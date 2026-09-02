"""Teacher dashboard: grading queue, groups, students, progress charts.

Runs on the Python standard library alone: python3 server.py
"""
import html
import json
import os
import re
import secrets
import urllib.parse
from datetime import timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import charts
import core
import uploads

CFG = core.load_config()
SESSIONS = {}
E = html.escape


# ------------------------------------------------------------------ layout

def page(title, body, active=""):
    def nav(href, label):
        cls = ' class="on"' if active == label else ""
        return f'<a href="{href}"{cls}>{label}</a>'

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{E(title)} · AzamatEnglish</title>
<link rel="stylesheet" href="/static/style.css"></head><body>
<header class="top">
<span class="brand"><span class="mark">A</span>AzamatEnglish</span>
<nav>{nav('/', 'Overview')}{nav('/queue', 'Grade')}{nav('/homework', 'Homework')}
{nav('/ratings', 'Ratings')}{nav('/assignments', 'Assignments')}{nav('/groups', 'Groups')}
{nav('/roster', 'Students')}{nav('/materials', 'Materials')}{nav('/vocab', 'Vocabulary')}{nav('/questions', 'Questions')}</nav>
<span class="right"><a href="/logout">Sign out</a></span></header>
<main>{body}</main></body></html>"""


def stat(k, v, sub=""):
    s = f" <small>{E(sub)}</small>" if sub else ""
    return f'<div class="stat"><div class="k">{E(k)}</div><div class="v">{v}{s}</div></div>'


def fmt(v, dash="—"):
    return dash if v is None else v


def score_pill(s):
    if s is None:
        return '<span class="pill mute">—</span>'
    cls = "risk" if s < 5 else ""
    return f'<span class="pill {cls}">{s:g}/10</span>'


# ------------------------------------------------------------------- pages

def view_login(req, err=""):
    msg = '<div class="flash err">Wrong password</div>' if err else ""
    body = f"""<div class="login card"><h1>Sign in</h1>
<p class="sub">Teacher access only.</p>{msg}
<form method="post" action="/login" class="inline">
<label class="f">Password<input type="password" name="password" autofocus></label>
<button>Enter</button></form></div>"""
    # deliberately not the teacher layout: a signed-out visitor sees no navigation
    return html_response(student_page("Sign in", body))


def view_overview(req, db):
    pending = db.execute(
        "SELECT COUNT(*) c FROM submissions WHERE status='pending'"
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

    action = (
        f'<div class="card"><strong>{pending}</strong> submission(s) waiting. '
        f'<a href="/queue">Start grading →</a></div>'
        if pending
        else ""
    )
    body = f"""<h1>Overview</h1><p class="sub">Where every group and student stands right now.</p>
{action}{cards}<h2>Needs attention</h2>{risk_html}"""
    return html_response(page("Overview", body, "Overview"))


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


def view_queue(req, db):
    sub = db.execute(
        "SELECT * FROM submissions WHERE status='pending' ORDER BY created_at LIMIT 1"
    ).fetchone()
    remaining = db.execute(
        "SELECT COUNT(*) c FROM submissions WHERE status='pending'"
    ).fetchone()["c"]
    if not sub:
        body = """<h1>Grading queue</h1>
<div class="card"><p style="margin:0">Queue is empty. Nothing to grade.</p></div>"""
        return html_response(page("Grade", body, "Grade"))

    student = db.execute("SELECT * FROM students WHERE id=?", (sub["student_id"],)).fetchone()
    assignment = (
        db.execute("SELECT * FROM assignments WHERE id=?", (sub["assignment_id"],)).fetchone()
        if sub["assignment_id"]
        else None
    )
    files = db.execute(
        "SELECT * FROM files WHERE submission_id=? ORDER BY ord, id", (sub["id"],)
    ).fetchall()
    st = core.student_stats(db, student["id"])
    tags = db.execute("SELECT * FROM tags ORDER BY sort, id").fetchall()

    shots = "".join(
        f'<img src="/media/{E(f["filename"])}" alt="page {i+1}" onclick="this.classList.toggle(\'zoom\')">'
        for i, f in enumerate(files)
    ) or '<p class="sub">No image attached.</p>'

    pad = "".join(
        f'<button type="button" data-score="{n}" onclick="pick({n})">{n}</button>'
        for n in list(range(1, 11))
    )
    tagboxes = "".join(
        f'<label><input type="checkbox" name="tag" value="{t["id"]}"><span>{E(t["label"])}</span></label>'
        for t in tags
    )

    prev = (
        f'Average {fmt(st["average"])} · last 3 {fmt(st["last3"])} · '
        f'{st["graded_count"]} graded · {st["missed"]} missed'
    )
    body = f"""<h1>Grading queue</h1>
