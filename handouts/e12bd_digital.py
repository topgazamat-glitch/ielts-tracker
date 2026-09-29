"""E12BD Travel - Azamat's Elementary booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(E12BD Travel - ANSWER KEY), joined box by box by hand. The Desktop copy of
this booklet has its section bars run into the boxes that follow them, which
would make the whole booklet one part; the Material Bank copy is built as the
others are, so it is the one used here.

As with E12AC, the booklet speaks Uzbek wherever it explains: every
explanation box, the goals, the "Why" column of the listening table, and a
line under every instruction. The English examples stay English, as do the
reading text, the dialogues and the exercises.

What a phone gets that paper does not:
  - taps for every choice: who says it, A/B/C, should or shouldn't, the
    loudest word, shouldn't or don't have to, the word that goes with each
    verb, which is different, the silent letter, T/M/N, T/F, Tom or Maya,
    which paragraph does which job and their order;
  - boxes where paper has none: 2.4, 2.6, 3.3, 3.4, 5.2.
The swap in 5.8 keeps its boxes; they are for class.

    python3 handouts/e12bd_digital.py            # writes handouts/e12bd.json, lists every box
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import (Handout, Q, choose, tick, own, write, fix, number, pair, report,   # noqa: E402
                     BLANK_TAG, LEADER_P, plain, ITEM_STYLE, NUM_SPAN, TEXT_SPAN)

DOCX = ("~/Documents/Claude/Material Bank/General English/A2 Elementary/_NEW BOOKLET STYLE/"
        "E12BD Travel — BOOKLET.docx")
W = "95%"

h = Handout(DOCX)
TAGS = {int(m.group(1)): m.group(0) for m in BLANK_TAG.finditer(h.html)}


def section(label):
    return h.html.index("%s  </span>" % label)


def either(*forms):
    return "/".join(forms)


def item_p(label, n, text_html, token):
    h.texts[(label, n)] = plain(text_html)
    return ('<p data-item="%s:%d" %s>%s%s</p>'
            % (label, n, ITEM_STYLE, NUM_SPAN % n, TEXT_SPAN % ("%s  %s" % (text_html, token))))


def key_list(pairs):
    return ('<table class="bk"><tr><td style="vertical-align:top;background:#F2F8F8;'
            'border-left:3px solid #127D80">'
            + "".join('<p style="margin:0"><span style="font-weight:700;color:#127D80">%s</span>  %s</p>'
                      % (l, html.escape(t, quote=False)) for l, t in pairs)
            + "</td></tr></table>")


def replace_table_after(label, new):
    a = h.html.index('<table class="bk">', section(label))
    b = h.html.index("</table>", a) + len("</table>")
    old = h.html[a:b]
    h.html = h.html[:a] + new + h.html[b:]
    return old


def words_of(label, n):
    m = next(m for m in h._items(label) if int(m.group(3)) == n)
    return [w.strip("?!.,") for w in re.sub(r"^\d+\s+", "", plain(m.group(4))).split() if w.strip("?!.,")]


# ------------------------------------------------------------ 1 Reading
for n in range(1, 5):
    h.item_box("1.3", n)
h.options_on_lines("1.3")
for n in range(1, 4):
    h.item_box("1.4", n, width="190px", where="leader")
h.leaders("1.5", "1.6  </span>", [(1, W, "Three sentences with should"), (2, W, "Three sentences with shouldn't")])
for n in range(1, 4):
    h.item_box("1.6", n, where="leader")

# ------------------------------------------------------------ 2 Grammar
for n in range(2, 9):                             # item 1 is the worked example
    h.item_box("2.4", n)
h.grid_rows("2.5")
LOUD = {}
for n in range(1, 5):
    LOUD[n] = words_of("2.6", n)
    h.item_box("2.6", n)

# ------------------------------------------------------------ 3 Vocabulary
# 3.1: the words first, as a key; then each verb, with a-f to tap
old = replace_table_after("3.1", "{{3.1}}")
cells = [plain(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", old, re.S)]
verbs = sorted((int(n), v) for n, v in (re.match(r"(\d+)\s+(.*)", c).groups() for c in cells
                                        if re.match(r"\d+\s", c)))
words31 = sorted(re.match(r"([a-f])\s+(.*)", c).groups() for c in cells if re.match(r"[a-f]\s", c))
h.html = h.html.replace("{{3.1}}", key_list(words31) + "".join(
    item_p("3.1", n, html.escape(v, quote=False), "{{box:3.1:%d:60px:}}" % n) for n, v in verbs))
ODD = h.odd_one_out("3.3", why="Why is it different?")
LETTERS = {}
for n in range(1, 7):
    word = words_of("3.4", n)[0]
    LETTERS[n] = list(dict.fromkeys(word))
    h.item_box("3.4", n)
for n in range(1, 5):
    h.item_box("3.5", n, where="leader")

# ------------------------------------------------------------ 4 Listening
for n in range(1, 6):
    h.item_box("5.1", n)
h.options_on_lines("5.1")

# ------------------------------------------------------------ 5 Writing
h.after_instruction("5.2", [(n, l, "60px", "") for n, l in enumerate("abcd", 1)])
replace_table_after("5.3", "".join(item_p("5.3", n, "Paragraph %d" % n, "{{box:5.3:%d:60px:}}" % n)
                                   for n in range(1, 5)))
for n in range(1, 4):
    h.item_box("5.4", n, where="leader")
h.leaders("5.7", "CHECK BEFORE", [(20, W, "Write your email here")])
h.html = h.html.replace(TAGS[95], "", 1)          # the word count: the box counts them itself
h.grid_rows("5.8")

# ------------------------------- every instruction, once more, in Uzbek
for label, text, *after in [
        ("1.1", "Muhokama qiling. Boshqa mamlakatda yashashni xohlaysizmi? Qaysi birida va nega?"),
        ("1.2", "Buni kim aytadi? *T* (Tom), *K* (Kirsten) yoki *M* (Maya) ni tanlang."),
        ("1.3", "Eng toʻgʻri javobni tanlang: *A*, *B* yoki *C*."),
        ("1.4", "Matndan shu maʼnodagi soʻzni toping."),
        ("1.5", "*should* bilan uchta va *shouldn't* bilan uchta gap toping."),
        ("1.6", "Savollarga javob bering."),
        ("2.1", "*Should* mi yoki *shouldn't* mi? Tanlang."),
        ("2.2", "*should* bilan savol tuzing."),
        ("2.3", "Suhbatni toʻldiring: *should* yoki *shouldn't*."),
        ("2.4", "Xatoni topib, toʻgʻrilang. IKKITA gap toʻgʻri — ular uchun *✓ It is correct* tugmasini bosing."),
        ("2.5", "Har bir vaziyat uchun ikkita maslahat bering — bittasi *should* bilan, bittasi *shouldn't* "
                "bilan."),
        ("2.6", "Tinglang va takrorlang. Eng baland aytilgan soʻzni tanlang."),
        ("2.7", "*Shouldn't* mi yoki *don't have to* mi? Tanlang."),
        ("3.1", "Feʼlni soʻz bilan moslang: harfni tanlang."),
        ("3.2", "Har bir gapni toʻgʻri feʼl bilan toʻldiring."),
        ("3.3", "Qaysi biri boshqacha? Tanlang va nega ekanini yozing."),
        ("3.4", "Har bir soʻzdagi aytilmaydigan harfni tanlang."),
        ("3.5", "Har bir gapdagi xatoni topib, toʻgʻri gapni yozing."),
        ("3.6", "Sherigingizdan soʻrang. Toʻliq gap bilan javob bering."),
        ("4.1", "Bir marta tinglang. Har bir narsani kim yoqtiradi — *T* (Tom), *M* (Maya) yoki *N* (hech "
                "kim)?"),
        ("4.2", "Yana tinglang. Toʻgʻri (*T*) mi yoki notoʻgʻri (*F*) mi?"),
        ("4.3", "Yana bir marta tinglang va har bir qatorni toʻldiring."),
        ("4.4", "Tinglang va nima boʻlishiga eʼtibor bering."),
        ("4.5", "Har bir iborani ikki marta ayting — avval sekin, keyin tez."),
        ("4.6", "Bu kim? *T* (Tom) yoki *M* (Maya) ni tanlang."),
        ("4.7", "Endi ularga maslahat bering. *should* va *shouldn't* ni ishlating."),
        ("5.1", "Tinglang va toʻgʻri javobni tanlang."),
        ("5.2", "Namunani oʻqing. Qaysi xatboshi qaysi vazifani bajaradi? Har bir xatboshi uchun 1–4 ni "
                "tanlang."),
        ("5.3", "Endi ularni tartib bilan joylang."),
        ("5.4", "Namuna haqidagi savollarga javob bering."),
        ("5.5", "Gaplarni tartib bilan raqamlab, xatboshi tuzing (1–4)."),
        ("5.6", "Avval reja tuzing. Ikki daqiqa, keyin yozing."),
        ("5.7", "Endi emailingizni yozing (100–120 soʻz). Doʻstingizning doʻsti bir haftaga shahringizga "
                "kelyapti. Unga nima qilishi kerak va nima qilmasligi kerakligini yozing.",
         "A friend of a friend is coming"),
        ("5.8", "Sherigingiz bilan emaillarni almashing. Uning emailini oʻqing va javob bering.")]:
    h.say_also(label, text, after=after[0] if after else None)

# ------------------------------------------ the explanations, told in Uzbek
h.goals([
    "*should* va *shouldn't* bilan maslahat berishni — *to* siz, *do* siz",
    "*shouldn't* ni *don't have to* dan farqlashni",
    "sayohat iboralarini ishlatishni — *make plans, book a hotel, pack a bag*",
    "gapiruvchi aslida nimani yoqtirishini hal qiladigan inkorlarni eshitishni",
    "*first, secondly* va *finally* bilan bogʻlangan toʻrt xatboshili doʻstona email yozishni",
])
h.retell("KEY WORDS", "KALIT SOʻZLAR", [
    "**abroad**  boshqa mamlakatda, chet elda",
    "**local people**  oʻsha joyning odamlari, mahalliy aholi",
    "**to get used to**  koʻnikmoq, gʻalati deb bilishni toʻxtatmoq",
    "**advice**  kimgadir nima qilishni aytish, maslahat",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — SHOULD VA SHOULDN'T", [
    "**SHOULD — maslahat uchun.** Bu buyruq ham, fakt ham emas. U „menimcha, bu yaxshi fikr“ degani — "
    "*shouldn't* esa „menimcha, bu yomon fikr“.",
    "[[+]] *should* + feʼlning oddiy shakli. *You should live like the local people. · You should learn six "
    "words.* *to* yoʻq, *-s* yoʻq, *-ing* yoʻq.",
    "[[−]] *shouldn't* + feʼlning oddiy shakli. *You shouldn't wait until the last week. · You shouldn't get "
    "angry.*",
    "[[?]] Savolda *should* birinchi keladi. *Should I go to Bangkok? · What should I do on an island? · Where "
    "should we stay?*",
    "[[✓ ✗]] Qisqa javoblar: *Yes, you should. / No, you shouldn't.*",
    "**Should hech qachon oʻzgarmaydi.** *shoulds* emas, *shoulded* emas, *to should* emas. Hamma shaxs uchun "
    "bitta shakl — shuning uchun u ingliz tilidagi eng oson feʼl, faqat unga tegmasangiz boʻldi.",
])
h.retell("ERROR WARNING", "DIQQAT — SHOULD DAGI XATOLAR", [
    "1 **Should bilan DO ishlatmang.** ✗ *What do I pack to go on holiday?* → ✓ *What should I pack to go on "
    "holiday?* · ✗ *What do I should do?* → ✓ *What should I do?*",
    "2 **Should dan keyin TO yoʻq.** ✗ *You should to go to Bangkok.* → ✓ *You should go to Bangkok.* · ✗ *You "
    "should not to worry.* → ✓ *You shouldn't worry.*",
    "3 **SHOULD — bu WOULD emas.** ✗ *It should be nice to travel abroad.* → ✓ *It would be nice to travel "
    "abroad.* *Should* maslahat beradi; *would* tasavvur qiladi.",
    "4 **SHOULDN'T — bu DON'T HAVE TO emas.** ✗ *You don't have to stay in that hotel; it's horrible.* → ✓ *You "
    "shouldn't stay there.* *Shouldn't* = yomon fikr. *Don't have to* = xohlasangiz qilasiz, majbur emassiz: "
    "*You don't have to know how to dive — it's a beginners' course.*",
    "5 **Bitta inkor yetadi.** ✗ *You shouldn't tell no one.* → ✓ *You shouldn't tell anyone.*",
])
h.retell("PRONUNCIATION — THE SILENT L", "TALAFFUZ — AYTILMAYDIGAN L", [
    "**SHOULD da L tovushi yoʻq.** U /ʃʊd/ — „shud“. Harf yoziladi, lekin hech qachon aytilmaydi. *would* "
    "/wʊd/, *could* /kʊd/ va *half* /hɑːf/ da ham shunday.",
    "**Unli esa qisqa.** /ʃʊd/, /ʃuːd/ emas. Uni choʻzsangiz, *shooed* ga oʻxshab qoladi — bu boshqa soʻz.",
    "**Gap ichida u deyarli yoʻqoladi.** *You should go* → /juʃəd gəʊ/. Baland soʻz — feʼl, shuning uchun "
    "*should* eshitilmasa ham maslahat eshitiladi.",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — SAYOHAT IBORALARI", [
    "Collocation — birga yashaydigan ikki-uch soʻz. Ularni mantiq bilan topib boʻlmaydi — bitta soʻzdek, bir "
    "boʻlak qilib oʻrganasiz.",
    "*make plans · change plans · plan a holiday · take a holiday*",
    "*travel abroad · live abroad · go back home · stay home*",
    "*book a hotel · stay in a hotel · pack a bag · unpack a bag*",
    "**Adashtiriladigan ikki juftlik.** *make plans* deyiladi, lekin *plan a holiday*. Mehmonxonani borishdan "
    "oldin *book a hotel* qilasiz, borganingizda esa unda *stay* qilasiz — ikki xil payt, ikki xil feʼl.",
])
h.retell("PRONUNCIATION — MORE SILENT LETTERS", "TALAFFUZ — YANA AYTILMAYDIGAN HARFLAR", [
    "Ingliz tili aytmaydigan harflarni ham yozadi. *should* dagi aytilmaydigan *l* ni koʻrdingiz. Mana eng koʻp "
    "uchraydigan boshqalari:",
    "[[L]] *should · would · could · half · walk · talk*",
    "[[K]] *know · knee · knife*   [[W]] *write · wrong · answer*",
    "[[H]] *hour · honest*   [[B]] *climb · thumb · comb*",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [
    "Ikki kishi vaqtini qayerda oʻtkazishni yoqtirishi haqida gapiradi. Tom Londonda oʻsgan. Maya Kritda "
    "yashaydi. Ular deyarli butunlay qarama-qarshi.",
    "Agar sinfingizda audio boʻlsa, bu 12.11-trek. Boʻlmasa, oʻqituvchingiz matnni oʻqib beradi — topshiriqlar "
    "bir xil.",
])
h.retell("WHY YOU DIDN'T HEAR IT", "NEGA ESHITMADINGIZ?", [
    "**Inkorlar butun maʼnoni beradi, lekin ular juda kichik.** *I'm never very happy · I don't do much sport · "
    "I've never really liked sport · I never go to museums.* Bittasini eshitmay qolsangiz, odamni teskari "
    "tushunasiz.",
    "**Shuning uchun mavzuga emas, NEVER va DON'T ga quloq soling.** Ikkala gapiruvchi ham shahar, sport va xarid "
    "haqida gapiradi. Ularni old tomondagi kichik soʻz ajratib turadi.",
])
h.retell("LISTENING INTO WRITING", "TINGLASHDAN YOZISHGA", [
    "Avval Fred Louisega taʼtili haqida gapirib beradi. Louise oʻsha yerda yashaydigan bir odamni taniydi — "
    "email shundan kelib chiqadi.",
])
h.retell("HOW A FRIENDLY EMAIL IS BUILT", "DOʻSTONA EMAIL QANDAY TUZILADI", [
    "Toʻrtta xatboshi, har birining oʻz vazifasi bor. Ularni alohida saqlang — email oson oʻqiladi; aralashtirib "
    "yuborsangiz — hech kim oxirigacha oʻqimaydi.",
    "1 **Salom va nega yozyapsiz.** *Hi Fred! Louise gave me your email address. She says you're coming to "
    "Porto!*",
    "2 **Maslahat — eng uzun xatboshi.** Uch-toʻrtta narsa, tartib bilan, har biridan oldin bogʻlovchi soʻz.",
    "3 **Yana bitta narsa.** Qoʻshimcha: ovqat, ob-havo, nima olish kerak, nimadan qochish kerak.",
    "4 **Xayrlashuv va taklif.** *Have a great trip — email me if you need anything!*",
    "**2-xatboshi uchun bogʻlovchi soʻzlar:** *First, … · And secondly, … · Finally, …* Ular gap boshida "
    "keladi, keyin vergul qoʻyiladi.",
])
h.retell("CHECK BEFORE YOU SEND IT", "YUBORISHDAN OLDIN TEKSHIRING", [
    "{box}  Toʻrtta xatboshi, har biri bitta vazifa.   {box}  2-xatboshida *First, And secondly* va *Finally*.",
    "{box}  *should* bilan kamida ikkita, *shouldn't* bilan bitta gap.   {box}  *should* dan keyin *to* yoʻq.",
    "{box}  Kamida bitta maslahat uchun nega ekanini aytdim.   {box}  Soʻzlar soni: 100–120.",
])
h.one_per_line("YUBORISHDAN OLDIN TEKSHIRING", None, at="box")
h.retell("THE WHOLE UNIT IN SIX LINES", "BUTUN BOʻLIM OLTI QATORDA", [
    "**SHOULD maslahat beradi.** *You should go.* *to* yoʻq, *do* yoʻq, *-s* yoʻq. U hech qachon oʻzgarmaydi.",
    "**SHOULDN'T — yomon fikr.** *Don't have to* — tanlash sizda. Ular bir xil emas.",
    "**Savolda SHOULD birinchi.** *What should I do? · Where should we stay?*",
    "**SHOULD dagi L aytilmaydi.** /ʃʊd/ — *would* va *could* kabi.",
    "**Iboralar:** *make plans · book a hotel · pack a bag · travel abroad · go back home*.",
    "**Emailda toʻrt xatboshi bor:** salom va nega · maslahat · yana bitta narsa · xayrlashuv.",
])
h.retell_cells({"with a question word": "soʻroq soʻzi bilan", "short answer": "qisqa javob"})
h.retell_cells({"What is written": "Yozilishi", "What you hear": "Eshitilishi", "Why": "Nega",
                "I have is one /v/": "<i>I have</i> bitta /v/ boʻlib qoladi",
                "never is the loud word": "<i>never</i> — baland aytiladigan soʻz",
                "two do sounds, one negative": "ikkita <i>do</i> tovushi, bitta inkor",
                "the tag runs together": "soʻroq qoʻshimchasi bitta soʻzdek qoʻshilib ketadi"},
               after="4.4  </span>")

# ------------------------------------------------------------------ the key
K = {}
TKM = {"T": "T · Tom", "K": "K · Kirsten", "M": "M · Maya"}
for n, a in enumerate("KTMKMT", 1):
    K[("1.2", n, 1)] = choose(["T", "K", "M"], a, labels=TKM)
for n, a in enumerate("BBCB", 1):
    K[("1.3", n, 1)] = choose(["A", "B", "C"], a)
for n, a in enumerate(["abroad", "foreigners/foreigner/other foreigners", "advice"], 1):
    K[("1.4", n, 1)] = Q(a)
K[("1.5", 1, 1)] = own()
K[("1.5", 2, 1)] = own()
for n in range(1, 4):
    K[("1.6", n, 1)] = own()
SS = ["should", "shouldn't"]
for n, a in enumerate(["should", "shouldn't", "should", "shouldn't", "should", "shouldn't"], 1):
    K[("2.1", n, 1)] = choose(SS, a)
for n, a in enumerate(["Should we go to a museum", "What clothes should I wear", "Should I come back later",
                       "What time should we arrive", "Where should we stay", "Who should we ask for advice"], 1):
    K[("2.2", n, 1)] = write(a)
for n, a in enumerate(["should", "should", "shouldn't", "should", "shouldn't", "should", "should", "should",
                       "should", "shouldn't"], 1):
    K[("2.3", n, 1)] = choose(SS, a)
TICKED = "✓/correct/tick"
for n, a in zip(range(2, 9), [
        either("You should go to Bangkok for a few days"),
        "It would be nice to travel abroad",
        either("You shouldn't stay in that hotel; it's horrible", "You shouldn't stay in that hotel, it's horrible",
               "You shouldn't stay in that hotel. It's horrible", "You shouldn't stay in that hotel",
               "You should not stay in that hotel; it's horrible", "You should not stay in that hotel"),
        either("You shouldn't tell anyone about the party", "You shouldn't tell anybody about the party",
               "You should tell no one about the party", "You should not tell anyone about the party"),
        TICKED,
        "What should I do on an island",
        TICKED]):
    K[("2.4", n, 1)] = fix(a)
for n in range(1, 7):                             # their own advice: his to read
    K[("2.5", n, 1)] = own()
for n, a in enumerate(["go", "wait", "do", "shouldn't"], 1):
    K[("2.6", n, 1)] = choose(LOUD[n], a)
SD = ["shouldn't", "don't have to"]
for n, a in enumerate(["don't have to", "shouldn't", "don't have to", "shouldn't", "don't have to",
                       "shouldn't"], 1):
    K[("2.7", n, 1)] = choose(SD, a)
for n, a in enumerate("bcdefa", 1):
    K[("3.1", n, 1)] = choose([l for l, _w in words31], a)
for n, a in enumerate(["plan", "travel/live/go", "book", "pack", "go", "made"], 1):
    K[("3.2", n, 1)] = Q(a)
DIFFERENT = {1: "pack plans", 2: "eat a hotel", 4: "open a bag"}
for n, words in ODD.items():
    K[("3.3", n, 1)] = choose(words, DIFFERENT.get(n) or next(w for w in words if "all correct" in w))
    K[("3.3", n, 2)] = own()
SILENT = {"should": "l", "know": "k", "write": "w", "hour": "h", "climb": "b", "half": "l"}
for n, letters in LETTERS.items():
    K[("3.4", n, 1)] = choose(letters, SILENT[words_of("3.4", n)[0]])
for n, a in enumerate([
        either("We went on a holiday in Turkey last summer", "We went on holiday in Turkey last summer",
               "We had a holiday in Turkey last summer", "We took a holiday in Turkey last summer"),
        either("I need to book a hotel for next week", "I need to book a hotel"),
        "She wants to travel abroad",
        "He goes back home every summer"], 1):
    K[("3.5", n, 1)] = write(a)
TMN = {"T": "T · Tom", "M": "M · Maya", "N": "N · neither"}
# as numbered: 1 big cities 2 beaches 3 shopping 4 the countryside 5 museums 6 water sports
for n, a in enumerate("TMTMNM", 1):
    K[("4.1", n, 1)] = choose(["T", "M", "N"], a, labels=TMN)
TF = {"T": "T · true", "F": "F · false"}
for n, a in enumerate("TFFTT", 1):
    K[("4.2", n, 1)] = choose(["T", "F"], a, labels=TF)
for key, a in (((1, 1), "always"), ((2, 1), "never"), ((2, 2), "nothing"), ((3, 1), "is"), ((4, 1), "city"),
               ((5, 1), "never")):
    K[("4.3",) + key] = Q(a)
TM = {"T": "T · Tom", "M": "M · Maya"}
for n, a in enumerate("TMTM", 1):
    K[("4.6", n, 1)] = choose(["T", "M"], a, labels=TM)
for n in range(1, 5):                             # their own advice
    K[("4.7", n, 1)] = own()
for n in range(1, 6):
    K[("5.1", n, 1)] = choose(["A", "B", "C"], "B")
for n, a in enumerate("3142", 1):                 # a b c d
    K[("5.2", n, 1)] = choose(["1", "2", "3", "4"], a)
for n, a in enumerate("bdac", 1):
    K[("5.3", n, 1)] = choose(["a", "b", "c", "d"], a)
for n in range(1, 4):
    K[("5.4", n, 1)] = own()
# as numbered: 1 And secondly 2 Finally 3 First 4 It's quiet then
for n, a in enumerate("3412", 1):
    K[("5.5", n, 1)] = number(a)
for n in range(1, 5):                             # the plan: notes
    K[("5.6", n, 1)] = own(control=None)
K[("5.7", 20, 1)] = own(control="essay")
for n in range(1, 7):                             # the checklist
    K[("5.7", n, 1)] = tick()
for n in range(1, 5):                             # about a partner's email, in class
    K[("5.8", n, 1)] = pair()

if __name__ == "__main__":
    data = h.build(K, "Elementary", 12, "Unit 12B & 12D — Travel")
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "e12bd.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
