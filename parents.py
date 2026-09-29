"""The parents' channel: one class's week or month, in numbers and in words.

Every class gets one post: a picture of the class table, a picture of how the
last weeks went, and a written report in Uzbek and then in Russian. The
numbers are the league's own - the same homework marks and lesson marks the
students see on their Class page - cut to the week or the month, so what a
parent reads and what their child says agree.

The pictures are drawn by card.py; the teacher's page and the sending live in
server.py; this file only works the figures out and writes them down.
"""
from datetime import datetime, timedelta, timezone

import core

UZ_MONTHS = ["yanvar", "fevral", "mart", "aprel", "may", "iyun", "iyul", "avgust",
             "sentabr", "oktabr", "noyabr", "dekabr"]
RU_MONTHS = ["январь", "февраль", "март", "апрель", "май", "июнь", "июль", "август",
             "сентябрь", "октябрь", "ноябрь", "декабрь"]
RU_OF = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа",
         "сентября", "октября", "ноября", "декабря"]

PERIODS = [("week", "This week"), ("lastweek", "Last week"),
           ("month", "This month"), ("lastmonth", "Last month")]


# ------------------------------------------------ the stretch of time

def _utc(day, off):
    """Local midnight at the start of `day`, as the UTC stamp the site stores."""
    return datetime(day.year, day.month, day.day, tzinfo=timezone.utc) - timedelta(hours=off)


def period(kind, cfg=None, at=None):
    """The week or month a report is about, in the teacher's timezone.

    Weeks run Monday to Sunday. 'week' and 'month' are the ones running now,
    counted up to this moment; 'lastweek' and 'lastmonth' are the whole ones
    before. Returns lo/hi as stored stamps, the first and last day, a key
    for remembering it was sent, and the one before it for comparing.
    """
    cfg = cfg or core.load_config()
    off = cfg["timezone_offset_hours"]
    at = at or core.now()
    today = (at + timedelta(hours=off)).date()
    if kind in ("week", "lastweek"):
        first = today - timedelta(days=today.weekday())
        if kind == "lastweek":
            first -= timedelta(days=7)
        end = first + timedelta(days=7)
        before = (first - timedelta(days=7), first)
        key = "W" + first.strftime("%G-%V")
    else:
        first = today.replace(day=1)
        if kind == "lastmonth":
            first = (first - timedelta(days=1)).replace(day=1)
        end = (first + timedelta(days=32)).replace(day=1)
        start_before = (first - timedelta(days=1)).replace(day=1)
        before = (start_before, first)
        key = "M" + first.strftime("%Y-%m")
    hi = min(_utc(end, off), at)
    return {"kind": kind, "monthly": kind in ("month", "lastmonth"),
            "lo": core.iso(_utc(first, off)), "hi": core.iso(hi),
            "first": first, "last": min(end - timedelta(days=1), today),
            "key": key,
            "before": {"lo": core.iso(_utc(before[0], off)),
                       "hi": core.iso(_utc(before[1], off))}}


def weeks_back(p, n, cfg=None):
    """The last n weeks up to the end of this period, oldest first: a month
    shows its own weeks, a week shows itself and the three before it."""
    cfg = cfg or core.load_config()
    off = cfg["timezone_offset_hours"]
    last = p["last"]
    monday = last - timedelta(days=last.weekday())
    out = []
    for i in range(n - 1, -1, -1):
        first = monday - timedelta(days=7 * i)
        if p["monthly"] and first + timedelta(days=6) < p["first"]:
            continue                       # a week wholly before the month
        out.append({"first": first, "last": first + timedelta(days=6),
                    "lo": core.iso(_utc(first, off)),
                    "hi": core.iso(min(_utc(first + timedelta(days=7), off), core.now()))})
    return out


def span_uz(first, last):
    if first.month == last.month:
        return ("%d-%s" % (first.day, UZ_MONTHS[first.month - 1]) if first == last
                else "%d–%d-%s" % (first.day, last.day, UZ_MONTHS[first.month - 1]))
    return "%d-%s – %d-%s" % (first.day, UZ_MONTHS[first.month - 1],
                              last.day, UZ_MONTHS[last.month - 1])


