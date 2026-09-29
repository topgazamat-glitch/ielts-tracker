"""E10BD Communication - Azamat's Elementary booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(E10BD Communication - answer key), joined box by box by hand. The Desktop
"new design" copy is used; it splits into its five parts as it should.

As with the other Elementary booklets, it speaks Uzbek wherever it
explains: every explanation box, the goals, the headings of the grammar and
number tables, the "Why" column of the listening table, and a line under
every instruction. The English examples stay English, as do the reading
text, the posts, the model and the exercises.

5.5 (mark where the word goes) asks for the sentence with the word in its
place. 4.1 is a guess, so its ticks are not marked; 3.5 is a partner's
numbers and 5.9's reply is written in class. Numbers in figures are right
with or without their commas; words with or without their hyphens.

    python3 handouts/e10bd_digital.py            # writes handouts/e10bd.json, lists every box
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import (Handout, Q, choose, tick, own, write, fix, note, pair, report,   # noqa: E402
                     BLANK_TAG, LEADER_P, plain, ITEM_STYLE, NUM_SPAN, TEXT_SPAN)

DOCX = "~/Desktop/Handouts/A2 Elementary/E10BD Communication/E10BD Communication — handout (new design).docx"
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


def spoken(*forms):
    """Numbers in words, with and without their hyphens: forty-five, forty five."""
    out = []
    for f in forms:
        out += [f] + ([f.replace("-", " ")] if "-" in f else [])
    return "/".join(out)


def figures(n):
    return "%s/%s" % ("{:,}".format(n), n) if n >= 1000 else str(n)


def with_the(*forms):
    """A superlative, with its the and - more leniently - without."""
    out = []
    for f in forms:
        out += [f, f[4:]] if f.startswith("the ") else [f]
    return "/".join(out)


def lines_instead_of_table(label, lines, width="60px", number=True):
    a, b = table_after(label)
    h.html = h.html[:a] + "".join(item_p(label, n, html.escape(t), "{{box:%s:%d:%s:}}" % (label, n, width),
                                         number=number)
                                  for n, t in lines) + h.html[b:]


# ------------------------------------------------------------ 1 Reading
FACTS12 = h.key_first("1.2")
boxes_for("1.3", range(1, 5), where="options")
h.options_on_lines("1.3")
boxes_for("1.4", range(1, 5), where="leader")
boxes_for("1.5", range(1, 5), where="leader")
h.leaders("1.6", "2.1  </span>", [(1, W, "Five superlative adjectives")])

# ------------------------------------------------------------ 2 Grammar
boxes_for("2.3", range(2, 9))                     # item 1 is the worked example
STRESS25 = {1: "the biggest", 2: "the easiest", 3: "the hardest", 4: "the most beautiful", 5: "the most useful",
            6: "the most difficult"}
boxes_for("2.5", STRESS25)

# ------------------------------------------------------------ 3 Vocabulary
a, b = section("3.4"), section("3.5")             # 3.4 has its boxes: no lines needed
h.html = h.html[:a] + LEADER_P.sub("", h.html[a:b]) + h.html[b:]

# ------------------------------------------------------------ 4 Listening
SAID42 = [(1, "He thinks it is a very beautiful language."),
          (2, "It is difficult for English speakers, but not for Mandarin speakers."),
          (3, "Many people think it is very easy."), (4, "More than 900 million people speak it.")]
lines_instead_of_table("4.2", SAID42)
boxes_for("4.3", range(1, 5), where="leader")
boxes_for("4.8", (1, 2, 3))
h.options_on_lines("4.8")

# ------------------------------------------------------------ 5 Writing
h.grid_rows("5.1")
h.html, speakers = re.subn(r'(<p data-item="5\.1:\d+"[^>]*><span style="font-weight:700">)(\d)</span>',
                           r"\1Speaker \2</span>", h.html)
if speakers != 3:
    raise SystemExit("5.1 has %d speakers" % speakers)
h.leaders("5.2", "SIX PEOPLE", [(1, W, "Whose opinion is closest to yours, and why?")])
ALSO55 = [(1, "I've got a new PC and I have a new laptop. (also)"),
          (2, "We had satnav and we took a street map. (too)"),
          (3, "She works for a phone company and she knows about computers. (also)"),
          (4, "Tablets are light. They have a large screen. (as well)")]
lines_instead_of_table("5.5", ALSO55, width=W)
boxes_for("5.6", range(1, 5), where="leader")
boxes_for("5.8", range(1, 5), where="leader")
h.leaders("5.9", "CHECK BEFORE", [(20, W, "Your post"), (21, W, "Your reply to a classmate's post, in class")])
h.html = h.html.replace(TAGS[112], "", 1)         # the word count: the box counts them itself

# ------------------------------- every instruction, once more, in Uzbek
for label, text in [
        ("1.1", "Muhokama qiling. Nechta tilda gapira olasiz? Sizningcha, dunyoda nechta til bor?"),
        ("1.2", "Sonni fakt bilan moslang: harfni tanlang."),
        ("1.3", "Eng toʻgʻri javobni tanlang: *A*, *B* yoki *C*."),
        ("1.4", "Matndan shu maʼnodagi soʻzni toping."),
        ("1.5", "Savollarga javob bering."),
        ("1.6", "Matndan beshta orttirma daraja sifatini topib, yozing."),
        ("2.1", "Orttirma daraja shaklini yozing."),
        ("2.2", "Orttirma daraja bilan toʻldiring."),
        ("2.3", "Xatoni topib, toʻgʻrilang. IKKITA gap toʻgʻri — ular uchun *✓ It is correct* tugmasini bosing."),
        ("2.4", "Matnni orttirma daraja shakli bilan toʻldiring."),
        ("2.5", "Urgʻuli qismni tanlang, keyin har birini ovoz chiqarib ayting."),
        ("2.6", "Savollarni orttirma daraja bilan toʻldiring. Keyin sherigingizdan soʻrang."),
        ("3.1", "Sonni raqam bilan yozing."),
        ("3.2", "Sonni soʻz bilan yozing."),
        ("3.3", "Toʻgʻri (*✓*) mi yoki notoʻgʻri (*✗*) mi? Notoʻgʻrilarini toʻgʻrilang."),
        ("3.4", "*and* qayerga qoʻyiladi? Sonni soʻz bilan yozing."),
        ("3.5", "Qaysi birini eshityapsiz? Belgilang. Keyin ularni sherigingizga oʻqib bering. Buni sinfda "
                "bajarasiz."),
        ("3.6", "Bu yillarni ayting va soʻz bilan yozing."),
        ("4.1", "Tinglashdan oldin. Sizningcha, u qaysi tillar haqida gapiradi? Belgilang."),
        ("4.2", "Bir marta tinglang. Gapni til bilan moslang."),
        ("4.3", "Yana tinglang va javob bering."),
        ("4.4", "Yana bir marta tinglang va har bir qatorni toʻldiring."),
        ("4.5", "Tinglang va nima boʻlishiga eʼtibor bering."),
        ("4.6", "Har bir iborani ikki marta ayting — avval sekin, keyin tez."),
        ("4.7", "Buni kim aytadi — boshlovchi (*H*) mi yoki professor (*P*) mi?"),
        ("4.8", "Gapiruvchi nima demoqchi? *A* yoki *B* ni tanlang."),
        ("5.1", "Tinglang va jadvalni toʻldiring."),
        ("5.2", "Qaysi gapiruvchining fikri sizniki bilan eng yaqin? Sherigingizga nega ekanini ayting."),
        ("5.3", "Bu fikrlar kimniki? Ismni tanlang."),
        ("5.4", "Postlardan toping…"),
        ("5.5", "Soʻz qayerga qoʻyiladi? Gapni soʻz bilan birga toʻliq yozing."),
        ("5.6", "Toʻgʻri (*✓*) mi yoki notoʻgʻri (*✗*) mi? Notoʻgʻrilarini toʻgʻrilang."),
        ("5.7", "Namunaviy post va javobni oʻqing. Keyin savollarga javob bering."),
        ("5.8", "Namuna haqidagi savollarga javob bering."),
        ("5.9", "Sizni jahlingizni chiqaradigan narsa haqida oʻz postingizni yozing (70–90 soʻz). Keyin "
                "almashing va javob yozing.")]:
    h.say_also(label, text)

# ------------------------------------------ the explanations, told in Uzbek
h.goals([
    "tillar haqidagi gʻayrioddiy fakt va raqamlar bor matnni oʻqishni",
    "orttirma daraja sifatlarini toʻgʻri ishlatishni va ularni qiyosiy darajadan farqlashni",
    "katta sonlarni aytish va yozishni, *and* ni toʻgʻri joyga qoʻyishni",
    "qaysi tillar qiyin, qaysilari oson ekani haqidagi radio dasturini tushunishni",
    "jahlingizni chiqaradigan narsa haqida post yozishni va fikrlarni *also*, *too* va *as well* bilan "
    "bogʻlashni",
])
h.retell("KEY WORDS", "KALIT SOʻZLAR", [
    "**an alphabet**  alifbo — tilning barcha harflari",
    "**a consonant**  undosh — *b*, *k* yoki *t* kabi harf",
    "**a vowel**  unli — *a*, *e* yoki *o* kabi harf",
    "**a volume**  jild — bir toʻplamdagi bitta kitob",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — ORTTIRMA DARAJA", [
    "Qiyosiy daraja ikki narsani solishtiradi. Orttirma daraja hammasining ichidan bittasini ajratib oladi — va "
    "unga deyarli doim *the* kerak.",
    "[[A]] Qisqa sifatlar — *-est* qoʻshiladi. *small → the smallest · hard → the hardest · long → the longest*",
    "[[B]] *-e* bilan yoki bitta unli + bitta undosh bilan tugasa. *nice → the nicest · big → the biggest · hot "
    "→ the hottest*",
    "[[C]] *-y* bilan tugasa. *easy → the easiest · heavy → the heaviest · pretty → the prettiest · dry → the "
    "driest*",
    "[[D]] Uzun sifatlar — *the most* ishlatiladi. *expensive → the most expensive · difficult → the most "
    "difficult · popular → the most popular*",
    "[[E]] Qoidasizlari. *good → the best · bad → the worst · far → the furthest*",
    "**Soʻz tartibi:** *the most* + sifat + ot. *the most practical laptop* deng, hech qachon *the laptop most "
    "practical* emas.",
])
h.retell("ERROR WARNING", "DIQQAT — KOʻP UCHRAYDIGAN XATOLAR", [
    "Besh narsa notoʻgʻri ketadi, oxirgi ikkitasi esa B1 darajagacha ham saqlanib qoladi:",
    "1 **Ikkilangan harf.** ✗ *bigest* → ✓ *biggest* · ✗ *cheappest* → ✓ *cheapest*",
    "2 **Qisqa sifat bilan most.** ✗ *Basque is the most hard language.* → ✓ *Basque is the hardest language.*",
    "3 **Orttirma daraja oʻrnida qiyosiy daraja.** ✗ *This is the cheaper dictionary in the shop.* → ✓ *the "
    "cheapest dictionary in the shop* · ✗ *He's the more intelligent person I know.* → ✓ *the most intelligent "
    "person I know*",
    "4 **most bilan soʻz tartibi.** ✗ *This is the laptop most practical for travelling.* → ✓ *the most "
    "practical laptop for travelling*",
    "5 **most oʻrnida more.** ✗ *I like more my smartphone.* → ✓ *I like my smartphone (the) most.*",
])
h.retell("PRONUNCIATION", "TALAFFUZ — ORTTIRMA DARAJA", [
    "Urgʻu *the* yoki *most* ga emas, sifatga tushadi. *the BIGgest · the EASiest · the HARDest*",
    "Savolda ham shunday: *What's the most BEAUtiful language in the world? · What's the most DIFFicult "
    "language?* Oʻquvchilar *most* ga urgʻu beradi — bu savoldek emas, bahsdek eshitiladi.",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — KATTA SONLAR", [
    "Ingliz tili katta sonlarni uchtadan boʻlaklab tuzadi va *and* ni faqat bitta joyga qoʻyadi.",
    "[[A]] Yuzlar. *603 = six hundred and three · 250 = two hundred and fifty · 900 = nine hundred* (*and* "
    "yoʻq)",
    "[[B]] *and* *hundred* soʻzidan keyin keladi — boshqa hech qayerda emas. *1,203 = one thousand, two hundred "
    "and three.*",
    "[[C]] Minglar. *12,000 = twelve thousand · 381,245 = three hundred and eighty-one thousand, two hundred and "
    "forty-five*",
    "[[D]] Millionlar. *2,000,670 = two million, six hundred and seventy · 900,000,000 = nine hundred million*",
    "Son aytilganda *hundred*, *thousand* va *million* hech qachon *-s* olmaydi: *six hundreds* emas, *six "
    "hundred*. *-s* faqat son boʻlmaganda qoʻshiladi: *hundreds of people*.",
])
h.retell("PRONUNCIATION", "TALAFFUZ — SONLAR", [
    "Oʻquvchilar doim adashtiradigan juftliklar. *thirteen* /θɜːTEEN/ da urgʻu oxirida; *thirty* /THIRty/ da — "
    "boshida. Tinglovchi uchun farq faqat shu.",
    "Ularni juft-juft ayting va farqni eshiting: *13 / 30 · 14 / 40 · 15 / 50 · 16 / 60 · 17 / 70 · 18 / 80 · "
    "19 / 90*",
    "*and* ga ham quloq soling. *Six hundred and three* — 603. *Six hundred, three* esa inglizcha emas. *and* ni "
    "eshitmasangiz, son odatda oʻsha yerda tugaydi.",
])
h.retell("YEARS ARE DIFFERENT", "YILLAR BOSHQACHA AYTILADI", [
    "Yil ikki yarim qilib aytiladi: *1755 = seventeen fifty-five · 1990 = nineteen ninety · 1806 = eighteen oh "
    "six*.",
    "Lekin 2000-yildan qoida oʻzgaradi: *2002 = two thousand and two · 2019 = twenty nineteen* (ikkalasi ham "
    "ishlatiladi).",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [
    "Tillarni oʻrganadigan va yangi kitobi chiqayotgan professor Ryan Hunter bilan radio intervyusini eshitasiz. "
    "Boshlovchi unga toʻrtta savol beradi.",
    "Agar sinfingizda audio boʻlsa, bu 10.04-trek. Boʻlmasa, oʻqituvchingiz matnni oʻqib beradi — topshiriqlar "
    "bir xil.",
])
h.retell("WHY YOU DIDN'T HEAR IT", "NEGA ESHITMADINGIZ?", [
    "**the butunlay yoʻqoladi.** *the biggest population* da /ðəbɪgɪst/ eshitiladi — sifat oldiga qoʻshilgan "
    "bitta kuchsiz tovush. Aniq *the* ni kutayotgan oʻquvchilar qiyosiy darajani eshitadi va *bigger* deb "
    "yozadi.",
    "**most ham kuchsiz.** *the most useful* → /ðəməstjuːsfəl/. Urgʻu sifatda, shuning uchun *most* ikki "
    "urgʻusiz tovush orasida deyarli yoʻqoladi.",
])
h.retell("LISTENING INTO WRITING", "TINGLASHDAN YOZISHGA", [
    "Avval uch kishining SMS xabarlar haqidagi gapini tinglang. Agar sinfingizda audio boʻlsa, bu 10.14-trek.",
])
h.retell("LINKING IDEAS WITH ALSO, TOO AND AS WELL", "ALSO, TOO VA AS WELL BILAN BOGʻLASH", [
    "Uchalasi ham „va yana bu ham“ degani. Farqi — qayerda turishida.",
    "*also* — yordamchi feʼldan keyin (*be, can, have*): *I can also understand why. · I've also got a friend "
    "like that.*",
    "*also* — asosiy feʼldan oldin: *She also knows a lot about computers.*",
    "*also* — yangi gap boshida: *Also, my friends send really funny texts.*",
    "*too* va *as well* — gap oxirida: *My sister does that too. · Some people post photos as well.*",
    "**Ehtiyot boʻling:** ✗ *I can too speak German.* → ✓ *I can also speak German* yoki ✓ *I can speak German "
    "too*. *too* hech qachon oʻrtada turmaydi.",
])
h.retell("CHECK BEFORE YOU HAND IT IN", "TOPSHIRISHDAN OLDIN TEKSHIRING", [
    "**Postingizda:** {box}  bitta orttirma daraja (*the worst thing, the most annoying…*)   {box}  bitta "
    "bogʻlovchi soʻz — *also, too* yoki *as well*   {box}  shunchaki fikr emas, haqiqiy misol.",
    "**Javobingizda:** {box}  rozilik yoki norozilik iborasi   {box}  postdagidan boshqa bogʻlovchi soʻz   "
    "{box}  shunchaki ha yoki yoʻq emas, sabab.",
    "{box}  *also* yordamchi feʼldan keyin, asosiy feʼldan oldin yoki gap boshida.   {box}  *too* va *as well* "
    "gap oxirida.   {box}  Soʻzlarni sanadim.",
])
h.one_per_line("TOPSHIRISHDAN OLDIN TEKSHIRING", None, at="box")
h.retell_cells({"Adjective": "Sifat", "Comparative": "Qiyosiy daraja", "Superlative": "Orttirma daraja",
                "Example": "Misol"})
h.retell_cells({"Number": "Son", "How you say it": "Qanday aytiladi"})
h.retell_cells({"What is written": "Yozilishi", "What you hear": "Eshitilishi", "Why": "Nega",
                "the joins to biggest": "<i>the</i> <i>biggest</i> ga qoʻshiladi",
                "most joins to useful": "<i>most</i> <i>useful</i> ga qoʻshiladi",
                "three words, two beats": "uch soʻz, ikki zarb",
                "than has no vowel of its own": "<i>than</i> ning oʻz unlisi yoʻq"},
               after="4.5  </span>")

# ------------------------------------------------------------------ the key
K = {}
for n, a in enumerate("cebad", 1):
    K[("1.2", n, 1)] = choose(FACTS12, a)
for n, a in enumerate("BCBB", 1):
    K[("1.3", n, 1)] = choose(["A", "B", "C"], a)
for n, a in enumerate(["an alphabet/alphabet", "a consonant/consonant", "a volume/volume/volumes", "steep"], 1):
    K[("1.4", n, 1)] = Q(a)
for n in range(1, 5):
    K[("1.5", n, 1)] = own()
K[("1.6", 1, 1)] = own()
for n, a in enumerate(["the shortest", "the funniest", "the driest", "the biggest", "the best", "the worst",
                       "the safest", "the hottest", "the most exciting", "the most tiring",
                       "the friendliest/the most friendly", "the most popular"], 1):
    K[("2.1", n, 1)] = Q(with_the(*a.split("/")))
for n, a in enumerate(["the best", "the most musical", "the hardest", "the easiest", "the biggest", "the longest",
                       "the worst", "the most interesting"], 1):
    K[("2.2", n, 1)] = Q(a)
TICKED = "✓/correct/tick"
for n, a in zip(range(2, 9), [
        either("This is the cheapest dictionary in the shop", "the cheapest"),
        either("He's the most intelligent person I know", "He is the most intelligent person I know",
               "the most intelligent"),
        either("This is the most practical laptop for travelling", "This is the most practical laptop for traveling",
               "the most practical laptop"),
        either("I like my smartphone the most", "I like my smartphone most", "I like my smartphone best",
               "I like my smartphone the best"),
        TICKED,
        TICKED,
        either("Mount Everest is the biggest mountain in the world", "Mount Everest is the highest mountain in the world",
               "the biggest", "the highest", "biggest", "highest")]):
    K[("2.3", n, 1)] = fix(a)
for n, a in enumerate(["the most beautiful", "the most difficult", "the most useful", "the best",
                       "the most popular"], 1):
    K[("2.4", n, 1)] = Q(a)
for n, phrase in STRESS25.items():
    words = phrase.split()
    K[("2.5", n, 1)] = choose(words, words[-1])
for n, a in enumerate(["the nicest", "the most beautiful", "the best", "the longest", "the hardest",
                       "the most difficult"], 1):
    K[("2.6", n, 1)] = Q(a)
for n, v in enumerate([603, 2002, 12000, 900000000, 600000, 8000000], 1):
    K[("3.1", n, 1)] = Q(figures(v))
for n, a in enumerate([spoken("eight hundred and forty"), spoken("seven thousand"), spoken("six hundred thousand"),
                       spoken("one million, two hundred and fifty thousand", "one million two hundred and fifty thousand",
                              "a million, two hundred and fifty thousand")], 1):
    K[("3.2", n, 1)] = Q(a)
for n, a in enumerate([spoken("six hundred and three"), TICKED, TICKED, spoken("two thousand and two"),
                       spoken("nine hundred million"), TICKED, TICKED,
                       spoken("one thousand, two hundred and three", "one thousand two hundred and three")], 1):
    K[("3.3", n, 1)] = fix(a)
for n, a in enumerate([spoken("one thousand, two hundred and three", "one thousand two hundred and three",
                              "a thousand, two hundred and three"),
                       spoken("four thousand and fifteen"),
                       spoken("fifty thousand, six hundred", "fifty thousand six hundred"),
                       spoken("three million and four")], 1):
    K[("3.4", n, 1)] = Q(a)
for n, a in enumerate([spoken("seventeen fifty-five"), spoken("nineteen ninety-one"),
                       spoken("eighteen oh six", "eighteen o six"), spoken("two thousand and two"),
                       spoken("twenty twenty-six", "two thousand and twenty-six")], 1):
    K[("3.6", n, 1)] = Q(a)
K[("3.6", 6, 1)] = own(control=None)              # the year they were born
for n in range(1, 9):                             # a guess before listening
    K[("4.1", n, 1)] = tick()
LANGS = ["Italian", "English", "Japanese", "Mandarin Chinese", "Basque", "Spanish", "Arabic", "Turkish"]
for n, a in enumerate(["Italian", "Japanese", "Spanish", "Mandarin Chinese"], 1):
    K[("4.2", n, 1)] = choose(LANGS, a)
K[("4.3", 1, 1)] = Q("Italian")
K[("4.3", 2, 1)] = Q("More than twenty/more than 20/over twenty/over 20/twenty/20/more than twenty languages")
K[("4.3", 3, 1)] = Q("In parts of Spain and France/in Spain and France/Spain and France/parts of Spain and France")
K[("4.3", 4, 1)] = Q("About 14%/14%/about 14 per cent/14 per cent/about fourteen per cent/fourteen per cent/"
                     "about 14 percent/14 percent/about fourteen percent/fourteen percent")
for n, a in enumerate(["musical", "hardest", "popular", "biggest", "useful"], 1):
    K[("4.4", n, 1)] = Q(a)
HP = {"H": "H · the host", "P": "P · the professor"}
for n, a in enumerate("PHPH", 1):
    K[("4.7", n, 1)] = choose(["H", "P"], a, labels=HP)
for n in (1, 2, 3):
    K[("4.8", n, 1)] = choose(["A", "B"], "B")
TEXTS = "send texts/texting/sending texts/text/texts/send texts and chat on social media apps/texts and social media"
PHONE = "talk on the phone/phone/talking on the phone/call/calling/talk/phone them/call them"
for n, a in enumerate(["her parents/parents/my parents/his parents/their parents", TEXTS, None,
                       "his family/family/her family/my family", PHONE, None,
                       "friends/her friends/his friends/my friends", PHONE, None], 1):
    K[("5.1", n, 1)] = Q(a) if a else own(control=None)
K[("5.2", 1, 1)] = pair()
NAMES = ["Genji", "Meepe", "MadMax", "AdamB", "Lars2", "Rainbows"]
for n, a in enumerate(["Genji", "Rainbows", "AdamB", "MadMax", "Lars2", "AdamB"], 1):
    K[("5.3", n, 1)] = choose(NAMES, a)
K[("5.4", 1, 1)] = own(control=None)
K[("5.4", 2, 1)] = Q("I don't agree with you, Genji/I don't agree with you/I don't agree")
K[("5.4", 3, 1)] = own(control=None)
K[("5.5", 1, 1)] = write(either("I've got a new PC and I also have a new laptop", "I've got a new PC and I've also got a new laptop",
                                "I've got a new PC and I have a new laptop too", "I've got a new PC and I have a new laptop as well"))
K[("5.5", 2, 1)] = write(either("We had satnav and we took a street map too", "We had satnav and we took a street map as well"))
K[("5.5", 3, 1)] = write(either("She works for a phone company and she also knows about computers",
                                "She works for a phone company and she also knows a lot about computers"))
K[("5.5", 4, 1)] = write(either("Tablets are light. They have a large screen as well", "They have a large screen as well",
                                "Tablets are light. They have a large screen too", "Tablets are light. Also, they have a large screen"))
for n, a in enumerate([either("I can speak French and I can also speak German", "I can speak French and I can speak German too",
                              "I can speak French and I can speak German as well", "I can also speak German"),
                       TICKED, TICKED,
                       either("I've got a laptop and also a tablet", "I've got a laptop and a tablet too",
                              "I've got a laptop and a tablet as well", "I've also got a laptop and a tablet")], 1):
    K[("5.6", n, 1)] = fix(a)
for n in range(1, 5):
    K[("5.8", n, 1)] = own()
K[("5.9", 20, 1)] = own(control="essay")
K[("5.9", 21, 1)] = pair()
for n in range(1, 10):                            # the checklist
    K[("5.9", n, 1)] = tick()

if __name__ == "__main__":
    data = h.build(K, "Elementary", 10, "Unit 10B & 10D — Communication")
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "e10bd.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
