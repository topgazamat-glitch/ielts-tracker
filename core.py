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
MATERIAL_DIR = os.path.join(DATA_DIR, "materials")
DB_PATH = os.path.join(DATA_DIR, "app.db")
CONFIG_PATH = os.path.join(ROOT, "config.json")

LEVELS = ["Beginner", "Elementary", "Pre-Intermediate", "Intermediate",
          "IELTS Novice", "IELTS Standard"]

# Materials are filed twice over: which collection, then which shelf inside it.
COLLECTIONS = {
    "empower": ("Empower materials",
                ["Unit handouts", "Listening audios", "Reading plus",
                 "Academic skills", "Unit vocabularies"]),
    "selfstudy": ("Self-Study",
                  ["Reading", "Listening", "Vocabulary", "Grammar", "Writing"]),
}
COLLECTION_ORDER = ["empower", "selfstudy"]

# every section name, used when validating an upload
CATEGORIES = [c for key in COLLECTION_ORDER for c in COLLECTIONS[key][1]]


def sections(collection):
    return COLLECTIONS.get(collection, COLLECTIONS["selfstudy"])[1]


def collection_label(collection):
    return COLLECTIONS.get(collection, COLLECTIONS["selfstudy"])[0]

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
    # environment always wins, so a hosted deploy never needs the file
    def env(name, key, cast=str):
        raw = os.environ.get(name)
        if raw is None or raw == "":
            return
        if cast is bool:
            cfg[key] = raw.strip().lower() in ("1", "true", "yes", "on")
        else:
            try:
                cfg[key] = cast(raw)
            except ValueError:
                pass

    env("TELEGRAM_TOKEN", "telegram_token")
    env("TEACHER_PASSWORD", "teacher_password")
    env("PORT", "port", int)
    env("AUTOMATION", "automation", bool)
    env("TIMEZONE_OFFSET_HOURS", "timezone_offset_hours", int)
    env("MIN_PHOTO_WIDTH", "min_photo_width", int)
    env("CHASE_HOURS", "chase_hours", int)
    env("CHASE_THRESHOLD", "chase_threshold", int)
    env("CHASE_MAX", "chase_max", int)
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
    os.makedirs(MATERIAL_DIR, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=30)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    return db


SCHEMA = """
CREATE TABLE IF NOT EXISTS levels (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    sort INTEGER NOT NULL DEFAULT 0
);

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
    scols = {r["name"] for r in db.execute("PRAGMA table_info(submissions)")}
    if "late" not in scols:
        db.execute("ALTER TABLE submissions ADD COLUMN late INTEGER NOT NULL DEFAULT 0")
    if "kind" not in scols:
        db.execute("ALTER TABLE submissions ADD COLUMN kind TEXT NOT NULL DEFAULT 'photo'")
    if "improves" not in scols:
        db.execute("ALTER TABLE submissions ADD COLUMN improves INTEGER")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS materials (
        id INTEGER PRIMARY KEY,
        group_id INTEGER REFERENCES groups(id),   -- NULL means every class
        title TEXT NOT NULL,
        note TEXT,
        filename TEXT NOT NULL,
        original_name TEXT,
        mime TEXT,
        size INTEGER,
        telegram_file_id TEXT,                    -- cached after the first send
        created_at TEXT NOT NULL,
        active INTEGER NOT NULL DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY,
        student_id INTEGER NOT NULL REFERENCES students(id),
        text TEXT NOT NULL,
        created_at TEXT NOT NULL,
        answer TEXT,
        answered_at TEXT
    );
    CREATE TABLE IF NOT EXISTS parents (
        id INTEGER PRIMARY KEY,
        student_id INTEGER NOT NULL REFERENCES students(id),
        telegram_id INTEGER UNIQUE,
        token TEXT UNIQUE,
        created_at TEXT NOT NULL
    );
    """)
    wcols = {r["name"] for r in db.execute("PRAGMA table_info(words)")}
    if "example" not in wcols:
        db.execute("ALTER TABLE words ADD COLUMN example TEXT")
    lcols = {r["name"] for r in db.execute("PRAGMA table_info(word_lists)")}
    if "source" not in lcols:
        db.execute("ALTER TABLE word_lists ADD COLUMN source TEXT")
    if "unit" not in lcols:
        db.execute("ALTER TABLE word_lists ADD COLUMN unit TEXT")
    gcols = {r["name"] for r in db.execute("PRAGMA table_info(groups)")}
    if "level_id" not in gcols:
        db.execute("ALTER TABLE groups ADD COLUMN level_id INTEGER REFERENCES levels(id)")
    mcols = {r["name"] for r in db.execute("PRAGMA table_info(materials)")}
    if mcols and "level_id" not in mcols:
        db.execute("ALTER TABLE materials ADD COLUMN level_id INTEGER REFERENCES levels(id)")
    if mcols and "category" not in mcols:
        db.execute("ALTER TABLE materials ADD COLUMN category TEXT")
    if mcols and "collection" not in mcols:
        # anything filed before collections existed used the Self-Study names
        db.execute("ALTER TABLE materials ADD COLUMN collection TEXT")
        db.execute("UPDATE materials SET collection='selfstudy' WHERE collection IS NULL")
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
    for i, name in enumerate(LEVELS):
        db.execute("INSERT OR IGNORE INTO levels (name, sort) VALUES (?,?)", (name, i))
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


