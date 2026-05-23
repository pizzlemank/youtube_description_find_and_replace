from pytrends.request import TrendReq
import pandas as pd
import datetime
import os
import time
import sys

def crawl():
    # hl='en-US', tz=360 (CST)
    pytrends = TrendReq(hl='en-US', tz=360)

    keywords = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]
    all_rising = []

    # Enhanced brand/IP blacklist
    brands = [
        'disney', 'marvel', 'star wars', 'nike', 'adidas', 'taylor swift', 'bts', 'michael jackson',
        'nba', 'wnba', 'nfl', 'mlb', 'nhl', 'nintendo', 'pokemon', 'harry potter', 'nasa',
        'hellstar', 'ysl', 'gucci', 'prada', 'louis vuitton', 'koningsdag', 'oranje', 'higgins',
        'wwe', 'kanye', 'drake', 'notre dame', 'ariana grande', 'george strait', 'olivia dean',
        'conan gray', 'man utd', 'lidl', 'm&s', 'mnet', 'amc', 'murder drones', 'luke combs',
        'ohio state', 'ufc', 'f1', 'nascar', 'sanrio', 'hello kitty', 'stussy', 'mclaren',
        'deftones', 'cleetus mcfarland', 'the neighbourhood', 'bring me the horizon',
        'khan asadi', 'lyrebird', 'anthropologie', 'carson hocevar', 'rihanna', 'morgan wallen',
        'valorant', 'kentucky derby', 'victoria beckham', 'kimi antonelli', 'no doubt',
        'bad omens', 'good mythical morning', 'riley green', 'ella langley', 'candace owens',
        'g59', 'grey59', 'greyfivenine', 'of the trees', 'harry styles', 'gracie abrams',
        'daniel caesar', 'jul', 'rcb', 'pga championship', 'edc', 'suzan en freek',
        'kaulitz hills', 'qsmp', 'ovo', 'arsenal', 'real madrid', 'liverpool', 'man city',
        'chelsea', 'bayern', 'barcelona', 'amiri', 'trapstar', 'corteiz', 'sp5der', 'minus two',
        'syna world'
    ]

    # Generic or irrelevant terms to skip entirely
    ignore_terms = [
        'meaning', 'definition', 'how to', 'why', 'iron', 'near me', 'template', 'mockup',
        'tee times', 'tee time', 'tee off', 'graphic tee', 'essential tee', 'vintage tee',
        'oversized tee', 'plain shirt', 'blank shirt', 'kaffee', 'rezepte', 'bh für', 'bra for',
        'tutorial', 'là gì'
    ]

    for kw in keywords:
        print(f"Fetching trends for '{kw}'...")
        try:
            # Using a retry mechanism for rate limiting (429)
            retry_count = 0
            while retry_count < 3:
                try:
                    pytrends.build_payload([kw], timeframe='now 7-d')
                    related_queries = pytrends.related_queries()
                    break
                except Exception as e:
                    if "429" in str(e):
                        print("Rate limited. Waiting 60s...")
                        time.sleep(60)
                        retry_count += 1
                    else:
                        raise e

            rising = related_queries.get(kw, {}).get('rising')
            if rising is not None and not rising.empty:
                all_rising.append(rising)

            time.sleep(5) # Delay to be respectful
        except Exception as e:
            print(f"Error fetching {kw}: {e}")

    if not all_rising:
        print("No rising trends found.")
        return

    df = pd.concat(all_rising).drop_duplicates(subset='query')

    # Filter for long tail (2+ words)
    df = df[df['query'].str.split().str.len() >= 2]

    # Filter out exact matches or very generic matches of our seeds
    seeds_extended = keywords + ['t shirt', 't-shirts', 'tshirts', 'shirts', 'tees']
    df = df[~df['query'].str.lower().isin(seeds_extended)]

    # Filter out ignored terms
    def should_ignore(query):
        query_l = query.lower()
        for term in ignore_terms:
            if term in query_l:
                return True
        return False

    df = df[~df['query'].apply(should_ignore)]

    # Check for IP
    def check_ip(query):
        query_l = query.lower()
        for brand in brands:
            if brand in query_l:
                return True
        return False

    df['is_ip'] = df['query'].apply(check_ip)

    # Generate Ideas
    def generate_idea(row):
        query = row['query']
        query_l = query.lower()

        if "merch" in query_l:
            return f"Fan-driven interest in '{query}'. Check if it's a creator or a niche event."

        # Identify the core subject by removing common apparel terms
        subject = query
        for term in ['t-shirt', 'tshirt', 't shirt', 'shirt', 'tank top', 'tanktop', 'tee']:
            if term in subject.lower():
                # Replace only the first occurrence to avoid messing up too much
                import re
                subject = re.compile(re.escape(term), re.IGNORECASE).sub('', subject).strip()

        subject = subject.replace('  ', ' ').strip()

        if subject:
            return f"Design concept: Focus on '{subject}'. Rising interest in this specific apparel niche."
        else:
            return f"General interest in {query}. Research specific sub-niches."

    df['idea'] = df.apply(generate_idea, axis=1)

    # Sort
    def score_to_int(val):
        if val == 'Breakout':
            return 9999
        try:
            return int(val)
        except:
            return 0

    df['score_val'] = df['value'].apply(score_to_int)
    df = df.sort_values(by='score_val', ascending=False)

    today = datetime.date.today().strftime("%Y-%m-%d")
    header = f"## {today}"

    # Avoid duplicate for same day
    existing_content = ""
    if os.path.exists("trends.md"):
        with open("trends.md", "r") as f:
            existing_content = f.read()

    if header in existing_content:
        print(f"Trends for {today} already exist in trends.md. Skipping append.")
        return

    # Build Content
    content = f"{header}\n\n"

    # General
    general_df = df[~df['is_ip']]
    if not general_df.empty:
        content += "### General Merch Opportunities\n\n"
        content += "| Keyword | Score | Why/Idea |\n"
        content += "|---------|-------|----------|\n"
        for _, row in general_df.iterrows():
            content += f"| {row['query']} | {row['value']} | {row['idea']} |\n"
        content += "\n"

    # IP Infringing
    ip_df = df[df['is_ip']]
    if not ip_df.empty:
        content += "### Potential IP Infringing Opportunities\n\n"
        content += "| Keyword | Score | Why/Idea |\n"
        content += "|---------|-------|----------|\n"
        for _, row in ip_df.iterrows():
            content += f"| {row['query']} | {row['value']} | {row['idea']} |\n"
        content += "\n"

    with open("trends.md", "w") as f:
        f.write(content + existing_content)

    print(f"Successfully updated trends.md with data for {today}.")

if __name__ == "__main__":
    crawl()
