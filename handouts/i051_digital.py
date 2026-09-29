"""I05.1 The natural world - Azamat's Intermediate booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(I05.1 The natural world - answer key), joined box by box by hand. At this
level the explanations stay English. The Desktop "new design" copy (21 Sep)
is used. Its fourth part is Everyday English and its fifth a paragraph to
write; there is no listening.

Put right here: 3.1's meanings ran almost a-h beside words 1-8 (only 1 and 2
swapped), so they are lettered in a different order.
Where the key gives samples but the prompt leaves one sentence (2.7), the
box is marked with every reasonable wording.

    python3 handouts/i051_digital.py            # writes handouts/i051.json, lists every box
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

DOCX = ("~/Desktop/Handouts/B1+ Intermediate/I05.1 The natural world/"
        "I05.1 The natural world — handout (new design).docx")
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
FORMS23 = {1: ["arrive", "will arrive"], 2: ["will", "is going to"], 3: ["leaves", "will leave"],
           4: ["will", "are going to"], 5: ["meet", "are meeting"], 6: ["comes", "will come"]}
boxes_for("2.3", FORMS23)
for n in range(1, 7):
    h.item_box("2.4", n, where="leader")
h.options_on_lines("2.6")
FORMS210 = {1: ["I'll", "I'm going to"], 2: ["help", "'ll help"], 3: ["are visiting", "will visit"],
            4: ["will", "are going to"], 5: ["might", "will"], 6: ["get", "will get"]}
boxes_for("2.10", FORMS210)
h.one_per_line("AN EMAIL TO A COLLEAGUE", "2.14  </span>", at="text")
h.options_on_lines("2.14")
h.leaders("2.15", "3.1  </span>", [(1, W, "Three plans and three predictions")])

# ------------------------------------------------------------ 3 Vocabulary
MEANINGS31, NEW31 = halves("3.1", "a-h", relabel="dgahbfce")
a = h.html.index('<table class="bk">', section("3.3"))
b = h.html.index("</table>", a) + len("</table>")
WB33 = [("conserve → the noun (thing)", "conservation"), ("conserve → the noun (person)", "conservationist"),
        ("protect → the noun (thing)", "protection"), ("protect → the noun (person)", "protector"),
        ("protect → the adjective", "protected/protective"), ("destroy → the noun (thing)", "destruction"),
        ("destroy → the adjective", "destructive"), ("recycle → the noun (thing)", "recycling"),
        ("recycle → the adjective", "recyclable/recycled"), ("sustain → the noun (thing)", "sustainability"),
        ("sustain → the adjective", "sustainable")]
h.html = h.html[:a] + ('<p style="margin-bottom:6px"><span style="color:#6E6E6E">Example: pollute → pollution · '
                       'polluter · polluted</span></p>') + "".join(
    item_p("3.3", n, html.escape(t), "{{box:3.3:%d:140px:}}" % n) for n, (t, _a) in enumerate(WB33, 1)) + h.html[b:]
FORMS35 = {1: ["protect", "protected"], 2: ["pollution", "polluted"], 3: ["sustain", "sustainable"],
           4: ["destroy", "destruction"], 5: ["conserve", "conservation"], 6: ["recycle", "recyclable"]}
boxes_for("3.5", FORMS35)
FORMS37 = {1: ["cut", "fall"], 2: ["protects", "prevents"], 3: ["damaged", "injured"], 4: ["tackle", "attack"],
           5: ["saves", "spends"], 6: ["threatens", "frightens"]}
boxes_for("3.7", FORMS37)
h.options_on_lines("3.11")
ODD312 = {1: ["drought", "flooding", "storm", "recycling"], 2: ["solar", "wind", "coal", "hydro"],
          3: ["protect", "preserve", "conserve", "destroy"], 4: ["emissions", "pollution", "waste", "conservation"]}
boxes_for("3.12", ODD312)
ENDS314, _n = halves("3.14", "a-e")
h.leaders("3.15", "4.1  </span>", [(1, W, "Four sentences about problems where you live")])

# ------------------------------------------------------------ 4 Everyday English
a = section("4.2")
b = h.html.index("4.3  </span>", a)
h.html = h.html[:a] + LEADER_P.sub("", h.html[a:b]).replace("<span class='tab'></span>", "") + h.html[b:]

# ------------------------------------------------------------ 5 Writing
h.leaders("5.1", "</div>", [(20, W, "Write your paragraph here")])

# ------------------------------------------------------------------ the key
K = {}
for n, a in enumerate("BBBAB", 1):
    K[("1.2", n, 1)] = choose(["A", "B", "C"], a)
for n in range(1, 5):
    K[("1.3", n, 1)] = own()
for n, a in enumerate(["monitor/to monitor/monitored", "flood defences/flood defenses",
                       "a drainage ditch/drainage ditch", "a nuisance/nuisance"], 1):
    K[("1.4", n, 1)] = Q(a)
for n, a in enumerate(["believed", "remove", "flow", "cleaner", "drainage", "expected"], 1):
    K[("1.5", n, 1)] = Q(a)
for n in range(1, 5):
    K[("1.6", n, 1)] = own()
AD = {"A": "A · agree", "D": "D · disagree"}
for n in range(1, 5):                             # their opinion
    K[("1.7", n, 1)] = choose(["A", "D"], labels=AD)
USES = {"P": "P · plan", "A": "A · arrangement", "Pr": "Pr · prediction", "D": "D · decision now"}
for n, a in enumerate(["P", "D", "A", "Pr", "Pr", "A", "P", "D"], 1):
    K[("2.1", n, 1)] = choose(["P", "A", "Pr", "D"], a, labels=USES)
for key, a in (((1, 1), either("will get", "'ll get", "is going to get")),
               ((2, 1), either("are visiting", "'re visiting", "are going to visit")),
               ((3, 1), either("is going to rain", "'s going to rain")), ((4, 1), "starts"),
               ((5, 1), either("'ll help", "will help")),
               ((6, 1), either("are going to build", "'re going to build", "are building")),
               ((7, 1), "Are"), ((7, 2), "coming"), ((8, 1), "may be")):
    K[("2.2",) + key] = Q(a)
for n, a in enumerate(["arrive", "is going to", "leaves", "will", "are meeting", "comes"], 1):
    K[("2.3", n, 1)] = choose(FORMS23[n], a)
TICKED = "✓/correct/tick"
for n, a in enumerate([
        either("I'll tell her as soon as I see her", "I will tell her as soon as I see her"),
        TICKED,
        either("Look at those clouds — it's going to rain", "Look at those clouds - it's going to rain",
               "Look at those clouds, it's going to rain", "it's going to rain", "it is going to rain"),
        TICKED,
        either("In my opinion it will be a very difficult winter", "In my opinion, it will be a very difficult winter",
               "In my opinion it'll be a very difficult winter"),
        either("What are you doing this evening", "What are you doing this evening? Are you free")], 1):
    K[("2.4", n, 1)] = fix(a)
for n, a in enumerate(["will/'ll/might/may/shall", "going", "Shall/Can/Should", "might/may/could",
                       "meeting/seeing", "leaves", "get/arrive", "are"], 1):
    K[("2.5", n, 1)] = Q(a)
for n, a in enumerate("CBCBB", 1):
    K[("2.6", n, 1)] = choose(["A", "B", "C", "D"], a)
for n, a in enumerate([
        either("Temperatures will rise by 2050", "Temperatures are going to rise by 2050"),
        either("We're meeting the council on Friday", "We are meeting the council on Friday"),
        either(*[s + " going to open a recycling " + c + " next year" for s in ("They're", "They are")
                 for c in ("centre", "center")]),
        either("That bag looks heavy — I'll carry it", "That bag looks heavy - I'll carry it",
               "That bag looks heavy, I'll carry it", "I'll carry it", "I will carry it"),
        "The exhibition opens at ten",
        either(*["It %s flood again this winter" % m for m in ("might", "may", "could")])], 1):
    K[("2.7", n, 1)] = write(a)
for n, a in enumerate([either("are going to plant", "'re going to plant"), "might rain",
                       either("'m seeing", "am seeing"), either("'ll carry", "will carry")], 1):
    K[("2.8", n, 1)] = Q(a)
for key, a in (((1, 1), either("will be living", "will live")), ((2, 1), either("won't know", "will not know")),
               ((3, 1), "arrives"), ((4, 1), "Are"), ((4, 2), "doing"),
               ((5, 1), either("is going to announce", "is announcing")), ((6, 1), either("will become", "'ll become"))):
    K[("2.9",) + key] = Q(a)
for n, a in enumerate(["I'm going to", "'ll help", "are visiting", "are going to", "might", "get"], 1):
    K[("2.10", n, 1)] = choose(FORMS210[n], a)
for n, a in enumerate([either("opens", "is opening"), either("are going to plant", "'re going to plant"),
                       either("will build", "'ll build"), "may take", either("'ll send", "will send"), "are"], 1):
    K[("2.11", n, 1)] = Q(a)
for n, a in enumerate(["come/get", "might/may/could/will", "are", "Shall"], 1):
    K[("2.12", n, 1)] = Q(a)
for n, a in enumerate([
        either("I'll call you when I get home this evening", "I will call you when I get home this evening"),
        either("Look at those clouds — I think it's going to rain in a minute",
               "Look at those clouds - I think it's going to rain in a minute",
               "I think it's going to rain in a minute", "it's going to rain in a minute"),
        either("What are you doing at the weekend? I mean your plans", "What are you doing at the weekend"),
        "The train leaves at 6.40 every morning"], 1):
    K[("2.13", n, 1)] = write(a)
for n, a in enumerate("CBBA", 1):
    K[("2.14", n, 1)] = choose(["A", "B", "C", "D"], a)
K[("2.15", 1, 1)] = own()
for n, old in enumerate("bacdefgh", 1):          # the key's letters, lettered afresh
    K[("3.1", n, 1)] = choose(MEANINGS31, NEW31[old])
for n, a in enumerate(["endangered", "Deforestation", "drought", "renewable", "emissions", "habitat",
                       "conservation", "sustainable"], 1):
    K[("3.2", n, 1)] = Q(a)
for n, (_t, a) in enumerate(WB33, 1):
    K[("3.3", n, 1)] = Q(a)
for n, a in enumerate(["pollution", "destruction", "conservationist", "recyclable", "protection", "sustainable",
                       "destructive", "polluted"], 1):
    K[("3.4", n, 1)] = Q(a)
for n, a in enumerate(["protected", "pollution", "sustainable", "destruction", "conservation", "recyclable"], 1):
    K[("3.5", n, 1)] = choose(FORMS35[n], a)
for n, a in enumerate(["cut/reduce", "protect/save", "preserve/destroy/protect", "tackle/solve",
                       "save/waste/renewable/solar/wind", "reduce/recycle/cut", "plant", "fossil"], 1):
    K[("3.6", n, 1)] = Q(a)
for n, a in enumerate(["cut", "protects", "damaged", "tackle", "saves", "threatens"], 1):
    K[("3.7", n, 1)] = choose(FORMS37[n], a)
BOX38 = ["carbon footprint", "fossil fuels", "global warming", "renewable energy", "single-use plastic",
         "food waste", "climate change", "greenhouse gases"]
for n, a in enumerate(["fossil fuels", "carbon footprint", "greenhouse gases", "renewable energy", "food waste",
                       "single-use plastic"], 1):
    K[("3.8", n, 1)] = choose(BOX38, a)
for n, a in enumerate(["non-renewable/nonrenewable", "unsustainable", "clean/unpolluted",
                       "destroy/harm/damage", "reduce/decrease/cut", "save/conserve"], 1):
    K[("3.9", n, 1)] = Q(a)
for n, a in enumerate(["reduce/cut", "renewable", "endangered", "tackle"], 1):
    K[("3.10", n, 1)] = Q(a)
for n, a in enumerate("ABBAC", 1):
    K[("3.11", n, 1)] = choose(["A", "B", "C", "D"], a)
for n, a in enumerate(["recycling", "coal", "destroy", "conservation"], 1):
    K[("3.12", n, 1)] = choose(ODD312[n], a)
for n, a in enumerate(["cost", "destroyed", "flooding", "footprint", "burst", "planted"], 1):
    K[("3.13", n, 1)] = Q(a)
for n, a in enumerate("badce", 1):
    K[("3.14", n, 1)] = choose(ENDS314, a)
K[("3.15", 1, 1)] = own()
LINKS = ["because", "because of", "so", "such as", "for example"]
for n, a in enumerate(["because of", "because", "so", "such as"], 1):
    K[("4.2", n, 1)] = choose(LINKS, a)
K[("5.1", 20, 1)] = own(control="essay")

if __name__ == "__main__":
    data = h.build(K, "Intermediate", 5, "Unit 5.1 — The natural world")
    out = os.path.join(HERE, "i051.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
