import re
import time
import datetime
import os
import pandas as pd
from pytrends.request import TrendReq

# Seed keywords for POD merch discovery
SEED_KEYWORDS = ['tshirt', 't-shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch']

# Apparel keywords required for long-tail matching
APPAREL_KEYWORDS = ['shirt', 'tshirt', 't-shirt', 'tank top', 'tanktop', 'tee', 'merch']

# Exact search terms to ignore (too generic or non-actionable)
EXACT_IGNORE_TERMS = {
    't shirt', 't-shirt', 'tshirt', 't-shirts', 't shirts', 'tshirts',
    'shirt', 'shirts', 'tee', 'tees', 'merch', 'tank top', 'tank tops', 'tanktop'
}

# Substring filter: exclude non-commercial, non-apparel, or irrelevant queries
EXCLUDE_SUBSTRINGS = [
    'meaning', 'definition', 'how to', 'why', 'iron', 'near me',
    'template', 'mockup', 'tee times', 'tee time', 'tee off',
    'graphic tee', 'essential tee', 'vintage tee', 'oversized tee',
    'plain shirt', 'blank shirt', 'kaffee', 'rezepte', 'bh für',
    'bra for', 'tutorial', 'bra', 't-shirt bra', 'tee height', 'là gì',
    't-shirt femme', 'custom t-shirt printing', 'roblox t-shirt'
]

# Blacklist of IP / Trademarked / Celebrity / Brand names
IP_BLACKLIST = [
    'disney', 'marvel', 'star wars', 'nike', 'adidas', 'taylor swift', 'bts',
    'michael jackson', 'nba', 'wnba', 'nfl', 'mlb', 'nhl', 'nintendo', 'pokemon',
    'harry potter', 'nasa', 'hellstar', 'ysl', 'gucci', 'prada', 'louis vuitton',
    'arsenal', 'real madrid', 'liverpool', 'man city', 'chelsea', 'bayern',
    'barcelona', 'knicks', 'lakers', 'celtics', 'warriors', 'bulls', 'amiri',
    'trapstar', 'corteiz', 'sp5der', 'minus two', 'syna world', 'harry styles',
    'gracie abrams', 'daniel caesar', 'bad bunny', 'billie eilish', 'drake',
    'kanye', 'travis scott', 'bruno mars', 'hello kitty', 'sanrio', 'nascar',
    'f1', 'mercedes', 'ferrari', 'red bull', 'toy story', 'psg', 'asap rocky',
    'megan moroney', 'sean john', 'morgan wallen', 'spurs', 'rcb', 'snipes',
    'asos', 'pattie gonia', 'wingstop', 'ariana grande', 'selena gomez',
    'carhartt', 'hazbin hotel', 'digital circus', 'tadc', 'linkin park',
    'bad omens', 'forrest frank', 'malcolm todd', 'böhse onkelz', 'love island',
    'eternal sunshine', 'madewell', 'anthropologie', 'glitch', 'stevie nicks',
    'beyonce', 'lilibet', 'olivia rodrigo', 'caitlin clark', 'sabrina carpenter',
    'messi', 'ronaldo', 'spiderman', 'spider-man', 'batman', 'superman', 'fifa',
    'uefa', 'palace', 'kobe', 'cowboys', 'yankees', 'dodgers', 'dfb', 'us open',
    'olympics', 'cecil', 'h&m', "levi's", 'zara', 'gap', 'old navy', 'lululemon',
    'patagonia', 'north face', 'under armour', 'puma', 'reebok', 'vans',
    'converse', 'stussy', 'supreme', 'hilary duff', 'lewis capaldi', 'radiohead',
    'beabadoobee', 'phoebe bridgers', 'kmfdm', 'ye', 'jackass', 'runescape',
    'supergirl', 'noah kahan', 'my chemical romance', 'mcr', 'john deere',
    'wimbledon', 'alan jackson'
]

def is_ip_infringing(keyword):
    """
    Check if the keyword contains any trademarked or IP-infringing brand/person using regex word boundaries.
    """
    kw_lower = keyword.lower()
    for ip in IP_BLACKLIST:
        pattern = r'\b' + re.escape(ip) + r'\b'
        if re.search(pattern, kw_lower):
            return True
    return False

def generate_idea(keyword):
    """
    Generates a description/idea/analysis for a keyword opportunity.
    """
    kw_lower = keyword.lower()

    # Priority apparel replacement (longer terms first)
    apparel_replacements = [
        'tshirts', 't-shirts', 'tank tops', 'tanktops',
        'tshirt', 't-shirt', 'tanktop', 'tank top', 'shirt', 'tee', 'merch'
    ]
    core_concept = kw_lower
    for term in apparel_replacements:
        pattern = r'\b' + re.escape(term) + r'\b'
        core_concept = re.sub(pattern, '', core_concept)

    core_concept = ' '.join(core_concept.split()).strip().title()
    if not core_concept:
        core_concept = keyword.title()

    if is_ip_infringing(keyword):
        return (
            f"High trending interest around '{core_concept}'. Likely trademarked/copyrighted entity or brand. "
            f"Avoid direct copy of trademarked logos or official artwork. Consider original parody, aesthetic inspiration, "
            f"or general niche theme if legally compliant."
        )

    return (
        f"Rising search demand for '{core_concept}'. Excellent POD niche opportunity! "
        f"Idea: Create a bold graphic typography or vintage-style illustration centered around '{core_concept}'. "
        f"Target audience is actively searching for apparel options."
    )

