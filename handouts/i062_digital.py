"""I06.2 Different cultures - Azamat's Intermediate booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(I06.2 Different cultures - answer key), joined box by box by hand. At this
level the explanations stay English. The Desktop "new design" copy (21 Sep)
is used; its exercises and boxes are the Material Bank copy's.

His own revision brief (I06.2 - REVISION BRIEF.md) lists defects in this
booklet; the ones a digital copy can mend are mended here:
  - 1.2 keyed B five times. Two items have their options reordered (3 and 5)
    so the answers run B B A B C, as the brief suggests;
  - 2.9's box promised six mistakes and printed four lines - it says four;
  - 3.1's meanings ran a-h beside words 1-8, so every answer was the next
    letter; the meanings are lettered in a different order here;
  - 5.5 had ten words for twelve cells - it is one line a word.
Where the key gives samples but the word given leaves one answer (2.6, 5.7),
the box is marked with every reasonable wording; 2.5 item 1 ("much ______
than I thought") takes any comparative, so it is his to read.

What a phone gets that paper does not: taps for every choice, the whole
word-building table one line a box, and boxes for 2.4, 2.8, 3.5, 3.7, 3.12,
4.6 and the review's six areas.

    python3 handouts/i062_digital.py            # writes handouts/i062.json, lists every box
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import (Handout, Q, choose, tick, own, write, fix, report,   # noqa: E402
                     BLANK_TAG, ITEM_P, plain, ITEM_STYLE, NUM_SPAN, TEXT_SPAN)

DOCX = ("~/Desktop/Handouts/B1+ Intermediate/I06.2 Different cultures/"
        "I06.2 Different cultures — handout (new design).docx")
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


def halves(label, letters, relabel=None):
    """The endings first, as a key; then each beginning with the letters to
    tap. relabel gives each ending a new letter, in the endings' order."""
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


def swap_in_item(label, n, one, other):
    """Swap two options' words in every paragraph of one item."""
    for m in reversed([m for m in ITEM_P.finditer(h.html) if m.group(2) == label and int(m.group(3)) == n]):
        guts = m.group(4).replace(one, "\0").replace(other, one).replace("\0", other)
        h.html = h.html[:m.start()] + m.group(1) + guts + "</p>" + h.html[m.end():]


def lines_for_table(label, lines, nth_table=0):
    """Swap the nth table after an exercise for one line a box."""
    a = h.html.index('<table class="bk">', section(label))
    for _ in range(nth_table):
        a = h.html.index('<table class="bk">', h.html.index("</table>", a))
    b = h.html.index("</table>", a) + len("</table>")
    h.html = h.html[:a] + "".join(item_p(label, n, html.escape(t), "{{box:%s:%d:%s:}}" % (label, n, w))
                                  for n, (t, w) in enumerate(lines, 1)) + h.html[b:]


def words_of(label, n):
    m = next(m for m in h._items(label) if int(m.group(3)) == n)
    return [w.strip("?!.,—") for w in re.sub(r"^\d+\s+", "", plain(m.group(4))).split() if w.strip("?!.,—")]


# ------------------------------------------------------------ the cover
h.cover("UNIT 6  ·  DIFFERENT CULTURES", "B1+ INTERMEDIATE", "Different cultures", "Lesson 6.2   ·   6B + 6D",
        "Food and taste · comparatives and superlatives · describing food · a café review")

# ------------------------------------------------------------ 1 Reading
swap_in_item("1.2", 3, "being fooled", "genuinely affected by hunger")
swap_in_item("1.2", 5, "the situation as well", "nothing that can be measured")
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
for n in range(1, 7):
    h.item_box("2.4", n, where="leader")
FORMS28 = {1: ["more salty", "saltier"], 2: ["very cheaper", "much cheaper"], 3: ["the most bad", "the worst"],
           4: ["more big", "bigger"], 5: ["the most careful", "the more careful"], 6: ["best", "the best"]}
for n in FORMS28:
    h.item_box("2.8", n)
h.html = h.html.replace("A CAFÉ REVIEW WITH SIX MISTAKES", "A CAFÉ REVIEW WITH FOUR MISTAKES", 1)
h.one_per_line("A CAFÉ REVIEW WITH FOUR MISTAKES", "2.10  </span>", at="text")
h.leaders("2.11", "3.1  </span>", [(1, W, "Five sentences comparing food")])

# ------------------------------------------------------------ 3 Vocabulary
MEANINGS31, NEW31 = halves("3.1", "a-h", relabel="dgahbfce")
WB33 = [("spice → the adjective", "120px"), ("boil → the adjective", "120px"), ("cream → the adjective", "120px"),
        ("grill → the adjective", "120px"), ("taste → the adjective", "120px"), ("bake → the adjective", "120px"),
        ("oil → the adjective", "120px"), ("steam → the adjective", "120px")]
