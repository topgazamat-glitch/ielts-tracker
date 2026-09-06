"""Read a 4000 Essential English Words book and file it as word lists.

    python3 import_words.py "essential words 1.pdf" --book 1
    python3 import_words.py "essential words 1.pdf" --book 1 --upload \
        --site https://... --password ...

Each unit in the book opens with a page of headwords: the word, its phonetics,
its part of speech, a one-line definition and an example. The phonetics come
through the PDF badly mangled and are thrown away; the rest is exactly what a
vocabulary list needs.
"""
import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pdftext

POSLINE = re.compile(r"\b(n|v|adj|adv|prep|conj|pron)\.\s*$")
TOKEN = re.compile(r"[A-Za-z][A-Za-z\-]{2,22}")
EXAMPLE = re.compile(r"^[\-—–*■»♦►•\s]*[»►\-—–*]\s*(.+)$")
NOISE = re.compile(r"[^A-Za-z\-]")


def clean(text):
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"^[^A-Za-z\"'(]+", "", text)      # bullets and stray marks
    return text.strip(" .,-")


def stem(word):
    return word[:max(4, len(word) - 3)].lower()


def headword(line, definition):
    """Which word on this line is the entry actually about?

    The bullet before a headword comes through as r, c, * v r and other
    rubbish, and the phonetics beside it are mangled, so the line cannot be
    read positionally. What is reliable is that the definition explains the
    word - so the headword is the token on the line that the next line is
    about.
    """
    low = definition.lower()
    best = ""
    for token in TOKEN.findall(line):
        if token.lower() in ("adj", "adv", "prep", "conj", "pron"):
            continue
        if stem(token) in low and len(token) > len(best):
            best = token
    return best.lower()


def read_book(path):
    """Yield (page number, [entries]) for every page that is a word list."""
    for num, lines in pdftext.extract(path):
        entries, i = [], 0
        while i < len(lines):
            line = lines[i].strip()
            m = POSLINE.search(line)
            if not m or i + 1 >= len(lines):
                i += 1
                continue
            definition = clean(lines[i + 1])
            word = headword(line, definition) if len(definition) > 12 else ""
            if not word:
                i += 1
                continue
            example = ""
            if i + 2 < len(lines):
                em = EXAMPLE.match(lines[i + 2].strip())
                if em:
                    example = clean(em.group(1))
            entries.append({"term": word, "pos": m.group(1),
                            "definition": definition, "example": example})
            i += 2
        if len(entries) >= 5:
            yield num, entries


def units(path):
    """Group the word pages into units.

    The book is entirely regular: each unit's words run across two facing
    pages, then five pages of exercises before the next unit begins. So a page
    that directly follows another word page belongs to the same unit.
    """
    out, last = [], None
    for num, entries in read_book(path):
        if last is not None and num == last + 1 and out:
            out[-1].extend(entries)
        else:
            out.append(list(entries))
        last = num
    return out


def post(opener, base, path, fields):
    data = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(base + path, data=data)
    return opener.open(req, timeout=60).read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--book", default="1")
    ap.add_argument("--group", default="", help="class id, or blank for every class")
    ap.add_argument("--site")
    ap.add_argument("--password")
    ap.add_argument("--upload", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    found = units(args.pdf)
    if args.limit:
        found = found[:args.limit]
    total = sum(len(u) for u in found)
    print("%d units, %d words" % (len(found), total))
    for i, unit in enumerate(found[:3], 1):
        print("  Unit %d (%d): %s" % (i, len(unit),
                                      ", ".join(w["term"] for w in unit[:6])))
    if not args.upload:
        print("\nNothing sent. Re-run with --upload once the table looks right.")
        return

    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor())
    post(opener, args.site, "/login", {"password": args.password})
    sent = 0
    for i, unit in enumerate(found, 1):
        title = "Essential Words %s · Unit %d" % (args.book, i)
        body = "\n".join(
            "%s = %s%s" % (w["term"], w["definition"],
                           " | " + w["example"] if w["example"] else "")
            for w in unit)
        post(opener, args.site, "/vocab/new",
             {"title": title, "source": "4000 Essential Words %s" % args.book,
              "unit": str(i), "group_id": args.group, "words": body})
        sent += len(unit)
        if i % 5 == 0 or i == len(found):
            print("  %d/%d units uploaded" % (i, len(found)))
    print("Done: %d words in %d lists." % (sent, len(found)))


if __name__ == "__main__":
    main()
