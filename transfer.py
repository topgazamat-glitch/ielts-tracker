"""Move real data - students, homework, submissions and photos - between servers.

    python3 transfer.py export            writes transfer.json

Then upload that file on the running dashboard at /import. The file contains
student names and their photographs, so it is never committed to git.

Importing is a merge, not a wipe: anything already present is matched and left
alone, so running it twice changes nothing.
"""
import base64
import json
import os
import sys

import core

PATH = os.path.join(core.ROOT, "transfer.json")
TABLES_WITH_PHOTOS = True


def export():
    db = core.connect()
    data = {"groups": [], "students": [], "assignments": [], "submissions": [],
            "word_lists": [], "questions": []}

    for g in db.execute("SELECT * FROM groups"):
        data["groups"].append({"name": g["name"], "join_code": g["join_code"]})

    gname = {g["id"]: g["name"] for g in db.execute("SELECT * FROM groups")}

    for s in db.execute("SELECT * FROM students"):
        data["students"].append({
            "telegram_id": s["telegram_id"], "name": s["name"],
            "group": gname.get(s["group_id"]), "lang": s["lang"],
            "created_at": s["created_at"], "active": s["active"], "token": s["token"],
        })

    for a in db.execute("SELECT * FROM assignments"):
        data["assignments"].append({
            "group": gname.get(a["group_id"]), "title": a["title"],
            "task_type": a["task_type"], "due_at": a["due_at"],
            "created_at": a["created_at"], "closed": a["closed"],
            "published": a["published"],
        })

    for sub in db.execute("SELECT * FROM submissions"):
        st = db.execute("SELECT telegram_id FROM students WHERE id=?",
                        (sub["student_id"],)).fetchone()
        a = db.execute("SELECT * FROM assignments WHERE id=?",
                       (sub["assignment_id"],)).fetchone() if sub["assignment_id"] else None
        files = []
        for f in db.execute("SELECT * FROM files WHERE submission_id=? ORDER BY ord",
                            (sub["id"],)):
            path = os.path.join(core.UPLOAD_DIR, f["filename"])
            blob = None
            if TABLES_WITH_PHOTOS and os.path.exists(path):
                with open(path, "rb") as fh:
                    blob = base64.b64encode(fh.read()).decode()
            files.append({"filename": f["filename"], "telegram_file_id": f["telegram_file_id"],
                          "width": f["width"], "height": f["height"], "ord": f["ord"],
                          "data": blob})
        tags = [r["label"] for r in db.execute(
            "SELECT label FROM tags JOIN submission_tags ON tags.id=tag_id"
            " WHERE submission_id=?", (sub["id"],))]
        data["submissions"].append({
            "student_telegram_id": st["telegram_id"] if st else None,
            "assignment_title": a["title"] if a else None,
            "assignment_due": a["due_at"] if a else None,
            "assignment_group": gname.get(a["group_id"]) if a else None,
            "created_at": sub["created_at"], "status": sub["status"],
            "score": sub["score"], "note": sub["note"], "graded_at": sub["graded_at"],
            "late": sub["late"], "kind": sub["kind"], "files": files, "tags": tags,
        })

    for wl in db.execute("SELECT * FROM word_lists"):
        data["word_lists"].append({
            "title": wl["title"], "source": wl["source"], "unit": wl["unit"],
            "group": gname.get(wl["group_id"]),
            "words": [{"term": w["term"], "translation": w["translation"],
                       "example": w["example"]}
                      for w in db.execute("SELECT * FROM words WHERE list_id=? ORDER BY ord",
                                          (wl["id"],))],
        })

    with open(PATH, "w") as fh:
        json.dump(data, fh, ensure_ascii=False)
    return data


