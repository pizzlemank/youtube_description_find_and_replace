import pandas as pd
from pytrends.request import TrendReq
from datetime import datetime
import os
import re

# Configuration
KW_LIST = ["tshirt", "shirt", "tank top", "merch", "t-shirt"]
MERCH_TERMS = ["shirt", "tshirt", "t-shirt", "tank top", "hoodie", "apparel", "clothing", "merch"]

# Basic list of IP-sensitive keywords (brands, franchises, celebrities, games, etc.)
IP_KEYWORDS = [
    "disney", "marvel", "star wars", "pokemon", "nintendo", "nike", "adidas", "gucci",
    "supreme", "barbie", "lego", "harry potter", "anime", "naruto", "one piece",
    "dragon ball", "netflix", "hulu", "hbo", "warner bros", "universal", "sony",
    "microsoft", "apple", "google", "amazon", "tesla", "spacex", "f1", "nba", "nfl", "mlb",
    "spiderman", "spider-man", "batman", "superman", "avengers", "mickey", "frozen",
    "fortnite", "roblox", "minecraft", "pokemon", "zelda", "mario", "sonic",
    "taylor swift", "beyonce", "drake", "kanye", "bts", "twice", "blackpink",
    "hazbin hotel", "helluva boss", "deltarune", "undertale", "genshin", "honkai",
    "nasa", "fbi", "cia", "usps", "stussy", "off-white", "yeezy"
]

# Generic terms to filter out
IGNORE_KEYWORDS = ["crossword", "clue", "meaning", "definition", "lyrics", "quotes", "size", "color", "red", "blue", "black", "white"]

def get_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    print(f"Fetching related queries for: {KW_LIST}")
    pytrends.build_payload(KW_LIST, cat=0, timeframe='now 1-d', geo='', gprop='')
    related_queries = pytrends.related_queries()

    all_rising = []
    for kw in KW_LIST:
        res = related_queries.get(kw)
        if res and res.get('rising') is not None and not res['rising'].empty:
            all_rising.append(res['rising'])

    if not all_rising:
        return pd.DataFrame()

    df = pd.concat(all_rising).drop_duplicates(subset=['query'])
    return df

def is_ip_infringing(query):
    query_lower = query.lower()
    for ip_kw in IP_KEYWORDS:
        if ip_kw in query_lower:
            return True
    return False

def generate_idea(query):
    query_lower = query.lower()
    if "funny" in query_lower:
        return "Focus on a humorous graphic or text-based design. High engagement on social media."
    elif any(term in query_lower for term in ["vintage", "retro", "90s", "80s"]):
        return "Use distressed textures and retro color palettes (neon, earth tones)."
    elif "cool" in query_lower:
        return "Trendy aesthetic, possibly minimalist or street-style oriented."
    elif "merch" in query_lower:
        item = query_lower.replace("merch", "").strip()
        return f"Fans are looking for {item} gear. Create inspired (non-infringing) designs that capture the 'vibe' of the fandom."
    elif any(term in query_lower for term in ["shirt", "tshirt", "t-shirt", "tank top"]):
        return "Rising niche demand. Analyze the specific topic and create a targeted design for this audience."
    else:
        return "Emerging trend. Consider a unique artistic interpretation or a typography-focused design that resonates with the search intent."

def format_table(df):
    if df.empty:
        return "No significant trends found in this category today."

    df = df.sort_values(by='value', ascending=False)

    table = "| Keyword | Score | Why / Idea |\n"
    table += "| :--- | :--- | :--- |\n"
    for _, row in df.iterrows():
        idea = generate_idea(row['query'])
        table += f"| {row['query']} | {row['value']} | {idea} |\n"
    return table

def main():
    df = get_trends()
    if df.empty:
        print("No trends found.")
        return

    df = df[~df['query'].str.contains('|'.join(IGNORE_KEYWORDS), case=False, na=False)]
    df['is_merch'] = df['query'].apply(lambda x: any(term in x.lower() for term in MERCH_TERMS))
    df['word_count'] = df['query'].apply(lambda x: len(x.split()))
    df = df[(df['is_merch']) | (df['word_count'] >= 3)]
    df['is_ip'] = df['query'].apply(is_ip_infringing)

    general_df = df[~df['is_ip']]
    ip_df = df[df['is_ip']]

    date_str = datetime.now().strftime("%Y-%m-%d")

    new_section = f"## {date_str}\n\n"
    new_section += "### General Merch Opportunities\n"
    new_section += format_table(general_df) + "\n\n"
    new_section += "### Potential IP Infringing Opportunities\n"
    new_section += format_table(ip_df) + "\n\n"
    new_section += "---\n"

    header = "# Merch Design Trends\n\n"

    if os.path.exists("trends.md"):
        with open("trends.md", "r") as f:
            content = f.read()
    else:
        content = ""

    # Check if we already added today's data (to avoid duplication)
    if f"## {date_str}" in content:
        print(f"Trends for {date_str} already exist in trends.md. Skipping.")
        return

    # Prepend new content
    if not content:
        final_content = header + new_section
    else:
        # Prepend to the top after the header
        body = content.replace(header, "")
        final_content = header + new_section + "\n" + body

    with open("trends.md", "w") as f:
        f.write(final_content)

    print(f"Successfully updated trends.md with trends for {date_str}.")

if __name__ == "__main__":
    main()
