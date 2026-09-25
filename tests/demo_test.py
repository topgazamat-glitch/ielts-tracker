"""Demo mode: invented students for showing management, and the walls
around them.

The demo is only safe if it is impossible for a made-up name to reach a
real page or a real phone. So most of this is about the walls: the real
database is untouched, a student's link ignores the cookie, a stranger
cannot switch it on, and the thread the bot runs on never sees it.

Run me with:  python3 run_tests.py demo
"""
import json
import os
import sys
import threading
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import tempfile
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None)

import core, server
core.init_db(); db = core.connect()
now = core.iso(core.now())
g = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('114','A',?)",
               (now,)).lastrowid
real_student = core.add_student(db, "Real Student", g)
tok = db.execute("SELECT token FROM students WHERE id=?",
                 (real_student,)).fetchone()["token"]
db.commit()
real_count = db.execute("SELECT COUNT(*) c FROM students").fetchone()["c"]
db.close()

fails, checks = [], 0


def check(what, cond):
    global checks
    checks += 1
    print(("  ok  " if cond else "  FAIL") + "  " + what)
    if not cond:
        fails.append(what)


srv = server.Server(("127.0.0.1", 8851), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.4)
base = "http://127.0.0.1:8851"


class Jar(urllib.request.HTTPCookieProcessor):
    pass


def client():
    import http.cookiejar
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    op.jar = jar
    return op


def cookies(op):
    return {c.name: c.value for c in op.jar}


pw = core.load_config()["teacher_password"]
teacher = client()
teacher.open(base + "/login", urllib.parse.urlencode({"password": pw}).encode())
check("the teacher is signed in", "ta_session" in cookies(teacher))


def get(op, path):
    r = op.open(base + path, timeout=20)
    return r.read().decode()


def post(op, path, fields=None):
    return op.open(base + path, urllib.parse.urlencode(fields or {}).encode(),
                   timeout=20)


# ------------------------------------------------------------ not on yet
kpi = get(teacher, "/kpi")
check("the KPI page offers the demo", "Open the demo" in kpi)
check("no banner before it is switched on", "demobar" not in kpi)
check("the demo file does not exist until it is asked for",
      not os.path.exists(core.DEMO_PATH))

# ---------------------------------------------------------------- on
post(teacher, "/demo/on")
check("switching on sets the cookie", cookies(teacher).get("ta_demo") == "1")
check("and makes the demo file", os.path.exists(core.DEMO_PATH))
page = get(teacher, "/kpi")
check("the banner is on every teacher page", "demobar" in page and
      "demobar" in get(teacher, "/records?v=leavers"))
check("the demo class is showing", "Demo 214" in get(teacher, "/records?v=leavers")
      or "28" in page)
charts = get(teacher, "/records?v=charts&group=1")
check("the charts have something to draw", charts.count("<svg") >= 2)
check("and are willing to speak about it", "There is something here" in charts)

# ---------------------------------------------------- the real file is safe
rdb = core.connect(real=True)
check("the real database still has only the real students",
      rdb.execute("SELECT COUNT(*) c FROM students").fetchone()["c"] == real_count)
check("and no invented leavers",
      rdb.execute("SELECT COUNT(*) c FROM enrolments WHERE ended_at IS NOT NULL"
                  ).fetchone()["c"] == 0)
check("and no invented exams",
      rdb.execute("SELECT COUNT(*) c FROM exam_results").fetchone()["c"] == 0)
rdb.close()

# a write made inside the demo lands in the demo file, not the real one
demo_db_count = None
post(teacher, "/records/left", {"student": "1", "reason": "bored",
                                 "when": now[:10]})
rdb = core.connect(real=True)
check("marking a leaver in the demo does not touch a real student",
      rdb.execute("SELECT active FROM students WHERE id=?",
                  (real_student,)).fetchone()[0] == 1)
rdb.close()

# ------------------------------------------------- the walls hold
student = client()
student.jar.set_cookie(next(c for c in teacher.jar if c.name == "ta_demo"))
sp = get(student, "/s/%s?tab=home" % tok)
check("a student's link ignores the demo cookie", "Real Student" in sp
      and "demobar" not in sp)
stranger = client()
stranger.jar.set_cookie(next(c for c in teacher.jar if c.name == "ta_demo"))
try:
    code = stranger.open(base + "/kpi", timeout=20).geturl()
    check("a stranger with the cookie but no login is sent to sign in",
          code.endswith("/login"))
except urllib.error.HTTPError as e:
    check("a stranger with the cookie but no login is refused", e.code in (302, 303, 401, 403))

# the thread the bot would use never sees the switch, even mid-request
seen = {}


def bot_thread():
    d = core.connect()
    seen["count"] = d.execute("SELECT COUNT(*) c FROM students").fetchone()["c"]
    d.close()


core.demo_on(True)            # pretend this thread is inside a demo request
t = threading.Thread(target=bot_thread); t.start(); t.join()
core.demo_on(False)
check("another thread connects to the real file while this one is in the demo",
      seen["count"] == real_count)

# ---------------------------------------------------------- reset and off
post(teacher, "/demo/reset")
ddb = core.connect(real=True)
ddb.close()
core.demo_on(True)
d = core.connect()
left = d.execute("SELECT COUNT(*) c FROM enrolments WHERE ended_at IS NOT NULL"
                 ).fetchone()["c"]
d.close()
core.demo_on(False)
check("reset puts the demo back to its six leavers", left == 6)

post(teacher, "/demo/off")
check("leaving clears the cookie", "ta_demo" not in cookies(teacher)
      or cookies(teacher).get("ta_demo") == "")
after = get(teacher, "/kpi")
check("and the banner goes", "demobar" not in after)
check("without signing the teacher out", "Open the demo" in after)
srv.shutdown()

print()
print("demo: %d checks, %d failed" % (checks, len(fails)))
sys.exit(1 if fails else 0)
