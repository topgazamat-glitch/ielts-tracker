"""Booklets in the order of the course: a booklet set as homework has to be
finished before anything after it opens.

The ones before the first booklet set to the class stay open as practice,
one never set holds nobody up, and a written answer the teacher later says
does not count does not shut the student out again.

Run me with:  python3 run_tests.py handout_order
"""
import html as _html
import json
import os
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request
from datetime import timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None); os.environ["TEACHER_PASSWORD"] = "pw"
import core, server

core.init_db(); db = core.connect()
now = core.iso(core.now())
lvl = db.execute("SELECT id FROM levels WHERE name='Pre-Intermediate'").fetchone()["id"]
g1 = db.execute("INSERT INTO groups (name, join_code, created_at, level_id) VALUES ('214','A',?,?)",
                (now, lvl)).lastrowid
g2 = db.execute("INSERT INTO groups (name, join_code, created_at, level_id) VALUES ('216','B',?,?)",
                (now, lvl)).lastrowid
ann = core.add_student(db, "Anvar", g1)
bek = core.add_student(db, "Bekzod", g1)
cam = core.add_student(db, "Kamola", g2)
tok = {sid: db.execute("SELECT token FROM students WHERE id=?", (sid,)).fetchone()["token"]
       for sid in (ann, bek, cam)}
TEAL = core.BOOKLET_TEAL


def bar(n, name):
    return ('<table class="bk"><tr><td style="background:#%s"><p><span>%d</span></p></td>'
            '<td><p><span>%s</span></p></td></tr></table>' % (TEAL, n, name))


def ex(label, text):
    return ('<p><span style="font-weight:700;color:#%s;font-size:12pt">%s  </span>'
            '<span>%s</span></p>' % (TEAL, label, text))


layout = ('<div class="booklet">' + bar(1, "Reading · a text")
          + ex("1.1", "Which word?") + '<p data-item="1.1:1"><span>1  </span><span>'
          '<input class="bk-blank" data-q="1" style="width:60px"></span></p>'
          + bar(2, "Writing · a note")
          + ex("2.1", "Why?") + '<p data-item="2.1:1"><span>1  </span><span>'
          '<input class="bk-blank" data-q="2" style="width:60px"></span></p>'
          + "</div>")


def handout(number, title):
    tid = core.load_test(db, {
        "level": "Pre-Intermediate", "number": number, "title": title, "kind": "handout",
        "layout": layout, "passages": {}, "questions": [
            {"num": 1, "kind": "typed", "prompt": "1.1  1", "answer": "went"},
            {"num": 2, "kind": "open", "prompt": "2.1  1 Why?", "answer": None, "control": "long"}]})
    db.execute("UPDATE dtests SET published=1 WHERE id=?", (tid,))
    db.commit()
    return tid


# made out of order, as they were uploaded
u3ac = handout(3, "Unit 3A & 3C — Money")
u2rp = handout(2, "Unit 2 ASRP — Travel")
u2bd = handout(2, "Unit 2B & 2D — Travel and tourism")
u1bd = handout(1, "Unit 1B & 1D — Communication")
u2ac = handout(2, "Unit 2A & 2C — Travel and tourism")
u1ac = handout(1, "Unit 1A & 1C — Communication")
NAME = {u1ac: "1AC", u1bd: "1BD", u2ac: "2AC", u2bd: "2BD", u2rp: "2 ASRP", u3ac: "3AC"}

fails, checks = [], 0


def check(what, cond):
    global checks
    checks += 1
    print(("  ok  " if cond else "  FAIL") + "  " + what)
    if not cond:
        fails.append(what)


srv = server.Server(("127.0.0.1", 8846), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.4)
base = "http://127.0.0.1:8846"
op = urllib.request.build_opener()


def get(path):
    return _html.unescape(op.open(base + path, timeout=20).read().decode())


def post(path, fields):
    return json.loads(op.open(base + path, urllib.parse.urlencode(fields).encode(),
                              timeout=20).read().decode())


def student(sid):
    return db.execute("SELECT * FROM students WHERE id=?", (sid,)).fetchone()


