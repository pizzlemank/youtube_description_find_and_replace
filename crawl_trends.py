import pandas as pd
from pytrends.request import TrendReq
import time
from datetime import datetime
import os
import re

# Configuration
SEED_KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]
TIMEFRAME = 'now 7-d'
IP_BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "taylor swift", "bts", "michael jackson",
    "nba", "wnba", "nfl", "mlb", "nhl", "nintendo", "pokemon", "harry potter", "nasa",
    "hellstar", "ysl", "gucci", "prada", "louis vuitton", "arsenal", "real madrid",
    "liverpool", "man city", "chelsea", "bayern", "barcelona", "knicks", "lakers",
    "celtics", "warriors", "bulls", "amiri", "trapstar", "corteiz", "sp5der", "minus two",
    "syna world", "harry styles", "gracie abrams", "daniel caesar", "bad bunny",
    "billie eilish", "drake", "kanye", "travis scott", "bruno mars", "hello kitty",
    "sanrio", "nascar", "f1", "mercedes", "ferrari", "red bull"
]

EXCLUDE_KEYWORDS = [
    "meaning", "definition", "how to", "why", "iron", "near me", "template", "mockup",
    "tee times", "tee time", "tee off", "graphic tee", "essential tee", "vintage tee",
    "oversized tee", "plain shirt", "blank shirt", "kaffee", "rezepte", "bh für",
    "bra for", "tutorial", "là gì"
]

APPAREL_TERMS = [
    "shirts", "tshirts", "t-shirts", "tank tops", "tanktops", "tees",
    "shirt", "tshirt", "t-shirt", "tank top", "tanktop", "tee", "merch"
]

def get_pytrends():
    return TrendReq(hl='en-US', tz=360)

def fetch_trends_with_retry(pytrends, kw_list):
    for attempt in range(3):
        try:
            pytrends.build_payload(kw_list, cat=0, timeframe=TIMEFRAME, geo='', gprop='')
            return pytrends.related_queries()
        except Exception as e:
            if "429" in str(e):
                print(f"Rate limit hit, retrying in 60s... (Attempt {attempt+1}/3)")
                time.sleep(60)
            else:
                print(f"Error fetching trends for {kw_list}: {e}")
                break
    return None

def is_ip_infringing(keyword):
    keyword_lower = keyword.lower()
    for ip in IP_BLACKLIST:
        if ip in keyword_lower:
            return True
    return False

def is_relevant(keyword):
    keyword_lower = keyword.lower()

    # Must be long tail (at least 2 words)
    if len(keyword_lower.split()) < 2:
        return False

    # Must contain an apparel term
    if not any(term in keyword_lower for term in APPAREL_TERMS):
        return False

    # Must not contain excluded keywords
    if any(ex in keyword_lower for ex in EXCLUDE_KEYWORDS):
        return False

    # Filter out generic seed keywords
    for seed in SEED_KEYWORDS:
        if keyword_lower == seed or keyword_lower == seed + "s":
            return False

    return True

def generate_idea(keyword):
    # Simple logic to generate a design idea by stripping apparel terms
    idea_base = keyword.lower()
    # Replace longer terms first
    for term in sorted(APPAREL_TERMS, key=len, reverse=True):
        idea_base = idea_base.replace(term, "")

    idea_base = re.sub(' +', ' ', idea_base).strip()
    if not idea_base:
        return "Generic apparel design"

    return f"Design featuring '{idea_base.title()}' concept. Popular rising search indicating market interest."

def main():
    pytrends = get_pytrends()
    all_results = []
    seen_keywords = set()

    for kw in SEED_KEYWORDS:
        print(f"Fetching related queries for: {kw}")
        results = fetch_trends_with_retry(pytrends, [kw])
        time.sleep(5) # Small delay to avoid 429

        if results and kw in results:
            rising = results[kw]['rising']
            if rising is not None and not rising.empty:
                for index, row in rising.iterrows():
                    keyword = row['query']
                    score = row['value']

                    if keyword not in seen_keywords and is_relevant(keyword):
                        seen_keywords.add(keyword)
                        all_results.append({
                            'keyword': keyword,
                            'score': score,
                            'ip_infringing': is_ip_infringing(keyword)
                        })

    if not all_results:
        print("No new trends found.")
        return

    # Sort by score descending, Breakout (treated as 9999) first
    def sort_score(val):
        if isinstance(val, str) and 'breakout' in val.lower():
            return 9999
        try:
            return int(val)
        except:
            return 0

    all_results.sort(key=lambda x: sort_score(x['score']), reverse=True)

    # Prepare markdown sections
    general_ops = []
    ip_ops = []

    for res in all_results:
        row = f"| {res['keyword']} | {res['score']} | {generate_idea(res['keyword'])} |"
        if res['ip_infringing']:
            ip_ops.append(row)
        else:
            general_ops.append(row)

    date_str = datetime.now().strftime("%Y-%m-%d")
    new_content = f"## {date_str}\n\n### General Merch Opportunities\n"
    new_content += "| Keyword | Score | Why/Idea |\n| :--- | :--- | :--- |\n"
    new_content += "\n".join(general_ops) + "\n\n"

    if ip_ops:
        new_content += "### Potential IP Infringing Opportunities\n"
        new_content += "| Keyword | Score | Why/Idea |\n| :--- | :--- | :--- |\n"
        new_content += "\n".join(ip_ops) + "\n\n"

    # Read existing content
    file_path = 'trends.md'
    title = "# Google Trends Merch Opportunities\n\n"
    existing_body = ""

    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if f"## {date_str}" in content:
                print(f"Trends for {date_str} already exist in {file_path}. Skipping update.")
                return

            lines = content.splitlines(keepends=True)
            if lines:
                # If first line is title, skip it for the body
                if lines[0].startswith("# "):
                    existing_body = "".join(lines[1:]).lstrip()
                else:
                    existing_body = "".join(lines).lstrip()

    # Prepend new content
    full_content = title + new_content + existing_body

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(full_content)

    print(f"Successfully updated {file_path} with {len(all_results)} trends.")

if __name__ == "__main__":
    main()
