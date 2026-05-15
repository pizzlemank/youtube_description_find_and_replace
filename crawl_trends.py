import os
import time
import datetime
import pandas as pd
from pytrends.request import TrendReq
from pytrends.exceptions import TooManyRequestsError

# Configuration
KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]
TIMEFRAME = 'now 7-d'
TRENDS_FILE = "trends.md"

# IP Infringing Blacklist (Keywords that suggest protected IP)
BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "taylor swift", "bts",
    "michael jackson", "nba", "wnba", "nfl", "mlb", "nhl", "nintendo", "pokemon",
    "harry potter", "nasa", "hellstar", "ysl", "gucci", "prada", "louis vuitton",
    "koningsdag", "oranje", "higgins", "wwe", "kanye", "drake", "notre dame",
    "ariana grande", "george strait", "olivia dean", "conan gray", "man utd",
    "lidl", "m&s", "mnet", "amc", "murder drones", "luke combs", "ohio state",
    "ufc", "f1", "nascar", "sanrio", "hello kitty", "stussy", "mclaren", "deftones",
    "cleetus mcfarland", "the neighbourhood", "bring me the horizon", "khan asadi",
    "lyrebird", "anthropologie", "carson hocevar", "rihanna", "morgan wallen",
    "valorant", "kentucky derby", "victoria beckham", "kimi antonelli", "no doubt",
    "bad omens", "good mythical morning", "riley green", "ella langley", "candace owens",
    "g59", "grey59", "greyfivenine", "of the trees"
]

EXCLUDE_TERMS = [
    "meaning", "definition", "how to", "why", "iron", "near me", "template", "mockup",
    "tee times", "tee time", "tee off", "graphic tee", "essential tee", "vintage tee",
    "oversized tee", "plain shirt", "blank shirt", "là gì"
]

def get_pytrends():
    return TrendReq(hl='en-US', tz=360)

def fetch_rising_queries(pytrends, keyword):
    print(f"Fetching rising queries for: {keyword}")
    retries = 3
    for i in range(retries):
        try:
            pytrends.build_payload([keyword], cat=0, timeframe=TIMEFRAME, geo='', gprop='')
            related_queries = pytrends.related_queries()
            if related_queries and keyword in related_queries:
                return related_queries[keyword]['rising']
            return None
        except TooManyRequestsError:
            wait_time = (i + 1) * 30
            print(f"Rate limited. Waiting {wait_time} seconds...")
            time.sleep(wait_time)
        except Exception as e:
            print(f"Error fetching {keyword}: {e}")
            break
    return None

def is_long_tail(query):
    return len(query.split()) >= 2

def contains_apparel_term(query):
    terms = ["shirt", "tshirt", "t-shirt", "tank top", "tanktop", "tee", "merch"]
    return any(term in query.lower() for term in terms)

def is_blacklisted(query):
    return any(brand in query.lower() for brand in BLACKLIST)

def is_excluded(query):
    return any(term in query.lower() for term in EXCLUDE_TERMS)

def generate_idea(keyword):
    # Simple logic to generate a design idea string
    clean_kw = keyword.lower()
    for term in ["t-shirt", "tshirt", "t shirt", "shirt", "tank top", "tanktop", "tee", "merch"]:
        clean_kw = clean_kw.replace(term, "").strip()

    clean_kw = " ".join(clean_kw.split()) # clean up spaces

    if not clean_kw:
        return "Generic apparel trend."

    return f"Create a design focusing on '{clean_kw}'. This is currently rising in search results."

def crawl():
    pytrends = get_pytrends()
    all_results = []
    seen_keywords = set()

    for kw in KEYWORDS:
        rising = fetch_rising_queries(pytrends, kw)
        if rising is not None and not rising.empty:
            for index, row in rising.iterrows():
                query = row['query']
                score = row['value']

                if query in seen_keywords:
                    continue

                if is_long_tail(query) and contains_apparel_term(query) and not is_excluded(query):
                    is_ip = is_blacklisted(query)
                    idea = generate_idea(query)
                    all_results.append({
                        'keyword': query,
                        'score': score,
                        'is_ip': is_ip,
                        'idea': idea
                    })
                    seen_keywords.add(query)

        # Small delay to avoid rate limiting
        time.sleep(5)

    if not all_results:
        print("No new trends found today.")
        return

    # Sort results by score (descending)
    # Handle 'Breakout' which pytrends returns for very fast rising terms
    def sort_score(val):
        if isinstance(val, str) and val.lower() == 'breakout':
            return 9999
        try:
            return int(val)
        except:
            return 0

    all_results.sort(key=lambda x: sort_score(x['score']), reverse=True)

    # Prepare Markdown
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    general_merch = [r for r in all_results if not r['is_ip']]
    ip_infringing = [r for r in all_results if r['is_ip']]

    new_content = f"## {today}\n\n"

    if general_merch:
        new_content += "### General Merch Opportunities\n"
        new_content += "| Keyword | Score | Why/Idea |\n"
        new_content += "|---------|-------|----------|\n"
        for r in general_merch:
            new_content += f"| {r['keyword']} | {r['score']} | {r['idea']} |\n"
        new_content += "\n"

    if ip_infringing:
        new_content += "### Potential IP Infringing Opportunities\n"
        new_content += "| Keyword | Score | Why/Idea |\n"
        new_content += "|---------|-------|----------|\n"
        for r in ip_infringing:
            new_content += f"| {r['keyword']} | {r['score']} | {r['idea']} (IP Warning) |\n"
        new_content += "\n"

    # Prepend to file
    if os.path.exists(TRENDS_FILE):
        with open(TRENDS_FILE, "r") as f:
            old_content = f.read()

        # Avoid duplicate entries for the same day if script is run multiple times
        if f"## {today}" in old_content:
            print(f"Results for {today} already exist in {TRENDS_FILE}. Skipping update.")
            return

        with open(TRENDS_FILE, "w") as f:
            f.write("# Google Trends Merch Opportunities\n\n" + new_content + old_content.replace("# Google Trends Merch Opportunities\n\n", ""))
    else:
        with open(TRENDS_FILE, "w") as f:
            f.write("# Google Trends Merch Opportunities\n\n" + new_content)

    print(f"Updated {TRENDS_FILE} with {len(all_results)} new trends.")

if __name__ == "__main__":
    crawl()
