import time
import datetime
import os
import hashlib
import pandas as pd
from pytrends.request import TrendReq

# Configuration
KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]
BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "taylor swift", "bts",
    "michael jackson", "nba", "nfl", "mlb", "nhl", "nintendo", "pokemon",
    "harry potter", "nasa", "hellstar", "ysl", "gucci", "prada", "louis vuitton",
    "koningsdag", "oranje", "higgins", "wwe", "kanye", "drake", "notre dame",
    "ariana grande", "george strait", "olivia dean", "conan gray", "man utd",
    "lidl", "m&s", "mnet", "amc", "murder drones", "luke combs", "ohio state",
    "ufc", "f1", "nascar", "sanrio", "hello kitty", "stussy", "mclaren",
    "deftones", "cleetus mcfarland", "the neighbourhood", "bring me the horizon",
    "bmth", "khan asadi", "lyrebird", "anthropologie", "carson hocevar", "rihanna",
    "morgan wallen", "valorant", "kentucky derby", "victoria beckham", "kimi antonelli",
    "mercedes", "cadillac", "chevrolet", "ford", "bmw", "audi"
]

EXCLUDE_TERMS = [
    "meaning", "definition", "how to", "why", "iron", "near me",
    "là gì", "tee time", "tee times", "tee off", "template", "mockup",
    "graphic tee", "essential tee", "vintage tee", "oversized tee",
    "plain shirt", "blank shirt"
]

def get_pytrends_with_retry():
    """Initializes TrendReq."""
    return TrendReq(hl='en-US', tz=360)

def fetch_rising_queries(pytrends, kw):
    """Fetches rising related queries for a keyword with retries for 429 errors."""
    for attempt in range(3):
        try:
            pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='', gprop='')
            related_queries = pytrends.related_queries()
            if kw in related_queries and related_queries[kw]['rising'] is not None:
                return related_queries[kw]['rising']
            return None
        except Exception as e:
            if "429" in str(e):
                wait_time = 10 * (attempt + 1)
                print(f"Rate limited (429) for {kw}. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"Error fetching {kw}: {e}")
                break
    return None

def is_ip_infringing(query):
    query_lower = query.lower()
    for brand in BLACKLIST:
        if brand in query_lower:
            return True
    return False

def generate_idea(query):
    """Generates a simple design idea based on the query."""
    q = query.lower()
    # Clean up common terms to find the core subject
    subject = q
    # Sort terms by length descending to replace "t-shirt" before "shirt"
    terms_to_remove = sorted(["tshirt", "t-shirt", "t shirt", "shirt", "tank top", "tanktop", "merch", "tee"], key=len, reverse=True)
    for term in terms_to_remove:
        subject = subject.replace(term, "").strip()

    # Remove extra spaces
    subject = " ".join(subject.split())

    if not subject:
        return "Trending apparel search. Focus on minimal aesthetic and high-quality fabric feel."

    ideas = [
        f"Create a unique graphic for '{subject}' using a modern streetwear aesthetic.",
        f"Typography design: Use a bold, trendy font for the phrase '{subject}'.",
        f"Illustrative approach: Draw a custom character or scene representing '{subject}'.",
        f"Vintage vibe: Design a distressed, 90s-style bootleg tee for '{subject}'.",
        f"Niche appeal: Create a design that speaks directly to the '{subject}' subculture."
    ]

    idx = int(hashlib.md5(subject.encode()).hexdigest(), 16) % len(ideas)
    return ideas[idx] + " Seeing increased search interest."

def process_trends():
    pytrends = get_pytrends_with_retry()
    all_results = []
    seen_queries = set()

    for kw in KEYWORDS:
        print(f"Fetching trends for: {kw}")
        rising = fetch_rising_queries(pytrends, kw)
        if rising is not None:
            for _, row in rising.iterrows():
                query = str(row['query'])
                score = row['value']

                # Filter: Long tail (at least 2 words)
                if len(query.split()) < 2:
                    continue

                # Filter: Exclude non-commercial intent or irrelevant terms
                if any(x in query.lower() for x in EXCLUDE_TERMS):
                    continue

                if query in seen_queries:
                    continue
                seen_queries.add(query)

                is_ip = is_ip_infringing(query)
                idea = generate_idea(query)

                all_results.append({
                    'keyword': query,
                    'score': score,
                    'is_ip': is_ip,
                    'idea': idea
                })
        time.sleep(2) # Small delay between keywords

    if not all_results:
        print("No new trends found today.")
        return

    # Sort results by score (descending)
    def sort_key(x):
        s = x['score']
        if isinstance(s, str) and 'breakout' in s.lower():
            return 9999
        try:
            return int(s)
        except:
            return 0

    all_results.sort(key=sort_key, reverse=True)

    # Separate sections
    general_ops = [r for r in all_results if not r['is_ip']]
    ip_ops = [r for r in all_results if r['is_ip']]

    date_str = datetime.date.today().strftime("%Y-%m-%d")

    new_content = f"## {date_str}\n\n"

    new_content += "### General Merch Opportunities\n"
    if general_ops:
        new_content += "| keyword | score | why you think is an opportunity, idea for design, or what the internet shopping is already doing |\n"
        new_content += "| --- | --- | --- |\n"
        for r in general_ops:
            new_content += f"| {r['keyword']} | {r['score']} | {r['idea']} |\n"
    else:
        new_content += "No general opportunities found.\n"

    new_content += "\n### Potential IP Infringing Opportunities\n"
    if ip_ops:
        new_content += "| keyword | score | why you think is an opportunity, idea for design, or what the internet shopping is already doing |\n"
        new_content += "| --- | --- | --- |\n"
        for r in ip_ops:
            new_content += f"| {r['keyword']} | {r['score']} | {r['idea']} |\n"
    else:
        new_content += "No potential IP infringing opportunities found.\n"

    new_content += "\n---\n\n"

    # Prepend to trends.md
    file_path = "trends.md"
    existing_content = ""
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            existing_content = f.read()

        # Avoid duplicate entries for the same day
        if f"## {date_str}" in existing_content:
            # For this task, if it already exists, we might want to OVERWRITE or just SKIP.
            # Usually daily crawl happens once.
            print(f"Trends for {date_str} already exist in {file_path}. Skipping update.")
            return

    with open(file_path, "w") as f:
        f.write(new_content + existing_content)

    print(f"Successfully updated {file_path} with {len(all_results)} new keywords.")

if __name__ == "__main__":
    process_trends()
