import feedparser
import requests
from bs4 import BeautifulSoup
from tokenisation import *

FEEDS = [
    "https://openai.com/blog/rss.xml", 
    "https://news.google.com/rss/search?q=technology",
    "http://feeds.arstechnica.com/arstechnica/index",
    "https://techcrunch.com/rss",
    "https://tldr.tech/api/rss/tech",
    "https://news.google.com/rss/search?q=technology",
    "https://www.wired.com/feed/tag/ai/latest/rss",
    "https://www.theverge.com/rss/index.xml"
]

def fetch_articles():
    articles = []
    for urlfeed in FEEDS:
        # Parse feed and iterate a small subset of entries to control time
        feed = feedparser.parse(urlfeed)
        for entry in feed.entries[:5]:
            # Fetch article page and extract paragraph text.
            html = requests.get(entry.link, timeout=10).text
            soup = BeautifulSoup(html, 'html.parser')
            # Join all <p> tags as a quick way to get readable article text
            text = " ".join(p.get_text() for p in soup.find_all("p"))
            articles.append({
                "title": entry.title,
                "text": text,
                "source": entry.link
            })

    return articles