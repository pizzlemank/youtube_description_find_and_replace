import pandas as pd
from pytrends.request import TrendReq
import datetime
import os
import time
import random

# List of seed keywords to find merch opportunities
SEED_KEYWORDS = ["tshirt", "shirt", "tank top", "merch", "tee", "t-shirt", "tshirts", "tanktop"]

# Keywords that might indicate IP infringement
IP_BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "bieber", "beiber",
    "taylor swift", "michael jackson", "one piece", "popeyes", "coachella",
    "anime", "netflix", "mickey", "trump", "biden", "nba", "nfl", "mlb", "nhl",
    "pokemon", "nintendo", "sony", "playstation", "xbox", "nasa", "hellstar",
    "karol g", "bruno mars", "sabrina carpenter"
]

# Apparel related terms to ensure we are looking at merch
APPAREL_TERMS = ["shirt", "tshirt", "tank top", "tanktop", "tee", "t-shirt"]

# Exclusion terms to filter out non-merch queries
EXCLUSION_TERMS = ["meaning", "definition", "how to", "why", "iron", "near me", "template", "mockup", "tee times", "tee time", "tee off"]

def get_trends():
    # Removed retries and backoff_factor to avoid "method_whitelist" error with newer urllib3/requests
    pytrends = TrendReq(hl='en-US', tz=360)
    all_rising = []

    for kw in SEED_KEYWORDS:
        print(f"Fetching trends for: {kw}")
        max_retries = 3
        for attempt in range(max_retries):
            try:
                pytrends.build_payload([kw], timeframe='now 7-d')
                related_queries = pytrends.related_queries()

                if kw in related_queries and related_queries[kw]['rising'] is not None:
                    rising = related_queries[kw]['rising']
                    all_rising.append(rising)

                # Sleep to avoid rate limiting
                time.sleep(random.uniform(2, 5))
                break # Success
            except Exception as e:
                print(f"Error fetching {kw} (attempt {attempt+1}/{max_retries}): {e}")
                if "429" in str(e):
                    wait_time = 10 * (attempt + 1)
                    print(f"Rate limited. Sleeping for {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    break # Don't retry for other errors

    if not all_rising:
        return pd.DataFrame()

    df = pd.concat(all_rising).drop_duplicates(subset='query')
    return df

def filter_merch_opportunities(df):
    if df.empty:
        return [], []

    general_merch = []
    ip_infringing = []

    for _, row in df.iterrows():
        query = row['query'].lower()
        # Handle 'Breakout' as a very high score
        score = row['value']

        # Robustly handle different score types (Breakout, int, numpy.int64)
        if isinstance(score, str) and 'breakout' in score.lower():
            numeric_score = 999999
            display_score = "Breakout"
        else:
            try:
                numeric_score = int(score)
                display_score = str(score)
            except:
                numeric_score = 0
                display_score = str(score)

        # Filter for long tail (at least 2 words)
        words = query.split()
        if len(words) < 2:
            continue

        # Ensure it contains apparel related words
        if not any(term in query for term in APPAREL_TERMS):
            continue

        # Filter out exclusion terms
        if any(term in query for term in EXCLUSION_TERMS):
            continue

        # Check for IP infringement
        is_ip = any(brand in query for brand in IP_BLACKLIST)

        # Generate a "Why/Idea"
        idea = generate_idea(query)

        item = {
            "keyword": query,
            "score": display_score,
            "numeric_score": numeric_score,
            "idea": idea
        }

        if is_ip:
            ip_infringing.append(item)
        else:
            general_merch.append(item)

    # Sort by numeric score descending
    general_merch.sort(key=lambda x: x['numeric_score'], reverse=True)
    ip_infringing.sort(key=lambda x: x['numeric_score'], reverse=True)

    return general_merch, ip_infringing

def generate_idea(query):
    # Basic logic to generate a design idea
    concept = query
    # Sort APPAREL_TERMS by length descending to replace the longest match first
    for term in sorted(APPAREL_TERMS, key=len, reverse=True):
        if term in concept:
            concept = concept.replace(term, "").strip()
            break

    concept = " ".join(concept.split()) # Clean extra spaces

    if not concept:
        concept = query

    return f"Rising demand for '{concept.capitalize()}'. Design idea: Focus on clean typography or a minimalist graphic representing the theme."

def update_trends_md(general, ip):
    date_str = datetime.date.today().strftime("%Y-%m-%d")

    # Check if we already have entries for today to avoid duplicates if run multiple times
    if os.path.exists("trends.md"):
        with open("trends.md", "r") as f:
            content = f.read()
            if f"## {date_str}" in content:
                print(f"Trends for {date_str} already exist. Skipping update.")
                return

    new_section = f"## {date_str}\n\n"

    new_section += "### General Merch Opportunities\n"
    new_section += "| Keyword | Score | Why / Idea |\n"
    new_section += "| :--- | :--- | :--- |\n"
    if not general:
        new_section += "| No new opportunities found | - | - |\n"
    for item in general:
        new_section += f"| {item['keyword']} | {item['score']} | {item['idea']} |\n"

    new_section += "\n### Potential IP Infringing Opportunities\n"
    new_section += "| Keyword | Score | Why / Idea |\n"
    new_section += "| :--- | :--- | :--- |\n"
    if not ip:
        new_section += "| No new opportunities found | - | - |\n"
    for item in ip:
        new_section += f"| {item['keyword']} | {item['score']} | {item['idea']} |\n"

    new_section += "\n---\n\n"

    header = "# Google Trends Merch Opportunities\n\nDaily crawl for T-shirt design ideas.\n\n"

    if os.path.exists("trends.md"):
        with open("trends.md", "r") as f:
            old_content = f.read()

        if old_content.startswith("# Google Trends Merch"):
            # Try to insert after the header
            parts = old_content.split("\n\n", 2)
            if len(parts) >= 3:
                final_content = parts[0] + "\n\n" + parts[1] + "\n\n" + new_section + parts[2]
            else:
                # If structure is different than expected, just append
                final_content = old_content.rstrip() + "\n\n" + new_section
        else:
            final_content = header + new_section + old_content
    else:
        final_content = header + new_section

    with open("trends.md", "w") as f:
        f.write(final_content)

if __name__ == "__main__":
    print(f"Starting crawl at {datetime.datetime.now()}...")
    df = get_trends()
    general, ip = filter_merch_opportunities(df)
    update_trends_md(general, ip)
    print("Done!")