def span_ru(first, last):
    if first.month == last.month:
        return ("%d %s" % (first.day, RU_OF[first.month - 1]) if first == last
                else "%d–%d %s" % (first.day, last.day, RU_OF[first.month - 1]))
    return "%d %s – %d %s" % (first.day, RU_OF[first.month - 1],
                              last.day, RU_OF[last.month - 1])


def short_days(first, last):
    """'22.09–28.09' - for the pictures, which both languages read."""
    return "%s–%s" % (first.strftime("%d.%m"), last.strftime("%d.%m"))


# ------------------------------------------------ the figures

def _mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def student_period(db, st, lo, hi, cfg):
    """One student over [lo, hi): what the league would have counted."""
    scores, late, missing, waiting, _pending, batches = core.homework_marks(db, st, lo, hi, [])
    set_n = len(scores) + waiting
    # the league scores a missing or late piece as a nought; a parent wants
    # the marks of the work that was handed in, and the misses said apart
    marks = sorted(scores)
    drop = missing + late
    while drop and marks and marks[0] == 0:
        marks.pop(0)
        drop -= 1
    homework_points = sum(sum(m) / len(m) / 10.0 * core.HOMEWORK_PER_SET
                          for m in batches.values())
    lessons = [((r["punctuality"] or 0) + (r["behaviour"] or 0) + (r["participation"] or 0)) / 15.0
               for r in db.execute(
                   "SELECT punctuality, behaviour, participation FROM lesson_marks"
                   " WHERE student_id=? AND day >= ? AND day < ?",
                   (st["id"], core.local_day(core.parse(lo), cfg), core.local_day(core.parse(hi), cfg)))]
    # a lesson is worth up to two points: its three marks out of fifteen
    conduct_points = sum(v * core.CONDUCT_PER_LESSON for v in lessons)
    words = db.execute(
        "SELECT COUNT(*) FROM word_progress WHERE student_id=? AND streak >= 3"
        " AND last_seen >= ? AND last_seen < ?", (st["id"], lo, hi)).fetchone()[0]
    parts = db.execute(
        "SELECT COUNT(*) FROM dparts p JOIN dattempts a ON a.id = p.attempt_id"
        " WHERE a.student_id=? AND p.checked_at >= ? AND p.checked_at < ?",
        (st["id"], lo, hi)).fetchone()[0]
    return {"student": st, "set": set_n, "done": set_n - missing, "late": late,
            "missing": missing, "waiting": waiting,
            "average": round(_mean(marks), 1) if marks else None,
            "lessons": len(lessons),
            "conduct": round(100 * _mean(lessons)) if lessons else None,
            "words": words, "parts": parts,
            "gained": round(homework_points + conduct_points, 1)}


