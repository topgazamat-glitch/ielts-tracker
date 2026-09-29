"""I07A House and home - Azamat's Intermediate booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(I07A House and home - ANSWER KEY), joined box by box by hand. At this level
the explanations stay English.

Put right here, since a page that marks itself cannot be wrong about its
own answers:
  - 4.4, line 5: the script says "It might be somewhere like Tokyo"; the key
    has must - the box takes what the speaker says;
  - 3.6 lists the particles in · into · out of · over · up · up with, one
    for each line, which leaves "Can you put me up with for two nights?" -
    not English. The list now says up is used twice, and 6 is put me up;
  - 4.2's table numbers its speakers 1, 3, 2, 4 down the columns; it is one
    line a speaker here, in order.
Where the key gives samples but the modal given leaves one answer (2.4), the
box is marked; the open deductions (2.7) are his to read.

What a phone gets that paper does not:
  - taps for every choice: A/B/C, agree or disagree, S/P/N, the meaning, the
    form in 2.9, the building from bottom to top, the stressed syllable,
    the word in 3.5, the word from the box, the odd one out, the other half,
    T/F, whether you hear the t, the loudest word, the three columns;
  - boxes where paper has none: 2.3, 2.5, 2.9, 3.1, 3.5, 3.14, 4.7.

    python3 handouts/i07a_digital.py            # writes handouts/i07a.json, lists every box
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import (Handout, Q, choose, tick, own, write, fix, report,   # noqa: E402
                     BLANK_TAG, plain, ITEM_STYLE, NUM_SPAN, TEXT_SPAN)

DOCX = ("~/Documents/Claude/Material Bank/General English/B1 Intermediate/_NEW BOOKLET STYLE/"
        "I07A House and home — BOOKLET.docx")
W = "95%"
YES_NO = ["✓", "✗"]

h = Handout(DOCX)
TAGS = {int(m.group(1)): m.group(0) for m in BLANK_TAG.finditer(h.html)}


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


def reword(label, old, new):
    at = section(label) + len("%s  </span>" % label)
    end = h.html.index("</p>", at)
    if plain(h.html[at:end]) != old:
        raise SystemExit("%s says %r" % (label, plain(h.html[at:end])))
    style = re.match(r'<span( style="[^"]*")?>', h.html[at:end])
    h.html = h.html[:at] + "<span%s>%s</span>" % (style.group(1) or "", html.escape(new)) + h.html[end:]


def words_of(label, n):
    m = next(m for m in h._items(label) if int(m.group(3)) == n)
    return [w.strip("?!.,—") for w in re.sub(r"^\d+\s+", "", plain(m.group(4))).split() if w.strip("?!.,—")]


# ------------------------------------------------------------ the cover
# This booklet has the older Empower cover; the page reads its name, lessons
# and goals from the cover the other booklets have.
h.cover("UNIT 7  ·  HOUSE AND HOME", "B1+ INTERMEDIATE", "House and home",
        "Lesson 7A   ·   It might be a holiday home",
        "Modals of deduction · describing houses and buildings · alternative places to stay")

# ------------------------------------------------------------ 1 Reading
for n in range(1, 6):
    h.item_box("1.2", n)
h.options_on_lines("1.2")
for n in range(1, 5):
    h.item_box("1.3", n, where="leader")
for n in range(1, 5):
    h.item_box("1.4", n, width="190px", where="leader")
for n in range(1, 5):
    h.item_box("1.6", n, where="leader")

# ------------------------------------------------------------ 2 Grammar
MEANINGS23 = halves("2.3", "a-c")
h.html = h.html.replace(TAGS[25], "", 1)          # 2.4's first line is the worked example
for n in range(1, 7):
    h.item_box("2.5", n, where="leader")
h.html = h.html.replace(TAGS[36], "", 1)          # and 2.7's
FORMS29 = {1: ["can't", "mustn't"], 2: ["must", "might"], 3: ["could", "must"],
           4: ["can't be sleeping", "can't sleeping"], 5: ["may not", "can't"], 6: ["must", "might"]}
for n in FORMS29:
    h.item_box("2.9", n)
h.one_per_line("SIX LINES, SIX MISTAKES", "2.12  </span>", at="text")
h.leaders("2.13", "3.1  </span>", [(1, W, "Six deductions")])

# ------------------------------------------------------------ 3 Vocabulary
WORDS31 = halves("3.1", "a-h")
h.one_per_line("FROM BOTTOM TO TOP", "3.4  </span>", at="text")
# 3.4: the table stacks badly on a phone, so one line a box, the example first
a = h.html.index('<table class="bk">', section("3.4"))
b = h.html.index("</table>", a) + len("</table>")
LINES34 = [("a neighbour — the stressed syllable", ["neigh", "bour"], "neigh"),
           ("the area you live in: neighbour……", None, "hood/neighbourhood/neighborhood"),
           ("that word — the stressed syllable", ["neigh", "bour", "hood"], "neigh"),
           ("comfort — the stressed syllable", ["com", "fort"], "com"),
           ("the adjective: comfort……", None, "able/comfortable"),
           ("that word — the stressed syllable", ["com", "fort", "a", "ble"], "com"),
           ("the adjective from space: spac……", None, "ious/spacious"),
           ("that word — the stressed syllable", ["spa", "cious"], "spa"),
           ("furniture — the stressed syllable", ["fur", "ni", "ture"], "fur"),
           ("to furnish — the stressed syllable", ["fur", "nish"], "fur")]
h.html = h.html[:a] + ('<p style="margin-bottom:6px"><span style="color:#6E6E6E">Example: a resident — '
                       '<b>RES</b>·i·dent · to reside — re·<b>SIDE</b></span></p>') + "".join(
    item_p("3.4", n, html.escape(text), "{{box:3.4:%d:%s:}}" % (n, "60px" if opts else "120px"))
    for n, (text, opts, _a) in enumerate(LINES34, 1)) + h.html[b:]
reword("3.4", "Complete the word-building table. Then mark the stressed syllable, as in the example.",
       "Build the words. Then tap the stressed syllable, as in the example.")
WORDS35 = {2: ["neighbour", "neighbourhood"], 3: ["space", "spacious"], 4: ["rent", "rental"],
           5: ["furnish", "furnished"], 6: ["locate", "location"]}
for n in WORDS35:                                 # 1 is the worked example
    h.item_box("3.5", n)
reword("3.6", "Phrasal verbs. Complete with the correct particle: in · into · out of · over · up · up with .",
       "Phrasal verbs. Complete with the correct particle: in · into · out of · over · up (use up twice).")
ENDS314 = halves("3.14", "a-e")
h.leaders("3.15", "4  </span>", [(1, W, "The home you live in now, and one before")])

# ------------------------------------------------------------ 4 Listening
a = h.html.index('<table class="bk">', section("4.2"))
b = h.html.index("</table>", a) + len("</table>")
h.html = h.html[:a] + "".join(item_p("4.2", k, "Speaker %d" % k, "{{box:4.2:%d:190px:}}" % k)
                              for k in range(1, 5)) + h.html[b:]
LOUD47 = {}
for n in range(1, 5):
    LOUD47[n] = words_of("4.7", n)
    h.item_box("4.7", n)
for n in range(1, 4):
    h.item_box("4.8", n)
h.options_on_lines("4.8")

# ------------------------------------------------------------ 5 Writing
WORDS51 = ["spacious", "run-down", "cosy", "cramped", "spotless", "well kept", "shabby", "modern", "gloomy",
           "impressive"]
a = h.html.index('<table class="bk">', section("5.1"))
b = h.html.index("</table>", a) + len("</table>")
h.html = h.html[:a] + "".join(item_p("5.1", n, html.escape(w), "{{box:5.1:%d:60px:}}" % n)
                              for n, w in enumerate(WORDS51, 1)) + h.html[b:]
h.replace_para("Not every box will be filled", "")
h.html = h.html.replace(TAGS[177], "", 1)         # 5.3's first line is the worked example
h.one_per_line("A BUILDING NEAR THE BAZAAR", "PLAN", at="text")
for n in range(1, 6):
    h.item_box("5.6", n, where="leader")
h.leaders("5.7", "CHECK BEFORE", [(20, W, "Write your description here")])
h.html = h.html.replace(TAGS[196], "", 1)         # the word count: the box counts them itself

# ------------------------------------------------------------------ the key
K = {}
for n, a in enumerate("BCABC", 1):
    K[("1.2", n, 1)] = choose(["A", "B", "C"], a)
for n in range(1, 5):
    K[("1.3", n, 1)] = own()
for n, a in enumerate(["a host/host", "listings/a listing/listing", "a cottage/cottage", "spotless"], 1):
    K[("1.4", n, 1)] = Q(a)
for n, a in enumerate(["money", "industry", "people/experience/neighbourhood", "breakfasts/breakfast", "Hosts",
                       "laundry/cleaning/washing", "alone"], 1):
    K[("1.5", n, 1)] = Q(a)
for n in range(1, 5):
    K[("1.6", n, 1)] = own()
AD = {"A": "A · agree", "D": "D · disagree"}
for n in range(1, 5):                             # their opinion
    K[("1.7", n, 1)] = choose(["A", "D"], labels=AD)
SPN = {"S": "S · sure it is", "P": "P · possible", "N": "N · sure it isn't"}
# 1 must is the example; as numbered 2 might 3 can't 4 could 5 may 6 may not 7 must be 8 can't be
for n, a in zip(range(2, 9), "PNPPPSN"):
    K[("2.1", n, 1)] = choose(["S", "P", "N"], a, labels=SPN)
for n, a in enumerate(["can't", "can't", "must", "could/might/may", "might/may", "can't", "must"], 1):
    K[("2.2", n, 1)] = Q(a)
for n, a in enumerate("baac", 1):
    K[("2.3", n, 1)] = choose(MEANINGS23, a)
for n, a in enumerate([
        "It might be cheaper in the countryside",
        either("That can't be my phone", "It can't be my phone"),
        "The teacher could speak French",
        either("They can't be at home", "They can't be home"),
        "She might not be well"], 2):
    K[("2.4", n, 1)] = write(a)
TICKED = "✓/correct/tick"
for n, a in enumerate([
        either("You must be tired after that journey", "You must be tired"),
        TICKED,
        either("It must be expensive to live here", "It must be expensive"),
        either(*["I think this %s be the key to the front door" % m for m in ("might", "could", "may")]),
        TICKED,
        either("It can't be his flat — he lives on the ground floor", "It can't be his flat - he lives on the ground floor",
               "It can't be his flat, he lives on the ground floor", "It can't be his flat")], 1):
    K[("2.5", n, 1)] = fix(a)
for n, a in enumerate("ACABB", 1):
    K[("2.6", n, 1)] = choose(["A", "B", "C", "D"], a)
for n in range(2, 6):                             # the key gives samples: his to read
    K[("2.7", n, 1)] = own()
for n, a in enumerate(["can't be", "might be building", "must be", "may not want"], 1):
    K[("2.8", n, 1)] = Q(a)
for n, a in enumerate(["can't", "must", "could", "can't be sleeping", "can't", "must"], 1):
    K[("2.9", n, 1)] = choose(FORMS29[n], a)
for n, a in enumerate(["must", "might/may/could", "might/may/could", "can't", "might/may/could", "might/may"], 1):
    K[("2.10", n, 1)] = Q(a)
for n, a in enumerate([
        either("That must be a lovely place to live", "Thanks for the photos! That must be a lovely place to live"),
        either("The building looks old — it must be at least a hundred years old",
               "The building looks old - it must be at least a hundred years old",
               "it must be at least a hundred years old"),
        "You must be very happy there",
        either(*["I think the flat upstairs %s be empty" % m for m in ("might", "may", "could")]),
        either("It can't be cheap, in that neighbourhood", "It can't be cheap in that neighbourhood", "It can't be cheap"),
        either("They can't be building a new one next door — there's no space",
               "They can't be building a new one next door - there's no space",
               "They can't be building a new one next door", "They can't be building a new one")], 1):
    K[("2.11", n, 1)] = write(a)
for n, a in enumerate("ABCB", 1):
    K[("2.12", n, 1)] = choose(["A", "B", "C", "D"], a)
K[("2.13", 1, 1)] = own()
for n, a in enumerate("hdagfbec", 1):
    K[("3.1", n, 1)] = choose(WORDS31, a)
for n, a in enumerate(["attic", "outskirts", "landlord", "terrace", "block of flats/a block of flats", "landing",
                       "cottage", "basement"], 1):
    K[("3.2", n, 1)] = Q(a)
FLOORS = ["the attic", "the basement", "the first floor", "the ground floor", "the roof", "the second floor"]
for key, a in (((1, 1), "the basement"), ((1, 2), "the ground floor"), ((1, 3), "the first floor"),
               ((4, 1), "the second floor"), ((4, 2), "the attic"), ((4, 3), "the roof")):
    K[("3.3",) + key] = choose(FLOORS, a)
for n, (_t, opts, a) in enumerate(LINES34, 1):
    K[("3.4", n, 1)] = choose(opts, a) if opts else Q(a)
for n, a in {2: "neighbourhood", 3: "spacious", 4: "rent", 5: "furnished", 6: "location"}.items():
    K[("3.5", n, 1)] = choose(WORDS35[n], a)
for n, a in enumerate(["into", "out of", "in", "over", "up", "up"], 1):
    K[("3.6", n, 1)] = Q(a)
for n, a in enumerate(["on", "on", "for", "with", "in", "at"], 1):
    K[("3.7", n, 1)] = Q(a)
for n, a in enumerate(["to", "for", "onto/over/out onto/out over", "on", "about", "about"], 1):
    K[("3.8", n, 1)] = Q(a)
BOX39 = ["moving", "renting", "floor", "block", "views", "location", "neighbourhood", "balcony"]
for n, a in enumerate(BOX39, 1):
    K[("3.9", n, 1)] = choose(BOX39, a)
for n, a in enumerate(["cramped/small/tiny", "filthy/dirty", "the top floor/top floor",
                       "to move out/move out", "the outskirts/outskirts/the suburbs/suburbs",
                       "a tenant/tenant"], 1):
    K[("3.10", n, 1)] = Q(a)
for n, a in enumerate("AABCB", 1):
    K[("3.11", n, 1)] = choose(["A", "B", "C", "D"], a)
ODD312 = {1: ["attic", "basement", "landing", "landlord"], 2: ["cottage", "villa", "bungalow", "balcony"],
          3: ["rent", "deposit", "tenant", "terrace"], 4: ["spacious", "cosy", "spotless", "doorbell"]}
for n, a in enumerate(["landlord", "balcony", "terrace", "doorbell"], 1):
    K[("3.12", n, 1)] = choose(ODD312[n], a)
for n, a in enumerate(["floor", "block", "landing", "spacious", "balcony", "view", "neighbourhood"], 1):
    K[("3.13", n, 1)] = Q(a)
for n, a in enumerate("badce", 1):
    K[("3.14", n, 1)] = choose(ENDS314, a)
K[("3.15", 1, 1)] = own()
for n in range(1, 5):                             # a guess: a country
    K[("4.1", n, 1)] = own(control=None)
for k, a in enumerate(["Mexico/Spain/Mexico or Spain", "Japan/Tokyo", "Dubai",
                       "Switzerland/Austria/Slovenia/Europe"], 1):
    K[("4.2", k, 1)] = Q(a)
TF = {"T": "T · true", "F": "F · false"}
for n, a in enumerate("FTTTTF", 1):
    K[("4.3", n, 1)] = choose(["T", "F"], a, labels=TF)
# 5 is might in the script ("It might be somewhere like Tokyo"), not must as the key has it
for n, a in enumerate(["can't", "can't", "could", "must", "might", "can't", "can't", "might"], 1):
    K[("4.4", n, 1)] = Q(a)
HEAR = {"✓": "✓ I hear it", "✗": "✗ it disappears"}
# as numbered: 1 can't get 2 could be 3 must earn 4 might be 5 must enjoy 6 can't always
for n, a in enumerate(["✗", "✗", "✓", "✗", "✓", "✓"], 1):
    K[("4.6", n, 1)] = choose(YES_NO, a, labels=HEAR)
for n, a in enumerate(["belong", "house", "space", "holiday"], 1):
    K[("4.7", n, 1)] = choose(LOUD47[n], a)
for n, a in enumerate("ABB", 1):
    K[("4.8", n, 1)] = choose(["A", "B"], a)
COLS = ["Positive", "Neutral or mixed", "Negative"]
SORT51 = {"spacious": "Neutral or mixed/Positive", "run-down": "Negative", "cosy": "Positive",
          "cramped": "Negative", "spotless": "Positive", "well kept": "Positive", "shabby": "Negative",
          "modern": "Neutral or mixed/Positive", "gloomy": "Negative", "impressive": "Positive"}
for n, w in enumerate(WORDS51, 1):
    K[("5.1", n, 1)] = choose(COLS, SORT51[w])
for n, a in enumerate(["on", "out", "storey/story", "by", "By", "sign"], 1):
    K[("5.2", n, 1)] = Q(a)
for n in range(2, 5):                             # the key gives samples: his to read
    K[("5.3", n, 1)] = own()
for k, a in enumerate(["a block of flats/block of flats", "run-down/run down",
                       "a basement/basement/steps down to a basement"], 1):
    K[("5.4", 1, k)] = Q(a)
for k, a in enumerate(["balcony/a balcony", "spotless", "must", "can't"], 1):
    K[("5.4", 5, k)] = Q(a)
for n in range(1, 6):
    K[("5.6", n, 1)] = own()
K[("5.7", 20, 1)] = own(control="essay")
for n in range(1, 9):                             # the checklist
    K[("5.7", n, 1)] = tick()

if __name__ == "__main__":
    data = h.build(K, "Intermediate", 7, "Unit 7A — House and home")
    out = os.path.join(HERE, "i07a.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
