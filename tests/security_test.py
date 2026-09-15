"""The locks: who can reach what, and what a leaked link costs.

Run me with:  python3 run_tests.py security
"""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None)
os.environ.pop("TEACHER_PASSWORD", None)
import core
core.init_db(); db = core.connect()
g = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('G','G',?)",
               (core.iso(core.now()),)).lastrowid
sid = db.execute("INSERT INTO students (name, group_id, active, created_at)"
                 " VALUES ('Nilufar',?,1,?)", (g, core.iso(core.now()))).lastrowid
db.commit()

print("1. A STUDENT LINK IS LONG ENOUGH TO BE UNGUESSABLE")
tok = core.student_token(db, sid)
print("   %d characters" % len(tok))
assert len(tok) >= 20

print("\n2. A SHARED LINK CAN BE TAKEN BACK")
fresh = core.reissue_token(db, sid)
print("   new link differs:", fresh != tok)
assert fresh != tok
print("   the old one is dead:", core.student_by_token(db, tok) is None)
assert core.student_by_token(db, tok) is None
print("   the new one works:", core.student_by_token(db, fresh)["name"])
assert core.student_by_token(db, fresh)["id"] == sid

print("\n3. THE PASSWORD IS MEASURED, NEVER PRINTED")
worry = core.password_worry({"teacher_password": "short"})
print("  ", worry)
assert "short" not in worry, "the password itself must never appear"
assert "5 characters" in worry
assert core.password_worry({"teacher_password": "changeme"})
long_one = {"teacher_password": "correct horse battery staple"}
os.environ["TEACHER_PASSWORD"] = "x"
print("   a long one kept in the host's settings:",
      repr(core.password_worry(long_one)))
assert core.password_worry(long_one) == ""
os.environ.pop("TEACHER_PASSWORD")

print("\n4. THE TELEGRAM BACKUP CAN BE TURNED OFF")
import jobs
made = jobs.backup()
off = jobs.send_backup_off_the_volume(db, {"backup_to_telegram": False}, made)
print("  ", off)
assert "off" in off

print("\nALL GOOD")
