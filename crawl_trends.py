import pandas as pd
from pytrends.request import TrendReq
from datetime import datetime
import os
import time

# Configuration
KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]
IP_BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "taylor swift", "bts",
    "michael jackson", "micheal jackson", "nba", "nfl", "mlb", "nhl", "nintendo",
    "pokemon", "harry potter", "nasa", "hellstar", "ysl", "gucci", "prada",
    "louis vuitton", "koningsdag", "oranje", "higgins", "wwe", "kanye", "drake",
    "notre dame"
]

EXCLUDE_KEYWORDS = [
    "meaning", "definition", "how to", "why", "iron", "near me",
    "template", "mockup", "tee times", "tee time", "tee off",
    "graphic tee", "essential tee", "vintage tee", "oversized tee",
    "plain shirt", "blank shirt"
]

def get_rising_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    all_trends = []

    for kw in KEYWORDS:
        print(f"Fetching trends for: {kw}")
        retries = 3
        while retries > 0:
            try:
                pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='', gprop='')
                related = pytrends.related_queries()

                if kw in related and related[kw]['rising'] is not None:
                    rising = related[kw]['rising']
                    for _, row in rising.iterrows():
                        all_trends.append({
                            'keyword': row['query'],
                            'score': row['value']
                        })
                time.sleep(2) # Avoid rate limiting
                break # Success
            except Exception as e:
                if "429" in str(e):
                    print(f"Rate limited for {kw}, retrying in 10s...")
                    time.sleep(10)
                    retries -= 1
                else:
                    print(f"Error fetching {kw}: {e}")
                    break

    return all_trends

def filter_and_categorize(trends):
    filtered_trends = []
    seen = set()

    for item in trends:
        kw = item['keyword'].lower()

        if kw in seen:
            continue
        seen.add(kw)

        # Long tail check (at least 2 words)
        words = kw.split()
        if len(words) < 2:
            continue

        # Relevance check
        if not any(apparel in kw for apparel in ["shirt", "tshirt", "t-shirt", "tank top", "tanktop", "tee", "merch"]):
            continue

        # Exclusion list
        if any(exclude in kw for exclude in EXCLUDE_KEYWORDS):
            continue

        # IP Check
        is_ip_infringing = any(brand in kw for brand in IP_BLACKLIST)

        # Why/Idea generation
        idea = generate_idea(kw)

        filtered_trends.append({
            'keyword': item['keyword'],
            'score': item['score'],
            'idea': idea,
            'is_ip': is_ip_infringing
        })

    return filtered_trends

def generate_idea(kw):
    kw_lower = kw.lower()
    if "funny" in kw_lower:
        return "Humorous text-based design. High potential for social sharing."
    if "cute" in kw_lower:
        return "Cutesy illustration style. Targets demographic looking for 'aesthetic' apparel."
    if "vintage" in kw_lower or "retro" in kw_lower:
        return "Distressed, vintage aesthetic. Trending look for casual wear."

    # Generic replacement - replace longest terms first to avoid partial replacements
    base_topic = kw_lower
    terms_to_remove = sorted([
        "t-shirt", "tshirt", "t shirt", "tank top", "tanktop", "shirt", "merch", "tee"
    ], key=len, reverse=True)
    for term in terms_to_remove:
        base_topic = base_topic.replace(term, "").strip()

    # Clean up double spaces
    base_topic = " ".join(base_topic.split())

    return f"Design focused on '{base_topic}'. Look for unique illustrations or slogans that resonate with this niche."

def format_as_markdown(trends):
    if not trends:
        return "No new trends found today."

    today = datetime.now().strftime("%Y-%m-%d")

    general_opportunities = [t for t in trends if not t['is_ip']]
    ip_opportunities = [t for t in trends if t['is_ip']]

    output = f"## {today}\n\n"

    output += "### General Merch Opportunities\n"
    if general_opportunities:
        output += "| Keyword | Score | Why/Idea |\n"
        output += "| :--- | :--- | :--- |\n"
        # Sort by score descending (Breakout is usually represented as a large number or string)
        def sort_key(x):
            val = x['score']
            if isinstance(val, (int, float)): return val
            try: return int(val)
            except: return 9999

        general_opportunities.sort(key=sort_key, reverse=True)
        for t in general_opportunities:
            output += f"| {t['keyword']} | {t['score']} | {t['idea']} |\n"
    else:
        output += "None found.\n"

    output += "\n### Potential IP Infringing Opportunities\n"
    if ip_opportunities:
        output += "| Keyword | Score | Why/Idea |\n"
        output += "| :--- | :--- | :--- |\n"
        # Sort by score descending
        ip_opportunities.sort(key=sort_key, reverse=True)
        for t in ip_opportunities:
            output += f"| {t['keyword']} | {t['score']} | {t['idea']} |\n"
    else:
        output += "None found.\n"

    return output

def update_trends_md(new_content):
    file_path = "trends.md"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            old_content = f.read()
    else:
        old_content = ""

    # Check if date already exists to avoid duplicates if run multiple times a day
    today_header = f"## {datetime.now().strftime('%Y-%m-%d')}"
    if today_header in old_content:
        print("Today's trends already updated. Skipping.")
        return

    with open(file_path, "w") as f:
        f.write(new_content + "\n" + old_content)

def main():
    trends = get_rising_trends()
    if not trends:
        print("No trends fetched.")
        return

    filtered = filter_and_categorize(trends)
    markdown_content = format_as_markdown(filtered)
    update_trends_md(markdown_content)
    print("trends.md updated successfully.")

if __name__ == "__main__":
    main()
