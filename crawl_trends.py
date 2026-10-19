import re
import time
from datetime import datetime
import pandas as pd
from pytrends.request import TrendReq

# List of seed keywords to query Google Trends
SEED_KEYWORDS = ['tshirt', 't-shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch']

# Exclude generic search terms or non-commercial/unrelated queries
EXCLUDE_TERMS = [
    'meaning', 'definition', 'how to', 'why', 'iron', 'near me', 'template',
    'mockup', 'tee times', 'tee time', 'tee off', 'graphic tee', 'essential tee',
    'vintage tee', 'oversized tee', 'plain shirt', 'blank shirt', 'kaffee',
    'rezepte', 'bh für', 'bra for', 'tutorial', 'bra', 't-shirt bra', 'tee height',
    'là gì', 't-shirt femme', 'custom t-shirt printing', 'roblox t-shirt',
    't shirt', 't-shirt', 'tshirt', 'shirts', 'tshirts', 't-shirts', 'tees', 'shirt'
]

# IP Blacklist terms for copyright/trademark infringement checks
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
    'asos', 'pattie gonia', 'wingstop', 'ariana grande', 'selena gomez', 'carhartt',
    'hazbin hotel', 'digital circus', 'tadc', 'linkin park', 'bad omens',
    'forrest frank', 'malcolm todd', 'böhse onkelz', 'love island', 'eternal sunshine',
    'madewell', 'anthropologie', 'glitch', 'stevie nicks', 'beyonce', 'lilibet',
    'olivia rodrigo', 'caitlin clark', 'sabrina carpenter', 'messi', 'ronaldo',
    'spiderman', 'spider-man', 'batman', 'superman', 'fifa', 'uefa', 'palace',
    'kobe', 'cowboys', 'yankees', 'dodgers', 'dfb', 'us open', 'olympics',
    'cecil', 'h&m', "levi's", 'zara', 'gap', 'old navy', 'lululemon',
    'patagonia', 'north face', 'under armour', 'puma', 'reebok', 'vans',
    'converse', 'stussy', 'supreme', 'hilary duff', 'lewis capaldi', 'radiohead',
    'beabadoobee', 'phoebe bridgers', 'kmfdm', 'ye', 'jackass', 'runescape',
    'supergirl', 'noah kahan', 'my chemical romance', 'mcr', 'john deere',
    'wimbledon', 'alan jackson', 'twenty one pilots', 'helluva boss', 'dunkin',
    'fontaines dc', 'calvin harris', 'tate mcrae', 'lizzy mcalpine', 'young miko',
    'elevation worship', 'yeat', 'brewers', 'world series'
]

def is_ip_infringing(keyword: str) -> bool:
    """Check if keyword matches any IP blacklist term using word boundaries."""
    kw_lower = keyword.lower()
    for term in IP_BLACKLIST:
        pattern = r'\b' + re.escape(term) + r'\b'
        if re.search(pattern, kw_lower):
            return True
    return False

