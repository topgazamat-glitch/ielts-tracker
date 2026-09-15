"""A unit's homework: found once, not typed twice.

Run me with:  python3 run_tests.py unithw
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
core.seed_prompts(db)

lvl = db.execute("SELECT id FROM levels WHERE name='Elementary'").fetchone()["id"]
g = db.execute("INSERT INTO groups (name, join_code, level_id, created_at)"
               " VALUES ('E1','E1',?,?)",
               (lvl, core.iso(core.now()))).lastrowid
sid = db.execute("INSERT INTO students (name, group_id, active, created_at)"
                 " VALUES ('Aziza',?,1,?)", (g, core.iso(core.now()))).lastrowid

tid = core.load_test(db, {
    "level": "Elementary", "number": 11, "title": "E11BD Entertainment (booklet)",
    "passages": {}, "layout": '<div class="booklet"><p>hello</p></div>',
    "questions": [{"num": 1, "kind": "typed", "prompt": "q", "answer": "yes",
                   "options": []}]})
db.execute("UPDATE dtests SET published=1 WHERE id=?", (tid,))
db.commit()

print("1. THE PLAN FINDS WHAT ALREADY EXISTS")
plan = core.unit_homework(db, g, 11, pair="B&D", kind="essay", practice="3")
kinds = [i["kind"] for i in plan["items"]]
print("   items:", kinds)
assert kinds == ["workbook", "booklet", "writing", "practice"]
booklet = plan["items"][1]
print("   the handout:", booklet["title"], "-> test", booklet["test_id"])
assert booklet["test_id"] == tid, "the booklet on that shelf should be found"
writing = plan["items"][2]
print("   the question:", (writing["prompt"] or "")[:60])
assert writing["prompt"], "a question should come from the bank"

print("\n2. WITHOUT A BOOKLET IT IS STILL A LINE OF HOMEWORK")
none_plan = core.unit_homework(db, g, 7, pair="A&C")
print("   unit 7:", none_plan["items"][1]["title"],
      "-> test", none_plan["items"][1]["test_id"])
assert none_plan["items"][1]["test_id"] is None

print("\n3. A BOOKLET IS TICKED BY SITTING IT, NOT BY A PHOTOGRAPH")
due = core.iso(core.now() + timedelta(days=1))
ids = []
for title, test_id in (("Workbook unit 11 B&D", None),
                       ("E11BD Entertainment", tid),
                       ("Writing — Entertainment", None)):
    ids.append(db.execute(
        "INSERT INTO assignments (group_id, title, due_at, created_at,"
        " published, test_id) VALUES (?,?,?,?,1,?)",
        (g, title, due, core.iso(core.now()), test_id)).lastrowid)
db.commit()
items = db.execute("SELECT * FROM assignments WHERE group_id=?", (g,)).fetchall()
before = core.set_progress(db, sid, items)
print("   before sitting it: %d of %d" % (before["done"], before["total"]))
assert before["done"] == 0

qs = core.test_questions(db, tid)
att = core.start_attempt(db, tid, sid)
core.submit_attempt(db, att, {q["id"]: "yes" for q, _o in qs})
after = core.set_progress(db, sid, items)
print("   after sitting it:  %d of %d" % (after["done"], after["total"]))
assert after["done"] == 1, "the booklet counts as handed in"

print("\n4. THE BOOKLET IS NOT SCORED TWICE")
core.start_season(db, core.now() - timedelta(days=2))
row = {r["student"]["name"]: r for r in core.championship(db)["rows"]}["Aziza"]
print("   homework points:", row["points"]["homework"])
# the sat test scores; the assignment pointing at it must not also count as
# a missed piece of homework
assert row["points"]["homework"] == core.HOMEWORK_PER_SET, row["points"]

print("\nALL GOOD")
