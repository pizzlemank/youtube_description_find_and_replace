import datetime
import os
import pandas as pd
from pytrends.request import TrendReq

# Configuration
SEED_KEYWORDS = ["tshirt", "shirt", "tank top", "merch"]
GEO = "US"
TIMEFRAME = "now 1-d"  # Last 24 hours
TRENDS_FILE = "trends.md"

# Potential IP Infringing keywords (simplified list)
IP_KEYWORDS = [
    "disney", "marvel", "star wars", "nintendo", "pokemon", "nike", "adidas",
    "gucci", "prada", "louis vuitton", "taylor swift", "beyonce", "nfl", "nba",
    "mlb", "nhl", "harry potter", "netflix", "hulu", "amazon", "google",
    "apple", "microsoft", "sony", "playstation", "xbox", "fortnite", "roblox",
    "minecraft", "bluey", "sanrio", "hello kitty", "lego", "barbie", "nasa",
    "sega", "sanic", "justin bieber", "kanye west", "kanye", "daniel caesar",
    "elizabeth taylor", "conan gray", "benson boone", "mario"
]

def get_rising_queries(pytrends, kw):
    print(f"Fetching rising queries for '{kw}'...")
    pytrends.build_payload([kw], cat=0, timeframe=TIMEFRAME, geo=GEO, gprop='')
    related_queries = pytrends.related_queries()
    if related_queries and kw in related_queries:
        return related_queries[kw]['rising']
    return None

def is_ip_infringing(query):
    query_lower = query.lower()
    for ip_kw in IP_KEYWORDS:
        if ip_kw in query_lower:
            return True
    return False

def generate_idea(query):
    query_lower = query.lower()
    # Simple logic for ideas
    if "tshirt" in query_lower or "shirt" in query_lower:
        base = query_lower.replace("tshirt", "").replace("shirt", "").strip()
        return f"Design featuring {base}. Trends suggest high interest in this specific variation."
    elif "tank top" in query_lower:
        base = query_lower.replace("tank top", "").strip()
        return f"Summer-ready tank top design for '{base}'. Focus on typography or minimalist graphics."
    else:
        return f"Explore {query} as a niche merch concept. High search velocity indicates untapped demand."

def filter_queries(df):
    if df is None or df.empty:
        return pd.DataFrame()

    # Filter for long-tail or specific apparel terms
    # We want queries that actually look like a design idea
    def keep_query(q):
        q = q.lower()
        # Avoid too generic or irrelevant queries
        if q in ["t shirt", "t-shirt", "tshirt", "shirt", "shirts", "tank top", "merch"]:
            return False
        # Avoid purely navigational/functional queries like "how to", "near me", "amazon"
        if any(x in q for x in ["how to", "near me", "login", "store", "sale", "cheap"]):
            return False
        # Prefer queries with apparel terms or 3+ words
        if any(x in q for x in ["shirt", "tshirt", "tank top", "tee", "hoodie"]):
            return True
        if len(q.split()) >= 3:
            return True
        return False

    df = df[df['query'].apply(keep_query)]
    return df

def format_as_markdown_table(df):
    if df.empty:
        return "No significant trends found for this category today."

    lines = ["| Keyword | Score | Why / Design Idea |", "| --- | --- | --- |"]
    for _, row in df.iterrows():
        query = row['query']
        value = row['value']
        idea = generate_idea(query)
        lines.append(f"| {query} | {value} | {idea} |")
    return "\n".join(lines)

def main():
    pytrends = TrendReq(hl='en-US', tz=360)

    all_rising = []
    for kw in SEED_KEYWORDS:
        rising = get_rising_queries(pytrends, kw)
        if rising is not None and not rising.empty:
            all_rising.append(rising)

    if not all_rising:
        print("No rising queries found across all seed keywords.")
        return

    df_all = pd.concat(all_rising).drop_duplicates(subset='query')
    df_filtered = filter_queries(df_all)

    if df_filtered.empty:
        print("No queries passed the filters.")
        return

    # Split into General and IP Infringing
    df_filtered['is_ip'] = df_filtered['query'].apply(is_ip_infringing)
    df_general = df_filtered[df_filtered['is_ip'] == False]
    df_ip = df_filtered[df_filtered['is_ip'] == True]

    date_str = datetime.date.today().strftime("%Y-%m-%d")

    new_content = f"## Trends for {date_str}\n\n"

    new_content += "### General Merch Opportunities\n\n"
    new_content += format_as_markdown_table(df_general) + "\n\n"

    new_content += "### Potential IP Infringing Opportunities\n\n"
    new_content += format_as_markdown_table(df_ip) + "\n\n"

    # Read existing content
    if os.path.exists(TRENDS_FILE):
        with open(TRENDS_FILE, 'r') as f:
            existing_content = f.read()
            # Check if we already added for today to avoid duplicates if run multiple times
            if f"## Trends for {date_str}" in existing_content:
                print(f"Trends for {date_str} already exist in {TRENDS_FILE}. Skipping append.")
                return
    else:
        existing_content = "# Merch Opportunity Trends\n\n"

    # Prepend new content after the title
    if "# Merch Opportunity Trends" in existing_content:
        parts = existing_content.split("# Merch Opportunity Trends\n\n", 1)
        final_content = "# Merch Opportunity Trends\n\n" + new_content + parts[1]
    else:
        final_content = "# Merch Opportunity Trends\n\n" + new_content + existing_content

    with open(TRENDS_FILE, 'w') as f:
        f.write(final_content)

    print(f"Successfully updated {TRENDS_FILE}")

if __name__ == "__main__":
    main()
