"""E09AB Clothes and shopping - Azamat's Elementary booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(E09AB Clothes and shopping - answer key), joined box by box by hand. The
Desktop "new design" copy is used; it splits into its five parts as it
should. His key says this one is for teaching 9A and 9B back to back, beside
E09AC and E09BD for the C and D lessons; all three are on the site, and the
one he sets is the one that counts.

As with the other Elementary booklets, it speaks Uzbek wherever it
explains: every explanation box, the goals, the spelling table, the "Why"
column of the listening table, and a line under every instruction. The
English examples stay English, as do the reading texts, the dialogues, the
model and the exercises.

Put right here: 4.2 item 3 asked about "the daughter"; the caller in the
script is Nilufar, a friend, so it asks about Nilufar. 3.7 (cross out the
letters you do not say) asks for the letters to be written instead; the
teacher reads them.

    python3 handouts/e09ab_digital.py            # writes handouts/e09ab.json, lists every box
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import (Handout, Q, choose, tick, own, write, fix, note, pair, report,   # noqa: E402
                     BLANK_TAG, LEADER_P, plain, ITEM_STYLE, NUM_SPAN, TEXT_SPAN)

DOCX = ("~/Desktop/Handouts/A2 Elementary/E09AB Clothes and shopping/"
        "E09AB Clothes and shopping — handout (new design).docx")
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


def in_order(label, lines):
    """"Number them 1-5": the paper's own numbers go, so the only numbers
    are the ones tapped."""
    a, b = table_after(label)
    h.html = h.html[:a] + "".join(
        item_p(label, n, "·  " + html.escape(t, quote=False), "{{box:%s:%d:60px:}}" % (label, n), number=False)
        for n, t in sorted(lines.items())) + h.html[b:]


def reword(label, old, new):
    at = section(label) + len("%s  </span>" % label)
    end = h.html.index("</p>", at)
    if plain(h.html[at:end]) != old:
        raise SystemExit("%s says %r" % (label, plain(h.html[at:end])))
    style = re.match(r'<span( style="[^"]*")?>', h.html[at:end])
    h.html = h.html[:at] + "<span%s>%s</span>" % (style.group(1) or "", html.escape(new)) + h.html[end:]


def words_between(label, n):
    """An item's choices, from "(a / b)" or "a / b" in its text."""
    m = next(m for m in h._items(label) if int(m.group(3)) == n)
    return plain(m.group(4))


def boxes_for(label, groups, where="first"):
    for n in groups:
        h.item_box(label, n, where=where)


def lines_for_table(label, lines, width=W):
    a, b = table_after(label)
    h.html = h.html[:a] + "".join(item_p(label, n, html.escape(t), "{{box:%s:%d:%s:}}" % (label, n, width))
                                  for n, t in enumerate(lines, 1)) + h.html[b:]


# ------------------------------------------------------------ 1 Reading
boxes_for("1.4", range(1, 5), where="options")
h.options_on_lines("1.4")
boxes_for("1.5", range(1, 5), where="leader")
boxes_for("1.6", range(1, 5), where="leader")
h.leaders("1.7", "1.8  </span>", [(1, W, "Present simple: three verbs"), (2, W, "Present continuous: three verbs")])
boxes_for("1.9", range(1, 5), where="leader")

# ------------------------------------------------------------ 2 Grammar
FORMS24 = {1: ["open", "am opening"], 2: ["sleeps", "is sleeping"], 3: ["wears", "is wearing"],
           4: ["wears", "is wearing"], 5: ["do you do", "are you doing"], 6: ["do you do", "are you doing"]}
boxes_for("2.4", FORMS24)
boxes_for("2.6", range(2, 9))                     # item 1 is the worked example
for q, a in ((77, 78), (79, 80), (81, 82)):      # 2.9: the question, then the short answer under it
    h.hints[q], h.hints[a] = "Your question", "Short answer"
    h.html = h.html.replace(TAGS[q], TAGS[q] + "<br>", 1)
    h.html = h.html.replace(TAGS[a], re.sub(r"width:[0-9.]+(px|pt|em)", "width:180px", TAGS[a]), 1)
h.options_on_lines("2.10")
lines_for_table("2.11", ["Two things happening right now:", "Two things that happen every day:"])
h.grid_rows("2.12")

# ------------------------------------------------------------ 3 Vocabulary
STRESS33 = {1: "bus stop", 2: "car park", 3: "cash machine", 4: "bookshop", 5: "clothes shop",
            6: "information desk"}
