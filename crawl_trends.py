import time
import pandas as pd
from pytrends.request import TrendReq
from datetime import datetime
import os
import re

# Configuration
KEYWORDS = ['tshirt', 't-shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch']
TIMEFRAME = 'now 7-d'
TRENDS_FILE = 'trends.md'
IP_BLACKLIST = [
    'disney', 'marvel', 'star wars', 'nike', 'adidas', 'taylor swift', 'bts',
    'michael jackson', 'nba', 'wnba', 'nfl', 'mlb', 'nhl', 'nintendo', 'pokemon',
    'harry potter', 'nasa', 'hellstar', 'ysl', 'gucci', 'prada', 'louis vuitton',
    'arsenal', 'real madrid', 'liverpool', 'man city', 'chelsea', 'bayern',
    'barcelona', 'knicks', 'lakers', 'celtics', 'warriors', 'bulls', 'amiri',
    'trapstar', 'corteiz', 'sp5der', 'minus two', 'syna world', 'harry styles',
    'gracie abrams', 'daniel caesar', 'bad bunny', 'billie eilish', 'drake',
    'kanye', 'travis scott', 'bruno mars', 'hello kitty', 'sanrio', 'nascar',
    'f1', 'mercedes', 'ferrari', 'red bull', 'toy story', 'psg', 'asap rocky',
    'megan moroney', 'sean john', 'morgan wallen', 'spurs', 'rcb', 'snipes',
    'asos', 'pattie gonia', 'wingstop', 'ariana grande', 'selena gomez',
    'carhartt', 'hazbin hotel', 'digital circus', 'tadc', 'linkin park',
    'bad omens', 'forrest frank', 'malcolm todd', 'böhse onkelz', 'love island',
    'eternal sunshine', 'madewell', 'anthropologie', 'glitch'
]

EXCLUDED_TERMS = [
    'meaning', 'definition', 'how to', 'why', 'iron', 'near me', 'template',
    'mockup', 'tee times', 'tee time', 'tee off', 'graphic tee', 'essential tee',
    'vintage tee', 'oversized tee', 'plain shirt', 'blank shirt', 'kaffee',
    'rezepte', 'bh für', 'bra for', 'tutorial', 'là gì'
]

def get_pytrends_with_retries():
    # We implement our own retry logic as suggested by memory
    for attempt in range(3):
        try:
            pytrends = TrendReq(hl='en-US', tz=360)
            return pytrends
        except Exception as e:
            print(f"Error initializing pytrends (attempt {attempt+1}): {e}")
            time.sleep(60)
    return None

def fetch_rising_queries(pytrends, keyword):
    for attempt in range(2):
        try:
            pytrends.build_payload([keyword], timeframe=TIMEFRAME)
            rising = pytrends.related_queries()[keyword]['rising']
            return rising
        except Exception as e:
            if "429" in str(e):
                print(f"Rate limited for '{keyword}'. Retrying in 30s...")
                time.sleep(30)
            else:
                print(f"Error fetching for '{keyword}': {e}")
                break
    return None

def generate_idea(query):
    # Basic logic to generate an idea/explanation
    query_clean = query.lower()
    for kw in KEYWORDS:
        query_clean = query_clean.replace(kw, '').strip()

    # Clean up extra spaces
    query_clean = re.sub(' +', ' ', query_clean)

    if not query_clean:
        return "Generic apparel search."

    return f"Design featuring '{query_clean}' aesthetic/quote. Market shows rising interest in this specific niche."

def process_trends():
    pytrends = get_pytrends_with_retries()
    if not pytrends:
        return

    all_trends = []
    seen_queries = set()

    for kw in KEYWORDS:
        print(f"Fetching trends for: {kw}")
        rising = fetch_rising_queries(pytrends, kw)
        if rising is not None and not rising.empty:
            for index, row in rising.iterrows():
                query = row['query']
                score = row['value']

                # Deduplication
                if query in seen_queries:
                    continue
                seen_queries.add(query)

                # Filter long-tail (2+ words)
                query_lower = query.lower()
                if len(query.split()) < 2:
                    continue

                # Ensure it contains an apparel-related term as per "long tail of - shirts or -tshirt..."
                if not any(term in query_lower for term in KEYWORDS):
                    continue

                # Filter excluded terms
                if any(term in query_lower for term in EXCLUDED_TERMS):
                    continue

                # Filter generic variations of seed keywords
                if query_lower in ['t shirt', 't-shirts', 'tees', 'tank tops', 't shirts', 'shirts', 't-shirt', 'shirt']:
                    continue

                is_ip_infringing = any(brand in query_lower for brand in IP_BLACKLIST)

                idea = generate_idea(query)

                all_trends.append({
                    'keyword': query,
                    'score': score,
                    'idea': idea,
                    'ip_infringing': is_ip_infringing
                })

        # Delay to mitigate rate limiting
        time.sleep(2)

    if not all_trends:
        print("No new trends found.")
        return

    # Sort by score (Breakout = 9999)
    def sort_key(x):
        val = x['score']
        if isinstance(val, str) and 'breakout' in val.lower():
            return 9999
        try:
            return int(val)
        except:
            return 0

    all_trends.sort(key=sort_key, reverse=True)

    # Prepare Markdown content
    date_str = datetime.now().strftime('%Y-%m-%d')

    # Check if today's entry already exists
    if os.path.exists(TRENDS_FILE):
        with open(TRENDS_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            if f"## {date_str}" in content:
                print(f"Trends for {date_str} already exist in {TRENDS_FILE}. Skipping.")
                return

    general_merch = [t for t in all_trends if not t['ip_infringing']]
    ip_infringing = [t for t in all_trends if t['ip_infringing']]

    new_content = f"## {date_str}\n\n"

    new_content += "### General Merch Opportunities\n"
    new_content += "| keyword | score | why you think is an opportunity, idea for design, or what the internet shopping is already doing |\n"
    new_content += "| --- | --- | --- |\n"
    for t in general_merch:
        new_content += f"| {t['keyword']} | {t['score']} | {t['idea']} |\n"

    new_content += "\n### Potential IP Infringing Opportunities\n"
    new_content += "| keyword | score | why you think is an opportunity, idea for design, or what the internet shopping is already doing |\n"
    new_content += "| --- | --- | --- |\n"
    for t in ip_infringing:
        new_content += f"| {t['keyword']} | {t['score']} | {t['idea']} |\n"

    new_content += "\n---\n"

    # Prepend to file
    if os.path.exists(TRENDS_FILE):
        with open(TRENDS_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Keep the title at the top if it exists
        title = "# Google Trends Merch Opportunities\n\n"
        body = "".join(lines)
        if body.startswith("# "):
            title_end = body.find("\n\n") + 2
            title = body[:title_end]
            body = body[title_end:]

        updated_content = title + new_content + body
    else:
        updated_content = "# Google Trends Merch Opportunities\n\n" + new_content

    with open(TRENDS_FILE, 'w', encoding='utf-8') as f:
        f.write(updated_content)

    print(f"Successfully updated {TRENDS_FILE} with {len(all_trends)} trends.")

if __name__ == "__main__":
    process_trends()
