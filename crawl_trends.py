import pandas as pd
from pytrends.request import TrendReq
import datetime
import os
import time

# List of seed keywords to find trends for
SEED_KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]

# Common IP-heavy keywords to flag
IP_BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "taylor swift", "bts",
    "michael jackson", "nba", "wnba", "nfl", "mlb", "nhl", "nintendo", "pokemon",
    "harry potter", "nasa", "hellstar", "ysl", "gucci", "prada", "louis vuitton",
    "arsenal", "real madrid", "liverpool", "man city", "chelsea", "bayern", "barcelona",
    "knicks", "lakers", "celtics", "warriors", "bulls", "amiri", "trapstar", "corteiz",
    "sp5der", "minus two", "syna world", "harry styles", "gracie abrams", "daniel caesar",
    "bad bunny", "billie eilish", "drake", "kanye", "travis scott", "bruno mars",
    "hello kitty", "sanrio", "nascar", "f1", "mercedes", "ferrari", "red bull",
    "toy story", "psg", "asap rocky", "megan moroney", "sean john", "morgan wallen",
    "spurs", "rcb", "snipes", "asos", "pattie gonia", "wingstop"
]

# Keywords to exclude (informational or irrelevant)
EXCLUDE_KEYWORDS = [
    "meaning", "definition", "how to", "why", "iron", "near me", "template", "mockup",
    "tee times", "tee time", "tee off", "graphic tee", "essential tee", "vintage tee",
    "oversized tee", "plain shirt", "blank shirt", "kaffee", "rezepte", "bh für", "bra for",
    "tutorial", "là gì"
]

def is_ip_infringing(keyword):
    keyword_lower = keyword.lower()
    for ip in IP_BLACKLIST:
        if ip in keyword_lower:
            return True
    return False

def generate_idea(keyword):
    # Simple logic to generate an idea or comment
    keyword_clean = keyword.lower()
    # Replace longer terms first to avoid partial replacements (e.g., 'tshirt' before 'shirt')
    sorted_seeds = sorted(SEED_KEYWORDS, key=len, reverse=True)
    for term in sorted_seeds:
        keyword_clean = keyword_clean.replace(term, "").strip()

    # Remove extra spaces
    keyword_clean = " ".join(keyword_clean.split())

    if not keyword_clean:
        return "Generic apparel search. Look for specific niches."

    return f"Design featuring '{keyword_clean.title()}'. Internet is searching for this specific term. Could be a minimalist typography or a graphic representation of {keyword_clean}."

def crawl():
    # hl='en-US', tz=360
    # Custom retry logic for 429
    pytrends = TrendReq(hl='en-US', tz=360)

    all_results = []

    for kw in SEED_KEYWORDS:
        print(f"Fetching trends for: {kw}")
        retries = 3
        while retries > 0:
            try:
                pytrends.build_payload([kw], timeframe='now 7-d')
                related = pytrends.related_queries()

                if kw in related and related[kw]['rising'] is not None:
                    df = related[kw]['rising']
                    for index, row in df.iterrows():
                        query = row['query']
                        score = row['value']

                        # Filter for long-tail (at least 2 words)
                        if len(query.split()) >= 2:
                            query_lower = query.lower()
                            # Ensure it's not just the seed keyword itself
                            if query_lower == kw.lower():
                                continue

                            # Filter out excluded keywords
                            if any(ex in query_lower for ex in EXCLUDE_KEYWORDS):
                                continue

                            all_results.append({
                                'keyword': query,
                                'score': score,
                                'is_ip': is_ip_infringing(query)
                            })
                time.sleep(5) # Avoid rate limiting between keywords
                break # Success
            except Exception as e:
                print(f"Error fetching {kw}: {e}")
                if "429" in str(e):
                    print("Rate limited. Waiting 60s...")
                    time.sleep(60)
                    retries -= 1
                else:
                    break # Other error, skip

    # Deduplicate
    unique_results = {res['keyword']: res for res in all_results}.values()

    # Sort results by score (descending)
    # 'Breakout' is often represented as a string, handle it
    def get_score_val(x):
        if isinstance(x, str) and 'breakout' in x.lower():
            return 9999
        try:
            return int(x)
        except:
            return 0

    sorted_results = sorted(unique_results, key=lambda x: get_score_val(x['score']), reverse=True)

    general_merch = []
    ip_infringing = []

    for res in sorted_results:
        idea = generate_idea(res['keyword'])
        entry = f"| {res['keyword']} | {res['score']} | {idea} |"
        if res['is_ip']:
            ip_infringing.append(entry)
        else:
            general_merch.append(entry)

    return general_merch, ip_infringing

def update_markdown(general, ip_infringing):
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    filename = "trends.md"

    # Check if we already updated today
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
            if f"## {date_str}" in content:
                print(f"Trends for {date_str} already exist in {filename}. Skipping.")
                return

    header = f"## {date_str}\n\n### General Merch Opportunities\n| Keyword | Score | Why/Idea |\n| --- | --- | --- |\n"

    general_content = "\n".join(general) if general else "| No trends found | - | - |"
    ip_header = "\n\n### Potential IP Infringing Opportunities\n| Keyword | Score | Why/Idea |\n| --- | --- | --- |\n"
    ip_content = "\n".join(ip_infringing) if ip_infringing else "| No potential IP issues found | - | - |"

    new_entry = header + general_content + ip_header + ip_content + "\n\n---\n\n"

    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            current_content = f.read()
    else:
        current_content = "# Google Trends Merch Crawler Results\n\n"

    # Find the first H2 or where to insert after the title
    # We want it right after the title to keep it latest first
    title_line = "# Google Trends Merch Crawler Results"
    if title_line in current_content:
        insertion_point = current_content.find(title_line) + len(title_line)
        # Advance to next double newline
        next_double_nl = current_content.find("\n\n", insertion_point)
        if next_double_nl != -1:
            updated_content = current_content[:next_double_nl+2] + new_entry + current_content[next_double_nl+2:]
        else:
            updated_content = current_content + "\n\n" + new_entry
    else:
        updated_content = "# Google Trends Merch Crawler Results\n\n" + new_entry + current_content

    with open(filename, "w", encoding="utf-8") as f:
        f.write(updated_content)

if __name__ == "__main__":
    general, ip = crawl()
    if general or ip:
        update_markdown(general, ip)
        print("trends.md updated successfully.")
    else:
        print("No new trends found today.")