def class_report(db, group_id, p, cfg=None):
    """Everything one class's post says, for period p (from period())."""
    cfg = cfg or core.load_config()
    g = db.execute("SELECT * FROM groups WHERE id=?", (group_id,)).fetchone()
    students = db.execute("SELECT * FROM students WHERE group_id=? AND active=1 ORDER BY name",
                          (group_id,)).fetchall()
    rows = [student_period(db, st, p["lo"], p["hi"], cfg) for st in students]
    before = {r["student"]["id"]: r for r in
              (student_period(db, st, p["before"]["lo"], p["before"]["hi"], cfg) for st in students)}

    # the class's place in the league: the table the students see
    champ = core.championship(db, cfg)
    league = {}
    if champ["started"]:
        for r in core.scope_standing(champ, group_id)["rows"]:
            league[r["student"]["id"]] = r
    for r in rows:
        lr = league.get(r["student"]["id"])
        r["rank"] = lr["rank"] if lr else None
        r["season"] = lr["total"] if lr else None
        r["before"] = before.get(r["student"]["id"])
    if league:
        rows.sort(key=lambda r: (r["rank"] is None, r["rank"] or 0, -r["gained"],
                                 r["student"]["name"]))
    else:
        # no season running: the class is ranked on this stretch alone
        rows.sort(key=lambda r: (-r["gained"], r["student"]["name"]))
        for i, r in enumerate(rows, 1):
            r["rank"] = i if r["gained"] > 0 else None

    def totals(rs):
        set_n = sum(r["set"] for r in rs)
        return {"set": set_n, "done": sum(r["done"] for r in rs),
                "done_pct": round(100 * sum(r["done"] for r in rs) / set_n) if set_n else None,
                "average": round(_mean([r["average"] for r in rs]), 1)
                if any(r["average"] is not None for r in rs) else None,
                "conduct": round(_mean([r["conduct"] for r in rs]))
                if any(r["conduct"] is not None for r in rs) else None,
                "lessons": max([r["lessons"] for r in rs] or [0]),
                "words": sum(r["words"] for r in rs)}

    # the pieces of homework whose deadline fell in the stretch
    tasks = db.execute(
        "SELECT COUNT(*) FROM assignments WHERE group_id=? AND published=1 AND in_league=1"
        " AND due_at >= ? AND due_at < ?", (group_id, p["lo"], p["hi"])).fetchone()[0]
    upcoming = db.execute(
        "SELECT title, due_at, test_id FROM assignments WHERE group_id=? AND published=1"
        " AND closed=0 AND due_at > ? ORDER BY due_at LIMIT 2",
        (group_id, core.iso(core.now()))).fetchall()
    weeks = []
    for w in weeks_back(p, 5 if p["monthly"] else 4, cfg):
        wr = [student_period(db, st, w["lo"], w["hi"], cfg) for st in students]
        weeks.append(dict(w, **totals(wr)))
    return {"group": g, "level": core.level_name(db, core.level_of(db, group_id)) or "",
            "period": p, "rows": rows, "league": bool(league),
            "totals": totals(rows), "before": totals(list(before.values())),
            "tasks": tasks, "upcoming": upcoming, "weeks": weeks,
            "made": core.now()}


# ------------------------------------------------ the words

def _n(x):
    """7.4 as the region writes it: 7,4 - and 8 not 8,0."""
    if x is None:
        return "–"
    return ("%g" % round(x, 1)).replace(".", ",")


def ru_plural(n, one, few, many):
    n = abs(int(n))
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


def highlights(rep):
    """The few things worth a sentence: the best of the stretch, the one who
    grew most, and who has work missing."""
    rows = rep["rows"]
    stars = [r for r in sorted(rows, key=lambda r: -r["gained"]) if r["gained"] > 0][:3]
    grown = None
    for r in rows:
        b = r["before"]
        if b and b["average"] is not None and r["average"] is not None:
            gain = r["average"] - b["average"]
            if gain >= 0.5 and (grown is None or gain > grown[1]):
                grown = (r, gain, b["average"])
    missing = sorted((r for r in rows if r["missing"]), key=lambda r: -r["missing"])
    return stars, grown, missing


def _names(rows, more, most=8):
    """'Kamola (2), Nodir (1)' - the count is how many pieces are missing."""
    shown = ", ".join("%s (%d)" % (r["student"]["name"], r["missing"]) for r in rows[:most])
    if len(rows) > most:
        shown += ", " + more % (len(rows) - most)
    return shown


def _upcoming_date(a, cfg):
    d = core.parse(a["due_at"]) + timedelta(hours=cfg["timezone_offset_hours"])
    return d.date()


