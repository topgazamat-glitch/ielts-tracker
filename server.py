"""Teacher dashboard: grading queue, groups, students, progress charts.

Runs on the Python standard library alone: python3 server.py
"""
import html
import json
import time
import os
import re
import secrets
import traceback
import urllib.parse
from datetime import timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import charts
import core
import uploads

CFG = core.load_config()
SESSIONS = {}
LOGIN_ATTEMPTS = {}          # client -> [timestamps of recent failures]
MAX_ATTEMPTS, LOCKOUT = 6, 900


def login_blocked(client):
    now = time.time()
    tries = [t for t in LOGIN_ATTEMPTS.get(client, []) if now - t < LOCKOUT]
    LOGIN_ATTEMPTS[client] = tries
    return len(tries) >= MAX_ATTEMPTS


def login_failed(client):
    LOGIN_ATTEMPTS.setdefault(client, []).append(time.time())
E = html.escape


# ------------------------------------------------------------------ layout

def page(title, body, active="", music=False):
    """The teacher's shell. Silent unless a page asks otherwise: marking
    for three hours should not come with a soundtrack - but the song of the
    day is the teacher's own choice, so that one plays here too."""
    tune = song_tag()
    def nav(href, label):
        cls = ' class="on"' if active == label else ""
        return f'<a href="{href}"{cls}>{label}</a>'

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{E(title)} · OlimovAzamat</title>
<link rel="stylesheet" href="/static/style.css"></head><body>
<header class="top">
<span class="brand"><span class="mark">O</span>OlimovAzamat</span>
<nav>{nav('/', 'Overview')}{nav('/queue', 'Grade')}{nav('/homework', 'Homework')}
{nav('/ratings', 'Progress')}{nav('/championship', 'League')}{nav('/assignments', 'Assignments')}{nav('/groups', 'Groups')}
{nav('/roster', 'Students')}{nav('/materials', 'Materials')}{nav('/vocab', 'Vocabulary')}{nav('/music', 'Music')}{nav('/play', 'Play')}{nav('/questions', 'Questions')}</nav>
<span class="right">{'<button type="button" id="musicbtn" class="musicbtn"'
  ' onclick="Music.toggle()" title="Music"></button>' if (music or tune) else ''}
<a href="/logout">Sign out</a></span></header>
<main>{body}</main>
{tune}{'<script src="/static/music.js" defer></script>' if (music or tune) else ''}
<script src="/static/nav.js" defer></script>
<script src="/static/materials.js" defer></script>
<script src="/static/grade.js" defer></script>
<script src="/static/roster.js" defer></script>
</body></html>"""


def stat(k, v, sub=""):
    s = f" <small>{E(sub)}</small>" if sub else ""
    return f'<div class="stat"><div class="k">{E(k)}</div><div class="v">{v}{s}</div></div>'


def fmt(v, dash="—"):
    return dash if v is None else v


def bar_colour(pct):
    return ("var(--warn)" if pct < 34
            else "var(--amber)" if pct < 67 else "var(--accent)")


def band_class(value, low, high):
    """Three states, not two: below `low` is a problem, at or above `high` is
    fine, and the stretch between them is the part worth watching."""
    if value is None:
        return "mute"
    if value < low:
        return "risk"
    return "good" if value >= high else "watch"


def score_pill(s):
    if s is None:
        return '<span class="pill mute">—</span>'
    return f'<span class="pill {band_class(s, 5, 8)}">{s:g}/10</span>'


# ------------------------------------------------------------------- pages

def view_login(req, err=""):
    text = err if isinstance(err, str) and err else "Wrong password"
    msg = f'<div class="flash err">{E(text)}</div>' if err else ""
    body = f"""<div class="login card"><h1>Sign in</h1>
<p class="sub">Teacher access only.</p>{msg}
<form method="post" action="/login" class="inline">
<label class="f">Password<input type="password" name="password" autofocus></label>
<button>Enter</button></form></div>"""
    # deliberately not the teacher layout: a signed-out visitor sees no navigation
    return html_response(student_page("Sign in", body))


def view_overview(req, db):
    pending = db.execute(
        "SELECT COUNT(*) c FROM submissions WHERE status='pending' AND draft=0"
    ).fetchone()["c"]
    students = db.execute("SELECT * FROM students WHERE active=1").fetchall()
    groups = db.execute("SELECT * FROM groups WHERE archived=0 ORDER BY name").fetchall()

    risky, all_avg = [], []
    for s in students:
        st = core.student_stats(db, s["id"])
        if st["average"] is not None:
            all_avg.append(st["average"])
        if st["at_risk"]:
            risky.append((s, st))
    risky.sort(key=lambda p: (-p[1]["consecutive_misses"], p[1]["trend"] or 0))

    avg = round(sum(all_avg) / len(all_avg), 2) if all_avg else None
    cards = (
        '<div class="grid">'
        + stat("Awaiting grading", pending)
        + stat("Active students", len(students))
        + stat("Groups", len(groups))
        + stat("Average score", fmt(avg), "/10" if avg else "")
        + "</div>"
    )

    if risky:
        rows = "".join(
            f'<tr><td><a href="/students/{s["id"]}">{E(s["name"])}</a></td>'
            f'<td>{E(group_name(db, s["group_id"]))}</td>'
            f'<td>{score_pill(st["last3"])}</td>'
            f'<td>{fmt(st["completion"], "—")}{"%" if st["completion"] is not None else ""}</td>'
            f'<td>{reason(st)}</td></tr>'
            for s, st in risky
        )
        risk_html = (
            '<div class="tablewrap"><table><tr><th>Student</th><th>Group</th>'
            "<th>Last 3</th><th>Completion</th><th>Why flagged</th></tr>"
            f"{rows}</table></div>"
        )
    else:
        risk_html = '<div class="card"><p class="sub" style="margin:0">Nobody is flagged. '
        risk_html += "Students appear here after two consecutive misses or a falling trend.</p></div>"

    body = f"""{today_block(db, pending)}
<h2>Where everyone stands</h2>{cards}<h2>Needs attention</h2>{risk_html}"""
    return html_response(page("Overview", body, "Overview"))


def todo(href, headline, detail, urgent=False):
    return (f'<a class="todo{" urgent" if urgent else ""}" href="{href}">'
            f'<div class="todo-head">{headline}</div>'
            f'<div class="sub" style="margin:2px 0 0">{detail}</div></a>')


def today_block(db, pending):
    """The first thing on the screen should be the work, not the statistics."""
    cfg = core.load_config()
    today = core.local_day(core.now(), cfg)
    items = ""

    if pending:
        oldest = db.execute(
            "SELECT created_at FROM submissions WHERE status='pending' AND draft=0"
            " ORDER BY created_at LIMIT 1").fetchone()
        waited = ""
        when = core.parse(oldest["created_at"]) if oldest else None
        if when:
            hours = (core.now() - when).total_seconds() / 3600
            waited = ("waiting %d days" % (hours // 24) if hours >= 48
                      else "waiting since yesterday" if hours >= 24
                      else "arrived today")
        items += todo("/queue", "%d to grade" % pending, waited or "in the queue",
                      urgent=pending >= 10)

    # a class that got a list of six tasks is one line, not six
    for r in db.execute(
        "SELECT a.group_id, g.name gname, COUNT(*) tasks,"
        "  (SELECT COUNT(*) FROM students st WHERE st.group_id=a.group_id"
        "   AND st.active=1) total,"
        "  (SELECT COUNT(DISTINCT s.student_id) FROM submissions s WHERE s.draft=0"
        "   AND s.assignment_id IN (SELECT id FROM assignments b"
        "     WHERE b.group_id=a.group_id AND b.closed=0 AND b.published=1"
        "     AND b.due_at LIKE ?)) got"
        " FROM assignments a JOIN groups g ON g.id=a.group_id"
        " WHERE a.closed=0 AND a.published=1 AND a.due_at LIKE ?"
        " GROUP BY a.group_id ORDER BY g.name",
        (today + "%", today + "%")).fetchall():
        items += todo(f'/groups/{r["group_id"]}?tab=homework',
                      "%s · due today" % E(r["gname"]),
                      "%d task%s — %d of %d students in"
                      % (r["tasks"], "" if r["tasks"] == 1 else "s",
                         r["got"], r["total"]),
                      urgent=bool(r["total"]) and r["got"] * 2 < r["total"])

    week = core.iso(core.now() - timedelta(days=7))
    silent = db.execute(
        "SELECT COUNT(*) c FROM students s WHERE s.active=1 AND NOT EXISTS ("
        "  SELECT 1 FROM submissions x WHERE x.student_id=s.id AND x.draft=0"
        "  AND x.created_at > ?)", (week,)).fetchone()["c"]
    if silent:
        items += todo("/ratings", "%d sent nothing this week" % silent,
                      "Bottom of the ratings table", urgent=silent >= 5)

    unread = db.execute(
        "SELECT COUNT(*) c FROM questions WHERE answer IS NULL").fetchone()["c"]
    if unread:
        items += todo("/questions", "%d question%s waiting" % (unread, "" if unread == 1 else "s"),
                      "Students asked you something")

    if not items:
        return ('<h1>Today</h1><div class="card"><p style="margin:0">'
                'Nothing is waiting. Everything is graded and every class is up to '
                'date.</p></div>')
    return f'<h1>Today</h1><div class="todos">{items}</div>'


def reason(st):
    bits = []
    if st["consecutive_misses"] >= 2:
        bits.append(f'{st["consecutive_misses"]} misses in a row')
    if st["trend"] is not None and st["trend"] <= -1.0:
        bits.append(f'trend {st["trend"]:+g}')
    return E(", ".join(bits) or "—")


def group_name(db, gid):
    if not gid:
        return "—"
    r = db.execute("SELECT name FROM groups WHERE id=?", (gid,)).fetchone()
    return r["name"] if r else "—"


AUDIO_EXT = (".oga", ".ogg", ".mp3", ".m4a", ".wav", ".opus", ".weba")


def is_audio(name):
    return (name or "").lower().endswith(AUDIO_EXT)


def shot(f, i):
    """One page of homework - or, for speaking, something you can actually play.

    A voice note is a file like any other, and rendering it through an <img>
    put a broken picture where the recording should have been.
    """
    small = screen_name(f)
    if is_audio(small):
        return (f'<audio controls preload="metadata" class="voice"'
                f' src="/media/{E(small)}"></audio>')
    dims = ""
    if f["width"] and f["height"]:
        dims = f' width="{f["width"]}" height="{f["height"]}"'
    full = f' data-full="/media/{E(f["filename"])}"' if small != f["filename"] else ""
    lazy = "" if i == 0 else ' loading="lazy"'
    return (f'<img src="/media/{E(small)}" alt="page {i+1}"{dims}{full}{lazy}'
            f' decoding="async" onclick="zoom(this)">')


def scorepad(name="score", value=None, small=False):
    """Whole marks on top, halves underneath - one tap either way."""
    cls = "scorepad" + (" mini" if small else "")
    def mark(v):
        return ' class="sel"' if value is not None and abs(value - v) < 1e-9 else ""
    whole = "".join(
        f'<button type="button" data-v="{n}" data-for="{name}"{mark(n)}>{n}</button>'
        for n in range(1, 11))
    half = "".join(
        f'<button type="button" class="half{" sel" if mark(n + 0.5) else ""}"'
        f' data-v="{n + 0.5}" data-for="{name}">{n}&frac12;</button>'
        for n in range(1, 10))
    return (f'<div class="{cls}">{whole}</div>'
            f'<div class="{cls} halves">{half}</div>')


def grade_form(db, sub, student, assignment, regrade=False):
    """The marking form, used for a fresh piece and for changing an old mark."""
    tags = db.execute("SELECT * FROM tags ORDER BY sort, id").fetchall()
    chosen = {r["tag_id"] for r in db.execute(
        "SELECT tag_id FROM submission_tags WHERE submission_id=?", (sub["id"],))}
    tagboxes = "".join(
        f'<label><input type="checkbox" name="tag" value="{t["id"]}"'
        f'{" checked" if t["id"] in chosen else ""}><span>{E(t["label"])}</span></label>'
        for t in tags)

    rubric = bool(assignment and assignment["rubric"])
    marks = core.criteria_for(db, sub["id"])
    if rubric:
        rows = ""
        for key, label, hint in core.CRITERIA:
            rows += (f'<div class="crit"><div><strong>{E(label)}</strong>'
                     f'<div class="sub">{E(hint)}</div></div>'
                     f'<input type="hidden" name="c_{key}" id="f_c_{key}"'
                     f' value="{marks.get(key, "")}">'
                     f'{scorepad("c_" + key, marks.get(key), small=True)}</div>')
        scoring = (f'<div class="criteria">{rows}</div>'
                   f'<p class="sub" id="overall">The overall mark is the average '
                   f'of these four.</p>')
    else:
        scoring = (f'<input type="hidden" name="score" id="f_score"'
                   f' value="{sub["score"] if sub["score"] is not None else ""}">'
                   f'{scorepad("score", sub["score"])}')

    tmpl = core.note_templates(db)
    chips = "".join(
        f'<button type="button" class="chip" onclick="useNote(this)">{E(t["text"])}</button>'
        for t in tmpl)
    manage = "".join(
        f'<li>{E(t["text"])}<form method="post" action="/notes/delete">'
        f'<input type="hidden" name="id" value="{t["id"]}">'
        f'<button class="linky">remove</button></form></li>' for t in tmpl)

    common = core.student_tag_counts(db, student["id"])
    recur = ""
    if common:
        recur = ('<div class="recur"><span class="sub">Keeps happening:</span> '
                 + " ".join(f'<span class="pill mute">{E(r["label"])} &times;{r["n"]}</span>'
                            for r in common) + "</div>")

    action = "/regrade" if regrade else "/grade"
    save = "Save the change" if regrade else "Save &amp; next"
    skip = ("" if regrade else
            '<button class="ghost" formaction="/skip" name="skip" value="1">Skip</button>')
    return f"""<form method="post" action="{action}" id="gform" class="card">
      <input type="hidden" name="submission_id" value="{sub['id']}">
      {scoring}
      {recur}
      <div class="tags">{tagboxes}</div>
      <label class="f">Note (optional)
        <textarea name="note" id="note" rows="2"
          placeholder="One line the student will read">{E(sub["note"] or "")}</textarea></label>
      <div class="chips">{chips}</div>
      <div style="display:flex;gap:8px;margin-top:10px">
        <button id="save"{"" if regrade or sub["score"] else " disabled"}>{save}</button>
        {skip}
      </div>
    </form>
    <details class="card"><summary>Edit the quick notes</summary>
      <ul class="tmpl">{manage or '<li class="sub">None yet.</li>'}</ul>
      <form method="post" action="/notes/new" class="adder">
        <input name="text" maxlength="300" placeholder="Add a sentence you write often" required>
        <button class="ghost">Add</button></form>
    </details>"""


def previous_panel(db, sub, student):
    """The last piece this student had marked, so you can see the difference."""
    prev = core.previous_graded(db, student["id"], sub["id"])
    if not prev:
        return '<div class="card"><div class="sub">No earlier marked work.</div></div>'
    files = db.execute("SELECT * FROM files WHERE submission_id=? ORDER BY ord, id LIMIT 2",
                       (prev["id"],)).fetchall()
    thumbs = ""
    for f in files:
        n = screen_name(f)
        thumbs += ('<span class="tinyaudio">&#9834; recording</span>' if is_audio(n)
                   else f'<img src="/media/{E(n)}" alt="" loading="lazy">')
    a = (db.execute("SELECT title FROM assignments WHERE id=?", (prev["assignment_id"],)).fetchone()
         if prev["assignment_id"] else None)
    when = (prev["graded_at"] or prev["created_at"] or "")[:10]
    note = f'<div class="sub prevnote">&ldquo;{E(prev["note"])}&rdquo;</div>' if prev["note"] else ""
    return f"""<div class="card prev">
      <div class="sub">Last time &mdash; {E(when)}{" &middot; " + E(a["title"]) if a else ""}</div>
      <div class="prevhead">{score_pill(prev["score"])}
        <a class="linky" href="/regrade/{prev["id"]}">change this mark</a></div>
      {note}
      <div class="prevshots">{thumbs}</div>
    </div>"""


def waiting_list(db, current_id):
    """Everyone still in the queue, so a name can be found without hunting."""
    rows = db.execute(
        "SELECT s.id, s.created_at, s.kind, s.late, st.name, st.group_id,"
        " a.title FROM submissions s JOIN students st ON st.id=s.student_id"
        " LEFT JOIN assignments a ON a.id=s.assignment_id"
        " WHERE s.status='pending' AND s.draft=0 ORDER BY s.created_at LIMIT 60"
    ).fetchall()
    if len(rows) < 2:
        return ""
    out = ""
    for r in rows:
        here = ' class="on"' if r["id"] == current_id else ""
        kind = ' <span class="pill mute">speaking</span>' if r["kind"] == "voice" else ""
        late = ' <span class="pill risk">late</span>' if r["late"] else ""
        out += (f'<li{here}><a href="/queue?id={r["id"]}">{E(r["name"])}</a>'
                f'<span class="sub">{E(group_name(db, r["group_id"]))}'
                f'{" &middot; " + E(r["title"]) if r["title"] else ""}</span>'
                f'{kind}{late}</li>')
    return (f'<details class="card queuelist"><summary>{len(rows)} waiting '
            f'&mdash; jump to anyone</summary><ul>{out}</ul></details>')


def undo_strip(db):
    """One click back to the mark you just gave, because keys slip."""
    last = core.last_graded(db)
    if not last:
        return ""
    st = db.execute("SELECT name FROM students WHERE id=?", (last["student_id"],)).fetchone()
    if not st:
        return ""
    return (f'<div class="undo">Last marked <strong>{E(st["name"])}</strong> '
            f'{score_pill(last["score"])} '
            f'<a class="linky" href="/regrade/{last["id"]}">change it</a></div>')


def grade_page(db, sub, regrade=False):
    student = db.execute("SELECT * FROM students WHERE id=?", (sub["student_id"],)).fetchone()
    assignment = (db.execute("SELECT * FROM assignments WHERE id=?",
                             (sub["assignment_id"],)).fetchone()
                  if sub["assignment_id"] else None)
    files = db.execute("SELECT * FROM files WHERE submission_id=? ORDER BY ord, id",
                       (sub["id"],)).fetchall()
    st = core.student_stats(db, student["id"])
    shots = "".join(shot(f, i) for i, f in enumerate(files)) \
        or '<p class="sub">Nothing attached.</p>'

    remaining = db.execute(
        "SELECT COUNT(*) c FROM submissions WHERE status='pending' AND draft=0"
    ).fetchone()["c"]

    # while this student is being scored, quietly pull the next one's pages, so
    # the queue never makes the teacher wait for a download again
    ahead = []
    if not regrade:
        nxt = db.execute(
            "SELECT * FROM submissions WHERE status='pending' AND draft=0 AND id<>?"
            " ORDER BY created_at LIMIT 1", (sub["id"],)).fetchone()
        if nxt:
            ahead = [screen_name(f) for f in db.execute(
                "SELECT * FROM files WHERE submission_id=? ORDER BY ord, id LIMIT 4",
                (nxt["id"],)).fetchall() if not is_audio(screen_name(f))]
    prefetch = json.dumps(["/media/" + n for n in ahead])

    prev = (f'Average {fmt(st["average"])} &middot; last 3 {fmt(st["last3"])} &middot; '
            f'{st["graded_count"]} graded &middot; {st["missed"]} missed')
    head = ("<h1>Change a mark</h1>" if regrade else "<h1>Grading queue</h1>")
    hint = ("" if regrade else
            f'<p class="sub">{remaining} waiting &middot; keys <span class="kbd">1</span>&ndash;'
            f'<span class="kbd">9</span> <span class="kbd">0</span>=10, hold '
            f'<span class="kbd">Shift</span> for a half, <span class="kbd">Enter</span> '
            f'to save, <span class="kbd">s</span> to skip.</p>')
    body = f"""{head}
{hint}
{"" if regrade else undo_strip(db)}
{"" if regrade else waiting_list(db, sub["id"])}
<div class="queue">
  <div class="shots">{shots}</div>
  <div>
    <div class="card">
      <div style="font-weight:600">{E(student["name"])}</div>
      <div class="sub" style="margin:2px 0 0">{E(group_name(db, student["group_id"]))} &middot;
        {E(assignment["title"]) if assignment else "unassigned"}
        {'<span class="pill risk">late</span>' if sub["late"] else ''}
        {'<span class="pill mute">speaking</span>' if sub["kind"] == "voice" else ''}
        {'<span class="pill mute">resubmission</span>' if sub["improves"] else ''}</div>
      <div class="sub" style="margin:6px 0 0">{prev}</div>
    </div>
    {grade_form(db, sub, student, assignment, regrade)}
    {previous_panel(db, sub, student)}
  </div>
</div>
<div id="gradedata" hidden data-skip="{sub["id"]}"
     data-regrade="{1 if regrade else 0}" data-prefetch="{E(prefetch)}"></div>"""
    return html_response(page("Change a mark" if regrade else "Grade", body, "Grade"))


def view_queue(req, db):
    core.seed_notes(db)
    want = (req["query"].get("id", [""])[0] or "").strip()
    sub = None
    if want.isdigit():
        sub = db.execute(
            "SELECT * FROM submissions WHERE id=? AND status='pending' AND draft=0",
            (int(want),)).fetchone()
    if not sub:
        sub = db.execute(
            "SELECT * FROM submissions WHERE status='pending' AND draft=0"
            " ORDER BY created_at LIMIT 1").fetchone()
    if not sub:
        body = f"""<h1>Grading queue</h1>
{undo_strip(db)}
<div class="card"><p style="margin:0">Queue is empty. Nothing to grade.</p></div>"""
        return html_response(page("Grade", body, "Grade"))
    return grade_page(db, sub)


def view_regrade(req, db, sid):
    sub = db.execute("SELECT * FROM submissions WHERE id=?", (sid,)).fetchone()
    if not sub:
        return not_found()
    core.seed_notes(db)
    return grade_page(db, sub, regrade=True)


def restore_photo(name):
    """Bring a page back from Telegram after its file was dropped from disk.

    Nothing is lost when a photo is offloaded - Telegram keeps the original and
    we keep its file_id - so an old submission still opens, it just takes a
    moment the first time.
    """
    token = core.load_config().get("telegram_token")
    if not token:
        return False
    db = core.connect()
    row = db.execute(
        "SELECT filename, telegram_file_id, preview, preview_id FROM files"
        " WHERE filename=? OR preview=? LIMIT 1", (name, name)).fetchone()
    if not row:
        return False
    # a screen-sized copy has its own id; asking for the full page instead would
    # pull megabytes to show a thumbnail
    wanted = (row["preview_id"] if row["preview"] == name
              else row["telegram_file_id"])
    if not wanted:
        return False
    try:
        import bot
        if not bot.download_photo(token, wanted, name):
            return False
    except Exception:
        return False
    db.execute("UPDATE files SET offloaded=0 WHERE filename=?", (name,))
    db.commit()
    return os.path.isfile(os.path.join(core.UPLOAD_DIR, name))


def screen_name(f):
    """The copy to put on screen: the small one when we have it."""
    try:
        return f["preview"] or f["filename"]
    except (IndexError, KeyError):
        return f["filename"]


def ring(percent, size=64):
    """A small progress ring - reads faster than a number on a card."""
    if percent is None:
        percent = 0
    r = (size - 8) / 2
    circ = 2 * 3.14159 * r
    done = circ * min(100, max(0, percent)) / 100
    colour = bar_colour(percent)
    return (f'<svg class="ring" viewBox="0 0 {size} {size}" width="{size}" height="{size}">'
            f'<circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none" stroke="var(--line)"'
            f' stroke-width="6"/>'
            f'<circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none" stroke="{colour}"'
            f' stroke-width="6" stroke-linecap="round"'
            f' stroke-dasharray="{done:.1f} {circ:.1f}"'
            f' transform="rotate(-90 {size/2} {size/2})"/>'
            f'<text x="50%" y="54%" text-anchor="middle" class="ringtext">{percent}%</text>'
            "</svg>")


def view_groups(req, db):
    groups = db.execute("SELECT * FROM groups WHERE archived=0 ORDER BY name").fetchall()
    bot_user = core.meta_get(db, "bot_username", "")
    levels = db.execute("SELECT * FROM levels ORDER BY sort").fetchall()
    level_opts = ('<option value="">— no level —</option>'
                  + "".join(f'<option value="{l["id"]}">{E(l["name"])}</option>'
                            for l in levels))

    cards = ""
    for g in groups:
        rows = group_rows(db, g["id"])
        comps = [r["completion"] for r in rows if r["completion"] is not None]
        avgs = [r["stats"]["average"] for r in rows if r["stats"]["average"] is not None]
        marks = [r["marks"]["overall"] for r in rows if r["marks"]["overall"] is not None]
        comp = round(sum(comps) / len(comps)) if comps else 0
        avg = round(sum(avgs) / len(avgs), 1) if avgs else None
        mark = round(sum(marks) / len(marks), 1) if marks else None
        risky = sum(1 for r in rows if r["stats"]["at_risk"])
        level = core.level_name(db, g["level_id"]) or "no level"
        warn = (f'<span class="pill risk">{risky} at risk</span>' if risky else "")
        cards += f"""<a class="groupcard" href="/groups/{g["id"]}">
  <div class="gc-head">
    <div><div class="gc-name">{E(g["name"])}</div>
      <div class="sub" style="margin:2px 0 0">{E(level)} · {len(rows)} students</div></div>
    {ring(comp)}
  </div>
  <div class="gc-figures">
    <div><span class="k">Average</span><span class="v">{fmt(avg)}</span></div>
    <div><span class="k">Lesson</span><span class="v">{fmt(mark)}</span></div>
    <div><span class="k">Code</span><span class="v mono">{E(g["join_code"])}</span></div>
  </div>
  <div class="gc-foot">{warn}<span class="gc-open">Open class →</span></div>
</a>"""

    invite = ""
    if bot_user:
        links = "".join(
            f'<tr><td>{E(g["name"])}</td><td><input readonly onclick="this.select()" '
            f'value="https://t.me/{bot_user}?start={g["join_code"]}" '
            f'style="width:100%;font-size:12px;font-family:ui-monospace,Menlo,monospace">'
            f'</td></tr>' for g in groups)
        invite = (f'<h2>Invite links</h2><div class="tablewrap"><table>'
                  f'<tr><th>Class</th><th>Send this to that class</th></tr>{links}'
                  f'</table></div>')

    body = f"""<h1>Your classes</h1>
