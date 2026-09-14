"""Turn one of the Claude-made booklets into a digital test.

The booklets share a shape: numbered exercises like "2.2 Complete with the
superlative.", each followed by its questions, and a matching answer key whose
lines read "2.2  1 'm living · 2 isn't · 3 send". The labels are what make this
possible - they join the two files together.

    python3 convert_booklet.py "BOOKLET.docx" "ANSWER KEY.docx" --out unit10.json

Only the exercises that can be marked by machine are taken: multiple choice,
true or false, and anything with one short answer per number. Discussion and
writing tasks are left for the teacher, which is where they belong.
"""
import argparse
import html
import json
import os
import re
import sys
import zipfile

LABEL = re.compile(r"^(\d+\.\d+)\s+(.*)$")
NUMBERED = re.compile(r"^(\d+)\s+(.*)$")
NEXT_LABEL = re.compile(r"\s\d+\.\d+\s")
OPTIONS = re.compile(r"\s([A-D])\s+(?=\S)")


def paragraphs(path):
    z = zipfile.ZipFile(os.path.expanduser(path))
    xml = z.read("word/document.xml").decode("utf-8", "replace")
    out = []
    for m in re.finditer(r"<w:p[ >].*?</w:p>", xml, re.S):
        t = "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", m.group(0), re.S))
        t = html.unescape(re.sub(r"<[^>]+>", "", t)).strip()
        if t:
            out.append(re.sub(r"\s+", " ", t))
    return out


def read_key(path):
    """label -> {question number: answer}"""
    keys = {}
    for line in paragraphs(path):
        m = LABEL.match(line)
        if not m:
            continue
        answers = {}
        for part in m.group(2).split("·"):
            n = NUMBERED.match(part.strip())
            if n:
                # a key line sometimes runs straight into the next exercise -
                # "lose. 1.8 1 para 5" - and without this the full stop and
                # everything after it became part of the answer
                answers[int(n.group(1))] = NEXT_LABEL.split(n.group(2))[0].strip()
        if answers:
            keys[m.group(1)] = answers
    return keys


def read_booklet(path):
    """label -> (instruction, {question number: text})"""
    lines = paragraphs(path)
    out, label, instruction, items = {}, None, "", {}
    for line in lines:
        m = LABEL.match(line)
        if m:
            if label and items:
                out[label] = (instruction, items)
            label, instruction, items = m.group(1), m.group(2), {}
            continue
        if not label:
            continue
        n = NUMBERED.match(line)
        if n and len(n.group(2)) > 2:
            items[int(n.group(1))] = n.group(2).strip()
    if label and items:
        out[label] = (instruction, items)
    return out


def split_options(text):
    """"Khmer has … A longer B the longest C the most long" -> stem + options."""
    marks = list(OPTIONS.finditer(" " + text))
    if len(marks) < 2:
        return text, []
    first = marks[0].start()
    stem = (" " + text)[:first].strip()
    opts = []
    for i, mk in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(" " + text)
        opts.append({"letter": mk.group(1),
                     "text": (" " + text)[mk.end():end].strip()})
    return stem, opts


def tidy_answer(want):
    """The key is written for a teacher, so it carries notes a student cannot type."""
    want = want.strip()
    # "Jin's grandmother (accept Jin)" -> both are right
    extra = re.search(r"\(accept ([^)]+)\)", want, re.I)
    want = re.sub(r"\s*\([^)]*\)", "", want).strip()
    if extra:
        want = want + "/" + extra.group(1).strip()
    return want.strip(" .·")


GAP = re.compile(r"[\u2026.]{3,}")


def typeable(want, why=False, prompt=""):
    """Could a student sitting at a keyboard produce exactly this?

    Everything here was found by marking a converted test with its own answer
    key and watching questions come back wrong. An answer the key itself
    cannot match is worse than no question: the student is right and the
    screen says otherwise.
    """
    if len(want) > 60 or "\u2026" in want or "\u00b7" in want:
        return "answer too long to mark" if why else False
    if want.endswith("?"):
        # the key holds the question the student was meant to write
        return "answer is a question to write" if why else False
    if want.startswith("\u2014") or " except " in want:
        return "answer is a note to the teacher" if why else False
    if len(want.split()) > 6:
        return "answer is a whole sentence" if why else False
    if "/" in want:
        parts = [p.strip() for p in want.split("/")]
        if any("," in p or len(p.split()) > 3 for p in parts):
            # "was / were, would definitely do" is two gaps, not two choices,
            # and the marker reads a slash as "either of these will do"
            return "two answers in one box" if why else False
        # The same slash means two different things. In "have/need" it offers
        # the student a choice; in "beat / won", against a sentence with two
        # gaps, it is the answer to each of them in turn. The prompt settles
        # it: two gaps, or a sentence that already shows the choices.
        if len(GAP.findall(prompt)) >= 2 or "/" in prompt:
            return "two answers in one box" if why else False
    return False if why else True


