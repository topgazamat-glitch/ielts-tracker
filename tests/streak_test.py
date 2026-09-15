"""A word answered before it was due does not walk itself to "known".

Run me with:  python3 run_tests.py streak
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
core.init_db(); db = core.connect()
g = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('G','G',?)",
               (core.iso(core.now()),)).lastrowid
sid = db.execute("INSERT INTO students (name, group_id, active, created_at)"
                 " VALUES ('S',?,1,?)", (g, core.iso(core.now()))).lastrowid
wl = db.execute("INSERT INTO word_lists (group_id, title, created_at)"
                " VALUES (?,?,?)", (g, "L", core.iso(core.now()))).lastrowid
wid = db.execute("INSERT INTO words (list_id, term, translation) VALUES (?,?,?)",
                 (wl, "apple", "olma")).lastrowid
db.commit()


def streak():
    return db.execute("SELECT streak FROM word_progress WHERE student_id=?"
                      " AND word_id=?", (sid, wid)).fetchone()["streak"]


def make_due():
    db.execute("UPDATE word_progress SET next_due=? WHERE student_id=? AND word_id=?",
               (core.iso(core.now() - timedelta(minutes=1)), sid, wid))
    db.commit()


print("1. THE FIRST CORRECT ANSWER COUNTS")
core.record_answer(db, sid, wid, True)
print("   streak:", streak())
assert streak() == 1

print("\n2. ANSWERING IT AGAIN STRAIGHT AWAY DOES NOT")
for _ in range(5):
    core.record_answer(db, sid, wid, True)
print("   streak after five more, none of them due:", streak())
assert streak() == 1, "grinding must not advance it"

print("\n3. WHEN IT IS DUE, IT ADVANCES")
make_due()
core.record_answer(db, sid, wid, True)
print("   streak:", streak())
assert streak() == 2

print("\n4. THREE IN A ROW, PROPERLY SPACED, IS KNOWN")
make_due(); core.record_answer(db, sid, wid, True)
print("   streak:", streak())
assert streak() == 3

print("\n5. GETTING IT WRONG RESETS IT, DUE OR NOT")
core.record_answer(db, sid, wid, False)
print("   streak:", streak())
assert streak() == 0

print("\n6. AN EARLY CORRECT ANSWER DOES NOT PUSH THE DATE OUT EITHER")
make_due()
core.record_answer(db, sid, wid, True)
before = db.execute("SELECT next_due FROM word_progress WHERE student_id=?"
                    " AND word_id=?", (sid, wid)).fetchone()["next_due"]
core.record_answer(db, sid, wid, True)
after = db.execute("SELECT next_due FROM word_progress WHERE student_id=?"
                   " AND word_id=?", (sid, wid)).fetchone()["next_due"]
print("   due unchanged:", before == after)
assert before == after

print("\nALL GOOD")
