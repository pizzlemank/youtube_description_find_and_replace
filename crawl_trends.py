import pandas as pd
from pytrends.request import TrendReq
import time
import datetime
import os
import re

# Configuration
SEED_KEYWORDS = ['tshirt', 't-shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch']
TIMEFRAME = 'now 7-d'
TRENDS_FILE = 'trends.md'

# IP Blacklist terms
IP_BLACKLIST = [
    'Disney', 'Marvel', 'Star Wars', 'Nike', 'Adidas', 'Taylor Swift', 'BTS', 'Michael Jackson',
    'NBA', 'WNBA', 'NFL', 'MLB', 'NHL', 'Nintendo', 'Pokemon', 'Harry Potter', 'NASA',
    'Hellstar', 'YSL', 'Gucci', 'Prada', 'Louis Vuitton', 'Arsenal', 'Real Madrid',
    'Liverpool', 'Man City', 'Chelsea', 'Bayern', 'Barcelona', 'Knicks', 'Lakers',
    'Celtics', 'Warriors', 'Bulls', 'Amiri', 'Trapstar', 'Corteiz', 'Sp5der', 'Minus Two',
    'Syna World', 'Harry Styles', 'Gracie Abrams', 'Daniel Caesar', 'Bad Bunny',
    'Billie Eilish', 'Drake', 'Kanye', 'Travis Scott', 'Bruno Mars', 'Hello Kitty',
    'Sanrio', 'NASCAR', 'F1', 'Mercedes', 'Ferrari', 'Red Bull', 'Toy Story', 'PSG',
    'ASAP Rocky', 'Megan Moroney', 'Sean John', 'Morgan Wallen', 'Spurs', 'RCB',
    'Snipes', 'ASOS', 'Pattie Gonia', 'Wingstop', 'Ariana Grande', 'Selena Gomez',
    'Carhartt', 'Hazbin Hotel', 'Digital Circus', 'TADC', 'Linkin Park', 'Bad Omens',
    'Forrest Frank', 'Malcolm Todd', 'Böhse Onkelz', 'Love Island', 'Eternal Sunshine',
    'Madewell', 'Anthropologie', 'Glitch', 'Stevie Nicks', 'Beyonce', 'Lilibet'
]

# Irrelevant or non-commercial terms to filter out
EXCLUDE_TERMS = [
    'meaning', 'definition', 'how to', 'why', 'iron', 'near me', 'template', 'mockup',
    'tee times', 'tee time', 'tee off', 'graphic tee', 'essential tee', 'vintage tee',
    'oversized tee', 'plain shirt', 'blank shirt', 'kaffee', 'rezepte', 'bh für',
    'bra for', 'tutorial', 'là gì', 't-shirt bra', 't shirt bra'
]

APPAREL_TERMS = [
    'tshirt', 't-shirt', 't shirts', 't shirt', 'tshirts', 'tank top', 'tanktop', 'shirt', 'tee', 'merch'
]

def is_ip_infringing(keyword):
    for term in IP_BLACKLIST:
        if re.search(rf'\b{re.escape(term)}\b', keyword, re.IGNORECASE):
            return True
    return False

def generate_idea(keyword):
    # Simple logic to generate an idea by removing apparel terms and describing it as a design concept
    concept = keyword.lower()
    # Sort APPAREL_TERMS by length descending to replace longer ones first
    for term in sorted(APPAREL_TERMS, key=len, reverse=True):
        concept = concept.replace(term, '')

    concept = concept.strip()
    # Clean up double spaces
    concept = re.sub(r'\s+', ' ', concept)

    if not concept:
        return "Generic apparel search, check for specific graphic styles."

    return f"Design featuring '{concept.title()}'. This is a trending niche topic. Explore aesthetic graphics or typography related to this concept."

