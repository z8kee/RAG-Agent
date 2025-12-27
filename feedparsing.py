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
    "https://news.google.com/rss/search?q=technology"

]

def fetch_articles():
    articles = []
    for urlfeed in FEEDS:
        feed = feedparser.parse(urlfeed)
        for entry in feed.entries[:5]:
            html = requests.get(entry.link, timeout=10).text
            soup = BeautifulSoup(html, 'html.parser')
            text = " ".join(p.get_text() for p in soup.find_all("p"))
            articles.append({
                "title": entry.title,
                "text": text,
                "source": entry.link
            })

    return articles
