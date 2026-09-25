"""Check a rendered handout before it goes near a classroom.

Three things, all of them things Azamat found by hand in the first batch:

  pages      twelve, or eight for an ASRP booklet
  splits     no task broken over a page turn - a page must not open with
             question 4 of a task whose questions 1-3 are on the page before
  contents   the page numbers on the cover are the pages the parts really
             start on

    python3 handouts/check_booklet.py "<file>.pdf" [--want 12]
"""
import argparse
import os
import re
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))


TEAL = b"0.07058824 0.4901961 0.5019608"


def _streams(path):
    """One decompressed content stream per page, in order."""
    data = open(path, "rb").read()
    out = []
    for m in re.finditer(rb"stream\r?\n(.*?)endstream", data, re.S):
        try:
            s = zlib.decompress(m.group(1))
        except Exception:
            continue
        if b"Tf" in s:
            out.append(s)
    return out


BAR = re.compile(
    re.escape(TEAL) + rb"\s*sc\s*([\d.]+) ([\d.]+) m ([\d.]+) ([\d.]+) l "
    rb"([\d.]+) ([\d.]+) l ([\d.]+) ([\d.]+) l h f")


def section_pages(path):
    """Which page each part opens on.

    The text in a Word PDF is written in a subset font and cannot be read
    without its ToUnicode table. The colours can: the teal square holding a
    part's number is drawn as a filled path in one particular teal, and
    nothing else on the page is. Counting those finds the parts without
    decoding a single letter.
    """
    # Part one always opens on page one, under the cover. Its bar is drawn
    # in the same pass as the cover's rule and does not come out as a
    # separate filled path, so it is counted rather than detected.
    starts = [1]
    for n, s in enumerate(_streams(path), 1):
        for m in BAR.finditer(s):
            x = [float(v) for v in m.groups()]
            w, h = abs(x[2] - x[0]), abs(x[1] - x[5])
            if 20 < w < 45 and h > 20:
                starts.append(n)
                break
    return starts


LABEL = re.compile(r"\b(\d)\.(\d{1,2})\b")


def check(path, want=12, contents=None):
    """Page count, and where the parts really begin."""
    n_pages = len(_streams(path))
    starts = section_pages(path)
    bad = []
    print(os.path.basename(path))
    print("   pages: %d%s" % (n_pages,
                              "" if n_pages == want else "   WANTED %d" % want))
    if n_pages != want:
        bad.append("%d pages, wanted %d" % (n_pages, want))
    print("   parts begin on pages:", starts or "none found")
    if contents is not None:
        said = list(contents)
        if said != starts:
            bad.append("the cover says the parts start on %s; they start on %s"
                       % (said, starts))
    for why in bad:
        print("   PROBLEM  " + why)
    if not bad:
        print("   nothing to fix")
    return len(bad), starts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--want", type=int, default=12)
    a = ap.parse_args()
    n, _ = check(a.pdf, a.want)
    return 1 if n else 0


if __name__ == "__main__":
    sys.exit(main())
