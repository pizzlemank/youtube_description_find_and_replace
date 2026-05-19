import pandas as pd
from pytrends.request import TrendReq
import time
import datetime
import os
import re

# Configuration
KEYWORDS = ['tshirt', 't-shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch']
TIMEFRAME = 'now 7-d'  # Last 7 days
TRENDS_FILE = 'trends.md'

BRAND_BLACKLIST = [
    'disney', 'marvel', 'star wars', 'nike', 'adidas', 'taylor swift', 'bts',
    'michael jackson', 'nba', 'wnba', 'nfl', 'mlb', 'nhl', 'nintendo', 'pokemon',
    'harry potter', 'nasa', 'hellstar', 'ysl', 'gucci', 'prada', 'louis vuitton',
    'koningsdag', 'oranje', 'higgins', 'wwe', 'kanye', 'drake', 'notre dame',
    'ariana grande', 'george strait', 'olivia dean', 'conan gray', 'man utd',
    'lidl', 'm&s', 'mnet', 'amc', 'murder drones', 'luke combs', 'ohio state',
    'ufc', 'f1', 'nascar', 'sanrio', 'hello kitty', 'stussy', 'mclaren',
    'deftones', 'cleetus mcfarland', 'the neighbourhood', 'bring me the horizon',
    'khan asadi', 'lyrebird', 'anthropologie', 'carson hocevar', 'rihanna',
    'morgan wallen', 'valorant', 'kentucky derby', 'victoria beckham',
    'kimi antonelli', 'no doubt', 'bad omens', 'good mythical morning',
    'riley green', 'ella langley', 'candace owens', 'g59', 'grey59', 'greyfivenine',
    'of the trees', 'harry styles', 'gracie abrams', 'daniel caesar', 'jul',
    'rcb', 'pga championship', 'edc', 'suzan en freek', 'kaulitz hills', 'qsmp', 'ovo'
]

EXCLUSION_KEYWORDS = [
    'meaning', 'definition', 'how to', 'why', 'iron', 'near me', 'template',
    'mockup', 'tee times', 'tee time', 'tee off', 'graphic tee', 'essential tee',
    'vintage tee', 'oversized tee', 'plain shirt', 'blank shirt', 'là gì',
    'kaffee', 'rezepte', 'bh für', 'bra for', 'how to', 'tutorial'
]

def is_ip_infringing(keyword):
    keyword_lower = keyword.lower()
    for brand in BRAND_BLACKLIST:
        if brand in keyword_lower:
            return True
    return False

def is_valid_merch_keyword(keyword):
    kw_lower = keyword.lower()
    # Must have at least 2 words
    if len(kw_lower.split()) < 2:
        return False
    # Must contain one of the apparel terms
    apparel_terms = ['shirt', 'tshirt', 't-shirt', 'tank top', 'tanktop', 'tee', 'merch']
    if not any(term in kw_lower for term in apparel_terms):
        return False
    # Exclude non-commercial/noise keywords
    if any(ex in kw_lower for ex in EXCLUSION_KEYWORDS):
        return False
    return True

def generate_idea(keyword):
    kw_lower = keyword.lower()
    # Simple logic to extract the "topic" and suggest a design
    topic = kw_lower
    # Replace longer terms first to avoid partial replacement issues
    for term in sorted(['t-shirt', 'tshirt', 't shirt', 'tank top', 'tanktop', 'shirt', 'tee', 'merch'], key=len, reverse=True):
        topic = topic.replace(term, '').strip()

    # Clean up multiple spaces
    topic = re.sub(' +', ' ', topic)

    if not topic:
        return "Trending apparel search. Design should focus on the exact keyword."

    return f"Design featuring '{topic}'. Possible graphic or typography style trending on search."

