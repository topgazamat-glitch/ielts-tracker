"""Teacher dashboard: grading queue, groups, students, progress charts.

Runs on the Python standard library alone: python3 server.py
"""
import html
import json
import math
import time
import os
import random
import re
import secrets
import threading
import traceback
import urllib.parse
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import card
import charts
import core
import parents
import uploads

CFG = core.load_config()
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

# The certificate's foil seal. These are the one place in the app with colours of
# their own: a certificate is printed and shared outside the site, so it keeps
# its gold whatever palette the page is wearing. Everything else uses the tokens
# in static/style.css.
FOIL = {"light": "#f7e3a1", "mid": "#d8b04a", "deep": "#a97c1c", "edge": "#8a6413"}


# ------------------------------------------------------------------ layout

def demo_banner():
    """Impossible to miss, on purpose. Nobody should ever wonder whether the
    class they are looking at is real."""
    if not core.demo_on():
        return ""
    return ('<div class="demobar"><strong>Demo.</strong> Every student on '
            'these pages is invented, and nothing here touches your real '
            'classes. <form method="post" action="/demo/reset">'
            '<button class="tab">Reset the demo</button></form>'
            '<form method="post" action="/demo/off">'
            '<button class="tab">Leave the demo</button></form></div>')


# The site grew one link at a time until eighteen of them wrapped to two rows
# and nobody could tell the day's work from the once-a-term pages. Five
# sections now, each a question the teacher actually asks: what is on today,
# what has come in, how are the students, what do I teach with, what does it
# pay. Every route is unchanged - only where the door to it is.
SECTIONS = [
    ("Today", "/", [("/", "Overview")]),
    ("Homework", "/queue", [("/queue", "Grade"), ("/speaking", "Speaking"), ("/homework", "Homework"),
                            ("/assignments", "Set homework")]),
    ("Students", "/roster", [("/roster", "Students"), ("/groups", "Groups"),
                             ("/ratings", "Progress"), ("/reteach", "Reteach"),
                             ("/records", "Records"), ("/questions", "Questions"),
                             ("/championship", "League"),
                             ("/parents", "Parents"),
                             ("/practice", "As a student")]),
    ("Materials", "/materials", [("/materials", "Materials"), ("/vocab", "Vocabulary"),
                                 ("/tests", "Tests"), ("/play", "Play"),
                                 ("/music", "Music")]),
    ("Insights", "/insights", [("/insights", "Insights"), ("/lessons", "Lessons"),
                               ("/kpi", "KPI")]),
]
SECTION_OF = {label: name for name, _home, pages in SECTIONS for _href, label in pages}


# One line drawing per section, in the sidebar's own stroke.
SIDE_ICONS = {
    "Today": '<rect x="3.5" y="5" width="17" height="15" rx="3"/><path d="M3.5 10h17M8 3v4M16 3v4"/>',
    "Homework": '<path d="M4 13l2.4-7.2A1.5 1.5 0 0 1 7.8 4.8h8.4a1.5 1.5 0 0 1 1.4 1L20 13v5a2 2 0 0 1-2 2H6'
                'a2 2 0 0 1-2-2z"/><path d="M4 13h4.5a3.5 3.5 0 0 0 7 0H20"/>',
    "Students": '<circle cx="9" cy="8" r="3.2"/><path d="M3.5 19.5a5.5 5.5 0 0 1 11 0"/>'
                '<path d="M15.5 5a3 3 0 0 1 0 6M17 14a5.5 5.5 0 0 1 3.5 5.5"/>',
    "Materials": '<path d="M12 6.5C10.3 5.2 7.9 4.5 4 4.5v13c3.9 0 6.3.7 8 2 1.7-1.3 4.1-2 8-2v-13'
                 'c-3.9 0-6.3.7-8 2z"/><path d="M12 6.5v13"/>',
    "Insights": '<path d="M4 20h16"/><path d="M7 16.5v-5M12 16.5V7M17 16.5v-8"/>',
    "Settings": '<path d="M4 7h9M17 7h3M4 17h3M11 17h9"/><circle cx="15" cy="7" r="2"/>'
                '<circle cx="9" cy="17" r="2"/>',
    "Sign out": '<path d="M14 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3"/><path d="M10 16l-4-4 4-4M6 12h9"/>',
    "Music": '<path d="M9 18V6.5l10-2V16"/><circle cx="6.5" cy="18" r="2.5"/><circle cx="16.5" cy="16" r="2.5"/>',
}


def side_icon(name):
    return ('<svg class="side-ico" viewBox="0 0 24 24" aria-hidden="true">%s</svg>'
            % SIDE_ICONS.get(name, SIDE_ICONS["Today"]))


def _static_version():
    """One fingerprint of everything in static/, worked out at start-up.

    Every page names the stylesheet and the scripts with it (?v=...), so a
    browser can keep them for a year and still fetch the new ones the moment
    a deploy changes them. They were kept for five minutes and then sent again
    whole - a quarter of a megabyte of stylesheet - on the first page after
    every short break, which is a long wait on a phone; and a change could
    only be seen after a hard reload.
    """
    import hashlib
    h = hashlib.sha1()
    folder = os.path.join(core.ROOT, "static")
    for name in sorted(os.listdir(folder)):
        full = os.path.join(folder, name)
        if os.path.isfile(full):
            h.update(name.encode())
            with open(full, "rb") as fh:
                h.update(fh.read())
    return h.hexdigest()[:10]


STATIC_V = _static_version()
# the gold mark from the rail, so a tab says whose site it is (and the
# browser stops asking for a /favicon.ico that is not there on every visit)
FAVICON = ('<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27'
           ' viewBox=%270 0 32 32%27%3E%3Crect width=%2732%27 height=%2732%27 rx=%279%27'
           ' fill=%27%23ffc76a%27/%3E%3Ccircle cx=%2716%27 cy=%2716%27 r=%277.2%27 fill=%27none%27'
           ' stroke=%27%232a0736%27 stroke-width=%273.6%27/%3E%3C/svg%3E">')

# Before the page is drawn: the sidebar as it was left, open or narrowed to
# its icons, so it never opens and then snaps shut on the way in.
SIDE_EARLY = ('<script>try{if(localStorage.getItem("side")==="rail")'
              'document.documentElement.classList.add("rail")}catch(e){}'
              'document.documentElement.classList.add("still")</script>')


def side_link(href, name, icon, on, badge=""):
    cls = ' class="on"' if on else ""
    return (f'<a href="{href}"{cls} data-tip="{E(name)}">{icon}'
            f'<span class="side-label">{E(name)}</span>{badge}</a>')


def side_nav(groups):
    """The sections, each with its pages under it: the section you are in
    shows them, any other opens with its arrow - a page that could only be
    found from inside its section was a page nobody found.
    groups: [(name, home, icon, on, badge, [(href, label, on, badge)])]"""
    out = []
    lit = ' class="on" aria-current="page"'
    for name, home, icon, on, badge, pages in groups:
        link = side_link(home, name, icon, on, badge)
        if len(pages) < 2:
            out.append(f'<div class="side-group">{link}</div>')
            continue
        subs = "".join(f'<a href="{h}"{lit if here else ""}>{E(l)}{b}</a>' for h, l, here, b in pages)
        out.append(
            f'<div class="side-group{" open" if on else ""}" data-sec="{E(name)}">'
            f'<div class="side-row">{link}'
            f'<button type="button" class="side-more" aria-expanded="{"true" if on else "false"}"'
            f' aria-label="{E(name)} pages"><svg viewBox="0 0 24 24" aria-hidden="true">'
            f'<path d="M9 6l6 6-6 6"/></svg></button></div>'
            f'<div class="side-sub"><div class="side-sub-in" role="group" aria-label="{E(name)}">'
            f'<p class="side-sub-head">{E(name)}</p>{subs}</div></div></div>')
    return "".join(out)


def top_tabs(name, pages):
    """The pages of the section, across the top of the work."""
    if len(pages) < 2:
        return ""
    here = ' class="on" aria-current="page"'
    links = "".join(f'<a href="{h}"{here if on else ""}>{E(l)}{b}</a>' for h, l, on, b in pages)
    return (f'<nav class="toptabs" aria-label="{E(name)}">{links}'
            f'<span class="tab-glide" aria-hidden="true"></span></nav>')


MUSIC_ROW = ('<div class="side-music"><button type="button" id="musicbtn" class="musicbtn"'
             ' onclick="Music.toggle()" title="Music" data-tip="Music"></button>'
             '<span id="songname" class="songname side-label" hidden></span></div>')


def shell(title, body, *, nav, foot, heading, tabs, home="/", role="Teacher", scripts=(),
          main_class="", after="", banner="", tune="", body_class="shell"):
    """The frame both sides of the site share: the rail down the left, the
    bar with the section's pages over the work, the work beneath."""
    main_attr = f' class="{main_class}"' if main_class else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{E(title)} · OlimovAzamat</title>
{SIDE_EARLY}
{FAVICON}<link rel="stylesheet" href="/static/style.css?v={STATIC_V}"></head><body class="{body_class}">
<aside class="side" id="side" aria-label="Main menu">
  <div class="side-head">
    <a class="side-brand" href="{home}" data-tip="OlimovAzamat"><span class="mark">O</span>
      <span class="side-label">OlimovAzamat<small>{E(role)}</small></span></a>
    <button type="button" class="side-toggle" id="sidetoggle" aria-controls="side" aria-expanded="true"
            title="Hide the menu  [" aria-label="Hide the menu"><svg viewBox="0 0 24 24" aria-hidden="true">
      <rect x="3.5" y="4.5" width="17" height="15" rx="3"/><path d="M9.5 4.5v15M15.5 10l-2 2 2 2"/></svg><svg
      class="side-x" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg></button>
  </div>
  <nav class="side-nav" aria-label="Sections">{nav}</nav>
  <div class="side-foot">{foot}</div>
</aside>
<div class="side-scrim" id="sidescrim"></div>
<div class="stage">
{banner}<header class="topbar">
  <div class="topbar-in">
    <button type="button" class="side-open" id="sideopen" aria-controls="side" aria-expanded="false"
            aria-label="Show the menu"><svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M4 7h16M4 12h16M4 17h16"/></svg></button>
    <div class="topbar-title">{E(heading)}</div>
    {tabs}
  </div>
</header>
<main{main_attr}>{body}</main>
{after}
</div>
{tune}{"".join(f'<script src="/static/{js}?v={STATIC_V}" defer></script>' for js in scripts)}
</body></html>"""


def page(title, body, active="", music=False):
    """The teacher's shell: the sections down the left, the pages of the one
    you are in across the top of the work, the work beneath. The sidebar
    narrows to its icons and back with one button (or the [ key), and
    remembers how it was left. Silent unless a page asks otherwise: marking
    for three hours should not come with a soundtrack - but the song of the
    day is the teacher's own choice, so that one plays here too."""
    tune = song_tag()
    section = SECTION_OF.get(active, "")
    if active == "Settings":
        section = "Settings"
    groups = [(name, home, side_icon(name), name == section, "",
               [(h, l, name == section and l == active, "") for h, l in pages])
              for name, home, pages in SECTIONS]
    tabs = next((top_tabs(name, [(h, l, l == active, "") for h, l in pages])
                 for name, _home, pages in SECTIONS if name == section), "")
    foot = ((MUSIC_ROW if (music or tune) else "")
            + side_link("/settings", "Settings", side_icon("Settings"), section == "Settings")
            + side_link("/logout", "Sign out", side_icon("Sign out"), False))
    scripts = (["music.js"] if (music or tune) else []) + [
        "shell.js", "nav.js", "listen.js", "materials.js", "voice.js", "speak.js", "grade.js", "prompts.js", "roster.js", "marks.js"]
    return shell(title, body, nav=side_nav(groups), foot=foot, heading=section or title, tabs=tabs,
                 scripts=scripts, banner=demo_banner(), tune=tune)


# A small drawing for each kind of figure, in the rail's stroke.
LOOK_ICONS = {
    "inbox": SIDE_ICONS["Homework"],
    "users": SIDE_ICONS["Students"],
    "chart": SIDE_ICONS["Insights"],
    "book": SIDE_ICONS["Materials"],
    "calendar": SIDE_ICONS["Today"],
    "check": '<circle cx="12" cy="12" r="8.5"/><path d="M8.5 12.3l2.4 2.4 4.8-5"/>',
    "clock": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
    "alert": '<path d="M12 4.5l8.5 15h-17z"/><path d="M12 10v4M12 17h.01"/>',
    "flame": '<path d="M12 3.5c.8 2.8 4.5 4.6 4.5 8.8a4.5 4.5 0 0 1-9 0c0-1.9.9-3.3 2-4.3.4 1.4 1.3 2.1 2.3 2.1'
             '-.3-2.4-.4-4.2.2-6.6z"/>',
    "message": '<path d="M4.5 5.5h15v10.5H9l-4.5 3.5z"/><path d="M8.5 9.5h7M8.5 12.5h4.5"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
}
# more drawings, for the shelves of files: what a section holds, what a file is
LOOK_ICONS.update({
    "headphones": '<path d="M4 15v-3a8 8 0 0 1 16 0v3"/><rect x="3.5" y="14" width="4" height="6" rx="1.6"/>'
                  '<rect x="16.5" y="14" width="4" height="6" rx="1.6"/>',
    "file": '<path d="M7 3.5h7l4.5 4.5v12a1.5 1.5 0 0 1-1.5 1.5H7A1.5 1.5 0 0 1 5.5 20V5A1.5 1.5 0 0 1 7 3.5z"/>'
            '<path d="M14 3.5V8h4.5M8.5 12.5h7M8.5 16h5"/>',
    "image": '<rect x="3.5" y="4.5" width="17" height="15" rx="2.5"/><circle cx="9" cy="10" r="1.8"/>'
             '<path d="M20.5 16l-5-5-8.5 8.5"/>',
    "video": '<rect x="3.5" y="6" width="12.5" height="12" rx="2.5"/><path d="M16 10.5l4.5-2.5v8l-4.5-2.5"/>',
    "slides": '<rect x="3.5" y="4.5" width="17" height="11.5" rx="2"/><path d="M12 16v3.5M8.5 19.5h7"/>',
    "trophy": '<path d="M8 4h8v5a4 4 0 0 1-8 0zM8 6H5v1.5A3 3 0 0 0 8 10.5M16 6h3v1.5a3 3 0 0 1-3 3M12 13v4M8.5 20h7M10 17h4"/>',
    "play": '<path d="M8.5 5.8v12.4L18.5 12z"/>',
    "bolt": '<path d="M13 2.5 5 13.5h6l-1 8 8-11h-6z"/>',
    "lock": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    "clipboard": '<rect x="5.5" y="5" width="13" height="15.5" rx="2"/><path d="M9 5V3.8h6V5M8.5 11l2 2 4-4M8.5 16.5h7"/>',
    "cap": '<path d="M2.5 9.5L12 5l9.5 4.5L12 14z"/><path d="M6.5 11.5v4c1.5 1.4 3.4 2 5.5 2s4-.6 5.5-2v-4M21.5 9.5v5"/>',
    "list": '<path d="M9 7h11M9 12h11M9 17h11"/><circle cx="4.8" cy="7" r=".9"/><circle cx="4.8" cy="12" r=".9"/>'
            '<circle cx="4.8" cy="17" r=".9"/>',
    "user": '<circle cx="12" cy="8" r="3.5"/><path d="M5 20a7 7 0 0 1 14 0"/>',
    "layers": '<path d="M12 4l8.5 4.5L12 13 3.5 8.5z"/><path d="M3.5 12.5L12 17l8.5-4.5M3.5 16.5L12 21l8.5-4.5"/>',
    "trash": '<path d="M4.5 7h15M9.5 7V4.8h5V7M6.5 7l.9 12.2a1.5 1.5 0 0 0 1.5 1.3h6.2a1.5 1.5 0 0 0 1.5-1.3L17.5 7'
             'M10 11v6M14 11v6"/>',
    "upload": '<path d="M12 15.5V4.5M7.5 9L12 4.5 16.5 9"/><path d="M4.5 15v3a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2v-3"/>',
    "search": '<circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.4-4.4"/>',
    "folder": '<path d="M3.5 7.5a2 2 0 0 1 2-2h4l2 2.5h7a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-13a2 2 0 0 1-2-2z"/>',
    "chevron": '<path d="M9 6l6 6-6 6"/>',
})
# which drawing and colour a figure takes, from the words of its label
STAT_LOOKS = [
    (("wait", "grading", "queue", "pending", "to mark"), "inbox", "amber"),
    (("marked", "graded", "checked"), "check", "green"),
    (("streak",), "flame", "amber"),
    (("left", "risk", "missed", "late", "flag", "behind"), "alert", "rose"),
    (("student", "people", "class", "group", "here", "active"), "users", "blue"),
    (("average", "score", "mark", "band", "exam", "result", "rating"), "chart", "plum"),
    (("homework", "done", "completion", "complete", "sent", "handed"), "check", "green"),
    (("week", "day", "time", "longest", "oldest"), "clock", "amber"),
    (("word", "vocab", "test", "material", "file", "handout"), "book", "blue"),
]


def look_icon(name, cls="look-ico"):
    return (f'<span class="{cls}" aria-hidden="true"><svg viewBox="0 0 24 24">'
            f'{LOOK_ICONS.get(name, LOOK_ICONS["chart"])}</svg></span>')


def stat(k, v, sub="", busy=False, icon=None, tone=None):
    """One figure, with a small drawing of what it counts. Colour means
    something here or it is not used: the only tile that turns red is the
    queue, and only when it has grown."""
    words = (k or "").lower()
    guess = next(((i, t) for keys, i, t in STAT_LOOKS if any(w in words for w in keys)), ("chart", "plum"))
    icon, tone = icon or guess[0], ("rose" if busy else tone or guess[1])
    s = f'<div class="note">{E(sub)}</div>' if sub else ""
    cls = "stat busy" if busy else "stat"
    return (f'<div class="{cls} t-{tone}">{look_icon(icon)}<div class="k">{E(k)}</div>'
            f'<div class="v">{v}</div>{s}</div>')


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
    return html_response(student_page("Sign in", body, music=False))


def view_overview(req, db):
    pending = db.execute(
        "SELECT COUNT(*) c FROM submissions WHERE status='pending' AND draft=0"
    ).fetchone()["c"]
    oldest = db.execute(
        "SELECT MIN(created_at) c FROM submissions WHERE status='pending'"
        " AND draft=0").fetchone()["c"]
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
    # The average is of the students who have a graded score, which on a day
    # with a queue is not all of them. Saying so stops it reading as a claim
    # about the class while half of it sits ungraded below.
    from_who = ("from %d of %d students" % (len(all_avg), len(students))
                if all_avg else "nothing graded yet")
    cards = (
        '<div class="grid">'
        + stat("Awaiting grading", pending, waited_for(oldest, pending),
               busy=pending >= 20)
        + stat("Active students", len(students), "in %d classes" % len(groups))
        + stat("Average score", fmt(avg), from_who)
        + "</div>"
    )

    # "Needs attention" firing for nearly everybody is not a warning, it is
    # wallpaper. The reasons are counted, the worst are shown, and the rest are
    # left to the Progress page rather than filling the screen.
    SHOW = 10
    why_counts = {}
    for _s, st in risky:
        if st["consecutive_misses"] >= 2:
            why_counts["misses in a row"] = why_counts.get("misses in a row", 0) + 1
        if st["trend"] is not None and st["trend"] <= -1.0:
            why_counts["a falling trend"] = why_counts.get("a falling trend", 0) + 1
    summary = ""
    if risky:
        parts = ", ".join("%d for %s" % (n, w)
                          for w, n in sorted(why_counts.items(), key=lambda p: -p[1]))
        more = (" Showing the %d worst." % SHOW) if len(risky) > SHOW else ""
        summary = (f'<p class="sub" style="margin-top:0">'
                   f'<strong>{len(risky)} of {len(students)}</strong> students '
                   f'flagged &mdash; {parts}.{more}</p>')
        if pending:
            summary += (f'<p class="sub">{pending} submissions are still waiting '
                        f'to be marked, and unmarked work counts as a miss, so '
                        f'some of these will clear themselves when you grade.</p>')

    if risky:
        risky = risky[:SHOW]
        rows = "".join(
            f'<tr><td><a href="/students/{s["id"]}">{E(s["name"])}</a></td>'
            f'<td>{E(group_name(db, s["group_id"]))}</td>'
            f'<td>{score_pill(st["last3"])}</td>'
            f'<td>{fmt(st["completion"], "—")}{"%" if st["completion"] is not None else ""}</td>'
            f'<td>{reason(st)}</td></tr>'
            for s, st in risky
        )
        risk_html = (
            summary
            + '<div class="tablewrap"><table><tr><th>Student</th><th>Group</th>'
            "<th>Last 3</th><th>Completion</th><th>Why flagged</th></tr>"
            f"{rows}</table></div>"
        )
    else:
        risk_html = '<div class="card"><p class="sub">Nobody is flagged. '
        risk_html += "Students appear here after two consecutive misses or a falling trend.</p></div>"

    # Housekeeping is real, but it is not the day's work: it sits last, in
    # one card, instead of a button and two warnings scattered up the page.
    worry = core.password_worry()
    housekeeping = (
        '<h2>Housekeeping</h2><div class="card">'
        + disk_note() + disk_breakdown_note()
        + (f'<p class="flash err">{E(worry)}</p>' if worry else "")
        + cleanup_button(db)
        + '<p class="sub flush gap-3">Everything here lives on one disk. '
          '<a class="linky" href="/backup">Download a copy of the database</a> '
          'and keep it somewhere else &mdash; the bot sends you one every day '
          'as well.</p></div>')
    body = f"""{today_block(db, pending)}
<h2>Where everyone stands</h2>{cards}<h2>Needs attention</h2>{risk_html}
{housekeeping}"""
    return html_response(page("Overview", body, "Overview"))


TODO_ICONS = {"/queue": "inbox", "/homework": "calendar", "/ratings": "alert", "/questions": "message"}


def todo(href, headline, detail, urgent=False):
    icon = next((i for start, i in TODO_ICONS.items() if href.startswith(start)), "arrow")
    return (f'<a class="todo todo-card{" urgent" if urgent else ""}" href="{href}">{look_icon(icon, "t-ico")}'
            f'<span class="t-text"><span class="todo-head">{headline}</span>'
            f'<span class="sub">{detail}</span></span>'
            f'<svg class="t-go" viewBox="0 0 24 24" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg></a>')


def today_head(db, pending):
    """The day, by name, and the two things most often done from here."""
    cfg = core.load_config()
    here = core.now() + timedelta(hours=cfg["timezone_offset_hours"])
    part = "morning" if here.hour < 12 else "afternoon" if here.hour < 18 else "evening"
    name = cfg.get("teacher_name") or "Azamat"
    grade = (f'<a class="btn" href="/queue">Grade {pending}</a>' if pending
             else '<a class="btn ghost" href="/queue">Grade</a>')
    return (f'<div class="pagehead"><div><p class="eyebrow">{here.strftime("%A, %-d %B")}</p>'
            f'<h1>Good {part}, {E(name)}</h1></div>'
            f'<div class="actions">{grade}<a class="btn ghost" href="/assignments">Set homework</a></div></div>')


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

    heard = [r for r in core.recordings(db) if not r["cant"] and not (r["note"] or r["fb_voice"])]
    if heard:
        items += todo("/speaking", "%d recording%s to listen to" % (len(heard), "" if len(heard) == 1 else "s"),
                      "from the handouts' speaking tasks", urgent=len(heard) >= 15)

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
        items += todo(f'/homework?group={r["group_id"]}',
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
        return (today_head(db, pending) + '<div class="card calm"><p>'
                'Nothing is waiting. Everything is graded and every class is up to '
                'date.</p></div>')
    return today_head(db, pending) + f'<div class="todos">{items}</div>'


def disk_breakdown_note():
    """Where the volume actually went - shown only when room is short."""
    free, total = core.disk_room()
    if not free or not total or free / total > 0.25:
        return ""
    rows = core.disk_breakdown()[:6]
    if not rows:
        return ""
    bits = " &middot; ".join("%s %s" % (E(n), core.human_size(b))
                             for n, b in rows if b)
    return '<p class="sub gap-2">On the disk: %s</p>' % bits


def cleanup_button(db):
    last = core.meta_get(db, "last_cleanup", "")
    return ('<form method="post" action="/cleanup" class="cleanup">'
            '<button class="ghost">Free up space now</button>'
            '<span class="sub flush">Lets go of the full-size photographs of '
            'work marked more than %s days ago; they come back from Telegram '
            'when opened.%s</span></form>'
            % (core.load_config().get("photo_keep_days", 10),
               ("<br>Last run: " + E(last)) if last else ""))


def disk_note():
    """Warn before the volume fills, not after - once it is full, the site
    still reads and nobody can sign in."""
    free, total = core.disk_room()
    if not free or not total:
        return ""
    share = free / total
    if share > 0.12:
        return ""
    return ('<div class="flash err gap-5">Only %.0f MB of %.1f GB left on the '
            'disk. When it fills, the site keeps loading pages but nobody can '
            'sign in. Delete some materials, or give the volume more room.'
            '</div>' % (free / 1048576, total / 1073741824))


def waited_for(oldest, pending):
    """How long the queue's oldest piece has been sitting there."""
    if not pending:
        return "nothing waiting"
    if not oldest:
        return ""
    days = (core.now() - core.parse(oldest)).days
    if days >= 1:
        return "oldest waiting %d day%s" % (days, "" if days == 1 else "s")
    return "all arrived today"


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


AUDIO_EXT = (".oga", ".ogg", ".mp3", ".m4a", ".wav", ".opus", ".weba", ".webm", ".mp4")


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


def attach_card(db, sub, student):
    """A piece that came without its task - the website lost the student's
    choice for a while - is put with the right one here, so it ticks their
    list and is marked the way that task is."""
    rows = db.execute(
        "SELECT id, title, due_at FROM assignments WHERE group_id=? AND published=1"
        " AND created_at >= ? ORDER BY COALESCE(due_at, created_at) DESC, id",
        (student["group_id"], core.iso(core.now() - timedelta(days=30)))).fetchall()
    if not rows:
        return ""
    cfg = core.load_config()
    opts = "".join(
        f'<option value="{a["id"]}">{E(a["title"])}'
        f'{" · due " + core.local_day(core.parse(a["due_at"]), cfg) if a["due_at"] else ""}</option>'
        for a in rows)
    return f"""<form method="post" action="/grade/attach" class="card attach">
  <input type="hidden" name="submission_id" value="{sub["id"]}">
  <label class="f">Which homework is this?<select name="assignment_id">{opts}</select></label>
  <button class="ghost">Put it there</button>
</form>"""


def act_grade_attach(req, db):
    f = req["form"]
    sid, aid = (f.get("submission_id", [""])[0] or ""), (f.get("assignment_id", [""])[0] or "")
    if not (sid.isdigit() and aid.isdigit()):
        return redirect("/queue")
    sub = db.execute("SELECT s.*, st.group_id FROM submissions s JOIN students st ON st.id=s.student_id"
                     " WHERE s.id=?", (int(sid),)).fetchone()
    a = db.execute("SELECT * FROM assignments WHERE id=?", (int(aid),)).fetchone()
    if not sub or not a or a["group_id"] != sub["group_id"]:
        return redirect("/queue")
    late = 1 if (a["due_at"] and sub["created_at"] > a["due_at"]) else 0
    db.execute("UPDATE submissions SET assignment_id=?, late=? WHERE id=?", (a["id"], late, sub["id"]))
    db.commit()
    return redirect(f"/queue?id={sub['id']}")


def grade_form(db, sub, student, assignment, regrade=False, gid=None, due=None):
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
    paper = bool(assignment and assignment["test_id"] and core.is_handout(db, assignment["test_id"]))
    if paper:
        # the paper copy of a digital handout: done or not done, and a real
        # mark only when the teacher chooses to give one
        tick = core.PAPER_TICK
        scoring = f"""<div class="tickpad">
  <p class="sub flush">The paper copy of a handout. Done is worth {tick:g} out of 10 &mdash;
  the half of the digital one's mark that is for doing it.</p>
  <div class="tickbtns">
    <button name="tick" value="done" id="tick-y" class="tick-yes">&#10003; Done &middot; {tick:g}/10</button>
    <button name="tick" value="not" id="tick-n" class="ghost danger">&#10007; Not complete</button>
  </div>
  <p class="sub flush">Keys <span class="kbd">y</span> and <span class="kbd">n</span>.</p>
</div>
<details class="gap-2"><summary>Mark it properly instead</summary>
<input type="hidden" name="score" id="f_score"
 value="{sub["score"] if sub["score"] is not None else ""}">{scorepad("score", sub["score"])}
</details>"""
    elif rubric:
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
    keep = ((f'<input type="hidden" name="group" value="{gid}">' if gid else "")
            + (f'<input type="hidden" name="due" value="{E(due)}">' if due else ""))
    return f"""<form method="post" action="{action}" id="gform" class="card">
      <input type="hidden" name="submission_id" value="{sub['id']}">{keep}
      {scoring}
      {recur}
      <div class="tags">{tagboxes}</div>
      <label class="f">Note (optional)
        <textarea name="note" id="note" rows="2"
          placeholder="One line the student will read">{E(sub["note"] or "")}</textarea></label>
      <div class="chips">{chips}</div>
      <div class="voice" id="voice" data-sid="{sub["id"]}">
        <div class="voice-row">
          <button type="button" class="ghost" id="rec"><i class="dot"></i>Record a voice note</button>
          <span class="rec-vu" id="recvu" hidden><i></i></span><span class="rec-clock" id="recclock"></span>
          <select class="mic-pick" id="recmic" hidden aria-label="Which microphone"></select>
          <span class="rec-say" id="rectime" aria-live="polite"></span>
        </div>
        <div class="voice-have" id="recwrap"{"" if sub["voice"] else " hidden"}>
          <audio controls preload="metadata" id="recplay"
                 src="{("/media/" + E(sub["voice"])) if sub["voice"] else ""}"></audio>
          <button type="button" class="linky danger" id="recdel">remove</button>
        </div>
      </div>
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


def queue_rows(db):
    """Every piece waiting to be marked, with the two things the teacher sorts
    by: whose class it is, and which lesson's deadline it belongs to."""
    cfg = core.load_config()
    out = []
    for r in db.execute(
            "SELECT s.id, s.student_id, s.created_at, s.kind, s.late, s.assignment_id,"
            " st.name, st.group_id, a.title, a.due_at"
            " FROM submissions s JOIN students st ON st.id=s.student_id"
            " LEFT JOIN assignments a ON a.id=s.assignment_id"
            " WHERE s.status='pending' AND s.draft=0 ORDER BY s.created_at").fetchall():
        day = core.deadline_parts(r["due_at"], cfg)[0] if r["due_at"] else ""
        out.append({"id": r["id"], "student_id": r["student_id"], "name": r["name"],
                    "group_id": r["group_id"], "created_at": r["created_at"],
                    "kind": r["kind"], "late": r["late"], "title": r["title"],
                    "due": day or "none"})
    return out


DUE_AT = re.compile(r"^\d{4}-\d{2}-\d{2}$|^none$")


def queue_filter(q):
    """The class and the deadline day a queue address asks for, if any."""
    g = (q.get("group", [""])[0] or "").strip()
    d = (q.get("due", [""])[0] or "").strip()
    return (int(g) if g.isdigit() else None), (d if DUE_AT.match(d) else None)


def queue_url(gid=None, due=None, **extra):
    """The address of a set. With neither class nor deadline it is the pile
    itself, and `all=1` keeps a save from landing back on the picker."""
    q = {}
    if gid:
        q["group"] = gid
    if due:
        q["due"] = due
    q.update({k: v for k, v in extra.items() if v})
    if not q:
        q["all"] = "1"
    return "/queue?" + urllib.parse.urlencode(q)


def in_set(rows, gid, due):
    return [r for r in rows if (gid is None or r["group_id"] == gid)
            and (due is None or r["due"] == due)]


def day_words(day, cfg):
    """A deadline day as a short label and how far off it is."""
    if day == "none":
        return "No deadline", ""
    when = datetime.strptime(day, "%Y-%m-%d").date()
    today = datetime.strptime(core.local_day(core.now(), cfg), "%Y-%m-%d").date()
    gap = (when - today).days
    rel = ("today" if gap == 0 else "tomorrow" if gap == 1 else "yesterday" if gap == -1
           else "in %d days" % gap if gap > 0 else "%d days ago" % -gap)
    return when.strftime("%a %-d %b"), rel


def queue_picker(db, rows, gid, due, pick=None):
    """What is waiting, as something to choose from rather than a chart to
    read. Four figures, then the classes as bars; press a class and its
    deadlines appear as bars; press a deadline and that is the set being
    marked. Every row is a label, one number and a button."""
    cfg = core.load_config()
    if not rows:
        return ""
    groups = {g["id"]: g["name"] for g in db.execute("SELECT id, name FROM groups")}
    oldest = min(r["created_at"] for r in rows)
    waited = (core.now() - core.parse(oldest)).days
    marked_today = db.execute(
        "SELECT COUNT(*) c FROM submissions WHERE status='graded' AND graded_at IS NOT NULL"
        " AND graded_at >= ?", (core.iso(core.now() - timedelta(hours=24)),)).fetchone()["c"]
    marked_week = db.execute(
        "SELECT COUNT(*) c FROM submissions WHERE status='graded' AND graded_at IS NOT NULL"
        " AND graded_at >= ?", (core.iso(core.now() - timedelta(days=7)),)).fetchone()["c"]
    tiles = ('<div class="grid qtiles">'
             + stat("Waiting to be marked", len(rows), "pieces of homework",
                    busy=len(rows) >= 20)
             + stat("Longest wait", "%d day%s" % (waited, "" if waited == 1 else "s")
                    if waited else "today", "the oldest piece arrived")
             + stat("Marked today", marked_today, "in the last 24 hours")
             + stat("Marked this week", marked_week, "in the last 7 days")
             + "</div>")

    by_class = {}
    for r in rows:
        by_class.setdefault(r["group_id"], []).append(r)
    classes = sorted(by_class, key=lambda g: groups.get(g, ""))

    def tab(href, label, n, on):
        return (f'<a class="tab{" on" if on else ""}" href="{href}">{E(label)}'
                f'<span class="n">{n}</span></a>')
    tabs = ('<div class="tabs">' + tab("/queue", "All classes", len(rows), pick is None)
            + "".join(tab("/queue?pick=%d" % g, groups.get(g, "?"), len(by_class[g]),
                          pick == g) for g in classes) + "</div>")

    def bar(label, note, n, top, href, on, button):
        pct = max(4, int(100 * n / top))
        return (f'<div class="pickrow{" on" if on else ""}">'
                f'<div class="pick-who"><a href="{href}">{label}</a>'
                f'{f"<div class=sub>{note}</div>" if note else ""}</div>'
                f'<div class="track"><div class="fill" style="width:{pct}%"></div></div>'
                f'<div class="n">{n}</div>'
                f'<a class="btn{" ghost" if on else ""}" href="{href}">{button}</a></div>')

    if pick is None or pick not in by_class:
        top = max(len(v) for v in by_class.values())
        body = ""
        for g in classes:
            mine = by_class[g]
            days = sorted({r["due"] for r in mine}, key=lambda d: (d == "none", d))
            first = days[0]
            when = (("oldest due " + day_words(first, cfg)[0]
                     + (" · " + day_words(first, cfg)[1] if day_words(first, cfg)[1] else ""))
                    if first != "none" else "no deadline")
            body += bar(E(groups.get(g, "?")),
                        f'{len(days)} deadline{"" if len(days) == 1 else "s"} &middot; {E(when)}',
                        len(mine), top, "/queue?pick=%d" % g, False, "Choose")
        lead = ("Press a class to see its lessons, then choose one - or take "
                "everything, oldest first.")
    else:
        mine = by_class[pick]
        by_day = {}
        for r in mine:
            by_day.setdefault(r["due"], []).append(r)
        days = sorted(by_day, key=lambda d: (d == "none", d))
        top = max(len(v) for v in by_day.values())
        body = ""
        for d in days:
            label, rel = day_words(d, cfg)
            titles = sorted({r["title"] or "no homework" for r in by_day[d]})
            shown = ", ".join(t[:28] for t in titles[:2]) + (
                " and %d more" % (len(titles) - 2) if len(titles) > 2 else "")
            here = gid == pick and due == d
            body += bar(("Due " + E(label)) if d != "none" else "No deadline",
                        (E(rel) + " &middot; " if rel else "") + E(shown),
                        len(by_day[d]), top, queue_url(pick, d), here,
                        "Marking now" if here else "Mark these")
        lead = (f"{E(groups.get(pick, '?'))}'s homework, by the lesson it was for, "
                "oldest first. Press one to mark just that set.")
    everything = ""
    if pick is None or pick not in by_class:
        everything = (f'<p class="gap-3 flush"><a class="btn ghost" href="/queue?all=1">'
                      f'Mark everything, oldest first &middot; {len(rows)}</a></p>')
    else:
        everything = (f'<p class="gap-3 flush"><a class="btn ghost" href="{queue_url(pick)}">'
                      f'Mark all of {E(groups.get(pick, "?"))}, oldest first &middot; '
                      f'{len(by_class[pick])}</a></p>')
    return (f'{tiles}<div class="card picker"><h3 class="flush">What to mark</h3>'
            f'<p class="sub gap-1">{lead}</p>{tabs}<div class="pickrows">{body}</div>'
            f'{everything}</div>')


def set_progress_counts(db, gid, due, left):
    """How far through a set the teacher is: what is marked against what is
    left. A set is one class's work for one lesson, so everything ever marked
    for it counts, not just today's."""
    if gid is None and due is None:
        return None
    cfg = core.load_config()
    marked = 0
    for r in db.execute(
            "SELECT s.id, st.group_id, a.due_at FROM submissions s"
            " JOIN students st ON st.id=s.student_id"
            " LEFT JOIN assignments a ON a.id=s.assignment_id"
            " WHERE s.status='graded' AND s.draft=0"
            + (" AND st.group_id=?" if gid else ""), (gid,) if gid else ()).fetchall():
        day = (core.deadline_parts(r["due_at"], cfg)[0] if r["due_at"] else "") or "none"
        if due is None or day == due:
            marked += 1
    return {"marked": marked, "total": marked + left}


def set_bar(db, rows, inset, gid, due):
    """One strip above the work: what is being marked, how far along, and the
    two ways out - jump to a student, or go back and choose something else.
    It replaces the whole picker on every page after the first, so the work
    stays at the top of the screen."""
    cfg = core.load_config()
    if gid or due:
        what = " &middot; ".join(
            ([E(group_name(db, gid))] if gid else [])
            + ([("due " + day_words(due, cfg)[0]) if due != "none" else "no deadline"]
               if due else []))
        rel = day_words(due, cfg)[1] if due and due != "none" else ""
        title = f'<strong>Marking {what}</strong>'
        note = (rel + " &middot; " if rel else "") + f'{len(inset)} left in this set'
    else:
        title = "<strong>Marking everything</strong>"
        note = f"{len(inset)} waiting, oldest first"
    prog = set_progress_counts(db, gid, due, len(inset))
    bar = ""
    if prog and prog["total"]:
        pct = int(100 * prog["marked"] / prog["total"])
        bar = (f'<div class="prog"><div class="track"><div class="fill" '
               f'style="width:{pct}%"></div></div><div class="sub">'
               f'{prog["marked"]} of {prog["total"]} marked</div></div>')
    acts = ((f'<a href="/queue?pick={gid}">Other lessons of {E(group_name(db, gid))}</a>'
             ' &middot; ' if gid else "") + '<a href="/queue">All classes</a>')
    return (f'<div class="setbar"><div class="what">{title}<div class="sub">{note}</div></div>'
            f'{bar}<div class="acts">{acts}</div></div>')


def waiting_list(db, current_id, rows, gid=None, due=None):
    """Everyone still in the set, so a name can be found without hunting."""
    rows = rows[:60]
    if len(rows) < 2:
        return ""
    out = ""
    for r in rows:
        here = ' class="on"' if r["id"] == current_id else ""
        kind = ' <span class="pill mute">speaking</span>' if r["kind"] == "voice" else ""
        late = ' <span class="pill risk">late</span>' if r["late"] else ""
        out += (f'<li{here}><a href="{queue_url(gid, due, id=r["id"])}">{E(r["name"])}</a>'
                f'<span class="sub">{E(group_name(db, r["group_id"]))}'
                f'{" &middot; " + E(r["title"]) if r["title"] else ""}</span>'
                f'{kind}{late}</li>')
    what = "in this set" if (gid or due) else "waiting"
    return (f'<details class="card queuelist"><summary>{len(rows)} {what} '
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


def grade_page(db, sub, regrade=False, rows=None, gid=None, due=None, show_picker=False,
               pick=None):
    student = db.execute("SELECT * FROM students WHERE id=?", (sub["student_id"],)).fetchone()
    assignment = (db.execute("SELECT * FROM assignments WHERE id=?",
                             (sub["assignment_id"],)).fetchone()
                  if sub["assignment_id"] else None)
    files = db.execute("SELECT * FROM files WHERE submission_id=? ORDER BY ord, id",
                       (sub["id"],)).fetchall()
    st = core.student_stats(db, student["id"])
    if sub["kind"] == "text":
        # typed work reads as a paper: the question, then what they wrote
        mins = ""
        if sub["written_secs"]:
            mins = " &middot; %d min at the keyboard" % max(1, sub["written_secs"] // 60)
        q = (f'<div class="question"><h3>The question</h3>'
             f'<div class="qtext">{E(assignment["prompt"])}</div></div>'
             if assignment and assignment["prompt"] else "")
        shots = (f'<div class="paper reading">{q}'
                 f'<div class="sheet"><h3>{sub["words"] or 0} words{mins}</h3>'
                 f'<div class="written">{E(sub["answer"] or "")}</div></div></div>')
    else:
        shots = "".join(shot(f, i) for i, f in enumerate(files)) \
            or '<p class="sub">Nothing attached.</p>'

    rows = rows if rows is not None else (queue_rows(db) if not regrade else [])
    inset = in_set(rows, gid, due)
    remaining = len(inset)

    # while this student is being scored, quietly pull the next one's pages, so
    # the queue never makes the teacher wait for a download again
    ahead = []
    if not regrade:
        nxt = next((r for r in inset if r["id"] != sub["id"]), None)
        if nxt:
            ahead = [screen_name(f) for f in db.execute(
                "SELECT * FROM files WHERE submission_id=? ORDER BY ord, id LIMIT 4",
                (nxt["id"],)).fetchall() if not is_audio(screen_name(f))]
    prefetch = json.dumps(["/media/" + n for n in ahead])
    back = queue_url(gid, due)

    prev = (f'Average {fmt(st["average"])} &middot; last 3 {fmt(st["last3"])} &middot; '
            f'{st["graded_count"]} graded &middot; {st["missed"]} missed')
    head = ("<h1>Change a mark</h1>" if regrade else "<h1>Grading queue</h1>")
    hint = ("" if regrade else
            f'<p class="sub"><a href="/queue/grid">Grade a whole task at once</a> '
            f'&middot; keys <span class="kbd">1</span>&ndash;'
            f'<span class="kbd">9</span> <span class="kbd">0</span>=10, hold '
            f'<span class="kbd">Shift</span> for a half, <span class="kbd">Enter</span> '
            f'to save, <span class="kbd">s</span> to skip.</p>')
    # The first page shows the picker so a set can be chosen; every page after
    # that shows only a strip saying which set, so the work stays at the top.
    top = ""
    if not regrade:
        top = ((queue_picker(db, rows, gid, due, pick) if show_picker else "")
               + set_bar(db, rows, inset, gid, due))
    body = f"""{head}
{hint}
{top}
{"" if regrade else undo_strip(db)}
{"" if regrade else waiting_list(db, sub["id"], inset, gid, due)}
<div class="queue">
  <div class="shots">{shots}</div>
  <div class="splitter" role="separator" aria-orientation="vertical"
       title="Drag to make the papers wider or narrower"></div>
  <div class="panel">
    <div class="card">
      <div style="font-weight:600">{E(student["name"])}</div>
      <div class="sub gap-1">{E(group_name(db, student["group_id"]))} &middot;
        {E(assignment["title"]) if assignment else "unassigned"}
        {'<span class="pill risk">late</span>' if sub["late"] else ''}
        {'<span class="pill mute">speaking</span>' if sub["kind"] == "voice" else ''}
        {'<span class="pill mute">resubmission</span>' if sub["improves"] else ''}</div>
      <div class="sub gap-2">{prev}</div>
    </div>
    {attach_card(db, sub, student) if not assignment else ""}
    {grade_form(db, sub, student, assignment, regrade, gid=gid, due=due)}
    {previous_panel(db, sub, student)}
  </div>
</div>
<div id="gradedata" hidden data-skip="{sub["id"]}" data-back="{E(back)}"
     data-name="{E(student["name"])}"
     data-regrade="{1 if regrade else 0}" data-prefetch="{E(prefetch)}"></div>"""
    return html_response(page("Change a mark" if regrade else "Grade", body, "Grade"))


def view_grade_grid(req, db):
    """Everyone's work for one piece of homework, side by side.

    One at a time means a page load between every student, and a page load is
    long enough to lose the thread of what an eight looks like today. Seeing a
    class together is faster and marks more consistently, because the comparison
    is in front of you rather than in your memory.
    """
    core.seed_notes(db)
    want = (req["query"].get("assignment", [""])[0] or "").strip()
    aid = int(want) if want.isdigit() else None

    sets = db.execute(
        "SELECT a.id, a.title, g.name klass, COUNT(*) n FROM submissions s"
        " JOIN assignments a ON a.id=s.assignment_id"
        " JOIN groups g ON g.id=a.group_id"
        " WHERE s.status='pending' AND s.draft=0"
        " GROUP BY a.id ORDER BY g.name, a.title").fetchall()
    loose = db.execute(
        "SELECT COUNT(*) c FROM submissions WHERE status='pending' AND draft=0"
        " AND assignment_id IS NULL").fetchone()["c"]

    if aid is None and sets:
        aid = sets[0]["id"]

    if aid:
        subs = db.execute(
            "SELECT s.*, st.name FROM submissions s JOIN students st ON st.id=s.student_id"
            " WHERE s.status='pending' AND s.draft=0 AND s.assignment_id=?"
            " ORDER BY st.name", (aid,)).fetchall()
    else:
        subs = db.execute(
            "SELECT s.*, st.name FROM submissions s JOIN students st ON st.id=s.student_id"
            " WHERE s.status='pending' AND s.draft=0 AND s.assignment_id IS NULL"
            " ORDER BY st.name").fetchall()

    tabs = "".join(
        f'<a class="tab{" on" if r["id"] == aid else ""}"'
        f' href="/queue/grid?assignment={r["id"]}">{E(r["klass"])} &middot; '
        f'{E(r["title"][:26])} <span class="sub">{r["n"]}</span></a>' for r in sets)
    if loose:
        tabs += (f'<a class="tab{" on" if aid is None else ""}"'
                 f' href="/queue/grid?assignment=0">No homework <span class="sub">'
                 f'{loose}</span></a>')

    assignment = (db.execute("SELECT * FROM assignments WHERE id=?", (aid,)).fetchone()
                  if aid else None)
    rubric = bool(assignment and assignment["rubric"])

    cards = ""
    for sub in subs:
        files = db.execute("SELECT * FROM files WHERE submission_id=? ORDER BY ord, id"
                           " LIMIT 4", (sub["id"],)).fetchall()
        shots = ""
        if sub["kind"] == "text":
            shots = (f'<div class="written short">{E(sub["answer"] or "")}</div>'
                     f'<div class="sub">{sub["words"] or 0} words</div>')
            files = []
        for f in files:
            n = screen_name(f)
            if is_audio(n):
                shots += (f'<audio controls preload="none" class="voice"'
                          f' src="/media/{E(n)}"></audio>')
            else:
                full = (' data-full="/media/%s"' % E(f["filename"])
                        if n != f["filename"] else "")
                shots += (f'<img src="/media/{E(n)}" loading="lazy" alt=""'
                          f' onclick="zoom(this)"{full}>')
        late = '<span class="pill risk">late</span>' if sub["late"] else ""
        cards += f"""<div class="gradecard" data-sub="{sub["id"]}">
  <div class="gchead"><strong>{E(sub["name"])}</strong> {late}</div>
  <div class="gcshots">{shots or '<span class="sub">nothing attached</span>'}</div>
  <input type="hidden" name="score_{sub["id"]}" id="f_score_{sub["id"]}" value="">
  {scorepad("score_%d" % sub["id"], None, small=True)}
  <input class="gcnote" name="note_{sub["id"]}" placeholder="note (optional)">
</div>"""

    head = "<h1>Grade a whole task</h1>"
    if not sets and not loose:
        return html_response(page("Grade", head + '<div class="card"><p>'
                                  'Nothing waiting.</p></div>', "Grade"))
    warn = ('<div class="card paused">This homework is marked on the four criteria, so it'
            ' needs the one-at-a-time page. <a href="/queue">Open the queue</a>.</div>'
            if rubric else "")
    body = f"""{head}
<p class="sub">Everyone's work for one task at a time. Tap a mark under each, then save the
lot &mdash; no page load between students, and you can see what an eight looks like today.
<a href="/queue">One at a time instead</a>.</p>
<div class="tabs">{tabs}</div>
{warn}
<form method="post" action="/grade/many" id="gridform">
<input type="hidden" name="assignment" value="{aid or 0}">
<div class="gradegrid">{cards or '<p class="sub">Nothing waiting for this one.</p>'}</div>
<div class="markbar" style="margin-top:14px;border:0">
  <button>Save the marked ones</button>
  <span class="sub" id="gridcount"></span>
</div></form>"""
    return html_response(page("Grade", body, "Grade"))


def act_grade_many(req, db):
    """Save every mark that was given, leave the rest waiting."""
    f = req["form"]
    done = 0
    graded = []
    for key, values in list(f.items()):
        m = re.match(r"^score_(\d+)$", key)
        if not m or not values or not values[0].strip():
            continue
        sid = int(m.group(1))
        sub = db.execute("SELECT * FROM submissions WHERE id=? AND status='pending'",
                         (sid,)).fetchone()
        if not sub:
            continue
        one = {"score": [values[0]],
               "note": f.get("note_%d" % sid, [""]),
               "tag": []}
        if save_grade(db, sub, one) is None:
            continue
        done += 1
        graded.append(sid)
    if graded:
        # one message after another, on a thread of their own: a whole class
        # marked on the grid kept the page waiting for twenty of them
        notify_later(notify_each, graded)
    back = (f.get("assignment", ["0"])[0] or "0").strip()
    return redirect("/queue/grid?assignment=%s" % back)


def view_queue(req, db):
    """The pile, sorted: by class and by deadline, and marked one set at a
    time when the teacher picks one."""
    core.seed_notes(db)
    gid, due = queue_filter(req["query"])
    p = (req["query"].get("pick", [""])[0] or "").strip()
    pick = int(p) if p.isdigit() else None
    if pick is not None and gid is None and due is None:
        gid = pick                      # the class's own work sits under its lessons
    rows = queue_rows(db)
    inset = in_set(rows, gid, due)
    want = (req["query"].get("id", [""])[0] or "").strip()
    sub = None
    if want.isdigit():
        sub = db.execute(
            "SELECT * FROM submissions WHERE id=? AND status='pending' AND draft=0",
            (int(want),)).fetchone()
    if not sub and inset:
        sub = db.execute("SELECT * FROM submissions WHERE id=?",
                         (inset[0]["id"],)).fetchone()
    if not sub:
        if rows and (gid or due):
            note = ('<div class="card good"><p class="flush"><strong>This set is done.'
                    f'</strong> {len(rows)} other piece{"" if len(rows) == 1 else "s"} '
                    f'still waiting &mdash; pick the next set above, or '
                    f'<a class="linky" href="/queue?all=1">mark everything</a>.</p></div>')
        else:
            note = '<div class="card"><p class="flush">Queue is empty. Nothing to grade.</p></div>'
        body = f"""<h1>Grading queue</h1>
{queue_picker(db, rows, gid, due, pick)}
{undo_strip(db)}
{note}"""
        return html_response(page("Grade", body, "Grade"))
    # the bare address is where a set gets chosen; anything more specific -
    # a set, or "everything" once chosen - is the workspace
    bare = gid is None and due is None and not want.isdigit() \
        and (req["query"].get("all", [""])[0] or "") != "1"
    return grade_page(db, sub, rows=rows, gid=gid, due=due,
                      show_picker=bare or pick is not None, pick=pick)


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
      <div class="sub gap-1">{E(level)} · {len(rows)} students</div></div>
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
            "index": core.overall_index(completion, stats["done_average"], marks["overall"]),
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
    lopts = '<option value="">no level</option>' + "".join(
        f'<option value="{l["id"]}"{" selected" if l["id"] == g["level_id"] else ""}>{E(l["name"])}</option>'
        for l in db.execute("SELECT id, name FROM levels ORDER BY sort"))
    moved = (query.get("level", [""])[0] or "").strip()
    note = (f'<div class="card good gap-2"><strong>{E(g["name"])} is now {E(level or "without a level")}.</strong> '
            f'Its students see the handouts, tests and materials of that level from now on.</div>'
            if moved else "")
    past = ('<div class="card bad gap-2"><strong>That deadline has already passed.</strong> '
            'Nothing was set &mdash; choose a date and time that is still to come.</div>'
            if query.get("pastdue") else "")
    # a class that finishes its book moves up a level; this is where
    change = f"""<details class="adder"><summary>Change level</summary>
<div class="card"><form method="post" action="/groups/{gid}/level" class="inline">
<label class="f">Level<select name="level_id">{lopts}</select></label>
<label class="f pushed">&nbsp;<button>Save</button></label></form>
<p class="sub gap-2">For a class that has finished its book and moved up. Its students
then see the handouts, tests and materials of the new level. Their homework, marks and
league points stay as they are.</p></div></details>"""
    head = (f'<h1>{E(g["name"])}</h1><p class="sub">'
            f'{E(level or "no level")} · join code '
            f'<span class="kbd">{E(g["join_code"])}</span></p>{note}{past}{change}{tabs}')

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
<div class="card"><p>{summary}</p></div>

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
    """Marking a lesson should take a few taps, not fifty-four.

    Three dropdowns a student meant eighteen students cost fifty-four separate
    choices, every lesson. Almost all of them were the same number. So the page
    now starts everyone somewhere sensible - last lesson, or one press of a
    preset - and asks only for the ones who were different.
    """
    cfg = core.load_config()
    day = (query.get("day", [None])[0] or core.local_day(core.now(), cfg))
    existing = core.marks_on(db, g["id"], day)
    previous, prev_day = core.last_marks_before(db, g["id"], day)
    students = db.execute(
        "SELECT * FROM students WHERE group_id=? AND active=1 ORDER BY name", (g["id"],)
    ).fetchall()

    rows = ""
    for st in students:
        row = existing.get(st["id"])
        was = previous.get(st["id"])
        hidden = "".join(
            f'<input type="hidden" name="{f}_{st["id"]}" id="f_{f}_{st["id"]}"'
            f' value="{row[f] if row and row[f] else ""}">' for f in core.MARK_FIELDS)
        pad = "".join(
            f'<button type="button" class="mk" data-sid="{st["id"]}" data-v="{n}">{n}</button>'
            for n in range(1, core.MARK_MAX + 1))
        detail = "".join(
            f'<label class="mdet"><span>{f[:4].title()}</span>'
            + "".join(f'<button type="button" class="mk one" data-sid="{st["id"]}"'
                      f' data-field="{f}" data-v="{n}">{n}</button>'
                      for n in range(1, core.MARK_MAX + 1))
            + "</label>" for f in core.MARK_FIELDS)
        last = (",".join(str(was[f] or "") for f in core.MARK_FIELDS)) if was else ""
        rows += (f'<tr data-sid="{st["id"]}" data-last="{last}">'
                 f'<td class="mname">{E(st["name"])}</td>'
                 f'<td class="markpad">{hidden}{pad}'
                 f'<button type="button" class="mk none" data-sid="{st["id"]}"'
                 f' data-v="">absent</button>'
                 f'<button type="button" class="linky split" data-sid="{st["id"]}">split</button>'
                 f'<div class="mdetails" id="d_{st["id"]}" hidden>{detail}</div></td>'
                 f'<td><input name="note_{st["id"]}" class="mnote"'
                 f' value="{E((row["note"] if row else "") or "")}"'
                 f' placeholder="note"></td></tr>')

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

    presets = "".join(
        f'<button type="button" class="ghost preset" data-all="{n}">Everyone {n}</button>'
        for n in range(core.MARK_MAX, core.MARK_MAX - 3, -1))
    copy_last = (f'<button type="button" class="ghost" id="copylast">Same as '
                 f'{E(prev_day)}</button>' if prev_day else "")

    return f"""<h2>Marks for {E(day)}</h2>
<p class="sub">One tap gives a student all three marks. Start everyone somewhere, then
change only the ones who were different &mdash; <span class="kbd">split</span> opens the
three separately when someone was late but worked well.</p>
<div class="card"><form method="post" action="/groups/{g["id"]}/marks" id="marksform">
<input type="hidden" name="day" value="{E(day)}">
<div class="markbar">{presets}{copy_last}
  <button type="button" class="ghost" id="clearall">Clear</button>
  <span class="sub" id="markcount"></span></div>
<div class="tablewrap"><table id="marks"><tr><th>Student</th>
<th>How were they?</th><th>Note</th></tr>
{rows or '<tr><td colspan=3 class="sub">Nobody in this class yet.</td></tr>'}</table></div>
<div class="inline gap-3">
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
      <div class="sub gap-1">{E(titles)} — last due {E(when)}</div>
    </div>
    <label class="f">New deadline
      <input type="date" name="due" value="{E(core.shift_days(when, 7))}" required
             min="{core.local_day(core.now(), core.load_config())}"></label>
    <label class="f">at
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


def owed_card(db, s):
    """Which of the class's handouts this student has to do: from when they
    joined the class, and less any the teacher lets them off."""
    cfg = core.load_config()
    since = core.student_since(s)
    day = core.local_day(core.parse(since), cfg) if since else ""
    excused = core.excused_tests(db, s["id"])
    rows = db.execute(
        "SELECT a.*, t.title ttitle FROM assignments a JOIN dtests t ON t.id=a.test_id"
        " WHERE a.group_id=? AND a.published=1 AND t.kind='handout'"
        " ORDER BY COALESCE(a.due_at, a.created_at)", (s["group_id"],)).fetchall()
    seen, lines = set(), ""
    for a in rows:
        if a["test_id"] in seen:
            continue
        seen.add(a["test_id"])
        due = core.local_day(core.parse(a["due_at"]), cfg) if a["due_at"] else "no deadline"
        hw = core.handout_homework(db, a, s["id"])
        if a["test_id"] in excused:
            state = '<span class="pill mute">let off</span>'
            act = ("Make them do it", "0")
        elif not core.owes(db, s, a, excused):
            state = '<span class="pill mute">before they joined</span>'
            act = None
        else:
            d = hw["digital"]
            state = ('<span class="pill good">done</span>' if hw["handed"] else
                     f'<span class="pill">{d["parts"]} of {d["total"]} parts</span>' if d["started"] else
                     '<span class="pill risk">not started</span>')
            act = ("Let them off", "1")
        button = (f'<form method="post" action="/students/{s["id"]}/excuse" class="owed-act">'
                  f'<input type="hidden" name="test_id" value="{a["test_id"]}">'
                  f'<input type="hidden" name="on" value="{act[1]}">'
                  f'<button class="ghost">{act[0]}</button></form>') if act else ""
        lines += (f'<tr><td>{E(a["ttitle"])}</td><td class="sub">{E(due)}</td>'
                  f'<td>{state}</td><td>{button}</td></tr>')
    return f"""<h2>Handouts they have to do</h2>
<div class="card owed">
<form method="post" action="/students/{s["id"]}/since" class="inline owed-since">
  <label class="f">Joined this class on<input type="date" name="since" value="{E(day)}"></label>
  <button class="ghost">Save</button>
</form>
<p class="sub flush">Homework whose deadline had passed before this day does not count for them &mdash;
not in the league, not as missed, and its handout does not hold up the next one. Leave it empty
if they have been in the class from the start. A handout you let them off works the same way;
they can still open it and practise.</p>
<div class="tablewrap"><table><tr><th>Handout</th><th>Due</th><th></th><th></th></tr>
{lines or '<tr><td colspan=4 class="sub">No handouts set to this class yet.</td></tr>'}</table></div>
</div>"""


def act_student_since(req, db, sid):
    raw = (req["form"].get("since", [""])[0] or "").strip()
    if raw and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        return redirect(f"/students/{sid}")
    when = core.day_start(raw, core.load_config()) if raw else None
    db.execute("UPDATE students SET group_since=? WHERE id=?", (when, sid))
    db.commit()
    return redirect(f"/students/{sid}")


def act_student_excuse(req, db, sid):
    tid = (req["form"].get("test_id", [""])[0] or "").strip()
    if tid.isdigit():
        core.set_excused(db, sid, int(tid), req["form"].get("on", [""])[0] == "1")
    return redirect(f"/students/{sid}")


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
        elif t.get("handout") and t["status"] == "handout":
            h_ = t["handout"]
            detail = f'digital handout · {h_["parts"]} of {h_["total"]} parts'
            state = (score_pill(t["score"]) if t["score"] is not None
                     else '<span class="pill mute">in progress</span>')
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
{owed_card(db, s)}
<h2>Report for parents</h2>
<div class="card">
<p class="sub gap-0">A read-only page you can send to a parent:
scores, homework, and how they are in class. No password, and nothing they can change.</p>
<div style="display:flex;gap:8px">
  <input id="plink2" readonly value="/p/{E(core.parent_token(db, s['id']))}"
         style="flex:1;font-family:ui-monospace,Menlo,monospace;font-size:13px">
  <button type="button" class="ghost" onclick="copy2()">Copy</button>
  <a class="btnlink" target="_blank" rel="noopener" href="/p/{E(core.parent_token(db, s['id']))}">Open</a>
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
<p class="sub gap-0">Send this to {E(s["name"])} only. It opens their own
upload page — no password, and it shows nobody else's work.</p>
<div style="display:flex;gap:8px">
  <input id="plink" readonly value="/s/{E(core.student_token(db, s['id']))}"
         style="flex:1;font-family:ui-monospace,Menlo,monospace;font-size:13px">
  <button type="button" class="ghost" onclick="copyLink()">Copy</button>
  <a class="btnlink" target="_blank" rel="noopener"
     href="/s/{E(core.student_token(db, s['id']))}">Open their page</a>
</div>
<p class="sub gap-2">It opens in a separate window, so this one stays
where it is &mdash; useful when you are showing the class what they will see.</p>
<form method="post" action="/students/{s['id']}/newlink" class="gap-2"
 onsubmit="return confirm('Give {E(s["name"])} a new link? The old one stops working, and they will need the new one.')">
<button class="ghost">New link</button>
<span class="sub">&nbsp;Use this if the link has been shared with somebody
else. The old one stops working at once.</span></form></div>
<script>
const box = document.getElementById('plink');
box.value = location.origin + box.value;
function copyLink() {{
  box.select(); navigator.clipboard.writeText(box.value);
}}
</script>
<h2>Parent link</h2>
<div class="card">
<p class="sub gap-0">Optional. A parent who taps this gets a weekly
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


def dest_on_site(db):
    """The Destination units on the site: suggested as the box is typed in,
    and listed under it, a tap puts one in."""
    units = []
    for t in db.execute("SELECT title FROM dtests WHERE series='destination' AND kind='handout'"
                        " ORDER BY title"):
        m = re.match(r"(Destination \S+)\s*·\s*Unit (\d+)\s*[—–-]\s*(.*)", t["title"])
        if m:
            units.append(("%s, Unit %s" % (m.group(1), m.group(2)), m.group(3)))
    units = sorted(set(units), key=lambda u: (u[0].split(",")[0], int(u[0].rsplit(" ", 1)[1])))
    if not units:
        return ""
    opts = "".join(f'<option value="{E(v)}">{E(v)} — {E(name)}</option>' for v, name in units)
    taps = "".join(f'<button type="button" class="chip destpick" data-dest="{E(v)}">{E(v)}'
                   f' <span class="sub">{E(name)}</span></button>' for v, name in units)
    return (f'<datalist id="destlist">{opts}</datalist>'
            f'<div class="destsite"><span class="sub">On the site, done there or on paper:</span> {taps}</div>')


def view_assignments(req, db, error="", keep=None):
    groups = db.execute("SELECT * FROM groups WHERE archived=0 ORDER BY name").fetchall()
    keep = keep or {}

    def kept(name, default=""):
        return (keep.get(name, [default])[0] or default) if keep else default
    checked = (lambda name, on=True: " checked" if (kept(name) == "1" if keep else on) else "")
    core.seed_prompts(db)
    sug_levels = "".join(f'<option value="{E(l)}">{E(l)}</option>' for l in core.LEVELS)
    sug_kinds = "".join(f'<option value="{k}">{E(lab)}</option>'
                        for k, lab, _w, _m in core.prompt_kinds())
    opts = "".join(f'<option value="{g["id"]}" data-level="{g["level_id"] or ""}"'
                   f' data-level-name="{E(core.level_name(db, g["level_id"]) or "")}"'
                   f'{" selected" if str(g["id"]) == kept("group_id") else ""}>{E(g["name"])}</option>'
                   for g in groups)
    # every digital handout of the course, under its level, to tick as many as
    # the homework needs; one open only as a class's homework says so. An older
    # version with the same title is left out.
    chosen = set(keep.get("handout", [])) if keep else set()
    shelves = ""
    open_titles = {r["title"] for r in db.execute(
        "SELECT title FROM dtests WHERE kind='handout' AND published=1")}
    for lv in db.execute("SELECT id, name FROM levels ORDER BY sort"):
        books = sorted((b for b in db.execute(
            "SELECT id, number, title, published FROM dtests WHERE kind='handout' AND level_id=?"
            " AND series IS NULL ORDER BY id DESC", (lv["id"],))
            if b["published"] or b["title"] not in open_titles), key=core.lesson_order)
        if books:
            shelves += (f'<fieldset class="hwshelf" data-level="{lv["id"]}"><legend>{E(lv["name"])}</legend>'
                        + "".join(f'<label class="hwbook"><input type="checkbox" name="handout" value="{b["id"]}"'
                                  f'{" checked" if str(b["id"]) in chosen else ""}>'
                                  f'<span>{E(b["title"])}'
                                  f'{"" if b["published"] else " <em>(opens only for this class)</em>"}'
                                  f'</span></label>' for b in books) + "</fieldset>")
    today = core.local_day(core.now(), core.load_config())
    warn = ('<div class="card bad gap-3"><strong>That deadline has already passed.</strong> '
            'Nothing was set: homework with a deadline in the past would close the moment it was '
            'set, students would never see it, and the league would count it as missed. '
            'Everything you typed is still below &mdash; change the date and set it again.</div>'
            if error == "past" else "")
    # the lessons a unit is taught in follow the class's level (core.LESSON_PLANS):
    # Beginner A / B / C, the others in pairs; the page swaps them when the class changes
    first = next((g for g in groups if str(g["id"]) == kept("group_id")), groups[0] if groups else None)
    first_level = core.level_name(db, first["level_id"]) if first else ""
    lessons = core.lessons_for(first_level)
    want = kept("pair", lessons[0][0])
    pairs = "".join(f'<option value="{E(v)}"{" selected" if want == v else ""}>{E(l)}</option>'
                    for v, l, _x in lessons)
    plans_json = E(json.dumps({lv: [[v, l] for v, l, _x in core.lessons_for(lv)]
                               for lv in core.LEVELS + [""]}))
    body = f"""<h1>Set homework</h1>{warn}
<p class="sub">Everything already set is on the <a class="linky" href="/homework">Homework</a>
page, where you see who has done it, change it or delete it.</p>
<form method="post" action="/assignments/list" class="card setform">
<div class="inline">
  <label class="f">Group<select name="group_id">{opts}</select></label>
  <label class="f">Due<input type="date" name="due" min="{today}"></label>
  <label class="f">at<input type="time" name="due_time" value="{E(kept("due_time", "23:59"))}" step="60"></label>
</div>

<div class="unitfill">
  <div class="inline">
    <label class="f">Unit<input type="number" name="unit" id="u_unit" min="1" max="20"
      value="{E(kept("unit"))}" style="width:80px"></label>
    <label class="f">Lessons<select name="pair" id="u_pair" data-plans="{plans_json}">{pairs}</select></label>
    <label class="f">Destination<input name="destination" id="u_dest" value="{E(kept("destination"))}"
      placeholder="e.g. Destination B1, Unit 7" style="width:240px" list="destlist"></label>
  </div>
  {dest_on_site(db)}
  <p class="sub flush" id="u_note">Pick the unit and the lesson: the workbook, the handout (and,
  where the level has them, the review and the unit test) fill in below &mdash; change or delete
  anything before you set it. A Destination unit you type is remembered for next time.</p>
</div>

<div class="f">Digital handouts <span class="sub">&mdash; tick as many as this homework has</span>
<div class="hwshelves" id="hwhandout">{shelves or '<p class="sub flush">None on the site yet.</p>'}</div></div>
<p class="sub flush">Students do each on the site &mdash; it marks itself, half for the parts done
by the deadline, half for the right answers &mdash; or send photos of the paper for your tick,
{core.PAPER_TICK:g} out of 10. The better of the two counts.</p>

<label class="f">Everything else, one per line
<textarea name="items" id="u_items" rows="5" class="wide"
placeholder="Workbook unit 4 A &amp; C&#10;Destination B1, Unit 7&#10;Practice test 3">{E(kept("items"))}</textarea></label>

<details class="gap-2"><summary>Add a writing task they type</summary>
<p class="sub gap-2">Students get a writing paper &mdash; the question on one side, the sheet
on the other &mdash; instead of sending a photo of their handwriting.</p>
<div class="inline gap-2" id="suggestbar">
<label class="f">Level<select id="sug_level">{sug_levels}</select></label>
<label class="f">Unit<select id="sug_unit"><option value="">any unit</option></select></label>
<label class="f">Kind<select id="sug_kind">{sug_kinds}</select></label>
<label class="f pushed">&nbsp;<button type="button" class="ghost"
  id="suggest">Suggest a question</button></label>
<label class="f pushed">&nbsp;<a class="linky" href="/prompts">the question bank</a></label>
</div>
<label class="f">The question
<textarea name="prompt" rows="4" class="wide"
 placeholder="Some people think that… Discuss both views and give your own opinion.">{E(kept("prompt"))}</textarea></label>
<div class="inline gap-2">
<label class="f">At least<input type="number" name="min_words" min="0" max="1000"
 placeholder="250" style="width:90px"> words</label>
<label class="f">Time<input type="number" name="minutes" min="0" max="240"
 placeholder="40" style="width:90px"> minutes</label>
<label class="f">Type<select name="task_type">
<option value="other">Other</option><option value="task2">Task 2</option>
<option value="task1">Task 1</option></select></label>
<label class="f pushed">&nbsp;
<span style="font-size:13px;color:var(--ink)" title="Task response, coherence, vocabulary, grammar">
<input type="checkbox" name="rubric" value="1"{checked("rubric", False)}> mark on the four criteria</span></label>
</div></details>

<div class="setgo">
  <label><input type="checkbox" name="publish" value="1"{checked("publish")}> open to students now</label>
  <label><input type="checkbox" name="announce" value="1"{checked("announce")}> tell them in Telegram</label>
  <button onclick="this.disabled=true;this.form.submit()">Set the homework</button>
</div>
</form>
<p class="sub gap-3">One line makes one piece of homework, several lines make several
&mdash; students pick which one they are sending and each gets its own score. Without
&ldquo;open to students now&rdquo; it is saved as a draft: nobody sees it until you press
Publish on the Homework page.</p>"""
    return html_response(page("Set homework", body, "Set homework"))


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
            f'<td><a href="/students/{s_["id"]}">{E(s_["name"])}</a>{nobot}'
            f' <a class="peek" target="_blank" rel="noopener" title="open their page"'
            f' href="/s/{E(core.student_token(db, s_["id"]))}">&#8599;</a></td>'
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
    # The address only matters when it is missing; when it is known it is a
    # footnote, and when it is not it is the one thing to fix before sharing.
    where_note = (f'<p class="flash warn">The public address has not been detected '
                  f'yet &mdash; open this page once on the real address, or student '
                  f'links will not work.</p>' if not site else "")
    counted = f"{len(people)} shown"
    if site:
        counted += f' &middot; student links use <code>{E(site)}</code>'

    body = f"""<h1>Students</h1>
<p class="sub">{counted}</p>
{where_note}
{tabs}
<div class="toolbar">{states}
<form method="get" action="/roster" class="inline">
<input type="hidden" name="group" value="{gid or ''}">
<input type="hidden" name="show" value="{E(show)}">
<input name="q" id="rq" value="{E(q)}" placeholder="Find a name" aria-label="Find a name">
<button class="ghost">Search</button>
</form></div>
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
<h2>Add a student by hand</h2>
<div class="card"><form method="post" action="/students/new" class="inline">
<label class="f">Name<input name="name" required placeholder="For someone not on Telegram"></label>
<label class="f">Class<select name="group_id">{opts}</select></label>
<label class="f pushed">&nbsp;<button>Add</button></label>
</form>
<p class="sub gap-3">They get their own page link straight away. If they
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
            f'<td>{E(group_name(db, wl["group_id"]))}</td>'
            f'<td>{E(core.level_name(db, wl["level_id"]) or "—")}</td>'
            f'<td>{n}</td><td>{learners}</td>'
            f'<td>{"active" if wl["active"] else "off"}</td></tr>'
        )
    opts = "".join(f'<option value="{g["id"]}">{E(g["name"])}</option>' for g in groups)
    levels = '<option value="">every level</option>' + "".join(
        f'<option value="{l["id"]}">{E(l["name"])}</option>'
        for l in db.execute("SELECT id, name FROM levels ORDER BY sort"))
    body = f"""<h1>Vocabulary</h1>
<p class="sub">Students practise these with <span class="kbd">/vocab</span> in the bot.
Words they get wrong come back the next day; words they know come back later and later.</p>
<div class="card"><form method="post" action="/vocab/new">
<div class="inline" style="margin-bottom:10px">
<label class="f">List title<input name="title" placeholder="Unit 15" required></label>
<label class="f">Book<input name="source" placeholder="4000 Essential Words 1"></label>
<label class="f">Unit<input name="unit" placeholder="15" style="width:80px"></label>
<label class="f">Group<select name="group_id">{opts}</select></label>
<label class="f">Level<select name="level_id">{levels}</select></label>
<label class="f">Section<select name="kind">
<option value="vocab">Vocabulary</option>
<option value="grammar">Grammar &mdash; each line carries its own wrong answers</option>
<option value="exam">Exam words</option>
</select></label></div>
<label class="f">One per line: <code>word = meaning</code>, or
<code>word = meaning | example sentence</code> to unlock fill-the-gap.
For a grammar list: <code>She is ____ than me. = taller | more tall | tallest</code>
<textarea name="words" rows="8" class="wide"
placeholder="abandon = tashlab ketmoq / покидать | They had to abandon the car.&#10;absolute = mutlaq / абсолютный"></textarea></label>
<div class="gap-3"><button>Create list</button></div></form></div>
<div class="tablewrap"><table><tr><th>List</th><th>Group</th><th>Level</th>
<th>Words</th><th>Practising</th><th>Status</th></tr>
{rows or '<tr><td colspan=6 class="sub">No word lists yet.</td></tr>'}</table></div>"""
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
    classes = "".join(
        f'<option value="{g["id"]}"{" selected" if g["id"] == wl["group_id"] else ""}>'
        f'{E(g["name"])}</option>'
        for g in db.execute("SELECT id, name FROM groups WHERE archived=0 ORDER BY name"))
    levels = "".join(
        f'<option value="{l["id"]}"{" selected" if l["id"] == wl["level_id"] else ""}>'
        f'{E(l["name"])}</option>'
        for l in db.execute("SELECT id, name FROM levels ORDER BY sort"))
    kinds = "".join(
        f'<option value="{k}"{" selected" if k == wl["kind"] else ""}>{E(v)}</option>'
        for k, v in KIND_NAME.items())
    also = {x for x in (wl["extra_levels"] or "").split(",") if x}
    extra = "".join(
        f'<label><input type="checkbox" name="extra" value="{l["id"]}"'
        f'{" checked" if str(l["id"]) in also else ""}> {E(l["name"])}</label>'
        for l in db.execute("SELECT id, name FROM levels ORDER BY sort"))
    also_line = ""
    if wl["extra_levels"]:
        names = [core.level_name(db, int(x)) for x in wl["extra_levels"].split(",") if x]
        also_line = " (also " + ", ".join(n for n in names if n) + ")"
    body = f"""<h1>{E(wl["title"])}</h1>
<p class="sub">{E(group_name(db, wl["group_id"]))} ·
{E(core.level_name(db, wl["level_id"]) or "every level")}{also_line} · the “hard” flag marks
words the group answers correctly less than 60% of the time — worth reteaching.</p>
<details class="adder"><summary>Rename, or change the class, level, book or step</summary>
<div class="card"><form method="post" action="/vocab/{wid}/rename" class="inline">
<label class="f grow">Title<input name="title" value="{E(wl["title"])}"
 required class="wide"></label>
<label class="f">Class<select name="group_id">
<option value=""{"" if wl["group_id"] else " selected"}>every class</option>{classes}
</select></label>
<label class="f">Level<select name="level_id">
<option value=""{"" if wl["level_id"] else " selected"}>every level</option>{levels}
</select></label>
<label class="f">Book<input name="source" value="{E(wl["source"] or "")}"
 placeholder="4000 Essential Words 1"></label>
<label class="f">Step<input name="step" type="number" min="0" max="999"
 value="{wl["step"] or 0}" class="tiny"></label>
<label class="f">Section<select name="kind">{kinds}</select></label>
<label class="f">Also show to<span class="alsolevels">{extra}</span></label>
<label class="f pushed">&nbsp;<button>Save</button></label></form></div></details>
<div class="card"><form method="post" action="/vocab/{wid}/add" class="inline">
<label class="f" style="flex:1">Add more words (one per line, <code>word = meaning</code>)
<textarea name="words" rows="3" class="wide"></textarea></label>
<button>Add</button></form></div>
<details class="adder"><summary>Replace every word in this list</summary>
<div class="card"><form method="post" action="/vocab/{wid}/replace">
<label class="f">One per line, <code>word = meaning</code>, or
<code>word = meaning | example sentence</code>. What students already know
about a word is kept as long as the word itself stays on the list.
<textarea name="words" rows="6" class="wide"></textarea></label>
<div class="gap-3"><button>Replace the list</button></div>
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


def parse_questions(text):
    """One question per line, for a grammar list:

        She is ____ than her sister. = taller | more tall | tallest | most tall

    The first answer after the = is the right one; the rest are the wrong
    options, and they travel with the question rather than being borrowed from
    other rows.
    """
    out = []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line or "=" not in line:
            continue
        head, _, rest = line.partition("=")
        parts = [p.strip() for p in rest.split("|")]
        parts = [p for p in parts if p]
        if not head.strip() or len(parts) < 2:
            continue
        out.append((head.strip()[:200], parts[0][:200], parts[1:4]))
    return out


def act_new_word_list(req, db):
    f = req["form"]
    title = (f.get("title", [""])[0] or "").strip()
    gid = f.get("group_id", [None])[0]
    kind = (f.get("kind", ["vocab"])[0] or "vocab")
    kind = kind if kind in ("vocab", "grammar", "exam") else "vocab"
    grammar = kind == "grammar"
    raw = f.get("words", [""])[0]
    pairs = parse_questions(raw) if grammar else parse_words(raw)
    if not title or not pairs:
        return redirect("/vocab")
    lvl = (f.get("level_id", [""])[0] or "").strip()
    wid = db.execute(
        "INSERT INTO word_lists (group_id, title, created_at, source, unit, kind,"
        " level_id) VALUES (?,?,?,?,?,?,?)",
        (int(gid) if gid else None, title, core.iso(core.now()),
         (f.get("source", [""])[0] or "").strip()[:80] or None,
         (f.get("unit", [""])[0] or "").strip()[:40] or None,
         kind, int(lvl) if lvl.isdigit() else None),
    ).lastrowid
    for i, item in enumerate(pairs):
        if grammar:
            term, answer, wrong = item
            db.execute("INSERT INTO words (list_id, term, translation, options, ord)"
                       " VALUES (?,?,?,?,?)",
                       (wid, term, answer, json.dumps(wrong, ensure_ascii=False), i))
        else:
            term, meaning, example = item
            db.execute("INSERT INTO words (list_id, term, translation, example, ord)"
                       " VALUES (?,?,?,?,?)", (wid, term, meaning, example, i))
    db.commit()
    return redirect(f"/vocab/{wid}")


def act_rename_word_list(req, db, wid):
    """A new title, or a different class, without touching the words.

    There was no way to change either once a list existed. A list made under
    the wrong name could only be left as it was or made again - and making it
    again left the first copy standing, because nothing can delete a list,
    with the students' practice still pointing at it.
    """
    wl = db.execute("SELECT id FROM word_lists WHERE id=?", (wid,)).fetchone()
    if not wl:
        return not_found()
    f = req["form"]
    title = (f.get("title", [""])[0] or "").strip()[:160]
    gid = (f.get("group_id", [""])[0] or "").strip()
    if not title:
        return redirect(f"/vocab/{wid}")
    group = int(gid) if gid.isdigit() and db.execute(
        "SELECT 1 FROM groups WHERE id=?", (int(gid),)).fetchone() else None
    lvl = (f.get("level_id", [""])[0] or "").strip()
    level = int(lvl) if lvl.isdigit() and db.execute(
        "SELECT 1 FROM levels WHERE id=?", (int(lvl),)).fetchone() else None
    step = (f.get("step", ["0"])[0] or "0").strip()
    source = (f.get("source", [""])[0] or "").strip()[:80] or None
    kind = (f.get("kind", [""])[0] or "").strip()
    kind = kind if kind in KIND_NAME else None
    valid = {str(r["id"]) for r in db.execute("SELECT id FROM levels")}
    extra = ",".join(sorted(v for v in f.get("extra", []) if v in valid)) or None
    db.execute("UPDATE word_lists SET title=?, group_id=?, level_id=?, source=?,"
               " step=?, kind=COALESCE(?, kind), extra_levels=? WHERE id=?",
               (title, group, level, source,
                int(step) if step.isdigit() and int(step) < 1000 else 0, kind,
                extra, wid))
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


def student_page(title, body, music=True):
    """Standalone layout - no teacher navigation, no sign-in.

    `music` is off for pages a stranger can reach: the song of the day
    belongs to the class, and its filename is nobody else's business.
    """
    bar = ('<span class="right"><span id="songname" class="songname" hidden>'
           '</span><button type="button" id="musicbtn" class="musicbtn"'
           ' onclick="Music.toggle()" title="Music"></button></span>'
           ) if music else ""
    tune = song_tag() if music else ""
    player = f'<script src="/static/music.js?v={STATIC_V}" defer></script>' if music else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{E(title)} · OlimovAzamat</title>
{FAVICON}<link rel="stylesheet" href="/static/style.css?v={STATIC_V}"></head>
<body><header class="top"><div class="bar">
<span class="brand"><span class="mark">O</span>OlimovAzamat</span>
{bar}</div></header>
<main class="portal">{body}</main>
{tune}{player}
{"".join(f'<script src="/static/{js}?v={STATIC_V}" defer></script>'
         for js in ("nav.js", "write.js", "book.js", "shrink.js", "handout.js",
                    "voice.js", "speak.js", "listen.js"))}</body></html>"""


# The student's page in five sections, the way an app on their phone would
# be: a bar of icons along the bottom, and inside a section a small strip of
# its pages. Ten tabs in three rows was a menu; this is a place.
ICONS = {
    "home": '<svg viewBox="0 0 24 24"><path d="M3 11.5 12 4l9 7.5"/><path d="M5.5 10v10h13V10"/>'
            '<path d="M10 20v-6h4v6"/></svg>',
    "learn": '<svg viewBox="0 0 24 24"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5z"/>'
             '<path d="M4 20.5A2.5 2.5 0 0 1 6.5 18H20"/><path d="M8 7h8M8 10.5h6"/></svg>',
    "play": '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M10 8.5v7l5.5-3.5z"/></svg>',
    "progress": '<svg viewBox="0 0 24 24"><path d="M4 20h16"/><path d="M7 16v-5M12 16V6M17 16v-8"/></svg>',
    "profile": '<svg viewBox="0 0 24 24"><circle cx="12" cy="8.5" r="3.5"/>'
               '<path d="M5 20a7 7 0 0 1 14 0"/></svg>',
}
PORTAL = [
    ("home", "Homework", [("home", "Send"), ("write", "Writing"),
                          ("feedback", "Feedback")]),
    ("learn", "Learn", [("materials", "Materials"), ("handouts", "Handouts"),
                        ("tests", "Tests")]),
    ("play", "Play", [("play", "Play"), ("battle", "Battle")]),
    ("progress", "Progress", [("progress", "Scores"), ("class", "Class"),
                              ("goal", "My goal"), ("rate", "Rate")]),
    ("profile", "Me", [("profile", "Profile")]),
]


def student_shell(s, db, token, tab, body, top="", music=True):
    """One page, five sections, everything the bot can do - in the same
    frame as the teacher's: the sections down the left on a laptop, the
    section's pages across the top, and on a phone the bar of five along the
    bottom, where a thumb finds it."""
    level = core.level_name(db, core.level_of(db, s["group_id"]))
    section = next((key for key, _l, pages in PORTAL
                    if any(p == tab for p, _ in pages)), "home")
    base = f"/s/{E(token)}?tab="
    # feedback the student has not opened yet is the one thing that should
    # be impossible to miss: a count on the section, and on its tab
    unseen = core.unseen_feedback(db, s["id"])
    badge = f'<i class="badge">{unseen}</i>' if unseen else ""

    def icon(key):
        return ICONS[key].replace("<svg ", '<svg class="side-ico" aria-hidden="true" ', 1)

    def pages_of(pages):
        return [(base + p, label, p == tab, badge if p == "feedback" else "") for p, label in pages]

    groups = [(label, base + pages[0][0], icon(key), key == section, badge if key == "home" else "",
               pages_of(pages)) for key, label, pages in PORTAL]
    title, pages = next((label, pages) for key, label, pages in PORTAL if key == section)
    initial = E((s["name"] or "?").strip()[:1].upper())
    group = E(group_name(db, s["group_id"])) + (" · " + E(level) if level else "")
    who = (f'<div class="side-who" data-tip="{E(s["name"])}"><span class="avatar">{initial}</span>'
           f'<span class="side-label"><b>{E(s["name"])}</b><small>{group}</small></span></div>')
    bar = "".join(
        f'<a class="{"on" if key == section else ""}" href="{base}{pages_[0][0]}">'
        f'{ICONS[key]}{badge if key == "home" else ""}<span>{label}</span></a>'
        for key, label, pages_ in PORTAL)
    # on a phone the rail is out of sight, so who this is stays on the page
    head = f"""<div class="whoami">
  <div class="avatar">{initial}</div>
  <div>
    <div class="name">{E(s["name"])}</div>
    <div class="sub">{group}</div>
  </div>
</div>"""
    tune = song_tag() if music else ""
    scripts = (["music.js"] if music else []) + [
        "shell.js", "nav.js", "write.js", "book.js", "shrink.js", "handout.js", "listen.js", "voice.js", "speak.js"]
    return html_response(shell(
        s["name"], top + head + body, nav=side_nav(groups), foot=who + (MUSIC_ROW if music else ""),
        heading=title, tabs=top_tabs(title, pages_of(pages)), home=base + "home", role="Student",
        scripts=scripts, main_class="portal", after=f'<nav class="pnav" aria-label="Sections">{bar}</nav>',
        tune=tune, body_class="shell student"))


def portal_home(db, s, token, flash, pick=""):
    st = core.student_stats(db, s["id"])
    # a handout can be sent as photographs of the paper too - worth the tick,
    # half of what the digital one can reach
    opens = [a for a in db.execute(
        "SELECT * FROM assignments WHERE group_id=? AND closed=0 AND published=1"
        " ORDER BY COALESCE(due_at, created_at) DESC, id DESC",
        (s["group_id"],)).fetchall()
        if core.still_open(a["due_at"])]
    if pick.isdigit() and any(str(a["id"]) == pick for a in opens):
        # the handout page's "send photos instead" lands here with it chosen
        opens.sort(key=lambda a: str(a["id"]) != pick)

    def label(a):
        if a["test_id"] and core.is_handout(db, a["test_id"]):
            return "%s — on paper (%g/10)" % (a["title"], core.PAPER_TICK)
        return a["title"]
    if opens:
        opts = "".join(f'<option value="{a["id"]}"{" selected" if str(a["id"]) == pick else ""}>'
                       f'{E(label(a))}</option>' for a in opens)
        picker = (f'<label class="f">Which task?<select name="assignment_id">{opts}</select></label>'
                  if len(opens) > 1 else
                  f'<input type="hidden" name="assignment_id" value="{opens[0]["id"]}">'
                  f'<p class="sub" style="margin:0 0 10px">For: <strong>'
                  f'{E(label(opens[0]))}</strong></p>')
    else:
        picker = '<p class="sub" style="margin:0 0 10px">No open task right now.</p>'

    lists = ""
    for due_at, items in core.open_sets(db, s["group_id"], for_student=True):
        prog = core.set_progress(db, s["id"], items)
        left = core.due_in_words(due_at)
        when = (f'{due_at[:10]} · {left}' if due_at else "no deadline")
        rows = ""
        for a in items:
            if a["id"] in prog.get("excused_ids", ()):
                # set before they joined the class, or they were let off it
                rows += (f'<li class="done"><span class="box">&ndash;</span>{E(a["title"])}'
                         f' <span class="pill mute">not needed</span></li>')
                continue
            done = a["id"] in prog["done_ids"]
            link = ""
            tid = a["test_id"] if "test_id" in a.keys() else None
            if tid and core.is_handout(db, tid):
                # a handout: open it and see how many parts are done - or, sent
                # on paper, where the photographs have got to
                hw = core.handout_homework(db, a, s["id"])
                state, paper = hw["digital"], hw["paper"]
                done = hw["handed"]
                first = None if done else core.handout_blocked_by(db, tid, s)
                here = f'/s/{E(token)}?tab=handouts&amp;h={tid}'
                if paper and not state["done"]:
                    tag = {"waiting": ('', "on paper &middot; sent"),
                           "ticked": (' good', "on paper &#10003; %g/10" % (paper["mark"] or 0)),
                           "late": (' risk', "on paper &middot; late"),
                           "rejected": (' risk', "on paper &#10007; not complete")}[paper["state"]]
                    link = (f' <span class="pill{tag[0]}">{tag[1]}</span>'
                            f' <a class="linky" href="{here}">'
                            f'{"do it here instead" if paper["state"] == "rejected" else "do it here for up to 10"}'
                            f' &rarr;</a>')
                elif state["done"]:
                    link = f' <span class="pill good">{state["mark"]:g} / 10</span>'
                elif first:
                    link = (f' <a class="linky" href="/s/{E(token)}?tab=handouts&amp;h={first["id"]}">'
                            f'finish {E(short_title(first))} first &rarr;</a>')
                else:
                    link = (f' <span class="pill">{state["parts"]}/{state["total"]} parts</span>'
                            f' <a class="linky" href="{here}">'
                            f'{"open it" if not state["started"] else "carry on"} &rarr;</a>')
            elif tid:
                # the handout is on the site, so the homework opens it rather
                # than telling the student to go and find it
                sat = db.execute(
                    "SELECT score, total FROM dattempts WHERE test_id=? AND"
                    " student_id=? AND finished_at IS NOT NULL"
                    " ORDER BY finished_at LIMIT 1", (tid, s["id"])).fetchone()
                done = bool(sat)
                link = (f' <span class="pill good">{sat["score"]} of '
                        f'{sat["total"]}</span>' if sat else
                        f' <a class="linky" href="/s/{E(token)}?tab=tests&amp;'
                        f't={tid}" data-reload>open it &rarr;</a>')
            rows += (f'<li class="{"done" if done else ""}">'
                     f'<span class="box">{"&#10003;" if done else ""}</span>'
                     f'{E(a["title"])}{link}</li>')
        pct = prog["percent"] or 0
        lists += f"""<div class="card">
  <div class="rowline"><strong>{E(when)}</strong>
    <span class="pill{" risk" if pct < 50 else ""}">{prog["done"]}/{prog["total"]}</span></div>
  <div class="pbar"><i style="width:{pct}%"></i></div>
  <ul class="checklist">{rows}</ul></div>"""
    if not lists:
        lists = '<div class="card empty-card"><p>Nothing set at the moment.</p></div>'

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

    unseen = core.unseen_feedback(db, s["id"])
    nudge = ""
    if unseen:
        nudge = (f'<a class="todo urgent fbnudge" href="/s/{E(token)}?tab=feedback">'
                 f'<div class="todo-head">New feedback from your teacher</div>'
                 f'<div class="sub gap-1">{unseen} piece{"" if unseen == 1 else "s"} of '
                 f'homework marked &mdash; see what they said &rarr;</div></a>')
    # a lesson happened today (the teacher marked the room) and this student
    # has not said how it was: ask, once
    cfg = core.load_config()
    today = core.local_day(core.now(), cfg)
    had_lesson = db.execute(
        "SELECT 1 FROM lesson_marks m JOIN students st ON st.id=m.student_id"
        " WHERE st.group_id=? AND m.day=? LIMIT 1", (s["group_id"], today)).fetchone()
    if had_lesson and not core.has_rated(db, s["id"], today):
        nudge += (f'<a class="todo fbnudge" href="/s/{E(token)}?tab=rate">'
                  f'<div class="todo-head">How was today\'s lesson?</div>'
                  f'<div class="sub gap-1">Six stars and thirty seconds. Anonymous '
                  f'&mdash; your teacher never sees who said what &rarr;</div></a>')
    return f"""{flash}{nudge}
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
    <div class="gap-3"><button>Send to teacher</button></div>
  </form>
</div>
{drafts}
<h2>What is left</h2>
{lists}"""


def stars(name):
    """Five stars for one aspect. Reversed in the markup so a plain CSS
    sibling rule can light the ones to the left of the chosen star."""
    out = ""
    for v in (5, 4, 3, 2, 1):
        out += (f'<input type="radio" name="{name}" id="{name}{v}" value="{v}" required>'
                f'<label for="{name}{v}" title="{v} of 5">&#9733;</label>')
    return f'<span class="stars">{out}</span>'


def portal_rate(db, s, token, query):
    """Rate the lesson, anonymously. The form never carries the student's
    name and the rating row never gets it; the page says so, because the
    promise is the point."""
    cfg = core.load_config()
    today = datetime.strptime(core.local_day(core.now(), cfg), "%Y-%m-%d").date()
    flash = ""
    got = (query.get("rated", [""])[0] or "")
    if got == "done":
        flash = ('<div class="card good"><p class="flush"><strong>Thank you.</strong> '
                 'Your rating is in, and nobody - not even your teacher - can see it '
                 'was yours.</p></div>')
    elif got == "already":
        flash = ('<div class="card"><p class="flush">You have already rated that '
                 'lesson. Thank you!</p></div>')
    elif got == "bad":
        flash = ('<div class="card"><p class="flush">Please give every line a star, '
                 'and pick a lesson from the last week.</p></div>')
    days = ""
    for back in range(0, 7):
        d = today - timedelta(days=back)
        key = d.isoformat()
        label = ("Today" if back == 0 else "Yesterday" if back == 1
                 else d.strftime("%A %-d %b"))
        done = core.has_rated(db, s["id"], key)
        days += (f'<option value="{key}"{" disabled" if done else ""}>'
                 f'{label}{" - rated" if done else ""}</option>')
    rows = "".join(
        f'<div class="rate-row"><div><div class="what">{E(label)}</div>'
        f'<div class="sub">{E(hint)}</div></div>{stars(key)}</div>'
        for key, label, hint in core.RATING_ASPECTS)
    summary = ""
    agg = core.lesson_ratings(db, s["group_id"], weeks=4)
    if agg["n"]:
        bars = "".join(
            f'<div class="aspect{" watch" if a["avg"] < 4 else ""}{" risk" if a["avg"] < 3 else ""}">'
            f'<div class="what">{E(a["label"])}</div>'
            f'<div class="track"><div class="fill" style="width:{a["avg"] / 5 * 100:.0f}%"></div></div>'
            f'<div class="n">{a["avg"]:.1f}</div></div>'
            for a in agg["aspects"] if a["avg"] is not None)
        summary = (f'<h2>How your class rated the last few weeks</h2><div class="card">'
                   f'<div class="aspects">{bars}</div><p class="sub gap-3 flush">'
                   f'{agg["n"]} ratings from your class in the last 4 weeks.</p></div>')
    return f"""<h2>Rate the lesson</h2>
{flash}
<div class="anon"><span class="lock">&#128274;</span><div><strong>Anonymous.</strong>
Your name is not saved with your answers, and your teacher only sees a class's
ratings once at least {core.MIN_RATERS} classmates have rated that week - never who
wrote what. Say what you really think; that is what makes lessons better.</div></div>
<div class="card gap-3"><form method="post" action="/s/{E(token)}/rate">
<label class="f">Which lesson?<select name="day">{days}</select></label>
<p class="sub gap-3">Five stars is "yes, completely"; one star is "not at all".</p>
{rows}
<label class="f gap-3">What was good? Keep doing it. (optional)
<textarea name="keep" rows="2" maxlength="300" placeholder="e.g. the group work, the examples on the board"></textarea></label>
<label class="f gap-2">What would you change? (optional)
<textarea name="change" rows="2" maxlength="300" placeholder="e.g. more time to speak, slower on the grammar"></textarea></label>
<div class="gap-3"><button>Send anonymously</button></div>
</form></div>
{summary}"""


def act_rate_lesson(req, db, token):
    s = core.student_by_token(db, token)
    if not s:
        return redirect(f"/s/{token}")
    f = req["form"]
    scores = {k: (f.get(k, [""])[0] or "") for k, _l, _h in core.RATING_ASPECTS}
    out = core.rate_lesson(db, s, (f.get("day", [""])[0] or "").strip(), scores,
                           keep=f.get("keep", [""])[0], change=f.get("change", [""])[0])
    return redirect(f"/s/{token}?tab=rate&rated={out}")


def portal_feedback(db, s, token):
    """What the teacher said about each piece of work, newest first, with
    the ones not yet opened marked as new. Opening the page is what marks
    them read - there is nothing to press."""
    rows = core.feedback_rows(db, s["id"])
    spoken = core.speak_feedback_for(db, s["id"])
    fresh = [r for r in rows if not r["seen"]] + [f for f in spoken if not f["seen"]]
    core.mark_feedback_seen(db, s["id"])
    if spoken:
        db.execute("UPDATE speak_feedback SET seen=1 WHERE seen=0 AND attempt_id IN"
                   " (SELECT id FROM dattempts WHERE student_id=?)", (s["id"],))
        db.commit()
    speak_cards = ""
    for f in spoken:
        v = core.speak_value(f["given"])
        mine = (f'<div class="fb-voice"><span class="sub">Your recording:</span><audio controls preload="none"'
                f' src="/s/{E(token)}/speak/{E(v["file"])}"></audio></div>' if v and not v["cant"] else "")
        note = f'<blockquote class="fb-note">{E(f["note"])}</blockquote>' if f["note"] else ""
        voice = (f'<div class="fb-voice"><span class="sub">Your teacher says:</span><audio controls preload="metadata"'
                 f' src="/s/{E(token)}/speakfb/{f["attempt_id"]}/{f["question_id"]}"></audio></div>'
                 if f["voice"] else "")
        speak_cards += f"""<div class="card fb{" new" if not f["seen"] else ""}">
  <div class="fb-head"><div><div class="fb-title">{MIC_SVG.replace('<svg', '<svg class="fb-mic"', 1)} Speaking · {E(f["title"])}</div>
    <div class="sub">{E((f["updated_at"] or "")[:10])} · task {E((f["prompt"] or "").split("  ")[0])}{' &middot; <span class="pill">new</span>' if not f["seen"] else ''}</div></div></div>
  {note}{voice}{mine}
</div>"""
    if not rows and speak_cards:
        return f"<h2>Feedback</h2><p class=\"sub\">What your teacher said about your recordings.</p>{speak_cards}"
    if not rows:
        return ('<h2>Feedback</h2><div class="card empty-card"><p class="flush">Nothing marked yet. '
                'When your teacher marks a piece of homework, what they said about it '
                'appears here.</p></div>')
    cards = ""
    for r in rows:
        when = (r["graded_at"] or "")[:10]
        tags = "".join(f'<span class="pill mute">{E(t)}</span>' for t in r["tags"])
        note = (f'<blockquote class="fb-note">{E(r["note"])}</blockquote>' if r["note"] else "")
        voice = (f'<div class="fb-voice"><span class="sub">Your teacher says:</span>'
                 f'<audio controls preload="metadata" '
                 f'src="/s/{E(token)}/voice/{r["id"]}"></audio></div>'
                 if r["voice"] else "")
        nothing = ("" if (r["note"] or r["tags"] or r["voice"]) else
                   '<p class="sub flush">Marked, with nothing to add.</p>')
        cards += f"""<div class="card fb{" new" if not r["seen"] else ""}">
  <div class="fb-head">
    <div><div class="fb-title">{E(r["title"] or "Homework")}</div>
      <div class="sub">{E(when)}{' &middot; <span class="pill">new</span>' if not r["seen"] else ''}</div></div>
    {score_pill(r["score"])}
  </div>
  {note}{voice}
  {f'<div class="fb-tags">{tags}</div>' if tags else ''}{nothing}
</div>"""
    head = (f'<p class="sub">{len(fresh)} new since you last looked.</p>' if fresh
            else '<p class="sub">Everything your teacher has said about your work.</p>')
    return f"<h2>Feedback</h2>{head}{speak_cards}{cards}"


def portal_materials(db, s, token, query):
    level_id = core.level_of(db, s["group_id"])
    if not level_id:
        return ('<div class="card empty-card"><p>Your class has no level yet. '
                'Ask your teacher.</p></div>')
    coll = (query.get("c", [None])[0] or "")
    sect = query.get("s", [None])[0]
    unit = query.get("u", [None])[0]
    sect = int(sect) if sect and sect.isdigit() else None
    unit = int(unit) if unit and unit.isdigit() else None
    base = f"/s/{E(token)}?tab=materials"

    def n_files(n):
        return "Empty" if not n else "%d file%s" % (n, "" if n == 1 else "s")

    def steps(*bits):
        """Where you are on the shelves, each step a way back up."""
        sep = '<span class="crumb-sep" aria-hidden="true">›</span>'
        out = [f'<a href="{href}">{E(label)}</a>' for label, href in bits[:-1]]
        out.append(f'<span class="here">{E(bits[-1][0])}</span>')
        return '<nav class="crumbs">' + sep.join(out) + "</nav>"

    top = ("Materials", base)
    if coll not in core.COLLECTIONS:
        counts = core.collection_counts(db, level_id)
        cards = "".join(
            shelf_card(f"{base}&amp;c={key}", E(core.collection_label(key)), n_files(counts.get(key, 0)),
                       *COLLECTION_LOOKS.get(key, ("folder", "plum")), empty=not counts.get(key))
            for key in core.COLLECTION_ORDER)
        return f'<h2>Materials</h2>{shelf_grid(cards)}'

    shelf = (core.collection_label(coll), f"{base}&amp;c={coll}")

    # the practice shelf is twenty buttons, and each holds a whole test - the
    # paper, its recording and its answers, so nothing has to be cross-referred
    if core.is_test_shelf(coll):
        have = core.units_across(db, level_id, coll)
        if unit is None:
            cards = "".join(
                shelf_card(f"{base}&amp;c={coll}&amp;u={n}", f"Test {n}", n_files(have.get(n, 0)),
                           "clipboard", "amber", empty=n not in have, small=True)
                for n in core.tests_in_collection(coll))
            return steps(top, shelf) + shelf_grid(cards, small=True)
        rows = core.files_in_test(db, level_id, coll, unit)
        order = {name: i for i, name in enumerate(core.sections(coll))}
        rows = sorted(rows, key=lambda m: (order.get(m["category"], 99), m["title"]))
        return steps(top, shelf, (f"Test {unit}", "")) + student_files(rows, token, show_cat=True)

    names = core.sections(coll)
    if query.get("audio") and sect is None:
        counts = core.level_counts(db, level_id, coll)
        cards = ""
        for label, section in (("Class book", "Listening audios"), ("Work book", "Workbook audios")):
            if section in names:
                cards += shelf_card(f"{base}&amp;c={coll}&amp;s={names.index(section)}", label,
                                    n_files(counts.get(section, 0)), *SECTION_LOOKS[section],
                                    empty=not counts.get(section))
        return steps(top, shelf, ("Listening audios", "")) + shelf_grid(cards)
    if sect is None:
        counts = core.level_counts(db, level_id, coll)
        cards = ""
        for i, name in enumerate(names):
            if name == "Workbook audios":
                continue                     # reached through Listening audios
            if name == "Listening audios":
                total = counts.get(name, 0) + counts.get("Workbook audios", 0)
                cards += shelf_card(f"{base}&amp;c={coll}&amp;audio=1", E(name), n_files(total),
                                    *SECTION_LOOKS[name], empty=not total)
                continue
            cards += shelf_card(f"{base}&amp;c={coll}&amp;s={i}", E(name), n_files(counts.get(name, 0)),
                                *SECTION_LOOKS.get(name, ("folder", "plum")), empty=not counts.get(name))
        return steps(top, shelf) + shelf_grid(cards)

    if not 0 <= sect < len(names):
        return steps(top, shelf)
    category = names[sect]
    place = (category, f"{base}&amp;c={coll}&amp;s={sect}")
    units = core.units_in(db, level_id, coll, category)

    if units and unit is None:
        numbers = core.units_for_level(db, level_id)
        if 0 in units:
            numbers = [0] + numbers
        icon, tone = SECTION_LOOKS.get(category, ("folder", "plum"))
        cards = "".join(
            shelf_card(f"{base}&amp;c={coll}&amp;s={sect}&amp;u={n}", "Welcome" if n == 0 else "Unit %d" % n,
                       n_files(units.get(n, 0)), tone=tone, badge=("W" if n == 0 else str(n)),
                       empty=n not in units, small=True)
            for n in numbers)
        return steps(top, shelf, place) + shelf_grid(cards, small=True)

    if unit is not None:
        mats = core.materials_in_unit(db, level_id, coll, category, unit)
        trail = steps(top, shelf, place, ("Welcome" if unit == 0 else "Unit %d" % unit, ""))
    else:
        mats = core.materials_at_level(db, level_id, coll, category)
        trail = steps(top, shelf, (category, ""))
    return trail + student_files(mats, token)


def student_files(mats, token, show_cat=False):
    """A shelf's files for a student: a recording plays in its own row, with
    the same player as the booklets; anything else opens with a tap."""
    if not mats:
        return ('<div class="empty-state">' + look_icon("folder", "empty-ico")
                + '<p><strong>Nothing here yet.</strong><br>Your teacher has not put anything on this shelf.</p></div>')
    rows = ""
    for m in mats:
        label, icon, tone = file_kind(m["original_name"] or m["filename"])
        src = f'/materials/{m["id"]}/file?s={E(token)}'
        meta = " · ".join(x for x in ((m["category"] if show_cat else ""), core.human_size(m["size"])) if x)
        note = f'<span class="f-note">{E(m["note"])}</span>' if m["note"] else ""
        if label == "Audio" or (m["mime"] or "").startswith("audio"):
            rows += (f'<li class="frow listen"><div class="lx" data-src="{src}" data-track="{E(m["title"])}"'
                     f' data-label="{E(m["title"])}">'
                     f'<button type="button" class="lx-play" aria-label="Play {E(m["title"])}">{PLAY_ICON}</button>'
                     f'<div class="lx-mid"><span class="lx-row"><span class="lx-label">{E(m["title"])}</span>'
                     f'<span class="lx-time">{E(meta)}</span></span>'
                     f'<span class="lx-bar" role="slider" tabindex="0" aria-label="Where in the recording"'
                     f' aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"><i></i></span>{note}</div>'
                     f'<button type="button" class="lx-back" aria-label="Back 5 seconds">'
                     f'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5V2L7 6l5 4V7a5 5 0 1 1-5 5H5'
                     f'a7 7 0 1 0 7-7z"/></svg><b>5</b></button></div></li>')
            continue
        rows += (f'<li class="frow"><span class="f-ico t-{tone}" title="{label}"><svg viewBox="0 0 24 24"'
                 f' aria-hidden="true">{LOOK_ICONS[icon]}</svg></span>'
                 f'<span class="f-main"><a class="f-name" href="{src}">{E(m["title"])}</a>'
                 f'<span class="f-meta">{E(label)} · {E(meta)}</span>{note}</span>'
                 f'<a class="f-open" href="{src}" aria-label="Open {E(m["title"])}">'
                 f'<svg viewBox="0 0 24 24" aria-hidden="true">{LOOK_ICONS["chevron"]}</svg></a></li>')
    return f'<div class="files view"><ul class="filelist">{rows}</ul></div>'


BLANK_AT = re.compile(r'<input class="bk-blank" data-q="(\d+)"')
# The booklets say which track a listening section needs - "this is track
# 10.02" - and the coursebook names its files the same way, so the player can
# be put in the right place without anybody typing a filename. A booklet
# retold in Uzbek says "bu 3.18-trek"; a listening in several recordings says
# "09.03–09.05-treklar" or "10.10 va 10.13-treklar"; and a few write
# "track 4.8" for 4.08.
_T = r"\d{1,2}\.\d{1,2}"
TRACK_AT = re.compile(
    r"tracks?\s*(?P<a>%s)(?:\s*(?:[–—-]|to)\s*(?P<b>%s)|\s*(?:and|&)\s*(?P<c>%s))?(?!\d)"
    r"|(?P<a2>%s)(?:\s*[–—]\s*(?P<b2>%s)|\s+va\s+(?P<c2>%s))?\s*-\s*trek" % ((_T,) * 6), re.I)
PARA = re.compile(r"<p\b[^>]*>.*?</p>", re.S)
PLAY_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true"><path class="lx-pl" d="M8 5.5v13l10.5-6.5z"/>' \
            '<path class="lx-pa" d="M7 5h3.6v14H7zM13.4 5H17v14h-3.6z"/></svg>'


def named_tracks(text):
    """Every (unit, number) a piece of text names as a track, in order: a
    range "09.03–09.05" is all three, "10.10 va 10.13" the two."""
    out = []
    for m in TRACK_AT.finditer(text):
        first = m.group("a") or m.group("a2")
        upto = m.group("b") or m.group("b2")
        also = m.group("c") or m.group("c2")
        u1, n1 = (int(x) for x in first.split("."))
        out.append((u1, n1))
        if upto:
            u2, n2 = (int(x) for x in upto.split("."))
            if u2 == u1 and n1 < n2 <= n1 + 12:
                out += [(u1, k) for k in range(n1 + 1, n2 + 1)]
            else:
                out.append((u2, n2))
        if also:
            out.append(tuple(int(x) for x in also.split(".")))
    return out


# Where a booklet names the wrong recording, checked against the coursebook's
# audio scripts: the track it names, and the ones its questions are really
# about. An empty list keeps the button off - 9A&B gives the people in the
# recording Uzbek names, so the recording would not match its questions.
TRACK_FIXES = {
    "Unit 3A & 3C — Money": {(3, 3): [(3, 2), (3, 3)]},          # the interview is 3.02, the lines 3.03
    "Unit 3B & 3D — Money": {(3, 11): [(3, 7)]},                 # Daniel on 'Ways of Life'
    "Unit 4B & 4D — Celebrations": {(4, 8): [(4, 6)]},          # Mike and Harry in Tokyo
    "Unit 9A & 9B — Clothes and shopping": {(9, 3): [], (9, 4): [], (9, 5): []},
}


def shelf_track(level, unit, num):
    """The name a track has on its level's shelf - uploads have used both
    4.08 and 04.08 - or None when it has not been put there."""
    for name in ("%d.%02d" % (unit, num), "%02d.%02d" % (unit, num)):
        if os.path.isfile(os.path.join(core.AUDIO_DIR, level, name + ".mp3")):
            return name
    return None


def add_players(html, level, who="", title=None):
    """Put a Listen button after the paragraph that names a track.

    Word splits a run wherever it likes, so "track 10.02" arrives as
    "track 1" in one span and "0.02" in the next, and a regex over the markup
    finds nothing. The paragraph's text is read with the tags taken out, and
    the button is added after the paragraph that mentions it. A track that is
    not on the site gets no button - the booklet already says the teacher will
    read the script - and the teacher, looking through, is told it is missing.
    """
    if not level:
        return html
    seen = set()
    fixes = TRACK_FIXES.get(title, {})

    def after(m):
        block = m.group(0)
        text = re.sub(r"<[^>]+>", "", block)
        found = []
        for unit, num in (t for named in named_tracks(text) for t in fixes.get(named, [named])):
            if (unit, num) not in seen:
                seen.add((unit, num))
                found.append((unit, num))
        players = ""
        for unit, num in found:
            shown = "%d.%02d" % (unit, num)
            name = shelf_track(level, unit, num)
            if not name:
                if not who:
                    players += ('<p class="lx-missing">Track %s is not on the site yet, so students '
                                'see no Listen button here.</p>' % shown)
                continue
            src = "/audio/%s/%s.mp3%s" % (urllib.parse.quote(level), name,
                                          "?s=" + urllib.parse.quote(who) if who else "")
            players += ('<div class="lx" data-src="%s" data-track="%s">'
                        '<button type="button" class="lx-play" aria-label="Play track %s">%s</button>'
                        '<div class="lx-mid"><span class="lx-row"><span class="lx-label">%s</span><span class="lx-time"></span></span>'
                        '<span class="lx-bar" role="slider" tabindex="0" aria-label="Where in the recording"'
                        ' aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"><i></i></span></div>'
                        '<button type="button" class="lx-back" aria-label="Back 5 seconds">'
                        '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5V2L7 6l5 4V7a5 5 0 1 1-5 5H5'
                        'a7 7 0 1 0 7-7z"/></svg><b>5</b></button></div>'
                        % (E(src), shown, shown, PLAY_ICON, "Listen · " + shown if len(found) > 1 else "Listen"))
        return block + players

    return PARA.sub(after, html)


MCQ_AT = re.compile(r'<span data-mcq="(\d+)"></span>')
LONG_AT = re.compile(r'<span data-long="(\d+)"></span>')


def fill_choices(layout, qs, given=None, marks=None):
    """Turn the markers in an exam layout into real controls.

    A Cambridge paper is answered by choosing A, B or C, not by typing the
    letter, so the layout carries a marker where each set of options goes and
    the radio buttons are put in here - where the question's own id, the
    student's own answer and the marking are all known.
    """
    by_num = {q["num"]: (q, o) for q, o in qs}

    def choices(m):
        got = by_num.get(int(m.group(1)))
        if not got:
            return ""
        q, opts = got
        mine = (given or {}).get(q["id"])
        shown = ""
        for o in opts:
            state = ""
            if marks is not None:
                if o["letter"] == q["answer"]:
                    state = " right"
                elif o["letter"] == mine:
                    state = " wrong"
            checked = " checked" if mine == o["letter"] else ""
            lock = " disabled" if marks is not None else ""
            shown += (f'<label class="exopt{state}">'
                      f'<input type="radio" name="q{q["id"]}"'
                      f' value="{E(o["letter"])}"{checked}{lock}>'
                      f'<b>{E(o["letter"])}</b>'
                      f'{" " + E(o["text"]) if o["text"] else ""}</label>')
        return f'<span class="exopts">{shown}</span>'

    def long_box(m):
        got = by_num.get(int(m.group(1)))
        if not got:
            return ""
        q, _o = got
        mine = (given or {}).get(q["id"]) or ""
        lock = " readonly" if marks is not None else ""
        return (f'<textarea class="exwrite" name="q{q["id"]}" rows="12"'
                f' placeholder="Write your email here."{lock}>{E(mine)}</textarea>')

    return LONG_AT.sub(long_box, MCQ_AT.sub(choices, layout))


# ------------------------------------------------------- handouts on a phone
#
# A handout is drawn for A4 and done on a phone. The layer below keeps the
# paper's design and changes only how each box is answered: a gap in a
# sentence stays in the sentence, a sentence of the student's own is a box
# that grows as they write, a choice is a row of chips to tap, a tick is a
# tick. Two-column exercises get their reading order back on a narrow
# screen, and every exercise gets an anchor so the page can be navigated.

BOOKLET_TEAL = core.BOOKLET_TEAL  # the booklets' own colour: section bars, exercise numbers
SECTION_AT = core.SECTION_AT
EXERCISE_AT = re.compile(
    r'<p((?: [a-z-]+="[^"]*")*)>(<span style="font-weight:700;color:#' + BOOKLET_TEAL
    + r';[^"]*">(\d+\.\d+)\s*</span>)')
INNER_TABLE_AT = re.compile(r'<table class="bk">((?:(?!<table).)*?)</table>', re.S)
ITEM_NO_AT = re.compile(r'data-item="[^":]+:(\d+)"')
CONTROL_AT = re.compile(r'<input class="bk-blank" data-q="(\d+)"([^>]*)>')
BOX_WIDTH_AT = re.compile(r'width:\s*([\d.]+)(px|%)')
PLACEHOLDER_AT = re.compile(r'placeholder="[^"]*"')


def _plain(fragment):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def _word_box(inner):
    """A box of words to choose from - "Complete with a word from the box" -
    is a row of short coloured cells. Stacked one to a line on a phone it
    becomes a tall column of single words; marked, it wraps like a sentence."""
    cells = re.findall(r"<td([^>]*)>(.*?)</td>", inner, re.S)
    words = [_plain(c) for _a, c in cells]
    if (len(cells) < 3 or not all(words) or max(map(len, words)) > 32
            or "bk-blank" in inner or "data-item" in inner):
        return None
    ground = [re.search(r"background:(#[0-9A-Fa-f]{6})", a) for a, _c in cells]
    if not all(ground) or len({g.group(1) for g in ground}) != 1:
        return None
    return '<table class="bk bk-wordbox" style="background:%s">%s</table>' % (ground[0].group(1), inner)


def _column_order(m):
    """Mark a two-column exercise whose items run down the columns, so a
    phone can stack them 1, 2, 3, 4 rather than 1, 3, 2, 4."""
    inner = m.group(1)
    box = _word_box(inner)
    if box:
        return box
    rows = [re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)
            for r in re.findall(r"<tr>(.*?)</tr>", inner, re.S)]
    if len(rows) < 2 or len(rows[0]) < 2 or any(len(r) != len(rows[0]) for r in rows):
        return m.group(0)
    grid = []
    for row in rows:
        line = []
        for cell in row:
            if not _plain(cell):
                line.append(None)
                continue
            n = ITEM_NO_AT.search(cell)
            if not n:
                return m.group(0)            # a table of text, not of items
            line.append(int(n.group(1)))
        grid.append(line)
    down = [row[c] for c in range(len(grid[0])) for row in grid if row[c] is not None]
    across = [n for row in grid for n in row if n is not None]
    if down != sorted(down) or len(set(down)) != len(down) or down == across:
        return m.group(0)
    return '<table class="bk bk-colgrid">%s</table>' % inner


def handout_controls(layout, qs, given=None, marks=None):
    """The handout's boxes as the controls a phone can use, plus the
    sections and exercises the page can jump to."""
    by_num = {q["num"]: (q, o) for q, o in qs}
    sections, exercises, seen = [], [], set()

    def section(m):
        sections.append((m.group(2), html.unescape(m.group(3)).strip()))
        return '<table class="bk bk-sec" id="sec-%s">%s' % (m.group(2), m.group(1))

    def exercise(m):
        label = m.group(3)
        if label in seen:
            return m.group(0)
        seen.add(label)
        end = m.string.find("</p>", m.end())
        what = _plain(m.string[m.end():end])[:60]
        exercises.append((label, what))
        return '<p id="ex-%s"%s>%s' % (label.replace(".", "-"), m.group(1) or "", m.group(2))

    def control(m):
        got = by_num.get(int(m.group(1)))
        if not got:
            return m.group(0)
        q, opts = got
        num, rest = m.group(1), m.group(2)
        mine = (given or {}).get(q["id"]) or ""
        mark = marks.get(q["id"]) if marks is not None else None
        lock = marks is not None
        kind = q["control"] if "control" in q.keys() else None
        if opts:
            chips = ""
            for o in opts:
                value, label = o["letter"], (o["text"] or o["letter"])
                on = mine == value
                state = (" right" if mark == 1 else " wrong") if (on and mark is not None) else ""
                if lock and mark == 0 and core.answer_matches(value, q["answer"]):
                    state += " is-key"           # the one they should have tapped
                chips += (f'<label class="bk-chip{state}"><input type="radio" '
                          f'name="q{q["id"]}" value="{E(value)}"{" checked" if on else ""}'
                          # a partner's answer, tapped in class: it may stay empty at home
                          f'{" data-optional" if kind in OPTIONAL_BOXES else ""}'
                          f'{" disabled" if lock else ""}><span>{E(label)}</span></label>')
            return f'<span class="bk-chips" data-q="{num}" role="radiogroup">{chips}</span>'
        if kind == "record":
            return speak_box(q, num, mine, lock)
        if kind == "tick":
            on = bool(mine.strip())
            return (f'<button type="button" class="bk-tick{" on" if on else ""}" '
                    f'data-q="{num}" aria-pressed="{"true" if on else "false"}" '
                    f'aria-label="Tick"{" disabled" if lock else ""}>&#10003;</button>'
                    f'<input type="hidden" name="q{q["id"]}" value="{E(mine)}" data-q="{num}">')
        w = BOX_WIDTH_AT.search(rest)
        wide = w and (w.group(2) == "%" or float(w.group(1)) >= 180)
        if kind == "pair" and "placeholder=" not in rest:
            rest += ' placeholder="in class"'     # says why it may stay empty
        if kind == "pair" and not wide:
            # done in class with a partner: a gap that may stay empty at home
            return f'<input class="bk-blank" data-q="{num}"{rest} data-optional enterkeyhint="next">'
        if kind in ("long", "tickfill", "essay", "note", "pair") or (wide and kind != "number"):
            state = " right" if mark == 1 else " wrong" if mark == 0 else ""
            hint = PLACEHOLDER_AT.search(rest)
            fill = (f'<button type="button" class="bk-tickfill" data-q="{num}">'
                    f'&#10003; It is correct</button>'
                    if kind == "tickfill" and not lock else "")
            if kind == "essay":          # a piece of writing: room to write, and a word count
                fill = f'<span class="bk-words" data-q="{num}" aria-live="polite"></span>'
            if lock and mark == 0:
                fill = f'<p class="bk-key">Answer: {E(hx_key(q["answer"]))}</p>'
            elif lock and mark is None and mine.strip():
                state = " teacher"
            short = (f' data-min-words="{core.WRITING_MIN_WORDS}"'
                     if core.is_writing(q) and not lock else "")
            return (f'<textarea class="bk-blank bk-long{" bk-essay" if kind == "essay" else ""}{state}" '
                    f'name="q{q["id"]}" data-q="{num}" rows="{4 if kind == "essay" else 1}" spellcheck="true"'
                    f'{short}{" data-optional" if kind in ("note", "pair") else ""}'
                    f'{" " + hint.group(0) if hint else ""}'
                    f'{" readonly" if lock else ""}>{E(mine)}</textarea>{fill}')
        if kind == "number":
            rest += ' inputmode="numeric" pattern="[0-9]*"'
        # a gap in a sentence stays in the sentence; fill_layout names it
        return f'<input class="bk-blank" data-q="{num}"{rest} enterkeyhint="next">'

    layout = SECTION_AT.sub(section, layout)
    layout = EXERCISE_AT.sub(exercise, layout)
    layout = INNER_TABLE_AT.sub(_column_order, layout)
    layout = CONTROL_AT.sub(control, layout)
    return layout, sections, exercises


def jump_menu(sections, exercises):
    """Every exercise, under its section, for the Go to… menu."""
    names = dict(sections)
    groups, order = {}, []
    for label, what in exercises:
        sec = label.split(".")[0]
        if sec not in groups:
            groups[sec] = []
            order.append(sec)
        groups[sec].append(f'<option value="ex-{label.replace(".", "-")}">'
                           f'{E(label)} &middot; {E(what)}</option>')
    out = ""
    for sec in order:
        title = names.get(sec, "")
        out += (f'<optgroup label="{E(sec + " " + title if title else "Section " + sec)}">'
                + "".join(groups[sec]) + "</optgroup>")
    return f'<select class="bk-jump" id="bkjump" aria-label="Go to an exercise"><option value="">Go to&hellip;</option>{out}</select>'


# ------------------------------------------------ a handout in five parts
#
# The booklet has five sections - Reading, Grammar, Vocabulary, Listening,
# Writing - and the phone shows one at a time. Every box in a part is
# answered, the part is checked once, the student sees how it went, and only
# then does the next part open; at the end, each part and the whole. What the
# paper explains - the reading text, the grammar and warning boxes, the
# tables - is redrawn in the site's own colours; the exercises keep the
# booklet's look, which the students already know.

# a tick, a correction to a sentence that was already right, and work done in
# class with a partner may all rightly stay empty: none of them holds a part back
OPTIONAL_BOXES = ("tick", "note", "pair")
MIC_SVG = ('<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="9" y="3" width="6" height="11" rx="3"/>'
           '<path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21M8.5 21h7"/></svg>')


def speak_box(q, num, mine, lock):
    """A speaking task's recorder: record, hear it back, and it is sent to the
    teacher. It counts as answered with a recording of at least
    SPEAK_MIN_SECONDS - or when the student says they cannot record. The
    page's sheet carries the addresses (speak.js reads them), since the box
    itself does not know whose page it is on."""
    v = core.speak_value(mine)
    have = bool(v and not v["cant"])
    cant = bool(v and v["cant"])
    need = core.SPEAK_MIN_SECONDS
    need_txt = "%d:%02d" % (need // 60, need % 60)
    secs = v["seconds"] if have else 0
    controls = ""
    if not lock:
        controls = (f'<div class="bk-rec-row"><button type="button" class="bk-rec-go"><i class="dot"></i>'
                    f'<span>{"Record again" if have else "Start recording"}</span></button>'
                    f'<span class="rec-vu" hidden><i></i></span>'
                    f'<span class="bk-rec-clock">0:00</span><span class="bk-rec-need">/ at least {need_txt}</span>'
                    f'<select class="mic-pick" hidden aria-label="Which microphone"></select></div>'
                    f'<p class="rec-say" aria-live="polite"></p>')
    file_attr = ' data-file="%s"' % E(v["file"]) if have else ""
    return (f'<div class="bk-rec{" has" if have else ""}{" locked" if lock else ""}" data-q="{num}"'
            f' data-qid="{q["id"]}" data-min="{need}"{file_attr}>'
            f'<div class="bk-rec-head"><span class="bk-rec-mic">{MIC_SVG}</span>'
            f'<span><b>Record your answer here</b><small>At least {need_txt} · it goes straight to your teacher'
            f'</small></span></div>{controls}'
            f'<div class="bk-rec-have"{"" if have else " hidden"}><audio controls preload="metadata"></audio>'
            f'<span class="bk-rec-len">{secs // 60}:{secs % 60:02d} · sent to your teacher ✓</span></div>'
            f'<p class="bk-rec-cantmsg"{"" if cant else " hidden"}>You told your teacher you can\'t record.'
            + ('' if lock else ' <button type="button" class="linky bk-rec-try">Try again</button>') + '</p>'
            + ('' if lock or have else
               f'<button type="button" class="linky bk-rec-cant"{" hidden" if cant else ""}>I can\'t record</button>')
            + f'<!--speakfb:{q["id"]}-->'
            f'<input type="hidden" name="q{q["id"]}" value="{E(mine)}" data-q="{num}" data-required></div>')


def speak_feedback_html(db, token, attempt_id, qid):
    """The teacher's answer to a recording, where the student made it."""
    f = db.execute("SELECT * FROM speak_feedback WHERE attempt_id=? AND question_id=?",
                   (attempt_id, qid)).fetchone()
    if not f:
        return ""
    note = f'<blockquote class="fb-note">{E(f["note"])}</blockquote>' if f["note"] else ""
    voice = (f'<audio controls preload="metadata" src="/s/{E(token)}/speakfb/{attempt_id}/{qid}"></audio>'
             if f["voice"] else "")
    return f'<div class="bk-rec-fb"><span class="hx-label">Your teacher says</span>{note}{voice}</div>'

BOOKLET_DEEP = "0B5456"          # the booklets' dark teal: a rule's name, DECIDE / OFFER
BOOKLET_RUST = "C0745F"          # the booklets' warning boxes
BOOKLET_HEAD = "E8F1F1"          # the header row of a booklet table
STYLE_ATTR = "style" + '="'      # the patterns below read the booklet's own styles
PANEL_AT = re.compile(
    r'<table class="bk"><tr><td ' + STYLE_ATTR + r'[^"]*background:#[0-9A-Fa-f]{6}[^"]*">'
    r'<table class="bk"><tr><td ' + STYLE_ATTR + r'[^"]*background:#([0-9A-Fa-f]{6})[^"]*">(.*?)</td></tr></table>'
    r'((?:(?!<table|</td></tr></table>).)*)</td></tr></table>', re.S)
RULE_LEAD_AT = re.compile(r'^<span ' + STYLE_ATTR + r'[^"]*font-weight:700;color:#' + BOOKLET_DEEP
                          + r'[^"]*">([^<]+)</span>')
SPAN_AT = re.compile(r'<span ' + STYLE_ATTR + r'([^"]*)">([^<]*)</span>')
EX_HEAD_AT = re.compile(r'font-weight:700;color:#' + BOOKLET_TEAL + r';[^"]*">\d+\.\d+')
SMALL_WORDS = {"a", "an", "the", "and", "or", "of", "in", "on", "at", "to", "for", "by", "with"}
HX_ICON = {
    "learn": '<path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5z"/><path d="M4 20.5A2.5 2.5 0 0 0 6.5 23H20v-5"/>',
    "warn": '<path d="M12 3 2 21h20z"/><path d="M12 10v5"/><path d="M12 18h.01"/>',
    "sound": '<path d="M4 10v4"/><path d="M8 7v10"/><path d="M12 4v16"/><path d="M16 8v8"/><path d="M20 11v2"/>',
    "listen": '<path d="M3 14v-2a9 9 0 0 1 18 0v2"/><path d="M3 14h4v6H3z"/><path d="M17 14h4v6h-4z"/>',
    "check": '<path d="M4 12l5 5L20 6"/>',
    "words": '<path d="M3 12V4h8l10 10-8 8z"/><path d="M7.5 7.5h.01"/>',
    "text": '<path d="M4 5h16v11H8l-4 4z"/>',
    "read": '<path d="M2 5h7a3 3 0 0 1 3 3v12a2 2 0 0 0-2-2H2z"/><path d="M22 5h-7a3 3 0 0 0-3 3v12a2 2 0 0 1 2-2h8z"/>',
}


def hx_icon(kind):
    return ('<svg class="hx-ico" viewBox="0 0 24 24" aria-hidden="true" fill="none" '
            'stroke="currentColor" stroke-width="2" stroke-linecap="round" '
            'stroke-linejoin="round">%s</svg>' % HX_ICON.get(kind, HX_ICON["learn"]))


def _title_case(text):
    """ONE DAY, ONE CITY -> One Day, One City. Sentence case would lower a
    name; title case keeps it."""
    if not text.isupper():
        return text
    words = text.lower().split(" ")
    return " ".join(w if (i and w in SMALL_WORDS) else w[:1].upper() + w[1:]
                    for i, w in enumerate(words))


def _hx_style(m):
    """Keep bold and italic; let the colours and sizes come from the site."""
    keep = [d.strip() for d in m.group(3).split(";")
            if d.strip().startswith(("font-weight", "font-style"))]
    return "<%s%s%s>" % (m.group(1), m.group(2), (" %s%s\"" % (STYLE_ATTR, ";".join(keep))) if keep else "")


def _hx_plainer(fragment):
    fragment = re.sub(r'<p class="sp"[^>]*></p>', "", fragment)
    fragment = re.sub(r' data-item="[^"]*"', "", fragment)
    return re.sub(r'<(p|span)([^>]*?) ' + STYLE_ATTR + r'([^"]*)"([^>]*)>',
                  lambda m: _hx_style(m).rstrip(">") + m.group(4) + ">", fragment)


def _hx_marks(fragment):
    """✗ and ✓ in the text drawn as the marks they are."""
    def text(m):
        t = m.group(1).replace("✗", '<span class="hx-no">✗</span>')
        t = t.replace("✓", '<span class="hx-yes">✓</span>')
        return ">" + t + "<"
    return re.sub(r">([^<]*[✗✓][^<]*)<", text, fragment)


def _hx_panel(m):
    colour, head, body = m.group(1).upper(), m.group(2), m.group(3)
    title = _plain(head)
    t = title.upper()
    if colour == BOOKLET_RUST:
        kind = "warn"
    elif t.startswith("CHECK") or "TEKSHIR" in t:
        kind = "check"
    elif "KEY WORD" in t or "KALIT SO" in t:
        kind = "words"
    elif any(w in t for w in ("PRONUNCIATION", "HEAR", "TALAFFUZ", "ESHIT")):
        kind = "sound"
    elif "LISTEN" in t or "TINGLA" in t:
        kind = "listen"
    elif "bk-blank" in body or re.match(r"(TWO EMAILS|REPLIES|A MESSAGE|AT THE |MODEL)", t):
        kind = "text"
    else:
        kind = "learn"
    paras = []
    for pm in re.finditer(r"<p([^>]*)>(.*?)</p>", body, re.S):
        attrs, inner = pm.group(1), pm.group(2)
        if 'class="sp"' in attrs or not (_plain(inner) or "<input" in inner):
            continue
        lead = RULE_LEAD_AT.match(inner)
        num = re.match(r'^(<span[^>]*>)(\d+)\s+', inner)
        cls = ""
        if lead:
            inner = ('<span class="hx-tag">%s</span><span class="hx-rule-text">%s</span>'
                     % (lead.group(1).strip(), _hx_plainer(inner[lead.end():])))
            cls = "hx-rule"
        else:
            if num and kind in ("warn", "learn", "sound"):
                inner = ('<span class="hx-num">%s</span>%s' % (num.group(2), num.group(1))
                         + inner[num.end():])
                cls = "hx-item"
            elif "padding-left" in attrs:
                cls = "hx-sub"
            inner = _hx_plainer(inner)
        paras.append('<p%s>%s</p>' % (' class="%s"' % cls if cls else "", inner))
    body = "".join(paras)
    if kind in ("warn", "learn", "sound"):
        body = _hx_marks(body)
    return ('<section class="hx-card hx-%s"><header class="hx-head">%s'
            '<span class="hx-label">%s</span></header><div class="hx-body">%s</div></section>'
            % (kind, hx_icon(kind), E(title), body))


def _top_nodes(fragment):
    """The top-level paragraphs and tables of a stretch of booklet, in order."""
    out, i, n = [], 0, len(fragment)
    start_at = re.compile(r"<(p|table|section|article|div)\b")
    while i < n:
        m = start_at.search(fragment, i)
        if not m:
            out.append(("text", fragment[i:]))
            break
        if m.start() > i:
            out.append(("text", fragment[i:m.start()]))
        name, depth, j = m.group(1), 0, n
        for t in re.finditer(r"<(/?)%s\b[^>]*>" % name, fragment[m.start():]):
            depth += -1 if t.group(1) else 1
            if depth == 0:
                j = m.start() + t.end()
                break
        out.append((name, fragment[m.start():j]))
        i = j
    return out


def _is_prose(node):
    kind, frag = node
    return (kind == "p" and "bk-blank" not in frag and "data-q=" not in frag
            and not EX_HEAD_AT.search(frag) and "{{box" not in frag
            and 'class="hx-uz"' not in frag)       # an instruction in Uzbek is not prose


def _hx_article(paras):
    """A run of plain paragraphs - the reading text - as an article."""
    paras = [p for p in paras if _plain(p)]
    title = stand = ""
    first = _plain(paras[0])
    spans = re.findall(SPAN_AT, paras[0])
    if len(first) < 90 and spans and all("font-weight:700" in st for st, tx in spans if tx.strip()):
        title = _title_case(first)
        paras = paras[1:]
    spans = re.findall(SPAN_AT, paras[0]) if paras else []
    if spans and all("italic" in st for st, tx in spans if tx.strip()):
        stand = _plain(paras[0])
        paras = paras[1:]
    words = sum(len(_plain(p).split()) for p in paras)
    body = ""
    for p in paras:
        inner = re.sub(r"^<p[^>]*>|</p>$", "", p)
        lead = re.match(r'^<span ' + STYLE_ATTR + r'[^"]*font-weight:700[^"]*">([^<]+)</span>', inner)
        if lead:
            inner = '<strong class="hx-lead">%s</strong>%s' % (lead.group(1).strip(),
                                                                _hx_plainer(inner[lead.end():]))
        else:
            inner = _hx_plainer(inner)
        body += "<p>%s</p>" % inner
    minutes = max(1, round(words / 150))
    return ('<article class="hx-read"><div class="hx-read-meta">%s<span class="hx-label">Reading</span>'
            '<span class="hx-read-len">%d words &middot; about %d min</span></div>%s%s'
            '<div class="hx-read-body">%s</div></article>'
            % (hx_icon("read"), words, minutes,
               '<h3 class="hx-read-title">%s</h3>' % E(title) if title else "",
               '<p class="hx-stand">%s</p>' % E(stand) if stand else "", body))


def _hx_table(frag):
    """A booklet table of examples, header row shaded, as one of the site's."""
    rows = re.findall(r"<tr>(.*?)</tr>", frag, re.S)
    if (len(rows) < 2 or "bk-blank" in frag or "data-q=" in frag or "{{box" in frag
            or frag.count("<table") > 1):
        return None
    head = re.findall(r'<td ' + STYLE_ATTR + r'([^"]*)"', rows[0])
    if not head or not all("#" + BOOKLET_HEAD in st.upper() for st in head):
        return None
    names = [_plain(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", rows[0], re.S)]
    out = ""
    for k, row in enumerate(rows):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
        if k == 0:
            out += "<tr>%s</tr>" % "".join("<th>%s</th>" % _hx_plainer(c) for c in cells)
            continue
        # each cell carries its column's name, so a phone can show a row as a block
        out += "<tr>%s</tr>" % "".join(
            '<td%s>%s</td>' % (' data-label="%s"' % E(names[i]) if i < len(names) and names[i] else "",
                               _hx_plainer(c)) for i, c in enumerate(cells))
    return '<div class="hx-scroll"><table class="hx-table hx-wide">%s</table></div>' % out


def hx_dress(fragment):
    """The paper's explanations in the site's clothes: boxes become cards,
    the reading text an article, tables of examples the site's tables."""
    fragment = PANEL_AT.sub(_hx_panel, fragment)
    nodes, out, run = _top_nodes(fragment), [], []

    def flush():
        prose = [f for k, f in run if k == "p" and _plain(f)]
        if len(prose) >= 3 and sum(len(_plain(f)) for f in prose) >= 350:
            out.append(_hx_article(prose))
        else:
            out.extend(f for _k, f in run)
        run.clear()
    for node in nodes:
        if _is_prose(node) or (node[0] == "text" and not node[1].strip() and run):
            run.append(node)
            continue
        flush()
        if node[0] == "table":
            out.append(_hx_table(node[1]) or node[1])
        else:
            out.append(node[1])
    flush()
    return "".join(out)


# the parts of a handout are worked out in core, where the league needs them too
handout_parts = core.handout_parts
part_keys = core.part_keys


def handout_cover(intro, t, level):
    """What the booklet's first page says about itself: its name, its two
    lessons, and what the student will be able to do."""
    tops = [f for k, f in _top_nodes(intro) if k == "p" and _plain(f)]
    name = _plain(tops[1]) if len(tops) > 1 else t["title"]
    sub = ""
    if len(tops) > 2:
        first = re.search(r"<span[^>]*>([^<]*)</span>", tops[2])
        sub = html.unescape(first.group(1)).strip() if first else _plain(tops[2])
    goals = []
    at = intro.find("You will learn to")
    if at > 0:
        for g in re.finditer(r"<p[^>]*>(.*?)</p>", intro[at:], re.S):
            text = g.group(1)
            if _plain(text).startswith("—"):
                text = re.sub(r"^<span[^>]*>—\s*</span>", "", text)
                goals.append(_hx_plainer(text))
    kicker = "Unit %s · %s" % (t["number"], level) if t["number"] else level
    return name, sub, kicker, goals


def hx_ring(right, marked, cls="hx-ring"):
    share = round(100 * right / marked) if marked else 0
    return (f'<svg class="{cls}" viewBox="0 0 36 36" aria-hidden="true">'
            f'<circle class="hx-ring-bg" cx="18" cy="18" r="15.9" pathLength="100"/>'
            f'<circle class="hx-ring-fg" cx="18" cy="18" r="15.9" pathLength="100"'
            f' stroke-dasharray="{share} 100"/></svg>')


def hx_key(answer):
    first = (answer or "").split("/")[0].strip()
    return "it was right as it was" if first == "✓" else first


def fill_layout(layout, qs, given=None, marks=None, level=None, who="", title=None):
    """Put the student's own boxes into the booklet's blanks.

    The booklet was rendered with `data-q="7"` where its seventh blank is, so
    the page is joined to the database by that number and nothing has to be
    guessed from the text around it.
    """
    by_num = {q["num"]: q for q, _o in qs}

    def box(m):
        q = by_num.get(int(m.group(1)))
        if not q:
            return m.group(0)
        val = (given or {}).get(q["id"])
        cls = "bk-blank"
        if marks is not None:
            got = marks.get(q["id"])
            cls += " right" if got == 1 else " wrong" if got == 0 else ""
        attr = (f' value="{E(val)}"' if val else "")
        ro = " readonly" if marks is not None else ""
        return (f'<input class="{cls}" name="q{q["id"]}"{attr}{ro}'
                f' data-q="{m.group(1)}"')

    filled = fill_choices(BLANK_AT.sub(box, layout), qs, given, marks)
    return add_players(filled, level, who, title)


def portal_handouts(db, s, token, query):
    """The booklets, as pages a student works through on their phone.

    A handout is not a test. There is no clock, nothing is handed in, and
    nobody is given a mark for it. What the student types is kept, so they
    can close the page on the bus and pick it up again at home, and so the
    teacher can see what they wrote.
    """
    base = f"/s/{E(token)}?tab=handouts"
    hid = query.get("h", [None])[0]
    hid = int(hid) if hid and hid.isdigit() else None

    if hid is None:
        return handout_shelf_page(db, s, token, base)

    t = db.execute("SELECT * FROM dtests WHERE id=? AND IFNULL(kind,'test')='handout'",
                   (hid,)).fetchone()
    if not t or not core.handout_open_to(db, hid, s["group_id"]):
        return '<h2>Handouts</h2><p class="sub">That booklet is not open.</p>'
    first = core.handout_blocked_by(db, hid, s)
    if first:
        return handout_shut(db, s, token, t, first)
    if not (t["layout"] if "layout" in t.keys() else None):
        return '<h2>Handouts</h2><p class="sub">That booklet has no pages.</p>'
    qs = core.test_questions(db, hid)
    attempt = db.execute(
        "SELECT * FROM dattempts WHERE test_id=? AND student_id=?"
        " ORDER BY id DESC LIMIT 1", (hid, s["id"])).fetchone()
    if not attempt:
        aid = core.start_attempt(db, hid, s["id"])
        attempt = db.execute("SELECT * FROM dattempts WHERE id=?",
                             (aid,)).fetchone()
    return handout_view(db, token, t, qs, attempt, query)


def handout_shelf_page(db, s, token, base):
    """The student's booklets: the one to carry on with at the top, then every
    booklet as a card that says how far they are - a bar of its parts, the
    homework deadline when it is set, the score when it is done - and the
    locked ones saying which booklet opens them. (A handout set as homework to
    this class opens for it even when it is not open to everyone as practice;
    they come in the order of the course, each one after a set booklet shut
    until that is finished.)"""
    shelf = core.handout_shelf(db, s)
    if not shelf:
        return ('<h2>Handouts</h2><div class="empty-state">' + look_icon("book", "empty-ico")
                + '<p><strong>Nothing here yet.</strong><br>Your teacher will put your booklets on this page.</p></div>')
    cfg = core.load_config()
    due = {}
    for r in db.execute("SELECT test_id, due_at FROM assignments WHERE group_id=? AND published=1"
                        " AND test_id IS NOT NULL", (s["group_id"],)):
        if r["due_at"] and (r["test_id"] not in due or r["due_at"] > due[r["test_id"]]):
            due[r["test_id"]] = r["due_at"]
    cards, carry, finished, total = "", None, 0, 0
    for b, first in shelf:
        total += 1
        badge = str(b["number"]) if b["number"] else (short_title(b)[:2] or "·")
        if first:
            cards += (f'<div class="hs-card shut" aria-disabled="true"><span class="hs-badge" title="Unit">{E(badge)}</span>'
                      f'<span class="hs-body"><span class="hs-name">{E(b["title"])}</span>'
                      f'<span class="hs-state">{LOCK_SVG}Opens when you finish {E(short_title(first))}</span></span></div>')
            continue
        layout = db.execute("SELECT layout FROM dtests WHERE id=?", (b["id"],)).fetchone()["layout"] or ""
        _intro, parts = handout_parts(layout)
        att = db.execute("SELECT id FROM dattempts WHERE test_id=? AND student_id=?"
                         " ORDER BY id DESC LIMIT 1", (b["id"], s["id"])).fetchone()
        done = core.handout_parts_done(db, att["id"]) if att else {}
        left = [p for p in parts if p[0] not in done]
        n_parts = max(len(parts), 1)
        pct = round(100 * len(done) / n_parts)
        homework = ""
        if b["id"] in due:
            day, rel = due_words(due[b["id"]], cfg)
            late = rel.endswith("ago") or rel == "yesterday"
            homework = (f'<span class="hs-pill{" late" if late else ""}">Homework · '
                        f'{"was due" if late else "due"} {E(rel)}</span>')
        if not done:
            state = f"{len(parts)} parts · not started"
            cls = "new"
        elif left:
            state = f"Part {len(done) + 1} of {len(parts)} next: {E(left[0][1])}"
            cls = "going"
        else:
            right = sum(r["right_n"] for r in done.values())
            marked = sum(r["right_n"] + r["wrong_n"] for r in done.values())
            state = f'{look_icon("check", "hs-done")}Finished · {right} of {marked} right'
            cls = "done"
            finished += 1
        if left and (carry is None or (b["id"] in due and carry[0]["id"] not in due)):
            carry = (b, left[0], len(done), len(parts), b["id"] in due)
        cards += (f'<a class="hs-card {cls}" href="{base}&amp;h={b["id"]}"><span class="hs-badge">{E(badge)}</span>'
                  f'<span class="hs-body"><span class="hs-name">{E(b["title"])}</span>{homework}'
                  f'<span class="hs-bar" role="img" aria-label="{len(done)} of {len(parts)} parts checked">'
                  f'<i style="width:{pct}%"></i></span><span class="hs-state">{state}</span></span></a>')
    hero = ""
    if carry:
        b, part, n_done, n_parts, is_hw = carry
        pct = round(100 * n_done / max(n_parts, 1))
        hero = (f'<a class="hs-next" href="{base}&amp;h={b["id"]}">'
                f'<span class="hs-next-k">{"Homework · " if is_hw else ""}{"Carry on" if n_done else "Start"}</span>'
                f'<span class="hs-next-t">{E(b["title"])}</span>'
                f'<span class="hs-next-p">Part {n_done + 1} of {n_parts} · {E(part[1])}</span>'
                f'<span class="hs-bar light"><i style="width:{pct}%"></i></span>'
                f'<span class="hs-next-go">{"Carry on" if n_done else "Open it"}'
                f'<svg viewBox="0 0 24 24" aria-hidden="true">{LOOK_ICONS["arrow"]}</svg></span></a>')
    return (f'<h2>Handouts</h2>{hero}'
            f'<p class="hs-sum"><strong>{finished} of {total}</strong> finished · one part at a time, nothing is timed,'
            f' and what you write is saved as you go.</p>'
            f'<div class="hs-shelf">{cards}</div>'
            f'<details class="hs-how"><summary>How handouts work</summary><p>Answer every box in a part and check it:'
            f' you see how you did straight away, and the next part opens. A booklet set as homework has to be'
            f' finished before the next one opens.</p></details>')


def short_title(t):
    """'Unit 12A & 12C' out of 'Unit 12A & 12C — Travel'."""
    return re.split(r"\s+[—–-]\s+", t["title"] or "", maxsplit=1)[0]


def handout_shut(db, s, token, t, first):
    """A booklet that opens only once an earlier one is finished: say which,
    and how far the student is with it."""
    state = core.handout_status(db, first["id"], s["id"])
    go = f"/s/{E(token)}?tab=handouts&amp;h={first['id']}"
    far = (f"You have checked {state['parts']} of its {state['total']} parts."
           if state["parts"] else f"It has {state['total']} parts, and you have not started it yet.")
    return f"""<h2>Handouts</h2>
<div class="card hx-shut">
  <p class="hx-shut-lock">{LOCK_SVG}</p>
  <h3>{E(t["title"])} is not open yet</h3>
  <p>Finish <strong>{E(first["title"])}</strong> first. {far}
  A booklet set as homework has to be finished before the ones after it open.</p>
  <p class="flush"><a class="btn" href="{go}">Open {E(short_title(first))} &rarr;</a></p>
</div>"""


def handout_where(parts, done, want):
    """Which part to show: the one asked for if it is open, else the first
    not yet checked, else the results. A part is open once every part before
    it has been checked - there is no skipping ahead."""
    order = [n for n, *_rest in parts]
    current = next((n for n in order if n not in done), None)
    if want == "end" and current is None:
        return "end", current
    if want.isdigit() and int(want) in order and (int(want) in done or int(want) == current):
        return int(want), current
    return (current if current is not None else "end"), current


LOCK_SVG = ('<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor"'
            ' stroke-width="2.2" stroke-linecap="round"><rect x="5" y="11" width="14" height="10" rx="2"/>'
            '<path d="M8 11V8a4 4 0 0 1 8 0v3"/></svg>')


def handout_view(db, token, t, qs, attempt, query):
    hid = t["id"]
    base = f"/s/{E(token)}?tab=handouts"
    here = f"{base}&amp;h={hid}"
    level = core.level_name(db, t["level_id"]) or ""
    intro, parts = handout_parts(t["layout"])
    done = core.handout_parts_done(db, attempt["id"])
    view, current = handout_where(parts, done, query.get("part", [""])[0])
    name, sub, kicker, goals = handout_cover(intro, t, level)
    given = {r["question_id"]: r["given"] for r in db.execute(
        "SELECT * FROM dresponses WHERE attempt_id=?", (attempt["id"],))}

    steps = ""
    for n, pname, _what, _m in parts:
        if n in done:
            state, dot = "done", "&#10003;"
        elif n == current:
            state, dot = "now", str(n)
        else:
            state, dot = "locked", LOCK_SVG
        mark = " here" if n == view else ""
        now = ' aria-current="step"' if mark else ""
        label = (f'<span class="hx-step-dot">{dot}</span>'
                 f'<span class="hx-step-name">{E(pname)}</span>')
        steps += (f'<li class="hx-step {state}{mark}" aria-disabled="true">{label}</li>'
                  if state == "locked" else
                  f'<li class="hx-step {state}{mark}"><a href="{here}&amp;part={n}"'
                  f'{now}>{label}</a></li>')
    finished = current is None
    end_label = ('<span class="hx-step-dot">&#9733;</span><span class="hx-step-name">Results</span>')
    steps += (f'<li class="hx-step done{" here" if view == "end" else ""}">'
              f'<a href="{here}&amp;part=end">{end_label}</a></li>' if finished else
              f'<li class="hx-step locked" aria-disabled="true">{end_label}</li>')
    # the cover is shown in full before the first part is checked and on the
    # results; every other part gets a strip, so the work is near the top
    slim = "" if (view == "end" or not done) else " slim"
    hero = f"""<p class="sub"><a class="crumb" href="{base}">Handouts</a> &rsaquo; {E(t["title"])}</p>
{homework_strip(db, t, attempt)}
<header class="hx-hero{slim}">
  <p class="hx-kicker">{E(kicker)}</p>
  <h1 class="hx-title">{E(name)}</h1>
  {f'<p class="hx-sub">{E(sub)}</p>' if sub else ""}
  <ol class="hx-steps">{steps}</ol>
</header>"""
    uzbek = 'data-lang="uz"' in t["layout"][:200]
    goals_head = (("Nimalarni mashq qildingiz" if view == "end" else "Bu qoʻllanmada oʻrganasiz")
                  if uzbek else
                  ("What you practised" if view == "end" else "In this handout you will learn to"))
    goals_card = (f'<section class="hx-goals"><h2 class="hx-label">{goals_head}</h2>'
                  f'<ul>{"".join(f"<li>{g}</li>" for g in goals)}</ul></section>' if goals else "")

    if view == "end":
        return hero + handout_results(parts, done, here, name) + goals_card

    idx = [n for n, *_r in parts].index(view)
    n, pname, what, markup = parts[idx]
    nums = set(part_keys(markup))
    pqs = [(q, o) for q, o in qs if q["num"] in nums]
    locked = n in done
    marks = None
    if locked:
        marks = {r["question_id"]: r["correct"] for r in db.execute(
            "SELECT question_id, correct FROM dresponses WHERE attempt_id=?", (attempt["id"],))}
    layout = '<div class="booklet">' + hx_dress(markup) + "</div>"
    layout, _secs, exercises = handout_controls(layout, pqs, given, marks)
    filled = fill_layout(layout, pqs, given, marks, level=audio_shelf(t, level), who=token,
                         title=t["title"])
    if locked:
        answer = {str(q["id"]): q["answer"] for q, _o in pqs}
        filled = re.sub(r'(<input class="bk-blank wrong" name="q(\d+)"[^>]*>)',
                        lambda m: m.group(1) + '<span class="bk-key">%s</span>'
                        % E(hx_key(answer.get(m.group(2)))), filled)
    head = (f'<div class="hx-parthead"><p class="hx-partno">Part {idx + 1} of {len(parts)}</p>'
            f'<h2>{E(pname)}</h2>{f"<p>{E(what)}</p>" if what else ""}</div>')
    filled = re.sub(r"<!--speakfb:(\d+)-->",
                    lambda m: speak_feedback_html(db, token, attempt["id"], int(m.group(1))), filled)
    sheet = (f'<div class="booksheet handout hx-sheet" data-speak="/s/{E(token)}/handout/{hid}/speak"'
             f' data-speakfile="/s/{E(token)}/speak/">{filled}</div>')
    if locked:
        after = parts[idx + 1] if idx + 1 < len(parts) else None
        if after:
            onward = (f'<a class="btn hx-go" href="{here}&amp;part={after[0]}">'
                      f'Next: {E(after[1])} &rsaquo;</a>')
        else:
            onward = f'<a class="btn hx-go" href="{here}&amp;part=end">See your results &rsaquo;</a>'
        r = done[n]
        return (hero + head + part_result(pname, r, onward) + sheet
                + f'<div class="hx-bottom">{onward}</div>')
    total = sum(1 for q, _o in pqs
                if (q["control"] if "control" in q.keys() else None) not in OPTIONAL_BOXES)
    # the button has to share a phone's width with two others
    check_label = f"Check {pname}" if len(pname) <= 11 else f"Check part {idx + 1}"
    return hero + (goals_card if idx == 0 else "") + head + sheet + f"""
<div class="savebar" id="savebar">
  <div class="sb-prog" aria-hidden="true"><i id="sbfill"></i></div>
  {jump_menu([(str(n), pname)], exercises)}
  <button type="button" class="ghost sb-next" id="sbnext"
          title="Go to the next empty box"><span id="sbcount">0 of {total}</span> &rsaquo;</button>
  <button type="button" class="checkbtn" id="checkbtn" data-label="{E(check_label)}">{E(check_label)}</button>
  <div class="sb-notes"><span id="savenote">Saved as you type</span>
    <span id="marknote" class="marknote">Answer every box, then check this part to open the next.</span></div>
</div>
<div id="handoutdata" hidden data-save="/s/{E(token)}/handout/{hid}/save"
     data-check="/s/{E(token)}/handout/{hid}/check" data-part="{n}"></div>"""


def homework_strip(db, t, attempt):
    """A handout set as homework says so: when it is due and what it is worth
    so far - half for the parts checked in time, half for the right answers."""
    st = db.execute("SELECT group_id FROM students WHERE id=?", (attempt["student_id"],)).fetchone()
    a = db.execute("SELECT * FROM assignments WHERE test_id=? AND group_id=? AND published=1"
                   " ORDER BY due_at IS NULL, due_at DESC LIMIT 1",
                   (t["id"], st["group_id"] if st else None)).fetchone()
    if not a:
        return ""
    state = core.handout_status(db, t["id"], attempt["student_id"], a["due_at"])
    cfg = core.load_config()
    when, rel = due_words(a["due_at"], cfg) if a["due_at"] else ("no deadline", "")
    open_now = core.still_open(a["due_at"])
    tail = (f"{state['parts']} of {state['total']} parts done in time &middot; "
            f"<strong>{state['mark']:g}</strong> out of 10 so far" if state["started"] else
            f"Not started &middot; {state['total']} parts")
    late = ("" if open_now else
            '<span class="pill risk">deadline passed &mdash; what you do now is practice</span> ')
    token = core.student_token(db, attempt["student_id"])
    paper = core.handout_homework(db, a, attempt["student_id"])["paper"]
    send = f'/s/{E(token)}?tab=home&amp;a={a["id"]}'
    if paper:
        said = {"waiting": "You sent it on paper. Your teacher will tick it.",
                "ticked": "Your paper copy was ticked: %g out of 10. Doing it here can reach 10."
                          % (paper["mark"] or 0),
                "late": "Your paper copy came after the deadline.",
                "rejected": "Your teacher said the paper copy was not complete. Do it here, or "
                            f'<a class="linky" href="{send}">send the photos again</a>.'}[paper["state"]]
        onpaper = f'<p class="hwpaper">{said}</p>'
    elif open_now:
        onpaper = (f'<p class="hwpaper">Did it on paper? Send photos of the pages instead &mdash; '
                   f'ticked by your teacher, it counts {core.PAPER_TICK:g} out of 10.</p>'
                   f'<a class="btn ghost hwsend" href="{send}">Send photos of the pages</a>')
    else:
        onpaper = ""
    return (f'<div class="hwstrip"><span class="pill">Homework</span> '
            f'<span>due {E(when)}{(" &middot; " + E(rel)) if rel and open_now else ""}</span> '
            f'{late}<span class="sub">{tail}</span>{onpaper}</div>')


def part_result(pname, r, onward):
    """How a part went, at the top of it once it is checked."""
    marked = r["right_n"] + r["wrong_n"]
    teacher = (f' &middot; {r["teacher_n"]} of your own for your teacher to read'
               if r["teacher_n"] else "")
    fix = (" The right answer is shown under each one to look at again."
           if r["wrong_n"] else " Every one right.")
    return f"""<section class="hx-result" id="result">
  <div class="hx-dial">{hx_ring(r["right_n"], marked)}<p class="hx-dial-fig"><b>{r["right_n"]}</b><small>/{marked}</small></p></div>
  <div class="hx-result-text"><h3>{E(pname)} checked</h3>
  <p>{r["right_n"]} of {marked} right{teacher}.{fix}</p>{onward}</div>
</section>"""


def handout_results(parts, done, here, name):
    """The end: each part and the whole, as rows a student can read at a glance."""
    right = sum(r["right_n"] for r in done.values())
    marked = sum(r["right_n"] + r["wrong_n"] for r in done.values())
    teacher = sum(r["teacher_n"] for r in done.values())
    share = round(100 * right / marked) if marked else 0
    rows = ""
    for n, pname, _w, _m in parts:
        r = done[n]
        m = r["right_n"] + r["wrong_n"]
        pct = round(100 * r["right_n"] / m) if m else 0
        rows += (f'<a class="hx-row" href="{here}&amp;part={n}"><span class="hx-row-name">'
                 f'<span class="hx-row-no">{n}</span>{E(pname)}</span>'
                 f'<i class="hx-bar"><b style="width:{pct}%"></b></i>'
                 f'<span class="hx-row-fig">{r["right_n"]}/{m}</span></a>')
    what = "the answer" if teacher == 1 else f"the {teacher} answers"
    mine = (f'<p class="hx-final-note">Your teacher will read {what} you wrote '
            f'in your own words.</p>' if teacher else "")
    return f"""<section class="hx-final">
  <div class="hx-dial hx-dial-big">{hx_ring(right, marked)}<p class="hx-dial-fig"><b>{share}%</b></p></div>
  <h2>You finished {E(name)}</h2>
  <p class="hx-final-sub">{right} of {marked} right across the {len(parts)} parts.</p>
  <div class="hx-rows">{rows}</div>{mine}
</section>"""


def act_handout_save(req, db, token, hid):
    """Keep what the student has typed. Nothing is marked and nothing is
    finished: a handout is theirs to come back to."""
    st = core.student_by_token(db, token)
    if not st:
        return json_response({"ok": False})
    if not core.handout_open_to(db, hid, st["group_id"]):
        return json_response({"ok": False})
    if core.handout_blocked_by(db, hid, st):
        return json_response({"ok": False, "locked": True})
    attempt = db.execute(
        "SELECT * FROM dattempts WHERE test_id=? AND student_id=?"
        " ORDER BY id DESC LIMIT 1", (hid, st["id"])).fetchone()
    if not attempt:
        aid = core.start_attempt(db, hid, st["id"])
    else:
        aid = attempt["id"]
    # a part already checked is locked: a late save from an old tab must not
    # change what was marked
    done = core.handout_parts_done(db, aid)
    frozen = set()
    if done:
        lay = db.execute("SELECT layout FROM dtests WHERE id=?", (hid,)).fetchone()["layout"] or ""
        nums = {k for n, _a, _b, m in handout_parts(lay)[1] if n in done for k in part_keys(m)}
        frozen = {r["id"] for r in db.execute("SELECT id, num FROM dquestions WHERE test_id=?",
                                              (hid,)) if r["num"] in nums}
    saved = 0
    for key, values in req["form"].items():
        m = re.match(r"^q(\d+)$", key)
        if not m or int(m.group(1)) in frozen:
            continue
        qid, answer = int(m.group(1)), (values[0] or "").strip()
        db.execute(
            "INSERT INTO dresponses (attempt_id, question_id, given, correct)"
            " VALUES (?,?,?,NULL)"
            " ON CONFLICT(attempt_id, question_id)"
            " DO UPDATE SET given=excluded.given", (aid, qid, answer))
        saved += 1
    db.commit()
    return json_response({"ok": True, "saved": saved})



def act_handout_speak(req, db, token, hid):
    """A recording made in a handout's speaking task: kept beside the answer
    it is, and the box counts as answered. Long enough or not at all - the
    page does not send a short one, and this does not keep one."""
    fields, files = req["files"]
    st = core.student_by_token(db, token)
    if not st or not core.handout_open_to(db, hid, st["group_id"]):
        return json_response({"ok": False})
    if core.handout_blocked_by(db, hid, st):
        return json_response({"ok": False, "why": "locked"})
    qid = (fields.get("q", [""])[0] or "").strip()
    q = qid.isdigit() and db.execute("SELECT * FROM dquestions WHERE id=? AND test_id=? AND control='record'",
                                     (int(qid), hid)).fetchone()
    if not q or not files:
        return json_response({"ok": False})
    try:
        secs = int(float(fields.get("seconds", ["0"])[0] or 0))
    except ValueError:
        secs = 0
    if secs < core.SPEAK_MIN_SECONDS:
        return json_response({"ok": False, "why": "short"})
    _name, data = files[0]
    if not data or len(data) < 1000:
        return json_response({"ok": False, "why": "empty"})
    if len(data) > 30 * 1024 * 1024:
        return json_response({"ok": False, "why": "too long"})
    attempt = db.execute("SELECT * FROM dattempts WHERE test_id=? AND student_id=? ORDER BY id DESC LIMIT 1",
                         (hid, st["id"])).fetchone()
    aid = attempt["id"] if attempt else core.start_attempt(db, hid, st["id"])
    done = core.handout_parts_done(db, aid)
    if done:
        lay = db.execute("SELECT layout FROM dtests WHERE id=?", (hid,)).fetchone()["layout"] or ""
        for n, _a, _b, m in handout_parts(lay)[1]:
            if n in done and q["num"] in set(part_keys(m)):
                return json_response({"ok": False, "why": "locked"})
    kind = (fields.get("kind", [""])[0] or "").split(";")[0].strip().lower()
    ext = VOICE_EXT.get(kind, ".webm")
    if ext not in (".m4a", ".webm", ".ogg", ".mp3"):
        ext = ".webm"
    name = "speak_%d_%d_%s%s" % (aid, q["id"], core.now().strftime("%Y%m%d%H%M%S"), ext)
    os.makedirs(core.UPLOAD_DIR, exist_ok=True)
    with open(os.path.join(core.UPLOAD_DIR, name), "wb") as fh:
        fh.write(data)
    old = db.execute("SELECT given FROM dresponses WHERE attempt_id=? AND question_id=?", (aid, q["id"])).fetchone()
    was = core.speak_value(old["given"]) if old else None
    if was and not was["cant"] and was["file"] != name:
        try:
            os.remove(os.path.join(core.UPLOAD_DIR, was["file"]))
        except OSError:
            pass
    value = "rec:%s:%d" % (name, min(secs, 3600))
    db.execute("INSERT INTO dresponses (attempt_id, question_id, given, correct) VALUES (?,?,?,NULL)"
               " ON CONFLICT(attempt_id, question_id) DO UPDATE SET given=excluded.given", (aid, q["id"], value))
    db.commit()
    return json_response({"ok": True, "value": value, "url": "/s/%s/speak/%s" % (token, name)})


def act_handout_check(req, db, token, hid):
    """Mark what the student has typed, straight away.

    The point of a handout is that nobody waits for it. Everything with an
    answer in the key is marked here and now, by the same comparison the
    tests use - forgiving about case, spacing and a stray full stop, strict
    about the word. The rest (a sentence of their own, a discussion, the
    listening tasks) has no right answer to compare with, and is reported as
    'for your teacher' rather than quietly counted wrong.
    """
    st = core.student_by_token(db, token)
    if not st:
        return json_response({"ok": False})
    if not core.handout_open_to(db, hid, st["group_id"]):
        return json_response({"ok": False})
    if core.handout_blocked_by(db, hid, st):
        return json_response({"ok": False, "locked": True})
    attempt = db.execute(
        "SELECT * FROM dattempts WHERE test_id=? AND student_id=?"
        " ORDER BY id DESC LIMIT 1", (hid, st["id"])).fetchone()
    aid = attempt["id"] if attempt else core.start_attempt(db, hid, st["id"])

    qs = {q["id"]: q for q in db.execute(
        "SELECT id, num, kind, answer, control FROM dquestions WHERE test_id=?", (hid,))}
    typed = {}
    for key, values in req["form"].items():
        m = re.match(r"^q(\d+)$", key)
        if m and int(m.group(1)) in qs:
            typed[int(m.group(1))] = (values[0] or "").strip()
    part = (req["form"].get("part", [""])[0] or "").strip()
    if part.isdigit():
        return check_part(db, token, hid, aid, int(part), qs, typed)

    marks, right, wrong, open_ = {}, 0, 0, 0
    for qid, text in typed.items():
        q = qs[qid]
        if q["kind"] == "open" or not q["answer"]:
            if text:
                open_ += 1
                marks[qid] = {"state": "teacher"}
            ok = None
        elif not text:
            ok = None
        else:
            ok = core.answer_matches(text, q["answer"])
            marks[qid] = {"state": "right" if ok else "wrong",
                          "answer": q["answer"] if not ok else None}
            right += 1 if ok else 0
            wrong += 0 if ok else 1
        db.execute(
            "INSERT INTO dresponses (attempt_id, question_id, given, correct)"
            " VALUES (?,?,?,?) ON CONFLICT(attempt_id, question_id)"
            " DO UPDATE SET given=excluded.given, correct=excluded.correct",
            (aid, qid, text, None if ok is None else (1 if ok else 0)))
    db.commit()
    return json_response({"ok": True, "marks": marks, "right": right,
                          "wrong": wrong, "teacher": open_,
                          "blank": sum(1 for q in qs.values()
                                       if q["kind"] != "open" and q["answer"]
                                       and not typed.get(q["id"], ""))})



def check_part(db, token, hid, aid, part, qs, typed):
    """Check one part of a handout - once, and only when it is complete.

    Every box in the part must have an answer (a tick, and a correction to a
    sentence that was already right, may stay empty). The part is marked,
    kept, and locked; the next part opens. Checking a part already checked
    changes nothing, and a part further on than the current one is refused.
    """
    t = db.execute("SELECT layout FROM dtests WHERE id=?", (hid,)).fetchone()
    _intro, parts = handout_parts(t["layout"] or "")
    order = [n for n, *_r in parts]
    markup = {n: m for n, _a, _b, m in parts}.get(part)
    if markup is None:
        return json_response({"ok": False})
    done = core.handout_parts_done(db, aid)
    last = part == order[-1]
    go = f"/s/{token}?tab=handouts&h={hid}&part={'end' if last else part}"
    if part in done:
        return json_response({"ok": True, "go": go})
    if part != next((n for n in order if n not in done), None):
        return json_response({"ok": False, "locked": True})
    nums = set(part_keys(markup))
    mine = [q for q in qs.values() if q["num"] in nums]
    saved = {r["question_id"]: r["given"] or "" for r in db.execute(
        "SELECT question_id, given FROM dresponses WHERE attempt_id=?", (aid,))}

    def text(q):
        return typed[q["id"]] if q["id"] in typed else saved.get(q["id"], "").strip()
    missing = sorted(q["num"] for q in mine
                     if (q["control"] or "") not in OPTIONAL_BOXES
                     and (not text(q) or core.too_short(q, text(q))))
    if missing:
        return json_response({"ok": False, "missing": missing})
    right, wrong = mark_part(db, aid, part, mine, text)
    return json_response({"ok": True, "go": go, "right": right, "wrong": wrong})


def mark_part(db, aid, part, mine, text):
    """Mark every box of one part, keep the marks, and record the part as checked."""
    right = wrong = teacher = 0
    for q in mine:
        got = text(q)
        if q["kind"] == "open" or not q["answer"]:
            ok = None
            teacher += 1 if got else 0
        else:
            ok = core.answer_matches(got, q["answer"])
            right += 1 if ok else 0
            wrong += 0 if ok else 1
        db.execute(
            "INSERT INTO dresponses (attempt_id, question_id, given, correct)"
            " VALUES (?,?,?,?) ON CONFLICT(attempt_id, question_id)"
            " DO UPDATE SET given=excluded.given, correct=excluded.correct",
            (aid, q["id"], got, None if ok is None else (1 if ok else 0)))
    core.record_part(db, aid, part, right, wrong, teacher)
    return right, wrong


def carry_checked_parts(db, old_tid, new_tid):
    """A part a student had already checked in the old version stays checked
    in the new one - they have seen its answers - marked again by the new
    key. Only between versions with the same parts."""
    lay = {r["id"]: r["layout"] or "" for r in db.execute(
        "SELECT id, layout FROM dtests WHERE id IN (?,?)", (old_tid, new_tid))}
    old_parts, new_parts = handout_parts(lay.get(old_tid, ""))[1], handout_parts(lay.get(new_tid, ""))[1]
    if [(n, name) for n, name, *_r in old_parts] != [(n, name) for n, name, *_r in new_parts]:
        return 0
    qs = db.execute("SELECT id, num, kind, answer, control FROM dquestions WHERE test_id=?",
                    (new_tid,)).fetchall()
    carried = 0
    for a in db.execute("SELECT id, student_id FROM dattempts WHERE test_id=?", (old_tid,)).fetchall():
        done = core.handout_parts_done(db, a["id"])
        if not done:
            continue
        aid = core.start_attempt(db, new_tid, a["student_id"])
        have = core.handout_parts_done(db, aid)
        given = {r["question_id"]: (r["given"] or "").strip() for r in db.execute(
            "SELECT question_id, given FROM dresponses WHERE attempt_id=?", (aid,))}
        for n, _name, _what, markup in new_parts:
            if n in done and n not in have:
                nums = set(part_keys(markup))
                mark_part(db, aid, n, [q for q in qs if q["num"] in nums],
                          lambda q: given.get(q["id"], ""))
                carried += 1
    return carried


def portal_tests(db, s, token, query):
    """Sit a test on the phone and see the score the moment it is handed in."""
    level_id = core.level_of(db, s["group_id"])
    tid = query.get("t", [None])[0]
    tid = int(tid) if tid and tid.isdigit() else None
    base = f"/s/{E(token)}?tab=tests"

    if tid is None:
        tests = core.digital_tests(db, level_id, published_only=True)
        done = {a["test_id"]: a for a in core.student_attempts(db, s["id"])}
        if not tests:
            return ('<h2>Tests</h2><div class="empty-state">' + look_icon("clipboard", "empty-ico")
                    + '<p><strong>No tests yet.</strong><br>Your teacher will put one here.</p></div>')
        cfg = core.load_config()
        due = {}
        for r in db.execute("SELECT test_id, due_at FROM assignments WHERE group_id=? AND published=1"
                            " AND test_id IS NOT NULL", (s["group_id"],)):
            if r["due_at"] and (r["test_id"] not in due or r["due_at"] > due[r["test_id"]]):
                due[r["test_id"]] = r["due_at"]
        cards, sat = "", 0
        for t in tests:
            a = done.get(t["id"])
            homework = ""
            if t["id"] in due and not a:
                day, rel = due_words(due[t["id"]], cfg)
                late = rel.endswith("ago") or rel == "yesterday"
                homework = (f'<span class="hs-pill{" late" if late else ""}">Homework · '
                            f'{"was due" if late else "due"} {E(rel)}</span>')
            if a:
                sat += 1
                pct = round(100 * a["score"] / a["total"]) if a["total"] else 0
                state = f'{look_icon("check", "hs-done")}Done · {a["score"]} of {a["total"]} right'
                bar = f'<span class="hs-bar" role="img" aria-label="{pct}% right"><i style="width:{pct}%"></i></span>'
                cls = "done"
            else:
                state = f'{t["n"]} questions · not taken yet'
                bar, cls = "", "new"
            # data-reload: a paper's clock and its saving start on a page
            # load of their own, never on a page swapped in (nav.js)
            cards += (f'<a class="hs-card {cls}" href="{base}&amp;t={t["id"]}" data-reload>'
                      f'<span class="hs-badge ico">'
                      f'<svg viewBox="0 0 24 24" aria-hidden="true">{LOOK_ICONS["clipboard"]}</svg></span>'
                      f'<span class="hs-body"><span class="hs-name">{E(t["title"])}</span>{homework}{bar}'
                      f'<span class="hs-state">{state}</span></span></a>')
        past = ""
        for a in core.student_attempts(db, s["id"])[:8]:
            pct = round(100 * a["score"] / a["total"]) if a["total"] else 0
            past += (f'<li class="rs-row"><span class="rs-score">{pct}%</span>'
                     f'<span class="rs-name">{E(a["title"])}</span>'
                     f'<span class="rs-meta"><strong>{a["score"]}</strong> of {a["total"]} · '
                     f'{E((a["finished_at"] or "")[:10])}</span></li>')
        return (f'<h2>Tests</h2><p class="hs-sum"><strong>{sat} of {len(tests)}</strong> taken · marked the moment'
                f' you hand it in.</p><div class="hs-shelf">{cards}</div>'
                + (f'<h2>Your results</h2><ul class="rs-list">{past}</ul>' if past else ""))

    t = db.execute("SELECT * FROM dtests WHERE id=? AND published=1", (tid,)).fetchone()
    if not t:
        return '<h2>Tests</h2><p class="sub">That test is not open.</p>'
    qs = core.test_questions(db, tid)

    prev = db.execute(
        "SELECT * FROM dattempts WHERE test_id=? AND student_id=? AND finished_at IS NOT NULL"
        " ORDER BY finished_at DESC LIMIT 1", (tid, s["id"])).fetchone()
    done_for_good = core.sat_already(db, tid, s["id"])
    if prev and (done_for_good or query.get("again", [""])[0] != "1"):
        again = ('<span class="sub">This paper is sat once, and you have sat '
                 'it.</span>' if done_for_good else
                 f'<a class="tab" href="{base}&amp;t={tid}&amp;again=1" data-reload>'
                 f'Try it again</a>')
        given = {r["question_id"]: r for r in db.execute(
            "SELECT * FROM dresponses WHERE attempt_id=?", (prev["id"],))}
        rows = ""
        for q, opts in qs:
            r = given.get(q["id"])
            mine = r["given"] if r else None
            ok = r and r["correct"]
            mark = ('<span class="pill good">correct</span>' if ok
                    else '<span class="pill risk">wrong</span>')
            lines = ""
            if q["kind"] == "typed" or not opts:
                lines = f'<div class="opt right"><b>answer</b> {E(q["answer"] or "")}</div>'
                if not ok:
                    lines += f'<div class="opt chosen"><b>you put</b> {E(mine or "—")}</div>'
            for o in opts:
                cls = ""
                if o["letter"] == q["answer"]:
                    cls = " right"
                elif o["letter"] == mine:
                    cls = " chosen"
                lines += (f'<div class="opt{cls}"><b>{E(o["letter"])}</b> '
                          f'{E(o["text"])}</div>')
            rows += (f'<div class="dq"><div class="dqhead"><b>{q["num"]}</b> '
                     f'{E(q["prompt"])} {mark}</div>{lines}</div>')
        layout = t["layout"] if "layout" in t.keys() else None
        if layout:
            mine = {q["id"]: (given[q["id"]]["given"] or "")
                    for q, _o in qs if q["id"] in given}
            marks = {q["id"]: given[q["id"]]["correct"]
                     for q, _o in qs if q["id"] in given}
            wrong = "".join(
                f'<li>{E(q["prompt"][:90])} &mdash; <b class="bk-was">'
                f'{E(q["answer"] or "")}</b></li>'
                for q, _o in qs
                if given.get(q["id"]) and given[q["id"]]["correct"] == 0)
            why = core.how_it_ended(db, prev["id"])
            note = {"time": "The time ran out, so the paper was handed in as it was.",
                    "left": "You left the page, so the paper was handed in."}.get(why, "")
            return f"""<h2>{E(t["title"])}</h2>
<div class="card champ-hero"><div class="sub">You scored</div>
<div class="champ-name">{prev["score"]} of {prev["total"]}</div></div>
{f'<p class="flash err">{E(note)}</p>' if note else ''}
<div class="booksheet">{fill_layout(layout, qs, mine, marks, level=core.level_name(db, t["level_id"]), who=token)}</div>
{f'<h2 class="gap-4">The ones to look at again</h2><ul class="attn">{wrong}</ul>'
 if wrong else ''}
<p class="gap-4"><a class="tab" href="{base}">Back to the tests</a>
{again}</p>"""
        return f"""<h2>{E(t["title"])}</h2>
<div class="card champ-hero"><div class="sub">You scored</div>
<div class="champ-name">{prev["score"]} of {prev["total"]}</div></div>
<div class="card">{rows}</div>
<p class="gap-4"><a class="tab" href="{base}">Back to the tests</a>
{again}</p>"""

    attempt = core.start_attempt(db, tid, s["id"])
    passage = (f'<div class="card"><div class="passage">{E(t["passage"])}</div></div>'
               if t["passage"] else "")
    rows = ""
    for q, opts in qs:
        if q["kind"] == "typed" or not opts:
            picks = (f'<input class="typedin" name="q{q["id"]}" autocomplete="off"'
                     f' autocapitalize="off" spellcheck="false"'
                     f' placeholder="your answer">')
        else:
            picks = "".join(
                f'<label class="keypick"><input type="radio" name="q{q["id"]}"'
                f' value="{E(o["letter"])}" required><span><b>{E(o["letter"])}</b> '
                f'{E(o["text"])}</span></label>' for o in opts)
        pic = (f'<img class="passageimg" src="/testimg/{E(q["image"])}" alt="">'
               if q["image"] else "")
        rows += (f'{pic}<div class="dq"><div class="dqhead"><b>{q["num"]}</b> '
                 f'{E(q["prompt"])}</div>{picks}</div>')
    layout = t["layout"] if "layout" in t.keys() else None
    if layout:
        marked = sum(1 for q, _o in qs if q["kind"] != "open")
        sofar = core.attempt_answers(db, attempt)
        back = (' <span class="pill">picked up where you left off</span>'
                if sofar else "")
        minutes = t["minutes"] if "minutes" in t.keys() else None
        strict = bool(t["strict"]) if "strict" in t.keys() else False
        started = db.execute("SELECT started_at FROM dattempts WHERE id=?",
                             (attempt,)).fetchone()["started_at"]
        left = ""
        if minutes:
            used = (core.now() - core.parse(started)).total_seconds()
            left = str(max(0, int(minutes * 60 - used)))
        exam = ""
        if minutes:
            exam = (f'<div class="exambar"><span class="exclock" id="exclock"'
                    f' data-left="{left}">--:--</span>'
                    f'<span class="sub">{minutes} minutes'
                    f'{" &middot; leaving this page hands it in" if strict else ""}'
                    f'</span></div>')
        intro = (f"An exam. You have {minutes} minutes, the clock does not stop, "
                 f"and it hands itself in when the time is up."
                 if minutes else
                 f"Your booklet. Fill it in here &mdash; it saves as you type, "
                 f"so you can stop and come back.")
        return f"""<h2>{E(t["title"])}</h2>
<p class="sub">{intro} The {marked} answers with a key are marked the moment
you hand it in.{back}</p>
{exam}
<form method="post" action="/s/{E(token)}/test/{tid}"
 data-save="/s/{E(token)}/test/{tid}/save"
 data-minutes="{minutes or ''}" data-strict="{1 if strict else 0}"
 data-left="{left}">
<div class="booksheet">{fill_layout(layout, qs, sofar, level=core.level_name(db, t["level_id"]), who=token)}</div>
<div class="gap-3"><button>Hand it in</button>
<span class="sub" id="booksaved"></span></div>
</form>"""
    return f"""<h2>{E(t["title"])}</h2>
<p class="sub">{len(qs)} questions. It is marked as soon as you hand it in.</p>
{passage}
<form method="post" action="/s/{E(token)}/test/{tid}">
<div class="card">{rows}</div>
<div class="gap-3"><button>Hand it in</button></div>
</form>"""


def note_ending(db, token, tid, why):
    s = core.student_by_token(db, token)
    if not s or not why:
        return
    row = db.execute("SELECT id FROM dattempts WHERE test_id=? AND student_id=?"
                     " ORDER BY id DESC LIMIT 1", (tid, s["id"])).fetchone()
    if row:
        core.finish_reason(db, row["id"], why)


def act_book_save(req, db, token, tid):
    """Hold on to what has been typed, without handing the paper in."""
    s = core.student_by_token(db, token)
    if not s:
        return json_response({"ok": False})
    row = db.execute(
        "SELECT id FROM dattempts WHERE test_id=? AND student_id=?"
        " AND finished_at IS NULL", (tid, s["id"])).fetchone()
    if not row:
        return json_response({"ok": False, "why": "handed in"})
    given = {}
    for key, vals in req["form"].items():
        if key.startswith("q") and key[1:].isdigit():
            given[int(key[1:])] = (vals[0] or "").strip()
    return json_response({"ok": True,
                          "kept": core.save_progress(db, row["id"], given)})


def act_student_write(req, db, token, sub_id, quiet=False):
    """Keep what has been typed; hand it in only when they say so."""
    s = core.student_by_token(db, token)
    if not s:
        return not_found()
    row = db.execute("SELECT * FROM submissions WHERE id=? AND student_id=?"
                     " AND kind='text'", (sub_id, s["id"])).fetchone()
    if not row or row["status"] != "pending":
        return (json_response({"ok": False}) if quiet
                else redirect(f"/s/{token}?tab=write"))
    f = req["form"]
    text = f.get("answer", [""])[0]
    secs = (f.get("seconds", [""])[0] or "").strip()
    hand_in = f.get("hand_in", [""])[0] == "1"
    core.save_writing(db, sub_id, text, int(secs) if secs.isdigit() else None, hand_in)
    if quiet:
        return json_response({"ok": True, "words": core.count_words(text)})
    if hand_in and row["assignment_id"]:
        try:
            notify_handed_in(db, sub_id)
        except Exception:
            traceback.print_exc()
    return redirect(f"/s/{token}?tab=write&a={row['assignment_id'] or ''}")


def notify_handed_in(db, sub_id):
    """Tell the teacher a typed answer has arrived, the way a photo does."""
    token = CFG.get("telegram_token")
    if not token:
        return
    row = db.execute(
        "SELECT s.words, st.name, a.title FROM submissions s"
        " JOIN students st ON st.id=s.student_id"
        " LEFT JOIN assignments a ON a.id=s.assignment_id WHERE s.id=?",
        (sub_id,)).fetchone()
    # the teachers the bot knows are kept as a list under "teachers"; this read
    # a key nothing ever writes, so a typed essay arrived without a word
    who = [str(t) for t in json.loads(core.meta_get(db, "teachers", "[]") or "[]")]
    old = core.meta_get(db, "teacher_chat_id")
    if old and str(old) not in who:
        who.append(str(old))
    if not row or not who:
        return
    import bot
    for tid in who:
        bot.send(token, tid, "%s typed %d words for %s" % (
            row["name"], row["words"] or 0, row["title"] or "a writing task"))


def act_student_test(req, db, token, tid):
    """Mark a handed-in test at once and send the student to their result."""
    s = core.student_by_token(db, token)
    if not s:
        return not_found()
    t = db.execute("SELECT id FROM dtests WHERE id=? AND published=1", (tid,)).fetchone()
    if not t:
        return redirect(f"/s/{token}?tab=tests")
    if core.sat_already(db, tid, s["id"]):
        # the page does not offer it, so this is a stale tab, a second phone,
        # or the back button - never a reason to overwrite a sat exam
        return redirect(f"/s/{token}?tab=tests&t={tid}")
    given = {}
    for key, values in req["form"].items():
        m = re.match(r"^q(\d+)$", key)
        if m and values:
            given[int(m.group(1))] = values[0]
    attempt = core.start_attempt(db, tid, s["id"])
    # answers already saved as they typed must not be lost when the paper is
    # handed in by the clock, which sends only what is on screen
    kept = core.attempt_answers(db, attempt)
    kept.update({k: v for k, v in given.items() if v})
    core.submit_attempt(db, attempt, kept)
    why = (req["form"].get("ended", [""])[0] or "").strip()
    if why in ("time", "left"):
        core.finish_reason(db, attempt, why)
    return redirect(f"/s/{token}?tab=tests&t={tid}")


def portal_write(db, s, token, query):
    """A writing paper: the question on one side, the sheet on the other.

    Laid out the way the real thing is, because the point is to practise under
    something like exam conditions - not to fill in a form. On a phone the two
    stack, with the question collapsed once it has been read, because a column
    of text and a column of typing side by side on a 360px screen is neither.
    """
    aid = query.get("a", [None])[0]
    aid = int(aid) if aid and aid.isdigit() else None
    base = f"/s/{E(token)}?tab=write"

    if aid is None:
        open_tasks = [a for a in db.execute(
            "SELECT * FROM assignments WHERE group_id=? AND closed=0 AND published=1"
            " AND prompt IS NOT NULL ORDER BY COALESCE(due_at, created_at) DESC",
            (s["group_id"],)) if core.still_open(a["due_at"])]
        done = {r["assignment_id"]: r for r in db.execute(
            "SELECT * FROM submissions WHERE student_id=? AND kind='text'",
            (s["id"],))}
        if not open_tasks:
            return ('<h2>Writing</h2><div class="card empty-card"><p>No writing task open just '
                    'now. When your teacher sets one it appears here.</p></div>')
        cards = ""
        for a in open_tasks:
            r = done.get(a["id"])
            if r and not r["draft"]:
                sub = "handed in &middot; %d words" % (r["words"] or 0)
            elif r and (r["words"] or 0):
                sub = "%d words so far" % r["words"]
            else:
                sub = "not started"
            day, clock = core.deadline_parts(a["due_at"], core.load_config())
            cards += (f'<a class="tile" href="{base}&amp;a={a["id"]}">'
                      f'<div class="tile-title">{E(a["title"])}</div>'
                      f'<div class="sub flush">{sub}'
                      f'{" &middot; due " + E(day) if day else ""}</div></a>')
        return f'<h2>Writing</h2><div class="tiles">{cards}</div>'

    task = core.writing_task(db, aid)
    if not task or task["group_id"] != s["group_id"]:
        return '<h2>Writing</h2><p class="sub">That task is not open to you.</p>'
    row = core.open_writing(db, s["id"], aid)
    handed = not row["draft"]
    day, clock = core.deadline_parts(task["due_at"], core.load_config())
    least = task["min_words"] or 0

    if handed:
        return f"""<h2>{E(task["title"])}</h2>
<div class="card good"><strong>Handed in.</strong>
<p class="sub gap-2">{row["words"] or 0} words. Your teacher will mark it and you
will see the score on your Homework page.</p></div>
<div class="paper"><div class="question"><h3>The question</h3>
<div class="qtext">{E(task["prompt"])}</div></div>
<div class="sheet"><h3>What you wrote</h3>
<div class="written">{E(row["answer"] or "")}</div></div></div>
<p class="gap-3"><a class="tab" href="{base}">Back to writing tasks</a></p>"""

    return f"""<h2>{E(task["title"])}</h2>
<p class="sub">Write your answer here instead of on paper. It saves as you type.
{"Due " + E(day) + " at " + E(clock) + "." if day else ""}</p>
<div class="paper" id="paper" data-sub="{row["id"]}" data-min="{least}"
     data-minutes="{task["minutes"] or 0}">
  <div class="question">
    <button type="button" class="qtoggle" id="qtoggle">The question</button>
    <div class="qbody" id="qbody"><div class="qtext">{E(task["prompt"])}</div></div>
  </div>
  <div class="sheet">
    <form method="post" action="/s/{E(token)}/write/{row["id"]}" id="writeform">
      <textarea name="answer" id="answer" spellcheck="false"
        placeholder="Start writing here…">{E(row["answer"] or "")}</textarea>
      <div class="sheetbar">
        <span id="wordcount" class="counter">0 words</span>
        <span id="clock" class="counter"></span>
        <span id="saved" class="sub"></span>
        <button name="hand_in" value="1">Hand it in</button>
      </div>
    </form>
  </div>
</div>"""


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
        elif t["submission_id"] or t["status"] == "handout":
            state = ('<span class="pill mute">in progress</span>' if t["status"] == "handout"
                     else '<span class="pill mute">waiting</span>')
        else:
            state = '<span class="pill risk">not sent</span>'
        hist += f'<tr><td>{E(t["title"])}</td><td class="right">{state}</td></tr>'
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


SURNAME_ENDS = ("ov", "ova", "ev", "eva", "yev", "yeva")


def first_name(full):
    """The name a student is called by. Uzbek names are usually written
    surname first - Jo'raboyev Abdurahmon - so a leading surname is skipped."""
    parts = (full or "").split()
    if not parts:
        return ""
    lead = parts[0].lower().replace("'", "").replace("\u2019", "")
    pick = parts[1] if len(parts) > 1 and lead.endswith(SURNAME_ENDS) else parts[0]
    return pick[:1].upper() + pick[1:]


def portal_profile(db, s, token, flash=""):
    """Who they are, how far up the mountain they are, and a line worth reading."""
    quote, who = core.quote_of_the_day()
    c = core.climb(db, s["id"])

    def field(key):
        return (s[key] if key in s.keys() else None) or ""

    here = field("climb_from") or core.camp_for_level(
        core.level_name(db, core.level_of(db, s["group_id"])))

    def camps(name, current):
        opts = ['<option value="">&mdash;</option>']
        for key, label in core.CAMPS:
            sel = " selected" if key == current else ""
            opts.append(f'<option value="{key}"{sel}>{E(label)}</option>')
        return f'<select name="{name}">{"".join(opts)}</select>'

    first = first_name(s["name"])
    hi = (E(first) + ", ") if first else ""

    def cap(t):
        return t[:1].upper() + t[1:]
    hero_stats, route, earned, opened = "", "", "", ""
    if not c:
        head = f"Where will you climb{', ' + E(first) if first else ''}?"
        lead = ("Pick the summit you dream of. Every piece of homework carries you "
                "a step closer.")
        opened = " open"
    else:
        goal = E(c["labels"][-1])
        passed = int(c["climbed"])
        summit = c["climbed"] >= c["camps"]
        if summit:
            head = cap(f"{hi}you made it to <em>{goal}</em>.")
            lead = "Stand here a moment and look down. Then choose a higher summit."
        elif c["percent"] < 34:
            head = cap(f"{hi}<em>{goal}</em> is waiting for you.")
            lead = "Every piece of homework is a step up the mountain."
        elif c["percent"] < 75:
            head = cap(f"{hi}you're on your way to <em>{goal}</em>.")
            lead = (f"{passed} camp{'' if passed == 1 else 's'} behind you. Keep climbing."
                    if passed else
                    f"The first camp, <em>{E(c['next_label'])}</em>, is "
                    f"{c['to_next']:g} points away.")
        else:
            left = (c["camps"] - c["climbed"]) * core.CLIMB_PER_CAMP
            head = cap(f"{hi}the summit is in sight.")
            lead = f"Only {left:.0f} points to <em>{goal}</em>."

        nxt = ('<div class="cl-stat"><div class="k">Summit</div><div class="v">Reached</div>'
               '<div class="sub">choose a higher one</div></div>' if summit else
               f'<div class="cl-stat"><div class="k">Next camp</div>'
               f'<div class="v">{E(c["next_label"])}</div>'
               f'<div class="sub">{c["to_next"]:g} points to go</div></div>')
        hero_stats = f"""<div class="cl-stats">
  <div class="cl-stat lead"><div class="k">You are at</div><div class="v">{E(c["at_label"])}</div>
    <div class="sub">{"your summit" if summit else f'{c["into_next"]}% of the way to the next camp'}</div></div>
  {nxt}
  <div class="cl-stat"><div class="k">Whole climb</div><div class="v">{c["percent"]:g}%</div>
    <div class="sub">{E(c["labels"][0])} &rarr; {goal}</div></div>
</div>"""
        steps = ""
        last = len(c["labels"]) - 1
        for i, label in enumerate(c["labels"]):
            dream = " dream" if i == last else ""
            if i < passed or (summit and i == last):
                cls, mark, note = "done", "&#10003;", "reached"
            elif i == passed:
                cls, mark = "here", ""
                note = (f'<span class="cl-mini"><i style="width:{c["into_next"]}%"></i></span>'
                        f'<span>{c["into_next"]}% to '
                        f'{E(c["labels"][i + 1]) if i < last else "the top"}</span>')
            else:
                cls = "ahead"
                mark = "&#9733;" if i == last else ""
                note = (f'{(i - c["climbed"]) * core.CLIMB_PER_CAMP:.0f} points away'
                        + (" &middot; your dream" if i == last else ""))
            steps += (f'<li class="{cls}{dream}"><span class="dot">{mark}</span>'
                      f'<div><div class="name">{E(label)}</div>'
                      f'<div class="sub">{note}</div></div></li>')
        route = f'<h4 class="cl-h">The route</h4><ol class="route">{steps}</ol>'
        earned = (f'<p class="cl-earned">Carried here by <strong>{c["graded"]}</strong> '
                  f'marked piece{"" if c["graded"] == 1 else "s"} of homework and '
                  f'<strong>{c["words"]}</strong> word{"" if c["words"] == 1 else "s"} you '
                  f'have kept. A piece marked 10/10 is one point; a camp is '
                  f'{core.CLIMB_PER_CAMP:g}. Nothing you type moves you up &mdash; only '
                  f'work does.</p>')
    face_photo = f"/s/{E(token)}/photo" if s["photo"] else ""
    choose = f"""<details class="cl-set"{opened}><summary>{"Change my route" if c else "Set my route"}</summary>
    <form method="post" action="/s/{E(token)}/profile" enctype="multipart/form-data"
          class="pf-set">
      <label class="f">I started at{camps("climb_from", here)}</label>
      <label class="f">I am climbing to{camps("climb_to", field("climb_to"))}</label>
      <button>Save</button>
    </form></details>"""

    return f"""{flash}
<div class="card cl-card">
  <div class="cl-hero">
    <i class="cl-shoot"></i><i class="cl-shoot two"></i>
    <div class="cl-top">
      <div class="cl-eyebrow">Your climb</div>
      <h3 class="cl-headline">{head}</h3>
      <p class="cl-lead">{lead}</p>
    </div>
    {charts.mountain(c, avatar=core.avatar_of(s), photo=face_photo)}
  </div>
  <div class="cl-body">
    {hero_stats}
    {route}
    {earned}
    {"" if c else choose}
    <div class="cl-quote"><span class="cl-star">&#10022;</span>
      <p>&ldquo;{E(quote)}&rdquo;</p><span class="who">{E(who)}</span></div>
    {choose if c else ""}
  </div>
</div>

<details class="adder"><summary>Edit my details</summary>
<div class="card"><form method="post" action="/s/{E(token)}/profile"
      enctype="multipart/form-data">
  <div class="inline">
    <label class="f">Name<input name="name" value="{E(s["name"])}" required></label>
    <label class="f">Phone<input name="phone" type="tel" value="{E(field("phone"))}"
      placeholder="+998 .."></label>
  </div>
  <label class="f gap-3">About you
    <input name="about" value="{E(field("about"))}"
           placeholder="Why you are learning English"></label>
  <label class="f gap-3">Your photo
    <input type="file" name="photo" accept="image/*"></label>
  <div class="gap-4"><button>Save</button></div>
</form></div></details>"""


def ordinal(n):
    return "%d%s" % (n, {1: "st", 2: "nd", 3: "rd"}.get(n if n % 100 < 20 else n % 10, "th"))


def rank_list(items, cls=""):
    """A ranking a phone can read: place, initial, name, a line under it, and
    the figure that decides it on the right. Each item is a dict with place
    (None for below the line), name, meta, value, unit and me."""
    out = ""
    line = False
    for it in items:
        if it.get("place") is None and not line and it.get("line"):
            out += f'<li class="lg-line">{it["line"]}</li>'
            line = True
        place = it.get("place")
        badge = (f'<span class="lg-place p{place}">{place}</span>' if place and place <= 3
                 else f'<span class="lg-place">{place if place else "&ndash;"}</span>')
        initial = E((first_name(it["name"]) or it["name"] or "?")[:1].upper())
        me = it.get("me")
        mark = ' id="me"' if me else ""
        out += (f'<li class="lg-row{" me" if me else ""}"{mark}>{badge}'
                f'<span class="lg-ava">{initial}</span>'
                f'<span class="lg-who"><span class="lg-name">{E(it["name"])}'
                + (' <span class="lg-you">you</span>' if me else "")
                + f'</span><span class="lg-meta">{it.get("meta", "")}</span></span>'
                f'<span class="lg-val"><b>{it["value"]}</b><small>{E(it.get("unit", ""))}</small></span></li>')
    return f'<ol class="lg-list{(" " + cls) if cls else ""}">{out}</ol>'


def podium(items):
    """The top three, standing on their steps: second, first, third."""
    top = {it["place"]: it for it in items if it.get("place") in (1, 2, 3)}
    if len(top) < 3:
        return ""
    cols = ""
    for p in (2, 1, 3):
        it = top[p]
        cols += (f'<div class="pd-col pd{p}{" me" if it.get("me") else ""}">'
                 f'<span class="pd-ava">{E((first_name(it["name"]) or "?")[:1].upper())}</span>'
                 f'<span class="pd-name">{E(first_name(it["name"]) or it["name"])}</span>'
                 f'<span class="pd-pts">{it["value"]} {E(it.get("unit", ""))}</span>'
                 f'<span class="pd-step">{p}</span></div>')
    return f'<div class="podium" aria-label="The top three">{cols}</div>'


def portal_champ_row(db, r, me_id, show_group=True, tops=None):
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
        best = (tops or {}).get(key) or 0
        share = (got / best * 100.0) if best else 0
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
<div class="card empty-card"><p>The championship has not started yet.
Your teacher will start it soon.</p></div>
<h2>Where you are</h2>
{standing_line(db, s) or '<p class="sub">Nothing marked yet.</p>'}"""

    mine = next((r for r in champ["rows"] if r["student"]["id"] == s["id"]), None)
    if not mine:
        return f"""<h2>Where you are</h2>
{standing_line(db, s) or '<p class="sub">Nothing marked yet.</p>'}"""

    shown = core.scope_standing(champ, s["group_id"]) if scope == "class" else champ
    here = next((r for r in shown["rows"] if r["student"]["id"] == s["id"]), mine)

    where = "in your class" if scope == "class" else "in the school"
    if here["eligible"]:
        rank = here["rank"]
        num, suf = str(rank), ordinal(rank)[len(str(rank)):]
        standing = (f'You are <strong>{ordinal(rank)}</strong> {where} with '
                    f'<strong>{here["total"]:g}</strong> points.')
        big = (f'<span class="lg-big">{num}<sup>{suf}</sup></span>'
               f'<span class="lg-of">{where}<br><small>of {shown["eligible"]}</small></span>')
    else:
        standing = (f'Your first {core.MIN_GRADED} deadlines have to pass before '
                    f'you enter. {here["graded"]} so far.')
        big = (f'<span class="lg-big lg-wait">{here["graded"]}<small>/{core.MIN_GRADED}</small></span>'
               f'<span class="lg-of">deadlines<br><small>before you enter</small></span>')

    best = {k: max([r["points"].get(k) or 0 for r in champ["rows"]] or [0])
            for k, _l, _w in core.CHAMPIONSHIP}
    parts = "".join(
        f'<div class="lg-part"><span class="lg-plabel">{E(label)}</span>'
        f'<span class="lg-pbar"><i style="width:'
        f'{min(100, (mine["points"].get(key, 0) / float(best.get(key) or 1) * 100)):.0f}%"></i></span>'
        f'<b>{mine["points"].get(key, 0):g}</b></div>'
        for key, label, weight in core.CHAMPIONSHIP)

    frozen = ('<div class="card paused"><strong>The league is paused.</strong>'
              '<p class="sub gap-2">Your teacher has stopped the '
              'table for now. Nothing counts towards the championship until it '
              'starts again &mdash; keep working, it will be back.</p></div>'
              if champ["paused"] else "")

    of, hw_of = core.SEASON_LESSONS, core.SEASON_HOMEWORK
    pace = ("Your season is finished and this score is final."
            if mine["done"] and mine["final"] else
            "Your lessons and homework sets are done. The last homework is still being marked, "
            "so this score can still move." if mine["done"] else
            f'Your season ends after {of} lessons and {hw_of} sets of homework.')

    def tab(sc, label):
        on = " on" if scope == sc else ""
        return (f'<a class="tab{on}" href="/s/{E(token)}?tab=class&amp;scope={sc}">'
                f'{E(label)}</a>')
    tabs = f'<div class="tabs lg-tabs">{tab("class", "My class")}{tab("school", "Whole school")}</div>'

    waiting = len(shown["rows"]) - shown["eligible"]
    items = []
    for r in shown["rows"]:
        st = r["student"]
        short = {"In the lesson": "Lesson"}
        bits = [f'{min(r["sets"], hw_of)}/{hw_of} homework', f'{r["lessons"]}/{of} lessons']
        if scope == "school":
            bits.insert(0, f'<span class="lg-cls">{E(group_name(db, st["group_id"]))}</span>')
        items.append({"place": r["rank"] if r["eligible"] else None, "name": st["name"],
                      "meta": " · ".join(bits), "value": f'{r["total"]:g}', "unit": "points",
                      "me": st["id"] == s["id"],
                      "line": f'Below the line: fewer than {core.MIN_GRADED} deadlines behind them yet'})
    below = (f'<p class="sub">The last {waiting} have not yet handed in '
             f'{core.MIN_GRADED} deadlines behind them yet, so they are below the '
             f'line for now.</p>' if waiting else "")
    lesson_pct = min(100, round(100 * mine["lessons"] / of)) if of else 0
    sets_pct = min(100, round(100 * mine["sets"] / hw_of)) if hw_of else 0

    return f"""<h2>Championship &mdash; season {champ["season"]}</h2>
{frozen}
<div class="lg-hero">
  <div class="lg-top"><span class="lg-rank">{big}</span><span class="lg-total"><b>{here["total"]:g}</b><small>points</small></span></div>
  <p class="lg-say">{standing} <a href="#me" class="findme">Find me in the table &darr;</a></p>
  <div class="lg-parts">{parts}</div>
  <div class="lg-season"><span>{pace}</span>
    <div class="lg-count"><span>Homework sets</span><span class="lg-sbar"><i style="width:{sets_pct}%"></i></span><b>{min(mine["sets"], hw_of)}/{hw_of}</b></div>
    <div class="lg-count"><span>Lessons</span><span class="lg-sbar"><i style="width:{lesson_pct}%"></i></span><b>{mine["lessons"]}/{of}</b></div></div>
</div>
{tabs}
{podium(items)}
{rank_list(items)}
{below}
<details class="lg-how"><summary>How the league works</summary>
<p>A season lasts {hw_of} sets of homework and {of} lessons, not a month, so everyone is judged over
the same amount of work &mdash; a class that had no homework for a while keeps going until it has had
its {hw_of} sets. A missed set counts as one of them, scored nought. Every set and every lesson adds
to your score, so it climbs as the season goes on.
You enter the table once your first {core.MIN_GRADED} deadlines have passed. The prize goes to the best
in the whole school.</p></details>
<h2>Your homework</h2>
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
    index = core.overall_index(completion, st["done_average"], marks["overall"])
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
        elif t["submission_id"] or t["status"] == "handout":
            state = ('<span class="pill mute">in progress</span>' if t["status"] == "handout"
                     else '<span class="pill mute">waiting to be marked</span>')
        else:
            state = '<span class="pill risk">not handed in</span>'
        hist += f'<tr><td>{E(t["title"])}</td><td class="right">{state}</td></tr>'

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
    <div class="sub">{E(group_name(db, s["group_id"]))}
      {"· " + E(level) if level else ""} · report for parents</div></div>
</div>
<div class="card"><p>Overall this student is <strong>{verdict}</strong>:
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
   else '<div class="card empty-card"><p class="sub">No lessons marked yet.</p></div>'}</div>
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
        issued = (goal["updated_at"] or "")[:10]
        given = first_name(s["name"]) or s["name"]
        family = " ".join(w for w in (s["name"] or "").split() if w != given) or "—"
        cefr = ("C2" if overall >= 8.5 else "C1" if overall >= 7 else "B2" if overall >= 5.5
                else "B1" if overall >= 4 else "A2")
        boxes = "".join(
            f'<div class="tr-box"><span class="tr-k">{core.BAND_LABELS[k]}</span>'
            f'<span class="tr-v">{scores[k]:g}</span></div>' for k in core.BAND_SECTIONS)
        # the paper itself says what it is: a line of tiny print, all over it,
        # that no crop and no edit takes out without taking the page with it
        micro = "IELTS ZONE &#183; TARGET &#183; NOT A TEST RESULT &#183; "
        card = f"""<div class="cert-wrap"><div class="cert tr" id="cert">
  <svg class="tr-paper" viewBox="0 0 800 600" preserveAspectRatio="none" aria-hidden="true">
    <defs>
      <pattern id="tr-micro" width="300" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(-18)">
        <text x="0" y="6.5" font-size="5.2" font-family="Helvetica, Arial, sans-serif" font-weight="700"
              textLength="300" lengthAdjust="spacing" fill="currentColor">{micro}{micro}</text></pattern>
      <pattern id="tr-wave" width="40" height="20" patternUnits="userSpaceOnUse">
        <path d="M0 10 Q10 0 20 10 T40 10" fill="none" stroke="currentColor" stroke-width=".6"/></pattern>
    </defs>
    <rect width="800" height="600" fill="url(#tr-wave)" class="tr-waves"/>
    <rect width="800" height="600" fill="url(#tr-micro)" class="tr-microprint"/>
    <rect x="10" y="10" width="780" height="580" rx="6" fill="none" stroke="currentColor" stroke-width="2.4"/>
    <rect x="17" y="17" width="766" height="566" rx="4" fill="none" stroke="currentColor" stroke-width=".8"/>
  </svg>
  <div class="tr-ribbon" aria-hidden="true">TARGET</div>
  <div class="tr-inner">
    <header class="tr-head">
      <div class="tr-brand"><img src="/static/zone-logo.png" alt=""><div><b>IELTS ZONE</b>
        <span>Target Score Report</span></div></div>
    </header>
    <section class="tr-sec">
      <h4>Student</h4>
      <div class="tr-who">
        <div class="tr-fields">
          <div class="tr-f"><span>Family name</span><b>{E(family)}</b></div>
          <div class="tr-f"><span>First name</span><b>{E(given)}</b></div>
          <div class="tr-f"><span>Goal set</span><b>{E(issued)}</b></div>
          <div class="tr-f"><span>Class</span><b>{E(group_name(db, s["group_id"]))}</b></div>
          <div class="tr-f"><span>Course level</span><b>{E(level or "—")}</b></div>
          <div class="tr-f"><span>My exam date</span><b>{E(target) if target else "not chosen yet"}</b></div>
        </div>
        <div class="tr-photo">{photo}</div>
      </div>
    </section>
    <section class="tr-sec">
      <h4>Target band scores</h4>
      <div class="tr-scores">{boxes}
        <div class="tr-box overall"><span class="tr-k">Overall target</span><span class="tr-v">{overall:g}</span></div>
        <div class="tr-box cefr"><span class="tr-k">CEFR level</span><span class="tr-v">{cefr}</span></div>
      </div>
    </section>
    <section class="tr-foot">
      <div class="tr-comment"><h4>Teacher's comment</h4>
        <p>{E(core.band_words(overall))} &mdash; the band {E(given)} is working towards.
        Every piece of homework brings it closer.</p>
        <div class="tr-sign"><span class="sig">Azamat</span><span class="line"></span><span class="who">Teacher, IELTS Zone</span></div>
      </div>
      <div class="cert-stamp tr-stamp" aria-hidden="true"><img src="/static/zone-logo.png" alt="">
        <svg viewBox="0 0 100 100"><defs><path id="stamp-ring" d="M50 50 m-38 0 a38 38 0 1 1 76 0 a38 38 0 1 1 -76 0"/></defs>
        <circle cx="50" cy="50" r="47" fill="none" stroke="currentColor" stroke-width="2.2"/>
        <circle cx="50" cy="50" r="29" fill="none" stroke="currentColor" stroke-width="1.2"/>
        <text font-size="10" font-weight="700" fill="currentColor">
        <textPath href="#stamp-ring" textLength="232" lengthAdjust="spacing">IELTS ZONE &#8226; MY GOAL &#8226; IELTS ZONE &#8226; MY GOAL &#8226;</textPath></text></svg></div>
    </section>
    <p class="tr-note">A target set at IELTS Zone &mdash; not a test result. This is not an IELTS Test Report Form
      and is not issued by IELTS, British Council, IDP or Cambridge.</p>
  </div>
</div>
</div>
<div style="margin-bottom:16px"><button type="button" onclick="window.print()">
  Print or save as PDF</button></div>
"""
    else:
        card = ('<div class="card"><p>Choose a band for all four '
                'sections and your card will appear here.</p></div>')

    return f"""{flash}
<h2>My goal</h2>
<p class="sub">Choose the band you are aiming for in each part, and your target certificate
appears below &mdash; print it and keep it where you study. The overall band is worked out
the way IELTS works it out: a quarter rounds up to the next half band.</p>
{card}
<div class="card"><form method="post" action="/s/{E(token)}/goal"
      enctype="multipart/form-data">
  <div class="inline">{"".join(picker(k) for k in core.BAND_SECTIONS)}
    <label class="f">Exam date (optional)<input type="date" name="target_date"
      value="{E(target)}"></label></div>
  <label class="f gap-3">Your photo (optional)
    <input type="file" name="photo" accept="image/*"></label>
  <div class="gap-3"><button>Save my goal</button></div>
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


KIND_NAME = {"vocab": "Vocabulary", "grammar": "Grammar",
             "exam": "Exam words"}
# the sections that open on their books rather than straight on the steps
BY_BOOK = ("vocab", "exam")


def solo_rows(rows, me_id, cols):
    """A ranking table: position, who, and the columns that matter for it."""
    out = ""
    for i, r in enumerate(rows, 1):
        mine = ' class="me"' if r["id"] == me_id else ""
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, str(i))
        out += (f'<tr{mine}><td class="num">{medal}</td>'
                f'<td class="who">{E(r["avatar"] or "")} {E(r["name"])}</td>'
                + "".join(f'<td class="num">{c(r)}</td>' for c in cols) + "</tr>")
    return out


def portal_play(db, s, token, query):
    """Solo play as a career: books, steps, and a step earned by passing.

    Nothing here touches the league. The live game still needs the teacher to
    host it; this is the same game for a student on their own.
    """
    base = f"/s/{E(token)}?tab=play"
    kind = (query.get("kind", [""])[0] or "")
    # a book with no name still needs a link of its own, and an empty value
    # never survives the address bar, so it travels as "-"
    book = query.get("book", [None])[0]
    if book == "-":
        book = ""
    lid = query.get("l", [""])[0]

    if lid.isdigit():
        wl = db.execute("SELECT * FROM word_lists WHERE id=?", (int(lid),)).fetchone()
        if not wl:
            return '<h2>Play</h2><p class="sub">That list is not open to your class.</p>'
        chain = core.play_chain(db, s, wl["kind"], (wl["source"] or "").strip())
        here = next((c for c in chain if c["list"]["id"] == wl["id"]), None)
        back = (f'{base}&amp;kind={E(wl["kind"])}'
                + (f'&amp;book={urllib.parse.quote(wl["source"] or "") or "-"}'
                   if wl["kind"] in BY_BOOK else ""))
        if not here:
            return '<h2>Play</h2><p class="sub">That list is not open to your class.</p>'
        if not here["unlocked"]:
            before = chain[here["step"] - 2]["list"]["title"]
            return (f'<p class="pl-back"><a href="{back}">&larr; All the steps</a></p>'
                    f'<div class="pl-locked">{look_icon("lock", "pl-lock")}<h2>{E(wl["title"])}</h2>'
                    f'<p>Step {here["step"]} is locked. Pass <strong>{E(before)}</strong> first.</p>'
                    f'<a class="btn" href="{back}">Back to the steps</a></div>')
        n = here["n"]
        round_n = min(core.SOLO_ROUND, n)
        mine = core.solo_best(db, s["id"], wl["id"])
        board = core.solo_list_board(db, wl["id"], s["group_id"])
        items = [{"place": i, "name": r["name"], "meta": "%d%% right" % r["pct"], "value": "%d" % r["best"],
                  "unit": "points", "me": r["id"] == s["id"]} for i, r in enumerate(board[:10], 1)]
        state = (f'{look_icon("check", "pl-ok")}Passed' if here["passed"] else
                 f'You need <strong>{here["need"]} of {round_n}</strong> to pass')
        me_line = (f'Your best this week: <strong>{mine["best"]}</strong> points, '
                   f'{mine["pct"]}% right, in {mine["rounds"]} round(s).'
                   if mine["rounds"] else "You have not played this step this week.")
        return f"""<p class="pl-back"><a href="{back}">&larr; All the steps</a></p>
<div class="pl-hero {E(wl["kind"])}">
  <span class="pl-hero-k">Step {here["step"]}</span>
  <h2 class="pl-hero-t">{E(wl["title"])}</h2>
  <p class="pl-hero-p">{n} questions &middot; a round is {round_n} of them, picked at random,
  {core.SOLO_SECONDS} seconds each</p>
  <p class="pl-hero-s">{state}</p>
  <form method="post" action="/s/{E(token)}/solo/start">
  <input type="hidden" name="list" value="{wl["id"]}">
  <button class="pl-go">{look_icon("play", "pl-go-ico")}{"Play it again" if here["passed"] else "Start step %d" % here["step"]}</button></form>
  <p class="pl-hero-me">{me_line}</p>
</div>
<h3 class="gap-4">This week in your class</h3>
{rank_list(items) if items else '<div class="empty-state">' + look_icon("trophy", "empty-ico")
 + '<p><strong>Nobody has played it yet this week.</strong><br>Be the first.</p></div>'}
<p class="sub gap-3">Your best round this week counts, however many you play. The
table starts again every Monday; a step you have passed stays passed.</p>"""

    if kind in KIND_NAME:
        if kind in BY_BOOK and book is None:
            books = core.play_books(db, s, kind)
            cards = ""
            for b in books:
                pct = round(100 * b["passed"] / b["steps"]) if b["steps"] else 0
                cards += (f'<a class="pl-book {E(kind)}" href="{base}&amp;kind={E(kind)}&amp;book='
                          f'{urllib.parse.quote(b["source"]) or "-"}">{look_icon("book", "pl-book-ico")}'
                          f'<span class="pl-book-t">{E(b["title"])}</span>'
                          f'<span class="pl-book-m">{b["passed"]} of {b["steps"]} '
                          f'step{"" if b["steps"] == 1 else "s"} passed</span>'
                          f'<span class="pl-bar"><i style="width:{pct}%"></i></span></a>')
            return (f'<p class="pl-back"><a href="{base}">&larr; Play</a></p>'
                    f"<h2>{KIND_NAME[kind]}</h2><p class=\"sub\">Pick a book. Each "
                    f"one is a ladder: pass a step to open the next.</p>"
                    + (f'<div class="pl-books">{cards}</div>' if cards else
                       '<div class="empty-state">' + look_icon("book", "empty-ico") + '<p><strong>No lists here yet.'
                       '</strong><br>Your teacher will add some.</p></div>'))

        chain = core.play_chain(db, s, kind, book if kind in BY_BOOK else None)
        title = ((book or "Other lists") if kind in BY_BOOK
                 else KIND_NAME[kind])
        steps = ""
        for c in chain:
            l, round_n = c["list"], min(core.SOLO_ROUND, c["n"])
            if c["passed"]:
                node, note, cls = LOOK_ICONS["check"], f'passed &middot; {c["n"]} questions', " passed"
            elif c["unlocked"]:
                node, note, cls = LOOK_ICONS["play"], f'{c["need"]} of {round_n} right to pass', " open"
            else:
                node, note, cls = LOOK_ICONS["lock"], "pass the step before it", " locked"
            inner = (f'<span class="lad-node"><svg viewBox="0 0 24 24" aria-hidden="true">{node}</svg></span>'
                     f'<span class="lad-card"><span class="lad-txt"><span class="lad-no">Step {c["step"]}</span>'
                     f'<span class="lad-t">{E(l["title"])}</span><span class="lad-n">{note}</span></span>'
                     + ('<span class="lad-go">Play</span>' if cls == " open" else "") + '</span>')
            steps += (f'<li class="lad-step{cls}"><a href="{base}&amp;l={l["id"]}">{inner}</a></li>'
                      if c["unlocked"] else f'<li class="lad-step{cls}"><div>{inner}</div></li>')
        done = sum(1 for c in chain if c["passed"])
        back = (f'{base}&amp;kind={E(kind)}'
                if kind in BY_BOOK and book is not None else base)
        pct = round(100 * done / len(chain)) if chain else 0
        return (f'<p class="pl-back"><a href="{back}">&larr; Back</a></p>'
                f"<h2>{E(title)}</h2>"
                + (f'<div class="lad-sum"><span><strong>{done} of {len(chain)}</strong> passed &middot; '
                   f'step {min(done + 1, len(chain))} is next</span>'
                   f'<span class="pl-bar"><i style="width:{pct}%"></i></span></div>' if chain else "")
                + (f'<ol class="lad {E(kind)}">{steps}</ol>' if steps else
                   '<div class="empty-state">' + look_icon("list", "empty-ico") + '<p><strong>No lists here yet.'
                   '</strong><br>Your teacher will add some.</p></div>'))

    live = core.live_game(db, s["group_id"])
    banner = (f'<a class="card playlive" href="/s/{E(token)}/game"><strong>Your '
              f'teacher\'s game is on.</strong> Join it now &rarr;</a>' if live else "")
    counts = {k: len(core.play_lists(db, s, k)) for k in KIND_NAME}
    passed = core.passed_lists(db, s["id"])
    got = {k: sum(1 for l in core.play_lists(db, s, k) if l["id"] in passed)
           for k in KIND_NAME}
    # a door only appears once there is something behind it
    icons = {"vocab": "message", "grammar": "layers", "exam": "clipboard"}
    doors = "".join(
        f'<a class="pl-door {k}" href="{base}&amp;kind={k}">{look_icon(icons[k], "pl-door-ico")}'
        f'<span class="pl-door-t">{KIND_NAME[k]}</span>'
        f'<span class="pl-door-m">{got[k]} of {counts[k]} steps passed</span>'
        f'<span class="pl-bar light"><i style="width:{round(100 * got[k] / counts[k])}%"></i></span></a>'
        for k in ("vocab", "grammar", "exam") if counts[k])
    # the fourth door: racing a classmate rather than the ladder
    waiting = len(core.open_invites(db, s))
    rec = core.battle_record(db, s["id"])
    doors += (f'<a class="pl-door battle" href="/s/{E(token)}?tab=battle">{look_icon("bolt", "pl-door-ico")}'
              f'<span class="pl-door-t">Battle</span>'
              f'<span class="pl-door-m">'
              + (f'{waiting} challenge{"" if waiting == 1 else "s"} waiting!'
                 if waiting else
                 (f'{rec["wins"]} win{"" if rec["wins"] == 1 else "s"} this week'
                  if rec["races"] else "race a classmate"))
              + '</span>' + (f'<span class="pl-ping">{waiting}</span>' if waiting else "") + '</a>')
    week = core.solo_week_board(db, s["group_id"])
    items = [{"place": i, "name": r["name"], "value": "%d" % r["points"], "unit": "points",
              "meta": "%d step%s passed this week" % (r["mastered"], "" if r["mastered"] == 1 else "s"),
              "me": r["id"] == s["id"]} for i, r in enumerate(week[:10], 1)]
    return f"""<h2>Play</h2>
{banner}
<div class="pl-doors">{doors}</div>
<h3 class="gap-4">This week's champions</h3>
{podium(items)}{rank_list(items) if items else
 '<div class="empty-state">' + look_icon("trophy", "empty-ico")
 + '<p><strong>Nobody has played yet this week.</strong><br>Pass a step and your name goes here first.</p></div>'}
<p class="sub gap-3">Each section is a ladder: pass a step to open the next one.
Passing means {core.SOLO_PASS}% right &mdash; {core.pass_mark(core.SOLO_ROUND)} out of
{core.SOLO_ROUND}. The table counts the steps you passed this week and starts again
every Monday; the steps themselves stay passed. This is just for fun: it is not
part of the league.</p>"""


def act_solo_start(req, db, token):
    s = core.student_by_token(db, token)
    if not s:
        return not_found()
    lid = (req["form"].get("list", [""])[0] or "")
    rid = core.start_solo(db, s, int(lid)) if lid.isdigit() else None
    if not rid:
        return redirect(f"/s/{token}?tab=play")
    return redirect(f"/s/{token}/solo/{rid}")


def solo_state_json(req, db, token, rid):
    s = core.student_by_token(db, token)
    st = core.solo_state(db, rid, s["id"]) if s else None
    return json_response(st or {"state": "gone"})


def act_solo_answer(req, db, token, rid):
    s = core.student_by_token(db, token)
    if not s:
        return json_response({"ok": False})
    f = req["form"]
    q, c = (f.get("q", [""])[0] or ""), (f.get("choice", [""])[0] or "")
    if not (q.isdigit() and c.lstrip("-").isdigit()):
        return json_response({"ok": False})
    r = core.answer_solo(db, rid, s["id"], int(q), int(c))
    return json_response(dict(r, ok=True) if r else {"ok": False})


def view_solo(req, db, token, rid):
    """The phone, alone: the live game's four targets, with nobody hosting."""
    s = core.student_by_token(db, token)
    if not s:
        return not_found()
    run = db.execute("SELECT r.*, l.title, l.kind, l.source FROM solo_runs r"
                     " JOIN word_lists l ON l.id=r.list_id"
                     " WHERE r.id=? AND r.student_id=?", (rid, s["id"])).fetchone()
    if not run:
        return redirect(f"/s/{token}?tab=play")
    body = f"""<div class="solo-stage"><p class="solotitle">{E(run["title"])}</p>
<div id="bar" class="solobar"></div>
<div id="play"></div></div>
<script>
const TOK = {json.dumps(token)}, RID = {rid}, LIST = {run["list_id"]};
const SENTENCE = {json.dumps(run["kind"] == "grammar")};
const KIND = {json.dumps(run["kind"])};
const BOOK = {json.dumps((run["source"] or "").strip() if run["kind"] == "vocab" else None)};
const SHAPES = ['\u25B2', '\u25C6', '\u25CF', '\u25A0'];
const SECS = {core.SOLO_SECONDS};
let st = null, ticker = null, busy = false, ac = null;
function esc(x) {{ return String(x).replace(/[&<>"]/g, c =>
  ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}})[c]); }}
function beep(freq, ms, type) {{
  try {{
    ac = ac || new (window.AudioContext || window.webkitAudioContext)();
    const o = ac.createOscillator(), g = ac.createGain();
    o.type = type || 'sine'; o.frequency.value = freq;
    g.gain.setValueAtTime(0.14, ac.currentTime);
    g.gain.exponentialRampToValueAtTime(0.0001, ac.currentTime + ms / 1000);
    o.connect(g); g.connect(ac.destination); o.start(); o.stop(ac.currentTime + ms / 1000);
  }} catch (e) {{}}
}}
function bar() {{
  document.getElementById('bar').innerHTML =
    '<span>Question ' + Math.min(st.number + 1, st.total) + ' of ' + st.total + '</span>' +
    (st.streak >= 2 ? '<span>' + st.streak + ' in a row 🔥</span>' : '<span></span>') +
    '<span><strong>' + st.score + '</strong> points</span>' +
    '<span class="sprog"><i style="width:' + Math.round(100 * st.number / st.total) + '%"></i></span>';
}}
async function load() {{
  const r = await fetch('/s/' + TOK + '/solo/' + RID + '.json', {{cache: 'no-store'}});
  st = await r.json();
  show();
}}
function show() {{
  clearInterval(ticker);
  const el = document.getElementById('play');
  if (st.state === 'done') {{
    document.getElementById('bar').innerHTML = '';
    const wrong = st.review.filter(x => !x.right);
    el.innerHTML =
      '<div class="gcard ' + (st.passed ? 'right' : 'wrong') + '">' +
      '<div class="gsmall">' + (st.passed ? 'Step passed' : 'Not passed') + '</div>' +
      '<div class="gbig">' + st.correct + ' of ' + st.total + '</div>' +
      '<div class="gsmall">' + (st.passed ? 'the next step is open'
        : 'you need ' + st.need + ' to pass') + '</div>' +
      '<div class="gsmall gap-2">' + st.score + ' points</div></div>' +
      (wrong.length ? '<h3>Look at these again</h3><div class="card solorev">' +
        wrong.map(x => '<p><span class="sub">' + esc(x.term) + '</span><br>' +
          '<strong>' + esc(x.answer) + '</strong>' +
          (x.given ? ' <span class="sub">(you chose ' + esc(x.given) + ')</span>'
                   : ' <span class="sub">(time ran out)</span>') + '</p>').join('') +
        '</div>' : '<p>Every one right. 🎉</p>') +
      '<form method="post" action="/s/' + TOK + '/solo/start">' +
      '<input type="hidden" name="list" value="' + LIST + '">' +
      '<button class="big">' + (st.passed ? 'Play it again' : 'Try again') +
      '</button></form>' +
      '<p class="gap-3"><a class="tab" href="/s/' + TOK + '?tab=play&amp;kind=' + KIND +
      (BOOK === null ? '' : '&amp;book=' + (encodeURIComponent(BOOK) || '-')) +
      '">' + (st.passed ? 'Next step' : 'Back to the steps') + '</a></p>';
    return;
  }}
  if (st.state !== 'question') {{ location.href = '/s/' + TOK + '?tab=play'; return; }}
  bar();
  let left = st.left;
  el.innerHTML =
    '<div class="gcard"><div class="gclock" id="clock">' + left + '</div>' +
    '<div class="gword' + (SENTENCE ? ' solo' : '') + '">' + esc(st.term) + '</div>' +
    '<div class="gtime"><i id="gtime" style="width:' + Math.round(100 * left / SECS) + '%"></i></div></div>' +
    '<div class="gopts">' + st.options.map((o, i) =>
      '<button class="gopt c' + i + '" onclick="pick(' + i + ')">' +
      '<span class="gshape">' + SHAPES[i] + '</span>' + esc(o) + '</button>').join('') +
    '</div>';
  busy = false;
  ticker = setInterval(() => {{
    left -= 1;
    const c = document.getElementById('clock');
    if (c) c.textContent = Math.max(0, left);
    const g = document.getElementById('gtime');
    if (g) {{ g.style.width = Math.max(0, Math.round(100 * left / SECS)) + '%'; g.classList.toggle('low', left <= 5); }}
    if (left <= 5 && left > 0) beep(880, 60);
    if (left <= 0) {{ clearInterval(ticker); pick(-1); }}
  }}, 1000);
}}
async function pick(i) {{
  if (busy) return;
  busy = true; clearInterval(ticker);
  document.querySelectorAll('.gopt').forEach(b => {{ b.disabled = true; b.classList.add('off'); }});
  const r = await fetch('/s/' + TOK + '/solo/' + RID + '/answer', {{method: 'POST',
    headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
    body: 'q=' + st.q + '&choice=' + i}});
  const a = await r.json();
  if (!a.ok) {{ load(); return; }}
  if (a.correct) {{ beep(660, 90); setTimeout(() => beep(990, 140), 100); }}
  else beep(180, 220, 'square');
  document.getElementById('play').innerHTML =
    '<div class="gcard ' + (a.correct ? 'right' : 'wrong') + '">' +
    '<div class="gbig">' + (a.correct ? 'Correct' : (i < 0 || a.late ? 'Time up' : 'Not this time')) + '</div>' +
    '<div class="gsmall">' + esc(st.term) + '</div>' +
    '<div class="soloans">' + esc(a.answer_text) + '</div>' +
    (a.points ? '<div class="gsmall">+' + a.points + ' points</div>' : '') + '</div>';
  setTimeout(load, a.correct ? 1300 : 2600);
}}
load();
</script>"""
    return html_response(student_page(run["title"], body))


def portal_battle(db, s, token, query):
    """The Battle door: start a race, join one by code, or answer an invitation."""
    base = f"/s/{E(token)}?tab=battle"
    mine = core.my_open_battle(db, s)
    running = (f'<a class="card playlive" href="/s/{E(token)}/battle/{mine["id"]}">'
               f'<strong>You are in a race.</strong> '
               f'{"Back to the lobby" if mine["state"] == "lobby" else "Back to the track"}'
               f' &rarr;</a>' if mine else "")
    invites = core.open_invites(db, s)
    inv_html = ""
    for i in invites:
        inv_html += (
            f'<div class="card invite"><div><strong>{E(i["from_name"])}</strong> '
            f'challenges you &middot; <span class="sub">{E(i["title"])}</span></div>'
            f'<div class="inviterow">'
            f'<form method="post" action="/s/{E(token)}/battle/join">'
            f'<input type="hidden" name="battle" value="{i["battle_id"]}">'
            f'<button class="big">Accept</button></form>'
            f'<form method="post" action="/s/{E(token)}/battle/decline">'
            f'<input type="hidden" name="battle" value="{i["battle_id"]}">'
            f'<button class="tab">No thanks</button></form></div></div>')

    lists = core.battle_lists(db, s)
    pick = ""
    for l in lists:
        n = db.execute("SELECT COUNT(*) c FROM words WHERE list_id=?",
                       (l["id"],)).fetchone()["c"]
        if n < 4:
            continue
        label = (l["source"] or KIND_NAME.get(l["kind"], "")).strip()
        pick += (f'<option value="{l["id"]}">{E(l["title"])}'
                 + (f' &mdash; {E(label)}' if label else "") + '</option>')

    rec = core.battle_record(db, s["id"])
    board = core.battle_week_board(db, s["group_id"])
    items = [{"place": i, "name": r["name"], "value": "%d" % r["points"], "unit": "points",
              "meta": "%d win%s · %d race%s" % (r["wins"], "" if r["wins"] == 1 else "s",
                                                r["races"], "" if r["races"] == 1 else "s"),
              "me": r["id"] == s["id"]} for i, r in enumerate(board[:10], 1)]
    mine_line = (f'This week: <strong>{rec["wins"]}</strong> win'
                 f'{"" if rec["wins"] == 1 else "s"} from {rec["races"]} race'
                 f'{"" if rec["races"] == 1 else "s"}.'
                 if rec["races"] else "You have not raced yet this week.")
    return f"""<p class="pl-back"><a href="/s/{E(token)}?tab=play">&larr; Play</a></p>
<div class="pl-hero battle">
  <span class="pl-hero-k">{look_icon("bolt", "pl-ok")} Battle</span>
  <h2 class="pl-hero-t">Race your classmates</h2>
  <p class="pl-hero-p">Up to {core.BATTLE_MAX} of you race through the same
  {core.BATTLE_ROUND} questions. Everyone runs at their own speed and you watch
  each other move. Fastest right answers win.</p>
  <p class="pl-hero-me">{mine_line}</p>
</div>
{running}{inv_html}
{"" if mine else f'''<div class="bt-pair"><div class="card bt-card">
<h3 class="flush">Start a race</h3>
<form method="post" action="/s/{E(token)}/battle/new" class="battlestart">
<label class="lab" for="blist">Topic</label>
<select id="blist" name="list" required>{pick}</select>
<button class="big gap-2">Open a lobby</button></form>
{"" if pick else '<p class="sub">No topics are open to your class yet.</p>'}
</div>
<div class="card bt-card">
<h3 class="flush">Join a race</h3>
<p class="sub">Type the four letters your classmate reads out.</p>
<form method="post" action="/s/{E(token)}/battle/code" class="battlecode">
<input name="code" maxlength="4" autocapitalize="characters" autocomplete="off"
 spellcheck="false" placeholder="ABCD" required>
<button class="big">Join</button></form>
</div></div>'''}
<h3 class="gap-4">This week's racers</h3>
{podium(items)}{rank_list(items) if items else '<div class="empty-state">' + look_icon("bolt", "empty-ico")
 + '<p><strong>Nobody has raced yet this week.</strong><br>Be the first.</p></div>'}
<p class="sub gap-3">The table starts again every Monday. Like Play, battles are
just for fun: they are not part of the league, and they do not open career steps.</p>"""


def act_battle_new(req, db, token):
    s = core.student_by_token(db, token)
    if not s:
        return not_found()
    lid = (req["form"].get("list", [""])[0] or "")
    bid = core.create_battle(db, s, int(lid)) if lid.isdigit() else None
    if not bid:
        return redirect(f"/s/{token}?tab=battle")
    return redirect(f"/s/{token}/battle/{bid}")


def act_battle_code(req, db, token):
    s = core.student_by_token(db, token)
    if not s:
        return not_found()
    b = core.battle_by_code(db, (req["form"].get("code", [""])[0] or ""))
    bid = core.join_battle(db, s, b["id"]) if b else None
    if not bid:
        return redirect(f"/s/{token}?tab=battle&e=code")
    return redirect(f"/s/{token}/battle/{bid}")


def act_battle_join(req, db, token):
    s = core.student_by_token(db, token)
    if not s:
        return not_found()
    raw = (req["form"].get("battle", [""])[0] or "")
    bid = core.join_battle(db, s, int(raw)) if raw.isdigit() else None
    if not bid:
        return redirect(f"/s/{token}?tab=battle&e=full")
    return redirect(f"/s/{token}/battle/{bid}")


def act_battle_decline(req, db, token):
    s = core.student_by_token(db, token)
    if not s:
        return not_found()
    raw = (req["form"].get("battle", [""])[0] or "")
    if raw.isdigit():
        core.decline_invite(db, s, int(raw))
    return redirect(f"/s/{token}?tab=battle")


def act_battle_invite(req, db, token, bid):
    s = core.student_by_token(db, token)
    if not s:
        return json_response({"ok": False})
    raw = (req["form"].get("who", [""])[0] or "")
    ok = core.invite_to_battle(db, s, bid, int(raw)) if raw.isdigit() else False
    return json_response({"ok": bool(ok)})


def act_battle_start(req, db, token, bid):
    s = core.student_by_token(db, token)
    if not s:
        return json_response({"ok": False})
    return json_response({"ok": core.start_battle(db, bid, s["id"])})


def act_battle_leave(req, db, token, bid):
    s = core.student_by_token(db, token)
    if not s:
        return not_found()
    core.leave_battle(db, s, bid)
    return redirect(f"/s/{token}?tab=battle")


def act_battle_answer(req, db, token, bid):
    s = core.student_by_token(db, token)
    if not s:
        return json_response({"ok": False})
    f = req["form"]
    q, c = (f.get("q", [""])[0] or ""), (f.get("choice", [""])[0] or "")
    if not (q.isdigit() and c.lstrip("-").isdigit()):
        return json_response({"ok": False})
    r = core.answer_battle(db, bid, s["id"], int(q), int(c))
    return json_response(dict(r, ok=True) if r else {"ok": False})


def battle_state_json(req, db, token, bid):
    s = core.student_by_token(db, token)
    if not s:
        return json_response({"state": "gone"})
    core.touch_student(db, s["id"])
    st = core.battle_state(db, bid, s["id"])
    if st and st["state"] == "lobby":
        st["mates"] = core.classmates_for_battle(db, s)
        st["invited"] = [r["to_id"] for r in db.execute(
            "SELECT to_id FROM battle_invites WHERE battle_id=?", (bid,)).fetchall()]
    return json_response(st or {"state": "gone"})


def view_battle(req, db, token, bid):
    """The lobby, then the track, then the finish: one page that follows the race."""
    s = core.student_by_token(db, token)
    if not s:
        return not_found()
    st = core.battle_state(db, bid, s["id"])
    if not st:
        return redirect(f"/s/{token}?tab=battle")
    body = f"""<div id="head"></div>
<div id="play"></div>
<script>
const TOK = {json.dumps(token)}, BID = {bid};
const SHAPES = ['▲', '◆', '●', '■'];
const CARS = ['●', '◆', '▲', '■'];
let st = null, ticker = null, poller = null, busy = false, ac = null, lastAt = {{}};
function esc(x) {{ return String(x).replace(/[&<>"]/g, c =>
  ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}})[c]); }}
function beep(freq, ms, type) {{
  try {{
    ac = ac || new (window.AudioContext || window.webkitAudioContext)();
    const o = ac.createOscillator(), g = ac.createGain();
    o.type = type || 'sine'; o.frequency.value = freq;
    g.gain.setValueAtTime(0.14, ac.currentTime);
    g.gain.exponentialRampToValueAtTime(0.0001, ac.currentTime + ms / 1000);
    o.connect(g); g.connect(ac.destination); o.start(); o.stop(ac.currentTime + ms / 1000);
  }} catch (e) {{}}
}}
function track(showScore) {{
  return '<div class="track">' + st.track.map((t, i) => {{
    const pct = st.total ? Math.round(100 * t.at / st.total) : 0;
    const moved = lastAt[t.id] !== undefined && lastAt[t.id] !== t.at;
    lastAt[t.id] = t.at;
    return '<div class="lane' + (t.me ? ' me' : '') + (t.home ? ' home' : '') + '">' +
      '<div class="lanetop"><span class="who">' +
        (t.place ? '<span class="place">' + t.place + '</span> ' : '') +
        esc(t.name) + (t.me ? ' <span class="sub">(you)</span>' : '') + '</span>' +
      '<span class="num">' + (showScore ? t.score + ' pts' : t.at + '/' + st.total) +
      '</span></div>' +
      '<div class="rail"><div class="fill c' + (i % 4) + '" style="width:' + pct + '%">' +
      '</div><span class="car' + (moved ? ' bump' : '') + '" style="left:' + pct + '%">' +
      CARS[i % 4] + '</span></div></div>';
  }}).join('') + '</div>';
}}
async function load() {{
  const r = await fetch('/s/' + TOK + '/battle/' + BID + '.json', {{cache: 'no-store'}});
  st = await r.json();
  show();
}}
function poll(ms) {{
  clearInterval(poller);
  poller = setInterval(async () => {{
    const r = await fetch('/s/' + TOK + '/battle/' + BID + '.json', {{cache: 'no-store'}});
    const next = await r.json();
    const was = st ? st.state : null;
    st = next;
    if (st.state !== was) {{ show(); return; }}
    if (st.state === 'lobby') drawLobby();
    else if (st.state === 'waiting' || st.state === 'done') show();
    else document.getElementById('rail').innerHTML = track(false);
  }}, ms);
}}
function drawLobby() {{
  const full = st.track.length >= st.seats;
  document.getElementById('head').innerHTML =
    '<p class="sub solotitle">' + esc(st.title) + '</p>';
  const mates = (st.mates || []).map(m =>
    '<button class="mate' + (m.online ? ' on' : '') +
    (st.invited.indexOf(m.id) >= 0 ? ' asked' : '') + '"' +
    (st.invited.indexOf(m.id) >= 0 || full ? ' disabled' : '') +
    ' onclick="invite(' + m.id + ')">' + esc(m.name) +
    '<span class="dot"></span></button>').join('');
  document.getElementById('play').innerHTML =
    '<div class="codecard"><div class="gsmall">Race code</div>' +
    '<div class="bigcode">' + esc(st.code) + '</div>' +
    '<div class="gsmall">Read it out, or tap a classmate below</div></div>' +
    '<h3>On the grid (' + st.track.length + ' of ' + st.seats + ')</h3>' +
    '<div class="seats">' + st.track.map((t, i) =>
      '<div class="seat"><span class="car c' + (i % 4) + '">' + CARS[i % 4] + '</span>' +
      esc(t.name) + (t.me ? ' <span class="sub">(you)</span>' : '') + '</div>').join('') +
    '</div>' +
    (mates ? '<h3 class="gap-3">Invite a classmate</h3><div class="mates">' +
      mates + '</div>' : '') +
    (st.host
      ? '<button class="big gap-3"' + (st.can_start ? '' : ' disabled') +
        ' onclick="go()">' + (st.can_start ? 'Start the race'
          : 'Waiting for someone to join') + '</button>'
      : '<p class="gap-3 sub">Waiting for the host to start the race…</p>') +
    '<form method="post" action="/s/' + TOK + '/battle/' + BID + '/leave">' +
    '<button class="tab gap-2">Leave</button></form>';
}}
async function invite(id) {{
  await fetch('/s/' + TOK + '/battle/' + BID + '/invite', {{method: 'POST',
    headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
    body: 'who=' + id}});
  load();
}}
async function go() {{
  await fetch('/s/' + TOK + '/battle/' + BID + '/start', {{method: 'POST',
    headers: {{'Content-Type': 'application/x-www-form-urlencoded'}}, body: ''}});
  load();
}}
function show() {{
  clearInterval(ticker);
  const el = document.getElementById('play');
  if (st.state === 'gone') {{ location.href = '/s/' + TOK + '?tab=battle'; return; }}
  if (st.state === 'lobby') {{ drawLobby(); poll(1500); return; }}
  if (st.state === 'waiting') {{
    document.getElementById('head').innerHTML =
      '<p class="sub solotitle">' + esc(st.title) + '</p>';
    el.innerHTML = '<div class="gcard"><div class="gsmall">You are home</div>' +
      '<div class="gbig">Finished</div><div class="gsmall">' +
      st.left_on_track + ' still racing…</div></div>' +
      '<div id="rail">' + track(true) + '</div>';
    poll(1200);
    return;
  }}
  if (st.state === 'done') {{
    clearInterval(poller);
    document.getElementById('head').innerHTML = '';
    const won = st.place === 1;
    const wrong = (st.review || []).filter(x => !x.right);
    el.innerHTML =
      '<div class="gcard ' + (won ? 'right' : '') + '">' +
      '<div class="gsmall">' + esc(st.title) + '</div>' +
      '<div class="gbig">' + (won ? '🏆 1st' :
        st.place === 2 ? '2nd' : st.place === 3 ? '3rd' : st.place + 'th') + '</div>' +
      '<div class="gsmall">' + st.correct + ' of ' + st.total + ' right · ' +
      st.score + ' points</div></div>' +
      track(true) +
      (wrong.length ? '<h3 class="gap-3">Look at these again</h3>' +
        '<div class="card solorev">' + wrong.map(x =>
          '<p><span class="sub">' + esc(x.term) + '</span><br><strong>' +
          esc(x.answer) + '</strong>' + (x.given
            ? ' <span class="sub">(you chose ' + esc(x.given) + ')</span>'
            : ' <span class="sub">(time ran out)</span>') + '</p>').join('') + '</div>'
        : '<p class="gap-3">Every one right. 🎉</p>') +
      '<p class="gap-3"><a class="tab" href="/s/' + TOK + '?tab=battle">' +
      'Race again</a></p>';
    return;
  }}
  // racing
  document.getElementById('head').innerHTML =
    '<div class="solobar"><span>Question ' + (st.q + 1) + ' of ' + st.total + '</span>' +
    '<span class="sub">' + esc(st.title) + '</span></div>';
  let left = st.left;
  el.innerHTML =
    '<div class="gcard"><div class="gclock" id="clock">' + left + '</div>' +
    '<div class="gword">' + esc(st.term) + '</div></div>' +
    '<div class="gopts">' + st.options.map((o, i) =>
      '<button class="gopt c' + i + '" onclick="pick(' + i + ')">' +
      '<span class="gshape">' + SHAPES[i] + '</span>' + esc(o) + '</button>').join('') +
    '</div><div id="rail">' + track(false) + '</div>';
  busy = false;
  poll(1400);
  ticker = setInterval(() => {{
    left -= 1;
    const c = document.getElementById('clock');
    if (c) c.textContent = Math.max(0, left);
    if (left <= 5 && left > 0) beep(880, 60);
    if (left <= 0) {{ clearInterval(ticker); pick(-1); }}
  }}, 1000);
}}
async function pick(i) {{
  if (busy) return;
  busy = true; clearInterval(ticker);
  document.querySelectorAll('.gopt').forEach(b => {{
    b.disabled = true; b.classList.add('off'); }});
  const r = await fetch('/s/' + TOK + '/battle/' + BID + '/answer', {{method: 'POST',
    headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
    body: 'q=' + st.q + '&choice=' + i}});
  const a = await r.json();
  if (!a.ok) {{ load(); return; }}
  if (a.correct) {{ beep(660, 90); setTimeout(() => beep(990, 140), 100); }}
  else beep(180, 220, 'square');
  const rail = document.getElementById('rail');
  document.getElementById('play').innerHTML =
    '<div class="gcard ' + (a.correct ? 'right' : 'wrong') + '">' +
    '<div class="gbig">' + (a.correct ? '+' + a.points :
      (i < 0 || a.late ? 'Time up' : 'Wrong')) + '</div>' +
    '<div class="gsmall">' + esc(st.term) + '</div>' +
    '<div class="soloans">' + esc(a.answer_text) + '</div></div>' +
    '<div id="rail">' + (rail ? rail.innerHTML : '') + '</div>';
  setTimeout(load, a.correct ? 700 : 1500);
}}
load();
</script>"""
    return html_response(student_page("Battle", body))


def view_student_portal(req, db, token, flash=""):
    s = core.student_by_token(db, token)
    if not s:
        return html_response(student_page("Not found",
            "<h1>Link not recognised</h1><p class='sub'>Ask your teacher for your link.</p>"), 404)
    core.touch_student(db, s["id"])   # so classmates can see who is here to race
    query = (req or {}).get("query", {}) if isinstance(req, dict) else {}
    tab = (query.get("tab", ["home"])[0] or "home")
    if tab == "materials":
        body = portal_materials(db, s, token, query)
    elif tab == "progress":
        body = portal_progress(db, s, token)
    elif tab == "write":
        body = portal_write(db, s, token, query)
    elif tab == "tests":
        body = portal_tests(db, s, token, query)
    elif tab == "play":
        body = portal_play(db, s, token, query)
    elif tab == "battle":
        body = portal_battle(db, s, token, query)
    elif tab == "handouts":
        body = portal_handouts(db, s, token, query)
    elif tab == "feedback":
        body = portal_feedback(db, s, token)
    elif tab == "rate":
        body = portal_rate(db, s, token, query)
    elif tab == "class":
        sc = (query.get("scope", ["class"])[0] or "class")
        body = portal_class(db, s, token, "school" if sc == "school" else "class")
    elif tab == "goal":
        body = portal_goal(db, s, token, flash)
    elif tab == "profile":
        body = portal_profile(db, s, token, flash)
    else:
        tab = "home"
        body = portal_home(db, s, token, flash, query.get("a", [""])[0] or "")
    if core.practice_on():
        # the teacher, going through the page as a student: the strip that
        # does the work for them, except inside the all-screens view
        framed = query.get("frame", [""])[0] == "1"
        return student_shell(s, db, token, tab, body, music=not framed,
                             top="" if framed else practice_bar(db, s, token, tab, query))
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
        # only accept an assignment that is genuinely open for this student's
        # group - a handout or a workbook unit included: its paper copy comes as
        # photographs, and dropping the choice filed them as unassigned
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


def _back(req, default):
    """Where a form wants to return to, if it said and the place is ours."""
    b = (req["form"].get("back", [""])[0] or "").strip()
    return b if b.startswith("/") and not b.startswith("//") else default


def set_url(gid, due):
    return "/homework/set?" + urllib.parse.urlencode({"group": gid, "due": due or ""})


def due_words(due_at, cfg):
    """A deadline as a teacher reads it at the start of a lesson: the day,
    the time, and how far away it is."""
    if not due_at:
        return "no deadline", ""
    day, clock = core.deadline_parts(due_at, cfg)
    when = core.parse(due_at)
    today = datetime.strptime(core.local_day(core.now(), cfg), "%Y-%m-%d").date()
    gap = (datetime.strptime(day, "%Y-%m-%d").date() - today).days
    if gap == 0:
        rel = "today"
    elif gap == 1:
        rel = "tomorrow"
    elif gap == -1:
        rel = "yesterday"
    elif gap > 1:
        rel = "in %d days" % gap
    else:
        rel = "%d days ago" % -gap
    nice = (when + timedelta(hours=cfg["timezone_offset_hours"])).strftime("%a %-d %b")
    return f"{nice} at {clock}", rel


def batch_state(r, due):
    """closed, draft, past due or open - the one word that says what a batch
    needs from the teacher."""
    if r["shut"] == 1:
        return "closed", '<span class="pill mute">closed</span>'
    if r["pubmax"] == 0:
        return "draft", '<span class="pill mute">draft</span>'
    if not core.still_open(due):
        return "past", '<span class="pill watch">deadline passed</span>'
    return "open", '<span class="pill">open</span>'


def view_homework(req, db):
    """Everything set, one line each, with the three things a teacher does
    to a piece of homework: see who has done it, change it, delete it."""
    cfg = core.load_config()
    q = req["query"]
    show = (q.get("show", ["open"])[0] or "open")
    if show not in ("open", "closed", "all"):
        show = "open"
    gid_s = (q.get("group", [""])[0] or "").strip()
    gid = int(gid_s) if gid_s.isdigit() else None
    groups = db.execute("SELECT * FROM groups WHERE archived=0 ORDER BY name").fetchall()

    rows = []
    for r in core.all_sets(db):
        if gid and r["group_id"] != gid:
            continue
        items = core.set_items(db, r["group_id"], r["due_at"])
        if not items:
            continue
        key, pill = batch_state(r, r["due_at"])
        if show == "open" and key == "closed":
            continue
        if show == "closed" and key != "closed":
            continue
        if not all(a["in_league"] for a in items):
            pill += ' <span class="pill mute">not in the league</span>'
        rows.append((r, items, key, pill))
    # What is coming up, soonest first, is what a lesson opens with; what
    # has passed follows, most recent first, so last week's is one glance
    # down and the term's back catalogue is at the bottom.
    order = {"open": 0, "draft": 1, "past": 2, "closed": 3}
    heading = {"open": "Coming up", "draft": "Drafts, not yet sent",
               "past": "Deadline passed", "closed": "Closed"}
    def when_key(t):
        due = t[0]["due_at"]
        return (due is None, due or "") if t[2] == "open" else (due is None,)
    rows.sort(key=lambda t: (order[t[2]],) + when_key(t))
    for k in ("draft", "past", "closed"):
        part = [t for t in rows if t[2] == k]
        part.sort(key=lambda t: (t[0]["due_at"] is None, t[0]["due_at"] or ""), reverse=True)
        rows = [t for t in rows if t[2] != k] + part
    rows.sort(key=lambda t: order[t[2]])          # stable: keeps each part's order

    here = f"/homework?show={show}" + (f"&group={gid}" if gid else "")
    lines = ""
    last_key = None
    for r, items, key, pill in rows:
        if key != last_key:
            n = sum(1 for t in rows if t[2] == key)
            lines += f'<h2 class="hwhead">{heading[key]} <span class="sub">{n}</span>'
            if key == "past":
                # One press for the whole pile: the pieces keep every mark
                # and every photo, they just stop being open.
                where = ("everything" if gid is None
                         else f"everything for {group_name(db, gid)}")
                lines += (f'<form method="post" action="/assignments/close-past" '
                          f'class="hwclose" onsubmit="return confirm('
                          f'{json.dumps("Close %s past its deadline? %d piece(s). Marks and photos are kept." % (where, n))})">'
                          f'<input type="hidden" name="group_id" value="{gid or ""}">'
                          f'<input type="hidden" name="back" value="{E(here)}">'
                          f'<button class="ghost">Close all {n} past their deadline</button>'
                          f'</form>')
            lines += '</h2>'
            last_key = key
        g = r["group_id"]
        due = r["due_at"]
        when, rel = due_words(due, cfg)
        prog = core.group_set_progress(db, g, items)
        done = sum(1 for p in prog if p["percent"] == 100)
        none = sum(1 for p in prog if not p["done"])
        total = len(prog)
        pct = int(100 * done / total) if total else 0
        titles = ", ".join(a["title"] for a in items[:3])
        if len(items) > 3:
            titles += " and %d more" % (len(items) - 3)
        detail = set_url(g, due)
        warn = ("Delete this homework for %s? Students' marked work is kept."
                % group_name(db, g))
        lines += f"""<div class="hw">
  <div class="hw-main">
    <div class="hw-title"><a href="{detail}"><strong>{E(group_name(db, g))}</strong></a>
      &middot; {E(when)}{f' <span class="rel">({E(rel)})</span>' if rel else ''} {pill}</div>
    <div class="sub">{len(items)} item{"" if len(items) == 1 else "s"}: {E(titles)}</div>
  </div>
  <div class="hw-done">
    <div class="pbar"><i style="width:{pct}%"></i></div>
    <div class="n"><strong>{done} of {total}</strong> done everything
      {f'&middot; <span class="bad">{none} sent nothing</span>' if none else ''}</div>
  </div>
  <div class="hw-acts">
    <a class="btn" href="{detail}">Who's done it</a>
    <a class="btn ghost" href="{detail}#manage">Change</a>
    <form method="post" action="/assignments/batch/delete"
      onsubmit="return confirm({json.dumps(warn)})">
      <input type="hidden" name="group_id" value="{g}">
      <input type="hidden" name="due" value="{E(due or "")}">
      <input type="hidden" name="back" value="{E(here)}">
      <button class="ghost danger">Delete</button></form>
  </div>
</div>"""

    def tab(href, label, on):
        return f'<a class="tab{" on" if on else ""}" href="{href}">{E(label)}</a>'
    gq = f"&group={gid}" if gid else ""
    states = ('<div class="tabs">'
              + tab(f"/homework?show=open{gq}", "Open", show == "open")
              + tab(f"/homework?show=closed{gq}", "Closed", show == "closed")
              + tab(f"/homework?show=all{gq}", "Everything", show == "all") + "</div>")
    classes = ('<div class="tabs">'
               + tab(f"/homework?show={show}", "All classes", gid is None)
               + "".join(tab(f'/homework?show={show}&group={g["id"]}', g["name"],
                             gid == g["id"]) for g in groups) + "</div>")
    if not lines:
        what = {"open": "No open homework", "closed": "Nothing closed yet",
                "all": "Nothing set yet"}[show]
        lines = (f'<div class="card"><p class="sub flush">{what}. '
                 f'Set some on the <a class="linky" href="/assignments">Set homework</a> '
                 f'page.</p></div>')
    just = (q.get("closed", [""])[0] or "").strip()
    flash = ""
    if just.isdigit():
        n = int(just)
        flash = (f'<p class="flash">Closed {n} piece{"" if n == 1 else "s"} of homework. '
                 f'They are under <a class="linky" href="/homework?show=closed">Closed</a>.</p>'
                 if n else '<p class="flash">Nothing was past its deadline.</p>')
    body = f"""<h1>Homework</h1>
<p class="sub">Everything you have set, nearest deadline first. Open one to see who has
done it before the lesson starts.</p>
{flash}<div class="toolbar">{classes}{states}</div>
<div class="hwlist">{lines}</div>"""
    return html_response(page("Homework", body, "Homework"))


def view_homework_set(req, db):
    """One piece of homework: who has done it, who has not, and every way
    to change it. The lists come first because that is what the lesson
    opens with; the controls sit below under "Change"."""
    cfg = core.load_config()
    q = req["query"]
    gid_s = (q.get("group", [""])[0] or "").strip()
    if not gid_s.isdigit():
        return not_found()
    gid = int(gid_s)
    due = (q.get("due", [""])[0] or "").strip() or None
    g = db.execute("SELECT * FROM groups WHERE id=?", (gid,)).fetchone()
    items = core.set_items(db, gid, due)
    if not g or not items:
        return not_found()
    r = db.execute(
        "SELECT group_id, due_at, COUNT(*) n, MIN(published) pub, MAX(published) pubmax,"
        " MIN(closed) shut, MAX(closed) shutmax FROM assignments"
        " WHERE group_id=? AND " + ("due_at IS NULL" if due is None else "due_at=?")
        + " GROUP BY group_id, due_at", (gid,) if due is None else (gid, due)).fetchone()
    key, pill = batch_state(r, due)
    if not all(a["in_league"] for a in items):
        pill += ' <span class="pill mute">not in the league</span>'
    when, rel = due_words(due, cfg)
    here = set_url(gid, due)

    prog = core.group_set_progress(db, gid, items)
    finished = [p for p in prog if p["percent"] == 100]
    partly = [p for p in prog if p["done"] and p["percent"] != 100]
    nothing = [p for p in prog if not p["done"]]
    partly.sort(key=lambda p: (p["done"], p["student"]["name"]))

    def names(group, missing=False):
        if not group:
            return '<li class="sub">nobody</li>'
        out = ""
        for p in sorted(group, key=lambda p: p["student"]["name"]):
            st = p["student"]
            extra = ""
            if missing:
                left = ", ".join(a["title"] for a in p["remaining"])
                extra = (f'<div class="sub">{p["done"]} of {p["total"]} &middot; '
                         f'missing {E(left)}</div>')
            out += f'<li><a href="/students/{st["id"]}">{E(st["name"])}</a>{extra}</li>'
        return out

    who = f"""<div class="who">
  <div class="card bad"><h3>Not started <span class="count">{len(nothing)}</span></h3>
    <ul>{names(nothing)}</ul></div>
  <div class="card mid"><h3>Partly done <span class="count">{len(partly)}</span></h3>
    <ul>{names(partly, missing=True)}</ul></div>
  <div class="card good"><h3>Done <span class="count">{len(finished)}</span></h3>
    <ul>{names(finished)}</ul></div>
</div>"""

    head = "".join(f'<th title="{E(a["title"])}">{E(a["title"][:14])}</th>' for a in items)
    handouts = {a["id"]: a["test_id"] for a in items if core.is_handout(db, a["test_id"])}

    def cell(a, p):
        if a["id"] in p.get("excused_ids", ()):
            return ('<td class="tick"><span class="pill mute" title="before they joined, or let off it">'
                    'not needed</span></td>')
        tid = handouts.get(a["id"])
        if tid:
            # a handout marks itself: its mark once the deadline has gone, the
            # parts done until then - or, done on paper, where the tick stands
            hw = core.handout_homework(db, a, p["student"]["id"])
            st, paper = hw["digital"], hw["paper"]
            if paper and hw["route"] != "digital":
                shown, cls = {"waiting": ("paper", ""), "ticked": ("%g" % (paper["mark"] or 0), " good"),
                              "late": ("late", " risk"), "rejected": ("&#10007;", " risk")}[paper["state"]]
                what = {"waiting": "sent on paper, waiting for your tick",
                        "ticked": "done on paper, ticked", "late": "sent on paper after the deadline",
                        "rejected": "on paper, not complete"}[paper["state"]]
                return (f'<td class="tick"><span class="pill{cls}" title="{what}">&#128196; {shown}'
                        f'</span></td>')
            if not st["started"]:
                return '<td class="tick"><span class="mute">&#11036;</span></td>'
            past = not core.still_open(due)
            shown = (f'{st["mark"]:g}' if past or st["done"] else f'{st["parts"]}/{st["total"]}')
            flag = ' <span class="pill risk">void</span>' if st["voided"] else ""
            return (f'<td class="tick"><span class="pill{" good" if st["done"] else ""}"'
                    f' title="{st["parts"]} of {st["total"]} parts, {st["mark"]:g} out of 10">'
                    f'{shown}</span>{flag}</td>')
        return ('<td class="tick">' + ("&#9989;" if a["id"] in p["done_ids"] else
                                       '<span class="mute">&#11036;</span>') + "</td>")
    grid = ""
    for p in prog:
        cells = "".join(cell(a, p) for a in items)
        cls = "pill risk" if p["percent"] < 50 else "pill"
        grid += (f'<tr><td><a href="/students/{p["student"]["id"]}">'
                 f'{E(p["student"]["name"])}</a></td>{cells}'
                 f'<td><span class="{cls}">{p["percent"]}%</span></td></tr>')

    # ------------------------------------------------------------ change it
    key_fields = (f'<input type="hidden" name="group_id" value="{gid}">'
                  f'<input type="hidden" name="due" value="{E(due or "")}">'
                  f'<input type="hidden" name="back" value="{E(here)}">')
    def form(action, label, cls="ghost", confirm=None, back=here):
        ask = f' onsubmit="return confirm({json.dumps(confirm)})"' if confirm else ""
        fields = key_fields.replace(f'value="{E(here)}"', f'value="{E(back)}"')
        return (f'<form method="post" action="/assignments/batch/{action}"{ask}>'
                f'{fields}<button class="{cls}">{label}</button></form>')
    counts = all(a["in_league"] for a in items)
    graded = core.set_graded_count(db, gid, due)
    buttons = ""
    if key == "draft":
        buttons += form("publish", "Publish to students", "")
    elif key == "closed":
        buttons += form("open", "Reopen")
    else:
        buttons += form("close", "Close")
    buttons += form("league", "Count in the league" if not counts
                    else "Leave out of the league")
    warn = ("Delete all %d item(s)? %d marked piece(s) stay with the student and "
            "keep their score - they just stop being linked to this homework."
            % (len(items), graded)) if graded else \
           "Delete all %d item(s)? Nothing has been handed in." % len(items)
    buttons += form("delete", "Delete this homework", "ghost danger", warn,
                    back="/homework")

    day, clock = core.deadline_parts(due, cfg)
    item_rows = ""
    for a in items:
        n = db.execute("SELECT COUNT(*) c FROM submissions WHERE assignment_id=?",
                       (a["id"],)).fetchone()["c"]
        if a["id"] in handouts:
            n = sum(1 for p in prog
                    if core.handout_status(db, handouts[a["id"]], p["student"]["id"])["started"])
        if a["closed"]:
            flip = ("open", "reopen")
        elif not a["published"]:
            flip = ("publish", "publish")
        else:
            flip = ("close", "close")
        item_rows += f"""<tr><td>
  <form method="post" action="/assignments/{a["id"]}/edit" class="inline rename">
    <input name="title" value="{E(a["title"])}" aria-label="Title">
    <input type="hidden" name="due" value="{E(day)}">
    <input type="hidden" name="due_time" value="{E(clock)}">
    <input type="hidden" name="back" value="{E(here)}">
    <button class="ghost">Save</button></form></td>
  <td class="sub">{E(a["task_type"])}{" &middot; criteria" if a["rubric"] else ""}</td>
  <td class="sub">{n} in</td>
  <td class="rowacts">
    <form method="post" action="/assignments/{a["id"]}/{flip[0]}">
      <input type="hidden" name="back" value="{E(here)}">
      <button class="linky">{flip[1]}</button></form>
    <form method="post" action="/assignments/{a["id"]}/delete"
      onsubmit="return confirm({json.dumps("Delete " + a["title"] + "?")})">
      <input type="hidden" name="back" value="{E(here)}">
      <button class="linky danger">delete</button></form></td></tr>"""

    today = core.local_day(core.now(), cfg)
    past = ('<div class="card bad gap-2"><strong>That deadline has already passed.</strong> '
            'Nothing was moved &mdash; choose a date and time that is still to come.</div>'
            if q.get("pastdue") else "")
    manage = f"""<h2 id="manage">Change it</h2>
{past}<div class="card">
<div class="batchacts">{buttons}</div>
<form method="post" action="/assignments/batch/edit" class="inline gap-4">
{key_fields}
<label class="f">New deadline<input type="date" name="new_due" value="{E(day)}" min="{today}"></label>
<label class="f">at<input type="time" name="new_time" value="{E(clock or "23:59")}" step="60"></label>
<label class="f pushed">&nbsp;<button class="ghost">Move the deadline</button></label>
</form>
<p class="sub gap-2">Moves every item together. Leaving it out of the league keeps it
on the students' page and keeps your marks &mdash; it simply stops awarding points.</p>
<div class="tablewrap gap-3"><table>
<tr><th>Item</th><th>Type</th><th>Sent</th><th></th></tr>{item_rows}</table></div>
</div>"""

    body = f"""<p class="crumb"><a href="/homework">&larr; All homework</a></p>
<h1>{E(g["name"])} &middot; {E(when)} {pill}</h1>
<p class="sub">{f"{E(rel)} &middot; " if rel else ""}{len(items)} item{"" if len(items) == 1 else "s"}
&middot; <strong>{len(finished)} of {len(prog)}</strong> have done everything.</p>
{who}
<h2>Item by item</h2>
<div class="tablewrap"><table><tr><th>Student</th>{head}<th>Done</th></tr>{grid}</table></div>
{handout_note(handouts)}
{manage}"""
    return html_response(page(f"{g['name']} homework", body, "Homework"))


def handout_note(handouts):
    """Under the table, for a set with a handout in it: what its column means,
    and where to read what the class wrote."""
    if not handouts:
        return ""
    links = " ".join(f'<a class="linky" href="/tests/{tid}/writing">read their writing</a>'
                     for tid in sorted(set(handouts.values())))
    return (f'<p class="sub gap-2">The handout marks itself: parts done until the '
            f'deadline, then its mark out of ten &mdash; half for the parts done in time, '
            f'half for the right answers. {links} &mdash; a nonsense answer can be '
            f'marked as not counting there, and the part it is in stops counting as done.</p>')



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
            f'<div class="card"><p class="sub">Nobody here yet.</p></div>')


def improved_table(db, rows):
    """Ranked on gain alone - the one table a weaker student can win."""
    if not rows:
        return ('<div class="card empty-card"><p class="sub">Nothing to compare '
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
                '<p class="sub gap-2">No student has missed two '
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



def view_reteach(req, db):
    """What to put on the board on Monday, read out of the answers.

    Everything else on this site reports what a student did. This reports
    what they got wrong, which is the only part a lesson can act on.
    """
    gid = req["query"].get("group", [None])[0]
    gid = int(gid) if gid and gid.isdigit() else None
    groups = db.execute("SELECT * FROM groups WHERE archived=0 ORDER BY name").fetchall()
    if gid is None and groups:
        gid = groups[0]["id"]

    def tab(href, label, on):
        return f'<a class="tab{" on" if on else ""}" href="{href}">{E(label)}</a>'
    tabs = ('<div class="tabs">'
            + "".join(tab(f'/reteach?group={g["id"]}', g["name"], gid == g["id"])
                      for g in groups) + "</div>")
    if not groups:
        return html_response(page("Reteach", "<h1>Reteach</h1>"
                                  "<p class='sub'>No classes yet.</p>", "Reteach"))

    r = core.reteach(db, gid)
    name = next((g["name"] for g in groups if g["id"] == gid), "")

    # ---- the words
    if r["words"]:
        rows = ""
        for w in r["words"]:
            bar = int(round(w["pct"]))
            rows += (f'<tr><td><strong>{E(w["term"])}</strong>'
                     f'<div class="sub">{E(w["answer"])}</div></td>'
                     f'<td class="sub">{E(w["list"])}</td>'
                     f'<td class="num">{w["who"]}</td>'
                     f'<td class="num">{w["seen"]}</td>'
                     f'<td class="num"><span class="pct pct-bad">{bar}%</span></td>'
                     f'</tr>')
        words = (f'<div class="tablewrap"><table class="rank">'
                 f'<tr><th>Word</th><th>From</th><th class="num">Students</th>'
                 f'<th class="num">Answers</th><th class="num">Right</th></tr>'
                 f'{rows}</table></div>'
                 f'<p class="sub gap-2">A word appears here once at least '
                 f'{core.RETEACH_MIN_WHO} students have met it '
                 f'{core.RETEACH_MIN_SEEN} times between them and the class is '
                 f'getting it right {core.RETEACH_HARD}% of the time or less.</p>')
    else:
        words = ('<div class="card empty-card"><p class="flush">Nothing to report yet. '
                 'Words appear here once the class has answered them enough '
                 'times for the figure to mean anything.</p></div>')

    # ---- the steps
    if r["steps"]:
        rows = ""
        for s in r["steps"]:
            cls = "pct-bad" if s["pct"] < core.SOLO_PASS else "pct-ok"
            rows += (f'<tr><td><a href="/vocab/{s["list_id"]}">'
                     f'{E(s["title"])}</a>'
                     + (f'<div class="sub">{E(s["book"])}</div>' if s["book"] else "")
                     + f'</td><td class="num">{s["who"]}</td>'
                     f'<td class="num">{s["runs"]}</td>'
                     f'<td class="num">{s["passes"]}</td>'
                     f'<td class="num"><span class="pct {cls}">{s["pct"]}%</span>'
                     f'</td></tr>')
        steps = (f'<div class="tablewrap"><table class="rank">'
                 f'<tr><th>Step</th><th class="num">Students</th>'
                 f'<th class="num">Rounds</th><th class="num">Passed</th>'
                 f'<th class="num">Average</th></tr>{rows}</table></div>'
                 f'<p class="sub gap-2">Passing a step is {core.SOLO_PASS}% right. '
                 f'A step needs four rounds before it is judged.</p>')
    else:
        steps = ('<div class="card empty-card"><p class="flush">Nobody in this class has '
                 'finished enough rounds in Play yet.</p></div>')

    # ---- the students
    # When nobody in the class has opened Play for a fortnight, every name
    # qualifies and the list stops being a list of people. That is a fact
    # about the class, so it is said once rather than twenty times.
    only_quiet = [x for x in r["students"] if x["reasons"] == [
        "nothing since %s" % (x["last"] or "never")[:10]]]
    total = db.execute("SELECT COUNT(*) c FROM students WHERE active=1"
                       " AND group_id IS ?", (gid,)).fetchone()["c"]
    herd = ""
    if total and len(only_quiet) > total / 2:
        newest = max((x["last"] or "") for x in only_quiet)[:10]
        herd = (f'<div class="card"><p class="flush">'
                f'<strong>{len(only_quiet)} of {total} students</strong> in this '
                f'class have not answered anything in Play since {E(newest)}. '
                f'That is a habit of the whole class rather than a worry about '
                f'individuals, so they are not listed one by one.</p></div>')
        r["students"] = [x for x in r["students"] if x not in only_quiet]

    if r["students"]:
        cards = ""
        for s in r["students"]:
            why = " &middot; ".join(E(x) for x in s["reasons"])
            flag = ('<span class="pill watch">homework looks fine</span>'
                    if s["homework_fine"] else
                    '<span class="pill mute">already flagged on Overview</span>')
            cards += (f'<div class="testfile"><div>'
                      f'<a href="/students/{s["id"]}"><strong>'
                      f'{E(s["avatar"] or "")} {E(s["name"])}</strong></a> {flag}'
                      f'<div class="sub">{why}</div></div></div>')
        students = herd + f'<div class="card">{cards}</div>'
    else:
        students = herd or ('<div class="card empty-card"><p class="flush">Nobody in this '
                            'class is slipping quietly.</p></div>')

    body = f"""<h1>What to reteach</h1>
<p class="sub">Class {E(name)} &middot; read out of every answer the class has
given in Play, in a battle and in the live game. This is the only page here
that reports what they got <em>wrong</em>.</p>
{tabs}
<h2 class="gap-4">Words this class keeps getting wrong</h2>
{words}
<h2 class="gap-4">Steps that are not landing</h2>
{steps}
<h2 class="gap-4">Students slipping quietly</h2>
<p class="sub">The Overview finds students who stop handing work in. These are
the other kind: the work arrives, so nothing flags them, but the words are not
going in.</p>
{students}"""
    return html_response(page("Reteach", body, "Reteach"))


def scatter(points, x_label, y_label, width=560, height=300):
    """A scatter plot as inline SVG.

    Drawn by hand rather than with a library because the site loads none,
    and a chart that needs a network to appear is no use on a phone in a
    classroom. Every axis label names a value the chart actually reaches.
    """
    pts = [(p[0], p[1], p[2]) for p in points
           if p[0] is not None and p[1] is not None]
    pad_l, pad_b, pad_t, pad_r = 44, 34, 12, 12
    w, h = width - pad_l - pad_r, height - pad_t - pad_b
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    # A chart drawn from three points, or from a column where every student
    # has the same figure, invents an axis out of nothing: it reads 22, 23,
    # 24 and looks like a finding. If there is nothing to show, show nothing
    # and let the words underneath do the work.
    if (len(pts) < core.ENOUGH or len(set(xs)) < 2 or len(set(ys)) < 2):
        return ""
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)

    def px(v):
        return pad_l + w * (v - x0) / (x1 - x0)

    def py(v):
        return pad_t + h - h * (v - y0) / (y1 - y0)

    grid = ""
    for i in range(5):
        y = pad_t + h * i / 4.0
        val = y1 - (y1 - y0) * i / 4.0
        grid += (f'<line x1="{pad_l}" y1="{y:.1f}" x2="{pad_l + w}" '
                 f'y2="{y:.1f}" class="gridline"/>'
                 f'<text x="{pad_l - 8}" y="{y + 4:.1f}" class="axis" '
                 f'text-anchor="end">{val + 0:.0f}</text>')
    for i in range(3):
        x = pad_l + w * i / 2.0
        val = x0 + (x1 - x0) * i / 2.0
        grid += (f'<text x="{x:.1f}" y="{pad_t + h + 20}" class="axis" '
                 f'text-anchor="middle">{val:.0f}</text>')

    dots = ""
    for x, y, who in pts:
        cls = "dot left" if who.get("left") else "dot"
        dots += (f'<circle cx="{px(x):.1f}" cy="{py(y):.1f}" r="5" '
                 f'class="{cls}"><title>{E(who["name"])} — '
                 f'{E(x_label)} {x:g}, {E(y_label)} {y:g}</title></circle>')

    return (f'<svg class="chart" viewBox="0 0 {width} {height}" '
            f'role="img" aria-label="{E(x_label)} against {E(y_label)}">'
            f'{grid}'
            f'<line x1="{pad_l}" y1="{pad_t + h}" x2="{pad_l + w}" '
            f'y2="{pad_t + h}" class="axisline"/>'
            f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" '
            f'y2="{pad_t + h}" class="axisline"/>{dots}'
            f'<text x="{pad_l + w / 2:.0f}" y="{height - 2}" class="axis" '
            f'text-anchor="middle">{E(x_label)}</text>'
            f'<text x="12" y="{pad_t + h / 2:.0f}" class="axis" '
            f'text-anchor="middle" transform="rotate(-90 12 '
            f'{pad_t + h / 2:.0f})">{E(y_label)}</text></svg>')


def bars(pairs, width=560, height=240):
    """A small bar chart, for counts rather than pairs."""
    if not pairs:
        return '<p class="sub">Nothing to draw yet.</p>'
    top = max(v for _k, v in pairs) or 1
    n = len(pairs)
    pad_l, pad_b, pad_t = 34, 46, 10
    w = width - pad_l - 12
    bw = w / max(1, n)
    out = ""
    for i, (k, v) in enumerate(pairs):
        bh = (height - pad_t - pad_b) * v / top
        x = pad_l + i * bw + bw * 0.15
        y = height - pad_b - bh
        out += (f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw * 0.7:.1f}" '
                f'height="{bh:.1f}" class="bar"/>'
                f'<text x="{x + bw * 0.35:.1f}" y="{y - 4:.1f}" class="axis" '
                f'text-anchor="middle">{v}</text>'
                f'<text x="{x + bw * 0.35:.1f}" y="{height - pad_b + 16:.1f}" '
                f'class="axis" text-anchor="middle">{E(str(k))}</text>')
    return (f'<svg class="chart" viewBox="0 0 {width} {height}" role="img">'
            f'{out}</svg>')


def finding(c):
    """What the numbers are allowed to say."""
    cls = {"clear": "good", "nothing": "mute", "few": "mute",
           "flat": "mute"}.get(c["verdict"], "mute")
    head = {"clear": "There is something here", "nothing": "Nothing clear",
            "few": "Not enough yet", "flat": "Nothing to compare"}[c["verdict"]]
    return (f'<p class="flush"><span class="pill {cls}">{head}</span></p>'
            f'<p class="sub gap-2">{E(c["says"])}</p>')


def donut(slices, big="", small="", size=200, empty="", labels=True):
    """A donut chart as inline SVG.

    Drawn as one ring of stroked arcs rather than pie wedges with a hole cut
    out: the arcs sit on a single circle with a hairline gap between them,
    which is what makes it read as a chart rather than a clip-art pie. Each
    slice is (label, value, class); the class names what the slice *is* -
    kept, ours, theirs - so the colour means the same thing on every chart.
    Slices worth a tenth or more carry their percentage; the legend carries
    all of them, with counts and shares. When there is nothing to draw the
    ring is drawn faint and says why, instead of vanishing."""
    total = sum(v for _l, v, _c in slices)
    c = size / 2.0
    ring, width = size * 0.40, size * 0.13
    if not total:
        return (f'<div class="donut empty"><svg viewBox="0 0 {size} {size}" role="img" '
                f'aria-label="{E(empty)}"><circle cx="{c}" cy="{c}" r="{ring}" '
                f'class="ring-empty"/>'
                f'<text x="{c}" y="{c + 5}" text-anchor="middle" class="small">'
                f'{E(empty or "nothing yet")}</text></svg></div>')
    shown = [(l, v, cls) for l, v, cls in slices if v]
    gap = 1.4 if len(shown) > 1 else 0
    arcs, marks = "", ""
    start = 0.0
    for label, v, cls in shown:
        pct = 100.0 * v / total
        length = max(0.0, pct - gap)
        arcs += (f'<circle cx="{c}" cy="{c}" r="{ring}" pathLength="100" '
                 f'class="slice {cls}" style="stroke-width:{width:.0f}" '
                 f'stroke-dasharray="{length:.2f} {100 - length:.2f}" '
                 f'stroke-dashoffset="{-(start + gap / 2):.2f}" '
                 f'transform="rotate(-90 {c} {c})">'
                 f'<title>{E(label)}: {v} ({pct:.0f}%)</title></circle>')
        # a share on the slice, unless it is the only slice: the middle says it
        if labels and pct >= 10 and len(shown) > 1:
            mid = math.radians((start + pct / 2) * 3.6 - 90)
            x, y = c + ring * math.cos(mid), c + ring * math.sin(mid)
            marks += (f'<text x="{x:.1f}" y="{y + 4:.1f}" text-anchor="middle" '
                      f'class="share">{pct:.0f}%</text>')
        start += pct
    centre = ""
    if big:
        y = c + 9 if not small else c + 3
        centre += f'<text x="{c}" y="{y:.0f}" text-anchor="middle" class="big">{E(big)}</text>'
    if small:
        centre += (f'<text x="{c}" y="{c + 22:.0f}" text-anchor="middle" class="small">'
                   f'{E(small)}</text>')
    legend = "".join(
        f'<li><i class="{cls}"></i><span class="what">{E(label)}</span>'
        f'<span class="n">{v}</span><span class="pc">{100.0 * v / total:.0f}%</span></li>'
        for label, v, cls in slices)
    return (f'<div class="donut"><svg viewBox="0 0 {size} {size}" role="img" '
            f'aria-label="{E(big)} {E(small)}">{arcs}{marks}{centre}</svg>'
            f'<ul class="legend">{legend}</ul></div>')


def band_pies(rows, empty_note):
    """One small pie per band: kept against left, the share kept in the
    middle. The sentence under each is the one a manager would ask for."""
    out = ""
    for r in rows:
        if not r["n"]:
            continue
        kept_pct = "%.0f%%" % (100.0 * r["kept"] / r["n"])
        pie = donut([("Still here", r["kept"], "kept"), ("Left", r["left"], "ours")],
                    big=kept_pct, small="still here", size=150, labels=False)
        pie = pie.replace('<ul class="legend">', '<ul class="legend" hidden>')
        out += (f'<div class="pie"><div class="pie-title">{E(r["label"])}</div>'
                f'<div class="sub">{E(r["note"])}</div>{pie}'
                f'<div class="pie-note"><strong>{r["left"]} of {r["n"]}</strong> left</div></div>')
    if not out:
        return f'<p class="sub flush">{empty_note}</p>'
    return f'<div class="pies">{out}</div>'


def compare_rows(rows):
    """Stayed against left, one measure per row, both bars on one scale."""
    out = ""
    for row in rows:
        if row["stayed"] is None or row["left"] is None:
            continue
        unit = row["unit"]
        top = {"%": 100.0, "/10": 10.0, "/5": 5.0}.get(
            unit, max(row["stayed"], row["left"], 1) * 1.15)
        shown = "" if unit == "d" else unit
        v = row["test"]["verdict"]
        word = {"clear": "a real gap", "nothing": "could be chance",
                "few": "too few to say", "flat": "no difference"}[v]

        def line(name, val, cls):
            pct = max(0, min(100, 100 * val / top))
            return (f'<div class="line {cls}"><span>{name}</span>'
                    f'<div class="track"><div class="fill" style="width:{pct:.0f}%"></div></div>'
                    f'<span class="v">{val:g}{shown}</span></div>')
        out += (f'<div class="row"><div class="label">{E(row["label"])}'
                f'<div class="sub">{row["n_stayed"]} stayed &middot; {row["n_left"]} left '
                f'&middot; {word}</div></div><div class="pair">'
                + line("Stayed", row["stayed"], "stayed")
                + line("Left", row["left"], "left") + "</div></div>")
    return f'<div class="cmp">{out}</div>' if out else '<p class="sub flush">Nothing to compare yet.</p>'


def driver_rows(drivers):
    """A signed bar of r per measure, faint where it could be chance."""
    out = ""
    for d in drivers:
        c = d["test"]
        r = c["r"]
        if r is None:
            bar = ""
        else:
            left = 50 if r >= 0 else 50 + r * 50
            cls = "r" + (" neg" if r < 0 else "") + ("" if c["verdict"] == "clear" else " faint")
            bar = f'<div class="{cls}" style="left:{left:.0f}%;width:{abs(r) * 50:.0f}%"></div>'
        word = {"clear": "r = %.2f, unlikely to be chance" % (r or 0),
                "nothing": "r = %.2f, could be chance" % (r or 0),
                "few": "%d of %d students needed" % (c["n"], core.ENOUGH),
                "flat": "nothing to compare"}[c["verdict"]]
        out += (f'<div class="row"><span>{E(d["label"])}</span>'
                f'<div class="axis">{bar}</div>'
                f'<span class="verdict sub">{E(word)}</span></div>')
    return f'<div class="drivers">{out}</div>'


def view_lessons(req, db):
    """What the students said about the lessons, in aggregate only.

    The page is the teacher's mirror: six aspects as bars, the weeks as a
    table, and the comments - but nothing from a class-week with fewer than
    MIN_RATERS ratings, so an honest student can stay an anonymous one."""
    q = req["query"]
    gid = (q.get("group", [""])[0] or "").strip()
    gid = int(gid) if gid.isdigit() else None
    weeks = (q.get("weeks", ["4"])[0] or "4")
    weeks = int(weeks) if weeks in ("4", "12", "0") else 4
    groups = db.execute("SELECT * FROM groups WHERE archived=0 ORDER BY name").fetchall()
    agg = core.lesson_ratings(db, gid, weeks)

    def tab(href, label, on):
        return f'<a class="tab{" on" if on else ""}" href="{href}">{E(label)}</a>'
    def url(g=gid, w=weeks):
        return "/lessons?" + urllib.parse.urlencode(
            {k: v for k, v in (("group", g or ""), ("weeks", w)) if v != ""})
    classes = ('<div class="tabs">' + tab(url(g=None), "All classes", gid is None)
               + "".join(tab(url(g=g["id"]), g["name"], gid == g["id"]) for g in groups)
               + "</div>")
    spans = ('<div class="tabs">' + tab(url(w=4), "Last 4 weeks", weeks == 4)
             + tab(url(w=12), "Last 12 weeks", weeks == 12)
             + tab(url(w=0), "Everything", weeks == 0) + "</div>")

    if not agg["n"]:
        note = ("Nothing to show yet. " + (
            f"{agg['hidden']} rating{'' if agg['hidden'] == 1 else 's'} are waiting for "
            f"classmates: a class's week appears once {core.MIN_RATERS} of them have rated it."
            if agg["hidden"] else
            "Students rate a lesson from their page: Progress &rarr; Rate. Once "
            f"{core.MIN_RATERS} classmates have rated a week, it appears here."))
        body = f"""<h1>Lessons</h1>
<p class="sub">How the lessons feel from the other side of the desk, in the students'
own words. Anonymous, and shown only in numbers big enough to stay so.</p>
<div class="toolbar">{classes}{spans}</div>
<div class="card"><p class="flush">{note}</p></div>"""
        return html_response(page("Lessons", body, "Lessons"))

    ranked = sorted([a for a in agg["aspects"] if a["avg"] is not None],
                    key=lambda a: -a["avg"])
    best, worst = ranked[0], ranked[-1]
    verdict = (f'<p class="sub">Strongest: <strong>{E(best["label"])}</strong> '
               f'({best["avg"]:.1f} of 5). To work on: <strong>{E(worst["label"])}</strong> '
               f'({worst["avg"]:.1f} of 5).</p>' if len(ranked) > 1 else "")
    bars = "".join(
        f'<div class="aspect{" watch" if a["avg"] < 4 else ""}{" risk" if a["avg"] < 3 else ""}">'
        f'<div class="what">{E(a["label"])}<div class="sub">{E(a["hint"])}</div></div>'
        f'<div class="track"><div class="fill" style="width:{a["avg"] / 5 * 100:.0f}%"></div></div>'
        f'<div class="n">{a["avg"]:.1f}</div></div>' for a in agg["aspects"] if a["avg"] is not None)
    tiles = ('<div class="grid">'
             + stat("Ratings", agg["n"], "from students, anonymous")
             + stat("Lessons rated", agg["lessons"], "class-days with a rating")
             + stat("Overall", f'{agg["overall"]:.1f}' if agg["overall"] else "—", "out of 5")
             + "</div>")
    wk = "".join(
        f'<tr><td>{E(w["week"])}</td><td class="sub">{", ".join(E(c) for c in w["classes"])}</td>'
        f'<td>{w["lessons"]}</td><td>{w["n"]}</td>'
        f'<td><span class="pill {band_class(w["overall"], 3, 4)}">{w["overall"]:.1f}</span></td></tr>'
        for w in reversed(agg["by_week"]))
    keep = "".join(f'<li>{E(c["keep"])}<div class="sub">{E(c["gname"])} &middot; {E(c["week"])}</div></li>'
                   for c in agg["comments"] if c["keep"])
    change = "".join(f'<li>{E(c["change"])}<div class="sub">{E(c["gname"])} &middot; {E(c["week"])}</div></li>'
                     for c in agg["comments"] if c["change"])
    hidden = (f'<p class="sub gap-3">{agg["hidden"]} more rating{"" if agg["hidden"] == 1 else "s"} '
              f'are not shown: their class-week has fewer than {core.MIN_RATERS} raters.</p>'
              if agg["hidden"] else "")
    body = f"""<h1>Lessons</h1>
<p class="sub">How the lessons feel from the other side of the desk. Anonymous, and shown
only in numbers big enough to stay so: a class's week appears once {core.MIN_RATERS}
students have rated it.</p>
<div class="toolbar">{classes}{spans}</div>
{tiles}
<h2>By aspect</h2>
<div class="card">{verdict}<div class="aspects">{bars}</div></div>
<h2>By week</h2>
<div class="tablewrap"><table><tr><th>Week</th><th>Classes</th><th>Lessons</th>
<th>Ratings</th><th>Overall</th></tr>{wk}</table></div>
<h2>What they said</h2>
<div class="said">
<div class="card"><h3>Keep doing</h3><ul>{keep or '<li class="sub">Nothing written yet.</li>'}</ul></div>
<div class="card"><h3>Change</h3><ul>{change or '<li class="sub">Nothing written yet.</li>'}</ul></div>
</div>{hidden}"""
    return html_response(page("Lessons", body, "Lessons"))


def view_insights(req, db):
    """The teaching cycle, read back: what students put in, what came out,
    who left and what they looked like before they did. Whole school by
    default, one class on request. Every chart says what it is allowed to
    say and no more."""
    core.backfill_enrolments(db)
    q = req["query"]
    gid = (q.get("group", [""])[0] or "").strip()
    gid = int(gid) if gid.isdigit() else None
    groups = db.execute("SELECT * FROM groups WHERE archived=0 ORDER BY name").fetchall()

    pts = core.cycle_points(db, gid)
    ret = core.retention(db)
    left = [p for p in pts if p["left"]]
    here = [p for p in pts if not p["left"]]

    def tab(href, label, on):
        return f'<a class="tab{" on" if on else ""}" href="{href}">{E(label)}</a>'
    classes = ('<div class="tabs">' + tab("/insights", "Whole school", gid is None)
               + "".join(tab(f'/insights?group={g["id"]}', g["name"], gid == g["id"])
                         for g in groups) + "</div>")

    # ------------------------------------------------------- in sentences
    findings = "".join(f"<li>{E(s)}</li>" for s in core.cycle_findings(pts, ret))

    # ------------------------------------------------------------ figures
    def avg(key):
        v = core._mean([p[key] for p in pts])
        return "—" if v is None else f"{v:g}"
    tiles = ('<div class="grid">'
             + stat("Students", len(pts), f"{len(here)} here, {len(left)} left")
             + stat("Homework done", avg("completion") + ("%" if avg("completion") != "—" else ""),
                    "of what was set, on average")
             + stat("In the classroom", avg("participation"), "out of 5, on average")
             + stat("Class tests", avg("class_tests") + ("%" if avg("class_tests") != "—" else ""),
                    "on average")
             + stat("Exam", avg("exam") + ("%" if avg("exam") != "—" else ""),
                    "latest exam, on average")
             + "</div>")

    # ------------------------------------------------------------- donuts
    ours = sum(1 for p in left if core.REASON_OURS.get(p["reason"], True))
    theirs = len(left) - ours
    kept_pct = ("%.0f%%" % (100.0 * len(here) / len(pts))) if pts else "—"
    keep = donut([("Still here", len(here), "kept"),
                  ("Left — could be ours", ours, "ours"),
                  ("Left — outside your control", theirs, "theirs")],
                 big=kept_pct, small="still here", empty="no students yet")
    reasons = {}
    for p in left:
        k = core.REASON_SHORT.get(p["reason"], p["reason"] or "unknown")
        reasons[k] = reasons.get(k, 0) + 1
    letters = "abcdef"
    why = donut([(k, v, letters[i % 6]) for i, (k, v) in
                 enumerate(sorted(reasons.items(), key=lambda kv: -kv[1]))],
                big=str(len(left)), small="left", empty="nobody has left")
    no_leavers = ("" if left else
                  '<p class="sub gap-2 flush">Nobody has been recorded as leaving yet. '
                  'When a student stops coming, mark them on the '
                  '<a class="linky" href="/records?v=leavers">Who left</a> tab and '
                  'these pies start to mean something.</p>')
    hw_pies = band_pies(core.bands(pts, "completion", core.HABIT_BANDS),
                        "No homework recorded yet.")
    room_pies = band_pies(core.bands(pts, "participation", core.ROOM_BANDS),
                          "No classroom marks recorded yet - they are given on the "
                          "Grade page, lesson by lesson.")

    # ----------------------------------------------------- the comparisons
    cmp_rows = core.left_vs_stayed(pts)
    drivers = core.exam_drivers(pts)
    top = drivers[0] if drivers and drivers[0]["test"]["r"] is not None else None
    top_chart = ""
    if top:
        top_chart = scatter([(p[top["key"]], p["exam"], p) for p in pts
                             if p[top["key"]] is not None and p["exam"] is not None],
                            top["label"].lower() + ", " + top["unit"].strip("/"),
                            "exam, %")
    hb_pairs = [(p["completion"], p["participation"], p) for p in pts
                if p["completion"] is not None and p["participation"] is not None]
    hb = core.correlate([(a, b) for a, b, _ in hb_pairs])
    quiet_pairs = [(p["quiet_days"], 100 if p["left"] else 0, p) for p in pts
                   if p["quiet_days"] is not None]
    qc = core.correlate([(a, 1 if b else 0) for a, b, _ in quiet_pairs])
    quiet_left = core._mean([p["quiet_days"] for p in left])
    quiet_here = core._mean([p["quiet_days"] for p in here])
    quiet_line = ""
    if quiet_left is not None and quiet_here is not None:
        quiet_line = (f'<p class="sub gap-2">The ones who left had been quiet for '
                      f'<strong>{quiet_left:g} days</strong> on average. The ones still '
                      f'here: <strong>{quiet_here:g}</strong>.</p>')
    elif not left:
        quiet_line = ('<p class="sub gap-2">Nobody has been recorded as leaving yet, '
                      'so there is nothing to compare the quiet ones against. This '
                      'chart is the reason the leaver register is worth keeping up.</p>')

    who = "the whole school" if gid is None else E(group_name(db, gid))
    body = f"""<h1>Insights</h1>
<p class="sub">The teaching cycle read back, for {who}: what students put in, what
came out, who left, and what they looked like before they did. Every chart says
only what the numbers can back.</p>
{classes}

<h2>What the numbers say</h2>
<div class="card"><ol class="findings">{findings}</ol></div>

<h2>Where things stand</h2>
{tiles}

<div class="insight-grid gap-4">
<div class="card"><h3 class="flush gap-3">Who is still here</h3>{keep}
<p class="sub gap-2 flush">"Could be ours" is a reason a teacher might have changed:
bored, no progress, a fallout. Moving away, money and finishing are not.</p></div>
<div class="card"><h3 class="flush gap-3">Why they left</h3>{why}
{no_leavers or '<p class="sub gap-2 flush">Recorded on the <a class="linky" href="/records?v=leavers">Who left</a> tab, one student at a time. This chart is only as honest as that habit.</p>'}</div>
</div>

<h2>Who leaves, by homework habit</h2>
<div class="card">{hw_pies}
<p class="sub gap-3 flush">Every student sorted by how much of the homework they
do, and in each group the share who are still here. If the weak-homework pie is
the red one, the homework is your early warning.</p></div>

<h2>Who leaves, by how they are in the classroom</h2>
<div class="card">{room_pies}
<p class="sub gap-3 flush">The same, by the classroom marks - punctuality,
behaviour and taking part, averaged. These are the two habits a teacher can
see with their own eyes, weeks before a student stops coming.</p></div>

<h2>What the leavers looked like before they left</h2>
<div class="card">{compare_rows(cmp_rows)}
<p class="sub gap-3 flush">The same students, measured before they went. A gap
marked "a real gap" is one too large to be chance for this many students; the
rest may still be true, but the numbers cannot yet say so.</p></div>

<details class="card stats"><summary>The statistics behind this &mdash; for the curious</summary>
<p class="sub gap-2">Everything above is already drawn from these. They are here for
anyone who wants to see the dots and the numbers themselves.</p>

<h3>What moves with the exam</h3>
{driver_rows(drivers)}
{top_chart}
<p class="sub gap-3">Strongest first. A bar to the right means the two rise
together; to the left, one rises as the other falls. A faint bar could be chance.
Whatever is at the top is your earliest warning of the exam result, weeks before it.</p>

<h3>Homework and the classroom</h3>
{scatter(hb_pairs, "homework done, %", "in the classroom, /5")}
{finding(hb)}
<p class="sub gap-2">Whether the ones who do the homework are also the ones
who are present in the room - or whether those are two different students.</p>

<h3>Going quiet, then leaving</h3>
{scatter(quiet_pairs, "days since their last homework",
         "left (100) or still here (0)")}
{finding(qc)}{quiet_line}
<p class="sub gap-3 flush">{len(pts)} students in all. A dot outlined in red is somebody
who has left. Hover or tap a dot for the name.</p></details>"""
    return html_response(page("Insights", body, "Insights"))


def view_records(req, db):
    """The cycle: who is here, who left and why, and the marks along the way.

    Two jobs on one page because they are the same job. A teacher entering
    this week's test scores is the teacher most likely to notice that
    somebody has stopped coming.
    """
    core.backfill_enrolments(db)
    q = req["query"]
    which = (q.get("v", ["scores"])[0] or "scores")
    gid = q.get("group", [None])[0]
    gid = int(gid) if gid and gid.isdigit() else None
    groups = db.execute("SELECT * FROM groups WHERE archived=0"
                        " ORDER BY name").fetchall()
    if gid is None and groups:
        gid = groups[0]["id"]

    def tab(href, label, on):
        return f'<a class="tab{" on" if on else ""}" href="{href}">{E(label)}</a>'
    views = ('<div class="tabs">'
             + tab(f"/records?v=scores&amp;group={gid}", "Scores",
                   which == "scores")
             + tab(f"/records?v=exams&amp;group={gid}", "Exams",
                   which == "exams")
             + tab("/records?v=leavers", "Who left", which == "leavers")
             + tab(f"/insights?group={gid}", "Insights &rarr;", False)
             + "</div>")
    classes = ('<div class="tabs">'
               + "".join(tab(f'/records?v={which}&amp;group={g["id"]}',
                             g["name"], gid == g["id"]) for g in groups)
               + "</div>") if which != "leavers" else ""

    if which == "leavers":
        return html_response(page("Records", leavers_panel(db) , "Records"))
    if which == "charts":                     # the old address of the charts
        return redirect(f"/insights?group={gid}" if gid else "/insights")

    students = db.execute(
        "SELECT * FROM students WHERE active=1 AND group_id=? ORDER BY name",
        (gid,)).fetchall()
    if which == "exams":
        body = exams_panel(db, gid, students)
    else:
        body = scores_panel(db, gid, students, q)
    return html_response(page("Records", f"""<h1>Records</h1>
<p class="sub">The whole cycle in one place: the marks a class gets along the
way, the exams at the end of it, and who left and why. Retention cannot be
worked out from anything else.</p>
{views}{classes}{body}""", "Records"))


def scores_panel(db, gid, students, q):
    """In-class tests. Effort and learning are kept apart, so this is only
    the learning half; the participation marks live on the Grade page."""
    tid = q.get("t", [None])[0]
    tid = int(tid) if tid and tid.isdigit() else None
    tests = core.class_tests(db, gid)
    listing = ""
    for t in tests[:12]:
        on = " on" if tid == t["id"] else ""
        listing += (f'<a class="steprow{on}" href="/records?v=scores&amp;'
                    f'group={gid}&amp;t={t["id"]}">'
                    f'<span class="steptitle">{E(t["title"])}</span>'
                    f'<span class="sub">{E(t["sat_on"][:10])} &middot; '
                    f'out of {t["max_score"]:g} &middot; {t["marked"]} marked'
                    f'</span></a>')
    today = core.iso(core.now())[:10]
    adder = f"""<details class="adder"><summary>New class test</summary>
<div class="card"><form method="post" action="/records/test/new" class="inline">
<input type="hidden" name="group" value="{gid}">
<label class="f grow">Title
  <input name="title" placeholder="Unit 3 vocabulary" required class="wide"></label>
<label class="f">Out of<input name="max" value="20" class="tiny"></label>
<label class="f">Date<input type="date" name="sat_on" value="{today}"></label>
<button>Add</button></form></div></details>"""

    if not tid:
        return (adder + (f'<div class="steps gap-3">{listing}</div>' if listing
                else '<div class="card empty-card"><p class="flush">No class tests for '
                     'this class yet.</p></div>'))

    test = db.execute("SELECT * FROM class_tests WHERE id=?", (tid,)).fetchone()
    have = core.class_test_scores(db, tid)
    rows = ""
    for s in students:
        r = have.get(s["id"])
        val = "" if not r or r["score"] is None else "%g" % r["score"]
        absent = " checked" if r and r["absent"] else ""
        rows += (f'<tr><td class="who">{E(s["avatar"] or "")} {E(s["name"])}</td>'
                 f'<td class="num"><input class="scorebox" name="s{s["id"]}"'
                 f' value="{val}" inputmode="decimal" autocomplete="off"></td>'
                 f'<td class="num"><label class="f"><input type="checkbox"'
                 f' name="a{s["id"]}"{absent}> absent</label></td></tr>')
    return f"""{adder}
<h2 class="gap-4">{E(test["title"])}</h2>
<p class="sub">{E(test["sat_on"][:10])} &middot; out of {test["max_score"]:g}.
Leave a box empty if you have not marked it yet; tick absent so it is not
counted as a zero.</p>
<form method="post" action="/records/test/{tid}/save">
<div class="tablewrap"><table class="rank">
<tr><th>Student</th><th class="num">Score</th><th class="num"></th></tr>
{rows}</table></div>
<div class="gap-3"><button>Save scores</button>
<a class="tab" href="/records?v=scores&amp;group={gid}">Back to the list</a></div>
</form>"""


def exams_panel(db, gid, students):
    """The centre's mid and final exams, and the shape of the marks."""
    today = core.iso(core.now())[:10]
    out = ['<details class="adder" open><summary>Enter exam results</summary>'
           '<div class="card">'
           f'<form method="post" action="/records/exam/save">'
           f'<input type="hidden" name="group" value="{gid}">'
           '<div class="inline setrow">'
           '<label class="f">Which<select name="kind">'
           '<option value="mid">Mid-course</option>'
           '<option value="final">Final</option></select></label>'
           '<label class="f grow">Title'
           '<input name="title" placeholder="Mid-course exam" class="wide"></label>'
           '<label class="f">Out of<input name="max" value="100" class="tiny"></label>'
           f'<label class="f">Date<input type="date" name="sat_on" value="{today}"></label>'
           '<label class="f">Marked by<input name="marked_by" '
           'placeholder="your name"></label></div>']
    rows = ""
    for s in students:
        rows += (f'<tr><td class="who">{E(s["avatar"] or "")} {E(s["name"])}</td>'
                 f'<td class="num"><input class="scorebox" name="s{s["id"]}"'
                 f' inputmode="decimal" autocomplete="off"></td></tr>')
    out.append(f'<div class="tablewrap"><table class="rank">'
               f'<tr><th>Student</th><th class="num">Score</th></tr>{rows}'
               f'</table></div><div class="gap-3"><button>Save results</button>'
               f'</div></form></div></details>')

    for kind, label in (("mid", "Mid-course"), ("final", "Final")):
        sp = core.exam_spread(db, kind, gid)
        if not sp:
            out.append(f'<h2 class="gap-4">{label}</h2><div class="card">'
                       f'<p class="flush">No results entered yet.</p></div>')
            continue
        widest = max(sp["bands"].values()) or 1
        bars = ""
        for band, n in sp["bands"].items():
            w = int(round(100.0 * n / widest))
            bars += (f'<div class="lane"><div class="lanetop">'
                     f'<span class="who">{band}%</span>'
                     f'<span class="num">{n}</span></div>'
                     f'<div class="rail"><div class="fill c1" '
                     f'style="width:{w}%"></div></div></div>')
        out.append(f"""<h2 class="gap-4">{label}</h2>
<div class="card"><p class="flush">
<strong>{sp["mean"]}%</strong> average across {sp["n"]} students &middot;
median {sp["median"]}% &middot; from {sp["lowest"]}% to {sp["highest"]}%.</p>
<p class="sub gap-2">The spread matters more than the average. You mark your
own students' papers, so a mean on its own is easy to doubt; a shape with
some low marks in it is not.</p>
<div class="track">{bars}</div></div>""")
    return "".join(out)


def leavers_panel(db):
    """Who left, when, and whether it was anything you could have changed."""
    r = core.retention(db)
    gone = core.leavers(db)
    here = db.execute("SELECT * FROM students WHERE active=1 ORDER BY name").fetchall()
    groups = db.execute("SELECT * FROM groups WHERE archived=0 ORDER BY name").fetchall()
    gname = {g["id"]: g["name"] for g in groups}

    reasons = "".join(f'<option value="{k}">{E(label)}</option>'
                      for k, label, _ours in core.LEAVE_REASONS)
    picker = "".join(f'<option value="{s["id"]}">{E(s["name"])}'
                     f' &mdash; {E(gname.get(s["group_id"], "no class"))}'
                     f'</option>' for s in here)
    today = core.iso(core.now())[:10]

    rows = ""
    for e in gone[:40]:
        ours = core.REASON_OURS.get(e["reason"])
        pill = ('<span class="pill risk">could be ours</span>' if ours
                else '<span class="pill mute">outside your control</span>')
        rows += (f'<tr><td class="who">{E(e["avatar"] or "")} {E(e["name"])}</td>'
                 f'<td class="sub">{E(e["group_name"] or "—")}</td>'
                 f'<td class="sub">{E((e["ended_at"] or "")[:10])}</td>'
                 f'<td>{E(core.REASON_LABEL.get(e["reason"], e["reason"] or "—"))}'
                 f' {pill}</td></tr>')

    rate = ("—" if r["rate"] is None else "%.1f%%" % r["rate"])
    rate_ours = ("—" if r["rate_ours"] is None else "%.1f%%" % r["rate_ours"])
    return f"""<h1>Records</h1>
<p class="sub">The whole cycle in one place.</p>
<div class="tabs"><a class="tab" href="/records?v=scores">Scores</a>
<a class="tab" href="/records?v=exams">Exams</a>
<a class="tab on" href="/records?v=leavers">Who left</a></div>

<div class="grid gap-3">
  {stat("Kept, last 90 days", rate)}
  {stat("Ignoring what you cannot control", rate_ours)}
  {stat("Students in the window", r["here"])}
  {stat("Left", r["left"])}
</div>
<p class="sub gap-2">Counted over {E(r["since"])} to {E(r["until"])}: everybody
whose time here overlapped the window, and the ones whose time ended inside
it. {r["ours"]} of the {r["left"]} had a reason you might have changed — the
rest moved away, ran out of money, or finished.</p>

<details class="adder" open><summary>Mark a student as left</summary>
<div class="card"><form method="post" action="/records/left" class="inline">
<label class="f grow">Student<select name="student" required>
<option value="">choose…</option>{picker}</select></label>
<label class="f">Reason<select name="reason">{reasons}</select></label>
<label class="f">Date<input type="date" name="when" value="{today}"></label>
<label class="f grow">Note (optional)<input name="note" class="wide"></label>
<button>Record it</button></form>
<p class="sub gap-2">This takes them off the roll and closes their time here.
If they come back, add them again and it starts a new spell — the old one
keeps its reason.</p></div></details>

<h2 class="gap-4">Who has left</h2>
{'<div class="tablewrap"><table class="rank"><tr><th>Student</th><th>Class</th>'
 '<th>When</th><th>Why</th></tr>' + rows + '</table></div>' if rows else
 '<div class="card empty-card"><p class="flush">Nobody recorded yet. From now on, every '
 'time a student stops coming, put them here — a retention rate cannot be '
 'worked out from anything else, and in six months this is the only place '
 'the answer will exist.</p></div>'}"""


def act_new_class_test(req, db):
    f = req["form"]
    gid = (f.get("group", [""])[0] or "")
    if not gid.isdigit():
        return redirect("/records")
    tid = core.new_class_test(db, int(gid), f.get("title", [""])[0],
                              f.get("max", ["20"])[0],
                              f.get("sat_on", [core.iso(core.now())[:10]])[0])
    return redirect(f"/records?v=scores&group={gid}&t={tid}")


def act_save_class_scores(req, db, tid):
    f = req["form"]
    test = db.execute("SELECT * FROM class_tests WHERE id=?", (tid,)).fetchone()
    if not test:
        return redirect("/records")
    scores, absent = {}, set()
    for key, values in f.items():
        m = re.match(r"^s(\d+)$", key)
        if m:
            raw = (values[0] or "").strip().replace(",", ".")
            sid = int(m.group(1))
            try:
                scores[sid] = float(raw) if raw else None
            except ValueError:
                scores[sid] = None
        m = re.match(r"^a(\d+)$", key)
        if m:
            absent.add(int(m.group(1)))
    for sid in absent:
        scores.setdefault(sid, None)
    core.save_class_scores(db, tid, scores, absent)
    return redirect(f"/records?v=scores&group={test['group_id']}&t={tid}")


def act_save_exam(req, db):
    f = req["form"]
    gid = (f.get("group", [""])[0] or "")
    if not gid.isdigit():
        return redirect("/records")
    scores = {}
    for key, values in f.items():
        m = re.match(r"^s(\d+)$", key)
        if not m:
            continue
        raw = (values[0] or "").strip().replace(",", ".")
        if not raw:
            continue
        try:
            scores[int(m.group(1))] = float(raw)
        except ValueError:
            pass
    kind = "final" if f.get("kind", ["mid"])[0] == "final" else "mid"
    core.save_exam(db, int(gid), kind,
                   (f.get("title", [""])[0] or "").strip() or None,
                   f.get("max", ["100"])[0],
                   f.get("sat_on", [core.iso(core.now())[:10]])[0], scores,
                   marked_by=(f.get("marked_by", [""])[0] or "").strip())
    return redirect(f"/records?v=exams&group={gid}")


def act_mark_left(req, db):
    f = req["form"]
    sid = (f.get("student", [""])[0] or "")
    if not sid.isdigit():
        return redirect("/records?v=leavers")
    core.mark_left(db, int(sid), f.get("reason", [""])[0],
                   when=(f.get("when", [""])[0] or None),
                   note=f.get("note", [""])[0])
    return redirect("/records?v=leavers")



NICE = {"ielts": "IELTS band", "celta": "CELTA", "avg": "students' average",
        "retention": "retention"}


def view_kpi(req, db):
    """What the ladder pays, where you stand on it, and what the next rung
    is worth in money.

    The point of the page is the last of those. "You could earn more" moves
    nobody; "the certificate is worth 1 700 000 a month at your headcount"
    is a decision.
    """
    q = req["query"]

    def num(key, default=None):
        raw = (q.get(key, [""])[0] or "").strip().replace(",", ".")
        if raw == "":
            return default
        try:
            return float(raw)
        except ValueError:
            return default

    prof = core.kpi_profile(db)
    ins = core.kpi_inputs(db)
    ielts = num("ielts", prof["ielts"])
    celta = 1 if q.get("celta") else (0 if "ielts" in q else prof["celta"])
    students = int(num("students", prof["students"] or ins["students"]) or 0)
    avg = num("avg", prof["avg_override"])
    if avg is None:
        avg = ins["avg_final"] if ins["avg_final"] is not None else ins["avg_mid"]
    ret = num("retention", prof["retention_override"])
    if ret is None:
        ret = ins["retention"]
    st = core.kpi_standing(db, ielts=ielts, celta=celta, avg=avg,
                           retention_pct=ret, students=students)
    cur = prof["currency"] or "so'm"

    rows = ""
    for r in st["levels"]:
        here = r["level"] == st["level"]
        mark = ("<span class=\"pill good\">you are here</span>" if here
                else "<span class=\"pill mute\">reached</span>" if r["met"]
                else "")
        needs = []
        if r["ielts_min"] is not None:
            needs.append("IELTS %g" % r["ielts_min"])
        if r["celta"]:
            needs.append("CELTA")
        if r["avg_min"] is not None:
            needs.append("avg %g%%" % r["avg_min"])
        if r["retention_min"] is not None:
            needs.append("retention %g%%" % r["retention_min"])
        short = ", ".join(
            "%s %g (you have %s)"
            % (NICE[k], want, "no" if k == "celta" else
               ("—" if got is None else "%g" % got))
            for k, want, got in r["missing"])
        tr = '<tr class="me">' if here else "<tr>"
        rows += (tr
                 + f'<td><strong>{E(r["name"])}</strong> {mark}'
                 + (f'<div class="sub">{E(r["note"])}</div>' if r["note"] else "")
                 + f'</td><td class="sub">{E(" · ".join(needs) or "nothing")}'
                 + (f'<div class="sub warn">{E(short)}</div>' if short else "")
                 + f'</td><td class="num">{core.money(r["per_student"], cur)}</td>'
                 f'<td class="num"><strong>{core.money(r["pay"], cur)}</strong>'
                 f'</td></tr>')

    if st["next"]:
        need = ", ".join(NICE[k] for k, _w, _g in st["next"]["missing"])
        nextline = (f'<p class="flush"><strong>{E(st["next"]["name"])}</strong> '
                    f'is worth <strong>{core.money(st["gap"], cur)} more a '
                    f'month</strong> at {st["students"]} students. '
                    f'What is missing: {E(need)}.</p>')
    else:
        nextline = ('<p class="flush">You are on the top rung. The only way '
                    'the number grows from here is more students.</p>')

    ladder = ""
    for r in st["levels"]:
        lv = db.execute("SELECT * FROM kpi_levels WHERE level=?",
                        (r["level"],)).fetchone()
        ladder += f"""<tr><td class="sub">{lv["level"]}</td>
<td><input name="name" value="{E(lv["name"])}" form="lv{lv["level"]}"></td>
<td><input name="per_student" value="{lv["per_student"]}" class="scorebox"
 form="lv{lv["level"]}"></td>
<td><input name="ielts_min" value="{"" if lv["ielts_min"] is None else "%g" % lv["ielts_min"]}"
 class="tiny" form="lv{lv["level"]}"></td>
<td><input type="checkbox" name="celta"{" checked" if lv["celta"] else ""}
 form="lv{lv["level"]}"></td>
<td><input name="avg_min" value="{"" if lv["avg_min"] is None else "%g" % lv["avg_min"]}"
 class="tiny" form="lv{lv["level"]}"></td>
<td><input name="retention_min" value="{"" if lv["retention_min"] is None else "%g" % lv["retention_min"]}"
 class="tiny" form="lv{lv["level"]}"></td>
<td><form method="post" action="/kpi/level/{lv["level"]}" id="lv{lv["level"]}">
<button>Save</button></form></td></tr>"""

    from_records = []
    if ins["retention"] is not None:
        a, b = ins["retention_window"]
        from_records.append(f'retention <strong>{ins["retention"]}%</strong> '
                            f'({E(a)} to {E(b)})')
    if ins["avg_final"] is not None:
        from_records.append(f'final average <strong>{ins["avg_final"]}%</strong> '
                            f'from {ins["avg_final_n"]} students')
    elif ins["avg_mid"] is not None:
        from_records.append(f'mid average <strong>{ins["avg_mid"]}%</strong> '
                            f'from {ins["avg_mid_n"]} students')
    offer = (("Your own records say: " + " &middot; ".join(from_records) + ".")
             if from_records else
             "Your records cannot work these out yet — record some leavers "
             "and enter an exam, and they will fill themselves in.")

    # the invitation to the demo, hidden while the demo is what is showing
    invite = "" if core.demo_on() else (
        '<div class="card gap-4"><p class="flush"><strong>Showing this to '
        'management?</strong> The demo puts an invented class of twenty-eight '
        'through a whole term \u2014 homework, tests, exams, six leavers \u2014 '
        'so every chart and figure on the site has something in it. It is a '
        'separate copy: nothing you do in it can reach your real students, '
        'and a banner stays on every page until you leave.</p>'
        '<form method="post" action="/demo/on" class="gap-2">'
        '<button>Open the demo</button></form></div>')
    body = f"""<h1>What the ladder pays</h1>
<p class="sub">Six levels, paid per student per month. Move the figures to
see what any of them would be worth to you. Nothing here is saved unless you
press save, so it is safe to play with.</p>

<div class="card">
<form method="get" action="/kpi" class="inline">
<label class="f">Your IELTS<input name="ielts" class="tiny"
 value="{"" if ielts is None else "%g" % ielts}"></label>
<label class="f">CELTA<input type="checkbox" name="celta"
 value="1"{" checked" if celta else ""}></label>
<label class="f">Students<input name="students" class="tiny"
 value="{students}"></label>
<label class="f">Students' average %<input name="avg" class="tiny"
 value="{"" if avg is None else "%g" % avg}"></label>
<label class="f">Retention %<input name="retention" class="tiny"
 value="{"" if ret is None else "%g" % ret}"></label>
<button>Work it out</button>
</form>
<p class="sub gap-2">{offer}</p>
</div>

<div class="grid gap-3">
  {stat("Where you stand", st["here"]["name"])}
  {stat("A month, at %d students" % st["students"],
        core.money(st["here"]["pay"], cur))}
  {stat("Per student", core.money(st["here"]["per_student"], cur))}
  {stat("The next rung is worth", core.money(st["gap"], cur) if st["next"] else "—")}
</div>
<div class="card">{nextline}</div>

<h2 class="gap-4">Every level, at your headcount</h2>
<div class="tablewrap"><table class="rank">
<tr><th>Level</th><th>What it asks for</th><th class="num">Per student</th>
<th class="num">A month</th></tr>{rows}</table></div>
<p class="sub gap-2">The ladder is a ladder: you are on the highest level you
can reach without skipping one below it. Level 1 asks for nothing, which is
why everybody starts there.</p>

{invite} The demo puts an invented class of twenty-eight through a
whole term — homework, tests, exams, six leavers — so every chart and figure
on the site has something in it. It is a separate copy: nothing you do in it
can reach your real students, and a banner stays on every page until you
leave.</p>
<details class="adder"><summary>Change the ladder</summary>
<div class="card">
<p class="sub">These are the centre's numbers, not the program's. Change them
when the centre changes them. Later this can be the manager's to set, with
every teacher reading their own standing off it.</p>
<div class="tablewrap"><table class="rank">
<tr><th></th><th>Name</th><th>Per student</th><th>IELTS</th><th>CELTA</th>
<th>Avg %</th><th>Retention %</th><th></th></tr>{ladder}</table></div>
<form method="post" action="/kpi/profile" class="inline gap-3">
<label class="f">Save my IELTS<input name="ielts" class="tiny"
 value="{"" if prof["ielts"] is None else "%g" % prof["ielts"]}"></label>
<label class="f">CELTA<input type="checkbox" name="celta" value="1"
{" checked" if prof["celta"] else ""}></label>
<label class="f">Currency<input name="currency" value="{E(cur)}"></label>
<button>Save my details</button></form>
</div></details>"""
    return html_response(page("KPI", body, "KPI"))


def act_save_kpi_level(req, db, level):
    f = req["form"]

    def num(key):
        raw = (f.get(key, [""])[0] or "").strip().replace(",", ".")
        if raw == "":
            return None
        try:
            return float(raw)
        except ValueError:
            return None

    per = num("per_student")
    core.save_kpi_level(
        db, level,
        name=(f.get("name", [""])[0] or "").strip() or "Level %d" % level,
        per_student=int(per) if per is not None else 0,
        ielts_min=num("ielts_min"), celta=1 if f.get("celta") else 0,
        avg_min=num("avg_min"), retention_min=num("retention_min"))
    return redirect("/kpi")


def act_save_kpi_profile(req, db):
    f = req["form"]
    raw = (f.get("ielts", [""])[0] or "").strip().replace(",", ".")
    try:
        ielts = float(raw) if raw else None
    except ValueError:
        ielts = None
    core.save_kpi_profile(db, ielts=ielts, celta=1 if f.get("celta") else 0,
                          currency=(f.get("currency", [""])[0] or "so'm").strip())
    return redirect("/kpi")


def act_demo_on(req, db):
    """Show management. Seeds the demo copy on first use, then sets a cookie
    that only a signed-in teacher's requests will honour."""
    core.demo_ready()
    return redirect("/insights", [("Set-Cookie", "ta_demo=1; Path=/; SameSite=Lax")])


def act_demo_off(req, db):
    return redirect("/", [("Set-Cookie", "ta_demo=; Path=/; Max-Age=0; SameSite=Lax")])


def act_demo_reset(req, db):
    core.demo_reset()
    return redirect("/insights")


# ------------------------------------------------ the parents' channel
#
# One post a class: the class table and the last weeks as pictures, and a
# written report in Uzbek and Russian (parents.py works it out, card.py draws
# it). The page shows each post exactly as it will appear, and one button
# posts them all. Sending runs on its own thread, on the real database, and
# never from the demo.

def parent_groups(db):
    return [g for g in db.execute("SELECT * FROM groups WHERE archived=0 ORDER BY name")
            if db.execute("SELECT 1 FROM students WHERE group_id=? AND active=1",
                          (g["id"],)).fetchone()]


def parents_kind(query):
    kind = (query.get("p", [""])[0] or "week")
    return kind if kind in dict(parents.PERIODS) else "week"


def view_parents(req, db):
    q = req.get("query", {}) if isinstance(req, dict) else {}
    kind = parents_kind(q)
    p = parents.period(kind, CFG)
    chan = core.parents_channel(db)
    token = CFG.get("telegram_token")
    state = parents.sending(db)
    going = parents.busy(db)

    flash = ""
    if q.get("said") == ["1"]:
        flash = '<div class="flash">Posted in the channel.</div>'
    elif q.get("e"):
        why = {"demo": "This is the demo: its classes are invented, so nothing is sent from it. "
                       "Leave the demo to send.",
               "channel": "There is no channel yet - see the steps below.",
               "bot": "The bot is not set up on this server, so nothing can be sent.",
               "busy": "A sending is still going. Wait for it to finish.",
               "none": "Tick at least one class.",
               "empty": "Write something first.",
               "said": "Telegram did not take it: " + (q.get("why", [""])[0] or "")}
        flash = '<div class="flash err">%s</div>' % E(why.get(q["e"][0], "Something went wrong."))
    if state:
        if going:
            flash += (f'<div class="flash">Sending: {state["done"]} of {state["total"]} classes '
                      f'posted. This page refreshes by itself.</div>')
        elif state.get("finished") and q.get("sent") == ["1"]:
            errs = state.get("errors") or []
            flash += ('<div class="flash%s">%d of %d classes posted.%s</div>' % (
                " err" if errs else "", state["total"] - len(errs), state["total"],
                "".join(" " + E(e) for e in errs)))

    # the channel: found by the bot, or typed in
    if chan:
        where = f'@{E(chan["username"])}' if chan.get("username") else "a private channel"
        chan_html = (f'<p class="flush">Posting to <strong>{E(chan["title"] or "the channel")}</strong> '
                     f'<span class="sub">({where})</span></p>')
    else:
        me = E(core.meta_get(db, "bot_username") or "your bot")
        chan_html = f"""<p class="flush"><strong>No channel yet.</strong></p>
<ol class="par-steps">
  <li>In Telegram, open the parents' channel and tap its name.</li>
  <li>Edit &rarr; Administrators &rarr; Add Admin &rarr; <strong>@{me}</strong>. Keep
  &ldquo;Post Messages&rdquo; on, and save.</li>
  <li>Forward any post from the channel to <strong>@{me}</strong>, from your own Telegram
  (the one that gets the homework). The bot answers straight away: connected, or what is
  still missing.</li>
</ol>"""
    others = [c for c in core.channels_seen(db)
              if c.get("admin") and (not chan or str(c["id"]) != str(chan["id"]))]
    pick = "".join(
        f'<form method="post" action="/parents/channel"><input type="hidden" name="id" value="{E(str(c["id"]))}">'
        f'<button class="ghost">Use &laquo;{E(c["title"] or str(c["id"]))}&raquo;'
        f'{" instead" if chan else ""}</button></form>' for c in others)
    if others and not chan:
        pick = ('<p class="sub flush">The bot has been made an administrator of these. '
                'Choose the parents&rsquo; one:</p>' + pick)

    tabs = "".join(
        f'<a class="tab{" on" if k == kind else ""}" href="/parents?p={k}">{E(label)}</a>'
        for k, label in parents.PERIODS)
    days = "%s – %s" % (p["first"].strftime("%d %b"), p["last"].strftime("%d %b"))

    groups = parent_groups(db)
    cards = ""
    for g in groups:
        rep = parents_report(db, g["id"], kind)
        when = parents.sent_at(db, p["key"], g["id"])
        # a class with nothing in the stretch has nothing to tell its parents
        quiet = not any(r["set"] or r["lessons"] or r["items"] for r in rep["rows"])
        sent = (f'<span class="pill ok">Sent {E(practice_when(when))}</span>' if when
                else '<span class="pill mute">Nothing to report</span>' if quiet else "")
        n = len(rep["rows"])
        src = f'/parents/card.png?g={g["id"]}&amp;p={kind}'
        shots = [(f"{src}&amp;k=league", "League", "The class league")] + [
            (f'{src}&amp;k=student&amp;s={r["student"]["id"]}', r["student"]["name"],
             "Report for " + r["student"]["name"]) for r in rep["rows"]]
        pics = "".join(f'<a class="par-shot{" par-wide" if i == 0 else ""}" href="{href}"'
                       f' target="_blank" rel="noopener">'
                       f'<img src="{href}" alt="{E(alt)}" loading="lazy"><span>{E(label)}</span></a>'
                       for i, (href, label, alt) in enumerate(shots))
        cards += f"""<section class="card par-class">
  <div class="par-head">
    <label class="par-pick"><input type="checkbox" name="g" value="{g["id"]}"{"" if (when or quiet) else " checked"}>
    <span><strong>{E(g["name"])}</strong> <span class="sub">{E(rep["level"])} &middot; {n} students
    &middot; {n + 1} pictures</span></span></label>
    {sent}
  </div>
  <div class="par-pics">{pics}</div>
  <label class="f">Your note to these parents (optional, posted before the pictures)
    <textarea name="note_{g["id"]}" rows="2" placeholder="Masalan: Keyingi dars juma kuni."></textarea></label>
</section>"""
    can = bool(chan and token and not core.demo_on() and not going)
    button = (f'<button{"" if can else " disabled"}>Send to the channel</button>')
    why_not = ("" if can else
               '<p class="sub flush">%s</p>' % (
                   "The demo's classes are invented: nothing is sent from here." if core.demo_on()
                   else "Sending&hellip;" if going
                   else "Connect a channel first (below)." if not chan
                   else "The bot is not set up on this server."))
    refresh = '<meta http-equiv="refresh" content="6">' if going else ""
    body = f"""{refresh}<h1>Parents' channel</h1>
{flash}
<form method="post" action="/parents/send" class="par-form"
      onsubmit="return confirm('Post the ticked classes in the parents\\' channel?')">
  <input type="hidden" name="p" value="{kind}">
  <div class="par-bar">
    <div class="tabs">{tabs}</div>
    <span class="sub">{E(days)}</span>
    {button}
  </div>
  {why_not}
  {cards or '<div class="card empty-card"><p class="flush">No classes with students yet.</p></div>'}
</form>
<h2>Write to all parents</h2>
<div class="card"><form method="post" action="/parents/say">
  <label class="f">One message, posted in the channel as you write it
  <textarea name="text" rows="4" placeholder="Hurmatli ota-onalar! ... / Уважаемые родители! ..."></textarea></label>
  <button{"" if (chan and token and not core.demo_on()) else " disabled"}>Post it</button>
</form></div>
<h2>The channel</h2>
<div class="card">{chan_html}<div class="row-actions">{pick}</div>
<form method="post" action="/parents/channel" class="par-typed">
  <label class="f">Or type a public channel's name<input name="username" placeholder="@channel_name"></label>
  <button class="ghost">Use it</button></form></div>"""
    return html_response(page("Parents", body, "Parents"))


_PARENTS_CACHE = {}


def parents_report(db, gid, kind):
    """A class's report, kept for two minutes: the Parents page asks for it
    once and then once for every picture on it, all at the same moment."""
    key = (core.demo_on(), gid, kind)
    hit = _PARENTS_CACHE.get(key)
    if hit and time.time() - hit[0] < 120:
        return hit[1]
    rep = parents.class_report(db, gid, parents.period(kind, CFG), CFG)
    if len(_PARENTS_CACHE) > 64:
        _PARENTS_CACHE.clear()
    _PARENTS_CACHE[key] = (time.time(), rep)
    return rep


def view_parents_card(req, db):
    q = req.get("query", {})
    gid = (q.get("g", [""])[0] or "")
    if not gid.isdigit():
        return not_found()
    rep = parents_report(db, int(gid), parents_kind(q))
    if q.get("k") == ["student"]:
        sid = (q.get("s", [""])[0] or "")
        r = next((r for r in rep["rows"] if str(r["student"]["id"]) == sid), None)
        if not r:
            return not_found()
        png_bytes = card.student(r, rep)
    else:
        png_bytes = card.league(rep)
    return 200, [("Content-Type", "image/png"), ("Cache-Control", "no-store"),
                 ("Content-Length", str(len(png_bytes)))], png_bytes


def act_parents_send(req, db):
    f = req["form"]
    kind = parents_kind(f)
    if core.demo_on():
        return redirect(f"/parents?p={kind}&e=demo")
    if not CFG.get("telegram_token"):
        return redirect(f"/parents?p={kind}&e=bot")
    if not core.parents_channel(db):
        return redirect(f"/parents?p={kind}&e=channel")
    if parents.busy(db):
        return redirect(f"/parents?p={kind}&e=busy")
    known = {g["id"] for g in parent_groups(db)}
    gids = [int(v) for v in f.get("g", []) if v.isdigit() and int(v) in known]
    if not gids:
        return redirect(f"/parents?p={kind}&e=none")
    notes = {gid: (f.get("note_%d" % gid, [""])[0] or "").strip()[:600] for gid in gids}
    # marked as going before the thread starts, so a second press is refused
    core.meta_set(db, "parents_sending", json.dumps(
        {"kind": kind, "total": len(gids), "done": 0, "errors": [],
         "started": core.iso(core.now()), "touched": core.iso(core.now()), "finished": None}))
    import threading
    threading.Thread(target=parents.send_all, daemon=True,
                     args=(CFG["telegram_token"], kind, gids, notes, CFG)).start()
    return redirect(f"/parents?p={kind}&sent=1")


def act_parents_say(req, db):
    text = (req["form"].get("text", [""])[0] or "").strip()
    chan = core.parents_channel(db)
    if core.demo_on():
        return redirect("/parents?e=demo")
    if not text:
        return redirect("/parents?e=empty")
    if not chan:
        return redirect("/parents?e=channel")
    if not CFG.get("telegram_token"):
        return redirect("/parents?e=bot")
    import bot
    res = bot.send(CFG["telegram_token"], chan["id"], text[:4000])
    if not res.get("ok"):
        return redirect("/parents?e=said&why=" + urllib.parse.quote(
            str(res.get("description") or res.get("error") or "")[:200]))
    return redirect("/parents?said=1")


def act_parents_channel(req, db):
    """Choose one of the channels the bot has found, or name a public one."""
    f = req["form"]
    if core.demo_on():
        return redirect("/parents?e=demo")
    cid = (f.get("id", [""])[0] or "").strip()
    seen = {str(c["id"]): c for c in core.channels_seen(db)}
    if cid in seen:
        core.meta_set(db, "parents_channel", json.dumps(seen[cid]))
        return redirect("/parents")
    name = (f.get("username", [""])[0] or "").strip().lstrip("@").split("/")[-1]
    token = CFG.get("telegram_token")
    if not name or not token:
        return redirect("/parents?e=" + ("bot" if name else "channel"))
    import bot
    res = bot.call(token, "getChat", chat_id="@" + name)
    chat = res.get("result") or {}
    if not res.get("ok") or chat.get("type") != "channel":
        return redirect("/parents?e=said&why=" + urllib.parse.quote(
            "no channel called @%s that the bot can see" % name))
    core.channel_seen(db, chat["id"], chat.get("title") or "", chat.get("username") or "", True)
    core.meta_set(db, "parents_channel", json.dumps(
        {"id": chat["id"], "title": chat.get("title") or "", "username": chat.get("username") or ""}))
    return redirect("/parents")


# ------------------------------------------------ the student page, as a student
#
# The teacher's way to go through the student page without joining a class
# through the bot and doing every task to see what comes after it. A copy of
# today's site gets one more student in the class the teacher picks; the
# student page of that student opens from the teacher's own browser only, and
# a strip at its top does the work - answers a part, finishes a booklet,
# marks the homework - so the next screen is one tap away. Nothing reaches
# the real site: the copy is a separate file, and the bot writes down what it
# would have sent instead of sending it.

PRACTICE_SCREENS = [(key, label, p, plabel) for key, label, pages in PORTAL
                    for p, plabel in pages]


def practice_when(stamp):
    try:
        return core.parse(stamp).strftime("%d %b, %H:%M")
    except Exception:
        return stamp or ""


def view_practice(req, db):
    info = core.practice_info()
    q = req.get("query", {}) if isinstance(req, dict) else {}
    note = ""
    if q.get("e") == ["room"]:
        note = ('<div class="flash err">There is not enough room on the server for a '
                'second copy of the site. Free some space on the Settings page first.</div>')
    now_card = ""
    if info:
        mb = info["bytes"] / 1048576
        now_card = f"""<div class="card try-now">
  <h3>Your practice student is in class {E(info["group"])}</h3>
  <p class="sub">{E(info["level"] or "no level")} &middot; copy made {E(practice_when(info["made"]))}
  &middot; {mb:.0f} MB</p>
  <div class="row-actions">
    <a class="btn" href="/s/{E(info["token"])}">Open the student page</a>
    <a class="btn ghost" href="/practice/screens">Every screen at once</a>
    <form method="post" action="/practice/end"><button class="ghost danger">Throw it away</button></form>
  </div>
</div>"""
    groups = db.execute("SELECT * FROM groups WHERE archived=0 ORDER BY name").fetchall()
    rows = ""
    for g in groups:
        n = db.execute("SELECT COUNT(*) n FROM students WHERE group_id=? AND active=1",
                       (g["id"],)).fetchone()["n"]
        level = core.level_name(db, core.level_of(db, g["id"])) or "no level"
        here = info and info["group_id"] == g["id"]
        rows += f"""<div class="try-class">
  <div><strong>{E(g["name"])}</strong><div class="sub">{E(level)} &middot; {n} students</div></div>
  <form method="post" action="/practice/start"><input type="hidden" name="group_id" value="{g["id"]}">
  <button class="{"ghost" if info else ""}">{"Start again here" if here else "Be a new student here"}</button></form>
</div>"""
    body = f"""<h1>The student page, as a student</h1>
{note}{now_card}
<div class="card">
  <h3>Pick a class</h3>
  <p class="sub">You join it as a new student in a copy of today's site: the same handouts,
  homework, tests and classmates. Buttons at the top of the page do each task for you, so the
  next screen is one tap away. Your real students, their marks and the league are not touched,
  and the bot sends nothing &mdash; what it would have said is shown on the page instead.
  {"Picking a class makes a fresh copy and replaces the one you have." if info else ""}</p>
  <div class="try-classes">{rows or '<p class="sub">No classes yet.</p>'}</div>
</div>"""
    return html_response(page("As a student", body, "As a student"))


def act_practice_start(req, db):
    gid = (req["form"].get("group_id", [""])[0] or "").strip()
    if not gid.isdigit() or not db.execute("SELECT 1 FROM groups WHERE id=?", (int(gid),)).fetchone():
        return redirect("/practice")
    token = core.practice_start(int(gid))
    if not token:
        return redirect("/practice?e=room")
    return redirect(f"/s/{token}")


def act_practice_end(req, db):
    core.practice_end()
    return redirect("/practice")


def view_practice_screens(req, db):
    info = core.practice_info()
    if not info:
        return redirect("/practice")
    tok = E(info["token"])
    cells = "".join(f"""<figure class="try-screen">
  <figcaption><span>{E(label)} &rsaquo; <strong>{E(plabel)}</strong></span>
  <a class="linky" href="/s/{tok}?tab={p}">Open</a></figcaption>
  <div class="try-phone"><iframe loading="lazy" title="{E(plabel)}"
    src="/s/{tok}?tab={p}&amp;frame=1"></iframe></div>
</figure>""" for _key, label, p, plabel in PRACTICE_SCREENS)
    body = f"""<div class="try-strip"><strong>Class {E(info["group"])}</strong>
<span class="sub">every screen of the student page, as your practice student sees it now</span>
<a class="btn ghost" href="/practice">Back</a></div>
<div class="try-screens">{cells}</div>"""
    return html_response(page("Every screen", body, "As a student"))


def practice_bar(db, s, token, tab, query):
    """The strip at the top of the practice student's page: where this is,
    and the buttons that do the task on screen."""
    info = core.practice_info() or {}
    here = f"/s/{E(token)}/practice"

    def button(what, label, ghost=False, **fields):
        hidden = "".join(f'<input type="hidden" name="{k}" value="{E(str(v))}">'
                         for k, v in fields.items())
        return (f'<form method="post" action="{here}/{what}">{hidden}'
                f'<button class="{"ghost" if ghost else ""}">{label}</button></form>')

    doing = ""
    hid = query.get("h", [""])[0]
    tid = query.get("t", [""])[0]
    if tab == "handouts" and hid.isdigit():
        hid = int(hid)
        blocker = core.handout_blocked_by(db, hid, s)
        if blocker:
            doing = button("finish", "Finish %s for me" % E(short_title(blocker)), h=blocker["id"])
        else:
            n = practice_current_part(db, s, hid)
            if n is not None:
                doing = (button("fill", "Answer part %d for me" % n, h=hid, part=n, how="right")
                         + button("fill", "&hellip; with mistakes", True, h=hid, part=n, how="mistakes")
                         + button("finish", "Finish the whole handout", True, h=hid))
    elif tab == "tests" and tid.isdigit() and not core.sat_already(db, int(tid), s["id"]):
        doing = (button("test", "Answer this test for me", t=tid, how="right")
                 + button("test", "&hellip; with mistakes", True, t=tid, how="mistakes"))
    if practice_waiting(db, s["id"]):
        doing += button("mark", "Mark my homework as the teacher", tab == "handouts")

    heard = core.practice_heard(db)
    said = ""
    if heard:
        items = "".join(f'<li><span class="sub">{E(practice_when(h["at"]))} &middot; to '
                        f'{E(h["to"])}</span><br>{E(h["text"]).replace(chr(10), "<br>")}</li>'
                        for h in heard)
        said = (f'<details class="try-heard"><summary>What Telegram would have sent '
                f'({len(heard)})</summary><ol>{items}</ol></details>')
    return f"""<div class="trybar" role="note">
  <div class="try-where"><strong>Practice copy</strong> &middot; class {E(info.get("group", ""))}
  <span class="sub">&mdash; nothing here reaches your students or the real site</span></div>
  <div class="try-do">{doing}
    <a class="btn ghost" href="/practice/screens">Every screen</a>
    <a class="btn ghost" href="/practice">Leave</a></div>
  {said}
</div>"""


def practice_current_part(db, s, hid):
    """The part of this handout the practice student is on, or None."""
    t = db.execute("SELECT layout FROM dtests WHERE id=?", (hid,)).fetchone()
    if not t:
        return None
    _intro, parts = handout_parts(t["layout"] or "")
    a = db.execute("SELECT id FROM dattempts WHERE test_id=? AND student_id=?"
                   " ORDER BY id DESC LIMIT 1", (hid, s["id"])).fetchone()
    done = core.handout_parts_done(db, a["id"]) if a else {}
    return next((n for n, *_r in parts if n not in done), None)


def practice_waiting(db, sid):
    """The practice student's newest piece of homework that nobody has marked."""
    return db.execute(
        "SELECT * FROM submissions WHERE student_id=? AND status='pending'"
        " AND IFNULL(draft, 0)=0 ORDER BY id DESC LIMIT 1", (sid,)).fetchone()


PRACTICE_SENTENCE = ("I think this is true for me because I do it every day "
                     "with my family and friends.")


def practice_answer(q, letters, rnd, mistakes, others):
    """What a student might have put in one box: the key's answer, and now
    and then - when asked for mistakes - something else."""
    kind = q["control"] if "control" in q.keys() else None
    answer = (q["answer"] or "").split("/")[0].strip()
    slip = mistakes and rnd.random() < 0.2
    if kind in OPTIONAL_BOXES:
        return answer if kind == "tick" else ""      # a partner's answer stays empty at home
    if letters:
        right = next((l for l in letters if q["answer"] and core.answer_matches(l, q["answer"])),
                     letters[0])
        wrong = [l for l in letters if l != right]
        return rnd.choice(wrong) if (slip and wrong) else right
    if q["kind"] == "open" or not q["answer"]:
        return PRACTICE_SENTENCE if core.is_writing(q) else "my own answer"
    if slip:
        wrong = [o for o in others if o and not core.answer_matches(o, q["answer"])]
        return rnd.choice(wrong) if wrong else "no idea"
    return answer


def practice_fill(db, test_id, nums, mistakes, seed):
    """{question id: answer} for the boxes numbered `nums` (all of them when
    None), and the questions themselves."""
    qs = {q["id"]: q for q in db.execute(
        "SELECT id, num, kind, answer, control FROM dquestions WHERE test_id=?", (test_id,))}
    letters = {}
    for o in db.execute("SELECT o.question_id, o.letter FROM doptions o JOIN dquestions q"
                        " ON q.id=o.question_id WHERE q.test_id=? ORDER BY o.id", (test_id,)):
        letters.setdefault(o["question_id"], []).append(o["letter"])
    mine = [q for q in qs.values() if nums is None or q["num"] in nums]
    others = [(q["answer"] or "").split("/")[0].strip() for q in mine
              if q["answer"] and q["id"] not in letters]
    rnd = random.Random(seed)
    return qs, {q["id"]: practice_answer(q, letters.get(q["id"]), rnd, mistakes, others)
                for q in mine}


def practice_check_part(db, token, s, hid, part, mistakes):
    """Answer one part of a handout and check it, the way the page would."""
    t = db.execute("SELECT layout FROM dtests WHERE id=?", (hid,)).fetchone()
    markup = {n: m for n, _a, _b, m in handout_parts(t["layout"] or "")[1]}.get(part)
    if markup is None:
        return None
    a = db.execute("SELECT id FROM dattempts WHERE test_id=? AND student_id=?"
                   " ORDER BY id DESC LIMIT 1", (hid, s["id"])).fetchone()
    aid = a["id"] if a else core.start_attempt(db, hid, s["id"])
    qs, typed = practice_fill(db, hid, set(part_keys(markup)), mistakes, hid * 100 + part)
    _status, _headers, blob = check_part(db, token, hid, aid, part, qs, typed)
    return json.loads(blob.decode("utf-8")).get("go")


def act_practice(req, db, token, what):
    """One of the practice strip's buttons."""
    s = core.student_by_token(db, token)
    if not s or not core.practice_on():
        return not_found()
    f = req["form"]
    mistakes = f.get("how", [""])[0] == "mistakes"
    hid = f.get("h", [""])[0]
    if what in ("fill", "finish") and hid.isdigit():
        hid = int(hid)
        if not core.handout_open_to(db, hid, s["group_id"]):
            return redirect(f"/s/{token}?tab=handouts")
        if what == "fill":
            part = f.get("part", [""])[0]
            go = practice_check_part(db, token, s, hid, int(part), mistakes) if part.isdigit() else None
            return redirect(go or f"/s/{token}?tab=handouts&h={hid}")
        go = None
        for _i in range(100):
            n = practice_current_part(db, s, hid)
            if n is None:
                break
            go = practice_check_part(db, token, s, hid, n, True)
            if go is None:
                break
        return redirect(f"/s/{token}?tab=handouts&h={hid}&part=end")
    tid = f.get("t", [""])[0]
    if what == "test" and tid.isdigit():
        tid = int(tid)
        ok = db.execute("SELECT id FROM dtests WHERE id=? AND published=1", (tid,)).fetchone()
        if ok and not core.sat_already(db, tid, s["id"]):
            _qs, given = practice_fill(db, tid, None, mistakes, tid)
            core.submit_attempt(db, core.start_attempt(db, tid, s["id"]), given)
        return redirect(f"/s/{token}?tab=tests&t={tid}")
    if what == "mark":
        sub = practice_waiting(db, s["id"])
        if sub:
            form = {"score": ["7"], "note": ["Good work. Check your articles and "
                                             "past tenses again."]}
            form.update({"c_" + k: ["6"] for k in core.CRITERIA_KEYS})
            if save_grade(db, sub, form) is not None:
                notify_graded(db, sub["id"])
        return redirect(f"/s/{token}?tab=feedback")
    return redirect(f"/s/{token}")



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


def view_transfer_json(req, db):
    """Everything the Import page can read back: students, homework, marks.

    Not the photographs. Every photograph on this server would have to be
    read into memory, base64 encoded - which makes it a third bigger again -
    and then held a second time inside one JSON string, all before a single
    byte reaches the teacher. There are gigabytes of them. The server has
    nothing like that much memory, so asking for this file used to kill the
    site outright, which is not a backup: it is an outage with a download
    button. The photographs already leave the volume by their own path, the
    daily copy to Telegram.
    """
    import transfer
    was, transfer.TABLES_WITH_PHOTOS = transfer.TABLES_WITH_PHOTOS, False
    try:
        data = transfer.export_db(db)
    finally:
        transfer.TABLES_WITH_PHOTOS = was
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
<div class="gap-3"><button>Import</button></div></form>
<p class="sub gap-3">This merges rather than replaces. Anything
already here is matched and left alone, so importing the same file twice changes
nothing.</p></div>
<h2>Download a backup</h2>
<div class="card"><p class="sub gap-0">Everything in one file:
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
<div style="display:flex;gap:8px;margin-top:18px;flex-wrap:wrap;align-items:center">
  <button onclick="step()" id="go">Start</button>
  <button class="ghost" onclick="toggleAuto()" id="autobtn">Auto: on</button>
  <label class="sub">Table for
    <select id="showfor" onchange="setShowFor(this.value)">
      <option value="3">3s</option><option value="5" selected>5s</option>
      <option value="8">8s</option><option value="10">10s</option>
    </select></label>
  <label class="sub">Start at
    <input id="minplayers" type="number" min="1" max="40" value="2"
           style="width:56px" onchange="setMin(this.value)"> in the room</label>
  <span class="sub" id="autonote"></span>
  <button class="ghost" onclick="if(confirm('End this game?'))location.href='/play/{g["id"]}/end'">End game</button>
</div>
<script>
const GID = {g["id"]};
let last = "", ac = null, lastTick = -1, lastState = "";
// The room runs itself: the clock ends a question, the table stands for a few
// seconds, then the next one comes up. Turning it off hands the pace back, for
// when a question is worth talking about.
let auto = true, revealAt = 0, showFor = 5;
// the lobby starts itself once the room has stopped filling up, so nobody is
// left outside because the teacher pressed Start a moment too early
let minPlayers = 2, settleFor = 15, lastCount = -1, steadySince = 0;

function remember(key, value) {{ try {{ localStorage.setItem(key, value); }} catch (e) {{}} }}
function recall(key, fallback) {{
  try {{ const v = localStorage.getItem(key); return v === null ? fallback : v; }}
  catch (e) {{ return fallback; }}
}}
function setShowFor(v) {{ showFor = +v || 5; revealAt = 0; remember('gameShowFor', showFor); }}
function setMin(v) {{ minPlayers = Math.max(1, +v || 2); remember('gameMinPlayers', minPlayers); }}
function toggleAuto() {{
  auto = !auto;
  revealAt = 0; steadySince = 0;
  document.getElementById('autobtn').textContent = 'Auto: ' + (auto ? 'on' : 'off');
}}
function loadPrefs() {{
  showFor = +recall('gameShowFor', 5) || 5;
  minPlayers = +recall('gameMinPlayers', 2) || 2;
  const sf = document.getElementById('showfor'); if (sf) sf.value = String(showFor);
  const mp = document.getElementById('minplayers'); if (mp) mp.value = String(minPlayers);
}}
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

  // ---- run the room, unless the teacher has taken the wheel
  let note = '';
  if (auto && !busy) {{
    if (s.state === 'lobby') {{
      // wait until the count has held still: someone is always last through the door
      if (s.players.length !== lastCount) {{
        lastCount = s.players.length;
        steadySince = Date.now();
      }}
      if (s.players.length >= minPlayers) {{
        const left = Math.ceil((settleFor * 1000 - (Date.now() - steadySince)) / 1000);
        if (left <= 0) {{ step(s.state, s.q_index); }}
        else {{ note = 'starting in ' + left + 's'; }}
      }} else {{
        note = 'waiting for ' + (minPlayers - s.players.length) + ' more';
      }}
    }} else if (s.state === 'question') {{
      const everyone = s.players.length > 0 && s.answered >= s.players.length;
      if (s.left <= 0 || everyone) {{
        note = everyone ? 'everyone answered' : '';
        step(s.state, s.q_index);
      }}
    }} else if (s.state === 'reveal') {{
      if (!revealAt) revealAt = Date.now();
      const left = Math.ceil((showFor * 1000 - (Date.now() - revealAt)) / 1000);
      if (left <= 0) {{ step(s.state, s.q_index); }}
      else {{ note = 'next question in ' + left + 's'; }}
    }}
  }}
  if (s.state !== 'reveal') revealAt = 0;
  if (s.state !== 'lobby') steadySince = 0;
  const noteEl = document.getElementById('autonote');
  if (noteEl.textContent !== note) noteEl.textContent = note;
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
    '<th></th><th>Right</th><th class="right">Points</th></tr>' +
    rows.map((r, i) => {{
      const d = r.delta > 0 ? '<span class="gup">&uarr;' + r.delta + '</span>'
              : r.delta < 0 ? '<span class="gdown">&darr;' + (-r.delta) + '</span>' : '';
      return '<tr><td>' + (i + from) + '.</td><td class="gcell">' + r.who +
        '</td><td>' + esc(r.name) + (r.run >= 2 ?
          ' <span class="grunmini">' + r.run + '🔥</span>' : '') +
        '</td><td>' + d + '</td><td>' + r.correct +
        '</td><td class="right"><strong>' + r.score + '</strong></td></tr>';
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
async function step(fromState, fromIndex) {{
  if (busy) return;                 // one press is one move, however hard it is hit
  busy = true;
  revealAt = 0; steadySince = 0;
  const btn = document.getElementById('go');
  btn.disabled = true;
  btn.textContent = '\u2026';
  Music.nudge();                    // the gesture browsers require for audio
  try {{
    // say which step this came from, so a stale press or a second board
    // cannot skip a question nobody has seen
    const body = (fromState === undefined) ? '' :
      'state=' + encodeURIComponent(fromState) + '&from=' + fromIndex;
    const r = await fetch('/play/' + GID + '/next', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
      body: body}});
    last = "";
    render(await r.json());         // straight from the reply, not the next poll
  }} catch (e) {{
    btn.disabled = false;
  }}
  busy = false;
}}
loadPrefs();
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
    f = req.get("form") or {}
    want = (f.get("state", [""])[0] or "").strip() or None
    idx = (f.get("from", [""])[0] or "").strip()
    core.advance_game(db, game_id, want, int(idx) if idx.lstrip("-").isdigit() else None)
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


def champ_row(db, r, show_group=True, me=None, tops=None):
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
        # nothing is out of anything now, so a bar is drawn against the best in
        # that column rather than against a ceiling that no longer exists
        best = (tops or {}).get(key) or 0
        share = (got / best * 100.0) if best else 0
        bars += (f'<td class="cpt"><span class="cbar"><i style="width:'
                 f'{min(100, share):.0f}%"></i></span>{got:g}</td>')
    group = f'<td>{E(group_name(db, st["group_id"]))}</td>' if show_group else ""
    mine = ' class="me"' if me == st["id"] else ""
    seen = r.get("lessons", 0)
    sets = r.get("sets", 0)
    of, hw_of = core.SEASON_LESSONS, core.SEASON_HOMEWORK
    hw = (f'<td class="sub">{hw_of}/{hw_of} &#10003;</td>' if sets >= hw_of
          else f'<td class="sub">{sets}/{hw_of}</td>')
    if r.get("done") and r.get("final"):
        lessons = (f'<td class="sub" title="lessons finished on {r["closed"]}; fifteen sets'
                   f' of homework due and marked">{of}/{of} &#10003;</td>')
    elif r.get("done"):
        lessons = (f'<td class="sub" title="lessons and sets finished, but'
                   f' the last homework is still to be marked">{of}/{of} '
                   f'<span class="pill watch">provisional</span></td>')
    elif r.get("closed"):
        lessons = (f'<td class="sub" title="lessons finished on {r["closed"]}; the season stays'
                   f' open until {hw_of} sets of homework have come due">{of}/{of} &#10003;</td>')
    else:
        lessons = f'<td class="sub">{seen}/{of}</td>'
    return (f'<tr{mine}><td>{place}</td>'
            f'<td><a href="/students/{st["id"]}">{E(st["name"])}</a></td>{group}'
            f'<td><strong>{r["total"]:g}</strong></td>{bars}{hw}{lessons}'
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
<p class="sub">A season runs for <strong>{core.SEASON_LESSONS} lessons and
{core.SEASON_HOMEWORK} sets of homework per student</strong>, not for a calendar month, so every
student is judged over exactly the same amount of teaching and homework. A student's season
closes once they have had both, and their score is frozen there, however long the rest of the
school takes to catch up.</p>
<form method="post" action="/championship/start" class="gap-4">
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

    head = "".join(f'<th title="up to {w:g} points each time">{E(l)}</th>'
                   for _k, l, w in core.CHAMPIONSHIP)
    tops = {k: max([r["points"].get(k) or 0 for r in standing["rows"]] or [0])
            for k, _l, _w in core.CHAMPIONSHIP}
    body = "".join(champ_row(db, r, show_group=gid is None, tops=tops)
                   for r in standing["rows"])

    winner = next((r for r in standing["rows"] if r["rank"] == 1), None)
    top = ""
    if winner:
        top = (f'<div class="champ-hero"><div class="sub">Leading season '
               f'{standing["season"]}</div>'
               f'<div class="champ-name">{E(winner["student"]["name"])}</div>'
               f'<div class="sub">{E(group_name(db, winner["student"]["group_id"]))}'
               f' &middot; {winner["total"]:g} points</div></div>')

    champs = {} if gid else core.class_champions(full, db)
    classes = ""
    for cid, r in sorted(champs.items(), key=lambda kv: group_name(db, kv[0])):
        classes += (f'<div class="quick"><div class="sub">{E(group_name(db, cid))}</div>'
                    f'<strong>{E(r["student"]["name"])}</strong>'
                    f'<div class="sub">{r["total"]:g} points</div></div>')

    total = len(standing["rows"])
    done = standing["finished"]
    settled = sum(1 for r in standing["rows"] if r.get("final"))
    # a resumed pause leaves no mark on the page, and silently drops the lessons
    # and homework that fell inside it - so say so plainly
    cfgx = core.load_config()
    gaps = ""
    for i, (a, b) in enumerate(standing.get("pauses") or []):
        first = core.local_day(core.parse(a), cfgx)
        last = ("still paused" if b == core.SEASON_OPEN
                else core.local_day(core.parse(b), cfgx))
        gaps += (f'<li><strong>{E(first)} to {E(last)}</strong> is not counted &mdash; '
                 f'lessons taught and homework due in that stretch score nothing.'
                 f'<form method="post" action="/championship/unpause" '
                 f'onsubmit="return confirm(\'Count {first} to {last} after all? '
                 f'Everyone\\u2019s score will change.\')">'
                 f'<input type="hidden" name="i" value="{i}">'
                 f'<button class="linky">count it after all</button></form></li>')
    skipped = ""
    gapbox = (f'<div class="card paused"><strong>Some of the season is being skipped'
              f'</strong><ul class="attn">{gaps}</ul></div>' if gaps else "")
    if standing["paused"]:
        control = (f'<form method="post" action="/championship/resume">'
                   f'<button>Resume season {standing["season"]}</button></form>')
        paused = (f'<div class="card paused"><strong>The league is paused.</strong>'
                  f'<p class="sub gap-2">Paused since '
                  f'{E(standing["paused_at"][:10])}. Nothing counts while it is off: '
                  f'homework marked now, lessons taught now and words learnt now all '
                  f'stay out of the season, and nobody\'s lesson count moves. The table '
                  f'below is frozen exactly as it stood.</p>'
                  f'<div class="gap-3">{control}</div></div>')
    else:
        paused = ""
        control = (f'<form method="post" action="/championship/pause">'
                   f'<button class="ghost">Pause the league</button></form>')
    when = {"homework": "every set you mark", "conduct": "every lesson"}
    rules = "".join(
        f'<li><strong>{E(l)}</strong> &mdash; up to {w:g} points '
        f'{when.get(k, "each time")}</li>' for k, l, w in core.CHAMPIONSHIP)
    body_html = f"""<h1>Championship</h1>
<p class="sub">Season {standing["season"]}, counting from
{E(standing.get("start_day") or standing["start"][:10])}{skipped}.
{core.SEASON_LESSONS} lessons and {core.SEASON_HOMEWORK} sets of homework each, everyone in the
school. It runs like a football league:
every piece of homework you set is worth up to {core.HOMEWORK_PER_SET:g} points and every
lesson up to {core.CONDUCT_PER_LESSON:g}, and those points are added to the running total
and never taken away. A digital test counts as a piece of homework, marked the moment it is
handed in. Late or never handed in scores nought; anything still waiting to be
marked is left out until you mark it.</p>
{top}
{paused}
{gapbox}
<div class="card"><strong>{done} of {total}</strong> students have finished their
{core.SEASON_LESSONS} lessons and {core.SEASON_HOMEWORK} sets of homework{", " + str(settled) + " of them settled" if done else ""}.
<p class="sub gap-2">Every student's season is the same size: their first
{core.SEASON_HOMEWORK} sets of homework and their first {core.SEASON_LESSONS} lessons. A set is
the homework that shares a deadline, and it takes its place once the deadline passes &mdash;
handed in, missed (a nought) or waiting to be marked. A class preparing for an exam with no
homework for a while keeps its season open until it has had its {core.SEASON_HOMEWORK} sets;
a class set more than that stops counting at the {core.SEASON_HOMEWORK}th. A student is marked
<span class="pill watch">provisional</span> while the last of their sets is waiting to be marked.</p>
<p class="sub gap-2">A student's lesson count only moves when you record
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
{core.MIN_GRADED} deadlines behind them needed to be eligible. The rest are listed below
the line for now.</p>
<div class="tablewrap"><table><tr><th>#</th><th>Student</th>
{"<th>Group</th>" if gid is None else ""}
<th>Total</th>{head}<th title="sets of homework due so far, of {core.SEASON_HOMEWORK}">Homework sets</th>
<th>Lessons</th><th>Handed in</th></tr>
{body or '<tr><td colspan=12 class="sub">Nobody yet.</td></tr>'}</table></div>
<h2>How the points work</h2>
<div class="card"><ul class="rules">{rules}</ul>
<p class="sub gap-3"><strong>Each time, not in total.</strong> A set of
homework marked 10, 8 and 7 averages 8.3, which is 2.5 of the 3 it was worth. The next set
marked 10, 9 and 8 averages 9, which is 2.7. That student now has 5.2 for homework, and it
keeps climbing all season.</p>
<p class="sub gap-3">Homework is the average mark out of ten, scaled to
3; a piece handed in after its deadline is a nought in that average. A digital test scores
the same way - its result out of ten, worth up to {core.HOMEWORK_PER_SET:g} - and only the
first sitting counts, so retaking a test to learn from it never moves the table. A test
that carries no deadline cannot be missed, so not sitting one is no points rather than a
nought. In the lesson is the average of punctuality, behaviour and taking
part, and each lesson is worth up to five. Both add up across the season rather than
averaging out: full marks means {core.SEASON_HOMEWORK} sets of homework at ten and
{core.SEASON_LESSONS} lessons at five, the same for everyone. A deadline that passed with nothing against it is a
nought, exactly like one handed in late. Work waiting to be marked is left out until you
mark it. A student needs {core.MIN_GRADED} deadlines behind them to be eligible. Nothing you have not recorded scores anything, so
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


def act_unpause_span(req, db):
    """Undo one recorded pause, so that stretch counts again."""
    i = (req["form"].get("i", [""])[0] or "").strip()
    if i.isdigit():
        core.drop_pause(db, int(i))
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


# ------------------------------------------------------------- the shelves
# Materials is a tree: level, collection, section, unit. Every step is a set of
# cards that say what they hold and how much room it takes; the last step is the
# files, each a row that can be ticked, and a page of them can go in one go.

SECTION_LOOKS = {
    "Unit handouts": ("file", "plum"), "Listening audios": ("headphones", "blue"),
    "Workbook audios": ("headphones", "green"), "Reading plus": ("book", "amber"),
    "Academic skills": ("cap", "plum"), "Unit vocabularies": ("list", "green"),
    "Unit tests": ("clipboard", "rose"), "Reading": ("book", "amber"), "Listening": ("headphones", "blue"),
    "Vocabulary": ("list", "green"), "Grammar": ("layers", "plum"), "Writing": ("file", "amber"),
    "Paper": ("file", "plum"), "Audio": ("headphones", "blue"), "Answer key": ("check", "green"),
}
COLLECTION_LOOKS = {"empower": ("book", "plum"), "selfstudy": ("user", "blue"), "practice": ("clipboard", "amber")}
LEVEL_TONES = ["green", "blue", "plum", "amber", "rose", "plum"]
FILE_KINDS = [  # (extensions, what it is, drawing, colour)
    ((".mp3", ".m4a", ".wav", ".ogg", ".aac", ".wma"), "Audio", "headphones", "blue"),
    ((".pdf",), "PDF", "file", "rose"),
    ((".doc", ".docx", ".odt", ".rtf", ".txt"), "Document", "file", "plum"),
    ((".ppt", ".pptx", ".key", ".odp"), "Slides", "slides", "amber"),
    ((".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic"), "Picture", "image", "green"),
    ((".mp4", ".mov", ".avi", ".mkv", ".webm"), "Video", "video", "amber"),
]


def file_kind(name):
    low = (name or "").lower()
    for exts, label, icon, tone in FILE_KINDS:
        if low.endswith(exts):
            return label, icon, tone
    return "File", "file", "plum"


def size_of(rows):
    return sum(r["size"] or 0 for r in rows)


def files_meta(rows):
    """'20 files · 40.2 MB', or 'Empty'."""
    n = len(rows)
    if not n:
        return "Empty"
    return "%d file%s · %s" % (n, "" if n == 1 else "s", core.human_size(size_of(rows)))


def shelf_card(href, name, meta, icon=None, tone="plum", empty=False, badge=None, small=False):
    """A step down the tree: a drawing (or a level's letters), the name, what it holds."""
    mark = (f'<span class="lvl-badge">{E(badge)}</span>' if badge
            else look_icon(icon) if icon else "")
    return (f'<a class="shelf t-{tone}{" empty" if empty else ""}{" small" if small else ""}" href="{href}">'
            f'{mark}<span class="shelf-text"><span class="shelf-name">{name}</span>'
            f'<span class="shelf-meta">{E(meta)}</span></span>'
            f'<svg class="shelf-go" viewBox="0 0 24 24" aria-hidden="true">{LOOK_ICONS["chevron"]}</svg></a>')


def shelf_grid(cards, small=False):
    return f'<div class="shelves{" small" if small else ""}">{cards}</div>'


def crumbs(db, level_id, coll, cat, unit, base):
    """Where you are, every step a way back up."""
    bits = [f'<a href="/materials">All levels</a>']
    if level_id:
        bits.append(f'<a href="{base[:-1]}">{E(core.level_name(db, level_id) or "")}</a>')
    if coll:
        bits.append(f'<a href="{base}c={coll}">{E(core.collection_label(coll))}</a>')
    if cat:
        bits.append(f'<a href="{base}c={coll}&amp;s={urllib.parse.quote(cat)}">{E(cat)}</a>')
    if unit is not None:
        bits.append("No unit" if unit == -1 else "Welcome" if unit == 0
                    else "%s %d" % (core.unit_word(coll), unit))
    last = bits.pop()
    sep = '<span class="crumb-sep" aria-hidden="true">›</span>'
    here = re.sub(r"<a [^>]*>(.*)</a>", r"\1", last)
    return ('<nav class="crumbs">' + sep.join(bits + [f'<span class="here">{here}</span>']) + "</nav>")


def wipe_form(back, rows, scope, what):
    """The one button that empties the place you are looking at - this level's
    own files only (shared files stay; they are deleted by ticking them)."""
    if not rows:
        return ""
    fields = "".join(f'<input type="hidden" name="{k}" value="{E(str(v))}">' for k, v in scope.items() if v is not None)
    n = len(rows)
    label = "Delete all %d file%s here" % (n, "" if n == 1 else "s")
    return (f'<form class="wipe" method="post" action="/materials/delete">'
            f'<input type="hidden" name="back" value="{E(back)}"><input type="hidden" name="what" value="scope">'
            f'{fields}<div class="wipe-text"><strong>{E(what)}</strong>'
            f'<span>{E(files_meta(rows))} · files shared with every level stay</span></div>'
            f'<button class="danger-btn" data-arm="Delete {n} file{"" if n == 1 else "s"} for good? Tap again">'
            f'{look_icon("trash", "btn-ico")}{label}</button></form>')


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
    cards, total = "", []
    for k, l in enumerate(levels):
        rows = core.materials_at_level(db, l["id"])
        total += [r for r in rows if r["level_id"] == l["id"]]
        initials = "".join(w[0] for w in re.findall(r"[A-Za-z]+", l["name"]))[:2].upper()
        cards += shelf_card(f'/materials?level={l["id"]}', E(l["name"]), files_meta(rows),
                            tone=LEVEL_TONES[k % len(LEVEL_TONES)], empty=not rows, badge=initials)
    shared = [r for r in db.execute("SELECT * FROM materials WHERE active=1 AND level_id IS NULL")]
    every = total + shared
    summary = (f'<p class="shelf-sum">{look_icon("folder", "sum-ico")}<span><strong>{len(every)} files</strong>'
               f' on the shelves · {E(core.human_size(size_of(every)))}'
               + (f' · {len(shared)} shared with every level' if shared else "") + "</span></p>")
    return summary + shelf_grid(cards)


def shelf_tiles(db, level_id, base):
    """Collections first - the same three steps students take in the bot."""
    cards = ""
    for k in core.COLLECTION_ORDER:
        rows = core.materials_at_level(db, level_id, k)
        icon, tone = COLLECTION_LOOKS.get(k, ("folder", "plum"))
        cards += shelf_card(f'{base}c={k}', E(core.collection_label(k)), files_meta(rows),
                            icon=icon, tone=tone, empty=not rows)
    own = core.materials_scope(db, level_id)
    name = core.level_name(db, level_id) or "this level"
    return (crumbs(db, level_id, None, None, None, base) + shelf_grid(cards)
            + wipe_form(base[:-1], own, {"level": level_id}, "Everything at %s" % name))


def section_tiles(db, level_id, coll, base):
    cards = ""
    for name in core.sections(coll):
        rows = core.materials_at_level(db, level_id, coll, name)
        icon, tone = SECTION_LOOKS.get(name, ("folder", "plum"))
        cards += shelf_card(f'{base}c={coll}&amp;s={urllib.parse.quote(name)}', E(name), files_meta(rows),
                            icon=icon, tone=tone, empty=not rows)
    own = core.materials_scope(db, level_id, coll)
    return (crumbs(db, level_id, coll, "", None, base) + shelf_grid(cards)
            + wipe_form(f"{base}c={coll}", own, {"level": level_id, "c": coll},
                        "Everything in %s" % core.collection_label(coll)))


def test_tiles(db, level_id, coll, base):
    """Twenty cards - Test 1 to Test 20 - each holding everything for that test."""
    href = f'{base}c={coll}'
    cards = ""
    for n in core.tests_in_collection(coll):
        rows = core.files_in_test(db, level_id, coll, n)
        cards += shelf_card(f'{href}&amp;u={n}', "Test %d" % n, files_meta(rows), small=True, empty=not rows)
    own = core.materials_scope(db, level_id, coll)
    return (crumbs(db, level_id, coll, None, None, base) + shelf_grid(cards, small=True)
            + wipe_form(href, own, {"level": level_id, "c": coll}, "Every practice test at this level"))


def unit_tiles(db, level_id, coll, cat, base):
    numbers = core.units_for_level(db, level_id)
    units = core.units_in(db, level_id, coll, cat)
    if 0 in units:
        numbers = [0] + numbers
    href = f'{base}c={coll}&amp;s={urllib.parse.quote(cat)}'
    cards = ""
    for n in numbers:
        rows = core.materials_in_unit(db, level_id, coll, cat, n)
        cards += shelf_card(f'{href}&amp;u={n}', "Welcome" if n == 0 else "Unit %d" % n, files_meta(rows),
                            small=True, empty=not rows)
    loose = [m for m in core.materials_at_level(db, level_id, coll, cat) if not m["unit"]]
    if loose:
        cards += shelf_card(f'{href}&amp;u=-1', "No unit", files_meta(loose), small=True)
    own = core.materials_scope(db, level_id, coll, cat)
    return (crumbs(db, level_id, coll, cat, None, base) + shelf_grid(cards, small=True)
            + wipe_form(f"{base}c={coll}&s={urllib.parse.quote(cat)}", own, {"level": level_id, "c": coll, "s": cat},
                        "Everything in %s" % cat))


def file_rows(db, mats, back, show_place=True, show_cat=False):
    """The files themselves: tick any, tick all, delete the ticked in one go;
    each row says what the file is and where it is filed."""
    if not mats:
        return ('<div class="empty-state">' + look_icon("folder", "empty-ico")
                + '<p><strong>Nothing here yet.</strong><br>Add a file with the button at the top.</p></div>')
    rows = ""
    for m in mats:
        label, icon, tone = file_kind(m["original_name"] or m["filename"])
        place = [m["category"]] if show_cat and m["category"] else []
        if show_place:
            place.append(core.level_name(db, m["level_id"]) or "All levels")
        if m["unit"]:
            place.append("%s %d" % (core.unit_word(m["collection"]), m["unit"]))
        if m["book"]:
            place.append(core.book_label(m["book"]))
        if m["group_id"]:
            place.append("only " + group_name(db, m["group_id"]))
        place.append(m["original_name"] or "")
        note = f'<span class="f-note">{E(m["note"])}</span>' if m["note"] else ""
        rows += (f'<li class="frow"><label class="pick"><input type="checkbox" name="id" value="{m["id"]}"'
                 f' data-size="{m["size"] or 0}" aria-label="Tick {E(m["title"])}"></label>'
                 f'<span class="f-ico t-{tone}" title="{label}"><svg viewBox="0 0 24 24" aria-hidden="true">'
                 f'{LOOK_ICONS[icon]}</svg></span>'
                 f'<span class="f-main"><a class="f-name" href="/materials/{m["id"]}/file">{E(m["title"])}</a>'
                 f'<span class="f-meta"><span class="f-msize">{E(core.human_size(m["size"]))} · </span>'
                 f'{E(" · ".join(p for p in place if p))}</span>{note}</span>'
                 f'<span class="f-size">{E(core.human_size(m["size"]))}</span><span class="f-acts">'
                 + (f'<button type="button" class="f-play" data-play aria-label="Play {E(m["title"])}">'
                    f'<svg viewBox="0 0 24 24" aria-hidden="true"><path class="pl" d="M8 5.5v13l10.5-6.5z"/>'
                    f'<path class="pa" d="M8 5.5v13M16 5.5v13"/></svg></button>'
                    f'<audio class="f-audio" preload="none" src="/materials/{m["id"]}/file"></audio>'
                    if label == "Audio" else "")
                 + f'<button class="f-del" name="one" value="{m["id"]}" title="Delete {E(m["title"])}"'
                 f' aria-label="Delete {E(m["title"])}" data-arm="Delete?">'
                 f'<svg viewBox="0 0 24 24" aria-hidden="true">{LOOK_ICONS["trash"]}</svg></button></span></li>')
    n = len(mats)
    return (f'<form class="files" method="post" action="/materials/delete" data-files>'
            f'<input type="hidden" name="back" value="{E(back)}">'
            f'<div class="files-head"><label class="pick all"><input type="checkbox" data-all>'
            f'<span>Select all</span></label>'
            f'<span class="files-count" data-count data-total="{E(files_meta(mats))}">{E(files_meta(mats))}</span>'
            f'<button class="danger-btn" name="what" value="picked" data-picked disabled'
            f' data-arm="Delete the ticked files for good? Tap again">'
            f'{look_icon("trash", "btn-ico")}<span data-label>Delete selected</span></button></div>'
            f'<ul class="filelist">{rows}</ul></form>')


def test_files(db, level_id, coll, unit, base):
    """One test: the paper, its audio and its answers, labelled and together."""
    rows = core.files_in_test(db, level_id, coll, unit)
    order = {name: i for i, name in enumerate(core.sections(coll))}
    rows = sorted(rows, key=lambda m: (order.get(m["category"], 99), m["title"]))
    back = f"{base}c={coll}&u={unit}"
    own = core.materials_scope(db, level_id, coll, None, unit)
    return (crumbs(db, level_id, coll, None, unit, base) + file_rows(db, rows, back, show_place=False, show_cat=True)
            + wipe_form(back, own, {"level": level_id, "c": coll, "u": unit}, "Everything for Test %d" % unit))


def material_hits(db, q, level_id, back):
    """Type a track number and get the file - faster than walking the tree."""
    like = "%" + q.replace("%", "") + "%"
    sql = ("SELECT * FROM materials WHERE active=1 AND (title LIKE ? OR original_name LIKE ?)")
    args = [like, like]
    if level_id:
        sql += " AND (level_id IS NULL OR level_id IS ?)"
        args.append(level_id)
    mats = db.execute(sql + " ORDER BY title LIMIT 500", args).fetchall()
    head = (f'<p class="shelf-sum">{look_icon("search", "sum-ico")}<span><strong>{len(mats)}'
            f' match{"" if len(mats) == 1 else "es"}</strong> for “{E(q)}”'
            + (" (the first 500)" if len(mats) == 500 else "") + "</span></p>")
    return head + file_rows(db, mats, back, show_cat=True)


def material_table(db, mats, head, back):
    return head + file_rows(db, mats, back, show_place=False)


def view_materials(req, db):
    groups = db.execute("SELECT * FROM groups WHERE archived=0 ORDER BY name").fetchall()
    levels = db.execute("SELECT * FROM levels ORDER BY sort").fetchall()
    only = req["query"].get("level", [None])[0]
    only = int(only) if only and only.isdigit() else None

    def tab(href, label, on):
        return f'<a class="tab{" on" if on else ""}" href="{href}">{E(label)}</a>'
    tabs = ('<div class="tabs levels">' + tab("/materials", "All levels", only is None)
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

    # this very view, so that a delete brings you back to it, not to the top
    here = "/materials?" + urllib.parse.urlencode(
        [(k, v) for k, v in (("level", only), ("q", q), ("c", coll), ("s", cat), ("u", unit)) if v not in (None, "")])
    search = f'''<form method="get" action="/materials" class="shelf-search" role="search">
  {f'<input type="hidden" name="level" value="{only}">' if only else ""}
  {look_icon("search", "search-ico")}
  <input name="q" value="{E(q)}" placeholder="Search by name or file, e.g. 8.03 or transcripts" aria-label="Search the shelves">
  {f'<a class="search-clear" href="{base[:-1]}">Clear</a>' if q else ""}
</form>'''

    if q:
        blocks = material_hits(db, q, only, here)
    elif not only:
        blocks = level_tiles(db, levels)
    elif not coll or coll not in core.COLLECTIONS:
        blocks = shelf_tiles(db, only, base)
    elif core.is_test_shelf(coll):
        blocks = (test_tiles(db, only, coll, base) if unit is None
                  else test_files(db, only, coll, unit, base))
    elif not cat:
        blocks = section_tiles(db, only, coll, base)
    elif unit is None and core.units_in(db, only, coll, cat):
        blocks = unit_tiles(db, only, coll, cat, base)
    else:
        rows = unit_files(db, only, coll, cat, unit)
        own = core.materials_scope(db, only, coll, cat, unit)
        what = "Everything in %s" % (cat if unit is None else "%s, %s" % (
            cat, "no unit" if unit == -1 else "Welcome" if unit == 0 else "Unit %d" % unit))
        blocks = (material_table(db, rows, crumbs(db, only, coll, cat, unit, base), here)
                  + wipe_form(here, own, {"level": only, "c": coll, "s": cat, "u": unit}, what))
    gone = (req["query"].get("gone", [""])[0] or "").strip()
    freed = (req["query"].get("freed", [""])[0] or "").strip()
    flash = (f'<div class="flash ok shelf-flash">Deleted {int(gone)} file{"" if gone == "1" else "s"}'
             f' · {E(core.human_size(int(freed)))} freed</div>'
             if gone.isdigit() and freed.isdigit() else "")
    blocks = flash + search + blocks

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
    body = f"""<div class="pagehead"><div><h1>Materials</h1>
<p class="sub">Filed by level, then collection, then section — the same tree students
walk through in the bot.</p></div>
<div class="actions"><a class="btn" href="#addfile" data-open="addfile">{look_icon("upload", "btn-ico")}Add a file</a></div></div>
{tabs}
{blocks}
<details class="adder" id="addfile"><summary>Add a file</summary>
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
<input name="note" placeholder="Read before Monday" class="wide"></label>
<label class="dropzone">
  <input type="file" name="file" required
         onchange="this.closest('.dropzone').classList.add('has');
                   this.nextElementSibling.textContent = this.files[0].name;">
  <span class="dz-label">Choose a file</span>
  <span class="dz-hint">PDF, Word, PowerPoint, images, audio or video. Up to 45 MB —
  Telegram's limit for what a bot can send.</span>
</label>
<div class="gap-3"><button>Upload</button></div></form></div>
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
    """The old one-file button (kept for any page still carrying it): it now
    comes back to where it was pressed."""
    back = (req["form"].get("back", ["/materials"])[0] or "/materials")
    gone, freed = core.delete_materials(db, [mid])
    return redirect(_after_delete(back, gone, freed))


def _after_delete(back, gone, freed):
    back = back if back.startswith("/materials") else "/materials"
    back = re.sub(r"[?&](gone|freed)=\d+", "", back)
    return back + ("&" if "?" in back else "?") + "gone=%d&freed=%d" % (gone, freed)


def act_delete_materials(req, db):
    """Delete several files at once: the ticked ones, one row's own button, or
    everything at the place the page shows (this level's own files only).
    The page's button asks twice; without the page's script the question comes
    as a page of its own, so nothing is ever deleted by one stray click."""
    f = req["form"]
    back = (f.get("back", ["/materials"])[0] or "/materials")
    if not back.startswith("/materials"):
        back = "/materials"
    what = (f.get("what", [""])[0] or "")
    one = (f.get("one", [""])[0] or "")
    if one.isdigit():
        ids = [int(one)]
    elif what == "picked":
        ids = [int(x) for x in f.get("id", []) if x.isdigit()]
    elif what == "scope":
        def num(k):
            v = (f.get(k, [""])[0] or "").strip()
            return int(v) if v.lstrip("-").isdigit() else None
        level = num("level")
        if level is None:
            return redirect(back)                 # never "every level at once"
        coll = (f.get("c", [""])[0] or "") or None
        cat = (f.get("s", [""])[0] or "") or None
        ids = [r["id"] for r in core.materials_scope(db, level, coll, cat, num("u"))]
    else:
        ids = []
    rows = [r for r in (db.execute("SELECT * FROM materials WHERE id=?", (i,)).fetchone() for i in ids) if r]
    if not rows:
        return redirect(back)
    if (f.get("confirm", [""])[0] or "") != "yes":
        keep = "".join(f'<input type="hidden" name="{E(k)}" value="{E(v)}">'
                       for k, vals in f.items() if k != "confirm" for v in vals)
        names = "".join(f"<li>{E(r['title'])} <span class='sub'>{E(r['original_name'] or '')}</span></li>"
                        for r in rows[:12])
        more = f"<li class='sub'>and {len(rows) - 12} more</li>" if len(rows) > 12 else ""
        body = (f'<div class="confirm-card">{look_icon("trash", "confirm-ico")}'
                f'<h1>Delete {len(rows)} file{"" if len(rows) == 1 else "s"}?</h1>'
                f'<p class="sub">{E(files_meta(rows))}. They come off the shelves and out of the bot for good;'
                f' your own copies on the computer are not touched.</p><ul class="confirm-list">{names}{more}</ul>'
                f'<form method="post" action="/materials/delete" class="inline">{keep}'
                f'<input type="hidden" name="confirm" value="yes">'
                f'<button class="danger-btn">{look_icon("trash", "btn-ico")}Yes, delete them</button>'
                f'<a class="btn ghost" href="{E(back)}">Keep them</a></form></div>')
        return html_response(page("Delete files", body, "Materials"))
    gone, freed = core.delete_materials(db, [r["id"] for r in rows])
    return redirect(_after_delete(back, gone, freed))


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


def view_prompts(req, db):
    """The bank of writing questions, and somewhere to add your own."""
    core.seed_prompts(db)
    level = (req["query"].get("level", [""])[0] or "").strip() or None
    kind = (req["query"].get("kind", [""])[0] or "").strip() or None
    rows = core.prompts_for(db, level, kind)
    labels = dict((k, lab) for k, lab, _w, _m in core.prompt_kinds())

    def tab(href, text, on):
        return f'<a class="tab{" on" if on else ""}" href="{href}">{E(text)}</a>'
    lv = ('<div class="tabs">' + tab("/prompts", "Every level", not level)
          + "".join(tab(f"/prompts?level={urllib.parse.quote(l)}", l, level == l)
                    for l in core.LEVELS) + "</div>")

    body_rows = ""
    ask = ' onsubmit="return confirm(&#39;Remove this question?&#39;)"'
    for r in rows:
        mine_tag = '<span class="pill mute">yours</span>' if r["mine"] else ""
        body_rows += (
            f'<tr><td class="sub">{E(r["level"])}</td>'
            f'<td class="sub">{E(labels.get(r["kind"], r["kind"]))}</td>'
            f'<td>{E(r["text"])}</td>'
            f'<td class="sub">{r["min_words"] or "&mdash;"} w</td>'
            f'<td class="sub">{r["used"]}&times;</td>'
            f'<td>{mine_tag}</td>'
            f'<td class="rowacts"><form method="post" action="/prompts/delete"'
            f'{ask}>'
            f'<input type="hidden" name="id" value="{r["id"]}">'
            f'<button class="linky danger">remove</button></form></td></tr>')

    lopts = "".join(f'<option value="{E(l)}">{E(l)}</option>' for l in core.LEVELS)
    kopts = "".join(f'<option value="{k}">{E(lab)}</option>'
                    for k, lab, _w, _m in core.prompt_kinds())
    body = f"""<h1>Writing questions</h1>
<p class="sub">What the site offers when you press <span class="kbd">Suggest a question</span>
on a writing task. It picks the least-used one for that level and kind, so the same
question does not come round every week. Add your own and they go into the same pot.</p>
{lv}
<div class="tablewrap"><table><tr><th>Level</th><th>Kind</th><th>Question</th>
<th>Words</th><th>Used</th><th></th><th></th></tr>
{body_rows or '<tr><td colspan=7 class="sub">Nothing here yet.</td></tr>'}</table></div>
<h2 class="gap-5">Add your own</h2>
<div class="card"><form method="post" action="/prompts/new">
<div class="inline gap-0">
<label class="f">Level<select name="level">{lopts}</select></label>
<label class="f">Kind<select name="kind">{kopts}</select></label>
<label class="f">At least<input type="number" name="min_words" min="0" max="1000"
  style="width:90px"> words</label>
<label class="f">Time<input type="number" name="minutes" min="0" max="240"
  style="width:90px"> minutes</label>
</div>
<label class="f">The question<textarea name="text" rows="3" class="wide" required
  placeholder="Some people think that…"></textarea></label>
<div class="gap-3"><button>Add it</button></div>
</form></div>"""
    return html_response(page("Writing questions", body, "Questions"))


def act_new_prompt(req, db):
    f = req["form"]
    def whole(key):
        v = (f.get(key, [""])[0] or "").strip()
        return int(v) if v.isdigit() and int(v) > 0 else None
    core.add_prompt(db, f.get("level", [""])[0], f.get("kind", [""])[0],
                    f.get("text", [""])[0], whole("min_words"), whole("minutes"))
    return redirect("/prompts")


def act_delete_prompt(req, db):
    pid = (req["form"].get("id", [""])[0] or "").strip()
    if pid.isdigit():
        core.delete_prompt(db, int(pid))
    return redirect("/prompts")


def units_json(req, db):
    """Which units of a level have a writing lesson, and what it is about."""
    level = (req["query"].get("level", [""])[0] or "").strip()
    core.seed_coursebook(db)
    rows = core.units_with_writing(db, level)
    return json_response({"units": [
        {"unit": r["unit"], "topic": r["topic"], "lesson": r["lesson"]} for r in rows]})


def suggest_json(req, db):
    """One question for a level and kind, for the button on the assignment form."""
    level = (req["query"].get("level", [""])[0] or "").strip()
    kind = (req["query"].get("kind", [""])[0] or "").strip()
    unit = (req["query"].get("unit", [""])[0] or "").strip()
    core.seed_prompts(db)
    core.seed_coursebook(db)
    row = core.suggest_prompt(db, level, kind, int(unit) if unit.isdigit() else None)
    if not row:
        return json_response({"ok": False,
                              "why": "nothing written for %s yet" % (level or "that level")})
    where = ""
    if row["unit"]:
        where = "Unit %d%s" % (row["unit"], " — " + row["topic"] if row["topic"] else "")
    return json_response({"ok": True, "text": row["text"], "where": where,
                          "min_words": row["min_words"], "minutes": row["minutes"]})


def view_tests(req, db):
    """Digital tests: made from the book, marked by the machine."""
    rows = core.digital_tests(db)
    body_rows = ""
    for t in rows:
        ready = t["n"] and t["n"] == t["keyed"]
        state = ('<span class="hb-chip open">published</span>' if t["published"]
                 else '<span class="hb-chip">draft</span>')
        key = ('<span class="hb-chip set">key complete</span>' if ready
               else f'<span class="hb-chip risk">{t["keyed"]} of {t["n"]} answers</span>')
        sat = db.execute("SELECT COUNT(*) c FROM dattempts WHERE test_id=?"
                         " AND finished_at IS NOT NULL", (t["id"],)).fetchone()["c"]
        body_rows += (f'<li class="hb-row"><span class="hb-badge ico">'
                      f'<svg viewBox="0 0 24 24" aria-hidden="true">{LOOK_ICONS["clipboard"]}</svg></span>'
                      f'<span class="hb-main"><a class="hb-title" href="/tests/{t["id"]}">{E(t["title"])}</a>'
                      f'<span class="hb-meta">{E(t["level"] or "any level")} · {t["n"]} questions · {sat} sat'
                      f' {key} {state}</span></span>'
                      f'<span class="hb-acts"><a class="btn ghost small" href="/tests/{t["id"]}">Open</a></span></li>')

    body = f"""{handouts_list(db)}<h1 class="h1-next">Digital tests</h1>
<p class="sub">A test taken on the phone and marked the moment it is handed in. The
questions come out of the practice book; the answer key does not, so a test cannot be
published until every answer has been set.</p>
{f'<ul class="hb-list boxed">{body_rows}</ul>' if body_rows else '<p class="hb-none">None yet.</p>'}
<h2>Load a test</h2>
<div class="card"><form method="post" action="/tests/new" enctype="multipart/form-data"
 class="inline">
<label class="f">File<input type="file" name="file" accept=".json,application/json" required></label>
<label class="f pushed">&nbsp;<button>Load it</button></label>
</form>
<p class="sub gap-3">A test file is prepared from the practice book on the computer
that runs the site. Load the file it produces here; the answer key is set on the
test's own page.</p></div>"""
    return html_response(page("Digital tests", body, "Tests"))


def audio_shelf(t, level):
    """Where a handout's recordings are: the class tracks of its level, or -
    for a workbook unit - the workbook's own, numbered the same way."""
    series = t["series"] if "series" in t.keys() else None
    return (level + " Workbook") if (series == "workbook" and level) else level


def handouts_list(db):
    """Every digital handout, so one can be found: another book's units
    (Destination) first, then the course's booklets by level - each with
    the classes it is set to and a way to look through it."""
    rows = db.execute(
        "SELECT t.*, l.name level, l.sort lsort FROM dtests t LEFT JOIN levels l ON l.id=t.level_id"
        " WHERE t.kind='handout'").fetchall()
    newest = {}
    for t in rows:                       # a rebuilt one replaces the one before it
        if t["title"] not in newest or t["published"] >= newest[t["title"]]["published"]:
            newest[t["title"]] = t
    rows = sorted(newest.values(), key=lambda t: (t["series"] is None, t["lsort"] or 0,
                                                  core.lesson_order(t)))

    def row(t):
        sets = [r["name"] for r in db.execute(
            "SELECT DISTINCT g.name FROM assignments a JOIN groups g ON g.id=a.group_id"
            " WHERE a.test_id=? AND a.published=1 ORDER BY g.name", (t["id"],))]
        parts = len(handout_parts(t["layout"] or "")[1])
        n = db.execute("SELECT COUNT(*) FROM dquestions WHERE test_id=?", (t["id"],)).fetchone()[0]
        if sets:
            chip = '<span class="hb-chip set">set to %s</span>' % E(", ".join(sets))
        elif t["published"]:
            chip = '<span class="hb-chip open">open to the level as practice</span>'
        else:
            chip = '<span class="hb-chip">not set yet</span>'
        badge = str(t["number"]) if t["number"] else "·"
        return (f'<li class="hb-row"><span class="hb-badge">{E(badge)}</span>'
                f'<span class="hb-main"><strong class="hb-title">{E(t["title"])}</strong>'
                f'<span class="hb-meta">{parts} parts · {n} boxes {chip}</span></span>'
                f'<span class="hb-acts"><a class="btn ghost small" href="/tests/{t["id"]}/look">Look through</a>'
                f'<a class="btn ghost small" href="/tests/{t["id"]}">Key</a></span></li>')

    def group(items, boxed=" boxed"):
        return (f'<ul class="hb-list{boxed}">{"".join(row(t) for t in items)}</ul>' if items
                else '<p class="hb-none">None on the site yet.</p>')

    levels = []
    for t in rows:
        if t["series"]:
            continue
        if not levels or levels[-1][0] != t["level"]:
            levels.append((t["level"], []))
        levels[-1][1].append(t)
    course = ""
    for k, (level, items) in enumerate(levels):
        set_n = sum(1 for t in items if db.execute(
            "SELECT 1 FROM assignments WHERE test_id=? AND published=1 LIMIT 1", (t["id"],)).fetchone())
        tone = LEVEL_TONES[k % len(LEVEL_TONES)]
        initials = "".join(w[0] for w in re.findall(r"[A-Za-z]+", level or "Any"))[:2].upper()
        course += (f'<details class="hb-level t-{tone}"><summary><span class="lvl-badge">{E(initials)}</span>'
                   f'<span class="shelf-text"><span class="shelf-name">{E(level or "any level")}</span>'
                   f'<span class="shelf-meta">{len(items)} booklet{"" if len(items) == 1 else "s"}'
                   + (f' · {set_n} set as homework' if set_n else "") + '</span></span>'
                   f'<svg class="shelf-go" viewBox="0 0 24 24" aria-hidden="true">{LOOK_ICONS["chevron"]}</svg>'
                   f'</summary>{group(items, "")}</details>')
    how = ("To set a Destination unit, write it in the Destination box on "
           '<a class="linky" href="/assignments">Set homework</a> the way the book names it - '
           "<em>Destination B1, Unit 12</em>. It opens only for the classes it is set to.")
    total = sum(len(items) for _l, items in levels)
    return f"""<h1>Digital handouts</h1>
<p class="sub">The course's booklets, done on the phone one part at a time, by level. Open a level to see
where each booklet is set, look through it as a student does, or check its key.</p>
<h2>Destination</h2>
<p class="sub">{how}</p>
{group([t for t in rows if t["series"] == "destination"])}
<h2>Workbook</h2>
<p class="sub">A workbook unit on the site is linked from its homework line by itself - <em>Workbook
unit 1 A&amp;C</em> - for classes of its level. Students do it there, or send photos of the pages.</p>
{group([t for t in rows if t["series"] == "workbook"])}
<h2>The course booklets <span class="h2-count">{total}</span></h2>
<div class="hb-levels">{course or '<p class="hb-none">None on the site yet.</p>'}</div>"""


def view_handout_look(req, db, tid):
    """A handout as a student sees it, part by part, for the teacher to look
    through - nothing saved, nothing checked. With ?answers=1 the key's
    answers are in the boxes."""
    t = db.execute("SELECT * FROM dtests WHERE id=? AND kind='handout'", (tid,)).fetchone()
    if not t:
        return not_found()
    q = req["query"]
    _intro, parts = handout_parts(t["layout"] or "")
    n = (q.get("part", ["1"])[0] or "1")
    idx = max(0, min(len(parts) - 1, int(n) - 1 if n.isdigit() else 0))
    num, pname, what, markup = parts[idx]
    show = q.get("answers") == ["1"]
    qs = core.test_questions(db, tid)
    nums = set(part_keys(markup))
    pqs = [(qq, o) for qq, o in qs if qq["num"] in nums]
    given = marks = None
    if show:
        given = {qq["id"]: (qq["answer"] or "").split("/")[0] for qq, _o in pqs if qq["answer"]}
        marks = {qq["id"]: 1 for qq, _o in pqs if qq["answer"]}
    layout = '<div class="booklet">' + hx_dress(markup) + "</div>"
    layout, _secs, _ex = handout_controls(layout, pqs, given, marks)
    level = core.level_name(db, t["level_id"]) or ""
    sheet = fill_layout(layout, pqs, given, marks, level=audio_shelf(t, level), title=t["title"])
    here = f"/tests/{tid}/look?answers={'1' if show else '0'}"
    steps = "".join(
        f'<a class="tab{" on" if i == idx else ""}" href="{here}&amp;part={i + 1}">{i + 1} {E(p[1])}</a>'
        for i, p in enumerate(parts))
    flip = (f'<a class="btn ghost" href="/tests/{tid}/look?answers={"0" if show else "1"}&amp;part={idx + 1}">'
            f'{"Hide the answers" if show else "Show the answers"}</a>')
    body = f"""<div class="trybar" role="note">
  <div class="try-where"><strong>{E(t["title"])}</strong>
  <span class="sub">&mdash; as a student sees it; nothing here is saved</span></div>
  <div class="try-do">{flip}<a class="btn ghost" href="/tests">Back to the list</a></div>
  <div class="tabs stretch psub">{steps}</div>
</div>
<div class="hx-parthead"><p class="hx-partno">Part {idx + 1} of {len(parts)}</p>
<h2>{E(pname)}</h2>{f"<p>{E(what)}</p>" if what else ""}</div>
<div class="booksheet handout hx-sheet">{sheet}</div>"""
    return html_response(student_page(t["title"], body, music=False))


def view_test(req, db, tid):
    t = db.execute("SELECT * FROM dtests WHERE id=?", (tid,)).fetchone()
    if not t:
        return not_found()
    qs = core.test_questions(db, tid)
    ready = core.test_ready(db, tid)

    # a booklet's boxes come exercise by exercise: "1.3  2 According to..." -
    # the instruction is said once at the head of its exercise, not on every box
    groups = []
    for q, opts in qs:
        m = re.match(r"(\d+\.\d+)\s{2,}(.*)", q["prompt"] or "", re.S)
        label, text = (m.group(1), m.group(2)) if m else ("", q["prompt"] or "")
        if not groups or groups[-1][0] != label:
            groups.append((label, []))
        groups[-1][1].append((q, opts, text))
    rows, unset = "", 0
    for label, items in groups:
        head = next((t for _q, _o, t in items if label and t.startswith(label)), "")
        inner = ""
        for k, (q, opts, text) in enumerate(items, 1):
            open_box = q["kind"] == "open"
            if q["kind"] == "typed" or not opts:
                picks = (f'<input class="typedin" name="q{q["id"]}" value="{E(q["answer"] or "")}"'
                         f' placeholder="{"marked by you - leave empty" if open_box else "the answer, or several separated by /"}">')
            else:
                picks = '<div class="kq-picks">' + "".join(
                    f'<label class="keypick"><input type="radio" name="q{q["id"]}"'
                    f' value="{E(o["letter"])}"{" checked" if q["answer"] == o["letter"] else ""}>'
                    f'<span><b>{E(o["letter"])}</b> {E(o["text"][:90])}</span></label>'
                    for o in opts) + '</div>'
            if open_box and not q["answer"]:
                flag = '<span class="hb-chip">you mark it</span>'
            elif not q["answer"]:
                flag = '<span class="hb-chip risk">no answer</span>'
                unset += 1
            else:
                flag = ""
            ways = len((q["answer"] or "").split("/")) if q["kind"] == "typed" and q["answer"] else 0
            if ways > 1:
                flag += f'<span class="hb-chip set">{ways} ways right</span>'
            said = "" if (label and text.startswith(label)) or not text else text
            if label and not said:
                said = f"Box {k}"
            pic = (f'<img class="passageimg" src="/testimg/{E(q["image"])}" alt="">' if q["image"] else "")
            inner += (f'{pic}<div class="kq{" unset" if not q["answer"] and not open_box else ""}'
                      f'{" bare" if said == f"Box {k}" else ""}">'
                      f'<span class="kq-n">{q["num"]}</span>'
                      f'<span class="kq-q">{E(said)}{(" " + flag) if flag else ""}</span>'
                      f'<span class="kq-a">{picks}</span></div>')
        if label:
            rows += (f'<section class="kx"><header class="kx-head"><span class="kx-label">{E(label)}</span>'
                     f'<span class="kx-text">{E(head[len(label):].strip() if head else "")}</span>'
                     f'<span class="kx-n">{len(items)} box{"" if len(items) == 1 else "es"}</span></header>'
                     f'{inner}</section>')
        else:
            rows += f'<section class="kx plain">{inner}</section>'

    passage = (f'<div class="card"><div class="sub">The text students read</div>'
               f'<div class="passage">{E(t["passage"])}</div></div>'
               if t["passage"] else "")

    sat = core.attempts_for_test(db, tid)
    results = ""
    if sat:
        results = f"<h2>Who has sat it <span class='h2-count'>{len(sat)}</span></h2><ul class='rs-list'>"
        for a in sat:
            pct = round(100 * (a["score"] or 0) / a["total"]) if a["total"] else 0
            results += (
                f'<li class="rs-row with-act"><span class="rs-score">{pct}%</span>'
                f'<span class="rs-name">{E(a["name"])}</span>'
                f'<span class="rs-meta"><strong>{a["score"]}</strong> of {a["total"]} · '
                f'{E((a["finished_at"] or "")[:16].replace("T", " "))}</span>'
                f'<form class="rs-act" method="post" action="/tests/{tid}/attempt/{a["id"]}/delete" '
                f'onsubmit="return confirm(\'Remove this sitting? '
                f'It is the one the league counts.\')">'
                f'<button class="ghost small">Remove</button></form></li>')
        results += "</ul>"
        written = sum(1 for p in core.written_answers(db, tid)
                      for a in p["answers"] if a["text"])
        if written:
            results += (f'<p class="gap-3"><a class="tab" '
                        f'href="/tests/{tid}/writing">Read the writing '
                        f'({written})</a></p>')

    mins = t["minutes"] if "minutes" in t.keys() else None
    strict = bool(t["strict"]) if "strict" in t.keys() else False
    once = bool(t["once"]) if "once" in t.keys() else False
    sitting = db.execute(
        "SELECT COUNT(*) c FROM dattempts WHERE test_id=? AND finished_at IS NULL",
        (tid,)).fetchone()["c"]
    busy = (f'<p class="sub gap-3" style="margin-bottom:0">'
            f'{sitting} student(s) have this open right now. Changing the time '
            f'changes their clock too, from when each of them started.</p>'
            if sitting else "")
    timing = f"""<h2>Exam conditions</h2>
<div class="card"><form method="post" action="/tests/{tid}/timing" class="inline">
<label class="f">Time<input type="number" name="minutes" min="0" max="240"
 value="{mins or ''}" placeholder="none" style="width:90px"> minutes</label>
<label class="f">Leaving the page
<select name="strict">
<option value="0"{"" if strict else " selected"}>does nothing</option>
<option value="1"{" selected" if strict else ""}>hands the paper in</option>
</select></label>
<label class="f">Sittings
<select name="once">
<option value="0"{"" if once else " selected"}>as many as they like</option>
<option value="1"{" selected" if once else ""}>one only</option>
</select></label>
<label class="f pushed">&nbsp;<button>Save</button></label>
</form>
<p class="sub gap-3"><strong>One only</strong> is what makes it an exam: once
a student has handed the paper in they see their result and their marked
paper, and there is no way back into it. Leave it on <strong>as many as they
like</strong> for a booklet worth redoing until it is right &mdash; the
league counts the first sitting either way.</p>
<p class="sub gap-3">Leave the time empty for no limit, and the booklet
behaves as it always has: no clock, and they can stop and come back. With a
time set, a bar counts down on screen and the paper hands itself in when it
reaches nought &mdash; with whatever they had written, which is saved as they
type, never a blank page.</p>{busy}</div>"""

    if ready:
        # only homework and the lesson count in the league: a test sat for
        # practice earns nothing, and one set as homework counts as homework
        note = ('Published, it is practice: students can sit it as often as they like and it '
                'earns no league points. Set it as homework, with a deadline, and it counts like '
                'any homework &mdash; the first sitting before the deadline, out of ten.')
        pub = (f'<form method="post" action="/tests/{tid}/publish">'
               f'<button{" class=ghost" if t["published"] else ""}>'
               f'{"Unpublish" if t["published"] else "Publish to students"}</button></form>')
    else:
        note = "Set every answer before publishing."
        pub = ""
    kind = "booklet" if (t["kind"] if "kind" in t.keys() else None) == "handout" else "test"
    look = (f'<a class="btn ghost" href="/tests/{tid}/look">Look through</a>' if kind == "booklet" else "")

    body = f"""<div class="pagehead"><div><p class="eyebrow">{"Digital handout" if kind == "booklet" else "Digital test"}</p>
<h1>{E(t["title"])}</h1>
<p class="key-chips"><span class="hb-chip">{len(qs)} questions</span>
<span class="hb-chip {"set" if ready else "risk"}">{"every answer set" if ready else "answer key incomplete"}</span>
<span class="hb-chip {"open" if t["published"] else ""}">{"published" if t["published"] else "not published"}</span></p></div>
<div class="actions">{look}{pub}</div></div>
<p class="sub key-note">{note}</p>
{passage}
<form method="post" action="/tests/{tid}/key" class="keyform">
<p class="key-how">Several answers that are all right go in one box, separated by <b>/</b>
&mdash; <em>doesn't/does not</em>. Capitals and a full stop at the end never count.</p>
{rows}
<div class="key-save"><span class="key-left">{f"{unset} box{'' if unset == 1 else 'es'} without an answer" if unset
 else "Every box has its answer"}</span><button>Save the answer key</button></div>
</form>
{carry_card(db, t, req)}
{timing}
{results}
<form method="post" action="/tests/{tid}/delete" class="key-delete"
 onsubmit="return confirm('Delete this {kind} and everything students scored on it?')">
<span>Deleting it takes every student's answers and marks on it with it.</span>
<button class="ghost danger">Delete this {kind}</button></form>"""
    return html_response(page(t["title"], body, "Tests"))


def carry_card(db, t, req):
    """On a rebuilt handout: bring the students' answers over from the old
    one, so nobody who had started it finds an empty page."""
    if (t["kind"] if "kind" in t.keys() else None) != "handout":
        return ""
    olds = db.execute("SELECT id, title, published FROM dtests WHERE kind='handout'"
                      " AND id<>? AND IFNULL(level_id,0)=IFNULL(?,0) ORDER BY id DESC",
                      (t["id"], t["level_id"])).fetchall()
    if not olds:
        return ""
    done = req["query"].get("carried", [""])[0]
    said = ""
    if done:
        who = req["query"].get("students", ["0"])[0]
        parts = req["query"].get("parts", ["0"])[0]
        locked = (f' {E(parts)} part(s) they had already checked stay checked, marked by this '
                  f'version\'s key.' if parts not in ("", "0") else "")
        said = (f'<p class="sub gap-3"><strong>{E(done)} answers</strong> brought over '
                f'for {E(who)} student(s). Anything they had already typed here was left alone.{locked}</p>')
    opts = "".join(f'<option value="{o["id"]}">{E(o["title"])} '
                   f'({"published" if o["published"] else "hidden"}, #{o["id"]})</option>'
                   for o in olds)
    return f"""<h2>Answers from an older version</h2>
<div class="card"><form method="post" action="/tests/{t["id"]}/carry" class="inline">
<label class="f">Copy what students typed in<select name="from">{opts}</select></label>
<label class="f pushed">&nbsp;<button>Bring their answers over</button></label>
</form>
<p class="sub gap-3">For a handout that was rebuilt: every box is matched by its
exercise and item, and each student finds their answers waiting here. The old
version keeps its copy.</p>{said}</div>"""


def act_test_carry(req, db, tid):
    new = db.execute("SELECT * FROM dtests WHERE id=? AND kind='handout'", (tid,)).fetchone()
    old = (req["form"].get("from", [""])[0] or "").strip()
    if not new or not old.isdigit() or int(old) == tid or not db.execute(
            "SELECT 1 FROM dtests WHERE id=? AND kind='handout'", (int(old),)).fetchone():
        return redirect(f"/tests/{tid}")
    done = core.carry_answers(db, int(old), tid)
    copied = sum(n for n, _left in done.values())
    parts = carry_checked_parts(db, int(old), tid)
    return redirect(f"/tests/{tid}?carried={copied}&students={len(done)}&parts={parts}")


def view_speaking(req, db):
    """Every recording the students made in their handouts, newest first:
    listen, then answer with a line of writing, a recording of your own, or
    both. The ones still waiting for an answer come first; a student who said
    they cannot record is listed too, so nobody skips it unnoticed."""
    show = (req["query"].get("show", ["waiting"])[0] or "waiting")
    rows = core.recordings(db, waiting=False)
    waiting = [r for r in rows if not r["cant"] and not (r["note"] or r["fb_voice"])]
    cant = [r for r in rows if r["cant"]]
    shown = waiting if show == "waiting" else cant if show == "cant" else rows

    def tab(key, label, n):
        on = " on" if show == key else ""
        return f'<a class="tab{on}" href="/speaking?show={key}">{E(label)} <span class="tab-n">{n}</span></a>'
    tabs = (f'<div class="tabs">{tab("waiting", "Waiting for you", len(waiting))}'
            f'{tab("all", "All recordings", len(rows))}{tab("cant", "Could not record", len(cant))}</div>')
    cards = ""
    for r in shown:
        label = (r["prompt"] or "").split("  ")[0]
        when = ""
        if r["stamp"]:
            # the file is named in UTC; he reads Tashkent time
            at = (datetime.strptime(r["stamp"], "%Y%m%d%H%M%S")
                  + timedelta(hours=core.load_config()["timezone_offset_hours"]))
            when = at.strftime("%-d %b, %H:%M")
        who = (f'<div class="sp-who"><span class="lg-ava">{E((first_name(r["name"]) or "?")[:1].upper())}</span>'
               f'<span><a href="/students/{r["student_id"]}"><b>{E(r["name"])}</b></a>'
               f'<small>{E(group_name(db, r["group_id"]))} · {E(r["title"])} · {E(label)}'
               f'{(" · " + when) if when else ""}</small></span></div>')
        if r["cant"]:
            cards += (f'<div class="card sp-card cant">{who}<p class="sp-cant">Pressed <b>I can&rsquo;t record</b>. '
                      f'Ask for a Telegram voice message, or help them with the microphone in class.</p></div>')
            continue
        key = f'{r["attempt_id"]}-{r["question_id"]}'
        fbv = (f'<div class="sp-fbv"><audio controls preload="none" src="/media/{E(r["fb_voice"])}"></audio>'
               f'<form method="post" action="/speaking/voice/delete" class="inline">'
               f'<input type="hidden" name="attempt" value="{r["attempt_id"]}">'
               f'<input type="hidden" name="question" value="{r["question_id"]}">'
               f'<button class="linky danger">remove</button></form></div>' if r["fb_voice"] else "")
        cards += f"""<div class="card sp-card" id="sp-{key}">{who}
  <div class="sp-play"><audio controls preload="none" src="/media/{E(r["file"])}"></audio>
    <span class="sp-len">{r["seconds"] // 60}:{r["seconds"] % 60:02d}</span></div>
  <form method="post" action="/speaking/note" class="sp-form">
    <input type="hidden" name="attempt" value="{r["attempt_id"]}"><input type="hidden" name="question" value="{r["question_id"]}">
    <textarea name="note" rows="2" placeholder="A line for the student - what was good, one thing to work on">{E(r["note"] or "")}</textarea>
    <div class="sp-acts"><button>Save the note</button>
      <button type="button" class="ghost sp-rec" data-attempt="{r["attempt_id"]}" data-question="{r["question_id"]}"><i class="dot"></i><span>Record a reply</span></button>
      <span class="rec-vu" hidden><i></i></span><span class="rec-clock"></span>
      <select class="mic-pick" hidden aria-label="Which microphone"></select></div>
    <p class="rec-say" aria-live="polite"></p>
  </form>{fbv}
</div>"""
    if not shown:
        msg = {"waiting": "Nothing is waiting. When students record their answers in a handout, the recordings arrive here.",
               "cant": "Nobody has said they can&rsquo;t record.",
               "all": "No recordings yet. They arrive here as students record in their handouts."}[show if show in ("waiting", "cant") else "all"]
        cards = f'<div class="empty-state">{look_icon("message", "empty-ico")}<p>{msg}</p></div>'
    body = (f'<div class="pagehead"><div><h1>Speaking</h1><p class="sub">What students recorded in their handouts. '
            f'Listen, then answer with a note, a recording, or both &mdash; they see it on their Feedback tab and '
            f'next to their recording. A recording counts once it is at least {core.SPEAK_MIN_SECONDS} seconds.'
            f'</p></div></div>{tabs}<div class="sp-list">{cards}</div>')
    return html_response(page("Speaking", body, "Speaking"))


def _speak_target(db, form):
    att, qid = (form.get("attempt", [""])[0] or ""), (form.get("question", [""])[0] or "")
    if not (att.isdigit() and qid.isdigit()):
        return None
    ok = db.execute("SELECT 1 FROM dresponses r JOIN dquestions q ON q.id=r.question_id"
                    " WHERE r.attempt_id=? AND r.question_id=? AND q.control='record'", (int(att), int(qid))).fetchone()
    return (int(att), int(qid)) if ok else None


def act_speak_note(req, db):
    t = _speak_target(db, req["form"])
    if t:
        core.save_speak_feedback(db, t[0], t[1], note=(req["form"].get("note", [""])[0] or "").strip())
    return redirect("/speaking?show=" + ("all" if t else "waiting") + ("#sp-%d-%d" % t if t else ""))


def act_speak_voice(req, db):
    """The teacher's spoken answer to a recording, uploaded as soon as it stops."""
    fields, files = req["files"]
    t = _speak_target(db, fields)
    if not t or not files:
        return json_response({"ok": False})
    _name, data = files[0]
    if not data or len(data) < 1000:
        return json_response({"ok": False, "why": "empty"})
    if len(data) > 15 * 1024 * 1024:
        return json_response({"ok": False, "why": "too long"})
    kind = (fields.get("kind", [""])[0] or "").split(";")[0].strip().lower()
    ext = VOICE_EXT.get(kind, ".webm")
    name = "speakfb_%d_%d_%s%s" % (t[0], t[1], core.now().strftime("%Y%m%d%H%M%S"), ext)
    os.makedirs(core.UPLOAD_DIR, exist_ok=True)
    with open(os.path.join(core.UPLOAD_DIR, name), "wb") as fh:
        fh.write(data)
    core.save_speak_feedback(db, t[0], t[1], voice=name)
    return json_response({"ok": True, "url": "/media/" + name})


def act_speak_voice_delete(req, db):
    t = _speak_target(db, req["form"])
    if t:
        core.save_speak_feedback(db, t[0], t[1], clear_voice=True)
    return redirect("/speaking?show=all" + ("#sp-%d-%d" % t if t else ""))


def view_test_writing(req, db, tid):
    """Every student's writing on one paper, in one place, ready to read."""
    t = db.execute("SELECT * FROM dtests WHERE id=?", (tid,)).fetchone()
    if not t:
        return not_found()
    parts = core.written_answers(db, tid)
    if not parts:
        body = (f'<h1>Writing &mdash; {E(t["title"])}</h1>'
                f'<p class="sub">This paper has nothing to write on: every '
                f'question marks itself.</p>'
                f'<p class="gap-3"><a class="tab" href="/tests/{tid}">'
                f'Back to the test</a></p>')
        return html_response(page("Writing", body, "Tests"))

    blocks = ""
    for part in parts:
        q = part["question"]
        written = [a for a in part["answers"] if a["text"]]
        blank = [a for a in part["answers"] if not a["text"]]
        counts = sorted(a["words"] for a in written)
        middle = counts[len(counts) // 2] if counts else 0
        head = (f'<h2>{E(q["prompt"])}</h2>'
                f'<p class="sub">{len(written)} written &middot; '
                f'{len(blank)} left blank &middot; '
                f'{middle} words in the middle of the class</p>')
        rows = ""
        handout = (t["kind"] if "kind" in t.keys() else None) == "handout"
        for a in written:
            when = E((a["finished_at"] or "")[:16].replace("T", " "))
            void = ""
            if handout:
                void = (f'<form method="post" action="/tests/{tid}/void" class="inline">'
                        f'<input type="hidden" name="attempt" value="{a["attempt_id"]}">'
                        f'<input type="hidden" name="question" value="{q["id"]}">'
                        f'<input type="hidden" name="on" value="{0 if a["void"] else 1}">'
                        f'<button class="linky{"" if a["void"] else " danger"}">'
                        f'{"count it after all" if a["void"] else "does not count"}</button></form>')
            flag = ' <span class="pill risk">does not count</span>' if a.get("void") else ""
            rows += (f'<div class="card writ">'
                     f'<div class="rowline">'
                     f'<strong><a href="/students/{a["student_id"]}">'
                     f'{E(a["name"])}</a>{flag}</strong>'
                     f'<span class="sub">{a["words"]} words &middot; {when} {void}</span>'
                     f'</div>'
                     f'<div class="passage gap-2">{E(a["text"])}</div></div>')
        if blank:
            rows += (f'<p class="sub gap-3">Nothing written by: '
                     f'{E(", ".join(a["name"] for a in blank))}</p>')
        if not part["answers"]:
            rows = '<p class="sub">Nobody has sat this paper yet.</p>'
        blocks += head + rows

    body = (f'<h1>Writing &mdash; {E(t["title"])}</h1>'
            f'<p class="sub">What students wrote, in their own words. Nothing '
            f'here is marked by the system &mdash; the writing is yours to '
            f'read.{" An answer marked as not counting takes the part it is in out of the handout&rsquo;s mark." if (t["kind"] if "kind" in t.keys() else None) == "handout" else ""}</p>'
            f'{blocks}'
            f'<p class="gap-4"><a class="tab" href="/tests/{tid}">'
            f'Back to the test</a></p>')
    return html_response(page("Writing", body, "Tests"))


def act_test_void(req, db, tid):
    """A written answer in a handout does not count - or counts after all."""
    f = req["form"]
    att, qid = (f.get("attempt", [""])[0] or ""), (f.get("question", [""])[0] or "")
    if att.isdigit() and qid.isdigit() and db.execute(
            "SELECT 1 FROM dattempts WHERE id=? AND test_id=?", (int(att), tid)).fetchone():
        core.void_answer(db, int(att), int(qid), (f.get("on", ["1"])[0] or "1") == "1")
    return redirect(f"/tests/{tid}/writing")


def act_test_timing(req, db, tid):
    """The teacher sets the clock, not the file the test arrived in.

    A time limit is a decision about a particular morning - how long the
    lesson is, whether this is a mock under exam conditions or a booklet to
    finish at home - so it belongs on the page, next to Publish, rather than
    inside something only I can rebuild.
    """
    if not db.execute("SELECT id FROM dtests WHERE id=?", (tid,)).fetchone():
        return not_found()
    raw = (req["form"].get("minutes", [""])[0] or "").strip()
    minutes = int(raw) if raw.isdigit() and 0 < int(raw) <= 240 else None
    strict = 1 if req["form"].get("strict", ["0"])[0] == "1" else 0
    once = 1 if req["form"].get("once", ["0"])[0] == "1" else 0
    db.execute("UPDATE dtests SET minutes=?, strict=?, once=? WHERE id=?",
               (minutes, strict, once, tid))
    db.commit()
    return redirect(f"/tests/{tid}")


def serve_track(req, db, level, track):
    """One coursebook track, for the booklet that asked for it."""
    safe = re.fullmatch(r"\d{1,2}\.\d{2}", track)
    if not safe:
        return not_found()
    path = os.path.join(core.AUDIO_DIR, level, track + ".mp3")
    if not os.path.isfile(os.path.abspath(path)) or \
            not os.path.abspath(path).startswith(os.path.abspath(core.AUDIO_DIR)):
        return not_found()
    data = open(path, "rb").read()
    # The shelf is named .mp3, but the Mac cannot encode mp3 and the mock
    # recordings come out of `say` as AAC in an MP4 container. Say what the
    # bytes actually are, or the phone refuses to play them.
    kind = "audio/mp4" if data[4:8] == b"ftyp" else "audio/mpeg"
    return (200, [("Content-Type", kind),
                  ("Content-Length", str(len(data))),
                  ("Cache-Control", "public, max-age=86400")], data)


def view_settings(req, db):
    """One page for the whole site: what it keeps, and how it behaves."""
    cfg = core.load_config()
    store = core.storage_summary(db)
    saved = req["query"].get("saved", [""])[0] == "1"
    did = (req["query"].get("did", [""])[0] or "").strip()

    free, total = store["free"], store["total"]
    bar = ""
    if free and total:
        used = 100 - int(free * 100 / total)
        bar = (f'<div class="rowline"><strong>Disk</strong>'
               f'<span class="sub">{core.human_size(total - free)} of '
               f'{core.human_size(total)} used</span></div>'
               f'<div class="pbar"><i style="width:{used}%"></i></div>')

    rows = ""
    for r in store["rows"]:
        count = f'{r["count"]} item(s) &middot; ' if r["count"] is not None else ""
        control = ""
        if r["key"] == "photos":
            control = (
                '<form method="post" action="/settings/purge" class="inline"'
                ' onsubmit="return confirm(\'Let go of the full-size photos '
                'older than that? They come back from Telegram when opened.\')">'
                '<input type="hidden" name="what" value="photos">'
                '<label class="f">older than<span class="with-unit">'
                '<input type="number" name="days" value="30" min="1" max="3650">'
                ' days</span></label>'
                '<label class="f pushed">&nbsp;<button class="ghost">'
                'Let them go</button></label></form>')
        elif r["key"] != "materials":
            what = r["key"]
            control = (
                f'<form method="post" action="/settings/purge"'
                f' onsubmit="return confirm(\'Delete {E(r["title"]).lower()}?'
                f' This cannot be undone here.\')">'
                f'<input type="hidden" name="what" value="{what}">'
                f'<button class="ghost danger">Delete</button></form>')
        else:
            control = ('<p class="sub flush">Remove these from the '
                       '<a class="linky" href="/materials">Materials</a> page, '
                       'one shelf at a time.</p>')
        rows += (f'<div class="card"><div class="rowline">'
                 f'<strong>{E(r["title"])}</strong>'
                 f'<span class="pill{" risk" if r["danger"] else ""}">'
                 f'{core.human_size(r["bytes"])}</span></div>'
                 f'<p class="sub">{count}{E(r["note"])}</p>{control}</div>')

    fields = ""
    for key, label, unit, help_ in core.EDITABLE:
        fields += (f'<label class="f">{E(label)}'
                   f'<span class="with-unit"><input type="number" name="{key}"'
                   f' value="{E(str(cfg.get(key, "")))}"> {E(unit)}</span>'
                   f'<span class="sub">{E(help_)}</span></label>')
    boxes = ""
    for key, label, help_ in core.SWITCHES:
        on = " checked" if cfg.get(key) else ""
        boxes += (f'<label class="f"><span style="font-size:13px;color:var(--ink)">'
                  f'<input type="checkbox" name="{key}" value="1"{on}> {E(label)}'
                  f'</span><span class="sub">{E(help_)}</span></label>')

    worry = core.password_worry()
    body = f"""<h1>Settings</h1>
<p class="sub">Everything the site keeps, and how it behaves. The password and
the bot token are not here: those belong in the host's own settings, where
changing one needs no deploy.</p>
{f'<p class="flash">Saved.</p>' if saved else ''}
{f'<p class="flash">{E(did)}</p>' if did else ''}
{f'<p class="flash err">{E(worry)}</p>' if worry else ''}

<h2>What is stored</h2>
<div class="card">{bar}
<p class="sub gap-2">The database itself is {core.human_size(store["database"])}.
<a class="linky" href="/backup">Download a copy</a> and keep it somewhere that
is not this server.</p></div>
{rows}

<h2>How the site behaves</h2>
<div class="card"><form method="post" action="/settings">
<div class="inline">{fields}</div>
<div class="inline gap-3">{boxes}</div>
<div class="gap-3"><button>Save</button></div>
</form></div>"""
    return html_response(page("Settings", body, "Settings"))


def act_settings(req, db):
    f = req["form"]
    values = {k: f.get(k, [""])[0] for k, _l, _u, _h in core.EDITABLE}
    switches = {k: f.get(k, [""])[0] == "1" for k, _l, _h in core.SWITCHES}
    core.save_settings(values, switches)
    return redirect("/settings?saved=1")


def act_settings_purge(req, db):
    f = req["form"]
    what = (f.get("what", [""])[0] or "").strip()
    days = (f.get("days", [""])[0] or "").strip()
    said = core.purge(db, what, days or None)
    core.make_room()
    return redirect("/settings?did=" + urllib.parse.quote(said))


def act_free_space(req, db):
    """Run the photograph cleanup now, rather than waiting for tomorrow.

    The job is deduplicated to once a day, which is right when it is working
    and wrong the moment the setting changes: after lowering how long photos
    are kept, the site would sit full until the next morning.
    """
    import jobs
    cfg = core.load_config()
    before, _total = core.disk_room()
    freed = jobs.offload_old_photos(db, cfg)
    core.make_room()
    after, _t = core.disk_room()
    gained = (after or 0) - (before or 0)
    core.meta_set(db, "last_cleanup",
                  "%s - %s, %s freed" % (core.iso(core.now())[:16],
                                         freed or "nothing to let go",
                                         core.human_size(max(0, gained))))
    db.commit()
    return redirect("/")


def act_new_track(req, db):
    """Put a coursebook track on the shelf its level reads from."""
    fields, files = req["files"]
    # parse_multipart hands back a list per field, the way a query string does
    level = (fields.get("level", [""])[0] or "").strip()
    if not files or not level:
        return redirect("/tests")
    name, blob = files[0][0], files[0][1]
    track = os.path.splitext(os.path.basename(name))[0]
    if not re.fullmatch(r"\d{1,2}\.\d{2}", track):
        return redirect("/tests")
    folder = os.path.join(core.AUDIO_DIR, level)
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, track + ".mp3"), "wb") as fh:
        fh.write(blob)
    return redirect("/tests")


def view_backup(req, db):
    """Hand the newest backup to the teacher, so a copy can leave the server.

    The scheduler sends one to Telegram every day, but that needs the bot and
    a teacher registered with it. This is the path that always works: press
    it, and the file is on your own machine.
    """
    import jobs
    folder = os.path.join(core.DATA_DIR, "backups")
    files = sorted(f for f in os.listdir(folder)) if os.path.isdir(folder) else []
    if not files:
        jobs.backup()
        files = sorted(os.listdir(folder))
    newest = os.path.join(folder, files[-1])
    data = open(newest, "rb").read()
    return (200, [("Content-Type", "application/octet-stream"),
                  ("Content-Disposition",
                   'attachment; filename="%s"' % files[-1]),
                  ("Content-Length", str(len(data)))], data)


def act_new_link(req, db, sid):
    """A fresh private link; the old one is dead from this moment."""
    core.reissue_token(db, sid)
    return redirect(f"/students/{sid}?relink=1")


def act_attempt_delete(req, db, tid, aid):
    """One sitting removed - a trial run, or a student who opened it by
    mistake. The league forgets it with the row."""
    core.drop_attempt(db, aid)
    return redirect(f"/tests/{tid}")


def act_new_test(req, db):
    fields, files = req["files"]
    if not files:
        return redirect("/tests")
    try:
        data = json.loads(files[0][1].decode("utf-8"))
    except Exception:
        return redirect("/tests")
    tid = core.load_test(db, data)
    core.add_recorders(db, tid)          # its speaking tasks get a recorder
    return redirect(f"/tests/{tid}")


def act_test_key(req, db, tid):
    answers = {}
    for key, values in req["form"].items():
        m = re.match(r"^q(\d+)$", key)
        if m:
            answers[int(m.group(1))] = values[0]
    core.set_answer_key(db, tid, answers)
    return redirect(f"/tests/{tid}")


def act_test_publish(req, db, tid):
    t = db.execute("SELECT published FROM dtests WHERE id=?", (tid,)).fetchone()
    if t and core.test_ready(db, tid):
        db.execute("UPDATE dtests SET published=? WHERE id=?",
                   (0 if t["published"] else 1, tid))
        db.commit()
    return redirect(f"/tests/{tid}")


def act_test_delete(req, db, tid):
    # Homework that sets it holds on to it: the delete was refused by the
    # database and the page said only "Something broke". Say what holds it.
    uses = db.execute(
        "SELECT a.title, a.due_at, g.name gname FROM assignments a"
        " LEFT JOIN groups g ON g.id=a.group_id WHERE a.test_id=?"
        " ORDER BY a.due_at DESC", (tid,)).fetchall()
    if uses:
        cfg = core.load_config()
        rows = "".join(
            f'<li>{E(u["gname"] or "a class")} &middot; {E(u["title"])}'
            f'{" &middot; due " + E(core.local_day(core.parse(u["due_at"]), cfg)) if u["due_at"] else ""}</li>'
            for u in uses[:12])
        more = f"<li>and {len(uses) - 12} more</li>" if len(uses) > 12 else ""
        return html_response(page("Not deleted", f"""<h1>Not deleted</h1>
<div class="card"><p class="flush">It is set as homework, so it stays until that homework is deleted:</p>
<ul>{rows}{more}</ul>
<p class="sub flush">Delete the homework on the <a class="linky" href="/homework?show=all">Homework</a> page
first, then delete this.</p></div>
<p><a class="tab" href="/tests/{tid}">Back</a></p>""", "Tests"))
    db.execute("DELETE FROM dtests WHERE id=?", (tid,))
    db.commit()
    core.forget_handout(tid)
    return redirect("/tests")


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
<audio controls preload="none" class="wide" src="/song/{E(day)}"></audio>
<p class="sub gap-3">{song["bytes"] / 1024.0 / 1024.0:.1f} MB
&middot; uploaded {E(song["created_at"][:16].replace("T", " "))}</p>
<form method="post" action="/music/delete" class="gap-3"
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
<form method="post" action="/music/new" enctype="multipart/form-data"
 class="inline">
<label class="f">Day<input type="date" name="day" value="{E(day)}"></label>
<label class="f">Song file
<input type="file" name="song" accept="audio/*,.mp3,.m4a,.ogg,.wav,.flac" required></label>
<label class="f">Title <span class="sub">(optional)</span>
<input name="title" maxlength="120" placeholder="Shown to the students"></label>
<label class="f">Artist <span class="sub">(optional)</span>
<input name="artist" maxlength="120"></label>
<div class="gap-3"><button>Set the song</button></div>
</form>
<p class="sub gap-3">mp3, m4a, ogg, wav or flac, up to 20 MB. Setting a
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

NOT_COMPLETE = {
    "en": "Not complete. Do it on the site, or send photos of all the pages again.",
    "uz": "Toʻliq emas. Saytda bajaring yoki barcha sahifalar rasmini qaytadan yuboring.",
    "ru": "Не полностью. Сделайте на сайте или пришлите фото всех страниц ещё раз.",
}


def save_grade(db, sub, form):
    """Write one mark, from either the queue or a correction. Returns the score."""
    assignment = (db.execute("SELECT * FROM assignments WHERE id=?",
                             (sub["assignment_id"],)).fetchone()
                  if sub["assignment_id"] else None)
    tick = (form.get("tick", [""])[0] or "").strip()
    paper = bool(assignment and assignment["test_id"] and core.is_handout(db, assignment["test_id"]))
    note = (form.get("note", [""])[0] or "").strip() or None
    if paper and tick in ("done", "not"):
        # the paper copy of a handout: done is the doing half, not complete a
        # nought - said in the student's own language when nothing is written
        score = core.PAPER_TICK if tick == "done" else 0.0
        if tick == "not" and not note:
            st = db.execute("SELECT lang FROM students WHERE id=?", (sub["student_id"],)).fetchone()
            note = NOT_COMPLETE.get(st["lang"] if st else "en", NOT_COMPLETE["en"])
    elif assignment and assignment["rubric"]:
        score = core.set_criteria(
            db, sub["id"],
            {k: form.get("c_" + k, [""])[0] for k in core.CRITERIA_KEYS})
    else:
        score = core.mark_score(form.get("score", [""])[0])
    if score is None:
        return None
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


VOICE_EXT = {"audio/mp4": ".m4a", "audio/x-m4a": ".m4a", "audio/webm": ".webm",
             "audio/ogg": ".ogg", "audio/mpeg": ".mp3"}


def act_grade_voice(req, db):
    """Keep the teacher's recording beside the piece it is about. Uploaded
    the moment the recording stops, so the mark itself can be saved the
    ordinary way afterwards. A second recording replaces the first."""
    fields, files = req["files"]
    sid = (fields.get("submission_id", [""])[0] or "").strip()
    if not sid.isdigit() or not files:
        return json_response({"ok": False})
    sub = db.execute("SELECT id, voice FROM submissions WHERE id=?", (int(sid),)).fetchone()
    if not sub:
        return json_response({"ok": False})
    filename, data = files[0]
    if not data or len(data) < 1000:
        # a recorder that never heard anything hands over a header and no sound
        return json_response({"ok": False, "why": "empty"})
    if len(data) > 15 * 1024 * 1024:
        return json_response({"ok": False, "why": "too long"})
    kind = (fields.get("kind", [""])[0] or "").split(";")[0].strip().lower()
    ext = VOICE_EXT.get(kind) or (os.path.splitext(filename or "")[1].lower() or ".webm")
    if ext not in (".m4a", ".webm", ".ogg", ".mp3"):
        ext = ".webm"
    name = "voice_%d_%s%s" % (sub["id"], core.now().strftime("%Y%m%d%H%M%S"), ext)
    os.makedirs(core.UPLOAD_DIR, exist_ok=True)
    with open(os.path.join(core.UPLOAD_DIR, name), "wb") as fh:
        fh.write(data)
    if sub["voice"] and sub["voice"] != name:
        try:
            os.remove(os.path.join(core.UPLOAD_DIR, sub["voice"]))
        except OSError:
            pass
    db.execute("UPDATE submissions SET voice=? WHERE id=?", (name, sub["id"]))
    db.commit()
    return json_response({"ok": True, "name": name, "url": "/media/" + name})


def act_grade_voice_delete(req, db):
    sid = (req["form"].get("submission_id", [""])[0] or "").strip()
    if sid.isdigit():
        sub = db.execute("SELECT id, voice FROM submissions WHERE id=?", (int(sid),)).fetchone()
        if sub and sub["voice"]:
            try:
                os.remove(os.path.join(core.UPLOAD_DIR, sub["voice"]))
            except OSError:
                pass
            db.execute("UPDATE submissions SET voice=NULL WHERE id=?", (sub["id"],))
            db.commit()
    return json_response({"ok": True})


def act_grade(req, db):
    sid = int(req["form"].get("submission_id", [0])[0])
    sub = db.execute("SELECT * FROM submissions WHERE id=?", (sid,)).fetchone()
    back = queue_url(*queue_filter(req["form"]))
    if not sub:
        return redirect(back)
    score = save_grade(db, sub, req["form"])
    if score is None:
        return redirect(back)
    # The same mark saved twice - Enter pressed twice, a form sent again - is
    # not news: the student was sent their score twice.
    if sub["status"] != "graded" or sub["score"] is None or abs(sub["score"] - score) > 1e-9:
        notify_later(notify_graded, sid)
    return redirect(back)


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
        notify_later(notify_graded, sid)
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


def notify_later(fn, *args):
    """Run fn(db, *args) on a thread of its own, so the page does not wait.

    Telling a student their mark meant working out where they stand in the
    class and two calls to Telegram, all before the next piece of work could
    open: a second or two on every save. The mark is saved before this
    starts; the message is best effort and must never put an error page in
    front of the person marking. The thread looks at the same copy of the
    data as the request - the demo copy or the practice copy stays that copy,
    so nothing invented can reach a real student's phone.
    """
    demo, practice = core.demo_on(), core.practice_on()

    def run():
        core.demo_on(demo)
        core.practice_on(practice)
        db = core.connect()
        try:
            fn(db, *args)
        except Exception:
            traceback.print_exc()
        finally:
            db.close()
    threading.Thread(target=run, daemon=True).start()


def notify_each(db, sids):
    for sid in sids:
        try:
            notify_graded(db, sid)
        except Exception:
            traceback.print_exc()        # one failed message does not stop the rest


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

    site = core.meta_get(db, "site_url")
    url = ("%s/s/%s?tab=feedback" % (site.rstrip("/"), core.student_token(db, row["sid"]))
           if site else None)
    voice = db.execute("SELECT voice FROM submissions WHERE id=?", (sid,)).fetchone()["voice"]
    bot.send_score(token, row["telegram_id"], row["lang"], row["title"], row["score"],
                   tags, row["note"], sid, student_id=row["sid"], url=url,
                   voice=os.path.join(core.UPLOAD_DIR, voice) if voice else None)


def act_skip(req, db):
    sid = req["form"].get("submission_id", [None])[0] or req["query"].get("submission_id", [None])[0]
    if sid:
        # push to the back of the queue rather than dropping it
        db.execute("UPDATE submissions SET created_at=? WHERE id=?", (core.iso(core.now()), int(sid)))
        db.commit()
    # the set being marked comes with the form, or with the keyboard's link
    gid, due = queue_filter(req["form"])
    if gid is None and due is None:
        gid, due = queue_filter(req["query"])
    return redirect(queue_url(gid, due))


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
    return redirect(f"/groups/{gid}?level=1")


def act_repeat_homework(req, db, gid):
    """Give the same list of tasks again with a new deadline.

    Setting homework is the most repetitive thing on the site: the same six or
    seven tasks, a week later. This is that, in one press.
    """
    f = req["form"]
    due = (f.get("due", [""])[0] or "").strip()
    if not due:
        return redirect(f"/groups/{gid}?tab=homework")
    due_iso = core.deadline_iso(due, f.get("due_time", [""])[0])
    if core.deadline_passed(due_iso):
        return redirect(f"/groups/{gid}?tab=homework&pastdue=1")
    made = []
    for a in core.last_homework_batch(db, gid):
        if already_set(db, gid, a["title"], due_iso):
            continue
        made.append(db.execute(
            "INSERT INTO assignments (group_id, title, task_type, due_at, created_at,"
            " published, test_id) VALUES (?,?,?,?,?,1,?)",
            (gid, a["title"], a["task_type"], due_iso, core.iso(core.now()),
             a["test_id"] if "test_id" in a.keys() else None),
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
    return redirect(_back(req, "/assignments"))


def act_unpublish_assignment(req, db, aid):
    db.execute("UPDATE assignments SET published=0 WHERE id=?", (aid,))
    db.commit()
    return redirect(_back(req, "/assignments"))


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
    return redirect(_back(req, "/assignments"))


def act_close_past(req, db):
    """Close every published piece whose deadline has passed - the whole
    school, or one class when the list was filtered to it. Nothing about
    the students' work changes; the pieces simply stop being open."""
    f = req["form"]
    gid = (f.get("group_id", [""])[0] or "").strip()
    rows = db.execute(
        "SELECT id, group_id, due_at FROM assignments"
        " WHERE closed=0 AND published=1 AND due_at IS NOT NULL"
        + (" AND group_id=?" if gid.isdigit() else ""),
        (int(gid),) if gid.isdigit() else ()).fetchall()
    cfg = core.load_config()
    shut = [r["id"] for r in rows if not core.still_open(r["due_at"], cfg)]
    for aid in shut:
        db.execute("UPDATE assignments SET closed=1 WHERE id=?", (aid,))
    db.commit()
    back = _back(req, "/homework")
    joiner = "&" if "?" in back else "?"
    return redirect(f"{back}{joiner}closed={len(shut)}")


def act_batch_open(req, db):
    gid, due, items = _batch_of(req, db)
    for a in items:
        db.execute("UPDATE assignments SET closed=0 WHERE id=?", (a["id"],))
    db.commit()
    return redirect(_back(req, "/assignments"))


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
    return redirect(_back(req, "/assignments"))


def act_batch_delete(req, db):
    """Remove a whole batch, but never the students' marked work."""
    gid, due, items = _batch_of(req, db)
    for a in items:
        db.execute("UPDATE submissions SET assignment_id=NULL WHERE assignment_id=?",
                   (a["id"],))
        db.execute("DELETE FROM assignments WHERE id=?", (a["id"],))
    db.commit()
    return redirect(_back(req, "/assignments"))


def act_batch_league(req, db):
    """Count a set of homework in the league, or stop counting it."""
    gid, due, items = _batch_of(req, db)
    if items:
        core.set_in_league(db, gid, due, not all(a["in_league"] for a in items))
    return redirect(_back(req, "/assignments"))


def act_batch_edit(req, db):
    """Move the deadline for every item that was set together."""
    gid, due, items = _batch_of(req, db)
    f = req["form"]
    when = core.deadline_iso(f.get("new_due", [""])[0], f.get("new_time", [""])[0])
    if not core.same_minute(when, due) and core.deadline_passed(when):
        back = _back(req, "/assignments")
        return redirect(back + ("&" if "?" in back else "?") + "pastdue=1")
    for a in items:
        db.execute("UPDATE assignments SET due_at=? WHERE id=?", (when, a["id"]))
    # a piece handed in before the new deadline is no longer late
    for a in items:
        db.execute(
            "UPDATE submissions SET late=CASE WHEN ? IS NOT NULL AND created_at > ?"
            " THEN 1 ELSE 0 END WHERE assignment_id=?", (when, when, a["id"]))
    db.commit()
    back = _back(req, "/assignments")
    # the homework's own page is addressed by its deadline, which just moved
    if back.startswith("/homework/set?") and gid:
        back = set_url(gid, when)
    return redirect(back)


def unit_plan_json(req, db):
    """What a unit's homework is, so the teacher does not retype it."""
    q = req["query"]
    gid = (q.get("group_id", [""])[0] or "").strip()
    unit = (q.get("unit", [""])[0] or "").strip()
    if not gid.isdigit() or not unit.isdigit():
        return json_response({"items": []})
    if q.get("peek") == ["1"]:
        # only the Destination unit remembered for this one, to fill the box in
        return json_response({"destination": core.destination_for(
            db, core.level_of(db, int(gid)), int(unit))})
    core.seed_prompts(db)
    dest = q.get("destination")
    plan = core.unit_homework(
        db, int(gid), int(unit),
        pair=(q.get("pair", ["A&C"])[0] or "A&C"),
        kind=(q.get("kind", ["essay"])[0] or "essay"),
        practice=(q.get("practice", [""])[0] or "").strip(),
        destination=dest[0] if dest else None)
    return json_response(plan)


def act_new_list(req, db):
    f = req["form"]
    gid = f.get("group_id", [None])[0]
    items = parse_list(f.get("items", [""])[0])
    # as many handouts as were ticked, each one more piece of the set
    books = []
    for handout in f.get("handout", []):
        handout = (handout or "").strip()
        if handout.isdigit() and gid and gid.isdigit():
            book = db.execute("SELECT id, title FROM dtests WHERE id=? AND kind='handout'"
                              " AND level_id=(SELECT level_id FROM groups WHERE id=?)",
                              (int(handout), int(gid))).fetchone()
            if book:
                books.append(book)
                if book["title"] not in items:
                    items.append(book["title"])
    if (f.get("prompt", [""])[0] or "").strip() and len(items) > 1 and not any(
            t.lower().startswith("writing") for t in items):
        # a question among several pieces is a writing task of its own: it
        # gets its own line rather than turning the first - the workbook -
        # into a writing paper. A lone line is the writing task itself.
        items.append("Writing")
    if not gid or not items:
        return redirect("/assignments")
    due = f.get("due", [""])[0]
    due_iso = core.deadline_iso(due, f.get("due_time", [""])[0])
    if core.deadline_passed(due_iso):
        # a deadline in the past closes the homework the moment it is set: the
        # students never see it and the league counts it as missed. The form
        # comes back as it was typed, with the date to fix.
        return view_assignments(req, db, error="past", keep=f)
    publish_now = f.get("publish", [""])[0] == "1"
    # the Destination unit typed for a unit is remembered for the next time
    unit_no = (f.get("unit", [""])[0] or "").strip()
    dest = (f.get("destination", [""])[0] or "").strip()
    if unit_no.isdigit() and dest:
        core.destination_for(db, core.level_of(db, int(gid)), int(unit_no), dest)
    # a question makes it a writing paper; only the first item carries it, since
    # one posting is one question
    prompt = (f.get("prompt", [""])[0] or "").strip() or None
    def whole(key):
        v = (f.get(key, [""])[0] or "").strip()
        return int(v) if v.isdigit() and int(v) > 0 else None
    minutes, min_words = whole("minutes"), whole("min_words")

    # The question belongs to the writing line, not to all of them. Setting
    # four things at once used to turn every one of them into the same writing
    # paper, because the prompt was handed to each row in the loop.
    writing_at = 0
    for i, t in enumerate(items):
        if t.lower().startswith("writing"):
            writing_at = i
            break

    # A line naming a booklet on this group's level *is* that booklet: the
    # homework links to it instead of telling the student to go and find it.
    booklets = {}
    level_id = core.level_of(db, int(gid))
    if level_id:
        for r in db.execute(
                "SELECT id, title FROM dtests WHERE level_id=? AND layout IS NOT NULL"
                " ORDER BY published, id", (level_id,)):
            booklets[r["title"].replace(" (booklet)", "").strip().lower()] = r["id"]
    for book in books:
        booklets[book["title"].strip().lower()] = book["id"]   # the ones ticked, exactly

    created = []
    for i, title in enumerate(items):
        if already_set(db, int(gid), title, due_iso):
            continue
        mine = prompt if (prompt and i == writing_at) else None
        created.append(db.execute(
            "INSERT INTO assignments (group_id, title, task_type, due_at, created_at,"
            " published, rubric, prompt, minutes, min_words, test_id)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (int(gid), title, f.get("task_type", ["other"])[0], due_iso,
             core.iso(core.now()), 1 if publish_now else 0,
             1 if f.get("rubric", [""])[0] == "1" else 0,
             mine, minutes if mine else None, min_words if mine else None,
             booklets.get(title.strip().lower()) or core.destination_test(db, title)
             or core.workbook_test(db, title, level_id) or core.unit_extra_test(db, title, level_id)),
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
    row = db.execute("SELECT group_id, due_at FROM assignments WHERE id=?", (aid,)).fetchone()
    back = _back(req, f"/groups/{row['group_id']}?tab=homework" if row else "/assignments")
    when = core.deadline_iso(due, f.get("due_time", [""])[0])
    if row and not core.same_minute(when, row["due_at"]) and core.deadline_passed(when):
        return redirect(back + ("&" if "?" in back else "?") + "pastdue=1")
    if title:
        db.execute("UPDATE assignments SET title=? WHERE id=?", (title[:120], aid))
    if row and not core.same_minute(when, row["due_at"]):
        db.execute("UPDATE assignments SET due_at=? WHERE id=?", (when, aid))
    db.commit()
    return redirect(back)


def act_delete_assignment(req, db, aid):
    """Remove the homework but never the students' work."""
    row = db.execute("SELECT group_id FROM assignments WHERE id=?", (aid,)).fetchone()
    db.execute("UPDATE submissions SET assignment_id=NULL WHERE assignment_id=?", (aid,))
    db.execute("DELETE FROM assignments WHERE id=?", (aid,))
    db.commit()
    return redirect(_back(
        req, f"/groups/{row['group_id']}?tab=homework" if row else "/assignments"))


def act_open_assignment(req, db, aid):
    row = db.execute("SELECT group_id FROM assignments WHERE id=?", (aid,)).fetchone()
    db.execute("UPDATE assignments SET closed=0 WHERE id=?", (aid,))
    db.commit()
    return redirect(_back(
        req, f"/groups/{row['group_id']}?tab=homework" if row else "/assignments"))


def act_close_assignment(req, db, aid):
    db.execute("UPDATE assignments SET closed=1 WHERE id=?", (aid,))
    db.commit()
    return redirect(_back(req, "/assignments"))


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
        core.set_group(db, sid, gid)
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
    ("GET", r"^/backup\.json$", view_transfer_json),
    ("POST", r"^/questions/(\d+)/answer$", act_answer_question),
    ("GET", r"^/materials$", view_materials),
    ("GET", r"^/materials/(\d+)/file$", view_material_file),
    ("GET",  r"^/assignments/unit\.json$", unit_plan_json),
    ("GET",  r"^/backup$", view_backup),
    ("GET",  r"^/prompts$", view_prompts),
    ("GET",  r"^/prompts/suggest$", suggest_json),
    ("GET",  r"^/prompts/units$", units_json),
    ("POST", r"^/prompts/new$", act_new_prompt),
    ("POST", r"^/prompts/delete$", act_delete_prompt),
    ("GET",  r"^/reteach$", view_reteach),
    ("GET",  r"^/records$", view_records),
    ("GET",  r"^/kpi$", view_kpi),
    ("POST", r"^/students/(\d+)/since$", act_student_since),
    ("POST", r"^/students/(\d+)/excuse$", act_student_excuse),
    ("POST", r"^/demo/on$", act_demo_on),
    ("POST", r"^/demo/off$", act_demo_off),
    ("POST", r"^/demo/reset$", act_demo_reset),
    ("GET",  r"^/parents$", view_parents),
    ("GET",  r"^/parents/card\.png$", view_parents_card),
    ("POST", r"^/parents/send$", act_parents_send),
    ("POST", r"^/parents/say$", act_parents_say),
    ("POST", r"^/parents/channel$", act_parents_channel),
    ("GET",  r"^/practice$", view_practice),
    ("GET",  r"^/practice/screens$", view_practice_screens),
    ("POST", r"^/practice/start$", act_practice_start),
    ("POST", r"^/practice/end$", act_practice_end),
    ("POST", r"^/kpi/level/(\d+)$", act_save_kpi_level),
    ("POST", r"^/kpi/profile$", act_save_kpi_profile),
    ("POST", r"^/records/test/new$", act_new_class_test),
    ("POST", r"^/records/test/(\d+)/save$", act_save_class_scores),
    ("POST", r"^/records/exam/save$", act_save_exam),
    ("POST", r"^/records/left$", act_mark_left),
    ("GET",  r"^/tests$", view_tests),
    ("GET",  r"^/tests/(\d+)$", view_test),
    ("GET",  r"^/tests/(\d+)/look$", view_handout_look),
    ("POST", r"^/tests/(\d+)/key$", act_test_key),
    ("POST", r"^/tests/(\d+)/publish$", act_test_publish),
    ("POST", r"^/tests/(\d+)/delete$", act_test_delete),
    ("POST", r"^/tests/(\d+)/carry$", act_test_carry),
    ("POST", r"^/tests/(\d+)/void$", act_test_void),
    ("POST", r"^/tests/(\d+)/timing$", act_test_timing),
    ("GET",  r"^/tests/(\d+)/writing$", view_test_writing),
    ("GET",  r"^/speaking$", view_speaking),
    ("POST", r"^/speaking/note$", act_speak_note),
    ("POST", r"^/speaking/voice/delete$", act_speak_voice_delete),
    ("POST", r"^/tests/(\d+)/attempt/(\d+)/delete$", act_attempt_delete),
    ("POST", r"^/students/(\d+)/newlink$", act_new_link),
    ("POST", r"^/cleanup$", act_free_space),
    ("GET",  r"^/settings$", view_settings),
    ("POST", r"^/settings$", act_settings),
    ("POST", r"^/settings/purge$", act_settings_purge),
    ("GET",  r"^/music$", view_music),
    ("POST", r"^/music/delete$", act_delete_song),
    ("POST", r"^/materials/(\d+)/delete$", act_delete_material),
    ("POST", r"^/materials/delete$", act_delete_materials),
    ("GET", r"^/vocab$", view_vocab),
    ("GET", r"^/vocab/(\d+)$", view_word_list),
    ("GET", r"^/skip$", act_skip),
    ("POST", r"^/grade$", act_grade),
    ("POST", r"^/grade/attach$", act_grade_attach),
    ("POST", r"^/regrade$", act_regrade),
    ("GET",  r"^/regrade/(\d+)$", view_regrade),
    ("POST", r"^/notes/new$", act_new_note),
    ("POST", r"^/notes/delete$", act_delete_note),
    ("POST", r"^/skip$", act_skip),
    ("POST", r"^/grade/voice/delete$", act_grade_voice_delete),
    ("POST", r"^/groups/new$", act_new_group),
    ("POST", r"^/groups/(\d+)/level$", act_set_group_level),
    ("POST", r"^/groups/(\d+)/repeat$", act_repeat_homework),
    ("GET",  r"^/queue/grid$", view_grade_grid),
    ("POST", r"^/grade/many$", act_grade_many),
    ("GET",  r"^/championship$", view_championship),
    ("POST", r"^/championship/start$", act_start_season),
    ("POST", r"^/championship/close$", act_close_season),
    ("POST", r"^/championship/pause$", act_pause_season),
    ("POST", r"^/championship/resume$", act_resume_season),
    ("POST", r"^/championship/unpause$", act_unpause_span),
    ("GET",  r"^/play$", view_play),
    ("GET",  r"^/play/(\d+)$", view_game_board),
    ("GET",  r"^/play/(\d+)/state\.json$", game_state_json),
    ("GET",  r"^/play/(\d+)/end$", act_game_end),
    ("POST", r"^/play/new$", act_new_game),
    ("POST", r"^/play/(\d+)/next$", act_game_next),
    ("GET",  r"^/homework/set$", view_homework_set),
    ("GET",  r"^/insights$", view_insights),
    ("GET",  r"^/lessons$", view_lessons),
    ("POST", r"^/assignments/list$", act_new_list),
    ("POST", r"^/assignments/batch/close$", act_batch_close),
    ("POST", r"^/assignments/close-past$", act_close_past),
    ("POST", r"^/assignments/batch/open$", act_batch_open),
    ("POST", r"^/assignments/batch/publish$", act_batch_publish),
    ("POST", r"^/assignments/batch/delete$", act_batch_delete),
    ("POST", r"^/assignments/batch/edit$", act_batch_edit),
    ("POST", r"^/assignments/batch/league$", act_batch_league),
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
    ("POST", r"^/vocab/(\d+)/rename$", act_rename_word_list),
]


# the stylesheet and the big scripts, gzipped once rather than on every visit
_ZIP_CACHE = {}


class Handler(BaseHTTPRequestHandler):
    server_version = "TA/1.0"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass

    def _same_origin(self):
        """Refuse a POST that another site asked the browser to make.

        The session cookie is already SameSite=Lax, which stops a browser
        sending it on a cross-site POST at all, so this is a second lock on
        the same door rather than the first. It reads Origin, falling back to
        Referer, and only refuses when one of them is present and points
        somewhere else - a request with neither is a script or the bot, not a
        browser being steered by a hostile page.
        """
        host = (self.headers.get("Host") or "").split(":")[0].lower()
        for name in ("Origin", "Referer"):
            raw = self.headers.get(name)
            if not raw or raw == "null":
                continue
            where = urllib.parse.urlsplit(raw).hostname or ""
            return where.lower() == host
        return True

    def _token(self):
        m = re.search(r"ta_session=([A-Za-z0-9_-]+)",
                      self.headers.get("Cookie", ""))
        return m.group(1) if m else None

    def _session(self):
        token = self._token()
        if not token:
            return False
        db = core.connect(real=True)     # sessions live in the real file only
        try:
            return core.session_live(db, token)
        finally:
            db.close()

    def _cookie(self, name):
        raw = self.headers.get("Cookie") or ""
        for part in raw.split(";"):
            k, _, v = part.strip().partition("=")
            if k == name:
                return v
        return ""

    def _enter_demo_if_asked(self, path):
        """Point this thread at the demo copy, for a signed-in teacher only.

        Student pages, parent pages and the static files never switch: a
        student's link is looked up in the real file whatever cookies the
        browser happens to carry. The bot and the jobs run on other threads
        and cannot see this at all.
        """
        core.demo_on(False)
        core.practice_on(False)
        if path.startswith("/s/try-"):
            # the practice student: read from the practice copy, and only
            # when it is the teacher asking - to anyone else it is no link
            if self._session() and core.is_practice_token(path.split("/")[2]):
                core.practice_on(True)
            return
        if path.startswith(("/s/", "/p/", "/static/", "/login", "/demo/")):
            return
        if self._cookie("ta_demo") == "1" and self._session():
            core.demo_ready()
            core.demo_on(True)

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
                 else "image/png" if name.endswith(".png")
                 else "application/octet-stream")
        # named with this deploy's fingerprint (STATIC_V): it cannot change
        # under that name, so it is kept; a bare name is kept five minutes
        q = urllib.parse.urlsplit(self.path).query
        keep = ("public, max-age=31536000, immutable" if ("v=" + STATIC_V) in q
                else "max-age=300")
        self._send(200, [("Content-Type", ctype), ("Content-Length", str(len(data))),
                         ("Cache-Control", keep)], data)

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
                 else "audio/mp4" if name.endswith((".m4a", ".aac", ".mp4"))
                 else "audio/webm" if name.endswith((".webm", ".weba"))
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
        m = re.match(r"^/s/([A-Za-z0-9_-]+)/solo/(\d+)(\.json)?$", path)
        if m:
            db = core.connect()
            try:
                fn = solo_state_json if m.group(3) else view_solo
                return self._send(*fn({"query": query}, db, m.group(1), int(m.group(2))))
            finally:
                db.close()
        m = re.match(r"^/s/([A-Za-z0-9_-]+)/battle/(\d+)(\.json)?$", path)
        if m:
            db = core.connect()
            try:
                fn = battle_state_json if m.group(3) else view_battle
                return self._send(*fn({"query": query}, db, m.group(1), int(m.group(2))))
            finally:
                db.close()
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
        elif query.get("e") == ["locked"]:
            # the upload refuses more photos for a task already handed in; it
            # said so with this code, and the page used to say nothing at all
            flash = ('<div class="flash err">That task has already been sent to your teacher, '
                     'so these photos were not added. Ask your teacher if you need to change it.</div>')
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

    ZIPPED = ("text/html", "text/css", "application/javascript", "application/json")

    def _squeeze(self, status, headers, body):
        """The same answer, gzipped, when the browser takes it that way.

        Pages, the stylesheet and the scripts are text and shrink to a fifth
        or less; on a phone's connection that is most of the wait. Pictures
        and recordings are already compressed and pass through as they are.
        """
        if (status != 200 or not body or len(body) < 1400
                or "gzip" not in (self.headers.get("Accept-Encoding") or "")):
            return headers, body
        names = {k.lower(): v for k, v in headers}
        if "content-encoding" in names or not names.get("content-type", "").startswith(self.ZIPPED):
            return headers, body
        import gzip
        key = body if names["content-type"].startswith(("text/css", "application/javascript")) else None
        packed = _ZIP_CACHE.get(key) if key is not None else None
        if packed is None:
            packed = gzip.compress(body, compresslevel=6)
            if key is not None:
                if len(_ZIP_CACHE) > 40:
                    _ZIP_CACHE.clear()
                _ZIP_CACHE[key] = packed
        headers = [(k, v) for k, v in headers if k.lower() != "content-length"]
        headers += [("Content-Encoding", "gzip"), ("Vary", "Accept-Encoding"),
                    ("Content-Length", str(len(packed)))]
        return headers, packed

    def _send(self, status, headers, body):
        """Write a response, in pieces, tolerating a client that walks away.

        A media element asks for a range, takes what it needs to fill its
        buffer and hangs up mid-transfer. That is normal behaviour, not an
        error: sending the body in one call made every one of those a broken
        pipe, and the browser answered each dead connection by opening another
        - which is what the stuttering was.
        """
        self._answered = True
        headers, body = self._squeeze(status, headers, body)
        try:
            self.send_response(status)
            for k, v in self.SECURITY_HEADERS:
                if k == "X-Frame-Options" and core.practice_on():
                    v = "SAMEORIGIN"    # the practice pages, framed on "Every screen"
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
        self._answered = True
        try:
            self.send_response(status)
            for k, v in self.SECURITY_HEADERS:
                if k == "X-Frame-Options" and core.practice_on():
                    v = "SAMEORIGIN"    # the practice pages, framed on "Every screen"
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
        self._answered = False
        self._enter_demo_if_asked(urllib.parse.urlsplit(self.path).path)
        core.memo_begin()               # a page is read, not changed: see core.memo_begin
        try:
            return self._do_GET_inner()
        except Exception as exc:
            self._broke(exc)
        finally:
            core.memo_end()
            core.demo_on(False)
            core.practice_on(False)

    def _broke(self, exc):
        """A page that failed outside the teacher's own routes - a student's,
        a parent's, a file. The teacher's routes catch their own errors;
        these did not, so the connection simply dropped: the student saw the
        host's bare 502, and nobody was told. Now the student gets a page that
        says what to do, and the teacher gets the error in Telegram."""
        traceback.print_exc()
        where = urllib.parse.urlsplit(self.path).path
        # never a student's link in a message, and one key per kind of page
        where = re.sub(r"^/([sp])/[A-Za-z0-9_-]+", r"/\1/<link>", where)
        where = re.sub(r"\d+", "N", where)
        core.report_breakage(where, exc)
        if self._answered:
            return                      # part of an answer has gone already
        self._send(*html_response(student_page(
            "Something went wrong",
            "<h1>Something went wrong</h1><p class='sub'>Your teacher has been told. "
            "Go back and try again in a minute &mdash; nothing you saved before is lost.</p>",
            music=False), 500))

    def _do_GET_inner(self):
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
        # the teacher's recording, playable from the student's own page only:
        # the piece must be theirs, and /media/ itself stays the teacher's
        m = re.match(r"^/s/([A-Za-z0-9_-]+)/voice/(\d+)$", path)
        if m:
            db = core.connect()
            try:
                st = core.student_by_token(db, m.group(1))
                row = st and db.execute(
                    "SELECT voice FROM submissions WHERE id=? AND student_id=?",
                    (int(m.group(2)), st["id"])).fetchone()
                if not row or not row["voice"]:
                    return self._send(*not_found())
                name = row["voice"]
            finally:
                db.close()
            return self._serve_media("/media/" + name)
        m = re.match(r"^/s/([A-Za-z0-9_-]+)/speak/([A-Za-z0-9_.-]+)$", path)
        if m:
            name = m.group(2)
            ok = core.SPEAK_FILE_AT.match(name)
            db = core.connect()
            try:
                st = core.student_by_token(db, m.group(1))
                mine = ok and st and db.execute("SELECT 1 FROM dattempts WHERE id=? AND student_id=?",
                                                (int(ok.group(1)), st["id"])).fetchone()
            finally:
                db.close()
            if not mine:
                return self._send(*not_found())
            return self._serve_media("/media/" + name)
        m = re.match(r"^/s/([A-Za-z0-9_-]+)/speakfb/(\d+)/(\d+)$", path)
        if m:
            db = core.connect()
            try:
                st = core.student_by_token(db, m.group(1))
                row = st and db.execute(
                    "SELECT f.voice FROM speak_feedback f JOIN dattempts a ON a.id=f.attempt_id"
                    " WHERE f.attempt_id=? AND f.question_id=? AND a.student_id=?",
                    (int(m.group(2)), int(m.group(3)), st["id"])).fetchone()
            finally:
                db.close()
            if not row or not row["voice"]:
                return self._send(*not_found())
            return self._serve_media("/media/" + row["voice"])
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
        m = re.match(r"^/testimg/([A-Za-z0-9_.-]+\.png)$", path)
        if m:
            full = os.path.join(core.MATERIAL_DIR, m.group(1))
            if not os.path.isfile(full):
                return self._send(*not_found())
            return self._send_file(200, [("Content-Type", "image/png"),
                                         ("Content-Length", str(os.path.getsize(full))),
                                         ("Cache-Control", "private, max-age=86400")],
                                   full, 0, os.path.getsize(full))

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
        m = re.match(r"^/audio/([^/]+)/(\d{1,2}\.\d{2})\.mp3$", path)
        if m:
            # a track is for the class, not for the open web: either a signed-in
            # teacher, or somebody holding a student's own link
            who = (query.get("s", [""])[0] or "").strip()
            allowed = self._session()
            if not allowed and who:
                db = core.connect()
                try:
                    allowed = bool(core.student_by_token(db, who))
                finally:
                    db.close()
            if not allowed:
                return self._send(*not_found())
            # the route table turns every captured group into an int, which a
            # level name is not, so this one is answered here
            db = core.connect()
            try:
                return self._send(*serve_track(
                    {"query": {}, "form": {}}, db,
                    urllib.parse.unquote(m.group(1)), m.group(2)))
            finally:
                db.close()

        if path == "/login":
            return self._send(*view_login(None))
        if path == "/logout":
            token = self._token()
            if token:
                db = core.connect()
                try:
                    core.close_session(db, token)
                finally:
                    db.close()
            return self._send(*redirect("/login", [("Set-Cookie", "ta_session=; Max-Age=0; Path=/")]))
        if not self._session():
            return self._send(*redirect("/login"))
        self._remember_site_url()
        if path.startswith("/media/"):
            return self._serve_media(path)
        return self._dispatch("GET", path, {"query": query, "form": {},
                                            "headers": self.headers})

    def do_POST(self):
        self._answered = False
        self._enter_demo_if_asked(urllib.parse.urlsplit(self.path).path)
        try:
            return self._do_POST_inner()
        except Exception as exc:
            self._broke(exc)
        finally:
            core.demo_on(False)
            core.practice_on(False)

    def _do_POST_inner(self):
        parsed = urllib.parse.urlsplit(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length") or 0)
        if length > uploads.MAX_BYTES:  # covers photo batches and data imports
            return self._send(*html_response(
                student_page("Too large", "<h1>Those photos are too large</h1>"
                             "<p class='sub'>Send fewer pages at a time.</p>"), 413))
        body = self.rfile.read(length) if length else b""

        if not self._same_origin():
            return self._send(*html_response(
                student_page("Not allowed", "<h1>That request came from "
                             "somewhere else</h1><p class='sub'>Open the site "
                             "itself and try again.</p>"), 403))

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

        if path == "/grade/voice":
            if not self._session():
                return self._send(*json_response({"ok": False}))
            fields, files = uploads.parse_multipart(
                body, self.headers.get("Content-Type", ""))
            db = core.connect()
            try:
                return self._send(*act_grade_voice(
                    {"query": {}, "form": {}, "files": (fields, files)}, db))
            finally:
                db.close()

        if path == "/speaking/voice":
            if not self._session():
                return self._send(*json_response({"ok": False}))
            fields, files = uploads.parse_multipart(body, self.headers.get("Content-Type", ""))
            db = core.connect()
            try:
                return self._send(*act_speak_voice({"query": {}, "form": {}, "files": (fields, files)}, db))
            finally:
                db.close()

        m = re.match(r"^/s/([A-Za-z0-9_-]+)/handout/(\d+)/speak$", path)
        if m:
            fields, files = uploads.parse_multipart(body, self.headers.get("Content-Type", ""))
            db = core.connect()
            try:
                return self._send(*act_handout_speak({"query": {}, "form": {}, "files": (fields, files)}, db,
                                                     m.group(1), int(m.group(2))))
            finally:
                db.close()

        if path == "/audio/new":
            if not self._session():
                return self._send(*redirect("/login"))
            fields, files = uploads.parse_multipart(
                body, self.headers.get("Content-Type", ""))
            db = core.connect()
            try:
                return self._send(*act_new_track(
                    {"query": {}, "form": {}, "files": (fields, files)}, db))
            finally:
                db.close()

        if path == "/tests/new":
            if not self._session():
                return self._send(*redirect("/login"))
            fields, files = uploads.parse_multipart(
                body, self.headers.get("Content-Type", ""))
            db = core.connect()
            try:
                return self._send(*act_new_test(
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

        m = re.match(r"^/s/([A-Za-z0-9_-]+)/rate$", path)
        if m:
            form = urllib.parse.parse_qs(body.decode("utf-8", "replace"),
                                         keep_blank_values=True)
            db = core.connect()
            try:
                return self._send(*act_rate_lesson({"query": {}, "form": form}, db,
                                                   m.group(1)))
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

        m = re.match(r"^/s/([A-Za-z0-9_-]+)/test/(\d+)/save$", path)
        if m:
            saved = urllib.parse.parse_qs(body.decode("utf-8", "replace"),
                                          keep_blank_values=True)
            db = core.connect()
            try:
                return self._send(*act_book_save(
                    {"query": {}, "form": saved}, db, m.group(1), int(m.group(2))))
            finally:
                db.close()

        m = re.match(r"^/s/([A-Za-z0-9_-]+)/write/(\d+)(/save)?$", path)
        if m:
            form = urllib.parse.parse_qs(body.decode("utf-8", "replace"),
                                         keep_blank_values=True)
            db = core.connect()
            try:
                return self._send(*act_student_write(
                    {"query": {}, "form": form}, db, m.group(1), int(m.group(2)),
                    quiet=bool(m.group(3))))
            finally:
                db.close()

        m = re.match(r"^/s/([A-Za-z0-9_-]+)/test/(\d+)$", path)
        if m:
            form = urllib.parse.parse_qs(body.decode("utf-8", "replace"),
                                         keep_blank_values=True)
            db = core.connect()
            try:
                return self._send(*act_student_test(
                    {"query": {}, "form": form}, db, m.group(1), int(m.group(2))))
            finally:
                db.close()

        m = re.match(r"^/s/([A-Za-z0-9_-]+)/practice/(fill|finish|test|mark)$", path)
        if m:
            form = urllib.parse.parse_qs(body.decode("utf-8", "replace"),
                                         keep_blank_values=True)
            db = core.connect()
            try:
                return self._send(*act_practice({"form": form}, db, m.group(1), m.group(2)))
            finally:
                db.close()

        m = re.match(r"^/s/([A-Za-z0-9_-]+)/handout/(\d+)/(save|check)$", path)
        if m:
            form = urllib.parse.parse_qs(body.decode("utf-8", "replace"),
                                         keep_blank_values=True)
            db = core.connect()
            try:
                fn = (act_handout_save if m.group(3) == "save"
                      else act_handout_check)
                return self._send(*fn({"form": form}, db, m.group(1),
                                      int(m.group(2))))
            finally:
                db.close()

        m = re.match(r"^/s/([A-Za-z0-9_-]+)/battle/"
                     r"(new|code|join|decline|(\d+)/(start|answer|invite|leave))$", path)
        if m:
            form = urllib.parse.parse_qs(body.decode("utf-8", "replace"),
                                         keep_blank_values=True)
            tok, what = m.group(1), m.group(2)
            db = core.connect()
            try:
                flat = {"new": act_battle_new, "code": act_battle_code,
                        "join": act_battle_join, "decline": act_battle_decline}
                if what in flat:
                    return self._send(*flat[what]({"form": form}, db, tok))
                onbattle = {"start": act_battle_start, "answer": act_battle_answer,
                            "invite": act_battle_invite, "leave": act_battle_leave}
                return self._send(*onbattle[m.group(4)](
                    {"form": form}, db, tok, int(m.group(3))))
            finally:
                db.close()

        m = re.match(r"^/s/([A-Za-z0-9_-]+)/solo/(start|(\d+)/answer)$", path)
        if m:
            form = urllib.parse.parse_qs(body.decode("utf-8", "replace"),
                                         keep_blank_values=True)
            db = core.connect()
            try:
                if m.group(2) == "start":
                    return self._send(*act_solo_start({"form": form}, db, m.group(1)))
                return self._send(*act_solo_answer({"form": form}, db, m.group(1),
                                                   int(m.group(3))))
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
                # Signing in had no error handling at all, so anything that
                # went wrong here dropped the connection and the host answered
                # 502 - no page, no log line, nothing to work from. A teacher
                # locked out of their own site deserves better than a blank.
                try:
                    db = core.connect()
                    try:
                        token = core.open_session(db)
                    finally:
                        db.close()
                except Exception as exc:
                    import traceback
                    traceback.print_exc()
                    core.report_breakage("/login", exc)
                    return self._send(*view_login(
                        None, err="Could not start a session: %s: %s"
                                  % (type(exc).__name__, str(exc)[:160])))
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
                    core.report_breakage(path, exc)
                    # the teacher is signed in, so the error itself can be shown:
                    # a page that only says "look in the log" helps nobody who
                    # cannot open the log
                    frames = traceback.extract_tb(exc.__traceback__)
                    where = ("%s, line %d, in %s" % (os.path.basename(frames[-1].filename),
                                                     frames[-1].lineno, frames[-1].name)
                             if frames else "")
                    detail = E("%s: %s" % (type(exc).__name__, exc))
                    return self._send(*html_response(
                        page("Error", "<h1>Something broke</h1><div class='card'>"
                             f"<p class='flush'><code>{detail}</code></p>"
                             f"<p class='sub gap-2 flush'>{E(where)}. The full trace is in "
                             "the server log, and a message has gone to you in Telegram."
                             "</p></div><p><a href='/'>Back to overview</a></p>"), 500))
                finally:
                    db.close()
        return self._send(*not_found())


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    # How many new connections may wait to be picked up. Python's default is
    # five: a class opening the site at the same moment was refused past the
    # fifth, which a browser shows as a page that will not load.
    request_queue_size = 128


def main():
    core.init_db()
    # A full volume does not announce itself: pages still read, and only
    # writing fails. Say it at startup, and clear the oldest backups if the
    # site is about to be unable to write at all.
    print("Disk:", core.make_room())
    if CFG["teacher_password"] == "changeme":
        print("!! Set a real teacher_password in config.json before sharing this URL.")
    port = CFG["port"]
    print(f"Dashboard: http://localhost:{port}")
    Server(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
