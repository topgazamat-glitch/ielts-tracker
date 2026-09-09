"""Shared config, database access and domain logic."""
import hashlib
import json
import os
import random
import sqlite3
import secrets
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
# DATA_DIR is overridable so a host can point it at a disk that survives
# redeploys - everything that must persist (database + photos) lives here.
DATA_DIR = os.environ.get("DATA_DIR") or os.path.join(ROOT, "data")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
MATERIAL_DIR = os.path.join(DATA_DIR, "materials")
MUSIC_DIR = os.path.join(DATA_DIR, "music")
DB_PATH = os.path.join(DATA_DIR, "app.db")
CONFIG_PATH = os.path.join(ROOT, "config.json")

LEVELS = ["Beginner", "Elementary", "Pre-Intermediate", "Intermediate",
          "IELTS Novice", "IELTS Standard"]

# Materials are filed twice over: which collection, then which shelf inside it.
COLLECTIONS = {
    "empower": ("Empower materials",
                ["Unit handouts", "Listening audios", "Workbook audios",
                 "Reading plus", "Academic skills", "Unit vocabularies",
                 "Unit tests"]),
    "selfstudy": ("Self-Study",
                  ["Reading", "Listening", "Vocabulary", "Grammar", "Writing"]),
    "practice": ("Practice tests",
                 ["Paper", "Audio", "Answer key"]),
}
COLLECTION_ORDER = ["empower", "selfstudy", "practice"]

# The practice shelf is numbered by test, not by coursebook unit, and a student
# wants one test with everything in it rather than three lists to cross-refer.
# So its tiles are the twenty tests, and the sections above become labels on the
# files inside each one.
TEST_COLLECTIONS = {"practice": 20}


def is_test_shelf(collection):
    return collection in TEST_COLLECTIONS


def tests_in_collection(collection):
    return list(range(1, TEST_COLLECTIONS.get(collection, 0) + 1))


def unit_word(collection):
    return "Test" if is_test_shelf(collection) else "Unit"


def has_units(collection):
    return True

# a material may also carry a unit number and which book it belongs to
BOOKS = {"class": "Class book", "work": "Work book"}
BOOK_ORDER = ["class", "work"]
UNITS = list(range(1, 13))

# how many units each level's coursebook has
LEVEL_UNIT_COUNT = {"Intermediate": 10}
DEFAULT_UNIT_COUNT = 12


def units_for_level(db, level_id, collection=None):
    """The numbers to offer - twenty tests on the practice shelf, else units."""
    if collection and is_test_shelf(collection):
        return tests_in_collection(collection)
    name = level_name(db, level_id)
    return list(range(1, LEVEL_UNIT_COUNT.get(name, DEFAULT_UNIT_COUNT) + 1))


def units_across(db, level_id, collection):
    """Every test number that has a file, whatever kind it is."""
    rows = db.execute(
        "SELECT unit, COUNT(*) c FROM materials WHERE active=1 AND collection=?"
        " AND unit IS NOT NULL AND (level_id IS NULL OR level_id IS ?)"
        " GROUP BY unit ORDER BY unit", (collection, level_id)).fetchall()
    return {r["unit"]: r["c"] for r in rows}