def shut(sid):
    return [NAME[b["id"]] for b, first in core.handout_shelf(db, student(sid)) if first]


def set_homework(tid, days=3):
    db.execute("INSERT INTO assignments (group_id, title, created_at, published, due_at, test_id)"
               " VALUES (?,?,?,1,?,?)", (g1, "handout", now,
                                         core.iso(core.now() + timedelta(days=days)), tid))
    db.commit()


def finish(sid, tid, parts=(1, 2)):
    q = {r["num"]: r["id"] for r in db.execute("SELECT id, num FROM dquestions WHERE test_id=?", (tid,))}
    for p in parts:
        out = post("/s/%s/handout/%d/check" % (tok[sid], tid),
                   {"part": str(p), "q%d" % q[1]: "went", "q%d" % q[2]: "Because it was raining"})
        assert out.get("ok"), out


print("1. THE ORDER OF THE COURSE")
order = [NAME[b["id"]] for b, _f in core.handout_shelf(db, student(ann))]
check("by unit, A & C before B & D, the review after its lessons: %s" % order,
      order == ["1AC", "1BD", "2AC", "2BD", "2 ASRP", "3AC"])
key = lambda title, n: core.lesson_order({"title": title, "number": n, "id": 1})
check("a single lesson and a run of lessons sort by their first letter",
      key("Unit 3A — Food", 3) < key("Unit 3B — Food", 3) < key("Unit 3 ASRP", 3)
      and key("Unit 1ABC — Hello", 1) < key("Unit 1D — Hello", 1)
      and key("Unit 5.1 — Nature", 5) < key("Unit 5.2 — Nature", 5) < key("Unit 5 ASRP", 5))
page = get("/s/%s?tab=handouts" % tok[ann])
check("and the Handouts page lists them so",
      page.index("Unit 1A & 1C") < page.index("Unit 1B & 1D") < page.index("Unit 2A & 2C")
      < page.index("Unit 2B & 2D") < page.index("Unit 2 ASRP") < page.index("Unit 3A & 3C"))

print("\n2. NOTHING SET YET: EVERYTHING IS OPEN")
check("no booklet is shut", shut(ann) == [])

print("\n3. SET 2A & 2C: WHAT COMES AFTER IT WAITS")
set_homework(u2ac)
check("2B & 2D, the review and Unit 3 are shut: %s" % shut(ann), shut(ann) == ["2BD", "2 ASRP", "3AC"])
check("the units before it stay open as practice", "1AC" not in shut(ann) and "1BD" not in shut(ann))
page = get("/s/%s?tab=handouts" % tok[ann])
check("the Handouts page says what opens them", "Opens when you finish Unit 2A & 2C" in page
      and 'href="/s/%s?tab=handouts&h=%d"' % (tok[ann], u3ac) not in page)
page = get("/s/%s?tab=handouts&h=%d" % (tok[ann], u3ac))
check("its address shows a closed door, and the way to the one to do",
      "Unit 3A & 3C — Money is not open yet" in page
      and "tab=handouts&h=%d" % u2ac in page and "Open Unit 2A & 2C" in page
      and "not started it yet" in page and "booksheet" not in page)
q3 = db.execute("SELECT id FROM dquestions WHERE test_id=? AND num=1", (u3ac,)).fetchone()["id"]
out = post("/s/%s/handout/%d/save" % (tok[ann], u3ac), {"q%d" % q3: "went"})
check("nothing can be saved into it", out.get("ok") is False and out.get("locked") is True)
out = post("/s/%s/handout/%d/check" % (tok[ann], u3ac), {"part": "1", "q%d" % q3: "went"})
check("or checked", out.get("ok") is False and out.get("locked") is True
      and not db.execute("SELECT 1 FROM dparts").fetchone())
check("another class is not held up by homework it was not set", shut(cam) == [])

print("\n4. HALF DONE IS NOT DONE")
finish(ann, u2ac, parts=(1,))
check("one part of two checked: still shut", shut(ann) == ["2BD", "2 ASRP", "3AC"])
page = get("/s/%s?tab=handouts&h=%d" % (tok[ann], u3ac))
check("and the closed page says how far they are", "checked 1 of its 2 parts" in page)