<p class="sub">{remaining} waiting · keys <span class="kbd">1</span>–<span class="kbd">9</span>
<span class="kbd">0</span>=10 to score, <span class="kbd">Enter</span> to save, <span class="kbd">s</span> to skip.</p>
<div class="queue">
  <div class="shots">{shots}</div>
  <div>
    <div class="card">
      <div style="font-weight:600">{E(student["name"])}</div>
      <div class="sub" style="margin:2px 0 0">{E(group_name(db, student["group_id"]))} ·
        {E(assignment["title"]) if assignment else "unassigned"}
        {'<span class="pill risk">late</span>' if sub["late"] else ''}
        {'<span class="pill mute">speaking</span>' if sub["kind"] == "voice" else ''}
        {'<span class="pill mute">resubmission</span>' if sub["improves"] else ''}</div>
      <div class="sub" style="margin:6px 0 0">{E(prev)}</div>
    </div>
    <form method="post" action="/grade" id="gform" class="card">
      <input type="hidden" name="submission_id" value="{sub['id']}">
      <input type="hidden" name="score" id="score">
      <div class="scorepad">{pad}</div>
      <div class="tags">{tagboxes}</div>
      <label class="f">Note (optional)
        <textarea name="note" rows="2" placeholder="One line the student will read"></textarea></label>
      <div style="display:flex;gap:8px;margin-top:10px">
        <button id="save" disabled>Save &amp; next</button>
        <button class="ghost" formaction="/skip" name="skip" value="1">Skip</button>
      </div>
    </form>
  </div>
</div>
<script>
function pick(n) {{
  document.getElementById('score').value = n;
  document.querySelectorAll('.scorepad button').forEach(b =>
    b.classList.toggle('sel', b.dataset.score == n));
  document.getElementById('save').disabled = false;
}}
document.addEventListener('keydown', e => {{
  if (e.target.tagName === 'TEXTAREA' && e.key !== 'Enter') return;
  if (e.key >= '1' && e.key <= '9') {{ pick(+e.key); e.preventDefault(); }}
  else if (e.key === '0') {{ pick(10); e.preventDefault(); }}
  else if (e.key === 'Enter') {{
    if (document.getElementById('score').value) {{
      e.preventDefault(); document.getElementById('gform').submit();
    }}
  }} else if (e.key === 's' && e.target.tagName !== 'TEXTAREA') {{
    location.href = '/skip?submission_id={sub["id"]}';
  }}
}});
</script>"""
    return html_response(page("Grade", body, "Grade"))


def view_groups(req, db):
    groups = db.execute("SELECT * FROM groups WHERE archived=0 ORDER BY name").fetchall()
    bot_user = core.meta_get(db, "bot_username", "")
    levels = db.execute("SELECT * FROM levels ORDER BY sort").fetchall()
    level_opts = ('<option value="">— no level —</option>'
                  + "".join(f'<option value="{l["id"]}">{E(l["name"])}</option>'
                            for l in levels))
    rows = ""
    for g in groups:
        members = db.execute(
            "SELECT COUNT(*) c FROM students WHERE group_id=? AND active=1", (g["id"],)
        ).fetchone()["c"]
        avgs = [
            core.student_stats(db, s["id"])["average"]
            for s in db.execute(
                "SELECT id FROM students WHERE group_id=? AND active=1", (g["id"],)
            ).fetchall()
        ]
        avgs = [a for a in avgs if a is not None]
        gavg = round(sum(avgs) / len(avgs), 2) if avgs else None
        if bot_user:
            link = f"https://t.me/{bot_user}?start={g['join_code']}"
            share = (f'<input readonly value="{E(link)}" onclick="this.select()" '
                     f'style="width:100%;font-size:12px;'
                     f'font-family:ui-monospace,Menlo,monospace">')
        else:
            share = '<span class="sub">—</span>'
        picker = "".join(
            f'<option value="{l["id"]}"{" selected" if l["id"]==g["level_id"] else ""}>'
            f'{E(l["name"])}</option>' for l in levels)
        lvl = (f'<form method="post" action="/groups/{g["id"]}/level">'
               f'<select name="level_id" onchange="this.form.submit()">'
               f'<option value="">— none —</option>{picker}</select></form>')
        rows += (
            f'<tr><td><a href="/groups/{g["id"]}">{E(g["name"])}</a></td>'
            f'<td>{lvl}</td>'
            f'<td><span class="kbd">{E(g["join_code"])}</span></td>'
            f"<td>{members}</td><td>{score_pill(gavg)}</td><td>{share}</td></tr>"
        )
    if bot_user:
        invite = ('<p class="sub">Send a group\'s invite link to its students. One tap '
                  'opens your bot and joins them - they never type a code.</p>')
    else:
        invite = ('<p class="sub">Students join with a group code. Once the bot has run '
                  'once with a token, ready-made invite links appear here.</p>')
    body = f"""<h1>Groups</h1>
{invite}
<div class="card"><form method="post" action="/groups/new" class="inline">
<label class="f">New group name<input name="name" placeholder="114" required></label>
<label class="f">Level<select name="level_id">{level_opts}</select></label>
<button>Create</button></form></div>
<div class="tablewrap"><table><tr><th>Group</th><th>Level</th><th>Join code</th>
<th>Students</th><th>Average</th><th>Invite link</th></tr>
{rows or '<tr><td colspan=6 class="sub">No groups yet.</td></tr>'}</table></div>"""
    return html_response(page("Groups", body, "Groups"))


def view_group(req, db, gid):
    g = db.execute("SELECT * FROM groups WHERE id=?", (gid,)).fetchone()
    if not g:
        return not_found()
    students = db.execute(
        "SELECT * FROM students WHERE group_id=? AND active=1 ORDER BY name", (gid,)
    ).fetchall()
    assignments = db.execute(
        "SELECT * FROM assignments WHERE group_id=? ORDER BY COALESCE(due_at,created_at), id",
        (gid,),
    ).fetchall()

    # group average per assignment, used both for its own chart and as the
    # reference band behind each student's line
    band, dist_html = [], ""
    for a in assignments:
        scores = [
            r["score"]
            for r in db.execute(
                "SELECT score FROM submissions WHERE assignment_id=? AND status='graded'",
                (a["id"],),
            ).fetchall()
        ]
        band.append(round(sum(scores) / len(scores), 2) if scores else None)
    timeline = [
        {"title": a["title"], "score": band[i], "status": "graded" if band[i] else "missing"}
        for i, a in enumerate(assignments)
    ]

    # show the spread for the most recent assignment that actually has grades -
    # the newest one is usually still sitting in the queue
    for a in reversed(assignments):
        scores = [
            r["score"]
            for r in db.execute(
                "SELECT score FROM submissions WHERE assignment_id=? AND status='graded'",
                (a["id"],),
            ).fetchall()
        ]
        if scores:
            dist_html = (
                f'<h2>Spread on “{E(a["title"])}”</h2>'
                f'<div class="card">{charts.distribution(scores)}</div>'
            )
            break

    rows = ""
    for s in students:
        st = core.student_stats(db, s["id"])
        spark = charts.sparkline([t["score"] for t in st["timeline"] if t["score"] is not None])
        flag = '<span class="pill risk">at risk</span>' if st["at_risk"] else ""
        comp = f'{st["completion"]}%' if st["completion"] is not None else "—"
        rows += (
            f'<tr><td><a href="/students/{s["id"]}">{E(s["name"])}</a> {flag}</td>'
            f'<td>{score_pill(st["average"])}</td><td>{score_pill(st["last3"])}</td>'
            f"<td>{comp}</td><td>{spark}</td></tr>"
        )

    body = f"""<h1>{E(g["name"])}</h1>
