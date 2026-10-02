"""P02AC Travel and tourism - the new-style Pre-Intermediate booklet (2A & 2C), done on a phone.

It replaces "Unit 2A & 2C - Travel and tourism" (test 79, p02ac_digital.py), the
older design; the exercises are all new, so no answers carry across. Built like
p01ac_new_digital.py: a TEAL build of the booklet (BOOK_THEME=teal node
build_p02ac.js, in the Material Bank's "B1 Pre-intermediate/_NEW BOOKLET STYLE/
digital source/"), the one-page tables unwrapped, Uzbek goals, instruction lines
and explanations.

The key (his P02AC ANSWER KEY) is written with variants.ok: every box that marks
itself takes every form of the right answer - short and full forms, figures and
words, with or without "a / the", British and American spelling - because he
found right answers marked wrong (2026-10-02). Where the form IS the point - the
spelling task 3.4, the past forms in 2.1 - only that form counts. Where a right
answer can be worded too many ways to list (2.2's two sentences, 2.8's
sentences with ago, 6.2's "which two numbers"), the box is his to read, not the
computer's.

What a phone gets that paper does not:
  - taps: the paragraph (1.2), TRUE / FALSE / NOT GIVEN (1.3), the ending /t/,
    /d/ or /ɪd/ (2.7 - on paper "tick the four with an extra syllable"), the
    matching letter (5.2), the checks before sending the recording (6.1);
  - a box per item where paper has ruled lines;
  - 2.6: the mistake as found (not marked), then the correction (marked).
5.5 (where words join) has no box: it is listening and saying aloud.

    python3 handouts/p02ac_new_digital.py       # writes handouts/p02ac_new.json, lists every box
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import (Handout, Q, choose, tick, own, write, report,   # noqa: E402
                     plain, told, bh_section_at, ITEM_STYLE, NUM_SPAN, TEXT_SPAN)
from variants import ok   # noqa: E402

DOCX = ("~/Documents/Claude/Material Bank/General English/B1 Pre-intermediate/_NEW BOOKLET STYLE/digital source/"
        "P02AC Travel and tourism — BOOKLET (teal, for the website).docx")
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


def section(label):
    return h.html.index("%s  </span>" % label)


def reword(label, old, new):
    at = section(label) + len("%s  </span>" % label)
    end = h.html.index("</p>", at)
    said = re.sub(r"\s+([.,!?)])", r"\1", plain(h.html[at:end]))   # Word splits runs before a full stop
    if said != old:
        raise SystemExit("%s says %r" % (label, said))
    style = re.match(r'<span( style="[^"]*")?>', h.html[at:end])
    h.html = h.html[:at] + "<span%s>%s</span>" % (style.group(1) or "", told(new, bare=True)) + h.html[end:]


def exact(*forms):
    """Only these forms (and their case) - for a task about the form itself."""
    return "/".join(forms)


# ------------------------------------------------------------ 1 Reading
for n in range(1, 7):
    h.item_box("1.2", n, where="leader")
for n in range(1, 8):
    h.item_box("1.3", n, where="leader")
h.leaders("1.5", "Grammar  ·", [(1, W, "Two ideas")])

# ------------------------------------------------------------ 2 Grammar
h.leaders("2.2", "2.3  </span>", [(n, W, "Two sentences: the truth") for n in range(1, 4)])
h.leaders("2.4", "2.5  </span>", [(n, W, "Your question") for n in range(1, 8)])
h.leaders("2.5", "2.6  </span>", [(1, W, "Your answer, in the past simple")])
reword("2.7", "Pronunciation. Listen to track 2.05 and track 2.06. Which verbs have an extra syllable, /ɪd/? "
              "Tick (✓) FOUR. Then complete the rule.",
       "Pronunciation. Listen to **track 2.05** and **track 2.06**. Which ending do you hear: **/t/**, **/d/** or "
       "**/ɪd/** (an extra syllable)? Tap it. Then read the rule.")
# the rule's two gaps are only dots on paper; on the phone it is read after the taps, so it says the answer
_at = h.html.index("2.7  </span>")
_r = h.html.index("/…/ and /…/", _at)
h.html = h.html[:_r] + "/t/ and /d/" + h.html[_r + len("/…/ and /…/"):]
h.leaders("2.8", "2.9  </span>", [(n, W, "Your sentence with ago") for n in range(1, 4)])
h.leaders("2.9", "Vocabulary  ·", [(1, W, "Four sentences about your last trip")])

# ------------------------------------------------------------ 3 Vocabulary
h.leaders("3.7", "Listening  ·", [(1, W, "Two sentences with a reason")])

# ------------------------------------------------------------ 4 Listening
h.leaders("4.4", "Everyday English  ·", [(1, W, "What he said, and why")])

# ------------------------------------------------------ 5 Everyday English
for n in range(1, 10):
    h.item_box("5.1", n, width="220px", where="leader")
h.leaders("5.3", "5.4  </span>", [(n, W, "Could you tell me …?") for n in range(1, 5)])
h.leaders("5.4", "5.5  </span>", [(1, W, "Why she runs back, and what she needs to do")])
reword("5.5", "Connected speech. When a word ends in a consonant sound and the next starts with a vowel sound, "
              "they join: Is‿anyone sitting here? Mark the joins (‿). Then listen to track 2.21 and say the questions.",
       "Connected speech. When a word ends in a consonant sound and the next starts with a vowel sound, they join: "
       "*Is‿anyone sitting here?* Find the joins, then listen to **track 2.21** and say the questions.")
h.leaders("5.6", "Speaking and writing  ·", [(1, W, "Your conversation")])

# ------------------------------------------------- 6 Speaking and writing
h.leaders("6.3", "</div>", [(1, W, "Describe the table here")])

# ------------------------------- every instruction, once more, in Uzbek
for label, text in [
        ("1.1", "Oʻqishdan oldin. Eng uzoq safaringiz qaysi edi? Qayerga va qanday bordingiz?"),
        ("1.2", "Bu maʼlumot qaysi xatboshida (*A–F*)? Bitta harf ikki marta ishlatiladi."),
        ("1.3", "Gaplar matnga mos keladimi? *TRUE* (toʻgʻri), *FALSE* (notoʻgʻri) yoki *NOT GIVEN* (matnda bu haqda "
                "hech narsa yoʻq) ni tanlang."),
        ("1.4", "Jadvalni toʻldiring. Matndan IKKI SOʻZDAN KOʻP BOʻLMAGAN soʻz va/yoki son yozing."),
        ("1.5", "Dalil haqida oʻylang. Baʼzi tarixchilar Ibn Battuta kitobidagi har bir joyga bormagan deb hisoblaydi. "
                "Ular buni qanday tekshirishi mumkin? Ikkita fikr yozing."),
        ("2.1", "Past Simple shaklini yozing."),
        ("2.2", "Matn haqidagi gaplar notoʻgʻri. Haqiqatni yozing: bitta inkor va bitta tasdiq gap."),
        ("2.3", "Dilshod oilaviy safar haqida yozmoqda. Matnni qavsdagi feʼllarning Past Simple shakli bilan "
                "toʻldiring."),
        ("2.4", "Kamola oʻtgan oy Samarqandga bordi. Savollarni yozing. Uning javoblari yordam beradi."),
        ("2.5", "Oʻylang. Matndagi uchta safardan qaysi biri eng qiyin boʻlgan deb oʻylaysiz? Past Simple da ikkita "
                "sabab keltiring."),
        ("2.6", "Bekzodning xabarida BESHTA xato bor. Avval xatoni, keyin toʻgʻrisini yozing."),
        ("2.7", "Talaffuz. 2.05 va 2.06-treklarni tinglang. Qaysi oxirni eshitasiz: */t/*, */d/* yoki */ɪd/* "
                "(qoʻshimcha boʻgʻin)? Tanlang. Keyin qoidani oʻqing."),
        ("2.8", "Qancha vaqt oldin? Hozir 2026-yil. Har biri haqida *ago* bilan gap yozing."),
        ("2.9", "Endi siz. Oxirgi safaringiz yoki taʼtilingiz haqida yozing: ikkita tasdiq gap, bitta inkor gap va "
                "*was* yoki *were* bilan bitta gap."),
        ("3.1", "Javohirning postini oʻqing. Qalin yozilgan iboralarga qarang. Toshkentdan ketishdan oldin nima "
                "qilishdi? Uchta narsani yozing."),
        ("3.2", "Har bir guruhga qaysi feʼl mos keladi? *book, buy, check, do, exchange, get, go, have, pack* yoki "
                "*stay* ni yozing."),
        ("3.3", "Bu nima? Ramkadagi soʻzni yozing."),
        ("3.4", "Imlo. Bu soʻzlar koʻpincha notoʻgʻri yoziladi. Har birini toʻgʻri yozing."),
        ("3.5", "Har bir gapni KATTA harflar bilan yozilgan soʻzning toʻgʻri shakli bilan toʻldiring."),
        ("3.6", "*trip*, *journey* yoki *travel*? *A trip* — borib-qaytish; *a journey* — yoʻldagi vaqt; *travel* — "
                "sayohat qilish faoliyati."),
        ("3.7", "Oʻylang. Taʼtilda nima muhimroq: qulaylikmi yoki sarguzashtmi? Sabab bilan ikkita gap yozing."),
        ("4.1", "3-kun (2.01-trek). Qaydlarni toʻldiring. IKKI SOʻZ VA/YOKI SONDAN KOʻP yozmang."),
        ("4.2", "7-kun (2.02-trek). Jadvalni toʻldiring. IKKI SOʻZ VA/YOKI SONDAN KOʻP yozmang."),
        ("4.3", "Richardning gaplarini Past Simple bilan toʻldiring. Keyin tekshirish uchun yana tinglang."),
        ("4.4", "Oʻylang. Soat 23:55 da yangi doʻstlari: «Biz bilan Tailandga borasanmi?» deb soʻrashdi. Richard nima "
                "deb javob berdi, sizningcha? Nega?"),
        ("5.1", "1-qism (2.16-trek). Savollarga javob bering. UCH SOʻZ VA/YOKI SONDAN KOʻP yozmang."),
        ("5.2", "Boshlanishlarni (*1–6*) oxirlar (*a–f*) bilan moslang. Tekshirish uchun 2.17-trekni tinglang."),
        ("5.3", "Savollarni xushmuomalaroq qiling. *Could you tell me …?* bilan boshlang."),
        ("5.4", "2-qism (2.23-trek). Enni nega orqaga yuguradi? Endi u nima qilishi kerak?"),
        ("5.5", "Bogʻlangan nutq. Soʻz undosh tovush bilan tugab, keyingisi unli tovush bilan boshlansa, ular "
                "qoʻshilib aytiladi. Qoʻshilish joylarini toping, keyin 2.21-trekni tinglab, savollarni ayting."),
        ("5.6", "Siz Toshkent vokzalidagi maʼlumot byurosidasiz. Suhbatni yozing (6–8 qator): Tushuntirishdagi uchta "
                "savolni bering, keyin toʻrtinchisi uchun *Sorry, just one more thing* yoki *Actually, there is one "
                "more thing* dan foydalaning."),
        ("6.1", "Har bir band uchun qayd yozing. Keyin oʻzingizni yozib oling: Past Simple da taxminan bir daqiqa "
                "gapiring va yozuvni oʻqituvchingizga yuboring."),
        ("6.2", "Matningiz uchun jadvalga qarang. Savollarga qisqa qayd shaklida javob bering."),
        ("6.3", "6.2 dagi jadvalni tasvirlang (80–100 soʻz). Namunadagidek boshlang, eng mashhur va eng kam mashhur "
                "joylarni ayting, sonlardan foydalaning va oʻz sababingiz bilan tugating. Past Simple ishlating.")]:
    h.say_also(label, text)

# ------------------------------------------ the explanations, told in Uzbek
h.retell("KEY WORDS", "KALIT SOʻZLAR", [
    "**a journey**  safar, yoʻl — bir joydan boshqa joyga borish",
    "**to set off**  yoʻlga chiqmoq",
    "**a novel**  roman — hikoyali uzun kitob",
    "**a package holiday**  yoʻl va mehmonxona birga sotiladigan dam olish",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — PAST SIMPLE", [          # the first of the two
    "[[A]] **Tasdiq.** Toʻgʻri feʼllarga **-ed** qoʻshiladi: *visit → visited · arrive → arrived*. Koʻp ishlatiladigan "
    "feʼllarning aksariyati **notoʻgʻri**: *go → went · take → took · buy → bought · leave → left · fly → flew*.",
    "[[B]] **Inkor va soʻroq** — **did / didn't + feʼlning oddiy shakli**: *He didn't come home for 24 years. · Did "
    "you have a good time? — Yes, I did. / No, I didn't. · Where did you go?*",
    "[[C]] **was / were** bilan *did* ishlatilmaydi: *The trip was a success. · We weren't tired. · Were you late?* "
    "**Vaqt soʻzlari:** *yesterday · last summer · in 1889 · two years ago* — **ago** vaqtdan keyin keladi.",
    "[[D]] **Istisnolar.** *did / didn't* dan keyin feʼl **oddiy shaklga** qaytadi: *Did you go?* — *Did you went?* "
    "emas. **Imlo:** *stop → stopped · plan → planned · travel → travelled* (harf ikkilanadi) · *study → studied*, "
    "lekin *play → played*.",
])
h.retell("WATCH OUT!", "DIQQAT — KOʻP UCHRAYDIGAN XATOLAR", [
    "1 ✗ *I didn't went to Khiva.* → ✓ *I didn't go …* — *didn't* + oddiy shakl.",
    "2 ✗ *Did you saw the Registan?* → ✓ *Did you see …?*",
    "3 ✗ *Where you went last summer?* → ✓ *Where did you go …?* — egadan oldin *did*.",
    "4 ✗ *We was very tired.* → ✓ *We were …* · ✗ *I buyed a hat.* → ✓ *I bought …*",
    "5 ✗ *I went there before two years.* → ✓ *two years ago*",
])
h.retell("WORD FAMILIES", "SOʻZ OILALARI", [
    "**travel** → *a traveller* (sayyoh) · *travelling* (Britaniya inglizchasida *-ll-*) · **tour** → *a tourist* · "
    "*tourism* · **visit** → *a visitor*",
    "**adventure** → *adventurous* (sarguzashtni yaxshi koʻradigan) · **luxury** → *luxurious* (hashamatli) · "
    "**pack** → *unpack* · **organise** → *an organisation*",
])
h.retell("ERROR WARNING", "DIQQAT — SAFAR SOʻZLARIDAGI XATOLAR", [
    "✗ *We made a travel to Khiva.* → ✓ *a trip* · ✗ *The travel took six hours.* → ✓ *The journey*",
    "✗ *We arrived to Bukhara at night.* → ✓ *arrived in* · ✗ *I went to abroad.* → ✓ *went abroad*",
    "✗ *We visited to my grandparents.* → ✓ *visited my grandparents* — *to* kerak emas",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [                 # the first of the two
    "Darslikda (2A dars) Richard Gretsiyadagi taʼtilda bir hafta davomida har bir savolga «ha» deb javob berdi. "
    "**2.01-trek**ni (3-kun) va **2.02-trek**ni (7-kun) tinglang.",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — MAʼLUMOT SOʻRASH", [
    "[[A]] **Maʼlumot soʻrash:** *What time's the next train? · How often do the trains leave? · Which platform does "
    "it leave from? · How much is a ticket? · Can I pay by card? · Where can I buy a magazine?*",
    "[[B]] **Sizga yordam beradigan odam:** *How can I help you? · Is there anything else I can help you with?* "
    "**Yana soʻrash:** *Sorry, just one more thing. · Actually, there is one more thing.*",
    "[[C]] **Xushmuomalaroq:** *Could you tell me where the ticket office is?* *Could you tell me …* dan keyin soʻz "
    "tartibi savoldagidek **emas**: *where the ticket office is* — *where is the ticket office* emas.",
    "[[D]] **Istisno.** *do / does / did* ham tushib qoladi: *What time does the museum open?* → *Could you tell me "
    "what time the museum opens?*",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [
    "Enni (1-unitdan) Britaniyadagi katta vokzalda. **2.16-trek**ni tinglang (1-qism). Keyin bir narsa notoʻgʻri "
    "ketadi: **2.23-trek**ni tinglang (2-qism). Darslik, 2-unit, 2C dars.",
])

# --------------------- the goals, in Uzbek, where the site's cover reads them
GOALS = [
    "buyuk sayohatchilar haqidagi matnni tushunishni",
    "Past Simple ni toʻgʻri ishlatishni: toʻgʻri va notoʻgʻri feʼllar, *did / didn't*, *was / were*, *ago*",
    "*-ed* oxirini toʻgʻri talaffuz qilishni: /t/, /d/, /ɪd/",
    "turizm soʻzlarini va *trip / journey / travel* farqini",
    "vokzal yoki muzeyda xushmuomalalik bilan maʼlumot soʻrashni",
    "oddiy jadvalni soʻz bilan tasvirlashni",
]
first_bar = bh_section_at().search(h.html).start()
h.html = (h.html[:first_bar] + '<table class="bk"><tr><td><p><span>You will learn to</span></p>'
          + "".join('<p><span>—  </span>%s</p>' % told(g, bare=True) for g in GOALS)
          + "</td></tr></table>" + h.html[first_bar:])

# ------------------------------------------------------------------ the key
K = {}
TFNG = ["TRUE", "FALSE", "NOT GIVEN"]
K[("1.1", 1, 1)] = own()
for n, a in enumerate("DBECBD", 1):
    K[("1.2", n, 1)] = choose(list("ABCDEF"), a)
for n, a in enumerate(["FALSE", "TRUE", "FALSE", "NOT GIVEN", "FALSE", "NOT GIVEN", "TRUE"], 1):
    K[("1.3", n, 1)] = choose(TFNG, a)
for n, a in enumerate([ok("Tangier", "Tangiers", "Tangier in Morocco"),
                       ok("24", "24 years", numbers=True),
                       ok("1841", "in 1841"),
                       ok("Loughborough"),
                       ok("world", articles=True),
                       ok("train", "trains", "by train", "train too"),
                       ok("72", "72 days", numbers=True)], 1):
    K[("1.4", n, 1)] = Q(a)
K[("1.5", 1, 1)] = own()

# 2.1 is about the past form itself: only that form, with its American spelling where there is one
for n, a in enumerate([exact("travelled", "traveled"), "stopped", "tried", "planned", "stayed",
                       "left", "flew", "caught", "spent", "brought"], 1):
    K[("2.1", n, 1)] = Q(a)
for n in range(1, 4):                             # two sentences each, many right wordings: his to read
    K[("2.2", n, 1)] = own()
for n, a in enumerate(["went", "took", "was", ok("didn't mind"), "played", "ate", "stayed", "climbed", "saw",
                       "bought", ok("didn't wear"), ok("didn't want")], 1):
    K[("2.3", n, 1)] = Q(a)
for n, a in enumerate([ok("How did you travel", "How did you travel there", "How did you get there"),
                       ok("Where did you stay"),
                       ok("Was the weather good", "Was the weather good there", "Was the weather nice"),
                       ok("Did you buy any souvenirs", "Did you buy souvenirs", "Did you buy any souvenir"),
                       ok("What did you like most", "What did you like the most", "What did you like best",
                          "What did you like most there", "What did you like the most there"),
                       ok("Were the people friendly", "Were the people there friendly"),
                       ok("How long did you stay", "How long did you stay there", "How long did you stay in Samarkand")],
                      1):
    K[("2.4", n, 1)] = write(a)
K[("2.5", 1, 1)] = own()
FIXED = [ok("We were", "We were there", "We were there for three days"),
         ok("I didn't go", "didn't go", "I didn't go to the museum"),
         ok("I bought", "bought", "I bought a great hat"),
         ok("Did you see", "Did you see my photos"),
         ok("Where did you go", "Where did you go last weekend")]
for n, a in enumerate(FIXED, 1):
    K[("2.6", n, 1)] = None                       # the mistake as they found it: theirs, not marked
    K[("2.6", n, 2)] = write(a, control=None)
ENDINGS = ["/t/", "/d/", "/ɪd/"]
for n, a in enumerate(["/ɪd/", "/ɪd/", "/d/", "/t/", "/t/", "/ɪd/", "/d/", "/t/", "/ɪd/", "/d/"], 1):
    K[("2.7", n, 1)] = choose(ENDINGS, a)
for n in range(1, 4):                             # sentences with ago: many right wordings, his to read
    K[("2.8", n, 1)] = own()
K[("2.9", 1, 1)] = own()

K[("3.1", 1, 1)] = own()                          # three things they did before they left: a list in any order
for n, forms in enumerate([("get", "got"), ("book", "booked"), ("exchange", "exchanged"), ("pack", "packed"),
                           ("check", "checked"), ("do", "did"), ("buy", "bought"), ("stay", "stayed"),
                           ("have", "had"), ("go", "went")], 1):
    K[("3.2", n, 1)] = Q(exact(*forms))
for n, a in enumerate([ok("passport", "passports", articles=True),
                       ok("guidebook", "guide book", "guide-book", articles=True),
                       ok("suntan lotion", "sun tan lotion", "suntan cream", "sun cream", articles=True),
                       ok("foreign currency", "currency", articles=True),
                       ok("backpack", "back pack", "rucksack", articles=True),
                       ok("suitcase", "suit case", articles=True),
                       ok("sunglasses", "sun glasses", articles=True),
                       ok("map", articles=True)], 1):
    K[("3.3", n, 1)] = Q(a)
for n, a in enumerate(["accommodation", "sightseeing", "souvenirs", "adventure", "luggage", "currency"], 1):
    K[("3.4", n, 1)] = Q(a)                       # a spelling task: the one spelling
for n, a in enumerate([ok("traveller"), "tourists", "adventurous", "luxurious", "Tourism"], 1):
    K[("3.5", n, 1)] = Q(a)
for n, a in enumerate(["trip", "journey", "travel", exact("journey", "trip")], 1):
    K[("3.6", n, 1)] = Q(a)
K[("3.7", 1, 1)] = own()

for n, a in enumerate([ok("an hour", "one hour", "1 hour", "hour", "about an hour", "about one hour", numbers=True),
                       ok("five", "5", "five people", "5 people"),
                       ok("sick", "very sick", "really sick", "worried", "really worried", "very worried"),
                       ok("fell over", "fell", "fell down", "fell off", "he fell over", "he fell"),
                       ok("ten", "10")], 1):
    K[("4.1", n, 1)] = Q(a)
for n, a in enumerate([ok("waiter", articles=True),
                       ok("fishermen", "fisherman", "fishers"),
                       ok("six", "6", "six in the morning", "6 in the morning", "six o'clock", "6 o'clock",
                          "6 am", "6 a.m.", "six am", "six a.m.", "6:00", "06:00", "6.00"),
                       ok("dancing", "dance", "a dancing"),
                       ok("boat trip", "boat trips", "same boat trip", "boat"),
                       ok("mosquitoes", "mosquitos", "the mosquitoes", "the mosquitos", "mosquito"),
                       ok("200 euros", "€200", "200 euro", "200", "two hundred euros", "200€", "over 200 euros",
                          "euro 200", "EUR 200", "200 EUR")], 1):
    K[("4.2", n, 1)] = Q(a)
for n, a in enumerate(["caught", ok("didn't get"), "made", "bit", "fell", "took"], 1):
    K[("4.3", n, 1)] = Q(a)
K[("4.4", 1, 1)] = own()

for n, a in enumerate([ok("her brother", "brother", "my brother", "his brother", "her brother Dan", "Dan",
                          "she is going to visit her brother", "to visit her brother", "visit her brother"),
                       ok("in four minutes", "four minutes", "4 minutes", "in 4 minutes", "in four mins",
                          "in 4 mins", "4 mins", "four mins", "in four minutes' time"),
                       ok("every 30 minutes", "30 minutes", "every thirty minutes", "thirty minutes",
                          "every half hour", "every half an hour", "half an hour", "twice an hour",
                          "every 30 mins", "30 mins", "two times an hour"),
                       ok("12", "twelve", "platform 12", "platform twelve", "from platform 12",
                          "from platform twelve", "No 12", "number 12"),
                       ok("Sunday", "on Sunday", "next Sunday", "she's coming back on Sunday"),
                       ok("from the employee", "the employee", "from him", "him", "from the man", "the man",
                          "from the assistant", "the assistant", "from the worker", "the worker",
                          "from the station employee", "the station employee", "from the staff", "from a worker",
                          "the employee sells it", "he can sell it", "from the station worker",
                          "from the employee there"),
                       ok("£26.30", "26.30", "26.30 pounds", "£26,30", "26,30", "26 pounds 30", "26 pounds 30 pence",
                          "twenty-six pounds thirty", "twenty six pounds thirty", "26.30 £", "£ 26.30",
                          "26 pounds and 30 pence", "26.3 pounds", "£26.3"),
                       ok("a magazine", "magazine", "magazines", "some magazines", "a magazine to read"),
                       ok("never very good", "not very good", "not good", "never good", "bad", "boring",
                          "they're never very good", "they're not very good", "his parties are never very good",
                          "never very good parties", "not very good parties", "they aren't very good",
                          "they are not good", "not so good")], 1):
    K[("5.1", n, 1)] = Q(a)
for n, a in enumerate("dfcabe", 1):
    K[("5.2", n, 1)] = choose(list("abcdef"), a)


def polite(*cores):
    forms = []
    for c in cores:
        for start in ("Could you tell me", "Excuse me, could you tell me", "Could you please tell me",
                      "Excuse me, could you please tell me"):
            for end in ("", ", please", " please"):
                forms.append("%s %s%s" % (start, c, end))
    return ok(*forms, limit=400)


for n, a in enumerate([polite("where the ticket office is"),
                       polite("what time the museum opens", "when the museum opens"),
                       polite("how much a ticket to Bukhara costs", "how much a ticket to Bukhara is",
                              "how much the ticket to Bukhara costs", "how much the ticket to Bukhara is",
                              "how much it costs to go to Bukhara"),
                       polite("which platform the Samarkand train leaves from",
                              "from which platform the Samarkand train leaves",
                              "which platform the train to Samarkand leaves from",
                              "what platform the Samarkand train leaves from")], 1):
    K[("5.3", n, 1)] = write(a)
K[("5.4", 1, 1)] = own()
K[("5.6", 1, 1)] = own(control="essay")

for n in range(1, 4):                             # notes, not sentences
    K[("6.1", n, 1)] = None
for n in range(4, 7):                             # the three checks before sending the recording
    K[("6.1", n, 1)] = tick()
K[("6.2", 1, 1)] = Q(ok("Samarkand", "Samarkand (12)", "Samarkand 12", "Samarkand, 12", "Samarkand with 12",
                        "Samarkand - 12", "Samarkand — 12"))
K[("6.2", 2, 1)] = Q(ok("abroad", "abroad (4)", "abroad 4", "abroad, 4", "going abroad", "go abroad",
                        "travelling abroad", "abroad - 4", "abroad — 4", "abroad with 4"))
K[("6.2", 3, 1)] = None                           # "Bukhara or Khiva and stayed at home", "7 and 7"... his to read
K[("6.2", 4, 1)] = None
K[("6.3", 1, 1)] = own(control="essay")

if __name__ == "__main__":
    data = h.build(K, "Pre-Intermediate", 2, "Unit 2A & 2C — Travel and tourism")
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "p02ac_new.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
