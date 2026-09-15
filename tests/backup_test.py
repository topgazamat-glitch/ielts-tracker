"""The backup can leave the server.

Run me with:  python3 run_tests.py backup
"""
import gzip
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None)
import core, jobs
core.init_db(); db = core.connect()
db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('G','G',?)",
           (core.iso(core.now()),))
db.commit()

print("1. A BACKUP IS MADE")
made = jobs.backup()
print("   ", os.path.basename(made), os.path.getsize(made), "bytes")
assert os.path.exists(made)
assert os.path.dirname(made) == os.path.join(core.DATA_DIR, "backups")

print("\n2. IT IS A REAL DATABASE, NOT A HALF-WRITTEN FILE")
import sqlite3
copy = sqlite3.connect(made)
n = copy.execute("SELECT COUNT(*) FROM groups").fetchone()[0]
copy.close()
print("   groups inside the copy:", n)
assert n == 1

print("\n3. WITH NOBODY REGISTERED, IT SAYS SO RATHER THAN FAILING")
cfg = dict(core.load_config())
cfg["telegram_token"] = ""
out = jobs.send_backup_off_the_volume(db, cfg, made)
print("   ", out)
assert out == "nobody to send it to"

print("\n4. IT COMPRESSES BEFORE SENDING")
gz = made + ".gz"
with open(made, "rb") as src, gzip.open(gz, "wb") as dst:
    dst.write(src.read())
small = os.path.getsize(gz) < os.path.getsize(made)
print("   %d -> %d bytes, smaller: %s"
      % (os.path.getsize(made), os.path.getsize(gz), small))
assert small
os.remove(gz)

print("\nALL GOOD")
