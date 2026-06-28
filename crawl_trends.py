import os
import datetime
import pandas as pd
from pytrends.request import TrendReq
import time
import re

# Keywords to track
SEED_KEYWORDS = ['tshirt', 't-shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch']

# IP Blacklist (common brands and properties)
IP_BLACKLIST = [
    'disney', 'marvel', 'star wars', 'nike', 'adidas', 'taylor swift', 'bts',
    'michael jackson', 'nba', 'wnba', 'nfl', 'mlb', 'nhl', 'nintendo', 'pokemon',
    'harry potter', 'nasa', 'hellstar', 'ysl', 'gucci', 'prada', 'louis vuitton',
    'arsenal', 'real madrid', 'liverpool', 'man city', 'chelsea', 'bayern', 'barcelona',
    'knicks', 'lakers', 'celtics', 'warriors', 'bulls', 'amiri', 'trapstar', 'corteiz',
    'sp5der', 'minus two', 'syna world', 'harry styles', 'gracie abrams', 'daniel caesar',
    'bad bunny', 'billie eilish', 'drake', 'kanye', 'travis scott', 'bruno mars',
    'hello kitty', 'sanrio', 'nascar', 'f1', 'mercedes', 'ferrari', 'red bull',
    'toy story', 'psg', 'asap rocky', 'megan moroney', 'sean john', 'morgan wallen',
    'spurs', 'rcb', 'snipes', 'asos', 'pattie gonia', 'wingstop', 'ariana grande',
    'selena gomez', 'carhartt', 'hazbin hotel', 'digital circus', 'tadc',
    'linkin park', 'bad omens', 'forrest frank', 'malcolm todd', 'böhse onkelz',
    'love island', 'eternal sunshine', 'madewell', 'anthropologie', 'glitch',
    'stevie nicks', 'beyonce', 'lilibet', 'olivia rodrigo', 'caitlin clark',
    'sabrina carpenter', 'messi', 'ronaldo', 'spiderman', 'spider-man', 'batman',
    'superman', 'fifa', 'uefa', 'palace', 'kobe', 'cowboys', 'yankees', 'dodgers',
    'dfb', 'us open', 'olympics', 'cecil', 'h&m', 'levi\'s', 'zara', 'gap',
    'old navy', 'lululemon', 'patagonia', 'north face', 'under armour', 'puma',
    'reebok', 'vans', 'converse', 'stussy', 'supreme', 'hilary duff', 'lewis capaldi',
    'radiohead', 'beabadoobee', 'phoebe bridgers', 'kmfdm', 'ye', 'jackass', 'runescape',
    'supergirl'
]

def is_ip_infringing(keyword):
    keyword_lower = keyword.lower()
    for item in IP_BLACKLIST:
        if re.search(rf'\b{re.escape(item)}\b', keyword_lower):
            return True
    return False

def generate_idea(keyword):
    # Simple logic to generate ideas
    clean_keyword = keyword

    # Sort SEED_KEYWORDS by length descending to replace longer terms first (e.g. 'tank top' before 'top' or 'shirt')
    sorted_seeds = sorted(SEED_KEYWORDS, key=len, reverse=True)

    for term in sorted_seeds:
        # Also handle plurals and common variants
        for t in [term + 's', term]:
            pattern = re.compile(re.escape(t), re.IGNORECASE)
            clean_keyword = pattern.sub('', clean_keyword).strip()

    clean_keyword = re.sub(' +', ' ', clean_keyword) # clean multiple spaces

    if not clean_keyword:
        clean_keyword = keyword

    return f"Design featuring '{clean_keyword}'. Consider using trending typography or a relevant graphic style. The internet is searching for this specific apparel item."

def fetch_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    all_results = []

    for kw in SEED_KEYWORDS:
        try:
            print(f"Fetching trends for: {kw}")
            pytrends.build_payload([kw], timeframe='now 7-d')
            related_queries = pytrends.related_queries()

            if kw in related_queries and related_queries[kw]['rising'] is not None:
                rising = related_queries[kw]['rising']
                for index, row in rising.iterrows():
                    query = row['query']
                    score = row['value']

                    # Criteria: long tail (2+ words)
                    if len(query.split()) >= 2:
                        # Check if it contains one of the seed keywords to ensure it's apparel related
                        # though it was a related query to a seed keyword, sometimes it's not
                        if any(term in query.lower() for term in SEED_KEYWORDS):
                            # Filter out generic ones like "t shirt", "t-shirts"
                            if query.lower() in [s.lower() for s in SEED_KEYWORDS] or query.lower() in [s.lower()+'s' for s in SEED_KEYWORDS]:
                                continue

                            # Filter out some non-merch related common phrases
                            if any(x in query.lower() for x in [
                                'meaning', 'definition', 'how to', 'why', 'iron', 'near me',
                                'template', 'mockup', 'tee times', 'tee time', 'tee off',
                                'graphic tee', 'essential tee', 'vintage tee', 'oversized tee',
                                'plain shirt', 'blank shirt', 'kaffee', 'rezepte', 'bh für',
                                'bra for', 'tutorial', 'bra', 't-shirt bra', 'tee height',
                                'là gì'
                            ]):
                                continue

                            all_results.append({
                                'keyword': query,
                                'score': score,
                                'ip_infringing': is_ip_infringing(query)
                            })
            time.sleep(5) # Rate limiting
        except Exception as e:
            print(f"Error fetching {kw}: {e}")

    return all_results

def update_trends_md(results):
    if not results:
        print("No new trends found.")
        return

    today = datetime.date.today().strftime('%Y-%m-%d')

    # Deduplicate
    unique_results = []
    seen = set()
    for res in results:
        if res['keyword'].lower() not in seen:
            unique_results.append(res)
            seen.add(res['keyword'].lower())

    # Sort results by score (descending), Breakout is treated as highest
    def get_score_val(s):
        if isinstance(s, str) and 'Breakout' in s:
            return 9999
        try:
            return int(s)
        except:
            return 0

    unique_results.sort(key=lambda x: get_score_val(x['score']), reverse=True)

    general = [r for r in unique_results if not r['ip_infringing']]
    infringing = [r for r in unique_results if r['ip_infringing']]

    new_content = f"## {today}\n\n"

    new_content += "### General Merch Opportunities\n"
    new_content += "| Keyword | Score | Why/Idea |\n"
    new_content += "|---------|-------|----------|\n"
    for r in general:
        idea = generate_idea(r['keyword'])
        new_content += f"| {r['keyword']} | {r['score']} | {idea} |\n"

    if infringing:
        new_content += "\n### Potential IP Infringing Opportunities\n"
        new_content += "| Keyword | Score | Why/Idea |\n"
        new_content += "|---------|-------|----------|\n"
        for r in infringing:
            idea = generate_idea(r['keyword'])
            new_content += f"| {r['keyword']} | {r['score']} | {idea} |\n"

    new_content += "\n"

    # Prepend to file
    try:
        with open('trends.md', 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        lines = ["# Google Trends Merch Opportunities\n"]

    header = lines[0]
    rest = "".join(lines[1:])

    # Check if we already added today's trends to avoid duplicates if run multiple times
    if any(f"## {today}" in line for line in lines):
        print(f"Trends for {today} already exist in trends.md. Skipping update.")
        return

    updated_content = header + "\n" + new_content + rest

    with open('trends.md', 'w', encoding='utf-8') as f:
        f.write(updated_content)

    print(f"Updated trends.md with {len(unique_results)} new trends.")

if __name__ == "__main__":
    results = fetch_trends()
    update_trends_md(results)
