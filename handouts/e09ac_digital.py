"""E09AC Clothes and shopping - Azamat's Elementary booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(E09AC Clothes and shopping - answer key), joined box by box by hand. The
Desktop "new design" copy is used; it splits into its five parts as it
should. E09AB covers 9A too; the one he sets is the one that counts.

As with the other Elementary booklets, it speaks Uzbek wherever it
explains: every explanation box, the goals, the headings of the grammar
table, the "Why" column of the listening table, and a line under every
instruction. The English examples stay English, as do the reading text,
the dialogues, the model and the exercises.

Put right here: 2.7 says TWO sentences are correct, but three are (3, 6 and
8, as the key has it): it says THREE. In 2.12 the answer is shown first and
the box for the question under it; the key gives samples, so the teacher
reads them, as with 2.9, 2.15 (the whole message again) and 3.14.
3.4 (a partner's prices), 3.11 (a map), 5.6 (marking the joins) and the
speaking tasks are done in class and get no boxes.

    python3 handouts/e09ac_digital.py            # writes handouts/e09ac.json, lists every box
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

DOCX = ("~/Desktop/Handouts/A2 Elementary/E09AC Clothes and shopping/"
        "E09AC Clothes and shopping — handout (new design).docx")
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


def answer_first(label, hint):
    """"Write the question for this answer": the answer, then the box under it."""
    for m in reversed(h._items(label)):
        tag = BLANK_TAG.search(m.group(4))
        said = re.sub(r"^\d+\s*\?\s*", "", plain(m.group(4))).strip()
        h.hints[int(tag.group(1))] = hint
        h.html = (h.html[:m.start()] + m.group(1) + NUM_SPAN % int(m.group(3))
                  + TEXT_SPAN % html.escape(said, quote=False) + "<br>" + tag.group(0) + "</p>" + h.html[m.end():])


def spoken(*forms):
    """A number in words, with and without its hyphens: ninety-nine, ninety nine."""
    out = []
    for f in forms:
        out += [f] + ([f.replace("-", " ")] if "-" in f else [])
    return "/".join(out)


def syllables(word):
    return re.split(r"[- ]", word)


# ------------------------------------------------------------ 1 Reading
boxes_for("1.2", range(1, 6), where="options")
h.options_on_lines("1.2")
for n in range(1, 6):
    h.item_box("1.3", n, placeholder="If it is false, correct it")
a, b = section("1.3"), section("1.4")             # the ruled lines the boxes replace
h.html = h.html[:a] + LEADER_P.sub("", h.html[a:b]) + h.html[b:]
boxes_for("1.4", range(1, 5), where="leader")
boxes_for("1.5", range(1, 5), where="leader")
h.leaders("1.6", "1.7  </span>", [(1, W, "Four examples: am / is / are + verb + -ing")])
h.hints[17] = "What they have in common"
boxes_for("1.9", range(1, 5), where="leader")

# ------------------------------------------------------------ 2 Grammar
reword("2.7", "Find and correct the mistake. TWO sentences are correct — tick them.",
       "Find and correct the mistake. THREE sentences are correct — tick them.")
boxes_for("2.7", range(2, 9))                     # item 1 is the worked example
answer_first("2.12", "Your question")
h.options_on_lines("2.13")
at = h.html.index("hurry up!", section("2.15"))
at = h.html.index("</table>", at) + len("</table>")      # the end of the message's box
h.html = (h.html[:at] + '<p style="margin-bottom:8px">{{box:2.15:1:95%:The message again, with the six mistakes '
          'corrected}}</p>' + h.html[at:])
h.texts[("2.15", 1)] = "The message, corrected"
h.leaders("2.16", "3.1  </span>", [(1, W, "Four sentences about your family now")])

# ------------------------------------------------------------ 3 Vocabulary
STRESS35 = {1: "book-shop", 2: "de-part-ment store", 3: "chem-ist", 4: "in-for-ma-tion desk", 5: "cash ma-chine",
            6: "fit-ting room"}
boxes_for("3.5", STRESS35)
ENDS38 = halves("3.8", "a-d")
ODD39 = {1: ["café", "restaurant", "chemist", "burger bar"], 2: ["stairs", "lift", "entrance", "bookshop"],
         3: ["cash machine", "ATM", "money", "card"], 4: ["clothes shop", "shoe shop", "department store", "car park"]}
boxes_for("3.9", ODD39)
boxes_for("3.10", range(1, 5), where="leader")
h.options_on_lines("3.15")

# ------------------------------------------------------------ 4 Listening
h.leaders("4.1", "4.2  </span>", [(1, W, "What can go wrong?")])
WHERE43 = {1: ["in the bookshop", "in a café"], 2: ["at the bus stop", "in the car park"],
           3: ["in the department store", "in a café"], 4: ["at the cash machine", "at the entrance"]}
boxes_for("4.3", WHERE43)
h.leaders("4.5", "WHY YOU DIDN", [(1, W, "The problem, and how Susie feels")])
boxes_for("4.8", (1, 2, 3))
h.options_on_lines("4.8")

# ------------------------------------------------------ 5 Everyday English
ANSWERS51 = halves("5.1", "a-d")
boxes_for("5.4", range(1, 5), where="leader")
boxes_for("5.8", range(1, 5), where="leader")
h.leaders("5.9", "CHECK BEFORE", [(20, W, "Write your conversation here")])

# ------------------------------- every instruction, once more, in Uzbek
for label, text in [
        ("1.1", "Muhokama qiling. Kiyimni qayerdan sotib olasiz? Shahringizda doʻstlaringiz bilan qayerda "
                "uchrashasiz?"),
        ("1.2", "Eng toʻgʻri javobni tanlang: *A*, *B* yoki *C*."),
        ("1.3", "Toʻgʻri (*T*) mi yoki notoʻgʻri (*F*) mi? Notoʻgʻrilarini toʻgʻrilab yozing."),
        ("1.4", "Matndan shu maʼnodagi soʻzni toping."),
        ("1.5", "Savollarga javob bering."),
        ("1.6", "Oxirgi xatboshidan *am / is / are* + feʼl + *-ing* ning TOʻRTTA misolini toping."),
        ("1.7", "Matndagi har bir iborani BITTA soʻz bilan toʻldiring."),
        ("1.8", "Uchrashish uchun yaxshi joymi (*✓*) yoki yomon joymi (*✗*)? Muallifning qoidasini ishlating."),
        ("1.9", "Matn haqidagi har bir gapdagi xatoni topib, toʻgʻrilang."),
        ("1.10", "Shahringizda uchrashish uchun qayer yaxshi joy? Sherigingizga nega ekanini ayting."),
        ("2.1", "*-ing* shaklini yozing."),
        ("2.2", "Imloni toʻgʻrilang."),
        ("2.3", "*Present continuous* bilan toʻldiring."),
        ("2.4", "Gaplarni inkor shaklda yozing."),
        ("2.5", "Savollar yozing."),
        ("2.6", "Qisqa javob yozing."),
        ("2.7", "Xatoni topib, toʻgʻrilang. UCHTA gap toʻgʻri — ular uchun *✓ It is correct* tugmasini bosing."),
        ("2.8", "Telefondagi suhbatni toʻldiring."),
        ("2.9", "Bu odamlarni koʻz oldingizga keltiring. Ular hozir nima qilyapti? Yozing."),
        ("2.10", "Soʻzlarni tartib bilan yozing."),
        ("2.11", "Oʻzingiz haqingizdagi savollarga qisqa javob bering."),
        ("2.12", "Har bir javob uchun savol yozing."),
        ("2.13", "Toʻgʻri javobni tanlang: *A*, *B* yoki *C*."),
        ("2.14", "*be* ning toʻgʻri shaklini tanlang."),
        ("2.15", "Xabardagi oltita xatoni toʻgʻrilang. Xabarni toʻgʻri qilib qayta yozing."),
        ("2.16", "Oilangizdagi odamlar hozir nima qilayotgani haqida toʻrtta gap yozing."),
        ("3.1", "Bu narsalarni qayerdan sotib olasiz? Doʻkonni tanlang."),
        ("3.2", "Qutidagi soʻz bilan toʻldiring."),
        ("3.3", "Narxlarni ayting va soʻz bilan yozing."),
        ("3.4", "Sherigingizni tinglang. Qaysi narxni eshitdingiz? Uni belgilang. Buni sinfda bajarasiz."),
        ("3.5", "Soʻz urgʻusi. Urgʻuli qismni tanlang, keyin ovoz chiqarib ayting."),
        ("3.6", "Bu odamlar qayerga borishi mumkin? Joyni yozing."),
        ("3.7", "Matnni xarid soʻzlari bilan toʻldiring."),
        ("3.8", "Ikki qismni moslang: harfni tanlang."),
        ("3.9", "Qaysi soʻz boshqacha? Uni tanlang."),
        ("3.10", "Har bir gapdagi xatoni topib, toʻgʻri gapni yozing."),
        ("3.11", "Oʻzingiz biladigan savdo markazining oddiy xaritasini chizing. Oltita joyni belgilang."),
        ("3.12", "Savdo markazidagi yoʻl koʻrsatishni toʻldiring."),
        ("3.13", "Narxni soʻz bilan yozing."),
        ("3.14", "Har bir kishi nima qilyapti? Xarid soʻzi va *present continuous* ni ishlating."),
        ("3.15", "Toʻgʻri javobni tanlang: *A*, *B* yoki *C*."),
        ("3.16", "Qaysi qavat? Tartib son bilan toʻldiring."),
        ("3.17", "Gaplarni xarid soʻzi va predlog bilan toʻldiring."),
        ("3.18", "Sherigingizga oxirgi marta xarid qilganingiz haqida gapirib bering. Bu boʻlimdan beshta soʻz "
                 "ishlating."),
        ("4.1", "Tinglashdan oldin taxmin qiling. Toʻrt kishi katta savdo markazida uchrashmoqchi boʻlsa, nima "
                "notoʻgʻri ketishi mumkin?"),
        ("4.2", "1-suhbatni tinglang. Savollarga javob bering."),
        ("4.3", "2- va 3-suhbatlarni tinglang. Har bir kishi qayerda? Javobni tanlang."),
        ("4.4", "Yana tinglang va har bir qatorni toʻldiring."),
        ("4.5", "4-suhbatni tinglang. Muammo nima va Susie oʻzini qanday his qilyapti?"),
        ("4.6", "Tinglang va nima boʻlishiga eʼtibor bering."),
        ("4.7", "Har bir savolni ikki marta ayting — avval sekin, keyin tez."),
        ("4.8", "Gapiruvchi nima demoqchi? *A* yoki *B* ni tanlang."),
        ("5.1", "Kiyim tanlash. Savolni javob bilan moslang: harfni tanlang."),
        ("5.2", "Har bir iborani BITTA soʻz bilan toʻldiring."),
        ("5.3", "Narsa haqidami (*T*) yoki odam haqidami (*P*)?"),
        ("5.4", "Har bir gapdagi xatoni topib, toʻgʻri gapni yozing."),
        ("5.5", "Birlikmi yoki koʻplikmi? Ikkala suhbatni toʻldiring."),
        ("5.6", "Soʻzlar qayerda qoʻshilishini belgilang. Keyin har bir qatorni tez ayting."),
        ("5.7", "Namunaviy suhbatni oʻqing. Keyin savollarga javob bering."),
        ("5.8", "Namuna haqidagi savollarga javob bering."),
        ("5.9", "Oʻz suhbatingizni yozing (10–12 qator). Kiyim doʻkonida biror narsa sotib oling.")]:
    h.say_also(label, text)

# ------------------------------------------ the explanations, told in Uzbek
h.goals([
    "odamlar hozir nima qilayotganini aytishni va bu haqda soʻrashni",
    "*-ing* shaklini toʻgʻri yozishni",
    "doʻkonlarni nomlashni va narxlarni aytishni",
    "qayerda uchrashishni kelishayotgan odamlarni tushunishni",
    "kiyim soʻrashni, uni kiyib koʻrishni va pul toʻlashni",
])
h.retell("KEY WORDS", "KALIT SOʻZLAR", [
    "**a shopping centre**  savdo markazi — koʻp doʻkonli katta bino",
    "**an entrance**  kirish joyi — ichkariga kiradigan eshik",
    "**a floor**  qavat — binoning bir darajasi",
    "**to arrange**  kelishmoq — vaqt va joyni rejalashtirmoq",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — PRESENT CONTINUOUS", [
    "*Present continuous* ni hozir, shu daqiqada boʻlayotgan narsa uchun ishlating.",
    "[[A]] Tasdiq: *am / is / are* + feʼl + *-ing*. *I'm waiting. · He's buying a book. · They're looking at "
    "furniture.*",
    "[[B]] Inkor: *am / is / are* dan keyin *not* qoʻying. *I'm not waiting. · We aren't buying anything. · "
    "She's not coming.*",
    "[[C]] Soʻroq: *am / is / are* ni oldinga qoʻying. *Are you having a coffee? · Is he parking the car? · What "
    "are you doing?*",
    "[[D]] Qisqa javoblar: *Yes, I am. · No, I'm not. · Yes, she is. · No, she isn't.* — hech qachon *Yes, I'm.*",
    "**-ing ning imlosi:** koʻp feʼllarga shunchaki *-ing* qoʻshiladi — *wait → waiting*. *-e* bilan tugaydigan "
    "feʼllarda *e* tushib qoladi — *come → coming*. Bitta unlili qisqa feʼllarda oxirgi harf ikkilanadi — "
    "*shop → shopping*.",
])
h.retell("ERROR WARNING", "DIQQAT — KOʻP UCHRAYDIGAN XATOLAR", [
    "Darslik eng avvalo bitta narsadan ogohlantiradi: *-ing* shaklining imlosi. Eng koʻp xato qilinadigan "
    "beshtasi:",
    "✗ *writting* → ✓ *writing* · ✗ *comeing / comming* → ✓ *coming*",
    "✗ *studing* → ✓ *studying* · ✗ *swiming* → ✓ *swimming* · ✗ *geting* → ✓ *getting*",
    "Har safar yana ikki narsani tekshiring:",
    "**be ni hech qachon tushirib qoldirmang.** ✗ *I waiting at the entrance.* → ✓ *I'm waiting at the "
    "entrance.*",
    "**Qisqa javobda qisqartma ishlatmang.** ✗ *Yes, I'm.* → ✓ *Yes, I am.*",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — XARID", [
    "Ikki toʻplam: doʻkonlarning oʻzi va savdo markazining qismlari.",
    "[[A]] Doʻkonlar: *a café · a bookshop · a fast food restaurant · a clothes shop · a chemist · a department "
    "store · a supermarket · a shoe shop*",
    "[[B]] Savdo markazining qismlari: *an entrance · stairs · a lift · a car park · a bus stop · an information "
    "desk · a cash machine (an ATM) · a fitting room*",
    "[[C]] Narxlarni aytish: *£4.99 = four ninety-nine · £115.97 = a hundred and fifteen ninety-seven · €49.99 = "
    "forty-nine ninety-nine*",
    "[[D]] Bu juftliklarda ehtiyot boʻling: *£19* va *£90* · *£13* va *£30* · *£17* va *£70*. Urgʻu koʻchadi: "
    "*nineTEEN*, lekin *NINEty*.",
    "**Soʻz urgʻusi:** *BOOK-shop · de-PART-ment store · CHEM-ist · in-for-MA-tion desk · CASH ma-chine*",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [
    "Toʻrtta qisqa telefon suhbatini eshitasiz. Toʻrt doʻst savdo markazida uchrashmoqchi, lekin ishlari "
    "yurishmaydi.",
    "Agar sinfingizda audio boʻlsa, bu 09.03–09.06-treklar. Boʻlmasa, oʻqituvchingiz matnni oʻqib beradi — "
    "topshiriqlar bir xil.",
])
h.retell("WHY YOU DIDN'T HEAR IT", "NEGA ESHITMADINGIZ?", [
    "*are you*, *is he* va *what are* da kichik soʻzlar bir-biriga qoʻshilib, tovushini yoʻqotadi. *Are you "
    "having* → /əjə hævɪŋ/, *what are you doing* → /wɒtəjə duːɪŋ/ boʻlib eshitiladi.",
    "Baland soʻz doim *-ing* li feʼl — oʻshanga quloq soling va orqaga qarab tushuning.",
])
h.retell("THREE MOMENTS IN A CLOTHES SHOP", "KIYIM DOʻKONIDAGI UCH LAHZA", [
    "Ingliz tilida kiyim sotib olish aslida uchta qisqa suhbat. Har biri uchun bir toʻplam ibora oʻrganing:",
    "1 **Tanlash** — oʻlcham, rang, nima qidirayotganingiz. 2 **Kiyib koʻrish.** 3 **Pul toʻlash.**",
])
h.retell("SAYING SOMETHING IS NICE", "BIROR NARSA CHIROYLI EKANINI AYTISH", [
    "Ikki xil qolip bor, va farqi muhim:",
    "*That looks great.* → narsa haqida.",
    "*It looks really good on you.* → uni kiygan odam haqida. Maʼnoni *on you* soʻzlari oʻzgartiradi.",
    "Boshqalari: *That suits you. · That's a nice colour on you. · I like those.*",
])
h.retell("ERROR WARNING", "DIQQAT — DOʻKONDAGI UCH XATO", [
    "Yozuvda eshitiladigan uchta xato — uchalasini ham tayyor ibora qilib yodlab oling:",
    "✗ *I take them.* → ✓ *I'll take them.* (doʻkonda „sotib olaman“ shunday deyiladi)",
    "✗ *How much they are?* → ✓ *How much are they?* (bu savol — feʼl oldin keladi)",
    "✗ *Can I pay with card?* → ✓ *Can I pay by card?* (naqd pul uchun *in cash* deyiladi: *in cash* yoki "
    "*by card*)",
])
h.retell("JOINING WORDS", "SOʻZLARNING QOʻSHILISHI", [
    "Soʻz undosh tovush bilan tugab, keyingi soʻz unli tovush bilan boshlansa, undosh keyingi soʻzga oʻtib, unga "
    "qoʻshiladi:",
    "*Can I help you?* → /kæ naɪ/ · *I'll take it.* → /teɪ kɪt/ · *Where are the fitting rooms?* → /weə rɑː/",
    "Shuning uchun yaxshi biladigan soʻzlaringizni ham koʻpincha tanimay qolasiz. Soʻz oʻzgarmagan — shunchaki "
    "birinchi tovushi oldinroq kelib qolgan.",
])
h.retell("CHECK BEFORE YOU PRACTISE IT", "MASHQ QILISHDAN OLDIN TEKSHIRING", [
    "{box}  Oʻlcham va rang haqida soʻradim.   {box}  Kiyib koʻrishni soʻradim.   {box}  Narxini feʼlni oldin "
    "qoʻyib soʻradim.",
    "{box}  *I take it* emas, *I'll take it / them* dedim.   {box}  *Can I pay by card?* deb soʻradim.",
    "{box}  Kimdir *on you* bilan yoqimli gap aytdi.   {box}  Ovoz chiqarib aytdim va soʻzlarni qoʻshdim.",
])
h.one_per_line("MASHQ QILISHDAN OLDIN TEKSHIRING", None, at="box")
h.retell_cells({"Positive +": "Tasdiq +", "Negative −": "Inkor −", "Question ?": "Soʻroq ?"})
h.retell_cells({"What is written": "Yozilishi", "What you hear": "Eshitilishi", "Why": "Nega",
                "are you → /əjə/": "<i>are you</i> → /əjə/",
                "what are you → one blur": "<i>what are you</i> bitta tovushga qoʻshilib ketadi",
                "just loses its t": "<i>just</i> dagi <i>t</i> yoʻqoladi",
                "aren't is short and quiet": "<i>aren't</i> qisqa va past aytiladi"},
               after="4.6  </span>")

# ------------------------------------------------------------------ the key
K = {}
for n, a in enumerate("BBACB", 1):
    K[("1.2", n, 1)] = choose(["A", "B", "C"], a)
TF = {"T": "T · true", "F": "F · false"}
for n, a in enumerate("TFTFT", 1):
    K[("1.3", n, 1)] = choose(["T", "F"], a, labels=TF)
    K[("1.3", n, 2)] = note()
for n, a in enumerate(["a shopping centre/shopping centre", "an entrance/entrance/entrances", "a floor/floor/floors",
                       "enormous"], 1):
    K[("1.4", n, 1)] = Q(a)
for n in range(1, 5):
    K[("1.5", n, 1)] = own()
K[("1.6", 1, 1)] = own()
for n, a in enumerate(["standing", "think", "make", "one", "lost", "happy"], 1):
    K[("1.7", n, 1)] = Q(a)
GOOD = {"yes": "✓ good", "no": "✗ bad"}
for n, a in enumerate(["no", "yes", "no", "yes", "no", "yes"], 1):
    K[("1.8", n, 1)] = choose(["yes", "no"], a, labels=GOOD)
K[("1.8", 6, 2)] = own()
for n in range(1, 5):
    K[("1.9", n, 1)] = own()
for n, a in zip(range(2, 9), ["coming", "writing", "shopping", "studying", "swimming", "getting", "looking"]):
    K[("2.1", n, 1)] = Q(a)
for n, a in enumerate(["writing", "coming", "studying", "swimming", "getting", "buying"], 1):
    K[("2.2", n, 1)] = Q(a)
for key, a in (((1, 1), either("'m waiting", "am waiting")), ((2, 1), either("'s buying", "is buying")),
               ((3, 1), either("aren't buying", "are not buying", "'re not buying")),
               ((3, 2), either("'re just looking", "are just looking")), ((4, 1), either("'s getting", "is getting")),
               ((5, 1), either("'re having", "are having")),
               ((6, 1), either("'m not standing", "am not standing")), ((7, 1), either("'re looking", "are looking")),
               ((8, 1), either("are running", "'re running"))):
    K[("2.3",) + key] = Q(a)
for n, a in enumerate([either("I'm not having a coffee", "I am not having a coffee"),
                       either("She isn't buying furniture", "She's not buying furniture", "She is not buying furniture"),
                       either("They aren't waiting at the bus stop", "They're not waiting at the bus stop",
                              "They are not waiting at the bus stop"),
                       either("We aren't getting off the bus", "We're not getting off the bus",
                              "We are not getting off the bus")], 1):
    K[("2.4", n, 1)] = write(a)
for n, a in enumerate(["Are you having a coffee", "Is he buying furniture", "What are you doing",
                       "Where are they waiting", "Why is she laughing"], 1):
    K[("2.5", n, 1)] = write(a)
for n, a in enumerate(["Yes, I am", "No, he isn't/No, he's not/No, he is not", "Yes, they are",
                       "No, she isn't/No, she's not/No, she is not"], 1):
    K[("2.6", n, 1)] = Q(a)
TICKED = "✓/correct/tick"
for n, a in zip(range(2, 9), [
        either("She's writing a message", "She is writing a message", "writing"),
        TICKED,
        either("Are you having a coffee", "having"),
        either("Yes, I am", "I am"),
        TICKED,
        either("They're coming now", "They are coming now", "coming"),
        TICKED]):
    K[("2.7", n, 1)] = fix(a)
for n, a in enumerate(["are you", "Are you having", either("'m not having", "am not having"),
                       either("'m buying", "am buying"), "are you doing", either("'m getting", "am getting"),
                       "are you calling/can you call", either("'s waiting", "is waiting")], 1):
    K[("2.8", n, 1)] = Q(a)
for n in range(1, 5):                             # what they picture: theirs to write
    K[("2.9", n, 1)] = own()
for n, a in enumerate([either("I'm waiting at the entrance", "I am waiting at the entrance"),
                       either("We aren't buying anything", "We are not buying anything"),
                       "What are you doing", "Is he getting some cash"], 1):
    K[("2.10", n, 1)] = write(a)
ME = "Yes, I am/No, I'm not/No, I am not"
for n, a in enumerate([ME, "Yes, it is/No, it isn't/No, it's not/No, it is not", ME,
                       "Yes, he is/No, he isn't/No, he's not/Yes, she is/No, she isn't/No, she's not"], 1):
    K[("2.11", n, 1)] = Q(a)
for n in range(1, 5):                             # samples in the key: many right questions
    K[("2.12", n, 1)] = own()
for n, a in enumerate("BACA", 1):
    K[("2.13", n, 1)] = choose(["A", "B", "C"], a)
for n, a in enumerate(["am", "is", "are", "is", "are", "are"], 1):
    K[("2.14", n, 1)] = choose(["am", "is", "are"], a)
K[("2.15", 1, 1)] = own()
K[("2.16", 1, 1)] = own()
SHOPS = ["a café", "a bookshop", "a fast food restaurant", "a clothes shop", "a chemist", "a department store",
         "a supermarket", "a shoe shop"]
for n, a in enumerate(["a chemist", "a bookshop", "a clothes shop/a department store", "a fast food restaurant",
                       "a supermarket", "a café"], 1):
    K[("3.1", n, 1)] = choose(SHOPS, a)
BOX32 = ["entrance", "stairs", "car park", "cash machine", "information desk", "fitting room", "lift", "bus stop"]
for key, a in (((1, 1), "cash machine"), ((2, 1), "information desk"), ((3, 1), "car park"), ((4, 1), "fitting room"),
               ((5, 1), "entrance"), ((6, 1), "lift"), ((6, 2), "stairs")):
    K[("3.2",) + key] = choose(BOX32, a)
for n, a in enumerate([spoken("four ninety-nine", "four pounds ninety-nine", "four pounds ninety-nine pence"),
                       spoken("nineteen fifty", "nineteen pounds fifty", "nineteen pounds fifty pence"),
                       spoken("ninety pounds", "ninety"),
                       spoken("a hundred and fifteen ninety-seven", "one hundred and fifteen ninety-seven",
                              "a hundred and fifteen pounds ninety-seven", "one hundred and fifteen pounds ninety-seven"),
                       spoken("thirteen seventy-five", "thirteen euros seventy-five"),
                       spoken("thirty euros", "thirty")], 1):
    K[("3.3", n, 1)] = Q(a)
STRESSED = {1: "book", 2: "part", 3: "chem", 4: "ma", 5: "cash", 6: "fit"}
for n, word in STRESS35.items():
    K[("3.5", n, 1)] = choose(syllables(word), STRESSED[n])
for n, a in enumerate(["the chemist/a chemist/chemist/the chemist's/a chemist's",
                       "the fitting room/the fitting rooms/fitting room/fitting rooms/a fitting room",
                       "the cash machine/a cash machine/cash machine/the ATM/an ATM/ATM",
                       "the information desk/an information desk/information desk",
                       "a fast food restaurant/the fast food restaurant/fast food restaurant/a fast-food restaurant/"
                       "fast-food restaurant"], 1):
    K[("3.6", n, 1)] = Q(a)
for n, a in enumerate(["car park", "lift", "clothes shop/department store", "fitting room/fitting rooms",
                       "cash machine/ATM", "fast food restaurant/fast-food restaurant", "chemist/chemist's",
                       "bookshop"], 1):
    K[("3.7", n, 1)] = Q(a)
for n, a in enumerate("bcad", 1):
    K[("3.8", n, 1)] = choose(ENDS38, a)
for n, a in enumerate(["chemist", "bookshop", "card", "car park"], 1):
    K[("3.9", n, 1)] = choose(ODD39[n], a)
for n, a in enumerate([
        either("I'm going to the chemist's shop to buy aspirin", "I'm going to the chemist to buy aspirin",
               "I'm going to the chemist's to buy aspirin", "to buy aspirin", "to buy"),
        either("Where are the fitting rooms", "are"),
        spoken("It costs nineteen ninety-nine exactly", "It costs nineteen ninety-nine", "nineteen ninety-nine",
               "It costs nineteen pounds ninety-nine exactly"),
        either("We're meeting at the entrance to the cinema on the third floor",
               "We are meeting at the entrance to the cinema on the third floor",
               "We're meeting at the entrance of the cinema on the third floor",
               "We are meeting at the entrance of the cinema on the third floor",
               "the entrance to the cinema on the third floor", "on the third floor")], 1):
    K[("3.10", n, 1)] = write(a)
for n, a in enumerate(["ground/first/second/third/fourth", "lift/stairs/escalator", "cash", "entrance",
                       "car park"], 1):
    K[("3.12", n, 1)] = Q(a)
for n, a in enumerate([spoken("seven fifty", "seven pounds fifty"), spoken("sixteen pounds", "sixteen"),
                       spoken("sixty pounds", "sixty"),
                       spoken("twenty-four ninety-nine", "twenty-four pounds ninety-nine")], 1):
    K[("3.13", n, 1)] = Q(a)
for n in range(1, 5):                             # samples in the key
    K[("3.14", n, 1)] = own()
for n, a in enumerate("BBBC", 1):
    K[("3.15", n, 1)] = choose(["A", "B", "C"], a)
for n, a in enumerate(["ground", "first", "second", "third"], 1):
    K[("3.16", n, 1)] = Q(a)
for key, a in (((1, 1), "at/by"), ((1, 2), "to/of"), ((2, 1), "on"), ((3, 1), "at/from"), ((4, 1), "on/in"),
               ((4, 2), "of/in")):
    K[("3.17",) + key] = Q(a)
K[("4.1", 1, 1)] = own()
K[("4.2", 1, 1)] = write("At the shopping mall, at around seven/at the shopping mall/at the mall/the shopping mall/"
                         "the mall/at the shopping centre/the shopping centre/at the shopping mall at around seven")
K[("4.2", 2, 1)] = own()
for n, a in enumerate(["in the bookshop", "at the bus stop", "in the department store", "at the cash machine"], 1):
    K[("4.3", n, 1)] = choose(WHERE43[n], a)
for key, a in (((1, 1), "having"), ((2, 1), "buying"), ((3, 1), "getting"), ((4, 1), "getting"), ((5, 1), "looking"),
               ((6, 1), "aren't"), ((6, 2), "looking")):
    K[("4.4",) + key] = Q(a)
K[("4.5", 1, 1)] = own()
for n, a in enumerate("BAB", 1):
    K[("4.8", n, 1)] = choose(["A", "B"], a)
for n, a in enumerate("bdac", 1):
    K[("5.1", n, 1)] = choose(ANSWERS51, a)
for n, a in enumerate(["size", "colour/color", "on", "fitting", "much", "by"], 1):
    K[("5.2", n, 1)] = Q(a)
TP = {"T": "T · the thing", "P": "P · the person"}
for n, a in enumerate("TPTPTP", 1):
    K[("5.3", n, 1)] = choose(["T", "P"], a, labels=TP)
for n, a in enumerate([either("OK, I'll take them", "I'll take them", "OK, I will take them", "I will take them"),
                       "How much are they", "Can I pay by card", "Where are the fitting rooms"], 1):
    K[("5.4", n, 1)] = write(a)
for n, a in enumerate(["are", "They're/They are", "them", "is", "It's/It is", "it"], 1):
    K[("5.5", n, 1)] = Q(a)
for n in range(1, 5):
    K[("5.8", n, 1)] = own()
K[("5.9", 20, 1)] = own(control="essay")
for n in range(1, 8):                             # the checklist
    K[("5.9", n, 1)] = tick()

if __name__ == "__main__":
    data = h.build(K, "Elementary", 9, "Unit 9A & 9C — Clothes and shopping")
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "e09ac.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
