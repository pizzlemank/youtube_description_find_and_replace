import pandas as pd
from pytrends.request import TrendReq
import time
from datetime import datetime
import os

# Configuration
KEYWORDS = ["tshirt", "shirt", "tank top", "merch"]
BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "bieber", "beiber", "taylor swift",
    "michael jackson", "one piece", "popeyes", "coachella", "anime", "netflix",
    "mickey", "trump", "biden", "nba", "nfl", "mlb", "nhl", "pokemon", "nintendo",
    "sony", "playstation", "xbox", "nasa", "hellstar", "karol g", "bruno mars", "sabrina carpenter"
]
NON_COMMERCIAL = ["meaning", "definition", "how to", "why", "iron", "near me", "template", "mockup"]

def get_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    all_rising = []

    for kw in KEYWORDS:
        print(f"Fetching trends for: {kw}")
        try:
            pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='', gprop='')
            related = pytrends.related_queries()
            if kw in related and related[kw]['rising'] is not None:
                df = related[kw]['rising']
                df['seed'] = kw
                all_rising.append(df)
            time.sleep(2)  # Avoid rate limiting
        except Exception as e:
            print(f"Error fetching {kw}: {e}")
            if "429" in str(e):
                print("Rate limit hit. Sleeping for 10 seconds...")
                time.sleep(10)
                # Retry once
                try:
                    pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='', gprop='')
                    related = pytrends.related_queries()
                    if kw in related and related[kw]['rising'] is not None:
                        df = related[kw]['rising']
                        df['seed'] = kw
                        all_rising.append(df)
                except:
                    pass

    if not all_rising:
        return pd.DataFrame()

    return pd.concat(all_rising).drop_duplicates(subset='query')

def filter_and_categorize(df):
    if df.empty:
        return [], []

    safe_opportunities = []
    ip_infringing = []

    for _, row in df.iterrows():
        query = row['query'].lower()
        value = row['value']

        # 1. Long tail check (at least 2 words)
        words = query.split()
        if len(words) < 2:
            continue

        # 2. Apparel check (must contain apparel related word)
        apparel_terms = ['shirt', 'tshirt', 'tank top', 'tanktop', 'tee', 'hoodie', 'merch']
        if not any(term in query for term in apparel_terms):
            continue

        # 3. Non-commercial filter
        if any(term in query for term in NON_COMMERCIAL):
            continue

        # Generate "Why/Idea"
        topic = query
        # Replace longer terms first to avoid partial replacement (e.g., 'tshirt' before 'shirt')
        for term in sorted(apparel_terms, key=len, reverse=True):
            topic = topic.replace(term, "").strip()

        # Clean up multiple spaces
        topic = " ".join(topic.split())

        idea = f"Rising interest in {topic}. Design should focus on unique typography or illustrative elements related to '{topic}'."

        # 4. IP Check
        is_ip = any(brand in query for brand in BLACKLIST)

        item = {
            "keyword": row['query'],
            "score": value,
            "idea": idea
        }

        if is_ip:
            ip_infringing.append(item)
        else:
            safe_opportunities.append(item)

    # Sort by score (descending). 'Breakout' is typically represented as a string or high value.
    def sort_key(x):
        val = x['score']
        try:
            return int(val)
        except (ValueError, TypeError):
            # If it's "Breakout" or something else, treat as highest
            return 999999

    safe_opportunities.sort(key=sort_key, reverse=True)
    ip_infringing.sort(key=sort_key, reverse=True)

    return safe_opportunities, ip_infringing

def format_markdown(safe, ip):
    date_str = datetime.now().strftime("%Y-%m-%d")
    md = f"## {date_str}\n\n"

    md += "### General Merch Opportunities\n"
    if not safe:
        md += "No trends found for today.\n"
    else:
        md += "| Keyword | Score | Why/Idea |\n"
        md += "| :--- | :--- | :--- |\n"
        for item in safe:
            md += f"| {item['keyword']} | {item['score']} | {item['idea']} |\n"

    md += "\n### Potential IP Infringing Opportunities\n"
    md += "> **Warning:** These keywords may contain trademarked terms. Use caution.\n\n"
    if not ip:
        md += "No IP infringing trends flagged today.\n"
    else:
        md += "| Keyword | Score | Why/Idea |\n"
        md += "| :--- | :--- | :--- |\n"
        for item in ip:
            md += f"| {item['keyword']} | {item['score']} | {item['idea']} |\n"

    md += "\n---\n"
    return md

def update_trends_file(new_content):
    filename = "trends.md"
    existing_content = ""
    if os.path.exists(filename):
        with open(filename, "r") as f:
            existing_content = f.read()

    # Check if we already added today's trends to avoid duplicates if run multiple times
    date_header = f"## {datetime.now().strftime('%Y-%m-%d')}"
    if date_header in existing_content:
        print("Today's trends already exist in trends.md. Skipping append to avoid duplication.")
        return

    with open(filename, "w") as f:
        f.write(new_content + "\n" + existing_content)

def main():
    print("Starting crawl...")
    df = get_trends()
    if df.empty:
        print("No trends found.")
        return

    safe, ip = filter_and_categorize(df)
    md_output = format_markdown(safe, ip)
    update_trends_file(md_output)
    print("Done! trends.md updated.")

if __name__ == "__main__":
    main()
