import pandas as pd
from pytrends.request import TrendReq
import datetime
import os
import time

# --- Configuration ---
KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]
TIMEFRAME = 'now 7-d'  # Last 7 days to get fresh rising trends
GEO = ''  # Worldwide
TRENDS_FILE = "trends.md"

# Expanded Brand Blacklist (Potential IP issues)
BRAND_BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "taylor swift", "bts",
    "michael jackson", "nba", "nfl", "mlb", "nhl", "nintendo", "pokemon",
    "harry potter", "nasa", "hellstar", "ysl", "gucci", "prada", "louis vuitton",
    "koningsdag", "oranje", "higgins", "wwe", "kanye", "drake", "notre dame",
    "ariana grande", "george strait", "olivia dean", "conan gray", "man utd",
    "lidl", "m&s", "mnet", "amc", "murder drones", "luke combs", "ohio state",
    "ufc", "f1", "nascar", "sanrio", "hello kitty", "stussy", "mclaren",
    "deftones", "cleetus mcfarland", "the neighbourhood", "bring me the horizon",
    "khan asadi", "lyrebird", "anthropologie", "carson hocevar"
]

# Keywords that often indicate non-merch search intent
EXCLUDE_KEYWORDS = [
    "meaning", "definition", "how to", "why", "iron", "near me", "template", "mockup",
    "tee times", "tee time", "tee off", "graphic tee", "essential tee", "vintage tee",
    "oversized tee", "plain shirt", "blank shirt"
]

def get_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    all_rising = []

    for kw in KEYWORDS:
        print(f"Fetching trends for: {kw}")
        try:
            pytrends.build_payload([kw], cat=0, timeframe=TIMEFRAME, geo=GEO, gprop='')
            related_queries = pytrends.related_queries()

            if kw in related_queries and related_queries[kw]['rising'] is not None:
                rising = related_queries[kw]['rising']
                all_rising.append(rising)

            # Small delay to avoid rate limiting
            time.sleep(2)
        except Exception as e:
            print(f"Error fetching {kw}: {e}")
            continue

    if not all_rising:
        return pd.DataFrame()

    df = pd.concat(all_rising).drop_duplicates(subset=['query'])
    return df

def is_ip_infringing(query):
    query_lower = query.lower()
    for brand in BRAND_BLACKLIST:
        if brand in query_lower:
            return True
    return False

def generate_idea(query):
    query_lower = query.lower()

    # Clean up the query to make a better idea string
    idea_base = query_lower
    for term in ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]:
        idea_base = idea_base.replace(term, "").strip()

    if not idea_base:
        idea_base = query_lower

    if "i love" in query_lower or "i heart" in query_lower:
        return f"Classic 'I Heart' design for {idea_base}. Use bold typography and a vibrant heart icon."
    elif "funny" in query_lower:
        return f"Humorous graphic or pun related to {idea_base}. Keep it simple and relatable."
    elif "vintage" in query_lower or "retro" in query_lower:
        return f"Retro 70s/80s style distressed graphic for {idea_base}."
    else:
        return f"Trending topic: {idea_base}. Design a unique graphic tee that captures the essence of this search, targeting fans of {idea_base}."

def process_trends(df):
    results = []

    for _, row in df.iterrows():
        query = row['query']
        score = row['value']

        # Filter for long-tail (at least 2 words)
        if len(query.split()) < 2:
            continue

        # Filter out common non-merch terms
        if any(exclude in query.lower() for exclude in EXCLUDE_KEYWORDS):
            continue

        is_ip = is_ip_infringing(query)
        idea = generate_idea(query)

        results.append({
            'keyword': query,
            'score': score,
            'idea': idea,
            'is_ip': is_ip
        })

    return results

def format_as_markdown(results):
    today = datetime.date.today().strftime("%Y-%m-%d")

    general = [r for r in results if not r['is_ip']]
    ip_infringing = [r for r in results if r['is_ip']]

    # Sort by score (descending)
    # Pytrends returns 'Breakout' for very high growth, we'll treat it as 10000 for sorting
    def sort_key(x):
        val = x['score']
        if isinstance(val, str) and val == 'Breakout':
            return 9999
        try:
            return int(val)
        except:
            return 0

    general.sort(key=sort_key, reverse=True)
    ip_infringing.sort(key=sort_key, reverse=True)

    output = f"## {today}\n\n"

    output += "### General Merch Opportunities\n"
    output += "| Keyword | Score | Why/Idea |\n"
    output += "| :--- | :--- | :--- |\n"
    for r in general:
        output += f"| {r['keyword']} | {r['score']} | {r['idea']} |\n"

    output += "\n### Potential IP Infringing Opportunities\n"
    output += "| Keyword | Score | Why/Idea |\n"
    output += "| :--- | :--- | :--- |\n"
    for r in ip_infringing:
        output += f"| {r['keyword']} | {r['score']} | {r['idea']} |\n"

    output += "\n---\n"
    return output

def main():
    df = get_trends()
    if df.empty:
        print("No rising trends found.")
        return

    results = process_trends(df)
    if not results:
        print("No suitable merch opportunities found after filtering.")
        return

    new_content = format_as_markdown(results)

    if os.path.exists(TRENDS_FILE):
        with open(TRENDS_FILE, "r") as f:
            old_content = f.read()

        # Avoid duplicate entries for the same day if run multiple times
        today_header = f"## {datetime.date.today().strftime('%Y-%m-%d')}"
        if today_header in old_content:
            print("Trends for today already exist in the file. Skipping update.")
            return

        final_content = new_content + "\n" + old_content
    else:
        final_content = "# Merch Trends Log\n\n" + new_content

    with open(TRENDS_FILE, "w") as f:
        f.write(final_content)

    print(f"Successfully updated {TRENDS_FILE}")

if __name__ == "__main__":
    main()
