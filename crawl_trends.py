import pandas as pd
from pytrends.request import TrendReq
import datetime
import os
import re
import time
from requests.exceptions import HTTPError

# Configuration
KEYWORDS = ['tshirt', 't-shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch']
BLACKLIST = [
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
    'caitlin clark', 'sabrina carpenter', 'messi', 'ronaldo', 'spiderman', 'spider-man',
    'batman', 'superman', 'fifa', 'uefa', 'palace', 'kobe', 'cowboys', 'yankees', 'dodgers',
    'dfb', 'us open', 'olympics', 'cecil', 'h&m', 'levi\'s', 'zara', 'gap', 'old navy',
    'lululemon', 'patagonia', 'north face', 'under armour', 'puma', 'reebok', 'vans',
    'converse', 'stussy', 'supreme', 'hilary duff', 'lewis capaldi', 'radiohead',
    'beabadoobee', 'phoebe bridgers', 'kmfdm', 'ye', 'jackass', 'runescape', 'supergirl'
]

APPAREL_TERMS = ['shirt', 'tshirt', 't-shirt', 'tank top', 'tanktop', 'tee', 'merch']

def is_ip_infringing(keyword):
    keyword_lower = keyword.lower()
    for term in BLACKLIST:
        if re.search(rf'\b{re.escape(term)}\b', keyword_lower):
            return True
    return False

def get_idea(keyword):
    # Clean up the keyword to make a design idea
    idea_base = keyword.lower()
    for term in sorted(APPAREL_TERMS, key=len, reverse=True):
        idea_base = idea_base.replace(term + 's', '').replace(term, '')

    idea_base = idea_base.strip()
    idea_base = re.sub(r'\s+', ' ', idea_base)

    if not idea_base:
        return "Generic apparel trend. Focus on minimalist typography or high-quality blanks."

    return f"Create a design featuring '{idea_base}'. The market is searching for this specific niche. Check social media for aesthetic cues (vintage, Y2K, minimalist)."

def fetch_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    all_results = []

    for kw in KEYWORDS:
        print(f"Fetching trends for: {kw}")
        try:
            pytrends.build_payload([kw], timeframe='now 7-d')
            related_queries = pytrends.related_queries()

            if kw in related_queries and related_queries[kw]['rising'] is not None:
                rising = related_queries[kw]['rising']
                for _, row in rising.iterrows():
                    query = row['query']
                    score = row['value']

                    # Filter for long-tail (2+ words) and must contain an apparel term
                    words = query.split()
                    if len(words) >= 2 and any(term in query.lower() for term in APPAREL_TERMS):
                        # Filter out exact matches or very generic ones
                        if query.lower().strip() in [t.strip() for t in APPAREL_TERMS] or query.lower() in ['t shirt', 't-shirts']:
                            continue

                        # Exclude some noise
                        exclude = ['meaning', 'definition', 'how to', 'why', 'iron', 'near me', 'template', 'mockup', 'tee times', 'tee time', 'tee off', 'graphic tee', 'essential tee', 'vintage tee', 'oversized tee', 'plain shirt', 'blank shirt', 'kaffee', 'rezepte', 'bh für', 'bra for', 'tutorial', 'bra', 't-shirt bra', 'tee height', 'là gì']
                        if any(ex in query.lower() for ex in exclude):
                            continue

                        all_results.append({
                            'keyword': query,
                            'score': score,
                            'ip_infringing': is_ip_infringing(query)
                        })

            time.sleep(5) # Avoid rate limiting
        except Exception as e:
            print(f"Error fetching {kw}: {e}")
            if "429" in str(e):
                print("Rate limit hit. Waiting longer...")
                time.sleep(10)

    return all_results

def update_markdown(results):
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    filename = 'trends.md'

    if not results:
        print("No new results found.")
        return

    # Deduplicate
    seen = set()
    unique_results = []
    for r in results:
        if r['keyword'].lower() not in seen:
            unique_results.append(r)
            seen.add(r['keyword'].lower())

    # Sort results: Breakout first, then by score descending
    def sort_key(x):
        val = x['score']
        if val == 'Breakout' or val == 99999:
            return 999999
        try:
            return int(val)
        except:
            return 0

    unique_results.sort(key=sort_key, reverse=True)

    general_merch = [r for r in unique_results if not r['ip_infringing']]
    ip_infringing = [r for r in unique_results if r['ip_infringing']]

    new_content = f"## {today}\n\n"

    if general_merch:
        new_content += "### General Merch Opportunities\n"
        new_content += "| Keyword | Score | Why/Idea |\n"
        new_content += "| :--- | :--- | :--- |\n"
        for r in general_merch:
            new_content += f"| {r['keyword']} | {r['score']} | {get_idea(r['keyword'])} |\n"
        new_content += "\n"

    if ip_infringing:
        new_content += "### Potential IP Infringing Opportunities\n"
        new_content += "| Keyword | Score | Why/Idea |\n"
        new_content += "| :--- | :--- | :--- |\n"
        for r in ip_infringing:
            new_content += f"| {r['keyword']} | {r['score']} | **Potential IP Infringement.** {get_idea(r['keyword'])} |\n"
        new_content += "\n"

    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            old_content = f.read()
            # Avoid duplicate entries for the same day if re-run
            if f"## {today}" in old_content:
                print(f"Content for {today} already exists in {filename}. Skipping update.")
                return
    else:
        old_content = "# Google Trends Merch Opportunities\n\n"

    # Prepend new content after the main header
    header = "# Google Trends Merch Opportunities\n\n"
    body = old_content.replace(header, "")
    final_content = header + new_content + body

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(final_content)

    print(f"Updated {filename} with {len(unique_results)} trends.")

if __name__ == "__main__":
    trends = fetch_trends()
    update_markdown(trends)
