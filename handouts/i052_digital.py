"""I05.2 The natural world - Azamat's Intermediate booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(I05.2 The natural world - answer key), joined box by box by hand. At this
level the explanations stay English. The Desktop "new design" copy (21 Sep)
is used. Its fourth part is Everyday English and its fifth a discussion
essay; there is no listening.

Put right here: 3.1's meanings ran a-h beside words 1-8, so every answer was
the next letter - they are lettered in a different order.
Where the key gives samples but the two ideas leave one sentence (2.7), the
box is marked with every reasonable wording, either clause first.

    python3 handouts/i052_digital.py            # writes handouts/i052.json, lists every box
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import (Handout, Q, choose, own, write, fix, report,   # noqa: E402
                     plain, ITEM_STYLE, NUM_SPAN, TEXT_SPAN)

DOCX = ("~/Desktop/Handouts/B1+ Intermediate/I05.2 The natural world/"
        "I05.2 The natural world — handout (new design).docx")
W = "95%"

h = Handout(DOCX)


def section(label):
    return h.html.index("%s  </span>" % label)


def either(*forms):
    return "/".join(forms)


def item_p(label, n, text_html, token):
    h.texts[(label, n)] = plain(text_html)
    return ('<p data-item="%s:%d" %s>%s%s</p>'
            % (label, n, ITEM_STYLE, NUM_SPAN % n, TEXT_SPAN % ("%s  %s" % (text_html, token))))


def key_list(pairs):
    return ('<table class="bk"><tr><td style="vertical-align:top;background:#F2F8F8;'
            'border-left:3px solid #127D80">'
            + "".join('<p style="margin:0"><span style="font-weight:700;color:#127D80">%s</span>  %s</p>'
                      % (l, html.escape(t, quote=False)) for l, t in pairs)
            + "</td></tr></table>")


def halves(label, letters, relabel=None):
    a = h.html.index('<table class="bk">', section(label))
    b = h.html.index("</table>", a) + len("</table>")
    cells = [plain(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", h.html[a:b], re.S)]
    begins = [re.match(r"(\d+)\s+(.*)", c).groups() for c in cells if re.match(r"\d+\s", c)]
    ends = sorted(re.match(r"([%s])\s+(.*)" % letters, c).groups() for c in cells
                  if re.match(r"[%s]\s" % letters, c))
    old_to_new = {old: (relabel[i] if relabel else old) for i, (old, _t) in enumerate(ends)}
    shown = sorted((old_to_new[old], text) for old, text in ends)
    h.html = h.html[:a] + key_list(shown) + "".join(
        item_p(label, int(n), html.escape(t, quote=False), "{{box:%s:%s:60px:}}" % (label, n))
        for n, t in begins) + h.html[b:]
    return [l for l, _t in shown], old_to_new


def cond(if_part, main, will_forms=True):
    """Both orders of a conditional: If X, Y and Y if X, with will / 'll."""
    mains = [main]
    if will_forms and " will " in main:
        mains.append(main.replace(" will ", "'ll ", 1).replace(" 'll", "'ll"))
    out = []
    for m in mains:
        out += ["%s, %s" % (if_part, m), "%s %s" % (if_part, m),
                "%s %s" % (m[0].upper() + m[1:], if_part[0].lower() + if_part[1:])]
    return out


# ------------------------------------------------------------ 1 Reading
for n in range(1, 6):
    h.item_box("1.2", n, where="options")
h.options_on_lines("1.2")
for n in range(1, 5):
    h.item_box("1.3", n, where="leader")
for n in range(1, 5):
    h.item_box("1.4", n, width="190px", where="leader")
for n in range(1, 5):
    h.item_box("1.6", n, where="leader")

# ------------------------------------------------------------ 2 Grammar
for n in range(1, 9):
    h.item_box("2.1", n)
FORMS23 = {1: ["rains", "will rain"], 2: ["freezes", "will freeze"], 3: ["want", "don't want"],
           4: ["will heat", "heat"], 5: ["is", "will be"], 6: ["rises", "will rise"]}
for n in FORMS23:
    h.item_box("2.3", n)
for n in range(1, 7):
    h.item_box("2.4", n, where="leader")
h.options_on_lines("2.6")
FORMS210 = {1: ["will mix", "mix"], 2: ["if", "unless"], 3: ["leave", "don't leave"], 4: ["works", "will work"],
            5: ["expands", "will expand"], 6: ["until", "unless"]}
for n in FORMS210:
    h.item_box("2.10", n)
h.one_per_line("A MESSAGE ABOUT THE WEEKEND", "2.14  </span>", at="text")
h.options_on_lines("2.14")
h.leaders("2.15", "3.1  </span>", [(1, W, "Six sentences about nature in your country")])

