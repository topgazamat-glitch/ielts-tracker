"""I01.1 Talk - Azamat's Intermediate booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(I01.1 Talk - answer key), joined box by box by hand. At this level the
explanations stay English. The Desktop "new design" copy is used. Its fourth
part is Everyday English and its fifth a guide to write; there is no
listening.

Put right here: 3.1's meanings ran almost a-h beside words 1-8, so they are
lettered in a different order. Stray asterisks from the typing ("open up*",
"get to know**", "*Aziz called Malika.*") are gone.
In 3.9 item 4 the key itself says no word is really the odd one ("accept
communicative"), so that tap is left for the teacher. 3.11 is a table to tick
on paper; here each verb gets the four words to tap, and the key's answer.
2.4 and 2.11 leave no gaps on paper: each item gets a box. In 2.3 the answer
is shown first and the box for the question under it. 2.8 (questions for an
interview, samples in the key) is left for the teacher.

    python3 handouts/i011_digital.py            # writes handouts/i011.json, lists every box
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import (Handout, Q, choose, own, write, fix, report,   # noqa: E402
                     LEADER_P, BLANK_TAG, plain, ITEM_STYLE, NUM_SPAN, TEXT_SPAN)

DOCX = ("~/Desktop/Handouts/B1+ Intermediate/I01.1 Talk/"
        "I01.1 Talk — handout (new design).docx")
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






def answer_first(label, hint):
    """"Write the question for this answer": the answer, then the box under it."""
    for m in reversed(h._items(label)):
        tag = BLANK_TAG.search(m.group(4))
        said = re.sub(r"^\d+\s*\?\s*", "", plain(m.group(4))).strip()
        h.hints[int(tag.group(1))] = hint
        h.html = (h.html[:m.start()] + m.group(1) + NUM_SPAN % int(m.group(3))
                  + TEXT_SPAN % html.escape(said, quote=False) + "<br>" + tag.group(0) + "</p>" + h.html[m.end():])


def reword(label, old, new):
    at = section(label) + len("%s  </span>" % label)
    end = h.html.index("</p>", at)
    if plain(h.html[at:end]) != old:
        raise SystemExit("%s says %r" % (label, plain(h.html[at:end])))
    style = re.match(r'<span( style="[^"]*")?>', h.html[at:end])
    h.html = h.html[:at] + "<span%s>%s</span>" % (style.group(1) or "", html.escape(new)) + h.html[end:]


# ------------------------------------------------------------ typing left over
h.html, stars = re.subn(r"(<span[^>]*>)\*{1,2}", r"\1", h.html)
h.html = h.html.replace("the same sentence — *</span>", "the same sentence — </span>", 1)
if "*" in plain(h.html):
    raise SystemExit("an asterisk is left after %d" % stars)

# ------------------------------------------------------------ 1 Reading
for n in range(1, 6):
    h.item_box("1.2", n, where="options")
h.options_on_lines("1.2")
for n in range(1, 5):
    h.item_box("1.3", n, where="leader")
for n in range(1, 5):
    h.item_box("1.4", n, width="190px", where="leader")

# ------------------------------------------------------------ 2 Grammar
answer_first("2.3", "Your question")
for n in range(1, 7):
    h.item_box("2.4", n, where="leader")
h.options_on_lines("2.5")
for n in range(1, 8):
    h.item_box("2.6", n, where="leader")
for n in range(1, 6):
    h.item_box("2.11", n, where="leader")
h.leaders("2.12", "2.13  </span>", [(1, W, "Three subject and three object questions")])

# ------------------------------------------------------------ 3 Vocabulary
MEANINGS31, NEW31 = halves("3.1", "a-h", relabel="dgahbfce")
WB33 = [("argue → the noun (thing)", "argument"), ("argue → the adjective", "argumentative"),
        ("advise → the noun (thing)", "advice"), ("advise → the adjective", "advisable"),
        ("support → the noun (thing)", "support"), ("support → the adjective", "supportive"),
        ("honesty → the adjective", "honest"), ("loyalty → the adjective", "loyal")]
a = h.html.index('<table class="bk">', section("3.3"))
b = h.html.index("</table>", a) + len("</table>")
h.html = h.html[:a] + ('<p style="margin-bottom:6px"><span style="color:#6E6E6E">Example: communicate → '
                       'communication · communicator · communicative</span></p>') + "".join(
    item_p("3.3", n, html.escape(t), "{{box:3.3:%d:140px:}}" % n) for n, (t, _a) in enumerate(WB33, 1)) + h.html[b:]
SITUATIONS35, _n = halves("3.5", "a-e")
FORMS37 = {1: ["very", "absolutely"], 2: ["very", "absolutely"], 3: ["really", "very"], 4: ["quite", "absolutely"],
           5: ["very", "absolutely"], 6: ["a bit", "absolutely"]}
boxes_for("3.7", FORMS37)
h.options_on_lines("3.8")
ODD39 = {n: [re.sub(r"\s*\((friend|extreme)\)$", "", w) for w in ws]
         for n, ws in h.odd_one_out("3.9", why="Why?").items()}
WITH311 = ["in touch", "up", "out", "to know"]
VERBS311 = ["keep", "get", "open", "fall", "catch"]
reword("3.11", "Tick (✓) the words that go with each verb. Some go with more than one.",
       "Which word goes with each verb in this section's phrases? Tap it.")
a = h.html.index('<table class="bk">', section("3.11"))
b = h.html.index("</table>", a) + len("</table>")
h.html = h.html[:a] + "".join(item_p("3.11", n, html.escape(v), "{{box:3.11:%d:60px:}}" % n)
                              for n, v in enumerate(VERBS311, 1)) + h.html[b:]
h.leaders("3.13", "3.14  </span>", [(1, W, "Three sentences, one for each")])
h.leaders("3.14", "4.1  </span>", [(1, W, "Five words, each with an example")])

# ------------------------------------------------------------ 4 Everyday English
for n in range(1, 5):
    h.item_box("4.2", n, where="leader")

# ------------------------------------------------------------ 5 Writing
h.leaders("5.1", "</div>", [(1, W, "Write your guide here")])

# ------------------------------------------------------------------ the key
K = {}
for n, a in enumerate("BBBBC", 1):
    K[("1.2", n, 1)] = choose(["A", "B", "C"], a)
for n in range(1, 5):
    K[("1.3", n, 1)] = own()
for n, a in enumerate(["superficial", "disappointments/disappointment", "the medium/medium",
                       "an acquaintance/acquaintance"], 1):
    K[("1.4", n, 1)] = Q(a)
for n, a in enumerate(["close", "superficial", "fears", "deeper", "version", "medium"], 1):
    K[("1.5", n, 1)] = Q(a)
AD = {"A": "A · agree", "D": "D · disagree"}
for n in range(1, 5):                             # their opinion
    K[("1.6", n, 1)] = choose(["A", "D"], labels=AD)
SO = {"S": "S · subject", "O": "O · object"}
for n, a in enumerate("SOSOSOSO", 1):
    K[("2.1", n, 1)] = choose(["S", "O"], a, labels=SO)
for key, a in (((1, 1), "sent"), ((2, 1), "did"), ((2, 2), "do"), ((3, 1), "taught"), ((4, 1), "came"),
               ((5, 1), "did"), ((5, 2), "meet"), ((6, 1), "happened"), ((7, 1), "uses"),
               ((8, 1), "did/is/was"), ((8, 2), "talk/talking")):
    K[("2.2",) + key] = Q(a)
for n, a in enumerate(["Who wrote the report", "What did she write", "Who paid for dinner",
                       either("What did he pay for", "What did he pay for?"), "What happened",
                       "Who did you call"], 1):
    K[("2.3", n, 1)] = write(a)
for n, a in enumerate(["Who did you invite", "Who invited you", "Who took your bag", "What did she say",
                       "How many people received the email", "Which film did you prefer"], 1):
    K[("2.4", n, 1)] = write(a)
for n, a in enumerate("ABBABB", 1):
    K[("2.5", n, 1)] = choose(["A", "B", "C", "D"], a)
TICKED = "✓/correct/tick"
for n, a in enumerate([
        either("Who told you that", "told"),
        either("What happened at the meeting", "happened"),
        either("Who did you invite to the party", "Who did you invite", "did you invite"),
        TICKED,
        either("How many students came to the lesson", "How many students came", "came"),
        TICKED,
        either("Who wrote this song", "wrote")], 1):
    K[("2.6", n, 1)] = fix(a)
for n, a in enumerate(["Who called", "Who did you", "What happened", "did you prefer"], 1):
    K[("2.7", n, 1)] = Q(a)
for n in range(1, 5):                             # samples in the key: many right questions
    K[("2.8", n, 1)] = own()
for n, a in enumerate([
        either("Who told you about the meeting", "Hi Aziz! Who told you about the meeting", "Who told you"),
        either("And what time did it start", "what time did it start", "did it start"),
        either("How many people came", "came"),
        either("Who did you speak to afterwards", "Who did you speak to", "did you speak")], 1):
    K[("2.9", n, 1)] = write(a)
for n, a in enumerate(["Who", "What/Who", "do", "What", "gives/contains/shows/has/expresses/states", "What"], 1):
    K[("2.10", n, 1)] = Q(a)
for n, a in enumerate([
        "Who invented the telephone",
        either('What does “acquaintance” mean', 'What does "acquaintance" mean', "What does acquaintance mean"),
        "How many friends do you have online",
        "Which app do teenagers use most",
        either("Who would you call at 3 a.m", "Who would you call at 3 am", "Who would you call at 3am")], 1):
    K[("2.11", n, 1)] = write(a)
K[("2.12", 1, 1)] = own()
for key, a in (((1, 1), "How many people came/How many people were/Who came/Who was"),
               ((2, 1), "Who gave/Who did/Who made"),
               ((3, 1), "What did you talk/What did you all talk/What were you talking")):
    K[("2.13",) + key] = Q(a)
for n, old in enumerate("bdcafehg", 1):          # the key's letters, lettered afresh
    K[("3.1", n, 1)] = choose(MEANINGS31, NEW31[old])
for key, a in (((1, 1), "catch up"), ((2, 1), "get to know"), ((3, 1), "opens up"), ((4, 1), "put my foot in it"),
               ((5, 1), "keep in touch"), ((6, 1), "sorted"), ((6, 2), "out"),
               ((7, 1), "get on well with/get on with/get along with"), ((8, 1), "fell out")):
    K[("3.2",) + key] = Q(a)
for n, (_t, a) in enumerate(WB33, 1):
    K[("3.3", n, 1)] = Q(a)
for n, a in enumerate(["honest", "advice", "argument", "supportive", "Loyalty", "communicative"], 1):
    K[("3.4", n, 1)] = Q(a)
for n, a in enumerate("badce", 1):
    K[("3.5", n, 1)] = choose(SITUATIONS35, a)
BOX36 = ["freezing", "enormous", "brilliant", "delicious", "exhausted", "astonished", "awful", "boiling"]
for n, a in enumerate(["brilliant", "awful", "exhausted", "freezing", "enormous", "astonished", "boiling",
                       "delicious"], 1):
    K[("3.6", n, 1)] = choose(BOX36, a)
for n, a in enumerate(["absolutely", "very", "really", "quite", "absolutely", "a bit"], 1):
    K[("3.7", n, 1)] = choose(FORMS37[n], a)
for n, a in enumerate("BCCBBA", 1):
    K[("3.8", n, 1)] = choose(["A", "B", "C", "D"], a)
for n, a in enumerate(["superficial", "tired", "put your foot in it", None, "give up"], 1):
    K[("3.9", n, 1)] = choose(ODD39[n], a)      # 4: the key says none really is
    K[("3.9", n, 2)] = own()
for n, a in enumerate(["got", "get", "open", "fell", "silly/trivial/stupid/ridiculous/small/unimportant",
                       "sorted", "touch"], 1):
    K[("3.10", n, 1)] = Q(a)
for n, a in enumerate(["in touch", "to know", "up", "out", "up"], 1):
    K[("3.11", n, 1)] = choose(WITH311, a)
for n, a in enumerate(["lifelong/childhood/old", "mutual", "make", "touch", "make", "loyal/reliable/trustworthy"], 1):
    K[("3.12", n, 1)] = Q(a)
K[("3.13", 1, 1)] = own()
K[("3.14", 1, 1)] = own()
for n in range(1, 5):
    K[("4.2", n, 1)] = own()
K[("5.1", 1, 1)] = own(control="essay")

if __name__ == "__main__":
    data = h.build(K, "Intermediate", 1, "Unit 1.1 — Talk")
    out = os.path.join(HERE, "i011.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
