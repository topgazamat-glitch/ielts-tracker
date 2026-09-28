"""B03B Food and drink - Azamat's Beginner booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(B03B Food and drink - ANSWER KEY), joined box by box by hand.

At this level most students cannot read an explanation in English, so every
box that explains - the grammar, the warnings, the pronunciation, the key
words, the checklist and what the booklet teaches - is told again in Uzbek.
The English examples inside them stay English: they are what is learned.
The reading text and the exercises stay English too.

What a phone gets that paper does not:
  - taps for every choice: country, T/F, at/in, a/an/-, meals, sounds, the
    odd one out, the adverb heard, the name, What time/When;
  - one line per row for the survey tables, instead of loose boxes;
  - the class and pair tasks (surveys, a partner's answers) keep their boxes
    but never hold a part back: they are done in class.

    python3 handouts/b03b_digital.py            # writes handouts/b03b.json, lists every box
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import (Handout, Q, choose, tick, own, write, fix, pair, report,   # noqa: E402
                     plain, ITEM_P, BLANK_TAG)

DOCX = ("~/Documents/Claude/Material Bank/General English/A1 Beginner/_NEW BOOKLET STYLE/"
        "B03B Food and drink — BOOKLET.docx")
TF = ["T", "F"]
ITEM_STYLE = 'style="margin-bottom:3.5px;line-height:1.25;padding-left:35px"'
NUM_SPAN = '<span style="color:#6E6E6E;font-size:10.5pt">%d  </span>'
TEXT_SPAN = '<span style="color:#1A1A1A;font-size:11.5pt">%s</span>'

h = Handout(DOCX)
TAGS = {int(m.group(1)): m.group(0) for m in BLANK_TAG.finditer(h.html)}


def items(label):
    return [m for m in ITEM_P.finditer(h.html) if m.group(2) == label]


def clock(*forms):
    """A time, as it may be written: with or without It's."""
    out = []
    for f in forms:
        out += [f, "it's " + f, "it is " + f]
    return "/".join(out)


# ------------------------------------------------------------ 1 Reading
# 1.1: coffee [ ] tea [ ] ... - one food to a line, Yes / No to tap
h.one_per_line(TAGS[0], "KEY WORDS", at="text")
h.leaders("1.6", "PRESENTATION — TELLING THE TIME", [])   # the frame is the three sentences

# ------------------------------------------------------------ 2 Grammar
for n in range(2, 9):                            # 2.7: item 1 is the worked example
    h.item_box("2.7", n)
h.grid_rows("2.8", ["Person 1:", "Person 2:", "Person 3:"])
# 2.9: the clocks cannot be drawn on a phone; the times are written in words
head = h.html.index("2.9  </span>")
a = h.html.index('<table class="bk">', head)
b = h.html.index("</table>", a) + len("</table>")
TIMES = ["7.45", "12.30", "3.20", "9.05"]
rows29 = ""
for n, i in enumerate((74, 75, 76, 77), 1):
    h.blanks[i].update(label="2.9", num=n, text=TIMES[n - 1])
    rows29 += ('<p data-item="2.9:%d" %s>%s%s</p>'
               % (n, ITEM_STYLE, NUM_SPAN % n, TEXT_SPAN % ("%s  →  %s" % (TIMES[n - 1], TAGS[i]))))
h.html = h.html[:a] + rows29 + h.html[b:]

# ------------------------------------------------------------ 3 Vocabulary
# 3.4: each word with /ɑː/ or /ɔː/ to tap, in place of the word box and the
# empty two-column table
WORDS34 = ["class", "all", "father", "afternoon", "water", "daughter", "past", "four"]
head = h.html.index("3.4  </span>")
t1 = h.html.index("<table", head)
t2 = h.html.index("<table", h.html.index("</table>", t1))
end = h.html.index("</table>", t2) + len("</table>")
assert plain(h.html[t2:end]).startswith("/ɑː/"), plain(h.html[t2:end])[:40]


def word_cell(n):
    h.texts[("3.4", n)] = WORDS34[n - 1]
    return ('<td style="vertical-align:top;border-top:0;border-bottom:0;border-left:0;border-right:0">'
            '<p data-item="3.4:%d" %s>%s%s</p></td>'
            % (n, ITEM_STYLE, NUM_SPAN % n, TEXT_SPAN % ("%s  {{box:3.4:%d:60px:}}" % (WORDS34[n - 1], n))))


