"""I09AC Entertainment - Azamat's Intermediate booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(I09AC Entertainment - ANSWER KEY), joined box by box by hand. At this level
the explanations stay English. Built from the Material Bank copy: his
Desktop redesign has the same exercises but would not split into parts.

Where the key gives samples but the words around the gap leave only one
sensible answer (3.8's based, set, plot, cast, watching; 3.10), the box is
marked, with every reasonable wording accepted; the two gaps in 3.8 that
really are a matter of taste (4 and 5) are his to read.

What a phone gets that paper does not:
  - taps for every choice: A/B/C, T/F/NG, the paragraph, passive or active,
    the tense, by or with, the form in the streaming text, -ed or -ing, the
    three -ed sounds, the word from the box, the other half, Ava or Lucas,
    who did what, recommending or responding, the words for waiting;
  - boxes where paper has none: 1.9, 2.1, 2.6, 2.7, 3.1, 3.7, 4.2.

    python3 handouts/i09ac_digital.py            # writes handouts/i09ac.json, lists every box
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

DOCX = ("~/Documents/Claude/Material Bank/General English/B1 Intermediate/_NEW BOOKLET STYLE/"
        "I09AC Entertainment — BOOKLET.docx")
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


def one_choice_a_line(label):
    """Two choices in one item: each group of chips on a line of its own."""
    h.html = re.sub(r"(\{\{box:%s:\d+:[^}]*\}\}) (\{\{box:%s:)" % (re.escape(label), re.escape(label)),
                    r"\1<br>\2", h.html)


# ------------------------------------------------------------ 1 Reading
for n in range(1, 5):
    h.item_box("1.2", n)
h.options_on_lines("1.2")
for n in range(1, 5):
    h.item_box("1.4", n, width="190px", where="leader")
for n in range(1, 5):
    h.item_box("1.5", n, where="leader")
h.leaders("1.6", "1.7  </span>", [(1, W, "Five passive verbs from the text")])
for n in range(1, 5):
    h.item_box("1.9", n, where="leader")

# ------------------------------------------------------------ 2 Grammar
PASSIVE21 = {1: "passive", 2: "active", 3: "passive", 4: "passive", 5: "passive", 6: "passive", 7: "active"}
for n in PASSIVE21:
    h.item_box("2.1", n)
for n in range(2, 9):                             # item 1 is the worked example
    h.item_box("2.6", n)
# 2.7: a box after each numbered choice in the text
FORMS27 = {1: ["has streamed", "has been streamed"], 2: ["started", "was started"], 3: ["has", "is had"],
           4: ["values", "is valued"], 5: ["spends", "is spent"], 6: ["has streamed", "has been streamed"],
           7: ["has taken over", "has been taken over"], 8: ["comes", "is come"]}
a = h.html.index("STREAMING, IN NUMBERS")
b = h.html.index("2.8  </span>", a)
part = h.html[a:b]
for n in FORMS27:
    at = part.index("(%d)" % n) + len("(%d)" % n)
    part = part[:at] + " {{box:2.7:%d:60px:}}" % n + part[at:]
    h.texts[("2.7", n)] = "(%d) %s" % (n, " / ".join(FORMS27[n]))
h.html = h.html[:a] + part + h.html[b:]

# ------------------------------------------------------------ 3 Vocabulary
ADJ31 = {1: [["disappointing", "disappointed"]], 2: [["interesting", "interested"]],
         3: [["amusing", "amused"], ["boring", "bored"]], 4: [["motivating", "motivated"]],
         5: [["depressing", "depressed"]], 6: [["interesting", "interested"]]}
for n, groups in ADJ31.items():
    for _g in groups:
        h.item_box("3.1", n)
one_choice_a_line("3.1")
SOUNDS = h.sort_words("3.3", ["amused", "bored", "depressed", "disappointed", "fascinated", "interested",
                              "motivated"], "/d/")
# 3.6: the endings first, as a key; then each beginning, with a-e to tap
a = h.html.index('<table class="bk">', section("3.6"))
b = h.html.index("</table>", a) + len("</table>")
cells = [plain(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", h.html[a:b], re.S)]
begins = [re.match(r"(\d+)\s+(.*)", c).groups() for c in cells if re.match(r"\d+\s", c)]
ENDS36 = sorted(re.match(r"([a-e])\s+(.*)", c).groups() for c in cells if re.match(r"[a-e]\s", c))
h.html = h.html[:a] + key_list(ENDS36) + "".join(
    item_p("3.6", int(n), html.escape(t, quote=False), "{{box:3.6:%s:60px:}}" % n) for n, t in begins) + h.html[b:]
for n in range(1, 6):
    h.item_box("3.7", n, where="leader")

# ------------------------------------------------------------ 4 Listening
for n in range(1, 4):
    h.item_box("4.2", n, where="leader")
for n in range(1, 8):
    h.item_box("4.3", n, where="leader")
for n in range(1, 4):
    h.item_box("4.8", n)
h.options_on_lines("4.8")

# ------------------------------------------------------------ 5 Everyday English
h.leaders("5.1", "5.2  </span>", [(1, W, "The three activities"), (2, W, "What they decide")])
# 5.6: each phrase on a line of its own, its gap where it is, and whether it is formal
a = h.html.index('<table class="bk">', section("5.6"))
a = h.html.index('<table class="bk">', h.html.index("</table>", a))       # past the word box
b = h.html.index("</table>", a) + len("</table>")
PHRASES56 = [("", " on", "informal"), ("", " a minute", "informal"), ("a minute / a ", "", "informal"),
             ("One moment, ", "", "formal"), ("Let me ", " (for you).", "informal")]
rows = ""
for n, (before, after, reg) in enumerate(PHRASES56, 1):
    h.texts[("5.6", n)] = "%s…%s (%s)" % (before, after, reg)
    rows += ('<p data-item="5.6:%d" %s>%s%s</p>'
             % (n, ITEM_STYLE, NUM_SPAN % n, TEXT_SPAN % ('%s……%s  <span style="color:#6E6E6E">· %s</span>'
                                                          '  {{box:5.6:%d:60px:}}'
                                                          % (html.escape(before), html.escape(after), reg, n))))
h.html = h.html[:a] + rows + h.html[b:]
at = section("5.6")
end = h.html.index("</p>", at)
h.html = h.html[:at] + h.html[at:end].replace("Complete the table.", "Complete each phrase.", 1) + h.html[end:]
for n in range(1, 5):
    h.item_box("5.8", n, where="leader")

# ------------------------------------------------------------------ the key
K = {}
for n, a in enumerate("BABC", 1):
    K[("1.2", n, 1)] = choose(["A", "B", "C"], a)
TFNG = {"T": "T · true", "F": "F · false", "NG": "NG · not given"}
for n, a in enumerate(["T", "T", "F", "NG", "NG", "F"], 1):
    K[("1.3", n, 1)] = choose(["T", "F", "NG"], a, labels=TFNG)
for n, a in enumerate(["a cliffhanger/cliffhanger", "hooked/be hooked/to be hooked",
                       "a strange flatness/strange flatness/flatness", "to lose its grip/lose its grip"], 1):
    K[("1.4", n, 1)] = Q(a)
for n in range(1, 5):
    K[("1.5", n, 1)] = own()
K[("1.6", 1, 1)] = own()
for n, a in enumerate(["started", "criticised/criticized", "report", "told", "delivery", "off", "lose"], 1):
    K[("1.7", n, 1)] = Q(a)
# as numbered: 1 a practical list 2 evidence from research 3 how it is designed 4 the other side
for n, a in enumerate("5324", 1):
    K[("1.8", n, 1)] = choose(["1", "2", "3", "4", "5"], a)
for n in range(1, 5):                             # the correction, in their words
    K[("1.9", n, 1)] = own()
for n in range(1, 5):                             # notes, compared in class
    K[("1.10", n, 1)] = own(control=None)
for n, a in PASSIVE21.items():
    K[("2.1", n, 1)] = choose(["passive", "active"], a)
TENSES = ["present simple", "present continuous", "past simple", "present perfect", "will", "modal"]
# as numbered: 1 was controlled 2 is released 3 has been criticised 4 can be reduced 5 are being made
# 6 will be announced
for n, a in enumerate(["past simple", "present simple", "present perfect", "modal", "present continuous",
                       "will"], 1):
    K[("2.2", n, 1)] = choose(TENSES, a)
for n, a in enumerate([
        "My laptop was stolen from the office",
        either("The special effects are created by a computer program",
               "The special effects are created by a computer programme"),
        "The film is being made in Brazil",
        "The results will be announced tomorrow",
        either("I was given this watch by my grandfather", "This watch was given to me by my grandfather",
               "I was given this watch"),
        "My car was being repaired at the time"], 1):
    K[("2.3", n, 1)] = write(a)
for n, a in enumerate([
        either("The work won't be finished by Saturday", "The work will not be finished by Saturday"),
        "Is the film being made in Brazil",
        "Are tomatoes grown in Spain",
        either("The car wasn't being driven too fast", "The car was not being driven too fast"),
        either("The sculpture hasn't been taken to the museum", "The sculpture has not been taken to the museum")],
        1):
    K[("2.4", n, 1)] = write(a)
for n, a in enumerate(["by", "with", "with", "by", "with", "by"], 1):
    K[("2.5", n, 1)] = choose(["by", "with"], a)
TICKED = "✓/correct/tick"
for n, a in zip(range(2, 9), [
        "The letter was sent yesterday",
        "The situation changed last year",
        "The results will be announced tomorrow",
        "It will be sent to you this afternoon",
        "We thought it was a good idea",
        TICKED,
        TICKED]):
    K[("2.6", n, 1)] = fix(a)
ANS27 = {1: "has been streamed", 2: "was started", 3: "has", 4: "is valued", 5: "spends", 6: "has been streamed",
         7: "has been taken over", 8: "comes"}
for n, a in ANS27.items():
    K[("2.7", n, 1)] = choose(FORMS27[n], a)
for n, a in enumerate(["was filmed", "happened", "are released", "arrived", "will be sent",
                       either("has changed", "'s changed")], 1):
    K[("2.8", n, 1)] = Q(a)
for n, a in enumerate([
        either("Binge watching has been criticised by doctors", "Binge watching has been criticized by doctors"),
        "The trailer was edited by a team in Vancouver",
        either("The lift hasn't been repaired", "The lift has not been repaired"),
        "The whole series is filmed in three months"], 1):
    K[("2.10", n, 1)] = write(a)
for n, a in enumerate("BCAB", 1):
    K[("2.11", n, 1)] = choose(["A", "B", "C"], a)
ANS31 = {1: ["disappointing"], 2: ["interesting"], 3: ["amused", "bored"], 4: ["motivating"],
         5: ["depressing"], 6: ["interested"]}
for n, groups in ADJ31.items():
    for k, (opts, a) in enumerate(zip(groups, ANS31[n]), 1):
        K[("3.1", n, k)] = choose(opts, a)
K[("3.2", 1, 1)] = choose(["a", "b"], "a")        # describes the film
K[("3.2", 2, 1)] = choose(["a", "b"], "b")        # describes the speaker
SOUND = {"amused": "/d/", "bored": "/d/", "depressed": "/t/"}
for n, w in enumerate(SOUNDS, 1):
    K[("3.3", n, 1)] = choose(["/d/", "/t/", "/ɪd/"], SOUND.get(w, "/ɪd/"))
for n, a in enumerate(["interested", "depressing", "disappointing", "amused", "motivated", "fascinating"], 1):
    K[("3.4", n, 1)] = Q(a)
BOX35 = ["based", "cast", "cliffhanger", "episode", "plot", "set", "soundtrack", "stars"]
for key, a in (((1, 1), "based"), ((2, 1), "plot"), ((3, 1), "set"), ((4, 1), "soundtrack"),
               ((5, 1), "episode"), ((5, 2), "cliffhanger"), ((6, 1), "stars"), ((6, 2), "cast")):
    K[("3.5",) + key] = choose(BOX35, a)
for n, a in enumerate("cdabe", 1):
    K[("3.6", n, 1)] = choose([l for l, _t in ENDS36], a)
for n, a in enumerate([
        either("I was very bored during the second episode", "I was very bored"),
        either("It's based on a novel by Tolstoy", "It is based on a novel by Tolstoy"),
        either("The film was directed by a director from Poland", "The film was made by a director from Poland",
               "The film was set in Poland"),
        either("I'm not a fan of it. I couldn't get into it", "I couldn't get into it"),
        either("That was the most interesting documentary I've seen",
               "That was the most interesting documentary I have seen")], 1):
    K[("3.7", n, 1)] = write(a)
for n, a in {1: "based", 2: "set", 3: "plot", 6: "cast", 7: "watching/watching it"}.items():
    K[("3.8", n, 1)] = Q(a)
K[("3.8", 4, 1)] = own(control=None)              # a matter of taste: his to read
K[("3.8", 5, 1)] = own(control=None)
for n, a in enumerate([
        either("was fascinated by the documentary", "was fascinated by it", "was fascinated with the documentary",
               "found the documentary fascinating", "found it fascinating"),
        either("was disappointing", "was a disappointing one"),
        "depressing",
        either("amusing", "very amusing", "amusing at all")], 1):
    K[("3.10", n, 1)] = Q(a)
for n in range(1, 6):                             # their own notes
    K[("3.12", n, 1)] = own(control=None)
for n, a in enumerate("BCBB", 1):
    K[("3.13", n, 1)] = choose(["A", "B", "C"], a)
for n in range(1, 7):                             # what they think: nothing to mark
    K[("4.1", n, 1)] = tick()
K[("4.2", 1, 1)] = choose(["Ava", "Lucas"], "Ava")
K[("4.2", 2, 1)] = choose(["Ava", "Lucas"], "Lucas")
K[("4.2", 3, 1)] = own(control=None)
for n in range(1, 8):
    K[("4.3", n, 1)] = own()
for key, a in (((1, 1), "disappointing"), ((2, 1), "interesting"), ((3, 1), "amused"), ((3, 2), "fascinated"),
               ((3, 3), "bored"), ((4, 1), "motivating"), ((5, 1), "depressing"), ((6, 1), "interested")):
    K[("4.4",) + key] = Q(a)
AL = {"A": "A · Ava", "L": "L · Lucas"}
for n, a in enumerate("ALAL", 1):
    K[("4.7", n, 1)] = choose(["A", "L"], a, labels=AL)
for n in range(1, 4):
    K[("4.8", n, 1)] = choose(["A", "B"], "B")
K[("5.1", 1, 1)] = own()
K[("5.1", 2, 1)] = own()
NAMES = ["Becky", "Rachel", "Tom", "Mark"]
for n, a in enumerate(["Becky", "Rachel", "Becky", "Tom", "Mark"], 1):
    K[("5.2", n, 1)] = choose(NAMES, a)
RRP = {"R": "R · recommending", "Rp": "Rp · responding"}
# as numbered: 1 great idea 2 meant to be 3 recommended 4 supposed to be 5 not a big fan 6 why don't we
# 7 great reviews 8 I doubt 9 you'd love it 10 sounds interesting, but
for n, a in enumerate(["Rp", "R", "R", "R", "Rp", "R", "R", "Rp", "R", "Rp"], 1):
    K[("5.3", n, 1)] = choose(["R", "Rp"], a, labels=RRP)
for n, a in enumerate(["meant", "supposed", "recommended", "reviews", "fan", "doubt"], 1):
    K[("5.4", n, 1)] = Q(a)
for n, a in enumerate([
        either("No, I bought the blue ones", "No, I bought the blue shoes", "No, the blue ones",
               "I bought the blue ones", "No, blue"),
        either("No, I went to the theatre", "No, I went to the theatre with John", "No, to the theatre",
               "I went to the theatre", "No, I went to the theater", "No, the theatre"),
        either("No, it was filmed in London", "No, in London", "It was filmed in London", "No, London"),
        either("No, it came out in March", "No, in March", "It came out in March", "No, March")], 1):
    K[("5.5", n, 1)] = write(a)
BOX56 = ["check", "hang", "please", "second", "wait"]
for n, a in enumerate(["hang", "wait", "second", "please", "check"], 1):
    K[("5.6", n, 1)] = choose(BOX56, a)
for n in range(1, 5):
    K[("5.8", n, 1)] = own()
for n in range(1, 7):                             # the checklist
    K[("5.9", n, 1)] = tick()

if __name__ == "__main__":
    data = h.build(K, "Intermediate", 9, "Unit 9A & 9C — Entertainment")
    out = os.path.join(HERE, "i09ac.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
