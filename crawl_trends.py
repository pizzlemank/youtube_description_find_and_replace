import os
import re
import time
import datetime
import pandas as pd
from pytrends.request import TrendReq

SEED_KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]

APPAREL_TERMS = [
    "tshirts", "tank tops", "tshirt", "t-shirt", "tanktop", "tank top",
    "shirts", "shirt", "tees", "tee", "merch"
]

EXCLUDED_TERMS = [
    "meaning", "definition", "how to", "why", "iron", "near me", "template",
    "mockup", "tee times", "tee time", "tee off", "graphic tee", "essential tee",
    "vintage tee", "oversized tee", "plain shirt", "blank shirt", "kaffee",
    "rezepte", "bh für", "bra for", "tutorial", "bra", "t-shirt bra",
    "tee height", "là gì", "t-shirt femme", "custom t-shirt printing", "roblox t-shirt"
]

EXACT_EXCLUDED = {
    "tshirt", "t shirt", "t-shirt", "tshirts", "t-shirts", "shirt", "shirts",
    "tee", "tees", "tank top", "tanktop", "tank tops", "merch"
}

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
    "messi", "ronaldo", "spiderman", "spider-man", "batman", "superman", "fifa",
    "uefa", "palace", "kobe", "cowboys", "yankees", "dodgers", "dfb", "us open",
    "olympics", "cecil", "h&m", "levi's", "zara", "gap", "old navy", "lululemon",
    "patagonia", "north face", "under armour", "puma", "reebok", "vans",
    "converse", "stussy", "supreme", "hilary duff", "lewis capaldi", "radiohead",
    "beabadoobee", "phoebe bridgers", "kmfdm", "ye", "jackass", "runescape",
    "supergirl", "noah kahan", "my chemical romance", "mcr", "john deere",
    "wimbledon", "alan jackson", "bronson"
]


def is_ip_infringing(keyword: str) -> bool:
    kw_lower = keyword.lower()
    for ip in IP_BLACKLIST:
        pattern = r"\b" + re.escape(ip) + r"\b"
        if re.search(pattern, kw_lower):
            return True
    return False


def is_valid_opportunity(keyword: str) -> bool:
    kw_lower = keyword.lower().strip()
    if kw_lower in EXACT_EXCLUDED:
        return False
    if len(kw_lower.split()) < 2:
        return False
    for exc in EXCLUDED_TERMS:
        if exc in kw_lower:
            return False
    has_apparel = any(term in kw_lower for term in APPAREL_TERMS)
    return has_apparel


def generate_why_idea(keyword: str, is_ip: bool) -> str:
    kw_lower = keyword.lower()
    concept = kw_lower
    # Replace apparel terms in order of length (longest first)
    sorted_apparel = sorted(APPAREL_TERMS, key=len, reverse=True)
    for term in sorted_apparel:
        concept = re.sub(r"\b" + re.escape(term) + r"\b", "", concept, flags=re.IGNORECASE)
    concept = re.sub(r"\s+", " ", concept).strip()

    if is_ip:
        return (
            f"Trending search related to pop culture / IP '{concept.title()}'. High demand on POD platforms "
            f"(Etsy, Redbubble, Amazon), but carries copyright/trademark infringement risk. Require official license or transformative homage design."
        )
    else:
        if concept:
            return (
                f"Surging demand for niche phrase/topic '{concept.title()}'. Opportunity to design a custom graphic shirt, "
                f"typography tee, or humorous artwork around '{concept}' targeting enthusiasts looking for specialized apparel."
            )
        else:
            return (
                f"Rising search trend in apparel. Design clean typography or bold graphic art targeting current online shoppers."
            )


def fetch_rising_queries():
    pytrend = TrendReq(hl="en-US", tz=360)
    all_results = []
    seen_keywords = set()

    for seed in SEED_KEYWORDS:
        print(f"Fetching related queries for seed: '{seed}'...")
        retries = 3
        while retries > 0:
            try:
                pytrend.build_payload([seed], cat=0, timeframe="now 7-d", geo="", gprop="")
                related = pytrend.related_queries()
                if seed in related and "rising" in related[seed] and related[seed]["rising"] is not None:
                    df = related[seed]["rising"]
                    for _, row in df.iterrows():
                        kw = str(row["query"]).strip()
                        val = row["value"]
                        val_str = str(val).strip()

                        if kw.lower() in seen_keywords:
                            continue
                        if not is_valid_opportunity(kw):
                            continue

                        seen_keywords.add(kw.lower())

                        # Score handling
                        if "Breakout" in val_str or val_str == "Breakout":
                            score_num = 9999
                            score_disp = "Breakout"
                        else:
                            try:
                                score_num = float(val)
                                score_disp = f"+{int(score_num)}%" if score_num > 0 else str(score_num)
                            except ValueError:
                                score_num = 0
                                score_disp = val_str

                        ip_flag = is_ip_infringing(kw)
                        why_idea = generate_why_idea(kw, ip_flag)

                        all_results.append({
                            "keyword": kw,
                            "score_num": score_num,
                            "score": score_disp,
                            "why_idea": why_idea,
                            "is_ip": ip_flag
                        })
                break
            except Exception as e:
                print(f"Error fetching '{seed}': {e}. Retrying in 10s... ({retries} left)")
                retries -= 1
                time.sleep(10)
        time.sleep(5)

    all_results.sort(key=lambda x: x["score_num"], reverse=True)
    return all_results


def update_trends_markdown(results):
    today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    filename = "trends.md"

    # Separate results
    general = [r for r in results if not r["is_ip"]]
    ip_infringing = [r for r in results if r["is_ip"]]

    # Build section text for today
    section_lines = [f"## {today_str}", ""]

    section_lines.append("### General Merch Opportunities")
    if general:
        section_lines.append("| keyword | score | why you think is an opportunity, idea for design, or what the internet shopping is already doing |")
        section_lines.append("|---|---|---|")
        for item in general:
            section_lines.append(f"| {item['keyword']} | {item['score']} | {item['why_idea']} |")
    else:
        section_lines.append("*No new general merch opportunities identified today.*")

    section_lines.append("")
    section_lines.append("### Potential IP Infringing Opportunities")
    if ip_infringing:
        section_lines.append("| keyword | score | why you think is an opportunity, idea for design, or what the internet shopping is already doing |")
        section_lines.append("|---|---|---|")
        for item in ip_infringing:
            section_lines.append(f"| {item['keyword']} | {item['score']} | {item['why_idea']} |")
    else:
        section_lines.append("*No potential IP infringing opportunities identified today.*")

    section_lines.append("")

    new_section_content = "\n".join(section_lines)

    # Read existing trends.md if exists
    header = "# Google Trends Merch Opportunities\n\n"
    existing_content = ""

    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            existing_content = f.read()

        # Check if today's header already exists
        if f"## {today_str}" in existing_content:
            print(f"Header for ## {today_str} already exists in {filename}. Skipping update.")
            return

        if existing_content.startswith("# Google Trends Merch Opportunities"):
            # Strip main header to prepend new section below it
            content_after_header = existing_content[len(header):]
            full_content = header + new_section_content + content_after_header
        else:
            full_content = header + new_section_content + existing_content
    else:
        full_content = header + new_section_content

    with open(filename, "w", encoding="utf-8") as f:
        f.write(full_content)

    print(f"Successfully updated {filename} for {today_str}.")


if __name__ == "__main__":
    results = fetch_rising_queries()
    print(f"Fetched {len(results)} total opportunity keywords.")
    update_trends_markdown(results)
