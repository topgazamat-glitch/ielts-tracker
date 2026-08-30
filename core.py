"""Shared config, database access and domain logic."""
import json
import os
import sqlite3
import secrets
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
# DATA_DIR is overridable so a host can point it at a disk that survives
# redeploys - everything that must persist (database + photos) lives here.
DATA_DIR = os.environ.get("DATA_DIR") or os.path.join(ROOT, "data")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
DB_PATH = os.path.join(DATA_DIR, "app.db")
CONFIG_PATH = os.path.join(ROOT, "config.json")

DEFAULT_TAGS = [
    "Under word count",
    "Watch articles",
    "Tense errors",
    "Weak linking",
    "Good structure",
    "Strong vocabulary",
    "Off topic",
    "Handwriting unclear",
]


def load_config():
    cfg = {
        "telegram_token": "",
        "teacher_password": "changeme",
        "port": 8080,
        "min_photo_width": 800,
        # messages the system sends on its own - off until you turn it on
        "automation": False,
        # hourly chasing in the run-up to a deadline
        "chase_hours": 6,        # start this many hours before the deadline
        "chase_threshold": 80,   # only chase students below this percent done
        "chase_max": 5,          # never send more than this many per deadline

        "timezone_offset_hours": 5,  # Tashkent
    }
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as fh:
            cfg.update(json.load(fh))
    # environment always wins, so deploys never need the file
    if os.environ.get("TELEGRAM_TOKEN"):
        cfg["telegram_token"] = os.environ["TELEGRAM_TOKEN"]
    if os.environ.get("TEACHER_PASSWORD"):
        cfg["teacher_password"] = os.environ["TEACHER_PASSWORD"]
    if os.environ.get("PORT"):
        cfg["port"] = int(os.environ["PORT"])
    return cfg


def now():
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.replace(microsecond=0).isoformat()


def parse(ts):
    if not ts:
        return None
    return datetime.fromisoformat(ts)


def local_day(dt, cfg):
    """Date string in the teacher's timezone, for grouping by day."""
    return (dt + timedelta(hours=cfg["timezone_offset_hours"])).strftime("%Y-%m-%d")


def connect():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=30)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    return db


SCHEMA = """
CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    join_code TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    archived INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY,
    telegram_id INTEGER UNIQUE,
    name TEXT NOT NULL,
    group_id INTEGER REFERENCES groups(id),
    lang TEXT NOT NULL DEFAULT 'en',
    created_at TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id),
    title TEXT NOT NULL,
    task_type TEXT NOT NULL DEFAULT 'task2',
    due_at TEXT,
    created_at TEXT NOT NULL,
    closed INTEGER NOT NULL DEFAULT 0,
    published INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id),
    assignment_id INTEGER REFERENCES assignments(id),
    created_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    score REAL,
    note TEXT,
    graded_at TEXT,
    media_group_id TEXT
);

CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY,
    submission_id INTEGER NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    telegram_file_id TEXT,
    width INTEGER,
    height INTEGER,
    ord INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY,
    label TEXT NOT NULL UNIQUE,
    sort INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS submission_tags (
    submission_id INTEGER NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id),
    PRIMARY KEY (submission_id, tag_id)
);

CREATE TABLE IF NOT EXISTS bot_state (
    telegram_id INTEGER PRIMARY KEY,
    step TEXT,
    payload TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS word_lists (
    id INTEGER PRIMARY KEY,
    group_id INTEGER REFERENCES groups(id),
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS words (
    id INTEGER PRIMARY KEY,
    list_id INTEGER NOT NULL REFERENCES word_lists(id) ON DELETE CASCADE,
    term TEXT NOT NULL,
    translation TEXT NOT NULL,
    ord INTEGER NOT NULL DEFAULT 0
);

-- one row per student per word: what drives spaced repetition
CREATE TABLE IF NOT EXISTS word_progress (
    student_id INTEGER NOT NULL REFERENCES students(id),
    word_id INTEGER NOT NULL REFERENCES words(id) ON DELETE CASCADE,
    seen INTEGER NOT NULL DEFAULT 0,
    correct INTEGER NOT NULL DEFAULT 0,
    streak INTEGER NOT NULL DEFAULT 0,
    next_due TEXT,
    last_seen TEXT,
    PRIMARY KEY (student_id, word_id)
);

CREATE TABLE IF NOT EXISTS quiz_sessions (
    id INTEGER PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id),
    list_id INTEGER REFERENCES word_lists(id),
    started_at TEXT NOT NULL,
    finished_at TEXT,
    asked INTEGER NOT NULL DEFAULT 0,
    correct INTEGER NOT NULL DEFAULT 0
);

-- one row per message the system has sent by itself, so a restart or a second
-- pass through the scheduler can never send the same reminder twice
CREATE TABLE IF NOT EXISTS notifications (
    kind TEXT NOT NULL,
    key TEXT NOT NULL,
    sent_at TEXT NOT NULL,
    PRIMARY KEY (kind, key)
);

CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT);

CREATE INDEX IF NOT EXISTS idx_sub_student ON submissions(student_id);
CREATE INDEX IF NOT EXISTS idx_sub_assignment ON submissions(assignment_id);
CREATE INDEX IF NOT EXISTS idx_sub_status ON submissions(status);
CREATE INDEX IF NOT EXISTS idx_files_sub ON files(submission_id);
CREATE INDEX IF NOT EXISTS idx_words_list ON words(list_id);
CREATE INDEX IF NOT EXISTS idx_wp_student ON word_progress(student_id);
CREATE INDEX IF NOT EXISTS idx_quiz_student ON quiz_sessions(student_id);
"""


