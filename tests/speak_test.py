"""A speaking task in a handout is recorded in the handout itself.

The booklets ask for a one-minute talk "sent to your teacher"; on the site
the task gets a recorder. A part with a recorder cannot be checked until a
recording of at least SPEAK_MIN_SECONDS is kept - or the student says they
cannot record, which the teacher sees. The teacher listens on the Speaking
page and answers with a note or a recording; the student finds it on the
Feedback tab. (His request and choices, 2026-10-03.)

Run me with:  python3 run_tests.py speak
"""
import http.cookiejar
import json
import os
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["DATA_DIR"] = tempfile.mkdtemp(); os.environ.pop("TELEGRAM_TOKEN", None)
os.environ["TEACHER_PASSWORD"] = "pw"
import core, server

db = core.init_db()
now = core.iso(core.now())
fails, checks = [], 0


def check(what, cond):
    global checks
    checks += 1
    print(("  ok  " if cond else "  FAIL") + "  " + what)
    if not cond:
        fails.append(what)


lvl = db.execute("SELECT id FROM levels WHERE name='Pre-Intermediate'").fetchone()["id"]
g = db.execute("INSERT INTO groups (name, join_code, created_at, level_id) VALUES ('214','SPK',?,?)",
               (now, lvl)).lastrowid
ali = core.add_student(db, "Ali", g)
bek = core.add_student(db, "Bekzod", g)
tok = {sid: db.execute("SELECT token FROM students WHERE id=?", (sid,)).fetchone()["token"] for sid in (ali, bek)}
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
          + bar(2, "Speaking and writing · a talk")
          + ex("2.1", "Make notes. Then record yourself: talk for about one minute and send the recording to your teacher.")
          + '<p data-item="2.1:1"><span>1  </span><span><input class="bk-blank" data-q="2" style="width:95%"></span></p>'
          + '<p>…… all the points <input class="bk-blank" data-q="3" style="width:20px"></p>'
          + ex("2.2", "Write a sentence.") + '<p data-item="2.2:1"><span>1  </span><span>'
          '<input class="bk-blank" data-q="4" style="width:95%"></span></p>'
          + "</div>")
tid = core.load_test(db, {
    "level": "Pre-Intermediate", "number": 3, "title": "Unit 3A & 3C — Money", "kind": "handout",
    "layout": layout, "passages": {}, "questions": [
        {"num": 1, "kind": "typed", "prompt": "1.1  1", "answer": "went"},
        {"num": 2, "kind": "open", "prompt": "2.1  1 notes", "answer": None, "control": "long"},
        {"num": 3, "kind": "open", "prompt": "2.1  check", "answer": None, "control": "tick"},
        {"num": 4, "kind": "open", "prompt": "2.2  1", "answer": None, "control": "long"}]})
db.execute("UPDATE dtests SET published=1 WHERE id=?", (tid,))
db.commit()

print("1. THE SPEAKING TASK GETS A RECORDER")
check("one recorder added", core.add_recorders(db, tid) == 1)
check("and never twice", core.add_recorders(db, tid) == 0)
rq = db.execute("SELECT * FROM dquestions WHERE test_id=? AND control='record'", (tid,)).fetchone()
lay = db.execute("SELECT layout FROM dtests WHERE id=?", (tid,)).fetchone()["layout"]
spot = lay.index('data-q="%d"' % rq["num"])
check("at the end of the task, after its checklist, before the next task",
      lay.index('data-q="3"') < spot < lay.index("2.2  </span>"))
check("labelled with its task", rq["prompt"].startswith("2.1"))

srv = server.Server(("127.0.0.1", 8897), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.4)
B = "http://127.0.0.1:8897"
anon = urllib.request.build_opener()


def post(path, fields):
    return json.loads(anon.open(B + path, urllib.parse.urlencode(fields).encode(), timeout=20).read().decode())


def upload(sid, seconds, size=6000):
    b = "----b" + uuid.uuid4().hex
    parts = [("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n" % (b, k, v)).encode()
             for k, v in {"q": rq["id"], "seconds": seconds, "kind": "audio/webm;codecs=opus"}.items()]
    parts.append(("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"speak.webm\"\r\n"
                  "Content-Type: audio/webm\r\n\r\n" % b).encode() + b"\x1aE" + b"x" * size
                 + ("\r\n--%s--\r\n" % b).encode())
    req = urllib.request.Request(B + "/s/%s/handout/%d/speak" % (tok[sid], tid), data=b"".join(parts),
                                 headers={"Content-Type": "multipart/form-data; boundary=" + b, "Origin": B})
    return json.loads(anon.open(req, timeout=20).read().decode())


qid = {r["num"]: r["id"] for r in db.execute("SELECT id, num FROM dquestions WHERE test_id=?", (tid,))}
out = post("/s/%s/handout/%d/check" % (tok[ali], tid), {"part": "1", "q%d" % qid[1]: "went"})
check("part 1 checks as before", out.get("ok"))

print("\n2. NO RECORDING, NO CHECK")
page = anon.open(B + "/s/%s?tab=handouts&h=%d&part=2" % (tok[ali], tid), timeout=20).read().decode()
check("the part shows the recorder, needed like any box", 'class="bk-rec' in page and "data-required" in page
      and "/handout/%d/speak" % tid in page)
