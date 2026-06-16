import pandas as pd
from pytrends.request import TrendReq
import time
import datetime
import re
import os

# Configuration
KEYWORDS = ['tshirt', 't-shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch']
TIMEFRAME = 'now 7-d'
GEO = ''  # Worldwide
TRENDS_FILE = 'trends.md'

# IP Blacklist (from memory and common sense)
IP_BLACKLIST = [
    'Disney', 'Marvel', 'Star Wars', 'Nike', 'Adidas', 'Taylor Swift', 'BTS',
    'Michael Jackson', 'NBA', 'WNBA', 'NFL', 'MLB', 'NHL', 'Nintendo', 'Pokemon',
    'Harry Potter', 'NASA', 'Hellstar', 'YSL', 'Gucci', 'Prada', 'Louis Vuitton',
    'Arsenal', 'Real Madrid', 'Liverpool', 'Man City', 'Chelsea', 'Bayern',
    'Barcelona', 'Knicks', 'Lakers', 'Celtics', 'Warriors', 'Bulls', 'Amiri',
    'Trapstar', 'Corteiz', 'Sp5der', 'Minus Two', 'Syna World', 'Harry Styles',
    'Gracie Abrams', 'Daniel Caesar', 'Bad Bunny', 'Billie Eilish', 'Drake',
    'Kanye', 'Travis Scott', 'Bruno Mars', 'Hello Kitty', 'Sanrio', 'NASCAR',
    'F1', 'Mercedes', 'Ferrari', 'Red Bull', 'Toy Story', 'PSG', 'ASAP Rocky',
    'Megan Moroney', 'Sean John', 'Morgan Wallen', 'Spurs', 'RCB', 'Snipes',
    'ASOS', 'Pattie Gonia', 'Wingstop', 'Ariana Grande', 'selena gomez',
    'Carhartt', 'Hazbin Hotel', 'Digital Circus', 'TADC', 'Linkin Park',
    'Bad Omens', 'Forrest Frank', 'Malcolm Todd', 'Böhse Onkelz', 'Love Island',
    'Eternal Sunshine', 'Madewell', 'Anthropologie', 'Glitch', 'Stevie Nicks',
    'Beyonce', 'Lilibet', 'Olivia Rodrigo', 'Caitlin Clark', 'Sabrina Carpenter'
]

APPAREL_TERMS = [
    'tshirts', 't-shirts', 'shirts', 'tank tops', 'tanktops', 'tees',
    'tshirt', 't-shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch'
]

EXCLUDE_TERMS = [
    'meaning', 'definition', 'how to', 'why', 'iron', 'near me', 'template',
    'mockup', 'tee times', 'tee time', 'tee off', 'graphic tee', 'essential tee',
    'vintage tee', 'oversized tee', 'plain shirt', 'blank shirt', 'kaffee',
    'rezepte', 'bh für', 'bra for', 'tutorial', 'bra', 't-shirt bra', 'là gì'
]

def is_ip_infringing(keyword):
    for brand in IP_BLACKLIST:
        if re.search(rf'\b{re.escape(brand)}\b', keyword, re.IGNORECASE):
            return True
    return False

def get_rising_trends(pytrends, keyword):
    print(f"Fetching trends for: {keyword}")
    try:
        pytrends.build_payload([keyword], timeframe=TIMEFRAME, geo=GEO)
        related_queries = pytrends.related_queries()
        if keyword in related_queries and related_queries[keyword]['rising'] is not None:
            return related_queries[keyword]['rising']
    except Exception as e:
        print(f"Error fetching {keyword}: {e}")
        if "429" in str(e):
            print("Rate limit hit. Waiting 30 seconds...")
            time.sleep(30)
            # One retry
            try:
                pytrends.build_payload([keyword], timeframe=TIMEFRAME, geo=GEO)
                related_queries = pytrends.related_queries()
                if keyword in related_queries and related_queries[keyword]['rising'] is not None:
                    return related_queries[keyword]['rising']
            except:
                pass
    return None

def process_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    all_data = []
    seen_keywords = set()

    for kw in KEYWORDS:
        rising = get_rising_trends(pytrends, kw)
        if rising is not None:
            for index, row in rising.iterrows():
                query = row['query'].lower()
                score = row['value']

                # Filter long tail (at least 2 words)
                if len(query.split()) < 2:
                    continue

                # Must contain apparel term
                if not any(term in query for term in APPAREL_TERMS):
                    continue

                # Exclude noise
                if any(term in query for term in EXCLUDE_TERMS):
                    continue

                # Deduplicate
                if query in seen_keywords:
                    continue
                seen_keywords.add(query)

                # Generate Idea
                idea_concept = query
                for term in APPAREL_TERMS:
                    idea_concept = re.sub(rf'\b{re.escape(term)}\b', '', idea_concept, flags=re.IGNORECASE)
                idea_concept = re.sub(r'\s+', ' ', idea_concept).strip()

                if not idea_concept:
                    continue # Skip generic "t shirt" queries

                infringing = is_ip_infringing(query)

                all_data.append({
                    'keyword': query,
                    'score': score,
                    'infringing': infringing,
                    'idea': f"Design based on '{idea_concept}'. Popular rising search."
                })

        time.sleep(5) # Delay between keywords

    if not all_data:
        print("No new trends found.")
        return

    # Sort by score (Breakout is usually a large number or string)
    def sort_score(val):
        if val == 'Breakout':
            return 9999
        try:
            return int(val)
        except:
            return 0

    all_data.sort(key=lambda x: sort_score(x['score']), reverse=True)

    # Separate sections
    general = [d for d in all_data if not d['infringing']]
    ip_infringe = [d for d in all_data if d['infringing']]

    today = datetime.date.today().isoformat()

    # Check if today already exists in trends.md
    if os.path.exists(TRENDS_FILE):
        with open(TRENDS_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            if f"## {today}" in content:
                print(f"Trends for {today} already exist. Skipping file update.")
                return

    output = f"## {today}\n\n"

    if general:
        output += "### General Merch Opportunities\n"
        output += "| keyword | score | why you think is an opportunity, idea for design, or what the internet shopping is already doing |\n"
        output += "| --- | --- | --- |\n"
        for d in general:
            output += f"| {d['keyword']} | {d['score']} | {d['idea']} |\n"
        output += "\n"

    if ip_infringe:
        output += "### Potential IP Infringing Opportunities\n"
        output += "| keyword | score | why you think is an opportunity, idea for design, or what the internet shopping is already doing |\n"
        output += "| --- | --- | --- |\n"
        for d in ip_infringe:
            output += f"| {d['keyword']} | {d['score']} | {d['idea']} |\n"
        output += "\n"

    # Prepend to file
    if os.path.exists(TRENDS_FILE):
        with open(TRENDS_FILE, 'r', encoding='utf-8') as f:
            existing_content = f.read()
    else:
        existing_content = "# Google Trends Merch Opportunities\n\n"

    # Find the main header and insert after it
    header = "# Google Trends Merch Opportunities\n\n"
    if existing_content.startswith(header):
        new_content = header + output + existing_content[len(header):]
    else:
        new_content = header + output + existing_content

    with open(TRENDS_FILE, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"Updated {TRENDS_FILE} with {len(all_data)} new trends.")

if __name__ == "__main__":
    process_trends()