def migrate(db):
    """Additive migrations so an existing database keeps its data."""
    cols = {r["name"] for r in db.execute("PRAGMA table_info(students)")}
    if "token" not in cols:
        db.execute("ALTER TABLE students ADD COLUMN token TEXT")
    acols = {r["name"] for r in db.execute("PRAGMA table_info(assignments)")}
    if "published" not in acols:
        # assignments that already existed were live, so they stay live
        db.execute("ALTER TABLE assignments ADD COLUMN published INTEGER NOT NULL DEFAULT 0")
        db.execute("UPDATE assignments SET published=1")
    db.commit()


def student_token(db, student_id):
    """Stable secret link for a student; created on first use."""
    row = db.execute("SELECT token FROM students WHERE id=?", (student_id,)).fetchone()
    if row and row["token"]:
        return row["token"]
    token = secrets.token_urlsafe(16)
    db.execute("UPDATE students SET token=? WHERE id=?", (token, student_id))
    db.commit()
    return token


def student_by_token(db, token):
    if not token or len(token) < 16:
        return None
    return db.execute(
        "SELECT * FROM students WHERE token=? AND active=1", (token,)
    ).fetchone()


def init_db():
    db = connect()
    db.executescript(SCHEMA)
    migrate(db)
    for i, label in enumerate(DEFAULT_TAGS):
        db.execute(
            "INSERT OR IGNORE INTO tags (label, sort) VALUES (?, ?)", (label, i)
        )
    db.commit()
    return db


def new_join_code(db):
    while True:
        code = "".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(6))
        if not db.execute("SELECT 1 FROM groups WHERE join_code=?", (code,)).fetchone():
            return code


# ---------------------------------------------------------------- analytics

def rolling_average(values, window=3):
    """Rolling mean over the last `window` non-null values, aligned to input."""
    out, buf = [], []
    for v in values:
        if v is None:
            out.append(None)
            continue
        buf.append(v)
        if len(buf) > window:
            buf.pop(0)
        out.append(round(sum(buf) / len(buf), 2))
    return out


def student_timeline(db, student_id):
    """Every assignment for the student's group, in order, with score or a miss.

    A missing submission is never scored zero - it is reported as a gap so the
    score trend measures ability and the completion rate measures discipline.
    """
    row = db.execute("SELECT group_id FROM students WHERE id=?", (student_id,)).fetchone()
    if not row or row["group_id"] is None:
        return []
    assignments = db.execute(
        "SELECT id, title, created_at, due_at FROM assignments"
        " WHERE group_id=? ORDER BY COALESCE(due_at, created_at), id",
        (row["group_id"],),
    ).fetchall()
    subs = {
        s["assignment_id"]: s
        for s in db.execute(
            "SELECT * FROM submissions WHERE student_id=? AND assignment_id IS NOT NULL"
            " ORDER BY created_at",
            (student_id,),
        ).fetchall()
    }
    timeline = []
    for a in assignments:
        s = subs.get(a["id"])
        timeline.append(
            {
                "assignment_id": a["id"],
                "title": a["title"],
                "due_at": a["due_at"],
                "submission_id": s["id"] if s else None,
                "status": (s["status"] if s else "missing"),
                "score": (s["score"] if s and s["status"] == "graded" else None),
            }
        )
    return timeline


