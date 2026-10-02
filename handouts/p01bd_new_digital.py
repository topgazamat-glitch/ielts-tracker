"""P01BD Communicating - the new-style Pre-Intermediate booklet (1B & 1D), done on a phone.

It replaces "Unit 1B & 1D - Communication" (test 88, p01bd_digital.py), whose
booklet was the older design; the exercises are all new, so no answers carry
across. Built like p01ac_new_digital.py and b04b_digital.py: a TEAL build of
the booklet (BOOK_THEME=teal node build_p01bd.js, in the Material Bank's
"B1 Pre-intermediate/_NEW BOOKLET STYLE/digital source/"), with the one-cell
tables that keep an exercise on one page of paper taken away.

Every explanation is told again in Uzbek (English examples kept) and every
instruction has a line in Uzbek; the reading, the model email and the
exercises stay English. The key is his (P01BD Communicating - ANSWER KEY).

What a phone gets that paper does not:
  - taps: TRUE / FALSE / NOT GIVEN (1.3), why the verb form (2.1), the
    option in 2.2 and 3.3, long or short vowel (3.5, a line per word instead
    of the table), happy or unhappy (4.2), Chris or Nina (4.6), the
    paragraph (5.1), the kind of mistake (5.3), the checks before sending the
    recording (4.8);
  - 2.4: "It is correct" for the right sentences, a box for the wrong ones;
  - 2.7: the mistake as found (not marked), then the correction (marked);
  - 5.3: the kind of mistake, then the correction - a correction that is only
    a capital letter (1) or a question mark (2) is the teacher's to mark, since
    the marking forgives case and full stops and would pass it unchanged.

    python3 handouts/p01bd_new_digital.py       # writes handouts/p01bd_new.json, lists every box
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import (Handout, Q, choose, tick, own, write, fix, report,   # noqa: E402
                     plain, told, bh_section_at, ITEM_STYLE, NUM_SPAN, TEXT_SPAN)
from variants import ok   # noqa: E402

DOCX = ("~/Documents/Claude/Material Bank/General English/B1 Pre-intermediate/_NEW BOOKLET STYLE/digital source/"
        "P01BD Communicating — BOOKLET (teal, for the website).docx")
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
    the choices to tap; anything between the instruction and the table (the
    list of words) goes too. words: [(plain word, markup to show)]"""
    a = h._instruction_end(label)
    t = h.html.index('<table class="bk">', a)
    b = h.html.index("</table>", t) + len("</table>")
    rows = ""
    for n, (word, shown) in enumerate(words, 1):
        h.texts[(label, n)] = word
        rows += ('<p data-item="%s:%d" %s>%s%s</p>'
                 % (label, n, ITEM_STYLE, NUM_SPAN % n,
                    TEXT_SPAN % ("%s  {{box:%s:%d:60px:}}" % (shown, label, n))))
    h.html = h.html[:a] + rows + h.html[b:]


def bold_letters(word, letters):
    i = word.index(letters)
    return '%s<span style="font-weight:700">%s</span>%s' % (word[:i], letters, word[i + len(letters):])


# ------------------------------------------------------------ 1 Reading
for n in range(1, 8):
    h.item_box("1.3", n, where="leader")
h.leaders("1.5", "Grammar  ·", [(1, W, "Your answer")])

# ------------------------------------------------------------ 2 Grammar
for n in range(1, 9):
    h.item_box("2.2", n)
for n in range(1, 7):
    h.item_box("2.4", n, where="leader")
h.leaders("2.5", "2.6  </span>", [(1, W, "Two sentences with these days")])
h.leaders("2.6", "2.7  </span>", [(n, W, "The question") for n in range(1, 5)])
h.leaders("2.9", "Vocabulary  ·", [(1, W, "Your usual week - two sentences"),
                                    (2, W, "This week or this month - two sentences")])

# ------------------------------------------------------------ 3 Vocabulary
for n in range(1, 7):
    h.item_box("3.3", n)
