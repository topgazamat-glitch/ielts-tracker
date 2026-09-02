"""Fill the database with fake data so the charts have something to show.

    python3 seed_demo.py          # add a demo group to what is already there
    python3 seed_demo.py --reset  # wipe everything, then add the demo group
    python3 seed_demo.py --empty  # wipe everything and add nothing (real start)
"""
import random
import sys
from datetime import timedelta

import core

if "--reset" in sys.argv or "--empty" in sys.argv:
    import os
    for f in ("app.db", "app.db-wal", "app.db-shm"):
        p = os.path.join(core.DATA_DIR, f)
        if os.path.exists(p):
            os.remove(p)
    for f in os.listdir(core.UPLOAD_DIR):
        if f.endswith(".jpg"):
            os.remove(os.path.join(core.UPLOAD_DIR, f))

db = core.init_db()
if "--empty" in sys.argv:
    print("Database wiped. Starting clean - create your first group in the dashboard.")
    raise SystemExit
random.seed(7)
now = core.now()

code = core.new_join_code(db)
gid = db.execute(
    "INSERT INTO groups (name, join_code, created_at) VALUES (?,?,?)",
    ("Demo · Mon/Wed 18:00", code, core.iso(now - timedelta(days=60))),
).lastrowid

names = ["Aziza K.", "Bekzod T.", "Dilnoza R.", "Jasur M.", "Kamola S.", "Nodir A."]
students = [
    db.execute(
        "INSERT INTO students (telegram_id, name, group_id, lang, created_at) VALUES (?,?,?,?,?)",
        (900000 + i, n, gid, ["en", "ru", "uz"][i % 3], core.iso(now - timedelta(days=55))),
    ).lastrowid
    for i, n in enumerate(names)
]

titles = ["Task 2 – Education", "Task 1 – Bar chart", "Task 2 – Technology",
          "Task 1 – Process", "Task 2 – Environment", "Task 2 – Work/life"]
assignments = []
for i, ti in enumerate(titles):
    due = now - timedelta(days=42 - i * 7)
    assignments.append(db.execute(
        "INSERT INTO assignments (group_id, title, task_type, due_at, created_at,"
        " closed, published) VALUES (?,?,?,?,?,?,1)",
        (gid, ti, "task1" if "Task 1" in ti else "task2", core.iso(due),
         core.iso(due - timedelta(days=6)), 1 if i < len(titles) - 1 else 0),
    ).lastrowid)

tag_ids = [r["id"] for r in db.execute("SELECT id FROM tags").fetchall()]
for si, sid in enumerate(students):
    base = random.uniform(4.5, 7.5)
    drift = random.uniform(-0.35, 0.4)
    for ai, aid in enumerate(assignments):
        if random.random() < (0.32 if si == 3 else 0.1):
            continue  # a genuine miss, deliberately left unscored
        created = core.parse(db.execute(
            "SELECT due_at FROM assignments WHERE id=?", (aid,)).fetchone()["due_at"])
        graded = ai < len(assignments) - 1
        score = max(1, min(10, round(base + drift * ai + random.uniform(-0.8, 0.8))))
        sub = db.execute(
            "INSERT INTO submissions (student_id, assignment_id, created_at, status, score,"
            " note, graded_at) VALUES (?,?,?,?,?,?,?)",
            (sid, aid, core.iso(created - timedelta(hours=5)),
             "graded" if graded else "pending", score if graded else None,
             None, core.iso(created) if graded else None),
        ).lastrowid
        if graded and random.random() < 0.6:
            db.execute("INSERT OR IGNORE INTO submission_tags (submission_id, tag_id)"
                       " VALUES (?,?)", (sub, random.choice(tag_ids)))

db.commit()
print(f"Demo group created. Join code: {code}")
print(f"{len(students)} students, {len(assignments)} assignments.")