lines_for_table("3.3", WB33)
h.html = h.html.replace('<p data-item="3.3:1"',
                        '<p style="margin-bottom:6px"><span style="color:#6E6E6E">Example: salt → salty · '
                        'fry → fried</span></p><p data-item="3.3:1"', 1)
FORMS35 = {1: ["spice", "spicy"], 2: ["boil", "boiled"], 3: ["cream", "creamy"], 4: ["taste", "tasteless"],
           5: ["grill", "grilled"], 6: ["oil", "oily"]}
for n in FORMS35:
    h.item_box("3.5", n)
FORMS37 = {1: ["cut", "chop"], 2: ["Boil", "Bake"], 3: ["do", "have"], 4: ["make", "do"], 5: ["took", "had"],
           6: ["came", "arrived"]}
for n in FORMS37:
    h.item_box("3.7", n)
ODD312 = {1: ["sweet", "salty", "sour", "crunchy"], 2: ["boiled", "grilled", "roasted", "greasy"],
          3: ["starter", "main course", "dessert", "recipe"], 4: ["delicious", "tasty", "disgusting", "mouth-watering"]}
for n in ODD312:
    h.item_box("3.12", n)
ENDS314, _n = halves("3.14", "a-e")
h.leaders("3.15", "4.1  </span>", [(1, W, "The best and the worst meal you have eaten")])

# ------------------------------------------------------------ 4 Listening
LOUD46 = {}
for n in range(1, 5):
    LOUD46[n] = words_of("4.6", n)
    h.item_box("4.6", n)
for n in range(1, 4):
    h.item_box("4.7", n)
h.options_on_lines("4.7")

# ------------------------------------------------------------ 5 Writing
WORDS55 = ["delicious", "overpriced", "fresh", "half cold", "reasonably friendly", "completely tasteless",
           "fairly pleasant", "wonderful", "overcooked", "a bit noisy"]
lines_for_table("5.5", [(w, "60px") for w in WORDS55])
for n in range(1, 6):
    h.item_box("5.10", n, where="leader")
h.leaders("5.11", "CHECK BEFORE", [(20, W, "Write your review here")])
h.html = h.html.replace(TAGS[221], "", 1)         # the word count: the box counts them itself

# ------------------------------------------------------------------ the key
K = {}
for n, a in enumerate("BBABC", 1):
    K[("1.2", n, 1)] = choose(["A", "B", "C"], a)
for n in range(1, 5):
    K[("1.3", n, 1)] = own()
for n, a in enumerate(["rate/to rate/rated", "surroundings", "recall/to recall", "an ingredient/ingredient"], 1):
    K[("1.4", n, 1)] = Q(a)
for n, a in enumerate(["best", "tastier", "surroundings", "strongest", "recall/remember", "disappointment"], 1):
    K[("1.5", n, 1)] = Q(a)
for n in range(1, 5):
    K[("1.6", n, 1)] = own()
AD = {"A": "A · agree", "D": "D · disagree"}
for n in range(1, 5):                             # their opinion
    K[("1.7", n, 1)] = choose(["A", "D"], labels=AD)
SL = {"S": "S · short", "L": "L · long"}
# as numbered: 1 cheap 2 delicious 3 spicy 4 convenient 5 sweet 6 expensive 7 tasty 8 disgusting
for n, a in enumerate("SLSLSLSL", 1):
    K[("2.1", n, 1)] = choose(["S", "L"], a, labels=SL)


def sup(word):
    return either("the " + word, word)


PAIRS22 = {1: ("cheaper", sup("cheapest")), 2: ("better", sup("best")), 3: ("spicier", sup("spiciest")),
           4: ("worse", sup("worst")), 5: ("more expensive", sup("most expensive")),
           6: ("further/farther", either(sup("furthest"), sup("farthest"))), 7: ("bigger", sup("biggest")),
           8: ("more delicious", sup("most delicious"))}
for n, (comp, sup_) in PAIRS22.items():
    K[("2.2", n, 1)] = Q(comp)
    K[("2.2", n, 2)] = Q(sup_)
for n, a in enumerate(["cheaper", "the best", "more convenient", "the highest", "saltier", "the worst",
                       "more relaxing", "further/farther"], 1):
    K[("2.3", n, 1)] = Q(a)
