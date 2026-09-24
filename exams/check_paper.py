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
#
# The Competency papers (B1 for Pre-Intermediate, B1+ for Intermediate) are a
# different animal. Azamat's own B1+ final runs 368 words at 21.6 words a
# sentence with 13.9% long words in the Part 4 article, and its cloze is
# denser still. Those are the numbers the B1+ mocks have to meet.
C_LONG_WORDS = (300, 410)
C_LONG_SENT = (15.0, 23.5)
C_LONG_PC = (9.0, 15.5)
C_GAP_WORDS = (90, 150)

# The B1 mid-course paper is a different shape of difficulty again. Measured
# from the official Empower B1 Mid-Course Competency test: its YES/NO text is
# long (459 words) but plain - 15.3 words a sentence, 7% long words - and its
# article is short with markedly short sentences, 279 words at 10.7. Long and
# plain is not the same as short and dense, and a mid paper should be the
# first of those.
MID_LONG_WORDS = (380, 520)
MID_LONG_SENT = (12.5, 18.0)
MID_LONG_PC = (4.5, 10.5)
MID_ART_WORDS = (245, 330)
MID_ART_SENT = (9.0, 14.5)
MID_ART_PC = (5.5, 11.5)
MID_GAP_WORDS = (75, 120)

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


def competency(name, p):
    """A B1 or B1+ Reading and Writing paper: YES/NO, a cloze, two emails.

    B1+ offers four options a question and B1 three, which is the difference
    between the two levels rather than a mistake in either.
    """
    plus = name.startswith("b1plus")
    n_opt = 4 if plus else 3
    letters = "ABCD" if plus else "ABC"
    bad = []

    def want(cond, why):
        if not cond:
            bad.append(why)

    want(len(p.R_PART1["questions"]) == 5, "Part 1 does not have five texts")
    for q in p.R_PART1["questions"]:
        want(len(q["options"]) == n_opt,
             "Q%s does not have %d options" % (q["q"], n_opt))
        want(q["answer"] in letters, "Q%s answer is out of range" % q["q"])
        want(bool(q["text"].strip()), "Q%s has no text to read" % q["q"])
    want(len(p.R_PART2["statements"]) == 5, "Part 2 does not have five sentences")
    for it in p.R_PART2["statements"]:
        want(it["answer"] in ("YES", "NO"), "Q%s is not YES or NO" % it["q"])
    want(len({it["answer"] for it in p.R_PART2["statements"]}) == 2,
         "Part 2 is all YES or all NO")
    want(len(p.R_PART3["questions"]) == 5, "Part 3 does not have five questions")
    for q in p.R_PART3["questions"]:
        want(len(q["options"]) == n_opt,
             "Q%s does not have %d options" % (q["q"], n_opt))
        want(q["answer"] in letters, "Q%s answer is out of range" % q["q"])
    want(len(p.R_PART4["gaps"]) == 5, "Part 4 does not have five gaps")
    for g in p.R_PART4["gaps"]:
        want(len(g["options"]) == n_opt,
             "Q%s does not have %d options" % (g["q"], n_opt))
        want(g["answer"] in letters, "Q%s answer is out of range" % g["q"])
    want(len(p.R_PART5["gaps"]) == 5, "Part 5 does not have five gaps")
    for g in p.R_PART5["gaps"]:
        want(bool(str(g["answer"]).strip()), "Q%s has no answer" % g["q"])

    nums = ([q["q"] for q in p.R_PART1["questions"]]
            + [it["q"] for it in p.R_PART2["statements"]]
            + [q["q"] for q in p.R_PART3["questions"]]
            + [g["q"] for g in p.R_PART4["gaps"]]
            + [g["q"] for g in p.R_PART5["gaps"]])
    want(nums == list(range(1, 26)), "reading is not numbered 1-25: %s" % nums)

    for part, text in ((4, p.R_PART4["text"]), (5, p.R_PART5["text"])):
        seen = [int(m) for m in re.findall(r"\((\d+)\)\s*\.", text)]
        asked = [g["q"] for g in (p.R_PART4 if part == 4 else p.R_PART5)["gaps"]]
        want(seen == asked,
             "Part %d: gaps in the text are %s but the questions are %s"
             % (part, seen, asked))

    want(len(p.WRITING1["points"]) == 3, "the first email does not ask three things")
    want(bool(p.WRITING2.get("quote")), "the second task has nothing to reply to")
    return bad


def check(name):
    p = importlib.import_module(name)
    if hasattr(p, "WRITING2"):      # the Competency shape, B1 and B1+
        print("%s" % name)
        bad = competency(name, p)
        mid = name.startswith("b1mid")
        for label, text, band in (
                ("Part 2 text", " ".join(p.R_PART2["text"]), "long"),
                ("Part 3 article", " ".join(p.R_PART3["text"]), "article"),
                ("Part 4 gapped text",
                 re.sub(r"\(\d+\)\s*\.+", "word", p.R_PART4["text"]), "gap"),
                ("Part 5 cloze",
                 re.sub(r"\(\d+\)\s*\.+", "word", p.R_PART5["text"]), "gap")):
            w, per, pc = measure(text)
            if band == "gap":
                checks = ((w, MID_GAP_WORDS if mid else C_GAP_WORDS,
                           "words", "%d"),)
            elif mid and band == "long":
                checks = ((w, MID_LONG_WORDS, "words", "%d"),
                          (per, MID_LONG_SENT, "words a sentence", "%.1f"),
                          (pc, MID_LONG_PC, "long words, %", "%.1f"))
            elif mid:
                checks = ((w, MID_ART_WORDS, "words", "%d"),
                          (per, MID_ART_SENT, "words a sentence", "%.1f"),
                          (pc, MID_ART_PC, "long words, %", "%.1f"))
            else:
                checks = ((w, C_LONG_WORDS, "words", "%d"),
                          (per, C_LONG_SENT, "words a sentence", "%.1f"),
                          (pc, C_LONG_PC, "long words, %", "%.1f"))
            judge = name.startswith("b1plus") or name.startswith("b1mid")
            for val, (lo, hi), what, fmt in checks:
                ok = (lo <= val <= hi) if judge else True
                print("   %-34s " % ("%s, %s" % (label, what)) + (fmt % val)
                      + ("  ok" if ok else "  OUT OF BAND (%s-%s)" % (lo, hi))
                      + ("" if judge else "   (B1: measured, not judged)"))
                if not ok:
                    bad.append("%s %s is %s, outside %s-%s"
                               % (label, what, fmt % val, lo, hi))
        for why in bad:
            print("   PROBLEM  " + why)
        print("   %d problem(s)\n" % len(bad))
        return len(bad)
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
        names = (["a2_mock_final"] + ["a2_mock_%d" % n for n in range(2, 7)]
                 + ["b1plus_mock_final"]
                 + ["b1plus_mock_%d" % n for n in range(2, 7)]
                 + ["b1mid_%d" % n for n in range(1, 6)])
        names = [n for n in names if os.path.exists(os.path.join(HERE, n + ".py"))]
    total = sum(check(n) for n in names)
    print("%d paper(s), %d problem(s)" % (len(names), total))
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
