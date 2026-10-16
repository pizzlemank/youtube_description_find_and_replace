import re
import time
import datetime
import pandas as pd
from pytrends.request import TrendReq

# Seed keywords to discover rising merch trends
SEED_KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]

# Apparel terms required for matching
APPAREL_TERMS = ["shirt", "tshirt", "t-shirt", "tank top", "tanktop", "tee", "merch"]

# Exact generic terms to exclude
EXACT_GENERIC_TERMS = {
    "t shirt", "t-shirt", "tshirt", "t shirts", "t-shirts", "tshirts",
    "shirt", "shirts", "tee", "tees", "tank top", "tank tops", "tanktop",
    "tanktops", "merch", "graphic tee", "essential tee", "vintage tee",
    "oversized tee", "plain shirt", "blank shirt"
}

# Non-commercial / irrelevant phrases to exclude
EXCLUDED_KEYWORDS = [
    "meaning", "definition", "how to", "why", "iron", "near me", "template",
    "mockup", "tee times", "tee time", "tee off", "graphic tee", "essential tee",
    "vintage tee", "oversized tee", "plain shirt", "blank shirt", "kaffee",
    "rezepte", "bh für", "bra for", "tutorial", "bra", "t-shirt bra", "tee height",
    "là gì", "t-shirt femme", "custom t-shirt printing", "roblox t-shirt"
]

# Comprehensive IP Blacklist
IP_BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "taylor swift", "bts",
    "michael jackson", "nba", "wnba", "nfl", "mlb", "nhl", "nintendo", "pokemon",
    "harry potter", "nasa", "hellstar", "ysl", "gucci", "prada", "louis vuitton",
    "arsenal", "real madrid", "liverpool", "man city", "chelsea", "bayern",
    "barcelona", "knicks", "lakers", "celtics", "warriors", "bulls", "amiri",
    "trapstar", "corteiz", "sp5der", "minus two", "syna world", "harry styles",
    "gracie abrams", "daniel caesar", "bad bunny", "billie eilish", "drake",
    "kanye", "travis scott", "bruno mars", "hello kitty", "sanrio", "nascar",
    "f1", "mercedes", "ferrari", "red bull", "toy story", "psg", "asap rocky",
    "megan moroney", "sean john", "morgan wallen", "spurs", "rcb", "snipes",
    "asos", "pattie gonia", "wingstop", "ariana grande", "selena gomez",
    "carhartt", "hazbin hotel", "digital circus", "tadc", "linkin park",
    "bad omens", "forrest frank", "malcolm todd", "böhse onkelz", "love island",
    "eternal sunshine", "madewell", "anthropologie", "glitch", "stevie nicks",
    "beyonce", "lilibet", "olivia rodrigo", "caitlin clark", "sabrina carpenter",
    "messi", "ronaldo", "spiderman", "spider-man", "batman", "superman", "fifa",
    "uefa", "palace", "kobe", "cowboys", "yankees", "dodgers", "dfb", "us open",
    "olympics", "cecil", "h&m", "levi's", "zara", "gap", "old navy", "lululemon",
    "patagonia", "north face", "under armour", "puma", "reebok", "vans",
    "converse", "stussy", "supreme", "hilary duff", "lewis capaldi", "radiohead",
    "beabadoobee", "phoebe bridgers", "kmfdm", "ye", "jackass", "runescape",
    "supergirl", "noah kahan", "my chemical romance", "mcr", "john deere",
    "wimbledon", "alan jackson"
]


def is_ip_infringing(keyword: str) -> bool:
    """Checks if a keyword contains any IP blacklisted term using regex word boundaries."""
    kw_lower = keyword.lower()
    for term in IP_BLACKLIST:
        pattern = r"\b" + re.escape(term.lower()) + r"\b"
        if re.search(pattern, kw_lower):
            return True
    return False


def is_valid_opportunity(keyword: str) -> bool:
    """Filters keywords for long-tail merch potential."""
    kw_lower = keyword.strip().lower()

    # Exact string match check against generic terms
    if kw_lower in EXACT_GENERIC_TERMS:
        return False

    # Check word count (must be 2+ words for long tail)
    words = kw_lower.split()
    if len(words) < 2:
        return False

    # Check excluded phrases
    for excl in EXCLUDED_KEYWORDS:
        if excl in kw_lower:
            return False

    # Must contain at least one apparel term
    has_apparel = any(term in kw_lower for term in APPAREL_TERMS)
    if not has_apparel:
        return False

    return True


