"""Everything the system does on its own, with nobody watching.

Runs on a background thread inside app.py: deadline reminders, nudges after a
missed assignment, weekly summaries, and database backups. Every message is
recorded in `notifications` first, so nothing is ever sent twice.
"""
import os
import shutil
import sqlite3
import time
from datetime import timedelta

import core

QUIET_START, QUIET_END = 9, 21   # local hours during which it may message people
BACKUP_KEEP = 14


def local_hour(cfg):
    return (core.now() + timedelta(hours=cfg["timezone_offset_hours"])).hour


def _send(token, chat_id, text):
    import bot
    return bot.send(token, chat_id, text)


def due_soon_reminders(db, token, cfg):
    """One nudge per student per assignment, roughly a day before it is due."""
    sent = 0
    horizon = core.iso(core.now() + timedelta(hours=26))
    for a in db.execute(
        "SELECT * FROM assignments WHERE closed=0 AND published=1 AND due_at IS NOT NULL"
        " AND due_at > ? AND due_at <= ?",
        (core.iso(core.now()), horizon),
    ).fetchall():
        for st in db.execute(
            "SELECT * FROM students WHERE group_id=? AND active=1 AND telegram_id IS NOT NULL",
            (a["group_id"],),
        ).fetchall():
            key = f"{a['id']}:{st['id']}"
            if core.already_sent(db, "due_soon", key):
                continue
            done = db.execute(
                "SELECT 1 FROM submissions WHERE student_id=? AND assignment_id=?",
                (st["id"], a["id"]),
            ).fetchone()
            if done:
                core.mark_sent(db, "due_soon", key)   # nothing to chase
                continue
            _send(token, st["telegram_id"], _phrase(st["lang"], "due_soon", a["title"]))
            core.mark_sent(db, "due_soon", key)
            sent += 1
    return sent


def missed_nudges(db, token, cfg):
    """The morning after a deadline, tell whoever did not send anything."""
    sent = 0
    since = core.iso(core.now() - timedelta(hours=36))
    for a in db.execute(
        "SELECT * FROM assignments WHERE closed=0 AND published=1 AND due_at IS NOT NULL"
        " AND due_at <= ? AND due_at >= ?",
        (core.iso(core.now()), since),
    ).fetchall():
        for st in db.execute(
            "SELECT * FROM students WHERE group_id=? AND active=1 AND telegram_id IS NOT NULL",
            (a["group_id"],),
        ).fetchall():
            key = f"{a['id']}:{st['id']}"
            if core.already_sent(db, "missed", key):
                continue
            done = db.execute(
                "SELECT 1 FROM submissions WHERE student_id=? AND assignment_id=?",
                (st["id"], a["id"]),
            ).fetchone()
            core.mark_sent(db, "missed", key)
            if done:
                continue
            _send(token, st["telegram_id"], _phrase(st["lang"], "missed", a["title"]))
            sent += 1
    return sent


def hourly_chase(db, token, cfg):
    """In the final hours before a deadline, chase whoever is behind.

    Guarded three ways: only inside waking hours (the caller checks), at most
    once per clock hour, and never more than `chase_max` times per deadline.
    """
    sent = 0
    now = core.now()
    window_end = core.iso(now + timedelta(hours=cfg.get("chase_hours", 6)))
    hour_bucket = now.strftime("%Y-%m-%dT%H")
    threshold = cfg.get("chase_threshold", 80)
    cap = cfg.get("chase_max", 5)

    groups = db.execute(
        "SELECT DISTINCT group_id FROM assignments WHERE closed=0 AND published=1"
    ).fetchall()
    for g in groups:
        for due_at, items in core.open_sets(db, g["group_id"]):
            if not due_at or due_at <= core.iso(now) or due_at > window_end:
                continue
            for row in core.group_set_progress(db, g["group_id"], items):
                st = row["student"]
                if not st["telegram_id"] or row["percent"] >= threshold:
                    continue
                already = db.execute(
                    "SELECT COUNT(*) c FROM notifications WHERE kind='chase' AND key LIKE ?",
                    (f"{due_at}:{st['id']}:%",),
                ).fetchone()["c"]
                if already >= cap:
                    continue
                key = f"{due_at}:{st['id']}:{hour_bucket}"
                if core.already_sent(db, "chase", key):
                    continue
                names = ", ".join(a["title"] for a in row["remaining"])
                _send(token, st["telegram_id"], _phrase_fmt(
                    st["lang"], "chase", done=row["done"], total=row["total"],
                    due=" (%s)" % due_at[:10], items=names))
                core.mark_sent(db, "chase", key)
                sent += 1
    return sent


