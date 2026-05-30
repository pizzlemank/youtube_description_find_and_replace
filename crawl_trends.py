import pandas as pd
from pytrends.request import TrendReq
import datetime
import os
import time
import random
import re

# Initialize pytrends with retry logic for 429
def get_pytrends():
    return TrendReq(hl='en-US', tz=360)

# Keywords to search for
SEED_KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]

# IP Blacklist for flagging
IP_BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "taylor swift", "bts", "michael jackson",
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

def is_ip_infringing(keyword):
    keyword_lower = keyword.lower()
    for ip in IP_BLACKLIST:
        if ip in keyword_lower:
            return True
    return False

def get_rising_queries(seed_keywords):
    pytrends = get_pytrends()
    all_rising = []
    for kw in seed_keywords:
        print(f"Fetching trends for: {kw}")
        for attempt in range(3):
            try:
                pytrends.build_payload([kw], timeframe='now 7-d')
                related_queries = pytrends.related_queries()
                rising = related_queries[kw]['rising']
                if rising is not None:
                    rising['seed'] = kw
                    all_rising.append(rising)
                time.sleep(5)
                break
            except Exception as e:
                print(f"Error fetching {kw} (attempt {attempt+1}): {e}")
                if "429" in str(e):
                    time.sleep(60)
                else:
                    time.sleep(10)

    if not all_rising:
        return pd.DataFrame()

    return pd.concat(all_rising).drop_duplicates(subset=['query'])

def filter_and_format(df):
    if df.empty:
        return [], []

    general_merch = []
    ip_infringing = []
    seen_queries = set()

    apparel_terms = ["tank top", "tanktop", "t-shirt", "tshirt", "shirt", "tee", "merch"]

    for _, row in df.iterrows():
        query = row['query']
        value = row['value']

        if query in seen_queries:
            continue
        seen_queries.add(query)

        query_lower = query.lower()

        # Filter: Long tail (at least 2 words)
        words = query.split()
        if len(words) < 2:
            continue

        # Filter: Must contain an apparel-related term
        if not any(term in query_lower for term in apparel_terms):
            continue

        # Filter out generic terms or unwanted terms
        if any(ex in query_lower for ex in EXCLUDE_KEYWORDS):
            continue

        if query_lower in ["t shirt", "t-shirts", "tees", "shirts", "merch"]:
            continue

        # Idea generation
        design_concept = query_lower
        # Sort terms by length descending to avoid partial replacement (e.g., 't-shirt' before 'shirt')
        for term in sorted(apparel_terms, key=len, reverse=True):
            design_concept = design_concept.replace(term, "")

        # Clean up multiple spaces
        design_concept = re.sub(' +', ' ', design_concept).strip()

        if not design_concept:
            design_concept = query

        idea = f"Focus on a creative design around '{design_concept}'. Consider the current internet hype for this topic."

        entry = {
            "keyword": query,
            "score": value,
            "idea": idea
        }

        if is_ip_infringing(query):
            ip_infringing.append(entry)
        else:
            general_merch.append(entry)

    return general_merch, ip_infringing

def format_table(entries):
    if not entries:
        return "No new opportunities found."

    def sort_key(x):
        val = x['score']
        if val == 'Breakout' or (isinstance(val, str) and 'breakout' in val.lower()):
            return 9999
        try:
            return int(val)
        except:
            return 0

    sorted_entries = sorted(entries, key=sort_key, reverse=True)

    table = "| keyword | score | why you think is an opportunity, idea for design, or what the internet shopping is already doing |\n"
    table += "| :--- | :--- | :--- |\n"
    for entry in sorted_entries:
        keyword = entry['keyword'].replace("|", "\\|")
        idea = entry['idea'].replace("|", "\\|")
        table += f"| {keyword} | {entry['score']} | {idea} |\n"
    return table

def main():
    df = get_rising_queries(SEED_KEYWORDS)
    general_merch, ip_infringing = filter_and_format(df)

    today = datetime.date.today().strftime("%Y-%m-%d")

    new_content = f"## {today}\n\n"
    new_content += "### General Merch Opportunities\n"
    new_content += format_table(general_merch)
    new_content += "\n\n### Potential IP Infringing Opportunities\n"
    new_content += format_table(ip_infringing)
    new_content += "\n\n"

    filename = "trends.md"
    title = "# Merch Trends\n\n"

    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            old_content = f.read()
    else:
        old_content = title

    if f"## {today}" in old_content:
        print("Already updated today. Skipping.")
        return

    if old_content.startswith(title):
        body = old_content[len(title):]
    else:
        body = old_content

    full_content = title + new_content + body

    with open(filename, "w", encoding="utf-8") as f:
        f.write(full_content)

    print(f"Updated {filename} with {len(general_merch) + len(ip_infringing)} trends.")

if __name__ == "__main__":
    main()
