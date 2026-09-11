"""Missing — see the assertions for what it guarantees.

Run me with:  python3 run_tests.py            (all of them)
              python3 tests/missing_test.py   (just this one)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
FIXTURES = os.path.join(ROOT, "tests", "fixtures")

import tempfile, shutil
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp

import core, server
core.init_db(); db = core.connect(); cfg = core.load_config()
today = core.local_day(core.now(), cfg)
core.save_song(db, today, "a.mp3", b"\xff\xfb\x90\x00" + b"\0"*5000, "Present", None)
h = server.view_music({"query": {}, "form": {}}, db)[2].decode("utf-8")
print("file present   ->", "on disk" in h, "| warning shown:", "lost their audio" in h)
os.remove(os.path.join(core.MUSIC_DIR, core.song_today(db, cfg)["filename"]))
h = server.view_music({"query": {}, "form": {}}, db)[2].decode("utf-8")
print("file deleted   ->", "file missing" in h, "| warning shown:", "lost their audio" in h)
assert "file missing" in h and "lost their audio" in h
print("/song then returns:", "404" if not server.song_range(db, None, None) else "200")
db.close(); shutil.rmtree(tmp)
print("Missing-file reporting works.")
