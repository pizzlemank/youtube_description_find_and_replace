import re
import time
from datetime import datetime, timezone
import pandas as pd
from pytrends.request import TrendReq

# Seed keywords to discover rising queries
SEED_KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]

# Exclude non-commercial, irrelevant, or generic search terms
IRRELEVANT_TERMS = [
    "meaning", "definition", "how to", "why", "iron", "near me", "template", "mockup",
    "tee times", "tee time", "tee off", "graphic tee", "essential tee", "vintage tee",
    "oversized tee", "plain shirt", "blank shirt", "kaffee", "rezepte", "bh für",
    "bra for", "tutorial", "bra", "t-shirt bra", "tee height", "là gì", "t-shirt femme",
    "custom t-shirt printing", "roblox t-shirt"
]

GENERIC_EXACT_MATCHES = [
    "tshirt", "t-shirt", "t shirt", "tshirts", "t-shirts", "t shirts",
    "shirt", "shirts", "tank top", "tank tops", "tanktop", "tanktops",
    "tee", "tees", "merch"
]

# Blacklist of IP / Brand names / Trademarks / Celebrity names
IP_BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "taylor swift", "bts",
    "michael jackson", "nba", "wnba", "nfl", "mlb", "nhl", "nintendo", "pokemon",
    "harry potter", "nasa", "hellstar", "ysl", "gucci", "prada", "louis vuitton",
    "arsenal", "real madrid", "liverpool", "man city", "chelsea", "bayern", "barcelona",
    "knicks", "lakers", "celtics", "warriors", "bulls", "amiri", "trapstar", "corteiz",
    "sp5der", "minus two", "syna world", "harry styles", "gracie abrams", "daniel caesar",
    "bad bunny", "billie eilish", "drake", "kanye", "travis scott", "bruno mars",
    "hello kitty", "sanrio", "nascar", "f1", "mercedes", "ferrari", "red bull",
    "toy story", "psg", "asap rocky", "megan moroney", "sean john", "morgan wallen",
    "spurs", "rcb", "snipes", "asos", "pattie gonia", "wingstop", "ariana grande",
    "selena gomez", "carhartt", "hazbin hotel", "digital circus", "tadc", "linkin park",
    "bad omens", "forrest frank", "malcolm todd", "böhse onkelz", "love island",
    "eternal sunshine", "madewell", "anthropologie", "glitch", "stevie nicks", "beyonce",
    "lilibet", "olivia rodrigo", "caitlin clark", "sabrina carpenter", "messi", "ronaldo",
    "spiderman", "spider-man", "batman", "superman", "fifa", "uefa", "palace", "kobe",
    "cowboys", "yankees", "dodgers", "dfb", "us open", "olympics", "cecil", "h&m",
    "levi's", "zara", "gap", "old navy", "lululemon", "patagonia", "north face",
    "under armour", "puma", "reebok", "vans", "converse", "stussy", "supreme",
    "hilary duff", "lewis capaldi", "radiohead", "beabadoobee", "phoebe bridgers",
    "kmfdm", "ye", "jackass", "runescape", "supergirl", "noah kahan",
    "my chemical romance", "mcr", "john deere", "wimbledon", "alan jackson"
]

def is_ip_infringing(keyword):
    """Check if the keyword contains any IP blacklist terms using whole-word matching."""
    keyword_lower = keyword.lower()
    for ip in IP_BLACKLIST:
        pattern = r'\b' + re.escape(ip) + r'\b'
        if re.search(pattern, keyword_lower):
            return True
    return False

def generate_why_idea(keyword, is_ip):
    """Generate 'Why / Idea' reasoning for the keyword."""
    # Prioritize replacing longer apparel terms before shorter ones
    concept = keyword
    for term in ["tank tops", "tank top", "tanktops", "tanktop", "t-shirts", "tshirts", "t-shirt", "tshirt", "shirts", "shirt", "tees", "tee", "merch"]:
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        concept = pattern.sub("", concept)
    concept = re.sub(r'\s+', ' ', concept).strip()
    if not concept:
        concept = keyword

    if is_ip:
        return f"Trending pop-culture / brand search related to '{concept}'. High search interest but potential trademark / IP risk. Search volume indicates active shoppers."
    else:
        return f"Rising trend for '{concept}'. Design idea: Create stylized typography / graphic illustration centered around '{concept}' targeting niche audiences."

