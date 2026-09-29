"""The parents' channel: each week, a class's league and a report on every
student, as pictures a parent can read on a phone.

A class's post is its league table - everyone's points and what they gained
that week - and then one picture per student: their place, the marks the
teacher gave in each lesson with the notes written in it, their homework and
its marks, their points week by week, and a few sentences in Uzbek and in
Russian. The numbers are the league's own, cut to the week, so what a parent
reads and what the child sees on their Class page agree.

card.py draws the pictures; server.py has the teacher's page and starts the
sending; this file works the figures out, writes the sentences and posts.
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

UZ_DAYS = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]
RU_DAYS = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
UZ_DAY = ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"]
RU_DAY = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
WEEKS_SHOWN = 6


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


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


def points_ru(x):
    """очко / очка / очков - and 10,9 очка, since a fraction takes the genitive."""
    if round(x, 1) != int(round(x, 1)):
        return "очка"
    return ru_plural(int(round(x)), "очко", "очка", "очков")


# ------------------------------------------------ one student, one stretch

def lessons(db, student_id, lo, hi, cfg):
    """The lessons marked in [lo, hi): the three marks out of five, and the
    teacher's note, oldest first."""
    from datetime import date
    out = []
    for r in db.execute(
            "SELECT day, punctuality, behaviour, participation, note FROM lesson_marks"
            " WHERE student_id=? AND day >= ? AND day < ? ORDER BY day",
            (student_id, core.local_day(core.parse(lo), cfg), core.local_day(core.parse(hi), cfg))):
        marks = [r["punctuality"], r["behaviour"], r["participation"]]
        out.append({"day": date.fromisoformat(r["day"]), "marks": marks,
                    "note": (r["note"] or "").strip(),
                    "average": _mean(marks)})
    return out


def homework_items(db, st, lo, hi):
    """Each piece of homework the stretch holds, and how it went - the same
    pieces, judged the same way, as core.homework_marks."""
    stamp = core.iso(core.now())
    out = []
    for a in db.execute(
            "SELECT id, title, due_at, test_id FROM assignments WHERE group_id=? AND published=1"
            " AND in_league=1 AND created_at < ?"
            " AND (created_at >= ? OR (due_at IS NOT NULL AND due_at >= ?))"
            " ORDER BY due_at IS NULL, due_at", (st["group_id"], hi, lo, lo)).fetchall():
        due = a["due_at"]
        item = {"title": a["title"], "due": due, "mark": None, "state": None}
        if due and due > stamp:
            item["state"] = "pending"
        elif a["test_id"] and not core.is_handout(db, a["test_id"]):
            if not db.execute("SELECT 1 FROM dtests WHERE id=?", (a["test_id"],)).fetchone():
                continue
            sat = db.execute(
                "SELECT score, total, finished_at FROM dattempts WHERE test_id=? AND student_id=?"
                " AND finished_at IS NOT NULL ORDER BY finished_at LIMIT 1",
                (a["test_id"], st["id"])).fetchone()
            if not sat or not sat["total"]:
                item["state"] = "missing" if due else None
            elif due and sat["finished_at"] > due:
                item["state"] = "late"
            else:
                item["state"], item["mark"] = "marked", round(sat["score"] * 10.0 / sat["total"], 1)
        elif a["test_id"]:
            # on the site or on paper: the better of the two, as the league has it
            hw = core.handout_homework(db, a, st["id"])
            paper = hw["paper"]
            if hw["mark"] is not None:
                item["state"], item["mark"] = "marked", round(hw["mark"], 1)
                item["paper"] = hw["route"] == "paper"
            elif paper and paper["state"] in ("waiting", "late"):
                item["state"] = paper["state"]
                item["mark"] = 0.0 if paper["state"] == "late" else None
            else:
                item["state"] = "missing" if due else None
        else:
            sub = db.execute(
                "SELECT status, score, created_at FROM submissions WHERE student_id=?"
                " AND assignment_id=? AND draft=0 ORDER BY status='graded' DESC,"
                " created_at LIMIT 1", (st["id"], a["id"])).fetchone()
            if not sub:
                item["state"] = "missing" if due else None
            elif sub["status"] != "graded" or sub["score"] is None:
                item["state"] = "waiting"
            elif due and sub["created_at"] > due:
                item["state"], item["mark"] = "late", sub["score"]
            else:
                item["state"], item["mark"] = "marked", sub["score"]
        if item["state"]:
            out.append(item)
    return out


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
    ls = lessons(db, st["id"], lo, hi, cfg)
    # a lesson is worth up to two points: its three marks out of fifteen
    conduct_points = sum(sum(v or 0 for v in l["marks"]) / 15.0 * core.CONDUCT_PER_LESSON
                         for l in ls)
    return {"student": st, "set": set_n, "done": set_n - missing, "late": late,
            "missing": missing, "waiting": waiting,
            "average": round(_mean(marks), 1) if marks else None,
            "lessons": ls,
            "conduct": round(_mean([l["average"] for l in ls]), 1) if ls else None,
            "gained": round(homework_points + conduct_points, 1)}


