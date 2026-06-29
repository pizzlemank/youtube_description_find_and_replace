import datetime
import os
import re
import time
import pandas as pd
from pytrends.request import TrendReq

# Configuration
KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]
TRENDS_FILE = "trends.md"
IP_BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "taylor swift", "bts",
    "michael jackson", "nba", "wnba", "nfl", "mlb", "nhl", "nintendo",
    "pokemon", "harry potter", "nasa", "hellstar", "ysl", "gucci", "prada",
    "louis vuitton", "arsenal", "real madrid", "liverpool", "man city", "chelsea",
    "bayern", "barcelona", "knicks", "lakers", "celtics", "warriors", "bulls",
    "amiri", "trapstar", "corteiz", "sp5der", "minus two", "syna world",
    "harry styles", "gracie abrams", "daniel caesar", "bad bunny", "billie eilish",
    "drake", "kanye", "travis scott", "bruno mars", "hello kitty", "sanrio",
    "nascar", "f1", "mercedes", "ferrari", "red bull", "toy story", "psg",
    "asap rocky", "megan moroney", "sean john", "morgan wallen", "spurs", "rcb",
    "snipes", "asos", "pattie gonia", "wingstop", "ariana grande", "selena gomez",
    "carhartt", "hazbin hotel", "digital circus", "tadc", "linkin park", "bad omens",
    "forrest frank", "malcolm todd", "böhse onkelz", "love island", "eternal sunshine",
    "madewell", "anthropologie", "glitch", "stevie nicks", "beyonce", "lilibet",
    "olivia rodrigo", "caitlin clark", "sabrina carpenter", "messi", "ronaldo",
    "spiderman", "spider-man", "batman", "superman", "fifa", "uefa", "palace",
    "kobe", "cowboys", "yankees", "dodgers", "dfb", "hilary duff", "lewis capaldi",
    "radiohead", "beabadoobee", "phoebe bridgers", "kmfdm", "ye", "jackass",
    "runescape", "supergirl"
]

EXCLUDE_KEYWORDS = [
    "meaning", "definition", "how to", "why", "iron", "near me", "template", "mockup",
    "tee times", "tee time", "tee off", "graphic tee", "essential tee", "vintage tee",
    "oversized tee", "plain shirt", "blank shirt", "kaffee", "rezepte", "bh für", "bra for",
    "tutorial", "bra", "t-shirt bra", "tee height", "là gì"
]

def is_ip_infringing(keyword):
    keyword_lower = keyword.lower()
    for brand in IP_BLACKLIST:
        if re.search(rf"\b{brand}\b", keyword_lower):
            return True
    return False

def generate_idea(keyword):
    # Simple logic to generate a design idea
    # Replace common apparel terms to get the core niche
    clean_keyword = keyword.lower()
    for term in ["tshirt", "t-shirt", "tank top", "tanktop", "shirt", "merch", "tee"]:
        clean_keyword = clean_keyword.replace(term, "")

    clean_keyword = clean_keyword.strip()
    if not clean_keyword:
        clean_keyword = keyword

    return f"Niche: {clean_keyword}. Design idea: Graphic featuring '{clean_keyword}' in a trendy style (vintage, minimalist, or streetwear). Internet search shows rising interest in this specific apparel variation."

def fetch_trends():
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
                    rising_df = related_queries[kw]['rising']
                    for _, row in rising_df.iterrows():
                        query = row['query']
                        query_lower = query.lower()
                        value = row['value']

                        # Filter: long tail (2+ words)
                        if len(query.split()) >= 2:
                            # Skip generic terms
                            if query_lower in ["t shirt", "t-shirt", "tank top", "tanktop", "tee shirt"]:
                                continue

                            # Skip excluded keywords
                            if any(ex in query_lower for ex in EXCLUDE_KEYWORDS):
                                continue

                            all_rising.append({'keyword': query, 'score': value})

                # Sleep to avoid rate limiting
                time.sleep(5)
                break
            except Exception as e:
                print(f"Error fetching {kw}: {e}")
                if "429" in str(e):
                    print("Rate limited. Sleeping for 10s and retrying...")
                    time.sleep(10)
                    retries -= 1
                else:
                    break

    # Deduplicate
    unique_trends = {t['keyword']: t for t in all_rising}.values()
    return list(unique_trends)

def update_trends_md(trends):
    if not trends:
        print("No new trends found.")
        return

    today = datetime.date.today().strftime("%Y-%m-%d")

    general_merch = []
    ip_infringing = []

    for t in trends:
        entry = {
            'keyword': t['keyword'],
            'score': t['score'],
            'idea': generate_idea(t['keyword'])
        }
        if is_ip_infringing(t['keyword']):
            ip_infringing.append(entry)
        else:
            general_merch.append(entry)

    # Sort by score descending
    def sort_score(val):
        if isinstance(val, int):
            return val
        if str(val).lower() == 'breakout':
            return 999999 # Very high value for breakout
        try:
            return int(val)
        except:
            return 0

    general_merch.sort(key=lambda x: sort_score(x['score']), reverse=True)
    ip_infringing.sort(key=lambda x: sort_score(x['score']), reverse=True)

    # Check if we already have entries for today to avoid duplicates
    existing_content = ""
    if os.path.exists(TRENDS_FILE):
        with open(TRENDS_FILE, "r") as f:
            existing_content = f.read()

    if f"## {today}" in existing_content:
        print(f"Trends for {today} already exist in {TRENDS_FILE}. Skipping update.")
        return

    new_content = f"## {today}\n\n"

    if general_merch:
        new_content += "### General Merch Opportunities\n"
        new_content += "| Keyword | Score | Why/Idea |\n"
        new_content += "|---------|-------|----------|\n"
        for item in general_merch:
            new_content += f"| {item['keyword']} | {item['score']} | {item['idea']} |\n"
        new_content += "\n"

    if ip_infringing:
        new_content += "### Potential IP Infringing Opportunities\n"
        new_content += "| Keyword | Score | Why/Idea |\n"
        new_content += "|---------|-------|----------|\n"
        for item in ip_infringing:
            new_content += f"| {item['keyword']} | {item['score']} | {item['idea']} |\n"
        new_content += "\n"

    # Prepend new content
    header = "# Google Trends Merch Opportunities\n\n"
    if header in existing_content:
        updated_content = existing_content.replace(header, header + new_content)
    else:
        updated_content = header + new_content + existing_content

    with open(TRENDS_FILE, "w") as f:
        f.write(updated_content)

    print(f"Updated {TRENDS_FILE} with {len(trends)} trends.")

if __name__ == "__main__":
    trends_data = fetch_trends()
    update_trends_md(trends_data)
