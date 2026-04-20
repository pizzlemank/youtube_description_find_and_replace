import pandas as pd
from pytrends.request import TrendReq
import time
from datetime import datetime
import os
import re

# Configuration
KEYWORDS = ["tshirt", "shirt", "tank top", "merch", "tee"]
APPAREL_TERMS = ["shirt", "tshirt", "tank top", "tanktop", "tee", "merch"]
BRAND_BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "bieber", "beiber",
    "taylor swift", "michael jackson", "one piece", "popeyes", "coachella",
    "anime", "netflix", "mickey", "trump", "biden", "nba", "nfl", "mlb", "nhl",
    "pokemon", "nintendo", "sony", "playstation", "xbox", "nasa", "hellstar",
    "karol g", "bruno mars", "sabrina carpenter", "billie eilish", "olivia rodrigo",
    "noah kahan", "frank ocean", "mashtag brady", "aldi", "morbid podcast", "ysl",
    "koningsdag", "oranje"
]
EXCLUDE_KEYWORDS = ["meaning", "definition", "how to", "why", "iron", "near me", "template", "mockup", "tee times", "tee time", "tee off"]

def get_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    all_rising = []

    for kw in KEYWORDS:
        print(f"Fetching trends for: {kw}")
        retries = 3
        while retries > 0:
            try:
                pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='', gprop='')
                related_queries = pytrends.related_queries()

                if kw in related_queries and related_queries[kw]['rising'] is not None:
                    rising = related_queries[kw]['rising']
                    all_rising.append(rising)

                time.sleep(2) # Avoid rate limiting
                break
            except Exception as e:
                print(f"Error fetching {kw}: {e}")
                if "429" in str(e):
                    print("Rate limited. Waiting 10s...")
                    time.sleep(10)
                    retries -= 1
                else:
                    break

    if not all_rising:
        return pd.DataFrame()

    df = pd.concat(all_rising).drop_duplicates(subset=['query'])
    return df

def is_long_tail_apparel(query):
    query = query.lower()
    # Check if it has at least 2 words
    if len(query.split()) < 2:
        return False

    # Check if it contains apparel terms
    if any(term in query for term in APPAREL_TERMS):
        return True

    return False

def contains_excluded(query):
    query = query.lower()
    return any(ex in query for ex in EXCLUDE_KEYWORDS)

def is_potential_ip(query):
    query = query.lower()
    return any(brand in query for brand in BRAND_BLACKLIST)

def generate_idea(query):
    query_clean = query.lower()
    for term in ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee"]:
        query_clean = query_clean.replace(term, "").strip()

    query_clean = re.sub(' +', ' ', query_clean) # remove double spaces

    return f"Design featuring '{query_clean}' aesthetic. High interest in {query} suggests market demand for this specific niche."

def format_table(df):
    if df.empty:
        return "No trends found for this period."

    lines = ["| Keyword | Score | Why / Idea |", "| --- | --- | --- |"]
    for _, row in df.iterrows():
        idea = generate_idea(row['query'])
        # Handle 'Breakout' score which is a string
        score = row['value']
        lines.append(f"| {row['query']} | {score} | {idea} |")

    return "\n".join(lines)

def main():
    print("Starting Trends Crawler...")
    df = get_trends()

    if df.empty:
        print("No data retrieved.")
        return

    # Filter for long-tail apparel
    df = df[df['query'].apply(is_long_tail_apparel)]

    # Filter out excluded keywords
    df = df[~df['query'].apply(contains_excluded)]

    # Separate IP infringing
    ip_df = df[df['query'].apply(is_potential_ip)]
    general_df = df[~df['query'].apply(is_potential_ip)]

    # Sort by score (Breakout is usually represented as a very high number or string)
    def sort_key(val):
        if isinstance(val, str) and val.lower() == 'breakout':
            return 999999
        try:
            return int(val)
        except:
            return 0

    if not general_df.empty:
        general_df = general_df.assign(sort_val=general_df['value'].apply(sort_key))
        general_df = general_df.sort_values(by='sort_val', ascending=False).drop(columns=['sort_val'])

    if not ip_df.empty:
        ip_df = ip_df.assign(sort_val=ip_df['value'].apply(sort_key))
        ip_df = ip_df.sort_values(by='sort_val', ascending=False).drop(columns=['sort_val'])

    date_str = datetime.now().strftime("%Y-%m-%d")

    new_content = f"## {date_str}\n\n"
    new_content += "### General Merch Opportunities\n"
    new_content += format_table(general_df) + "\n\n"
    new_content += "### Potential IP Infringing Opportunities\n"
    new_content += format_table(ip_df) + "\n\n"
    new_content += "---\n\n"

    # Read existing content
    existing_content = ""
    if os.path.exists("trends.md"):
        # Check if today's entry already exists to avoid duplicates if run multiple times
        with open("trends.md", "r") as f:
            existing_content = f.read()
            if f"## {date_str}" in existing_content:
                print("Entry for today already exists. Skipping update.")
                return

    with open("trends.md", "w") as f:
        f.write("# Print-on-Demand Trends\n\n" + new_content + existing_content.replace("# Print-on-Demand Trends\n\n", ""))

    print(f"Successfully updated trends.md for {date_str}")

if __name__ == "__main__":
    main()
