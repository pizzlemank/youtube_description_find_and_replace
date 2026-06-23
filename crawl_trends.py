import time
import datetime
import re
import pandas as pd
from pytrends.request import TrendReq

# Configuration
KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]
TIMEFRAME = 'now 7-d'
GEO = ''  # Worldwide

# IP Blacklist (Example list of potentially infringing terms)
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
    "messi", "ronaldo", "spiderman", "spider-man", "batman", "superman", "fifa", "uefa",
    "palace", "kobe", "cowboys", "yankees", "dodgers", "dfb", "us open", "olympics"
]

def is_ip_infringing(keyword):
    """Simple check for IP infringement based on blacklist."""
    keyword_lower = keyword.lower()
    for brand in IP_BLACKLIST:
        if re.search(r'\b' + re.escape(brand) + r'\b', keyword_lower):
            return True
    return False

def generate_idea(keyword):
    """Generates a simple idea/description for the keyword."""
    # Clean up the keyword for the idea
    clean_keyword = keyword
    # Order matters for replacement to catch long phrases first
    sorted_keywords = sorted(KEYWORDS, key=len, reverse=True)
    for term in sorted_keywords:
        # Handle plurals and multiple variations
        clean_keyword = re.sub(rf'\b{term}s?\b', '', clean_keyword, flags=re.IGNORECASE)
        clean_keyword = re.sub(rf'\b{term.replace(" ", "")}s?\b', '', clean_keyword, flags=re.IGNORECASE)

    clean_keyword = re.sub(r'\s+', ' ', clean_keyword).strip()

    if not clean_keyword:
        return "Generic apparel trend."

    return f"Create a unique design focused on '{clean_keyword}'. People are searching for this specifically on apparel."

def process_trends(df):
    if df.empty:
        return [], []

    general_opportunities = []
    ip_infringing = []
    seen_keywords = set()

    # Filter and categorize
    for _, row in df.iterrows():
        keyword = row['query']
        score = row['value']

        # Deduplicate
        if keyword in seen_keywords:
            continue
        seen_keywords.add(keyword)

        # Criteria: Long tail (2+ words) and contains one of the apparel keywords
        words = keyword.split()
        if len(words) < 2:
            continue

        # Must contain at least one of our seed keywords (to ensure it's merch related)
        # and not just be the seed keyword itself
        keyword_lower = keyword.lower()
        if not any(term in keyword_lower for term in KEYWORDS):
            continue

        # Filter out generic searches like "t shirt" or "shirts"
        if keyword_lower in [k.lower() for k in KEYWORDS] or keyword_lower in [k.lower() + 's' for k in KEYWORDS]:
            continue

        # Filter out some non-merch related noise
        noise = ["meaning", "definition", "how to", "why", "iron", "near me", "template", "mockup", "tee times", "tee time", "tee off", "graphic tee", "essential tee", "vintage tee", "oversized tee", "plain shirt", "blank shirt", "kaffee", "rezepte", "bh für", "bra for", "tutorial", "bra", "t-shirt bra", "là gì"]
        if any(n in keyword_lower for n in noise):
            continue

        item = {
            'keyword': keyword,
            'score': score,
            'idea': generate_idea(keyword)
        }

        if is_ip_infringing(keyword):
            ip_infringing.append(item)
        else:
            general_opportunities.append(item)

    # Sort by score descending (Breakout is usually represented as high value or 0 in some versions, handling string vs int)
    def sort_key(x):
        try:
            return int(x['score'])
        except:
            return 9999 if x['score'] == 'Breakout' else 0

    general_opportunities.sort(key=sort_key, reverse=True)
    ip_infringing.sort(key=sort_key, reverse=True)

    return general_opportunities, ip_infringing

def format_table(items):
    if not items:
        return "No opportunities found for this category today."

    table = "| keyword | score | Why/Idea |\n"
    table += "| :--- | :--- | :--- |\n"
    for item in items:
        # Escape pipe characters in keyword and idea for markdown table
        kw = item['keyword'].replace('|', r'\|')
        score = str(item['score']).replace('|', r'\|')
        idea = item['idea'].replace('|', r'\|')
        table += f"| {kw} | {score} | {idea} |\n"
    return table

def update_markdown(general, infringing):
    today = datetime.date.today().isoformat()
    filename = 'trends.md'

    # Prepare new content
    new_content = f"## {today}\n\n"
    new_content += "### General Merch Opportunities\n"
    new_content += format_table(general) + "\n"
    new_content += "### Potential IP Infringing Opportunities\n"
    new_content += format_table(infringing) + "\n\n"

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        lines = ["# Google Trends Merch Opportunities\n\n"]

    # Find the main header
    header_found = False
    output_lines = []

    # Check if today's entry already exists to avoid duplicates if run multiple times
    if any(f"## {today}" in line for line in lines):
        print(f"Trends for {today} already exist in {filename}. Skipping update.")
        return

    for line in lines:
        output_lines.append(line)
        if "# Google Trends Merch Opportunities" in line and not header_found:
            output_lines.append("\n" + new_content)
            header_found = True

    if not header_found:
        # If header not found (shouldn't happen if initialized), prepend everything
        output_lines = ["# Google Trends Merch Opportunities\n\n", new_content] + lines

    with open(filename, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)
    print(f"Updated {filename} with {len(general) + len(infringing)} new entries.")

def fetch_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    all_results = []

    for kw in KEYWORDS:
        print(f"Fetching trends for: {kw}")
        success = False
        retries = 0
        while not success and retries < 2:
            try:
                pytrends.build_payload([kw], timeframe=TIMEFRAME, geo=GEO)
                related_queries = pytrends.related_queries()

                if kw in related_queries:
                    rising = related_queries[kw]['rising']
                    if rising is not None and not rising.empty:
                        all_results.append(rising)

                success = True
                time.sleep(5) # Delay to avoid rate limiting
            except Exception as e:
                print(f"Error fetching trends for {kw}: {e}")
                if "429" in str(e):
                    print("Rate limited. Sleeping for 30s...")
                    time.sleep(30)
                    retries += 1
                else:
                    break # Other errors, skip this keyword

    if all_results:
        return pd.concat(all_results)
    return pd.DataFrame()

if __name__ == "__main__":
    df = fetch_trends()
    general, infringing = process_trends(df)
    print(f"Found {len(general)} general opportunities and {len(infringing)} potential IP infringements.")
    update_markdown(general, infringing)
