"""P01BD Communication - Azamat's Pre-Intermediate booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(P01BD Communication - answer key), joined box by box by hand. Every
explanation is told again in Uzbek, with the English examples kept, and
every instruction has a line in Uzbek under it; the reading, the texts to
fill in and the exercises stay English.

Put right here, since a page that marks itself cannot be wrong about its
own answers:
  - 2.3 says TWO sentences are correct; the key's note says three, and three
    are (2, 4, 5). The key also ticks 7, "He works in a bank at the moment,
    but it's only for the summer" - but that is temporary, the booklet's own
    rule D, so it wants the continuous: He's working;
  - 3.5 asks whether the bold letters are long or short. The bold in rarely
    (a) and usually (ua) is neither a clear long nor a clear short vowel, so
    either answer is right there;
  - 3.4's "It's especially / a bit cold today": especially cold is good
    English too, so both are right.

What a phone gets that paper does not:
  - taps for every choice: who says it, A/B/C, H/P/N/T, right or wrong,
    stronger or weaker, the eight frequency adverbs in order, the adverb in
    3.4, long or short, the stressed syllable, the speaker's topic, happy or
    unhappy, which speaker, Nina or Chris, U/B/M, the kind of mistake;
  - boxes where paper has none: 1.6's four sentences, 2.3, 3.4, 3.6, 4.2.

    python3 handouts/p01bd_digital.py            # writes handouts/p01bd.json, lists every box
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import (Handout, Q, choose, tick, own, write, fix, report,   # noqa: E402
                     BLANK_TAG, LEADER_P, plain, ITEM_STYLE, NUM_SPAN, TEXT_SPAN)

DOCX = ("~/Desktop/Handouts/B1 Pre-Intermediate/P01BD Communication/"
        "P01BD Communication — handout (new design).docx")
W = "95%"
YES_NO = ["✓", "✗"]

h = Handout(DOCX)
TAGS = {int(m.group(1)): m.group(0) for m in BLANK_TAG.finditer(h.html)}


def section(label):
    """Where an exercise begins."""
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


def ruled_to_boxes(label, until, boxes):
    """Paper's ruled lines go, and `boxes` come under the instruction - for a
    task that wants more answers than it has lines."""
    head = section(label)
    tail = h.html.index(until, head)
    h.html = h.html[:head] + LEADER_P.sub("", h.html[head:tail]) + h.html[tail:]
    h.after_instruction(label, boxes)


def either(*forms):
    return "/".join(forms)


# ------------------------------------------------------------ 1 Reading
h.options_on_lines("1.3")
for n in range(1, 5):
    h.item_box("1.3", n, where="options")
for n in range(1, 5):
    h.item_box("1.4", n, width="190px", where="leader")
for n in range(1, 5):
    h.item_box("1.5", n, where="leader")
ruled_to_boxes("1.6", "2  </span>", [(n, "", W, "Sentence %d" % n) for n in range(1, 5)])

# ------------------------------------------------------------ 2 Grammar
# 2.3: three sentences are correct, not two
a = section("2.3")
b = h.html.index("</p>", a)
h.html = h.html[:a] + h.html[a:b].replace("TWO", "THREE", 1) + h.html[b:]
for n in range(2, 9):                             # item 1 is the worked example
    h.item_box("2.3", n)

# ------------------------------------------------------------ 3 Vocabulary
# 3.2: the eight places on the line, one to a row, each with the eight adverbs
PLACES = ["100%", "", "", "", "", "", "", "0%"]
rows = "".join(item_p("3.2", n, "%s place%s" % (["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th"][n - 1],
                                                   " (%s)" % PLACES[n - 1] if PLACES[n - 1] else ""),
                      "{{box:3.2:%d:60px:}}" % n) for n in range(1, 9))
at = section("3.2")
first = h.html.index('<table class="bk">', at)
a = h.html.index('<table class="bk">', h.html.index("</table>", first))
b = h.html.index("</table>", a) + len("</table>")
h.html = h.html[:a] + rows + h.html[b:]
PAIRS34 = {1: ["absolutely", "quite"], 2: ["absolutely", "pretty"], 3: ["really", "a bit"],
           4: ["completely", "fairly"], 5: ["totally", "slightly"], 6: ["especially", "a bit"]}
for n in PAIRS34:
    h.item_box("3.4", n)
SYLL = {}
for m in h._items("3.6"):                         # the syllables are the choice
    n = int(m.group(3))
    SYLL[n] = re.split(r"[-\s]+", re.sub(r"^\d+\s+", "", plain(m.group(4))))
for n in sorted(SYLL):
    h.item_box("3.6", n)

# ------------------------------------------------------------ 4 Listening
# 4.2: the topics first, as a key; then each speaker, with a-d to tap
old = replace_table_after("4.2", "{{4.2}}")
cells = [plain(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", old, re.S)]
pairs = [(cells[k], cells[k + 1]) for k in range(2, len(cells) - 1, 2)]
speakers = [re.match(r"(\d+)\s+(.*)", s).groups() for s, _t in pairs]
topics = sorted(re.match(r"([a-d])\s+(.*)", t).groups() for _s, t in pairs)
h.html = h.html.replace("{{4.2}}", key_list(topics) + "".join(
    item_p("4.2", int(n), html.escape(s, quote=False), "{{box:4.2:%s:60px:}}" % n) for n, s in speakers))
h.grid_rows("4.3")
h.options_on_lines("4.8")
for n in (1, 2, 3):
    h.item_box("4.8", n)

# ------------------------------------------------------------ 5 Writing
h.leaders("5.1", "5.2  </span>", [(1, "60px", "")])
for n in range(1, 5):
    h.item_box("5.2", n, where="leader")
h.leaders("5.6", "5.7  </span>", [(n, W, "Sentence %d, corrected" % n) for n in range(1, 7)])
for n in range(1, 5):
    h.item_box("5.8", n, where="leader")
h.leaders("5.9", "CHECK BEFORE", [(20, W, "Write your email here")])
h.html = h.html.replace(TAGS[134], "", 1)         # the word count: the box counts them itself

# ------------------------------- every instruction, once more, in Uzbek
for label, text in [
        ("1.1", "Muhokama qiling. Tugʻilgan kun tabriknomalarini yuborasizmi? Qoʻlda xat yozasizmi? Agar yoʻq "
                "boʻlsa, oʻrniga nima qilasiz?"),
        ("1.2", "Buni kim aytadi? *J* (Jin), *Ju* (Julie), *M* (Marc) yoki *G* (Gabriel) ni tanlang."),
        ("1.3", "Eng toʻgʻri javobni tanlang: *A*, *B* yoki *C*."),
        ("1.4", "Matndan shu maʼnodagi soʻz yoki iborani toping."),
        ("1.5", "Savollarga javob bering."),
        ("1.6", "Har bir gapiruvchi bitta present continuous gap ishlatadi. Toʻrttasini ham toping va yozing."),
        ("2.1", "Odatmi (*H*), doimiy holatmi (*P*), aynan hozirmi (*N*) yoki vaqtinchalikmi (*T*)? Tanlang."),
        ("2.2", "Present simple yoki present continuous bilan toʻldiring."),
        ("2.3", "Xatoni topib, toʻgʻrilang. UCHTA gap toʻgʻri — ular uchun *✓ It is correct* tugmasini bosing."),
        ("2.4", "Gaplarni boʻlishsiz shaklga oʻtkazing."),
        ("2.5", "Savollar tuzing."),
        ("2.6", "Holat feʼlimi yoki harakat feʼlimi? Qaysi gaplar notoʻgʻri? *✓* yoki *✗* ni tanlang."),
        ("2.7", "Matnni toʻgʻri shakl bilan toʻldiring."),
        ("2.8", "Suhbatni toʻldiring."),
        ("3.1", "Kuchliroqmi (*S*) yoki kuchsizroqmi (*W*)? Tanlang."),
        ("3.2", "Takrorlanish ravishlarini chiziqqa joylang — 100% dan 0% gacha, tartib bilan."),
        ("3.3", "Ravishni toʻgʻri joyga qoʻyib, gapni qayta yozing."),
        ("3.4", "Toʻgʻri ravishni tanlang."),
        ("3.5", "Qalin harflardagi unli uzunmi (*L*) yoki qisqami (*S*)? Tanlang."),
        ("3.6", "Soʻz urgʻusi. Urgʻuli boʻgʻinni tanlang, keyin soʻzni ovoz chiqarib ayting."),
        ("3.7", "Matnni ravishlar bilan toʻldiring."),
        ("4.1", "Tinglashdan oldin taxmin qiling. Bulardan qaysilari haqida gap boradi deb oʻylaysiz? Belgilang."),
        ("4.2", "Bir marta tinglang. Har bir gapiruvchini mavzusi bilan moslang: harfni tanlang."),
        ("4.3", "Yana tinglang. Texnologiyadan xursandmi (☺) yoki norozimi (☹)? Nega?"),
        ("4.4", "Yana bir marta tinglang va har bir qatorni eshitgan ravishingiz bilan toʻldiring."),
        ("4.5", "Tinglang va nima boʻlishiga eʼtibor bering."),
        ("4.6", "Har bir iborani ikki marta ayting — avval sekin, keyin tez."),
        ("4.7", "Buni qaysi gapiruvchi aytishi mumkin? Ismni tanlang."),
        ("4.8", "Gapiruvchi nima demoqchi? *A* yoki *B* ni tanlang."),
        ("5.1", "Tinglang. Kim aloqani yaxshiroq saqlaydi — Nina yoki Chris?"),
        ("5.2", "Yana tinglang va javob bering."),
        ("5.3", "Bu xabar iboralari nimani anglatadi? Oʻz soʻzlaringiz bilan yozing."),
        ("5.4", "Simon buni kimga yozadi? *U* (amakisi va uning rafiqasi), *B* (Blake) yoki *M* (Mika)?"),
        ("5.5", "Xatolarni toping. Har biri qanday xato — bosh harf, tinish belgisi, grammatika yoki imlo?"),
        ("5.6", "Endi 5.5 dagi har bir gapni toʻgʻri yozing."),
        ("5.7", "Namunaviy emailni oʻqing. Keyin savollarga javob bering."),
        ("5.8", "Namuna haqidagi savollarga javob bering."),
        ("5.9", "Oʻz emailingizni yozing (100–120 soʻz). Siz qayerdadir safardasiz va rasmlar yuboryapsiz.")]:
    h.say_also(label, text)

# ------------------------------------------ the explanations, told in Uzbek
h.goals([
    "qanday muloqot qilishingiz haqida gapirishni",
    "*present simple* va *present continuous* orasida toʻgʻri tanlashni",
    "daraja va takrorlanish ravishlarini toʻgʻri joyda ishlatishni",
    "texnologiya haqida fikr bildirayotgan odamlarni tushunishni",
    "shaxsiy email yozishni — va oʻz xatolaringizni topishni",
])
h.retell("KEY WORDS", "KALIT SOʻZLAR", [
    "**to keep in touch**  aloqada boʻlmoq, aloqani uzmaslik",
    "**a feed**  ilovada koʻradigan postlaringiz roʻyxati (lenta)",
    "**to cancel**  rejani bekor qilmoq",
    "**a follower**  postlaringizni oʻqib boradigan odam (obunachi)",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — PRESENT SIMPLE VA PRESENT CONTINUOUS", [
    "Ikkala zamon ham hozirgi vaqt haqida gapiradi. Farqi — vaziyat qancha davom etishida.",
    "[[A]] **Present simple — odatlar va kundalik ishlar.** *I send a text when I plan something. · She calls "
    "her mother every Sunday.*",
    "[[B]] **Present simple — his-tuygʻular va doimiy holatlar.** *I like putting photos on my blog. · He lives "
    "in Tashkent.*",
    "[[C]] **Present continuous — aynan hozir boʻlayotgan ish.** *I'm waiting for her text. · Listen — "
    "somebody's calling you.*",
    "[[D]] **Present continuous — shu kunlardagi vaqtinchalik ish.** *She's writing a blog this year. · I'm "
    "living in Canada at the moment.*",
    "**Odatda continuous shaklda ishlatilmaydigan feʼllar:** *like · love · hate · prefer · want · need · know · "
    "understand · believe · mean · seem*. *I know him* deng, hech qachon *I am knowing him* emas.",
])
h.retell("ERROR WARNING", "DIQQAT — ZAMONLARDAGI XATOLAR", [
    "Uchta narsa notoʻgʻri ketadi, uchinchisi esa eng uzoq saqlanib qoladigani:",
    "1 **Odat uchun continuous.** ✗ *I am usually texting my friends.* → ✓ *I usually text my friends.*",
    "2 **Aynan hozirgi ish uchun simple.** ✗ *Wait — I wait for her message.* → ✓ *I'm waiting for her "
    "message.*",
    "3 **Holat feʼli continuous shaklda.** ✗ *I am knowing him for two years.* → ✓ *I've known him for two "
    "years.* · ✗ *I am wanting a coffee.* → ✓ *I want a coffee.*",
    "Yana bitta kichik xato: ✗ *She's living in Almaty since 2020.* — *since* va *for* bilan boshqa zamon kerak. "
    "Continuous ni *this year, at the moment, this week* uchun saqlang.",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — RAVISHLAR", [
    "Ikki xil ravish, ikki xil vazifa.",
    "[[A]] **Daraja ravishlari — kuchliroq:** *really · especially · particularly · absolutely · completely · "
    "totally* · *I absolutely hate it. · It's especially useful.*",
    "[[B]] **Daraja ravishlari — kuchsizroq:** *quite · pretty · fairly · a bit · slightly* · *I'm quite shy. · "
    "It's pretty hot here.*",
    "[[C]] **Takrorlanish ravishlari:** *always* (100%) *· normally · usually · often · sometimes · rarely · "
    "hardly ever · never* (0%)",
    "[[D]] **Qayerga qoʻyiladi:** asosiy feʼldan oldin — *I rarely call.* · *be* dan keyin — *She's always "
    "late.* · *always* va *never* odatda gap boshida kelmaydi.",
    "**Ehtiyot boʻling:** *absolutely · completely · totally* kuchli soʻzlar bilan keladi — *absolutely hate* "
    "deyiladi, *absolutely like* emas.",
])
h.retell("PRONUNCIATION", "TALAFFUZ", [
    "Uzun yoki qisqa unli? Yozilishi oʻxshash, lekin aytilishi farq qiladi:",
    "[[QISQA]] *cancel · blog · sometimes · rarely* (birinchi tovush)",
    "[[UZUN]] *really · write · photos · usually*",
    "**Uzun ravishlardagi urgʻu:** *esPEcially · parTICularly · ABsolutely · NORmally · HARDly ever*",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [
    "Toʻrt kishi qanday qilib aloqada boʻlishi haqida gapiradi. Ularning baʼzilari texnologiyadan xursand, "
    "baʼzilari esa yoʻq.",
    "Agar sinfingizda audio boʻlsa, bu 01.04-trek. Boʻlmasa, oʻqituvchingiz matnni oʻqib beradi — topshiriqlar "
    "bir xil.",
])
h.retell("WHY YOU DIDN'T HEAR IT", "NEGA ESHITMADINGIZ?", [
    "**Tez nutqda uzun ravishlar ezilib ketadi.** *Especially* /speʃli/ ga aylanadi — toʻrt emas, uch boʻgʻin. "
    "*Particularly* /pətɪkjəli/ boʻladi. *Absolutely* urgʻuni birinchi boʻgʻinda saqlaydi, lekin oʻrtasi "
    "yoʻqoladi: /æbsəluːtli/. Urgʻuli boʻgʻin qoladi, atrofidagi hamma narsa tushib qoladi.",
])
h.retell("LISTENING INTO WRITING", "TINGLASHDAN YOZISHGA", [
    "Avval doʻstlar va oila bilan aloqada boʻlish haqida gaplashayotgan ikki kishini tinglang. Ulardan biri bu "
    "ishda ikkinchisidan ancha yaxshi. Agar sinfingizda audio boʻlsa, bu 01.09-trek.",
])
h.retell("ONE PERSON, THREE EMAILS", "BITTA ODAM, UCHTA EMAIL", [
    "Simon Salamankada oʻqiyapti. U bitta safar haqida uch kishiga yozadi, va har bir email boshqacha:",
    "[[U]] **Amakisi va uning rafiqasiga** — shahar, kurs, ob-havo. *Hope you're both well…* bilan boshlaydi, "
    "*Love to all* bilan tugatadi.",
    "[[B]] **Doʻsti Blakega** — boshqa talabalar, kechqurun birga chiqish, vaqt qanchalik tez oʻtayotgani. "
    "*How's it going?* bilan boshlaydi, *See you back at college* bilan tugatadi.",
    "[[M]] **Singlisi Mikaga** — u yashayotgan oila, ularning qizi, qizning ishi. *Love, Simon xx* bilan "
    "tugatadi.",
])
h.retell("CORRECTING YOUR OWN MISTAKES", "OʻZ XATOLARINGIZNI TOʻGʻRILASH", [
    "Biror narsani yuborishdan oldin uni toʻrt marta oʻqing — har safar faqat bitta narsani qidiring:",
    "1 **Bosh harflar** — ✗ *i'm in salamanca, in spain* → ✓ *I'm in Salamanca, in Spain*",
    "2 **Tinish belgilari** — ✗ *Hope youre both well and are enjoying the Summer* → ✓ *Hope you're both well "
    "and are enjoying the summer.*",
    "3 **Grammatika** — ✗ *She speak English quite good* → ✓ *She speaks English quite well* · ✗ *I having a "
    "great time* → ✓ *I'm having a great time*",
    "4 **Imlo** — ✗ *fotos · corse · diferent · countrys* → ✓ *photos · course · different · countries*",
])
h.retell("CHECK BEFORE YOU HAND IT IN", "TOPSHIRISHDAN OLDIN TEKSHIRING", [
    "{box}  Hozir yoki shu oy boʻlayotgan ishlar uchun ikkita *present continuous* feʼl ishlatdim.   {box}  "
    "Odatlar uchun ikkita *present simple* feʼl ishlatdim.",
    "{box}  Uchta ravish ishlatdim, jumladan bitta takrorlanish ravishini toʻgʻri joyda.   {box}  Emailni oʻsha "
    "odamga yoziladigandek boshladim va tugatdim.",
    "{box}  Bosh harflar tekshirildi.   {box}  Tinish belgilari tekshirildi.   {box}  Grammatika tekshirildi.   "
    "{box}  Imlo tekshirildi.   {box}  Soʻzlar soni: 100–120.",
])
h.one_per_line("TOPSHIRISHDAN OLDIN TEKSHIRING", None, at="box")
h.retell_cells({"Present simple": "Present simple — oddiy hozirgi zamon",
                "Present continuous": "Present continuous — davomli hozirgi zamon",
                "I usually text my friends. (habit)": "<i>I usually text my friends.</i> (odat)",
                "I' m waiting for a reply. (right now)": "<i>I'm waiting for a reply.</i> (aynan hozir)",
                "She lives in Almaty. (permanent)": "<i>She lives in Almaty.</i> (doimiy)",
                "She' s living in Almaty this year. (temporary)":
                    "<i>She's living in Almaty this year.</i> (vaqtinchalik)",
                "I like getting postcards. (feeling)": "<i>I like getting postcards.</i> (his-tuygʻu)",
                "Stronger": "Kuchliroq", "Weaker": "Kuchsizroq"})
h.retell_cells({"What is written": "Yozilishi", "What you hear": "Eshitilishi", "Why": "Nega",
                "the first syllable disappears": "birinchi boʻgʻin yoʻqoladi",
                "five syllables become four": "beshta boʻgʻin toʻrttaga aylanadi",
                "hate it joins into one word": "<i>hate it</i> bitta soʻzdek qoʻshilib ketadi",
                "the two words join": "ikki soʻz qoʻshilib ketadi"},
               after="4.5  </span>")

# ------------------------------------------------------------------ the key
K = {}
WHO = {"J": "J · Jin", "Ju": "Ju · Julie", "M": "M · Marc", "G": "G · Gabriel"}
for n, a in enumerate(["J", "G", "M", "Ju", "M", "G"], 1):
    K[("1.2", n, 1)] = choose(["J", "Ju", "M", "G"], a, labels=WHO)
for n, a in enumerate("BCBB", 1):
    K[("1.3", n, 1)] = choose(["A", "B", "C"], a)
for n, a in enumerate(["to keep in touch/keep in touch/keep in touch with", "a feed/feed/my feed",
                       "to cancel/cancel/cancelling", "a follower/follower/followers"], 1):
    K[("1.4", n, 1)] = Q(a)
for n in range(1, 5):
    K[("1.5", n, 1)] = own()
for n in range(1, 5):                             # the key accepts any four
    K[("1.6", n, 1)] = own()
HPNT = {"H": "H · habit", "P": "P · permanent", "N": "N · right now", "T": "T · temporary"}
for n, a in zip(range(2, 7), "NPTPN"):          # 2 waiting 3 lives 4 blog this year 5 hate 6 calling
    K[("2.1", n, 1)] = choose(["H", "P", "N", "T"], a, labels=HPNT)
for key, a in (((1, 1), "check"), ((2, 1), either("am waiting", "'m waiting")),
               ((3, 1), either("is living", "'s living")), ((4, 1), either("doesn't like", "does not like")),
               ((5, 1), "are"), ((5, 2), "doing"), ((6, 1), "make"),
               ((7, 1), either("is writing", "'s writing")), ((7, 2), either("is travelling", "'s travelling",
                                                                             "is traveling", "'s traveling")),
               ((8, 1), "Do"), ((8, 2), "know")):
    K[("2.2",) + key] = Q(a)
TICKED = "✓/correct/tick"


def calling():
    out = []
    for verb in ("somebody's calling you", "somebody is calling you", "someone's calling you",
                 "someone is calling you"):
        out += ["Listen — " + verb, "Listen - " + verb, "Listen – " + verb, "Listen, " + verb,
                "Listen " + verb, verb]
    return either(*out)


for n, a in zip(range(2, 9), [
        TICKED,
        either("I've known him for two years", "I have known him for two years"),
        TICKED,
        TICKED,
        either("I want a coffee"),
        either(*[s + rest for s in ("He's working in a bank at the moment", "He is working in a bank at the moment")
                 for rest in ("", ", but it's only for the summer", " but it's only for the summer")]),
        calling()]):
    K[("2.3", n, 1)] = fix(a)
for n, a in enumerate([
        either("I'm not waiting for a reply", "I am not waiting for a reply"),
        either("She doesn't write a blog every week", "She does not write a blog every week"),
        either("They aren't staying with a Spanish family", "They're not staying with a Spanish family",
               "They are not staying with a Spanish family"),
        either("He doesn't like video calls", "He does not like video calls")], 1):
    K[("2.4", n, 1)] = write(a)
for n, a in enumerate(["How often do you send postcards", "What are you reading at the moment",
                       "Does your sister live in Tashkent", "Why is he writing a blog this year"], 1):
    K[("2.5", n, 1)] = write(a)
RW = {"✓": "✓ right", "✗": "✗ wrong"}
for n, a in enumerate(["✗", "✓", "✗", "✓", "✗", "✓"], 1):   # knowing, learning, wanting, looking, understanding, studying
    K[("2.6", n, 1)] = choose(YES_NO, a, labels=RW)
for n, a in enumerate([either("am living", "'m living"), either("isn't", "is not", "'s not"), "send",
                       either("am writing", "'m writing"), "take", "emails", "asks",
                       either("is waiting", "'s waiting")], 1):
    K[("2.7", n, 1)] = Q(a)
for n, a in enumerate(["are you doing", either("am waiting", "'m waiting"), "Do you want",
                       either("am going", "'m going"), either("don't think", "do not think"), "usually work",
                       either("am doing", "'m doing")], 1):
    K[("2.8", n, 1)] = Q(a)
SW = {"S": "S · stronger", "W": "W · weaker"}
for n, a in zip(range(2, 9), "WSWSWSW"):        # quite, absolutely, a bit, particularly, pretty, especially, fairly
    K[("3.1", n, 1)] = choose(["S", "W"], a, labels=SW)
FREQ = ["always", "normally", "usually", "often", "sometimes", "rarely", "hardly ever", "never"]
for n, a in enumerate(["always", "normally/usually", "usually/normally", "often", "sometimes", "rarely",
                       "hardly ever", "never"], 1):
    K[("3.2", n, 1)] = choose(FREQ, a)
for n, a in enumerate(["I rarely call my grandmother",
                       either("She is always late for everything", "She's always late for everything"),
                       "We hardly ever send postcards", "I particularly enjoy getting letters",
                       either("He is quite shy", "He's quite shy")], 1):
    K[("3.3", n, 1)] = write(a)
for n, a in enumerate(["absolutely", "pretty", "really", "completely", "totally", "a bit/especially"], 1):
    K[("3.4", n, 1)] = choose(PAIRS34[n], a)
LS = {"L": "L · long", "S": "S · short"}
# as numbered: 1 cancel 2 really 3 blog 4 write 5 sometimes 6 photos 7 rarely 8 usually
for n, a in enumerate(["S", "L", "S", "L", "S", "L", "L/S", "L/S"], 1):
    K[("3.5", n, 1)] = choose(["L", "S"], a, labels=LS)
STRESS = {"especially": "pe", "particularly": "tic", "absolutely": "ab", "normally": "nor", "hardlyever": "hard",
          "usually": "u"}
for n, syll in SYLL.items():
    K[("3.6", n, 1)] = choose(syll, STRESS["".join(syll)])
for n in range(1, 7):                             # the key gives samples: his to read
    K[("3.7", n, 1)] = own(control=None)
for n in range(1, 7):                             # what they expect: nothing to mark
    K[("4.1", n, 1)] = tick()
for n, a in enumerate("cdab", 1):                 # Tara, Magda, Chris, Mike
    K[("4.2", n, 1)] = choose([l for l, _t in topics], a)
FACE = {"☺": "☺ happy", "☹": "☹ unhappy"}
for n, a in enumerate(["☺", "☹", "☺", "☺/☹"]):   # Tara, Magda, Chris, Mike - either, with a reason
    K[("4.3", 2 * n + 1, 1)] = choose(["☺", "☹"], a, labels=FACE)
    K[("4.3", 2 * n + 2, 1)] = own()
for n, a in enumerate(["hardly", "especially", "absolutely", "much/far", "really", "never"], 1):
    K[("4.4", n, 1)] = Q(a)
NAMES = ["Tara", "Magda", "Chris", "Mike"]
for n, a in enumerate(NAMES, 1):
    K[("4.7", n, 1)] = choose(NAMES, a)
for n, a in enumerate("BBA", 1):
    K[("4.8", n, 1)] = choose(["A", "B"], a)
K[("5.1", 1, 1)] = choose(["Nina", "Chris"], "Chris")
for n in range(1, 5):
    K[("5.2", n, 1)] = own()
for n in range(1, 5):                             # what each means, in their words
    K[("5.3", n, 1)] = own()
UBM = {"U": "U · uncle and aunt", "B": "B · Blake", "M": "M · Mika"}
for n, a in enumerate("MUBUBM", 1):
    K[("5.4", n, 1)] = choose(["U", "B", "M"], a, labels=UBM)
KINDS = ["capitals", "punctuation", "grammar", "spelling"]
for n, a in enumerate(["punctuation/capitals", "capitals", "grammar", "grammar", "spelling", "spelling"], 1):
    K[("5.5", n, 1)] = choose(KINDS, a)
K[("5.6", 1, 1)] = write(either("Hope you're both well and are enjoying the summer"))
# 2 is only capitals, and a box does not see capitals: his to read
K[("5.6", 2, 1)] = own()
K[("5.6", 3, 1)] = write(either("I'm having a great time here, and the time's going much too quickly",
                                "I am having a great time here, and the time's going much too quickly",
                                "I'm having a great time here, and the time is going much too quickly",
                                "I am having a great time here, and the time is going much too quickly"))
K[("5.6", 4, 1)] = write(either(*[a + b + c for a in ("She speaks English quite well",)
                                  for b in (", but we usually speak Spanish", " but we usually speak Spanish")
                                  for c in ("", " together")]))
K[("5.6", 5, 1)] = write("Here are some photos of my group on the Spanish course")
K[("5.6", 6, 1)] = write(either("We're all from different countries", "We are all from different countries"))
for n in range(1, 5):
    K[("5.8", n, 1)] = own()
K[("5.9", 20, 1)] = own(control="essay")
for n in range(1, 10):                            # the checklist
    K[("5.9", n, 1)] = tick()

if __name__ == "__main__":
    data = h.build(K, "Pre-Intermediate", 1, "Unit 1B & 1D — Communication")
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "p01bd.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
