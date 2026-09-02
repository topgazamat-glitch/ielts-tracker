"""Carry classes and word lists to a new server without losing invite links.

`python3 bootstrap.py export` writes bootstrap.json (groups with their join
codes, and vocabulary). `app.py` imports it automatically the first time it
starts against an empty database, so the links you already gave students keep
working after a move.

Deliberately contains no personal data: no students, no submissions, no scores.
"""
import json
import os
import sys

import core

PATH = os.path.join(core.ROOT, "bootstrap.json")


def export():
    db = core.connect()
    data = {
        "groups": [
            {"name": g["name"], "join_code": g["join_code"]}
            for g in db.execute("SELECT * FROM groups WHERE archived=0 ORDER BY id")
        ],
        "word_lists": [],
    }
    for wl in db.execute("SELECT * FROM word_lists WHERE active=1"):
        g = db.execute("SELECT name FROM groups WHERE id=?", (wl["group_id"],)).fetchone()
        data["word_lists"].append({
            "title": wl["title"],
            "source": wl["source"],
            "unit": wl["unit"],
            "group": g["name"] if g else None,
            "words": [
                {"term": w["term"], "translation": w["translation"], "example": w["example"]}
                for w in db.execute(
                    "SELECT * FROM words WHERE list_id=? ORDER BY ord", (wl["id"],))
            ],
        })
    with open(PATH, "w") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    words = sum(len(l["words"]) for l in data["word_lists"])
    return len(data["groups"]), len(data["word_lists"]), words


def load_if_empty(db):
    """Import once, into a database that has no groups yet."""
    if not os.path.exists(PATH):
        return False
    if db.execute("SELECT COUNT(*) c FROM groups").fetchone()["c"]:
        return False
    with open(PATH) as fh:
        data = json.load(fh)
    ids = {}
    for g in data.get("groups", []):
        ids[g["name"]] = db.execute(
            "INSERT INTO groups (name, join_code, created_at) VALUES (?,?,?)",
            (g["name"], g["join_code"], core.iso(core.now())),
        ).lastrowid
    for wl in data.get("word_lists", []):
        lid = db.execute(
            "INSERT INTO word_lists (group_id, title, created_at, source, unit)"
            " VALUES (?,?,?,?,?)",
            (ids.get(wl.get("group")), wl["title"], core.iso(core.now()),
             wl.get("source"), wl.get("unit")),
        ).lastrowid
        for i, w in enumerate(wl.get("words", [])):
            db.execute(
                "INSERT INTO words (list_id, term, translation, example, ord)"
                " VALUES (?,?,?,?,?)",
                (lid, w["term"], w["translation"], w.get("example"), i),
            )
    db.commit()
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "export":
        g, l, w = export()
        print(f"bootstrap.json written: {g} group(s), {l} word list(s), {w} word(s)")
    else:
        print(__doc__)
