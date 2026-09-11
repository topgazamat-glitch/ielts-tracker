"""Season — see the assertions for what it guarantees.

Run me with:  python3 run_tests.py            (all of them)
              python3 tests/season_test.py   (just this one)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
FIXTURES = os.path.join(ROOT, "tests", "fixtures")

import tempfile, shutil
tmp = tempfile.mkdtemp()
os.environ["DATA_DIR"] = tmp

import core
from datetime import timedelta

core.init_db()
db = core.connect()
cfg = core.load_config()

g = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('Test','TSTX',?)",
               (core.iso(core.now()),)).lastrowid
def mk(name):
    return db.execute("INSERT INTO students (name, group_id, active, created_at)"
                      " VALUES (?,?,1,?)", (name, g, core.iso(core.now()))).lastrowid
ali, vali, new = mk("Ali"), mk("Vali"), mk("Newcomer")
db.commit()

print("1. Table is clear before the season starts")
st = core.championship(db)
print("   started:", st["started"], "rows:", len(st["rows"]), "season:", st["season"])
assert st["started"] is False and st["rows"] == []

# backdate the season so every lesson below sits in the past, as in real use
start = core.now() - timedelta(days=40)
core.start_season(db, start)
print("2. Season started at", core.season_start(db))

# --- lessons: Ali gets 18 lessons, Vali 15, Newcomer 4. One lesson BEFORE the start.
def lesson(sid, day, p=5, b=5, part=5):
    db.execute("INSERT OR REPLACE INTO lesson_marks (student_id, day, punctuality,"
               " behaviour, participation, created_at) VALUES (?,?,?,?,?,?)",
               (sid, day, p, b, part, core.iso(core.now())))

before = core.local_day(start - timedelta(days=3), cfg)
lesson(ali, before, 5, 5, 5)                       # must not count
days = [core.local_day(start + timedelta(days=i), cfg) for i in range(30)]
for i in range(18):
    lesson(ali, days[i], 5, 5, 5)
for i in range(15):
    lesson(vali, days[i], 3, 3, 3)
for i in range(4):
    lesson(new, days[i], 5, 5, 5)
db.commit()

hi_a, n_a, closed_a = core.season_window(db, ali, core.season_start(db), cfg)
hi_v, n_v, closed_v = core.season_window(db, vali, core.season_start(db), cfg)
hi_n, n_n, closed_n = core.season_window(db, new, core.season_start(db), cfg)
print("3. Lesson counting (the pre-season lesson is excluded)")
print("   Ali   18 recorded ->", n_a, "counted, closed on", closed_a, "(day", days.index(closed_a), ")")
print("   Vali  15 recorded ->", n_v, "counted, closed on", closed_v)
print("   New    4 recorded ->", n_n, "counted, closed:", closed_n)
assert (n_a, closed_a) == (15, days[14]), (n_a, closed_a)
assert (n_v, closed_v) == (15, days[14])
assert (n_n, closed_n) == (4, None)

print("4. Homework set during the season counts, however late it is answered")
def task(n, made):
    return db.execute("INSERT INTO assignments (group_id, title, created_at, published,"
        " due_at) VALUES (?,?,?,1,?)",
        (g, "HW %d" % n, core.iso(made), core.iso(made + timedelta(days=1)))).lastrowid
tasks = [task(k, start + timedelta(days=k)) for k in range(1, 5)]
def hand(sid, when, score, task_i=0):
    db.execute("INSERT INTO submissions (student_id, assignment_id, status, score,"
               " created_at, kind) VALUES (?,?,'graded',?,?,'photo')",
               (sid, tasks[task_i], score, core.iso(when)))
# three good pieces inside the season for each
for i in (1, 2, 3):
    hand(ali, start + timedelta(days=i, hours=1), 8, i - 1)
    hand(vali, start + timedelta(days=i, hours=1), 8, i - 1)
# Ali hands in a perfect 10 on day 20 - AFTER his season closed on day 14
hand(ali, start + timedelta(days=20), 10, 3)
db.commit()

st = core.championship(db)
by = {r["student"]["name"]: r for r in st["rows"]}
print("   Ali: %s" % by["Ali"]["handed"])
print("   all four were set during his season, so all four count;")
print("   the one he sent on day 20 was long past its deadline, so it is a nought")
assert by["Ali"]["graded"] == 4, by["Ali"]["graded"]
assert by["Ali"]["late"] == 1, by["Ali"]["late"]

print("5. The table")
for r in st["rows"]:
    print("   %-10s rank %-5s total %-5s hw %-5s conduct %-5s lessons %2d/%d %s" % (
        r["student"]["name"], r["rank"], r["total"],
        r["points"]["homework"], r["points"]["conduct"],
        r["lessons"], core.SEASON_LESSONS, "finished" if r["done"] else ""))
assert by["Ali"]["done"] and by["Vali"]["done"] and not by["Newcomer"]["done"]
# same homework, better conduct -> Ali above Vali
assert by["Ali"]["total"] > by["Vali"]["total"]
print("   Ali and Vali both averaged 8/10; Ali wins on lesson marks (5s vs 3s). Correct.")

print("6. Closing the season keeps the record and clears the table")
core.close_season(db)
past = core.past_seasons(db)
print("   record book:", [(r["no"], r["winner_name"], r["winner_points"]) for r in past])
assert len(past) == 1 and past[0]["winner_name"] == "Ali"
st2 = core.championship(db)
print("   new season number:", st2["season"], "started:", st2["started"])
print("   everyone back to zero:",
      sorted({r["total"] for r in st2["rows"]}), "lessons:",
      sorted({r["lessons"] for r in st2["rows"]}))
assert st2["season"] == 2
assert all(r["total"] == 0 for r in st2["rows"])
assert all(r["lessons"] == 0 for r in st2["rows"])

print("\nAll season checks passed.")
db.close()
shutil.rmtree(tmp)
