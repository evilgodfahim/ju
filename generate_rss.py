import requests
import json
from datetime import datetime, timezone

# Target JSON endpoint
JSON_URL = "https://www.jugantor.com/ajax/load/latestnews/30/0/0"

# FlareSolverr endpoint (local service)
FLARESOLVERR_URL = "http://localhost:8191/v1"

OUTPUT_FILE = "rss.xml"


def fetch_latest_news_via_flaresolverr(target_url):
    """
    Sends a request to FlareSolverr.
    FlareSolverr loads the page in a real browser and returns the response body.
    """

    payload = {
        "cmd": "request.get",
        "url": target_url,
        "maxTimeout": 60000
    }

    response = requests.post(
        FLARESOLVERR_URL,
        json=payload,
        timeout=90
    )
    response.raise_for_status()

    data = response.json()

    if data.get("status") != "ok":
        raise RuntimeError("FlareSolverr failed to fetch the URL")

    # FlareSolverr returns the response body as a string
    body = data["solution"]["response"]

    return json.loads(body)


def convert_to_rss(items):
    rss_items = ""

    for item in items:
        title = item.get("headline", "")
        link = item.get("url", "")
        description = item.get("description", "")

        # Proper RFC 822 datetime in UTC
        pub_date = datetime.now(timezone.utc).strftime(
            "%a, %d %b %Y %H:%M:%S +0000"
        )

        thumb = item.get("thumb")
        enclosure = (
            f'<enclosure url="{thumb}" type="image/jpeg"/>'
            if thumb else ""
        )

        rss_items += f"""
    <item>
        <title><![CDATA[{title}]]></title>
        <link>{link}</link>
        <guid isPermaLink="true">{link}</guid>
        <description><![CDATA[{description}]]></description>
        {enclosure}
        <pubDate>{pub_date}</pubDate>
    </item>
    """

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
</rss>
"""


def save_rss(file_name, content):
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    news_items = fetch_latest_news_via_flaresolverr(JSON_URL)
    items_xml = convert_to_rss(news_items)
    rss_feed = build_rss(items_xml)
    save_rss(OUTPUT_FILE, rss_feed)


if __name__ == "__main__":
    main()