<p class="sub">Click a class to see its students, marks, homework and progress.</p>
<div class="groupgrid">{cards or '<div class="card">No classes yet.</div>'}</div>
<h2>Add a class</h2>
<div class="card"><form method="post" action="/groups/new" class="inline">
<label class="f">Name<input name="name" placeholder="114" required></label>
<label class="f">Level<select name="level_id">{level_opts}</select></label>
<button>Create</button></form></div>
{invite}"""
    return html_response(page("Classes", body, "Groups"))


def group_rows(db, gid, since=None):
    """One row per student: effort, attainment, conduct, and a combined index."""
    rows = []
    for st in db.execute(
        "SELECT * FROM students WHERE group_id=? AND active=1 ORDER BY name", (gid,)
    ).fetchall():
        stats = core.student_stats(db, st["id"])
        marks = core.mark_stats(db, st["id"], since)
        completion = core.live_completion(db, st["id"])
        rows.append({
            "student": st, "stats": stats, "marks": marks,
            "completion": completion,
            "index": core.overall_index(completion, stats["average"], marks["overall"]),
        })
    rows.sort(key=lambda r: (-(r["index"] or 0), r["student"]["name"]))
    return rows


def view_group(req, db, gid):
    g = db.execute("SELECT * FROM groups WHERE id=?", (gid,)).fetchone()
    if not g:
        return not_found()
    query = req["query"]
    tab = (query.get("tab", ["overview"])[0] or "overview")
    period = (query.get("period", ["weekly"])[0] or "weekly")
    if period not in ("daily", "weekly", "monthly"):
        period = "weekly"

    def link(t, label):
        on = " on" if tab == t else ""
        return f'<a class="tab{on}" href="/groups/{gid}?tab={t}">{label}</a>'
    tabs = ('<div class="tabs">' + link("overview", "Overview")
            + link("marks", "Lesson marks") + link("homework", "Homework")
            + link("students", "Students") + "</div>"
            + f'<p class="sub" style="margin-top:-8px">'
            f'<a href="/groups">← all classes</a></p>')

    level = core.level_name(db, g["level_id"])
    head = (f'<h1>{E(g["name"])}</h1><p class="sub">'
            f'{E(level or "no level")} · join code '
            f'<span class="kbd">{E(g["join_code"])}</span></p>{tabs}')

    if tab == "marks":
        return html_response(page(g["name"], head + group_marks(db, g, query), "Groups"))
    if tab == "homework":
        return html_response(page(g["name"], head + group_homework(db, g), "Groups"))
    if tab == "students":
        return html_response(page(g["name"], head + group_students(db, g), "Groups"))
    return html_response(page(g["name"], head + group_overview(db, g, period), "Groups"))


def group_overview(db, g, period):
    rows = group_rows(db, g["id"])
    comps = [r["completion"] for r in rows if r["completion"] is not None]
    avgs = [r["stats"]["average"] for r in rows if r["stats"]["average"] is not None]
    marks = [r["marks"]["overall"] for r in rows if r["marks"]["overall"] is not None]
    lessons = db.execute(
        "SELECT COUNT(DISTINCT day) c FROM lesson_marks m JOIN students s"
        " ON s.id=m.student_id WHERE s.group_id=?", (g["id"],)).fetchone()["c"]
    waiting = db.execute(
        "SELECT COUNT(*) c FROM submissions s JOIN students st ON st.id=s.student_id"
        " WHERE st.group_id=? AND s.status='pending' AND s.draft=0", (g["id"],)
    ).fetchone()["c"]
    comp = round(sum(comps) / len(comps)) if comps else 0

    def plink(p, label):
        on = " on" if period == p else ""
        return (f'<a class="tab{on}" href="/groups/{g["id"]}?period={p}">{label}</a>')
    switch = ('<div class="tabs">' + plink("daily", "Daily") + plink("weekly", "Weekly")
              + plink("monthly", "Monthly") + "</div>")
    limit = {"daily": 14, "weekly": 8, "monthly": 6}[period]
    periods = core.group_periods(db, g["id"], period, limit)

    # a sentence a human can read, before any chart
    trend = ""
    scored = [p for p in periods if p["score"] is not None]
    if len(scored) >= 2:
        change = scored[-1]["score"] - scored[0]["score"]
        word = "up" if change > 0.2 else ("down" if change < -0.2 else "steady")
        trend = (f" Scores are {word}"
                 + (f" {abs(round(change, 1))} points" if word != "steady" else "")
                 + f" over the last {len(scored)} {period[:-2] if period.endswith('ly') else period}s.")
    risky = [r for r in rows if r["stats"]["at_risk"]]
    summary = (f"{len(rows)} students, {comp}% of homework in."
               + trend
               + (f" {len(risky)} need attention: "
                  + ", ".join(E(r["student"]["name"]) for r in risky[:4]) + "."
                  if risky else " Nobody is flagged."))

    student_rows = ""
    for i, r in enumerate(rows, 1):
        st, s2, m = r["student"], r["stats"], r["marks"]
        medal = {1: "&#129351;", 2: "&#129352;", 3: "&#129353;"}.get(i, str(i) + ".")
        cpct = r["completion"] if r["completion"] is not None else 0
        bar = (f'<div class="pbar" style="width:96px"><i style="width:{cpct}%;'
               f'background:{bar_colour(cpct)}"></i></div>')
        flag = '<span class="pill risk">at risk</span>' if s2["at_risk"] else ""
        ptok = core.parent_token(db, st["id"])
        student_rows += (
            f'<tr><td>{medal}</td>'
            f'<td><a href="/students/{st["id"]}">{E(st["name"])}</a> {flag}</td>'
            f'<td><strong>{fmt(r["index"])}</strong></td>'
            f'<td>{bar}</td><td>{cpct}%</td>'
            f'<td>{score_pill(s2["average"])}</td>'
            f'<td>{fmt(m["overall"])}</td><td>{s2["missed"]}</td>'
            f'<td><a class="mini" href="/p/{E(ptok)}">Parent report</a></td></tr>')

    return f"""<div class="grid">
{stat("Students", len(rows))}{stat("Homework done", str(comp) + "%")}
{stat("Average score", fmt(round(sum(avgs) / len(avgs), 2) if avgs else None), "/10")}
{stat("Lesson mark", fmt(round(sum(marks) / len(marks), 2) if marks else None), "/5")}
{stat("To grade", waiting)}</div>
<div class="card"><p style="margin:0">{summary}</p></div>

<div class="quicklinks">
  <a class="quick" href="/groups/{g["id"]}?tab=marks">
    <strong>Mark today's lesson</strong>
    <span class="sub">Punctuality, behaviour, participation · {lessons} lessons recorded</span></a>
  <a class="quick" href="/groups/{g["id"]}?tab=homework">
    <strong>Homework for this class</strong>
    <span class="sub">Edit, close or delete what you have set</span></a>
  <a class="quick" href="/queue">
    <strong>Grade waiting work</strong>
    <span class="sub">{waiting} piece(s) across all classes</span></a>
</div>

<h2>How the class is doing</h2>
{switch}
<div class="card">{charts.period_bars(periods)}
<div class="legend"><span><i style="background:var(--accent)"></i>homework score /10</span>
<span><i style="background:var(--ink-3)"></i>lesson mark /5, doubled to share the axis</span>
</div></div>

<h2>Live standing</h2>
<p class="sub">Index out of 100: half homework done, a quarter average score,
a quarter lesson marks. Click a name for their full record, or send a parent the
report link.</p>
<div class="tablewrap"><table><tr><th>#</th><th>Student</th><th>Index</th>
<th>Homework</th><th></th><th>Average</th><th>Lesson</th><th>Missed</th><th></th></tr>
{student_rows or '<tr><td colspan=9 class="sub">Nobody has joined this class yet.</td></tr>'}
</table></div>
<div class="card">{charts.bars_h([(r["student"]["name"], r["index"],
    (r["completion"] or 0) < 50) for r in rows])}</div>"""


def group_students(db, g):
    rows = group_rows(db, g["id"])
    out = ""
    for r in rows:
        st, s2, m = r["student"], r["stats"], r["marks"]
        spark = charts.sparkline([t["score"] for t in s2["timeline"] if t["score"] is not None])
        flag = '<span class="pill risk">at risk</span>' if s2["at_risk"] else ""
        comp = f'{r["completion"]}%' if r["completion"] is not None else "—"
        out += (f'<tr><td><a href="/students/{st["id"]}">{E(st["name"])}</a> {flag}</td>'
                f'<td><strong>{fmt(r["index"])}</strong></td>'
                f'<td>{comp}</td><td>{score_pill(s2["average"])}</td>'
                f'<td>{fmt(m["punctuality"])}</td><td>{fmt(m["behaviour"])}</td>'
                f'<td>{fmt(m["participation"])}</td>'
                f'<td>{s2["missed"]}</td><td>{spark}</td>'
                f'<td><form method="post" action="/students/{st["id"]}/pause">'
                f'<button class="ghost">Pause</button></form></td>'
                f'<td><form method="post" action="/students/{st["id"]}/delete"'
                f' onsubmit="return confirm(\'Remove {E(st["name"])} and all their work'
                f' for good? This cannot be undone.\')">'
                f'<button class="ghost danger">Remove</button></form></td></tr>')

    paused = ""
    for st in db.execute(
        "SELECT * FROM students WHERE group_id=? AND active=0 ORDER BY name", (g["id"],)
    ).fetchall():
        paused += (f'<tr><td>{E(st["name"])}</td>'
                   f'<td><form method="post" action="/students/{st["id"]}/resume">'
                   f'<button class="ghost">Bring back</button></form></td>'
                   f'<td><form method="post" action="/students/{st["id"]}/delete"'
                   f' onsubmit="return confirm(\'Remove {E(st["name"])} and all their'
                   f' work for good?\')">'
                   f'<button class="ghost danger">Remove</button></form></td></tr>')
    paused_block = ""
    if paused:
        paused_block = (f'<h2>Paused</h2><p class="sub">Out of the standings, the '
                        f'reminders and their own page until you bring them back.</p>'
                        f'<div class="tablewrap"><table><tr><th>Student</th><th></th>'
                        f'<th></th></tr>{paused}</table></div>')

    return f"""<h2>Students</h2>
<p class="sub">Index out of 100. Marks are averages out of 5 across every lesson recorded.
<strong>Pause</strong> keeps everything but takes them out of the class;
<strong>Remove</strong> deletes them and their work for good.</p>
<div class="tablewrap"><table><tr><th>Student</th><th>Index</th><th>Done</th>
<th>Average</th><th>Punct.</th><th>Behav.</th><th>Partic.</th><th>Missed</th>
<th>Trend</th><th></th><th></th></tr>
{out or '<tr><td colspan=11 class="sub">Nobody has joined yet.</td></tr>'}</table></div>
{paused_block}"""


def group_marks(db, g, query):
    day = (query.get("day", [None])[0] or
           core.local_day(core.now(), core.load_config()))
    existing = core.marks_on(db, g["id"], day)
    students = db.execute(
        "SELECT * FROM students WHERE group_id=? AND active=1 ORDER BY name", (g["id"],)
    ).fetchall()

    def picker(sid, field, value):
        opts = "".join(
            f'<option value="{n}"{" selected" if value == n else ""}>{n}</option>'
            for n in range(core.MARK_MAX, 0, -1))
        blank = '<option value=""{}>—</option>'.format(" selected" if not value else "")
        return (f'<select name="{field}_{sid}" class="mark">{blank}{opts}</select>')

    rows = ""
    for st in students:
        row = existing.get(st["id"])
        cells = "".join(
            f'<td>{picker(st["id"], f, row[f] if row else None)}</td>'
            for f in core.MARK_FIELDS)
        rows += (f'<tr><td>{E(st["name"])}</td>{cells}'
                 f'<td><input name="note_{st["id"]}" value="{E((row["note"] if row else "") or "")}"'
                 f' placeholder="optional" style="width:100%"></td></tr>')

    history = ""
    for h in db.execute(
        "SELECT m.day, COUNT(*) n, AVG((COALESCE(m.punctuality,0)+COALESCE(m.behaviour,0)"
        "+COALESCE(m.participation,0))/3.0) avg FROM lesson_marks m"
        " JOIN students s ON s.id=m.student_id WHERE s.group_id=?"
        " GROUP BY m.day ORDER BY m.day DESC LIMIT 12", (g["id"],)
    ).fetchall():
        history += (f'<tr><td><a href="/groups/{g["id"]}?tab=marks&amp;day={h["day"]}">'
                    f'{E(h["day"])}</a></td><td>{h["n"]} student(s)</td>'
                    f'<td>{round(h["avg"], 2)}/5</td></tr>')

    return f"""<h2>Marks for {E(day)}</h2>
<p class="sub">Give each student 1 to 5 for how they were in the lesson. Saving again
on the same date replaces what is there.</p>
<div class="card"><form method="post" action="/groups/{g["id"]}/marks">
<input type="hidden" name="day" value="{E(day)}">
<div class="tablewrap"><table><tr><th>Student</th><th>Punctuality</th><th>Behaviour</th>
<th>Participation</th><th>Note</th></tr>
{rows or '<tr><td colspan=5 class="sub">Nobody in this class yet.</td></tr>'}</table></div>
<div class="inline" style="margin-top:12px">
<label class="f">Lesson date<input type="date" name="day2" value="{E(day)}"></label>
<button>Save marks</button></div></form></div>
<h2>Lessons recorded</h2>
<div class="tablewrap"><table><tr><th>Date</th><th>Marked</th><th>Class average</th></tr>
{history or '<tr><td colspan=3 class="sub">No lessons marked yet.</td></tr>'}</table></div>"""


def group_homework(db, g):
    rows = ""
    for a in db.execute(
        "SELECT * FROM assignments WHERE group_id=? ORDER BY closed,"
        " COALESCE(due_at, created_at) DESC, id DESC", (g["id"],)
    ).fetchall():
        got = db.execute(
            "SELECT COUNT(*) c FROM submissions WHERE assignment_id=? AND draft=0",
            (a["id"],)).fetchone()["c"]
        total = db.execute(
            "SELECT COUNT(*) c FROM students WHERE group_id=? AND active=1",
            (g["id"],)).fetchone()["c"]
        if a["closed"]:
            state = '<span class="pill mute">closed</span>'
        elif not a["published"]:
            state = '<span class="pill mute">draft</span>'
        elif not core.still_open(a["due_at"]):
            state = '<span class="pill watch">deadline passed</span>'
        else:
            state = '<span class="pill">open</span>'
        due, due_time = core.deadline_parts(a["due_at"])
        rows += f"""<tr><td>
  <form method="post" action="/assignments/{a["id"]}/edit" class="inline">
    <input name="title" value="{E(a["title"])}" style="min-width:210px">
    <input type="date" name="due" value="{E(due)}">
    <input type="time" name="due_time" value="{E(due_time)}" step="60">
    <button class="ghost">Save</button>
  </form></td>
  <td>{state}</td><td>{got}/{total}</td>
  <td><form method="post" action="/assignments/{a["id"]}/{"open" if a["closed"] else "close"}">
      <button class="ghost">{"Reopen" if a["closed"] else "Close"}</button></form></td>
  <td><form method="post" action="/assignments/{a["id"]}/delete"
        onsubmit="return confirm('Delete this homework? Student work is kept but unassigned.')">
      <button class="ghost">Delete</button></form></td></tr>"""
    last = core.last_homework_batch(db, g["id"])
    if last:
        when, last_time = core.deadline_parts(
            last[0]["due_at"] or last[0]["created_at"])
        titles = ", ".join(a["title"] for a in last[:3])
        if len(last) > 3:
            titles += " and %d more" % (len(last) - 3)
        repeat = f"""<div class="card">
  <form method="post" action="/groups/{g["id"]}/repeat" class="inline">
    <div style="flex:1;min-width:220px">
      <div style="font-weight:600">Set the same homework again</div>
      <div class="sub" style="margin:2px 0 0">{E(titles)} — last due {E(when)}</div>
    </div>
    <label class="f" style="margin:0">New deadline
      <input type="date" name="due" value="{E(core.shift_days(when, 7))}" required></label>
    <label class="f" style="margin:0">at
      <input type="time" name="due_time" value="{E(last_time or '23:59')}" step="60"></label>
    <label class="check"><input type="checkbox" name="announce" value="1" checked>
      <span>Tell students</span></label>
    <button>Repeat {len(last)} task{"" if len(last) == 1 else "s"}</button>
  </form></div>"""
    else:
        repeat = ""

    return f"""<h2>Homework set for this class</h2>
<p class="sub">Edit the title or deadline and press Save. Closing hides it from students
but keeps the scores; deleting keeps the students' work and detaches it.</p>
{repeat}
<div class="tablewrap"><table><tr><th>Homework</th><th>State</th><th>In</th>
<th></th><th></th></tr>
{rows or '<tr><td colspan=5 class="sub">Nothing set yet.</td></tr>'}</table></div>"""


def view_student(req, db, sid):
    s = db.execute("SELECT * FROM students WHERE id=?", (sid,)).fetchone()
    if not s:
        return not_found()
    st = core.student_stats(db, sid)

    band = []
    for t in st["timeline"]:
        r = db.execute(
            "SELECT AVG(score) a FROM submissions WHERE assignment_id=? AND status='graded'",
            (t["assignment_id"],),
        ).fetchone()
        band.append(round(r["a"], 2) if r["a"] is not None else None)

    hist = ""
    for t in reversed(st["timeline"]):
        if t["submission_id"]:
            sub = db.execute(
                "SELECT * FROM submissions WHERE id=?", (t["submission_id"],)
            ).fetchone()
            tags = [
                r["label"]
                for r in db.execute(
                    "SELECT label FROM tags JOIN submission_tags ON tags.id=tag_id"
                    " WHERE submission_id=?",
                    (sub["id"],),
                ).fetchall()
            ]
            detail = " · ".join(filter(None, [", ".join(tags), sub["note"] or ""]))
            state = score_pill(t["score"]) if t["score"] is not None else '<span class="pill mute">pending</span>'
        else:
            detail, state = "", '<span class="pill risk">not submitted</span>'
        hist += (
            f'<tr><td>{E(t["title"])}</td><td>{state}</td>'
            f'<td class="sub">{E(detail)}</td></tr>'
        )

    groups = db.execute("SELECT * FROM groups WHERE archived=0 ORDER BY name").fetchall()
    opts = "".join(
        f'<option value="{g["id"]}"{" selected" if g["id"]==s["group_id"] else ""}>{E(g["name"])}</option>'
        for g in groups
    )
    comp = f'{st["completion"]}%' if st["completion"] is not None else "—"
    trend = f'{st["trend"]:+g}' if st["trend"] is not None else "—"

    body = f"""<h1>{E(s["name"])}</h1>
<p class="sub">{E(group_name(db, s["group_id"]))} · language {E(s["lang"])}</p>
<div class="grid">{stat("Average", fmt(st["average"]), "/10")}
{stat("Last 3", fmt(st["last3"]), "/10")}{stat("Completion", comp)}
{stat("Trend", trend)}</div>
<h2>Progress</h2>
<div class="card">{charts.score_line(st["timeline"], band=band)}
<div class="legend"><span><i style="background:var(--accent)"></i>rolling average of 3</span>
<span><i style="background:var(--band)"></i>group average</span>
<span style="color:var(--warn)">✕ not submitted</span></div></div>
<h2>History</h2>
<div class="tablewrap"><table><tr><th>Assignment</th><th>Score</th><th>Feedback</th></tr>
{hist or '<tr><td colspan=3 class="sub">No assignments yet.</td></tr>'}</table></div>
<h2>Report for parents</h2>
<div class="card">
<p class="sub" style="margin:0 0 8px">A read-only page you can send to a parent:
scores, homework, and how they are in class. No password, and nothing they can change.</p>
<div style="display:flex;gap:8px">
  <input id="plink2" readonly value="/p/{E(core.parent_token(db, s['id']))}"
         style="flex:1;font-family:ui-monospace,Menlo,monospace;font-size:13px">
  <button type="button" class="ghost" onclick="copy2()">Copy</button>
  <a class="ghost" style="align-self:center" href="/p/{E(core.parent_token(db, s['id']))}"
     target="_blank">Preview</a>
</div></div>
<script>
const b2 = document.getElementById('plink2');
b2.value = location.origin + b2.value;
function copy2() {{ b2.select(); navigator.clipboard.writeText(b2.value); }}
</script>
<h2>Their private link</h2>
<div class="card">
<p class="sub" style="margin:0 0 8px">Send this to {E(s["name"])} only. It opens their own
upload page — no password, and it shows nobody else's work.</p>
<div style="display:flex;gap:8px">
  <input id="plink" readonly value="/s/{E(core.student_token(db, s['id']))}"
         style="flex:1;font-family:ui-monospace,Menlo,monospace;font-size:13px">
  <button type="button" class="ghost" onclick="copyLink()">Copy</button>
</div></div>
<script>
const box = document.getElementById('plink');
box.value = location.origin + box.value;
function copyLink() {{
  box.select(); navigator.clipboard.writeText(box.value);
}}
</script>
<h2>Parent link</h2>
<div class="card">
<p class="sub" style="margin:0 0 8px">Optional. A parent who taps this gets a weekly
summary of {E(s["name"])}'s completion and average — nothing else.</p>
<input readonly id="klink" value="/start P{E(core.parent_token(db, s['id']))}"
       style="width:100%;font-family:ui-monospace,Menlo,monospace;font-size:13px">
</div>
<script>
const kb = document.getElementById('klink');
const botUser = "{E(core.meta_get(db, 'bot_username', '') or '')}";
kb.value = botUser ? "https://t.me/" + botUser + "?start=P{E(core.parent_token(db, s['id']))}"
                   : "Run the bot once to generate this link";
</script>
<h2>Settings</h2>
<div class="card"><form method="post" action="/students/{s['id']}/update" class="inline">
<label class="f">Name<input name="name" value="{E(s['name'])}"></label>
<label class="f">Group<select name="group_id">{opts}</select></label>
<button>Save</button></form></div>"""
    return html_response(page(s["name"], body, "Groups"))


def batch_block(db, r, cfg, open_only):
    """One homework batch: what it is, how it is going, and how to manage it."""
    gid, due = r["group_id"], r["due_at"]
    items = core.set_items(db, gid, due)
    if not items:
        return ""
    closed = r["shut"] == 1                       # every item closed
    draft = r["pubmax"] == 0                      # nothing published yet
    if open_only and closed:
        return ""

    day, clock = core.deadline_parts(due, cfg)
    when = f"{day} at {clock}" if day else "no deadline"
    got, total = core.set_received(db, gid, due)
    graded = core.set_graded_count(db, gid, due)

    state = ('<span class="pill mute">closed</span>' if closed
             else '<span class="pill mute">draft</span>' if draft
             else '<span class="pill">open</span>')
    if r["shut"] != r["shutmax"] or (not draft and r["pub"] != r["pubmax"]):
        state += ' <span class="pill mute">mixed</span>'

    key = f'<input type="hidden" name="group_id" value="{gid}">' \
          f'<input type="hidden" name="due" value="{E(due or "")}">'
    def form(action, label, cls="ghost", confirm=None):
        ask = f' onsubmit="return confirm({json.dumps(confirm)})"' if confirm else ""
        return (f'<form method="post" action="/assignments/batch/{action}"{ask}>'
                f'{key}<button class="{cls}">{label}</button></form>')

    buttons = ""
    if draft:
        buttons += form("publish", "Publish all", "")
    elif closed:
        buttons += form("open", "Reopen all")
    else:
        buttons += form("close", "Close all")
    warn = ("Delete all %d item(s)? %d marked piece(s) stay with the student "
            "and keep their score - they just stop being linked to this homework."
            % (len(items), graded)) if graded else \
           "Delete all %d item(s)? Nothing has been handed in." % len(items)
    buttons += form("delete", "Delete all", "ghost danger", warn)

    rows = ""
    for a in items:
        n = db.execute("SELECT COUNT(*) c FROM submissions WHERE assignment_id=?",
                       (a["id"],)).fetchone()["c"]
        if a["closed"]:
            act = (f'<form method="post" action="/assignments/{a["id"]}/open">'
                   f'<button class="linky">reopen</button></form>')
        elif not a["published"]:
            act = (f'<form method="post" action="/assignments/{a["id"]}/publish">'
                   f'<button class="linky">publish</button></form>')
        else:
            act = (f'<form method="post" action="/assignments/{a["id"]}/close">'
                   f'<button class="linky">close</button></form>')
        rows += (f'<tr><td>{E(a["title"])}</td>'
                 f'<td class="sub">{E(a["task_type"])}'
                 f'{" &middot; criteria" if a["rubric"] else ""}</td>'
                 f'<td class="sub">{n} in</td>'
                 f'<td class="rowacts">{act}'
                 f'<form method="post" action="/assignments/{a["id"]}/delete"'
                 f' onsubmit="return confirm({json.dumps("Delete " + a["title"] + "?")})">'
                 f'<button class="linky danger">delete</button></form></td></tr>')

    edit = f"""<details><summary>Edit this homework</summary>
<form method="post" action="/assignments/batch/edit" class="inline" style="margin-top:10px">
{key}
<label class="f">New deadline<input type="date" name="new_due" value="{E(day)}"></label>
<label class="f">at<input type="time" name="new_time" value="{E(clock or "23:59")}" step="60"></label>
<label class="f" style="justify-content:flex-end">&nbsp;<button>Move the deadline</button></label>
</form>
<p class="sub" style="margin:8px 0 0">Moves every item in this batch. A piece already
handed in after the old deadline stops counting as late.</p>
<div class="tablewrap" style="margin-top:10px"><table>
<tr><th>Item</th><th>Type</th><th>Sent</th><th></th></tr>{rows}</table></div>
</details>"""

    return f"""<div class="card batch">
  <div class="batchhead">
    <div><strong>{E(group_name(db, gid))}</strong> &mdash; {E(when)} {state}
      <div class="sub">{len(items)} item(s) &middot; {got} of {total} students have sent
        something{" &middot; " + str(graded) + " marked" if graded else ""}</div></div>
    <div class="batchacts">{buttons}</div>
  </div>
  {edit}
</div>"""


def view_assignments(req, db):
    groups = db.execute("SELECT * FROM groups WHERE archived=0 ORDER BY name").fetchall()
    cfg = core.load_config()
    show_closed = req["query"].get("closed", [""])[0] == "1"
    sets = core.all_sets(db)
    blocks = "".join(batch_block(db, r, cfg, not show_closed) for r in sets)
    shut = sum(1 for r in sets if r["shut"] == 1)
    opts = "".join(f'<option value="{g["id"]}">{E(g["name"])}</option>' for g in groups)
    body = f"""<h1>Assignments</h1>
