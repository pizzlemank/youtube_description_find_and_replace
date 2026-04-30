import time
import random
import datetime
import os
import re
from pytrends.request import TrendReq
from pytrends.exceptions import TooManyRequestsError

# List of keywords that might indicate IP infringement (brands, characters, etc.)
IP_BLACKLIST = [
    'disney', 'marvel', 'star wars', 'nike', 'adidas', 'taylor swift', 'bts',
    'michael jackson', 'nba', 'nfl', 'mlb', 'nhl', 'nintendo', 'pokemon',
    'harry potter', 'nasa', 'hellstar', 'ysl', 'gucci', 'prada', 'louis vuitton',
    'koningsdag', 'oranje', 'higgins', 'wwe', 'kanye', 'drake', 'notre dame',
    'ariana grande', 'george strait', 'olivia dean', 'conan gray', 'man utd',
    'lidl', 'm&s', 'mnet', 'amc', 'murder drones', 'luke combs', 'ohio state',
    'wwe', 'ufc', 'f1', 'nascar', 'sanrio', 'hello kitty', 'barbie', 'oppenheimer',
    'bluey', 'inter miami', 'messi', 'ronaldo', 'real madrid', 'liverpool',
    'manchester', 'arsenal', 'chelsea', 'supreme', 'stussy', 'bape'
]

APPAREL_KEYWORDS = ['shirt', 'tshirt', 't-shirt', 'tank top', 'tanktop', 'tee', 'merch']

def get_pytrends_with_retries(pytrends, method_name, *args, **kwargs):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            method = getattr(pytrends, method_name)
            return method(*args, **kwargs)
        except TooManyRequestsError:
            wait_time = (attempt + 1) * 10 + random.randint(1, 5)
            print(f"Rate limited. Waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}...")
            time.sleep(wait_time)
        except Exception as e:
            if '429' in str(e):
                 wait_time = (attempt + 1) * 10 + random.randint(1, 5)
                 print(f"Rate limited (429). Waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}...")
                 time.sleep(wait_time)
                 continue
            print(f"An error occurred during {method_name}: {e}")
            break
    return None

def build_payload_with_retries(pytrends, keywords, **kwargs):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            pytrends.build_payload(keywords, **kwargs)
            return True
        except TooManyRequestsError:
            wait_time = (attempt + 1) * 10 + random.randint(1, 5)
            print(f"Rate limited during build_payload. Waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}...")
            time.sleep(wait_time)
        except Exception as e:
            if '429' in str(e):
                 wait_time = (attempt + 1) * 10 + random.randint(1, 5)
                 print(f"Rate limited (429) during build_payload. Waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}...")
                 time.sleep(wait_time)
                 continue
            print(f"An error occurred during build_payload: {e}")
            break
    return False

def is_ip_infringement(keyword):
    keyword_lower = keyword.lower()
    for brand in IP_BLACKLIST:
        if brand in keyword_lower:
            return True
    return False

def generate_idea(keyword):
    clean_keyword = keyword
    for apparel in sorted(APPAREL_KEYWORDS, key=len, reverse=True):
        clean_keyword = re.sub(rf'\b{apparel}\b', '', clean_keyword, flags=re.IGNORECASE).strip()

    clean_keyword = re.sub(r'\s+', ' ', clean_keyword).strip()

    if not clean_keyword:
        clean_keyword = keyword

    ideas = [
        f"Design featuring '{clean_keyword}' in a minimalist typography style.",
        f"Vintage distressed look with '{clean_keyword}' as the central element.",
        f"Cute illustration representing '{clean_keyword}' for a niche audience.",
        f"Bold, high-contrast graphic centered around '{clean_keyword}'.",
        f"Funny quote or pun related to '{clean_keyword}'."
    ]
    return random.choice(ideas)

def crawl():
    pytrends = TrendReq(hl='en-US', tz=360)
    all_results = []
    seen_keywords = set()

    for seed in APPAREL_KEYWORDS:
        print(f"Fetching rising trends for: {seed}")
        if not build_payload_with_retries(pytrends, [seed], timeframe='now 7-d'):
            continue

        related = get_pytrends_with_retries(pytrends, 'related_queries')

        if related and seed in related and related[seed]['rising'] is not None:
            rising = related[seed]['rising']
            for _, row in rising.iterrows():
                keyword = row['query']
                score = row['value']

                if len(keyword.split()) < 2:
                    continue

                if any(x in keyword.lower() for x in ['meaning', 'definition', 'how to', 'why', 'iron', 'near me']):
                    continue

                if keyword in seen_keywords:
                    continue
                seen_keywords.add(keyword)

                is_ip = is_ip_infringement(keyword)
                idea = generate_idea(keyword)

                all_results.append({
                    'keyword': keyword,
                    'score': score,
                    'is_ip': is_ip,
                    'idea': idea
                })
        time.sleep(2)

    return all_results

def format_markdown(results):
    if not results:
        return ""

    today = datetime.date.today().strftime("%Y-%m-%d")

    general = [r for r in results if not r['is_ip']]
    ip_potential = [r for r in results if r['is_ip']]

    def sort_key(x):
        val = x['score']
        if isinstance(val, str):
            if val == 'Breakout':
                return 9999
            try:
                return int(val)
            except:
                return 0
        return int(val)

    general.sort(key=sort_key, reverse=True)
    ip_potential.sort(key=sort_key, reverse=True)

    output = f"## {today}\n\n"

    output += "### General Merch Opportunities\n"
    output += "| Keyword | Score | Why/Idea |\n"
    output += "|---------|-------|----------|\n"
    for r in general:
        output += f"| {r['keyword']} | {r['score']} | {r['idea']} |\n"

    output += "\n### Potential IP Infringing Opportunities\n"
    output += "| Keyword | Score | Why/Idea |\n"
    output += "|---------|-------|----------|\n"
    for r in ip_potential:
        output += f"| {r['keyword']} | {r['score']} | {r['idea']} |\n"

    output += "\n---\n"
    return output

def main():
    print("Starting crawl...")
    results = crawl()
    print(f"Crawl finished. Found {len(results)} keywords.")

    new_content = format_markdown(results)

    if not new_content:
        print("No new trends found today.")
        return

    filename = 'trends.md'
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            existing_content = f.read()
    else:
        existing_content = "# Google Trends Merch Opportunities\n\n"

    today = datetime.date.today().strftime("%Y-%m-%d")
    if f"## {today}" in existing_content:
        print(f"Trends for {today} already exist in {filename}. Skipping update.")
        return

    title_end = existing_content.find('\n\n') + 2
    if title_end < 2:
        final_content = existing_content + "\n" + new_content
    else:
        final_content = existing_content[:title_end] + new_content + existing_content[title_end:]

    with open(filename, 'w') as f:
        f.write(final_content)

    print(f"Updated {filename}")

if __name__ == "__main__":
    main()