<p class="sub">Join code <span class="kbd">{E(g["join_code"])}</span> ·
{len(students)} students · {len(assignments)} assignments</p>
<h2>Group average over time</h2>
<div class="card">{charts.score_line(timeline)}</div>
{dist_html}
<h2>Students</h2>
<div class="tablewrap"><table><tr><th>Student</th><th>Average</th><th>Last 3</th>
<th>Completion</th><th>Trend</th></tr>
{rows or '<tr><td colspan=5 class="sub">Nobody has joined yet.</td></tr>'}</table></div>"""
    return html_response(page(g["name"], body, "Groups"))


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


def view_assignments(req, db):
    groups = db.execute("SELECT * FROM groups WHERE archived=0 ORDER BY name").fetchall()
    rows = ""
    for a in db.execute(
        "SELECT * FROM assignments ORDER BY closed, COALESCE(due_at, created_at) DESC, id DESC"
    ).fetchall():
        got = db.execute(
            "SELECT COUNT(*) c FROM submissions WHERE assignment_id=?", (a["id"],)
        ).fetchone()["c"]
        total = db.execute(
            "SELECT COUNT(*) c FROM students WHERE group_id=? AND active=1", (a["group_id"],)
        ).fetchone()["c"]
        if a["closed"]:
            state = '<span class="pill mute">closed</span>'
            close = ""
        elif not a["published"]:
            state = '<span class="pill mute">draft</span>'
            close = (
                f'<form method="post" action="/assignments/{a["id"]}/publish" class="inline">'
                f'<label style="font-size:12px;color:var(--muted)">'
                f'<input type="checkbox" name="announce" value="1" checked> tell students</label>'
                f'<button>Publish</button></form>'
            )
        else:
            state = '<span class="pill">open</span>'
            close = (
                f'<form method="post" action="/assignments/{a["id"]}/close" '
                f'style="display:inline"><button class="ghost">Close</button></form> '
                f'<form method="post" action="/assignments/{a["id"]}/unpublish" '
                f'style="display:inline"><button class="ghost">Hide</button></form>'
            )
        rows += (
            f'<tr><td>{E(a["title"])}</td><td>{E(group_name(db, a["group_id"]))}</td>'
            f'<td>{E(a["task_type"])}</td><td>{E((a["due_at"] or "—")[:10])}</td>'
            f"<td>{got}/{total}</td><td>{state}</td><td>{close}</td></tr>"
        )
    opts = "".join(f'<option value="{g["id"]}">{E(g["name"])}</option>' for g in groups)
    body = f"""<h1>Assignments</h1>
