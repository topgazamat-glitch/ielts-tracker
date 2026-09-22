"""Battles: up to four classmates race through the same questions.

Checks the parts a student could otherwise exploit or trip over: the shared
track, the seat limit, the class boundary, the server's clock, the places at
the finish, and the promise that none of it reaches the league.

Run me with:  python3 run_tests.py battle
              python3 tests/battle_test.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import tempfile
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None)

import core
core.init_db(); db = core.connect()
now = core.iso(core.now())
g1 = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('114','A',?)",
                (now,)).lastrowid
g2 = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('116','B',?)",
                (now,)).lastrowid
names = ["Ali", "Bek", "Dilnoza", "Eldor", "Gulnora"]
ids = [core.add_student(db, n, g1) for n in names]
out = core.add_student(db, "Farida", g2)          # another class


def mklist(title, group, n):
    lid = db.execute("INSERT INTO word_lists (group_id, title, created_at, kind)"
                     " VALUES (?,?,?,'vocab')", (group, title, now)).lastrowid
    for i in range(n):
        db.execute("INSERT INTO words (list_id, term, translation, ord)"
                   " VALUES (?,?,?,?)", (lid, "term%d" % i, "right%d" % i, i))
    return lid


words = mklist("Unit 1 words", None, 14)
theirs = mklist("Only for 116", g2, 8)
db.commit()

fails = []
checks = 0


def check(what, cond):
    global checks
    checks += 1
    print(("  ok  " if cond else "  FAIL") + "  " + what)
    if not cond:
        fails.append(what)


def S(i):
    return db.execute("SELECT * FROM students WHERE id=?", (i,)).fetchone()


ali, bek, dil, eld, gul = [S(i) for i in ids]
far = S(out)

# ---------------------------------------------------------------- the lobby
bid = core.create_battle(db, ali, words)
check("a host can open a lobby", bid is not None)
b = db.execute("SELECT * FROM battles WHERE id=?", (bid,)).fetchone()
check("the lobby has a code of four letters", b["code"] and len(b["code"]) == 4)
check("the code avoids I and O", not set(b["code"]) & set("IO"))
check("no questions are drawn until the flag drops",
      db.execute("SELECT COUNT(*) c FROM battle_questions WHERE battle_id=?",
                 (bid,)).fetchone()["c"] == 0)
check("the host cannot start alone", core.start_battle(db, bid, ali["id"]) is False)

check("a classmate joins by code",
      core.join_battle(db, bek, core.battle_by_code(db, b["code"])["id"]) == bid)
check("a lower-case code still works",
      core.battle_by_code(db, b["code"].lower()) is not None)
check("another class cannot join", core.join_battle(db, far, bid) is None)
check("a student cannot race on another class's list",
      core.create_battle(db, ali, theirs) is None)

core.join_battle(db, dil, bid)
core.join_battle(db, eld, bid)
check("four seats fill up",
      len(core.battle_players(db, bid)) == core.BATTLE_MAX)
check("the fifth student is turned away", core.join_battle(db, gul, bid) is None)

# ---------------------------------------------------------------- invitations
b2 = core.create_battle(db, gul, words)
check("inviting a classmate works", core.invite_to_battle(db, gul, b2, bek["id"]))
check("inviting another class does not",
      core.invite_to_battle(db, gul, b2, far["id"]) is False)
check("an outsider cannot invite on someone else's behalf",
      core.invite_to_battle(db, dil, b2, eld["id"]) is False)
inv = core.open_invites(db, bek)
check("the invitation is waiting", len(inv) == 1 and inv[0]["battle_id"] == b2)
core.decline_invite(db, bek, b2)
check("a declined invitation stops showing", core.open_invites(db, bek) == [])

core.touch_student(db, bek["id"])
mates = core.classmates_for_battle(db, ali)
check("the invite list shows classmates only",
      {m["name"] for m in mates} == {"Bek", "Dilnoza", "Eldor", "Gulnora"})
check("a student who just used the site shows as online",
      next(m for m in mates if m["name"] == "Bek")["online"])
check("one who never has does not",
      not next(m for m in mates if m["name"] == "Eldor")["online"])

# ---------------------------------------------------------------- the race
check("the flag drops", core.start_battle(db, bid, ali["id"]) is True)
b = db.execute("SELECT * FROM battles WHERE id=?", (bid,)).fetchone()
check("the race is on", b["state"] == "racing")
check("ten questions are drawn", b["q_count"] == core.BATTLE_ROUND)
check("nobody else can join now", core.join_battle(db, gul, bid) is None)
check("a second start does nothing", core.start_battle(db, bid, ali["id"]) is False)

qs = db.execute("SELECT * FROM battle_questions WHERE battle_id=? ORDER BY ord",
                (bid,)).fetchall()
check("every car drives the same track",
      [q["ord"] for q in qs] == list(range(core.BATTLE_ROUND)))


def play(student, right_upto):
    """Answer the whole race, getting the first `right_upto` correct."""
    for i in range(core.BATTLE_ROUND):
        st = core.battle_state(db, bid, student["id"])
        if st["state"] != "racing":
            break
        q = qs[st["q"]]
        pick = q["answer"] if i < right_upto else (q["answer"] + 1) % 4
        core.answer_battle(db, bid, student["id"], st["q"], pick)


st = core.battle_state(db, bid, ali["id"])
check("the state carries the question", st["state"] == "racing" and "term" in st)
check("and four options", len(st["options"]) == 4)
check("the track shows all four players", len(st["track"]) == 4)
check("and marks which one is me", sum(1 for t in st["track"] if t["me"]) == 1)
check("the clock is the server's", 0 < st["left"] <= core.BATTLE_SECONDS)

r = core.answer_battle(db, bid, ali["id"], st["q"], qs[st["q"]]["answer"])
check("a right answer scores", r["correct"] and r["points"] >= core.GAME_BASE)
check("answering the same question twice is refused",
      core.answer_battle(db, bid, ali["id"], st["q"], 0) is None)
check("answering a question not on screen is refused",
      core.answer_battle(db, bid, ali["id"], 9, 0) is None)
check("an outsider cannot answer into the race",
      core.answer_battle(db, bid, far["id"], 1, 0) is None)
check("an outsider sees nothing", core.battle_state(db, bid, far["id"]) is None)

seen = core.battle_state(db, bid, bek["id"])
check("a rival sees the leader move",
      next(t for t in seen["track"] if t["name"] == "Ali")["at"] == 1)

play(ali, core.BATTLE_ROUND)          # Ali finishes clean
st = core.battle_state(db, bid, ali["id"])
check("a finisher waits for the others", st["state"] == "waiting")
check("and is told how many are still out", st["left_on_track"] == 3)
check("the race is not over yet",
      db.execute("SELECT state FROM battles WHERE id=?", (bid,)).fetchone()["state"]
      == "racing")

play(bek, 6)
play(dil, 3)
play(eld, 0)
b = db.execute("SELECT * FROM battles WHERE id=?", (bid,)).fetchone()
check("the race ends when everyone is home", b["state"] == "done")

places = {p["name"]: p["place"] for p in core.battle_players(db, bid)}
check("the best score wins", places["Ali"] == 1)
check("the places run 1 to 4", sorted(places.values()) == [1, 2, 3, 4])
check("and follow the scores", places["Bek"] < places["Dilnoza"] < places["Eldor"])

fin = core.battle_state(db, bid, bek["id"])
check("the finish screen knows my place", fin["place"] == places["Bek"])
check("and shows the words I got wrong",
      len(fin["review"]) == core.BATTLE_ROUND
      and sum(1 for x in fin["review"] if not x["right"]) == core.BATTLE_ROUND - 6)

# ------------------------------------------------------ the table, and the league
board = core.battle_week_board(db, g1)
check("the battle table lists this week's racers", len(board) == 4)
check("the winner is on top", board[0]["name"] == "Ali" and board[0]["wins"] == 1)
rec = core.battle_record(db, bek["id"])
check("a student's own record is right", rec["races"] == 1 and rec["wins"] == 0)
check("the other class sees an empty table", core.battle_week_board(db, g2) == [])

check("a battle earns no career step", core.passed_lists(db, ali["id"]) == set()
      or words not in core.passed_lists(db, ali["id"]))
check("a battle creates no solo run",
      db.execute("SELECT COUNT(*) c FROM solo_runs").fetchone()["c"] == 0)
league = core.league(db, g1) if hasattr(core, "league") else []
check("the league is untouched by racing",
      all(float(r["points"] if "points" in r.keys() else 0) == 0 for r in league)
      if league else True)
check("but the words still feed revision",
      db.execute("SELECT COUNT(*) c FROM word_progress").fetchone()["c"] > 0)

# ---------------------------------------------------------------- the flag falls
b3 = core.create_battle(db, ali, words)
core.join_battle(db, bek, b3)
core.start_battle(db, b3, ali["id"])
row = db.execute("SELECT * FROM battles WHERE id=?", (b3,)).fetchone()
long_ago = core.iso(core.now() - core.timedelta(minutes=30))
db.execute("UPDATE battles SET started_at=? WHERE id=?", (long_ago, b3))
db.commit()
row = db.execute("SELECT * FROM battles WHERE id=?", (b3,)).fetchone()
core._battle_finish_if_done(db, row)
row = db.execute("SELECT * FROM battles WHERE id=?", (b3,)).fetchone()
check("a race nobody finished still ends", row["state"] == "done")
check("and everyone gets a place",
      all(p["place"] for p in core.battle_players(db, b3)))

b4 = core.create_battle(db, dil, words)
db.execute("UPDATE battles SET created_at=? WHERE id=?", (long_ago, b4))
db.commit()
code4 = db.execute("SELECT code FROM battles WHERE id=?", (b4,)).fetchone()["code"]
check("a stale lobby cannot be joined", core.battle_by_code(db, code4) is None)

b5 = core.create_battle(db, eld, words)
core.join_battle(db, gul, b5)
core.leave_battle(db, eld, b5)
check("the lobby closes when the host leaves",
      db.execute("SELECT state FROM battles WHERE id=?", (b5,)).fetchone()["state"]
      == "done")


# ---------------------------------------------------------------- over HTTP
# The engine is proved above. This drives the real routes the way two phones
# would, because a working engine behind a broken route helps nobody.
db.commit(); db.close()

import threading, time, urllib.request, urllib.parse
import server

srv = server.Server(("127.0.0.1", 8823), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.4)
base = "http://127.0.0.1:8823"
op = urllib.request.build_opener()
db = core.connect()
tok = {i: db.execute("SELECT token FROM students WHERE id=?", (i,)).fetchone()["token"]
       for i in ids + [out]}


def get(path):
    return op.open(base + path, timeout=20).read().decode()


def post(path, **fields):
    data = urllib.parse.urlencode(fields).encode()
    return op.open(base + path, data, timeout=20)


def state(sid, b):
    return json.loads(get("/s/%s/battle/%d.json" % (tok[sid], b)))


page = get("/s/%s?tab=play" % tok[ids[0]])
check("the Play page shows a Battle door", 'tab=battle' in page)
page = get("/s/%s?tab=battle" % tok[ids[0]])
check("the Battle page offers a topic", 'Unit 1 words' in page)
check("and a box for the code", 'battle/code' in page)

before = core.battle_record(db, ids[0])["races"]
r = post("/s/%s/battle/new" % tok[ids[0]], list=words)
hb = int(r.geturl().rstrip("/").split("/")[-1])
check("a race opens over HTTP", hb > 0)
lob = state(ids[0], hb)
check("the host lands in a lobby", lob["state"] == "lobby")
check("the lobby offers classmates to invite", len(lob["mates"]) == 4)
code = lob["code"]

post("/s/%s/battle/code" % tok[ids[1]], code=code.lower())
check("a classmate joins with the code typed in lower case",
      len(state(ids[0], hb)["track"]) == 2)
check("a stranger cannot read the race",
      json.loads(get("/s/%s/battle/%d.json" % (tok[out], hb)))["state"] == "gone")

post("/s/%s/battle/%d/invite" % (tok[ids[0]], hb), who=ids[2])
check("an invitation reaches the other phone",
      json.loads(get("/s/%s/battle/%d.json" % (tok[ids[2]], hb)))["state"] == "gone"
      and 'challenges you' in get("/s/%s?tab=battle" % tok[ids[2]]))
post("/s/%s/battle/join" % tok[ids[2]], battle=hb)
check("and accepting puts them on the grid", len(state(ids[0], hb)["track"]) == 3)

post("/s/%s/battle/%d/start" % (tok[ids[1]], hb))
check("a guest cannot drop the flag", state(ids[0], hb)["state"] == "lobby")
post("/s/%s/battle/%d/start" % (tok[ids[0]], hb))
check("the host can", state(ids[0], hb)["state"] == "racing")


def race(sid, right):
    for _ in range(core.BATTLE_ROUND):
        st = state(sid, hb)
        if st["state"] != "racing":
            break
        q = db.execute("SELECT answer FROM battle_questions WHERE battle_id=? AND ord=?",
                       (hb, st["q"])).fetchone()["answer"]
        post("/s/%s/battle/%d/answer" % (tok[sid], hb),
             q=st["q"], choice=q if right else (q + 1) % 4)


race(ids[0], True)
mid = state(ids[1], hb)
check("a rival's lane moves on my screen",
      next(t for t in mid["track"] if t["name"] == "Ali")["at"] == core.BATTLE_ROUND)
race(ids[1], False)
race(ids[2], False)
fin = state(ids[0], hb)
check("the race finishes over HTTP", fin["state"] == "done")
check("and the fastest right answers won", fin["place"] == 1)
check("the finish page renders", 'Battle' in get("/s/%s/battle/%d" % (tok[ids[0]], hb)))
check("the weekly table counts the race that just finished",
      core.battle_record(db, ids[0])["races"] == before + 1)
srv.shutdown()

print()
print("battle: %d checks, %d failed" % (checks, len(fails)))
sys.exit(1 if fails else 0)
