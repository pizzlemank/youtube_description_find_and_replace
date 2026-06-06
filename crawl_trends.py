import pandas as pd
from pytrends.request import TrendReq
import time
import datetime
import os
import re

# Configuration
KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]
TIMEFRAME = "now 7-d"
GEO = ""  # Worldwide
RETRY_DELAY = 60
MAX_RETRIES = 3
DELAY_BETWEEN_KEYWORDS = 5

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

EXCLUDE_KEYWORDS = [
    "meaning", "definition", "how to", "why", "iron", "near me", "template",
    "mockup", "tee times", "tee time", "tee off", "graphic tee", "essential tee",
    "vintage tee", "oversized tee", "plain shirt", "blank shirt", "kaffee",
    "rezepte", "bh für", "bra for", "tutorial", "là gì"
]

APPAREL_TERMS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]

def get_pytrends_with_retries():
    # Newer urllib3 versions might cause issues with method_whitelist, so we handle retries manually
    return TrendReq(hl='en-US', tz=360)

def fetch_trends(pytrends, keyword):
    for attempt in range(MAX_RETRIES):
        try:
            pytrends.build_payload([keyword], cat=0, timeframe=TIMEFRAME, geo=GEO, gprop='')
            related_queries = pytrends.related_queries()
            if keyword in related_queries and related_queries[keyword]['rising'] is not None:
                return related_queries[keyword]['rising']
            return pd.DataFrame()
        except Exception as e:
            if "429" in str(e):
                print(f"Rate limit hit for {keyword}. Retrying in {RETRY_DELAY} seconds... (Attempt {attempt+1}/{MAX_RETRIES})")
                time.sleep(RETRY_DELAY)
            else:
                print(f"Error fetching trends for {keyword}: {e}")
                break
    return pd.DataFrame()

def is_ip_infringing(keyword):
    keyword_lower = keyword.lower()
    for brand in IP_BLACKLIST:
        if brand in keyword_lower:
            return True
    return False

def should_exclude(keyword):
    keyword_lower = keyword.lower()
    # Check for excluded phrases
    for exclude in EXCLUDE_KEYWORDS:
        if exclude in keyword_lower:
            return True

    # Check if it's too short (less than 2 words)
    words = keyword.split()
    if len(words) < 2:
        return True

    # Check if it contains at least one apparel term
    has_apparel = False
    for term in APPAREL_TERMS:
        if term in keyword_lower:
            has_apparel = True
            break
    if not has_apparel:
        return True

    # Filter out generic apparel terms
    generic_matches = ["t shirt", "t-shirts", "tees", "tshirt", "t-shirt"]
    if keyword_lower in generic_matches:
        return True

    return False

def generate_idea(keyword):
    # Simple idea generation logic
    clean_keyword = keyword.lower()
    for term in ["tshirt", "t-shirt", "tank top", "tanktop", "merch", "shirts", "shirt", "tees", "tee"]:
        clean_keyword = clean_keyword.replace(term, "").strip()

    # Clean up multiple spaces
    clean_keyword = re.sub(' +', ' ', clean_keyword)

    if not clean_keyword:
        return "Trending apparel design based on search interest."

    return f"Create a minimalist or graphic design centered around '{clean_keyword.title()}'. The internet is searching for this specific niche, indicating high demand."

def process_trends():
    pytrends = get_pytrends_with_retries()
    all_results = []
    seen_keywords = set()

    for kw in KEYWORDS:
        print(f"Fetching trends for: {kw}")
        df = fetch_trends(pytrends, kw)
        if not df.empty:
            for _, row in df.iterrows():
                query = row['query']
                score = row['value']

                if query not in seen_keywords and not should_exclude(query):
                    seen_keywords.add(query)
                    is_ip = is_ip_infringing(query)
                    idea = generate_idea(query)

                    # Convert score to int or handle 'Breakout'
                    if score == 'Breakout':
                        numeric_score = 9999
                    else:
                        try:
                            numeric_score = int(score)
                        except:
                            numeric_score = 0

                    all_results.append({
                        'keyword': query,
                        'score': score,
                        'numeric_score': numeric_score,
                        'is_ip': is_ip,
                        'idea': idea
                    })
        time.sleep(DELAY_BETWEEN_KEYWORDS)

    if not all_results:
        print("No new trends found.")
        return

    # Sort results by numeric score descending
    all_results.sort(key=lambda x: x['numeric_score'], reverse=True)

    general_merch = [r for r in all_results if not r['is_ip']]
    ip_infringing = [r for r in all_results if r['is_ip']]

    today = datetime.date.today().strftime("%Y-%m-%d")

    # Read existing content
    content = ""
    if os.path.exists("trends.md"):
        with open("trends.md", "r", encoding="utf-8") as f:
            content = f.read()

    # Avoid duplicate entry for the same day
    if f"## {today}" in content:
        print(f"Trends for {today} already exist in trends.md. Skipping update.")
        return

    new_entry = f"## {today}\n\n"

    if general_merch:
        new_entry += "### General Merch Opportunities\n"
        new_entry += "| keyword | score | why you think is an opportunity, idea for design, or what the internet shopping is already doing |\n"
        new_entry += "| --- | --- | --- |\n"
        for r in general_merch:
            new_entry += f"| {r['keyword']} | {r['score']} | {r['idea']} |\n"
        new_entry += "\n"

    if ip_infringing:
        new_entry += "### Potential IP Infringing Opportunities\n"
        new_entry += "| keyword | score | why you think is an opportunity, idea for design, or what the internet shopping is already doing |\n"
        new_entry += "| --- | --- | --- |\n"
        for r in ip_infringing:
            new_entry += f"| {r['keyword']} | {r['score']} | {r['idea']} |\n"
        new_entry += "\n"

    # Prepend new entry
    title = "# Google Trends Merch Opportunities"

    if content.startswith(title):
        # Remove the title and any leading newlines from the old content
        content_body = content[len(title):].lstrip()
        final_content = f"{title}\n\n{new_entry}{content_body}"
    else:
        final_content = f"{title}\n\n{new_entry}{content}"

    with open("trends.md", "w", encoding="utf-8") as f:
        f.write(final_content)

    print(f"Successfully updated trends.md with {len(all_results)} new trends.")

if __name__ == "__main__":
    process_trends()
