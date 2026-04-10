import pandas as pd
from pytrends.request import TrendReq
import datetime
import os
import re
import time

# --- Configuration ---
KEYWORDS = ['tshirt', 'shirt', 'tank top', 'merch']
TIMEFRAME = 'now 7-d'  # Last 7 days to get "rising" trends
GEO = 'US'  # Primarily US market for POD
TRENDS_FILE = 'trends.md'

# Basic blacklist for IP infringement detection
# This is not exhaustive but covers major categories
IP_BLACKLIST = [
    'disney', 'marvel', 'dc comics', 'star wars', 'mickey', 'pokemon', 'nintendo',
    'nike', 'adidas', 'gucci', 'prada', 'louis vuitton', 'chanel',
    'nfl', 'nba', 'mlb', 'nhl', 'fifa', 'olympics',
    'harry potter', 'game of thrones', 'netflix', 'hulu', 'hbo',
    'taylor swift', 'beyonce', 'drake', 'kanye', 'ye', 'bts', 'bruno mars', 'hello kitty',
    'michael jackson', 'morgan wallen', 'meatcanyon', 'meat canyon', 'cdawgva', 'masayoshi takanaka',
    'trump', 'biden', 'obama', 'masters', 'world cup', 'zara', 'lululemon', 'skims', 'nasa'
]

def is_ip_infringing(keyword):
    """Simple check against a blacklist."""
    keyword_lower = keyword.lower()
    for item in IP_BLACKLIST:
        # Use regex to find whole words to avoid false positives (e.g., "nike" in "uniken")
        if re.search(r'\b' + re.escape(item) + r'\b', keyword_lower):
            return True
    return False

def get_opportunity_reason(keyword):
    """
    Generates a 'Why/Idea' message.
    In a real-world scenario, this might use LLM or more complex logic.
    For this script, we'll provide some generic but helpful context.
    """
    keyword_lower = keyword.lower()

    if 'meme' in keyword_lower:
        return "Viral meme trend, high engagement potential for younger audience."
    if any(word in keyword_lower for word in ['funny', 'humor', 'joke']):
        return "Evergreen humor niche, likely a specific joke or pun gaining traction."
    if any(word in keyword_lower for word in ['vintage', 'retro']):
        return "Nostalgia factor, popular aesthetic for apparel."
    if any(word in keyword_lower for word in ['birthday', 'gift']):
        return "Personalized gift niche, consistent demand."

    return "Rising search interest indicates emerging demand. Design idea: Minimalist typography or illustrative graphic based on the keyword."

def fetch_trends():
    pytrends = TrendReq(hl='en-US', tz=360)

    all_rising = []

    for kw in KEYWORDS:
        print(f"Fetching trends for: {kw}")
        try:
            pytrends.build_payload([kw], cat=0, timeframe=TIMEFRAME, geo=GEO, gprop='')
            related_queries = pytrends.related_queries()

            if kw in related_queries and related_queries[kw]['rising'] is not None:
                rising = related_queries[kw]['rising']
                # Filter for long tail: must contain the seed keyword or related apparel terms
                # and have more than just the seed word
                for _, row in rising.iterrows():
                    query = row['query']
                    value = row['value']

                    # Basic long-tail and relevance check
                    # Exclude non-commercial intent keywords
                    exclude_terms = ['how to', 'near me', 'meaning', 'definition', 'why', 'iron', 'template', 'mockup']
                    if len(query.split()) > 1 and not any(term in query.lower() for term in exclude_terms):
                         all_rising.append({'keyword': query, 'score': value})

            # Avoid hitting rate limits
            time.sleep(2)

        except Exception as e:
            print(f"Error fetching {kw}: {e}")
            if "429" in str(e):
                print("Rate limited. Sleeping for 10s...")
                time.sleep(10)

    # Remove duplicates
    unique_trends = {t['keyword']: t for t in all_rising}.values()
    return sorted(unique_trends, key=lambda x: x['score'], reverse=True)

def update_trends_file(trends):
    today = datetime.datetime.now().strftime('%Y-%m-%d')

    general_merch = []
    ip_infringing = []

    for t in trends:
        if is_ip_infringing(t['keyword']):
            ip_infringing.append(t)
        else:
            general_merch.append(t)

    # Format tables
    def format_table(data):
        if not data:
            return "No trends found for this category today.\n"

        table = "| keyword | score | why you think is an opportunity, idea for design, or what the internet shopping is already doing |\n"
        table += "| :--- | :--- | :--- |\n"
        for t in data:
            reason = get_opportunity_reason(t['keyword'])
            table += f"| {t['keyword']} | {t['score']} | {reason} |\n"
        return table

    new_content = f"## {today}\n\n"
    new_content += "### General Merch Opportunities\n"
    new_content += format_table(general_merch)
    new_content += "\n### Potential IP Infringing Opportunities\n"
    new_content += format_table(ip_infringing)
    new_content += "\n---\n\n"

    # Read existing content
    if os.path.exists(TRENDS_FILE):
        with open(TRENDS_FILE, 'r') as f:
            existing_content = f.read()
            # If the today's section already exists, we might want to avoid duplicates if running multiple times a day
            # But for simplicity, we'll just prepend.
            if f"## {today}" in existing_content:
                print(f"Trends for {today} already exist in {TRENDS_FILE}. Skipping to avoid duplication.")
                return
    else:
        existing_content = ""
        header = "# POD Merch Trends Daily Crawler\n\nDaily automated crawl of Google Trends to identify T-shirt and apparel opportunities.\n\n"
        existing_content = header

    # Prepend new content after the main header if it's a new file,
    # or just at the top if we want latest to earliest.
    # Actually, a better way is to keep the main header at the top.

    main_header = "# POD Merch Trends Daily Crawler\n\nDaily automated crawl of Google Trends to identify T-shirt and apparel opportunities.\n\n"

    if os.path.exists(TRENDS_FILE):
        with open(TRENDS_FILE, 'r') as f:
            lines = f.readlines()

        # Strip header to re-insert it later
        if lines and lines[0].startswith("# POD Merch Trends Daily Crawler"):
            content_without_header = "".join(lines[3:]) if len(lines) > 3 else ""
        else:
            content_without_header = "".join(lines)

        final_content = main_header + new_content + content_without_header
    else:
        final_content = main_header + new_content

    with open(TRENDS_FILE, 'w') as f:
        f.write(final_content)

    print(f"Successfully updated {TRENDS_FILE}")

if __name__ == "__main__":
    print("Starting trends crawl...")
    trends_data = fetch_trends()
    if trends_data:
        update_trends_file(trends_data)
    else:
        print("No rising trends found.")
