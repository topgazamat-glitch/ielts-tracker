"""P03AC Money - Azamat's Pre-Intermediate booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(P03AC Money - answer key), joined box by box by hand. Every explanation is
told again in Uzbek, with the English examples kept, and every instruction
has a line in Uzbek under it; the reading, the texts to fill in and the
exercises stay English.

What a phone gets that paper does not:
  - taps for every choice: who says it, A/B/C, perfect or past simple, the
    words in the box, the two o sounds, Mike or Kathie, true or false,
    assistant or customer;
  - the number pad for the till phrases in order;
  - boxes where paper has none: 2.5's corrections, 3.5, 5.2's questions,
    the answers about the model.
The stray "6" under 5.3, a numbered line with nothing on it, is gone.

    python3 handouts/p03ac_digital.py            # writes handouts/p03ac.json, lists every box
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import (Handout, Q, choose, tick, own, write, fix, number, report,   # noqa: E402
                     BLANK_TAG, ITEM_P, LEADER_P, plain)

DOCX = "~/Desktop/Handouts/B1 Pre-Intermediate/P03AC Money/P03AC Money — handout (new design).docx"
W = "95%"

h = Handout(DOCX)
TAGS = {int(m.group(1)): m.group(0) for m in BLANK_TAG.finditer(h.html)}


def section(label):
    return h.html.index("%s  </span>" % label)


def either(*forms):
    return "/".join(forms)


def have(*rest):
    """'ve done / have done, for each form given."""
    return either(*[p + r for r in rest for p in ("'ve ", "have ")])


# ------------------------------------------------------------ 1 Reading
h.options_on_lines("1.3")
for n in range(1, 5):
    h.item_box("1.3", n, where="options")
for n in range(1, 4):
    h.item_box("1.4", n, width="190px", where="leader")
h.leaders("1.5", "1.6  </span>", [(1, W, "Three present perfect verbs, and why"),
                                  (2, W, "Three past simple verbs, and why")])
for n in range(1, 4):
    h.item_box("1.6", n, where="leader")

# ------------------------------------------------------------ 2 Grammar
for n in range(2, 9):                             # item 1 is the worked example
    h.item_box("2.5", n)

# ------------------------------------------------------------ 3 Vocabulary
for n in range(1, 5):
    h.item_box("3.5", n, where="leader")

# ------------------------------------------------------------ 4 Listening
h.options_on_lines("4.6")
for n in (1, 2, 3):
    h.item_box("4.6", n)

# ------------------------------------------------------------ 5 Everyday English
for n in range(1, 4):                             # the questions under the table
    h.item_box("5.2", n, where="leader")
six = next(m for m in ITEM_P.finditer(h.html) if m.group(2) == "5.3" and m.group(3) == "6"
           and plain(m.group(4)) == "6")
h.html = h.html[:six.start()] + h.html[six.end():]
for n in range(1, 5):
    h.item_box("5.7", n, where="leader")
h.leaders("5.8", "CHECK BEFORE", [(20, W, "Write your conversation here")])
h.html = h.html.replace(TAGS[120], "", 1)         # the line count: the box counts the words itself

