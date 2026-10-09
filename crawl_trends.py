import re
import time
import datetime
import os
import pandas as pd
from pytrends.request import TrendReq

# Seed keywords to crawl
SEED_KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]

# Apparel keywords that long-tail terms should contain
APPAREL_TERMS = ["shirt", "tshirt", "t-shirt", "tank top", "tanktop", "tee", "merch"]

# Generic seed / exact match phrases to ignore
EXCLUDE_EXACT = {
    "tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch",
    "t shirt", "t-shirts", "t shirts", "tees", "graphic tee", "essential tee",
    "vintage tee", "oversized tee", "plain shirt", "blank shirt", "shirts"
}

# Non-commercial or irrelevant query filter terms
IRRELEVANT_TERMS = [
    "meaning", "definition", "how to", "why", "iron", "near me", "template",
    "mockup", "tee times", "tee time", "tee off", "kaffee", "rezepte", "bh für",
    "bra for", "tutorial", "bra", "t-shirt bra", "tee height", "là gì",
    "t-shirt femme", "custom t-shirt printing", "roblox t-shirt"
]

# Blacklist for IP infringing terms (matched as whole words using regex \b)
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
    "phoebe bridgers", "kmfdm", "ye", "jackass", "runescape", "supergirl", "noah kahan",
    "my chemical romance", "mcr", "john deere", "wimbledon", "alan jackson"
]

def is_ip_infringing(keyword):
    """Check if keyword contains any blacklisted IP term using word boundary regex."""
    kw_lower = keyword.lower()
    for term in IP_BLACKLIST:
        pattern = r'\b' + re.escape(term) + r'\b'
        if re.search(pattern, kw_lower):
            return True
    return False

def generate_why_idea(keyword):
    """Generate insight / idea description for POD merch based on keyword."""
    # Clean term by replacing apparel words (longer/plural terms first)
    clean_topic = keyword.lower()
    for term in ["t-shirts", "tshirts", "tank tops", "tanktops", "t-shirt", "tshirt", "tanktop", "tank top", "shirt", "tee", "merch"]:
        clean_topic = re.sub(r'\b' + re.escape(term) + r'\b', '', clean_topic)
    clean_topic = ' '.join(clean_topic.split()).strip()

    if not clean_topic:
        clean_topic = keyword

    if is_ip_infringing(keyword):
        return f"Trending pop-culture/brand topic ({clean_topic.title()}). High consumer demand on POD marketplaces, but caution required due to potential trademark/copyright restrictions. Consider original royalty-free inspired concepts."
    else:
        return f"Rising niche search query focusing on '{clean_topic.title()}'. High opportunity for custom graphic apparel on Etsy/Amazon/Redbubble. Design idea: Create bold text or illustration typography focusing on '{clean_topic}' theme."

def parse_score(val):
    """Parse score value into integer for sorting, treating 'Breakout' as 9999."""
    if isinstance(val, str):
        if val.lower() == 'breakout':
            return 9999
        try:
            return int(val.replace('+', '').replace(',', ''))
        except ValueError:
            return 0
    elif isinstance(val, (int, float)):
        return int(val)
    return 0

def fetch_trending_queries():
    pytrends = TrendReq(hl='en-US', tz=360)
    seen_keywords = set()
    results = []

    for kw in SEED_KEYWORDS:
        print(f"Fetching related queries for seed: '{kw}'...")
        success = False
        for attempt in range(3):
            try:
                pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='', gprop='')
                related = pytrends.related_queries()
                success = True
                break
            except Exception as e:
                print(f"Attempt {attempt + 1} failed for '{kw}': {e}. Retrying in 10s...")
                time.sleep(10)

        if not success or kw not in related or related[kw]['rising'] is None:
            print(f"No rising queries found for '{kw}' or request failed.")
            continue

        df_rising = related[kw]['rising']
        for _, row in df_rising.iterrows():
            query = str(row['query']).strip()
            score = row['value']
            q_lower = query.lower()

            # Check deduplication
            if q_lower in seen_keywords:
                continue

            # Check long-tail (2+ words)
            words = q_lower.split()
            if len(words) < 2:
                continue

            # Check if contains apparel term
            if not any(apparel_term in q_lower for apparel_term in APPAREL_TERMS):
                continue

            # Check exact generic excludes
            if q_lower in EXCLUDE_EXACT:
                continue

            # Check irrelevant terms
            if any(irr in q_lower for irr in IRRELEVANT_TERMS):
                continue

            seen_keywords.add(q_lower)
            results.append({
                "keyword": query,
                "score": score,
                "score_num": parse_score(score),
                "is_ip": is_ip_infringing(query),
                "why_idea": generate_why_idea(query)
            })

        time.sleep(5)  # Delay between requests to prevent rate limiting

    # Sort results by score_num descending
    results.sort(key=lambda x: x["score_num"], reverse=True)
    return results

def format_markdown_table(items):
    if not items:
        return "_No new trending merch opportunities found for today._\n"

    lines = ["| Keyword | Score | Why / Idea / Market Insight |", "| --- | --- | --- |"]
    for item in items:
        score_str = f"Breakout (+{item['score_num']}%)" if item['score_num'] == 9999 else str(item['score'])
        # Escape pipe characters if any in content
        kw_clean = item['keyword'].replace('|', '\\|')
        idea_clean = item['why_idea'].replace('|', '\\|')
        lines.append(f"| {kw_clean} | {score_str} | {idea_clean} |")
    return "\n".join(lines) + "\n"

def update_trends_md(results):
    today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    general_items = [r for r in results if not r['is_ip']]
    ip_items = [r for r in results if r['is_ip']]

    section_content = f"## {today_str}\n\n"
    section_content += "### General Merch Opportunities\n"
    section_content += format_markdown_table(general_items) + "\n"
    section_content += "### Potential IP Infringing Opportunities\n"
    section_content += format_markdown_table(ip_items) + "\n"

    file_path = "trends.md"
    header = "# Google Trends Merch Opportunities\n\n"

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check if today's section already exists
        if f"## {today_str}" in content:
            print(f"Section for {today_str} already exists in {file_path}. Skipping update.")
            return

        if content.startswith(header):
            body = content[len(header):]
            new_content = header + section_content + "\n" + body
        else:
            new_content = header + section_content + "\n" + content
    else:
        new_content = header + section_content

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"Successfully updated {file_path} for {today_str}.")

if __name__ == "__main__":
    print("Starting Google Trends merch crawl...")
    results = fetch_trending_queries()
    print(f"Found {len(results)} opportunity terms.")
    update_trends_md(results)
