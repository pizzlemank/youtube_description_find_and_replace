import os
import datetime
from pytrends.request import TrendReq
import pandas as pd

# Basic list of known brands/IPs to flag
IP_KEYWORDS = [
    'disney', 'marvel', 'star wars', 'bts', 'hannah montana', 'netflix',
    'nintendo', 'nike', 'adidas', 'apple', 'amazon', 'google', 'facebook',
    'instagram', 'tiktok', 'youtube', 'harry potter', 'pokemon', 'anime',
    'naruto', 'one piece', 'dragon ball', 'mickey', 'minnie', 'barbie',
    'lego', 'minecraft', 'roblox', 'fortnite', 'call of duty', 'nba', 'nfl',
    'mlb', 'nhl', 'taylor swift', 'beyonce', 'drake', 'kpop', 'bts', 'blackpink',
    'sanrio', 'hello kitty', 'bluey', 'peppa pig', 'marvel', 'dc comics',
    'batman', 'superman', 'spiderman', 'avengers', 'star trek', 'game of thrones'
]

GENERIC_KEYWORDS = [
    'white', 'black', 'blue', 'red', 'green', 'yellow', 'pink', 'purple',
    'orange', 'grey', 'gray', 'brown', 'men', 'women', 'mens', 'womens',
    'man', 'woman', 'unisex', 'cotton', 'polyester', 'size', 'small',
    'medium', 'large', 'xl', 'xxl', 'comfort colors', 'gildan', 'bella canvas',
    'plain', 'blank', 'wholesale', 'bulk', 'printing', 'custom', 'maker',
    'near me', 'h&m', 'zara', 'walmart', 'target', 'amazon'
]

def is_ip_infringing(query):
    query_lower = query.lower()
    for ip in IP_KEYWORDS:
        if ip in query_lower:
            return True
    return False

def is_generic(query):
    query_lower = query.lower()
    # If the query is just one of the seed keywords or generic terms
    seeds = ['tshirt', 't shirt', 'shirt', 'tank top', 'merch', 'tanktop']
    if query_lower in seeds:
        return True

    # Check if it's mostly generic
    words = query_lower.split()
    if all(word in GENERIC_KEYWORDS or word in seeds for word in words):
        return True

    return False

def get_opportunity_reason(query, value):
    query_lower = query.lower()

    is_breakout = False
    if isinstance(value, str) and value.lower() == 'breakout':
        is_breakout = True
        value_display = "BREAKOUT"
    else:
        try:
            val_int = int(value)
            value_display = f"+{val_int}%"
        except:
            value_display = str(value)
            val_int = 0

    reasons = []
    if 'wolf' in query_lower:
        reasons.append("Animal/Nature niche is evergreen. Wolf designs often have a 'cool' or 'lone wolf' appeal.")
    if 'cat' in query_lower or 'dog' in query_lower:
        reasons.append("Pet niches are highly profitable. Focus on specific breeds or funny pet traits.")
    if 'funny' in query_lower or 'meme' in query_lower:
        reasons.append("Humor-based designs spread well on social media.")
    if 'vintage' in query_lower or 'retro' in query_lower:
        reasons.append("Retro aesthetics (90s, 80s) are currently very popular in apparel.")
    if 'autism' in query_lower or 'awareness' in query_lower:
        reasons.append("Cause-based designs show strong community support and identity.")
    if 'love' in query_lower or 'i love' in query_lower:
        reasons.append("Expressive 'I Love' statements are simple and effective for POD.")

    if is_breakout:
        reasons.append("Breakout trend! Extremely high interest spike. High potential for quick sales.")
    elif val_int > 500:
        reasons.append(f"Huge growth ({value_display}). Strong market entry opportunity.")
    elif val_int > 200:
        reasons.append(f"Significant rising trend ({value_display}). Good momentum.")
    else:
        reasons.append(f"Rising interest ({value_display}). Worth exploring for niche designs.")

    return " ".join(reasons)

def crawl():
    pytrends = TrendReq(hl='en-US', tz=360)
    seeds = ['tshirt', 'shirt', 'tank top', 'merch']

    all_rising = []

    for seed in seeds:
        try:
            pytrends.build_payload([seed], cat=0, timeframe='now 7-d', geo='US', gprop='')
            related = pytrends.related_queries()
            if seed in related and related[seed]['rising'] is not None:
                rising_df = related[seed]['rising']
                all_rising.append(rising_df)
        except Exception as e:
            print(f"Error fetching for {seed}: {e}")

    if not all_rising:
        print("No rising trends found.")
        return

    df = pd.concat(all_rising).drop_duplicates(subset='query')

    # Filter out generic stuff
    df = df[~df['query'].apply(is_generic)]

    ip_infringing = []
    general_merch = []

    for _, row in df.iterrows():
        query = row['query']
        value = row['value']
        reason = get_opportunity_reason(query, value)

        # Format score for the table
        score_display = "BREAKOUT" if (isinstance(value, str) and value.lower() == 'breakout') else str(value)

        entry = f"| {query} | {score_display} | {reason} |"

        if is_ip_infringing(query):
            ip_infringing.append(entry)
        else:
            general_merch.append(entry)

    # Prepare markdown
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    new_content = f"# Google Trends Merch Opportunities - {date_str}\n\n"

    new_content += "## General Merch Opportunities\n"
    new_content += "| keyword | score | why you think is an opportunity, idea for design, or what the internet shopping is already doing |\n"
    new_content += "|---|---|---|\n"
    if general_merch:
        new_content += "\n".join(general_merch) + "\n"
    else:
        new_content += "| No new general opportunities found today. | - | - |\n"

    new_content += "\n## Potential IP Infringing Opportunities\n"
    new_content += "| keyword | score | why you think is an opportunity, idea for design, or what the internet shopping is already doing |\n"
    new_content += "|---|---|---|\n"
    if ip_infringing:
        new_content += "\n".join(ip_infringing) + "\n"
    else:
        new_content += "| No new IP infringing opportunities found today. | - | - |\n"

    new_content += "\n---\n\n"

    # Prepend to file
    existing_content = ""
    if os.path.exists("trends.md"):
        with open("trends.md", "r") as f:
            existing_content = f.read()

    with open("trends.md", "w") as f:
        f.write(new_content + existing_content)

if __name__ == "__main__":
    crawl()
