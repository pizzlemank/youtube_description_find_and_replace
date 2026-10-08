#!/usr/bin/env python3
import datetime
import re
import time
import pandas as pd
from pytrends.request import TrendReq

# Seed keywords to discover related queries for POD
SEED_KEYWORDS = [
    "tshirt",
    "t-shirt",
    "shirt",
    "tank top",
    "tanktop",
    "tee",
    "merch",
]

# Words that indicate apparel or merch items
APPAREL_TERMS = [
    "shirt",
    "tshirt",
    "t-shirt",
    "tank top",
    "tanktop",
    "tee",
    "merch",
]

# Irrelevant or non-commercial search phrases to filter out
EXCLUDE_TERMS = [
    "meaning",
    "definition",
    "how to",
    "why",
    "iron",
    "near me",
    "template",
    "mockup",
    "tee times",
    "tee time",
    "tee off",
    "graphic tee",
    "essential tee",
    "vintage tee",
    "oversized tee",
    "plain shirt",
    "blank shirt",
    "kaffee",
    "rezepte",
    "bh für",
    "bra for",
    "tutorial",
    "bra",
    "t-shirt bra",
    "tee height",
    "là gì",
    "t-shirt femme",
    "custom t-shirt printing",
    "roblox t-shirt",
]

# Exact or highly generic apparel terms to ignore
GENERIC_APPAREL_EXACT = {
    "t shirt",
    "t-shirt",
    "tshirt",
    "t-shirts",
    "tshirts",
    "shirt",
    "shirts",
    "tee",
    "tees",
    "tank top",
    "tank tops",
    "tanktop",
    "tanktops",
    "merch",
}

# IP / Trademark / Copyright blacklist terms
IP_BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "taylor swift", "bts",
    "michael jackson", "nba", "wnba", "nfl", "mlb", "nhl", "nintendo", "pokemon",
    "pokémon", "harry potter", "nasa", "hellstar", "ysl", "gucci", "prada",
    "louis vuitton", "arsenal", "real madrid", "liverpool", "man city", "chelsea",
    "bayern", "barcelona", "knicks", "lakers", "celtics", "warriors", "bulls",
    "amiri", "trapstar", "corteiz", "sp5der", "minus two", "syna world",
    "harry styles", "gracie abrams", "daniel caesar", "bad bunny", "billie eilish",
    "drake", "kanye", "travis scott", "bruno mars", "hello kitty", "sanrio",
    "nascar", "f1", "mercedes", "ferrari", "red bull", "toy story", "psg",
    "asap rocky", "megan moroney", "sean john", "morgan wallen", "spurs", "rcb",
    "snipes", "asos", "pattie gonia", "wingstop", "ariana grande", "selena gomez",
    "carhartt", "hazbin hotel", "digital circus", "tadc", "linkin park", "bad omens",
    "forrest frank", "malcolm todd", "böhse onkelz", "love island", "eternal sunshine",
    "madewell", "anthropologie", "glitch", "stevie nicks", "beyonce", "beyoncé",
    "lilibet", "olivia rodrigo", "caitlin clark", "sabrina carpenter", "messi",
    "ronaldo", "spiderman", "spider-man", "batman", "superman", "fifa", "uefa",
    "palace", "kobe", "cowboys", "yankees", "dodgers", "dfb", "us open", "olympics",
    "cecil", "h&m", "levi's", "zara", "gap", "old navy", "lululemon", "patagonia",
    "north face", "under armour", "puma", "reebok", "vans", "converse", "stussy",
    "supreme", "hilary duff", "lewis capaldi", "radiohead", "beabadoobee",
    "phoebe bridgers", "kmfdm", "ye", "jackass", "runescape", "supergirl",
    "noah kahan", "my chemical romance", "mcr", "john deere", "wimbledon", "alan jackson"
]

def is_ip_infringing(keyword: str) -> bool:
    """Check if keyword matches any blacklisted IP using regex word boundaries."""
    kw_lower = keyword.lower()
    for ip in IP_BLACKLIST:
        pattern = r"\b" + re.escape(ip) + r"\b"
        if re.search(pattern, kw_lower):
            return True
    return False

def parse_score(val) -> int:
    """Convert score to integer for sorting, treating Breakout as 9999."""
    if isinstance(val, str):
        if val.strip().lower() == "breakout":
            return 9999
        try:
            val = val.replace("+", "").replace("%", "").strip()
            return int(val)
        except ValueError:
            return 0
    elif isinstance(val, (int, float)):
        return int(val)
    return 0

def generate_idea(keyword: str, score_str: str) -> str:
    """Generate design concept / market reasoning for a keyword."""
    # Clean up apparel terms to isolate core subject
    core_concept = keyword.lower()
    replacements = [
        "t-shirts", "tshirts", "t-shirt", "tshirt",
        "tank tops", "tanktop", "tank top",
        "graphic tees", "graphic tee", "shirts", "shirt",
        "tees", "tee", "merch"
    ]
    for rep in replacements:
        pattern = re.compile(re.escape(rep), re.IGNORECASE)
        core_concept = pattern.sub("", core_concept)
    core_concept = re.sub(r"\s+", " ", core_concept).strip()
    if not core_concept:
        core_concept = keyword

    if score_str == "Breakout" or score_str == "9999":
        trend_desc = "Breakout search interest (+1000%+ surge)."
    else:
        trend_desc = f"Rising trend ({score_str})."

    return (
        f"{trend_desc} Concept: '{core_concept.title()}' graphic/text artwork. "
        f"High demand on POD platforms (Amazon Merch, Etsy, Redbubble) for niche fans/buyers."
    )

