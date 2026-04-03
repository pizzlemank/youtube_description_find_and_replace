import pandas as pd
from pytrends.request import TrendReq
import time

def fetch_trends(keywords):
    pytrends = TrendReq(hl='en-US', tz=360)
    all_rising = []

    for kw in keywords:
        print(f"Fetching trends for: {kw}")
        try:
            pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='', gprop='')
            related_queries = pytrends.related_queries()

            if kw in related_queries and related_queries[kw]['rising'] is not None:
                rising = related_queries[kw]['rising']
                rising['seed'] = kw
                all_rising.append(rising)
        except Exception as e:
            print(f"Error fetching {kw}: {e}")

        # Sleep to avoid rate limiting
        time.sleep(2)

    if not all_rising:
        return pd.DataFrame()

    return pd.concat(all_rising, ignore_index=True).drop_duplicates(subset=['query'])

def filter_trends(df):
    if df.empty:
        return df

    apparel_terms = ['shirt', 'tshirt', 't-shirt', 'tanktop', 'tank top', 'merch', 'tee', 'hoodie']

    # Filter for keywords containing apparel terms
    mask = df['query'].str.contains('|'.join(apparel_terms), case=False, na=False)
    df = df[mask].copy()

    # Filter for long-tail (3+ words)
    df['word_count'] = df['query'].str.split().str.len()
    df = df[df['word_count'] >= 3].copy()

    # Filter out common non-commercial or noisy terms
    noise = ['meaning', 'definition', 'crossword', 'clue', 'how to', 'what is']
    mask_noise = ~df['query'].str.contains('|'.join(noise), case=False, na=False)
    df = df[mask_noise].copy()

    return df

def categorize_trends(df):
    if df.empty:
        return df, pd.DataFrame()

    # List of known brands, franchises, etc. that might be IP infringing
    ip_list = [
        'disney', 'marvel', 'star wars', 'mickey', 'minnie', 'pokemon', 'nintendo',
        'nike', 'adidas', 'gucci', 'prada', 'netflix', 'hulu', 'amazon', 'apple',
        'nasa', 'fbi', 'cia', 'harry potter', 'warner bros', 'dc comics', 'batman',
        'superman', 'spiderman', 'iron man', 'avengers', 'barbie', 'lego',
        'nfl', 'nba', 'mlb', 'nhl', 'fifa', 'nike', 'adidas', 'puma', 'reebok',
        'spongebob', 'travis scott', 'ye ', 'kanye', 'bts', 'hayley williams',
        '5sos', 'daniel caesar', 'the neighborhood', 'the neighbourhood', 'artemis',
        'final four', 'ncaa', 'world cup', 'olympics', 'super bowl'
    ]

    mask_ip = df['query'].str.contains('|'.join(ip_list), case=False, na=False)
    ip_df = df[mask_ip].copy()
    general_df = df[~mask_ip].copy()

    return general_df, ip_df

def format_as_table(df):
    if df.empty:
        return "No new trends found for this section."

    table = "| keyword | score | why/idea |\n| --- | --- | --- |\n"
    for _, row in df.iterrows():
        kw = row['query']
        score = row['value']
        # Simple placeholder for why/idea - can be improved with more logic if needed
        idea = f"Rising search for '{kw}'. Potential design: minimal style with bold typography."
        table += f"| {kw} | {score} | {idea} |\n"
    return table

def update_trends_md(general_df, ip_df):
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    new_content = f"## {now} Update\n\n"
    new_content += "### General Merch Opportunities\n"
    new_content += format_as_table(general_df) + "\n\n"
    new_content += "### Potential IP Infringing Opportunities\n"
    new_content += format_as_table(ip_df) + "\n\n"
    new_content += "---\n\n"

    try:
        with open("trends.md", "r") as f:
            old_content = f.read()
    except FileNotFoundError:
        old_content = ""

    # Prepend new content
    with open("trends.md", "w") as f:
        f.write(new_content + old_content)

if __name__ == "__main__":
    seeds = ["tshirt", "shirt", "tank top", "merch"]
    df = fetch_trends(seeds)
    df = filter_trends(df)
    general_df, ip_df = categorize_trends(df)

    update_trends_md(general_df, ip_df)
    print("trends.md updated successfully.")
