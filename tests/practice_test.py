"""The student page, gone through by the teacher as a student: a practice
copy of the site, a practice student in it, and buttons that do each task -
with nothing reaching the real site or anybody's Telegram.

Run me with:  python3 run_tests.py practice
"""
import html as _html
import http.cookiejar
import os
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None); os.environ["TEACHER_PASSWORD"] = "pw"
import core, server, bot

core.init_db(); db = core.connect()
now = core.iso(core.now())
lvl = db.execute("SELECT id FROM levels WHERE name='Pre-Intermediate'").fetchone()["id"]
g1 = db.execute("INSERT INTO groups (name, join_code, created_at, level_id) VALUES ('214','A',?,?)",
                (now, lvl)).lastrowid
ann = core.add_student(db, "Anvar", g1)
db.execute("UPDATE students SET telegram_id=555 WHERE id=?", (ann,))
ann_tok = db.execute("SELECT token FROM students WHERE id=?", (ann,)).fetchone()["token"]
core.meta_set(db, "teachers", "[777]")
core.meta_set(db, "teacher_chat_id", "777")
TEAL = core.BOOKLET_TEAL


def bar(n, name):
    return ('<table class="bk"><tr><td style="background:#%s"><p><span>%d</span></p></td>'
            '<td><p><span>%s</span></p></td></tr></table>' % (TEAL, n, name))


def ex(label, text):
    return ('<p><span style="font-weight:700;color:#%s;font-size:12pt">%s  </span>'
            '<span>%s</span></p>' % (TEAL, label, text))


def line(label, n, q):
    return ('<p data-item="%s:%d"><span>%d  </span><span>'
            '<input class="bk-blank" data-q="%d" style="width:60px"></span></p>' % (label, n, n, q))


layout = ('<div class="booklet">' + bar(1, "Reading · a text")
          + ex("1.1", "Which word?") + line("1.1", 1, 1) + line("1.1", 2, 2)
          + ex("1.2", "Which day?") + '<p data-item="1.2:1"><span>1  </span><span>'
            '<input class="bk-blank" data-q="3" style="width:60px"></span></p>'
          + bar(2, "Writing · a note")
          + ex("2.1", "Why?") + line("2.1", 1, 4) + line("2.1", 2, 5)
          + "</div>")
DAY = [{"letter": d, "text": "Day " + d} for d in "123"]


def handout(number, title):
    tid = core.load_test(db, {
        "level": "Pre-Intermediate", "number": number, "title": title, "kind": "handout",
        "layout": layout, "passages": {}, "questions": [
            {"num": 1, "kind": "typed", "prompt": "1.1  1", "answer": "went/had gone"},
            {"num": 2, "kind": "typed", "prompt": "1.1  2", "answer": "saw"},
            {"num": 3, "kind": "typed", "prompt": "1.2  1", "answer": "2", "options": DAY},
            {"num": 4, "kind": "open", "prompt": "2.1  1 Why?", "answer": None, "control": "long"},
            {"num": 5, "kind": "open", "prompt": "2.1  2 Partner", "answer": None, "control": "pair"}]})
    db.execute("UPDATE dtests SET published=1 WHERE id=?", (tid,))
    db.commit()
    return tid


u1 = handout(1, "Unit 1A & 1C — Communication")
u2 = handout(2, "Unit 2A & 2C — Travel and tourism")
# the first one is homework, so the second waits for it
db.execute("INSERT INTO assignments (group_id, title, created_at, published, due_at, test_id)"
           " VALUES (?,?,?,1,?,?)", (g1, "handout", now,
                                     core.iso(core.now() + timedelta(days=3)), u1))
test = core.load_test(db, {"level": "Pre-Intermediate", "number": 1, "title": "Past simple quiz",
                           "passages": {}, "questions": [
                               {"num": 1, "kind": "choice", "prompt": "I ... there.", "answer": "B",
                                "options": [{"letter": "A", "text": "go"}, {"letter": "B", "text": "went"}]},
                               {"num": 2, "kind": "choice", "prompt": "She ... it.", "answer": "A",
                                "options": [{"letter": "A", "text": "saw"}, {"letter": "B", "text": "seen"}]}]})
