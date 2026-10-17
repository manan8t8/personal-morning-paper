import math
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime


def age_hours(published):
    try:
        dt = parsedate_to_datetime(published)
        return max((datetime.now(timezone.utc) - dt).total_seconds() / 3600, 0)
    except Exception:
        return 24.0


def score_article(article, weights):
    """0.5 reader interest + 0.3 story importance + 0.2 freshness."""
    max_w = max(weights.values()) if weights else 1.0
    topic_w = weights.get(article["topic"], 0.0) / (max_w or 1.0)
    recency = math.exp(-age_hours(article.get("published", "")) / 24)
    importance = article.get("importance", 5) / 10
    return round(0.5 * topic_w + 0.3 * importance + 0.2 * recency, 4)


def explain(article):
    why = f"Matches your interest in {article['topic']}"
    if age_hours(article.get("published", "")) < 12:
        why += ", and it is fresh"
    if article.get("importance", 5) >= 8:
        why += ", and it is a major story"
    return why


def rank_articles(articles, weights, n):
    """Score, remove duplicates, cap any one topic, return the top n."""
    seen, scored = set(), []
    for a in articles:
        key = a["title"].lower()
        if key in seen:
            continue
        seen.add(key)
        a = dict(a)
        a["score"] = score_article(a, weights)
        a["why"] = explain(a)
        scored.append(a)
    scored.sort(key=lambda a: a["score"], reverse=True)
    cap = max(2, math.ceil(n / 2))
    counts, picked = {}, []
    for a in scored:
        if counts.get(a["topic"], 0) >= cap:
            continue
        counts[a["topic"]] = counts.get(a["topic"], 0) + 1
        picked.append(a)
        if len(picked) == n:
            break
    return picked