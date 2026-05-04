import os
import datetime
import pandas as pd
from pytrends.request import TrendReq
import time

# --- Configuration ---
KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]
BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "taylor swift", "bts",
    "michael jackson", "nba", "nfl", "mlb", "nhl", "nintendo", "pokemon",
    "harry potter", "nasa", "hellstar", "ysl", "gucci", "prada", "louis vuitton",
    "koningsdag", "oranje", "higgins", "wwe", "kanye", "drake", "notre dame",
    "ariana grande", "george strait", "olivia dean", "conan gray", "man utd",
    "lidl", "m&s", "mnet", "amc", "murder drones", "luke combs", "ohio state",
    "ufc", "f1", "nascar", "sanrio", "hello kitty", "stussy", "mclaren",
    "deftones", "cleetus mcfarland", "the neighbourhood", "bring me the horizon",
    "khan asadi", "lyrebird", "anthropologie", "carson hocevar", "rihanna",
    "morgan wallen", "valorant", "kentucky derby", "victoria beckham", "kimi antonelli"
]

EXCLUDE_TERMS = [
    "meaning", "definition", "how to", "why", "iron", "near me", "template",
    "mockup", "tee times", "tee time", "tee off", "graphic tee", "essential tee",
    "vintage tee", "oversized tee", "plain shirt", "blank shirt"
]

TRENDS_FILE = "trends.md"

def get_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    all_rising = []

    for kw in KEYWORDS:
        print(f"Fetching trends for: {kw}")
        retries = 3
        while retries > 0:
            try:
                pytrends.build_payload([kw], timeframe='now 7-d')
                related_queries = pytrends.related_queries()

                if kw in related_queries and related_queries[kw]['rising'] is not None:
                    rising = related_queries[kw]['rising']
                    all_rising.append(rising)

                time.sleep(2) # Avoid rate limiting
                break
            except Exception as e:
                print(f"Error fetching {kw}: {e}")
                # If 429, wait longer
                if "429" in str(e):
                    print("Rate limited. Waiting 60 seconds...")
                    time.sleep(60)
                    retries -= 1
                else:
                    break

    if not all_rising:
        return pd.DataFrame()

    df = pd.concat(all_rising).drop_duplicates(subset='query')
    return df

def is_ip_infringing(query):
    query_lower = query.lower()
    for brand in BLACKLIST:
        if brand in query_lower:
            return True
    return False

def is_relevant(query):
    query_lower = query.lower()

    # Must be long tail (2+ words)
    if len(query.split()) < 2:
        return False

    # Check for apparel terms
    apparel_terms = ["shirt", "tshirt", "t-shirt", "tank top", "tanktop", "tee", "merch"]
    has_apparel = any(term in query_lower for term in apparel_terms)
    if not has_apparel:
        return False

    # Exclude non-commercial terms
    if any(term in query_lower for term in EXCLUDE_TERMS):
        return False

    return True

def generate_idea(query):
    query_lower = query.lower()
    # Clean up the query for the idea prompt
    clean_query = query_lower
    for term in ["t-shirt", "tshirt", "t shirt", "shirt", "tanktop", "tank top", "tee", "merch"]:
        clean_query = clean_query.replace(term, "")
    clean_query = " ".join(clean_query.split()) # remove extra spaces

    # Simple idea generation logic
    idea = f"Design a '{clean_query}' themed graphic. "
    if "autism" in query_lower:
        idea += "Use puzzle pieces or infinity symbols with supportive text."
    elif "wolf" in query_lower:
        idea += "Cool aesthetic wolf illustration, maybe vintage style."
    elif "funny" in query_lower:
        idea += "Use a bold, readable font for the joke."
    else:
        idea += "Look for trending aesthetics related to this niche on Pinterest/TikTok."

    return idea

def format_markdown(df):
    if df.empty:
        return ""

    df['is_ip'] = df['query'].apply(is_ip_infringing)
    df['idea'] = df['query'].apply(generate_idea)

    # Sort by value (score) descending. 'Breakout' should be at the top.
    def score_to_int(val):
        if isinstance(val, str) and val == 'Breakout':
            return 9999
        try:
            return int(val)
        except:
            return 0

    df['score_int'] = df['value'].apply(score_to_int)
    df = df.sort_values(by='score_int', ascending=False)

    general_df = df[df['is_ip'] == False]
    ip_df = df[df['is_ip'] == True]

    now = datetime.datetime.now().strftime("%Y-%m-%d")
    output = f"## {now}\n\n"

    output += "### General Merch Opportunities\n"
    output += "| Keyword | Score | Why/Idea |\n"
    output += "| :--- | :--- | :--- |\n"
    for _, row in general_df.iterrows():
        output += f"| {row['query']} | {row['value']} | {row['idea']} |\n"

    output += "\n### Potential IP Infringing Opportunities\n"
    output += "| Keyword | Score | Why/Idea |\n"
    output += "| :--- | :--- | :--- |\n"
    for _, row in ip_df.iterrows():
        output += f"| {row['query']} | {row['value']} | {row['idea']} |\n"

    output += "\n---\n"
    return output

def main():
    print("Starting trends crawl...")
    df = get_trends()

    if df.empty:
        print("No trends found.")
        return

    # Filter for relevance
    df = df[df['query'].apply(is_relevant)]

    if df.empty:
        print("No relevant trends found after filtering.")
        return

    new_content = format_markdown(df)

    if os.path.exists(TRENDS_FILE):
        with open(TRENDS_FILE, "r") as f:
            old_content = f.read()

        # Avoid duplicate entries for the same day if re-run
        today_header = f"## {datetime.datetime.now().strftime('%Y-%m-%d')}"
        if today_header in old_content:
            print("Today's trends already recorded. Skipping update to avoid duplication.")
            return

        with open(TRENDS_FILE, "w") as f:
            f.write(new_content + "\n" + old_content)
    else:
        with open(TRENDS_FILE, "w") as f:
            f.write(new_content)

    print(f"Trends updated in {TRENDS_FILE}")

if __name__ == "__main__":
    main()
