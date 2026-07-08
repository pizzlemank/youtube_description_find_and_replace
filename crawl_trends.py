import pandas as pd
from pytrends.request import TrendReq
import time
import datetime
import os
import re

# Configuration
KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]
TIMEFRAME = 'now 7-d'
TRENDS_FILE = "trends.md"

IP_BLACKLIST = [
    "Disney", "Marvel", "Star Wars", "Nike", "Adidas", "Taylor Swift", "BTS", "Michael Jackson",
    "NBA", "WNBA", "NFL", "MLB", "NHL", "Nintendo", "Pokemon", "Harry Potter", "NASA", "Hellstar",
    "YSL", "Gucci", "Prada", "Louis Vuitton", "Arsenal", "Real Madrid", "Liverpool", "Man City",
    "Chelsea", "Bayern", "Barcelona", "Knicks", "Lakers", "Celtics", "Warriors", "Bulls", "Amiri",
    "Trapstar", "Corteiz", "Sp5der", "Minus Two", "Syna World", "Harry Styles", "Gracie Abrams",
    "Daniel Caesar", "Bad Bunny", "Billie Eilish", "Drake", "Kanye", "Travis Scott", "Bruno Mars",
    "Hello Kitty", "Sanrio", "NASCAR", "f1", "Mercedes", "Ferrari", "Red Bull", "Toy Story", "PSG",
    "ASAP Rocky", "Megan Moroney", "Sean John", "Morgan Wallen", "Spurs", "RCB", "Snipes", "ASOS",
    "Pattie Gonia", "Wingstop", "Ariana Grande", "selena gomez", "Carhartt", "Hazbin Hotel",
    "Digital Circus", "TADC", "Linkin Park", "Bad Omens", "Forrest Frank", "Malcolm Todd",
    "Böhse Onkelz", "Love Island", "Eternal Sunshine", "Madewell", "Anthropologie", "Glitch",
    "Stevie Nicks", "Beyonce", "Lilibet", "Olivia Rodrigo", "Caitlin Clark", "Sabrina Carpenter",
    "Messi", "Ronaldo", "Spiderman", "Spider-man", "Batman", "Superman", "FIFA", "UEFA", "Palace",
    "Kobe", "Cowboys", "Yankees", "Dodgers", "DFB", "US Open", "Olympics", "Cecil", "H&M",
    "Levi's", "Zara", "Gap", "Old Navy", "Lululemon", "Patagonia", "North Face", "Under Armour",
    "Puma", "Reebok", "Vans", "Converse", "Stussy", "Supreme", "Hilary Duff", "Lewis Capaldi",
    "Radiohead", "Beabadoobee", "Phoebe Bridgers", "KMFDM", "Ye", "Jackass", "Runescape",
    "Supergirl", "Noah Kahan", "My Chemical Romance", "MCR", "John Deere", "Wimbledon", "Alan Jackson"
]

EXCLUSION_KEYWORDS = [
    "meaning", "definition", "how to", "why", "iron", "near me", "template", "mockup",
    "tee times", "tee time", "tee off", "graphic tee", "essential tee", "vintage tee",
    "oversized tee", "plain shirt", "blank shirt", "kaffee", "rezepte", "bh für", "bra for",
    "tutorial", "bra", "t-shirt bra", "tee height", "là gì", "t-shirt femme",
    "custom t-shirt printing", "roblox t-shirt"
]

APPAREL_TERMS = ["shirt", "tshirt", "t-shirt", "tank top", "tanktop", "tee", "merch", "tshirts", "tees"]

def is_ip_infringing(keyword):
    for term in IP_BLACKLIST:
        if re.search(rf"\b{re.escape(term)}\b", keyword, re.IGNORECASE):
            return True
    return False

def get_design_idea(keyword):
    idea = keyword
    # Priority replacement for longer terms
    sorted_apparel = sorted(APPAREL_TERMS, key=len, reverse=True)
    for term in sorted_apparel:
        pattern = rf"\b{re.escape(term)}\b"
        if re.search(pattern, idea, re.IGNORECASE):
            idea = re.sub(pattern, "", idea, flags=re.IGNORECASE).strip()
            break

    idea = re.sub(r'\s+', ' ', idea).strip()
    return f"Design featuring '{idea}' concept."

def fetch_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    all_results = []
    seen_keywords = set()

    for kw in KEYWORDS:
        print(f"Fetching trends for: {kw}")
        retries = 3
        while retries > 0:
            try:
                pytrends.build_payload([kw], timeframe=TIMEFRAME)
                related_queries = pytrends.related_queries()

                if kw in related_queries and related_queries[kw]['rising'] is not None:
                    rising = related_queries[kw]['rising']
                    for index, row in rising.iterrows():
                        query = row['query'].lower()
                        value = row['value']

                        # Filtering
                        if query in seen_keywords: continue
                        if len(query.split()) < 2: continue
                        if any(ex in query for ex in EXCLUSION_KEYWORDS): continue
                        if not any(app in query for app in APPAREL_TERMS): continue
                        if query in [k.lower() for k in KEYWORDS]: continue

                        score = 9999 if value == 'Breakout' else int(value)
                        all_results.append({
                            'keyword': query,
                            'score': score,
                            'infringing': is_ip_infringing(query)
                        })
                        seen_keywords.add(query)

                time.sleep(5) # Delay between keywords
                break
            except Exception as e:
                print(f"Error fetching {kw}: {e}")
                if "429" in str(e):
                    print("Rate limit hit, sleeping...")
                    time.sleep(10)
                    retries -= 1
                else:
                    break

    return all_results

def update_trends_file(results):
    today = datetime.date.today().isoformat()
    header_date = f"## {today}"

    if os.path.exists(TRENDS_FILE):
        with open(TRENDS_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            if header_date in content:
                print(f"Trends for {today} already exist in {TRENDS_FILE}. Skipping update.")
                return
    else:
        content = "# Google Trends Merch Opportunities\n\n"

    general = [r for r in results if not r['infringing']]
    infringing = [r for r in results if r['infringing']]

    # Sort by score descending
    general.sort(key=lambda x: x['score'], reverse=True)
    infringing.sort(key=lambda x: x['score'], reverse=True)

    new_section = f"{header_date}\n\n"

    new_section += "### General Merch Opportunities\n"
    new_section += "| keyword | score | Why/Idea |\n"
    new_section += "|---------|-------|----------|\n"
    for item in general:
        idea = get_design_idea(item['keyword'])
        score_display = "Breakout" if item['score'] == 9999 else str(item['score'])
        new_section += f"| {item['keyword']} | {score_display} | {idea} |\n"

    new_section += "\n### Potential IP Infringing Opportunities\n"
    new_section += "| keyword | score | Why/Idea |\n"
    new_section += "|---------|-------|----------|\n"
    for item in infringing:
        idea = get_design_idea(item['keyword'])
        score_display = "Breakout" if item['score'] == 9999 else str(item['score'])
        new_section += f"| {item['keyword']} | {score_display} | {idea} |\n"

    new_section += "\n---\n\n"

    # Prepend
    main_header = "# Google Trends Merch Opportunities\n\n"
    if main_header in content:
        updated_content = content.replace(main_header, main_header + new_section)
    else:
        updated_content = main_header + new_section + content

    with open(TRENDS_FILE, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    print(f"Updated {TRENDS_FILE} with {len(results)} new trends.")

if __name__ == "__main__":
    trends = fetch_trends()
    if trends:
        update_trends_file(trends)
    else:
        print("No new trends found.")
