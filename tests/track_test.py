"""A coursebook track is served as the format it really is.

The shelf keeps every track under a .mp3 name, but the mock recordings are
AAC in an MP4 container, because the Mac cannot encode mp3. Sending those
bytes labelled audio/mpeg makes some phones refuse to play them.

Run me with:  python3 run_tests.py track
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import tempfile
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None)

import core, server
core.init_db()
db = core.connect()

fails = []


def check(what, cond):
    print(("  ok  " if cond else "  FAIL") + "  " + what)
    if not cond:
        fails.append(what)


folder = os.path.join(core.AUDIO_DIR, "Elementary")
os.makedirs(folder, exist_ok=True)

# a real mp3 begins with an ID3 tag or a frame header
open(os.path.join(folder, "1.01.mp3"), "wb").write(b"ID3\x03\x00" + b"\0" * 64)
# an m4a begins with a size then "ftyp"
open(os.path.join(folder, "99.01.mp3"), "wb").write(
    b"\x00\x00\x00\x20ftypM4A " + b"\0" * 64)


def kind_of(track):
    code, headers, _body = server.serve_track({}, db, "Elementary", track)
    return code, dict(headers).get("Content-Type")


code, kind = kind_of("1.01")
check("an mp3 is still served as audio/mpeg", code == 200 and kind == "audio/mpeg")
code, kind = kind_of("99.01")
check("an m4a is served as audio/mp4", code == 200 and kind == "audio/mp4")
check("a track that is not there is not found", kind_of("7.77")[0] == 404)
check("a track name with a slash is refused",
      server.serve_track({}, db, "Elementary", "../../etc/passwd")[0] == 404)

print()
print("track: %d failed" % len(fails))
sys.exit(1 if fails else 0)