def generate_design_idea(keyword: str, is_ip: bool) -> str:
    """Generates design ideas / market context for a keyword."""
    if is_ip:
        return "Popular trending pop culture / IP query. High search volume on marketplaces, but high risk for trademark / copyright infringement."

    # Extract core subject by cleaning apparel words
    clean_concept = keyword.lower()
    # Prioritize longer terms before shorter ones
    replace_terms = [
        "t-shirts", "tank tops", "tshirts", "tank top", "tanktop",
        "t-shirt", "tshirt", "shirts", "shirt", "tees", "tee", "merch"
    ]
    for term in replace_terms:
        clean_concept = re.sub(r"\b" + re.escape(term) + r"\b", "", clean_concept)

    clean_concept = " ".join(clean_concept.split()).title()

    if clean_concept:
        return f"High demand POD niche centered on '{clean_concept}'. Ideal for a bold graphic layout, funny typography, or retro vintage emblem on t-shirts & tank tops."
    else:
        return "Trending search query on Google. Great opportunity for minimalist or targeted niche graphic apparel designs."


def parse_score(val) -> int:
    """Converts Google Trends score into an integer for sorting ('Breakout' = 9999)."""
    if isinstance(val, str):
        if val.strip().lower() == "breakout":
            return 9999
        try:
            # Handle percentage strings like "+500%"
            val_clean = val.replace("+", "").replace("%", "").replace(",", "").strip()
            return int(float(val_clean))
        except ValueError:
            return 0
    elif isinstance(val, (int, float)):
        return int(val)
    return 0


def fetch_trends():
    """Fetches rising queries from Google Trends using pytrends with retries."""
    pytrends = TrendReq(hl="en-US", tz=360)
    results = []
    seen_keywords = set()

    for seed in SEED_KEYWORDS:
        print(f"Fetching Google Trends for seed: {seed}")
        retries = 3
        df_rising = None

        while retries > 0:
            try:
                pytrends.build_payload([seed], cat=0, timeframe="now 7-d", geo="", gprop="")
                related = pytrends.related_queries()
                if seed in related and related[seed]["rising"] is not None:
                    df_rising = related[seed]["rising"]
                break
            except Exception as e:
                print(f"Rate limited or error on '{seed}': {e}. Retrying in 10s...")
                retries -= 1
                time.sleep(10)

        if df_rising is not None and not df_rising.empty:
            for _, row in df_rising.iterrows():
                query = str(row["query"]).strip()
                value = row["value"]

                if query.lower() in seen_keywords:
                    continue

                if is_valid_opportunity(query):
                    seen_keywords.add(query.lower())
                    score_num = parse_score(value)
                    score_str = "Breakout" if score_num == 9999 else (f"+{score_num}%" if score_num > 0 else str(value))
                    ip_flag = is_ip_infringing(query)
                    idea = generate_design_idea(query, ip_flag)

                    results.append({
                        "keyword": query,
                        "score_num": score_num,
                        "score": score_str,
                        "idea": idea,
                        "is_ip": ip_flag
                    })

        # Pause to mitigate rate limiting
        time.sleep(5)

    return results


def format_markdown_table(items):
    """Formats list of items as a Markdown table."""
    if not items:
        return "_No trending items identified for this section today._\n"

    table_lines = [
        "| Keyword | Score | Why / Design Idea / Market Context |",
        "| --- | --- | --- |"
    ]
    for item in items:
        kw = item["keyword"].replace("|", "\\|")
        sc = str(item["score"]).replace("|", "\\|")
        idea = item["idea"].replace("|", "\\|")
        table_lines.append(f"| {kw} | {sc} | {idea} |")

    return "\n".join(table_lines) + "\n"


def update_trends_markdown(results):
    """Prepends new trend results under '# Google Trends Merch Opportunities' in trends.md."""
    today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    # Sort results by score_num descending
    general_items = sorted([r for r in results if not r["is_ip"]], key=lambda x: x["score_num"], reverse=True)
    ip_items = sorted([r for r in results if r["is_ip"]], key=lambda x: x["score_num"], reverse=True)

    today_section = f"## {today_str}\n\n"
    today_section += "### General Merch Opportunities\n\n"
    today_section += format_markdown_table(general_items) + "\n"
    today_section += "### Potential IP Infringing Opportunities\n\n"
    today_section += format_markdown_table(ip_items) + "\n"

    filename = "trends.md"
    existing_content = ""

    try:
        with open(filename, "r", encoding="utf-8") as f:
            existing_content = f.read()
    except FileNotFoundError:
        existing_content = "# Google Trends Merch Opportunities\n\n"

    # Avoid duplicate entry for the exact same date
    if f"## {today_str}" in existing_content:
        print(f"Section for date {today_str} already exists in {filename}. Skipping prepend.")
        return

    header_title = "# Google Trends Merch Opportunities"
    if header_title in existing_content:
        parts = existing_content.split(header_title, 1)
        new_content = header_title + "\n\n" + today_section + parts[1].lstrip("\n")
    else:
        new_content = header_title + "\n\n" + today_section + existing_content

    with open(filename, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"Successfully updated {filename} for {today_str}.")


def main():
    print("Starting Google Trends merch crawl...")
    results = fetch_trends()
    print(f"Found {len(results)} total potential merch opportunities.")
    update_trends_markdown(results)


if __name__ == "__main__":
    main()
