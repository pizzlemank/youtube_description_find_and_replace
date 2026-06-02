import pandas as pd
from pytrends.request import TrendReq
import time
import datetime
import os
import re

# Configuration
KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]
TIMEFRAME = "now 7-d"
RETRIES = 3
RETRY_DELAY = 60
QUERY_DELAY = 5

IP_BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "taylor swift", "bts",
    "michael jackson", "nba", "wnba", "nfl", "mlb", "nhl", "nintendo", "pokemon",
    "harry potter", "nasa", "hellstar", "ysl", "gucci", "prada", "louis vuitton",
    "arsenal", "real madrid", "liverpool", "man city", "chelsea", "bayern",
    "barcelona", "knicks", "lakers", "celtics", "warriors", "bulls", "amiri",
    "trapstar", "corteiz", "sp5der", "minus two", "syna world", "harry styles",
    "gracie abrams", "daniel caesar", "bad bunny", "billie eilish", "drake",
    "kanye", "travis scott", "bruno mars", "hello kitty", "sanrio", "nascar",
    "f1", "mercedes", "ferrari", "red bull", "toy story", "psg", "asap rocky",
    "megan moroney", "sean john", "morgan wallen", "spurs", "rcb", "snipes",
    "asos", "pattie gonia", "wingstop"
]

IRRELEVANT_TERMS = [
    "meaning", "definition", "how to", "why", "iron", "near me", "template",
    "mockup", "tee times", "tee time", "tee off", "graphic tee", "essential tee",
    "vintage tee", "oversized tee", "plain shirt", "blank shirt", "kaffee",
    "rezepte", "bh für", "bra for", "tutorial", "là gì"
]

APPAREL_TERMS = ["tshirts", "t-shirts", "shirts", "tank tops", "tanktops", "tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]

def get_pytrends():
    return TrendReq(hl='en-US', tz=360)

def fetch_rising_queries(pytrends, keyword):
    for attempt in range(RETRIES):
        try:
            pytrends.build_payload([keyword], timeframe=TIMEFRAME)
            related_queries = pytrends.related_queries()
            if keyword in related_queries and related_queries[keyword]['rising'] is not None:
                return related_queries[keyword]['rising']
            return pd.DataFrame()
        except Exception as e:
            if "429" in str(e) and attempt < RETRIES - 1:
                print(f"Rate limited. Sleeping for {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                print(f"Error fetching {keyword}: {e}")
                break
    return pd.DataFrame()

def is_ip_infringing(query):
    query_lower = query.lower()
    for brand in IP_BLACKLIST:
        if brand in query_lower:
            return True
    return False

def is_irrelevant(query):
    query_lower = query.lower()
    # Filter out generic keyword variations
    if query_lower in ["t shirt", "t-shirts", "tees", "shirt", "tshirt"]:
        return True

    # Must contain at least one apparel term to be relevant to the request
    has_apparel_term = any(term in query_lower for term in ["shirt", "tshirt", "t-shirt", "tank top", "tanktop", "tee", "merch"])
    if not has_apparel_term:
        return True

    for term in IRRELEVANT_TERMS:
        if term in query_lower:
            return True
    # Long tail check (2+ words)
    if len(query.split()) < 2:
        return True
    return False

def generate_idea(query):
    idea = query
    for term in APPAREL_TERMS:
        # Use regex for case-insensitive replacement of whole words
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        idea = pattern.sub("", idea)

    idea = re.sub(r'\s+', ' ', idea).strip()
    if not idea:
        return f"Design related to '{query}'"
    return f"Graphic design featuring '{idea}' theme"

def main():
    pytrends = get_pytrends()
    all_results = []
    seen_keywords = set()

    for kw in KEYWORDS:
        print(f"Fetching trends for: {kw}")
        df = fetch_rising_queries(pytrends, kw)
        if not df.empty:
            for _, row in df.iterrows():
                query = row['query']
                value = row['value']

                if query in seen_keywords:
                    continue

                if is_irrelevant(query):
                    continue

                seen_keywords.add(query)

                score = 9999 if value == 'Breakout' else int(value)
                is_ip = is_ip_infringing(query)
                idea = generate_idea(query)

                all_results.append({
                    'keyword': query,
                    'score': score,
                    'display_score': value,
                    'idea': idea,
                    'is_ip': is_ip
                })

        time.sleep(QUERY_DELAY)

    if not all_results:
        print("No new trends found.")
        return

    # Sort by score descending
    all_results.sort(key=lambda x: x['score'], reverse=True)

    general_merch = [r for r in all_results if not r['is_ip']]
    ip_merch = [r for r in all_results if r['is_ip']]

    date_str = datetime.date.today().strftime("%Y-%m-%d")
    header = f"## {date_str}\n\n"

    content = ""
    if general_merch:
        content += "### General Merch Opportunities\n"
        content += "| Keyword | Score | Why/Idea |\n"
        content += "| --- | --- | --- |\n"
        for r in general_merch:
            content += f"| {r['keyword']} | {r['display_score']} | {r['idea']} |\n"
        content += "\n"

    if ip_merch:
        content += "### Potential IP Infringing Opportunities\n"
        content += "| Keyword | Score | Why/Idea |\n"
        content += "| --- | --- | --- |\n"
        for r in ip_merch:
            content += f"| {r['keyword']} | {r['display_score']} | {r['idea']} |\n"
        content += "\n"

    filename = "trends.md"
    title = "# Google Trends Merch Opportunities\n\n"

    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            existing_content = f.read()

        if f"## {date_str}" in existing_content:
            print(f"Trends for {date_str} already exist in {filename}. Skipping update.")
            return

        # Keep the title at the top, prepend new content below it
        if existing_content.startswith("# Google Trends"):
            body = existing_content[len(title):]
            new_content = title + header + content + body
        else:
            new_content = header + content + existing_content
    else:
        new_content = title + header + content

    with open(filename, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"Successfully updated {filename}")

if __name__ == "__main__":
    main()
