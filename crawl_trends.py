import pandas as pd
from pytrends.request import TrendReq
import datetime
import os
import time
import re

def crawl_trends():
    # hl='en-US', tz=360 (CST)
    pytrends = TrendReq(hl='en-US', tz=360)

    # Core seed keywords to find merch opportunities
    seed_keywords = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]

    all_rising = []

    for kw in seed_keywords:
        print(f"Fetching trends for {kw}...")
        # retry logic for rate limiting
        for attempt in range(3):
            try:
                pytrends.build_payload([kw], timeframe='now 7-d')
                related_queries = pytrends.related_queries()

                if kw in related_queries:
                    rising = related_queries[kw]['rising']
                    if rising is not None:
                        all_rising.append(rising)

                # Sleep to avoid rate limiting
                time.sleep(5)
                break
            except Exception as e:
                print(f"Error fetching {kw} (attempt {attempt+1}): {e}")
                time.sleep(60) # Wait longer on error
                continue

    if not all_rising:
        print("No trends found.")
        return

    df = pd.concat(all_rising).drop_duplicates(subset=['query'])

    # Handle 'Breakout' values by assigning a high numeric value for sorting
    def parse_value(val):
        if isinstance(val, str) and val.lower() == 'breakout':
            return 9999
        try:
            return int(val)
        except:
            return 0

    df['score_numeric'] = df['value'].apply(parse_value)
    df = df.sort_values(by='score_numeric', ascending=False)

    # IP Infringing Keywords / Brands / Teams
    ip_blacklist = [
        "disney", "marvel", "star wars", "nike", "adidas", "taylor swift", "bts",
        "michael jackson", "nba", "wnba", "nfl", "mlb", "nhl", "nintendo", "pokemon",
        "harry potter", "nasa", "hellstar", "ysl", "gucci", "prada", "louis vuitton",
        "arsenal", "real madrid", "liverpool", "man city", "chelsea", "bayern", "barcelona",
        "knicks", "lakers", "celtics", "warriors", "bulls", "amiri", "trapstar", "corteiz",
        "sp5der", "minus two", "syna world", "harry styles", "gracie abrams", "daniel caesar",
        "bad bunny", "billie eilish", "drake", "kanye", "travisscott", "travis scott"
    ]

    # Terms that indicate the result is NOT a merch opportunity or is too generic
    exclusion_list = [
        "meaning", "definition", "how to", "why", "iron", "near me", "template", "mockup",
        "tee times", "tee time", "tee off", "graphic tee", "essential tee", "vintage tee",
        "oversized tee", "plain shirt", "blank shirt", "kaffee", "rezepte", "bh für", "bra for",
        "tutorial", "là gì"
    ]

    # Also exclude exact matches of seed keywords if they are too generic
    generic_filters = ["t shirt", "t-shirts", "tees", "shirts", "merch"]

    infringing = []
    opportunities = []
    processed_keywords = set()

    for _, row in df.iterrows():
        query = row['query'].lower().strip()
        score = row['value']

        # 1. Long tail check (2+ words)
        if len(query.split()) < 2:
            continue

        # 2. Exclusion list check
        if any(excl in query for excl in exclusion_list):
            continue

        # 3. Generic filter check
        if query in generic_filters:
            continue

        # 4. Deduplication
        if query in processed_keywords:
            continue
        processed_keywords.add(query)

        # Check IP infringement
        is_infringing = any(brand in query for brand in ip_blacklist)

        # Generate idea/context
        idea = generate_idea(query)

        entry = {
            "keyword": query,
            "score": score,
            "idea": idea
        }

        if is_infringing:
            infringing.append(entry)
        else:
            opportunities.append(entry)

    update_trends_md(opportunities, infringing)

def generate_idea(query):
    # Clean the query for better idea generation
    # Remove common apparel terms to find the "concept"
    concept = query
    apparel_terms = ["t-shirt", "tshirt", "t shirt", "shirt", "tank top", "tanktop", "tee", "merch"]
    for term in sorted(apparel_terms, key=len, reverse=True):
        concept = concept.replace(term, "")

    concept = re.sub(r'\s+', ' ', concept).strip()

    if not concept:
        concept = query

    return f"Niche concept: '{concept}'. This is trending as a rising search term. Design idea: Combine this concept with a unique illustrative style (vintage, minimalist, or street-wear)."

def update_trends_md(opportunities, infringing):
    today = datetime.date.today().strftime("%Y-%m-%d")

    # Check if we already have entries for today to avoid duplicates if run multiple times
    if os.path.exists("trends.md"):
        with open("trends.md", "r") as f:
            first_line = f.readline()
            if f"## {today}" in first_line:
                print(f"Trends for {today} already exist in trends.md. Skipping update.")
                return

    content = f"## {today}\n\n"

    content += "### General Merch Opportunities\n"
    content += "| Keyword | Score | Why/Idea |\n"
    content += "|---------|-------|----------|\n"
    for opt in opportunities[:50]: # Limit to top 50
        content += f"| {opt['keyword']} | {opt['score']} | {opt['idea']} |\n"

    content += "\n### Potential IP Infringing Opportunities\n"
    content += "| Keyword | Score | Why/Idea |\n"
    content += "|---------|-------|----------|\n"
    for inf in infringing[:20]: # Limit to top 20
        content += f"| {inf['keyword']} | {inf['score']} | {inf['idea']} |\n"

    content += "\n---\n\n"

    if os.path.exists("trends.md"):
        with open("trends.md", "r") as f:
            old_content = f.read()
    else:
        old_content = ""

    with open("trends.md", "w") as f:
        f.write(content + old_content)
    print(f"trends.md updated for {today}")

if __name__ == "__main__":
    crawl_trends()
