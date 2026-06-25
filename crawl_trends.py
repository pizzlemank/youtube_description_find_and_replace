import pandas as pd
from pytrends.request import TrendReq
import time
import datetime
import os
import re

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
    'beyonce', 'lilibet', 'olivia rodrigo', 'caitlin clark', 'sabrina carpenter',
    'messi', 'ronaldo', 'spiderman', 'spider-man', 'batman', 'superman', 'fifa',
    'uefa', 'palace', 'kobe', 'cowboys', 'yankees', 'dodgers', 'dfb', 'us open',
    'olympics'
]

APPAREL_TERMS = ['shirt', 'tshirt', 't-shirt', 'tank top', 'tanktop', 'tee', 'merch']

EXCLUSION_KEYWORDS = [
    'meaning', 'definition', 'how to', 'why', 'iron', 'near me', 'template',
    'mockup', 'tee times', 'tee time', 'tee off', 'graphic tee', 'essential tee',
    'vintage tee', 'oversized tee', 'plain shirt', 'blank shirt', 'kaffee',
    'rezepte', 'bh für', 'bra for', 'tutorial', 'bra', 't-shirt bra', 'là gì'
]

def is_ip_infringing(keyword):
    keyword_lower = keyword.lower()
    for term in IP_BLACKLIST:
        if re.search(rf'\b{re.escape(term)}\b', keyword_lower):
            return True
    return False

def is_relevant(keyword):
    keyword_lower = keyword.lower()

    # Check if it has at least 2 words
    if len(keyword_lower.split()) < 2:
        return False

    # Check if it contains an apparel term
    has_apparel = any(term in keyword_lower for term in APPAREL_TERMS)
    if not has_apparel:
        return False

    # Check for exclusions
    if any(ex in keyword_lower for ex in EXCLUSION_KEYWORDS):
        return False

    # Filter out generic seed variations
    generic_seeds = ['t shirt', 't-shirts', 'tees']
    if keyword_lower in generic_seeds or keyword_lower in APPAREL_TERMS:
        return False

    return True

def fetch_trends(seed_keywords):
    pytrends = TrendReq(hl='en-US', tz=360)
    all_rising = []

    for kw in seed_keywords:
        print(f"Fetching trends for: {kw}")
        retries = 3
        while retries > 0:
            try:
                pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='', gprop='')
                related_queries = pytrends.related_queries()

                if kw in related_queries and related_queries[kw]['rising'] is not None:
                    rising_df = related_queries[kw]['rising']
                    all_rising.append(rising_df)

                time.sleep(5) # Delay to mitigate rate limiting
                break
            except Exception as e:
                if "429" in str(e):
                    print(f"Rate limited (429) for {kw}. Retrying in 30s...")
                    time.sleep(30)
                    retries -= 1
                else:
                    print(f"Error fetching {kw}: {e}")
                    break

    if not all_rising:
        return pd.DataFrame(columns=['query', 'value'])

    df = pd.concat(all_rising).drop_duplicates(subset=['query'])

    # Apply filtering
    df = df[df['query'].apply(is_relevant)]

    # Mark IP infringement
    df['is_ip'] = df['query'].apply(is_ip_infringing)

    return df

def generate_why_idea(keyword):
    # Simple logic to generate a design idea by stripping common apparel terms
    concept = keyword.lower()
    # Replace plurals first to avoid leaving 's'
    for term in ['tshirts', 't-shirts', 'tank tops', 'tanktops']:
        concept = concept.replace(term, '')
    for term in APPAREL_TERMS:
        concept = concept.replace(term, '')

    concept = concept.strip()
    # Clean up multiple spaces
    concept = re.sub(' +', ' ', concept)

    if not concept:
        return "Trending apparel search; create a unique design around this niche."

    return f"Trending search for '{concept}'. Design idea: A creative graphic or typography focused on '{concept}' that appeals to this audience."

def update_trends_md(df):
    if df.empty:
        print("No new trends found.")
        return

    today = datetime.date.today().strftime("%Y-%m-%d")

    # Sort by score (value), treating 'Breakout' as 9999
    def get_score(val):
        if val == 'Breakout':
            return 9999
        try:
            return int(val)
        except:
            return 0

    df['score_num'] = df['value'].apply(get_score)
    df = df.sort_values(by='score_num', ascending=False)

    # Prepare markdown sections
    general_df = df[~df['is_ip']]
    ip_df = df[df['is_ip']]

    new_content = f"## {today}\n\n"

    if not general_df.empty:
        new_content += "### General Merch Opportunities\n\n"
        new_content += "| keyword | score | why you think is an opportunity, idea for design, or what the internet shopping is already doing |\n"
        new_content += "| :--- | :--- | :--- |\n"
        for _, row in general_df.iterrows():
            why = generate_why_idea(row['query'])
            new_content += f"| {row['query']} | {row['value']} | {why} |\n"
        new_content += "\n"

    if not ip_df.empty:
        new_content += "### Potential IP Infringing Opportunities\n\n"
        new_content += "| keyword | score | why you think is an opportunity, idea for design, or what the internet shopping is already doing |\n"
        new_content += "| :--- | :--- | :--- |\n"
        for _, row in ip_df.iterrows():
            why = generate_why_idea(row['query'])
            new_content += f"| {row['query']} | {row['value']} | {why} |\n"
        new_content += "\n"

    # Read existing content
    if os.path.exists("trends.md"):
        with open("trends.md", "r", encoding="utf-8") as f:
            lines = f.readlines()
    else:
        lines = ["# Google Trends Merch Opportunities\n"]

    # Check if we already updated today to avoid duplicates
    if any(f"## {today}" in line for line in lines):
        print(f"Already updated trends.md for {today}. Skipping.")
        return

    # Prepend after the main header
    header = lines[0]
    rest = "".join(lines[1:])

    final_content = header + "\n" + new_content + rest

    with open("trends.md", "w", encoding="utf-8") as f:
        f.write(final_content)
    print(f"Successfully updated trends.md with {len(df)} new trends.")

if __name__ == "__main__":
    seeds = ['tshirt', 't-shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch']
    trends = fetch_trends(seeds)
    update_trends_md(trends)
