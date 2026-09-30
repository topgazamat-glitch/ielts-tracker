"""Photos sent from the student's page reach the task they were sent for -
a handout's paper copy and a linked workbook unit included - and a piece
that arrived without its task can be put with it from the Grade screen.

The paper route's first version dropped the student's choice whenever the
task had a digital version, filing the photos as unassigned; the tests of it
put submissions straight into the database and never went through the page.
This one does.

Run me with:  python3 run_tests.py upload_route
"""
import http.cookiejar
import os
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request
import uuid
from datetime import timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["DATA_DIR"] = tempfile.mkdtemp(); os.environ.pop("TELEGRAM_TOKEN", None)
os.environ["TEACHER_PASSWORD"] = "pw"
import core, server, png

db = core.init_db()
now = core.now()
fails, checks = [], 0


def check(what, cond):
    global checks
    checks += 1
    print(("  ok  " if cond else "  FAIL") + "  " + what)
    if not cond:
        fails.append(what)


lvl = db.execute("SELECT id FROM levels WHERE name='Pre-Intermediate'").fetchone()["id"]
g = db.execute("INSERT INTO groups (name, join_code, created_at, level_id) VALUES ('214','A',?,?)",
               (core.iso(now), lvl)).lastrowid
sid = core.add_student(db, "Aziza", g)
tok = db.execute("SELECT token FROM students WHERE id=?", (sid,)).fetchone()["token"]
layout = ('<div class="booklet"><table class="bk"><tr><td style="background:#%s"><p><span>1</span></p></td>'
          '<td><p><span>Part · one</span></p></td></tr></table><p><span>1  </span>'
          '<input class="bk-blank" data-q="1"></p></div>' % core.BOOKLET_TEAL)
h1 = core.load_test(db, {"level": "Pre-Intermediate", "number": 1, "title": "Unit 1A & 1C — One",
                         "kind": "handout", "layout": layout, "passages": {},
                         "questions": [{"num": 1, "kind": "typed", "prompt": "1.1  1", "answer": "went"}]})
wbu = core.load_test(db, {"level": "Pre-Intermediate", "number": 1, "title": "Workbook · Unit 1A & 1C — One",
                          "kind": "handout", "series": "workbook", "layout": layout, "passages": {},
                          "questions": [{"num": 1, "kind": "typed", "prompt": "1.1  1", "answer": "went"}]})
db.execute("UPDATE dtests SET published=1 WHERE id=?", (h1,))
db.commit()

srv = server.Server(("127.0.0.1", 8898), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.4)
base = "http://127.0.0.1:8898"
student = urllib.request.build_opener()
jar = http.cookiejar.CookieJar()
teacher = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
teacher.open(base + "/login", urllib.parse.urlencode({"password": "pw"}).encode()).read()

due = core.local_day(now + timedelta(days=2), core.load_config())
teacher.open(base + "/assignments/list", urllib.parse.urlencode(
    [("group_id", g), ("due", due), ("due_time", "20:00"), ("publish", "1"), ("handout", str(h1)),
     ("items", "Workbook unit 1 A&C\nDestination B1, Unit 7")]).encode(), timeout=30).read()
set_now = {r["title"]: r for r in db.execute("SELECT * FROM assignments WHERE group_id=?", (g,))}
a_hand, a_wb, a_dest = (set_now["Unit 1A & 1C — One"]["id"], set_now["Workbook unit 1 A&C"]["id"],
                        set_now["Destination B1, Unit 7"]["id"])
check("three pieces: the handout, the linked workbook unit and a Destination line",
      set_now["Unit 1A & 1C — One"]["test_id"] == h1 and set_now["Workbook unit 1 A&C"]["test_id"] == wbu
      and set_now["Destination B1, Unit 7"]["test_id"] is None)

page = png.Canvas(1600, 1200, (250, 250, 246)).to_png()


def upload(aid):
    b = "----b" + uuid.uuid4().hex
    body = b"".join([
        ('--%s\r\nContent-Disposition: form-data; name="assignment_id"\r\n\r\n%d\r\n' % (b, aid)).encode(),
        ('--%s\r\nContent-Disposition: form-data; name="photos"; filename="p.png"\r\n'
         'Content-Type: image/png\r\n\r\n' % b).encode(), page, ("\r\n--%s--\r\n" % b).encode()])
    req = urllib.request.Request(base + "/s/%s/upload" % tok, data=body, method="POST")
    req.add_header("Content-Type", "multipart/form-data; boundary=" + b)
    return student.open(req, timeout=30).geturl()


def finish():
    d = db.execute("SELECT id FROM submissions WHERE student_id=? AND draft=1 ORDER BY id DESC LIMIT 1",
                   (sid,)).fetchone()
    student.open(base + "/s/%s/finish/%d" % (tok, d["id"]), b"", timeout=30).read()
    return d["id"]


print("1. PHOTOS REACH THE TASK THEY WERE SENT FOR")
for aid, what in ((a_hand, "the handout's paper copy"), (a_wb, "the workbook, linked to its digital unit"),
                  (a_dest, "a plain line")):
    where = upload(aid)
    sub = finish()
    got = db.execute("SELECT assignment_id FROM submissions WHERE id=?", (sub,)).fetchone()[0]
    check("%s: filed under it, not unassigned" % what, got == aid and "e=" not in where)
items = core.homework_items(db, g, set_now["Workbook unit 1 A&C"]["due_at"])
check("and all three are ticked on the student's list",
      len(core.set_progress(db, sid, items)["done_ids"]) == 3)

print("\n2. A PAPER COPY TURNED DOWN CAN BE SENT AGAIN")
hand_sub = db.execute("SELECT id FROM submissions WHERE assignment_id=?", (a_hand,)).fetchone()[0]
teacher.open(base + "/grade", urllib.parse.urlencode({"submission_id": hand_sub, "tick": "not"}).encode(),
             timeout=30).read()
where = upload(a_hand)
check("sending the handout again is not refused", "e=locked" not in where)
where = upload(a_wb)
finish() if "e=locked" not in where else None
check("but a piece already sent and not turned down still is",
      "e=locked" in upload(a_dest))

print("\n3. A PIECE THAT CAME WITHOUT ITS TASK")
lost = db.execute("INSERT INTO submissions (student_id, assignment_id, created_at, status, draft, kind)"
                  " VALUES (?,NULL,?,'pending',0,'photo')", (sid, core.iso(now))).lastrowid
db.execute("INSERT INTO files (submission_id, filename, ord) VALUES (?,?,0)", (lost, "x.png"))
db.commit()
gp = teacher.open(base + "/queue?id=%d" % lost, timeout=30).read().decode()
check("the Grade screen asks which homework it is", "Which homework is this?" in gp
      and 'value="%d"' % a_hand in gp)
where = teacher.open(base + "/grade/attach", urllib.parse.urlencode(
    {"submission_id": lost, "assignment_id": a_hand}).encode(), timeout=30).geturl()
check("put with the handout, it is that task's now",
      db.execute("SELECT assignment_id FROM submissions WHERE id=?", (lost,)).fetchone()[0] == a_hand)
gp = teacher.open(base + where[len(base):], timeout=30).read().decode()
check("and is ticked, like any paper copy of a handout", 'name="tick" value="done"' in gp)
srv.shutdown()

print()
print("upload_route: %d checks, %d failed" % (checks, len(fails)))
sys.exit(1 if fails else 0)
