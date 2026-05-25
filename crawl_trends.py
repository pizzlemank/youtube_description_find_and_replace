import pandas as pd
from pytrends.request import TrendReq
import datetime
import os
import time

# List of keywords to seed the search
SEED_KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]

# Common apparel terms for filtering
APPAREL_TERMS = ["t-shirt", "tshirt", "t shirt", "shirt", "tank top", "tanktop", "tee", "merch"]

# IP Blacklist - known brands, franchises, and celebrities
IP_BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "taylor swift", "bts",
    "michael jackson", "nba", "wnba", "nfl", "mlb", "nhl", "nintendo", "pokemon",
    "harry potter", "nasa", "hellstar", "ysl", "gucci", "prada", "louis vuitton",
    "arsenal", "real madrid", "liverpool", "man city", "chelsea", "bayern", "barcelona",
    "knicks", "lakers", "celtics", "warriors", "bulls", "amiri", "trapstar", "corteiz",
    "sp5der", "minus two", "syna world", "harry styles", "gracie abrams", "daniel caesar",
    "bad bunny", "billie eilish", "drake", "kanye", "travis scott"
]

def get_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    all_rising_queries = []

    for keyword in SEED_KEYWORDS:
        print(f"Fetching trends for: {keyword}")

        # Retry mechanism for rate limiting
        max_retries = 3
        for attempt in range(max_retries):
            try:
                pytrends.build_payload([keyword], cat=0, timeframe='now 7-d', geo='', gprop='')
                related_queries = pytrends.related_queries()

                if keyword in related_queries and related_queries[keyword]['rising'] is not None:
                    rising = related_queries[keyword]['rising']
                    all_rising_queries.append(rising)

                # Sleep to avoid rate limiting between keywords
                time.sleep(5)
                break # Success, move to next keyword
            except Exception as e:
                print(f"Error fetching {keyword} (attempt {attempt + 1}): {e}")
                if "429" in str(e) and attempt < max_retries - 1:
                    print("Rate limit hit, sleeping for 60 seconds...")
                    time.sleep(60)
                else:
                    # Non-rate-limit error or max retries reached
                    break

    if not all_rising_queries:
        return pd.DataFrame()

    df = pd.concat(all_rising_queries).drop_duplicates(subset='query')
    return df

def filter_and_categorize(df):
    opportunities = []

    for _, row in df.iterrows():
        query = row['query'].lower()
        value = row['value']

        # Long-tail check: at least 2 words
        words = query.split()
        if len(words) < 2:
            continue

        # Ensure it contains an apparel term
        if not any(term in query for term in APPAREL_TERMS):
            continue

        # Exclude very generic terms that are basically just our seeds or slight variations
        generic_variations = [k.lower() for k in SEED_KEYWORDS] + ["t shirt", "t-shirts", "tees"]
        if query.strip() in generic_variations:
            continue

        # Common non-commercial or irrelevant terms
        exclude = [
            "meaning", "definition", "how to", "why", "iron", "near me",
            "template", "mockup", "tee times", "tee time", "tee off",
            "graphic tee", "essential tee", "vintage tee", "oversized tee",
            "plain shirt", "blank shirt", "kaffee", "rezepte", "bh für", "bra for",
            "tutorial", "là gì"
        ]
        if any(ex in query for ex in exclude):
            continue

        # IP check
        is_ip = any(brand in query for brand in IP_BLACKLIST)

        # Generate "Why/Idea"
        idea = generate_idea(query)

        opportunities.append({
            'keyword': row['query'],
            'score': value,
            'idea': idea,
            'is_ip': is_ip
        })

    return opportunities

def generate_idea(query):
    # Heuristic based idea generation
    clean_query = query
    # Sort APPAREL_TERMS by length descending to replace "t-shirt" before "shirt"
    sorted_terms = sorted(APPAREL_TERMS, key=len, reverse=True)
    for term in sorted_terms:
        clean_query = clean_query.replace(term, "").strip()

    # Clean up multiple spaces
    clean_query = " ".join(clean_query.split())

    # Capitalize for better presentation
    idea_subject = clean_query.title()

    if not idea_subject:
        return "Generic trending apparel. Focus on high-quality typography or minimalist design."

    return f"Design opportunity for '{idea_subject}'. This long-tail keyword is rising in search volume, suggesting a specific niche or event that shoppers are looking for."

def format_markdown(opportunities):
    today = datetime.date.today().strftime("%Y-%m-%d")

    general = [o for o in opportunities if not o['is_ip']]
    ip_infringing = [o for o in opportunities if o['is_ip']]

    # Sort by score (Breakout is usually represented as a very high number or 'Breakout' string)
    # We'll treat 'Breakout' as 9999 for sorting if it's a string
    def sort_key(x):
        try:
            return int(x['score'])
        except:
            return 9999

    general.sort(key=sort_key, reverse=True)
    ip_infringing.sort(key=sort_key, reverse=True)

    output = f"## {today}\n\n"

    output += "### General Merch Opportunities\n"
    if general:
        output += "| Keyword | Score | Why/Idea |\n"
        output += "| :--- | :--- | :--- |\n"
        for o in general:
            output += f"| {o['keyword']} | {o['score']} | {o['idea']} |\n"
    else:
        output += "No general opportunities found today.\n"

    output += "\n### Potential IP Infringing Opportunities\n"
    if ip_infringing:
        output += "| Keyword | Score | Why/Idea |\n"
        output += "| :--- | :--- | :--- |\n"
        for o in ip_infringing:
            output += f"| {o['keyword']} | {o['score']} | {o['idea']} |\n"
    else:
        output += "No IP infringing opportunities found today.\n"

    output += "\n---\n"
    return output

def update_trends_file(new_content):
    file_path = "trends.md"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            existing_content = f.read()
    else:
        existing_content = ""

    # Check if we already added content for today to avoid duplicates if run multiple times
    today_header = f"## {datetime.date.today().strftime('%Y-%m-%d')}"
    if today_header in existing_content:
        print("Trends for today already exist in trends.md. Skipping update.")
        return

    with open(file_path, "w") as f:
        f.write(new_content + "\n" + existing_content)

if __name__ == "__main__":
    print("Starting trends crawl...")
    df = get_trends()
    if not df.empty:
        opportunities = filter_and_categorize(df)
        if opportunities:
            markdown_content = format_markdown(opportunities)
            update_trends_file(markdown_content)
            print("trends.md updated successfully.")
        else:
            print("No suitable opportunities found.")
    else:
        print("No rising queries found.")
