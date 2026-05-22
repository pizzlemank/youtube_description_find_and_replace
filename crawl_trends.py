import pandas as pd
from pytrends.request import TrendReq
import time
from datetime import datetime

BRAND_BLACKLIST = [
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
    "bad omens", "good mythical morning", "riley green", "ella langley",
    "candace owens", "g59", "grey59", "greyfivenine", "of the trees", "harry styles",
    "gracie abrams", "daniel caesar", "jul", "rcb", "pga championship", "edc",
    "suzan en freek", "kaulitz hills", "qsmp", "ovo", "arsenal", "real madrid",
    "liverpool", "man city", "chelsea", "bayern", "barcelona", "amiri", "trapstar",
    "corteiz", "sp5der", "minus two", "syna world", "roblox", "lego", "minecraft",
    "fortnite", "bluey", "sanrio", "hello kitty", "kuromi", "cinnamoroll",
    "my melody", "pompompurin", "squishmallow", "sonny angel"
]

def is_ip_infringing(query):
    query_lower = query.lower()
    for brand in BRAND_BLACKLIST:
        if brand in query_lower:
            return True
    return False

def fetch_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    keywords = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]

    all_related_queries = {}

    for kw in keywords:
        print(f"Fetching trends for: {kw}")
        pytrends.build_payload([kw], timeframe='now 7-d')
        related_queries = pytrends.related_queries()

        if kw in related_queries:
            rising = related_queries[kw]['rising']
            if rising is not None and not rising.empty:
                for index, row in rising.iterrows():
                    query = row['query']
                    score = row['value']

                    # Long tail: 2+ words
                    if len(query.split()) < 2:
                        continue

                    # Must contain an apparel term
                    apparel_terms = ["shirt", "tshirt", "t-shirt", "tank top", "tanktop", "tee", "merch"]
                    if not any(term in query.lower() for term in apparel_terms):
                        continue

                    # Filter out golf tee times etc and non-merch related terms
                    exclude_terms = [
                        "tee times", "tee time", "tee off", "graphic tee",
                        "essential tee", "vintage tee", "oversized tee",
                        "plain shirt", "blank shirt", "kaffee", "rezepte",
                        "bh für", "bra for", "tutorial", "meaning", "definition"
                    ]
                    if any(term in query.lower() for term in exclude_terms):
                        continue

                    if query not in all_related_queries:
                        all_related_queries[query] = {
                            'score': score,
                            'is_ip': is_ip_infringing(query)
                        }

        # Be nice to Google API
        time.sleep(5)

    return all_related_queries

def generate_why_idea(query):
    query_lower = query.lower()
    # Simple idea generation logic
    # Use long to short replacement to avoid partial replacements
    clean_query = query_lower
    for term in sorted(["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "merch", "tee"], key=len, reverse=True):
        clean_query = clean_query.replace(term, "")

    clean_query = " ".join(clean_query.split()) # clean up spaces

    if "funny" in query_lower:
        return f"Funny graphic design focused on '{clean_query}'. Trending humor in apparel."
    elif "vintage" in query_lower:
        return f"Retro/Vintage aesthetic for '{clean_query}'. High demand for nostalgic looks."
    elif "cute" in query_lower:
        return f"Kawaii or cute illustration style for '{clean_query}'."
    else:
        return f"Growing interest in '{clean_query}'. Target this niche with a unique design style."

def format_as_markdown(trends):
    date_str = datetime.now().strftime("%Y-%m-%d")
    md_content = f"## {date_str}\n\n"

    general_merch = []
    ip_infringing = []

    # Sort by score descending
    sorted_trends = sorted(trends.items(), key=lambda x: x[1]['score'] if isinstance(x[1]['score'], int) else 9999, reverse=True)

    for kw, data in sorted_trends:
        row = f"| {kw} | {data['score']} | {generate_why_idea(kw)} |"
        if data['is_ip']:
            ip_infringing.append(row)
        else:
            general_merch.append(row)

    header = "| Keyword | Score | Why/Idea |\n| :--- | :--- | :--- |\n"

    md_content += "### General Merch Opportunities\n"
    if general_merch:
        md_content += header + "\n".join(general_merch) + "\n\n"
    else:
        md_content += "No new general opportunities found.\n\n"

    md_content += "### Potential IP Infringing Opportunities\n"
    if ip_infringing:
        md_content += header + "\n".join(ip_infringing) + "\n\n"
    else:
        md_content += "No new IP infringing opportunities found.\n\n"

    return md_content

def update_trends_file(new_content):
    filename = "trends.md"
    try:
        with open(filename, "r") as f:
            existing_content = f.read()
    except FileNotFoundError:
        existing_content = ""

    date_str = datetime.now().strftime("%Y-%m-%d")
    if f"## {date_str}" in existing_content:
        print(f"Trends for {date_str} already exist in {filename}. Skipping update.")
        return

    # Prepend new content
    with open(filename, "w") as f:
        f.write(new_content + existing_content)

if __name__ == "__main__":
    trends = fetch_trends()
    if trends:
        new_content = format_as_markdown(trends)
        update_trends_file(new_content)
        print("trends.md updated successfully.")
    else:
        print("No new trends found today.")