<p class="sub">Open assignments are what the bot offers students when they send a photo.</p>
<div class="card"><form method="post" action="/assignments/new" class="inline">
<label class="f">Title<input name="title" placeholder="Task 2 – Technology essay" required></label>
<label class="f">Group<select name="group_id">{opts}</select></label>
<label class="f">Type<select name="task_type">
<option value="task2">Task 2</option><option value="task1">Task 1</option>
<option value="other">Other</option></select></label>
<label class="f">Due<input type="date" name="due"></label>
<label class="f" style="justify-content:flex-end">&nbsp;
<span style="font-size:13px;color:var(--ink)">
<input type="checkbox" name="publish" value="1"> open to students now</span></label>
<label class="f" style="justify-content:flex-end">&nbsp;
<span style="font-size:13px;color:var(--ink)">
<input type="checkbox" name="announce" value="1" checked> and tell them in Telegram</span></label>
<button>Create</button></form>
<p class="sub" style="margin:10px 0 0">Without the tick it is saved as a draft: students
cannot see it or submit to it until you press Publish.</p></div>
<h2>Post a homework list</h2>
<div class="card"><form method="post" action="/assignments/list">
<div class="inline" style="margin-bottom:10px">
<label class="f">Group<select name="group_id">{opts}</select></label>
<label class="f">Due<input type="date" name="due"></label>
<label class="f" style="justify-content:flex-end">&nbsp;
<span style="font-size:13px;color:var(--ink)">
<input type="checkbox" name="publish" value="1" checked> open to students now</span></label>
<label class="f" style="justify-content:flex-end">&nbsp;
<span style="font-size:13px;color:var(--ink)">
<input type="checkbox" name="announce" value="1" checked> send them the list</span></label>
</div>
<label class="f">One item per line — numbering is optional
<textarea name="items" rows="6" style="width:100%"
placeholder="1. Task 2 essay – Technology&#10;2. Grammar handout page 45&#10;3. Vocabulary unit 4 – write 10 sentences"></textarea></label>
<div style="margin-top:10px"><button onclick="this.disabled=true;this.form.submit()">
Post list</button></div></form>
<p class="sub" style="margin:10px 0 0">Each line becomes its own item, so students pick
which one they are sending and you get a separate score for each.</p></div>
<h2>All assignments</h2>
<div class="tablewrap"><table><tr><th>Title</th><th>Group</th><th>Type</th><th>Due</th>
<th>Received</th><th></th><th></th></tr>
{rows or '<tr><td colspan=7 class="sub">No assignments yet.</td></tr>'}</table></div>"""
    return html_response(page("Assignments", body, "Assignments"))


def view_roster(req, db):
    rows = ""
    for s in db.execute("SELECT * FROM students ORDER BY active DESC, name").fetchall():
        st = core.student_stats(db, s["id"])
        rows += (
            f'<tr><td><a href="/students/{s["id"]}">{E(s["name"])}</a></td>'
            f'<td>{E(group_name(db, s["group_id"]))}</td>'
            f'<td>{score_pill(st["average"])}</td>'
            f'<td>{st["graded_count"]}</td><td>{st["missed"]}</td>'
            f'<td>{"active" if s["active"] else "inactive"}</td></tr>'
        )
    body = f"""<h1>Students</h1><p class="sub">Everyone who has joined through the bot.</p>
