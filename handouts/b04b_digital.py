"""B04B My life and my family - Azamat's Beginner booklet (4B), done on a phone.

The first booklet of the new style (BRIEF §0 in the Material Bank) to go online.
Two things are different from the older Beginner booklets, and this script
puts both right before the usual work:

  - the new booklets are drawn in the purple "web" theme, but the site reads
    the booklets' teal (section bars, exercise numbers, panels); so this reads
    a TEAL build of the same booklet, made with BOOK_THEME=teal from
    build_b04b.js and kept in "_NEW BOOKLET STYLE/digital source/". The site
    dresses it in its own plum anyway;
  - every exercise sits in a one-cell borderless table that keeps it on one
    page of paper; a phone has no pages, so those tables are taken away and
    the page has the older booklets' shape (the reading text becomes prose,
    which the site sets as an article).

As with the other Beginner booklets, every box that explains is told again in
Uzbek, as is every instruction; the English examples, the reading and the
exercises stay English. The key is his (B04B ... ANSWER KEY), box by box.

What the paper leaves to a pen: 3.7's "circle the odd word" is a tap, with a
box for why; the ruled lines under a writing task become one growing box per
item; the essay is one big box with a word count. 5.2 (say the sentences
aloud) has no box, and 5.3's three checks are ticks - the recording itself is
sent to the teacher, as the booklet says. The 5.6 plan needs three people,
the fourth and fifth rows may stay empty.

    python3 handouts/b04b_digital.py            # writes handouts/b04b.json, lists every box
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import (Handout, Q, choose, tick, own, write, note, report,   # noqa: E402
                     BLANK_TAG, plain, ITEM_P, told, bh_section_at)

DOCX = ("~/Documents/Claude/Material Bank/General English/A1 Beginner/_NEW BOOKLET STYLE/digital source/"
        "B04B My life and my family — BOOKLET (teal, for the website).docx")
W = "95%"

h = Handout(DOCX)

# ------------------------------------------------- the one-page blocks go
OPEN = re.compile(r'<table class="bk">|</table>')
BLOCK = re.compile(r'<tr><td style="vertical-align:top;border-top:0;border-bottom:0;border-left:0;border-right:0">'
                   r'(.*)</td></tr>$', re.S)


def unwrap_blocks(page):
    while True:
        stack = []
        for m in OPEN.finditer(page):
            if m.group(0) != "</table>":
                stack.append(m.start())
                continue
            start = stack.pop()
            inner = page[start + len('<table class="bk">'):m.start()]
            depth = rows = cells = 0
            for t in re.finditer(r'<table class="bk">|</table>|<tr>|<td\b', inner):
                tok = t.group(0)
                if tok.startswith("<table"):
                    depth += 1
                elif tok == "</table>":
                    depth -= 1
                elif depth == 0 and tok == "<tr>":
                    rows += 1
                elif depth == 0:
                    cells += 1
            body = BLOCK.match(inner)
            if rows == 1 and cells == 1 and body:
                page = page[:start] + body.group(1) + page[m.end():]
                break
        else:
            return page


h.html = unwrap_blocks(h.html)


def either(*forms):
    return "/".join(forms)


def words(n):
    """A number in words, with or without its hyphen."""
    return either(n, n.replace("-", " ")) if "-" in n else n


def section(label):
    return h.html.index("%s  </span>" % label)


def boxes_per_item(label, until, nums, placeholder=""):
    """The ruled lines under each item go; each item gets one growing box."""
    h.leaders(label, until, [])
    for n in nums:
        h.item_box(label, n, width=W, placeholder=placeholder)


def reword(label, old, new):
    at = section(label) + len("%s  </span>" % label)
    end = h.html.index("</p>", at)
    if plain(h.html[at:end]) != old:
        raise SystemExit("%s says %r" % (label, plain(h.html[at:end])))
    style = re.match(r'<span( style="[^"]*")?>', h.html[at:end])
    h.html = h.html[:at] + "<span%s>%s</span>" % (style.group(1) or "", new) + h.html[end:]


# ------------------------------------------------------------ 1 Reading
h.leaders("1.1", "FAMOUS BROTHERS", [(1, W, "Write your sentence")])
h.leaders("1.8", "Grammar  ·", [(1, W, "Two sentences")])

# ------------------------------------------------------------ 2 Grammar
h.leaders("2.4", "2.5  </span>", [(1, W, "Dilshod"), (2, W, "Gulnora"), (3, W, "Sanjar")])
boxes_per_item("2.5", "2.6  </span>", range(1, 4))
boxes_per_item("2.7", "2.8  </span>", range(1, 5))
boxes_per_item("2.8", "2.9  </span>", range(1, 5))
h.leaders("2.9", "Vocabulary  ·", [(1, W, "Four sentences")])

# ------------------------------------------------------------ 3 Vocabulary
reword("3.7", "Think. Which word is different? Circle it and say why in a few words.",
       "Think. Which word is different? Tap it, then say why in a few words.")
ODD = {}
for m in reversed([m for m in ITEM_P.finditer(h.html) if m.group(2) == "3.7"]):
    n = int(m.group(3))
    guts = m.group(4)
    tag = BLANK_TAG.search(guts)
    if not tag:                                   # the worked example has no box
        continue
    arrow = guts.index("→")
    words_html = guts[:arrow]
    ODD[n] = [w.strip() for w in re.sub(r"^\d+\s+", "", plain(words_html)).split("·")]
    new = ("%s%s<br>{{box:3.7:%d:60px:}}  <span>Why?</span> %s</span>"
           % (m.group(1), words_html.rstrip(), n, tag.group(0)))
    h.html = h.html[:m.start()] + new + "</p>" + h.html[m.end():]
boxes_per_item("3.10", "3.11  </span>", range(1, 5))
h.leaders("3.11", "Listening  ·", [(1, W, "Your sentence")])

# ------------------------------------------------------------ 4 Listening
h.leaders("4.5", "Speaking and writing  ·", [(1, W, "Two sentences")])

# ------------------------------------------------------------ 5 Speaking and writing
boxes_per_item("5.1", "5.2  </span>", range(1, 7))
boxes_per_item("5.4", "5.5  </span>", range(1, 4))


def plan_rows(label):
    """The plan table, every column a box (grid_rows takes the first column as
    each row's name): one block per person, each box with its column's name."""
    head = h.html.index("%s  </span>" % label)
    a = h.html.index('<table class="bk">', head)
    b = h.html.index("</table>", a) + len("</table>")
    rows = [re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)
            for r in re.findall(r"<tr>(.*?)</tr>", h.html[a:b], re.S)]
    names = [plain(c) for c in rows[0]]
    out = ""
    for k, row in enumerate(rows[1:], 1):
        bits = []
        for name, cell in zip(names, row):
            tag = BLANK_TAG.search(cell)
            h.blanks[int(tag.group(1))]["text"] = "Person %d · %s" % (k, name)
            box = re.sub(r' style="[^"]*"', "", tag.group(0))[:-1] + ' style="width:11em">'
            bits.append('<span style="color:#6E6E6E">%s</span> %s' % (name, box))
        out += ('<p data-item="%s:%d" style="margin-bottom:8px"><span style="font-weight:700">Person %d</span>'
                '<br>%s</p>' % (label, k, k, "<br>".join(bits)))
    h.html = h.html[:a] + out + h.html[b:]


plan_rows("5.6")
h.leaders("5.7", "</div>", [(1, W, "Write about your family here")])

# ------------------------------- every instruction, once more, in Uzbek
for label, text in [
        ("1.1", "Oʻqishdan oldin. Akangiz, ukangiz, opangiz yoki singlingiz bormi? Toʻliq gap yozing."),
        ("1.2", "Toʻgʻri (*T*) mi yoki notoʻgʻri (*F*) mi? Tanlang."),
        ("1.3", "Gaplarni toʻldiring. BITTA soʻz yoki son yozing."),
        ("1.4", "Yoshlarni soʻz bilan yozing."),
        ("1.5", "Oʻylang. *Fakt* hamma uchun toʻgʻri. *Fikr* — bir odam oʻylaydigan narsa. *F* (fakt) yoki "
                "*O* (fikr) ni tanlang."),
        ("1.6", "Feʼllarni toping. Matndagi feʼlni yozing. Keyin: bu feʼllar qaysi harf bilan tugaydi?"),
        ("1.7", "Imlo. Bu oilalar qaysi davlatdan? Davlat nomini yozing."),
        ("1.8", "Oʻzbekistondagi yoki boshqa davlatdagi mashhur oila haqida ikkita rost gap yozing."),
        ("2.1", "*he / she / it* shaklini yozing."),
        ("2.2", "*he*, *she* yoki *it* ni tanlang."),
        ("2.3", "Azizning matnini toʻldiring. Qavsdagi feʼllarni ishlating."),
        ("2.4", "Jadvalga qarang. Har bir odam haqida ikkita gap yozing."),
        ("2.5", "Boshqa odam haqida yozing. Feʼlni oʻzgartiring."),
        ("2.6", "*-s*, *-es* yoki *–* (hech narsa) ni tanlang."),
        ("2.7", "Har bir gapda BITTA xato bor. Toʻgʻri gapni yozing."),
        ("2.8", "Soʻzlarni tartib bilan qoʻying. Gapni yozing."),
        ("2.9", "Endi siz. Oilangizdagi odamlar haqida toʻrtta gap yozing. Har birida boshqa feʼl ishlating."),
        ("3.1", "Lazizning oilaviy surat haqidagi xabarini oʻqing. Qalin soʻzlarga qarang. Keyin savollarga "
                "javob bering."),
        ("3.2", "Jadvalni toʻldiring: erkak / oʻgʻil bola — ayol / qiz bola."),
        ("3.3", "Soʻzni yozing."),
        ("3.4", "Bitta yoki koʻp? Koʻplik shaklini yozing. Ehtiyot boʻling — TOʻRTTASI qoidaga boʻysunmaydi!"),
        ("3.5", "Boburning oila daraxtiga qarang. Ismlarni yozing."),
        ("3.6", "*am*, *is*, *has*, *lives* yoki *only* ni tanlang."),
        ("3.7", "Oʻylang. Qaysi soʻz boshqacha? Uni tanlang, keyin nega ekanini bir-ikki soʻz bilan yozing."),
        ("3.8", "Sonlarni soʻz bilan yozing."),
        ("3.9", "Sonlar soʻz bilan. Javobni soʻz bilan yozing."),
        ("3.10", "Oilangizdagi odamlar haqida savol va javob yozing."),
        ("3.11", "Bu soʻzlarni uch marta ovoz chiqarib ayting. *th* uchun tilingizni tishlaringiz orasiga "
                 "qoʻying. Keyin uchta soʻz bilan bitta gap yozing."),
        ("4.1", "Tinglang. Oila aʼzosini bildiruvchi soʻzni yozing."),
        ("4.2", "Ularning kasbi nima? Eshitgan kasbingizni tanlang."),
        ("4.3", "Yana tinglang. Toʻgʻri (*T*) mi yoki notoʻgʻri (*F*) mi?"),
        ("4.4", "Imlo va sonlar. Javobni yozing."),
        ("4.5", "04.08-trekdagi odamlar haqida ikkita gap yozing. *has* yoki *-s* li feʼl ishlating."),
        ("5.1", "Savollarga javob bering. Toʻliq gaplar yozing."),
        ("5.2", "Yozib olishdan oldin. Bu gaplarni uch marta ovoz chiqarib ayting. *-s* aniq eshitilsin."),
        ("5.3", "Oʻzingizni yozib oling. Oilangiz haqida taxminan bir daqiqa gapiring. 5.1 dagi javoblaringizdan "
                "foydalaning, lekin ularni oʻqimang. Yozuvni oʻqituvchingizga yuboring."),
        ("5.4", "Madinaning matnini oʻqing. Toping…"),
        ("5.5", "Bir oʻquvchi bu matnni yozgan. BESHTA xatoni toping va toʻgʻrisini yozing."),
        ("5.6", "Matningizni rejalashtiring. Uch-toʻrt kishi haqida qisqa yozib qoʻying."),
        ("5.7", "Oilangiz haqida yozing (50–70 soʻz). 5.6 dagi reja va Madinaning matnidan foydalaning: kim · "
                "yoshi · qayerda · ishi yoki maktabi.")]:
    h.say_also(label, text)

# ------------------------------------------ the explanations, told in Uzbek
h.retell("KEY WORDS", "KALIT SOʻZLAR", [
    "**famous**  mashhur — hamma uni taniydi",
    "**a prince**  shahzoda — qirolning oʻgʻli",
    "**a boxer**  bokschi — mushtlashadigan sportchi",
    "**the mayor**  shahar hokimi — shaharning boshligʻi",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — HE / SHE / IT + FEʼL-S", [
    "[[A]] **I, you, we, they** dan keyin feʼl oʻzgarmaydi: *I live in Tashkent. · They work in a bank.* "
    "**He, she, it** dan keyin esa feʼlga **-s** qoʻshiladi: *He lives in Tashkent. · She works in a bank.*",
    "[[B]] **Imlo.** Koʻp feʼllar: **+ s** — *works, lives, plays, speaks*. **-o, -ch, -sh, -x** bilan "
    "tugasa: **+ es** — *goes, does, watches, teaches, washes*. Undoshdan keyin **-y** boʻlsa: **y → ies** — "
    "*study → studies* (lekin *play → plays*). **Istisno:** *have → has*.",
    "[[C]] **He, she yoki it?** **he** — erkak yoki oʻgʻil bola · **she** — ayol yoki qiz bola · **it** — narsa "
    "yoki hayvon. Oʻzbek tilida *u* uchalasi uchun bitta soʻz — ingliz tilida esa tanlashingiz kerak!",
    "[[D]] **Ism yoki ot** ham *he / she / it* kabi ishlaydi: *Serena has two daughters. · My brother plays "
    "football. · The cat sleeps a lot.*",
])
h.retell_cells({"Person": "Kim", "Verb": "Feʼl", "Example": "Misol"}, after="HE / SHE / IT + FEʼL-S")
h.retell("WATCH OUT!", "DIQQAT — KOʻP UCHRAYDIGAN XATOLAR", [
    "1 ✗ *She have two sisters.* → ✓ *She has two sisters.* — *she* dan keyin *has*.",
    "2 ✗ *My brother live in Moscow.* → ✓ *My brother lives in Moscow.* — *-s* ni unutmang.",
    "3 ✗ *My mother is work in a hospital.* → ✓ *My mother works in a hospital.* — *is* kerak emas.",
    "4 ✗ *My sister is a doctor. He works at night.* → ✓ *She works at night.* — opa-singil, ona, xola: "
    "*she*!",
    "5 ✗ *He studys. She gos.* → ✓ *He studies. She goes.* — imloga eʼtibor bering.",
])
h.retell("SAY IT — THREE SOUNDS OF -S", "AYTING — -S NING UCH XIL TOVUSHI", [
    "**/s/**  *works · speaks · likes*      **/z/**  *lives · plays · goes · has*      **/ɪz/**  *watches · "
    "teaches · washes*",
    "Har bir guruhni uch marta ovoz chiqarib ayting.",
])
h.retell("NUMBERS 21–100", "SONLAR 21–100", [
    "**21** *twenty-one* · **34** *thirty-four* · **40** *forty* (*fourty* emas) · **57** *fifty-seven* · "
    "**63** *sixty-three* · **79** *seventy-nine* · **85** *eighty-five* · **99** *ninety-nine* · **100** "
    "*a hundred*",
    "Oʻnlik + chiziqcha (**-**) + birlik: *twenty-one*. *twenty and one* emas.",
])
h.retell("ERROR WARNING — AGE", "DIQQAT — YOSH", [
    "Yoshni aytganda *have* emas, **be** ishlatamiz: ✓ *I'm 20.* ✓ *She's 46.* ✗ *I have 20 years.* ✗ *She "
    "has 46 years.*",
    "Savol: ✓ *How old are you? · How old is your mother?* ✗ *How many years are you?*",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [
    "Darslikdagi **04.08-trek**ni tinglang (4-unit, 4B dars): oltita mashhur odam va ularning oilalari.",
    "Agar trek sizda boʻlmasa, oʻqituvchingizdan soʻrang.",
])
h.retell("USEFUL LANGUAGE", "FOYDALI IBORALAR", [
    "Oilangiz haqida gapirganda va yozganda shu iboralardan foydalaning:",
    "*There are … people in my family. · My father works in … · My sister is … (years old). · She studies at "
    "… · He lives in … · We live in …*",
])

# --------------------- the goals, in Uzbek, where the site's cover reads them
# The new booklets have no "You will learn to" box (he dropped it on paper);
# the site's cover lists the goals from one, as on every other Beginner handout.
GOALS = [
    "*he / she / it* dan keyin feʼlga *-s* qoʻshishni: *She works. He lives. It has.*",
    "*goes, watches, studies, has* kabi shakllarni toʻgʻri yozishni",
    "*u* ni toʻgʻri tarjima qilishni: erkak — *he*, ayol — *she*, narsa yoki hayvon — *it*",
    "oila va odamlar haqidagi soʻzlarni: *son, daughter, aunt, uncle, men, women, children, people*",
    "sonlarni 21 dan 100 gacha aytish va yozishni",
    "yoshni *be* bilan aytishni: *She's 46.* — *She has 46 years* emas",
    "oilangiz haqida gapirib, qisqa matn yozishni",
]
first_bar = bh_section_at().search(h.html).start()
h.html = (h.html[:first_bar] + '<table class="bk"><tr><td><p><span>You will learn to</span></p>'
          + "".join('<p><span>—  </span>%s</p>' % told(g, bare=True) for g in GOALS)
          + "</td></tr></table>" + h.html[first_bar:])

# ------------------------------------------------------------------ the key
K = {}
TF = {"T": "T · true", "F": "F · false"}
FO = {"F": "F · fact", "O": "O · opinion"}
K[("1.1", 1, 1)] = own()
for n, a in enumerate("FTFTFFFT", 1):
    K[("1.2", n, 1)] = choose(["T", "F"], a, labels=TF)
for n, a in enumerate([either("45", "forty-five", "forty five"), "England", "Meghan",
                       either("Kyiv", "Kiev"), either("three", "3")], 1):
    K[("1.3", n, 1)] = Q(a)
for n, a in enumerate(["forty-six", "forty-four", "forty-two", "fifty"], 1):
    K[("1.4", n, 1)] = Q(words(a))
for n, a in enumerate("FOFOFO", 1):
    K[("1.5", n, 1)] = choose(["F", "O"], a, labels=FO)
for n, a in enumerate(["lives", "lives", "works", "has"], 1):
    K[("1.6", n, 1)] = Q(a)
K[("1.6", 4, 2)] = Q(either("s", "-s", "S"))
for n, a in enumerate([either("the USA", "USA", "the US", "US", "the United States", "United States", "America"),
                       either("the United Kingdom", "United Kingdom", "the UK", "UK", "England", "Britain",
                              "Great Britain"),
                       "Ukraine"], 1):
    K[("1.7", n, 1)] = Q(a)
K[("1.8", 1, 1)] = own()
for n, a in enumerate(["lives", "plays", "goes", "watches", "studies", "teaches", "has", "speaks"], 1):
    K[("2.1", n, 1)] = Q(a)
for n, a in enumerate(["She", "He", "It", "She", "It"], 1):
    K[("2.2", n, 1)] = choose(["He", "She", "It"], a)
for n, a in enumerate(["works", "teaches", "studies", "go", "lives", "has"], 1):
    K[("2.3", n, 1)] = Q(a)
for n in range(1, 4):                             # two sentences of their own about each person
    K[("2.4", n, 1)] = own()
for n, a in enumerate([either("My friend has two brothers", "has two brothers"),
                       either("My sister goes to school by bus", "goes to school by bus"),
                       either("My grandfather watches TV in the evening", "watches TV in the evening")], 1):
    K[("2.5", n, 1)] = write(a)                    # the whole sentence, or only what follows "My friend …"
for n, a in enumerate(["–", "-es", "–", "-s", "–", "-es"], 1):
    K[("2.6", n, 1)] = choose(["-s", "-es", "–"], a)
for n, a in enumerate(["My uncle has a big car", "Our teacher speaks three languages",
                       "My mother works in a shop", either("My sister is 15. She goes to school", "She goes to school")], 1):
    K[("2.7", n, 1)] = write(a)
for n, a in enumerate(["My grandmother lives in Khiva",
                       either("Lola has a brother and a sister", "Lola has a sister and a brother"),
                       either("My cousin goes to school by bus", "My cousin goes by bus to school"),
                       "My aunt teaches English"], 1):
    K[("2.8", n, 1)] = write(a)
K[("2.9", 1, 1)] = own()
for n, a in enumerate(["grandparents", either("two", "2"), "aunt"], 1):
    K[("3.1", n, 1)] = Q(a)
for n, a in enumerate(["daughter", "sister", "wife", "grandfather", "uncle"], 1):
    K[("3.2", n, 1)] = Q(a)
for n, a in enumerate(["parents", "children", "wife", "grandfather"], 1):
    K[("3.3", n, 1)] = Q(a)
for n, a in enumerate(["girls", "men", "women", "children", "people", "babies"], 1):
    K[("3.4", n, 1)] = Q(a)
for n, a in enumerate([either("Akmal and Nodira", "Nodira and Akmal"), "Madina", "Akmal",
                       either("38", "thirty-eight", "thirty eight", "She is 38", "She's 38", "38 years old")], 1):
    K[("3.5", n, 1)] = Q(a)
for n, a in enumerate(["am", "has", "lives", "only", "is", "lives"], 1):
    K[("3.6", n, 1)] = choose(["am", "is", "has", "lives", "only"], a)
ODD_KEY = {1: "aunt", 2: "girl", 3: "fourteen", 4: "baby", 5: "son"}
for n in sorted(ODD):
    if ODD_KEY[n] not in ODD[n]:
        raise SystemExit("3.7 item %d: %s is not one of %s" % (n, ODD_KEY[n], ODD[n]))
    K[("3.7", n, 1)] = choose(ODD[n], ODD_KEY[n])
    K[("3.7", n, 2)] = own()
for n, a in enumerate(["twenty-eight", "forty-one", "fifty-five", "sixty-six", "seventy-three", "eighty-seven",
                       "ninety-two", either("a hundred", "one hundred", "hundred")], 1):
    K[("3.8", n, 1)] = Q(words(a))
for n, a in enumerate(["eighty", "ninety-two", either("a hundred", "one hundred", "hundred"), "thirty-three",
                       "seventy-five", "thirty-eight"], 1):
    K[("3.9", n, 1)] = Q(words(a))
for n in range(1, 5):                             # about their own family
    K[("3.10", n, 1)] = own()
K[("3.11", 1, 1)] = own()
for (n, k), a in {(1, 1): "husband", (1, 2): "sister", (2, 1): "parents", (3, 1): "wife", (3, 2): "daughter",
                  (4, 1): "father", (5, 1): "mother"}.items():
    K[("4.1", n, k)] = Q(a)
JOBS = ["football player", "pop star", "film star", "film director", "actor", "singer"]
for n, a in enumerate(JOBS, 1):
    K[("4.2", n, 1)] = choose(JOBS, a)
for n, a in enumerate("TFTFTF", 1):
    K[("4.3", n, 1)] = choose(["T", "F"], a, labels=TF)
K[("4.4", 1, 1)] = Q("Cuba")
K[("4.4", 2, 1)] = Q("three")
K[("4.5", 1, 1)] = own()
for n in range(1, 7):
    K[("5.1", n, 1)] = own()
for n in range(1, 4):                             # the checks before they send the recording
    K[("5.3", n, 1)] = tick()
for n in range(1, 4):                             # verbs, ages, the opinion: any of several
    K[("5.4", n, 1)] = own()
for n in range(1, 6):                             # the mistake, then its correction - in any order
    K[("5.5", n, 1)] = own()
    K[("5.5", n, 2)] = own()
for n in range(1, 21):                            # the plan: three people at least
    K[("5.6", n, 1)] = own() if n <= 12 else note()
K[("5.7", 1, 1)] = own(control="essay")

if __name__ == "__main__":
    data = h.build(K, "Beginner", 4, "Unit 4B — My life and my family")
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "b04b.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