def files_in_test(db, level_id, collection, unit):
    return db.execute(
        "SELECT * FROM materials WHERE active=1 AND collection=? AND unit=?"
        " AND (level_id IS NULL OR level_id IS ?) ORDER BY category, title",
        (collection, unit, level_id)).fetchall()

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
        "draft_hours": 2,        # send an unfinished draft after this long
        "late_window_hours": 0,  # how long past a deadline students may still send

        "timezone_offset_hours": 5,  # Tashkent
    }
    # config.json lives beside the source, but a run pointed at its own data
    # directory is a copy - a test, a spare checkout - and must not inherit the
    # real bot token from it. Two programs polling one Telegram account both
    # receive every message and both answer it, which is how a bot ends up
    # saying everything twice. A hosted deploy passes its token in the
    # environment below, so it is unaffected.
    own_data = os.environ.get("DATA_DIR")
    path = os.path.join(own_data, "config.json") if own_data else CONFIG_PATH
    if os.path.exists(path):
        with open(path) as fh:
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
    env("PHOTO_KEEP_DAYS", "photo_keep_days", int)
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
    os.makedirs(MUSIC_DIR, exist_ok=True)
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
    if "photo" not in cols:
        db.execute("ALTER TABLE students ADD COLUMN photo TEXT")
    if "avatar" not in cols:
        db.execute("ALTER TABLE students ADD COLUMN avatar TEXT")
    if "phone" not in cols:
        db.execute("ALTER TABLE students ADD COLUMN phone TEXT")
    if "about" not in cols:
        db.execute("ALTER TABLE students ADD COLUMN about TEXT")
    # where they say they started and where they are heading, out of ten
    if "journey_from" not in cols:
        db.execute("ALTER TABLE students ADD COLUMN journey_from REAL")
    if "journey_to" not in cols:
        db.execute("ALTER TABLE students ADD COLUMN journey_to REAL")
    if "journey_at" not in cols:
        db.execute("ALTER TABLE students ADD COLUMN journey_at TEXT")
    # the climb: which camp they set out from and which one they are heading for
    if "climb_from" not in cols:
        db.execute("ALTER TABLE students ADD COLUMN climb_from TEXT")
    if "climb_to" not in cols:
        db.execute("ALTER TABLE students ADD COLUMN climb_to TEXT")
    fcols = {r["name"] for r in db.execute("PRAGMA table_info(files)")}
    if "preview" not in fcols:
        # a screen-sized copy, so grading does not pull the full page shot
        db.execute("ALTER TABLE files ADD COLUMN preview TEXT")
    if "preview_id" not in fcols:
        # Telegram's id for the screen-sized copy; fetched when first needed
        db.execute("ALTER TABLE files ADD COLUMN preview_id TEXT")
    if "offloaded" not in fcols:
        # 1 = the big file has been deleted from disk; Telegram still has it
        db.execute("ALTER TABLE files ADD COLUMN offloaded INTEGER NOT NULL DEFAULT 0")
    acols = {r["name"] for r in db.execute("PRAGMA table_info(assignments)")}
    if "rubric" not in acols:
        # marked on the four criteria rather than one number
        db.execute("ALTER TABLE assignments ADD COLUMN rubric INTEGER NOT NULL DEFAULT 0")
    scols = {r["name"] for r in db.execute("PRAGMA table_info(submissions)")}
    if "late" not in scols:
        db.execute("ALTER TABLE submissions ADD COLUMN late INTEGER NOT NULL DEFAULT 0")
    if "kind" not in scols:
        db.execute("ALTER TABLE submissions ADD COLUMN kind TEXT NOT NULL DEFAULT 'photo'")
    if "improves" not in scols:
        db.execute("ALTER TABLE submissions ADD COLUMN improves INTEGER")
    if "draft" not in scols:
        # work in progress: pages can still be added, the teacher cannot see it.
        # everything that already existed was already sent, so it stays 0.
        db.execute("ALTER TABLE submissions ADD COLUMN draft INTEGER NOT NULL DEFAULT 0")
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
    CREATE TABLE IF NOT EXISTS goals (
        student_id INTEGER PRIMARY KEY REFERENCES students(id),
        listening REAL, reading REAL, writing REAL, speaking REAL,
        target_date TEXT,
        updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS lesson_marks (
        id INTEGER PRIMARY KEY,
        student_id INTEGER NOT NULL REFERENCES students(id),
        day TEXT NOT NULL,                 -- YYYY-MM-DD, the lesson date
        punctuality INTEGER,               -- 1..5
        behaviour INTEGER,
        participation INTEGER,
        note TEXT,
        created_at TEXT NOT NULL,
        UNIQUE (student_id, day)
    );
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY,
        student_id INTEGER NOT NULL REFERENCES students(id),
        text TEXT NOT NULL,
        created_at TEXT NOT NULL,
        answer TEXT,
        answered_at TEXT
    );
    CREATE TABLE IF NOT EXISTS games (
        id INTEGER PRIMARY KEY,
        group_id INTEGER REFERENCES groups(id),
        list_id INTEGER REFERENCES word_lists(id),
        code TEXT UNIQUE,
        state TEXT NOT NULL DEFAULT 'lobby',   -- lobby | question | reveal | done
        q_index INTEGER NOT NULL DEFAULT -1,
        q_count INTEGER NOT NULL DEFAULT 10,
        seconds INTEGER NOT NULL DEFAULT 20,
        opened_at TEXT,                        -- when the current question went up
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS game_questions (
        id INTEGER PRIMARY KEY,
        game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
        ord INTEGER NOT NULL,
        word_id INTEGER NOT NULL REFERENCES words(id),
        options TEXT NOT NULL,                 -- JSON, four translations
        answer INTEGER NOT NULL                -- which of them is right
    );
    CREATE TABLE IF NOT EXISTS game_players (
        id INTEGER PRIMARY KEY,
        game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
        student_id INTEGER NOT NULL REFERENCES students(id),
        score INTEGER NOT NULL DEFAULT 0,
        correct INTEGER NOT NULL DEFAULT 0,
        run INTEGER NOT NULL DEFAULT 0,        -- correct answers in a row, right now
        prev_rank INTEGER,                     -- where they stood a question ago
        delta INTEGER NOT NULL DEFAULT 0,      -- places gained on the last question
        joined_at TEXT NOT NULL,
        UNIQUE (game_id, student_id)
    );
    CREATE TABLE IF NOT EXISTS game_answers (
        id INTEGER PRIMARY KEY,
        game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
        question_id INTEGER NOT NULL REFERENCES game_questions(id) ON DELETE CASCADE,
        student_id INTEGER NOT NULL REFERENCES students(id),
        choice INTEGER,
        correct INTEGER NOT NULL DEFAULT 0,
        ms INTEGER,
        UNIQUE (game_id, question_id, student_id)
    );
    CREATE TABLE IF NOT EXISTS criteria_scores (
        submission_id INTEGER NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
        key TEXT NOT NULL,
        score REAL NOT NULL,
        PRIMARY KEY (submission_id, key)
    );
    CREATE TABLE IF NOT EXISTS note_templates (
        id INTEGER PRIMARY KEY,
        text TEXT NOT NULL,
        sort INTEGER NOT NULL DEFAULT 0,
        uses INTEGER NOT NULL DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS daily_music (
        id INTEGER PRIMARY KEY,
        day TEXT NOT NULL UNIQUE,          -- YYYY-MM-DD in the teacher's timezone
        title TEXT,
        artist TEXT,
        filename TEXT NOT NULL,
        original_name TEXT,
        mime TEXT NOT NULL,
        bytes INTEGER NOT NULL,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS seasons (
        id INTEGER PRIMARY KEY,
        no INTEGER NOT NULL,
        started_at TEXT NOT NULL,
        closed_at TEXT NOT NULL,
        winner_id INTEGER REFERENCES students(id),
        winner_name TEXT,
        winner_points REAL,
        standing TEXT                      -- the whole table as it stood, as json
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
    if mcols and "unit" not in mcols:
        db.execute("ALTER TABLE materials ADD COLUMN unit INTEGER")
    if mcols and "book" not in mcols:
        db.execute("ALTER TABLE materials ADD COLUMN book TEXT")
    if mcols and "collection" not in mcols:
        # anything filed before collections existed used the Self-Study names
        db.execute("ALTER TABLE materials ADD COLUMN collection TEXT")
        db.execute("UPDATE materials SET collection='selfstudy' WHERE collection IS NULL")
    acols = {r["name"] for r in db.execute("PRAGMA table_info(assignments)")}
    if "published" not in acols:
        # assignments that already existed were live, so they stay live
        db.execute("ALTER TABLE assignments ADD COLUMN published INTEGER NOT NULL DEFAULT 0")
        db.execute("UPDATE assignments SET published=1")
    # the game tables shipped before characters and rank movement did
    gpcols = {r["name"] for r in db.execute("PRAGMA table_info(game_players)")}
    if gpcols:
        if "run" not in gpcols:
            db.execute("ALTER TABLE game_players ADD COLUMN"
                       " run INTEGER NOT NULL DEFAULT 0")
        if "prev_rank" not in gpcols:
            db.execute("ALTER TABLE game_players ADD COLUMN prev_rank INTEGER")
        if "delta" not in gpcols:
            db.execute("ALTER TABLE game_players ADD COLUMN"
                       " delta INTEGER NOT NULL DEFAULT 0")

    # these tables arrived after the first release, so their indexes live here
    db.executescript("""
    CREATE INDEX IF NOT EXISTS idx_sub_queue ON submissions(status, draft, created_at);
    CREATE INDEX IF NOT EXISTS idx_students_group ON students(group_id, active);
    CREATE INDEX IF NOT EXISTS idx_assign_group ON assignments(group_id, closed);
    CREATE INDEX IF NOT EXISTS idx_mat_shelf
        ON materials(level_id, collection, category, unit);
    CREATE INDEX IF NOT EXISTS idx_marks_student ON lesson_marks(student_id, day);
    CREATE INDEX IF NOT EXISTS idx_goals_student ON goals(student_id);
    CREATE INDEX IF NOT EXISTS idx_game_live ON games(group_id, state);
    CREATE INDEX IF NOT EXISTS idx_game_q ON game_questions(game_id, ord);
    CREATE INDEX IF NOT EXISTS idx_game_ans ON game_answers(game_id, question_id);
    """)
    db.commit()


def shift_days(day, n):
    """'2026-09-01' plus n days, as the same kind of string."""
    try:
        d = datetime.strptime(day[:10], "%Y-%m-%d") + timedelta(days=n)
    except (ValueError, TypeError):
        d = now() + timedelta(days=n)
    return d.strftime("%Y-%m-%d")


def last_homework_batch(db, group_id):
    """The most recent set of tasks given to a class, in the order they were set.

    Homework is usually handed out as a list on one day, so 'last week's
    homework' means everything sharing that newest deadline.
    """
    newest = db.execute(
        "SELECT COALESCE(due_at, created_at) k FROM assignments WHERE group_id=?"
        " ORDER BY k DESC LIMIT 1", (group_id,)).fetchone()
    if not newest or not newest["k"]:
        return []
    return db.execute(
        "SELECT * FROM assignments WHERE group_id=?"
        " AND substr(COALESCE(due_at, created_at), 1, 10)=? ORDER BY id",
        (group_id, newest["k"][:10])).fetchall()


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
            " AND draft=0 ORDER BY created_at",
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


# ------------------------------------------------------------ live vocabulary game
#
# A room of phones answering the same question at the same time. There is no
# socket here on purpose: each phone asks "what is on screen now?" once a second
# and gets a few hundred bytes back. On classroom mobile data that beats a live
# connection, because a missed poll simply retries while a dropped socket ends
# the game for that student.

# a character to be, chosen once and kept. Emoji rather than drawings: they
# cost no bandwidth in a classroom, render on every phone in the room, and a
# clean emoji beats homemade artwork.
AVATARS = ["\U0001F98A", "\U0001F43C", "\U0001F981", "\U0001F42F",
           "\U0001F989", "\U0001F438", "\U0001F419", "\U0001F984",
           "\U0001F41D", "\U0001F42C", "\U0001F985", "\U0001F43A"]


def set_avatar(db, student_id, emoji):
    if emoji not in AVATARS:
        return False
    db.execute("UPDATE students SET avatar=? WHERE id=?", (emoji, student_id))
    db.commit()
    return True


def avatar_of(row):
    """Everyone has one, whether or not they have chosen: the fallback is
    steady per student, so the same person is always the same animal.

    Takes a student row, or any row carrying that student's avatar and id.
    """
    def field(name):
        try:
            return row[name]
        except (IndexError, KeyError):
            return None
    seed = field("sid")
    if seed is None:
        seed = field("student_id")
    if seed is None:
        seed = field("id") or 0
    return field("avatar") or AVATARS[seed % len(AVATARS)]


GAME_BASE = 500          # points for being right at all
GAME_SPEED = 500         # the most that answering fast can add
GAME_CODE_CHARS = "ACDEFGHJKLMNPQRTUVWXY3479"   # no O/0, no I/1, no S/5


def game_code(db):
    while True:
        code = "".join(secrets.choice(GAME_CODE_CHARS) for _ in range(5))
        if not db.execute("SELECT 1 FROM games WHERE code=?", (code,)).fetchone():
            return code


def make_game(db, group_id, list_id, q_count=10, seconds=20):
    """Draw the questions up front, so the game cannot stall mid-round.

    Wrong options come from other words on the same list, which makes them
    plausible rather than absurd - a student has to actually know the word.
    """
    words = db.execute(
        "SELECT id, term, translation FROM words WHERE list_id=? ORDER BY id",
        (list_id,)).fetchall()
    if len(words) < 4:
        return None
    picked = list(words)
    random.shuffle(picked)
    picked = picked[:max(1, min(q_count, len(picked)))]

    gid = db.execute(
        "INSERT INTO games (group_id, list_id, code, q_count, seconds, created_at)"
        " VALUES (?,?,?,?,?,?)",
        (group_id, list_id, game_code(db), len(picked), seconds, iso(now()))).lastrowid

    pool = [w["translation"] for w in words]
    for i, w in enumerate(picked):
        others = [t for t in pool if t != w["translation"]]
        random.shuffle(others)
        options = others[:3] + [w["translation"]]
        random.shuffle(options)
        db.execute(
            "INSERT INTO game_questions (game_id, ord, word_id, options, answer)"
            " VALUES (?,?,?,?,?)",
            (gid, i, w["id"], json.dumps(options, ensure_ascii=False),
             options.index(w["translation"])))
    db.commit()
    return gid


def live_game(db, group_id):
    """The game this class is in the middle of, if any."""
    return db.execute(
        "SELECT * FROM games WHERE group_id=? AND state IN ('lobby','question','reveal')"
        " ORDER BY id DESC LIMIT 1", (group_id,)).fetchone()


def game_question(db, game):
    if game["q_index"] < 0:
        return None
    return db.execute("SELECT * FROM game_questions WHERE game_id=? AND ord=?",
                      (game["id"], game["q_index"])).fetchone()


def shuffle_for(student_id, question_id, n=4):
    """A per-student order for the answers, stable across polls.

    Two students side by side see the same four words in different places, so
    copying a neighbour's screen tells you nothing.
    """
    seed = hashlib.sha256(("%d:%d" % (student_id, question_id)).encode()).digest()
    order = list(range(n))
    # Fisher-Yates driven by the digest, so it is the same every time it is asked
    for i in range(n - 1, 0, -1):
        j = seed[i] % (i + 1)
        order[i], order[j] = order[j], order[i]
    return order


def game_seconds_left(game):
    if game["state"] != "question" or not game["opened_at"]:
        return 0
    gone = (now() - parse(game["opened_at"])).total_seconds()
    return max(0, round(game["seconds"] - gone, 1))


def join_game(db, game_id, student_id):
    db.execute("INSERT OR IGNORE INTO game_players (game_id, student_id, joined_at)"
               " VALUES (?,?,?)", (game_id, student_id, iso(now())))
    db.commit()


def answer_game(db, game, student_id, choice):
    """Score one answer. Right and fast beats right and slow; nothing is lost by
    a student whose phone dropped and came back."""
    q = game_question(db, game)
    if not q or game["state"] != "question":
        return None
    if db.execute("SELECT 1 FROM game_answers WHERE game_id=? AND question_id=?"
                  " AND student_id=?", (game["id"], q["id"], student_id)).fetchone():
        return None                                   # one answer per question
    left = game_seconds_left(game)
    if left <= 0:
        return None
    was_right = (choice == q["answer"])
    points = 0
    if was_right:
        points = GAME_BASE + int(GAME_SPEED * (left / float(game["seconds"])))
    db.execute(
        "INSERT INTO game_answers (game_id, question_id, student_id, choice, correct, ms)"
        " VALUES (?,?,?,?,?,?)",
        (game["id"], q["id"], student_id, choice, 1 if was_right else 0,
         int((game["seconds"] - left) * 1000)))
    db.execute("UPDATE game_players SET score=score+?, correct=correct+?,"
               " run=CASE WHEN ? THEN run+1 ELSE 0 END"
               " WHERE game_id=? AND student_id=?",
               (points, 1 if was_right else 0, 1 if was_right else 0,
                game["id"], student_id))
    db.commit()
    record_answer(db, student_id, q["word_id"], was_right)   # feeds the bot's revision
    return {"correct": was_right, "points": points, "answer": q["answer"]}


def game_board(db, game_id, limit=None):
    rows = db.execute(
        "SELECT p.*, s.name, s.avatar FROM game_players p"
        " JOIN students s ON s.id=p.student_id"
        " WHERE p.game_id=? ORDER BY p.score DESC, s.name", (game_id,)).fetchall()
    return rows[:limit] if limit else rows


def advance_game(db, game_id):
    """Lobby -> question -> reveal -> question ... -> done."""
    g = db.execute("SELECT * FROM games WHERE id=?", (game_id,)).fetchone()
    if not g or g["state"] == "done":
        return
    if g["state"] in ("lobby", "reveal"):
        nxt = g["q_index"] + 1
        if nxt >= g["q_count"]:
            db.execute("UPDATE games SET state='done' WHERE id=?", (game_id,))
        else:
            db.execute("UPDATE games SET state='question', q_index=?, opened_at=?"
                       " WHERE id=?", (nxt, iso(now()), game_id))
    else:
        db.execute("UPDATE games SET state='reveal' WHERE id=?", (game_id,))
        _snapshot_ranks(db, game_id)
    db.commit()


def _snapshot_ranks(db, game_id):
    """Who moved, and by how much, on the question just finished."""
    for place, row in enumerate(game_board(db, game_id), 1):
        was = row["prev_rank"]
        db.execute("UPDATE game_players SET delta=?, prev_rank=? WHERE id=?",
                   (0 if was is None else was - place, place, row["id"]))
    db.commit()


def end_game(db, game_id):
    db.execute("UPDATE games SET state='done' WHERE id=?", (game_id,))
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


def still_open(due_at, cfg=None):
    """Is this deadline still accepting work?

    A task whose deadline has passed disappears from the student's list, so a
    new week's homework is never shown next to last week's.
    """
    if not due_at:
        return True
    cfg = cfg or load_config()
    grace = timedelta(hours=cfg.get("late_window_hours", 0))
    end = parse(due_at)
    return end is None or (end + grace) >= now()


def all_sets(db):
    """Every homework batch, newest first, however it was posted.

    A list posted in one go shares a class and a deadline, so that pair is the
    batch - the same grouping the Homework page already uses. One assignment
    posted alone is simply a batch of one.
    """
    rows = db.execute(
        "SELECT group_id, due_at, COUNT(*) n, MIN(published) pub, MAX(published) pubmax,"
        " MIN(closed) shut, MAX(closed) shutmax, MAX(created_at) made"
        " FROM assignments GROUP BY group_id, due_at"
        " ORDER BY MAX(created_at) DESC").fetchall()
    return rows


def set_items(db, group_id, due_at):
    if due_at is None:
        return db.execute(
            "SELECT * FROM assignments WHERE group_id=? AND due_at IS NULL"
            " ORDER BY id", (group_id,)).fetchall()
    return db.execute(
        "SELECT * FROM assignments WHERE group_id=? AND due_at=? ORDER BY id",
        (group_id, due_at)).fetchall()


def set_received(db, group_id, due_at):
    """How many students in the class have sent something for this batch."""
    items = set_items(db, group_id, due_at)
    if not items:
        return 0, 0
    ids = [a["id"] for a in items]
    marks = ",".join("?" * len(ids))
    got = db.execute(
        "SELECT COUNT(DISTINCT student_id) c FROM submissions"
        " WHERE assignment_id IN (%s)" % marks, ids).fetchone()["c"]
    total = db.execute(
        "SELECT COUNT(*) c FROM students WHERE group_id=? AND active=1",
        (group_id,)).fetchone()["c"]
    return got, total


def set_graded_count(db, group_id, due_at):
    """Marked pieces that would lose their link if the batch were deleted."""
    items = set_items(db, group_id, due_at)
    if not items:
        return 0
    ids = [a["id"] for a in items]
    marks = ",".join("?" * len(ids))
    return db.execute(
        "SELECT COUNT(*) c FROM submissions WHERE assignment_id IN (%s)"
        " AND status='graded'" % marks, ids).fetchone()["c"]


def open_sets(db, group_id, for_student=False):
    """Open homework grouped by deadline, soonest first.

    for_student drops anything past its deadline; the teacher keeps seeing
    everything on the dashboard.
    """
    rows = db.execute(
        "SELECT DISTINCT due_at FROM assignments WHERE group_id=? AND published=1"
        " AND closed=0 ORDER BY due_at IS NULL, due_at", (group_id,)
    ).fetchall()
    out = []
    for r in rows:
        if for_student and not still_open(r["due_at"]):
            continue
        out.append((r["due_at"], homework_items(db, group_id, r["due_at"])))
    return out


def last_closed_set(db, group_id, days=10):
    """The most recent homework whose deadline has just gone.

    An empty homework list reads as a broken bot to a student who knows they
    were set something. Being able to say "it closed on Friday" is the
    difference between an explanation and a fault.
    """
    since = iso(now() - timedelta(days=days))
    rows = db.execute(
        "SELECT DISTINCT due_at FROM assignments WHERE group_id=? AND published=1"
        " AND closed=0 AND due_at IS NOT NULL AND due_at >= ?"
        " ORDER BY due_at DESC", (group_id, since)).fetchall()
    for r in rows:
        if not still_open(r["due_at"]):
            return r["due_at"]
    return None


def set_progress(db, student_id, items):
    """Which items of a set this student has sent something for."""
    if not items:
        return {"done": 0, "total": 0, "percent": None, "remaining": [], "done_ids": set()}
    ids = [a["id"] for a in items]
    rows = db.execute(
        "SELECT DISTINCT assignment_id FROM submissions WHERE student_id=? AND draft=0"
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
        " AND assignment_id IS NOT NULL AND draft=0",
        (student_id,),
    ).fetchone()["c"]
    return round(100 * min(done, total) / total)


def improvement(db, student_id, weeks=4):
    """How much a student has gained on their own recent past.

    Compares the average of the last `weeks` against the `weeks` before that.
    This is the one measure a weaker student can top outright, because it asks
    nothing about ability - only about getting better than you were.

    Returns None until there are at least two graded pieces in each window;
    below that the number is noise, not progress.
    """
    now_ = now()
    mid = iso(now_ - timedelta(weeks=weeks))
    start = iso(now_ - timedelta(weeks=weeks * 2))

    def avg(lo, hi):
        r = db.execute(
            "SELECT AVG(score) a, COUNT(*) n FROM submissions WHERE student_id=?"
            " AND status='graded' AND score IS NOT NULL"
            " AND created_at >= ? AND created_at < ?", (student_id, lo, hi)).fetchone()
        return (r["a"], r["n"])

    before, n_before = avg(start, mid)
    after, n_after = avg(mid, iso(now_ + timedelta(days=1)))
    if n_before < 2 or n_after < 2:
        return None
    return round(after - before, 2)


def rating_rows(db, group_id=None):
    """Live standings, best first, on everything a student is judged by.

    Ranked on overall_index rather than homework alone: effort is half of it,
    attainment a quarter, and how they are in the room - punctuality, behaviour,
    participation - the last quarter. All three are things the teacher already
    records, and leaving conduct out meant a student who is never late and always
    speaks up earned nothing for it.
    """
    where = "WHERE active=1" + (" AND group_id=?" if group_id else "")
    args = (group_id,) if group_id else ()
    rows = []
    for st in db.execute(f"SELECT * FROM students {where}", args).fetchall():
        stats = student_stats(db, st["id"])
        v = vocab_stats(db, st["id"])
        marks = mark_stats(db, st["id"])
        completion = live_completion(db, st["id"])
        rows.append({
            "student": st,
            "completion": completion,
            "due_completion": stats["completion"],
            "average": stats["average"],
            "graded": stats["graded_count"],
            "missed": stats["missed"],
            "streak": streak(db, st["id"]),
            "vocab": v["known"],
            "at_risk": stats["at_risk"],
            "marks": marks["overall"],
            "lessons": marks["lessons"],
            "index": overall_index(completion, stats["average"], marks["overall"]),
            "gain": improvement(db, st["id"]),
        })
    rows.sort(key=lambda r: (-(r["index"] or 0), -(r["completion"] or 0),
                             -(r["average"] or 0), r["student"]["name"]))
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    return rows


# Quotes for the student page. One a day, the same one for everybody, so a
# class can talk about it. Kept short and about work rather than destiny.
QUOTES = [
    ("It always seems impossible until it is done.", "Nelson Mandela"),
    ("The expert in anything was once a beginner.", "Helen Hayes"),
    ("Little by little, a little becomes a lot.", "Tanzanian proverb"),
    ("I have not failed. I have found ten thousand ways that will not work.",
     "Thomas Edison"),
    ("Practice is the hardest part of learning.", "Zeami"),
    ("A river cuts through rock not because of its power, but its persistence.",
     "Jim Watkins"),
    ("The beautiful thing about learning is that nobody can take it from you.",
     "B. B. King"),
    ("Fall seven times, stand up eight.", "Japanese proverb"),
    ("You do not have to be great to start, but you have to start to be great.",
     "Zig Ziglar"),
    ("Knowledge is a treasure, but practice is the key to it.", "Lao Tzu"),
    ("The secret of getting ahead is getting started.", "Mark Twain"),
    ("A year from now you will wish you had started today.", "Karen Lamb"),
    ("Learning another language is like becoming another person.", "Haruki Murakami"),
    ("Small daily improvements are the key to staggering long-term results.",
     "Robin Sharma"),
    ("If you are working on something you care about, you do not have to be pushed.",
     "Steve Jobs"),
    ("Doing your best matters more than being the best.", "Unknown"),
    ("Language is the road map of a culture.", "Rita Mae Brown"),
    ("Mistakes are proof that you are trying.", "Unknown"),
    ("The more you read, the more things you will know.", "Dr. Seuss"),
    ("Slow progress is still progress.", "Unknown"),
    ("Do not wish it were easier; wish you were better.", "Jim Rohn"),
    ("One language sets you in a corridor for life. Two open every door along the way.",
     "Frank Smith"),
    ("Effort only fully releases its reward after a person refuses to quit.",
     "Napoleon Hill"),
    ("Study without desire spoils the memory.", "Leonardo da Vinci"),
    ("What we learn with pleasure we never forget.", "Alfred Mercier"),
    ("Courage is not having the strength to go on; it is going on when you have none.",
     "Theodore Roosevelt"),
    ("There are no shortcuts to any place worth going.", "Beverly Sills"),
    ("Be patient with yourself. Nothing in nature blooms all year.", "Unknown"),
]


# The mountain. Every camp between not speaking English and the top band, in
# the order a student actually passes them. The named levels are the ones this
# school teaches; above them the camps are IELTS bands, because that is what a
# student at that height is aiming at.
CAMPS = [
    ("beginner", "Beginner"),
    ("elementary", "Elementary"),
    ("pre", "Pre-Intermediate"),
    ("inter", "Intermediate"),
    ("upper", "Upper-Intermediate"),
    ("b55", "IELTS 5.5"),
    ("b60", "IELTS 6.0"),
    ("b65", "IELTS 6.5"),
    ("b70", "IELTS 7.0"),
    ("b75", "IELTS 7.5"),
    ("b80", "IELTS 8.0"),
    ("b85", "IELTS 8.5"),
    ("b90", "IELTS 9.0"),
]
CAMP_INDEX = {key: i for i, (key, _label) in enumerate(CAMPS)}
CAMP_LABEL = dict(CAMPS)

# What one camp costs. A piece of homework marked ten out of ten is worth one
# point, a five is worth half, and twenty known words are worth one more. A term
# of steady work is roughly one camp - which is honest: nobody climbs from
# Beginner to band eight in a term, and pretending otherwise helps no one.
CLIMB_PER_CAMP = 25.0


def camp_for_level(name):
    """The camp a class's level corresponds to, for a sensible default."""
    return {"Beginner": "beginner", "Elementary": "elementary",
            "Pre-Intermediate": "pre", "Intermediate": "inter",
            "IELTS Novice": "upper", "IELTS Standard": "b60"}.get(name or "")


def climb_points(db, student_id):
    """Everything they have actually earned towards the next camp."""
    row = db.execute(
        "SELECT COALESCE(SUM(score), 0) / 10.0 pts, COUNT(*) n FROM submissions"
        " WHERE student_id=? AND status='graded' AND score IS NOT NULL",
        (student_id,)).fetchone()
    words = vocab_stats(db, student_id)["known"]
    return round(row["pts"] + words * 0.05, 2), row["n"], words


def climb(db, student_id):
    """Where they are on the mountain, and how they got there.

    The height is earned, never claimed: it comes from marked homework and
    words they have actually held on to. Choosing a distant goal makes the
    climb longer, not the progress smaller.
    """
    s = db.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()
    if not s:
        return None
    try:
        frm, to = s["climb_from"], s["climb_to"]
    except (IndexError, KeyError):
        return None
    if frm not in CAMP_INDEX or to not in CAMP_INDEX:
        return None
    start, goal = CAMP_INDEX[frm], CAMP_INDEX[to]
    if goal <= start:
        return None

    points, graded, words = climb_points(db, student_id)
    camps = goal - start
    climbed = min(points / CLIMB_PER_CAMP, camps)          # never past the summit
    here = start + climbed
    reached = start + int(climbed)
    nxt = min(reached + 1, goal)
    into = (climbed - int(climbed)) if climbed < camps else 1.0
    return {
        "from": frm, "to": to, "start": start, "goal": goal,
        "camps": camps, "climbed": round(climbed, 2), "here": here,
        "percent": round(climbed / camps * 100, 1) if camps else 0,
        "at_label": CAMP_LABEL[CAMPS[reached][0]],
        "next_label": CAMP_LABEL[CAMPS[nxt][0]],
        "into_next": int(round(into * 100)),
        "points": points, "graded": graded, "words": words,
        "to_next": round(max(0.0, (int(climbed) + 1) * CLIMB_PER_CAMP - points), 1),
        "labels": [CAMP_LABEL[CAMPS[i][0]] for i in range(start, goal + 1)],
    }


# --------------------------------------------------------------- championship
#
# A month-long contest across the whole school, with a real prize at the end of
# it. Two rules shape everything here. Every measure is a share of what was
# available to that student, never a raw count, so a class set twelve tasks and
# a class set six can stand in the same table. And most of the weight sits on
# what a student decides to do rather than on how good their English already
# is, because a table that rewards ability hands the prize to the same three
# people every month and everybody else stops reading it.

CHAMPIONSHIP = [
    ("homework", "Homework", 3.0),
    ("vocab", "Words learned", 2.0),
    ("conduct", "In the lesson", 2.0),
]
CHAMPIONSHIP_MAX = sum(w for _k, _l, w in CHAMPIONSHIP)
MIN_GRADED = 3          # fewer than this and one lucky mark decides the month
VOCAB_TARGET = 60       # words for full marks; beyond this it is worth nothing


def deadline_iso(day, clock=None, cfg=None):
    """A deadline typed in Tashkent time, stored as the instant it really is.

    Deadlines used to be written as 23:59 UTC, which is five in the morning
    here - so every one of them fell most of a day later than it read. The time
    is taken as local now and converted, which is what a teacher means when
    they write six o'clock.
    """
    if not day:
        return None
    cfg = cfg or load_config()
    clock = (clock or "").strip() or "23:59"
    try:
        when = datetime.strptime("%s %s" % (day, clock), "%Y-%m-%d %H:%M")
    except ValueError:
        try:
            when = datetime.strptime(day, "%Y-%m-%d").replace(hour=23, minute=59)
        except ValueError:
            return None
    when = when.replace(tzinfo=timezone.utc) - timedelta(
        hours=cfg["timezone_offset_hours"])
    return iso(when)


def deadline_parts(due_at, cfg=None):
    """A stored deadline back as the date and time a teacher would type."""
    cfg = cfg or load_config()
    when = parse(due_at)
    if not when:
        return "", ""
    local = when + timedelta(hours=cfg["timezone_offset_hours"])
    return local.strftime("%Y-%m-%d"), local.strftime("%H:%M")


def month_key(dt=None, cfg=None):
    return local_day(dt or now(), cfg or load_config())[:7]


def month_bounds(month, cfg=None):
    """The UTC instants a local month begins and ends.

    Worth doing properly rather than comparing text: the prize turns on it, and
    an evening submission in Tashkent is already the next day in UTC.
    """
    cfg = cfg or load_config()
    offset = timedelta(hours=cfg["timezone_offset_hours"])
    first = datetime.strptime(month + "-01", "%Y-%m-%d").replace(tzinfo=timezone.utc)
    nxt = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
    return iso(first - offset), iso(nxt - offset)


def previous_month(month):
    first = datetime.strptime(month + "-01", "%Y-%m-%d")
    return (first - timedelta(days=1)).strftime("%Y-%m")


def _avg_between(db, student_id, lo, hi):
    r = db.execute(
        "SELECT AVG(score) a, COUNT(*) n FROM submissions WHERE student_id=?"
        " AND status='graded' AND score IS NOT NULL AND created_at >= ?"
        " AND created_at < ?", (student_id, lo, hi)).fetchone()
    return r["a"], r["n"]


SEASON_LESSONS = 15
SEASON_OPEN = "9999-12-31T00:00:00+00:00"   # a season still running has no end yet


def season_start(db):
    """When the running season began, or None if the league has not started."""
    return meta_get(db, "season_start")


def season_no(db):
    v = meta_get(db, "season_no")
    return int(v) if v and str(v).isdigit() else 1


def start_season(db, when=None):
    meta_set(db, "season_start", iso(when or now()))
    meta_set(db, "season_no", str(season_no(db)))
    clear_pauses(db)


def pause_windows(db):
    """The stretches the league was switched off, as (from, to) instants.

    A pause has to be subtracted rather than simply ignored: homework marked
    during a holiday, lessons taught during it and words learnt during it must
    all stay out of the season, or pausing would quietly reward whoever kept
    working while the table was frozen.
    """
    raw = meta_get(db, "season_pauses")
    out = [tuple(w) for w in json.loads(raw)] if raw else []
    at = meta_get(db, "season_paused_at")
    if at:
        out.append((at, SEASON_OPEN))
    return out


def is_paused(db):
    return bool(meta_get(db, "season_paused_at"))


def pause_season(db, when=None):
    if not is_paused(db):
        meta_set(db, "season_paused_at", iso(when or now()))


def resume_season(db, when=None):
    at = meta_get(db, "season_paused_at")
    if not at:
        return
    raw = meta_get(db, "season_pauses")
    done = json.loads(raw) if raw else []
    done.append([at, iso(when or now())])
    meta_set(db, "season_pauses", json.dumps(done))
    meta_set(db, "season_paused_at", "")


def clear_pauses(db):
    meta_set(db, "season_pauses", "[]")
    meta_set(db, "season_paused_at", "")


def paused_at(stamp, windows):
    """Was this instant inside a pause?"""
    return any(lo <= stamp < hi for lo, hi in windows)


def paused_day(day, windows, cfg):
    """Was this whole teaching day inside a pause?"""
    for lo, hi in windows:
        end = "9999-12-31" if hi == SEASON_OPEN else local_day(parse(hi), cfg)
        if local_day(parse(lo), cfg) <= day < end:
            return True
    return False


def day_start(day, cfg):
    """The UTC instant a local day begins."""
    first = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return iso(first - timedelta(hours=cfg["timezone_offset_hours"]))


def season_window(db, student_id, lo, cfg):
    """One student's slice of the season: it closes on their 15th lesson.

    A season is counted in lessons, not in days, so a class that met thirteen
    times and a class that met twelve are judged over the same amount of
    teaching. Once a student has had their fifteenth recorded lesson their
    season is finished and nothing after it counts, however long the calendar
    takes everybody else.
    """
    lo_day = local_day(parse(lo), cfg)
    windows = pause_windows(db)
    days = [r["day"] for r in db.execute(
        "SELECT day FROM lesson_marks WHERE student_id=? AND day >= ?"
        " ORDER BY day", (student_id, lo_day))
        if not paused_day(r["day"], windows, cfg)]
    if len(days) >= SEASON_LESSONS:
        closed = days[SEASON_LESSONS - 1]
        after = (datetime.strptime(closed, "%Y-%m-%d")
                 + timedelta(days=1)).strftime("%Y-%m-%d")
        return day_start(after, cfg), SEASON_LESSONS, closed
    return SEASON_OPEN, len(days), None


def championship(db, cfg=None):
    """Everyone's standing for the running season, best first."""
    cfg = cfg or load_config()
    lo = season_start(db)
    if not lo:
        return {"started": False, "season": season_no(db), "start": None,
                "rows": [], "eligible": 0, "finished": 0,
                "paused": False, "paused_at": None}

    windows = pause_windows(db)
    rows = []
    for st in db.execute("SELECT * FROM students WHERE active=1 ORDER BY name"):
        hi, lessons, closed = season_window(db, st["id"], lo, cfg)

        # Homework is the average of the marks given, not the number handed in,
        # so two classes set different amounts of work still compare. Anything
        # arriving after its deadline counts as a zero in that average.
        marked = db.execute(
            "SELECT s.score, s.created_at sent, a.due_at due FROM submissions s"
            " LEFT JOIN assignments a ON a.id=s.assignment_id"
            " WHERE s.student_id=? AND s.status='graded' AND s.score IS NOT NULL"
            " AND s.created_at >= ? AND s.created_at < ?", (st["id"], lo, hi)).fetchall()
        counted, late = [], 0
        for r in marked:
            if paused_at(r["sent"], windows):
                continue
            if r["due"] and r["sent"] > r["due"]:
                counted.append(0.0)
                late += 1
            else:
                counted.append(r["score"])
        graded = len(counted)
        parts = {}
        if graded:
            parts["homework"] = sum(counted) / graded / 10.0

        words = sum(1 for r in db.execute(
            "SELECT last_seen FROM word_progress WHERE student_id=? AND streak >= 3"
            " AND last_seen >= ? AND last_seen < ?", (st["id"], lo, hi))
            if not paused_at(r["last_seen"], windows))
        parts["vocab"] = min(1.0, words / float(VOCAB_TARGET))

        scored = [(r["punctuality"] or 0) + (r["behaviour"] or 0)
                  + (r["participation"] or 0) for r in db.execute(
            "SELECT day, punctuality, behaviour, participation FROM lesson_marks"
            " WHERE student_id=? AND day >= ? AND day < ?",
            (st["id"], local_day(parse(lo), cfg), local_day(parse(hi), cfg)))
            if not paused_day(r["day"], windows, cfg)]
        parts["conduct"] = (min(1.0, (sum(scored) / len(scored) / 3.0) / float(MARK_MAX))
                            if scored else 0.0)
        lesson_n = len(scored)

        # no rescaling: the scale is small and fixed, so what is missing shows
        # as a nought rather than quietly inflating everything else
        points = {k: parts.get(k, 0.0) * w for k, _l, w in CHAMPIONSHIP}
        rows.append({
            "student": st, "points": {k: round(v, 2) for k, v in points.items()},
            "total": round(sum(points.values()), 2),
            "graded": graded, "words": words, "late": late,
            "handed": ("%d marked%s" % (graded, ", %d late" % late if late else "")
                       if graded else "nothing marked"),
            "lessons": lessons, "closed": closed, "done": closed is not None,
            "marked_lessons": lesson_n,
            "average": round(sum(counted) / graded, 2) if graded else None,
            "eligible": graded >= MIN_GRADED,
            "missing": [l for k, l, _w in CHAMPIONSHIP if not parts.get(k)],
        })

    rows.sort(key=lambda r: (r["eligible"], r["total"],
                             r["points"].get("homework", 0)), reverse=True)
    place = 0
    for r in rows:
        if r["eligible"]:
            place += 1
            r["rank"] = place
        else:
            r["rank"] = None
    return {"started": True, "season": season_no(db), "start": lo, "rows": rows,
            "paused": is_paused(db), "paused_at": meta_get(db, "season_paused_at"),
            "eligible": sum(1 for r in rows if r["eligible"]),
            "finished": sum(1 for r in rows if r["done"])}


def close_season(db, cfg=None):
    """Write the table into the record book, then start the next season.

    The prize is real money, so the standing that decided it is kept rather
    than recomputed later from data that will have moved on.
    """
    standing = championship(db, cfg)
    if not standing["started"]:
        return None
    winner = next((r for r in standing["rows"] if r["rank"] == 1), None)
    snapshot = [{"rank": r["rank"], "name": r["student"]["name"],
                 "total": r["total"], "points": r["points"],
                 "graded": r["graded"], "words": r["words"],
                 "lessons": r["lessons"]} for r in standing["rows"]]
    db.execute(
        "INSERT INTO seasons (no, started_at, closed_at, winner_id, winner_name,"
        " winner_points, standing) VALUES (?,?,?,?,?,?,?)",
        (standing["season"], standing["start"], iso(now()),
         winner["student"]["id"] if winner else None,
         winner["student"]["name"] if winner else None,
         winner["total"] if winner else None, json.dumps(snapshot)),
    )
    meta_set(db, "season_no", str(standing["season"] + 1))
    meta_set(db, "season_start", iso(now()))
    db.commit()
    return standing


def past_seasons(db):
    return db.execute("SELECT * FROM seasons ORDER BY no DESC").fetchall()


def scope_standing(standing, group_id):
    """The same table narrowed to one class, ranked within it.

    A student in Beginner is permanently fortieth in a school-wide list, which
    is a poor thing to show someone every day. The prize is still school-wide;
    this only changes who they are standing next to.
    """
    if not group_id:
        return standing
    rows = [dict(r) for r in standing["rows"]
            if r["student"]["group_id"] == group_id]
    rows.sort(key=lambda r: (r["eligible"], r["total"],
                             r["points"].get("homework", 0)), reverse=True)
    place = 0
    for r in rows:
        if r["eligible"]:
            place += 1
            r["rank"] = place
        else:
            r["rank"] = None
    out = dict(standing)
    out["rows"] = rows
    out["eligible"] = sum(1 for r in rows if r["eligible"])
    out["finished"] = sum(1 for r in rows if r["done"])
    return out


def class_champions(standing, db):
    """The best eligible student in each class - six winners, not one."""
    best = {}
    for r in standing["rows"]:
        if not r["eligible"]:
            continue
        gid = r["student"]["group_id"]
        if gid and (gid not in best or r["total"] > best[gid]["total"]):
            best[gid] = r
    return best


CRITERIA = [
    ("task", "Task response", "Did they answer the question that was asked?"),
    ("coherence", "Coherence", "Paragraphs, linking, does it follow?"),
    ("lexis", "Vocabulary", "Range and accuracy of word choice"),
    ("grammar", "Grammar", "Range and accuracy of structures"),
]
CRITERIA_KEYS = [k for k, _l, _h in CRITERIA]

DEFAULT_NOTES = [
    "Good structure - keep using those linking words.",
    "Answer the whole question: you left half of it out.",
    "Watch your articles: a / the / nothing.",
    "Strong vocabulary here. Now use it in the next one too.",
    "Too short. Aim for the full word count.",
    "Much better than last time - the practice is showing.",
]


def seed_notes(db):
    """Six sentences to start from; the teacher edits them from the queue."""
    if db.execute("SELECT COUNT(*) c FROM note_templates").fetchone()["c"]:
        return
    for i, text in enumerate(DEFAULT_NOTES):
        db.execute("INSERT INTO note_templates (text, sort) VALUES (?,?)", (text, i))
    db.commit()


def note_templates(db):
    return db.execute(
        "SELECT * FROM note_templates ORDER BY uses DESC, sort, id").fetchall()


def add_note_template(db, text):
    text = (text or "").strip()
    if not text:
        return
    nxt = db.execute("SELECT COALESCE(MAX(sort),0)+1 s FROM note_templates").fetchone()["s"]
    db.execute("INSERT INTO note_templates (text, sort) VALUES (?,?)", (text[:300], nxt))
    db.commit()


def delete_note_template(db, tid):
    db.execute("DELETE FROM note_templates WHERE id=?", (tid,))
    db.commit()


def used_note(db, text):
    """Nudge whichever template this note came from up the list."""
    if not text:
        return
    db.execute("UPDATE note_templates SET uses=uses+1 WHERE text=?", (text.strip(),))
    db.commit()


def set_criteria(db, submission_id, scores):
    """Store the per-criterion marks and return the overall, or None.

    The overall is the plain average of whatever was filled in, to the nearest
    half - the same scale as a hand-given mark, so ratings and the championship
    need to know nothing about criteria.
    """
    db.execute("DELETE FROM criteria_scores WHERE submission_id=?", (submission_id,))
    kept = []
    for key in CRITERIA_KEYS:
        v = mark_score(scores.get(key))
        if v is None:
            continue
        db.execute("INSERT INTO criteria_scores (submission_id, key, score)"
                   " VALUES (?,?,?)", (submission_id, key, v))
        kept.append(v)
    db.commit()
    if not kept:
        return None
    return round(sum(kept) / len(kept) * 2) / 2.0


def criteria_for(db, submission_id):
    return {r["key"]: r["score"] for r in db.execute(
        "SELECT key, score FROM criteria_scores WHERE submission_id=?",
        (submission_id,))}


def previous_graded(db, student_id, before_id):
    """The last piece this student had marked before this one."""
    return db.execute(
        "SELECT * FROM submissions WHERE student_id=? AND status='graded'"
        " AND score IS NOT NULL AND id<>? ORDER BY COALESCE(graded_at, created_at) DESC,"
        " id DESC LIMIT 1", (student_id, before_id)).fetchone()


def student_tag_counts(db, student_id, days=60):
    """Which mistakes keep coming back for this student."""
    since = iso(now() - timedelta(days=days))
    return db.execute(
        "SELECT t.label, COUNT(*) n FROM submission_tags st"
        " JOIN tags t ON t.id=st.tag_id"
        " JOIN submissions s ON s.id=st.submission_id"
        " WHERE s.student_id=? AND s.created_at >= ?"
        " GROUP BY t.id ORDER BY n DESC, t.label LIMIT 6",
        (student_id, since)).fetchall()


def last_graded(db):
    """The most recently marked piece, for the undo strip on the queue."""
    return db.execute(
        "SELECT * FROM submissions WHERE status='graded' AND score IS NOT NULL"
        " ORDER BY graded_at DESC, id DESC LIMIT 1").fetchone()


def mark_score(raw):
    """A mark out of ten, in halves, or None. Anything else is refused."""
    try:
        v = float(raw)
    except (TypeError, ValueError):
        return None
    if not 1 <= v <= 10 or abs(v * 2 - round(v * 2)) > 1e-9:
        return None
    return round(v, 1)


AUDIO_TYPES = {
    ".mp3": "audio/mpeg", ".m4a": "audio/mp4", ".aac": "audio/aac",
    ".ogg": "audio/ogg", ".oga": "audio/ogg", ".opus": "audio/ogg",
    ".wav": "audio/wav", ".flac": "audio/flac", ".weba": "audio/webm",
}
MAX_SONG_BYTES = 20 * 1024 * 1024


def audio_type(filename):
    """The content type for an uploaded song, or None if it is not audio."""
    return AUDIO_TYPES.get(os.path.splitext(filename or "")[1].lower())


def song_for(db, day):
    return db.execute("SELECT * FROM daily_music WHERE day=?", (day,)).fetchone()


def song_today(db, cfg=None):
    return song_for(db, local_day(now(), cfg or load_config()))


def recent_songs(db, limit=60):
    return db.execute("SELECT * FROM daily_music ORDER BY day DESC LIMIT ?",
                      (limit,)).fetchall()


def save_song(db, day, filename, blob, title=None, artist=None):
    """Put one song on one day, replacing whatever was there.

    The file is named after the day rather than the upload, so re-uploading
    cannot leave the previous day's audio orphaned on the volume.
    """
    mime = audio_type(filename)
    if not mime:
        raise ValueError("not an audio file")
    if len(blob) > MAX_SONG_BYTES:
        raise ValueError("too large")
    ext = os.path.splitext(filename)[1].lower()
    stored = "%s%s" % (day, ext)
    old = song_for(db, day)
    with open(os.path.join(MUSIC_DIR, stored), "wb") as fh:
        fh.write(blob)
    if old and old["filename"] != stored:
        drop_song_file(old["filename"])
    db.execute(
        "INSERT INTO daily_music (day, title, artist, filename, original_name,"
        " mime, bytes, created_at) VALUES (?,?,?,?,?,?,?,?)"
        " ON CONFLICT(day) DO UPDATE SET title=excluded.title,"
        " artist=excluded.artist, filename=excluded.filename,"
        " original_name=excluded.original_name, mime=excluded.mime,"
        " bytes=excluded.bytes, created_at=excluded.created_at",
        (day, (title or "").strip() or None, (artist or "").strip() or None,
         stored, filename, mime, len(blob), iso(now())),
    )
    db.commit()
    return song_for(db, day)


def drop_song_file(filename):
    try:
        os.remove(os.path.join(MUSIC_DIR, filename))
    except OSError:
        pass


def delete_song(db, day):
    row = song_for(db, day)
    if not row:
        return
    drop_song_file(row["filename"])
    db.execute("DELETE FROM daily_music WHERE day=?", (day,))
    db.commit()


def music_bytes(db):
    r = db.execute("SELECT COALESCE(SUM(bytes),0) b, COUNT(*) n FROM daily_music").fetchone()
    return r["b"], r["n"]


def quote_of_the_day(cfg=None):
    """The same quote for everyone today, a different one tomorrow."""
    cfg = cfg or load_config()
    day = local_day(now(), cfg)
    ordinal = datetime.strptime(day, "%Y-%m-%d").toordinal()
    return QUOTES[ordinal % len(QUOTES)]


def journey(db, student_id):
    """How far along their own road they are.

    They say where they started and where they are going; the middle is their
    real marked work, so the line cannot be talked up. Returns None until they
    have set it and have something graded to show.
    """
    s = db.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()
    if not s:
        return None
    try:
        start, goal = s["journey_from"], s["journey_to"]
    except (IndexError, KeyError):
        return None
    if start is None or goal is None or goal <= start:
        return None

    weeks = db.execute(
        "SELECT strftime('%Y-%W', created_at) wk, AVG(score) avg, COUNT(*) n"
        " FROM submissions WHERE student_id=? AND status='graded' AND score IS NOT NULL"
        " GROUP BY wk ORDER BY wk", (student_id,)).fetchall()
    points = [{"week": r["wk"], "score": round(r["avg"], 2), "count": r["n"]}
              for r in weeks]
    if not points:
        return None
    now_score = points[-1]["score"]
    span = goal - start
    done = max(0.0, min(1.0, (now_score - start) / span)) if span else 0.0
    return {"start": start, "goal": goal, "now": now_score,
            "percent": int(round(done * 100)), "points": points,
            "set_at": s["journey_at"]}


def next_step(db, student_id):
    """Where a student stands, and the nearest thing they could do about it.

    A rank on its own does not move anybody. A rank plus one reachable action
    does, so this works out how many more pieces of homework would close the
    gap to whoever is directly above them, and says so in those terms.

    Returns None when there is nothing honest to say - no class, no standings,
    or a gap that homework alone cannot close.
    """
    me = db.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()
    if not me or not me["group_id"]:
        return None
    rows = rating_rows(db, me["group_id"])
    mine = next((i for i, r in enumerate(rows) if r["student"]["id"] == student_id), None)
    if mine is None or len(rows) < 2:
        return None

    out = {"rank": rows[mine]["rank"], "of": len(rows), "index": rows[mine]["index"],
           "ahead": None, "behind": None, "tasks": None, "gap": None}

    if mine > 0:
        above = rows[mine - 1]
        out["ahead"] = above["student"]["name"]
        gap = (above["index"] or 0) - (rows[mine]["index"] or 0)
        out["gap"] = round(gap, 1)
        total = db.execute(
            "SELECT COUNT(*) c FROM assignments WHERE group_id=? AND published=1",
            (me["group_id"],)).fetchone()["c"]
        # handing in one more piece moves completion by 100/total, and completion
        # is half of the index
        if total:
            per_task = 0.5 * (100.0 / total)
            if gap <= 0:
                # level on points, separated only by name: one more breaks the tie
                out["tasks"] = 1
            elif per_task > 0:
                need = int(gap // per_task) + (1 if gap % per_task else 0)
                if 1 <= need <= 3:
                    out["tasks"] = need
    if mine + 1 < len(rows):
        out["behind"] = rows[mine + 1]["student"]["name"]
    return out


def most_improved(db, group_id=None, limit=10):
    """Ranked purely on gain against the student's own previous month.

    Only students who actually went up: a table headed "most improved" that
    lists people who got worse is a punishment, not an encouragement.
    """
    rows = [r for r in rating_rows(db, group_id)
            if r["gain"] is not None and r["gain"] > 0]
    rows.sort(key=lambda r: (-r["gain"], r["student"]["name"]))
    return rows[:limit]


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
    if n is None:
        return ""
    if n == 0:
        return "0 B"
    for unit in ("B", "KB", "MB"):
        if n < 1024 or unit == "MB":
            return ("%.0f %s" if unit == "B" else "%.1f %s") % (n, unit)
        n /= 1024.0


def units_in(db, level_id, collection, category):
    """Which unit numbers have anything in this section, and how many files."""
    rows = db.execute(
        "SELECT unit, COUNT(*) c FROM materials WHERE active=1 AND collection=?"
        " AND category=? AND unit IS NOT NULL AND (level_id IS NULL OR level_id IS ?)"
        " GROUP BY unit ORDER BY unit", (collection, category, level_id)
    ).fetchall()
    return {r["unit"]: r["c"] for r in rows}


def books_in(db, level_id, collection, category, unit):
    rows = db.execute(
        "SELECT book, COUNT(*) c FROM materials WHERE active=1 AND collection=?"
        " AND category=? AND unit=? AND (level_id IS NULL OR level_id IS ?)"
        " GROUP BY book", (collection, category, unit, level_id)
    ).fetchall()
    return {(r["book"] or "class"): r["c"] for r in rows}


def materials_in_unit(db, level_id, collection, category, unit, book=None):
    sql = ("SELECT * FROM materials WHERE active=1 AND collection=? AND category=?"
           " AND unit=? AND (level_id IS NULL OR level_id IS ?)")
    args = [collection, category, unit, level_id]
    if book:
        sql += " AND (book=? OR (book IS NULL AND ?='class'))"
        args += [book, book]
    return db.execute(sql + " ORDER BY title", args).fetchall()


def book_label(book):
    return BOOKS.get(book or "class", BOOKS["class"])


def open_draft(db, student_id, assignment_id):
    """The unfinished work for this task, if the student has started it."""
    if assignment_id is None:
        return None
    return db.execute(
        "SELECT * FROM submissions WHERE student_id=? AND assignment_id=? AND draft=1"
        " ORDER BY created_at DESC LIMIT 1", (student_id, assignment_id)
    ).fetchone()


def sent_submission(db, student_id, assignment_id):
    """Work already handed in for this task - the reason to refuse more photos."""
    if assignment_id is None:
        return None
    return db.execute(
        "SELECT * FROM submissions WHERE student_id=? AND assignment_id=? AND draft=0"
        " ORDER BY created_at DESC LIMIT 1", (student_id, assignment_id)
    ).fetchone()


def finish_draft(db, submission_id):
    """Hand a draft in: from here it is visible to the teacher and locked."""
    db.execute("UPDATE submissions SET draft=0, created_at=? WHERE id=? AND draft=1",
               (iso(now()), submission_id))
    db.commit()


def open_submission(db, student_id, assignment_id):
    """The piece of work already in progress for this task, if any.

    One task means one submission: extra photos join the ungraded one rather
    than piling up as separate entries in the teacher's queue. Once it has been
    graded, the next photo starts a fresh attempt.
    """
    if assignment_id is None:
        return None
    return db.execute(
        "SELECT * FROM submissions WHERE student_id=? AND assignment_id=?"
        " AND status='pending' ORDER BY created_at DESC LIMIT 1",
        (student_id, assignment_id),
    ).fetchone()


def page_count(db, submission_id):
    return db.execute(
        "SELECT COUNT(*) c FROM files WHERE submission_id=?", (submission_id,)
    ).fetchone()["c"]


def merge_submissions(db, keep_id, drop_id):
    """Fold one submission's pages into another and remove the empty shell."""
    if keep_id == drop_id:
        return
    start = page_count(db, keep_id)
    for i, f in enumerate(db.execute(
            "SELECT * FROM files WHERE submission_id=? ORDER BY ord, id", (drop_id,))):
        db.execute("UPDATE files SET submission_id=?, ord=? WHERE id=?",
                   (keep_id, start + i, f["id"]))
    db.execute("DELETE FROM submissions WHERE id=?", (drop_id,))
    db.commit()


# ---------------------------------------------------------- lesson marks

MARK_FIELDS = ("punctuality", "behaviour", "participation")
MARK_LABELS = {"punctuality": "Punctuality", "behaviour": "Behaviour",
               "participation": "Participation"}
MARK_MAX = 5


def marks_on(db, group_id, day):
    """What was recorded for this class on one date, keyed by student."""
    rows = db.execute(
        "SELECT m.* FROM lesson_marks m JOIN students s ON s.id=m.student_id"
        " WHERE s.group_id=? AND m.day=?", (group_id, day)
    ).fetchall()
    return {r["student_id"]: r for r in rows}


def save_mark(db, student_id, day, values, note=None):
    clean = {}
    for field in MARK_FIELDS:
        v = values.get(field)
        clean[field] = v if isinstance(v, int) and 1 <= v <= MARK_MAX else None
    db.execute(
        "INSERT INTO lesson_marks (student_id, day, punctuality, behaviour,"
        " participation, note, created_at) VALUES (?,?,?,?,?,?,?)"
        " ON CONFLICT(student_id, day) DO UPDATE SET punctuality=excluded.punctuality,"
        " behaviour=excluded.behaviour, participation=excluded.participation,"
        " note=excluded.note",
        (student_id, day, clean["punctuality"], clean["behaviour"],
         clean["participation"], note, iso(now())),
    )


def mark_stats(db, student_id, since=None):
    """Averages per criterion, and how many lessons were recorded."""
    sql = "SELECT * FROM lesson_marks WHERE student_id=?"
    args = [student_id]
    if since:
        sql += " AND day >= ?"
        args.append(since)
    rows = db.execute(sql, args).fetchall()
    out = {"lessons": len(rows)}
    total, count = 0.0, 0
    for field in MARK_FIELDS:
        values = [r[field] for r in rows if r[field] is not None]
        out[field] = round(sum(values) / len(values), 2) if values else None
        total += sum(values)
        count += len(values)
    out["overall"] = round(total / count, 2) if count else None
    return out


def overall_index(completion, average, marks):
    """One number out of 100, so a class can be ranked on more than scores.

    Half effort, a quarter attainment, a quarter how they are in the room -
    weighted this way on purpose, because effort is what a student controls.
    """
    parts, weights = [], []
    if completion is not None:
        parts.append(completion); weights.append(0.5)
    if average is not None:
        parts.append(average * 10); weights.append(0.25)
    if marks is not None:
        parts.append(marks / MARK_MAX * 100); weights.append(0.25)
    if not parts:
        return None
    return round(sum(p * w for p, w in zip(parts, weights)) / sum(weights))


# ------------------------------------------------------- period reporting

def period_key(day, period):
    d = datetime.strptime(day, "%Y-%m-%d")
    if period == "daily":
        return day
    if period == "weekly":
        return "%s-W%02d" % d.isocalendar()[:2]
    return d.strftime("%Y-%m")


def group_periods(db, group_id, period="weekly", limit=8):
    """Average score, completion and lesson mark per day, week or month."""
    subs = db.execute(
        "SELECT s.score, s.graded_at, s.created_at FROM submissions s"
        " JOIN students st ON st.id=s.student_id"
        " WHERE st.group_id=? AND s.status='graded' AND s.score IS NOT NULL",
        (group_id,),
    ).fetchall()
    marks = db.execute(
        "SELECT m.* FROM lesson_marks m JOIN students s ON s.id=m.student_id"
        " WHERE s.group_id=?", (group_id,),
    ).fetchall()

    buckets = {}
    for row in subs:
        day = (row["graded_at"] or row["created_at"] or "")[:10]
        if not day:
            continue
        b = buckets.setdefault(period_key(day, period), {"scores": [], "marks": []})
        b["scores"].append(row["score"])
    for row in marks:
        b = buckets.setdefault(period_key(row["day"], period), {"scores": [], "marks": []})
        for field in MARK_FIELDS:
            if row[field] is not None:
                b["marks"].append(row[field])

    out = []
    for key in sorted(buckets)[-limit:]:
        b = buckets[key]
        out.append({
            "key": key,
            "score": round(sum(b["scores"]) / len(b["scores"]), 2) if b["scores"] else None,
            "mark": round(sum(b["marks"]) / len(b["marks"]), 2) if b["marks"] else None,
            "count": len(b["scores"]),
        })
    return out


def remove_student(db, student_id):
    """Delete a student and everything attached to them. Not reversible."""
    photos = [r["filename"] for r in db.execute(
        "SELECT f.filename FROM files f JOIN submissions s ON s.id=f.submission_id"
        " WHERE s.student_id=?", (student_id,))]
    db.execute("DELETE FROM files WHERE submission_id IN"
               " (SELECT id FROM submissions WHERE student_id=?)", (student_id,))
    db.execute("DELETE FROM submission_tags WHERE submission_id IN"
               " (SELECT id FROM submissions WHERE student_id=?)", (student_id,))
    # read this before the row goes: the old order looked it up afterwards, by
    # which time the subquery matched nothing and the state was left behind
    who = db.execute("SELECT telegram_id FROM students WHERE id=?",
                     (student_id,)).fetchone()
    for table in ("submissions", "word_progress", "quiz_sessions", "questions",
                  "parents", "lesson_marks", "students"):
        db.execute(f"DELETE FROM {table} WHERE student_id=?"
                   if table != "students" else "DELETE FROM students WHERE id=?",
                   (student_id,))
    if who and who["telegram_id"]:
        db.execute("DELETE FROM bot_state WHERE telegram_id=?", (who["telegram_id"],))
    db.commit()
    return photos


def last_active(db, student_id):
    """The last sign of life: work sent, or words practised."""
    a = db.execute("SELECT MAX(created_at) t FROM submissions WHERE student_id=?",
                   (student_id,)).fetchone()["t"]
    b = db.execute("SELECT MAX(last_seen) t FROM word_progress WHERE student_id=?",
                   (student_id,)).fetchone()["t"]
    best = max([x for x in (a, b) if x], default=None)
    if not best:
        return None, None
    days = (now() - parse(best)).days
    return best, days


def add_student(db, name, group_id):
    """A student who cannot use Telegram still needs a place and a link."""
    name = (name or "").strip()
    if not name or not group_id:
        return None
    sid = db.execute(
        "INSERT INTO students (name, group_id, active, created_at) VALUES (?,?,1,?)",
        (name[:80], int(group_id), iso(now()))).lastrowid
    db.commit()
    student_token(db, sid)
    return sid


def move_student(db, student_id, group_id):
    db.execute("UPDATE students SET group_id=? WHERE id=?", (int(group_id), student_id))
    db.commit()


def set_student_active(db, student_id, active):
    db.execute("UPDATE students SET active=? WHERE id=?", (1 if active else 0, student_id))
    db.commit()


# ------------------------------------------------------------- band scores

BAND_SECTIONS = ("listening", "reading", "writing", "speaking")
BAND_LABELS = {"listening": "Listening", "reading": "Reading",
               "writing": "Writing", "speaking": "Speaking"}


def valid_band(value):
    """IELTS bands run 0 to 9 in half steps."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if not 0 <= v <= 9:
        return None
    return round(v * 2) / 2


def overall_band(scores):
    """The four sections averaged, rounded the way IELTS rounds.

    A quarter rounds up to the next half band, three quarters up to the next
    whole band; anything else falls to the nearest half.
    """
    values = [v for v in scores if v is not None]
    if len(values) < 4:
        return None
    avg = sum(values) / 4.0
    floor_half = int(avg * 2) / 2.0
    return floor_half + 0.5 if (avg - floor_half) >= 0.25 else floor_half


def get_goal(db, student_id):
    return db.execute("SELECT * FROM goals WHERE student_id=?", (student_id,)).fetchone()


def save_goal(db, student_id, scores, target_date=None):
    db.execute(
        "INSERT INTO goals (student_id, listening, reading, writing, speaking,"
        " target_date, updated_at) VALUES (?,?,?,?,?,?,?)"
        " ON CONFLICT(student_id) DO UPDATE SET listening=excluded.listening,"
        " reading=excluded.reading, writing=excluded.writing,"
        " speaking=excluded.speaking, target_date=excluded.target_date,"
        " updated_at=excluded.updated_at",
        (student_id, scores.get("listening"), scores.get("reading"),
         scores.get("writing"), scores.get("speaking"), target_date, iso(now())),
    )
    db.commit()


def band_words(band):
    if band is None:
        return ""
    if band >= 8:
        return "Very good to expert user"
    if band >= 7:
        return "Good user"
    if band >= 6:
        return "Competent user"
    if band >= 5:
        return "Modest user"
    return "Limited user"
