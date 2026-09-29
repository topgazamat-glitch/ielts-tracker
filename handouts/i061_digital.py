"""I06.1 Different cultures - Azamat's Intermediate booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(I06.1 Different cultures - answer key), joined box by box by hand. At this
level the explanations stay English. The Desktop "new design" copy (21 Sep)
is used. It has four parts - there is no writing section - and the older
cover, which goes through Handout.cover.

Put right here, since a page that marks itself cannot be wrong about its
own answers:
  - 4.7: "I never completely got used to it myself" is Speaker 3 in the
    script ("The one thing I still find strange is bedtimes"); the key has
    Speaker 2, who says the opposite of Nigeria's custom. 3 is taken there,
    and "Neither system is wrong" takes Speaker 2 (Nigeria against the
    States) as well as the key's 3.
Where the key gives samples but the word given leaves one answer (2.7), the
box is marked with every reasonable wording.

What a phone gets that paper does not: taps for every choice, the
word-building table one line a box, and boxes for 2.1, 2.3, 2.4, 2.10, 3.5,
3.7 and 3.12.

    python3 handouts/i061_digital.py            # writes handouts/i061.json, lists every box
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import (Handout, Q, choose, tick, own, write, fix, report,   # noqa: E402
                     plain, ITEM_STYLE, NUM_SPAN, TEXT_SPAN)

DOCX = ("~/Desktop/Handouts/B1+ Intermediate/I06.1 Different cultures/"
        "I06.1 Different cultures — handout (new design).docx")
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


def halves(label, letters):
    a = h.html.index('<table class="bk">', section(label))
    b = h.html.index("</table>", a) + len("</table>")
    cells = [plain(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", h.html[a:b], re.S)]
    begins = [re.match(r"(\d+)\s+(.*)", c).groups() for c in cells if re.match(r"\d+\s", c)]
    ends = sorted(re.match(r"([%s])\s+(.*)" % letters, c).groups() for c in cells
                  if re.match(r"[%s]\s" % letters, c))
    h.html = h.html[:a] + key_list(ends) + "".join(
        item_p(label, int(n), html.escape(t, quote=False), "{{box:%s:%s:60px:}}" % (label, n))
        for n, t in begins) + h.html[b:]
    return [l for l, _t in ends]


def choices(label, groups):
    """A chip row for each "a / b" choice in an item."""
    for n in groups:
        h.item_box(label, n)


# ------------------------------------------------------------ the cover
h.cover("UNIT 6  ·  DIFFERENT CULTURES", "B1+ INTERMEDIATE", "Different cultures", "Lesson 6.1   ·   6A + 6C",
        "Unwritten rules · modals of obligation · compound nouns · listening")

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
choices("2.1", range(1, 9))
FORMS23 = {1: ["mustn't", "don't have to"], 2: ["mustn't", "don't have to"], 3: ["must", "had to"],
           4: ["should", "are supposed to"], 5: ["allowed", "supposed"], 6: ["needn't", "mustn't"]}
choices("2.3", FORMS23)
for n in range(1, 7):
    h.item_box("2.4", n, where="leader")
h.options_on_lines("2.6")
FORMS210 = {1: ["mustn't", "don't have to"], 2: ["mustn't", "needn't"], 3: ["must", "had to"],
            4: ["allowed", "supposed"], 5: ["should", "must"], 6: ["aren't allowed", "don't have to"]}
choices("2.10", FORMS210)
h.one_per_line("AN EMAIL TO A VISITING COLLEAGUE", "2.14  </span>", at="text")
h.options_on_lines("2.14")
h.leaders("2.15", "3.1  </span>", [(1, W, "Six rules for visitors")])

# ------------------------------------------------------------ 3 Vocabulary
ENDS31 = halves("3.1", "a-h")
a = h.html.index('<table class="bk">', section("3.3"))
b = h.html.index("</table>", a) + len("</table>")
WB33 = ["tradition", "custom", "politeness", "formality", "respect", "difference", "similarity"]
h.html = h.html[:a] + ('<p style="margin-bottom:6px"><span style="color:#6E6E6E">Example: culture → cultural'
                       '</span></p>') + "".join(
    item_p("3.3", n, "%s → the adjective" % w, "{{box:3.3:%d:120px:}}" % n) for n, w in enumerate(WB33, 1)) + h.html[b:]
FORMS35 = {1: ["polite", "politeness"], 2: ["tradition", "traditional"], 3: ["formal", "formally"],
           4: ["custom", "customary"], 5: ["respect", "respectful"], 6: ["difference", "different"]}
choices("3.5", FORMS35)
FORMS37 = {1: ["make", "do"], 2: ["shake", "give"], 3: ["take", "put"], 4: ["break", "crash"],
           5: ["follow", "obey"], 6: ["make", "keep"]}
choices("3.7", FORMS37)
h.options_on_lines("3.11")
ODD312 = {1: ["greeting", "gesture", "handshake", "taboo"], 2: ["polite", "respectful", "courteous", "rude"],
          3: ["custom", "tradition", "ritual", "costume"],
          4: ["dress code", "body language", "small talk", "culture shock"]}
choices("3.12", ODD312)
ENDS314 = halves("3.14", "a-e")
h.leaders("3.15", "4.1  </span>", [(1, W, "Four sentences about customs in your country")])

# ------------------------------------------------------------ 4 Listening
h.grid_rows("4.2")
h.leaders("4.8", "</div>", [(n, W, "Speaker %d" % n) for n in range(1, 4)])

# ------------------------------------------------------------------ the key
K = {}
for n, a in enumerate("BABAB", 1):
    K[("1.2", n, 1)] = choose(["A", "B", "C"], a)
for n in range(1, 5):
    K[("1.3", n, 1)] = own()
for n, a in enumerate(["trivial", "modest", "a newcomer/newcomer/newcomers", "interpret/to interpret"], 1):
    K[("1.4", n, 1)] = Q(a)
for n, a in enumerate(["writes", "done", "interpret", "apps", "agree", "notice"], 1):
    K[("1.5", n, 1)] = Q(a)
for n in range(1, 5):
    K[("1.6", n, 1)] = own()
AD = {"A": "A · agree", "D": "D · disagree"}
for n in range(1, 5):                             # their opinion
    K[("1.7", n, 1)] = choose(["A", "D"], labels=AD)
FN = {"F": "F · forbidden", "N": "N · not necessary"}
for n, a in enumerate("FNFNFNFN", 1):
    K[("2.1", n, 1)] = choose(["F", "N"], a, labels=FN)
for key, a in (((1, 1), either("don't have to", "do not have to")), ((2, 1), "must"), ((3, 1), "had to"),
               ((4, 1), "should"), ((5, 1), either("aren't allowed to", "are not allowed to")), ((6, 1), "Do"),
               ((6, 2), "have to"), ((7, 1), "was supposed to"), ((8, 1), either("mustn't", "must not"))):
    K[("2.2",) + key] = Q(a)
for n, a in enumerate(["don't have to", "mustn't", "had to", "are supposed to", "allowed", "needn't"], 1):
    K[("2.3", n, 1)] = choose(FORMS23[n], a)
TICKED = "✓/correct/tick"
for n, a in enumerate([
        "You must show your passport at the gate",
        either("You mustn't smoke anywhere in the hospital", "You must not smoke anywhere in the hospital",
               "You aren't allowed to smoke anywhere in the hospital"),
        TICKED,
        "I had to work last weekend",
        TICKED,
        either("Do I have to book a table", "Do I need to book a table")], 1):
    K[("2.4", n, 1)] = fix(a)
for n, a in enumerate(["have/need", "mustn't/can't", "have/need", "supposed", "Are", "should", "had", "needn't"], 1):
    K[("2.5", n, 1)] = Q(a)
for n, a in enumerate("BCBCA", 1):
    K[("2.6", n, 1)] = choose(["A", "B", "C", "D"], a)
for n, a in enumerate([
        either("You have to book in advance", "We have to book in advance"),
        either("You mustn't smoke here", "You must not smoke here"),
        either("You needn't bring food", "You don't need to bring food", "You do not need to bring food",
               "You need not bring food"),
        either("You're allowed to take photographs", "You are allowed to take photographs",
               "You're allowed to take photos", "You are allowed to take photos", "Photography is allowed"),
        either("We're supposed to start at nine", "We are supposed to start at nine"),
        "You should take a gift"], 1):
    K[("2.7", n, 1)] = write(a)
for n, a in enumerate([either("don't have to wear", "do not have to wear"), either("mustn't feed", "must not feed"),
                       "had to leave", either("aren't allowed to smoke", "are not allowed to smoke")], 1):
    K[("2.8", n, 1)] = Q(a)
for key, a in (((1, 1), "have to"), ((2, 1), "had to"), ((3, 1), either("don't need", "do not need")),
               ((4, 1), either("aren't allowed to", "are not allowed to")), ((5, 1), "Are"),
               ((5, 2), "supposed to"), ((6, 1), either("shouldn't", "should not"))):
    K[("2.9",) + key] = Q(a)
for n, a in enumerate(["don't have to", "mustn't", "had to", "allowed", "should", "aren't allowed"], 1):
    K[("2.10", n, 1)] = choose(FORMS210[n], a)
NOT_NEEDED = either("don't have to", "needn't", "do not have to", "don't need to")
for n, a in enumerate([either("must", "have to"), NOT_NEEDED, "should", NOT_NEEDED,
                       either("mustn't", "must not", "shouldn't"), either("mustn't", "must not", "shouldn't")], 1):
    K[("2.11", n, 1)] = Q(a)
for n, a in enumerate(["have/need", "supposed", "mustn't/can't", "had"], 1):
    K[("2.12", n, 1)] = Q(a)
for n, a in enumerate([
        "You must bring your passport to the office",
        either("You mustn't be late — the meeting starts exactly at nine",
               "You mustn't be late - the meeting starts exactly at nine", "You mustn't be late",
               "You must not be late"),
        either("Yesterday I had to stay until eight o'clock", "I had to stay until eight o'clock"),
        "Do I have to book the meeting room myself"], 1):
    K[("2.13", n, 1)] = write(a)
for n, a in enumerate("BCBA", 1):
    K[("2.14", n, 1)] = choose(["A", "B", "C", "D"], a)
K[("2.15", 1, 1)] = own()
for n, a in enumerate("caegdhfb", 1):
    K[("3.1", n, 1)] = choose(ENDS31, a)
for n, a in enumerate(["eye contact", "culture shock", "dress code", "small talk", "business card",
                       "table manners", "dinner party", "body language"], 1):
    K[("3.2", n, 1)] = Q(a)
for n, a in enumerate(["traditional", "customary", "polite", "formal", "respectful", "different", "similar"], 1):
    K[("3.3", n, 1)] = Q(a)
for n, a in enumerate(["customary", "cultural", "traditional", "respect", "formal", "similarities",
                       "impolite/rude", "different"], 1):
    K[("3.4", n, 1)] = Q(a)
for n, a in enumerate(["politeness", "traditional", "formally", "customary", "respect", "different"], 1):
    K[("3.5", n, 1)] = choose(FORMS35[n], a)
for n, a in enumerate(["dress", "table", "business", "culture", "body", "small", "contact", "dinner"], 1):
    K[("3.6", n, 1)] = Q(a)
for n, a in enumerate(["make", "shake", "take", "break", "follow", "keep/make"], 1):
    K[("3.7", n, 1)] = choose(FORMS37[n], a)
BOX38 = ["greeting", "gesture", "custom", "etiquette", "taboo", "hospitality", "ritual", "manners"]
for n, a in enumerate(["hospitality", "taboo", "greeting", "etiquette/manners", "gesture", "ritual/custom"], 1):
    K[("3.8", n, 1)] = choose(BOX38, a)
for n, a in enumerate(["impolite/rude", "informal", "different/dissimilar", "disrespectful",
                       "modern/untraditional/non-traditional", "unusual"], 1):
    K[("3.9", n, 1)] = Q(a)
for n, a in enumerate(["manners", "stress", "customary", "small"], 1):
    K[("3.10", n, 1)] = Q(a)
for n, a in enumerate("BBCBA", 1):
    K[("3.11", n, 1)] = choose(["A", "B", "C", "D"], a)
for n, a in enumerate(["taboo", "rude", "costume", "culture shock"], 1):
    K[("3.12", n, 1)] = choose(ODD312[n], a)
for n, a in enumerate(["custom/rule/tradition", "code", "talk", "taboo", "hospitality", "funny/amusing"], 1):
    K[("3.13", n, 1)] = Q(a)
for n, a in enumerate("badce", 1):
    K[("3.14", n, 1)] = choose(ENDS314, a)
K[("3.15", 1, 1)] = own()
for n in range(1, 7):                             # what they expect: nothing to mark
    K[("4.1", n, 1)] = tick()
for n, a in enumerate(["Brazil", "Nigeria", "Britain/the UK/UK/England/the United Kingdom"]):
    K[("4.2", 2 * n + 1, 1)] = Q(a)
    K[("4.2", 2 * n + 2, 1)] = own(control=None)
TF = {"T": "T · true", "F": "F · false"}
for n, a in enumerate("FTFTTF", 1):
    K[("4.3", n, 1)] = choose(["T", "F"], a, labels=TF)
for key, a in (((1, 1), either("don't have to", "do not have to")), ((2, 1), either("shouldn't", "should not")),
               ((3, 1), "have"), ((4, 1), "supposed"), ((5, 1), either("mustn't", "must not")), ((5, 2), "must"),
               ((6, 1), either("mustn't", "must not"))):
    K[("4.4",) + key] = Q(a)
SPK = {"1": "1 · Brazil", "2": "2 · Nigeria", "3": "3 · Britain"}
# 3 takes speaker 2 as well; 5 is speaker 3 in the script, not 2 as the key has it
for n, a in enumerate(["1", "2", "2/3", "1", "3", "3"], 1):
    K[("4.7", n, 1)] = choose(["1", "2", "3"], a, labels=SPK)
for n in range(1, 4):
    K[("4.8", n, 1)] = own()

if __name__ == "__main__":
    data = h.build(K, "Intermediate", 6, "Unit 6A & 6C — Different cultures")
    out = os.path.join(HERE, "i061.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
