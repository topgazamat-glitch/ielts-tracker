"""The workbook's units on a shelf of their own: "Workbook handouts".

On the students' Handouts page the course booklets come first, then the
workbook's units - the ones of the class's level open to it as practice, and
any set to the class. A workbook unit never locks and is never locked, and it
is never on the booklets' shelf.

Run me with:  python3 run_tests.py workbook_shelf
"""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None); os.environ["TEACHER_PASSWORD"] = "pw"
import core, server

core.init_db(); db = core.connect()
now = core.iso(core.now())
fails, checks = [], 0


def check(what, cond):
    global checks
    checks += 1
    print(("  ok  " if cond else "  FAIL") + "  " + what)
    if not cond:
        fails.append(what)


pre = db.execute("SELECT id FROM levels WHERE name='Pre-Intermediate'").fetchone()["id"]
inter = db.execute("SELECT id FROM levels WHERE name='Intermediate'").fetchone()["id"]
g = db.execute("INSERT INTO groups (name, join_code, created_at, level_id) VALUES ('214','A',?,?)",
               (now, pre)).lastrowid
sid = core.add_student(db, "Anvar", g)
student = db.execute("SELECT * FROM students WHERE id=?", (sid,)).fetchone()
TEAL = core.BOOKLET_TEAL
LAYOUT = ('<div class="booklet"><table class="bk"><tr><td style="background:#%s"><p><span>1</span></p></td>'
          '<td><p><span>Part · one</span></p></td></tr></table>'
          '<p><span style="font-weight:700;color:#%s;font-size:12pt">1.1  </span><span>Which?</span></p>'
          '<p data-item="1.1:1"><span>1  </span><span><input class="bk-blank" data-q="1" style="width:60px">'
          '</span></p></div>' % (TEAL, TEAL))


def shelf_item(level, number, title, series=None, published=1):
    tid = core.load_test(db, {"level": level, "number": number, "title": title, "kind": "handout",
                              "layout": LAYOUT, "passages": {},
                              "questions": [{"num": 1, "kind": "typed", "prompt": "1.1 1", "answer": "a",
                                             "options": []}]})
    db.execute("UPDATE dtests SET published=?, series=? WHERE id=?", (published, series, tid))
    db.commit()
    return tid


book = shelf_item("Pre-Intermediate", 1, "Unit 1A & 1C — Communication")
wb_ac = shelf_item("Pre-Intermediate", 1, "Workbook · Unit 1A & 1C — Communication", "workbook")
wb_bd = shelf_item("Pre-Intermediate", 1, "Workbook · Unit 1B & 1D — Communication", "workbook")
wb_2 = shelf_item("Pre-Intermediate", 2, "Workbook · Unit 2A & 2C — Travel", "workbook", published=0)
wb_other = shelf_item("Intermediate", 1, "Workbook · Unit 1A & 1C — Talk", "workbook")

print("1. WHAT IS ON WHICH SHELF")
mine = [b["id"] for b in core.workbook_shelf(db, student)]
check("the workbook shelf has the level's open units, in the order of the course", mine == [wb_ac, wb_bd])
check("not a unit kept back, nor another level's", wb_2 not in mine and wb_other not in mine)
check("the booklets' shelf has no workbook unit", [b["id"] for b, _f in core.handout_shelf(db, student)] == [book])
db.execute("INSERT INTO assignments (group_id, title, due_at, created_at, published, test_id)"
           " VALUES (?,?,?,?,1,?)", (g, "Workbook unit 2 A&C", now, now, wb_2))
db.commit()
check("a unit set to the class joins its shelf, even one kept back",
      [b["id"] for b in core.workbook_shelf(db, student)] == [wb_ac, wb_bd, wb_2])
check("a workbook unit is never locked", core.handout_blocked_by(db, wb_2, student) is None)

print("\n2. ON THE PAGE")
page = server.handout_shelf_page(db, student, student["token"], "/s/x?tab=handouts")
check("the booklets first, then the shelf called Workbook handouts",
      0 < page.index("Unit 1A &amp; 1C — Communication") < page.index("Workbook handouts")
      < page.index("Workbook · Unit 1B &amp; 1D"))
check("the unit set as homework says so on its card", "Homework · " in page.split("Workbook handouts", 1)[1])
db.execute("DELETE FROM dtests WHERE id=?", (book,)); db.commit()
page = server.handout_shelf_page(db, student, student["token"], "/s/x?tab=handouts")
check("with no booklet open, the workbook shelf is still there", "Workbook handouts" in page
      and "Nothing here yet" not in page)

print()
print("workbook_shelf: %d checks, %d failed" % (checks, len(fails)))
sys.exit(1 if fails else 0)