def fetch_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    all_results = []
    seen_keywords = set()

    for kw in SEED_KEYWORDS:
        print(f"Fetching trends for: {kw}")
        try:
            # Retry mechanism for 429 errors
            for attempt in range(3):
                try:
                    pytrends.build_payload([kw], timeframe=TIMEFRAME)
                    related_queries = pytrends.related_queries()
                    break
                except Exception as e:
                    if "429" in str(e) and attempt < 2:
                        print("Rate limited. Sleeping for 30 seconds...")
                        time.sleep(30)
                    else:
                        raise e

            if kw in related_queries and related_queries[kw]['rising'] is not None:
                rising = related_queries[kw]['rising']
                for index, row in rising.iterrows():
                    query = row['query']
                    score = row['value']

                    # Filter: long tail (2+ words)
                    if len(query.split()) < 2:
                        continue

                    # Filter: must contain an apparel term
                    if not any(term in query.lower() for term in APPAREL_TERMS):
                        continue

                    # Filter: exclude irrelevant terms
                    if any(term in query.lower() for term in EXCLUDE_TERMS):
                        continue

                    # Filter: exclude exact/generic matches of seed keywords
                    if query.lower().strip() in [s.lower() for s in SEED_KEYWORDS] or query.lower().strip() in ['t shirts', 't-shirts', 'tees']:
                        continue

                    if query not in seen_keywords:
                        all_results.append({
                            'keyword': query,
                            'score': score,
                            'is_ip': is_ip_infringing(query)
                        })
                        seen_keywords.add(query)

            # Delay to avoid rate limiting
            time.sleep(5)

        except Exception as e:
            print(f"Error fetching {kw}: {e}")

    return all_results

def update_trends_md(results):
    if not results:
        print("No new trends found.")
        return

    today = datetime.date.today().strftime('%Y-%m-%d')

    # Check if we already have entries for today
    if os.path.exists(TRENDS_FILE):
        with open(TRENDS_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            if f"## {today}" in content:
                print(f"Trends for {today} already exist in {TRENDS_FILE}. Skipping update.")
                return

    # Sort by score descending (treating 'Breakout' as 9999)
    def get_score(res):
        s = res['score']
        if isinstance(s, str) and s.lower() == 'breakout':
            return 9999
        try:
            return int(s)
        except:
            return 0

    results.sort(key=get_score, reverse=True)

    general_merch = [r for r in results if not r['is_ip']]
    ip_infringing = [r for r in results if r['is_ip']]

    new_section = f"## {today}\n\n"

    if general_merch:
        new_section += "### General Merch Opportunities\n"
        new_section += "| Keyword | Score | Why/Idea |\n"
        new_section += "| :--- | :--- | :--- |\n"
        for r in general_merch:
            idea = generate_idea(r['keyword'])
            new_section += f"| {r['keyword']} | {r['score']} | {idea} |\n"
        new_section += "\n"

    if ip_infringing:
        new_section += "### Potential IP Infringing Opportunities\n"
        new_section += "| Keyword | Score | Why/Idea |\n"
        new_section += "| :--- | :--- | :--- |\n"
        for r in ip_infringing:
            idea = generate_idea(r['keyword'])
            new_section += f"| {r['keyword']} | {r['score']} | **Warning: Potential IP Infringement.** {idea} |\n"
        new_section += "\n"

    if os.path.exists(TRENDS_FILE):
        with open(TRENDS_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Find the title or first header to prepend after it
        title_index = 0
        for i, line in enumerate(lines):
            if line.startswith('# '):
                title_index = i + 1
                break

        updated_content = "".join(lines[:title_index]) + "\n" + new_section + "".join(lines[title_index:])
    else:
        updated_content = "# Google Trends Merch Opportunities\n\n" + new_section

    with open(TRENDS_FILE, 'w', encoding='utf-8') as f:
        f.write(updated_content)

    print(f"Updated {TRENDS_FILE} with {len(results)} new trends.")

if __name__ == "__main__":
    trends = fetch_trends()
    update_trends_md(trends)
