import os
import time
from datetime import datetime
import pandas as pd
from pytrends.request import TrendReq
import numpy as np

def fetch_trends():
    # Use a retry mechanism as pytrends can be flaky with 429s
    pytrends = TrendReq(hl='en-US', tz=360)
    seed_keywords = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]

    all_rising = []

    for kw in seed_keywords:
        print(f"Fetching trends for: {kw}")
        for attempt in range(3):
            try:
                pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='', gprop='')
                related = pytrends.related_queries()
                rising = related.get(kw, {}).get('rising')
                if rising is not None:
                    all_rising.append(rising)
                time.sleep(2) # Avoid rate limiting
                break
            except Exception as e:
                print(f"Error fetching {kw} (attempt {attempt+1}): {e}")
                time.sleep(5)

    if not all_rising:
        return pd.DataFrame()

    df = pd.concat(all_rising).drop_duplicates(subset='query')
    return df

def is_ip_infringing(query):
    blacklist = [
        "disney", "marvel", "star wars", "nike", "adidas", "taylor swift", "bts",
        "michael jackson", "nba", "nfl", "mlb", "nhl", "nintendo", "pokemon",
        "harry potter", "nasa", "hellstar", "ysl", "gucci", "prada", "louis vuitton",
        "koningsdag", "oranje", "higgins", "wwe", "kanye", "drake", "notre dame",
        "ariana grande", "george strait", "olivia dean", "conan gray", "man utd",
        "lidl", "m&s", "mnet", "amc", "murder drones", "luke combs", "ohio state",
        "ufc", "f1", "nascar", "sanrio", "hello kitty", "stussy", "mclaren",
        "deftones", "cleetus mcfarland", "the neighbourhood", "bring me the horizon",
        "khan asadi", "lyrebird", "anthropologie", "carson hocevar"
    ]
    query_lower = query.lower()
    for item in blacklist:
        if item in query_lower:
            return True
    return False

def generate_idea(query):
    # Basic logic: remove the seed keyword and suggest a design
    # Order matters: replace longer strings first
    merch_terms = ["t-shirt", "tshirt", "t shirt", "tank top", "tanktop", "shirt", "tee", "merch"]
    clean_query = query.lower()
    for term in merch_terms:
        clean_query = clean_query.replace(term, "").strip()

    # Remove extra spaces
    clean_query = " ".join(clean_query.split())

    if not clean_query:
        clean_query = query

    return f"Design featuring '{clean_query.title()}'. This keyword is trending in apparel searches. Consider creating a unique graphic or typography design around this theme."

def process_trends(df):
    merch_terms = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]

    opportunities = []
    ip_infringing = []
    seen_keywords = set()

    for _, row in df.iterrows():
        query = row['query']
        score = row['value']

        if query in seen_keywords:
            continue
        seen_keywords.add(query)

        # Filter for long tail (at least 2 words)
        words = query.split()
        if len(words) < 2:
            continue

        # Must contain a merch term
        if not any(term in query.lower() for term in merch_terms):
            continue

        # Skip generic or non-commercial ones
        skips = [
            "meaning", "definition", "how to", "why", "iron", "near me",
            "template", "mockup", "tee times", "tee time", "tee off",
            "graphic tee", "essential tee", "vintage tee", "oversized tee",
            "plain shirt", "blank shirt"
        ]
        if any(skip in query.lower() for skip in skips):
            continue

        idea = generate_idea(query)

        entry = {
            "keyword": query,
            "score": score,
            "idea": idea
        }

        if is_ip_infringing(query):
            ip_infringing.append(entry)
        else:
            opportunities.append(entry)

    return opportunities, ip_infringing

def get_sort_score(score):
    if isinstance(score, str) and (score == 'Breakout' or score == 'breakout'):
        return 9999
    try:
        return int(score)
    except:
        return 0

def update_trends_md(opportunities, ip_infringing):
    date_str = datetime.now().strftime("%Y-%m-%d")

    if not opportunities and not ip_infringing:
        print("No opportunities to write.")
        return

    new_content = f"## {date_str}\n\n"

    new_content += "### General Merch Opportunities\n"
    new_content += "| Keyword | Score | Why/Idea |\n"
    new_content += "|---------|-------|----------|\n"

    sorted_opps = sorted(opportunities, key=lambda x: get_sort_score(x['score']), reverse=True)
    for opt in sorted_opps:
        new_content += f"| {opt['keyword']} | {opt['score']} | {opt['idea']} |\n"

    new_content += "\n### Potential IP Infringing Opportunities\n"
    new_content += "| Keyword | Score | Why/Idea |\n"
    new_content += "|---------|-------|----------|\n"

    sorted_ip = sorted(ip_infringing, key=lambda x: get_sort_score(x['score']), reverse=True)
    for opt in sorted_ip:
        new_content += f"| {opt['keyword']} | {opt['score']} | {opt['idea']} |\n"

    new_content += "\n---\n\n"

    if os.path.exists("trends.md"):
        with open("trends.md", "r") as f:
            old_content = f.read()
    else:
        old_content = ""

    # Check if we already updated today to avoid duplicates if run multiple times
    if f"## {date_str}" in old_content:
        print(f"Today's ({date_str}) trends already updated in trends.md.")
        return

    with open("trends.md", "w") as f:
        f.write(new_content + old_content)

if __name__ == "__main__":
    df = fetch_trends()
    if not df.empty:
        opportunities, ip_infringing = process_trends(df)
        update_trends_md(opportunities, ip_infringing)
        print("Successfully updated trends.md")
    else:
        print("No trends found.")