def get_trends():
    # hl='en-US', tz=360 (CST)
    pytrends = TrendReq(hl='en-US', tz=360)
    all_data = []

    for kw in KEYWORDS:
        print(f"Fetching trends for: {kw}")
        try:
            # Pytrends sometimes fails with 429, implement a simple retry
            success = False
            for attempt in range(3):
                try:
                    # In newer versions of urllib3, method_whitelist is renamed to allowed_methods
                    # Pytrends might still use old parameters in its sessions.
                    # Let's try to handle it more robustly or just wrap the call.
                    pytrends.build_payload([kw], timeframe=TIMEFRAME)
                    related_queries = pytrends.related_queries()
                    success = True
                    break
                except Exception as e:
                    print(f"Attempt {attempt+1} failed for {kw}: {e}")
                    if ("429" in str(e) or "Too Many Requests" in str(e)) and attempt < 2:
                        print(f"Rate limited for {kw}. Waiting 30s...")
                        time.sleep(30)
                    else:
                        break

            if success and kw in related_queries:
                rising = related_queries[kw]['rising']
                if rising is not None and not rising.empty:
                    for index, row in rising.iterrows():
                        query = row['query']
                        value = row['value']
                        if is_valid_merch_keyword(query):
                            all_data.append({
                                'keyword': query,
                                'score': value,
                                'infringing': is_ip_infringing(query)
                            })
            time.sleep(5) # Delay between keywords to avoid rate limit
        except Exception as e:
            print(f"Error processing {kw}: {e}")

    return all_data

def format_score(score):
    if score == 'Breakout' or str(score) == '9999' or score == 9999:
        return 'Breakout'
    return str(score)

def update_trends_md(data):
    today = datetime.date.today().strftime("%Y-%m-%d")

    if not data:
        print("No new trends found today.")
        # Even if no data, we should at least check if file exists
        if not os.path.exists(TRENDS_FILE):
             with open(TRENDS_FILE, 'w') as f:
                 f.write("# Google Trends Merch Opportunities\n\n")
        return

    # Deduplicate data
    unique_data = []
    seen = set()
    for item in data:
        if item['keyword'] not in seen:
            unique_data.append(item)
            seen.add(item['keyword'])

    # Sort by score (Breakout is highest)
    def score_val(x):
        val = x['score']
        if val == 'Breakout': return 9999
        try:
            return int(val)
        except:
            return 0

    unique_data.sort(key=score_val, reverse=True)

    general = [d for d in unique_data if not d['infringing']]
    infringing = [d for d in unique_data if d['infringing']]

    new_content = f"## {today}\n\n"

    new_content += "### General Merch Opportunities\n"
    new_content += "| keyword | score | Why/Idea |\n"
    new_content += "| :--- | :--- | :--- |\n"
    for item in general:
        new_content += f"| {item['keyword']} | {format_score(item['score'])} | {generate_idea(item['keyword'])} |\n"

    new_content += "\n### Potential IP Infringing Opportunities\n"
    new_content += "| keyword | score | Why/Idea |\n"
    new_content += "| :--- | :--- | :--- |\n"
    for item in infringing:
        new_content += f"| {item['keyword']} | {format_score(item['score'])} | {generate_idea(item['keyword'])} |\n"

    new_content += "\n---\n"

    old_content = ""
    if os.path.exists(TRENDS_FILE):
        with open(TRENDS_FILE, 'r') as f:
            old_content = f.read()
    else:
        old_content = "# Google Trends Merch Opportunities\n\n"

    # Check if we already added today's data to avoid duplicates if run multiple times
    if f"## {today}" in old_content:
        print(f"Data for {today} already exists in {TRENDS_FILE}. Skipping append.")
        return

    # If it's a new file or doesn't have the title, ensure it's there
    if not old_content.startswith("# Google Trends Merch Opportunities"):
        old_content = "# Google Trends Merch Opportunities\n\n" + old_content

    # We want to insert after the title
    title_end = old_content.find("\n\n") + 2
    if title_end < 2: # No title found or weird format
         final_content = new_content + old_content
    else:
         final_content = old_content[:title_end] + new_content + old_content[title_end:]

    with open(TRENDS_FILE, 'w') as f:
        f.write(final_content)

    print(f"Updated {TRENDS_FILE} with {len(unique_data)} trends.")

if __name__ == "__main__":
    trends_data = get_trends()
    update_trends_md(trends_data)
