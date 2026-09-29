"""Pre-Intermediate Unit 4 ASP+RP homework - done on a phone.

Azamat's homework pack (Pre-intermediate Unit 4 ASP+RP - HOMEWORK - STUDENT,
and its ANSWER KEY) is not drawn in the booklet style: its gaps are dotted
text and it has no section bars, so the page reader finds nothing in it to
answer. This writes it out again in the booklet's own markup - the same
section bars, exercise numbers and panels - so it works like every other
handout: four parts, one at a time, checked, then the next.

The four parts follow the pack's own seam. Each sheet has parts A-C, which
the paper lets students check themselves against a SELF-CHECK box, and
parts D-E, which the teacher marks. So: Sheet 1 A-C, Sheet 1 D-E, Sheet 2
A-C, Sheet 2 D-E. The self-check boxes go - the site checks instead, and a
box of answers on the same page would give them away.

Explanations are in Uzbek (the two grammar boxes, the two strategy boxes,
the note about the audio, the goals), with the English examples kept, and
every instruction has a line in Uzbek under it. The texts to read, the
exercises and the model language stay English. Where the key gives a model
rather than one answer - the definitions with MEANS, the notes on a talk,
the writing - the box is the teacher's to read.

    python3 handouts/asrp4_digital.py            # writes handouts/asrp4.json, lists every box
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import digital                                                          # noqa: E402
from digital import Q, choose, own, write, report, told, plain           # noqa: E402

TEAL, DEEP, SOFT = "127D80", "0B5456", "F2F8F8"


def md(text):
    """English text with **bold** and *italic*, escaped."""
    t = html.escape(text, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r'<span style="font-weight:700">\1</span>', t)
    return re.sub(r"\*(.+?)\*", r'<span style="font-style:italic">\1</span>', t)


def bar(n, name, what):
    return ('<table class="bk"><tr><td style="vertical-align:top;background:#%s;border-top:0;'
            'border-bottom:0;border-left:0;border-right:0"><p style="text-align:center;margin-bottom:0px">'
            '<span style="font-weight:700;color:#FFFFFF;font-size:13pt">%d</span></p></td>'
            '<td style="vertical-align:top;border-top:0;border-bottom:1px solid #%s;border-left:0;'
            'border-right:0"><p style="margin-bottom:0px"><span style="font-weight:700;color:#%s;'
            'font-size:12.5pt">%s  ·  %s</span></p></td></tr></table>'
            % (TEAL, n, TEAL, DEEP, html.escape(name), html.escape(what)))


def ex(label, text):
    return ('<p style="margin-top:10px;margin-bottom:5px;padding-left:32px"><span style="font-weight:700;'
            'color:#%s;font-size:12pt">%s  </span><span style="font-weight:700;color:#1A1A1A;'
            'font-size:11.5pt">%s</span></p>' % (TEAL, label, md(text)))


def note(text):
    """A line of the paper's own under an instruction - a task to follow."""
    return ('<p style="margin-top:0px;margin-bottom:6px;line-height:1.35;padding-left:32px">'
            '<span style="font-style:italic;color:#1A1A1A;font-size:11.5pt">%s</span></p>' % md(text))


BOX = {}


def box(label, n, width="130px", hint=""):
    return "{{box:%s:%d:%s:%s}}" % (label, n, width, hint)


def item(h, label, n, text, *boxes):
    """One numbered line; each {} in the text is the next of `boxes`."""
    h.texts[(label, n)] = plain(md(text.replace("{}", "……")))
    parts = md(text).split("{}")
    out = parts[0]
    for b, tail in zip(boxes, parts[1:]):
        out += b + tail
    return ('<p data-item="%s:%d" style="margin-bottom:4.75px;line-height:1.33333;padding-left:48px">'
            '<span style="color:#6E6E6E;font-size:9.5pt">%d  </span><span style="color:#1A1A1A;'
            'font-size:11.5pt">%s</span></p>' % (label, n, n, out))


def panel(title, paras, colour=TEAL, ground=SOFT):
    head = ('<table class="bk"><tr><td style="vertical-align:top;background:#%s;border-top:1px solid #%s;'
            'border-bottom:1px solid #%s;border-left:1px solid #%s;border-right:1px solid #%s">'
            '<table class="bk"><tr><td style="vertical-align:top;background:#%s;border-top:0;border-bottom:0;'
            'border-left:0;border-right:0"><p style="margin-bottom:0px"><span style="font-weight:700;'
            'color:#FFFFFF">%s</span></p></td></tr></table>'
            % (ground, colour, colour, colour, colour, colour, html.escape(title)))
    return head + "".join(told(p) for p in paras) + "</td></tr></table>"