def deadline_summary(db, token, cfg):
    """Once a deadline passes, send the teacher the full roll-call."""
    import json
    teachers = json.loads(core.meta_get(db, "teachers", "[]"))
    if not teachers:
        return 0
    now = core.now()
    since = core.iso(now - timedelta(hours=30))
    sent = 0
    rows = db.execute(
        "SELECT DISTINCT group_id, due_at FROM assignments WHERE published=1"
        " AND due_at IS NOT NULL AND due_at <= ? AND due_at >= ?",
        (core.iso(now), since),
    ).fetchall()
    for r in rows:
        key = f"{r['group_id']}:{r['due_at']}"
        if core.already_sent(db, "summary", key):
            continue
        items = core.homework_items(db, r["group_id"], r["due_at"])
        if not items:
            core.mark_sent(db, "summary", key)
            continue
        prog = core.group_set_progress(db, r["group_id"], items)
        gname = db.execute("SELECT name FROM groups WHERE id=?", (r["group_id"],)).fetchone()
        lines = [f"Deadline passed - {gname['name'] if gname else ''} ({r['due_at'][:10]})",
                 f"{len(items)} task(s) set"]
        for row in prog:
            mark = "OK" if row["percent"] == 100 else f"{row['percent']}%"
            missing = ("" if not row["remaining"]
                       else " - missing: " + ", ".join(a["title"] for a in row["remaining"]))
            lines.append(f"{row['student']['name']}: {row['done']}/{row['total']} ({mark}){missing}")
        done_all = sum(1 for row in prog if row["percent"] == 100)
        lines.append(f"{done_all} of {len(prog)} finished everything.")
        for tid in teachers:
            _send(token, tid, "\n".join(lines)[:4000])
        core.mark_sent(db, "summary", key)
        sent += 1
    return sent


def parent_weekly(db, token, cfg):
    """A short weekly note to any parent who has used their link."""
    week = (core.now() + timedelta(hours=cfg["timezone_offset_hours"])).strftime("%G-W%V")
    sent = 0
    for p in db.execute(
        "SELECT * FROM parents WHERE telegram_id IS NOT NULL"
    ).fetchall():
        key = f"{p['id']}:{week}"
        if core.already_sent(db, "parent", key):
            continue
        st = db.execute("SELECT * FROM students WHERE id=?", (p["student_id"],)).fetchone()
        if not st:
            core.mark_sent(db, "parent", key)
            continue
        s = core.student_stats(db, st["id"])
        msg = ("Weekly summary for %s\n"
               "Homework completed: %s%%\n"
               "Average score: %s/10\n"
               "Missed: %d") % (
            st["name"],
            s["completion"] if s["completion"] is not None else "-",
            s["average"] if s["average"] is not None else "-",
            s["missed"])
        _send(token, p["telegram_id"], msg)
        core.mark_sent(db, "parent", key)
        sent += 1
    return sent


def vocab_due(db, token, cfg):
    """Once a day, tell students how many words are waiting for review."""
    day = (core.now() + timedelta(hours=cfg["timezone_offset_hours"])).strftime("%Y-%m-%d")
    sent = 0
    for st in db.execute(
        "SELECT * FROM students WHERE active=1 AND telegram_id IS NOT NULL"
    ).fetchall():
        key = f"{st['id']}:{day}"
        if core.already_sent(db, "vocabdue", key):
            continue
        v = core.vocab_stats(db, st["id"])
        core.mark_sent(db, "vocabdue", key)
        if v["due"] >= 5:
            _send(token, st["telegram_id"],
                  "%d words are ready to review. Tap Practise words." % v["due"])
            sent += 1
    return sent


def rescue_drafts(db, token, cfg):
    """Send anything a student photographed but forgot to finish.

    The Finish button stops stray photos landing in the wrong task, but it must
    never be the reason a student's work is not marked.
    """
    import bot
    cutoff = core.iso(core.now() - timedelta(hours=cfg.get("draft_hours", 2)))
    sent = 0
    for row in db.execute(
        "SELECT s.*, a.title FROM submissions s LEFT JOIN assignments a"
        " ON a.id=s.assignment_id WHERE s.draft=1 AND s.created_at <= ?", (cutoff,)
    ).fetchall():
        if not core.page_count(db, row["id"]):
            continue
        core.finish_draft(db, row["id"])
        bot.notify_teachers_new(db, token, row["id"])
        st = db.execute("SELECT telegram_id, lang FROM students WHERE id=?",
                        (row["student_id"],)).fetchone()
        if st and st["telegram_id"]:
            _send(token, st["telegram_id"],
                  bot.t(st["lang"], "auto_sent", title=row["title"] or "homework",
                        n=core.page_count(db, row["id"])))
        sent += 1
    return sent


