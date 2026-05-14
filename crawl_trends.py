import time
import datetime
import os
import pandas as pd
from pytrends.request import TrendReq

def fetch_trends(keywords):
    pytrends = TrendReq(hl='en-US', tz=360)
    all_rising = []

    for kw in keywords:
        print(f"Fetching trends for: {kw}")
        retries = 3
        while retries > 0:
            try:
                pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='US')
                related = pytrends.related_queries()
                if kw in related and related[kw]['rising'] is not None:
                    rising = related[kw]['rising']
                    all_rising.append(rising)
                time.sleep(5) # Increased delay
                break
            except Exception as e:
                print(f"Error fetching {kw}: {e}. Retrying...")
                retries -= 1
                time.sleep(10)

    if not all_rising:
        return pd.DataFrame()

    df = pd.concat(all_rising).drop_duplicates(subset=['query'])
    return df

def is_long_tail_apparel(query):
    apparel_terms = ['shirt', 'tshirt', 't-shirt', 'tank top', 'tanktop', 'tee', 'merch']
    excluded_terms = [
        'meaning', 'definition', 'how to', 'why', 'iron', 'near me',
        'template', 'mockup', 'tee times', 'tee time', 'tee off',
        'graphic tee', 'essential tee', 'vintage tee', 'oversized tee',
        'plain shirt', 'blank shirt', 'là gì'
    ]
    query_lower = query.lower()

    if any(term in query_lower for term in excluded_terms):
        return False

    words = query_lower.split()
    if len(words) < 2:
        return False
    return any(term in query_lower for term in apparel_terms)

BRAND_BLACKLIST = [
    'disney', 'marvel', 'star wars', 'nike', 'adidas', 'taylor swift', 'bts',
    'michael jackson', 'nba', 'wnba', 'nfl', 'mlb', 'nhl', 'nintendo', 'pokemon',
    'harry potter', 'nasa', 'hellstar', 'ysl', 'gucci', 'prada', 'louis vuitton',
    'koningsdag', 'oranje', 'higgins', 'wwe', 'kanye', 'drake', 'notre dame',
    'ariana grande', 'george strait', 'olivia dean', 'conan gray', 'man utd',
    'lidl', 'm&s', 'mnet', 'amc', 'murder drones', 'luke combs', 'ohio state',
    'ufc', 'f1', 'nascar', 'sanrio', 'hello kitty', 'stussy', 'mclaren',
    'deftones', 'cleetus mcfarland', 'the neighbourhood', 'bring me the horizon',
    'khan asadi', 'lyrebird', 'anthropologie', 'carson hocevar', 'rihanna',
    'morgan wallen', 'valorant', 'kentucky derby', 'victoria beckham',
    'kimi antonelli', 'no doubt', 'bad omens', 'good mythical morning',
    'riley green', 'ella langley', 'candace owens', 'g59', 'grey59', 'greyfivenine',
    'of the trees'
]

def is_ip_infringing(query):
    query_lower = query.lower()
    return any(brand in query_lower for brand in BRAND_BLACKLIST)

def generate_idea(query):
    query_clean = query.lower()
    # Replace long terms first to avoid partial replacement (e.g. 't-shirt' before 'shirt')
    for term in ['t-shirt', 'tshirt', 't shirt', 'tank top', 'tanktop', 'shirt', 'tee', 'merch']:
        query_clean = query_clean.replace(term, '').strip()

    query_clean = " ".join(query_clean.split())
    if not query_clean:
        return "Generic design", "N/A"

    idea = f"Design featuring '{query_clean}' with relevant graphics."
    why = f"Rising search interest for '{query}' indicates demand for this specific concept."
    return idea, why

def update_trends_file(df):
    if df.empty:
        print("No new trends found.")
        return

    today = datetime.date.today().strftime("%Y-%m-%d")

    general_merch = []
    ip_infringing = []

    # Sort by value before processing
    if not df.empty:
        def convert_score(x):
            if isinstance(x, str):
                if x == 'Breakout': return 9999
                try: return int(x)
                except: return 0
            # Some pandas types might need handling
            try: return int(x)
            except: return 0

        df['sort_val'] = df['value'].apply(convert_score)
        df = df.sort_values(by='sort_val', ascending=False)

    for _, row in df.iterrows():
        query = row['query']
        score = row['value']

        if not is_long_tail_apparel(query):
            continue

        idea, why = generate_idea(query)
        entry = f"| {query} | {score} | {why} Idea: {idea} |"

        if is_ip_infringing(query):
            ip_infringing.append(entry)
        else:
            general_merch.append(entry)

    if not general_merch and not ip_infringing:
        print("No relevant apparel trends found after filtering.")
        return

    new_content = f"\n## {today}\n"

    if general_merch:
        new_content += "\n### General Merch Opportunities\n"
        new_content += "| Keyword | Score | Why/Idea |\n"
        new_content += "| --- | --- | --- |\n"
        new_content += "\n".join(general_merch) + "\n"

    if ip_infringing:
        new_content += "\n### Potential IP Infringing Opportunities\n"
        new_content += "| Keyword | Score | Why/Idea |\n"
        new_content += "| --- | --- | --- |\n"
        new_content += "\n".join(ip_infringing) + "\n"

    try:
        with open("trends.md", "r") as f:
            old_content = f.read()
    except FileNotFoundError:
        old_content = "# Google Trends - POD Merch Opportunities\n"

    # Avoid duplicate updates for the same day
    if f"## {today}" in old_content:
        print(f"Trends for {today} already exist in trends.md. Skipping.")
        return

    # Prepend new content after the title
    title_end = old_content.find("\n") + 1
    updated_content = old_content[:title_end] + new_content + old_content[title_end:]

    with open("trends.md", "w") as f:
        f.write(updated_content)
    print(f"Updated trends.md with {len(general_merch) + len(ip_infringing)} new entries.")

if __name__ == "__main__":
    seed_keywords = ['tshirt', 't-shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch']
    trends_df = fetch_trends(seed_keywords)
    update_trends_file(trends_df)