TICKED = "✓/correct/tick"
for n, a in enumerate([
        "Life is easier now than it used to be",
        TICKED,
        "It was the best day of my holiday",
        TICKED,
        "My town will be bigger in twenty years",
        either("It's the most beautiful city in the country", "It is the most beautiful city in the country")], 1):
    K[("2.4", n, 1)] = fix(a)
K[("2.5", 1, 1)] = own(control=None)              # any comparative fits: his to read
for n, a in {2: "the", 3: "as", 4: "most", 5: "by", 6: "higher/more/bigger/lower/cheaper/less",
             7: "nearly/quite", 8: "best"}.items():
    K[("2.5", n, 1)] = Q(a)
for n, a in enumerate([
        either("isn't as spicy as the soup", "is not as spicy as the soup"),
        either("This is the cheapest restaurant in town", "This restaurant is the cheapest in town",
               "This is the cheapest restaurant in the town", "It's the cheapest restaurant in town"),
        either(*[p + " the best meal I" + v + " ever eaten" for p in ("It's", "It is", "This is", "That's", "That was")
                 for v in (" have", "'ve")]),
        either("The café is slightly more expensive than the bakery",
               "The cafe is slightly more expensive than the bakery"),
        "Restaurant food is much better than machine food",
        either("This is the worst thing on the menu", "This is the worst dish on the menu",
               "It's the worst thing on the menu", "It is the worst thing on the menu")], 1):
    K[("2.6", n, 1)] = write(a)
for n, a in enumerate(["was more expensive than/is more expensive than", "is better than",
                       "isn't as hot as/is not as hot as", "I've ever had/I have ever had"], 1):
    K[("2.7", n, 1)] = Q(a)
for n, a in enumerate(["saltier", "much cheaper", "the worst", "bigger", "the most careful", "the best"], 1):
    K[("2.8", n, 1)] = choose(FORMS28[n], a)
for n, a in enumerate([
        either("This is the most popular café in our street", "This is the most popular cafe in our street",
               "the most popular"),
        either("The coffee is much cheaper than at the bakery", "much cheaper"),
        either("It was the best breakfast I have had this month", "the best breakfast"),
        either("The staff are the kindest people in the town", "the kindest people")], 1):
    K[("2.9", n, 1)] = write(a)
for n, a in enumerate("BBAC", 1):
    K[("2.10", n, 1)] = choose(["A", "B", "C", "D"], a)
K[("2.11", 1, 1)] = own()
for n in range(1, 9):                             # word n goes with its own meaning, now lettered afresh
    K[("3.1", n, 1)] = choose(MEANINGS31, NEW31["abcdefgh"[n - 1]])
for n, a in enumerate(["tough", "bland", "sour", "tender", "crunchy", "greasy", "rich", "raw"], 1):
    K[("3.2", n, 1)] = Q(a)
for n, a in enumerate(["spicy", "boiled", "creamy", "grilled", "tasty", "baked", "oily", "steamed"], 1):
    K[("3.3", n, 1)] = Q(a)
for n, a in enumerate(["spicy", "creamy", "grilled", "steamed", "tasteless", "oily", "baked", "salt"], 1):
    K[("3.4", n, 1)] = Q(a)
for n, a in enumerate(["spicy", "boiled", "creamy", "tasteless", "grilled", "oily"], 1):
    K[("3.5", n, 1)] = choose(FORMS35[n], a)
for n, a in enumerate(["starving", "bowl", "eat", "three-course/three course", "local/traditional", "street",
                       "light", "under/under-"], 1):
    K[("3.6", n, 1)] = Q(a)
for n, a in enumerate(["chop/cut", "Boil", "have", "make", "took/had", "came"], 1):
    K[("3.7", n, 1)] = choose(FORMS37[n], a)
BOX38 = ["starter", "main course", "dessert", "portion", "recipe", "ingredient", "leftovers", "takeaway"]
for n, a in enumerate(["starter", "portion", "recipe", "leftovers", "ingredient", "takeaway"], 1):
    K[("3.8", n, 1)] = choose(BOX38, a)
for n, a in enumerate(["sour/savoury/savory/bitter/salty", "tough", "spicy/tasty/flavourful/flavorful", "cooked",
                       "disgusting/horrible/awful/tasteless", "undercooked"], 1):
    K[("3.9", n, 1)] = Q(a)
for n, a in enumerate(["bland", "portion", "crispy/crunchy", "leftovers"], 1):
    K[("3.10", n, 1)] = Q(a)
for n, a in enumerate("BCBBB", 1):
    K[("3.11", n, 1)] = choose(["A", "B", "C", "D"], a)
for n, a in enumerate(["crunchy", "greasy", "recipe", "disgusting"], 1):
    K[("3.12", n, 1)] = choose(ODD312[n], a)
