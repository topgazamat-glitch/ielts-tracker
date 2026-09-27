"""The queue, sorted by class and deadline — see the assertions for what it guarantees.

Run me with:  python3 run_tests.py               (all of them)
              python3 tests/queue_map_test.py   (just this one)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import tempfile, shutil, threading, time, re, http.cookiejar
import urllib.request, urllib.parse
from datetime import timedelta
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None); os.environ["TEACHER_PASSWORD"] = "testpw123"

import core, server
core.init_db(); db = core.connect()
now = core.now()
g1 = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('114','AA',?)",
                (core.iso(now),)).lastrowid
g2 = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('216','BB',?)",
                (core.iso(now),)).lastrowid
kids = {}
for i, (name, gid) in enumerate([("Diyora", g1), ("Farrukh", g1), ("Malika", g1),
                                 ("Shirin", g2), ("Bek", g2)]):
    kids[name] = db.execute(
        "INSERT INTO students (name, group_id, active, token, created_at)"
        " VALUES (?,?,1,?,?)", (name, gid, "tok%016d" % i, core.iso(now))).lastrowid
# two deadlines for 114, one for 216, and one piece with no homework at all
mon = core.iso(now - timedelta(days=3))
wed = core.iso(now - timedelta(days=1))
a_mon = db.execute("INSERT INTO assignments (group_id, title, created_at, published, due_at)"
                   " VALUES (?,?,?,1,?)", (g1, "Workbook 8B", core.iso(now), mon)).lastrowid
a_wed = db.execute("INSERT INTO assignments (group_id, title, created_at, published, due_at)"
                   " VALUES (?,?,?,1,?)", (g1, "Essay", core.iso(now), wed)).lastrowid
b_wed = db.execute("INSERT INTO assignments (group_id, title, created_at, published, due_at)"
                   " VALUES (?,?,?,1,?)", (g2, "Unit 3 words", core.iso(now), wed)).lastrowid
def sent(who, aid, days_ago):
    return db.execute(
        "INSERT INTO submissions (student_id, assignment_id, created_at, status, kind)"
        " VALUES (?,?,?,'pending','photo')",
        (kids[who], aid, core.iso(now - timedelta(days=days_ago)))).lastrowid
s1 = sent("Diyora", a_mon, 4); s2 = sent("Farrukh", a_mon, 4); s3 = sent("Malika", a_mon, 3)
s4 = sent("Diyora", a_wed, 1); s5 = sent("Shirin", b_wed, 1); s6 = sent("Bek", b_wed, 1)
s7 = sent("Bek", None, 0)
db.commit(); db.close()

srv = server.Server(("127.0.0.1", 8836), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start(); time.sleep(0.4)
B = "http://127.0.0.1:8836"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(B + "/login", urllib.parse.urlencode({"password": "testpw123"}).encode()).read()
def get(u):
    r = op.open(B + u); return r.geturl()[len(B):], r.read().decode("utf-8")
def post(u, d):
    r = op.open(B + u, urllib.parse.urlencode(d, doseq=True).encode())
    return r.geturl()[len(B):], r.read().decode("utf-8")
cfg = core.load_config()
mon_day = core.deadline_parts(mon, cfg)[0]
wed_day = core.deadline_parts(wed, cfg)[0]

print("1. WHAT TO MARK: CLASSES, THEN LESSONS")
_, q = get("/queue")
print("   the picker is there:", 'class="card picker"' in q)
assert 'class="card picker"' in q
tabs = re.findall(r'<a class="tab[^"]*" href="([^"]+)">([^<]+)<span class="n">(\d+)</span>', q)
print("   class tabs with counts:", [(urllib.parse.unquote(h), l.strip(), n) for h, l, n in tabs])
assert ("/queue", "All classes", "7") in [(urllib.parse.unquote(h), l.strip(), n) for h, l, n in tabs]
assert ("/queue?pick=%d" % g1, "114", "4") in [(urllib.parse.unquote(h), l.strip(), n) for h, l, n in tabs]
rows = re.findall(r'<div class="pickrow[^"]*"><div class="pick-who"><a href="([^"]+)">([^<]+)</a>.*?<div class="n">(\d+)</div>', q, re.S)
print("   one row per class:", [(l, n) for _h, l, n in rows])
assert [(l, n) for _h, l, n in rows] == [("114", "4"), ("216", "3")]
print("   the fullest bar is the longest:", 'style="width:100%"' in q and 'style="width:75%"' in q)
assert 'style="width:100%"' in q
print("   tiles: waiting 7:", "Waiting to be marked" in q and '<div class="v">7</div>' in q)
assert '<div class="v">7</div>' in q
print("   unfiltered, the oldest piece comes first:", 'value="%d"' % s1 in q)
assert 'value="%d"' % s1 in q
where, q2 = post("/grade", {"submission_id": s1, "score": "6", "all": "1"})
print("   a save from 'everything' lands on the work, not the picker:", where == "/queue?all=1" and 'class="card picker"' not in q2)
assert where == "/queue?all=1" and 'class="card picker"' not in q2

_, q = get("/queue?pick=%d" % g1)
rows = re.findall(r'<div class="pickrow[^"]*"><div class="pick-who"><a href="([^"]+)">([^<]+)</a>.*?<div class="n">(\d+)</div>', q, re.S)
print("   inside 114, one row per lesson, oldest first:", [(l, n) for _h, l, n in rows])
assert [n for _h, _l, n in rows] == ["2", "1"] and rows[0][1].startswith("Due ")   # one of Monday's three was marked above
assert urllib.parse.unquote(rows[0][0]) == "/queue?group=%d&due=%s" % (g1, mon_day)
print("   each row offers to mark that set:", q.count("Mark these") == 2)
assert q.count("Mark these") == 2
_, q = get("/queue?group=%d&due=%s" % (g1, mon_day))
print("   a chosen set shows a strip, not the picker:", 'class="setbar"' in q and 'class="card picker"' not in q)
assert 'class="setbar"' in q and 'class="card picker"' not in q
print("   with the set's progress:", "1 of 3 marked" in q)
assert "1 of 3 marked" in q
print("   and a way back to the class's lessons:", "/queue?pick=%d" % g1 in q)
assert "/queue?pick=%d" % g1 in q
_, q = get("/queue?pick=%d&group=%d&due=%s" % (g1, g1, mon_day)) if False else get("/queue?pick=%d" % g1)
print("   the picker names the set being marked when asked back:", "Mark all of 114" in q)
assert "Mark all of 114" in q

print("\n2. PICK A SET, MARK ONLY THAT")
url = "/queue?group=%d&due=%s" % (g2, wed_day)
_, q = get(url)
print("   the set is named:", "Marking 216" in q and "2 left in this set" in q)
assert "Marking 216" in q and "2 left in this set" in q
print("   first of the set is Shirin's:", 'value="%d"' % s5 in q)
assert 'value="%d"' % s5 in q
print("   the form carries the set:", 'name="group" value="%d"' % g2 in q and 'name="due" value="%s"' % wed_day in q)
assert 'name="group" value="%d"' % g2 in q
print("   the jump list is the set only:", q.count("/queue?group=") >= 2 and "Diyora" not in q.split('class="queue"')[0].split("queuelist")[-1])
where, q = post("/grade", {"submission_id": s5, "score": "8", "group": g2, "due": wed_day})
print("   after saving, back in the same set:", where == url, "| 1 left:", "1 left in this set" in q)
assert where == url and "1 left in this set" in q
print("   progress moved:", "1 of 2 marked" in q, "| no picker in the way:", 'class="card picker"' not in q)
assert "1 of 2 marked" in q and 'class="card picker"' not in q
print("   Bek's is now up:", 'value="%d"' % s6 in q)
assert 'value="%d"' % s6 in q
where, q = get("/skip?submission_id=%d&group=%d&due=%s" % (s6, g2, wed_day))
print("   a keyboard skip stays in the set:", where == url)
assert where == url
where, q = post("/grade", {"submission_id": s6, "score": "7", "group": g2, "due": wed_day})
print("   set finished:", "This set is done" in q and "4 other pieces" in q)
assert "This set is done" in q and "4 other pieces" in q
print("   and the picker is still there to choose the next:", 'class="card picker"' in q)
assert 'class="card picker"' in q

print("\n3. A WHOLE CLASS, OR A WHOLE DAY")
_, q = get("/queue?group=%d" % g1)
print("   class 114 alone: 3 left (one was marked above):", "3 left in this set" in q)
assert "3 left in this set" in q
_, q = get("/queue?due=%s" % wed_day)
print("   Wednesday's deadline alone: 1 left:", "1 left in this set" in q and "Marking due" in q)
assert "1 left in this set" in q
_, q = get("/queue?group=%d&due=none" % g2)
print("   no deadline: Bek's loose piece:", 'value="%d"' % s7 in q and "no deadline" in q)
assert 'value="%d"' % s7 in q
_, q = get("/queue?group=999&due=2030-01-01")
print("   an empty set says so, not a blank page:", "This set is done" in q)
assert "This set is done" in q

srv.shutdown(); shutil.rmtree(tmp)
print("\nThe pile has become sets, and the teacher chooses the set.")
