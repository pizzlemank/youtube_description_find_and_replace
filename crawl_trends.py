import os
import re
import time
import datetime
import pandas as pd
from pytrends.request import TrendReq

# Seed keywords for Google Trends query
SEED_KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]

# Exact generic phrases to exclude if query is equal to them
EXACT_GENERIC_TERMS = [
    "t shirt", "t-shirt", "t-shirts", "tshirts", "shirts", "tank tops", "tees", "shirt", "tee", "tanktop", "tank top", "merch"
]

# Non-commercial or irrelevant phrases to exclude if present in query
NON_COMMERCIAL_TERMS = [
    "meaning", "definition", "how to", "why", "iron", "near me", "template",
    "mockup", "tee times", "tee time", "tee off", "graphic tee", "essential tee",
    "vintage tee", "oversized tee", "plain shirt", "blank shirt", "kaffee",
    "rezepte", "bh für", "bra for", "tutorial", "bra", "t-shirt bra", "tee height",
    "là gì", "t-shirt femme", "custom t-shirt printing", "roblox t-shirt"
]

# Blacklist terms for identifying IP infringement risks
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
    "madewell", "anthropologie", "glitch", "stevie nicks", "beyonce", "lilibet",
    "olivia rodrigo", "caitlin clark", "sabrina carpenter", "messi", "ronaldo",
    "spiderman", "spider-man", "batman", "superman", "fifa", "uefa", "palace",
    "kobe", "cowboys", "yankees", "dodgers", "dfb", "us open", "olympics", "cecil",
    "h&m", "levi's", "levis", "zara", "gap", "old navy", "lululemon", "patagonia",
    "north face", "under armour", "puma", "reebok", "vans", "converse", "stussy",
    "supreme", "hilary duff", "lewis capaldi", "radiohead", "beabadoobee",
    "phoebe bridgers", "kmfdm", "ye", "jackass", "runescape", "supergirl",
    "noah kahan", "my chemical romance", "mcr", "john deere", "wimbledon", "alan jackson"
]

def parse_score(score_val):
    """Converts a Google Trends score to an integer for sorting."""
    score_str = str(score_val).strip()
    if score_str.lower() == "breakout":
        return 9999
    try:
        clean_val = re.sub(r"[^\d]", "", score_str)
        return int(clean_val) if clean_val else 0
    except (ValueError, TypeError):
        return 0

def is_ip_infringing(keyword):
    """Checks if keyword contains IP blacklisted brand or trademark using word boundaries."""
    keyword_lower = keyword.lower()
    for ip in IP_BLACKLIST:
        pattern = r"\b" + re.escape(ip) + r"\b"
        if re.search(pattern, keyword_lower):
            return True
    return False

def generate_idea(keyword):
    """Generates design ideas/explanations for a trend keyword."""
    subject = keyword.lower()
    apparel_terms_sorted = ["tank tops", "tanktop", "tank top", "t-shirts", "tshirts", "t-shirt", "tshirt", "shirts", "shirt", "tees", "tee", "merch"]
    for term in apparel_terms_sorted:
        subject = re.sub(r"\b" + re.escape(term) + r"\b", "", subject)
    subject = re.sub(r"\s+", " ", subject).strip()

    if not subject:
        subject = keyword.title()
    else:
        subject = subject.title()

    if is_ip_infringing(keyword):
        return (f"Popular search related to trademarked term '{subject}'. "
                f"High search demand on POD platforms, but check copyright/trademark licensing before listing.")
    else:
        return (f"Trending search niche centered around '{subject}'. "
                f"Design idea: Bold typography or retro graphics featuring '{subject}' "
                f"to capitalize on current viral interest on Etsy/Amazon/Redbubble.")

