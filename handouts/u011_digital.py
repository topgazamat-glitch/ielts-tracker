"""U01.1 People - Azamat's Elementary booklet (unit 1), done on a phone.

His design is rendered as it is and this decides every box. The key is his
(U01.1 People - answer key), joined box by box by hand. The Desktop "new
design" copy is used; it splits into its six parts as it should. This is
the older, shorter design: its explanation boxes are one cell with a title
bar, so they are told again in Uzbek here by `retell_box`.

Put right here: the vocabulary note gave "Uzbeki" as an -i nationality; the
word is Uzbek, so the example is Iraqi, and the Uzbek note says so. In 1.2
item 6 the key has true, but Marta and Paulo are both from Brazil (the text
itself says all four friends are from different countries): both answers
count, and he may want to change the sentence. The table in 3.1 is one line
per country. 5.1 is a role-play in class.

    python3 handouts/u011_digital.py            # writes handouts/u011.json, lists every box
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import (Handout, Q, choose, tick, own, write, fix, note, pair, report,   # noqa: E402
                     BLANK_TAG, LEADER_P, plain, told, ITEM_STYLE, NUM_SPAN, TEXT_SPAN)

DOCX = "~/Desktop/Handouts/A2 Elementary/U01.1 People/U01.1 People — handout (new design).docx"
W = "95%"

h = Handout(DOCX)
TAGS = {int(m.group(1)): m.group(0) for m in BLANK_TAG.finditer(h.html)}


def section(label):
    return h.html.index("%s  </span>" % label)


def either(*forms):
    return "/".join(forms)


def item_p(label, n, text_html, token, number=True):
    h.texts[(label, n)] = plain(text_html)
    return ('<p data-item="%s:%d" %s>%s%s</p>'
            % (label, n, ITEM_STYLE, NUM_SPAN % n if number else "",
               TEXT_SPAN % ("%s  %s" % (text_html, token))))


def key_list(pairs):
    return ('<table class="bk"><tr><td style="vertical-align:top;background:#F2F8F8;'
            'border-left:3px solid #127D80">'
            + "".join('<p style="margin:0"><span style="font-weight:700;color:#127D80">%s</span>  %s</p>'
                      % (l, html.escape(t, quote=False)) for l, t in pairs)
            + "</td></tr></table>")


def table_after(label):
    a = h.html.index('<table class="bk">', section(label))
    return a, h.html.index("</table>", a) + len("</table>")


def halves(label, letters, token="{{box:%s:%s:60px:}}"):
    a, b = table_after(label)
    cells = [plain(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", h.html[a:b], re.S)]
    begins = [re.match(r"(\d+)\s+(.*)", c).groups() for c in cells if re.match(r"\d+\s", c)]
    ends = sorted(re.match(r"([%s])\s+(.*)" % letters, c).groups() for c in cells
                  if re.match(r"[%s]\s" % letters, c))
    h.html = h.html[:a] + key_list(ends) + "".join(
        item_p(label, int(n), html.escape(t, quote=False), token % (label, n)) for n, t in begins) + h.html[b:]
    return [l for l, _t in ends]


def in_order(label, lines):
    """"Number them 1-5": the paper's own numbers go, so the only numbers
    are the ones tapped."""
    a, b = table_after(label)
    h.html = h.html[:a] + "".join(
        item_p(label, n, "·  " + html.escape(t, quote=False), "{{box:%s:%d:60px:}}" % (label, n), number=False)
        for n, t in sorted(lines.items())) + h.html[b:]


def reword(label, old, new):
    at = section(label) + len("%s  </span>" % label)
    end = h.html.index("</p>", at)
    if plain(h.html[at:end]) != old:
        raise SystemExit("%s says %r" % (label, plain(h.html[at:end])))
    style = re.match(r'<span( style="[^"]*")?>', h.html[at:end])
    h.html = h.html[:at] + "<span%s>%s</span>" % (style.group(1) or "", html.escape(new)) + h.html[end:]


def words_between(label, n):
    """An item's choices, from "(a / b)" or "a / b" in its text."""
    m = next(m for m in h._items(label) if int(m.group(3)) == n)
    return plain(m.group(4))


def boxes_for(label, groups, where="first"):
    for n in groups:
        h.item_box(label, n, where=where)


def retell_box(title, new_title, paragraphs):
    """The older design's explanation box - a cell whose first line is the
    title bar - told again: the new title in the bar, the new lines below it."""
    m = re.search(r'(<p[^>]*><span[^>]*>)\s*%s\s*(</span></p>)(.*?)(</td>)' % re.escape(title), h.html, re.S)
    if not m:
        raise SystemExit("no box called %r" % title)
    bar = re.sub(r"\sdata-item=\"[^\"]*\"", "", m.group(1))
    h.html = (h.html[:m.start()] + bar + "  %s  " % html.escape(new_title) + m.group(2)
              + "".join(told(p) for p in paragraphs) + m.group(4) + h.html[m.end():])