<div class="tablewrap"><table><tr><th>Name</th><th>Group</th><th>Average</th>
<th>Graded</th><th>Missed</th><th>Status</th></tr>
{rows or '<tr><td colspan=6 class="sub">Nobody yet. Share a group join code.</td></tr>'}</table></div>"""
    return html_response(page("Students", body, "Students"))



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


def act_add_words(req, db, wid):
    pairs = parse_words(req["form"].get("words", [""])[0])
    start = db.execute("SELECT COUNT(*) c FROM words WHERE list_id=?", (wid,)).fetchone()["c"]
    for i, (term, meaning, example) in enumerate(pairs):
        db.execute("INSERT INTO words (list_id, term, translation, example, ord)"
                   " VALUES (?,?,?,?,?)", (wid, term, meaning, example, start + i))
    db.commit()
    return redirect(f"/vocab/{wid}")



# ------------------------------------------------------- student-facing page

def student_page(title, body):
    """Standalone layout - no teacher navigation, no sign-in."""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{E(title)} · AzamatEnglish</title>
<link rel="stylesheet" href="/static/style.css"></head>
<body><header class="top"><span class="brand"><span class="mark">A</span>AzamatEnglish</span></header>
<main style="max-width:600px">{body}</main></body></html>"""


def view_student_portal(req, db, token, flash=""):
    s = core.student_by_token(db, token)
    if not s:
        return html_response(student_page("Not found",
            "<h1>Link not recognised</h1><p class='sub'>Ask your teacher for your link.</p>"), 404)
    st = core.student_stats(db, s["id"])
    opens = db.execute(
        "SELECT * FROM assignments WHERE group_id=? AND closed=0"
        " ORDER BY COALESCE(due_at, created_at) DESC, id DESC",
        (s["group_id"],),
    ).fetchall()

    if opens:
        opts = "".join(f'<option value="{a["id"]}">{E(a["title"])}</option>' for a in opens)
        picker = (f'<label class="f">Assignment<select name="assignment_id">{opts}</select></label>'
                  if len(opens) > 1 else
                  f'<input type="hidden" name="assignment_id" value="{opens[0]["id"]}">'
                  f'<p class="sub" style="margin:0 0 10px">For: <strong>{E(opens[0]["title"])}</strong></p>')
    else:
        picker = '<p class="sub" style="margin:0 0 10px">No open assignment right now.</p>'

    hist = ""
    for t in reversed(st["timeline"][-8:]):
        if t["score"] is not None:
            state = score_pill(t["score"])
        elif t["submission_id"]:
            state = '<span class="pill mute">waiting</span>'
        else:
            state = '<span class="pill risk">not submitted</span>'
        hist += f'<tr><td>{E(t["title"])}</td><td>{state}</td></tr>'

    materials_html = ""
    for cat in core.CATEGORIES:
        mats = core.materials_for(db, s["group_id"], cat)
        if not mats:
            continue
        items = "".join(
            f'<tr><td><a href="/materials/{m["id"]}/file">{E(m["title"])}</a></td>'
            f'<td class="sub">{E(core.human_size(m["size"]))}</td></tr>' for m in mats[:25])
        materials_html += (f'<h2>{E(cat)}</h2><div class="tablewrap">'
                           f'<table>{items}</table></div>')
    if materials_html:
        materials_html = "<h2>Materials</h2>" + materials_html
    avg = fmt(st["average"])
    comp = f'{st["completion"]}%' if st["completion"] is not None else "—"
    body = f"""<h1>{E(s["name"])}</h1>
<p class="sub">{E(group_name(db, s["group_id"]))}</p>
{flash}
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
<div class="grid">{stat("Average", avg, "/10")}{stat("Last 3", fmt(st["last3"]), "/10")}
{stat("Completion", comp)}</div>
<h2>Your progress</h2>
<div class="card">{charts.score_line(st["timeline"])}</div>
{materials_html}
<h2>Recent work</h2>
<div class="card" style="padding:0"><table>{hist or
  '<tr><td class="sub" style="padding:14px">Nothing yet.</td></tr>'}</table></div>
<p class="sub">Keep this link private — it is yours.</p>"""
    return html_response(student_page(s["name"], body))


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

    sub_id = db.execute(
        "INSERT INTO submissions (student_id, assignment_id, created_at) VALUES (?,?,?)",
        (s["id"], aid, core.iso(core.now())),
    ).lastrowid
    for i, (data, w, h, kind) in enumerate(accepted):
        name = f"{sub_id}_{i}_{int(core.now().timestamp())}.{'png' if kind == 'png' else 'jpg'}"
        with open(os.path.join(core.UPLOAD_DIR, name), "wb") as fh:
            fh.write(data)
        db.execute(
            "INSERT INTO files (submission_id, filename, width, height, ord)"
            " VALUES (?,?,?,?,?)",
            (sub_id, name, w, h, i),
        )
    db.commit()
    return redirect(f"/s/{token}?ok={len(accepted)}&r={rejected}")


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



