import pandas as pd
from pytrends.request import TrendReq
import datetime
import os
import time
import re

# Configuration
SEED_KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]
IP_BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "taylor swift", "bts", "michael jackson",
    "nba", "wnba", "nfl", "mlb", "nhl", "nintendo", "pokemon", "harry potter", "nasa",
    "hellstar", "ysl", "gucci", "prada", "louis vuitton", "arsenal", "real madrid", "liverpool",
    "man city", "chelsea", "bayern", "barcelona", "knicks", "lakers", "celtics", "warriors", "bulls",
    "amiri", "trapstar", "corteiz", "sp5der", "minus two", "syna world", "harry styles",
    "gracie abrams", "daniel caesar", "bad bunny", "billie eilish", "drake", "kanye", "travis scott",
    "bruno mars", "hello kitty", "sanrio", "nascar", "f1", "mercedes", "ferrari", "red bull",
    "toy story", "psg", "asap rocky", "megan moroney", "sean john", "morgan wallen", "spurs",
    "rcb", "snipes", "asos", "pattie gonia", "wingstop", "ariana grande", "selena gomez",
    "carhartt", "hazbin hotel", "digital circus", "tadc", "linkin park", "bad omens",
    "forrest frank", "malcolm todd", "böhse onkelz", "love island", "eternal sunshine",
    "madewell", "anthropologie", "glitch", "stevie nicks", "beyonce", "lilibet",
    "olivia rodrigo", "caitlin clark", "sabrina carpenter", "messi", "ronaldo", "spiderman",
    "spider-man", "batman", "superman", "fifa", "uefa", "palace", "kobe", "cowboys",
    "yankees", "dodgers", "dfb", "us open", "olympics", "cecil", "h&m", "levi's", "zara",
    "gap", "old navy", "lululemon", "patagonia", "north face", "under armour", "puma",
    "reebok", "vans", "converse", "stussy", "supreme", "hilary duff", "lewis capaldi",
    "radiohead", "beabadoobee", "phoebe bridgers", "kmfdm", "ye", "jackass", "runescape",
    "supergirl", "noah kahan", "my chemical romance", "mcr", "john deere", "wimbledon", "alan jackson"
]

APPAREL_TERMS = ["t-shirt", "tshirt", "tank top", "tanktop", "shirt", "merch", "tee"]

def is_ip_infringing(keyword):
    keyword_lower = keyword.lower()
    for brand in IP_BLACKLIST:
        if re.search(rf"\b{re.escape(brand)}\b", keyword_lower):
            return True
    return False

def generate_idea(keyword):
    # Simple logic to generate ideas based on the keyword
    clean_keyword = keyword.lower()
    # Replace longest terms first to avoid partial replacements (e.g. "tshirt" -> "t")
    sorted_terms = sorted(APPAREL_TERMS, key=len, reverse=True)
    for term in sorted_terms:
        # Use regex to replace whole words or specific suffixes
        clean_keyword = re.sub(rf"\b{re.escape(term)}s?\b", "", clean_keyword).strip()

    if not clean_keyword:
        clean_keyword = keyword

    # Clean up multiple spaces
    clean_keyword = re.sub(r'\s+', ' ', clean_keyword).strip()

    return f"Graphic design featuring '{clean_keyword.title()}' with artistic typography or relevant illustration. Popular style on Etsy/Redbubble."

def fetch_trends():
    # Use custom retry logic as pytrends' built-in can sometimes be finicky with newer urllib3
    pytrends = TrendReq(hl='en-US', tz=360)
    all_rising_queries = []

    for kw in SEED_KEYWORDS:
        print(f"Fetching trends for: {kw}")
        retries = 3
        while retries > 0:
            try:
                pytrends.build_payload([kw], timeframe='now 7-d')
                related_queries = pytrends.related_queries()

                if kw in related_queries and related_queries[kw]['rising'] is not None:
                    rising = related_queries[kw]['rising']
                    all_rising_queries.append(rising)

                time.sleep(5) # Avoid rate limiting
                break
            except Exception as e:
                print(f"Error fetching {kw}: {e}")
                if "429" in str(e):
                    print("Rate limited. Waiting 10 seconds...")
                    time.sleep(10)
                    retries -= 1
                else:
                    break

    if not all_rising_queries:
        return pd.DataFrame()

    df = pd.concat(all_rising_queries).drop_duplicates(subset=['query'])
    return df

def main():
    print("Starting trends crawl...")
    df = fetch_trends()

    if df.empty:
        print("No new trends found.")
        return

    # Filtering
    # 1. Long tail (at least 2 words)
    # 2. Contains apparel term (though we searched for them, sometimes results are generic)
    # 3. Not just the seed keyword itself

    df = df[df['query'].str.split().str.len() >= 2]

    # Filter out queries that don't actually contain an apparel term or are too generic
    def filter_query(q):
        q = q.lower()
        if any(term in q for term in APPAREL_TERMS):
            # Exclude very generic ones like "t shirt" if they somehow got here
            if q.strip() in SEED_KEYWORDS:
                return False
            # Exclude non-commercial/irrelevant
            exclude = ["meaning", "definition", "how to", "why", "iron", "near me", "template", "mockup", "tee times", "tee time", "tee off", "graphic tee", "essential tee", "vintage tee", "oversized tee", "plain shirt", "blank shirt", "kaffee", "rezepte", "bh für", "bra for", "tutorial", "bra", "t-shirt bra", "tee height", "là gì", "t-shirt femme", "custom t-shirt printing", "roblox t-shirt"]
            if any(ex in q for ex in exclude):
                return False
            return True
        return False

    df = df[df['query'].apply(filter_query)]

    if df.empty:
        print("No relevant trends after filtering.")
        return

    # Sort by score (Breakout is usually high)
    def score_to_int(s):
        if s == 'Breakout': return 9999
        try: return int(s)
        except: return 0

    df['score_val'] = df['value'].apply(score_to_int)
    df = df.sort_values(by='score_val', ascending=False)

    today = datetime.date.today().strftime("%Y-%m-%d")

    # Update trends.md
    filename = "trends.md"
    main_header = "# Google Trends Merch Opportunities\n\n"

    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            old_content = f.read()
        if f"## {today}" in old_content:
            print(f"Trends for {today} already exist in {filename}. Skipping update.")
            return

    general_ops = []
    ip_ops = []

    for _, row in df.iterrows():
        kw = row['query']
        score = row['value']
        idea = generate_idea(kw)

        entry = f"| {kw} | {score} | {idea} |"

        if is_ip_infringing(kw):
            ip_ops.append(entry)
        else:
            general_ops.append(entry)

    # Prepare Markdown content
    content = f"## {today}\n\n### General Merch Opportunities\n| keyword | score | Why/Idea |\n| :--- | :--- | :--- |\n"
    if general_ops:
        content += "\n".join(general_ops) + "\n"
    else:
        content += "| None | - | - |\n"

    content += "\n### Potential IP Infringing Opportunities\n| keyword | score | Why/Idea |\n| :--- | :--- | :--- |\n"
    if ip_ops:
        content += "\n".join(ip_ops) + "\n"
    else:
        content += "| None | - | - |\n"

    content += "\n---\n"

    # Update trends.md
    filename = "trends.md"
    main_header = "# Google Trends Merch Opportunities\n\n"

    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            old_content = f.read()

        if main_header in old_content:
            new_file_content = old_content.replace(main_header, main_header + content + "\n")
        else:
            new_file_content = main_header + content + "\n" + old_content
    else:
        new_file_content = main_header + content

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(new_file_content)

    print(f"Successfully updated {filename}")

if __name__ == "__main__":
    main()