def prose(text, lead=None, bold=False, italic=False):
    style = "color:#1A1A1A;font-size:11.5pt" + (";font-weight:700" if bold else "") + \
        (";font-style:italic" if italic else "")
    body = '<span style="%s">%s</span>' % (style, html.escape(text, quote=False))
    if lead:
        body = ('<span style="font-weight:700;color:#1A1A1A;font-size:11.5pt">%s</span>'
                % html.escape(lead, quote=False)) + body.replace(">", ">  ", 1)
    return '<p style="margin-top:0px;margin-bottom:3.7px;line-height:1.25">%s</p>' % body


def key_list(pairs):
    """The endings or meanings to choose from, as a key above the items."""
    return ('<table class="bk"><tr><td style="vertical-align:top;background:#%s;border-left:3px solid #%s">'
            % (SOFT, TEAL)
            + "".join('<p style="margin:0"><span style="font-weight:700;color:#%s">%s</span>  %s</p>'
                      % (TEAL, l, html.escape(t, quote=False)) for l, t in pairs)
            + "</td></tr></table>")


h = digital.Handout.__new__(digital.Handout)
h.blanks, h.removed, h.texts, h.hints = [], set(), {}, {}
W = "95%"
P = []                                                  # the page, piece by piece

# ------------------------------------------------------------------ the cover
P.append('<p><span>UNIT 4  ·  ACADEMIC SKILLS PLUS &amp; READING PLUS</span></p>'
         '<p><span>Rituals and the city</span></p>'
         '<p><span>Unit 4 homework  ·  Selfies and social rituals  ·  The other side of the city</span></p>'
         '<table class="bk"><tr><td><p><span>You will learn to</span></p>'
         + "".join('<p><span>—  </span>%s</p>' % told(g, bare=True) for g in (
             "soʻzga *word + be + umumiy ot + which / that* skeleti bilan taʼrif berishni",
             "taʼrif kelayotganini bildiruvchi iboralarni tanishni — *which means, in other words, by this I mean*",
             "taqdimotda asosiy fikrni tafsilotdan ajratishni",
             "blogdagi *going to*, *present continuous* va *will* reja haqida nima deyishini tushunishni",
             "matndan kerakli maʼlumotni tez topishni — *scanning*",
             "oʻz madaniyatingizdagi bir marosimga taʼrif va blog uchun post yozishni"))
         + "</td></tr></table>")

# ------------------------------------------------ 1 Sheet 1, A-C: defining
P.append(bar(1, "Defining", "chunks, definitions, main points"))
P.append(panel("TINGLASH SHART EMAS", [
    "Bu uy vazifasi uchun audio kerak emas. 1- va 2-qismlar Denizning selfi haqidagi taqdimotiga "
    "asoslangan, lekin ular oʻrgatadigan hamma narsa — taʼriflovchi iboralar, asosiy fikr va tafsilot — "
    "shu sahifada bor, 2-qismda esa yana bir taqdimot matn shaklida berilgan. 3- va 4-qismlarga audio "
    "umuman kerak emas.",
]))
P.append(ex("1.1", "Chunks from the presentation. Complete each phrase with ONE word."))
for n, text in enumerate([
        "A cup of tea in bed before I get up is part of my morning {} .",
        "Rituals are {} from one generation to the next.",
        "Young people take selfies at weddings — it has become a {} ritual.",
        "Think about the way people {} for the camera.",
        "People always want positive social media {} .",
        "A selfie can create a {} impression — a life that is not the real one.",
        "Selfies are a way to show you {} to a group.",
        "Showing a picture of yourself is not a new idea — think of old self-{} ."], 1):
    P.append(item(h, "1.1", n, text, box("1.1", n)))