def view_ratings(req, db):
    """Live standings: completion first, then average score."""
    gid = req["query"].get("group", [None])[0]
    gid = int(gid) if gid and gid.isdigit() else None
    groups = db.execute("SELECT * FROM groups WHERE archived=0 ORDER BY name").fetchall()
    def tab(href, label, on):
        return f'<a class="tab{" on" if on else ""}" href="{href}">{E(label)}</a>'
    tabs = ('<div class="tabs">' + tab("/ratings", "All groups", gid is None)
            + "".join(tab(f'/ratings?group={g["id"]}', g["name"], gid == g["id"])
                      for g in groups) + "</div>")
    rows = core.rating_rows(db, gid)
    medals = {1: "&#129351;", 2: "&#129352;", 3: "&#129353;"}
    body_rows = ""
    for r in rows:
        st = r["student"]
        comp = r["completion"] if r["completion"] is not None else 0
        bar = (f'<div style="background:var(--line);border-radius:4px;height:8px;width:90px">'
               f'<div style="background:{"var(--warn)" if comp < 50 else "var(--accent)"};'
               f'height:8px;border-radius:4px;width:{comp}%"></div></div>')
        streak = f'&#128293; {r["streak"]}' if r["streak"] >= 2 else ""
        body_rows += (
            f'<tr><td>{medals.get(r["rank"], str(r["rank"]) + ".")}</td>'
            f'<td><a href="/students/{st["id"]}">{E(st["name"])}</a></td>'
            f'<td>{E(group_name(db, st["group_id"]))}</td>'
            f'<td>{bar}</td><td>{comp}%</td>'
            f'<td>{score_pill(r["average"])}</td><td>{r["graded"]}</td>'
            f'<td>{r["missed"]}</td><td>{streak}</td><td>{r["vocab"]}</td></tr>'
        )
    dl = f'/export.csv?group={gid}' if gid else '/export.csv'
    body = f"""<h1>Ratings</h1>
<p class="sub">Ranked by homework completed first, then average score — effort is the
part a student controls.</p>
{tabs}
<div class="tablewrap"><table><tr><th>#</th><th>Student</th><th>Group</th>
<th>Completion</th><th></th><th>Average</th><th>Graded</th><th>Missed</th>
<th>Streak</th><th>Words</th></tr>
{body_rows or '<tr><td colspan=10 class="sub">Nobody has joined yet.</td></tr>'}</table></div>
<p><a href="{dl}">Download as CSV</a> — opens in Excel.</p>"""
    return html_response(page("Ratings", body, "Ratings"))


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


def view_export(req, db):
    gid = req["query"].get("group", [None])[0]
    gid = int(gid) if gid and gid.isdigit() else None
    out = ["rank,name,group,completion_percent,average_score,graded,missed,streak,words_known"]
    for r in core.rating_rows(db, gid):
        st = r["student"]
        name = '"%s"' % st["name"].replace('"', "'")
        out.append(",".join(str(x) for x in [
            r["rank"], name, '"%s"' % group_name(db, st["group_id"]),
            r["completion"] if r["completion"] is not None else "",
            r["average"] if r["average"] is not None else "",
            r["graded"], r["missed"], r["streak"], r["vocab"],
        ]))
    payload = "\n".join(out).encode("utf-8-sig")   # BOM so Excel reads it correctly
    return 200, [("Content-Type", "text/csv; charset=utf-8"),
                 ("Content-Disposition", 'attachment; filename="ratings.csv"'),
                 ("Content-Length", str(len(payload)))], payload


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

    blocks = ""
    for cat in core.CATEGORIES:
        sql = "SELECT * FROM materials WHERE active=1 AND category=?"
        args = [cat]
        if only:
            sql += " AND level_id=?"
            args.append(only)
        mats = db.execute(sql + " ORDER BY created_at DESC", args).fetchall()
        if not mats:
            continue
        rows = ""
        for m in mats:
            scope = core.level_name(db, m["level_id"]) or "All levels"
            if m["group_id"]:
                scope += " · " + group_name(db, m["group_id"])
            note = (f'<div class="sub" style="margin:2px 0 0">{E(m["note"])}</div>'
                    if m["note"] else "")
            rows += (
                f'<tr><td><a href="/materials/{m["id"]}/file">{E(m["title"])}</a>{note}</td>'
                f'<td>{E(scope)}</td><td class="sub">{E(m["original_name"] or "")}</td>'
                f'<td>{E(core.human_size(m["size"]))}</td>'
                f'<td><form method="post" action="/materials/{m["id"]}/delete">'
                f'<button class="ghost">Remove</button></form></td></tr>')
        blocks += (f"<h2>{E(cat)}</h2><div class=\"tablewrap\"><table>"
                   f"<tr><th>Title</th><th>Level</th><th>File</th><th>Size</th><th></th></tr>"
                   f"{rows}</table></div>")
    if not blocks:
        blocks = ('<div class="card"><p style="margin:0">Nothing uploaded yet for '
                  'this level.</p></div>')

    lopts = ('<option value="">All levels</option>'
             + "".join(f'<option value="{l["id"]}">{E(l["name"])}</option>' for l in levels))
    copts = "".join(f'<option value="{E(c)}">{E(c)}</option>' for c in core.CATEGORIES)
    gopts = ('<option value="">Every class at that level</option>'
             + "".join(f'<option value="{g["id"]}">{E(g["name"])}</option>' for g in groups))
    body = f"""<h1>Materials</h1>
<p class="sub">Books, handouts and audio, filed by level and section. Students see the
shelves for their own level under <strong>Materials</strong> in the bot.</p>
<div class="card"><form method="post" action="/materials/new" enctype="multipart/form-data">
<div class="inline" style="margin-bottom:12px">
<label class="f">Title<input name="title" placeholder="Unit 15 - reading passage" required></label>
<label class="f">Level<select name="level_id">{lopts}</select></label>
<label class="f">Section<select name="category">{copts}</select></label>
<label class="f">Class<select name="group_id">{gopts}</select></label>
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
{tabs}
{blocks}"""
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
    category = (fields.get("category", [""])[0] or "").strip()
    if category not in core.CATEGORIES:
        category = core.CATEGORIES[0]
    db.execute(
        "INSERT INTO materials (group_id, title, note, filename, original_name, mime,"
        " size, created_at, level_id, category) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (int(gid) if gid.isdigit() else None, title[:120],
         (fields.get("note", [""])[0] or "").strip()[:300] or None,
         name, original[:150], uploads.content_type(original), len(blob),
         core.iso(core.now()), int(lid) if lid.isdigit() else None, category),
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