h.leaders("3.4", "3.5  </span>", [(n, W, "The sentence") for n in range(1, 4)])
VOWELS = [("rarely", "a"), ("cancel", "a"), ("really", "ea"), ("especially", "e"), ("write", "i"),
          ("particularly", "i"), ("photos", "o"), ("blog", "o"), ("usually", "u"), ("sometimes", "o")]
reword("3.5", "Long or short vowel? Say each word and listen to the letters in bold. Write the word in the correct "
              "column. (Listen to track 1.10 to check, then repeat the sentences on track 1.11.)",
       "Long or short vowel? Say each word and listen to the letters in **bold**. Tap **long** (as in *see, two, "
       "go, my*) or **short** (as in *sit, hot, cup, red*). (Listen to **track 1.10** to check, then repeat the "
       "sentences on **track 1.11**.)")
taps_instead_of_table("3.5", [(w, bold_letters(w, l)) for w, l in VOWELS])
h.leaders("3.7", "Listening and speaking  ·", [(1, W, "Three sentences")])

# ------------------------------------------------- 4 Listening and speaking
h.leaders("4.4", "4.5  </span>", [(1, W, "Your example and reason")])
for n in range(1, 5):
    h.item_box("4.6", n, width="220px", where="leader")

# ------------------------------------------------------------ 5 Writing
h.leaders("5.2", "5.3  </span>", [(1, W, "What you found")])
for n in range(1, 9):
    h.item_box("5.3", n, where="leader")
    h.item_box("5.3", n, width="95%", placeholder="The correction")
h.leaders("5.6", "5.7  </span>", [(1, W, "Paragraph 2")])
h.leaders("5.7", "</div>", [(1, W, "Write your email here")])

