import pandas as pd
from pytrends.request import TrendReq
import time
import random
import datetime
import os
import re

# Seed keywords for POD niche
SEED_KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]

def get_pytrends_with_retry(pytrends, kw_list, retries=3):
    for i in range(retries):
        try:
            pytrends.build_payload(kw_list, cat=0, timeframe='now 7-d', geo='', gprop='')
            return pytrends.related_queries()
        except Exception as e:
            if "429" in str(e):
                print(f"Rate limited. Waiting 60s before retry {i+1}/{retries}...")
                time.sleep(60)
            else:
                print(f"Error fetching data for {kw_list}: {e}")
                break
    return None

IP_BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "taylor swift", "bts",
    "michael jackson", "nba", "wnba", "nfl", "mlb", "nhl", "nintendo", "pokemon",
    "harry potter", "nasa", "hellstar", "ysl", "gucci", "prada", "louis vuitton",
    "arsenal", "real madrid", "liverpool", "man city", "chelsea", "bayern", "barcelona",
    "knicks", "lakers", "celtics", "warriors", "bulls", "amiri", "trapstar", "corteiz",
    "sp5der", "minus two", "syna world", "harry styles", "gracie abrams", "daniel caesar",
    "bad bunny", "billie eilish", "drake", "kanye", "travis scott", "bruno mars",
    "hello kitty", "sanrio", "nascar", "f1", "mercedes", "ferrari", "red bull",
    "toy story", "psg", "ariana grande", "linkin park", "hazbin hotel", "helluva boss",
    "digital circus", "tadc", "glitch", "zach bryan", "phoebe bridgers", "love island",
    "scary movie", "bad omens", "limp bizkit", "dawid podsiadło", "malcolm todd",
    "forrest frank", "rock am ring", "selena gomez", "madewell", "carhartt",
    "böhse onkelz", "palace", "asap rocky", "megan moroney", "sean john", "morgan wallen"
]

def is_ip_infringing(query):
    query = query.lower()
    return any(brand in query for brand in IP_BLACKLIST)

def generate_idea(query):
    # Simple idea generation by removing apparel terms and suggesting a design
    # Sort by length descending to replace longer terms first (e.g. 'tank top' before 'top')
    apparel_terms = sorted(["shirt", "tshirt", "t-shirt", "tank top", "tanktop", "tee", "merch"], key=len, reverse=True)
    concept = query.lower()
    for term in apparel_terms:
        concept = concept.replace(term, "")
    # Clean up multiple spaces
    concept = re.sub(' +', ' ', concept).strip()
    return f"Design focused on '{concept.title()}'. People are searching for this style of apparel."

def is_long_tail_apparel(query):
    query = query.lower()
    # Check for apparel terms
    apparel_terms = ["shirt", "tshirt", "t-shirt", "tank top", "tanktop", "tee", "merch"]
    has_apparel = any(term in query for term in apparel_terms)

    # Check for 2+ words
    word_count = len(query.split())

    # Exclude very generic terms or noise
    noise_terms = ["meaning", "definition", "how to", "why", "iron", "near me", "template", "mockup", "tee times", "tee time", "tee off"]
    is_not_noise = not any(term in query for term in noise_terms)

    return has_apparel and word_count >= 2 and is_not_noise

def main():
    pytrends = TrendReq(hl='en-US', tz=360)
    all_rising_queries = []

    for kw in SEED_KEYWORDS:
        print(f"Fetching trends for: {kw}")
        results = get_pytrends_with_retry(pytrends, [kw])

        if results and kw in results:
            rising = results[kw]['rising']
            if rising is not None and not rising.empty:
                all_rising_queries.append(rising)

        # Delay to avoid rate limiting
        time.sleep(5 + random.random() * 5)

    if not all_rising_queries:
        print("No rising queries found.")
        return

    df = pd.concat(all_rising_queries).drop_duplicates(subset=['query'])

    # Apply filtering
    df['is_valid'] = df['query'].apply(is_long_tail_apparel)
    filtered_df = df[df['is_valid']].copy()

    # Categorize
    filtered_df['is_infringing'] = filtered_df['query'].apply(is_ip_infringing)
    filtered_df['idea'] = filtered_df['query'].apply(generate_idea)

    print(f"Found {len(filtered_df)} filtered rising queries.")

    update_trends_md(filtered_df)

def update_trends_md(df):
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")

    content = f"## {date_str}\n\n"

    general = df[~df['is_infringing']]
    infringing = df[df['is_infringing']]

    content += "### General Merch Opportunities\n"
    if not general.empty:
        content += "| Keyword | Score | Why/Idea |\n"
        content += "| :--- | :--- | :--- |\n"
        for _, row in general.iterrows():
            content += f"| {row['query']} | {row['value']} | {row['idea']} |\n"
    else:
        content += "No new general opportunities found today.\n"

    content += "\n### Potential IP Infringing Opportunities\n"
    if not infringing.empty:
        content += "| Keyword | Score | Why/Idea |\n"
        content += "| :--- | :--- | :--- |\n"
        for _, row in infringing.iterrows():
            content += f"| {row['query']} | {row['value']} | {row['idea']} |\n"
    else:
        content += "No new IP infringing opportunities found today.\n"

    content += "\n---\n"

    if os.path.exists("trends.md"):
        with open("trends.md", "r") as f:
            lines = f.readlines()

        # Keep the title at the top
        title = "# Google Trends Merch Crawler\n\n"
        other_content = "".join(lines[1:]) if lines and lines[0].startswith("#") else "".join(lines)

        # Check if we already added for today to avoid duplicates
        if f"## {date_str}" in other_content:
            print(f"Trends for {date_str} already exist in trends.md. Skipping file update.")
            return

        new_content = title + content + other_content
    else:
        new_content = "# Google Trends Merch Crawler\n\n" + content

    with open("trends.md", "w") as f:
        f.write(new_content)
    print("trends.md updated successfully.")

if __name__ == "__main__":
    main()