P.append(panel("TUSHUNTIRISH — TAʼRIF QANDAY TUZILADI", [
    "Deniz oʻn daqiqalik taqdimotida besh-olti soʻzga taʼrif beradi va har bir taʼrifning skeleti bir "
    "xil. Skeletni oʻrganib olsangiz, istalgan narsaga taʼrif bera olasiz.",
    "[[1]] **Soʻz + BE + umumiy ot + WHICH / THAT + u nima qiladi.** *A ritual is an activity that is "
    "always done in the same way. · Selfies are photos which you take of yourself.* Umumiy ot "
    "(*activity, photo, person, place*) — oʻquvchilar eng koʻp unutadigan qism; usiz gap buziladi: ✗ "
    "*A ritual is always done the same way.*",
    "[[2]] **Yoki soʻz + MEANS + gap.** *Narcissistic means we love ourselves too much. · To pose means "
    "to hold your body in a special way for a photo.* *Means* dagi *-s* ga eʼtibor bering — u hech "
    "qachon tushib qolmaydi.",
    "[[3]] **Taʼrif kelayotganini bildiruvchi signallar.** *What exactly do we mean by…? · …, which "
    "means… · …, in other words, … · By this I mean…* Bular — gapiruvchi siz bu soʻzni bilmasligingiz "
    "mumkin deb oʻylaganining belgisi.",
    "**Qochish kerak boʻlgan xato:** ✗ *A ritual is when you do something every day.* *When* — ot emas. "
    "Avval umumiy otni ayting — *a ritual is a habit that…* — shunda gap hikoya emas, taʼrif boʻladi.",
]))
P.append(ex("1.2", "Complete each definition with the general noun and *which / that*."))
P.append(item(h, "1.2", 1, "A stranger is a {} you don't know.", box("1.2", 1, "170px")))
P.append(item(h, "1.2", 2, "A generation is a {} of people {} were born at about the same time.",
              box("1.2", 2, "130px"), box("1.2", 2, "100px")))
P.append(item(h, "1.2", 3, "A pose is the {} you hold your body for a photo.", box("1.2", 3, "170px")))
P.append(item(h, "1.2", 4, "Feedback is {} people tell you about your work.", box("1.2", 4, "170px")))
P.append(item(h, "1.2", 5, "A self-portrait is a {} an artist paints of himself or herself.", box("1.2", 5, "170px")))
P.append(item(h, "1.2", 6, "A wedding is a {} two people get married.", box("1.2", 6, "170px")))
P.append(ex("1.3", "Rewrite each one with MEANS."))
for n, (word, start) in enumerate([("inherited", "Inherited"), ("upload", "To upload"),
                                   ("narcissistic", "Narcissistic"), ("fit in", "To fit in")], 1):
    P.append(item(h, "1.3", n, "%s → %s {}" % (word, start),
                  box("1.3", n, W, "means …")))
P.append(ex("1.4", "Find and correct the mistake."))
for n, text in enumerate(["A ritual is when you always do something the same way.",
                          "A selfie is a photo who you take of yourself.",
                          "Culture mean the habits and beliefs of a group of people.",
                          "Feedback is a people tell you what they think."], 1):
    P.append(item(h, "1.4", n, text + " {}", box("1.4", n, W, "Write the correct sentence")))
P.append(panel("STRATEGIYA — ASOSIY FIKR VA TAFSILOT", [
    "Taqdimotda ikki xil gap boʻladi va ularni turlicha yozib olish kerak. **Asosiy fikrlar** — "
    "taqdimot qurilgan olti-yetti gʻoya. **Tafsilotlar** — har biriga ilashgan narsalar: misol, raqam, "
    "ism, iqtibos.",
    "[[QANDAY ESHITILADI]] Asosiy fikr odatda boʻlim boshida keladi, sekin aytiladi va koʻpincha signal "
    "soʻz bilan boshlanadi — *First…, Another thing…, Let's think about…*. Tafsilot undan keyin, tezroq "
    "keladi va koʻpincha *for example, such as, according to* yoki shunchaki raqam bilan boshlanadi.",
    "[[QAYDLARDA]] Asosiy fikr chapda, tafsilotlar uning ostida, ichkariroqda. Faqat asosiy fikrlardan "
    "iborat sahifa — bu xulosa. Faqat tafsilotlardan iborat sahifa — hech kimga foydasi yoʻq faktlar "
    "roʻyxati.",
    "[[SINOV]] Tafsilotlarni yoping — taqdimot baribir tushunarli. Asosiy fikrlarni yoping — "
    "tushunarsiz boʻlib qoladi.",
]))
P.append(ex("1.5", "Main point (M) or detail (D)?"))
for n, text in enumerate(["A million selfies are taken every day.",
                          "Rituals pass from one generation to the next.",
                          "Browne says this in *Profiles of Popular Culture*, 2005.",
                          "The way you pose is part of the ritual.",
                          "Selfies are a way of saying *this is me*.",
                          "Most people who take selfies are between 18 and 24."], 1):
    P.append(item(h, "1.5", n, text + " {}", box("1.5", n)))

