import time
import datetime
import pandas as pd
from pytrends.request import TrendReq
import numpy as np
import os
import re

# Brand blacklist to flag potential IP infringement
BRAND_BLACKLIST = [
    'disney', 'marvel', 'star wars', 'nike', 'adidas', 'taylor swift', 'bts',
    'michael jackson', 'nba', 'wnba', 'nfl', 'mlb', 'nhl', 'nintendo', 'pokemon',
    'harry potter', 'nasa', 'hellstar', 'ysl', 'gucci', 'prada', 'louis vuitton',
    'koningsdag', 'oranje', 'higgins', 'wwe', 'kanye', 'drake', 'notre dame',
    'ariana grande', 'george strait', 'olivia dean', 'conan gray', 'man utd',
    'lidl', 'm&s', 'mnet', 'amc', 'murder drones', 'luke combs', 'ohio state',
    'ufc', 'f1', 'nascar', 'sanrio', 'hello kitty', 'stussy', 'mclaren',
    'deftones', 'cleetus mcfarland', 'the neighbourhood', 'bring me the horizon',
    'khan asadi', 'lyrebird', 'anthropologie', 'carson hocevar', 'rihanna',
    'morgan wallen', 'valorant', 'kentucky derby', 'victoria beckham',
    'kimi antonelli', 'no doubt', 'bad omens', 'good mythical morning',
    'riley green', 'ella langley', 'candace owens', 'g59', 'grey59',
    'greyfivenine', 'of the trees'
]

EXCLUDED_TERMS = [
    'meaning', 'definition', 'how to', 'why', 'iron', 'near me',
    'template', 'mockup', 'tee times', 'tee time', 'tee off',
    'graphic tee', 'essential tee', 'vintage tee', 'oversized tee',
    'plain shirt', 'blank shirt', 'là gì'
]

def get_pytrends_client():
    return TrendReq(hl='en-US', tz=360)

def fetch_rising_queries(pytrends, kw_list):
    retries = 3
    for i in range(retries):
        try:
            pytrends.build_payload(kw_list, cat=0, timeframe='now 7-d', geo='', gprop='')
            related_queries = pytrends.related_queries()
            return related_queries
        except Exception as e:
            print(f"Error fetching data for {kw_list}: {e}. Retrying {i+1}/{retries}...")
            time.sleep(5 * (i + 1))
    return None

def is_ip_infringing(query):
    query_lower = query.lower()
    for brand in BRAND_BLACKLIST:
        if brand in query_lower:
            return True
    return False

def generate_idea(query):
    # Clean up the query to extract a core concept
    concept = query.lower()
    # Remove apparel terms
    for term in ['t-shirt', 'tshirt', 't shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch']:
        concept = concept.replace(term, '')
    concept = concept.strip()
    concept = re.sub(' +', ' ', concept)

    if not concept:
        return "Generic apparel search. Look for trending niches or aesthetic styles."

    return f"Trending concept: '{concept.title()}'. Design idea: Create a unique illustration or typography based on this theme. Check if there are specific viral moments or quotes associated with it."

def process_trends(df):
    results = []
    for _, row in df.iterrows():
        query = row['query']
        score = row['value']

        # Filter for long tail (at least 2 words)
        if len(query.split()) < 2:
            continue

        # Filter out excluded terms
        if any(term in query.lower() for term in EXCLUDED_TERMS):
            continue

        ip_infringing = is_ip_infringing(query)
        idea = generate_idea(query)

        results.append({
            'keyword': query,
            'score': score,
            'idea': idea,
            'ip_infringing': ip_infringing
        })
    return results

def update_trends_md(results):
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    general_items = [r for r in results if not r['ip_infringing']]
    ip_items = [r for r in results if r['ip_infringing']]

    # Sort by score descending
    def get_score_val(x):
        if isinstance(x, str) and x.lower() == 'breakout':
            return 9999
        try:
            return int(x)
        except:
            return 0

    general_items.sort(key=lambda x: get_score_val(x['score']), reverse=True)
    ip_items.sort(key=lambda x: get_score_val(x['score']), reverse=True)

    new_content = f"## {today}\n\n"

    new_content += "### General Merch Opportunities\n"
    if general_items:
        new_content += "| Keyword | Score | Why/Idea |\n"
        new_content += "| --- | --- | --- |\n"
        for item in general_items:
            new_content += f"| {item['keyword']} | {item['score']} | {item['idea']} |\n"
    else:
        new_content += "No new general opportunities found today.\n"

    new_content += "\n### Potential IP Infringing Opportunities\n"
    if ip_items:
        new_content += "| Keyword | Score | Why/Idea |\n"
        new_content += "| --- | --- | --- |\n"
        for item in ip_items:
            new_content += f"| {item['keyword']} | {item['score']} | {item['idea']} |\n"
    else:
        new_content += "No new potential IP infringing opportunities found today.\n"

    new_content += "\n---\n\n"

    filename = 'trends.md'
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            old_content = f.read()

        # Avoid duplicate updates for the same day if run multiple times
        if f"## {today}" in old_content:
            print(f"Trends for {today} already exist in {filename}. Skipping update.")
            return

        with open(filename, 'w') as f:
            f.write(new_content + old_content)
    else:
        with open(filename, 'w') as f:
            f.write("# Google Trends Merch Opportunities\n\n" + new_content)

def main():
    pytrends = get_pytrends_client()
    seed_keywords = ['tshirt', 't-shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch']

    all_rising_results = []
    unique_queries = set()

    for seed in seed_keywords:
        print(f"Fetching trends for: {seed}")
        results = fetch_rising_queries(pytrends, [seed])
        if results and seed in results:
            rising = results[seed]['rising']
            if rising is not None:
                # Deduplicate before appending
                for _, row in rising.iterrows():
                    if row['query'] not in unique_queries:
                        all_rising_results.append(pd.DataFrame([row]))
                        unique_queries.add(row['query'])
        time.sleep(2)

    if all_rising_results:
        df = pd.concat(all_rising_results)
        print(f"Found {len(df)} unique rising queries.")
        processed_results = process_trends(df)
        update_trends_md(processed_results)
        print("trends.md updated successfully.")
    else:
        print("No rising queries found.")

if __name__ == "__main__":
    main()
