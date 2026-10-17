import json
import sqlite3

DB_PATH = "paper.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            minutes INTEGER DEFAULT 10,
            created TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS user_topics (
            user_id INTEGER,
            topic TEXT,
            weight REAL,
            PRIMARY KEY (user_id, topic)
        );
        CREATE TABLE IF NOT EXISTS editions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            edition_date TEXT,
            data TEXT,
            created TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            link TEXT,
            topic TEXT,
            action TEXT,
            created TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)


def create_user(name, minutes, topics):
    """topics is a dict like {"cricket": 1.0, "ai": 1.0}."""
    with get_conn() as c:
        cur = c.execute(
            "INSERT INTO users (name, minutes) VALUES (?, ?)", (name, minutes)
        )
        uid = cur.lastrowid
        for topic, weight in topics.items():
            c.execute(
                "INSERT OR REPLACE INTO user_topics VALUES (?, ?, ?)",
                (uid, topic, weight),
            )
    return uid


def get_user(uid):
    with get_conn() as c:
        return c.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()


def get_weights(uid):
    with get_conn() as c:
        rows = c.execute(
            "SELECT topic, weight FROM user_topics WHERE user_id = ?", (uid,)
        ).fetchall()
    return {r["topic"]: r["weight"] for r in rows}


def save_edition(uid, edition_date, data):
    with get_conn() as c:
        c.execute(
            "DELETE FROM editions WHERE user_id = ? AND edition_date = ?",
            (uid, edition_date),
        )
        cur = c.execute(
            "INSERT INTO editions (user_id, edition_date, data) VALUES (?, ?, ?)",
            (uid, edition_date, json.dumps(data)),
        )
        return cur.lastrowid

def get_edition_for_date(uid, edition_date):
    with get_conn() as c:
        return c.execute(
            "SELECT * FROM editions WHERE user_id = ? AND edition_date = ?",
            (uid, edition_date),
        ).fetchone()


def get_edition_by_id(uid, eid):
    with get_conn() as c:
        return c.execute(
            "SELECT * FROM editions WHERE user_id = ? AND id = ?", (uid, eid)
        ).fetchone()


def list_editions(uid):
    with get_conn() as c:
        return c.execute(
            "SELECT id, edition_date FROM editions WHERE user_id = ? "
            "ORDER BY edition_date DESC",
            (uid,),
        ).fetchall()
        
def record_event(uid, link, topic, action):

    with get_conn() as c:
        c.execute(
            "INSERT INTO events (user_id, link, topic, action) VALUES (?, ?, ?, ?)",
            (uid, link, topic, action),
        )


def adjust_weight(uid, topic, delta):
    with get_conn() as c:
        row = c.execute(
            "SELECT weight FROM user_topics WHERE user_id = ? AND topic = ?",
            (uid, topic),
        ).fetchone()
        if row:
            new = min(3.0, max(0.05, row["weight"] + delta))
        else:
            new = max(0.1, 0.5 + delta)  # a brand-new interest starts mid-way
        c.execute(
            "INSERT OR REPLACE INTO user_topics VALUES (?, ?, ?)", (uid, topic, new)
        )
    return round(new, 2)


def get_skipped_links(uid):
    with get_conn() as c:
        rows = c.execute(
            "SELECT link FROM events WHERE user_id = ? AND action = 'skip'", (uid,)
        ).fetchall()
    return {r["link"] for r in rows}