# ------------------------------------------------------------ ratings

def streak(db, student_id):
    """Consecutive past assignments submitted, counting back from the newest."""
    n = 0
    for row in reversed(student_timeline(db, student_id)):
        if not _is_past(row["due_at"]):
            continue
        if row["submission_id"]:
            n += 1
        else:
            break
    return n


def live_completion(db, student_id):
    """Share of ALL set homework handed in, including work not yet due.

    student_stats["completion"] only counts past deadlines - right for judging
    who is falling behind, wrong for a live table, where a student should be
    able to climb by doing today's homework today.
    """
    row = db.execute("SELECT group_id FROM students WHERE id=?", (student_id,)).fetchone()
    if not row or row["group_id"] is None:
        return None
    total = db.execute(
        "SELECT COUNT(*) c FROM assignments WHERE group_id=? AND published=1",
        (row["group_id"],),
    ).fetchone()["c"]
    if not total:
        return None
    done = db.execute(
        "SELECT COUNT(DISTINCT assignment_id) c FROM submissions WHERE student_id=?"
        " AND assignment_id IS NOT NULL",
        (student_id,),
    ).fetchone()["c"]
    return round(100 * min(done, total) / total)


def rating_rows(db, group_id=None):
    """Live standings: completion, average score and streak, best first.

    Completion is ranked before score on purpose - it is the part a student
    fully controls, so the table rewards effort rather than raw ability.
    """
    where = "WHERE active=1" + (" AND group_id=?" if group_id else "")
    args = (group_id,) if group_id else ()
    rows = []
    for st in db.execute(f"SELECT * FROM students {where}", args).fetchall():
        stats = student_stats(db, st["id"])
        v = vocab_stats(db, st["id"])
        rows.append({
            "student": st,
            "completion": live_completion(db, st["id"]),
            "due_completion": stats["completion"],
            "average": stats["average"],
            "graded": stats["graded_count"],
            "missed": stats["missed"],
            "streak": streak(db, st["id"]),
            "vocab": v["known"],
            "at_risk": stats["at_risk"],
        })
    rows.sort(key=lambda r: (-(r["completion"] or 0), -(r["average"] or 0),
                             r["student"]["name"]))
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    return rows


def parent_token(db, student_id):
    row = db.execute("SELECT token FROM parents WHERE student_id=? AND telegram_id IS NULL",
                     (student_id,)).fetchone()
    if row:
        return row["token"]
    token = secrets.token_urlsafe(9)
    db.execute("INSERT INTO parents (student_id, token, created_at) VALUES (?,?,?)",
               (student_id, token, iso(now())))
    db.commit()
    return token


def due_in_words(due_at):
    """'in 6 hours' / 'tomorrow' / 'overdue' - for student-facing countdowns."""
    d = parse(due_at)
    if not d:
        return ""
    delta = d - now()
    hours = delta.total_seconds() / 3600
    if hours < 0:
        return "overdue"
    if hours < 1:
        return "under an hour left"
    if hours < 24:
        return "%d hours left" % int(hours)
    return "%d days left" % round(hours / 24)


# --------------------------------------------------------- quiz modes

QUIZ_MODES = {
    "m2w": "Meaning to word",       # shows the meaning, pick the English word
    "w2m": "Word to meaning",       # shows the word, pick the meaning
    "type": "Spell it",             # shows the meaning, type the word
    "gap": "Fill the gap",          # example sentence with the word removed
    "mix": "Mixed",                 # a bit of everything, hardest last
}
QUIZ_LENGTHS = (5, 10, 20)


