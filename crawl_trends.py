import time
import datetime
import os
import pandas as pd
from pytrends.request import TrendReq

# Configuration
SEEDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]
APPAREL_TERMS = ["shirt", "tshirt", "t-shirt", "tank top", "tanktop", "tee", "merch"]
BRAND_BLACKLIST = [
    "disney", "marvel", "star wars", "starwars", "nike", "adidas", "bieber", "taylor swift",
    "michael jackson", "one piece", "popeyes", "coachella", "netflix", "mickey", "mickey mouse",
    "trump", "biden", "nba", "nfl", "mlb", "nhl", "pokemon", "nintendo", "sony", "playstation", "xbox",
    "nasa", "hellstar", "karol g", "bruno mars", "sabrina carpenter", "billie eilish", "billie",
    "olivia rodrigo", "noah kahan", "frank ocean", "mashtag brady", "aldi", "morbid podcast",
    "ysl", "koningsdag", "oranje", "higgins", "kelce", "mahomes", "stroud", "wwe", "the weeknd",
    "chrome hearts", "stussy", "vultures", "kanye"
]

EXCLUDE_TERMS = [
    "meaning", "definition", "how to", "why", "iron", "near me", "template", "mockup",
    "tee times", "tee time", "tee off", "graphic tee", "essential tee", "vintage tee",
    "oversized tee", "plain shirt", "blank shirt"
]

def get_rising_queries(keywords):
    # Use a custom session if needed to handle retries, but for now simple TrendReq
    # We'll implement a simple retry logic for 429s
    pytrends = TrendReq(hl='en-US', tz=360)
    all_rising = []

    for kw in keywords:
        print(f"Fetching trends for: {kw}")
        retries = 3
        while retries > 0:
            try:
                pytrends.build_payload([kw], timeframe='now 7-d')
                related_queries = pytrends.related_queries()

                if kw in related_queries and related_queries[kw]['rising'] is not None:
                    rising = related_queries[kw]['rising']
                    rising['seed'] = kw
                    all_rising.append(rising)
                break # Success
            except Exception as e:
                print(f"Error fetching {kw}: {e}")
                if "429" in str(e):
                    print("Rate limit hit, sleeping for 10 seconds...")
                    time.sleep(10)
                    retries -= 1
                else:
                    break # Other error

        time.sleep(2) # Avoid rate limiting

    if not all_rising:
        return pd.DataFrame()

    return pd.concat(all_rising).drop_duplicates(subset=['query'])

def is_ip_infringing(query):
    query_lower = query.lower()
    for brand in BRAND_BLACKLIST:
        if brand in query_lower:
            return True
    return False

def generate_idea(query):
    # Simple logic to generate an idea based on the query
    clean_query = query.lower()
    # Replace apparel terms with empty string to isolate the niche
    # Sort APPAREL_TERMS by length descending to replace longer ones first (e.g. "t-shirt" before "shirt")
    for term in sorted(APPAREL_TERMS, key=len, reverse=True):
        clean_query = clean_query.replace(term, "").strip()

    # Clean up multiple spaces
    clean_query = " ".join(clean_query.split())

    if not clean_query:
        return "General apparel design idea."

    return f"Design focused on '{clean_query.title()}' theme. Possible text-based or minimalist graphic design for fans of this niche."

def format_as_markdown(df):
    if df.empty:
        return ""

    # Filter for long-tail (at least 2 words) and contains apparel terms
    df['is_long_tail'] = df['query'].apply(lambda x: len(x.split()) >= 2)
    df['has_apparel_term'] = df['query'].apply(lambda x: any(term in x.lower() for term in APPAREL_TERMS))
    df['is_excluded'] = df['query'].apply(lambda x: any(term in x.lower() for term in EXCLUDE_TERMS))

    filtered_df = df[df['is_long_tail'] & df['has_apparel_term'] & ~df['is_excluded']].copy()

    if filtered_df.empty:
        return ""

    # Sort by score (value)
    # Pytrends 'value' can be a percentage (e.g., 1000) or 'Breakout'
    def sort_score(val):
        if val == 'Breakout':
            return 9999
        try:
            # Pytrends returns int or float sometimes, or string
            return int(val)
        except:
            return 0

    filtered_df['score_numeric'] = filtered_df['value'].apply(sort_score)
    filtered_df = filtered_df.sort_values(by='score_numeric', ascending=False)

    ip_df = filtered_df[filtered_df['query'].apply(is_ip_infringing)]
    clean_df = filtered_df[~filtered_df['query'].apply(is_ip_infringing)]

    output = f"### {datetime.date.today().strftime('%Y-%m-%d')}\n\n"

    output += "#### General Merch Opportunities\n"
    output += "| Keyword | Score | Why/Idea |\n"
    output += "| :--- | :--- | :--- |\n"
    if clean_df.empty:
        output += "| None found | - | - |\n"
    else:
        for _, row in clean_df.iterrows():
            output += f"| {row['query']} | {row['value']} | {generate_idea(row['query'])} |\n"

    output += "\n#### Potential IP Infringing Opportunities\n"
    output += "| Keyword | Score | Why/Idea |\n"
    output += "| :--- | :--- | :--- |\n"
    if ip_df.empty:
        output += "| None found | - | - |\n"
    else:
        for _, row in ip_df.iterrows():
            output += f"| {row['query']} | {row['value']} | {generate_idea(row['query'])} (CAUTION: Brand/IP/Event detected) |\n"

    return output

def update_trends_file(markdown_content):
    if not markdown_content:
        print("No trends found to update.")
        return

    filename = "trends.md"

    # Check if we already added trends for today
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            content = f.read()
            today_str = datetime.date.today().strftime('%Y-%m-%d')
            if f"### {today_str}" in content:
                print("Today's trends already added.")
                return
    else:
        content = "# Google Trends Merch Opportunities\n\nDaily crawl of Google Trends for POD niche identification.\n\n"

    # Find where to insert (after the header)
    header_marker = "Daily crawl of Google Trends for POD niche identification.\n\n"
    insert_pos = content.find(header_marker)
    if insert_pos == -1:
        # Fallback if header is different
        new_content = markdown_content + "\n\n" + content
    else:
        insert_pos += len(header_marker)
        new_content = content[:insert_pos] + markdown_content + "\n\n" + content[insert_pos:]

    with open(filename, 'w') as f:
        f.write(new_content)
    print("Trends updated successfully.")

if __name__ == "__main__":
    rising_df = get_rising_queries(SEEDS)
    md = format_as_markdown(rising_df)
    update_trends_file(md)
