"""Feedback the student cannot miss — see the assertions for what it guarantees.

Run me with:  python3 run_tests.py              (all of them)
              python3 tests/feedback_test.py   (just this one)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import tempfile, shutil, threading, time, re, http.cookiejar, uuid
import urllib.request, urllib.parse
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None); os.environ["TEACHER_PASSWORD"] = "testpw123"

import core, server, bot
core.init_db(); db = core.connect()
now = core.iso(core.now())
g = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('214','AA',?)",
               (now,)).lastrowid
sid = db.execute("INSERT INTO students (name, group_id, active, token, created_at)"
                 " VALUES ('Shirin',?,1,'tok0000000000000001',?)", (g, now)).lastrowid
a = db.execute("INSERT INTO assignments (group_id, title, created_at, published, due_at)"
               " VALUES (?,?,?,1,?)", (g, "Essay: my city", now, now)).lastrowid
sub = db.execute("INSERT INTO submissions (student_id, assignment_id, created_at, status, kind)"
                 " VALUES (?,?,?,'pending','photo')", (sid, a, now)).lastrowid
db.execute("INSERT OR IGNORE INTO tags (label, sort) VALUES ('Watch articles', 1)")
tag = db.execute("SELECT id FROM tags WHERE label='Watch articles'").fetchone()["id"]
db.commit(); db.close()

srv = server.Server(("127.0.0.1", 8839), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start(); time.sleep(0.4)
B = "http://127.0.0.1:8839"
S = B + "/s/tok0000000000000001"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(B + "/login", urllib.parse.urlencode({"password": "testpw123"}).encode()).read()
def student(tab):
    return urllib.request.urlopen(S + "?tab=" + tab, timeout=30).read().decode("utf-8")

print("1. NOTHING MARKED YET")
pg = student("feedback")
print("   the Feedback tab sits under Homework:", ">Feedback<" in pg and "Nothing marked yet" in pg)
assert ">Feedback<" in pg and "Nothing marked yet" in pg
print("   no badge anywhere:", 'class="badge"' not in pg)
assert 'class="badge"' not in pg

print("\n2. THE TEACHER RECORDS A VOICE NOTE, THEN MARKS")
q = op.open(B + "/queue?all=1").read().decode("utf-8")
print("   the marking panel has a recorder:", 'id="rec"' in q and 'id="voice"' in q)
assert 'id="rec"' in q and 'id="voice"' in q
boundary = "----t" + uuid.uuid4().hex
blob = b"\x1aE\xdf\xa3fake-webm-bytes" * 120
body = b"".join([
    ("--%s\r\nContent-Disposition: form-data; name=\"submission_id\"\r\n\r\n%d\r\n" % (boundary, sub)).encode(),
    ("--%s\r\nContent-Disposition: form-data; name=\"kind\"\r\n\r\naudio/webm;codecs=opus\r\n" % boundary).encode(),
    ("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"voice.webm\"\r\n"
     "Content-Type: audio/webm\r\n\r\n" % boundary).encode(), blob,
    ("\r\n--%s--\r\n" % boundary).encode()])
req = urllib.request.Request(B + "/grade/voice", data=body, method="POST")
req.add_header("Content-Type", "multipart/form-data; boundary=" + boundary)
import json
out = json.loads(op.open(req, timeout=30).read().decode("utf-8"))
print("   recording accepted:", out.get("ok"), out.get("name"))
assert out.get("ok") and out["name"].startswith("voice_%d_" % sub) and out["name"].endswith(".webm")
db = core.connect()
print("   kept beside the piece:", db.execute("SELECT voice FROM submissions WHERE id=?", (sub,)).fetchone()["voice"] == out["name"])
db.close()
r = op.open(B + out["url"], timeout=30)
print("   served to the teacher as audio/webm:", r.headers.get("Content-Type") == "audio/webm", "| bytes match:", r.read() == blob)
assert r.headers.get("Content-Type") == "audio/webm"
r = urllib.request.urlopen(S + "/voice/%d" % sub, timeout=30)
print("   and to the student from their own link:", r.headers.get("Content-Type") == "audio/webm" and r.read() == blob)
assert r.headers.get("Content-Type") == "audio/webm"
try:
    urllib.request.urlopen(B + "/s/tok0000000000000009/voice/%d" % sub, timeout=30); other = False
except urllib.error.HTTPError as e:
    other = e.code == 404
print("   but not to a different student:", other)
assert other

op.open(B + "/grade", urllib.parse.urlencode({"submission_id": sub, "score": "7.5",
        "note": "Good ideas. Watch a / the before nouns.", "tag": tag, "all": "1"}).encode()).read()

print("\n3. THE STUDENT CANNOT MISS IT")
pg = student("home")
print("   a badge on the Homework section:", pg.count('class="badge">1</i>') >= 1)
assert 'class="badge">1</i>' in pg
print("   a nudge at the top of the home tab:", "New feedback from your teacher" in pg)
assert "New feedback from your teacher" in pg
pg = student("feedback")
print("   the mark, the note, the tag and the recording, marked new:",
      "7.5/10" in pg and "Watch a / the before nouns." in pg and "Watch articles" in pg
      and "<audio" in pg and 'class="card fb new"' in pg)
assert "7.5/10" in pg and "Watch a / the before nouns." in pg and "Watch articles" in pg
assert "<audio" in pg and 'class="card fb new"' in pg
print("   the recording plays from the page:", "/voice/%d" % sub in pg)
assert "/voice/%d" % sub in pg
pg = student("home")
print("   opening it cleared the badge:", 'class="badge"' not in pg and "New feedback" not in pg)
assert 'class="badge"' not in pg
print("   and the card is no longer new:", 'class="card fb"' in student("feedback"))
assert 'class="card fb"' in student("feedback")

print("\n4. THE BOT SAYS WHERE TO LOOK")
lines = bot.score_lines("en", "Essay: my city", 7.5, ["Watch articles"],
                        "Good ideas.", url="https://x.example/s/tok?tab=feedback", voice=True)
print("   text:", " | ".join(lines))
assert any("tab=feedback" in l for l in lines) and any("voice note" in l for l in lines)
assert lines[0].endswith("7.5/10")
for lang in ("ru", "uz"):
    ls = bot.score_lines(lang, "x", 8, [], None, url="u", voice=True)
    print("   %s has both lines: %s" % (lang, len(ls) == 3))
    assert len(ls) == 3

print("\n5. A RECORDING CAN BE TAKEN BACK")
op.open(B + "/grade/voice/delete", urllib.parse.urlencode({"submission_id": sub}).encode()).read()
db = core.connect()
gone = db.execute("SELECT voice FROM submissions WHERE id=?", (sub,)).fetchone()["voice"] is None
db.close()
print("   cleared:", gone, "| file removed:", not os.path.exists(os.path.join(core.UPLOAD_DIR, out["name"])))
assert gone and not os.path.exists(os.path.join(core.UPLOAD_DIR, out["name"]))

srv.shutdown(); shutil.rmtree(tmp)
print("\nWhat the teacher said is now the first thing the student sees.")
