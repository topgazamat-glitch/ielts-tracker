"""P03AC Money - the new-style Pre-Intermediate booklet (3A & 3C), done on a phone.

It replaces "Unit 3A & 3C - Money" (test 89, p03ac_digital.py), the older design;
the exercises are all new, so no answers carry across. Built like
p02ac_new_digital.py: a TEAL build of the booklet (BOOK_THEME=teal node
build_p03ac.js, in the Material Bank's "B1 Pre-intermediate/_NEW BOOKLET STYLE/
digital source/"), the one-page tables unwrapped, Uzbek goals, instruction lines
and explanations.

The key (his P03AC ANSWER KEY) is written with variants.ok: every box that marks
itself takes every form of the right answer - short and full forms, figures and
words, with or without "a / the", British and American spelling. Where the form
IS the point - the past forms and participles in 2.1, the short forms heard in
2.7, the small unstressed words in 5.3 - only that form counts. Where a right
answer can be worded too many ways to list (2.5's two questions, 5.5's ways of
changing your mind, 6.2's sentences), the box is his to read, not the computer's.

What a phone gets that paper does not:
  - taps: the paragraph (1.2), TRUE / FALSE / NOT GIVEN (1.3), PP or PS (2.2),
    the right form (2.3), who says it (4.2, 5.2), the order at the till (5.4),
    the checks before sending the recording (6.1);
  - a box per item where paper has ruled lines;
  - 2.6: the mistake as found (not marked), then the correction (marked).

    python3 handouts/p03ac_new_digital.py       # writes handouts/p03ac_new.json, lists every box
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import (Handout, Q, choose, tick, own, write, report,   # noqa: E402
                     plain, told, bh_section_at)
from variants import ok   # noqa: E402

DOCX = ("~/Documents/Claude/Material Bank/General English/B1 Pre-intermediate/_NEW BOOKLET STYLE/digital source/"
        "P03AC Money — BOOKLET (teal, for the website).docx")
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


def exact(*forms):
    """Only these forms (and their case) - for a task about the form itself."""
    return "/".join(forms)


# ------------------------------------------------------------ 1 Reading
# 1.4's timeline sits in two halves side by side on paper, to save a page; a
# phone stacks every cell, which would mix the two halves up - so it becomes one
# timeline in the order the things happened, its boxes moved with their cells
_at = h.html.index("1.4  </span>")
_t0 = h.html.index('<table class="bk">', _at)
_t1 = h.html.index("</table>", _t0) + len("</table>")
_rows = [re.findall(r"<td\b.*?</td>", r, re.S) for r in re.findall(r"<tr>(.*?)</tr>", h.html[_t0:_t1], re.S)]
assert all(len(r) == 4 for r in _rows), [len(r) for r in _rows]
_new = [_rows[0][:2]] + [r[:2] for r in _rows[1:]] + [r[2:] for r in _rows[1:]]
h.html = (h.html[:_t0] + '<table class="bk">' + "".join("<tr>%s</tr>" % "".join(r) for r in _new) + "</table>"
          + h.html[_t1:])
for n in range(1, 7):
    h.item_box("1.2", n, where="leader")
for n in range(1, 8):
    h.item_box("1.3", n, where="leader")
h.leaders("1.5", "Grammar  ·", [(1, W, "Who changed it, and why companies like such stories")])

# ------------------------------------------------------------ 2 Grammar
h.leaders("2.5", "2.6  </span>", [(n, W, "Have you ever …? + your follow-up question") for n in range(1, 5)])
h.leaders("2.8", "2.9  </span>", [(1, W, "One sentence in the present perfect, one in the past simple")])
h.leaders("2.9", "2.10  </span>", [(1, W, "Four sentences about money and shopping")])

# ------------------------------------------------------------ 3 Vocabulary
h.leaders("3.6", "Listening  ·", [(1, W, "Two or three sentences with a reason")])

# ------------------------------------------------------------ 4 Listening
h.leaders("4.3", "4.4  </span>", [(1, W, "Why he didn't get the jeans")])
h.leaders("4.4", "4.5  </span>", [(1, W, "Clever or unkind? And why")])
h.leaders("4.5", "Everyday English  ·", [(1, W, "Your Have you ever …? question and a follow-up")])

# ------------------------------------------------------ 5 Everyday English
for n in range(1, 9):
    h.item_box("5.1", n, width="220px", where="leader")
h.leaders("5.5", "5.6  </span>", [(n, W, "Actually, … / On second thoughts, …") for n in range(1, 4)])
h.leaders("5.6", "Speaking and writing  ·", [(1, W, "Your conversation in the shop")])

# ------------------------------------------------- 6 Speaking and writing
h.leaders("6.4", "</div>", [(1, W, "Write your opinion text here")])

# ------------------------------- every instruction, once more, in Uzbek
for label, text in [
        ("1.1", "Oʻqishdan oldin. Oxirgi marta biror narsa sotib olganingizda qanday toʻladingiz — naqd pul, karta "
                "yoki telefon bilanmi?"),
        ("1.2", "Bu maʼlumot qaysi xatboshida (*A–F*)?"),
        ("1.3", "Gaplar matnga mos keladimi? *TRUE* (toʻgʻri), *FALSE* (notoʻgʻri) yoki *NOT GIVEN* (matnda bu haqda "
                "hech narsa yoʻq) ni tanlang."),
        ("1.4", "Vaqt jadvalini toʻldiring. Matndan IKKI SOʻZDAN KOʻP BOʻLMAGAN soʻz va/yoki son yozing."),
        ("1.5", "Dalil haqida oʻylang. Yoʻqolgan hamyon haqidagi hikoyani kim oʻzgartirdi? Kompaniyalar nega bunday "
                "hikoyalarni yaxshi koʻradi? Ikkita gap yozing."),
        ("2.1", "Past Simple va Past Participle (uchinchi shakl) ni yozing."),
        ("2.2", "Bu soʻzlar qaysi zamon bilan keladi? *PP* (Present Perfect) yoki *PS* (Past Simple) ni tanlang."),
        ("2.3", "Toʻgʻri shaklni tanlang."),
        ("2.4", "Timur va Shahzoda xarid haqida gaplashmoqda. Suhbatni qavsdagi feʼllar bilan toʻldiring: Present "
                "Perfect yoki Past Simple."),
        ("2.5", "*Have you ever …?* savolini yozing. Keyin Past Simple da davom ettiruvchi savol yozing."),
        ("2.6", "Sardorning xabarida BESHTA xato bor. Avval xatoni, keyin toʻgʻrisini yozing."),
        ("2.7", "Talaffuz. 3.04-trekni tinglang. Eshitgan qisqa shakllaringizni yozing: *'ve, 's, haven't, hasn't, "
                "Have, has*. Keyin gaplarni ovoz chiqarib ayting."),
        ("2.8", "Oʻylang. Matndagi qaysi ixtiro odamlar hayotini eng koʻp oʻzgartirgan? Ikkita gap yozing: biri "
                "Present Perfect da, biri Past Simple da."),
        ("2.9", "Endi siz. Pul va xarid haqida toʻrtta gap yozing: ikkitasi tajribangiz haqida (*ever / never*) va "
                "ikkitasi biror narsa *qachon* boʻlganini aytadi."),
        ("2.10", "*been* yoki *gone*? Tushuntirishning D qismiga qarang."),
        ("3.1", "3.01-trekni tinglang: Kerol va Brayanning hikoyalari (darslik, Vocabulary Focus 3A). Sonlarni "
                "yozing."),
        ("3.2", "Ramkadagi soʻzlarni maʼnolari bilan moslang."),
        ("3.3", "Gaplarni toʻldiring. *borrow, lend, owe, afford, spend* yoki *cost* ning toʻgʻri shaklini "
                "ishlating."),
        ("3.4", "Predloglar. *in, by, for, from, to* yoki *on* bilan toʻldiring."),
        ("3.5", "Har bir gapni KATTA harflar bilan yozilgan soʻzning toʻgʻri shakli bilan toʻldiring."),
        ("3.6", "Oʻylang. Doʻstlardan qarz olish yaxshi fikrmi? Sabab bilan ikki-uchta gap yozing."),
        ("4.1", "Qaydlarni toʻldiring. IKKI SOʻZ VA/YOKI SONDAN KOʻP yozmang."),
        ("4.2", "Buni kim aytadi? *M* (Mike), *K* (Kathie) yoki *J* (Janie)."),
        ("4.3", "Erkak nega jinsi shimni ololmadi? Bir-ikkita gap yozing."),
        ("4.4", "Oʻylang. Keksa ayol aqllimi yoki mehrsizmi? Sabab bilan ikkita gap yozing."),
        ("4.5", "Endi siz. Mike yoki Kathie uchun *Have you ever …?* savolini va davom ettiruvchi savolni yozing."),
        ("5.1", "Savollarga javob bering. UCH SOʻZDAN KOʻP yozmang."),
        ("5.2", "3.14-trekni tinglang. Buni kim aytadi: sotuvchi (*SA*) yoki xaridor (*C*)?"),
        ("5.3", "Gapdagi urgʻu. Kichik soʻzlarga urgʻu tushmaydi, shuning uchun ularni eshitish qiyin. 3.16-trekni "
                "tinglang va tushib qolgan soʻzlarni yozing."),
        ("5.4", "3-qism (3.17-trek): Mark kassada toʻlaydi. Qatorlarni tartiblang: *1–8*. Keyin tinglab tekshiring."),
        ("5.5", "Fikringizni oʻzgartiring. Nima deysiz? *Actually, …* yoki *On second thoughts, …* bilan boshlang."),
        ("5.6", "Onangiz uchun sovgʻa kerak. Toshkentdagi doʻkon sotuvchisi bilan suhbatingizni yozing (8 qator). A, B "
                "va C dagi iboralardan foydalaning va bir marta fikringizni oʻzgartiring."),
        ("6.1", "Har bir band uchun qayd yozing. Keyin oʻzingizni yozib oling: taxminan bir daqiqa gapiring va yozuvni "
                "oʻqituvchingizga yuboring. Present Perfect bilan boshlang va Past Simple da davom eting."),
        ("6.2", "Namunani oʻqing. Savollarga qisqa qayd shaklida javob bering."),
        ("6.3", "12-sahifadagi savol boʻyicha matningizni rejalashtiring. Faqat qaydlar."),
        ("6.4", "*Naqd pul bilan toʻlash yaxshimi yoki karta bilanmi?* Fikringizni namunadagidek uch xatboshida yozing "
                "(100–130 soʻz). *Firstly, Secondly, For example* va *To sum up* ni, Present Perfect da bitta gap, "
                "Past Simple da bitta gap va 3-boʻlimdan ikkita soʻz ishlating.")]:
    h.say_also(label, text)

# ------------------------------------------ the explanations, told in Uzbek
h.retell("KEY WORDS", "KALIT SOʻZLAR", [
    "**to swap**  ayirboshlamoq — bir narsani berib, boshqasini olmoq",
    "**a coin**  tanga — kichik dumaloq metall pul",
    "**a note**  qogʻoz pul, kupyura",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — PRESENT PERFECT YOKI PAST SIMPLE", [       # the first of the two
    "[[A]] **Present Perfect** (*have / has* + uchinchi shakl) — **hozirgacha boʻlgan hayotingizdagi tajriba**, "
    "qachonligi aytilmaydi: *I've used a cash machine. · She has never borrowed money. · Have you ever bought "
    "anything online? · I've worked on sales days three times before.*",
    "[[B]] **Past Simple** — **tugagan vaqt**, *qachon* ekanini aytamiz yoki soʻraymiz: *I bought it yesterday / "
    "last week / in 2024 / two days ago / when I was ten. · When did you buy it?*",
    "[[C]] **Suhbat** koʻpincha Present Perfect bilan boshlanib, Past Simple da davom etadi: *Have you ever lost "
    "your wallet? — Yes, I have. — Where did you lose it? — I lost it on the bus.* Yana: *the cleverest customer "
    "I've ever met.*",
    "[[D]] **Istisnolar.** Tugagan vaqt bilan Present Perfect hech qachon ishlatilmaydi: *I bought it yesterday* — "
    "*I've bought it yesterday* emas. **been** yoki **gone**? *She's been to Dubai* (borib, qaytib keldi) · *She's "
    "gone to Dubai* (hozir oʻsha yerda).",
])
h.retell("WATCH OUT!", "DIQQAT — KOʻP UCHRAYDIGAN XATOLAR", [
    "1 ✗ *I have bought this phone last year.* → ✓ *I bought …* — tugagan vaqt.",
    "2 ✗ *Did you ever been to Dubai?* → ✓ *Have you ever been …?*",
    "3 ✗ *When have you paid?* → ✓ *When did you pay?* — *when* tugagan vaqtni soʻraydi.",
    "4 ✗ *I have went to the bazaar.* → ✓ *I have been / I went …* · ✗ *I never have used a card.* → ✓ *I have "
    "never used …*",
])
h.retell("ERROR WARNING", "DIQQAT — PUL SOʻZLARIDAGI XATOLAR", [
    "✗ *Can you borrow me 10,000 som?* → ✓ *lend me* — *borrow from* (qarz olmoq), *lend to* (qarz bermoq)",
    "✗ *I took a credit from the bank.* → ✓ *got a loan* · ✗ *I can't let myself buy it.* → ✓ *I can't afford it.*",
    "✗ *The price is very expensive.* → ✓ *The price is very high. / It's very expensive.*",
    "✗ *I paid the bread.* → ✓ *paid for the bread* · ✗ *I have a debt to him.* → ✓ *I owe him money.*",
])
h.retell("WORD FAMILIES", "SOʻZ OILALARI", [
    "**pay** → *a payment* (toʻlov) · **save** → *savings* (jamgʻarma, bankdagi pul) · **afford** → *affordable* "
    "(arzon, hamyonbop)",
    "**buy** → *a buyer* (xaridor) · **sell** → *a seller* (sotuvchi) · *a sale* (chegirmali savdo) · **price** → "
    "*pricey* (soʻzlashuvda: qimmat)",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [                 # the first of the two
    "Darslikda (3A dars) muxbir Janie *Black Friday* chegirmalar kunida ikki sotuvchi — Mike va Kathie bilan "
    "gaplashadi. **3.02-trek**ni tinglang.",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — DOʻKONDA", [
    "[[A]] **Sotuvchi:** *Can I help you? · Are you looking for anything in particular? · What sort of thing does he "
    "like? · How about this?*",
    "[[B]] **Xaridor:** *We're looking for a present for a friend. · What is it exactly? · What does it do? · Do you "
    "have anything cheaper? · Could you show us something else? · We'll take it.*",
    "[[C]] **Kassada:** *Who's next, please? · How would you like to pay? — Cash. / By card. · Can you put your card "
    "in, please? · Can you enter your PIN, please? · Here's your receipt.*",
    "[[D]] **Fikrni oʻzgartirish:** *Actually, I think I'll put it on my credit card. · On second thoughts, I think we "
    "should get something sporty.* **Istisno:** *actually* — «aslida», hech qachon «hozir» emas. «Hozir» uchun *at "
    "the moment* deng: *This phone is very popular at the moment.*",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [
    "Reychel va Markka Leo uchun tugʻilgan kun sovgʻasi kerak. **3.12-trek** (1-qism) va **3.13-trek**ni (2-qism) "
    "tinglang — darslik, 3-unit, 3C dars.",
])

# --------------------- the goals, in Uzbek, where the site's cover reads them
GOALS = [
    "pul tarixi haqidagi matnni tushunishni va dalilni baholashni",
    "Present Perfect va Past Simple ni farqlashni: *ever / never / before* va tugagan vaqt",
    "pul va xarid soʻzlarini: *borrow / lend, owe, afford, save up, discount, bargain*",
    "doʻkonda sotuvchi bilan gaplashishni va kassada toʻlashni",
    "fikringizni oʻzgartirishni: *Actually … / On second thoughts …*",
    "uch xatboshidan iborat fikr matnini yozishni",
]
first_bar = bh_section_at().search(h.html).start()
h.html = (h.html[:first_bar] + '<table class="bk"><tr><td><p><span>You will learn to</span></p>'
          + "".join('<p><span>—  </span>%s</p>' % told(g, bare=True) for g in GOALS)
          + "</td></tr></table>" + h.html[first_bar:])

# ------------------------------------------------------------------ the key
K = {}
TFNG = ["TRUE", "FALSE", "NOT GIVEN"]
K[("1.1", 1, 1)] = own()
for n, a in enumerate("CADEFB", 1):
    K[("1.2", n, 1)] = choose(list("ABCDEF"), a)
for n, a in enumerate(["FALSE", "FALSE", "NOT GIVEN", "TRUE", "FALSE", "TRUE", "NOT GIVEN"], 1):
    K[("1.3", n, 1)] = choose(TFNG, a)
# the boxes are numbered in the order they stand on paper, where the timeline is
# two halves side by side: (1) (4) / (2) (5) / (3) (6)
for n, a in enumerate([ok("Lydia", "in Lydia"),                                          # (1)
                       ok("1950", "in 1950"),                                            # (4)
                       ok("paper", "paper notes", "paper money"),                        # (2)
                       ok("cash machine", "cash-machine", "cashmachine", "ATM", "cash point", "cashpoint",
                          "cash machine in London", articles=True),                      # (5)
                       ok("Sweden", "in Sweden"),                                        # (3)
                       ok("som", "so'm", "sum", "soum", "the som", "so‘m")], 1):         # (6)
    K[("1.4", n, 1)] = Q(a)
K[("1.5", 1, 1)] = own()

# 2.1 is about the forms themselves: only those forms
PARTS = [("bought", "bought"), ("spent", "spent"), ("lent", "lent"), ("paid", "paid"), ("sold", "sold"),
         ("gave", "given"), ("took", "taken"), ("saw", "seen"), ("won", "won"), ("borrowed", "borrowed")]
for n, (past, part) in enumerate(PARTS, 1):
    K[("2.1", n, 1)] = Q(past)
    K[("2.1", n, 2)] = Q(part)
for n, a in enumerate(["PS", "PP", "PS", "PP", "PS", "PP", "PS", "PS", "PP", "PS"], 1):
    K[("2.2", n, 1)] = choose(["PP", "PS"], a)
for n, (opts, a) in enumerate([(["has opened", "opened"], "opened"),
                               (["Have you ever paid", "Did you ever pay"], "Have you ever paid"),
                               (["have never borrowed", "never borrowed"], "have never borrowed"),
                               (["has lost", "lost"], "lost"),
                               (["Have you been", "Did you go"], "Did you go"),
                               (["has visited", "visited"], "visited"),
                               (["have ever met", "ever met"], "have ever met"),
                               (["have bought", "bought"], "bought")], 1):
    K[("2.3", n, 1)] = choose(opts, a)
for n, a in enumerate(["Have", "bought", "have", "bought", "cost", "Did", "arrive", "took",
                       ok("have never ordered", "'ve never ordered"),
                       ok("have always bought", "'ve always bought"),
                       "Have", ok("got", "gotten"), "paid"], 1):
    K[("2.4", n, 1)] = Q(a)
for n in range(1, 5):                             # two questions in one box, many right wordings: his to read
    K[("2.5", n, 1)] = own()
FIXED = [ok("I bought", "bought", "I bought a new phone yesterday", "I bought a new phone"),
         ok("Have you ever bought", "Have you ever bought anything", "Have you ever bought anything in a Black Friday sale"),
         ok("went", "My sister went", "My sister went to the sales", "My sister went to the sales last year",
            "went to the sales last year", "has been", "My sister has been to the sales", "has been to the sales"),
         ok("She has never paid", "has never paid", "She has never paid full price",
            "She has never paid full price for anything", "She never paid", "never paid",
            "She never paid full price", "She never paid full price for anything"),
         ok("When did you get", "When did you get your phone", "did you get", "When did you buy",
            "When did you buy your phone")]
for n, a in enumerate(FIXED, 1):
    K[("2.6", n, 1)] = None                       # the mistake as they found it: theirs, not marked
    K[("2.6", n, 2)] = write(a, control=None)
# 2.7 is about the short forms heard; the full forms are right English too, so they count
for n, a in enumerate([exact("'ve", "’ve", "ve"), exact("'s", "’s", "s"),
                       ok("haven't", "have not", "havent"), ok("hasn't", "has not", "hasnt"),
                       "Have", "has"], 1):
    K[("2.7", n, 1)] = Q(a)
K[("2.8", 1, 1)] = own()
K[("2.9", 1, 1)] = own()
for n, a in enumerate(["gone", "been", "gone", "been"], 1):
    K[("2.10", n, 1)] = Q(a)

for n, a in enumerate([ok("100", "£100", "100 pounds", "one hundred", "a hundred"),
                       ok("700", "£700", "700 pounds", "seven hundred"),
                       ok("1,000", "1000", "£1,000", "£1000", "1 000", "1,000 pounds", "1000 pounds", "one thousand",
                          "a thousand"),
                       ok("499", "£499", "499 pounds"),
                       ok("400", "£400", "400 pounds", "four hundred"),
                       ok("399", "£399", "399 pounds")], 1):
    K[("3.1", n, 1)] = Q(a)
for n, a in enumerate(["lend", "borrow", "afford", ok("loan", articles=True), "owe",
                       ok("pay back", "pay it back", "pay the money back"), ok("save up", "save"),
                       ok("discount", articles=True), ok("bargain", articles=True),
                       ok("special offer", articles=True)], 1):
    K[("3.2", n, 1)] = Q(a)
K[("3.3", 1, 1)] = Q("lend")
K[("3.3", 2, 1)] = Q("spent")
K[("3.3", 3, 1)] = Q("borrowed")
K[("3.3", 4, 1)] = Q(exact("costs", "cost"))
K[("3.3", 4, 2)] = Q("afford")
K[("3.3", 5, 1)] = Q("owe")
K[("3.3", 6, 1)] = Q("cost")
K[("3.3", 7, 1)] = Q(ok("borrowed", "has borrowed", "'s borrowed", "had borrowed"))
for n, a in enumerate([exact("in", "with"), exact("by", "with"), "for", "from", "to", "on",
                       exact("in", "at"), "on"], 1):
    K[("3.4", n, 1)] = Q(a)
for n, a in enumerate(["payment", "savings", "affordable", "seller", "sale"], 1):
    K[("3.5", n, 1)] = Q(a)
K[("3.6", 1, 1)] = own()

for n, a in enumerate([ok("7 o'clock", "seven o'clock", "7", "seven", "7 pm", "7 p.m.", "7pm", "7.00", "7:00",
                          "19:00", "19.00", "7 in the evening", "seven in the evening", "7 o'clock last night"),
                       ok("13", "thirteen", "13 hours", "thirteen hours"),
                       ok("one-pound", "one pound", "£1", "1 pound", "1-pound", "£1.00", "1£", "a one-pound",
                          "a one pound", "a £1", "one-pound T-shirt", "£1 T-shirt"),
                       ok("chair", articles=True),
                       ok("cups", "cup", "four cups", "4 cups"),
                       ok("75", "£75", "75 pounds", "seventy-five"),
                       ok("25", "£25", "25 pounds", "twenty-five"),
                       ok("100", "£100", "100 pounds", "a hundred", "one hundred"),
                       ok("midnight", "about midnight", "12", "twelve", "12 o'clock", "twelve o'clock",
                          "12 midnight", "12 am", "12 a.m.", "00:00", "0:00", "24:00"),
                       ok("8", "eight", "8 hours", "eight hours")], 1):
    K[("4.1", n, 1)] = Q(a)
for n, a in enumerate("MKJMKJ", 1):
    K[("4.2", n, 1)] = choose(["M", "K", "J"], a)
K[("4.3", 1, 1)] = own()
K[("4.4", 1, 1)] = own()
K[("4.5", 1, 1)] = own()

for n, a in enumerate([ok("Leo's", "Leo", "Leo's birthday", "it's Leo's", "it's Leo's birthday", "it is Leo's"),
                       ok("Annie", "Annie did", "Annie told them"),
                       ok("something fun", "something funny", "a fun present", "a fun thing", "fun",
                          "something sporty", "sporty", "a sporty present", "something fun and sporty"),
                       ok("on your fingers", "your fingers", "on the fingers", "fingers", "on fingers",
                          "on his fingers", "on my fingers"),
                       ok("an alarm clock", "alarm clock", "an alarm", "alarm"),
                       ok("money", "your money", "their money", "his money"),
                       ok("a football clock", "football clock", "the football clock"),
                       ok("football", "about football", "talking about football")], 1):
    K[("5.1", n, 1)] = Q(a)
for n, a in enumerate(["SA", "C", "SA", "SA", "C", "C", "C", "C"], 1):
    K[("5.2", n, 1)] = choose(["SA", "C"], a)
for (n, box), a in {(1, 1): "to", (1, 2): "a", (2, 1): "me", (3, 1): "for", (3, 2): "a", (3, 3): "for",
                    (4, 1): "in", (4, 2): "a", (5, 1): "a", (5, 2): "of"}.items():
    K[("5.3", n, box)] = Q(a)
for n, a in enumerate("31742856", 1):             # a b c d e f g h
    K[("5.4", n, 1)] = choose(list("12345678"), a)
for n in range(1, 4):                             # many right ways to change your mind: his to read
    K[("5.5", n, 1)] = own()
K[("5.6", 1, 1)] = own(control="essay")

for n in range(1, 4):                             # notes, not sentences
    K[("6.1", n, 1)] = None
for n in range(4, 7):                             # the three checks before sending the recording
    K[("6.1", n, 1)] = tick()
K[("6.2", 1, 1)] = Q(ok("It is better to shop in a real shop", "it's better to shop in a real shop",
                        "it is better to shop in a shop", "shopping in a real shop is better", "a real shop is better",
                        "real shops are better", "shops are better", "in a real shop", "a real shop", "real shop",
                        "shop in a real shop", "shopping in a real shop", "in a shop", "a shop is better",
                        "better to shop in a real shop", "better to shop in a shop", "shopping in a shop is better",
                        limit=200))
K[("6.2", 2, 1)] = Q(ok("Firstly, Secondly", "Firstly and Secondly", "Firstly and secondly",
                        "Firstly secondly", "Firstly; Secondly", "firstly, secondly", "Firstly - Secondly",
                        "Firstly — Secondly", "Firstly & Secondly", "Firstly, and Secondly"))
K[("6.2", 3, 1)] = None                           # two sentences copied from the model: his to read
K[("6.2", 4, 1)] = Q(ok("To sum up", "to sum up"))
for n in range(1, 4):                             # the plan: notes
    K[("6.3", n, 1)] = None
K[("6.4", 1, 1)] = own(control="essay")

if __name__ == "__main__":
    data = h.build(K, "Pre-Intermediate", 3, "Unit 3A & 3C — Money")
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "p03ac_new.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
