"""P03BD Money - Azamat's Pre-Intermediate booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(P03BD Money - answer key), joined box by box by hand. Every explanation is
told again in Uzbek, with the English examples kept, and every instruction
has a line in Uzbek under it; the reading, the texts to fill in and the
exercises stay English.

Two lines in 4.3 are a word short of what Daniel says, so the boxes take
what he says: "I haven't given the sofa away yet" wants away yet in the
second box (yet alone is right too), and "I've just started cooking" wants
've just started where the line prints (just) start.

What a phone gets that paper does not:
  - taps for every choice: who says it, A/B/C, already/yet/just, the two
    loudest words, make/do/give for each noun, /dʒ/ or /j/, the word in each
    line of 4.1, yes or no, which job each paragraph does, their order;
  - boxes where paper has none: 2.2, 2.5, 2.6, 3.5, 4.1, 5.3.
The 4.7 and 5.2 pair work keeps its boxes; the partner's are for class.

    python3 handouts/p03bd_digital.py            # writes handouts/p03bd.json, lists every box
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import (Handout, Q, choose, tick, own, write, fix, pair, report,   # noqa: E402
                     BLANK_TAG, ITEM_P, plain, ITEM_STYLE, NUM_SPAN, TEXT_SPAN)

DOCX = "~/Desktop/Handouts/B1 Pre-Intermediate/P03BD Money/P03BD Money — handout (new design).docx"
W = "95%"

h = Handout(DOCX)
TAGS = {int(m.group(1)): m.group(0) for m in BLANK_TAG.finditer(h.html)}


def section(label):
    return h.html.index("%s  </span>" % label)


def either(*forms):
    return "/".join(forms)


def have(*rest):
    return either(*[p + r for r in rest for p in ("'ve ", "have ")])


def item_p(label, n, text_html, token):
    h.texts[(label, n)] = plain(text_html)
    return ('<p data-item="%s:%d" %s>%s%s</p>'
            % (label, n, ITEM_STYLE, NUM_SPAN % n, TEXT_SPAN % ("%s  %s" % (text_html, token))))


def replace_table_after(label, new):
    at = section(label)
    a = h.html.index('<table class="bk">', at)
    b = h.html.index("</table>", a) + len("</table>")
    h.html = h.html[:a] + new + h.html[b:]


def retell_table(after, cells):
    """Cells told again in the first table after `after` - every one that
    says the same thing, since a word like "middle" is in two rows."""
    a = h.html.index('<table class="bk">', h.html.index(after))
    b = h.html.index("</table>", h.html.index("</table>", a) + 1) + len("</table>")
    seen = set()

    def swap(m):
        text = plain(m.group(2))
        if text in cells:
            seen.add(text)
            return '%s<p><span>%s</span></p></td>' % (m.group(1), cells[text])
        return m.group(0)
    h.html = h.html[:a] + re.sub(r"(<td[^>]*>)((?:(?!<td|<table).)*?)</td>", swap, h.html[a:b],
                                 flags=re.S) + h.html[b:]
    if seen != set(cells):
        raise SystemExit("cells not found: %s" % sorted(set(cells) - seen))


def words_of(label, n):
    m = next(m for m in h._items(label) if int(m.group(3)) == n)
    return [w.strip("?!.,") for w in re.sub(r"^\d+\s+", "", plain(m.group(4))).split() if w.strip("?!.,")]


def add_to_item(label, n, extra):
    m = next(m for m in h._items(label) if int(m.group(3)) == n)
    h.texts.setdefault((label, n), plain(m.group(4)))
    h.html = h.html[:m.start()] + m.group(1) + m.group(4) + extra + "</p>" + h.html[m.end():]


# ------------------------------------------------------------ 1 Reading
h.options_on_lines("1.3")
for n in range(1, 5):
    h.item_box("1.3", n, where="options")
for n in range(1, 4):
    h.item_box("1.4", n, width="190px", where="leader")
h.leaders("1.5", "1.6  </span>", [(1, W, "Three sentences with already"), (2, W, "Three sentences with yet")])
for n in range(1, 4):
    h.item_box("1.6", n, where="leader")

# ------------------------------------------------------------ 2 Grammar
WORD22 = {1: "yet", 2: "already", 3: "yet", 4: "already", 5: "yet", 6: "just"}
for n, w in WORD22.items():
    h.item_box("2.2", n, placeholder="The sentence with %s" % w)
for n in range(2, 9):                             # item 1 is the worked example
    h.item_box("2.5", n)
LOUD = {}
for n in range(1, 5):
    LOUD[n] = words_of("2.6", n)
    add_to_item("2.6", n, '<br><span style="color:#6E6E6E">1st loud word</span> {{box:2.6:%d:60px:}}'
                          '<br><span style="color:#6E6E6E">2nd loud word</span> {{box:2.6:%d:60px:}}' % (n, n))

# ------------------------------------------------------------ 3 Vocabulary
NOUNS = h.sort_words("3.1", ["a donation", "voluntary work", "directions", "a payment", "a job", "advice",
                             "a note", "the shopping", "an example"], "MAKE")
for n in range(1, 5):
    h.item_box("3.5", n, where="leader")

# ------------------------------------------------------------ 4 Listening
CHOICE41 = {1: ["bored", "annoyed", "confused"], 2: ["IT equipment", "furniture", "clothes"],
            3: ["free time activities", "food", "transport"]}
for n in CHOICE41:
    h.item_box("4.1", n)
h.grid_rows("4.2")
h.options_on_lines("4.6")
for n in (1, 2, 3):
    h.item_box("4.6", n)
h.grid_rows("4.7")

# ------------------------------------------------------------ 5 Writing
h.grid_rows("5.1")
h.after_instruction("5.3", [(n, l, "60px", "") for n, l in enumerate("abcd", 1)])
replace_table_after("5.4", "".join(item_p("5.4", n, "Paragraph %d" % n, "{{box:5.4:%d:60px:}}" % n)
                                   for n in range(1, 5)))
h.options_on_lines("5.5")
for n in range(1, 5):
    h.item_box("5.5", n)
h.leaders("5.7", "CHECK BEFORE", [(20, W, "Write your email here")])
h.html = h.html.replace(TAGS[100], "", 1)         # the word count: the box counts them itself

# ------------------------------- every instruction, once more, in Uzbek
for label, text, *after in [
        ("1.1", "Muhokama qiling. Uyingizdagi qancha narsadan bir yildan beri foydalanmagansiz? Ulardan "
                "birortasini berib yubora olasizmi?"),
        ("1.2", "Buni kim aytadi? *M* (Malika), *T* (Timur) yoki *D* (Dilnoza) ni tanlang."),
        ("1.3", "Eng toʻgʻri javobni tanlang: *A*, *B* yoki *C*."),
        ("1.4", "Matndan shu maʼnodagi soʻz yoki iborani toping."),
        ("1.5", "*already* bilan uchta va *yet* bilan uchta gap toping. Har bir soʻz qayerda turibdi?"),
        ("1.6", "Savollarga javob bering."),
        ("2.1", "Feʼlning uchinchi shakli (past participle) bilan toʻldiring."),
        ("2.2", "Qavsdagi soʻzni toʻgʻri joyga qoʻyib, oʻsha gapni yozing."),
        ("2.3", "*Already*, *yet* yoki *just*?"),
        ("2.4", "Suhbatni toʻldiring."),
        ("2.5", "Xatoni topib, toʻgʻrilang. TOʻRTTA gap toʻgʻri — ular uchun *✓ It is correct* tugmasini bosing."),
        ("2.6", "Tinglang va har bir gapdagi eng baland ikki soʻzni tanlang — gapdagi tartibi bilan."),
        ("3.1", "Har bir otni toʻgʻri ustunga joylang: *MAKE*, *DO* yoki *GIVE*."),
        ("3.2", "*make*, *do* yoki *give* ning toʻgʻri shakli bilan toʻldiring."),
        ("3.3", "Har bir iborani BITTA soʻz bilan toʻldiring."),
        ("3.4", "*/dʒ/* mi yoki */j/* mi? Tanlang."),
        ("3.5", "Har bir gapdagi xatoni topib, toʻgʻri gapni yozing."),
        ("3.6", "Sherigingizdan soʻrang. Toʻliq gap bilan javob bering."),
        ("4.1", "Bir marta tinglang. Har bir qatorda toʻgʻri soʻzni tanlang."),
        ("4.2", "Yana tinglang va uchta nuqta boʻyicha qisqacha yozib oling."),
        ("4.3", "Yana bir marta tinglang va har bir qatorni toʻldiring."),
        ("4.4", "Tinglang va nima boʻlishiga eʼtibor bering."),
        ("4.5", "Har bir iborani ikki marta ayting — avval sekin, keyin tez."),
        ("4.6", "Gapiruvchi nima demoqchi? *A* yoki *B* ni tanlang."),
        ("4.7", "Endi siz. Jadvalni oʻzingiz uchun toʻldiring, keyin sherigingizdan soʻrang."),
        ("5.1", "Tinglang va jadvalni toʻldiring."),
        ("5.2", "Kimning sababi sizning sababingizga eng yaqin? Sherigingizga nega ekanini ayting."),
        ("5.3", "Namunani oʻqing. Qaysi xatboshi qaysi vazifani bajaradi? Har bir xatboshi uchun 1–4 ni tanlang."),
        ("5.4", "Endi ularni tartib bilan joylang."),
        ("5.5", "Qaysi gap xatboshini yaxshiroq boshlaydi? *A* yoki *B* ni tanlang."),
        ("5.6", "Avval reja tuzing. Ikki daqiqa, keyin yozing."),
        ("5.7", "Endi yangilik emailingizni yozing (120–150 soʻz). Pul yigʻgan haqiqiy vaqtingiz haqida yozing "
                "yoki siz va doʻstlaringiz ishda yoki maktabda xayriya uchun 1 000 000 soʻm yigʻdingiz deb "
                "tasavvur qiling.", "at work or school.")]:
    h.say_also(label, text, after=after[0] if after else None)

# ------------------------------------------ the explanations, told in Uzbek
h.goals([
    "*already, just* va *yet* ni toʻgʻri joyga qoʻyishni — oʻrtada, oʻrtada va oxirida",
    "kamroq narsa bilan yashash va nima qilgan-qilmaganingiz haqida gapirishni",
    "*make, do* va *give* ni toʻgʻri otlar bilan ishlatishni",
    "/dʒ/ va /j/ tovushlarini farqlab eshitishni",
    "har biri bitta vazifali toʻrt xatboshidan iborat yangilik emailini yozishni",
])
h.retell("KEY WORDS", "KALIT SOʻZLAR", [
    "**to give away**  tekinga berib yubormoq",
    "**a charity**  yordam beradigan tashkilot (xayriya tashkiloti)",
    "**generous**  saxiy, berishni yaxshi koʻradigan",
    "**to declutter**  keraksiz narsalardan xalos boʻlmoq",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — ALREADY, YET VA JUST", [
    "3A da savol „qaysi zamon?“ edi. Bu yerda zamon aniq — bu present perfect — savol esa kichik soʻz qayerga "
    "qoʻyilishi va u nima qilishida.",
    "[[ALREADY]] **Qilingan, va kutilganidan ertaroq.** *I've already given away four bags of clothes. · He's "
    "already asked me twice.* *have* bilan uchinchi shakl orasiga qoʻyiladi.",
    "[[YET]] **Qilinmagan — lekin kutilyapti.** *I haven't touched the books yet. · Have you sold your car "
    "yet?* Gap oxiriga qoʻyiladi va faqat inkor gaplarda va savollarda keladi.",
    "[[JUST]] **Juda oz vaqt oldin qilingan.** *I've just given away my second guitar.* Oʻrni *already* bilan "
    "bir xil — feʼlning ikki qismi orasida.",
    "[[→]] **Uchalasi birga.** *I've just finished the kitchen. I've already done the bedroom. I haven't started "
    "the books yet.* Uchta gap, uchta bosqich, uchta oʻrin.",
    "**Nega aynan shu zamonga tegishli?** Uchalasi ham *hozir* haqida nimadir aytadi: hozir qilingan, hozir "
    "qilinmagan, bir lahza oldin rost boʻldi. Present perfect aynan shu uchun — shuning uchun ular past simple "
    "bilan deyarli uchramaydi.",
])
h.retell("ERROR WARNING", "DIQQAT — ALREADY, YET VA JUST DAGI XATOLAR", [
    "1 **YET tasdiq gap uchun emas.** ✗ *I have finished yet.* → ✓ *I have already finished.* yoki ✓ *I haven't "
    "finished yet.* Gap tasdiq boʻlsa, sizga *already* kerak.",
    "2 **ALREADY oxiriga qoʻyilmaydi.** ✗ *I have given it away already* — mumkin, lekin hayratlangandek "
    "eshitiladi. Oddiy oʻrni — oʻrtada: *I've already given it away.*",
    "3 **YET ni oʻrtaga qoʻymang.** ✗ *I haven't yet done it* — rasmiy va kam uchraydi. Bu darajada: *I haven't "
    "done it yet.*",
    "4 **JUST bu yerda present perfect talab qiladi.** ✗ *I just gave it away* — amerikacha va norasmiy. "
    "Imtihonlar tekshiradigan ingliz tilida: *I've just given it away.*",
    "5 **3A dagi tuzoq hali ham ochiq:** ✗ *I've already given it away yesterday.* → ✓ *I gave it away "
    "yesterday.* Tugagan vaqt baribir hammasidan ustun.",
])
h.retell("PRONUNCIATION", "TALAFFUZ", [
    "Kichik soʻzlar urgʻusiz, shuning uchun ularni eshitmay qolasiz. *I've already done it* → baland soʻzlar "
    "*already* va *done*; *I've* esa /aɪv/, deyarli hech narsa.",
    "**Lekin oxiridagi YET baland.** *I haven't done it yet.* U gapning oxirgi soʻzi, shuning uchun ovozning "
    "pasayishini oʻzida olib yuradi — bu foydali, chunki aynan u gap inkor ekanini bildiradi.",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — MAKE, DO VA GIVE", [
    "Uchta juda keng tarqalgan feʼl, va qaysi biri kerakligini ot hal qiladi. Buni qoida bilan topib "
    "boʻlmaydi — bular birikmalar (collocations), ularni juftlik qilib oʻrganasiz.",
    "[[MAKE]] *a note · a donation · a payment · a mistake · friends · a decision · a change · money · a "
    "difference*",
    "[[DO]] *a task · voluntary work · the shopping · a job · homework · the washing-up · business · your best*",
    "[[GIVE]] *money away · directions · advice · an example · a lift · a hand · a reason · a talk*",
    "**Taxminiy gʻoya, agar kerak boʻlsa.** *Make* — ilgari yoʻq narsani yaratadi. *Do* — biror faoliyatni "
    "bajaradi. *Give* — biror narsani boshqa odamga oʻtkazadi. Bu koʻpincha taxmin qilishga yordam beradi — "
    "lekin koʻpincha ishlamaydi ham, shuning uchun juftliklarni baribir yodlash kerak.",
])
h.retell("PRONUNCIATION — THE LETTERS J AND Y", "TALAFFUZ — J VA Y HARFLARI", [
    "Qogʻozda bir-biriga oʻxshash, ogʻizda esa umuman boshqa-boshqa ikki tovush.",
    "[[/dʒ/]] D bilan boshlanadi: *just · enjoy · join · job · large · age*",
    "[[/j/]] umuman D yoʻq, til sirpanadi: *yet · you · young · year · yes*",
    "**Sinov juftligi:** *just* /dʒʌst/ va *yet* /jet/. Qoʻlingizni tomogʻingizga qoʻyib, ikkalasini ayting. "
    "/dʒ/ da til tanglayga tegib, qoʻyib yuboradi; /j/ da hech narsaga tegmaydi.",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [
    "*Ways of Life* degan radio dasturi. Tinglovchi Daniel qoʻngʻiroq qilib, kamroq narsa bilan yashash "
    "tajribasi haqida gapiradi — nimalarni berib yuborgani va keyin nima oʻzgargani haqida.",
    "Agar sinfingizda audio boʻlsa, bu 3.11-trek. Boʻlmasa, oʻqituvchingiz matnni oʻqib beradi — topshiriqlar "
    "bir xil.",
])
h.retell("WHY YOU DIDN'T HEAR IT", "NEGA ESHITMADINGIZ?", [
    "**ALREADY va JUST feʼlning oʻrtasiga siqib qoʻyiladi.** *I've already given* → /aɪv ɔːlredi gɪvn/. Uchta "
    "soʻz, va birinchisi bitta /v/ tovushi.",
    "**YET oxirida, shuning uchun u saqlanib qoladi.** *I haven't done it yet.* Gap oxirida aniq *yet* ni "
    "eshitsangiz, gap inkor yoki savol boʻlgan — oʻrtasini eshitmagan boʻlsangiz ham, u haqida nimadir "
    "bilasiz.",
])
h.retell("LISTENING INTO WRITING", "TINGLASHDAN YOZISHGA", [
    "Avval toʻrt kishi xayriyaga pul berish-bermasligi va qanday berishi haqida gapiradi. Ulardan ikkitasi "
    "beradi; ikkitasining esa bermaslikka sababi bor.",
])
h.retell("WHAT AN UPDATE EMAIL IS FOR", "YANGILIK EMAILI NIMA UCHUN KERAK", [
    "Siz pul yigʻdingiz. Endi yordam bergan odamlarga yozasiz. Email toʻrtta vazifani bajaradi va har bir "
    "vazifa — bitta xatboshi.",
    "1 **Kirish.** Rahmat ayting va qancha yigʻganingizni ayting. Ikkalasini ham birinchi ikki gapda.",
    "2 **Qanday yigʻdingiz.** Tadbirlar, pishiriqlar, bozor. Odamlar bu qismni yaxshi koʻradi, chunki ular "
    "oʻsha yerda boʻlgan.",
    "3 **Xayriya tashkiloti pulni nimaga ishlatadi.** Tashkilot tarixi emas — aynan shu pul nima qilishi. "
    "Bitta aniq misol uchta umumiy gapdan yaxshiroq.",
    "4 **Yakun.** Yana bir bor rahmat ayting va keyin nima boʻlishini ayting.",
    "**Ehtiyot boʻling:** yangilik emaili yana pul soʻramaydi va uzr soʻramaydi. Agar shulardan birini "
    "qilayotgan boʻlsangiz, siz boshqa email yozgansiz.",
])
h.retell("PARAGRAPHING — THE RULE UNDER THE RULE", "XATBOSHILARGA BOʻLISH — QOIDA OSTIDAGI QOIDA", [
    "**Bitta xatboshi — bitta vazifa.** Xatboshi nima uchunligini toʻrt soʻzda ayta olmasangiz, u ikkita "
    "vazifani bajaryapti va ikkita xatboshi boʻlishi kerak.",
    "**Har birini uni eʼlon qiladigan gap bilan boshlang.** *This email is to say thank you… · Many of you "
    "bought tickets… · The charity will use the money…* Oʻquvchi xatboshini oʻqishdan oldin qayerda ekanini "
    "biladi.",
    "**Raqam va minnatdorchilikni tepada birga saqlang.** Odamlar emailning birinchi ikki qatorini oʻqiydi, "
    "qolganiga koʻz yugurtirib chiqadi. Agar £750 uchinchi xatboshida boʻlsa, oʻquvchilaringizning yarmi uni "
    "hech qachon koʻrmaydi.",
])
h.retell("CHECK BEFORE YOU SEND IT", "YUBORISHDAN OLDIN TEKSHIRING", [
    "{box}  Toʻrtta xatboshi, har biri bitta vazifa.   {box}  Pul miqdori va rahmat ikkalasi ham birinchi "
    "xatboshida.",
    "{box}  3-xatboshida pul nima qilishi haqida bitta aniq misol bor.   {box}  Pul soʻramadim va uzr "
    "soʻramadim.",
    "{box}  Kamida bitta *already, just* yoki *yet*.   {box}  Soʻzlar soni: 120–150.",
])
h.one_per_line("YUBORISHDAN OLDIN TEKSHIRING", None, at="box")
retell_table("TUSHUNTIRISH — ALREADY, YET VA JUST",
             {"Word": "Soʻz", "Where": "Qayerda", "Example": "Misol", "middle": "oʻrtada", "end": "oxirida",
              "yet (negative)": "yet (inkor gapda)", "yet (question)": "yet (savolda)"})
h.retell_cells({"What is written": "Yozilishi", "What you hear": "Eshitilishi", "Why": "Nega",
                "I have is one /v/": "<i>I have</i> bitta /v/ boʻlib qoladi",
                "yet is the last, loud word": "<i>yet</i> — oxirgi, baland soʻz",
                "just is stressed here": "bu yerda <i>just</i> urgʻuli",
                "have you almost vanishes": "<i>have you</i> deyarli yoʻqoladi"},
               after="4.4  </span>")

# ------------------------------------------------------------------ the key
K = {}
MTD = {"M": "M · Malika", "T": "T · Timur", "D": "D · Dilnoza"}
for n, a in enumerate("TDMDMT", 1):
    K[("1.2", n, 1)] = choose(["M", "T", "D"], a, labels=MTD)
for n in range(1, 5):
    K[("1.3", n, 1)] = choose(["A", "B", "C"], "B")
for n, a in enumerate(["to miss/miss/missed", "to replace/replace", "to fit/fit/fits"], 1):
    K[("1.4", n, 1)] = Q(a)
K[("1.5", 1, 1)] = own()
K[("1.5", 2, 1)] = own()
for n in range(1, 4):
    K[("1.6", n, 1)] = own()
for n, a in enumerate(["given", "sold", "found", "left", "raised", "told"], 1):
    K[("2.1", n, 1)] = Q(a)
for n, a in enumerate([
        "Have you had a chance to read it yet",
        either("I've already given them away", "I have already given them away"),
        either("I haven't stopped using my car yet", "I have not stopped using my car yet"),
        either(*[p + s for p in ("", "I sold my car last week and ")
                 for s in ("I've already bought a bike", "I have already bought a bike")]),
        "Have you decided which books to give away yet",
        either(*[p + s for p in ("", "Don't call her — ", "Don't call her - ", "Don't call her, ",
                                 "Don't call her ")
                 for s in ("she's just left the office", "she has just left the office")])], 1):
    K[("2.2", n, 1)] = write(a)
for key, a in (((1, 1), "just"), ((2, 1), "yet"), ((2, 2), "yet"), ((3, 1), "already"), ((4, 1), "already"),
               ((5, 1), "yet"), ((6, 1), "just/already")):
    K[("2.3",) + key] = choose(["already", "yet", "just"], a)
for n, a in enumerate(["Have you finished", "yet", have("just finished"), "already did", "already done",
                       either("haven't touched", "have not touched"), "yet", "Have you given", "yet",
                       have("already taken")], 1):
    K[("2.4", n, 1)] = Q(a)
TICKED = "✓/correct/tick"
for n, a in zip(range(2, 9), [
        either("I haven't given it away yet", "I have not given it away yet"),
        "I gave it away yesterday",
        TICKED, TICKED, TICKED,
        # with five minutes ago it is the past simple; with just, the time goes
        either("I've just given it away", "I have just given it away", "I gave it away five minutes ago"),
        TICKED]):
    K[("2.5", n, 1)] = fix(a)
LOUDEST = {1: ("already", "done"), 2: ("haven't", "yet"), 3: ("just", "left"), 4: ("finished", "yet")}
for n, (first, second) in LOUDEST.items():
    K[("2.6", n, 1)] = choose(LOUD[n], first)
    K[("2.6", n, 2)] = choose(LOUD[n], second)
MDG = ["MAKE", "DO", "GIVE"]
SORT = {"a donation": "MAKE", "voluntary work": "DO", "directions": "GIVE", "a payment": "MAKE", "a job": "DO",
        "advice": "GIVE", "a note": "MAKE", "the shopping": "DO", "an example": "GIVE"}
for n, noun in enumerate(NOUNS, 1):
    K[("3.1", n, 1)] = choose(MDG, SORT[noun])
for n, a in enumerate(["made", "gave", "do", "gave", "did", "made"], 1):
    K[("3.2", n, 1)] = Q(a)
for n, a in enumerate(["make", "give", "give", "do", "give", "do"], 1):
    K[("3.3", n, 1)] = Q(a)
# as numbered: 1 just 2 yet 3 enjoy 4 you 5 join 6 young
for n, a in enumerate(["/dʒ/", "/j/", "/dʒ/", "/j/", "/dʒ/", "/j/"], 1):
    K[("3.4", n, 1)] = choose(["/dʒ/", "/j/"], a)
for n, a in enumerate([
        either("She gave me some good advice about it", "She gave me some good advice"),
        either("I want to make a donation to that charity", "I want to make a donation"),
        either("He did a very good job on the kitchen", "He did a very good job"),
        either("Can you do me a favour", "Can you do me a favor", "Can you give me a hand")], 1):
    K[("3.5", n, 1)] = write(a)
for n, a in enumerate(["bored", "furniture", "transport"], 1):
    K[("4.1", n, 1)] = choose(CHOICE41[n], a)
for n in range(1, 4):                             # notes, in their words
    K[("4.2", n, 1)] = own()
for key, a in (((1, 1), "gave"), ((1, 2), "already"), ((2, 1), either("haven't given", "have not given")),
               ((2, 2), "away yet/yet"), ((3, 1), "Have"), ((3, 2), "missed"), ((3, 3), "yet"), ((4, 1), "sold"),
               ((4, 2), either("haven't wanted", "have not wanted")),
               ((5, 1), have("just started", "just"))):
    K[("4.3",) + key] = Q(a)
for n in range(1, 4):
    K[("4.6", n, 1)] = choose(["A", "B"], "B")
for n in range(1, 7):                             # you, then your partner, three rows
    K[("4.7", n, 1)] = own() if n % 2 else pair()
for n in range(7, 10):                            # the question and answers, asked in class
    K[("4.7", n, 1)] = pair()
YN = {"yes": "yes", "no": "no"}
for n, (who, a) in enumerate([("Shona", "yes"), ("Jack", "no"), ("Jessica", "yes"), ("William", "no")]):
    K[("5.1", 2 * n + 1, 1)] = choose(["yes", "no"], a, labels=YN)
    K[("5.1", 2 * n + 2, 1)] = own(control=None)
for n, a in enumerate("2413", 1):                 # a b c d
    K[("5.3", n, 1)] = choose(["1", "2", "3", "4"], a)
for n, a in enumerate("cadb", 1):
    K[("5.4", n, 1)] = choose(["a", "b", "c", "d"], a)
for n, a in enumerate("BABA", 1):
    K[("5.5", n, 1)] = choose(["A", "B"], a)
for n in range(1, 5):                             # the plan: notes
    K[("5.6", n, 1)] = own(control=None)
K[("5.7", 20, 1)] = own(control="essay")
for n in range(1, 7):                             # the checklist
    K[("5.7", n, 1)] = tick()

if __name__ == "__main__":
    data = h.build(K, "Pre-Intermediate", 3, "Unit 3B & 3D — Money")
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "p03bd.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