def teacher_digest(db, token, cfg):
    """Once a week: who is slipping, and how big the queue is."""
    week = (core.now() + timedelta(hours=cfg["timezone_offset_hours"])).strftime("%G-W%V")
    if core.already_sent(db, "digest", week):
        return 0
    import json
    import bot
    teachers = json.loads(core.meta_get(db, "teachers", "[]"))
    if not teachers:
        return 0
    pending = db.execute(
        "SELECT COUNT(*) c FROM submissions WHERE status='pending'"
    ).fetchone()["c"]
    risky = []
    for st in db.execute("SELECT * FROM students WHERE active=1").fetchall():
        s = core.student_stats(db, st["id"])
        if s["at_risk"]:
            risky.append(f"• {st['name']} ({s['missed']} missed)")
    lines = [f"Weekly summary", f"{pending} submission(s) waiting to grade."]
    lines.append("Needs attention:\n" + "\n".join(risky) if risky
                 else "Nobody is flagged this week.")
    for tid in teachers:
        _send(token, tid, "\n\n".join(lines))
    core.mark_sent(db, "digest", week)
    return len(teachers)


PHRASES = {
    "due_soon": {
        "en": "Reminder: “{title}” is due tomorrow. Send a photo when it is ready.",
        "ru": "Напоминание: «{title}» нужно сдать завтра. Отправьте фото, когда будет готово.",
        "uz": "Eslatma: “{title}” ertaga topshiriladi. Tayyor bo'lganda rasmini yuboring.",
    },
    "missed": {
        "en": "The deadline for “{title}” has passed and you did not send it. "
              "Speak to your teacher if you still want it marked.",
        "ru": "Срок сдачи «{title}» истёк, работа не отправлена. "
              "Обратитесь к преподавателю, если хотите её сдать.",
        "uz": "“{title}” muddati tugadi, ish yuborilmadi. "
              "Baholanishini istasangiz, o'qituvchi bilan gaplashing.",
    },
}


def _phrase(lang, kind, title):
    table = PHRASES[kind]
    return table.get(lang, table["en"]).format(title=title)


def _phrase_fmt(lang, kind, **kw):
    import bot
    return bot.t(lang, "hw_" + kind, **kw)


def backup(db_path=None):
    """A consistent copy of the database, even while it is being written to."""
    db_path = db_path or core.DB_PATH
    out_dir = os.path.join(core.DATA_DIR, "backups")
    os.makedirs(out_dir, exist_ok=True)
    stamp = core.now().strftime("%Y-%m-%d")
    dest = os.path.join(out_dir, f"app-{stamp}.db")
    src = sqlite3.connect(db_path)
    try:
        with sqlite3.connect(dest) as dst:
            src.backup(dst)          # safe online copy, not a file copy
    finally:
        src.close()
    keep = sorted(f for f in os.listdir(out_dir) if f.endswith(".db"))
    for old in keep[:-BACKUP_KEEP]:
        os.remove(os.path.join(out_dir, old))
    return dest


def tick(cfg):
    """One pass. Safe to call as often as you like; the work is deduplicated."""
    token = cfg.get("telegram_token")
    db = core.connect()
    done = {}
    try:
        if core.already_sent(db, "backup", core.now().strftime("%Y-%m-%d")):
            done["backup"] = "already today"
        else:
            done["backup"] = os.path.basename(backup())
            core.mark_sent(db, "backup", core.now().strftime("%Y-%m-%d"))
        if not cfg.get("automation"):
            done["messages"] = "disabled (set automation: true in config.json)"
        elif token and QUIET_START <= local_hour(cfg) < QUIET_END:
            done["rescued"] = rescue_drafts(db, token, cfg)
            done["due_soon"] = due_soon_reminders(db, token, cfg)
            done["chase"] = hourly_chase(db, token, cfg)
            done["missed"] = missed_nudges(db, token, cfg)
            done["summary"] = deadline_summary(db, token, cfg)
            done["digest"] = teacher_digest(db, token, cfg)
            done["parents"] = parent_weekly(db, token, cfg)
            done["vocab_due"] = vocab_due(db, token, cfg)
    finally:
        db.close()
    return done


def forever():
    while True:
        try:
            cfg = core.load_config()
            tick(cfg)
        except Exception as exc:
            print("scheduler error:", exc)
        time.sleep(900)   # every 15 minutes
