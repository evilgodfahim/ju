import requests
from datetime import datetime

# URL for latest news JSON
JSON_URL = "https://www.jugantor.com/ajax/load/latestnews/30/0/0"
OUTPUT_FILE = "rss.xml"

def fetch_latest_news(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def convert_to_rss(items):
    rss_items = ""
    for item in items:
        title = item["headline"]
        link = item["url"]
        description = item.get("description", "")
        
        # Convert publishDateTime to RSS format (UTC simplified)
        pub_date = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
        
        # Optional image enclosure
        thumb = item.get("thumb")
        enclosure = f'<enclosure url="{thumb}" type="image/jpeg"/>' if thumb else ""
        
        rss_items += f"""
    <item>
        <title>{title}</title>
        <link>{link}</link>
        <guid>{link}</guid>
        <description>{description}</description>
        {enclosure}
        <pubDate>{pub_date}</pubDate>
    </item>
    """
    return rss_items

def build_rss(items_xml):
    rss_feed = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
    <title>Jugantor Latest News</title>
    <link>https://www.jugantor.com</link>
    <description>Latest news from Jugantor</description>
    {items_xml}
</channel>
</rss>
"""
    return rss_feed

def save_rss(file_name, content):
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"RSS feed saved to {file_name}")

def main():
    news_items = fetch_latest_news(JSON_URL)
    items_xml = convert_to_rss(news_items)
    rss_feed = build_rss(items_xml)
    save_rss(OUTPUT_FILE, rss_feed)

if __name__ == "__main__":
    main()
