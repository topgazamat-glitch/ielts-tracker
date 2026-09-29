"""I10BD Opportunities - Azamat's Intermediate booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(I10BD Opportunities - ANSWER KEY), joined box by box by hand. At this level
the explanations stay English. Built from the Material Bank copy, as I10AC
is: his Desktop redesign has the same exercises but would not split into
parts.

Where the key allows more than it prints, so does the page: 2.6 takes
wouldn't as a loud word in "I wouldn't have bought it" (the key's own "or
wouldn't"), and 3.3 takes asked two hospitals as well as got.

What a phone gets that paper does not:
  - taps for every choice: T/B/C, A/B/C, the right form in 2.1, the two
    stressed words, do/make/take, the stressed syllable, which situation,
    T/F, advice only or a picture of the future;
  - boxes where paper has none: 2.1, 2.4, 2.6, 3.2, 3.4, 3.5, 5.2.
The swap in 5.8 keeps its boxes; they are for class.

    python3 handouts/i10bd_digital.py            # writes handouts/i10bd.json, lists every box
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import (Handout, Q, choose, tick, own, write, fix, pair, report,   # noqa: E402
                     BLANK_TAG, LEADER_P, plain, ITEM_STYLE, NUM_SPAN, TEXT_SPAN)

DOCX = ("~/Documents/Claude/Material Bank/General English/B1 Intermediate/_NEW BOOKLET STYLE/"
        "I10BD Opportunities — BOOKLET.docx")
W = "95%"

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


def words_of(label, n):
    m = next(m for m in h._items(label) if int(m.group(3)) == n)
    return [w.strip("?!.,") for w in re.sub(r"^\d+\s+", "", plain(m.group(4))).split() if w.strip("?!.,")]


def add_to_item(label, n, extra):
    m = next(m for m in h._items(label) if int(m.group(3)) == n)
    h.texts.setdefault((label, n), plain(m.group(4)))
    h.html = h.html[:m.start()] + m.group(1) + m.group(4) + extra + "</p>" + h.html[m.end():]


def drop_lines(start, until):
    """Ruled lines the boxes have made unnecessary."""
    a = h.html.index(start)
    b = h.html.index(until, a)
    h.html = h.html[:a] + LEADER_P.sub("", h.html[a:b]) + h.html[b:]


def had(*forms):
    """had X / 'd X, and the like, for the if half."""
    out = []
    for f in forms:
        out += [f]
        if f.startswith("had "):
            out.append("'d " + f[4:])
        if f.startswith("hadn't "):
            out.append("had not " + f[7:])
    return out


def would_have(*forms):
    out = []
    for f in forms:
        out += [f]
        if f.startswith("would have "):
            out.append("'d have " + f[11:])
        if f.startswith("wouldn't have "):
            out.append("would not have " + f[14:])
    return out


def third(subject_if, if_half, subject_main, main_half, tail=""):
    """Every way of writing one third conditional, either half first."""
    def join(subject, verb):                      # I'd, not I 'd
        return subject + ("" if verb.startswith("'") else " ") + verb
    out = []
    for i in had(if_half):
        for m in would_have(main_half):
            cond, result = join(subject_if, i), join(subject_main, m) + tail
            out += ["If %s, %s" % (cond, result), "If %s %s" % (cond, result),
                    "%s if %s" % (result[0].upper() + result[1:], cond)]
    return either(*out)


# ------------------------------------------------------------ 1 Reading
for n in range(1, 5):
    h.item_box("1.3", n)
h.options_on_lines("1.3")
for n in range(1, 4):
    h.item_box("1.4", n, width="190px", where="leader")
h.leaders("1.5", "1.6  </span>", [(1, W, "The first one, and what really happened"),
                                  (2, W, "The second one, and what really happened")])
for n in range(1, 4):
    h.item_box("1.6", n, where="leader")

# ------------------------------------------------------------ 2 Grammar
FORMS21 = {1: ["had had", "have had"], 2: ["would have finished", "had finished"],
           3: ["hadn't gone", "didn't go"], 4: ["wouldn't meet", "wouldn't have met"],
           5: ["had taken", "would take"], 6: ["wouldn't have got", "wouldn't get"]}
for n in FORMS21:
    h.item_box("2.1", n)
for n in range(2, 9):                             # item 1 is the worked example
    h.item_box("2.4", n)
LOUD = {}
for n in range(1, 5):
    LOUD[n] = words_of("2.6", n)
    add_to_item("2.6", n, '<br><span style="color:#6E6E6E">1st stressed word</span> {{box:2.6:%d:60px:}}'
                          '<br><span style="color:#6E6E6E">2nd stressed word</span> {{box:2.6:%d:60px:}}' % (n, n))

