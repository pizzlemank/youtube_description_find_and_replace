import time
import datetime
import re
import os
import pandas as pd
from pytrends.request import TrendReq

# Seed keywords to query
SEED_KEYWORDS = ['tshirt', 't-shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch']

# Apparel terms for filtering long-tail keywords
APPAREL_TERMS = ['shirt', 'tshirt', 't-shirt', 'tank top', 'tanktop', 'tee', 'merch']

# Excluded non-commercial or generic search terms
EXCLUDED_TERMS = [
    'meaning', 'definition', 'how to', 'why', 'iron', 'near me', 'template', 'mockup',
    'tee times', 'tee time', 'tee off', 'graphic tee', 'essential tee', 'vintage tee',
    'oversized tee', 'plain shirt', 'blank shirt', 'kaffee', 'rezepte', 'bh für',
    'bra for', 'tutorial', 'bra', 't-shirt bra', 'tee height', 'là gì', 't-shirt femme',
    'custom t-shirt printing', 'roblox t-shirt'
]

# Exact matches or generic seed variations to filter out
GENERIC_EXACT = [
    't shirt', 't-shirt', 'tshirt', 't shirts', 't-shirts', 'tshirts',
    'shirt', 'shirts', 'tee', 'tees', 'tank top', 'tank tops', 'tanktop',
    'tanktops', 'merch'
]

# IP Blacklist terms for regex matching with word boundaries
IP_BLACKLIST = [
    'disney', 'marvel', 'star wars', 'nike', 'adidas', 'taylor swift', 'bts',
    'michael jackson', 'nba', 'wnba', 'nfl', 'mlb', 'nhl', 'nintendo', 'pokemon',
    'harry potter', 'nasa', 'hellstar', 'ysl', 'gucci', 'prada', 'louis vuitton',
    'arsenal', 'real madrid', 'liverpool', 'man city', 'chelsea', 'bayern', 'barcelona',
    'knicks', 'lakers', 'celtics', 'warriors', 'bulls', 'amiri', 'trapstar', 'corteiz',
    'sp5der', 'minus two', 'syna world', 'harry styles', 'gracie abrams', 'daniel caesar',
    'bad bunny', 'billie eilish', 'drake', 'kanye', 'travis scott', 'bruno mars',
    'hello kitty', 'sanrio', 'nascar', 'f1', 'mercedes', 'ferrari', 'red bull',
    'toy story', 'psg', 'asap rocky', 'megan moroney', 'sean john', 'morgan wallen',
    'spurs', 'rcb', 'snipes', 'asos', 'pattie gonia', 'wingstop', 'ariana grande',
    'selena gomez', 'carhartt', 'hazbin hotel', 'digital circus', 'tadc', 'linkin park',
    'bad omens', 'forrest frank', 'malcolm todd', 'böhse onkelz', 'love island',
    'eternal sunshine', 'madewell', 'anthropologie', 'glitch', 'stevie nicks',
    'beyonce', 'lilibet', 'olivia rodrigo', 'caitlin clark', 'sabrina carpenter',
    'messi', 'ronaldo', 'spiderman', 'spider-man', 'batman', 'superman', 'fifa',
    'uefa', 'palace', 'kobe', 'cowboys', 'yankees', 'dodgers', 'dfb', 'us open',
    'olympics', 'cecil', 'h&m', "levi's", 'zara', 'gap', 'old navy', 'lululemon',
    'patagonia', 'north face', 'under armour', 'puma', 'reebok', 'vans', 'converse',
    'stussy', 'supreme', 'hilary duff', 'lewis capaldi', 'radiohead', 'beabadoobee',
    'phoebe bridgers', 'kmfdm', 'ye', 'jackass', 'runescape', 'supergirl',
    'noah kahan', 'my chemical romance', 'mcr', 'john deere', 'wimbledon', 'alan jackson'
]

def is_ip_infringing(keyword):
    """Checks if keyword matches any IP blacklist item using word boundaries."""
    kw_lower = keyword.lower()
    for ip in IP_BLACKLIST:
        pattern = r'\b' + re.escape(ip) + r'\b'
        if re.search(pattern, kw_lower):
            return True
    return False

def parse_score(val):
    """Parses trend score to an integer value for sorting."""
    if isinstance(val, str):
        if 'breakout' in val.lower():
            return 9999
        try:
            return int(val.replace('+', '').replace('%', '').strip())
        except ValueError:
            return 0
    elif isinstance(val, (int, float)):
        return int(val)
    return 0

def format_score(val):
    """Formats score for display in table."""
    if isinstance(val, str) and 'breakout' in val.lower():
        return 'Breakout'
    score_num = parse_score(val)
    if score_num == 9999:
        return 'Breakout'
    return f"+{score_num}%" if score_num > 0 else str(score_num)

