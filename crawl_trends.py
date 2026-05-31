import pandas as pd
from pytrends.request import TrendReq
import time
from datetime import datetime
import os
import re

# Configuration
SEED_KEYWORDS = ['tshirt', 't-shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch']
TIMEFRAME = 'now 7-d'
IP_BLACKLIST = [
    'disney', 'marvel', 'star wars', 'nike', 'adidas', 'taylor swift', 'bts',
    'michael jackson', 'nba', 'wnba', 'nfl', 'mlb', 'nhl', 'nintendo', 'pokemon',
    'harry potter', 'nasa', 'hellstar', 'ysl', 'gucci', 'prada', 'louis vuitton',
    'arsenal', 'real madrid', 'liverpool', 'man city', 'chelsea', 'bayern', 'barcelona',
    'knicks', 'lakers', 'celtics', 'warriors', 'bulls', 'amiri', 'trapstar', 'corteiz',
    'sp5der', 'minus two', 'syna world', 'harry styles', 'gracie abrams', 'daniel caesar',
    'bad bunny', 'billie eilish', 'drake', 'kanye', 'travis scott', 'bruno mars',
    'hello kitty', 'sanrio', 'nascar', 'f1', 'mercedes', 'ferrari', 'red bull'
]

EXCLUDE_KEYWORDS = [
    'meaning', 'definition', 'how to', 'why', 'iron', 'near me', 'template',
    'mockup', 'tee times', 'tee time', 'tee off', 'graphic tee', 'essential tee',
    'vintage tee', 'oversized tee', 'plain shirt', 'blank shirt', 'kaffee',
    'rezepte', 'bh für', 'bra for', 'tutorial', 'là gì'
]

APPAREL_TERMS = [
    'tshirts', 't-shirts', 'tshirt', 't-shirt', 'tank tops', 'tank top',
    'tanktops', 'tanktop', 'shirts', 'shirt', 'tees', 'tee', 'merch'
]

def get_pytrends():
    return TrendReq(hl='en-US', tz=360)

def fetch_trends_with_retry(pytrends, kw_list):
    for attempt in range(3):
        try:
            pytrends.build_payload(kw_list, cat=0, timeframe=TIMEFRAME, geo='', gprop='')
            return pytrends.related_queries()
        except Exception as e:
            print(f"Error fetching {kw_list}, attempt {attempt+1}: {e}")
            if "429" in str(e):
                print("Rate limit hit, waiting 60s...")
                time.sleep(60)
            else:
                time.sleep(5)
    return None

def generate_idea(keyword):
    # Clean up the keyword to create a design idea
    temp_kw = keyword.lower()
    for term in sorted(APPAREL_TERMS, key=len, reverse=True):
        temp_kw = temp_kw.replace(term, "design")

    temp_kw = re.sub(' +', ' ', temp_kw).strip()
    return f"Design focused on '{temp_kw}'. Internet is searching for this specific apparel item, suggesting a niche demand."

def process_trends():
    pytrends = get_pytrends()
    all_rising = []
    seen_keywords = set()

    for kw in SEED_KEYWORDS:
        print(f"Fetching trends for: {kw}")
        result = fetch_trends_with_retry(pytrends, [kw])
        if result and kw in result:
            rising = result[kw]['rising']
            if rising is not None:
                for _, row in rising.iterrows():
                    query = row['query'].lower()
                    score = row['value']

                    # Filtering
                    if query in seen_keywords: continue
                    if len(query.split()) < 2: continue
                    if any(ex in query for ex in EXCLUDE_KEYWORDS): continue
                    if not any(term in query for term in APPAREL_TERMS): continue
                    # Avoid just the seed keywords or generic variations
                    if query.strip() in ['t shirt', 't-shirts', 't shirts', 'tees']: continue

                    is_ip = any(ip in query for ip in IP_BLACKLIST)

                    all_rising.append({
                        'keyword': query,
                        'score': 9999 if score == 'Breakout' else int(score),
                        'is_ip': is_ip,
                        'idea': generate_idea(query)
                    })
                    seen_keywords.add(query)
        time.sleep(5) # Small delay between keywords

    if not all_rising:
        print("No new trends found.")
        return

    # Sort by score descending
    all_rising.sort(key=lambda x: x['score'], reverse=True)

    general_merch = [t for t in all_rising if not t['is_ip']]
    ip_infringing = [t for t in all_rising if t['is_ip']]

    date_str = datetime.now().strftime('%Y-%m-%d')
    output = f"\n## {date_str}\n\n"

    if general_merch:
        output += "### General Merch Opportunities\n\n"
        output += "| keyword | score | Why/Idea |\n"
        output += "| --- | --- | --- |\n"
        for t in general_merch:
            output += f"| {t['keyword']} | {t['score']} | {t['idea']} |\n"
        output += "\n"

    if ip_infringing:
        output += "### Potential IP Infringing Opportunities\n\n"
        output += "| keyword | score | Why/Idea |\n"
        output += "| --- | --- | --- |\n"
        for t in ip_infringing:
            output += f"| {t['keyword']} | {t['score']} | {t['idea']} |\n"
        output += "\n"

    # Write to trends.md
    if os.path.exists('trends.md'):
        with open('trends.md', 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if date already exists to avoid duplicates
        if f"## {date_str}" in content:
            print(f"Trends for {date_str} already exist in trends.md. Skipping append.")
            return

        # Prepend after the first header and description
        header_end = content.find('---') + 3
        new_content = content[:header_end] + output + content[header_end:]

        with open('trends.md', 'w', encoding='utf-8') as f:
            f.write(new_content)
    else:
        with open('trends.md', 'w', encoding='utf-8') as f:
            f.write("# Google Trends Merch Opportunities\n\n" + output)

    print(f"Successfully updated trends.md with {len(all_rising)} new trends.")

if __name__ == "__main__":
    process_trends()
