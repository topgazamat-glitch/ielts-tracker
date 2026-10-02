"""Deleting files from the shelves: one, the ticked ones, or everything in one
place - and never one stray click, never another level's files, never the
files shared with every level unless they are ticked by name.

He had to remove 336 audio files one by one, each Remove sending him back to
the top of Materials (2026-10-03). This is the page he asked for instead.

Run me with:  python3 run_tests.py materials_delete
"""
import http.cookiejar
import os
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request

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


lvl = {r["name"]: r["id"] for r in db.execute("SELECT id, name FROM levels")}
PI, EL = lvl["Pre-Intermediate"], lvl["Elementary"]


def put(title, level, section="Listening audios", unit=1, size=1000):
    name = "m_%s_%s.mp3" % (title.replace(".", "_"), level)
    with open(os.path.join(core.MATERIAL_DIR, name), "wb") as fh:
        fh.write(b"x" * size)
    return db.execute(
        "INSERT INTO materials (title, filename, original_name, mime, size, level_id, collection, category,"
        " unit, created_at, active) VALUES (?,?,?,?,?,?,?,?,?,?,1)",
        (title, name, title + ".mp3", "audio/mpeg", size, level, "empower", section, unit, now)).lastrowid


pi = [put("1.0%d" % n, PI) for n in range(1, 6)]
pi2 = [put("2.0%d" % n, PI, unit=2) for n in range(1, 3)]
el = [put("1.0%d" % n, EL) for n in range(1, 4)]
shared = put("Welcome song", None, unit=1)
db.commit()


def alive(mid):
    return bool(db.execute("SELECT 1 FROM materials WHERE id=?", (mid,)).fetchone())


def on_disk(mid):
    row = db.execute("SELECT filename FROM materials WHERE id=?", (mid,)).fetchone()
    return bool(row) and os.path.exists(os.path.join(core.MATERIAL_DIR, row["filename"]))


srv = server.Server(("127.0.0.1", 8899), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.4)
base = "http://127.0.0.1:8899"
jar = http.cookiejar.CookieJar()


class NoFollow(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


teacher = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar), NoFollow)
try:
    teacher.open(base + "/login", urllib.parse.urlencode({"password": "pw"}).encode()).read()
except urllib.error.HTTPError:
    pass


def post(fields):
    """(status, where it sends you or the page)"""
    body = urllib.parse.urlencode(fields, doseq=True).encode()
    try:
        r = teacher.open(base + "/materials/delete", body)
        return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Location", "")


here = "/materials?level=%d&c=empower&s=Listening+audios&u=1" % PI

print("1. THE PAGE")
page = teacher.open(base + here).read().decode()
check("the unit's files are rows that can be ticked", page.count('name="id"') == 6)   # 5 + the shared one
check("with a select-all and one button for the ticked", "data-all" in page and "data-picked" in page)
check("and one button for everything here, which says how many of this level's own",
      "Delete all 5 files here" in page)

print("\n2. NOTHING GOES ON ONE CLICK")
st, out = post({"what": "picked", "id": [str(pi[0]), str(pi[1])], "back": here})
check("without the second yes, a page asks: %s" % st, st == 200 and "Delete 2 files?" in out)
check("and nothing is gone", alive(pi[0]) and alive(pi[1]))

print("\n3. THE TICKED ONES")
st, loc = post({"what": "picked", "id": [str(pi[0]), str(pi[1])], "back": here, "confirm": "yes"})
check("gone, from the list and from the disk", not alive(pi[0]) and not alive(pi[1])
      and not os.path.exists(os.path.join(core.MATERIAL_DIR, "m_1_01_%d.mp3" % PI)))
check("and back to the same place, saying what was freed: %s" % loc,
      st in (302, 303) and loc.startswith(here) and "gone=2" in loc and "freed=2000" in loc)
page = teacher.open(base + loc).read().decode()
check("the page says so", "Deleted 2 files" in page)

print("\n4. ONE ROW'S OWN BUTTON")
st, loc = post({"one": str(pi[2]), "id": [str(pi[3])], "back": here, "confirm": "yes"})
check("only that row goes, not what else was ticked", not alive(pi[2]) and alive(pi[3]))

print("\n5. EVERYTHING HERE")
st, loc = post({"what": "scope", "level": str(PI), "c": "empower", "s": "Listening audios", "u": "1",
                "back": here, "confirm": "yes"})
check("this level's unit 1 is empty", not any(alive(m) for m in pi))
check("the next unit is untouched", all(alive(m) for m in pi2))
check("another level's files are untouched", all(alive(m) for m in el))
check("the file shared with every level stays", alive(shared) and on_disk(shared))

print("\n6. NEVER EVERY LEVEL AT ONCE")
st, loc = post({"what": "scope", "c": "empower", "back": "/materials", "confirm": "yes"})
check("a scope with no level deletes nothing", all(alive(m) for m in el + pi2) and alive(shared))
st, loc = post({"what": "picked", "id": [str(el[0])], "back": "https://example.com/", "confirm": "yes"})
check("and it only ever sends you back into Materials: %s" % loc, loc.startswith("/materials"))

print("\n7. A WHOLE LEVEL")
st, out = post({"what": "scope", "level": str(EL), "back": "/materials?level=%d" % EL})
check("asks first, naming how many", st == 200 and "Delete 2 files?" in out)
st, loc = post({"what": "scope", "level": str(EL), "back": "/materials?level=%d" % EL, "confirm": "yes"})
check("then every Elementary file is gone", not any(alive(m) for m in el))
check("and Pre-Intermediate's unit 2 and the shared file are still there", all(alive(m) for m in pi2) and alive(shared))

print("\n8. TICKING THE SHARED FILE BY NAME")
st, loc = post({"what": "picked", "id": [str(shared)], "back": "/materials", "confirm": "yes"})
check("is the one way it goes", not alive(shared))

srv.shutdown()
print()
print("materials_delete: %d checks, %d failed" % (checks, len(fails)))
sys.exit(1 if fails else 0)
