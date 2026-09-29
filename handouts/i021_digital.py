"""I02.1 Modern life - Azamat's Intermediate booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(I02.1 Modern life - answer key), joined box by box by hand. At this level
the explanations stay English. The Desktop "new design" copy is used. Its
fourth part is Everyday English and its fifth an email to write; there is no
listening.

This key is out of step with the booklet. From 2.6 its numbers run behind
(its 2.6 is the booklet's 2.7, its 2.9 the booklet's 2.11; its 3.7 is the
booklet's 3.8, its 3.9 the booklet's 3.11). It has no answers for 2.6, 2.10,
2.12, 2.13, 2.14, 3.7, 3.9, 3.12, 3.13 or 3.14, and only four of 2.9's six
questions. Each answer is joined to its exercise by what it says, and the
missing ones are written here.

2.9 and 2.13 leave no gaps on paper (write the question; correct the line):
each item gets a box.

    python3 handouts/i021_digital.py            # writes handouts/i021.json, lists every box
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

DOCX = ("~/Desktop/Handouts/B1+ Intermediate/I02.1 Modern life/"
        "I02.1 Modern life — handout (new design).docx")
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

# ------------------------------------------------------------ 2 Grammar
boxes_for("2.1", range(1, 9))
for n in range(1, 7):
    h.item_box("2.4", n, where="leader")
h.options_on_lines("2.5")
for n in range(1, 7):
    h.item_box("2.9", n)
h.options_on_lines("2.11")
for n in range(1, 7):
    h.item_box("2.13", n)
h.options_on_lines("2.14")
h.leaders("2.15", "3  </span>", [(1, W, "Three present perfect, three past simple")])

# ------------------------------------------------------------ 3 Vocabulary
MEANINGS31, NEW31 = halves("3.1", "a-h", relabel="dgahbfce")
WB33 = [("train → the noun (thing)", "training"), ("train → the noun (person)", "trainer/trainee"),
        ("qualify → the noun (thing)", "qualification"), ("qualify → the adjective", "qualified"),
        ("manage → the noun (thing)", "management"), ("manage → the noun (person)", "manager"),
        ("manage → the adjective", "managerial"), ("apply → the noun (thing)", "application"),
        ("apply → the noun (person)", "applicant"), ("retire → the noun (thing)", "retirement")]
a = h.html.index('<table class="bk">', section("3.3"))
b = h.html.index("</table>", a) + len("</table>")
h.html = h.html[:a] + ('<p style="margin-bottom:6px"><span style="color:#6E6E6E">Example: employ → employment · '
                       'employer / employee · employed</span></p>') + "".join(
    item_p("3.3", n, html.escape(t), "{{box:3.3:%d:140px:}}" % n) for n, (t, _a) in enumerate(WB33, 1)) + h.html[b:]
PHRASES35, _n = halves("3.5", "a-e")
FORMS36 = {1: ["a work", "work"], 2: ["job", "career"], 3: ["job", "profession"], 4: ["a job", "a work"],
           5: ["work", "job"], 6: ["work", "job"]}
boxes_for("3.6", FORMS36)
h.options_on_lines("3.8")
ODD310 = {1: ["salary", "wages", "income", "profession"], 2: ["apply for", "turn down", "hand in", "gain"],
          3: ["employer", "employee", "employment", "manager"], 4: ["promoted", "redundant", "qualified", "trained"]}
boxes_for("3.10", ODD310)
ENDS313, _n = halves("3.13", "a-e")
FORMS314 = {1: ["make", "gain"], 2: ["handed", "gave"], 3: ["taking", "making"], 4: ["made", "done"],
            5: ["job", "profession"], 6: ["work", "a work"]}
boxes_for("3.14", FORMS314)
h.leaders("3.15", "4.1  </span>", [(1, W, "Four sentences about your work or study history")])

# ------------------------------------------------------------ 4 Everyday English
for n in range(1, 5):
    h.item_box("4.2", n, where="leader")

# ------------------------------------------------------------ 5 Writing
h.leaders("5.1", "</div>", [(1, W, "Write your email here")])

# ------------------------------------------------------------------ the key
K = {}
for n, a in enumerate("BCBAB", 1):
    K[("1.2", n, 1)] = choose(["A", "B", "C"], a)
for n in range(1, 5):
    K[("1.3", n, 1)] = own()
for n, a in enumerate(["a candidate/candidate", "turn down", "likeability", "qualifications"], 1):
    K[("1.4", n, 1)] = Q(a)
for n, a in enumerate(["recruitment", "people/candidates", "qualifications", "likeability", "taught",
                       "examples"], 1):
    K[("1.5", n, 1)] = Q(a)
AD = {"A": "A · agree", "D": "D · disagree"}
for n in range(1, 5):                             # their opinion
    K[("1.6", n, 1)] = choose(["A", "D"], labels=AD)
TENSES = {"PP": "PP · present perfect", "PS": "PS · past simple"}
for n, a in enumerate(["PP", "PS"] * 4, 1):
    K[("2.1", n, 1)] = choose(["PP", "PS"], a, labels=TENSES)
for key, a in (((1, 1), either("have worked", "'ve worked", "have been working", "'ve been working")),
               ((2, 1), "left"), ((3, 1), "Have"), ((3, 2), "had"),
               ((4, 1), either("hasn't finished", "has not finished")), ((5, 1), "opened"),
               ((6, 1), either("have already interviewed", "'ve already interviewed")),
               ((7, 1), "did"), ((7, 2), "arrive"), ((8, 1), either("have never been", "'ve never been"))):
    K[("2.2",) + key] = Q(a)
for n, a in enumerate(["for", "since", "since", "for", "since", "for", "since", "for"], 1):
    K[("2.3", n, 1)] = choose(["for", "since"], a)
TICKED = "✓/correct/tick"
for n, a in enumerate([
        either("I saw him yesterday at the office", "I saw him at the office yesterday", "saw"),
        either("She has worked here for ten years", "She's worked here for ten years", "for ten years", "for"),
        TICKED,
        either("He went to Samarkand last week", "went"),
        TICKED,
        either("Have you ever had a job you loved", "Have you ever had")], 1):
    K[("2.4", n, 1)] = fix(a)
for n, a in enumerate("BCBBB", 1):
    K[("2.5", n, 1)] = choose(["A", "B", "C", "D"], a)
PARTS26 = [("was/were", "been"), ("went", "gone"), ("had", "had"), ("took", "taken"), ("left", "left"),
           ("wrote", "written"), ("gave", "given"), ("made", "made"), ("found", "found"), ("became", "become")]
for n, (past, participle) in enumerate(PARTS26, 1):
    K[("2.6", n, 1)] = Q(past)
    K[("2.6", n, 2)] = Q(participle)
for n, a in enumerate([either("has worked here since", "'s worked here since", "has been working here since",
                              "'s been working here since"),
                       either("have never been", "'ve never been"),
                       either("haven't seen him", "have not seen him"),
                       either(*[s + " " + v + " for" for s in ("has been", "'s been")
                                for v in ("doing the course", "on the course", "doing it", "studying",
                                          "taking the course")])], 1):
    K[("2.7", n, 1)] = Q(a)
for n, a in enumerate([either("have you worked", "have you been working"), either("'ve been", "have been"),
                       "did you leave", "left", "Have you ever managed", "led"], 1):
    K[("2.8", n, 1)] = Q(a)
for n, a in enumerate(["Have you ever worked at night", "Have you ever had an interview in English",
                       "Have you ever applied for a job online",
                       either("Have you ever turned down a job offer", "Have you ever turned a job offer down"),
                       "Have you ever worked in another city",
                       either("Have you ever trained someone else", "Have you ever trained anyone else")], 1):
    K[("2.9", n, 1)] = write(a)
for key, a in (((1, 1), either("have visited", "'ve visited")), ((2, 1), either("have ever seen", "'ve ever seen")),
               ((3, 1), either("hasn't replied", "has not replied")), ((4, 1), "have"), ((4, 2), "had"),
               ((5, 1), "sent"),
               ((6, 1), either("have worked", "'ve worked", "have been working", "'ve been working"))):
    K[("2.10",) + key] = Q(a)
for n, a in enumerate("BBCB", 1):
    K[("2.11", n, 1)] = choose(["A", "B", "C", "D"], a)
for n, a in enumerate([either("'ve been", "have been"), "started", either("has been", "'s been"), "lost",
                       either("took on", "'ve taken on", "have taken on"),
                       either("haven't had", "have not had"), "did your project go"], 1):
    K[("2.12", n, 1)] = Q(a)
for n, a in enumerate([
        "I applied yesterday",
        either("She has worked here since 2020", "She's worked here since 2020", "She has been working here since 2020",
               "She's been working here since 2020"),
        "Have you ever been abroad",
        "He left the company in May",
        either("We have known each other for years", "We've known each other for years"),
        either("Did you finish it yesterday", "Have you finished it already", "Have you already finished it")], 1):
    K[("2.13", n, 1)] = write(a)
for n, a in enumerate("BBCB", 1):
    K[("2.14", n, 1)] = choose(["A", "B", "C", "D"], a)
K[("2.15", 1, 1)] = own()
for n, old in enumerate("bdacfehg", 1):          # the key's letters, lettered afresh
    K[("3.1", n, 1)] = choose(MEANINGS31, NEW31[old])
for key, a in (((1, 1), "applied for"), ((2, 1), "turned down"), ((3, 1), "were made redundant"),
               ((4, 1), "taking on"), ((5, 1), "handed in his notice"),
               ((6, 1), "has been promoted/has got promoted/'s been promoted/'s got promoted/got promoted/was promoted"),
               ((7, 1), "gain/can gain/will gain"), ((7, 2), "experience"), ((8, 1), "work shifts")):
    K[("3.2",) + key] = Q(a)
for n, (_t, a) in enumerate(WB33, 1):
    K[("3.3", n, 1)] = Q(a)
for n, a in enumerate(["qualifications", "applicants/applications", "employer", "manager", "training",
                       "retirement"], 1):
    K[("3.4", n, 1)] = Q(a)
for n, a in enumerate("badce", 1):
    K[("3.5", n, 1)] = choose(PHRASES35, a)
for n, a in enumerate(["work", "career", "profession", "a job", "job", "work"], 1):
    K[("3.6", n, 1)] = choose(FORMS36[n], a)
for n, a in enumerate(["for", "down", "in", "on", "redundant", "promoted", "experience", "shifts"], 1):
    K[("3.7", n, 1)] = Q(a)
for n, a in enumerate("ABCBA", 1):
    K[("3.8", n, 1)] = choose(["A", "B", "C", "D"], a)
BOX39 = ["salary", "promotion", "colleague", "deadline", "shift", "notice", "candidate", "contract"]
for n, a in enumerate(["colleague", "contract", "deadline", "shift", "promotion", "salary"], 1):
    K[("3.9", n, 1)] = choose(BOX39, a)
for n, a in enumerate(["profession", "gain", "employment", "redundant"], 1):
    K[("3.10", n, 1)] = choose(ODD310[n], a)
for n, a in enumerate(["applied", "offered", "gained", "promoted", "redundant", "notice"], 1):
    K[("3.11", n, 1)] = Q(a)
for n, a in enumerate(["made", "handed", "applied", "took/take", "promoted", "shifts"], 1):
    K[("3.12", n, 1)] = Q(a)
for n, a in enumerate("cabed", 1):
    K[("3.13", n, 1)] = choose(ENDS313, a)
for n, a in enumerate(["gain", "handed", "taking", "made", "profession", "work"], 1):
    K[("3.14", n, 1)] = choose(FORMS314[n], a)
K[("3.15", 1, 1)] = own()
for n in range(1, 5):
    K[("4.2", n, 1)] = own()
K[("5.1", 1, 1)] = own(control="essay")

if __name__ == "__main__":
    data = h.build(K, "Intermediate", 2, "Unit 2.1 — Modern life")
    out = os.path.join(HERE, "i021.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