def fetch_trends():
    """Fetch related queries from Google Trends."""
    pytrend = TrendReq(hl="en-US", tz=360)
    seen_keywords = set()
    general_opportunities = []
    ip_opportunities = []

    for seed in SEED_KEYWORDS:
        print(f"Fetching related queries for seed: '{seed}'...")
        retries = 3
        data = None
        for attempt in range(retries):
            try:
                pytrend.build_payload([seed], timeframe="now 7-d")
                data = pytrend.related_queries()
                break
            except Exception as e:
                print(f"  Attempt {attempt + 1} failed for '{seed}': {e}")
                if attempt < retries - 1:
                    print("  Retrying in 10 seconds...")
                    time.sleep(10)

        if not data or seed not in data:
            print(f"  No data retrieved for '{seed}'.")
            time.sleep(5)
            continue

        seed_data = data[seed]
        rising_df = seed_data.get("rising")

        if rising_df is None or rising_df.empty:
            print(f"  No rising queries found for '{seed}'.")
            time.sleep(5)
            continue

        for _, row in rising_df.iterrows():
            query = str(row["query"]).strip()
            score_val = row["value"]

            query_lower = query.lower()

            # Skip exact/generic terms
            if query_lower in GENERIC_APPAREL_EXACT:
                continue

            # Must contain at least 2 words (long-tail)
            words = query_lower.split()
            if len(words) < 2:
                continue

            # Must contain an apparel term
            if not any(apparel in query_lower for apparel in APPAREL_TERMS):
                continue

            # Must not contain excluded non-commercial terms
            if any(ex in query_lower for ex in EXCLUDE_TERMS):
                continue

            # Deduplication
            if query_lower in seen_keywords:
                continue
            seen_keywords.add(query_lower)

            score_num = parse_score(score_val)
            score_display = "Breakout" if score_num == 9999 else (f"+{score_val}%" if isinstance(score_val, int) else str(score_val))

            idea = generate_idea(query, score_display)
            item = {
                "keyword": query,
                "score_num": score_num,
                "score_display": score_display,
                "idea": idea
            }

            if is_ip_infringing(query):
                ip_opportunities.append(item)
            else:
                general_opportunities.append(item)

        time.sleep(5)

    # Sort descending by numeric score
    general_opportunities.sort(key=lambda x: x["score_num"], reverse=True)
    ip_opportunities.sort(key=lambda x: x["score_num"], reverse=True)

    return general_opportunities, ip_opportunities

def update_trends_markdown(general_opps, ip_opps):
    """Write or prepend results to trends.md."""
    today_str = datetime.date.today().isoformat()
    filename = "trends.md"

    # Format Markdown tables
    date_section = f"## {today_str}\n\n"

    date_section += "### General Merch Opportunities\n\n"
    if general_opps:
        date_section += "| Keyword | Score | Why / Design Idea / Market Trend |\n"
        date_section += "| --- | --- | --- |\n"
        for item in general_opps:
            date_section += f"| {item['keyword']} | {item['score_display']} | {item['idea']} |\n"
        date_section += "\n"
    else:
        date_section += "No general merch opportunities found for today.\n\n"

    date_section += "### Potential IP Infringing Opportunities\n\n"
    if ip_opps:
        date_section += "| Keyword | Score | Why / Design Idea / Market Trend |\n"
        date_section += "| --- | --- | --- |\n"
        for item in ip_opps:
            date_section += f"| {item['keyword']} | {item['score_display']} | {item['idea']} |\n"
        date_section += "\n"
    else:
        date_section += "No potential IP infringing opportunities found for today.\n\n"

    header_title = "# Google Trends Merch Opportunities\n\n"

    # Read existing content if trends.md exists
    existing_content = ""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            existing_content = f.read()
    except FileNotFoundError:
        existing_content = ""

    # Parse existing date sections (dated with '## YYYY-MM-DD')
    # Extract any existing sections that start with ## YYYY-MM-DD
    date_blocks = {}
    pattern = r"^## (\d{4}-\d{2}-\d{2})\n\n(.*?)(?=(^## \d{4}-\d{2}-\d{2}\n\n|\Z))"
    matches = re.finditer(pattern, existing_content, re.MULTILINE | re.DOTALL)
    for match in matches:
        sec_date = match.group(1)
        sec_content = match.group(0)
        date_blocks[sec_date] = sec_content

    # Set/Update today's section
    date_blocks[today_str] = date_section

    # Sort dates in descending order (latest to earliest)
    sorted_dates = sorted(date_blocks.keys(), reverse=True)

    new_content = header_title
    for d in sorted_dates:
        new_content += date_blocks[d]

    with open(filename, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"Successfully updated {filename}")

def main():
    print("Starting Google Trends Merch Crawler...")
    general_opps, ip_opps = fetch_trends()
    print(f"Found {len(general_opps)} general opportunities and {len(ip_opps)} potential IP infringing opportunities.")
    update_trends_markdown(general_opps, ip_opps)

if __name__ == "__main__":
    main()
