"""I07B House and home - Azamat's Intermediate booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(I07B House and home - ANSWER KEY), joined box by box by hand. At this level
the explanations stay English.

Put right here, since a page that marks itself cannot be wrong about its
own answers:
  - 1.6 says "Write the number (1-5)", but the text has six paragraphs and
    the key answers "para 6" - the page offers 1-6;
  - 5.1's "accept either column" for quiet and isolated is how it is marked.
Where the key gives samples but the word given leaves one answer (2.12), the
box is marked with every reasonable wording.

What a phone gets that paper does not:
  - taps for every choice: A/B/C, the paragraph, agree or disagree, C or U,
    many or much, a few / little, the complaint, the form in 2.6, less or
    fewer, too many / too much / not enough, the preposition, the stress
    pattern, the odd one out, the other half, T/F, the loudest word, the
    three columns of 5.1;
  - boxes where paper has none: 2.6, 2.10, 3.1, 3.6, 3.7, 3.11, 3.14, 4.6, 4.7.

    python3 handouts/i07b_digital.py            # writes handouts/i07b.json, lists every box
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
        "I07B House and home — BOOKLET.docx")
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


def halves(label, letters="a-f"):
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


def words_of(label, n):
    m = next(m for m in h._items(label) if int(m.group(3)) == n)
    return [w.strip("?!.,—") for w in re.sub(r"^\d+\s+", "", plain(m.group(4))).split() if w.strip("?!.,—")]


# ------------------------------------------------------------ 1 Reading
for n in range(1, 6):
    h.item_box("1.2", n)
h.options_on_lines("1.2")
for n in range(1, 5):
    h.item_box("1.3", n, where="leader")
for n in range(1, 5):
    h.item_box("1.4", n, width="190px", where="leader")
a = section("1.6")
b = h.html.index("</p>", a)
h.html = h.html[:a] + h.html[a:b].replace("1–5", "1–6", 1) + h.html[b:]
for n in range(1, 5):
    h.item_box("1.8", n, where="leader")

# ------------------------------------------------------------ 2 Grammar
FORMS26 = {1: ["many", "much"], 2: ["fewer", "less"], 3: ["Too much", "Too many"], 4: ["a little", "a few"],
           5: ["enough big", "big enough"], 6: ["many", "a lot of"]}
for n in FORMS26:
    h.item_box("2.6", n)
for n in range(2, 9):                             # item 1 is the worked example
    h.item_box("2.10", n)
h.leaders("2.14", "3  </span>", [(1, W, "Five sentences, five quantifiers")])

# ------------------------------------------------------------ 3 Vocabulary
ENDS31 = halves("3.1")
STRESS = h.sort_words("3.4", ["argue", "complain", "care", "apologise", "belong", "worry", "depend", "rely",
                              "succeed", "cope", "believe", "wait"], "O (one")
PREP36 = {1: ["on", "in"], 2: ["with", "to"], 3: ["in", "on"], 4: ["about", "with"], 5: ["about", "for"],
          6: ["on", "of"]}
for n in PREP36:
    h.item_box("3.6", n)
for n in range(1, 7):
    h.item_box("3.7", n, where="leader")
ODD311 = {1: ["care", "complain", "worry", "belong"], 2: ["depend", "rely", "concentrate", "apologise"],
          3: ["believe", "succeed", "take part", "argue"], 4: ["cope", "agree", "argue", "pay"]}
for n in ODD311:
    h.item_box("3.11", n)
ENDS314 = halves("3.14", "a-e")
h.leaders("3.15", "4  </span>", [(1, W, "Five sentences, five verb + preposition pairs")])

# ------------------------------------------------------------ 4 Listening
h.leaders("4.2", "4.3  </span>", [(n, W, "Reason %d" % n) for n in range(1, 4)])
LOUD47 = {}
for n in range(1, 5):
    LOUD47[n] = words_of("4.7", n)
    h.item_box("4.7", n)
for n in range(1, 4):
    h.item_box("4.8", n)
h.options_on_lines("4.8")

# ------------------------------------------------------------ 5 Writing
# 5.1: one line a word, with the three columns to tap
WORDS51 = ["lively", "run-down", "well connected", "quiet", "overcrowded", "green", "isolated", "convenient",
           "noisy", "affordable"]
a = h.html.index('<table class="bk">', section("5.1"))
b = h.html.index("</table>", a) + len("</table>")
h.html = h.html[:a] + "".join(item_p("5.1", n, html.escape(w), "{{box:5.1:%d:60px:}}" % n)
                              for n, w in enumerate(WORDS51, 1)) + h.html[b:]
h.replace_para("Not every box will be filled", "")
h.html = h.html.replace(TAGS[198], "", 1)         # 5.3's first line is the worked example
h.one_per_line("A DISTRICT NEAR THE CANAL", "PLAN", at="text")
for n in range(1, 6):
    h.item_box("5.6", n, where="leader")
h.leaders("5.7", "CHECK BEFORE", [(20, W, "Write your description here")])
h.html = h.html.replace(TAGS[217], "", 1)         # the word count: the box counts them itself

# ------------------------------------------------------------------ the key
K = {}
for n, a in enumerate("BCBBB", 1):
    K[("1.2", n, 1)] = choose(["A", "B", "C"], a)
for n in range(1, 5):
    K[("1.3", n, 1)] = own()
for n, a in enumerate(["a returner/returner", "rely on/to rely on", "anonymous", "cope with/to cope with"], 1):
    K[("1.4", n, 1)] = Q(a)
for n, a in enumerate(["third", "few", "about", "on", "more/fewer", "anonymous", "cope"], 1):
    K[("1.5", n, 1)] = Q(a)
# as numbered: 1 suit different people 2 why a car matters 3 the writer's test 4 how many come back
# 5 jobs 6 being unknown
for n, a in enumerate("526134", 1):
    K[("1.6", n, 1)] = choose(["1", "2", "3", "4", "5", "6"], a)
for n, a in enumerate(["warmly", "complain", "rely", "depend", "enough", "satisfaction", "belonged", "cope"], 1):
    K[("1.7", n, 1)] = Q(a)
for n in range(1, 5):
    K[("1.8", n, 1)] = own()
AD = {"A": "A · agree", "D": "D · disagree"}
for n in range(1, 5):                             # their opinion
    K[("1.9", n, 1)] = choose(["A", "D"], labels=AD)
CU = {"C": "C · countable", "U": "U · uncountable"}
# 1 traffic is the example; as numbered 2 restaurant 3 noise 4 advice 5 opportunity 6 furniture 7 crime
# 8 neighbour
for n, a in zip(range(2, 9), "CUUCUUC"):
    K[("2.1", n, 1)] = choose(["C", "U"], a, labels=CU)
for key, a in (((1, 1), "many"), ((2, 1), "much"), ((3, 1), "much"), ((4, 1), "many"), ((5, 1), "much"),
               ((6, 1), "many"), ((6, 2), "much")):
    K[("2.2",) + key] = choose(["many", "much"], a)
FEW = ["a few", "a little", "few", "little"]
for n, a in enumerate(["a few", "little", "few", "a little", "few", "a few"], 1):
    K[("2.3", n, 1)] = choose(FEW, a)
for n, a in enumerate("BAB", 1):
    K[("2.4", n, 1)] = choose(["A", "B"], a)
for n, a in enumerate(["of", "nearly/quite", "no", "some", "any", "far", "lot", "fast/quickly"], 1):
    K[("2.5", n, 1)] = Q(a)
for n, a in enumerate(["much", "fewer", "Too many", "a little", "big enough", "a lot of"], 1):
    K[("2.6", n, 1)] = choose(FORMS26[n], a)
for n, a in enumerate(["less", "fewer", "less", "fewer", "less", "fewer"], 1):
    K[("2.7", n, 1)] = choose(["less", "fewer"], a)
for n, a in enumerate(["a few", "any", "lots/plenty", "too", "little", "enough", "Many/Some", "none"], 1):
    K[("2.8", n, 1)] = Q(a)
for n, a in enumerate(["very few", "too narrow", "plenty of", "Few people/Very few people"], 1):
    K[("2.9", n, 1)] = Q(a)
TICKED = "✓/correct/tick"
for n, a in zip(range(2, 9), [
        either("I didn't bring enough bags, so we had to come back", "enough bags"),
        TICKED,
        either("We saw a lot of butterflies in the park last Sunday", "We saw lots of butterflies in the park last Sunday",
               "a lot of butterflies", "lots of butterflies"),
        either("The station is too far to walk to", "too far"),
        either("Few people know about this place, so it's usually quiet", "Few people know"),
        TICKED,
        either("I'd like to ask you some questions, if you have time", "some questions")]):
    K[("2.10", n, 1)] = fix(a)
TOO = ["too many", "too much", "not enough"]
for key, a in (((1, 1), "too many"), ((1, 2), "not enough"), ((2, 1), "too much"), ((3, 1), "too many"),
               ((3, 2), "not enough"), ((4, 1), "too many")):
    K[("2.11",) + key] = choose(TOO, a)
for n, a in enumerate([
        either("We have very few cafés in the whole town", "There are very few cafés in the whole town",
               "We have few cafés in the whole town", "We have very few cafes in the whole town"),
        either("There is very little crime here", "There's very little crime here"),
        either("The flat is too small for four people", "The flat's too small for four people"),
        either("There are plenty of buses", "There are plenty of buses here")], 1):
    K[("2.12", n, 1)] = write(a)
for n, a in enumerate("BCAB", 1):
    K[("2.13", n, 1)] = choose(["A", "B", "C", "D"], a)
K[("2.14", 1, 1)] = own()
for n, a in enumerate("ffabcdea", 1):
    K[("3.1", n, 1)] = choose(ENDS31, a)
for key, a in (((1, 1), "depends"), ((1, 2), "on"), ((2, 1), "cope"), ((2, 2), "with"), ((3, 1), "succeeded"),
               ((3, 2), "in"), ((4, 1), "apologise/apologize"), ((4, 2), "for"), ((5, 1), "argued"),
               ((5, 2), "with"), ((6, 1), "complain"), ((6, 2), "about"), ((7, 1), "believe"), ((7, 2), "in"),
               ((8, 1), "belongs"), ((8, 2), "to")):
    K[("3.2",) + key] = Q(a)
for n, a in enumerate(["for", "about", "for", "on", "about", "in"], 1):
    K[("3.3", n, 1)] = Q(a)
PATTERN = {"care": "O", "cope": "O", "wait": "O", "argue": "Oo", "worry": "Oo", "apologise": "oOoo"}
for n, w in enumerate(STRESS, 1):
    K[("3.4", n, 1)] = choose(["O", "Oo", "oO", "oOoo"], PATTERN.get(w, "oO"))
for key, a in (((1, 1), "to"), ((1, 2), "for"), ((2, 1), "to"), ((2, 2), "about"), ((3, 1), "to"),
               ((4, 1), "for"), ((5, 1), "for"), ((6, 1), "to")):
    K[("3.5",) + key] = Q(a)
for n, a in enumerate(["on", "with", "in", "about", "about", "on"], 1):
    K[("3.6", n, 1)] = choose(PREP36[n], a)
for n, a in enumerate([
        either("I'm worried about the noise from the road", "I am worried about the noise from the road"),
        either("She apologised to me for being late", "She apologized to me for being late"),
        either("You can depend on him — he always turns up", "You can depend on him - he always turns up",
               "You can depend on him, he always turns up", "You can depend on him"),
        "They complained to the council about the rubbish",
        "This flat belongs to my aunt",
        "He never succeeded in finding a job there"], 1):
    K[("3.7", n, 1)] = write(a)
for n, a in enumerate(["about", "on", "about", "with", "to", "in", "for", "with"], 1):
    K[("3.8", n, 1)] = Q(a)
for n, a in enumerate(["about", "to", "on", "on", "in", "for", "to", "with"], 1):
    K[("3.9", n, 1)] = Q(a)
for n, a in enumerate(["about", "on", "to", "in", "for", "with"], 1):
    K[("3.10", n, 1)] = Q(a)
for n, a in enumerate(["belong", "apologise", "argue", "pay"], 1):
    K[("3.11", n, 1)] = choose(ODD311[n], a)
for n, a in enumerate(["rely on", "apologised for/apologized for", "belongs to",
                       "cope/cope with it/cope with everything"], 1):
    K[("3.12", n, 1)] = Q(a)
for n, a in enumerate("BCBAC", 1):
    K[("3.13", n, 1)] = choose(["A", "B", "C"], a)
for n, a in enumerate("badce", 1):
    K[("3.14", n, 1)] = choose(ENDS314, a)
K[("3.15", 1, 1)] = own()
for n in range(1, 7):                             # what they expect: nothing to mark
    K[("4.1", n, 1)] = tick()
for n in range(1, 4):
    K[("4.2", n, 1)] = own()
TF = {"T": "T · true", "F": "F · false"}
for n, a in enumerate("TFTTTF", 1):
    K[("4.3", n, 1)] = choose(["T", "F"], a, labels=TF)
for n, a in enumerate(["much", "a lot/lots", "more", "much", "lot", "little"], 1):
    K[("4.4", n, 1)] = Q(a)
FULL = {"✓": "✓ a full word", "✗": "✗ it disappears"}
for n in range(1, 5):                             # in fast speech, in none of them
    K[("4.6", n, 1)] = choose(YES_NO, "✗", labels=FULL)
for n, a in enumerate(["much/going", "crime", "safer", "miss"], 1):
    K[("4.7", n, 1)] = choose(LOUD47[n], a)
for n, a in enumerate("BAB", 1):
    K[("4.8", n, 1)] = choose(["A", "B"], a)
COLS = ["Positive", "Neutral or mixed", "Negative"]
SORT51 = {"lively": "Positive", "run-down": "Negative", "well connected": "Positive",
          "quiet": "Neutral or mixed/Positive", "overcrowded": "Negative", "green": "Positive",
          "isolated": "Neutral or mixed/Negative", "convenient": "Positive", "noisy": "Negative",
          "affordable": "Positive"}
for n, w in enumerate(WORDS51, 1):
    K[("5.1", n, 1)] = choose(COLS, SORT51[w])
for n, a in enumerate(["on", "distance", "of", "connected", "rely", "enough/much"], 1):
    K[("5.2", n, 1)] = Q(a)
for n in range(2, 5):                             # the key gives samples: his to read
    K[("5.3", n, 1)] = own()
for k, a in enumerate(["a lot of/lots of/plenty of", "not enough/very few", "rely on"], 1):
    K[("5.4", 1, k)] = Q(a)
for k, a in enumerate(["very little", "too many/too many cars", "not enough", "complain about"], 1):
    K[("5.4", 5, k)] = Q(a)
for n in range(1, 6):
    K[("5.6", n, 1)] = own()
K[("5.7", 20, 1)] = own(control="essay")
for n in range(1, 9):                             # the checklist
    K[("5.7", n, 1)] = tick()

if __name__ == "__main__":
    data = h.build(K, "Intermediate", 7, "Unit 7B — House and home")
    out = os.path.join(HERE, "i07b.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