# ------------------------------- every instruction, once more, in Uzbek
for label, text in [
        ("1.1", "Oʻqishdan oldin. Kecha nechta xabar yubordingiz? Kimlarga?"),
        ("1.2", "Vaqt jadvalini toʻldiring. Matndan yil, ism yoki BITTA SOʻZ yozing."),
        ("1.3", "Gaplar matnga mos keladimi? *TRUE* (toʻgʻri), *FALSE* (notoʻgʻri) yoki *NOT GIVEN* (matnda bu "
                "haqda hech narsa yoʻq) ni tanlang."),
        ("1.4", "Koʻrsatilgan xatboshidan shu maʼnodagi soʻz yoki iborani toping."),
        ("1.5", "Dalil haqida oʻylang. F xatboshida ijtimoiy tarmoqlar bu sonlarni oʻzgartirmagani aytilgan. Buni "
                "kim aytyapti va u qayerdan biladi? Nega bu «Internetda 500 ta doʻstim bor!» degan doʻstning "
                "gapidan kuchliroq dalil?"),
        ("2.1", "Muallif nega shu feʼl shaklini ishlatgan? *H* (odat yoki kundalik ish), *P* (doimiy holat yoki "
                "his), *N* (hozir boʻlayotgan) yoki *T* (vaqtinchalik, shu kunlarda) ni tanlang."),
        ("2.2", "Toʻgʻri variantni tanlang."),
        ("2.3", "Madina buvisi uchun ovozli xabar yozib olyapti. Qavsdagi feʼllarni Present Simple yoki Present "
                "Continuous shaklida qoʻyib, xabarni toʻldiring."),
        ("2.4", "Toʻgʻri gaplar uchun *✓ It is correct* tugmasini bosing. Notoʻgʻrilarini toʻgʻrilab yozing."),
        ("2.5", "Oʻylang. Oilangizning aloqa qilish usuli qanday oʻzgaryapti? *these days* bilan ikkita gap yozing."),
        ("2.6", "Savollarni Present Simple yoki Present Continuous shaklida yozing."),
        ("2.7", "Boburning xabarida BESHTA xato bor. Avval xatoni, keyin toʻgʻrisini yozing."),
        ("2.8", "*-ing* shaklini yozing."),
        ("2.9", "Endi siz. Odatdagi haftangiz haqida ikkita gap (Present Simple) va shu hafta yoki shu oy haqida "
                "ikkita gap (Present Continuous) yozing."),
        ("3.1", "Jasurning postini oʻqing. Qalin yozilgan ravishlarga qarang."),
        ("3.2", "Qanchalik tez-tez? Shkalani postdagi ravishlar bilan toʻldiring."),
        ("3.3", "Yaxshiroq ravishni tanlang."),
        ("3.4", "Ravishni toʻgʻri joyga qoʻyib, gapni yozing."),
        ("3.5", "Choʻziq unlimi (*long*) yoki qisqa unlimi (*short*)? Har bir soʻzni ayting, qalin harflarga quloq "
                "soling va tanlang. Tekshirish uchun 1.10-trekni tinglang, keyin 1.11-trekdagi gaplarni takrorlang."),
        ("3.6", "*keep*, *get*, *lose*, *hear* yoki *into* ni toʻgʻri shaklda qoʻyib, toʻldiring."),
        ("3.7", "Oʻylang. Qanday aloqada boʻlishingiz haqida bu boʻlimdagi uchta har xil ravish bilan uchta rost gap "
                "yozing."),
        ("4.1", "Jadvalni toʻldiring. Har bir javobga IKKI SOʻZDAN KOʻP yozmang."),
        ("4.2", "Texnologiya muloqotni oʻzgartirayotganidan kim mamnun? *H* (mamnun) yoki *U* (mamnun emas) ni "
                "tanlang."),
        ("4.3", "Qavsdagi feʼllar bilan gapiruvchilarning gaplarini toʻldiring. Keyin tekshirish uchun yana tinglang."),
        ("4.4", "Oʻylang. SMS biror narsani aytishning notoʻgʻri usuli boʻlishi mumkinmi? Misol va sabab keltiring."),
        ("4.5", "Qanchalik tez-tez? Eshitgan ravish yoki iborangiz bilan jadvalni toʻldiring."),
        ("4.6", "Savollarga javob bering. Har bir javobga TOʻRT SOʻZDAN KOʻP yozmang."),
        ("4.7", "Har bir band uchun qayd yozing. Faqat qaydlar — toʻliq gaplar emas."),
        ("4.8", "Oʻzingizni yozib oling. Taxminan bir daqiqa gapiring: qaydlaringiz, 3-boʻlimdagi ikkita ravish va u "
                "odam shu kunlarda nima qilayotgani haqida bitta gapdan foydalaning. Yozuvni oʻqituvchingizga "
                "yuboring."),
        ("5.1", "Namunaning qaysi xatboshisi (*1–5*) …"),
        ("5.2", "Namunadan toping: vaqtinchalik ishlar uchun Present Continuous dagi ikkita feʼl, ikkita "
                "takrorlanish ravishi, xatni boshlash uchun bitta va tugatish uchun bitta ibora."),
        ("5.3", "Boshqa xatdan olingan har bir gapda BITTA xato bor. *P* (tinish belgisi), *C* (bosh harf), *G* "
                "(grammatika) yoki *Sp* (imlo) ni tanlang va toʻgʻrisini yozing."),
        ("5.4", "Topshiriqni oʻqing. *A* yoki *B* ni tanlang va kiritishingiz kerak boʻlgan maʼlumotlarga eʼtibor "
                "bering."),
        ("5.5", "Xatingizni rejalashtiring. Faqat qaydlar."),
        ("5.6", "Xatingizning 2-xatboshisini yozing. Uni *P*, *C*, *G* va *Sp* xatolari uchun tekshiring."),
        ("5.7", "Xatingizni yozing (120–150 soʻz). 5.5 dagi reja, beshta xatboshi, Present Simple va Continuous, "
                "ikkita ravish hamda namunadagi boshlanish va tugash iboralaridan foydalaning. Keyin *P*, *C*, *G* "
                "va *Sp* xatolarini tekshiring.")]:
    h.say_also(label, text)

