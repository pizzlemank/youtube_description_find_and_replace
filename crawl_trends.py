import pandas as pd
from pytrends.request import TrendReq
import datetime
import os
import re
import time

# List of seed keywords to find rising trends for
SEED_KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]

# Blacklist of brands and IPs to flag potential infringement
IP_BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "taylor swift", "bts", "michael jackson",
    "nba", "wnba", "nfl", "mlb", "nhl", "nintendo", "pokemon", "harry potter", "nasa",
    "hellstar", "ysl", "gucci", "prada", "louis vuitton", "arsenal", "real madrid", "liverpool",
    "man city", "chelsea", "bayern", "barcelona", "knicks", "lakers", "celtics", "warriors", "bulls",
    "amiri", "trapstar", "corteiz", "sp5der", "minus two", "syna world", "harry styles",
    "gracie abrams", "daniel caesar", "bad bunny", "billie eilish", "drake", "kanye", "travis scott",
    "bruno mars", "hello kitty", "sanrio", "nascar", "f1", "mercedes", "ferrari", "red bull",
    "toy story", "psg", "asap rocky", "megan moroney", "sean john", "morgan wallen", "spurs", "rcb",
    "snipes", "asos", "pattie gonia", "wingstop", "ariana grande", "selena gomez", "carhartt",
    "hazbin hotel", "digital circus", "tadc", "linkin park", "bad omens", "forrest frank",
    "malcolm todd", "böhse onkelz", "love island", "eternal sunshine", "madewell", "anthropologie",
    "glitch", "stevie nicks", "beyonce", "lilibet", "olivia rodrigo", "caitlin clark", "sabrina carpenter",
    "messi", "ronaldo", "spiderman", "spider-man", "batman", "superman", "fifa", "uefa", "palace",
    "kobe", "cowboys", "yankees", "dodgers", "dfb", "us open", "olympics", "cecil", "h&m", "levi's",
    "zara", "gap", "old navy", "lululemon", "patagonia", "north face", "under armour", "puma", "reebok",
    "vans", "converse", "stussy", "supreme", "hilary duff", "lewis capaldi", "radiohead", "beabadoobee",
    "phoebe bridgers", "kmfdm", "ye", "jackass", "runescape", "supergirl", "noah kahan", "my chemical romance",
    "mcr", "john deere", "wimbledon", "alan jackson"
]

# Words that indicate the query is likely not a merch opportunity
EXCLUDE_WORDS = [
    "meaning", "definition", "how to", "why", "iron", "near me", "template", "mockup",
    "tee times", "tee time", "tee off", "graphic tee", "essential tee", "vintage tee",
    "oversized tee", "plain shirt", "blank shirt", "kaffee", "rezepte", "bh für", "bra for",
    "tutorial", "bra", "t-shirt bra", "tee height", "là gì", "t-shirt femme",
    "custom t-shirt printing", "roblox t-shirt"
]

def is_ip_infringing(query):
    query_lower = query.lower()
    for brand in IP_BLACKLIST:
        if re.search(rf"\b{re.escape(brand)}\b", query_lower):
            return True
    return False

def is_valid_merch_opportunity(query):
    query_lower = query.lower()
    # Must be at least 2 words (long tail)
    if len(query_lower.split()) < 2:
        return False

    # Check if it contains apparel related terms
    apparel_terms = ["shirt", "tshirt", "t-shirt", "tank top", "tanktop", "tee", "merch"]
    if not any(term in query_lower for term in apparel_terms):
        return False

    # Check for excluded words
    if any(word in query_lower for word in EXCLUDE_WORDS):
        return False

    # Filter out exact matches of seed keywords (too generic)
    if query_lower in SEED_KEYWORDS or query_lower in ["t shirt", "t-shirts", "tees"]:
        return False

    return True

def generate_idea(query):
    query_lower = query.lower()
    # Remove the apparel terms to get the core topic
    topic = query_lower
    for term in ["t-shirt", "tshirt", "shirt", "tank top", "tanktop", "tee", "merch", "tshirts", "tees", "shirts"]:
        topic = re.sub(rf"\b{term}\b", "", topic).strip()

    topic = re.sub(r'\s+', ' ', topic).strip()

    if not topic:
        return "Generic apparel trend. Focus on minimalist typography or popular colorways."

    ideas = [
        f"Rising interest in {topic}. Design idea: Graphic illustration featuring {topic} with a trendy font.",
        f"Shoppers are looking for {topic} apparel. Could be a viral moment or niche hobby.",
        f"Potential for a 'I love {topic}' or '{topic} Squad' style design.",
        f"Niche trend: {topic}. Look for aesthetic styles on Pinterest/TikTok for inspiration."
    ]
    # Simple hash-based selection for variety
    return ideas[len(topic) % len(ideas)]

def get_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    all_rising = []

    print("Fetching trends...")
    for kw in SEED_KEYWORDS:
        try:
            print(f"Querying for {kw}...")
            pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='', gprop='')
            related = pytrends.related_queries()

            if related[kw]['rising'] is not None:
                rising_df = related[kw]['rising']
                for index, row in rising_df.iterrows():
                    query = row['query']
                    score = row['value']

                    if is_valid_merch_opportunity(query):
                        all_rising.append({
                            'keyword': query,
                            'score': score,
                            'infringing': is_ip_infringing(query)
                        })
            time.sleep(5) # Avoid rate limiting
        except Exception as e:
            print(f"Error fetching {kw}: {e}")

    # Deduplicate
    unique_trends = {t['keyword']: t for t in all_rising}.values()
    return sorted(unique_trends, key=lambda x: x['score'] if isinstance(x['score'], int) else 9999, reverse=True)

def update_markdown(trends):
    today = datetime.date.today().strftime("%Y-%m-%d")
    header = f"## {today}\n\n"

    general_table = "### General Merch Opportunities\n\n| Keyword | Score | Why/Idea |\n| :--- | :--- | :--- |\n"
    ip_table = "### Potential IP Infringing Opportunities\n\n| Keyword | Score | Why/Idea |\n| :--- | :--- | :--- |\n"

    general_count = 0
    ip_count = 0

    for t in trends:
        idea = generate_idea(t['keyword'])
        row = f"| {t['keyword']} | {t['score']} | {idea} |\n"
        if t['infringing']:
            ip_table += row
            ip_count += 1
        else:
            general_table += row
            general_count += 1

    content = header
    if general_count > 0:
        content += general_table + "\n"
    if ip_count > 0:
        content += ip_table + "\n"

    if general_count == 0 and ip_count == 0:
        content += "No significant trends found today.\n\n"

    filename = "trends.md"
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            old_content = f.read()

        # Check if we already added today's trends
        if f"## {today}" in old_content:
            print(f"Trends for {today} already exist in {filename}. Skipping update.")
            return

        # Prepend after the main title if it exists, otherwise just prepend
        if "# Google Trends Merch Opportunities" in old_content:
            new_content = old_content.replace("# Google Trends Merch Opportunities", f"# Google Trends Merch Opportunities\n\n{content}")
        else:
            new_content = f"# Google Trends Merch Opportunities\n\n{content}\n" + old_content
    else:
        new_content = f"# Google Trends Merch Opportunities\n\n{content}"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"Successfully updated {filename}")

if __name__ == "__main__":
    trends = get_trends()
    if trends:
        update_markdown(trends)
    else:
        print("No trends found.")
