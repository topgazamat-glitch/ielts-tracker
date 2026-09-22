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
BOOKS = {"exam": "A2 Key exam words"}          # a batch of exam words is its own book
# a batch can say which book and level it belongs to, in the module itself

LEVEL_NAME = "Elementary"
PAST = re.compile(r"\b(was|were|didn't|did you|went|bought|ate|saw)\b", re.I)


PAIRS = ("vocab", "exam")      # a word and its meaning, not four options


def lines_of(kind, items):
    if kind in PAIRS:
        return "\n".join("%s = %s" % (a, b) for a, b in items)
    return "\n".join("%s = %s | %s | %s | %s" % it for it in items)


def check(mod, allow_past_from=6):
    problems = []
    for title, kind, step, items in mod.LISTS:
        m = re.search(r"Unit (\d+)", title)
        unit = int(m.group(1)) if m else 99      # exam words follow no unit order
        if kind in PAIRS:
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
    problems = check(mod, allow_past_from=getattr(mod, "PAST_FROM", 6))
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
        r'<option value="(\d+)">([^<]+)</option>', index))[
            getattr(mod, "LEVEL", LEVEL_NAME)]
    for title, kind, step, items in mod.LISTS:
        if title in index:
            print("already there:", title[:60]); continue
        book = getattr(mod, "BOOK", None) or BOOKS.get(kind, BOOK)
        form = {"title": title, "source": book, "unit": str(step),
                "group_id": "", "words": lines_of(kind, items)}
        form["kind"] = kind
        r = op.open(SITE + "/vocab/new", urllib.parse.urlencode(form).encode(),
                    timeout=180)
        wid = int(r.geturl().rsplit("/", 1)[1])
        op.open(SITE + "/vocab/%d/rename" % wid, urllib.parse.urlencode(
            {"title": title, "group_id": "", "level_id": level,
             "source": book, "step": str(step)}).encode(), timeout=60)
        page = op.open(SITE + "/vocab/%d" % wid, timeout=60).read().decode()
        print("%-60s -> /vocab/%-4d %d questions"
              % (title[:60], wid, len(re.findall(r"<tr><td>", page))))
    return 0





def replace_by_title(mod_name, id_from, id_to):
    """Swap the contents of lists found by their title, whatever id they hold."""
    import html
    import upload_booklets as ub
    mod = importlib.import_module(mod_name)
    op = ub.sign_in(SITE, os.environ["TEACHER_PASSWORD"])
    where = {}
    for wid in range(id_from, id_to + 1):
        try:
            page = html.unescape(op.open(SITE + "/vocab/%d" % wid, timeout=60).read().decode())
        except Exception:
            continue
        m = re.search(r"<h1>(.*?)</h1>", page, re.S)
        if m:
            where[m.group(1).strip()] = wid
    for title, kind, step, items in mod.LISTS:
        wid = where.get(title.strip())
        if not wid:
            print("NOT FOUND on the site:", title[:56]); continue
        op.open(SITE + "/vocab/%d/replace" % wid,
                urllib.parse.urlencode({"words": lines_of(kind, items)}).encode(),
                timeout=180)
        after = op.open(SITE + "/vocab/%d" % wid, timeout=60).read().decode()
        print("/vocab/%-4d %-52s %d questions"
              % (wid, title[:52], len(re.findall(r"<tr><td>", after))))


def replace_existing(pairs):
    """Swap the contents of lists that are already on the site.

    The site keeps a list and its students' progress and changes only the
    words, so a student who has already passed a step does not lose it.
    """
    import html
    import upload_booklets as ub
    mod_name, first_id = pairs
    mod = importlib.import_module(mod_name)
    op = ub.sign_in(SITE, os.environ["TEACHER_PASSWORD"])
    for i, (title, kind, step, items) in enumerate(mod.LISTS):
        wid = first_id + i
        page = html.unescape(op.open(SITE + "/vocab/%d" % wid, timeout=60).read().decode())
        there = re.search(r"<h1>(.*?)</h1>", page, re.S).group(1)
        if there.strip() != title.strip():
            print("SKIPPED /vocab/%d: it holds %r, not %r" % (wid, there[:40], title[:40]))
            continue
        op.open(SITE + "/vocab/%d/replace" % wid,
                urllib.parse.urlencode({"words": lines_of(kind, items)}).encode(),
                timeout=180)
        after = op.open(SITE + "/vocab/%d" % wid, timeout=60).read().decode()
        print("/vocab/%d %-46s %d questions" % (wid, title[:46],
                                                len(re.findall(r"<tr><td>", after))))


if __name__ == "__main__":
    if "--retitle" in sys.argv:
        i = sys.argv.index("--retitle")
        replace_by_title(sys.argv[1], int(sys.argv[i + 1]), int(sys.argv[i + 2]))
        sys.exit(0)
    if "--replace" in sys.argv:
        replace_existing((sys.argv[1], int(sys.argv[sys.argv.index("--replace") + 1])))
        sys.exit(0)
    sys.exit(main())
