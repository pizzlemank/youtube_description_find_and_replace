import time
import datetime
import re
import os
import pandas as pd
from pytrends.request import TrendReq
from requests.exceptions import HTTPError

# --- Configuration ---
SEED_KEYWORDS = ['tshirt', 't-shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch']
TIMEFRAME = 'now 7-d'  # Last 7 days
TRENDS_FILE = 'trends.md'

# Extensive IP Blacklist (Brands, Celebs, Sports Teams, Franchises)
IP_BLACKLIST = [
    'disney', 'marvel', 'star wars', 'nike', 'adidas', 'taylor swift', 'bts', 'michael jackson',
    'nba', 'wnba', 'nfl', 'mlb', 'nhl', 'nintendo', 'pokemon', 'harry potter', 'nasa',
    'hellstar', 'ysl', 'gucci', 'prada', 'louis vuitton', 'arsenal', 'real madrid', 'liverpool',
    'man city', 'chelsea', 'bayern', 'barcelona', 'knicks', 'lakers', 'celtics', 'warriors',
    'bulls', 'amiri', 'trapstar', 'corteiz', 'sp5der', 'minus two', 'syna world', 'harry styles',
    'gracie abrams', 'daniel caesar', 'bad bunny', 'billie eilish', 'drake', 'kanye', 'travis scott',
    'bruno mars', 'hello kitty', 'sanrio', 'nascar', 'f1', 'mercedes', 'ferrari', 'red bull',
    'toy story', 'psg', 'asap rocky', 'megan moroney', 'sean john', 'morgan wallen', 'spurs',
    'rcb', 'snipes', 'asos', 'pattie gonia', 'wingstop', 'ariana grande', 'selena gomez',
    'carhartt', 'hazbin hotel', 'digital circus', 'tadc', 'linkin park', 'bad omens',
    'forrest frank', 'malcolm todd', 'böhse onkelz', 'love island', 'eternal sunshine',
    'madewell', 'anthropologie', 'glitch', 'stevie nicks', 'beyonce', 'lilibet', 'olivia rodrigo',
    'caitlin clark', 'sabrina carpenter', 'messi', 'ronaldo', 'spiderman', 'spider-man', 'batman',
    'superman', 'fifa', 'uefa', 'palace', 'kobe', 'cowboys', 'yankees', 'dodgers', 'dfb',
    'us open', 'olympics', 'cecil', 'h&m', "levi's", 'zara', 'gap', 'old navy', 'lululemon',
    'patagonia', 'north face', 'under armour', 'puma', 'reebok', 'vans', 'converse', 'stussy',
    'supreme', 'hilary duff', 'lewis capaldi', 'radiohead', 'beabadoobee', 'phoebe bridgers',
    'kmfdm', 'ye', 'jackass', 'runescape', 'supergirl', 'noah kahan', 'my chemical romance',
    'mcr', 'john deere', 'wimbledon', 'alan jackson'
]

# Generic terms to filter out (avoiding common apparel terms themselves)
GENERIC_FILTERS = [
    'meaning', 'definition', 'how to', 'why', 'iron', 'near me', 'template', 'mockup',
    'tee times', 'tee time', 'tee off', 'graphic tee', 'essential tee', 'vintage tee',
    'oversized tee', 'plain shirt', 'blank shirt', 'kaffee', 'rezepte', 'bh für',
    'bra for', 'tutorial', 'bra', 't-shirt bra', 'tee height', 'là gì', 't-shirt femme',
    'custom t-shirt printing', 'roblox t-shirt'
]

def fetch_rising_queries(pytrends, keyword):
    """Fetches rising related queries for a keyword with retries."""
    for attempt in range(3):
        try:
            pytrends.build_payload([keyword], timeframe=TIMEFRAME)
            related_queries = pytrends.related_queries()
            if keyword in related_queries and related_queries[keyword]['rising'] is not None:
                return related_queries[keyword]['rising']
            return pd.DataFrame()
        except Exception as e:
            print(f"Error fetching for {keyword}: {e}")
            if "429" in str(e):
                print("Rate limit hit. Waiting 10 seconds...")
                time.sleep(10)
            else:
                break
    return pd.DataFrame()