def student_stats(db, student_id):
    tl = student_timeline(db, student_id)
    graded = [t["score"] for t in tl if t["score"] is not None]
    due_passed = [t for t in tl if _is_past(t["due_at"])]
    missed = [t for t in due_passed if t["status"] == "missing"]
    completion = (
        round(100 * (len(due_passed) - len(missed)) / len(due_passed))
        if due_passed
        else None
    )
    trend = None
    if len(graded) >= 4:
        half = len(graded) // 2
        trend = round(
            sum(graded[half:]) / len(graded[half:]) - sum(graded[:half]) / len(graded[:half]), 2
        )
    consecutive_misses = 0
    for t in reversed(due_passed):
        if t["status"] == "missing":
            consecutive_misses += 1
        else:
            break
    return {
        "timeline": tl,
        "average": round(sum(graded) / len(graded), 2) if graded else None,
        "last3": round(sum(graded[-3:]) / len(graded[-3:]), 2) if graded else None,
        "graded_count": len(graded),
        "completion": completion,
        "missed": len(missed),
        "trend": trend,
        "consecutive_misses": consecutive_misses,
        "at_risk": consecutive_misses >= 2 or (trend is not None and trend <= -1.0),
    }


def _is_past(due_at):
    d = parse(due_at)
    return d is not None and d < now()


# ------------------------------------------------------- vocabulary practice

# Days until a word comes back, indexed by how many times it has been answered
# correctly in a row. A wrong answer resets the streak to zero, so a word the
# student keeps missing keeps returning the next day.
INTERVALS = [1, 2, 4, 8, 16, 32, 64]
QUIZ_LENGTH = 10


def meta_get(db, key, default=None):
    r = db.execute("SELECT v FROM meta WHERE k=?", (key,)).fetchone()
    return r["v"] if r else default


def meta_set(db, key, value):
    db.execute(
        "INSERT INTO meta (k, v) VALUES (?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",
        (key, value),
    )
    db.commit()


def lists_for_student(db, student_id):
    r = db.execute("SELECT group_id FROM students WHERE id=?", (student_id,)).fetchone()
    if not r or r["group_id"] is None:
        return []
    return db.execute(
        "SELECT wl.* FROM word_lists wl WHERE wl.active=1 AND"
        " (wl.group_id IS NULL OR wl.group_id=?)"
        " AND EXISTS (SELECT 1 FROM words w WHERE w.list_id=wl.id)"
        " ORDER BY wl.created_at DESC",
        (r["group_id"],),
    ).fetchall()


def pick_quiz_words(db, student_id, list_id, count=QUIZ_LENGTH):
    """Words due for review first, then ones never seen, then anything else."""
    rows = db.execute(
        "SELECT w.*, p.next_due, p.seen FROM words w"
        " LEFT JOIN word_progress p ON p.word_id=w.id AND p.student_id=?"
        " WHERE w.list_id=?",
        (student_id, list_id),
    ).fetchall()
    stamp = iso(now())
    due = [w for w in rows if w["next_due"] and w["next_due"] <= stamp]
    fresh = [w for w in rows if not w["seen"]]
    rest = [w for w in rows if w not in due and w not in fresh]
    import random

    random.shuffle(due)
    random.shuffle(fresh)
    random.shuffle(rest)
    return (due + fresh + rest)[:count]


def quiz_options(db, list_id, correct_word, n=4):
    """The right answer plus distractors drawn from the same list."""
    import random

    others = db.execute(
        "SELECT * FROM words WHERE list_id=? AND id!=? ORDER BY RANDOM() LIMIT ?",
        (list_id, correct_word["id"], n - 1),
    ).fetchall()
    opts = list(others) + [correct_word]
    random.shuffle(opts)
    return opts


def record_answer(db, student_id, word_id, was_correct):
    row = db.execute(
        "SELECT * FROM word_progress WHERE student_id=? AND word_id=?",
        (student_id, word_id),
    ).fetchone()
    seen = (row["seen"] if row else 0) + 1
    correct = (row["correct"] if row else 0) + (1 if was_correct else 0)
    streak = ((row["streak"] if row else 0) + 1) if was_correct else 0
    days = INTERVALS[min(streak, len(INTERVALS) - 1)] if was_correct else 1
    db.execute(
        "INSERT INTO word_progress (student_id, word_id, seen, correct, streak,"
        " next_due, last_seen) VALUES (?,?,?,?,?,?,?)"
        " ON CONFLICT(student_id, word_id) DO UPDATE SET seen=excluded.seen,"
        " correct=excluded.correct, streak=excluded.streak,"
        " next_due=excluded.next_due, last_seen=excluded.last_seen",
        (student_id, word_id, seen, correct, streak,
         iso(now() + timedelta(days=days)), iso(now())),
    )
    db.commit()


