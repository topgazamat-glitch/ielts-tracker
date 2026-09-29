"""E10AC Communication - Azamat's Elementary booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(E10AC Communication - answer key), joined box by box by hand. The Desktop
"new design" copy is used; it splits into its five parts as it should.

As with the other Elementary booklets, it speaks Uzbek wherever it
explains: every explanation box, the goals, the headings and "Type" column
of the grammar table, the IT table's headings, the "Why" column of the
listening table, and a line under every instruction. The English examples
stay English, as do the reading text, the dialogues, the model and the
exercises.

5.7 numbers its lines 1-4 and then asks for the order 1-4; the lines lose
their numbers, so the only numbers are the ones tapped. 4.1 is a guess, so
its ticks are not marked. 5.10 is done in pairs in class.

    python3 handouts/e10ac_digital.py            # writes handouts/e10ac.json, lists every box
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

DOCX = "~/Desktop/Handouts/A2 Elementary/E10AC Communication/E10AC Communication — handout (new design).docx"
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


def compared(subject, adjective, other):
    """"X is (much / far / a lot) ADJ-er than Y" in every usual strength."""
    return "/".join("%s is %s%s than %s" % (subject, w, adjective, other)
                    for w in ("", "much ", "far ", "a lot ", "a bit "))


# ------------------------------------------------------------ 1 Reading
boxes_for("1.3", range(1, 5), where="options")
h.options_on_lines("1.3")
boxes_for("1.4", range(1, 5), where="leader")
h.leaders("1.5", "1.6  </span>", [(1, W, "Six comparative adjectives")])

# ------------------------------------------------------------ 2 Grammar
boxes_for("2.3", range(2, 9))                     # item 1 is the worked example
h.options_on_lines("2.6")

# ------------------------------------------------------------ 3 Vocabulary
NOUNS32 = h.key_first("3.2")
STRESS34 = {1: "go online", 2: "check my emails", 3: "click on a link", 4: "visit a website",
            5: "save the document", 6: "charge my phone"}
boxes_for("3.4", STRESS34)
boxes_for("3.5", range(1, 5), where="leader")

# ------------------------------------------------------------ 4 Listening
boxes_for("4.2", (1, 2), where="leader")
a = h.html.index('<table class="bk">', h.html.index("</table>", h.html.index('<table class="bk">', section("4.3"))))
b = h.html.index("</table>", a) + len("</table>")    # 4.3's grid is its second table: the notes come first
rows = [re.findall(r"<td[^>]*>(.*?)</td>", r, re.S) for r in re.findall(r"<tr>(.*?)</tr>", h.html[a:b], re.S)]
names = [plain(c) for c in rows[0][1:]]
grid = ""
for k, row in enumerate(rows[1:], 1):
    bits = []
    for name, cell in zip(names, row[1:]):
        tag = BLANK_TAG.search(cell)
        h.blanks[int(tag.group(1))]["text"] = "%s — %s" % (plain(row[0]), name)
        bits.append('<span style="color:#6E6E6E">%s</span> %s' % (html.escape(name), tag.group(0)))
    grid += ('<p data-item="4.3:%d" style="margin-bottom:8px"><span style="font-weight:700">%s</span><br>%s</p>'
             % (k + 10, html.escape(plain(row[0])), "<br>".join(bits)))
h.html = h.html[:a] + grid + h.html[b:]
h.options_on_lines("4.8")
boxes_for("4.8", (1, 2, 3))

# ------------------------------------------------------ 5 Everyday English
boxes_for("5.1", range(1, 5), where="leader")
h.leaders("5.2", "ASKING FOR HELP", [(1, W, "Annie's problem, and does Leo solve it?")])
boxes_for("5.3", range(1, 7), where="leader")
ANSWERS54 = halves("5.4", "a-c")
STRESS55 = {1: "Could you help me?", 2: "Do you mind showing me?", 3: "Would you mind explaining it?",
            4: "Can you have a look?"}
boxes_for("5.5", STRESS55)
STEPS57 = {1: "And in the end, save the photos here.", 2: "Touch the word 'Open' here.",
           3: "And next, go to a new screen.", 4: "Choose the photo you want."}
in_order("5.7", STEPS57)
boxes_for("5.9", range(1, 5), where="leader")

# ------------------------------- every instruction, once more, in Uzbek
for label, text in [
        ("1.1", "Muhokama qiling. Uy vazifangizni nimada yozasiz — telefonda, planshetda, noutbukda yoki qogʻozda? "
                "Nega?"),
        ("1.2", "Buni kim aytadi? *D* (Dilnoza), *R* (Rustam), *F* (Farida), *B* (Bek), *M* (Maya) yoki *S* (Sam) "
                "ni tanlang."),
        ("1.3", "Eng toʻgʻri javobni tanlang: *A*, *B* yoki *C*."),
        ("1.4", "Matndan shu maʼnodagi soʻzni toping."),
        ("1.5", "Matndan oltita qiyosiy sifatni topib, yozing."),
        ("1.6", "Matndagi har bir iborani BITTA soʻz bilan toʻldiring."),
        ("2.1", "Qiyosiy shaklini yozing."),
        ("2.2", "Qiyosiy sifat + *than* bilan toʻldiring."),
        ("2.3", "Xatoni topib, toʻgʻrilang. IKKITA gap toʻgʻri — ular uchun *✓ It is correct* tugmasini bosing."),
        ("2.4", "Farqni kattaroq yoki kichikroq qilish uchun *much*, *far* yoki *a bit* qoʻshing. Butun gapni "
                "yozing."),
        ("2.5", "Matnni toʻgʻri shakl bilan toʻldiring."),
        ("2.6", "Toʻgʻri javobni tanlang: *A*, *B* yoki *C*."),
        ("2.7", "Qiyosiy gap yozing. Qavs ichidagi soʻzni ishlating."),
        ("3.1", "Iboralarni toʻldiring."),
        ("3.2", "Feʼllarni otlar bilan moslang. Baʼzan ikki javob ham toʻgʻri — bittasini tanlang."),
        ("3.3", "Gaplarni 3.2 dagi ibora bilan toʻldiring."),
        ("3.4", "Urgʻuli soʻzni tanlang, keyin iborani ovoz chiqarib ayting."),
        ("3.5", "Har bir gapdagi xatoni topib, toʻgʻri gapni yozing."),
        ("3.6", "Suhbatni qutidagi iboralar bilan toʻldiring."),
        ("4.1", "Tinglashdan oldin taxmin qiling. Suhbatda ulardan qaysilari tilga olinadi deb oʻylaysiz? "
                "Belgilang."),
        ("4.2", "Bir marta tinglang va javob bering."),
        ("4.3", "Yana tinglang. 1–4 izohlarni toʻgʻri joyga qoʻying."),
        ("4.4", "Yana bir marta tinglang va har bir qatorni eshitgan soʻzingiz bilan toʻldiring."),
        ("4.5", "Tinglang va nima boʻlishiga eʼtibor bering."),
        ("4.6", "Har bir iborani ikki marta ayting — avval sekin, keyin tez."),
        ("4.7", "Buni kim aytadi — ota (*F*) mi yoki qizi (*D*) mi?"),
        ("4.8", "Gapiruvchi nima demoqchi? *A* yoki *B* ni tanlang."),
        ("5.1", "1-qismni tinglang va javob bering."),
        ("5.2", "2-qismni tinglang. Annining muammosi nima va Leo uni hal qiladimi?"),
        ("5.3", "Toʻgʻri gaplar uchun *✓ It is correct* tugmasini bosing. Notoʻgʻrilarini toʻgʻrilang."),
        ("5.4", "Savollarni javoblar bilan moslang. Bitta javob ikkalasiga ham toʻgʻri keladi."),
        ("5.5", "Urgʻuli soʻzni tanlang. Keyin har birini pasayuvchi ohang bilan ayting."),
        ("5.6", "Bularni kim aytadi — yordam berayotgan odam (*H*) mi yoki oʻrganayotgan odam (*L*) mi?"),
        ("5.7", "Koʻrsatmalarni mantiqiy tartibda raqamlang (1–4)."),
        ("5.8", "Namunaviy suhbatni oʻqing, keyin javob bering."),
        ("5.9", "Namuna haqidagi savollarga javob bering."),
        ("5.10", "Juftlikda ishlang. A oʻquvchi yordam soʻraydi, B oʻquvchi tushuntiradi. Keyin almashing. Buni "
                 "sinfda bajarasiz.")]:
    h.say_also(label, text)

# ------------------------------------------ the explanations, told in Uzbek
h.goals([
    "ikkita oʻxshash qurilmani solishtiradigan matnni oʻqib tushunishni",
    "qiyosiy sifatlarni toʻgʻri ishlatishni va toʻgʻri yozishni",
    "IT iboralarini ishlatishni — *download a file, click on a link*",
    "telefonlarni uy telefoni bilan solishtirayotgan oddiy suhbatni tushunishni",
    "texnika boʻyicha yordam soʻrashni va berilgan koʻrsatmalarni tekshirishni",
])
h.retell("KEY WORDS", "KALIT SOʻZLAR", [
    "**a keyboard**  klaviatura — harflar joylashgan qism",
    "**a screen**  ekran — qaraydigan qismingiz",
    "**a case**  gʻilof — biror narsani himoya qiladigan qoplama",
    "**second-hand**  yangi emas; oldin ishlatilgan",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — QIYOSIY SIFATLAR", [
    "Ikki narsa bir-biridan qanday farq qilishini aytish uchun qiyosiy sifatni ishlatamiz. Ikkinchi qismi — "
    "*than*.",
    "[[A]] Qisqa sifatlar — *-er* qoʻshiladi. *small → smaller · cheap → cheaper · hard → harder · Earbuds are "
    "smaller than headphones.*",
    "[[B]] *-e* bilan yoki bitta unli + bitta undosh bilan tugasa. *nice → nicer · big → bigger · thin → "
    "thinner · hot → hotter*",
    "[[C]] *-y* bilan tugasa. *easy → easier · heavy → heavier · noisy → noisier · happy → happier*",
    "[[D]] Uzun sifatlar (2+ boʻgʻin) — *more* ishlatiladi. *expensive → more expensive · comfortable → more "
    "comfortable · interesting → more interesting*",
    "[[E]] Qoidasizlari — yodlab oling. *good → better · bad → worse · far → further*",
    "**Farqni kattalashtirish yoki kichraytirish:** *much / far / a lot* + qiyosiy — *much better, far more "
    "expensive*. *a bit / a little* — *a bit heavier*.",
])
h.retell("ERROR WARNING", "DIQQAT — KOʻP UCHRAYDIGAN XATOLAR", [
    "Bu darajadagi deyarli har bir xato shu toʻrttasidan biri:",
    "1 **Imlo — ikkilangan harf.** ✗ *biger* → ✓ *bigger* · ✗ *cheapper* → ✓ *cheaper*. Harf faqat bitta unli + "
    "bitta undoshdan keyin ikkilanadi: *big, thin, hot, wet*. *cheap* da ikkita unli bor, shuning uchun "
    "ikkilanmaydi.",
    "2 **Qisqa sifat bilan more.** ✗ *more hard* → ✓ *harder* · ✗ *more light* → ✓ *lighter*",
    "3 **more va -er birga.** ✗ *more heavier* → ✓ *heavier* · ✗ *more smaller* → ✓ *smaller*",
    "4 **very oʻrnida more.** ✗ *I haven't got headphones because they are more expensive.* → ✓ *… because they "
    "are very expensive.* *more* ni faqat ikki narsani solishtirganda ishlating.",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — IT IBORALARI", [
    "Bu feʼl va otlar birga keladi. Yakka soʻzni emas, butun iborani oʻrganing.",
    "[[A]] *go online · check my emails · make calls* — *I go online every morning and check my emails.*",
    "[[B]] *download a file / a document · save a file / a document* — *Download the file, then save it.*",
    "[[C]] *click on a link · visit a website* — *Don't click on links from people you don't know.*",
    "[[D]] *log into a computer / a website · charge a phone / a computer* — *I logged into the website but I forgot "
    "my password.*",
    "**Ikki feʼl, bitta ot:** *download* ham, *save* ham *a file* va *a document* bilan keladi. *Log into* ham, "
    "*charge* ham *a computer* bilan keladi.",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [
    "*A landline* — uydagi simli eski telefon. Ota va qizining uy telefonini qoldirish-qoldirmaslik haqidagi "
    "suhbatini eshitasiz.",
    "Agar sinfingizda audio boʻlsa, bu 10.03-trek. Boʻlmasa, oʻqituvchingiz matnni oʻqib beradi — topshiriqlar "
    "bir xil.",
])
h.retell("WHY YOU DIDN'T HEAR IT", "NEGA ESHITMADINGIZ?", [
    "**than hech qachon urgʻu olmaydi.** *safer than a mobile* da u /ðən/ ga qisqaradi — oldingi soʻzdan ham "
    "tezroq aytiladigan bitta kuchsiz tovush. Oʻquvchilar kuchli *than* ni kutadi, uni eshitmaydi va "
    "solishtirishni butunlay oʻtkazib yuboradi.",
    "U oldingi soʻzga ham qoʻshiladi: *cheaper than* → /tʃiːpəðən/ · *better than* → /betəðən/ · *safer than* → "
    "/seɪfəðən/.",
])
h.retell("LISTENING INTO SPEAKING", "TINGLASHDAN GAPIRISHGA", [
    "Avval Anni va Leoni tinglang. Anni planshetida bir narsani qila olmayapti. Agar sinfingizda audio boʻlsa, "
    "bu 10.10 va 10.13-treklar.",
])
h.retell("ASKING FOR HELP", "YORDAM SOʻRASH", [
    "*Could you help me? · Can you help me? · Would you mind showing me? · Do you mind showing me?*",
    "**mind dan keyin -ing ishlatish shart:** *Would you mind showing me? · Do you mind explaining it?* Hech "
    "qachon *Would you mind show me*.",
    "**Javob berish.** *Could you…?* ga → *Yes, of course. / No problem.* *Do you mind…?* ga → *No, not at all. "
    "/ No problem.*",
    "**mind bilan ehtiyot boʻling.** *Do you mind…?* — „siz uchun muammomi?“ degani. Shuning uchun *No* — „ha, "
    "yordam beraman“ degani. Doʻstona iltimosga *Yes* desangiz, rad etgandek eshitiladi.",
])
h.retell("MAIN STRESS AND INTONATION", "ASOSIY URGʻU VA OHANG", [
    "Yordam soʻralgan savolda urgʻu asosiy feʼlga tushadi va ovoz oxirida pasayadi:",
    "*Could you HELP me?* ↘ · *Do you mind SHOWing me?* ↘ · *Would you mind EXplaining it?* ↘",
    "Oxirida koʻtariluvchi ovoz hayron yoki sabrsizdek eshitiladi. Pasayuvchi ovoz — doʻstona.",
])
h.retell("CHECKING INSTRUCTIONS", "KOʻRSATMALARNI TEKSHIRISH", [
    "Kimdir biror narsani tushuntirayotganda, uni unga qaytarib ayting. Uch usul:",
    "*So first I touch this button?* — qadamni savol qilib takrorlang.",
    "*Like this?* — uni bajarayotganingizda.",
    "*Is that right?* — bajarib boʻlganingizdan keyin.",
])
h.retell("CHECK YOUR CONVERSATION", "SUHBATINGIZNI TEKSHIRING", [
    "{box}  *Could you…?* yoki *Would/Do you mind …ing?* bilan yordam soʻradim.   {box}  Sherigim toʻgʻri javob "
    "berdi (*mind* bilan ehtiyot boʻling).",
    "{box}  Koʻrsatmalarni uch marta tekshirdim — *So first…? · Like this? · Is that right?*   {box}  *First / "
    "Then / After that* ni ishlatdim.",
    "{box}  Asosiy feʼlga urgʻu berdim va har bir savol oxirida ovozim pasaydi.",
])
h.one_per_line("SUHBATINGIZNI TEKSHIRING", None, at="box")
h.retell_cells({"Verb": "Feʼl", "Goes with": "Nima bilan keladi", "Example": "Misol"},
               after="TUSHUNTIRISH — IT IBORALARI")
h.retell_cells({"Adjective": "Sifat", "Type": "Turi", "Comparative": "Qiyosiy daraja", "Example": "Misol",
                "short": "qisqa", "vowel + consonant": "unli + undosh", "ends in -y": "<i>-y</i> bilan tugaydi",
                "long": "uzun", "irregular": "qoidasiz"},
               after="TUSHUNTIRISH — QIYOSIY SIFATLAR")
h.retell_cells({"What is written": "Yozilishi", "What you hear": "Eshitilishi", "Why": "Nega",
                "than joins to cheaper": "<i>than</i> <i>cheaper</i> ga qoʻshiladi",
                "only much and safe are strong": "faqat <i>much</i> va <i>safe</i> kuchli",
                "three words, two beats": "uch soʻz, ikki zarb",
                "need it joins into one word": "<i>need it</i> bitta soʻzga qoʻshiladi"},
               after="4.5  </span>")

# ------------------------------------------------------------------ the key
K = {}
WHO = {"D": "D · Dilnoza", "R": "R · Rustam", "F": "F · Farida", "B": "B · Bek", "M": "M · Maya", "S": "S · Sam"}
for n, a in enumerate("DFBMRS", 1):
    K[("1.2", n, 1)] = choose(["D", "R", "F", "B", "M", "S"], a, labels=WHO)
for n, a in enumerate("BBBC", 1):
    K[("1.3", n, 1)] = choose(["A", "B", "C"], a)
for n, a in enumerate(["a keyboard/keyboard", "a screen/screen", "a case/case", "second-hand/second hand"], 1):
    K[("1.4", n, 1)] = Q(a)
K[("1.5", 1, 1)] = own()
for n, a in enumerate(["lighter", "lasts", "much", "still", "fuller", "less", "more"], 1):
    K[("1.6", n, 1)] = Q(a)
for n, a in enumerate(["cheaper", "bigger", "easier", "more comfortable", "better", "worse", "thinner",
                       "more modern", "noisier", "further/farther", "hotter", "more interesting"], 1):
    K[("2.1", n, 1)] = Q(a)
for n, a in enumerate(["lighter than", "older than", "faster than", "cheaper than", "more important than",
                       "worse than", "smaller than", "more comfortable than"], 1):
    K[("2.2", n, 1)] = Q(a)
TICKED = "✓/correct/tick"
for n, a in zip(range(2, 9), [
        either("This screen is bigger", "bigger"),
        either("Her computer is faster than mine", "than"),
        either("The new model is better", "better"),
        either("This bag is heavier than my old one", "heavier"),
        TICKED,
        either("I don't buy headphones because they're very expensive",
               "I don't buy headphones because they are very expensive", "very expensive", "very"),
        TICKED]):
    K[("2.3", n, 1)] = fix(a)
K[("2.4", 1, 1)] = write("/".join("A laptop is %s faster than a tablet" % w for w in ("much", "far", "a lot")))
K[("2.4", 2, 1)] = write("/".join("My phone is %s heavier than yours" % w for w in ("a bit", "a little")))
K[("2.4", 3, 1)] = write("/".join("This one is %s more expensive" % w for w in ("much", "far", "a lot")))
for n, a in enumerate(["slower", "quieter", "faster", "faster", "bigger", "brighter", "noisier", "worse", "better",
                       "more comfortable"], 1):
    K[("2.5", n, 1)] = Q(a)
for n, a in enumerate("BBCA", 1):
    K[("2.6", n, 1)] = choose(["A", "B", "C"], a)
K[("2.7", 1, 1)] = write(compared("Headphones", "more expensive", "earbuds"))
K[("2.7", 2, 1)] = write(compared("The laptop", "heavier", "the tablet"))
K[("2.7", 3, 1)] = write(compared("Your battery", "better", "mine") + "/" + compared("Yours", "better", "mine"))
K[("2.7", 4, 1)] = write(compared("The metro", "faster", "the bus"))
for n, a in ((2, "heck/check"), (3, "ake/make"), (4, "onnect to/connect to/onnect/connect")):
    K[("3.1", n, 1)] = Q(a)
for n, a in enumerate(["b/c", "e", "a", "a/f", "b/c", "d/f"], 1):
    K[("3.2", n, 1)] = choose(NOUNS32, a)
for n, a in enumerate(["charge my phone/charge it/charge my battery",
                       "click on links/click on a link/click on the links/click on the link",
                       "Save the document/Save the file/Save your document/Save your file/Save it",
                       "go online/visit a website/visit the website/check the news",
                       "log into the website/log into it/log in/log into the site",
                       "download it/download/download the film"], 1):
    K[("3.3", n, 1)] = Q(a)
STRESSED = {1: "online", 2: "emails", 3: "link", 4: "website", 5: "document", 6: "phone"}
for n, phrase in STRESS34.items():
    K[("3.4", n, 1)] = choose(phrase.split(), STRESSED[n])
for n, a in enumerate([
        either("I clicked on the link and nothing happened", "clicked on the link"),
        either("Can you download the file for me", "Could you download the file for me"),
        either("I need to charge my phone", "charge my phone"),
        either("He logged into the website with my password", "He logged in to the website with my password",
               "He logged into the website", "logged into")], 1):
    K[("3.5", n, 1)] = write(a)
BOX36 = ["charge it", "click on it", "downloading", "go online", "log into", "save it", "visit"]
for n, a in enumerate(["go online", "log into", "visit", "click on it", "downloading", "save it", "charge it"], 1):
    K[("3.6", n, 1)] = choose(BOX36, a)
for n in range(1, 7):                             # a guess before listening
    K[("4.1", n, 1)] = tick()
K[("4.2", 1, 1)] = write("He wants to give up the landline/give up the landline/the landline/"
                         "He wants to stop using the landline/He wants to get rid of the landline/"
                         "get rid of the landline/give up the phone")
K[("4.2", 2, 1)] = choose(["Yes", "No"], "No")
NOTES = ["1", "2", "3", "4"]
for n, a in enumerate("3142", 1):                 # landline good, bad; smartphone good, bad
    K[("4.3", 4, n)] = choose(NOTES, a)
for n, a in enumerate(["safer", "need", "text", "work", "keep"], 1):
    K[("4.4", n, 1)] = Q(a)
FD = {"F": "F · the father", "D": "D · the daughter"}
for n, a in enumerate("FDFD", 1):
    K[("4.7", n, 1)] = choose(["F", "D"], a, labels=FD)
for n in (1, 2, 3):
    K[("4.8", n, 1)] = choose(["A", "B"], "B")
K[("5.1", 1, 1)] = Q("Dan")
K[("5.1", 2, 1)] = own()
K[("5.1", 3, 1)] = Q("Leo")
K[("5.1", 4, 1)] = own()
K[("5.2", 1, 1)] = own()
for n, a in enumerate([TICKED, either("Would you mind telling me", "telling"), TICKED,
                       either("Could you show me", "show"), TICKED, "Can you help me"], 1):
    K[("5.3", n, 1)] = fix(a)
for n, a in enumerate(["a/b", "a/c"], 1):
    K[("5.4", n, 1)] = choose(ANSWERS54, a)
STRESSED55 = {1: "help", 2: "showing", 3: "explaining", 4: "look"}
for n, question in STRESS55.items():
    K[("5.5", n, 1)] = choose(question.rstrip("?").split(), STRESSED55[n])
HL = {"H": "H · helping", "L": "L · learning"}
for n, a in enumerate("LHLHLH", 1):
    K[("5.6", n, 1)] = choose(["H", "L"], a, labels=HL)
# in order: Touch the word 'Open', And next, Choose the photo, And in the end
for n, a in {1: "4", 2: "1", 3: "2", 4: "3"}.items():
    K[("5.7", n, 1)] = choose(["1", "2", "3", "4"], a)
for n in range(1, 5):
    K[("5.9", n, 1)] = own()
for n in range(1, 6):                             # the checklist, after the pair work
    K[("5.10", n, 1)] = tick()

if __name__ == "__main__":
    data = h.build(K, "Elementary", 10, "Unit 10A & 10C — Communication")
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "e10ac.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
