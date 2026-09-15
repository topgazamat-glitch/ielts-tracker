"""A half-finished booklet survives a closed tab.

Run me with:  python3 run_tests.py booksave
"""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None)
import core
core.init_db(); db = core.connect()

lvl = db.execute("SELECT id FROM levels WHERE name='Elementary'").fetchone()["id"]
g = db.execute("INSERT INTO groups (name, join_code, level_id, created_at)"
               " VALUES ('G','G',?,?)", (lvl, core.iso(core.now()))).lastrowid
sid = db.execute("INSERT INTO students (name, group_id, active, created_at)"
                 " VALUES ('Nodira',?,1,?)", (g, core.iso(core.now()))).lastrowid
tid = core.load_test(db, {
    "level": "Elementary", "number": 1, "title": "T", "passages": {},
    "layout": '<div class="booklet"></div>',
    "questions": [
        {"num": 1, "kind": "typed", "prompt": "a", "answer": "red", "options": []},
        {"num": 2, "kind": "typed", "prompt": "b", "answer": "blue", "options": []},
        {"num": 3, "kind": "open", "prompt": "c", "answer": None, "options": []},
    ]})
db.execute("UPDATE dtests SET published=1 WHERE id=?", (tid,)); db.commit()
qs = core.test_questions(db, tid)
ids = [q["id"] for q, _o in qs]

print("1. TYPING IS KEPT WITHOUT HANDING IT IN")
att = core.start_attempt(db, tid, sid)
core.save_progress(db, att, {ids[0]: "red", ids[2]: "my own words"})
back = core.attempt_answers(db, att)
print("   kept:", back)
assert back == {ids[0]: "red", ids[2]: "my own words"}
open_still = db.execute("SELECT finished_at FROM dattempts WHERE id=?",
                        (att,)).fetchone()["finished_at"]
print("   still unfinished:", open_still is None)
assert open_still is None, "saving must not hand the paper in"

print("\n2. COMING BACK REUSES THE SAME PAPER")
again = core.start_attempt(db, tid, sid)
print("   same attempt:", again == att)
assert again == att
assert core.attempt_answers(db, again)[ids[0]] == "red"

print("\n3. TYPING OVER AN ANSWER REPLACES IT")
core.save_progress(db, att, {ids[0]: "green"})
print("   now:", core.attempt_answers(db, att)[ids[0]])
assert core.attempt_answers(db, att)[ids[0]] == "green"

print("\n4. NOTHING IS MARKED UNTIL IT IS HANDED IN")
rows = db.execute("SELECT correct FROM dresponses WHERE attempt_id=?", (att,)).fetchall()
print("   correct flags before handing in:", [r["correct"] for r in rows])
assert all(r["correct"] is None for r in rows)

print("\n5. HANDING IN MARKS WHAT IS THERE")
core.save_progress(db, att, {ids[1]: "blue"})
score, total = core.submit_attempt(db, att, core.attempt_answers(db, att))
print("   scored %d of %d (the open box is not counted)" % (score, total))
assert total == 2, "only the two with a key are scored"
assert score == 1, "green is wrong, blue is right"

print("\n6. A HANDED-IN PAPER CANNOT BE QUIETLY EDITED")
n = core.save_progress(db, att, {ids[0]: "red"})
print("   boxes kept after handing in:", n)
assert n == 0

print("\nALL GOOD")
