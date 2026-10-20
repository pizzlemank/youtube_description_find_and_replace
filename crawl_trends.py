import os
import re
import time
import datetime
import pandas as pd
from pytrends.request import TrendReq

SEED_KEYWORDS = ['tshirt', 't-shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch']

EXACT_EXCLUDE_TERMS = {
    'tshirt', 't-shirt', 't shirt', 'tshirts', 't-shirts', 't shirts',
    'shirt', 'shirts', 'tank top', 'tank tops', 'tanktop', 'tanktops',
    'tee', 'tees', 'merch'
}

IRRELEVANT_TERMS = [
    'meaning', 'definition', 'how to', 'why', 'iron', 'near me', 'template',
    'mockup', 'tee times', 'tee time', 'tee off', 'graphic tee', 'essential tee',
    'vintage tee', 'oversized tee', 'plain shirt', 'blank shirt', 'kaffee',
    'rezepte', 'bh für', 'bra for', 'tutorial', 'bra', 't-shirt bra',
    'tee height', 'là gì', 't-shirt femme', 'custom t-shirt printing', 'roblox t-shirt'
]

IP_BLACKLIST = [
    "Disney", "Marvel", "Star Wars", "Nike", "Adidas", "Taylor Swift", "BTS",
    "Michael Jackson", "NBA", "WNBA", "NFL", "MLB", "NHL", "Nintendo", "Pokemon", "Pokémon",
    "Harry Potter", "NASA", "Hellstar", "YSL", "Gucci", "Prada", "Louis Vuitton",
    "Arsenal", "Real Madrid", "Liverpool", "Man City", "Chelsea", "Bayern",
    "Barcelona", "Knicks", "Lakers", "Celtics", "Warriors", "Bulls", "Amiri",
    "Trapstar", "Corteiz", "Sp5der", "Minus Two", "Syna World", "Harry Styles",
    "Gracie Abrams", "Daniel Caesar", "Bad Bunny", "Billie Eilish", "Drake",
    "Kanye", "Travis Scott", "Bruno Mars", "Hello Kitty", "Sanrio", "NASCAR",
    "f1", "Mercedes", "Ferrari", "Red Bull", "Toy Story", "PSG", "ASAP Rocky",
    "Megan Moroney", "Sean John", "Morgan Wallen", "Spurs", "RCB", "Snipes",
    "ASOS", "Pattie Gonia", "Wingstop", "Ariana Grande", "selena gomez",
    "Carhartt", "Hazbin Hotel", "Digital Circus", "TADC", "Linkin Park",
    "Bad Omens", "Forrest Frank", "Malcolm Todd", "Böhse Onkelz", "Love Island",
    "Eternal Sunshine", "Madewell", "Anthropologie", "Glitch", "Stevie Nicks",
    "Beyonce", "Lilibet", "Olivia Rodrigo", "Caitlin Clark", "Sabrina Carpenter",
    "Messi", "Ronaldo", "Spiderman", "Spider-man", "Batman", "Superman", "FIFA",
    "UEFA", "Palace", "Kobe", "Cowboys", "Yankees", "Dodgers", "DFB", "US Open",
    "Olympics", "Cecil", "H&M", "Levi's", "Zara", "Gap", "Old Navy", "Lululemon",
    "Patagonia", "North Face", "Under Armour", "Puma", "Reebok", "Vans",
    "Converse", "Stussy", "Supreme", "Hilary Duff", "Lewis Capaldi", "Radiohead",
    "Beabadoobee", "Phoebe Bridgers", "KMFDM", "Ye", "Jackass", "Runescape",
    "Supergirl", "Noah Kahan", "My Chemical Romance", "MCR", "John Deere",
    "Wimbledon", "Alan Jackson", "Twenty One Pilots", "Helluva Boss", "Dunkin",
    "Fontaines DC", "Calvin Harris", "Tate McRae", "Lizzy McAlpine", "Young Miko",
    "Elevation Worship", "Yeat", "Milwaukee Brewers", "World Series", "Fortnite",
    "Roblox", "Minecraft", "Zara Larsson"
]

def is_ip_infringing(keyword):
    """Check if keyword matches any IP blacklisted terms using regex word boundaries."""
    for ip in IP_BLACKLIST:
        pattern = r'\b' + re.escape(ip) + r'\b'
        if re.search(pattern, keyword, re.IGNORECASE):
            return True
    return False

def clean_design_idea(keyword):
    """Extract design concept by removing apparel terms (longer terms first)."""
    apparel_replacements = [
        'tank tops', 'tank top', 'tanktops', 'tanktop',
        't-shirts', 't-shirt', 'tshirts', 'tshirt',
        'shirts', 'shirt', 'tees', 'tee', 'merch'
    ]
    concept = keyword.lower()
    for term in apparel_replacements:
        pattern = r'\b' + re.escape(term) + r'\b'
        concept = re.sub(pattern, '', concept, flags=re.IGNORECASE)

    concept = re.sub(r'\s+', ' ', concept).strip().title()
    if not concept:
        concept = keyword.title()

    return f"Trending search demand on Google. Design idea: Typographic or illustrated design highlighting '{concept}'. Target POD platforms like Redbubble, Merch by Amazon, or Etsy."

