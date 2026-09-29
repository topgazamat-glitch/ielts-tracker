"""A handout in parts: one at a time, checked once, the next one opened only
after it - and the answers of a rebuilt handout carried over.

Run me with:  python3 run_tests.py handout_parts
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import tempfile
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None); os.environ["TEACHER_PASSWORD"] = "testpw123"

import core, server
core.init_db(); db = core.connect()
now = core.iso(core.now())

lvl = db.execute("SELECT id FROM levels WHERE name='Pre-Intermediate'").fetchone()["id"]
g = db.execute("INSERT INTO groups (name, join_code, created_at, level_id)"
               " VALUES ('214','X',?,?)", (now, lvl)).lastrowid
sid = core.add_student(db, "Iroda", g)
tok = db.execute("SELECT token FROM students WHERE id=?", (sid,)).fetchone()["token"]

TEAL = server.BOOKLET_TEAL


def bar(n, name):
    return ('<table class="bk"><tr><td style="background:#%s"><p><span>%d</span></p></td>'
            '<td><p><span>%s</span></p></td></tr></table>' % (TEAL, n, name))


def ex(label, text):
    return ('<p><span style="font-weight:700;color:#%s;font-size:12pt">%s  </span>'
            '<span>%s</span></p>' % (TEAL, label, text))


def box(n):
    return '<input class="bk-blank" data-q="%d" style="width:60px">' % n


def panel(head_colour, title, body):
    return ('<table class="bk"><tr><td style="background:#F2F8F8;border-left:1px solid #127D80">'
            '<table class="bk"><tr><td style="background:#%s"><p><span style="font-weight:700;'
            'color:#FFFFFF">%s</span></p></td></tr></table>%s</td></tr></table>'
            % (head_colour, title, body))


story = "".join('<p><span style="font-weight:700;color:#1A1A1A">DAY %s.</span><span style="color:#1A1A1A">'
                '  I arrived in the afternoon and did not go to the cathedral. Instead I went to a museum '
                'of clocks, which the book gave four lines and no photograph at all.</span></p>' % d
                for d in ("ONE", "TWO", "THREE"))
layout = (
    '<div class="booklet">'
    '<p><span>UNIT 2</span></p><p><span style="font-size:20pt">Travel</span></p>'
    '<p><span style="font-weight:700">Lessons 2A + 2C · We had an adventure</span></p>'
    '<table class="bk"><tr><td><p><span>You will learn to</span></p>'
    '<p><span>—  </span><span>use the </span><span style="font-weight:700">past simple</span></p></td></tr></table>'
    + bar(1, "Reading · the last page rule")
    + '<p><span style="font-weight:700;color:#1A1A1A">The Last Page Rule</span></p>' + story
    + ex("1.1", "Which day?") + '<p data-item="1.1:1"><span>1  </span><span>Clocks ' + box(1) + '</span></p>'
    + '<p data-item="1.1:2"><span>2  </span><span>Go ' + box(2) + '</span></p>'
    + '<p data-item="1.1:3"><span>3  </span><span>Why? ' + box(3) + '</span></p>'
    + '<p data-item="1.1:4"><span>4  </span><span>Your partner? ' + box(5) + '</span></p>'
    + bar(2, "Grammar · past simple")
    + panel("C0745F", "ERROR WARNING",
            '<p><span style="font-weight:700">1  Double past.</span><span> I didn\'t went. ✗ → '
            'I didn\'t go. ✓</span></p>')
    + '<table class="bk"><tr><td style="background:#E8F1F1"><p>Use</p></td><td style="background:#E8F1F1">'
      '<p>Example</p></td></tr><tr><td><p>positive</p></td><td><p>It was hot.</p></td></tr></table>'
    + ex("2.1", "Past simple.") + '<p data-item="2.1:1"><span>1  </span><span>go ' + box(4) + '</span></p>'
    + '</div>')
DAY = [{"letter": d, "text": "Day " + d} for d in "123"]
hid = core.load_test(db, {
    "level": "Pre-Intermediate", "number": 2, "title": "Unit 2A & 2C — Travel",
    "kind": "handout", "layout": layout, "passages": {},
    "questions": [
        {"num": 1, "kind": "typed", "prompt": "1.1  1 Clocks", "answer": "1", "options": DAY},
        {"num": 2, "kind": "typed", "prompt": "1.1  2 Go", "answer": "went"},
        {"num": 3, "kind": "open", "prompt": "1.1  3 Why?", "answer": None, "control": "long"},
        {"num": 4, "kind": "typed", "prompt": "2.1  1 go", "answer": "went"},
        {"num": 5, "kind": "open", "prompt": "1.1  4 Your partner?", "answer": None, "control": "pair"},
    ]})
db.execute("UPDATE dtests SET published=1 WHERE id=?", (hid,))
db.commit()
qid = {r["num"]: r["id"] for r in db.execute("SELECT id, num FROM dquestions WHERE test_id=?", (hid,))}

fails, checks = [], 0


def check(what, cond):
    global checks
    checks += 1
    print(("  ok  " if cond else "  FAIL") + "  " + what)
    if not cond:
        fails.append(what)


import html as _html
import threading, time, urllib.request, urllib.parse, http.cookiejar
srv = server.Server(("127.0.0.1", 8843), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.4)
base = "http://127.0.0.1:8843"
op = urllib.request.build_opener()


def get(path):
    return _html.unescape(op.open(base + path, timeout=20).read().decode())


def post(path, fields):
    return json.loads(op.open(base + path, urllib.parse.urlencode(fields).encode(),
                              timeout=20).read().decode())


H = "/s/%s?tab=handouts&h=%d" % (tok, hid)
CHECK = "/s/%s/handout/%d/check" % (tok, hid)
SAVE = "/s/%s/handout/%d/save" % (tok, hid)

print("1. ONE PART AT A TIME, AND NO SKIPPING AHEAD")
pg = get(H)
check("the first part is shown", "Part 1 of 2" in pg and 'data-part="1"' in pg)
check("the second part's boxes are not on the page", 'data-q="4"' not in pg)
check("its step is locked", re.search(r'hx-step locked[^"]*" aria-disabled="true"><span class="hx-step-dot">'
                                      r'<svg', pg) is not None)
check("asking for part 2 by address still shows part 1", 'data-part="1"' in get(H + "&part=2"))
check("the cover names the booklet and what it teaches",
      "Travel" in pg and "Lessons 2A + 2C" in pg and "past simple" in pg and "hx-goals" in pg)
out = post(CHECK, {"part": "2", "q%d" % qid[4]: "went"})
check("checking part 2 first is refused", out.get("ok") is False and out.get("locked"))

check("a box done in class says so and is not required",
      re.search(r'name="q%d"[^>]*placeholder="in class"[^>]*data-optional' % qid[5], pg) is not None)

print("\n2. THE PAPER'S EXPLANATIONS IN THE SITE'S CLOTHES")
check("the reading text is an article with its title", '<article class="hx-read">' in pg
      and '<h3 class="hx-read-title">The Last Page Rule</h3>' in pg)
check("with its length for the reader", re.search(r"\d+ words &middot; about \d+ min", pg.replace("·", "&middot;")) is not None
      or re.search(r"\d+ words · about \d+ min", pg) is not None)
check("each paragraph's bold opening is a lead", pg.count('class="hx-lead"') == 3)
check("the booklet's own colours are gone from the article",
      "#1A1A1A" not in pg[pg.index("<article"):pg.index("</article>")])

print("\n3. A PART IS CHECKED ONCE, WHEN IT IS COMPLETE")
out = post(CHECK, {"part": "1", "q%d" % qid[1]: "2"})
check("with boxes empty it is refused, and says which", out.get("ok") is False
      and out.get("missing") == [2, 3])
check("nothing is recorded", not core.handout_parts_done(db, db.execute(
    "SELECT id FROM dattempts WHERE test_id=?", (hid,)).fetchone()["id"]))
post(SAVE, {"q%d" % qid[3]: "Because it was quiet."})
out = post(CHECK, {"part": "1", "q%d" % qid[1]: "2", "q%d" % qid[2]: "go"})
check("complete - saved boxes count - it is checked", out.get("ok") is True
      and out.get("go", "").endswith("&part=1") and out["right"] == 0 and out["wrong"] == 2)
aid = db.execute("SELECT id FROM dattempts WHERE test_id=?", (hid,)).fetchone()["id"]
row = core.handout_parts_done(db, aid)[1]
check("the part's result is kept", (row["right_n"], row["wrong_n"], row["teacher_n"]) == (0, 2, 1))
pg = get(H + "&part=1")
check("the checked part opens on its result", '<section class="hx-result"' in pg
      and "Reading checked" in pg and "0 of 2 right" in pg)
check("the right chip is shown for a wrong choice", "is-key" in pg)
check("the right word is shown beside a wrong gap", '<span class="bk-key">went</span>' in pg)
check("the boxes are locked", 'readonly' in pg and "disabled" in pg and 'id="handoutdata"' not in pg)
check("and the way on is to part 2", "Next: Grammar" in pg)
post(SAVE, {"q%d" % qid[2]: "went"})
check("a late save cannot change a checked part", db.execute(
    "SELECT given FROM dresponses WHERE attempt_id=? AND question_id=?", (aid, qid[2])).fetchone()[0] == "go")
again = post(CHECK, {"part": "1", "q%d" % qid[1]: "1", "q%d" % qid[2]: "went"})
check("checking it again changes nothing", again.get("ok") and core.handout_parts_done(db, aid)[1]["wrong_n"] == 2)

print("\n4. THE NEXT PART, THEN THE WHOLE")
pg = get(H)
check("part 2 opens by itself now", 'data-part="2"' in pg and "Part 2 of 2" in pg)
check("the header is a strip after the first part", 'class="hx-hero slim"' in pg)
check("the warning box is a warning card", "hx-card hx-warn" in pg and 'class="hx-no">✗' in pg)
check("the table of examples is the site's table", 'class="hx-table hx-wide"' in pg
      and re.search(r"<th>(<p>)?Use", pg) is not None)
out = post(CHECK, {"part": "2", "q%d" % qid[4]: "went"})
check("the last part goes on to the results", out.get("go", "").endswith("&part=end"))
pg = get(H)
check("the results: each part and the whole", 'class="hx-final"' in pg and "1 of 3 right across the 2 parts" in pg
      and pg.count('class="hx-row"') == 2)
check("with what is left for the teacher", "the answer you wrote in your own words" in pg)
lst = get("/s/%s?tab=handouts" % tok)
check("the list says it is finished", "Finished" in lst and "1 of 3 right" in lst)

print("\n5. A REBUILT HANDOUT KEEPS WHAT STUDENTS TYPED")
check("a backtick is an apostrophe", core.answer_matches("won`t", "won't"))
check("a comma needs no space after it", core.answer_matches("yes,let's", "Yes, let's"))
_chip = '<p><input class="bk-blank" data-q="1" style="width:60px"></p>'
_opts = [{"letter": "always", "text": ""}, {"letter": "never", "text": ""}]
_q = {"id": 7, "num": 1, "control": "pair", "answer": None, "kind": "open"}
check("chips for a partner's answer, tapped in class, may stay empty at home",
      "data-optional" in server.handout_controls(_chip, [(_q, _opts)])[0]
      and "data-optional" not in server.handout_controls(_chip, [(dict(_q, control=None), _opts)])[0])
check("a dash on its own is an answer: no article",
      core.answer_matches("–", "–") and core.answer_matches("-", "the/–")
      and not core.answer_matches("–", "a") and not core.answer_matches("the", "–"))
old = core.load_test(db, {
    "level": "Pre-Intermediate", "number": 2, "title": "Old version", "kind": "handout",
    "layout": layout, "passages": {},
    "questions": [
        {"num": 1, "kind": "typed", "prompt": "1.1  1 Clocks", "answer": "1"},
        {"num": 2, "kind": "typed", "prompt": "1.1  2 Go", "answer": "went"},
        {"num": 3, "kind": "open", "prompt": "1.1  3 Why?", "answer": None},
        {"num": 4, "kind": "typed", "prompt": "2.1  1 go", "answer": "went"},
    ]})
new = core.load_test(db, {
    "level": "Pre-Intermediate", "number": 2, "title": "New version", "kind": "handout",
    "layout": layout, "passages": {},
    "questions": [
        {"num": 1, "kind": "typed", "prompt": "1.1  1 Clocks", "answer": "1", "options": DAY},
        {"num": 2, "kind": "typed", "prompt": "1.1  2 Go", "answer": "'ll",
         "options": [{"letter": "'ll", "text": ""}, {"letter": "won't", "text": ""}]},
        {"num": 3, "kind": "open", "prompt": "1.1  3 Why?", "answer": None},
        {"num": 4, "kind": "typed", "prompt": "2.1  1 go", "answer": "went"},
    ]})
other = core.add_student(db, "Bek", g)
oa = core.start_attempt(db, old, other)
oq = {r["num"]: r["id"] for r in db.execute("SELECT id, num FROM dquestions WHERE test_id=?", (old,))}
nq = {r["num"]: r["id"] for r in db.execute("SELECT id, num FROM dquestions WHERE test_id=?", (new,))}
for n, text in ((1, "Day 1"), (2, "will"), (3, "It was quiet"), (4, "goed")):
    db.execute("INSERT INTO dresponses (attempt_id, question_id, given) VALUES (?,?,?)", (oa, oq[n], text))
na = core.start_attempt(db, new, other)
db.execute("INSERT INTO dresponses (attempt_id, question_id, given) VALUES (?,?,?)", (na, nq[4], "went"))
db.commit()
jar = http.cookiejar.CookieJar()
teacher = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
teacher.open(base + "/login", urllib.parse.urlencode({"password": "testpw123"}).encode()).read()
tp = _html.unescape(teacher.open(base + "/tests/%d" % new, timeout=20).read().decode())
check("the teacher's page of a handout offers to bring answers over", "Bring their answers over" in tp
      and "Old version" in tp)
r = teacher.open(base + "/tests/%d/carry" % new, urllib.parse.urlencode({"from": old}).encode(), timeout=20)
check("and says how many came over", "carried=3" in r.geturl() and "students=1" in r.geturl())
got = {r["question_id"]: r["given"] for r in db.execute("SELECT * FROM dresponses WHERE attempt_id=?", (na,))}
check("a typed choice becomes its chip", got.get(nq[1]) == "1")
check("'will' becomes the 'll chip", got.get(nq[2]) == "'ll")
check("their own words come over as they were", got.get(nq[3]) == "It was quiet")
check("what they had already typed in the new one is left alone", got.get(nq[4]) == "went")
check("the old version keeps its copy", db.execute(
    "SELECT COUNT(*) FROM dresponses WHERE attempt_id=?", (oa,)).fetchone()[0] == 4)

check("a comma does not make a sentence wrong",
      core.answer_matches("In the evening I have dinner", "In the evening, I have dinner"))

same = core.load_test(db, {
    "level": "Pre-Intermediate", "number": 2, "title": "Same again", "kind": "handout",
    "layout": layout, "passages": {}, "questions": [
        {"num": 1, "kind": "typed", "prompt": "1.1  1 Clocks", "answer": "1", "options": DAY},
        {"num": 2, "kind": "typed", "prompt": "1.1  2 Go", "answer": "went"},
        {"num": 3, "kind": "open", "prompt": "1.1  3 Why?", "answer": None, "control": "long"},
        {"num": 4, "kind": "typed", "prompt": "2.1  1 go", "answer": "went"},
        {"num": 5, "kind": "open", "prompt": "1.1  4 Your partner?", "answer": None, "control": "pair"}]})
r = teacher.open(base + "/tests/%d/carry" % same, urllib.parse.urlencode({"from": hid}).encode(), timeout=20)
check("parts already checked come over checked", "parts=2" in r.geturl())
sa = db.execute("SELECT id FROM dattempts WHERE test_id=? AND student_id=?", (same, sid)).fetchone()["id"]
sd = core.handout_parts_done(db, sa)
check("and marked again by the new key", sorted(sd) == [1, 2] and sd[1]["wrong_n"] == 2 and sd[2]["right_n"] == 1)
db.execute("UPDATE dtests SET published=1 WHERE id=?", (same,)); db.commit()
spg = get("/s/%s?tab=handouts&h=%d&part=1" % (tok, same))
check("so the student cannot change what they have already seen marked",
      "Reading checked" in spg and 'id="handoutdata"' not in spg)
db.execute("UPDATE dtests SET published=0 WHERE id=?", (same,)); db.commit()

print("\n6. A BOOKLET WHOSE EXPLANATIONS ARE IN UZBEK")
uz = core.load_test(db, {
    "level": "Pre-Intermediate", "number": 3, "title": "Uzbek version", "kind": "handout",
    "layout": layout.replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
                    .replace("Which day?</span></p>", "Which day?</span></p>"
                             '<p class="hx-uz" lang="uz">Qaysi kun? Tanlang.</p>', 1),
    "passages": {}, "questions": [{"num": n, "kind": "open", "prompt": "x", "answer": None}
                                  for n in (1, 2, 3, 4, 5)]})
db.execute("UPDATE dtests SET published=1 WHERE id=?", (uz,)); db.commit()
upg = get("/s/%s?tab=handouts&h=%d" % (tok, uz))
check("its cover says what it teaches in Uzbek", "Bu qoʻllanmada oʻrganasiz" in upg)
check("and it is still split into its parts", "Part 1 of 2" in upg)
check("the instruction is told again in Uzbek, on its own line",
      '<p class="hx-uz" lang="uz">Qaysi kun? Tanlang.</p>' in upg)
check("which is not mistaken for part of the reading text",
      "Qaysi kun" not in upg[upg.index("<article"):upg.index("</article>")])
kinds = server.hx_dress(panel("127D80", "TALAFFUZ — /ɑː/", "<p><span>Ikkita tovush.</span></p>")
                        + panel("127D80", "TOPSHIRISHDAN OLDIN TEKSHIRING", "<p><span>x</span></p>")
                        + panel("127D80", "KALIT SOʻZLAR", "<p><span>x</span></p>"))
check("Uzbek box titles are recognised", "hx-card hx-sound" in kinds and "hx-card hx-check" in kinds
      and "hx-card hx-words" in kinds)

print("\n7. A STUDENT WHO LEAVES TAKES THEIR PARTS WITH THEM")
core.remove_student(db, sid)
check("no part rows are left behind", db.execute("SELECT COUNT(*) FROM dparts").fetchone()[0] == 0)
srv.shutdown()

print()
print("handout_parts: %d checks, %d failed" % (checks, len(fails)))
sys.exit(1 if fails else 0)
