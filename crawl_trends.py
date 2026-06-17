import os
import datetime
import pandas as pd
from pytrends.request import TrendReq
import time
import re

# Configuration
KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]
IP_BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "taylor swift", "bts",
    "michael jackson", "nba", "wnba", "nfl", "mlb", "nhl", "nintendo", "pokemon",
    "harry potter", "nasa", "hellstar", "ysl", "gucci", "prada", "louis vuitton",
    "arsenal", "real madrid", "liverpool", "man city", "chelsea", "bayern", "barcelona",
    "knicks", "lakers", "celtics", "warriors", "bulls", "amiri", "trapstar", "corteiz",
    "sp5der", "minus two", "syna world", "harry styles", "gracie abrams", "daniel caesar",
    "bad bunny", "billie eilish", "drake", "kanye", "travis scott", "bruno mars",
    "hello kitty", "sanrio", "nascar", "f1", "mercedes", "ferrari", "red bull",
    "toy story", "psg", "asap rocky", "megan moroney", "sean john", "morgan wallen",
    "spurs", "rcb", "snipes", "asos", "pattie gonia", "wingstop", "ariana grande",
    "selena gomez", "carhartt", "hazbin hotel", "digital circus", "tadc", "linkin park",
    "bad omens", "forrest frank", "malcolm todd", "böhse onkelz", "love island",
    "eternal sunshine", "madewell", "anthropologie", "glitch", "stevie nicks", "beyonce",
    "lilibet", "olivia rodrigo", "caitlin clark", "sabrina carpenter"
]

EXCLUDED_TERMS = [
    "meaning", "definition", "how to", "why", "iron", "near me", "template", "mockup",
    "tee times", "tee time", "tee off", "graphic tee", "essential tee", "vintage tee",
    "oversized tee", "plain shirt", "blank shirt", "kaffee", "rezepte", "bh für",
    "bra for", "tutorial", "bra", "t-shirt bra", "là gì"
]

APPAREL_TERMS = ["tshirt", "t-shirt", "tank top", "tanktop", "shirt", "tee", "merch"]

def is_ip_infringing(keyword):
    keyword_lower = keyword.lower()
    for brand in IP_BLACKLIST:
        if re.search(rf"\b{brand}\b", keyword_lower):
            return True
    return False

def generate_idea(keyword):
    # Simple idea generation logic
    clean_keyword = keyword.lower()
    # Replace longer terms first to avoid partial matches (e.g., "shirt" in "tshirt")
    for term in sorted(APPAREL_TERMS, key=len, reverse=True):
        clean_keyword = clean_keyword.replace(term + "s", "").replace(term, "")

    clean_keyword = re.sub(r'\s+', ' ', clean_keyword).strip()

    if not clean_keyword:
        return "Generic apparel trend."

    return f"Create a unique graphic design focusing on '{clean_keyword}'. Look for niche-specific aesthetic (vintage, minimalist, or bold typography)."

def fetch_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    all_results = []

    for kw in KEYWORDS:
        print(f"Fetching trends for: {kw}")
        try:
            pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='', gprop='')
            related_queries = pytrends.related_queries()

            if kw in related_queries:
                rising = related_queries[kw]['rising']
                if rising is not None and not rising.empty:
                    all_results.append(rising)

            # Sleep to avoid rate limiting
            time.sleep(5)
        except Exception as e:
            print(f"Error fetching {kw}: {e}")
            if "429" in str(e):
                print("Rate limit hit, sleeping longer...")
                time.sleep(30)

    if not all_results:
        return pd.DataFrame()

    df = pd.concat(all_results).drop_duplicates(subset='query')
    return df

def process_trends(df):
    if df.empty:
        return [], []

    general_merch = []
    ip_infringing = []
    processed_keywords = set()

    for _, row in df.iterrows():
        query = row['query'].lower()
        score = row['value']

        # Long tail check (at least 2 words)
        words = query.split()
        if len(words) < 2:
            continue

        # Must contain an apparel term or be highly relevant to the seed
        if not any(term in query for term in APPAREL_TERMS):
            continue

        # Filter out generic searches or unwanted terms
        if any(term in query for term in EXCLUDED_TERMS):
            continue

        if any(term == query for term in APPAREL_TERMS) or any(term + "s" == query for term in APPAREL_TERMS):
            continue

        if query in processed_keywords:
            continue
        processed_keywords.add(query)

        idea = generate_idea(query)
        entry = {
            "keyword": query,
            "score": score,
            "idea": idea
        }

        if is_ip_infringing(query):
            ip_infringing.append(entry)
        else:
            general_merch.append(entry)

    # Sort by score, handling 'Breakout' as the highest value
    def get_score_value(entry):
        score = entry['score']
        if isinstance(score, str) and score.lower() == 'breakout':
            return 9999
        try:
            return int(score)
        except (ValueError, TypeError):
            return 0

    general_merch.sort(key=get_score_value, reverse=True)
    ip_infringing.sort(key=get_score_value, reverse=True)

    return general_merch, ip_infringing

def format_table(entries):
    if not entries:
        return "No significant trends found."

    table = "| keyword | score | Why/Idea |\n|---------|-------|----------|\n"
    for e in entries:
        # Replace 'Breakout' with a high number for display if needed, but here we just use what Google gives
        score_val = e['score']
        table += f"| {e['keyword']} | {score_val} | {e['idea']} |\n"
    return table

def update_trends_md(general, ip):
    today = datetime.date.today().strftime("%Y-%m-%d")

    content = f"## {today}\n\n"
    content += "### General Merch Opportunities\n\n"
    content += format_table(general)
    content += "\n\n"
    content += "### Potential IP Infringing Opportunities\n\n"
    content += format_table(ip)
    content += "\n\n---\n\n"

    filename = "trends.md"

    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            existing_content = f.read()

        # Check if today's entry already exists to avoid duplicates if run multiple times
        if f"## {today}" in existing_content:
            print(f"Entry for {today} already exists. Skipping update.")
            return

        # Prepend after the main header if it exists
        header_text = "# Google Trends Merch Opportunities"
        if existing_content.startswith(header_text):
            header = header_text + "\n\n"
            body = existing_content[len(header_text):].lstrip()
        else:
            body = existing_content

        new_content = header + content + body
    else:
        new_content = "# Google Trends Merch Opportunities\n\n" + content

    with open(filename, "w", encoding="utf-8") as f:
        f.write(new_content)

def main():
    df = fetch_trends()
    general, ip = process_trends(df)
    update_trends_md(general, ip)
    print("trends.md updated successfully.")

if __name__ == "__main__":
    main()
