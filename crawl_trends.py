import datetime
import re
import time
import pandas as pd
from pytrends.request import TrendReq

SEED_KEYWORDS = ["tshirt", "t-shirt", "shirt", "tank top", "tanktop", "tee", "merch"]

APPAREL_TERMS = ["shirt", "tshirt", "t-shirt", "tank top", "tanktop", "tee", "merch"]

EXACT_EXCLUSIONS = {
    "t shirt", "t shirts", "t-shirt", "t-shirts", "tshirt", "tshirts",
    "tee", "tees", "shirt", "shirts", "tank top", "tank tops", "tanktop", "tanktops", "merch"
}

NON_COMMERCIAL_TERMS = [
    "meaning", "definition", "how to", "why", "iron", "near me", "template",
    "mockup", "tee times", "tee time", "tee off", "graphic tee", "essential tee",
    "vintage tee", "oversized tee", "plain shirt", "blank shirt", "kaffee",
    "rezepte", "bh für", "bra for", "tutorial", "bra", "t-shirt bra", "tee height",
    "là gì", "t-shirt femme", "custom t-shirt printing", "roblox t-shirt"
]

IP_BLACKLIST = [
    "disney", "marvel", "star wars", "nike", "adidas", "taylor swift", "bts",
    "michael jackson", "nba", "wnba", "nfl", "mlb", "nhl", "nintendo", "pokemon",
    "pokémon", "harry potter", "nasa", "hellstar", "ysl", "gucci", "prada",
    "louis vuitton", "arsenal", "real madrid", "liverpool", "man city", "chelsea",
    "bayern", "barcelona", "knicks", "lakers", "celtics", "warriors", "bulls",
    "amiri", "trapstar", "corteiz", "sp5der", "minus two", "syna world",
    "harry styles", "gracie abrams", "daniel caesar", "bad bunny", "billie eilish",
    "drake", "kanye", "travis scott", "bruno mars", "hello kitty", "sanrio",
    "nascar", "f1", "mercedes", "ferrari", "red bull", "toy story", "psg",
    "asap rocky", "megan moroney", "sean john", "morgan wallen", "spurs", "rcb",
    "snipes", "asos", "pattie gonia", "wingstop", "ariana grande", "selena gomez",
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
    "wimbledon", "alan jackson"
]


def is_ip_infringing(keyword: str) -> bool:
    kw_lower = keyword.lower()
    for ip in IP_BLACKLIST:
        pattern = r"\b" + re.escape(ip) + r"\b"
        if re.search(pattern, kw_lower):
            return True
    return False


def parse_score(value) -> int:
    if str(value).strip().lower() == "breakout":
        return 9999
    try:
        return int(str(value).replace("+", "").replace("%", "").strip())
    except ValueError:
        return 0


def generate_idea(keyword: str) -> str:
    kw_lower = keyword.lower()
    clean_topic = kw_lower
    sorted_terms = sorted(
        ["tshirts", "tank tops", "t-shirts", "tank top", "tanktop", "tshirt", "t-shirt", "shirts", "shirt", "tees", "tee", "merch"],
        key=len, reverse=True
    )
    for term in sorted_terms:
        clean_topic = re.sub(r"\b" + re.escape(term) + r"\b", "", clean_topic)
    clean_topic = " ".join(clean_topic.split()).title().strip()
    if not clean_topic:
        clean_topic = keyword.title()

    return f"Surging demand around '{clean_topic}'. Ideal for POD t-shirts featuring illustrative graphic artwork or bold typography inspired by '{clean_topic}'."


def fetch_trends_data():
    pytrends = TrendReq(hl="en-US", tz=360)
    all_results = {}

    for seed in SEED_KEYWORDS:
        retries = 3
        while retries > 0:
            try:
                pytrends.build_payload([seed], timeframe="now 7-d")
                related = pytrends.related_queries()
                if seed in related and related[seed]["rising"] is not None:
                    df = related[seed]["rising"]
                    for _, row in df.iterrows():
                        query = str(row["query"]).strip()
                        value = row["value"]
                        kw_lower = query.lower()

                        if kw_lower in EXACT_EXCLUSIONS:
                            continue

                        if any(non_com in kw_lower for non_com in NON_COMMERCIAL_TERMS):
                            continue

                        words = kw_lower.split()
                        if len(words) < 2:
                            continue

                        if not any(apparel in kw_lower for apparel in APPAREL_TERMS):
                            continue

                        score = parse_score(value)
                        if query not in all_results or score > parse_score(all_results[query]["value"]):
                            all_results[query] = {
                                "keyword": query,
                                "value": value,
                                "score": score
                            }
                break
            except Exception as e:
                retries -= 1
                if retries == 0:
                    print(f"Failed fetching for seed '{seed}': {e}")
                else:
                    time.sleep(10)
        time.sleep(5)

    return list(all_results.values())


def update_trends_markdown(opportunities, date_str=None):
    if date_str is None:
        date_str = datetime.date.today().isoformat()

    general_opps = []
    ip_opps = []

    for item in opportunities:
        kw = item["keyword"]
        val_str = str(item["value"])
        if val_str.lower() == "breakout":
            display_score = "Breakout"
        else:
            display_score = f"+{val_str}%" if not val_str.startswith("+") else val_str

        idea = generate_idea(kw)
        entry = {
            "keyword": kw,
            "score": display_score,
            "numeric_score": item["score"],
            "why": idea
        }

        if is_ip_infringing(kw):
            ip_opps.append(entry)
        else:
            general_opps.append(entry)

    general_opps.sort(key=lambda x: x["numeric_score"], reverse=True)
    ip_opps.sort(key=lambda x: x["numeric_score"], reverse=True)

    lines = [f"## {date_str}\n"]

    lines.append("### General Merch Opportunities\n")
    if general_opps:
        lines.append("| Keyword | Score | Why/Idea/Market |")
        lines.append("| --- | --- | --- |")
        for g in general_opps:
            lines.append(f"| {g['keyword']} | {g['score']} | {g['why']} |")
    else:
        lines.append("No general merch opportunities found for this period.")
    lines.append("\n")

    lines.append("### Potential IP Infringing Opportunities\n")
    if ip_opps:
        lines.append("| Keyword | Score | Why/Idea/Market |")
        lines.append("| --- | --- | --- |")
        for ip in ip_opps:
            lines.append(f"| {ip['keyword']} | {ip['score']} | {ip['why']} |")
    else:
        lines.append("No potential IP infringing opportunities found for this period.")
    lines.append("\n")

    new_section_content = "\n".join(lines)

    existing_content = ""
    try:
        with open("trends.md", "r", encoding="utf-8") as f:
            existing_content = f.read()
    except FileNotFoundError:
        pass

    header = "# Google Trends Merch Opportunities\n\n"

    if f"## {date_str}" in existing_content:
        print(f"Section for date {date_str} already exists in trends.md. Skipping duplicate update.")
        return

    if existing_content.startswith("# Google Trends Merch Opportunities"):
        body = existing_content[len(header):].lstrip()
        final_content = header + new_section_content + "\n" + body
    else:
        final_content = header + new_section_content

    with open("trends.md", "w", encoding="utf-8") as f:
        f.write(final_content.strip() + "\n")

    print(f"Successfully updated trends.md for {date_str}")


if __name__ == "__main__":
    opps = fetch_trends_data()
    update_trends_markdown(opps)
