import time
import pandas as pd
from pytrends.request import TrendReq
from datetime import datetime
import os
import re

# Configuration
SEED_KEYWORDS = ['tshirt', 't-shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch']
APPAREL_TERMS = ['shirt', 'tshirt', 't-shirt', 'tank top', 'tanktop', 'tee', 'merch']
BLACKLIST = [
    'disney', 'marvel', 'star wars', 'nike', 'adidas', 'taylor swift', 'bts',
    'michael jackson', 'micheal jackson', 'nba', 'nfl', 'mlb', 'nhl',
    'nintendo', 'pokemon', 'harry potter', 'nasa', 'hellstar', 'ysl',
    'gucci', 'prada', 'louis vuitton', 'koningsdag', 'oranje', 'higgins',
    'wwe', 'kanye', 'drake', 'notre dame', 'ariana grande', 'george strait',
    'olivia dean', 'conan gray', 'man utd', 'lidl', 'm&s', 'mnet', 'amc',
    'murder drones'
]
EXCLUDE_KEYWORDS = [
    'meaning', 'definition', 'how to', 'why', 'iron', 'near me',
    'template', 'mockup', 'tee times', 'tee time', 'tee off',
    'graphic tee', 'essential tee', 'vintage tee', 'oversized tee',
    'plain shirt', 'blank shirt'
]

def get_pytrends_with_retry():
    # Simple initialization. Retry logic is in the query loop.
    return TrendReq(hl='en-US', tz=360)

def fetch_trends(pytrends, keyword):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            pytrends.build_payload([keyword], timeframe='now 7-d')
            related_queries = pytrends.related_queries()
            if keyword in related_queries:
                return related_queries[keyword]['rising']
            return None
        except Exception as e:
            if "429" in str(e):
                print(f"Rate limit hit for {keyword}. Waiting 10s...")
                time.sleep(10)
            else:
                print(f"Error fetching trends for {keyword}: {e}")
                break
    return None

def is_ip_infringing(keyword):
    k_lower = keyword.lower()
    for brand in BLACKLIST:
        if brand in k_lower:
            return True
    return False

def is_valid_opportunity(keyword):
    k_lower = keyword.lower()

    # Must be long tail (2+ words)
    if len(k_lower.split()) < 2:
        return False

    # Must contain apparel terms
    if not any(term in k_lower for term in APPAREL_TERMS):
        return False

    # Exclude common non-merch terms
    if any(ex in k_lower for ex in EXCLUDE_KEYWORDS):
        return False

    return True

def generate_idea(keyword):
    # Remove apparel terms to find the subject
    subject = keyword.lower()
    # Sort APPAREL_TERMS by length descending to replace longer phrases first
    sorted_terms = sorted(APPAREL_TERMS, key=len, reverse=True)
    for term in sorted_terms:
        subject = subject.replace(term, '')

    subject = re.sub(r'\s+', ' ', subject).strip()

    if not subject:
        return "Generic apparel design."

    return f"Design featuring '{subject.title()}' with a unique artistic style or catchphrase."

def process_trends():
    pytrends = get_pytrends_with_retry()
    all_results = []
    seen_keywords = set()

    for seed in SEED_KEYWORDS:
        print(f"Fetching trends for: {seed}")
        rising = fetch_trends(pytrends, seed)
        if rising is not None and not rising.empty:
            for index, row in rising.iterrows():
                query = row['query']
                score = row['value']

                if is_valid_opportunity(query) and query not in seen_keywords:
                    seen_keywords.add(query)
                    all_results.append({
                        'keyword': query,
                        'score': score,
                        'infringing': is_ip_infringing(query)
                    })
        time.sleep(2) # Delay between seeds

    return all_results

def format_score(score):
    if isinstance(score, str) and 'Breakout' in score:
        return 9999
    try:
        return int(score)
    except:
        return 0

def update_trends_file(results):
    today = datetime.now().strftime('%Y-%m-%d')

    # Check if we already updated today
    if os.path.exists('trends.md'):
        with open('trends.md', 'r') as f:
            content = f.read()
            if f"## Trends for {today}" in content:
                print("Trends for today already recorded.")
                return

    general = []
    infringing = []

    for res in results:
        idea = generate_idea(res['keyword'])
        line = f"| {res['keyword']} | {res['score']} | {idea} |"
        if res['infringing']:
            infringing.append(line)
        else:
            general.append(line)

    # Sort by score
    def get_sort_key(line):
        parts = line.split('|')
        if len(parts) > 2:
            return format_score(parts[2].strip())
        return 0

    general.sort(key=get_sort_key, reverse=True)
    infringing.sort(key=get_sort_key, reverse=True)

    new_content = f"## Trends for {today}\n\n"

    new_content += "### General Merch Opportunities\n"
    new_content += "| Keyword | Score | Why/Idea |\n"
    new_content += "| --- | --- | --- |\n"
    if general:
        new_content += "\n".join(general) + "\n"
    else:
        new_content += "No new general opportunities found.\n"

    new_content += "\n### Potential IP Infringing Opportunities\n"
    new_content += "| Keyword | Score | Why/Idea |\n"
    new_content += "| --- | --- | --- |\n"
    if infringing:
        new_content += "\n".join(infringing) + "\n"
    else:
        new_content += "No new infringing opportunities found.\n"

    new_content += "\n---\n\n"

    old_content = ""
    if os.path.exists('trends.md'):
        with open('trends.md', 'r') as f:
            old_content = f.read()

    with open('trends.md', 'w') as f:
        f.write(new_content + old_content)

    print(f"Successfully updated trends.md for {today}")

if __name__ == "__main__":
    results = process_trends()
    if results:
        update_trends_file(results)
    else:
        print("No rising trends found today.")