# ------------------------------- every instruction, once more, in Uzbek
for label, text, *after in [
        ("1.1", "Muhokama qiling. Hayotingizda sotib olgan eng yaxshi narsa nima? Uni qancha vaqt oldin sotib "
                "olgansiz?"),
        ("1.2", "Buni kim aytadi? *S* (Sardor), *N* (Nilufar) yoki *J* (Jasur) ni tanlang."),
        ("1.3", "Eng toʻgʻri javobni tanlang: *A*, *B* yoki *C*."),
        ("1.4", "Matndan shu maʼnodagi soʻz yoki iborani toping."),
        ("1.5", "Matndan uchta present perfect va uchta past simple feʼlni toping. Har biri nega ishlatilgan?"),
        ("1.6", "Savollarga javob bering."),
        ("2.1", "Present perfect (*PP*) mi yoki past simple (*PS*) mi? Faqat vaqt ifodasiga qarang."),
        ("2.2", "Present perfect yoki past simple bilan toʻldiring."),
        ("2.3", "Ikkinchi savolni past simple da yozing."),
        ("2.4", "Suhbatni toʻldiring."),
        ("2.5", "Xatoni topib, toʻgʻrilang. IKKITA gap toʻgʻri — ular uchun *✓ It is correct* tugmasini bosing."),
        ("2.6", "Tinglang va takrorlang. Bu qaysi zamon?"),
        ("3.1", "Har bir savolni ramkadagi soʻz bilan toʻldiring: tanlang."),
        ("3.2", "*Borrow*, *lend*, *owe* yoki *pay back*? Hikoyani toʻldiring."),
        ("3.3", "Har bir gapni BITTA soʻz bilan toʻldiring."),
        ("3.4", "*/əʊ/* mi yoki */ɔː/* mi? Tanlang."),
        ("3.5", "Har bir gapdagi xatoni topib, toʻgʻri gapni yozing."),
        ("3.6", "Sherigingizdan soʻrang. Toʻliq gap bilan javob bering."),
        ("4.1", "Bir marta tinglang. Buni kim qilgan — *M* (Mike) mi yoki *K* (Kathie) mi?"),
        ("4.2", "Yana tinglang. Toʻgʻri (*T*) mi yoki notoʻgʻri (*F*) mi?"),
        ("4.3", "Yana bir marta tinglang va har bir qatorni toʻldiring."),
        ("4.4", "Tinglang va nima boʻlishiga eʼtibor bering."),
        ("4.5", "Har bir iborani ikki marta ayting — avval sekin, keyin tez."),
        ("4.6", "Gapiruvchi nima demoqchi? *A* yoki *B* ni tanlang."),
        ("5.1", "Har bir iborani BITTA soʻz bilan toʻldiring."),
        ("5.2", "Sotuvchimi (*A*) yoki xaridormi (*C*)? Keyin savollarga javob bering."),
        ("5.3", "Kassadagi beshta iborani tartib bilan raqamlang (1–5)."),
        ("5.4", "Fikringizni oʻzgartiring. Ikkinchi qatorni yozing."),
        ("5.5", "Har bir gapni toʻldiring. Tushirib qoldirilgan soʻzlarning hammasi urgʻusiz."),
        ("5.6", "Namunaviy suhbatni oʻqing. Keyin javob bering."),
        ("5.7", "Namuna haqidagi savollarga javob bering."),
        ("5.8", "Endi oʻz doʻkon suhbatingizni yozing (12–14 qator). Ikki kishi uchinchi odamga sovgʻa sotib "
                "olyapti. Bu boʻlimdan kamida beshta iborani ishlating va bir marta fikringizni oʻzgartiring.",
         "change your mind once")]:
    h.say_also(label, text, after=after[0] if after else None)

