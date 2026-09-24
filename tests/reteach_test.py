"""What to reteach: the page that reads the answers back to the teacher.

Every answer writes a row to word_progress, and until now nothing told the
teacher what was in it. These checks are about the two ways such a page
lies: by calling something a finding when one student had a bad evening,
and by missing the student whose homework is fine but whose words are not.

Run me with:  python3 run_tests.py reteach
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
now = core.now()
iso = core.iso

g1 = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('114','A',?)",
                (iso(now),)).lastrowid
g2 = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('116','B',?)",
                (iso(now),)).lastrowid
names = ["Aziz", "Malika", "Jasur", "Nodira", "Bek"]
ids = [core.add_student(db, n, g1) for n in names]
other = core.add_student(db, "Farida", g2)

lid = db.execute("INSERT INTO word_lists (title, active, created_at, kind)"
                 " VALUES ('Unit 7B words',1,?,'vocab')", (iso(now),)).lastrowid
words = {}
for term in ("borrow", "lend", "easy", "hard", "rare", "private"):
    words[term] = db.execute(
        "INSERT INTO words (list_id, term, translation) VALUES (?,?,?)",
        (lid, term, term + "-uz")).lastrowid
db.commit()

fails = []
checks = 0


def check(what, cond):
    global checks
    checks += 1
    print(("  ok  " if cond else "  FAIL") + "  " + what)
    if not cond:
        fails.append(what)


def progress(sid, term, seen, correct, due=None, last=None):
    db.execute(
        "INSERT INTO word_progress (student_id, word_id, seen, correct, streak,"
        " next_due, last_seen) VALUES (?,?,?,?,0,?,?)",
        (sid, words[term], seen, correct,
         iso(due or now + core.timedelta(days=3)), iso(last or now)))


# "borrow" is genuinely hard: four students, plenty of answers, mostly wrong
for sid in ids[:4]:
    progress(sid, "borrow", 6, 1)
# "lend" is hard too, but slightly better
for sid in ids[:4]:
    progress(sid, "lend", 5, 2)
# "rare" looks terrible but only one student has ever seen it
progress(ids[0], "rare", 20, 2)
# "easy" is easy
for sid in ids:
    progress(sid, "easy", 6, 6)
# "private" is borderline but above the line
for sid in ids[:3]:
    progress(sid, "private", 10, 8)
# the other class fails something else entirely
progress(other, "hard", 30, 3)
db.commit()

hard = core.reteach_words(db, g1)
terms = [h["term"] for h in hard]
check("the word the class fails most comes first", terms[:1] == ["borrow"])
check("a second hard word is listed", "lend" in terms)
check("a word only one student has met is not a finding", "rare" not in terms)
check("a word the class knows is not listed", "easy" not in terms)
check("a word above the line is not listed", "private" not in terms)
check("another class's trouble stays in that class",
      "hard" not in terms and [h["term"] for h in core.reteach_words(db, g2)] == [])
top = hard[0]
check("the figures are the class's, not one student's",
      top["who"] == 4 and top["seen"] == 24 and top["correct"] == 4)
check("the percentage is right", top["pct"] == 17)
check("the list it came from is named", top["list"] == "Unit 7B words")

# ---------------------------------------------------------------- the steps
def run(sid, correct, when=None):
    db.execute(
        "INSERT INTO solo_runs (student_id, list_id, q_count, seconds, score,"
        " correct, started_at, finished_at) VALUES (?,?,20,20,0,?,?,?)",
        (sid, lid, correct, iso(now), iso(when or now)))


for sid in ids:                       # a step the class keeps failing
    run(sid, 11)
lid2 = db.execute("INSERT INTO word_lists (title, active, created_at, kind)"
                  " VALUES ('Unit 1A words',1,?,'vocab')", (iso(now),)).lastrowid
for sid in ids:
    run(sid, 19)
db.execute("UPDATE solo_runs SET list_id=? WHERE correct=19", (lid2,))
# one run only: not enough to judge a step on
lid3 = db.execute("INSERT INTO word_lists (title, active, created_at, kind)"
                  " VALUES ('Unit 9C words',1,?,'vocab')", (iso(now),)).lastrowid
run(ids[0], 2)
db.execute("UPDATE solo_runs SET list_id=? WHERE correct=2", (lid3,))
db.commit()

steps = core.reteach_steps(db, g1)
titles = [s["title"] for s in steps]
check("the worst step is first", titles[:1] == ["Unit 7B words"])
check("a step played once is not judged", "Unit 9C words" not in titles)
check("the pass count is counted", steps[0]["passes"] == 0)
check("the average is the class's", steps[0]["pct"] == 55)
check("the step everyone passes ranks last", titles[-1] == "Unit 1A words")

# ------------------------------------------------------------ the students
# Aziz: homework perfect, vocabulary poor - invisible to the Overview
a = db.execute("INSERT INTO assignments (group_id, title, created_at, published,"
               " due_at) VALUES (?,?,?,1,?)",
               (g1, "HW", iso(now), iso(now + core.timedelta(days=1)))).lastrowid
for sid in ids:
    db.execute("INSERT INTO submissions (student_id, assignment_id, status,"
               " score, created_at, kind) VALUES (?,?, 'graded', 9, ?, 'photo')",
               (sid, a, iso(now)))
for term in ("hard",):
    for sid in ids[:1]:
        progress(sid, term, 60, 20)
db.commit()

who = core.quiet_strugglers(db, g1)
by = {w["name"]: w for w in who}
check("the student with poor recall is named", "Aziz" in by)
check("and the page says why", any("%" in r for r in by["Aziz"]["reasons"]))
check("it notices that the homework looks fine", by["Aziz"]["homework_fine"])

# Bek has stopped playing altogether
db.execute("UPDATE word_progress SET last_seen=? WHERE student_id=?",
           (iso(now - core.timedelta(days=30)), ids[4]))
# and has a pile of revision waiting
for term in ("borrow", "lend", "easy"):
    db.execute("UPDATE word_progress SET next_due=? WHERE student_id=? AND word_id=?",
               (iso(now - core.timedelta(days=2)), ids[4], words[term]))
db.commit()
who = core.quiet_strugglers(db, g1)
bek = next((w for w in who if w["name"] == "Bek"), None)
check("a student who has stopped playing is found", bek is not None)
check("and is told to be quiet, in those words",
      bek and any("nothing since" in r for r in bek["reasons"]))
check("a student who is fine is not on the list",
      "Malika" not in {w["name"] for w in who} or
      by.get("Malika", {}).get("reasons"))
check("the other class is not mixed in",
      "Farida" not in {w["name"] for w in who})

whole = core.reteach(db, g1)
check("the page gets all three answers at once",
      set(whole) == {"words", "steps", "students"} and whole["words"])

print()
print("reteach: %d checks, %d failed" % (checks, len(fails)))
sys.exit(1 if fails else 0)
