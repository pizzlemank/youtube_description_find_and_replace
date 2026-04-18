import datetime
import os
import time
import pandas as pd
from pytrends.request import TrendReq

# Configuration
SEED_KEYWORDS = ["tshirt", "shirt", "tank top", "merch", "tee"]
APPAREL_TERMS = ["tank top", "tanktop", "tshirt", "shirt", "merch", "tee"]
IP_BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "bieber", "beiber",
    "taylor swift", "michael jackson", "one piece", "popeyes", "coachella",
    "anime", "netflix", "mickey", "trump", "biden", "nba", "nfl", "mlb", "nhl",
    "pokemon", "nintendo", "sony", "playstation", "xbox", "nasa", "hellstar",
    "karol g", "bruno mars", "sabrina carpenter"
]

def get_rising_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    all_results = []

    for kw in SEED_KEYWORDS:
        print(f"Fetching trends for: {kw}")
        try:
            pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='', gprop='')
            related = pytrends.related_queries()
            if kw in related and related[kw]['rising'] is not None:
                df = related[kw]['rising']
                all_results.append(df)
            time.sleep(2) # Avoid rate limiting
        except Exception as e:
            print(f"Error fetching {kw}: {e}")
            if "429" in str(e):
                print("Rate limited. Sleeping for 10s...")
                time.sleep(10)

    if not all_results:
        return pd.DataFrame()

    return pd.concat(all_results).drop_duplicates(subset=['query'])

def filter_trends(df):
    if df.empty:
        return df

    # Long tail (2+ words)
    df = df[df['query'].str.split().str.len() >= 2]

    # Contains apparel term
    def contains_apparel(q):
        return any(term in q.lower() for term in APPAREL_TERMS)

    df = df[df['query'].apply(contains_apparel)]

    # Exclude obvious non-commercial/info searches
    exclude = ["meaning", "definition", "how to", "why", "iron", "near me", "template", "mockup", "tee times", "tee time", "tee off"]
    def is_valid(q):
        return not any(ex in q.lower() for ex in exclude)

    df = df[df['query'].apply(is_valid)]

    return df

def check_ip_infringement(query):
    query_lower = query.lower()
    for brand in IP_BLACKLIST:
        if brand in query_lower:
            return True
    return False

def generate_idea(query):
    # Simple logic to generate a design idea
    q = query.lower()
    for term in APPAREL_TERMS:
        q = q.replace(term, "").strip()

    # Clean up multiple spaces
    q = " ".join(q.split())

    if not q:
        return "Generic design based on trending apparel search."

    return f"Design featuring '{q}' theme. Market is searching for this specific niche. Look for unique typography or illustrative styles relating to {q}."

def format_results(df):
    if df.empty:
        return "", ""

    general_rows = []
    ip_rows = []

    # Sort by value (score) descending
    # 'Breakout' is represented as a high number in value usually, or string.
    # Let's handle 'Breakout' as 999,999 for sorting.
    def parse_value(v):
        if pd.isna(v):
            return 0
        if isinstance(v, str) and 'Breakout' in v:
            return 999999
        try:
            # Handle both strings and numeric types (like numpy.int64)
            return int(v)
        except (ValueError, TypeError):
            return 0

    df['sort_val'] = df['value'].apply(parse_value)
    df = df.sort_values(by='sort_val', ascending=False)

    for _, row in df.iterrows():
        query = row['query']
        score = row['value']
        idea = generate_idea(query)
        markdown_row = f"| {query} | {score} | {idea} |"

        if check_ip_infringement(query):
            ip_rows.append(markdown_row)
        else:
            general_rows.append(markdown_row)

    return "\n".join(general_rows), "\n".join(ip_rows)

def update_trends_file(general_md, ip_md):
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    header = f"## {date_str}\n\n"

    content = ""
    if general_md:
        content += "### General Merch Opportunities\n"
        content += "| Keyword | Score | Why/Idea |\n"
        content += "| --- | --- | --- |\n"
        content += general_md + "\n\n"

    if ip_md:
        content += "### Potential IP Infringing Opportunities\n"
        content += "> **Warning:** These may violate intellectual property rights. Proceed with extreme caution.\n\n"
        content += "| Keyword | Score | Why/Idea |\n"
        content += "| --- | --- | --- |\n"
        content += ip_md + "\n\n"

    if not content:
        content = "No significant trends found today.\n\n"

    new_entry = header + content

    existing_content = ""
    if os.path.exists("trends.md"):
        with open("trends.md", "r") as f:
            existing_content = f.read()

    # Avoid duplicate for the same day if run multiple times
    if f"## {date_str}" in existing_content:
        print(f"Entry for {date_str} already exists in trends.md. Skipping.")
        return

    with open("trends.md", "w") as f:
        f.write(new_entry + existing_content)

def main():
    print("Starting Trends Crawler...")
    df = get_rising_trends()
    df = filter_trends(df)
    general_md, ip_md = format_results(df)
    update_trends_file(general_md, ip_md)
    print("Done!")

if __name__ == "__main__":
    main()
