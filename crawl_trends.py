import time
import pandas as pd
from pytrends.request import TrendReq
from datetime import datetime
import os
import re

# IP Blacklist (partial list, should be expanded)
BLACKLIST = [
    "disney", "marvel", "star wars", "starwars", "nike", "adidas", "bieber",
    "taylor swift", "michael jackson", "one piece", "popeyes", "coachella",
    "netflix", "mickey", "mickey mouse", "trump", "biden", "nba", "nfl", "mlb", "nhl",
    "pokemon", "nintendo", "sony", "playstation", "xbox", "nasa", "hellstar",
    "karol g", "bruno mars", "sabrina carpenter", "billie eilish", "billie",
    "olivia rodrigo", "noah kahan", "frank ocean", "mashtag brady", "aldi",
    "morbid podcast", "ysl", "koningsdag", "oranje", "higgins", "kelce", "mahomes",
    "stroud", "wwe", "the weeknd", "chrome hearts", "stussy", "vultures", "kanye"
]

APPAREL_KEYWORDS = ["shirt", "tshirt", "t-shirt", "tank top", "tanktop", "tee", "merch"]

def fetch_trends(seed_keywords):
    pytrends = TrendReq(hl='en-US', tz=360)
    all_rising = []

    for kw in seed_keywords:
        print(f"Fetching rising queries for: {kw}")
        retries = 3
        while retries > 0:
            try:
                # Use a smaller timeframe to get more recent "rising" trends
                pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='', gprop='')
                related_queries = pytrends.related_queries()
                rising = related_queries[kw]['rising']
                if rising is not None and not rising.empty:
                    rising['seed_keyword'] = kw
                    all_rising.append(rising)
                    print(f"  Found {len(rising)} rising queries.")
                else:
                    print(f"  No rising queries found for {kw}.")
                break
            except Exception as e:
                print(f"  Error fetching {kw}: {e}")
                if "429" in str(e):
                    print("  Rate limited. Sleeping for 10 seconds...")
                    time.sleep(10)
                    retries -= 1
                else:
                    break
        time.sleep(2)  # Delay between keywords

    if all_rising:
        # Sort by value (score) descending. Breakout is treated as 9999
        df = pd.concat(all_rising).drop_duplicates(subset='query')
        return df
    return pd.DataFrame()

def process_trends(df):
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    # Filter for long tail (at least 2 words)
    df = df[df['query'].str.split().str.len() >= 2].copy()

    # Ensure it contains one of our apparel keywords
    def contains_apparel(query):
        q = query.lower()
        return any(ak in q for ak in APPAREL_KEYWORDS)

    df = df[df['query'].apply(contains_apparel)].copy()

    # Filter out some noise
    noise_keywords = [
        'meaning', 'definition', 'how to', 'why', 'iron', 'near me',
        'template', 'mockup', 'tee times', 'tee time', 'tee off',
        'graphic tee', 'essential tee', 'vintage tee', 'oversized tee',
        'plain shirt', 'blank shirt'
    ]
    for nk in noise_keywords:
        df = df[~df['query'].str.contains(nk, case=False)]

    def is_ip_infringing(query):
        query_lower = query.lower()
        for brand in BLACKLIST:
            if brand in query_lower:
                return True
        return False

    def generate_idea(row):
        query = row['query']
        # Remove apparel keywords to see the core niche
        clean_query = query.lower()
        # Order matters: replace longer strings first
        for ak in sorted(APPAREL_KEYWORDS, key=len, reverse=True):
            clean_query = clean_query.replace(ak, "")

        clean_query = re.sub(' +', ' ', clean_query).strip()

        if not clean_query:
            return f"Generic {row['seed_keyword']} trend. Focus on quality and fit."

        return f"Rising interest in '{query}'. Good opportunity for a design focusing on '{clean_query}'. The market is looking for specific '{clean_query}' themed apparel."

    df['is_ip'] = df['query'].apply(is_ip_infringing)
    df['idea'] = df.apply(generate_idea, axis=1)

    # Convert 'Breakout' score to a high number for sorting
    def clean_score(val):
        if isinstance(val, str) and val == 'Breakout':
            return 9999
        try:
            return int(val)
        except:
            return 0

    df['score_num'] = df['value'].apply(clean_score)
    df = df.sort_values(by='score_num', ascending=False)

    general = df[~df['is_ip']]
    ip_infringing = df[df['is_ip']]

    return general, ip_infringing

def format_markdown_table(df):
    if df.empty:
        return "No opportunities found for this category today."

    header = "| Keyword | Score | Why/Idea |\n| :--- | :--- | :--- |\n"
    rows = ""
    for _, row in df.iterrows():
        rows += f"| {row['query']} | {row['value']} | {row['idea']} |\n"
    return header + rows

def update_trends_md(general, ip_infringing):
    date_str = datetime.now().strftime("%Y-%m-%d")

    new_content = f"## {date_str}\n\n"
    new_content += "### General Merch Opportunities\n\n"
    new_content += format_markdown_table(general) + "\n\n"
    new_content += "### Potential IP Infringing Opportunities\n\n"
    new_content += format_markdown_table(ip_infringing) + "\n\n"
    new_content += "---\n\n"

    if os.path.exists("trends.md"):
        with open("trends.md", "r") as f:
            old_content = f.read()
        # Check if we already updated today to avoid duplicates
        if f"## {date_str}" in old_content:
            print(f"Trends for {date_str} already exist in trends.md. Skipping update.")
            return

        # We want to prepend the new content after the main header
        if old_content.startswith("# Merch Opportunity Trends"):
            header_end = old_content.find("\n\n") + 2
            content = old_content[:header_end] + new_content + old_content[header_end:]
        else:
            content = new_content + old_content
    else:
        content = "# Merch Opportunity Trends\n\n" + new_content

    with open("trends.md", "w") as f:
        f.write(content)
    print("trends.md updated successfully.")

if __name__ == "__main__":
    seeds = APPAREL_KEYWORDS
    df = fetch_trends(seeds)
    if not df.empty:
        general, ip_infringing = process_trends(df)
        update_trends_md(general, ip_infringing)
    else:
        print("No data collected, trends.md not updated.")
