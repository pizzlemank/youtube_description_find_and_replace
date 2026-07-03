import pandas as pd
from pytrends.request import TrendReq
import datetime
import os
import re
import time

# Configuration
SEED_KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]
TRENDS_FILE = "trends.md"
# Initial IP Blacklist - can be expanded
IP_BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "taylor swift", "bts",
    "michael jackson", "nba", "wnba", "nfl", "mlb", "nhl", "nintendo",
    "pokemon", "harry potter", "nasa", "hellstar", "ysl", "gucci", "prada",
    "louis vuitton", "arsenal", "real madrid", "liverpool", "man city",
    "chelsea", "bayern", "barcelona", "knicks", "lakers", "celtics",
    "warriors", "bulls", "amiri", "trapstar", "corteiz", "sp5der",
    "minus two", "syna world", "ye", "kanye", "psg", "noah kahan",
    "radiohead", "bruno mars", "my chemical romance", "mcr", "jackass",
    "john deere", "wimbledon", "alan jackson"
]

def get_rising_queries(pytrends, keyword):
    print(f"Fetching rising queries for: {keyword}")
    for attempt in range(3):
        try:
            pytrends.build_payload([keyword], timeframe='now 7-d')
            related_queries = pytrends.related_queries()
            if keyword in related_queries and related_queries[keyword]['rising'] is not None:
                return related_queries[keyword]['rising']
            return pd.DataFrame()
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                print(f"Rate limited (429). Retrying in 10s... (Attempt {attempt+1}/3)")
                time.sleep(10)
                continue
            else:
                print(f"Error fetching data for {keyword}: {e}")
                return pd.DataFrame()
    return pd.DataFrame()

def is_ip_infringing(query):
    query_lower = query.lower()
    for brand in IP_BLACKLIST:
        if re.search(rf"\b{brand}\b", query_lower):
            return True
    return False

def generate_idea(keyword):
    # Simple logic to generate a design idea or rationale
    # Removes apparel terms to get the core topic
    core_topic = keyword
    for term in SEED_KEYWORDS:
        core_topic = re.sub(rf"\b{term}s?\b", "", core_topic, flags=re.IGNORECASE).strip()

    if not core_topic:
        core_topic = keyword

    return f"Capitalize on the rising interest in '{core_topic}'. Design could feature unique typography or graphic elements related to the theme."

def process_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    all_results = []
    seen_queries = set()

    for kw in SEED_KEYWORDS:
        df = get_rising_queries(pytrends, kw)
        if not df.empty:
            for _, row in df.iterrows():
                query = row['query']
                score = row['value']

                # Filter: Long tail (2+ words) and must contain an apparel term (though seeds usually ensure this)
                words = query.split()
                if len(words) < 2:
                    continue

                # Check if it contains any of the seed keywords to ensure it's apparel related
                if not any(term in query.lower() for term in SEED_KEYWORDS):
                    continue

                if query.lower() not in seen_queries:
                    all_results.append({
                        'keyword': query,
                        'score': score,
                        'is_ip': is_ip_infringing(query)
                    })
                    seen_queries.add(query.lower())

        # Sleep to avoid rate limiting
        time.sleep(5)

    if not all_results:
        print("No new trends found.")
        return

    # Separate into General and IP Infringing
    general = [r for r in all_results if not r['is_ip']]
    ip_infringing = [r for r in all_results if r['is_ip']]

    # Sort by score (Breakout is usually represented as a high number or string)
    def sort_key(x):
        try:
            return int(x['score'])
        except:
            return 99999 # Breakout

    general.sort(key=sort_key, reverse=True)
    ip_infringing.sort(key=sort_key, reverse=True)

    # Format Markdown
    today = datetime.date.today().strftime("%Y-%m-%d")
    md_content = f"## {today}\n\n### General Merch Opportunities\n"
    md_content += "| keyword | score | why you think is an opportunity, idea for design, or what the internet shopping is already doing |\n"
    md_content += "| :--- | :--- | :--- |\n"
    for item in general:
        md_content += f"| {item['keyword']} | {item['score']} | {generate_idea(item['keyword'])} |\n"

    md_content += "\n### Potential IP Infringing Opportunities\n"
    md_content += "| keyword | score | why you think is an opportunity, idea for design, or what the internet shopping is already doing |\n"
    md_content += "| :--- | :--- | :--- |\n"
    for item in ip_infringing:
        md_content += f"| {item['keyword']} | {item['score']} | {generate_idea(item['keyword'])} |\n"
    md_content += "\n---\n"

    # Prepend to trends.md
    if os.path.exists(TRENDS_FILE):
        with open(TRENDS_FILE, "r") as f:
            existing_content = f.read()

        # Check if today's header already exists to avoid double-posting
        today_header = f"## {today}"
        if today_header in existing_content:
            print(f"Data for {today} already exists in {TRENDS_FILE}. Skipping prepend.")
            return

        # Split by the main header and prepend
        header = "# Google Trends Merch Opportunities\n\n"
        if existing_content.startswith(header):
            new_content = header + md_content + existing_content[len(header):]
        else:
            new_content = header + md_content + existing_content
    else:
        new_content = "# Google Trends Merch Opportunities\n\n" + md_content

    with open(TRENDS_FILE, "w") as f:
        f.write(new_content)

    print(f"Updated {TRENDS_FILE} with {len(all_results)} trends.")

if __name__ == "__main__":
    process_trends()