# ------------------------------------------- 2 Sheet 1, D-E: a new talk
P.append(bar(2, "Presentation", "why do we shake hands?"))
P.append(ex("2.1", "A new presentation excerpt. Read it, then do the tasks."))
P.append(prose("WHY DO WE SHAKE HANDS?", bold=True))
P.append(prose("From a student presentation on greeting rituals.", italic=True))
for para in [
        "Today I want to talk about a ritual so ordinary that nobody notices it: the handshake. What "
        "exactly do we mean by a ritual here? I mean an action that has a fixed form — you do it the same "
        "way every time — and a social meaning that everybody in the group understands.",
        "First, where does it come from? Nobody knows for certain, but the most popular theory is that it "
        "started as a way of showing you had no weapon. An open right hand, in other words, means I'm not "
        "going to hurt you. There's a carving from Greece, from about 500 BC, which shows two soldiers "
        "doing exactly this.",
        "Second, the handshake has rules, and the rules are inherited — by this I mean that nobody teaches "
        "them in a classroom; you copy the adults around you. In most of Europe a handshake should be "
        "firm, which means strong but not painful, and it should last about two seconds. In some parts of "
        "Asia a softer, longer handshake is polite, and a firm one is rude. Same action, opposite meanings.",
        "Finally, the handshake is changing. After 2020 many people stopped shaking hands and started other "
        "things — a nod, a touch of the elbow, a hand on the heart. Some researchers think the handshake "
        "will come back completely. Others think a new ritual will replace it. What do you think?"]:
    P.append(prose(para))
P.append(ex("2.2", "Find and write down:"))
P.append(item(h, "2.2", 1, "the THREE main points, in the speaker's words: {}", box("2.2", 1, W)))
P.append(item(h, "2.2", 2, "one detail for the first main point: {}", box("2.2", 2, W)))
P.append(item(h, "2.2", 3, "one detail for the second main point: {}", box("2.2", 3, W)))
P.append(item(h, "2.2", 4, "the word the speaker defines with *in other words*: {} and the one defined "
                           "with *which means*: {}", box("2.2", 4, "170px"), box("2.2", 4, "130px")))
P.append(ex("2.3", "Now answer."))
P.append(item(h, "2.3", 1, "Which two signposts introduce main points 1 and 2? {} and {}",
              box("2.3", 1, "110px"), box("2.3", 1, "110px")))
P.append(item(h, "2.3", 2, "Why does the speaker define *ritual* again at the start, when Deniz already "
                           "defined it? {}", box("2.3", 2, W)))
P.append(item(h, "2.3", 3, "*Same action, opposite meanings.* Is this a main point or a detail? Why? {}",
              box("2.3", 3, W)))
P.append(item(h, "2.3", 4, "The speaker ends with a question. Is it a main point? What is it for? {}",
              box("2.3", 4, W)))
P.append(ex("2.4", "Define a ritual from your own culture (80–100 words)."))
P.append(note("Choose a ritual your family or your country has — a greeting, a meal, a holiday custom, "
              "something you do before an exam. Write one paragraph that (1) names it and defines it with "
              "the skeleton from Part 1, (2) gives one detail about where it comes from or how it is done, "
              "and (3) explains two words a foreigner would not know, using two different defining "
              "expressions."))
P.append('<p style="margin-bottom:8px">%s</p>' % box("2.4", 1, W, "Write your paragraph here"))
h.texts[("2.4", 1)] = "Define a ritual from your own culture"

# ------------------------------------ 3 Sheet 2, A-C: the other side of the city
P.append(bar(3, "Futures", "adjectives, three futures, scanning"))
P.append(ex("3.1", "Six adjectives from the blog. Match each to its definition."))
MEANINGS = [("a", "below the surface of the ground"), ("b", "makes you think a lot about something"),
            ("c", "very small"), ("d", "makes you feel fear"), ("e", "strange and a little scary, in a fun way"),
            ("f", "with a special, exciting quality — like a story")]
P.append(key_list(MEANINGS))
ADJ = ["spooky", "magical", "underground", "tiny", "frightening", "thought-provoking"]
for n, word in enumerate(ADJ, 1):
    P.append(item(h, "3.1", n, word + " {}", box("3.1", n)))
