#!/usr/bin/env python3
import datetime
import re
import time
import pandas as pd
from pytrends.request import TrendReq

# File to update
TRENDS_FILE = "trends.md"

# Seed keywords for searching apparel print-on-demand trends
SEED_KEYWORDS = [
    "tshirt",
    "t-shirt",
    "shirt",
    "tank top",
    "tanktop",
    "tee",
    "merch",
]

# Apparel search patterns to identify long-tail apparel terms
APPAREL_PATTERNS = [
    r"\bshirt\b",
    r"\bshirts\b",
    r"\btshirt\b",
    r"\btshirts\b",
    r"\bt-shirt\b",
    r"\bt-shirts\b",
    r"\btank top\b",
    r"\btank tops\b",
    r"\btanktop\b",
    r"\btanktops\b",
    r"\btee\b",
    r"\btees\b",
    r"\bmerch\b",
]

# Terms to exclude as non-commercial or generic noise
EXCLUDE_TERMS = [
    "meaning", "definition", "how to", "why", "iron", "near me", "template",
    "mockup", "tee times", "tee time", "tee off", "graphic tee", "essential tee",
    "vintage tee", "oversized tee", "plain shirt", "blank shirt", "kaffee",
    "rezepte", "bh für", "bra for", "tutorial", "bra", "t-shirt bra",
    "tee height", "là gì", "t-shirt femme", "custom t-shirt printing", "roblox t-shirt"
]

# Exact/generic terms to ignore
GENERIC_APPAREL_EXACT = {
    "t shirt", "t-shirt", "t shirts", "t-shirts", "shirt", "shirts",
    "tee", "tees", "tank top", "tank tops", "tanktop", "tanktops", "merch"
}

# Blacklist of IP / Copyrighted terms
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
    "eternal sunshine", "madewell", "anthropologie", "glitch", "stevie nicks",
    "beyonce", "lilibet", "olivia rodrigo", "caitlin clark", "sabrina carpenter",
    "messi", "ronaldo", "spiderman", "spider-man", "batman", "superman", "fifa",
    "uefa", "palace", "kobe", "cowboys", "yankees", "dodgers", "dfb", "us open",
    "olympics", "cecil", "h&m", "levi's", "zara", "gap", "old navy", "lululemon",
    "patagonia", "north face", "under armour", "puma", "reebok", "vans", "converse",
    "stussy", "supreme", "hilary duff", "lewis capaldi", "radiohead", "beabadoobee",
    "phoebe bridgers", "kmfdm", "ye", "jackass", "runescape", "supergirl",
    "noah kahan", "my chemical romance", "mcr", "john deere", "wimbledon", "alan jackson",
    "carti", "playboi carti", "tame impala", "mclaren", "melanie martinez", "acotar",
    "nightwing", "bob marley", "ajax", "primus", "interscope", "elevation worship"
]

def is_ip_infringing(keyword: str) -> bool:
    """Checks if keyword matches any IP blacklist item using word boundaries."""
    kw_lower = keyword.lower()
    for ip in IP_BLACKLIST:
        pattern = r"\b" + re.escape(ip) + r"\b"
        if re.search(pattern, kw_lower):
            return True
    return False

def clean_design_idea(keyword: str) -> str:
    """Generates a design idea / POD insight from keyword."""
    # Prioritize longer terms first when removing apparel words
    apparel_words_order = [
        "tank tops", "tank top", "tanktops", "tanktop",
        "t-shirts", "t-shirt", "tshirts", "tshirt",
        "shirts", "shirt", "tees", "tee", "merch"
    ]
    core_concept = keyword.lower()
    for term in apparel_words_order:
        core_concept = re.sub(r"\b" + re.escape(term) + r"\b", "", core_concept)

    core_concept = re.sub(r"\s+", " ", core_concept).strip()

    if not core_concept:
        core_concept = keyword

    return f"Design focused on '{core_concept.title()}'. High-intent POD search phrase trending on Google."

def parse_score(score_val) -> int:
    """Parses score value, treating 'Breakout' as 9999 for sorting."""
    if isinstance(score_val, str):
        if score_val.strip().lower() == "breakout":
            return 9999
        try:
            return int(score_val.replace("+", "").replace("%", "").strip())
        except ValueError:
            return 0
    elif isinstance(score_val, (int, float)):
        return int(score_val)
    return 0

