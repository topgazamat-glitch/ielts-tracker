"""B04A My life and my family - Azamat's Beginner booklet (4A), done on a phone.

His design is rendered as it is and this decides every box. The key is his
(B04A My life and my family - ANSWER KEY), joined box by box by hand. This is
the Material Bank copy (_NEW BOOKLET STYLE); it splits into its five parts.

As with the other Beginner booklets, every box that explains is told again
in Uzbek, as are the goals and every instruction; the English examples stay
English, as do the reading and the exercises.

Put right here: 2.5 says TWO sentences are correct; three are (2, 5 and 7 -
the key says so itself): it says THREE. What the paper has students
underline or tick is tapped or typed instead: 3.4's two loud words are typed
with a comma, 4.2's choice is a tap, 4.1 is one tap between the three names,
4.4 is "same" or "different" for each line. 3.2 items 2 and 4 take teach and
speak as well as teaches and speaks - the key says the -s is not tested yet.
The survey, the interviews and the mingle are done in class.

    python3 handouts/b04a_digital.py            # writes handouts/b04a.json, lists every box
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import (Handout, Q, choose, tick, own, write, fix, pair, report,   # noqa: E402
                     BLANK_TAG, plain, ITEM_STYLE, NUM_SPAN, TEXT_SPAN)

DOCX = ("~/Documents/Claude/Material Bank/General English/A1 Beginner/_NEW BOOKLET STYLE/"
        "B04A My life and my family — BOOKLET.docx")
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


def reword(label, old, new):
    at = section(label) + len("%s  </span>" % label)
    end = h.html.index("</p>", at)
    if plain(h.html[at:end]) != old:
        raise SystemExit("%s says %r" % (label, plain(h.html[at:end])))
    style = re.match(r'<span( style="[^"]*")?>', h.html[at:end])
    h.html = h.html[:at] + "<span%s>%s</span>" % (style.group(1) or "", html.escape(new)) + h.html[end:]


def boxes_for(label, nums, width="95%", placeholder=""):
    for n in nums:
        h.item_box(label, n, width=width, placeholder=placeholder)


# ------------------------------------------------------------ 2 Grammar
ENDS23 = halves("2.3", "abcde")
reword("2.5", "Find and correct the mistake. TWO sentences are correct — tick them.",
       "Find and correct the mistake. THREE sentences are correct — tick them.")
boxes_for("2.5", range(2, 9))                     # item 1 is the worked example
h.grid_rows("2.7", ["Person 1", "Person 2", "Person 3"])

# ------------------------------------------------------------ 3 Vocabulary
ENDS31 = halves("3.1", "abcdef")
reword("3.4", "Underline the TWO loud words in each question.",
       "Write the TWO loud words in each question, with a comma.")
boxes_for("3.4", range(1, 6), width="180px", placeholder="loud, words")
h.leaders("3.5", "BEFORE YOU LISTEN", [(n, W, "Sentence %d" % n) for n in range(1, 5)])

# ------------------------------------------------------------ 4 Listening
at = h.html.index(TAGS[74])                        # three ticks on one line: one tap between the names
a, b = h.html.rfind("<p", 0, at), h.html.index("</p>", at) + len("</p>")
h.html = h.html[:a] + item_p("4.1", 1, "Who?", "{{box:4.1:1:60px:}}", number=False) + h.html[b:]
reword("4.2", "Listen again. Underline the correct answer.", "Listen again. Choose the correct answer.")
boxes_for("4.2", range(1, 7), width="60px")
reword("4.4", "Compare Miriam and Nilufar (Section 1). Tick what is the same.",
       "Compare Miriam and Nilufar (Section 1). The same for both, or different?")
h.grid_rows("4.5")
h.leaders("4.6", "PRESENTATION — A PARAGRAPH", [(n, W, "Sentence %d" % n) for n in range(1, 4)])

# ------------------------------------------------------------ 5 Speaking and writing
h.grid_rows("5.3")
h.leaders("5.4", "CHECK BEFORE", [(20, W, "Write about your life here")])
h.html = h.html.replace(TAGS[118], "", 1)          # the word count: the box counts them itself
boxes_for("5.6", range(1, 7))
FACES, CAN_DO = h.can_do_grid("5.9")

# ------------------------------- every instruction, once more, in Uzbek
for label, text in [
        ("1.1", "Oʻzingiz haqingizda javob bering."),
        ("1.2", "Qaysi gap toʻgʻri? Faqat BITTASI. Toʻgʻrisiga *✓*, qolganlariga *✗* ni tanlang."),
        ("1.3", "U bu narsalar haqida nima deydi? Bir-ikki soʻz yozing."),
        ("1.4", "Toʻgʻri (*T*) mi yoki notoʻgʻri (*F*) mi?"),
        ("1.5", "Savollarga qisqa javob bering."),
        ("1.6", "Nilufarning hayoti haqida nima deb oʻylaysiz? Sherigingizga ayting."),
        ("2.1", "Soʻroq soʻzini tanlang: *Where, When, What, What time* yoki *Who*."),
        ("2.2", "Soʻzlarni tartib bilan qoʻyib, savol tuzing."),
        ("2.3", "Ha/yoʻq savolimi yoki *Wh-* savolmi? Har bir savolga javobning harfini tanlang."),
        ("2.4", "Har bir javob uchun savol yozing."),
        ("2.5", "Xatoni topib, toʻgʻrilang. UCHTA gap toʻgʻri — ular uchun *✓ It is correct* tugmasini bosing."),
        ("2.6", "Suhbatni toʻldiring."),
        ("2.7", "Uch kishidan soʻrang. Qisqa javoblarni yozing. Buni sinfda bajarasiz."),
        ("3.1", "Feʼlni sherigiga moslang: harfni tanlang."),
        ("3.2", "Toʻgʻri feʼl bilan toʻldiring."),
        ("3.3", "*at, to, in, the* yoki *–* (hech narsa) ni tanlang."),
        ("3.4", "Har bir savoldagi IKKI baland soʻzni vergul bilan yozing."),
        ("3.5", "Oʻzingiz haqingizda toʻrtta rost gap yozing. Toʻrt xil feʼl ishlating."),
        ("4.1", "Bir marta tinglang. Kim Oklendda yashaydi, lekin Vellingtonda ishlaydi?"),
        ("4.2", "Yana tinglang. Toʻgʻri javobni tanlang."),
        ("4.3", "Yana bir marta tinglang. Tom bergan savollarni yozing."),
        ("4.4", "Miriam va Nilufarni (1-boʻlim) solishtiring. Ikkalasida bir xilmi (*same*) yoki "
                "farqlimi (*different*)?"),
        ("4.5", "Endi siz. Sherigingizdan intervyu oling. Javoblarni yozing. Buni sinfda bajarasiz."),
        ("4.6", "Miriam haqida uchta gap yozing. 3-boʻlimdagi uch xil feʼlni ishlating."),
        ("5.1", "Namunani oʻqing. Toping…"),
        ("5.2", "Azizning oltita gapini olish uchun beriladigan oltita savolni yozing."),
        ("5.3", "Sinf boʻylab soʻrashing. Uch kishiga oltita savolingizni bering. Buni sinfda bajarasiz."),
        ("5.4", "Hayotingiz haqida yozing (60–80 soʻz). Olti gap, olti feʼl, namunadagi tartib."),
        ("5.5", "Sherigingiz bilan almashing. Uning matnini oʻqing va unga beradigan UCHTA savol yozing."),
        ("5.6", "Bir oʻquvchi yozgan oltita savolni toʻgʻrilang. Har birida bitta xato bor."),
        ("5.7", "Ikki rost, bitta yolgʻon. Hayotingiz haqida uchta gap yozing, bittasi yolgʻon. Sherigingiz "
                "savollar berib, yolgʻonni topadi. Buni sinfda bajarasiz."),
        ("5.8", "Sinfga ayting: 5.7 da sherigingiz haqida sizni hayron qoldirgan bitta narsa."),
        ("5.9", "Butun darsni eslang. Har bir ish uchun qanchalik qila olishingizni tanlang.")]:
    h.say_also(label, text)

# ------------------------------------------ the explanations, told in Uzbek
h.goals([
    "*Where / When / What / What time / Who + do you…?* deb soʻrashni",
    "*do* ni tushirib qoldirmaslikni — *Where DO you live?*, hech qachon *Where you live?* emas",
    "qisqa javob berishni: *In Tashkent. At nine. My parents.*",
    "*live, work, study, speak, go, play, teach, meet* feʼllarini toʻgʻri sherik soʻzlar bilan ishlatishni",
    "*study at university, go home, play the guitar* deyishni",
    "soʻroq soʻzi va feʼlni baland, *do you* ni esa past aytishni",
])
h.retell("KEY WORDS", "KALIT SOʻZLAR", [
    "**a blog**  blog — internetdagi shaxsiy sahifa",
    "**expensive**  qimmat — koʻp pul turadi",
    "**stay with**  birovnikida qisqa vaqt yashamoq",
    "**a language school**  til maktabi — til oʻrganish uchun maktab",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — WH- SAVOLLAR", [
    "3-unitda siz HA / YOʻQ savollarini berdingiz: *Do you work at home? — Yes, I do. / No, I don't.*",
    "Endi sizga „ha“ yoki „yoʻq“ emas, maʼlumot kerak. Oldiga SOʻROQ SOʻZINI qoʻying. Qolgan hamma narsa "
    "oʻzgarmaydi.",
    "[[WHERE]] joy. *Where do you live? — In Samarkand. · Where do you work? — In an office.*",
    "[[WHEN]] vaqt yoki kun. *When do you go home? — On Wednesday. · When do you have dinner? — At eight.*",
    "[[WHAT]] narsa. *What do you study? — English. · What do you do at the weekend? — I play football.*",
    "[[WHAT TIME]] soat. *What time do you start work? — At nine.*",
    "[[WHO]] odam. *Who do you live with? — My brother.*",
    "Tartib har doim bir xil: **soʻroq soʻzi + DO + you + feʼl?** *Where — do — you — live?* Toʻrt boʻlak, "
    "har doim shu tartibda.",
])
h.retell("ERROR WARNING", "DIQQAT — KOʻP UCHRAYDIGAN XATOLAR", [
    "1 **DO ni yoʻqotmang.** ✗ *Where you live?* ✗ *What you study?* → ✓ *Where do you live?* ✓ *What do "
    "you study?* Soʻroq soʻzi *do* ning oʻrnini bosmaydi — ikkalasi ham kerak.",
    "2 **Feʼlni birinchi qoʻymang.** ✗ *Where live you?* → ✓ *Where do you live?* Ingliz tilida savolda asosiy "
    "feʼl hech qachon *you* dan oldin kelmaydi.",
    "3 **WHAT DO YOU DO? — bitta savol.** Birinchi *do* — yordamchi, ikkinchi *do* — *do* feʼlining oʻzi "
    "(nima qilasiz yoki ishingiz). ✗ *What you do?* → ✓ *What do you do?*",
    "4 **Javob savolni takrorlamaydi.** *Where do you live?* — ✓ *In Samarkand.* ✗ *I live is in Samarkand* "
    "emas. Qisqa javob yetarli, inglizlar ham shunday javob beradi.",
    "5 **WHAT TIME soatni soʻraydi. WHEN esa har qanday vaqtni.** *What time…? — At nine.* *When…? — At nine "
    "/ On Monday / In the evening.*",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — SAKKIZ FEʼL VA ULARNING SHERIKLARI", [
    "Sakkizta feʼl hayotingizning koʻp qismini tasvirlaydi. Har birini sherik soʻzlari bilan birga oʻrganing.",
    "*live in a flat · in a house · in Tashkent · with my parents · work in an office · in a bank · in a "
    "hospital · at home*",
    "*study at university · at school · English · maths · speak English · Spanish · two languages*",
    "*go to the gym · to the cinema · home · to work · play football · tennis · the guitar*",
    "*teach English · young children · meet my friends · people · a friend for coffee*",
    "Roʻyxat ichida ikki kichik qoida bor. *go home* — *to* siz. *play the guitar*, lekin *play football* — "
    "cholgʻu asboblari *the* oladi, sport turlari olmaydi.",
])
h.retell("LANGUAGE PLUS — STUDY", "QOʻSHIMCHA — STUDY", [
    "**study + joy:** *study at university / at school / at a language school*",
    "**study + fan:** *study English / Spanish / maths / art* — predlogsiz.",
    "Demak: *I study English at university.* Avval fan, keyin *at* + joy.",
])
h.retell("PRONUNCIATION — WHICH WORDS ARE LOUD IN A QUESTION?", "TALAFFUZ — SAVOLDA QAYSI SOʻZLAR BALAND?", [
    "Savolda ikki xil soʻz baland aytiladi: SOʻROQ SOʻZI va ASOSIY FEʼL. *WHERE do you LIVE? · WHAT do you "
    "STUDY?*",
    "Ikki xil soʻz past aytiladi: *DO* va PREDLOG. *do you* → /djə/. *in* → /ɪn/, juda tez. *Do you WORK in an "
    "OFFice?* — baland soʻzlar *work* va *office*.",
    "**Nega muhim.** *WHERE DO YOU LIVE* ni toʻrtta bir xil soʻz bilan aytsangiz, robotga oʻxshaydi — va "
    "tushunish osonlashmaydi, qiyinlashadi. Ikki baland soʻz, qolgani past.",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [
    "Tom va Miriam Yangi Zelandiyadagi bir ziyofatda tanishadi. Ulardan biri Oklendda yashaydi, lekin "
    "Vellingtonda ishlaydi — Nilufar kabi ikki shahar. Kim ekanini va Miriamning hayoti haqidagi "
    "tafsilotlarni tinglang.",
    "Agar sinfingizda audio boʻlsa, bu 4.4-trek. Boʻlmasa, oʻqituvchingiz matnni oʻqib beradi — "
    "topshiriqlar bir xil.",
])
h.retell("WHY YOU DIDN'T HEAR IT", "NEGA ESHITMADINGIZ?", [
    "Soʻroq soʻzi baland; *do you* esa bitta past tovush. *Where do you live?* → /weə djə lɪv/. *do* ni "
    "kutsangiz, savolni oʻtkazib yuborasiz. Birinchi baland soʻzni tinglang — u qanday javob kelishini "
    "aytadi.",
    "Javob esa odatda predlog bilan boshlanadi. *In Auckland. On Monday. At eight. With my husband.* Oʻsha "
    "kichik soʻz qaysi savolga javob ekanini bildiradi.",
])
h.retell("PRESENTATION — A PARAGRAPH ABOUT YOUR LIFE", "TUSHUNTIRISH — HAYOTINGIZ HAQIDA BITTA ABZATS", [
    "Olti gap, olti feʼl, bitta abzats. Har bir gap 2-boʻlimdagi savollardan biriga javob beradi.",
    "[[NAMUNA]] *My name's Aziz and I'm from Namangan, but I live in Tashkent now. I live in a flat with two "
    "friends. I study economics at university, and I work in a café on Saturdays. I speak Uzbek, Russian and "
    "a little English. In the evening I go to the gym. At the weekend I meet my friends and we play football "
    "in the park.*",
    "Tartibga qarang: qayerda yashaysiz → kim bilan → nima oʻqiysiz yoki qayerda ishlaysiz → tillar → "
    "kechqurunlar → dam olish kunlari. Har bir gapda sakkiz feʼldan biri bor.",
])
h.retell("CHECK BEFORE YOU GIVE IT IN", "TOPSHIRISHDAN OLDIN TEKSHIRING", [
    "{box}  Sakkiz feʼldan kamida oltitasi.",
    "{box}  *study at university · go home* (*to* siz) *· play the guitar*.",
    "{box}  *I* yoki *we* dan keyin feʼlga *-s* qoʻshilmagan.",
    "{box}  Bitta gap *and* yoki *but* bilan bogʻlangan.",
    "{box}  Shahar va til nomlari bosh harf bilan.",
    "{box}  Soʻzlarni sanadim.",
])
h.one_per_line("TOPSHIRISHDAN OLDIN TEKSHIRING", None, at="box")
h.retell_cells({"Question word": "Soʻroq soʻzi", "verb": "feʼl", "Answer": "Javob"}, after="WH- SAVOLLAR")

# ------------------------------------------------------------------ the key
K = {}
for n in range(1, 4):                             # about you
    K[("1.1", n, 1)] = own()
TICK = {"✓": "✓ true", "✗": "✗ not true"}
for n, a in enumerate("✗✓✗", 1):
    K[("1.2", n, 1)] = choose(["✓", "✗"], a, labels=TICK)
for n, a in enumerate([either("very expensive", "expensive", "they're very expensive", "they are very expensive"),
                       either("small", "a small flat", "it's small", "it is small", "small flat"),
                       either("three", "3", "three days", "3 days", "Monday to Wednesday"),
                       either("two", "2", "two days", "2 days", "Thursday and Friday"),
                       either("Saturday morning", "on Saturday morning", "Saturday", "on Saturday"),
                       either("Sunday, in the park", "Sunday", "on Sunday", "in the park", "on Sunday in the park",
                              "every week", "not very good", "we're not very good")], 1):
    K[("1.3", n, 1)] = Q(a)
TF = {"T": "T · true", "F": "F · false"}
for n, a in enumerate("TFTTFF", 1):
    K[("1.4", n, 1)] = choose(["T", "F"], a, labels=TF)
for n, a in enumerate([either("In Samarkand", "Samarkand", "She lives in Samarkand"),
                       either("In Tashkent", "Tashkent", "In an office", "In an office near the station",
                              "In Tashkent, in an office near the station", "In an office in Tashkent",
                              "She works in Tashkent", "She works in an office"),
                       either("On Wednesday evening", "Wednesday evening", "On Wednesday", "Wednesday",
                              "She goes home on Wednesday evening"),
                       either("English", "She studies English"),
                       either("She plays football", "plays football", "football", "She plays football with her friends",
                              "She plays football in the park", "play football")], 1):
    K[("1.5", n, 1)] = Q(a)
QW = ["Where", "When", "What", "What time", "Who"]
for n, a in enumerate(["Where", "What", "What time/When", "When", "Who", "Where"], 1):
    K[("2.1", n, 1)] = choose(QW, a)
for n, a in enumerate(["Do you work in an office", "What do you study at university", "Do you speak Spanish",
                       "Where do you work", "Where do you live", "When do you go to the gym"], 1):
    K[("2.2", n, 1)] = write(a)
for n, a in enumerate("bcaed", 1):
    K[("2.3", n, 1)] = choose(ENDS23, a)
for n, a in enumerate(["Where do you live", "What do you study",
                       either("What time do you have lunch", "When do you have lunch"),
                       either("When do you go home", "What day do you go home"),
                       "Who do you live with"], 1):
    K[("2.4", n, 1)] = write(a)
TICKED = "✓/correct/tick"
for n, a in zip(range(2, 9), [TICKED, "Where do you live", "What do you do at the weekend", TICKED,
                              "When do you go to the gym", TICKED,
                              either("I work in a bank", "In a bank", "Where do you work? — I work in a bank",
                                     "Where do you work? I work in a bank")]):
    K[("2.5", n, 1)] = fix(a)
for n, a in enumerate(["Where", "live", "where", "work", "What", "start", "When", "Who"], 1):
    K[("2.6", n, 1)] = Q(a)
for n in range(1, 13):                            # three people, asked in class
    K[("2.7", n, 1)] = pair()
for n, a in enumerate("cefabd", 1):
    K[("3.1", n, 1)] = choose(ENDS31, a)
for n, a in enumerate(["live", "teaches/teach", "go", "speaks/speak", "play", "meet"], 1):
    K[("3.2", n, 1)] = Q(a)
PREP = ["at", "to", "in", "the", "–"]
for n, a in enumerate(["at", "–", "the", "in", "–", "to", "in", "–"], 1):
    K[("3.3", n, 1)] = choose(PREP, a)
for n, a in enumerate(["Where, live", "What, study", "work, office", "When, gym", "Who, live"], 1):
    K[("3.4", n, 1)] = Q(a)
for n in range(1, 5):
    K[("3.5", n, 1)] = own()
K[("4.1", 1, 1)] = choose(["Tom", "Miriam", "both of them"], "Miriam")
for n, (opts, a) in enumerate([(["Brazilian", "a New Zealander"], "Brazilian"),
                               (["Brazil", "New Zealand"], "New Zealand"),
                               (["is", "isn't"], "isn't"),
                               (["is", "isn't"], "is"),
                               (["English", "Portuguese"], "Portuguese"),
                               (["every day", "on Monday"], "on Monday")], 1):
    K[("4.2", n, 1)] = choose(opts, a)
for n, (q, v) in enumerate([("Where", "live"), ("Where", "work"), ("Who", "live"),
                            (either("What", "What language", "What languages", "Which language"), "at home"),
                            ("When", None)], 1):
    K[("4.3", n, 1)] = Q(q)
    if v:
        K[("4.3", n, 2)] = Q(v)
SAME = {"same": "the same", "different": "different"}
for n, a in enumerate(["same", "same", "different", "different", "different", "same"], 1):
    K[("4.4", n, 1)] = choose(["same", "different"], a, labels=SAME)
for n in range(1, 6):                             # the partner's answers
    K[("4.5", n, 1)] = pair()
for n in range(1, 4):
    K[("4.6", n, 1)] = own()
K[("5.1", 1, 1)] = own()                          # the eight verbs, in any order
K[("5.1", 2, 1)] = Q(either("two friends", "with two friends", "I live in a flat with two friends",
                            "in a flat with two friends"))
K[("5.1", 3, 1)] = Q(either("on Saturdays", "Saturdays", "on Saturday", "Saturday",
                            "I work in a café on Saturdays", "in a café on Saturdays"))
K[("5.1", 4, 1)] = own()                          # two sentences will do
for n, a in enumerate(["Where do you live", "Who do you live with",
                       either("What do you study", "Where do you work", "What do you study at university",
                              "What do you study? Where do you work", "What do you study and where do you work"),
                       either("What languages do you speak", "What language do you speak"),
                       either("What do you do in the evening", "What do you do in the evenings"),
                       "What do you do at the weekend"], 1):
    K[("5.2", n, 1)] = write(a)
for n in range(1, 6):                             # the mingle
    K[("5.3", n, 1)] = pair()
K[("5.4", 20, 1)] = own(control="essay")
for n in range(1, 7):                             # the checklist
    K[("5.4", n, 1)] = tick()
for n in range(1, 4):
    K[("5.5", n, 1)] = own()
for n, a in enumerate(["Where do you live", either("What do you do at the weekend", "What do you do"),
                       "Who do you live with", "What time do you get up", "Where do you study",
                       "When do you go to the gym"], 1):
    K[("5.6", n, 1)] = write(a)
FACE_SAYS = dict(zip(FACES, ["🙂 Ha", "😐 Qisman", "🙁 Hali yoʻq"]))
for n in CAN_DO:
    K[("5.9", n, 1)] = choose(FACES, labels=FACE_SAYS)

if __name__ == "__main__":
    data = h.build(K, "Beginner", 4, "Unit 4A — My life and my family")
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "b04a.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
