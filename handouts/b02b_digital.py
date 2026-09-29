"""B02B All about me - Azamat's Beginner booklet (2B), done on a phone.

His design is rendered as it is and this decides every box. The key is his
(B02B All about me - ANSWER KEY), joined box by box by hand. This one exists
only in the Material Bank (_NEW BOOKLET STYLE); it splits into its five parts
as it should.

As with the other Beginner booklets, every box that explains is told again
in Uzbek, as are the goals and every instruction; the English examples stay
English, as do the reading, the model and the exercises.

Put right here: 4.3 line 2 read "Yes, I ... . It's here." - but in the
script she says No, I don't (she has no computer), and the key's answer is
don't; the line reads "No, I ... . I have my phone and two books." 2.8's
questions (the key accepts anything that fits) are the teacher's to read;
the survey and partner tables are done in class.

    python3 handouts/b02b_digital.py            # writes handouts/b02b.json, lists every box
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

DOCX = ("~/Documents/Claude/Material Bank/General English/A1 Beginner/_NEW BOOKLET STYLE/"
        "B02B All about me — BOOKLET.docx")
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


def uzbek_after(containing, text):
    """An Uzbek line under a paragraph that is not an exercise's instruction."""
    at = h.html.index(containing)
    end = h.html.index("</p>", at) + len("</p>")
    h.html = h.html[:end] + '<p class="hx-uz" lang="uz">%s</p>' % told(text, bare=True) + h.html[end:]


# ------------------------------------------------------------ 2 Grammar
rows_as_lines("2.3")
boxes_for("2.5", range(2, 9))                     # item 1 is the worked example
h.grid_rows("2.6")
rows_as_lines("2.8")

# ------------------------------------------------------------ 3 Vocabulary
boxes_for("3.5", range(1, 5), where="leader")
ENDS36 = halves("3.6", "a-d")
a, b = table_after("3.7")                         # a line a row: what they have, what they don't
tags = [t.group(0) for t in BLANK_TAG.finditer(h.html[a:b])]
h.html = h.html[:a] + "".join(
    '<p style="margin-bottom:8px"><span style="color:#6E6E6E">I have…</span> %s<br>'
    '<span style="color:#6E6E6E">I don\'t have…</span> %s</p>' % (tags[k], tags[k + 1])
    for k in range(0, len(tags), 2)) + h.html[b:]

# ------------------------------------------------------------ 4 Listening
m = re.search(r'(<p data-item="4\.3:2"[^>]*>.*?)Yes, I (<input[^>]*>) \. It&#x27;s here\.', h.html, re.S)
if not m:
    raise SystemExit("4.3 line 2 has moved")
h.html = h.html[:m.start()] + m.group(1) + "No, I " + m.group(2) + " . I have my phone and two books." + h.html[m.end():]
h.grid_rows("4.6")

# ------------------------------------------------------------ 5 Grammar and sounds
EXTRA54 = {1: ["knives", "bottles", "villages", "apples"], 2: ["books", "glasses", "pens", "keys"],
           3: ["tickets", "phones", "boxes", "books"], 4: ["cities", "watches", "babies", "photos"]}
boxes_for("5.4", EXTRA54)
boxes_for("5.6", (1, 2, 3), where="leader")
h.leaders("5.7", "CHECK BEFORE", [(20, W, "Write about your bag here")])
h.html = h.html.replace(TAGS[163], "", 1)         # the word count: the box counts them itself
FACES, CAN_DO = h.can_do_grid("5.9")

