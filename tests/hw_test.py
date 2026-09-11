"""Hw — see the assertions for what it guarantees.

Run me with:  python3 run_tests.py            (all of them)
              python3 tests/hw_test.py   (just this one)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
FIXTURES = os.path.join(ROOT, "tests", "fixtures")

import tempfile, shutil
from datetime import timedelta
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None)

import core
core.init_db(); db = core.connect(); cfg = core.load_config()
g = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('T','TT',?)",
               (core.iso(core.now()),)).lastrowid
start = core.now() - timedelta(days=20)
core.start_season(db, start)

def student(name):
    return db.execute("INSERT INTO students (name, group_id, active, token, created_at)"
        " VALUES (?,?,1,?,?)", (name, g, name.ljust(20, "x"), core.iso(core.now()))).lastrowid

# three tasks, all due in the past
tasks = []
for i in range(3):
    tasks.append(db.execute(
        "INSERT INTO assignments (group_id, title, created_at, published, due_at)"
        " VALUES (?,?,?,1,?)",
        (g, "Task %d" % (i+1), core.iso(start + timedelta(days=i)),
         core.iso(start + timedelta(days=i+2)))).lastrowid)

def hand(sid, task_i, score, late=False, ungraded=False):
    a = tasks[task_i]
    due = db.execute("SELECT due_at FROM assignments WHERE id=?", (a,)).fetchone()["due_at"]
    when = core.parse(due) + timedelta(hours=3 if late else -3)
    db.execute("INSERT INTO submissions (student_id, assignment_id, status, score,"
               " created_at, kind) VALUES (?,?,?,?,?,'photo')",
               (sid, a, "pending" if ungraded else "graded",
                None if ungraded else score, core.iso(when)))

alisher = student("Alisher");  [hand(alisher, i, 8) for i in range(3)]       # all three, 8s
bek     = student("Bek");      hand(bek, 0, 10)                              # one, perfect
dilnoza = student("Dilnoza");  hand(dilnoza, 0, 9); hand(dilnoza, 1, 9)      # two, nines
rustam  = student("Rustam")                                                  # nothing
sardor  = student("Sardor");   hand(sardor, 0, 10); hand(sardor, 1, 10, late=True)
malika  = student("Malika");   hand(malika, 0, 8); hand(malika, 1, 9, ungraded=True)
db.commit()

st = core.championship(db)
by = {r["student"]["name"]: r for r in st["rows"]}
print("Three tasks were set. All three deadlines have passed.\n")
print("%-9s %-34s %-7s %-6s" % ("student", "what happened", "hw pts", "rank"))
for n in ("Alisher", "Bek", "Dilnoza", "Sardor", "Malika", "Rustam"):
    r = by[n]
    print("%-9s %-34s %-7s %-6s" % (n, r["handed"], r["points"]["homework"],
                                    r["rank"] if r["rank"] else "-"))

print("\nChecks:")
a, b, d = by["Alisher"], by["Bek"], by["Dilnoza"]
print("  three 8s beats one 10:      %.2f > %.2f  %s" % (
    a["points"]["homework"], b["points"]["homework"],
    a["points"]["homework"] > b["points"]["homework"]))
assert a["points"]["homework"] > b["points"]["homework"]
print("  two 9s beats one 10:        %.2f > %.2f  %s" % (
    d["points"]["homework"], b["points"]["homework"],
    d["points"]["homework"] > b["points"]["homework"]))
assert d["points"]["homework"] > b["points"]["homework"]
print("  one of three (10) scores:   %.2f of 3  (10+0+0)/3 = 3.33/10" % b["points"]["homework"])
assert abs(b["points"]["homework"] - 1.0) < 0.01
print("  two of three (9,9) scores:  %.2f of 3  (9+9+0)/3 = 6/10" % d["points"]["homework"])
assert abs(d["points"]["homework"] - 1.8) < 0.01
print("  did nothing scores nought:  %.2f, and is ranked, not hidden: %s" % (
    by["Rustam"]["points"]["homework"], by["Rustam"]["rank"] is not None))
assert by["Rustam"]["points"]["homework"] == 0 and by["Rustam"]["rank"]
print("  late still scores nought:   Sardor %s" % by["Sardor"]["handed"])
assert by["Sardor"]["late"] == 1
print("  unmarked work is left out:  Malika %s" % by["Malika"]["handed"])
assert by["Malika"]["waiting"] == 1
print("     -> her average is over %d pieces, not %d" % (
    by["Malika"]["graded"], by["Malika"]["graded"] + 1))

print("\nEverybody is now in the table:", st["eligible"], "of", len(st["rows"]))
assert st["eligible"] == 6
db.close(); shutil.rmtree(tmp)
print("\nHomework counts what was set.")
