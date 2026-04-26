import time
import pandas as pd
from pytrends.request import TrendReq
from datetime import datetime
import re
import os

# Blacklist of known brands/IPs to flag potential infringement
IP_BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "taylor swift", "bts",
    "michael jackson", "micheal jackson", "nba", "nfl", "mlb", "nhl", "nintendo", "pokemon",
    "harry potter", "nasa", "hellstar", "ysl", "gucci", "prada", "louis vuitton",
    "koningsdag", "oranje", "higgins", "wwe", "kanye", "drake", "notre dame"
]

# Irrelevant terms that don't represent a direct merch opportunity
IRRELEVANT_TERMS = [
    "meaning", "definition", "how to", "why", "iron", "near me", "template",
    "mockup", "tee times", "tee time", "tee off", "graphic tee", "essential tee",
    "vintage tee", "oversized tee", "plain shirt", "blank shirt"
]

APPAREL_TERMS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]

def fetch_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    seed_keywords = APPAREL_TERMS
    all_rising_queries = []

    for keyword in seed_keywords:
        print(f"Fetching trends for: {keyword}")
        try:
            pytrends.build_payload([keyword], cat=0, timeframe='now 7-d', geo='', gprop='')
            related_queries = pytrends.related_queries()

            if keyword in related_queries:
                rising = related_queries[keyword]['rising']
                if rising is not None and not rising.empty:
                    # Filter for long-tail keywords (at least 2 words)
                    rising = rising[rising['query'].str.split().str.len() > 1]
                    # Filter for keywords that actually contain apparel terms
                    apparel_pattern = '|'.join(APPAREL_TERMS)
                    rising = rising[rising['query'].str.contains(apparel_pattern, case=False, na=False)]
                    all_rising_queries.append(rising)

            time.sleep(2)
        except Exception as e:
            print(f"Error fetching trends for {keyword}: {e}")
            if "429" in str(e):
                print("Rate limited. Sleeping for a bit...")
                time.sleep(10)

    if all_rising_queries:
        combined_df = pd.concat(all_rising_queries).drop_duplicates(subset=['query'])
        return combined_df
    return pd.DataFrame()

def is_ip_infringing(query):
    query_lower = query.lower()
    for brand in IP_BLACKLIST:
        if brand in query_lower:
            return True
    return False

def is_irrelevant(query):
    query_lower = query.lower()
    for term in IRRELEVANT_TERMS:
        if term in query_lower:
            return True
    return False

def generate_idea(query):
    # Simple idea generation: extract the non-apparel part and suggest a design
    query_lower = query.lower()
    concept = query_lower
    # Replace longer terms first to avoid partial replacement (e.g., 't-shirt' before 'shirt')
    sorted_apparel = sorted(APPAREL_TERMS, key=len, reverse=True)
    for term in sorted_apparel:
        concept = concept.replace(term, "").strip()

    # Clean up multiple spaces
    concept = re.sub(' +', ' ', concept)

    if not concept:
        return "Generic design based on search term."

    return f"Design featuring '{concept.title()}'. This is a trending niche topic. The internet is likely looking for unique, artist-driven interpretations of this specific theme."

def format_as_markdown_table(df):
    if df.empty:
        return "No opportunities found."

    # Ensure scores are formatted nicely (some might be 'Breakout')
    df['display_value'] = df['value'].apply(lambda x: f"**{x}**" if x == 'Breakout' or (isinstance(x, (int, float)) and x > 1000) else str(x))

    # Add Idea column
    df['idea'] = df['query'].apply(generate_idea)

    # Sort by score (treating 'Breakout' as very high)
    def sort_key(val):
        if val == 'Breakout': return 999999
        try:
            return int(val)
        except:
            return 0

    df['sort_val'] = df['value'].apply(sort_key)
    df = df.sort_values(by='sort_val', ascending=False)

    header = "| Keyword | Score | Why/Idea |\n| :--- | :--- | :--- |\n"
    rows = ""
    for _, row in df.iterrows():
        rows += f"| {row['query']} | {row['display_value']} | {row['idea']} |\n"

    return header + rows

def update_trends_file(general_table, ip_table):
    today = datetime.now().strftime("%Y-%m-%d")
    new_content = f"## {today}\n\n"
    new_content += "### General Merch Opportunities\n\n"
    new_content += general_table + "\n\n"
    new_content += "### Potential IP Infringing Opportunities\n\n"
    new_content += ip_table + "\n\n"
    new_content += "---\n\n"

    if os.path.exists("trends.md"):
        with open("trends.md", "r") as f:
            existing_content = f.read()
    else:
        existing_content = ""

    # Prepend new content
    # If the date already exists, we might want to skip or update,
    # but for simplicity we'll just prepend.
    if f"## {today}" in existing_content:
        print(f"Trends for {today} already exist in trends.md. Skipping file update.")
        return

    full_content = "# Google Trends Merch Opportunities\n\n" + new_content + existing_content.replace("# Google Trends Merch Opportunities\n\n", "")

    with open("trends.md", "w") as f:
        f.write(full_content)
    print("trends.md updated.")

def main():
    df = fetch_trends()
    if not df.empty:
        # Filter out irrelevant terms
        df = df[~df['query'].apply(is_irrelevant)]

        # Split into general and potential IP infringing
        df['is_ip'] = df['query'].apply(is_ip_infringing)

        general_df = df[~df['is_ip']].copy()
        ip_df = df[df['is_ip']].copy()

        general_table = format_as_markdown_table(general_df)
        ip_table = format_as_markdown_table(ip_df)

        update_trends_file(general_table, ip_table)
    else:
        print("No trends found today.")

if __name__ == "__main__":
    main()