# ------------------------------- every instruction, once more, in Uzbek
for label, text in [
        ("1.1", "Bugun sumkangizda nima bor? Uchta narsani ayting."),
        ("1.2", "Kimda bor? *A* (Aziza), *B* (Ben) yoki *M* (Mei) ni tanlang."),
        ("1.3", "Toʻgʻri (*T*) mi yoki notoʻgʻri (*F*) mi?"),
        ("1.4", "Nechta? Sonini yozing."),
        ("1.5", "Gaplarni matndagi soʻz bilan toʻldiring."),
        ("1.6", "Endi siz. Gaplarni toʻldiring."),
        ("2.1", "*have* yoki *don't have* ni tanlang."),
        ("2.2", "*Do* bilan savol tuzing."),
        ("2.3", "Qisqa javoblarni toʻldiring."),
        ("2.4", "Suhbatni toʻldiring."),
        ("2.5", "Xatoni topib, toʻgʻrilang. IKKITA gap toʻgʻri — ular uchun *✓ It is correct* tugmasini bosing."),
        ("2.6", "Uch kishidan soʻrang. *✓* yoki *✗* yozing. Buni sinfda bajarasiz."),
        ("2.7", "Tinglang va ayting. Tezmi (*F*) yoki sekinmi (*S*)?"),
        ("2.8", "Har bir javob uchun savol yozing."),
        ("2.9", "Oʻzingiz haqingizda uchta rost gap yozing."),
        ("3.1", "*a* yoki *an* ni tanlang."),
        ("3.2", "Har bir gapni narsa nomi bilan toʻldiring."),
        ("3.3", "Sonni soʻz bilan yozing."),
        ("3.4", "Gaplarni oʻqing. Sonni raqam bilan yozing."),
        ("3.5", "Xatoni topib, toʻgʻri gapni yozing."),
        ("3.6", "Ikki qismni moslang: harfni tanlang."),
        ("3.7", "Sizda bor uchta narsani va yoʻq uchta narsani yozing."),
        ("3.8", "Sherigingiz bilan ishlang. Bir son ayting, sherigingiz keyingisini aytadi."),
        ("4.1", "Bir marta tinglang. Uning sumkasida nima bor? Har biri uchun *✓* yoki *✗* ni tanlang."),
        ("4.2", "Yana tinglang. Toʻgʻri (*T*) mi yoki notoʻgʻri (*F*) mi?"),
        ("4.3", "Yana bir marta tinglang va har bir qatorni toʻldiring."),
        ("4.4", "Tinglang va nima boʻlishiga eʼtibor bering."),
        ("4.5", "Har birini ikki marta ayting — avval sekin, keyin tez."),
        ("4.6", "Endi siz. Sherigingizdan sumkasi haqida soʻrang. Buni sinfda bajarasiz."),
        ("5.1", "Koʻplik shaklini yozing."),
        ("5.2", "Har bir gapni koʻplik shakli bilan toʻldiring."),
        ("5.3", "/s/, /z/ yoki /ɪz/? Tovushni tanlang."),
        ("5.4", "Qaysi soʻz koʻplikda qoʻshimcha boʻgʻin oladi? Tanlang."),
        ("5.5", "Namunani oʻqing. Keyin javob bering."),
        ("5.6", "Namuna haqidagi savollarga javob bering."),
        ("5.7", "Endi sumkangiz haqida yozing (50–60 soʻz)."),
        ("5.8", "Sherigingiz bilan almashing. Uning matnini oʻqib, javob bering. Buni sinfda bajarasiz."),
        ("5.9", "Butun darsni eslang. Har bir ish uchun qanchalik qila olishingizni tanlang.")]:
    h.say_also(label, text)
uzbek_after("One thing I still want to practise:", "Hali ham mashq qilmoqchi boʻlgan bitta narsa:")

