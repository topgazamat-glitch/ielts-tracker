"""E12AC Travel - Azamat's Elementary booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(E12AC Travel - answer key), joined box by box by hand - with one change:
1.2 item 2, "You live with a family", is job 3 in the text (the mountain
farm: "you live with a local family"), not job 2 as the key has it.

As with Beginner 3B, the booklet speaks Uzbek wherever it explains: every
explanation box, the goals, the "Why" column of the listening table, and a
line under every instruction. The English examples stay English, as do the
reading text, the dialogues and the exercises.

    python3 handouts/e12ac_digital.py            # writes handouts/e12ac.json, lists every box
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import (Handout, Q, choose, tick, own, write, fix, note, pair, report,   # noqa: E402
                     BLANK_TAG, plain)

DOCX = "~/Desktop/Handouts/A2 Elementary/E12AC Travel/E12AC Travel — handout (new design).docx"
TF = ["T", "F"]
JOB = {"1": "Job 1", "2": "Job 2", "3": "Job 3", "none": "None"}

h = Handout(DOCX)
TAGS = {int(m.group(1)): m.group(0) for m in BLANK_TAG.finditer(h.html)}

# ------------------------------------------------------------ 1 Reading
for n in (1, 2, 3):
    h.item_box("1.4", n, width="170px", where="leader")
h.leaders("1.5", "1.6  </span>", [(1, "95%", "Six geography words")])
for n in (1, 2, 3):
    h.item_box("1.6", n, where="leader")

# ------------------------------------------------------------ 2 Grammar
for n in range(2, 9):                            # 2.4: item 1 is the worked example
    h.item_box("2.4", n)
h.leaders("2.5", "PRONUNCIATION", [(20, "95%", "Your three sentences")])
LOUD = {}                                        # 2.6: tap the loudest word
for m in h._items("2.6"):
    n = int(m.group(3))
    LOUD[n] = [w.strip("?.!,") for w in re.sub(r"^\d+\s+", "", plain(m.group(4))).split()]
for n in sorted(LOUD):
    h.item_box("2.6", n)
h.grid_rows("2.7", [""])

# ------------------------------------------------------------ 3 Vocabulary
WORDS31 = h.sort_words("3.1", ["beach", "desert", "field", "forest", "glacier", "hill",
                               "island", "jungle", "lake", "mountain", "river", "woods"], "Water")
ODD = h.odd_one_out("3.3", why="Why? (Nega?)")
for n in (1, 2, 3, 4):
    h.item_box("3.5", n, where="leader")
h.leaders("3.6", "BEFORE YOU LISTEN", [(1, "95%", "Where you live, in three geography words")])

# ------------------------------------------------------------ 4 Listening
h.grid_rows("4.2", ["Emily:", "Chloe:"])
h.options_on_lines("4.6")
for n in (1, 2, 3):
    h.item_box("4.6", n)
for n in range(1, 7):
    h.item_box("4.7", n, placeholder="If it is false, correct it")
# 4.8: the paper's frame is two sentences, one to cross out - a phone gets the
# model and one box
h.replace_para(TAGS[83], '<p><span style="font-style:italic">I\'m going to …, because … '
                         '/ I\'m not going to …, because …</span></p>')
h.leaders("4.8", "SHOWING SURPRISE", [(20, "95%", "Would you take one? Why?")])

# ------------------------------------------------------ 5 Everyday English
ENDS = h.key_first("5.3")
for n in (1, 2, 3):
    h.item_box("5.6", n, where="leader")
h.leaders("5.7", "CHECK BEFORE", [(20, "95%", "Write your conversation here")])

# ------------------------------- every instruction, once more, in Uzbek
INSTRUCTIONS = [
    ("1.1", "Muhokama qiling. Taʼtilda siz uchun nima muhim? Yangi odamlar bilan tanishishmi? "
            "Mahalliy taommi? Yangi sport turimi? Hech narsa qilmaslikmi?"),
    ("1.2", "Qaysi ish? *Job 1*, *Job 2* yoki *Job 3* ni tanlang."),
    ("1.3", "Har bir kishi uchun eng mos ishni tanlang. Hech biri toʻgʻri kelmasa — *None*."),
    ("1.4", "Matndan shu maʼnodagi soʻzni toping."),
    ("1.5", "Matndan oltita geografiya soʻzini toping."),
    ("1.6", "Savollarga javob bering."),
    ("2.1", "*am*, *is* yoki *are* ni tanlang."),
    ("2.2", "Gapni *be going to* bilan yozing."),
    ("2.3", "Suhbatni qavs ichidagi soʻzlar bilan toʻldiring."),
    ("2.4", "Xatoni topib, toʻgʻrilang. IKKITA gap toʻgʻri — ular uchun *✓ It is correct* tugmasini bosing."),
    ("2.5", "Keyingi taʼtilingiz haqida uchta rost gap yozing."),
    ("2.6", "Tinglang va har bir gapdagi eng baland aytilgan soʻzni tanlang."),
    ("2.7", "Qisqa javob bering, keyin yana bitta gap qoʻshing."),
    ("2.8", "Sherigingizdan rejalari haqida soʻrang va javoblarini yozing. Buni sinfda bajarasiz."),
    ("3.1", "Har bir soʻzning guruhini tanlang: suv yoki muz, baland yoki tekis joy, daraxtlar."),
    ("3.2", "Har bir gapni geografiya soʻzi bilan toʻldiring."),
    ("3.3", "Qaysi soʻz boshqacha? Uni tanlang va nega ekanini yozing."),
    ("3.4", "Har bir soʻzda nechta boʻgʻin bor? Tanlang. Keyin urgʻuli boʻgʻinni ovoz chiqarib ayting."),
    ("3.5", "Har bir gapdagi xatoni topib, toʻgʻrilang."),
    ("3.6", "Yashaydigan joyingizni tasvirlang. Uchta geografiya soʻzini ishlating."),
    ("4.1", "Bir marta tinglang. Har bir kishi qaysi ishni xohlaydi? Tanlang."),
    ("4.2", "Yana tinglang va jadvalni toʻldiring."),
    ("4.3", "Yana bir marta tinglang va har bir qatorni toʻldiring."),
    ("4.4", "Tinglang va nima boʻlishiga eʼtibor bering."),
    ("4.5", "Har bir iborani ikki marta ayting — avval sekin, keyin tez."),
    ("4.6", "Gapiruvchi nima demoqchi? *A* yoki *B* ni tanlang."),
    ("4.7", "Toʻgʻri (*T*) yoki notoʻgʻri (*F*)? Notoʻgʻrilarini toʻgʻrilab yozing."),
    ("4.8", "Endi siz. Shu taʼtillardan birini tanlarmidingiz? Nega?"),
    ("5.1", "Hayratingizni bildiruvchi qisqa savolni yozing."),
    ("5.2", "Mehmonxonadagi suhbatni toʻldiring."),
    ("5.3", "Ikki qismni moslashtiring."),
    ("5.4", "Har bir gapda /t/ bor undoshlar guruhini toping va ovoz chiqarib ayting."),
    ("5.5", "Namunaviy suhbatni oʻqing. Keyin javob bering."),
    ("5.6", "Namuna haqidagi savollarga javob bering."),
]
for label, text in INSTRUCTIONS:
    h.say_also(label, text)
h.say_also("5.7", "Endi oʻz suhbatingizni yozing (10–12 qator). Mehmonxonaga kelasiz, joylashasiz, "
           "keyin sayohat haqida soʻraysiz. Bu boʻlimdagi kamida beshta iborani ishlating va bir "
           "marta hayratingizni bildiring.", after="You arrive at a hotel")

# ------------------------------------------ the explanations, told in Uzbek
h.goals([
    "*be going to* ni rejalar uchun ishlatishni — har safar uchala qismi bilan",
    "bu shaklni buzadigan beshta xatodan qochishni",
    "geografiya soʻzlarini birinchi boʻgʻinga urgʻu berib aytishni",
    "ikki kishining taʼtil rejalari haqidagi suhbatini tushunishni",
    "mehmonxonaga joylashishni, turistik maʼlumot soʻrashni va hayratni bildirishni",
])
h.retell("KEY WORDS", "KALIT SOʻZLAR", [
    "**accommodation**  yashash joyi, tunash uchun joy",
    "**local**  shu hududdan boʻlgan, mahalliy",
    "**scenery**  manzara, atrofda koʻrinadigan narsalar",
    "**pay**  ish uchun olinadigan pul, maosh",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — BE GOING TO", [     # the first of the two
    "**BE GOING TO** — oldindan qilingan reja uchun. Bu shunchaki fikr yoki orzu emas, gapirishdan "
    "*oldin* qabul qilingan qaror.",
    "[[+]] *be + going to +* feʼl. *I'm going to find out more about it. · She's going to leave her "
    "job. · We're going to stay in a hotel.*",
    "[[−]] Inkor qilish uchun feʼlni emas, **BE** ni inkor qiling. *I'm not going to go to university "
    "next year. · They aren't going to visit us.*",
    "[[?]] Savolda **BE** oldinga chiqadi. *You are going to do it.* → *Are you going to do it?* · "
    "*What are you going to do?* · *Is he going to come?*",
    "[[!]] Har doim uch qism: **be + going to + feʼlning oddiy shakli**. Oʻquvchilar koʻpincha "
    "bittasini — odatda oʻrtadagisini — tushirib qoldiradi.",
    "**Urgʻu qayerga tushadi.** *going to* ga emas — asosiy feʼlga. *What are you going to DO? · "
    "I'm going to TRAVel.* Tez nutqda *going to* deyarli eshitilmaydi, shuning uchun uni "
    "eshitmaysiz.",
])
h.retell("ERROR WARNING", "DIQQAT — KOʻP UCHRAYDIGAN XATOLAR", [
    "1 **GOING ni tushirib qoldirmang.** ✗ *How are you to get to the airport?* → ✓ *How are you "
    "going to get to the airport?*",
    "2 **AM / IS / ARE ni tushirib qoldirmang.** ✗ *We going to go to the beach.* → ✓ *We are going "
    "to go to the beach.*",
    "3 **TO dan keyingi feʼlga -ing qoʻshilmaydi.** ✗ *I'm going to wearing my new shorts.* → ✓ "
    "*I'm going to wear my new shorts.* Bir gapda bitta -ing yetarli.",
    "4 **GO TO — bu BE GOING TO emas.** ✗ *I'm happy that I go to Finland.* → ✓ *I'm happy that "
    "I'm going to Finland.*",
    "5 **WILL bilan bir xil emas.** ✗ *I bought new boots because I will go hiking.* → ✓ "
    "*…because I'm going to go hiking.* Botinkani allaqachon sotib oldingiz — demak, reja oldindan "
    "bor edi. Bu *be going to*.",
])
h.retell("PRONUNCIATION", "TALAFFUZ — GOING TO", [
    "**GOING TO yoʻqolib ketadi.** Tez aytilsa, u /gənə/ ga aylanadi — urgʻusiz ikki kichik "
    "tovush. *I'm going to travel* → /aɪm gənə travl/.",
    "**Shuning uchun oxiridagi feʼlga quloq soling:** *travel · stay · look · do.* Feʼl baland "
    "aytiladi va aniq eshitiladigan yagona qism shu — rejani bilish uchun shuning oʻzi yetarli.",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — GEOGRAFIYA SOʻZLARI", [
    "[[SUV]] *a lake · a river · a waterfall · a beach · the coast · a glacier* (muzlik)",
    "[[BALAND VA TEKIS]] *a mountain · a hill · a field · the countryside · a desert* (suvsiz choʻl)",
    "[[DARAXTLAR]] *a forest · the woods* (kichikroq) *· a jungle / a rainforest* (issiq va nam)",
    "[[YANA BITTA]] *an island* — atrofi suv bilan oʻralgan quruqlik.",
    "**Adashtiriladigan ikki juftlik.** *A hill* kichik, *a mountain* katta. *The woods* kichik, "
    "*a forest* katta. *The coast* — quruqlik dengiz bilan tutashgan chiziq; *a beach* esa uning "
    "qumli bir boʻlagi.",
])
h.retell("PRONUNCIATION — WORD STRESS", "TALAFFUZ — SOʻZ URGʻUSI", [
    "Deyarli barcha geografiya soʻzlarida urgʻu **birinchi boʻgʻinga** tushadi. Bu juda qulay: "
    "uni qoida sifatida eslab qoling va faqat istisnolarni yodlang.",
    "[[BIRINCHI BOʻGʻIN]] *MOUN-tain · RIV-er · IS-land · DE-sert · FOR-est · JUN-gle · "
    "WA-ter-fall · COUN-try-side*",
    "[[BIR BOʻGʻINLI]] *lake · beach · hill · field · coast · woods* — bu yerda tanlash shart emas.",
    "**ISLAND ga ehtiyot boʻling:** *s* harfi oʻqilmaydi — /aɪlənd/. *DESERT* /DEZət/ — qumli "
    "choʻl; *dessert* /dɪZɜːT/ — ovqatdan keyingi shirinlik. Bitta harf, boshqa urgʻu — va ikki "
    "xil sayohat.",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [
    "Ikkita suhbat, ikkalasi ham bitta sayt haqida — *Work Around the World*. Birinchisida Emily "
    "oʻz rejasini Zoe bilan boʻlishadi. Ikkinchisida Chloe oʻz rejasini Frank bilan boʻlishadi.",
    "Agar sinfingizda audio boʻlsa, bu 12.03-trek. Boʻlmasa, oʻqituvchingiz matnni oʻqib beradi — "
    "topshiriqlar bir xil.",
])
h.retell("WHY YOU DIDN'T HEAR IT", "NEGA ESHITMADINGIZ?", [
    "**GOING TO hech qachon toʻliq aytilmaydi.** *I'm going to email* → /aɪm gənə iːmeɪl/. "
    "Oʻrtadagi ikki soʻz bitta tovushga aylanadi va hech biri urgʻu olmaydi.",
    "**Shuning uchun feʼllarni sanang.** Agar /gənə/ ga oʻxshash tovushdan keyin -ed ham, -s ham "
    "qoʻshilmagan feʼlni eshitsangiz, bu reja haqidagi gap. Savollarga javob berish uchun shuning "
    "oʻzi yetarli.",
])
h.retell("SHOWING SURPRISE", "HAYRATNI BILDIRISH", [
    "Kimdir sizga yangilik aytsa, ingliz tilida shunchaki *oh* deyilmaydi. Kichkina savol bilan "
    "javob beriladi — shu savol suhbatdoshingizga uni tinglayotganingizni bildiradi.",
    "[[OSON YOʻL]] *Really?* — har doim ishlaydi. Har qanday yangilikka shunday javob berish mumkin.",
    "[[YAXSHIROQ]] Gapdagi yordamchi feʼlni takrorlang. *I've won a competition.* → *Have you?* · "
    "*She's going to leave.* → *Is she?* · *They came yesterday.* → *Did they?*",
    "**Qanday tuziladi.** Suhbatdoshning gapidan yordamchi feʼlni oling (*have, is, did, can*) va "
    "*I* ni *you* ga almashtiring. Ikki soʻz — va siz darslikdagidek emas, tirik odamdek "
    "gapirasiz.",
    "**Ohangni koʻtaring.** Oxirida ovoz ancha koʻtariladi. Bir tekis aytilgan *Have you?* "
    "zerikkandek eshitiladi — siz aytmoqchi boʻlgan narsaning aksi.",
])
h.retell("CHECKING IN AT A HOTEL", "MEHMONXONAGA JOYLASHISH", [
    "Oltita ibora — qayerda tursangiz ham, har safar hammasini ishlatasiz.",
    "*I've got a reservation for a double room for two nights.*",
    "*Is breakfast included? · Is there a car park? · Is there wi-fi in the room? · Is there a "
    "safe in the room? · What time is checkout?*",
    "**Ehtiyot boʻling:** *Is breakfast included?* — *Is breakfast include?* emas. -ed soʻzning bir "
    "qismi, garchi deyarli eshitilmasa ham.",
])
h.retell("ASKING FOR TOURIST INFORMATION", "TURISTIK MAʼLUMOT SOʻRASH", [
    "Yana beshtasi — pastdagi qabulxona yoki burchakdagi turistik ofis uchun.",
    "*Can you help me? · Is there a city bus tour I can go on? · How much is it for a ticket? · "
    "Can I buy tickets here? · I'll have a ticket, please.*",
    "**Eng foydalisi — oxirgisi.** *I'll have a ticket, please* ingliz tilida “buni hozir sotib "
    "olaman” degani. *I want a ticket* xato emas, lekin shirinlik soʻrayotgan boladek eshitiladi.",
])
h.retell("PRONUNCIATION — CONSONANT CLUSTERS WITH T", "TALAFFUZ — T BILAN UNDOSHLAR GURUHI", [
    "Ingliz tilida soʻz oxirida bir nechta undosh ketma-ket keladi, /t/ esa koʻpincha ularning "
    "oʻrtasida boʻladi. Butun guruhni ayting — orasiga unli qoʻshmang.",
    "*next* /nekst/ · *tourist* /tʊərɪst/ · *left* /left/ · *tickets* /tɪkɪts/ · *nights* /naɪts/",
    "**Qochish kerak boʻlgan xato:** /neks-i-t/ yoki /lef-i-t/ demang — u yerda unli yoʻq. /t/ ni "
    "tez ayting, u deyarli eshitilmasin, lekin uni tashlab ham ketmang.",
])
h.retell("CHECK BEFORE YOU PRACTISE IT", "MASHQ QILISHDAN OLDIN TEKSHIRING", [
    "{box}  Bron qilganingizni aytdingiz.   {box}  Nonushta va chiqish vaqtini soʻradingiz.   "
    "{box}  Narxini va qayerdan joʻnashini soʻradingiz.",
    "{box}  *I'll have…, please* bilan tugatdingiz.   {box}  Kimdir hayratini faqat *Really?* bilan "
    "emas, qisqa savol bilan bildirdi.",
    "{box}  Qabulxona xodimi boshidan oxirigacha xushmuomala.   {box}  Qatorlar soni: {box}",
])
h.one_per_line("MASHQ QILISHDAN OLDIN TEKSHIRING", None, at="box")
# the tables that explain, in Uzbek too: a cell is matched by what it says,
# since Word splits a cell's words across several pieces of formatting
CELLS = {"Full form": "Toʻliq shakl", "Short form": "Qisqa shakl",
         "(no short form in a question)": "(savolda qisqa shakl yoʻq)",
         "not Yes, I'm.": "<i>Yes, I'm</i> deyilmaydi.",
         "What is written": "Yozilishi", "What you hear": "Eshitilishi", "Why": "Nega",
         "four words become two": "toʻrt soʻz ikkitaga aylanadi",
         "going to has no stress": "<i>going to</i> urgʻusiz aytiladi",
         "the NOT is loud": "<i>NOT</i> baland aytiladi",
         "are you almost vanishes": "<i>are you</i> deyarli eshitilmaydi"}
done = []


def uz_cell(m):
    text = plain(m.group(2))
    if text in CELLS:
        done.append(text)
        return '%s<p><span>%s</span></p></td>' % (m.group(1), CELLS[text])
    return m.group(0)


h.html = re.sub(r"(<td[^>]*>)((?:(?!<td|<table).)*?)</td>", uz_cell, h.html, flags=re.S)
if sorted(done) != sorted(CELLS):
    raise SystemExit("cells not found once each: %s" % sorted(set(CELLS) ^ set(done)))

# ------------------------------------------------------------------ the key
K = {}
# as numbered: 1 children 2 a family 3 a beach 4 hardest 5 most people 6 a boat
for n, a in enumerate("232321", 1):               # 2: "you live with a local family" is job 3
    K[("1.2", n, 1)] = choose(["1", "2", "3"], a, labels=JOB)
for n, a in enumerate(["1", "3", "2", "none"], 1):
    K[("1.3", n, 1)] = choose(["1", "2", "3", "none"], a, labels=JOB)
for n, a in enumerate(["accommodation", "scenery", "patience"], 1):
    K[("1.4", n, 1)] = Q(a)
K[("1.5", 1, 1)] = own()                          # any six real geography words: his to read
for n in (1, 2, 3):
    K[("1.6", n, 1)] = own()
for n, a in enumerate(["am", "is", "are", "are", "are", "is"], 1):
    K[("2.1", n, 1)] = choose(["am", "is", "are"], a)
for n, a in enumerate([
        "I'm going to find out more about it/I am going to find out more about it",
        "She isn't going to go to university/She is not going to go to university/"
        "She's not going to go to university",
        "What are you going to do next year",
        "We're going to spend two months travelling/We are going to spend two months travelling/"
        "We're going to spend two months traveling/We are going to spend two months traveling",
        "They aren't going to stay in a hotel/They are not going to stay in a hotel/"
        "They're not going to stay in a hotel",
        "How long are you going to stay"], 1):
    K[("2.2", n, 1)] = write(a)
for n, a in enumerate(["are you going to do", "'m going to spend/am going to spend",
                       "'m going to go/am going to go", "are you going to pay",
                       "'m not going to pay/am not going to pay", "'m going to work/am going to work",
                       "are you going to do", "'m going to look/am going to look",
                       "'m not going to do/am not going to do"], 1):
    K[("2.3", n, 1)] = Q(a)
TICKED = "✓/correct/tick"
for n, a in zip(range(2, 9), [
        "We are going to go to the beach/We're going to go to the beach",
        "I'm going to wear my new shorts/I am going to wear my new shorts",
        "I'm happy that I'm going to Finland next week/I'm happy that I am going to Finland next week/"
        "I am happy that I'm going to Finland next week/I am happy that I am going to Finland next week",
        "I bought new boots because I'm going to go hiking/I bought new boots because I am going to go "
        "hiking/because I'm going to go hiking/because I am going to go hiking",
        TICKED,
        "Yes, I am",
        TICKED]):
    K[("2.4", n, 1)] = fix(a)
for n in (1, 2, 3, 4):
    K[("2.5", n, 1)] = own(control=None)
K[("2.5", 20, 1)] = own()
for n, a in zip(sorted(LOUD), ["do", "travel", "leave", "stay"]):
    K[("2.6", n, 1)] = choose(LOUD[n], a)
for n in (1, 2, 3, 4):
    K[("2.7", n, 1)] = own()
for n in (1, 2, 3, 4):                            # ask a partner: in class
    K[("2.8", n, 1)] = pair()
GROUP = {"water": "Water / ice", "land": "High / flat", "trees": "Trees"}   # one line on a phone
SORT = {"beach": "water", "glacier": "water", "lake": "water", "river": "water",
        "desert": "land", "field": "land", "hill": "land", "island": "land/water", "mountain": "land",
        "forest": "trees", "jungle": "trees", "woods": "trees"}   # island: both, says his key
for n, w in enumerate(WORDS31, 1):
    K[("3.1", n, 1)] = choose(["water", "land", "trees"], SORT[w], labels=GROUP)
for n, a in enumerate(["woods/countryside/the woods/the countryside", "beach", "hill/mountain",
                       "island", "desert", "jungle/rainforest"], 1):
    K[("3.2", n, 1)] = Q(a)
for n, a in zip((1, 2, 3, 4), ["field", "hill", "mountain", "river"]):
    K[("3.3", n, 1)] = choose(ODD[n], a)
    K[("3.3", n, 2)] = own()
# as numbered: 1 mountain 2 island 3 waterfall 4 countryside 5 desert 6 jungle
for n, a in enumerate("223322", 1):
    K[("3.4", n, 1)] = choose(["1", "2", "3"], a)
for n, a in enumerate([
        "We stayed in a small hotel on the coast of Italy/on the coast of Italy/the coast of Italy/coast",
        "There are a lot of trees — it's a big forest/There are a lot of trees, it's a big forest/"
        "There are a lot of trees. It's a big forest/it's a big forest/it is a big forest/a big forest/forest",
        "We climbed a very high mountain/a very high mountain/mountain/"
        "We climbed a very high mountain. It was 3,000 metres",
        "The Sahara is the biggest desert in the world/the biggest desert in the world/"
        "the biggest desert/desert"], 1):
    K[("3.5", n, 1)] = write(a)
K[("3.6", 1, 1)] = own()
for n, a in zip((1, 2), ["3", "2"]):              # Emily: the mountains; Chloe: the beach
    K[("4.1", n, 1)] = choose(["1", "2", "3"], a, labels=JOB)
for n in range(1, 7):
    K[("4.2", n, 1)] = own()
for n, a in enumerate(["are you going to", "'m not going to/am not going to", "'m going to/am going to",
                       "'m going to/am going to", "'m going to/am going to"], 1):
    K[("4.3", n, 1)] = Q(a)
for n in (1, 2, 3):
    K[("4.6", n, 1)] = choose(["A", "B"], "B")
for n, a in enumerate("FFTFFT", 1):
    K[("4.7", n, 1)] = choose(TF, a)
    K[("4.7", n, 2)] = note()
K[("4.8", 20, 1)] = own()
# as numbered: 1 won 2 leave 3 went 4 Georgian 5 travel 6 didn't like
for n, a in enumerate(["Have you", "Is she", "Did they", "Can he", "Are you", "Didn't you"], 1):
    K[("5.1", n, 1)] = Q(a + "/Really")           # Really? is accepted; the key pushes for the copy
for n, a in enumerate(["got", "included", "there", "time"], 1):
    K[("5.2", n, 1)] = Q(a)
for n, a in enumerate("cdaeb", 1):
    K[("5.3", n, 1)] = choose(ENDS, a)
K[("5.6", 1, 1)] = own()
K[("5.6", 2, 1)] = write("I'll have a ticket, please/I'll have a ticket then, please/"
                         "I'll have a ticket/I will have a ticket, please")
K[("5.6", 3, 1)] = write("Can I pay by card/And can I pay by card")
K[("5.7", 20, 1)] = own(control="essay")
for n in range(1, 8):                             # the checklist
    K[("5.7", n, 1)] = tick()
K[("5.7", 8, 1)] = own(control="number")          # Lines: ...

if __name__ == "__main__":
    data = h.build(K, "Elementary", 12, "Unit 12A & 12C — Travel")
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "e12ac.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
