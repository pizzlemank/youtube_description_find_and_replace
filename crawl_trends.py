import pandas as pd
from pytrends.request import TrendReq
import time
import datetime
import os
import re

# Configuration
SEED_KEYWORDS = ['tshirt', 'shirt', 'tank top', 'merch', 'tee']
TIMEFRAME = 'now 7-d'
BRAND_BLACKLIST = [
    'disney', 'marvel', 'star wars', 'nike', 'adidas', 'bieber', 'taylor swift',
    'michael jackson', 'one piece', 'popeyes', 'coachella', 'netflix', 'mickey',
    'trump', 'biden', 'nba', 'nfl', 'mlb', 'nhl', 'pokemon', 'nintendo', 'sony',
    'playstation', 'xbox', 'nasa', 'hellstar', 'karol g', 'bruno mars',
    'sabrina carpenter', 'billie eilish', 'olivia rodrigo', 'noah kahan',
    'frank ocean', 'mashtag brady', 'aldi', 'morbid podcast', 'ysl',
    'koningsdag', 'oranje', 'higgins', 'kelce', 'mahomes', 'stroud'
]
EXCLUSION_KEYWORDS = [
    'meaning', 'definition', 'how to', 'why', 'iron', 'near me',
    'template', 'mockup', 'tee times', 'tee time', 'tee off',
    'graphic tee', 'essential tee', 'vintage tee', 'oversized tee',
    'plain shirt', 'blank shirt'
]
APPAREL_TERMS = ['shirt', 'tshirt', 'tank top', 'tanktop', 'tee']

def get_pytrends():
    return TrendReq(hl='en-US', tz=360)

def fetch_trends(pytrends, keyword):
    retries = 3
    for i in range(retries):
        try:
            pytrends.build_payload([keyword], timeframe=TIMEFRAME)
            related_queries = pytrends.related_queries()
            if keyword in related_queries and 'rising' in related_queries[keyword] and related_queries[keyword]['rising'] is not None:
                return related_queries[keyword]['rising']
            return None
        except Exception as e:
            if '429' in str(e):
                print(f"Rate limit hit for {keyword}, retrying in 10s... ({i+1}/{retries})")
                time.sleep(10)
            else:
                print(f"Error fetching trends for {keyword}: {e}")
                break
    return None

def is_ip_infringing(query):
    query_lower = query.lower()
    for brand in BRAND_BLACKLIST:
        if brand in query_lower:
            return True
    return False

def generate_idea(query):
    # Remove apparel terms to get the core concept
    concept = query.lower()
    # Sort apparel terms by length descending to replace longer ones first
    for term in sorted(APPAREL_TERMS, key=len, reverse=True):
        concept = concept.replace(term, '')

    concept = re.sub(r'\s+', ' ', concept).strip()
    return f"Design featuring '{concept.title()}' theme. Popular search trend indicates market interest in this niche."

def process_trends():
    pytrends = get_pytrends()
    all_results = []

    for seed in SEED_KEYWORDS:
        print(f"Fetching trends for: {seed}")
        rising = fetch_trends(pytrends, seed)
        if rising is not None and not rising.empty:
            all_results.append(rising)
        time.sleep(2) # Delay to avoid rate limiting

    if not all_results:
        print("No trends found.")
        return None

    df = pd.concat(all_results).drop_duplicates(subset=['query'])

    # Filter for long tail and apparel terms
    def filter_query(row):
        query = str(row['query']).lower()
        # 2+ words
        if len(query.split()) < 2:
            return False
        # Contains apparel term
        if not any(term in query for term in APPAREL_TERMS):
            return False
        # Not in exclusion list
        if any(exc in query for exc in EXCLUSION_KEYWORDS):
            return False
        return True

    df = df[df.apply(filter_query, axis=1)].copy()

    if df.empty:
        print("No matching trends after filtering.")
        return None

    # Handle scores
    def parse_score(val):
        if val == 'Breakout':
            return 999999
        try:
            return int(val)
        except:
            return 0

    df['score_numeric'] = df['value'].apply(parse_score)
    df = df.sort_values(by='score_numeric', ascending=False)

    # Categorize
    general_merch = []
    ip_infringing = []

    for _, row in df.iterrows():
        query = row['query']
        score = row['value']
        idea = generate_idea(query)

        entry = f"| {query} | {score} | {idea} |"

        if is_ip_infringing(query):
            ip_infringing.append(entry)
        else:
            general_merch.append(entry)

    return general_merch, ip_infringing

def update_markdown(general_merch, ip_infringing):
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    header = "# Google Trends Merch Opportunities\n\n"

    if os.path.exists('trends.md'):
        with open('trends.md', 'r') as f:
            content = f.read()
            if f"## Trends for {date_str}" in content:
                print(f"Trends for {date_str} already exist. Skipping.")
                return
    else:
        content = header

    new_content = f"## Trends for {date_str}\n\n"

    new_content += "### General Merch Opportunities\n"
    new_content += "| Keyword | Score | Why/Idea |\n"
    new_content += "| :--- | :--- | :--- |\n"
    if general_merch:
        new_content += "\n".join(general_merch) + "\n\n"
    else:
        new_content += "| None found | - | - |\n\n"

    new_content += "### Potential IP Infringing Opportunities\n"
    new_content += "| Keyword | Score | Why/Idea |\n"
    new_content += "| :--- | :--- | :--- |\n"
    if ip_infringing:
        new_content += "\n".join(ip_infringing) + "\n\n"
    else:
        new_content += "| None found | - | - |\n\n"

    # Prepend new content after the header
    if content.startswith(header):
        body = content[len(header):]
        updated_content = header + new_content + body
    else:
        updated_content = header + new_content + content

    with open('trends.md', 'w') as f:
        f.write(updated_content)
    print("trends.md updated successfully.")

if __name__ == "__main__":
    results = process_trends()
    if results:
        update_markdown(*results)
    else:
        # If no new trends, we might still want to ensure trends.md exists
        if not os.path.exists('trends.md'):
            with open('trends.md', 'w') as f:
                f.write("# Google Trends Merch Opportunities\n\n")
