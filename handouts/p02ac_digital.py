"""P02AC Travel and tourism - Azamat's own booklet, done on a phone.

His design is rendered as it is; this decides every box. The key is his
(P02AC Travel and tourism - answer key), joined box by box by hand.

What a phone gets that paper does not:
  - taps for every choice: day 1/2/3, A/B/C, ticks and crosses, the odd
    word out, /ɪd/ /t/ /d/, T/F, a-f, the phrases in a box;
  - a box for every exercise the paper leaves to a ruled line or to "circle":
    1.5, 1.6, 2.5, 2.8, 3.2, 3.3, 3.5, 4.2's corrections, 5.1, 5.7;
  - the speaking tasks (3.6, 4.1, 5.6) keep their instructions and lose the
    ruled lines, which were for notes in class.

    python3 handouts/p02ac_digital.py            # writes handouts/p02ac.json, lists every box
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import (Handout, Q, choose, tick, own, write, fix, note, number,   # noqa: E402
                     report, plain, ITEM_P, BLANK_TAG)

DOCX = ("~/Desktop/Handouts/B1 Pre-Intermediate/P02AC Travel and tourism/"
        "P02AC Travel and tourism — handout (new design).docx")
YES_NO = ["✓", "✗"]
ITEM_STYLE = 'style="margin-bottom:3.5px;line-height:1.25;padding-left:35px"'
NUM_SPAN = '<span style="color:#6E6E6E;font-size:10.5pt">%d  </span>'
TEXT_SPAN = '<span style="color:#1A1A1A;font-size:11.5pt">%s</span>'

h = Handout(DOCX)
BLANK_AT = {int(m.group(1)): m.group(0) for m in BLANK_TAG.finditer(h.html)}


def items(label):
    return [m for m in ITEM_P.finditer(h.html) if m.group(2) == label]


def options_on_lines(label):
    """A, B and C each on a line of their own, not run together in one line
    that wraps wherever the phone's width happens to fall."""
    for m in reversed(items(label)):
        guts = re.sub(r"(<span[^>]*>)([ABC])(</span>)", r"<br>\1\2\3", m.group(4))
        guts = re.sub(r"^<br>", "", guts)
        h.html = h.html[:m.start()] + m.group(1) + guts + "</p>" + h.html[m.end():]


# ---------------------------------------------------------------- 1 Reading
options_on_lines("1.3")
for n in (1, 2, 3, 4):
    h.item_box("1.3", n, where="options")
for n in (1, 2, 3):
    h.item_box("1.4", n, width="170px", where="leader")
h.leaders("1.5", "1.6  </span>", [(1, "95%", "Five regular verbs"),
                                   (2, "95%", "Five irregular verbs")])
for n in (1, 2, 3):
    h.item_box("1.6", n, where="leader")

# ---------------------------------------------------------------- 2 Grammar
# 2.4: a negative and a question, one box each, without the "/" between them
for i, j in ((30, 31), (32, 33), (34, 35)):
    h.hints[i], h.hints[j] = "Negative", "Question"
    a = h.html.index(BLANK_AT[i]) + len(BLANK_AT[i])
    b = h.html.index(BLANK_AT[j], a)
    h.html = h.html[:a] + re.sub(r"\s/\s", " ", h.html[a:b], count=1) + h.html[b:]
for n in range(2, 9):                            # item 1 is the worked example
    h.item_box("2.5", n)
# 2.7: the answer first, then the box for the question it answers
for m in reversed(items("2.7")):
    tag = BLANK_TAG.search(m.group(4))
    i = int(tag.group(1))
    h.hints[i] = "Write the question"
    guts = m.group(4).replace(tag.group(0), "", 1)
    guts = re.sub(r"\?\s*—\s*", "", guts, count=1)
    h.html = h.html[:m.start()] + m.group(1) + guts + tag.group(0) + "</p>" + h.html[m.end():]
h.leaders("2.8", "3.1  </span>", [(1, "95%", "A question with was or were"),
                                   (2, "95%", "A question with was or were"),
                                   (3, "95%", "A question with did"),
                                   (4, "95%", "A question with did")])

# ------------------------------------------------------------- 3 Vocabulary
# 3.2: the four words are the choice - tap the odd one out, then say why
ODD = {}
for m in reversed(items("3.2")):
    n = int(m.group(3))
    ODD[n] = [w.strip() for w in re.sub(r"^\d+\s+", "", plain(m.group(4))).split("·")]
for n in (1, 2, 3, 4):
    h.item_box("3.2", n)
    h.item_box("3.2", n, placeholder="Why?")
