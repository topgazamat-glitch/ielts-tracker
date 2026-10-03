"""P03BD Money - the new-style Pre-Intermediate booklet (3B & 3D), done on a phone.

It replaces "Unit 3B & 3D - Money" (test 90, p03bd_digital.py), the older design;
the exercises are all new, so no answers carry across. Built like
p03ac_new_digital.py from a TEAL build of the booklet (BOOK_THEME=teal node
build_p03bd.js), the one-page tables unwrapped, Uzbek goals, instruction lines
and explanations. The article's World Giving Index paragraph was put into the
past on 3 October 2026 (the index ended in 2024) - paper and phone alike.

The key (his P03BD ANSWER KEY) is written with variants.ok: every box that marks
itself takes every form of the right answer - short and full forms, figures and
words, with or without "a / the". Where the form IS the point - already / yet,
make / do / give, raise / rise - only that form counts. Where a right answer can
be worded too many ways to list (2.4's questions and answers about you, 5.2's
sentences found in the model), the box is his to read.

What a phone gets that paper does not:
  - taps: the paragraph (1.2), TRUE / FALSE / NOT GIVEN (1.3), the right form
    (2.5), A / B / C (4.2), who (4.6), which paragraph (5.1), the order (5.3),
    the checks before sending the recording (4.8);
  - 3.2 and 3.4 sort words into columns on paper; on a phone each phrase gets
    its own tap - make, do or give (3.2), /dʒ/ or /j/ (3.4);
  - 2.3's list becomes one line per job, with the box under it;
  - 2.6: the mistake as found (not marked), then the correction (marked).

    python3 handouts/p03bd_new_digital.py       # writes handouts/p03bd_new.json, lists every box
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import (Handout, Q, choose, tick, own, write, report,   # noqa: E402
                     plain, told, bh_section_at, ITEM_STYLE, NUM_SPAN, TEXT_SPAN, BLANK_TAG)
from variants import ok   # noqa: E402

DOCX = ("~/Documents/Claude/Material Bank/General English/B1 Pre-intermediate/_NEW BOOKLET STYLE/digital source/"
        "P03BD Money — BOOKLET (teal, for the website).docx")
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


def lines_instead_of_table(label):
    """A table with a box in its last column - "the job, done or not, your
    sentence" - becomes one line per row with the box under it: a phone would
    stack the three cells into a list that no longer reads as a row."""
    a = h.html.index('<table class="bk">', section(label))
    b = h.html.index("</table>", a) + len("</table>")
    rows = [re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)
            for r in re.findall(r"<tr>(.*?)</tr>", h.html[a:b], re.S)]
    out = ""
    for row in rows[1:]:
        tag = BLANK_TAG.search(row[-1])
        lead = " — ".join(plain(c) for c in row[:-1])
        if not tag:                                  # the worked example
            out += '<p style="margin-bottom:6px;color:#6E6E6E">%s: <i>%s</i></p>' % (
                html.escape(lead), html.escape(plain(row[-1])))
            continue
        i = int(tag.group(1))
        h.blanks[i]["text"] = lead
        out += '<p data-item="%s:%d" %s>%s<br>%s</p>' % (
            label, h.blanks[i]["num"], ITEM_STYLE, TEXT_SPAN % html.escape(lead), tag.group(0))
    h.html = h.html[:a] + out + h.html[b:]


# ------------------------------------------------------------ 1 Reading
for n in range(1, 6):
    h.item_box("1.2", n, where="leader")
for n in range(1, 8):
    h.item_box("1.3", n, where="leader")
h.leaders("1.5", "1.6  </span>", [(1, W, "Does it prove it? What would be stronger?")])
h.leaders("1.6", "Grammar  ·", [(1, W, "Your answers to the three questions")])

# ------------------------------------------------------------ 2 Grammar
h.leaders("2.1", "2.2  </span>", [(11, W, "Your sentence with already"), (12, W, "Your sentence with yet")])
h.leaders("2.2", "2.3  </span>", [(n, W, "The sentence") for n in range(1, 6)])
lines_instead_of_table("2.3")
h.leaders("2.4", "2.5  </span>", [(n, W, "Your question with yet, and your answer") for n in range(1, 5)])
for n in range(1, 7):
    h.item_box("2.5", n, width="200px")
h.leaders("2.7", "2.8  </span>", [(1, W, "Two things already done, two not done yet")])

# ------------------------------------------------------------ 3 Vocabulary
reword("3.2", "Write each phrase in the correct column.",
       "Which verb goes with each phrase: **make**, **do** or **give**? Tap it.")
taps_instead("3.2", ["a friend", "a good job", "sb advice", "a note of sth", "sb directions", "volunteer work",
                     "a payment", "money away", "something fun", "an example", "a donation", "a task"])
reword("3.4", "Sound and spelling. Is the first sound /dʒ/ (as in just) or /j/ (as in yet)? Write each word in the "
              "correct column. Then say them aloud. (Listen to track 3.10 first.)",
       "Sound and spelling. Is the first sound **/dʒ/** (as in *just*) or **/j/** (as in *yet*)? Tap it. Then say "
       "the words aloud. (Listen to **track 3.10** first.)")
taps_instead("3.4", ["enjoy", "you", "join", "young", "generous", "yesterday", "January", "year", "job",
                     "university"])
h.leaders("3.7", "3.8  </span>", [(1, W, "Two sentences with a reason")])

# ------------------------------------------------------------ 4 Listening
h.leaders("4.3", "4.4  </span>", [(n, W, "Your sentence with already or yet") for n in range(1, 5)])
h.leaders("4.4", "4.5  </span>", [(1, W, "Do you believe him? Why?")])

# -------------------------------------------------------------- 5 Writing
h.leaders("5.2", "5.3  </span>", [(1, W, "already / yet / make, do or give")])
h.leaders("5.6", "5.7  </span>", [(1, W, "Your first paragraph")])
h.leaders("5.7", "</div>", [(1, W, "Write your email here")])

# ------------------------------- every instruction, once more, in Uzbek
for label, text in [
        ("1.1", "Oʻqishdan oldin. Oxirgi marta biror narsa — pul, buyum yoki vaqtingizni — qachon berganingizni "
                "eslang. Kimga berdingiz?"),
        ("1.2", "Bu maʼlumot qaysi xatboshida (*A–F*)? Bitta harf ikki marta ishlatiladi."),
        ("1.3", "Gaplar matnga mos keladimi? *TRUE* (toʻgʻri), *FALSE* (notoʻgʻri) yoki *NOT GIVEN* (matnda bu haqda "
                "hech narsa yoʻq) ni tanlang."),
        ("1.4", "Qisqacha mazmunni toʻldiring. Matndan IKKI SOʻZDAN KOʻP BOʻLMAGAN soʻz va/yoki son yozing."),
        ("1.5", "Dalil haqida oʻylang. Finining hikoyasi berish odamni baxtli qilishini *isbotlaydimi*? Nega? Qanday "
                "dalil kuchliroq boʻlardi?"),
        ("1.6", "D xatboshidagi uchta savolga oʻzingiz haqingizda javob bering. 1.1 dagi javobingizdan foydalaning."),
        ("2.1", "*already* yoki *yet* bilan toʻldiring. Keyin oʻzingiz haqingizda ikkita toʻgʻri gap yozing: biri "
                "*already*, biri *yet* bilan."),
        ("2.2", "Qavsdagi soʻzni toʻgʻri joyga qoʻying. Gapni yozing."),
        ("2.3", "Nilufar xayriya konserti tashkil qilmoqda. Uning roʻyxatiga qarang. *already* yoki *yet* bilan "
                "gaplar yozing."),
        ("2.4", "*yet* bilan savollar yozing. Keyin ularga oʻzingiz haqingizda javob bering: *Yes, I have.* / *No, "
                "not yet.*"),
        ("2.5", "Present Perfect yoki Past Simple? Toʻgʻri variantni tanlang."),
        ("2.6", "Bekzod xayriya savdosida yordam bermoqda. Uning xabarida BESHTA xato bor. Avval xatoni, keyin "
                "toʻgʻrisini yozing."),
        ("2.7", "Endi siz. Bu hafta *allaqachon* qilgan ikkita ishingizni va hali *qilmagan* (lekin qilmoqchi "
                "boʻlgan) ikkita ishingizni yozing."),
        ("2.8", "Ikki qoʻshni hashar kuniga tayyorlanmoqda. Suhbatni qavsdagi feʼllar va *already* yoki *yet* bilan "
                "toʻldiring."),
        ("3.1", "Sardorning postini oʻqing. Qalin yozilgan iboralarga qarang."),
        ("3.2", "Har bir iboraga qaysi feʼl mos keladi: *make*, *do* yoki *give*? Tanlang."),
        ("3.3", "Har bir gapni *make*, *do* yoki *give* ning toʻgʻri shakli bilan toʻldiring."),
        ("3.4", "Tovush va imlo. Birinchi tovush */dʒ/* (*just* dagidek) yoki */j/* (*yet* dagidek)mi? Tanlang. Keyin "
                "soʻzlarni ovoz chiqarib ayting. (Avval 3.10-trekni tinglang.)"),
        ("3.5", "Har bir gapni KATTA harflar bilan yozilgan soʻzning toʻgʻri shakli bilan toʻldiring."),
        ("3.6", "*raise* yoki *rise*? Toʻgʻri shaklini ishlating."),
        ("3.7", "Oʻylang. Qaysi biri yaxshiroq: pul berishmi yoki vaqt berishmi? Sabab bilan ikkita gap yozing."),
        ("3.8", "*just* bilan iboralar. *just over, just under, just in time* yoki *just like* bilan toʻldiring."),
        ("4.1", "Qaydlarni toʻldiring. Har bir javobga IKKI SOʻZ VA/YOKI SONDAN KOʻP yozmang."),
        ("4.2", "Toʻgʻri javobni tanlang: *A*, *B* yoki *C*."),
        ("4.3", "Deniel haqida *already* yoki *yet* bilan gaplar yozing."),
        ("4.4", "Oʻylang. Deniel buyumlarini berib yuborish uni baxtliroq qildi deydi. Unga ishonasizmi? Nega?"),
        ("4.5", "Jadvalni toʻldiring. Har bir javobga IKKI SOʻZDAN KOʻP yozmang."),
        ("4.6", "Kim…? *S* (Shona), *JA* (Jack), *JE* (Jessica) yoki *W* (William)."),
        ("4.7", "Har bir band uchun qayd yozing. Faqat qaydlar — toʻliq gaplar emas."),
        ("4.8", "Oʻzingizni yozib oling. Qaydlaringiz, *already* yoki *yet* bilan bitta gap va 3-boʻlimdan ikkita "
                "ibora bilan taxminan bir daqiqa gapiring. Yozuvni oʻqituvchingizga yuboring."),
        ("5.1", "Namunaning qaysi xatboshisi (*1–4*) …"),
        ("5.2", "Namunadan toping: *already* bilan bitta gap, *yet* bilan bitta gap va 3-boʻlimdagi bitta *make / do / "
                "give* iborasi."),
        ("5.3", "Bu toʻrtta xatboshi boshqa bir xatdan olingan, lekin tartibi notoʻgʻri. Toʻgʻri tartibni tanlang."),
        ("5.4", "Topshiriqni oʻqing. *A* yoki *B* ni tanlang va kiritishingiz kerak boʻlgan maʼlumotni belgilang."),
        ("5.5", "Xatingizni rejalashtiring. Faqat qaydlar."),
        ("5.6", "Xatingizning birinchi xatboshisini yozing. Tekshiring: unda nega yozayotganingiz *va* asosiy "
                "yangilik bormi?"),
        ("5.7", "Xatingizni yozing (120–150 soʻz). 5.5 dagi rejangiz, toʻrt xatboshi, *already* va *yet* hamda "
                "namunadan bitta iborani ishlating.")]:
    h.say_also(label, text)

# ------------------------------------------ the explanations, told in Uzbek
h.retell("KEY WORDS", "KALIT SOʻZLAR", [
    "**a fortune**  juda katta pul, boylik",
    "**generous**  saxiy — boshqalarga berishni yaxshi koʻradigan",
    "**a charity**  xayriya tashkiloti — muhtojlarga yordam beradigan guruh",
    "**to volunteer**  koʻngilli boʻlib, tekinga ishlamoq",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — ALREADY VA YET", [         # the first of the two
    "[[A]] **already** = allaqachon boʻldi — koʻpincha kutilganidan ertaroq. *have / has* bilan uchinchi shakl "
    "**orasiga** qoʻyiladi: *I've already given £50. · More than 200 people have already signed the Pledge.*",
    "[[B]] **yet** = hozirgacha. **Inkor** va **soʻroq** gaplarda, gap **oxirida**: *We haven't sold the books yet. · "
    "Have you paid yet?* Qisqa javob: *Not yet.*",
    "[[C]] **Tugagan vaqt yoʻq.** *yesterday, last week, in 2020* bilan Past Simple: *I've already paid.* → *I paid "
    "yesterday.* — *I've already paid yesterday* emas.",
    "[[D]] **Istisnolar.** Savoldagi *already* ajablanishni bildiradi: *Have you already spent all your money?!* "
    "*yet* hech qachon tasdiq gapda ishlatilmaydi: *I've finished yet* emas → *I've already finished*. Notoʻgʻri "
    "feʼllarning uchinchi shaklini yodlang: give → *given* · do → *done* · make → *made* · pay → *paid* · spend → "
    "*spent* · sell → *sold* · buy → *bought*.",
])
h.retell("WATCH OUT!", "DIQQAT — KOʻP UCHRAYDIGAN XATOLAR", [
    "1 ✗ *I already have given it away.* → ✓ *I've already given it away.* — *already* *have* dan keyin.",
    "2 ✗ *I haven't already paid.* → ✓ *I haven't paid yet.* — inkorda *yet*.",
    "3 ✗ *Did you send the money yet?* → ✓ *Have you sent the money yet?* — Present Perfect.",
    "4 ✗ *We've already raised it last week.* → ✓ *We raised it last week.* — tugagan vaqt = Past Simple.",
    "5 ✗ *She has give all her old clothes away.* → ✓ *She has given …* — uchinchi shakl.",
])
h.retell("WORD FAMILIES — CHARITY", "SOʻZ OILALARI — XAYRIYA", [
    "**generous** → *generosity* (saxiylik) · **donate** → *a donation* (ehson), *a donor* (ehson qiluvchi) · "
    "**volunteer** (feʼl ham, ot ham) → *voluntary* (ixtiyoriy) · **charity** → *charitable* (xayriya) · **support** → "
    "*a supporter* · **sponsor** sb (kimdir xayriya uchun biror ish qilganda unga pul bermoq)",
    "**raise** money — pul yigʻmoq (toʻgʻri feʼl: *raised*) — lekin narxlar **rise** — oshadi (notoʻgʻri: *rose, "
    "risen*, toʻldiruvchisiz)",
])
h.retell("ERROR WARNING", "DIQQAT — MAKE / DO / GIVE XATOLARI", [
    "✗ *I did a donation.* → ✓ *made a donation* · ✗ *She makes volunteer work.* → ✓ *does volunteer work*",
    "✗ *He gave me an advice.* → ✓ *some advice / a piece of advice* · ✗ *We rose a lot of money.* → ✓ *raised*",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [                 # the first of the two
    "**3.07-trek**ni tinglang (darslik, 3-unit, 3B dars). Salli radio dasturini olib boradi. Uning mehmoni "
    "**Deniel** kamroq narsa bilan yashashni oʻrganmoqda.",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [
    "**3.18-trek**ni tinglang (darslik, 3-unit, 3D dars). **Shona**, **Jack**, **Jessica** va **William** xayriyaga "
    "pul berish haqida gapiradi.",
])
h.retell("PRESENTATION — PARAGRAPHS", "TUSHUNTIRISH — XATBOSHILAR", [
    "[[A]] **Bitta xatboshi — bitta fikr.** Yangi fikrni boshlaganda yangi xatboshi boshlang va xatboshilar orasida "
    "bitta qator tashlang. Birinchi gap xatboshi nima haqida ekanini aytadi.",
    "[[B]] **Yangilik xati toʻrt qismdan iborat:** **1** nega yozyapsiz (rahmat + asosiy yangilik) · **2** nima "
    "boʻldi · **3** pul nimaga sarflanadi · **4** keyingi tadbir + yana rahmat.",
    "[[C]] **Foydali iboralar:** *This email is to say a big thank you to … · I'm writing to let you know … · We've "
    "(already) raised … · The money will help … · Our next event is … · Thanks again for all your help.*",
])

# --------------------- the goals, in Uzbek, where the site's cover reads them
GOALS = [
    "berish va saxiylik haqidagi matnni tushunishni va dalilni baholashni",
    "Present Perfect ni *already* va *yet* bilan ishlatishni",
    "*make / do / give* iboralarini va xayriya soʻzlarini",
    "/dʒ/ va /j/ tovushlarini farqlashni",
    "radio dasturi va toʻrt kishining gaplarini tinglab tushunishni",
    "toʻrt xatboshidan iborat yangilik xatini yozishni",
]
first_bar = bh_section_at().search(h.html).start()
h.html = (h.html[:first_bar] + '<table class="bk"><tr><td><p><span>You will learn to</span></p>'
          + "".join('<p><span>—  </span>%s</p>' % told(g, bare=True) for g in GOALS)
          + "</td></tr></table>" + h.html[first_bar:])

# ------------------------------------------------------------------ the key
K = {}
TFNG = ["TRUE", "FALSE", "NOT GIVEN"]
K[("1.1", 1, 1)] = own()
for n, a in enumerate("DCBEB", 1):
    K[("1.2", n, 1)] = choose(list("ABCDEF"), a)
for n, a in enumerate(["FALSE", "TRUE", "FALSE", "FALSE", "FALSE", "NOT GIVEN", "TRUE"], 1):
    K[("1.3", n, 1)] = choose(TFNG, a)
for n, a in enumerate([ok("Duty Free Shoppers", "Duty-Free Shoppers", "Duty Free Shopper", "DFS", "Duty Free"),
                       ok("secret", "in secret", "secretly"),
                       ok("eight billion", "8 billion", "8,000,000,000", "8000000000", "about eight billion",
                          "about 8 billion", "$8 billion", "8 billion dollars", "eight billion dollars"),
                       ok("economy class", "economy", "in economy class", "in economy"),
                       ok("inspired", "inspired them"),
                       ok("2010", "in 2010")], 1):
    K[("1.4", n, 1)] = Q(a)
K[("1.5", 1, 1)] = own()
K[("1.6", 1, 1)] = own()

for n, a in enumerate(["yet", "already", "yet", "already", "yet", "already", "yet", "already", "yet", "already"], 1):
    K[("2.1", n, 1)] = Q(a)
K[("2.1", 11, 1)] = own()
K[("2.1", 12, 1)] = own()
for n, a in enumerate([ok("I've already given my old phone to my cousin", "I have already given my old phone to my cousin"),
                       ok("Have you paid for the concert tickets yet"),
                       ok("We haven't counted the money from the cake sale yet"),
                       ok("The animal shelter has already spent the money on food"),
                       ok("Has Sardor done his volunteer work this week yet",
                          "Has Sardor done his volunteer work yet this week")], 1):
    K[("2.2", n, 1)] = write(a)


def told_of(*bodies):
    """Every way of saying the same sentence about Nilufar or Daniel: she / he,
    or the name, with the short and the long form of has."""
    out = []
    for b in bodies:
        for who in b[0]:
            out.append("%s %s" % (who, b[1]))
    return ok(*out, limit=400)


SHE = ("She", "Nilufar")
for n, a in enumerate([told_of((SHE, "has already printed the tickets"), (SHE, "has printed the tickets already")),
                       told_of((SHE, "hasn't sold all the tickets yet"), (SHE, "hasn't sold all of the tickets yet")),
                       told_of((SHE, "has already found a singer"), (SHE, "has found a singer already")),
                       told_of((SHE, "hasn't bought the drinks yet")),
                       told_of((SHE, "hasn't made a poster yet"), (SHE, "hasn't made the poster yet"))], 1):
    K[("2.3", n, 1)] = write(a)
for n in range(1, 5):                             # questions about you, and your own answers: his to read
    K[("2.4", n, 1)] = own()
for n, (opts, a) in enumerate([(["I've already paid", "I already paid"], "I've already paid"),
                               (["raised", "has raised"], "raised"),
                               (["Have you sent", "Did you send"], "Have you sent"),
                               (["gave", "has given"], "gave"),
                               (["Has Aziz phoned", "Did Aziz phone"], "Did Aziz phone"),
                               (["haven't decided", "didn't decide"], "haven't decided")], 1):
    K[("2.5", n, 1)] = choose(opts, a)
FIXED = [ok("We've already sold", "We have already sold", "We've already sold fifty cakes",
            "We have already sold fifty cakes", "already sold"),
         ok("we haven't sold the books yet", "haven't sold the books yet", "But we haven't sold the books yet",
            "haven't sold them yet", "we haven't sold them yet"),
         ok("Have you found", "Have you found a box", "Have you found a box for the money yet",
            "Have you found a box for the money", "Have you found a box yet"),
         ok("has brought", "Dilnoza has brought", "Dilnoza has brought more cakes",
            "Dilnoza has brought more cakes from home", "brought"),
         ok("we counted the money", "We counted the money last night", "we counted the money from Friday's sale",
            "we counted the money from Friday's sale last night", "counted the money", "we counted",
            "counted the money last night")]
for n, a in enumerate(FIXED, 1):
    K[("2.6", n, 1)] = None                       # the mistake as they found it: theirs, not marked
    K[("2.6", n, 2)] = write(a, control=None)
K[("2.7", 1, 1)] = own()
for n, a in enumerate(["Have", "called", "yet", "already", "spoken", "bought", "yet", "already",
                       ok("got", "gotten"), "has", "made", "yet"], 1):
    K[("2.8", n, 1)] = Q(a)

K_MDG = ["make", "do", "give", "make", "give", "do", "make", "give", "do", "give", "make", "do"]
for n, a in enumerate(K_MDG, 1):
    K[("3.2", n, 1)] = choose(["make", "do", "give"], a)
for n, a in enumerate(["done", "made", "give", "made", "gave", "do"], 1):
    K[("3.3", n, 1)] = Q(a)
for n, a in enumerate(["/dʒ/", "/j/", "/dʒ/", "/j/", "/dʒ/", "/j/", "/dʒ/", "/j/", "/dʒ/", "/j/"], 1):
    K[("3.4", n, 1)] = choose(["/dʒ/", "/j/"], a)
for n, a in enumerate(["generosity", "donation", "volunteer", "charitable", "sponsored"], 1):
    K[("3.5", n, 1)] = Q(a)
for n, a in enumerate(["raised", exact("rise", "rose"), "raise", "risen"], 1):
    K[("3.6", n, 1)] = Q(a)
K[("3.7", 1, 1)] = own()
for n, a in enumerate(["just in time", "just under", "just like", "just over"], 1):
    K[("3.8", n, 1)] = Q(a)

for n, a in enumerate([ok("annoyed", "annoyed with his life", "a bit annoyed", "just annoyed"),
                       ok("six", "6", "six things", "6 things"),
                       ok("mobile phone", "mobile", "phone", "mobile-phone", "cell phone", "smartphone",
                          "his mobile phone", "his phone"),
                       ok("tablet", articles=True),
                       ok("bike", "his bike", "bicycle", "by bike", "ride his bike", "rides his bike"),
                       ok("hospital", "hospitals")], 1):
    K[("4.1", n, 1)] = Q(a)
K[("4.2", 1, 1)] = choose(["A", "B", "C"], "A")
K[("4.2", 2, 1)] = choose(["A", "B", "C"], "B")
HE = ("He", "Daniel")
for n, a in enumerate([told_of((HE, "has already given away his tablet"), (HE, "has already given his tablet away")),
                       told_of((HE, "hasn't found anyone who wants his desktop computer yet"),
                               (HE, "hasn't found anyone who wants his desktop yet"),
                               (HE, "hasn't found anyone who wants it yet"),
                               (HE, "hasn't found anyone for his desktop computer yet"),
                               (HE, "hasn't found anybody who wants his desktop computer yet")),
                       told_of((HE, "has already stopped using his car")),
                       told_of((HE, "has already given £25 to charity"), (HE, "has already given 25 pounds to charity"),
                               (HE, "has already given £25 to a charity"),
                               (HE, "has already given £25 to a children's hospital"))], 1):
    K[("4.3", n, 1)] = write(a)
K[("4.4", 1, 1)] = own()
for n, a in enumerate([ok("marathon", articles=True),
                       ok("childhoods", "childhood"),
                       ok("Greenpeace", "Green peace"),
                       ok("calendars", "their calendars", "calendar"),
                       ok("natural"),
                       ok("afford", "afford to", "really afford"),
                       ok("door-to-door", "door to door", "from door to door"),
                       ok("history", "our history")], 1):
    K[("4.5", n, 1)] = Q(a)
for n, a in enumerate(["JE", "S", "JA", "W"], 1):
    K[("4.6", n, 1)] = choose(["S", "JA", "JE", "W"], a)
for n in range(1, 4):                             # notes, not sentences
    K[("4.7", n, 1)] = None
for n in range(1, 4):                             # the three checks before sending the recording
    K[("4.8", n, 1)] = tick()

for n, a in enumerate("3142", 1):
    K[("5.1", n, 1)] = choose(list("1234"), a)
K[("5.2", 1, 1)] = own()
for n, a in enumerate("bdac", 1):
    K[("5.3", n, 1)] = choose(list("abcd"), a)
for n in range(1, 5):                             # the plan: notes
    K[("5.5", n, 1)] = None
K[("5.6", 1, 1)] = own()
K[("5.7", 1, 1)] = own(control="essay")

if __name__ == "__main__":
    data = h.build(K, "Pre-Intermediate", 3, "Unit 3B & 3D — Money")
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "p03bd_new.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
