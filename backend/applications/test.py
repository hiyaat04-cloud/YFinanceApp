import requests
import feedparser

TEST_QUERY = "TCS stock"
RSS_URL = f"https://news.google.com/rss/search?q={TEST_QUERY}&hl=en-IN&gl=IN&ceid=IN:en"

# Use a User-Agent to mimic a web browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

print(f"Testing direct URL access: {RSS_URL}")

try:
    # 1. Fetch the raw XML data
    response = requests.get(RSS_URL, headers=headers, timeout=10)
    response.raise_for_status() # Raise exception for bad status codes (4xx or 5xx)

    # 2. Parse the raw XML data
    feed = feedparser.parse(response.content)

    if feed.status == 200 and feed.entries:
        print("✅ SUCCESS: Successfully fetched and parsed entries.")
        print(f"First headline title: {feed.entries[0].title}")
        print(f"First headline link: {feed.entries[0].link}")
    else:
        print(f"❌ FAILURE: Received status {feed.status}. Feed entries: {len(feed.entries)}.")
        print("Possible causes: Query returned no results or feed content is malformed.")

except requests.exceptions.RequestException as e:
    print(f"❌ CRITICAL CONNECTION FAILURE: Request timed out or failed to connect: {e}")