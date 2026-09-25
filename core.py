"""Shared config, database access and domain logic."""
import hashlib
import json
import os
import random
import re
import sqlite3
import secrets
import shutil
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
# DATA_DIR is overridable so a host can point it at a disk that survives
# redeploys - everything that must persist (database + photos) lives here.
DATA_DIR = os.environ.get("DATA_DIR") or os.path.join(ROOT, "data")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
MATERIAL_DIR = os.path.join(DATA_DIR, "materials")
MUSIC_DIR = os.path.join(DATA_DIR, "music")
AUDIO_DIR = os.path.join(DATA_DIR, "audio")      # the coursebook's own tracks
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

        # the daily backup is also sent to the teacher in Telegram, which puts
        # the whole student database in a chat history: a fair trade against
        # losing everything, but it should be a choice
        "backup_to_telegram": True,

        # How long a graded page keeps its full-resolution photograph on the
        # disk; after that it is fetched back from Telegram when opened.
        #
        # Ten days, because the arithmetic decides it: sixty students send
        # about 200 MB of photographs a day, so every day of keeping costs a
        # fifth of a gigabyte. Ten days is a fortnight of marking within easy
        # reach and about 2 GB of the volume - raise it and the disk fills,
        # lower it and old work takes a moment to open.
        "photo_keep_days": 10,

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
    env("BACKUP_TO_TELEGRAM", "backup_to_telegram", bool)
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
    test_id INTEGER REFERENCES dtests(id),   -- when the homework is a booklet
    due_at TEXT,
    created_at TEXT NOT NULL,
    closed INTEGER NOT NULL DEFAULT 0,
    published INTEGER NOT NULL DEFAULT 0,
    in_league INTEGER NOT NULL DEFAULT 1
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
    # CREATE TABLE IF NOT EXISTS never adds a column to a table that is already
    # there, so anything added to dquestions after its first deploy needs this
    qcols = {r["name"] for r in db.execute("PRAGMA table_info(dquestions)")}
    if qcols and "image" not in qcols:
        db.execute("ALTER TABLE dquestions ADD COLUMN image TEXT")

    tcols = {r["name"] for r in db.execute("PRAGMA table_info(dtests)")}
    if tcols and "minutes" not in tcols:
        # a test sat under exam conditions: the clock, and whether leaving the
        # window ends it
        db.execute("ALTER TABLE dtests ADD COLUMN minutes INTEGER")
        db.execute("ALTER TABLE dtests ADD COLUMN strict INTEGER NOT NULL DEFAULT 0")
    if tcols and "once" not in tcols:
        # an exam is sat once; a practice test is sat as often as it helps
        db.execute("ALTER TABLE dtests ADD COLUMN once INTEGER NOT NULL DEFAULT 0")
    if tcols and "layout" not in tcols:
        # the booklet itself, as the student's own page, with its blanks
        # marked up so their boxes go back in the right holes
        db.execute("ALTER TABLE dtests ADD COLUMN layout TEXT")
    if tcols and "in_league" not in tcols:
        # a test can be published for practice without deciding the table
        db.execute("ALTER TABLE dtests ADD COLUMN in_league"
                   " INTEGER NOT NULL DEFAULT 1")
    tcols = {r["name"] for r in db.execute("PRAGMA table_info(dtests)")}
    if tcols and "kind" not in tcols:
        # a handout is a test that is not a test: no clock, no one sitting,
        # no score to chase. It lives on its own page so the Tests tab stays
        # a list of things that are actually marked.
        db.execute("ALTER TABLE dtests ADD COLUMN kind TEXT NOT NULL"
                   " DEFAULT 'test'")

    acols = {r["name"] for r in db.execute("PRAGMA table_info(assignments)")}
    if "prompt" not in acols:
        # a writing task carries its question, so the student can see it beside
        # the sheet they are writing on, the way a real paper is laid out
        db.execute("ALTER TABLE assignments ADD COLUMN prompt TEXT")
        db.execute("ALTER TABLE assignments ADD COLUMN minutes INTEGER")
        db.execute("ALTER TABLE assignments ADD COLUMN min_words INTEGER")
    pcols = {r["name"] for r in db.execute("PRAGMA table_info(prompts)")}
    if pcols and "unit" not in pcols:
        for col in ("unit INTEGER", "lesson TEXT", "topic TEXT"):
            db.execute("ALTER TABLE prompts ADD COLUMN %s" % col)
    if "test_id" not in acols:
        # a piece of homework can *be* the digital booklet, rather than a line
        # of text telling the student to go and find it
        db.execute("ALTER TABLE assignments ADD COLUMN test_id INTEGER"
                   " REFERENCES dtests(id)")
    if "in_league" not in acols:
        # homework can be set, marked and seen by students without counting
        # towards the league - a leftover set, or one that was only practice
        db.execute("ALTER TABLE assignments ADD COLUMN in_league"
                   " INTEGER NOT NULL DEFAULT 1")
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
    if "answer" not in scols:
        # typed work, instead of a photograph of handwriting
        db.execute("ALTER TABLE submissions ADD COLUMN answer TEXT")
        db.execute("ALTER TABLE submissions ADD COLUMN words INTEGER")
        db.execute("ALTER TABLE submissions ADD COLUMN written_secs INTEGER")
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
    -- solo play: a student on their own, from the Play tab. Never in the league.
    CREATE TABLE IF NOT EXISTS solo_runs (
        id INTEGER PRIMARY KEY,
        student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
        list_id INTEGER NOT NULL REFERENCES word_lists(id) ON DELETE CASCADE,
        q_count INTEGER NOT NULL,
        seconds INTEGER NOT NULL,
        score INTEGER NOT NULL DEFAULT 0,
        correct INTEGER NOT NULL DEFAULT 0,
        started_at TEXT NOT NULL,
        finished_at TEXT
    );
    CREATE TABLE IF NOT EXISTS solo_questions (
        id INTEGER PRIMARY KEY,
        run_id INTEGER NOT NULL REFERENCES solo_runs(id) ON DELETE CASCADE,
        ord INTEGER NOT NULL,
        word_id INTEGER NOT NULL REFERENCES words(id) ON DELETE CASCADE,
        options TEXT NOT NULL,                 -- JSON, four answers
        answer INTEGER NOT NULL,               -- which of them is right
        shown_at TEXT,                         -- the server's clock, not the phone's
        choice INTEGER,                        -- -1 when the time ran out
        correct INTEGER,
        points INTEGER NOT NULL DEFAULT 0
    );
    CREATE INDEX IF NOT EXISTS solo_runs_by_student ON solo_runs(student_id, list_id);
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
    CREATE TABLE IF NOT EXISTS sessions (
        token TEXT PRIMARY KEY,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS prompts (
        id INTEGER PRIMARY KEY,
        level TEXT NOT NULL,               -- Beginner ... IELTS Standard
        kind TEXT NOT NULL,                -- email, letter, opinion, task1 ...
        text TEXT NOT NULL,
        min_words INTEGER,
        minutes INTEGER,
        unit INTEGER,                      -- the coursebook unit it belongs to
        lesson TEXT,                       -- which lesson slot it is taught in
        topic TEXT,                        -- the unit's title, for the picker
        mine INTEGER NOT NULL DEFAULT 0,   -- written by the teacher, not shipped
        used INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS dtests (
        id INTEGER PRIMARY KEY,
        level_id INTEGER REFERENCES levels(id),
        number INTEGER,
        title TEXT NOT NULL,
        passage TEXT,                      -- the gap-fill text, when there is one
        published INTEGER NOT NULL DEFAULT 0,
        in_league INTEGER NOT NULL DEFAULT 1,
        layout TEXT,                       -- the booklet as a page, when there is one
        minutes INTEGER,                   -- a time limit, for an exam
        strict INTEGER NOT NULL DEFAULT 0, -- leaving the window ends it
        once INTEGER NOT NULL DEFAULT 0,   -- one sitting only: an exam, not practice
        kind TEXT NOT NULL DEFAULT 'test', -- 'test' is marked; 'handout' is worked through
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS dquestions (
        id INTEGER PRIMARY KEY,
        test_id INTEGER NOT NULL REFERENCES dtests(id) ON DELETE CASCADE,
        num INTEGER NOT NULL,
        kind TEXT NOT NULL,
        prompt TEXT NOT NULL,
        answer TEXT,                       -- null until the teacher sets the key
        image TEXT,                        -- a passage that only exists as a picture
        ord INTEGER NOT NULL DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS doptions (
        id INTEGER PRIMARY KEY,
        question_id INTEGER NOT NULL REFERENCES dquestions(id) ON DELETE CASCADE,
        letter TEXT NOT NULL,
        text TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS dattempts (
        id INTEGER PRIMARY KEY,
        test_id INTEGER NOT NULL REFERENCES dtests(id) ON DELETE CASCADE,
        student_id INTEGER NOT NULL REFERENCES students(id),
        started_at TEXT NOT NULL,
        finished_at TEXT,
        score INTEGER,
        total INTEGER
    );
    CREATE TABLE IF NOT EXISTS dresponses (
        attempt_id INTEGER NOT NULL REFERENCES dattempts(id) ON DELETE CASCADE,
        question_id INTEGER NOT NULL REFERENCES dquestions(id) ON DELETE CASCADE,
        given TEXT,
        correct INTEGER,
        PRIMARY KEY (attempt_id, question_id)
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
    -- ---------------------------------------------------------------- the cycle
    --
    -- A student joins, works, sits the exams, and then either stays or goes.
    -- None of that was ever written down: `students.active` was a flag nobody
    -- set, so a retention rate could not be worked out from this database at
    -- all. These four tables are what make the cycle a record rather than a
    -- memory.
    --
    -- Every one of them carries a teacher_id from the first day. There is one
    -- teacher today and no login for anybody else, but adding the column now
    -- costs nothing and means opening this to colleagues is a login screen
    -- rather than a migration of every row.
    CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        ielts REAL,                        -- the teacher's own band
        celta INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL
    );
    -- one row per spell at the centre, so a student who leaves and comes back
    -- has two, and neither overwrites the other
    CREATE TABLE IF NOT EXISTS enrolments (
        id INTEGER PRIMARY KEY,
        student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
        teacher_id INTEGER REFERENCES teachers(id),
        group_id INTEGER REFERENCES groups(id),
        started_at TEXT NOT NULL,
        ended_at TEXT,                     -- null means still here
        reason TEXT,                       -- why they left, from a fixed list
        note TEXT,
        created_at TEXT NOT NULL
    );
    -- work done in the room. Kept apart from the participation marks on
    -- purpose: one measures effort, the other measures learning, and
    -- averaging them together hides both.
    CREATE TABLE IF NOT EXISTS class_tests (
        id INTEGER PRIMARY KEY,
        teacher_id INTEGER REFERENCES teachers(id),
        group_id INTEGER REFERENCES groups(id),
        title TEXT NOT NULL,
        max_score REAL NOT NULL DEFAULT 100,
        sat_on TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS class_test_scores (
        test_id INTEGER NOT NULL REFERENCES class_tests(id) ON DELETE CASCADE,
        student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
        score REAL,
        absent INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY (test_id, student_id)
    );
    -- the centre's own mid and final exams. marked_by is recorded because the
    -- teacher marks their own students, and an average is only believable
    -- when you can see who produced it.
    CREATE TABLE IF NOT EXISTS exam_results (
        id INTEGER PRIMARY KEY,
        student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
        teacher_id INTEGER REFERENCES teachers(id),
        group_id INTEGER REFERENCES groups(id),
        kind TEXT NOT NULL,                -- 'mid' or 'final'
        title TEXT,
        score REAL,
        max_score REAL NOT NULL DEFAULT 100,
        sat_on TEXT NOT NULL,
        marked_by TEXT,
        created_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS enrolments_by_student
        ON enrolments(student_id, ended_at);
    CREATE INDEX IF NOT EXISTS exam_results_by_student
        ON exam_results(student_id, kind);
    CREATE TABLE IF NOT EXISTS parents (
        id INTEGER PRIMARY KEY,
        student_id INTEGER NOT NULL REFERENCES students(id),
        telegram_id INTEGER UNIQUE,
        token TEXT UNIQUE,
        created_at TEXT NOT NULL
    );
    -- a battle: up to four classmates racing through the same questions at
    -- their own speed, each watching the others move. Never in the league.
    CREATE TABLE IF NOT EXISTS battles (
        id INTEGER PRIMARY KEY,
        code TEXT UNIQUE,
        group_id INTEGER REFERENCES groups(id),
        list_id INTEGER NOT NULL REFERENCES word_lists(id) ON DELETE CASCADE,
        host_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
        q_count INTEGER NOT NULL,
        seconds INTEGER NOT NULL,
        state TEXT NOT NULL DEFAULT 'lobby',   -- lobby | racing | done
        created_at TEXT NOT NULL,
        started_at TEXT,
        finished_at TEXT
    );
    -- one shared set of questions, in one shared order: the race is only fair
    -- if every car drives the same track
    CREATE TABLE IF NOT EXISTS battle_questions (
        id INTEGER PRIMARY KEY,
        battle_id INTEGER NOT NULL REFERENCES battles(id) ON DELETE CASCADE,
        ord INTEGER NOT NULL,
        word_id INTEGER NOT NULL REFERENCES words(id) ON DELETE CASCADE,
        options TEXT NOT NULL,                 -- JSON, four answers
        answer INTEGER NOT NULL,
        UNIQUE (battle_id, ord)
    );
    CREATE TABLE IF NOT EXISTS battle_players (
        id INTEGER PRIMARY KEY,
        battle_id INTEGER NOT NULL REFERENCES battles(id) ON DELETE CASCADE,
        student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
        score INTEGER NOT NULL DEFAULT 0,
        correct INTEGER NOT NULL DEFAULT 0,
        answered INTEGER NOT NULL DEFAULT 0,   -- how far along the track they are
        place INTEGER,                         -- 1 is the winner, set at the end
        joined_at TEXT NOT NULL,
        finished_at TEXT,
        UNIQUE (battle_id, student_id)
    );
    CREATE TABLE IF NOT EXISTS battle_answers (
        id INTEGER PRIMARY KEY,
        battle_id INTEGER NOT NULL REFERENCES battles(id) ON DELETE CASCADE,
        student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
        ord INTEGER NOT NULL,
        shown_at TEXT,                         -- the server's clock, not the phone's
        choice INTEGER,                        -- -1 when the time ran out
        correct INTEGER,
        points INTEGER NOT NULL DEFAULT 0,
        UNIQUE (battle_id, student_id, ord)
    );
    CREATE TABLE IF NOT EXISTS battle_invites (
        id INTEGER PRIMARY KEY,
        battle_id INTEGER NOT NULL REFERENCES battles(id) ON DELETE CASCADE,
        from_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
        to_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
        created_at TEXT NOT NULL,
        state TEXT NOT NULL DEFAULT 'open',    -- open | joined | declined
        UNIQUE (battle_id, to_id)
    );
    CREATE INDEX IF NOT EXISTS battles_by_group ON battles(group_id, state);
    CREATE INDEX IF NOT EXISTS battle_players_by_student
        ON battle_players(student_id, battle_id);
    """)
    scols = {r["name"] for r in db.execute("PRAGMA table_info(students)")}
    if "last_seen" not in scols:
        # who is on the site right now, so a student can invite a classmate
        # who will actually answer rather than one who went home
        db.execute("ALTER TABLE students ADD COLUMN last_seen TEXT")
    wcols = {r["name"] for r in db.execute("PRAGMA table_info(words)")}
    if "example" not in wcols:
        db.execute("ALTER TABLE words ADD COLUMN example TEXT")
    if "options" not in wcols:
        # a grammar question carries its own wrong answers: drawing them from
        # other rows would offer "bigger / apple / quickly" and give the game away
        db.execute("ALTER TABLE words ADD COLUMN options TEXT")
    lcols = {r["name"] for r in db.execute("PRAGMA table_info(word_lists)")}
    if lcols and "kind" not in lcols:
        db.execute("ALTER TABLE word_lists ADD COLUMN kind TEXT NOT NULL DEFAULT 'vocab'")
    lcols = {r["name"] for r in db.execute("PRAGMA table_info(word_lists)")}
    if lcols and "level_id" not in lcols:
        # which level a list is for. Without it every student saw every list,
        # so an Elementary class was offered Intermediate conditionals.
        db.execute("ALTER TABLE word_lists ADD COLUMN level_id INTEGER"
                   " REFERENCES levels(id)")
    lcols = {r["name"] for r in db.execute("PRAGMA table_info(word_lists)")}
    if lcols and "extra_levels" not in lcols:
        # a list belongs to one level, but some are worth more than one: the
        # A2 exam words are the floor for Pre-Intermediate too, because the
        # B1 exam list contains every A2 word.
        db.execute("ALTER TABLE word_lists ADD COLUMN extra_levels TEXT")
    lcols = {r["name"] for r in db.execute("PRAGMA table_info(word_lists)")}
    if lcols and "step" not in lcols:
        # where a list sits in its ladder. 0 means "wherever its unit number
        # puts it", which is right for a book of numbered units.
        db.execute("ALTER TABLE word_lists ADD COLUMN step INTEGER NOT NULL DEFAULT 0")
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


def disk_room():
    """How much room is left where the data lives.

    Returns (free_bytes, total_bytes). Everything - the database, the uploaded
    photographs, a thousand course files and the daily backups - shares one
    volume, and when it fills, SQLite stops being able to write: the site
    still reads, so pages load, and every attempt to sign in fails with
    "database or disk is full".
    """
    try:
        usage = shutil.disk_usage(DATA_DIR)
        return usage.free, usage.total
    except Exception:
        return None, None


def disk_breakdown():
    """What is actually using the volume, biggest first.

    Worth measuring rather than assuming: the photographs were reckoned at
    1.3 MB each from a subtraction, and turned out to be nearer 300 KB, which
    made every estimate built on it wrong.
    """
    out = []
    try:
        for name in sorted(os.listdir(DATA_DIR)):
            path = os.path.join(DATA_DIR, name)
            if os.path.isfile(path):
                out.append((name, os.path.getsize(path)))
                continue
            total = 0
            for root, _dirs, files in os.walk(path):
                for f in files:
                    try:
                        total += os.path.getsize(os.path.join(root, f))
                    except OSError:
                        pass
            out.append((name + "/", total))
    except OSError:
        return []
    return sorted(out, key=lambda p: -p[1])


def make_room(keep=2):
    """Throw away the oldest backups when the volume is nearly full.

    The backups are the first thing to go because they are the one thing on
    the volume that is reproducible on demand, and because a backup is no use
    at all if it is the reason the site cannot write.
    """
    free, total = disk_room()
    if free is None or total is None:
        return "cannot tell"
    if free > 250 * 1024 * 1024:
        return "%.0f MB free" % (free / 1048576)
    folder = os.path.join(DATA_DIR, "backups")
    if not os.path.isdir(folder):
        return "%.0f MB free, no backups to remove" % (free / 1048576)
    files = sorted(f for f in os.listdir(folder) if f.endswith(".db"))
    removed = 0
    for old in files[:-keep] if len(files) > keep else []:
        try:
            os.remove(os.path.join(folder, old))
            removed += 1
        except OSError:
            pass
    after, _t = disk_room()
    return ("only %.0f MB free - removed %d old backup(s), %.0f MB free now"
            % (free / 1048576, removed, (after or 0) / 1048576))


# ------------------------------------------------------------- what is stored

def storage_summary(db):
    """Everything the site keeps, what it costs, and what can safely go.

    Written for the Settings page, where the teacher decides what to throw
    away. Each row says how much room it takes and, where it matters, how much
    of it exists nowhere else.
    """
    rows = []
    free, total = disk_room()
    sizes = dict(disk_breakdown())

    photos = db.execute("SELECT COUNT(*) n FROM files").fetchone()["n"]
    only = db.execute("SELECT COUNT(*) n FROM files"
                      " WHERE telegram_file_id IS NULL").fetchone()["n"]
    rows.append({
        "key": "photos", "title": "Photographs of homework",
        "count": photos, "bytes": sizes.get("uploads/", 0),
        "note": ("%d of them were uploaded from the website and exist nowhere "
                 "else; the rest can be fetched back from Telegram." % only)
        if only else "All of them can be fetched back from Telegram.",
        "danger": bool(only)})

    mats = db.execute("SELECT COUNT(*) n FROM materials").fetchone()["n"]
    rows.append({
        "key": "materials", "title": "Course files on the shelves",
        "count": mats, "bytes": sizes.get("materials/", 0),
        "note": "Books, audio and papers you uploaded. All of it is still on "
                "your own computer.", "danger": False})

    rows.append({
        "key": "audio", "title": "Coursebook tracks for the booklets",
        "count": None, "bytes": sizes.get("audio/", 0),
        "note": "The listening tracks the booklets play. Re-uploaded with one "
                "command.", "danger": False})

    rows.append({
        "key": "music", "title": "Songs of the day",
        "count": db.execute("SELECT COUNT(*) n FROM songs").fetchone()["n"]
        if table_exists(db, "songs") else None,
        "bytes": sizes.get("music/", 0),
        "note": "One track a day. Removing them does not affect anybody's "
                "work.", "danger": False})

    rows.append({
        "key": "backups", "title": "Database backups",
        "count": None, "bytes": sizes.get("backups/", 0),
        "note": "Daily copies of the database, kept on this same disk. Keep a "
                "copy somewhere else as well.", "danger": True})

    return {"rows": rows, "free": free, "total": total,
            "database": sizes.get("app.db", 0)}


def table_exists(db, name):
    return bool(db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,)).fetchone())


# The settings a teacher may change from the website. The password and the
# bot token are deliberately not here: those belong in the host's own
# settings, where changing one does not need a deploy and nothing prints it.
EDITABLE = [
    ("photo_keep_days", "Keep photographs for", "days",
     "After this, a page is fetched back from Telegram when you open it. "
     "Every day of keeping costs about 200 MB."),
    ("min_photo_width", "Reject photographs narrower than", "pixels",
     "A page photographed too small cannot be read, and is refused before it "
     "reaches your queue."),
    ("chase_hours", "Chase a missing photo after", "hours",
     "How long the bot waits before reminding a student who has sent nothing."),
    ("chase_threshold", "Only chase below", "%",
     "Students already above this completion are left alone."),
    ("chase_max", "Never chase more than", "times",
     "A limit per student per piece of homework."),
    ("timezone_offset_hours", "Hours ahead of UTC", "",
     "Tashkent is 5. Deadlines and the day's date follow this."),
]
SWITCHES = [
    ("automation", "Send reminders and digests",
     "When off, the bot answers students but never messages them first."),
    ("backup_to_telegram", "Send the daily backup to me in Telegram",
     "Puts a copy of the whole database in your chat history - a fair trade "
     "against losing it, but it is a copy of everybody's data."),
]


def save_settings(values, switches):
    """Write the teacher's settings, keeping the secrets untouched."""
    own = os.environ.get("DATA_DIR")
    path = os.path.join(own, "config.json") if own else CONFIG_PATH
    current = {}
    if os.path.exists(path):
        with open(path) as fh:
            current = json.load(fh)
    for key, _label, _unit, _help in EDITABLE:
        if key in values and str(values[key]).strip().lstrip("-").isdigit():
            current[key] = int(values[key])
    for key, _label, _help in SWITCHES:
        current[key] = bool(switches.get(key))
    tmp = path + ".new"
    with open(tmp, "w") as fh:
        json.dump(current, fh, indent=2)
    os.replace(tmp, path)          # never leave a half-written config behind
    return current


def purge(db, what, days=None):
    """Throw something away, and say what went. Never touches the database."""
    gone = freed = 0

    def drop(path):
        nonlocal gone, freed
        try:
            freed += os.path.getsize(path)
            os.remove(path)
            gone += 1
        except OSError:
            pass

    if what == "audio":
        for root, _d, files in os.walk(AUDIO_DIR):
            for f in files:
                drop(os.path.join(root, f))
    elif what == "music":
        for root, _d, files in os.walk(MUSIC_DIR):
            for f in files:
                drop(os.path.join(root, f))
        db.execute("DELETE FROM songs") if table_exists(db, "songs") else None
        db.commit()
    elif what == "backups":
        folder = os.path.join(DATA_DIR, "backups")
        if os.path.isdir(folder):
            for f in sorted(os.listdir(folder))[:-1]:     # keep the newest
                drop(os.path.join(folder, f))
    elif what == "photos":
        # only ones that can be fetched back, and only when asked for a window
        cutoff = iso(now() - timedelta(days=int(days or 30)))
        for r in db.execute(
                "SELECT f.id, f.filename FROM files f"
                " JOIN submissions s ON s.id = f.submission_id"
                " WHERE f.telegram_file_id IS NOT NULL AND f.offloaded = 0"
                "   AND s.created_at < ?", (cutoff,)).fetchall():
            drop(os.path.join(UPLOAD_DIR, r["filename"]))
            db.execute("UPDATE files SET offloaded=1 WHERE id=?", (r["id"],))
        db.commit()
    else:
        return "nothing to do"
    return "%d file(s), %s freed" % (gone, human_size(freed))


def password_worry(cfg=None):
    """Say so when the one key to everything is a weak one.

    One password opens the whole dashboard: every student's name, their
    photographs, their scores, and a download of the entire database. It is
    never printed here, only measured.
    """
    cfg = cfg or load_config()
    pw = cfg.get("teacher_password") or ""
    if pw == "changeme" or not pw:
        return "The teacher password is still the example one."
    if len(pw) < 12:
        return ("The teacher password is %d characters. Three or four "
                "unrelated words would be far harder to guess and easier to "
                "type." % len(pw))
    if not os.environ.get("TEACHER_PASSWORD"):
        return ("The password is in config.json rather than the host's own "
                "settings, so changing it needs a deploy.")
    return ""


def reissue_token(db, student_id):
    """Give a student a new private link, and make the old one dead.

    A link is a password that never changes and gets forwarded. Until now
    there was no way to take one back: a student who shared theirs had shared
    their work and their scores for good.
    """
    token = secrets.token_urlsafe(16)
    db.execute("UPDATE students SET token=? WHERE id=?", (token, student_id))
    db.commit()
    return token


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
    seed_prompts(db)
    seed_coursebook(db)
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

    # A word answered before it was due does not advance the streak. Spacing is
    # the whole method: remembering a word you saw a minute ago proves nothing,
    # and a student who kept pressing practise could walk a word to "known" in
    # an afternoon. Getting it wrong still counts, and still resets it.
    due = row and row["next_due"] and parse(row["next_due"]) <= now()
    early = bool(row) and not due
    if not was_correct:
        streak = 0
    elif early:
        streak = row["streak"]
    else:
        streak = (row["streak"] if row else 0) + 1

    if was_correct and early:
        days = None                       # leave the date alone; it is not due yet
    else:
        days = INTERVALS[min(streak, len(INTERVALS) - 1)] if was_correct else 1
    db.execute(
        "INSERT INTO word_progress (student_id, word_id, seen, correct, streak,"
        " next_due, last_seen) VALUES (?,?,?,?,?,?,?)"
        " ON CONFLICT(student_id, word_id) DO UPDATE SET seen=excluded.seen,"
        " correct=excluded.correct, streak=excluded.streak,"
        " next_due=excluded.next_due, last_seen=excluded.last_seen",
        (student_id, word_id, seen, correct, streak,
         iso(now() + timedelta(days=days)) if days is not None
         else row["next_due"], iso(now())),
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


def four_options(word, pool):
    """The four answers a question offers, shuffled.

    A grammar question brings its own wrong answers; a vocabulary word borrows
    three meanings from the other words on its list, which keeps them plausible.
    """
    own = []
    if "options" in word.keys() and word["options"]:
        try:
            own = [str(x) for x in json.loads(word["options"]) if str(x).strip()]
        except ValueError:
            own = []
    if own:
        options = own[:3] + [word["translation"]]
    else:
        others = [t for t in pool if t != word["translation"]]
        random.shuffle(others)
        options = others[:3] + [word["translation"]]
    random.shuffle(options)
    return options


def make_game(db, group_id, list_id, q_count=10, seconds=20):
    """Draw the questions up front, so the game cannot stall mid-round.

    Wrong options come from other words on the same list, which makes them
    plausible rather than absurd - a student has to actually know the word.
    """
    words = db.execute(
        "SELECT id, term, translation, options FROM words WHERE list_id=? ORDER BY id",
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
        options = four_options(w, pool)
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


def advance_game(db, game_id, expect_state=None, expect_index=None):
    """Lobby -> question -> reveal -> question ... -> done.

    A caller may say which step it thinks it is on. If the game has already
    moved past that - a second board open in another window, a double press,
    a timer firing just as the button is hit - the request is ignored rather
    than skipping a question nobody has seen.
    """
    g = db.execute("SELECT * FROM games WHERE id=?", (game_id,)).fetchone()
    if not g or g["state"] == "done":
        return
    if expect_state is not None and g["state"] != expect_state:
        return
    if expect_index is not None and g["q_index"] != expect_index:
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


# ------------------------------------------------------------- solo play
#
# The live game needs the teacher to host it. Solo play is the same game with
# nobody at the front: a student picks a list and plays a round alone.
#
# It is deliberately kept out of the league. What makes its ranking fair:
#   - the clock is the server's. The phone asks for a question, the server
#     notes the moment it handed it over, and the speed bonus is measured from
#     there - so a student cannot slow the clock or send an answer "early";
#   - every round is the same length and draws its questions at random from
#     the list, so learning one round's order by heart gains nothing;
#   - the tables are for this week only and for your own class only, so a
#     student who joins on Thursday is not already hopelessly behind;
#   - the week's champion is whoever has mastered the most lists, not whoever
#     replayed one list the most. Replaying helps you learn; it cannot buy rank.

SOLO_ROUND = 20          # questions in a round, or the whole list if shorter
SOLO_SECONDS = 20        # per question, the same as the live game
SOLO_PASS = 90           # per cent right to pass a step: 18 out of 20
SOLO_MASTERED = SOLO_PASS   # the weekly table counts a passed step as mastered


def week_start(cfg=None):
    """Monday 00:00 in the teacher's timezone, as a UTC timestamp string."""
    cfg = cfg or load_config()
    off = timedelta(hours=cfg["timezone_offset_hours"])
    local = now() + off
    monday = (local - timedelta(days=local.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0)
    return iso(monday - off)


def play_lists(db, student, kind):
    """The lists this student can play.

    Switched on, of this kind, for their class or for every class, and at
    their level or at no level in particular. A list with no level set stays
    visible to everybody, so nothing disappears until it is filed.
    """
    level = level_of(db, student["group_id"])
    return db.execute(
        "SELECT l.*, (SELECT COUNT(*) FROM words w WHERE w.list_id=l.id) n"
        " FROM word_lists l WHERE l.active=1 AND l.kind=?"
        " AND (l.group_id IS NULL OR l.group_id=?)"
        " AND (l.level_id IS NULL OR l.level_id=?"
        "      OR ',' || IFNULL(l.extra_levels, '') || ',' LIKE '%,' || ? || ',%')"
        " AND (SELECT COUNT(*) FROM words w WHERE w.list_id=l.id) >= 4"
        " ORDER BY l.id DESC",
        (kind, student["group_id"], level, level)).fetchall()


def pass_mark(n):
    """How many of n questions must be right to pass: 18 out of 20."""
    return -(-n * SOLO_PASS // 100)


def passed_lists(db, student_id):
    """Every list this student has ever passed. Progress is kept for good:
    a step you have earned is not taken back on Monday."""
    return {r["list_id"] for r in db.execute(
        "SELECT list_id FROM solo_runs WHERE student_id=? AND finished_at IS NOT NULL"
        " AND correct * 100 >= q_count * ?", (student_id, SOLO_PASS))}


def _order_key(l):
    unit = (l["unit"] or "").strip()
    return (l["step"] or 0, int(unit) if unit.isdigit() else 9999, l["id"])


def play_chain(db, student, kind, source=None):
    """The ladder: the lists in order, each locked until the one before it is passed.

    This is the career: step one is open to everybody, and every step after it
    has to be earned. The lock is here, not only in the page, so typing a
    list's number into the address bar does not skip it.
    """
    lists = [l for l in play_lists(db, student, kind)
             if source is None or (l["source"] or "") == source]
    lists.sort(key=_order_key)
    passed = passed_lists(db, student["id"])
    out, open_next = [], True
    for i, l in enumerate(lists):
        done = l["id"] in passed
        out.append({"list": l, "step": i + 1, "passed": done, "unlocked": open_next,
                    "n": l["n"], "need": pass_mark(min(SOLO_ROUND, l["n"]))})
        open_next = done                       # the next step waits for this one
    return out


def play_books(db, student, kind="vocab"):
    """Vocabulary is filed by book; each book is its own ladder."""
    seen, books = set(), []
    for l in sorted(play_lists(db, student, kind), key=_order_key):
        name = (l["source"] or "").strip()
        if name in seen:
            continue
        seen.add(name)
        chain = play_chain(db, student, kind, name)
        books.append({"source": name, "title": name or "Other lists",
                      "steps": len(chain),
                      "passed": sum(1 for c in chain if c["passed"])})
    return books


def can_play(db, student, list_id):
    """Playable only if it is this student's list and its step is unlocked."""
    row = db.execute("SELECT kind, source FROM word_lists WHERE id=?",
                     (list_id,)).fetchone()
    if not row:
        return False
    chain = play_chain(db, student, row["kind"], (row["source"] or "").strip())
    return any(c["list"]["id"] == list_id and c["unlocked"] for c in chain)


def start_solo(db, student, list_id, q_count=SOLO_ROUND, seconds=SOLO_SECONDS):
    """A fresh round. An unfinished one on the same list is abandoned, not resumed:
    resuming would let a student peek at a question, leave, and come back."""
    if not can_play(db, student, list_id):
        return None
    words = db.execute("SELECT * FROM words WHERE list_id=? ORDER BY id",
                       (list_id,)).fetchall()
    picked = list(words)
    random.shuffle(picked)
    picked = picked[:min(q_count, len(picked))]
    rid = db.execute(
        "INSERT INTO solo_runs (student_id, list_id, q_count, seconds, started_at)"
        " VALUES (?,?,?,?,?)",
        (student["id"], list_id, len(picked), seconds, iso(now()))).lastrowid
    pool = [w["translation"] for w in words]
    for i, w in enumerate(picked):
        options = four_options(w, pool)
        db.execute("INSERT INTO solo_questions (run_id, ord, word_id, options, answer)"
                   " VALUES (?,?,?,?,?)",
                   (rid, i, w["id"], json.dumps(options, ensure_ascii=False),
                    options.index(w["translation"])))
    db.commit()
    return rid


def _solo_run(db, run_id, student_id):
    return db.execute("SELECT * FROM solo_runs WHERE id=? AND student_id=?",
                      (run_id, student_id)).fetchone()


def _solo_timeout(db, run):
    """A question left past its time counts as missed: nothing to gain by waiting."""
    q = db.execute("SELECT * FROM solo_questions WHERE run_id=? AND choice IS NULL"
                   " ORDER BY ord LIMIT 1", (run["id"],)).fetchone()
    if q and q["shown_at"]:
        used = (now() - parse(q["shown_at"])).total_seconds()
        if used > run["seconds"] + 2:
            db.execute("UPDATE solo_questions SET choice=-1, correct=0, points=0"
                       " WHERE id=?", (q["id"],))
            db.commit()
            return True
    return False


def _solo_finish_if_done(db, run):
    left = db.execute("SELECT COUNT(*) c FROM solo_questions WHERE run_id=?"
                      " AND choice IS NULL", (run["id"],)).fetchone()["c"]
    if left == 0 and not run["finished_at"]:
        t = db.execute("SELECT COALESCE(SUM(points),0) p, COALESCE(SUM(correct),0) c"
                       " FROM solo_questions WHERE run_id=?", (run["id"],)).fetchone()
        db.execute("UPDATE solo_runs SET score=?, correct=?, finished_at=? WHERE id=?",
                   (t["p"], t["c"], iso(now()), run["id"]))
        db.commit()


def solo_state(db, run_id, student_id):
    """What the phone should show now. Serving a question starts its clock."""
    run = _solo_run(db, run_id, student_id)
    if not run:
        return None
    while _solo_timeout(db, run):
        pass
    _solo_finish_if_done(db, run)
    run = _solo_run(db, run_id, student_id)
    done = db.execute("SELECT * FROM solo_questions WHERE run_id=? AND choice IS NOT NULL"
                      " ORDER BY ord", (run_id,)).fetchall()
    score = sum(q["points"] for q in done)
    streak = 0
    for q in reversed(done):
        if not q["correct"]:
            break
        streak += 1
    base = {"total": run["q_count"], "number": len(done), "score": score,
            "streak": streak, "list_id": run["list_id"]}
    if run["finished_at"]:
        review = []
        for q in done:
            w = db.execute("SELECT term, translation FROM words WHERE id=?",
                           (q["word_id"],)).fetchone()
            opts = json.loads(q["options"])
            review.append({"term": w["term"], "answer": w["translation"],
                           "given": opts[q["choice"]] if q["choice"] >= 0 else None,
                           "right": bool(q["correct"])})
        need = pass_mark(run["q_count"])
        base.update(state="done", correct=run["correct"], score=run["score"],
                    review=review, need=need, passed=run["correct"] >= need)
        return base
    q = db.execute("SELECT * FROM solo_questions WHERE run_id=? AND choice IS NULL"
                   " ORDER BY ord LIMIT 1", (run_id,)).fetchone()
    if not q["shown_at"]:
        db.execute("UPDATE solo_questions SET shown_at=? WHERE id=?", (iso(now()), q["id"]))
        db.commit()
        q = db.execute("SELECT * FROM solo_questions WHERE id=?", (q["id"],)).fetchone()
    used = (now() - parse(q["shown_at"])).total_seconds()
    w = db.execute("SELECT term FROM words WHERE id=?", (q["word_id"],)).fetchone()
    base.update(state="question", q=q["ord"], term=w["term"],
                options=json.loads(q["options"]),
                left=max(0, int(round(run["seconds"] - used))), seconds=run["seconds"])
    return base


def answer_solo(db, run_id, student_id, ord_, choice):
    """Mark one answer against the server's clock. One answer per question."""
    run = _solo_run(db, run_id, student_id)
    if not run or run["finished_at"]:
        return None
    q = db.execute("SELECT * FROM solo_questions WHERE run_id=? AND choice IS NULL"
                   " ORDER BY ord LIMIT 1", (run_id,)).fetchone()
    if not q or q["ord"] != ord_ or not q["shown_at"]:
        return None                       # not the question on screen
    used = (now() - parse(q["shown_at"])).total_seconds()
    left = run["seconds"] - used
    right = left > 0 and choice == q["answer"]
    points = GAME_BASE + int(GAME_SPEED * (left / float(run["seconds"]))) if right else 0
    db.execute("UPDATE solo_questions SET choice=?, correct=?, points=? WHERE id=?",
               (choice if left > 0 else -1, 1 if right else 0, points, q["id"]))
    db.commit()
    record_answer(db, student_id, q["word_id"], right)   # feeds the bot's revision, as the live game does
    _solo_finish_if_done(db, run)
    word = db.execute("SELECT translation FROM words WHERE id=?", (q["word_id"],)).fetchone()
    return {"correct": right, "points": points, "answer": q["answer"],
            "answer_text": word["translation"], "late": left <= 0}


def solo_list_board(db, list_id, group_id, since=None):
    """This week's best round on one list, for each classmate who played it."""
    since = since or week_start()
    return db.execute(
        "SELECT s.id, s.name, s.avatar, MAX(r.score) best,"
        " MAX(100 * r.correct / r.q_count) pct, COUNT(*) rounds"
        " FROM solo_runs r JOIN students s ON s.id=r.student_id"
        " WHERE r.list_id=? AND s.group_id=? AND s.active=1"
        " AND r.finished_at IS NOT NULL AND r.finished_at >= ?"
        " GROUP BY s.id ORDER BY best DESC, s.name", (list_id, group_id, since)).fetchall()


def solo_week_board(db, group_id, since=None):
    """The week's champions: most lists mastered, then the best points across them.

    Mastering a list means one round of at least SOLO_MASTERED per cent right.
    Each list counts once however often it is replayed, so the way up the
    table is to learn more lists, not to grind the same one."""
    since = since or week_start()
    rows = db.execute(
        "SELECT r.student_id, r.list_id, MAX(r.score) best,"
        " MAX(100 * r.correct / r.q_count) pct"
        " FROM solo_runs r JOIN students s ON s.id=r.student_id"
        " WHERE s.group_id=? AND s.active=1 AND r.finished_at IS NOT NULL"
        " AND r.finished_at >= ? GROUP BY r.student_id, r.list_id",
        (group_id, since)).fetchall()
    per = {}
    for r in rows:
        d = per.setdefault(r["student_id"], {"mastered": 0, "points": 0, "lists": 0})
        d["lists"] += 1
        d["points"] += r["best"]
        if r["pct"] >= SOLO_MASTERED:
            d["mastered"] += 1
    out = []
    for sid, d in per.items():
        st = db.execute("SELECT id, name, avatar FROM students WHERE id=?", (sid,)).fetchone()
        out.append(dict(d, id=sid, name=st["name"], avatar=st["avatar"]))
    out.sort(key=lambda d: (-d["mastered"], -d["points"], d["name"]))
    return out


def solo_best(db, student_id, list_id, since=None):
    since = since or week_start()
    return db.execute(
        "SELECT MAX(score) best, MAX(100 * correct / q_count) pct, COUNT(*) rounds"
        " FROM solo_runs WHERE student_id=? AND list_id=? AND finished_at IS NOT NULL"
        " AND finished_at >= ?", (student_id, list_id, since)).fetchone()


# ---------------------------------------------------------------- battles
#
# Up to four classmates race through the same ten questions. Everyone runs at
# their own speed and watches the others move along the track, which is where
# the idea came from: the multiplayer races in Blur.
#
# Like solo play, a battle never touches the league. It keeps its own weekly
# table so that beating a classmate is worth something without letting anyone
# farm points off a weaker friend.

BATTLE_MAX = 4           # cars on the track, as in Blur
BATTLE_ROUND = 10        # questions in a race: short enough to want a rematch
BATTLE_SECONDS = 15      # per question, quicker than solo play
BATTLE_LOBBY_MINS = 20   # a lobby nobody started is stale after this
BATTLE_ONLINE_SECS = 150 # "online now" for the invite list
BATTLE_CODE_LETTERS = "ABCDEFGHJKLMNPQRSTUVWXYZ"   # no I or O: they read as 1 and 0


def touch_student(db, student_id):
    """Remember that this student is on the site, for the invite list."""
    db.execute("UPDATE students SET last_seen=? WHERE id=?", (iso(now()), student_id))
    db.commit()


def _battle_code(db):
    for _ in range(50):
        code = "".join(random.choice(BATTLE_CODE_LETTERS) for _ in range(4))
        if not db.execute("SELECT 1 FROM battles WHERE code=? AND state<>'done'",
                          (code,)).fetchone():
            return code
    return None


def battle_lists(db, student):
    """Topics a student may race on: everything their class can see.

    Deliberately not the career ladder. A battle earns no step, so letting a
    student race on a step they have not reached yet gives nothing away that
    matters, and it would be a poor challenge if the two of them had to have
    climbed to exactly the same rung.
    """
    out = []
    for kind in ("vocab", "grammar", "exam"):
        out.extend(play_lists(db, student, kind))
    return out


def can_battle_on(db, student, list_id):
    return any(l["id"] == list_id for l in battle_lists(db, student))


def create_battle(db, student, list_id, q_count=BATTLE_ROUND, seconds=BATTLE_SECONDS):
    """Open a lobby and put the host in it. Questions are drawn at the start,
    not now, so a host cannot open a lobby to peek at the questions."""
    if not can_battle_on(db, student, list_id):
        return None
    n = db.execute("SELECT COUNT(*) c FROM words WHERE list_id=?",
                   (list_id,)).fetchone()["c"]
    if n < 4:
        return None
    code = _battle_code(db)
    if not code:
        return None
    bid = db.execute(
        "INSERT INTO battles (code, group_id, list_id, host_id, q_count, seconds,"
        " state, created_at) VALUES (?,?,?,?,?,?,'lobby',?)",
        (code, student["group_id"], list_id, student["id"],
         min(q_count, n), seconds, iso(now()))).lastrowid
    db.execute("INSERT INTO battle_players (battle_id, student_id, joined_at)"
               " VALUES (?,?,?)", (bid, student["id"], iso(now())))
    db.commit()
    return bid


def battle_by_code(db, code):
    return db.execute(
        "SELECT * FROM battles WHERE code=? AND state='lobby'"
        " AND created_at >= ? ORDER BY id DESC LIMIT 1",
        ((code or "").strip().upper(),
         iso(now() - timedelta(minutes=BATTLE_LOBBY_MINS)))).fetchone()


def battle_players(db, battle_id):
    return db.execute(
        "SELECT p.*, s.name, s.avatar FROM battle_players p"
        " JOIN students s ON s.id=p.student_id"
        " WHERE p.battle_id=? ORDER BY p.joined_at, p.id", (battle_id,)).fetchall()


def join_battle(db, student, battle_id):
    """Take a free seat. Full, started, or another class's race: no."""
    b = db.execute("SELECT * FROM battles WHERE id=?", (battle_id,)).fetchone()
    if not b or b["state"] != "lobby":
        return None
    if b["group_id"] is not None and student["group_id"] != b["group_id"]:
        return None
    seats = db.execute("SELECT COUNT(*) c FROM battle_players WHERE battle_id=?",
                       (battle_id,)).fetchone()["c"]
    mine = db.execute("SELECT 1 FROM battle_players WHERE battle_id=? AND student_id=?",
                      (battle_id, student["id"])).fetchone()
    if not mine:
        if seats >= BATTLE_MAX:
            return None
        db.execute("INSERT INTO battle_players (battle_id, student_id, joined_at)"
                   " VALUES (?,?,?)", (battle_id, student["id"], iso(now())))
    db.execute("UPDATE battle_invites SET state='joined'"
               " WHERE battle_id=? AND to_id=? AND state='open'",
               (battle_id, student["id"]))
    db.commit()
    return b["id"]


def leave_battle(db, student, battle_id):
    """Only from the lobby. Leaving a race in progress is just losing it."""
    b = db.execute("SELECT * FROM battles WHERE id=?", (battle_id,)).fetchone()
    if not b or b["state"] != "lobby":
        return False
    db.execute("DELETE FROM battle_players WHERE battle_id=? AND student_id=?",
               (battle_id, student["id"]))
    if student["id"] == b["host_id"]:
        db.execute("UPDATE battles SET state='done', finished_at=? WHERE id=?",
                   (iso(now()), battle_id))      # the host left: the lobby closes
    db.commit()
    return True


def classmates_for_battle(db, student):
    """Who this student can invite, the ones on the site right now first."""
    cutoff = iso(now() - timedelta(seconds=BATTLE_ONLINE_SECS))
    rows = db.execute(
        "SELECT id, name, avatar, last_seen FROM students"
        " WHERE active=1 AND id<>? AND group_id IS ? ORDER BY name",
        (student["id"], student["group_id"])).fetchall()
    return [{"id": r["id"], "name": r["name"], "avatar": r["avatar"],
             "online": bool(r["last_seen"] and r["last_seen"] >= cutoff)}
            for r in rows]


def invite_to_battle(db, student, battle_id, to_id):
    b = db.execute("SELECT * FROM battles WHERE id=? AND state='lobby'",
                   (battle_id,)).fetchone()
    if not b:
        return False
    if not db.execute("SELECT 1 FROM battle_players WHERE battle_id=? AND student_id=?",
                      (battle_id, student["id"])).fetchone():
        return False                    # only someone already in the lobby invites
    other = db.execute("SELECT * FROM students WHERE id=? AND active=1",
                       (to_id,)).fetchone()
    if not other or other["group_id"] != student["group_id"]:
        return False
    db.execute("INSERT OR IGNORE INTO battle_invites (battle_id, from_id, to_id,"
               " created_at) VALUES (?,?,?,?)",
               (battle_id, student["id"], to_id, iso(now())))
    db.commit()
    return True


def open_invites(db, student):
    """Invitations waiting for this student, newest first."""
    since = iso(now() - timedelta(minutes=BATTLE_LOBBY_MINS))
    return db.execute(
        "SELECT i.*, s.name from_name, b.code, b.id battle_id, l.title"
        " FROM battle_invites i"
        " JOIN battles b ON b.id=i.battle_id"
        " JOIN students s ON s.id=i.from_id"
        " JOIN word_lists l ON l.id=b.list_id"
        " WHERE i.to_id=? AND i.state='open' AND b.state='lobby'"
        " AND i.created_at >= ? ORDER BY i.id DESC", (student["id"], since)).fetchall()


def decline_invite(db, student, battle_id):
    db.execute("UPDATE battle_invites SET state='declined'"
               " WHERE battle_id=? AND to_id=?", (battle_id, student["id"]))
    db.commit()


def my_open_battle(db, student):
    """A lobby or a race this student is already in, so Play can point at it."""
    since = iso(now() - timedelta(minutes=BATTLE_LOBBY_MINS))
    return db.execute(
        "SELECT b.* FROM battles b JOIN battle_players p ON p.battle_id=b.id"
        " WHERE p.student_id=? AND b.state IN ('lobby','racing')"
        " AND b.created_at >= ? ORDER BY b.id DESC LIMIT 1",
        (student["id"], since)).fetchone()


def start_battle(db, battle_id, host_id):
    """The host drops the flag. Questions are drawn now, once, for everybody."""
    b = db.execute("SELECT * FROM battles WHERE id=? AND host_id=? AND state='lobby'",
                   (battle_id, host_id)).fetchone()
    if not b:
        return False
    players = battle_players(db, battle_id)
    if len(players) < 2:
        return False                    # a race needs somebody to race
    words = db.execute("SELECT * FROM words WHERE list_id=? ORDER BY id",
                       (b["list_id"],)).fetchall()
    picked = list(words)
    random.shuffle(picked)
    picked = picked[:min(b["q_count"], len(picked))]
    pool = [w["translation"] for w in words]
    for i, w in enumerate(picked):
        options = four_options(w, pool)
        db.execute("INSERT INTO battle_questions (battle_id, ord, word_id, options,"
                   " answer) VALUES (?,?,?,?,?)",
                   (battle_id, i, w["id"], json.dumps(options, ensure_ascii=False),
                    options.index(w["translation"])))
    db.execute("UPDATE battles SET state='racing', q_count=?, started_at=? WHERE id=?",
               (len(picked), iso(now()), battle_id))
    db.commit()
    return True


def _battle_deadline(b):
    """When the flag falls whatever anyone has left: the whole track, plus a
    little, so a player who loses their signal cannot hold the others up."""
    return parse(b["started_at"]) + timedelta(
        seconds=b["q_count"] * (b["seconds"] + 3) + 20)


def _battle_timeout(db, b, student_id):
    """A question left past its time is missed, the same as in solo play."""
    a = db.execute("SELECT * FROM battle_answers WHERE battle_id=? AND student_id=?"
                   " AND choice IS NULL ORDER BY ord LIMIT 1",
                   (b["id"], student_id)).fetchone()
    if a and a["shown_at"]:
        used = (now() - parse(a["shown_at"])).total_seconds()
        if used > b["seconds"] + 2:
            db.execute("UPDATE battle_answers SET choice=-1, correct=0, points=0"
                       " WHERE id=?", (a["id"],))
            db.commit()
            return True
    return False


def _battle_tally(db, b, student_id):
    t = db.execute(
        "SELECT COUNT(*) n, COALESCE(SUM(points),0) p, COALESCE(SUM(correct),0) c"
        " FROM battle_answers WHERE battle_id=? AND student_id=? AND choice IS NOT NULL",
        (b["id"], student_id)).fetchone()
    db.execute("UPDATE battle_players SET answered=?, score=?, correct=?"
               " WHERE battle_id=? AND student_id=?",
               (t["n"], t["p"], t["c"], b["id"], student_id))
    if t["n"] >= b["q_count"]:
        db.execute("UPDATE battle_players SET finished_at=COALESCE(finished_at,?)"
                   " WHERE battle_id=? AND student_id=?",
                   (iso(now()), b["id"], student_id))
    db.commit()


def _battle_finish_if_done(db, b):
    """The race ends when every car is home, or when the flag falls."""
    if b["state"] != "racing":
        return
    left = db.execute("SELECT COUNT(*) c FROM battle_players"
                      " WHERE battle_id=? AND finished_at IS NULL",
                      (b["id"],)).fetchone()["c"]
    over = now() >= _battle_deadline(b)
    if left and not over:
        return
    if over:
        # anyone still out on the track is marked home where they stood
        db.execute("UPDATE battle_players SET finished_at=? WHERE battle_id=?"
                   " AND finished_at IS NULL", (iso(now()), b["id"]))
    # places: most points wins; a tie goes to whoever got there first
    rows = db.execute(
        "SELECT student_id FROM battle_players WHERE battle_id=?"
        " ORDER BY score DESC, correct DESC, finished_at ASC, id ASC",
        (b["id"],)).fetchall()
    for i, r in enumerate(rows):
        db.execute("UPDATE battle_players SET place=? WHERE battle_id=? AND student_id=?",
                   (i + 1, b["id"], r["student_id"]))
    db.execute("UPDATE battles SET state='done', finished_at=? WHERE id=?",
               (iso(now()), b["id"]))
    db.commit()


def battle_state(db, battle_id, student_id):
    """Everything the phone draws: the lobby, the track, or the finish."""
    b = db.execute("SELECT b.*, l.title, l.kind FROM battles b"
                   " JOIN word_lists l ON l.id=b.list_id WHERE b.id=?",
                   (battle_id,)).fetchone()
    if not b:
        return None
    if not db.execute("SELECT 1 FROM battle_players WHERE battle_id=? AND student_id=?",
                      (battle_id, student_id)).fetchone():
        return None
    if b["state"] == "racing":
        while _battle_timeout(db, b, student_id):
            pass
        _battle_tally(db, b, student_id)
        _battle_finish_if_done(db, b)
        b = db.execute("SELECT b.*, l.title, l.kind FROM battles b"
                       " JOIN word_lists l ON l.id=b.list_id WHERE b.id=?",
                       (battle_id,)).fetchone()
    players = battle_players(db, battle_id)
    track = [{"id": p["student_id"], "name": p["name"], "me": p["student_id"] == student_id,
              "at": p["answered"], "score": p["score"], "correct": p["correct"],
              "place": p["place"], "home": bool(p["finished_at"])} for p in players]
    track.sort(key=lambda t: (-(t["place"] or 99) if b["state"] == "done" else 0,
                              -t["score"], -t["at"]))
    if b["state"] == "done":
        track.sort(key=lambda t: t["place"] or 99)
    base = {"state": b["state"], "code": b["code"], "title": b["title"],
            "kind": b["kind"], "total": b["q_count"], "seconds": b["seconds"],
            "host": b["host_id"] == student_id, "track": track,
            "list_id": b["list_id"], "id": b["id"]}
    if b["state"] == "lobby":
        base["can_start"] = b["host_id"] == student_id and len(players) >= 2
        base["seats"] = BATTLE_MAX
        return base
    if b["state"] == "done":
        me = next((p for p in players if p["student_id"] == student_id), None)
        base.update(place=me["place"] if me else None,
                    score=me["score"] if me else 0,
                    correct=me["correct"] if me else 0,
                    review=_battle_review(db, battle_id, student_id))
        return base
    # racing: the question this player is on
    a = db.execute("SELECT * FROM battle_answers WHERE battle_id=? AND student_id=?"
                   " AND choice IS NULL ORDER BY ord LIMIT 1",
                   (battle_id, student_id)).fetchone()
    if not a:
        done = db.execute("SELECT COUNT(*) c FROM battle_answers WHERE battle_id=?"
                          " AND student_id=?", (battle_id, student_id)).fetchone()["c"]
        if done >= b["q_count"]:
            base["state"] = "waiting"       # home, watching the others come in
            base["left_on_track"] = sum(1 for t in track if not t["home"])
            return base
        q = db.execute("SELECT * FROM battle_questions WHERE battle_id=? AND ord=?",
                       (battle_id, done)).fetchone()
        db.execute("INSERT INTO battle_answers (battle_id, student_id, ord, shown_at)"
                   " VALUES (?,?,?,?)", (battle_id, student_id, q["ord"], iso(now())))
        db.commit()
        a = db.execute("SELECT * FROM battle_answers WHERE battle_id=? AND student_id=?"
                       " AND ord=?", (battle_id, student_id, q["ord"])).fetchone()
    q = db.execute("SELECT * FROM battle_questions WHERE battle_id=? AND ord=?",
                   (battle_id, a["ord"])).fetchone()
    if not a["shown_at"]:
        db.execute("UPDATE battle_answers SET shown_at=? WHERE id=?",
                   (iso(now()), a["id"]))
        db.commit()
        a = db.execute("SELECT * FROM battle_answers WHERE id=?", (a["id"],)).fetchone()
    used = (now() - parse(a["shown_at"])).total_seconds()
    w = db.execute("SELECT term FROM words WHERE id=?", (q["word_id"],)).fetchone()
    base.update(q=q["ord"], term=w["term"], options=json.loads(q["options"]),
                left=max(0, int(round(b["seconds"] - used))))
    return base


def _battle_review(db, battle_id, student_id):
    rows = db.execute(
        "SELECT a.choice, a.correct, q.options, q.answer, w.term, w.translation"
        " FROM battle_answers a"
        " JOIN battle_questions q ON q.battle_id=a.battle_id AND q.ord=a.ord"
        " JOIN words w ON w.id=q.word_id"
        " WHERE a.battle_id=? AND a.student_id=? AND a.choice IS NOT NULL"
        " ORDER BY a.ord", (battle_id, student_id)).fetchall()
    out = []
    for r in rows:
        opts = json.loads(r["options"])
        out.append({"term": r["term"], "answer": r["translation"],
                    "given": opts[r["choice"]] if r["choice"] >= 0 else None,
                    "right": bool(r["correct"])})
    return out


def answer_battle(db, battle_id, student_id, ord_, choice):
    """One answer, against the server's clock. Scored as solo play is."""
    b = db.execute("SELECT * FROM battles WHERE id=?", (battle_id,)).fetchone()
    if not b or b["state"] != "racing":
        return None
    a = db.execute("SELECT * FROM battle_answers WHERE battle_id=? AND student_id=?"
                   " AND choice IS NULL ORDER BY ord LIMIT 1",
                   (battle_id, student_id)).fetchone()
    if not a or a["ord"] != ord_ or not a["shown_at"]:
        return None                     # not the question on their screen
    q = db.execute("SELECT * FROM battle_questions WHERE battle_id=? AND ord=?",
                   (battle_id, ord_)).fetchone()
    used = (now() - parse(a["shown_at"])).total_seconds()
    left = b["seconds"] - used
    right = left > 0 and choice == q["answer"]
    points = GAME_BASE + int(GAME_SPEED * (left / float(b["seconds"]))) if right else 0
    db.execute("UPDATE battle_answers SET choice=?, correct=?, points=? WHERE id=?",
               (choice if left > 0 else -1, 1 if right else 0, points, a["id"]))
    db.commit()
    record_answer(db, student_id, q["word_id"], right)
    _battle_tally(db, b, student_id)
    _battle_finish_if_done(db, b)
    word = db.execute("SELECT translation FROM words WHERE id=?",
                      (q["word_id"],)).fetchone()
    return {"correct": right, "points": points, "answer": q["answer"],
            "answer_text": word["translation"], "late": left <= 0}


def battle_week_board(db, group_id, since=None):
    """This week's racers. Its own table: the league never sees any of this."""
    since = since or week_start()
    return db.execute(
        "SELECT s.id, s.name, s.avatar,"
        "       COUNT(*) races,"
        "       COALESCE(SUM(CASE WHEN p.place=1 THEN 1 ELSE 0 END),0) wins,"
        "       COALESCE(SUM(p.score),0) points"
        " FROM battle_players p"
        " JOIN battles b ON b.id=p.battle_id"
        " JOIN students s ON s.id=p.student_id"
        " WHERE b.state='done' AND b.finished_at >= ? AND s.active=1"
        "   AND s.group_id IS ?"
        " GROUP BY s.id, s.name, s.avatar"
        " ORDER BY wins DESC, points DESC, races ASC", (since, group_id)).fetchall()


def battle_record(db, student_id, since=None):
    """One student's week: races, wins, best finish."""
    since = since or week_start()
    r = db.execute(
        "SELECT COUNT(*) races,"
        "       COALESCE(SUM(CASE WHEN p.place=1 THEN 1 ELSE 0 END),0) wins,"
        "       COALESCE(SUM(p.score),0) points"
        " FROM battle_players p JOIN battles b ON b.id=p.battle_id"
        " WHERE p.student_id=? AND b.state='done' AND b.finished_at >= ?",
        (student_id, since)).fetchone()
    return {"races": r["races"], "wins": r["wins"], "points": r["points"]}


# --------------------------------------------------------------- reteaching
#
# Every answer a student gives - in Play, in a battle, in the live game -
# writes a row to word_progress. Nothing read it back to the teacher, so a
# class could fail the same word ninety times and nobody would know unless
# they happened to be standing there.
#
# These three questions are what a teacher would ask if they could hold
# eighty-five students in their head at once:
#   which words is this class getting wrong?
#   which steps are they failing?
#   who is quietly slipping while their homework still looks fine?

RETEACH_MIN_SEEN = 8      # answers before a word can be called hard
RETEACH_MIN_WHO = 3       # students, so one bad night is not a finding
RETEACH_HARD = 60         # per cent right, at or below which it needs work
OVERDUE_MANY = 25         # revision words past due before it is worth saying
QUIET_DAYS = 7            # days away from Play before a student is "quiet"


def reteach_words(db, group_id, limit=20, min_seen=RETEACH_MIN_SEEN,
                  min_who=RETEACH_MIN_WHO):
    """The words this class gets wrong most, worst first.

    A word only counts once enough of the class has met it enough times:
    one student having a bad evening is not a lesson plan.
    """
    rows = db.execute(
        "SELECT w.id, w.term, w.translation, l.title list_title, l.kind,"
        "       SUM(p.seen) seen, SUM(p.correct) correct,"
        "       COUNT(DISTINCT p.student_id) who"
        "  FROM word_progress p"
        "  JOIN words w ON w.id = p.word_id"
        "  JOIN word_lists l ON l.id = w.list_id"
        "  JOIN students s ON s.id = p.student_id"
        " WHERE s.active = 1 AND s.group_id IS ?"
        " GROUP BY w.id"
        # the aggregates are spelled out again rather than using the aliases:
        # an unqualified `seen` in HAVING resolves to word_progress.seen, one
        # student's count, not the class's total
        " HAVING SUM(p.seen) >= ? AND COUNT(DISTINCT p.student_id) >= ?"
        " ORDER BY (correct * 1.0 / seen), seen DESC"
        " LIMIT ?", (group_id, min_seen, min_who, limit)).fetchall()
    out = []
    for r in rows:
        pct = int(round(100.0 * r["correct"] / r["seen"]))
        if pct > RETEACH_HARD:
            continue
        out.append({"word_id": r["id"], "term": r["term"],
                    "answer": r["translation"], "list": r["list_title"],
                    "kind": r["kind"], "seen": r["seen"],
                    "correct": r["correct"], "pct": pct, "who": r["who"]})
    return out


def reteach_steps(db, group_id, limit=10, min_runs=4):
    """The Play steps this class does worst on.

    A word tells you what to put on the board; a step tells you which lesson
    did not land.
    """
    rows = db.execute(
        "SELECT l.id, l.title, l.kind, l.source,"
        "       COUNT(*) runs, COUNT(DISTINCT r.student_id) who,"
        "       AVG(r.correct * 100.0 / r.q_count) pct,"
        "       SUM(CASE WHEN r.correct * 100.0 / r.q_count >= ?"
        "                THEN 1 ELSE 0 END) passes"
        "  FROM solo_runs r"
        "  JOIN word_lists l ON l.id = r.list_id"
        "  JOIN students s ON s.id = r.student_id"
        " WHERE r.finished_at IS NOT NULL AND s.active = 1 AND s.group_id IS ?"
        " GROUP BY l.id"
        " HAVING COUNT(*) >= ?"
        " ORDER BY pct"
        " LIMIT ?", (SOLO_PASS, group_id, min_runs, limit)).fetchall()
    return [{"list_id": r["id"], "title": r["title"], "kind": r["kind"],
             "book": (r["source"] or "").strip(), "runs": r["runs"],
             "who": r["who"], "pct": int(round(r["pct"])),
             "passes": r["passes"]} for r in rows]


def quiet_strugglers(db, group_id):
    """Students the homework view cannot see.

    view_overview finds the ones who stop handing work in. These are the
    opposite: the homework arrives, so nothing is flagged, but the words are
    not going in. Ordered worst first.
    """
    now_iso = iso(now())
    quiet_before = iso(now() - timedelta(days=QUIET_DAYS))
    out = []
    for s in db.execute(
            "SELECT * FROM students WHERE active=1 AND group_id IS ?"
            " ORDER BY name", (group_id,)).fetchall():
        p = db.execute(
            "SELECT COUNT(*) words, COALESCE(SUM(seen),0) seen,"
            "       COALESCE(SUM(correct),0) correct,"
            "       SUM(CASE WHEN next_due <= ? THEN 1 ELSE 0 END) overdue,"
            "       MAX(last_seen) last"
            "  FROM word_progress WHERE student_id=?",
            (now_iso, s["id"])).fetchone()
        if not p["words"]:
            continue
        pct = int(round(100.0 * p["correct"] / p["seen"])) if p["seen"] else 0
        overdue = p["overdue"] or 0
        quiet = not p["last"] or p["last"] < quiet_before
        stats = student_stats(db, s["id"])
        reasons = []
        if p["seen"] >= 40 and pct <= RETEACH_HARD:
            reasons.append("%d%% right on %d answers" % (pct, p["seen"]))
        if overdue >= OVERDUE_MANY:
            reasons.append("%d words due for revision" % overdue)
        if quiet:
            reasons.append("nothing since %s" % (p["last"] or "never")[:10])
        if not reasons:
            continue
        out.append({"id": s["id"], "name": s["name"], "avatar": s["avatar"],
                    "pct": pct, "seen": p["seen"], "overdue": overdue,
                    "last": p["last"], "quiet": quiet, "reasons": reasons,
                    # the point of the page: homework is fine, so nothing
                    # else on the site is going to mention this student
                    "homework_fine": not stats["at_risk"],
                    "average": stats["average"]})
    out.sort(key=lambda r: (not r["homework_fine"], r["pct"], -r["overdue"]))
    return out


def reteach(db, group_id):
    """Everything the reteaching page needs for one class."""
    return {"words": reteach_words(db, group_id),
            "steps": reteach_steps(db, group_id),
            "students": quiet_strugglers(db, group_id)}


# ------------------------------------------------------------- the cycle
#
# Why a student left is the one fact nobody ever writes down, and it is the
# one the whole retention question rests on. A fixed list matters: free text
# never adds up, and "she moved to Tashkent" and "moved away" have to be the
# same row when you count them.
#
# The split is deliberate. Some reasons are the teacher's to do something
# about and some are not, and a retention rate that mixes them tells the
# teacher off for a family moving city.
LEAVE_REASONS = [
    ("finished", "Finished the course", False),
    ("moved", "Moved away", False),
    ("money", "Could not afford it", False),
    ("timetable", "Timetable stopped working", False),
    ("health", "Health or family", False),
    ("other_centre", "Went to another centre", True),
    ("progress", "Felt they were not progressing", True),
    ("unhappy", "Unhappy with the class", True),
    ("bored", "Lost interest", True),
    ("unknown", "Just stopped coming", True),
]
REASON_LABEL = {k: label for k, label, _ours in LEAVE_REASONS}
REASON_OURS = {k: ours for k, _label, ours in LEAVE_REASONS}


def the_teacher(db):
    """The one teacher, until there are accounts for others."""
    row = db.execute("SELECT * FROM teachers ORDER BY id LIMIT 1").fetchone()
    if row:
        return row
    cfg = load_config()
    tid = db.execute(
        "INSERT INTO teachers (name, celta, created_at) VALUES (?,0,?)",
        (cfg.get("teacher_name") or "Teacher", iso(now()))).lastrowid
    db.commit()
    return db.execute("SELECT * FROM teachers WHERE id=?", (tid,)).fetchone()


def backfill_enrolments(db):
    """Everybody already on the books is here, and has been since they joined.

    Without this the register would show an empty history and every student
    would look like they arrived the day the feature was built.
    """
    t = the_teacher(db)
    made = 0
    for s in db.execute("SELECT * FROM students WHERE active=1").fetchall():
        has = db.execute("SELECT 1 FROM enrolments WHERE student_id=?",
                         (s["id"],)).fetchone()
        if has:
            continue
        db.execute(
            "INSERT INTO enrolments (student_id, teacher_id, group_id,"
            " started_at, created_at) VALUES (?,?,?,?,?)",
            (s["id"], t["id"], s["group_id"], s["created_at"] or iso(now()),
             iso(now())))
        made += 1
    if made:
        db.commit()
    return made


def current_enrolment(db, student_id):
    return db.execute(
        "SELECT * FROM enrolments WHERE student_id=? AND ended_at IS NULL"
        " ORDER BY id DESC LIMIT 1", (student_id,)).fetchone()


def mark_left(db, student_id, reason, when=None, note=""):
    """Close the student's spell here, and take them off the roll."""
    if reason not in REASON_LABEL:
        return False
    e = current_enrolment(db, student_id)
    if not e:
        t = the_teacher(db)
        s = db.execute("SELECT * FROM students WHERE id=?",
                       (student_id,)).fetchone()
        if not s:
            return False
        e_id = db.execute(
            "INSERT INTO enrolments (student_id, teacher_id, group_id,"
            " started_at, created_at) VALUES (?,?,?,?,?)",
            (student_id, t["id"], s["group_id"], s["created_at"] or iso(now()),
             iso(now()))).lastrowid
    else:
        e_id = e["id"]
    db.execute("UPDATE enrolments SET ended_at=?, reason=?, note=? WHERE id=?",
               (when or iso(now()), reason, (note or "").strip(), e_id))
    db.execute("UPDATE students SET active=0 WHERE id=?", (student_id,))
    db.commit()
    return True


def mark_returned(db, student_id, group_id=None):
    """A student who comes back starts a new spell, not a rewritten old one."""
    s = db.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()
    if not s:
        return False
    if current_enrolment(db, student_id):
        db.execute("UPDATE students SET active=1 WHERE id=?", (student_id,))
        db.commit()
        return True
    t = the_teacher(db)
    db.execute(
        "INSERT INTO enrolments (student_id, teacher_id, group_id, started_at,"
        " created_at) VALUES (?,?,?,?,?)",
        (student_id, t["id"], group_id or s["group_id"], iso(now()), iso(now())))
    db.execute("UPDATE students SET active=1 WHERE id=?", (student_id,))
    db.commit()
    return True


def leavers(db, since=None, group_id=None):
    sql = ("SELECT e.*, s.name, s.avatar, g.name group_name FROM enrolments e"
           " JOIN students s ON s.id=e.student_id"
           " LEFT JOIN groups g ON g.id=e.group_id"
           " WHERE e.ended_at IS NOT NULL")
    args = []
    if since:
        sql += " AND e.ended_at >= ?"; args.append(since)
    if group_id:
        sql += " AND e.group_id=?"; args.append(group_id)
    return db.execute(sql + " ORDER BY e.ended_at DESC", args).fetchall()


def retention(db, since=None, until=None):
    """How many were here, how many went, and how much of it was ours.

    Counted over a window: everybody whose spell overlapped it, and of those
    the ones that ended inside it. A rate over no window at all is only ever
    flattering.
    """
    until = until or iso(now())
    since = since or iso(now() - timedelta(days=90))
    here = db.execute(
        "SELECT COUNT(*) c FROM enrolments"
        " WHERE started_at <= ? AND (ended_at IS NULL OR ended_at >= ?)",
        (until, since)).fetchone()["c"]
    gone = db.execute(
        "SELECT reason, COUNT(*) c FROM enrolments"
        " WHERE ended_at IS NOT NULL AND ended_at >= ? AND ended_at <= ?"
        " GROUP BY reason", (since, until)).fetchall()
    left = sum(r["c"] for r in gone)
    ours = sum(r["c"] for r in gone if REASON_OURS.get(r["reason"]))
    return {"here": here, "left": left, "ours": ours,
            "kept": here - left,
            "rate": round(100.0 * (here - left) / here, 1) if here else None,
            "rate_ours": round(100.0 * (here - ours) / here, 1) if here else None,
            "by_reason": {r["reason"]: r["c"] for r in gone},
            "since": since[:10], "until": until[:10]}


# ------------------------------------------------------------ scores in

def class_tests(db, group_id=None, limit=40):
    sql = ("SELECT t.*, g.name group_name,"
           " (SELECT COUNT(*) FROM class_test_scores x WHERE x.test_id=t.id"
           "  AND x.score IS NOT NULL) marked"
           " FROM class_tests t LEFT JOIN groups g ON g.id=t.group_id")
    args = []
    if group_id:
        sql += " WHERE t.group_id=?"; args.append(group_id)
    return db.execute(sql + " ORDER BY t.sat_on DESC, t.id DESC LIMIT ?",
                      args + [limit]).fetchall()


def new_class_test(db, group_id, title, max_score, sat_on):
    t = the_teacher(db)
    return db.execute(
        "INSERT INTO class_tests (teacher_id, group_id, title, max_score,"
        " sat_on, created_at) VALUES (?,?,?,?,?,?)",
        (t["id"], group_id, (title or "Class test").strip(),
         float(max_score or 100), sat_on, iso(now()))).lastrowid


def save_class_scores(db, test_id, scores, absent=()):
    """scores maps student id -> number or None."""
    for sid, value in scores.items():
        db.execute(
            "INSERT INTO class_test_scores (test_id, student_id, score, absent)"
            " VALUES (?,?,?,?) ON CONFLICT(test_id, student_id)"
            " DO UPDATE SET score=excluded.score, absent=excluded.absent",
            (test_id, sid, value, 1 if sid in absent else 0))
    db.commit()


def class_test_scores(db, test_id):
    return {r["student_id"]: r for r in db.execute(
        "SELECT * FROM class_test_scores WHERE test_id=?", (test_id,))}


def save_exam(db, group_id, kind, title, max_score, sat_on, scores,
              marked_by=""):
    """One row per student, so a re-sit is a second row and not an overwrite."""
    t = the_teacher(db)
    made = 0
    for sid, value in scores.items():
        if value is None:
            continue
        existing = db.execute(
            "SELECT id FROM exam_results WHERE student_id=? AND kind=?"
            " AND sat_on=?", (sid, kind, sat_on)).fetchone()
        if existing:
            # a correction to one mark must not wipe who marked the paper:
            # only overwrite the name when a new one is actually given
            db.execute("UPDATE exam_results SET score=?, max_score=?, title=?,"
                       " marked_by=COALESCE(NULLIF(?,''), marked_by)"
                       " WHERE id=?",
                       (value, float(max_score or 100), title, marked_by,
                        existing["id"]))
        else:
            db.execute(
                "INSERT INTO exam_results (student_id, teacher_id, group_id,"
                " kind, title, score, max_score, sat_on, marked_by, created_at)"
                " VALUES (?,?,?,?,?,?,?,?,?,?)",
                (sid, t["id"], group_id, kind, title, value,
                 float(max_score or 100), sat_on, marked_by, iso(now())))
        made += 1
    db.commit()
    return made


def exam_rows(db, group_id=None, kind=None):
    sql = ("SELECT e.*, s.name, g.name group_name FROM exam_results e"
           " JOIN students s ON s.id=e.student_id"
           " LEFT JOIN groups g ON g.id=e.group_id WHERE 1=1")
    args = []
    if group_id:
        sql += " AND e.group_id=?"; args.append(group_id)
    if kind:
        sql += " AND e.kind=?"; args.append(kind)
    return db.execute(sql + " ORDER BY e.sat_on DESC, s.name", args).fetchall()


def exam_spread(db, kind, group_id=None):
    """The shape of a set of marks, not just the middle of it.

    An average is easy to doubt, particularly when the teacher marked the
    papers themselves. A spread with some low marks in it is believable in a
    way a bare mean never is.
    """
    rows = [r for r in exam_rows(db, group_id, kind) if r["score"] is not None]
    if not rows:
        return None
    pcts = sorted(100.0 * r["score"] / (r["max_score"] or 100) for r in rows)
    n = len(pcts)
    bands = {"<40": 0, "40-54": 0, "55-69": 0, "70-84": 0, "85+": 0}
    for p in pcts:
        key = ("<40" if p < 40 else "40-54" if p < 55 else "55-69" if p < 70
               else "70-84" if p < 85 else "85+")
        bands[key] += 1
    return {"n": n, "mean": round(sum(pcts) / n, 1),
            "median": round(pcts[n // 2], 1),
            "lowest": round(pcts[0], 1), "highest": round(pcts[-1], 1),
            "bands": bands}


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


def set_in_league(db, group_id, due_at, on):
    """Count a whole set of homework in the league, or stop counting it."""
    if due_at is None:
        db.execute("UPDATE assignments SET in_league=? WHERE group_id=? AND due_at IS NULL",
                   (1 if on else 0, group_id))
    else:
        db.execute("UPDATE assignments SET in_league=? WHERE group_id=? AND due_at=?",
                   (1 if on else 0, group_id, due_at))
    db.commit()


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
    # a booklet is handed in by sitting it, not by sending a photograph, so
    # its tick comes from the attempt
    for a in items:
        tid = a["test_id"] if "test_id" in a.keys() else None
        if tid and a["id"] not in done_ids and db.execute(
                "SELECT 1 FROM dattempts WHERE test_id=? AND student_id=?"
                " AND finished_at IS NOT NULL LIMIT 1",
                (tid, student_id)).fetchone():
            done_ids.add(a["id"])
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

# A season is counted in lessons, not in days, so a class that met thirteen times
# and a class that met twelve are judged over the same amount of teaching.
SEASON_LESSONS = 15
SEASON_OPEN = "9999-12-31T00:00:00+00:00"   # a season still running has no end yet

CHAMPIONSHIP = [
    ("homework", "Homework", 3.0),
    ("conduct", "In the lesson", 2.0),
]
# what a single fixture of each kind is worth; the season total has no ceiling
CHAMPIONSHIP_MAX = sum(w for _k, _l, w in CHAMPIONSHIP)
MIN_GRADED = 3          # fewer than this and one lucky mark decides the season

# A football league, not an exam. Every homework you set is a fixture worth up to
# three points - the average of the marks in it, out of ten - and every lesson is
# a fixture worth up to two. Those points are added to the running total and
# never taken away, so the table climbs all season and a good week shows.
#
# Nothing is capped: a season with more fixtures simply has more points in it,
# the way a longer league season does.
HOMEWORK_PER_SET = 3.0      # the most one piece of homework can be worth
CONDUCT_PER_LESSON = 2.0    # the most one lesson can be worth
VOCAB_TARGET = 60       # kept for the Progress page; it scores nothing for now


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


def drop_pause(db, index):
    """Take back a recorded pause, so what happened inside it counts again.

    A pause is easy to start by accident and, once resumed, used to be
    invisible: a lesson taught that day stayed on the class's marking page but
    counted for nobody. Undoing one has to be possible without a developer.
    """
    raw = meta_get(db, "season_pauses")
    done = json.loads(raw) if raw else []
    if 0 <= index < len(done):
        done.pop(index)
        meta_set(db, "season_pauses", json.dumps(done))
        return True
    # the open one, if that is the index being pointed at
    if index == len(done) and is_paused(db):
        meta_set(db, "season_paused_at", "")
        return True
    return False


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


def handed_summary(graded, late, missing, waiting, pending=0):
    """The one line under a student's name, in plain words."""
    bits = []
    done = graded - late - missing
    if done > 0:
        bits.append("%d on time" % done)
    if late:
        bits.append("%d late" % late)
    if missing:
        bits.append("%d not handed in" % missing)
    if waiting:
        bits.append("%d waiting to be marked" % waiting)
    if pending:
        bits.append("%d not due yet" % pending)
    return ", ".join(bits) or "nothing due yet"


def homework_marks(db, student, lo, hi, windows):
    """Every piece of homework this student was set, and what it was worth.

    The average used to be taken over the work that arrived, which meant a
    student who did one piece well beat one who did all three - and, worse, that
    handing in late scored a nought while handing in nothing at all was simply
    left out of the sum. A deadline that has passed with nothing against it is a
    nought, the same as a late one.

    Work that has been handed in but not yet marked is left out entirely: that
    is the teacher's queue, not the student's fault.

    A season is fifteen lessons, and homework set in the last of them falls due
    after the fifteenth lesson has been and gone. Picking homework by its
    deadline therefore measured conduct over fifteen lessons and homework over
    about thirteen, and left the last two pieces free to skip. Homework is
    counted by the lesson it was set in instead, and each piece is judged once
    its deadline passes - which may be after the season's lessons are finished.
    A score is not final until they have all come due and been marked.

    Only homework that still exists counts. Deleting a piece of homework leaves
    the students' marked work in place with its link removed - the record is
    never destroyed - and those loose marks used to keep scoring here, so a
    deleted task went on deciding the table. The assignments are the list now,
    and a mark with nothing to belong to is left out.

    Returns (scores, late, missing, waiting, pending).
    """
    stamp = iso(now())
    # set during the season, or set just before it and falling due inside it -
    # a deadline should not be lost because the season began the morning after
    # the homework was written
    was_set = db.execute(
        "SELECT id, due_at FROM assignments WHERE group_id=? AND published=1"
        " AND in_league=1 AND test_id IS NULL"
        " AND created_at < ? AND (created_at >= ? OR (due_at IS NOT NULL AND due_at >= ?))"
        " ORDER BY due_at IS NULL, due_at",
        (student["group_id"], hi, lo, lo)).fetchall()

    scores, late, missing, waiting, pending = [], 0, 0, 0, 0
    batches = {}                      # (due_at) -> the marks from that set
    for a in was_set:
        due = a["due_at"]
        if due and due > stamp:
            pending += 1                  # set, but the deadline has not arrived
            continue
        if due and paused_at(due, windows):
            continue                      # the league was off when this fell due
        sub = db.execute(
            "SELECT status, score, created_at FROM submissions WHERE student_id=?"
            " AND assignment_id=? AND draft=0 ORDER BY status='graded' DESC,"
            " created_at LIMIT 1", (student["id"], a["id"])).fetchone()
        key = due or "none"
        if not sub:
            # with no deadline there is nothing to be late for and nothing to
            # have missed, so silence is not a nought - it is simply not counted
            if due:
                scores.append(0.0)
                batches.setdefault(key, []).append(0.0)
                missing += 1
            continue
        if paused_at(sub["created_at"], windows):
            continue
        if sub["status"] != "graded" or sub["score"] is None:
            waiting += 1                  # sitting in the marking queue
        elif due and sub["created_at"] > due:
            scores.append(0.0)
            batches.setdefault(key, []).append(0.0)
            late += 1
        else:
            scores.append(sub["score"])
            batches.setdefault(key, []).append(float(sub["score"]))
    return scores, late, missing, waiting, pending, batches


def test_marks(db, student, lo, hi, windows):
    """Digital tests sat this season, each one its own fixture.

    A test is homework that marks itself, so it earns its points the same way
    a marked set does: the score out of ten, worth up to three points, added to
    the running total.

    Only the *first* finished attempt counts. Students may sit a test again as
    often as they like - that is what it is for - but if the best of nine tries
    decided the table, the table would measure persistence at retaking rather
    than what anyone knows, which is the fault that took the vocabulary streak
    out of the scoring.

    A test carries no deadline, so a student who never sat one is not given a
    nought: in a table where points accumulate, the missed points are the loss.
    """
    level_id = level_of(db, student["group_id"])
    if level_id is None:
        return {}
    rows = db.execute(
        "SELECT a.test_id, a.score, a.total, a.finished_at"
        "  FROM dattempts a JOIN dtests t ON t.id = a.test_id"
        " WHERE a.student_id=? AND a.finished_at IS NOT NULL"
        "   AND t.published=1 AND t.in_league=1 AND t.level_id=?"
        "   AND a.finished_at >= ? AND a.finished_at < ?"
        " ORDER BY a.finished_at",
        (student["id"], level_id, lo, hi)).fetchall()
    first = {}
    for r in rows:
        if r["test_id"] in first or not r["total"]:
            continue                      # a later retake, or a test with no questions
        if paused_at(r["finished_at"], windows):
            continue                      # the league was off when they sat it
        first[r["test_id"]] = [round(r["score"] * 10.0 / r["total"], 2)]
    return first


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

        counted, late, missing, waiting, pending, batches = homework_marks(
            db, st, lo, hi, windows)
        # a test that marks itself is a piece of homework like any other, and
        # is keyed so it can never collide with a set of handed-in work
        sat = test_marks(db, st, lo, hi, windows)
        for test_id, marks in sat.items():
            batches["test:%d" % test_id] = marks
            counted.extend(marks)
        graded = len(counted)
        parts = {}
        # each set of homework is its own fixture: the average of the marks in
        # it, out of ten, worth up to three points, added to the running total
        earned = 0.0
        for marks in batches.values():
            earned += sum(marks) / len(marks) / 10.0 * HOMEWORK_PER_SET
        if batches:
            parts["homework"] = round(earned, 2)

        words = sum(1 for r in db.execute(
            "SELECT last_seen FROM word_progress WHERE student_id=? AND streak >= 3"
            " AND last_seen >= ? AND last_seen < ?", (st["id"], lo, hi))
            if not paused_at(r["last_seen"], windows))


        scored = [(r["punctuality"] or 0) + (r["behaviour"] or 0)
                  + (r["participation"] or 0) for r in db.execute(
            "SELECT day, punctuality, behaviour, participation FROM lesson_marks"
            " WHERE student_id=? AND day >= ? AND day < ?",
            (st["id"], local_day(parse(lo), cfg), local_day(parse(hi), cfg)))
            if not paused_day(r["day"], windows, cfg)]
        # each lesson is its own fixture too, worth up to two points
        parts["conduct"] = round(
            sum(v / 3.0 / 5.0 * CONDUCT_PER_LESSON for v in scored), 2)
        lesson_n = len(scored)

        # the parts are points already - each fixture was scored as it happened
        points = {k: round(parts.get(k, 0.0), 2) for k, _l, _w in CHAMPIONSHIP}
        rows.append({
            "student": st, "points": {k: round(v, 2) for k, v in points.items()},
            "total": round(sum(points.values()), 2),
            "graded": graded, "words": words, "late": late,
            "not_handed": missing, "waiting": waiting, "pending": pending,
            "handed": handed_summary(graded, late, missing, waiting, pending),
            "lessons": lessons, "closed": closed, "done": closed is not None,
            # the lessons can be finished while homework from the last of them
            # is still to come due, or still to be marked
            "final": closed is not None and not pending and not waiting,
            "marked_lessons": lesson_n,
            "average": round(sum(counted) / graded, 2) if graded else None,
            # deadlines behind them, not marks given: a student should not drop
            # out of the table because their work is sitting in the queue
            "eligible": (graded + waiting) >= MIN_GRADED,
            "counted": graded,
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
            # a pause quietly removes the lessons and homework inside it, so the
            # page has to be able to say which stretches are not being counted
            "pauses": windows,
            "start_day": local_day(parse(lo), cfg),
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


def answer_matches(given, expected):
    """Is a typed answer right?

    Marking typing has to be forgiving about the things that are not the point -
    case, spacing, a stray full stop, a curly apostrophe - and strict about the
    word itself. Several acceptable answers are separated by a slash.
    """
    def tidy(t):
        t = (t or "").strip().lower()
        t = t.replace("\u2019", "'").replace("\u2018", "'")
        t = re.sub(r"^[\s\-–—]+|[\s.,;:!?]+$", "", t)
        return re.sub(r"\s+", " ", t)
    got = tidy(given)
    if not got:
        return False
    for want in str(expected or "").split("/"):
        want = tidy(want)
        if want and got == want:
            return True
    return False


def load_test(db, data):
    """Create a digital test from the importer's json. Answers stay empty."""
    level = db.execute("SELECT id FROM levels WHERE name=?",
                       (data.get("level", ""),)).fetchone()
    tid = db.execute(
        "INSERT INTO dtests (level_id, number, title, passage, published, layout,"
        " minutes, strict, once, kind, created_at)"
        " VALUES (?,?,?,?,0,?,?,?,?,?,?)",
        (level["id"] if level else None, data.get("number"),
         data.get("title") or "Practice test",
         (data.get("passages") or {}).get("gap") or None,
         data.get("layout"), data.get("minutes"),
         1 if data.get("strict") else 0, 1 if data.get("once") else 0,
         "handout" if data.get("kind") == "handout" else "test",
         iso(now()))).lastrowid
    for i, q in enumerate(data.get("questions") or []):
        # a reading passage printed as a picture travels inside the file, and is
        # written out here so the page can simply point at it
        img = None
        if q.get("image_b64"):
            import base64
            img = "t%s_q%s.png" % (tid, q.get("num") or i + 1)
            with open(os.path.join(MATERIAL_DIR, img), "wb") as fh:
                fh.write(base64.b64decode(q["image_b64"]))
        qid = db.execute(
            "INSERT INTO dquestions (test_id, num, kind, prompt, answer, image, ord)"
            " VALUES (?,?,?,?,?,?,?)",
            (tid, q.get("num") or i + 1, q.get("kind") or "mcq",
             q.get("prompt") or "", q.get("answer"), img, i)).lastrowid
        for o in q.get("options") or []:
            db.execute("INSERT INTO doptions (question_id, letter, text) VALUES (?,?,?)",
                       (qid, o.get("letter") or "?", o.get("text") or ""))
    db.commit()
    return tid


def digital_tests(db, level_id=None, published_only=False, kind="test"):
    """The digital papers for a level.

    `kind` separates the two things that live in this table: 'test' for a
    paper that is marked, 'handout' for a booklet a student works through.
    Pass None for both.
    """
    sql = ("SELECT t.*, l.name level,"
           " (SELECT COUNT(*) FROM dquestions q WHERE q.test_id=t.id) n,"
           " (SELECT COUNT(*) FROM dquestions q WHERE q.test_id=t.id AND q.answer IS NOT NULL) keyed"
           " FROM dtests t LEFT JOIN levels l ON l.id=t.level_id")
    where, args = [], []
    if level_id:
        where.append("(t.level_id IS NULL OR t.level_id=?)"); args.append(level_id)
    if published_only:
        where.append("t.published=1")
    if kind is not None:
        where.append("IFNULL(t.kind,'test')=?"); args.append(kind)
    if where:
        sql += " WHERE " + " AND ".join(where)
    return db.execute(sql + " ORDER BY t.number, t.id", args).fetchall()


def test_questions(db, test_id):
    qs = db.execute("SELECT * FROM dquestions WHERE test_id=? ORDER BY ord, num",
                    (test_id,)).fetchall()
    out = []
    for q in qs:
        # in the order they were written, not alphabetically. A, B, C, D come
        # out the same either way, but a YES / NO question sorted by letter
        # reads NO / YES, which is backwards from the paper it copies.
        opts = db.execute("SELECT * FROM doptions WHERE question_id=? ORDER BY id",
                          (q["id"],)).fetchall()
        out.append((q, opts))
    return out


def set_answer_key(db, test_id, answers):
    """answers maps question id -> letter. An empty letter clears it."""
    for qid, letter in answers.items():
        # a typed answer is a word or two, not a letter
        db.execute("UPDATE dquestions SET answer=? WHERE id=? AND test_id=?",
                   ((letter or "").strip()[:120] or None, qid, test_id))
    db.commit()


def test_ready(db, test_id):
    """Can it be published?

    A booklet has boxes the key cannot mark - a conversation to complete, a
    discussion to answer in your own words. Those are still the student's work
    and are still saved, but they are not questions waiting for an answer key,
    so they do not hold up publishing. A test with nothing *but* those is not
    ready, because nothing in it could be marked at all.
    """
    r = db.execute("SELECT COUNT(*) n, SUM(answer IS NOT NULL) k,"
                   " SUM(answer IS NULL AND kind='open') o FROM dquestions"
                   " WHERE test_id=?", (test_id,)).fetchone()
    marked = r["k"] or 0
    return bool(marked) and r["n"] == marked + (r["o"] or 0)


def sat_already(db, test_id, student_id):
    """Has this student finished this paper, on a test that is sat once?

    An exam is not practice. The same paper opened a second time would mean a
    student who has seen the answers sitting it again, and because only the
    first sitting counts in the league, a retake could also quietly replace
    nothing while looking to them like a second chance.
    """
    t = db.execute("SELECT once FROM dtests WHERE id=?", (test_id,)).fetchone()
    if not t or not (t["once"] if "once" in t.keys() else 0):
        return False
    return bool(db.execute(
        "SELECT 1 FROM dattempts WHERE test_id=? AND student_id=?"
        " AND finished_at IS NOT NULL LIMIT 1", (test_id, student_id)).fetchone())


def start_attempt(db, test_id, student_id):
    row = db.execute(
        "SELECT * FROM dattempts WHERE test_id=? AND student_id=? AND finished_at IS NULL",
        (test_id, student_id)).fetchone()
    if row:
        return row["id"]
    new_id = db.execute(
        "INSERT INTO dattempts (test_id, student_id, started_at) VALUES (?,?,?)",
        (test_id, student_id, iso(now()))).lastrowid
    # Without this the row dies with the request that made it. Nothing noticed
    # while a paper was only ever handed in whole; the moment the page began
    # saving as it was typed, there was no attempt left to save against.
    db.commit()
    return new_id


SESSION_DAYS = 30


def open_session(db):
    """A signed-in session that outlives a restart.

    Sessions were a dictionary in memory, so every deploy - and every time the
    host restarted the app - signed the teacher out, often in the middle of
    marking. They live in the database now, and are swept when they expire.
    """
    token = secrets.token_urlsafe(24)
    db.execute("INSERT INTO sessions (token, created_at) VALUES (?,?)",
               (token, iso(now())))
    db.execute("DELETE FROM sessions WHERE created_at < ?",
               (iso(now() - timedelta(days=SESSION_DAYS)),))
    db.commit()
    return token


def session_live(db, token):
    if not token:
        return False
    row = db.execute(
        "SELECT created_at FROM sessions WHERE token=?", (token,)).fetchone()
    if not row:
        return False
    return parse(row["created_at"]) > now() - timedelta(days=SESSION_DAYS)


def close_session(db, token):
    db.execute("DELETE FROM sessions WHERE token=?", (token,))
    db.commit()


def report_breakage(where, exc):
    """Tell the teacher the site broke, rather than letting a student do it.

    At most one message an hour for the same page, because a broken page that
    everybody reloads would otherwise send the same message forty times. The
    text is the error, never the student's work.
    """
    try:
        cfg = load_config()
        token = cfg.get("telegram_token")
        if not token:
            return
        db = connect()
        try:
            ids = json.loads(meta_get(db, "teachers", "[]"))
            if not ids:
                return
            key = "broke:%s" % where
            last = meta_get(db, key, "")
            if last and parse(last) > now() - timedelta(hours=1):
                return
            meta_set(db, key, iso(now()))
        finally:
            db.close()
        import bot
        text = ("Something broke on the site.\n\n%s\n%s: %s\n\n"
                "Students will have seen an error page here."
                % (where, type(exc).__name__, str(exc)[:300]))
        for tid in ids:
            try:
                bot.send(token, tid, text)
            except Exception:
                pass
    except Exception:
        pass            # a failure to report must never take the site down


def finish_reason(db, attempt_id, why):
    """Why a paper was handed in: the clock, or the student leaving it."""
    meta_set(db, "ended:%d" % attempt_id, why)


def how_it_ended(db, attempt_id):
    return meta_get(db, "ended:%d" % attempt_id, "")


def save_progress(db, attempt_id, given):
    """Keep what has been typed so far, without handing it in.

    A booklet is a hundred boxes and it is filled in on a phone, where a call,
    a flat battery or a closed tab is ordinary. Nothing is marked here -
    `correct` stays NULL until the paper is handed in - so this is only the
    student's work being held on to.
    """
    row = db.execute("SELECT test_id FROM dattempts WHERE id=? AND"
                     " finished_at IS NULL", (attempt_id,)).fetchone()
    if not row:
        return 0
    ours = {r["id"] for r in db.execute(
        "SELECT id FROM dquestions WHERE test_id=?", (row["test_id"],))}
    n = 0
    for qid, text in given.items():
        if qid not in ours:
            continue
        db.execute(
            "INSERT INTO dresponses (attempt_id, question_id, given, correct)"
            " VALUES (?,?,?,NULL) ON CONFLICT(attempt_id, question_id)"
            " DO UPDATE SET given=excluded.given", (attempt_id, qid, text or None))
        n += 1
    db.commit()
    return n


def attempt_answers(db, attempt_id):
    """What is already in the boxes of an unfinished paper."""
    return {r["question_id"]: r["given"] for r in db.execute(
        "SELECT question_id, given FROM dresponses WHERE attempt_id=?",
        (attempt_id,)) if r["given"]}


def submit_attempt(db, attempt_id, given):
    """Mark it. given maps question id -> letter."""
    a = db.execute("SELECT * FROM dattempts WHERE id=?", (attempt_id,)).fetchone()
    if not a:
        return None
    qs = db.execute("SELECT id, answer, kind FROM dquestions WHERE test_id=?",
                    (a["test_id"],)).fetchall()
    kinds = {r["id"]: r["kind"] for r in db.execute(
        "SELECT id, kind FROM dquestions WHERE test_id=?", (a["test_id"],))}
    score, out_of = 0, 0
    for q in qs:
        letter = (given.get(q["id"]) or "").strip() or None
        kind = kinds.get(q["id"])
        if kind == "open":
            # kept, shown back, never right or wrong
            ok = None
        elif kind == "typed":
            ok = 1 if answer_matches(letter, q["answer"]) else 0
        else:
            ok = 1 if (letter and q["answer"] and letter == q["answer"]) else 0
        if ok is not None:
            score += ok
            out_of += 1
        db.execute("INSERT INTO dresponses (attempt_id, question_id, given, correct)"
                   " VALUES (?,?,?,?) ON CONFLICT(attempt_id, question_id) DO UPDATE"
                   " SET given=excluded.given, correct=excluded.correct",
                   (attempt_id, q["id"], letter, ok))
    db.execute("UPDATE dattempts SET finished_at=?, score=?, total=? WHERE id=?",
               (iso(now()), score, out_of, attempt_id))
    db.commit()
    return score, out_of


def written_answers(db, test_id):
    """Every student's written answer on this paper, ready to be read.

    The marked questions score themselves; the writing does not, and until
    now it was saved where only the student who wrote it could see it. This
    gathers it - one question at a time, one student at a time, newest
    sitting first - so a teacher can read thirty-nine emails in one place
    instead of thirty-nine.
    """
    out = []
    for q in db.execute(
            "SELECT * FROM dquestions WHERE test_id=? AND kind='open'"
            " ORDER BY num", (test_id,)):
        answers = []
        for r in db.execute(
                "SELECT s.id student_id, s.name, a.finished_at, r.given"
                " FROM dattempts a JOIN students s ON s.id=a.student_id"
                " LEFT JOIN dresponses r ON r.attempt_id=a.id AND r.question_id=?"
                " WHERE a.test_id=? AND a.finished_at IS NOT NULL"
                " ORDER BY s.name", (q["id"], test_id)):
            text = (r["given"] or "").strip()
            answers.append({"student_id": r["student_id"], "name": r["name"],
                            "finished_at": r["finished_at"], "text": text,
                            "words": len(text.split()) if text else 0})
        out.append({"question": q, "answers": answers})
    return out


def attempts_for_test(db, test_id):
    return db.execute(
        "SELECT a.*, s.name FROM dattempts a JOIN students s ON s.id=a.student_id"
        " WHERE a.test_id=? AND a.finished_at IS NOT NULL"
        " ORDER BY a.score DESC, a.finished_at", (test_id,)).fetchall()


def drop_attempt(db, attempt_id):
    """Rub out one sitting, and the answers that went with it.

    A teacher opening a test to see what it looks like leaves a real attempt
    behind, and because only the first sitting counts, that trial run is the
    one the league would keep forever. Removing it is the honest fix; there is
    nothing else in the system that can put it right.
    """
    row = db.execute("SELECT test_id, student_id FROM dattempts WHERE id=?",
                     (attempt_id,)).fetchone()
    if not row:
        return None
    db.execute("DELETE FROM dresponses WHERE attempt_id=?", (attempt_id,))
    db.execute("DELETE FROM dattempts WHERE id=?", (attempt_id,))
    db.commit()
    return row["test_id"]


def student_attempts(db, student_id):
    return db.execute(
        "SELECT a.*, t.title FROM dattempts a JOIN dtests t ON t.id=a.test_id"
        " WHERE a.student_id=? AND a.finished_at IS NOT NULL"
        " ORDER BY a.finished_at DESC", (student_id,)).fetchall()


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
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
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


def last_marks_before(db, group_id, day):
    """What this class was given at their previous lesson, keyed by student.

    Most students are the same most days, so the quickest honest way to mark a
    lesson is to start from the last one and change who differs.
    """
    prev = db.execute(
        "SELECT m.day FROM lesson_marks m JOIN students s ON s.id=m.student_id"
        " WHERE s.group_id=? AND m.day < ? ORDER BY m.day DESC LIMIT 1",
        (group_id, day)).fetchone()
    if not prev:
        return {}, None
    return marks_on(db, group_id, prev["day"]), prev["day"]


def marks_on(db, group_id, day):
    """What was recorded for this class on one date, keyed by student."""
    rows = db.execute(
        "SELECT m.* FROM lesson_marks m JOIN students s ON s.id=m.student_id"
        " WHERE s.group_id=? AND m.day=?", (group_id, day)
    ).fetchall()
    return {r["student_id"]: r for r in rows}


def seed_coursebook(db):
    """The writing lesson from each unit of the coursebook they are studying."""
    if db.execute("SELECT COUNT(*) c FROM prompts WHERE unit IS NOT NULL"
                  " AND mine=0").fetchone()["c"]:
        return
    try:
        import writing_bank as wb
    except ImportError:
        return
    for row in wb.LESSONS:
        level = row["level"]
        slot = wb.WRITING_SLOT.get(level, "D")
        words, mins = {"Beginner": (60, 20), "Elementary": (90, 25),
                       "Pre-Intermediate": (140, 30),
                       "Intermediate": (180, 35)}.get(level, (150, 30))
        db.execute(
            "INSERT INTO prompts (level, kind, text, min_words, minutes, unit,"
            " lesson, topic, mine, created_at) VALUES (?,?,?,?,?,?,?,?,0,?)",
            (level, "coursebook", row["task"], words, mins, row["unit"],
             slot, row["title"], iso(now())))
    db.commit()


def units_with_writing(db, level):
    rows = db.execute(
        "SELECT unit, topic, lesson FROM prompts WHERE level=? AND unit IS NOT NULL"
        " GROUP BY unit ORDER BY unit", (level,)).fetchall()
    return rows


# The shape a unit's homework always takes, in the order it is always given.
# Written down here because it was being retyped every week, and because the
# writing task was then typed a second time to make it digital.
UNIT_PLAN = [
    ("workbook", "Workbook unit {unit} {pair}"),
    ("booklet", "12-page handout \u2014 unit {unit}"),
    ("writing", "Writing \u2014 {kind}"),
    ("practice", "Practice test {test}"),
]


def unit_homework(db, group_id, unit, pair="A&C", kind="essay", practice=""):
    """Everything a unit's homework needs, found rather than retyped.

    The booklet and the writing question already exist in the system: one is a
    digital test on that level's shelf, the other is in the question bank
    against that unit. This joins them to the lines the teacher would have
    written by hand, so setting a unit's homework is one form rather than two.
    """
    level_id = level_of(db, group_id)
    level = level_name(db, level_id) if level_id else ""
    out = {"level": level, "unit": unit, "items": []}

    out["items"].append({"kind": "workbook", "test_id": None,
                         "title": "Workbook unit %s %s" % (unit, pair)})

    booklet = None
    if level_id:
        booklet = db.execute(
            "SELECT id, title FROM dtests WHERE level_id=? AND number=?"
            " AND layout IS NOT NULL ORDER BY published DESC, id DESC LIMIT 1",
            (level_id, unit)).fetchone()
    out["items"].append({
        "kind": "booklet",
        "test_id": booklet["id"] if booklet else None,
        "title": (booklet["title"].replace(" (booklet)", "") if booklet
                  else "12-page handout \u2014 unit %s" % unit)})

    row = suggest_prompt(db, level, kind, unit) if level else None
    out["items"].append({
        "kind": "writing", "test_id": None,
        "title": "Writing \u2014 %s" % (row["topic"] if row and row["topic"]
                                    else kind),
        "prompt": row["text"] if row else "",
        "minutes": row["minutes"] if row and "minutes" in row.keys() else None})

    if practice:
        out["items"].append({"kind": "practice", "test_id": None,
                             "title": "Practice test %s" % practice})
    return out


def seed_prompts(db):
    """Put the shipped questions in once, and never tread on the teacher's own."""
    if db.execute("SELECT COUNT(*) c FROM prompts WHERE mine=0").fetchone()["c"]:
        return
    try:
        import prompts_seed as seed
    except ImportError:
        return
    for level, kinds in seed.BANK.items():
        words, mins = seed.DEFAULTS.get(level, (None, None))
        for kind, texts in kinds.items():
            for t in texts:
                db.execute(
                    "INSERT INTO prompts (level, kind, text, min_words, minutes,"
                    " mine, created_at) VALUES (?,?,?,?,?,0,?)",
                    (level, kind, t, words, mins, iso(now())))
    db.commit()


def prompt_kinds():
    try:
        import prompts_seed as seed
        return seed.KINDS
    except ImportError:
        return [("opinion", "Opinion", None, None)]


def suggest_prompt(db, level, kind, unit=None):
    """One question, least-used first, so the same one is not set every week."""
    if unit:
        row = db.execute(
            "SELECT * FROM prompts WHERE level=? AND unit=? ORDER BY used, RANDOM()"
            " LIMIT 1", (level, unit)).fetchone()
        if row:
            db.execute("UPDATE prompts SET used=used+1 WHERE id=?", (row["id"],))
            db.commit()
            return row
    row = db.execute(
        "SELECT * FROM prompts WHERE level=? AND kind=?"
        " ORDER BY used, RANDOM() LIMIT 1", (level, kind)).fetchone()
    if row:
        db.execute("UPDATE prompts SET used=used+1 WHERE id=?", (row["id"],))
        db.commit()
    return row


def prompts_for(db, level=None, kind=None):
    sql, args = "SELECT * FROM prompts", []
    where = []
    if level:
        where.append("level=?"); args.append(level)
    if kind:
        where.append("kind=?"); args.append(kind)
    if where:
        sql += " WHERE " + " AND ".join(where)
    return db.execute(sql + " ORDER BY level, kind, used, id", args).fetchall()


def add_prompt(db, level, kind, text, min_words=None, minutes=None):
    text = (text or "").strip()
    if not text or not level or not kind:
        return None
    pid = db.execute(
        "INSERT INTO prompts (level, kind, text, min_words, minutes, mine, created_at)"
        " VALUES (?,?,?,?,?,1,?)",
        (level, kind, text[:1500], min_words, minutes, iso(now()))).lastrowid
    db.commit()
    return pid


def delete_prompt(db, pid):
    db.execute("DELETE FROM prompts WHERE id=?", (pid,))
    db.commit()


def count_words(text):
    """Words the way a writing paper counts them."""
    return len([w for w in re.split(r"\s+", (text or "").strip()) if w])


def writing_task(db, assignment_id):
    a = db.execute("SELECT * FROM assignments WHERE id=?", (assignment_id,)).fetchone()
    return a if a and a["prompt"] else None


def open_writing(db, student_id, assignment_id):
    """The student's answer in progress, made if this is their first look."""
    row = db.execute(
        "SELECT * FROM submissions WHERE student_id=? AND assignment_id=?"
        " AND kind='text' ORDER BY id DESC LIMIT 1",
        (student_id, assignment_id)).fetchone()
    if row:
        return row
    sid = db.execute(
        "INSERT INTO submissions (student_id, assignment_id, created_at, kind, draft,"
        " answer, words) VALUES (?,?,?, 'text', 1, '', 0)",
        (student_id, assignment_id, iso(now()))).lastrowid
    db.commit()
    return db.execute("SELECT * FROM submissions WHERE id=?", (sid,)).fetchone()


def save_writing(db, sub_id, text, seconds=None, hand_in=False):
    """Keep what has been typed. Handing in is the only thing that is final.

    Saving happens while they write, so a closed tab or a flat battery costs a
    few seconds of typing rather than an essay.
    """
    text = text or ""
    fields = [text, count_words(text)]
    sql = "UPDATE submissions SET answer=?, words=?"
    if seconds is not None:
        sql += ", written_secs=?"
        fields.append(int(seconds))
    if hand_in:
        sql += ", draft=0, created_at=?"
        fields.append(iso(now()))
    sql += " WHERE id=? AND status='pending'"
    fields.append(sub_id)
    db.execute(sql, fields)
    db.commit()


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
    # a past season keeps its winner's name in the record book; only the link
    # to a row that is about to disappear is let go
    db.execute("UPDATE seasons SET winner_id=NULL WHERE winner_id=?", (student_id,))
    db.execute("DELETE FROM dresponses WHERE attempt_id IN"
               " (SELECT id FROM dattempts WHERE student_id=?)", (student_id,))
    db.execute("DELETE FROM game_answers WHERE student_id=?", (student_id,))
    db.execute("DELETE FROM solo_questions WHERE run_id IN"
               " (SELECT id FROM solo_runs WHERE student_id=?)", (student_id,))
    for table in ("submissions", "word_progress", "quiz_sessions", "questions",
                  "parents", "lesson_marks", "goals", "game_players", "dattempts",
                  "solo_runs", "students"):
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
