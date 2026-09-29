"""A handout set as homework, done on the site or on paper: photographs of the
paper copy are ticked by the teacher - done is worth 5 out of 10, not complete
is a nought - and the better of the two routes is what counts.

Run me with:  python3 run_tests.py paper
"""
import html as _html
import http.cookiejar
import os
import re
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
import core, server, bot, parents

db = core.init_db()
cfg = core.load_config()
now = core.now()
lvl = db.execute("SELECT id FROM levels WHERE name='Pre-Intermediate'").fetchone()["id"]
g = db.execute("INSERT INTO groups (name, join_code, created_at, level_id) VALUES ('214','A',?,?)",
               (core.iso(now - timedelta(days=30)), lvl)).lastrowid
ann, bek, cam, dil, eve = (core.add_student(db, n, g) for n in ("Ann", "Bek", "Cam", "Dil", "Eve"))
db.execute("UPDATE students SET lang='uz' WHERE id=?", (dil,))
tok = {s: db.execute("SELECT token FROM students WHERE id=?", (s,)).fetchone()["token"]
       for s in (ann, bek, cam, dil, eve)}
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
          + bar(2, "Grammar · past")
          + ex("2.1", "Past of go") + '<p data-item="2.1:1"><span>1  </span><span>'
          '<input class="bk-blank" data-q="2" style="width:60px"></span></p>'
          + "</div>")


def handout(number, title):
    tid = core.load_test(db, {
        "level": "Pre-Intermediate", "number": number, "title": title, "kind": "handout",
        "layout": layout, "passages": {}, "questions": [
            {"num": 1, "kind": "typed", "prompt": "1.1  1", "answer": "went"},
            {"num": 2, "kind": "typed", "prompt": "2.1  1", "answer": "went"}]})
    for n in (1, 2):
        db.execute("UPDATE dquestions SET answer='went' WHERE test_id=? AND num=?", (tid, n))
    db.execute("UPDATE dtests SET published=1 WHERE id=?", (tid,))
    db.commit()
    return tid


h1 = handout(1, "Unit 1A & 1C — Communication")
h2 = handout(2, "Unit 2A & 2C — Travel")
a1 = db.execute("INSERT INTO assignments (group_id, title, created_at, published, due_at, test_id)"
                " VALUES (?,?,?,1,?,?)", (g, "Unit 1A & 1C — Communication", core.iso(now - timedelta(days=2)),
                                          core.iso(now + timedelta(days=2)), h1)).lastrowid
wb = db.execute("INSERT INTO assignments (group_id, title, created_at, published, due_at)"
                " VALUES (?,?,?,1,?)", (g, "Workbook unit 1 A&C", core.iso(now - timedelta(days=2)),
                                        core.iso(now + timedelta(days=2)))).lastrowid
db.commit()
A1 = db.execute("SELECT * FROM assignments WHERE id=?", (a1,)).fetchone()
fails, checks = [], 0


def check(what, cond):
    global checks
    checks += 1
    print(("  ok  " if cond else "  FAIL") + "  " + what)
    if not cond:
        fails.append(what)


srv = server.Server(("127.0.0.1", 8895), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.4)
base = "http://127.0.0.1:8895"
op = urllib.request.build_opener()
jar = http.cookiejar.CookieJar()
teacher = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
teacher.open(base + "/login", urllib.parse.urlencode({"password": "pw"}).encode()).read()


def get(path, who=op):
    return _html.unescape(who.open(base + path, timeout=30).read().decode())


def post(path, fields, who=op):
    import json
    r = who.open(base + path, urllib.parse.urlencode(fields).encode(), timeout=30)
    body = r.read().decode()
    try:
        return json.loads(body)
    except ValueError:
        return r.geturl()


def send_paper(sid, aid, when=None):
    """Photographs of the paper copy, as the upload leaves them."""
    sub = db.execute("INSERT INTO submissions (student_id, assignment_id, created_at, status, draft, kind)"
                     " VALUES (?,?,?,'pending',0,'photo')",
                     (sid, aid, core.iso(when or core.now()))).lastrowid
    db.execute("INSERT INTO files (submission_id, filename, ord) VALUES (?,?,0)", (sub, "p%d.jpg" % sub))
    db.commit()
    return sub


def do_digital(sid, parts=(1, 2), answer="went"):
    q = {r["num"]: r["id"] for r in db.execute("SELECT id, num FROM dquestions WHERE test_id=?", (h1,))}
    for p in parts:
        out = post("/s/%s/handout/%d/check" % (tok[sid], h1), {"part": str(p), "q%d" % q[p]: answer})
        assert out.get("ok"), out


