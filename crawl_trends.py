import time
import datetime
import os
import pandas as pd
from pytrends.request import TrendReq

# Configuration
KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]
TRENDS_FILE = "trends.md"
BLACKLIST = [
    "disney", "marvel", "star wars", "starwars", "nike", "adidas", "bieber",
    "taylor swift", "michael jackson", "one piece", "popeyes", "coachella",
    "netflix", "mickey", "mickey mouse", "trump", "biden", "nba", "nfl", "mlb",
    "nhl", "pokemon", "nintendo", "sony", "playstation", "xbox", "nasa",
    "hellstar", "karol g", "bruno mars", "sabrina carpenter", "billie eilish",
    "billie", "olivia rodrigo", "noah kahan", "frank ocean", "mashtag brady",
    "aldi", "morbid podcast", "ysl", "koningsdag", "oranje", "higgins", "kelce",
    "mahomes", "stroud", "wwe", "the weeknd", "chrome hearts", "stussy", "vultures", "kanye",
    "drake", "notre dame"
]

def is_ip_infringing(query):
    query_lower = query.lower()
    for brand in BLACKLIST:
        if brand in query_lower:
            return True
    return False

def generate_idea(query):
    query_lower = query.lower()
    # Basic idea generation logic
    if "autism" in query_lower:
        return "Awareness design, possibly combining with the mentioned theme (e.g., wolf)."
    if "funny" in query_lower or "joke" in query_lower:
        return "Text-based humorous design targeting this niche."

    clean_query = query
    for kw in ["tshirt", "t-shirt", "t shirt", "shirt", "tank top", "tanktop", "tee", "merch"]:
        clean_query = clean_query.replace(kw, "")

    clean_query = " ".join(clean_query.split()).strip()

    return f"Design centered around '{clean_query}'. Check social media for current memes or aesthetic styles related to this."

def get_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    all_rising = []

    for kw in KEYWORDS:
        print(f"Fetching rising queries for: {kw}")
        try:
            pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='', gprop='')
            related_queries = pytrends.related_queries()

            if kw in related_queries:
                rising = related_queries[kw]['rising']
                if rising is not None and not rising.empty:
                    all_rising.append(rising)

            # Rate limiting prevention
            time.sleep(2)
        except Exception as e:
            print(f"Error fetching {kw}: {e}")
            time.sleep(10)

    if not all_rising:
        return pd.DataFrame()

    df = pd.concat(all_rising).drop_duplicates(subset=['query'])

    # Filter for long tail (at least 2 words)
    df = df[df['query'].str.split().str.len() >= 2]

    # Filter out generic or irrelevant terms
    exclude = ["meaning", "definition", "how to", "why", "iron", "near me", "template", "mockup", "tee times", "tee time", "tee off", "graphic tee", "essential tee", "vintage tee", "oversized tee", "plain shirt", "blank shirt"]
    for word in exclude:
        df = df[~df['query'].str.contains(word, case=False)]

    return df

def update_trends_file(df):
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    existing_content = ""
    if os.path.exists(TRENDS_FILE):
        with open(TRENDS_FILE, "r") as f:
            existing_content = f.read()

    if f"## {today}" in existing_content:
        print(f"Trends for {today} already exist in {TRENDS_FILE}. Skipping update.")
        return

    if df.empty:
        print("No new trends found.")
        return

    # Sort by value (score)
    # Pytrends 'value' can be 'Breakout' or an integer.
    # Treat 'Breakout' as 9999 for sorting.
    def sort_val(v):
        if v == 'Breakout': return 9999
        try: return int(v)
        except: return 0

    df['sort_score'] = df['value'].apply(sort_val)
    df = df.sort_values(by='sort_score', ascending=False)

    ip_infringing = []
    general_merch = []

    for _, row in df.iterrows():
        query = row['query']
        score = row['value']
        idea = generate_idea(query)

        entry = f"| {query} | {score} | {idea} |"

        if is_ip_infringing(query):
            ip_infringing.append(entry)
        else:
            general_merch.append(entry)

    new_content = f"## {today}\n\n"

    if general_merch:
        new_content += "### General Merch Opportunities\n"
        new_content += "| Keyword | Score | Why/Idea |\n"
        new_content += "|---------|-------|----------|\n"
        new_content += "\n".join(general_merch) + "\n\n"

    if ip_infringing:
        new_content += "### Potential IP Infringing Opportunities\n"
        new_content += "| Keyword | Score | Why/Idea |\n"
        new_content += "|---------|-------|----------|\n"
        new_content += "\n".join(ip_infringing) + "\n\n"

    # Prepend new content
    with open(TRENDS_FILE, "w") as f:
        f.write(new_content + existing_content)

    print(f"Updated {TRENDS_FILE} with {len(df)} trends.")

if __name__ == "__main__":
    df = get_trends()
    update_trends_file(df)
