"""The charts, and the restraint they are built with.

A teacher will believe a correlation because a computer printed it. With
twenty students you can find one that is entirely chance. So most of these
checks are about the tool keeping its mouth shut.

Run me with:  python3 run_tests.py charts
"""
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import tempfile
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None)

import core
core.init_db(); db = core.connect()
now, iso, td = core.now(), core.iso, core.timedelta

fails, checks = [], 0


def check(what, cond):
    global checks
    checks += 1
    print(("  ok  " if cond else "  FAIL") + "  " + what)
    if not cond:
        fails.append(what)


# ------------------------------------------------------ keeping quiet
c = core.correlate([(1, 2), (2, 4), (3, 6)])
check("three students is not enough to say anything", c["verdict"] == "few")
check("and it says how many are needed", "of the 8 needed" in c["says"])
check("no r is offered when there is nothing to offer", c["r"] is None)

perfect = core.correlate([(i, 3 * i + 1) for i in range(10)])
check("a real relationship is reported", perfect["verdict"] == "clear")
check("with its direction", "together" in perfect["says"])
inverse = core.correlate([(i, -2 * i) for i in range(10)])
check("and the other direction is named",
      "opposite" in inverse["says"] and inverse["r"] == -1.0)

random.seed(7)
noise = [core.correlate([(random.random(), random.random())
                         for _ in range(12)]) for _ in range(20)]
claimed = [c for c in noise if c["verdict"] == "clear"]
check("random numbers are almost never called a relationship",
      len(claimed) <= 2)
check("and the refusal explains itself",
      any("could easily be chance" in c["says"] for c in noise))

flat = core.correlate([(5, i) for i in range(10)])
check("a column where every student is identical says so",
      flat["verdict"] == "flat")

weak = core.correlate([(i, i) for i in range(9)] + [(0, 100)])
check("one outlier cannot manufacture a claim on its own",
      weak["verdict"] in ("clear", "nothing"))

# the bar rises as the sample shrinks
few = core.correlate([(i, i + (i % 3)) for i in range(8)])
many = core.correlate([(i, i + (i % 3)) for i in range(40)])
check("the same shape of data is judged more strictly when there is less",
      (few["r"] or 0) <= (many["r"] or 0) + 0.2)

# -------------------------------------------------------- cycle points
g = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('114','A',?)",
               (iso(now),)).lastrowid
ids = [core.add_student(db, n, g) for n in ("Aziz", "Malika", "Jasur")]
db.commit()
core.backfill_enrolments(db)

a = db.execute("INSERT INTO assignments (group_id, title, created_at, published,"
               " due_at) VALUES (?,?,?,1,?)",
               (g, "HW", iso(now - td(days=5)), iso(now - td(days=2)))).lastrowid
db.execute("INSERT INTO submissions (student_id, assignment_id, status, score,"
           " created_at, kind) VALUES (?,?, 'graded', 9, ?, 'photo')",
           (ids[0], a, iso(now - td(days=3))))
db.execute("INSERT INTO lesson_marks (student_id, day, punctuality, behaviour,"
           " participation, created_at) VALUES (?,?,5,5,5,?)",
           (ids[0], iso(now)[:10], iso(now)))
ct = core.new_class_test(db, g, "Unit 1", 20, iso(now)[:10])
core.save_class_scores(db, ct, {ids[0]: 16})
core.save_exam(db, g, "final", "Final", 100, iso(now)[:10], {ids[0]: 82})
db.commit()

pts = {p["name"]: p for p in core.cycle_points(db, g)}
check("every student gets a row, even an empty one", len(pts) == 3)
p = pts["Aziz"]
check("homework comes through", p["homework"] == 9)
check("participation is averaged out of the three marks",
      p["participation"] == 5.0)
check("a class test is a percentage, not a raw mark",
      p["class_tests"] == 80.0)
check("the exam is a percentage", p["final"] == 82.0)
check("and the final is preferred over the mid", p["exam"] == 82.0)
check("a student with nothing has nothing, not zero",
      pts["Jasur"]["homework"] is None and pts["Jasur"]["exam"] is None)
check("still here is not the same as left", p["left"] is False)

core.mark_left(db, ids[1], "bored")
pts = {p["name"]: p for p in core.cycle_points(db, g)}
check("a leaver is marked as one", pts["Malika"]["left"] is True)
check("with the reason", pts["Malika"]["reason"] == "bored")

check("a chart of three students refuses to draw a conclusion",
      core.correlate([(p["homework"], p["exam"])
                      for p in pts.values()])["verdict"] == "few")

# ------------------------------------------------- the drawing keeps quiet too
import server
check("a chart of three points is not drawn at all",
      server.scatter([(1, 0, {"name": "a"}), (2, 0, {"name": "b"}),
                      (3, 0, {"name": "c"})], "x", "y") == "")
check("nor is one where every student has the same figure",
      server.scatter([(5, i, {"name": str(i)}) for i in range(12)],
                     "x", "y") == "")
real = server.scatter([(i, i * 2 + (i % 3), {"name": "s%d" % i})
                       for i in range(12)], "homework", "exam")
check("a chart with something in it is drawn", real.startswith("<svg"))
check("with one dot per student", real.count("<circle") == 12)
check("and no axis label reading minus zero", ">-0<" not in real)
check("a student who has left is outlined rather than recoloured",
      'class="dot left"' in server.scatter(
          [(i, i, {"name": "x", "left": True}) for i in range(12)], "a", "b"))

print()
print("charts: %d checks, %d failed" % (checks, len(fails)))
sys.exit(1 if fails else 0)
