import time
import random
import pandas as pd
from pytrends.request import TrendReq
from datetime import datetime
import os
import re

# Configuration
SEED_KEYWORDS = ['tshirt', 't-shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch']
TIMEFRAME = 'now 7-d'
DELAY_BETWEEN_QUERIES = 5
MAX_RETRIES = 2
RETRY_DELAY = 30

# Filtering configuration
APPAREL_TERMS = ['shirt', 'tshirt', 't-shirt', 'tank top', 'tanktop', 'tee', 'merch']
EXCLUDED_TERMS = [
    'meaning', 'definition', 'how to', 'why', 'iron', 'near me', 'template',
    'mockup', 'tee times', 'tee time', 'tee off', 'graphic tee', 'essential tee',
    'vintage tee', 'oversized tee', 'plain shirt', 'blank shirt', 'kaffee',
    'rezepte', 'bh für', 'bra for', 'tutorial', 'bra', 't-shirt bra', 'là gì'
]

IP_BLACKLIST = [
    'disney', 'marvel', 'star wars', 'nike', 'adidas', 'taylor swift', 'bts',
    'michael jackson', 'nba', 'wnba', 'nfl', 'mlb', 'nhl', 'nintendo', 'pokemon',
    'harry potter', 'nasa', 'hellstar', 'ysl', 'gucci', 'prada', 'louis vuitton',
    'arsenal', 'real madrid', 'liverpool', 'man city', 'chelsea', 'bayern',
    'barcelona', 'knicks', 'lakers', 'celtics', 'warriors', 'bulls', 'amiri',
    'trapstar', 'corteiz', 'sp5der', 'minus two', 'syna world', 'harry styles',
    'gracie abrams', 'daniel caesar', 'bad bunny', 'billie eilish', 'drake',
    'kanye', 'travis scott', 'bruno mars', 'hello kitty', 'sanrio', 'nascar',
    'f1', 'mercedes', 'ferrari', 'red bull', 'toy story', 'psg', 'asap rocky',
    'megan moroney', 'sean john', 'morgan wallen', 'spurs', 'rcb', 'snipes',
    'asos', 'pattie gonia', 'wingstop', 'ariana grande', 'selena gomez',
    'carhartt', 'hazbin hotel', 'digital circus', 'tadc', 'linkin park',
    'bad omens', 'forrest frank', 'malcolm todd', 'böhse onkelz', 'love island',
    'eternal sunshine', 'madewell', 'anthropologie', 'glitch', 'stevie nicks',
    'beyonce', 'lilibet'
]

def is_ip_infringing(query):
    """Checks if a query contains any blacklisted IP terms using word boundaries."""
    query_lower = query.lower()
    for term in IP_BLACKLIST:
        if re.search(rf'\b{re.escape(term.lower())}\b', query_lower):
            return True
    return False

def is_relevant_merch(query):
    """Filters for long-tail merch-related keywords while excluding noise."""
    query_lower = query.lower()

    # Check for excluded terms
    if any(term in query_lower for term in EXCLUDED_TERMS):
        return False

    # Check for apparel terms
    has_apparel = any(term in query_lower for term in APPAREL_TERMS)
    if not has_apparel:
        return False

    # Long-tail: 2+ words
    words = query_lower.split()
    if len(words) < 2:
        return False

    # Avoid exact matches or generic variations of seed keywords
    if query_lower in SEED_KEYWORDS or query_lower in ['t shirts', 't-shirts', 'tees']:
        return False

    return True

def generate_idea(query):
    """Generates a simple design idea based on the keyword."""
    query_clean = query.lower()

    # Priority for longer apparel terms
    long_apparel_terms = ['t-shirt', 'tshirt', 'tank top', 'tanktop', 'merch']
    for term in long_apparel_terms:
        if term in query_clean:
            concept = query_clean.replace(term, '').strip()
            # Clean up potential double spaces
            concept = re.sub(' +', ' ', concept)
            return f"Design a creative graphic featuring '{concept}'. The market is searching for specific {term} designs for this niche."

    # Fallback to shorter terms
    for term in ['shirt', 'tee']:
        if term in query_clean:
            concept = query_clean.replace(term, '').strip()
            concept = re.sub(' +', ' ', concept)
            return f"Design a creative graphic featuring '{concept}'. This is a trending search for {term} designs."

    return f"Trending search for '{query}'. Great opportunity for a themed design."

