import os
import time
import datetime
import pandas as pd
from pytrends.request import TrendReq
from urllib3.exceptions import MaxRetryError

# Configuration
KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]
TIMEFRAME = "now 7-d"
GEO = ""  # Global
BRAND_BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "taylor swift", "bts",
    "michael jackson", "nba", "nfl", "mlb", "nhl", "nintendo", "pokemon",
    "harry potter", "nasa", "hellstar", "ysl", "gucci", "prada", "louis vuitton",
    "koningsdag", "oranje", "higgins", "wwe", "kanye", "drake", "notre dame",
    "ariana grande", "george strait", "olivia dean", "conan gray", "man utd",
    "lidl", "m&s", "mnet", "amc", "murder drones", "luke combs", "ohio state",
    "ufc", "f1", "nascar", "sanrio", "hello kitty", "stussy", "mclaren",
    "deftones", "cleetus mcfarland", "the neighbourhood", "bring me the horizon",
    "khan asadi", "lyrebird", "anthropologie", "carson hocevar", "rihanna",
    "morgan wallen", "valorant", "kentucky derby", "victoria beckham", "kimi antonelli"
]

EXCLUDE_KEYWORDS = [
    "meaning", "definition", "how to", "why", "iron", "near me", "template",
    "mockup", "tee times", "tee time", "tee off", "graphic tee", "essential tee",
    "vintage tee", "oversized tee", "plain shirt", "blank shirt", "là gì"
]

def get_pytrends():
    # Use custom retry logic instead of pytrends built-in to avoid 'method_whitelist' error in newer urllib3
    return TrendReq(hl='en-US', tz=360)

def fetch_rising_queries(pytrends, keyword):
    print(f"Fetching trends for: {keyword}")
    for attempt in range(3):
        try:
            pytrends.build_payload([keyword], timeframe=TIMEFRAME, geo=GEO)
            related = pytrends.related_queries()
            if keyword in related and related[keyword]['rising'] is not None:
                return related[keyword]['rising']
            return pd.DataFrame()
        except Exception as e:
            if "429" in str(e):
                wait = (attempt + 1) * 30
                print(f"Rate limited (429). Retrying in {wait}s...")
                time.sleep(wait)
            else:
                print(f"Error fetching {keyword}: {e}")
                break
    return pd.DataFrame()

def is_ip_infringing(query):
    query_lower = query.lower()
    for brand in BRAND_BLACKLIST:
        if brand in query_lower:
            return True
    return False

def is_valid_merch_query(query):
    query_lower = query.lower()
    # Must be at least 2 words
    if len(query_lower.split()) < 2:
        return False
    # Exclude non-commercial or irrelevant terms
    for exclude in EXCLUDE_KEYWORDS:
        if exclude in query_lower:
            return False
    return True

def generate_idea(query):
    query_lower = query.lower()
    # Simple logic to generate a "why/idea"
    idea = f"Rising search for '{query}'. "

    clean_query = query_lower
    for term in ["t-shirt", "tshirt", "t shirt", "shirt", "tank top", "tanktop", "tee", "merch"]:
        if term in clean_query:
            clean_query = clean_query.replace(term, "").strip()
            break

    if clean_query:
        idea += f"Focus on design elements related to '{clean_query}'. "

    idea += "Check current competitors on Amazon/Etsy for style inspiration (minimalist, vintage, or bold text)."
    return " ".join(idea.split())

def main():
    pytrends = get_pytrends()
    all_results = []
    seen_queries = set()

    for kw in KEYWORDS:
        df = fetch_rising_queries(pytrends, kw)
        if not df.empty:
            for _, row in df.iterrows():
                query = row['query']
                value = row['value']

                if query not in seen_queries and is_valid_merch_query(query):
                    seen_queries.add(query)

                    # Convert value to sortable score
                    score = 9999 if value == 'Breakout' else int(value)

                    item = {
                        'keyword': query,
                        'score': score,
                        'score_display': value,
                        'idea': generate_idea(query),
                        'is_ip': is_ip_infringing(query)
                    }
                    all_results.append(item)

        # Small delay to avoid rate limiting
        time.sleep(2)

    if not all_results:
        print("No new trends found.")
        return

    # Sort by score descending
    all_results.sort(key=lambda x: x['score'], reverse=True)

    # Separate into IP and General
    general = [r for r in all_results if not r['is_ip']]
    ip_infringing = [r for r in all_results if r['is_ip']]

    # Prepare markdown
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    md_content = f"## {date_str}\n\n"

    if general:
        md_content += "### General Merch Opportunities\n"
        md_content += "| Keyword | Score | Why/Idea |\n"
        md_content += "| :--- | :--- | :--- |\n"
        for r in general:
            md_content += f"| {r['keyword']} | {r['score_display']} | {r['idea']} |\n"
        md_content += "\n"

    if ip_infringing:
        md_content += "### Potential IP Infringing Opportunities\n"
        md_content += "| Keyword | Score | Why/Idea |\n"
        md_content += "| :--- | :--- | :--- |\n"
        for r in ip_infringing:
            md_content += f"| {r['keyword']} | {r['score_display']} | {r['idea']} |\n"
        md_content += "\n"

    # Write to trends.md (prepend)
    filename = "trends.md"
    existing_content = ""
    if os.path.exists(filename):
        with open(filename, "r") as f:
            existing_content = f.read()

    # Avoid duplicate for the same day
    if f"## {date_str}" in existing_content:
        print(f"Trends for {date_str} already exist in {filename}. Skipping.")
        return

    with open(filename, "w") as f:
        f.write(md_content + existing_content)

    print(f"Successfully updated {filename} with {len(all_results)} trends.")

if __name__ == "__main__":
    main()