P.append(ex("3.2", "Now complete each phrase from the blog with ONE of the six."))
for n, text in enumerate([
        "The Mail Rail is a really {} place — a secret railway nobody knows about.",
        "It is deeper {} than the famous Tube.",
        "Leadenhall Market really does look like a strange and {} place.",
        "Things are arranged in interesting and {} ways.",
        "The clown museum is {} and opens one day a month.",
        "Do you think a ride through the old tunnels will be {} ?"], 1):
    P.append(item(h, "3.2", n, text, box("3.2", n)))
P.append(panel("TUSHUNTIRISH — BITTA BLOGDA UCHTA KELASI ZAMON", [
    "Blog dam olish kunlari haqida, shuning uchun unda kelasi zamon shakllari koʻp — va mualliflar uchta "
    "turli shaklni, har birini oʻz sababi bilan ishlatadi. Oʻqishdagi savol — *qaysi shakl?* emas, "
    "*bu shakl reja qanchalik aniq ekani haqida nima deydi?*",
    "[[BE GOING TO]] **Reja — qaror qilingan, lekin hali kelishilmagan boʻlishi mumkin.** *I'm going to a "
    "really spooky place at the weekend. · We're going to visit a couple of places.* Muallif qaror "
    "qilgan. Boshqa kimdir ishtirok etishi haqida hali hech narsa aytilmagan.",
    "[[PRESENT CONTINUOUS]] **Kelishuv — vaqti va boshqa odamlar bilan.** *We're meeting at the school at "
    "11 a.m. on Saturday.* Vaqt aniq, boshqalar kutilmoqda. Qayerda boʻlish kerakligini aynan shu shakl "
    "aytadi.",
    "[[WILL]] **Taxmin yoki taklif, reja emas.** *I think it will be really interesting. · Do you think it "
    "will be frightening? · Then I'll email him.* Muallif kelajak haqida taxmin qilyapti yoki yozayotgan "
    "paytda qaror qilyapti.",
    "**Demak, blogdan amaliy maʼlumot — qayerda, qachon, kim bilan — qidirsangiz, PRESENT CONTINUOUS ni "
    "qidiring.** Kelishuvlar oʻsha yerda. *Going to* niyatni, *will* esa fikrni bildiradi.",
]))
P.append(ex("3.3", "Plan (P), arrangement (A) or prediction / offer (W)?"))
for n, text in enumerate(["I'm going to a spooky place at the weekend.",
                          "We're meeting at the school at 11 a.m.",
                          "I think it will be really interesting.",
                          "We're going to visit a couple of places.",
                          "Then I'll email him.",
                          "I'm planning to go on Friday after class."], 1):
    P.append(item(h, "3.3", n, text + " {}", box("3.3", n)))
P.append(ex("3.4", "Complete with the form that fits the meaning in brackets."))
for n, text in enumerate([
        "We {} (visit) the market first — we decided last night. (plan)",
        "Kyoko and I {} (meet) outside King's Cross at two. (arrangement)",
        "I don't think it {} (be) very crowded on a Friday. (prediction)",
        "Leave a comment and I {} (add) your name to the list. (offer)",
        "Who {} (come) on Saturday? Write your name below. (arrangement)"], 1):
    P.append(item(h, "3.4", n, text, box("3.4", n, "170px")))
P.append(panel("STRATEGIYA — SCANNING (TEZ QIDIRISH)", [
    "**Scanning** — bitta narsani izlab oʻqish va qolgan hammasiga eʼtibor bermaslik. Siz matnni "
    "tushunishga harakat qilmayapsiz. Siz ov qilyapsiz — vaqt, narx, ism, kun — koʻzingiz tez harakat "
    "qilib, faqat kerakli narsaning shakliga duch kelganda toʻxtashi kerak.",
    "[[AVVAL]] **Qarashdan oldin javob qanday koʻrinishini hal qiling.** Vaqt *11 a.m.* yoki *two "
    "o'clock* kabi koʻrinadi. Kun bosh harf bilan yoziladi — *Saturday*. Narxda belgi bor. Joy nomi "
    "bosh harf bilan. Shaklni bilsangiz, uni oʻz ichiga ololmaydigan butun qatorlarni tashlab ketasiz.",
    "[[TUZILISH]] **Sahifa tuzilishidan foydalaning.** Blogda ismlar qalin harfda, har bir odamga "
    "alohida xatboshi, amaliy maʼlumot esa deyarli har doim postning birinchi yoki oxirgi qatorida. "
    "Avval oʻsha qatorlarni koʻzdan kechiring.",
    "[[TOʻXTANG]] **Topganingizda toʻxtang.** Javobni topib, keyin tekshirish uchun oʻqishda davom etish — "
    "eng koʻp uchraydigan xato. Keyingi savolga oʻting.",
]))
P.append(ex("3.5", "Scan the blog on the coursebook page for these. Time yourself — aim for under two minutes."))
SCAN1 = ["What time do Anna and Kyoko meet?", "Which day is Kuba going?",
         "How many letters did the Mail Rail carry a day?", "How old is Leadenhall Market?",
         "When did the Mail Rail close?", "How many egg faces are in the museum?"]
