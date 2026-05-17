import os
import time
from datetime import datetime
import pandas as pd
from pytrends.request import TrendReq

# Configuration
SEEDS = ['tshirt', 't-shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch']
# Comprehensive brand/person blacklist
BLACKLIST = [
    'disney', 'marvel', 'star wars', 'nike', 'adidas', 'taylor swift', 'bts',
    'michael jackson', 'nba', 'wnba', 'nfl', 'mlb', 'nhl', 'nintendo', 'pokemon',
    'harry potter', 'nasa', 'hellstar', 'ysl', 'gucci', 'prada', 'louis vuitton',
    'koningsdag', 'oranje', 'higgins', 'wwe', 'kanye', 'drake', 'notre dame',
    'ariana grande', 'george strait', 'olivia dean', 'conan gray', 'man utd',
    'lidl', 'm&s', 'mnet', 'amc', 'murder drones', 'luke combs', 'ohio state',
    'ufc', 'f1', 'nascar', 'sanrio', 'hello kitty', 'stussy', 'mclaren', 'deftones',
    'cleetus mcfarland', 'the neighbourhood', 'bring me the horizon', 'khan asadi',
    'lyrebird', 'anthropologie', 'carson hocevar', 'rihanna', 'morgan wallen',
    'valorant', 'kentucky derby', 'victoria beckham', 'kimi antonelli', 'no doubt',
    'bad omens', 'good mythical morning', 'riley green', 'ella langley', 'candace owens',
    'g59', 'grey59', 'greyfivenine', 'dr pepper', 'sean strickland', 'lorde', 'ovo',
    'pga', 'mcr', 'don toliver', 'of the trees'
]

NEGATIVES = [
    'meaning', 'definition', 'how to', 'why', 'iron', 'near me', 'template',
    'mockup', 'tee times', 'tee time', 'tee off', 'graphic tee', 'essential tee',
    'vintage tee', 'oversized tee', 'plain shirt', 'blank shirt', 'là gì', 'what does',
    'how much'
]

TRENDS_FILE = 'trends.md'

def get_rising_queries(pytrends, seed):
    retries = 3
    for i in range(retries):
        try:
            # We use a custom retry logic to avoid pytrends' own which sometimes fails with newer urllib3
            pytrends.build_payload(kw_list=[seed], timeframe='now 7-d', geo='US')
            related_queries = pytrends.related_queries()
            if seed in related_queries:
                return related_queries[seed]['rising']
        except Exception as e:
            print(f"Error fetching {seed} (attempt {i+1}/{retries}): {e}")
            if "429" in str(e):
                print("Rate limited. Waiting 60 seconds...")
                time.sleep(60)
            else:
                time.sleep(5)
    return None

def is_ip_infringing(keyword):
    k = keyword.lower()
    for brand in BLACKLIST:
        if brand in k:
            return True
    return False

def is_negative(keyword):
    k = keyword.lower()
    for neg in NEGATIVES:
        if neg in k:
            return True
    return False

def generate_idea(keyword):
    clean_kw = keyword.lower()
    # Prioritize longer replacements to avoid partial matches
    for term in ['t-shirt', 'tshirt', 't shirt', 'tank top', 'tanktop', 'merch', 'tee']:
        clean_kw = clean_kw.replace(term, '')

    # Remove extra spaces
    clean_kw = " ".join(clean_kw.split())
    clean_kw = clean_kw.strip().title()

    if not clean_kw:
        clean_kw = keyword.title()

    return f"High interest in '{clean_kw}'. Consider a design that references this trending topic using original artwork or a clever typography style that appeals to the niche."

def main():
    pytrends = TrendReq(hl='en-US', tz=360)
    all_results = []
    seen_keywords = set()

    for seed in SEEDS:
        print(f"Checking {seed}...")
        rising = get_rising_queries(pytrends, seed)
        if rising is not None and not rising.empty:
            for _, row in rising.iterrows():
                kw = row['query']
                score = row['value']

                # Basic filtering: Long tail (2+ words)
                words = kw.split()
                if len(words) < 2:
                    continue

                if is_negative(kw):
                    continue

                if kw in seen_keywords:
                    continue

                seen_keywords.add(kw)
                all_results.append({
                    'keyword': kw,
                    'score': score,
                    'is_ip': is_ip_infringing(kw)
                })
        time.sleep(5)

    if not all_results:
        print("No new trends found.")
        return

    # Sort results
    def sort_key(x):
        val = x['score']
        if isinstance(val, str):
            if 'Breakout' in val:
                return 999999
            try:
                return int(val.replace(',', '').replace('+', ''))
            except:
                return 0
        return val

    all_results.sort(key=sort_key, reverse=True)

    # Separate after sorting
    general = [r for r in all_results if not r['is_ip']]
    ip_infringing = [r for r in all_results if r['is_ip']]

    # Format Markdown
    today = datetime.now().strftime('%Y-%m-%d')

    if os.path.exists(TRENDS_FILE):
        with open(TRENDS_FILE, 'r') as f:
            if f"## {today}" in f.read():
                print(f"Entry for {today} already exists in {TRENDS_FILE}. Updating it.")
                # We will overwrite it for this run to ensure we get the latest
                pass

    output = f"\n## {today}\n\n"

    output += "### General Merch Opportunities\n"
    output += "| Keyword | Score | Why/Idea |\n"
    output += "|---------|-------|----------|\n"
    if not general:
        output += "| None found | - | - |\n"
    for r in general:
        output += f"| {r['keyword']} | {r['score']} | {generate_idea(r['keyword'])} |\n"

    output += "\n### Potential IP Infringing Opportunities\n"
    output += "| Keyword | Score | Why/Idea |\n"
    output += "|---------|-------|----------|\n"
    if not ip_infringing:
        output += "| None found | - | - |\n"
    for r in ip_infringing:
        output += f"| {r['keyword']} | {r['score']} | Likely IP protected ({r['keyword']}). Use for inspiration only or avoid. |\n"

    header = "# Google Trends Merch Opportunities\n"
    if os.path.exists(TRENDS_FILE):
        with open(TRENDS_FILE, 'r') as f:
            lines = f.readlines()

        # Remove old entry for today if it exists
        new_lines = []
        skip = False
        for line in lines:
            if line.startswith(f"## {today}"):
                skip = True
                continue
            if skip and line.startswith("## "):
                skip = False
            if not skip:
                new_lines.append(line)

        content = "".join(new_lines).replace(header, "").strip()
    else:
        content = ""

    with open(TRENDS_FILE, 'w') as f:
        f.write(header + output + "\n" + content)

    print(f"Updated {TRENDS_FILE} with {len(all_results)} trends.")

if __name__ == "__main__":
    main()
