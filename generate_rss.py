import cloudscraper
import json
from datetime import datetime, timezone

JSON_URL = "https://www.jugantor.com/ajax/load/latestnews/30/0/0"
OUTPUT_FILE = "rss.xml"

HEADERS = {
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.jugantor.com/",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_latest_news(url):
    scraper = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "linux", "mobile": False}
    )
    print(f"Fetching: {url}")
    response = scraper.get(url, headers=HEADERS, timeout=30)
    print(f"HTTP status: {response.status_code}")
    response.raise_for_status()

    data = response.json()
    count = len(data) if isinstance(data, list) else "?"
    print(f"Parsed {count} items")
    return data


def convert_to_rss(items):
    if not items:
        print("WARNING: No items to convert")
        return ""

    rss_items = ""
    skipped = 0

    for i, item in enumerate(items):
        title = item.get("headline", "")
        link = item.get("url", "")
        description = item.get("description", "")

        if not title and not link:
            skipped += 1
            continue

        pub_date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")

        thumb = item.get("thumb")
        enclosure = f'<enclosure url="{thumb}" type="image/jpeg"/>' if thumb else ""

        rss_items += f"""
    <item>
        <title><![CDATA[{title}]]></title>
        <link>{link}</link>
        <guid isPermaLink="true">{link}</guid>
        <description><![CDATA[{description}]]></description>
        {enclosure}
        <pubDate>{pub_date}</pubDate>
    </item>"""

    if skipped:
        print(f"Skipped {skipped} items with no title or link")
    return rss_items


def build_rss(items_xml):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
    <title>Jugantor Latest News</title>
    <link>https://www.jugantor.com</link>
    <description>Latest news from Jugantor</description>
    {items_xml}
</channel>
</rss>"""


def main():
    print("=" * 60)
    print("Starting RSS feed generation")
    print("=" * 60)

    try:
        news_items = fetch_latest_news(JSON_URL)
        items_xml = convert_to_rss(news_items)
        rss = build_rss(items_xml)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(rss)
        print(f"Saved: {OUTPUT_FILE}")

        print("=" * 60)
        print("Done")
        print("=" * 60)

    except Exception as e:
        print("=" * 60)
        print(f"FATAL: {type(e).__name__}: {e}")
        print("=" * 60)
        raise


if __name__ == "__main__":
    main()
