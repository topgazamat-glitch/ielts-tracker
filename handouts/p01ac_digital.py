"""P01AC Communication - Azamat's Pre-Intermediate booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(P01AC Communication - answer key), joined box by box by hand. Every
explanation is told again in Uzbek, with the English examples kept, and
every instruction has a line in Uzbek under it; the reading, the texts to
fill in and the exercises stay English.

Three things in the booklet are put right here, since a page that marks
itself cannot be wrong about its own answers:
  - 2.3 lists do, does, did, is, are or was, but its key wants were (6) and
    have (8) as well - the list now has them;
  - 2.5 says TWO sentences are correct; the key has three (3, 6, 8);
  - the stress on delicious and fantastic is marked DE-li-cious and
    FAN-tastic in the boxes, but de-LI-cious and fan-TAS-tic in the key
    and in 3.5 - the boxes now agree with the key.

What a phone gets that paper does not:
  - taps for every choice: A/B/C, good or bad question, the rule kept or
    not, be or do, subject or object, +/-/=, the adjectives in the box,
    very or really, the stressed syllable, 1/2/3, the replies in 5.3, the
    loudest word, who a greeting is for;
  - boxes where paper has none: 2.8's five corrections, 3.4, 3.5, 5.3, 5.5.

    python3 handouts/p01ac_digital.py            # writes handouts/p01ac.json, lists every box
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import (Handout, Q, choose, tick, own, write, fix, number, report,   # noqa: E402
                     BLANK_TAG, plain, ITEM_STYLE, NUM_SPAN, TEXT_SPAN)

DOCX = ("~/Desktop/Handouts/B1 Pre-Intermediate/P01AC Communication/"
        "P01AC Communication — handout (new design).docx")
W = "95%"
YES_NO = ["✓", "✗"]

h = Handout(DOCX)
TAGS = {int(m.group(1)): m.group(0) for m in BLANK_TAG.finditer(h.html)}


def section(label):
    """Where an exercise begins and the next one does."""
    return h.html.index("%s  </span>" % label)


def item_p(label, n, text_html, token):
    h.texts[(label, n)] = plain(text_html)
    return ('<p data-item="%s:%d" %s>%s%s</p>'
            % (label, n, ITEM_STYLE, NUM_SPAN % n, TEXT_SPAN % ("%s  %s" % (text_html, token))))


def replace_table_after(label, new):
    """Swap the first table after an exercise's instruction for `new`."""
    at = section(label)
    a = h.html.index('<table class="bk">', at)
    b = h.html.index("</table>", a) + len("</table>")
    old = h.html[a:b]
    h.html = h.html[:a] + new + h.html[b:]
    return old


def key_list(pairs):
    return ('<table class="bk"><tr><td style="vertical-align:top;background:#F2F8F8;'
            'border-left:3px solid #127D80">'
            + "".join('<p style="margin:0"><span style="font-weight:700;color:#127D80">%s</span>  %s</p>'
                      % (l, html.escape(t, quote=False)) for l, t in pairs)
            + "</td></tr></table>")


def words_of(label, n):
    m = next(m for m in h._items(label) if int(m.group(3)) == n)
    return [w.strip("?!.,") for w in re.sub(r"^\d+\s+", "", plain(m.group(4))).split() if w.strip("?!.,")]


# ------------------------------------------------------------ 1 Reading
h.options_on_lines("1.2")
for n in range(1, 6):
    h.item_box("1.2", n, where="options")
for n in range(1, 5):
    h.item_box("1.3", n, where="leader")
for n in range(1, 5):
    h.item_box("1.4", n, width="190px", where="leader")

# ------------------------------------------------------------ 2 Grammar
# 2.1: the gap in each question is only there to show where the verb goes;
# what the student gives is B or D
for i in (10, 11, 13, 15, 17, 19):
    h.html = h.html.replace(TAGS[i], "……", 1)
# 2.3: the list of words, as the key needs it
B_ = '<span style="font-weight:700;color:#1A1A1A;font-size:11.5pt">%s</span>'
I_ = '<span style="font-weight:700;font-style:italic;color:#1A1A1A;font-size:11.5pt">%s</span>'
a = section("2.3") + len("2.3  </span>")
b = h.html.index("</p>", a)
words = ["do", "does", "did", "is", "are", "was", "were"]
h.html = (h.html[:a] + B_ % "Complete with " + (B_ % ", ").join(I_ % w for w in words)
          + B_ % " or " + I_ % "have" + B_ % "." + h.html[b:])
