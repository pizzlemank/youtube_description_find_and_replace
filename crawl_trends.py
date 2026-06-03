import pandas as pd
from pytrends.request import TrendReq
import time
from datetime import date
import os
import re

# Configuration
KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]
TIMEFRAME = 'now 7-d'  # Last 7 days to get fresh rising trends
IP_BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "taylor swift", "bts", "mickey",
    "nba", "nfl", "mlb", "nhl", "pokemon", "harry potter", "nintendo", "playstation",
    "xbox", "gucci", "prada", "louis vuitton", "supreme", "stussy", "drake", "kanye",
    "travis scott", "billie eilish", "barbie", "oppenheimer", "netflix", "hulu",
    "amazon", "google", "apple", "microsoft", "sony", "warner bros", "universal",
    "paramount", "mcdonalds", "starbucks", "coca cola", "pepsi", "nasa", "hellstar",
    "trapstar", "corteiz", "sp5der", "minus two", "syna world", "amiri", "ysl",
    "balenciaga", "fendi", "versace", "hermes", "cartier", "rolex", "omega",
    "patek philippe", "audemars piguet", "hublot", "iwc", "tag heuer", "breitling",
    "panerai", "tudor", "cartier", "tiffany", "boucheron", "van cleef", "bulgari",
    "chopard", "piaget", "graff", "harry winston", "mikimoto", "tasaki", "arsenal",
    "real madrid", "liverpool", "man city", "chelsea", "bayern", "barcelona",
    "knicks", "lakers", "celtics", "warriors", "bulls", "yankees", "dodgers",
    "red sox", "cubs", "mets", "braves", "astros", "phillies", "rangers", "mariners",
    "asap rocky", "megan moroney", "sean john", "morgan wallen", "spurs", "rcb",
    "snipes", "asos", "pattie gonia", "psg", "wingstop"
]

EXCLUDE_TERMS = [
    "meaning", "definition", "how to", "why", "iron", "near me", "template", "mockup",
    "tee times", "tee time", "tee off", "graphic tee", "essential tee", "vintage tee",
    "oversized tee", "plain shirt", "blank shirt", "kaffee", "rezepte", "bh für", "bra for",
    "tutorial", "là gì"
]

def generate_idea(keyword):
    """Generates a simple design idea or rationale based on the keyword."""
    # Clean the keyword to extract core concept
    # Sort KEYWORDS by length descending to replace "tank top" before "top"
    sorted_keywords = sorted(KEYWORDS, key=len, reverse=True)
    core = keyword.lower()
    for s in sorted_keywords:
        # Also handle plurals
        core = core.replace(s + "s", "").replace(s, "").strip()

    # Clean up multiple spaces
    core = re.sub(' +', ' ', core)

    if not core:
        return "Popular demand for this basic apparel item; consider unique colorways or premium materials."

    # Simple templates for ideas that cover "Why/Idea/What market is doing"
    templates = [
        f"Rising interest in '{core}'; the market is leaning towards vintage/distressed looks.",
        f"Minimalist typography design featuring '{core}' is trending on social media.",
        f"Combine '{core}' with bold, Y2K-style graphics to capture the current youth market.",
        f"Niche opportunity for '{core}' enthusiasts; try a 'clean girl' or 'quiet luxury' aesthetic.",
        f"High search volume for '{core}'; current bestsellers use 'ugly/ironic' design styles.",
        f"Create a 'souvenir' style design for '{core}' which is gaining viral traction.",
        f"Targeting '{core}'; internet shoppers are looking for high-quality, heavyweight embroidery-look prints."
    ]
    # Return one based on hash to keep it consistent but somewhat varied
    return templates[hash(keyword) % len(templates)]