print("1. THE STUDENT CAN SEND THE PAPER COPY")
home = get("/s/%s?tab=home" % tok[ann])
check("the Send screen offers the handout, on paper, worth 5", "Communication — on paper (5/10)" in home)
check("and the workbook as before", "Workbook unit 1 A&C" in home)
check("the bot offers it too", a1 in [a["id"] for a in bot.open_assignments(db, g)])
page = get("/s/%s?tab=handouts&h=%d" % (tok[ann], h1))
check("the handout itself says it can be sent on paper instead",
      "Send photos of the pages" in page and "tab=home&a=%d" % a1 in page)
check("which opens the Send screen with it chosen", re.search(
    r'<option value="%d" selected>' % a1, get("/s/%s?tab=home&a=%d" % (tok[ann], a1))) is not None)
check("before anything, the next booklet is shut", core.handout_blocked_by(db, h2, core.student_by_token(db, tok[ann])))

print("\n2. SENT ON PAPER, WAITING FOR THE TICK")
s_ann = send_paper(ann, a1)
st_ann = core.student_by_token(db, tok[ann])
check("the next booklet opens once the paper copy is sent", core.handout_blocked_by(db, h2, st_ann) is None)
hw = core.handout_homework(db, A1, ann)
check("it is handed in, waiting", hw["handed"] and hw["paper"]["state"] == "waiting" and hw["mark"] is None)
check("the homework list ticks it", a1 in core.set_progress(db, ann, [A1])["done_ids"])
check("and says it went on paper", "on paper · sent" in get("/s/%s?tab=home" % tok[ann]))

print("\n3. THE TEACHER TICKS IT")
gp = get("/queue?id=%d" % s_ann, teacher)
check("the Grade screen shows done and not complete, not the 1-10 keypad",
      'name="tick" value="done"' in gp and 'name="tick" value="not"' in gp and "Done · 5/10" in gp
      and "Mark it properly instead" in gp)
wsub = send_paper(bek, wb)
gp2 = get("/queue?id=%d" % wsub, teacher)
check("ordinary homework is marked as before", 'name="tick"' not in gp2 and "scorepad" in gp2 or 'id="f_score"' in gp2)
post("/grade", {"submission_id": s_ann, "tick": "done"}, teacher)
check("done is 5 out of 10", db.execute("SELECT status, score FROM submissions WHERE id=?",
                                         (s_ann,)).fetchone()["score"] == 5)
hw = core.handout_homework(db, A1, ann)
check("it counts: 5, on paper", hw["mark"] == 5 and hw["route"] == "paper")
check("the student sees the tick", "on paper ✓ 5/10" in get("/s/%s?tab=home" % tok[ann])
      and "Your paper copy was ticked: 5 out of 10" in get("/s/%s?tab=handouts&h=%d" % (tok[ann], h1)))

print("\n4. NOT COMPLETE")
s_dil = send_paper(dil, a1)
st_dil = core.student_by_token(db, tok[dil])
check("sent: the next booklet opens", core.handout_blocked_by(db, h2, st_dil) is None)
post("/grade", {"submission_id": s_dil, "tick": "not"}, teacher)
row = db.execute("SELECT score, note FROM submissions WHERE id=?", (s_dil,)).fetchone()
check("not complete is a nought, with a word in the student's language",
      row["score"] == 0 and row["note"].startswith("Toʻliq emas"))
check("and shuts the next booklet again", core.handout_blocked_by(db, h2, st_dil) is not None)
check("the homework list no longer ticks it", a1 not in core.set_progress(db, dil, [A1])["done_ids"])
check("the handout tells them what to do", "not complete. Do it here" in
      get("/s/%s?tab=handouts&h=%d" % (tok[dil], h1)))

print("\n5. THE BETTER OF THE TWO COUNTS")
do_digital(bek)                                  # all right, on the site
s_cam = send_paper(cam, a1)
post("/grade", {"submission_id": s_cam, "tick": "done"}, teacher)
do_digital(cam, parts=(1,), answer="goed")       # half done, and wrong
check("on the site only: the site's mark", core.handout_homework(db, A1, bek)["route"] == "digital"
      and core.handout_homework(db, A1, bek)["mark"] > 5)
cam_hw = core.handout_homework(db, A1, cam)
check("both: the better one - the paper tick beats a poor start online",
      cam_hw["mark"] == 5 and cam_hw["route"] == "paper")

# Eve's photographs come after the deadline
s_eve = send_paper(eve, a1, when=now + timedelta(days=3))
post("/grade", {"submission_id": s_eve, "tick": "done"}, teacher)
# the deadline passes
db.execute("UPDATE assignments SET due_at=? WHERE id=?", (core.iso(core.now() + timedelta(seconds=1)), a1))
db.execute("UPDATE submissions SET created_at=? WHERE id=?", (core.iso(now + timedelta(days=3)), s_eve))
db.commit()
time.sleep(1.2)


