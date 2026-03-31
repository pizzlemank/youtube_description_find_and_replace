import pandas as pd
from pytrends.request import TrendReq
import datetime
import os
import re

# List of common IP-infringing keywords (brands, franchises, celebrities, sports teams, etc.)
IP_KEYWORDS = [
    "disney", "marvel", "star wars", "nintendo", "pokemon", "anime", "nike", "adidas",
    "gucci", "prada", "harry potter", "netflix", "hulu", "amazon", "apple", "google",
    "microsoft", "sony", "playstation", "xbox", "warner bros", "dc comics", "mickey",
    "minnie", "donald duck", "spiderman", "batman", "superman", "iron man", "captain america",
    "thor", "hulk", "black widow", "black panther", "doctor strange", "guardians of the galaxy",
    "avengers", "justice league", "bluey", "peppa pig", "paw patrol", "barbie", "lego",
    "fortnite", "roblox", "minecraft", "call of duty", "grand theft auto", "among us",
    "hello kitty", "sanrio", "snoopy", "peanuts", "garfield", "looney tunes", "bugs bunny",
    "daffy duck", "tweety", "scooby doo", "tom and jerry", "flintstones", "simpsons",
    "south park", "family guy", "rick and morty", "game of thrones", "stranger things",
    "squid game", "breaking bad", "friends", "the office", "greys anatomy", "mandalorian",
    "baby yoda", "grogu", "squishmallows", "jellycat", "bts", "blackpink", "twice", "stray kids",
    "blue jays", "dodgers", "yankees", "lakers", "warriors", "nfl", "nba", "mlb", "nhl",
    "under armour", "puma", "reebok", "hannah montana", "taylor swift", "beyonce",
    "kanye", "yeat", "travis scott", "drake", "melanie martinez", "5sos", "lany",
    "masters", "olympics", "world cup", "fifa", "premier league", "champions league"
]

GENERIC_TERMS = [
    "t-shirt", "tshirt", "shirt", "tank top", "tank", "merch", "clothing", "apparel", "men's", "women's", "kids"
]

def check_ip_infringement(keyword):
    keyword_lower = keyword.lower()
    for ip in IP_KEYWORDS:
        if re.search(rf"\b{re.escape(ip)}\b", keyword_lower):
            return True
    return False

def get_why_idea(keyword):
    keyword_lower = keyword.lower()
    if "wolf" in keyword_lower:
        return "Wolves are a popular niche for 'cool' or 'lone wolf' aesthetics. Design: A majestic wolf silhouette with a forest background."
    elif "autism" in keyword_lower:
        return "High demand for neurodiversity awareness. Design: Puzzle pieces or infinity symbol with inclusive messaging."
    elif "funny" in keyword_lower or "joke" in keyword_lower:
        return "Humor always sells. Design: Minimalist text with a witty pun or relatable observation."
    elif "government" in keyword_lower:
        return "Political or satirical commentary. Design: Sarcastic quote about bureaucracy or patriotic imagery."
    elif "vintage" in keyword_lower or "retro" in keyword_lower:
        return "Timeless appeal. Design: Distressed textures, sunset gradients, and 80s/90s typography."
    elif "cute" in keyword_lower or "kawaii" in keyword_lower:
        return "Broad appeal for children and adults. Design: Small, adorable characters with big eyes."
    elif "easter" in keyword_lower:
        return "Seasonal demand for Easter. Design: Bunny ears, colorful eggs, or 'Egg-cellent' puns."
    elif "tour" in keyword_lower or "concert" in keyword_lower:
        return "Music fans looking for memorabilia. Design: Graphic inspired by the artist's style (avoiding IP)."
    else:
        return f"Trending keyword: {keyword}. High search volume indicates current interest. Design should capture the core theme with a unique twist."

def crawl_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    kw_list = ["tshirt", "shirt", "tank top", "merch"]

    all_data = []

    for kw in kw_list:
        try:
            pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='', gprop='')
            related_queries = pytrends.related_queries()

            if kw in related_queries and related_queries[kw]['rising'] is not None:
                rising = related_queries[kw]['rising']
                for index, row in rising.iterrows():
                    query = row['query']
                    score = row['value']

                    # Filtering: must be at least 2 words or contain specific merch terms,
                    # but avoid purely generic terms like "t-shirt"
                    query_clean = query.lower().strip()
                    if query_clean in GENERIC_TERMS:
                        continue

                    if len(query.split()) >= 2 or any(term in query_clean for term in ["shirt", "tshirt", "tank", "merch"]):
                        all_data.append({
                            'keyword': query,
                            'score': score,
                            'ip_infringing': check_ip_infringement(query)
                        })
        except Exception as e:
            print(f"Error fetching data for {kw}: {e}")

    if not all_data:
        print("No new trends found.")
        return

    # De-duplicate
    df = pd.DataFrame(all_data).drop_duplicates(subset=['keyword'])

    # Sort by score descending
    df = df.sort_values(by='score', ascending=False)

    now = datetime.datetime.now().strftime("%Y-%m-%d")

    general_merch = df[df['ip_infringing'] == False]
    ip_merch = df[df['ip_infringing'] == True]

    new_entry = f"## {now}\n\n### General Merch Opportunities\n\n"
    if not general_merch.empty:
        new_entry += "| Keyword | Score | Why / Idea |\n"
        new_entry += "| :--- | :--- | :--- |\n"
        for _, row in general_merch.iterrows():
            new_entry += f"| {row['keyword']} | {row['score']} | {get_why_idea(row['keyword'])} |\n"
    else:
        new_entry += "No new general merch opportunities found today.\n"

    new_entry += "\n### Potential IP Infringing Opportunities\n\n"
    if not ip_merch.empty:
        new_entry += "| Keyword | Score | Why / Idea |\n"
        new_entry += "| :--- | :--- | :--- |\n"
        for _, row in ip_merch.iterrows():
            new_entry += f"| {row['keyword']} | {row['score']} | This likely infringes on existing IP. Use with extreme caution or avoid. Idea: Create an 'inspired-by' design that does not use protected names or logos. |\n"
    else:
        new_entry += "No new potential IP infringing opportunities found today.\n"

    new_entry += "\n---\n\n"

    header = "# T-Shirt Merch Trends\n\nDaily crawl of Google Trends to identify Print-on-Demand (POD) opportunities.\n\n---\n\n"

    existing_content = ""
    if os.path.exists("trends.md"):
        with open("trends.md", "r") as f:
            existing_content = f.read()

    if f"## {now}" in existing_content:
        print(f"Trends for {now} already exist in trends.md. Skipping.")
        return

    # If file is empty or just has header, start fresh
    if not existing_content.strip() or "# T-Shirt Merch Trends" not in existing_content:
        content = header + new_entry
    else:
        # Insert after the header
        parts = existing_content.split("---", 1)
        if len(parts) > 1:
            # We want to keep the header and the first --- separator
            content = parts[0] + "---" + "\n\n" + new_entry + parts[1].strip() + "\n"
        else:
            content = header + new_entry + existing_content

    with open("trends.md", "w") as f:
        f.write(content)

    print(f"Successfully updated trends.md with {len(df)} new trends.")

if __name__ == "__main__":
    crawl_trends()
