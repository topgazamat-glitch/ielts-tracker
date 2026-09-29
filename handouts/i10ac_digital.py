"""I10AC Opportunities - Azamat's Intermediate booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(I10AC Opportunities - ANSWER KEY), joined box by box by hand. At this level
the explanations stay English. Built from the Material Bank copy: his
redesign on the Desktop has the same exercises, laid out again, but its
section bars share a table with what follows them, so it would not split
into parts.

Put right here, since a page that marks itself cannot be wrong about its
own answers:
  - 2.3 says TWO sentences are correct; the key ticks three (4, 6 and 8 -
    8 is a first conditional and perfectly formed), so the page says three;
  - 4.6: "I'm not fit enough" is Libby's line in the script ("I wouldn't do
    a full marathon - I'm not fit enough"), though the key gives it to Gina,
    whose reason it also is - so either is right.

What a phone gets that paper does not:
  - taps for every choice: S/R/C, A/B/C, the verb forms in 2.2, weak or
    strong, Libby or Gina, problem or reassurance, sure or unsure;
  - boxes where paper has none: 2.2, 2.3, 3.5, and one box for the whole
    conversation in 5.7, since at home the student writes both parts.

    python3 handouts/i10ac_digital.py            # writes handouts/i10ac.json, lists every box
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import Handout, Q, choose, tick, own, write, fix, report, plain   # noqa: E402

DOCX = ("~/Documents/Claude/Material Bank/General English/B1 Intermediate/_NEW BOOKLET STYLE/"
        "I10AC Opportunities — BOOKLET.docx")
W = "95%"

h = Handout(DOCX)


def section(label):
    return h.html.index("%s  </span>" % label)


def either(*forms):
    return "/".join(forms)


def would(*rest):
    return either(*[p + r for r in rest for p in ("would ", "'d ")])


# ------------------------------------------------------------ 1 Reading
for n in range(1, 5):
    h.item_box("1.3", n)
h.options_on_lines("1.3")
for n in range(1, 4):
    h.item_box("1.4", n, width="190px", where="leader")
h.leaders("1.5", "1.6  </span>", [(1, W, "Three conditional sentences"), (2, W, "Which one is about the past?")])
for n in range(1, 4):
    h.item_box("1.6", n, where="leader")

# ------------------------------------------------------------ 2 Grammar
CHOICES22 = {1: [["rains", "rained"]], 2: [["rains", "rained"]], 3: [["wins", "won"], ["will", "would"]],
             4: [["wins", "won"], ["will", "would"]], 5: [["don't", "didn't"], ["won't", "wouldn't"]],
             6: [["stay", "stayed"], ["can", "could"]]}
for n, groups in CHOICES22.items():
    for _g in groups:
        h.item_box("2.2", n, width="60px")
h.html = re.sub(r"(\{\{box:2\.2:\d+:[^}]*\}\}) (\{\{box:2\.2:)", r"\1<br>\2", h.html)   # one choice a line
a = section("2.3")
b = h.html.index("</p>", a)
h.html = h.html[:a] + h.html[a:b].replace("TWO", "THREE", 1) + h.html[b:]
for n in range(2, 9):                             # item 1 is the worked example
    h.item_box("2.3", n)

# ------------------------------------------------------------ 3 Vocabulary
for n in range(1, 5):
    h.item_box("3.5", n, where="leader")

# ------------------------------------------------------------ 4 Listening
for n in range(1, 3):
    h.item_box("4.1", n, where="leader")
for n in range(1, 6):
    h.item_box("4.2", n, where="leader")
for n in range(1, 4):
    h.item_box("4.7", n)
h.options_on_lines("4.7")

# ------------------------------------------------------------ 5 Everyday English
for n in range(1, 4):
    h.item_box("5.1", n, where="leader")
for n in range(1, 5):
    h.item_box("5.6", n, where="leader")
h.leaders("5.7", "CHECK YOUR", [(20, W, "Write your conversation here — both A and B")])

# ------------------------------------------------------------------ the key
K = {}
SRC = {"S": "S · swimming", "R": "R · the race", "C": "C · climbing"}
for n, a in enumerate("RSCRSC", 1):
    K[("1.2", n, 1)] = choose(["S", "R", "C"], a, labels=SRC)
for n in range(1, 5):
    K[("1.3", n, 1)] = choose(["A", "B", "C"], "B")
for n, a in enumerate(["put it off/to put it off/put off/to put off", "humiliating",
                       "furious with/furious"], 1):
    K[("1.4", n, 1)] = Q(a)
K[("1.5", 1, 1)] = own()
K[("1.5", 2, 1)] = own()
for n in range(1, 4):
    K[("1.6", n, 1)] = own()
for key, a in (((1, 1), "was/were"), ((1, 2), would("definitely do")), ((2, 1), "went"),
               ((2, 2), would("absolutely love")), ((3, 1), "knew"), ((3, 2), would("call")),
               ((4, 1), would("get")), ((4, 2), "applied"), ((5, 1), "would"), ((5, 2), "do"), ((5, 3), "won"),
               ((6, 1), either("didn't treat", "did not treat")), ((6, 2), would("stay"))):
    K[("2.1",) + key] = Q(a)
ANS22 = {1: ["rains"], 2: ["rained"], 3: ["wins", "will"], 4: ["won", "would"], 5: ["didn't", "wouldn't"],
         6: ["stayed", "could"]}
for n, groups in CHOICES22.items():
    for k, (opts, a) in enumerate(zip(groups, ANS22[n]), 1):
        K[("2.2", n, k)] = choose(opts, a)
TICKED = "✓/correct/tick"
for n, a in zip(range(2, 9), [
        either("If you came with me, it would be fun", "it would be fun"),
        either("If we went to the mall, we could get ice cream", "we could get ice cream"),
        TICKED,
        either(*[p + r for p in ("If she were here, ", "If she was here, ")
                 for r in ("she'd know what to do", "she would know what to do")]),
        TICKED,
        "What would you do if you lost your passport",
        TICKED]):
    K[("2.3", n, 1)] = fix(a)
for n, a in enumerate(["were/was", would("take"), "went", would("have to"), "could come", "wanted",
                       either("didn't work", "did not work"), either("would come", "could come", "'d come"),
                       "would think", either("wasn't", "weren't", "was not", "were not")], 1):
    K[("2.4", n, 1)] = Q(a)
WS = {"W": "W · weak", "S": "S · strong"}
for n, a in enumerate("WSWSWS", 1):             # I'd, Yes I would, You'd, wouldn't, It'd, Would you
    K[("2.5", n, 1)] = choose(["W", "S"], a, labels=WS)
K[("2.6", 1, 1)] = Q(either(*[b + f + c + d for b in ("were ", "was ") for f in ("fitter", "fit enough")
                              for c in (", ", " ") for d in ("I'd do it", "I would do it")]))
K[("2.6", 2, 1)] = write(either(*["If she knew his number, she " + v + " call him" for v in ("could", "would")]))
K[("2.6", 3, 1)] = write(either(*["If we had a car, we " + v + " take the bus"
                                  for v in ("wouldn't", "would not")]))
K[("2.6", 4, 1)] = write(either(*[p + v for p in ("If I were you, ", "If I was you, ")
                                  for v in ("I'd say something", "I would say something")]))
K[("2.7", 1, 1)] = own()
K[("2.7", 2, 1)] = own(control=None)              # what they would learn: a word or two
K[("2.7", 2, 2)] = own()
K[("2.7", 3, 1)] = own()
for key, a in (((1, 1), "referee"), ((2, 1), "competitors"), ((3, 1), "beat"), ((3, 2), "won"),
               ((4, 1), "trains"), ((5, 1), "net"), ((5, 2), "scored"), ((6, 1), "spectators")):
    K[("3.1",) + key] = Q(a)
for n, a in enumerate(["of", "in", "about", "with", "for", "to", "of", "at", "of", "with"], 1):
    K[("3.2", n, 1)] = Q(a)
for n, a in enumerate(["about", "of", "for", "of", "in", "with", "of", "to"], 1):
    K[("3.3", n, 1)] = Q(a)
K[("3.4", 1, 1)] = Q("in")
K[("3.4", 1, 2)] = own(control=None)
K[("3.4", 2, 1)] = own(control=None)              # at + something, in one box
K[("3.4", 2, 2)] = Q("at")
K[("3.4", 2, 3)] = own(control=None)
K[("3.4", 3, 1)] = Q("about")
K[("3.4", 3, 2)] = own(control=None)
K[("3.4", 4, 1)] = Q("of")
K[("3.4", 4, 2)] = own(control=None)
for n, a in enumerate([
        either("I'm very interested in photography", "I am very interested in photography"),
        either("She's really good at tennis", "She is really good at tennis"),
        "He was worried about the exam all week",
        either("We beat Spain", "We won the match against Spain", "We beat Spain in the match")], 1):
    K[("3.5", n, 1)] = write(a)
for n in range(1, 3):
    K[("4.1", n, 1)] = own()
for n in range(1, 6):
    K[("4.2", n, 1)] = own()
for n, a in enumerate(["went", "should", "went", "was/were", "was/were"], 1):
    K[("4.3", n, 1)] = Q(a)
LG = {"L": "L · Libby", "G": "G · Gina"}
# as numbered: 1 didn't plan 2 too frightened 3 moving around 4 not a serious race 5 not fit enough
# 6 two months. 5 is Libby's words and Gina's reason: either
for n, a in enumerate(["G", "L", "G", "L", "G/L", "L"], 1):
    K[("4.6", n, 1)] = choose(["L", "G"], a, labels=LG)
for n in range(1, 4):
    K[("4.7", n, 1)] = choose(["A", "B"], "B")
for n in range(1, 4):
    K[("5.1", n, 1)] = own()
PR = {"P": "P · problem", "R": "R · reassurance"}
for n, a in enumerate("PRPRPR", 1):
    K[("5.2", n, 1)] = choose(["P", "R"], a, labels=PR)
for n in range(1, 4):                             # the key gives samples: his to read
    K[("5.3", n, 1)] = own()
SU = {"S": "S · sure", "U": "U · unsure"}
for n, a in enumerate("SUSU", 1):
    K[("5.4", n, 1)] = choose(["S", "U"], a, labels=SU)
for n in range(1, 5):
    K[("5.6", n, 1)] = own()
K[("5.7", 20, 1)] = own(control="essay")
for n in range(1, 6):                             # the checklist
    K[("5.7", n, 1)] = tick()

if __name__ == "__main__":
    data = h.build(K, "Intermediate", 10, "Unit 10A & 10C — Opportunities")
    out = os.path.join(HERE, "i10ac.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
