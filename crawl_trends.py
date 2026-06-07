import pandas as pd
from pytrends.request import TrendReq
import time
from datetime import datetime
import os
import re
import sys

# IP Blacklist
IP_BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "taylor swift", "bts",
    "michael jackson", "nba", "wnba", "nfl", "mlb", "nhl", "nintendo", "pokemon",
    "harry potter", "nasa", "hellstar", "ysl", "gucci", "prada", "louis vuitton",
    "arsenal", "real madrid", "liverpool", "man city", "chelsea", "bayern", "barcelona",
    "knicks", "lakers", "celtics", "warriors", "bulls", "amiri", "trapstar", "corteiz",
    "sp5der", "minus two", "syna world", "harry styles", "gracie abrams", "daniel caesar",
    "bad bunny", "billie eilish", "drake", "kanye", "travis scott", "bruno mars",
    "hello kitty", "sanrio", "nascar", "f1", "mercedes", "ferrari", "red bull",
    "toy story", "psg", "asap rocky", "megan moroney", "sean john", "morgan wallen",
    "spurs", "rcb", "snipes", "asos", "pattie gonia", "wingstop", "madewell", "carhartt"
]

# Non-commercial or irrelevant keywords to filter out
EXCLUDE_KEYWORDS = [
    "meaning", "definition", "how to", "why", "iron", "near me", "template", "mockup",
    "tee times", "tee time", "tee off", "graphic tee", "essential tee", "vintage tee",
    "oversized tee", "plain shirt", "blank shirt", "kaffee", "rezepte", "bh für", "bra for",
    "tutorial"
]

APPAREL_KEYWORDS = [
    "tshirt", "t-shirt", "t shirt", "shirt", "tank top", "tanktop",
    "tee", "merch", "tshirts", "t-shirts", "shirts", "tees"
]

def is_ip_infringing(query):
    query_lower = query.lower()
    for ip in IP_BLACKLIST:
        if ip in query_lower:
            return True
    return False

def generate_idea(query):
    query_lower = query.lower()

    if "funny" in query_lower:
        return f"Humorous design concept based on '{query}'. Focus on clever typography."
    if "vintage" in query_lower:
        return f"Retro/Vintage style design. Use distressed textures and muted colors."
    if "aesthetic" in query_lower:
        return f"Aesthetic/Minimalist design. Target Gen-Z/TikTok trends."

    # Default idea generator
    clean_query = query_lower
    # Sort by length descending to replace longer phrases first
    sorted_keywords = sorted(APPAREL_KEYWORDS, key=len, reverse=True)
    for kw in sorted_keywords:
        clean_query = clean_query.replace(kw, "").strip()

    clean_query = re.sub(' +', ' ', clean_query).strip()

    if not clean_query:
        return f"Trending apparel search for '{query}'. High interest niche."

    return f"Design concept: '{clean_query}'. Rising interest in this specific apparel niche."

def fetch_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    seed_keywords = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]

    all_rising_queries = []

    for kw in seed_keywords:
        print(f"Fetching trends for: {kw}")
        retries = 3
        while retries > 0:
            try:
                # Use a smaller timeframe if needed, but 'now 7-d' is usually good for rising trends
                pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='', gprop='')
                related_queries = pytrends.related_queries()

                if kw in related_queries and related_queries[kw]['rising'] is not None:
                    rising = related_queries[kw]['rising']
                    all_rising_queries.append(rising)
                break
            except Exception as e:
                print(f"Error fetching {kw}: {e}")
                if "429" in str(e):
                    print("Rate limited. Sleeping for 60s...")
                    time.sleep(60)
                    retries -= 1
                else:
                    break

        time.sleep(5)

    if not all_rising_queries:
        return pd.DataFrame()

    df = pd.concat(all_rising_queries).drop_duplicates(subset=['query'])

    # Filtering
    # 1. Long tail (2+ words)
    df = df[df['query'].str.split().str.len() >= 2]

    # 2. Must contain an apparel keyword
    pattern = '|'.join([re.escape(k) for k in APPAREL_KEYWORDS])
    df = df[df['query'].str.contains(pattern, case=False, na=False)]

    # 3. Exclude very generic ones
    df = df[~df['query'].str.lower().isin([k.lower() for k in APPAREL_KEYWORDS])]

    # 4. Exclude irrelevant keywords (like golf "tee times")
    exclude_pattern = '|'.join([re.escape(k) for k in EXCLUDE_KEYWORDS])
    df = df[~df['query'].str.contains(exclude_pattern, case=False, na=False)]

    # 5. Vietnamese "là gì" (what is) often appears in trends but isn't a merch opportunity
    df = df[~df['query'].str.contains("là gì", case=False, na=False)]

    # 6. Categorize
    df['is_ip'] = df['query'].apply(is_ip_infringing)
    df['idea'] = df['query'].apply(generate_idea)

    return df

