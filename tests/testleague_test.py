"""Tests and the league: practice earns nothing; a test set as homework is homework.

Only homework and the lesson count. A test a student sits on their own -
a mock, a practice paper - earns no points however well it goes. A test
the teacher sets as homework, with a deadline, counts like any piece of
homework: its first sitting before the deadline, out of ten, averaged with
the rest of that set.

Run me with:  python3 run_tests.py testleague
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

start = core.now() - timedelta(days=20)
lvl = db.execute("SELECT id FROM levels WHERE name='Intermediate'").fetchone()["id"]
g = db.execute("INSERT INTO groups (name, join_code, level_id, created_at)"
               " VALUES ('T','T',?,?)", (lvl, core.iso(core.now()))).lastrowid
core.start_season(db, start)


def student(name):
    return db.execute("INSERT INTO students (name, group_id, active, created_at)"
                      " VALUES (?,?,1,?)",
                      (name, g, core.iso(core.now()))).lastrowid


def a_test(title, marks=10, published=1):
    data = {"level": "Intermediate", "number": 1, "title": title,
            "passages": {}, "questions": [
                {"num": i + 1, "prompt": "q%d" % i, "answer": "yes",
                 "kind": "typed", "options": []} for i in range(marks)]}
    tid = core.load_test(db, data)
    db.execute("UPDATE dtests SET published=?, level_id=? WHERE id=?", (published, lvl, tid))
    return tid


def set_as_homework(tid, due, title="Test", also=None):
    """Set a test as homework, due at `due`; `also` is a photo item in the same set."""
    made = core.iso(start + timedelta(days=1))
    db.execute("INSERT INTO assignments (group_id, title, created_at, published, due_at, test_id)"
               " VALUES (?,?,?,1,?,?)", (g, title, made, core.iso(due), tid))
    if also:
        return db.execute("INSERT INTO assignments (group_id, title, created_at, published, due_at)"
                          " VALUES (?,?,?,1,?)", (g, also, made, core.iso(due))).lastrowid


def sit(sid, tid, right, when):
    """Sit a test getting `right` of its questions correct, finished at `when`."""
    qs = core.test_questions(db, tid)
    att = core.start_attempt(db, tid, sid)
    core.submit_attempt(db, att, {q["id"]: ("yes" if i < right else "no")
                                  for i, (q, _o) in enumerate(qs)})
    db.execute("UPDATE dattempts SET finished_at=? WHERE id=?", (core.iso(when), att))
    db.commit()
    return att


def points(name):
    rows = {r["student"]["name"]: r for r in core.championship(db)["rows"]}
    return rows[name]["points"].get("homework", 0.0)


print("1. A TEST SAT FOR PRACTICE EARNS NOTHING")
mock = a_test("A2 Mock 4", marks=10)
a = student("Ali")
for day in (1, 2, 3):
    sit(a, mock, 10, start + timedelta(days=day))
print("   three perfect sittings of a published mock -> homework %s" % points("Ali"))
assert points("Ali") == 0.0

print("\n2. A TEST SET AS HOMEWORK IS HOMEWORK")
unit = a_test("Unit 1 test", marks=10)
due = start + timedelta(days=5)
wb = set_as_homework(unit, due, "Unit 1 test", also="Workbook unit 1")
b = student("Bek")
sit(b, unit, 6, due - timedelta(days=1))
db.execute("INSERT INTO submissions (student_id, assignment_id, status, score, created_at, kind)"
           " VALUES (?,?,'graded',10,?,'photo')", (b, wb, core.iso(due - timedelta(days=1))))
db.commit()
print("   test 6/10, workbook 10/10 -> average 8 -> homework %s" % points("Bek"))
assert points("Bek") == round(8 / 10 * core.HOMEWORK_PER_SET, 2)

print("\n3. ONLY THE FIRST SITTING BEFORE THE DEADLINE")
sit(b, unit, 10, due - timedelta(hours=12))          # a perfect retake
print("   a perfect retake changes nothing -> homework %s" % points("Bek"))
assert points("Bek") == round(8 / 10 * core.HOMEWORK_PER_SET, 2)
c = student("Dil")
sit(c, unit, 10, due + timedelta(hours=2))
print("   sat perfectly two hours late -> homework %s" % points("Dil"))
assert points("Dil") == 0.0
rows = {r["student"]["name"]: r for r in core.championship(db)["rows"]}
assert rows["Dil"]["late"] >= 1

print("\n4. NOT SAT BY THE DEADLINE IS A NOUGHT, LIKE MISSING HOMEWORK")
e = student("Eva")
db.commit()
rows = {r["student"]["name"]: r for r in core.championship(db)["rows"]}
print("   sat nothing -> homework %s, not handed %s" % (points("Eva"), rows["Eva"]["not_handed"]))
assert points("Eva") == 0.0 and rows["Eva"]["not_handed"] == 2

print("\n5. BEFORE ITS DEADLINE IT IS STILL TO COME")
soon = a_test("Unit 2 test", marks=10)
set_as_homework(soon, core.now() + timedelta(days=2), "Unit 2 test")
db.commit()
rows = {r["student"]["name"]: r for r in core.championship(db)["rows"]}
print("   pending for Eva:", rows["Eva"]["pending"])
assert rows["Eva"]["pending"] == 1

print("\n6. A TRIAL SITTING CAN BE RUBBED OUT")
gul = student("Gul")
att = sit(gul, unit, 10, due - timedelta(days=2))
print("   sat it perfectly -> homework %s" % points("Gul"))
assert points("Gul") == round(5 / 10 * core.HOMEWORK_PER_SET, 2)     # 10 and a missing 0
core.drop_attempt(db, att)
db.commit()
print("   removed -> homework %s" % points("Gul"))
assert points("Gul") == 0.0

print("\n7. THE TEST'S PAGE SAYS SO")
import server
src = open(os.path.join(ROOT, "server.py")).read()
assert "Count in the league" not in src.split("def view_test(")[1].split("def view_test_writing")[0]
assert "earns no league points" in src
print("   no switch to put practice in the league; the page says practice earns nothing")

print("\nALL GOOD")
