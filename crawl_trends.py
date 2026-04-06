import pandas as pd
from pytrends.request import TrendReq
import datetime
import os
import re
import time

def get_trends():
    pytrends = TrendReq(hl='en-US', tz=360)

    # Common merch-related seed keywords
    seed_keywords = ['tshirt', 'shirt', 'tank top', 'merch']

    all_results = []

    for kw in seed_keywords:
        try:
            print(f"Fetching trends for {kw}...")
            pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo='', gprop='')
            related_queries = pytrends.related_queries()

            if kw in related_queries and related_queries[kw]['rising'] is not None:
                rising = related_queries[kw]['rising']
                for index, row in rising.iterrows():
                    all_results.append({
                        'keyword': row['query'],
                        'score': row['value'],
                        'seed': kw
                    })
            time.sleep(2) # Avoid rate limiting
        except Exception as e:
            print(f"Error fetching trends for {kw}: {e}")

    return all_results

def is_ip_infringing(keyword):
    # A more comprehensive list of known IP-heavy terms.
    blacklist = [
        'disney', 'marvel', 'star wars', 'nike', 'adidas', 'nfl', 'nba', 'mlb', 'nhl',
        'pokemon', 'nintendo', 'anime', 'movie', 'netflix', 'harry potter', 'barbie',
        'lego', 'band', 'concert', 'tour', 'mickey', 'mouse', 'batman', 'superman',
        'spiderman', 'avengers', 'disneyland', 'walt', 'pixar', 'warner bros',
        'gucci', 'prada', 'zara', 'h&m', 'brand', 'official', 'national geographic',
        'michael jackson', 'celebrity', 'singer', 'actor', 'actress', 'fortnite',
        'roblox', 'minecraft', 'supreme', 'champion', 'under armour', 'puma',
        'reebok', 'vans', 'converse', 'levis', 'calvin klein', 'tommy hilfiger',
        'ralph lauren', 'lacoste', 'fendi', 'versace', 'burberry', 'chanel',
        'louis vuitton', 'hermes', 'dior', 'balenciaga', 'yeezy', 'off-white'
    ]
    keyword_lower = keyword.lower()
    for item in blacklist:
        # Use regex for better matching (word boundaries)
        if re.search(rf'\b{re.escape(item)}\b', keyword_lower):
            return True
    return False

def filter_and_categorize(trends):
    merch_patterns = [
        r'\bshirt\b', r'\btshirt\b', r'\bt-shirt\b', r'\btanktop\b',
        r'\btank top\b', r'\bhoodie\b', r'\bmerch\b'
    ]

    # Filter out common non-commercial search terms
    exclude_patterns = [
        r'\bmeaning\b', r'\bdefinition\b', r'\bcrossword\b', r'\bclue\b',
        r'\bhow to\b', r'\bwhy\b'
    ]

    filtered_trends = []
    for trend in trends:
        kw = trend['keyword'].lower()
        # Ensure it's long tail and contains merch keywords
        if any(re.search(pattern, kw) for pattern in merch_patterns):
            # Exclude non-commercial intent
            if any(re.search(pattern, kw) for pattern in exclude_patterns):
                continue

            # Try to ensure it's not JUST the seed keyword
            if len(kw.split()) >= 2:
                trend['is_ip'] = is_ip_infringing(kw)
                filtered_trends.append(trend)

    # Remove duplicates
    seen_keywords = set()
    unique_trends = []
    for t in filtered_trends:
        if t['keyword'] not in seen_keywords:
            unique_trends.append(t)
            seen_keywords.add(t['keyword'])

    return sorted(unique_trends, key=lambda x: x['score'], reverse=True)

def generate_markdown(trends):
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')

    general_section = f"### General Merch Opportunities - {date_str}\n\n"
    general_section += "| keyword | score | why/idea |\n"
    general_section += "| :--- | :--- | :--- |\n"

    ip_section = f"### Potential IP Infringing Opportunities - {date_str}\n\n"
    ip_section += "| keyword | score | why/idea |\n"
    ip_section += "| :--- | :--- | :--- |\n"

    gen_count = 0
    ip_count = 0

    for t in trends:
        kw = t['keyword'].lower()
        # Improved "why" generator
        if t['is_ip']:
            why = "Likely IP infringing. High search volume detected for a major brand or character. Avoid direct usage; consider if there is a parody or fair-use angle, but proceed with caution."
        else:
            if "funny" in kw:
                why = "Humor-based design. People are looking for laughs. Use bold, clear typography and a simple graphic that complements the joke."
            elif any(x in kw for x in ["vintage", "retro", "90s", "80s"]):
                why = "Nostalgic appeal. Trend for throwback styles is strong. Use distressed textures, neon accents, or classic serif fonts."
            elif "aesthetic" in kw or "vaporwave" in kw:
                why = "Visual style trend. Target audience values unique, artistic compositions. Use pastel gradients and low-poly or retro-tech motifs."
            elif any(x in kw for x in ["dog", "cat", "pet", "animal"]):
                why = "Pet lover niche. High engagement. Create a cute or relatable design featuring the specific animal."
            elif any(x in kw for x in ["mom", "dad", "grandpa", "grandma", "family"]):
                why = "Family/Gift niche. Great for upcoming holidays or birthdays. Focus on sentimental or 'best ever' themes."
            elif any(x in kw for x in ["teacher", "nurse", "doctor", "engineer", "job"]):
                why = "Profession pride. People love wearing their identity. Use icons related to the career and an empowering or humorous slogan."
            else:
                why = "Niche long-tail keyword. Rising interest suggests low competition but growing demand. Create a design that speaks directly to this specific subculture."

        row = f"| {t['keyword']} | {t['score']} | {why} |\n"

        if t['is_ip']:
            ip_section += row
            ip_count += 1
        else:
            general_section += row
            gen_count += 1

    return (general_section if gen_count > 0 else ""), (ip_section if ip_count > 0 else "")

def update_trends_md(gen_md, ip_md):
    if not gen_md and not ip_md:
        print("No new trends found today.")
        return

    # Header
    header = "# Google Trends Merch Opportunities\n\n"

    if os.path.exists('trends.md'):
        with open('trends.md', 'r') as f:
            content = f.read()
    else:
        content = header

    # Ensure the header is at the top if it wasn't there
    if not content.startswith(header):
        content = header + content.replace(header, "")

    new_entries = ""
    if gen_md:
        new_entries += gen_md + "\n"
    if ip_md:
        new_entries += ip_md + "\n"

    # Prepend new entries after the header
    updated_content = content.replace(header, header + new_entries)

    with open('trends.md', 'w') as f:
        f.write(updated_content)

if __name__ == "__main__":
    print("Fetching trends...")
    trends = get_trends()
    print(f"Found {len(trends)} raw trends.")
    filtered = filter_and_categorize(trends)
    print(f"Filtered to {len(filtered)} relevant trends.")
    gen_md, ip_md = generate_markdown(filtered)
    update_trends_md(gen_md, ip_md)
    print("trends.md updated.")
