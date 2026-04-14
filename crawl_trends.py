import pandas as pd
from pytrends.request import TrendReq
import time
import datetime
import os
import re

BRAND_BLACKLIST = [
    'disney', 'marvel', 'nike', 'adidas', 'star wars', 'pokemon', 'nintendo',
    'netflix', 'harry potter', 'lego', 'barbie', 'mickey mouse', 'minnie mouse',
    'superman', 'batman', 'spider-man', 'iron man', 'avengers', 'frozen',
    'fortnite', 'minecraft', 'roblox', 'nasa', 'national geographic',
    'nba', 'nfl', 'mlb', 'nhl', 'taylor swift', 'beyonce', 'bieber', 'drake',
    'harry styles', 'kanye', 'trump', 'biden', 'obama', 'michael jackson',
    'elvis', 'beatles', 'rolling stones', 'metallica', 'pink floyd'
]

def is_ip_infringement(query):
    query_lower = query.lower()
    for brand in BRAND_BLACKLIST:
        if re.search(rf'\b{brand}\b', query_lower):
            return True
    return False

def get_trends():
    pytrends = TrendReq(hl='en-US', tz=360)

    seed_keywords = ['tshirt', 'shirt', 'tank top', 'merch']
    all_rising_queries = []

    for kw in seed_keywords:
        print(f"Fetching trends for: {kw}")
        retries = 3
        while retries > 0:
            try:
                pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='', gprop='')
                related_queries = pytrends.related_queries()

                if kw in related_queries:
                    rising = related_queries[kw]['rising']
                    if rising is not None:
                        all_rising_queries.append(rising)
                break # Success
            except Exception as e:
                print(f"Error fetching {kw}: {e}")
                if "429" in str(e):
                    print("Rate limited. Sleeping for 10s...")
                    time.sleep(10)
                    retries -= 1
                else:
                    break

        # Sleep to avoid rate limiting
        time.sleep(2)

    if not all_rising_queries:
        return pd.DataFrame()

    df = pd.concat(all_rising_queries).drop_duplicates(subset='query')

    # Filter for long tail apparel keywords
    # Criteria: contains one of the seed keyword types but has more than one word
    apparel_terms = ['shirt', 'tshirt', 't-shirt', 'tanktop', 'tank top', 'merch', 'tee']

    def is_relevant(query):
        query_lower = query.lower()
        has_apparel = any(term in query_lower for term in apparel_terms)
        is_long_tail = len(query.split()) >= 2

        # Exclude generic or irrelevant searches
        exclude_terms = ['meaning', 'definition', 'how to', 'why', 'iron', 'near me', 'template', 'mockup']
        is_not_excluded = not any(term in query_lower for term in exclude_terms)

        return has_apparel and is_long_tail and is_not_excluded

    df = df[df['query'].apply(is_relevant)]

    # Identify IP infringement
    df['is_ip'] = df['query'].apply(is_ip_infringement)

    return df

def generate_why(query):
    query_lower = query.lower()
    if 'shirt' in query_lower or 'tshirt' in query_lower or 'tee' in query_lower:
        item = "t-shirt"
    elif 'tank' in query_lower:
        item = "tank top"
    else:
        item = "merch"

    keyword_topic = query_lower
    # Replace terms from longest to shortest to avoid partial replacements (like 't' from 'tshirt')
    for term in sorted(['shirt', 'tshirt', 't-shirt', 'tanktop', 'tank top', 'merch', 'tee'], key=len, reverse=True):
        keyword_topic = keyword_topic.replace(term, '').strip()

    return f"Rising interest in {query}. Design idea: create a unique, stylized graphic centered around '{keyword_topic}' that appeals to this niche."

def update_markdown(df):
    if df.empty:
        print("No new trends to update.")
        return

    today = datetime.date.today().strftime("%Y-%m-%d")

    # Check if we already updated today to avoid duplicates
    if os.path.exists('trends.md'):
        with open('trends.md', 'r') as f:
            content = f.read()
            if f"## {today}" in content:
                print(f"Already updated for {today}.")
                return
    else:
        content = ""

    new_content = f"## {today}\n\n"

    # General Opportunities
    general_df = df[~df['is_ip']]
    if not general_df.empty:
        new_content += "### General Merch Opportunities\n\n"
        new_content += "| Keyword | Score | Why / Idea |\n"
        new_content += "| :--- | :--- | :--- |\n"
        for _, row in general_df.sort_values(by='value', ascending=False).iterrows():
            why = generate_why(row['query'])
            # Google Trends sometimes uses 'Breakout' as a string or large number
            score = row['value']
            if score == 999999 or score > 10000: score = "Breakout"
            new_content += f"| {row['query']} | {score} | {why} |\n"
        new_content += "\n"

    # IP Infringing Opportunities
    ip_df = df[df['is_ip']]
    if not ip_df.empty:
        new_content += "### Potential IP Infringing Opportunities\n\n"
        new_content += "| Keyword | Score | Why / Idea |\n"
        new_content += "| :--- | :--- | :--- |\n"
        for _, row in ip_df.sort_values(by='value', ascending=False).iterrows():
            why = generate_why(row['query'])
            score = row['value']
            if score == 999999 or score > 10000: score = "Breakout"
            new_content += f"| {row['query']} | {score} | {why} |\n"
        new_content += "\n"

    # Prepend to existing content
    with open('trends.md', 'w') as f:
        f.write(new_content + content)

if __name__ == "__main__":
    df = get_trends()
    if not df.empty:
        # Handle 'Breakout' scores by assigning a high number for sorting
        df['value'] = df['value'].apply(lambda x: 999999 if x == 'Breakout' or (isinstance(x, str) and 'Breakout' in x) else x)
        update_markdown(df)
        print("trends.md updated successfully.")
    else:
        print("No trends found.")
