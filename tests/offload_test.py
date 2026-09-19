"""Letting go of old photographs, without losing one.

Run me with:  python3 run_tests.py offload
"""
import os
import sys
import tempfile
from datetime import timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None)
import core, jobs
core.init_db(); db = core.connect()
os.makedirs(core.UPLOAD_DIR, exist_ok=True)

g = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('G','G',?)",
               (core.iso(core.now()),)).lastrowid
sid = db.execute("INSERT INTO students (name, group_id, active, created_at)"
                 " VALUES ('S',?,1,?)", (g, core.iso(core.now()))).lastrowid
old_day = core.iso(core.now() - timedelta(days=40))


def photo(name, tg_id, preview=None, status="graded", when=None):
    sub = db.execute("INSERT INTO submissions (student_id, status, created_at, kind)"
                     " VALUES (?,?,?,'photo')",
                     (sid, status, when or old_day)).lastrowid
    open(os.path.join(core.UPLOAD_DIR, name), "wb").write(b"x" * 5000)
    if preview:
        open(os.path.join(core.UPLOAD_DIR, preview), "wb").write(b"x" * 500)
    db.execute("INSERT INTO files (submission_id, filename, telegram_file_id,"
               " preview, ord) VALUES (?,?,?,?,1)", (sub, name, tg_id, preview))
    db.commit()
    return name


here = lambda n: os.path.isfile(os.path.join(core.UPLOAD_DIR, n))

a = photo("a.jpg", "tg-a", preview="a_s.jpg")          # has a screen copy
b = photo("b.jpg", "tg-b")                             # no screen copy
c = photo("c.jpg", "tg-gone")                          # Telegram will not return it
d = photo("d.jpg", None)                               # only copy anywhere
e = photo("e.jpg", "tg-e", preview="e_s.jpg", status="pending")
f = photo("f.jpg", "tg-f", preview="f_s.jpg", when=core.iso(core.now()))

jobs.telegram_has = lambda token, fid: fid != "tg-gone"
said = jobs.offload_old_photos(db, {"photo_keep_days": 21, "telegram_token": "x"})
print("1. WHAT THE PASS DID\n   ", said)

print("\n2. A PAGE WITH A SCREEN COPY GOES")
print("   a.jpg on disk:", here(a), "| its screen copy:", here("a_s.jpg"))
assert not here(a) and here("a_s.jpg")

print("\n3. ONE WITHOUT A SCREEN COPY GOES ONLY IF TELEGRAM CONFIRMS IT")
print("   b.jpg (Telegram has it):", here(b))
print("   c.jpg (Telegram lost it):", here(c))
assert not here(b), "confirmed: safe to let go"
assert here(c), "unconfirmed: must be kept"

print("\n4. A PAGE WITH NO OTHER COPY ANYWHERE IS NEVER TOUCHED")
print("   d.jpg:", here(d))
assert here(d)

print("\n5. UNGRADED AND RECENT WORK IS LEFT ALONE")
print("   e.jpg (not graded):", here(e), "| f.jpg (sent today):", here(f))
assert here(e) and here(f)

print("\n6. THE DEFAULT IS TEN DAYS, NOT THREE MONTHS")
print("   default:", core.load_config()["photo_keep_days"], "days")
assert core.load_config()["photo_keep_days"] == 10

print("\nALL GOOD")