def is_ip_infringing(keyword):
    """Checks if a keyword contains any blacklisted IP terms."""
    keyword_lower = keyword.lower()
    for term in IP_BLACKLIST:
        if re.search(rf'\b{re.escape(term)}\b', keyword_lower):
            return True
    return False

def generate_idea(keyword):
    """Generates a simple design idea based on the keyword."""
    # Clean up common apparel terms to get the core concept
    concept = keyword.lower()
    for term in ['tshirts', 't-shirts', 'tank tops', 'tanktop', 'tshirt', 't-shirt', 'shirt', 'tee', 'merch']:
        concept = concept.replace(term, '')
    concept = re.sub(r'\s+', ' ', concept).strip()

    return f"Design featuring '{concept.title()}'. Target audience interested in this trending topic."

def main():
    pytrends = TrendReq(hl='en-US', tz=360)
    all_results = []
    seen_keywords = set()

    print(f"Starting crawl at {datetime.datetime.now()}")

    for seed in SEED_KEYWORDS:
        print(f"Fetching rising queries for: {seed}")
        df = fetch_rising_queries(pytrends, seed)

        if not df.empty:
            for index, row in df.iterrows():
                query = row['query']
                score = row['value']

                # Deduplication
                if query in seen_keywords:
                    continue
                seen_keywords.add(query)

                # Filtering: Long tail (2+ words) and contains apparel term
                words = query.split()
                has_apparel_term = any(term in query.lower() for term in SEED_KEYWORDS)
                is_generic = any(term in query.lower() for term in GENERIC_FILTERS)

                if len(words) >= 2 and has_apparel_term and not is_generic:
                    all_results.append({
                        'keyword': query,
                        'score': score,
                        'infringing': is_ip_infringing(query)
                    })

        time.sleep(5) # Delay to avoid rate limiting

    if not all_results:
        print("No new trends found.")
        return

    # Sort by score descending (Breakout = 9999 for sorting)
    def get_sort_score(val):
        if val == 'Breakout' or (isinstance(val, str) and 'Breakout' in val):
            return 9999
        try:
            return int(val)
        except:
            return 0

    all_results.sort(key=lambda x: get_sort_score(x['score']), reverse=True)

    # Separate into General and Infringing
    general = [r for r in all_results if not r['infringing']]
    infringing = [r for r in all_results if r['infringing']]

    # Prepare Markdown content
    today = datetime.date.today().isoformat()
    md_content = f"\n## {today}\n\n### General Merch Opportunities\n"
    md_content += "| Keyword | Score | Why/Idea |\n"
    md_content += "| :--- | :--- | :--- |\n"

    for r in general:
        idea = generate_idea(r['keyword'])
        md_content += f"| {r['keyword']} | {r['score']} | {idea} |\n"

    if infringing:
        md_content += "\n### Potential IP Infringing Opportunities\n"
        md_content += "| Keyword | Score | Why/Idea |\n"
        md_content += "| :--- | :--- | :--- |\n"
        for r in infringing:
            idea = generate_idea(r['keyword'])
            md_content += f"| {r['keyword']} | {r['score']} | {idea} |\n"

    # Write to trends.md
    if not os.path.exists(TRENDS_FILE):
        with open(TRENDS_FILE, 'w', encoding='utf-8') as f:
            f.write("# Google Trends Merch Opportunities\n")

    with open(TRENDS_FILE, 'r', encoding='utf-8') as f:
        existing_content = f.read()

    # Avoid duplicate entry for the same day
    if f"## {today}" in existing_content:
        print(f"Trends for {today} already exist in {TRENDS_FILE}. Skipping file update.")
    else:
        # Prepend after the main header
        header = "# Google Trends Merch Opportunities\n"
        new_file_content = header + md_content + existing_content[len(header):]
        with open(TRENDS_FILE, 'w', encoding='utf-8') as f:
            f.write(new_file_content)
        print(f"Updated {TRENDS_FILE} with {len(all_results)} new trends.")

if __name__ == "__main__":
    main()
