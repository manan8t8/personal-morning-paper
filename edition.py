import json
import random

import db
import ingest
from scoring import rank_articles

GENERAL = ["world news", "technology", "business", "science", "health",
           "sports", "entertainment", "education"]
SIZE = {5: 8, 10: 12, 15: 18}


def gather(topic, limit):
    arts = ingest.get_topic_articles(topic, limit)
    if arts:
        return arts
    try:  # offline fallback so the demo never dies
        with open("cache.json", encoding="utf-8") as f:
            cached = json.load(f)
        return [a for a in cached if a["topic"] == topic] or cached[:limit]
    except Exception:
        return []


def build_edition(user):
    weights = db.get_weights(user["id"])
    skipped = db.get_skipped_links(user["id"])
    size = SIZE.get(user["minutes"], 12)
    top_topics = sorted(weights, key=weights.get, reverse=True)[:5]

    candidates = []
    for t in top_topics:
        candidates += gather(t, 6)
    candidates = [a for a in candidates if a["link"] not in skipped]

    explore = []
    pool = [t for t in GENERAL if t not in weights]
    if pool:
        explore = gather(random.choice(pool), 4)
        explore = [a for a in explore if a["link"] not in skipped]
        explore = sorted(explore, key=lambda a: a["importance"], reverse=True)[:2]
        for a in explore:
            a["why"] = "Something outside your usual interests"
            a["score"] = 0

    ranked = rank_articles(candidates, weights, size - len(explore))
    return {
        "lead": ranked[0] if ranked else None,
        "featured": ranked[1:4],
        "briefs": ranked[4:] + explore,
    }