"""I03.1 Relationships - Azamat's Intermediate booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(I03.1 Relationships - answer key), joined box by box by hand. At this level
the explanations stay English. The Desktop "new design" copy is used. Its
fourth part is Everyday English and its fifth a story to write; there is no
listening.

Put right here: 3.1's meanings ran almost a-h beside words 1-8 (only pairs
swapped), so they are lettered in a different order. 3.11 item 4 had a gap
in "( ... friend)" that is only an example, not a box. The error warning in
part 4 had "~~at the end~~" typed out; it reads "at the end". The
word-building table in 3.3 is one line per box.
2.7 items 2-6 can be joined in many right ways (because, so, after, either
half first), so the teacher reads them; item 1 starts "When I" and is marked.

    python3 handouts/i031_digital.py            # writes handouts/i031.json, lists every box
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import (Handout, Q, choose, own, write, fix, report,   # noqa: E402
                     LEADER_P, plain, ITEM_STYLE, NUM_SPAN, TEXT_SPAN)

DOCX = ("~/Desktop/Handouts/B1+ Intermediate/I03.1 Relationships/"
        "I03.1 Relationships — handout (new design).docx")
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
boxes_for("2.1", range(1, 9))
FORMS23 = {1: ["left", "had left"], 2: ["was reading", "had read"], 3: ["had known", "were knowing"],
           4: ["had been working", "was working"], 5: ["interrupted", "had interrupted"],
           6: ["were talking", "talked"]}
boxes_for("2.3", FORMS23)
for n in range(1, 7):
    h.item_box("2.4", n, where="leader")
h.options_on_lines("2.6")
h.options_on_lines("2.13")
h.leaders("2.14", "3  </span>", [(1, W, "Six sentences: how you met someone you know well")])

# ------------------------------------------------------------ 3 Vocabulary
MEANINGS31, NEW31 = halves("3.1", "a-h", relabel="dgahbfce")
WB33 = [("relate → the noun (thing)", "relationship/relation"), ("relate → the noun (person)", "relative/relation"),
        ("relate → the adjective", "related"), ("support → the noun (thing)", "support"),
        ("support → the noun (person)", "supporter"), ("support → the adjective", "supportive"),
        ("trust → the noun (thing)", "trust"), ("trust → the adjective", "trusting/trustworthy/trusted"),
        ("argue → the noun (thing)", "argument"), ("argue → the adjective", "argumentative"),
        ("rely → the noun (thing)", "reliance"), ("rely → the adjective", "reliable")]
a = h.html.index('<table class="bk">', section("3.3"))
b = h.html.index("</table>", a) + len("</table>")
h.html = h.html[:a] + ('<p style="margin-bottom:6px"><span style="color:#6E6E6E">Example: friend → friendship · '
                       'friend · friendly</span></p>') + "".join(
    item_p("3.3", n, html.escape(t), "{{box:3.3:%d:140px:}}" % n) for n, (t, _a) in enumerate(WB33, 1)) + h.html[b:]
FORMS35 = {1: ["support", "supportive"], 2: ["relation", "relationship"], 3: ["rely", "reliable"],
           4: ["argue", "argument"], 5: ["friend", "friendly"], 6: ["trust", "trusting"]}
boxes_for("3.5", FORMS35)
FORMS37 = {1: ["fell", "made"], 2: ["lost", "kept"], 3: ["made", "grew"], 4: ["looks", "gets"],
           5: ["get", "take"], 6: ["get", "make"]}
boxes_for("3.7", FORMS37)
h.options_on_lines("3.10")
h.html = re.sub(r'<input class="bk-blank" data-blank="148"[^>]*>', "…", h.html)   # an example, not a box
ODD311 = {1: ["loyal", "supportive", "jealous", "kind"], 2: ["colleague", "neighbour", "argument", "classmate"],
          3: ["fall out", "argue", "make up", "disagree"], 4: ["close", "old", "mutual", "angry"]}
boxes_for("3.11", ODD311)
ENDS313, _n = halves("3.13", "a-e")
h.leaders("3.14", "4.1  </span>", [(1, W, "Four sentences about people in your life")])

# ------------------------------------------------------------ 4 Everyday English
if h.html.count("~~at the end~~") != 1:
    raise SystemExit("the struck-out 'at the end' has moved")
h.html = h.html.replace("~~at the end~~", "at the end")
for n in range(1, 5):
    h.item_box("4.2", n, where="leader")

# ------------------------------------------------------------ 5 Writing
h.leaders("5.1", "</div>", [(1, W, "Write your story here")])

# ------------------------------------------------------------------ the key
K = {}
for n, a in enumerate("BBABA", 1):
    K[("1.2", n, 1)] = choose(["A", "B", "C"], a)
for n in range(1, 5):
    K[("1.3", n, 1)] = own()
for n, a in enumerate(["interrupt", "survive", "evidence",
                       "make up our minds/make up your mind/make up one's mind/make up their minds"], 1):
    K[("1.4", n, 1)] = Q(a)
for n, a in enumerate(["four", "interrupted", "avoided", "missed", "grandmothers", "quickly/soon/fast"], 1):
    K[("1.5", n, 1)] = Q(a)
for n in range(1, 5):
    K[("1.6", n, 1)] = own()
AD = {"A": "A · agree", "D": "D · disagree"}
for n in range(1, 5):                             # their opinion
    K[("1.7", n, 1)] = choose(["A", "D"], labels=AD)
for n, a in enumerate(["PC", "PS", "PP", "PP", "PC", "PS", "PP", "PS"], 1):
    K[("2.1", n, 1)] = choose(["PS", "PC", "PP"], a)
for key, a in (((1, 1), "was waiting"), ((1, 2), "started"), ((2, 1), "had already left"), ((2, 2), "arrived"),
               ((3, 1), "were talking"), ((3, 2), "walked"), ((4, 1), "reached"),
               ((4, 2), "had discovered/had already discovered"),
               ((5, 1), either("didn't know", "did not know")), ((5, 2), "had fallen"), ((6, 1), "looked"),
               ((6, 2), "had been driving/had driven"), ((7, 1), "were"), ((7, 2), "doing"), ((7, 3), "phoned"),
               ((8, 1), "recognised/recognized"), ((8, 2), "had seen")):
    K[("2.2",) + key] = Q(a)
for n, a in enumerate(["had left", "was reading", "had known", "had been working", "had interrupted",
                       "were talking"], 1):
    K[("2.3", n, 1)] = choose(FORMS23[n], a)
TICKED = "✓/correct/tick"
for n, a in enumerate([
        either("While I was walking home, I saw an old friend", "I saw an old friend", "saw"),
        TICKED,
        either("I had known him for ten years before we became close", "had known"),
        TICKED,
        either("They fell out last summer", "fell out"),
        either("It had been raining all day, so the ground was wet", "It had rained all day, so the ground was wet",
               "so the ground was wet")], 1):
    K[("2.4", n, 1)] = fix(a)
PARTS25 = [("met", "met"), ("knew", "known"), ("grew", "grown"), ("fell", "fallen"), ("became", "become"),
           ("kept", "kept"), ("lost", "lost"), ("spoke", "spoken"), ("broke", "broken"), ("forgave", "forgiven")]
for n, (past, participle) in enumerate(PARTS25, 1):
    K[("2.5", n, 1)] = Q(past)
    K[("2.5", n, 2)] = Q(participle)
for n, a in enumerate("BCBBC", 1):
    K[("2.6", n, 1)] = choose(["A", "B", "C", "D"], a)
K[("2.7", 1, 1)] = write(either("arrived, she had already left", "arrived, she had left",
                                "When I arrived, she had already left", "When I arrived, she had left"))
for n in range(2, 7):
    K[("2.7", n, 1)] = own()
for n, a in enumerate(["had left before", "had been raining", "had never spoken",
                       "While I was walking/While I was going/While I was coming"], 1):
    K[("2.8", n, 1)] = Q(a)
for key, a in (((1, 1), "didn't recognise/did not recognise/didn't recognize/did not recognize"),
               ((1, 2), "had cut"), ((2, 1), "were sitting"), ((2, 2), "began"),
               ((3, 1), "had gone/had already gone"), ((4, 1), "was crying"), ((4, 2), "had read"),
               ((5, 1), "had lived/had been living"), ((5, 2), "moved"), ((6, 1), "did"), ((6, 2), "say"),
               ((6, 3), "told")):
    K[("2.9",) + key] = Q(a)
for n, a in enumerate(["had been raining", "had already closed", "was standing", "walked",
                       either("didn't say", "did not say"), "offered", either("hadn't spoken", "had not spoken")], 1):
    K[("2.10", n, 1)] = Q(a)
for n, a in enumerate(["already/never", "was", "had", "been", "was", "time"], 1):
    K[("2.11", n, 1)] = Q(a)
for n, a in enumerate([
        either("When I arrived, she had already left", "she had already left", "had already left"),
        either("I had known him since school", "had known"),
        either("While I was walking home, I saw an accident", "While I was walking home", "was walking"),
        either("It had rained all morning, so we stayed in", "It had been raining all morning, so we stayed in",
               "had rained", "had been raining")], 1):
    K[("2.12", n, 1)] = write(a)
for n, a in enumerate("BCBC", 1):
    K[("2.13", n, 1)] = choose(["A", "B", "C", "D"], a)
K[("2.14", 1, 1)] = own()
for n, old in enumerate("badcfehg", 1):          # the key's letters, lettered afresh
    K[("3.1", n, 1)] = choose(MEANINGS31, NEW31[old])
for n, a in enumerate(["look up to", "lost touch", "fell out", "get to know", "have a lot in common",
                       "was there for", "made up", "get on with/get on well with/get along with"], 1):
    K[("3.2", n, 1)] = Q(a)
for n, (_t, a) in enumerate(WB33, 1):
    K[("3.3", n, 1)] = Q(a)
for n, a in enumerate(["friendship", "supportive", "relationship", "reliable", "argument", "trust", "friendly",
                       "relatives/relations"], 1):
    K[("3.4", n, 1)] = Q(a)
for n, a in enumerate(["supportive", "relationship", "reliable", "argument", "friendly", "trust"], 1):
    K[("3.5", n, 1)] = choose(FORMS35[n], a)
for n, a in enumerate(["get", "fall", "lose/keep", "make", "get", "have", "look", "be"], 1):
    K[("3.6", n, 1)] = Q(a)
for n, a in enumerate(["fell", "kept", "made", "looks", "get", "get"], 1):
    K[("3.7", n, 1)] = choose(FORMS37[n], a)
BOX38 = ["loyal", "supportive", "reliable", "jealous", "generous", "stubborn", "patient", "sociable"]
for n, a in enumerate(["stubborn", "loyal/reliable", "sociable", "jealous", "patient", "generous"], 1):
    K[("3.8", n, 1)] = choose(BOX38, a)
for n, a in enumerate(["disloyal", "mean/selfish/stingy/ungenerous", "impatient",
                       "unsociable/shy/antisocial/unsocial", "unreliable", "dishonest"], 1):
    K[("3.9", n, 1)] = Q(a)
for n, a in enumerate("AAABC", 1):
    K[("3.10", n, 1)] = choose(["A", "B", "C", "D"], a)
for n, a in enumerate(["jealous", "argument", "make up", "angry"], 1):
    K[("3.11", n, 1)] = choose(ODD311[n], a)
for n, a in enumerate(["get", "fell", "up", "touch", "common", "look"], 1):
    K[("3.12", n, 1)] = Q(a)
for n, a in enumerate("baced", 1):
    K[("3.13", n, 1)] = choose(ENDS313, a)
K[("3.14", 1, 1)] = own()
for n in range(1, 5):
    K[("4.2", n, 1)] = own()
K[("5.1", 1, 1)] = own(control="essay")

if __name__ == "__main__":
    data = h.build(K, "Intermediate", 3, "Unit 3.1 — Relationships")
    out = os.path.join(HERE, "i031.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
