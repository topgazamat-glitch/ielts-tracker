"""B02A All about me - Azamat's Beginner booklet (2A), done on a phone.

His design is rendered as it is and this decides every box. The key is his
(B02A All about me - answer key), joined box by box by hand. The Desktop
"new design" copy is used; it splits into its five parts as it should.

As with the other Beginner booklets, every box that explains is told again
in Uzbek, as are the goals and every instruction; the English examples stay
English, as do the reading, the model and the exercises.

Put right here: in 2.1 the key has item 1 (Valencia is big. ... a big city.)
as It isn't; it is It's, and the key's own note that only item 4 is positive
misses it. 1.2 asks whose home is a flat and whose a house - a tap for
each; the table in 2.4 is one line per question; the partner tables (4.7,
5.7, 5.8) are done in class.

    python3 handouts/b02a_digital.py            # writes handouts/b02a.json, lists every box
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

DOCX = "~/Desktop/Handouts/A1 Beginner/B02A All about me/B02A All about me — handout (new design).docx"
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


def rows_as_lines(label, skip_header=True, joiner="  —  "):
    """A table of prompts and boxes as one line per row: each cell kept as it is."""
    a, b = table_after(label)
    rows = [re.findall(r"<td[^>]*>(.*?)</td>", r, re.S) for r in re.findall(r"<tr>(.*?)</tr>", h.html[a:b], re.S)]
    out = ""
    for row in rows[1:] if skip_header else rows:
        cells = [re.sub(r"</?p[^>]*>", "", c).strip() for c in row]
        out += '<p style="margin-bottom:8px">%s</p>' % joiner.join(c for c in cells if c)
    h.html = h.html[:a] + out + h.html[b:]


def people_rows(label, heads, count):
    """A survey table with nothing but boxes: one block per person."""
    a, b = table_after(label)
    tags = [t.group(0) for t in BLANK_TAG.finditer(h.html[a:b])]
    out = ""
    for k in range(count):
        mine = tags[k * len(heads):(k + 1) * len(heads)]
        out += ('<p style="margin-bottom:8px"><span style="font-weight:700">Person %d</span><br>%s</p>'
                % (k + 1, "<br>".join('<span style="color:#6E6E6E">%s</span> %s' % (html.escape(hd), t)
                                      for hd, t in zip(heads, mine))))
    h.html = h.html[:a] + out + h.html[b:]


def pairs_as_lines(label):
    """A four-column table - name, box, name, box - as one name a line."""
    a, b = table_after(label)
    rows = [re.findall(r"<td[^>]*>(.*?)</td>", r, re.S) for r in re.findall(r"<tr>(.*?)</tr>", h.html[a:b], re.S)]
    pairs = [(plain(r[k]), BLANK_TAG.search(r[k + 1])) for r in rows[1:] for k in (0, 2) if len(r) > k + 1]
    h.html = h.html[:a] + "".join('<p style="margin-bottom:8px">%s  %s</p>' % (html.escape(c), t.group(0))
                                  for c, t in sorted(pairs, key=lambda p: int(p[1].group(1)))) + h.html[b:]


# ------------------------------------------------------------ 1 Reading
pairs_as_lines("1.2")

# ------------------------------------------------------------ 2 Grammar
rows_as_lines("2.4")
boxes_for("2.6", range(2, 9))                     # item 1 is the worked example
h.grid_rows("2.8")

# ------------------------------------------------------------ 3 Vocabulary
boxes_for("3.5", range(1, 5), where="leader")

# ------------------------------------------------------------ 4 Listening
h.grid_rows("4.1")
people_rows("4.7", ["Name", "Where from?", "City, town or village?"], 3)

# ------------------------------------------------------------ 5 Grammar and writing
boxes_for("5.3", range(1, 5), where="leader")
boxes_for("5.5", (1, 2, 3), where="leader")
h.leaders("5.6", "CHECK BEFORE", [(20, W, "Write about your home and a friend's home")])
h.html = h.html.replace(TAGS[148], "", 1)         # the word count: the box counts them itself
h.grid_rows("5.7")

# ------------------------------- every instruction, once more, in Uzbek
for label, text in [
        ("1.1", "Soʻzlarga qarang. Qayerda yashaysiz? Tanlang."),
        ("1.2", "Kimning uyi kvartira (*a flat*), kimniki hovli uy (*a house*)? Tanlang."),
        ("1.3", "Toʻgʻri (*T*) mi yoki notoʻgʻri (*F*) mi?"),
        ("1.4", "Shahar (*C*), shaharcha (*T*) yoki qishloq (*V*)?"),
        ("1.5", "Gaplarni matndagi soʻz bilan toʻldiring."),
        ("1.6", "Endi siz. Gaplarni toʻldiring."),
        ("2.1", "*It's* yoki *It isn't* ni tanlang."),
        ("2.2", "*He's*, *she's* yoki *it's* ni tanlang."),
        ("2.3", "Savol tuzing."),
        ("2.4", "Qisqa javoblarni toʻldiring."),
        ("2.5", "Uchta suhbatni toʻldiring."),
        ("2.6", "Xatoni topib, toʻgʻrilang. UCHTA gap toʻgʻri — ular uchun *✓ It is correct* tugmasini bosing."),
        ("2.7", "Tinglang va ayting. Tezmi (*F*) yoki sekinmi (*S*)?"),
        ("2.8", "Har bir joy haqida IKKITA gap yozing — biri *it's* bilan, biri *it isn't* bilan."),
        ("2.9", "Sherigingizdan soʻrang. Qisqa javob bering, keyin yana bitta gap qoʻshing."),
        ("3.1", "Qarama-qarshi maʼnodagi soʻzni yozing."),
        ("3.2", "*big*, *small*, *old* yoki *new* ni tanlang."),
        ("3.3", "*In* mi yoki *near* mi?"),
        ("3.4", "/h/ mi yoki /w/ mi? Tovushni tanlang."),
        ("3.5", "Xatoni topib, toʻgʻri gapni yozing."),
        ("4.1", "Bir marta tinglang. Shahar, shaharcha yoki qishloq?"),
        ("4.2", "Yana tinglang. Toʻgʻri (*T*) mi yoki notoʻgʻri (*F*) mi?"),
        ("4.3", "Yana bir marta tinglang va har bir qatorni toʻldiring."),
        ("4.4", "Tinglang va nima boʻlishiga eʼtibor bering."),
        ("4.5", "Har birini ikki marta ayting — avval sekin, keyin tez."),
        ("4.6", "Buni kim aytadi? *G* (Giovanna), *N* (Nuria) yoki *R* (Robin) ni tanlang."),
        ("4.7", "Endi siz. Uch kishidan soʻrang va javoblarini yozing. Buni sinfda bajarasiz."),
        ("5.1", "Egalik soʻzini yozing."),
        ("5.2", "*my*, *your*, *his*, *her*, *our* yoki *their* ni tanlang."),
        ("5.3", "Xatoni topib, toʻgʻri gapni yozing."),
        ("5.4", "Namunani oʻqing. Keyin javob bering."),
        ("5.5", "Namuna haqidagi savollarga javob bering."),
        ("5.6", "Endi oʻz uyingiz va doʻstingizning uyi haqida yozing (50–60 soʻz)."),
        ("5.7", "Sherigingiz bilan qogʻoz almashing. Uning matnini oʻqib, jadvalni toʻldiring. Buni sinfda "
                "bajarasiz."),
        ("5.8", "Endi sinfga sherigingiz haqida gapirib bering. *his* yoki *her* ni ishlating. Buni sinfda "
                "bajarasiz.")]:
    h.say_also(label, text)

# ------------------------------------------ the explanations, told in Uzbek
h.goals([
    "oʻz shahringiz haqida gapirishni — katta shahar, shaharcha yoki qishloq",
    "joy uchun *it's* va *it isn't*, odam uchun *he's* yoki *she's* ishlatishni",
    "uyni oddiy sifatlar va ularning qarama-qarshisi bilan tasvirlashni",
    "*in* va *near* orasida tanlashni",
    "*my, your, his, her, our, their* ni ishlatishni va uyingiz haqida yozishni",
])
h.retell("KEY WORDS", "KALIT SOʻZLAR", [
    "**a city**  katta shahar — *Tashkent, London*",
    "**a town**  shaharcha — unchalik katta emas",
    "**a village**  qishloq — juda kichik",
    "**a flat**  kvartira — katta binodagi uy",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — IT VA THEY", [
    "1-boʻlimda olti shaxsni oʻrgandingiz: *I · you · we · he · she · they*. Mana yettinchisi — uni ularning "
    "hammasidan koʻproq ishlatasiz.",
    "[[IT]] *IT* = bitta narsa yoki bitta joy. Odam emas. *Valencia? It's a city. · It's a small house. · It isn't "
    "very old.*",
    "[[THEY]] *THEY* = ikkita yoki koʻproq. Narsalar, joylar yoki odamlar. *They're old houses. · They aren't big.*",
    "[[?]] Savollar: *Is it a big city? · Are they new houses?* Feʼl oldinga chiqadi — xuddi 1-boʻlimdagidek.",
    "[[✓ ✗]] Qisqa javoblar: *Yes, it is. / No, it isn't. · Yes, they are. / No, they aren't.*",
    "**Odammi yoki joymi?** Har bir gapda shuni tanlaysiz. *Robin is from Polperro. He's British.* — Robin — odam. "
    "· *Polperro is in the UK. It's a village.* — Polperro — joy.",
])
h.retell("ERROR WARNING", "DIQQAT — KOʻP UCHRAYDIGAN XATOLAR", [
    "1 **IT soʻzini tushirib qoldirmang.** ✗ *Is in Japan?* → ✓ *Is it in Japan?* Hamma bilsa ham, ingliz tilida "
    "nima haqida gapirayotganingiz aytiladi.",
    "2 **Qisqa HA javobi uzun shaklni saqlaydi.** ✗ *Yes, it's.* → ✓ *Yes, it is.* Lekin *No, it isn't* toʻgʻri. "
    "„Ha“ — uzun, „yoʻq“ — qisqa.",
    "3 **IT odamlar uchun emas.** ✗ *My friend Sonia? It's from Plymouth.* → ✓ *She's from Plymouth.* Odamlar "
    "uchun doim *he* va *she* ishlating.",
    "4 **Ikki xil, ikkalasi ham toʻgʻri:** *It isn't old = It's not old. · They aren't big = They're not big.*",
])
h.retell("PRONUNCIATION", "TALAFFUZ — IT'S", [
    "**IT'S — ikki soʻz emas, bitta tovush.** *it is → it's* /ɪts/. Tez ayting. Har safar *it is* ni sekin "
    "aytsangiz, inglizchangiz robotnikidek eshitiladi.",
    "**Lekin HA javobida sekinlashing.** *Yes, it is.* — bu yerda *is* oxirgi va baland soʻz. Shuning uchun *Yes, "
    "it's* notoʻgʻri eshitiladi: gapning oxiri yoʻq.",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — SIFATLAR", [
    "Sifatlar juft-juft boʻladi. Ikkalasini birga oʻrgansangiz, ikki barobar tez oʻrganasiz.",
    "*big — small · old — new · good — bad · easy — difficult · interesting — boring · right — wrong · happy — sad "
    "· beautiful · funny*",
    "**Sifat qayerda turadi.** Otdan oldin: *a big city*. Yoki *is* dan keyin: *the city is big*. Hech qachon "
    "otdan keyin emas: ✗ *a city big*",
    "**Sifatga -s qoʻshilmaydi.** ✓ *two big houses* · ✗ *two bigs houses*. Ingliz tilida sifat hech narsaga "
    "qarab oʻzgarmaydi.",
    "Ikkitasini *AND* bilan qoʻshsangiz ham boʻladi: *It's big and beautiful. · It's old, small and very nice.*",
])
h.retell("IN AND NEAR", "IN VA NEAR", [
    "Ikkita juda kichik soʻz, oʻquvchilar ularni yillar davomida adashtiradi.",
    "**IN** = ichida. *Naples is in Italy. · My flat is in a new part of the city. · I live in Tashkent.*",
    "**NEAR** = yaqinida, lekin ichida emas. *Sagunto is near Valencia. · Sōka is near Tokyo.*",
    "**Tekshiruv:** kattaroq joyning ichidami? Unda *in*. Yonidami? Unda *near*. *Sōka is near Tokyo* — u "
    "Tokioning bir qismi emas.",
])
h.retell("PRONUNCIATION — THE LETTERS H AND W", "TALAFFUZ — H VA W HARFLARI", [
    "Rus va oʻzbek tilida gapiradiganlar almashtirib yuboradigan ikki harf.",
    "**/h/** — faqat havo, ovozsiz: *house · home · happy · her · his*",
    "**/w/** — avval lablaringizni yumaloqlang: *where · what · we · wrong · woman*",
    "**Tuzoq:** *who* *w* bilan yoziladi, lekin /h/ bilan aytiladi — /huː/. *where* va *what* esa /v/ bilan emas, "
    "/w/ bilan aytiladi. Qoʻlingizni ogʻzingiz oldiga tuting: /h/ iliq havo chiqaradi, /w/ chiqarmaydi.",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [
    "Uch kishi bir xil ikkita savolga javob beradi: *where are you from?* va *is it a big city?*",
    "Bu uch kishi — *Giovanna, Nuria* va *Robin*. Ular bilan 1-qismda tanishgansiz.",
])
h.retell("WHY YOU DIDN'T HEAR IT", "NEGA ESHITMADINGIZ?", [
    "**Tez aytilganda IT'S va IT ISN'T deyarli bir xil eshitiladi.** /ɪts/ va /ɪtznt/. Farqi — oʻrtadagi bitta "
    "qoʻshimcha tovush, u esa juda tez oʻtib ketadi.",
    "**Shuning uchun IT dan KEYINGI soʻzga quloq soling.** *It's big. · It isn't big.* Sifat — baland soʻz, u "
    "hech qachon yoʻqolmaydi. Yaqinida *but* ni ham eshitsangiz, gap odatda avval inkor, keyin tasdiq boʻladi.",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — MY, YOUR, HIS, HER", [
    "Narsa kimniki ekanini aytadigan oltita kichik soʻz. Har bir shaxsning bittasi bor va ular hech qachon "
    "oʻzgarmaydi.",
    "*I → my · you → your · he → his · she → her · we → our · they → their*",
    "*My flat is small. · Is this your book? · His home is old and beautiful. · She's here with her friend. · This "
    "is our home in Madrid. · Is that their home?*",
    "**Ular hech qachon -s olmaydi va narsaga qarab oʻzgarmaydi.** *my house* va *my houses* — *my* bir xil. U "
    "egasiga qarab oʻzgaradi, narsaga qarab emas.",
])
h.retell("CHECK BEFORE YOU GIVE IT IN", "TOPSHIRISHDAN OLDIN TEKSHIRING", [
    "{box}  Har bir gapda *is* yoki *isn't* bor.   {box}  Joy uchun *he's* yoki *she's* emas, *it's* ishlatdim.",
    "{box}  Erkak uchun *his*, ayol uchun *her* ishlatdim.   {box}  *your* va *their* da *r* harfi bor.",
    "{box}  Har bir sifat otdan oldin yoki *is* dan keyin turibdi.   {box}  Soʻzlarni sanadim.",
])
h.one_per_line("TOPSHIRISHDAN OLDIN TEKSHIRING", None, at="box")
h.retell("THE WHOLE LESSON IN SIX LINES", "BUTUN DARS OLTI QATORDA", [
    "**Joy — IT.** *Tashkent? It's a city.* Odam — *he* yoki *she*.",
    "**Nima EMASligini ham ayting.** *It's big. It isn't old.* Ikki gap — va istalgan narsani tasvirlab berdingiz.",
    "**Sifat oldinda yoki IS dan keyin turadi.** *a small flat · the flat is small.* Hech qachon otdan keyin emas.",
    "**IN — ichida. NEAR — yonida.** *in Turkey · near Istanbul.*",
    "**Kimniki?** *my · your · his · her · our · their.* Ular hech qachon oʻzgarmaydi.",
    "**Va ehtiyot boʻlish kerak boʻlgani:** *Yes, it is.* — hech qachon *Yes, it's.*",
])
h.retell_cells({"Person": "Shaxs", "Possessive": "Egalik", "Example": "Misol"})
h.retell_cells({"What is written": "Yozilishi", "What you hear": "Eshitilishi", "Why": "Nega",
                "two words, one sound": "ikki soʻz, bitta tovush",
                "one extra sound in the middle": "oʻrtada bitta qoʻshimcha tovush",
                "is it runs together": "<i>is it</i> qoʻshilib ketadi",
                "is is the loud last word": "<i>is</i> — baland oxirgi soʻz"},
               after="4.4  </span>")

# ------------------------------------------------------------------ the key
K = {}
K[("1.1", 1, 1)] = choose(["city", "town", "village"])   # where they live
HOME = ["a flat", "a house"]
for n, a in enumerate(["a flat", "a house", "a flat", "a flat", "a house", "a flat"], 1):
    K[("1.2", n, 1)] = choose(HOME, a)
TF = {"T": "T · true", "F": "F · false"}
for n, a in enumerate("FTFTFT", 1):
    K[("1.3", n, 1)] = choose(["T", "F"], a, labels=TF)
CTV = {"C": "C · city", "T": "T · town", "V": "V · village"}
for n, a in enumerate("CTCVCC", 1):
    K[("1.4", n, 1)] = choose(["C", "T", "V"], a, labels=CTV)
for n, a in enumerate(["small", "old", "old", "new", "isn't"], 1):
    K[("1.5", n, 1)] = Q(a)
for key in ((1, 1), (2, 1), (3, 1), (3, 2), (4, 1)):   # their own home
    K[("1.6",) + key] = own(control=None)
IT = ["It's", "It isn't"]
for n, a in enumerate(["It's", "It isn't", "It isn't", "It's", "It isn't", "It isn't"], 1):
    K[("2.1", n, 1)] = choose(IT, a)
for n, a in enumerate(["It's", "He's", "She's", "It's", "It's", "It's"], 1):
    K[("2.2", n, 1)] = choose(["He's", "She's", "It's"], a)
for n, a in enumerate(["Is it a big city", "Are they new houses", "Is it near Tokyo", "Are they beautiful",
                       "Is it an old village"], 1):
    K[("2.3", n, 1)] = write(a)
for n, a in enumerate(["it isn't/it's not/it is not", "they are", "it is", "they aren't/they're not/they are not"], 1):
    K[("2.4", n, 1)] = Q(a)
for n, a in enumerate(["Is it", "It isn't/It's not/It is not", "It's/It is", "it is", "Is", "isn't/is not"], 1):
    K[("2.5", n, 1)] = Q(a)
TICKED = "✓/correct/tick"
for n, a in zip(range(2, 9), [
        "Yes, it is",
        either("She's from Plymouth", "She is from Plymouth"),
        TICKED, TICKED,
        either("It's a village", "It is a village"),
        either("Are they new houses? Yes, they are", "Yes, they are"),
        TICKED]):
    K[("2.6", n, 1)] = fix(a)
FS = {"F": "F · fast", "S": "S · slow"}
for n, a in enumerate("FSFS", 1):
    K[("2.7", n, 1)] = choose(["F", "S"], a, labels=FS)
for n in range(1, 9):                             # their own places
    K[("2.8", n, 1)] = own(control=None)
for n, a in enumerate(["small", "new/young", "bad", "difficult/hard", "boring", "wrong", "sad/unhappy", "old"], 1):
    K[("3.1", n, 1)] = Q(a)
for n, a in enumerate(["big", "small", "old", "new", "small", "old"], 1):
    K[("3.2", n, 1)] = choose(["big", "small", "old", "new"], a)
for n, a in enumerate(["in", "near", "in", "near", "in", "near"], 1):
    K[("3.3", n, 1)] = choose(["in", "near"], a)
for n, a in enumerate(["/h/", "/w/", "/h/", "/w/", "/h/", "/w/"], 1):
    K[("3.4", n, 1)] = choose(["/h/", "/w/"], a)
for n, a in enumerate([either("It's a big city", "It is a big city", "a big city"),
                       either("They're two small houses", "They are two small houses", "small"),
                       either("Sōka is near Tokyo", "Soka is near Tokyo", "near"),
                       either("My flat is in a new part of the city", "in")], 1):
    K[("3.5", n, 1)] = write(a)
for n, a in enumerate(["Ravello", "town/a town", "Valencia", "city/a city", "Polperro", "village/a village"], 1):
    K[("4.1", n, 1)] = Q(a)
for n, a in enumerate("TFTFTF", 1):
    K[("4.2", n, 1)] = choose(["T", "F"], a, labels=TF)
for key, a in (((1, 1), "It's/It is"), ((2, 1), "It isn't/It's not/It is not"), ((2, 2), "it's/it is"),
               ((3, 1), "It's/It is"), ((4, 1), "isn't/is not"), ((4, 2), "It's/It is"), ((5, 1), "isn't/is not"),
               ((5, 2), "It's/It is")):
    K[("4.3",) + key] = Q(a)
GNR = {"G": "G · Giovanna", "N": "N · Nuria", "R": "R · Robin"}
for n, a in enumerate("GNRNRN", 1):
    K[("4.6", n, 1)] = choose(["G", "N", "R"], a, labels=GNR)
for n in range(1, 11):                            # three people, in class
    K[("4.7", n, 1)] = pair()
for n, a in enumerate(["my", "his", "her", "our", "your", "their"], 1):
    K[("5.1", n, 1)] = Q(a)
POSS = ["my", "your", "his", "her", "our", "their"]
for n, a in enumerate(["my", "his", "her", "their", "our", "your"], 1):
    K[("5.2", n, 1)] = choose(POSS, a)
for n, a in enumerate([either("Is this your flat", "your"), either("Their house is in Naples", "Their"),
                       either("Sonia and her friend are from Plymouth", "her"), either("This is our home", "our")], 1):
    K[("5.3", n, 1)] = write(a)
for n in (1, 2, 3):
    K[("5.5", n, 1)] = own()
K[("5.6", 20, 1)] = own(control="essay")
for n in range(1, 7):                             # the checklist
    K[("5.6", n, 1)] = tick()
for n in range(1, 9):                             # a partner's text, in class
    K[("5.7", n, 1)] = pair()
for n in range(1, 6):
    K[("5.8", n, 1)] = pair()

if __name__ == "__main__":
    data = h.build(K, "Beginner", 2, "Unit 2A — All about me")
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "b02a.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
