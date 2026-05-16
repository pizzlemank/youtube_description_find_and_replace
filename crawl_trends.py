import pandas as pd
from pytrends.request import TrendReq
import time
import datetime
import os
import re

# Configuration
KEYWORDS = ['tshirt', 't-shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch']
TIMEFRAME = 'now 7-d'  # Last 7 days
TRENDS_FILE = 'trends.md'

# IP Blacklist - common brands and characters to flag
IP_BLACKLIST = [
    'disney', 'marvel', 'star wars', 'nike', 'adidas', 'taylor swift', 'bts', 'michael jackson',
    'nba', 'wnba', 'nfl', 'mlb', 'nhl', 'nintendo', 'pokemon', 'harry potter', 'nasa',
    'hellstar', 'ysl', 'gucci', 'prada', 'louis vuitton', 'koningsdag', 'oranje', 'higgins',
    'wwe', 'kanye', 'drake', 'notre dame', 'ariana grande', 'george strait', 'olivia dean',
    'conan gray', 'man utd', 'lidl', 'm&s', 'mnet', 'amc', 'murder drones', 'luke combs',
    'ohio state', 'ufc', 'f1', 'nascar', 'sanrio', 'hello kitty', 'stussy', 'mclaren',
    'deftones', 'cleetus mfarland', 'the neighbourhood', 'bring me the horizon', 'khan asadi',
    'lyrebird', 'anthropologie', 'carson hocevar', 'rihanna', 'morgan wallen', 'valorant',
    'kentucky derby', 'victoria beckham', 'kimi antonelli', 'no doubt', 'bad omens',
    'good mythical morning', 'riley green', 'ella langley', 'candace owens', 'g59', 'grey59',
    'greyfivenine', 'of the trees'
]

# Irrelevant terms to filter out
FILTER_OUT = [
    'meaning', 'definition', 'how to', 'why', 'iron', 'near me', 'template', 'mockup',
    'tee times', 'tee time', 'tee off', 'graphic tee', 'essential tee', 'vintage tee',
    'oversized tee', 'plain shirt', 'blank shirt', 'là gì'
]

def get_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    all_rising = []

    for kw in KEYWORDS:
        print(f"Fetching trends for: {kw}")
        try:
            # Build payload
            # We retry because Google Trends API is very sensitive to rate limits
            max_retries = 3
            related_queries = None
            for i in range(max_retries):
                try:
                    pytrends.build_payload([kw], cat=0, timeframe=TIMEFRAME, geo='')
                    related_queries = pytrends.related_queries()
                    break
                except Exception as e:
                    if "429" in str(e):
                        if i == max_retries - 1: raise e
                        print(f"Rate limited (429). Waiting longer... (Retry {i+1})")
                        time.sleep(30 * (i + 1))
                        continue
                    else:
                        raise e

            if kw in related_queries:
                rising = related_queries[kw]['rising']
                if rising is not None and not rising.empty:
                    all_rising.append(rising)

            # Small sleep to avoid aggressive rate limiting
            time.sleep(5)

        except Exception as e:
            print(f"Error fetching trends for {kw}: {e}")

    if not all_rising:
        return pd.DataFrame()

    return pd.concat(all_rising).drop_duplicates(subset=['query'])

def is_long_tail(query):
    # Check if query has at least 2 words
    return len(query.split()) >= 2

def contains_apparel_term(query):
    apparel_terms = ['shirt', 'tshirt', 't-shirt', 'tank top', 'tanktop', 'tee', 'merch']
    return any(term in query.lower() for term in apparel_terms)

def is_ip_infringing(query):
    query_lower = query.lower()
    return any(brand in query_lower for brand in IP_BLACKLIST)

def is_filtered_out(query):
    query_lower = query.lower()
    return any(term in query_lower for term in FILTER_OUT)

def generate_idea(query):
    # Simple logic to generate a design idea from the keyword
    clean_query = query.lower()
    # Remove the shirt/tshirt part to get the core concept
    core = clean_query
    for term in ['t-shirt', 'tshirt', 't shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch']:
        core = core.replace(term, '')

    core = core.strip()
    core = re.sub(' +', ' ', core) # remove double spaces

    if not core:
        return "Generic design based on the trending term."

    return f"Design focused on '{core.title()}'. Possible typographic or illustrative style targeting fans of this trend."

def process_trends(df):
    if df.empty:
        return [], []

    # Sort by value (Score) - Handle 'Breakout' as 9999
    # Ensure value is numeric for sorting
    def convert_value(v):
        if isinstance(v, str) and v == 'Breakout':
            return 9999
        try:
            return int(v)
        except (ValueError, TypeError):
            return 0

    df['score'] = df['value'].apply(convert_value)
    df = df.sort_values(by='score', ascending=False)

    general_opportunities = []
    ip_infringing = []

    seen_queries = set()

    for _, row in df.iterrows():
        query = row['query']
        score = row['value'] # Keep original string (e.g. 'Breakout')

        if query in seen_queries:
            continue
        seen_queries.add(query)

        if not is_long_tail(query) or not contains_apparel_term(query):
            continue

        if is_filtered_out(query):
            continue

        idea = generate_idea(query)
        entry = {
            'keyword': query,
            'score': score,
            'idea': idea
        }

        if is_ip_infringing(query):
            ip_infringing.append(entry)
        else:
            general_opportunities.append(entry)

    return general_opportunities, ip_infringing

def update_trends_md(general, ip):
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    new_content = f"## {today}\n\n"

    new_content += "### General Merch Opportunities\n"
    new_content += "| Keyword | Score | Why/Idea |\n"
    new_content += "| :--- | :--- | :--- |\n"
    if not general:
        new_content += "| No significant general trends found today | - | - |\n"
    else:
        for item in general:
            new_content += f"| {item['keyword']} | {item['score']} | {item['idea']} |\n"

    new_content += "\n### Potential IP Infringing Opportunities\n"
    new_content += "| Keyword | Score | Why/Idea |\n"
    new_content += "| :--- | :--- | :--- |\n"
    if not ip:
        new_content += "| No significant IP trends found today | - | - |\n"
    else:
        for item in ip:
            new_content += f"| {item['keyword']} | {item['score']} | {item['idea']} |\n"

    new_content += "\n---\n\n"

    # Read existing content
    existing_content = ""
    if os.path.exists(TRENDS_FILE):
        # Check if we already updated today to avoid duplicates if run multiple times
        with open(TRENDS_FILE, 'r') as f:
            existing_content = f.read()
            if f"## {today}" in existing_content:
                print(f"Trends for {today} already exist in {TRENDS_FILE}. Skipping update.")
                return

    # Prepend new content
    with open(TRENDS_FILE, 'w') as f:
        f.write("# Google Trends Merch Opportunities\n\n" + new_content + existing_content.replace("# Google Trends Merch Opportunities\n\n", ""))

if __name__ == "__main__":
    print("Starting Trends Crawl...")
    trends_df = get_trends()
    if not trends_df.empty:
        general, ip = process_trends(trends_df)
        update_trends_md(general, ip)
        print("Trends updated successfully.")
    else:
        print("No trends found.")
