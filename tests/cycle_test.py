"""The cycle: who joined, who left and why, and the marks along the way.

The retention rate is the number a teacher's pay partly depends on, so the
counting has to be right in the awkward cases: a student who leaves and comes
back, a window that only half overlaps a spell, and the difference between
churn a teacher could have prevented and a family moving city.

Run me with:  python3 run_tests.py cycle
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import tempfile
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None)

import core
core.init_db(); db = core.connect()
now, iso, td = core.now(), core.iso, core.timedelta

g = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('114','A',?)",
               (iso(now),)).lastrowid
g2 = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('116','B',?)",
                (iso(now),)).lastrowid
names = ["Aziz", "Malika", "Jasur", "Nodira", "Bek", "Dilnoza"]
ids = [core.add_student(db, n, g) for n in names]
db.execute("UPDATE students SET created_at=? WHERE id IN (%s)"
           % ",".join("?" * len(ids)),
           [iso(now - td(days=120))] + ids)
db.commit()

fails, checks = [], 0


def check(what, cond):
    global checks
    checks += 1
    print(("  ok  " if cond else "  FAIL") + "  " + what)
    if not cond:
        fails.append(what)


# --------------------------------------------------------------- backfill
made = core.backfill_enrolments(db)
check("everybody already on the books gets a spell", made == len(ids))
check("running it twice adds nothing", core.backfill_enrolments(db) == 0)
e = core.current_enrolment(db, ids[0])
check("the spell starts when they joined, not today",
      e["started_at"][:10] == iso(now - td(days=120))[:10])
check("and it is open", e["ended_at"] is None)

# ----------------------------------------------------------------- leaving
check("a made-up reason is refused", core.mark_left(db, ids[0], "banana") is False)
check("a real one is accepted",
      core.mark_left(db, ids[0], "moved", when=iso(now - td(days=10))))
check("they come off the roll",
      db.execute("SELECT active FROM students WHERE id=?", (ids[0],)).fetchone()[0] == 0)
check("the spell is closed with its reason",
      core.current_enrolment(db, ids[0]) is None)
row = db.execute("SELECT * FROM enrolments WHERE student_id=?", (ids[0],)).fetchone()
check("the reason is kept", row["reason"] == "moved")

core.mark_left(db, ids[1], "bored", when=iso(now - td(days=5)))
core.mark_left(db, ids[2], "money", when=iso(now - td(days=200)))   # long ago

# ------------------------------------------------------------ coming back
core.mark_returned(db, ids[0])
check("a returning student is back on the roll",
      db.execute("SELECT active FROM students WHERE id=?", (ids[0],)).fetchone()[0] == 1)
check("and starts a second spell, leaving the first alone",
      db.execute("SELECT COUNT(*) c FROM enrolments WHERE student_id=?",
                 (ids[0],)).fetchone()["c"] == 2)
check("the closed spell still says why it ended",
      db.execute("SELECT reason FROM enrolments WHERE student_id=? AND"
                 " ended_at IS NOT NULL", (ids[0],)).fetchone()[0] == "moved")

# ------------------------------------------------------------- retention
r = core.retention(db, since=iso(now - td(days=90)))
check("someone who left before the window is not counted as leaving in it",
      r["left"] == 2)
check("and their spell is not counted as present either", r["here"] == 6)
check("the rate is over the window", r["rate"] == round(100.0 * 4 / 6, 1))
check("churn the teacher could have prevented is counted apart",
      r["ours"] == 1 and r["rate_ours"] > r["rate"])
check("a family moving city is not the teacher's fault",
      core.REASON_OURS["moved"] is False and core.REASON_OURS["bored"] is True)
check("the reasons are broken out",
      r["by_reason"].get("bored") == 1 and r["by_reason"].get("moved") == 1)

# ------------------------------------------------------------ class tests
tid = core.new_class_test(db, g, "Unit 3 vocabulary", 20,
                          iso(now - td(days=3))[:10])
core.save_class_scores(db, tid, {ids[3]: 18, ids[4]: 11, ids[5]: None},
                       absent={ids[5]})
got = core.class_test_scores(db, tid)
check("a score is kept", got[ids[3]]["score"] == 18)
check("an absent student is marked absent, not zero",
      got[ids[5]]["score"] is None and got[ids[5]]["absent"] == 1)
core.save_class_scores(db, tid, {ids[4]: 14})
check("a correction overwrites rather than duplicates",
      core.class_test_scores(db, tid)[ids[4]]["score"] == 14)
check("the test lists how many are marked",
      core.class_tests(db, g)[0]["marked"] == 2)

# ------------------------------------------------------------------ exams
n = core.save_exam(db, g, "mid", "Mid-course", 100, iso(now - td(days=30))[:10],
                   {ids[3]: 72, ids[4]: 38, ids[5]: 91}, marked_by="Azamat")
check("the exam saves a row per student", n == 3)
core.save_exam(db, g, "mid", "Mid-course", 100, iso(now - td(days=30))[:10],
               {ids[4]: 45})
check("re-marking corrects instead of adding a row",
      len([r for r in core.exam_rows(db, g, "mid")]) == 3)
check("who marked it is recorded",
      core.exam_rows(db, g, "mid")[0]["marked_by"] == "Azamat")
sp = core.exam_spread(db, "mid", g)
check("the spread is reported, not just the middle",
      sp["n"] == 3 and sp["lowest"] == 45.0 and sp["highest"] == 91.0)
check("and it is banded so the shape is visible",
      sp["bands"]["40-54"] == 1 and sp["bands"]["85+"] == 1)
check("a final with no rows says nothing rather than zero",
      core.exam_spread(db, "final", g) is None)

# ------------------------------------------------ ready for other teachers
check("every new row carries a teacher", all(
    db.execute("SELECT COUNT(*) c FROM %s WHERE teacher_id IS NULL" % t
               ).fetchone()["c"] == 0
    for t in ("enrolments", "class_tests", "exam_results")))

print()
print("cycle: %d checks, %d failed" % (checks, len(fails)))
sys.exit(1 if fails else 0)
