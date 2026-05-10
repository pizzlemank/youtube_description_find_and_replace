import datetime
import os
import time
import pandas as pd
from pytrends.request import TrendReq

# Configuration
SEED_KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]
BRAND_BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "taylor swift", "bts",
    "michael jackson", "nba", "nfl", "mlb", "nhl", "nintendo", "pokemon",
    "harry potter", "nasa", "hellstar", "ysl", "gucci", "prada", "louis vuitton",
    "koningsdag", "oranje", "higgins", "wwe", "kanye", "drake", "notre dame",
    "ariana grande", "george strait", "olivia dean", "conan gray", "man utd",
    "lidl", "m&s", "mnet", "amc", "murder drones", "luke combs", "ohio state",
    "ufc", "f1", "nascar", "sanrio", "hello kitty", "stussy", "mclaren", "deftones",
    "cleetus mcfarland", "the neighbourhood", "bring me the horizon", "khan asadi",
    "lyrebird", "anthropologie", "carson hocevar", "rihanna", "morgan wallen",
    "valorant", "kentucky derby", "victoria beckham", "kimi antonelli",
    "wnba", "no doubt", "bad omens", "good mythical morning", "riley green",
    "ella langley", "candace owens", "g59", "grey59", "greyfivenine", "of the trees"
]

EXCLUDE_TERMS = [
    "meaning", "definition", "how to", "why", "iron", "near me",
    "template", "mockup", "tee times", "tee time", "tee off",
    "graphic tee", "essential tee", "vintage tee", "oversized tee",
    "plain shirt", "blank shirt", "là gì"
]

def is_ip_infringing(query):
    query_lower = query.lower()
    for brand in BRAND_BLACKLIST:
        if brand in query_lower:
            return True
    return False

def get_opportunity_idea(query):
    query_lower = query.lower()
    # Clean up the keyword to get the core concept
    clean_concept = query_lower
    for term in SEED_KEYWORDS:
        clean_concept = clean_concept.replace(term, "").strip()

    clean_concept = " ".join(clean_concept.split()) # remove double spaces

    if not clean_concept:
        clean_concept = query

    return f"Design a unique '{clean_concept}' concept. Current trend shows high interest in this niche. Focus on original typography or custom illustrations to avoid generic looks."

def main():
    print("Starting Google Trends crawl...")
    pytrends = TrendReq(hl='en-US', tz=360)

    all_rising_queries = []

    for seed in SEED_KEYWORDS:
        print(f"Fetching rising queries for: {seed}")
        retries = 3
        while retries > 0:
            try:
                pytrends.build_payload([seed], cat=0, timeframe='now 7-d', geo='US')
                related = pytrends.related_queries()

                if seed in related and related[seed]['rising'] is not None:
                    df = related[seed]['rising']
                    all_rising_queries.append(df)

                time.sleep(2) # Be nice to Google
                break
            except Exception as e:
                print(f"Error fetching {seed}: {e}")
                if "429" in str(e):
                    print("Rate limit hit, sleeping for 60 seconds...")
                    time.sleep(60)
                    retries -= 1
                else:
                    break

    if not all_rising_queries:
        print("No rising queries found today.")
        return

    full_df = pd.concat(all_rising_queries).drop_duplicates(subset='query')

    # Filter for long-tail (at least 2 words)
    full_df = full_df[full_df['query'].str.split().str.len() >= 2]

    # Filter out exclude terms
    for term in EXCLUDE_TERMS:
        full_df = full_df[~full_df['query'].str.contains(term, case=False)]

    # Sort by value (score)
    # Pytrends returns 'Breakout' or numeric strings.
    def sort_key(val):
        if val == 'Breakout':
            return 9999
        try:
            return int(val)
        except:
            return 0

    full_df['score_val'] = full_df['value'].apply(sort_key)
    full_df = full_df.sort_values(by='score_val', ascending=False)

    # Separate IP vs General
    general_merch = []
    ip_infringing = []

    for _, row in full_df.iterrows():
        query = row['query']
        score = row['value']

        # Ensure it actually contains one of our seed keywords or related apparel terms
        # to ensure it's a merch opportunity
        apparel_terms = SEED_KEYWORDS + ["tee", "tshirt", "shirt", "tank top", "tanktop"]
        if not any(term in query.lower() for term in apparel_terms):
            continue

        item = {
            'keyword': query,
            'score': score,
            'idea': get_opportunity_idea(query)
        }

        if is_ip_infringing(query):
            ip_infringing.append(item)
        else:
            general_merch.append(item)

    # Generate Markdown
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    md_content = f"\n## {today_str}\n\n"

    md_content += "### General Merch Opportunities\n"
    if general_merch:
        md_content += "| Keyword | Score | Why/Idea |\n"
        md_content += "| :--- | :--- | :--- |\n"
        for item in general_merch[:15]: # Top 15
            md_content += f"| {item['keyword']} | {item['score']} | {item['idea']} |\n"
    else:
        md_content += "No general opportunities found today.\n"

    md_content += "\n### Potential IP Infringing Opportunities\n"
    if ip_infringing:
        md_content += "| Keyword | Score | Why/Idea |\n"
        md_content += "| :--- | :--- | :--- |\n"
        for item in ip_infringing[:10]: # Top 10
            md_content += f"| {item['keyword']} | {item['score']} | {item['idea']} |\n"
    else:
        md_content += "No IP infringing opportunities found today.\n"

    md_content += "\n---\n"

    # Prepend to trends.md
    try:
        with open("trends.md", "r") as f:
            original_content = f.read()
    except FileNotFoundError:
        original_content = "# Google Trends Merch Opportunities\n\n---\n"

    # Check if we already added today's data (avoid duplicates if run multiple times)
    if f"## {today_str}" in original_content:
        print(f"Data for {today_str} already exists in trends.md. Skipping.")
        return

    # Find the insertion point (after the header)
    header_end = original_content.find("---") + 3
    new_total_content = original_content[:header_end] + md_content + original_content[header_end:]

    with open("trends.md", "w") as f:
        f.write(new_total_content)

    print(f"Successfully updated trends.md with {len(general_merch)} general and {len(ip_infringing)} IP infringing items.")

if __name__ == "__main__":
    main()