def gap_sentence(word):
    """The example with the word blanked out, or None if it cannot be made."""
    example = word["example"] if "example" in word.keys() else None
    if not example:
        return None
    term = word["term"].strip()
    low, lowterm = example.lower(), term.lower()
    i = low.find(lowterm)
    if i < 0:
        return None
    return example[:i] + "_" * max(4, len(term)) + example[i + len(term):]


def pick_mode(mode, word, streak):
    """For 'mix', choose a mode that suits how well the word is known."""
    if mode != "mix":
        if mode == "gap" and gap_sentence(word) is None:
            return "m2w"
        return mode
    if streak >= 3 and gap_sentence(word) is not None:
        return "gap"
    if streak >= 2:
        return "type"
    if streak >= 1:
        return "w2m"
    return "m2w"


def scope_words(db, student_id, list_id, scope, count):
    """scope: 'due' (review), 'new' (never seen) or 'all'."""
    rows = db.execute(
        "SELECT w.*, p.next_due, p.seen, p.streak FROM words w"
        " LEFT JOIN word_progress p ON p.word_id=w.id AND p.student_id=?"
        " WHERE w.list_id=?", (student_id, list_id)
    ).fetchall()
    stamp = iso(now())
    import random
    if scope == "due":
        pool = [w for w in rows if w["next_due"] and w["next_due"] <= stamp]
    elif scope == "new":
        pool = [w for w in rows if not w["seen"]]
    else:
        pool = list(rows)
    if not pool:
        pool = list(rows)
    random.shuffle(pool)
    return pool[:count]


# ------------------------------------------------------------- materials

def level_of(db, group_id):
    row = db.execute("SELECT level_id FROM groups WHERE id=?", (group_id,)).fetchone()
    return row["level_id"] if row else None


def level_name(db, level_id):
    if not level_id:
        return None
    row = db.execute("SELECT name FROM levels WHERE id=?", (level_id,)).fetchone()
    return row["name"] if row else None


def materials_at_level(db, level_id, collection=None, category=None):
    """Everything on one level's shelf, regardless of which class is asking."""
    sql = "SELECT * FROM materials WHERE active=1 AND (level_id IS NULL OR level_id IS ?)"
    args = [level_id]
    if collection:
        sql += " AND collection=?"
        args.append(collection)
    if category:
        sql += " AND category=?"
        args.append(category)
    return db.execute(sql + " ORDER BY created_at DESC", args).fetchall()


def level_counts(db, level_id, collection):
    counts = {}
    for m in materials_at_level(db, level_id, collection):
        key = m["category"] or sections(collection)[0]
        counts[key] = counts.get(key, 0) + 1
    return counts


def collection_counts(db, level_id):
    return {key: len(materials_at_level(db, level_id, key)) for key in COLLECTION_ORDER}


def materials_for(db, group_id, category=None):
    """What one class can see: their level's shelf, plus anything shared with all.

    A material aimed at a level reaches every class at that level; one aimed at a
    single class reaches only that class; one with neither reaches everybody.
    """
    level_id = level_of(db, group_id)
    sql = ("SELECT * FROM materials WHERE active=1"
           " AND (group_id IS NULL OR group_id=?)"
           " AND (level_id IS NULL OR level_id IS ?)")
    args = [group_id, level_id]
    if category:
        sql += " AND category=?"
        args.append(category)
    sql += " ORDER BY category, created_at DESC"
    return db.execute(sql, args).fetchall()


def material_counts(db, group_id):
    """How many files sit on each shelf, so empty ones can be hidden."""
    counts = {c: 0 for c in CATEGORIES}
    for m in materials_for(db, group_id):
        counts[m["category"] or "Reading"] = counts.get(m["category"] or "Reading", 0) + 1
    return counts


def groups_at_level(db, level_id):
    return db.execute(
        "SELECT * FROM groups WHERE archived=0 AND level_id=? ORDER BY name", (level_id,)
    ).fetchall()


def human_size(n):
    if not n:
        return ""
    for unit in ("B", "KB", "MB"):
        if n < 1024 or unit == "MB":
            return ("%.0f %s" if unit == "B" else "%.1f %s") % (n, unit)
        n /= 1024.0