db.execute("UPDATE dtests SET published=1 WHERE id=?", (test,))
db.commit()

# the bot may try: a token is set, and every door to Telegram is watched
server.CFG["telegram_token"] = "TEST-TOKEN"
knocked = []
_real_urlopen = urllib.request.urlopen


def watched(req, *a, **k):
    url = req.full_url if hasattr(req, "full_url") else str(req)
    if "api.telegram.org" in url:
        knocked.append(url)
        raise AssertionError("Telegram was called: " + url)
    return _real_urlopen(req, *a, **k)


urllib.request.urlopen = watched


def real_counts():
    real = core.connect(real=True)
    try:
        return {t: real.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]
                for t in ("students", "dattempts", "dparts", "dresponses", "submissions")}
    finally:
        real.close()


before = real_counts()

fails, checks = [], 0


def check(what, cond):
    global checks
    checks += 1
    print(("  ok  " if cond else "  FAIL") + "  " + what)
    if not cond:
        fails.append(what)


srv = server.Server(("127.0.0.1", 8893), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.4)
base = "http://127.0.0.1:8893"
stranger = urllib.request.build_opener()
jar = http.cookiejar.CookieJar()
teacher = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
teacher.open(base + "/login", urllib.parse.urlencode({"password": "pw"}).encode()).read()


def get(path, who=teacher):
    return _html.unescape(who.open(base + path, timeout=20).read().decode())


def press(path, fields):
    """Post a form the way the page does, and land where it sends us."""
    r = teacher.open(base + path, urllib.parse.urlencode(fields).encode(), timeout=30)
    return r.geturl(), _html.unescape(r.read().decode())


def copy():
    c = core.connect(real=True)
    c.close()
    import sqlite3
    d = sqlite3.connect(core.PRACTICE_PATH)
    d.row_factory = sqlite3.Row
    return d


print("1. THE TEACHER PICKS A CLASS")
pg = get("/practice")
check("the page lists the class to join", "214" in pg and "Be a new student here" in pg)
check("and is in the teacher's menu", 'href="/practice"' in get("/"))
where, pg = press("/practice/start", {"group_id": g1})
tok = urllib.parse.urlsplit(where).path.split("/")[2]
check("starting lands on the practice student's page", tok.startswith("try-") and "Practice student" in pg)
check("which says it is a copy", "Practice copy" in pg and "nothing here reaches your students" in pg)
check("the real site has no practice student", real_counts() == before)

print("\n2. THE LINK IS NOBODY ELSE'S")
try:
    stranger.open(base + "/s/" + tok, timeout=20).read()
    shown = True
except urllib.error.HTTPError as e:
    shown = e.code != 404
check("opened without the teacher's sign-in it is not a link", not shown)
check("a real student's page still reads the real site, even for the teacher",
      "Anvar" in get("/s/" + ann_tok) and "Practice copy" not in get("/s/" + ann_tok))
check("and a real student's page has no practice strip for anyone",
      "Practice copy" not in get("/s/" + ann_tok, stranger))

print("\n3. THE HANDOUTS, WITHOUT DOING THEM")
pg = get("/s/%s?tab=handouts&h=%d" % (tok, u2))
check("a shut booklet offers to finish the one before it", "Finish Unit 1A & 1C for me" in pg)
where, pg = press("/s/%s/practice/finish" % tok, {"h": u1})
c = copy()
sid = int(core.meta_get(c, "practice_student"))
att = c.execute("SELECT id FROM dattempts WHERE test_id=? AND student_id=?", (u1, sid)).fetchone()
check("finishing checks every part in the copy",
      att and c.execute("SELECT COUNT(*) FROM dparts WHERE attempt_id=?", (att["id"],)).fetchone()[0] == 2)