def get_pytrends_with_retry():
    """Returns a TrendReq object with custom retry handling for 429 errors."""
    # We'll implement retry logic around the data fetching calls themselves
    return TrendReq(hl='en-US', tz=360)

def fetch_rising_queries(pytrends, keyword):
    """Fetches rising related queries for a keyword with retry logic."""
    for attempt in range(MAX_RETRIES + 1):
        try:
            pytrends.build_payload([keyword], cat=0, timeframe=TIMEFRAME, geo='', gprop='')
            related_queries = pytrends.related_queries()
            if keyword in related_queries and related_queries[keyword]['rising'] is not None:
                return related_queries[keyword]['rising']
            return pd.DataFrame()
        except Exception as e:
            if "429" in str(e):
                if attempt < MAX_RETRIES:
                    print(f"Rate limited for '{keyword}'. Retrying in {RETRY_DELAY}s...")
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    print(f"Max retries reached for '{keyword}'. Skipping.")
            else:
                print(f"Error fetching data for '{keyword}': {e}")
            return pd.DataFrame()

def main():
    pytrends = get_pytrends_with_retry()
    all_results = []

    print(f"Starting crawl at {datetime.now()}")

    for kw in SEED_KEYWORDS:
        print(f"Fetching rising queries for: {kw}")
        rising_df = fetch_rising_queries(pytrends, kw)

        if not rising_df.empty:
            all_results.append(rising_df)

        time.sleep(DELAY_BETWEEN_QUERIES)

    if not all_results:
        print("No rising queries found.")
        return

    combined_df = pd.concat(all_results).drop_duplicates(subset=['query'])

    # Apply filtering
    combined_df['is_relevant'] = combined_df['query'].apply(is_relevant_merch)
    relevant_df = combined_df[combined_df['is_relevant']].copy()

    print(f"Found {len(relevant_df)} relevant rising queries.")

    if relevant_df.empty:
        return

    # Sort and add ideas
    relevant_df['is_ip'] = relevant_df['query'].apply(is_ip_infringing)
    relevant_df['idea'] = relevant_df['query'].apply(generate_idea)

    # Format score: breakout -> 9999 for sorting
    relevant_df['score_numeric'] = pd.to_numeric(relevant_df['value'].replace('Breakout', '9999'), errors='coerce').fillna(0)
    relevant_df = relevant_df.sort_values(by='score_numeric', ascending=False)

    # Split into IP and General
    general_df = relevant_df[~relevant_df['is_ip']]
    ip_df = relevant_df[relevant_df['is_ip']]

    # Prepare markdown
    today = datetime.now().strftime('%Y-%m-%d')
    markdown_output = f"\n## {today}\n"

    if not general_df.empty:
        markdown_output += "\n### General Merch Opportunities\n"
        markdown_output += "| keyword | score | Why/Idea |\n"
        markdown_output += "| :--- | :--- | :--- |\n"
        for _, row in general_df.iterrows():
            markdown_output += f"| {row['query']} | {row['value']} | {row['idea']} |\n"

    if not ip_df.empty:
        markdown_output += "\n### Potential IP Infringing Opportunities\n"
        markdown_output += "| keyword | score | Why/Idea |\n"
        markdown_output += "| :--- | :--- | :--- |\n"
        for _, row in ip_df.iterrows():
            markdown_output += f"| {row['query']} | {row['value']} | {row['idea']} |\n"

    # Prepend to trends.md
    if os.path.exists('trends.md'):
        with open('trends.md', 'r', encoding='utf-8') as f:
            content = f.read()

        # Avoid duplicate daily updates
        if f"## {today}" in content:
            print(f"Already updated trends.md for {today}. Skipping.")
            return

        header = "# Google Trends Merch Opportunities\n"
        new_content = header + markdown_output + content.replace(header, "")

        with open('trends.md', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Updated trends.md successfully.")
    else:
        with open('trends.md', 'w', encoding='utf-8') as f:
            f.write("# Google Trends Merch Opportunities\n" + markdown_output)
        print("Created trends.md with new data.")

if __name__ == "__main__":
    main()