out = post("/s/%s/handout/%d/check" % (tok[ali], tid), {"part": "2", "q%d" % qid[2]: "my notes here today"})
check("checking without it is refused, naming the recorder: %s" % out.get("missing"),
      not out.get("ok") and rq["num"] in (out.get("missing") or []))

print("\n3. TOO SHORT IS NOT KEPT")
out = upload(ali, 30)
check("30 seconds is refused: %s" % out, out.get("ok") is False and out.get("why") == "short")
out = upload(ali, 52)
check("52 seconds is kept: %s" % out.get("value"), out.get("ok") and out["value"].startswith("rec:speak_"))
name = out["value"].split(":")[1]
check("the file is on the disk", os.path.isfile(os.path.join(core.UPLOAD_DIR, name)))
out = post("/s/%s/handout/%d/check" % (tok[ali], tid), {"part": "2", "q%d" % qid[2]: "my notes here today",
                                                        "q%d" % qid[4]: "I bought a coat last week"})
check("now the part checks: %s" % out, out.get("ok"))
check("the student hears it back", anon.open(B + "/s/%s/speak/%s" % (tok[ali], name), timeout=20).status == 200)
try:
    anon.open(B + "/s/%s/speak/%s" % (tok[bek], name), timeout=20)
    other = True
except urllib.error.HTTPError:
    other = False
check("another student cannot", not other)

print("\n4. A STUDENT WHO CANNOT RECORD")
post("/s/%s/handout/%d/check" % (tok[bek], tid), {"part": "1", "q%d" % qid[1]: "went"})
out = post("/s/%s/handout/%d/check" % (tok[bek], tid), {"part": "2", "q%d" % qid[2]: "notes of my own",
                                                        "q%d" % qid[4]: "I have never sold anything",
                                                        "q%d" % rq["id"]: "cant"})
check("says so, and the part checks", out.get("ok"))

print("\n5. THE TEACHER LISTENS AND ANSWERS")
jar = http.cookiejar.CookieJar()
teacher = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
teacher.open(B + "/login", urllib.parse.urlencode({"password": "pw"}).encode(), timeout=20).read()
sp = teacher.open(B + "/speaking", timeout=20).read().decode()
check("Ali's recording waits on the Speaking page", "Ali" in sp and name in sp)
cant = teacher.open(B + "/speaking?show=cant", timeout=20).read().decode()
check("Bekzod is listed as unable to record", "Bekzod" in cant and "can&rsquo;t record" in cant)
today = teacher.open(B + "/", timeout=20).read().decode()
check("Today says a recording is waiting", "1 recording to listen to" in today)
aid = db.execute("SELECT id FROM dattempts WHERE test_id=? AND student_id=?", (tid, ali)).fetchone()["id"]
teacher.open(B + "/speaking/note", urllib.parse.urlencode(
    {"attempt": aid, "question": rq["id"], "note": "Good pace - try more past simple."}).encode(), timeout=20).read()
check("the note is kept, and the student has something new", core.unseen_feedback(db, ali) == 1)
fb = anon.open(B + "/s/%s?tab=feedback" % tok[ali], timeout=20).read().decode()
check("the Feedback tab shows it with the recording", "Good pace - try more past simple." in fb and name in fb)
check("and opening it marks it seen", core.unseen_feedback(db, ali) == 0)
sp = teacher.open(B + "/speaking", timeout=20).read().decode()
check("it no longer waits", name not in sp)

print("\n6. A SPOKEN REPLY")
b = "----b" + uuid.uuid4().hex
parts = [("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n" % (b, k, v)).encode()
         for k, v in {"attempt": aid, "question": rq["id"], "kind": "audio/mp4"}.items()]
parts.append(("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"reply.m4a\"\r\n"
              "Content-Type: audio/mp4\r\n\r\n" % b).encode() + b"y" * 4000 + ("\r\n--%s--\r\n" % b).encode())
req = urllib.request.Request(B + "/speaking/voice", data=b"".join(parts),
                             headers={"Content-Type": "multipart/form-data; boundary=" + b, "Origin": B})
out = json.loads(teacher.open(req, timeout=20).read().decode())
check("the teacher's reply is kept: %s" % out, out.get("ok") and out["url"].endswith(".m4a"))
check("the note stays beside it", db.execute("SELECT note FROM speak_feedback WHERE attempt_id=?", (aid,)).fetchone()[0]
      == "Good pace - try more past simple.")
check("the student hears it", anon.open(B + "/s/%s/speakfb/%d/%d" % (tok[ali], aid, rq["id"]), timeout=20).status == 200)
fb = anon.open(B + "/s/%s?tab=handouts&h=%d&part=2" % (tok[ali], tid), timeout=20).read().decode()
check("and finds it next to the recording in the handout", "Your teacher says" in fb
      and "/speakfb/%d/%d" % (aid, rq["id"]) in fb)

srv.shutdown()
print()
print("speak: %d checks, %d failed" % (checks, len(fails)))
sys.exit(1 if fails else 0)
