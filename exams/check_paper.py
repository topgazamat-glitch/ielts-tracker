"""Check a mock paper before anybody sits it.

Two kinds of check. The first is structural: the right number of questions,
every answer a real option, no answer key that points at nothing. The second
is the level, which is the whole point of a mock - a paper that is easier or
harder than the real final tells the student nothing useful.

The bands come from measuring Azamat's own Test 1 and Test 2 finals:

    Part 3 article   180-200 words, 10-15 words a sentence, 6-9% long words
    Part 4 text       85-105 words, 11-18 words a sentence

"Long word" means eight letters or more, which at A2 is the rough line
between a word they have met and a word they have to work out.

    python3 exams/check_paper.py a2_mock_2
    python3 exams/check_paper.py --all
"""
import argparse
import importlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# measured from the real papers; see the module docstring
ART_WORDS = (170, 210)
ART_SENT = (9.0, 16.0)
ART_LONG = (5.0, 10.0)
TXT_WORDS = (80, 115)


def words(t):
    return re.findall(r"[A-Za-z][A-Za-z'-]*", t)


def measure(text):
    w = words(text)
    sents = [s for s in re.split(r"[.!?]+", text) if words(s)]
    per = sum(len(words(s)) for s in sents) / max(1, len(sents))
    long_pc = 100.0 * len([x for x in w if len(x) >= 8]) / max(1, len(w))
    return len(w), per, long_pc


def check(name):
    p = importlib.import_module(name)
    bad = []

    def want(cond, why):
        if not cond:
            bad.append(why)

    # ---- listening
    want(len(p.PART1) == 5, "Part 1 has %d conversations, not 5" % len(p.PART1))
    for c in p.PART1:
        want(len(c["options"]) == 3, "Q%s does not have three options" % c["q"])
        want(c["answer"] in "ABC", "Q%s answer is not A, B or C" % c["q"])
        want(bool(c["lines"]), "Q%s has no recording" % c["q"])
    want(len(p.PART2["people"]) == 5, "Part 2 does not have five people")
    want(len(p.PART2["options"]) == 8, "Part 2 does not have eight options")
    letters = {L for L, _ in p.PART2["options"]}
    for q, a in p.PART2["answers"].items():
        want(a in letters, "Part 2 answer %s for %s is not an option" % (a, q))
    want(len(set(p.PART2["answers"].values())) == 5,
         "Part 2 uses the same letter twice")
    want(len(p.PART3["questions"]) == 5, "Part 3 does not have five questions")
    for q in p.PART3["questions"]:
        want(len(q["options"]) == 3, "Q%s does not have three options" % q["q"])
        want(q["answer"] in "ABC", "Q%s answer is not A, B or C" % q["q"])
    want(len(p.PART4["gaps"]) == 5, "Part 4 does not have five gaps")
    for g in p.PART4["gaps"]:
        want(bool(str(g["answer"]).strip()), "Q%s has no answer" % g["q"])

    nums = ([c["q"] for c in p.PART1]
            + [int(q) for q, _ in p.PART2["people"]]
            + [q["q"] for q in p.PART3["questions"]]
            + [g["q"] for g in p.PART4["gaps"]])
    want(nums == list(range(1, 21)),
         "listening is not numbered 1-20: %s" % nums)

    # ---- reading
    want(len(p.R_PART1["notices"]) == 8, "Reading 1 does not have eight notices")
    want(len(p.R_PART1["items"]) == 5, "Reading 1 does not have five questions")
    nl = {L for L, _ in p.R_PART1["notices"]}
    for n, _t, a in p.R_PART1["items"]:
        want(a in nl, "Reading 1 Q%d answer %s is not a notice" % (n, a))
    want(len({a for _n, _t, a in p.R_PART1["items"]}) == 5,
         "Reading 1 uses the same notice twice")
    for n, _stem, opts, a in p.R_PART2["items"]:
        want(len(opts) == 3, "Reading 2 Q%d does not have three options" % n)
        want(a in "ABC", "Reading 2 Q%d answer is not A, B or C" % n)
    want(len(p.R_PART3["questions"]) == 5, "Reading 3 does not have five questions")
    for q in p.R_PART3["questions"]:
        want(len(q["options"]) == 3, "Reading 3 Q%s has not three options" % q["q"])
        want(q["answer"] in "ABC", "Reading 3 Q%s answer is not A, B or C" % q["q"])
    for n, opts, a in p.R_PART4["items"]:
        want(len(opts) == 3, "Reading 4 Q%d does not have three options" % n)
        want(a in "ABC", "Reading 4 Q%d answer is not A, B or C" % n)
    want(sorted(p.R_PART5["answers"]) == list(range(21, 26)),
         "Reading 5 is not numbered 21-25")
    for n, a in p.R_PART5["answers"].items():
        want(bool(str(a).strip()), "Reading 5 gap %d has no answer" % n)

    rnums = ([n for n, _t, _a in p.R_PART1["items"]]
             + [n for n, _s, _o, _a in p.R_PART2["items"]]
             + [q["q"] for q in p.R_PART3["questions"]]
             + [n for n, _o, _a in p.R_PART4["items"]]
             + sorted(p.R_PART5["answers"]))
    want(rnums == list(range(1, 26)),
         "reading is not numbered 1-25: %s" % rnums)

    want(len(p.WRITING["points"]) == 4, "the email does not ask for four things")

    # every gap in a text has a question, and every question a gap
    gaps4 = [int(m) for m in re.findall(r"(\d+)\s*…", p.R_PART4["text"])]
    want(gaps4 == [n for n, _o, _a in p.R_PART4["items"]],
         "Reading 4: the gaps in the text are %s but the questions are %s"
         % (gaps4, [n for n, _o, _a in p.R_PART4["items"]]))
    body = " ".join(b for _g, b, _s in p.R_PART5["letters"])
    gaps5 = [int(m) for m in re.findall(r"(\d+)\s*…", body)]
    want(sorted(gaps5) == sorted(p.R_PART5["answers"]),
         "Reading 5: the gaps in the letters are %s but the answers are %s"
         % (sorted(gaps5), sorted(p.R_PART5["answers"])))

    # ---- the level
    art = " ".join(p.R_PART3["text"])
    aw, asent, along = measure(art)
    tw, tsent, _tl = measure(re.sub(r"\d+\s*…+", "word", p.R_PART4["text"]))

    def band(v, lo, hi, what, fmt="%.1f"):
        ok = lo <= v <= hi
        print("   %-34s " % what + (fmt % v)
              + ("  ok" if ok else "  OUT OF BAND (%s-%s)" % (lo, hi)))
        if not ok:
            bad.append("%s is %s, outside %s-%s" % (what, fmt % v, lo, hi))

    print("%s" % name)
    band(aw, ART_WORDS[0], ART_WORDS[1], "Part 3 article, words", "%d")
    band(asent, ART_SENT[0], ART_SENT[1], "  words a sentence")
    band(along, ART_LONG[0], ART_LONG[1], "  long words, %")
    band(tw, TXT_WORDS[0], TXT_WORDS[1], "Part 4 text, words", "%d")

    for why in bad:
        print("   PROBLEM  " + why)
    print("   %d problem(s)\n" % len(bad))
    return len(bad)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("papers", nargs="*")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    names = a.papers
    if a.all or not names:
        names = ["a2_mock_final"] + ["a2_mock_%d" % n for n in range(2, 7)]
        names = [n for n in names if os.path.exists(os.path.join(HERE, n + ".py"))]
    total = sum(check(n) for n in names)
    print("%d paper(s), %d problem(s)" % (len(names), total))
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