def clean_subject(keyword: str) -> str:
    """Extract core topic from apparel search query by replacing apparel terms."""
    cleaned = keyword.lower()
    # Prioritize longer terms first to prevent partial replacements
    apparel_terms = ['t-shirts', 'tshirts', 'tank tops', 'tanktop', 'tank top', 't-shirt', 'tshirt', 'shirts', 'shirt', 'tees', 'tee', 'merch']
    for term in apparel_terms:
        cleaned = re.sub(r'\b' + re.escape(term) + r'\b', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned if cleaned else keyword

def generate_idea(keyword: str, is_ip: bool) -> str:
    """Generate design ideas or opportunity explanation."""
    subject = clean_subject(keyword)
    if is_ip:
        return f"Trending query related to '{subject}'. **Warning: IP/Trademark risk!** Do not copy protected logos/names directly. Look for generic, non-infringing parody or related niche angles if safe."
    else:
        return f"High demand search for '{subject}' apparel. **Idea:** Create unique typography or graphic illustration for '{subject}'. Check current Etsy/Amazon search results for creative inspiration."

def parse_score(value) -> tuple[int, str]:
    """Parse score for sorting (treating Breakout as 9999) and display string."""
    val_str = str(value).strip()
    if 'breakout' in val_str.lower():
        return (9999, 'Breakout')

    # Try parsing numeric value
    clean_num = re.sub(r'[^\d]', '', val_str)
    if clean_num:
        num = int(clean_num)
        return (num, f"+{num}%" if not val_str.startswith('+') and not val_str.endswith('%') else val_str)
    return (0, val_str)

def fetch_rising_queries() -> list[dict]:
    """Fetch rising queries from Google Trends for seed keywords with retry handling."""
    pytrends = TrendReq(hl='en-US', tz=360)
    all_results = []
    seen_keywords = set()

    for seed in SEED_KEYWORDS:
        print(f"Fetching trends for seed: '{seed}'...")
        success = False
        retries = 3

        while retries > 0 and not success:
            try:
                pytrends.build_payload([seed], timeframe='now 7-d', geo='')
                related = pytrends.related_queries()
                if seed in related and related[seed]['rising'] is not None:
                    df = related[seed]['rising']
                    for _, row in df.iterrows():
                        kw = str(row['query']).strip()
                        raw_value = row['value']

                        kw_lower = kw.lower()

                        # Filter long-tail requirements & exclusions
                        words = kw_lower.split()
                        if len(words) < 2:
                            continue

                        # Exclude exact or non-commercial terms
                        if any(ex in kw_lower for ex in EXCLUDE_TERMS):
                            continue

                        if kw_lower in seen_keywords:
                            continue

                        seen_keywords.add(kw_lower)
                        sort_score, score_display = parse_score(raw_value)

                        ip_flag = is_ip_infringing(kw)
                        idea = generate_idea(kw, ip_flag)

                        all_results.append({
                            'keyword': kw,
                            'score_num': sort_score,
                            'score_display': score_display,
                            'why_idea': idea,
                            'is_ip': ip_flag
                        })
                success = True
            except Exception as e:
                print(f"Error fetching '{seed}': {e}. Retrying in 10s...")
                retries -= 1
                time.sleep(10)

        time.sleep(5) # Delay between queries to avoid rate limits

    return all_results

def update_trends_markdown(results: list[dict], filepath: str = 'trends.md'):
    """Format results into markdown and prepend to trends.md chronologically."""
    today_str = datetime.now().strftime('%Y-%m-%d')
    date_header = f"## {today_str}"

    # Sort results by score descending
    results = sorted(results, key=lambda x: x['score_num'], reverse=True)

    general_ops = [r for r in results if not r['is_ip']]
    ip_ops = [r for r in results if r['is_ip']]

    def build_table(items):
        if not items:
            return "_No new opportunities found today._\n"
        lines = ["| Keyword | Score | Why / Idea / Market |", "| --- | --- | --- |"]
        for item in items:
            lines.append(f"| {item['keyword']} | {item['score_display']} | {item['why_idea']} |")
        return "\n".join(lines) + "\n"

    new_content_block = f"{date_header}\n\n"
    new_content_block += "### General Merch Opportunities\n"
    new_content_block += build_table(general_ops) + "\n"
    new_content_block += "### Potential IP Infringing Opportunities\n"
    new_content_block += build_table(ip_ops) + "\n"

    existing_content = ""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            existing_content = f.read()
    except FileNotFoundError:
        pass

    if "# Google Trends Merch Opportunities" not in existing_content:
        full_document = "# Google Trends Merch Opportunities\n\n" + new_content_block
    else:
        # Check if date header already exists to avoid redundant entries on the same day
        if date_header in existing_content:
            print(f"Header '{date_header}' already exists in {filepath}. Replacing date block...")
            # Split document at the date header
            parts = existing_content.split(date_header)
            header_part = parts[0]
            # Find next '## ' header if any
            rest = parts[1]
            next_date_match = re.search(r'\n## ', rest)
            if next_date_match:
                remainder = rest[next_date_match.start():]
            else:
                remainder = ""
            full_document = header_part + new_content_block + remainder
        else:
            # Prepend below main header
            parts = existing_content.split("# Google Trends Merch Opportunities\n", 1)
            full_document = "# Google Trends Merch Opportunities\n\n" + new_content_block + parts[1].lstrip()

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(full_document)
    print(f"Successfully updated {filepath}.")

if __name__ == '__main__':
    print("Starting Google Trends Merch Opportunities Crawlers...")
    trends_data = fetch_rising_queries()
    print(f"Found {len(trends_data)} unique opportunities.")
    update_trends_markdown(trends_data)