for m in reversed(items("3.2")):
    boxes = "".join(re.findall(r"\{\{box:[^}]*\}\}", m.group(4)))
    n = int(m.group(3))
    h.html = (h.html[:m.start()] + m.group(1) + NUM_SPAN % n + boxes + "</p>" + h.html[m.end():])
for n in (1, 2, 3, 4):
    h.item_box("3.3", n, where="leader")
# 3.5: each word with /ɪd/ /t/ /d/ to tap, in place of the word box and the
# empty three-column table
WORDS = ["arrived", "believed", "ended", "included", "looked",
         "shouted", "smiled", "stopped", "waited", "watched"]
head = h.html.index("3.5  </span>")
t1 = h.html.index("<table", head)
t2 = h.html.index("<table", h.html.index("</table>", t1))
end = h.html.index("</table>", t2) + len("</table>")
assert plain(h.html[t2:end]).startswith("/ɪd/")


def word_cell(n):
    h.texts[("3.5", n)] = WORDS[n - 1]
    return ('<td style="vertical-align:top;border-top:0;border-bottom:0;border-left:0;border-right:0">'
            '<p data-item="3.5:%d" %s>%s%s</p></td>'
            % (n, ITEM_STYLE, NUM_SPAN % n,
               TEXT_SPAN % ("%s  {{box:3.5:%d:60px:}}" % (WORDS[n - 1], n))))


rows = "".join("<tr>%s%s</tr>" % (word_cell(n), word_cell(n + 5)) for n in range(1, 6))
h.html = h.html[:t1] + '<table class="bk">' + rows + "</table>" + h.html[end:]
h.leaders("3.6", "4.1  </span>", [])            # speaking: no lines to fill

# -------------------------------------------------------------- 4 Listening
h.leaders("4.1", "4.2  </span>", [])            # speaking
for n in range(1, 6):
    h.item_box("4.2", n, where="leader", placeholder="If it is false, correct it")
options_on_lines("4.7")
for n in (1, 2, 3):
    h.item_box("4.7", n)

# ---------------------------------------------------------- 5 Everyday English
for n in (1, 2, 3, 4):
    h.item_box("5.1", n, where="leader")


def endings_first():
    """5.2 on paper is two columns, beginnings and endings, side by side; a
    phone stacks them into one list that alternates between the two. The
    six endings go first, as a key; then the six beginnings, each with
    a-f to tap."""
    head = h.html.index("5.2  </span>")
    a = h.html.index('<table class="bk">', head)
    b = h.html.index("</table>", a) + len("</table>")
    begin, ends = [], []
    for tr in re.findall(r"<tr>(.*?)</tr>", h.html[a:b], re.S):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        if not plain("".join(cells)):
            continue
        n = int(re.search(r'data-item="5\.2:(\d+)"', cells[0]).group(1))
        begin.append((n, cells[0]))
        letter, rest = re.match(r"([a-f])\s+(.*)", plain(cells[1])).groups()
        ends.append((letter, rest))
    assert len(begin) == 6, begin
    key = ('<table class="bk"><tr><td style="vertical-align:top;background:#F2F8F8;'
           'border-left:3px solid #127D80">'
           + "".join('<p style="margin:0"><span style="font-weight:700;color:#127D80">%s</span>  %s</p>'
                     % (l, r.replace("&", "&amp;").replace("<", "&lt;")) for l, r in sorted(ends))
           + "</td></tr></table>")
    h.html = h.html[:a] + key + "".join(c for _n, c in sorted(begin)) + h.html[b:]


endings_first()
h.leaders("5.6", "5.7  </span>", [])            # pair work: no lines to fill
h.leaders("5.7", "CHECK YOUR CONVERSATION", [(20, "95%", "The question they answered best"),
                                              (21, "95%", "The next best"),
                                              (22, "95%", "The one they found hardest")])
h.one_per_line("CHECK YOUR CONVERSATION", None, at="box")

# ------------------------------------------------------------------- the key
K = {}
DAY = {"1": "Day 1", "2": "Day 2", "3": "Day 3"}
for n, a in enumerate("321231", 1):
    K[("1.2", n, 1)] = choose(["1", "2", "3"], a, labels=DAY)
for n in (1, 2, 3, 4):
    K[("1.3", n, 1)] = choose(["A", "B", "C"], "B")
for n, a in enumerate(["a souvenir/souvenir/souvenirs", "sunburn/sunburnt/sunburned",
                       "charming"], 1):
    K[("1.4", n, 1)] = Q(a)
for n in (1, 2):
    K[("1.5", n, 1)] = own()
for n in (1, 2, 3):
    K[("1.6", n, 1)] = own()
for n, a in enumerate("arrived stopped carried started went bought saw ate had felt "
                      "became slept".split(), 1):
    K[("2.1", n, 1)] = Q(a)