# ------------------------------------------ the explanations, told in Uzbek
h.retell("KEY WORDS", "KALIT SOʻZLAR", [
    "**to keep in touch**  aloqada boʻlmoq",
    "**a stamp**  pochta markasi — xat uchun toʻlanganini bildiradigan kichik qogʻoz",
    "**a network**  tarmoq — bir-biriga ulangan kompyuterlar",
    "**a pixel**  piksel — ekrandagi bitta mitti nuqta",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — PRESENT SIMPLE VA PRESENT CONTINUOUS", [
    "[[A]] **Present Simple** — **odatlar va kundalik ishlar** uchun: *I check my messages every morning.* — va "
    "**doimiy holatlar hamda hislar** uchun: *My grandmother lives in Fergana. She loves voice messages.* Inkor va "
    "soʻroqda *do / does*: *She doesn't use Instagram. · Do you write letters?*",
    "[[B]] **Present Continuous** (*am / is / are* + *-ing*) — **hozir boʻlayotgan** ishlar: *Shh! I'm recording a "
    "message.* — va **shu kunlardagi vaqtinchalik** ishlar: *This year my brother is studying in Seoul. · More "
    "people are sending voice messages these days.* *be* ni tushirib qoldirmang: *She's watching* — *She watching* "
    "emas.",
    "[[C]] **Vaqt soʻzlari:** Simple — *always, usually, every day, on Sundays* · Continuous — *now, at the moment, "
    "today, this week, these days*. **-ing imlosi:** *write → writing · chat → chatting · travel → travelling · lie "
    "→ lying*.",
    "[[D]] **Istisno — holat feʼllari.** *like, love, hate, want, need, know, understand, believe, prefer, mean, "
    "belong* odatda Continuous da ishlatilmaydi: *I know her* — *I'm knowing her* emas. Ikki feʼlning maʼnosi "
    "oʻzgaradi: *I think it's a good app* (fikr) / *I'm thinking about it* (harakat) · *I have a phone* (egalik) / "
    "*I'm having dinner* (harakat).",
])
h.retell("WATCH OUT!", "DIQQAT — KOʻP UCHRAYDIGAN XATOLAR", [
    "1 ✗ *I am liking this app.* → ✓ *I like this app.* — *like* holat feʼli.",
    "2 ✗ *She watching a video now.* → ✓ *She's watching …* — *be* ni tushirib qoldirmang.",
    "3 ✗ *He don't use social media.* → ✓ *He doesn't use …* — *he / she / it* + *doesn't*.",
    "4 ✗ *I'm usually sending my mum a text at lunch.* → ✓ *I usually send …* — bu odat.",
    "5 ✗ *What do you do now? Can I call you?* → ✓ *What are you doing now?* — hozir boʻlayotgan ish.",
    "6 ✗ *Sorry, I'm not understanding your message.* → ✓ *I don't understand …* — holat feʼli.",
])
h.retell("ADVERBS THAT MAKE WORDS STRONGER OR WEAKER", "KUCHAYTIRUVCHI VA KUCHSIZLANTIRUVCHI RAVISHLAR", [
    "**+ feʼl:** *I absolutely love … · I really like … · I particularly enjoy …*    **+ sifat:** *pretty good · "
    "fairly slow · really easy*",
    "**especially** = boshqalaridan koʻra koʻproq: *I like voice messages, especially from my grandmother.* "
    "**Oʻrni:** asosiy feʼldan oldin, lekin *be* dan keyin: *I often call her. · I'm often online.*",
])
h.retell("KEEPING IN TOUCH", "ALOQADA BOʻLISH", [
    "**keep in touch with** sb (aloqada boʻlmoq) · **get in touch with** sb (bogʻlanmoq, koʻpincha uzoq vaqtdan "
    "keyin) · **lose touch with** sb (aloqani yoʻqotmoq) · **hear from** sb (kimdandir xabar olmoq) · **be into** "
    "sth (biror narsani juda yoqtirmoq: *I'm really into blogs.*)",
])
h.retell("ERROR WARNING", "DIQQAT — RAVISHLARDAGI XATOLAR", [
    "✗ *I very like voice messages.* → ✓ *I really like* · ✗ *I hardly ever don't call him.* → ✓ *I hardly ever "
    "call him* — ikki inkor boʻlmaydi",
    "✗ *I always am online.* → ✓ *I'm always online* · ✗ *I keep in touch my cousins.* → ✓ *keep in touch with my "
    "cousins*",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [                 # the first of the two
    "Darslikdagi **1.09-trek**ni tinglang (1-unit, 1B dars). Tara, Magda, Kris va Mayk texnologiya muloqotni "
    "qanday oʻzgartirayotgani haqida gapirishadi.",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [
    "Darslikdagi **1.21-trek**ni tinglang (1-unit, 1D dars). Kris va Nina oila va doʻstlar bilan aloqada boʻlish "
    "haqida gapirishadi.",
])
h.retell("PRESENTATION — CHECK YOUR WRITING", "TUSHUNTIRISH — YOZGANINGIZNI TEKSHIRING", [
    "[[A]] **Tinish belgilari (P):** savoldan keyin soʻroq belgisi · qisqa shakllarda apostrof: *I'm, it's, what's, "
    "don't*.",
    "[[B]] **Bosh harflar (C):** ismlar, shahar va davlatlar, tillar va millatlar, hafta kunlari va oylar hamda *I*: "
    "*Laylo, Almaty, Kazakh, Monday, July*.",
    "[[C]] **Grammatika (G):** *he / she / it* dan keyin *-s* · Present Continuous da *be* · savollarda soʻz tartibi.",
    "[[D]] **Imlo (Sp):** *usually · really · beautiful · friend · because · studying*. Har bir xatni yuborishdan "
    "oldin toʻrttalasini tekshiring.",
])

# --------------------- the goals, in Uzbek, where the site's cover reads them
GOALS = [
    "xat, email, SMS va emoji tarixi haqidagi matnni tushunishni",
    "Present Simple va Present Continuous ni farqlashni — holat feʼllari bilan",
    "*hardly ever, pretty, absolutely* kabi ravishlarni toʻgʻri joyda ishlatishni",
    "*keep in touch, get in touch, hear from* iboralarini",
    "aloqa haqida gapirayotgan odamlarni tushunishni",
    "uzoqdagi odamga email yozib, uni xatolar uchun tekshirishni",
]
first_bar = bh_section_at().search(h.html).start()
h.html = (h.html[:first_bar] + '<table class="bk"><tr><td><p><span>You will learn to</span></p>'
          + "".join('<p><span>—  </span>%s</p>' % told(g, bare=True) for g in GOALS)
          + "</td></tr></table>" + h.html[first_bar:])

# ------------------------------------------------------------------ the key
K = {}
TFNG = ["TRUE", "FALSE", "NOT GIVEN"]
TICKED = "✓/correct/tick"
K[("1.1", 1, 1)] = own()
for n, a in enumerate([ok("stamp", "postage stamp"), "1971", ok("@", "at", "the @", "@ sign"),
                       ok("Neil Papworth", "Papworth", "Neil"), "Christmas", "1999",
                       ok("pixels", "pixel"), ok("collection", "permanent collection")], 1):
    K[("1.2", n, 1)] = Q(a)
for n, a in enumerate(["TRUE", "NOT GIVEN", "FALSE", "TRUE", "FALSE", "NOT GIVEN", "FALSE"], 1):
    K[("1.3", n, 1)] = choose(TFNG, a)
for n, a in enumerate([either("keep in touch", "keeping in touch"), "sender", "ordinary", "appeared", "separate",
                       "reply", "tiny", "meaningful"], 1):
    K[("1.4", n, 1)] = Q(a)
K[("1.5", 1, 1)] = own()

USE = {"H": "H · habit", "P": "P · permanent", "N": "N · now", "T": "T · temporary"}
for n, a in enumerate("HNTPHNTP", 1):
    K[("2.1", n, 1)] = choose(["H", "P", "N", "T"], a, labels=USE)
for n, (opts, a) in enumerate([(["posts", "is posting"], "posts"), (["have", "are having"], "are having"),
                               (["Do you know", "Are you knowing"], "Do you know"),
                               (["learn", "are learning"], "are learning"),
                               (["don't understand", "am not understanding"], "don't understand"),
                               (["doesn't usually reply", "isn't usually replying"], "doesn't usually reply"),
                               (["do you laugh", "are you laughing"], "are you laughing"),
                               (["think", "am thinking"], "think")], 1):
    K[("2.2", n, 1)] = choose(opts, a)
for n, a in enumerate([either("am sitting", "'m sitting", "I'm sitting", "I am sitting"),
                       either("is raining", "'s raining", "It's raining", "It is raining"),
                       ok("are studying", "'re studying"), "have", "work",
                       either("am not working", "'m not working", "I'm not working", "I am not working"),
                       either("is getting", "'s getting"), "miss", "Do", "go"], 1):
    K[("2.3", n, 1)] = Q(a)
for n, a in enumerate([either("I know all my classmates' birthdays", "I know all my classmates birthdays",
                              "I know all my classmate's birthdays", "I know"), TICKED,
                       either("This phone belongs to my brother", "belongs"), TICKED,
                       either("She wants a new laptop for her birthday", "She wants", "wants",
                              "She would like a new laptop for her birthday"), TICKED], 1):
    K[("2.4", n, 1)] = fix(a)
K[("2.5", 1, 1)] = own()
for n, a in enumerate([ok("Do you usually reply to messages quickly", "Do you usually reply to your messages quickly"),
                       either("What is your best friend doing at the moment",
                              "What's your best friend doing at the moment"),
                       ok("How often do your parents call you", "How often do your parents phone you"),
                       ok("Are you learning anything new this month", "Are you learning something new this month")], 1):
    K[("2.6", n, 1)] = write(a)
FIXED = [either("I'm writing", "I am writing", "I'm writing this on the bus", "I am writing this on the bus"),
         either("I usually walk", "I usually walk to school"),
         either("Do you know", "Do you know Sardor's new number"),
         either("He doesn't answer", "doesn't answer", "He doesn't answer my messages", "He does not answer",
                "He does not answer my messages"),
         either("what are you doing now", "what are you doing", "And what are you doing now")]
for n, a in enumerate(FIXED, 1):
    K[("2.7", n, 1)] = None                       # the mistake as they found it: theirs, not marked
    K[("2.7", n, 2)] = write(a, control=None)
for n, a in enumerate(["chatting", "writing", either("travelling", "traveling"), "planning", "lying", "using",
                       "getting", "making"], 1):
    K[("2.8", n, 1)] = Q(a)
K[("2.9", 1, 1)] = own()
K[("2.9", 2, 1)] = own()

for n, a in enumerate(["almost always", "usually", either("rarely", "hardly ever"), either("hardly ever", "rarely")], 1):
    K[("3.2", n, 1)] = Q(a)
for n, (opts, a) in enumerate([(["absolutely", "fairly"], "absolutely"), (["pretty", "particularly"], "pretty"),
                               (["especially", "pretty"], "especially"), (["fairly", "absolutely"], "fairly"),
                               (["particularly", "pretty"], "particularly"), (["really", "especially"], "really")], 1):
    K[("3.3", n, 1)] = choose(opts, a)
for n, a in enumerate([either("I'm hardly ever late for school", "I am hardly ever late for school"),
                       ok("My mum usually sends me voice messages at lunchtime",
                          "My mum usually sends me voice messages at lunch time"),
                       ok("My friends almost always reply to my messages in five minutes", numbers=True)], 1):
    K[("3.4", n, 1)] = write(a)
LONG = {"rarely", "really", "write", "photos", "usually"}
for n, (w, _l) in enumerate(VOWELS, 1):
    K[("3.5", n, 1)] = choose(["long", "short"], "long" if w in LONG else "short")
for n, a in enumerate(["lost", "hear", "get", "keep", "into", "keep"], 1):
    K[("3.6", n, 1)] = Q(a)
K[("3.7", 1, 1)] = own()

for n, a in enumerate([either("text message", "a text message", "text", "a text"), "days", "cancel", "explanation",
                       ok("presents", "gifts"), ok("wall", "Facebook wall"), ok("South America"),
                       ok("blog", articles=True), ok("letter", articles=True)], 1):
    K[("4.1", n, 1)] = Q(a)
for n, a in enumerate("UHUU", 1):
    K[("4.2", n, 1)] = choose(["H", "U"], a, labels={"H": "H · happy", "U": "U · unhappy"})
for (n, k), a in {(1, 1): "send", (2, 1): "get", (3, 1): either("is travelling", "'s travelling", "is traveling"),
                  (4, 1): either("is writing", "'s writing"), (4, 2): either("is doing", "'s doing"),
                  (5, 1): "calls"}.items():
    K[("4.3", n, k)] = Q(a)
K[("4.4", 1, 1)] = own()
for n, a in enumerate(["sometimes", "month", "hardly ever", "weekend", "often"], 1):
    K[("4.5", n, 1)] = Q(a)
for n, a in enumerate([either("she forgets", "forgets", "she forgets to write", "she forgets it"),
                       either("she gets worried", "she's worried", "she is worried", "she worries", "gets worried",
                              "to know what he's doing"),
                       either("when she meets them", "when they meet", "when she sees them", "when she meets friends"),
                       either("a particularly good photo", "a good photo", "particularly good photos", "good photos",
                              "a photo", "photos")], 1):
    K[("4.6", n, 1)] = Q(a)
K[("4.6", 4, 2)] = choose(["Chris", "Nina"], "Chris")
for n in range(1, 5):                             # notes, not sentences
    K[("4.7", n, 1)] = None
for n in range(1, 4):                             # the checks before they send the recording
    K[("4.8", n, 1)] = tick()

for n, a in enumerate(["3", "4", "2", "5"], 1):
    K[("5.1", n, 1)] = choose(["1", "2", "3", "4", "5"], a)
K[("5.2", 1, 1)] = own()
KIND = {"P": "P · punctuation", "C": "C · capital letter", "G": "G · grammar", "Sp": "Sp · spelling"}
for n, (kind, fixed) in enumerate([
        ("C", None), ("P", None),                 # a capital, a question mark: the teacher's to mark
        ("P", either("I'm having a great time here", "I'm")),
        ("G", either("My host mother cooks amazing plov every Sunday", "cooks")),
        ("Sp", either("We usually have lessons in the morning", "usually")),
        ("G", either("I'm studying biology and chemistry this month", "I am studying biology and chemistry this month",
                     "I'm studying", "I am studying")),
        ("P", either("The camp is next to a lake, and it's beautiful", "The camp is next to a lake and it's beautiful",
                     "it's", "it's beautiful", "The camp is next to a lake, and it is beautiful")),
        ("Sp", either("The other students are very friendly", "friendly"))], 1):
    K[("5.3", n, 1)] = choose(["P", "C", "G", "Sp"], kind, labels=KIND)
    K[("5.3", n, 2)] = write(fixed, control=None) if fixed else None
for n in range(1, 6):                             # the plan
    K[("5.5", n, 1)] = None
K[("5.6", 1, 1)] = own()
K[("5.7", 1, 1)] = own(control="essay")

if __name__ == "__main__":
    data = h.build(K, "Pre-Intermediate", 1, "Unit 1B & 1D — Communicating")
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "p01bd_new.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
