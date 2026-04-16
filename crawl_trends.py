import time
import datetime
import os
import re
import pandas as pd
from pytrends.request import TrendReq

# Configuration
KEYWORDS = ["tshirt", "shirt", "tank top", "merch"]
APPAREL_TERMS = ["t-shirt", "tshirt", "tank top", "shirt", "tee", "merch"]
IP_BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "bieber", "beiber", "taylor swift",
    "michael jackson", "one piece", "popeyes", "coachella", "anime", "netflix", "mickey",
    "trump", "biden", "nba", "nfl", "mlb", "nhl", "pokemon", "nintendo", "sony", "playstation",
    "xbox", "nasa", "hellstar", "karol g", "bruno mars", "sabrina carpenter"
]

NEGATIVE_KEYWORDS = [
    "meaning", "definition", "how to", "why", "iron", "near me", "template", "mockup", "transparent", "png"
]

TRENDS_FILE = "trends.md"

def get_rising_queries():
    pytrends = TrendReq(hl='en-US', tz=360)
    all_rising = []

    for kw in KEYWORDS:
        retries = 3
        while retries > 0:
            print(f"Fetching trends for: {kw}")
            try:
                pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='', gprop='')
                related_queries = pytrends.related_queries()

                if kw in related_queries:
                    rising = related_queries[kw]['rising']
                    if rising is not None:
                        rising['seed'] = kw
                        all_rising.append(rising)
                break # Success
            except Exception as e:
                print(f"Error fetching {kw}: {e}")
                if "429" in str(e):
                    print("Rate limited. Sleeping 10s...")
                    time.sleep(10)
                    retries -= 1
                else:
                    break # Don't retry for other errors

        time.sleep(2) # Modest delay between different keywords

    if not all_rising:
        return pd.DataFrame()

    df = pd.concat(all_rising, ignore_index=True)
    # Deduplicate
    df = df.drop_duplicates(subset=['query'])
    return df

def is_long_tail(query):
    return len(query.split()) >= 2

def contains_apparel(query):
    return any(term in query.lower() for term in APPAREL_TERMS)

def is_ip_infringing(query):
    query_lower = query.lower()
    for brand in IP_BLACKLIST:
        # Check for word boundary OR if it's a long string containing the brand (common for IP theft)
        if brand in query_lower:
            return True
    return False

def contains_negative(query):
    query_lower = query.lower()
    return any(neg in query_lower for neg in NEGATIVE_KEYWORDS)

def generate_idea(query):
    # Simple logic to generate an "idea" or explanation
    query_clean = query.lower()
    for term in APPAREL_TERMS:
        query_clean = query_clean.replace(term, "").strip()

    return f"Design focused on '{query_clean}' niche. Rising interest suggests low supply for specific long-tail variants."

def format_markdown_table(df):
    if df.empty:
        return "No data found for this period."

    lines = ["| Keyword | Score | Why/Idea |", "| :--- | :--- | :--- |"]
    for _, row in df.iterrows():
        idea = generate_idea(row['query'])
        score = row['value']
        # Convert score to string, handle potential 'Breakout'
        score_str = str(score)
        lines.append(f"| {row['query']} | {score_str} | {idea} |")

    return "\n".join(lines)

def main():
    df = get_rising_queries()

    if df.empty:
        print("No new trends found.")
        return

    # Filtering
    df['is_long_tail'] = df['query'].apply(is_long_tail)
    df['has_apparel'] = df['query'].apply(contains_apparel)
    df['has_negative'] = df['query'].apply(contains_negative)

    # Exclude non-apparel, too short, or containing negative keywords
    df = df[df['is_long_tail'] & df['has_apparel'] & ~df['has_negative']]

    # Categorize
    df['is_ip'] = df['query'].apply(is_ip_infringing)

    # Sort by value. If 'Breakout' is present, it might be a string.
    # Let's convert 'Breakout' to a high number for sorting.
    def sort_val(val):
        if isinstance(val, str) and 'breakout' in val.lower():
            return 999999
        try:
            return int(val)
        except:
            return 0

    df['sort_score'] = df['value'].apply(sort_val)

    general_df = df[~df['is_ip']].sort_values(by='sort_score', ascending=False)
    ip_df = df[df['is_ip']].sort_values(by='sort_score', ascending=False)

    # Prepare Content
    today = datetime.date.today().strftime("%Y-%m-%d")
    content = f"## {today}\n\n"

    content += "### General Merch Opportunities\n"
    content += format_markdown_table(general_df)
    content += "\n\n"

    content += "### Potential IP Infringing Opportunities\n"
    content += format_markdown_table(ip_df)
    content += "\n\n"

    # Prepend to file, maintaining the title at the top
    title = "# Merch Trends\n\n"
    if os.path.exists(TRENDS_FILE):
        with open(TRENDS_FILE, "r") as f:
            old_content = f.read()

        # Avoid double posting for the same day if run multiple times
        if f"## {today}" in old_content:
            print(f"Trends for {today} already exist in {TRENDS_FILE}. Overwriting only that section would be complex, so skipping or appending is simpler. For now, we prepend if date is not there.")
            return

        # Remove title from old content if it exists to avoid duplication
        if old_content.startswith(title):
            old_content = old_content[len(title):]

        new_file_content = title + content + old_content
    else:
        new_file_content = title + content

    with open(TRENDS_FILE, "w") as f:
        f.write(new_file_content)

    print(f"Successfully updated {TRENDS_FILE}")

if __name__ == "__main__":
    main()
