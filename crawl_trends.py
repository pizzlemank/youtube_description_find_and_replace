import pandas as pd
from pytrends.request import TrendReq
import datetime
import os
import re
import time

def get_trends():
    # Use a custom retry mechanism because the built-in one in pytrends
    # sometimes has issues with newer urllib3 versions (method_whitelist error)
    pytrends = TrendReq(hl='en-US', tz=360)

    # Keywords to seed the search
    keywords = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]

    all_rising = []

    for kw in keywords:
        print(f"Fetching trends for {kw}...")
        try:
            # Re-initialize to refresh session if needed
            pytrends = TrendReq(hl='en-US', tz=360)
            pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='', gprop='')
            related_queries = pytrends.related_queries()

            if kw in related_queries and related_queries[kw]['rising'] is not None:
                rising = related_queries[kw]['rising']
                all_rising.append(rising)

            # Sleep to avoid rate limiting
            time.sleep(5)
        except Exception as e:
            print(f"Error fetching {kw}: {e}")
            if "429" in str(e):
                print("Rate limit hit, sleeping for 30s...")
                time.sleep(30)

    if not all_rising:
        return pd.DataFrame()

    df = pd.concat(all_rising).drop_duplicates(subset=['query'])
    return df

def is_ip_infringing(query):
    # Expanded list of IP infringing terms
    ip_blacklist = [
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
    query_lower = query.lower()
    for brand in ip_blacklist:
        # Use word boundaries to avoid false positives (e.g., 'nba' in 'sunbathing')
        if re.search(rf'\b{re.escape(brand)}\b', query_lower):
            return True
    return False

def generate_idea(query):
    # Basic idea generation logic
    q = query.lower()

    # Priority for longer terms to avoid partial replacement (e.g. 'tank top' before 'top')
    apparel_regex = r'\b(tshirt|tshirts|t-shirt|t-shirts|shirt|shirts|tank top|tanktop|tee|merch)\b'

    # Remove the apparel word to get the "topic"
    topic = re.sub(apparel_regex, '', q).strip()
    topic = re.sub(r'\s+', ' ', topic) # Clean extra spaces

    if not topic:
        return "General apparel design related to this trending keyword."

    return f"Design idea: '{topic}' themed graphic. The internet is searching for this specifically on apparel. Consider a unique layout or font that stands out from standard merch."

def update_trends_md(df):
    if df.empty:
        print("No new trends found.")
        return

    today = datetime.date.today().strftime("%Y-%m-%d")

    # Read existing content
    if os.path.exists("trends.md"):
        with open("trends.md", "r", encoding="utf-8") as f:
            existing_content = f.read()
    else:
        existing_content = "# Google Trends Merch Opportunities\n\n"

    # Check if we already have entries for today to avoid duplicates
    if f"## {today}" in existing_content:
        print(f"Trends for {today} already exist in trends.md. Skipping update.")
        return

    general_merch = []
    ip_infringing = []

    # Pre-process for sorting: convert 'Breakout' to a high number
    def get_score(val):
        if isinstance(val, str) and val.lower() == 'breakout':
            return 9999
        try:
            return int(val)
        except:
            return 0

    df['numeric_score'] = df['value'].apply(get_score)
    df = df.sort_values(by='numeric_score', ascending=False)

    apparel_terms = ["shirt", "tshirt", "t-shirt", "tank top", "tanktop", "tee", "merch"]
    # Terms to exclude
    exclude_terms = [
        "meaning", "definition", "how to", "why", "iron", "near me", "template", "mockup",
        "tee times", "tee time", "tee off", "graphic tee", "essential tee", "vintage tee",
        "oversized tee", "plain shirt", "blank shirt", "kaffee", "rezepte", "bh für", "bra for",
        "tutorial", "bra", "t-shirt bra", "là gì"
    ]

    seen_queries = set()

    for _, row in df.iterrows():
        query = row['query']
        score = row['value']

        if query in seen_queries:
            continue
        seen_queries.add(query)

        query_lower = query.lower()

        # Check if it's long tail (at least 2 words)
        if len(query.split()) < 2:
            continue

        # Check if it contains any apparel term
        if not any(term in query_lower for term in apparel_terms):
            continue

        # Check exclusion list
        if any(ex in query_lower for ex in exclude_terms):
            continue

        # Avoid very generic ones
        if query_lower.strip() in ["t shirt", "t-shirts", "tees"]:
            continue

        idea = generate_idea(query)
        line = f"| {query} | {score} | {idea} |"

        if is_ip_infringing(query):
            ip_infringing.append(line)
        else:
            general_merch.append(line)

    if not general_merch and not ip_infringing:
        print("No qualified trends after filtering.")
        return

    new_content = f"## {today}\n\n"

    if general_merch:
        new_content += "### General Merch Opportunities\n"
        new_content += "| keyword | score | Why/Idea |\n"
        new_content += "| :--- | :--- | :--- |\n"
        new_content += "\n".join(general_merch) + "\n\n"

    if ip_infringing:
        new_content += "### Potential IP Infringing Opportunities\n"
        new_content += "| keyword | score | Why/Idea |\n"
        new_content += "| :--- | :--- | :--- |\n"
        new_content += "\n".join(ip_infringing) + "\n\n"

    # Insert new content after the main header
    header = "# Google Trends Merch Opportunities\n\n"
    if existing_content.startswith(header):
        updated_content = header + new_content + existing_content[len(header):]
    else:
        updated_content = header + new_content + existing_content

    with open("trends.md", "w", encoding="utf-8") as f:
        f.write(updated_content)
    print("trends.md updated.")

if __name__ == "__main__":
    df = get_trends()
    update_trends_md(df)