h.html = (h.html[:t1] + '<table class="bk">'
          + "".join("<tr>%s%s</tr>" % (word_cell(n), word_cell(n + 4)) for n in range(1, 5))
          + "</table>" + h.html[end:])
# 3.6: the four words are the choice - tap the odd one out, then say why
ODD = {}
for m in items("3.6"):
    ODD[int(m.group(3))] = [w.strip() for w in re.sub(r"^\d+\s+", "", plain(m.group(4))).split("·")]
for n in (1, 2, 3, 4):
    h.item_box("3.6", n)
    h.item_box("3.6", n, placeholder="Why? (Nega?)")
for m in reversed(items("3.6")):
    boxes = "".join(re.findall(r"\{\{box:[^}]*\}\}", m.group(4)))
    h.html = h.html[:m.start()] + m.group(1) + NUM_SPAN % int(m.group(3)) + boxes + "</p>" + h.html[m.end():]

# ------------------------------------------------------------ 4 Listening
h.grid_rows("4.2", ["Food:", "Dinner time:"])
h.grid_rows("4.5", [""])
h.leaders("4.6", "4.7  </span>", [(1, "95%", "Two sentences about you")])
for m in reversed(items("4.7")):                 # 1 ... at ...  →  2 ... at ...  : a line each
    guts = re.sub(r"\s*→\s*", "<br>", m.group(4))
    h.html = h.html[:m.start()] + m.group(1) + guts + "</p>" + h.html[m.end():]

# ------------------------------------------------------ 5 Speaking and writing
h.leaders("5.5", "CHECK BEFORE", [(20, "95%", "Write about your day in meals here")])
h.grid_rows("5.7", [""])
h.leaders("5.8", "5.9  </span>", [(1, "95%", "Three sentences about your survey")])
FACES, CAN_DO = h.can_do_grid("5.9")

