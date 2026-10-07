import datetime
import re
import time
from pytrends.request import TrendReq

# Seed keywords for POD merch discovery
SEED_KEYWORDS = [
    "tshirt",
    "t-shirt",
    "shirt",
    "tank top",
    "tanktop",
    "tee",
    "merch",
]

# Apparel keywords to verify presence in long-tail query
APPAREL_KEYWORDS = [
    "shirt",
    "tshirt",
    "t-shirt",
    "tank top",
    "tanktop",
    "tee",
    "merch",
]

# Apparel terms for cleaning/stripping when generating design ideas (sorted longest to shortest)
APPAREL_STRIP_TERMS = [
    "tank top",
    "tanktop",
    "t-shirts",
    "t-shirt",
    "tshirts",
    "tshirt",
    "shirts",
    "shirt",
    "tees",
    "tee",
    "merch",
]

# Generic apparel queries to exclude as noise
GENERIC_EXCLUSIONS = {
    "t shirt",
    "t shirts",
    "t-shirt",
    "t-shirts",
    "tshirt",
    "tshirts",
    "shirt",
    "shirts",
    "tee",
    "tees",
    "tank top",
    "tank tops",
    "tanktop",
    "tanktops",
    "merch",
    "t shirt design",
    "shirt design",
    "t shirt printing",
}

# Non-commercial / irrelevant query keywords
NOISE_KEYWORDS = [
    "meaning",
    "definition",
    "how to",
    "why",
    "iron",
    "near me",
    "template",
    "mockup",
    "tee times",
    "tee time",
    "tee off",
    "graphic tee",
    "essential tee",
    "vintage tee",
    "oversized tee",
    "plain shirt",
    "blank shirt",
    "kaffee",
    "rezepte",
    "bh für",
    "bra for",
    "tutorial",
    "bra",
    "t-shirt bra",
    "tee height",
    "là gì",
    "t-shirt femme",
    "custom t-shirt printing",
    "roblox t-shirt",
]

# IP Blacklist for identifying potential IP infringement
IP_BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "taylor swift", "bts",
    "michael jackson", "nba", "wnba", "nfl", "mlb", "nhl", "nintendo", "pokemon",
    "harry potter", "nasa", "hellstar", "ysl", "gucci", "prada", "louis vuitton",
    "arsenal", "real madrid", "liverpool", "man city", "chelsea", "bayern",
    "barcelona", "knicks", "lakers", "celtics", "warriors", "bulls", "amiri",
    "trapstar", "corteiz", "sp5der", "minus two", "syna world", "harry styles",
    "gracie abrams", "daniel caesar", "bad bunny", "billie eilish", "drake",
    "kanye", "travis scott", "bruno mars", "hello kitty", "sanrio", "nascar",
    "f1", "mercedes", "ferrari", "red bull", "toy story", "psg", "asap rocky",
    "megan moroney", "sean john", "morgan wallen", "spurs", "rcb", "snipes",
    "asos", "pattie gonia", "wingstop", "ariana grande", "selena gomez",
    "carhartt", "hazbin hotel", "digital circus", "tadc", "linkin park",
    "bad omens", "forrest frank", "malcolm todd", "böhse onkelz", "love island",
    "eternal sunshine", "madewell", "anthropologie", "glitch", "stevie nicks",
    "beyonce", "lilibet", "olivia rodrigo", "caitlin clark", "sabrina carpenter",
    "messi", "ronaldo", "spiderman", "spider-man", "batman", "superman",
    "fifa", "uefa", "palace", "kobe", "cowboys", "yankees", "dodgers", "dfb",
    "us open", "olympics", "cecil", "h&m", "levi's", "zara", "gap", "old navy",
    "lululemon", "patagonia", "north face", "under armour", "puma", "reebok",
    "vans", "converse", "stussy", "supreme", "hilary duff", "lewis capaldi",
    "radiohead", "beabadoobee", "phoebe bridgers", "kmfdm", "ye", "jackass",
    "runescape", "supergirl", "noah kahan", "my chemical romance", "mcr",
    "john deere", "wimbledon", "alan jackson"
]

def is_ip_infringing(keyword: str) -> bool:
    """Checks if keyword contains any blacklisted IP term using word boundaries."""
    kw_lower = keyword.lower()
    for term in IP_BLACKLIST:
        pattern = r"\b" + re.escape(term.lower()) + r"\b"
        if re.search(pattern, kw_lower):
            return True
    return False

def is_valid_merch_query(query: str) -> bool:
    """Validates if query is a long-tail apparel merch query and not noise."""
    q_lower = query.strip().lower()

    if q_lower in GENERIC_EXCLUSIONS:
        return False

    words = q_lower.split()
    if len(words) < 2:
        return False

    if any(noise in q_lower for noise in NOISE_KEYWORDS):
        return False

    if not any(apparel_term in q_lower for apparel_term in APPAREL_KEYWORDS):
        return False

    return True

