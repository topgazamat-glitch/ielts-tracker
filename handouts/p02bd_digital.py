"""P02BD Travel and tourism - Azamat's Pre-Intermediate booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(P02BD Travel and tourism - answer key), joined box by box by hand. Its
explanations are told again in Uzbek - every explanation box, the goals,
the headings of the tables that explain, and a line under every exercise
instruction - with the English examples kept;
the reading, the texts to fill in and the exercises stay English.

What a phone gets that paper does not:
  - taps for every choice: which story, A/B/C, stopped or continued,
    when/while, weak or strong, the endings in 3.1, A/B, and the two
    answers of 5.1 that paper asks to underline;
  - the ▲ gaps of 5.2 become the five linking words to tap, where the ▲ is;
  - a box for every exercise that paper leaves to ruled lines: 1.5, 1.6,
    2.8, 3.4, 4.2, 5.5 and the blog itself, with a word count.

    python3 handouts/p02bd_digital.py            # writes handouts/p02bd.json, lists every box
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import (Handout, Q, choose, tick, own, write, fix, note, number, report,   # noqa: E402
                     BLANK_TAG, plain)

DOCX = ("~/Desktop/Handouts/B1 Pre-Intermediate/P02BD Travel and tourism/"
        "P02BD Travel and tourism — handout (new design).docx")
TF = ["T", "F"]

h = Handout(DOCX)
TAGS = {int(m.group(1)): m.group(0) for m in BLANK_TAG.finditer(h.html)}

# ------------------------------------------------------------ 1 Reading
h.options_on_lines("1.3")
for n in (1, 2, 3, 4):
    h.item_box("1.3", n, where="options")
for n in (1, 2, 3):
    h.item_box("1.4", n, width="170px", where="leader")
h.leaders("1.5", "1.6  </span>", [(1, "95%", "Six past continuous verbs, and what interrupted each")])
for n in (1, 2, 3):
    h.item_box("1.6", n, where="leader")

# ------------------------------------------------------------ 2 Grammar
for n in range(2, 9):                            # 2.5: item 1 is the worked example
    h.item_box("2.5", n)
h.leaders("2.8", "3.1  </span>", [(1, "95%", "Three sentences - when once, while once")])

# ------------------------------------------------------------ 3 Vocabulary
ENDS = h.key_first("3.1")
for n in (1, 2, 3, 4):
    h.item_box("3.4", n, where="leader")
h.leaders("3.6", "BEFORE YOU LISTEN", [])      # speaking: no lines to fill

# ------------------------------------------------------------ 4 Listening
h.leaders("4.1", "4.2  </span>", [])            # speaking
h.grid_rows("4.2", [""])
h.options_on_lines("4.7")
for n in (1, 2, 3):
    h.item_box("4.7", n)

# ------------------------------------------------------------ 5 Writing
# 5.1: paper asks to underline one of two; a phone taps it
for n in range(1, 6):
    h.item_box("5.1", n)
# 5.2: the ▲ is where the word goes - so that is where the choice goes
for m in reversed(list(h._items("5.2"))):
    n = int(m.group(3))
    if "▲" not in m.group(4):
        continue
    h.texts[("5.2", n)] = plain(m.group(4))
    guts = m.group(4).replace("▲", "{{box:5.2:%d:60px:}}" % n, 1)
    h.html = h.html[:m.start()] + m.group(1) + guts + "</p>" + h.html[m.end():]
# 5.3: once with so, once with because - one box each, without the "/" between
for i, j in ((94, 95), (96, 97)):
    h.hints[i], h.hints[j] = "With so", "With because"
    a = h.html.index(TAGS[i]) + len(TAGS[i])
    b = h.html.index(TAGS[j], a)
    h.html = h.html[:a] + re.sub(r"\s/\s", " ", h.html[a:b], count=1) + h.html[b:]
for n in (1, 2, 3, 4):
    h.item_box("5.5", n, where="leader")
h.grid_rows("5.6", [""])
h.leaders("5.7", "CHECK BEFORE", [(20, "95%", "Write your blog entry here")])

# ------------------------------- every instruction, once more, in Uzbek
# Said the way the phone asks for it: where paper says "write" or
# "underline" a letter or a word, the student taps, so the Uzbek says "tanlang".
INSTRUCTIONS = [
    ("1.1", "Muhokama qiling. Hayotingizdagi eng yomon safar qaysi boʻlgan? Nima notoʻgʻri ketgan?"),
    ("1.2", "Qaysi hikoya? *Platform*, *Stranger* yoki *The push* ni tanlang."),
    ("1.3", "Eng toʻgʻri javobni tanlang: *A*, *B* yoki *C*."),
    ("1.4", "Matndan shu maʼnodagi soʻz yoki iborani toping."),
    ("1.5", "Matndan oltita *past continuous* feʼlni toping. Har bir harakat davom etayotganda nima "
            "sodir boʻldi?"),
    ("1.6", "Savollarga javob bering."),
    ("2.1", "Gaplarni *past continuous* bilan toʻldiring."),
    ("2.2", "*Past simple* mi yoki *past continuous* mi? Gaplarni toʻldiring."),
    ("2.3", "Uzun harakat toʻxtadimi (*S*) yoki davom etdimi (*C*)? Tanlang."),
    ("2.4", "*when* yoki *while*? Tanlang."),
    ("2.5", "Xatoni topib, toʻgʻrilang. IKKITA gap toʻgʻri — ular uchun *✓ It is correct* tugmasini bosing."),
    ("2.6", "Hikoyani qavs ichidagi feʼllar bilan toʻldiring."),
    ("2.7", "Har bir gapni *past simple* dagi harakat bilan tugating."),
    ("2.8", "Oʻzingizning bir safaringiz haqida uchta gap yozing. *when* ni bir marta, *while* ni bir "
            "marta ishlating."),
    ("3.1", "Har bir iborani maʼnosi bilan moslashtiring: mos harfni tanlang."),
    ("3.2", "Hikoyani 3.1 dagi iboralar bilan toʻldiring."),
    ("3.3", "Muammo nima edi? Bitta soʻz yoki ibora yozing."),
    ("3.4", "Har bir gapdagi xatoni topib, toʻgʻrilang."),
    ("3.5", "Kuchsiz (*W*) mi yoki kuchli (*S*) mi? Tanlang, keyin har bir gapni ovoz chiqarib ayting."),
    ("3.6", "Sherigingizga yomon ketgan bir safaringiz haqida aytib bering. Bu boʻlimdagi beshta iborani "
            "ishlating."),
    ("4.1", "Tinglashdan oldin. Sizningcha, nima boʻlgan? Sherigingizga aytib bering."),
    ("4.2", "Bir marta tinglang. Har biri haqida qisqa qayd yozing."),
    ("4.3", "Yana tinglang va har bir qatorni toʻldiring."),
    ("4.4", "Tinglang va nima boʻlishiga eʼtibor bering."),
    ("4.5", "Har bir iborani ikki marta ayting — avval sekin, keyin tez."),
    ("4.6", "Voqealarni sodir boʻlgan tartibda raqamlang, 1–6."),
    ("4.7", "Gapiruvchi nima demoqchi? *A* yoki *B* ni tanlang."),
    ("5.1", "Tinglang va toʻgʻri javobni tanlang."),
    ("5.2", "▲ belgisi turgan joy uchun *and*, *but*, *so*, *because* yoki *when* ni tanlang."),
    ("5.3", "Har bir juftlikni ikki marta bogʻlang — bir marta *so* bilan, bir marta *because* bilan."),
    ("5.4", "Namunaviy blog yozuvini oʻqing, keyin javob bering."),
    ("5.5", "Namuna haqidagi savollarga javob bering."),
    ("5.6", "Avval reja tuzing: ikki daqiqa, keyin yozing."),
    ("5.7", "Endi oʻz blog yozuvingizni yozing (120–150 soʻz). Taʼtil, yangi joydagi birinchi kun yoki "
            "yaqinda borgan joyingizni tanlang."),
]
for label, text in INSTRUCTIONS:
    h.say_also(label, text)

# ------------------------------------------ the explanations, told in Uzbek
h.goals([
    "*past continuous* ni fon uchun, *past simple* ni sodir boʻlgan voqea uchun ishlatishni",
    "*when* va *while* dan toʻgʻrisini tanlashni",
    "safardagi muammolarni tasvirlashni — kechikish, ish tashlash, buzilib qolish, adashib qolish",
    "kuchsiz aytilgan *was* va *were* ni eshitishni — va inkor baland aytilishini bilishni",
    "*and, but, so, because* va *when* bilan bogʻlangan sayohat blogini yozishni",
])
h.retell("KEY WORDS", "KALIT SOʻZLAR", [
    "**a delay**  kechikish — rejadagidan kechroq sodir boʻlish",
    "**to break down**  buzilib qolmoq (mashina, avtobus)",
    "**a lift**  birovning mashinasida tekin olib borish",
    "**a platform**  poyezdga chiqish uchun turiladigan joy, platforma",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — PAST CONTINUOUS", [     # the first of the two
    "**Past continuous** — oʻtmishdagi uzoqroq davom etgan harakat. Odatda uni *past simple* "
    "dagi qisqaroq harakat boʻlib qoʻyadi.",
    "[[SHAKLI]] *was / were* + feʼl + *-ing*. *It was raining. · All the other passengers were "
    "waiting for me.* · Inkor: *It wasn't raining.* · Savol: *Was it raining?*",
    "[[→]] **Uzun harakat birinchi boshlanadi.** *I was reading my book when a flight attendant "
    "spoke to me.* Avval oʻqish boshlangan, gapirish uni boʻlgan.",
    "[[A]] **Baʼzan uzun harakat qisqasi sababli TOʻXTAYDI.** *I was running for the bus when my "
    "bag opened.* Yugurish toʻxtadi.",
    "[[B]] **Baʼzan u keyin ham DAVOM ETADI.** *I was reading my book when she spoke to me.* U "
    "gapirdi, oʻqish esa davom etdi.",
    "[[!]] **Bir vaqtda ikkita uzun harakat — ikkalasi ham continuous.** *While I was waiting, he "
    "was making tea.*",
    "[[WHEN / WHILE]] *when* odatda *past simple* bilan, *while* esa odatda *past continuous* "
    "bilan keladi. *…when the turbulence started. · While I was waiting…*",
])
h.retell("ERROR WARNING", "DIQQAT — KOʻP UCHRAYDIGAN XATOLAR", [
    "Toʻrtta xato uchraydi, ularning koʻpchiligi — birinchi ikkitasi:",
    "1 **Fon kerak boʻlgan joyda past simple.** ✗ *I read my book when she spoke to me.* → ✓ "
    "*I was reading my book when she spoke to me.* Birinchi gap kitobni u gapirgandan *keyin* "
    "oʻqiganingizni bildiradi.",
    "2 **Qisqa harakat uchun past continuous.** ✗ *The coach was breaking down.* → ✓ *The coach "
    "broke down.* Buzilib qolish bir soniyada sodir boʻladi, bir soat davom etmaydi.",
    "3 **they bilan was, he bilan were.** ✗ *They was waiting* → ✓ *They were waiting* · ✗ "
    "*He were driving* → ✓ *He was driving*",
    "4 **Holat feʼllari.** ✗ *I was knowing the answer* → ✓ *I knew the answer*. *know · want · "
    "like · understand · need* bu yerda ham continuous shaklda ishlatilmaydi.",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — SAFAR IBORALARI", [
    "[[SAFAR]] Boshidan oxirigacha: *set off* (yoʻlga chiqmoq) → *board a train or plane* (poyezd "
    "yoki samolyotga chiqmoq) → *take off* (samolyot uchib ketmoq) → *land* (samolyot qoʻnmoq) → "
    "*change* (bir poyezddan tushib, boshqasiga chiqmoq) → *get to a place* (yetib bormoq)",
    "[[YANA]] *travel around a country* (mamlakatni aylanib chiqmoq) · *hitchhike* (yoʻl chetida "
    "turib, tekin olib ketishlarini soʻramoq) · *give somebody a lift* (birovni mashinada "
    "boradigan joyiga olib bormoq)",
    "[[MUAMMOLAR]] Ish chappasiga ketganda: *miss a train · your car breaks down · there is "
    "turbulence during the flight · you have an accident · you get stuck in a traffic jam · there "
    "is something wrong with the plane · there is a strike · you get lost · there is a long queue · "
    "there is a delay*",
    "**Ehtiyot boʻling:** poyezdga ulgurmay qolsangiz, *miss a train* deysiz, *lose* emas. "
    "*Take off* — samolyotning ishi, yoʻlovchining emas.",
])
h.retell("PRONUNCIATION — WAS AND WERE", "TALAFFUZ — WAS VA WERE", [
    "**Tasdiq gap va savollarda ular kuchsiz aytiladi.** *It was raining* → /wəz/. · *We were "
    "driving* → /wə/. · *Were we driving fast?* → /wə/. Ular deyarli eshitilmaydi.",
    "**Inkorda ular kuchli aytiladi.** *It WASN'T raining* → /wɒznt/. · *We WEREN'T driving fast* "
    "→ /wɜːnt/.",
    "**Demak, baland aytilgani — inkor.** Bu oʻquvchilar kutganining aksi. U yerda aniq, urgʻuli "
    "soʻzni eshitsangiz, bu deyarli har doim *wasn't* yoki *weren't*.",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [
    "Gazetadagi sarlavha: *WOMAN ANGRY AFTER FLIGHT IN TOILET* — “Parvozni hojatxonada "
    "oʻtkazgan ayol gʻazabda”. Nima boʻlganini ayolning oʻzi aytib berishini eshitasiz.",
    "Agar sinfingizda audio boʻlsa, bu 2B yozuvi. Boʻlmasa, oʻqituvchingiz matnni oʻqib beradi — "
    "topshiriqlar bir xil.",
])
h.retell("WHY YOU DIDN'T HEAR IT", "NEGA ESHITMADINGIZ?", [
    "**Was va were deyarli yoʻqolib ketadi.** *I was reading* → /aɪwəzriːdɪŋ/ — ikki urgʻuli "
    "tovush orasida bitta kuchsiz tovush. Oʻquvchilar *reading* ni eshitib, hozirgi zamonni "
    "yozib qoʻyadi.",
    "**Was keyingi soʻzga qoʻshilib ketadi.** *was a* → /wəzə/ · *were all* → /wərɔːl/ · *was in* "
    "→ /wəzɪn/. *-ing* ga quloq soling: yordamchi feʼl uning oldida baribir bor — eshitsangiz ham, "
    "eshitmasangiz ham.",
])
h.retell("LISTENING INTO WRITING", "TINGLASHDAN YOZISHGA", [
    "Avval Perudan Avstraliyaga olti oyga uchib ketayotgan **Lucila** ning Sidneyda yashaydigan "
    "dugonasi **Katie** bilan suhbatini tinglang.",
])
h.retell("LINKING WORDS", "BOGʻLOVCHI SOʻZLAR", [
    "Blogni beshta kichik soʻz bogʻlab turadi. Har birining oʻz vazifasi bor:",
    "[[AND]] oʻxshash fikr qoʻshadi. *They were very friendly and welcoming.*",
    "[[BUT]] boshqacha fikr qoʻshadi. *Some of them are expensive, but most are really cheap.*",
    "[[SO]] natijani bildiradi. *I slept most of the way, so I'm not tired.*",
    "[[BECAUSE]] sababni bildiradi. *You can't bring fresh fruit because it could carry diseases.*",
    "[[WHEN]] ikki narsa bir vaqtda yoki biri ikkinchisidan keyin darhol sodir boʻladi. *When I got "
    "off the plane, the first thing I noticed was how organised everything is.*",
    "**So va because bir-biriga teskari.** *It was raining, so we stayed in.* · *We stayed in "
    "because it was raining.* Faktlar bir xil, tartibi teskari. Ularni almashtirib qoʻyish — bu "
    "darsdagi eng koʻp uchraydigan xato.",
])
h.retell("CHECK BEFORE YOU HAND IT IN", "TOPSHIRISHDAN OLDIN TEKSHIRING", [
    "{box}  Toʻrtta xatboshi.   {box}  Beshala bogʻlovchi soʻz, har biri oʻz vazifasida.   "
    "{box}  *so* va *because* toʻgʻri tartibda.",
    "{box}  Fon uchun ikkita *past continuous* feʼl, sodir boʻlgan voqealar uchun *past simple*.   "
    "{box}  U yerda boʻlmagan odam taxmin qila olmaydigan bitta tafsilot.",
    "{box}  Shunchaki *that's all* bilan emas, oldinga qaraydigan gap bilan tugatdim.   "
    "{box}  Soʻzlar soni: {box}",
])
h.one_per_line("TOPSHIRISHDAN OLDIN TEKSHIRING", None, at="box")
h.retell_cells({
    "Past simple — the short, finished action": "Past simple — qisqa, tugallangan harakat",
    "Past continuous — the longer background": "Past continuous — uzoqroq davom etgan fon",
    "What is written": "Yozilishi", "What you hear": "Eshitilishi", "Why": "Nega",
    "was has no vowel of its own": "<i>was</i> ning oʻz unlisi yoʻq",
    "were all becomes one sound": "<i>were all</i> bitta tovushga aylanadi",
    "the negative is stressed": "inkor urgʻu oladi",
    "four words, two beats": "toʻrt soʻz, ikki urgʻu",
})

# ------------------------------------------------------------------ the key
K = {}
STORY = {"P": "Platform", "S": "Stranger", "U": "The push"}
for n, a in enumerate("SUPSUP", 1):
    K[("1.2", n, 1)] = choose(["P", "S", "U"], a, labels=STORY)
for n in (1, 2, 3, 4):
    K[("1.3", n, 1)] = choose(["A", "B", "C"], "B")
for n, a in enumerate(["break down/breaks down/broke down", "refuse/refused", "climb/climbing"], 1):
    K[("1.4", n, 1)] = Q(a)
K[("1.5", 1, 1)] = own()                          # any six, with the reason: his to read
for n in (1, 2, 3):
    K[("1.6", n, 1)] = own()
for n, a in enumerate(["was raining", "were waiting", "was reading", "was sitting",
                       "weren't driving/were not driving"], 1):
    K[("2.1", n, 1)] = Q(a)
K[("2.1", 6, 1)] = Q("Were")
K[("2.1", 6, 2)] = Q("travelling/traveling")
for n, parts in enumerate([
        ["was leaving", "realised/realized"],
        ["was travelling/was traveling", "lost"],
        ["was running", "opened", "fell"],
        ["was driving", "stopped"],
        ["stole", "was standing"]], 1):
    for k, a in enumerate(parts, 1):
        K[("2.2", n, k)] = Q(a)
DONE = {"S": "S · stopped", "C": "C · continued"}
# as numbered: 1 running, 2 reading, 3 driving, 4 raining
for n, a in enumerate("SCSC", 1):
    K[("2.3", n, 1)] = choose(["S", "C"], a, labels=DONE)
for n, a in enumerate(["while", "when", "when", "while"], 1):
    K[("2.4", n, 1)] = choose(["when", "while"], a)
TICKED = "✓/correct/tick"
for n, a in zip(range(2, 9), [
        "The coach broke down on the mountain road/The coach broke down/broke down",
        "They were waiting for me at the station/They were waiting/were waiting",
        "He was driving too fast/He was driving/was driving",
        TICKED,
        "I knew the answer immediately/I knew the answer/knew",
        TICKED,
        "We were travelling around Europe last year/We were traveling around Europe last year/"
        "We were travelling/were travelling"]):
    K[("2.5", n, 1)] = fix(a)
for n, a in enumerate(["was", "was waiting", "weren't talking/were not talking", "were standing",
                       "stopped", "asked", "didn't want/did not want", "knew", "got", "drove",
                       "refused", "was driving", "told"], 1):
    K[("2.6", n, 1)] = Q(a)
for n in (1, 2, 3, 4):                            # any past simple action: his to read
    K[("2.7", n, 1)] = own()
K[("2.8", 1, 1)] = own()
for n, a in enumerate("dcegfhab", 1):
    K[("3.1", n, 1)] = choose(ENDS, a)
for n, a in enumerate(["travelled around/traveled around", "set off", "took off", "landed",
                       "hitchhiked", "gave us a lift", "boarded", "changed", "got to"], 1):
    K[("3.2", n, 1)] = Q(a)
for n, a in enumerate([
        "turbulence/there was turbulence",
        "a traffic jam/traffic jam/stuck in a traffic jam/we got stuck in a traffic jam/they got stuck in a traffic jam",
        "the car broke down/car broke down/broke down/a breakdown/breakdown",
        "they missed the train/we missed the train/missed the train",
        "a strike/strike/there was a strike",
        "they got lost/we got lost/got lost/lost"], 1):
    K[("3.3", n, 1)] = Q(a)
for n, a in enumerate([
        "I missed my train this morning/I missed my train/missed my train/missed",
        "The plane took off at six/Our plane took off at six/The plane took off",
        "The car broke down on the motorway/The car broke down/broke down",
        "There was a big queue at the ticket office, so we waited an hour/"
        "There was a big queue at the ticket office/at the ticket office"], 1):
    K[("3.4", n, 1)] = write(a)
LOUD = {"W": "Weak", "S": "Strong"}
# as numbered: 1 It was raining 2 It wasn't raining 3 Was it raining? 4 We were driving fast
# 5 We weren't driving fast 6 Were we driving fast?
for n, a in enumerate("WSWWSW", 1):
    K[("3.5", n, 1)] = choose(["W", "S"], a, labels=LOUD)
for n in range(1, 6):                             # notes while listening: his to read
    K[("4.2", n, 1)] = own()
for n, a in enumerate(["was raining", "was waiting/were waiting", "was reading", "was sitting",
                       "applauded/clapped"], 1):
    K[("4.3", n, 1)] = Q(a)
# as numbered: 1 argued 2 applauded 3 toilet 4 raining 5 spoke 6 boarded - in the order they happened
for n, a in enumerate("264153", 1):
    K[("4.6", n, 1)] = number(a)
for n in (1, 2, 3):
    K[("4.7", n, 1)] = choose(["A", "B"], "B")
for n, (opts, a) in enumerate([
        (["at five", "after six o'clock"], "after six o'clock"),
        (["the airport", "the train station"], "the airport"),
        (["too tired to enjoy", "excited by"], "too tired to enjoy"),
        (["similar to", "different from"], "different from"),
        (["her whole trip", "a short time"], "a short time")], 1):
    K[("5.1", n, 1)] = choose(opts, a)
LINKS = ["and", "but", "so", "because", "when"]
for n, a in enumerate(["so", "when", "so", "but", "because", "when", "because", "but"], 1):
    K[("5.2", n, 1)] = choose(LINKS, a)
K[("5.3", 1, 1)] = write("It was raining, so we stayed in the hotel")
K[("5.3", 1, 2)] = write("We stayed in the hotel because it was raining")
K[("5.3", 2, 1)] = write("The train was cancelled, so we took a taxi/The train was canceled, so we took a taxi")
K[("5.3", 2, 2)] = write("We took a taxi because the train was cancelled/We took a taxi because the train was canceled")
for n in (1, 2, 3, 4):
    K[("5.5", n, 1)] = own()
for n in (1, 2, 3, 4):                            # a plan: notes, not the work
    K[("5.6", n, 1)] = note()
K[("5.7", 20, 1)] = own(control="essay")
for n in range(1, 8):                             # the checklist
    K[("5.7", n, 1)] = tick()
K[("5.7", 8, 1)] = own(control="number")          # Words: ...

if __name__ == "__main__":
    data = h.build(K, "Pre-Intermediate", 2, "Unit 2B & 2D — Travel and tourism")
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "p02bd.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