def class_report(db, group_id, p, cfg=None):
    """Everything one class's post shows, for period p (from period())."""
    cfg = cfg or core.load_config()
    g = db.execute("SELECT * FROM groups WHERE id=?", (group_id,)).fetchone()
    students = db.execute("SELECT * FROM students WHERE group_id=? AND active=1 ORDER BY name",
                          (group_id,)).fetchall()
    rows = []
    weeks = weeks_back(p, WEEKS_SHOWN, cfg) if not p["monthly"] else weeks_back(p, 5, cfg)
    for st in students:
        r = student_period(db, st, p["lo"], p["hi"], cfg)
        r["items"] = homework_items(db, st, p["lo"], p["hi"])
        r["weekly"] = [(w, student_period(db, st, w["lo"], w["hi"], cfg)["gained"]) for w in weeks]
        rows.append(r)

    # the class's own league: the table the students see on their Class page
    champ = core.championship(db, cfg)
    league = {}
    if champ["started"]:
        for lr in core.scope_standing(champ, group_id)["rows"]:
            league[lr["student"]["id"]] = lr
    for r in rows:
        lr = league.get(r["student"]["id"])
        r["rank"] = lr["rank"] if lr else None
        r["season"] = lr["total"] if lr else None
    if league:
        rows.sort(key=lambda r: (r["rank"] is None, r["rank"] or 0, -r["gained"],
                                 r["student"]["name"]))
    else:
        # no season running: the class is ranked on this stretch alone
        rows.sort(key=lambda r: (-r["gained"], r["student"]["name"]))
        for i, r in enumerate(rows, 1):
            r["rank"] = i if r["gained"] > 0 else None
    return {"group": g, "level": core.level_name(db, core.level_of(db, group_id)) or "",
            "period": p, "rows": rows, "league": bool(league), "size": len(rows),
            "weeks": weeks}


# ------------------------------------------------ what is said about a student

def _first(name):
    return (name or "").split()[0] if name else ""


def summary_uz(r, rep):
    p = rep["period"]
    name = _first(r["student"]["name"])
    when = "Bu oy" if p["monthly"] else "Bu hafta"
    out = []
    ls = r["lessons"]
    if ls:
        out.append("%s %s %d ta darsda baho oldi, oʻrtacha %s / 5." % (
            when, name, len(ls), _n(r["conduct"])))
    else:
        out.append("%s %s darsda baho olmadi." % (when, name))
    if r["set"]:
        line = "Uy vazifalari: %d tadan %d tasi topshirildi" % (r["set"], r["done"])
        if r["average"] is not None:
            line += ", oʻrtacha baho %s / 10" % _n(r["average"])
        out.append(line + ".")
        if r["missing"]:
            out.append("%d ta vazifa topshirilmagan." % r["missing"])
    if r["gained"]:
        out.append("Ligada %s ball toʻpladi%s." % (
            _n(r["gained"]), (" va guruhda %d-oʻrinda turibdi" % r["rank"]) if r["rank"] else ""))
    return " ".join(out)