# 2.5: three sentences are correct, not two
a = section("2.5")
b = h.html.index("</p>", a)
h.html = h.html[:a] + h.html[a:b].replace("TWO", "THREE", 1) + h.html[b:]
for n in range(2, 9):                             # item 1 is the worked example
    h.item_box("2.5", n)
# 2.8: the five questions, corrected, in the order they come
t = h.html.index("AT THE LANGUAGE CENTRE")
inner_end = h.html.index("</table>", t) + len("</table>")
outer_end = h.html.index("</table>", inner_end) + len("</table>")
boxes = '<p style="margin:6px 0 4px;padding-left:32px"><span style="font-style:italic">' \
        'Write the five questions, corrected, in the order they come.</span></p>'
for n in range(1, 6):
    boxes += item_p("2.8", n, "Mistake %d:" % n, "{{box:2.8:%d:95%%:Corrected question}}" % n)
h.html = h.html[:outer_end] + boxes + h.html[outer_end:]

# ------------------------------------------------------------ 3 Vocabulary
for n in range(1, 7):
    h.item_box("3.4", n)                          # very / really, to tap
SYLL = {}
for m in h._items("3.5"):                         # the syllables are the choice
    n = int(m.group(3))
    SYLL[n] = re.sub(r"^\d+\s+", "", plain(m.group(4))).split("-")
for n in sorted(SYLL):
    h.item_box("3.5", n)
for n in range(1, 5):
    h.item_box("3.7", n, where="leader")

# ------------------------------------------------------------ 4 Listening
h.leaders("4.3", "4.4  </span>", [(1, W, "Who, and why?")])
h.leaders("4.5", "WHY YOU DIDN", [(n, W, "Question %d" % n) for n in range(1, 5)])
h.options_on_lines("4.8")
for n in (1, 2, 3):
    h.item_box("4.8", n)

# ------------------------------------------------------ 5 Everyday English
# 5.2: each phrase from 5.1, and who it is for - the paper's two columns do
# not hold four and two
GREETINGS = ["Long time no see!", "How are you?", "Great to see you!", "Where are you living these days?",
             "My name's Mark, by the way.", "Nice to meet you."]
replace_table_after("5.2", "".join(item_p("5.2", n, html.escape(g, quote=False), "{{box:5.2:%d:60px:}}" % n)
                                   for n, g in enumerate(GREETINGS, 1)))