def generate_idea(keyword, is_ip):
    """Generates a why / design idea / market explanation for a keyword."""
    kw_clean = keyword.lower()
    # Replace longer terms first
    replacements = ['t-shirts', 'tshirts', 't-shirt', 'tshirt', 'tank tops', 'tank top', 'tanktops', 'tanktop', 'shirts', 'shirt', 'tees', 'tee', 'merch']
    core_concept = kw_clean
    for r in replacements:
        core_concept = re.sub(r'\b' + re.escape(r) + r'\b', '', core_concept)
    core_concept = re.sub(r'\s+', ' ', core_concept).strip().title()

    if not core_concept:
        core_concept = keyword.title()

    if is_ip:
        return f"High search surge for brand/media '{core_concept}'. Likely trademarked/copyrighted IP. Avoid direct copying; observe fan demand trends or create authorized/original inspired themes."
    else:
        return f"Rising demand for '{core_concept}'. Great POD opportunity: create clean vector graphic or typography design featuring '{core_concept}' on t-shirts and tank tops."

def fetch_rising_queries():
    """Fetches rising queries from Google Trends for seed keywords."""
    pytrends = TrendReq(hl='en-US', tz=360)
    all_results = []
    seen_keywords = set()

    for seed in SEED_KEYWORDS:
        print(f"Fetching trends for seed: '{seed}'...")
        retries = 3
        df_rising = None

        for attempt in range(retries):
            try:
                pytrends.build_payload([seed], cat=0, timeframe='now 7-d', geo='', gprop='')
                related = pytrends.related_queries()
                if seed in related and related[seed]['rising'] is not None:
                    df_rising = related[seed]['rising']
                break
            except Exception as e:
                print(f"Attempt {attempt + 1} failed for '{seed}': {e}")
                if attempt < retries - 1:
                    print("Pausing 10s before retry...")
                    time.sleep(10)
                else:
                    print(f"Skipping seed '{seed}' due to repeated errors.")

        if df_rising is not None and not df_rising.empty:
            for _, row in df_rising.iterrows():
                query = str(row['query']).strip()
                val = row['value']
                q_lower = query.lower()

                # Deduplication check
                if q_lower in seen_keywords:
                    continue

                # Must contain at least 2 words (long tail)
                words = q_lower.split()
                if len(words) < 2:
                    continue

                # Must contain apparel term
                if not any(app in q_lower for app in APPAREL_TERMS):
                    continue

                # Must not contain excluded non-commercial/generic terms
                if any(ex in q_lower for ex in EXCLUDED_TERMS):
                    continue

                # Must not be exact generic match
                if q_lower in GENERIC_EXACT:
                    continue

                seen_keywords.add(q_lower)
                ip_flag = is_ip_infringing(query)
                score_num = parse_score(val)
                score_str = format_score(val)
                idea = generate_idea(query, ip_flag)

                all_results.append({
                    'keyword': query,
                    'score_num': score_num,
                    'score_str': score_str,
                    'is_ip': ip_flag,
                    'idea': idea
                })

        time.sleep(5)

    return all_results

def update_trends_markdown(results):
    """Updates trends.md with new data, maintaining chronological order."""
    today_str = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')
    date_header = f"## {today_str}"

    general_items = [r for r in results if not r['is_ip']]
    ip_items = [r for r in results if r['is_ip']]

    # Sort descending by score
    general_items.sort(key=lambda x: x['score_num'], reverse=True)
    ip_items.sort(key=lambda x: x['score_num'], reverse=True)

    def build_table(items):
        if not items:
            return "_No trending items found for this category today._\n\n"
        table = "| Keyword | Score | Why / Idea / Market |\n| --- | --- | --- |\n"
        for item in items:
            table += f"| {item['keyword']} | {item['score_str']} | {item['idea']} |\n"
        return table + "\n"

    new_section = f"{date_header}\n\n"
    new_section += "### General Merch Opportunities\n"
    new_section += build_table(general_items)
    new_section += "### Potential IP Infringing Opportunities\n"
    new_section += build_table(ip_items)

    main_header = "# Google Trends Merch Opportunities\n\n"

    existing_content = ""
    if os.path.exists("trends.md"):
        with open("trends.md", "r", encoding="utf-8") as f:
            existing_content = f.read()

    if existing_content.startswith("# Google Trends Merch Opportunities"):
        body = existing_content[len(main_header):]
    else:
        body = existing_content

    # Filter out today's section if present in existing body to avoid duplicate sections
    if date_header in body:
        sections = re.split(r'\n(?=## \d{4}-\d{2}-\d{2})', '\n' + body)
        filtered_sections = []
        for sec in sections:
            sec_clean = sec.strip()
            if not sec_clean:
                continue
            if sec_clean.startswith(date_header):
                continue
            filtered_sections.append(sec_clean)
        body = "\n\n".join(filtered_sections)
        if body:
            body = "\n\n" + body
    else:
        body = body.lstrip()

    updated_content = main_header + new_section + body

    with open("trends.md", "w", encoding="utf-8") as f:
        f.write(updated_content)

    print("Successfully updated trends.md!")

if __name__ == "__main__":
    results = fetch_rising_queries()
    print(f"Total relevant opportunities found: {len(results)}")
    update_trends_markdown(results)
