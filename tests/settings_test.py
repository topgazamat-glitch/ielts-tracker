"""Settings — what it can throw away, and what it must never touch.

Run me with:  python3 run_tests.py settings
"""
import json
import os
import sys
import tempfile
from datetime import timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None)
import core
core.init_db(); db = core.connect()
os.makedirs(core.UPLOAD_DIR, exist_ok=True)
os.makedirs(core.AUDIO_DIR, exist_ok=True)
os.makedirs(core.MUSIC_DIR, exist_ok=True)

g = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('G','G',?)",
               (core.iso(core.now()),)).lastrowid
sid = db.execute("INSERT INTO students (name, group_id, active, created_at)"
                 " VALUES ('S',?,1,?)", (g, core.iso(core.now()))).lastrowid
old = core.iso(core.now() - timedelta(days=60))


def page(name, tg, when):
    sub = db.execute("INSERT INTO submissions (student_id, status, created_at, kind)"
                     " VALUES (?,'graded',?,'photo')", (sid, when)).lastrowid
    open(os.path.join(core.UPLOAD_DIR, name), "wb").write(b"x" * 9000)
    db.execute("INSERT INTO files (submission_id, filename, telegram_file_id, ord)"
               " VALUES (?,?,?,1)", (sub, name, tg))
    db.commit()


page("keep_only_copy.jpg", None, old)          # the web upload: only copy
page("from_telegram.jpg", "tg-1", old)         # recoverable
page("recent.jpg", "tg-2", core.iso(core.now()))
open(os.path.join(core.AUDIO_DIR, "10.02.mp3"), "wb").write(b"a" * 3000)
open(os.path.join(core.MUSIC_DIR, "song.mp3"), "wb").write(b"m" * 3000)
here = lambda p, n: os.path.isfile(os.path.join(p, n))

print("1. THE SUMMARY SAYS WHAT EXISTS NOWHERE ELSE")
s = core.storage_summary(db)
photos = [r for r in s["rows"] if r["key"] == "photos"][0]
print("   ", photos["note"])
assert "exist nowhere else" in photos["note"]
assert photos["danger"]

print("\n2. LETTING GO OF OLD PHOTOS SPARES THE ONLY COPY")
print("   ", core.purge(db, "photos", days=30))
print("   the web upload is still here:", here(core.UPLOAD_DIR, "keep_only_copy.jpg"))
print("   the Telegram one has gone:  ", not here(core.UPLOAD_DIR, "from_telegram.jpg"))
print("   today's work is untouched:  ", here(core.UPLOAD_DIR, "recent.jpg"))
assert here(core.UPLOAD_DIR, "keep_only_copy.jpg"), "the only copy must survive"
assert not here(core.UPLOAD_DIR, "from_telegram.jpg")
assert here(core.UPLOAD_DIR, "recent.jpg")

print("\n3. AUDIO AND SONGS CAN GO")
print("   ", core.purge(db, "audio"))
print("   ", core.purge(db, "music"))
assert not here(core.AUDIO_DIR, "10.02.mp3")
assert not here(core.MUSIC_DIR, "song.mp3")

print("\n4. THE NEWEST BACKUP IS ALWAYS KEPT")
import jobs
for _ in range(3):
    jobs.backup()
folder = os.path.join(core.DATA_DIR, "backups")
for i, day in enumerate(("2026-01-01", "2026-01-02")):
    open(os.path.join(folder, "app-%s.db" % day), "wb").write(b"b" * 1000)
before = sorted(os.listdir(folder))
print("   ", core.purge(db, "backups"))
after = sorted(os.listdir(folder))
print("   %d backups -> %d, newest kept: %s" % (len(before), len(after), after))
assert len(after) == 1 and after == before[-1:]

print("\n5. SAVING SETTINGS KEEPS THE SECRETS")
path = os.path.join(core.DATA_DIR, "config.json")
json.dump({"teacher_password": "hunter-hunter-hunter",
           "telegram_token": "123:secret", "photo_keep_days": 90},
          open(path, "w"))
core.save_settings({"photo_keep_days": "14", "min_photo_width": "800"},
                   {"automation": True, "backup_to_telegram": False})
now = json.load(open(path))
print("   kept days:", now["photo_keep_days"], "| automation:", now["automation"],
      "| backup to telegram:", now["backup_to_telegram"])
assert now["photo_keep_days"] == 14 and now["min_photo_width"] == 800
assert now["automation"] is True and now["backup_to_telegram"] is False
print("   password still there:", now["teacher_password"] == "hunter-hunter-hunter")
print("   bot token still there:", now["telegram_token"] == "123:secret")
assert now["teacher_password"] == "hunter-hunter-hunter"
assert now["telegram_token"] == "123:secret"

print("\n6. RUBBISH IN THE FORM CHANGES NOTHING")
core.save_settings({"photo_keep_days": "not a number"}, {})
assert json.load(open(path))["photo_keep_days"] == 14

print("\nALL GOOD")
