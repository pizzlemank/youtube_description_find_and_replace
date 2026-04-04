import pandas as pd
from pytrends.request import TrendReq
import datetime
import os
import time
import re

# List of seed keywords to start the crawl
SEED_KEYWORDS = ["tshirt", "shirt", "tank top", "merch"]

# Blacklist of keywords that might indicate IP infringement (brands, famous people, etc.)
IP_BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "apple", "google",
    "bts", "taylor swift", "drake", "ncaa", "nfl", "nba", "mlb", "super bowl",
    "minecraft", "roblox", "pokemon", "anime", "naruto", "one piece",
    "travis scott", "kanye", "yeezy", "netflix", "hbo", "warner bros",
    "gucci", "prada", "louis vuitton", "chanel", "zara", "h&m", "calvin klein",
    "national geographic", "nasa", "fbi", "cia", "rcb", "ipl", "csk"
]

# Apparel terms to ensure long-tail relevance
APPAREL_TERMS = ["shirt", "tshirt", "t-shirt", "tanktop", "tank top", "hoodie", "tee"]

def fetch_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    all_rising_queries = []

    for keyword in SEED_KEYWORDS:
        print(f"Fetching trends for: {keyword}")
        try:
            pytrends.build_payload([keyword], timeframe='now 7-d')
            related_queries = pytrends.related_queries()

            if keyword in related_queries and related_queries[keyword]['rising'] is not None:
                rising = related_queries[keyword]['rising']
                all_rising_queries.append(rising)

            # Sleep to avoid rate limiting
            time.sleep(2)
        except Exception as e:
            print(f"Error fetching {keyword}: {e}")

    if not all_rising_queries:
        return pd.DataFrame()

    df = pd.concat(all_rising_queries).drop_duplicates(subset='query')
    return df

def filter_and_categorize(df):
    if df.empty:
        return [], []

    general_opportunities = []
    ip_infringing = []

    for _, row in df.iterrows():
        query = row['query'].lower()
        score = row['value']

        # Check if it's apparel related (long tail)
        is_apparel = any(term in query for term in APPAREL_TERMS)
        if not is_apparel:
            continue

        # Basic filtering for junk
        if any(junk in query for junk in ["meaning", "definition", "crossword", "clue", "how to", "why"]):
            continue

        # Check for IP infringement using word boundaries to avoid false positives
        is_ip = False
        for brand in IP_BLACKLIST:
            if re.search(rf'\b{re.escape(brand)}\b', query):
                is_ip = True
                break

        idea = generate_idea(query)
        entry = {
            "keyword": row['query'],
            "score": score,
            "idea": idea
        }

        if is_ip:
            ip_infringing.append(entry)
        else:
            general_opportunities.append(entry)

    return general_opportunities, ip_infringing

def generate_idea(query):
    # Simple rule-based "idea" generation since we don't have LLM access in the script itself easily
    # (In a real scenario, one might use an LLM here)
    if "wolf" in query:
        return "Alpha/Sigma wolf aesthetic is trending. Use dark colors and vintage '90s bootleg style."
    elif "funny" in query:
        return "Humor based on the specific niche mentioned. Minimalist typography usually works best."
    elif "vintage" in query:
        return "Distressed textures, washed-out colors, and retro fonts."
    else:
        return f"Trending search for '{query}'. Research current social media memes or news related to this for design inspiration."

def format_markdown_table(data):
    if not data:
        return "No opportunities found."

    header = "| Keyword | Score | Why/Idea/Market |\n| :--- | :--- | :--- |\n"
    rows = ""
    for item in data:
        rows += f"| {item['keyword']} | {item['score']} | {item['idea']} |\n"
    return header + rows

def update_trends_file(general, ip):
    today = datetime.date.today().strftime("%Y-%m-%d")

    new_entry = f"## {today}\n\n"
    new_entry += "### General Merch Opportunities\n\n"
    new_entry += format_markdown_table(general)
    new_entry += "\n\n### Potential IP Infringing Opportunities\n\n"
    new_entry += format_markdown_table(ip)
    new_entry += "\n\n---\n\n"

    header = "# Print-on-Demand Trends\n\n"

    if os.path.exists("trends.md"):
        with open("trends.md", "r") as f:
            existing_content = f.read()

        # Avoid duplicate entries for the same day if re-run
        if f"## {today}" in existing_content:
            print(f"Trends for {today} already exist in trends.md. Skipping append.")
            return

        # Insert after the header if it exists, otherwise prepend
        if existing_content.startswith(header):
            full_content = header + new_entry + existing_content[len(header):]
        else:
            full_content = header + new_entry + existing_content
    else:
        full_content = header + new_entry

    with open("trends.md", "w") as f:
        f.write(full_content)

if __name__ == "__main__":
    print("Starting trend crawl...")
    trends_df = fetch_trends()
    gen, ip = filter_and_categorize(trends_df)
    update_trends_file(gen, ip)
    print("Crawl complete and trends.md updated.")
