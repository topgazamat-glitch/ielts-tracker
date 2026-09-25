"""The KPI ladder: which level a teacher is on, and what each one pays.

This decides money, so the awkward cases matter more than the ordinary one:
a teacher who meets level five's requirements but not level four's, a
certificate that blocks everything above it, and thresholds the centre
changes next year.

Run me with:  python3 run_tests.py kpi
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import tempfile
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None)

import core
core.init_db(); db = core.connect()

fails, checks = [], 0


def check(what, cond):
    global checks
    checks += 1
    print(("  ok  " if cond else "  FAIL") + "  " + what)
    if not cond:
        fails.append(what)


def at(**kw):
    kw.setdefault("students", 20)
    return core.kpi_standing(db, **kw)


levels = core.kpi_levels(db)
check("six levels are seeded", len(levels) == 6)
check("the rates are the centre's",
      [l["per_student"] for l in levels]
      == [180000, 200000, 220000, 240000, 280000, 310000])
check("level one asks for nothing",
      levels[0]["ielts_min"] is None and not levels[0]["celta"])
check("level two is flagged as a guess", "GUESS" in (levels[1]["note"] or ""))

# --------------------------------------------------------------- climbing
s = at(ielts=None, celta=0, avg=None, retention_pct=None)
check("a teacher with nothing recorded is on level one", s["level"] == 1)
check("and is paid the level one rate", s["here"]["pay"] == 180000 * 20)

s = at(ielts=8.0, celta=0, avg=70, retention_pct=70)
check("IELTS 8 with 70 and 70 reaches level three", s["level"] == 3)
check("level four is the next rung", s["next"]["level"] == 4)
check("and what it needs is the certificate",
      [m[0] for m in s["next"]["missing"]] == ["celta"])

s = at(ielts=9.0, celta=0, avg=90, retention_pct=95)
check("no certificate stops a band 9 teacher at level three", s["level"] == 3)
s = at(ielts=9.0, celta=1, avg=90, retention_pct=95)
check("with the certificate the same teacher reaches level six",
      s["level"] == 6)
check("and there is no rung above it", s["next"] is None)

s = at(ielts=8.0, celta=1, avg=90, retention_pct=95)
check("IELTS 8 with the certificate stops at level four", s["level"] == 4)
s = at(ielts=8.5, celta=1, avg=90, retention_pct=95)
check("8.5 reaches level five", s["level"] == 5)

# the ladder is a ladder: you cannot stand on a rung with one missing below
s = at(ielts=9.0, celta=1, avg=50, retention_pct=95)
check("a low student average holds a band 9 teacher at level one",
      s["level"] == 1)
check("but the page still shows what the higher levels would pay",
      s["levels"][5]["pay"] == 310000 * 20)
check("and marks them as not met", s["levels"][5]["met"] is False)

# 65 clears level two's (guessed) 60 but not level three's 70, which is
# exactly why level two's thresholds are worth getting right
s = at(ielts=8.0, celta=1, avg=70, retention_pct=65)
check("retention five points short of level three holds them at two",
      s["level"] == 2)
check("and the reason given is the retention",
      [m[0] for m in s["next"]["missing"]] == ["retention"])
check("the shortfall is spelled out, not just flagged",
      s["next"]["missing"][0][1:] == (70, 65))

# ------------------------------------------------------------ the money
s = at(ielts=8.0, celta=0, avg=70, retention_pct=70, students=85)
check("pay is the rate times the headcount",
      s["here"]["pay"] == 220000 * 85)
check("the next level is worth the difference",
      s["gap"] == (240000 - 220000) * 85)
check("every level is priced for the same students",
      [r["pay"] for r in s["levels"]]
      == [n * 85 for n in (180000, 200000, 220000, 240000, 280000, 310000)])

# --------------------------------------------------------- the centre moves
core.save_kpi_level(db, 3, avg_min=80)
s = at(ielts=8.0, celta=0, avg=70, retention_pct=70)
check("raising a threshold moves the teacher down", s["level"] == 2)
core.save_kpi_level(db, 3, avg_min=70)
core.save_kpi_level(db, 6, per_student=350000)
s = at(ielts=8.0, celta=0, avg=70, retention_pct=70, students=10)
check("changing a rate changes what that level would pay",
      s["levels"][5]["pay"] == 350000 * 10)
core.save_kpi_level(db, 6, per_student=310000)

# ------------------------------------------------------- reading the records
prof = core.kpi_profile(db)
check("a profile is made on demand", prof["teacher_id"] == 1)
core.save_kpi_profile(db, ielts=8.5, celta=1, students=40)
s = core.kpi_standing(db, avg=75, retention_pct=75)
check("the saved profile is used when nothing is passed in",
      s["ielts"] == 8.5 and s["celta"] == 1 and s["students"] == 40)
check("and it lands on level five", s["level"] == 5)

ins = core.kpi_inputs(db)
check("the records offer their own figures",
      set(ins) >= {"retention", "avg_final", "avg_mid", "students"})
check("an average from no exams is not reported as zero",
      ins["avg_final"] is None and ins["avg_final_n"] == 0)

check("money reads as money", core.money(18700000) == "18 700 000 so'm")

print()
print("kpi: %d checks, %d failed" % (checks, len(fails)))
sys.exit(1 if fails else 0)