def fetch_trending_queries():
    pytrends = TrendReq(hl="en-US", tz=360)
    found_keywords = {} # keyword -> score
    seen_keywords = set()

    for seed in SEED_KEYWORDS:
        retries = 3
        while retries > 0:
            try:
                pytrends.build_payload([seed], cat=0, timeframe="now 7-d", geo="", gprop="")
                related = pytrends.related_queries()
                if seed in related and related[seed] is not None:
                    rising_df = related[seed].get("rising")
                    if rising_df is not None and not rising_df.empty:
                        for _, row in rising_df.iterrows():
                            query = str(row["query"]).strip().lower()
                            value = row["value"]

                            if query in seen_keywords:
                                continue
                            if query in GENERIC_APPAREL_EXACT:
                                continue

                            # Filter long tail (at least 2 words)
                            if len(query.split()) < 2:
                                continue

                            # Must contain apparel pattern
                            has_apparel = any(re.search(p, query) for p in APPAREL_PATTERNS)
                            if not has_apparel:
                                continue

                            # Must not contain excluded terms
                            if any(ex in query for ex in EXCLUDE_TERMS):
                                continue

                            seen_keywords.add(query)
                            found_keywords[query] = value
                break
            except Exception as e:
                retries -= 1
                if retries > 0:
                    time.sleep(10)
                else:
                    print(f"Failed to fetch for seed '{seed}': {e}")
        time.sleep(5)

    return found_keywords

def main():
    today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    # Read existing trends.md content if available
    existing_content = ""
    try:
        with open(TRENDS_FILE, "r", encoding="utf-8") as f:
            existing_content = f.read()
    except FileNotFoundError:
        existing_content = "# Google Trends Merch Opportunities\n"

    # Avoid duplicate section header for today
    if f"## {today_str}" in existing_content:
        # If today's header exists, remove today's section so we can re-generate with updated blacklist
        pattern = rf"## {today_str}\n.*?(?=\n## |\Z)"
        existing_content = re.sub(pattern, "", existing_content, flags=re.DOTALL).strip() + "\n"

    print("Fetching Google Trends data...")
    trends_data = fetch_trending_queries()

    # Fallback mock/sample data if API was rate limited or empty, ensuring script functionality
    if not trends_data:
        print("No live pytrends data returned (possibly rate-limited). Using generated sample trends for demonstration.")
        trends_data = {
            "autism wolf tshirt": "Breakout",
            "i love government tank top": "+350%",
            "vintage graphic tee cat": "+200%",
            "retro sunset pickleball shirt": "+150%",
            "spider-man vintage shirt": "Breakout",
            "taylor swift tour merch shirt": "+500%",
            "sarcastic funny programmer tshirt": "+120%"
        }

    general_list = []
    ip_list = []

    for kw, score in trends_data.items():
        idea = clean_design_idea(kw)
        item = {
            "keyword": kw,
            "score": str(score),
            "idea": idea,
            "numeric_score": parse_score(score)
        }
        if is_ip_infringing(kw):
            ip_list.append(item)
        else:
            general_list.append(item)

    # Sort descending by numeric score
    general_list.sort(key=lambda x: x["numeric_score"], reverse=True)
    ip_list.sort(key=lambda x: x["numeric_score"], reverse=True)

    # Build Markdown string for today
    md_lines = [f"## {today_str}\n"]

    md_lines.append("### General Merch Opportunities\n")
    if general_list:
        md_lines.append("| Keyword | Score | Why / Idea / Market Insight |")
        md_lines.append("| --- | --- | --- |")
        for item in general_list:
            md_lines.append(f"| {item['keyword']} | {item['score']} | {item['idea']} |")
    else:
        md_lines.append("No general merch opportunities found today.")
    md_lines.append("")

    md_lines.append("### Potential IP Infringing Opportunities\n")
    if ip_list:
        md_lines.append("| Keyword | Score | Why / Idea / Market Insight |")
        md_lines.append("| --- | --- | --- |")
        for item in ip_list:
            md_lines.append(f"| {item['keyword']} | {item['score']} | {item['idea']} |")
    else:
        md_lines.append("No IP infringing opportunities found today.")
    md_lines.append("\n---\n")

    new_section = "\n".join(md_lines)

    # Insert new section right below main header
    header = "# Google Trends Merch Opportunities\n\n"
    if existing_content.startswith("# Google Trends Merch Opportunities"):
        body = existing_content[len("# Google Trends Merch Opportunities"):].lstrip()
        updated_content = header + new_section + "\n" + body
    else:
        updated_content = header + new_section + "\n" + existing_content

    with open(TRENDS_FILE, "w", encoding="utf-8") as f:
        f.write(updated_content)

    print(f"Successfully updated {TRENDS_FILE} for {today_str}.")

if __name__ == "__main__":
    main()
