import datetime
import os
import re
import time
import pandas as pd
from pytrends.request import TrendReq

# Configuration
KEYWORDS = ["tshirt", "shirt", "tank top", "merch"]
BRAND_BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "gucci", "prada", "louis vuitton",
    "bieber", "beiber", "swift", "bts", "kpop", "nfl", "nba", "mlb", "nhl", "pokemon", "nintendo",
    "playstation", "xbox", "netflix", "amazon", "apple", "google", "microsoft",
    "trump", "biden", "harris", "obama", "nascar", "f1", "ufc", "wwe", "masters", "bruno mars",
    "kylie jenner", "michael jackson", "nasa", "national geographic", "coachella",
    "ethel cain", "sabrina carpenter", "sabrina", "katseye", "karol g", "morgan wallen",
    "britney spears", "skylrk", "skylark"
]

def is_ip_infringing(query):
    query_lower = query.lower()
    for brand in BRAND_BLACKLIST:
        if re.search(rf"\b{brand}\b", query_lower):
            return True
    return False

def generate_why_idea(query):
    query_lower = query.lower()
    if "wolf" in query_lower:
        return "Wolves are a classic evergreen niche. Could be a 'three wolf moon' style or a minimalist geometric design."
    if "cat" in query_lower or "dog" in query_lower:
        return "Pet owners love niche-specific apparel. Try a funny quote combined with the breed/animal."
    if "vintage" in query_lower or "retro" in query_lower:
        return "Retro aesthetics (80s/90s) are trending. Use distressed textures and neon/pastel colors."
    if "funny" in query_lower or "quote" in query_lower:
        return "Text-based designs with clever typography often perform well. Focus on readability and humor."

    return f"Rising interest in '{query}'. Design could focus on the specific niche or subculture mentioned. Look at top results on Redbubble/Amazon for inspiration."

def crawl():
    pytrends = TrendReq(hl='en-US', tz=360)
    all_rising = []

    for kw in KEYWORDS:
        print(f"Fetching trends for: {kw}")
        try:
            pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='US', gprop='')
            related = pytrends.related_queries()
            rising = related[kw]['rising']
            if rising is not None:
                # Handle 'Breakout' which is often returned as a string in some contexts or high int
                # In pandas, it might be an object column if 'Breakout' is present
                rising['value'] = rising['value'].apply(lambda x: 999999 if x == 'Breakout' else x)
                all_rising.append(rising)
            time.sleep(2) # Avoid rate limiting
        except Exception as e:
            print(f"Error fetching {kw}: {e}")
            if "429" in str(e):
                print("Rate limited. Sleeping for 10 seconds...")
                time.sleep(10)

    if not all_rising:
        print("No rising trends found.")
        return

    df = pd.concat(all_rising).drop_duplicates(subset=['query'])

    # Filtering: Long tail (2+ words)
    df = df[df['query'].str.split().str.len() >= 2]

    # Filter out common non-merch terms
    exclude_terms = ["meaning", "definition", "how to", "why", "iron", "near me", "template", "mockup"]
    for term in exclude_terms:
        df = df[~df['query'].str.contains(term, case=False)]

    # Separate IP Infringing
    df['is_ip'] = df['query'].apply(is_ip_infringing)

    general_df = df[~df['is_ip']].copy()
    ip_df = df[df['is_ip']].copy()

    # Sort by value (rising score)
    general_df = general_df.sort_values(by='value', ascending=False)
    ip_df = ip_df.sort_values(by='value', ascending=False)

    # Generate MD
    today = datetime.date.today().strftime("%Y-%m-%d")

    # Check if we already have entries for today
    if os.path.exists("trends.md"):
        with open("trends.md", "r") as f:
            old_content = f.read()
        if f"## Trends for {today}" in old_content:
            print(f"Trends for {today} already exist in trends.md. Skipping.")
            return
    else:
        old_content = ""

    md_output = f"## Trends for {today}\n\n"

    md_output += "### General Merch Opportunities\n\n"
    md_output += "| Keyword | Score | Why/Idea |\n"
    md_output += "| --- | --- | --- |\n"
    for _, row in general_df.iterrows():
        score = "Breakout" if row['value'] == 999999 else row['value']
        why = generate_why_idea(row['query'])
        md_output += f"| {row['query']} | {score} | {why} |\n"

    md_output += "\n### Potential IP Infringing Opportunities\n\n"
    md_output += "| Keyword | Score | Why/Idea |\n"
    md_output += "| --- | --- | --- |\n"
    for _, row in ip_df.iterrows():
        score = "Breakout" if row['value'] == 999999 else row['value']
        why = generate_why_idea(row['query'])
        md_output += f"| {row['query']} | {score} | {why} |\n"

    md_output += "\n---\n\n"

    with open("trends.md", "w") as f:
        f.write(md_output + old_content)
    print(f"Successfully updated trends.md with trends for {today}.")

if __name__ == "__main__":
    crawl()
