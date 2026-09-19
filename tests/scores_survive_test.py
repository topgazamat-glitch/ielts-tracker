"""Deleting a photograph must never change a mark.

Run me with:  python3 run_tests.py scores_survive
"""
import os
import sys
import tempfile
from datetime import timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None)
import core
core.init_db(); db = core.connect(); cfg = core.load_config()
os.makedirs(core.UPLOAD_DIR, exist_ok=True)

start = core.now() - timedelta(days=40)
g = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('G','G',?)",
               (core.iso(start),)).lastrowid
sid = db.execute("INSERT INTO students (name, group_id, active, created_at)"
                 " VALUES ('Madina',?,1,?)", (g, core.iso(start))).lastrowid
core.start_season(db, start)

# three pieces of homework, marked 9, 7 and 10
marks = [9, 7, 10]
for i, score in enumerate(marks):
    made = start + timedelta(days=i)
    a = db.execute("INSERT INTO assignments (group_id, title, created_at,"
                   " published, due_at) VALUES (?,?,?,1,?)",
                   (g, "HW %d" % i, core.iso(made),
                    core.iso(made + timedelta(hours=12)))).lastrowid
    sub = db.execute("INSERT INTO submissions (student_id, assignment_id, status,"
                     " score, created_at, kind) VALUES (?,?,'graded',?,?,'photo')",
                     (sid, a, score, core.iso(made + timedelta(hours=1)))).lastrowid
    name = "page_%d.jpg" % i
    open(os.path.join(core.UPLOAD_DIR, name), "wb").write(b"x" * 9000)
    db.execute("INSERT INTO files (submission_id, filename, telegram_file_id, ord)"
               " VALUES (?,?,?,1)", (sub, name, "tg-%d" % i))
for i in range(3):
    core.save_mark(db, sid, core.local_day(start + timedelta(days=i), cfg),
                   {"punctuality": 5, "behaviour": 5, "participation": 5}, None)
db.commit()


def standing():
    row = {r["student"]["name"]: r for r in core.championship(db)["rows"]}["Madina"]
    return row["points"]["homework"], row["points"]["conduct"], row["total"]


before = standing()
print("1. THE LEAGUE BEFORE")
print("   homework %.2f · in the lesson %.2f · total %.2f" % before)
assert before[0] > 0

print("\n2. LET THE PHOTOGRAPHS GO")
said = core.purge(db, "photos", days=1)
print("   ", said)
left = [f for f in os.listdir(core.UPLOAD_DIR) if f.endswith(".jpg")]
print("   photographs still on the disk:", len(left))
assert not left, "the files should be gone"

print("\n3. THE LEAGUE AFTER")
after = standing()
print("   homework %.2f · in the lesson %.2f · total %.2f" % after)
assert after == before, "a mark must not move when a picture is deleted"

print("\n4. THE MARKS THEMSELVES ARE UNTOUCHED")
scores = [r["score"] for r in db.execute(
    "SELECT score FROM submissions WHERE student_id=? ORDER BY created_at", (sid,))]
print("   scores on record:", scores)
assert scores == marks

print("\n5. THE WORK IS STILL THERE, ONLY THE PICTURE IS NOT")
n = db.execute("SELECT COUNT(*) c FROM submissions WHERE student_id=?"
               " AND status='graded'", (sid,)).fetchone()["c"]
off = db.execute("SELECT COUNT(*) c FROM files WHERE offloaded=1").fetchone()["c"]
print("   graded submissions: %d · pages marked as fetch-on-demand: %d" % (n, off))
assert n == 3 and off == 3



print("\n6. THE SAME HOLDS FOR A PAGE UPLOADED FROM THE WEBSITE")
# one more piece of homework, its photo sent through the site, so there is no
# copy in Telegram - the kind "Let them go" refuses to touch
made = start + timedelta(days=4)
a = db.execute("INSERT INTO assignments (group_id, title, created_at, published,"
               " due_at) VALUES (?,?,?,1,?)",
               (g, "HW web", core.iso(made),
                core.iso(made + timedelta(hours=12)))).lastrowid
sub = db.execute("INSERT INTO submissions (student_id, assignment_id, status,"
                 " score, created_at, kind) VALUES (?,?,'graded',8,?,'photo')",
                 (sid, a, core.iso(made + timedelta(hours=1)))).lastrowid
web = "web_page.jpg"
open(os.path.join(core.UPLOAD_DIR, web), "wb").write(b"y" * 9000)
db.execute("INSERT INTO files (submission_id, filename, telegram_file_id, ord)"
           " VALUES (?,?,NULL,1)", (sub, web))
db.commit()
with_web = standing()
print("   with the web page marked 8: homework %.2f · total %.2f"
      % (with_web[0], with_web[2]))

print("\n7. THE BUTTON REFUSES TO TOUCH IT")
core.purge(db, "photos", days=1)
print("   still on the disk:", os.path.isfile(os.path.join(core.UPLOAD_DIR, web)))
assert os.path.isfile(os.path.join(core.UPLOAD_DIR, web))

print("\n8. AND IF IT IS DELETED BY HAND, THE MARK STILL STANDS")
os.remove(os.path.join(core.UPLOAD_DIR, web))
after_web = standing()
print("   homework %.2f · total %.2f" % (after_web[0], after_web[2]))
assert after_web == with_web, "the mark does not depend on the picture existing"
print("   the score on record:", db.execute(
    "SELECT score FROM submissions WHERE id=?", (sub,)).fetchone()["score"])

print("\nALL GOOD")