<p class="sub">Open assignments are what the bot offers students when they send a photo.</p>
<h2>Set homework</h2>
<div class="card"><form method="post" action="/assignments/list">
<div class="inline" style="margin-bottom:10px">
<label class="f">Group<select name="group_id">{opts}</select></label>
<label class="f">Type<select name="task_type">
<option value="other">Other</option><option value="task2">Task 2</option>
<option value="task1">Task 1</option></select></label>
<label class="f">Due<input type="date" name="due"></label>
<label class="f">at<input type="time" name="due_time" value="23:59" step="60"></label>
<label class="f" style="justify-content:flex-end">&nbsp;
<span style="font-size:13px;color:var(--ink)">
<input type="checkbox" name="publish" value="1" checked> open to students now</span></label>
<label class="f" style="justify-content:flex-end">&nbsp;
<span style="font-size:13px;color:var(--ink)">
<input type="checkbox" name="announce" value="1" checked> tell them in Telegram</span></label>
<label class="f" style="justify-content:flex-end">&nbsp;
<span style="font-size:13px;color:var(--ink)" title="Task response, coherence, vocabulary, grammar">
<input type="checkbox" name="rubric" value="1"> mark on the four criteria</span></label>
</div>
<label class="f">One item per line &mdash; numbering is optional
<textarea name="items" rows="6" style="width:100%" required
placeholder="Task 2 essay &ndash; Technology&#10;Grammar handout page 45&#10;Vocabulary unit 4 &ndash; write 10 sentences"></textarea></label>
<div style="margin-top:10px"><button onclick="this.disabled=true;this.form.submit()">
Set the homework</button></div></form>
<p class="sub" style="margin:10px 0 0">One line makes one piece of homework, several lines
make several &mdash; students pick which one they are sending and each gets its own score.
Without &ldquo;open to students now&rdquo; it is saved as a draft: nobody sees it until you
press Publish below.</p></div>
<h2>Homework you have set</h2>
<p class="sub">Everything posted together is one piece of homework here, the way you set
it. Close, move or delete the whole batch, or open it to deal with a single item.
{shut} batch(es) closed &mdash;
<a href="/assignments?closed={0 if show_closed else 1}">{"hide" if show_closed else "show"} them</a>.</p>
{blocks or '<div class="card"><p style="margin:0" class="sub">Nothing set yet.</p></div>'}"""
    return html_response(page("Assignments", body, "Assignments"))


def view_roster(req, db):
    """Everyone, with the things you actually do to a student on the same page."""
    q = (req["query"].get("q", [""])[0] or "").strip()
    gid = (req["query"].get("group", [""])[0] or "").strip()
    gid = int(gid) if gid.isdigit() else None
    show = (req["query"].get("show", ["active"])[0] or "active")
    groups = db.execute("SELECT * FROM groups WHERE archived=0 ORDER BY name").fetchall()
    opts = "".join(f'<option value="{g["id"]}">{E(g["name"])}</option>' for g in groups)

    where, args = [], []
    if gid:
        where.append("group_id=?"); args.append(gid)
    if show == "active":
        where.append("active=1")
    elif show == "paused":
        where.append("active=0")
    if q:
        where.append("name LIKE ?"); args.append("%" + q + "%")
    sql = "SELECT * FROM students"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY active DESC, name"
    people = db.execute(sql, args).fetchall()

    rows = ""
    for s_ in people:
        st = core.student_stats(db, s_["id"])
        seen, days = core.last_active(db, s_["id"])
        if days is None:
            quiet = '<span class="pill risk">never</span>'
        elif days >= 14:
            quiet = f'<span class="pill risk">{days}d ago</span>'
        elif days >= 7:
            quiet = f'<span class="pill watch">{days}d ago</span>'
        else:
            quiet = f'<span class="sub">{days}d ago</span>'
        move = "".join(
            f'<option value="{g["id"]}"{" selected" if g["id"] == s_["group_id"] else ""}>'
            f'{E(g["name"])}</option>' for g in groups)
        if s_["active"]:
            hold = (f'<form method="post" action="/students/{s_["id"]}/pause">'
                    f'<button class="linky">pause</button></form>')
        else:
            hold = (f'<form method="post" action="/students/{s_["id"]}/resume">'
                    f'<button class="linky">resume</button></form>')
        nobot = "" if s_["telegram_id"] else ' <span class="pill mute">no bot</span>'
        warn = ("Delete %s for good? Every piece of homework, mark, lesson record and "
                "word they have practised goes with them. This cannot be undone - "
                "use pause instead if they may come back." % s_["name"])
        rows += (
            f'<tr>'
            f'<td><input type="checkbox" class="pick" name="id" value="{s_["id"]}"'
            f' form="bulk"></td>'
            f'<td><a href="/students/{s_["id"]}">{E(s_["name"])}</a>{nobot}</td>'
            f'<td><form method="post" action="/students/{s_["id"]}/move" class="movef">'
            f'<select name="group_id" onchange="this.form.submit()">{move}</select>'
            f'</form></td>'
            f'<td>{score_pill(st["average"])}</td>'
            f'<td>{st["graded_count"]}</td><td>{st["missed"]}</td>'
            f'<td>{quiet}</td>'
            f'<td class="rowacts">{hold}'
            f'<form method="post" action="/students/{s_["id"]}/delete"'
            f' onsubmit="return confirm({json.dumps(warn)})">'
            f'<button class="linky danger">delete</button></form></td></tr>')

    def tab(href, label, on):
        return f'<a class="tab{" on" if on else ""}" href="{href}">{E(label)}</a>'
    base = f"?show={show}" if show != "active" else "?"
    tabs = ('<div class="tabs">'
            + tab(f"/roster?show={show}", "All classes", gid is None)
            + "".join(tab(f'/roster?group={g["id"]}&show={show}', g["name"], gid == g["id"])
                      for g in groups) + "</div>")
    states = ('<div class="tabs">'
              + tab(f"/roster{'?group=%d&' % gid if gid else '?'}show=active", "Active", show == "active")
              + tab(f"/roster{'?group=%d&' % gid if gid else '?'}show=paused", "Paused", show == "paused")
              + tab(f"/roster{'?group=%d&' % gid if gid else '?'}show=all", "Everyone", show == "all")
              + "</div>")

    site = core.meta_get(db, "site_url")
    where_note = (f'Student links use <code>{E(site)}</code>' if site
                  else '<span style="color:var(--warn)">The public address has not been '
                       'detected yet &mdash; reload this page once on the real address.</span>')

    body = f"""<h1>Students</h1>
<p class="sub">{len(people)} shown. {where_note}</p>
{tabs}
{states}
<form method="get" action="/roster" class="inline" style="margin:12px 0">
<input type="hidden" name="group" value="{gid or ''}">
<input type="hidden" name="show" value="{E(show)}">
<label class="f">Find<input name="q" id="rq" value="{E(q)}" placeholder="type a name"></label>
<label class="f" style="justify-content:flex-end">&nbsp;<button class="ghost">Search</button></label>
</form>
<form method="post" action="/students/bulk" id="bulk"></form>
<div class="bulkbar" id="bulkbar" hidden>
  <span><b id="npicked">0</b> selected</span>
  <select name="group_id" form="bulk">{opts}</select>
  <button form="bulk" name="do" value="move" class="ghost">Move to this class</button>
  <button form="bulk" name="do" value="pause" class="ghost">Pause them</button>
  <button form="bulk" name="do" value="resume" class="ghost">Resume them</button>
</div>
<div class="tablewrap"><table id="roster"><tr>
<th><input type="checkbox" id="pickall"></th>
<th>Name</th><th>Class</th><th>Average</th><th>Graded</th><th>Missed</th>
<th>Last seen</th><th></th></tr>
{rows or '<tr><td colspan=8 class="sub">Nobody matches.</td></tr>'}</table></div>
<h2 style="margin-top:28px">Add a student by hand</h2>
<div class="card"><form method="post" action="/students/new" class="inline">
<label class="f">Name<input name="name" required placeholder="For someone not on Telegram"></label>
<label class="f">Class<select name="group_id">{opts}</select></label>
<label class="f" style="justify-content:flex-end">&nbsp;<button>Add</button></label>
</form>
<p class="sub" style="margin:10px 0 0">They get their own page link straight away. If they
join through the bot later, that account links up on its own.</p></div>"""
    return html_response(page("Students", body, "Students"))


def act_new_student(req, db):
    f = req["form"]
    core.add_student(db, f.get("name", [""])[0], f.get("group_id", [None])[0])
    return redirect("/roster")


def act_move_student(req, db, sid):
    gid = (req["form"].get("group_id", [""])[0] or "").strip()
    if gid.isdigit():
        core.move_student(db, sid, int(gid))
    return redirect("/roster")


def act_bulk_students(req, db):
    """Do one thing to several students - moving a class up a level, mostly."""
    f = req["form"]
    ids = [int(i) for i in f.get("id", []) if str(i).isdigit()]
    do = (f.get("do", [""])[0] or "").strip()
    gid = (f.get("group_id", [""])[0] or "").strip()
    for sid in ids:
        if do == "move" and gid.isdigit():
            core.move_student(db, sid, int(gid))
        elif do == "pause":
            core.set_student_active(db, sid, False)
        elif do == "resume":
            core.set_student_active(db, sid, True)
    return redirect("/roster")


def view_vocab(req, db):
    groups = db.execute("SELECT * FROM groups WHERE archived=0 ORDER BY name").fetchall()
    rows = ""
    for wl in db.execute(
        "SELECT * FROM word_lists ORDER BY active DESC, created_at DESC"
    ).fetchall():
        n = db.execute("SELECT COUNT(*) c FROM words WHERE list_id=?", (wl["id"],)).fetchone()["c"]
        learners = db.execute(
            "SELECT COUNT(DISTINCT student_id) c FROM word_progress p"
            " JOIN words w ON w.id=p.word_id WHERE w.list_id=?", (wl["id"],)
        ).fetchone()["c"]
        rows += (
            f'<tr><td><a href="/vocab/{wl["id"]}">{E(wl["title"])}</a></td>'
            f'<td>{E(group_name(db, wl["group_id"]))}</td><td>{n}</td><td>{learners}</td>'
            f'<td>{"active" if wl["active"] else "off"}</td></tr>'
        )
    opts = "".join(f'<option value="{g["id"]}">{E(g["name"])}</option>' for g in groups)
    body = f"""<h1>Vocabulary</h1>
<p class="sub">Students practise these with <span class="kbd">/vocab</span> in the bot.
Words they get wrong come back the next day; words they know come back later and later.</p>
<div class="card"><form method="post" action="/vocab/new">
<div class="inline" style="margin-bottom:10px">
<label class="f">List title<input name="title" placeholder="Unit 15" required></label>
<label class="f">Book<input name="source" placeholder="4000 Essential Words 1"></label>
<label class="f">Unit<input name="unit" placeholder="15" style="width:80px"></label>
<label class="f">Group<select name="group_id">{opts}</select></label></div>
<label class="f">One per line: <code>word = meaning</code>, or
<code>word = meaning | example sentence</code> to unlock fill-the-gap
<textarea name="words" rows="8" style="width:100%"
placeholder="abandon = tashlab ketmoq / покидать | They had to abandon the car.&#10;absolute = mutlaq / абсолютный"></textarea></label>
<div style="margin-top:10px"><button>Create list</button></div></form></div>
<div class="tablewrap"><table><tr><th>List</th><th>Group</th><th>Words</th>
<th>Practising</th><th>Status</th></tr>
{rows or '<tr><td colspan=5 class="sub">No word lists yet.</td></tr>'}</table></div>"""
    return html_response(page("Vocabulary", body, "Vocabulary"))


def view_word_list(req, db, wid):
    wl = db.execute("SELECT * FROM word_lists WHERE id=?", (wid,)).fetchone()
    if not wl:
        return not_found()
    rows = ""
    for w in db.execute("SELECT * FROM words WHERE list_id=? ORDER BY ord, id", (wid,)).fetchall():
        agg = db.execute(
            "SELECT COUNT(*) n, SUM(CASE WHEN streak>=3 THEN 1 ELSE 0 END) known,"
            " SUM(seen) seen, SUM(correct) correct FROM word_progress WHERE word_id=?",
            (w["id"],),
        ).fetchone()
        acc = (round(100 * agg["correct"] / agg["seen"]) if agg["seen"] else None)
        hard = acc is not None and acc < 60
        flag = '<span class="pill risk">hard</span>' if hard else ""
        shown = "—" if acc is None else f"{acc}%"
        gap = "&#10003;" if w["example"] else '<span class="sub">—</span>'
        rows += (
            f'<tr><td>{E(w["term"])}</td><td class="sub">{E(w["translation"])}</td>'
            f'<td>{gap}</td><td>{agg["known"] or 0}</td><td>{shown}</td><td>{flag}</td></tr>'
        )
    body = f"""<h1>{E(wl["title"])}</h1>
<p class="sub">{E(group_name(db, wl["group_id"]))} · the “hard” flag marks words the
group answers correctly less than 60% of the time — worth reteaching.</p>
<div class="card"><form method="post" action="/vocab/{wid}/add" class="inline">
<label class="f" style="flex:1">Add more words (one per line, <code>word = meaning</code>)
<textarea name="words" rows="3" style="width:100%"></textarea></label>
<button>Add</button></form></div>
<details class="adder"><summary>Replace every word in this list</summary>
<div class="card"><form method="post" action="/vocab/{wid}/replace">
<label class="f">One per line, <code>word = meaning</code>, or
<code>word = meaning | example sentence</code>. What students already know
about a word is kept as long as the word itself stays on the list.
<textarea name="words" rows="6" style="width:100%"></textarea></label>
<div style="margin-top:10px"><button>Replace the list</button></div>
</form></div></details>
<div class="tablewrap"><table><tr><th>Word</th><th>Meaning</th><th>Gap mode</th>
<th>Students who know it</th><th>Group accuracy</th><th></th></tr>
{rows or '<tr><td colspan=5 class="sub">Empty list.</td></tr>'}</table></div>"""
    return html_response(page(wl["title"], body, "Vocabulary"))


def parse_words(text):
    """One word per line. Accepts:

        word = meaning
        word = meaning | example sentence
        word <tab> meaning <tab> example sentence

    An example sentence unlocks the fill-the-gap mode for that word.
    """
    out = []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = None
        if "\t" in line:
            parts = [p.strip() for p in line.split("\t")]
        else:
            for sep in (" = ", "=", " - ", " \u2013 ", " \u2014 "):
                if sep in line:
                    head, _, rest = line.partition(sep)
                    parts = [head.strip()] + [p.strip() for p in rest.split("|", 1)]
                    break
        if not parts or len(parts) < 2 or not parts[0] or not parts[1]:
            continue
        term, meaning = parts[0][:80], parts[1][:200]
        example = parts[2][:300] if len(parts) > 2 and parts[2] else None
        out.append((term, meaning, example))
    return out


def act_new_word_list(req, db):
    f = req["form"]
    title = (f.get("title", [""])[0] or "").strip()
    gid = f.get("group_id", [None])[0]
    pairs = parse_words(f.get("words", [""])[0])
    if not title or not pairs:
        return redirect("/vocab")
    wid = db.execute(
        "INSERT INTO word_lists (group_id, title, created_at, source, unit)"
        " VALUES (?,?,?,?,?)",
        (int(gid) if gid else None, title, core.iso(core.now()),
         (f.get("source", [""])[0] or "").strip()[:80] or None,
         (f.get("unit", [""])[0] or "").strip()[:40] or None),
    ).lastrowid
    for i, (term, meaning, example) in enumerate(pairs):
        db.execute("INSERT INTO words (list_id, term, translation, example, ord)"
                   " VALUES (?,?,?,?,?)", (wid, term, meaning, example, i))
    db.commit()
    return redirect(f"/vocab/{wid}")


def act_replace_words(req, db, wid):
    """Put a whole new set of meanings on an existing list.

    Retranslating a list used to mean deleting it and starting again, which
    threw away whatever practice students had already done against those
    words. This keeps the list and swaps its contents, carrying each
    student's progress across to the word of the same name.
    """
    pairs = parse_words(req["form"].get("words", [""])[0])
    if not pairs:
        return redirect(f"/vocab/{wid}")
    was = {r["term"].lower(): r["id"]
           for r in db.execute("SELECT id, term FROM words WHERE list_id=?", (wid,))}
    # the new words have to exist before progress can be moved onto them, and
    # the old ones cannot be deleted until nothing points at them any more
    for i, (term, meaning, example) in enumerate(pairs):
        new_id = db.execute(
            "INSERT INTO words (list_id, term, translation, example, ord)"
            " VALUES (?,?,?,?,?)", (wid, term, meaning, example, i)).lastrowid
        old_id = was.pop(term.lower(), None)
        if old_id is not None:
            db.execute("UPDATE word_progress SET word_id=? WHERE word_id=?",
                       (new_id, old_id))
            db.execute("UPDATE game_questions SET word_id=? WHERE word_id=?",
                       (new_id, old_id))
    keep = [r["id"] for r in db.execute(
        "SELECT id FROM words WHERE list_id=? ORDER BY id DESC LIMIT ?",
        (wid, len(pairs)))]
    marks = ",".join("?" * len(keep))
    db.execute("DELETE FROM word_progress WHERE word_id IN"
               " (SELECT id FROM words WHERE list_id=? AND id NOT IN (%s))" % marks,
               [wid] + keep)
    db.execute("DELETE FROM game_questions WHERE word_id IN"
               " (SELECT id FROM words WHERE list_id=? AND id NOT IN (%s))" % marks,
               [wid] + keep)
    db.execute("DELETE FROM words WHERE list_id=? AND id NOT IN (%s)" % marks,
               [wid] + keep)
    db.commit()
    return redirect(f"/vocab/{wid}")


def act_add_words(req, db, wid):
    pairs = parse_words(req["form"].get("words", [""])[0])
    start = db.execute("SELECT COUNT(*) c FROM words WHERE list_id=?", (wid,)).fetchone()["c"]
    for i, (term, meaning, example) in enumerate(pairs):
        db.execute("INSERT INTO words (list_id, term, translation, example, ord)"
                   " VALUES (?,?,?,?,?)", (wid, term, meaning, example, start + i))
    db.commit()
    return redirect(f"/vocab/{wid}")



# ------------------------------------------------------- student-facing page

_song_cache = {"day": None, "tag": ""}


def song_tag():
    """A <script> naming today's song, or "" on a day nobody set one.

    Looked up once a day rather than once a page: every rendered page carries
    this, and the answer only changes at midnight or when a song is uploaded.
    """
    day = core.local_day(core.now(), core.load_config())
    if _song_cache["day"] == day:
        return _song_cache["tag"]
    db = core.connect()
    try:
        row = core.song_for(db, day)
    finally:
        db.close()
    tag = ""
    if row:
        name = row["title"] or row["original_name"] or "Song of the day"
        if row["artist"]:
            name += " — " + row["artist"]
        stamp = re.sub(r"\D", "", row["created_at"] or "")[-8:]
        tag = ("<script>window.SONG=%s;</script>"
               % json.dumps({"url": "/song?v=" + stamp, "name": name}))
    _song_cache["day"], _song_cache["tag"] = day, tag
    return tag


def forget_song():
    _song_cache["day"] = None


def student_page(title, body):
    """Standalone layout - no teacher navigation, no sign-in."""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{E(title)} · OlimovAzamat</title>
<link rel="stylesheet" href="/static/style.css"></head>
<body><header class="top"><span class="brand"><span class="mark">O</span>OlimovAzamat</span>
<span class="right"><span id="songname" class="songname" hidden></span>
<button type="button" id="musicbtn" class="musicbtn"
  onclick="Music.toggle()" title="Music"></button></span></header>
<main style="max-width:600px">{body}</main>
{song_tag()}
<script src="/static/music.js" defer></script>
<script src="/static/nav.js" defer></script></body></html>"""


def student_shell(s, db, token, tab, body):
    """One page, four tabs, everything the bot can do."""
    level = core.level_name(db, core.level_of(db, s["group_id"]))
    tabs = [("home", "Homework"), ("materials", "Materials"),
            ("progress", "Progress"), ("class", "Class"), ("goal", "My goal"),
            ("profile", "Profile")]
    nav = "".join(
        f'<a class="tab{" on" if tab == key else ""}" '
        f'href="/s/{E(token)}?tab={key}">{label}</a>' for key, label in tabs)
    head = f"""<div class="whoami">
  <div class="avatar">{E((s["name"] or "?").strip()[:1].upper())}</div>
  <div>
    <div class="name">{E(s["name"])}</div>
    <div class="sub" style="margin:0">{E(group_name(db, s["group_id"]))}
      {"· " + E(level) if level else ""}</div>
  </div>
</div>
<div class="tabs stretch">{nav}</div>"""
    return html_response(student_page(s["name"], head + body))


def portal_home(db, s, token, flash):
    st = core.student_stats(db, s["id"])
    opens = [a for a in db.execute(
        "SELECT * FROM assignments WHERE group_id=? AND closed=0 AND published=1"
        " ORDER BY COALESCE(due_at, created_at) DESC, id DESC",
        (s["group_id"],)).fetchall() if core.still_open(a["due_at"])]
    if opens:
        opts = "".join(f'<option value="{a["id"]}">{E(a["title"])}</option>' for a in opens)
        picker = (f'<label class="f">Which task?<select name="assignment_id">{opts}</select></label>'
                  if len(opens) > 1 else
                  f'<input type="hidden" name="assignment_id" value="{opens[0]["id"]}">'
                  f'<p class="sub" style="margin:0 0 10px">For: <strong>'
                  f'{E(opens[0]["title"])}</strong></p>')
    else:
        picker = '<p class="sub" style="margin:0 0 10px">No open task right now.</p>'

    lists = ""
    for due_at, items in core.open_sets(db, s["group_id"], for_student=True):
        prog = core.set_progress(db, s["id"], items)
        left = core.due_in_words(due_at)
        when = (f'{due_at[:10]} · {left}' if due_at else "no deadline")
        rows = ""
        for a in items:
            done = a["id"] in prog["done_ids"]
            rows += (f'<li class="{"done" if done else ""}">'
                     f'<span class="box">{"&#10003;" if done else ""}</span>'
                     f'{E(a["title"])}</li>')
        pct = prog["percent"] or 0
        lists += f"""<div class="card">
  <div class="rowline"><strong>{E(when)}</strong>
    <span class="pill{" risk" if pct < 50 else ""}">{prog["done"]}/{prog["total"]}</span></div>
  <div class="pbar"><i style="width:{pct}%"></i></div>
  <ul class="checklist">{rows}</ul></div>"""
    if not lists:
        lists = '<div class="card"><p style="margin:0">Nothing set at the moment.</p></div>'

    drafts = ""
    for d in db.execute(
        "SELECT s.id, s.assignment_id, a.title, a.due_at,"
        " (SELECT COUNT(*) FROM files f WHERE f.submission_id=s.id) pages"
        " FROM submissions s LEFT JOIN assignments a ON a.id=s.assignment_id"
        " WHERE s.student_id=? AND s.draft=1 ORDER BY s.created_at", (s["id"],)
    ).fetchall():
        drafts += f"""<div class="card">
  <div class="rowline"><strong>{E(d["title"] or "Unassigned")}</strong>
    <span class="pill mute">{d["pages"]} page(s) · not sent</span></div>
  <p class="sub" style="margin:6px 0 10px">Add more photos above, or send it now.</p>
  <div style="display:flex;gap:8px;flex-wrap:wrap">
    <form method="post" action="/s/{E(token)}/finish/{d["id"]}">
      <button>Finish and send</button></form>
    <form method="post" action="/s/{E(token)}/discard/{d["id"]}">
      <button class="ghost">Delete</button></form>
  </div></div>"""
    if drafts:
        drafts = "<h2>Ready to send</h2>" + drafts

    return f"""{flash}
<h2>Send your homework</h2>
<div class="card">
  <form method="post" action="/s/{E(token)}/upload" enctype="multipart/form-data">
    {picker}
    <label class="dropzone">
      <input type="file" name="photo" accept="image/*" multiple required
             onchange="this.closest('.dropzone').classList.add('has');
                       this.nextElementSibling.textContent =
                         this.files.length + ' page(s) chosen';">
      <span class="dz-label">Choose photos of your work</span>
      <span class="dz-hint">Whole page, from directly above, in good light.
      You can attach several pages at once.</span>
    </label>
    <div style="margin-top:12px"><button>Send to teacher</button></div>
  </form>
</div>
{drafts}
<h2>What is left</h2>
{lists}"""