# 5.3: the replies first, as a key; then each greeting, with a-e to tap
old = replace_table_after("5.3", "{{5.3}}")
cells = [plain(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", old, re.S)]
pairs = [(cells[k], cells[k + 1]) for k in range(2, len(cells) - 1, 2) if cells[k]]
greet = [re.match(r"(\d+)\s+(.*)", g).groups() for g, _r in pairs]
replies = sorted(re.match(r"([a-e])\s+(.*)", r).groups() for _g, r in pairs)
h.html = h.html.replace("{{5.3}}", key_list(replies) + "".join(
    item_p("5.3", int(n), html.escape(g, quote=False), "{{box:5.3:%s:60px:}}" % n) for n, g in greet))
LOUD = {}
for m in h._items("5.5"):
    LOUD[int(m.group(3))] = words_of("5.5", int(m.group(3)))
for n in sorted(LOUD):
    h.item_box("5.5", n)
for n in range(1, 5):
    h.item_box("5.8", n, where="leader")
h.leaders("5.9", "CHECK BEFORE", [(20, W, "Write your conversation here")])

# ------------------------------- every instruction, once more, in Uzbek
for label, text in [
        ("1.1", "Muhokama qiling. Yangi odamlar bilan odatda qayerda tanishasiz? Odatda birinchi qanday savol "
                "berasiz?"),
        ("1.2", "Eng toʻgʻri javobni tanlang: *A*, *B* yoki *C*."),
        ("1.3", "Oʻz soʻzlaringiz bilan javob bering."),
        ("1.4", "Matndan shu maʼnodagi soʻz yoki iborani toping."),
        ("1.5", "Yaxshi birinchi savolmi (*G*) yoki yomon birinchi savolmi (*B*)? Tanlang va nega ekanini ayting."),
        ("1.6", "Toʻrtta qisqa suhbatni oʻqing. Ikkinchi gapiruvchi qoidaga amal qildimi? *✓* yoki *✗* ni tanlang."),
        ("2.1", "*be* mi (*B*) yoki *do / does / did* mi (*D*)? Tanlang."),
        ("2.2", "Soʻzlarni toʻgʻri tartibda yozing."),
        ("2.3", "*do, does, did, is, are, was, were* yoki *have* bilan toʻldiring."),
        ("2.4", "Ega haqidagi savolmi (*S*) yoki toʻldiruvchi haqidagi savolmi (*O*)? Tanlang, keyin gapni "
                "toʻldiring."),
        ("2.5", "Xatoni topib, toʻgʻrilang. UCHTA gap toʻgʻri — ular uchun *✓ It is correct* tugmasini bosing."),
        ("2.6", "Har bir javob uchun savol yozing. Qalin yozilgan qism haqida soʻrang."),
        ("2.7", "Suhbatni savollar bilan toʻldiring."),
        ("2.8", "Suhbatdagi soʻz tartibini toʻgʻrilang. BESHTA xato bor. Toʻgʻrilangan savollarni suhbatdagi "
                "tartibda yozing."),
        ("3.1", "Ijobiymi (*+*), salbiymi (*−*) yoki oʻrtachami (*=*)? Tanlang."),
        ("3.2", "Har bir gapni ramkadagi sifat bilan toʻldiring: tanlang."),
        ("3.3", "Qarama-qarshi maʼnoli soʻzni yozing."),
        ("3.4", "*very* mi yoki *really* mi? Toʻgʻrisini tanlang."),
        ("3.5", "Soʻz urgʻusi. Urgʻuli boʻgʻinni tanlang, keyin soʻzni ovoz chiqarib ayting."),
        ("3.6", "Yaxshiroq sifat tanlang. Har safar *nice* va *bad* oʻrniga boshqa sifat yozing."),
        ("3.7", "Har bir gapdagi xatoni topib, toʻgʻri gapni yozing."),
        ("3.8", "Matnni sifatlar bilan toʻldiring."),
        ("4.1", "Tinglashdan oldin: bazmda qaysi mavzular haqida gapirilishini kutasiz? Belgilang."),
        ("4.2", "Bir marta tinglang. Har bir juftlik nima haqida gapiradi? *1*, *2* yoki *3* ni tanlang — "
                "hech biri gapirmasa, *none*."),
        ("4.3", "Yana tinglang. Qaysi gapiruvchi suhbatdan zavq olmayapti? Nega?"),
        ("4.4", "Yana bir marta tinglang va har bir qatorni eshitgan sifatingiz bilan toʻldiring."),
        ("4.5", "Tinglang va eshitgan TOʻRTTA savolingizni yozing."),
        ("4.6", "Bu savollarni yana tinglang va nima boʻlishiga eʼtibor bering."),
        ("4.7", "Har bir savolni ikki marta ayting — avval sekin, keyin tez."),
        ("4.8", "Gapiruvchi nima demoqchi? *A* yoki *B* ni tanlang."),
        ("5.1", "Salomlashish. Har bir iborani BITTA soʻz bilan toʻldiring."),
        ("5.2", "5.1 dagi har bir iborani kim bilan ishlatasiz? Tanlang."),
        ("5.3", "Har bir salomlashishni tabiiy javob bilan moslashtiring: mos harfni tanlang."),
        ("5.4", "Har bir munosabatni toʻgʻri qolip bilan toʻldiring."),
        ("5.5", "Gap urgʻusi. Har bir munosabatdagi eng baland aytiladigan soʻzni tanlang, keyin ayting."),
        ("5.6", "Suhbatni tugatish. Toʻrt qadamni tartib bilan raqamlang (1–4)."),
        ("5.7", "Namunaviy suhbatni oʻqing. Keyin savollarga javob bering."),
        ("5.8", "Namuna haqidagi savollarga javob bering."),
        ("5.9", "Oʻz suhbatingizni yozing (10–12 qator). Koʻchada eski doʻstingizni uchratib qoldingiz.")]:
    h.say_also(label, text)

# ------------------------------------------ the explanations, told in Uzbek
h.goals([
    "shaxsiy savollar berish va ularga javob berishni",
    "savollarni toʻgʻri tuzishni, jumladan ega haqidagi savollarni",
    "narsalarni kundalik sifatlar bilan tasvirlashni",
    "bazmda yengil suhbat qilayotgan odamlarni tushunishni",
    "salomlashish, qiziqish bildirish va suhbatni xushmuomalalik bilan tugatishni",
])
h.retell("KEY WORDS", "KALIT SOʻZLAR", [
    "**small talk**  arzimas mavzudagi yengil suhbat",
    "**a stranger**  notanish odam",
    "**awkward**  noqulay, qiyin",
    "**to have something in common**  umumiy qiziqishga ega boʻlmoq",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — SAVOL SHAKLLARI", [     # the first of the two
    "Ingliz tilida savolda soʻz tartibi oʻzgaradi. Gapni emas, shaklni oʻrganing.",
    "[[A]] **be bilan: be birinchi keladi.** *Are you married? · Is she your sister? · Why were you late?*",
    "[[B]] **Boshqa feʼllar bilan: do / does / did qoʻshing va feʼlning oddiy shaklini ishlating.** *Do you "
    "like the music? · Where did you meet?* — hech qachon *Where did you met* emas.",
    "[[C]] **Ega haqidagi savol.** Harakatni kim yoki nima bajarayotganini soʻrasangiz, *do* qoʻshilmaydi. "
    "*Who knows Ana? · What happened? · How many people came?*",
    "[[D]] **Predloglar oxiriga qoʻyiladi.** *Who did you come with? · What are you looking at?* — *With who "
    "did you come* emas.",
    "[[SOʻROQ SOʻZLARI]] *who · what · where · when · why · how · which · whose* · *how* + sifat: *how old · "
    "how much · how many · how long · how often*",
])
h.retell("ERROR WARNING", "DIQQAT — SAVOLDAGI XATOLAR", [           # the first of the two
    "Bu beshta xato deyarli har bir Pre-intermediate sinfida uchraydi, chunki oʻzbek va rus tillarida savol "
    "soʻz tartibi bilan emas, ohang yoki yuklama bilan tuziladi:",
    "1 **do ni qoʻshing.** ✗ *Where you live?* → ✓ *Where do you live?*",
    "2 **Feʼlni oldinga chiqarmang.** ✗ *What means this word?* → ✓ *What does this word mean?* · ✗ *How "
    "much costs it?* → ✓ *How much does it cost?*",
    "3 **did dan keyin feʼlning oddiy shakli.** ✗ *Where did you went?* → ✓ *Where did you go?*",
    "4 **Ega haqidagi savolda do yoʻq.** ✗ *Who did come?* → ✓ *Who came?*",
    "5 **Predlog oxiriga.** ✗ *With who did you come?* → ✓ *Who did you come with?*",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — KUNDALIK SIFATLAR", [
    "Bular — odamlar suhbatda haqiqatan ishlatadigan sifatlar. Ularni guruhlarga boʻlib oʻrganing.",
    "[[IJOBIY]] *lovely · beautiful · delicious · perfect · amazing · fantastic · brilliant · nice*",
    "[[SALBIY]] *awful · horrible · boring · rude · ugly · silly · strange*",
    "[[OʻRTACHA]] *all right* — *The film was all right, but the ending was a bit strange.*",
    "[[KUCHLI]] Kuchli sifatlar allaqachon *very* maʼnosini beradi: *amazing · delicious · awful · "
    "brilliant*. *really amazing* deng, hech qachon *very amazing* emas.",
    "**Soʻz urgʻusi:** *de-LI-cious · a-MA-zing · BEAU-ti-ful · HOR-ri-ble · BOR-ing · all RIGHT*",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [
    "Tugʻilgan kun bazmidagi uchta qisqa suhbatni eshitasiz. Har birida ikki kishi gaplashadi — lekin "
    "hammasi ham undan zavq olmayapti.",
    "Agar sinfingizda audio boʻlsa, bu 1.1–1.3-treklar. Boʻlmasa, oʻqituvchingiz matnni oʻqib beradi — "
    "topshiriqlar bir xil.",
])
h.retell("WHY YOU DIDN'T HEAR IT", "NEGA ESHITMADINGIZ?", [
    "**Savolda do you deyarli yoʻqolib ketadi.** *Do you* /djə/ yoki hatto /jə/ ga, *did you* esa /dɪdʒə/ ga "
    "aylanadi. Baland aytiladiganlari — feʼl va undan keyingi ot: shularga quloq soling, qolganini soʻroq "
    "soʻzi olib ketadi.",
])
h.retell("THE THREE JOBS OF A CONVERSATION", "SUHBATNING UCHTA VAZIFASI", [
    "Tanish odam bilan boʻladigan har bir qisqa suhbat bir xil uchta ishni bajaradi. Har biri uchun bitta "
    "iboralar toʻplamini oʻrganing:",
    "[[1]] **Salomlashing.**",
    "[[2]] **Aytganlariga qiziqish bildiring.**",
    "[[3]] **Suhbatni xushmuomalalik bilan tugating** — hamma unutadigan qism.",
])
h.retell("SHOWING INTEREST", "QIZIQISH BILDIRISH", [
    "Kimdir sizga biror narsa aytsa, inglizlar javob berishdan oldin munosabat bildiradi. Munosabat qisqa va "
    "deyarli har doim *undov + sifat* boʻladi:",
    "*What a lovely surprise! · Oh, how nice! · That's fantastic news! · That sounds lovely. · Wow, really?*",
    "**Qolip muhim:** *What a* + sifat + ot! · *How* + sifat! · *That's* + sifat + *news!* · *That sounds* + "
    "sifat.",
])
h.retell("ERROR WARNING", "DIQQAT — MUNOSABATDAGI XATOLAR", [
    "Oʻquvchilar bu iboralarni ishlatganda uchta narsa notoʻgʻri ketadi:",
    "1 **Umuman munosabat bildirmaslik.** Munosabatsiz javob ingliz tilida sovuq eshitiladi, soʻzlar "
    "xushmuomala boʻlsa ham. ✗ *'I got the job.' — 'OK.'*",
    "2 **Notoʻgʻri qolip.** ✗ *What a lovely!* → ✓ *What a lovely surprise!* (*what a* dan keyin ot kerak) · "
    "✗ *How nice news!* → ✓ *That's nice news!* (*how* dan keyin faqat sifat keladi)",
    "3 **Bir tekis urgʻu.** Sifat — gapdagi eng baland soʻz. *That's fan-TAS-tic news!* Bir tekis aytilsa, "
    "kinoyadek eshitiladi.",
])
h.retell("CHECK BEFORE YOU PRACTISE IT", "MASHQ QILISHDAN OLDIN TEKSHIRING", [
    "{box}  Ikkita salomlashish iborasini ishlatdim.   {box}  Ikki marta *What a… / How… / That's… news! / "
    "That sounds…* bilan munosabat bildirdim.",
    "{box}  Ikkita savol berdim va soʻz tartibi toʻgʻri.   {box}  3-boʻlimdan uchta sifat ishlatdim.",
    "{box}  Toʻrt qadamning hammasi bilan tugatdim: sabab, yoqimli boʻldi, reja, xayrlashuv.   {box}  Sifatga "
    "urgʻu berib, ovoz chiqarib aytdim.",
])
h.one_per_line("MASHQ QILISHDAN OLDIN TEKSHIRING", None, at="box")
h.retell_cells({"Question word": "Soʻroq soʻzi", "Auxiliary": "Yordamchi feʼl", "Subject": "Ega",
                "Verb + rest": "Feʼl va qolgani"})
h.retell_cells({"What is written": "Yozilishi", "What you hear": "Eshitilishi", "Why": "Nega",
                "t + d join, you → /jə/": "<i>t</i> va <i>d</i> qoʻshiladi, <i>you</i> → /jə/"},
               after="4.6  </span>")                # "Why" is also a question word in 2's table

# ------------------------------------------------------------------ the key
K = {}
for n, a in enumerate("BABAB", 1):
    K[("1.2", n, 1)] = choose(["A", "B", "C"], a)
for n in range(1, 5):
    K[("1.3", n, 1)] = own()
for n, a in enumerate(["small talk", "a stranger/stranger",
                       "to have something in common/have something in common/to have in common/have in common",
                       "to panic/panic"], 1):
    K[("1.4", n, 1)] = Q(a)
GOOD = {"G": "G · good", "B": "B · bad"}
# as numbered: 1 know Ana 2 earn 3 first time 4 married 5 the talk 6 rent
for n, a in enumerate("GBGBGB", 1):
    K[("1.5", n, 1)] = choose(["G", "B"], a, labels=GOOD)
for n, a in enumerate(["✗", "✓", "✓", "✗"], 1):
    K[("1.6", n, 1)] = choose(YES_NO, a)
BD = {"B": "B · be", "D": "D · do / does / did"}
for n, a in zip(range(2, 7), "DBDBD"):          # 2 play 3 sister 4 meet 5 late 6 like
    K[("2.1", n, 1)] = choose(["B", "D"], a, labels=BD)
for n, a in enumerate(["Where do you live", "Where did you meet", "Do you like the music", "Why were you late",
                       "Who do you know at the party"], 1):
    K[("2.2", n, 1)] = write(a)
for n, a in enumerate(["Do", "Is", "did", "does", "Are", "were", "does", "have"], 1):
    K[("2.3", n, 1)] = Q(a)
SO = {"S": "S · subject", "O": "O · object"}
for n, (so, words) in enumerate([("S", ["knows"]), ("O", ["did", "meet"]), ("S", ["happened"]),
                                 ("O", ["did", "say"]), ("S", ["came"])], 1):
    K[("2.4", n, 1)] = choose(["S", "O"], so, labels=SO)
    for k, wd in enumerate(words, 2):
        K[("2.4", n, k)] = Q(wd)
TICKED = "✓/correct/tick"
for n, a in zip(range(2, 9), [
        "What does this word mean",
        TICKED,
        "Where did you go last summer/Where did you go",
        "Who came to the party/Who came",
        TICKED,
        "Who did you come with",
        TICKED]):
    K[("2.5", n, 1)] = fix(a)
for n, a in enumerate(["Where did you meet her", "Who invited you", "How much did it cost",
                       "Who did you come with", "How long have you lived here"], 1):
    K[("2.6", n, 1)] = write(a)
for n, a in enumerate(["How do you know Ana", "Where do you work", "What do you do there",
                       "How long have you been a nurse"], 1):
    K[("2.7", n, 1)] = write(a)
for n, a in enumerate([
        "Where are you from",
        "How long have you studied here/How long have you been studying here/How long have you studied/"
        "How long have you been studying",
        "What does 'placement test' mean/What does placement test mean/What does “placement test” mean",
        "Who told you about this centre/Who told you about this center/Who told you",
        "Who did you come with"], 1):
    K[("2.8", n, 1)] = write(a)
PMO = {"+": "+ positive", "−": "− negative", "=": "= OK"}
# item 1 is the worked example; as numbered: 2 awful 3 boring 4 lovely 5 all right 6 amazing 7 rude
# 8 perfect 9 strange 10 horrible
for n, a in zip(range(2, 11), ["−", "−", "+", "=", "+", "−", "+", "−", "−"]):
    K[("3.1", n, 1)] = choose(["+", "−", "="], a, labels=PMO)
BOXW = ["delicious", "boring", "rude", "all right", "strange", "lovely", "awful", "perfect"]
for n, a in enumerate(["perfect", "delicious", "rude", "all right", "strange", "boring", "lovely", "awful"], 1):
    K[("3.2", n, 1)] = choose(BOXW, a)
for n, a in enumerate(["ugly", "boring", "rude", "awful/horrible/terrible", "silly", "strange/weird"], 1):
    K[("3.3", n, 1)] = Q(a)
# 3.4, as numbered: 1 amazing 2 good 3 delicious 4 boring 5 rude 6 perfect. A strong adjective takes
# only really; with an ordinary one both are right, as the key says of good
for n, a in enumerate(["really", "very/really", "really", "very/really", "very/really", "really"], 1):
    K[("3.4", n, 1)] = choose(["very", "really"], a)
STRESS = {"delicious": "li", "amazing": "ma", "beautiful": "beau", "horrible": "hor", "boring": "bor",
          "fantastic": "tas"}
for n, syll in SYLL.items():
    K[("3.5", n, 1)] = choose(syll, STRESS["".join(syll)])
NICE_FOOD = "delicious/lovely/amazing/fantastic/brilliant/perfect/wonderful"
NICE_VIEW = "beautiful/amazing/lovely/fantastic/brilliant/perfect/wonderful"
for n, a in enumerate([NICE_FOOD, "perfect/lovely/beautiful/amazing/fantastic/brilliant/wonderful",
                       "awful/boring/horrible/terrible/strange/silly", "rude/awful/horrible/terrible/strange/silly",
                       NICE_VIEW], 1):
    K[("3.6", n, 1)] = Q(a)
for n, a in enumerate([
        "The food was really delicious/The food was delicious",
        "It was an awful film/It was a really awful film",
        "The weather is perfect today",
        "He was rude to the waiter"], 1):
    K[("3.7", n, 1)] = write(a)
for n in range(1, 7):                             # the key gives samples: his to read
    K[("3.8", n, 1)] = own(control=None)
for n in range(1, 7):                             # what they expect: nothing to mark
    K[("4.1", n, 1)] = tick()
WHO = {"1": "1", "2": "2", "3": "3", "none": "none"}
# as numbered: 1 the party 2 where they live 3 people they know 4 work 5 money 6 their interests
for n, a in enumerate(["1", "2", "1", "2", "none", "3"], 1):
    K[("4.2", n, 1)] = choose(["1", "2", "3", "none"], a, labels=WHO)
K[("4.3", 1, 1)] = own()
for key, a in (((1, 1), "perfect"), ((2, 1), "delicious"), ((3, 1), "all right"), ((3, 2), "boring"),
               ((4, 1), "boring"), ((5, 1), "strange")):
    K[("4.4",) + key] = Q(a)
for n in range(1, 5):                             # the key does not say which four
    K[("4.5", n, 1)] = own()
for n, a in enumerate("BAB", 1):
    K[("4.8", n, 1)] = choose(["A", "B"], a)
for n, a in enumerate(["see", "are", "see", "living", "way", "meet"], 1):
    K[("5.1", n, 1)] = Q(a)
KN = {"know": "Somebody I know", "new": "Somebody new"}
for n, a in enumerate(["know", "know", "know", "know", "new", "new"], 1):
    K[("5.2", n, 1)] = choose(["know", "new"], a, labels=KN)
for n, a in enumerate("bdeca", 1):
    K[("5.3", n, 1)] = choose([l for l, _r in replies], a)
ADJ = ["fantastic", "brilliant", "great", "amazing", "wonderful", "lovely", "nice", "perfect"]
NEWS = "/".join("%s news" % a for a in ADJ)
K[("5.4", 1, 1)] = Q(NEWS)
K[("5.4", 2, 1)] = Q("/".join(ADJ))
K[("5.4", 3, 1)] = Q("/".join("%s %s" % (a, n) for a in ADJ + ["kind"]
                              for n in ("surprise", "idea", "present", "gift", "thought")))
K[("5.4", 4, 1)] = Q("/".join(ADJ))
K[("5.4", 5, 1)] = Q(NEWS)
LOUDEST = {1: "lovely", 2: "fantastic", 3: "nice", 4: "lovely"}
for n, words in LOUD.items():
    K[("5.5", n, 1)] = choose(words, LOUDEST[n])
# as numbered: 1 say goodbye 2 say it was good 3 give a reason 4 make a plan
for n, a in enumerate("4213", 1):
    K[("5.6", n, 1)] = number(a)
for n in range(1, 5):
    K[("5.8", n, 1)] = own()
K[("5.9", 20, 1)] = own(control="essay")
for n in range(1, 7):                             # the checklist
    K[("5.9", n, 1)] = tick()

if __name__ == "__main__":
    data = h.build(K, "Pre-Intermediate", 1, "Unit 1A & 1C — Communication")
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "p01ac.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
