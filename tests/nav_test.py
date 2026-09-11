"""Nav — see the assertions for what it guarantees.

Run me with:  python3 run_tests.py            (all of them)
              python3 tests/nav_test.py   (just this one)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
FIXTURES = os.path.join(ROOT, "tests", "fixtures")

import tempfile, shutil, threading, time, re, http.cookiejar, urllib.request, urllib.parse, random
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None); os.environ["TEACHER_PASSWORD"] = "testpw123"

import core, server
core.init_db(); db = core.connect(); cfg = core.load_config()
from datetime import timedelta

# a school with enough in it that every page has something to render
gids = []
for i, nm in enumerate(["Beginner", "Elementary", "Intermediate"]):
    gids.append(db.execute("INSERT INTO groups (name, join_code, created_at) VALUES (?,?,?)",
                (nm, "CD%02d" % i, core.iso(core.now()))).lastrowid)
random.seed(3)
for i in range(18):
    sid = db.execute("INSERT INTO students (name, group_id, active, token, created_at)"
          " VALUES (?,?,1,?,?)", ("Student %02d" % i, gids[i % 3],
          "tok%016d" % i, core.iso(core.now()))).lastrowid
    a = db.execute("INSERT INTO assignments (group_id, title, created_at, published)"
                   " VALUES (?,?,?,1)", (gids[i % 3], "Task %d" % i,
                   core.iso(core.now()))).lastrowid
    for k in range(3):
        db.execute("INSERT INTO submissions (student_id, assignment_id, status, score,"
                   " created_at, kind) VALUES (?,?,'graded',?,?,'photo')",
                   (sid, a, random.choice([6,7,8,9]), core.iso(core.now() - timedelta(days=k+1))))
    db.execute("INSERT INTO lesson_marks (student_id, day, punctuality, behaviour,"
               " participation, created_at) VALUES (?,?,4,4,4,?)",
               (sid, core.local_day(core.now() - timedelta(days=1), cfg), core.iso(core.now())))
wl = db.execute("INSERT INTO word_lists (title, active, created_at) VALUES ('Unit 1',1,?)",
                (core.iso(core.now()),)).lastrowid
for w in ["abandon", "ability", "abolish"]:
    db.execute("INSERT INTO words (list_id, term, translation) VALUES (?,?,?)",
               (wl, w, "meaning of " + w))
core.start_season(db, core.now() - timedelta(days=5))
core.save_song(db, core.local_day(core.now(), cfg), "x.mp3",
               b"\xff\xfb\x90\x00" + b"\0"*9000, "Test song", "Someone")
db.commit(); db.close()

srv = server.Server(("127.0.0.1", 8805), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start(); time.sleep(0.4)
B = "http://127.0.0.1:8805"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(B + "/login", urllib.parse.urlencode({"password": "testpw123"}).encode()).read()

PAGES = [("/", "Overview"), ("/queue", "Grade"), ("/homework", "Homework"),
         ("/ratings", "Ratings"), ("/championship", "League"),
         ("/assignments", "Assignments"), ("/groups", "Groups"),
         ("/roster", "Students"), ("/materials", "Materials"),
         ("/vocab", "Vocabulary"), ("/music", "Music"), ("/play", "Play"),
         ("/questions", "Questions")]
print("%-14s %-8s %s" % ("PAGE", "STATUS", "MUSIC WHEN YOU CLICK IT"))
smooth = fallback = 0
for path, label in PAGES:
    try:
        r = op.open(B + path); html = r.read().decode("utf-8", "replace"); code = r.status
    except Exception as e:
        print("%-14s %-8s ERROR %s" % (label, "?", e)); continue
    m = re.search(r"<main[^>]*>(.*)</main>", html, re.S)
    body = m.group(1) if m else ""
    has = "<script" in body
    if has: fallback += 1
    else: smooth += 1
    print("%-14s %-8s %s" % (label, code, "reloads (has its own script)" if has
                             else "keeps playing"))
print("\n%d pages keep the music, %d reload" % (smooth, fallback))

# student portal tabs
print("\nStudent portal tabs:")
for tab in ["home", "materials", "progress", "class", "goal", "profile"]:
    r = urllib.request.urlopen(B + "/s/tok0000000000000000?tab=" + tab)
    html = r.read().decode("utf-8", "replace")
    m = re.search(r"<main[^>]*>(.*)</main>", html, re.S)
    has = "<script" in (m.group(1) if m else "")
    print("  %-9s %s" % (tab, "reloads" if has else "keeps playing"))
srv.shutdown(); shutil.rmtree(tmp)