def portal_materials(db, s, token, query):
    level_id = core.level_of(db, s["group_id"])
    if not level_id:
        return ('<div class="card"><p style="margin:0">Your class has no level yet. '
                'Ask your teacher.</p></div>')
    coll = (query.get("c", [None])[0] or "")
    sect = query.get("s", [None])[0]
    unit = query.get("u", [None])[0]
    sect = int(sect) if sect and sect.isdigit() else None
    unit = int(unit) if unit and unit.isdigit() else None
    base = f"/s/{E(token)}?tab=materials"

    if coll not in core.COLLECTIONS:
        counts = core.collection_counts(db, level_id)
        cards = "".join(
            f'<a class="tile" href="{base}&amp;c={key}">'
            f'<div class="tile-title">{E(core.collection_label(key))}</div>'
            f'<div class="sub" style="margin:0">{counts.get(key, 0)} files</div></a>'
            for key in core.COLLECTION_ORDER)
        return f'<h2>Materials</h2><div class="tiles">{cards}</div>'

    crumb = f'<a class="crumb" href="{base}">Materials</a> › {E(core.collection_label(coll))}'

    # the practice shelf is twenty buttons, and each holds a whole test - the
    # paper, its recording and its answers, so nothing has to be cross-referred
    if core.is_test_shelf(coll):
        have = core.units_across(db, level_id, coll)
        if unit is None:
            cards = "".join(
                f'<a class="tile small{"" if n in have else " empty"}" '
                f'href="{base}&amp;c={coll}&amp;u={n}">'
                f'<div class="tile-title">Test {n}</div>'
                f'<div class="sub" style="margin:0">'
                f'{have[n]} file{"" if have.get(n) == 1 else "s"}</div></a>'
                if n in have else
                f'<a class="tile small empty" href="{base}&amp;c={coll}&amp;u={n}">'
                f'<div class="tile-title">Test {n}</div>'
                f'<div class="sub" style="margin:0">empty</div></a>'
                for n in core.tests_in_collection(coll))
            return f'<p class="sub">{crumb}</p><div class="tiles">{cards}</div>'
        rows = core.files_in_test(db, level_id, coll, unit)
        order = {name: i for i, name in enumerate(core.sections(coll))}
        rows = sorted(rows, key=lambda m: (order.get(m["category"], 99), m["title"]))
        crumb += f' › <a class="crumb" href="{base}&amp;c={coll}">Test {unit}</a>'
        if not rows:
            return (f'<p class="sub">{crumb}</p><div class="card">'
                    f'<p style="margin:0">Nothing here yet.</p></div>')
        parts = ""
        for m in rows:
            kind = m["category"] or "File"
            src = f'/materials/{m["id"]}/file?s={E(token)}'
            player = (f'<audio controls preload="none" class="voice" src="{src}"></audio>'
                      if (m["mime"] or "").startswith("audio") else "")
            parts += (f'<div class="testfile"><div>'
                      f'<span class="pill mute">{E(kind)}</span> '
                      f'<a href="{src}">{E(m["title"])}</a>'
                      f'<div class="sub">{E(core.human_size(m["size"]))}</div></div>'
                      f'{player}</div>')
        return f'<p class="sub">{crumb}</p><div class="card">{parts}</div>'

    if query.get("audio") and sect is None:
        counts = core.level_counts(db, level_id, coll)
        names = core.sections(coll)
        cards = ""
        for label, section in (("Class book", "Listening audios"),
                               ("Work book", "Workbook audios")):
            if section in names:
                cards += (f'<a class="tile" href="{base}&amp;c={coll}'
                          f'&amp;s={names.index(section)}">'
                          f'<div class="tile-title">{E(label)}</div>'
                          f'<div class="sub" style="margin:0">'
                          f'{counts.get(section, 0)} files</div></a>')
        return (f'<p class="sub">{crumb} › Listening audios</p>'
                f'<div class="tiles">{cards}</div>')
    if sect is None:
        counts = core.level_counts(db, level_id, coll)
        cards = ""
        for i, name in enumerate(core.sections(coll)):
            if name == "Workbook audios":
                continue                     # reached through Listening audios
            if name == "Listening audios":
                total = counts.get(name, 0) + counts.get("Workbook audios", 0)
                cards += (f'<a class="tile" href="{base}&amp;c={coll}&amp;audio=1">'
                          f'<div class="tile-title">{E(name)}</div>'
                          f'<div class="sub" style="margin:0">{total} files</div></a>')
                continue
            cards += (f'<a class="tile" href="{base}&amp;c={coll}&amp;s={i}">'
                      f'<div class="tile-title">{E(name)}</div>'
                      f'<div class="sub" style="margin:0">'
                      f'{counts.get(name, 0)} files</div></a>')
        return f'<p class="sub">{crumb}</p><div class="tiles">{cards}</div>'

    names = core.sections(coll)
    if not 0 <= sect < len(names):
        return f'<p class="sub">{crumb}</p>'
    category = names[sect]
    crumb += f' › <a class="crumb" href="{base}&amp;c={coll}">{E(category)}</a>'
    units = core.units_in(db, level_id, coll, category)

    if units and unit is None:
        numbers = core.units_for_level(db, level_id)
        if 0 in units:
            numbers = [0] + numbers
        cards = "".join(
            f'<a class="tile small{"" if n in units else " empty"}" '
            f'href="{base}&amp;c={coll}&amp;s={sect}&amp;u={n}">'
            f'<div class="tile-title">{"Welcome" if n == 0 else "Unit %d" % n}</div>'
            f'<div class="sub" style="margin:0">{units.get(n, 0)} files</div></a>'
            for n in numbers)
        return f'<p class="sub">{crumb}</p><div class="tiles">{cards}</div>'

    if unit is not None:
        mats = core.materials_in_unit(db, level_id, coll, category, unit)
        crumb += " › " + ("Welcome" if unit == 0 else "Unit %d" % unit)
    else:
        mats = core.materials_at_level(db, level_id, coll, category)
    if not mats:
        return f'<p class="sub">{crumb}</p><div class="card"><p style="margin:0">Nothing here yet.</p></div>'
    parts = []
    for m in mats:
        icon = "&#9834;" if (m["mime"] or "").startswith("audio") else "&#128196;"
        note = f'<span class="sub">{E(m["note"])}</span>' if m["note"] else ""
        parts.append(
            f'<a class="filerow" href="/materials/{m["id"]}/file?s={E(token)}">'
            f'<span class="ficon">{icon}</span>'
            f'<span class="fname">{E(m["title"])}{note}</span>'
            f'<span class="fsize">{E(core.human_size(m["size"]))}</span></a>')
    rows = "".join(parts)
    return f'<p class="sub">{crumb}</p><div class="filelist">{rows}</div>'


def portal_progress(db, s, token):
    st = core.student_stats(db, s["id"])
    v = core.vocab_stats(db, s["id"])
    band = []
    for row in st["timeline"]:
        r = db.execute(
            "SELECT AVG(score) a FROM submissions WHERE assignment_id=? AND status='graded'",
            (row["assignment_id"],)).fetchone()
        band.append(round(r["a"], 2) if r["a"] is not None else None)
    hist = ""
    for t in reversed(st["timeline"]):
        if t["score"] is not None:
            state = score_pill(t["score"])
        elif t["submission_id"]:
            state = '<span class="pill mute">waiting</span>'
        else:
            state = '<span class="pill risk">not sent</span>'
        hist += f'<tr><td>{E(t["title"])}</td><td style="text-align:right">{state}</td></tr>'
    comp = f'{st["completion"]}%' if st["completion"] is not None else "—"
    vocab = ""
    if v["practised"]:
        vocab = (f'<div class="grid">{stat("Words known", v["known"])}'
                 f'{stat("Accuracy", str(v["accuracy"]) + "%")}'
                 f'{stat("Due for review", v["due"])}</div>')
    return f"""<h2>Your scores</h2>
<div class="grid">{stat("Average", fmt(st["average"]), "/10")}
{stat("Last 3", fmt(st["last3"]), "/10")}{stat("Completion", comp)}
{stat("Streak", core.streak(db, s["id"]))}</div>
<div class="card">{charts.score_line(st["timeline"], band=band)}
<div class="legend"><span><i style="background:var(--accent)"></i>your trend</span>
<span><i style="background:var(--ink-3)"></i>class average</span>
<span style="color:var(--warn)">✕ not sent</span></div></div>
{vocab}
<h2>Every task</h2>
<div class="tablewrap"><table>{hist or '<tr><td class="sub">Nothing yet.</td></tr>'}</table></div>"""


def standing_line(db, s):
    """One sentence telling a student where they are and what would move them."""
    n = core.next_step(db, s["id"])
    if not n:
        return ""
    place = "%d%s of %d" % (n["rank"],
                            {1: "st", 2: "nd", 3: "rd"}.get(
                                n["rank"] if n["rank"] < 20 else n["rank"] % 10, "th"),
                            n["of"])
    if n["rank"] == 1:
        tail = (f'{E(n["behind"])} is right behind you.' if n["behind"]
                else "Top of the class.")
    elif n["tasks"]:
        tail = ("Hand in one more piece of homework and you pass %s."
                % E(n["ahead"]) if n["tasks"] == 1 else
                "Hand in %d more pieces of homework and you pass %s."
                % (n["tasks"], E(n["ahead"])))
    elif n["gap"]:
        tail = "You are %g points behind %s." % (n["gap"], E(n["ahead"]))
    else:
        tail = "Level with %s." % E(n["ahead"])
    return (f'<div class="standing"><strong>You are {place}.</strong> {tail}</div>')


def portal_profile(db, s, token, flash=""):
    """Who they are, how far up the mountain they are, and a line worth reading."""
    quote, who = core.quote_of_the_day()
    c = core.climb(db, s["id"])

    def field(key):
        return (s[key] if key in s.keys() else None) or ""

    photo = (f'<img class="pf-photo" src="/s/{E(token)}/photo" alt="">'
             if s["photo"] else
             f'<div class="pf-photo empty">{core.avatar_of(s)}</div>')

    here = field("climb_from") or core.camp_for_level(
        core.level_name(db, core.level_of(db, s["group_id"])))

    def camps(name, current):
        opts = ['<option value="">&mdash;</option>']
        for key, label in core.CAMPS:
            sel = " selected" if key == current else ""
            opts.append(f'<option value="{key}"{sel}>{E(label)}</option>')
        return f'<select name="{name}">{"".join(opts)}</select>'

    if c:
        if c["climbed"] >= c["camps"]:
            line = "You are standing on the summit. Choose a higher one."
        else:
            line = (f'{c["to_next"]:g} more points and you reach '
                    f'<strong>{E(c["next_label"])}</strong>')
        body = (
            '<div class="pf-figure">'
            f'<span class="pf-pct">{c["percent"]:g}<small>%</small></span>'
            f'<span class="pf-of">of the way from {E(c["labels"][0])} '
            f'to {E(c["labels"][-1])}</span></div>'
            f'<div class="pf-bar"><i style="width:{c["percent"]:g}%"></i></div>'
            f'<p class="sub pf-now">Camp reached: <strong>{E(c["at_label"])}</strong>'
            f' &middot; {line}</p>'
            + charts.mountain(c)
            + '<p class="sub pf-earned">Earned by '
              f'{c["graded"]} marked piece{"" if c["graded"] == 1 else "s"} of homework'
              f' and {c["words"]} word{"" if c["words"] == 1 else "s"} you have kept.'
              ' Nothing you type moves the climber &mdash; only work does.</p>')
    else:
        body = ('<p class="sub" style="margin:0 0 4px">Choose the camp you set out '
                'from and the one you are climbing towards. Your homework and the '
                'words you learn carry the climber up &mdash; nothing you type does.</p>')

    return f"""{flash}
<div class="pf-head">{photo}
  <div><h2 style="margin:0">{E(s["name"])}</h2>
    <p class="sub" style="margin:2px 0 0">{E(group_name(db, s["group_id"]))}
      &middot; {E(core.level_name(db, core.level_of(db, s["group_id"])) or "")}</p></div>
</div>

<div class="card pf-card">
  <h3 class="pf-title">Your climb</h3>
  {body}
  <form method="post" action="/s/{E(token)}/profile" enctype="multipart/form-data"
        class="pf-set">
    <label class="f">I started at{camps("climb_from", here)}</label>
    <label class="f">I am climbing to{camps("climb_to", field("climb_to"))}</label>
    <button>Save</button>
  </form>
</div>

<div class="quote">
  <p>&ldquo;{E(quote)}&rdquo;</p>
  <span>{E(who)}</span>
</div>

<details class="adder"><summary>Edit my details</summary>
<div class="card"><form method="post" action="/s/{E(token)}/profile"
      enctype="multipart/form-data">
  <div class="inline">
    <label class="f">Name<input name="name" value="{E(s["name"])}" required></label>
    <label class="f">Phone<input name="phone" type="tel" value="{E(field("phone"))}"
      placeholder="+998 .."></label>
  </div>
  <label class="f" style="margin-top:10px">About you
    <input name="about" value="{E(field("about"))}"
           placeholder="Why you are learning English"></label>
  <label class="f" style="margin-top:10px">Your photo
    <input type="file" name="photo" accept="image/*"></label>
  <div style="margin-top:14px"><button>Save</button></div>
</form></div></details>"""


def portal_champ_row(db, r, me_id, show_group=True):
    """One line of the league as a student sees it.

    The same table the teacher sees, minus the links into the teacher's pages:
    a league nobody can read in full is a league students argue about.
    """
    st = r["student"]
    me = st["id"] == me_id
    medals = {1: "&#129351;", 2: "&#129352;", 3: "&#129353;"}
    place = (medals.get(r["rank"], str(r["rank"]) + ".") if r["rank"]
             else '<span class="sub">&mdash;</span>')
    bars = ""
    for key, label, weight in core.CHAMPIONSHIP:
        got = r["points"].get(key, 0)
        share = got / weight * 100.0 if weight else 0
        bars += (f'<td class="cpt"><span class="cbar"><i style="width:'
                 f'{min(100, share):.0f}%"></i></span>{got:g}</td>')
    of = core.SEASON_LESSONS
    lessons = (f'<td class="sub">{of}/{of} &#10003;</td>' if r["done"]
               else f'<td class="sub">{r["lessons"]}/{of}</td>')
    mark = ' id="me" class="me"' if me else ''
    group = (f'<td class="sub">{E(group_name(db, st["group_id"]))}</td>'
             if show_group else "")
    return (f'<tr{mark}><td>{place}</td>'
            f'<td>{E(st["name"])}{" &#9668;" if me else ""}</td>'
            f'{group}'
            f'<td><strong>{r["total"]:g}</strong></td>{bars}{lessons}</tr>')


def portal_class(db, s, token, scope="class"):
    """One league table, not two.

    This page used to stack the championship on top of a second ranked table
    with a different formula, so a student could be first in one and eighth in
    the other on the same screen. The ranking now lives in the championship
    alone; what is left of the old table is their own line, which is the part
    that told them something.
    """
    champ = core.championship(db)
    if not champ["started"]:
        return f"""<h2>Championship</h2>
<div class="card"><p style="margin:0">The championship has not started yet.
Your teacher will start it soon.</p></div>
<h2>Where you are</h2>
{standing_line(db, s) or '<p class="sub">Nothing marked yet.</p>'}"""

    mine = next((r for r in champ["rows"] if r["student"]["id"] == s["id"]), None)
    if not mine:
        return f"""<h2>Where you are</h2>
{standing_line(db, s) or '<p class="sub">Nothing marked yet.</p>'}"""

    shown = core.scope_standing(champ, s["group_id"]) if scope == "class" else champ
    here = next((r for r in shown["rows"] if r["student"]["id"] == s["id"]), mine)

    if here["eligible"]:
        rank = here["rank"]
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(rank if rank < 20 else rank % 10, "th")
        where = "in your class" if scope == "class" else "in the school"
        standing = (f'You are <strong>{rank}{suffix}</strong> {where} with '
                    f'<strong>{here["total"]:g}</strong> of {core.CHAMPIONSHIP_MAX:g} points')
    else:
        standing = (f'You need {core.MIN_GRADED} marked pieces of homework this '
                    f'season to enter. You have {here["graded"]}')

    parts = "".join(
        f'<div class="cp"><span>{E(label)}</span>'
        f'<span class="cbar"><i style="width:'
        f'{min(100, (mine["points"].get(key, 0) / float(weight) * 100)):.0f}%"></i></span>'
        f'<b>{mine["points"].get(key, 0):g}</b></div>'
        for key, label, weight in core.CHAMPIONSHIP)

    frozen = ('<div class="card paused"><strong>The league is paused.</strong>'
              '<p class="sub" style="margin:6px 0 0">Your teacher has stopped the '
              'table for now. Nothing counts towards the championship until it '
              'starts again &mdash; keep working, it will be back.</p></div>'
              if champ["paused"] else "")

    left = core.SEASON_LESSONS - mine["lessons"]
    pace = ("Your season is finished &mdash; this score is finalised."
            if mine["done"] else
            f'{mine["lessons"]} of {core.SEASON_LESSONS} lessons done, {left} to go.')

    def tab(sc, label):
        on = " on" if scope == sc else ""
        return (f'<a class="tab{on}" href="/s/{E(token)}?tab=class&amp;scope={sc}">'
                f'{E(label)}</a>')
    tabs = f'<div class="tabs">{tab("class", "My class")}{tab("school", "Whole school")}</div>'

    rows = "".join(portal_champ_row(db, r, s["id"], show_group=scope == "school")
                   for r in shown["rows"])
    chead = "".join(f'<th title="up to {w:g} points">{E(l)}</th>'
                    for _k, l, w in core.CHAMPIONSHIP)
    waiting = len(shown["rows"]) - shown["eligible"]
    below = (f'<p class="sub">The last {waiting} have not yet handed in '
             f'{core.MIN_GRADED} marked pieces, so they are below the line and '
             f'cannot win this season.</p>' if waiting else "")

    return f"""<h2>Championship &mdash; season {champ["season"]}</h2>
<p class="sub">A season lasts {core.SEASON_LESSONS} lessons, not a month, so everyone is
judged over the same amount of teaching. {pace}
The prize goes to the best in the whole school.</p>
{frozen}
<div class="card"><p style="margin:0 0 12px">{standing}.
<a href="#me" class="findme">Find me in the table &darr;</a></p>
<div class="cparts">{parts}</div></div>
{tabs}
<div class="tablewrap"><table><tr><th>#</th><th>Student</th>
{"<th>Class</th>" if scope == "school" else ""}
<th>Points</th>{chead}<th>Lessons</th></tr>{rows}</table></div>
{below}
<h2 style="margin-top:26px">Your homework</h2>
{standing_line(db, s) or '<p class="sub">Nothing marked yet.</p>'}"""


def view_parent_report(req, db, token):
    """A read-only page a parent can open - no login, no upload, no materials."""
    row = db.execute("SELECT * FROM parents WHERE token=?", (token,)).fetchone()
    if not row:
        return html_response(student_page("Not found",
            "<h1>Link not recognised</h1><p class='sub'>Ask the teacher for the "
            "current link.</p>"), 404)
    s = db.execute("SELECT * FROM students WHERE id=?", (row["student_id"],)).fetchone()
    if not s:
        return not_found()

    st = core.student_stats(db, s["id"])
    marks = core.mark_stats(db, s["id"])
    completion = core.live_completion(db, s["id"])
    index = core.overall_index(completion, st["average"], marks["overall"])
    level = core.level_name(db, core.level_of(db, s["group_id"]))

    band = []
    for t in st["timeline"]:
        r = db.execute(
            "SELECT AVG(score) a FROM submissions WHERE assignment_id=? AND status='graded'"
            " AND draft=0", (t["assignment_id"],)).fetchone()
        band.append(round(r["a"], 2) if r["a"] is not None else None)

    hist = ""
    for t in reversed(st["timeline"][-12:]):
        if t["score"] is not None:
            state = score_pill(t["score"])
        elif t["submission_id"]:
            state = '<span class="pill mute">waiting to be marked</span>'
        else:
            state = '<span class="pill risk">not handed in</span>'
        hist += f'<tr><td>{E(t["title"])}</td><td style="text-align:right">{state}</td></tr>'

    mark_cards = "".join(
        stat(core.MARK_LABELS[f], fmt(marks[f]), "/5") for f in core.MARK_FIELDS)
    recent = ""
    for m in db.execute(
        "SELECT * FROM lesson_marks WHERE student_id=? ORDER BY day DESC LIMIT 8",
        (s["id"],)
    ).fetchall():
        vals = " · ".join(
            f"{core.MARK_LABELS[f][:5]} {m[f]}" for f in core.MARK_FIELDS
            if m[f] is not None)
        note = f' <span class="sub">{E(m["note"])}</span>' if m["note"] else ""
        recent += f'<tr><td>{E(m["day"])}</td><td>{E(vals)}{note}</td></tr>'

    verdict = "doing well" if (index or 0) >= 75 else (
        "making progress" if (index or 0) >= 50 else "needs support")
    body = f"""<div class="whoami">
  <div class="avatar">{E((s["name"] or "?").strip()[:1].upper())}</div>
  <div><div class="name">{E(s["name"])}</div>
    <div class="sub" style="margin:0">{E(group_name(db, s["group_id"]))}
      {"· " + E(level) if level else ""} · report for parents</div></div>
</div>
<div class="card"><p style="margin:0">Overall this student is <strong>{verdict}</strong>:
{completion if completion is not None else 0}% of homework handed in,
an average score of {fmt(st["average"])} out of 10, and
{fmt(marks["overall"])} out of 5 for how they are in class across
{marks["lessons"]} lesson(s).</p></div>
<div class="grid">{stat("Overall index", fmt(index), "/100")}
{stat("Homework done", (str(completion) + "%") if completion is not None else "—")}
{stat("Average score", fmt(st["average"]), "/10")}
{stat("Not handed in", st["missed"])}</div>
<h2>In the classroom</h2>
<div class="grid">{mark_cards}</div>
<div class="tablewrap">{"<table>" + recent + "</table>" if recent
   else '<div class="card"><p style="margin:0" class="sub">No lessons marked yet.</p></div>'}</div>
<h2>Homework, piece by piece</h2>
<div class="card">{charts.score_line(st["timeline"], band=band)}
<div class="legend"><span><i style="background:var(--accent)"></i>their trend</span>
<span><i style="background:var(--ink-3)"></i>class average</span>
<span style="color:var(--warn)">✕ not handed in</span></div></div>
<div class="tablewrap"><table>{hist or '<tr><td class="sub">Nothing yet.</td></tr>'}</table></div>
<p class="sub">Prepared by their teacher. Figures update by themselves as work
is marked.</p>"""
    return html_response(student_page("%s — report" % s["name"], body))


def portal_goal(db, s, token, flash=""):
    """A band card the student sets for themselves - a target, not a result."""
    goal = core.get_goal(db, s["id"])
    scores = {k: (goal[k] if goal else None) for k in core.BAND_SECTIONS}
    overall = core.overall_band([scores[k] for k in core.BAND_SECTIONS])
    level = core.level_name(db, core.level_of(db, s["group_id"]))

    def picker(field):
        opts = ['<option value="">—</option>']
        v = scores[field]
        n = 9.0
        while n >= 0:
            sel = " selected" if v is not None and abs(v - n) < 0.01 else ""
            opts.append(f'<option value="{n:g}"{sel}>{n:g}</option>')
            n -= 0.5
        return (f'<label class="f">{core.BAND_LABELS[field]}'
                f'<select name="{field}" class="mark">{"".join(opts)}</select></label>')

    photo = (f'<img class="cert-photo" src="/s/{E(token)}/photo" alt="">' if s["photo"]
             else '<div class="cert-photo empty">your photo</div>')
    target = (goal["target_date"] if goal and goal["target_date"] else "")

    if overall is not None:
        rows = "".join(
            f'<div class="sk"><span class="sk-name">{core.BAND_LABELS[k]}</span>'
            f'<span class="sk-dots"></span>'
            f'<span class="sk-band">{scores[k]:g}</span></div>'
            for k in core.BAND_SECTIONS)
        number = "OA-%s-%04d" % ((goal["updated_at"] or "")[:4] or "2026", s["id"])
        issued = (goal["updated_at"] or "")[:10]
        card = f"""<div class="cert-wrap"><div class="cert" id="cert">
  <svg class="cert-guilloche" viewBox="0 0 800 600" preserveAspectRatio="none"
       aria-hidden="true">
    <defs><pattern id="weave" width="26" height="26" patternUnits="userSpaceOnUse">
      <path d="M0 13 Q6.5 0 13 13 T26 13" fill="none" stroke="currentColor"
            stroke-width=".7"/>
      <path d="M13 0 Q26 6.5 13 13 T13 26" fill="none" stroke="currentColor"
            stroke-width=".7"/>
    </pattern></defs>
    <rect x="8" y="8" width="784" height="584" fill="url(#weave)" opacity=".5"/>
    <rect x="8" y="8" width="784" height="584" fill="none" stroke="currentColor"
          stroke-width="2"/>
    <rect x="18" y="18" width="764" height="564" fill="none" stroke="currentColor"
          stroke-width=".8"/>
    <g fill="none" stroke="currentColor" stroke-width="1.2">
      <path d="M18 54 q0-36 36-36 M30 54 q0-24 24-24"/>
      <path d="M782 54 q0-36-36-36 M770 54 q0-24-24-24"/>
      <path d="M18 546 q0 36 36 36 M30 546 q0 24 24 24"/>
      <path d="M782 546 q0 36-36 36 M770 546 q0 24-24 24"/>
    </g>
  </svg>
  <div class="cert-watermark">OA</div>
  <div class="cert-inner">
    <div class="cert-brand"><span class="cert-mark">O</span>OlimovAzamat</div>
    <div class="cert-kicker">Certificate of Achievement</div>
    <div class="cert-rule"><span></span>&#10022;<span></span></div>
    <p class="cert-lede">This is to certify that</p>
    <div class="cert-holder">{E(s["name"])}</div>
    <p class="cert-lede">of {E(group_name(db, s["group_id"]))}
      {"· " + E(level) if level else ""} achieved the following band scores</p>
    <div class="cert-main">
      {photo}
      <div class="cert-skills">{rows}</div>
      <div class="cert-seal">
        <svg viewBox="0 0 120 120" aria-hidden="true">
          <defs><radialGradient id="foil" cx="35%" cy="30%">
            <stop offset="0%" stop-color="#f7e3a1"/><stop offset="45%" stop-color="#d8b04a"/>
            <stop offset="100%" stop-color="#a97c1c"/></radialGradient></defs>
          <circle cx="60" cy="60" r="52" fill="url(#foil)"/>
          <circle cx="60" cy="60" r="44" fill="none" stroke="#fff" stroke-opacity=".55"/>
          <circle cx="60" cy="60" r="52" fill="none" stroke="#8a6413" stroke-width="1.5"/>
        </svg>
        <div class="cert-sealtext"><span class="k">Overall</span>
          <span class="v">{overall:g}</span></div>
      </div>
    </div>
    <div class="cert-descriptor">{E(core.band_words(overall))}</div>
    <div class="cert-sign">
      <div><div class="sig">Azamat</div><div class="line"></div><span>Teacher</span></div>
      <div><div class="sig"></div><div class="line"></div>
        <span>Issued {E(issued)}</span></div>
    </div>
    <div class="cert-serial">No. {E(number)}
      {"· exam date " + E(target) if target else ""}</div>
    <div class="cert-note">Awarded by OlimovAzamat for a mock examination.
      This is not an IELTS Test Report Form and is not issued by IELTS,
      British Council, IDP or Cambridge.</div>
  </div>
</div>
</div>
<div style="margin-bottom:16px"><button type="button" onclick="window.print()">
  Print or save as PDF</button></div>
"""
    else:
        card = ('<div class="card"><p style="margin:0">Choose a band for all four '
                'sections and your card will appear here.</p></div>')

    return f"""{flash}
<h2>My certificate</h2>
<p class="sub">Set the band you are aiming for — or the one you got in a mock exam —
and your certificate appears below. The overall band is worked out the way IELTS
works it out: a quarter rounds up to the next half band.</p>
{card}
<div class="card"><form method="post" action="/s/{E(token)}/goal"
      enctype="multipart/form-data">
  <div class="inline">{"".join(picker(k) for k in core.BAND_SECTIONS)}
    <label class="f">Exam date (optional)<input type="date" name="target_date"
      value="{E(target)}"></label></div>
  <label class="f" style="margin-top:12px">Your photo (optional)
    <input type="file" name="photo" accept="image/*"></label>
  <div style="margin-top:12px"><button>Save my goal</button></div>
</form></div>"""


