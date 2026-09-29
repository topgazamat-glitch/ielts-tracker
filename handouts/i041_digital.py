"""I04.1 Personality - Azamat's Intermediate booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(I04.1 Personality - answer key), joined box by box by hand. At this level
the explanations stay English. The Desktop "new design" copy is used. Its
fourth part is Everyday English and its fifth a profile to write; there is no
listening.

Put right here: 3.1's meanings ran almost a-h beside words 1-8 (only pairs
swapped), so they are lettered in a different order. In 2.10 items 4 and 7
the key gives "managed to / was able to", but the sentence already has the
"to": the box wants managed or was (were) able. The word-building table in
3.3 is one line per box. 4.2's ruled lines under each tag are dropped: the
tag is the answer.

    python3 handouts/i041_digital.py            # writes handouts/i041.json, lists every box
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

DOCX = ("~/Desktop/Handouts/B1+ Intermediate/I04.1 Personality/"
        "I04.1 Personality — handout (new design).docx")
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
FORMS23 = {1: ["could", "was able to"], 2: ["could", "managed to"], 3: ["can", "be able to"],
           4: ["can't", "doesn't can"], 5: ["could", "managed to"], 6: ["can", "be able to"]}
boxes_for("2.3", FORMS23)
for n in range(1, 7):
    h.item_box("2.4", n, where="leader")
h.options_on_lines("2.6")
h.options_on_lines("2.14")
h.leaders("2.15", "3  </span>", [(1, W, "Three sentences about now, three about the past")])

# ------------------------------------------------------------ 3 Vocabulary
MEANINGS31, NEW31 = halves("3.1", "a-h", relabel="dgahbfce")
WB33 = [("succeed → the noun (thing)", "success"), ("succeed → the adjective", "successful"),
        ("achieve → the noun (thing)", "achievement"), ("achieve → the noun (person)", "achiever"),
        ("achieve → the adjective", "achievable"), ("compete → the noun (thing)", "competition"),
        ("compete → the noun (person)", "competitor"), ("compete → the adjective", "competitive"),
        ("train → the noun (thing)", "training"), ("train → the noun (person)", "trainer"),
        ("train → the adjective", "trained"), ("skill → the noun (thing)", "skill"),
        ("skill → the adjective", "skilful/skillful/skilled")]
a = h.html.index('<table class="bk">', section("3.3"))
b = h.html.index("</table>", a) + len("</table>")
h.html = h.html[:a] + ('<p style="margin-bottom:6px"><span style="color:#6E6E6E">Example: able → ability · '
                       'able</span></p>') + "".join(
    item_p("3.3", n, html.escape(t), "{{box:3.3:%d:140px:}}" % n) for n, (t, _a) in enumerate(WB33, 1)) + h.html[b:]
FORMS35 = {1: ["skill", "skilful"], 2: ["achieve", "achievement"], 3: ["compete", "competitive"],
           4: ["train", "trainer"], 5: ["able", "ability"], 6: ["succeed", "successful"]}
boxes_for("3.5", FORMS35)
FORMS37 = {1: ["picked", "took"], 2: ["master", "manage"], 3: ["struggle", "fight"], 4: ["keep", "hold"],
           5: ["has", "makes"], 6: ["is", "does"]}
boxes_for("3.7", FORMS37)
h.options_on_lines("3.11")
ODD312 = {1: ["gifted", "talented", "natural", "hopeless"], 2: ["skilled", "trained", "experienced", "promising"],
          3: ["master", "pick up", "learn", "struggle"], 4: ["ability", "achievement", "competitor", "skill"]}
boxes_for("3.12", ODD312)
ENDS314, _n = halves("3.14", "a-e")
h.leaders("3.15", "4  </span>", [(1, W, "Four sentences: what you are good at and what you struggle with")])

# ------------------------------------------------------------ 4 Everyday English
a = section("4.2")
b = h.html.index("4.3  </span>", a)
h.html = h.html[:a] + LEADER_P.sub("", h.html[a:b]) + h.html[b:]

# ------------------------------------------------------------ 5 Writing
h.leaders("5.1", "</div>", [(1, W, "Write your profile here")])

# ------------------------------------------------------------------ the key
K = {}
for n, a in enumerate("BBABB", 1):
    K[("1.2", n, 1)] = choose(["A", "B", "C"], a)
for n in range(1, 5):
    K[("1.3", n, 1)] = own()
for n, a in enumerate(["deliberate practice", "an excuse/excuse", "unwelcome",
                       "an expert performer/expert performer/expert performers/expert"], 1):
    K[("1.4", n, 1)] = Q(a)
for n, a in enumerate(["famous", "good", "talent", "practice/practise", "excuse", "practised/practiced"], 1):
    K[("1.5", n, 1)] = Q(a)
for n in range(1, 5):
    K[("1.6", n, 1)] = own()
AD = {"A": "A · agree", "D": "D · disagree"}
for n in range(1, 5):                             # their opinion
    K[("1.7", n, 1)] = choose(["A", "D"], labels=AD)
GO = {"G": "G · general ability", "O": "O · one occasion"}
for n, a in enumerate("GOGOGOGO", 1):
    K[("2.1", n, 1)] = choose(["G", "O"], a, labels=GO)
NEVER = either("have never been able to", "'ve never been able to", "am never able to", "'m never able to")
for n, a in enumerate([either("couldn't", "could not"), either("is able to", "'s able to"), "managed",
                       "to be able to", "could", either("will be able to", "'ll be able to"), "was able to",
                       NEVER], 1):
    K[("2.2", n, 1)] = Q(a)
for n, a in enumerate(["could", "managed to", "be able to", "can't", "managed to", "be able to"], 1):
    K[("2.3", n, 1)] = choose(FORMS23[n], a)
TICKED = "✓/correct/tick"
for n, a in enumerate([
        either("I want to be able to speak Japanese", "be able to"),
        TICKED,
        either("I managed to pass my driving test on Tuesday", "I was able to pass my driving test on Tuesday",
               "managed to", "was able to"),
        TICKED,
        either("We will be able to help you next week", "We'll be able to help you next week",
               "will be able to"),
        either("I am good at cooking", "I'm good at cooking", "good at cooking")], 1):
    K[("2.4", n, 1)] = fix(a)
for n, a in enumerate(["been", "managed", "at", "be", "Could", "were", "of", "ability", "how", "be"], 1):
    K[("2.5", n, 1)] = Q(a)
for n, a in enumerate("BBACB", 1):
    K[("2.6", n, 1)] = choose(["A", "B", "C", "D"], a)
for n, a in enumerate([
        "She managed to finish the race",
        either("I couldn't hear him at all", "I could not hear him at all"),
        either("He is able to concentrate for hours", "He's able to concentrate for hours"),
        either("I can't sing", "I cannot sing"),
        either("They didn't manage to book a table", "They did not manage to book a table"),
        either("I'd like to be able to drive", "I would like to be able to drive")], 1):
    K[("2.7", n, 1)] = write(a)
for n, a in enumerate([either("couldn't finish", "could not finish"), "managed to convince",
                       either("'ll be able to help", "will be able to help"),
                       either("is very good at", "'s very good at")], 1):
    K[("2.8", n, 1)] = Q(a)
for n, a in enumerate(["could", "managed", either("will be able to", "'ll be able to"),
                       either("couldn't", "could not"), "were able to", NEVER], 1):
    K[("2.9", n, 1)] = Q(a)
for n, a in enumerate(["Can/Could", "managed", "could", "managed/was able", "Could",
                       either("couldn't", "could not", "can't", "cannot"), "managed/were able"], 1):
    K[("2.10", n, 1)] = Q(a)
for n, a in enumerate(["could", either("couldn't", "could not"), "managed",
                       either("am able to", "'m able to"), either("'m not able to", "am not able to"),
                       either("will be able to", "'ll be able to")], 1):
    K[("2.11", n, 1)] = Q(a)
for n, a in enumerate(["of", "ability", "at", "managed"], 1):
    K[("2.12", n, 1)] = Q(a)
for n, a in enumerate([
        either("I want to be able to drive before September", "be able to"),
        either("I managed to pass the theory test last Friday", "I was able to pass the theory test last Friday",
               "managed to", "was able to"),
        either("Will you be able to give me a lesson on Tuesday", "be able to"),
        either("I'm not very good at parking", "I am not very good at parking", "good at parking",
               "at parking")], 1):
    K[("2.13", n, 1)] = write(a)
for n, a in enumerate("BCCB", 1):
    K[("2.14", n, 1)] = choose(["A", "B", "C", "D"], a)
K[("2.15", 1, 1)] = own()
for n, old in enumerate("badcfehg", 1):          # the key's letters, lettered afresh
    K[("3.1", n, 1)] = choose(MEANINGS31, NEW31[old])
for n, a in enumerate(["gifted", "skilled", "competent", "hopeless", "pick up", "master", "struggle with",
                       "keep at"], 1):
    K[("3.2", n, 1)] = Q(a)
for n, (_t, a) in enumerate(WB33, 1):
    K[("3.3", n, 1)] = Q(a)
for n, a in enumerate(["ability", "achievement", "successful", "competitive", "trainer",
                       "skilful/skillful/skilled", "competitors", "succeeded"], 1):
    K[("3.4", n, 1)] = Q(a)
for n, a in enumerate(["skilful", "achievement", "competitive", "trainer", "ability", "successful"], 1):
    K[("3.5", n, 1)] = choose(FORMS35[n], a)
for n, a in enumerate(["at", "for", "at", "of", "to", "up", "with", "at"], 1):
    K[("3.6", n, 1)] = Q(a)
for n, a in enumerate(["picked", "master", "struggle", "keep", "has", "is"], 1):
    K[("3.7", n, 1)] = choose(FORMS37[n], a)
BOX38 = ["talented", "gifted", "competent", "hopeless", "skilled", "expert", "promising", "experienced"]
for n, a in enumerate(["gifted/talented", "competent", "promising", "hopeless", "experienced/skilled", "expert"], 1):
    K[("3.8", n, 1)] = choose(BOX38, a)
for n, a in enumerate(["untalented", "unskilled", "unsuccessful", "incompetent", "unable", "inexperienced"], 1):
    K[("3.9", n, 1)] = Q(a)
for n, a in enumerate(["gift", "gifted/talented", "struggle", "master", "keep"], 1):
    K[("3.10", n, 1)] = Q(a)
for n, a in enumerate("BABBB", 1):
    K[("3.11", n, 1)] = choose(["A", "B", "C", "D"], a)
for n, a in enumerate(["hopeless", "promising", "struggle", "competitor"], 1):
    K[("3.12", n, 1)] = choose(ODD312[n], a)
for n, a in enumerate(["gifted/talented", "expert", "practised/practiced/trained", "pick", "master", "keep"], 1):
    K[("3.13", n, 1)] = Q(a)
for n, a in enumerate("bcaed", 1):
    K[("3.14", n, 1)] = choose(ENDS314, a)
K[("3.15", 1, 1)] = own()
for n, a in enumerate(["can't you", "did she", "haven't they", "is it"], 1):
    K[("4.2", n, 1)] = Q(a)
K[("5.1", 1, 1)] = own(control="essay")

if __name__ == "__main__":
    data = h.build(K, "Intermediate", 4, "Unit 4.1 — Personality")
    out = os.path.join(HERE, "i041.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