TASTES = "salty/spicy/sweet/sour/bitter/rich/hot/cold/bland/creamy/greasy/oily"
for n, a in enumerate(["starter", TASTES, "course", "tough", "greasy/oily/cold", "tasteless/bland",
                       "leftovers/rest/food/chicken"], 1):
    K[("3.13", n, 1)] = Q(a)
for n, a in enumerate("badce", 1):
    K[("3.14", n, 1)] = choose(ENDS314, a)
K[("3.15", 1, 1)] = own()
for n in range(1, 5):                             # a guess, corrected afterwards
    K[("4.1", n, 1)] = own(control=None)
MENTION = {"✓": "✓ mentioned", "✗": "✗ not mentioned"}
# as numbered: 1 how many 2 cheap to run 3 who invented 4 what else 5 how it tasted 6 repair
for n, a in enumerate(["✓", "✓", "✗", "✓", "✓", "✗"], 1):
    K[("4.2", n, 1)] = choose(YES_NO, a, labels=MENTION)
TF = {"T": "T · true", "F": "F · false"}
for n, a in enumerate("TFTFTF", 1):
    K[("4.3", n, 1)] = choose(["T", "F"], a, labels=TF)
for key, a in (((1, 1), "cheaper"), ((2, 1), "more quickly"), ((2, 2), "more easily"), ((3, 1), "most"),
               ((4, 1), "more convenient"), ((5, 1), "longer"), ((6, 1), "better"), ((7, 1), "the best"),
               ((8, 1), "a bit more/more")):
    K[("4.4",) + key] = Q(a)
for n, a in enumerate(["cheaper", "best", "longer", "curry"], 1):
    K[("4.6", n, 1)] = choose(LOUD46[n], a)
for n, a in enumerate("BAB", 1):
    K[("4.7", n, 1)] = choose(["A", "B"], a)
REFERS = ["the number of machines", "people per machine", "the price in yen", "the price in pounds"]
for n, a in enumerate(REFERS, 1):
    K[("4.8", n, 1)] = choose(REFERS, a)
for key in [(k, j) for k in (1, 2, 3) for j in (1, 2)]:   # notes on what each speaker says
    K[("5.2",) + key] = own(control=None)
SPK = {"1": "1 · Marat", "2": "2 · Nilufar", "3": "3 · Diego"}
for n, a in enumerate("121332", 1):
    K[("5.3", n, 1)] = choose(["1", "2", "3"], a, labels=SPK)
for n, (word, first) in enumerate([("atmosphere", "a"), ("world", "w"), ("live", "l"), ("plate", "p"),
                                   ("visit", "v"), ("get", "g")], 1):
    K[("5.4", n, 1)] = Q(either(word[len(first):], word))
    K[("5.4", n, 2)] = own(control=None)          # the six areas: their notes
COLS = ["Positive", "Fairly positive", "Slightly negative", "Very negative"]
SORT55 = {"delicious": "Positive", "overpriced": "Slightly negative", "fresh": "Positive",
          "half cold": "Very negative", "reasonably friendly": "Fairly positive",
          "completely tasteless": "Very negative", "fairly pleasant": "Fairly positive", "wonderful": "Positive",
          "overcooked": "Very negative", "a bit noisy": "Slightly negative"}
for n, w in enumerate(WORDS55, 1):
    K[("5.5", n, 1)] = choose(COLS, SORT55[w])
SW = {"S": "S · stronger", "W": "W · weaker"}
# as numbered: 1 absolutely 2 a bit 3 completely 4 fairly 5 extremely 6 quite 7 really 8 rather 9 terribly
# 10 slightly
for n, a in enumerate("SWSWSWSWSW", 1):
    K[("5.6", n, 1)] = choose(["S", "W"], a, labels=SW)
for n, a in enumerate([
        either("The sauce wasn't very tasty", "The sauce was not very tasty"),
        "My soup was completely cold",
        "The portions were absolutely tiny",
        either("The service wasn't very good", "The service was not very good"),
        "The staff were reasonably friendly"], 1):
    K[("5.7", n, 1)] = write(a)
for n, a in enumerate(["over", "under", "over", "over", "over/under", "over"], 1):
    K[("5.8", n, 1)] = choose(["over", "under"], a)
for n in range(1, 6):
    K[("5.10", n, 1)] = own()
K[("5.11", 20, 1)] = own(control="essay")
for n in range(1, 8):                             # the checklist
    K[("5.11", n, 1)] = tick()

if __name__ == "__main__":
    data = h.build(K, "Intermediate", 6, "Unit 6B & 6D — Different cultures")
    out = os.path.join(HERE, "i062.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
