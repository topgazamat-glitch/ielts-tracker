"""Set homework by the unit, the way each level is taught: Beginner lesson by
lesson - A, B, then C with the unit's review and its test - the other levels in
pairs. Picking the unit fills the homework in; nothing is set until the teacher
presses the button, and a line with a digital version links to it.

Run me with:  python3 run_tests.py lessonplan
"""
import json
import os
import sys
import tempfile
from datetime import timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None); os.environ["TEACHER_PASSWORD"] = "pw"
import core, server

db = core.init_db()
now = core.now()
fails, checks = [], 0


def check(what, cond):
    global checks
    checks += 1
    print(("  ok  " if cond else "  FAIL") + "  " + what)
    if not cond:
        fails.append(what)


beg = db.execute("SELECT id FROM levels WHERE name='Beginner'").fetchone()["id"]
ele = db.execute("SELECT id FROM levels WHERE name='Elementary'").fetchone()["id"]
gb = db.execute("INSERT INTO groups (name, join_code, created_at, level_id) VALUES ('114','B1',?,?)",
                (core.iso(now), beg)).lastrowid
ge = db.execute("INSERT INTO groups (name, join_code, created_at, level_id) VALUES ('214','E1',?,?)",
                (core.iso(now), ele)).lastrowid
db.commit()

# what is on the Beginner shelf: the 4B handout and the 4B workbook
b04b = core.load_test(db, json.load(open(os.path.join(ROOT, "handouts", "b04b.json"))))
wb4b = core.load_test(db, json.load(open(os.path.join(ROOT, "handouts", "wb_b_04b.json"))))
db.execute("UPDATE dtests SET published=1 WHERE id=?", (b04b,))
db.commit()

print("1. EACH LEVEL HAS ITS OWN LESSONS")
check("Beginner: A, B, and C with the review and the test",
      [v for v, _l, _x in core.lessons_for("Beginner")] == ["A", "B", "C"]
      and core.lessons_for("Beginner")[2][2] == ["review", "unittest"])
check("the others: in pairs, as before",
      [v for v, _l, _x in core.lessons_for("Elementary")] == ["A&C", "B&D", "ASRP"])

print("\n2. THE PLAN FOR ONE BEGINNER LESSON")
plan = core.unit_homework(db, gb, 4, pair="B", kind="none")
by = {i["kind"]: i for i in plan["items"]}
check("lesson B: the workbook and the handout, nothing more",
      [i["kind"] for i in plan["items"]] == ["workbook", "booklet"])
check("the workbook line names the one lesson and finds it on the site",
      by["workbook"]["title"] == "Workbook unit 4B" and by["workbook"]["test_id"] == wb4b)
check("the handout is the 4B one", by["booklet"]["test_id"] == b04b)
plan_a = core.unit_homework(db, gb, 4, pair="A", kind="none")
check("lesson A, not on the site yet: still lines, linking to nothing",
      [(i["title"], i["test_id"]) for i in plan_a["items"]]
      == [("Workbook unit 4A", None), ("12-page handout — unit 4A", None)])

print("\n3. LESSON C BRINGS THE REVIEW AND THE UNIT TEST")
plan_c = core.unit_homework(db, gb, 4, pair="C", kind="none")
check("workbook, handout, review, unit test - in that order",
      [i["kind"] for i in plan_c["items"]] == ["workbook", "booklet", "review", "unittest"])
check("named so a teacher reads them",
      [i["title"] for i in plan_c["items"][2:]] == ["Review — unit 4", "Unit 4 progress test"])
check("with no digital version yet, they link to nothing", all(i["test_id"] is None for i in plan_c["items"][2:]))
# a unit test on the site, later: the same line finds it
ut = core.load_test(db, {"level": "Beginner", "number": 4, "title": "Unit 4 progress test", "kind": "test",
                         "passages": {}, "questions": [{"num": 1, "kind": "typed", "prompt": "q",
                                                        "answer": "a", "options": []}]})
db.execute("UPDATE dtests SET series='unittest' WHERE id=?", (ut,))
db.commit()
check("once it is there, the plan links it",
      core.unit_homework(db, gb, 4, pair="C", kind="none")["items"][3]["test_id"] == ut)
check("only on its own level and unit", core.unit_extra_test(db, "Unit 4 progress test", ele) is None
      and core.unit_extra_test(db, "Unit 5 progress test", beg) is None)
check("a workbook line is not a unit test", core.unit_extra_test(db, "Workbook unit 4C", beg) is None)

print("\n4. ON THE PAGE, AND SET")
import threading, time, urllib.request, urllib.parse, http.cookiejar
srv = server.Server(("127.0.0.1", 8897), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.4)
base = "http://127.0.0.1:8897"
teacher = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
teacher.open(base + "/login", urllib.parse.urlencode({"password": "pw"}).encode()).read()
page = teacher.open(base + "/assignments", timeout=30).read().decode()
check("the page carries every level's lessons, for when the class changes",
      'data-plans="' in page and "Lesson C + Review + Unit test" in page and "B &amp; D" in page)
picked = json.loads(teacher.open(base + "/assignments/unit.json?" + urllib.parse.urlencode(
    {"group_id": gb, "unit": 4, "pair": "C", "kind": "none"}), timeout=30).read())
check("asking for unit 4, lesson C, fills it in", [i["kind"] for i in picked["items"]]
      == ["workbook", "booklet", "review", "unittest"])
due = core.local_day(now + timedelta(days=3), core.load_config())
teacher.open(base + "/assignments/list", urllib.parse.urlencode({
    "group_id": gb, "due": due, "due_time": "21:00", "publish": "1",
    "items": "Workbook unit 4B\nUnit 4 progress test\nReview — unit 4"}).encode(), timeout=30).read()
rows = {r["title"]: r["test_id"] for r in db.execute("SELECT title, test_id FROM assignments WHERE group_id=?", (gb,))}
check("set: the workbook line links to the digital workbook", rows.get("Workbook unit 4B") == wb4b)
check("the unit test line to the unit test", rows.get("Unit 4 progress test") == ut)
check("a review with no digital version stays a line to tick", "Review — unit 4" in rows
      and rows["Review — unit 4"] is None)
srv.shutdown()

print()
print("lessonplan: %d checks, %d failed" % (checks, len(fails)))
sys.exit(1 if fails else 0)
