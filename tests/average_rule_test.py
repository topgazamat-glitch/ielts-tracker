"""Every piece of homework is out of ten, marked by hand or by itself, and
the average is over every piece whose deadline has gone - one not done is a
nought. Four set, three done: averaged over four. A piece handed in and not
yet marked waits for its mark.

Run me with:  python3 run_tests.py average
"""
import os
import sys
import tempfile
from datetime import timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["DATA_DIR"] = tempfile.mkdtemp(); os.environ.pop("TELEGRAM_TOKEN", None)
import core, parents

db = core.init_db()
now = core.now()
fails, checks = [], 0


def check(what, cond):
    global checks
    checks += 1
    print(("  ok  " if cond else "  FAIL") + "  " + what)
    if not cond:
        fails.append(what)


g = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('214','A',?)",
               (core.iso(now),)).lastrowid
ann = core.add_student(db, "Ann", g)
bek = core.add_student(db, "Bek", g)


def piece(title, days_ago_due=1):
    return db.execute("INSERT INTO assignments (group_id, title, created_at, published, due_at)"
                      " VALUES (?,?,?,1,?)", (g, title, core.iso(now - timedelta(days=5)),
                                              core.iso(now - timedelta(days=days_ago_due)))).lastrowid


def hand_in(sid, aid, score=None):
    db.execute("INSERT INTO submissions (student_id, assignment_id, status, score, created_at, kind, draft)"
               " VALUES (?,?,?,?,?,'photo',0)", (sid, aid, "graded" if score is not None else "pending",
                                                score, core.iso(now - timedelta(days=2))))


set4 = [piece("Workbook"), piece("Destination"), piece("Handout"), piece("Writing")]
for aid, score in zip(set4, (8, 9, 7)):
    hand_in(ann, aid, score)                     # the fourth is not done
for aid, score in zip(set4, (10, 10, 10)):
    hand_in(bek, aid, score)
hand_in(bek, set4[3])                            # handed in, not marked yet
db.commit()

st = core.student_stats(db, ann)
check("four set, three done - 8, 9, 7 - is 6 on average, not 8", st["average"] == 6.0)
row = db.execute("SELECT * FROM students WHERE id=?", (ann,)).fetchone()
scores, late, missing, waiting, _p, batches = core.homework_marks(
    db, row, core.iso(now - timedelta(days=10)), core.iso(now), [])
check("the league's set is the same average", round(sum(scores) / len(scores), 2) == 6.0 and missing == 1)
p = parents.period("week")
rep = parents.student_period(db, row, core.iso(now - timedelta(days=10)), core.iso(now), core.load_config())
check("and so is the parents' report", rep["average"] == 6.0)
check("the marks of the work done alone are kept for the ranking", st["done_average"] == 8.0)
check("a piece waiting for its mark is not a nought - it waits",
      core.student_stats(db, bek)["average"] == 10.0)

print()
print("average_rule: %d checks, %d failed" % (checks, len(fails)))
sys.exit(1 if fails else 0)
