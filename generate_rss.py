import sys
import time
import os
import cloudscraper
from datetime import datetime, timezone

JSON_URL = "https://www.jugantor.com/ajax/load/latestnews/30/0/0"
OUTPUT_FILE = "rss.xml"

HEADERS = {
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.jugantor.com/",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_latest_news(url, retries=3, backoff=15):
    scraper = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "linux", "mobile": False}
    )
    for attempt in range(1, retries + 1):
        try:
            print(f"Fetching (attempt {attempt}/{retries}): {url}")
            response = scraper.get(url, headers=HEADERS, timeout=30)
            print(f"HTTP status: {response.status_code}")
            response.raise_for_status()
            data = response.json()
            count = len(data) if isinstance(data, list) else "?"
            print(f"Parsed {count} items")
            return data
        except Exception as e:
            print(f"Attempt {attempt} failed: {type(e).__name__}: {e}")
            if attempt < retries:
                wait = backoff * attempt
                print(f"Waiting {wait}s before retry...")
                time.sleep(wait)

    return None  # all attempts exhausted


def convert_to_rss(items):
    if not items:
        print("WARNING: No items to convert")
        return ""

    rss_items = ""
    skipped = 0

    for item in items:
        title = item.get("headline", "")
        link = item.get("url", "")
        description = item.get("description", "")

        if not title and not link:
            skipped += 1
            continue

        # Use API's own timestamp if available, fall back to now
        raw_date = item.get("created_at") or item.get("publish_date") or item.get("date")
        try:
            pub_date = datetime.fromisoformat(raw_date).strftime("%a, %d %b %Y %H:%M:%S +0000") if raw_date else None
        except (ValueError, TypeError):
            pub_date = None
        pub_date = pub_date or datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")

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

    news_items = fetch_latest_news(JSON_URL)

    if news_items is None:
        print("All fetch attempts failed.")
        if os.path.exists(OUTPUT_FILE):
            print(f"Keeping existing {OUTPUT_FILE} — no update this run.")
        else:
            print("No existing feed to fall back on.")
        print("Exiting cleanly (workflow will not fail).")
        sys.exit(0)

    items_xml = convert_to_rss(news_items)
    rss = build_rss(items_xml)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(rss)
    print(f"Saved: {OUTPUT_FILE}")

    print("=" * 60)
    print("Done")
    print("=" * 60)


if __name__ == "__main__":
    main()