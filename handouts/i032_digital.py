"""I03.2 Relationships - Azamat's Intermediate booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(I03.2 Relationships - answer key), joined box by box by hand. At this level
the explanations stay English. The Desktop "new design" copy is used. Its
fourth part is Everyday English and its fifth a description to write; there
is no listening.

Put right here: 3.1's meanings ran almost a-h beside words 1-8 (only pairs
swapped), so they are lettered in a different order. 2.1 ("tick where would
is possible") is a yes or no for every sentence, so the ones left alone are
marked too. In 2.3 item 2 the key has would, but used to is just as right
("Every Friday we used to meet"): both count. In 2.13 item 1 the key allows
"A with used to", but A is "used" and "We used go camping" is wrong: C only.
The word-building table in 3.3 is one line per box, and 3.9's
words to replace are underlined, as its instruction says they are.

    python3 handouts/i032_digital.py            # writes handouts/i032.json, lists every box
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

DOCX = ("~/Desktop/Handouts/B1+ Intermediate/I03.2 Relationships/"
        "I03.2 Relationships — handout (new design).docx")
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
FORMS23 = {1: ["used to", "would"], 2: ["used to", "would"], 3: ["Did you use to", "Did you used to"],
           4: ["didn't use to", "didn't used to"], 5: ["usually", "used to"], 6: ["would", "used to"]}
boxes_for("2.3", FORMS23)
for n in range(1, 7):
    h.item_box("2.4", n, where="leader")
h.options_on_lines("2.6")
h.options_on_lines("2.13")
h.leaders("2.14", "3  </span>", [(1, W, "Three sentences with used to, three with usually")])

# ------------------------------------------------------------ 3 Vocabulary
MEANINGS31, NEW31 = halves("3.1", "a-h", relabel="dgahbfce")
WB33 = [("parent → the noun (thing)", "parenthood"), ("parent → the adjective", "parental"),
        ("child → the noun (thing)", "childhood"), ("child → the adjective", "childish/childlike"),
        ("neighbour → the noun (thing)", "neighbourhood/neighborhood"),
        ("neighbour → the adjective", "neighbourly/neighborly"),
        ("care → the noun (thing)", "care"), ("care → the noun (person)", "carer/caregiver"),
        ("care → the adjective", "caring"), ("depend → the noun (thing)", "dependence/dependency"),
        ("depend → the adjective", "dependent")]
a = h.html.index('<table class="bk">', section("3.3"))
b = h.html.index("</table>", a) + len("</table>")
h.html = h.html[:a] + ('<p style="margin-bottom:6px"><span style="color:#6E6E6E">Example: marry → marriage · '
                       'married</span></p>') + "".join(
    item_p("3.3", n, html.escape(t), "{{box:3.3:%d:140px:}}" % n) for n, (t, _a) in enumerate(WB33, 1)) + h.html[b:]
FORMS35 = {1: ["marry", "married"], 2: ["child", "childish"], 3: ["child", "childhood"], 4: ["care", "caring"],
           5: ["neighbour", "neighbourhood"], 6: ["depend", "dependent"]}
boxes_for("3.5", FORMS35)
FORMS37 = {1: ["takes", "brings"], 2: ["split", "put"], 3: ["looked", "grew"], 4: ["put", "take"],
           5: ["got", "brought"], 6: ["grew", "caught"]}
boxes_for("3.7", FORMS37)
a, b = section("3.9"), section("3.10")          # the words to replace, underlined as the paper says
part = h.html[a:b]
for words in ("her sons", "the children", "the noise", "my mother", "Dilnoza", "her aunt"):
    part = part.replace(" %s." % words, " <u>%s</u>." % words, 1)
part = re.sub(r'(<input class="bk-blank"[^>]*style="width:)\d+px', r"\g<1>150px", part)
h.html = h.html[:a] + part + h.html[b:]
h.options_on_lines("3.10")
ODD311 = {1: ["bring up", "raise", "look after", "split up"], 2: ["relative", "in-law", "colleague", "stepsister"],
          3: ["caring", "supportive", "loyal", "childish"], 4: ["grow up", "get together", "meet up", "catch up"]}
boxes_for("3.11", ODD311)
ENDS313, _n = halves("3.13", "a-e")
h.leaders("3.14", "4.1  </span>", [(1, W, "Four sentences about your family")])

# ------------------------------------------------------------ 4 Everyday English
for n in range(1, 5):
    h.item_box("4.2", n, where="leader", placeholder="Echo question, then one more")

# ------------------------------------------------------------ 5 Writing
h.leaders("5.1", "</div>", [(1, W, "Write your description here")])

# ------------------------------------------------------------------ the key
K = {}
for n, a in enumerate("BBBBA", 1):
    K[("1.2", n, 1)] = choose(["A", "B", "C"], a)
for n in range(1, 5):
    K[("1.3", n, 1)] = own()
for n, a in enumerate(["the exception/exception", "repetition", "bleak",
                       "network/close network/a network/their close network"], 1):
    K[("1.4", n, 1)] = Q(a)
for n, a in enumerate(["phone/call/ring", "argument", "shorter", "network/friends", "repetition",
                       "repaired/fixed/mended"], 1):
    K[("1.5", n, 1)] = Q(a)
for n in range(1, 5):
    K[("1.6", n, 1)] = own()
AD = {"A": "A · agree", "D": "D · disagree"}
for n in range(1, 5):                             # their opinion
    K[("1.7", n, 1)] = choose(["A", "D"], labels=AD)
YN = {"yes": "✓ would is possible", "no": "✗ only used to"}
for n in range(1, 9):
    K[("2.1", n, 1)] = choose(["yes", "no"], "yes" if n % 2 else "no", labels=YN)
DIDNT = lambda verb: either("didn't use to " + verb, "did not use to " + verb)
for key, a in (((1, 1), "used to phone"), ((2, 1), DIDNT("like")), ((3, 1), "Did"), ((3, 2), "use to live"),
               ((4, 1), "used to spend"), ((5, 1), DIDNT("have")), ((6, 1), "used to be"),
               ((7, 1), "Did"), ((7, 2), "use to eat"), ((8, 1), DIDNT("understand"))):
    K[("2.2",) + key] = Q(a)
for n, a in enumerate(["used to", "would/used to", "Did you use to", "didn't use to", "usually", "used to"], 1):
    K[("2.3", n, 1)] = choose(FORMS23[n], a)
TICKED = "✓/correct/tick"
for n, a in enumerate([
        either("Did you use to work here", "use to"),
        TICKED,
        either("I used to be very shy as a child", "used to be"),
        TICKED,
        either("She used to live in Bukhara", "used to"),
        either("I used to phone her every day", "used to phone", "used to")], 1):
    K[("2.4", n, 1)] = fix(a)
for n, a in enumerate(["used", "use", "Did", "would", "used", "used", "used", "used"], 1):
    K[("2.5", n, 1)] = Q(a)
for n, a in enumerate("BABCB", 1):
    K[("2.6", n, 1)] = choose(["A", "B", "C", "D"], a)
for n, a in enumerate([
        either("I used to play the piano", "I used to play the piano as a child"),
        "She used to live in Moscow",
        either("We didn't use to have a television", "We did not use to have a television",
               "We didn't use to have a TV"),
        "Did you use to walk to school",
        "They used to be very close friends",
        either("I didn't use to understand her at all", "I did not use to understand her at all")], 1):
    K[("2.7", n, 1)] = write(a)
for n, a in enumerate(["used to call/used to phone/used to ring", "would visit",
                       either("'m used to getting", "am used to getting"), DIDNT("like")], 1):
    K[("2.8", n, 1)] = Q(a)
for n, a in enumerate(["saw", "used to spend/would spend", "used to be", "called", "would read/used to read",
                       DIDNT("have")], 1):
    K[("2.9", n, 1)] = Q(a)
for n, a in enumerate(["used to phone/would phone", "used to stand/would stand", "would meet/used to meet",
                       "moved", "got", "usually send/send"], 1):
    K[("2.10", n, 1)] = Q(a)
for n, a in enumerate(["used", "use", "would", "use"], 1):
    K[("2.11", n, 1)] = Q(a)
for n, a in enumerate([
        either("Did you use to live in Samarkand", "use to"),
        either("I used to be very shy when I was young", "used to be"),
        either("She used to call me every week", "used to"),
        either("I didn't use to enjoy studying at all", "I didn't use to enjoy studying", "use to")], 1):
    K[("2.12", n, 1)] = write(a)
for n, a in enumerate("CBAC", 1):
    K[("2.13", n, 1)] = choose(["A", "B", "C", "D"], a)
K[("2.14", 1, 1)] = own()
for n, old in enumerate("badcfehg", 1):          # the key's letters, lettered afresh
    K[("3.1", n, 1)] = choose(MEANINGS31, NEW31[old])
for n, a in enumerate(["takes after", "brought up", "get together", "split up", "look after", "grew up",
                       "caught up", "put up with"], 1):
    K[("3.2", n, 1)] = Q(a)
for n, (_t, a) in enumerate(WB33, 1):
    K[("3.3", n, 1)] = Q(a)
for n, a in enumerate(["married", "childhood", "caring", "neighbourhood/neighborhood", "childish", "Parental",
                       "dependent", "carer/caregiver"], 1):
    K[("3.4", n, 1)] = Q(a)
for n, a in enumerate(["married", "childish", "childhood", "caring", "neighbourhood", "dependent"], 1):
    K[("3.5", n, 1)] = choose(FORMS35[n], a)
for n, a in enumerate(["up", "after", "after", "up", "up", "together", "up", "up"], 1):
    K[("3.6", n, 1)] = Q(a)
for n, a in enumerate(["takes", "split", "looked", "put", "got", "grew"], 1):
    K[("3.7", n, 1)] = choose(FORMS37[n], a)
BOX38 = ["a relative", "an in-law", "a colleague", "an acquaintance", "a partner", "a neighbour", "a classmate",
         "a stepbrother"]
for n, a in enumerate(["an acquaintance", "a colleague", "an in-law", "a partner", "a stepbrother",
                       "a relative"], 1):
    K[("3.8", n, 1)] = choose(BOX38, a)
for n, (tail, subject) in enumerate([("brought them up", "She"), ("looks after them", "He"),
                                     ("put up with it", "They"), ("take after her", "I"),
                                     ("caught up with her", "We"), ("looks up to her", "She")], 1):
    K[("3.9", n, 1)] = Q(either(tail, subject + " " + tail))
for n, a in enumerate("ABACB", 1):
    K[("3.10", n, 1)] = choose(["A", "B", "C", "D"], a)
for n, a in enumerate(["split up", "colleague", "childish", "grow up"], 1):
    K[("3.11", n, 1)] = choose(ODD311[n], a)
for n, a in enumerate(["up", "after", "after", "up", "together", "up"], 1):
    K[("3.12", n, 1)] = Q(a)
for n, a in enumerate("badce", 1):
    K[("3.13", n, 1)] = choose(ENDS313, a)
K[("3.14", 1, 1)] = own()
for n in range(1, 5):
    K[("4.2", n, 1)] = own()
K[("5.1", 1, 1)] = own(control="essay")

if __name__ == "__main__":
    data = h.build(K, "Intermediate", 3, "Unit 3.2 — Relationships")
    out = os.path.join(HERE, "i032.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
