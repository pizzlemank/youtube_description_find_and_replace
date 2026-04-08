import pandas as pd
from pytrends.request import TrendReq
import datetime
import os
import time
import re

# Configuration
KEYWORDS = ["tshirt", "shirt", "tank top", "merch"]
APPAREL_TERMS = ["shirt", "tshirt", "t-shirt", "tanktop", "tank top", "merch", "tee"]
EXCLUDE_TERMS = ["how to", "meaning", "definition", "why", "iron", "near me", "template", "mockup"]

IP_BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "gucci", "prada",
    "mickey", "minnie", "pokemon", "nintendo", "sony", "playstation",
    "xbox", "apple", "iphone", "google", "facebook", "instagram", "netflix",
    "amazon", "tesla", "spacex", "nasa", "fbi", "cia", "unicef", "who",
    "walmart", "target", "costco", "starbucks", "mcdonalds", "coca cola",
    "pepsi", "red bull", "monster energy", "budweiser", "heineken",
    "supreme", "off-white", "yeezy", "jordan", "vans", "converse",
    "harry potter", "game of thrones", "batman", "superman", "spiderman",
    "avengers", "iron man", "captain america", "thor", "hulk", "black widow",
    "black panther", "doctor strange", "guardians of the galaxy", "eternals",
    "shang-chi", "ms marvel", "she-hulk", "moon knight", "loki", "falcon",
    "winter soldier", "scarlet witch", "vision", "hawkeye", "daredevil",
    "punisher", "ghost rider", "blade", "x-men", "wolverine", "deadpool",
    "fantastic four", "silver surfer", "venom", "carnage", "morbius",
    "michael jackson", "kanye west", "taylor swift", "beyonce", "drake",
    "justin bieber", "rihanna", "eminem", "jay-z", "lady gaga", "katy perry",
    "ariana grande", "selena gomez", "billie eilish", "ed sheeran", "adele",
    "bruno mars", "the weeknd", "post malone", "kendrick lamar", "j cole",
    "lil wayne", "nicki minaj", "cardi b", "megan thee stallion", "doja cat",
    "national geographic", "olivia rodrigo", "taylor swift", "eras tour"
]

# Utility functions
def is_ip_infringing(keyword):
    keyword_lower = keyword.lower()
    for brand in IP_BLACKLIST:
        if re.search(rf"\b{brand}\b", keyword_lower):
            return True
    return False

def get_opportunity_idea(keyword):
    keyword_lower = keyword.lower()
    if "autism" in keyword_lower:
        return "Awareness design, maybe with puzzle pieces or infinity symbol. High emotional value."
    if "wolf" in keyword_lower:
        return "Animal graphic, vintage or minimalist style. Popular niche."
    if "love" in keyword_lower:
        return "Expressive typography design. Good for gifts."
    if "funny" in keyword_lower:
        return "Humorous text-based design. High shareability."
    return f"Trending long-tail search. Design inspired by '{keyword}' with unique artistic twist."

def fetch_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    all_data = []

    for kw in KEYWORDS:
        print(f"Fetching trends for: {kw}")
        try:
            pytrends.build_payload([kw], timeframe='now 7-d')
            related = pytrends.related_queries()
            rising = related[kw]['rising']

            if rising is not None and not rising.empty:
                for _, row in rising.iterrows():
                    query = row['query']
                    score = row['value']

                    # Filter for long-tail (contains apparel term + at least one other word)
                    # And exclude non-merch intent
                    query_lower = query.lower()
                    if any(term in query_lower for term in APPAREL_TERMS) and \
                       len(query.split()) > 1 and \
                       not any(exc in query_lower for exc in EXCLUDE_TERMS):
                        all_data.append({
                            'keyword': query,
                            'score': score,
                            'is_ip': is_ip_infringing(query)
                        })
            time.sleep(2) # Avoid rate limiting
        except Exception as e:
            print(f"Error fetching {kw}: {e}")

    return all_data

def format_markdown(data):
    today = datetime.date.today().strftime("%Y-%m-%d")
    header = f"## {today}\n\n"

    general_table = "### General Merch Opportunities\n| Keyword | Score | Why/Idea |\n|---|---|---|\n"
    ip_table = "### Potential IP Infringing Opportunities\n| Keyword | Score | Why/Idea |\n|---|---|---|\n"

    gen_count = 0
    ip_count = 0

    for item in data:
        idea = get_opportunity_idea(item['keyword'])
        row = f"| {item['keyword']} | {item['score']} | {idea} |\n"
        if item['is_ip']:
            ip_table += row
            ip_count += 1
        else:
            general_table += row
            gen_count += 1

    content = header
    if gen_count > 0:
        content += general_table + "\n"
    if ip_count > 0:
        content += ip_table + "\n"

    return content

def main():
    print("Starting crawl...")
    trends_data = fetch_trends()
    if not trends_data:
        print("No new trends found.")
        return

    # Deduplicate
    unique_trends = {t['keyword']: t for t in trends_data}.values()

    new_content = format_markdown(unique_trends)

    filename = "trends.md"
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            old_content = f.read()

        # Check if today's date already exists to avoid duplicates if run multiple times
        today = datetime.date.today().strftime("%Y-%m-%d")
        if f"## {today}" in old_content:
             print(f"Trends for {today} already exist in {filename}. Skipping append.")
             return

        with open(filename, 'w') as f:
            f.write(new_content + "\n---\n\n" + old_content)
    else:
        with open(filename, 'w') as f:
            f.write(new_content)

    print(f"Successfully updated {filename}")

if __name__ == "__main__":
    main()
