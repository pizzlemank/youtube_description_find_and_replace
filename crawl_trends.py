import time
import pandas as pd
from pytrends.request import TrendReq
from datetime import datetime
import os

def fetch_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    keywords = ['tshirt', 't-shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch']
    apparel_terms = ['shirt', 'tshirt', 't-shirt', 'tank top', 'tanktop', 'tee', 'merch']
    all_rising = []

    for kw in keywords:
        print(f"Fetching trends for: {kw}")
        retries = 3
        while retries > 0:
            try:
                pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='', gprop='')
                related_queries = pytrends.related_queries()

                if kw in related_queries and related_queries[kw]['rising'] is not None:
                    rising = related_queries[kw]['rising']
                    all_rising.append(rising)

                # Sleep to avoid rate limiting
                time.sleep(5)
                break
            except Exception as e:
                print(f"Error fetching trends for {kw}: {e}")
                if "429" in str(e):
                    print("Rate limit hit. Sleeping for 60 seconds...")
                    time.sleep(60)
                    retries -= 1
                else:
                    break

    if not all_rising:
        return pd.DataFrame()

    df = pd.concat(all_rising).drop_duplicates(subset=['query'])

    # Filtering for long-tail keywords (2+ words) containing apparel terms
    def is_valid(query):
        query_low = query.lower()
        words = query_low.split()
        if len(words) < 2:
            return False

        # Check if it's just a generic term like "t shirt" or "tank top"
        if query_low in ['t shirt', 't-shirt', 'tshirt', 'tank top', 'tanktop', 'tees']:
            return False

        # Exclude common non-merch related terms
        exclude = [
            'meaning', 'definition', 'how to', 'why', 'iron', 'near me', 'template', 'mockup',
            'tee times', 'tee time', 'tee off', 'graphic tee', 'essential tee', 'vintage tee',
            'oversized tee', 'plain shirt', 'blank shirt', 'kaffee', 'rezepte', 'bh für', 'bra for',
            'tutorial', 'là gì'
        ]
        if any(ex in query_low for ex in exclude):
            return False

        return any(term in query_low for term in apparel_terms)

    df = df[df['query'].apply(is_valid)]

    # Handle 'Breakout' score by converting to a large number for sorting
    def parse_score(val):
        if val == 'Breakout':
            return 9999
        try:
            return int(val)
        except:
            return 0

    df['score_val'] = df['value'].apply(parse_score)
    df = df.sort_values(by='score_val', ascending=False)

    # IP Infringement Detection
    ip_blacklist = [
        'disney', 'marvel', 'star wars', 'nike', 'adidas', 'taylor swift', 'bts',
        'michael jackson', 'nba', 'wnba', 'nfl', 'mlb', 'nhl', 'nintendo', 'pokemon',
        'harry potter', 'nasa', 'hellstar', 'ysl', 'gucci', 'prada', 'louis vuitton',
        'arsenal', 'real madrid', 'liverpool', 'man city', 'chelsea', 'bayern', 'barcelona',
        'knicks', 'lakers', 'celtics', 'warriors', 'bulls', 'amiri', 'trapstar', 'corteiz',
        'sp5der', 'minus two', 'syna world', 'harry styles', 'gracie abrams', 'daniel caesar',
        'bad bunny', 'billie eilish', 'drake', 'kanye', 'travis scott', 'hello kitty', 'bruno mars'
    ]

    def check_ip(query):
        return any(brand in query.lower() for brand in ip_blacklist)

    df['is_ip_infringing'] = df['query'].apply(check_ip)

    return df

def generate_idea(query):
    # Simple idea generation based on the query
    clean_query = query.lower()
    # Sort terms by length descending to replace longer ones first (e.g. 't-shirt' before 'shirt')
    terms = sorted(['shirt', 'tshirt', 't-shirt', 'tank top', 'tanktop', 'tee', 'merch', 't shirt'], key=len, reverse=True)
    for term in terms:
        clean_query = clean_query.replace(term, '').strip()

    # Clean up multiple spaces
    clean_query = ' '.join(clean_query.split())

    if not clean_query:
        clean_query = query # fallback if everything was replaced

    return f"Design concept: '{clean_query}'. This is a rising search term on Google Trends. Opportunity to create a unique graphic or typography-based design for POD platforms."

def update_trends_md(df):
    if df.empty:
        print("No new trends found.")
        return

    today = datetime.now().strftime('%Y-%m-%d')
    header = f"## {today}\n\n"

    gen_df = df[~df['is_ip_infringing']]
    ip_df = df[df['is_ip_infringing']]

    content = header

    if not gen_df.empty:
        content += "### General Merch Opportunities\n"
        content += "| keyword | score | Why/Idea |\n"
        content += "| :--- | :--- | :--- |\n"
        for _, row in gen_df.iterrows():
            idea = generate_idea(row['query'])
            content += f"| {row['query']} | {row['value']} | {idea} |\n"
        content += "\n"

    if not ip_df.empty:
        content += "### Potential IP Infringing Opportunities\n"
        content += "| keyword | score | Why/Idea |\n"
        content += "| :--- | :--- | :--- |\n"
        for _, row in ip_df.iterrows():
            idea = generate_idea(row['query'])
            content += f"| {row['query']} | {row['value']} | {idea} (Flagged for potential IP) |\n"
        content += "\n"

    existing_content = ""
    if os.path.exists('trends.md'):
        with open('trends.md', 'r') as f:
            existing_content = f.read()

    # Avoid duplicate headers for the same day
    if header.strip() in existing_content:
        print(f"Trends for {today} already exist in trends.md")
        return

    with open('trends.md', 'w') as f:
        f.write(content + existing_content)

    print(f"Updated trends.md with {len(df)} new trends.")

if __name__ == "__main__":
    df = fetch_trends()
    update_trends_md(df)