# ------------------------------------------------------------ 3 Vocabulary
MEANINGS31, NEW31 = halves("3.1", "a-h", relabel="dgahbfce")
a = h.html.index('<table class="bk">', section("3.3"))
b = h.html.index("</table>", a) + len("</table>")
WB33 = ["mountain", "forest", "danger", "ice", "sand", "rock", "wind", "storm", "fog"]
h.html = h.html[:a] + ('<p style="margin-bottom:6px"><span style="color:#6E6E6E">Example: nature → natural'
                       '</span></p>') + "".join(
    item_p("3.3", n, "%s → the adjective" % w, "{{box:3.3:%d:120px:}}" % n) for n, w in enumerate(WB33, 1)) + h.html[b:]
FORMS35 = {1: ["rock", "rocky"], 2: ["nature", "natural"], 3: ["ice", "icy"], 4: ["mountain", "mountainous"],
           5: ["wind", "windy"], 6: ["wild", "wildlife"]}
for n in FORMS35:
    h.item_box("3.5", n)
FORMS37 = {1: ["predator", "prey"], 2: ["shore", "short"], 3: ["stream", "steam"], 4: ["dessert", "desert"],
           5: ["wood", "wooden"], 6: ["climate", "weather"]}
for n in FORMS37:
    h.item_box("3.7", n)
h.options_on_lines("3.11")
ODD312 = {1: ["valley", "cliff", "cave", "species"], 2: ["stream", "river", "lake", "desert"],
          3: ["fertile", "barren", "rocky", "sandy"], 4: ["predator", "prey", "habitat", "wildlife"]}
for n in ODD312:
    h.item_box("3.12", n)
ENDS314, _n = halves("3.14", "a-e")
h.leaders("3.15", "4.1  </span>", [(1, W, "A natural place you know well")])

# ------------------------------------------------------------ 4 Everyday English
for n in range(1, 5):
    h.item_box("4.2", n, where="leader")

# ------------------------------------------------------------ 5 Writing
h.leaders("5.1", "</div>", [(20, W, "Write your essay here")])

# ------------------------------------------------------------------ the key
K = {}
for n, a in enumerate("BBABB", 1):
    K[("1.2", n, 1)] = choose(["A", "B", "C"], a)
for n in range(1, 5):
    K[("1.3", n, 1)] = own()
for n, a in enumerate(["a generalist/generalist", "a specialist/specialist", "tolerate/to tolerate",
                       "indicate/to indicate"], 1):
    K[("1.4", n, 1)] = Q(a)
for n, a in enumerate(["everywhere", "cells", "warms", "specialised/specialized", "generalist",
                       "adaptable/ordinary"], 1):
    K[("1.5", n, 1)] = Q(a)
for n in range(1, 5):
    K[("1.6", n, 1)] = own()
AD = {"A": "A · agree", "D": "D · disagree"}
for n in range(1, 5):                             # their opinion
    K[("1.7", n, 1)] = choose(["A", "D"], labels=AD)
ZF = {"Z": "Z · zero", "F": "F · first"}
for n, a in enumerate("ZFZFZFZF", 1):
    K[("2.1", n, 1)] = choose(["Z", "F"], a, labels=ZF)
for key, a in (((1, 1), "heat"), ((1, 2), "melts"), ((2, 1), "rains"), ((2, 2), either("won't go", "will not go")),
               ((3, 1), either("will die", "'ll die")), ((3, 2), "gets"),
               ((4, 1), either("don't water", "do not water")), ((4, 2), "die"),
               ((5, 1), either("'ll send", "will send")), ((5, 2), "arrives"), ((6, 1), "act"),
               ((6, 2), either("will disappear", "'ll disappear")), ((7, 1), "calls"),
               ((7, 2), either("'ll tell", "will tell")), ((8, 1), "floats"), ((8, 2), "put")):
    K[("2.2",) + key] = Q(a)
for n, a in enumerate(["rains", "freezes", "want", "heat", "is", "rises"], 1):
    K[("2.3", n, 1)] = choose(FORMS23[n], a)
TICKED = "✓/correct/tick"
for n, a in enumerate([
        either(*cond("If it snows", "we will stay at home")),
        TICKED,
        either(*cond("Unless you hurry", "you will miss the bus")),
        TICKED,
        either("I'll call you when I arrive", "I will call you when I arrive"),
        either(*cond("If she comes", "I will be very pleased"))], 1):
    K[("2.4", n, 1)] = fix(a)
for n, a in enumerate(["rains/snows", "if/when", "Unless", "until", "die", "melts", "as", "if", "warms/heats",
                       "will/'ll/can/might/may"], 1):
    K[("2.5", n, 1)] = Q(a)
for n, a in enumerate("BBBBA", 1):
    K[("2.6", n, 1)] = choose(["A", "B", "C", "D"], a)
for n, a in enumerate([
        cond("If you don't water the plants", "they will die") + cond("Unless you water the plants", "they will die"),
        cond("Unless you hurry", "you will miss the bus") + cond("If you don't hurry", "you will miss the bus"),
        cond("If you heat metal", "it expands"),
        cond("If we act now", "the species will survive"),
        cond("If the temperature rises", "the ice melts"),
        cond("If you revise properly", "you will pass") + cond("unless you revise properly", "You won't pass")], 1):
    K[("2.7", n, 1)] = write(either(*a))