def parse_score(val):
    """Convert score value to integer for sorting. Treat 'Breakout' as 9999."""
    if isinstance(val, str) and 'breakout' in val.lower():
        return 9999
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0

def fetch_trending_queries():
    """Fetch rising queries from Google Trends with retry logic and rate limit handling."""
    pytrend = TrendReq(hl='en-US', tz=360)
    seen_keywords = set()
    general_ops = []
    ip_ops = []

    for seed in SEED_KEYWORDS:
        print(f"Fetching trends for seed keyword: '{seed}'...")
        retries = 3
        while retries > 0:
            try:
                pytrend.build_payload([seed], timeframe='now 7-d')
                related = pytrend.related_queries()
                if seed in related and related[seed]['rising'] is not None:
                    df = related[seed]['rising']
                    for _, row in df.iterrows():
                        query = str(row['query']).strip()
                        value = str(row['value']).strip()

                        query_lower = query.lower()

                        # Must be long-tail (2+ words)
                        if len(query_lower.split()) < 2:
                            continue

                        # Must contain apparel term
                        if not any(term in query_lower for term in ["shirt", "tshirt", "t-shirt", "tank top", "tanktop", "tee", "merch"]):
                            continue

                        # Skip generic exact matches
                        if query_lower in GENERIC_EXACT_MATCHES:
                            continue

                        # Skip irrelevant terms
                        if any(irr in query_lower for irr in IRRELEVANT_TERMS):
                            continue

                        # Deduplicate
                        if query_lower in seen_keywords:
                            continue
                        seen_keywords.add(query_lower)

                        ip_flag = is_ip_infringing(query)
                        why_idea = generate_why_idea(query, ip_flag)

                        entry = {
                            "keyword": query,
                            "score": value,
                            "why": why_idea,
                            "sort_score": parse_score(value)
                        }

                        if ip_flag:
                            ip_ops.append(entry)
                        else:
                            general_ops.append(entry)

                break  # Success, exit retry loop
            except Exception as e:
                print(f"Error fetching for '{seed}': {e}. Retrying in 10s...")
                retries -= 1
                time.sleep(10)

        time.sleep(5)  # Delay between seed queries to avoid rate limits

    # Sort descending by score
    general_ops.sort(key=lambda x: x['sort_score'], reverse=True)
    ip_ops.sort(key=lambda x: x['sort_score'], reverse=True)

    return general_ops, ip_ops

def format_markdown_table(items):
    """Format a list of entries into a Markdown table."""
    if not items:
        return "| Keyword | Score | Why / Idea |\n| --- | --- | --- |\n| *No trends found* | - | - |\n"

    table = "| Keyword | Score | Why / Idea |\n| --- | --- | --- |\n"
    for item in items:
        # Escape pipe characters if any
        kw = item['keyword'].replace("|", "\\|")
        score = item['score'].replace("|", "\\|")
        why = item['why'].replace("|", "\\|")
        table += f"| {kw} | {score} | {why} |\n"
    return table

def update_trends_file(general_ops, ip_ops):
    """Update trends.md prepending new date section under main header."""
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    header_date = f"## {today_str}"

    file_path = "trends.md"
    existing_content = ""

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            existing_content = f.read()
    except FileNotFoundError:
        pass

    # Check if section for today already exists
    if header_date in existing_content:
        print(f"Section for date {today_str} already exists in trends.md. Skipping update.")
        return

    # Build new entry markdown
    new_section = f"{header_date}\n\n"
    new_section += "### General Merch Opportunities\n\n"
    new_section += format_markdown_table(general_ops) + "\n"
    new_section += "### Potential IP Infringing Opportunities\n\n"
    new_section += format_markdown_table(ip_ops) + "\n"

    main_header = "# Google Trends Merch Opportunities\n\n"

    if existing_content.startswith("# Google Trends Merch Opportunities"):
        # Split after main header
        rest = existing_content[len(main_header):].lstrip("\n")
        updated_content = main_header + new_section + rest
    else:
        updated_content = main_header + new_section + existing_content

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(updated_content)

    print(f"Successfully updated {file_path} for {today_str}.")

def main():
    general_ops, ip_ops = fetch_trending_queries()
    update_trends_file(general_ops, ip_ops)

if __name__ == "__main__":
    main()