def text_uz(rep, cfg=None):
    cfg = cfg or core.load_config()
    p, t, b = rep["period"], rep["totals"], rep["before"]
    g = rep["group"]["name"]
    when = (("%s oyi" % UZ_MONTHS[p["first"].month - 1]).capitalize() if p["monthly"]
            else "%s haftasi" % span_uz(p["first"], p["last"]))
    was = "oʻtgan oy" if p["monthly"] else "oʻtgan hafta"
    out = ["🇺🇿 %s-guruh · %s hisoboti" % (g, when), ""]
    if t["set"]:
        line = "📝 Uy vazifalari: %d ta vazifa berildi, guruh ularning %d foizini bajardi" % (
            rep["tasks"] or 1, t["done_pct"])
        if b["done_pct"] is not None:
            line += " (%s %d foiz)" % (was, b["done_pct"])
        out.append(line + ".")
    else:
        out.append("📝 Bu davrda muddati tugagan uy vazifasi boʻlmadi.")
    if t["average"] is not None:
        line = "⭐ Oʻrtacha baho: %s / 10" % _n(t["average"])
        if b["average"] is not None:
            line += " (%s %s)" % (was, _n(b["average"]))
        out.append(line + ".")
    if t["conduct"] is not None:
        out.append("🎓 Darsdagi faollik: %d foiz." % t["conduct"])
    if t["words"]:
        out.append("📚 Yangi soʻzlar: guruh %d ta soʻz yodladi." % t["words"])
    stars, grown, missing = highlights(rep)
    if stars or grown or missing:
        out.append("")
    if stars:
        out.append("🏆 %s eng yaxshilari: " % ("Oyning" if p["monthly"] else "Haftaning") + ", ".join(
            "%s (+%s ball)" % (r["student"]["name"], _n(r["gained"])) for r in stars) + ".")
    if grown:
        r, _gain, old = grown
        out.append("📈 Eng katta oʻsish: %s — oʻrtacha baho %s dan %s ga koʻtarildi." % (
            r["student"]["name"], _n(old), _n(r["average"])))
    if missing:
        out.append("⚠️ Vazifa topshirmaganlar: " + _names(missing, "va yana %d kishi") + ".")
    for a in rep["upcoming"][:1]:
        d = _upcoming_date(a, cfg)
        out.append("⏰ Keyingi muddat: %s — %s." % (span_uz(d, d), a["title"]))
    return "\n".join(out)


def text_ru(rep, cfg=None):
    cfg = cfg or core.load_config()
    p, t, b = rep["period"], rep["totals"], rep["before"]
    g = rep["group"]["name"]
    when = ("за %s" % RU_MONTHS[p["first"].month - 1] if p["monthly"]
            else "за неделю %s" % span_ru(p["first"], p["last"]))
    was = "в прошлом месяце" if p["monthly"] else "на прошлой неделе"
    out = ["🇷🇺 Группа %s · отчёт %s" % (g, when), ""]
    if t["set"]:
        line = "📝 Домашние задания: задано %d, группа выполнила %d%%" % (
            rep["tasks"] or 1, t["done_pct"])
        if b["done_pct"] is not None:
            line += " (%s %d%%)" % (was, b["done_pct"])
        out.append(line + ".")
    else:
        out.append("📝 В этот период сроков сдачи домашних заданий не было.")
    if t["average"] is not None:
        line = "⭐ Средняя оценка: %s из 10" % _n(t["average"])
        if b["average"] is not None:
            line += " (%s %s)" % (was, _n(b["average"]))
        out.append(line + ".")
    if t["conduct"] is not None:
        out.append("🎓 Работа на уроках: %d%%." % t["conduct"])
    if t["words"]:
        out.append("📚 Новые слова: группа выучила %d %s." % (
            t["words"], ru_plural(t["words"], "слово", "слова", "слов")))
    stars, grown, missing = highlights(rep)
    if stars or grown or missing:
        out.append("")
    if stars:
        out.append("🏆 Лучшие за %s: " % ("месяц" if p["monthly"] else "неделю") + ", ".join(
            "%s (+%s)" % (r["student"]["name"], _n(r["gained"])) for r in stars) + ".")
    if grown:
        r, _gain, old = grown
        out.append("📈 Самый большой рост: %s — средняя оценка выросла с %s до %s." % (
            r["student"]["name"], _n(old), _n(r["average"])))
    if missing:
        out.append("⚠️ Не сдали задания: " + _names(missing, "и ещё %d") + ".")
    for a in rep["upcoming"][:1]:
        d = _upcoming_date(a, cfg)
        out.append("⏰ Ближайший срок: %s — %s." % (span_ru(d, d), a["title"]))
    return "\n".join(out)


def post_text(rep, note="", cfg=None):
    """The written report: the teacher's own words first, if any, then Uzbek,
    then Russian - one message, well inside Telegram's 4096 letters."""
    parts = []
    if note.strip():
        parts.append("✍️ " + note.strip())
    parts += [text_uz(rep, cfg), text_ru(rep, cfg)]
    return "\n\n".join(parts)[:4000]


