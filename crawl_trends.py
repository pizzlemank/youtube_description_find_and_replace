import pandas as pd
from pytrends.request import TrendReq
import time
import re
import datetime
import os

# Configuration
KEYWORDS = ['tshirt', 't-shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch']
TIMEFRAME = 'now 7-d'
RETRIES = 3
RETRY_DELAY = 10
QUERY_DELAY = 5

IP_BLACKLIST = [
    'Disney', 'Marvel', 'Star Wars', 'Nike', 'Adidas', 'Taylor Swift', 'BTS', 'Michael Jackson',
    'NBA', 'WNBA', 'NFL', 'MLB', 'NHL', 'Nintendo', 'Pokemon', 'Harry Potter', 'NASA', 'Hellstar',
    'YSL', 'Gucci', 'Prada', 'Louis Vuitton', 'Arsenal', 'Real Madrid', 'Liverpool', 'Man City',
    'Chelsea', 'Bayern', 'Barcelona', 'Knicks', 'Lakers', 'Celtics', 'Warriors', 'Bulls', 'Amiri',
    'Trapstar', 'Corteiz', 'Sp5der', 'Minus Two', 'Syna World', 'Harry Styles', 'Gracie Abrams',
    'Daniel Caesar', 'Bad Bunny', 'Billie Eilish', 'Drake', 'Kanye', 'Travis Scott', 'Bruno Mars',
    'Hello Kitty', 'Sanrio', 'NASCAR', 'F1', 'Mercedes', 'Ferrari', 'Red Bull', 'Toy Story', 'PSG',
    'ASAP Rocky', 'Megan Moroney', 'Sean John', 'Morgan Wallen', 'Spurs', 'RCB', 'Snipes', 'ASOS',
    'Pattie Gonia', 'Wingstop', 'Ariana Grande', 'selena gomez', 'Carhartt', 'Hazbin Hotel',
    'Digital Circus', 'TADC', 'Linkin Park', 'Bad Omens', 'Forrest Frank', 'Malcolm Todd',
    'Böhse Onkelz', 'Love Island', 'Eternal Sunshine', 'Madewell', 'Anthropologie', 'Glitch',
    'Stevie Nicks', 'Beyonce', 'Lilibet', 'Olivia Rodrigo', 'Caitlin Clark', 'Sabrina Carpenter',
    'Messi', 'Ronaldo', 'Spiderman', 'Spider-man', 'Batman', 'Superman', 'FIFA', 'UEFA', 'Palace',
    'Kobe', 'Cowboys', 'Yankees', 'Dodgers', 'DFB', 'US Open', 'Olympics', 'Cecil', 'H&M', "Levi's",
    'Zara', 'Gap', 'Old Navy', 'Lululemon', 'Patagonia', 'North Face', 'Under Armour', 'Puma',
    'Reebok', 'Vans', 'Converse', 'Stussy', 'Supreme', 'Hilary Duff', 'Lewis Capaldi', 'Radiohead',
    'Beabadoobee', 'Phoebe Bridgers', 'KMFDM', 'Ye', 'Jackass', 'Runescape', 'Supergirl'
]

EXCLUDE_KEYWORDS = [
    'meaning', 'definition', 'how to', 'why', 'iron', 'near me', 'template', 'mockup',
    'tee times', 'tee time', 'tee off', 'graphic tee', 'essential tee', 'vintage tee',
    'oversized tee', 'plain shirt', 'blank shirt', 'kaffee', 'rezepte', 'bh für', 'bra for',
    'tutorial', 'bra', 't-shirt bra', 'là gì', 'tee height'
]

APPAREL_TERMS = [
    'tshirts', 't-shirts', 't-shirt', 'tshirt', 'tank tops', 'tank top', 'tanktop',
    'shirts', 'shirt', 'tees', 'tee', 'merch'
]

