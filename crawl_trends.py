import time
import pandas as pd
from pytrends.request import TrendReq
from datetime import datetime

def get_pytrends_results(keywords):
    # Initialize pytrends with a bit more robust settings if needed
    # Note: method_whitelist is deprecated in newer urllib3, so we handle retries manually
    pytrends = TrendReq(hl='en-US', tz=360)
    all_data = []

    for kw in keywords:
        print(f"Searching for seed keyword: {kw}")
        retries = 3
        while retries > 0:
            try:
                pytrends.build_payload([kw], timeframe='now 7-d')
                related = pytrends.related_queries()
                if kw in related and related[kw]['rising'] is not None:
                    df = related[kw]['rising']
                    all_data.append(df)
                break
            except Exception as e:
                print(f"Error fetching data for {kw}: {e}")
                if "429" in str(e):
                    print("Rate limit (429) hit, waiting 10 seconds before retry...")
                    time.sleep(10)
                    retries -= 1
                else:
                    # For other errors, don't retry
                    break
        time.sleep(2) # Polite delay between keywords

    if not all_data:
        return pd.DataFrame(columns=['query', 'value'])

    return pd.concat(all_data).drop_duplicates('query')

APPAREL_KEYWORDS = ['shirt', 'tshirt', 't-shirt', 'tank top', 'tanktop', 'tee', 'merch']

BLACKLIST = [
    'disney', 'marvel', 'star wars', 'nike', 'adidas', 'taylor swift', 'bts',
    'michael jackson', 'micheal jackson', 'nba', 'nfl', 'mlb', 'nhl',
    'nintendo', 'pokemon', 'harry potter', 'nasa', 'hellstar', 'ysl', 'gucci',
    'prada', 'louis vuitton', 'koningsdag', 'oranje', 'higgins', 'wwe',
    'kanye', 'drake', 'notre dame'
]

EXCLUDE_TERMS = [
    'meaning', 'definition', 'how to', 'why', 'iron', 'near me', 'template',
    'mockup', 'tee times', 'tee time', 'tee off', 'graphic tee', 'essential tee',
    'vintage tee', 'oversized tee', 'plain shirt', 'blank shirt'
]

def is_ip_infringing(query):
    query_lower = query.lower()
    for brand in BLACKLIST:
        if brand in query_lower:
            return True
    return False

def is_valid_merch_query(query):
    query_lower = query.lower()

    # Must have 2+ words
    if len(query_lower.split()) < 2:
        return False

    # Must contain an apparel keyword
    if not any(ak in query_lower for ak in APPAREL_KEYWORDS):
        return False

    # Must not contain excluded terms
    if any(et in query_lower for et in EXCLUDE_TERMS):
        return False

    return True

def generate_idea(query):
    query_lower = query.lower()
    concept = query_lower

    # Remove apparel keywords to find the core concept
    # Sort by length descending to replace longer ones first (e.g. 't-shirt' before 'shirt')
    for ak in sorted(APPAREL_KEYWORDS, key=len, reverse=True):
        concept = concept.replace(ak, "")

    concept = " ".join(concept.split()).strip()

    if not concept:
        return "General apparel design around the keyword."

    return f"Design featuring '{concept}' theme. People are searching for specific '{concept}' apparel which indicates a niche demand."

def update_trends_md(df):
    if df.empty:
        print("No new trends to add.")
        return

    today = datetime.now().strftime('%Y-%m-%d')

    # Sort results by value (score) descending
    # Handle 'Breakout' which is often used in rising trends
    def sort_key(val):
        if isinstance(val, str) and val.lower() == 'breakout':
            return 9999
        try:
            return int(val)
        except:
            return 0

    df['sort_val'] = df['value'].apply(sort_key)
    df = df.sort_values('sort_val', ascending=False)

    general = df[~df['is_ip']]
    infringing = df[df['is_ip']]

    new_content = f"## {today}\n\n"

    new_content += "### General Merch Opportunities\n"
    if not general.empty:
        new_content += "| keyword | score | why/idea |\n"
        new_content += "|---------|-------|----------|\n"
        for _, row in general.iterrows():
            new_content += f"| {row['query']} | {row['value']} | {row['idea']} |\n"
    else:
        new_content += "No general opportunities found today.\n"

    new_content += "\n### Potential IP Infringing Opportunities\n"
    if not infringing.empty:
        new_content += "| keyword | score | why/idea |\n"
        new_content += "|---------|-------|----------|\n"
        for _, row in infringing.iterrows():
            new_content += f"| {row['query']} | {row['value']} | {row['idea']} |\n"
    else:
        new_content += "No IP infringing opportunities found today.\n"

    new_content += "\n---\n\n"

    try:
        with open("trends.md", "r") as f:
            existing_content = f.read()
            # Avoid duplicate entries for the same day if script is run multiple times
            if f"## {today}" in existing_content:
                print(f"Trends for {today} already exist in trends.md. Skipping update.")
                return
    except FileNotFoundError:
        existing_content = ""

    with open("trends.md", "w") as f:
        f.write(new_content + existing_content)

    print(f"Successfully updated trends.md with {len(df)} new trends.")

if __name__ == "__main__":
    seeds = APPAREL_KEYWORDS
    results = get_pytrends_results(seeds)

    if results.empty:
        print("No results found.")
    else:
        # Filter for valid merch queries
        results['is_valid'] = results['query'].apply(is_valid_merch_query)
        filtered_results = results[results['is_valid']].copy()

        if filtered_results.empty:
            print("No valid merch queries found after filtering.")
        else:
            # Check for IP infringement
            filtered_results['is_ip'] = filtered_results['query'].apply(is_ip_infringing)

            # Generate ideas
            filtered_results['idea'] = filtered_results['query'].apply(generate_idea)

            update_trends_md(filtered_results)