def update_trends_md(df):
    today = datetime.now().strftime("%Y-%m-%d")
    filename = "trends.md"

    if df.empty:
        print("No new trends to add today.")
        header_check = f"## {today}"
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                if header_check in f.read():
                    return
        content = f"## {today}\n\nNo significant new trends found today.\n\n"
    else:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                existing_content = f.read()
            if f"## {today}" in existing_content:
                print(f"Trends for {today} already exist in {filename}. Skipping update.")
                return
        else:
            existing_content = "# Google Trends Merch Opportunities\n\nThis file tracks daily Google Trends for T-shirt and apparel merchandise opportunities.\n\n"

        general_df = df[~df['is_ip']].copy()
        ip_df = df[df['is_ip']].copy()

        content = f"## {today}\n\n"

        def sort_val(val):
            if val == 'Breakout':
                return 9999
            try:
                if isinstance(val, (int, float)):
                    return int(val)
                clean_val = str(val).replace('+', '').replace(',', '')
                return int(clean_val)
            except:
                return 0

        if not general_df.empty:
            content += "### General Merch Opportunities\n\n"
            content += "| Keyword | Score | Why/Idea |\n"
            content += "| :--- | :--- | :--- |\n"
            general_df['sort_score'] = general_df['value'].apply(sort_val)
            for _, row in general_df.sort_values(by='sort_score', ascending=False).iterrows():
                content += f"| {row['query']} | {row['value']} | {row['idea']} |\n"
            content += "\n"

        if not ip_df.empty:
            content += "### Potential IP Infringing Opportunities\n\n"
            content += "| Keyword | Score | Why/Idea |\n"
            content += "| :--- | :--- | :--- |\n"
            ip_df['sort_score'] = ip_df['value'].apply(sort_val)
            for _, row in ip_df.sort_values(by='sort_score', ascending=False).iterrows():
                content += f"| {row['query']} | {row['value']} | {row['idea']} |\n"
            content += "\n"

    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    else:
        lines = ["# Google Trends Merch Opportunities\n", "\n", "This file tracks daily Google Trends for T-shirt and apparel merchandise opportunities.\n", "\n"]

    insert_idx = 0
    for i, line in enumerate(lines):
        if line.startswith("# "):
            insert_idx = i + 1
            while insert_idx < len(lines) and not lines[insert_idx].startswith("## "):
                if lines[insert_idx].strip() == "" and insert_idx + 1 < len(lines) and lines[insert_idx+1].startswith("## "):
                    break
                insert_idx += 1
            break

    new_content_lines = [line + "\n" for line in content.split("\n")]
    if insert_idx < len(lines) and lines[insert_idx].strip() != "":
         new_content_lines.append("\n")

    final_lines = lines[:insert_idx] + new_content_lines + lines[insert_idx:]

    with open(filename, 'w', encoding='utf-8') as f:
        f.writelines(final_lines)

if __name__ == "__main__":
    try:
        df = fetch_trends()
        update_trends_md(df)
        print("Done successfully.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)
