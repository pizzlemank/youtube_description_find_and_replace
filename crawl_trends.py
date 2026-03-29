import time
import datetime
import pandas as pd
from pytrends.request import TrendReq
import os

# Configuration
SEEDS = ["tshirt", "shirt", "tanktop", "merch", "t-shirt"]
TIMEFRAME = 'now 7-d'
TRENDS_FILE = "trends.md"

# Preliminary list of high-risk IP keywords
IP_KEYWORDS = [
    "disney", "marvel", "star wars", "mickey", "pokemon", "nintendo", "anime",
    "nike", "adidas", "gucci", "prada", "nba", "nfl", "mlb", "nhl", "fifa",
    "harry potter", "hogwarts", "blue jays", "dodgers", "hannah montana",
    "bts", "5sos", "twice", "lany", "digital circus", "tadc", "glitch",
    "minecraft", "roblox", "fortnite", "taylor swift", "eras tour",
    "netflix", "stranger things", "batman", "superman", "spider-man",
    "sanrio", "hello kitty", "snoopy", "peanuts", "barbie"
]

# Words to filter out as too generic or irrelevant for POD design ideas
GENERIC_WORDS = ["plain", "blank", "cheap", "bulk", "cotton", "custom", "printing", "design", "buy", "online"]

def is_ip_infringing(query):
    query_lower = query.lower()
    for ip_word in IP_KEYWORDS:
        if ip_word in query_lower:
            return True
    return False

def is_too_generic(query):
    query_lower = query.lower()
    # If it's just one word, it might be too broad unless it's a specific niche
    if len(query.split()) < 2:
        return True
    for word in GENERIC_WORDS:
        if word in query_lower:
            return True
    return False

def generate_description(query):
    # Simple logic to generate a reason/idea
    query_lower = query.lower()
    if "tshirt" in query_lower or "shirt" in query_lower:
        base = "Popular apparel search."
    else:
        base = "Rising merchandise interest."

    return f"{base} Potential for unique graphic design targeting this niche."

def crawl():
    pytrends = TrendReq(hl='en-US', tz=360)
    all_rising = []

    for seed in SEEDS:
        print(f"Fetching trends for: {seed}")
        try:
            pytrends.build_payload([seed], timeframe=TIMEFRAME)
            queries = pytrends.related_queries()
            if seed in queries and queries[seed]['rising'] is not None:
                rising = queries[seed]['rising']
                # Add seed info
                rising['seed'] = seed
                all_rising.append(rising)
            time.sleep(1) # Rate limiting
        except Exception as e:
            print(f"Error fetching {seed}: {e}")

    if not all_rising:
        print("No new trends found.")
        return

    df = pd.concat(all_rising).drop_duplicates(subset=['query'])

    # Filter and categorize
    general_merch = []
    ip_infringing = []

    for _, row in df.iterrows():
        query = row['query']
        score = row['value']

        if is_too_generic(query):
            continue

        desc = generate_description(query)
        entry = {
            'keyword': query,
            'score': score,
            'why': desc
        }

        if is_ip_infringing(query):
            ip_infringing.append(entry)
        else:
            general_merch.append(entry)

    # Prepare markdown
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    md_content = f"## Trends Crawled on {now}\n\n"

    md_content += "### General Merch Opportunities\n"
    md_content += "| Keyword | Score | Why / Idea |\n"
    md_content += "|---------|-------|------------|\n"
    for item in general_merch:
        md_content += f"| {item['keyword']} | {item['score']} | {item['why']} |\n"

    md_content += "\n### Potential IP Infringing Opportunities\n"
    md_content += "| Keyword | Score | Why / Idea |\n"
    md_content += "|---------|-------|------------|\n"
    for item in ip_infringing:
        md_content += f"| {item['keyword']} | {item['score']} | {item['why']} |\n"

    md_content += "\n---\n\n"

    # Prepend to file
    existing_content = ""
    if os.path.exists(TRENDS_FILE):
        with open(TRENDS_FILE, "r") as f:
            existing_content = f.read()

    with open(TRENDS_FILE, "w") as f:
        f.write(md_content + existing_content)

    print(f"Updated {TRENDS_FILE} with {len(general_merch)} general and {len(ip_infringing)} IP infringing items.")

if __name__ == "__main__":
    crawl()
