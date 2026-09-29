"""I04.2 Personality - Azamat's Intermediate booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(I04.2 Personality - answer key), joined box by box by hand. At this level
the explanations stay English. The Desktop "new design" copy is used. Its
fourth part is Everyday English and its fifth an advert to write; there is no
listening.

Articles are tapped, not typed: a, an, the or – (no article) as chips, so
nobody has to find a dash on a phone keyboard.

Put right here: 3.1's meanings ran almost a-h beside words 1-8 (only pairs
swapped), so they are lettered in a different order. In 2.9 item 1 the key
gives "her (or -)", but the exercise offers only a, an, the or -: "-" is the
answer. The table in 3.3 is one line per adjective.

    python3 handouts/i042_digital.py            # writes handouts/i042.json, lists every box
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

DOCX = ("~/Desktop/Handouts/B1+ Intermediate/I04.2 Personality/"
        "I04.2 Personality — handout (new design).docx")
W = "95%"
ART = ["a", "an", "the", "–"]

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


def add_to_item(label, n, extra):
    m = next(m for m in h._items(label) if int(m.group(3)) == n)
    h.texts.setdefault((label, n), plain(m.group(4)))
    h.html = h.html[:m.start()] + m.group(1) + m.group(4) + extra + "</p>" + h.html[m.end():]


def boxes_for(label, groups):
    for n in groups:
        h.item_box(label, n)


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
FORMS23 = {1: ["a", "the"], 2: ["a", "the"], 3: ["The life", "Life"], 4: ["a", "an"],
           5: ["The most of", "Most of"], 6: ["the hospital", "hospital"]}
boxes_for("2.3", FORMS23)
for n in range(1, 7):
    h.item_box("2.4", n, where="leader")
h.options_on_lines("2.6")
FORMS210 = {1: ["a", "the"], 2: ["a", "the"], 3: ["A", "The"], 4: ["–", "the"], 6: ["a", "the"]}
boxes_for("2.10", FORMS210)
add_to_item("2.10", 5, '<br><span style="color:#6E6E6E">goes to … work</span> {{box:2.10:5:60px:}}'
                       '<br><span style="color:#6E6E6E">by … car</span> {{box:2.10:5:60px:}}')
h.options_on_lines("2.14")
h.leaders("2.15", "3  </span>", [(1, W, "Six sentences about people you know")])

# ------------------------------------------------------------ 3 Vocabulary
MEANINGS31, NEW31 = halves("3.1", "a-h", relabel="dgahbfce")
NOUNS33 = [("patient", "patience"), ("honest", "honesty"), ("confident", "confidence"),
           ("generous", "generosity"), ("ambitious", "ambition"), ("arrogant", "arrogance"),
           ("modest", "modesty"), ("sensitive", "sensitivity"), ("loyal", "loyalty")]
a = h.html.index('<table class="bk">', section("3.3"))
b = h.html.index("</table>", a) + len("</table>")
h.html = h.html[:a] + ('<p style="margin-bottom:6px"><span style="color:#6E6E6E">Example: kind → kindness'
                       '</span></p>') + "".join(
    item_p("3.3", n, html.escape(adj) + " →", "{{box:3.3:%d:140px:}}" % n)
    for n, (adj, _noun) in enumerate(NOUNS33, 1)) + h.html[b:]
FORMS35 = {1: ["sensible", "sensitive"], 2: ["sensible", "sensitive"], 3: ["self-confident", "self-conscious"],
           4: ["sympathetic", "likeable"], 5: ["ambitious", "arrogant"], 6: ["economic", "economical"]}
boxes_for("3.5", FORMS35)
FORMS37 = {1: ["generous", "selfish"], 2: ["reliable", "moody"], 3: ["modest", "arrogant"],
           4: ["bossy", "easy-going"], 5: ["patient", "impatient"], 6: ["ambitious", "lazy"]}
boxes_for("3.7", FORMS37)
h.options_on_lines("3.11")
ODD312 = {1: ["outgoing", "sociable", "friendly", "reserved"], 2: ["bossy", "arrogant", "selfish", "considerate"],
          3: ["kindness", "honesty", "patient", "generosity"], 4: ["tends to", "comes across as", "can be a bit", "always"]}
boxes_for("3.12", ODD312)
ENDS314, _n = halves("3.14", "a-e")
h.leaders("3.15", "4  </span>", [(1, W, "Three people you know well")])

# ------------------------------------------------------------ 4 Everyday English
for n in range(1, 5):
    h.item_box("4.2", n, where="leader")

# ------------------------------------------------------------ 5 Writing
h.leaders("5.1", "</div>", [(1, W, "Write your advert here")])

# ------------------------------------------------------------------ the key
K = {}
for n, a in enumerate("BBABB", 1):
    K[("1.2", n, 1)] = choose(["A", "B", "C"], a)
for n in range(1, 5):
    K[("1.3", n, 1)] = own()
for n, a in enumerate(["reckless", "regardless of/regardless", "open-plan/open plan/open-plan office",
                       "evidence"], 1):
    K[("1.4", n, 1)] = Q(a)
for n, a in enumerate(["loudest", "confidence", "ability", "most", "risks", "write/put/note"], 1):
    K[("1.5", n, 1)] = Q(a)
for n in range(1, 5):
    K[("1.6", n, 1)] = own()
AD = {"A": "A · agree", "D": "D · disagree"}
for n in range(1, 5):                             # their opinion
    K[("1.7", n, 1)] = choose(["A", "D"], labels=AD)
for n, a in enumerate(["an", "the", "–", "a", "the", "–", "the", "a"], 1):
    K[("2.1", n, 1)] = choose(ART, a)
for key, a in (((1, 1), "a"), ((1, 2), "the"), ((2, 1), "an"), ((3, 1), "–/the"), ((4, 1), "the"),
               ((5, 1), "–"), ((6, 1), "the"), ((7, 1), "–"), ((8, 1), "an"), ((8, 2), "–")):
    K[("2.2",) + key] = choose(ART, a)
for n, a in enumerate(["a", "the", "Life", "a", "Most of", "hospital"], 1):
    K[("2.3", n, 1)] = choose(FORMS23[n], a)
TICKED = "✓/correct/tick"
for n, a in enumerate([
        either("She is a very sensible woman", "She's a very sensible woman", "a very sensible woman"),
        either("Honesty is important in a team", "Honesty is important"),
        TICKED,
        either("He goes to bed very late", "goes to bed"),
        TICKED,
        either("He's the most reliable person in the office", "He is the most reliable person in the office",
               "the most reliable person")], 1):
    K[("2.4", n, 1)] = fix(a)
for n, a in enumerate(["an", "a", "a", "an", "–", "the", "–", "the", "–", "a"], 1):
    K[("2.5", n, 1)] = choose(ART, a)
for n, a in enumerate("CDBAD", 1):
    K[("2.6", n, 1)] = choose(["A", "B", "C", "D"], a)
for n in range(1, 7):
    K[("2.7", n, 1)] = choose(["the", "–"], "–")
    K[("2.7", n, 2)] = choose(["the", "–"], "the")
for n, a in enumerate(["the best", "the most patient", "a bus", "works as an"], 1):
    K[("2.8", n, 1)] = Q(a)
for key, a in (((1, 1), "the"), ((1, 2), "–"), ((2, 1), "–"), ((2, 2), "the"), ((3, 1), "–"), ((3, 2), "–"),
               ((3, 3), "the/–"), ((4, 1), "a"), ((5, 1), "–"), ((5, 2), "a"), ((5, 3), "the"),
               ((6, 1), "the"), ((6, 2), "–")):
    K[("2.9",) + key] = choose(ART, a)
for n, a in {1: "a", 2: "the", 3: "The", 4: "the", 6: "the"}.items():
    K[("2.10", n, 1)] = choose(FORMS210[n], a)
K[("2.10", 5, 1)] = choose(["–", "the"], "–")
K[("2.10", 5, 2)] = choose(["–", "the"], "–")
for n, a in enumerate(["an", "a", "the", "the", "–", "–"], 1):
    K[("2.11", n, 1)] = choose(ART, a)
for n, a in enumerate(["an", "the", "–", "an", "the", "–"], 1):
    K[("2.12", n, 1)] = choose(ART, a)
for n, a in enumerate([
        either("Dilnoza is a very reliable person", "Dilnoza is a very reliable person.", "a very reliable person"),
        either("Patience is her greatest quality", "Patience"),
        either("She goes to work earlier than anyone", "goes to work", "to work"),
        either("She was the best assistant we have had", "She was the best assistant we've had",
               "the best assistant")], 1):
    K[("2.13", n, 1)] = write(a)
for n, a in enumerate("BDCD", 1):
    K[("2.14", n, 1)] = choose(["A", "B", "C", "D"], a)
K[("2.15", 1, 1)] = own()
for n, old in enumerate("badcfehg", 1):          # the key's letters, lettered afresh
    K[("3.1", n, 1)] = choose(MEANINGS31, NEW31[old])
for n, a in enumerate(["modest", "bossy", "moody", "easy-going/easy going/easygoing", "stubborn",
                       "considerate", "outgoing", "reserved"], 1):
    K[("3.2", n, 1)] = Q(a)
for n, (_adj, noun) in enumerate(NOUNS33, 1):
    K[("3.3", n, 1)] = Q(noun)
for n, a in enumerate(["kindness", "confidence", "honesty", "arrogance", "patience", "ambition",
                       "generosity", "loyalty"], 1):
    K[("3.4", n, 1)] = Q(a)
for n, a in enumerate(["sensitive", "sensible", "self-conscious", "sympathetic", "arrogant", "economical"], 1):
    K[("3.5", n, 1)] = choose(FORMS35[n], a)
for n, a in enumerate(["un", "im", "dis", "in", "un", "in", "dis", "un"], 1):
    K[("3.6", n, 1)] = choose(["un", "im", "in", "dis"], a)
for n, a in enumerate(["selfish", "reliable", "modest", "easy-going", "impatient", "ambitious"], 1):
    K[("3.7", n, 1)] = choose(FORMS37[n], a)
BOX38 = ["outgoing", "reserved", "considerate", "stubborn", "ambitious", "moody", "modest", "reliable"]
for n, a in enumerate(["reliable", "ambitious", "stubborn", "modest", "reserved", "considerate"], 1):
    K[("3.8", n, 1)] = choose(BOX38, a)
for n, a in enumerate(["mean/selfish/stingy/ungenerous", "reserved/shy/quiet/introverted",
                       "impatient", "arrogant/boastful/big-headed/immodest", "unreliable",
                       "uptight/tense/anxious/nervous/stressed"], 1):
    K[("3.9", n, 1)] = Q(a)
for n, a in enumerate(["tends", "across", "bit", "modest"], 1):
    K[("3.10", n, 1)] = Q(a)
for n, a in enumerate("AABAB", 1):
    K[("3.11", n, 1)] = choose(["A", "B", "C", "D"], a)
for n, a in enumerate(["reserved", "considerate", "patient", "always"], 1):
    K[("3.12", n, 1)] = choose(ODD312[n], a)
for n, a in enumerate(["across", "arrogant", "bit", "tended",
                       "reliable/dependable",
                       "patience/sensitivity/interest/consideration/empathy/sympathy/kindness"], 1):
    K[("3.13", n, 1)] = Q(a)
for n, a in enumerate("caebd", 1):
    K[("3.14", n, 1)] = choose(ENDS314, a)
K[("3.15", 1, 1)] = own()
for n in range(1, 5):
    K[("4.2", n, 1)] = own()
K[("5.1", 1, 1)] = own(control="essay")

if __name__ == "__main__":
    data = h.build(K, "Intermediate", 4, "Unit 4.2 — Personality")
    out = os.path.join(HERE, "i042.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