print("\n5. THE NEXT SET BOOKLET, ON THE HOMEWORK LIST")
set_homework(u2bd, days=6)
home = get("/s/%s?tab=home" % tok[ann])
check("2B & 2D's homework line sends them to 2A & 2C first",
      "finish Unit 2A & 2C first" in home)

print("\n6. FINISHED: THE NEXT ONE OPENS")
finish(ann, u2ac, parts=(2,))
check("2B & 2D opens; it is homework too, so what is after it waits: %s" % shut(ann),
      shut(ann) == ["2 ASRP", "3AC"])
check("Bekzod, who has done nothing, is still held at 2A & 2C", shut(bek) == ["2BD", "2 ASRP", "3AC"])
page = get("/s/%s?tab=handouts&h=%d" % (tok[ann], u2bd))
check("2B & 2D's pages are there to work on", "booksheet" in page and "not open yet" not in page)
finish(ann, u2bd)
check("with 2B & 2D done, the review nobody set holds nobody up", shut(ann) == [])

print("\n7. AN ANSWER THAT DOES NOT COUNT DOES NOT SHUT THEM OUT")
att = db.execute("SELECT id FROM dattempts WHERE test_id=? AND student_id=?", (u2ac, ann)).fetchone()["id"]
q2 = db.execute("SELECT id FROM dquestions WHERE test_id=? AND num=2", (u2ac,)).fetchone()["id"]
core.void_answer(db, att, q2)
check("the mark knows it does not count", core.handout_status(db, u2ac, ann)["voided"] == 1)
check("but the booklets after it stay open", shut(ann) == [])

print("\n8. AFTER THE DEADLINE, THE NEW EDITION TAKES THE OLD ONE'S PLACE")
old = handout(1, "Unit 1A & 1C — Communication (first edition)")
db.execute("UPDATE dtests SET published=0 WHERE id=?", (old,))
new = handout(1, "Unit 1A & 1C — Communicating")
lone = handout(3, "Unit 3B & 3D — Money (first edition)")
db.execute("UPDATE dtests SET published=0 WHERE id=?", (lone,))
NAME.update({old: "old 1AC", new: "new 1AC", lone: "old 3BD"})
aid = db.execute("INSERT INTO assignments (group_id, title, created_at, published, due_at, test_id)"
                 " VALUES (?,?,?,1,?,?)", (g2, "handout", now, core.iso(core.now() + timedelta(days=2)), old)).lastrowid
db.execute("INSERT INTO assignments (group_id, title, created_at, published, due_at, test_id)"
           " VALUES (?,?,?,1,?,?)", (g2, "handout", now, core.iso(core.now() - timedelta(days=3)), lone))
db.commit()


def names(sid):
    return [NAME[b["id"]] for b, _f in core.handout_shelf(db, student(sid))]


check("before the deadline the class has the old edition: %s" % names(cam), "old 1AC" in names(cam))
check("and it holds the course back, the new edition too", shut(cam)[:2] == ["new 1AC", "1BD"])
db.execute("UPDATE assignments SET due_at=? WHERE id=?", (core.iso(core.now() - timedelta(days=3)), aid))
db.commit()
check("after the deadline the old edition gives way to the new: %s" % names(cam),
      "old 1AC" not in names(cam) and "new 1AC" in names(cam))
check("and holds nothing back", shut(cam) == [])
check("the homework itself still points at the old edition, so its mark stands",
      db.execute("SELECT test_id FROM assignments WHERE id=?", (aid,)).fetchone()["test_id"] == old)
check("an old booklet with no new edition stays where it was", "old 3BD" in names(cam))
check("a published booklet never gives way", "1AC" in names(cam))
check("another class never had the old edition, so it never sees it", "old 1AC" not in names(ann))

srv.shutdown()
print()
print("handout_order: %d checks, %d failed" % (checks, len(fails)))
sys.exit(1 if fails else 0)
