"""E07BD Transport - Azamat's Elementary booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(E07BD Transport - answer key), joined box by box by hand. The Desktop
"new design" copy is used; it splits into its five parts as it should.

As with E12AC and E12BD, the booklet speaks Uzbek wherever it explains: every
explanation box, the goals, the "Why" column of the listening table, and a
line under every instruction. The English examples stay English, as do the
reading text, the dialogues, the model email and the exercises.

Put right here: 2.5 says TWO sentences are correct, but three are (2, 5 and
8, as the key has it): it says THREE. 4.9 and 5.9 number their lines 1-5 and
then ask for the order 1-5; the lines lose their numbers, so the only
numbers are the ones tapped.

What a phone gets that paper does not:
  - taps for every choice: which city, A/B/C, T/F, love/like/don't mind,
    like or 'd like, do/does, + or -, the stressed syllable, which word is
    different, S or A, the order, after/when/while, true for Ahmed or not;
  - boxes where paper has none: 1.3, 2.5, 2.8, 3.4, 3.5, 3.9, 4.1, 4.10,
    5.1, 5.4, 5.7, 5.8, 5.11.
3.15 (several right pairings; the key says accept any the student can
justify) and 5.10 (the point is the comma, which marking ignores) are for
the teacher.

    python3 handouts/e07bd_digital.py            # writes handouts/e07bd.json, lists every box
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import (Handout, Q, choose, tick, own, write, fix, note, report,   # noqa: E402
                     BLANK_TAG, LEADER_P, plain, ITEM_STYLE, NUM_SPAN, TEXT_SPAN)

DOCX = "~/Desktop/Handouts/A2 Elementary/E07BD Transport/E07BD Transport — handout (new design).docx"
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


# ------------------------------------------------------------ 1 Reading
boxes_for("1.3", range(1, 5), where="options")
h.options_on_lines("1.3")
for n in range(1, 6):
    h.item_box("1.4", n, placeholder="If it is false, correct it")
a, b = section("1.4"), section("1.5")             # the ruled lines the boxes replace
h.html = h.html[:a] + LEADER_P.sub("", h.html[a:b]) + h.html[b:]
boxes_for("1.5", range(1, 5), where="leader")

# ------------------------------------------------------------ 2 Grammar
reword("2.5", "Find and correct the mistake. TWO sentences are correct — tick them.",
       "Find and correct the mistake. THREE sentences are correct — tick them.")
boxes_for("2.5", range(2, 9))                     # item 1 is the worked example
FORMS28 = {1: ["like", "'d like"], 2: ["like", "'d like"], 3: ["likes", "'d like"], 4: ["like", "'d like"],
           5: ["like", "'d like"], 6: ["likes", "'d like"]}
boxes_for("2.8", FORMS28)
MEANINGS211 = halves("2.11", "a-d")
h.options_on_lines("2.14")
h.leaders("2.15", "3.1  </span>", [(1, W, "Four true sentences about you")])

# ------------------------------------------------------------ 3 Vocabulary
SYLLABLES = {1: "com-for-ta-ble", 2: "ex-pen-sive", 3: "dan-ger-ous", 4: "un-com-for-ta-ble", 5: "crow-ded",
             6: "emp-ty"}
boxes_for("3.4", SYLLABLES)
FORMS35 = {1: ["cheap", "expensive"], 2: ["safe", "dangerous"], 3: ["empty", "crowded"],
           4: ["comfortable", "uncomfortable"], 5: ["fast", "slow"], 6: ["clean", "dirty"]}
boxes_for("3.5", FORMS35)
ENDS38 = halves("3.8", "a-d")
ODD39 = {1: ["fast", "quick", "slow", "rapid"], 2: ["cheap", "expensive", "costly", "dear"],
         3: ["clean", "dirty", "tidy", "washed"], 4: ["safe", "dangerous", "careful", "secure"]}
boxes_for("3.9", ODD39)
boxes_for("3.10", range(1, 5), where="leader")
ADJ315 = halves("3.15", "a-e", token="{{box:%s:%s:120px:e.g. a, c}}")
h.options_on_lines("3.18")
h.leaders("3.19", "BEFORE YOU LISTEN", [(1, W, "Transport in your town, with four adjectives")])

# ------------------------------------------------------------ 4 Listening
HOW41 = ["metro", "car", "bus", "on foot"]
boxes_for("4.1", (1, 2))
h.grid_rows("4.2")
h.grid_rows("4.3")
TOPICS49 = {1: "the traffic", 2: "the stations", 3: "how they came", 4: "the car", 5: "the metro"}
in_order("4.9", TOPICS49)
boxes_for("4.10", (1, 2, 3))
h.options_on_lines("4.10")

# ------------------------------------------------------------ 5 Writing
h.after_instruction("5.1", [(1, "", "60px", "")])
LINKS = ["after", "when", "while"]
boxes_for("5.4", range(1, 6))
boxes_for("5.7", range(1, 5), where="leader")
boxes_for("5.8", range(1, 5), where="leader")
PARTS59 = {1: "my free time and what I like doing", 2: "Best wishes, and my name", 3: "Dear …, and thank you",
           4: "my age, my study and my family", 5: "what I want to do there"}
in_order("5.9", PARTS59)
h.item_box("5.11", 1)
h.options_on_lines("5.11")
h.leaders("5.12", "CHECK BEFORE", [(20, W, "Write your email here")])
h.html = h.html.replace(TAGS[200], "", 1)         # the word count: the box counts them itself

# ------------------------------- every instruction, once more, in Uzbek
for label, text in [
        ("1.1", "Muhokama qiling. Maktabga yoki ishga qanday borasiz? Bu qancha vaqt oladi?"),
        ("1.2", "Qaysi shahar? *I* (Istanbul), *B* (Bogota) yoki *A* (Almati) ni tanlang."),
        ("1.3", "Eng toʻgʻri javobni tanlang: *A*, *B* yoki *C*."),
        ("1.4", "Toʻgʻri (*T*) mi yoki notoʻgʻri (*F*) mi? Notoʻgʻrilarini toʻgʻrilab yozing."),
        ("1.5", "Matndan shu maʼnodagi soʻzni toping."),
        ("1.6", "Matnni toʻldiring: har bir boʻshliqqa BITTA soʻz."),
        ("1.7", "Qaysi shaharga borishni xohlaysiz? Sherigingizga nega ekanini ayting."),
        ("2.1", "*-ing* shaklini yozing."),
        ("2.2", "Soʻzlarni toʻgʻri tartibda yozing."),
        ("2.3", "Qavs ichidagi feʼlning toʻgʻri shakli bilan toʻldiring."),
        ("2.4", "Qaysi biri? *love*, *like*, *don't mind*, *don't like* yoki *hate* ni tanlang."),
        ("2.5", "Xatoni topib, toʻgʻrilang. UCHTA gap toʻgʻri — ular uchun *✓ It is correct* tugmasini bosing."),
        ("2.6", "Gaplarni inkor shaklda yozing."),
        ("2.7", "Savollar yozing, keyin sherigingizdan soʻrang."),
        ("2.8", "*like* mi yoki *would like* mi? Toʻgʻrisini tanlang."),
        ("2.9", "Suhbatni qutidagi soʻzlar bilan toʻldiring."),
        ("2.10", "*-ing* shaklining imlosini toʻgʻrilang."),
        ("2.11", "Gapni maʼnosi bilan moslang: harfni tanlang."),
        ("2.12", "*do*, *does*, *don't* yoki *doesn't* ni tanlang."),
        ("2.13", "Matnni feʼlning *-ing* shakli bilan toʻldiring."),
        ("2.14", "Toʻgʻri javobni tanlang: *A*, *B* yoki *C*."),
        ("2.15", "Oʻzingiz haqingizda toʻrtta rost gap yozing. Har birida boshqa feʼl ishlating."),
        ("3.1", "Jadvalni qarama-qarshi maʼnodagi sifat bilan toʻldiring."),
        ("3.2", "Ijobiy (+) mi yoki salbiy (−) mi? Tanlang."),
        ("3.3", "Har bir gapni sifat bilan toʻldiring."),
        ("3.4", "Soʻz urgʻusi. Urgʻuli boʻgʻinni tanlang, keyin soʻzni ovoz chiqarib ayting."),
        ("3.5", "Toʻgʻri sifatni tanlang."),
        ("3.6", "Sherigingizning gapiga qarshi chiqing. Qarama-qarshi sifatni ishlating."),
        ("3.7", "Matnni toʻldiring: har bir boʻshliqqa BITTA sifat."),
        ("3.8", "Ikki qismni moslang: harfni tanlang."),
        ("3.9", "Qaysi soʻz boshqacha? Uni tanlang."),
        ("3.10", "Har bir gapdagi xatoni topib, toʻgʻri gapni yozing."),
        ("3.11", "Qavs ichidagi feʼlni *-ing* shaklida yozing."),
        ("3.12", "Ikkinchi gapni qarama-qarshi maʼnodagi sifat bilan toʻldiring."),
        ("3.13", "Bir soʻz bilan javob bering. Qaysi sifat?"),
        ("3.14", "Suhbatni sifatlar bilan toʻldiring."),
        ("3.15", "Qaysi sifatlar qaysi otga mos keladi? Baʼzilari bir nechtasiga mos. Harflarini yozing."),
        ("3.16", "Qarama-qarshi maʼnodagi gapni yozing."),
        ("3.17", "Qutidagi sifat bilan toʻldiring. Har bir soʻzni bir marta ishlating."),
        ("3.18", "Toʻgʻri javobni tanlang: *A*, *B* yoki *C*."),
        ("3.19", "Shahringizdagi transport haqida yozing. Bu boʻlimdagi toʻrtta sifatni ishlating."),
        ("4.1", "Tinglashdan oldin taxmin qiling. Har bir kishi qanday kelgan deb oʻylaysiz?"),
        ("4.2", "Bir marta tinglang. Jadvalni toʻldiring."),
        ("4.3", "Yana tinglang. Har bir kishi nima deb oʻylaydi? Jadvalni toʻldiring."),
        ("4.4", "Yana bir marta tinglang. Har bir gapni *love*, *like*, *don't like*, *don't mind* yoki *hate* "
                "bilan toʻldiring."),
        ("4.5", "Tinglang va nima boʻlishiga eʼtibor bering."),
        ("4.6", "Har bir gapni ikki marta ayting — avval sekin, keyin tez."),
        ("4.7", "Buni kim aytadi — Svetlana (*S*) mi yoki Alex (*A*) mi?"),
        ("4.8", "Tinglang va suhbatdagi qatorlarni toʻldiring."),
        ("4.9", "Mavzularni eshitgan tartibingizda raqamlang (1–5)."),
        ("4.10", "Gapiruvchi nima demoqchi? *A* yoki *B* ni tanlang."),
        ("5.1", "Tinglang. Finn Ahmedga qaysi oilani tanlashni aytadimi?"),
        ("5.2", "Yana tinglang. Har bir qator Ahmed uchun toʻgʻrimi? *✓* yoki *✗* ni tanlang."),
        ("5.3", "Ahmed uchun qaysi oila yaxshi? Nega? Sherigingizga ayting."),
        ("5.4", "Toʻgʻri soʻzni tanlang. Baʼzan ikkitasi ham toʻgʻri boʻladi."),
        ("5.5", "Qavs ichidagi soʻz bilan ikki gapni bitta qiling."),
        ("5.6", "Namunaviy emailni oʻqing. Keyin savollarga javob bering."),
        ("5.7", "Namuna haqidagi savollarga javob bering."),
        ("5.8", "Har bir gapdagi xatoni topib, toʻgʻri gapni yozing."),
        ("5.9", "Email qismlarini toʻgʻri tartibda raqamlang (1–5)."),
        ("5.10", "Bogʻlovchi soʻzni gap boshiga qoʻyib, gapni qayta yozing. Vergulni unutmang."),
        ("5.11", "Emailni tugatish uchun qaysi gap eng yaxshi? *A*, *B* yoki *C* ni tanlang."),
        ("5.12", "Emailingizni yozing (60–80 soʻz). Ikkita bogʻlovchi soʻz va *-ing* bilan uchta yoqtirish "
                 "feʼlini ishlating.")]:
    h.say_also(label, text)

# ------------------------------------------ the explanations, told in Uzbek
h.goals([
    "nimani qilishni yoqtirishingiz va yoqtirmasligingizni aytishni",
    "transportni tasvirlashni — *fast, crowded, cheap*",
    "safar haqida fikr bildirayotgan odamlarni tushunishni",
    "gaplarni *after*, *when* va *while* bilan bogʻlashni",
    "oʻzingiz haqingizda email yozishni",
])
h.retell("KEY WORDS", "KALIT SOʻZLAR", [
    "**underground**  yer ostida",
    "**crowded**  odam juda koʻp, tiqilinch",
    "**a lane**  yoʻlning bir qismi, alohida yoʻlak",
    "**a passenger**  yoʻlovchi — transportda ketayotgan odam",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — LOVE / LIKE / DON'T MIND / HATE + -ING", [
    "Bu feʼllar bilan biror ishni qanchalik yoqtirishimizni aytamiz. Ulardan keyingi feʼl *-ing* bilan tugaydi.",
    "[[A]] Juda yoqadi → *love* · *I love going on the metro.*",
    "[[B]] Yaxshi → *like* · *I like driving in the city.*",
    "[[C]] Mayli, farqi yoʻq → *don't mind* · *I don't mind sitting in traffic.*",
    "[[D]] Yoqmaydi → *don't like* · Umuman yoqmaydi → *hate* · *I hate sitting in traffic.*",
    "**-ing ning imlosi:** *drive → driving* (*e* tushib qoladi) · *sit → sitting* (*t* ikkilanadi) · "
    "*go → going* · *travel → travelling*.",
    "Bu feʼllardan keyin ot ham kelishi mumkin: *I love cars. · I hate buses.*",
])
h.retell("ERROR WARNING", "DIQQAT — KOʻP UCHRAYDIGAN XATOLAR", [
    "1 **love / like / don't mind / hate dan keyingi feʼl doim -ing bilan tugaydi** (bu darajada). "
    "✗ *I hate use public transport.* → ✓ *I hate using public transport.* · ✗ *I love to go by car.* → "
    "✓ *I love going by car.*",
    "2 **Birinchi feʼlga -ing qoʻshmang.** ✗ *I loving cars.* → ✓ *I love cars.*",
    "3 **I like va I'd like — har xil narsa.** ✗ *I like travelling to Canada next year.* → ✓ *I'd like to "
    "travel to Canada next year.*",
    "*I like* = doim, umuman. *I'd like* = xohlayman, kelajakda bir marta — va undan keyin *-ing* emas, "
    "*to* + feʼl keladi.",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — TRANSPORT SIFATLARI", [
    "Bu sifatlar qarama-qarshi juftlik boʻlib keladi. Ularni ikkitadan oʻrganing.",
    "[[A]] *fast ↔ slow* · *The tram is fast. The bus is slow.*",
    "[[B]] *safe ↔ dangerous · clean ↔ dirty*",
    "[[C]] *empty ↔ crowded* (yoki *full*) · *comfortable ↔ uncomfortable*",
    "[[D]] *cheap ↔ expensive* · *A ticket is cheap. A taxi is expensive.*",
    "**Soʻz urgʻusi:** *COM-for-ta-ble · DAN-ger-ous · ex-PEN-sive · un-COM-for-ta-ble · CROW-ded*.",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [
    "Svetlana va Alexni eshitasiz. Ular Moskvada yashaydi va shahar markazida uchrashishyapti. Ikkalasi har xil "
    "yoʻl bilan kelgan.",
    "Agar sinfingizda audio boʻlsa, bu 07.10-trek. Boʻlmasa, oʻqituvchingiz matnni oʻqib beradi — topshiriqlar "
    "bir xil.",
])
h.retell("WHY YOU DIDN'T HEAR IT", "NEGA ESHITMADINGIZ?", [
    "**Tez nutqda don't juda qisqa.** Boshqa undoshdan oldin *t* deyarli yoʻqoladi: *I don't like* "
    "/aɪ dəʊn laɪk/ boʻlib, *I don't mind* esa /aɪ dəʊm maɪnd/ boʻlib eshitiladi.",
    "Asosiy feʼldan oldingi qisqa, past ovozli soʻzga quloq soling.",
])
h.retell("LISTENING INTO WRITING", "TINGLASHDAN YOZISHGA", [
    "Avval Ahmed va Finnni tinglang. Ahmed Sidneyga ketyapti va u yerda yashash uchun oila (*homestay*) tanlashi "
    "kerak. Agar sinfingizda audio boʻlsa, bu 07.21-trek.",
])
h.retell("LINKING IDEAS: AFTER, WHEN, WHILE", "GAPLARNI BOGʻLASH: AFTER, WHEN, WHILE", [
    "*while* va *when* bir vaqtda boʻladigan ikki narsani bogʻlaydi: *I want to study while I'm in Sydney.*",
    "*after* va *when* har xil vaqtda boʻladigan ikki narsani bogʻlaydi: *I want to work after I finish "
    "university.*",
    "Bogʻlovchi soʻz gap boshida kelsa, ikki qism orasiga vergul qoʻyiladi: *When I'm in Sydney, I want to study "
    "hard.*",
])
h.retell("ERROR WARNING", "DIQQAT — AFTER, WHEN, WHILE DAN KEYIN WILL YOʻQ", [
    "**after, when yoki while dan keyin hech qachon will ishlatmang.** Hozirgi oddiy zamonni (*present simple*) "
    "ishlating:",
    "✗ *When I will be in Sydney…* → ✓ *When I'm in Sydney, I want to study.*",
    "✗ *I want to be a teacher after I will finish university.* → ✓ *after I finish university*",
    "Maʼno baribir kelasi zamon — lekin feʼl hozirgi zamonda. Ingliz tilida shunday, oʻzbek tilida esa unday "
    "emas, shuning uchun yozgan har bir gapingizni tekshiring.",
])
h.retell("PLAN", "REJA", [
    "**1-xatboshi** — ismingiz, mamlakatingiz va minnatdorchilik. **2-xatboshi** — yoshingiz, oʻqishingiz yoki "
    "ishingiz, oilangiz.",
    "**3-xatboshi** — boʻsh vaqtingiz. *love · like · don't mind · hate* + *-ing* ni ishlating. **4-xatboshi** — "
    "u yerda nima qilmoqchisiz va undan keyin nima qilmoqchisiz.",
    "**5-xatboshi** — *I'm looking forward to meeting you when I arrive.* Keyin *Best wishes* va ismingiz.",
])
h.retell("USEFUL PHRASES", "FOYDALI IBORALAR", [
    "**Boshlanishi:** *Dear Mr and Mrs …, · Thank you for offering to be my homestay family.*",
    "**Oʻzingiz haqingizda:** *My name is … and I come from … · I am … years old and I study … · In my free time "
    "I love …*",
    "**Tugashi:** *I'm looking forward to meeting you when I arrive. · Best wishes,*",
])
h.retell("CHECK BEFORE YOU HAND IT IN", "TOPSHIRISHDAN OLDIN TEKSHIRING", [
    "{box}  *Dear* bilan boshladim va *Best wishes* bilan tugatdim.   {box}  Minnatdorchilik bildirdim.   "
    "{box}  Kim ekanimni aytdim.",
    "{box}  Oʻqishim yoki ishim va boʻsh vaqtim haqida yozdim.   {box}  Oilam haqida yozdim.   "
    "{box}  U yerda nima qilmoqchi ekanimni aytdim.",
    "{box}  *after, when* yoki *while* ni ikki marta ishlatdim, ulardan keyin *will* yoʻq.   {box}  *love / like "
    "/ don't mind / hate* dan keyingi har bir feʼl *-ing* bilan tugaydi.",
    "{box}  *I'm looking forward to…* ni ishlatdim.   {box}  Soʻzlarimni sanadim.",
])
h.one_per_line("TOPSHIRISHDAN OLDIN TEKSHIRING", None, at="box")
h.retell_cells({"Feeling": "Hissiyot", "Sentence": "Gap", "Meaning": "Maʼnosi"})
h.retell_cells({"What is written": "Yozilishi", "What you hear": "Eshitilishi", "Why": "Nega",
                "the t disappears before l": "<i>l</i> dan oldin <i>t</i> yoʻqoladi",
                "n becomes m before m": "<i>m</i> dan oldin <i>n</i> <i>m</i> ga aylanadi",
                "love and going join": "<i>love</i> va <i>going</i> qoʻshilib ketadi",
                "it is → it's": "<i>it is</i> → <i>it's</i> boʻladi"},
               after="4.5  </span>")

# ------------------------------------------------------------------ the key
K = {}
CITY = {"I": "I · Istanbul", "B": "B · Bogotá", "A": "A · Almaty"}
for n, a in enumerate("BAAIBA", 1):
    K[("1.2", n, 1)] = choose(["I", "B", "A"], a, labels=CITY)
for n, a in enumerate("BBBC", 1):
    K[("1.3", n, 1)] = choose(["A", "B", "C"], a)
TF = {"T": "T · true", "F": "F · false"}
for n, a in enumerate("FTFFT", 1):
    K[("1.4", n, 1)] = choose(["T", "F"], a, labels=TF)
    K[("1.4", n, 2)] = note()
for n, a in enumerate(["crowded", "a lane/lane/lanes", "a passenger/passenger/passengers", "quiet"], 1):
    K[("1.5", n, 1)] = Q(a)
for n, a in enumerate(["cheap", "late", "metro", "seat", "beautiful/comfortable/quiet", "stations"], 1):
    K[("1.6", n, 1)] = Q(a)
for n, a in zip(range(2, 9), ["sitting", "driving", "walking", "travelling/traveling", "waiting", "flying",
                              "getting"]):
    K[("2.1", n, 1)] = Q(a)
for n, a in enumerate(["I love going on the metro", "I don't like driving", "I hate sitting in traffic",
                       "I don't mind walking"], 1):
    K[("2.2", n, 1)] = write(a)
for n, a in enumerate(["travelling/traveling", "waiting", "walking", "flying", "driving", "getting", "sitting",
                       "using"], 1):
    K[("2.3", n, 1)] = Q(a)
FEEL = ["love", "like", "don't mind", "don't like", "hate"]
for n, a in enumerate(["love", "hate", "don't mind", "like", "don't like"], 1):
    K[("2.4", n, 1)] = choose(FEEL, a)
TICKED = "✓/correct/tick"
for n, a in zip(range(2, 9), [
        TICKED,
        either("I love going by car", "going"),
        either("I love my new bicycle", "love"),
        TICKED,
        either("He doesn't like flying", "He does not like flying", "doesn't"),
        either("I'd like to travel to Canada next summer", "I would like to travel to Canada next summer",
               "I'd like to travel"),
        TICKED]):
    K[("2.5", n, 1)] = fix(a)
for n, a in enumerate([
        either("I don't like walking to work", "I do not like walking to work"),
        either("She doesn't love flying", "She does not love flying", "She doesn't like flying", "She hates flying"),
        either("They don't like sitting in traffic", "They do not like sitting in traffic"),
        either("He doesn't mind waiting", "He does not mind waiting")], 1):
    K[("2.6", n, 1)] = write(a)
for n, a in enumerate([either("Do you like travelling by bus", "Do you like traveling by bus"),
                       "Does your friend love driving", "Do you mind walking in the rain",
                       "Does your family hate waiting"], 1):
    K[("2.7", n, 1)] = write(a)
for n, a in enumerate(["'d like", "like", "'d like", "like", "like", "'d like"], 1):
    K[("2.8", n, 1)] = choose(FORMS28[n], a)
BOX29 = ["love", "don't like", "hate", "don't mind", "like"]
for n, a in enumerate(["hate", "don't mind", "like", "love", "don't like"], 1):
    K[("2.9", n, 1)] = choose(BOX29, a)
for n, a in enumerate(["driving", "sitting", "getting", "waiting", "flying", "walking"], 1):
    K[("2.10", n, 1)] = Q(a)
for n, a in enumerate("badc", 1):
    K[("2.11", n, 1)] = choose(MEANINGS211, a)
DOES = ["do", "does", "don't", "doesn't"]
for key, a in (((1, 1), "do"), ((1, 2), "do"), ((2, 1), "does"), ((2, 2), "doesn't"), ((3, 1), "don't"),
               ((4, 1), "doesn't"), ((5, 1), "do"), ((6, 1), "don't")):
    K[("2.12",) + key] = choose(DOES, a)
for n, a in enumerate(["driving", "sitting", "standing", "cycling", "going", "walking"], 1):
    K[("2.13", n, 1)] = Q(a)
for n, a in enumerate("BBBA", 1):
    K[("2.14", n, 1)] = choose(["A", "B", "C"], a)
K[("2.15", 1, 1)] = own()
for n, a in enumerate(["slow", "safe", "crowded/full", "comfortable", "dirty", "cheap"], 1):
    K[("3.1", n, 1)] = Q(a)
PM = {"+": "+ positive", "−": "− negative"}
for n, a in zip(range(2, 9), ["−", "−", "+", "+", "−", "+", "−"]):
    K[("3.2", n, 1)] = choose(["+", "−"], a, labels=PM)
for n, a in enumerate(["empty", "expensive", "crowded/full", "comfortable", "slow", "dirty"], 1):
    K[("3.3", n, 1)] = Q(a)
STRESSED = {1: "com", 2: "pen", 3: "dan", 4: "com", 5: "crow", 6: "emp"}
for n, word in SYLLABLES.items():
    K[("3.4", n, 1)] = choose(word.split("-"), STRESSED[n])
for n, a in enumerate(["cheap", "dangerous", "empty", "uncomfortable", "fast", "clean"], 1):
    K[("3.5", n, 1)] = choose(FORMS35[n], a)
for n, a in enumerate(["cheap", "crowded/full", "comfortable/fast/clean", "comfortable/clean", "cheap/fast/safe",
                       "dangerous"], 1):
    K[("3.7", n, 1)] = Q(a)
for n, a in enumerate("badc", 1):
    K[("3.8", n, 1)] = choose(ENDS38, a)
for n, a in enumerate(["slow", "cheap", "dirty", "dangerous"], 1):
    K[("3.9", n, 1)] = choose(ODD39[n], a)
for n, a in enumerate([
        either("The train is very crowded today", "crowded"),
        either("This seat is uncomfortable", "uncomfortable"),
        either("Taxis in my city are very expensive", "expensive"),
        either("The metro is cleaner than the bus", "cleaner", "cleaner than the bus")], 1):
    K[("3.10", n, 1)] = write(a)
for n, a in enumerate(["standing", "sitting", "walking", "cycling"], 1):
    K[("3.11", n, 1)] = Q(a)
for n, a in enumerate(["empty", "cheap", "uncomfortable", "safe", "clean", "fast"], 1):
    K[("3.12", n, 1)] = Q(a)
for n, a in enumerate(["crowded/full", "cheap", "comfortable", "empty"], 1):
    K[("3.13", n, 1)] = Q(a)
for n, a in enumerate(["crowded/full", "cheap", "fast/quick", "slow", "comfortable"], 1):
    K[("3.14", n, 1)] = Q(a)
for n in range(1, 6):                             # several pairings work: the teacher's to judge
    K[("3.15", n, 1)] = own(control=None)
for n, a in enumerate(["empty", "expensive", "dirty", "dangerous"], 1):
    K[("3.16", n, 1)] = Q(a)
BOX317 = ["fast", "dirty", "empty", "expensive", "uncomfortable", "safe"]
for n, a in enumerate(["empty", "safe", "uncomfortable", "dirty", "fast", "expensive"], 1):
    K[("3.17", n, 1)] = choose(BOX317, a)
for n, a in enumerate("BABB", 1):
    K[("3.18", n, 1)] = choose(["A", "B", "C"], a)
K[("3.19", 1, 1)] = own()
for n in (1, 2):                                  # a guess before listening
    K[("4.1", n, 1)] = choose(HOW41)
for n, a in enumerate(["metro/the metro/by metro/on the metro", "half an hour/30 minutes/thirty minutes",
                       "car/by car/the car", "about an hour/an hour/one hour/1 hour/about one hour"], 1):
    K[("4.2", n, 1)] = Q(a)
for n, a in enumerate([
        "quick/so quick/fast",                                   # metro: Svetlana
        "crowded/so crowded/dirty/crowded and dirty/not clean/not always very clean/crowded and not clean",
        "beautiful",                                             # stations
        "terrible",
        "slow/always so slow/so slow/always slow/boring",       # driving
        "not too bad/not bad/OK/okay/fine/good/nice",
        "very nice/nice",                                        # the car
        "nice/quite nice/comfortable/very comfortable/big/big inside/comfortable and big/"
        "very comfortable and big inside/nice, comfortable and big/quite a nice car"], 1):
    K[("4.3", n, 1)] = Q(a)
for n, a in enumerate(["love", "don't like", "love", "like", "hate", "don't mind"], 1):
    K[("4.4", n, 1)] = choose(["love", "like", "don't mind", "don't like", "hate"], a)
SA = {"S": "S · Svetlana", "A": "A · Alex"}
for n, a in enumerate("SASASA", 1):
    K[("4.7", n, 1)] = choose(["S", "A"], a, labels=SA)
for n, a in enumerate(["traffic", "course", "quick", "clean", "radio", "big"], 1):
    K[("4.8", n, 1)] = Q(a)
ORDER = ["1", "2", "3", "4", "5"]
# heard in this order: how they came, the metro, the stations, the traffic, the car
for n, a in {1: "4", 2: "3", 3: "1", 4: "5", 5: "2"}.items():
    K[("4.9", n, 1)] = choose(ORDER, a)
for n, a in enumerate("BBA", 1):
    K[("4.10", n, 1)] = choose(["A", "B"], a)
K[("5.1", 1, 1)] = choose(["Yes", "No"], "No")
AHMED = {"yes": "✓ true for Ahmed", "no": "✗ not true"}
for n, a in enumerate(["no", "no", "yes", "yes", "yes", "yes", "no", "no"], 1):
    K[("5.2", n, 1)] = choose(["yes", "no"], a, labels=AHMED)
for n, a in enumerate(["after/when", "when/while", "after/when", "after/when", "when/while"], 1):
    K[("5.4", n, 1)] = choose(LINKS, a)
for n, a in enumerate([
        either("After I finish school, I want to study medicine", "I want to study medicine after I finish school"),
        either("While I'm in London, I want to see the Tube", "While I am in London, I want to see the Tube",
               "I want to see the Tube while I'm in London", "I want to see the Tube while I am in London"),
        either("When I arrive, I'll send you a message", "When I arrive, I will send you a message",
               "I'll send you a message when I arrive", "I will send you a message when I arrive")], 1):
    K[("5.5", n, 1)] = write(a)
for n in (1, 2, 4):
    K[("5.7", n, 1)] = own()
K[("5.7", 3, 1)] = Q("Paragraph 2/2/paragraph two/the second paragraph/the second one/second")
for n, a in enumerate([
        either("When I arrive in Sydney, I want to call you", "When I arrive in Sydney", "arrive"),
        either("I want to work after I finish university", "after I finish university", "finish"),
        either("While I am in London, I'd like to see the Tube", "While I'm in London, I'd like to see the Tube",
               "While I am in London", "While I'm in London", "am"),
        either("After I finish this course, I would like to travel", "After I finish this course", "finish")], 1):
    K[("5.8", n, 1)] = write(a)
# the email's parts in order: Dear, my age, my free time, what I want to do, Best wishes
for n, a in {1: "3", 2: "5", 3: "1", 4: "2", 5: "4"}.items():
    K[("5.9", n, 1)] = choose(ORDER, a)
for n in range(1, 4):                             # the comma is the point, and marking ignores commas
    K[("5.10", n, 1)] = own()
K[("5.11", 1, 1)] = choose(["A", "B", "C"], "B")
K[("5.12", 20, 1)] = own(control="essay")
for n in range(1, 11):                            # the checklist
    K[("5.12", n, 1)] = tick()

if __name__ == "__main__":
    data = h.build(K, "Elementary", 7, "Unit 7B & 7D — Transport")
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "e07bd.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