boxes_for("3.3", STRESS33)
WORDS34 = h.sort_words("3.4", ["belt", "boots", "coat", "dress", "earrings", "gloves", "jeans", "jumper",
                               "necklace", "ring", "scarf", "shorts", "skirt", "socks", "trainers", "watch"],
                       "On your feet")
for n in range(1, 7):
    h.item_box("3.7", n, width="150px", placeholder="the letters")
ODD39 = h.odd_one_out("3.9", why="Why is it different?")
boxes_for("3.10", range(1, 5), where="leader")
ENDS313 = h.key_first("3.13")
ODD314 = h.odd_one_out("3.14", why="Why is it different?")
h.options_on_lines("3.15")
h.grid_rows("3.16")

# ------------------------------------------------------------ 4 Listening
h.leaders("4.1", "4.2  </span>", [(1, W, "Three places")])
if h.html.count("Why is the daughter worried") != 1:
    raise SystemExit("4.2 item 3 has moved")
h.html = h.html.replace("Why is the daughter worried", "Why is Nilufar worried")
boxes_for("4.2", (1, 2, 3), where="leader")
h.options_on_lines("4.8")
boxes_for("4.8", (1, 2, 3))

# ------------------------------------------------------------ 5 Speaking
boxes_for("5.1", (1, 2), where="options")
h.options_on_lines("5.1")
for n in range(1, 5):
    h.item_box("5.3", n)
    h.item_box("5.3", n, placeholder="If it is false, correct it")
a, b = section("5.3"), h.html.index("TWO FESTIVALS")
h.html = h.html[:a] + LEADER_P.sub("", h.html[a:b]) + h.html[b:]
boxes_for("5.4", range(1, 5), where="leader")
boxes_for("5.8", range(1, 5), where="leader")
h.leaders("5.9", "5.10  </span>", [(1, W, "Write your description here")])
h.html = h.html.replace(TAGS[195], "", 1)         # the word count: the box counts them itself