def act_student_profile(req, db, token):
    """Save whichever part of the profile was submitted.

    There are two forms on this page - the journey and the details - so only
    fields that actually arrived may be written. Updating everything each time
    would let saving one form quietly empty the other.
    """
    s = core.student_by_token(db, token)
    if not s:
        return redirect(f"/s/{token}")
    fields, files = req["files"]

    sets, args = [], []

    def submitted(key, limit):
        if key not in fields:
            return False, None
        return True, ((fields.get(key, [""])[0] or "").strip()[:limit] or None)

    given, name = submitted("name", 60)
    if given and name:                      # never let them erase themselves
        sets.append("name=?")
        args.append(name)
    for key, limit in (("phone", 30), ("about", 160)):
        given, value = submitted(key, limit)
        if given:
            sets.append(key + "=?")
            args.append(value)

    if "climb_from" in fields or "climb_to" in fields:
        def camp(key):
            v = (fields.get(key, [""])[0] or "").strip()
            return v if v in core.CAMP_INDEX else None
        frm, to = camp("climb_from"), camp("climb_to")
        if frm and to and core.CAMP_INDEX[to] <= core.CAMP_INDEX[frm]:
            to = None                       # a summit below you is not a summit
        sets += ["climb_from=?", "climb_to=?", "journey_at=COALESCE(journey_at, ?)"]
        args += [frm, to, core.iso(core.now())]

    if sets:
        db.execute("UPDATE students SET %s WHERE id=?" % ", ".join(sets),
                   args + [s["id"]])
        db.commit()

    for filename, blob in files[:1]:
        w, h, kind = uploads.image_size(blob)
        if kind:
            fname = "photo_%d_%d.%s" % (s["id"], int(core.now().timestamp()),
                                        "png" if kind == "png" else "jpg")
            with open(os.path.join(core.UPLOAD_DIR, fname), "wb") as fh:
                fh.write(blob)
            old = s["photo"]
            db.execute("UPDATE students SET photo=? WHERE id=?", (fname, s["id"]))
            db.commit()
            if old and old != fname:
                path = os.path.join(core.UPLOAD_DIR, old)
                if os.path.exists(path):
                    os.remove(path)
    return redirect(f"/s/{token}?tab=profile&saved=1")


def act_student_goal(req, db, token):
    s = core.student_by_token(db, token)
    if not s:
        return redirect(f"/s/{token}")
    fields, files = req["files"]
    scores = {k: core.valid_band((fields.get(k, [""])[0] or "").strip())
              for k in core.BAND_SECTIONS}
    date = (fields.get("target_date", [""])[0] or "").strip()
    core.save_goal(db, s["id"], scores, date if re.match(r"^\d{4}-\d{2}-\d{2}$", date) else None)
    for filename, blob in files[:1]:
        w, h, kind = uploads.image_size(blob)
        if kind:
            name = f"photo_{s['id']}_{int(core.now().timestamp())}." + \
                   ("png" if kind == "png" else "jpg")
            with open(os.path.join(core.UPLOAD_DIR, name), "wb") as fh:
                fh.write(blob)
            old = s["photo"]
            db.execute("UPDATE students SET photo=? WHERE id=?", (name, s["id"]))
            db.commit()
            if old and old != name:
                path = os.path.join(core.UPLOAD_DIR, old)
                if os.path.exists(path):
                    os.remove(path)
    return redirect(f"/s/{token}?tab=goal")


def view_student_portal(req, db, token, flash=""):
    s = core.student_by_token(db, token)
    if not s:
        return html_response(student_page("Not found",
            "<h1>Link not recognised</h1><p class='sub'>Ask your teacher for your link.</p>"), 404)
    query = (req or {}).get("query", {}) if isinstance(req, dict) else {}
    tab = (query.get("tab", ["home"])[0] or "home")
    if tab == "materials":
        body = portal_materials(db, s, token, query)
    elif tab == "progress":
        body = portal_progress(db, s, token)
    elif tab == "class":
        sc = (query.get("scope", ["class"])[0] or "class")
        body = portal_class(db, s, token, "school" if sc == "school" else "class")
    elif tab == "goal":
        body = portal_goal(db, s, token, flash)
    elif tab == "profile":
        body = portal_profile(db, s, token, flash)
    else:
        tab = "home"
        body = portal_home(db, s, token, flash)
    return student_shell(s, db, token, tab, body)


def act_student_finish(req, db, token, sub_id):
    s = core.student_by_token(db, token)
    if not s:
        return redirect(f"/s/{token}")
    row = db.execute("SELECT * FROM submissions WHERE id=? AND student_id=? AND draft=1",
                     (sub_id, s["id"])).fetchone()
    if row and core.page_count(db, sub_id):
        core.finish_draft(db, sub_id)
        token_cfg = core.load_config().get("telegram_token")
        if token_cfg:
            import bot
            bot.notify_teachers_new(db, token_cfg, sub_id)
    return redirect(f"/s/{token}?sent=1")


def act_student_discard(req, db, token, sub_id):
    s = core.student_by_token(db, token)
    if not s:
        return redirect(f"/s/{token}")
    row = db.execute("SELECT * FROM submissions WHERE id=? AND student_id=?",
                     (sub_id, s["id"])).fetchone()
    if row and row["status"] != "graded":
        for f in db.execute("SELECT filename FROM files WHERE submission_id=?", (sub_id,)):
            path = os.path.join(core.UPLOAD_DIR, f["filename"])
            if os.path.exists(path):
                os.remove(path)
        db.execute("DELETE FROM files WHERE submission_id=?", (sub_id,))
        db.execute("DELETE FROM submissions WHERE id=?", (sub_id,))
        db.commit()
    return redirect(f"/s/{token}")


def act_student_upload(req, db, token):
    s = core.student_by_token(db, token)
    if not s:
        return redirect(f"/s/{token}")
    fields, files = req["files"]
    if not files:
        return redirect(f"/s/{token}?e=none")

    aid = None
    raw_aid = (fields.get("assignment_id") or [None])[0]
    if raw_aid and raw_aid.isdigit():
        # only accept an assignment that is genuinely open for this student's group
        ok = db.execute(
            "SELECT id FROM assignments WHERE id=? AND group_id=? AND closed=0",
            (int(raw_aid), s["group_id"]),
        ).fetchone()
        aid = ok["id"] if ok else None

    accepted, rejected = [], 0
    for filename, data in files[:uploads.MAX_FILES]:
        w, h, kind = uploads.image_size(data)
        if not kind or max(w or 0, h or 0) < CFG["min_photo_width"]:
            rejected += 1
            continue
        accepted.append((data, w, h, kind))
    if not accepted:
        return redirect(f"/s/{token}?e=small")

    # more photos for a task already in progress join it rather than starting again
    already = core.sent_submission(db, s["id"], aid)
    if already:
        return redirect(f"/s/{token}?e=locked")
    existing = core.open_draft(db, s["id"], aid)
    if existing:
        sub_id = existing["id"]
        start = core.page_count(db, sub_id)
    else:
        sub_id = db.execute(
            "INSERT INTO submissions (student_id, assignment_id, created_at, draft)"
            " VALUES (?,?,?,1)", (s["id"], aid, core.iso(core.now())),
        ).lastrowid
        start = 0
    for i, (data, w, h, kind) in enumerate(accepted, start):
        name = (f"{sub_id}_{i}_{int(core.now().timestamp())}"
                f".{'png' if kind == 'png' else 'jpg'}")
        with open(os.path.join(core.UPLOAD_DIR, name), "wb") as fh:
            fh.write(data)
        db.execute(
            "INSERT INTO files (submission_id, filename, width, height, ord)"
            " VALUES (?,?,?,?,?)",
            (sub_id, name, w, h, i),
        )
    db.commit()
    return redirect(f"/s/{token}?ok={len(accepted)}&r={rejected}"
                    f"&p={core.page_count(db, sub_id)}")


def view_homework(req, db):
    """Who has handed in what, per homework set, worst student first."""
    blocks = ""
    for g in db.execute("SELECT * FROM groups WHERE archived=0 ORDER BY name").fetchall():
        sets = core.open_sets(db, g["id"])
        if not sets:
            continue
        for due_at, items in sets:
            prog = core.group_set_progress(db, g["id"], items)
            if not prog:
                continue
            finished = sum(1 for r in prog if r["percent"] == 100)
            avg = round(sum(r["percent"] for r in prog) / len(prog))
            head = "".join(f'<th title="{E(a["title"])}">{E(a["title"][:14])}</th>' for a in items)
            body = ""
            for r in prog:
                cells = "".join(
                    '<td style="text-align:center">'
                    + ("&#9989;" if a["id"] in r["done_ids"] else
                       '<span style="color:var(--muted)">&#11036;</span>')
                    + "</td>"
                    for a in items
                )
                cls = ' class="pill risk"' if r["percent"] < 50 else ' class="pill"'
                body += (f'<tr><td><a href="/students/{r["student"]["id"]}">'
                         f'{E(r["student"]["name"])}</a></td>{cells}'
                         f'<td><span{cls}>{r["percent"]}%</span></td></tr>')
            blocks += f"""<h2>{E(g["name"])} — due {E((due_at or "no deadline")[:10])}</h2>
<p class="sub">{len(items)} task(s) · {finished} of {len(prog)} students finished everything ·
group average {avg}%</p>
<div class="tablewrap"><table><tr><th>Student</th>{head}<th>Done</th></tr>{body}</table></div>"""
    if not blocks:
        blocks = ('<div class="card"><p style="margin:0">No open homework. '
                  'Post a list on the Assignments page.</p></div>')
    body = f"""<h1>Homework</h1>
<p class="sub">A tick means the student has sent something for that item. Rows are
ordered worst first, so whoever needs chasing is at the top.</p>{blocks}"""
    return html_response(page("Homework", body, "Homework"))



def rating_table(db, rows, show_group=False):
    medals = {1: "&#129351;", 2: "&#129352;", 3: "&#129353;"}
    body_rows = ""
    for r in rows:
        st = r["student"]
        comp = r["completion"] if r["completion"] is not None else 0
        bar = (f'<div style="background:var(--line);border-radius:4px;height:8px;'
               f'width:90px"><div style="background:{bar_colour(comp)};'
               f'height:8px;border-radius:4px;width:{comp}%"></div></div>')
        streak = (f'<span class="pill gold">&#128293; {r["streak"]}</span>'
                  if r["streak"] >= 2 else "")
        gain = ""
        if r["gain"] is not None and abs(r["gain"]) >= 0.1:
            up = r["gain"] > 0
            gain = (f'<span class="pill {"good" if up else "risk"}">'
                    f'{"+" if up else ""}{r["gain"]:g}</span>')
        group_cell = (f'<td>{E(group_name(db, st["group_id"]))}</td>'
                      if show_group else "")
        body_rows += (
            f'<tr><td>{medals.get(r["rank"], str(r["rank"]) + ".")}</td>'
            f'<td><a href="/students/{st["id"]}">{E(st["name"])}</a></td>'
            f'{group_cell}'
            f'<td><strong>{fmt(r["index"])}</strong></td>'
            f'<td>{bar}</td><td>{comp}%</td>'
            f'<td>{score_pill(r["average"])}</td>'
            f'<td>{fmt(r["marks"])}</td>'
            f'<td>{gain}</td><td>{r["missed"]}</td><td>{streak}</td>'
            f'<td>{r["vocab"]}</td></tr>')
    head = ('<th>#</th><th>Student</th>' + ("<th>Group</th>" if show_group else "")
            + '<th>Score /100</th><th>Homework</th><th></th><th>Average</th>'
            '<th>Lesson /5</th><th>Change</th><th>Missed</th><th>Streak</th>'
            '<th>Words</th>')
    cols = 12 if show_group else 11
    return (f'<div class="tablewrap"><table><tr>{head}</tr>{body_rows}'
            f'</table></div>' if body_rows else
            f'<div class="card"><p class="sub" style="margin:0">Nobody here yet.</p></div>')


def improved_table(db, rows):
    """Ranked on gain alone - the one table a weaker student can win."""
    if not rows:
        return ('<div class="card"><p class="sub" style="margin:0">Nothing to compare '
                'yet. It needs a student who went up, with at least two graded pieces '
                'this month and two the month before.</p></div>')
    out = ""
    for i, r in enumerate(rows, 1):
        st = r["student"]
        up = r["gain"] > 0
        out += (f'<tr><td>{i}.</td>'
                f'<td><a href="/students/{st["id"]}">{E(st["name"])}</a></td>'
                f'<td>{E(group_name(db, st["group_id"]))}</td>'
                f'<td><span class="pill {"good" if up else "risk"}">'
                f'{"+" if up else ""}{r["gain"]:g}</span></td>'
                f'<td>{score_pill(r["average"])}</td></tr>')
    return ('<div class="tablewrap"><table><tr><th>#</th><th>Student</th>'
            '<th>Group</th><th>Change this month</th><th>Average now</th></tr>'
            + out + "</table></div>")


def attention_block(db, rows):
    """The point of this page: who has stopped, and who is slipping.

    The ranking below is ordering, not a competition - the competition is the
    championship, and students see that one. What only this page can tell you is
    who has quietly stopped handing work in, which the league cannot show
    because it marks the average of what arrives, not what is missing.
    """
    stopped, slipping = [], []
    for r in rows:
        st = r["student"]
        if r["missed"] and r["missed"] >= 2:
            stopped.append((r["missed"], st, r))
        elif r["gain"] is not None and r["gain"] <= -0.5:
            slipping.append((r["gain"], st, r))
    if not stopped and not slipping:
        return ('<div class="card good"><strong>Nobody is behind.</strong>'
                '<p class="sub" style="margin:6px 0 0">No student has missed two '
                'pieces or dropped half a mark.</p></div>')
    out = ""
    if stopped:
        stopped.sort(key=lambda x: -x[0])
        out += "<h3>Not handing work in</h3><ul class=\"attn\">"
        for missed, st, r in stopped[:12]:
            out += (f'<li><a href="/students/{st["id"]}">{E(st["name"])}</a>'
                    f'<span class="sub">{E(group_name(db, st["group_id"]))}</span>'
                    f'<span class="pill risk">{missed} missed</span>'
                    f'<span class="sub">{r["completion"] or 0}% done</span></li>')
        out += "</ul>"
    if slipping:
        slipping.sort(key=lambda x: x[0])
        out += "<h3>Marks falling</h3><ul class=\"attn\">"
        for gain, st, r in slipping[:12]:
            out += (f'<li><a href="/students/{st["id"]}">{E(st["name"])}</a>'
                    f'<span class="sub">{E(group_name(db, st["group_id"]))}</span>'
                    f'<span class="pill risk">{gain:g}</span>'
                    f'<span class="sub">now {fmt(r["average"])}</span></li>')
        out += "</ul>"
    return f'<div class="card attn-card">{out}</div>'


def view_ratings(req, db):
    """Standings on everything a student is judged by, class by class."""
    gid = req["query"].get("group", [None])[0]
    gid = int(gid) if gid and gid.isdigit() else None
    scope = req["query"].get("scope", [""])[0]
    groups = db.execute("SELECT * FROM groups WHERE archived=0 ORDER BY name").fetchall()

    def tab(href, label, on):
        return f'<a class="tab{" on" if on else ""}" href="{href}">{E(label)}</a>'
    tabs = ('<div class="tabs">'
            + tab("/ratings", "By class", gid is None and scope != "all")
            + tab("/ratings?scope=all", "Whole school", scope == "all")
            + "".join(tab(f'/ratings?group={g["id"]}', g["name"], gid == g["id"])
                      for g in groups) + "</div>")

    if scope == "all":
        note = ("Everyone in one list. Useful for a school-wide prize, but a Beginner "
                "and an Intermediate are set different homework, so the fair comparison "
                "is the one class by class.")
        tables = rating_table(db, core.rating_rows(db), show_group=True)
        improved = improved_table(db, core.most_improved(db))
    elif gid:
        note = "Ranked within this class."
        tables = rating_table(db, core.rating_rows(db, gid))
        improved = improved_table(db, core.most_improved(db, gid))
    else:
        note = ("Each class ranked against itself, which is the only fair comparison "
                "&mdash; classes are set different work.")
        tables = ""
        for g in groups:
            rows = core.rating_rows(db, g["id"])
            if not rows:
                continue
            tables += (f'<h2 style="margin-top:28px">{E(g["name"])} '
                       f'<span class="sub" style="font-weight:400">'
                       f'{E(core.level_name(db, g["level_id"]) or "no level")}</span></h2>'
                       + rating_table(db, rows))
        improved = improved_table(db, core.most_improved(db))

    dl = f'/export.csv?group={gid}' if gid else '/export.csv'
    watch = attention_block(db, core.rating_rows(db, gid) if gid else core.rating_rows(db))
    body = f"""<h1>Progress</h1>
<p class="sub">Your own view of the school &mdash; who is slipping and who needs a word.
Students do not see this page; the table they compete in is the
<a href="/championship">championship</a>, which marks the average of what arrives and so
cannot tell you who has stopped handing work in. This can.</p>
{watch}
<h2 style="margin-top:30px">Everyone, in order</h2>
<p class="sub">Half is effort, a quarter the scores, a quarter how they are in the room.
{note}</p>
{tabs}
{tables}
<h2 style="margin-top:34px">Most improved</h2>
<p class="sub">Measured against the student&rsquo;s own last month, so this is the
table anyone can win &mdash; it asks nothing about how strong they already were.</p>
{improved}
<p style="margin-top:20px"><a href="{dl}">Download as CSV</a> — opens in Excel.</p>"""
    return html_response(page("Progress", body, "Progress"))



def view_questions(req, db):
    rows = ""
    for q in db.execute(
        "SELECT q.*, s.name FROM questions q JOIN students s ON s.id=q.student_id"
        " ORDER BY q.answered_at IS NOT NULL, q.created_at DESC LIMIT 100"
    ).fetchall():
        if q["answer"]:
            action = f'<span class="sub">{E(q["answer"][:120])}</span>'
        else:
            action = (f'<form method="post" action="/questions/{q["id"]}/answer" class="inline">'
                      f'<input name="answer" placeholder="Your answer" style="flex:1;min-width:220px">'
                      f'<button>Send</button></form>')
        rows += (f'<tr><td>{E(q["name"])}</td><td>{E(q["text"][:200])}</td>'
                 f'<td>{E(q["created_at"][:16].replace("T", " "))}</td><td>{action}</td></tr>')
    body = f"""<h1>Questions</h1>
<p class="sub">Students ask with the “Ask teacher” button. Your answer goes back to
them in Telegram.</p>
<div class="tablewrap"><table><tr><th>Student</th><th>Question</th><th>Asked</th>
<th>Answer</th></tr>
{rows or '<tr><td colspan=4 class="sub">No questions yet.</td></tr>'}</table></div>"""
    return html_response(page("Questions", body, "Questions"))


def act_answer_question(req, db, qid):
    answer = (req["form"].get("answer", [""])[0] or "").strip()
    if not answer:
        return redirect("/questions")
    q = db.execute("SELECT * FROM questions WHERE id=?", (qid,)).fetchone()
    if not q:
        return redirect("/questions")
    db.execute("UPDATE questions SET answer=?, answered_at=? WHERE id=?",
               (answer, core.iso(core.now()), qid))
    db.commit()
    token = core.load_config().get("telegram_token")
    st = db.execute("SELECT telegram_id, lang FROM students WHERE id=?",
                    (q["student_id"],)).fetchone()
    if token and st and st["telegram_id"]:
        import bot
        bot.send(token, st["telegram_id"], bot.t(st["lang"], "ask_answer", answer=answer))
    return redirect("/questions")


def view_backup(req, db):
    """Download everything - students, homework, submissions, photos - as one file."""
    import transfer
    data = transfer.export_db(db)
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
    stamp = core.now().strftime("%Y-%m-%d")
    return 200, [("Content-Type", "application/json; charset=utf-8"),
                 ("Content-Disposition", f'attachment; filename="backup-{stamp}.json"'),
                 ("Content-Length", str(len(payload)))], payload


def view_import(req, db, flash=""):
    counts = {t: db.execute(f"SELECT COUNT(*) c FROM {t}").fetchone()["c"]
              for t in ("groups", "students", "assignments", "submissions", "files")}
    body = f"""<h1>Import data</h1>
<p class="sub">Move students, homework, submissions and photographs from another
copy of this system. Run <code>python3 transfer.py export</code> there, then upload
the <code>transfer.json</code> it produces.</p>
{flash}
<div class="card"><form method="post" action="/import" enctype="multipart/form-data">
<input type="file" name="file" accept=".json,application/json" required
       style="width:100%;padding:14px;border:1px dashed var(--line)">
<div style="margin-top:12px"><button>Import</button></div></form>
<p class="sub" style="margin:10px 0 0">This merges rather than replaces. Anything
already here is matched and left alone, so importing the same file twice changes
nothing.</p></div>
<h2>Download a backup</h2>
<div class="card"><p class="sub" style="margin:0 0 8px">Everything in one file:
students, homework, submissions, scores and the photographs themselves. Keep a copy
somewhere of your own — it is the file this page accepts back.</p>
<a href="/backup.json"><button type="button">Download backup</button></a></div>
<h2>Currently stored</h2>
<div class="grid">{"".join(stat(k, v) for k, v in counts.items())}</div>"""
    return html_response(page("Import", body, ""))


def act_import(req, db):
    _fields, files = req["files"]
    if not files:
        return view_import(req, db, '<div class="flash err">No file was attached.</div>')
    try:
        data = json.loads(files[0][1].decode("utf-8"))
    except Exception as exc:
        return view_import(req, db,
                           f'<div class="flash err">That file could not be read: {E(str(exc))}</div>')
    import transfer
    added = transfer.import_all(db, data)
    summary = ", ".join(f"{v} {k}" for k, v in added.items() if v)
    return view_import(req, db,
                       f'<div class="flash">Imported: {E(summary or "nothing new")}.</div>')


# ------------------------------------------------------------- live game

def view_play(req, db):
    """Set a game up. Everything about it is decided here, then it just runs."""
    groups = db.execute("SELECT * FROM groups WHERE archived=0 ORDER BY name").fetchall()
    lists = db.execute(
        "SELECT l.*, (SELECT COUNT(*) FROM words w WHERE w.list_id=l.id) n"
        " FROM word_lists l WHERE l.active=1 ORDER BY l.title").fetchall()
    playable = [l for l in lists if l["n"] >= 4]

    live = ""
    for g in db.execute(
        "SELECT * FROM games WHERE state IN ('lobby','question','reveal')"
        " ORDER BY id DESC").fetchall():
        live += (f'<div class="card"><strong>{E(group_name(db, g["group_id"]))}</strong> '
                 f'&middot; code <span class="kbd">{E(g["code"])}</span> '
                 f'&middot; <a href="/play/{g["id"]}">open the board &rarr;</a></div>')

    if not playable:
        body = ("<h1>Live game</h1><div class=\"card\"><p style=\"margin:0\">"
                "You need a word list with at least four words in it. Add one on the "
                "<a href='/vocab'>Vocabulary</a> page and it will appear here.</p></div>")
        return html_response(page("Live game", body, "Play"))

    gopts = "".join(f'<option value="{g["id"]}">{E(g["name"])}</option>' for g in groups)
    lopts = "".join(f'<option value="{l["id"]}">{E(l["title"])} ({l["n"]} words)</option>'
                    for l in playable)
    body = f"""<h1>Live game</h1>
<p class="sub">A word on the big screen, four answers on their phones. Right earns
points, right and fast earns more. Every answer also counts towards the student&rsquo;s
revision in the bot, so a game on Tuesday changes what they are asked on Thursday.</p>
{live}
<div class="card"><form method="post" action="/play/new" class="inline">
  <label class="f">Class<select name="group_id">{gopts}</select></label>
  <label class="f">Word list<select name="list_id">{lopts}</select></label>
  <label class="f">Questions<select name="q_count">
    <option>5</option><option selected>10</option><option>15</option>
    <option>20</option></select></label>
  <label class="f">Seconds each<select name="seconds">
    <option>10</option><option>15</option><option selected>20</option>
    <option>30</option></select></label>
  <label class="check"><input type="checkbox" name="tell" value="1" checked>
    <span>Message the class on Telegram</span></label>
  <button>Start a game</button>
</form></div>"""
    return html_response(page("Live game", body, "Play"))


def act_new_game(req, db):
    f = req["form"]
    gid = f.get("group_id", [None])[0]
    lid = f.get("list_id", [None])[0]
    if not gid or not lid:
        return redirect("/play")
    def num(key, default):
        v = f.get(key, [""])[0]
        return int(v) if v.isdigit() else default
    game_id = core.make_game(db, int(gid), int(lid), num("q_count", 10), num("seconds", 20))
    if not game_id:
        return redirect("/play")
    # unticking the box sets a game up without telling anybody, which is how you
    # try one out before using it in front of a class
    if f.get("tell", [""])[0] == "1":
        invite_to_game(db, game_id)
    return redirect(f"/play/{game_id}")


def invite_to_game(db, game_id):
    """Nudge the class in Telegram so nobody has to be told a link out loud."""
    token = CFG.get("telegram_token")
    g = db.execute("SELECT * FROM games WHERE id=?", (game_id,)).fetchone()
    if not token or not g:
        return
    try:
        import bot
    except Exception:
        return
    base = core.meta_get(db, "site_url") or ""
    for st in db.execute(
        "SELECT * FROM students WHERE group_id=? AND active=1"
        " AND telegram_id IS NOT NULL", (g["group_id"],)).fetchall():
        try:
            url = base + "/s/" + core.student_token(db, st["id"]) + "/game"
            bot.send(token, st["telegram_id"],
                     bot.t(st["lang"] or "en", "game_invite", url=url))
        except Exception:
            continue          # a blocked bot is one student, not the class


