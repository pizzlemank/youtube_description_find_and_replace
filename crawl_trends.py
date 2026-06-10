import pandas as pd
from pytrends.request import TrendReq
import datetime
import os
import time

# List of seed keywords to find related rising trends
SEED_KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]

# Blacklist of potentially IP infringing terms
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
    "selena Gomez", "carhartt", "hazbin hotel", "digital circus", "tadc", "linkin park",
    "bad omens", "forrest frank", "malcolm todd", "böhse onkelz", "love island",
    "eternal sunshine", "madewell", "anthropologie", "glitch"
]

def is_ip_infringing(keyword):
    keyword_lower = keyword.lower()
    for brand in IP_BLACKLIST:
        # Lowercase the brand just in case, and check if it exists as a whole word or significant part
        brand_lower = brand.lower()
        if brand_lower in keyword_lower:
            # Basic word boundary check to avoid false positives like "sunbathing" for "nba"
            # Using a simple check: brand is at start, end, or surrounded by non-alphanumerics
            import re
            pattern = rf"\b{re.escape(brand_lower)}\b"
            if re.search(pattern, keyword_lower):
                return True
    return False

def get_opportunity_idea(keyword):
    # Simple logic to generate an idea or comment
    keyword_lower = keyword.lower()

    # Remove common apparel terms to find the core niche
    niche = keyword_lower
    # Sort by length descending to replace longer phrases first
    apparel_terms = sorted(["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch", "tshirts", "shirts", "tees", "tank tops"], key=len, reverse=True)
    for term in apparel_terms:
        niche = niche.replace(term, "").strip()

    # Clean up any double spaces
    niche = " ".join(niche.split())

    if not niche:
        return "Generic apparel search. Look for specific sub-niches or trending events within this category."

    # Check if it's a "versus" or "and" topic
    if " vs " in niche or " and " in niche:
        return f"Trending comparison or duo: '{niche}'. Create a design that captures both elements or the rivalry/partnership."

    return f"Rising interest in '{niche}'. This looks like a specific niche opportunity. Research what fans/customers of '{niche}' value and design a unique graphic or catchy slogan around it."

def crawl():
    pytrends = TrendReq(hl='en-US', tz=360)

    all_results = []

    for kw in SEED_KEYWORDS:
        print(f"Fetching trends for: {kw}")
        retries = 3
        while retries > 0:
            try:
                pytrends.build_payload([kw], timeframe='now 7-d')
                related_queries = pytrends.related_queries()

                if kw in related_queries:
                    rising = related_queries[kw]['rising']
                    if rising is not None and not rising.empty:
                        all_results.append(rising)

                # Sleep to avoid rate limiting
                time.sleep(10)
                break
            except Exception as e:
                if "429" in str(e):
                    print(f"Rate limited for {kw}, retrying in 30s...")
                    time.sleep(30)
                    retries -= 1
                else:
                    print(f"Error fetching {kw}: {e}")
                    break

    if not all_results:
        print("No rising trends found.")
        return

    df = pd.concat(all_results).drop_duplicates(subset=['query'])

    # Filter for long tail (at least 2 words) and contains apparel terms
    def is_valid(query):
        words = query.split()
        if len(words) < 2:
            return False

        # Check if it contains any of our seed keywords or variants
        query_lower = query.lower()

        # Exclude non-commercial or irrelevant terms
        exclude_terms = [
            "meaning", "definition", "how to", "why", "iron", "near me",
            "template", "mockup", "tee times", "tee time", "tee off",
            "graphic tee", "essential tee", "vintage tee", "oversized tee",
            "plain shirt", "blank shirt"
        ]
        if any(ex in query_lower for ex in exclude_terms):
            return False

        if any(term in query_lower for term in SEED_KEYWORDS):
             # Exclude very generic ones like "t shirt" or "tshirt" which might have slipped in
             if query_lower.strip() in SEED_KEYWORDS or query_lower.strip() in ["t shirt", "t-shirts", "tees"]:
                 return False
             return True
        return False

    df = df[df['query'].apply(is_valid)]

    # Sort by value (score) descending
    # 'Breakout' is returned as a string, let's treat it as a high number
    def parse_value(val):
        if isinstance(val, str) and 'Breakout' in val:
            return 9999
        try:
            return int(val)
        except:
            return 0

    df['score_val'] = df['value'].apply(parse_value)
    df = df.sort_values(by='score_val', ascending=False)

    today = datetime.date.today().strftime("%Y-%m-%d")

    general_ops = []
    ip_ops = []

    for _, row in df.iterrows():
        kw = row['query']
        score = row['value']
        idea = get_opportunity_idea(kw)

        entry = f"| {kw} | {score} | {idea} |"

        if is_ip_infringing(kw):
            ip_ops.append(entry)
        else:
            general_ops.append(entry)

    # Update trends.md
    output = f"## {today}\n\n"

    output += "### General Merch Opportunities\n"
    output += "| keyword | score | Why/Idea |\n"
    output += "| --- | --- | --- |\n"
    if general_ops:
        output += "\n".join(general_ops) + "\n"
    else:
        output += "| None found | - | - |\n"

    output += "\n### Potential IP Infringing Opportunities\n"
    output += "| keyword | score | Why/Idea |\n"
    output += "| --- | --- | --- |\n"
    if ip_ops:
        output += "\n".join(ip_ops) + "\n"
    else:
        output += "| None found | - | - |\n"

    output += "\n---\n\n"

    filename = "trends.md"
    existing_content = ""
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            # Skip the title if it exists to prepend
            content = f.read()
            if "# Google Trends Merch Opportunities" in content:
                parts = content.split("# Google Trends Merch Opportunities\n\n", 1)
                if len(parts) > 1:
                    existing_content = parts[1]
                else:
                    existing_content = ""
            else:
                existing_content = content

    with open(filename, "w", encoding="utf-8") as f:
        f.write("# Google Trends Merch Opportunities\n\n")
        f.write(output)
        f.write(existing_content)

if __name__ == "__main__":
    crawl()