# ------------------------------------------------------------ 1 Reading
for n in range(1, 7):
    h.item_box("1.2", n)
    h.item_box("1.2", n, placeholder="If it is false, correct it")
a, b = section("1.2"), section("1.3")             # the ruled lines the boxes replace
h.html = h.html[:a] + LEADER_P.sub("", h.html[a:b]) + h.html[b:]
boxes_for("1.3", range(1, 6), where="leader")

# ------------------------------------------------------------ 2 Grammar
FORMS21 = ["am", "is", "are"]
boxes_for("2.1", range(1, 7))
boxes_for("2.2", range(1, 6), where="leader")

# ------------------------------------------------------------ 3 Vocabulary
a, b = table_after("3.1")                         # one country a line
rows = [re.findall(r"<td[^>]*>(.*?)</td>", r, re.S) for r in re.findall(r"<tr>(.*?)</tr>", h.html[a:b], re.S)]
pairs = [(r[0], r[1]) for r in rows[1:]] + [(r[2], r[3]) for r in rows[1:]]
order = {int(t.group(1)): k for k, (c, n) in enumerate(pairs) for t in BLANK_TAG.finditer(c + n)}


def shown(cell):
    tag = BLANK_TAG.search(cell)
    return tag.group(0) if tag else html.escape(plain(cell))


lines31 = "".join('<p style="margin-bottom:8px"><span style="color:#6E6E6E">Country</span> %s  '
                  '<span style="color:#6E6E6E">· Nationality</span> %s</p>' % (shown(c), shown(n))
                  for c, n in sorted(pairs, key=lambda p: min([int(t.group(1)) for t in BLANK_TAG.finditer(p[0] + p[1])]
                                                              or [0])))
h.html = h.html[:a] + lines31 + h.html[b:]
if h.html.count("Pakistani, Uzbeki") != 1:
    raise SystemExit("the -i example has moved")
h.html = h.html.replace("Pakistani, Uzbeki", "Pakistani, Iraqi")
ODD32 = h.odd_one_out("3.2", why="Why is it different?")

# ------------------------------------------------------ 4 Everyday English
boxes_for("4.2", (1, 2, 3), where="leader")

# ------------------------------------------------------------ 6 Writing
h.leaders("6.1", "Check your work", [(1, W, "Write your 6–8 sentences here")])

# ------------------------------- every instruction, once more, in Uzbek
for label, text in [
        ("1.1", "Sherigingiz bilan gaplashing. Boshqa mamlakatlardan doʻstlaringiz bormi? Ular qayerdan?"),
        ("1.2", "Gaplar toʻgʻrimi (*T*) yoki notoʻgʻrimi (*F*)? Notoʻgʻrilarini toʻgʻrilab yozing."),
        ("1.3", "Savollarga toʻliq gap bilan javob bering."),
        ("1.4", "Matndan toʻrtta kasbni toping."),
        ("2.1", "Toʻgʻri shaklni tanlang."),
        ("2.2", "Gaplarni inkor shaklda yozing. Qisqartmalardan foydalaning."),
        ("2.3", "Xabarni *am, is, are, isn't* yoki *aren't* bilan toʻldiring."),
        ("3.1", "Jadvalni toʻldiring."),
        ("3.2", "Har bir guruhdagi boshqacha soʻzni tanlang va nega ekanini yozing."),
        ("3.3", "Gaplarni qutidagi soʻz bilan toʻldiring."),
        ("4.1", "Suhbatni oʻqing. Rustam til maktabining qabulxonasida."),
        ("4.2", "Suhbatdan toping…"),
        ("5.1", "Rolli oʻyin. A oʻquvchi sport zalida, maktabda yoki mehmonxonada ishlaydi. B oʻquvchi — yangi mijoz. "
                "Buni sinfda bajarasiz."),
        ("6.1", "Oʻzingiz va hayotingizdagi ikki kishi haqida 6–8 ta gap yozing.")]:
    h.say_also(label, text)