def fetch_rising_queries():
    """
    Fetches rising queries for seed keywords from Google Trends with retry logic and rate limit handling.
    """
    pytrends = TrendReq(hl='en-US', tz=360)
    opportunities = []
    seen_keywords = set()

    for seed in SEED_KEYWORDS:
        print(f"Fetching trends for seed: '{seed}'...")
        tries = 0
        df_rising = None

        while tries < 3:
            try:
                pytrends.build_payload([seed], cat=0, timeframe='now 7-d', geo='', gprop='')
                related = pytrends.related_queries()
                if seed in related and related[seed]['rising'] is not None:
                    df_rising = related[seed]['rising']
                break
            except Exception as e:
                print(f"  Attempt {tries + 1} failed for seed '{seed}': {e}")
                tries += 1
                time.sleep(10)

        if df_rising is None or df_rising.empty:
            print(f"  No rising queries found for '{seed}'.")
            time.sleep(5)
            continue

        for _, row in df_rising.iterrows():
            query = str(row['query']).strip()
            score_val = row['value']
            query_lower = query.lower()

            # Filter conditions
            if query_lower in seen_keywords:
                continue
            if query_lower in EXACT_IGNORE_TERMS:
                continue
            if len(query_lower.split()) < 2:
                continue
            if not any(app in query_lower for app in APPAREL_KEYWORDS):
                continue
            if any(sub in query_lower for sub in EXCLUDE_SUBSTRINGS):
                continue

            seen_keywords.add(query_lower)

            # Process score
            if str(score_val).strip().lower() == 'breakout':
                num_score = 9999
                score_str = "Breakout"
            else:
                try:
                    num_score = int(score_val)
                    score_str = f"+{num_score}%"
                except (ValueError, TypeError):
                    num_score = 0
                    score_str = str(score_val)

            idea = generate_idea(query)
            is_ip = is_ip_infringing(query)

            opportunities.append({
                'keyword': query,
                'score_num': num_score,
                'score_str': score_str,
                'why_idea': idea,
                'is_ip': is_ip
            })

        time.sleep(5)

    return opportunities

def sort_opportunities(opps):
    """
    Sorts opportunities by score descending.
    """
    return sorted(opps, key=lambda x: x['score_num'], reverse=True)

def generate_markdown_section(date_str, sorted_opps):
    """
    Formats the opportunities into a Markdown section with tables for General and IP Infringing categories.
    """
    general_opps = [o for o in sorted_opps if not o['is_ip']]
    ip_opps = [o for o in sorted_opps if o['is_ip']]

    lines = [f"## {date_str}", ""]

    lines.append("### General Merch Opportunities")
    if general_opps:
        lines.append("| Keyword | Score | Why / Idea / Market Context |")
        lines.append("|---|---|---|")
        for o in general_opps:
            lines.append(f"| {o['keyword']} | {o['score_str']} | {o['why_idea']} |")
    else:
        lines.append("_No general merch opportunities detected today._")

    lines.append("")
    lines.append("### Potential IP Infringing Opportunities")
    if ip_opps:
        lines.append("| Keyword | Score | Why / Idea / Market Context |")
        lines.append("|---|---|---|")
        for o in ip_opps:
            lines.append(f"| {o['keyword']} | {o['score_str']} | {o['why_idea']} |")
    else:
        lines.append("_No potential IP infringing opportunities detected today._")

    lines.append("")
    return "\n".join(lines)

def update_trends_markdown(file_path, new_section_md, date_str):
    """
    Prepends the new daily section into trends.md below the main header.
    Prevents duplicate section insertion for the same date.
    """
    main_header = "# Google Trends Merch Opportunities"

    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = f"{main_header}\n\n"

    # Avoid duplicate entry for the same date header
    if f"## {date_str}" in content:
        print(f"Data for date {date_str} already exists in {file_path}. Skipping prepending.")
        return

    if main_header in content:
        parts = content.split(main_header, 1)
        updated_content = parts[0] + main_header + "\n\n" + new_section_md + "\n" + parts[1].lstrip()
    else:
        updated_content = f"{main_header}\n\n{new_section_md}\n\n" + content

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)

def main():
    today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    print(f"Starting Google Trends crawl for {today_str}...")

    opps = fetch_rising_queries()
    sorted_opps = sort_opportunities(opps)

    markdown_section = generate_markdown_section(today_str, sorted_opps)
    update_trends_markdown('trends.md', markdown_section, today_str)

    print(f"Crawl completed successfully. Updated trends.md for {today_str}.")

if __name__ == "__main__":
    main()
