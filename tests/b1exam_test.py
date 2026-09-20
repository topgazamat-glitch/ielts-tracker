"""The B1+ mock: the shape of the real paper, and a paper that marks itself.

Run me with:  python3 run_tests.py b1exam
              python3 tests/b1exam_test.py
"""
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "exams"))

tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None)
import core
import b1plus_mock_final as p

print("1. IT IS BUILT TO THE SHAPE OF THE REAL B1+ PAPER")
listening = (len(p.PART1) + len(p.PART2["gaps"]) + len(p.PART3["questions"])
             + len(p.PART4["statements"]))
reading = (len(p.R_PART1["questions"]) + len(p.R_PART2["statements"])
           + len(p.R_PART3["questions"]) + len(p.R_PART4["gaps"])
           + len(p.R_PART5["gaps"]))
print("   listening %d marks · reading %d marks · writing %d tasks"
      % (listening, reading, 2))
assert listening == 20, listening
assert reading == 25, reading

# four options is what separates the B1+ paper from the A2 one
for q in p.R_PART1["questions"] + p.R_PART3["questions"]:
    assert len(q["options"]) == 4, (q["q"], len(q["options"]))
for g in p.R_PART4["gaps"]:
    assert len(g["options"]) == 4, g["q"]
print("   every reading choice offers four options, as the real paper does")

# the numbering a student is told to follow
assert [q["q"] for q in p.R_PART1["questions"]] == [1, 2, 3, 4, 5]
assert [g["q"] for g in p.R_PART5["gaps"]] == [21, 22, 23, 24, 25]
assert [i["q"] for i in p.PART1] == [1, 2, 3, 4, 5]
assert [s["q"] for s in p.PART4["statements"]] == [16, 17, 18, 19, 20]
print("   reading runs 1-25 and listening 1-20, with no gaps")

# every listening question has a recording that could be read aloud
for it in p.PART1:
    assert it["lines"] and all(len(t.split()) > 2 for _v, t in it["lines"])
for part in (p.PART2, p.PART3, p.PART4):
    assert part["lines"]
print("   every listening part has a script to record")

print()
print("2. THE ANSWERS ARE INSIDE THE PAPER")
for q in p.R_PART1["questions"] + p.R_PART3["questions"]:
    assert q["answer"] in "ABCD" and len(q["answer"]) == 1, q
for g in p.R_PART4["gaps"]:
    assert g["answer"] in "ABCD", g
for s in p.R_PART2["statements"] + p.PART4["statements"]:
    assert s["answer"] in ("YES", "NO"), s
for it in p.PART1:
    assert it["answer"] in "ABC", it
print("   every key is one of the options actually offered")

# an open cloze answer has to be a word a student could think of
for g in p.R_PART5["gaps"]:
    for w in g["answer"].split("/"):
        assert w.strip() and " " not in w.strip(), g
print("   every open-cloze answer is a single word")

print()
print("3. A PERFECT PAPER SCORES FULL MARKS ON THE WEBSITE")
core.init_db(); db = core.connect()
g = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('G','G',?)",
               (core.iso(core.now()),)).lastrowid
sid = db.execute("INSERT INTO students (name, group_id, active, created_at)"
                 " VALUES ('S',?,1,?)", (g, core.iso(core.now()))).lastrowid
paper = json.load(open(os.path.join(ROOT, "exams", "b1plus_mock_digital.json")))
tid = core.load_test(db, paper)
db.execute("UPDATE dtests SET published=1 WHERE id=?", (tid,))
db.commit()

row = db.execute("SELECT minutes, strict, once FROM dtests WHERE id=?",
                 (tid,)).fetchone()
print("   %s minutes · one sitting only: %s" % (row["minutes"], bool(row["once"])))
assert row["once"] == 1

qs = core.test_questions(db, tid)
kinds = {}
for q, _o in qs:
    kinds[q["kind"]] = kinds.get(q["kind"], 0) + 1
print("   questions:", kinds)
assert kinds == {"mcq": 20, "typed": 5, "open": 2}, kinds

# the options must reach the student in the order the paper prints them
for q, opts in qs:
    letters = [o["letter"] for o in opts]
    if len(letters) == 4:
        assert letters == ["A", "B", "C", "D"], letters
    elif len(letters) == 2:
        assert letters == ["YES", "NO"], letters
print("   options keep their printed order, including YES before NO")

attempt = core.start_attempt(db, tid, sid)
given = {}
for q, _o in qs:
    if q["kind"] == "open":
        given[q["id"]] = "I am writing to tell you about the new centre."
    elif q["kind"] == "typed":
        given[q["id"]] = (q["answer"] or "").split("/")[0].strip()
    else:
        given[q["id"]] = q["answer"]
core.submit_attempt(db, attempt, given)
got = db.execute("SELECT score, total FROM dattempts WHERE id=?", (attempt,)).fetchone()
print("   scored %s of %s" % (got["score"], got["total"]))
assert (got["score"], got["total"]) == (25, 25), dict(got)

# the written answers are kept, and never scored
written = core.written_answers(db, tid)
print("   writing tasks kept for the teacher:", len(written))
assert len(written) == 2
assert all(a["text"] for part in written for a in part["answers"])

# a paper of wrong answers scores nothing, so the marking is not simply generous
attempt2 = core.start_attempt(db, tid, sid)
db.execute("UPDATE dattempts SET finished_at=NULL WHERE id=?", (attempt2,))
wrong = {}
for q, opts in qs:
    if q["kind"] == "mcq":
        other = [o["letter"] for o in opts if o["letter"] != q["answer"]]
        wrong[q["id"]] = other[0]
    elif q["kind"] == "typed":
        wrong[q["id"]] = "zzz"
core.submit_attempt(db, attempt2, wrong)
bad = db.execute("SELECT score FROM dattempts WHERE id=?", (attempt2,)).fetchone()
print("   a paper of wrong answers scores", bad["score"])
assert bad["score"] == 0, bad["score"]

print()
print("PASS  the B1+ mock is the real paper's shape and marks itself correctly")