for n, text in enumerate(SCAN1, 1):
    P.append(item(h, "3.5", n, text + " {}", box("3.5", n, "170px")))
P.append(ex("3.6", "Which post did you find each answer in?"))
for n, text in enumerate(SCAN1, 1):
    P.append(item(h, "3.6", n, text + " {}", box("3.6", n)))

# ----------------------------------------------- 4 Sheet 2, D-E: a new blog
P.append(bar(4, "Blog", "the other side of town"))
P.append(ex("4.1", "A new blog. Scan first, then read."))
P.append(prose("City College Blog — The Other Side of Town", bold=True))
P.append(prose("Going somewhere new this weekend? Post it here and see who wants to come.", italic=True))
for lead, para in [
        ("Farrukh — The old bathhouse.",
         "There's a bathhouse near the old market that closed in the 1980s and has just reopened as a café. "
         "The building is 400 years old and the main room is round, with a hole in the roof for the light. "
         "It's a bit spooky in the evening, in a good way. I'm going on Sunday afternoon if anyone wants to "
         "come. I think the tea will be expensive, but the room is worth it."),
        ("Madina and Laylo — Rooftop cinema.",
         "We're going to the open-air cinema on the roof of the old textile factory on Saturday night. They "
         "show one film a week, always something old, and you sit on cushions. It's tiny — about forty "
         "seats — so you have to book. We've booked two already. We're meeting at the factory gate at 8.30; "
         "the film starts at nine. Bring a jacket. It'll be cold up there after ten."),
        ("Sherzod — The puppet workshop.",
         "Behind the puppet theatre there's a workshop where they make the puppets, and on the first Saturday "
         "of every month you can go in. The man who runs it has worked there for fifty years. He'll show you "
         "how the heads are carved and let you try. It's thought-provoking — every puppet has a face that "
         "took a week to make. I'm planning to go this Saturday at ten. Leave a comment and I'll put your "
         "name on the list; they only take twelve people."),
        ("Nodira — The night market.",
         "Not underground and not secret — everybody knows about the night market — but it's magical after "
         "eleven, when the tourists have gone and the stalls start to close. The bread is half price. I'm "
         "going to walk through it on Friday at about half past eleven. No booking, no list. Just turn up.")]:
    P.append(prose(para, lead=lead))
P.append(ex("4.2", "Scan. Under two minutes."))
for n, text in enumerate(["Which place is 400 years old?", "What time does the film start?",
                          "How many people can visit the workshop?", "Which day is the night market?",
                          "How many seats has the cinema got?", "How long has the puppet-maker worked there?"], 1):
    P.append(item(h, "4.2", n, text + " {}", box("4.2", n, "170px")))
P.append(ex("4.3", "Now read properly and answer."))
for n, text in enumerate([
        "Which THREE places need booking or a list, and which one doesn't?",
        "Find one *going to*, one present continuous and one *will* in Madina and Laylo's post. What does "
        "each one tell you?",
        "Which post is closest to Manuel's Mail Rail post, and why?",
        "Nodira's post has two negatives in the first line. What is she comparing her place to?"], 1):
    P.append(item(h, "4.3", n, text + " {}", box("4.3", n, W)))
P.append(ex("4.4", "Write your own post for the blog (80–100 words)."))
P.append(note("Choose a real place in your town that tourists don't know about. Write a post like the ones "
              "above: what it is and why it's worth it (use two of the six adjectives from 3.1), your plan "
              "(*be going to*), the arrangement — day, time, meeting point — in the present continuous, and "
              "one prediction with *will*. End with how people can join you."))
P.append('<p style="margin-bottom:8px">%s</p>' % box("4.4", 1, W, "Write your post here"))
h.texts[("4.4", 1)] = "Write your own post for the blog"

h.html = '<div class="booklet">' + "".join(P) + "</div>"

