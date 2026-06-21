import pandas as pd
from pytrends.request import TrendReq
import time
import datetime
import os
import re

# Configuration
KEYWORDS = ['tshirt', 't-shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch']
EXCLUDED_TERMS = [
    'meaning', 'definition', 'how to', 'why', 'iron', 'near me', 'template',
    'mockup', 'tee times', 'tee time', 'tee off', 'graphic tee', 'essential tee',
    'vintage tee', 'oversized tee', 'plain shirt', 'blank shirt', 'kaffee',
    'rezepte', 'bh für', 'bra for', 'tutorial', 'bra', 't-shirt bra', 'là gì'
]
IP_BLACKLIST = [
    'Disney', 'Marvel', 'Star Wars', 'Nike', 'Adidas', 'Taylor Swift', 'BTS',
    'Michael Jackson', 'NBA', 'WNBA', 'NFL', 'MLB', 'NHL', 'Nintendo', 'Pokemon',
    'Harry Potter', 'NASA', 'Hellstar', 'YSL', 'Gucci', 'Prada', 'Louis Vuitton',
    'Arsenal', 'Real Madrid', 'Liverpool', 'Man City', 'Chelsea', 'Bayern',
    'Barcelona', 'Knicks', 'Lakers', 'Celtics', 'Warriors', 'Bulls', 'Amiri',
    'Trapstar', 'Corteiz', 'Sp5der', 'Minus Two', 'Syna World', 'Harry Styles',
    'Gracie Abrams', 'Daniel Caesar', 'Bad Bunny', 'Billie Eilish', 'Drake',
    'Kanye', 'Travis Scott', 'Bruno Mars', 'Hello Kitty', 'Sanrio', 'NASCAR',
    'F1', 'Mercedes', 'Ferrari', 'Red Bull', 'Toy Story', 'PSG', 'ASAP Rocky',
    'Megan Moroney', 'Sean John', 'Morgan Wallen', 'Spurs', 'RCB', 'Snipes',
    'ASOS', 'Pattie Gonia', 'Wingstop', 'Ariana Grande', 'selena gomez',
    'Carhartt', 'Hazbin Hotel', 'Digital Circus', 'TADC', 'Linkin Park',
    'Bad Omens', 'Forrest Frank', 'Malcolm Todd', 'Böhse Onkelz', 'Love Island',
    'Eternal Sunshine', 'Madewell', 'Anthropologie', 'Glitch', 'Stevie Nicks',
    'Beyonce', 'Lilibet', 'Olivia Rodrigo', 'Caitlin Clark', 'Sabrina Carpenter'
]

APPAREL_TERMS = ['tshirt', 't-shirt', 'tshirts', 't-shirts', 'shirt', 'shirts', 'tank top', 'tanktop', 'tank tops', 'tanktops', 'tee', 'tees', 'merch']

def is_ip_infringing(keyword):
    for term in IP_BLACKLIST:
        if re.search(rf'\b{re.escape(term)}\b', keyword, re.IGNORECASE):
            return True
    return False

def get_design_idea(keyword):
    clean_keyword = keyword.lower()
    # Replace longer terms first
    sorted_apparel = sorted(APPAREL_TERMS, key=len, reverse=True)
    for term in sorted_apparel:
        clean_keyword = clean_keyword.replace(term, '')

    clean_keyword = re.sub(r'\s+', ' ', clean_keyword).strip()
    if not clean_keyword:
        clean_keyword = keyword

    return f"Graphic featuring '{clean_keyword}'. Focus on clean typography or a minimalist illustration of the concept."

def fetch_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    all_results = []
    seen_keywords = set()

    for kw in KEYWORDS:
        print(f"Fetching trends for: {kw}")
        retries = 2
        while retries >= 0:
            try:
                pytrends.build_payload([kw], timeframe='now 7-d')
                related_queries = pytrends.related_queries()

                if kw in related_queries and related_queries[kw]['rising'] is not None:
                    rising = related_queries[kw]['rising']
                    for _, row in rising.iterrows():
                        query = row['query']
                        value = row['value']

                        # Filtering
                        if query in seen_keywords:
                            continue

                        words = query.split()
                        if len(words) < 2:
                            continue

                        if not any(term in query.lower() for term in APPAREL_TERMS):
                            continue

                        if any(term in query.lower() for term in EXCLUDED_TERMS):
                            continue

                        # Exact match or generic variations of seed keywords
                        if query.lower().strip() in ['t shirt', 't-shirts', 'tees', 'merch']:
                            continue

                        score = 9999 if value == 'Breakout' else int(value)

                        all_results.append({
                            'keyword': query,
                            'score': score,
                            'infringing': is_ip_infringing(query),
                            'idea': get_design_idea(query)
                        })
                        seen_keywords.add(query)

                break # Success
            except Exception as e:
                print(f"Error fetching {kw}: {e}")
                if "429" in str(e):
                    print("Rate limit hit, sleeping for 30s...")
                    time.sleep(30)
                    retries -= 1
                else:
                    break

        time.sleep(5) # Delay between keywords

    return all_results

def update_trends_md(results):
    if not results:
        print("No new trends found.")
        return

    # Sort by score descending
    results.sort(key=lambda x: x['score'], reverse=True)

    today = datetime.date.today().strftime('%Y-%m-%d')

    general_table = "| Keyword | Score | Why/Idea |\n|---------|-------|----------|\n"
    ip_table = "| Keyword | Score | Why/Idea |\n|---------|-------|----------|\n"

    gen_count = 0
    ip_count = 0

    for res in results:
        row = f"| {res['keyword']} | {res['score']} | {res['idea']} |\n"
        if res['infringing']:
            ip_table += row
            ip_count += 1
        else:
            general_table += row
            gen_count += 1

    content = f"## {today}\n\n"
    if gen_count > 0:
        content += "### General Merch Opportunities\n\n" + general_table + "\n"
    if ip_count > 0:
        content += "### Potential IP Infringing Opportunities\n\n" + ip_table + "\n"

    filepath = 'trends.md'
    header = "# Google Trends Merch Opportunities\n\n"

    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            old_content = f.read()

        # Check if today's update already exists
        if f"## {today}" in old_content:
            print(f"Trends for {today} already exist in {filepath}. Skipping.")
            return

        if header in old_content:
            new_file_content = old_content.replace(header, header + content)
        else:
            new_file_content = header + content + old_content
    else:
        new_file_content = header + content

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_file_content)

    print(f"Successfully updated {filepath} with {len(results)} new trends.")

if __name__ == "__main__":
    trends = fetch_trends()
    update_trends_md(trends)