def vocab_stats(db, student_id):
    """A word counts as known once it has been recalled 3 times in a row."""
    rows = db.execute(
        "SELECT p.streak, p.seen, p.correct FROM word_progress p"
        " JOIN words w ON w.id=p.word_id WHERE p.student_id=?",
        (student_id,),
    ).fetchall()
    total_words = db.execute(
        "SELECT COUNT(*) c FROM words w JOIN word_lists wl ON wl.id=w.list_id"
        " WHERE wl.active=1 AND (wl.group_id IS NULL OR wl.group_id="
        " (SELECT group_id FROM students WHERE id=?))",
        (student_id,),
    ).fetchone()["c"]
    known = sum(1 for r in rows if r["streak"] >= 3)
    seen = sum(r["seen"] for r in rows)
    right = sum(r["correct"] for r in rows)
    due = db.execute(
        "SELECT COUNT(*) c FROM word_progress WHERE student_id=? AND next_due<=?",
        (student_id, iso(now())),
    ).fetchone()["c"]
    return {
        "total": total_words,
        "practised": len(rows),
        "known": known,
        "accuracy": round(100 * right / seen) if seen else None,
        "due": due,
        "mastery": round(100 * known / total_words) if total_words else None,
    }


def already_sent(db, kind, key):
    return db.execute(
        "SELECT 1 FROM notifications WHERE kind=? AND key=?", (kind, str(key))
    ).fetchone() is not None


def mark_sent(db, kind, key):
    db.execute(
        "INSERT OR IGNORE INTO notifications (kind, key, sent_at) VALUES (?,?,?)",
        (kind, str(key), iso(now())),
    )
    db.commit()


# ------------------------------------------------------- homework sets

def homework_items(db, group_id, due_at):
    """The items a teacher posted together: same group, same deadline."""
    if due_at is None:
        return db.execute(
            "SELECT * FROM assignments WHERE group_id=? AND published=1 AND closed=0"
            " AND due_at IS NULL ORDER BY id", (group_id,)
        ).fetchall()
    return db.execute(
        "SELECT * FROM assignments WHERE group_id=? AND published=1 AND closed=0"
        " AND due_at=? ORDER BY id", (group_id, due_at)
    ).fetchall()


def open_sets(db, group_id):
    """Open homework grouped by deadline, soonest first."""
    rows = db.execute(
        "SELECT DISTINCT due_at FROM assignments WHERE group_id=? AND published=1"
        " AND closed=0 ORDER BY due_at IS NULL, due_at", (group_id,)
    ).fetchall()
    return [(r["due_at"], homework_items(db, group_id, r["due_at"])) for r in rows]


def set_progress(db, student_id, items):
    """Which items of a set this student has sent something for."""
    if not items:
        return {"done": 0, "total": 0, "percent": None, "remaining": [], "done_ids": set()}
    ids = [a["id"] for a in items]
    rows = db.execute(
        "SELECT DISTINCT assignment_id FROM submissions WHERE student_id=?"
        " AND assignment_id IN (%s)" % ",".join("?" * len(ids)),
        [student_id] + ids,
    ).fetchall()
    done_ids = {r["assignment_id"] for r in rows}
    remaining = [a for a in items if a["id"] not in done_ids]
    return {
        "done": len(done_ids),
        "total": len(items),
        "percent": round(100 * len(done_ids) / len(items)),
        "remaining": remaining,
        "done_ids": done_ids,
    }


def group_set_progress(db, group_id, items):
    """Every active student's progress on one homework set, worst first."""
    out = []
    for st in db.execute(
        "SELECT * FROM students WHERE group_id=? AND active=1 ORDER BY name", (group_id,)
    ).fetchall():
        p = set_progress(db, st["id"], items)
        out.append({"student": st, **p})
    out.sort(key=lambda r: (r["percent"] if r["percent"] is not None else 0, r["student"]["name"]))
    return out