def caption(rep):
    p = rep["period"]
    what = "Oylik hisobot · Месячный отчёт" if p["monthly"] else "Haftalik hisobot · Недельный отчёт"
    return "%s-guruh · Группа %s\n%s · %s" % (rep["group"]["name"], rep["group"]["name"], what,
                                              short_days(p["first"], p["last"]))


# ------------------------------------------------ sending

import time

# Telegram lets a bot put about twenty messages a minute into one channel; a
# class is three (two pictures and the text), so the classes go ten seconds
# apart and a whole school stays inside the limit.
SEND_GAP = 10
ROWS_PER_PICTURE = 22
_sleep = time.sleep


def pictures(rep):
    """The class table - in pieces for a very big class - and the weeks."""
    import card
    rows = rep["rows"]
    chunks = [rows[i:i + ROWS_PER_PICTURE] for i in range(0, len(rows), ROWS_PER_PICTURE)] or [[]]
    return [card.class_table(rep, chunk) for chunk in chunks] + [card.trend(rep)]


def sent_at(db, key, group_id):
    r = db.execute("SELECT sent_at FROM notifications WHERE kind='parents_post' AND key=?",
                   ("%s:%d" % (key, group_id),)).fetchone()
    return r["sent_at"] if r else None


def sending(db):
    """How the last sending went: {started, total, done, errors, finished, ...}."""
    import json
    raw = core.meta_get(db, "parents_sending")
    try:
        return json.loads(raw) if raw else None
    except ValueError:
        return None


def busy(db):
    """Is a sending still going? One that has said nothing for a quarter of
    an hour has died with a restart, and does not block the next."""
    s = sending(db)
    return bool(s and not s.get("finished")
                and core.parse(s["touched"]) > core.now() - timedelta(minutes=15))


def send_all(token, kind, group_ids, notes, cfg=None, pause=None):
    """Post every class in group_ids to the parents' channel, one after the
    other. Runs on its own thread, on the real database, and writes how far
    it has got for the Parents page to show."""
    import json
    cfg = cfg or core.load_config()
    pause = pause or _sleep
    db = core.connect(real=True)
    try:
        chan = core.parents_channel(db)
        p = period(kind, cfg)
        status = {"kind": kind, "key": p["key"], "total": len(group_ids), "done": 0,
                  "errors": [], "started": core.iso(core.now()), "finished": None}

        def save():
            status["touched"] = core.iso(core.now())
            core.meta_set(db, "parents_sending", json.dumps(status))
        save()
        for i, gid in enumerate(group_ids):
            try:
                _post_class(db, token, chan, p, gid, notes, cfg, pause, status)
            except Exception as exc:      # one class going wrong must not stop the rest
                status["errors"].append("class %d: %s" % (gid, exc))
            status["done"] = i + 1
            save()
            if i < len(group_ids) - 1:
                pause(SEND_GAP)
        status["finished"] = core.iso(core.now())
        save()
        return status
    finally:
        db.close()


def _post_class(db, token, chan, p, gid, notes, cfg, pause, status):
    """One class's post: the pictures as an album, then the written report."""
    import bot
    rep = class_report(db, gid, p, cfg)
    res = None
    for _try in range(3):
        res = bot.send_album(token, chan["id"], pictures(rep), caption(rep))
        wait = (res.get("parameters") or {}).get("retry_after")
        if res.get("ok") or not wait:
            break
        pause(min(int(wait), 60) + 1)       # too fast: Telegram says how long to wait
    if res.get("ok"):
        pause(2)
        res = bot.send(token, chan["id"], post_text(rep, notes.get(gid, ""), cfg))
    if res.get("ok"):
        key = "%s:%d" % (p["key"], gid)
        db.execute("DELETE FROM notifications WHERE kind='parents_post' AND key=?", (key,))
        core.mark_sent(db, "parents_post", key)
    else:
        status["errors"].append("%s: %s" % (rep["group"]["name"], res.get("description")
                                            or res.get("error") or "Telegram said no"))