# ------------------------------- every instruction, once more, in Uzbek
# Said the way the phone asks for it: where paper says "write T or F", the
# student taps, so the Uzbek says "tanlang" (choose).
INSTRUCTIONS = [
    ("1.1", "Nonushtangiz. Har bir ovqat uchun *Yes* (ha) yoki *No* (yoʻq) ni tanlang."),
    ("1.2", "Qaysi davlat? *Italy* (Italiya), *Turkey* (Turkiya) yoki *Japan* (Yaponiya) ni tanlang."),
    ("1.3", "Toʻgʻri (*T*) yoki notoʻgʻri (*F*)?"),
    ("1.4", "Gaplarni matndagi soʻz bilan toʻldiring."),
    ("1.5", "Qaysi nonushta sizniki bilan bir xil? Qaysi biri juda boshqacha? Sherigingizga aytib bering."),
    ("1.6", "Endi oʻz davlatingizdagi nonushta haqida uchta gap yozing."),
    ("2.1", "Vaqtni soʻz bilan yozing."),
    ("2.2", "Vaqtni raqam bilan yozing."),
    ("2.3", "*at* yoki *in* ni tanlang."),
    ("2.4", "*have* va qavs ichidagi ovqat nomi bilan toʻldiring."),
    ("2.5", "*What time* bilan savol yozing. Keyin oʻzingiz haqingizda javob bering."),
    ("2.6", "Qavs ichidagi ravishni toʻgʻri joyga qoʻyib, gapni toʻliq yozing."),
    ("2.7", "Xatoni topib, toʻgʻrilang. IKKITA gap toʻgʻri — ular uchun *✓ It is correct* tugmasini bosing."),
    ("2.8", "Uch kishidan soʻrang va vaqtlarni yozing. Buni sinfda bajarasiz."),
    ("2.9", "Vaqtni soʻz bilan yozing. Soatni daftaringizga chizsangiz ham boʻladi."),
    ("3.1", "Qaysi mahal? *Breakfast* (nonushta), *Lunch* (tushlik) yoki *Dinner* (kechki ovqat) ni "
            "tanlang. Baʼzilariga ikkita javob ham toʻgʻri — bittasini tanlang."),
    ("3.2", "Ovqat nomini yozing."),
    ("3.3", "*a*, *an* yoki hech narsa (*–*)? Tanlang."),
    ("3.4", "Har bir soʻzdagi tovushni tanlang: /ɑː/ (*half* dagi kabi) yoki /ɔː/ (*quarter* dagi kabi)."),
    ("3.5", "Bu vaqtlarni ovoz chiqarib ayting. Daftaringizda /ɑː/ ning tagiga chizing, /ɔː/ ni aylanaga oling."),
    ("3.6", "Qaysi soʻz boshqacha? Uni tanlang va nega ekanini yozing."),
    ("3.7", "Sherigingizga har bir mahalda nima yeyishingizni aytib bering."),
    ("4.1", "Bir marta tinglang. Har bir kishi qaysi davlatdan? Tanlang."),
    ("4.2", "Yana tinglang. Har bir kishi nima yeydi va soat nechada? Yozing."),
    ("4.3", "Yana bir marta tinglang. Eshitgan ravishingizni tanlang."),
    ("4.4", "Toʻgʻri (*T*) yoki notoʻgʻri (*F*)?"),
    ("4.5", "Endi siz. Sherigingizdan kechki ovqati haqida soʻrang. Buni sinfda bajarasiz."),
    ("4.6", "Julie, Lucas yoki Monica — kim sizga koʻproq oʻxshaydi? Ikkita gap yozing."),
    ("4.7", "Uchta kechki ovqatni vaqt boʻyicha tartiblang: eng ertasidan eng kechigacha."),
    ("5.1", "Namunani yana oʻqing va quyidagilarni toping."),
    ("5.2", "Oʻzingiz haqingizda toʻliq gaplar bilan javob bering."),
    ("5.3", "Beshta savolingizni boshqa oʻquvchilarga bering. Kimning javoblari sizniki bilan bir xil?"),
    ("5.4", "*What time* yoki *When* ni tanlang. Baʼzan ikkalasi ham toʻgʻri."),
    ("5.6", "Sherigingiz bilan matn almashing. Uning matnini oʻqib, toʻldiring. Buni sinfda bajarasiz."),
    ("5.7", "Sinf soʻrovi. Har bir gap uchun bitta odam toping va ismini yozing. Buni sinfda bajarasiz."),
    ("5.8", "Sinfga natijani aytib bering. Soʻrovingiz haqida uchta gap yozing."),
    ("5.9", "Butun darsni eslang. Har bir ish uchun qanchalik qila olishingizni tanlang."),
]
for label, text in INSTRUCTIONS:
    h.say_also(label, text)
h.say_also("5.5", "Kuningiz haqida ovqatlar orqali yozing (50–60 soʻz), namunadagi tuzilishda. "
           "Unda boʻlsin: uch mahal ovqat · uchta aniq vaqt · ikkita chastota ravishi · "
           "*in the morning / evening* · *at the weekend*.", after="Include:")

