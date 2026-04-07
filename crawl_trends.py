import pandas as pd
from pytrends.request import TrendReq
import datetime
import os
import re
import time

def crawl():
    print("Starting Google Trends crawl...")
    # hl='en-US', tz=360 (CST)
    pytrends = TrendReq(hl='en-US', tz=360)

    # Keywords to search for
    seed_keywords = ['tshirt', 'shirt', 'tank top', 'merch']

    all_rising = []

    for kw in seed_keywords:
        print(f"Fetching trends for: {kw}")
        try:
            # Using a 7-day timeframe to catch recent rising trends
            pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='', gprop='')
            related_queries = pytrends.related_queries()

            if kw in related_queries:
                rising = related_queries[kw]['rising']
                if rising is not None and not rising.empty:
                    rising['seed'] = kw
                    all_rising.append(rising)
            # Sleep to avoid rate limiting from Google
            time.sleep(2)
        except Exception as e:
            print(f"Error fetching {kw}: {e}")

    if not all_rising:
        print("No rising trends found today.")
        # If no trends, we still might want to mark the date to avoid repeated attempts
        # but for now, let's just return.
        return

    df = pd.concat(all_rising)

    # Filter for long tail and remove generic ones
    # We want keywords that contain one of our seed terms
    df = df[df['query'].str.contains('|'.join(['shirt', 'tshirt', 'tank top', 'merch']), case=False)]

    # Exclude common non-commercial or irrelevant terms that aren't good for POD
    exclude_terms = [
        'how to', 'meaning', 'definition', 'crossword', 'clue', 'why', 'iron',
        'near me', 'template', 'mockup', 'size chart', 'dye', 'bleach', 'wash'
    ]
    df = df[~df['query'].str.contains('|'.join(exclude_terms), case=False)]

    # Deduplicate
    df = df.drop_duplicates(subset=['query'])

    # IP Infringement detection - Heuristic based on known brands
    ip_brands = [
        'disney', 'marvel', 'dc comics', 'star wars', 'nike', 'adidas', 'gucci', 'prada', 'zara',
        'h&m', 'nintendo', 'pokemon', 'harry potter', 'netflix', 'michael jackson', 'ye', 'kanye',
        'olivia rodrigo', 'bruno mars', 'taylor swift', 'lego', 'barbie', 'oppenheimer', 'apple',
        'warner bros', 'paramount', 'sony', 'universal', 'mcdonalds', 'starbucks', 'cocacola', 'pepsi'
    ]

    def is_potential_ip(query):
        query_lower = query.lower()
        for brand in ip_brands:
            # Using word boundaries to avoid matching parts of words (e.g., 'apple' in 'pineapple')
            if re.search(rf'\b{brand}\b', query_lower):
                return True
        return False

    df['is_ip'] = df['query'].apply(is_potential_ip)

    # Generate "Why" / Idea column
    def generate_why(row):
        query = row['query']
        score = row['value']

        # Simple heuristics for design ideas
        if 'easter' in query.lower():
            return f"Holiday trend ({score}%). Design idea: Minimalist bunny or punny Easter typography for family matching."
        if 'tshirt' in query.lower() or 'shirt' in query.lower():
            return f"Rising interest in specific apparel ({score}%). Good for targeted graphic design. Check Amazon/Etsy for current competition."
        if 'merch' in query.lower():
            return f"Creator or niche event merch rising ({score}%). Opportunity to capture similar aesthetic or related fan interest."

        return f"Trending keyword ({score}%). Check search volume and design styles on POD platforms."

    df['why'] = df.apply(generate_why, axis=1)

    # Prepare Markdown content
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")

    # Check if we already have an entry for today to avoid duplicates in the file
    if os.path.exists("trends.md"):
        with open("trends.md", "r") as f:
            content = f.read()
            if f"## {date_str}" in content:
                print(f"Trends for {date_str} already exist in trends.md. Skipping update.")
                return

    general_df = df[~df['is_ip']]
    ip_df = df[df['is_ip']]

    md_content = f"## {date_str}\n\n"

    md_content += "### General Merch Opportunities\n"
    if not general_df.empty:
        md_content += "| keyword | score | why you think is an opportunity, idea for design, or what the internet shopping is already doing |\n"
        md_content += "|---------|-------|------------------------------------------------------------------------------------------------|\n"
        for _, row in general_df.iterrows():
            md_content += f"| {row['query']} | {row['value']} | {row['why']} |\n"
    else:
        md_content += "No new general opportunities found today.\n"

    md_content += "\n### Potential IP Infringing Opportunities\n"
    if not ip_df.empty:
        md_content += "| keyword | score | why you think is an opportunity, idea for design, or what the internet shopping is already doing |\n"
        md_content += "|---------|-------|------------------------------------------------------------------------------------------------|\n"
        for _, row in ip_df.iterrows():
            md_content += f"| {row['query']} | {row['value']} | {row['why']} |\n"
    else:
        md_content += "No new IP infringing opportunities found today.\n"

    md_content += "\n---\n"

    # Prepend to trends.md (latest to earliest)
    existing_content = ""
    if os.path.exists("trends.md"):
        with open("trends.md", "r") as f:
            existing_content = f.read()

    with open("trends.md", "w") as f:
        f.write(md_content + "\n" + existing_content)
    print(f"Successfully updated trends.md for {date_str}")

if __name__ == "__main__":
    crawl()
