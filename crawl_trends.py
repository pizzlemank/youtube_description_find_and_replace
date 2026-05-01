import pandas as pd
from pytrends.request import TrendReq
import time
from datetime import datetime
import os
import re

# Configuration
KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]
BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "taylor swift", "bts",
    "michael jackson", "nba", "nfl", "mlb", "nhl", "nintendo", "pokemon",
    "harry potter", "nasa", "hellstar", "ysl", "gucci", "prada", "louis vuitton",
    "koningsdag", "oranje", "higgins", "wwe", "kanye", "drake", "notre dame",
    "ariana grande", "george strait", "olivia dean", "conan gray", "man utd",
    "lidl", "m&s", "mnet", "amc", "murder drones", "luke combs", "ohio state",
    "ufc", "f1", "nascar", "sanrio", "hello kitty"
]

EXCLUDE_TERMS = [
    "meaning", "definition", "how to", "why", "iron", "near me", "template",
    "mockup", "tee times", "tee time", "tee off", "graphic tee", "essential tee",
    "vintage tee", "oversized tee", "plain shirt", "blank shirt"
]

TRENDS_FILE = "trends.md"

def get_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    all_data = []

    for kw in KEYWORDS:
        print(f"Fetching trends for: {kw}")
        try:
            # Build payload with retry mechanism for rate limiting
            success = False
            retries = 3
            while not success and retries > 0:
                try:
                    pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='', gprop='')
                    success = True
                except Exception as e:
                    print(f"Error building payload for {kw}: {e}. Retrying...")
                    time.sleep(5)
                    retries -= 1

            if not success:
                continue

            related_queries = pytrends.related_queries()
            if kw in related_queries and related_queries[kw]['rising'] is not None:
                df = related_queries[kw]['rising']
                all_data.append(df)

            time.sleep(2) # Avoid aggressive rate limiting
        except Exception as e:
            print(f"Failed to fetch {kw}: {e}")

    if not all_data:
        return pd.DataFrame()

    return pd.concat(all_data).drop_duplicates(subset=['query'])

def filter_and_format(df):
    if df.empty:
        return [], []

    general_opportunities = []
    ip_infringing = []

    seen_queries = set()

    for _, row in df.iterrows():
        query = str(row['query']).lower()
        score = row['value']

        # Long tail check (2+ words)
        words = query.split()
        if len(words) < 2:
            continue

        # Check if it contains any of our seed terms
        if not any(term in query for term in KEYWORDS):
            continue

        # Exclude non-commercial terms
        if any(term in query for term in EXCLUDE_TERMS):
            continue

        if query in seen_queries:
            continue
        seen_queries.add(query)

        # Generate idea/why
        topic = query
        # Sort keywords by length descending to replace longer ones first (e.g. "t-shirt" before "shirt")
        for term in sorted(KEYWORDS, key=len, reverse=True):
            topic = re.sub(rf'\b{re.escape(term)}\b', '', topic).strip()
        topic = re.sub(' +', ' ', topic) # clean extra spaces

        idea = f"Design targeting '{topic}' niche. Rising interest indicates market demand for specific '{query}' styles."

        # Check IP infringement
        is_ip = any(brand in query for brand in BLACKLIST)

        item = {
            "keyword": query,
            "score": score,
            "idea": idea
        }

        if is_ip:
            ip_infringing.append(item)
        else:
            general_opportunities.append(item)

    # Sort by score (Breakout is usually string 'Breakout', pytrends might return it)
    def sort_key(x):
        val = x['score']
        if isinstance(val, str) and 'breakout' in val.lower():
            return 9999
        try:
            return int(val)
        except:
            return 0

    general_opportunities.sort(key=sort_key, reverse=True)
    ip_infringing.sort(key=sort_key, reverse=True)

    return general_opportunities, ip_infringing

def update_markdown(general, ip):
    today = datetime.now().strftime("%Y-%m-%d")

    new_content = f"## {today}\n\n"

    new_content += "### General Merch Opportunities\n"
    if general:
        new_content += "| keyword | score | Why/Idea |\n"
        new_content += "| :--- | :--- | :--- |\n"
        for item in general:
            new_content += f"| {item['keyword']} | {item['score']} | {item['idea']} |\n"
    else:
        new_content += "No new general opportunities found.\n"

    new_content += "\n### Potential IP Infringing Opportunities\n"
    if ip:
        new_content += "| keyword | score | Why/Idea |\n"
        new_content += "| :--- | :--- | :--- |\n"
        for item in ip:
            new_content += f"| {item['keyword']} | {item['score']} | {item['idea']} |\n"
    else:
        new_content += "No new potential IP infringing opportunities found.\n"

    new_content += "\n---\n\n"

    current_content = ""
    if os.path.exists(TRENDS_FILE):
        with open(TRENDS_FILE, "r") as f:
            current_content = f.read()

    # Check if we already updated today to avoid duplicates if run multiple times
    if f"## {today}" in current_content:
        print(f"Trends for {today} already exist in {TRENDS_FILE}. Skipping update.")
        return

    with open(TRENDS_FILE, "w") as f:
        f.write(new_content + current_content)

    print(f"Updated {TRENDS_FILE} with {len(general) + len(ip)} new trends.")

if __name__ == "__main__":
    print("Starting Trends Crawl...")
    trends_df = get_trends()
    gen, ip = filter_and_format(trends_df)
    update_markdown(gen, ip)
    print("Crawl Complete.")