def view_game_board(req, db, game_id):
    """The projector. Big type, no chrome - it is read from the back of a room."""
    g = db.execute("SELECT * FROM games WHERE id=?", (game_id,)).fetchone()
    if not g:
        return not_found()
    body = f"""<h1 style="margin-bottom:4px">{E(group_name(db, g["group_id"]))}</h1>
<p class="sub">Students join at <strong>your site address + /s/ their own link + /game</strong>,
or straight from the message the bot sent them.
Code <span class="kbd">{E(g["code"])}</span></p>
<div id="board"></div>
<div style="display:flex;gap:8px;margin-top:18px;flex-wrap:wrap">
  <button onclick="step()" id="go">Start</button>
  <button class="ghost" onclick="if(confirm('End this game?'))location.href='/play/{g["id"]}/end'">End game</button>
</div>
<script>
const GID = {g["id"]};
let last = "", ac = null, lastTick = -1, lastState = "";
// the projector is the thing with speakers, so the room hears the clock here
function beep(freq, ms, type) {{
  try {{
    ac = ac || new (window.AudioContext || window.webkitAudioContext)();
    const o = ac.createOscillator(), gain = ac.createGain();
    o.type = type || 'sine'; o.frequency.value = freq;
    gain.gain.setValueAtTime(0.2, ac.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.0001, ac.currentTime + ms / 1000);
    o.connect(gain); gain.connect(ac.destination);
    o.start(); o.stop(ac.currentTime + ms / 1000);
  }} catch (e) {{}}
}}
function esc(x) {{ return String(x).replace(/[&<>"]/g, c =>
  ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}})[c]); }}
async function poll() {{
  try {{
    const r = await fetch('/play/' + GID + '/state.json', {{cache:'no-store'}});
    const s = await r.json();
    render(s);
  }} catch (e) {{}}
  setTimeout(poll, 900);
}}
function render(s) {{
  if (s.state === 'question' && s.left <= 5 && s.left > 0 && s.left !== lastTick) {{
    lastTick = s.left; beep(760, 80);
  }}
  if (s.state !== lastState) {{
    if (s.state === 'reveal') beep(520, 120);
    if (s.state === 'done') {{ beep(660, 140);
      setTimeout(() => beep(880, 180), 150); setTimeout(() => beep(1100, 260), 320); }}
    lastState = s.state;
  }}
  document.getElementById('go').textContent =
    s.state === 'lobby' ? 'Start' :
    s.state === 'question' ? 'Show the answer' :
    s.state === 'reveal' ? 'Next question' : 'Finished';
  document.getElementById('go').disabled = busy || (s.state === 'done');
  let h = '';
  if (s.state === 'lobby') {{
    h = '<div class="gcard"><div class="gbig">' + s.players.length +
        ' in the room</div><div class="groom">' +
        s.players.map(p => '<span class="gface"><b>' + p.who + '</b>' +
          esc(p.name) + '</span>').join('') + '</div></div>';
  }} else if (s.state === 'question') {{
    h = '<div class="gcard"><div class="gsmall">Question ' + (s.q_index + 1) +
        ' of ' + s.q_count + ' &middot; ' + s.left + 's</div>' +
        '<div class="gword">' + esc(s.term) + '</div>' +
        '<div class="gsmall">' + s.answered + ' of ' + s.players.length +
        ' answered</div></div>';
  }} else if (s.state === 'reveal') {{
    h = '<div class="gcard"><div class="gsmall">The answer was</div>' +
        '<div class="gword">' + esc(s.answer_text) + '</div>' +
        '<div class="gsmall">' + esc(s.term) + '</div></div>' + board(s.board);
  }} else {{
    h = podium(s.board) + board(s.board.slice(3), 4);
  }}
  if (h !== last) {{ document.getElementById('board').innerHTML = h; last = h; }}
}}
function board(rows, from) {{
  if (!rows.length) return '';
  from = from || 1;
  return '<div class="tablewrap"><table><tr><th>#</th><th></th><th>Student</th>' +
    '<th></th><th>Right</th><th style="text-align:right">Points</th></tr>' +
    rows.map((r, i) => {{
      const d = r.delta > 0 ? '<span class="gup">&uarr;' + r.delta + '</span>'
              : r.delta < 0 ? '<span class="gdown">&darr;' + (-r.delta) + '</span>' : '';
      return '<tr><td>' + (i + from) + '.</td><td class="gcell">' + r.who +
        '</td><td>' + esc(r.name) + (r.run >= 2 ?
          ' <span class="grunmini">' + r.run + '🔥</span>' : '') +
        '</td><td>' + d + '</td><td>' + r.correct +
        '</td><td style="text-align:right"><strong>' + r.score + '</strong></td></tr>';
    }}).join('') + '</table></div>';
}}
function podium(rows) {{
  if (!rows.length) return '';
  const top = rows.slice(0, 3);
  const order = [1, 0, 2];   // second, first, third - the way a podium stands
  return '<div class="podium">' + order.filter(i => top[i]).map(i =>
    '<div class="pstep p' + (i + 1) + '"><div class="pface">' + top[i].who +
    '</div><div class="pname">' + esc(top[i].name) + '</div>' +
    '<div class="pscore">' + top[i].score + '</div>' +
    '<div class="pblock">' + (i + 1) + '</div></div>').join('') + '</div>';
}}
let busy = false;
async function step() {{
  if (busy) return;                 // one press is one move, however hard it is hit
  busy = true;
  const btn = document.getElementById('go');
  btn.disabled = true;
  btn.textContent = '\u2026';
  Music.nudge();                    // the gesture browsers require for audio
  try {{
    const r = await fetch('/play/' + GID + '/next', {{method:'POST'}});
    last = "";
    render(await r.json());         // straight from the reply, not the next poll
  }} catch (e) {{
    btn.disabled = false;
  }}
  busy = false;
}}
poll();
</script>"""
    return html_response(page("Game", body, "Play", music=True))


def game_state_json(req, db, game_id):
    g = db.execute("SELECT * FROM games WHERE id=?", (game_id,)).fetchone()
    if not g:
        return not_found()
    q = core.game_question(db, g)
    answered = 0
    term = answer_text = ""
    if q:
        term = db.execute("SELECT term FROM words WHERE id=?",
                          (q["word_id"],)).fetchone()["term"]
        answer_text = json.loads(q["options"])[q["answer"]]
        answered = db.execute(
            "SELECT COUNT(*) c FROM game_answers WHERE game_id=? AND question_id=?",
            (g["id"], q["id"])).fetchone()["c"]
    board = [{"name": r["name"], "score": r["score"], "correct": r["correct"],
              "who": core.avatar_of(r), "delta": r["delta"], "run": r["run"]}
             for r in core.game_board(db, g["id"])]
    payload = {"state": g["state"], "q_index": g["q_index"], "q_count": g["q_count"],
               "left": core.game_seconds_left(g), "term": term,
               "answer_text": answer_text, "answered": answered,
               "players": [{"name": b["name"], "who": b["who"]} for b in board],
               "board": board}
    return json_response(payload)


def act_game_next(req, db, game_id):
    """Advance, and answer with the state it just moved to.

    The board used to learn what happened from its next poll, which meant up
    to two seconds of nothing after a click - long enough that the teacher
    presses again, and the second press advances it a second time.
    """
    core.advance_game(db, game_id)
    return game_state_json(req, db, game_id)


def act_game_end(req, db, game_id):
    core.end_game(db, game_id)
    return redirect("/play")


def json_response(payload):
    blob = json.dumps(payload).encode("utf-8")
    return 200, [("Content-Type", "application/json; charset=utf-8"),
                 ("Cache-Control", "no-store"),
                 ("Content-Length", str(len(blob)))], blob


def view_student_game(req, db, token):
    """The phone. Four big targets, nothing to read but the answers."""
    s = core.student_by_token(db, token)
    if not s:
        return not_found()
    g = core.live_game(db, s["group_id"])
    if not g:
        body = ("<h1>No game running</h1><div class=\"card\"><p style=\"margin:0\">"
                "Your teacher has not started one. This page will work the moment "
                "they do.</p></div>"
                f"<p><a href=\"/s/{E(token)}\">Back to my page</a></p>")
        return html_response(student_page("Game", body))
    core.join_game(db, g["id"], s["id"])
    body = f"""<h1 style="margin-bottom:2px">Vocabulary game</h1>
<p class="sub" id="sub">Waiting for your teacher to start&hellip;</p>
<div id="play"></div>
<script>
const TOK = {json.dumps(token)};
const SHAPES = ['\u25B2', '\u25C6', '\u25CF', '\u25A0'];
let shown = -1, locked = false, last = "", ac = null, lastTick = -1, revealed = -1;
function esc(x) {{ return String(x).replace(/[&<>"]/g, c =>
  ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}})[c]); }}
// sound without files: two oscillators are enough for a tick and a ding
function beep(freq, ms, type) {{
  try {{
    ac = ac || new (window.AudioContext || window.webkitAudioContext)();
    const o = ac.createOscillator(), gain = ac.createGain();
    o.type = type || 'sine'; o.frequency.value = freq;
    gain.gain.setValueAtTime(0.14, ac.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.0001, ac.currentTime + ms / 1000);
    o.connect(gain); gain.connect(ac.destination);
    o.start(); o.stop(ac.currentTime + ms / 1000);
  }} catch (e) {{}}
}}
async function poll() {{
  try {{
    const r = await fetch('/s/' + TOK + '/game.json', {{cache:'no-store'}});
    render(await r.json());
  }} catch (e) {{}}
  setTimeout(poll, 1000);
}}
let AVATARS = [];
function chooser(s) {{
  AVATARS = s.avatars;
  return '<p class="sub" style="margin-bottom:6px">Pick your character</p>' +
    '<div class="gwho">' + s.avatars.map((a, i) =>
      '<button class="gpick' + (a === s.who ? ' on' : '') +
      '" onclick="pickWho(' + i + ')">' + a + '</button>').join('') +
    '</div>';
}}
function render(s) {{
  document.getElementById('sub').textContent = s.sub;
  let h = '';
  if (s.state === 'question') {{
    if (s.q !== shown) {{ shown = s.q; locked = s.answered; }}
    if (s.answered || s.left <= 0) locked = true;
    if (s.left <= 5 && s.left > 0 && s.left !== lastTick) {{
      lastTick = s.left; beep(880, 70);
    }}
    h = '<div class="gcard"><div class="gclock">' + s.left + '</div>' +
        '<div class="gword">' + esc(s.term) + '</div></div>' +
        '<div class="gopts">' + s.options.map((o, i) =>
          '<button class="gopt c' + i + (locked ? ' off' : '') + '" ' +
          (locked ? 'disabled' : 'onclick="pick(' + i + ')"') + '>' +
          '<span class="gshape">' + SHAPES[i] + '</span>' + esc(o) + '</button>').join('') +
        '</div>';
    if (locked) h += '<p class="sub">' + (s.answered ? 'Answer sent.' : 'Time up.') +
      ' Waiting for the others&hellip;</p>';
  }} else if (s.state === 'reveal') {{
    if (revealed !== s.q) {{
      revealed = s.q;
      if (s.was_right) {{ beep(660, 90); setTimeout(() => beep(990, 140), 100); }}
      else beep(180, 220, 'square');
    }}
    shown = -1; locked = false;
    const move = s.delta > 0 ? '<span class="gup">&uarr;' + s.delta + '</span>'
               : s.delta < 0 ? '<span class="gdown">&darr;' + (-s.delta) + '</span>' : '';
    h = '<div class="gcard ' + (s.was_right ? 'right' : 'wrong') + '">' +
        '<div class="gbig">' + (s.was_right ? 'Correct' : 'Not this time') + '</div>' +
        '<div class="gsmall">' + esc(s.term) + ' &mdash; ' + esc(s.answer_text) +
        '</div></div>' +
        (s.run >= 2 ? '<div class="grun">' + s.run + ' in a row 🔥</div>' : '') +
        '<div class="gcard"><div class="gsmall">Your points ' + move + '</div>' +
        '<div class="gbig">' + s.score + '</div></div>';
  }} else if (s.state === 'done') {{
    h = '<div class="gcard"><div class="gwhobig">' + s.who + '</div>' +
        '<div class="gsmall">Finished &mdash; you got ' + s.correct + ' right</div>' +
        '<div class="gbig">' + s.score + ' points</div>' +
        '<div class="gsmall">' + s.place + '</div></div>' +
        '<p><a href="/s/' + TOK + '">Back to my page</a></p>';
  }} else {{
    h = '<div class="gcard"><div class="gwhobig">' + s.who + '</div>' +
        '<div class="gbig">You are in</div>' +
        '<div class="gsmall">Look at the screen</div></div>' + chooser(s);
  }}
  if (h !== last) {{ document.getElementById('play').innerHTML = h; last = h; }}
}}
async function pick(i) {{
  locked = true; last = ""; beep(520, 60);
  await fetch('/s/' + TOK + '/game/answer', {{method:'POST',
    headers: {{'Content-Type':'application/x-www-form-urlencoded'}},
    body: 'choice=' + i}});
}}
async function pickWho(i) {{
  last = ""; beep(700, 60);
  await fetch('/s/' + TOK + '/game/avatar', {{method:'POST',
    headers: {{'Content-Type':'application/x-www-form-urlencoded'}},
    body: 'who=' + encodeURIComponent(AVATARS[i])}});
}}
poll();
</script>"""
    return html_response(student_page("Game", body))


def student_game_json(req, db, token):
    s = core.student_by_token(db, token)
    if not s:
        return not_found()
    g = core.live_game(db, s["group_id"]) or db.execute(
        "SELECT * FROM games WHERE group_id=? ORDER BY id DESC LIMIT 1",
        (s["group_id"],)).fetchone()
    if not g:
        return json_response({"state": "none", "sub": "No game running."})
    me = db.execute("SELECT * FROM game_players WHERE game_id=? AND student_id=?",
                    (g["id"], s["id"])).fetchone()
    out = {"state": g["state"], "score": me["score"] if me else 0,
           "correct": me["correct"] if me else 0, "sub": "", "q": g["q_index"],
           "run": me["run"] if me else 0, "delta": me["delta"] if me else 0,
           "who": core.avatar_of(s), "avatars": core.AVATARS}
    q = core.game_question(db, g)

    if g["state"] == "question" and q:
        opts = json.loads(q["options"])
        order = core.shuffle_for(s["id"], q["id"])
        out["options"] = [opts[i] for i in order]
        out["term"] = db.execute("SELECT term FROM words WHERE id=?",
                                 (q["word_id"],)).fetchone()["term"]
        out["left"] = int(core.game_seconds_left(g))
        out["answered"] = bool(db.execute(
            "SELECT 1 FROM game_answers WHERE game_id=? AND question_id=? AND student_id=?",
            (g["id"], q["id"], s["id"])).fetchone())
        out["sub"] = "Question %d of %d" % (g["q_index"] + 1, g["q_count"])
    elif g["state"] == "reveal" and q:
        opts = json.loads(q["options"])
        out["answer_text"] = opts[q["answer"]]
        out["term"] = db.execute("SELECT term FROM words WHERE id=?",
                                 (q["word_id"],)).fetchone()["term"]
        row = db.execute(
            "SELECT correct FROM game_answers WHERE game_id=? AND question_id=?"
            " AND student_id=?", (g["id"], q["id"], s["id"])).fetchone()
        out["was_right"] = bool(row and row["correct"])
        out["sub"] = "Question %d of %d" % (g["q_index"] + 1, g["q_count"])
    elif g["state"] == "done":
        board = core.game_board(db, g["id"])
        place = next((i for i, r in enumerate(board, 1)
                      if r["student_id"] == s["id"]), None)
        out["place"] = ("%d of %d" % (place, len(board))) if place else ""
        out["sub"] = "Game over"
    else:
        out["sub"] = "Waiting for your teacher to start…"
    return json_response(out)


def act_student_avatar(req, db, token):
    s = core.student_by_token(db, token)
    if not s:
        return not_found()
    core.set_avatar(db, s["id"], (req["form"].get("who", [""])[0] or ""))
    return json_response({"ok": True})


def act_student_answer(req, db, token):
    s = core.student_by_token(db, token)
    if not s:
        return not_found()
    g = core.live_game(db, s["group_id"])
    if not g:
        return json_response({"ok": False})
    raw = (req["form"].get("choice", [""])[0] or "").strip()
    if not raw.isdigit():
        return json_response({"ok": False})
    q = core.game_question(db, g)
    if not q:
        return json_response({"ok": False})
    # they tapped a position on their own shuffled screen; translate it back
    order = core.shuffle_for(s["id"], q["id"])
    shown = int(raw)
    if not 0 <= shown < len(order):
        return json_response({"ok": False})
    core.join_game(db, g["id"], s["id"])
    result = core.answer_game(db, g, s["id"], order[shown])
    return json_response({"ok": bool(result)})


def champ_row(db, r, show_group=True, me=None):
    st = r["student"]
    medals = {1: "&#129351;", 2: "&#129352;", 3: "&#129353;"}
    place = (medals.get(r["rank"], str(r["rank"]) + ".") if r["rank"]
             else '<span class="sub">&mdash;</span>')
    bars = ""
    for key, label, weight in core.CHAMPIONSHIP:
        got = r["points"].get(key)
        if got is None:
            bars += f'<td class="sub cnone" title="{E(label)}: nothing recorded">&mdash;</td>'
            continue
        share = got / weight * 100.0 if weight else 0
        bars += (f'<td class="cpt"><span class="cbar"><i style="width:'
                 f'{min(100, share):.0f}%"></i></span>{got:g}</td>')
    group = f'<td>{E(group_name(db, st["group_id"]))}</td>' if show_group else ""
    mine = ' class="me"' if me == st["id"] else ""
    seen = r.get("lessons", 0)
    of = core.SEASON_LESSONS
    lessons = (f'<td class="sub" title="season closed on {r["closed"]}">'
               f'{of}/{of} &#10003;</td>' if r.get("done")
               else f'<td class="sub">{seen}/{of}</td>')
    return (f'<tr{mine}><td>{place}</td>'
            f'<td><a href="/students/{st["id"]}">{E(st["name"])}</a></td>{group}'
            f'<td><strong>{r["total"]:g}</strong></td>{bars}{lessons}'
            f'<td class="sub">{E(r["handed"])}</td></tr>')


def view_championship(req, db):
    """The season table, with every student's parts on show.

    The breakdown is the point: a prize decided by numbers nobody can see is a
    prize people argue about.
    """
    full = core.championship(db)
    gid = (req["query"].get("class", [""])[0] or "").strip()
    gid = int(gid) if gid.isdigit() else None
    standing = core.scope_standing(full, gid) if gid else full
    past = core.past_seasons(db)

    history = ""
    if past:
        history = "<h2>Past seasons</h2><div class=\"tablewrap\"><table>" \
                  "<tr><th>Season</th><th>Winner</th><th>Points</th><th>Closed</th></tr>"
        for row in past:
            history += (f'<tr><td>{row["no"]}</td>'
                        f'<td><strong>{E(row["winner_name"] or "&mdash;")}</strong></td>'
                        f'<td>{row["winner_points"] or 0:g}</td>'
                        f'<td class="sub">{E(row["closed_at"][:10])}</td></tr>')
        history += "</table></div>"

    if not standing["started"]:
        body_html = f"""<h1>Championship</h1>
<p class="sub">The table is clear. Season {standing["season"]} begins the moment you
start it, and nothing recorded before that counts towards it.</p>
<div class="card"><h2 style="margin-top:0">Season {standing["season"]}</h2>
<p class="sub">A season runs for <strong>{core.SEASON_LESSONS} lessons per student</strong>,
not for a calendar month. A class that meets thirteen times and a class that meets twelve
are then judged over exactly the same amount of teaching. A student's season closes on
their {core.SEASON_LESSONS}th recorded lesson and their score is frozen there, however
long the rest of the school takes to catch up.</p>
<form method="post" action="/championship/start" style="margin-top:14px">
<button>Start season {standing["season"]}</button></form></div>
{history}"""
        return html_response(page("Championship", body_html, "League"))

    groups = db.execute("SELECT * FROM groups WHERE archived=0 ORDER BY name").fetchall()
    def ctab(href, label, on):
        return f'<a class="tab{" on" if on else ""}" href="{href}">{E(label)}</a>'
    scope = ('<div class="tabs">'
             + ctab("/championship", "Whole school", gid is None)
             + "".join(ctab(f'/championship?class={g["id"]}', g["name"], gid == g["id"])
                       for g in groups) + "</div>")

    head = "".join(f'<th title="{w} points">{E(l)}</th>'
                   for _k, l, w in core.CHAMPIONSHIP)
    body = "".join(champ_row(db, r, show_group=gid is None) for r in standing["rows"])

    winner = next((r for r in standing["rows"] if r["rank"] == 1), None)
    top = ""
    if winner:
        top = (f'<div class="champ-hero"><div class="sub">Leading season '
               f'{standing["season"]}</div>'
               f'<div class="champ-name">{E(winner["student"]["name"])}</div>'
               f'<div class="sub">{E(group_name(db, winner["student"]["group_id"]))}'
               f' &middot; {winner["total"]:g} of {core.CHAMPIONSHIP_MAX:g} points</div></div>')

    champs = {} if gid else core.class_champions(full, db)
    classes = ""
    for cid, r in sorted(champs.items(), key=lambda kv: group_name(db, kv[0])):
        classes += (f'<div class="quick"><div class="sub">{E(group_name(db, cid))}</div>'
                    f'<strong>{E(r["student"]["name"])}</strong>'
                    f'<div class="sub">{r["total"]:g} points</div></div>')

    total = len(standing["rows"])
    done = standing["finished"]
    if standing["paused"]:
        control = (f'<form method="post" action="/championship/resume">'
                   f'<button>Resume season {standing["season"]}</button></form>')
        paused = (f'<div class="card paused"><strong>The league is paused.</strong>'
                  f'<p class="sub" style="margin:6px 0 0">Paused since '
                  f'{E(standing["paused_at"][:10])}. Nothing counts while it is off: '
                  f'homework marked now, lessons taught now and words learnt now all '
                  f'stay out of the season, and nobody\'s lesson count moves. The table '
                  f'below is frozen exactly as it stood.</p>'
                  f'<div style="margin-top:12px">{control}</div></div>')
    else:
        paused = ""
        control = (f'<form method="post" action="/championship/pause">'
                   f'<button class="ghost">Pause the league</button></form>')
    rules = "".join(f'<li><strong>{E(l)}</strong> &mdash; up to {w:g} points</li>'
                    for _k, l, w in core.CHAMPIONSHIP)
    body_html = f"""<h1>Championship</h1>
<p class="sub">Season {standing["season"]}, started {E(standing["start"][:10])}.
{core.SEASON_LESSONS} lessons each, {core.CHAMPIONSHIP_MAX:g} points, everyone in the school.
Homework is the average of the marks you give &mdash; not how many pieces &mdash; so two
classes set different amounts of work still stand in the same table. Anything handed in
after its deadline counts as a nought in that average.</p>
{top}
{paused}
<div class="card"><strong>{done} of {total}</strong> students have finished their
{core.SEASON_LESSONS} lessons.
<p class="sub" style="margin:6px 0 0">A student's lesson count only moves when you record
their marks for that day, so the season advances at the speed you record it. Close the
season when enough of them have finished: the table is written into the record book with
the winner's name, and the next season starts clear from that moment.</p>
<div class="seasonbtns">
<form method="post" action="/championship/close"
 onsubmit="return confirm('Close season {standing["season"]} and start the next one? The table is kept in the record book.')">
<button class="danger">Close season {standing["season"]}</button></form>
{"" if standing["paused"] else control}</div></div>
{"<h2>Class champions</h2><div class='quicklinks'>" + classes + "</div>" if classes else ""}
<h2>The table</h2>
{scope}
<p class="sub">{standing["eligible"]} of {total} students have the
{core.MIN_GRADED} marked pieces needed to be eligible. The rest are listed below the
line and cannot win this season.</p>
<div class="tablewrap"><table><tr><th>#</th><th>Student</th>
{"<th>Group</th>" if gid is None else ""}
<th>Total</th>{head}<th>Lessons</th><th>Handed in</th></tr>
{body or '<tr><td colspan=11 class="sub">Nobody yet.</td></tr>'}</table></div>
<h2>How the points work</h2>
<div class="card"><ul class="rules">{rules}</ul>
<p class="sub" style="margin:10px 0 0">Homework is the average mark out of ten, scaled to
3; a piece handed in after its deadline is a nought in that average. Words count up to
{core.VOCAB_TARGET}. In the lesson is the average of punctuality, behaviour and taking
part. A student needs {core.MIN_GRADED} marked pieces to be eligible &mdash; otherwise one
lucky ten out of ten decides the season. Nothing you have not recorded scores anything, so
an unmarked lesson is a nought for everyone alike and the order of the table is
unaffected.</p></div>
{history}"""
    return html_response(page("Championship", body_html, "League"))


def act_start_season(req, db):
    core.start_season(db)
    return redirect("/championship")


def act_close_season(req, db):
    core.close_season(db)
    return redirect("/championship")


def act_pause_season(req, db):
    core.pause_season(db)
    return redirect("/championship")


def act_resume_season(req, db):
    core.resume_season(db)
    return redirect("/championship")


def view_export(req, db):
    gid = req["query"].get("group", [None])[0]
    gid = int(gid) if gid and gid.isdigit() else None
    out = ["rank,name,group,overall_score,completion_percent,average_score,"
           "lesson_mark,change_this_month,graded,missed,streak,words_known"]
    for r in core.rating_rows(db, gid):
        st = r["student"]
        name = '"%s"' % st["name"].replace('"', "'")
        out.append(",".join(str(x) for x in [
            r["rank"], name, '"%s"' % group_name(db, st["group_id"]),
            r["index"] if r["index"] is not None else "",
            r["completion"] if r["completion"] is not None else "",
            r["average"] if r["average"] is not None else "",
            r["marks"] if r["marks"] is not None else "",
            r["gain"] if r["gain"] is not None else "",
            r["graded"], r["missed"], r["streak"], r["vocab"],
        ]))
    payload = "\n".join(out).encode("utf-8-sig")   # BOM so Excel reads it correctly
    return 200, [("Content-Type", "text/csv; charset=utf-8"),
                 ("Content-Disposition", 'attachment; filename="ratings.csv"'),
                 ("Content-Length", str(len(payload)))], payload


def crumbs(db, level_id, coll, cat, unit, base):
    bits = [f'<a class="crumb" href="{base[:-1]}">All sections</a>']
    if coll:
        bits.append(f'<a class="crumb" href="{base}c={coll}">'
                    f'{E(core.collection_label(coll))}</a>')
    if cat:
        bits.append(f'<a class="crumb" href="{base}c={coll}&amp;s={E(cat)}">{E(cat)}</a>')
    if unit is not None:
        bits.append("Welcome" if unit == 0
                    else "%s %d" % (core.unit_word(coll), unit))
    return '<p class="sub">' + " &rsaquo; ".join(bits) + "</p>"


def tile(href, title, sub, small=False, empty=False):
    return (f'<a class="tile{" small" if small else ""}{" empty" if empty else ""}"'
            f' href="{href}"><div class="tile-title">{title}</div>'
            f'<div class="sub" style="margin:0">{sub}</div></a>')


def unit_files(db, level_id, coll, cat, unit):
    """Unit -1 is the drawer for anything filed without a unit number."""
    if unit is None:
        return core.materials_at_level(db, level_id, coll, cat)
    if unit == -1:
        return [m for m in core.materials_at_level(db, level_id, coll, cat)
                if not m["unit"]]
    return core.materials_in_unit(db, level_id, coll, cat, unit)


def level_tiles(db, levels):
    """No level picked yet - show the shelves rather than every file at once."""
    cards = ""
    for l in levels:
        n = len(core.materials_at_level(db, l["id"]))
        cards += tile(f'/materials?level={l["id"]}', E(l["name"]),
                      "%d files" % n, empty=not n)
    return ('<p class="sub">Pick a level, or search above.</p>'
            f'<div class="tiles">{cards}</div>')


def shelf_tiles(db, level_id, base):
    """Collections first - the same three steps students take in the bot."""
    counts = core.collection_counts(db, level_id)
    cards = "".join(
        tile(f'{base}c={k}', E(core.collection_label(k)), "%d files" % counts.get(k, 0))
        for k in core.COLLECTION_ORDER)
    return f'<div class="tiles">{cards}</div>'


def section_tiles(db, level_id, coll, base):
    counts = core.level_counts(db, level_id, coll)
    cards = "".join(
        tile(f'{base}c={coll}&amp;s={urllib.parse.quote(name)}', E(name),
             "%d files" % counts.get(name, 0), empty=not counts.get(name))
        for name in core.sections(coll))
    return (crumbs(db, level_id, coll, "", None, base)
            + f'<div class="tiles">{cards}</div>')


