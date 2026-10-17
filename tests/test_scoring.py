from scoring import score_article, rank_articles


def art(topic, title, importance=5):
    return {"topic": topic, "title": title, "link": title,
            "importance": importance, "published": ""}


def test_liked_topic_scores_higher():
    w = {"ai": 1.0, "cricket": 0.1}
    assert score_article(art("ai", "a"), w) > score_article(art("cricket", "b"), w)


def test_rank_removes_duplicates():
    out = rank_articles([art("ai", "same"), art("ai", "Same")], {"ai": 1.0}, 5)
    assert len(out) == 1


def test_rank_orders_by_score():
    w = {"ai": 1.0, "cricket": 0.2}
    out = rank_articles([art("cricket", "c"), art("ai", "a")], w, 5)
    assert out[0]["topic"] == "ai"