for n, a in enumerate(["unless you hurry",
                       either("If you heat water to one hundred degrees", "If you heat water to 100 degrees",
                              "If you heat water to a hundred degrees", "If water reaches one hundred degrees",
                              "If water reaches 100 degrees"),
                       either("'ll stay in if it rains", "will stay in if it rains"), "might survive"], 1):
    K[("2.8", n, 1)] = Q(a)
for key, a in (((1, 1), "continue"), ((1, 2), either("will disappear", "'ll disappear")), ((2, 1), "floats"),
               ((2, 2), "is"), ((3, 1), either("won't finish", "will not finish")), ((3, 2), "helps"),
               ((4, 1), "see"), ((4, 2), "tell"), ((5, 1), "floods"), ((5, 2), "rains"),
               ((6, 1), either("would be", "'ll be", "will be", "'d be")), ((6, 2), "agree")):
    K[("2.9",) + key] = Q(a)
for n, a in enumerate(["mix", "if", "leave", "works", "expands", "until"], 1):
    K[("2.10", n, 1)] = choose(FORMS210[n], a)
for n, a in enumerate(["warms", "holds", "is", either("will have", "'ll have"), "ends",
                       either("will die", "'ll die")], 1):
    K[("2.11", n, 1)] = Q(a)
for n, a in enumerate(["Unless", "melts", "when", either("won't", "can't")], 1):
    K[("2.12", n, 1)] = Q(a)
for n, a in enumerate([
        either(*cond("If it rains tomorrow", "we will stay at home")),
        either(*(cond("Unless you revise", "you will fail the test") + cond("If you don't revise",
                                                                             "you will fail the test"))),
        either(*cond("If you heat water to 100 degrees", "it boils")),
        either("I'll call you when I get there", "I will call you when I get there")], 1):
    K[("2.13", n, 1)] = write(a)
for n, a in enumerate("BBAB", 1):
    K[("2.14", n, 1)] = choose(["A", "B", "C", "D"], a)
K[("2.15", 1, 1)] = own()
for n in range(1, 9):                             # word n goes with its own meaning, lettered afresh
    K[("3.1", n, 1)] = choose(MEANINGS31, NEW31["abcdefgh"[n - 1]])
for n, a in enumerate(["fertile", "barren", "glacier", "predator", "prey", "wetland", "cliff", "vegetation"], 1):
    K[("3.2", n, 1)] = Q(a)
for n, a in enumerate(["mountainous", "forested", "dangerous", "icy", "sandy", "rocky", "windy", "stormy",
                       "foggy"], 1):
    K[("3.3", n, 1)] = Q(a)
for n, a in enumerate(["mountainous", "rocky", "stormy", "icy", "sandy", "naturally", "fog", "dangerous"], 1):
    K[("3.4", n, 1)] = Q(a)
for n, a in enumerate(["rocky", "natural", "icy", "mountainous", "wind", "wildlife"], 1):
    K[("3.5", n, 1)] = choose(FORMS35[n], a)
for n, a in enumerate(["range", "bank/bed", "species", "habitat/resource/resources/wonder/disaster/harbour/park",
                       "edge/top/foot", "flock", "water", "beach/shore"], 1):
    K[("3.6", n, 1)] = Q(a)
for n, a in enumerate(["predator", "shore", "stream", "desert", "wood", "climate"], 1):
    K[("3.7", n, 1)] = choose(FORMS37[n], a)
BOX38 = ["a valley", "a cave", "a waterfall", "a glacier", "a wetland", "a coastline", "a stream", "a cliff"]
for n, a in enumerate(["a valley", "a cave", "a waterfall", "a stream", "a coastline", "a cliff"], 1):
    K[("3.8", n, 1)] = choose(BOX38, a)
for n, a in enumerate(["barren/infertile", "sparse/thin", "accessible/nearby/near/central", "prey",
                       "gentle/flat/shallow", "robust/tough/strong/sturdy"], 1):
    K[("3.9", n, 1)] = Q(a)
for n, a in enumerate(["remote", "fragile", "dense", "predator/predators", "species"], 1):
    K[("3.10", n, 1)] = Q(a)
for n, a in enumerate("ABABB", 1):
    K[("3.11", n, 1)] = choose(["A", "B", "C", "D"], a)
for n, a in enumerate(["species", "desert", "fertile", "habitat"], 1):
    K[("3.12", n, 1)] = choose(ODD312[n], a)
for n, a in enumerate(["glacier", "stream", "fertile", "remote", either("will run", "'ll run"),
                       "move/leave/adapt"], 1):
    K[("3.13", n, 1)] = Q(a)
for n, a in enumerate("bcaed", 1):
    K[("3.14", n, 1)] = choose(ENDS314, a)
K[("3.15", 1, 1)] = own()
for n in range(1, 5):                             # their own answers, with time bought first
    K[("4.2", n, 1)] = own()
K[("5.1", 20, 1)] = own(control="essay")

if __name__ == "__main__":
    data = h.build(K, "Intermediate", 5, "Unit 5.2 — The natural world")
    out = os.path.join(HERE, "i052.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