def import_all(db, data):
    """Merge into whatever is already there. Safe to run more than once."""
    added = {"groups": 0, "students": 0, "assignments": 0, "submissions": 0,
             "photos": 0, "word_lists": 0}

    gid = {}
    for g in data.get("groups", []):
        row = db.execute("SELECT id FROM groups WHERE join_code=? OR name=?",
                         (g["join_code"], g["name"])).fetchone()
        if row:
            gid[g["name"]] = row["id"]
        else:
            gid[g["name"]] = db.execute(
                "INSERT INTO groups (name, join_code, created_at) VALUES (?,?,?)",
                (g["name"], g["join_code"], core.iso(core.now()))).lastrowid
            added["groups"] += 1

    sid = {}
    for s in data.get("students", []):
        row = db.execute("SELECT id FROM students WHERE telegram_id=?",
                         (s["telegram_id"],)).fetchone()
        if row:
            sid[s["telegram_id"]] = row["id"]
            continue
        sid[s["telegram_id"]] = db.execute(
            "INSERT INTO students (telegram_id, name, group_id, lang, created_at,"
            " active, token) VALUES (?,?,?,?,?,?,?)",
            (s["telegram_id"], s["name"], gid.get(s["group"]), s["lang"],
             s["created_at"], s.get("active", 1), s.get("token"))).lastrowid
        added["students"] += 1

    aid = {}
    for a in data.get("assignments", []):
        key = (a["group"], a["title"], a["due_at"])
        row = db.execute(
            "SELECT id FROM assignments WHERE group_id=? AND title=?"
            " AND (due_at IS ? OR due_at=?)",
            (gid.get(a["group"]), a["title"], a["due_at"], a["due_at"])).fetchone()
        if row:
            aid[key] = row["id"]
            continue
        aid[key] = db.execute(
            "INSERT INTO assignments (group_id, title, task_type, due_at, created_at,"
            " closed, published) VALUES (?,?,?,?,?,?,?)",
            (gid.get(a["group"]), a["title"], a["task_type"], a["due_at"],
             a["created_at"], a["closed"], a["published"])).lastrowid
        added["assignments"] += 1

    for sub in data.get("submissions", []):
        student = sid.get(sub["student_telegram_id"])
        if not student:
            continue
        key = (sub["assignment_group"], sub["assignment_title"], sub["assignment_due"])
        assignment = aid.get(key)
        if db.execute("SELECT id FROM submissions WHERE student_id=? AND created_at=?",
                      (student, sub["created_at"])).fetchone():
            continue
        new_id = db.execute(
            "INSERT INTO submissions (student_id, assignment_id, created_at, status,"
            " score, note, graded_at, late, kind) VALUES (?,?,?,?,?,?,?,?,?)",
            (student, assignment, sub["created_at"], sub["status"], sub["score"],
             sub["note"], sub["graded_at"], sub.get("late", 0),
             sub.get("kind", "photo"))).lastrowid
        added["submissions"] += 1
        for f in sub.get("files", []):
            db.execute(
                "INSERT INTO files (submission_id, filename, telegram_file_id, width,"
                " height, ord) VALUES (?,?,?,?,?,?)",
                (new_id, f["filename"], f["telegram_file_id"], f["width"],
                 f["height"], f["ord"]))
            if f.get("data"):
                path = os.path.join(core.UPLOAD_DIR, f["filename"])
                if not os.path.exists(path):
                    with open(path, "wb") as fh:
                        fh.write(base64.b64decode(f["data"]))
                    added["photos"] += 1
        for label in sub.get("tags", []):
            t = db.execute("SELECT id FROM tags WHERE label=?", (label,)).fetchone()
            if t:
                db.execute("INSERT OR IGNORE INTO submission_tags (submission_id, tag_id)"
                           " VALUES (?,?)", (new_id, t["id"]))

    for wl in data.get("word_lists", []):
        if db.execute("SELECT id FROM word_lists WHERE title=?", (wl["title"],)).fetchone():
            continue
        lid = db.execute(
            "INSERT INTO word_lists (group_id, title, created_at, source, unit)"
            " VALUES (?,?,?,?,?)",
            (gid.get(wl.get("group")), wl["title"], core.iso(core.now()),
             wl.get("source"), wl.get("unit"))).lastrowid
        for i, w in enumerate(wl.get("words", [])):
            db.execute("INSERT INTO words (list_id, term, translation, example, ord)"
                       " VALUES (?,?,?,?,?)",
                       (lid, w["term"], w["translation"], w.get("example"), i))
        added["word_lists"] += 1

    db.commit()
    return added


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "export":
        d = export()
        size = os.path.getsize(PATH) / 1024 / 1024
        print("transfer.json written: %.1f MB" % size)
        for k, v in d.items():
            print("  %s: %d" % (k, len(v)))
    else:
        print(__doc__)
