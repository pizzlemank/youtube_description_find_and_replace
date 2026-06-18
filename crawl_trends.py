import pandas as pd
from pytrends.request import TrendReq
import time
import datetime
import os
import re

# Configuration
SEED_KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]
TIMEFRAME = 'now 7-d'
GEO = ''  # Worldwide

# IP Blacklist - Extensive list of brands, franchises, and celebrities
IP_BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "taylor swift", "bts", "michael jackson",
    "nba", "wnba", "nfl", "mlb", "nhl", "nintendo", "pokemon", "harry potter", "nasa",
    "hellstar", "ysl", "gucci", "prada", "louis vuitton", "arsenal", "real madrid", "liverpool",
    "man city", "chelsea", "bayern", "barcelona", "knicks", "lakers", "celtics", "warriors",
    "bulls", "amiri", "trapstar", "corteiz", "sp5der", "minus two", "syna world", "harry styles",
    "gracie abrams", "daniel caesar", "bad bunny", "billie eilish", "drake", "kanye",
    "travis scott", "bruno mars", "hello kitty", "sanrio", "nascar", "f1", "mercedes",
    "ferrari", "red bull", "toy story", "psg", "asap rocky", "megan moroney", "sean john",
    "morgan wallen", "spurs", "rcb", "snipes", "asos", "pattie gonia", "wingstop",
    "ariana grande", "selena gomez", "carhartt", "hazbin hotel", "digital circus", "tadc",
    "linkin park", "bad omens", "forrest frank", "malcolm todd", "böhse onkelz", "love island",
    "eternal sunshine", "madewell", "anthropologie", "glitch", "stevie nicks", "beyonce",
    "lilibet", "olivia rodrigo", "caitlin clark", "sabrina carpenter"
]

# Exclusion list for generic or non-commercial terms
EXCLUSIONS = [
    "meaning", "definition", "how to", "why", "iron", "near me", "template", "mockup",
    "tee times", "tee time", "tee off", "graphic tee", "essential tee", "vintage tee",
    "oversized tee", "plain shirt", "blank shirt", "kaffee", "rezepte", "bh für", "bra for",
    "tutorial", "bra", "t-shirt bra", "là gì"
]

def is_ip_infringing(keyword):
    keyword_lower = keyword.lower()
    for term in IP_BLACKLIST:
        if re.search(r'\b' + re.escape(term) + r'\b', keyword_lower):
            return True
    return False

def should_exclude(keyword):
    keyword_lower = keyword.lower()
    # Check if keyword is too short or just one of the seeds
    if len(keyword_lower.split()) < 2:
        return True
    if keyword_lower in [s.lower() for s in SEED_KEYWORDS]:
        return True
    for term in EXCLUSIONS:
        if term in keyword_lower:
            return True
    return False

def get_rising_queries(pytrends, keyword):
    print(f"Fetching rising queries for: {keyword}")
    try:
        pytrends.build_payload([keyword], timeframe=TIMEFRAME, geo=GEO)
        related_queries = pytrends.related_queries()
        if keyword in related_queries and related_queries[keyword]['rising'] is not None:
            return related_queries[keyword]['rising']
        else:
            return pd.DataFrame()
    except Exception as e:
        print(f"Error fetching {keyword}: {e}")
        if "429" in str(e):
            print("Rate limit hit. Sleeping for 30s...")
            time.sleep(30)
            # One retry
            try:
                pytrends.build_payload([keyword], timeframe=TIMEFRAME, geo=GEO)
                related_queries = pytrends.related_queries()
                if keyword in related_queries and related_queries[keyword]['rising'] is not None:
                    return related_queries[keyword]['rising']
            except:
                pass
        return pd.DataFrame()

def generate_idea(keyword):
    idea = keyword
    # Remove apparel terms to get the core concept
    for term in ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch", "tshirts", "t-shirts", "shirts"]:
        idea = re.sub(r'\b' + re.escape(term) + r'\b', '', idea, flags=re.IGNORECASE)
    idea = idea.strip()
    idea = re.sub(r'\s+', ' ', idea)
    return f"Design featuring '{idea}'. Trends suggest rising interest in this specific apparel niche."

def main():
    pytrends = TrendReq(hl='en-US', tz=360)

    all_results = []
    seen_keywords = set()

    for kw in SEED_KEYWORDS:
        df = get_rising_queries(pytrends, kw)
        if not df.empty:
            for index, row in df.iterrows():
                query = row['query']
                score = row['value']

                if query not in seen_keywords and not should_exclude(query):
                    seen_keywords.add(query)
                    all_results.append({
                        'keyword': query,
                        'score': score,
                        'infringing': is_ip_infringing(query)
                    })
        time.sleep(5) # Delay between seeds

    if not all_results:
        print("No results found.")
        return

    # Sort by score descending
    def sort_score(val):
        if val == 'Breakout':
            return 9999
        try:
            return int(val)
        except:
            return 0

    all_results.sort(key=lambda x: sort_score(x['score']), reverse=True)

    general_merch = [r for r in all_results if not r['infringing']]
    ip_infringing = [r for r in all_results if r['infringing']]

    today = datetime.date.today().strftime("%Y-%m-%d")
    date_header = f"## {today}"

    # Read existing content
    if os.path.exists("trends.md"):
        with open("trends.md", "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = "# Google Trends Merch Opportunities\n"

    if date_header in content:
        print(f"Results for {today} already exist in trends.md. Skipping update to avoid duplicates.")
        return

    output = f"\n{date_header}\n\n"

    output += "### General Merch Opportunities\n\n"
    if general_merch:
        output += "| Keyword | Score | Why/Idea |\n"
        output += "| :--- | :--- | :--- |\n"
        for item in general_merch:
            idea = generate_idea(item['keyword'])
            output += f"| {item['keyword']} | {item['score']} | {idea} |\n"
    else:
        output += "No new general opportunities found today.\n"

    output += "\n### Potential IP Infringing Opportunities\n\n"
    if ip_infringing:
        output += "| Keyword | Score | Why/Idea |\n"
        output += "| :--- | :--- | :--- |\n"
        for item in ip_infringing:
            idea = generate_idea(item['keyword'])
            output += f"| {item['keyword']} | {item['score']} | {idea} |\n"
    else:
        output += "No potential IP infringing opportunities found today.\n"

    lines = content.splitlines(keepends=True)
    if not lines:
        lines = ["# Google Trends Merch Opportunities\n"]

    # Insert after header
    new_content = [lines[0], output] + lines[1:]

    with open("trends.md", "w", encoding="utf-8") as f:
        f.writelines(new_content)

    print(f"Updated trends.md with {len(all_results)} new entries.")

if __name__ == "__main__":
    main()
