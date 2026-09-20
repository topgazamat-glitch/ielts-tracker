"""Exam conditions: the clock, the window rule, and what survives them.

Run me with:  python3 run_tests.py exam
"""
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None)
import core
core.init_db(); db = core.connect()

g = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('G','G',?)",
               (core.iso(core.now()),)).lastrowid
sid = db.execute("INSERT INTO students (name, group_id, active, created_at)"
                 " VALUES ('S',?,1,?)", (g, core.iso(core.now()))).lastrowid

paper = json.load(open(os.path.join(ROOT, "exams", "a2_mock_digital.json")))
tid = core.load_test(db, paper)
db.execute("UPDATE dtests SET published=1 WHERE id=?", (tid,))
db.commit()

print("1. THE PAPER KNOWS IT IS AN EXAM")
row = db.execute("SELECT minutes, strict, layout FROM dtests WHERE id=?",
                 (tid,)).fetchone()
print("   minutes: %s · leaving the page ends it: %s" % (row["minutes"], bool(row["strict"])))
assert row["minutes"] == 50 and row["strict"] == 1
assert row["layout"]

qs = core.test_questions(db, tid)
kinds = {}
for q, _o in qs:
    kinds[q["kind"]] = kinds.get(q["kind"], 0) + 1
print("   questions:", kinds)
assert kinds.get("mcq") == 20 and kinds.get("typed") == 5 and kinds.get("open") == 1

print("\n2. A PERFECT PAPER IS FULL MARKS, AND THE EMAIL IS NOT SCORED")
att = core.start_attempt(db, tid, sid)
given = {}
for q, _o in qs:
    given[q["id"]] = ("An email." if q["kind"] == "open"
                      else (q["answer"] or "").split("/")[0].strip())
score, total = core.submit_attempt(db, att, given)
print("   %d of %d" % (score, total))
assert (score, total) == (25, 25)

print("\n3. WHAT WAS TYPED SURVIVES THE CLOCK RUNNING OUT")
att2 = core.start_attempt(db, tid, sid)          # a second sitting
half = {}
for q, _o in list(qs)[:8]:
    half[q["id"]] = (q["answer"] or "A").split("/")[0].strip()
core.save_progress(db, att2, half)
kept = core.attempt_answers(db, att2)
print("   answers saved while working:", len(kept))
assert len(kept) == 8
# the clock hands in whatever is on screen; the saved answers are merged first
merged = dict(kept)
merged.update({})
s2, t2 = core.submit_attempt(db, att2, merged)
print("   handed in by the clock -> %d of %d" % (s2, t2))
assert s2 == 8, "the eight answered before the bell must still count"

print("\n4. THE PAPER REMEMBERS HOW IT ENDED")
core.finish_reason(db, att2, "time")
print("   reason:", core.how_it_ended(db, att2))
assert core.how_it_ended(db, att2) == "time"
core.finish_reason(db, att2, "left")
assert core.how_it_ended(db, att2) == "left"
print("   changed to:", core.how_it_ended(db, att2))
assert core.how_it_ended(db, 999999) == ""

print("\n5. THE PAGE CARRIES THE RULES TO THE BROWSER")
import server
book = open(os.path.join(ROOT, "static", "book.js")).read()
for needed in ('data-minutes', 'visibilitychange', 'handIn("time")',
               'handIn("left")', 'form.submit()'):
    print("   %-24s in book.js: %s" % (needed, needed in book))
    assert needed in book

print("\nALL GOOD")