# ------------------------------- every instruction, once more, in Uzbek
for label, text in [
        ("1.1", "Muhokama qiling. Shahringizdagi doʻkonlarda yilning eng gavjum kuni qaysi? Oʻsha kuni xarid qilgani "
                "borasizmi?"),
        ("1.2", "Buni kim aytadi? *B* (Bahodir), *M* (Malika) yoki *E* (Eldor) ni tanlang."),
        ("1.3", "Odatda (*U*) mi yoki hozir (*N*) mi? Tanlang."),
        ("1.4", "Eng toʻgʻri javobni tanlang: *A*, *B* yoki *C*."),
        ("1.5", "Matndan shu maʼnodagi soʻzni toping."),
        ("1.6", "Savollarga javob bering."),
        ("1.7", "Matndan uchta *present simple* va uchta *present continuous* feʼlini toping."),
        ("1.8", "Matndagi har bir qatorni BITTA soʻz bilan toʻldiring."),
        ("1.9", "Matn haqidagi har bir gapdagi xatoni topib, toʻgʻrilang."),
        ("1.10", "Qisqa mazmunni toʻldiring: har bir boʻshliqqa BITTA soʻz."),
        ("1.11", "Sherigingiz bilan gaplashing."),
        ("2.1", "*-ing* shaklini yozing."),
        ("2.2", "*Present continuous* bilan toʻldiring."),
        ("2.3", "*Simple* (*S*) mi yoki *continuous* (*C*) mi? Faqat vaqt soʻziga qarang."),
        ("2.4", "Toʻgʻri shaklni tanlang."),
        ("2.5", "*Present simple* yoki *present continuous* bilan toʻldiring."),
        ("2.6", "Xatoni topib, toʻgʻrilang. IKKITA gap toʻgʻri — ular uchun *✓ It is correct* tugmasini bosing."),
        ("2.7", "Gapni boshqa zamonda qayta yozing. Vaqt soʻzini ham oʻzgartiring."),
        ("2.8", "Xabarni toʻldiring."),
        ("2.9", "Oʻzingiz haqingizda savol va qisqa javob yozing."),
        ("2.10", "Toʻgʻri javobni tanlang: *A*, *B* yoki *C*."),
        ("2.11", "Derazadan qarang yoki uyingiz haqida oʻylang. Toʻrtta rost gap yozing."),
        ("2.12", "Gapirish. Sherigingizdan soʻrang va qisqa javoblarini yozing. Buni sinfda bajarasiz."),
        ("3.1", "Har bir kishining gapini oʻqing. Ularga qaysi doʻkon kerak?"),
        ("3.2", "Bu odamlar savdo markazida qayerga borishi mumkin?"),
        ("3.3", "Urgʻuli soʻzni tanlang, keyin uni ovoz chiqarib ayting."),
        ("3.4", "Har bir kiyim soʻzining guruhini tanlang: oyoqda, qoʻlda yoki qolganlari."),
        ("3.5", "*a*, *a pair of* yoki hech narsa (*–*)? Tanlang."),
        ("3.6", "Qaysi tovush? *1* /ɒ/, *2* /uː/, *3* /ʌ/ yoki *4* /əʊ/ ni tanlang."),
        ("3.7", "Har bir soʻzda aytilmaydigan harflarni yozing."),
        ("3.8", "Tasvirni toʻldiring."),
        ("3.9", "Qaysi soʻz boshqacha? Uni tanlang va nega ekanini yozing."),
        ("3.10", "Har bir gapdagi xatoni topib, toʻgʻri gapni yozing."),
        ("3.11", "Har bir gapni feʼlning toʻgʻri shakli va kiyim soʻzi bilan toʻldiring."),
        ("3.12", "Suhbatni toʻldiring. Bu narsani sotib olganingizning ertasi kuni."),
        ("3.13", "Ikki qismni moslang: harfni tanlang."),
        ("3.14", "Qaysi soʻz boshqacha? Uni tanlang va nega ekanini yozing."),
        ("3.15", "Toʻgʻri javobni tanlang: *A*, *B* yoki *C*."),
        ("3.16", "Gapirish. Sherigingizdan soʻrang va qisqa javoblarini yozing. Buni sinfda bajarasiz."),
        ("4.1", "Tinglashdan oldin. Katta savdo markazida doʻstingizga kutib turishni aytishingiz mumkin boʻlgan "
                "uchta joyni yozing."),
        ("4.2", "1-qoʻngʻiroqni tinglang. Savollarga javob bering."),
        ("4.3", "2- va 3-qoʻngʻiroqlarni tinglang. Har bir kishi qayerda? Joyni tanlang."),
        ("4.4", "Yana tinglang va har bir qatorni toʻldiring."),
        ("4.5", "Tinglang va nima boʻlishiga eʼtibor bering."),
        ("4.6", "Har bir qatorni ikki marta ayting — avval sekin, keyin tez."),
        ("4.7", "Tasdiq (+) mi yoki inkor (−) mi? Baland aytilgan soʻzga quloq soling."),
        ("4.8", "Gapiruvchi nima demoqchi? *A* yoki *B* ni tanlang."),
        ("5.1", "Bir marta tinglang. Toʻgʻri javobni tanlang."),
        ("5.2", "Yana tinglang. Har bir kiyim soʻzini eshitdingizmi? *✓* yoki *✗* ni tanlang."),
        ("5.3", "Yana bir marta tinglang. Toʻgʻri (*T*) mi yoki notoʻgʻri (*F*) mi? Notoʻgʻrilarini toʻgʻrilab "
                "yozing."),
        ("5.4", "Ikki bayram haqidagi savollarga javob bering."),
        ("5.5", "Soʻzlarni toʻgʻri tartibda yozing."),
        ("5.6", "*wear* mi yoki *carry* mi? Tanlang."),
        ("5.7", "Namunani oʻqing, keyin javob bering."),
        ("5.8", "Namuna haqidagi savollarga javob bering."),
        ("5.9", "Bir odamni tasvirlang. 50–60 soʻz yozing, keyin ismini aytmasdan sherigingizga oʻqib bering. U "
                "kimligini topa oladimi?"),
        ("5.10", "Topishmoq oʻyini. Sherigingiz sinfdagi kimnidir tasvirlaydi. Kim ekanini bilish uchun savollar "
                 "bering.")]:
    h.say_also(label, text)

