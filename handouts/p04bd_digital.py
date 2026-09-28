"""P04BD Celebrations - Azamat's own booklet, done on a phone.

His design is rendered as it is; this decides every box. The key is his
(P04BD Celebrations - ANSWER KEY), joined box by box by hand, because the
key is written for a teacher and the automatic reader mis-joins it.

What a phone gets that paper does not:
  - taps for every choice: T/F/DS, a-d, D/O/P/S, 'll/won't/shall/let's,
    very/absolutely, ticks and crosses, Kamola/Bek;
  - 3.4 and 3.5, which on paper are "circle", can be answered at all -
    3.5 is marked, 3.4 is saved for the teacher because it is a listening
    task he reads aloud in class;
  - one growing box for each piece of writing instead of six ruled lines.

    python3 handouts/p04bd_digital.py            # writes handouts/p04bd.json, lists every box
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import Handout, Q, choose, tick, own, write, fix, report   # noqa: E402

DOCX = ("~/Documents/Claude/Material Bank/General English/B1 Pre-intermediate/"
        "P04BD Celebrations — BOOKLET.docx")
TF = ["T", "F", "DS"]
YES_NO = ["✓", "✗"]
MODALS = ["'ll", "won't", "shall"]

h = Handout(DOCX)
for n in (1, 2, 3):
    h.item_box("1.5", n, where="leader")
for n in range(1, 7):
    h.item_box("4.2", n, where="leader")
for n in (1, 2, 3, 4):
    h.item_box("5.3", n, where="leader")
for n in (2, 3, 4, 5, 6):                       # item 1 is the worked example
    h.item_box("2.5", n)
for n in range(1, 6):
    h.item_box("3.4", n, width="60px")
for n in range(1, 9):
    h.item_box("3.5", n, width="60px")
h.leaders("5.4", "5.5  </span>", [(1, "95%", "Write your invitation here")])
h.leaders("5.5", "CHECK BEFORE", [(20, "95%", "Write your reply here")])
h.one_per_line('data-item="5.2:1"', 'data-item="5.2:2"', at="text")
h.one_per_line("CHECK BEFORE", "5.6  </span>", at="box")
FACES, CAN_DO = h.can_do_grid("5.6")


def places_first():
    """1.2 on paper is two lists side by side in one row - "8 am ...... a the
    covered market" - which a phone runs together into one line with the
    choice in the middle of it. The four places go first, as a key; then the
    four times, each with a, b, c, d to tap."""
    head = h.html.index("1.2  </span>")
    a = h.html.index('<table class="bk">', head)
    b = h.html.index("</table>", a) + len("</table>")
    items, places = [], []
    for m in re.finditer(r'(<p data-item="1\.2:(\d+)"[^>]*>)(<span[^>]*>\d+\s*</span>)'
                         r'<span([^>]*)>([^<]*?)\s*(<input class="bk-blank"[^>]*>)\s*'
                         r'([a-d])\s+([^<]*?)\s*</span></p>', h.html[a:b]):
        p_open, n, num, attrs, when, box, letter, place = m.groups()
        items.append((int(n), "%s%s<span%s>%s  %s</span></p>" % (p_open, num, attrs, when.strip(), box)))
        places.append((letter, place))
    assert len(items) == 4, items
    key = ('<table class="bk"><tr><td style="vertical-align:top;background:#F2F8F8;'
           'border-left:3px solid #127D80"><p style="margin:0">'
           + " ".join('<span style="white-space:nowrap;margin-right:18px">'
                      '<span style="font-weight:700;color:#127D80">%s</span>  %s</span>' % lp
                      for lp in sorted(places))
           + "</p></td></tr></table>")
    h.html = h.html[:a] + key + "".join(p for _n, p in sorted(items)) + h.html[b:]


places_first()

K = {}
# 1 Reading
for n, a in zip((1, 2, 3, 4), "cdab"):     # 8 am c · midday d · 2 pm a · 7 pm b
    K[("1.2", n, 1)] = choose(list("abcd"), a)
for n, a in enumerate(["F", "F", "T", "DS", "F", "T"], 1):
    K[("1.3", n, 1)] = choose(TF, a)
for n, a in enumerate(["crowded", "ugly", "narrow", "ancient", "noisy", "huge"], 1):
    K[("1.4", n, 1)] = Q(a)
for n in (1, 2, 3):
    K[("1.5", n, 1)] = own()
# 2 Grammar
for n, a in enumerate(["D/O", "S", "P", "O", "D", "P"], 1):
    K[("2.1", n, 1)] = choose(["D", "O", "P", "S"], a)
for n, a in enumerate(["shall", "'ll/will", "'ll/will", "shall", "won't/will not", "shall"], 1):
    K[("2.2", n, 1)] = choose(MODALS, a)
for n in (1, 2, 3, 4):
    K[("2.3", n, 1)] = own()
for n, a in enumerate(["'m meeting/am meeting", "'m going to visit/am going to visit",
                       "'ll get/will get", "'re having/are having", "'ll drive/will drive",
                       "'m not going to eat/am not going to eat"], 1):
    K[("2.4", n, 1)] = Q(a)
TICKED = "✓/correct/tick"
for n, a in zip((2, 3, 4, 5, 6),
                [TICKED, "I'm meeting Anna on Tuesday/I am meeting Anna on Tuesday",
                 "Yes, let's/Yes let's", TICKED,
                 "Let's visit the museum this afternoon/"
                 "Shall we visit the museum this afternoon"]):
    K[("2.5", n, 1)] = fix(a)
for n, a in enumerate(["shall", "let's", "shall", "won't/will not", "'ll/will",
                       "won't/will not", "shall", "let's"], 1):
    K[("2.6", n, 1)] = choose(MODALS + ["let's"], a)
for n in (1, 2, 3, 4):
    K[("2.7", n, 1)] = own()
# 3 Vocabulary
for n, a in enumerate(["ancient", "empty", "wide", "noisy", "outdoor", "ordinary",
                       "tiny", "ugly"], 1):
    K[("3.1", n, 1)] = Q(a)
for n, a in enumerate(["crowded", "huge", "ancient", "narrow", "outdoor", "noisy"], 1):
    K[("3.2", n, 1)] = Q(a)
for n, a in enumerate(["absolutely", "very", "absolutely", "very/absolutely",
                       "absolutely", "very"], 1):
    K[("3.3", n, 1)] = choose(["very", "absolutely"], a)
for n in range(1, 6):                           # he reads it aloud: his to mark
    K[("3.4", n, 1)] = choose(["want to", "won't"])
# /əʊ/ like won't: go know boat hotel old; not: hot stop not (as numbered)
for n, a in zip(range(1, 9), ["✓", "✗", "✓", "✗",
                              "✓", "✗", "✓", "✓"]):
    K[("3.5", n, 1)] = choose(YES_NO, a)
# 4 Listening
for n, a in zip((1, 2, 3, 4, 5), ["✗", "✓", "✓", "✗", "✓"]):
    K[("4.1", n, 1)] = choose(YES_NO, a)
K[("4.1", 6, 1)] = own()
for n in range(1, 7):
    K[("4.2", n, 1)] = own()
for n, a in enumerate(["won't/will not", "shall", "'ll/will", "won't/will not", "shall"], 1):
    K[("4.3", n, 1)] = choose(MODALS, a)
for key in (("4.4", 1, 1), ("4.4", 1, 2), ("4.4", 2, 1), ("4.4", 2, 2)):
    K[key] = own()
for n in range(1, 5):
    K[("4.5", n, 1)] = own()
for n in range(1, 7):
    K[("4.6", n, 1)] = choose(YES_NO, "✓")
K[("4.6", 6, 2)] = own()
# 5 Writing
K[("5.1", 1, 1)] = own()
K[("5.1", 2, 1)] = Q("fruit")
K[("5.1", 2, 2)] = Q("bread")
for n in (1, 2, 3, 4):
    K[("5.1", 3, n)] = own(control=None)
for n, a in enumerate(["Kamola", "Bek", "Kamola"], 1):
    K[("5.2", 1, n)] = choose(["Kamola", "Bek"], a)
for n, a in enumerate(["Would you like to come to my birthday party",
                       "Thanks for inviting me to your wedding",
                       "I'm afraid I can't go to the cinema with you/"
                       "I am afraid I can't go to the cinema with you",
                       "I'd love to come, but I'm busy that weekend/"
                       "I'd love to come but I'm busy that weekend"], 1):
    K[("5.3", n, 1)] = write(a)
K[("5.4", 1, 1)] = own(control="essay")
for n in range(1, 8):                           # CHECK BEFORE YOU HAND IT IN
    K[("5.5", n, 1)] = tick()
K[("5.5", 8, 1)] = own(control="number")        # Words: ...
K[("5.5", 20, 1)] = own(control="essay")
# the paper's faces are what is saved; the chips show one set of faces, all
# emoji, with a word, since ☺ and ☹ are drawn as text and 😐 in colour
FACE_SAYS = dict(zip(FACES, ["🙂 Yes", "😐 Nearly", "🙁 Not yet"]))
for n in CAN_DO:                                # the self-check: one face a row
    K[("5.6", n, 1)] = choose(FACES, labels=FACE_SAYS)

if __name__ == "__main__":
    data = h.build(K, "Pre-Intermediate", 4, "Unit 4B & 4D — Celebrations")
    out = os.path.join(HERE, "p04bd.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
