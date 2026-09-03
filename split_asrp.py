"""Split an Empower Academic Skills / Reading Plus book into one PDF per lesson.

    python3 split_asrp.py "~/Downloads/intermediate ASRP.pdf" --out "~/Downloads/ASRP intermediate"

Finds where each lesson starts by reading the page headers, then writes
"Unit 3 Academic Skills.pdf" and "Unit 3 Reading Plus.pdf" into a folder per
unit. Pages are copied object for object, so quality is untouched.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pdfsplit

ACADEMIC = re.compile(r"Academic\s*Skills", re.I)
READING = re.compile(r"Reading\s*Plus", re.I)
UNIT = re.compile(r"Unit\s*(\d{1,2})\b", re.I)


def page_text(doc, page):
    contents = doc.get(page.get("Contents"))
    chunks = []
    if isinstance(contents, list):
        for c in contents:
            s = doc.get(c)
            if isinstance(s, pdfsplit.Stream):
                chunks.append(s.data())
    elif isinstance(contents, pdfsplit.Stream):
        chunks.append(contents.data())
    raw = b"\n".join(chunks)
    out = []
    for m in re.finditer(rb"\((?:\\.|[^\\()])*\)", raw):
        out.append(m.group(0)[1:-1].decode("latin-1"))
    return re.sub(r"\s+", " ", " ".join(out))


def find_lessons(doc):
    """[(kind, unit, first_page, last_page)] with pages 0-based."""
    pages = doc.pages()
    texts = [page_text(doc, p) for p in pages]
    starts = []
    for i, text in enumerate(texts):
        if ACADEMIC.search(text):
            starts.append((i, "Academic Skills"))
        elif READING.search(text):
            starts.append((i, "Reading Plus"))
    lessons = []
    seen = {"Academic Skills": 0, "Reading Plus": 0}
    for n, (start, kind) in enumerate(starts):
        end = (starts[n + 1][0] - 1) if n + 1 < len(starts) else len(pages) - 1
        seen[kind] += 1
        unit = None
        for i in range(start, end + 1):
            m = UNIT.search(texts[i])
            if m and 1 <= int(m.group(1)) <= 12:
                unit = int(m.group(1))
                break
        lessons.append((kind, unit or seen[kind], start, end))
    return lessons


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--out", required=True)
    ap.add_argument("--write", action="store_true", help="actually write the files")
    args = ap.parse_args()

    src = os.path.expanduser(args.pdf)
    out_root = os.path.expanduser(args.out)
    doc = pdfsplit.Document(src)
    lessons = find_lessons(doc)

    print("%-16s %-5s %-9s %s" % ("LESSON", "UNIT", "PAGES", "FILE"))
    for kind, unit, start, end in lessons:
        name = "Unit %d %s.pdf" % (unit, kind)
        print("%-16s %-5d %-9s %s" % (kind, unit, "%d-%d" % (start + 1, end + 1), name))
    print()
    print("%d lesson(s) from %d pages" % (lessons and len(lessons) or 0, len(doc.pages())))
    if not args.write:
        print("Nothing written. Add --write when the table looks right.")
        return 0

    total = 0
    for kind, unit, start, end in lessons:
        folder = os.path.join(out_root, "Unit %d" % unit)
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, "Unit %d %s.pdf" % (unit, kind))
        size = pdfsplit.write_pages(doc, list(range(start, end + 1)), path)
        total += size
        print("  %-34s %5.0f KB" % (os.path.basename(path), size / 1024))
    print("Done: %d file(s), %.1f MB in %s" % (len(lessons), total / 1024 / 1024, out_root))
    return 0


if __name__ == "__main__":
    sys.exit(main())
