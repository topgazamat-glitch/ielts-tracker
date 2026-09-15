"""A test that marks itself earns league points, once.

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


def a_test(title, marks=10, published=1, in_league=1, level=None):
    data = {"level": "Intermediate", "number": 1, "title": title,
            "passages": {}, "questions": [
                {"num": i + 1, "prompt": "q%d" % i, "answer": "yes",
                 "kind": "typed", "options": []} for i in range(marks)]}
    tid = core.load_test(db, data)
    db.execute("UPDATE dtests SET published=?, in_league=?, level_id=? WHERE id=?",
               (published, in_league, level if level is not None else lvl, tid))
    return tid


def sit(sid, tid, right, when=None):
    """Sit a test getting `right` of its questions correct."""
    qs = core.test_questions(db, tid)
    att = core.start_attempt(db, tid, sid)
    core.submit_attempt(db, att, {q["id"]: ("yes" if i < right else "no")
                                  for i, (q, _o) in enumerate(qs)})
    if when:
        db.execute("UPDATE dattempts SET finished_at=? WHERE id=?",
                   (core.iso(when), att))
    db.commit()
    return att


def points(name):
    rows = {r["student"]["name"]: r for r in core.championship(db)["rows"]}
    return rows[name]["points"]["homework"]


print("1. A SAT TEST IS WORTH POINTS")
t1 = a_test("Unit 1", marks=10)
a = student("Ali")
sit(a, t1, 10, start + timedelta(days=1))
db.commit()
print("   10 of 10 on one test -> homework %s" % points("Ali"))
assert points("Ali") == core.HOMEWORK_PER_SET, points("Ali")

b = student("Bek")
sit(b, t1, 5, start + timedelta(days=1))
db.commit()
print("    5 of 10 on one test -> homework %s" % points("Bek"))
assert points("Bek") == round(core.HOMEWORK_PER_SET / 2, 2)

print("\n2. TESTS ADD UP LIKE FIXTURES")
t2 = a_test("Unit 2", marks=10)
sit(a, t2, 10, start + timedelta(days=2))
db.commit()
print("   a second perfect test -> homework %s" % points("Ali"))
assert points("Ali") == core.HOMEWORK_PER_SET * 2

print("\n3. RETAKING DOES NOT RAISE THE SCORE")
before = points("Bek")
sit(b, t1, 10, start + timedelta(days=3))       # a perfect retake
db.commit()
print("   Bek retakes 5/10 and gets 10/10 -> homework %s (was %s)"
      % (points("Bek"), before))
assert points("Bek") == before, "only the first sitting counts"

print("\n4. A TEST LEFT OUT OF THE LEAGUE SCORES NOTHING")
t3 = a_test("Practice only", marks=10, in_league=0)
c = student("Dil")
sit(c, t3, 10, start + timedelta(days=2))
db.commit()
print("   10 of 10 on an excluded test -> homework %s" % points("Dil"))
assert points("Dil") == 0.0

print("\n5. AN UNPUBLISHED TEST SCORES NOTHING")
t4 = a_test("Draft", marks=10, published=0)
d = student("Eva")
sit(d, t4, 10, start + timedelta(days=2))
db.commit()
print("   10 of 10 on a draft -> homework %s" % points("Eva"))
assert points("Eva") == 0.0

print("\n6. NOT SITTING A TEST IS NOT A NOUGHT, IT IS NO POINTS")
e = student("Fara")
db.commit()
print("   sat nothing -> homework %s" % points("Fara"))
assert points("Fara") == 0.0
# and it does not drag down someone who did sit one
sit(e, t1, 10, start + timedelta(days=4))
db.commit()
print("   then sits one perfectly -> homework %s" % points("Fara"))
assert points("Fara") == core.HOMEWORK_PER_SET

print("\n7. A PAUSED STRETCH DOES NOT COUNT")
core.pause_season(db, start + timedelta(days=6))
core.resume_season(db, start + timedelta(days=8))
t5 = a_test("Unit 3", marks=10)
sit(a, t5, 10, start + timedelta(days=7))
db.commit()
print("   a perfect test sat while paused -> homework %s" % points("Ali"))
assert points("Ali") == core.HOMEWORK_PER_SET * 2, "the pause should swallow it"



print("\n8. A TRIAL SITTING CAN BE RUBBED OUT")
gid = student("Gul")
att = sit(gid, t1, 10, start + timedelta(days=5))  # before the pause
db.commit()
print("   sat it perfectly -> homework %s" % points("Gul"))
assert points("Gul") == core.HOMEWORK_PER_SET
left = db.execute("SELECT COUNT(*) c FROM dresponses WHERE attempt_id=?",
                  (att,)).fetchone()["c"]
core.drop_attempt(db, att)
after = db.execute("SELECT COUNT(*) c FROM dresponses WHERE attempt_id=?",
                   (att,)).fetchone()["c"]
db.commit()
print("   removed: %d answers before, %d after -> homework %s"
      % (left, after, points("Gul")))
assert after == 0, "the answers go with the sitting"
assert points("Gul") == 0.0, "the league forgets it"

# and the first-sitting rule now applies to whatever they do next
sit(gid, t1, 5, start + timedelta(days=9))   # after the pause of step 7
db.commit()
print("   sits it again, 5 of 10 -> homework %s" % points("Gul"))
assert points("Gul") == round(core.HOMEWORK_PER_SET / 2, 2)

print("\nALL GOOD")