# ------------------------------- every instruction, once more, in Uzbek
for label, text in [
        ("1.1", "Taqdimotdagi iboralar. Har birini BITTA soʻz bilan toʻldiring."),
        ("1.2", "Har bir taʼrifni umumiy ot va *which / that* bilan toʻldiring."),
        ("1.3", "Har birini *MEANS* bilan qayta yozing."),
        ("1.4", "Xatoni topib, toʻgʻri gapni yozing."),
        ("1.5", "Asosiy fikrmi (*M*) yoki tafsilotmi (*D*)? Tanlang."),
        ("2.1", "Yangi taqdimotdan parcha. Uni oʻqing, keyin topshiriqlarni bajaring."),
        ("2.2", "Toping va yozing."),
        ("2.3", "Endi savollarga javob bering."),
        ("3.1", "Blogdagi oltita sifat. Har birini taʼrifi bilan moslashtiring: mos harfni tanlang."),
        ("3.2", "Endi har bir iborani shu oltitadan BITTASI bilan toʻldiring."),
        ("3.3", "Rejami (*P*), kelishuvmi (*A*) yoki taxmin / taklifmi (*W*)? Tanlang."),
        ("3.4", "Qavs ichidagi maʼnoga mos shakl bilan toʻldiring."),
        ("3.5", "Darslikdagi blogdan quyidagilarni tez qidirib toping. Vaqtni belgilang — ikki daqiqadan "
                "kamiga harakat qiling."),
        ("3.6", "Har bir javobni qaysi postdan topdingiz? Tanlang."),
        ("4.1", "Yangi blog. Avval tez koʻz yugurtiring, keyin oʻqing."),
        ("4.2", "Tez qidiring. Ikki daqiqadan kam."),
        ("4.3", "Endi diqqat bilan oʻqing va javob bering.")]:
    h.say_also(label, text)
h.say_also("2.4", "Oʻz madaniyatingizdagi bir marosimga taʼrif bering (80–100 soʻz). Oilangiz yoki "
           "mamlakatingizdagi bir marosimni tanlang — salomlashish, ovqat, bayram odati, imtihon oldidan "
           "qiladigan ishingiz. Bitta xatboshi yozing: (1) uni nomlang va 1-qismdagi skelet bilan taʼrif "
           "bering, (2) uning kelib chiqishi yoki qanday bajarilishi haqida bitta tafsilot keltiring, "
           "(3) chet ellik tushunmaydigan ikkita soʻzni ikki xil taʼriflovchi ibora bilan tushuntiring.",
           after="Choose a ritual your family")
h.say_also("4.4", "Blog uchun oʻz postingizni yozing (80–100 soʻz). Shahringizdagi sayyohlar bilmaydigan "
           "haqiqiy joyni tanlang. Yuqoridagilarga oʻxshash post yozing: bu nima va nega arziydi (3.1 "
           "dagi oltita sifatdan ikkitasini ishlating), rejangiz (*be going to*), kelishuv — kun, vaqt, "
           "uchrashuv joyi — present continuous da, va *will* bilan bitta taxmin. Oxirida boshqalar sizga "
           "qanday qoʻshilishi mumkinligini yozing.", after="Choose a real place in your town")

# ------------------------------------------------------------------ the key
K = {}
for n, a in enumerate(["ritual", "passed/inherited", "social", "pose", "feedback", "false", "belong",
                       "portraits/portrait"], 1):
    K[("1.1", n, 1)] = Q(a)
K[("1.2", 1, 1)] = Q("person who/person that/man who/woman who")
K[("1.2", 2, 1)] = Q("group")
K[("1.2", 2, 2)] = Q("who/that")
K[("1.2", 3, 1)] = Q("way that/way in which/way which/position in which/manner in which")
K[("1.2", 4, 1)] = Q("what/the things that/things that/the things which/things which/information that/"
                     "the information that/information which/something that/the comments that/comments that/"
                     "the words that/words that")
K[("1.2", 5, 1)] = Q("picture that/picture which/painting that/painting which/portrait that/portrait which")
K[("1.2", 6, 1)] = Q("ceremony when/ceremony where/ceremony at which/ceremony in which/day when/"
                     "day on which/event when/event where/event at which/celebration when/celebration where/"
                     "celebration at which/party where/party at which")
for n in (1, 2, 3, 4):                        # a definition of their own: his to read
    K[("1.3", n, 1)] = own()