def test_tiles(db, level_id, coll, base):
    """Twenty buttons - Test 1 to Test 20 - each holding everything for that test."""
    have = core.units_across(db, level_id, coll)
    href = f'{base}c={coll}'
    cards = "".join(
        tile(f'{href}&amp;u={n}', "Test %d" % n,
             "%d file%s" % (have[n], "" if have[n] == 1 else "s") if n in have else "empty",
             small=True, empty=n not in have)
        for n in core.tests_in_collection(coll))
    return (crumbs(db, level_id, coll, None, None, base)
            + f'<div class="tiles">{cards}</div>')


def test_files(db, level_id, coll, unit, base):
    """One test: the paper, its audio and its answers, labelled and together."""
    rows = core.files_in_test(db, level_id, coll, unit)
    order = {name: i for i, name in enumerate(core.sections(coll))}
    rows = sorted(rows, key=lambda m: (order.get(m["category"], 99), m["title"]))
    if not rows:
        body = ('<div class="card"><p style="margin:0" class="sub">Nothing here yet.'
                '</p></div>')
    else:
        items = ""
        for m in rows:
            kind = m["category"] or "File"
            size = "%.1f MB" % ((m["size"] or 0) / 1048576.0)
            player = ""
            if is_audio(m["original_name"] or m["filename"]):
                player = (f'<audio controls preload="none" class="voice"'
                          f' src="/materials/{m["id"]}/file"></audio>')
            items += (f'<div class="testfile"><div>'
                      f'<span class="pill mute">{E(kind)}</span> '
                      f'<a href="/materials/{m["id"]}/file">{E(m["title"])}</a>'
                      f'<div class="sub">{E(size)}</div></div>{player}</div>')
        body = f'<div class="card">{items}</div>'
    return crumbs(db, level_id, coll, None, unit, base) + body


def unit_tiles(db, level_id, coll, cat, base):
    units = core.units_in(db, level_id, coll, cat)
    numbers = core.units_for_level(db, level_id)
    if 0 in units:
        numbers = [0] + numbers
    href = f'{base}c={coll}&amp;s={urllib.parse.quote(cat)}'
    cards = "".join(
        tile(f'{href}&amp;u={n}', "Welcome" if n == 0 else "Unit %d" % n,
             "%d files" % units.get(n, 0), small=True, empty=n not in units)
        for n in numbers)
    loose = [m for m in core.materials_at_level(db, level_id, coll, cat) if not m["unit"]]
    if loose:
        cards += tile(f'{href}&amp;u=-1', "No unit", "%d files" % len(loose), small=True)
    return (crumbs(db, level_id, coll, cat, None, base)
            + f'<div class="tiles">{cards}</div>')


def material_hits(db, q, level_id):
    """Type a track number and get the file - faster than walking the tree."""
    like = "%" + q.replace("%", "") + "%"
    sql = ("SELECT * FROM materials WHERE active=1 AND (title LIKE ? OR original_name LIKE ?)")
    args = [like, like]
    if level_id:
        sql += " AND (level_id IS NULL OR level_id IS ?)"
        args.append(level_id)
    mats = db.execute(sql + " ORDER BY title LIMIT 200", args).fetchall()
    head = f'<p class="sub">{len(mats)} match{"" if len(mats) == 1 else "es"} for "{E(q)}"</p>'
    return material_table(db, mats, head)


def material_table(db, mats, head):
    if not mats:
        return head + ('<div class="card"><p style="margin:0">Nothing here yet.</p></div>')
    rows = ""
    for m in mats:
        scope = core.level_name(db, m["level_id"]) or "All levels"
        if m["unit"]:
            scope += " · Unit %d" % m["unit"]
        if m["book"]:
            scope += " · " + core.book_label(m["book"])
        if m["group_id"]:
            scope += " · " + group_name(db, m["group_id"])
        note = (f'<div class="sub" style="margin:2px 0 0">{E(m["note"])}</div>'
                if m["note"] else "")
        rows += (f'<tr><td><a href="/materials/{m["id"]}/file">{E(m["title"])}</a>{note}</td>'
                 f'<td>{E(scope)}</td><td class="sub">{E(m["original_name"] or "")}</td>'
                 f'<td>{E(core.human_size(m["size"]))}</td>'
                 f'<td><form method="post" action="/materials/{m["id"]}/delete">'
                 f'<button class="ghost">Remove</button></form></td></tr>')
    return (head + '<div class="tablewrap"><table><tr><th>Title</th><th>Level</th>'
            '<th>File</th><th>Size</th><th></th></tr>' + rows + "</table></div>")


def view_materials(req, db):
    groups = db.execute("SELECT * FROM groups WHERE archived=0 ORDER BY name").fetchall()
    levels = db.execute("SELECT * FROM levels ORDER BY sort").fetchall()
    only = req["query"].get("level", [None])[0]
    only = int(only) if only and only.isdigit() else None

    def tab(href, label, on):
        return f'<a class="tab{" on" if on else ""}" href="{href}">{E(label)}</a>'
    tabs = ('<div class="tabs">' + tab("/materials", "All levels", only is None)
            + "".join(tab(f'/materials?level={l["id"]}', l["name"], only == l["id"])
                      for l in levels) + "</div>")

    q = (req["query"].get("q", [""])[0] or "").strip()
    coll = (req["query"].get("c", [""])[0] or "")
    cat = (req["query"].get("s", [""])[0] or "")
    unit = req["query"].get("u", [None])[0]
    unit = int(unit) if unit and unit.lstrip("-").isdigit() else None

    base = "/materials" + (f"?level={only}" if only else "?")
    if not base.endswith(("?", "&")):
        base += "&"

    search = f'''<div class="card" style="padding:12px 14px">
<form method="get" action="/materials" class="inline">
  {f'<input type="hidden" name="level" value="{only}">' if only else ""}
  <input name="q" value="{E(q)}" placeholder="Search by name, e.g. 8.03 or transcripts"
         style="min-width:280px">
  <button class="ghost">Search</button>
  {f'<a class="mini" href="{base[:-1]}">Clear</a>' if q else ""}
</form></div>'''

    if q:
        blocks = search + material_hits(db, q, only)
    elif not only:
        blocks = search + level_tiles(db, levels)
    elif not coll or coll not in core.COLLECTIONS:
        blocks = search + shelf_tiles(db, only, base)
    elif core.is_test_shelf(coll):
        blocks = search + (test_tiles(db, only, coll, base) if unit is None
                           else test_files(db, only, coll, unit, base))
    elif not cat:
        blocks = search + section_tiles(db, only, coll, base)
    elif unit is None and core.units_in(db, only, coll, cat):
        blocks = search + unit_tiles(db, only, coll, cat, base)
    else:
        blocks = search + material_table(
            db, unit_files(db, only, coll, cat, unit),
            crumbs(db, only, coll, cat, unit, base))

    lopts = ('<option value="">All levels</option>'
             + "".join(f'<option value="{l["id"]}">{E(l["name"])}</option>' for l in levels))
    kopts = "".join(f'<option value="{k}">{E(core.collection_label(k))}</option>'
                    for k in core.COLLECTION_ORDER)
    gopts = ('<option value="">Every class at that level</option>'
             + "".join(f'<option value="{g["id"]}">{E(g["name"])}</option>' for g in groups))
    # the list covers both shelves: units for a coursebook, tests for the
    # practice shelf, which runs past twelve
    highest = max([len(core.UNITS)] + list(core.TEST_COLLECTIONS.values()))
    uopts = ('<option value="">— none —</option>'
             + "".join(f'<option value="{n}">{n}</option>'
                       for n in range(1, highest + 1)))
    bopts = ('<option value="">— none —</option>'
             + "".join(f'<option value="{k}">{E(v)}</option>'
                       for k, v in core.BOOKS.items()))
    sections_json = json.dumps({k: core.sections(k) for k in core.COLLECTION_ORDER})
    body = f"""<h1>Materials</h1>
<p class="sub">Filed by level, then collection, then section — the same tree students
walk through in the bot.</p>
{tabs}
{blocks}
<details class="adder"><summary>Add a file</summary>
<div class="card"><form method="post" action="/materials/new" enctype="multipart/form-data">
<div class="inline" style="margin-bottom:12px">
<label class="f">Title<input name="title" placeholder="Unit 5 handout" required></label>
<label class="f">Level<select name="level_id">{lopts}</select></label>
<label class="f">Collection<select name="collection" id="coll"
  data-sections="{E(sections_json)}">{kopts}</select></label>
<label class="f">Section<select name="category" id="sect"></select></label>
<label class="f">Class<select name="group_id">{gopts}</select></label>
<label class="f">Unit / Test<select name="unit" id="unitsel">{uopts}</select></label>
<label class="f">Book<select name="book">{bopts}</select></label>
</div>
<label class="f" style="margin-bottom:12px">Note (optional)
<input name="note" placeholder="Read before Monday" style="width:100%"></label>
<label class="dropzone">
  <input type="file" name="file" required
         onchange="this.closest('.dropzone').classList.add('has');
                   this.nextElementSibling.textContent = this.files[0].name;">
  <span class="dz-label">Choose a file</span>
  <span class="dz-hint">PDF, Word, PowerPoint, images, audio or video. Up to 45 MB —
  Telegram's limit for what a bot can send.</span>
</label>
<div style="margin-top:12px"><button>Upload</button></div></form></div>
</details>"""
    return html_response(page("Materials", body, "Materials"))


def act_new_material(req, db):
    fields, files = req["files"]
    title = (fields.get("title", [""])[0] or "").strip()
    if not title or not files:
        return redirect("/materials")
    original, blob = files[0]
    if len(blob) > 45 * 1024 * 1024:
        return redirect("/materials")
    gid = (fields.get("group_id", [""])[0] or "").strip()
    ext = uploads.safe_ext(original)
    name = f"m{int(core.now().timestamp())}_{secrets.token_hex(4)}{ext}"
    with open(os.path.join(core.MATERIAL_DIR, name), "wb") as fh:
        fh.write(blob)
    lid = (fields.get("level_id", [""])[0] or "").strip()
    collection = (fields.get("collection", [""])[0] or "").strip()
    if collection not in core.COLLECTIONS:
        collection = core.COLLECTION_ORDER[0]
    category = (fields.get("category", [""])[0] or "").strip()
    if category not in core.sections(collection):
        category = core.sections(collection)[0]
    raw_unit = (fields.get("unit", [""])[0] or "").strip()
    # 0 is the Welcome unit - it is a real unit for filing, it just sits
    # before Unit 1 and so is not in core.UNITS. The practice shelf counts
    # tests instead, and there are twenty of those.
    allowed = (core.tests_in_collection(collection)
               if core.is_test_shelf(collection) else core.UNITS)
    unit = (int(raw_unit) if raw_unit.isdigit()
            and (int(raw_unit) in allowed or int(raw_unit) == 0) else None)
    book = (fields.get("book", [""])[0] or "").strip()
    book = book if book in core.BOOKS else None
    db.execute(
        "INSERT INTO materials (group_id, title, note, filename, original_name, mime,"
        " size, created_at, level_id, category, collection, unit, book)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (int(gid) if gid.isdigit() else None, title[:120],
         (fields.get("note", [""])[0] or "").strip()[:300] or None,
         name, original[:150], uploads.content_type(original), len(blob),
         core.iso(core.now()), int(lid) if lid.isdigit() else None, category,
         collection, unit, book),
    )
    db.commit()
    return redirect("/materials")


def act_delete_material(req, db, mid):
    row = db.execute("SELECT * FROM materials WHERE id=?", (mid,)).fetchone()
    if row:
        path = os.path.join(core.MATERIAL_DIR, row["filename"])
        if os.path.exists(path):
            os.remove(path)
        db.execute("DELETE FROM materials WHERE id=?", (mid,))
        db.commit()
    return redirect("/materials")


def serve_material(db, mid, student=None):
    row = db.execute("SELECT * FROM materials WHERE id=? AND active=1", (mid,)).fetchone()
    if not row:
        return not_found()
    if student is not None:
        # a student may only reach their own level's shelf
        own = core.level_of(db, student["group_id"])
        if row["level_id"] not in (None, own):
            return not_found()
        if row["group_id"] not in (None, student["group_id"]):
            return not_found()
    path = os.path.join(core.MATERIAL_DIR, row["filename"])
    if not os.path.isfile(path):
        return not_found()
    with open(path, "rb") as fh:
        blob = fh.read()
    fname = (row["original_name"] or row["filename"]).replace('"', "")
    return 200, [("Content-Type", row["mime"] or "application/octet-stream"),
                 ("Content-Disposition", f'inline; filename="{fname}"'),
                 ("Content-Length", str(len(blob)))], blob


def view_music(req, db):
    """One song a day, chosen by hand.

    Deliberately manual: the point is that the teacher picks it, so students
    arrive to something a person chose rather than a playlist.
    """
    cfg = core.load_config()
    today = core.local_day(core.now(), cfg)
    day = (req["query"].get("day", [""])[0] or "").strip()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", day):
        day = today
    note = (req["query"].get("note", [""])[0] or "").strip()
    song = core.song_for(db, day)
    used, count = core.music_bytes(db)

    notes = {"big": "That file is over 20 MB. Save it smaller, or pick a shorter track.",
             "type": "That is not an audio file. Use mp3, m4a, ogg, wav or flac.",
             "none": "No file was chosen.",
             "saved": "Saved. Everyone will hear it today.",
             "gone": "Removed."}
    banner = (f'<div class="card {"paused" if note != "saved" else "good"}">'
              f'{E(notes[note])}</div>' if note in notes else "")

    if song:
        name = E(song["title"] or song["original_name"] or "Today's song")
        by = f' <span class="sub">&mdash; {E(song["artist"])}</span>' if song["artist"] else ""
        current = f"""<div class="card">
<div class="sub">Playing on {E(day)}{" (today)" if day == today else ""}</div>
<h2 style="margin:4px 0 10px">{name}{by}</h2>
<audio controls preload="none" style="width:100%" src="/song/{E(day)}"></audio>
<p class="sub" style="margin:10px 0 0">{song["bytes"] / 1024.0 / 1024.0:.1f} MB
&middot; uploaded {E(song["created_at"][:16].replace("T", " "))}</p>
<form method="post" action="/music/delete" style="margin-top:10px"
 onsubmit="return confirm('Remove the song for {E(day)}?')">
<input type="hidden" name="day" value="{E(day)}">
<button class="ghost danger">Remove this song</button></form></div>"""
    else:
        current = (f'<div class="card"><div class="sub">Nothing set for {E(day)}'
                   f'{" (today)" if day == today else ""}.</div></div>')

    rows = ""
    missing = 0
    for r in core.recent_songs(db, 30):
        here = ' class="me"' if r["day"] == today else ''
        # a row whose file has gone would otherwise fail silently, playing
        # nothing and looking exactly like a day nobody set a song for
        ok = os.path.isfile(os.path.join(core.MUSIC_DIR, r["filename"]))
        if not ok:
            missing += 1
        state = ('<span class="sub">on disk</span>' if ok
                 else '<strong class="gone">file missing</strong>')
        rows += (f'<tr{here}>'
                 f'<td><a href="/music?day={r["day"]}">{r["day"]}</a></td>'
                 f'<td>{E(r["title"] or r["original_name"] or "&mdash;")}</td>'
                 f'<td class="sub">{E(r["artist"] or "")}</td>'
                 f'<td class="sub">{r["bytes"] / 1024.0 / 1024.0:.1f} MB</td>'
                 f'<td>{state}</td></tr>')

    body = f"""<h1>Song of the day</h1>
<p class="sub">One track a day for the whole school. Students hear it on their pages,
and so do you &mdash; the &#9834; button in the corner turns it on and off, and it is
remembered per person, so anyone who wants silence keeps silence.</p>
{banner}
{current}
<div class="card"><h2 style="margin-top:0">Set a song</h2>
<form method="post" action="/music/new" enctype="multipart/form-data">
<label>Day<input type="date" name="day" value="{E(day)}"></label>
<label>Song file
<input type="file" name="song" accept="audio/*,.mp3,.m4a,.ogg,.wav,.flac" required></label>
<label>Title <span class="sub">(optional)</span>
<input name="title" maxlength="120" placeholder="Shown to the students"></label>
<label>Artist <span class="sub">(optional)</span>
<input name="artist" maxlength="120"></label>
<div style="margin-top:12px"><button>Set the song</button></div>
</form>
<p class="sub" style="margin:12px 0 0">mp3, m4a, ogg, wav or flac, up to 20 MB. Setting a
song for a day that already has one replaces it. Works from a phone: the file picker
opens your music or your downloads.</p></div>
<h2>Recent days</h2>
<p class="sub">{count} songs stored, {used / 1024.0 / 1024.0:.0f} MB in all.</p>
<div class="tablewrap"><table><tr><th>Day</th><th>Title</th><th>Artist</th>
<th>Size</th><th>File</th></tr>
{rows or '<tr><td colspan=5 class="sub">Nothing yet.</td></tr>'}
</table></div>
{f'<div class="card paused">{missing} of these have lost their audio file. The day is'
 ' still listed but nothing will play; set the song again for that day.</div>'
 if missing else ''}"""
    return html_response(page("Song of the day", body, "Music"))


def act_new_song(req, db):
    fields, files = req["files"]
    cfg = core.load_config()
    day = (fields.get("day", [""])[0] or "").strip()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", day):
        day = core.local_day(core.now(), cfg)
    if not files:
        return redirect(f"/music?day={day}&note=none")
    filename, blob = files[0]
    try:
        core.save_song(db, day, filename, blob,
                       fields.get("title", [""])[0], fields.get("artist", [""])[0])
    except ValueError as exc:
        return redirect(f"/music?day={day}&note="
                        + ("big" if "large" in str(exc) else "type"))
    forget_song()
    return redirect(f"/music?day={day}&note=saved")


def act_delete_song(req, db):
    day = (req["form"].get("day", [""])[0] or "").strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", day):
        core.delete_song(db, day)
    forget_song()
    return redirect(f"/music?day={day}&note=gone")


SONG_READ = 64 * 1024


def song_range(db, day, rng):
    """Work out what to send for a song request, without reading the file.

    Returns (status, headers, path, start, length). The body is streamed from
    disk afterwards, so a whole-file response costs 64 KB of memory rather than
    the size of the track - which is why nothing here caps the range. Handing
    back a slice would mean the player coming back for more mid-song, and that
    round trip is audible.
    """
    row = core.song_for(db, day) if day else core.song_today(db)
    if not row:
        return None
    path = os.path.join(core.MUSIC_DIR, row["filename"])
    if not os.path.isfile(path):
        return None
    size = os.path.getsize(path)
    m = re.match(r"bytes=(\d*)-(\d*)$", (rng or "").strip())
    start, end, partial = 0, size - 1, False
    if m and (m.group(1) or m.group(2)):
        if m.group(1):
            start = int(m.group(1))
            if m.group(2):
                end = min(int(m.group(2)), size - 1)
        else:                                   # bytes=-N, the last N bytes
            start = max(0, size - int(m.group(2)))
        if start >= size or start > end:
            return (416, [("Content-Range", "bytes */%d" % size),
                          ("Content-Length", "0")], None, 0, 0)
        partial = True
    length = end - start + 1
    headers = [("Content-Type", row["mime"]),
               ("Accept-Ranges", "bytes"),
               ("Content-Length", str(length)),
               # the url carries the upload stamp, so a cached copy is never
               # stale: this is what stops every page click refetching the song
               ("Cache-Control", "public, max-age=31536000, immutable")]
    if partial:
        headers.append(("Content-Range", "bytes %d-%d/%d" % (start, end, size)))
    return (206 if partial else 200, headers, path, start, length)


def view_material_file(req, db, mid):
    return serve_material(db, mid)


# ----------------------------------------------------------------- actions

def save_grade(db, sub, form):
    """Write one mark, from either the queue or a correction. Returns the score."""
    assignment = (db.execute("SELECT * FROM assignments WHERE id=?",
                             (sub["assignment_id"],)).fetchone()
                  if sub["assignment_id"] else None)
    if assignment and assignment["rubric"]:
        score = core.set_criteria(
            db, sub["id"],
            {k: form.get("c_" + k, [""])[0] for k in core.CRITERIA_KEYS})
    else:
        score = core.mark_score(form.get("score", [""])[0])
    if score is None:
        return None
    note = (form.get("note", [""])[0] or "").strip() or None
    db.execute(
        "UPDATE submissions SET status='graded', score=?, note=?, graded_at=? WHERE id=?",
        (score, note, core.iso(core.now()), sub["id"]))
    db.execute("DELETE FROM submission_tags WHERE submission_id=?", (sub["id"],))
    for t in form.get("tag", []):
        if t.strip().isdigit():
            db.execute(
                "INSERT OR IGNORE INTO submission_tags (submission_id, tag_id) VALUES (?,?)",
                (sub["id"], int(t)))
    db.commit()
    core.used_note(db, note)
    return score


def act_grade(req, db):
    sid = int(req["form"].get("submission_id", [0])[0])
    sub = db.execute("SELECT * FROM submissions WHERE id=?", (sid,)).fetchone()
    if not sub or save_grade(db, sub, req["form"]) is None:
        return redirect("/queue")
    try:
        notify_graded(db, sid)
    except Exception:
        # the score is saved either way; telling the student is best effort and
        # must never put an error page in front of the person marking
        traceback.print_exc()
    return redirect("/queue")


def act_regrade(req, db):
    """Change a mark that was already given, and tell the student if it moved."""
    sid = int(req["form"].get("submission_id", [0])[0])
    sub = db.execute("SELECT * FROM submissions WHERE id=?", (sid,)).fetchone()
    if not sub:
        return redirect("/queue")
    was = sub["score"]
    score = save_grade(db, sub, req["form"])
    if score is None:
        return redirect("/regrade/%d" % sid)
    if was is None or abs((was or 0) - score) > 1e-9:
        # only when the number actually moved: a corrected tag is not news
        try:
            notify_graded(db, sid)
        except Exception:
            traceback.print_exc()
    back = (req["form"].get("back", [""])[0] or "").strip()
    return redirect(back if back.startswith("/") else "/queue")


def act_new_note(req, db):
    core.add_note_template(db, req["form"].get("text", [""])[0])
    return redirect("/queue")


def act_delete_note(req, db):
    tid = (req["form"].get("id", [""])[0] or "").strip()
    if tid.isdigit():
        core.delete_note_template(db, int(tid))
    return redirect("/queue")


def notify_graded(db, sid):
    """Tell the student their score, if a bot token is configured."""
    token = CFG.get("telegram_token")
    if not token:
        return
    row = db.execute(
        "SELECT s.score, s.note, st.id sid, st.telegram_id, st.lang, a.title"
        " FROM submissions s"
        " JOIN students st ON st.id=s.student_id"
        " LEFT JOIN assignments a ON a.id=s.assignment_id WHERE s.id=?",
        (sid,),
    ).fetchone()
    if not row or not row["telegram_id"]:
        return
    tags = [
        r["label"]
        for r in db.execute(
            "SELECT label FROM tags JOIN submission_tags ON tags.id=tag_id WHERE submission_id=?",
            (sid,),
        ).fetchall()
    ]
    import bot  # local import keeps the web app importable without the bot

    bot.send_score(token, row["telegram_id"], row["lang"], row["title"], row["score"],
                   tags, row["note"], sid, student_id=row["sid"])


def act_skip(req, db):
    sid = req["form"].get("submission_id", [None])[0] or req["query"].get("submission_id", [None])[0]
    if sid:
        # push to the back of the queue rather than dropping it
        db.execute("UPDATE submissions SET created_at=? WHERE id=?", (core.iso(core.now()), int(sid)))
        db.commit()
    return redirect("/queue")


def act_new_group(req, db):
    name = (req["form"].get("name", [""])[0] or "").strip()
    lid = (req["form"].get("level_id", [""])[0] or "").strip()
    if name:
        db.execute(
            "INSERT INTO groups (name, join_code, created_at, level_id) VALUES (?,?,?,?)",
            (name, core.new_join_code(db), core.iso(core.now()),
             int(lid) if lid.isdigit() else None),
        )
        db.commit()
    return redirect("/groups")


def act_set_group_level(req, db, gid):
    lid = (req["form"].get("level_id", [""])[0] or "").strip()
    db.execute("UPDATE groups SET level_id=? WHERE id=?",
               (int(lid) if lid.isdigit() else None, gid))
    db.commit()
    return redirect("/groups")


def act_repeat_homework(req, db, gid):
    """Give the same list of tasks again with a new deadline.

    Setting homework is the most repetitive thing on the site: the same six or
    seven tasks, a week later. This is that, in one press.
    """
    due = (req["form"].get("due", [""])[0] or "").strip()
    if not due:
        return redirect(f"/groups/{gid}?tab=homework")
    due_iso = core.deadline_iso(due, f.get("due_time", [""])[0])
    made = []
    for a in core.last_homework_batch(db, gid):
        if already_set(db, gid, a["title"], due_iso):
            continue
        made.append(db.execute(
            "INSERT INTO assignments (group_id, title, task_type, due_at, created_at,"
            " published) VALUES (?,?,?,?,?,1)",
            (gid, a["title"], a["task_type"], due_iso, core.iso(core.now())),
        ).lastrowid)
    db.commit()
    if made and req["form"].get("announce", [""])[0] == "1":
        for aid in made:
            announce(db, aid)
    return redirect(f"/groups/{gid}?tab=homework")


def announce(db, aid):
    token = core.load_config().get("telegram_token")
    if not token:
        return 0
    import bot
    return bot.announce_assignment(token, db, aid)


def act_publish_assignment(req, db, aid):
    db.execute("UPDATE assignments SET published=1 WHERE id=?", (aid,))
    db.commit()
    if req["form"].get("announce", [""])[0] == "1":
        announce(db, aid)
    return redirect("/assignments")


def act_unpublish_assignment(req, db, aid):
    db.execute("UPDATE assignments SET published=0 WHERE id=?", (aid,))
    db.commit()
    return redirect("/assignments")


def parse_list(text):
    """One homework item per line. Strips '1.', '1)', '-' and '•' prefixes."""
    items = []
    for line in (text or "").splitlines():
        line = re.sub(r"^\s*(?:\d+\s*[.)\]]|[-*\u2022])\s*", "", line).strip()
        if line:
            items.append(line[:120])
    return items


def already_set(db, group_id, title, due_iso):
    """Guards against a double-click posting the same list twice."""
    return db.execute(
        "SELECT id FROM assignments WHERE group_id=? AND title=? AND closed=0"
        " AND (due_at IS ? OR due_at=?)",
        (group_id, title, due_iso, due_iso),
    ).fetchone() is not None



