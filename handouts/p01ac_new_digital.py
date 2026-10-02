"""P01AC Communicating - the new-style Pre-Intermediate booklet (1A & 1C), done on a phone.

It replaces "Unit 1A & 1C - Communication" (test 87, p01ac_digital.py), whose
booklet was the older design; the exercises are all new, so no answers carry
across. Built like b04b_digital.py: it reads a TEAL build of the booklet
(BOOK_THEME=teal node build_p01ac.js, kept in the Material Bank's
"B1 Pre-intermediate/_NEW BOOKLET STYLE/digital source/") and unwraps the
one-cell tables that keep each exercise on one page of paper.

As on the other Pre-Intermediate handouts, every explanation is told again in
Uzbek (English examples kept) and every instruction has a line in Uzbek; the
reading, the model and the exercises stay English. The key is his
(P01AC Communicating - ANSWER KEY), box by box.

What a phone gets that paper does not:
  - taps: the headings (1.2), TRUE / FALSE / NOT GIVEN (1.3), the question
    word (2.3), the adjective groups (3.2, a line per adjective instead of
    the table), the stress pattern (3.4, likewise), the conversations (4.2),
    T / F (5.1), greeting or ending (5.3), the three checks before sending
    the recording (6.2);
  - a box per item where paper has ruled lines (2.1, 2.4, 2.6, 5.5 marked
    by the key; 2.5, 2.9, 4.4, 5.4 the student's own);
  - 2.7: the mistake as the student found it (not marked), then the
    correction (marked, with the short and the whole-sentence forms);
  - 3.3's first letters stay on the page, so the box takes the whole word or
    only the rest of it.
2.8 (stress in questions) has no box: it is listening and saying aloud.

    python3 handouts/p01ac_new_digital.py       # writes handouts/p01ac_new.json, lists every box
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import (Handout, Q, choose, tick, own, write, note, report,   # noqa: E402
                     plain, told, bh_section_at, ITEM_STYLE, NUM_SPAN, TEXT_SPAN)
from variants import ok   # noqa: E402

DOCX = ("~/Documents/Claude/Material Bank/General English/B1 Pre-intermediate/_NEW BOOKLET STYLE/digital source/"
        "P01AC Communicating — BOOKLET (teal, for the website).docx")
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


def either(*forms):
    return "/".join(forms)


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


def taps_instead_of_table(label, words):
    """The paper's table to write words into becomes one line per word, with
    the groups to tap; anything between the instruction and the table (a list
    of the words) goes too."""
    a = h._instruction_end(label)
    t = h.html.index('<table class="bk">', a)
    b = h.html.index("</table>", t) + len("</table>")
    rows = ""
    for n, w in enumerate(words, 1):
        h.texts[(label, n)] = w
        rows += ('<p data-item="%s:%d" %s>%s%s</p>'
                 % (label, n, ITEM_STYLE, NUM_SPAN % n,
                    TEXT_SPAN % ("%s  {{box:%s:%d:60px:}}" % (html.escape(w), label, n))))
    h.html = h.html[:a] + rows + h.html[b:]


# ------------------------------------------------------------ 1 Reading
for n in range(1, 9):
    h.item_box("1.3", n, where="leader")
h.leaders("1.5", "Grammar  ·", [(1, W, "Your answer")])

# ------------------------------------------------------------ 2 Grammar
h.leaders("2.1", "2.2  </span>", [(n, W, "Question %d" % n) for n in range(1, 7)])
for n in range(1, 7):
    h.item_box("2.3", n)
h.leaders("2.4", "2.5  </span>", [(n, W, "Sardor's question") for n in range(1, 6)])
h.leaders("2.5", "2.6  </span>", [(1, W, "A good first question"), (2, W, "Too personal - and why")])
h.leaders("2.6", "2.7  </span>", [(n, W, "The question") for n in range(1, 4)])
reword("2.8", "Pronunciation. Listen to track 1.08. Underline the stressed words. Then say each question aloud three times.",
       "Pronunciation. Listen to **track 1.08**. Which words are stressed? Then say each question aloud three times.")
h.leaders("2.9", "Vocabulary  ·", [(1, W, "with be"), (2, W, "with does"), (3, W, "with did"),
                                    (4, W, "with What … like?"), (5, W, "with a preposition at the end")])

# ------------------------------------------------------------ 3 Vocabulary
ADJ = ["wonderful", "perfect", "amazing", "gorgeous", "delicious", "all right", "beautiful", "lovely",
       "awful", "horrible", "rude", "boring", "silly", "serious", "strange", "ugly"]
reword("3.2", "Write the sixteen adjectives from the post in the table.",
       "Which group is each adjective from the post in? Tap **very good**, **OK**, **bad** or **how people act**.")
taps_instead_of_table("3.2", ADJ)
h.leaders("3.3", "3.4  </span>", [(11, W, "Your sentence with wonderful or horrible")])
STRESSED = ["all right", "amazing", "awful", "boring", "delicious", "gorgeous", "horrible", "lovely",
            "perfect", "serious", "silly", "strange", "ugly"]
reword("3.4", "Word stress. Write each adjective in the correct column. Then say the words aloud. "
              "(Listen to track 1.04 to check.)",
       "Word stress. Tap the pattern of each adjective: **●** is the stressed syllable, **•** a weak one. "
       "Then say the words aloud. (Listen to **track 1.04** to check.)")
taps_instead_of_table("3.4", STRESSED)
h.leaders("3.6", "Listening  ·", [(1, W, "Your celebration")])

# ------------------------------------------------------------ 4 Listening
h.leaders("4.4", "Everyday English  ·", [(1, W, "Conversation 2: who, what, your advice"),
                                         (2, W, "Conversation 3: who, what, your advice")])

# ------------------------------------------------------ 5 Everyday English
for n in range(1, 8):
    h.item_box("5.2", n, width="200px", where="leader")
h.leaders("5.4", "5.5  </span>", [(1, W, "Your reply and question"), (2, W, "Your reply and question")])
h.leaders("5.5", "5.6  </span>", [(n, W, "The sentence, correct") for n in range(1, 4)])
reword("5.6", "You meet an old school friend in a shop. Write the conversation (6 lines): greet, show interest "
              "twice, end it. Then underline the words that give information, as in track 1.18, and say your "
              "lines aloud.",
       "You meet an old school friend in a shop. Write the conversation (6 lines): greet, show interest "
       "twice, end it. Then say your lines aloud, stressing the words that give information, as in "
       "**track 1.18**.")
h.leaders("5.6", "Speaking and writing  ·", [(1, W, "Your conversation")])

# ------------------------------------------------- 6 Speaking and writing
h.leaders("6.4", "</div>", [(1, W, "Write your opinion text here")])

# ------------------------------- every instruction, once more, in Uzbek
for label, text in [
        ("1.1", "Oʻqishdan oldin. Oilangizda mehmon bilan qanday salomlashishadi? Bitta gap yozing."),
        ("1.2", "B–F xatboshilar uchun toʻgʻri sarlavhani tanlang. Ikkita sarlavha ortiqcha."),
        ("1.3", "Gaplar matnga mos keladimi? *TRUE* (toʻgʻri), *FALSE* (notoʻgʻri) yoki *NOT GIVEN* (matnda bu "
                "haqda hech narsa yoʻq) ni tanlang."),
        ("1.4", "E va F xatboshilarning qisqacha mazmunini toʻldiring. Matndan IKKI SOʻZDAN KOʻP BOʻLMAGAN soʻz "
                "va/yoki son yozing."),
        ("1.5", "Dalil haqida oʻylang. Chikagodagi yoʻlovchilarga notanish odam bilan gaplashish yoqdi. Bu "
                "Toshkentdagi avtobus yoʻlovchilariga ham yoqadi, degani emasmi? Nega?"),
        ("2.1", "Soʻzlarni tartibga solib, savol tuzing."),
        ("2.2", "*do, does, did, is, are, was* yoki *were* bilan toʻldiring."),
        ("2.3", "Toʻgʻri soʻroq soʻzini tanlang."),
        ("2.4", "Sardor toʻyda bir mehmon bilan tanishdi. Uning savollarini yozing. Javoblar sizga yordam beradi."),
        ("2.5", "Oʻylang. Birinchi suhbat uchun yaxshi BITTA savol va juda shaxsiy BITTA savol yozing. Nega u "
                "juda shaxsiy?"),
        ("2.6", "*What … like?* yoki *Do you like …?* Savolni yozing."),
        ("2.7", "Kamola yangi xonadoshiga yozmoqda. Xabarda BESHTA xato bor. Avval xatoni, keyin toʻgʻrisini "
                "yozing."),
        ("2.8", "Talaffuz. 1.08-trekni tinglang. Qaysi soʻzlar urgʻuli? Keyin har bir savolni uch marta ovoz "
                "chiqarib ayting."),
        ("2.9", "Endi siz. Yangi sinfdoshingizga beshta savol yozing: *be* bilan, *does* bilan, *did* bilan, "
                "*What … like?* bilan va oxirida predlog bilan."),
        ("3.1", "Dilnozaning postini oʻqing. Qalin yozilgan sifatlarga qarang."),
        ("3.2", "Postdagi har bir sifat qaysi guruhda? Tanlang: juda yaxshi (*very good*), oʻrtacha (*OK*), yomon "
                "(*bad*) yoki odamlarning xulqi (*how people act*)."),
        ("3.3", "Har bir gapni 3.2 dagi sifat bilan toʻldiring. Birinchi harf berilgan. Keyin *wonderful* yoki "
                "*horrible* bilan oʻz gapingizni yozing."),
        ("3.4", "Soʻz urgʻusi. Har bir sifatning urgʻu qolipini tanlang: *●* — urgʻuli boʻgʻin, *•* — urgʻusiz "
                "boʻgʻin. Soʻzlarni ovoz chiqarib ayting. Tekshirish uchun 1.04-trekni tinglang."),
        ("3.5", "Har bir gapni KATTA harflar bilan yozilgan soʻzning toʻgʻri shakli bilan toʻldiring."),
        ("3.6", "Oʻylang. Oxirgi borgan bayramingizni ikkita ijobiy va ikkita salbiy sifat bilan tasvirlang."),
        ("4.1", "Bazmdagi gaplarni 3-boʻlimdagi sifat bilan toʻldiring. Keyin tekshirish uchun 1.02-trekni "
                "tinglang."),
        ("4.2", "Qaysi suhbatda (*1*, *2* yoki *3*) bu mavzular haqida gapiriladi? Bitta mavzu ikkita suhbatda bor."),
        ("4.3", "Qaydlarni toʻldiring. Har bir javobga IKKI SOʻZDAN KOʻP yozmang."),
        ("4.4", "Oʻylang. 2- va 3-suhbatda bir kishi suhbatni qiyinlashtiradi. Har safar kim (*D* yoki *C*? *E* "
                "yoki *F*?) va u nima xato qiladi? Har biriga bitta maslahat yozing."),
        ("5.1", "1-qism (1.14-trek). *T* (toʻgʻri) yoki *F* (notoʻgʻri) ni tanlang."),
        ("5.2", "2-qism (1.19-trek). Savollarga javob bering. Har bir javobga UCH SOʻZDAN KOʻP yozmang."),
        ("5.3", "Suhbatlardagi iboralarni BITTA soʻz bilan toʻldiring. Keyin *G* (salomlashish) yoki *E* "
                "(xayrlashish) ni tanlang. Tekshirish uchun 1.15 va 1.20-treklarni tinglang."),
        ("5.4", "Qiziqish bildiring. *What a …!*, *How …!* yoki *That's …!* va 3-boʻlimdagi sifat bilan javob "
                "yozing. Keyin BITTA savol bering."),
        ("5.5", "Har bir gapda BITTA xato bor. Toʻgʻrisini yozing."),
        ("5.6", "Doʻkonda eski maktab doʻstingizni uchratib qoldingiz. Suhbatni yozing (6 qator): salomlashing, "
                "ikki marta qiziqish bildiring, suhbatni tugating. Keyin qatorlaringizni ovoz chiqarib ayting — "
                "1.18-trekdagidek, maʼlumot beruvchi soʻzlarni urgʻu bilan."),
        ("6.1", "Har bir band uchun qayd yozing. Faqat qaydlar — toʻliq gaplar emas."),
        ("6.2", "Oʻzingizni yozib oling. Taxminan bir daqiqa gapiring: qaydlaringiz, siz yoki u odam bergan ikkita "
                "savol va 3-boʻlimdagi ikkita sifatdan foydalaning. Keyin yozuvni oʻqituvchingizga yuboring."),
        ("6.3", "6.4 dagi matningizni rejalashtiring. Namunadan foydalaning. Faqat qaydlar."),
        ("6.4", "*Small talk* — vaqtni behuda sarflash. Qoʻshilasizmi? Uch xatboshidan iborat fikr matnini yozing "
                "(100–130 soʻz). 6.3 dagi reja, 1-boʻlimdagi bitta fikr, 3-boʻlimdagi ikkita sifatdan foydalaning "
                "va oʻquvchiga savol bilan boshlang.")]:
    h.say_also(label, text)

# ------------------------------------------ the explanations, told in Uzbek
h.retell("KEY WORDS", "KALIT SOʻZLAR", [
    "**a stranger**  notanish odam",
    "**to greet**  salomlashmoq",
    "**to bow**  taʼzim qilmoq — boshni yoki gavdani oldinga egmoq",
    "**awkward**  noqulay, qiyin",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — SAVOL SHAKLLARI", [          # the first of the two
    "[[A]] **be bilan savollar:** (soʻroq soʻzi) + **be** + ega. *Are you a student? · Where is your sister? · "
    "Why were you late?* *do* qoʻshilmaydi: *Do you are …?* emas.",
    "[[B]] **Boshqa feʼllar bilan:** (soʻroq soʻzi) + **do / does / did** + ega + feʼlning oddiy shakli. *Where do "
    "you live? · Does she know Ana? · What did you study?* *does* va *did* dan keyin feʼlga *-s* ham, *-ed* ham "
    "qoʻshilmaydi: *Does she work …?* — *Does she works?* emas.",
    "[[C]] **Soʻroq soʻzlari:** *who · what · where · when · why · which · whose · how often* · **how much** + "
    "sanalmaydigan ot (*How much rent …?*) · **how many** + koʻplik (*How many languages …?*) · *what kind of …* "
    "**What … like?** narsani tasvirlab berishni soʻraydi, yoqtirishni emas: *What was the party like?* — *It was "
    "great!*",
    "[[D]] **Istisnolar.** Predlog **oxirida** qoladi: *Where are you from? · Who do you live with? · What are you "
    "talking about?* *can, will, should* bilan ham *do* ishlatilmaydi: *Can you speak Russian?*",
])
h.retell("WATCH OUT!", "DIQQAT — KOʻP UCHRAYDIGAN XATOLAR", [
    "1 ✗ *Where you live?* → ✓ *Where do you live?* — egadan oldin *do / does / did*.",
    "2 ✗ *Do you are married?* → ✓ *Are you married?* — *be* bilan *do* ishlatilmaydi.",
    "3 ✗ *Does she works in a bank?* → ✓ *Does she work …?* — *does* dan keyin *-s* yoʻq.",
    "4 ✗ *What means “rude”?* → ✓ *What does “rude” mean?*",
    "5 ✗ *How many money do you earn?* → ✓ *How much money …?* — *money* sanalmaydi.",
])
h.retell("WORD FAMILIES", "SOʻZ OILALARI", [
    "**bore** → **boring** (zeriktiradigan narsa: film, nutq) · **bored** (siz his qiladigan narsa — zerikkan): "
    "*The speech was boring, so I was bored.*",
    "**strange** → **a stranger** (notanish odam) · **rude** → **rudely**, **rudeness** · **serious** → "
    "**seriously** · **beautiful** → **beauty** · **amaze** → **amazing** · **amazed**",
])
h.retell("ERROR WARNING", "DIQQAT — SIFATLARDAGI XATOLAR", [
    "✗ *The plov was very delicious.* → ✓ *really delicious* — *very* kuchli sifatlar bilan ishlatilmaydi: "
    "*amazing, awful, delicious, gorgeous, perfect …*",
    "✗ *I'm boring at long parties.* → ✓ *I'm bored* · ✗ *It was a very perfect day.* → ✓ *a perfect day*",
    "✗ *My brother is very beautiful.* → ✓ *good-looking / handsome* (erkaklar haqida) · ✗ *He asked me a "
    "rude.* → ✓ *a rude question*",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [                 # the first of the two
    "Darslikdagi **1.01-trek**ni tinglang (1-unit, 1A dars). Ana tugʻilgan kunini nishonlamoqda: birinchi marta "
    "tanishayotgan mehmonlarning uchta suhbatini eshitasiz.",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — SALOMLASHISH VA XAYRLASHISH", [
    "[[A]] **Tanish odam bilan salomlashish:** *Long time no see! · How are you? · Great to see you! · Where are "
    "you living these days?* Javob: *I'm great, thanks. How are you? · Lovely to see you, too.*",
    "[[B]] **Yangi odam bilan tanishish:** *My name's Mark, by the way.* — *Hi. Nice to meet you.* — *Nice to meet "
    "you, too.*",
    "[[C]] **Qiziqish bildirish:** **What a** + sifat + ot (*What a lovely surprise!*) · **How** + sifat (*How "
    "nice!*) · **That's** + sifat (+ ot) (*That's fantastic news!*) · *Oh, that's good.* Istisno: ot boʻlmasa, "
    "*What* emas, **How**: *How lovely!* — *What lovely!* emas.",
    "[[D]] **Suhbatni tugatish:** *(Anyway,) we really must go. · It was really nice to meet you. · It was great "
    "to see you again. · We must meet up soon! · Say hello to Dan for me!*",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [
    "Enni koʻchada eski dugonasi Reychel va uning eri Mark bilan uchrashib qoladi: **1.14-trek**ni tinglang "
    "(1-qism). Keyin ular kafega borishadi va Ennining yigiti Leo bilan tanishishadi: **1.19-trek**ni tinglang "
    "(2-qism). Darslik, 1-unit, 1C dars.",
])

# --------------------- the goals, in Uzbek, where the site's cover reads them
GOALS = [
    "notanish odam bilan suhbat boshlash va uni davom ettirishni",
    "savollarni toʻgʻri tuzishni: *be*, *do / does / did*, *What … like?*, oxirida predlog",
    "odamlar, ovqat va kunlarni sifatlar bilan tasvirlashni — *boring* va *bored* farqi bilan",
    "bazmdagi va kafedagi suhbatlarni tushunishni",
    "salomlashish, qiziqish bildirish va suhbatni xushmuomalalik bilan tugatishni",
    "oʻz fikringizni uch xatboshida yozishni",
]
first_bar = bh_section_at().search(h.html).start()
h.html = (h.html[:first_bar] + '<table class="bk"><tr><td><p><span>You will learn to</span></p>'
          + "".join('<p><span>—  </span>%s</p>' % told(g, bare=True) for g in GOALS)
          + "</td></tr></table>" + h.html[first_bar:])

# ------------------------------------------------------------------ the key
K = {}
TF = {"T": "T · true", "F": "F · false"}
TFNG = ["TRUE", "FALSE", "NOT GIVEN"]
ROMAN = ["i", "ii", "iii", "iv", "v", "vi", "vii"]
K[("1.1", 1, 1)] = own()
for n, a in enumerate(["ii", "iv", "i", "v", "vi"], 1):
    K[("1.2", n, 1)] = choose(ROMAN, a)
for n, a in enumerate(["FALSE", "FALSE", "TRUE", "FALSE", "NOT GIVEN", "FALSE", "NOT GIVEN", "TRUE"], 1):
    K[("1.3", n, 1)] = choose(TFNG, a)
for n, a in enumerate(["Chicago", "silence", ok("awkward", "very awkward"), ok("pleasant", "more pleasant"), "2018",
                       ok("liking gap", "the liking gap", "liking-gap")], 1):
    K[("1.4", n, 1)] = Q(a)
K[("1.5", 1, 1)] = own()

for n, a in enumerate([ok("Where are you from"), ok("How did you meet Ana"), ok("What does your brother do"),
                       ok("What was the food like"), ok("Does she live near here"), ok("Why were you late")], 1):
    K[("2.1", n, 1)] = write(a)
for n, a in enumerate(["did", "Do", "was", "Is", "does", "Were", "are", "did"], 1):
    K[("2.2", n, 1)] = Q(a)
for n, (opts, a) in enumerate([(["How much", "How many"], "How many"), (["Who", "Whose"], "Whose"),
                               (["How often", "How much"], "How often"),
                               (["What kind of", "Which kind"], "What kind of"),
                               (["How much", "How many"], "How much"), (["What", "Which"], "Which")], 1):
    K[("2.3", n, 1)] = choose(opts, a)
for n, a in enumerate([ok("How do you know the bride"), ok("What do you do", "What's your job", "What is your job"),
                       ok("Did you come by car", "Did you come here by car"),
                       ok("Does your brother speak English"), ok("Who do you live with")], 1):
    K[("2.4", n, 1)] = write(a)
K[("2.5", 1, 1)] = own()
K[("2.5", 2, 1)] = own()
for n, a in enumerate([either("What's your new teacher like", "What is your new teacher like"),
                       "Do you like basketball",
                       either("What was the weather like in Samarkand", "What's the weather like in Samarkand",
                              "What is the weather like in Samarkand")], 1):
    K[("2.6", n, 1)] = write(a)
FIXED = [either("Where are you from"),
         either("Are you a student", "Are you a student at the university", "Are you a student at the university too"),
         either("What does night owl mean", "What does “night owl” mean", 'What does "night owl" mean',
                "What does 'night owl' mean"),
         either("Does your family live", "Does your family live in Tashkent"),
         either("how much money", "how much money do we pay", "how much money do we pay for the internet",
                "And how much money do we pay for the internet")]
for n, a in enumerate(FIXED, 1):
    K[("2.7", n, 1)] = None                       # the mistake as they found it: theirs, not marked
    K[("2.7", n, 2)] = write(a, control=None)
for n in range(1, 6):
    K[("2.9", n, 1)] = own()

GROUPS = ["very good", "OK", "bad", "how people act"]
GROUP_OF = {"wonderful": "very good", "perfect": "very good", "amazing": "very good", "gorgeous": "very good",
            "delicious": "very good", "all right": "OK", "beautiful": "very good", "lovely": "very good",
            "awful": "bad", "horrible": "bad", "rude": "how people act", "boring": either("bad", "how people act"),
            "silly": "how people act", "serious": either("how people act", "bad"),
            "strange": either("how people act", "bad"), "ugly": "bad"}
for n, w in enumerate(ADJ, 1):
    K[("3.2", n, 1)] = choose(GROUPS, GROUP_OF[w])
for n, (full, rest) in enumerate([("rude", "ude"), ("silly", "illy"), ("delicious", "elicious"),
                                  ("strange", "trange"), ("awful", "wful"), ("serious", "erious"),
                                  ("gorgeous", "orgeous"), ("perfect", "erfect"), ("lovely", "ovely"),
                                  ("ugly", "gly")], 1):
    K[("3.3", n, 1)] = Q(either(full, rest))
K[("3.3", 11, 1)] = own()
PATTERNS = ["●", "●•", "•●", "●••", "•●•"]
STRESS = {"all right": "•●", "amazing": "•●•", "awful": "●•", "boring": "●•", "delicious": "•●•",
          "gorgeous": "●•", "horrible": "●••", "lovely": "●•", "perfect": "●•", "serious": "●••",
          "silly": "●•", "strange": "●", "ugly": "●•"}
for n, w in enumerate(STRESSED, 1):
    K[("3.4", n, 1)] = choose(PATTERNS, STRESS[w])
for n, a in enumerate(["boring", "bored", "stranger", "rudely", "amazed"], 1):
    K[("3.5", n, 1)] = Q(a)
K[("3.6", 1, 1)] = own()

for (n, k), a in {(1, 1): "perfect", (2, 1): "delicious", (3, 1): ok("all right", "alright"), (3, 2): "boring",
                  (4, 1): "awful", (5, 1): "strange"}.items():
    K[("4.1", n, k)] = Q(a)
CONV = ["1", "2", "3", "1 & 2", "1 & 3", "2 & 3"]
for n, a in enumerate(["1", "2", "1 & 2", "2", "3", "1"], 1):
    K[("4.2", n, 1)] = choose(CONV, a)
for n, a in enumerate([ok("university", "the university", "uni"), ok("Literature", "English Literature"),
                       ok("next door", "next-door"), ok("river", "the river"), ok("bank", articles=True),
                       ok("earns", "earn"), ok("boring", "a bit boring"),
                       ok("watching films", "films", "watching movies", "movies", "watching a film", "watch films"),
                       "Peru"], 1):
    K[("4.3", n, 1)] = Q(a)
K[("4.4", 1, 1)] = own()
K[("4.4", 2, 1)] = own()

for n, a in enumerate("TFFFFT", 1):
    K[("5.1", n, 1)] = choose(["T", "F"], a, labels=TF)
for n, a in enumerate([either("rugby", "the rugby"), either("florist", "a florist", "she's a florist"),
                       either("a wedding", "to a wedding", "wedding"), "Tina", "marketing",
                       either("her brother", "Dan", "her brother Dan", "her brother, Dan", "brother", "his brother"),
                       either("Leo's", "Leo", "Leo's birthday")], 1):
    K[("5.2", n, 1)] = Q(a)
for n, (w, ge) in enumerate([("see", "G"), ("days", "G"), ("way", "G"), ("go", "E"), ("meet", "E"), ("up", "E"),
                             (ok("hello", "hi"), "E"), ("see", "E")], 1):
    K[("5.3", n, 1)] = Q(w)
    K[("5.3", n, 2)] = choose(["G", "E"], ge, labels={"G": "G · greeting", "E": "E · ending"})
K[("5.4", 1, 1)] = own()
K[("5.4", 2, 1)] = own()
for n, a in enumerate([either("How lovely! I love your new flat", "How lovely", "How lovely. I love your new flat",
                              "How lovely, I love your new flat", "What a lovely flat! I love your new flat",
                              "What a lovely flat"),
                       ok("Say hello to Dan for me", "Say hi to Dan for me"), ok("It was really nice to meet you")], 1):
    K[("5.5", n, 1)] = write(a)
K[("5.6", 1, 1)] = own(control="essay")

for n in range(1, 5):                             # notes, not sentences
    K[("6.1", n, 1)] = None
for n in range(1, 4):                             # the checks before they send the recording
    K[("6.2", n, 1)] = tick()
for n in range(1, 4):
    K[("6.3", n, 1)] = None
K[("6.4", 1, 1)] = own(control="essay")

if __name__ == "__main__":
    data = h.build(K, "Pre-Intermediate", 1, "Unit 1A & 1C — Communicating")
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "p01ac_new.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
