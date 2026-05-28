import time
import datetime
import os
import pandas as pd
from pytrends.request import TrendReq

def get_pytrends():
    # hl = host language, tz = timezone offset
    return TrendReq(hl='en-US', tz=360)

def fetch_trends(pytrends, kw_list):
    all_rising = []
    for kw in kw_list:
        print(f"Fetching trends for: {kw}")
        success = False
        retries = 3
        while not success and retries > 0:
            try:
                pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='', gprop='')
                related_queries = pytrends.related_queries()
                if kw in related_queries and related_queries[kw]['rising'] is not None:
                    rising = related_queries[kw]['rising']
                    all_rising.append(rising)
                success = True
                time.sleep(5) # Delay to avoid 429
            except Exception as e:
                print(f"Error fetching {kw}: {e}")
                if "429" in str(e):
                    print("Rate limit hit, sleeping for 60s...")
                    time.sleep(60)
                    retries -= 1
                else:
                    break # Other errors, don't retry for now

    if not all_rising:
        return pd.DataFrame()

    return pd.concat(all_rising).drop_duplicates(subset=['query'])

IP_BLACKLIST = [
    'disney', 'marvel', 'star wars', 'nike', 'adidas', 'taylor swift', 'bts', 'michael jackson',
    'nba', 'wnba', 'nfl', 'mlb', 'nhl', 'nintendo', 'pokemon', 'harry potter', 'nasa',
    'hellstar', 'ysl', 'gucci', 'prada', 'louis vuitton', 'arsenal', 'real madrid', 'liverpool',
    'man city', 'chelsea', 'bayern', 'barcelona', 'knicks', 'lakers', 'celtics', 'warriors', 'bulls',
    'amiri', 'trapstar', 'corteiz', 'sp5der', 'minus two', 'syna world', 'harry styles',
    'gracie abrams', 'daniel caesar', 'bad bunny', 'billie eilish', 'drake', 'kanye', 'travis scott',
    'bruno mars', 'hello kitty', 'sanrio', 'nascar', 'f1', 'mercedes', 'ferrari', 'red bull'
]

APPAREL_TERMS = ['shirt', 'tshirt', 't-shirt', 'tank top', 'tanktop', 'tee', 'merch']

EXCLUDE_TERMS = [
    'meaning', 'definition', 'how to', 'why', 'iron', 'near me', 'template', 'mockup',
    'tee times', 'tee time', 'tee off', 'graphic tee', 'essential tee', 'vintage tee',
    'oversized tee', 'plain shirt', 'blank shirt', 'kaffee', 'rezepte', 'bh für', 'bra for',
    'tutorial', 'là gì'
]

def is_ip_infringing(query):
    query_lower = query.lower()
    for brand in IP_BLACKLIST:
        if brand in query_lower:
            return True
    return False

def is_valid_opportunity(query):
    query_lower = query.lower()
    # Must be long tail (2+ words)
    if len(query_lower.split()) < 2:
        return False

    # Must contain apparel term
    if not any(term in query_lower for term in APPAREL_TERMS):
        return False

    # Filter out exact seed keywords or very generic ones
    if query_lower in APPAREL_TERMS or query_lower in ['t shirt', 't-shirts', 'tees']:
        return False

    # Filter out excluded terms
    if any(term in query_lower for term in EXCLUDE_TERMS):
        return False

    return True

def generate_idea(query):
    query_lower = query.lower()
    concept = query_lower
    # Try to extract the main concept by removing the apparel term
    # Sort APPAREL_TERMS by length descending to catch 't-shirt' before 'shirt'
    for term in sorted(APPAREL_TERMS, key=len, reverse=True):
        if term in concept:
            concept = concept.replace(term, '').strip()
            break

    # Clean up multiple spaces
    concept = ' '.join(concept.split())

    if not concept:
        return f"Trending {query} search. People are looking for this specific style."

    return f"Trending design for '{concept}'. Possible design: a graphic or typography featuring '{concept}' that appeals to this trending niche."

def main():
    pytrends = get_pytrends()
    seed_keywords = ['tshirt', 't-shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch']

    df = fetch_trends(pytrends, seed_keywords)

    if df.empty:
        print("No trends found.")
        return

    # Process score for sorting
    def process_score(val):
        if val == 'Breakout':
            return 9999
        try:
            return int(val)
        except:
            return 0

    df['numeric_score'] = df['value'].apply(process_score)
    df = df.sort_values(by='numeric_score', ascending=False)

    # Filter and categorize
    general_opps = []
    ip_opps = []

    seen_queries = set()

    for _, row in df.iterrows():
        query = row['query']
        if query in seen_queries:
            continue
        seen_queries.add(query)

        if is_valid_opportunity(query):
            idea = generate_idea(query)
            entry = {
                'keyword': query,
                'score': row['value'],
                'idea': idea
            }
            if is_ip_infringing(query):
                ip_opps.append(entry)
            else:
                general_opps.append(entry)

    if not general_opps and not ip_opps:
        print("No valid opportunities found after filtering.")
        return

    # Prepare markdown
    today = datetime.date.today().strftime('%Y-%m-%d')
    markdown_content = f"## {today}\n\n"

    markdown_content += "### General Merch Opportunities\n"
    if general_opps:
        markdown_content += "| keyword | score | why you think is an opportunity, idea for design, or what the internet shopping is already doing |\n"
        markdown_content += "| :--- | :--- | :--- |\n"
        for opp in general_opps:
            markdown_content += f"| {opp['keyword']} | {opp['score']} | {opp['idea']} |\n"
    else:
        markdown_content += "No new general opportunities found.\n"

    markdown_content += "\n### Potential IP Infringing Opportunities\n"
    if ip_opps:
        markdown_content += "| keyword | score | why you think is an opportunity, idea for design, or what the internet shopping is already doing |\n"
        markdown_content += "| :--- | :--- | :--- |\n"
        for opp in ip_opps:
            markdown_content += f"| {opp['keyword']} | {opp['score']} | {opp['idea']} |\n"
    else:
        markdown_content += "No new IP infringing opportunities found.\n"

    markdown_content += "\n---\n\n"

    # Prepend to trends.md, but keep title at top if it exists
    filename = 'trends.md'
    header = "# Merch Trends Tracker\n\nDaily automated Google Trends crawl for Print-on-Demand (POD) opportunities.\n\n---\n\n"
    existing_content = ""

    if os.path.exists(filename):
        with open(filename, 'r') as f:
            existing_content = f.read()
            if f"## {today}" in existing_content:
                print(f"Trends for {today} already exist. Skipping.")
                return

            # Remove header from existing content if it exists to avoid duplication
            if existing_content.startswith("# Merch Trends Tracker"):
                parts = existing_content.split("---\n\n", 1)
                if len(parts) > 1:
                    existing_content = parts[1]
                else:
                    # If format is different, just keep it as is and we might have double header
                    # but splitting by --- is safer
                    pass

    with open(filename, 'w') as f:
        f.write(header + markdown_content + existing_content)

    print(f"Successfully updated {filename}")

if __name__ == "__main__":
    main()