# ------------------------------------------ the explanations, told in Uzbek
h.goals([
    "*present continuous* ning tasdiq, inkor va soʻroq shakllarini ishlatishni",
    "*-ing* shakllarini toʻgʻri yozishni — *writing · coming · studying · swimming*",
    "*present simple* (odatda) va *present continuous* (hozir) orasida tanlashni",
    "xarid soʻzlarini, savdo markazidagi joylarni va kiyim soʻzlarini ishlatishni",
    "uchrashishni kelishayotgan odamlarni tushunishni va kimdir nima kiyganini tasvirlashni",
])
h.retell("KEY WORDS", "KALIT SOʻZLAR", [
    "**a customer**  xaridor — biror narsa sotib oladigan odam",
    "**a queue**  navbat — kutib turgan odamlar qatori",
    "**a shelf**  javon — doʻkonda narsalar turadigan joy",
    "**a break**  tanaffus — ishdagi qisqa dam olish",
])
h.retell("PRESENTATION — THE FORM", "TUSHUNTIRISH — SHAKLI", [
    "*Present continuous* = *am / is / are* + feʼl + *-ing*. U hozir boʻlayotgan narsalar uchun.",
    "[[+]] Tasdiq. *I'm reading a magazine. · We're waiting at the entrance. · She's talking on the phone.*",
    "[[−]] Inkor. *I'm not drinking coffee. · We aren't / We're not waiting. · He isn't / He's not coming.*",
    "[[?]] Soʻroq. *Are you parking the car? · Is he buying anything? · What are you doing?*",
    "[[→]] Qisqa javoblar. *Yes, I am. / No, I'm not. · Yes, she is. / No, she isn't. · Yes, we are. / No, we "
    "aren't.*",
    "**be ni hech qachon tushirib qoldirmang.** ✗ *I working today* → ✓ *I'm working today*. Yolgʻiz *-ing* "
    "feʼl emas.",
])
h.retell("ERROR WARNING — SPELLING", "DIQQAT — IMLO", [
    "Oʻqituvchingiz eng koʻp koʻradigan toʻrttasi:",
    "✗ *writting* → ✓ *writing* · ✗ *comeing / comming* → ✓ *coming* · ✗ *studing* → ✓ *studying* · ✗ *swiming* "
    "→ ✓ *swimming*",
    "Qoida: oxirgi *-e* tushib qoladi, oxirgi undosh faqat bitta unlidan keyin ikkilanadi, oxirgi *-y* ga esa "
    "tegilmaydi. Shuning uchun *write* da *e* yoʻqoladi, *swim* da *m* ikkilanadi, *study* esa hammasini "
    "saqlaydi.",
])
h.retell("PRESENTATION — WHICH TENSE?", "TUSHUNTIRISH — QAYSI ZAMON?", [
    "Ikkala zamon ham hozirgi vaqt haqida, shuning uchun savol doim bitta: odatdami yoki hozirmi?",
    "**Present simple** = odatda qiladigan ishlarimiz. *I open at nine. · People ask me where the chemist is. · "
    "She wears jeans.*",
    "**Present continuous** = hozir boʻlayotgan narsalar. *I'm carrying boxes. · A man is asking me about the car "
    "park. · She's wearing a dress.*",
    "Qaysi biri ekanini vaqt soʻzlari aytadi:",
    "**simple** — *always · usually · normally · often · sometimes · never · every day · at weekends*",
    "**continuous** — *now · right now · today · at the moment · this week*",
])
h.retell("ERROR WARNING — THE WRONG TENSE", "DIQQAT — NOTOʻGʻRI ZAMON", [
    "1 **Simple kerak joyda continuous.** ✗ *All the masks are being really beautiful.* → ✓ *All the masks are "
    "really beautiful.* Niqoblar faqat bugun chiroyli emas.",
    "2 **Continuous kerak joyda simple.** ✗ *Look — I stand in the middle of the square.* → ✓ *I'm standing in "
    "the middle of the square.* U yerda doim turmaydi.",
    "3 **Mos kelmaydigan vaqt soʻzi.** ✗ *I'm going to school every day.* → ✓ *I go to school every day.*",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — DOʻKONLAR, JOYLAR VA KIYIMLAR", [
    "Soʻzlarni uzun roʻyxat qilib emas, guruh-guruh qilib oʻrganing.",
    "[[A]] Doʻkonlar: *a bookshop · a chemist · a clothes shop · a department store · a café · a fast food "
    "restaurant*",
    "[[B]] Savdo markazidagi joylar: *the entrance · the stairs · the information desk · the cash machine · the "
    "car park · the bus stop*",
    "[[C]] Kiyimlar: *a coat · a dress · a jumper · a shirt · a skirt · a T-shirt · jeans · shorts · trousers*",
    "[[D]] Mayda narsalar: *a belt · a scarf · a watch · a ring · a necklace · earrings · gloves · socks · shoes · "
    "boots · trainers · jewellery*",
    "**Ikki qismli narsa = a pair of.** *a pair of jeans · a pair of shoes · a pair of gloves.* Bu soʻzlarning "
    "birlik shakli yoʻq: *a jean* deb boʻlmaydi.",
])
h.retell("PRONUNCIATION — TWO-WORD NOUNS", "TALAFFUZ — IKKI SOʻZLI OTLAR", [
    "Ikki soʻzli otda urgʻu birinchi soʻzga tushadi: *BUS stop · CAR park · CASH machine · BOOKshop · DEPARTment "
    "store · INformation desk*.",
    "Urgʻuni notoʻgʻri qoʻysangiz, ikki alohida narsadek eshitiladi. *BUS stop* — joy; *bus STOP* esa avtobusga "
    "buyruqdek eshitiladi.",
])
h.retell("PRONUNCIATION — THE LETTER O", "TALAFFUZ — O HARFI", [
    "*o* harfining toʻrtta koʻp uchraydigan tovushi bor. Har biri uchun bitta soʻz oʻrganing — qolganlari "
    "ergashadi:",
    "[[1]] /ɒ/ *sock · coffee · box*   [[2]] /uː/ *boot · shoe · group · two*",
    "[[3]] /ʌ/ *glove · come · mother*   [[4]] /əʊ/ *coat · know · phone*",
    "**Aytilmaydigan harflar:** *jewellery* — /dʒuːəlri/. Xuddi shunday: *veg(e)table · int(e)resting · "
    "choc(o)late · cam(e)ra · comf(or)table*.",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [
    "Toʻrt doʻst kinodan oldin katta savdo markazida uchrashmoqchi. Uchta qisqa telefon qoʻngʻirogʻini eshitasiz.",
    "Agar sinfingizda audio boʻlsa, bu 09.03–09.05-treklar. Boʻlmasa, oʻqituvchingiz matnni oʻqib beradi — "
    "topshiriqlar bir xil.",
])
h.retell("WHY YOU DIDN'T HEAR IT", "NEGA ESHITMADINGIZ?", [
    "**Urgʻu inkorga tushadi.** *We AREN'T buying anything* da kuchli soʻz — *aren't*, *buying* emas. Tasdiqda esa "
    "*are* kuchsiz: *we're BUYing* → /wəbaɪɪŋ/.",
    "Demak, *we're buying* bilan *we aren't buying* orasidagi farq juda kichik *n't* tovushida emas — qaysi soʻz "
    "baland aytilishida. *n* ga emas, baland soʻzga quloq soling.",
])
h.retell("LISTENING INTO SPEAKING", "TINGLASHDAN GAPIRISHGA", [
    "Avval ikkita telefon qoʻngʻirogʻi. Ikki doʻst bayramda, va ikkalasi ham odatda hech qachon kiymaydigan "
    "narsani kiyib olgan.",
    "Agar sinfingizda audio boʻlsa, bu 09.10-trek. Boʻlmasa, oʻqituvchingiz matnni oʻqib beradi.",
])
h.retell("DESCRIBING WHAT SOMEBODY IS WEARING", "KIMDIR NIMA KIYGANINI TASVIRLASH", [
    "*Present continuous* ni ishlating — bu u odatda kiyadigan narsa emas, hozir ustida bor narsa.",
    "**Tartib:** *She's wearing a long red dress.* — avval oʻlcham yoki uzunlik, keyin rang, keyin ot. "
    "*a red long dress* emas.",
    "**Foydali qoʻshimchalar:** *with* — *a dress with big flowers on it* · *round* — *a scarf round her neck* · "
    "*on* — *boots on her feet*",
    "**Ehtiyot boʻling:** *He's wearing glasses* ✓, lekin *He has glasses* — koʻzoynagi bor degani. *wear* — "
    "*carry* emas: paltoni *wear* qilasiz, sumkani *carry* qilasiz.",
])
h.retell("CHECK BEFORE YOU READ IT OUT", "OʻQIB BERISHDAN OLDIN TEKSHIRING", [
    "{box}  *Present simple* bilan bitta gap — u odatda nima kiyadi.   {box}  *Present continuous* bilan "
    "ikki-uchta gap — hozir ustida nima bor.",
    "{box}  Kamida beshta kiyim soʻzi.   {box}  Sifatlar toʻgʻri tartibda — avval oʻlcham yoki uzunlik, keyin "
    "rang.   {box}  *wear* va *carry* toʻgʻri ishlatilgan.",
    "{box}  *-ing* larim toʻgʻri yozilgan: *wearing · carrying · standing · smiling · sitting*.   {box}  "
    "Soʻzlarni sanadim.",
])
h.one_per_line("OʻQIB BERISHDAN OLDIN TEKSHIRING", None, at="box")
h.retell_cells({"Spelling rule": "Imlo qoidasi", "Verb": "Feʼl", "-ing form": "<i>-ing</i> shakli",
                "most verbs — just add -ing": "koʻp feʼllar — shunchaki <i>-ing</i> qoʻshiladi",
                "ends in -e — drop the e": "<i>-e</i> bilan tugasa — <i>e</i> tushib qoladi",
                "one vowel + one consonant — double it": "bitta unli + bitta undosh — undosh ikkilanadi",
                "ends in -y — change nothing": "<i>-y</i> bilan tugasa — hech narsa oʻzgarmaydi"})
h.retell_cells({"What is written": "Yozilishi", "What you hear": "Eshitilishi", "Why": "Nega",
                "we're is weak and joins on": "<i>we're</i> kuchsiz va keyingi soʻzga qoʻshiladi",
                "the negative takes the stress": "urgʻu inkorga tushadi",
                "are you becomes one weak sound": "<i>are you</i> bitta kuchsiz tovushga aylanadi",
                "just is weak, off is strong": "<i>just</i> kuchsiz, <i>off</i> kuchli"},
               after="4.5  </span>")

# ------------------------------------------------------------------ the key
K = {}
BME = {"B": "B · Bahodir", "M": "M · Malika", "E": "E · Eldor"}
for n, a in enumerate("MEMEBE", 1):
    K[("1.2", n, 1)] = choose(["B", "M", "E"], a, labels=BME)
UN = {"U": "U · usually", "N": "N · right now"}
for n, a in enumerate("UNUNUN", 1):
    K[("1.3", n, 1)] = choose(["U", "N"], a, labels=UN)
for n, a in enumerate("ABAB", 1):
    K[("1.4", n, 1)] = choose(["A", "B", "C"], a)
for n, a in enumerate(["a customer/customer/customers", "a queue/queue", "a shelf/shelf/shelves", "tips/a tip/tip"], 1):
    K[("1.5", n, 1)] = Q(a)
for n in range(1, 5):
    K[("1.6", n, 1)] = own()
K[("1.7", 1, 1)] = own()
K[("1.7", 2, 1)] = own()
for n, a in enumerate(["is", "carrying", "know", "aren't", "quiet", "is", "longer"], 1):
    K[("1.8", n, 1)] = Q(a)
for n in range(1, 5):
    K[("1.9", n, 1)] = own()
for n, a in enumerate(["opens", "read", "queue", "hundred", "seconds", "quiet", "children", "shorter/better"], 1):
    K[("1.10", n, 1)] = Q(a)
for n, a in enumerate(["writing", "coming", "studying", "swimming", "shopping", "carrying", "getting", "making",
                       "running", "waiting"], 1):
    K[("2.1", n, 1)] = Q(a)
for key, a in (((1, 1), either("'m carrying", "am carrying")),
               ((2, 1), either("isn't reading", "is not reading", "'s not reading")), ((3, 1), "Are"),
               ((3, 2), "waiting"), ((4, 1), either("aren't serving", "are not serving", "'re not serving")),
               ((5, 1), either("is asking", "'s asking")), ((6, 1), "are"), ((6, 2), "doing"),
               ((7, 1), either("is looking", "'s looking")), ((8, 1), either("'m standing", "am standing"))):
    K[("2.2",) + key] = Q(a)
SC = {"S": "S · simple", "C": "C · continuous"}
for n, a in enumerate("CSCSCSCS", 1):
    K[("2.3", n, 1)] = choose(["S", "C"], a, labels=SC)
for n, a in enumerate(["open", "is sleeping", "is wearing", "wears", "are you doing", "do you do"], 1):
    K[("2.4", n, 1)] = choose(FORMS24[n], a)
for key, a in (((1, 1), "make"), ((1, 2), either("'m making", "am making")),
               ((2, 1), either("doesn't wear", "does not wear")), ((2, 2), either("'s wearing", "is wearing")),
               ((3, 1), "Do"), ((3, 2), "go"), ((4, 1), either("is taking", "'s taking")), ((5, 1), "closes"),
               ((5, 2), either("'re hurrying", "are hurrying")), ((6, 1), either("is studying", "'s studying"))):
    K[("2.5",) + key] = Q(a)
TICKED = "✓/correct/tick"
for n, a in zip(range(2, 9), [
        either("All the masks are really beautiful", "are"),
        either("Look — I'm standing in the middle of the square", "Look - I'm standing in the middle of the square",
               "I'm standing in the middle of the square", "I am standing in the middle of the square",
               "I'm standing"),
        either("I go to school every day", "go"),
        TICKED,
        either("He's studying English at the moment", "He is studying English at the moment", "He's studying English",
               "studying"),
        TICKED,
        either("They aren't swimming, they're just sitting", "They aren't swimming", "They are not swimming",
               "swimming")]):
    K[("2.6", n, 1)] = fix(a)
for n, a in enumerate([either("I'm reading right now", "I am reading right now", "I'm reading now"),
                       either("She usually talks to a customer", "She usually talks to customers",
                              "She usually talks to a customer.", "Usually she talks to a customer"),
                       either("We never serve food", "We never serve food today")], 1):
    K[("2.7", n, 1)] = write(a)
for n, a in enumerate([either("'m standing", "am standing"), either("'m looking", "am looking"),
                       either("'s waiting", "is waiting"), "says", "is", "meet", either("'s raining", "is raining"),
                       either("'s dying", "is dying"), either("'m not enjoying", "am not enjoying")], 1):
    K[("2.8", n, 1)] = Q(a)
for n, (question, short) in enumerate([
        ("Are you studying English at the moment", "Yes, I am/No, I'm not/No, I am not"),
        ("Is your family having dinner right now",
         "Yes, it is/No, it isn't/No, it's not/Yes, they are/No, they aren't/No, they're not"),
        ("Do you usually go shopping on Saturdays", "Yes, I do/No, I don't/No, I do not")], 1):
    K[("2.9", n, 1)] = write(question)
    K[("2.9", n, 2)] = Q(short)
for n, a in enumerate("BACB", 1):
    K[("2.10", n, 1)] = choose(["A", "B", "C"], a)
K[("2.11", 1, 1)] = own()
K[("2.11", 2, 1)] = own()
for n in range(1, 5):                             # a partner's answers, in class
    K[("2.12", n, 1)] = pair()
SHOPS = ["a bookshop", "a chemist", "a clothes shop", "a department store", "a café", "a fast food restaurant"]
for n, a in enumerate(["a chemist", "a bookshop", "a clothes shop/a department store", "a fast food restaurant",
                       "a café", "a department store"], 1):
    K[("3.1", n, 1)] = choose(SHOPS, a)
PLACES = ["the entrance", "the stairs", "the information desk", "the cash machine", "the car park", "the bus stop"]
for n, a in enumerate(["the cash machine", "the information desk", "the car park", "the bus stop", "the entrance",
                       "the stairs"], 1):
    K[("3.2", n, 1)] = choose(PLACES, a)
for n, words in STRESS33.items():
    parts = ["book", "shop"] if words == "bookshop" else words.split()
    K[("3.3", n, 1)] = choose(parts, parts[0])
GROUP34 = {"feet": "On your feet", "hands": "Hands / arms", "rest": "The rest"}
FEET, HANDS = {"boots", "socks", "trainers"}, {"gloves", "ring", "watch"}
for n, w in enumerate(WORDS34, 1):
    K[("3.4", n, 1)] = choose(["feet", "hands", "rest"], "feet" if w in FEET else "hands" if w in HANDS else "rest",
                              labels=GROUP34)
PAIR = ["a", "a pair of", "–"]
for n, a in enumerate(["a pair of", "a", "a pair of", "–", "a", "a pair of"], 1):
    K[("3.5", n, 1)] = choose(PAIR, a)
SOUND = {"1": "1 /ɒ/", "2": "2 /uː/", "3": "3 /ʌ/", "4": "4 /əʊ/"}
for n, a in enumerate("12341234", 1):
    K[("3.6", n, 1)] = choose(["1", "2", "3", "4"], a, labels=SOUND)
for n in range(1, 7):                             # letters to cross out: the teacher reads them
    K[("3.7", n, 1)] = own(control=None)
for n, a in enumerate(["bus", "coat", "scarf", "boots", "department", "watch/phone"], 1):
    K[("3.8", n, 1)] = Q(a)
for n, a in {1: "gloves", 2: "entrance", 3: "stairs", 4: "belt"}.items():
    K[("3.9", n, 1)] = choose(ODD39[n], a)
    K[("3.9", n, 2)] = own()
for n, a in enumerate([
        either("She's wearing jeans", "She is wearing jeans", "She's wearing a pair of jeans",
               "She is wearing a pair of jeans", "jeans", "a pair of jeans"),
        either("I bought a new piece of jewellery", "I bought some new jewellery", "I bought new jewellery",
               "a new piece of jewellery", "some jewellery"),
        either("He's putting on his gloves", "He is putting on his gloves", "his gloves", "gloves"),
        either("We waited at the bus stop for twenty minutes", "the bus stop", "bus stop")], 1):
    K[("3.10", n, 1)] = write(a)
for key, a in (((1, 1), either("'m putting on", "am putting on")),
               ((1, 2), "coat/jacket/gloves/scarf/boots/hat/jumper/sweater"),
               ((2, 1), "try on"), ((2, 2), "shirt/one/size"),
               ((3, 1), either("'s taking off", "is taking off")),
               ((3, 2), "jumper/coat/jacket/scarf/sweater/shirt"),
               ((4, 1), "wears"), ((4, 2), "dress/skirt/hat/suit/tie")):
    K[("3.11",) + key] = Q(a)
BOX312 = ["change", "fit", "receipt", "returns", "size", "smaller", "wrong"]
for n, a in enumerate(["returns", "fit", "wrong", "smaller", "receipt", "change", "size"], 1):
    K[("3.12", n, 1)] = choose(BOX312, a)
for n, a in enumerate("cabd", 1):
    K[("3.13", n, 1)] = choose(ENDS313, a)
for n, a in {1: "entrance", 2: "scarf", 3: "jumper", 4: "shoes"}.items():
    K[("3.14", n, 1)] = choose(ODD314[n], a)
    K[("3.14", n, 2)] = own()
for n, a in enumerate("ABCA", 1):
    K[("3.15", n, 1)] = choose(["A", "B", "C"], a)
for n in range(1, 5):                             # a partner's answers, in class
    K[("3.16", n, 1)] = pair()
K[("4.1", 1, 1)] = own()
K[("4.2", 1, 1)] = write("Go and see a film/see a film/go to the cinema/watch a film/a film/go to see a film")
K[("4.2", 2, 1)] = write("About seven/seven/at seven/7/about 7/around seven/at around seven/at about seven/"
                         "7 o'clock/seven o'clock/at 7")
K[("4.2", 3, 1)] = own()
WHERE43 = ["the bookshop", "the bus stop", "the department store", "the cash machine", "the café", "the entrance"]
for n, a in enumerate(["the bookshop", "the bus stop", "the department store", "the cash machine"], 1):
    K[("4.3", n, 1)] = choose(WHERE43, a)
for key, a in (((1, 1), "having"), ((2, 1), "buying"), ((3, 1), "getting"), ((4, 1), "meet"), ((5, 1), "buying"),
               ((5, 2), "looking")):
    K[("4.4",) + key] = Q(a)
PM = {"+": "+ positive", "−": "− negative"}
for n, a in enumerate(["+", "−", "+", "−"], 1):
    K[("4.7", n, 1)] = choose(["+", "−"], a, labels=PM)
for n in (1, 2, 3):
    K[("4.8", n, 1)] = choose(["A", "B"], "B")
for n, a in enumerate("BA", 1):
    K[("5.1", n, 1)] = choose(["A", "B", "C"], a)
HEARD = {"yes": "✓ heard", "no": "✗ not heard"}
for n, a in enumerate(["yes", "yes", "yes", "yes", "no", "yes", "no", "no"], 1):
    K[("5.2", n, 1)] = choose(["yes", "no"], a, labels=HEARD)
TF = {"T": "T · true", "F": "F · false"}
for n, a in enumerate("FTFT", 1):
    K[("5.3", n, 1)] = choose(["T", "F"], a, labels=TF)
    K[("5.3", n, 2)] = note()
for n in range(1, 5):
    K[("5.4", n, 1)] = own()
for n, a in enumerate(["a long blue dress", "a big green jumper", "old black boots"], 1):
    K[("5.5", n, 1)] = Q(a)
for n, a in enumerate(["carrying", "wearing", "carrying", "wearing"], 1):
    K[("5.6", n, 1)] = choose(["wearing", "carrying"], a)
for n in range(1, 5):
    K[("5.8", n, 1)] = own()
K[("5.9", 1, 1)] = own(control="essay")
for n in range(1, 8):                             # the checklist
    K[("5.10", 4, n)] = tick()

if __name__ == "__main__":
    data = h.build(K, "Elementary", 9, "Unit 9A & 9B — Clothes and shopping")
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "e09ab.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
