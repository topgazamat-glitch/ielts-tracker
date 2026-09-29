"""I01.2 Talk - Azamat's Intermediate booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(I01.2 Talk - answer key), joined box by box by hand. At this level the
explanations stay English. The Desktop "new design" copy is used. Its fourth
part is Everyday English and its fifth a guide to write; there is no
listening.

The key has no answers for 2.9, 2.11, 3.10, 3.11 or 3.12; they are written
here. 2.8 leaves no gaps on paper (write the question): each item gets a box.
In 3.8 each item gets the words to tap and a box for why; "(extreme)" after
item 2's words was a hint, not a word. 3.1 is lettered as it is: its answers
are already well mixed. 3.5's box lists the answers in the items' order, so
its words are tapped from A to Z instead.

    python3 handouts/i012_digital.py            # writes handouts/i012.json, lists every box
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

DOCX = ("~/Desktop/Handouts/B1+ Intermediate/I01.2 Talk/"
        "I01.2 Talk — handout (new design).docx")
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

# ------------------------------------------------------------ 2 Grammar
boxes_for("2.1", range(1, 9))
FORMS23 = {1: ["think", "am thinking"], 2: ["think", "am thinking"], 3: ["has", "is having"],
           4: ["has", "is having"], 5: ["tastes", "is tasting"], 6: ["tastes", "is tasting"]}
boxes_for("2.3", FORMS23)
for n in range(1, 7):
    h.item_box("2.4", n, where="leader")
h.options_on_lines("2.5")
for n in range(1, 5):
    h.item_box("2.8", n)
for n in range(1, 5):
    h.item_box("2.10", n, where="leader", placeholder="The other tense, and how the meaning changes")
h.options_on_lines("2.11")
h.leaders("2.12", "3  </span>", [(1, W, "Three simple, three continuous")])

# ------------------------------------------------------------ 3 Vocabulary
MEANINGS31, _n = halves("3.1", "a-h")
WB33 = [("speak → the noun (person)", "speaker"), ("speak → the adjective", "spoken"),
        ("improve → the noun (thing)", "improvement"), ("improve → the adjective", "improved"),
        ("fluent → the noun (thing)", "fluency"), ("translate → the noun (thing)", "translation"),
        ("translate → the noun (person)", "translator"), ("pronounce → the noun (thing)", "pronunciation"),
        ("pronounce → the adjective", "pronounced")]
a = h.html.index('<table class="bk">', section("3.3"))
b = h.html.index("</table>", a) + len("</table>")
h.html = h.html[:a] + ('<p style="margin-bottom:6px"><span style="color:#6E6E6E">Example: learn → learning · '
                       'learner</span></p>') + "".join(
    item_p("3.3", n, html.escape(t), "{{box:3.3:%d:140px:}}" % n) for n, (t, _a) in enumerate(WB33, 1)) + h.html[b:]
FORMS36 = {1: ["very", "absolutely"], 2: ["very", "absolutely"], 3: ["really", "very"], 4: ["quite", "absolutely"],
           5: ["very", "absolutely"], 6: ["a bit", "absolutely"]}
boxes_for("3.6", FORMS36)
h.options_on_lines("3.7")
ODD38 = {n: [w.replace(" (extreme)", "") for w in ws] for n, ws in h.odd_one_out("3.8", why="Why?").items()}
SITUATIONS310, _n = halves("3.10", "a-e")
ODD312 = {1: ["pick up", "look up", "give up", "take up"], 2: ["fluency", "accuracy", "learner", "confidence"],
          3: ["starving", "hungry", "exhausted", "furious"], 4: ["translate", "pronounce", "improve", "learning"]}
boxes_for("3.12", ODD312)
h.leaders("3.13", "4.1  </span>", [(1, W, "Four sentences about your learning habits")])

# ------------------------------------------------------------ 4 Everyday English
for n in range(1, 5):
    h.item_box("4.2", n, where="leader")

# ------------------------------------------------------------ 5 Writing
h.leaders("5.1", "</div>", [(1, W, "Write your guide here")])

# ------------------------------------------------------------------ the key
K = {}
for n, a in enumerate("BBBBB", 1):
    K[("1.2", n, 1)] = choose(["A", "B", "C"], a)
for n in range(1, 5):
    K[("1.3", n, 1)] = own()
for n, a in enumerate(["fluent", "a plateau/plateau", "exposure", "accelerates/accelerate/accelerating"], 1):
    K[("1.4", n, 1)] = Q(a)
for n, a in enumerate(["conversation", "fluency", "inefficient", "speaking", "phrases", "plateau"], 1):
    K[("1.5", n, 1)] = Q(a)
AD = {"A": "A · agree", "D": "D · disagree"}
for n in range(1, 5):                             # their opinion
    K[("1.6", n, 1)] = choose(["A", "D"], labels=AD)
SC = {"S": "S · simple", "C": "C · continuous"}
for n, a in enumerate("SCSCSCSC", 1):
    K[("2.1", n, 1)] = choose(["S", "C"], a, labels=SC)
for key, a in (((1, 1), either("is sleeping", "'s sleeping")), ((2, 1), "studies/is studying"),
               ((3, 1), either("don't understand", "do not understand")), ((4, 1), either("is snowing", "'s snowing")),
               ((5, 1), "have"), ((6, 1), either("is working", "'s working")), ((7, 1), "leaves"),
               ((8, 1), "do/are"), ((8, 2), "do/doing")):
    K[("2.2",) + key] = Q(a)
for n, a in enumerate(["think", "am thinking", "has", "is having", "tastes", "is tasting"], 1):
    K[("2.3", n, 1)] = choose(FORMS23[n], a)
TICKED = "✓/correct/tick"
for n, a in enumerate([
        either("I have known him since we were children", "I've known him since we were children", "have known"),
        either(*[s + " in a bank for ten years" for s in ("She has been working", "She's been working",
                                                         "She has worked", "She's worked")]),
        TICKED,
        either("I don't believe that story", "I do not believe that story", "don't believe"),
        TICKED,
        either("They want to move house", "want")], 1):
    K[("2.4", n, 1)] = fix(a)
for n, a in enumerate("BCCCB", 1):
    K[("2.5", n, 1)] = choose(["A", "B", "C", "D"], a)
for n, a in enumerate([either("don't normally take", "do not normally take"), either("is staying", "'s staying"),
                       "usually study"], 1):
    K[("2.6", n, 1)] = Q(a)
for n, a in enumerate([either("'m writing", "am writing"), either("'m doing", "am doing"), "hate", "start",
                       either("'m getting up", "am getting up"), "speaks",
                       either("don't understand", "do not understand"), either("'m improving", "am improving")], 1):
    K[("2.7", n, 1)] = Q(a)
for n, a in enumerate(["Where do you usually study", "What are you reading at the moment",
                       "How often does your family eat together",
                       either("Are you learning any other language this year",
                              "Are you learning any other languages this year")], 1):
    K[("2.8", n, 1)] = write(a)
for n, a in enumerate(["are you doing", either("'m studying", "am studying"), "Are you enjoying",
                       either("don't understand", "do not understand"), "Do you speak", "speak"], 1):
    K[("2.9", n, 1)] = Q(a)
for n in range(1, 5):
    K[("2.10", n, 1)] = own()
for n, a in enumerate("BCBC", 1):
    K[("2.11", n, 1)] = choose(["A", "B", "C", "D"], a)
K[("2.12", 1, 1)] = own()
for n, a in enumerate("bdfhaegc", 1):
    K[("3.1", n, 1)] = choose(MEANINGS31, a)
for key, a in (((1, 1), "picked up"), ((2, 1), "look"), ((2, 2), "up"), ((3, 1), "catch up"), ((4, 1), "give up"),
               ((5, 1), "brushing up on"), ((6, 1), "go over"), ((7, 1), "keep up"), ((8, 1), "drilled")):
    K[("3.2",) + key] = Q(a)
for n, (_t, a) in enumerate(WB33, 1):
    K[("3.3", n, 1)] = Q(a)
for n, a in enumerate(["pronunciation", "improvement", "fluency", "translator", "learner", "speaker"], 1):
    K[("3.4", n, 1)] = Q(a)
BOX35 = ["impossible", "fascinating", "essential", "terrified", "furious", "delighted", "starving", "exhausted"]
for n, a in enumerate(BOX35, 1):                  # the box is in the items' order: tap from A to Z
    K[("3.5", n, 1)] = choose(sorted(BOX35), a)
for n, a in enumerate(["absolutely", "very", "really", "quite", "absolutely", "a bit"], 1):
    K[("3.6", n, 1)] = choose(FORMS36[n], a)
for n, a in enumerate("ABABC", 1):
    K[("3.7", n, 1)] = choose(["A", "B", "C", "D"], a)
for n, a in enumerate(["hesitant", "tired", "give up", "learning"], 1):
    K[("3.8", n, 1)] = choose(ODD38[n], a)
    K[("3.8", n, 2)] = own()
for n, a in enumerate(["picked", "gave", "keep/catch", "terrifying/impossible/exhausting", "look",
                       "confidence/fluency"], 1):
    K[("3.9", n, 1)] = Q(a)
for n, a in enumerate("badce", 1):
    K[("3.10", n, 1)] = choose(SITUATIONS310, a)
for n, a in enumerate(["fluency/confidence", "brush", "picked",
                       "give", "pronunciation/fluency/English/accent/vocabulary/grammar/speaking/writing/spelling/"
                       "listening/reading/confidence/accuracy/French/Spanish/Russian/German/Arabic/Turkish",
                       "keep"], 1):
    K[("3.11", n, 1)] = Q(a)
for n, a in enumerate(["give up", "learner", "hungry", "learning"], 1):
    K[("3.12", n, 1)] = choose(ODD312[n], a)
K[("3.13", 1, 1)] = own()
for n in range(1, 5):
    K[("4.2", n, 1)] = own()
K[("5.1", 1, 1)] = own(control="essay")

if __name__ == "__main__":
    data = h.build(K, "Intermediate", 1, "Unit 1.2 — Talk")
    out = os.path.join(HERE, "i012.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
