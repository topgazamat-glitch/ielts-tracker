"""Check a batch of Play lists, then put them on the site.

Checked before anything is sent, because a bad list is seen by students
before it is seen by anybody else:
  - the site's parser splits on " = " and " | ", so neither may appear inside
    a question or an answer;
  - a multiple-choice question needs four different options;
  - a vocabulary list must not give two words the same meaning, because the
    game builds the wrong answers out of the other meanings on the list, and
    two the same makes a question with no right answer;
  - Elementary has not met the past simple before Unit 6, so an early unit
    that uses it is a mistake, not a challenge.

    python3 handouts/empower_upload.py empower_e_2_4            (check only)
    python3 handouts/empower_upload.py empower_e_2_4 --upload
"""
import collections
import importlib
import os
import re
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

SITE = "https://ielts-tracker-production.up.railway.app"
BOOK = "Empower Elementary"
LEVEL_NAME = "Elementary"
PAST = re.compile(r"\b(was|were|didn't|did you|went|bought|ate|saw)\b", re.I)


def lines_of(kind, items):
    if kind == "vocab":
        return "\n".join("%s = %s" % (a, b) for a, b in items)
    return "\n".join("%s = %s | %s | %s | %s" % it for it in items)


def check(mod, allow_past_from=6):
    problems = []
    for title, kind, step, items in mod.LISTS:
        unit = int(re.search(r"Unit (\d+)", title).group(1))
        if kind == "vocab":
            meanings = [b for _a, b in items]
            for m, c in collections.Counter(meanings).items():
                if c > 1:
                    problems.append((title, "two words share the meaning %r" % m))
            for a, b in items:
                if "=" in a + b or "|" in a + b:
                    problems.append((title, "separator inside %r" % a))
        else:
            for it in items:
                if len(it) != 5:
                    problems.append((title, "not four options: %r" % (it[0],)))
                    continue
                q, opts = it[0], list(it[1:])
                if len(set(opts)) != 4:
                    problems.append((title, "a repeated option: %r" % q))
                if "=" in q or "|" in q or any("=" in o or "|" in o for o in opts):
                    problems.append((title, "separator inside %r" % q))
                if unit < allow_past_from and PAST.search(q):
                    problems.append((title, "past simple too early: %r" % q))
        if len(items) != 25:
            problems.append((title, "%d questions, expected 25" % len(items)))
    return problems


def main():
    name = sys.argv[1]
    mod = importlib.import_module(name)
    problems = check(mod)
    for title, why in problems:
        print("PROBLEM  %-46s %s" % (title[:46], why))
    print("%d lists, %d questions, %d problems"
          % (len(mod.LISTS), sum(len(i) for _t, _k, _s, i in mod.LISTS), len(problems)))
    if problems or "--upload" not in sys.argv:
        return 1 if problems else 0

    import html
    import upload_booklets as ub
    op = ub.sign_in(SITE, os.environ["TEACHER_PASSWORD"])
    index = html.unescape(op.open(SITE + "/vocab", timeout=60).read().decode())
    level = dict((m[1], m[0]) for m in re.findall(
        r'<option value="(\d+)">([^<]+)</option>', index))[LEVEL_NAME]
    for title, kind, step, items in mod.LISTS:
        if title in index:
            print("already there:", title[:60]); continue
        form = {"title": title, "source": BOOK, "unit": str(step),
                "group_id": "", "words": lines_of(kind, items)}
        if kind == "grammar":
            form["kind"] = "grammar"
        r = op.open(SITE + "/vocab/new", urllib.parse.urlencode(form).encode(),
                    timeout=180)
        wid = int(r.geturl().rsplit("/", 1)[1])
        op.open(SITE + "/vocab/%d/rename" % wid, urllib.parse.urlencode(
            {"title": title, "group_id": "", "level_id": level,
             "source": BOOK, "step": str(step)}).encode(), timeout=60)
        page = op.open(SITE + "/vocab/%d" % wid, timeout=60).read().decode()
        print("%-60s -> /vocab/%-4d %d questions"
              % (title[:60], wid, len(re.findall(r"<tr><td>", page))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
