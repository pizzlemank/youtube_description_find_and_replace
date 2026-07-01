import time
import datetime
import pandas as pd
import re
import os
from pytrends.request import TrendReq

# Common IP/Brands to flag
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
    "phoebe bridgers", "kmfdm", "ye", "jackass", "runescape", "supergirl", "roblox"
]

APPAREL_TERMS = ["shirt", "tshirt", "t-shirt", "tank top", "tanktop", "tee", "merch"]

# Terms that often appear with "tee" but aren't apparel or are too generic
EXCLUDE_TERMS = [
    "meaning", "definition", "how to", "why", "iron", "near me", "template", "mockup",
    "tee times", "tee time", "tee off", "graphic tee", "essential tee", "vintage tee",
    "oversized tee", "plain shirt", "blank shirt", "kaffee", "rezepte", "bh für", "bra for",
    "tutorial", "bra", "t-shirt bra", "tee height", "printing"
]

def is_ip_infringing(query):
    query_lower = query.lower()
    for term in IP_BLACKLIST:
        if re.search(rf"\b{re.escape(term)}\b", query_lower):
            return True
    return False

def get_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    seed_keywords = APPAREL_TERMS
    all_rising_queries = []

    for kw in seed_keywords:
        print(f"Fetching trends for: {kw}")
        try:
            success = False
            retries = 3
            while not success and retries > 0:
                try:
                    pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='', gprop='')
                    related_queries = pytrends.related_queries()
                    success = True
                except Exception as e:
                    print(f"Rate limited or error for {kw}, retrying... {e}")
                    time.sleep(10)
                    retries -= 1

            if success and kw in related_queries and related_queries[kw]['rising'] is not None:
                rising = related_queries[kw]['rising']
                all_rising_queries.append(rising)

            time.sleep(5)
        except Exception as e:
            print(f"Error fetching {kw}: {e}")
            time.sleep(10)

    if not all_rising_queries:
        return pd.DataFrame()

    df = pd.concat(all_rising_queries, ignore_index=True)
    df = df.drop_duplicates(subset=['query'])
    return df

def filter_and_categorize(df):
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    def is_valid_merch_query(query):
        query_lower = query.lower()

        # Long tail check
        words = query_lower.split()
        if len(words) < 2:
            return False

        # Must contain apparel term
        if not any(term in query_lower for term in APPAREL_TERMS):
            return False

        # Exclude generic exact matches
        if query_lower.strip() in ["t shirt", "t-shirt", "t-shirts", "tshirts", "tees", "merch"]:
            return False

        # Exclude known non-apparel or too generic terms
        if any(term in query_lower for term in EXCLUDE_TERMS):
            return False

        # Specific exclude for "là gì" (Vietnamese for "what is")
        if "là gì" in query_lower:
            return False

        # Exclude very generic apparel queries in other languages
        if query_lower.strip() in ["t-shirt femme", "t-shirt homme"]:
            return False

        return True

    df['is_valid'] = df['query'].apply(is_valid_merch_query)
    df = df[df['is_valid']].copy()

    df['is_ip'] = df['query'].apply(is_ip_infringing)

    def convert_value(val):
        if val == 'Breakout':
            return 9999
        try:
            return int(val)
        except:
            return 0

    df['score'] = df['value'].apply(convert_value)
    df = df.sort_values(by='score', ascending=False)

    general_merch = df[~df['is_ip']].copy()
    ip_merch = df[df['is_ip']].copy()

    return general_merch, ip_merch

def generate_idea(query):
    query_lower = query.lower()
    concept = query_lower
    # Order matters: replace longer terms first
    sorted_terms = sorted(APPAREL_TERMS + ["tshirts", "t-shirts", "tank tops"], key=len, reverse=True)
    for term in sorted_terms:
        concept = concept.replace(term, "")

    concept = concept.strip().replace("  ", " ")
    if not concept:
        concept = query

    return f"Design featuring '{concept}'. This is a rising long-tail search on Google Trends, indicating a specific niche opportunity. Check if competitors on Amazon/Etsy have similar designs."

def format_as_table(df):
    if df.empty:
        return "No opportunities found for this category."

    header = "| Keyword | Score | Why/Idea |"
    separator = "| --- | --- | --- |"
    rows = []
    for _, row in df.iterrows():
        idea = generate_idea(row['query'])
        rows.append(f"| {row['query']} | {row['value']} | {idea} |")

    return "\n".join([header, separator] + rows)

def update_trends_file(general_df, ip_df):
    today = datetime.date.today().isoformat()

    new_content = f"## {today}\n\n### General Merch Opportunities\n\n"
    new_content += format_as_table(general_df)
    new_content += "\n\n### Potential IP Infringing Opportunities\n\n"
    new_content += format_as_table(ip_df)
    new_content += "\n\n---\n\n"

    filename = "trends.md"
    main_header = "# Google Trends Merch Opportunities\n\n"

    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            existing_content = f.read()

        if f"## {today}" in existing_content:
            # Forcing update for verification during development
            if os.environ.get("FORCE_UPDATE") == "1":
                # Remove old section for today and prepend new one
                pattern = rf"## {today}.*?---\n\n"
                existing_content = re.sub(pattern, "", existing_content, flags=re.DOTALL)
            else:
                print(f"Trends for {today} already exist in {filename}. Skipping update.")
                return

        if existing_content.startswith(main_header):
            combined_content = main_header + new_content + existing_content[len(main_header):]
        else:
            combined_content = main_header + new_content + existing_content
    else:
        combined_content = main_header + new_content

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(combined_content)
    print(f"Updated {filename}")

if __name__ == "__main__":
    df = get_trends()
    general, ip = filter_and_categorize(df)
    update_trends_file(general, ip)