def _batch_of(req, db):
    """The (group, deadline) pair a batch form is pointing at."""
    f = req["form"]
    gid = (f.get("group_id", [""])[0] or "").strip()
    if not gid.isdigit():
        return None, None, []
    due = (f.get("due", [""])[0] or "").strip() or None
    return int(gid), due, core.set_items(db, int(gid), due)


def act_batch_close(req, db):
    gid, due, items = _batch_of(req, db)
    for a in items:
        db.execute("UPDATE assignments SET closed=1 WHERE id=?", (a["id"],))
    db.commit()
    return redirect("/assignments")


def act_batch_open(req, db):
    gid, due, items = _batch_of(req, db)
    for a in items:
        db.execute("UPDATE assignments SET closed=0 WHERE id=?", (a["id"],))
    db.commit()
    return redirect("/assignments")


def act_batch_publish(req, db):
    gid, due, items = _batch_of(req, db)
    fresh = [a["id"] for a in items if not a["published"]]
    for aid in fresh:
        db.execute("UPDATE assignments SET published=1 WHERE id=?", (aid,))
    db.commit()
    if fresh and gid:
        try:
            announce_list(db, gid, fresh)
        except Exception:
            traceback.print_exc()
    return redirect("/assignments")


def act_batch_delete(req, db):
    """Remove a whole batch, but never the students' marked work."""
    gid, due, items = _batch_of(req, db)
    for a in items:
        db.execute("UPDATE submissions SET assignment_id=NULL WHERE assignment_id=?",
                   (a["id"],))
        db.execute("DELETE FROM assignments WHERE id=?", (a["id"],))
    db.commit()
    return redirect("/assignments")


def act_batch_edit(req, db):
    """Move the deadline for every item that was set together."""
    gid, due, items = _batch_of(req, db)
    f = req["form"]
    when = core.deadline_iso(f.get("new_due", [""])[0], f.get("new_time", [""])[0])
    for a in items:
        db.execute("UPDATE assignments SET due_at=? WHERE id=?", (when, a["id"]))
    # a piece handed in before the new deadline is no longer late
    for a in items:
        db.execute(
            "UPDATE submissions SET late=CASE WHEN ? IS NOT NULL AND created_at > ?"
            " THEN 1 ELSE 0 END WHERE assignment_id=?", (when, when, a["id"]))
    db.commit()
    return redirect("/assignments")


def act_new_list(req, db):
    f = req["form"]
    gid = f.get("group_id", [None])[0]
    items = parse_list(f.get("items", [""])[0])
    if not gid or not items:
        return redirect("/assignments")
    due = f.get("due", [""])[0]
    due_iso = core.deadline_iso(due, f.get("due_time", [""])[0])
    publish_now = f.get("publish", [""])[0] == "1"
    created = []
    for title in items:
        if already_set(db, int(gid), title, due_iso):
            continue
        created.append(db.execute(
            "INSERT INTO assignments (group_id, title, task_type, due_at, created_at,"
            " published, rubric) VALUES (?,?,?,?,?,?,?)",
            (int(gid), title, f.get("task_type", ["other"])[0], due_iso,
             core.iso(core.now()), 1 if publish_now else 0,
             1 if f.get("rubric", [""])[0] == "1" else 0),
        ).lastrowid)
    db.commit()
    if publish_now and f.get("announce", [""])[0] == "1":
        announce_list(db, int(gid), created)
    return redirect("/assignments")


def announce_list(db, group_id, ids):
    """One message listing the whole set, rather than one ping per item."""
    token = core.load_config().get("telegram_token")
    if not token or not ids:
        return 0
    import bot
    rows = db.execute(
        "SELECT title, due_at FROM assignments WHERE id IN (%s)"
        % ",".join("?" * len(ids)), ids
    ).fetchall()
    due = rows[0]["due_at"][:10] if rows and rows[0]["due_at"] else ""
    sent = 0
    for st in db.execute(
        "SELECT telegram_id, lang FROM students WHERE group_id=? AND active=1"
        " AND telegram_id IS NOT NULL", (group_id,)
    ).fetchall():
        head = bot.t(st["lang"], "homework_list", due=(" (due %s)" % due) if due else "")
        body = "\n".join("%d. %s" % (i + 1, r["title"]) for i, r in enumerate(rows))
        bot.send(token, st["telegram_id"], head + "\n\n" + body)
        sent += 1
    return sent


def act_save_marks(req, db, gid):
    f = req["form"]
    day = (f.get("day2", [""])[0] or f.get("day", [""])[0] or "").strip()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", day):
        return redirect(f"/groups/{gid}?tab=marks")
    for st in db.execute(
        "SELECT id FROM students WHERE group_id=? AND active=1", (gid,)
    ).fetchall():
        values = {}
        for field in core.MARK_FIELDS:
            raw = (f.get(f"{field}_{st['id']}", [""])[0] or "").strip()
            values[field] = int(raw) if raw.isdigit() else None
        note = (f.get(f"note_{st['id']}", [""])[0] or "").strip()[:200] or None
        if any(v is not None for v in values.values()) or note:
            core.save_mark(db, st["id"], day, values, note)
    db.commit()
    return redirect(f"/groups/{gid}?tab=marks&day={day}")


def act_edit_assignment(req, db, aid):
    f = req["form"]
    title = (f.get("title", [""])[0] or "").strip()
    due = (f.get("due", [""])[0] or "").strip()
    row = db.execute("SELECT group_id FROM assignments WHERE id=?", (aid,)).fetchone()
    if title:
        db.execute("UPDATE assignments SET title=? WHERE id=?", (title[:120], aid))
    db.execute("UPDATE assignments SET due_at=? WHERE id=?",
               (core.deadline_iso(due, f.get("due_time", [""])[0]), aid))
    db.commit()
    return redirect(f"/groups/{row['group_id']}?tab=homework" if row else "/assignments")


def act_delete_assignment(req, db, aid):
    """Remove the homework but never the students' work."""
    row = db.execute("SELECT group_id FROM assignments WHERE id=?", (aid,)).fetchone()
    db.execute("UPDATE submissions SET assignment_id=NULL WHERE assignment_id=?", (aid,))
    db.execute("DELETE FROM assignments WHERE id=?", (aid,))
    db.commit()
    return redirect(f"/groups/{row['group_id']}?tab=homework" if row else "/assignments")


def act_open_assignment(req, db, aid):
    row = db.execute("SELECT group_id FROM assignments WHERE id=?", (aid,)).fetchone()
    db.execute("UPDATE assignments SET closed=0 WHERE id=?", (aid,))
    db.commit()
    return redirect(f"/groups/{row['group_id']}?tab=homework" if row else "/assignments")


def act_close_assignment(req, db, aid):
    db.execute("UPDATE assignments SET closed=1 WHERE id=?", (aid,))
    db.commit()
    return redirect("/assignments")


def _back_to_group(db, sid):
    row = db.execute("SELECT group_id FROM students WHERE id=?", (sid,)).fetchone()
    return redirect(f"/groups/{row['group_id']}?tab=students" if row and row["group_id"]
                    else "/roster")


def act_pause_student(req, db, sid):
    where = _back_to_group(db, sid)
    core.set_student_active(db, sid, False)
    return where


def act_resume_student(req, db, sid):
    where = _back_to_group(db, sid)
    core.set_student_active(db, sid, True)
    return where


def act_delete_student(req, db, sid):
    where = _back_to_group(db, sid)
    photos = core.remove_student(db, sid)
    for name in photos:
        path = os.path.join(core.UPLOAD_DIR, name)
        if os.path.exists(path):
            os.remove(path)
    return where


def act_update_student(req, db, sid):
    f = req["form"]
    name = (f.get("name", [""])[0] or "").strip()
    gid = f.get("group_id", [None])[0]
    if name:
        db.execute("UPDATE students SET name=? WHERE id=?", (name, sid))
    if gid:
        db.execute("UPDATE students SET group_id=? WHERE id=?", (int(gid), sid))
    db.commit()
    return redirect(f"/students/{sid}")


# ------------------------------------------------------------------ plumbing

def html_response(body, status=200, extra=None):
    payload = body.encode("utf-8")
    headers = [("Content-Type", "text/html; charset=utf-8"), ("Content-Length", str(len(payload)))]
    headers += extra or []
    return status, headers, payload


def redirect(location, extra=None):
    return 303, [("Location", location), ("Content-Length", "0")] + (extra or []), b""


def not_found():
    return html_response(page("Not found", "<h1>Not found</h1>"), 404)


ROUTES = [
    ("GET", r"^/$", lambda r, db: view_overview(r, db)),
    ("GET", r"^/queue$", view_queue),
    ("GET", r"^/groups$", view_groups),
    ("GET", r"^/groups/(\d+)$", view_group),
    ("GET", r"^/students/(\d+)$", view_student),
    ("GET", r"^/assignments$", view_assignments),
    ("GET", r"^/roster$", view_roster),
    ("GET", r"^/homework$", view_homework),
    ("GET", r"^/ratings$", view_ratings),
    ("GET", r"^/questions$", view_questions),
    ("GET", r"^/export\.csv$", view_export),
    ("GET", r"^/import$", view_import),
    ("GET", r"^/backup\.json$", view_backup),
    ("POST", r"^/questions/(\d+)/answer$", act_answer_question),
    ("GET", r"^/materials$", view_materials),
    ("GET", r"^/materials/(\d+)/file$", view_material_file),
    ("GET",  r"^/music$", view_music),
    ("POST", r"^/music/delete$", act_delete_song),
    ("POST", r"^/materials/(\d+)/delete$", act_delete_material),
    ("GET", r"^/vocab$", view_vocab),
    ("GET", r"^/vocab/(\d+)$", view_word_list),
    ("GET", r"^/skip$", act_skip),
    ("POST", r"^/grade$", act_grade),
    ("POST", r"^/regrade$", act_regrade),
    ("GET",  r"^/regrade/(\d+)$", view_regrade),
    ("POST", r"^/notes/new$", act_new_note),
    ("POST", r"^/notes/delete$", act_delete_note),
    ("POST", r"^/skip$", act_skip),
    ("POST", r"^/groups/new$", act_new_group),
    ("POST", r"^/groups/(\d+)/level$", act_set_group_level),
    ("POST", r"^/groups/(\d+)/repeat$", act_repeat_homework),
    ("GET",  r"^/championship$", view_championship),
    ("POST", r"^/championship/start$", act_start_season),
    ("POST", r"^/championship/close$", act_close_season),
    ("POST", r"^/championship/pause$", act_pause_season),
    ("POST", r"^/championship/resume$", act_resume_season),
    ("GET",  r"^/play$", view_play),
    ("GET",  r"^/play/(\d+)$", view_game_board),
    ("GET",  r"^/play/(\d+)/state\.json$", game_state_json),
    ("GET",  r"^/play/(\d+)/end$", act_game_end),
    ("POST", r"^/play/new$", act_new_game),
    ("POST", r"^/play/(\d+)/next$", act_game_next),
    ("POST", r"^/assignments/list$", act_new_list),
    ("POST", r"^/assignments/batch/close$", act_batch_close),
    ("POST", r"^/assignments/batch/open$", act_batch_open),
    ("POST", r"^/assignments/batch/publish$", act_batch_publish),
    ("POST", r"^/assignments/batch/delete$", act_batch_delete),
    ("POST", r"^/assignments/batch/edit$", act_batch_edit),
    ("POST", r"^/assignments/(\d+)/close$", act_close_assignment),
    ("POST", r"^/assignments/(\d+)/open$", act_open_assignment),
    ("POST", r"^/assignments/(\d+)/edit$", act_edit_assignment),
    ("POST", r"^/assignments/(\d+)/delete$", act_delete_assignment),
    ("POST", r"^/groups/(\d+)/marks$", act_save_marks),
    ("POST", r"^/assignments/(\d+)/publish$", act_publish_assignment),
    ("POST", r"^/assignments/(\d+)/unpublish$", act_unpublish_assignment),
    ("POST", r"^/students/new$", act_new_student),
    ("POST", r"^/students/bulk$", act_bulk_students),
    ("POST", r"^/students/(\d+)/move$", act_move_student),
    ("POST", r"^/students/(\d+)/update$", act_update_student),
    ("POST", r"^/students/(\d+)/pause$", act_pause_student),
    ("POST", r"^/students/(\d+)/resume$", act_resume_student),
    ("POST", r"^/students/(\d+)/delete$", act_delete_student),
    ("POST", r"^/vocab/new$", act_new_word_list),
    ("POST", r"^/vocab/(\d+)/add$", act_add_words),
    ("POST", r"^/vocab/(\d+)/replace$", act_replace_words),
]


class Handler(BaseHTTPRequestHandler):
    server_version = "TA/1.0"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass

    def _session(self):
        cookie = self.headers.get("Cookie", "")
        m = re.search(r"ta_session=([A-Za-z0-9_-]+)", cookie)
        return bool(m and m.group(1) in SESSIONS)

    def _serve_static(self, path):
        name = os.path.basename(path)
        full = os.path.join(core.ROOT, "static", name)
        if not os.path.isfile(full):
            return self._send(*not_found())
        with open(full, "rb") as fh:
            data = fh.read()
        ctype = ("text/css" if name.endswith(".css")
                 else "application/javascript" if name.endswith(".js")
                 else "audio/mpeg" if name.endswith(".mp3")
                 else "application/octet-stream")
        self._send(200, [("Content-Type", ctype), ("Content-Length", str(len(data))),
                         ("Cache-Control", "max-age=300")], data)

    def _serve_media(self, path):
        name = os.path.basename(urllib.parse.unquote(path))
        full = os.path.join(core.UPLOAD_DIR, name)
        if not os.path.isfile(full):
            # old pages are dropped from the disk once they are months past
            # grading, but Telegram keeps them, so fetch it back on demand
            if not restore_photo(name):
                return self._send(*not_found())
        ctype = ("audio/ogg" if name.endswith((".oga", ".ogg"))
                 else "audio/mpeg" if name.endswith(".mp3")
                 else "audio/mp4" if name.endswith((".m4a", ".aac"))
                 else "audio/wav" if name.endswith(".wav")
                 else "image/png" if name.endswith(".png") else "image/jpeg")
        size = os.path.getsize(full)
        start, end, partial = 0, size - 1, False
        m = re.match(r"bytes=(\d*)-(\d*)$", (self.headers.get("Range") or "").strip())
        if m and (m.group(1) or m.group(2)):
            # a recording will not play or seek in Safari without this
            if m.group(1):
                start = int(m.group(1))
                if m.group(2):
                    end = min(int(m.group(2)), size - 1)
            else:
                start = max(0, size - int(m.group(2)))
            if start >= size or start > end:
                return self._send(416, [("Content-Range", "bytes */%d" % size),
                                        ("Content-Length", "0")], b"")
            partial = True
        headers = [("Content-Type", ctype), ("Accept-Ranges", "bytes"),
                   ("Content-Length", str(end - start + 1)),
                   ("Cache-Control", "private, max-age=3600")]
        if partial:
            headers.append(("Content-Range", "bytes %d-%d/%d" % (start, end, size)))
        self._send_file(206 if partial else 200, headers, full, start, end - start + 1)

    def _student_get(self, path, query):
        parts = path.split("/")
        if len(parts) == 4 and parts[3] in ("game", "game.json"):
            db = core.connect()
            try:
                fn = view_student_game if parts[3] == "game" else student_game_json
                return self._send(*fn({"query": query}, db, parts[2]))
            finally:
                db.close()
        if len(parts) != 3 or not parts[2]:
            return self._send(*not_found())
        flash = ""
        if query.get("sent"):
            flash = '<div class="flash">Sent to your teacher.</div>'
        elif "ok" in query:
            n = query["ok"][0]
            rejected = (query.get("r") or ["0"])[0]
            pages = (query.get("p") or [""])[0]
            extra = (f" {rejected} photo(s) were too small to read and were not sent."
                     if rejected not in ("0", "") else "")
            total = (f" That task now has {pages} page(s)."
                     if pages and pages != n else "")
            flash = (f'<div class="flash">Sent {E(n)} page(s) to your teacher.'
                     f'{E(total)}{E(extra)}</div>')
        elif query.get("saved"):
            flash = '<div class="flash">Saved.</div>'
        elif query.get("e") == ["small"]:
            flash = ('<div class="flash err">Those photos are too small or blurry to read. '
                     'Retake them: page flat, camera directly above, good light.</div>')
        elif query.get("e") == ["none"]:
            flash = '<div class="flash err">No photo was attached.</div>'
        db = core.connect()
        try:
            return self._send(*view_student_portal(
                {"query": query}, db, parts[2], flash))
        finally:
            db.close()

    def _remember_site_url(self):
        """Learn the public address from the teacher's own visit, once."""
        host = self.headers.get("Host")
        if not host or host.startswith(("localhost", "127.0.0.1")):
            return
        proto = self.headers.get("X-Forwarded-Proto", "https")
        url = "%s://%s" % (proto, host)
        db = core.connect()
        try:
            if core.meta_get(db, "site_url") != url:
                core.meta_set(db, "site_url", url)
        finally:
            db.close()

    SECURITY_HEADERS = [
        ("X-Content-Type-Options", "nosniff"),
        ("X-Frame-Options", "DENY"),
        ("Referrer-Policy", "same-origin"),
        ("Strict-Transport-Security", "max-age=31536000"),
    ]

    def _send(self, status, headers, body):
        """Write a response, in pieces, tolerating a client that walks away.

        A media element asks for a range, takes what it needs to fill its
        buffer and hangs up mid-transfer. That is normal behaviour, not an
        error: sending the body in one call made every one of those a broken
        pipe, and the browser answered each dead connection by opening another
        - which is what the stuttering was.
        """
        try:
            self.send_response(status)
            for k, v in self.SECURITY_HEADERS:
                self.send_header(k, v)
            for k, v in headers:
                self.send_header(k, v)
            self.end_headers()
            if body and self.command != "HEAD":
                view = memoryview(body)
                for off in range(0, len(view), 64 * 1024):
                    self.wfile.write(view[off:off + 64 * 1024])
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True

    def _send_file(self, status, headers, path, start, length):
        """Stream a file from disk, in pieces, tolerating a client hanging up.

        Memory stays at one buffer no matter how big the track is, so a song
        can be answered whole and the player never has to come back for the
        next piece while it is playing.
        """
        try:
            self.send_response(status)
            for k, v in self.SECURITY_HEADERS:
                self.send_header(k, v)
            for k, v in headers:
                self.send_header(k, v)
            self.end_headers()
            if self.command == "HEAD" or not length:
                return
            with open(path, "rb") as fh:
                fh.seek(start)
                left = length
                while left > 0:
                    chunk = fh.read(min(SONG_READ, left))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    left -= len(chunk)
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True

    def do_HEAD(self):
        # players ask before they fetch; a 501 here reads as a broken file
        self.do_GET()

    def do_GET(self):
        parsed = urllib.parse.urlsplit(self.path)
        path, query = parsed.path, urllib.parse.parse_qs(parsed.query)

        if path.startswith("/static/"):
            return self._serve_static(path)
        m = re.match(r"^/s/([A-Za-z0-9_-]+)/photo$", path)
        if m:
            db = core.connect()
            try:
                st = core.student_by_token(db, m.group(1))
                if not st or not st["photo"]:
                    return self._send(*not_found())
                full = os.path.join(core.UPLOAD_DIR, st["photo"])
                if not os.path.isfile(full):
                    return self._send(*not_found())
                with open(full, "rb") as fh:
                    blob = fh.read()
                ctype = "image/png" if st["photo"].endswith(".png") else "image/jpeg"
                return self._send(200, [("Content-Type", ctype),
                                        ("Content-Length", str(len(blob))),
                                        ("Cache-Control", "private, max-age=300")], blob)
            finally:
                db.close()
        if path.startswith("/s/"):
            return self._student_get(path, query)
        if path.startswith("/p/"):
            parts = path.split("/")
            db = core.connect()
            try:
                return self._send(*view_parent_report(None, db, parts[2] if len(parts) > 2 else ""))
            finally:
                db.close()
        if re.match(r"^/materials/\d+/file$", path):
            db = core.connect()
            try:
                student = None
                if not self._session():
                    token = (query.get("s") or [""])[0]
                    student = core.student_by_token(db, token)
                    if not student:
                        return self._send(*redirect("/login"))
                return self._send(*serve_material(db, int(path.split("/")[2]), student))
            finally:
                db.close()
        m = re.match(r"^/song(?:/(\d{4}-\d{2}-\d{2}))?$", path)
        if m:
            # the whole school shares one track a day, so this is deliberately
            # open: an <audio> element cannot carry a student's token
            db = core.connect()
            try:
                plan = song_range(db, m.group(1), self.headers.get("Range"))
                if not plan:
                    return self._send(*not_found())
                status, headers, path, start, length = plan
                if path is None:                       # 416, no body to stream
                    return self._send(status, headers, b"")
                return self._send_file(status, headers, path, start, length)
            finally:
                db.close()
        if path == "/login":
            return self._send(*view_login(None))
        if path == "/logout":
            return self._send(*redirect("/login", [("Set-Cookie", "ta_session=; Max-Age=0; Path=/")]))
        if not self._session():
            return self._send(*redirect("/login"))
        self._remember_site_url()
        if path.startswith("/media/"):
            return self._serve_media(path)
        return self._dispatch("GET", path, {"query": query, "form": {},
                                            "headers": self.headers})

    def do_POST(self):
        parsed = urllib.parse.urlsplit(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length") or 0)
        if length > uploads.MAX_BYTES:  # covers photo batches and data imports
            return self._send(*html_response(
                student_page("Too large", "<h1>Those photos are too large</h1>"
                             "<p class='sub'>Send fewer pages at a time.</p>"), 413))
        body = self.rfile.read(length) if length else b""

        if path == "/materials/new":
            if not self._session():
                return self._send(*redirect("/login"))
            fields, files = uploads.parse_multipart(
                body, self.headers.get("Content-Type", ""))
            db = core.connect()
            try:
                return self._send(*act_new_material(
                    {"query": {}, "form": {}, "files": (fields, files)}, db))
            finally:
                db.close()

        if path == "/music/new":
            if not self._session():
                return self._send(*redirect("/login"))
            fields, files = uploads.parse_multipart(
                body, self.headers.get("Content-Type", ""))
            db = core.connect()
            try:
                return self._send(*act_new_song(
                    {"query": {}, "form": {}, "files": (fields, files)}, db))
            finally:
                db.close()

        if path == "/import":
            if not self._session():
                return self._send(*redirect("/login"))
            fields, files = uploads.parse_multipart(
                body, self.headers.get("Content-Type", ""))
            db = core.connect()
            try:
                return self._send(*act_import(
                    {"query": {}, "form": {}, "files": (fields, files)}, db))
            finally:
                db.close()

        if re.match(r"^/s/[A-Za-z0-9_-]+/goal$", path):
            fields, files = uploads.parse_multipart(
                body, self.headers.get("Content-Type", ""))
            db = core.connect()
            try:
                return self._send(*act_student_goal(
                    {"query": {}, "form": {}, "files": (fields, files)},
                    db, path.split("/")[2]))
            finally:
                db.close()

        m = re.match(r"^/s/([A-Za-z0-9_-]+)/(finish|discard)/(\d+)$", path)
        if m:
            db = core.connect()
            try:
                fn = act_student_finish if m.group(2) == "finish" else act_student_discard
                return self._send(*fn({"query": {}, "form": {}}, db,
                                      m.group(1), int(m.group(3))))
            finally:
                db.close()

        if path.startswith("/s/") and path.endswith("/game/avatar"):
            token = path.split("/")[2]
            form = urllib.parse.parse_qs(body.decode("utf-8", "replace"),
                                         keep_blank_values=True)
            db = core.connect()
            try:
                return self._send(*act_student_avatar(
                    {"query": {}, "form": form}, db, token))
            finally:
                db.close()

        if path.startswith("/s/") and path.endswith("/game/answer"):
            token = path.split("/")[2]
            form = urllib.parse.parse_qs(body.decode("utf-8", "replace"),
                                         keep_blank_values=True)
            db = core.connect()
            try:
                return self._send(*act_student_answer(
                    {"query": {}, "form": form}, db, token))
            finally:
                db.close()

        if path.startswith("/s/") and path.endswith("/profile"):
            token = path.split("/")[2]
            fields, files = uploads.parse_multipart(
                body, self.headers.get("Content-Type", ""))
            db = core.connect()
            try:
                return self._send(*act_student_profile(
                    {"query": {}, "form": {}, "files": (fields, files)}, db, token))
            finally:
                db.close()

        if path.startswith("/s/") and path.endswith("/upload"):
            token = path.split("/")[2]
            fields, files = uploads.parse_multipart(
                body, self.headers.get("Content-Type", ""))
            db = core.connect()
            try:
                return self._send(*act_student_upload(
                    {"query": {}, "form": {}, "files": (fields, files)}, db, token))
            finally:
                db.close()

        raw = body.decode("utf-8", "replace")
        form = urllib.parse.parse_qs(raw, keep_blank_values=True)

        if path == "/login":
            client = self.headers.get("X-Forwarded-For", self.client_address[0]).split(",")[0]
            if login_blocked(client):
                return self._send(*view_login(None, err="Too many attempts. "
                                              "Wait 15 minutes."))
            # read the file fresh, so changing the password only needs a save
            expected = core.load_config()["teacher_password"]
            if secrets.compare_digest(form.get("password", [""])[0], expected):
                LOGIN_ATTEMPTS.pop(client, None)
                token = secrets.token_urlsafe(24)
                SESSIONS[token] = True
                return self._send(
                    *redirect("/", [("Set-Cookie",
                                     f"ta_session={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=2592000")])
                )
            login_failed(client)
            time.sleep(1.0)          # make guessing slow as well as limited
            return self._send(*view_login(None, err=True))
        if not self._session():
            return self._send(*redirect("/login"))
        return self._dispatch("POST", path, {"query": {}, "form": form})

    def _dispatch(self, method, path, req):
        for m, pattern, fn in ROUTES:
            if m != method:
                continue
            match = re.match(pattern, path)
            if match:
                db = core.connect()
                try:
                    args = [int(g) for g in match.groups()]
                    return self._send(*fn(req, db, *args))
                except Exception as exc:
                    import traceback
                    traceback.print_exc()
                    return self._send(*html_response(
                        page("Error", "<h1>Something broke</h1><div class='card'>"
                             "<p style='margin:0'>The details are in the server log."
                             "</p></div><p><a href='/'>Back to overview</a></p>"), 500))
                finally:
                    db.close()
        return self._send(*not_found())


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main():
    core.init_db()
    if CFG["teacher_password"] == "changeme":
        print("!! Set a real teacher_password in config.json before sharing this URL.")
    port = CFG["port"]
    print(f"Dashboard: http://localhost:{port}")
    Server(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
