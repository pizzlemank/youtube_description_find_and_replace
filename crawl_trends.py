import pandas as pd
from pytrends.request import TrendReq
import time
import datetime
import re
import os

# Initialize pytrends
# hl='en-US' for English (United States), tz=360 is CST (Central Standard Time)
pytrends = TrendReq(hl='en-US', tz=360)

# Seed keywords for apparel - used to find rising related queries
SEED_KEYWORDS = ['tshirt', 't-shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch']

# IP Blacklist - brands, celebrities, sports teams, etc. to flag for caution
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
    'Stevie Nicks', 'Beyonce', 'Lilibet', 'Olivia Rodrigo', 'Caitlin Clark', 'Sabrina Carpenter'
]

# Irrelevant terms to filter out noise
EXCLUDE_KEYWORDS = [
    'meaning', 'definition', 'how to', 'why', 'iron', 'near me', 'template', 'mockup',
    'tee times', 'tee time', 'tee off', 'graphic tee', 'essential tee', 'vintage tee',
    'oversized tee', 'plain shirt', 'blank shirt', 'kaffee', 'rezepte', 'bh für',
    'bra for', 'tutorial', 'bra', 't-shirt bra', 'là gì'
]

def is_ip_infringing(keyword):
    """Checks if a keyword contains any terms from the IP blacklist using word boundaries."""
    for term in IP_BLACKLIST:
        if re.search(r'\b' + re.escape(term) + r'\b', keyword, re.IGNORECASE):
            return True
    return False

def get_rising_trends(seed_keyword):
    """Fetches rising related queries for a given seed keyword with retry logic for 429 errors."""
    print(f"Fetching trends for: {seed_keyword}")
    retries = 2
    for i in range(retries + 1):
        try:
            # timeframe='now 7-d' for the last week
            pytrends.build_payload([seed_keyword], timeframe='now 7-d', geo='')
            related_queries = pytrends.related_queries()
            if seed_keyword in related_queries:
                return related_queries[seed_keyword]['rising']
            return None
        except Exception as e:
            print(f"Error fetching trends for {seed_keyword}: {e}")
            if i < retries:
                print("Retrying in 30 seconds...")
                time.sleep(30)
            else:
                return None

def generate_idea(keyword):
    """Generates a simple design idea or reason based on the keyword."""
    # Clean up the keyword to extract the main concept
    idea_base = keyword.lower()
    # Replace apparel terms (longest first to avoid partial replacement like 'tshirt' -> 't-')
    sorted_seeds = sorted(SEED_KEYWORDS, key=len, reverse=True)
    for term in sorted_seeds:
        idea_base = idea_base.replace(term, '')

    idea_base = idea_base.strip()
    idea_base = re.sub(r'\s+', ' ', idea_base)

    if not idea_base:
        return "Generic apparel design based on the trending keyword."

    return f"Design concept focusing on '{idea_base}'. The internet is showing increased interest in this niche."

def process_trends():
    """Main loop to process all seed keywords and gather valid trends."""
    all_results = []
    seen_keywords = set()

    for seed in SEED_KEYWORDS:
        rising = get_rising_trends(seed)
        if rising is not None and not rising.empty:
            for index, row in rising.iterrows():
                keyword = row['query'].lower()
                score = row['value']

                # Deduplication across different seed keyword runs
                if keyword in seen_keywords:
                    continue
                seen_keywords.add(keyword)

                # Criteria: Long tail (2+ words)
                if len(keyword.split()) < 2:
                    continue

                # Criteria: Must contain one of our target apparel terms
                if not any(term in keyword for term in SEED_KEYWORDS):
                    continue

                # Criteria: Exclude generic or irrelevant terms
                if any(ex in keyword for ex in EXCLUDE_KEYWORDS):
                    continue

                # Criteria: Filter out exact matches of seed keywords or very generic ones
                if keyword in [s.lower() for s in SEED_KEYWORDS] or keyword in ['t shirt', 't-shirts', 'tees']:
                    continue

                infringing = is_ip_infringing(keyword)
                idea = generate_idea(keyword)

                all_results.append({
                    'keyword': keyword,
                    'score': score,
                    'infringing': infringing,
                    'idea': idea
                })
        # Polite delay to avoid rate limiting
        time.sleep(5)

    return all_results

def update_trends_file(results):
    """Formats results and prepends them to trends.md."""
    if not results:
        print("No new trends found.")
        return

    today = datetime.date.today().strftime('%Y-%m-%d')

    # Check if a section for today already exists to avoid duplicates on same-day reruns
    if os.path.exists('trends.md'):
        with open('trends.md', 'r', encoding='utf-8') as f:
            content = f.read()
            if f"## {today}" in content:
                print(f"Trends for {today} already exist in trends.md. Skipping update.")
                return

    general_merch = [r for r in results if not r['infringing']]
    ip_infringing = [r for r in results if r['infringing']]

    # Sort helper to handle 'Breakout' and numeric scores
    def sort_key(x):
        val = x['score']
        if isinstance(val, str) and val.lower() == 'breakout':
            return 9999
        try:
            return int(val)
        except (ValueError, TypeError):
            return 0

    general_merch.sort(key=sort_key, reverse=True)
    ip_infringing.sort(key=sort_key, reverse=True)

    # Build the Markdown string for today's findings
    new_entry = f"## {today}\n\n"

    if general_merch:
        new_entry += "### General Merch Opportunities\n\n"
        new_entry += "| keyword | score | Why/Idea |\n"
        new_entry += "| --- | --- | --- |\n"
        for r in general_merch:
            new_entry += f"| {r['keyword']} | {r['score']} | {r['idea']} |\n"
        new_entry += "\n"

    if ip_infringing:
        new_entry += "### Potential IP Infringing Opportunities\n\n"
        new_entry += "| keyword | score | Why/Idea |\n"
        new_entry += "| --- | --- | --- |\n"
        for r in ip_infringing:
            new_entry += f"| {r['keyword']} | {r['score']} | {r['idea']} |\n"
        new_entry += "\n"

    header = "# Google Trends Merch Opportunities\n"

    # Prepend the new entry below the main header
    if os.path.exists('trends.md'):
        with open('trends.md', 'r', encoding='utf-8') as f:
            current_content = f.read()

        if current_content.startswith(header):
            # Insert after the header
            final_content = header + "\n" + new_entry + current_content[len(header):].lstrip()
        else:
            # If header is missing for some reason, just prepend
            final_content = header + "\n" + new_entry + current_content
    else:
        final_content = header + "\n" + new_entry

    with open('trends.md', 'w', encoding='utf-8') as f:
        f.write(final_content)

    print(f"Successfully updated trends.md with {len(results)} results.")

if __name__ == "__main__":
    found_trends = process_trends()
    update_trends_file(found_trends)
