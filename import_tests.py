"""Turn one test in a practice-book Word file into a digital test.

    python3 import_tests.py "~/Downloads/full book 1.docx" --test 1 --out test1.json

Reads the Reading section, which is the part that can be marked by machine, and
writes it as json for the Tests page to load. The answer key is not in the book,
so every question comes out with answer null and has to be filled in on the
review page before students can sit it.
"""
import argparse
import html
import json
import os
import re
import sys
import zipfile


def paragraphs(path):
    z = zipfile.ZipFile(path)
    xml = z.read("word/document.xml").decode("utf-8", "replace")
    out = []
    for m in re.finditer(r"<w:p[ >].*?</w:p>", xml, re.S):
        t = "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", m.group(0), re.S))
        out.append(html.unescape(re.sub(r"<[^>]+>", "", t)).strip())
    return out


def section(paras, test, name, nxt):
    a = next((i for i, t in enumerate(paras)
              if re.match(r"(?i)^test\s*%d\s+%s\b" % (test, name), t)), None)
    b = next((i for i, t in enumerate(paras)
              if i > (a or 0) and re.match(r"(?i)^test\s*%d\s+%s\b" % (test, nxt), t)), None)
    if a is None or b is None:
        return []
    return [t for t in paras[a:b] if t]


def truefalse(seg):
    """Questions 11-15: five statements marked YES or NO."""
    i = next((k for k, t in enumerate(seg) if "mark YES" in t), None)
    if i is None:
        return []
    out, n = [], 11
    for t in seg[i + 1:]:
        if re.match(r"(?i)^part\b", t) or re.match(r"^\d+\s", t):
            break
        if len(t) < 15:
            continue
        out.append({"num": n, "kind": "yesno", "prompt": t,
                    "options": [{"letter": "A", "text": "YES"},
                                {"letter": "B", "text": "NO"}], "answer": None})
        n += 1
        if n > 15:
            break
    return out


def numbered_mcq(seg, first, last):
    """Questions like `16 What is ...` followed by four option lines."""
    out = []
    for n in range(first, last + 1):
        i = next((k for k, t in enumerate(seg) if re.match(r"^%d\s+\S" % n, t)), None)
        if i is None:
            continue
        stem = re.sub(r"^%d\s+" % n, "", seg[i]).strip()
        opts = []
        for t in seg[i + 1:i + 9]:
            if re.match(r"^\d+\s+\S", t) or re.match(r"(?i)^part\b", t):
                break
            if len(t) < 2:
                continue
            opts.append(t)
            if len(opts) == 4:
                break
        if len(opts) != 4:
            continue
        out.append({"num": n, "kind": "mcq", "prompt": stem,
                    "options": [{"letter": "ABCD"[k], "text": o}
                                for k, o in enumerate(opts)], "answer": None})
    return out


def gapfill(seg):
    """Questions 21-25: a text with gaps, then lettered options for each."""
    i = next((k for k, t in enumerate(seg) if "choose the correct answer for each gap" in t), None)
    if i is None:
        return [], ""
    passage = []
    j = i + 1
    while j < len(seg) and not re.match(r"^\d+$", seg[j]):
        passage.append(seg[j])
        j += 1
    out = []
    while j < len(seg):
        m = re.match(r"^(\d+)$", seg[j])
        if not m:
            break
        n = int(m.group(1))
        opts = []
        j += 1
        while j < len(seg) and re.match(r"^[ABCD]\s+\S", seg[j]):
            opts.append({"letter": seg[j][0], "text": seg[j][1:].strip()})
            j += 1
        if opts:
            out.append({"num": n, "kind": "gap", "prompt": "Gap %d" % n,
                        "options": opts, "answer": None})
    return out, "\n\n".join(passage)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("book")
    ap.add_argument("--test", type=int, required=True)
    ap.add_argument("--level", default="Pre-Intermediate")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    paras = paragraphs(os.path.expanduser(args.book))
    seg = section(paras, args.test, "Reading", "Writing")
    if not seg:
        print("Could not find Test %d Reading in that file." % args.test)
        return 1

    questions = []
    questions += truefalse(seg)
    questions += numbered_mcq(seg, 16, 20)
    gaps, passage = gapfill(seg)
    questions += gaps

    # the passage each part refers to, kept for the ones that have one
    part4 = [t for t in seg if len(t) > 300]
    data = {
        "level": args.level,
        "number": args.test,
        "title": "Practice Test %d — Reading" % args.test,
        "source": os.path.basename(args.book),
        "passages": {"gap": passage, "long": part4[:1]},
        "questions": questions,
    }
    out = args.out or "test%02d.json" % args.test
    json.dump(data, open(out, "w"), indent=1, ensure_ascii=False)
    kinds = {}
    for q in questions:
        kinds[q["kind"]] = kinds.get(q["kind"], 0) + 1
    print("Test %d Reading -> %s" % (args.test, out))
    print("   %d questions  %s" % (len(questions), kinds))
    print("   every answer is null until the key is filled in on the Tests page")
    return 0


if __name__ == "__main__":
    sys.exit(main())
