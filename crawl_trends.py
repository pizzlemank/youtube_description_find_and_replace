import time
import pandas as pd
from pytrends.request import TrendReq
import requests
import datetime
import os
import re

IP_BLACKLIST = [
    'disney', 'marvel', 'star wars', 'nike', 'adidas', 'taylor swift', 'bts', 'michael jackson',
    'nba', 'wnba', 'nfl', 'mlb', 'nhl', 'nintendo', 'pokemon', 'harry potter', 'nasa', 'hellstar',
    'ysl', 'gucci', 'prada', 'louis vuitton', 'arsenal', 'real madrid', 'liverpool', 'man city',
    'chelsea', 'bayern', 'barcelona', 'knicks', 'lakers', 'celtics', 'warriors', 'bulls', 'amiri',
    'trapstar', 'corteiz', 'sp5der', 'minus two', 'syna world', 'harry styles', 'gracie abrams',
    'daniel caesar', 'bad bunny', 'billie eilish', 'drake', 'kanye', 'travis scott', 'bruno mars',
    'hello kitty', 'sanrio', 'nascar', 'f1', 'mercedes', 'ferrari', 'red bull', 'toy story', 'psg',
    'asap rocky', 'megan moroney', 'sean john', 'morgan wallen', 'spurs', 'rcb', 'snipes', 'asos',
    'pattie gonia', 'wingstop', 'ariana grande', 'selena gomez', 'carhartt', 'hazbin hotel',
    'digital circus', 'tadc', 'linkin park', 'bad omens', 'forrest frank', 'malcolm todd',
    'böhse onkelz', 'love island', 'eternal sunshine', 'madewell', 'anthropologie', 'glitch',
    'stevie nicks', 'beyonce', 'lilibet'
]

EXCLUDED_TERMS = [
    'meaning', 'definition', 'how to', 'why', 'iron', 'near me', 'template', 'mockup',
    'tee times', 'tee time', 'tee off', 'graphic tee', 'essential tee', 'vintage tee',
    'oversized tee', 'plain shirt', 'blank shirt', 'kaffee', 'rezepte', 'bh für',
    'bra for', 'tutorial', 'bra', 't-shirt bra', 'là gì'
]

APPAREL_TERMS = ['tshirt', 't-shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch']

def is_ip_infringing(keyword):
    """Checks if a keyword contains any blacklisted IP terms using word boundaries."""
    for term in IP_BLACKLIST:
        if re.search(rf'\b{re.escape(term)}\b', keyword, re.IGNORECASE):
            return True
    return False

def is_relevant(keyword):
    """Checks if a keyword is relevant for POD and follows long-tail criteria."""
    # Must have at least 2 words
    if len(keyword.split()) < 2:
        return False

    # Must contain at least one apparel term
    if not any(term in keyword for term in APPAREL_TERMS):
        return False

    # Must not contain excluded terms
    for term in EXCLUDED_TERMS:
        if term in keyword:
            return False

    # Exact match of seed keywords or very generic ones are boring
    if keyword.strip() in APPAREL_TERMS or keyword.strip() in ['t-shirts', 'tshirts', 'tees']:
        return False

    return True

def get_pytrends():
    """Initializes TrendReq with custom retry logic for 429 errors."""
    return TrendReq(hl='en-US', tz=360)

def fetch_rising_queries(pytrends, keyword):
    """Fetches rising related queries for a given keyword with retries."""
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            pytrends.build_payload([keyword], timeframe='now 7-d', geo='')
            related_queries = pytrends.related_queries()
            if keyword in related_queries and related_queries[keyword]['rising'] is not None:
                return related_queries[keyword]['rising']
            return pd.DataFrame()
        except Exception as e:
            if "429" in str(e) and attempt < max_retries:
                print(f"Rate limited for '{keyword}'. Retrying in 30s... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(30)
            else:
                print(f"Error fetching trends for '{keyword}': {e}")
                return pd.DataFrame()
    return pd.DataFrame()

def generate_idea(keyword):
    """Generates a simple design idea by removing apparel terms."""
    # Order by length descending to catch 'tank top' before 'top' or 'tank' if those were in APPAREL_TERMS
    # For now, just the terms we have.
    sorted_terms = sorted(['tshirt', 't-shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch', 'tshirts', 't-shirts', 'tees'], key=len, reverse=True)
    idea_base = keyword
    for term in sorted_terms:
        idea_base = re.sub(rf'\b{re.escape(term)}\b', '', idea_base, flags=re.IGNORECASE).strip()

    idea_base = re.sub(r'\s+', ' ', idea_base) # clean up double spaces
    if not idea_base:
        return "Popular apparel search, look into current aesthetic trends."
    return f"Create a design featuring '{idea_base}' targeting this niche."

def format_table(results):
    """Formats results into a Markdown table."""
    if not results:
        return "No results found for this section.\n"

    # Sort results by score descending, Breakout = 9999
    def get_score(res):
        s = res['score']
        if isinstance(s, str) and 'Breakout' in s:
            return 9999
        try:
            return int(s)
        except:
            return 0

    sorted_res = sorted(results, key=get_score, reverse=True)

    table = "| Keyword | Score | Why/Idea |\n| :--- | :--- | :--- |\n"
    for res in sorted_res:
        idea = generate_idea(res['keyword'])
        table += f"| {res['keyword']} | {res['score']} | {idea} |\n"
    return table

def main():
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    trends_file = "trends.md"

    # Check if we already updated today
    if os.path.exists(trends_file):
        with open(trends_file, 'r', encoding='utf-8') as f:
            if f"## {today}" in f.read():
                print(f"Trends for {today} already exist in {trends_file}. Skipping.")
                return

    pytrends = get_pytrends()
    seed_keywords = APPAREL_TERMS

    all_results = []
    seen_keywords = set()

    for seed in seed_keywords:
        print(f"Fetching rising queries for: {seed}")
        df = fetch_rising_queries(pytrends, seed)

        if not df.empty:
            for _, row in df.iterrows():
                kw = row['query'].lower()
                if kw not in seen_keywords and is_relevant(kw):
                    all_results.append({
                        'keyword': kw,
                        'score': row['value'],
                        'is_ip': is_ip_infringing(kw)
                    })
                    seen_keywords.add(kw)

        time.sleep(5)

    if not all_results:
        print("No new trends found today.")
        return

    general_merch = [r for r in all_results if not r['is_ip']]
    ip_infringing = [r for r in all_results if r['is_ip']]

    output = f"## {today}\n\n"
    output += "### General Merch Opportunities\n"
    output += format_table(general_merch) + "\n"
    output += "### Potential IP Infringing Opportunities\n"
    output += format_table(ip_infringing) + "\n"

    # Prepend to file
    with open(trends_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the main title
    title_match = re.search(r'^# .*\n', content)
    if title_match:
        header = title_match.group(0)
        rest = content[title_match.end():]
        new_content = header + "\n" + output + rest
    else:
        new_content = output + content

    with open(trends_file, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"Updated {trends_file} with {len(all_results)} new trends.")

if __name__ == "__main__":
    main()
