"""I08B Information - Azamat's Intermediate booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(I08B Information - ANSWER KEY), joined box by box by hand. At this level
the explanations stay English.

Put right here, since a page that marks itself cannot be wrong about its
own answers:
  - 2.4 says TWO sentences are correct; the key ticks three (3, 6 and 8),
    so the page says three.
Where the key gives samples but the pattern leaves little choice (3.3, the
reported sentences), the box is marked with every reasonable wording; the
direct speech in 3.8 and the concrete details in 5.2 and 5.4 are his to read.

What a phone gets that paper does not:
  - taps for every choice: A/B/C, the paragraph, real or fake, agree or
    disagree, -ing or to, the form in 2.6, the three patterns, the verb from
    the box, the other half, the odd one out, the stronger verb, the stressed
    word, T/F, presenter or expert, A or B;
  - boxes where paper has none: 2.4, 2.6, 3.5, 3.7, 3.9, 4.7, 5.1.

    python3 handouts/i08b_digital.py            # writes handouts/i08b.json, lists every box
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import (Handout, Q, choose, tick, own, write, fix, note, number, report,   # noqa: E402
                     BLANK_TAG, plain, ITEM_STYLE, NUM_SPAN, TEXT_SPAN)

DOCX = ("~/Documents/Claude/Material Bank/General English/B1 Intermediate/_NEW BOOKLET STYLE/"
        "I08B Information — BOOKLET.docx")
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


def halves(label):
    """"Match the halves" with no boxes on paper: the endings first, as a key;
    then each beginning, with the letters to tap."""
    a = h.html.index('<table class="bk">', section(label))
    b = h.html.index("</table>", a) + len("</table>")
    cells = [plain(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", h.html[a:b], re.S)]
    begins = [re.match(r"(\d+)\s+(.*)", c).groups() for c in cells if re.match(r"\d+\s", c)]
    ends = sorted(re.match(r"([a-f])\s+(.*)", c).groups() for c in cells if re.match(r"[a-f]\s", c))
    h.html = h.html[:a] + key_list(ends) + "".join(
        item_p(label, int(n), html.escape(t, quote=False), "{{box:%s:%s:60px:}}" % (label, n))
        for n, t in begins) + h.html[b:]
    return [l for l, _t in ends]


def objects(verb_phrase, rest):
    """asked us to wait, asked me to wait ... - the key does not say who."""
    return [verb_phrase + " " + o + " " + rest for o in ("us", "me", "him", "her", "them", "everyone")]


# ------------------------------------------------------------ 1 Reading
for n in range(1, 6):
    h.item_box("1.2", n)
h.options_on_lines("1.2")
for n in range(1, 5):
    h.item_box("1.3", n, where="leader")
for n in range(1, 5):
    h.item_box("1.4", n, width="190px", where="leader")
for n in range(1, 5):
    h.item_box("1.8", n, where="leader")

# ------------------------------------------------------------ 2 Grammar
a = section("2.4")
b = h.html.index("</p>", a)
h.html = h.html[:a] + h.html[a:b].replace("TWO", "THREE", 1) + h.html[b:]
for n in range(2, 9):                             # item 1 is the worked example
    h.item_box("2.4", n)
FORMS26 = {1: ["paying", "to pay"], 2: ["booking", "to book"], 3: ["writing", "to write"],
           4: ["phoning", "to phone"], 5: ["enjoying", "to enjoy"], 6: ["living", "to live"]}
for n in FORMS26:
    h.item_box("2.6", n)

# ------------------------------------------------------------ 3 Vocabulary
VERBS31 = h.sort_words("3.1", ["offer", "ask", "recommend", "promise", "persuade", "suggest", "threaten",
                               "warn", "admit", "agree", "advise", "refuse", "remind"], "verb + to")
for n in range(1, 7):
    h.item_box("3.5", n, where="leader")
ENDS37 = halves("3.7")
ODD39 = {1: ["offer", "promise", "admit", "agree"], 2: ["warn", "advise", "suggest", "remind"],
         3: ["recommend", "suggest", "admit", "refuse"], 4: ["warn", "advise", "remind", "offer"]}
for n in ODD39:
    h.item_box("3.9", n)
h.leaders("3.14", "3.15  </span>", [(1, W, "Report the conversation — five reporting verbs")])
h.leaders("3.15", "4  </span>", [(1, W, "Four sentences, four reporting verbs")])

# ------------------------------------------------------------ 4 Listening
for n in range(1, 9):                             # the correction, for the false ones
    h.item_box("4.3", n, where="leader", placeholder="If false, correct it")
LOUD47 = {1: ["But", "can", "we", "trust", "online", "reviews"], 2: ["Well", "maybe", "eighty", "per", "cent",
                                                                      "of", "the", "time"],
          3: ["Of", "course", "that", "is", "against", "the", "law"], 4: ["But", "it", "certainly", "happens"]}
for n in LOUD47:
    h.item_box("4.7", n)
for n in range(1, 4):
    h.item_box("4.9", n)
h.options_on_lines("4.9")

# ------------------------------------------------------------ 5 Writing
h.html = h.html.replace(TAGS[189], "", 1)         # 5.2's first line is the worked example
h.one_per_line("A REVIEW THAT CONVINCES NOBODY", "PLAN", at="text")
for n in range(1, 6):
    h.item_box("5.6", n, where="leader")
h.leaders("5.7", "CHECK BEFORE", [(20, W, "Write your review here")])
h.html = h.html.replace(TAGS[214], "", 1)         # the word count: the box counts them itself

# ------------------------------------------------------------------ the key
K = {}
for n, a in enumerate("BBBBC", 1):
    K[("1.2", n, 1)] = choose(["A", "B", "C"], a)
for n in range(1, 5):
    K[("1.3", n, 1)] = own()
for n, a in enumerate(["genuine", "a rating/rating", "to filter out/filter out", "quietly"], 1):
    K[("1.4", n, 1)] = Q(a)
# as numbered: 1 how the software works 2 the one test 3 how people drift into faking 4 why faking is
# worth it 5 which reviews to read last 6 evidence they are bought and sold
for n, a in enumerate("453162", 1):
    K[("1.5", n, 1)] = choose(["1", "2", "3", "4", "5", "6"], a)
for n, a in enumerate(["out", "likely", "offering", "known", "become", "goes", "beats", "probably"], 1):
    K[("1.6", n, 1)] = Q(a)
RF = {"R": "R · real", "F": "F · fake"}
for n, a in enumerate("FRFRFR", 1):              # friendly, after closing, amazing food, soup, best hotel, lift
    K[("1.7", n, 1)] = choose(["R", "F"], a, labels=RF)
K[("1.7", 6, 2)] = own()                          # what the real ones have in common
for n in range(1, 5):
    K[("1.8", n, 1)] = own()
AD = {"A": "A · agree", "D": "D · disagree"}
for n in range(1, 5):                             # their opinion
    K[("1.9", n, 1)] = choose(["A", "D"], labels=AD)
IT = {"I": "I · -ing", "T": "T · to + infinitive"}
# 1 enjoy is the example; as numbered 2 decide 3 suggest 4 promise 5 manage 6 avoid 7 admit 8 refuse
# 9 recommend 10 hope
for n, a in zip(range(2, 11), "TITTIITIT"):
    K[("2.1", n, 1)] = choose(["I", "T"], a, labels=IT)
for n, a in enumerate(["reading", "to make", "asking", "to give", "waiting", "to get", "to buy", "writing"], 1):
    K[("2.2", n, 1)] = Q(a)
for n, a in enumerate(["us to wait", "him not to sit", "me to try", "us to book", "her to wash"], 1):
    K[("2.3", n, 1)] = Q(a)
TICKED = "✓/correct/tick"
for n, a in zip(range(2, 9), [
        either("I enjoyed meeting your brother last week", "enjoyed meeting"),
        TICKED,
        either("I like being at home at the weekend", "I like to be at home at the weekend", "like being",
               "like to be"),
        either("He's interested in hearing about your trip", "He is interested in hearing about your trip",
               "interested in hearing"),
        TICKED,
        either("They warned us not to eat there", "warned us not to eat"),
        TICKED]):
    K[("2.4", n, 1)] = fix(a)
for n, a in enumerate(["to", "in", "worth", "out", "at", "to"], 1):
    K[("2.5", n, 1)] = Q(a)
for n, a in enumerate(["to pay", "booking", "to write", "phoning", "to enjoy", "living"], 1):
    K[("2.6", n, 1)] = choose(FORMS26[n], a)
for n, a in enumerate(["to stay", "reading", "to be", "to book", "giving", "to find", "to pay", "to do"], 1):
    K[("2.7", n, 1)] = Q(a)
K[("2.8", 1, 1)] = Q(either(*objects("asked", "to wait")))
K[("2.8", 2, 1)] = Q(either(*objects("warned", "not to go")))
K[("2.8", 3, 1)] = Q(either("promised to write", "promised me to write", "promised that she would write"))
K[("2.8", 4, 1)] = Q(either(*objects("advised", "to book")))
for n, verb in enumerate(["read", "rain", "phone"], 1):
    ing = {"read": "reading", "rain": "raining", "phone": "phoning"}[verb]
    K[("2.9", n, 1)] = Q(either(ing, "to " + verb))
    K[("2.9", n, 2)] = Q(either("to " + verb, ing))
for n, a in enumerate(["to pay", "waiting", "reading", "to leave/to give", "complaining", "booking"], 1):
    K[("2.10", n, 1)] = Q(a)
for n, a in enumerate([
        either("It's worth booking early", "It is worth booking early"),
        either("It's difficult to choose from photographs", "It is difficult to choose from photographs"),
        either("I'm interested in hearing about your trip", "I am interested in hearing about your trip")], 1):
    K[("2.11", n, 1)] = write(a)
for n, a in enumerate("BCBC", 1):
    K[("2.12", n, 1)] = choose(["A", "B", "C", "D"], a)
for n in range(1, 5):
    K[("2.13", n, 1)] = own()
PATTERNS = ["+ to", "+ object + to", "+ -ing"]
SORT = {"offer": "+ to", "promise": "+ to", "threaten": "+ to", "agree": "+ to", "refuse": "+ to",
        "ask": "+ object + to", "persuade": "+ object + to", "warn": "+ object + to", "advise": "+ object + to",
        "remind": "+ object + to", "recommend": "+ -ing", "suggest": "+ -ing", "admit": "+ -ing"}
for n, v in enumerate(VERBS31, 1):
    K[("3.1", n, 1)] = choose(PATTERNS, SORT[v])
for n, a in enumerate(["ask", "promise", "persuade", "offering", "warn", "threaten", "recommend", "advise"], 1):
    K[("3.2", n, 1)] = Q(a)
K[("3.3", 1, 1)] = write("offered to pay for the taxi")
K[("3.3", 2, 1)] = write(either(*objects("warned", "not to sit down")))
K[("3.3", 3, 1)] = write(either("recommended trying the fish", "recommended the fish",
                                "recommended that I try the fish", "recommended that I should try the fish",
                                "recommended that we try the fish"))
K[("3.3", 4, 1)] = write(either("refused to do it", "refused"))
K[("3.3", 5, 1)] = write(either("admitted writing them", "admitted that he wrote them", "admitted to writing them",
                                "admitted having written them", "admitted that he had written them"))
K[("3.3", 6, 1)] = write(either("suggested asking somebody", "suggested asking someone",
                                "suggested that we ask somebody", "suggested that we should ask somebody",
                                "suggested we ask somebody", "suggested that we ask someone"))
BOX34 = ["admit", "threaten", "persuade", "remind", "refuse", "offer"]
for n, a in enumerate(["threaten", "admit", "persuade", "offer", "refuse", "remind"], 1):
    K[("3.4", n, 1)] = choose(BOX34, a)
for n, a in enumerate([
        either("He admitted writing the reviews", "He admitted to writing the reviews"),
        either("She suggested going to the other café", "She suggested going to the other cafe"),
        "They warned us not to park there",
        "He offered to pay for the meal",
        "I recommend reading the bad reviews",
        either("She promised to write it", "She promised me that she would write it",
               "She promised me she would write it")], 1):
    K[("3.5", n, 1)] = write(a)
for n, a in enumerate(["to fix", "forgetting", "asking", "to give", "to write", "to take", "not to book"], 1):
    K[("3.6", n, 1)] = Q(a)
for n, a in enumerate("bcade", 1):
    K[("3.7", n, 1)] = choose(ENDS37, a)
for n in range(1, 5):                             # the key gives samples: his to read
    K[("3.8", n, 1)] = own()
for n, a in enumerate(["admit", "suggest", "refuse", "offer"], 1):
    K[("3.9", n, 1)] = choose(ODD39[n], a)


def reported(subjects, verb, obj, rest):
    out = []
    for s in subjects:
        for o in obj:
            out.append((s + verb + (" " + o if o else "") + " " + rest).strip())
    return either(*out)


SUBJ = ["", "He ", "She ", "They "]
OBJ = ["us", "me", "him", "her", "them"]
K[("3.10", 1, 1)] = Q(reported(SUBJ, "advised", OBJ, "to book early"))
K[("3.10", 1, 2)] = Q(reported(SUBJ, "advised", OBJ, "not to book late"))
K[("3.10", 2, 1)] = Q(reported(SUBJ, "recommended", [""], "taking the fish"))
K[("3.10", 2, 2)] = Q(reported(SUBJ, "recommended", [""], "not taking the meat"))
K[("3.10", 3, 1)] = Q(reported(SUBJ, "suggested", [""], "going now"))
K[("3.10", 3, 2)] = Q(reported(SUBJ, "suggested", [""], "not going now"))
for n, a in enumerate(["to help/to help me/to help you/to help us", "doing it/it/that it was her",
                       "not to be late", "walking"], 1):
    K[("3.11", n, 1)] = Q(a)
PAIRS312 = {1: ["advise", "warn"], 2: ["suggest", "insist"], 3: ["ask", "demand"], 4: ["recommend", "promise"]}
for n, a in enumerate(["warn", "insist", "demand", "promise"], 1):
    K[("3.12", n, 1)] = choose(PAIRS312[n], a)
for n, a in enumerate("ABCAB", 1):
    K[("3.13", n, 1)] = choose(["A", "B", "C"], a)
K[("3.14", 1, 1)] = own()
K[("3.15", 1, 1)] = own()
for n in range(1, 5):                             # a guess: nothing to mark
    K[("4.1", n, 1)] = tick()
# as numbered: 1 read reviews 2 influenced 3 genuine 4 dollars
for n, a in enumerate(["90", "70", "80", "85"], 1):
    K[("4.2", n, 1)] = number(a)
TF = {"T": "T · true", "F": "F · false"}
for n, a in enumerate("TTFTFTFT", 1):
    K[("4.3", n, 1)] = choose(["T", "F"], a, labels=TF)
    K[("4.3", n, 2)] = note()                    # a correction only where it is false
for n, a in enumerate(["ask", "promise", "persuade", "offering", "warn", "threaten", "recommend", "advise"], 1):
    K[("4.4", n, 1)] = Q(a)
FULL = {"✓": "✓ a full word", "✗": "✗ it disappears"}
for n, a in enumerate(["✓", "✗", "✓", "✗"], 1):   # I would say, I'd recommend, I would certainly, They'd have
    K[("4.6", n, 1)] = choose(YES_NO, a, labels=FULL)
for n, a in enumerate(["trust", "eighty", "law", "certainly"], 1):
    K[("4.7", n, 1)] = choose(LOUD47[n], a)
PJ = {"P": "P · presenter", "J": "J · the expert"}
for n, a in enumerate("PJPJ", 1):
    K[("4.8", n, 1)] = choose(["P", "J"], a, labels=PJ)
for n, a in enumerate("BAB", 1):
    K[("4.9", n, 1)] = choose(["A", "B"], a)
for n in range(1, 4):
    K[("5.1", n, 1)] = choose(["A", "B"], "B")
K[("5.1", 3, 2)] = own()                          # what the B sentences have
for n in range(2, 5):                             # their concrete detail: his to read
    K[("5.2", n, 1)] = own()
for n, a in enumerate(["by", "helpful/friendly/kind/welcoming/attentive", "booking", "recommend", "complaint",
                       "fair/honest"], 1):
    K[("5.3", n, 1)] = Q(a)
for k in range(1, 5):                             # something concrete: his to read
    K[("5.4", 1, k)] = own(control=None)
K[("5.4", 5, 1)] = own(control=None)
K[("5.4", 5, 2)] = Q("recommend going/recommend going there/I recommend going/I recommend going there")
K[("5.4", 5, 3)] = own(control=None)
for n in range(1, 6):
    K[("5.6", n, 1)] = own()
K[("5.7", 20, 1)] = own(control="essay")
for n in range(1, 9):                             # the checklist
    K[("5.7", n, 1)] = tick()

if __name__ == "__main__":
    data = h.build(K, "Intermediate", 8, "Unit 8B — Information")
    out = os.path.join(HERE, "i08b.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