NOUNS = ["habit", "activity", "action", "custom", "tradition", "thing", "practice", "ceremony"]
ritual = []
for noun in NOUNS:
    art = "an" if noun[0] in "aeiou" else "a"
    for rel in ("that", "which"):
        for rest in ("you always do the same way", "you always do in the same way",
                     "is always done the same way", "is always done in the same way"):
            ritual.append("A ritual is %s %s %s %s" % (art, noun, rel, rest))
K[("1.4", 1, 1)] = write("/".join(ritual))
K[("1.4", 2, 1)] = write("A selfie is a photo which you take of yourself/A selfie is a photo that you "
                         "take of yourself/A selfie is a photo you take of yourself")
K[("1.4", 3, 1)] = write("Culture means the habits and beliefs of a group of people")
K[("1.4", 4, 1)] = own()                      # the key gives the idea, not one sentence
MD = {"M": "M · main point", "D": "D · detail"}
for n, a in enumerate("DMDMMD", 1):
    K[("1.5", n, 1)] = choose(["M", "D"], a, labels=MD)

for n in (1, 2, 3):
    K[("2.2", n, 1)] = own()
K[("2.2", 4, 1)] = Q("open right hand/an open right hand/the open right hand/open hand/an open hand/"
                     "the open hand/hand/a hand/the hand")
K[("2.2", 4, 2)] = Q("firm/a firm handshake/firm handshake")
K[("2.3", 1, 1)] = Q("First/Firstly")
K[("2.3", 1, 2)] = Q("Second/Secondly")
for n in (2, 3, 4):
    K[("2.3", n, 1)] = own()
K[("2.4", 1, 1)] = own(control="essay")

# 3.1 as listed: spooky e, magical f, underground a, tiny c, frightening d, thought-provoking b
for n, a in enumerate("efacdb", 1):
    K[("3.1", n, 1)] = choose([l for l, _t in MEANINGS], a)
for n, a in enumerate(["spooky", "underground", "magical", "thought-provoking", "tiny", "frightening"], 1):
    K[("3.2", n, 1)] = choose(ADJ, a)
PAW = {"P": "P · plan", "A": "A · arrangement", "W": "W · prediction / offer"}
for n, a in enumerate("PAWPWP", 1):
    K[("3.3", n, 1)] = choose(["P", "A", "W"], a, labels=PAW)
for n, a in enumerate(["'re going to visit/are going to visit", "'re meeting/are meeting",
                       "will be/'ll be", "'ll add/will add", "is coming/'s coming"], 1):
    K[("3.4", n, 1)] = Q(a)
for n, a in enumerate([
        "11 a.m./11 am/11am/11a.m./11/eleven/11.00/11:00/at 11/at 11 a.m./at 11 am/at eleven/"
        "eleven o'clock/at eleven o'clock/11 o'clock",
        "Friday/on Friday",
        "four million/4 million/4,000,000/4000000/four million letters/4 million letters",
        "over 600 years/600 years/more than 600 years/over 600 years old/600 years old/"
        "more than 600 years old/over 600/more than 600/600",
        "2003/in 2003",
        "200/two hundred/200 egg faces/about 200"], 1):
    K[("3.5", n, 1)] = Q(a)
POST = {"M": "M · Manuel", "A": "A · Anna & Kyoko", "K&S": "K&S · Kim & Santiago", "K": "K · Kuba"}
for n, a in enumerate(["A", "K", "M", "A", "M", "K"], 1):
    K[("3.6", n, 1)] = choose(["M", "A", "K&S", "K"], a, labels=POST)

for n, a in enumerate([
        "the bathhouse/bathhouse/the old bathhouse/old bathhouse/Farrukh's bathhouse/the bathhouse café",
        "nine/9/at nine/at 9/9 pm/9 p.m./9pm/9.00/9:00/21:00/nine o'clock/at nine o'clock/at 9 pm",
        "twelve/12/12 people/twelve people",
        "Friday/on Friday",
        "about forty/forty/40/about 40/around forty/around 40/forty seats/40 seats/about forty seats/"
        "about 40 seats",
        "fifty years/50 years/50/fifty/for fifty years/for 50 years"], 1):
    K[("4.2", n, 1)] = Q(a)
for n in (1, 2, 3, 4):                        # read properly: the key accepts any sensible reading
    K[("4.3", n, 1)] = own()
K[("4.4", 1, 1)] = own(control="essay")

if __name__ == "__main__":
    data = h.build(K, "Pre-Intermediate", 4, "Unit 4 ASRP — Rituals and the city")
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "asrp4.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
