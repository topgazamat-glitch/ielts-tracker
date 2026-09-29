"""The parents' channel: a class's week or month worked out, drawn, written in
Uzbek and Russian, and posted - with nothing sent from the demo, and nothing
sent twice by a second press.

Run me with:  python3 run_tests.py parents
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
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None); os.environ["TEACHER_PASSWORD"] = "pw"
import core, server, parents, card, bot

cfg = core.load_config()
db = core.init_db()
fails, checks = [], 0


def check(what, cond):
    global checks
    checks += 1
    print(("  ok  " if cond else "  FAIL") + "  " + what)
    if not cond:
        fails.append(what)


print("1. THE WEEK AND THE MONTH")
# Wednesday 30 September 2026, 15:00 in Tashkent
at = datetime(2026, 9, 30, 10, 0, tzinfo=timezone.utc)
w = parents.period("week", cfg, at)
check("a week starts on Monday, local midnight", str(w["first"]) == "2026-09-28"
      and w["lo"] == "2026-09-27T19:00:00+00:00")
check("and runs up to now", w["hi"] == core.iso(at))
lw = parents.period("lastweek", cfg, at)
check("last week is Monday to Sunday", str(lw["first"]) == "2026-09-21" and str(lw["last"]) == "2026-09-27")
check("and is compared with the week before it", lw["before"]["lo"] == "2026-09-13T19:00:00+00:00")
m = parents.period("month", cfg, at)
lm = parents.period("lastmonth", cfg, at)
check("this month is September, last month August",
      str(m["first"]) == "2026-09-01" and str(lm["first"]) == "2026-08-01" and str(lm["last"]) == "2026-08-31")
check("dates in Uzbek and Russian", parents.span_uz(lw["first"], lw["last"]) == "21–27-sentabr"
      and parents.span_ru(lw["first"], lw["last"]) == "21–27 сентября"
      and parents.span_ru(w["first"], w["first"] + timedelta(days=6)) == "28 сентября – 4 октября")
check("Russian counts words properly", [parents.ru_plural(n, "слово", "слова", "слов")
                                        for n in (1, 3, 5, 11, 21, 22)]
      == ["слово", "слова", "слов", "слов", "слово", "слова"])

print("\n2. ONE CLASS'S WEEK")
now = core.now()
lvl = db.execute("SELECT id FROM levels WHERE name='Elementary'").fetchone()["id"]
g = db.execute("INSERT INTO groups (name, join_code, created_at, level_id) VALUES ('114','E',?,?)",
               (core.iso(now - timedelta(days=40)), lvl)).lastrowid
g2 = db.execute("INSERT INTO groups (name, join_code, created_at, level_id) VALUES ('116','F',?,?)",
                (core.iso(now - timedelta(days=40)), lvl)).lastrowid
aziza = core.add_student(db, "Aziza", g)
bek = core.add_student(db, "Bekzod", g)
moh = core.add_student(db, "Мохинур", g)
core.add_student(db, "Otabek", g2)
p = parents.period("week", cfg)
lo = core.parse(p["lo"])
set_at, due = lo + timedelta(hours=1), min(lo + timedelta(hours=30), now - timedelta(minutes=5))
a1 = db.execute("INSERT INTO assignments (group_id, title, created_at, published, due_at) VALUES (?,?,?,1,?)",
                (g, "Writing 1", core.iso(set_at), core.iso(due))).lastrowid
for sid, score in ((aziza, 9), (moh, 6)):
    db.execute("INSERT INTO submissions (student_id, assignment_id, created_at, status, score, graded_at)"
               " VALUES (?,?,?,?,?,?)", (sid, a1, core.iso(set_at + timedelta(hours=2)), "graded", score,
                                         core.iso(due)))
day = core.local_day(set_at, cfg)
for sid, v, note in ((aziza, 5, "Juda faol boʻldi."), (bek, 3, ""), (moh, 4, "")):
    db.execute("INSERT INTO lesson_marks (student_id, day, punctuality, behaviour, participation,"
               " note, created_at) VALUES (?,?,?,?,?,?,?)", (sid, day, v, v, v, note, core.iso(now)))
db.execute("INSERT INTO assignments (group_id, title, created_at, published, due_at) VALUES (?,?,?,1,?)",
           (g, "Unit 2A handout", core.iso(set_at), core.iso(now + timedelta(days=2))))
db.commit()
rep = parents.class_report(db, g, p, cfg)
row = {r["student"]["name"]: r for r in rep["rows"]}
check("homework done and set, per student", (row["Aziza"]["done"], row["Aziza"]["set"]) == (1, 1)
      and (row["Bekzod"]["done"], row["Bekzod"]["missing"]) == (0, 1))
check("the mark is of the work handed in", row["Aziza"]["average"] == 9 and row["Bekzod"]["average"] is None)
check("each lesson with its three marks and the teacher's note",
      len(row["Aziza"]["lessons"]) == 1 and row["Aziza"]["lessons"][0]["marks"] == [5, 5, 5]
      and row["Aziza"]["lessons"][0]["note"] == "Juda faol boʻldi.")
check("lesson marks averaged out of five", row["Aziza"]["conduct"] == 5 and row["Bekzod"]["conduct"] == 3)
states = {r["student"]["name"]: [(i["title"], i["state"], i["mark"]) for i in r["items"]] for r in rep["rows"]}
check("each piece of homework and how it went",
      states["Aziza"] == [("Writing 1", "marked", 9), ("Unit 2A handout", "pending", None)]
      and states["Bekzod"][0] == ("Writing 1", "missing", None))
check("with no season running, the class is ranked on the week",
      [r["student"]["name"] for r in rep["rows"]] == ["Aziza", "Мохинур", "Bekzod"]
      and rep["rows"][0]["rank"] == 1)
check("points week by week, this week last", len(row["Aziza"]["weekly"]) == parents.WEEKS_SHOWN
      and row["Aziza"]["weekly"][-1][1] == row["Aziza"]["gained"] > 0)
uz, ru = parents.summary_uz(row["Aziza"], rep), parents.summary_ru(row["Aziza"], rep)
check("a few sentences in Uzbek", "Aziza 1 ta darsda baho oldi" in uz and "1-oʻrinda" in uz)
check("and in Russian", "сдано 1 из 1" in ru and "1-е место в группе" in ru)
check("Bekzod's says what is missing", "1 ta vazifa topshirilmagan" in parents.summary_uz(row["Bekzod"], rep)
      and "Не сдано: 1" in parents.summary_ru(row["Bekzod"], rep))
check("points in Russian", [parents.points_ru(x) for x in (1, 2, 5, 10.9, 21)]
      == ["очко", "очка", "очков", "очка", "очко"])

print("\n3. THE PICTURES")
lg, one = card.league(rep), card.student(row["Мохинур"], rep)
check("the league is a picture", lg[:8] == b"\x89PNG\r\n\x1a\n" and len(lg) > 5000)
check("so is each student's report", one[:8] == b"\x89PNG\r\n\x1a\n")
check("every letter they use is in the font", all(
    ch in card.atlas()["m32"]["glyphs"] for ch in "Мохинур Oʻrtacha Ўғҳқ Ёё"))
pics = parents.pictures(rep)
check("a class is its league and then a picture a student, each named",
      len(pics) == 4 and "114-guruh" in pics[0][1] and pics[1][1].startswith("Aziza"))
big = dict(rep, rows=rep["rows"] * 6)
check("a long class has its league over two pictures", len(parents.pictures(big)) == 2 + 18)

print("\n4. THE PAGE, AND SENDING")
server.CFG["telegram_token"] = "TEST-TOKEN"
posted = []


def fake_album(token, chat_id, pngs, caption="", captions=None):
    posted.append(("album", chat_id, len(pngs), captions))
    return {"ok": True, "result": []}


def fake_send(token, chat_id, text, keyboard=None, markup=None):
    posted.append(("text", chat_id, text))
    return {"ok": True, "result": {"message_id": 1}}


bot.send_album, bot.send = fake_album, fake_send
parents._sleep = lambda s: None

srv = server.Server(("127.0.0.1", 8894), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.4)
base = "http://127.0.0.1:8894"
jar = http.cookiejar.CookieJar()
teacher = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
teacher.open(base + "/login", urllib.parse.urlencode({"password": "pw"}).encode()).read()


def get(path):
    return _html.unescape(teacher.open(base + path, timeout=30).read().decode())


def press(path, fields):
    r = teacher.open(base + path, urllib.parse.urlencode(fields, doseq=True).encode(), timeout=30)
    return r.geturl(), _html.unescape(r.read().decode())


pg = get("/parents")
check("the page shows each class: its league and a picture a student",
      "114" in pg and "116" in pg and "/parents/card.png?g=%d&p=week&k=league" % g in pg
      and "k=student&s=%d" % aziza in pg)
check("a class with nothing that week is not ticked", "Nothing to report" in pg
      and 'name="g" value="%d" checked' % g2 not in pg and 'name="g" value="%d" checked' % g in pg)
check("and is in the teacher's menu", 'href="/parents"' in get("/"))
r = teacher.open(base + "/parents/card.png?g=%d&p=week&k=student&s=%d" % (g, moh), timeout=30)
check("a student's picture is served as a picture", r.headers.get("Content-Type") == "image/png"
      and r.read()[:4] == b"\x89PNG")
check("without a channel, sending is not offered", "No channel yet" in pg)
where, _pg = press("/parents/send", {"p": "week", "g": [g, g2]})
check("and a send is refused", "e=channel" in where and not posted)

# the teacher adds the bot to the channel; Telegram tells the bot
bot.note_channel(db, {"chat": {"id": -1001234, "type": "channel", "title": "Ota-onalar 114"},
                      "new_chat_member": {"status": "administrator"}})
check("the bot remembers the channel it was made an admin of",
      core.parents_channel(db)["id"] == -1001234)
bot.note_channel(db, {"chat": {"id": 55, "type": "private"}, "text": "hi"})
check("a private chat is not a channel", core.parents_channel(db)["id"] == -1001234)
pg = get("/parents")
check("the page says where it will post", "Ota-onalar 114" in pg)

session = next(c.value for c in jar if c.name == "ta_session")
req = urllib.request.Request(base + "/parents/send", urllib.parse.urlencode(
    {"p": "week", "g": [g]}, doseq=True).encode(),
    headers={"Cookie": "ta_session=%s; ta_demo=1" % session})


class Stay(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None                        # read where it would go, do not follow


try:
    urllib.request.build_opener(Stay).open(req, timeout=120)
    where = ""
except urllib.error.HTTPError as e:
    where = e.headers.get("Location") or ""
check("nothing is sent from the demo", "e=demo" in where and not posted)

where, _pg = press("/parents/send", {"p": "week", "g": [g, g2], "note_%d" % g: "Juma kuni dars yoʻq."})
check("sending starts, and the page says so", "sent=1" in where)
for _ in range(100):
    st = parents.sending(db)
    if st and st.get("finished"):
        break
    time.sleep(0.1)
check("the note first, then each class's pictures",
      [k[0] for k in posted] == ["text", "album", "album"])
check("into the channel", all(k[1] == -1001234 for k in posted))
check("the note says which class it is for", "114-guruh" in posted[0][2] and "Juma kuni" in posted[0][2])
check("a class's album: the league, then a picture a student, each captioned",
      posted[1][2] == 4 and "114-guruh" in posted[1][3][0] and posted[1][3][1].startswith("Aziza")
      and posted[2][2] == 2)
check("nothing went wrong", st["errors"] == [] and st["done"] == 2 and st["pictures"] == 6)
pg = get("/parents")
check("a class already sent is marked, and not ticked again",
      "Sent " in pg and 'name="g" value="%d" checked' % g not in pg)

where, _pg = press("/parents/say", {"text": "Hurmatli ota-onalar! Ertaga dars yoʻq."})
check("one message to all parents goes to the channel",
      "said=1" in where and posted[-1] == ("text", -1001234, "Hurmatli ota-onalar! Ertaga dars yoʻq."))

bot.note_channel(db, {"chat": {"id": -1001234, "type": "channel", "title": "Ota-onalar 114"},
                      "new_chat_member": {"status": "left"}})
check("taken off the channel, the bot stops posting there", core.parents_channel(db) is None)
srv.shutdown()

print()
print("parents: %d checks, %d failed" % (checks, len(fails)))
sys.exit(1 if fails else 0)