# ------------------------------------------------------------ 3 Vocabulary
PHRASES = h.sort_words("3.1", ["a decision", "some research", "a chance", "friends", "a job", "a look",
                               "the most of it", "voluntary work", "an opportunity"], "DO")
VERBS32 = {1: ["do", "make", "take"], 2: ["doing", "making", "taking"], 3: ["doing", "making", "taking"],
           4: ["do", "make", "take"], 5: ["do", "make", "take"], 6: ["do", "make", "take"]}
for n in VERBS32:
    h.item_box("3.2", n)
SYLL34 = {1: ["make", "a", "de", "ci", "sion"], 2: ["take", "a", "chance"], 3: ["do", "some", "re", "search"],
          4: ["make", "the", "most", "of", "it"], 5: ["take", "an", "op", "por", "tu", "ni", "ty"],
          6: ["do", "some", "bo", "dy", "a", "fa", "vour"]}
for n in SYLL34:
    h.item_box("3.4", n)
for n in range(1, 5):
    h.item_box("3.5", n, where="leader")

# ------------------------------------------------------------ 4 Listening
a = h.html.index('<table class="bk">', section("4.1"))
b = h.html.index("</table>", a) + len("</table>")
cells = [plain(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", h.html[a:b], re.S)]
SITUATIONS = sorted(re.match(r"([a-d])\s+(.*)", c).groups() for c in cells if re.match(r"[a-d]\s", c))
h.html = h.html[:a] + key_list(SITUATIONS) + "".join(
    item_p("4.1", n, "Conversation %d" % n, "{{box:4.1:%d:60px:}}" % n) for n in range(1, 5)) + h.html[b:]
for n in range(1, 4):
    h.item_box("4.6", n)
h.options_on_lines("4.6")
drop_lines("4.7  </span>", "LISTENING INTO WRITING")
a = section("4.7")
b = h.html.index("LISTENING INTO WRITING", a)
h.html = h.html[:a] + re.sub(r"\s*·\s*", "<br>", h.html[a:b], count=1) + h.html[b:]   # one sentence a line

# ------------------------------------------------------------ 5 Writing
h.grid_rows("5.1")
h.leaders("5.2", "ADVISING A COURSE", [(1, W, "Greg's third conditional"), (2, W, "What is he claiming?")])
for n in range(1, 5):
    h.item_box("5.6", n, where="leader")
h.leaders("5.7", "CHECK BEFORE", [(20, W, "Write your reply here")])
h.html = h.html.replace(TAGS[90], "", 1)          # the word count: the box counts them itself
h.grid_rows("5.8")
drop_lines("5.9  </span>", "</div>")

# ------------------------------------------------------------------ the key
K = {}
TBC = {"T": "T · Tom", "B": "B · Betty", "C": "C · Carla"}
for n, a in enumerate("BCTCBT", 1):
    K[("1.2", n, 1)] = choose(["T", "B", "C"], a, labels=TBC)
for n in range(1, 5):
    K[("1.3", n, 1)] = choose(["A", "B", "C"], "B")
for n, a in enumerate(["handwriting", "to unsubscribe/unsubscribe/unsubscribed", "a grant/grant"], 1):
    K[("1.4", n, 1)] = Q(a)
K[("1.5", 1, 1)] = own()
K[("1.5", 2, 1)] = own()
for n in range(1, 4):
    K[("1.6", n, 1)] = own()
for n, a in enumerate(["had had", "would have finished", "hadn't gone", "wouldn't have met", "had taken",
                       "wouldn't have got"], 1):
    K[("2.1", n, 1)] = choose(FORMS21[n], a)
for key, a in (((1, 1), would_have("would have won")), ((1, 2), had("hadn't hurt")),
               ((2, 1), would_have("wouldn't have bought")), ((2, 2), had("had known")),
               ((3, 1), had("hadn't pushed")), ((3, 2), would_have("would have hit")),
               ((4, 1), would_have("wouldn't have discovered")), ((4, 2), had("hadn't read")),
               ((5, 1), had("hadn't gone")), ((5, 2), would_have("wouldn't have met")),
               ((6, 1), would_have("would have gone")), ((6, 2), had("hadn't broken down"))):
    K[("2.2",) + key] = Q(either(*a))
for n in range(1, 5):                             # the facts, in their words
    K[("2.3", n, 1)] = own()
TICKED = "✓/correct/tick"
for n, a in zip(range(2, 9), [
        "It would have been better to stay at home",
        third("I", "had known", "I", "would have told you"),
        "What would you have done",
        third("he", "had had more time", "he", "would have helped"),
        TICKED,
        third("they", "had arrived earlier", "they", "would have seen her"),
        TICKED]):
    K[("2.4", n, 1)] = fix(a)
K[("2.5", 1, 1)] = own()
K[("2.5", 2, 1)] = own(control=None)              # a job: a word or two
K[("2.5", 2, 2)] = own()
K[("2.5", 3, 1)] = own()
K[("2.5", 4, 1)] = own()
# in sentence order: 1 won / easily 2 bought / it, or wouldn't / bought 3 car / hit
# 4 the key's truth / letters is the whole 4.3 line; here it is discovered / truth
STRESSED = {1: ("won", "easily"), 2: ("bought/wouldn't", "it/bought"), 3: ("car", "hit"),
            4: ("discovered/wouldn't", "truth/discovered")}
for n, (first, second) in STRESSED.items():
    K[("2.6", n, 1)] = choose(LOUD[n], first)
    K[("2.6", n, 2)] = choose(LOUD[n], second)
for n, a in enumerate([
        third("I", "had set an alarm", "I", "wouldn't have missed the meeting"),
        third("she", "hadn't studied medicine", "she", "wouldn't have met her husband", ""),
        third("we", "had booked", "we", "would have got a table"),
        third("he", "hadn't taken the job", "he", "wouldn't have moved to Almaty")], 1):
    K[("2.7", n, 1)] = write(a)
K[("2.7", 2, 1)] = write(K[("2.7", 2, 1)].answer + "/" + third("she", "hadn't studied medicine", "she",
                                                             "wouldn't have met her husband", " there"))
DMT = ["DO", "MAKE", "TAKE"]
SORT = {"a decision": "MAKE", "some research": "DO", "a chance": "TAKE", "friends": "MAKE", "a job": "DO",
        "a look": "TAKE", "the most of it": "MAKE", "voluntary work": "DO", "an opportunity": "TAKE"}
for n, p in enumerate(PHRASES, 1):
    K[("3.1", n, 1)] = choose(DMT, SORT[p])
for n, a in enumerate(["make", "doing", "taking", "take", "make", "take"], 1):
    K[("3.2", n, 1)] = choose(VERBS32[n], a)
for key, a in (((1, 1), "made"), ((2, 1), "got/asked/persuaded"), ((2, 2), "borrowed/got"), ((3, 1), "made"),
               ((4, 1), "did"), ((5, 1), "take"), ((6, 1), "took")):
    K[("3.3",) + key] = Q(a)
for n, a in enumerate(["ci", "chance", "search", "most", "tu", "fa"], 1):
    K[("3.4", n, 1)] = choose(SYLL34[n], a)
for n, a in enumerate(["I want to do some voluntary work next summer", "He made a big decision last year",
                       "She made a lot of money in that job", "Let me take a look at the timetable"], 1):
    K[("3.5", n, 1)] = write(a)
for n, a in enumerate("cabd", 1):
    K[("4.1", n, 1)] = choose([l for l, _t in SITUATIONS], a)
TF = {"T": "T · true", "F": "F · false"}
for n, a in enumerate("FFFTT", 1):
    K[("4.2", n, 1)] = choose(["T", "F"], a, labels=TF)
for key, a in (((1, 1), would_have("would have won")), ((1, 2), had("hadn't hurt")),
               ((2, 1), would_have("wouldn't have bought")), ((2, 2), had("had known")),
               ((3, 1), had("hadn't pushed")), ((3, 2), would_have("would have hit")),
               ((4, 1), would_have("wouldn't have discovered")), ((4, 2), had("hadn't read"))):
    K[("4.3",) + key] = Q(either(*a))
for n in range(1, 4):
    K[("4.6", n, 1)] = choose(["A", "B"], "B")
for n in range(1, 5):                             # their own week
    K[("4.7", n, 1)] = own(control=None)
for n in range(1, 6):                             # notes on what Greg says
    K[("5.1", n, 1)] = own()
K[("5.2", 1, 1)] = own()
K[("5.2", 2, 1)] = own()
AF = {"A": "A · advice only", "F": "F · a picture of the future"}
for n, a in enumerate("AFAFAF", 1):
    K[("5.3", n, 1)] = choose(["A", "F"], a, labels=AF)
for n in range(1, 6):                             # the key gives samples: his to read
    K[("5.4", n, 1)] = own()
for n in range(1, 5):
    K[("5.6", n, 1)] = own()
K[("5.7", 20, 1)] = own(control="essay")
for n in range(1, 7):                             # the checklist
    K[("5.7", n, 1)] = tick()
for n in range(1, 5):                             # about a partner's email, in class
    K[("5.8", n, 1)] = pair()
K[("5.9", 1, 1)] = own(control=None)
K[("5.9", 2, 1)] = own(control=None)

if __name__ == "__main__":
    data = h.build(K, "Intermediate", 10, "Unit 10B & 10D — Opportunities")
    out = os.path.join(HERE, "i10bd.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
