import pandas as pd
from pytrends.request import TrendReq
import datetime
import os
import re
import time

def get_trends():
    pytrends = TrendReq(hl='en-US', tz=360)

    keywords = ['tshirt', 'shirt', 'tank top', 'merch']
    all_rising_queries = []

    for kw in keywords:
        print(f"Fetching trends for: {kw}")
        try:
            pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='', gprop='')
            related_queries = pytrends.related_queries()

            if kw in related_queries and related_queries[kw]['rising'] is not None:
                rising = related_queries[kw]['rising']
                rising['seed'] = kw
                all_rising_queries.append(rising)
        except Exception as e:
            print(f"Error fetching {kw}: {e}")

        # Sleep to avoid rate limiting
        time.sleep(5)

    if not all_rising_queries:
        return pd.DataFrame()

    df = pd.concat(all_rising_queries, ignore_index=True)
    return df

def is_ip_infringing(keyword):
    # A simple blacklist of common brands and IP terms
    blacklist = [
        'disney', 'marvel', 'star wars', 'nike', 'adidas', 'gucci', 'prada',
        'pokemon', 'nintendo', 'anime', 'movie', 'film', 'netflix', 'series',
        'band', 'singer', 'actor', 'celebrity', 'harry potter', 'lego',
        'mickey', 'minnie', 'donald duck', 'frozen', 'elsa', 'avengers',
        'iron man', 'spider-man', 'batman', 'superman', 'dc comics',
        'taylor swift', 'kanye', 'ye', 'drake', 'michael jackson', 'beatles',
        'olivia rodrigo', 'bruno mars', 'daniel caesar', 'tame impala', 'suicideboys',
        'masters', 'national geographic', 'nasa'
    ]

    keyword_lower = keyword.lower()
    for item in blacklist:
        if re.search(rf'\b{re.escape(item)}\b', keyword_lower):
            return True
    return False

def filter_and_categorize(df):
    if df.empty:
        return [], []

    # Filter for long-tail (at least 3 words or contains specific apparel terms)
    # Also remove generic terms
    apparel_terms = ['shirt', 'tshirt', 't-shirt', 'tank top', 'tanktop', 'merch', 'tee']
    exclude_terms = ['meaning', 'definition', 'how to', 'why', 'iron', 'near me', 'template', 'mockup']

    general_merch = []
    ip_infringing = []

    seen_keywords = set()

    for _, row in df.iterrows():
        query = row['query']
        value = row['value']

        query_lower = query.lower()

        if query_lower in seen_keywords:
            continue
        seen_keywords.add(query_lower)

        # Check if it contains at least one apparel term
        if not any(term in query_lower for term in apparel_terms):
            continue

        # Exclude non-merch intent
        if any(term in query_lower for term in exclude_terms):
            continue

        # Score/Value check - pytrends 'rising' value is often a percentage increase or 'Breakout'
        score = str(value)

        idea = f"Potential niche for {query}. The internet is showing rising interest in this specific apparel item."

        entry = {
            'keyword': query,
            'score': score,
            'idea': idea
        }

        if is_ip_infringing(query):
            ip_infringing.append(entry)
        else:
            general_merch.append(entry)

    return general_merch, ip_infringing

def format_markdown_table(data):
    if not data:
        return "No opportunities found for this category."

    header = "| keyword | score | why you think is an opportunity, idea for design, or what the internet shopping is already doing |\n"
    separator = "| :--- | :--- | :--- |\n"
    rows = ""
    for item in data:
        rows += f"| {item['keyword']} | {item['score']} | {item['idea']} |\n"

    return header + separator + rows

def update_trends_file(general, ip):
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    new_content = f"## {today}\n\n"
    new_content += "### General Merch Opportunities\n"
    new_content += format_markdown_table(general)
    new_content += "\n\n### Potential IP Infringing Opportunities\n"
    new_content += format_markdown_table(ip)
    new_content += "\n\n---\n\n"

    filename = 'trends.md'
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            old_content = f.read()
            # If today's section already exists, we might want to avoid duplicates if running multiple times a day
            # But for simplicity, we'll just prepend.
            if f"## {today}" in old_content:
                print(f"Trends for {today} already exist in {filename}. Skipping update to avoid duplication.")
                return
    else:
        old_content = ""

    with open(filename, 'w') as f:
        f.write(new_content + old_content)

def main():
    print("Starting Trends Crawler...")
    trends_df = get_trends()
    if trends_df.empty:
        print("No rising trends found.")
        return

    general, ip = filter_and_categorize(trends_df)
    update_trends_file(general, ip)
    print("trends.md updated successfully.")

if __name__ == "__main__":
    main()
