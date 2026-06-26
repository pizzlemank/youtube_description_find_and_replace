import pandas as pd
from pytrends.request import TrendReq
import time
import datetime
import os
import re

# Keywords to search for
SEED_KEYWORDS = ['tshirt', 't-shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch']

# IP Blacklist (common brands, characters, etc.)
IP_BLACKLIST = [
    'disney', 'marvel', 'star wars', 'nike', 'adidas', 'taylor swift', 'bts', 'michael jackson',
    'nba', 'wnba', 'nfl', 'mlb', 'nhl', 'nintendo', 'pokemon', 'harry potter', 'nasa', 'hellstar',
    'ysl', 'gucci', 'prada', 'louis vuitton', 'arsenal', 'real madrid', 'liverpool', 'man city',
    'chelsea', 'bayern', 'barcelona', 'knicks', 'lakers', 'celtics', 'warriors', 'bulls',
    'amiri', 'trapstar', 'corteiz', 'sp5der', 'minus two', 'syna world', 'harry styles',
    'gracie abrams', 'daniel caesar', 'bad bunny', 'billie eilish', 'drake', 'kanye',
    'travis scott', 'bruno mars', 'hello kitty', 'sanrio', 'nascar', 'f1', 'mercedes',
    'ferrari', 'red bull', 'toy story', 'psg', 'asap rocky', 'megan moroney', 'sean john',
    'morgan wallen', 'spurs', 'rcb', 'snipes', 'asos', 'pattie gonia', 'wingstop',
    'ariana grande', 'selena gomez', 'carhartt', 'hazbin hotel', 'digital circus', 'tadc',
    'linkin park', 'bad omens', 'forrest frank', 'malcolm todd', 'böhse onkelz', 'love island',
    'eternal sunshine', 'madewell', 'anthropologie', 'glitch', 'stevie nicks', 'beyonce',
    'lilibet', 'olivia rodrigo', 'caitlin clark', 'sabrina carpenter', 'messi', 'ronaldo',
    'spiderman', 'spider-man', 'batman', 'superman', 'fifa', 'uefa', 'palace', 'kobe',
    'cowboys', 'yankees', 'dodgers', 'dfb', 'us open', 'olympics', 'cecil', 'h&m', 'h und m',
    'levis', 'levi\'s', 'zara', 'gap', 'old navy', 'lululemon', 'patagonia', 'north face',
    'under armour', 'puma', 'reebok', 'vans', 'converse', 'stussy', 'supreme'
]

# Words that usually indicate non-commercial or irrelevant trends
EXCLUDE_KEYWORDS = [
    'meaning', 'definition', 'how to', 'why', 'iron', 'near me', 'template', 'mockup',
    'tee times', 'tee time', 'tee off', 'graphic tee', 'essential tee', 'vintage tee',
    'oversized tee', 'plain shirt', 'blank shirt', 'kaffee', 'rezepte', 'bh für', 'bra for',
    'tutorial', 'bra', 't-shirt bra', 'là gì', 'tee height'
]

def is_ip_infringing(keyword):
    keyword_lower = keyword.lower()
    for term in IP_BLACKLIST:
        if re.search(rf'\b{re.escape(term)}\b', keyword_lower):
            return True
    return False

def generate_idea(keyword):
    # Basic idea generation logic
    clean_keyword = keyword
    for seed in SEED_KEYWORDS:
        # Plurals and variations
        for variation in [seed + 's', seed]:
             clean_keyword = re.sub(rf'\b{re.escape(variation)}\b', '', clean_keyword, flags=re.IGNORECASE).strip()

    clean_keyword = re.sub(r'\s+', ' ', clean_keyword).strip()

    if not clean_keyword:
        return "Generic apparel search, look for trending aesthetics."

    return f"Create a unique graphic design focusing on '{clean_keyword}'. Check if there's a specific viral meme or event associated with it."

