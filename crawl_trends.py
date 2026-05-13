import time
import datetime
import os
import pandas as pd
import numpy as np
from pytrends.request import TrendReq
import pytrends.exceptions

# Configuration
KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]
APPAREL_TERMS = ["shirt", "tshirt", "t-shirt", "tank top", "tanktop", "tee", "merch"]
TRENDS_FILE = "trends.md"

# IP Blacklist - Expand this list as needed
IP_BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "taylor swift", "bts",
    "michael jackson", "nba", "wnba", "nfl", "mlb", "nhl", "nintendo", "pokemon",
    "harry potter", "nasa", "hellstar", "ysl", "gucci", "prada", "louis vuitton",
    "koningsdag", "oranje", "higgins", "wwe", "kanye", "drake", "notre dame",
    "ariana grande", "george strait", "olivia dean", "conan gray", "man utd",
    "lidl", "m&s", "mnet", "amc", "murder drones", "luke combs", "ohio state",
    "ufc", "f1", "nascar", "sanrio", "hello kitty", "stussy", "mclaren",
    "deftones", "cleetus mcfarland", "the neighbourhood", "bring me the horizon",
    "khan asadi", "lyrebird", "anthropologie", "carson hocevar", "rihanna",
    "morgan wallen", "valorant", "kentucky derby", "victoria beckham",
    "kimi antonelli", "no doubt", "bad omens", "good mythical morning",
    "riley green", "ella langley", "candace owens", "g59", "grey59",
    "greyfivenine", "of the trees"
]

EXCLUDED_KEYWORDS = [
    "meaning", "definition", "how to", "why", "iron", "near me", "template",
    "mockup", "tee times", "tee time", "tee off", "graphic tee", "essential tee",
    "vintage tee", "oversized tee", "plain shirt", "blank shirt", "là gì"
]

def get_pytrends_with_retry():
    return TrendReq(hl='en-US', tz=360)

def fetch_rising_queries(pytrends, kw):
    retries = 3
    delay = 10
    for i in range(retries):
        try:
            pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='', gprop='')
            related_queries = pytrends.related_queries()
            if kw in related_queries:
                return related_queries[kw]['rising']
            return None
        except Exception as e:
            print(f"Error fetching {kw} (Attempt {i+1}/{retries}): {e}")
            if "429" in str(e):
                time.sleep(delay * (i + 1) * 5)
            else:
                time.sleep(delay)
    return None

def is_ip_infringing(query):
    query_lower = query.lower()
    for brand in IP_BLACKLIST:
        if brand in query_lower:
            return True
    return False

def is_valid_opportunity(query):
    query_lower = query.lower()

    # Check if it contains any apparel term
    has_apparel = any(term in query_lower for term in APPAREL_TERMS)
    if not has_apparel:
        return False

    # Long tail check (at least 2 words)
    if len(query.split()) < 2:
        return False

    # Exclude non-commercial/irrelevant terms
    if any(ex in query_lower for ex in EXCLUDED_KEYWORDS):
        return False

    return True

def generate_idea(query):
    query_lower = query.lower()
    clean_query = query
    # Remove apparel terms to get the core concept
    for term in sorted(APPAREL_TERMS, key=len, reverse=True):
        if term in query_lower:
            clean_query = clean_query.replace(term, "").replace(term.capitalize(), "").strip()

    clean_query = " ".join(clean_query.split()) # Clean up multiple spaces

    if not clean_query:
        return "Rising interest in generic apparel. Focus on quality and niche colorways."

    return f"Design centered around '{clean_query}'. Internet is seeing a spike in interest for this niche. Could work well as a minimalist graphic or a bold typography design."

def main():
    pytrends = get_pytrends_with_retry()
    all_findings = []
    seen_keywords = set()

    for kw in KEYWORDS:
        print(f"Checking keyword: {kw}")
        rising = fetch_rising_queries(pytrends, kw)
        if rising is not None:
            for index, row in rising.iterrows():
                query = row['query']
                score = row['value']

                if query in seen_keywords:
                    continue

                if is_valid_opportunity(query):
                    infringing = is_ip_infringing(query)
                    idea = generate_idea(query)
                    all_findings.append({
                        'keyword': query,
                        'score': score,
                        'idea': idea,
                        'infringing': infringing
                    })
                    seen_keywords.add(query)

        time.sleep(5)

    if not all_findings:
        print("No new trends found today.")
        return

    # Separate into normal and IP infringing
    normal_opps = [f for f in all_findings if not f['infringing']]
    ip_opps = [f for f in all_findings if f['infringing']]

    # Sort by score descending (treating 'Breakout' as 9999)
    def sort_key(x):
        val = x['score']
        if isinstance(val, str) and val == 'Breakout':
            return 9999
        try:
            return int(val)
        except:
            return 0

    normal_opps.sort(key=sort_key, reverse=True)
    ip_opps.sort(key=sort_key, reverse=True)

    today = datetime.date.today().strftime("%Y-%m-%d")

    new_content = f"## {today}\n\n"

    if normal_opps:
        new_content += "### General Merch Opportunities\n\n"
        new_content += "| keyword | score | Why/Idea |\n"
        new_content += "| :--- | :--- | :--- |\n"
        for f in normal_opps:
            new_content += f"| {f['keyword']} | {f['score']} | {f['idea']} |\n"
        new_content += "\n"

    if ip_opps:
        new_content += "### Potential IP Infringing Opportunities\n\n"
        new_content += "| keyword | score | Why/Idea |\n"
        new_content += "| :--- | :--- | :--- |\n"
        for f in ip_opps:
            new_content += f"| {f['keyword']} | {f['score']} | {f['idea']} |\n"
        new_content += "\n"

    # Prepend to file
    existing_content = ""
    if os.path.exists(TRENDS_FILE):
        with open(TRENDS_FILE, "r") as f:
            existing_content = f.read()
            if f"## {today}" in existing_content:
                print(f"Trends for {today} already exist in {TRENDS_FILE}. Skipping append.")
                return

    header = "# Google Trends Merch Opportunities\n\n"
    with open(TRENDS_FILE, "w") as f:
        if existing_content.startswith("# Google Trends Merch Opportunities"):
            content_after_header = existing_content[len(header):]
            f.write(header + new_content + content_after_header)
        else:
            f.write(header + new_content + existing_content)

    print(f"Successfully updated {TRENDS_FILE} with {len(all_findings)} findings.")

if __name__ == "__main__":
    main()
