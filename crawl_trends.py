import pandas as pd
from pytrends.request import TrendReq
import time
from datetime import datetime
import re
import os

# Brand/IP blacklist for detection
IP_BLACKLIST = [
    "disney", "marvel", "nike", "adidas", "gucci", "prada", "zara", "star wars",
    "mickey", "harry potter", "pokemon", "nintendo", "lego", "netflix",
    "warner bros", "dc comics", "barbie", "sanrio", "hello kitty", "mickey mouse"
]

# Non-commercial intent filters
EXCLUDE_KEYWORDS = ["meaning", "definition", "crossword", "clue", "how to", "why"]

def fetch_trends(keywords, timeframe='now 7-d'):
    pytrends = TrendReq(hl='en-US', tz=360)
    all_rising_queries = []

    for kw in keywords:
        print(f"Fetching trends for: {kw}")
        try:
            pytrends.build_payload([kw], timeframe=timeframe)
            related_queries = pytrends.related_queries()

            if related_queries and kw in related_queries:
                data = related_queries[kw]
                if data is not None and 'rising' in data:
                    rising = data['rising']
                    if rising is not None:
                        # Extract the rising queries as a list of dicts for easier handling
                        all_rising_queries.extend(rising.to_dict('records'))

            # Sleep to avoid rate limiting
            time.sleep(2)
        except Exception as e:
            print(f"Error fetching {kw}: {e}")

    return all_rising_queries

def filter_and_categorize(queries):
    filtered_data = {
        "general": [],
        "potential_ip": []
    }

    seen_queries = set()

    for item in queries:
        query = str(item['query']).lower()
        value = item['value']

        if query in seen_queries:
            continue
        seen_queries.add(query)

        # Check if it's long tail and contains apparel terms
        is_apparel = any(term in query for term in ["shirt", "tshirt", "tanktop", "merch"])

        # Filter out generic terms like just "shirt"
        is_too_generic = query in ["shirt", "tshirt", "t-shirt", "tank top", "tanktop", "merch"]

        # Filter out non-commercial intent
        has_bad_intent = any(term in query for term in EXCLUDE_KEYWORDS)

        if is_apparel and not is_too_generic and not has_bad_intent:
            # Detect IP infringement
            is_ip_infringing = any(re.search(rf"\b{re.escape(brand)}\b", query) for brand in IP_BLACKLIST)

            result_item = {
                "keyword": query,
                "score": value,
                "idea": generate_idea(query)
            }

            if is_ip_infringing:
                filtered_data["potential_ip"].append(result_item)
            else:
                filtered_data["general"].append(result_item)

    return filtered_data

def generate_idea(query):
    # Simple logic for generating ideas/why it's an opportunity
    return f"Trending search for '{query}'. Consider a unique design combining this theme with popular niches or aesthetic styles currently trending on social media."

def format_markdown(data):
    today = datetime.now().strftime("%Y-%m-%d")
    md_content = f"## {today}\n\n"

    md_content += "### General Merch Opportunities\n"
    if data["general"]:
        md_content += "| keyword | score | why/idea |\n"
        md_content += "|---------|-------|----------|\n"
        for item in data["general"]:
            md_content += f"| {item['keyword']} | {item['score']} | {item['idea']} |\n"
    else:
        md_content += "No new general opportunities found.\n"

    md_content += "\n### Potential IP Infringing Opportunities\n"
    if data["potential_ip"]:
        md_content += "| keyword | score | why/idea |\n"
        md_content += "|---------|-------|----------|\n"
        for item in data["potential_ip"]:
            md_content += f"| {item['keyword']} | {item['score']} | {item['idea']} |\n"
    else:
        md_content += "No new potential IP infringing opportunities found.\n"

    md_content += "\n---\n\n"
    return md_content

def update_trends_md(new_content):
    filepath = "trends.md"
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            existing_content = f.read()

        # Check if the current date is already in the file to avoid duplicate entries
        today = datetime.now().strftime("%Y-%m-%d")
        if f"## {today}" in existing_content:
            print(f"Trends for {today} already exist in {filepath}.")
            return

        with open(filepath, "w") as f:
            f.write(new_content + existing_content)
    else:
        with open(filepath, "w") as f:
            f.write("# Google Trends Merch Opportunity Crawl\n\n" + new_content)

if __name__ == "__main__":
    seeds = ["tshirt", "shirt", "tank top", "merch"]
    queries = fetch_trends(seeds)
    if queries:
        results = filter_and_categorize(queries)
        md_table = format_markdown(results)
        update_trends_md(md_table)
        print("trends.md updated successfully.")
    else:
        print("No trends found.")
