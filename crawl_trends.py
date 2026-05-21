import pandas as pd
from pytrends.request import TrendReq
import time
from datetime import datetime
import os
import random

def get_trends():
    pytrends = TrendReq(hl='en-US', tz=360)

    seed_keywords = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]
    all_rising_queries = []

    for kw in seed_keywords:
        print(f"Fetching trends for: {kw}")
        retries = 3
        while retries > 0:
            try:
                pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='', gprop='')
                related_queries = pytrends.related_queries()

                if kw in related_queries and related_queries[kw]['rising'] is not None:
                    rising = related_queries[kw]['rising']
                    all_rising_queries.append(rising)

                # Sleep to avoid rate limiting
                time.sleep(5)
                break
            except Exception as e:
                print(f"Error fetching {kw}: {e}")
                if "429" in str(e):
                    print("Rate limit hit, sleeping for 60s...")
                    time.sleep(60)
                    retries -= 1
                else:
                    time.sleep(5)
                    break

    if not all_rising_queries:
        return pd.DataFrame()

    df = pd.concat(all_rising_queries).drop_duplicates(subset='query')

    # Ensure value (score) is numeric for sorting, handling 'Breakout'
    def clean_score(val):
        if val == 'Breakout' or (isinstance(val, str) and 'breakout' in val.lower()):
            return 9999
        try:
            return int(val)
        except:
            return 0

    df['sort_score'] = df['value'].apply(clean_score)
    df = df.sort_values(by='sort_score', ascending=False).drop(columns=['sort_score'])
    return df

def is_ip_infringing(query):
    blacklist = [
        "disney", "marvel", "star wars", "nike", "adidas", "taylor swift", "bts",
        "michael jackson", "nba", "wnba", "nfl", "mlb", "nhl", "nintendo", "pokemon",
        "harry potter", "nasa", "hellstar", "ysl", "gucci", "prada", "louis vuitton",
        "koningsdag", "oranje", "higgins", "wwe", "kanye", "drake", "notre dame",
        "ariana grande", "george strait", "olivia dean", "conan gray", "man utd",
        "lidl", "m&s", "mnet", "amc", "murder drones", "luke combs", "ohio state",
        "ufc", "f1", "nascar", "sanrio", "hello kitty", "stussy", "mclaren",
        "deftones", "cleetus mcfarland", "the neighbourhood", "bring me the horizon",
        "khan asadi", "lyrebird", "anthropologie", "carson hocevar", "rihanna",
        "morgan wallen", "valorant", "kentucky derby", "victoria beckham",
        "kimi antonelli", "no doubt", "bad omens", "good mythical morning",
        "riley green", "ella Langley", "candace owens", "g59", "grey59", "greyfivenine",
        "of the trees", "harry styles", "gracie abrams", "daniel caesar", "jul",
        "rcb", "pga championship", "edc", "suzan en freek", "kaulitz hills", "qsmp", "ovo",
        "arsenal", "real madrid", "liverpool", "man city", "chelsea", "bayern", "barcelona",
        "amiri", "stussy", "trapstar", "corteiz", "sp5der", "minus two", "syna world"
    ]
    query_lower = query.lower()
    for brand in blacklist:
        if brand in query_lower:
            return True
    return False

def generate_idea(query):
    # Clean up the query for the idea generation
    query_clean = query.lower()
    # Sort terms by length descending to replace longer phrases first
    terms_to_remove = sorted(["t-shirt", "tshirt", "t shirt", "shirt", "merch", "tank top", "tanktop", "tee"], key=len, reverse=True)
    for term in terms_to_remove:
        query_clean = query_clean.replace(term, "")
    query_clean = " ".join(query_clean.split()).strip() # remove extra spaces

    if not query_clean:
        query_clean = query

    ideas = [
        f"Create a unique graphic featuring '{query_clean}'. Focus on bold typography and illustrative elements.",
        f"Trending topic: '{query_clean}'. Design a minimalist aesthetic shirt that appeals to fans of this niche.",
        f"Internet is searching for '{query_clean}'. Consider a vintage or distressed look for this design.",
        f"Opportunity for '{query_clean}'. Combine this with a popular art style like synthwave or line art.",
        f"Niche found: '{query_clean}'. Great for a 'I'd rather be...' or 'Official member of...' style design."
    ]
    return random.choice(ideas)

def filter_queries(df):
    if df.empty:
        return df

    # Long tail (2+ words)
    df = df[df['query'].str.split().str.len() >= 2]

    # Must contain apparel terms but not BE just the term
    apparel_terms = ["shirt", "tshirt", "t-shirt", "tank top", "tanktop", "tee", "merch"]
    def has_apparel(q):
        q = q.lower()
        if q in apparel_terms or q == "t shirt":
            return False
        return any(term in q for term in apparel_terms)

    df = df[df['query'].apply(has_apparel)]

    # Exclude non-commercial/irrelevant
    exclude = ["meaning", "definition", "how to", "why", "iron", "near me", "template", "mockup", "tee times", "tee time", "tee off", "graphic tee", "essential tee", "vintage tee", "oversized tee", "plain shirt", "blank shirt", "kaffee", "rezepte", "bh für", "bra for", "tutorial", "là gì"]
    def is_relevant(q):
        q = q.lower()
        return not any(ex in q for ex in exclude)

    df = df[df['query'].apply(is_relevant)]

    return df

def update_trends_md(df):
    if df.empty:
        print("No new trends found today.")
        return

    today = datetime.now().strftime("%Y-%m-%d")

    general_merch = []
    ip_infringing = []

    for _, row in df.iterrows():
        query = row['query']
        score = row['value']
        idea = generate_idea(query)

        entry = f"| {query} | {score} | {idea} |"

        if is_ip_infringing(query):
            ip_infringing.append(entry)
        else:
            general_merch.append(entry)

    content = f"## {today}\n\n"

    if general_merch:
        content += "### General Merch Opportunities\n"
        content += "| Keyword | Score | Why/Idea |\n"
        content += "| :--- | :--- | :--- |\n"
        content += "\n".join(general_merch) + "\n\n"

    if ip_infringing:
        content += "### Potential IP Infringing Opportunities\n"
        content += "| Keyword | Score | Why/Idea |\n"
        content += "| :--- | :--- | :--- |\n"
        content += "\n".join(ip_infringing) + "\n\n"

    filename = "trends.md"
    existing_content = ""
    if os.path.exists(filename):
        with open(filename, "r") as f:
            existing_content = f.read()

    # Avoid duplicate header if run multiple times same day
    if f"## {today}" in existing_content:
        print(f"Trends for {today} already exist in {filename}. Skipping update to avoid duplication.")
        return

    with open(filename, "w") as f:
        f.write(content + existing_content)

    print(f"Updated {filename} with {len(df)} new trends.")

if __name__ == "__main__":
    trends_df = get_trends()
    filtered_df = filter_queries(trends_df)
    update_trends_md(filtered_df)
