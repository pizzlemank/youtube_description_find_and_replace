import pandas as pd
from pytrends.request import TrendReq
from pytrends.exceptions import TooManyRequestsError
import datetime
import os
import re
import time

def crawl_google_trends():
    pytrends = TrendReq(hl='en-US', tz=360)

    # Target keywords to find merch opportunities
    # Using broader seed keywords to catch various niches
    keywords = ["tshirt", "shirt", "tank top", "merch"]
    all_rising_queries = []

    for kw in keywords:
        try:
            # Using a 7-day timeframe to catch recent rising trends
            pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='', gprop='')
            related_queries = pytrends.related_queries()

            if kw in related_queries and related_queries[kw]['rising'] is not None:
                rising = related_queries[kw]['rising']
                rising['seed'] = kw
                all_rising_queries.append(rising)

            # To avoid rate limiting from Google
            time.sleep(2)
        except TooManyRequestsError:
            print("Rate limited. Sleeping for 10 seconds...")
            time.sleep(10)
        except Exception as e:
            print(f"Error fetching for {kw}: {e}")

    if not all_rising_queries:
        return pd.DataFrame()

    df = pd.concat(all_rising_queries)
    return df

def is_potential_ip_infringement(keyword):
    # Blacklist of known brands, franchises, and celebrities
    brands = [
        # Entertainment & Media
        "disney", "marvel", "star wars", "nintendo", "pokemon", "netflix", "hulu", "hbo",
        "warner bros", "universal", "mickey", "minnie", "harry potter", "naruto",
        "one piece", "dragon ball", "anime", "manga", "studio ghibli", "pixar",
        "superman", "batman", "spiderman", "avengers", "justice league", "game of thrones",
        "stranger things", "bluey", "peppa pig", "barbie", "lego",

        # Brands
        "nike", "adidas", "gucci", "prada", "louis vuitton", "supreme", "stussy",
        "apple", "google", "microsoft", "amazon", "tesla", "nasa", "national geographic",

        # Celebrities & Artists
        "taylor swift", "beyonce", "drake", "kanye", "ye", "travis scott", "bruno mars",
        "morgan wallen", "ethel cain", "justin bieber", "tame impala", "bilmuri",
        "meat canyon", "meatcanyon", "cdawgva", "alex warren", "annie elise",
        "michael jackson", "elvis", "the beatles", "rolling stones", "nirvana",

        # Sports
        "nfl", "nba", "mlb", "nhl", "fifa", "olympics", "masters", "coachella",
        "f1", "formula 1", "wwe", "ufc",

        # Misc
        "hello kitty", "sanrio", "kuromi", "my melody", "pokemon", "squishmallows"
    ]

    keyword_lower = keyword.lower()
    for brand in brands:
        # Use word boundaries to avoid false positives
        if re.search(rf"\b{brand}\b", keyword_lower):
            return True
    return False

def is_junk_keyword(keyword):
    # Terms that indicate non-commercial or non-merch intent
    junk_terms = [
        "how to", "meaning", "definition", "why", "iron", "wash", "dry", "near me",
        "store", "shop", "factory", "company", "template", "mockup", "size chart",
        "cleaning", "repair", "wholesale", "manufacturer"
    ]
    keyword_lower = keyword.lower()
    for term in junk_terms:
        if term in keyword_lower:
            return True
    return False

def generate_opportunity_reason(keyword):
    keyword_lower = keyword.lower()
    if "merch" in keyword_lower:
        return "Direct interest in creator/event merchandise. Identify the core audience and design around catchphrases or iconic imagery from the source."

    apparel_terms = ["shirt", "tshirt", "tank top", "tanktop", "tee"]
    for term in apparel_terms:
        if term in keyword_lower:
            topic = keyword_lower.replace(term, "").strip()
            return f"Specific search for {term} related to '{topic}'. This indicates a niche demand. Design should focus on the aesthetic of '{topic}'."

    return f"Rising interest in '{keyword}'. Potentially a new viral trend. Research current social media (TikTok/Twitter) for the specific context of this rise."

def update_trends_md(df):
    if df.empty:
        print("No new trends found.")
        return

    today = datetime.date.today().strftime("%Y-%m-%d")

    # Filter for long tail and ensure it contains apparel-related terms to be more specific
    # or just keep it as long tail (> 1 word) as requested
    filtered_df = df[df['query'].str.split().str.len() > 1]

    # Specific filtering: check if it contains common apparel terms or is high interest
    # The user asked for "long tail of - shirts or -tshirt, tanktop, etc"
    apparel_regex = r"(shirt|tshirt|tanktop|tank top|tee|merch)"

    general_opportunities = []
    ip_opportunities = []

    seen_queries = set()

    for _, row in filtered_df.iterrows():
        query = row['query']
        if query in seen_queries:
            continue
        seen_queries.add(query)

        if is_junk_keyword(query):
            continue

        # Ensure it fits the user's specific apparel criteria if possible,
        # but don't be too strict if it's a very high rising 'merch' query
        if not re.search(apparel_regex, query.lower()) and row['value'] != 'Breakout' and int(row['value']) < 200:
             continue

        value = row['value']
        is_ip = is_potential_ip_infringement(query)
        reason = generate_opportunity_reason(query)

        entry = f"| {query} | {value} | {reason} |"

        if is_ip:
            ip_opportunities.append(entry)
        else:
            general_opportunities.append(entry)

    if not general_opportunities and not ip_opportunities:
        print("No high-quality opportunities found today.")
        return

    # Prepare the new content
    new_content = f"## {today}\n\n"

    if general_opportunities:
        new_content += "### General Merch Opportunities\n"
        new_content += "| Keyword | Score | Why/Idea |\n"
        new_content += "| :--- | :--- | :--- |\n"
        new_content += "\n".join(general_opportunities) + "\n\n"

    if ip_opportunities:
        new_content += "### Potential IP Infringing Opportunities\n"
        new_content += "| Keyword | Score | Why/Idea |\n"
        new_content += "| :--- | :--- | :--- |\n"
        new_content += "\n".join(ip_opportunities) + "\n\n"

    # Read existing content
    existing_content = ""
    if os.path.exists("trends.md"):
        with open("trends.md", "r") as f:
            existing_content = f.read()

    # Avoid adding the same day's data twice
    if f"## {today}" in existing_content:
        print(f"Trends for {today} already exist in trends.md. Skipping update.")
        return

    header = "# Google Trends Merch Opportunities\n\n"
    if existing_content.startswith(header):
        content_to_keep = existing_content[len(header):]
        final_content = header + new_content + content_to_keep
    else:
        final_content = header + new_content + existing_content

    with open("trends.md", "w") as f:
        f.write(final_content)
    print(f"Successfully updated trends.md with data for {today}.")

if __name__ == "__main__":
    trends_df = crawl_google_trends()
    update_trends_md(trends_df)
