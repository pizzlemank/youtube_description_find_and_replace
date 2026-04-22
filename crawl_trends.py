import pandas as pd
from pytrends.request import TrendReq
import datetime
import os
import time

def get_trends():
    pytrends = TrendReq(hl='en-US', tz=360)

    keywords = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]
    all_rising_queries = []

    for kw in keywords:
        retries = 3
        while retries > 0:
            try:
                pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='', gprop='')
                related_queries = pytrends.related_queries()

                if kw in related_queries and related_queries[kw]['rising'] is not None:
                    rising = related_queries[kw]['rising']
                    all_rising_queries.append(rising)
                time.sleep(2) # Avoid rate limiting
                break
            except Exception as e:
                if "429" in str(e):
                    print(f"Rate limited for {kw}, retrying in 10s...")
                    time.sleep(10)
                    retries -= 1
                else:
                    print(f"Error fetching for {kw}: {e}")
                    break

    if not all_rising_queries:
        return pd.DataFrame()

    df = pd.concat(all_rising_queries).drop_duplicates(subset='query')
    return df

def is_ip_infringing(query):
    blacklist = [
        "disney", "marvel", "star wars", "nike", "adidas", "bieber", "taylor swift",
        "michael jackson", "one piece", "popeyes", "coachella", "netflix", "mickey",
        "trump", "biden", "nba", "nfl", "mlb", "nhl", "pokemon", "nintendo", "sony",
        "playstation", "xbox", "nasa", "hellstar", "karol g", "bruno mars",
        "sabrina carpenter", "billie eilish", "olivia rodrigo", "noah kahan",
        "frank ocean", "mashtag brady", "aldi", "morbid podcast", "ysl",
        "koningsdag", "oranje", "higgins", "kelce", "mahomes", "stroud",
        "wwe", "the weeknd", "hellstar", "chrome hearts", "stussy", "vultures", "kanye",
        "billie", "mickey mouse", "starwars", "nintendo", "playstation", "xbox"
    ]
    query_lower = query.lower()
    for brand in blacklist:
        if brand in query_lower:
            return True
    return False

def generate_idea(query):
    query_lower = query.lower()
    # Remove apparel terms to find the core topic
    # Sort by length descending to avoid partial matches (e.g., 'tshirt' before 'shirt')
    apparel_terms = sorted(['tshirt', 't-shirt', 'shirt', 'tank top', 'tanktop', 'tee', 'merch'], key=len, reverse=True)

    topic = query_lower
    found_term = "merch"
    for term in apparel_terms:
        if term in topic:
            found_term = term
            topic = topic.replace(term, "")
            break

    topic = topic.strip().title()
    if not topic:
        topic = "General"

    return f"Rising interest in {topic} {found_term}. Design idea: Create a unique, stylized graphic representing '{topic}' that appeals to the current search trend. Check popular social media for visual cues."

def main():
    df = get_trends()

    if df.empty:
        print("No new trends found.")
        return

    # Filter for long tail (at least 2 words)
    df = df[df['query'].str.split().str.len() >= 2]

    # Ensure it contains apparel related words as per requirements
    apparel_keywords = ['shirt', 'tshirt', 'tank top', 'tanktop', 'tee', 'merch']
    df = df[df['query'].str.contains('|'.join(apparel_keywords), case=False)]

    # Filter out generic terms or non-merch related
    exclude = ["meaning", "definition", "how to", "why", "iron", "near me", "template", "mockup", "tee times", "tee time", "tee off", "graphic tee", "essential tee", "vintage tee", "oversized tee", "plain shirt", "blank shirt"]
    df = df[~df['query'].str.contains('|'.join(exclude), case=False)]

    # Sort by score (value) descending. 'Breakout' strings are usually large numbers in pytrends value.
    # We ensure value is numeric for sorting.
    df['value'] = pd.to_numeric(df['value'], errors='coerce').fillna(9999) # Treat breakout as high
    df = df.sort_values(by='value', ascending=False)

    today = datetime.date.today().strftime("%Y-%m-%d")

    # Check if we already updated today to avoid duplicates
    if os.path.exists("trends.md"):
        with open("trends.md", "r") as f:
            existing_content = f.read()
        if f"## {today}" in existing_content:
            print(f"Already updated for {today}. Skipping.")
            return
    else:
        existing_content = ""

    general_merch = []
    ip_infringing = []

    for _, row in df.iterrows():
        query = row['query']
        score = row['value']
        if score == 9999:
            score_str = "Breakout"
        else:
            score_str = str(int(score))

        idea = generate_idea(query)

        entry = f"| {query} | {score_str} | {idea} |"

        if is_ip_infringing(query):
            ip_infringing.append(entry)
        else:
            general_merch.append(entry)

    # Prepare the update
    new_content = f"## {today}\n\n"

    new_content += "### General Merch Opportunities\n"
    new_content += "| Keyword | Score | Why/Idea |\n"
    new_content += "| :--- | :--- | :--- |\n"
    if general_merch:
        new_content += "\n".join(general_merch) + "\n"
    else:
        new_content += "| None found | - | - |\n"

    new_content += "\n### Potential IP Infringing Opportunities\n"
    new_content += "| Keyword | Score | Why/Idea |\n"
    new_content += "| :--- | :--- | :--- |\n"
    if ip_infringing:
        new_content += "\n".join(ip_infringing) + "\n"
    else:
        new_content += "| None found | - | - |\n"

    new_content += "\n---\n\n"

    # Prepend to trends.md
    with open("trends.md", "w") as f:
        header = "# Google Trends Merch Opportunities\n\n"
        clean_existing = existing_content.replace(header, "")
        f.write(header + new_content + clean_existing)

if __name__ == "__main__":
    main()
