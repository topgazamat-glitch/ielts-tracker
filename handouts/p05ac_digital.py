"""P05AC Work - the new-style Pre-Intermediate booklet (5A & 5C), done on a phone.

Built like p03bd_new_digital.py from a TEAL build of the booklet (BOOK_THEME=teal
node build_p05ac.js, kept in "_NEW BOOKLET STYLE/digital source/"): the one-page
tables unwrapped, Uzbek goals, instruction lines and explanations. There was no
older 5A & 5C handout, so nothing is replaced and no answers carry across.

The key (his P05AC ANSWER KEY) is written with variants.ok, at his request (3
October 2026: "giving all the possible answers to avoid confusion among
students"): every box that marks itself takes every form of the right answer -
short and full forms (don't / do not, can't / cannot), with or without "a / an /
the", a figure or words. Where a task names the forms to use (2.3 have to, 2.4
mustn't or don't have to, 2.5 had to / didn't have to), only those forms count -
their short and full forms both. Where the task lets a right answer be said
another right way, the other ways count too: 5.3 "if you like", "Can I …?",
"How about giving / buying …"; 5.5 a different right correction ("Why don't you
ask …?"); 2.7 the corrected words alone or the corrected sentence, whole or in
part; 2.6 and 5.5 with or without the question mark.

What a phone gets that paper does not:
  - taps: who has the rule (1.2), TRUE / FALSE / NOT GIVEN (1.3), the meaning
    (2.1), the right option (2.2), job or work (3.6), who says it (4.2), T / F
    (5.1), does Tina do it (5.2, yes / no rather than a tick, which would read
    as "it was right as it was"), offer or suggestion (5.3), the checks before
    sending the recording (6.2);
  - 3.2 and 3.4 sort into columns on paper; on a phone each group of partners
    gets its verb to tap (3.2) and each job its stress pattern (3.4);
  - 2.7: the mistake as found (not marked), then the correction (marked);
  - 5.7 asked to underline the stressed words, which a phone cannot do: the
    instruction keeps the saying aloud.
The recorder for 6.2 is added by the site itself (core.add_recorders).

    python3 handouts/p05ac_digital.py       # writes handouts/p05ac.json, lists every box
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
from variants import ok as _ok   # noqa: E402


def ok(*answers, **kw):
    """variants.ok without "you've to" / "I've to": have to is not shortened."""
    return "/".join(f for f in _ok(*answers, **kw).split("/") if "'ve to" not in f.lower())

DOCX = ("~/Documents/Claude/Material Bank/General English/B1 Pre-intermediate/_NEW BOOKLET STYLE/digital source/"
        "P05AC Work — BOOKLET (teal, for the website).docx")
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


def taps_instead(label, words):
    """A sort-into-columns task becomes one line per word, each with its own
    box: everything from the end of the instruction to the end of the task's
    table goes, and its old boxes with it."""
    a = h.html.index("</p>", section(label)) + len("</p>")
    b = h.html.index("</table>", a) + len("</table>")
    lines = "".join('<p data-item="%s:%d" %s>%s%s {{box:%s:%d:200px:}}</p>'
                    % (label, n, ITEM_STYLE, NUM_SPAN % n, TEXT_SPAN % html.escape(w), label, n)
                    for n, w in enumerate(words, 1))
    for n, w in enumerate(words, 1):
        h.texts[(label, n)] = w
    h.html = h.html[:a] + lines + h.html[b:]


def boxes_per_item(label, until, nums, placeholder=""):
    """Several ruled lines under each item go; each item gets one growing box."""
    h.leaders(label, until, [])
    for n in nums:
        h.item_box(label, n, width=W, placeholder=placeholder)


# ------------------------------------------------------------ 1 Reading
for n in range(1, 8):
    h.item_box("1.3", n, where="leader")
h.leaders("1.5", "Grammar  ·", [(1, W, "Who says it? How do they know? Which is stronger?")])

# ------------------------------------------------------------ 2 Grammar
h.leaders("2.1", "2.2  </span>", [(11, W, "Your sentence with don't have to"),
                                   (12, W, "Your sentence with mustn't")])
for n in range(1, 9):
    h.item_box("2.2", n, width="200px")
h.leaders("2.6", "2.7  </span>", [(n, W, "The question") for n in range(1, 5)])
h.leaders("2.8", "2.9  </span>", [(1, W, "Four sentences: have to · don't have to · mustn't or can't · can")])
h.leaders("2.9", "Vocabulary  ·", [(1, W, "Your new rule, and why")])

# ------------------------------------------------------------ 3 Vocabulary
reword("3.2", "Which verb goes with each group? Write have, work, need, deal with, earn, be or make.",
       "Which verb goes with each group: **have**, **work**, **need**, **deal with**, **earn**, **be** or **make**? "
       "Tap it.")
PARTNERS = ["long hours · in a team · at weekends",
            "a university degree · good qualifications · several years of training",
            "people every day · serious problems",
            "a good salary · money",
            "important decisions",
            "a lot of skills · a nice working environment",
            "self-employed"]
taps_instead("3.2", PARTNERS)
for n in range(1, 9):
    h.item_box("3.3", n, where="leader")
reword("3.4", "Word stress. Write each job in the correct column. Then say the words aloud. (Listen to track 5.01 "
              "to check.)",
       "Word stress. Which pattern does each job have? Tap it (*banker* is **O**o). Then say the words aloud. "
       "(Listen to **track 5.01** to check.)")
STRESS_JOBS = ["accountant", "electrician", "gardener", "hairdresser", "lawyer", "plumber", "scientist"]
taps_instead("3.4", STRESS_JOBS)
h.leaders("3.7", "Listening  ·", [(1, W, "Three things in order, and why the first")])

# ------------------------------------------------------------ 4 Listening
h.leaders("4.4", "Everyday English  ·", [(1, W, "The job, and two reasons")])

# ------------------------------------------------------- 5 Everyday English
reword("5.2", "Part 2 (track 5.15). Which jobs will Tina do today? Tick (✓) FOUR.",
       "Part 2 (track 5.15). Will Tina do this job today? Tap **yes** or **no** — FOUR are yes.")
h.leaders("5.2", "5.3  </span>", [(7, W, "Why not the other two?")])
h.leaders("5.4", "5.5  </span>", [(n, W, "Your reply") for n in range(1, 3)])
h.leaders("5.5", "5.6  </span>", [(n, W, "The correct sentence") for n in range(1, 5)])
boxes_per_item("5.6", "5.7  </span>", range(1, 4), placeholder="One offer and one suggestion")
reword("5.7", "Pronunciation. Here shall, could and should are not stressed: their vowel is /ə/. Underline the "
              "stressed words, then say each sentence aloud three times.",
       "Pronunciation. Here *shall*, *could* and *should* are not stressed: their vowel is /ə/. Say each sentence "
       "aloud three times, stressing the important words.")

# ------------------------------------------------- 6 Speaking and writing
h.leaders("6.4", "</div>", [(1, W, "Write your text here")])

# ------------------------------- every instruction, once more, in Uzbek
for label, text in [
        ("1.1", "Oʻqishdan oldin. Sizningcha, qaysi kasbning qoidalari eng gʻalati: taksi haydovchisi, astronavt, saroy "
                "qoʻriqchisi yoki uchuvchi? Taxminingizni yozing."),
        ("1.2", "Bu qaysi kasb? *T* (taksi haydovchisi), *A* (astronavt), *G* (qoʻriqchi) yoki *P* (uchuvchi) ni "
                "tanlang."),
        ("1.3", "Gaplar matnga mos keladimi? *TRUE* (toʻgʻri), *FALSE* (notoʻgʻri) yoki *NOT GIVEN* (matnda bu haqda "
                "hech narsa yoʻq) ni tanlang."),
        ("1.4", "B xatboshining qisqacha mazmunini toʻldiring. Matndan IKKI SOʻZDAN KOʻP BOʻLMAGAN soʻz va/yoki son "
                "yozing."),
        ("1.5", "Dalil haqida oʻylang. Har bir gapni kim aytyapti? Ular buni qayerdan biladi? Qaysi biri kuchliroq dalil "
                "va nega?"),
        ("2.1", "Feʼl nimani bildiradi? *N* (kerak), *NN* (shart emas), *NA* (mumkin emas) yoki *A* (mumkin) ni "
                "tanlang. Keyin oʻzingiz bilgan kasb haqida ikkita gap yozing: biri *don't have to*, biri *mustn't* "
                "bilan."),
        ("2.2", "Toʻgʻri variantni tanlang."),
        ("2.3", "*have to* ning toʻgʻri shakli bilan toʻldiring: *have to, has to, don't have to, doesn't have to, do … "
                "have to, does … have to*."),
        ("2.4", "*mustn't* yoki *don't have to*? Gaplarni toʻldiring."),
        ("2.5", "Rustam bobo ellik yil oldin Samarqandda avtobus haydovchisi boʻlgan. Qavsdagi feʼl bilan *had to* yoki "
                "*didn't have to* ni yozing."),
        ("2.6", "Dilshod — elektrik. *have to* bilan savollarni yozing. Uning javoblari sizga yordam beradi."),
        ("2.7", "Sevara kafeda yangi ishni boshladi. Uning xabarida BESHTA xato bor. Avval xatoni, keyin toʻgʻrisini "
                "yozing."),
        ("2.8", "Endi siz. Maktabingiz yoki ishingiz haqida toʻrtta rost gap yozing: biri *have to*, biri *don't have "
                "to*, biri *mustn't* yoki *can't*, biri *can* bilan."),
        ("2.9", "Oʻylang. Maktabingiz yoki ish joyingizni yaxshiroq qiladigan BITTA yangi qoida yozing. *must* yoki "
                "*have to* ni ishlating va sababini ayting."),
        ("3.1", "Malikaning postini oʻqing. Qalin yozilgan iboralarga qarang."),
        ("3.2", "Har bir guruhga qaysi feʼl mos keladi: *have, work, need, deal with, earn, be* yoki *make*? Tanlang."),
        ("3.3", "Bu kim? Qutichadagi kasbni yozing."),
        ("3.4", "Urgʻu. Har bir kasbda urgʻu qanday? Tanlang (*banker* — **O**o). Keyin soʻzlarni ovoz chiqarib ayting. "
                "(Tekshirish uchun 5.01-trekni tinglang.)"),
        ("3.5", "Har bir gapni KATTA harflar bilan yozilgan soʻzning toʻgʻri shakli bilan toʻldiring."),
        ("3.6", "*job* yoki *work*? Tanlang."),
        ("3.7", "Oʻylang. Ishda siz uchun 3.2 dagi qaysi UCHTA narsa eng muhim? Ularni tartib bilan yozing va "
                "birinchisini nega tanlaganingizni tushuntiring."),
        ("4.1", "Jadvalni toʻldiring. Har bir javobga IKKI SOʻZDAN KOʻP yozmang."),
        ("4.2", "Buni kim aytadi? *A* (Alisha), *J* (Jason) yoki *M* (Megan) ni tanlang."),
        ("4.3", "Gaplarni *have to*, *don't have to*, *can't* yoki *don't need* bilan toʻldiring. Tekshirish uchun yana "
                "tinglang."),
        ("4.4", "Oʻylang. Uchta ishdan qaysi biri sizga koʻproq yoqadi? Ikkita sabab keltiring: biri gapiruvchilardan "
                "biri aytgan narsa, biri oʻzingizniki."),
        ("5.1", "1-qism (5.13-trek). *T* (toʻgʻri) yoki *F* (notoʻgʻri) ni tanlang."),
        ("5.2", "2-qism (5.15-trek). Tina bugun bu ishni qiladimi? *yes* yoki *no* ni tanlang — TOʻRTTASI *yes*. Keyin "
                "qolgan ikki ishni nega qilmasligini yozing."),
        ("5.3", "Suhbatdagi har bir gapni BITTA soʻz bilan toʻldiring. Keyin *O* (taklif — offer) yoki *S* (maslahat — "
                "suggestion) ni tanlang."),
        ("5.4", "Doʻstingiz uzr soʻrayapti. C qismidagi ibora bilan tinchlantiruvchi javob yozing va yana bitta gap "
                "qoʻshing."),
        ("5.5", "Har bir gapda BITTA xato bor. Gapni toʻgʻri yozing."),
        ("5.6", "Har bir vaziyat uchun BITTA taklif (offer) va BITTA maslahat (suggestion) yozing. Har safar boshqa "
                "ibora ishlating."),
        ("5.7", "Talaffuz. Bu gaplarda *shall*, *could* va *should* urgʻusiz aytiladi: unli tovushi /ə/. Har bir gapni "
                "uch marta ovoz chiqarib ayting."),
        ("6.1", "Har bir band uchun qayd yozing. Faqat qaydlar — toʻliq gaplar emas."),
        ("6.2", "Oʻzingizni yozib oling. Qaydlaringiz, *have to* va 3-boʻlimdagi ikkita ibora bilan taxminan bir daqiqa "
                "gapiring. Yozuvni oʻqituvchingizga yuboring."),
        ("6.3", "6.4 dagi matningizni rejalashtiring. Namunadan foydalaning. Faqat qaydlar."),
        ("6.4", "*Ishdagi qatʼiy qoidalar yaxshimi?* Uch xatboshidan iborat fikr matnini yozing (100–130 soʻz). 6.3 dagi "
                "rejangiz, 1-boʻlimdagi bitta fikr va *have to*, *mustn't* yoki *don't have to* ni ishlating.")]:
    h.say_also(label, text)

# ------------------------------------------ the explanations, told in Uzbek
h.retell("KEY WORDS", "KALIT SOʻZLAR", [
    "**a route**  yoʻnalish — bir joydan boshqa joyga boradigan yoʻl",
    "**satnav**  navigator — mashinada yoʻlni koʻrsatadigan qurilma",
    "**laundry**  kir yuvish — kiyimlarni yuvish",
    "**a warning**  ogohlantirish — xavf haqida aytilgan soʻzlar",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — MUST / HAVE TO / CAN", [          # the first of the two
    "[[A]] **have to = kerak, zarur** (qoida bor yoki vaziyat shuni talab qiladi). *Astronauts have to exercise every "
    "day. · My sister has to start work at six.* Soʻroq va inkor *do / does* bilan: *Do you have to wear a uniform? · "
    "He doesn't have to work at weekends.* Oʻtgan zamon: **had to** — *Yesterday I had to stay late.*",
    "[[B]] **must = kerak, zarur** — koʻpincha yozma qoida yoki gapiruvchining oʻz fikri. *All visitors must wear a "
    "helmet. · I must call my mum tonight.* *must* dan keyin *to* qoʻyilmaydi: *must wear* — *must to wear* emas. "
    "*must* ning oʻtgan zamon shakli yoʻq: **had to** ishlating.",
    "[[C]] **mustn't / can't = mumkin emas, ruxsat yoʻq.** *Pilots mustn't drink alcohol before a flight. · You can't "
    "use satnav in the test.* **can = mumkin, ruxsat bor:** *You can leave early on Friday.*",
    "[[D]] **Tuzoq: mustn't ≠ don't have to.** *You mustn't come in* — kirish mumkin emas, kirmang! *You don't have to "
    "come in* — kirish shart emas, lekin xohlasangiz kirishingiz mumkin. *Astronauts don't have to do laundry* — kir "
    "yuvish mashinasi yoʻq; ular qoidani buzmayapti.",
])
h.retell("WATCH OUT!", "DIQQAT — KOʻP UCHRAYDIGAN XATOLAR", [
    "1 ✗ *I must to go now.* → ✓ *I must go now.* — *must* dan keyin *to* yoʻq.",
    "2 ✗ *He have to work on Saturday.* → ✓ *He has to work on Saturday.* — *he / she / it* + *has to*.",
    "3 ✗ *Do I must wear a tie?* → ✓ *Do I have to wear a tie?* — soʻroq: *do* + *have to*.",
    "4 ✗ *Yesterday I must stay late.* → ✓ *Yesterday I had to stay late.* — oʻtgan zamon = *had to*.",
    "5 ✗ *It's Sunday — you mustn't go to work.* → ✓ *you don't have to go to work.* — shart emas, taqiqlanmagan.",
])
h.retell("WORD FAMILIES", "SOʻZ OILALARI", [
    "**employ** (ishga olmoq) → *an employer* (ish beruvchi — boshliq yoki kompaniya) · *an employee* (xodim) · "
    "*employment* (ish bilan bandlik) · *unemployed* (ishsiz) · *self-employed* (oʻzi uchun ishlaydigan)",
    "**qualify** → *a qualification* (malaka, diplom) · *qualified* (malakali)    **train** → *training* "
    "(tayyorgarlik) · *a trainee* (oʻrganayotgan xodim)    **decide** → *a decision* (qaror)",
])
h.retell("ERROR WARNING", "DIQQAT — ISH HAQIDAGI XATOLAR", [
    "✗ *She works as accountant.* → ✓ *as an accountant* — kasbdan oldin *a / an* · ✗ *I'm looking for a work.* → ✓ "
    "*a job* — *work* bilan *a* ishlatilmaydi",
    "✗ *He does important decisions.* → ✓ *makes* — qaror *make* bilan · ✗ *My father is self-employment.* → ✓ "
    "*self-employed*",
    "✗ *I deal people every day.* → ✓ *deal with people* — *with* kerak · ✗ *I have a lot of works today.* → ✓ *a lot "
    "of work* — *work* sanalmaydi",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [                 # the first of the two
    "**5.03-trek**ni tinglang (darslik, 5-unit, 5A dars). **Alisha**, **Jason** va **Megan** hozirgi va oldingi "
    "ishlari haqida gapiradi.",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — TAKLIF, MASLAHAT VA TASALLI", [
    "[[A]] **Taklif (offer)** — buni siz qilasiz: *I'll do it, if you want. · Shall I help you? · Would you like me to "
    "…? · Do you want me to …? · Why don't I …?* Istisno: taklifda **Shall I …?** ishlatiladi, hech qachon *Will I "
    "…?* emas.",
    "[[B]] **Maslahat (suggestion)** — buni boshqa odam qilishi mumkin: *Why don't you …? · You could … · Maybe you "
    "should …* **How about** dan keyin **-ing**: *How about taking her some flowers?* — *How about to take* emas.",
    "[[C]] **Tasalli (reassurance)** — odamga xavotir olmaslikni aytish: *It doesn't matter. · Never mind. · Don't "
    "worry about it. · It's no problem. · I'll be fine.*",
    "[[D]] **Taklifga javob:** *That would be great. · OK, if you're sure. · Are you sure?* — *No, don't worry. I'll "
    "do it tomorrow.*",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [
    "Rachelning gul doʻkoni bor, Tina unga yordam beradi. Rachel dugonasi Anniedan xabar oladi. **5.13-trek**ni (1-qism) "
    "va **5.15-trek**ni (2-qism) tinglang — darslik, 5-unit, 5C dars.",
])

# --------------------- the goals, in Uzbek, where the site's cover reads them
GOALS = [
    "ishdagi qoidalar haqidagi matnni tushunishni va dalilni baholashni",
    "*must / have to* (kerak), *don't have to* (shart emas), *mustn't / can't* (mumkin emas) va *can* (mumkin) ni "
    "ishlatishni",
    "oʻtgan zamondagi majburiyatni *had to* bilan aytishni",
    "kasblar va ish haqidagi iboralarni: *earn a good salary, work long hours, deal with people*",
    "taklif va maslahat berishni, xavotirlangan odamni tinchlantirishni",
    "ishdagi qoidalar haqida fikr matni yozishni",
]
first_bar = bh_section_at().search(h.html).start()
h.html = (h.html[:first_bar] + '<table class="bk"><tr><td><p><span>You will learn to</span></p>'
          + "".join('<p><span>—  </span>%s</p>' % told(g, bare=True) for g in GOALS)
          + "</td></tr></table>" + h.html[first_bar:])

# ------------------------------------------------------------------ the key
K = {}
TFNG = ["TRUE", "FALSE", "NOT GIVEN"]
K[("1.1", 1, 1)] = None                          # their guess: a word or two, theirs
for n, a in enumerate("TAGPPA", 1):
    K[("1.2", n, 1)] = choose(["T", "A", "G", "P"], a)
for n, a in enumerate(["FALSE", "FALSE", "TRUE", "TRUE", "FALSE", "NOT GIVEN", "FALSE"], 1):
    K[("1.3", n, 1)] = choose(TFNG, a)
for n, a in enumerate([ok("the Knowledge", "Knowledge", "the Knowledge of London"),
                       ok("25,000", "about 25,000", "twenty-five thousand", "twenty five thousand",
                          "about twenty-five thousand", "25 thousand"),
                       ok("satnav", "sat nav", "sat-nav", "a satnav", "satnavs", "GPS"),
                       ok("route", "routes"),
                       ok("years"),
                       ok("brain", "the brain", "brains")], 1):
    K[("1.4", n, 1)] = Q(a)
K[("1.5", 1, 1)] = own()

MEANING = {"N": "N · necessary", "NN": "NN · not necessary", "NA": "NA · not allowed", "A": "A · allowed"}
for n, a in enumerate(["NA", "NN", "NA", "A", "N", "NN", "A", "N", "N", "NA"], 1):
    K[("2.1", n, 1)] = choose(["N", "NN", "NA", "A"], a, labels=MEANING)
K[("2.1", 11, 1)] = own()
K[("2.1", 12, 1)] = own()
for n, (opts, a) in enumerate([(["doesn't have to", "mustn't"], "doesn't have to"),
                               (["must", "don't have to"], "must"),
                               (["can't", "don't have to"], "can't"),
                               (["can", "must"], "can"),
                               (["have to", "can't"], "have to"),
                               (["mustn't", "don't have to"], "don't have to"),
                               (["mustn't", "don't have to"], "mustn't"),
                               (["Do you have to", "Must you to"], "Do you have to")], 1):
    K[("2.2", n, 1)] = choose(opts, a)
# 2.3 asks for a form of HAVE TO: that form, short or full
K[("2.3", 1, 1)] = Q(ok("has to"))
K[("2.3", 2, 1)] = Q(ok("don't have to"))
K[("2.3", 3, 1)] = Q("Does")
K[("2.3", 3, 2)] = Q(ok("have to"))
K[("2.3", 4, 1)] = Q(ok("have to"))
K[("2.3", 5, 1)] = Q(ok("don't have to"))
K[("2.3", 6, 1)] = Q("Do")
K[("2.3", 6, 2)] = Q(ok("have to"))
for n, a in enumerate(["don't have to", "mustn't", "don't have to", "mustn't", "don't have to", "mustn't"], 1):
    K[("2.4", n, 1)] = Q(ok(a))
for n, a in enumerate(["had to get up", "had to check", "didn't have to work", "had to learn",
                       "didn't have to buy"], 1):
    K[("2.5", n, 1)] = Q(ok(a))
for n, a in enumerate([ok("Do you have to wear special clothes", "Do you have to wear any special clothes"),
                       ok("Do you have to work at weekends", "Do you have to work on weekends",
                          "Do you have to work at the weekend", "Do you have to work at the weekends",
                          "Do you have to work on the weekend"),
                       ok("Does your boss have to check your work"),
                       ok("Do you have to have a university degree", "Do you have to have a degree")], 1):
    K[("2.6", n, 1)] = write(a)
FIXED = [ok("must wear", "I must wear", "I must wear a black shirt", "I must wear a black shirt every day",
            "have to wear", "I have to wear", "I have to wear a black shirt", "I have to wear a black shirt every day"),
         ok("has to", "has to check", "manager has to", "My manager has to", "My manager has to check",
            "My manager has to check the money", "My manager has to check the money every hour"),
         ok("had to", "had to stay", "I had to stay", "Yesterday I had to stay", "I had to stay until ten",
            "Yesterday I had to stay until ten",
            "Yesterday I had to stay until ten because we were so busy"),
         ok("don't have to", "don't have to pay", "we don't have to pay", "we don't have to pay for lunch",
            "don't need to", "don't need to pay", "we don't need to pay", "we don't need to pay for lunch"),
         ok("Do I", "Do I have to", "Do I have to work", "Do I have to work on Sundays")]
for n, a in enumerate(FIXED, 1):
    K[("2.7", n, 1)] = None                       # the mistake as they found it: theirs, not marked
    K[("2.7", n, 2)] = write(a, control=None)
K[("2.8", 1, 1)] = own()
K[("2.9", 1, 1)] = own()

VERBS = ["have", "work", "need", "deal with", "earn", "be", "make"]
for n, a in enumerate(["work", "need", "deal with", "earn", "make", "have", "be"], 1):
    K[("3.2", n, 1)] = choose(VERBS, a)
for n, a in enumerate(["plumber", "lawyer", "hairdresser", "gardener", "scientist", "accountant", "IT worker",
                       "electrician"], 1):
    K[("3.3", n, 1)] = Q(ok(a, articles=True))
STRESS = ["Oo", "Ooo", "oOo", "ooOo"]
for n, a in enumerate(["oOo", "ooOo", "Ooo", "Ooo", "Oo", "Oo", "Ooo"], 1):
    K[("3.4", n, 1)] = choose(STRESS, a)
for n, a in enumerate([ok("self-employed", "self employed", "selfemployed"), "qualifications", "employees",
                       "training", "unemployed"], 1):
    K[("3.5", n, 1)] = Q(a)
for n, a in enumerate(["job", "work", "work", "job"], 1):
    K[("3.6", n, 1)] = choose(["job", "work"], a)
K[("3.7", 1, 1)] = own()

for n, a in enumerate([ok("designer", "game designer", "video game designer", "a designer"),
                       ok("IT worker", "an IT worker"),
                       ok("design", "game design", "designing"),
                       ok("instructor", "an instructor", "skateboard instructor", "teacher", "a teacher"),
                       ok("plumber", "a plumber"),
                       ok("certificate", "a certificate"),
                       ok("island", "an island", "the island"),
                       ok("bank", "a bank", "the bank")], 1):
    K[("4.1", n, 1)] = Q(a)
for n, a in enumerate("AJMAJ", 1):
    K[("4.2", n, 1)] = choose(["A", "J", "M"], a, labels={"A": "A · Alisha", "J": "J · Jason", "M": "M · Megan"})
for n, a in enumerate(["have to", "don't have to", "can't", "have to", "don't need", "don't have to"], 1):
    K[("4.3", n, 1)] = Q(ok(a))
K[("4.4", 1, 1)] = own()

for n, a in enumerate("TFTT", 1):
    K[("5.1", n, 1)] = choose(["T", "F"], a)
DOES = {"yes": "yes · Tina does it", "no": "no · not today"}
for n, a in enumerate(["yes", "yes", "no", "yes", "no", "yes"], 1):
    K[("5.2", n, 1)] = choose(["yes", "no"], a, labels=DOES)
K[("5.2", 7, 1)] = own()
OS = {"O": "O · offer", "S": "S · suggestion"}
for n, (word, kind) in enumerate([(ok("want", "like"), "O"),
                                  ("don't", "S"),               # "Why do not you" is not English
                                  ("Shall/Can/Should", "O"),
                                  ("me", "O"),
                                  ("could/can/should", "S"),
                                  ("taking/giving/buying/bringing/sending/getting", "S")], 1):
    K[("5.3", n, 1)] = Q(word)
    K[("5.3", n, 2)] = choose(["O", "S"], kind, labels=OS)
for n in range(1, 3):
    K[("5.4", n, 1)] = own()
for n, a in enumerate(["/".join(["How about asking your boss for a day off",      # not "Why do not you"
                                 "Why don't you ask your boss for a day off",
                                 "Maybe you should ask your boss for a day off", "You could ask your boss for a day off"]),
                       ok("Shall I carry those boxes for you", "Can I carry those boxes for you",
                          "Should I carry those boxes for you", "I'll carry those boxes for you"),
                       ok("Would you like me to help you", "Would you like me to help"),
                       ok("You could start with the easy jobs")], 1):
    K[("5.5", n, 1)] = write(a)
for n in range(1, 4):
    K[("5.6", n, 1)] = own()

for n in range(1, 5):                             # notes, not sentences
    K[("6.1", n, 1)] = None
for n in range(1, 4):                             # the three checks before sending the recording
    K[("6.2", n, 1)] = tick()
for n in range(1, 4):                             # the plan: notes
    K[("6.3", n, 1)] = None
K[("6.4", 1, 1)] = own(control="essay")

if __name__ == "__main__":
    data = h.build(K, "Pre-Intermediate", 5, "Unit 5A & 5C — Work")
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "p05ac.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
