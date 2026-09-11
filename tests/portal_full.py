"""Portal full — see the assertions for what it guarantees.

Run me with:  python3 run_tests.py            (all of them)
              python3 tests/portal_full.py   (just this one)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
FIXTURES = os.path.join(ROOT, "tests", "fixtures")

import tempfile, shutil, re, random
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp

import core, server
core.init_db()
db = core.connect()
cfg = core.load_config()
from datetime import timedelta

# six classes, 57 students, like the real school
gids = []
for i, nm in enumerate(["Beginner", "Elementary", "Pre-Int", "Intermediate",
                        "IELTS Novice", "IELTS Standard"]):
    gids.append(db.execute("INSERT INTO groups (name, join_code, created_at)"
                           " VALUES (?,?,?)", (nm, "C%03d" % i, core.iso(core.now()))).lastrowid)
sids = []
for i in range(57):
    sids.append(db.execute("INSERT INTO students (name, group_id, active, token,"
                " created_at) VALUES (?,?,1,?,?)",
                ("Student %02d" % (i + 1), gids[i % 6], "tok%d" % i,
                 core.iso(core.now()))).lastrowid)
db.commit()

start = core.now() - timedelta(days=30)
core.start_season(db, start)
random.seed(7)
a = db.execute("INSERT INTO assignments (group_id, title, created_at) VALUES (?,?,?)",
               (gids[0], "HW", core.iso(core.now()))).lastrowid
for sid in sids:
    for k in range(random.choice([0, 1, 2, 4, 5, 6])):
        db.execute("INSERT INTO submissions (student_id, assignment_id, status, score,"
                   " created_at, kind) VALUES (?,?,'graded',?,?,'photo')",
                   (sid, a, random.choice([5, 6, 7, 8, 9, 10]),
                    core.iso(start + timedelta(days=k + 1))))
    for d in range(random.choice([0, 3, 9, 15, 15])):
        db.execute("INSERT OR REPLACE INTO lesson_marks (student_id, day, punctuality,"
                   " behaviour, participation, created_at) VALUES (?,?,?,?,?,?)",
                   (sid, core.local_day(start + timedelta(days=d), cfg),
                    random.randint(3, 5), random.randint(3, 5), random.randint(3, 5),
                    core.iso(core.now())))
db.commit()

st = db.execute("SELECT * FROM students WHERE name='Student 07'").fetchone()
h = server.portal_class(db, st, st["token"], "school")
rows = h.count("<tr")
print("school view: %d bytes, %d table rows" % (len(h), rows))
c = server.portal_class(db, st, st["token"], "class")
print("class view: %d rows (their class only)" % c.count("<tr"))
assert c.count("<tr") < rows, "the class view must be shorter"
assert "Class standings" not in h, "the second leaderboard must be gone"
print("own row anchored:", 'id="me"' in h)
print("find-me link:", 'href="#me"' in h)
print("no teacher links leaked:", "/students/" not in h)
champ = core.championship(db)
print("eligible: %d of %d, finished: %d" % (champ["eligible"], len(champ["rows"]), champ["finished"]))
m = re.search(r"You (are|need)[^<]*", h); print("standing:", m.group(0) if m else "none")
m = re.search(r"below the line[^<]*", h); print("line note:", bool(m))
# show the top of the league as a student sees it
tbl = h[h.index("<th>Class</th>"):]
for line in re.findall(r"<tr.*?</tr>", tbl)[:6]:
    txt = re.sub(r"<[^>]+>", " ", line)
    print("   ", " ".join(txt.split()))
db.close(); shutil.rmtree(tmp)