# ------------------------------------------ the explanations, told in Uzbek
h.goals([
    "soatni *o'clock*, *past* va *to* bilan aytishni",
    "nonushta, tushlik va kechki ovqatni qachon qilishingizni aytishni (*the* qoʻyilmaydi)",
    "vaqt uchun *at*, kunning qismi uchun *in* ishlatishni va *at night* ni eslab qolishni",
    "*What time do you…?* va *When…?* deb soʻrashni",
    "3A dagi chastota ravishlarini (*always, usually, sometimes, never*) vaqt bilan birga ishlatishni",
    "yana oʻn ikkita ovqat nomini va *half past four* dagi /ɑː/ va /ɔː/ tovushlarini",
])
h.retell("KEY WORDS", "KALIT SOʻZLAR", [
    "**number one**  eng mashhur, birinchi oʻrinda",
    "**a pastry**  kichkina shirin pishiriq, koʻpincha mevali",
    "**cereal**  makkajoʻxori yoki bugʻdoy donachalari, sut bilan yeyiladi",
    "**late**  kech (erta emas)",
])
h.retell("PRESENTATION — TELLING THE TIME", "TUSHUNTIRISH — SOATNI AYTISH", [
    "Hamma ishni ikki soʻz bajaradi: **PAST** va **TO**. Yarim soatgacha soatdan necha daqiqa "
    "*oʻtganini* aytasiz (*past*). Yarim soatdan keyin keyingi soatgacha necha daqiqa *qolganini* "
    "aytasiz (*to*).",
    "[[PAST]] *2.00 two o'clock · 2.15 (a) quarter past two · 2.20 twenty past two · 2.30 half past two*",
    "[[TO]] *2.40 twenty to three · 2.45 (a) quarter to three · 2.55 five to three*",
    "**Uchta narsani eslab qoling.** *o'clock* faqat aniq soat uchun — ✗ *half past two o'clock* "
    "deyilmaydi. · *half* doim *past* bilan keladi, hech qachon *to* bilan emas. · *to* dan keyin "
    "soat bittaga oshadi: 2.45 — *a quarter to three*.",
    "**Oson yoʻl ham toʻgʻri.** *Two fifteen. Two thirty. Two forty-five.* Avval soatni, keyin "
    "daqiqani ayting — hamma tushunadi. Lekin *past* va *to* ni eshitib tushunishingiz kerak, "
    "chunki inglizlar aynan shunday gapiradi.",
])
h.retell("PRESENTATION — WHEN YOU EAT", "TUSHUNTIRISH — QACHON OVQATLANAMIZ", [
    "[[OVQAT]] Ovqat nomlari oldidan **THE** qoʻyilmaydi. *I have breakfast at seven. · We have lunch "
    "at one. · They have dinner late.* ✗ *I have the breakfast* deyilmaydi.",
    "[[AT]] **AT** + aniq vaqt: *at seven o'clock · at half past twelve · at night · at the weekend*",
    "[[IN]] **IN** + kunning qismi: *in the morning · in the afternoon · in the evening* — lekin "
    "*at night*. Bu yagona istisno, uni shunchaki yodlab oling.",
    "[[SAVOL]] Savol **WHAT TIME** yoki **WHEN** bilan boshlanadi. *What time do you have lunch?* = "
    "*When do you have lunch?* Savol bir xil, javob ham bir xil: *At one.*",
    "[[3A DAN]] Bularni 3A dan bilasiz: *I usually have lunch at one. · We never have dinner before "
    "eight.* Chastota ravishi doimgidek *have* dan oldin keladi. Yangi narsa bitta: endi u vaqt "
    "bilan birga ishlatiladi.",
])
h.retell("ERROR WARNING", "DIQQAT — KOʻP UCHRAYDIGAN XATOLAR", [
    "1 **Ovqat nomi oldidan artikl qoʻyilmaydi.** ✗ *I have the dinner at eight.* → ✓ *I have dinner "
    "at eight.*",
    "2 **Aniq vaqt uchun AT, kunning qismi uchun IN.** ✗ *in seven o'clock* → ✓ *at seven o'clock*. "
    "✗ *at the morning* → ✓ *in the morning*.",
    "3 **Daqiqa aytilsa, o'clock ishlatilmaydi.** ✗ *half past seven o'clock* → ✓ *half past seven*.",
    "4 **Savolga DO kerak.** ✗ *What time you have lunch?* → ✓ *What time do you have lunch?*",
    "5 **Ovqat nomi bilan eat emas, have ishlatiladi.** *I eat rice* ✓, lekin *I have lunch* — "
    "*eat lunch* ham mumkin, ammo odamlar *have lunch* deydi.",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — OVQAT NOMLARI", [
    "[[OVQATLAR]] *breakfast* — nonushta (ertalab) · *lunch* — tushlik (kun oʻrtasida) · "
    "*dinner* — kechki ovqat (kechqurun)",
    "[[YANGI]] *an orange · a sandwich · butter · a biscuit · a banana · a pizza · a potato · "
    "a tomato · an apple · ice cream · cheese · a cake*",
    "[[MATNDAN]] *a pastry · cereal · toast · jam · soup*",
    "**Qaysilari A oladi?** Agar sanash mumkin boʻlsa — *an apple, two apples* — oldidan *a* yoki "
    "*an* qoʻyiladi. Sanab boʻlmasa — *butter, cheese, jam, ice cream* — *a* qoʻyilmaydi: "
    "*I have some cheese*, ✗ *a cheese* emas.",
])
h.retell("PRONUNCIATION — /Ɑː/ AND /Ɔː/", "TALAFFUZ — /ɑː/ VA /ɔː/", [
    "Ikkita choʻziq tovush — ikkalasi ham hozir oʻrgangan vaqtlaringizda bor.",
    "[[/ɑː/]] ogʻzingizni keng oching — *past · half · class · father · afternoon*",
    "[[/ɔː/]] lablaringizni yumaloq qiling — *four · quarter · all · water · daughter*",
    "**Nega bu muhim:** *half past four* da ikkalasi ham bor — /hɑːf pɑːst fɔː/. Keng, keng, "
    "yumaloq. Agar *half* ni yumaloq lab bilan aytsangiz, u *hoff* boʻlib eshitiladi va hech kim "
    "soat necha ekanini tushunmaydi.",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [
    "Uch kishi — Julie, Lucas va Monica — kechki ovqat haqida gapiradi. Har biri boshqa davlatdan. "
    "**Qayerdan**, **nima yeyishi** va **soat nechada** ekaniga quloq soling.",
    "Agar sinfingizda audio boʻlsa, bu 3.12-trek. Boʻlmasa, oʻqituvchingiz matnni oʻqib beradi — "
    "topshiriqlar bir xil.",
])
h.retell("WHY YOU DIDN'T HEAR IT", "NEGA ESHITMADINGIZ?", [
    "**Vaqtlar tez aytiladi, past va to esa juda ohista aytiladi.** *Half past six* — /hɑːf pɑːs sɪks/: "
    "*past* dagi t tovushi *six* dagi s ga qoʻshilib ketadi. Avval soatni tinglang — u baland "
    "aytiladi. Keyin *past* yoki *to* ekanini aniqlang.",
    "**Ravish feʼldan balandroq aytiladi.** *We USUally have rice* — chastota soʻzi urgʻu oladi, "
    "chunki u yangi maʼlumot. Shuning uchun 4.3 ni bajara olasiz.",
])
h.retell("PRESENTATION — A DAY IN FIVE SENTENCES", "TUSHUNTIRISH — BESH GAPDA BIR KUN", [
    "Ovqatlaringiz haqidagi qisqa matnning oʻz tuzilishi bor: **avval vaqt, keyin qaysi mahal "
    "ovqat (nonushta, tushlik yoki kechki ovqat), keyin nima yeyishingiz.** Soʻng navbatdagisi.",
    "[[NAMUNA]] *In the morning, I have breakfast at half past seven. I usually have bread, cheese "
    "and tea. At one o'clock I have lunch at work — a sandwich and an apple. In the evening, we "
    "have dinner together at about eight. We always have rice. At the weekend, breakfast is late — "
    "sometimes at ten!*",
    "**Nima uchun yaxshi chiqqan:** koʻp gaplar vaqt soʻzi bilan boshlanadi · *have* + ovqat, "
    "*the* qoʻyilmaydi · deyarli har gapda bitta chastota ravishi · vaqt uchun *at*, kunning qismi uchun *in*.",
])
h.retell("LANGUAGE PLUS — WHAT TIME…? AND WHEN…?", "QOʻSHIMCHA — WHAT TIME…? VA WHEN…?", [
    "Ikkalasi bir narsani soʻraydi: *What time do you have dinner?* = *When do you have dinner?*",
    "**Lekin javoblar farq qilishi mumkin.** *What time* aniq soatni kutadi: *At eight.* *When* "
    "har qanday javobni qabul qiladi: *At eight / In the evening / After work / Late.* Demak, aniq "
    "soatni bilmoqchi boʻlsangiz, *what time* deb soʻrang.",
])
h.retell("CHECK BEFORE YOU GIVE IT IN", "TOPSHIRISHDAN OLDIN TEKSHIRING", [
    "{box}  *have* + ovqat nomi, *the* qoʻyilmaydi.   {box}  *at* + vaqt, *in* + kunning qismi, *at night*.",
    "{box}  Ravishlar *have* dan oldin.   {box}  Daqiqa bilan *o'clock* yoʻq.",
    "{box}  Uchta vaqt soʻz bilan yozilgan.   {box}  Soʻzlar soni: {box}",
])
h.one_per_line("TOPSHIRISHDAN OLDIN TEKSHIRING", "5.6  </span>", at="box")

# ------------------------------------------------------------------ the key
K = {}
for n in range(1, 8):                            # 1.1 your breakfast: yours to say
    K[("1.1", n, 1)] = choose(["Yes", "No"])
COUNTRY = {"I": "Italy", "T": "Turkey", "J": "Japan"}
for n, a in enumerate("JITIJT", 1):
    K[("1.2", n, 1)] = choose(["I", "T", "J"], a, labels=COUNTRY)
for n, a in enumerate("FTFFTF", 1):
    K[("1.3", n, 1)] = choose(TF, a)
for n, a in enumerate(["pastry/a pastry", "standing", "slow", "tea", "soup"], 1):
    K[("1.4", n, 1)] = Q(a)
for n in (1, 2, 3, 4):                           # 1.6 the frame: their own country
    K[("1.6", n, 1)] = own(control=None)
# 2.1: past / to, or the easy way the booklet also calls right
for n, a in enumerate([
        clock("seven o'clock", "seven"),
        clock("quarter past seven", "a quarter past seven", "seven fifteen"),
        clock("half past seven", "seven thirty"),
        clock("quarter to eight", "a quarter to eight", "seven forty-five", "seven forty five"),
        clock("twenty past seven", "seven twenty"),
        clock("ten to eight", "seven fifty")], 1):
    K[("2.1", n, 1)] = Q(a)
for n, a in enumerate(["9.30/9:30/09.30/09:30", "12.45/12:45", "6.10/6:10/06.10/06:10",
                       "10.40/10:40", "12.00/12:00/12", "7.55/7:55/07.55/07:55"], 1):
    K[("2.2", n, 1)] = Q(a)
for n, a in enumerate(["at", "in", "at", "in", "at", "at"], 1):
    K[("2.3", n, 1)] = choose(["at", "in"], a)
for n, a in enumerate(["have breakfast", "have lunch", "have dinner", "have lunch"], 1):
    K[("2.4", n, 1)] = Q(a)
for n, meal in enumerate(["breakfast", "lunch", "dinner"], 1):
    K[("2.5", n, 1)] = Q("What time do you have/What time do you have %s" % meal)
    K[("2.5", n, 2)] = own(control=None)
K[("2.5", 4, 1)] = Q("What time is your/What time's your/What time is your English class/"
                     "What time's your English class")
K[("2.5", 4, 2)] = own(control=None)
for n, a in enumerate([
        "I sometimes have breakfast at 9.00 at the weekend/Sometimes I have breakfast at 9.00 at the weekend/"
        "I sometimes have breakfast at 9:00 at the weekend/Sometimes I have breakfast at 9:00 at the weekend",
        "I usually have a sandwich for lunch/Usually I have a sandwich for lunch",
        "I never have breakfast",
        "In the evening, I always have dinner at about 7.00/In the evening, I always have dinner at about 7:00/"
        "I always have dinner at about 7.00 in the evening/I always have dinner at about 7:00 in the evening"], 1):
    K[("2.6", n, 1)] = write(a)
TICKED = "✓/correct/tick"
for n, a in zip(range(2, 9), [
        TICKED,
        "She has breakfast at seven o'clock/at seven o'clock/at",
        "What time do you have lunch",
        "It's half past four/It is half past four/half past four",
        TICKED,
        "They have lunch in the afternoon/in the afternoon/in",
        "I have breakfast in the morning/in the morning/in"]):
    K[("2.7", n, 1)] = fix(a)
for n in range(1, 13):                           # 2.8 ask three people: in class
    K[("2.8", n, 1)] = pair()
for n, a in enumerate([
        clock("quarter to eight", "a quarter to eight", "seven forty-five", "seven forty five"),
        clock("half past twelve", "twelve thirty"),
        clock("twenty past three", "three twenty"),
        clock("five past nine", "nine oh five", "nine o five")], 1):
    K[("2.9", n, 1)] = Q(a)
MEAL = {"B": "Breakfast", "L": "Lunch", "D": "Dinner"}
# as numbered: 1 cereal 2 sandwich 3 pizza 4 toast and jam 5 soup 6 rice and fish
for n, a in enumerate(["B", "L", "L/D", "B", "L/D", "D/B"], 1):
    K[("3.1", n, 1)] = choose(["B", "L", "D"], a, labels=MEAL)
for n, a in enumerate(["a banana/banana", "a tomato/tomato", "a sandwich/sandwich",
                       "ice cream/an ice cream/ice-cream", "an orange/orange", "butter"], 1):
    K[("3.2", n, 1)] = Q(a)
# as numbered: 1 apple 2 cheese 3 banana 4 butter 5 sandwich 6 ice cream 7 orange 8 jam
for n, a in enumerate(["an", "–", "a", "–", "a", "–", "an", "–"], 1):
    K[("3.3", n, 1)] = choose(["a", "an", "–"], a)
WIDE = {"class", "father", "afternoon", "past"}
for n, w in enumerate(WORDS34, 1):
    K[("3.4", n, 1)] = choose(["/ɑː/", "/ɔː/"], "/ɑː/" if w in WIDE else "/ɔː/",
                              labels={"/ɑː/": "/ɑː/ half", "/ɔː/": "/ɔː/ quarter"})
for n, a in zip((1, 2, 3, 4), ["cheese", "four", "pizza", "tomato"]):
    K[("3.6", n, 1)] = choose(ODD[n], a)
    K[("3.6", n, 2)] = own()
COUNTRIES = ["Turkey", "Spain", "the USA", "Brazil", "Mexico", "China"]
for n, a in zip((1, 2, 3), ["China", "Brazil", "Spain"]):       # 1 Julie 2 Lucas 3 Monica
    K[("4.1", n, 1)] = choose(COUNTRIES, a)
SIX = "half past six/six thirty/6.30/6:30/at half past six"
EIGHT = ("eight o'clock/eight/8.00/8:00/about eight/about eight o'clock/at eight/at eight o'clock/"
         "at about eight/at about eight o'clock")
TEN = "ten o'clock/ten/10.00/10:00/at ten/at ten o'clock"
for n, a in enumerate([None, SIX, None, EIGHT, None, TEN], 1):   # food / time, row by row
    K[("4.2", n, 1)] = Q(a) if a else own(control=None)
ADVERBS = ["always", "usually", "sometimes", "never"]
for n, a in enumerate(["usually", "sometimes", "never", "usually"], 1):
    K[("4.3", n, 1)] = choose(ADVERBS, a)
for n, a in enumerate("TTFFTF", 1):
    K[("4.4", n, 1)] = choose(TF, a)
for n in range(1, 5):                            # 4.5 ask your partner: in class
    K[("4.5", n, 1)] = pair()
K[("4.6", 1, 1)] = own()
NAMES = ["Julie", "Lucas", "Monica"]
for nth, (who, when) in enumerate([("Julie", SIX), ("Lucas", EIGHT), ("Monica", TEN)]):
    K[("4.7", 1, 2 * nth + 1)] = choose(NAMES, who)
    K[("4.7", 1, 2 * nth + 2)] = Q(when)
for n in (1, 2, 3):                              # 5.1 find in the model: his to read
    K[("5.1", n, 1)] = own()
for n in range(1, 6):
    K[("5.2", n, 1)] = own()
for n, a in enumerate(["What time/When", "When", "When", "What time/When"], 1):
    K[("5.4", n, 1)] = choose(["What time", "When"], a)
K[("5.5", 20, 1)] = own(control="essay")
for n in range(1, 7):                            # the checklist
    K[("5.5", n, 1)] = tick()
K[("5.5", 7, 1)] = own(control="number")        # Words: ...
K[("5.6", 1, 1)] = pair()
K[("5.6", 1, 2)] = pair()
for n in (2, 3, 4):
    K[("5.6", n, 1)] = pair()
for n in range(1, 6):                            # 5.7 class survey
    K[("5.7", n, 1)] = pair()
K[("5.8", 1, 1)] = pair()
FACE_SAYS = dict(zip(FACES, ["🙂 Ha", "😐 Qisman", "🙁 Hali yoʻq"]))
for n in CAN_DO:
    K[("5.9", n, 1)] = choose(FACES, labels=FACE_SAYS)

if __name__ == "__main__":
    data = h.build(K, "Beginner", 3, "Unit 3B — Food and drink")
    # the explanations are in Uzbek: the page says so, and the cover follows
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "b03b.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
