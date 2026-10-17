import os
import json
import feedparser
from urllib.parse import quote_plus
from google import genai
from google.genai import types

MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")


def fetch_articles(topic, limit=8):
    """Fetch recent headlines for a topic from Google News RSS."""
    url = (
        "https://news.google.com/rss/search?q="
        + quote_plus(f"{topic} when:2d")
        + "&hl=en-US&gl=US&ceid=US:en"
    )
    feed = feedparser.parse(url)
    articles = []
    for e in feed.entries[:limit]:
        source = e.get("source", {}).get("title", "")
        title = e.title
        if source and title.endswith(" - " + source):
            title = title[: -len(source) - 3]
        articles.append({
            "topic": topic,
            "title": title,
            "link": e.link,
            "source": source,
            "published": e.get("published", ""),
        })
    return articles


def enrich(articles):
    """Add a one-line summary and importance score to each article using Gemini."""
    if not articles:
        return articles
    headlines = "\n".join(
        f"{i}. {a['title']} ({a['source']})" for i, a in enumerate(articles)
    )
    prompt = (
        "You are a newspaper editor. For each numbered headline below, return a "
        "JSON array of objects with these keys: id (the number), summary (one "
        "plain sentence that expands the headline without inventing facts), "
        "importance (integer 1-10, how significant the story is).\n\n"
        "Headlines:\n" + headlines
    )
    try:
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        resp = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json", temperature=0
            ),
        )
        by_id = {d["id"]: d for d in json.loads(resp.text)}
    except Exception as err:
        print("AI enrichment failed, using fallback:", err)
        by_id = {}
    for i, a in enumerate(articles):
        d = by_id.get(i, {})
        a["summary"] = d.get("summary", a["title"])
        a["importance"] = d.get("importance", 5)
    return articles


def get_topic_articles(topic, limit=8):
    return enrich(fetch_articles(topic, limit))


if __name__ == "__main__":
    all_articles = []
    for topic in ["artificial intelligence", "cricket"]:
        all_articles += get_topic_articles(topic, limit=5)
    for a in all_articles:
        print(f"[{a['topic']}] {a['title']} ({a['source']})")
        print("  ", a["summary"], "| importance:", a["importance"])
    with open("cache.json", "w", encoding="utf-8") as f:
        json.dump(all_articles, f, indent=2)
    print("\nSaved cache.json")