def is_valid_keyword(keyword):
    """Validates long-tail structure and excludes generic/unwanted terms."""
    kw_lower = keyword.lower().strip()
    words = kw_lower.split()

    # Must be long tail (2+ words)
    if len(words) < 2:
        return False

    # Exclude exact generic phrases
    if kw_lower in EXACT_GENERIC_TERMS:
        return False

    # Check for non-commercial or irrelevant phrases
    for exc in NON_COMMERCIAL_TERMS:
        pattern = r"\b" + re.escape(exc) + r"\b"
        if re.search(pattern, kw_lower):
            return False

    # Must contain apparel indicator keyword
    apparel_indicators = ["shirt", "tshirt", "t-shirt", "tank top", "tanktop", "tee", "merch"]
    if not any(re.search(r"\b" + re.escape(ind) + r"\b", kw_lower) for ind in apparel_indicators):
        return False

    return True

def fetch_trending_queries():
    """Fetches rising related queries from Google Trends with custom retry logic."""
    pytrends = TrendReq(hl="en-US", tz=360)
    seen_keywords = set()
    opportunities = []

    for seed in SEED_KEYWORDS:
        retries = 3
        while retries > 0:
            try:
                pytrends.build_payload([seed], cat=0, timeframe="now 7-d", geo="", gprop="")
                related = pytrends.related_queries()
                if seed in related and related[seed]["rising"] is not None:
                    df = related[seed]["rising"]
                    for _, row in df.iterrows():
                        kw = str(row["query"]).strip()
                        score = row["value"]

                        if kw in seen_keywords:
                            continue

                        if is_valid_keyword(kw):
                            seen_keywords.add(kw)
                            opportunities.append({
                                "keyword": kw,
                                "score": score,
                                "score_num": parse_score(score),
                                "is_ip": is_ip_infringing(kw),
                                "why_idea": generate_idea(kw)
                            })
                break
            except Exception as e:
                print(f"Error fetching for seed '{seed}': {e}. Retrying in 10s...")
                retries -= 1
                time.sleep(10)

        # Pause between seed queries to minimize rate limiting
        time.sleep(5)

    return opportunities

def format_markdown_table(items):
    """Formats a list of opportunity items as a Markdown table."""
    if not items:
        return "_No new opportunities found for this category today._\n"

    table_lines = [
        "| Keyword | Score | Why / Design Idea / Market Context |",
        "| --- | --- | --- |"
    ]
    for item in items:
        kw = item["keyword"].replace("|", "\\|")
        score = str(item["score"]).replace("|", "\\|")
        why = item["why_idea"].replace("|", "\\|")
        table_lines.append(f"| {kw} | {score} | {why} |")

    return "\n".join(table_lines) + "\n"

def update_trends_markdown(opportunities):
    """Prepends new date entry into trends.md under main title."""
    filename = "trends.md"
    today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    # Sort opportunities descending by score
    general_opps = sorted([op for op in opportunities if not op["is_ip"]], key=lambda x: x["score_num"], reverse=True)
    ip_opps = sorted([op for op in opportunities if op["is_ip"]], key=lambda x: x["score_num"], reverse=True)

    new_section = f"## {today_str}\n\n"
    new_section += "### General Merch Opportunities\n"
    new_section += format_markdown_table(general_opps) + "\n"
    new_section += "### Potential IP Infringing Opportunities\n"
    new_section += format_markdown_table(ip_opps) + "\n"

    title_header = "# Google Trends Merch Opportunities\n\n"

    existing_content = ""
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            existing_content = f.read()

    # Overwrite today's section if updating or replace
    if f"## {today_str}" in existing_content:
        # Simple reset of file for clean update
        existing_content = re.sub(rf"## {today_str}.*?(?=(## \d{{4}}-\d{{2}}-\d{{2}}|$))", "", existing_content, flags=re.DOTALL)

    if existing_content.startswith("# Google Trends Merch Opportunities"):
        body = existing_content[len(title_header):]
        updated_content = title_header + new_section + body
    else:
        updated_content = title_header + new_section + existing_content

    with open(filename, "w", encoding="utf-8") as f:
        f.write(updated_content)

    print(f"Successfully updated {filename} with latest trends.")

def main():
    print("Starting Google Trends merch crawl...")
    opps = fetch_trending_queries()
    print(f"Found {len(opps)} total valid opportunities.")
    update_trends_markdown(opps)

if __name__ == "__main__":
    main()