# ------------------------------------------ the explanations, told in Uzbek
h.goals([
    "bitta savol yordamida present perfect va past simple orasida tanlashni",
    "xarid tajribalari haqida *ever, never* va *three times* bilan gapirishni",
    "pul soʻzlarini ishlatishni — va *borrow, lend, owe* ni adashtirmaslikni",
    "sotuvchilarning chegirmalar kuni haqidagi hikoyalarini tushunishni",
    "doʻkonda gaplashish, fikrni oʻzgartirish va kassada toʻlashni",
])
h.retell("KEY WORDS", "KALIT SOʻZLAR", [
    "**a bargain**  juda arzonga olingan yaxshi narsa",
    "**to afford**  biror narsaga pulingiz yetmoq",
    "**to regret**  qilgan ishingizdan afsuslanmoq",
    "**second-hand**  yangi emas; ilgari birovniki boʻlgan",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — PRESENT PERFECT YOKI PAST SIMPLE?", [
    "Ikkala zamon ham oʻtgan voqealar haqida gapiradi. Qaysi biri kerakligini bitta savol hal qiladi — va u har "
    "safar bir xil savol.",
    "[[SAVOL]] **Men bu QACHON boʻlganini aytyapmanmi?** Ha boʻlsa — past simple. Yoʻq boʻlsa — present perfect.",
    "[[PP]] **Present perfect = tajriba, butun hayotingizning qaysidir vaqtida.** *I've ridden it nearly every "
    "day. · I've never liked it.* Savolda: *Have you ever bought anything in a sale?* Vaqt aytilmaydi va "
    "kerak ham emas.",
    "[[PS]] **Past simple = aniq bir payt.** *I bought it eleven years ago. · We stood there for two hours. · The "
    "doors opened.* Vaqtni aytdingizmi — present perfect ishlatib boʻlmaydi.",
    "[[→]] **Ular juftlikda ishlaydi.** *Have you ever queued for the sales all night? — Yes, I have. It was two "
    "years ago, and I wanted a tablet.* Savol present perfect bilan ochiladi; javob vaqtni aytadi va past simple "
    "ga oʻtadi.",
    "**Past simple talab qiladigan soʻzlar:** *yesterday · last night · this morning · two years ago · in 2019 · "
    "when I was a student*. **Present perfect bilan keladigan soʻzlar:** *ever · never · before · in my life · "
    "once · twice · three times*.",
])
h.retell("ERROR WARNING", "DIQQAT — ZAMONLARDAGI XATOLAR", [
    "1 **Present perfect gapda vaqt ifodasi.** ✗ *I've bought this phone last year.* → ✓ *I bought this phone "
    "last year.* Bu darajadagi eng keng tarqalgan xato, va uni koʻrish oson: vaqt soʻzlarini qidiring.",
    "2 **Butun hayot nazarda tutilganda past simple.** ✗ *Did you ever buy anything in a sale?* → ✓ *Have you "
    "ever bought anything in a sale?* *Ever* — hayotingizning istalgan vaqtida, shuning uchun present perfect "
    "kerak.",
    "3 **BEEN va GONE bir xil soʻz emas.** *I've been to Dubai* = borib, qaytib keldim. *She's gone to Dubai* = u "
    "hozir oʻsha yerda. Tajriba uchun doim *been* kerak.",
    "4 **EVER va NEVER ning oʻrni.** ✗ *I have seen never crowds like this.* → ✓ *I have never seen crowds like "
    "this.* *Ever* va *never* uchinchi shakldagi feʼldan (past participle) oldin keladi.",
    "5 **Qisqa javob toʻliq shaklni saqlaydi.** ✗ *Yes, I've.* → ✓ *Yes, I have.* Lekin *No, I haven't* — "
    "toʻgʻri. Ha uchun toʻliq, yoʻq uchun qisqa.",
])
h.retell("PRONUNCIATION", "TALAFFUZ", [
    "Zamon feʼldan oldingi bitta kichik tovushda yashaydi. *I've bought* → /aɪv bɔːt/ · *I bought* → /aɪ bɔːt/. "
    "Feʼl bir xil eshitiladi; butun farq — /v/.",
    "Savollarda bu yanada qiyin. *Have you ever…?* → /əvju evə/ · *Did you…?* → /dɪdʒə/. Yordamchi feʼllarning "
    "hech biri urgʻu olmaydi, shuning uchun vaqt ifodasiga quloq soling — *last night, ever, two years ago* doim "
    "baland aytiladi va ular zamonni aytib beradi.",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — PUL VA XARID", [
    "[[PUL OLISH]] *borrow* (kimdandir) *· lend* (kimgadir) *· owe · get a loan · pay back*",
    "[[PULGA EGA BOʻLISH]] *afford · save up for · a bank account · cost · spend money on*",
    "[[KAMROQ TOʻLASH]] *a discount · a special offer · a bargain · a sale · reduced*",
    "**Adashtiriladigan uchtasi.** *I borrow from you* (pul menga keladi). · *You lend to me* (pul sizdan "
    "ketadi). · Keyin, qaytarib bermagunimcha, *I owe you*, va oxirida *I pay it back*. Bitta voqea, uchta feʼl, "
    "uchta har xil ega.",
    "**AFFORD bilan ehtiyot boʻling.** U deyarli doim *can* yoki *can't* dan keyin keladi: *I can't afford it.* "
    "*I don't afford it* emas. *Cost* esa predlogsiz: *It cost £80*, hech qachon *it cost for £80* emas.",
])
h.retell("PRONUNCIATION — THE TWO O SOUNDS", "TALAFFUZ — IKKI XIL O TOVUSHI", [
    "Pul soʻzlarida *o* harfi koʻp, va u ikki xil tovush beradi — rus va oʻzbek tilida gapiruvchilar ularni "
    "bitta qilib yuboradi.",
    "[[/əʊ/]] uzun, lablar harakatlanadi: *owe · a loan · borrow · only · phone*",
    "[[/ɔː/]] tekis, lablar qimirlamaydi: *afford · bought · thought · more · course*",
    "Juftlikni ovoz chiqarib ayting: *owe* /əʊ/ va *or* /ɔː/. Agar bir xil eshitilsa, ikkinchisi juda qisqa — "
    "/ɔː/ uzun, faqat u harakatlanmaydi.",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [
    "Radio jurnalisti Janie yilning eng katta chegirmalar kuni oxirida ikki sotuvchidan intervyu oladi. Mike "
    "ilgari ham chegirmalar kunida ishlagan. Kathie esa yoʻq.",
    "Agar sinfingizda audio boʻlsa, bu 3.03-trek. Boʻlmasa, oʻqituvchingiz matnni oʻqib beradi — topshiriqlar bir "
    "xil.",
])
h.retell("WHY YOU DIDN'T HEAR IT", "NEGA ESHITMADINGIZ?", [
    "**Zamonni yordamchi feʼl koʻtaradi, lekin uni hech kim toʻliq aytmaydi.** *I've worked* → /aɪv wɜːkt/ · *I "
    "worked* → /aɪ wɜːkt/. Ikki zamonni uchta tovush ajratib turadi.",
    "Shuning uchun vaqt ifodasiga quloq soling. U doim urgʻuli va zamonni oʻzi hal qiladi: *three times before "
    "· this morning · at about midnight last night · never*.",
])
h.retell("TALKING TO PEOPLE IN SHOPS", "DOʻKONDA GAPLASHISH", [
    "Doʻkondagi suhbatning faqat ikki tomoni bor va har bir tomonning oʻz iboralari bor. Ularni ikki guruhda "
    "oʻrganing.",
    "[[SOTUVCHI]] *Can I help you? · Are you looking for anything in particular? · What sort of thing does he "
    "like?*",
    "[[XARIDOR]] *We're looking for a present for a friend. · What does it do? · Do you have anything cheaper? · "
    "Could you show us something else? · We'll take it.*",
    "**Ehtiyot boʻling:** *We'll take it* — inglizcha „sotib olamiz“ degani. *I will buy it* deyish xato emas, "
    "lekin sotuvchi buni suhbatning oxiri deb eshitmaydi — ibora esa aynan shu uchun kerak.",
])
h.retell("PAYING AT THE TILL", "KASSADA TOʻLASH", [
    "Yana beshta tayyor ibora. Ingliz tilida gaplashiladigan istalgan mamlakatdagi istalgan doʻkonda ularning "
    "hammasini shu tartibda eshitasiz:",
    "*Who's next, please? · How would you like to pay? · Can you put your card in, please? · Can you enter your "
    "PIN, please? · Here's your receipt.*",
    "**Ikkita talaffuzni toʻgʻri qiling.** *receipt* — /rɪˈsiːt/, *p* aytilmaydi. *PIN* esa uchta harf emas, "
    "bitta soʻz qilib aytiladi.",
])
h.retell("CHANGING YOUR MIND", "FIKRNI OʻZGARTIRISH", [
    "Ingliz tilida fikr oʻzgarganini ochiq aytish kerak. Shunchaki boshqa narsa desangiz, suhbatdoshingiz sizni "
    "notoʻgʻri eshitdim deb oʻylaydi.",
    "*On second thoughts, I really think we should get something sporty. · Actually, I think I'll put it on my "
    "credit card.*",
    "**Ular bir xil emas.** *On second thoughts* — „yana oʻylab koʻrdim“ degani, demak oldin birinchi fikr "
    "boʻlgan boʻlishi kerak. *Actually* yengilroq va boshqa odamning gapini ham toʻgʻrilashi mumkin. Ikkalasi "
    "ham gap boshida, vergul bilan keladi.",
])
h.retell("PRONUNCIATION — SENTENCE STRESS", "TALAFFUZ — GAP URGʻUSI", [
    "Ingliz tili har bir soʻzga bir xil vaqt bermaydi. Muhim soʻzlar uzun va baland; qolganlari ular orasiga "
    "siqib qoʻyiladi.",
    "*This looks perfect.* — toʻrt boʻgʻin, ikkitasi urgʻuli. · *We're only here for Leo.* — olti boʻgʻin, "
    "ikkitasi urgʻuli.",
    "Siqiladigan soʻzlar doim bir xil turdagi soʻzlar: *to · a · the · for · of · you · your*. Ular hech qachon "
    "gapning asosiy maʼnosi emas, shuning uchun ingliz tili ularga vaqt sarflamaydi — aynan shuning uchun ularni "
    "eshitmaysiz.",
])
h.retell("CHECK BEFORE YOU PRACTISE IT", "MASHQ QILISHDAN OLDIN TEKSHIRING", [
    "{box}  Sotuvchi *Can I help you?* bilan boshlaydi.   {box}  Kimdir doʻkonga nega kelganini aytadi.   {box}  "
    "Bitta savol narsa nima qilishini soʻraydi.",
    "{box}  Bitta xaridor arzonroq yoki boshqa narsa soʻraydi.   {box}  Kimdir *On second thoughts* yoki "
    "*Actually* bilan fikrini oʻzgartiradi.",
    "{box}  Suhbat *We'll take it* va kassa iborasi bilan tugaydi.   {box}  Qatorlar soni: 12–14.",
])
h.one_per_line("MASHQ QILISHDAN OLDIN TEKSHIRING", None, at="box")
h.retell_cells({"Present perfect — did it ever happen?": "Present perfect — bu hech boʻlganmi?",
                "Past simple — when, and what happened?": "Past simple — qachon, va nima boʻldi?",
                "First question — present perfect": "Birinchi savol — present perfect",
                "Second question — past simple": "Ikkinchi savol — past simple"})
h.retell_cells({"What is written": "Yozilishi", "What you hear": "Eshitilishi", "Why": "Nega",
                "I have is one /v/": "<i>I have</i> bitta /v/ boʻlib qoladi",
                "have you almost vanishes": "<i>have you</i> deyarli yoʻqoladi",
                "no /v/ — it's the past simple": "/v/ yoʻq — bu past simple",
                "never is the loud word": "<i>never</i> — baland aytiladigan soʻz",
                "You said": "Siz aytdingiz", "Now change it": "Endi oʻzgartiring"},
               after="4.4  </span>")

# ------------------------------------------------------------------ the key
K = {}
SNJ = {"S": "S · Sardor", "N": "N · Nilufar", "J": "J · Jasur"}
for n, a in enumerate("SNJSJN", 1):
    K[("1.2", n, 1)] = choose(["S", "N", "J"], a, labels=SNJ)
for n in range(1, 5):
    K[("1.3", n, 1)] = choose(["A", "B", "C"], "B")
for n, a in enumerate(["reduced", "to regret/regret", "to owe/owe/owes"], 1):
    K[("1.4", n, 1)] = Q(a)
K[("1.5", 1, 1)] = own()
K[("1.5", 2, 1)] = own()
for n in range(1, 4):
    K[("1.6", n, 1)] = own()
PPS = {"PP": "PP · present perfect", "PS": "PS · past simple"}
# as numbered: 1 last night 2 ever 3 three times 4 two years ago 5 in my life 6 this morning 7 never
# 8 when I was a student
for n, a in enumerate(["PS", "PP", "PP", "PS", "PP", "PS", "PP", "PS"], 1):
    K[("2.1", n, 1)] = choose(["PP", "PS"], a, labels=PPS)
for key, a in (((1, 1), have("worked")), ((2, 1), "opened"), ((3, 1), have("never known")),
               ((4, 1), "started"), ((5, 1), have("ever met")), ((6, 1), "Have"), ((6, 2), "been")):
    K[("2.2",) + key] = Q(a)
for n in range(1, 5):                             # the key gives samples: his to read
    K[("2.3", n, 1)] = own(control=None)
for n, a in enumerate(["Have you ever queued", "have", "did", "stood", "did you buy", "cost",
                       have("never done"), "Were you", "came", either("didn't buy", "did not buy")], 1):
    K[("2.4", n, 1)] = Q(a)
TICKED = "✓/correct/tick"
for n, a in zip(range(2, 9), [
        "Have you ever bought anything in a sale",
        either(*[s + r for s in ("She's been to the sales three times this month",
                                 "She has been to the sales three times this month")
                 for r in (", and she's here now", " and she's here now", "")]),
        either("I have never seen crowds like this", "I've never seen crowds like this"),
        "Yes, I have",
        TICKED,
        TICKED,
        either("We opened the doors this morning at six", "We opened the doors at six this morning")]):
    K[("2.5", n, 1)] = fix(a)
for n, a in enumerate(["PP", "PS", "PP", "PS"], 1):   # I've bought, I bought, Have you seen, Did you see
    K[("2.6", n, 1)] = choose(["PP", "PS"], a, labels=PPS)
BOX31 = ["bargain", "discount", "loan", "money", "sale"]
for n, a in enumerate(["money", "loan", "discount", "sale", "bargain"], 1):
    K[("3.1", n, 1)] = choose(BOX31, a)
for n, a in enumerate(["lend", "borrowed", "owed", "paid back/paid"], 1):
    K[("3.2", n, 1)] = Q(a)
for key, a in (((1, 1), "up"), ((2, 1), "cost"), ((3, 1), "afford"), ((3, 2), "account"),
               ((4, 1), "discount"), ((5, 1), "offer"), ((6, 1), "bargain")):
    K[("3.3",) + key] = Q(a)
OO = ["/əʊ/", "/ɔː/"]
# as numbered: 1 owe 2 afford 3 loan 4 bought 5 borrow 6 more
for n, a in enumerate(["/əʊ/", "/ɔː/", "/əʊ/", "/ɔː/", "/əʊ/", "/ɔː/"], 1):
    K[("3.4", n, 1)] = choose(OO, a)
for n, a in enumerate([
        either("I can't afford a new laptop this year", "I cannot afford a new laptop this year",
               "I can not afford a new laptop this year"),
        either("Can you lend me twenty thousand so'm", "Can I borrow twenty thousand so'm",
               "Can I borrow twenty thousand so'm from you"),
        "The jacket cost about two hundred dollars",
        either("I must pay my brother back on Friday", "I must pay back my brother on Friday")], 1):
    K[("3.5", n, 1)] = write(a)
MK = {"M": "M · Mike", "K": "K · Kathie"}
for n, a in enumerate("KMKM", 1):                 # first time, disappointed people, not well, three before
    K[("4.1", n, 1)] = choose(["M", "K"], a, labels=MK)
TF = {"T": "T · true", "F": "F · false"}
for n, a in enumerate("TFFTT", 1):
    K[("4.2", n, 1)] = choose(["T", "F"], a, labels=TF)
for key, a in (((1, 1), have("worked")), ((1, 2), have("never seen")), ((2, 1), "opened"), ((3, 1), "started"),
               ((4, 1), have("ever met")), ((5, 1), have("never worked")),
               ((5, 2), either("didn't know", "did not know"))):
    K[("4.3",) + key] = Q(a)
for n in range(1, 4):
    K[("4.6", n, 1)] = choose(["A", "B"], "B")
for n, a in enumerate(["help", "looking", "anything", "sort", "do", "cheaper", "show", "take"], 1):
    K[("5.1", n, 1)] = Q(a)
AC = {"A": "A · assistant", "C": "C · customer"}
for n, a in enumerate("ACAC", 1):
    K[("5.2", n, 1)] = choose(["A", "C"], a, labels=AC)
K[("5.2", 1, 2)] = write(either("We're looking for a present for a friend", "We are looking for a present for a friend"))
K[("5.2", 2, 2)] = own()                          # two phrases in one box: his to read
K[("5.2", 3, 2)] = write("What does it do")
# as numbered: 1 PIN 2 who's next 3 receipt 4 how would you like to pay 5 card in
for n, a in enumerate("41523", 1):
    K[("5.3", n, 1)] = number(a)
K[("5.4", 1, 1)] = Q("On second thoughts/Actually/On second thought")
for n in range(2, 5):                             # the key gives samples: his to read
    K[("5.4", n, 1)] = own()
for key, a in (((1, 1), "to"), ((1, 2), "at"), ((1, 3), "a"), ((2, 1), "me"), ((2, 2), "the"),
               ((3, 1), "for"), ((3, 2), "a"), ((3, 3), "for"), ((3, 4), "my"), ((4, 1), "in"), ((4, 2), "a"),
               ((5, 1), "a"), ((5, 2), "lot"), ((5, 3), "of"), ((5, 4), "to")):
    K[("5.5",) + key] = Q(a)
for n in range(1, 5):
    K[("5.7", n, 1)] = own()
K[("5.8", 20, 1)] = own(control="essay")
for n in range(1, 8):                             # the checklist
    K[("5.8", n, 1)] = tick()

if __name__ == "__main__":
    data = h.build(K, "Pre-Intermediate", 3, "Unit 3A & 3C — Money")
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "p03ac.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