# ------------------------------------------ the explanations, told in Uzbek
h.goals([
    "sizda nima bor va nima yoʻqligini aytishni",
    "*Do you have…?* deb soʻrashni va *Yes, I do* yoki *No, I don't* deb javob berishni",
    "odamlar olib yuradigan oʻnta narsani *a* yoki *an* bilan aytishni",
    "koʻplik shaklini yasashni — *-s*, *-es* va oʻzgaradiganlari",
    "koʻplikdagi *-s* ning uchta tovushini va qaysi biri boʻgʻin qoʻshishini eshitishni",
])
h.retell("KEY WORDS", "KALIT SOʻZLAR", [
    "**a bag**  sumka — ichiga narsa solasiz",
    "**a key**  kalit — u bilan eshikni ochasiz",
    "**a ticket**  chipta — avtobus, poyezd yoki kino uchun",
    "**an umbrella**  soyabon — yomgʻir uchun",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — HAVE", [
    "*HAVE* — „bu sizniki“ yoki „u siz bilan“ degani. Bu *be* dan keyin kerak boʻladigan ikkinchi feʼl.",
    "[[+]] *I have · you have · we have · they have. I have a phone. · You have my keys. · We have two tickets.*",
    "[[−]] *DON'T* ishlating. *I don't have an umbrella. · They don't have a car.* *don't* dan keyingi feʼl doim "
    "*have*, hech qachon *has* emas.",
    "[[?]] *DO* ishlating. *Do you have a phone? · Do they have tickets?* *do* oldinga chiqadi, feʼl esa "
    "oʻzgarmaydi.",
    "[[✓ ✗]] Qisqa javoblar: *Yes, I do. / No, I don't. · Yes, they do. / No, they don't.*",
    "**Ehtiyot boʻling — bu BE emas.** *be* bilan feʼlni oldinga surasiz: *Are you a student?* *have* bilan esa "
    "*do* qoʻshasiz: *Do you have a phone?* Ikki feʼl — ikki xil savol.",
])
h.retell("ERROR WARNING", "DIQQAT — KOʻP UCHRAYDIGAN XATOLAR", [
    "1 **Savolga DO kerak.** ✗ *Have you a phone?* → ✓ *Do you have a phone?*",
    "2 **DON'T va DO dan keyin feʼl — HAVE.** ✗ *I don't has a car.* → ✓ *I don't have a car.* · ✗ *Do you has "
    "it?* → ✓ *Do you have it?*",
    "3 **HAVE — bu BE emas.** ✗ *I am 20 years.* → ✓ *I am 20 years old.* Va ✗ *I have hungry.* → ✓ *I am "
    "hungry.* Koʻp tillarda bu yerda „bor“ ishlatiladi. Ingliz tilida esa *be*.",
    "4 **Qisqa javob HAVE emas, DO bilan.** ✗ *Yes, I have.* → ✓ *Yes, I do.* Savol *Do you…?* edi, demak javob "
    "*do*.",
])
h.retell("PRONUNCIATION — DO YOU DISAPPEARS", "TALAFFUZ — DO YOU YOʻQOLADI", [
    "*Do you* → /djə/ yoki /dʒə/. Ikki soʻz bitta kichik tovushga aylanadi. *Do you have a phone?* → /dʒə hævə "
    "fəʊn/.",
    "**Shuning uchun HAVE ga quloq soling.** *have* — baland soʻz, u savol *be* haqida emasligini bildiradi. /hæv/ "
    "ni eshitsangiz, javob — *Yes, I do.*",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — NARSALAR, A VA AN, SONLAR", [
    "Odamlar olib yuradigan oʻnta narsa: *a computer · a newspaper · a knife · a phone · a key · a watch · an "
    "umbrella · a ticket · a book · a bottle of water*",
    "**A yoki AN?** Koʻp soʻzlardan oldin *a*: *a key, a book, a phone*. *a, e, i, o, u* dan oldin *an*: *an "
    "umbrella, an apple, an egg*.",
    "**Gap harfda emas, TOVUSHDA.** *a university* — chunki u „yu“ deb aytiladi. · *an hour* — chunki *h* "
    "aytilmaydi va u „auə“ deb eshitiladi. Avval soʻzni ayting, keyin tanlang.",
    "Sonlar 1–12: *one · two · three · four · five · six · seven · eight · nine · ten · eleven · twelve*",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [
    "Bir ayol aeroportda. Xodim undan sumkasi haqida soʻraydi. Sumkadagi ikkita narsani samolyotga olib boʻlmaydi — "
    "qaysi ikkitasi ekanini bilasizmi?",
    "Agar sinfingizda audio boʻlsa, bu 2.15-trek. Boʻlmasa, oʻqituvchingiz matnni oʻqib beradi — topshiriqlar bir "
    "xil.",
])
h.retell("WHY YOU DIDN'T HEAR IT", "NEGA ESHITMADINGIZ?", [
    "**Koʻplikdagi -s juda kichik va juda muhim.** *a book* va *books* orasida bitta tovush farq bor. *a knife* va "
    "*knives* koʻproq oʻzgaradi — lekin ular ham xuddi shunday tez oʻtib ketadi.",
    "**Oldidagi songa quloq soling.** *two books · three newspapers · one phone*. Son baland aytiladi va *-s* "
    "butunlay yoʻqolganda ham birlik yoki koʻplik ekanini aytib beradi.",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — BIRLIK VA KOʻPLIK", [
    "**Koʻp soʻzlarga shunchaki -s qoʻshiladi.** *book → books · phone → phones · key → keys · ticket → tickets*",
    "**-ch, -sh, -ss, -s, -x dan keyin -es qoʻshiladi.** *watch → watches · glass → glasses · box → boxes · dish → "
    "dishes*",
    "**-y dan oldin undosh boʻlsa, -ies boʻladi.** *city → cities · baby → babies · country → countries* (lekin "
    "*boy → boys* — *y* dan oldin unli bor)",
    "**Baʼzilari butunlay oʻzgaradi.** *knife → knives · life → lives · man → men · woman → women · child → "
    "children*",
    "**Va ogohlantirish:** *photo → photos*, *photoes* emas. *-o* bilan tugaydigan baʼzi soʻzlarga shunchaki *-s* "
    "qoʻshiladi. Ularni birma-bir oʻrganish kerak.",
])
h.retell("PRONUNCIATION — THE THREE SOUNDS OF -S", "TALAFFUZ — -S NING UCHTA TOVUSHI", [
    "Harf doim *s*, lekin tovushi uchta. Siz tanlamaysiz — oldingi tovush siz uchun tanlaydi.",
    "[[/s/]] jimjit tovushdan keyin (*p, t, k, f*): *books · tickets · cups*",
    "[[/z/]] ovozli tovush yoki unlidan keyin: *keys · phones · bottles · pens*",
    "[[/ɪz/]] vishillovchi tovushdan keyin (*ch, sh, ss, s, x, ge*): *watches · glasses · boxes · villages*",
    "**Faqat /ɪz/ boʻgʻin qoʻshadi.** *book* ham, *books* ham bitta boʻgʻin. *watch* — bitta, *watches* — ikkita. "
    "Qarsak chalib ayting — eshitasiz.",
])
h.retell("CHECK BEFORE YOU GIVE IT IN", "TOPSHIRISHDAN OLDIN TEKSHIRING", [
    "{box}  Har bir koʻplikda *-s* yoki *-es* bor.   {box}  Har bir birlikdagi narsadan oldin *a* yoki *an* "
    "yozdim.",
    "{box}  Kamida bir marta *don't have* ishlatdim.   {box}  *I have hungry* yoki *I have 20 years* deb "
    "yozmadim.",
    "{box}  Kamida ikki marta son ishlatdim.   {box}  Soʻzlarni sanadim.",
])
h.one_per_line("TOPSHIRISHDAN OLDIN TEKSHIRING", None, at="box")
h.retell_cells({"What is written": "Yozilishi", "What you hear": "Eshitilishi", "Why": "Nega",
                "do you is one sound": "<i>do you</i> bitta tovush",
                "the number tells you": "son aytib beradi",
                "do is the loud last word": "<i>do</i> — baland oxirgi soʻz",
                "of is almost nothing": "<i>of</i> deyarli eshitilmaydi"},
               after="4.4  </span>")

# ------------------------------------------------------------------ the key
K = {}
for n in range(1, 4):                             # what is in their bag
    K[("1.1", n, 1)] = own(control=None)
ABM = {"A": "A · Aziza", "B": "B · Ben", "M": "M · Mei"}
for n, a in enumerate("BABMBM", 1):
    K[("1.2", n, 1)] = choose(["A", "B", "M"], a, labels=ABM)
TF = {"T": "T · true", "F": "F · false"}
for n, a in enumerate("FTTFTT", 1):
    K[("1.3", n, 1)] = choose(["T", "F"], a, labels=TF)
for n, a in enumerate(["2/two", "3/three", "2/two", "1/one", "1/one", "1/one"], 1):
    K[("1.4", n, 1)] = Q(a)
for n, a in enumerate(["small", "broken", "heavy", "phone", "sister"], 1):
    K[("1.5", n, 1)] = Q(a)
for key in ((1, 1), (2, 1), (2, 2), (3, 1), (4, 1)):   # their own bag
    K[("1.6",) + key] = own(control=None)
HAVE = ["have", "don't have"]
for n, a in enumerate(["have", "don't have", "have", "don't have", "have", "don't have"], 1):
    K[("2.1", n, 1)] = choose(HAVE, a)
for n, a in enumerate(["Do you have a phone", "Do they have tickets", "Do we have an umbrella",
                       "Do you have a computer", "Do they have my keys"], 1):
    K[("2.2", n, 1)] = write(a)
for n, a in enumerate(["I do", "they don't/they do not", "we do/you do", "I don't/I do not"], 1):
    K[("2.3", n, 1)] = Q(a)
for n, a in enumerate(["Do", "have", "do", "Do", "have", "don't/do not", "Do", "have", "don't have/do not have",
                       "don't/do not"], 1):
    K[("2.4", n, 1)] = Q(a)
TICKED = "✓/correct/tick"
for n, a in zip(range(2, 9), [
        either("I don't have a car", "I do not have a car", "have"),
        either("Do you have my keys", "have"),
        "Yes, I do",
        either("I am hungry", "I'm hungry", "am"),
        TICKED, TICKED,
        either("I am 20 years old", "I'm 20 years old", "I am 20", "I'm 20", "years old")]):
    K[("2.5", n, 1)] = fix(a)
for n in range(1, 13):                            # the survey, in class
    K[("2.6", n, 1)] = pair()
FS = {"F": "F · fast", "S": "S · slow"}
for n, a in enumerate("FSFS", 1):
    K[("2.7", n, 1)] = choose(["F", "S"], a, labels=FS)
for n in range(1, 4):                             # any question that fits the answer
    K[("2.8", n, 1)] = own()
for n in range(1, 4):                             # true sentences about them
    K[("2.9", n, 1)] = own(control=None)
for n, a in enumerate(["a", "an", "a", "an", "a", "an", "a", "an"], 1):
    K[("3.1", n, 1)] = choose(["a", "an"], a)
for n, a in enumerate(["key", "umbrella", "newspaper", "knife", "watch", "bottle"], 1):
    K[("3.2", n, 1)] = Q(a)
for n, a in enumerate(["three", "seven", "nine", "eleven", "twelve", "eight"], 1):
    K[("3.3", n, 1)] = Q(a)
for n, a in enumerate(["3", "5", "11", "8"], 1):
    K[("3.4", n, 1)] = Q(a)
for n, a in enumerate([either("I have an umbrella in my bag", "an umbrella"),
                       either("She has a key and a phone", "a key and a phone"),
                       either("We wait for an hour every morning", "an hour"),
                       either("I have three newspapers", "three newspapers", "newspapers")], 1):
    K[("3.5", n, 1)] = write(a)
for n, a in enumerate("badc", 1):
    K[("3.6", n, 1)] = choose(ENDS36, a)
for n in range(1, 7):                             # their own things
    K[("3.7", n, 1)] = own(control=None)
IN_BAG = {"yes": "✓ in her bag", "no": "✗ not in her bag"}
for n, a in enumerate(["yes", "no", "yes", "no", "yes", "yes", "yes", "no"], 1):
    K[("4.1", n, 1)] = choose(["yes", "no"], a, labels=IN_BAG)
for n, a in enumerate("TTFTT", 1):
    K[("4.2", n, 1)] = choose(["T", "F"], a, labels=TF)
for key, a in (((1, 1), "Do"), ((1, 2), "have"), ((2, 1), "don't/do not"), ((3, 1), "Do"), ((3, 2), "have"),
               ((4, 1), "don't/do not"), ((5, 1), "Sorry/I'm sorry/I am sorry"), ((5, 2), "can't/cannot/can not")):
    K[("4.3",) + key] = Q(a)
for n in range(1, 9):                             # a partner's bag, in class
    K[("4.6", n, 1)] = pair()
for n, a in enumerate(["books", "watches", "keys", "cities", "knives", "photos", "glasses", "babies"], 1):
    K[("5.1", n, 1)] = Q(a)
for n, a in enumerate(["keys", "glasses", "photos", "cities", "knives", "women"], 1):
    K[("5.2", n, 1)] = Q(a)
for n, a in enumerate(["/s/", "/z/", "/ɪz/", "/z/", "/s/", "/ɪz/"], 1):
    K[("5.3", n, 1)] = choose(["/s/", "/z/", "/ɪz/"], a)
for n, a in {1: "villages", 2: "glasses", 3: "boxes", 4: "watches"}.items():
    K[("5.4", n, 1)] = choose(EXTRA54[n], a)
K[("5.6", 1, 1)] = own()
K[("5.6", 2, 1)] = own()
K[("5.6", 3, 1)] = write("Because she always forgets it/She always forgets it/Because she forgets it/"
                         "because she always forgets it")
K[("5.7", 20, 1)] = own(control="essay")
for n in range(1, 7):                             # the checklist
    K[("5.7", n, 1)] = tick()
for n in range(1, 4):                             # a partner's text, in class
    K[("5.8", n, 1)] = pair()
FACE_SAYS = dict(zip(FACES, ["🙂 Ha", "😐 Qisman", "🙁 Hali yoʻq"]))
for n in CAN_DO:
    K[("5.9", n, 1)] = choose(FACES, labels=FACE_SAYS)
K[("5.9", 19, 1)] = note()                        # one thing to practise: may stay empty

if __name__ == "__main__":
    data = h.build(K, "Beginner", 2, "Unit 2B — All about me")
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "b02b.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
