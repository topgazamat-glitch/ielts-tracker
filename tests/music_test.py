"""Music — see the assertions for what it guarantees.

Run me with:  python3 run_tests.py            (all of them)
              python3 tests/music_test.py   (just this one)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
FIXTURES = os.path.join(ROOT, "tests", "fixtures")

import tempfile, shutil, re, struct
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp

import core, server, uploads
core.init_db(); db = core.connect(); cfg = core.load_config()
g = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('T','TT',?)",
               (core.iso(core.now()),)).lastrowid
db.execute("INSERT INTO students (name, group_id, active, token, created_at)"
           " VALUES ('Ali',?,1,'tok',?)", (g, core.iso(core.now()))); db.commit()
st = db.execute("SELECT * FROM students").fetchone()
today = core.local_day(core.now(), cfg)

# a small but genuine mp3 frame payload
blob = b"ID3\x03\x00\x00\x00\x00\x00\x00" + (b"\xff\xfb\x90\x00" + b"\x00" * 400) * 300
print("test file: %.1f KB" % (len(blob) / 1024.0))

class Hdr(dict):
    def get(self, k, d=None): return dict.get(self, k, d)

print("\n1. Before anything is uploaded")
print("   student page has SONG:", "window.SONG" in server.student_page("x", "y"))
print("   /song returns:", "404" if not server.song_range(db, None, None) else "200")

print("\n2. Upload through the real form handler")
fields = {"day": [today], "title": ["Lovely Day"], "artist": ["Bill Withers"]}
files = [("lovely day.mp3", blob)]
r = server.act_new_song({"query": {}, "form": {}, "files": (fields, files)}, db)
print("   redirect:", r[1][0][1] if r[0] in (302, 303) else r[0])
row = core.song_today(db, cfg)
print("   stored as:", row["filename"], "|", row["mime"], "|", row["bytes"], "bytes")
print("   on disk:", os.path.isfile(os.path.join(core.MUSIC_DIR, row["filename"])))

print("\n3. Serving (the plan, streamed from disk)")
code, hdrs, path, start, length = server.song_range(db, None, None)
h = dict(hdrs)
print("   full:  %d  %s  %s bytes  accept-ranges=%s" % (
    code, h["Content-Type"], h["Content-Length"], h.get("Accept-Ranges")))
assert code == 200 and length == len(blob) and start == 0
code, hdrs, path, start, length = server.song_range(db, None, "bytes=100-199")
print("   range: %d  %s  %d bytes from %d" % (
    code, dict(hdrs).get("Content-Range"), length, start))
assert code == 206 and length == 100 and start == 100
code, hdrs, path, start, length = server.song_range(db, None, "bytes=-50")
print("   tail:  %d  %s" % (code, dict(hdrs).get("Content-Range")))
assert code == 206 and start == len(blob) - 50
print("   past the end: %d (416 = correct refusal)"
      % server.song_range(db, None, "bytes=999999999-")[0])
assert server.song_range(db, None, "bytes=999999999-")[0] == 416

print("\n4. It reaches both shells")
server.forget_song()
sp = server.student_page("x", "y")
tp = server.page("x", "y")
m = re.search(r"window\.SONG=(\{[^}]*\})", sp)
print("   student:", m.group(1) if m else "MISSING")
print("   teacher carries it too:", "window.SONG" in tp)
print("   music.js loaded on teacher page:", "/static/music.js" in tp)
assert m and "window.SONG" in tp and "/static/music.js" in tp

print("\n5. Replacing the same day keeps one file")
files = [("other.m4a", blob[:5000])]
server.act_new_song({"query": {}, "form": {},
                     "files": ({"day": [today], "title": ["Second try"]}, files)}, db)
print("   files on disk:", sorted(os.listdir(core.MUSIC_DIR)))
row = core.song_today(db, cfg)
print("   now:", row["filename"], row["mime"], row["title"])
assert len(os.listdir(core.MUSIC_DIR)) == 1

print("\n6. Refusals")
for name, data, why in [("notes.txt", b"hello", "not audio"),
                        ("huge.mp3", b"x" * (21 * 1024 * 1024), "over 20 MB")]:
    r = server.act_new_song({"query": {}, "form": {},
                             "files": ({"day": [today]}, [(name, data)])}, db)
    print("   %-10s -> %s (%s)" % (name, r[1][0][1].split("note=")[-1], why))
r = server.act_new_song({"query": {}, "form": {}, "files": ({"day": [today]}, [])}, db)
print("   no file   -> %s" % r[1][0][1].split("note=")[-1])
print("   the good song survived all that:", core.song_today(db, cfg)["title"])

print("\n7. The teacher page renders")
h = server.view_music({"query": {}, "form": {}}, db)[2].decode("utf-8")
print("   %d bytes, has player: %s, has upload form: %s, lists the day: %s" % (
    len(h), "<audio" in h, 'name="song"' in h, today in h))

print("\n8. Removing it")
server.act_delete_song({"query": {}, "form": {"day": [today]}}, db)
print("   row gone:", core.song_today(db, cfg) is None,
      "| file gone:", os.listdir(core.MUSIC_DIR) == [])
server.forget_song()
print("   student page falls back to the synth:",
      "window.SONG" not in server.student_page("x", "y"))
print("\nAll music checks passed.")
db.close(); shutil.rmtree(tmp)