def serve_material(db, mid):
    row = db.execute("SELECT * FROM materials WHERE id=? AND active=1", (mid,)).fetchone()
    if not row:
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


def view_material_file(req, db, mid):
    return serve_material(db, mid)


# ----------------------------------------------------------------- actions

def act_grade(req, db):
    f = req["form"]
    sid = int(f.get("submission_id", [0])[0])
    score = f.get("score", [""])[0]
    if not score:
        return redirect("/queue")
    db.execute(
        "UPDATE submissions SET status='graded', score=?, note=?, graded_at=? WHERE id=?",
        (float(score), (f.get("note", [""])[0] or "").strip() or None, core.iso(core.now()), sid),
    )
    db.execute("DELETE FROM submission_tags WHERE submission_id=?", (sid,))
    for t in f.get("tag", []):
        if not t.strip().isdigit():
            continue
        db.execute(
            "INSERT OR IGNORE INTO submission_tags (submission_id, tag_id) VALUES (?,?)",
            (sid, int(t)),
        )
    db.commit()
    notify_graded(db, sid)
    return redirect("/queue")


def notify_graded(db, sid):
    """Tell the student their score, if a bot token is configured."""
    token = CFG.get("telegram_token")
    if not token:
        return
    row = db.execute(
        "SELECT s.score, s.note, st.telegram_id, st.lang, a.title FROM submissions s"
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
                   tags, row["note"], sid)


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


def act_new_assignment(req, db):
    f = req["form"]
    title = (f.get("title", [""])[0] or "").strip()
    gid = f.get("group_id", [None])[0]
    if not title or not gid:
        return redirect("/assignments")
    due = f.get("due", [""])[0]
    due_iso = f"{due}T23:59:00+00:00" if due else None
    publish_now = f.get("publish", [""])[0] == "1"
    if already_set(db, int(gid), title, due_iso):
        return redirect("/assignments")
    aid = db.execute(
        "INSERT INTO assignments (group_id, title, task_type, due_at, created_at, published)"
        " VALUES (?,?,?,?,?,?)",
        (int(gid), title, f.get("task_type", ["task2"])[0], due_iso,
         core.iso(core.now()), 1 if publish_now else 0),
    ).lastrowid
    db.commit()
    if publish_now and f.get("announce", [""])[0] == "1":
        announce(db, aid)
    return redirect("/assignments")


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


