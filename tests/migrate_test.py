"""Migrate — see the assertions for what it guarantees.

Run me with:  python3 run_tests.py            (all of them)
              python3 tests/migrate_test.py   (just this one)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
FIXTURES = os.path.join(ROOT, "tests", "fixtures")

import tempfile, shutil, sqlite3
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp

import core
# build the table exactly as the earlier deploy did, without the image column
core.init_db()
db = core.connect()
db.execute("DROP TABLE IF EXISTS dquestions")
db.execute("""CREATE TABLE dquestions (
    id INTEGER PRIMARY KEY, test_id INTEGER NOT NULL, num INTEGER NOT NULL,
    kind TEXT NOT NULL, prompt TEXT NOT NULL, answer TEXT,
    ord INTEGER NOT NULL DEFAULT 0)""")
db.commit()
cols = {r["name"] for r in db.execute("PRAGMA table_info(dquestions)")}
print("before migrate, has image:", "image" in cols)
assert "image" not in cols
core.migrate(db)
cols = {r["name"] for r in db.execute("PRAGMA table_info(dquestions)")}
print("after  migrate, has image:", "image" in cols)
assert "image" in cols
# and an insert with an image now works, as the live upload will
tid = db.execute("INSERT INTO dtests (title, created_at) VALUES ('t',?)",
                 (core.iso(core.now()),)).lastrowid
db.execute("INSERT INTO dquestions (test_id, num, kind, prompt, answer, image, ord)"
           " VALUES (?,1,'mcq','q','A','x.png',0)", (tid,))
db.commit()
print("insert with an image column: ok")
core.migrate(db)          # must be safe to run again
print("migrate is repeatable: ok")
db.close(); shutil.rmtree(tmp)
