import pandas as pd
from pytrends.request import TrendReq
from datetime import datetime
import os
import time

# List of common IP/Brands to flag
IP_KEYWORDS = [
    'nike', 'adidas', 'disney', 'marvel', 'star wars', 'nintendo', 'pokemon',
    'anime', 'manga', 'netflix', 'hulu', 'hbo', 'warner bros', 'universal',
    'gucci', 'prada', 'louis vuitton', 'chanel', 'supreme', 'off-white',
    'nba', 'nfl', 'mlb', 'nhl', 'premier league', 'fifa', 'f1', 'nascar',
    'harry potter', 'lord of the rings', 'game of thrones', 'stranger things',
    'barbie', 'hot wheels', 'lego', 'minecraft', 'roblox', 'fortnite',
    'band', 'concert', 'tour', 'album', 'singer', 'rapper', 'artist',
    'hannah montana', 'rcb', 'ipl', 'ncaa', 'final four', 'world cup',
    'taylor swift', 'beyonce', 'bts', 'blackpink', 'k-pop', 'kpop',
    'sanrio', 'hello kitty', 'bluey', 'peppa pig', 'paw patrol',
    'nike', 'puma', 'reebok', 'under armour', 'lululemon'
]

# Generic terms to filter out (too broad)
GENERIC_TERMS = [
    'shirt', 'tshirt', 't shirt', 't-shirt', 'tee', 'teeshirt',
    'tank top', 'tanktop', 'merch', 'merchandise', 'clothing',
    'apparel', 'fashion', 'style', 'design', 'custom', 'personalized',
    'men', 'women', 'kids', 'boys', 'girls', 'unisex', 'size', 'color',
    'white', 'black', 'blue', 'red', 'green', 'yellow', 'pink', 'purple'
]

def is_ip_infringing(keyword):
    keyword_lower = keyword.lower()
    for ip in IP_KEYWORDS:
        if ip in keyword_lower:
            return True
    return False

def get_opportunity_analysis(keyword):
    # Simple heuristic for "why/idea"
    keyword_lower = keyword.lower()
    if 'meme' in keyword_lower:
        return "Trending meme; design should be humorous and timely. High potential for viral sharing."
    if 'vintage' in keyword_lower or 'retro' in keyword_lower:
        return "Nostalgia factor; use distressed textures and 80s/90s color palettes. Popular for casual wear."
    if 'quote' in keyword_lower or 'saying' in keyword_lower:
        return "Typography focused; use bold, readable fonts. Great for gift-giving niches."
    if is_ip_infringing(keyword):
        return "Potential IP risk; likely a brand or franchise. Consider checking if it's a parody opportunity or avoid."

    return "Rising interest; investigate if this is tied to a specific subculture or event. Design could be a direct text-based graphic."

def fetch_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    seed_keywords = ["tshirt", "shirt", "tank top", "merch"]

    all_rising = []

    for kw in seed_keywords:
        print(f"Fetching trends for: {kw}")
        try:
            pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='', gprop='')
            related = pytrends.related_queries()

            if kw in related and related[kw]['rising'] is not None:
                rising_df = related[kw]['rising']
                all_rising.append(rising_df)

            # Sleep to avoid rate limiting
            time.sleep(2)
        except Exception as e:
            print(f"Error fetching {kw}: {e}")

    if not all_rising:
        return pd.DataFrame()

    combined_df = pd.concat(all_rising).drop_duplicates(subset=['query'])

    # Filter out very generic keywords that are just the seed words themselves or colors
    def is_too_generic(q):
        q = q.lower()
        if q in GENERIC_TERMS:
            return True
        # If it's just "color tshirt" etc.
        words = q.split()
        if len(words) <= 1:
             return True
        return False

    combined_df = combined_df[~combined_df['query'].apply(is_too_generic)]

    return combined_df

def format_markdown_table(df):
    if df.empty:
        return "No new trends found today."

    header = "| keyword | score | why you think is an opportunity, idea for design, or what the internet shopping is already doing|\n| :--- | :--- | :--- |\n"
    rows = []
    for _, row in df.iterrows():
        kw = row['query']
        score = row['value']
        analysis = get_opportunity_analysis(kw)
        rows.append(f"| {kw} | {score} | {analysis} |")

    return header + "\n".join(rows)

def update_trends_file():
    df = fetch_trends()

    if df.empty:
        print("No trends found.")
        return

    # Split into IP and General
    df['is_ip'] = df['query'].apply(is_ip_infringing)

    ip_df = df[df['is_ip']]
    general_df = df[~df['is_ip']]

    date_str = datetime.now().strftime("%Y-%m-%d")
    date_header = f"## {date_str}"

    new_content = f"{date_header}\n\n"

    new_content += "### General Merch Opportunities\n"
    new_content += format_markdown_table(general_df) + "\n\n"

    new_content += "### Potential IP Infringing Opportunities\n"
    new_content += format_markdown_table(ip_df) + "\n\n"

    file_path = "trends.md"
    main_title = "# Tshirt Merch Trends\n\n"
    description = "*Daily updates on rising Google Trends for Print-on-Demand (POD) opportunities.*\n\n"

    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            existing_content = f.read()

        # Avoid duplicate entries for the same day
        if date_header in existing_content:
            print(f"Trends for {date_str} already exist in {file_path}. Skipping update.")
            return

        # Prepend new content after title and description
        header_to_keep = main_title + description
        if existing_content.startswith(main_title):
            # Try to remove title and description if they exist
            content_to_strip = existing_content
            if content_to_strip.startswith(header_to_keep):
                content_to_strip = content_to_strip.replace(header_to_keep, "", 1)
            else:
                content_to_strip = content_to_strip.replace(main_title, "", 1)

            updated_content = header_to_keep + new_content + content_to_strip
        else:
            updated_content = header_to_keep + new_content + existing_content
    else:
        updated_content = header_to_keep + new_content

    with open(file_path, 'w') as f:
        f.write(updated_content)

    print(f"Updated {file_path} successfully.")

if __name__ == "__main__":
    update_trends_file()
