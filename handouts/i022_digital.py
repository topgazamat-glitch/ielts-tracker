"""I02.2 Modern life - Azamat's Intermediate booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(I02.2 Modern life - answer key), joined box by box by hand. At this level
the explanations stay English. The Desktop "new design" copy is used. Its
fourth part is Everyday English and its fifth an email to write; there is no
listening.

This key is out of step with the booklet. From 2.7 its numbers run one
behind (its 2.7 is the booklet's 2.8, its 2.9 the booklet's 2.10), and
from 3.5 two behind (its 3.5 is the booklet's 3.6, its 3.10 the booklet's
3.12). It has no answers for 2.7, 2.11, 2.12, 2.13, 3.5, 3.7 or 3.13, and only
six of 3.4's eight. Each answer is joined to its exercise by what it says, and
the missing ones are written here. 2.7 (questions for given answers) and
2.11 item 6 (any past participle) are left for the teacher. In 2.7 the
answer is shown first and the box for the question under it.

Put right here too: 3.1's meanings ran almost a-h beside words 1-8 (only
pairs swapped), so they are lettered in a different order. The
word-building table in 3.3 is one line per box.

    python3 handouts/i022_digital.py            # writes handouts/i022.json, lists every box
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

DOCX = ("~/Desktop/Handouts/B1+ Intermediate/I02.2 Modern life/"
        "I02.2 Modern life — handout (new design).docx")
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
FORMS23 = {1: ["read", "been reading"], 2: ["read", "been reading"], 3: ["known", "been knowing"],
           4: ["repaired", "been repairing"], 5: ["had", "been having"], 6: ["worked", "been working"]}
boxes_for("2.3", FORMS23)
for n in range(1, 7):
    h.item_box("2.4", n, where="leader")
h.options_on_lines("2.6")
for m in reversed(h._items("2.7")):               # the answer first, then the question to write for it
    tag = BLANK_TAG.search(m.group(4))
    said = re.sub(r"^\d+\s*\?\s*", "", plain(m.group(4))).strip()
    h.hints[int(tag.group(1))] = "How long …? or How many …?"
    h.html = (h.html[:m.start()] + m.group(1) + NUM_SPAN % int(m.group(3))
              + TEXT_SPAN % html.escape(said, quote=False) + "<br>" + tag.group(0) + "</p>" + h.html[m.end():])
h.options_on_lines("2.13")
h.leaders("2.14", "3  </span>", [(1, W, "Three simple, three continuous")])

# ------------------------------------------------------------ 3 Vocabulary
MEANINGS31, NEW31 = halves("3.1", "a-h", relabel="dgahbfce")
WB33 = [("develop → the noun (thing)", "development"), ("develop → the noun (person)", "developer"),
        ("develop → the adjective", "developed/developing"), ("use → the noun (thing)", "use/usage"),
        ("use → the noun (person)", "user"), ("use → the adjective", "useful/usable"),
        ("secure → the noun (thing)", "security"), ("secure → the adjective", "secure"),
        ("innovate → the noun (thing)", "innovation"), ("innovate → the noun (person)", "innovator"),
        ("innovate → the adjective", "innovative"), ("reliable → the noun (thing)", "reliability")]
a = h.html.index('<table class="bk">', section("3.3"))
b = h.html.index("</table>", a) + len("</table>")
h.html = h.html[:a] + ('<p style="margin-bottom:6px"><span style="color:#6E6E6E">Example: connect → connection · '
                       'connected</span></p>') + "".join(
    item_p("3.3", n, html.escape(t), "{{box:3.3:%d:140px:}}" % n) for n, (t, _a) in enumerate(WB33, 1)) + h.html[b:]
FORMS35 = {1: ["use", "useful"], 2: ["develop", "developer"], 3: ["connect", "connection"],
           4: ["secure", "security"], 5: ["innovate", "innovative"], 6: ["rely", "reliable"]}
boxes_for("3.5", FORMS35)
FORMS37 = {1: ["install", "update"], 2: ["crashed", "charged"], 3: ["back up", "log in"], 4: ["restart", "freeze"],
           5: ["froze", "installed"], 6: ["charge", "crash"]}
boxes_for("3.7", FORMS37)
h.options_on_lines("3.10")
ODD311 = {1: ["download", "install", "update", "crash"], 2: ["battery", "screen", "storage", "password"],
          3: ["developer", "user", "connection", "designer"], 4: ["useless", "brilliant", "slow", "enormous"]}
boxes_for("3.11", ODD311)
ENDS313, _n = halves("3.13", "a-e")
h.leaders("3.14", "4.1  </span>", [(1, W, "Four sentences about your own devices")])

# ------------------------------------------------------------ 4 Everyday English
for n in range(1, 5):
    h.item_box("4.2", n, where="leader")

# ------------------------------------------------------------ 5 Writing
h.leaders("5.1", "</div>", [(1, W, "Write your email here")])

# ------------------------------------------------------------------ the key
K = {}
for n, a in enumerate("BBBAB", 1):
    K[("1.2", n, 1)] = choose(["A", "B", "C"], a)
for n in range(1, 5):
    K[("1.3", n, 1)] = own()
for n, a in enumerate(["a feature/feature", "clutter", "resent", "the direction of travel/direction of travel"], 1):
    K[("1.4", n, 1)] = Q(a)
for n, a in enumerate(["asking", "use", "enjoyed", "features", "calm", "removing"], 1):
    K[("1.5", n, 1)] = Q(a)
for n in range(1, 5):
    K[("1.6", n, 1)] = own()
AD = {"A": "A · agree", "D": "D · disagree"}
for n in range(1, 5):                             # their opinion
    K[("1.7", n, 1)] = choose(["A", "D"], labels=AD)
SC = {"S": "S · simple", "C": "C · continuous"}
for n, a in enumerate("CSCSCSCS", 1):
    K[("2.1", n, 1)] = choose(["S", "C"], a, labels=SC)
for key, a in (((1, 1), either("have been using", "'ve been using", "have used", "'ve used")),
               ((2, 1), either("has downloaded", "'s downloaded")), ((3, 1), "have"), ((3, 2), "been waiting"),
               ((4, 1), either("haven't finished", "have not finished")),
               ((5, 1), either("has been acting", "'s been acting")),
               ((6, 1), either("have already backed up", "'ve already backed up")),
               ((7, 1), either("has been writing", "'s been writing")), ((8, 1), "have"), ((8, 2), "sent")):
    K[("2.2",) + key] = Q(a)
for n, a in enumerate(["read", "been reading", "known", "been repairing", "had", "been working"], 1):
    K[("2.3", n, 1)] = choose(FORMS23[n], a)
TICKED = "✓/correct/tick"
for n, a in enumerate([
        either("I've owned this laptop for five years", "I have owned this laptop for five years", "owned",
               "I've had this laptop for five years", "I have had this laptop for five years"),
        TICKED,
        either("She's sent three emails this morning", "She has sent three emails this morning", "sent"),
        either("We've been waiting for two hours", "We have been waiting for two hours", "for two hours"),
        TICKED,
        either("I've finished the report", "I have finished the report", "finished")], 1):
    K[("2.4", n, 1)] = fix(a)
for n, a in enumerate(["written", "read", "sent", "made", "taken", "bought", "kept", "lost", "built", "chosen"], 1):
    K[("2.5", n, 1)] = Q(a)
for n, a in enumerate("CABCC", 1):
    K[("2.6", n, 1)] = choose(["A", "B", "C", "D"], a)
for n in range(1, 7):                             # the key has none; many right questions
    K[("2.7", n, 1)] = own()
for n, a in enumerate([either("have been using", "'ve been using"),
                       either(*[s + " " + v + " since" for s in ("has been", "'s been")
                                for v in ("doing the course", "doing it", "studying", "taking the course",
                                          "on the course")]),
                       either("have had", "'ve had"), either("has been raining", "'s been raining")], 1):
    K[("2.8", n, 1)] = Q(a)
for key, a in (((1, 1), either("has been getting", "'s been getting")), ((2, 1), either("have deleted", "'ve deleted")),
               ((3, 1), either("has been trying", "'s been trying")),
               ((4, 1), either("haven't decided", "have not decided")),
               ((5, 1), "have"), ((5, 2), "restarted"), ((6, 1), either("have been testing", "'ve been testing"))):
    K[("2.9",) + key] = Q(a)
for n, a in enumerate(["have you been doing", either("'ve been updating", "have been updating"), "have you finished",
                       "started", "has each one taken", either("'ve never seen", "have never seen")], 1):
    K[("2.10", n, 1)] = Q(a)
for n, a in enumerate(["been", "has", "long", "yet", "since"], 1):
    K[("2.11", n, 1)] = Q(a)
K[("2.11", 6, 1)] = own(control=None)             # any past participle: restarted, tried, checked...
for n, a in enumerate([
        either("I've sent you three emails this week", "I have sent you three emails this week",
               "Hi Aziz. I've sent you three emails this week", "sent"),
        either("I've known about the problem since Monday", "I have known about the problem since Monday", "known"),
        either("We've been testing the system for two weeks", "We have been testing the system for two weeks",
               "for two weeks"),
        either("How many times have you restarted it", "restarted")], 1):
    K[("2.12", n, 1)] = write(a)
for n, a in enumerate("CBBC", 1):
    K[("2.13", n, 1)] = choose(["A", "B", "C", "D"], a)
K[("2.14", 1, 1)] = own()
for n, old in enumerate("badcfehg", 1):          # the key's letters, lettered afresh
    K[("3.1", n, 1)] = choose(MEANINGS31, NEW31[old])
for n, a in enumerate(["froze", "back up", "crashed", "install/download", "log in", "updated", "charge", "restart"], 1):
    K[("3.2", n, 1)] = Q(a)
for n, (_t, a) in enumerate(WB33, 1):
    K[("3.3", n, 1)] = Q(a)
for n, a in enumerate(["users", "connection", "developer", "security", "innovation", "reliable", "useful",
                       "reliable"], 1):
    K[("3.4", n, 1)] = Q(a)
for n, a in enumerate(["useful", "developer", "connection", "secure", "innovative", "reliable"], 1):
    K[("3.5", n, 1)] = choose(FORMS35[n], a)
for n, a in enumerate(["download/install", "back", "log", "charge", "install/update/download", "restart/reboot",
                       "change/enter/reset/type", "send/read/write/delete"], 1):
    K[("3.6", n, 1)] = Q(a)
for n, a in enumerate(["update", "crashed", "back up", "restart", "froze", "charge"], 1):
    K[("3.7", n, 1)] = choose(FORMS37[n], a)
BOX38 = ["battery", "screen", "password", "settings", "storage", "notification", "device", "update"]
for n, a in enumerate(["battery", "storage", "settings", "notification", "password", "update"], 1):
    K[("3.8", n, 1)] = choose(BOX38, a)
for n, a in enumerate(["awful/terrible/horrible/dreadful",
                       "brilliant/excellent/fantastic/amazing/wonderful/superb",
                       "painfully slow/useless/unbearably slow",
                       "astonishing/amazing/astounding/incredible/shocking",
                       "essential/invaluable/indispensable",
                       "enormous/huge/massive/gigantic"], 1):
    K[("3.9", n, 1)] = Q(a)
for n, a in enumerate("BAACC", 1):
    K[("3.10", n, 1)] = choose(["A", "B", "C", "D"], a)
for n, a in enumerate(["crash", "password", "connection", "slow"], 1):
    K[("3.11", n, 1)] = choose(ODD311[n], a)
for n, a in enumerate(["logged", "crashed", "restarted/rebooted", "froze", "backed", "update"], 1):
    K[("3.12", n, 1)] = Q(a)
for n, a in enumerate("bdace", 1):
    K[("3.13", n, 1)] = choose(ENDS313, a)
K[("3.14", 1, 1)] = own()
for n in range(1, 5):
    K[("4.2", n, 1)] = own()
K[("5.1", 1, 1)] = own(control="essay")

if __name__ == "__main__":
    data = h.build(K, "Intermediate", 2, "Unit 2.2 — Modern life")
    out = os.path.join(HERE, "i022.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
