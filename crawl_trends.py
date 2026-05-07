import time
import datetime
import os
import pandas as pd
import numpy as np
from pytrends.request import TrendReq

# Configuration
KEYWORDS = ['tshirt', 't-shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch']
TIMEFRAME = 'now 7-d'
TRENDS_FILE = 'trends.md'

BRAND_BLACKLIST = [
    'disney', 'marvel', 'star wars', 'nike', 'adidas', 'taylor swift', 'bts',
    'michael jackson', 'nba', 'nfl', 'mlb', 'nhl', 'nintendo', 'pokemon',
    'harry potter', 'nasa', 'hellstar', 'ysl', 'gucci', 'prada', 'louis vuitton',
    'koningsdag', 'oranje', 'higgins', 'wwe', 'kanye', 'drake', 'notre dame',
    'ariana grande', 'george strait', 'olivia dean', 'conan gray', 'man utd',
    'lidl', 'm&s', 'mnet', 'amc', 'murder drones', 'luke combs', 'ohio state',
    'ufc', 'f1', 'nascar', 'sanrio', 'hello kitty', 'stussy', 'mclaren',
    'deftones', 'cleetus mcfarland', 'the neighbourhood', 'bring me the horizon',
    'khan asadi', 'lyrebird', 'anthropologie', 'carson hocevar', 'rihanna',
    'morgan wallen', 'valorant', 'kentucky derby', 'victoria beckham', 'kimi antonelli'
]

def get_pytrends():
    return TrendReq(hl='en-US', tz=360)

def fetch_rising_queries(pytrends, kw):
    for attempt in range(3):
        try:
            # Re-initialize TrendReq might help with sessions
            pytrends = TrendReq(hl='en-US', tz=360)
            pytrends.build_payload([kw], cat=0, timeframe=TIMEFRAME, geo='', gprop='')
            related = pytrends.related_queries()
            if kw in related and related[kw]['rising'] is not None:
                return related[kw]['rising']
            return None
        except Exception as e:
            print(f"Error fetching for {kw}: {e}. Retrying in {attempt * 10 + 5}s...")
            time.sleep(attempt * 10 + 5)
    return None

def is_ip_infringing(query):
    query_lower = query.lower()
    for brand in BRAND_BLACKLIST:
        if brand in query_lower:
            return True
    return False

def generate_idea(query):
    q = query.lower()
    # Replace the most specific terms first
    for term in ['t-shirt', 'tshirt', 't shirt', 'tank top', 'tanktop', 'shirt', 'tee']:
        if term in q:
            concept = q.replace(term, '').strip()
            if concept:
                # Clean up multiple spaces
                concept = ' '.join(concept.split())
                return f"Design featuring '{concept.title()}'. This is trending as a specific {term} search."
    return "Trend-based design. People are searching for this specific term."

def main():
    pytrends = get_pytrends()
    all_data = []

    print("Starting crawl...")
    for kw in KEYWORDS:
        print(f"Fetching related queries for: {kw}")
        rising = fetch_rising_queries(pytrends, kw)
        if rising is not None:
            for index, row in rising.iterrows():
                query = row['query']
                score = row['value']

                # Criteria: long tail (2+ words)
                if len(query.split()) < 2:
                    continue

                # Check if it contains apparel keywords
                apparel_terms = ['shirt', 'tshirt', 't-shirt', 'tank top', 'tanktop', 'tee', 'merch']
                if not any(term in query.lower() for term in apparel_terms):
                    continue

                all_data.append({
                    'keyword': query,
                    'score': score,
                    'infringing': is_ip_infringing(query)
                })
        time.sleep(5) # Increased delay

    if not all_data:
        print("No new trends found or all requests failed.")
        # If we couldn't get data, don't update the file yet to avoid empty sections
        return

    # Deduplicate
    unique_data = {}
    for d in all_data:
        if d['keyword'] not in unique_data:
            unique_data[d['keyword']] = d

    unique_list = list(unique_data.values())

    # Sort by score (Breakout is a string, handle it)
    def sort_key(x):
        val = x['score']
        if isinstance(val, str) and val == 'Breakout':
            return 9999
        try:
            # Handle numpy types or strings
            if isinstance(val, (int, np.integer)):
                return int(val)
            return int(val)
        except:
            return 0

    sorted_data = sorted(unique_list, key=sort_key, reverse=True)

    general_merch = [d for d in sorted_data if not d['infringing']]
    ip_infringing = [d for d in sorted_data if d['infringing']]

    now = datetime.datetime.now().strftime("%Y-%m-%d")

    new_content = f"## {now}\n\n"

    new_content += "### General Merch Opportunities\n"
    new_content += "| keyword | score | Why/Idea |\n"
    new_content += "| :--- | :--- | :--- |\n"
    for d in general_merch:
        new_content += f"| {d['keyword']} | {d['score']} | {generate_idea(d['keyword'])} |\n"

    new_content += "\n### Potential IP Infringing Opportunities\n"
    new_content += "| keyword | score | Why/Idea |\n"
    new_content += "| :--- | :--- | :--- |\n"
    for d in ip_infringing:
        new_content += f"| {d['keyword']} | {d['score']} | {generate_idea(d['keyword'])} (POTENTIAL IP ISSUE) |\n"

    new_content += "\n---\n\n"

    # Read existing content
    if os.path.exists(TRENDS_FILE):
        with open(TRENDS_FILE, 'r') as f:
            existing_content = f.read()
            if f"## {now}" in existing_content:
                print(f"Data for {now} already exists in {TRENDS_FILE}. Skipping append.")
                return
    else:
        existing_content = "# Google Trends Merch Opportunities\n\nDaily crawl of Google Trends for T-shirt and Merch opportunities.\n\n"

    # Find the insertion point (after the header)
    header_marker = "Daily crawl of Google Trends for T-shirt and Merch opportunities.\n\n"
    marker_pos = existing_content.find(header_marker)

    if marker_pos != -1:
        insertion_point = marker_pos + len(header_marker)
        final_content = existing_content[:insertion_point] + new_content + existing_content[insertion_point:]
    else:
        # Fallback if header is different
        final_content = existing_content + "\n" + new_content

    with open(TRENDS_FILE, 'w') as f:
        f.write(final_content)

    print(f"Successfully updated {TRENDS_FILE}")

if __name__ == "__main__":
    main()
