import pandas as pd
from pytrends.request import TrendReq
import time
import os
from datetime import datetime
import re

# Initialize pytrends
pytrends = TrendReq(hl='en-US', tz=360)

KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]
APPAREL_TERMS = ["shirt", "tshirt", "t-shirt", "tank top", "tanktop", "tee", "merch"]
EXCLUDE_TERMS = [
    "meaning", "definition", "how to", "why", "iron", "near me", "template", "mockup",
    "tee times", "tee time", "tee off", "graphic tee", "essential tee", "vintage tee",
    "oversized tee", "plain shirt", "blank shirt", "kaffee", "rezepte", "bh für", "bra for",
    "tutorial", "là gì"
]

IP_BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "taylor swift", "bts", "michael jackson",
    "nba", "wnba", "nfl", "mlb", "nhl", "nintendo", "pokemon", "harry potter", "nasa",
    "hellstar", "ysl", "gucci", "prada", "louis vuitton", "arsenal", "real madrid", "liverpool",
    "man city", "chelsea", "bayern", "barcelona", "knicks", "lakers", "celtics", "warriors", "bulls",
    "amiri", "trapstar", "corteiz", "sp5der", "minus two", "syna world", "harry styles", "gracie abrams",
    "daniel caesar", "bad bunny", "billie eilish", "drake", "kanye", "travis scott", "bruno mars",
    "hello kitty", "sanrio", "nascar", "f1", "mercedes", "ferrari", "red bull", "toy story", "psg",
    "asap rocky", "megan moroney", "sean john", "morgan wallen", "spurs", "rcb", "snipes", "asos"
]

def fetch_trends_with_retry(kw, retries=3, delay=60):
    for i in range(retries):
        try:
            pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='', gprop='')
            related_queries = pytrends.related_queries()
            if kw in related_queries:
                return related_queries[kw]['rising']
            return None
        except Exception as e:
            print(f"Attempt {i+1} failed for {kw}: {e}")
            if "429" in str(e):
                print(f"Rate limited. Waiting {delay} seconds...")
                time.sleep(delay)
            else:
                break
    return None

def filter_queries(df):
    if df.empty:
        return df

    # 1. Long tail (2+ words)
    df = df[df['query'].str.split().str.len() >= 2].copy()

    # 2. Contains apparel term
    df = df[df['query'].str.contains('|'.join(APPAREL_TERMS), case=False)]

    # 3. Exclude irrelevant terms
    df = df[~df['query'].str.contains('|'.join(EXCLUDE_TERMS), case=False)]

    # 4. Remove exact matches of seed keywords
    df = df[~df['query'].str.lower().isin([k.lower() for k in KEYWORDS])]

    # 5. Deduplicate
    df = df.drop_duplicates(subset=['query'])

    return df

def check_ip_infringement(query):
    query_lower = query.lower()
    for brand in IP_BLACKLIST:
        if brand in query_lower:
            return True
    return False

def generate_idea(query):
    # Basic idea generation logic: clean up the query to find the "concept"
    concept = query.lower()
    # Sort terms by length descending to replace "tank top" before "tank"
    sorted_terms = sorted(APPAREL_TERMS, key=len, reverse=True)
    for term in sorted_terms:
        # Use regex to replace whole words or common variations
        pattern = re.compile(rf'\b{term}s?\b', re.IGNORECASE)
        concept = pattern.sub("", concept).strip()

    concept = re.sub(' +', ' ', concept) # remove extra spaces

    if not concept:
        concept = query

    return f"Design featuring '{concept}'. Capture interest from this trending search."

def format_row(row):
    idea = generate_idea(row['query'])
    return f"| {row['query']} | {row['value']} | {idea} |"

def update_trends_file(df):
    if df.empty:
        print("No new trends to add.")
        return

    today = datetime.now().strftime("%Y-%m-%d")

    def sort_key(val):
        if val == 'Breakout':
            return 999999
        try:
            return int(val)
        except:
            return 0

    df['sort_val'] = df['value'].apply(sort_key)

    general_df = df[~df['is_ip_infringing']].sort_values(by='sort_val', ascending=False)
    ip_df = df[df['is_ip_infringing']].sort_values(by='sort_val', ascending=False)

    header = f"## {today}\n\n"
    content = header

    if not general_df.empty:
        content += "### General Merch Opportunities\n\n"
        content += "| Keyword | Score | Why/Idea/Market |\n"
        content += "| :--- | :--- | :--- |\n"
        for _, row in general_df.iterrows():
            content += format_row(row) + "\n"
        content += "\n"

    if not ip_df.empty:
        content += "### Potential IP Infringing Opportunities\n\n"
        content += "| Keyword | Score | Why/Idea/Market |\n"
        content += "| :--- | :--- | :--- |\n"
        for _, row in ip_df.iterrows():
            content += format_row(row) + "\n"
        content += "\n"

    content += "---\n\n"

    filename = "trends.md"
    title = "# Merch Trends\n\n"

    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            existing_content = f.read()

        if f"## {today}" in existing_content:
            print(f"Trends for {today} already exist in {filename}. Skipping update.")
            return

        if existing_content.startswith("# Merch Trends"):
            new_content = title + content + existing_content[len(title):]
        else:
            new_content = title + content + existing_content
    else:
        new_content = title + content

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(new_content)

def fetch_all_trends():
    all_rising_queries = []

    # Using a set to deduplicate as we fetch
    seen_queries = set()

    for kw in KEYWORDS:
        print(f"Fetching trends for: {kw}")
        rising = fetch_trends_with_retry(kw)
        if rising is not None:
            all_rising_queries.append(rising)

        time.sleep(5)

    if not all_rising_queries:
        return pd.DataFrame()

    df = pd.concat(all_rising_queries, ignore_index=True)
    df = filter_queries(df)

    if not df.empty:
        df['is_ip_infringing'] = df['query'].apply(check_ip_infringement)

    return df

if __name__ == "__main__":
    df = fetch_all_trends()
    update_trends_file(df)
    print("trends.md updated.")