def crawl():
    print("Starting Google Trends crawl...")
    # Use higher timeout and more retries conceptually, though TrendReq is simple
    pytrends = TrendReq(hl='en-US', tz=360)

    all_rising = []

    for kw in KEYWORDS:
        print(f"Fetching related queries for: {kw}")
        max_retries = 3
        for attempt in range(max_retries):
            try:
                pytrends.build_payload([kw], timeframe=TIMEFRAME)
                related = pytrends.related_queries()

                if kw in related and related[kw]['rising'] is not None:
                    rising_df = related[kw]['rising']
                    # Add source keyword for context
                    rising_df['source'] = kw
                    all_rising.append(rising_df)

                # Wait to avoid rate limits
                time.sleep(5)
                break # Success
            except Exception as e:
                print(f"Error fetching {kw} (Attempt {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(60) # Longer wait on error
                else:
                    print(f"Failed to fetch {kw} after {max_retries} attempts.")

    if not all_rising:
        print("No rising trends found.")
        return

    df = pd.concat(all_rising).drop_duplicates(subset=['query'])

    # Filter for long tail (2+ words)
    df = df[df['query'].str.split().str.len() >= 2]

    # Ensure it contains one of our target apparel keywords to reduce noise
    apparel_pattern = '|'.join(KEYWORDS)
    df = df[df['query'].str.contains(apparel_pattern, case=False, na=False)]

    # Filter out exclude terms
    exclude_pattern = '|'.join(EXCLUDE_TERMS)
    df = df[~df['query'].str.contains(exclude_pattern, case=False, na=False)]

    # Handle "Breakout" and ensure numeric scores for sorting
    df['value'] = df['value'].apply(lambda x: 9999 if x == 'Breakout' else x)
    df['value'] = pd.to_numeric(df['value'], errors='coerce').fillna(0).astype(int)

    # Deduplicate again just in case across different seeds
    df = df.sort_values('value', ascending=False)

    general_merch = []
    ip_infringing = []

    processed_queries = set()

    for _, row in df.iterrows():
        query = row['query']
        if query in processed_queries:
            continue
        processed_queries.add(query)

        score = row['value']

        is_ip = any(black in query.lower() for black in IP_BLACKLIST)

        entry = {
            'keyword': query,
            'score': "Breakout" if score == 9999 else score,
            'idea': generate_idea(query)
        }

        if is_ip:
            ip_infringing.append(entry)
        else:
            general_merch.append(entry)

    update_markdown(general_merch, ip_infringing)

def update_markdown(general, ip):
    today = date.today().strftime("%Y-%m-%d")

    # Check if this date already exists to avoid duplicates
    if os.path.exists("trends.md"):
        with open("trends.md", "r", encoding="utf-8") as f:
            existing_content = f.read()
            if f"## {today}" in existing_content:
                print(f"Trends for {today} already exist in trends.md. Skipping update.")
                return

    content = f"## {today}\n\n"

    content += "### General Merch Opportunities\n\n"
    if general:
        content += "| keyword | score | Why/Idea |\n"
        content += "| :--- | :--- | :--- |\n"
        for item in general:
            content += f"| {item['keyword']} | {item['score']} | {item['idea']} |\n"
    else:
        content += "No new general opportunities found today.\n"

    content += "\n### Potential IP Infringing Opportunities\n\n"
    if ip:
        content += "| keyword | score | Why/Idea |\n"
        content += "| :--- | :--- | :--- |\n"
        for item in ip:
            content += f"| {item['keyword']} | {item['score']} | {item['idea']} (⚠️ Potential IP Infringement) |\n"
    else:
        content += "No potential IP infringing opportunities found today.\n"

    content += "\n---\n\n"

    # Read existing content
    if os.path.exists("trends.md"):
        with open("trends.md", "r", encoding="utf-8") as f:
            lines = f.readlines()
    else:
        lines = ["# POD Merch Trends Tracker\n\n"]

    # Find where to insert (after the title and intro)
    insert_pos = 0
    for i, line in enumerate(lines):
        if line.startswith("# "):
            insert_pos = i + 1
            # Keep looking for the first blank line after the title or intro
            continue
        if insert_pos > 0 and line.strip() == "":
            insert_pos = i + 1
            break

    # Insert new content
    new_lines = lines[:insert_pos] + [content] + lines[insert_pos:]

    with open("trends.md", "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"Successfully updated trends.md with data for {today}")

if __name__ == "__main__":
    crawl()