# ------------------------------------------ the explanations, told in Uzbek
retell_box("Key words", "Kalit soʻzlar", [
    "**a language exchange**  til almashish ilovasi — odamlar oʻz tilini oʻrgatib, sizning tilingizni "
    "oʻrganadigan ilova",
    "**abroad**  chet elda, boshqa mamlakatda",
    "**shy**  uyatchan — yangi odamlar bilan jim",
    "**a neighbour**  qoʻshni — yoningizda yashaydigan odam",
])
retell_box("Error warning", "Diqqat", [
    "**Yosh haqida gapirganda have emas, be ishlatiladi:**",
    "✓ *I am 26 years old.* · ✗ *I have 26 years*",
    "**Ikkala inkor shakli ham toʻgʻri:** *she isn't* = *she's not*",
])
retell_box("Vocabulary note", "Lugʻat izohi", [
    "Millatni bildiruvchi soʻzlar doim bosh harf bilan boshlanadi: *Japanese*, *japanese* emas.",
    "Koʻp uchraydigan qoʻshimchalar: *-an* — *Colombian, Russian* · *-ese* — *Japanese, Chinese* · *-ish* — "
    "*British, Turkish* · *-i* — *Pakistani, Iraqi*",
    "*Uzbek* ning oxirida hech narsa yoʻq: *He is Uzbek.* *Uzbeki* emas.",
])
retell_box("Useful phrases", "Foydali iboralar", [
    "**Soʻrash:** *What's your name / surname? · How do you spell that? · Where are you from?*",
    "**Tekshirish:** *Sorry, can you repeat that? · Sorry, is that 22 or 32? · So that's K-A-R-I-M-O-V, right?*",
])
retell_box("Remember", "Esda tuting", [
    "Qabul xodimi ikkita javobni tekshirishi (*Sorry, is that…?*) va doʻstona gap bilan tugatishi kerak.",
])
retell_box("Check your work", "Ishingizni tekshiring", [
    "☐ har bir gapda *am / is / are* bor   ☐ ismlar va millatlar bosh harf bilan   ☐ har bir gap oxirida nuqta",
])
h.retell_cells({"Positive": "Tasdiq", "Negative": "Inkor"})

# ------------------------------------------------------------------ the key
K = {}
TF = {"T": "T · true", "F": "F · false"}
for n, a in enumerate(["T", "F", "T", "F", "F", "T/F"], 1):
    K[("1.2", n, 1)] = choose(["T", "F"], a, labels=TF)
    K[("1.2", n, 2)] = note()
K[("1.3", 1, 1)] = write("She is 26/She is 26 years old/She's 26/She's 26 years old/Diana is 26/Diana is 26 years old")
K[("1.3", 2, 1)] = write("Her dream is to work abroad/Her dream is to work in another country/She wants to work abroad/"
                         "Diana's dream is to work abroad")
K[("1.3", 3, 1)] = write("He is a taxi driver/He's a taxi driver/Tomo is a taxi driver/He is a taxi driver in Osaka/"
                         "He's a taxi driver in Osaka")
K[("1.3", 4, 1)] = write("Their students are children/They are children/Their students are children")
K[("1.3", 5, 1)] = own()
JOBS = "nurse/taxi driver/teacher/student/a nurse/a taxi driver/a teacher/a student/teachers/students"
for n in range(1, 5):                             # the four jobs, in any order
    K[("1.4", n, 1)] = Q(JOBS)
for n, a in enumerate(["is", "am", "are", "is", "are", "is"], 1):
    K[("2.1", n, 1)] = choose(FORMS21, a)
for n, a in enumerate(["Amira isn't in Egypt now/Amira's not in Egypt now", "I'm not shy",
                       "We aren't strangers/We're not strangers", "My questions aren't difficult",
                       "Tomo isn't a nurse/Tomo's not a nurse"], 1):
    K[("2.2", n, 1)] = write(a)
BE = ["am", "is", "are", "isn't", "aren't"]
for n, a in enumerate(["am", "is", "aren't", "are", "is", "are", "is", "am", "is"], 1):
    K[("2.3", n, 1)] = choose(BE, a)
for n, a in enumerate(["Japanese", "Brazilian", "German", "Egyptian",
                       "the UK/UK/Britain/Great Britain/the United Kingdom/England", "Turkey", "Chinese", "Uzbek",
                       "Italy", "Russian", "American"], 1):
    K[("3.1", n, 1)] = Q(a)
for n, a in {1: "Brazil", 2: "Italian", 3: "Japan"}.items():
    K[("3.2", n, 1)] = choose(ODD32[n], a)
    K[("3.2", n, 2)] = own()
BOX33 = ["Colombian", "Egyptian", "Japanese", "Uzbek", "Brazil", "Germany", "Japan", "Colombia"]
for key, a in (((1, 1), "Colombia"), ((1, 2), "Colombian"), ((2, 1), "Japan"), ((3, 1), "Egyptian"),
               ((3, 2), "Germany"), ((4, 1), "Uzbek")):
    K[("3.3",) + key] = choose(BOX33, a)
K[("4.2", 1, 1)] = own()
K[("4.2", 2, 1)] = write("Where are you from/And where are you from, Rustam/Where are you from, Rustam/"
                         "And where are you from")
K[("4.2", 3, 1)] = own()
K[("6.1", 1, 1)] = own(control="essay")

if __name__ == "__main__":
    data = h.build(K, "Elementary", 1, "Unit 1.1 — People")
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "u011.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