def summary_ru(r, rep):
    p = rep["period"]
    when = "за месяц" if p["monthly"] else "за неделю"
    out = []
    ls = r["lessons"]
    if ls:
        out.append("Оценки на уроках %s: %d %s, в среднем %s из 5." % (
            when, len(ls), ru_plural(len(ls), "урок", "урока", "уроков"), _n(r["conduct"])))
    else:
        out.append("Оценок на уроках %s нет." % when)
    if r["set"]:
        line = "Домашние задания: сдано %d из %d" % (r["done"], r["set"])
        if r["average"] is not None:
            line += ", средняя оценка %s из 10" % _n(r["average"])
        out.append(line + ".")
        if r["missing"]:
            out.append("Не сдано: %d." % r["missing"])
    if r["gained"]:
        out.append("В лиге %s: +%s %s%s." % (
            when, _n(r["gained"]), points_ru(r["gained"]),
            (", %d-е место в группе" % r["rank"]) if r["rank"] else ""))
    return " ".join(out)


def caption_for(r, rep):
    """Under a student's picture: the name, so a parent can search for it."""
    g = rep["group"]["name"]
    return "%s · %s-guruh · Группа %s" % (r["student"]["name"], g, g)


def league_caption(rep):
    p = rep["period"]
    g = rep["group"]["name"]
    return "%s-guruh · Группа %s\n%s · %s" % (
        g, g, "Liga, oy · Лига, месяц" if p["monthly"] else "Liga, hafta · Лига, неделя",
        short_days(p["first"], p["last"]))


# ------------------------------------------------ sending

import time

# Telegram lets a bot put about twenty messages a minute into one channel, and
# each picture of an album counts as one, so after an album the sending waits
# three and a half seconds a picture. A class of twelve takes about a minute.
PER_PICTURE = 3.5
ALBUM = 10                 # the most pictures Telegram takes in one album
LEAGUE_ROWS = 14           # a longer class has its league split over pictures
_sleep = time.sleep


def pictures(rep):
    """[(png, caption)] for one class: its league, then each student."""
    import card
    rows = rep["rows"]
    out = []
    chunks = [rows[i:i + LEAGUE_ROWS] for i in range(0, len(rows), LEAGUE_ROWS)] or [[]]
    for i, chunk in enumerate(chunks):
        out.append((card.league(rep, chunk, first=i * LEAGUE_ROWS), league_caption(rep) if not i else ""))
    for r in rows:
        out.append((card.student(r, rep), caption_for(r, rep)))
    return out


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
                _post_class(db, token, chan, p, gid, notes, cfg, pause, status, save)
            except Exception as exc:      # one class going wrong must not stop the rest
                status["errors"].append("class %d: %s" % (gid, exc))
            status["done"] = i + 1
            save()
        status["finished"] = core.iso(core.now())
        save()
        return status
    finally:
        db.close()


def _post_class(db, token, chan, p, gid, notes, cfg, pause, status, save):
    """One class: the teacher's note if there is one, then the pictures in
    albums of ten, each picture with its caption."""
    import bot
    rep = class_report(db, gid, p, cfg)
    note = (notes.get(gid) or "").strip()
    if note:
        res = bot.send(token, chan["id"], "✍️ %s-guruh · Группа %s\n\n%s" % (
            rep["group"]["name"], rep["group"]["name"], note))
        if not res.get("ok"):
            raise RuntimeError(res.get("description") or res.get("error") or "Telegram said no")
        pause(PER_PICTURE)
    pics = pictures(rep)
    for start in range(0, len(pics), ALBUM):
        batch = pics[start:start + ALBUM]
        res = None
        for _try in range(3):
            res = bot.send_album(token, chan["id"], [png for png, _c in batch],
                                 captions=[c for _p, c in batch])
            wait = (res.get("parameters") or {}).get("retry_after")
            if res.get("ok") or not wait:
                break
            pause(min(int(wait), 90) + 1)       # too fast: Telegram says how long to wait
        if not res.get("ok"):
            raise RuntimeError("%s: %s" % (rep["group"]["name"], res.get("description")
                                           or res.get("error") or "Telegram said no"))
        status["pictures"] = status.get("pictures", 0) + len(batch)
        save()
        pause(PER_PICTURE * len(batch))
    key = "%s:%d" % (p["key"], gid)
    db.execute("DELETE FROM notifications WHERE kind='parents_post' AND key=?", (key,))
    core.mark_sent(db, "parents_post", key)
