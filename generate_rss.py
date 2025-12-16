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

    try:
        print(f"Sending request to FlareSolverr for: {target_url}")
        response = requests.post(
            FLARESOLVERR_URL,
            json=payload,
            timeout=90
        )
        response.raise_for_status()

        data = response.json()
        print(f"FlareSolverr status: {data.get('status')}")

        if data.get("status") != "ok":
            error_msg = data.get('message', 'Unknown error')
            print(f"FlareSolverr error: {error_msg}")
            raise RuntimeError(f"FlareSolverr failed: {error_msg}")

        # Access the correct response body field
        # FlareSolverr v3+ uses different structure
        solution = data.get("solution", {})
        
        # Try different possible response fields
        body = None
        if "response" in solution:
            body = solution["response"]
        elif "body" in solution:
            body = solution["body"]
        elif "html" in solution:
            body = solution["html"]
        
        if body is None:
            print(f"Available solution keys: {solution.keys()}")
            print(f"Full response structure: {json.dumps(data, indent=2)[:1000]}")
            raise ValueError("Could not find response body in FlareSolverr response")
        
        print(f"Response body type: {type(body)}")
        print(f"Response body length: {len(body) if body else 0}")
        
        if not body or not str(body).strip():
            print("WARNING: Empty response body from FlareSolverr")
            return []
        
        # Try to parse as JSON
        try:
            parsed = json.loads(body)
            print(f"Successfully parsed JSON with {len(parsed) if isinstance(parsed, list) else 'unknown'} items")
            return parsed
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Response preview (first 500 chars): {str(body)[:500]}")
            
            # Check if response is HTML wrapping JSON (common with browser responses)
            if isinstance(body, str) and body.strip().startswith('<'):
                print("Detected HTML wrapper - attempting to extract JSON from <pre> tags")
                
                # Extract content between <pre> and </pre> tags
                import re
                pre_match = re.search(r'<pre[^>]*>(.*?)</pre>', body, re.DOTALL)
                
                if pre_match:
                    json_content = pre_match.group(1).strip()
                    print(f"Extracted {len(json_content)} chars from <pre> tag")
                    
                    try:
                        parsed = json.loads(json_content)
                        print(f"Successfully parsed extracted JSON with {len(parsed) if isinstance(parsed, list) else 'unknown'} items")
                        return parsed
                    except json.JSONDecodeError as e2:
                        print(f"Failed to parse extracted content: {e2}")
                        print(f"Extracted content preview: {json_content[:500]}")
                        raise ValueError(f"Extracted content is not valid JSON: {e2}")
                else:
                    print("ERROR: Could not find <pre> tags in HTML response")
                    raise ValueError("JSON wrapped in HTML but no <pre> tags found")
            
            raise ValueError(f"Response is not valid JSON: {e}")

    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to FlareSolverr at http://localhost:8191")
        print("Make sure FlareSolverr service is running")
        raise
    except requests.exceptions.Timeout:
        print("ERROR: Request to FlareSolverr timed out")
        raise
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {type(e).__name__}: {e}")
        raise


def convert_to_rss(items):
    """Convert news items to RSS format"""
    if not items:
        print("WARNING: No items to convert to RSS")
        return ""
    
    rss_items = ""

    for i, item in enumerate(items):
        title = item.get("headline", "")
        link = item.get("url", "")
        description = item.get("description", "")

        if not title and not link:
            print(f"Skipping item {i}: missing title and link")
            continue

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
    """Build complete RSS feed"""
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
    """Save RSS feed to file"""
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"RSS feed saved to {file_name}")


def main():
    try:
        print("=" * 60)
        print("Starting RSS feed generation")
        print("=" * 60)
        
        news_items = fetch_latest_news_via_flaresolverr(JSON_URL)
        
        item_count = len(news_items) if isinstance(news_items, list) else 0
        print(f"Retrieved {item_count} news items")
        
        if item_count == 0:
            print("WARNING: No news items retrieved, generating empty RSS feed")
        
        items_xml = convert_to_rss(news_items)
        rss_feed = build_rss(items_xml)
        save_rss(OUTPUT_FILE, rss_feed)
        
        print("=" * 60)
        print("RSS generation completed successfully")
        print("=" * 60)
        
    except Exception as e:
        print("=" * 60)
        print(f"FATAL ERROR: {type(e).__name__}: {e}")
        print("=" * 60)
        raise


if __name__ == "__main__":
    main()