def fetch_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    all_results = []

    for kw in SEED_KEYWORDS:
        print(f"Fetching trends for: {kw}")
        try:
            pytrends.build_payload([kw], timeframe='now 7-d')
            related_queries = pytrends.related_queries()

            if kw in related_queries and related_queries[kw]['rising'] is not None:
                rising = related_queries[kw]['rising']
                for index, row in rising.iterrows():
                    query = row['query']
                    score = row['value']

                    # Filtering
                    if any(exclude in query.lower() for exclude in EXCLUDE_KEYWORDS):
                        continue

                    # Must be long tail (at least 2 words)
                    if len(query.split()) < 2:
                        continue

                    # Must contain one of the seed keywords (or related apparel terms)
                    if not any(seed in query.lower() for seed in SEED_KEYWORDS):
                        continue

                    # Exact matches of seed keywords are usually too broad/boring
                    if query.lower() in [s.lower() for s in SEED_KEYWORDS] or query.lower() in ['t shirt', 't-shirts', 'tees']:
                        continue

                    # Deduplicate
                    if query not in [r['keyword'] for r in all_results]:
                        all_results.append({
                            'keyword': query,
                            'score': score,
                            'is_ip': is_ip_infringing(query)
                        })

            time.sleep(5) # Avoid rate limiting
        except Exception as e:
            print(f"Error fetching {kw}: {e}")
            if "429" in str(e):
                print("Rate limit hit. Retrying after 10s...")
                time.sleep(10)
                try:
                    pytrends.build_payload([kw], timeframe='now 7-d')
                    related_queries = pytrends.related_queries()
                    if kw in related_queries and related_queries[kw]['rising'] is not None:
                        rising = related_queries[kw]['rising']
                        for index, row in rising.iterrows():
                            query = row['query']
                            score = row['value']
                            if any(exclude in query.lower() for exclude in EXCLUDE_KEYWORDS): continue
                            if len(query.split()) < 2: continue
                            if not any(seed in query.lower() for seed in SEED_KEYWORDS): continue
                            if query.lower() in [s.lower() for s in SEED_KEYWORDS] or query.lower() in ['t shirt', 't-shirts', 'tees']: continue
                            if query not in [r['keyword'] for r in all_results]:
                                all_results.append({'keyword': query, 'score': score, 'is_ip': is_ip_infringing(query)})
                except Exception as e2:
                    print(f"Retry failed for {kw}: {e2}")

    return all_results

def update_trends_md(results):
    today = datetime.date.today().strftime('%Y-%m-%d')

    if not results:
        print("No new trends found today.")
        return

    # Sort results: Breakout (represented as high number) first, then by score descending
    def get_score(val):
        if isinstance(val, str) and 'Breakout' in val:
            return 9999
        try:
            return int(val)
        except:
            return 0

    results.sort(key=lambda x: get_score(x['score']), reverse=True)

    general_merch = [r for r in results if not r['is_ip']]
    ip_infringing = [r for r in results if r['is_ip']]

    new_content = f"## {today}\n\n"

    if general_merch:
        new_content += "### General Merch Opportunities\n"
        new_content += "| keyword | score | why you think is an opportunity, idea for design, or what the internet shopping is already doing |\n"
        new_content += "| :--- | :--- | :--- |\n"
        for r in general_merch:
            idea = generate_idea(r['keyword'])
            new_content += f"| {r['keyword']} | {r['score']} | {idea} |\n"
        new_content += "\n"

    if ip_infringing:
        new_content += "### Potential IP Infringing Opportunities\n"
        new_content += "| keyword | score | why you think is an opportunity, idea for design, or what the internet shopping is already doing |\n"
        new_content += "| :--- | :--- | :--- |\n"
        for r in ip_infringing:
            idea = generate_idea(r['keyword'])
            new_content += f"| {r['keyword']} | {r['score']} | **Potential IP Issue.** {idea} |\n"
        new_content += "\n"

    filename = 'trends.md'
    header = "# Google Trends Merch Opportunities\n\n"

    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            current_content = f.read()

        if f"## {today}" in current_content:
            print(f"Trends for {today} already exist in {filename}. Skipping update.")
            return

        # Keep the header at the top, prepend new content below it
        if current_content.startswith("# Google Trends Merch Opportunities"):
            content_without_header = current_content.replace(header, "", 1)
            updated_content = header + new_content + content_without_header
        else:
            updated_content = header + new_content + current_content
    else:
        updated_content = header + new_content

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(updated_content)

    print(f"Successfully updated {filename}")

if __name__ == "__main__":
    trends = fetch_trends()
    update_trends_md(trends)
