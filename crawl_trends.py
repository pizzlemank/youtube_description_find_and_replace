import pandas as pd
from pytrends.request import TrendReq
import time
from datetime import datetime
import os
import re

# Configuration
KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]
TIMEFRAME = 'now 7-d'  # Last 7 days
GEOGRAPHICAL_AREA = '' # Worldwide
BRAND_BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "taylor swift", "bts",
    "michael jackson", "nba", "wnba", "nfl", "mlb", "nhl", "nintendo", "pokemon",
    "harry potter", "nasa", "hellstar", "ysl", "gucci", "prada", "louis vuitton",
    "koningsdag", "oranje", "higgins", "wwe", "kanye", "drake", "notre dame",
    "ariana grande", "george strait", "olivia dean", "conan gray", "man utd",
    "lidl", "m&s", "mnet", "amc", "murder drones", "luke combs", "ohio state",
    "ufc", "f1", "nascar", "sanrio", "hello kitty", "stussy", "mclaren", "deftones",
    "cleetus mcfarland", "the neighbourhood", "bring me the horizon", "khan asadi",
    "lyrebird", "anthropologie", "carson hocevar", "rihanna", "morgan wallen",
    "valorant", "kentucky derby", "victoria beckham", "kimi antonelli", "no doubt",
    "bad omens", "good mythical morning", "riley green", "ella langley", "candace owens",
    "g59", "grey59", "greyfivenine", "of the trees", "harry styles", "gracie abrams",
    "daniel caesar", "jul", "rcb", "pga championship", "edc", "suzan en freek",
    "kaulitz hills", "qsmp", "ovo"
]

EXCLUDED_TERMS = [
    "meaning", "definition", "how to", "why", "iron", "near me", "template",
    "mockup", "tee times", "tee time", "tee off", "graphic tee", "essential tee",
    "vintage tee", "oversized tee", "plain shirt", "blank shirt", "kaffee",
    "rezepte", "bh für", "bra for", "tutorial", "là gì"
]

def is_ip_infringing(keyword):
    keyword_lower = keyword.lower()
    for brand in BRAND_BLACKLIST:
        if brand in keyword_lower:
            return True
    return False

def generate_design_idea(keyword):
    # Simple logic to generate ideas based on the keyword
    clean_keyword = re.sub(r'\b(tshirt|t-shirt|shirt|tank top|tanktop|tee|merch)\b', '', keyword, flags=re.IGNORECASE).strip()
    clean_keyword = re.sub(r'\s+', ' ', clean_keyword)

    if not clean_keyword:
        return "Generic apparel design."

    return f"Design featuring '{clean_keyword}'. Focus on trending aesthetics related to the topic."

def fetch_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    all_results = []

    for kw in KEYWORDS:
        print(f"Fetching related queries for: {kw}")
        related_queries = {}
        retries = 3
        while retries > 0:
            try:
                pytrends.build_payload([kw], cat=0, timeframe=TIMEFRAME, geo=GEOGRAPHICAL_AREA, gprop='')
                related_queries = pytrends.related_queries()
                break
            except Exception as e:
                if "429" in str(e):
                    print(f"Rate limited for {kw}. Retrying in 60 seconds...")
                    time.sleep(60)
                    retries -= 1
                else:
                    print(f"Error fetching {kw}: {e}")
                    retries = 0
                    related_queries = {}

        try:
            if kw in related_queries and related_queries[kw]['rising'] is not None:
                rising = related_queries[kw]['rising']
                for index, row in rising.iterrows():
                    query = row['query']
                    value = row['value']

                    # Filtering: Long tail (2+ words)
                    if len(query.split()) < 2:
                        continue

                    # Filtering: Excluded terms
                    if any(term in query.lower() for term in EXCLUDED_TERMS):
                        continue

                    all_results.append({
                        'keyword': query,
                        'score': value,
                        'is_ip': is_ip_infringing(query)
                    })

            time.sleep(5) # Avoid rate limiting
        except Exception as e:
            print(f"Error fetching {kw}: {e}")

    return all_results

def format_results(results):
    if not results:
        return ""

    # Sort by score descending
    # 'Breakout' is represented by high number in pytrends sometimes, or just string.
    # Let's handle 'Breakout' as 9999
    for r in results:
        if isinstance(r['score'], str) and r['score'].lower() == 'breakout':
            r['score_val'] = 9999
        else:
            try:
                r['score_val'] = int(r['score'])
            except:
                r['score_val'] = 0

    results.sort(key=lambda x: x['score_val'], reverse=True)

    general_merch = [r for r in results if not r['is_ip']]
    ip_infringing = [r for r in results if r['is_ip']]

    today = datetime.now().strftime("%Y-%m-%d")
    output = f"## {today}\n\n"

    output += "### General Merch Opportunities\n\n"
    output += "| keyword | score | Why/Idea |\n"
    output += "| :--- | :--- | :--- |\n"
    for r in general_merch:
        idea = generate_design_idea(r['keyword'])
        output += f"| {r['keyword']} | {r['score']} | {idea} |\n"

    if ip_infringing:
        output += "\n### Potential IP Infringing Opportunities\n\n"
        output += "| keyword | score | Why/Idea |\n"
        output += "| :--- | :--- | :--- |\n"
        for r in ip_infringing:
            idea = generate_design_idea(r['keyword'])
            output += f"| {r['keyword']} | {r['score']} | POTENTIAL IP INFRINGEMENT. {idea} |\n"

    return output

def update_trends_file(new_content):
    if not new_content:
        print("No new trends found.")
        return

    filename = "trends.md"

    if os.path.exists(filename):
        with open(filename, 'r') as f:
            existing_content = f.read()
    else:
        existing_content = "# Google Trends Merch Opportunities\n\n"

    # Check if we already added today's trends
    today_header = f"## {datetime.now().strftime('%Y-%m-%d')}"
    if today_header in existing_content:
        print("Today's trends already added. Skipping to avoid duplicates.")
        return

    # Prepend new content after the title
    if "# Google Trends Merch Opportunities" in existing_content:
        title, rest = existing_content.split("\n\n", 1)
        full_content = f"{title}\n\n{new_content}\n\n{rest}"
    else:
        full_content = f"# Google Trends Merch Opportunities\n\n{new_content}\n\n{existing_content}"

    with open(filename, 'w') as f:
        f.write(full_content)
    print(f"Successfully updated {filename}")

if __name__ == "__main__":
    results = fetch_trends()
    # Deduplicate
    unique_results = []
    seen = set()
    for r in results:
        if r['keyword'].lower() not in seen:
            unique_results.append(r)
            seen.add(r['keyword'].lower())

    markdown_output = format_results(unique_results)
    update_trends_file(markdown_output)
