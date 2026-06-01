import os
import pandas as pd
from pytrends.request import TrendReq
from datetime import datetime
import time
import re

# Configuration
SEED_KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]
TRENDS_FILE = "trends.md"
IP_BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "taylor swift", "bts", "michael johnson",
    "nba", "wnba", "nfl", "mlb", "nhl", "nintendo", "pokemon", "harry potter", "nasa",
    "hellstar", "ysl", "gucci", "prada", "louis vuitton", "arsenal", "real madrid", "liverpool",
    "man city", "chelsea", "bayern", "barcelona", "knicks", "lakers", "celtics", "warriors", "bulls",
    "amiri", "trapstar", "corteiz", "sp5der", "minus two", "syna world", "harry styles",
    "gracie abrams", "daniel caesar", "bad bunny", "billie eilish", "drake", "kanye", "travis scott",
    "bruno mars", "hello kitty", "sanrio", "nascar", "f1", "mercedes", "ferrari", "red bull"
]

EXCLUDE_KEYWORDS = [
    "meaning", "definition", "how to", "why", "iron", "near me", "template", "mockup",
    "tee times", "tee time", "tee off", "graphic tee", "essential tee", "vintage tee", "oversized tee",
    "plain shirt", "blank shirt", "kaffee", "rezepte", "bh für", "bra for", "tutorial", "là gì"
]

def is_ip_infringing(query):
    query_lower = query.lower()
    for brand in IP_BLACKLIST:
        if brand in query_lower:
            return True
    return False

def generate_idea(query):
    # Simple rule-based idea generation
    query_clean = query.lower()
    # Sort by length descending to replace longer terms first (e.g., 'tshirt' before 'shirt')
    sorted_seeds = sorted(SEED_KEYWORDS, key=len, reverse=True)
    for term in sorted_seeds:
        query_clean = query_clean.replace(term, "").strip()

    # Handle plural cases too
    for term in sorted_seeds:
        query_clean = query_clean.replace(term + "s", "").strip()

    query_clean = re.sub(r'\s+', ' ', query_clean)

    if not query_clean:
        return "Generic apparel design based on the trend."

    return f"Create a unique design focusing on '{query_clean}'. Look for aesthetic styles like vintage, minimalist, or streetwear that appeal to this niche."

def fetch_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    all_results = []

    for kw in SEED_KEYWORDS:
        print(f"Fetching trends for: {kw}")
        try:
            # Build payload with a retry mechanism for rate limits
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='', gprop='')
                    related_queries = pytrends.related_queries()
                    break
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries - 1:
                        print(f"Rate limited. Waiting 60s... (Attempt {attempt+1}/{max_retries})")
                        time.sleep(60)
                    else:
                        raise e

            rising = related_queries[kw]['rising']
            if rising is not None and not rising.empty:
                for _, row in rising.iterrows():
                    query = row['query']
                    score = row['value']

                    # Filtering
                    query_lower = query.lower()

                    # 1. Must be long tail (at least 2 words)
                    if len(query.split()) < 2:
                        continue

                    # 2. Must contain an apparel term (implicitly handled by being a related query of SEED_KEYWORDS,
                    # but let's be explicit if we want specific long-tails)
                    # Actually, since it's a related query to "tshirt", it's likely relevant.

                    # 3. Exclude generic/irrelevant stuff
                    if any(exclude in query_lower for exclude in EXCLUDE_KEYWORDS):
                        continue

                    # 4. Avoid exact matches of seed keywords
                    if query_lower in SEED_KEYWORDS:
                        continue

                    all_results.append({
                        'keyword': query,
                        'score': score,
                        'is_ip': is_ip_infringing(query)
                    })
        except Exception as e:
            print(f"Error fetching {kw}: {e}")

        time.sleep(5) # Small delay between keywords

    return all_results

def update_markdown(results):
    if not results:
        print("No new results to add.")
        return

    today = datetime.now().strftime("%Y-%m-%d")

    general_merch = [r for r in results if not r['is_ip']]
    ip_infringing = [r for r in results if r['is_ip']]

    # Sort by score descending
    def get_score(val):
        if val == 'Breakout' or val == 'breakout':
            return 9999
        try:
            return int(val)
        except:
            return 0

    general_merch.sort(key=lambda x: get_score(x['score']), reverse=True)
    ip_infringing.sort(key=lambda x: get_score(x['score']), reverse=True)

    new_content = f"## {today}\n\n"

    new_content += "### General Merch Opportunities\n"
    new_content += "| Keyword | Score | Why/Idea |\n"
    new_content += "| :--- | :--- | :--- |\n"
    for item in general_merch:
        idea = generate_idea(item['keyword'])
        new_content += f"| {item['keyword']} | {item['score']} | {idea} |\n"

    new_content += "\n### Potential IP Infringing Opportunities\n"
    new_content += "| Keyword | Score | Why/Idea |\n"
    new_content += "| :--- | :--- | :--- |\n"
    for item in ip_infringing:
        new_content += f"| {item['keyword']} | {item['score']} | **Potential IP Infringement.** Study the trend but avoid direct use of protected assets. |\n"

    new_content += "\n---\n"

    # Read existing content
    if os.path.exists(TRENDS_FILE):
        with open(TRENDS_FILE, "r", encoding="utf-8") as f:
            existing_content = f.read()
    else:
        existing_content = "# Google Trends Merch Opportunities\n\n"

    # Find the position to insert (after the title)
    title_match = re.search(r"^# .*\n\n", existing_content)
    if title_match:
        insert_pos = title_match.end()
        # Check if today's header already exists to avoid duplicates if run multiple times same day
        if f"## {today}" in existing_content:
            print(f"Already updated for {today}.")
            return

        updated_content = existing_content[:insert_pos] + new_content + existing_content[insert_pos:]
    else:
        updated_content = existing_content + "\n" + new_content

    with open(TRENDS_FILE, "w", encoding="utf-8") as f:
        f.write(updated_content)

    print(f"Successfully updated {TRENDS_FILE}")

if __name__ == "__main__":
    results = fetch_trends()
    # Deduplicate results by keyword
    unique_results = []
    seen_keywords = set()
    for r in results:
        if r['keyword'].lower() not in seen_keywords:
            unique_results.append(r)
            seen_keywords.add(r['keyword'].lower())

    update_markdown(unique_results)
