import time
import datetime
import os
import re
from pytrends.request import TrendReq
import pandas as pd

# Keywords to track
SEED_KEYWORDS = ['tshirt', 'shirt', 'tank top', 'merch', 'tee']

# Brand/IP Blacklist (Expanded)
IP_BLACKLIST = [
    'disney', 'marvel', 'star wars', 'mickey', 'nike', 'adidas', 'nfl', 'nba', 'mlb',
    'pokemon', 'nintendo', 'harry potter', 'netflix', 'looney tunes', 'warner bros',
    'nasa', 'national geographic', 'gucci', 'prada', 'chanel', 'supreme', 'stussy',
    'taylor swift', 'beyonce', 'bts', 'drake', 'anime', 'manga', 'naruto', 'one piece',
    'dragon ball', 'bluey', 'barbie', 'sanrio', 'hello kitty', 'snoopy', 'peanuts',
    'pixar', 'dc comics', 'batman', 'superman', 'wonder woman', 'spider-man', 'avengers',
    'iron man', 'captain america', 'thor', 'hulk', 'black panther', 'star trek',
    'game of thrones', 'stranger things', 'squid game', 'friends', 'the office',
    'rock band', 'rolling stones', 'led zeppelin', 'pink floyd', 'metallica', 'ac/dc',
    'bieber', 'michael jackson', 'jackson'
]

# Negative keywords to filter out non-merch intent
NEGATIVE_KEYWORDS = [
    'meaning', 'definition', 'how to', 'why', 'iron', 'near me', 'template', 'mockup',
    'vector', 'png', 'svg', 'free', 'cheap', 'wholesale', 'manufacturer', 'printing',
    'custom', 'personalize', 'maker', 'generator', 'tee time', 'tee off'
]

def is_ip_infringing(keyword):
    keyword_lower = keyword.lower()
    for brand in IP_BLACKLIST:
        if re.search(rf'\b{brand}\b', keyword_lower):
            return True
    return False

def is_relevant_long_tail(keyword):
    kw_lower = keyword.lower()
    # Must contain an apparel term
    apparel_terms = ['shirt', 'tshirt', 't-shirt', 'tanktop', 'tank top', 'tee']
    has_apparel = any(term in kw_lower for term in apparel_terms)

    # Must not be just the apparel term
    words = kw_lower.split()
    is_long_tail = len(words) >= 2

    # Check negative keywords
    has_negative = any(neg in kw_lower for neg in NEGATIVE_KEYWORDS)

    return has_apparel and is_long_tail and not has_negative

def get_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    all_data = []

    for seed in SEED_KEYWORDS:
        try:
            print(f"Fetching trends for: {seed}")
            pytrends.build_payload([seed], timeframe='now 7-d')
            related = pytrends.related_queries()

            if seed in related and related[seed]['rising'] is not None:
                df = related[seed]['rising']
                for _, row in df.iterrows():
                    query = row['query']
                    score = row['value']

                    if is_relevant_long_tail(query):
                        all_data.append({
                            'keyword': query,
                            'score': score
                        })
            time.sleep(2) # Small delay to avoid 429
        except Exception as e:
            print(f"Error fetching {seed}: {e}")
            if "429" in str(e):
                print("Rate limited. Sleeping...")
                time.sleep(10)

    return all_data

def generate_merch_idea(keyword):
    kw = keyword.lower()
    if 'cat' in kw:
        return "Niche cat-themed design. Suggest minimalist line art or funny text."
    if 'dog' in kw:
        return "Dog breed specific or general pet lover design."
    if 'funny' in kw or 'joke' in kw:
        return "Humorous typography-based design."
    if 'vintage' in kw or 'retro' in kw:
        return "Distressed, 70s/80s style graphic."
    if 'quote' in kw:
        return "Inspirational or sarcastic quote in trendy font."

    return "Rising trend; identify the core audience and create a unique graphic or slogan."

def update_trends_md(data):
    today = datetime.date.today().strftime("%Y-%m-%d")

    # Deduplicate and sort by score descending
    unique_data = {}
    for item in data:
        kw = item['keyword']
        # Google Trends can return 'Breakout' as a score. Handle it as a high numeric value for comparison.
        current_score = 999999 if item['score'] == 'Breakout' else (item['score'] if isinstance(item['score'], int) else 0)

        if kw not in unique_data:
            unique_data[kw] = item
        else:
            existing_score_raw = unique_data[kw]['score']
            existing_score = 999999 if existing_score_raw == 'Breakout' else (existing_score_raw if isinstance(existing_score_raw, int) else 0)
            if current_score > existing_score:
                unique_data[kw] = item

    sorted_items = sorted(unique_data.values(), key=lambda x: 999999 if x['score'] == 'Breakout' else (x['score'] if isinstance(x['score'], int) else 0), reverse=True)

    general = []
    ip_infringing = []

    for item in sorted_items:
        kw = item['keyword']
        score = item['score']
        idea = generate_merch_idea(kw)
        row = f"| {kw} | {score} | {idea} |"

        if is_ip_infringing(kw):
            ip_infringing.append(row)
        else:
            general.append(row)

    # Prepare content
    new_content = f"## {today}\n\n"

    new_content += "### General Merch Opportunities\n"
    new_content += "| Keyword | Score | Why/Idea |\n"
    new_content += "| --- | --- | --- |\n"
    if general:
        new_content += "\n".join(general) + "\n\n"
    else:
        new_content += "No new general opportunities found today.\n\n"

    new_content += "### Potential IP Infringing Opportunities\n"
    new_content += "| Keyword | Score | Why/Idea |\n"
    new_content += "| --- | --- | --- |\n"
    if ip_infringing:
        new_content += "\n".join(ip_infringing) + "\n\n"
    else:
        new_content += "No new IP infringing opportunities found today.\n\n"

    # Read existing content
    if os.path.exists('trends.md'):
        with open('trends.md', 'r') as f:
            existing_content = f.read()
            if f"## {today}" in existing_content:
                print(f"Trends for {today} already exist in trends.md. Appending anyway or skipping?")
                # For now, let's skip to avoid duplication if run multiple times a day
                return
    else:
        existing_content = ""

    with open('trends.md', 'w') as f:
        f.write(new_content + existing_content)

if __name__ == "__main__":
    trends_data = get_trends()
    if trends_data:
        update_trends_md(trends_data)
        print("Updated trends.md successfully.")
    else:
        # If no data found, maybe try again later or just log it
        print("No rising apparel-related data fetched today.")