for n, a in enumerate("worked spent stayed won took went".split(), 1):
    K[("2.2", n, 1)] = Q(a)
for n, a in enumerate(["weren't/were not", "didn't/did not", "Did", "was", "was", "did"], 1):
    K[("2.3", n, 1)] = Q(a)
for n, (neg, ask) in enumerate([
        ("She didn't book a hotel/She did not book a hotel", "Did she book a hotel"),
        ("It wasn't expensive/It was not expensive", "Was it expensive"),
        ("They didn't go sightseeing/They did not go sightseeing", "Did they go sightseeing")], 1):
    K[("2.4", n, 1)] = write(neg)
    K[("2.4", n, 2)] = write(ask)
TICKED = "✓/correct/tick"
for n, a in zip(range(2, 9), [
        "Was it hot",
        "Where did you go on Tuesday/Where did you go",
        "We stopped for lunch at two/We stopped/stopped",
        TICKED, TICKED,
        "Did you see the market/Did you see/see",
        "She carried the bags all the way back/She carried/carried"]):
    K[("2.5", n, 1)] = fix(a)
for n, a in enumerate(["was", "arrived", "wasn't/was not", "were", "complained", "moved",
                       "was", "took", "didn't feel/did not feel", "saw", "Did you get"], 1):
    K[("2.6", n, 1)] = Q(a)
for n in (1, 2, 3, 4):                           # his key gives samples: his to mark
    K[("2.7", n, 1)] = own()
    K[("2.8", n, 1)] = own()
for n, a in enumerate(["checked in", "self-catering/self catering",
                       "all-inclusive/all inclusive", "suntan lotion/sun tan lotion",
                       "day trip/day-trip", "hand luggage", "sightseeing", "souvenirs"], 1):
    K[("3.1", n, 1)] = Q(a)
for n, a in zip((1, 2, 3, 4), ["suitcase", "landmark", "postcard", "coast"]):
    K[("3.2", n, 1)] = choose(ODD[n], a)
    K[("3.2", n, 2)] = own()
for n, a in enumerate([
        "I went to the travel agent's and she booked it for me/"
        "the travel agent's/travel agent's",
        "We took a lot of photos at the castle/We took a lot of photos/took",
        "The hotel was all-inclusive/The hotel was all inclusive/all-inclusive",
        "We went sightseeing all morning/We went sightseeing/went sightseeing/went"], 1):
    K[("3.3", n, 1)] = write(a)
EXTRA = {"needed", "decided", "wanted", "started"}
for n, w in enumerate(["changed", "needed", "decided", "played", "asked", "wanted",
                       "started", "watched"], 1):
    K[("3.4", n, 1)] = choose(YES_NO, "✓" if w in EXTRA else "✗")
SOUND = {"ended": "/ɪd/", "included": "/ɪd/", "shouted": "/ɪd/", "waited": "/ɪd/",
         "looked": "/t/", "stopped": "/t/", "watched": "/t/",
         "arrived": "/d/", "believed": "/d/", "smiled": "/d/"}
for n, w in enumerate(WORDS, 1):
    K[("3.5", n, 1)] = choose(["/ɪd/", "/t/", "/d/"], SOUND[w])
for n, a in enumerate("TFTFF", 1):
    K[("4.2", n, 1)] = choose(["T", "F"], a)
    K[("4.2", n, 2)] = note()
for n, a in enumerate(["slept", "showed/taught", "stood", "thought", "asked"], 1):
    K[("4.3", n, 1)] = Q(a)
for n, a in enumerate("536241", 1):             # the order the events happened in
    K[("4.6", n, 1)] = number(a)
for n in (1, 2, 3):
    K[("4.7", n, 1)] = choose(["A", "B"], "B")
for n in (1, 2, 3, 4):                           # "Listen and answer": his to mark
    K[("5.1", n, 1)] = own()
for n, a in enumerate("decabf", 1):
    K[("5.2", n, 1)] = choose(list("abcdef"), a)
BOX = ["Can I", "Could you tell me", "How much", "What time", "Where can I"]
for n, a in enumerate(["Could you tell me", "What time", "How much", "Where can I", "Can I"], 1):
    K[("5.3", n, 1)] = choose(BOX, a)
for n, a in enumerate("ABAA", 1):
    K[("5.4", n, 1)] = choose(["A", "B"], a)
for n in (20, 21, 22):
    K[("5.7", n, 1)] = own()
for n in range(1, 6):                            # CHECK YOUR CONVERSATION
    K[("5.7", n, 1)] = tick()

if __name__ == "__main__":
    data = h.build(K, "Pre-Intermediate", 2, "Unit 2A & 2C — Travel and tourism")
    out = os.path.join(HERE, "p02ac.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