def generate_design_idea(keyword: str) -> str:
    """Generates design idea and context for POD merch."""
    core_concept = keyword.lower()
    for term in APPAREL_STRIP_TERMS:
        core_concept = re.sub(r"\b" + re.escape(term) + r"\b", "", core_concept)
    core_concept = re.sub(r"\s+", " ", core_concept).strip()

    if not core_concept:
        core_concept = keyword

    return f"High demand trend! Core theme: '{core_concept}'. Create custom graphic or typography POD design targeting searchers looking for '{keyword}'."

def score_to_int(score) -> int:
    """Converts score to integer for sorting, treating 'Breakout' as 9999."""
    if isinstance(score, str):
        if "breakout" in score.lower():
            return 9999
        try:
            return int(score.replace("%", "").replace("+", "").strip())
        except ValueError:
            return 0
    elif isinstance(score, (int, float)):
        return int(score)
    return 0

def fetch_trending_queries():
    """Fetches rising queries from Google Trends with custom retry logic."""
    pytrend = TrendReq(hl='en-US', tz=360)
    all_results = {}

    for seed in SEED_KEYWORDS:
        print(f"Fetching trends for seed: '{seed}'...")
        success = False
        retries = 3

        for attempt in range(retries):
            try:
                pytrend.build_payload([seed], cat=0, timeframe='now 7-d')
                related_queries = pytrend.related_queries()
                if seed in related_queries and related_queries[seed]['rising'] is not None:
                    df = related_queries[seed]['rising']
                    for _, row in df.iterrows():
                        query = str(row['query']).strip()
                        value = row['value']

                        if is_valid_merch_query(query):
                            # Deduplicate and keep highest score
                            if query not in all_results or score_to_int(value) > score_to_int(all_results[query]['score']):
                                all_results[query] = {
                                    'keyword': query,
                                    'score': value,
                                    'score_num': score_to_int(value),
                                    'idea': generate_design_idea(query),
                                    'is_ip': is_ip_infringing(query)
                                }
                success = True
                break
            except Exception as e:
                print(f"Attempt {attempt + 1} failed for '{seed}': {e}")
                if "429" in str(e):
                    print("Rate limited (429). Waiting 10 seconds before retrying...")
                    time.sleep(10)
                else:
                    time.sleep(3)

        if not success:
            print(f"Failed to fetch data for seed '{seed}'.")

        time.sleep(5)  # Pause between seeds to prevent rate limits

    return list(all_results.values())

def update_trends_markdown(results):
    """Updates trends.md prepending the new day's results under main title."""
    today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    # Read existing content
    content = ""
    try:
        with open("trends.md", "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        content = ""

    # Check if header for today already exists
    today_header = f"## {today_str}"
    if today_header in content:
        print(f"Header '{today_header}' already present in trends.md. Skipping update for today.")
        return

    # Categorize results
    general_items = [r for r in results if not r['is_ip']]
    ip_items = [r for r in results if r['is_ip']]

    # Sort each list by score descending
    general_items.sort(key=lambda x: x['score_num'], reverse=True)
    ip_items.sort(key=lambda x: x['score_num'], reverse=True)

    # Build markdown entry for today
    new_entry = [f"## {today_str}", ""]

    new_entry.append("### General Merch Opportunities")
    if general_items:
        new_entry.append("| Keyword | Score | Why/Idea |")
        new_entry.append("| --- | --- | --- |")
        for item in general_items:
            score_str = f"+{item['score']}%" if isinstance(item['score'], int) else str(item['score'])
            new_entry.append(f"| {item['keyword']} | {score_str} | {item['idea']} |")
    else:
        new_entry.append("No new general merch opportunities identified today.")

    new_entry.append("")
    new_entry.append("### Potential IP Infringing Opportunities")
    if ip_items:
        new_entry.append("| Keyword | Score | Why/Idea |")
        new_entry.append("| --- | --- | --- |")
        for item in ip_items:
            score_str = f"+{item['score']}%" if isinstance(item['score'], int) else str(item['score'])
            new_entry.append(f"| {item['keyword']} | {score_str} | {item['idea']} |")
    else:
        new_entry.append("No potential IP infringing opportunities identified today.")

    new_entry.append("")
    new_entry_str = "\n".join(new_entry)

    main_title = "# Google Trends Merch Opportunities"

    if main_title in content:
        # Prepend below the main title
        parts = content.split(main_title, 1)
        updated_content = f"{main_title}\n\n{new_entry_str}\n{parts[1].lstrip()}"
    else:
        updated_content = f"{main_title}\n\n{new_entry_str}\n{content}"

    with open("trends.md", "w", encoding="utf-8") as f:
        f.write(updated_content)

    print("trends.md updated successfully!")

def main():
    print("Starting Google Trends merch crawl...")
    results = fetch_trending_queries()
    print(f"Total matching opportunities found: {len(results)}")
    update_trends_markdown(results)

if __name__ == "__main__":
    main()