def parse_score(score_val):
    """Convert score to integer for sorting, treating 'Breakout' as 9999."""
    if isinstance(score_val, str):
        if 'breakout' in score_val.lower():
            return 9999
        try:
            # handle formats like '+250%' or '250'
            cleaned = score_val.replace('+', '').replace('%', '').replace(',', '').strip()
            return int(cleaned)
        except ValueError:
            return 0
    elif isinstance(score_val, (int, float)):
        return int(score_val)
    return 0

def fetch_rising_queries():
    """Fetch rising queries from Google Trends for seed keywords."""
    print("Initializing PyTrends...")
    pytrends = TrendReq(hl='en-US', tz=360)

    all_results = {}

    for kw in SEED_KEYWORDS:
        print(f"Fetching trends for seed keyword: '{kw}'...")
        retries = 3
        for attempt in range(retries):
            try:
                pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='', gprop='')
                related = pytrends.related_queries()
                if kw in related and related[kw]['rising'] is not None:
                    df = related[kw]['rising']
                    for _, row in df.iterrows():
                        query = str(row['query']).strip()
                        value = str(row['value']).strip()
                        if query not in all_results:
                            all_results[query] = value
                break
            except Exception as e:
                print(f"Attempt {attempt + 1} failed for '{kw}': {e}")
                if attempt < retries - 1:
                    print("Retrying in 10 seconds...")
                    time.sleep(10)
                else:
                    print(f"Skipping '{kw}' after maximum retries.")
        time.sleep(5)

    return all_results

def filter_and_categorize(results_dict):
    """Filter raw results into General and IP-Infringing categories."""
    general_opportunities = []
    ip_opportunities = []

    apparel_terms_pattern = r'\b(shirt|shirts|tshirt|tshirts|t-shirt|t-shirts|tank top|tank tops|tanktop|tanktops|tee|tees|merch)\b'

    for query, score in results_dict.items():
        query_lower = query.lower().strip()

        # Check exact generic exclusion
        if query_lower in EXACT_EXCLUDE_TERMS:
            continue

        # Long tail check (>= 2 words)
        words = query_lower.split()
        if len(words) < 2:
            continue

        # Must contain an apparel term
        if not re.search(apparel_terms_pattern, query_lower):
            continue

        # Exclude non-commercial / irrelevant queries
        if any(irrelevant in query_lower for irrelevant in IRRELEVANT_TERMS):
            continue

        parsed_score = parse_score(score)
        idea = clean_design_idea(query)

        entry = {
            'keyword': query,
            'score': score,
            'parsed_score': parsed_score,
            'idea': idea
        }

        if is_ip_infringing(query):
            ip_opportunities.append(entry)
        else:
            general_opportunities.append(entry)

    # Sort descending by score
    general_opportunities.sort(key=lambda x: x['parsed_score'], reverse=True)
    ip_opportunities.sort(key=lambda x: x['parsed_score'], reverse=True)

    return general_opportunities, ip_opportunities

def format_markdown_table(items):
    """Format list of items as markdown table."""
    if not items:
        return "| Keyword | Score | Why/Idea |\n| --- | --- | --- |\n| No data found | - | - |\n"

    lines = ["| Keyword | Score | Why/Idea |", "| --- | --- | --- |"]
    for item in items:
        # Escape pipe symbols if present
        kw = item['keyword'].replace('|', '&#124;')
        sc = str(item['score']).replace('|', '&#124;')
        idea = item['idea'].replace('|', '&#124;')
        lines.append(f"| {kw} | {sc} | {idea} |")
    return "\n".join(lines) + "\n"

def update_trends_markdown(general_ops, ip_ops):
    """Update trends.md prepending the new day section right under the main title."""
    today_str = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')
    date_header = f"## {today_str}"

    filename = "trends.md"
    existing_content = ""
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            existing_content = f.read()

    # Check if date header already exists to avoid duplicate entries on same day
    # If it exists, we replace the existing date section
    main_title = "# Google Trends Merch Opportunities\n\n"

    new_section = f"{date_header}\n\n"
    new_section += "### General Merch Opportunities\n\n"
    new_section += format_markdown_table(general_ops) + "\n"
    new_section += "### Potential IP Infringing Opportunities\n\n"
    new_section += format_markdown_table(ip_ops) + "\n"

    if date_header in existing_content:
        # Replace the section for today
        pattern = r"## " + re.escape(today_str) + r"\n\n.*?(?=\n## |\Z)"
        existing_content = re.sub(pattern, new_section.strip(), existing_content, flags=re.DOTALL)
        full_content = existing_content
    else:
        if existing_content.startswith("# Google Trends Merch Opportunities"):
            rest_of_content = existing_content[len(main_title):].lstrip()
            full_content = main_title + new_section + rest_of_content
        else:
            full_content = main_title + new_section + existing_content

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(full_content)

    print(f"Successfully updated {filename} for {today_str}.")

def main():
    raw_results = fetch_rising_queries()
    general_ops, ip_ops = filter_and_categorize(raw_results)
    update_trends_markdown(general_ops, ip_ops)

if __name__ == "__main__":
    main()