def act_new_list(req, db):
    f = req["form"]
    gid = f.get("group_id", [None])[0]
    items = parse_list(f.get("items", [""])[0])
    if not gid or not items:
        return redirect("/assignments")
    due = f.get("due", [""])[0]
    due_iso = f"{due}T23:59:00+00:00" if due else None
    publish_now = f.get("publish", [""])[0] == "1"
    created = []
    for title in items:
        if already_set(db, int(gid), title, due_iso):
            continue
        created.append(db.execute(
            "INSERT INTO assignments (group_id, title, task_type, due_at, created_at, published)"
            " VALUES (?,?,?,?,?,?)",
            (int(gid), title, f.get("task_type", ["other"])[0], due_iso,
             core.iso(core.now()), 1 if publish_now else 0),
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


def act_close_assignment(req, db, aid):
    db.execute("UPDATE assignments SET closed=1 WHERE id=?", (aid,))
    db.commit()
    return redirect("/assignments")


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
    ("POST", r"^/materials/(\d+)/delete$", act_delete_material),
    ("GET", r"^/vocab$", view_vocab),
    ("GET", r"^/vocab/(\d+)$", view_word_list),
    ("GET", r"^/skip$", act_skip),
    ("POST", r"^/grade$", act_grade),
    ("POST", r"^/skip$", act_skip),
    ("POST", r"^/groups/new$", act_new_group),
    ("POST", r"^/groups/(\d+)/level$", act_set_group_level),
    ("POST", r"^/assignments/new$", act_new_assignment),
    ("POST", r"^/assignments/list$", act_new_list),
    ("POST", r"^/assignments/(\d+)/close$", act_close_assignment),
    ("POST", r"^/assignments/(\d+)/publish$", act_publish_assignment),
    ("POST", r"^/assignments/(\d+)/unpublish$", act_unpublish_assignment),
    ("POST", r"^/students/(\d+)/update$", act_update_student),
    ("POST", r"^/vocab/new$", act_new_word_list),
    ("POST", r"^/vocab/(\d+)/add$", act_add_words),
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
        ctype = "text/css" if name.endswith(".css") else "application/octet-stream"
        self._send(200, [("Content-Type", ctype), ("Content-Length", str(len(data))),
                         ("Cache-Control", "max-age=300")], data)

    def _serve_media(self, path):
        name = os.path.basename(urllib.parse.unquote(path))
        full = os.path.join(core.UPLOAD_DIR, name)
        if not os.path.isfile(full):
            return self._send(*not_found())
        with open(full, "rb") as fh:
            data = fh.read()
        ctype = ("audio/ogg" if name.endswith((".oga", ".ogg"))
                 else "image/png" if name.endswith(".png") else "image/jpeg")
        self._send(200, [("Content-Type", ctype), ("Content-Length", str(len(data))),
                         ("Cache-Control", "private, max-age=3600")], data)

    def _student_get(self, path, query):
        parts = path.split("/")
        if len(parts) != 3 or not parts[2]:
            return self._send(*not_found())
        flash = ""
        if "ok" in query:
            n = query["ok"][0]
            rejected = (query.get("r") or ["0"])[0]
            extra = (f" {rejected} photo(s) were too small to read and were not sent."
                     if rejected not in ("0", "") else "")
            flash = (f'<div class="flash">Sent {E(n)} page(s) to your teacher.'
                     f'{E(extra)}</div>')
        elif query.get("e") == ["small"]:
            flash = ('<div class="flash err">Those photos are too small or blurry to read. '
                     'Retake them: page flat, camera directly above, good light.</div>')
        elif query.get("e") == ["none"]:
            flash = '<div class="flash err">No photo was attached.</div>'
        db = core.connect()
        try:
            return self._send(*view_student_portal(None, db, parts[2], flash))
        finally:
            db.close()

    def _send(self, status, headers, body):
        self.send_response(status)
        for k, v in headers:
            self.send_header(k, v)
        self.end_headers()
        if body:
            self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlsplit(self.path)
        path, query = parsed.path, urllib.parse.parse_qs(parsed.query)

        if path.startswith("/static/"):
            return self._serve_static(path)
        if path.startswith("/s/"):
            return self._student_get(path, query)
        if re.match(r"^/materials/\d+/file$", path):
            db = core.connect()
            try:
                return self._send(*serve_material(db, int(path.split("/")[2])))
            finally:
                db.close()
        if path == "/login":
            return self._send(*view_login(None))
        if path == "/logout":
            return self._send(*redirect("/login", [("Set-Cookie", "ta_session=; Max-Age=0; Path=/")]))
        if not self._session():
            return self._send(*redirect("/login"))
        if path.startswith("/media/"):
            return self._serve_media(path)
        return self._dispatch("GET", path, {"query": query, "form": {}})

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
            # read the file fresh, so changing the password only needs a save
            expected = core.load_config()["teacher_password"]
            if secrets.compare_digest(form.get("password", [""])[0], expected):
                token = secrets.token_urlsafe(24)
                SESSIONS[token] = True
                return self._send(
                    *redirect("/", [("Set-Cookie",
                                     f"ta_session={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=2592000")])
                )
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
                        page("Error", f"<h1>Something broke</h1>"
                             f"<div class='card'><code>{E(str(exc))}</code></div>"
                             "<p><a href='/'>Back to overview</a></p>"), 500))
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
