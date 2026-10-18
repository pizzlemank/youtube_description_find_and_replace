#!/usr/bin/env python3
"""
Google Trends Merch Crawler for POD Opportunities.
Crawls Google Trends for related queries to apparel seed keywords,
categorizes results into general vs. potential IP infringing,
and updates trends.md in Markdown table format.
"""

import os
import re
import time
from datetime import datetime
import pandas as pd
from pytrends.request import TrendReq

SEED_KEYWORDS = [
    "tshirt",
    "t-shirt",
    "shirt",
    "tank top",
    "tanktop",
    "tee",
    "merch",
]

# Words/phrases to filter out generic/non-commercial queries
EXCLUDE_TERMS = [
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

# Seed terms to exclude exact/generic matches
GENERIC_SEED_TERMS = [
    "t shirt",
    "t-shirt",
    "tshirts",
    "t-shirts",
    "shirt",
    "shirts",
    "tee",
    "tees",
    "tank top",
    "tank tops",
    "merch",
]

# Blacklist of brands/IPs/celebrities/teams
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
    kw = keyword.lower()
    for term in IP_BLACKLIST:
        pattern = r"\b" + re.escape(term) + r"\b"
        if re.search(pattern, kw):
            return True
    return False


def generate_idea(keyword: str) -> str:
    kw = keyword.lower()
    # Clean apparel keywords to isolate the core niche topic
    topic = kw
    for term in ["tshirts", "t-shirts", "tank tops", "tshirt", "t-shirt", "tank top", "tanktop", "shirt", "tee", "merch"]:
        topic = re.sub(r"\b" + re.escape(term) + r"\b", "", topic, flags=re.IGNORECASE)
    topic = re.sub(r"\s+", " ", topic).strip()

    if not topic:
        topic = keyword

    if is_ip_infringing(keyword):
        return f"Trending search around '{topic}'. High demand but contains registered IP/brand elements. Verify licensing before creating designs."

    return f"Surging demand around '{topic}'. High conversion potential for POD. Create bold graphic typography or illustrative art targeting '{topic}' enthusiasts."


def parse_score(value) -> int:
    if str(value).lower() == "breakout":
        return 9999
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def fetch_trends_data():
    pytrend = TrendReq(hl="en-US", tz=360)
    results = []
    seen_keywords = set()

    for seed in SEED_KEYWORDS:
        print(f"Fetching Google Trends for seed: '{seed}'...")
        retries = 3
        while retries > 0:
            try:
                pytrend.build_payload([seed], cat=0, timeframe="now 7-d", geo="", gprop="")
                related = pytrend.related_queries()
                seed_data = related.get(seed, {})
                for query_type in ["rising", "top"]:
                    df = seed_data.get(query_type)
                    if df is not None and not df.empty:
                        for _, row in df.iterrows():
                            kw = str(row["query"]).strip().lower()
                            val = row["value"]

                            # Exclude short/single-word or duplicate keywords
                            words = kw.split()
                            if len(words) < 2 or kw in seen_keywords:
                                continue

                            # Exclude exact generic seed terms
                            if kw in GENERIC_SEED_TERMS:
                                continue

                            # Exclude non-commercial terms
                            if any(ex in kw for ex in EXCLUDE_TERMS):
                                continue

                            seen_keywords.add(kw)
                            score = parse_score(val)
                            score_display = "+Breakout" if score == 9999 else f"+{score}%" if query_type == "rising" else str(score)

                            results.append({
                                "keyword": kw,
                                "score": score,
                                "score_display": score_display,
                                "is_ip": is_ip_infringing(kw),
                                "idea": generate_idea(kw)
                            })
                break
            except Exception as e:
                print(f"Error fetching data for '{seed}': {e}. Retrying in 10s... ({retries} left)")
                time.sleep(10)
                retries -= 1

        time.sleep(5)  # Delay between requests to avoid rate limits

    # Sort results by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def format_markdown_table(items):
    if not items:
        return "_No items identified for this category today._\n"

    table = "| Keyword | Score | Why / Design Idea / Market Context |\n"
    table += "|---|---|---|\n"
    for item in items:
        kw = item["keyword"]
        score = item["score_display"]
        idea = item["idea"]
        table += f"| {kw} | {score} | {idea} |\n"
    return table


def update_trends_markdown(results):
    today = datetime.now().strftime("%Y-%m-%d")

    general_items = [r for r in results if not r["is_ip"]]
    ip_items = [r for r in results if r["is_ip"]]

    today_section = f"## {today}\n\n"
    today_section += "### General Merch Opportunities\n\n"
    today_section += format_markdown_table(general_items) + "\n"
    today_section += "### Potential IP Infringing Opportunities\n\n"
    today_section += format_markdown_table(ip_items) + "\n"

    filename = "trends.md"
    header = "# Google Trends Merch Opportunities\n\nAutomated daily scan of trending search queries on Google Trends targeting Print-On-Demand (POD) apparel keywords.\n\n"

    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()

        if f"## {today}" in content:
            print(f"Section for {today} already exists in {filename}. Prepending updated data.")

        # Prepend today's section under main header if header exists
        if header.strip() in content:
            updated_content = content.replace(header, header + today_section + "\n")
        else:
            updated_content = header + today_section + "\n" + content
    else:
        updated_content = header + today_section

    with open(filename, "w", encoding="utf-8") as f:
        f.write(updated_content)

    print(f"Successfully updated {filename}")


def main():
    print("Starting Google Trends Crawl...")
    results = fetch_trends_data()
    print(f"Found {len(results)} total candidate keywords.")
    update_trends_markdown(results)
    print("Crawl complete!")


if __name__ == "__main__":
    main()