def league(sid):
    st = db.execute("SELECT * FROM students WHERE id=?", (sid,)).fetchone()
    scores, late, missing, waiting, _p, _b = core.homework_marks(
        db, st, core.iso(now - timedelta(days=10)), core.iso(core.now()), [])
    return scores, late, missing


A1 = db.execute("SELECT * FROM assignments WHERE id=?", (a1,)).fetchone()
check("the league: Ann's paper tick is 5", 5.0 in league(ann)[0])
check("Bek's work on the site counts in full", max(league(bek)[0]) > 5)
check("Dil's not-complete paper is a missing piece", league(dil)[2] >= 1)
check("Eve's late paper is a late nought", league(eve)[1] == 1)

print("\n6. THE TEACHER'S TABLE AND THE PARENTS' REPORT")
hp = get("/homework/set?" + urllib.parse.urlencode({"group": g, "due": A1["due_at"]}), teacher)
check("the homework table shows who did it on paper, and how it went",
      "📄 5" in hp and "📄 ✗" in hp and "done on paper, ticked" in hp)
items = parents.homework_items(db, core.student_by_token(db, tok[ann]) or
                               db.execute("SELECT * FROM students WHERE id=?", (ann,)).fetchone(),
                               core.iso(now - timedelta(days=10)), core.iso(core.now()))
h_item = next(i for i in items if i["title"].startswith("Unit 1A"))
check("the parents' report has the mark, and that it was on paper",
      h_item["mark"] == 5 and h_item.get("paper") is True)

print("\n7. THE UNIT'S HOMEWORK, IN ONE GO")
import json
plan = json.loads(teacher.open(base + "/assignments/unit.json?" + urllib.parse.urlencode(
    {"group_id": g, "unit": 4, "pair": "A&C", "kind": "none",
     "destination": "Destination B1, Unit 7 (Grammar)"}), timeout=30).read())
titles = [i["title"] for i in plan["items"]]
check("workbook first, then the Destination unit typed for it",
      titles[:2] == ["Workbook unit 4 A&C", "Destination B1, Unit 7 (Grammar)"])
check("no writing when none is wanted", not any(t.startswith("Writing") for t in titles))
peek = json.loads(teacher.open(base + "/assignments/unit.json?" + urllib.parse.urlencode(
    {"group_id": g, "unit": 4, "peek": 1}), timeout=30).read())
check("the Destination unit is remembered for that unit", peek["destination"] == "Destination B1, Unit 7 (Grammar)")
plan = json.loads(teacher.open(base + "/assignments/unit.json?" + urllib.parse.urlencode(
    {"group_id": g, "unit": 4, "pair": "ASRP", "kind": "none"}), timeout=30).read())
check("and comes back by itself next time; Academic Skills comes with the review",
      plan["items"][0]["title"] == "Workbook unit 4 — Academic Skills, Reading Plus and Review"
      and plan["items"][1]["title"] == "Destination B1, Unit 7 (Grammar)")
page = re.sub(r"\s+", " ", get("/assignments", teacher))
check("one form: the unit, the lessons and the Destination box are in it",
      page.count('action="/assignments/list"') == 1 and 'name="destination" id="u_dest"' in page
      and 'name="unit" id="u_unit"' in page and "unitbuild" not in page)
check("and it says the handout can come on paper",
      "send photos of the paper for your tick, 5 out of 10" in page)
due = core.local_day(core.now() + timedelta(days=3), cfg)
teacher.open(base + "/assignments/list", urllib.parse.urlencode({
    "group_id": g, "due": due, "due_time": "20:00", "publish": "1", "unit": "5",
    "destination": "Destination B1, Unit 9", "handout": str(h2),
    "items": "Workbook unit 5 A&C\nDestination B1, Unit 9",
    "prompt": "Write about your town.", "min_words": "120"}).encode(), timeout=30).read()
set_now = db.execute("SELECT title, prompt, test_id FROM assignments WHERE group_id=? AND due_at LIKE ?"
                     " ORDER BY id", (g, due + "%")).fetchall()
check("setting it makes each line a piece, the handout included",
      [r["title"] for r in set_now][:2] == ["Workbook unit 5 A&C", "Destination B1, Unit 9"]
      and any(r["test_id"] == h2 for r in set_now))
check("a question gets a writing line of its own, not the workbook's",
      set_now[0]["prompt"] is None and any(r["title"] == "Writing" and r["prompt"] for r in set_now))
check("and the Destination unit typed is remembered for that unit",
      core.destination_for(db, lvl, 5) == "Destination B1, Unit 9")
srv.shutdown()

print()
print("paper_route: %d checks, %d failed" % (checks, len(fails)))
sys.exit(1 if fails else 0)
