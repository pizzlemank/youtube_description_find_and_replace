import pandas as pd
from pytrends.request import TrendReq
import datetime
import time
import re
import os

def get_trends():
    pytrends = TrendReq(hl='en-US', tz=360)

    seed_keywords = ['tshirt', 't-shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch']
    apparel_terms = ['shirt', 'tshirt', 't-shirt', 'tank top', 'tanktop', 'tee', 'merch', 'shirts', 'tshirts', 'tees']

    # Exclusion list to filter out noise
    exclusions = [
        'meaning', 'definition', 'how to', 'why', 'iron', 'near me', 'template', 'mockup',
        'tee times', 'tee time', 'tee off', 'graphic tee', 'essential tee', 'vintage tee',
        'oversized tee', 'plain shirt', 'blank shirt', 'kaffee', 'rezepte', 'bh für', 'bra for',
        'tutorial', 'bra', 't-shirt bra', 'tee height', 'là gì', 't-shirt femme',
        'custom t-shirt printing', 'roblox t-shirt'
    ]

    # IP Blacklist
    ip_blacklist = [
        'disney', 'marvel', 'star wars', 'nike', 'adidas', 'taylor swift', 'bts', 'michael jackson',
        'nba', 'wnba', 'nfl', 'mlb', 'nhl', 'nintendo', 'pokemon', 'harry potter', 'nasa',
        'hellstar', 'ysl', 'gucci', 'prada', 'louis vuitton', 'arsenal', 'real madrid', 'liverpool',
        'man city', 'chelsea', 'bayern', 'barcelona', 'knicks', 'lakers', 'celtics', 'warriors',
        'bulls', 'amiri', 'trapstar', 'corteiz', 'sp5der', 'minus two', 'syna world',
        'harry styles', 'gracie abrams', 'daniel caesar', 'bad bunny', 'billie eilish', 'drake',
        'kanye', 'travis scott', 'bruno mars', 'hello kitty', 'sanrio', 'nascar', 'f1', 'mercedes',
        'ferrari', 'red bull', 'toy story', 'psg', 'asap rocky', 'megan moroney', 'sean john',
        'morgan wallen', 'spurs', 'rcb', 'snipes', 'asos', 'pattie gonia', 'wingstop',
        'ariana grande', 'selena gomez', 'carhartt', 'hazbin hotel', 'digital circus', 'tadc',
        'linkin park', 'bad omens', 'forrest frank', 'malcolm todd', 'böhse onkelz', 'love island',
        'eternal sunshine', 'madewell', 'anthropologie', 'glitch', 'stevie nicks', 'beyonce',
        'lilibet', 'olivia rodrigo', 'caitlin clark', 'sabrina carpenter', 'messi', 'ronaldo',
        'spiderman', 'spider-man', 'batman', 'superman', 'fifa', 'uefa', 'palace', 'kobe',
        'cowboys', 'yankees', 'dodgers', 'dfb', 'us open', 'olympics', 'cecil', 'h&m', "levi's",
        'zara', 'gap', 'old navy', 'lululemon', 'patagonia', 'north face', 'under armour', 'puma',
        'reebok', 'vans', 'converse', 'stussy', 'supreme', 'hilary duff', 'lewis capaldi',
        'radiohead', 'beabadoobee', 'phoebe bridgers', 'kmfdm', 'ye', 'jackass', 'runescape',
        'supergirl', 'noah kahan', 'my chemical romance', 'mcr', 'john deere', 'wimbledon',
        'alan jackson'
    ]

    all_trends = []

    for kw in seed_keywords:
        print(f"Fetching trends for: {kw}")
        try:
            pytrends.build_payload([kw], timeframe='now 7-d')
            related = pytrends.related_queries()

            if kw in related and related[kw]['rising'] is not None:
                df = related[kw]['rising']
                for index, row in df.iterrows():
                    query = row['query'].lower()
                    score = row['value']

                    # Filtering
                    words = query.split()

                    # Criteria: long tail (2+ words)
                    if len(words) < 2:
                        continue

                    # Criteria: contains apparel term
                    if not any(term in query for term in apparel_terms):
                        continue

                    # Criteria: not a generic variation of seed
                    if query in seed_keywords or query in apparel_terms:
                        continue

                    # Exclusion list
                    if any(exc in query for exc in exclusions):
                        continue

                    all_trends.append({'keyword': query, 'score': score})

            time.sleep(5) # Avoid rate limiting
        except Exception as e:
            print(f"Error fetching {kw}: {e}")
            time.sleep(10)

    if not all_trends:
        print("No trends found.")
        return

    # Deduplicate
    unique_trends = {t['keyword']: t['score'] for t in all_trends}

    general_merch = []
    ip_infringing = []

    for kw, score in unique_trends.items():
        is_ip = False
        for ip in ip_blacklist:
            if re.search(rf'\b{re.escape(ip)}\b', kw):
                is_ip = True
                break

        # Generate idea
        idea_source = kw
        # Replace apparel terms with empty string to get the core concept
        # Sort apparel terms by length descending to replace longer ones first (e.g. 'tank top' before 'top')
        sorted_apparel = sorted(apparel_terms, key=len, reverse=True)
        for term in sorted_apparel:
            idea_source = re.sub(rf'\b{re.escape(term)}\b', '', idea_source).strip()

        idea_source = re.sub(' +', ' ', idea_source) # clean spaces

        idea = f"Design featuring '{idea_source}'" if idea_source else "Generic apparel design"

        item = [kw, score, idea]
        if is_ip:
            ip_infringing.append(item)
        else:
            general_merch.append(item)

    # Sort by score descending (Breakout = 99999)
    def sort_score(item):
        val = item[1]
        if isinstance(val, str) and 'breakout' in val.lower():
            return 99999
        try:
            return int(val)
        except:
            return 0

    general_merch.sort(key=sort_score, reverse=True)
    ip_infringing.sort(key=sort_score, reverse=True)

    update_trends_file(general_merch, ip_infringing)

def update_trends_file(general, ip):
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    with open('trends.md', 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if already updated today
    if f"## {today}" in content:
        print("Already updated today.")
        # We might want to skip or overwrite. The prompt implies "everyday crawl",
        # usually it means append if not there.
        # For testing, I'll allow it or just proceed.
        # Let's proceed to allow multiple runs for testing if needed, or just return.
        # return

    new_content = f"## {today}\n\n"

    if general:
        new_content += "### General Merch Opportunities\n\n"
        new_content += "| keyword | score | Why/Idea |\n"
        new_content += "| :--- | :--- | :--- |\n"
        for item in general:
            new_content += f"| {item[0]} | {item[1]} | {item[2]} |\n"
        new_content += "\n"

    if ip:
        new_content += "### Potential IP Infringing Opportunities\n\n"
        new_content += "| keyword | score | Why/Idea |\n"
        new_content += "| :--- | :--- | :--- |\n"
        for item in ip:
            new_content += f"| {item[0]} | {item[1]} | {item[2]} |\n"
        new_content += "\n"

    # Prepend after the main header
    header = "# Google Trends Merch Opportunities\n"
    if header in content:
        body = content.replace(header, "")
        final_content = header + "\n" + new_content + body
    else:
        final_content = header + "\n" + new_content + content

    with open('trends.md', 'w', encoding='utf-8') as f:
        f.write(final_content)
    print(f"Updated trends.md for {today}")

if __name__ == "__main__":
    get_trends()
