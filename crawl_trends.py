import pandas as pd
from pytrends.request import TrendReq
import datetime
import os
import re
import time

# List of keywords to check for rising trends
KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]

# IP Blacklist - simplified version, can be expanded
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
    "spurs", "rcb", "snipes", "asos", "pattie gonia", "wingstop", "ariana grande",
    "selena gomez", "carhartt", "hazbin hotel", "digital circus", "tadc", "linkin park",
    "bad omens", "forrest frank", "malcolm todd", "böhse onkelz", "love island",
    "eternal sunshine", "madewell", "anthropologie", "glitch", "stevie nicks", "beyonce",
    "lilibet"
]

def is_ip_infringing(keyword):
    keyword_lower = keyword.lower()
    for brand in IP_BLACKLIST:
        if re.search(rf"\b{brand}\b", keyword_lower):
            return True
    return False

def generate_idea(keyword):
    # Simple idea generation logic
    keyword_lower = keyword.lower()
    clean_keyword = keyword
    for term in ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch", "tshirts", "tank tops", "tees"]:
        clean_keyword = re.sub(rf"\b{term}\b", "", clean_keyword, flags=re.IGNORECASE).strip()

    clean_keyword = re.sub(r'\s+', ' ', clean_keyword)

    if not clean_keyword:
        return "Generic apparel trend."

    return f"Focus on '{clean_keyword}' as a design concept. The internet is searching for specific variations of this theme. Create a unique graphic or typography-based design around this niche."

def get_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    all_rising = []

    for kw in KEYWORDS:
        print(f"Fetching trends for: {kw}")
        retries = 2
        while retries >= 0:
            try:
                pytrends.build_payload([kw], timeframe='now 7-d')
                related_queries = pytrends.related_queries()

                if kw in related_queries and related_queries[kw]['rising'] is not None:
                    rising = related_queries[kw]['rising']
                    # Filter for long tail (at least 2 words)
                    rising = rising[rising['query'].str.split().str.len() >= 2]
                    # Filter out generic 't shirt' search itself if it's there
                    rising = rising[~rising['query'].str.lower().isin(['t shirt', 't-shirt', 'tshirt', 'shirt', 'tank top', 'tee'])]
                    # Filter out some very common non-merch terms
                    exclude = ['meaning', 'definition', 'how to', 'why', 'iron', 'near me', 'template', 'mockup', 'tee times', 'tee time', 'tee off', 'graphic tee', 'essential tee', 'vintage tee', 'oversized tee', 'plain shirt', 'blank shirt', 'kaffee', 'rezepte', 'bh für', 'bra for', 'tutorial', 'bra', 't-shirt bra', 'là gì']
                    for ex in exclude:
                        rising = rising[~rising['query'].str.contains(ex, case=False)]

                    if not rising.empty:
                        all_rising.append(rising)
                time.sleep(5) # Avoid rate limits
                break
            except Exception as e:
                print(f"Error fetching {kw}: {e}")
                if "429" in str(e):
                    print("Rate limit hit. Waiting 30 seconds...")
                    time.sleep(30)
                    retries -= 1
                else:
                    break

    if not all_rising:
        return pd.DataFrame()

    df = pd.concat(all_rising).drop_duplicates(subset='query')
    # Sort by value (Score) - Breakout is usually high
    df['score'] = df['value'].apply(lambda x: 9999 if x == 'Breakout' else int(x))
    df = df.sort_values(by='score', ascending=False)

    return df

def update_trends_md(df):
    if df.empty:
        print("No new trends found.")
        return

    today = datetime.date.today().strftime("%Y-%m-%d")

    # Check if we already have entries for today to avoid duplicates if run multiple times
    if os.path.exists("trends.md"):
        with open("trends.md", "r", encoding="utf-8") as f:
            content = f.read()
            if f"## {today}" in content:
                print(f"Trends for {today} already exist in trends.md. Skipping.")
                return
    else:
        content = "# Google Trends Merch Opportunities\n\n"

    infringing = []
    general = []

    for _, row in df.iterrows():
        keyword = row['query']
        score = row['value']
        idea = generate_idea(keyword)

        entry = f"| {keyword} | {score} | {idea} |"

        if is_ip_infringing(keyword):
            infringing.append(entry)
        else:
            general.append(entry)

    new_section = f"## {today}\n\n"

    if general:
        new_section += "### General Merch Opportunities\n"
        new_section += "| Keyword | Score | Why/Idea |\n"
        new_section += "| :--- | :--- | :--- |\n"
        new_section += "\n".join(general) + "\n\n"

    if infringing:
        new_section += "### Potential IP Infringing Opportunities\n"
        new_section += "| Keyword | Score | Why/Idea |\n"
        new_section += "| :--- | :--- | :--- |\n"
        new_section += "\n".join(infringing) + "\n\n"

    # Prepend new section below the title
    title_end = content.find("\n\n")
    if title_end == -1:
        # Fallback if no title found
        updated_content = "# Google Trends Merch Opportunities\n\n" + new_section + content.replace("# Google Trends Merch Opportunities\n", "")
    else:
        updated_content = content[:title_end+2] + new_section + content[title_end+2:]

    with open("trends.md", "w", encoding="utf-8") as f:
        f.write(updated_content)

    print(f"Updated trends.md with {len(df)} trends.")

if __name__ == "__main__":
    trends_df = get_trends()
    update_trends_md(trends_df)
