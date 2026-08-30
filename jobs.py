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
        "en": "You have not sent “{title}” yet. You can still send it — late is better than missing.",
        "ru": "Вы ещё не отправили «{title}». Можно отправить сейчас — лучше поздно, чем никогда.",
        "uz": "Siz hali “{title}” ni yubormadingiz. Hozir ham yuborsangiz bo'ladi.",
    },
}


def _phrase(lang, kind, title):
    table = PHRASES[kind]
    return table.get(lang, table["en"]).format(title=title)


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
            done["due_soon"] = due_soon_reminders(db, token, cfg)
            done["missed"] = missed_nudges(db, token, cfg)
            done["digest"] = teacher_digest(db, token, cfg)
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
