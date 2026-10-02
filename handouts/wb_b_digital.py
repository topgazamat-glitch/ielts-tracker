"""Empower Beginner (A1 Starter) Workbook, lesson 4B - done on a phone.

The Beginner workbook on Azamat's Mac (Desktop / Empower Second Edition -
Books / 1. A1 Starter) is a scan, so its page is written out again by hand
from the page image - page 23, 4B "She has a sister and a brother" - in the
booklet's markup, as wb_pi_digital.py does for the Pre-Intermediate
workbook: four parts, each checked, then the next, and each exercise keeps
the book's number and letter (1a, 1b, 2a ...). The answers are the book's key
(page 89); the examples the book fills in are shown filled in.

The family tree is a drawing, which a page of text cannot show, so it is
told in three sentences - who is married to whom, and whose children are
whose - which is all the eight sentences of 3a ask about.

The recording for 4a is the workbook's own track 04.02, on the shelf
"Beginner Workbook" (the class audio numbers its tracks the same way). It is
not on the Mac yet; until it is, the page has no Listen button and the
Uzbek line says to say the words aloud - the answer is in the sound of th.

Beginner lessons come one at a time, not in pairs, so a homework line
"Workbook unit 4B" (or "4 B") names this one; core.workbook_test reads it.

Every instruction has a line in Uzbek under it, as in the Beginner handouts.

    python3 handouts/wb_b_digital.py       # writes handouts/wb_b_04b.json
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import Q, choose, report                                             # noqa: E402
from dest_b1_digital import md, bar, ex, box, item, para, word_box, cover, handout, panel  # noqa: E402
from wb_pi_digital import example, done, listen                                   # noqa: E402


def either(*forms):
    return "/".join(forms)


def words(n):
    return either(n, n.replace("-", " ")) if "-" in n else n


def unit4b():
    h, P, K = handout(), [], {}
    P.append(cover("WORKBOOK  ·  BEGINNER  ·  UNIT 4", "My life and my family",
                   "4B She has a sister and a brother",
                   ["*he / she / it* dan keyin feʼlga *-s* qoʻshishni: *works, lives, has*",
                    "*teaches, studies, goes* kabi shakllarni toʻgʻri yozishni",
                    "sonlarni 21 dan 100 gacha soʻz bilan yozishni",
                    "oila aʼzolarini bildiruvchi soʻzlarni: *son, daughter, wife, parents*",
                    "*th* ning /ð/ tovushini eshitishni: *that, mother, they*"]))

    # ------------------------------------------------ 1 grammar
    P.append(bar(1, "4B Grammar", "present simple: he / she / it positive"))
    P.append(ex("1.1", "**1a**  Choose the correct words."))
    P.append(example(1, "Pablo %s an international family." % done("has")))
    for n, (text, opts, a) in enumerate([
            ("My dad {} at the university.", ["teachs", "teaches"], "teaches"),
            ("Julie {} in a big house.", ["lives", "livs"], "lives"),
            ("Sandro {} in an office.", ["works", "workes"], "works"),
            ("My brother {} maths.", ["studys", "studies"], "studies"),
            ("Camila {} the guitar.", ["plays", "playes"], "plays"),
            ("Ryan {} Chinese.", ["speakes", "speaks"], "speaks"),
            ("My mum {} to the gym every day.", ["goes", "gos"], "goes")], 2):
        P.append(item(h, "1.1", n, text, box("1.1", n)))
        K[("1.1", n, 1)] = choose(opts, a)

    P.append(ex("1.2", "**1b**  Complete the sentences with the correct form of the verbs in brackets."))
    P.append(example(1, "Dean %s tennis and football. (like)" % done("likes")))
    for n, (text, a) in enumerate([
            ("My sister {} to the cinema every weekend. (go)", "goes"),
            ("Jack {} Italian at university. (study)", "studies"),
            ("Mandy {} a sister and two brothers. (have)", "has"),
            ("My brother {} cola every day. (drink)", "drinks"),
            ("My mum {} young children. (teach)", "teaches"),
            ("Enrique {} at home. (work)", "works"),
            ("My friend Sonya {} in Berlin. (live)", "lives")], 2):
        P.append(item(h, "1.2", n, text, box("1.2", n)))
        K[("1.2", n, 1)] = Q(a)

    # ------------------------------------------------ 2 numbers
    P.append(bar(2, "4B Vocabulary", "numbers 2"))
    P.append(ex("2.1", "**2a**  Write the numbers in words."))
    P.append(example(1, "51  →  %s" % done("fifty-one")))
    for n, (num, a) in enumerate([(27, "twenty-seven"), (45, "forty-five"), (89, "eighty-nine"),
                                  (34, "thirty-four"), (98, "ninety-eight"), (66, "sixty-six"),
                                  (100, either("a hundred", "one hundred", "hundred")),
                                  (72, "seventy-two")], 2):
        P.append(item(h, "2.1", n, "%d  →  {}" % num, box("2.1", n, "200px", "in words")))
        K[("2.1", n, 1)] = Q(words(a))

    # ------------------------------------------------ 3 family
    P.append(bar(3, "4B Vocabulary", "family and people"))
    P.append(ex("3.1", "**3a**  Look at the family tree. Complete the sentences with the words in the box."))
    P.append(panel("THE FAMILY TREE", [
        "**Ron** and **Mary** are married. Their children are **Diana**, **Michael** and **Laura**.",
        "**Michael** and **Jane** are married. Their children are **Oliver** and **Natalie**.",
        "**Natalie** and **James** are married.",
    ]))
    P.append(word_box(["brother", "daughter", "father", "husband", "mother", "parents", "sister", "son", "wife"]))
    P.append(example(1, "Michael is Jane's %s." % done("husband")))
    for n, (text, a) in enumerate([
            ("Michael is Natalie's {} .", "father"), ("Jane is Oliver's {} .", "mother"),
            ("Ron and Mary are Laura's {} .", "parents"), ("Oliver is Natalie's {} .", "brother"),
            ("Diana is Ron's {} .", "daughter"), ("Oliver is Michael's {} .", "son"),
            ("Natalie is James's {} .", "wife"), ("Laura is Diana's {} .", "sister")], 2):
        P.append(item(h, "3.1", n, text, box("3.1", n)))
        K[("3.1", n, 1)] = Q(a)

    # ------------------------------------------------ 4 pronunciation
    P.append(bar(4, "4B Pronunciation", "sound and spelling /ð/"))
    P.append(ex("4.1", "**4a**  Listen. Does the word have the /ð/ sound? Choose ✓ or ✗."))
    P.append(listen("04.02", "Listen"))
    HAS = {"yes": "✓ /ð/", "no": "✗ no /ð/"}      # ✓ as an answer reads "it was right as it was"
    for n, (word, a) in enumerate([("she", "no"), ("that", "yes"), ("right", "no"), ("father", "yes"),
                                   ("mother", "yes"), ("three", "no"), ("they", "yes"), ("the", "yes"),
                                   ("eight", "no"), ("brother", "yes")], 1):
        P.append(item(h, "4.1", n, word + "  {}", box("4.1", n, "60px")))
        K[("4.1", n, 1)] = choose(["yes", "no"], a, labels=HAS)

    h.html = '<div class="booklet">' + "".join(P) + "</div>"
    for label, text in [
            ("1.1", "Toʻgʻri soʻzni tanlang."),
            ("1.2", "Qavsdagi feʼlning toʻgʻri shakli bilan gaplarni toʻldiring."),
            ("2.1", "Sonlarni soʻz bilan yozing."),
            ("3.1", "Oila daraxtiga qarang. Gaplarni qutichadagi soʻzlar bilan toʻldiring."),
            ("4.1", "Tinglang. Soʻzda /ð/ tovushi bormi? *✓* yoki *✗* ni tanlang. Yozuv boʻlmasa, har bir "
                    "soʻzni ovoz chiqarib ayting: /ð/ — *this* dagi *th*, tilingiz tishlaringiz orasida, ovozingiz "
                    "ham chiqadi.")]:
        h.say_also(label, text)
    return h.build(K, "Beginner", 4, "Workbook · Unit 4B — My life and my family")


if __name__ == "__main__":
    data = unit4b()
    data["series"] = "workbook"
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "wb_b_04b.json")
    json.dump(data, open(out, "w"))
    report(data)
