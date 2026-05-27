import time
import pandas as pd
from pytrends.request import TrendReq
from datetime import date
import os
import re

def fetch_trends(pytrends, keywords):
    all_rising = []
    for kw in keywords:
        print(f"Fetching trends for: {kw}")

        # Build payload with custom retry for 429
        success = False
        for attempt in range(3):
            try:
                pytrends.build_payload([kw], timeframe='now 7-d')
                success = True
                break
            except Exception as e:
                if '429' in str(e):
                    print(f"Rate limited during build_payload for {kw}. Waiting 60s (Attempt {attempt+1}/3)...")
                    time.sleep(60)
                else:
                    print(f"Error building payload for {kw}: {e}")
                    break

        if not success:
            continue

        # Fetch related queries with custom retry for 429
        for attempt in range(3):
            try:
                related_queries = pytrends.related_queries()
                if kw in related_queries and related_queries[kw]['rising'] is not None:
                    rising = related_queries[kw]['rising']
                    all_rising.append(rising)
                break
            except Exception as e:
                if '429' in str(e):
                    print(f"Rate limited during related_queries for {kw}. Waiting 60s (Attempt {attempt+1}/3)...")
                    time.sleep(60)
                else:
                    print(f"Error fetching related queries for {kw}: {e}")
                    break

        # Small delay between keywords to mitigate rate limiting
        time.sleep(5)

    if not all_rising:
        return pd.DataFrame(columns=['query', 'value'])

    return pd.concat(all_rising).drop_duplicates(subset=['query'])

def main():
    pytrends = TrendReq(hl='en-US', tz=360)
    keywords = ['tshirt', 't-shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch']

    df = fetch_trends(pytrends, keywords)

    if df.empty:
        print("No rising trends found.")
        return

    # Process score: 'Breakout' -> 9999, others to int
    def process_score(val):
        if val == 'Breakout':
            return 9999
        try:
            return int(val)
        except:
            return 0

    df['score'] = df['value'].apply(process_score)
    df = df.sort_values(by='score', ascending=False)

    # Blacklist of IP-related keywords
    ip_blacklist = [
        'disney', 'marvel', 'star wars', 'nike', 'adidas', 'taylor swift', 'bts',
        'michael jackson', 'nba', 'wnba', 'nfl', 'mlb', 'nhl', 'nintendo', 'pokemon',
        'harry potter', 'nasa', 'hellstar', 'ysl', 'gucci', 'prada', 'louis vuitton',
        'arsenal', 'real madrid', 'liverpool', 'man city', 'chelsea', 'bayern', 'barcelona',
        'knicks', 'lakers', 'celtics', 'warriors', 'bulls', 'amiri', 'trapstar', 'corteiz',
        'sp5der', 'minus two', 'syna world', 'harry styles', 'gracie abrams', 'daniel caesar',
        'bad bunny', 'billie eilish', 'drake', 'kanye', 'travis scott', 'bruno mars',
        'hello kitty', 'sanrio', 'nascar', 'f1', 'mercedes', 'ferrari', 'red bull'
    ]

    # Commercial/Relevant filters
    exclude_terms = [
        'meaning', 'definition', 'how to', 'why', 'iron', 'near me', 'template', 'mockup',
        'tee times', 'tee time', 'tee off', 'graphic tee', 'essential tee', 'vintage tee',
        'oversized tee', 'plain shirt', 'blank shirt', 'kaffee', 'rezepte', 'bh für', 'bra for',
        'tutorial', 'là gì'
    ]

    apparel_terms = ['shirt', 'tshirt', 't-shirt', 'tank top', 'tanktop', 'tee', 'merch']

    def is_ip_infringing(query):
        q = query.lower()
        return any(brand in q for brand in ip_blacklist)

    def is_relevant(query):
        q = query.lower()
        # Must be long tail (2+ words)
        if len(q.split()) < 2:
            return False
        # Must contain an apparel term
        if not any(term in q for term in apparel_terms):
            return False
        # Exclude exact matches or very generic ones
        if q.strip() in apparel_terms or q.strip() in ['t shirt', 't-shirts', 'tees']:
            return False
        # Exclude non-commercial terms
        if any(term in q for term in exclude_terms):
            return False
        return True

    def generate_idea(query):
        # Clean up the keyword to form an idea
        idea = query
        # Remove common apparel terms to get the core concept
        # Order matters: replace longer strings first
        for term in sorted(['t-shirt', 'tshirt', 't shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch'], key=len, reverse=True):
            idea = re.sub(rf'\b{term}s?\b', '', idea, flags=re.IGNORECASE).strip()

        # Clean up multiple spaces
        idea = re.sub(r'\s+', ' ', idea).strip()

        if not idea:
            return f"Design related to '{query}'"
        return f"A design featuring '{idea}'"

    # Filter and categorize
    results = []
    processed_keywords = set()

    for _, row in df.iterrows():
        query = row['query']
        if query in processed_keywords:
            continue

        if is_relevant(query):
            is_ip = is_ip_infringing(query)
            idea = generate_idea(query)
            results.append({
                'keyword': query,
                'score': row['score'],
                'idea': idea,
                'is_ip': is_ip
            })
            processed_keywords.add(query)

    if not results:
        print("No relevant trends found after filtering.")
        return

    # Prepare markdown
    today = date.today().strftime('%Y-%m-%d')
    markdown_output = f"## {today}\n\n"

    general_merch = [r for r in results if not r['is_ip']]
    ip_infringing = [r for r in results if r['is_ip']]

    if general_merch:
        markdown_output += "### General Merch Opportunities\n"
        markdown_output += "| keyword | score | Why/Idea |\n"
        markdown_output += "| :--- | :--- | :--- |\n"
        for r in general_merch:
            markdown_output += f"| {r['keyword']} | {r['score']} | {r['idea']} |\n"
        markdown_output += "\n"

    if ip_infringing:
        markdown_output += "### Potential IP Infringing Opportunities\n"
        markdown_output += "| keyword | score | Why/Idea |\n"
        markdown_output += "| :--- | :--- | :--- |\n"
        for r in ip_infringing:
            markdown_output += f"| {r['keyword']} | {r['score']} | {r['idea']} |\n"
        markdown_output += "\n"

    # Prepend to trends.md
    filename = 'trends.md'
    existing_content = ""
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            existing_content = f.read()

    # Avoid duplicate daily updates if script runs multiple times
    if f"## {today}" in existing_content:
        print(f"Trends for {today} already exist in {filename}. Skipping update.")
        return

    with open(filename, 'w') as f:
        f.write(markdown_output + existing_content)

    print(f"Updated {filename} with {len(results)} trends.")

if __name__ == "__main__":
    main()
