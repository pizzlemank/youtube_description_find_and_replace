import pandas as pd
from pytrends.request import TrendReq
import datetime
import os
import time
import re

def crawl_trends():
    pytrends = TrendReq(hl='en-US', tz=360)

    seed_keywords = ["tshirt", "shirt", "tank top", "merch"]
    all_rising_queries = []

    # Blacklist for IP infringement detection
    ip_blacklist = [
        "disney", "marvel", "star wars", "nike", "adidas", "pokemon", "nintendo",
        "harry potter", "netflix", "anime", "manga", "band", "concert", "tour",
        "official", "brand", "logo", "gucci", "prada", "versace", "nasa",
        "national geographic", "patagonia", "north face", "champion", "under armour",
        "lego", "barbie", "sanrio", "hello kitty", "snoopy", "peanuts",
        "bieber", "kylie jenner", "sabrina carpenter", "bruno mars", "morgan wallen",
        "ethel cain", "bilmuri", "masters", "coachella", "rcb", "michael jackson",
        "meat canyon", "meatcanyon", "annie elise", "bluey", "taylor swift", "eras tour",
        "deadpool", "wolverine", "mickey", "minnie", "donald duck", "goofy",
        "superman", "batman", "wonder woman", "spider-man", "spiderman", "avengers",
        "iron man", "captain america", "thor", "hulk", "black widow", "black panther",
        "guardians of the galaxy", "star trek", "doctor who", "game of thrones",
        "stranger things", "squid game", "one piece", "naruto", "dragon ball",
        "attack on titan", "demon slayer", "jujutsu kaisen", "minecraft", "roblox",
        "fortnite", "call of duty", "zelda", "mario", "sonic"
    ]

    print("Fetching trends...")
    for kw in seed_keywords:
        try:
            pytrends.build_payload([kw], timeframe='now 7-d')
            related_queries = pytrends.related_queries()

            if kw in related_queries and related_queries[kw]['rising'] is not None:
                rising = related_queries[kw]['rising']
                all_rising_queries.append(rising)

            # Sleep to avoid rate limiting
            time.sleep(2)
        except Exception as e:
            print(f"Error fetching for {kw}: {e}")
            if "429" in str(e):
                print("Rate limited. Sleeping for 10 seconds...")
                time.sleep(10)

    if not all_rising_queries:
        print("No rising queries found.")
        return

    df = pd.concat(all_rising_queries).drop_duplicates(subset='query')

    # Filter for long-tail (at least 2 words) and must contain apparel terms
    apparel_terms = ['shirt', 'tshirt', 't-shirt', 'tank top', 'tanktop', 'hoodie', 'merch', 'tee']

    def is_valid_merch_kw(query):
        query = query.lower()
        words = query.split()
        if len(words) < 2:
            return False
        if not any(term in query for term in apparel_terms):
            return False
        # Filter out generic searches like "how to make a shirt"
        exclude_terms = ['meaning', 'definition', 'how to', 'why', 'iron', 'near me', 'template', 'mockup']
        if any(term in query for term in exclude_terms):
            return False
        return True

    df = df[df['query'].apply(is_valid_merch_kw)]

    if df.empty:
        print("No valid merch keywords found after filtering.")
        return

    # Categorize IP Infringement
    def check_ip(query):
        query = query.lower()
        for brand in ip_blacklist:
            if re.search(rf'\b{brand}\b', query):
                return True
        return False

    df['is_ip'] = df['query'].apply(check_ip)

    # Generate "Why/Idea"
    def generate_why(query):
        # Placeholder logic for "Why"
        words = query.lower().split()
        # Remove apparel terms to find the "niche"
        niche_words = [w for w in words if w not in apparel_terms]
        niche = " ".join(niche_words) if niche_words else "this"

        if "merch" in query:
            return f"High intent for '{niche}' merchandise. People are looking for specific items related to this topic. Check if there's a gap in the market for creative, unofficial fan art (if not infringing)."

        return f"Rising interest in '{query}'. Consider a unique graphic design focusing on the '{niche}' niche. The 'rising' status suggests it's a breakout trend that could be profitable on Amazon Merch or Redbubble."

    df['why'] = df['query'].apply(generate_why)

    # Prepare Markdown
    today = datetime.date.today().strftime("%Y-%m-%d")

    safe_df = df[~df['is_ip']]
    ip_df = df[df['is_ip']]

    markdown_output = f"## {today}\n\n"

    markdown_output += "### General Merch Opportunities\n"
    if not safe_df.empty:
        markdown_output += "| Keyword | Score | Why/Idea |\n"
        markdown_output += "|---------|-------|----------|\n"
        for _, row in safe_df.iterrows():
            markdown_output += f"| {row['query']} | {row['value']} | {row['why']} |\n"
    else:
        markdown_output += "No new general opportunities found today.\n"

    markdown_output += "\n### Potential IP Infringing Opportunities\n"
    markdown_output += "> **Warning:** These keywords may contain trademarked or copyrighted terms. Proceed with caution.\n\n"
    if not ip_df.empty:
        markdown_output += "| Keyword | Score | Why/Idea |\n"
        markdown_output += "|---------|-------|----------|\n"
        for _, row in ip_df.iterrows():
            markdown_output += f"| {row['query']} | {row['value']} | {row['why']} |\n"
    else:
        markdown_output += "No new IP infringing opportunities found today.\n"

    markdown_output += "\n---\n"

    # Prepend to trends.md
    filename = 'trends.md'
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            content = f.read()

        # Avoid duplicate entries for the same day
        if f"## {today}" in content:
            print(f"Trends for {today} already exist in {filename}. Skipping update.")
            return

        with open(filename, 'w') as f:
            f.write(markdown_output + "\n" + content)
    else:
        with open(filename, 'w') as f:
            f.write("# Print-on-Demand Trends\n\n" + markdown_output)

    print(f"Successfully updated {filename}")

if __name__ == "__main__":
    crawl_trends()
