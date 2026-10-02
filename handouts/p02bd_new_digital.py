"""P02BD Travel and tourism - the new-style Pre-Intermediate booklet (2B & 2D), done on a phone.

It replaces "Unit 2B & 2D - Travel and tourism" (test 85, p02bd_digital.py), the
older design; the exercises are all new, so no answers carry across. Built like
p02ac_new_digital.py: a TEAL build of the booklet (BOOK_THEME=teal node
build_p02bd.js), the one-page tables unwrapped, Uzbek goals, instruction lines
and explanations.

The key is written with variants.ok, so every box that marks itself takes every
form of a right answer (he found right answers marked wrong, 2026-10-02), and
where two answers are both right English the box takes both:
  - 2.4 and 5.4: a sentence joined with when / while in either order, with or
    without the comma;
  - 2.8: *When I was waiting …* as well as *While …*; 3.5: *get on / off* the bus
    and the train (both are true), *drove off / away*, *get in / into* the taxi;
    5.3: *and* where *so* is the key but *and* is also good English.
5.2 (the words after each linking word in the model) is his to read: several
places in the model are right.

What a phone gets that paper does not:
  - taps: the headings (1.2), TRUE / FALSE / NOT GIVEN (1.3), the two options
    in each 2.3 sentence, weak or strong (2.9), the verb that does not fit
    (3.4 - "cross it out" on paper), the order of events (4.1), the checks
    before sending the recording (4.7);
  - a box per item where paper has ruled lines; 2.7's mistake (not marked)
    then its correction (marked).

    python3 handouts/p02bd_new_digital.py       # writes handouts/p02bd_new.json, lists every box
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
        "P02BD Travel and tourism — BOOKLET (teal, for the website).docx")
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


def joined(cont, simple, extra=()):
    """A past continuous action and the past simple one that stopped it, joined with
    when or while in every order a good sentence can take."""
    forms = ["%s when %s" % (cont, simple), "When %s, %s" % (cont, simple), "When %s %s" % (cont, simple),
             "While %s, %s" % (cont, simple), "While %s %s" % (cont, simple),
             "%s while %s" % (simple, cont), "%s when %s" % (simple, cont)]
    return ok(*(forms + list(extra)), limit=200)


# ------------------------------------------------------------ 1 Reading
for n in range(1, 9):
    h.item_box("1.3", n, where="leader")
h.leaders("1.5", "Grammar  ·", [(1, W, "Your answer")])

# ------------------------------------------------------------ 2 Grammar
h.leaders("2.2", "2.3  </span>", [(n, W, "What was he or she doing?") for n in range(1, 3)])
for n in range(1, 7):                             # two choices in each sentence
    h.item_box("2.3", n, width="60px")
    h.item_box("2.3", n, width="60px")
h.leaders("2.4", "2.5  </span>", [(n, W, "One sentence with when or while") for n in range(1, 5)])
h.leaders("2.6", "2.7  </span>", [(1, W, "Three sentences")])
h.leaders("2.10", "Vocabulary  ·", [(1, W, "Four sentences about a journey")])

# ------------------------------------------------------------ 3 Vocabulary
reword("3.4", "Which verb does NOT go with the words? Cross it out.",
       "Which verb does NOT go with the words? Tap it.")
for n in range(1, 9):
    h.item_box("3.4", n, width="60px")
h.leaders("3.6", "Listening and speaking  ·", [(1, W, "Two sentences")])

# ------------------------------------------------- 4 Listening and speaking
h.leaders("4.4", "4.5  </span>", [(1, W, "True or not? Two reasons")])

# ------------------------------------------------------------ 5 Writing
h.leaders("5.1", "5.2  </span>", [(1, W, "Title, date, two feelings, a question")])
h.leaders("5.4", "5.5  </span>", [(n, W, "One sentence") for n in range(1, 6)])
h.leaders("5.6", "</div>", [(1, W, "Write your blog post here")])

# ------------------------------- every instruction, once more, in Uzbek
for label, text in [
        ("1.1", "Oʻqishdan oldin. Siz yoki oilangiz uchun yomon ketgan bir safarni eslang. Nima boʻldi?"),
        ("1.2", "B–E xatboshilar uchun toʻgʻri sarlavhani tanlang. Ikkita sarlavha ortiqcha."),
        ("1.3", "Gaplar matnga mos keladimi? *TRUE* (toʻgʻri), *FALSE* (notoʻgʻri) yoki *NOT GIVEN* (matnda bu haqda "
                "hech narsa yoʻq) ni tanlang."),
        ("1.4", "C xatboshining qisqacha mazmunini toʻldiring. Matndan IKKI SOʻZDAN KOʻP BOʻLMAGAN soʻz va/yoki son "
                "yozing."),
        ("1.5", "Dalil haqida oʻylang. D xatboshida Yaponiyada odamlar poyezdlar oʻz vaqtida yurishini kutishi "
                "aytilgan. Buni qaysi fakt tasdiqlaydi? Bitta voqea yetarlimi? Nima yordam beradi?"),
        ("2.1", "Qavsdagi feʼlning Past Continuous shakli bilan toʻldiring."),
        ("2.2", "Soat 7 da aeroportga taksi eshik oldida edi. Karimovlar nima qilayotgan edi?"),
        ("2.3", "Past Simple mi yoki Past Continuous mi? Toʻgʻri variantni tanlang."),
        ("2.4", "Gaplarni *when* yoki *while* bilan bogʻlang. Past Simple va Past Continuous ishlating."),
        ("2.5", "Jasurning hikoyasini qavsdagi feʼllar bilan Past Simple yoki Past Continuous da toʻldiring."),
        ("2.6", "Oʻylang. Kul buluti aeroportlarni yopganda Yevropada boʻlganingizni tasavvur qiling. Uchta gap yozing: "
                "nima qilayotgan edingiz va keyin nima qildingiz?"),
        ("2.7", "Kamolaning xabarida BESHTA xato bor. Avval xatoni, keyin toʻgʻrisini yozing."),
        ("2.8", "*when* mi yoki *while* mi? Gaplarni toʻldiring."),
        ("2.9", "Talaffuz. 2.14 va 2.15-treklarni tinglang. *was / were* kuchsiz (*W*) mi yoki *wasn't / weren't* "
                "kuchli (*S*) mi? Keyin gaplarni ayting."),
        ("2.10", "Endi siz. Esingizda qolgan bir safar haqida yozing: biror narsa sodir boʻlganda nima boʻlayotgan "
                 "edi (toʻrtta gap)."),
        ("3.1", "Sardorning postini oʻqing. Qalin yozilgan iboralarga qarang."),
        ("3.2", "Ramkadagi feʼllarning toʻgʻri shakli bilan toʻldiring."),
        ("3.3", "*There was / were* + muammo. Toʻldiring."),
        ("3.4", "Qaysi feʼl bu soʻzlar bilan ishlatilMAYDI? Uni tanlang."),
        ("3.5", "Har bir gapni BITTA soʻz bilan toʻldiring."),
        ("3.6", "Oʻylang. Sizningcha, bu boʻlimdagi qaysi safar muammosi eng yomoni? Nega? Ikkita gap yozing."),
        ("4.1", "Voqealarni sodir boʻlgan tartibda raqamlang (*1–6*)."),
        ("4.2", "Savollarga javob bering. UCH SOʻZ VA/YOKI SONDAN KOʻP yozmang."),
        ("4.3", "Hikoyadagi gaplarni (2.12-trek) Past Simple yoki Past Continuous bilan toʻldiring."),
        ("4.4", "Oʻylang. Sizningcha, bu hikoya rostmi? Ikkita sabab keltiring."),
        ("4.5", "Qaydlarni toʻldiring. IKKI SOʻZ VA/YOKI SONDAN KOʻP yozmang."),
        ("4.6", "Keti kelishini eslaydi. Past Continuous bilan toʻldiring, keyin tekshirish uchun yana tinglang."),
        ("4.7", "Har bir band uchun qayd yozing. Keyin oʻzingizni yozib oling: taxminan bir daqiqa gapiring va "
                "yozuvni oʻqituvchingizga yuboring."),
        ("5.1", "Blog post — xat emas. Namunadan toping: sarlavha, sana, ikkita his va oʻquvchilarga bitta savol."),
        ("5.2", "Namunadan har bir bogʻlovchi soʻzga BITTA misol toping. Undan keyin keladigan soʻzlarni yozing."),
        ("5.3", "*and*, *but*, *so*, *because* yoki *when* bilan toʻldiring."),
        ("5.4", "Ikki gapni qavsdagi soʻz bilan bogʻlab, bitta gap yozing."),
        ("5.5", "Safarning birinchi kuni haqida blog post rejalashtiring — haqiqiy safar yoki qilmoqchi boʻlgan "
                "safaringiz. Faqat qaydlar."),
        ("5.6", "Blog postingizni yozing (100–130 soʻz). 5.5 dagi reja, toʻrtta qisqa xatboshi, Past Simple va Past "
                "Continuous hamda *and*, *but*, *so*, *because* va *when* dan kamida bir martadan foydalaning.")]:
    h.say_also(label, text)

# ------------------------------------------ the explanations, told in Uzbek
h.retell("KEY WORDS", "KALIT SOʻZLAR", [
    "**to erupt**  (vulqon haqida) otilmoq — olov va kul chiqarmoq",
    "**ash**  kul — olov yoki vulqondan chiqadigan kulrang kukun",
    "**to cancel**  bekor qilmoq",
    "**stuck**  qolib ketgan — harakatlana olmaydigan",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — PAST CONTINUOUS", [          # the first of the two
    "[[A]] **Shakl:** *was / were* + *-ing*. *It was raining. · The passengers were waiting. · I wasn't listening. · "
    "Were you sleeping?*",
    "[[B]] **Davom etayotgan harakatni qisqaroq harakat (Past Simple) toʻxtatadi:** *I was reading my book when the "
    "flight attendant spoke to me. · While we were driving to the airport, the car broke down.*",
    "[[C]] **Hikoyaning fonida:** *It was raining, and people were hurrying to the station. Then I saw …* **Bir vaqtda "
    "boʻlgan ikki uzun harakat:** *While I was packing, my brother was sleeping.*",
    "[[D]] **Istisnolar.** *while* + Past Continuous, lekin qisqa harakat bilan *when*: *when the plane landed* — "
    "*while the plane landed* emas. Holat feʼllari (*know, like, want, believe*) Continuous da ishlatilmaydi: *I "
    "didn't know the way.* Zamon hikoyani oʻzgartiradi: *When we arrived, the train left* (biz keldik, keyin u "
    "ketdi) ≠ *When we arrived, the train was leaving* (u allaqachon joʻnayotgan edi).",
])
h.retell("WATCH OUT!", "DIQQAT — KOʻP UCHRAYDIGAN XATOLAR", [
    "1 ✗ *I was read a book when …* → ✓ *I was reading …* — *was* + *-ing*.",
    "2 ✗ *We was waiting for the bus.* → ✓ *We were waiting …*",
    "3 ✗ *I am walking home yesterday when …* → ✓ *I was walking …* — hozirgi emas, oʻtgan zamon.",
    "4 ✗ *While the plane landed, I was sleeping.* → ✓ *When the plane landed, …*",
    "5 ✗ *I wasn't knowing the way.* → ✓ *I didn't know the way.* — holat feʼli.",
])
h.retell("WORDPOWER — OFF", "WORDPOWER — OFF", [
    "**bir joydan uzoqlashish:** *set off · drive off · I'm off!* (= ketyapman) · **kattaroq narsadan ajralish:** "
    "*take off* (samolyot; kiyimni yechmoq) · *fall off · get off the bus · 20% off* (arzonroq)",
    "**quvvat yoʻq:** *turn off the lights · The electricity was off.* · avtobus, poyezd, samolyot bilan **get on / "
    "off** — lekin mashina yoki taksi bilan **get in / out of** · **by** car / bus / train — lekin **on foot**",
])
h.retell("ERROR WARNING", "DIQQAT — SAFAR IBORALARIDAGI XATOLAR", [
    "✗ *We lost the train.* → ✓ *missed the train* · ✗ *We arrived to the station.* → ✓ *arrived at / got to*",
    "✗ *I go to school by foot.* → ✓ *on foot* · ✗ *The plane flied up.* → ✓ *took off* · ✗ *Get in the bus!* → ✓ "
    "*get on*",
    "✗ *We were in the plane for six hours.* → ✓ *on the plane* (samolyot, poyezd, avtobusda — *on*)",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [                 # the first of the two
    "Darslikdagi **2.11-trek**ni tinglang (2-unit, 2B dars). Bir ayol Istanbulga uchgan samolyotdagi voqeani "
    "hikoya qiladi.",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [
    "Darslikdagi **2.24-trek**ni tinglang (2-unit, 2D dars). Limalik Lusila Sidneyga koʻchib ketyapti. Uning dugonasi "
    "Keti u yerda allaqachon yashaydi.",
])
h.retell("PRESENTATION — LINKING WORDS", "TUSHUNTIRISH — BOGʻLOVCHI SOʻZLAR", [
    "[[A]] **and** qoʻshadi: *The hotel is small and clean.* **but** qarama-qarshilikni bildiradi: *The flight was "
    "long, but I slept.*",
    "[[B]] **so** natijani bildiradi: *It was windy, so I lost my hat.* **because** sababni bildiradi: *We took a "
    "ferry because I wanted to see Asia.*",
    "[[C]] **when** vaqtni bildiradi: *When we were crossing, the wind was strong.* *but* va *so* dan oldin odatda "
    "vergul qoʻyiladi — *because* dan oldin emas.",
    "[[D]] **Sayohat blogi:** sarlavha va sana · qisqa xatboshilar · nima qildingiz, nimani koʻrdingiz va oʻzingizni "
    "qanday his qildingiz · samimiy til · oxirida ertangi rejalar.",
])

# --------------------- the goals, in Uzbek, where the site's cover reads them
GOALS = [
    "yomon ketgan safarlar haqidagi matnni tushunishni",
    "Past Continuous ni Past Simple bilan ishlatishni: *when* va *while*",
    "safar muammolarini va *off* bilan iboralarni",
    "samolyotdagi voqea va yangi shahar haqidagi suhbatni tushunishni",
    "*and, but, so, because, when* bilan gaplarni bogʻlashni",
    "sayohat blogi yozishni",
]
first_bar = bh_section_at().search(h.html).start()
h.html = (h.html[:first_bar] + '<table class="bk"><tr><td><p><span>You will learn to</span></p>'
          + "".join('<p><span>—  </span>%s</p>' % told(g, bare=True) for g in GOALS)
          + "</td></tr></table>" + h.html[first_bar:])

# ------------------------------------------------------------------ the key
K = {}
TFNG = ["TRUE", "FALSE", "NOT GIVEN"]
ROMAN = ["i", "ii", "iii", "iv", "v", "vi"]
K[("1.1", 1, 1)] = own()
for n, a in enumerate(["iv", "i", "iii", "vi"], 1):
    K[("1.2", n, 1)] = choose(ROMAN, a)
for n, a in enumerate(["FALSE", "TRUE", "FALSE", "NOT GIVEN", "TRUE", "FALSE", "NOT GIVEN", "FALSE"], 1):
    K[("1.3", n, 1)] = choose(TFNG, a)
for n, a in enumerate([ok("August", "in August"),
                       ok("Beijing"),
                       ok("100 kilometres", "100", numbers=True, units=True),
                       ok("twelve days", "12", numbers=True),
                       ok("one kilometre", "1 kilometre", "a kilometre", "one", numbers=True, units=True),
                       ok("water", "bottles of water", "drinking water")], 1):
    K[("1.4", n, 1)] = Q(a)
K[("1.5", 1, 1)] = own()

for (n, k), a in {(1, 1): ok("was waiting"), (2, 1): ok("was snowing"),
                  (3, 1): ok("weren't sleeping"), (4, 1): "were", (4, 2): "doing",
                  (5, 1): ok("were standing"), (6, 1): "Was", (6, 2): "listening"}.items():
    K[("2.1", n, k)] = Q(a)
K[("2.2", 1, 1)] = write(ok("Mum was looking for the passports", "Mum was looking for passports",
                            "Mum was looking for their passports", "Mom was looking for the passports",
                            "Mother was looking for the passports", "His mum was looking for the passports",
                            "She was looking for the passports"))
K[("2.2", 2, 1)] = write(ok("Aziz and Lola were still sleeping", "Aziz and Lola were sleeping",
                            "Aziz and Lola were still asleep", "Lola and Aziz were still sleeping",
                            "They were still sleeping", "Aziz and Lola were still sleeping in bed",
                            "Aziz and Lola still were sleeping"))
for n, (first, second) in enumerate([(["waited", "were waiting"], ["started", "was starting"]),
                                     (["packed", "was packing"], ["rang", "was ringing"]),
                                     (["landed", "was landing"], ["got", "were getting"]),
                                     (["slept", "was sleeping"], ["arrived", "was arriving"]),
                                     (["started", "was starting"], ["travelled", "were travelling"]),
                                     (["didn't know", "wasn't knowing"], ["got", "was getting"])], 1):
    ans = ["were waiting", "was packing", "landed", "was sleeping", "started", "didn't know"][n - 1]
    ans2 = ["started", "rang", "got", "arrived", "were travelling", "got"][n - 1]
    K[("2.3", n, 1)] = choose(first, ans)
    K[("2.3", n, 2)] = choose(second, ans2)
for n, a in enumerate([joined("we were driving to the airport", "the car broke down"),
                       joined("the flight attendant was bringing the food", "the turbulence started"),
                       joined("Malika was buying a ticket", "she lost her passport",
                              ["Malika lost her passport while she was buying a ticket",
                               "Malika lost her passport when she was buying a ticket",
                               "While she was buying a ticket, Malika lost her passport",
                               "When she was buying a ticket, Malika lost her passport"]),
                       joined("they were sleeping", "the train stopped in the middle of the desert")], 1):
    K[("2.4", n, 1)] = write(a)
for n, a in enumerate([ok("was travelling", "was traveling"), ok("was snowing"), "got", ok("were waiting"),
                       ok("cancelled", "canceled"), ok("was looking"), "met", ok("talked", "were talking"),
                       "took off", "were"], 1):
    K[("2.5", n, 1)] = Q(a)
K[("2.6", 1, 1)] = own()
FIXED = [ok("I was driving", "was driving", "I was driving to Samarkand"),
         ok("We were listening", "were listening", "We were listening to music"),
         ok("When we arrived", "When", "When we arrived, it was raining"),
         ok("I didn't know", "didn't know", "I didn't know the way", "I didn't know the way to the hotel"),
         ok("when we found it", "we found it", "found", "When we found it, it was very late", "found it")]
for n, a in enumerate(FIXED, 1):
    K[("2.7", n, 1)] = None                       # the mistake as they found it: theirs, not marked
    K[("2.7", n, 2)] = write(a, control=None)
for n, a in enumerate([ok("While", "When"), "when", "When", ok("while", "when"), ok("While", "When"), "when",
                       ok("While", "When")], 1):
    K[("2.8", n, 1)] = Q(a)
WS = {"W": "W · weak", "S": "S · strong"}
for n, a in enumerate("WSWSWS", 1):
    K[("2.9", n, 1)] = choose(["W", "S"], a, labels=WS)
K[("2.10", 1, 1)] = own()

for (n, k), a in {(1, 1): "set off", (2, 1): "landed", (3, 1): "broke down", (4, 1): "miss", (5, 1): "board",
                  (6, 1): "got lost", (7, 1): "give", (7, 2): ok("a lift", "lift"), (8, 1): "get to",
                  (9, 1): "land"}.items():
    K[("3.2", n, k)] = Q(a)
for n, a in enumerate([ok("a traffic jam", "traffic jam", "a big traffic jam"),
                       ok("a strike", "strike"),
                       ok("a long queue", "long queue", "a queue", "a long line"),
                       ok("something wrong with", "something wrong with the", "a problem with"),
                       ok("a lot of turbulence", "lots of turbulence", "turbulence", "much turbulence"),
                       ok("a delay", "delay"),
                       ok("a strike", "strike")], 1):
    K[("3.3", n, 1)] = Q(a)
for n, (opts, a) in enumerate([(["miss", "lose", "catch"], "lose"), (["give", "get", "make"], "make"),
                               (["get", "be", "make"], "make"), (["set", "take", "board"], "board"),
                               (["board", "miss", "drive"], "drive"), (["have", "make", "be in"], "make"),
                               (["get to", "arrive", "reach"], "arrive"), (["get on", "get off", "get in"], "get in")],
                              1):
    K[("3.4", n, 1)] = choose(opts, a)
for n, a in enumerate([ok("off", "on"), ok("off", "on"), "off", "off", "on", ok("in", "into"), "by", "off",
                       ok("off", "away"), ok("off", "on")], 1):
    K[("3.5", n, 1)] = Q(a)
K[("3.6", 1, 1)] = own()

for n, a in enumerate("416253", 1):
    K[("4.1", n, 1)] = choose(list("123456"), a)
for n, a in enumerate([ok("check in", "check-in", "checkin", "check in for the flight"),
                       ok("the toilet", "toilet", "in the toilet", "on the toilet", "the plane's toilet",
                          "in the plane's toilet", "the bathroom", "in the bathroom"),
                       ok("a seatbelt", "seatbelt", "a seat belt", "seat belt", "seatbelts", "a belt", "seat-belt"),
                       ok("about five", "five", "about five passengers", "five passengers", "around five",
                          numbers=True),
                       ok("an hour", "one hour", "about an hour", "1 hour", "a hour", "an hour's delay", numbers=True),
                       ok("a joke", "joke", "just a joke")], 1):
    K[("4.2", n, 1)] = Q(a)
for (n, k), a in {(1, 1): ok("was raining"), (1, 2): "left", (2, 1): "boarded", (2, 2): ok("were waiting"),
                  (3, 1): ok("was reading"), (3, 2): "spoke", (4, 1): ok("was sitting"), (4, 2): "started"}.items():
    K[("4.3", n, k)] = Q(a)
K[("4.4", 1, 1)] = own()
for n, a in enumerate([ok("five", "5", "five o'clock", "5 o'clock", "5 pm", "5 p.m.", "five pm", "17:00", "5:00",
                          "about five", "about 5", "5.00", "five p.m."),
                       ok("six", "6", "six o'clock", "6 o'clock", "6 pm", "6 p.m.", "six pm", "18:00", "6:00", "6.00",
                          "six p.m."),
                       ok("Central Station", "Central", "the Central Station", "Central station", "the central station",
                          "Sydney Central Station"),
                       ok("four months", "4 months", "four month"),
                       ok("Harbour Bridge", "Sydney Harbour Bridge", "the Harbour Bridge", "Harbor Bridge", "bridge",
                          "harbour bridge"),
                       ok("Birmingham", "from Birmingham", "Birmingham, UK", "Birmingham in the UK"),
                       ok("concert hall", "a concert hall", "great concert hall", "concert hall with live music"),
                       ok("housemates", "house mates", "house-mates", "housemate", "a housemate")], 1):
    K[("4.5", n, 1)] = Q(a)
K[("4.6", 1, 1)] = Q(ok("were landing"))
K[("4.6", 2, 1)] = Q(ok("was feeling"))
for n in range(1, 5):                             # notes, not sentences
    K[("4.7", n, 1)] = None
for n in range(5, 8):                             # the three checks before sending the recording
    K[("4.7", n, 1)] = tick()

K[("5.1", 1, 1)] = own()
for n in range(1, 7):                             # several places in the model are right: his to read
    K[("5.2", n, 1)] = None
for n, a in enumerate([ok("so", "and"), ok("because", "when"), "and", "When", "but", ok("so", "and"), "because",
                       "but"], 1):
    K[("5.3", n, 1)] = Q(a)
for n, a in enumerate([
        ok("The ferry was cheap, but it was very slow", "The ferry was cheap but it was very slow",
           "The ferry was cheap, but very slow", "The ferry was cheap but very slow",
           "The ferry was cheap, but it was slow", "The ferry was cheap but slow"),
        ok("I was hungry, so I bought some simit", "I was hungry so I bought some simit",
           "I was hungry, so I bought simit", "I was hungry so I bought simit"),
        joined("we were walking to the bazaar", "it started to rain",
               ["We were walking to the bazaar, when it started to rain"]),
        ok("We stayed in a hostel because hotels were too expensive",
           "We stayed in a hostel, because hotels were too expensive",
           "Because hotels were too expensive, we stayed in a hostel",
           "Because hotels were too expensive we stayed in a hostel",
           "We stayed in a hostel because the hotels were too expensive"),
        ok("The bazaar was crowded and very colourful", "The bazaar was crowded and it was very colourful",
           "The bazaar was crowded, and it was very colourful", "The bazaar was crowded, and very colourful",
           "The bazaar was very crowded and very colourful", "The bazaar was crowded and colourful")], 1):
    K[("5.4", n, 1)] = write(a)
K[("5.5", 1, 1)] = None                           # the plan: title + date, then paragraphs 1-4
K[("5.5", 1, 2)] = None
for n in range(2, 5):
    K[("5.5", n, 1)] = None
K[("5.6", 1, 1)] = own(control="essay")

if __name__ == "__main__":
    data = h.build(K, "Pre-Intermediate", 2, "Unit 2B & 2D — Travel and tourism")
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "p02bd_new.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