def is_ip_infringing(keyword):
    for brand in IP_BLACKLIST:
        if re.search(rf'\b{re.escape(brand)}\b', keyword, re.IGNORECASE):
            return True
    return False

def generate_idea(keyword):
    idea = keyword
    # Replace longer apparel terms first to avoid partial replacement issues
    sorted_apparel = sorted(APPAREL_TERMS, key=len, reverse=True)
    for term in sorted_apparel:
        idea = re.sub(rf'\b{re.escape(term)}\b', '', idea, flags=re.IGNORECASE)

    idea = re.sub(r'\s+', ' ', idea).strip()
    if not idea:
        return "Generic apparel design"
    return f"Design focused on '{idea}'"

def fetch_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    all_results = []
    seen_keywords = set()

    for kw in KEYWORDS:
        for attempt in range(RETRIES):
            try:
                print(f"Fetching related queries for: {kw}")
                pytrends.build_payload([kw], cat=0, timeframe=TIMEFRAME, geo='', gprop='')
                related = pytrends.related_queries()

                if kw in related and related[kw]['rising'] is not None:
                    df = related[kw]['rising']
                    for _, row in df.iterrows():
                        query = row['query']
                        value = row['value']

                        # Filtering
                        if query in seen_keywords:
                            continue

                        words = query.split()
                        if len(words) < 2: # Long tail check
                            continue

                        # Exclude generic or non-commercial
                        if any(ex in query.lower() for ex in EXCLUDE_KEYWORDS):
                            continue

                        # Exclude exact seed matches or very generic ones
                        if query.lower() in [k.lower() for k in APPAREL_TERMS]:
                            continue

                        score = 9999 if value == 'Breakout' else int(value)

                        all_results.append({
                            'keyword': query,
                            'score': score,
                            'infringing': is_ip_infringing(query)
                        })
                        seen_keywords.add(query)

                time.sleep(QUERY_DELAY)
                break # Success, break retry loop
            except Exception as e:
                print(f"Error fetching {kw}: {e}")
                if attempt < RETRIES - 1:
                    print(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    print(f"Failed to fetch {kw} after {RETRIES} attempts.")

    return all_results

def update_trends_md(results):
    if not results:
        print("No new results to add.")
        return

    today = datetime.date.today().strftime('%Y-%m-%d')
    header = f"## {today}\n\n"

    # Check if today's entry already exists
    content = ""
    if os.path.exists('trends.md'):
        with open('trends.md', 'r', encoding='utf-8') as f:
            content = f.read()
            if header in content:
                print(f"Trends for {today} already exist in trends.md. Skipping update.")
                return

    # Sort results by score desc
    results.sort(key=lambda x: x['score'], reverse=True)

    general_table = "| Keyword | Score | Why/Idea |\n| :--- | :--- | :--- |\n"
    ip_table = "| Keyword | Score | Why/Idea |\n| :--- | :--- | :--- |\n"

    gen_count = 0
    ip_count = 0

    for res in results:
        idea = generate_idea(res['keyword'])
        row = f"| {res['keyword']} | {res['score']} | {idea} |\n"
        if res['infringing']:
            ip_table += row
            ip_count += 1
        else:
            general_table += row
            gen_count += 1

    new_entry = header
    if gen_count > 0:
        new_entry += "### General Merch Opportunities\n\n" + general_table + "\n"
    if ip_count > 0:
        new_entry += "### Potential IP Infringing Opportunities\n\n" + ip_table + "\n"

    # Prepend to content
    main_header = "# Google Trends Merch Opportunities\n\n"
    if content.startswith(main_header):
        updated_content = main_header + new_entry + content[len(main_header):]
    else:
        updated_content = main_header + new_entry + content

    with open('trends.md', 'w', encoding='utf-8') as f:
        f.write(updated_content)
    print(f"Successfully updated trends.md with {len(results)} new items.")

if __name__ == "__main__":
    trends = fetch_trends()
    update_trends_md(trends)