def build(booklet, key, title, level, number):
    questions, n = [], 0
    skipped = []
    for label in sorted(booklet, key=lambda s: [int(x) for x in s.split(".")]):
        instruction, items = booklet[label]
        answers = key.get(label)
        if not answers:
            skipped.append((label, instruction, "no answers"))
            continue
        for num in sorted(items):
            want = answers.get(num)
            if want is None:
                continue
            want = tidy_answer(want)
            stem, opts = split_options(items[num])
            n += 1
            prompt = stem if stem else items[num]
            # a prompt that is really the answer written out is no use as a question
            if "✗" in prompt or "→" in prompt:
                n -= 1
                skipped.append((label, instruction, "the prompt gives it away"))
                break
            q = {"num": n, "prompt": "%s  %s" % (label, prompt), "answer": want}
            if opts and any(o["letter"] == want.strip() for o in opts):
                q["kind"] = "mcq"
                q["options"] = opts
            elif want.strip() in ("T", "F", "True", "False"):
                q["kind"] = "yesno"
                q["options"] = [{"letter": "T", "text": "True"},
                                {"letter": "F", "text": "False"}]
                q["answer"] = want.strip()[0]
            elif re.fullmatch(r"[A-Za-z]{1,2}", want) and not opts:
                # a matching exercise: the answer is a code from a list the
                # student can see on paper and cannot be expected to type
                n -= 1
                skipped.append((label, instruction, "matching - needs its list"))
                break
            elif not typeable(want, prompt=prompt):
                # one unmarkable answer is not a reason to throw away the
                # other nine questions in the exercise - drop just this one
                n -= 1
                why = typeable(want, why=True, prompt=prompt)
                if (label, instruction, why) not in skipped:
                    skipped.append((label, instruction, why))
                continue
            else:
                q["kind"] = "typed"
                q["options"] = []
            questions.append(q)
    return {"level": level, "number": number, "title": title,
            "passages": {}, "questions": questions}, skipped


# The booklets are filed by level and named with a level letter - "E09AC",
# "I06.1", "P01BD" - so the level should not have to be typed in and got wrong
# on all thirty of them.
FOLDER_LEVELS = [
    ("pre-intermediate", "Pre-Intermediate"),
    ("intermediate", "Intermediate"),
    ("elementary", "Elementary"),
    ("beginner", "Beginner"),
]
PREFIX_LEVELS = {"E": "Elementary", "U": "Elementary", "I": "Intermediate",
                 "P": "Pre-Intermediate", "B": "Beginner"}


def guess_level(path):
    """The folder it sits in first, then the letter it starts with."""
    low = os.path.abspath(os.path.expanduser(path)).lower()
    for needle, level in FOLDER_LEVELS:
        if needle in low:
            return level
    first = os.path.basename(path)[:1].upper()
    return PREFIX_LEVELS.get(first)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("booklet")
    ap.add_argument("key")
    ap.add_argument("--title", default="")
    ap.add_argument("--level", default="",
                    help="normally worked out from the folder and the filename")
    ap.add_argument("--number", type=int, default=1)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    booklet = read_booklet(args.booklet)
    key = read_key(args.key)
    print("booklet: %d labelled exercises | key: %d" % (len(booklet), len(key)))
    title = args.title or os.path.basename(args.booklet).split("—")[0].strip()
    level = args.level or guess_level(args.booklet)
    if not level:
        sys.exit("Could not tell the level from the name or the folder - "
                 "pass --level \"Elementary\" (or Pre-Intermediate, "
                 "Intermediate, Beginner).")
    print("level: %s%s" % (level, "" if args.level else " (from the folder)"))
    data, skipped = build(booklet, key, title, level, args.number)
    kinds = {}
    for q in data["questions"]:
        kinds[q["kind"]] = kinds.get(q["kind"], 0) + 1
    print("made %d questions %s" % (len(data["questions"]), kinds))
    if skipped:
        print("left for you (%d):" % len(skipped))
        for label, instruction, why in skipped[:10]:
            print("   %-6s %-52s %s" % (label, instruction[:52], why))
    out = args.out or "booklet.json"
    json.dump(data, open(out, "w"), ensure_ascii=False)
    print("wrote", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
