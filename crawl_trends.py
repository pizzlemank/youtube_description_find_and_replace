import time
import pandas as pd
from pytrends.request import TrendReq
import random
import re
from datetime import datetime
import os

IP_BLACKLIST = [
    "Disney", "Marvel", "Star Wars", "Nike", "Adidas", "Taylor Swift", "BTS", "Michael Jackson",
    "NBA", "WNBA", "NFL", "MLB", "NHL", "Nintendo", "Pokemon", "Harry Potter", "NASA",
    "Hellstar", "YSL", "Gucci", "Prada", "Louis Vuitton", "Arsenal", "Real Madrid",
    "Liverpool", "Man City", "Chelsea", "Bayern", "Barcelona", "Knicks", "Lakers",
    "Celtics", "Warriors", "Bulls", "Amiri", "Trapstar", "Corteiz", "Sp5der", "Minus Two",
    "Syna World", "Harry Styles", "Gracie Abrams", "Daniel Caesar", "Bad Bunny",
    "Billie Eilish", "Drake", "Kanye", "Travis Scott", "Bruno Mars", "Hello Kitty",
    "Sanrio", "NASCAR", "F1", "Mercedes", "Ferrari", "Red Bull", "Toy Story", "PSG",
    "ASAP Rocky", "Megan Moroney", "Sean John", "Morgan Wallen", "Spurs", "RCB", "Snipes",
    "ASOS", "Pattie Gonia", "Wingstop", "Ariana Grande", "Selena Gomez", "Carhartt",
    "Hazbin Hotel", "Digital Circus", "TADC", "Linkin Park", "Bad Omens", "Forrest Frank",
    "Malcolm Todd", "Böhse Onkelz", "Love Island", "Eternal Sunshine", "Madewell",
    "Anthropologie", "Glitch"
]

EXCLUDED_KEYWORDS = [
    'meaning', 'definition', 'how to', 'why', 'iron', 'near me', 'template', 'mockup',
    'tee times', 'tee time', 'tee off', 'graphic tee', 'essential tee', 'vintage tee',
    'oversized tee', 'plain shirt', 'blank shirt', 'kaffee', 'rezepte', 'bh für',
    'bra for', 'tutorial', 'là gì'
]

def check_ip_infringement(query):
    for term in IP_BLACKLIST:
        if re.search(rf'\b{re.escape(term)}\b', query, re.IGNORECASE):
            return True
    return False

def clean_and_filter_results(df):
    if df.empty:
        return df

    # Map 'Breakout' to 9999
    df['value'] = df['value'].apply(lambda x: 9999 if x == 'Breakout' else int(x))

    # Filter for long tail (2+ words)
    df = df[df['query'].str.split().str.len() >= 2]

    # Exclude exact matches or generic variations of seeds
    seeds = ['tshirt', 't shirt', 't-shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch', 'tees']
    df = df[~df['query'].str.lower().isin(seeds)]

    # Exclude non-commercial or irrelevant terms
    for term in EXCLUDED_KEYWORDS:
        df = df[~df['query'].str.contains(term, case=False, na=False)]

    # Deduplicate
    df = df.drop_duplicates(subset=['query'])

    # Sort by score
    df = df.sort_values(by='value', ascending=False)

    return df

def fetch_trends(keywords, timeframe='now 7-d'):
    pytrends = TrendReq(hl='en-US', tz=360)
    all_rising = []

    for kw in keywords:
        print(f"Fetching trends for: {kw}")
        retries = 3
        while retries > 0:
            try:
                pytrends.build_payload([kw], timeframe=timeframe)
                related_queries = pytrends.related_queries()

                if kw in related_queries and related_queries[kw]['rising'] is not None:
                    rising = related_queries[kw]['rising']
                    rising['seed'] = kw
                    all_rising.append(rising)

                # Success, break retry loop
                break
            except Exception as e:
                print(f"Error fetching {kw}: {e}")
                retries -= 1
                if retries > 0:
                    wait_time = 30 # Standard wait for 429
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"Failed to fetch trends for {kw} after retries.")

        # 5 second delay between keywords to avoid rate limiting
        time.sleep(5)

    if not all_rising:
        return pd.DataFrame()

    return pd.concat(all_rising, ignore_index=True)

def generate_idea(query):
    # Priorities: longer terms first
    apparel_terms = ['tshirts', 't-shirts', 'tank tops', 'tanktop', 'tshirt', 't-shirt', 'shirt', 'tee', 'merch']
    concept = query
    for term in apparel_terms:
        concept = re.sub(rf'\b{re.escape(term)}\b', '', concept, flags=re.IGNORECASE).strip()

    concept = re.sub(rf'\s+', ' ', concept)
    if not concept:
        concept = query

    return f"Trending design concept: {concept}. Consider a clean typography or illustrative style."

def update_trends_md(df, filepath='trends.md'):
    if df.empty:
        print("No new trends found.")
        return

    today = datetime.now().strftime('%Y-%m-%d')

    # Read existing content
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    else:
        lines = ["# Merch Trends\n"]

    # Check if today already exists
    if any(f"## {today}" in line for line in lines):
        print(f"Trends for {today} already exist in {filepath}. Skipping.")
        return

    # Split into General and IP
    gen_df = df[df['is_ip'] == False]
    ip_df = df[df['is_ip'] == True]

    new_content = [f"## {today}\n\n"]

    if not gen_df.empty:
        new_content.append("### General Merch Opportunities\n\n")
        new_content.append("| keyword | score | Why/Idea |\n")
        new_content.append("| :--- | :--- | :--- |\n")
        for _, row in gen_df.iterrows():
            new_content.append(f"| {row['query']} | {row['value']} | {row['idea']} |\n")
        new_content.append("\n")

    if not ip_df.empty:
        new_content.append("### Potential IP Infringing Opportunities\n\n")
        new_content.append("| keyword | score | Why/Idea |\n")
        new_content.append("| :--- | :--- | :--- |\n")
        for _, row in ip_df.iterrows():
            new_content.append(f"| {row['query']} | {row['value']} | {row['idea']} |\n")
        new_content.append("\n")

    # Keep the header, then prepend new content
    header = lines[0]
    rest = lines[1:]

    final_content = [header, "\n"] + new_content + rest

    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(final_content)
    print(f"Updated {filepath} with {len(df)} trends.")

if __name__ == "__main__":
    seeds = ['tshirt', 't-shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch']
    df = fetch_trends(seeds)
    df = clean_and_filter_results(df)

    if not df.empty:
        df['is_ip'] = df['query'].apply(check_ip_infringement)
        df['idea'] = df['query'].apply(generate_idea)
        update_trends_md(df)
    else:
        print("No results to process.")
