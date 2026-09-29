"""I09BD Entertainment - Azamat's Intermediate booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(I09BD Entertainment - ANSWER KEY), joined box by box by hand. At this level
the explanations stay English. Built from the Material Bank copy: his
Desktop redesign has the same exercises but would not split into parts.

The marking forgives commas - a phone keyboard makes them easy to drop, and
elsewhere they are not the point. Here they sometimes are: 2.5's Palace
Hotel is wrong only for its missing comma, so that box is his to read
rather than marked right for the sentence copied out unchanged. Where a
comma sits beside a word that is marked (2.3, 2.7), the word is marked.

What a phone gets that paper does not:
  - taps for every choice: B/S/F, A/B/C, D or ND, whether the pronoun can
    go, the stressed syllable, which music, the contrast words;
  - boxes where paper has none: 2.4, 2.5, 3.4, 4.1, 5.3.

    python3 handouts/i09bd_digital.py            # writes handouts/i09bd.json, lists every box
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import (Handout, Q, choose, tick, own, write, fix, report,   # noqa: E402
                     BLANK_TAG, LEADER_P, plain, ITEM_STYLE, NUM_SPAN, TEXT_SPAN)

DOCX = ("~/Documents/Claude/Material Bank/General English/B1 Intermediate/_NEW BOOKLET STYLE/"
        "I09BD Entertainment — BOOKLET.docx")
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


def reword(label, old, new):
    """The instruction after an exercise's number, said differently. Word
    splits a line across pieces of formatting, so the whole line is
    replaced, in the style of its first piece."""
    at = section(label) + len("%s  </span>" % label)
    end = h.html.index("</p>", at)
    if plain(h.html[at:end]) != old:
        raise SystemExit("%s says %r" % (label, plain(h.html[at:end])))
    style = re.match(r'<span( style="[^"]*")?>', h.html[at:end])
    h.html = h.html[:at] + "<span%s>%s</span>" % (style.group(1) or "", html.escape(new)) + h.html[end:]


# ------------------------------------------------------------ 1 Reading
for n in range(1, 5):
    h.item_box("1.3", n)
h.options_on_lines("1.3")
for n in range(1, 4):
    h.item_box("1.4", n, width="190px", where="leader")
h.leaders("1.5", "1.6  </span>", [(1, W, "Six relative clauses from the text"),
                                  (2, W, "Which ones have a comma in front?")])
for n in range(1, 4):
    h.item_box("1.6", n, where="leader")

# ------------------------------------------------------------ 2 Grammar
reword("2.4", "Cross out the pronoun where it can be left out. Two cannot be.",
       "Can the pronoun be left out? Two cannot be.")
for n in range(1, 5):
    h.item_box("2.4", n)
for n in range(2, 7):                             # item 1 is the worked example
    h.item_box("2.5", n)

# ------------------------------------------------------------ 3 Vocabulary
reword("3.4", "Mark the stress, then say the pair out loud.",
       "Tap the stressed syllable of the second word, then say the pair out loud.")
SYLL34 = {1: ["mu", "si", "cian"], 2: ["ce", "le", "bra", "tion"], 3: ["cre", "a", "tiv", "i", "ty"],
          4: ["re", "lax", "a", "tion"], 5: ["hap", "pi", "ness"], 6: ["de", "vel", "op", "ment"]}
for n in SYLL34:
    h.item_box("3.4", n)
a = section("3.6")
b = h.html.index("4  </span>", a)
h.html = h.html[:a] + LEADER_P.sub("", h.html[a:b]) + h.html[b:]      # talk, not write

# ------------------------------------------------------------ 4 Listening
a = h.html.index('<table class="bk">', section("4.1"))
b = h.html.index("</table>", a) + len("</table>")
cells = [plain(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", h.html[a:b], re.S)]
speakers = [re.match(r"(\d+)\s+(.*)", c).groups() for c in cells if re.match(r"\d+\s", c)]
MUSIC = sorted(re.match(r"([a-c])\s+(.*)", c).groups() for c in cells if re.match(r"[a-c]\s", c))
h.html = h.html[:a] + key_list(MUSIC) + "".join(
    item_p("4.1", int(n), html.escape(s, quote=False), "{{box:4.1:%s:60px:}}" % n) for n, s in speakers) + h.html[b:]
for n in range(1, 5):
    h.item_box("4.2", n, where="leader")
for n in range(1, 4):
    h.item_box("4.6", n)
h.options_on_lines("4.6")

# ------------------------------------------------------------ 5 Writing
for n in range(1, 4):
    h.item_box("5.1", n, where="leader")
for n in range(1, 5):
    h.item_box("5.3", n, where="leader")
for n in range(1, 5):
    h.item_box("5.5", n, where="leader")
h.leaders("5.7", "CHECK BEFORE", [(20, W, "Write your article here")])
h.html = h.html.replace(TAGS[84], "", 1)          # the word count: the box counts them itself

# ------------------------------------------------------------------ the key
K = {}
BSF = {"B": "B · the big one", "S": "S · the small one", "F": "F · the free one"}
for n, a in enumerate("BSSFBF", 1):
    K[("1.2", n, 1)] = choose(["B", "S", "F"], a, labels=BSF)
for n in range(1, 5):
    K[("1.3", n, 1)] = choose(["A", "B", "C"], "B")
for n, a in enumerate(["a line-up/line-up/the line-up/a lineup/lineup", "faultless",
                       "an achievement/achievement"], 1):
    K[("1.4", n, 1)] = Q(a)
K[("1.5", 1, 1)] = own()
K[("1.5", 2, 1)] = own()
for n in range(1, 4):
    K[("1.6", n, 1)] = own()
DND = {"D": "D · defining", "ND": "ND · non-defining"}
for n, a in enumerate(["D", "ND", "D", "ND"], 1):
    K[("2.1", n, 1)] = choose(["D", "ND"], a, labels=DND)
for n, a in enumerate(["whose", "where", "when", "which/that", "whose", "who/that"], 1):
    K[("2.2", n, 1)] = Q(a)
K[("2.3", 1, 1)] = write(either(*[s + r for s in ("That's the stage ", "That is the stage ")
                                  for r in ("where we're going to perform", "where we are going to perform",
                                            "we're going to perform on", "that we're going to perform on",
                                            "which we're going to perform on", "on which we're going to perform",
                                            "we are going to perform on", "that we are going to perform on",
                                            "which we are going to perform on")]))
K[("2.3", 2, 1)] = write("Glastonbury, which is most famous as a music festival, also has comedy")
K[("2.3", 3, 1)] = write(either("We need music that makes you want to dance",
                                "We need music which makes you want to dance"))
K[("2.3", 4, 1)] = write(either("I went back to Verona, where I had first heard opera",
                                "I went back to Verona, where I first heard opera"))
GO = ["can be left out", "must stay"]
for n, a in enumerate(["must stay", "can be left out", "can be left out", "must stay"], 1):
    K[("2.4", n, 1)] = choose(GO, a)
TICKED = "✓/correct/tick"
K[("2.5", 2, 1)] = own(control="tickfill")        # wrong only for its comma: his to read
K[("2.5", 3, 1)] = fix(either("I finally went to the USA, which I had always dreamed of visiting",
                              "the USA, which I had always dreamed of visiting"))
K[("2.5", 4, 1)] = fix(TICKED)
K[("2.5", 5, 1)] = fix(either("The album, which came out last year, is her best",
                              "The album that came out last year is her best",
                              "The album, which came out last year"))
K[("2.5", 6, 1)] = fix(TICKED)
for n, a in enumerate(["who", "that/which", "that/which", "that/which", "which/, which", "when/, when"], 1):
    K[("2.7", n, 1)] = Q(a)
for n in range(1, 5):
    K[("2.8", n, 1)] = own()
for key, a in (((1, 1), "audience"), ((2, 1), "instruments"), ((3, 1), "track"), ((3, 2), "album"),
               ((4, 1), "choir"), ((5, 1), "performed/played"), ((6, 1), "orchestra")):
    K[("3.1",) + key] = Q(a)
for n, a in enumerate(["beauty", "celebration", "creativity", "development", "happiness", "musician",
                       "organiser/organizer/organisation/organization", "performer", "performance",
                       "guitarist", "honesty", "culture"], 1):
    K[("3.2", n, 1)] = Q(a)
for key, a in (((1, 1), "performer"), ((1, 2), "performance"), ((2, 1), "creativity"), ((2, 2), "create"),
               ((3, 1), "organiser/organizer"), ((3, 2), "organise/organize")):
    K[("3.3",) + key] = Q(a)
for n, a in enumerate(["si", "bra", "tiv", "a", "hap", "vel"], 1):
    K[("3.4", n, 1)] = choose(SYLL34[n], a)
for n, a in enumerate(["organiser/organizer", "performers", "celebration", "relaxation", "beauty",
                       "ability"], 1):
    K[("3.5", n, 1)] = Q(a)
for n, a in enumerate("cab", 1):                  # Annie, Jeff, Erica
    K[("4.1", n, 1)] = choose([l for l, _m in MUSIC], a)
for n in range(1, 5):
    K[("4.2", n, 1)] = own()
for n, a in enumerate(["which/that", "who/that", "that/which", "who/that", "who", "which"], 1):
    K[("4.3", n, 1)] = Q(a)
for n in range(1, 4):
    K[("4.6", n, 1)] = choose(["A", "B"], "B")
for n in range(1, 4):
    K[("5.1", n, 1)] = own()
BUT = ["however", "although", "while", "despite", "in spite of"]
for n, a in enumerate(["however", "although/while", "although/while", "despite/in spite of",
                       "despite/in spite of", "however"], 1):
    K[("5.2", n, 1)] = choose(BUT, a)
for n, a in enumerate([
        either("Although it was expensive, we went", "Despite the cost, we went", "Despite the price, we went",
               "Despite it being expensive, we went", "In spite of the cost, we went",
               "Even though it was expensive, we went"),
        either("In spite of the noise, I enjoyed it", "Despite the noise, I enjoyed it",
               "Although it was noisy, I enjoyed it"),
        either("I like live music; however, I hate crowds", "I like live music. However, I hate crowds",
               "I like live music, but I hate crowds", "Although I like live music, I hate crowds",
               "I like live music; however I hate crowds"),
        either("Although I booked early, the seats were terrible",
               "Even though I booked early, the seats were terrible",
               "Despite booking early, the seats were terrible",
               "In spite of booking early, the seats were terrible")], 1):
    K[("5.3", n, 1)] = write(a)
for n in range(1, 5):
    K[("5.5", n, 1)] = own()
for n in range(1, 5):                             # the plan: notes
    K[("5.6", n, 1)] = own(control=None)
K[("5.7", 20, 1)] = own(control="essay")
for n in range(1, 8):                             # the checklist
    K[("5.7", n, 1)] = tick()

if __name__ == "__main__":
    data = h.build(K, "Intermediate", 9, "Unit 9B & 9D — Entertainment")
    out = os.path.join(HERE, "i09bd.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