check("and shows the booklet's results", "part=end" in where)
pg = get("/s/%s?tab=handouts&h=%d" % (tok, u2))
check("the next booklet is open now, with a part to answer", "Answer part 1 for me" in pg)
where, pg = press("/s/%s/practice/fill" % tok, {"h": u2, "part": 1, "how": "right"})
a2 = c.execute("SELECT id FROM dattempts WHERE test_id=? AND student_id=?", (u2, sid)).fetchone()["id"]
p1 = c.execute("SELECT * FROM dparts WHERE attempt_id=? AND part=1", (a2,)).fetchone()
check("answering a part checks it, all right: %s/%s" % (p1 and p1["right_n"], p1 and p1["wrong_n"]),
      p1 and p1["right_n"] == 3 and p1["wrong_n"] == 0)
check("a chip is answered with its letter",
      c.execute("SELECT r.given FROM dresponses r JOIN dquestions q ON q.id=r.question_id"
                " WHERE r.attempt_id=? AND q.num=3", (a2,)).fetchone()["given"] == "2")
check("and the page goes where the check button would have sent it", "part=1" in where)
where, pg = press("/s/%s/practice/fill" % tok, {"h": u2, "part": 2, "how": "mistakes"})
p2 = c.execute("SELECT * FROM dparts WHERE attempt_id=? AND part=2", (a2,)).fetchone()
check("the writing part is checked too, its sentence long enough", p2 is not None)
check("a partner's box is left empty, as it would be at home",
      (c.execute("SELECT r.given FROM dresponses r JOIN dquestions q ON q.id=r.question_id"
                 " WHERE r.attempt_id=? AND q.num=5", (a2,)).fetchone()["given"] or "") == "")
check("nothing has been checked on the real site", real_counts() == before)

print("\n4. A TEST, AND HOMEWORK MARKED")
pg = get("/s/%s?tab=tests&t=%d" % (tok, test))
check("a test offers to be answered", "Answer this test for me" in pg)
press("/s/%s/practice/test" % tok, {"t": test, "how": "right"})
a = c.execute("SELECT * FROM dattempts WHERE test_id=? AND student_id=?", (test, sid)).fetchone()
check("and is handed in, all right", a and a["finished_at"] and a["score"] == 2)
c.execute("INSERT INTO submissions (student_id, created_at, status) VALUES (?,?,'pending')", (sid, now))
c.commit()
pg = get("/s/%s?tab=home" % tok)
check("homework nobody has marked can be marked from the page", "Mark my homework as the teacher" in pg)
where, pg = press("/s/%s/practice/mark" % tok, {})
check("marking it opens the feedback the student sees", "tab=feedback" in where)
check("the copy has the mark", c.execute("SELECT status, score FROM submissions WHERE student_id=?",
                                         (sid,)).fetchone()["score"] == 7)
check("what the bot would have said is on the page", "What Telegram would have sent" in pg
      and "to the practice student" in pg)
check("and Telegram itself was never called", knocked == [])
check("the real site still has not moved", real_counts() == before)

print("\n5. EVERY SCREEN AT ONCE")
pg = get("/practice/screens")
check("one frame for each of the student page's screens",
      pg.count("<iframe") == len(server.PRACTICE_SCREENS) == 13)
r = teacher.open(base + "/s/%s?tab=progress&frame=1" % tok, timeout=20)
framed = _html.unescape(r.read().decode())
check("a framed screen has no practice strip", "Practice copy" not in framed and "Scores" in framed)
check("and may be framed by the site itself", r.headers.get("X-Frame-Options") == "SAMEORIGIN")
r = teacher.open(base + "/s/" + ann_tok, timeout=20)
check("which no real student's page may", r.headers.get("X-Frame-Options") == "DENY")

print("\n6. THROWN AWAY")
c.close()
press("/practice/end", {})
check("the copy is gone", not os.path.exists(core.PRACTICE_PATH))
try:
    get("/s/" + tok)
    gone = False
except urllib.error.HTTPError as e:
    gone = e.code == 404
check("and its link with it", gone)
check("the real site is as it was", real_counts() == before)
srv.shutdown()

print()
print("practice: %d checks, %d failed" % (checks, len(fails)))
sys.exit(1 if fails else 0)
