"""The Homework page is a list you manage — see the assertions for what it guarantees.

Run me with:  python3 run_tests.py            (all of them)
              python3 tests/hwlist_test.py   (just this one)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import tempfile, shutil, threading, time, re, http.cookiejar
import urllib.request, urllib.parse
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None); os.environ["TEACHER_PASSWORD"] = "testpw123"

import core, server
core.init_db(); db = core.connect()
now = core.iso(core.now())
g1 = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('114','AA',?)",
                (now,)).lastrowid
g2 = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('216','BB',?)",
                (now,)).lastrowid
kids = {}
for i, (name, gid) in enumerate([("Diyora", g1), ("Farrukh", g1), ("Malika", g1),
                                 ("Shirin", g2)]):
    kids[name] = db.execute(
        "INSERT INTO students (name, group_id, active, token, created_at)"
        " VALUES (?,?,1,?,?)", (name, gid, "tok%016d" % i, now)).lastrowid
db.commit(); db.close()

srv = server.Server(("127.0.0.1", 8831), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start(); time.sleep(0.4)
B = "http://127.0.0.1:8831"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(B + "/login", urllib.parse.urlencode({"password": "testpw123"}).encode()).read()
def get(u): return op.open(B + u).read().decode("utf-8")
def post(u, d):
    r = op.open(B + u, urllib.parse.urlencode(d, doseq=True).encode())
    return r.geturl()[len(B):], r.read().decode("utf-8")

print("1. TWO CLASSES, TWO PIECES OF HOMEWORK, ONE LIST")
post("/assignments/list", {"group_id": g1, "items": "Workbook 8B\nHandout 8.2\nEssay",
                           "task_type": "other", "due": "2030-10-01", "due_time": "18:00",
                           "publish": "1"})
post("/assignments/list", {"group_id": g2, "items": "Unit 3 words",
                           "task_type": "other", "due": "2030-10-02", "due_time": "18:00",
                           "publish": "1"})
db = core.connect()
due1 = db.execute("SELECT due_at FROM assignments WHERE group_id=?", (g1,)).fetchone()["due_at"]
items = db.execute("SELECT id, title FROM assignments WHERE group_id=? ORDER BY id",
                   (g1,)).fetchall()
# Diyora sent everything, Farrukh one thing, Malika nothing
for a in items:
    db.execute("INSERT INTO submissions (student_id, assignment_id, created_at, status)"
               " VALUES (?,?,?,'pending')", (kids["Diyora"], a["id"], now))
db.execute("INSERT INTO submissions (student_id, assignment_id, created_at, status)"
           " VALUES (?,?,?,'pending')", (kids["Farrukh"], items[0]["id"], now))
db.commit(); db.close()

pg = get("/homework")
rows = pg.count('class="hw"')
print("   pieces of homework listed:", rows)
assert rows == 2
for word in ("Who's done it", "Change", "Delete"):
    print("   every row has %-14s %s" % (word + ":", pg.count(word) >= 2))
    assert pg.count(word) >= 2
print("   114 reads '1 of 3 done everything':", "<strong>1 of 3</strong> done everything" in pg)
assert "<strong>1 of 3</strong> done everything" in pg
print("   and '1 sent nothing':", "1 sent nothing" in pg)
assert "1 sent nothing" in pg
one = get(f"/homework?group={g2}")
print("   filtered to one class:", one.count('class="hw"') == 1 and "216" in one)
assert one.count('class="hw"') == 1

print("\n2. WHO HAS DONE IT, AT A GLANCE")
url = "/homework/set?" + urllib.parse.urlencode({"group": g1, "due": due1})
pg = get(url)
def block(title):
    m = re.search(r"<h3>%s.*?</ul>" % re.escape(title), pg, re.S)
    return m.group(0) if m else ""
ns, pd, dn = block("Not started"), block("Partly done"), block("Done")
print("   not started: Malika  ", "Malika" in ns and "Diyora" not in ns and "Farrukh" not in ns)
print("   partly done: Farrukh ", "Farrukh" in pd and "Malika" not in pd)
print("   done: Diyora         ", "Diyora" in dn and "Farrukh" not in dn)
assert "Malika" in ns and "Diyora" not in ns and "Farrukh" not in ns
assert "Farrukh" in pd and "Malika" not in pd
assert "Diyora" in dn and "Farrukh" not in dn
print("   Farrukh's missing items named:", "missing Handout 8.2, Essay" in pd)
assert "missing Handout 8.2, Essay" in pd
print("   the counts on the cards:", '<span class="count">1</span>' in ns
      and '<span class="count">1</span>' in pd and '<span class="count">1</span>' in dn)
print("   a Change section with the controls:", 'id="manage"' in pg and "Move the deadline" in pg)
assert 'id="manage"' in pg and "Move the deadline" in pg

print("\n3. CHANGING IT BRINGS YOU BACK")
where, _ = post("/assignments/batch/edit", {"group_id": g1, "due": due1,
                                            "new_due": "2030-10-03", "new_time": "18:00",
                                            "back": url})
db = core.connect()
due2 = db.execute("SELECT due_at FROM assignments WHERE group_id=?", (g1,)).fetchone()["due_at"]
db.close()
print("   deadline moved:", due2 != due1 and due2.startswith("2030-10-03"))
assert due2 != due1 and due2.startswith("2030-10-03")
print("   landed back on the homework's page:", where.startswith("/homework/set?"))
assert where.startswith("/homework/set?")
url = "/homework/set?" + urllib.parse.urlencode({"group": g1, "due": due2})

where, _ = post(f"/assignments/{items[2]['id']}/edit",
                {"title": "Essay - Technology", "due": "2030-10-03", "due_time": "18:00",
                 "back": url})
db = core.connect()
a = db.execute("SELECT title, due_at FROM assignments WHERE id=?", (items[2]["id"],)).fetchone()
db.close()
print("   item renamed:", a["title"] == "Essay - Technology")
assert a["title"] == "Essay - Technology"
print("   its deadline untouched:", a["due_at"] == due2)
assert a["due_at"] == due2
print("   back on the same page:", where == url)
assert where == url

where, _ = post("/assignments/batch/close", {"group_id": g1, "due": due2,
                                             "back": "https://evil.example/x"})
print("   an off-site 'back' is ignored:", where == "/assignments")
assert where == "/assignments"
print("   closed ones leave the open list:", "114" not in get("/homework").split("hwlist")[1])
print("   and appear under Closed:", '<span class="pill mute">closed</span>' in get("/homework?show=closed"))
assert '<span class="pill mute">closed</span>' in get("/homework?show=closed")

print("\n3b. ONE BUTTON CLOSES EVERYTHING PAST ITS DEADLINE")
post("/assignments/batch/open", {"group_id": g1, "due": due2})     # 114 open again, due 2030
post("/assignments/list", {"group_id": g1, "items": "Old essay\nOld grammar",
                           "task_type": "other", "due": "2020-01-10", "due_time": "18:00",
                           "publish": "1"})
post("/assignments/list", {"group_id": g2, "items": "Old words",
                           "task_type": "other", "due": "2020-01-11", "due_time": "18:00",
                           "publish": "1"})
pg = get("/homework")
print("   the button names the pile:", "Close all 2 past their deadline" in pg)
assert "Close all 2 past their deadline" in pg
where, pg = post("/assignments/close-past", {"group_id": g2, "back": "/homework?group=%d" % g2})
db = core.connect()
still = db.execute("SELECT COUNT(*) c FROM assignments WHERE closed=0 AND due_at LIKE '2020%'").fetchone()["c"]
db.close()
print("   one class only, when the list was filtered:", still == 2 and "closed=1" in where)
assert still == 2 and "closed=1" in where
where, pg = post("/assignments/close-past", {"group_id": "", "back": "/homework"})
db = core.connect()
still = db.execute("SELECT COUNT(*) c FROM assignments WHERE closed=0 AND due_at LIKE '2020%'").fetchone()["c"]
future = db.execute("SELECT COUNT(*) c FROM assignments WHERE closed=0 AND due_at LIKE '2030%'").fetchone()["c"]
db.close()
print("   then the whole school:", still == 0, " and 2030's homework stays open:", future == 4)
assert still == 0 and future == 4   # 114's three and 216's one
print("   told how many:", "Closed 2 pieces" in pg)
assert "Closed 2 pieces" in pg

print("\n4. DELETING KEEPS THE STUDENTS' WORK")
where, _ = post("/assignments/batch/delete", {"group_id": g1, "due": due2, "back": "/homework"})
db = core.connect()
left = db.execute("SELECT COUNT(*) c FROM assignments WHERE group_id=? AND due_at=?",
                  (g1, due2)).fetchone()["c"]
kept = db.execute("SELECT COUNT(*) c FROM submissions WHERE student_id=?",
                  (kids["Diyora"],)).fetchone()["c"]
db.close()
print("   homework gone:", left == 0, "  Diyora's 3 pieces kept:", kept == 3)
assert left == 0 and kept == 3
print("   back on the list:", where == "/homework")
assert where == "/homework"
try:
    get(url); gone = False
except urllib.error.HTTPError as e:
    gone = e.code == 404
print("   a deleted set's page is a 404:", gone)
assert gone

print("\n5. SET HOMEWORK IS FOR SETTING; THE LIST LIVES ON HOMEWORK")
pg = get("/assignments")
print("   titled Set homework:", "<h1>Set homework</h1>" in pg)
print("   points at the Homework page:", 'href="/homework"' in pg)
print("   no batch list of its own:", "Homework you have set" not in pg)
assert "<h1>Set homework</h1>" in pg and 'href="/homework"' in pg
assert "Homework you have set" not in pg

srv.shutdown(); shutil.rmtree(tmp)
print("\nOne list, three buttons, and the lesson can start.")
