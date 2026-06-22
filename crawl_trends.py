import pandas as pd
from pytrends.request import TrendReq
import time
from datetime import date
import os
import re

# Configuration
SEED_KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]
APPAREL_TERMS = ["shirt", "tshirt", "t-shirt", "tank top", "tanktop", "tee", "merch"]

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
    "messi", "ronaldo", "spiderman", "spider-man", "batman", "superman", "fifa", "uefa",
    "malcolm todd", "böhse onkelz", "love island", "eternal sunshine", "madewell", "anthropologie",
    "glitch", "stevie nicks", "beyonce", "lilibet", "olivia rodrigo", "caitlin clark", "sabrina carpenter"
]

TRENDS_FILE = "trends.md"

def get_rising_queries(pytrends, keyword):
    print(f"Fetching trends for: {keyword}")
    pytrends.build_payload([keyword], timeframe='now 7-d')
    related_queries = pytrends.related_queries()

    if keyword in related_queries and related_queries[keyword]['rising'] is not None:
        return related_queries[keyword]['rising']
    return pd.DataFrame()

def is_ip_infringing(keyword):
    keyword_lower = keyword.lower()
    for brand in IP_BLACKLIST:
        if re.search(rf"\b{re.escape(brand)}\b", keyword_lower):
            return True
    return False

def generate_idea(keyword):
    # Simple logic to generate an idea
    # Order matters: replace longer terms first
    sorted_terms = sorted(APPAREL_TERMS, key=len, reverse=True)
    idea = keyword.lower()
    for term in sorted_terms:
        # Also handle plurals and common variations
        idea = re.sub(rf"\b{re.escape(term)}s?\b", "", idea)

    # Clean up dashes and extra spaces
    idea = idea.replace("-", " ").strip()
    idea = re.sub(r'\s+', ' ', idea)

    if not idea:
        return "Generic apparel design"

    return f"Design featuring '{idea.title()}' concept"

def main():
    pytrends = TrendReq(hl='en-US', tz=360)

    all_results = []

    for kw in SEED_KEYWORDS:
        df = get_rising_queries(pytrends, kw)
        if not df.empty:
            all_results.append(df)
        time.sleep(5)  # Avoid rate limiting

    if not all_results:
        print("No rising queries found.")
        return

    merged_df = pd.concat(all_results).drop_duplicates(subset='query')

    # Filter for long-tail and contains apparel terms
    opportunities = []
    for _, row in merged_df.iterrows():
        query = row['query'].lower()
        # Must be at least 2 words and contain one of the apparel terms
        words = query.split()
        if len(words) >= 2 and any(term in query for term in APPAREL_TERMS):
            # Check if it's just a generic term like "t shirt"
            if query.strip() in SEED_KEYWORDS or query.strip() in ["t shirt", "t-shirts", "tees"]:
                continue

            # Filter out some noise
            if any(x in query for x in [
                "meaning", "definition", "how to", "why", "iron", "near me",
                "template", "mockup", "tee times", "tee time", "tee off",
                "graphic tee", "essential tee", "vintage tee", "oversized tee",
                "plain shirt", "blank shirt", "kaffee", "rezepte", "bh für", "bra for",
                "tutorial", "bra", "t-shirt bra"
            ]):
                continue

            if "là gì" in query: # Vietnamese for "is what"
                continue

            opportunities.append({
                'keyword': row['query'],
                'score': row['value'],
                'ip_infringing': is_ip_infringing(row['query'])
            })

    if not opportunities:
        print("No specific merch opportunities found after filtering.")
        return

    # Sort by score (Breakout is high)
    def sort_key(x):
        if x['score'] == 'Breakout':
            return 999999
        try:
            return int(x['score'])
        except:
            return 0

    opportunities.sort(key=sort_key, reverse=True)

    general_ops = [op for op in opportunities if not op['ip_infringing']]
    ip_ops = [op for op in opportunities if op['ip_infringing']]

    today = date.today().strftime("%Y-%m-%d")

    new_content = f"## {today}\n\n"

    if general_ops:
        new_content += "### General Merch Opportunities\n\n"
        new_content += "| keyword | score | Why/Idea |\n"
        new_content += "|---------|-------|----------|\n"
        for op in general_ops:
            idea = generate_idea(op['keyword'])
            new_content += f"| {op['keyword']} | {op['score']} | {idea} |\n"
        new_content += "\n"

    if ip_ops:
        new_content += "### Potential IP Infringing Opportunities\n\n"
        new_content += "| keyword | score | Why/Idea |\n"
        new_content += "|---------|-------|----------|\n"
        for op in ip_ops:
            new_content += f"| {op['keyword']} | {op['score']} | Potential IP: {op['keyword']} |\n"
        new_content += "\n"

    # Prepend to file
    header = "# Google Trends Merch Opportunities\n\n"
    if os.path.exists(TRENDS_FILE):
        with open(TRENDS_FILE, 'r') as f:
            current_content = f.read()

        # Remove old header if it exists to avoid duplication
        if current_content.startswith(header):
            current_content = current_content[len(header):]

        # Check if today's entry already exists to avoid duplicate runs on same day
        if f"## {today}" in current_content:
            print("Today's trends already recorded.")
            return

        final_content = header + new_content + current_content
    else:
        final_content = header + new_content

    with open(TRENDS_FILE, 'w') as f:
        f.write(final_content)

    print(f"Updated {TRENDS_FILE} with {len(opportunities)} opportunities.")

if __name__ == "__main__":
    main()
