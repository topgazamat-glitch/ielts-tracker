"""Destination B1 (Grammar and Vocabulary), units 12 and 23 - done on a phone.

Destination is a second book beside the course: a unit of it is set as
homework next to the workbook and the handout. The PDF on Azamat's Mac is a
scan, so the pages here are written out again by hand from the page images
(PDF pages 47-50 and 96-98), in the booklet's own markup - section bars,
exercise numbers, panels - so a unit works like every handout: in parts,
each checked, then the next. Each exercise keeps the book's letter (A, B, C
...) so a student doing it on paper and one doing it here are on the same
exercise. The answers are the book's own key (PDF pages 237-238 and 244).

The files carry series "destination": such a unit opens for the class it is
set to, whatever its level, is linked from a line "Destination B1, Unit 12"
in Set homework, and never joins the chain of the course's booklets.

Every instruction has a line in Uzbek under it, and unit 23's grammar box is
told again in Uzbek with the book's English examples kept, as in the
Pre-Intermediate handouts.

Put right against the key:
  - Unit 23 B5 ("So how ..... it happen?"): the key prints "how"; the gap
    comes after "how", so the answer is "did".
Accepted beyond the key, because the sentence is right with them too:
  - Unit 12 I3 "he cares ..... me": "for" as well as "about".
  - Unit 12 I9 "we chat ..... each other": "with" as well as "to".
  - British and American spellings (apologised / apologized, neighbourhood /
    neighborhood, cafés / cafes), and in H either the ending or the whole word.

    python3 handouts/dest_b1_digital.py     # writes handouts/dest_b1_12.json and dest_b1_23.json
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import digital                                                          # noqa: E402
from digital import Q, choose, write, report, told, plain               # noqa: E402

TEAL, DEEP, SOFT = "127D80", "0B5456", "F2F8F8"
W = "95%"


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


def gapped(h, label, text, width="110px"):
    """A text with numbered gaps, "(3) {}": each gap is item 3 of the exercise."""
    out, pos = "", 0
    for m in re.finditer(r"\((\d+)\) \{\}", text):
        n = int(m.group(1))
        near = lambda t: re.sub(r"\(\d+\) \{\}", "……", t)
        before = near(text[max(0, m.start() - 40):m.start()])
        after = near(text[m.end():m.end() + 30])
        h.texts[(label, n)] = plain(md(before + " …… " + after))
        out += md(text[pos:m.start()]) + '<span style="font-weight:700">(%d)</span> ' % n \
            + box(label, n, width)
        pos = m.end()
    return out + md(text[pos:])


def para(inner, style="margin-bottom:6px;line-height:1.45;padding-left:48px"):
    return '<p style="%s"><span style="color:#1A1A1A;font-size:11.5pt">%s</span></p>' % (style, inner)


def panel(title, paras, colour=TEAL, ground=SOFT):
    head = ('<table class="bk"><tr><td style="vertical-align:top;background:#%s;border-top:1px solid #%s;'
            'border-bottom:1px solid #%s;border-left:1px solid #%s;border-right:1px solid #%s">'
            '<table class="bk"><tr><td style="vertical-align:top;background:#%s;border-top:0;border-bottom:0;'
            'border-left:0;border-right:0"><p style="margin-bottom:0px"><span style="font-weight:700;'
            'color:#FFFFFF">%s</span></p></td></tr></table>'
            % (ground, colour, colour, colour, colour, colour, html.escape(title)))
    return head + "".join(told(p) for p in paras) + "</td></tr></table>"


def key_list(pairs):
    """The words or endings to choose from, as a box above the items."""
    return ('<table class="bk"><tr><td style="vertical-align:top;background:#%s;border-left:3px solid #%s">'
            % (SOFT, TEAL)
            + "".join('<p style="margin:0"><span style="font-weight:700;color:#%s">%s</span>  %s</p>'
                      % (TEAL, l, html.escape(t, quote=False)) for l, t in pairs)
            + "</td></tr></table>")


def word_box(words):
    return ('<table class="bk"><tr><td style="vertical-align:top;background:#%s;border-left:3px solid #%s">'
            '<p style="margin:0;line-height:1.6"><span style="color:#1A1A1A;font-size:11.5pt">%s</span></p>'
            '</td></tr></table>' % (SOFT, TEAL, "  ·  ".join(html.escape(w) for w in words)))


def cover(kicker, name, sub, goals):
    return ('<p><span>%s</span></p><p><span>%s</span></p><p><span>%s</span></p>'
            '<table class="bk"><tr><td><p><span>You will learn to</span></p>%s</td></tr></table>'
            % (html.escape(kicker), html.escape(name), html.escape(sub),
               "".join('<p><span>—  </span>%s</p>' % told(g, bare=True) for g in goals)))


def handout():
    h = digital.Handout.__new__(digital.Handout)
    h.blanks, h.removed, h.texts, h.hints = [], set(), {}, {}
    return h


# ================================================================== unit 12

def unit12():
    h, P, K = handout(), [], {}
    P.append(cover("DESTINATION B1  ·  UNIT 12  ·  VOCABULARY", "Friends and relations",
                   "Topic vocabulary  ·  phrasal verbs  ·  prepositional phrases  ·  word formation  ·  word patterns",
                   ["doʻst va qarindoshlar haqida gapirishga kerak soʻzlarni — *loyal, generous, relations, stranger*",
                    "*bring up, fall out, get on, split up* kabi frazali feʼllarni",
                    "*in common, on purpose, on your own* kabi predlogli iboralarni",
                    "bir soʻzdan boshqasini yasashni — *forgive → forgiveness, honest → dishonest*",
                    "sifat va feʼllardan keyin qaysi predlog kelishini — *fond of, proud of, apologise for*"]))

    # ---------------------------------------------------- 1 topic vocabulary
    P.append(bar(1, "Topic vocabulary", "people and relationships"))
    P.append(panel("MAVZU LUGʻATI  ·  Topic vocabulary", [
        "**Feʼllar:** *apologise, decorate, defend, introduce, recognise, rent, respect, trust*",
        "**Sifatlar:** *close, confident, cool, divorced, generous, grateful, independent, loving, loyal, "
        "ordinary, patient, private, single*",
        "**Otlar:** *boyfriend, couple, flat, girlfriend, guest, mood, neighbourhood, relation, stranger*",
    ]))
    P.append(ex("1.1", "**A**  Complete using the words in the box."))
    A = ["close", "confident", "cool", "divorced", "generous", "grateful", "independent", "loving",
         "loyal", "ordinary", "patient", "private", "single"]
    P.append(word_box(A))
    for n, (text, a) in enumerate([
            ("Thanks for looking after my dog for the weekend. I'm really {} .", "grateful"),
            ("Judy is one of the most {} people I know. She's always giving me presents!", "generous"),
            ("I don't want a girlfriend. I like being {} .", "single"),
            ("It will take a while for Simon to forgive you. You'll just have to be {} .", "patient"),
            ("Adam's parents are {} , so he only sees his dad at the weekend.", "divorced"),
            ("Cats are more {} than dogs. They live their own lives and don't need human company.", "independent"),
            ("I'm very {} to my best friend. I'd never talk about her behind her back.", "loyal"),
            ("Sandy's such a {} dog. He's always so happy to see us when we come home!", "loving"),
            ("I'm not a very {} person. I get nervous when I have to speak in public.", "confident"),
            ("My diary is {} . No one is allowed to read it apart from me.", "private"),
            ("I tell my sister all my problems and secrets. We have a very {} relationship.", "close"),
            ("My uncle's really {} ! He's in a rock band!", "cool"),
            ("I'm just a/an {} person with a normal life – but I'm quite happy!", "ordinary")], 1):
        P.append(item(h, "1.1", n, text, box("1.1", n)))
        K[("1.1", n, 1)] = Q(a)

    P.append(ex("1.2", "**B**  Complete using a word formed from the letters given."))
    for n, (text, letters, a) in enumerate([
            ("Don't you think Ben and Angie make a lovely {} ?", "LEOPUC", "couple"),
            ("How many {} are staying at the hotel at the moment?", "SEGUTS", "guests"),
            ("All our {} are coming to the wedding.", "SNOREALIT", "relations"),
            ("A {} is just a friend you haven't met yet!", "GRANTERS", "stranger"),
            ("How long have you been going out with your {} ?", "DRINFEYOB", "boyfriend"),
            ("Why are you in such a bad {} ?", "ODOM", "mood"),
            ("My grandparents live in a really quiet {} .", "OHIDROUGHBONE", "neighbourhood/neighborhood"),
            ("My cousin has just moved into a {} in the city centre.", "ATLF", "flat"),
            ("I'm going to the cinema with my {} tonight.", "REDGINFLIR", "girlfriend")], 1):
        P.append(item(h, "1.2", n, "%s  **%s**" % (text, " ".join(letters)), box("1.2", n, "150px")))
        K[("1.2", n, 1)] = Q(a)

    P.append(ex("1.3", "**C**  Each of the words in bold is in the wrong sentence. Write the correct word."))
    for n, (text, a) in enumerate([
            ("I was first **respected** to Jake at a party. {}", "introduced"),
            ("I shouldn't have **rented** you. Now I know you can't keep a secret! {}", "trusted"),
            ("Our house is being **recognised** so we're staying with my grandparents at the moment. {}",
             "decorated"),
            ("Everyone **apologised** Mr Turner because he was strict but fair. {}", "respected"),
            ("Have you **introduced** to Kelly for losing her CD? {}", "apologised/apologized"),
            ("Sarah said I was a liar but Carol **trusted** me and said I wasn't. {}", "defended"),
            ("We **decorated** a small house in the countryside for the summer. {}", "rented"),
            ("No one **defended** Phil when he came to the party dressed as an old man. {}",
             "recognised/recognized")], 1):
        P.append(item(h, "1.3", n, text, box("1.3", n, "150px", "the right word")))
        K[("1.3", n, 1)] = Q(a)

    # ------------------------------------- 2 phrasal verbs, prepositional phrases
    P.append(bar(2, "Phrasal verbs", "and prepositional phrases"))
    P.append(panel("FRAZALI FEʼLLAR  ·  Phrasal verbs", [
        "**bring up** — bolani katta boʻlguncha tarbiyalamoq  ·  **fall out (with)** — urishib, "
        "doʻstlikni uzmoq  ·  **get on (with)** — yaxshi munosabatda boʻlmoq  ·  **go out with** — "
        "biror kishi bilan uchrashib yurmoq",
        "**grow up** — katta boʻlmoq (bolalar)  ·  **let down** — umidini puchga chiqarmoq  ·  "
        "**look after** — qaramoq, gʻamxoʻrlik qilmoq  ·  **split up** — ajrashmoq, munosabatni tugatmoq",
        "[[PREDLOGLI IBORALAR]] *by yourself · in common (with) · in contact (with) · in love (with) · "
        "on purpose · on your own*",
    ]))
    P.append(ex("2.1", "**D**  Choose the correct word."))
    D = [("I thought I could trust you! You've really let me {} .", [("off", "down", "down")]),
         ("Do you get {} well with your older sister?", [("on", "in", "on")]),
         ("As children grow {} , they want more independence from their parents.", [("off", "up", "up")]),
         ("Dave has fallen {} with Jason and they're not talking to each other at the moment.",
          [("off", "out", "out")]),
         ("Ed was brought {} by his aunt because his parents lived abroad.", [("in", "up", "up")]),
         ("I used to go {} with Tony but we split {} about a year ago.",
          [("out", "by", "out"), ("off", "up", "up")]),
         ("I hate looking {} my baby brother!", [("after", "over", "after")])]
    for n, (text, picks) in enumerate(D, 1):
        P.append(item(h, "2.1", n, text, *[box("2.1", n) for _p in picks]))
        for k, (a, b, right) in enumerate(picks, 1):
            K[("2.1", n, k)] = choose([a, b], right)

    P.append(ex("2.2", "**E**  Write one word in each gap."))
    P.append(para('<span style="font-weight:700;font-size:12.5pt">Advice for parents of teenagers</span>'))
    P.append(para(gapped(h, "2.2",
        "You've always (1) {} up your children to come to you when they're in trouble. You feel it's "
        "your job to (2) {} after them when they're having problems. But now, as your children are "
        "(3) {} up, they often don't want to share their problems with you. That's perfectly normal, "
        "so don't worry! Of course, you want to (4) {} on well with your children, but that means you "
        "have to give them some freedom.")))
    P.append(para(gapped(h, "2.2",
        "Maybe they've (5) {} out with their best friend and feel upset and angry. Maybe they've just "
        "(6) {} up with the boyfriend or girlfriend they've been (7) {} out with. Maybe they've been "
        "(8) {} down by a friend who they trusted. Teenagers go through all these problems. If they "
        "want to talk to you about it, then that's fine. But if they don't, don't force them. They'll "
        "come to you when they're ready.")))
    for n, a in enumerate(["brought", "look", "growing", "get", "fallen", "split", "going", "let"], 1):
        K[("2.2", n, 1)] = Q(a)

    P.append(ex("2.3", "**F**  Each of the words in bold is wrong. Write the correct word."))
    for n, (text, a) in enumerate([
            ("Are you still **on** contact with any friends from university? {}", "in"),
            ("I'm going to split up with Dan because we've got nothing **from** common. {}", "in"),
            ("I don't think I'd like to live **on** myself. {}", "by"),
            ("Would you like to live **by** your own? {}", "on"),
            ("Fiona didn't break your MP3 player **with** purpose. It was an accident! {}", "on"),
            ("Guess what! Mike and Julie are **at** love with each other. {}", "in")], 1):
        P.append(item(h, "2.3", n, text, box("2.3", n, "90px")))
        K[("2.3", n, 1)] = Q(a)

    # ---------------------------------------------------- 3 word formation
    P.append(bar(3, "Word formation", "new words from old ones"))
    P.append(panel("SOʻZ YASALISHI  ·  Word formation", [
        "**able** → *ability, disabled, unable*  ·  **admire** → *admiration*  ·  **care** → *careful, "
        "careless*  ·  **confident** → *confidence*  ·  **forgive** → *forgave, forgiven, forgiveness*",
        "**honest** → *dishonest, honesty*  ·  **introduce** → *introduction*  ·  **lie** → *liar, "
        "lying*  ·  **person** → *personality, personal*  ·  **relate** → *relative, relation, relationship*",
    ]))
    P.append(ex("3.1", "**G**  Complete by changing the form of the word in capitals."))
    for n, (text, word, a) in enumerate([
            ("I'm asking for your {} !", "FORGIVE", "forgiveness"),
            ("Doug is such a {} . I never believe a word he says!", "LIE", "liar"),
            ("Be {} ! I've just painted the walls and they're wet.", "CARE", "careful"),
            ("Lying to your dad like that was really {} .", "HONEST", "dishonest"),
            ("My brother is {} but that doesn't stop him from doing lots of sport.", "ABLE", "disabled"),
            ("I haven't got the {} to go up to a stranger at a party and introduce myself.",
             "CONFIDENT", "confidence"),
            ("My best friend gives me lots of help with my {} problems.", "PERSON", "personal"),
            ("My {} with Chris lasted for over three years.", "RELATION", "relationship")], 1):
        P.append(item(h, "3.1", n, "%s  **%s**" % (text, word), box("3.1", n, "150px")))
        K[("3.1", n, 1)] = Q(a)

    P.append(ex("3.2", "**H**  Complete the words."))
    for n, (stem, rest, a) in enumerate([
            ("Liz has got a really lively person", " .", "ality/personality"),
            ("Roger is always losing things. He's so care", " !", "less/careless"),
            ("I really admire you for your honest", " .", "y/honesty"),
            ("I have a lot of admir", " for Linda. She's achieved such a lot.", "ation/admiration"),
            ("Uncle Alan has an amazing mental ab", " – he can guess the number you're thinking of.",
             "ility/ability"),
            ("In the introduc", " to this book, it says that moving house is extremely stressful.",
             "tion/introduction"),
            ("Most of my relat", " live in Canada so I don't see them very often.",
             "ions/ives/relations/relatives")], 1):
        P.append(item(h, "3.2", n, stem + "{}" + rest, box("3.2", n, "90px", "…")))
        K[("3.2", n, 1)] = Q(a)

    # ---------------------------------------------------- 4 word patterns
    P.append(bar(4, "Word patterns", "which preposition comes next"))
    P.append(panel("SOʻZ BIRIKMALARI  ·  Word patterns", [
        "[[SIFATLAR]] *fond of · jealous of · kind to · married to · proud of*",
        "[[FEʼLLAR]] *admire sb for · apologise (to sb) for · argue (with sb) about · care about · "
        "chat (to sb) about*",
        "[[OTLAR]] *an argument (with sb) about · a relationship with*",
    ]))
    P.append(ex("4.1", "**I**  Write one word in each gap."))
    P.append(para(gapped(h, "4.1",
        "I'm very fond (1) {} my husband, William. I've been married (2) {} him for over sixty years. "
        "I know he cares (3) {} me now just as much as when we first met all those years ago. I'd got "
        "lost, and I asked him for directions. He was so kind (4) {} me. He offered to drive me wherever "
        "I wanted to go. It was love at first sight and since then my relationship (5) {} him has always "
        "been wonderful.", "90px")))
    P.append(para(gapped(h, "4.1",
        "William is proud (6) {} my success as an artist, and he's never been jealous (7) {} my fame. "
        "I really admire him (8) {} supporting me so much over the years. Every evening, we chat (9) {} "
        "each other (10) {} the day's events. Of course, we do sometimes argue (11) {} things. All "
        "couples do. But whenever I have an argument (12) {} him, we soon start laughing and both "
        "apologise (13) {} each other (14) {} getting angry. I can't imagine life without him!", "90px")))
    for n, a in enumerate(["of", "to", "about/for", "to", "with", "of", "of", "for", "to/with", "about",
                           "about", "with", "to", "for"], 1):
        K[("4.1", n, 1)] = Q(a)

    h.html = '<div class="booklet">' + "".join(P) + "</div>"
    for label, text in [
            ("1.1", "Qutichadagi soʻzlar bilan toʻldiring."),
            ("1.2", "Berilgan harflardan soʻz tuzib, gapni toʻldiring."),
            ("1.3", "Qalin soʻzlar boshqa gapga tushib qolgan. Har bir gapga mos soʻzni yozing."),
            ("2.1", "Toʻgʻri soʻzni tanlang."),
            ("2.2", "Har bir boʻshliqqa bitta soʻz yozing."),
            ("2.3", "Qalin soʻz notoʻgʻri. Toʻgʻrisini yozing."),
            ("3.1", "Katta harf bilan yozilgan soʻzning shaklini oʻzgartirib, toʻldiring."),
            ("3.2", "Soʻzning oxirini yozib, toʻldiring."),
            ("4.1", "Har bir boʻshliqqa bitta soʻz — predlog — yozing.")]:
        h.say_also(label, text)
    data = h.build(K, "Pre-Intermediate", 12, "Destination B1 · Unit 12 — Friends and relations")
    return data


# ================================================================== unit 23

def unit23():
    h, P, K = handout(), [], {}
    P.append(cover("DESTINATION B1  ·  UNIT 23  ·  GRAMMAR", "Questions, question tags, indirect questions",
                   "Asking  ·  checking  ·  asking politely",
                   ["turli zamonlarda savol tuzishni — *Do you…? Were they…? Have you…?*",
                    "*who* va *what* bilan savolda *do* qachon kerakligini — *Who told you? / Who did you tell?*",
                    "gap oxiriga soʻroq qoʻshimchasini qoʻyishni — *isn't it? have you? shall we?*",
                    "muloyim, bilvosita savol berishni — *Could you tell me where the bank is?*"]))

    # ---------------------------------------------------- 1 questions
    P.append(bar(1, "Questions", "the auxiliary before the subject"))
    P.append(panel("TUSHUNTIRISH — SAVOL QANDAY TUZILADI", [
        "Savolda yordamchi feʼl egadan **oldin** keladi.",
        "[[ODDIY ZAMONLAR]] *do / does / did* + ega + feʼlning oddiy shakli: *Do you feel cold? · Did they "
        "go shopping?* Feʼl oʻzgarmaydi: ✗ *Did they went…?* ✗ *Does she likes…?*",
        "[[DAVOMIY VA PERFEKT ZAMONLAR]] *be* yoki *have* egadan oldinga chiqadi: *Am I annoying you? · "
        "Were they waiting for you? · Have you seen this film? · Had it started?*",
        "[[BE ASOSIY FEʼL BOʻLSA]] *Am I late? · Were you all right? · Have you been ill?*",
        "[[HAVE ASOSIY FEʼL BOʻLSA]] *do* bilan: *Does she have a bath every day? · Did they have lunch at "
        "one o'clock?*",
        "[[MODALLAR]] modal egadan oldin: *Should I call the police? · Could you call me later?*",
        "[[SOʻROQ SOʻZLARI]] *Who was in prison? · What's your name? · Where do they live? · Why did you do that?*",
    ]))
    P.append(panel("EʼTIBOR BERING", [
        "Majhul nisbatda (passive) faqat **birinchi** yordamchi feʼl egadan oldin keladi: *Was Mr Jenkins "
        "arrested yesterday? · Has Mr Jenkins been arrested?*",
        "*Who* yoki *what* **toʻldiruvchi** haqida soʻrasa, *do* kerak; **ega** haqida soʻrasa, kerak emas: "
        "*Who told you?* (= Kimdir sizga aytdi. Kim?) · *Who did you tell?* (= Siz kimgadir aytdingiz. Kimga?)",
    ], colour="C0745F", ground="FBF3EF"))
    P.append(ex("1.1", "**A**  The words and phrases in bold in each sentence are wrong. Write the correct "
                "word or phrase."))
    for n, (text, a) in enumerate([
            ("Does Debbie **likes** Greek food? {}", "like"),
            ("Did Anne and Carlo **went** to Spain last year? {}", "go"),
            ("**Was** Dawn and Jennifer with you? {}", "Were"),
            ("**Has Claudia** a haircut every Thursday? {}", "Does Claudia have"),
            ("Have you **buy** the new *Arctic Monkeys'* CD yet? {}", "bought"),
            ("**Does** Tim going to be in the school play? {}", "Is"),
            ("**It would be** the best thing to do? {}", "Would it be"),
            ("Were you **play** basketball when it started snowing? {}", "playing")], 1):
        P.append(item(h, "1.1", n, text, box("1.1", n, "170px", "the right words")))
        K[("1.1", n, 1)] = Q(a)

    P.append(ex("1.2", "**B**  Write one word in each gap."))
    lines = [("Rachel", "Hi, Ben! (1) {} are you?"),
             ("Ben", "I'm fine. (2) {} you hear about Mr Watkins, the maths teacher?"),
             ("Rachel", "No. (3) {} happened to him?"),
             ("Ben", "He fell out of the window of his classroom!"),
             ("Rachel", "(4) {} pushed him?"),
             ("Ben", "No one!"),
             ("Rachel", "So how (5) {} it happen?"),
             ("Ben", "He was sitting on the windowsill and he just fell backwards!"),
             ("Rachel", "Oh dear! Poor Mr Watkins. (6) {} he hurt?"),
             ("Ben", "No. Luckily his classroom is on the ground floor."),
             ("Rachel", "That's lucky! (7) {} you there at the time?"),
             ("Ben", "Yes! We were having a maths lesson."),
             ("Rachel", "So (8) {} did you all do?"),
             ("Ben", "We ran outside to help him. We were all laughing, though!"),
             ("Rachel", "(9) {} he think it was funny, too?"),
             ("Ben", "Not at first, but he laughed about it afterwards.")]
    for who, said in lines:
        P.append(para('<span style="font-weight:700">%s:</span>  %s' % (who, gapped(h, "1.2", said, "100px")),
                      style="margin-bottom:4px;line-height:1.45;padding-left:48px"))
    # the key prints "how" for 5; the gap follows "how", so it is "did"
    for n, a in enumerate(["How", "Did", "What", "Who", "did", "Was", "Were", "what", "Did"], 1):
        K[("1.2", n, 1)] = Q(a)

    # ---------------------------------------------------- 2 question tags
    P.append(bar(2, "Question tags", "isn't it? have you?"))
    P.append(panel("TUSHUNTIRISH — SOʻROQ QOʻSHIMCHASI (QUESTION TAG)", [
        "Gap oxiridagi qisqa savol. Ikki vazifasi bor: suhbatdoshning roziligini kutish — *It's confusing, "
        "isn't it?* — yoki biror narsa toʻgʻriligini tekshirish — *You haven't been to prison, have you?*",
        "[[QOIDA]] Gap tasdiq boʻlsa, tag inkor; gap inkor boʻlsa, tag tasdiq. Tagda gapdagi yordamchi feʼl "
        "takrorlanadi: *Phil works here, doesn't he? · They didn't leave, did they? · You are coming, aren't "
        "you? · They weren't looking, were they? · They've gone, haven't they? · You hadn't seen it, had you?*",
        "[[BE, HAVE VA MODALLAR]] *He's new here, isn't he? · You weren't old enough, were you? · They have "
        "a car, haven't / don't they? · You didn't have a shower every day, did you? · Jan should be here by "
        "now, shouldn't she? · You won't make a mess, will you?*",
    ]))
    P.append(panel("YODDA TUTING", [
        "*I am* bilan tag *aren't I?*, *I'm not* bilan esa *am I?*: *I'm right, aren't I? · I'm not "
        "stupid, am I?*",
        "*Let's* bilan tag *shall we?*: *Let's do the washing-up later, shall we?*",
    ], colour="C0745F", ground="FBF3EF"))
    P.append(ex("2.1", "**C**  Match to make sentences."))
    ENDS = [("A", "weren't they?"), ("B", "have you?"), ("C", "don't you?"), ("D", "didn't they?"),
            ("E", "are you?"), ("F", "haven't you?"), ("G", "will she?"), ("H", "doesn't she?"),
            ("I", "isn't it?"), ("J", "am I?")]
    P.append(key_list(ENDS))
    for n, (text, a) in enumerate([
            ("You live in a village,", "C"), ("You're not fifteen years old,", "E"),
            ("Carol has a maths test tomorrow,", "H"), ("They were having lunch at the time,", "A"),
            ("You've been to France,", "F"), ("I'm not the only one,", "J"),
            ("They all passed the test,", "D"), ("You haven't seen Linda anywhere,", "B"),
            ("She won't tell anyone else,", "G"), ("This is the right DVD,", "I")], 1):
        P.append(item(h, "2.1", n, text + " {}", box("2.1", n)))
        K[("2.1", n, 1)] = choose([l for l, _t in ENDS], a)

    P.append(ex("2.2", "**D**  Complete the question tags."))
    for n, (text, a) in enumerate([
            ("Mark doesn't eat meat, {} he?", "does"),
            ("We should phone Grandma, {} we?", "shouldn't/should not"),
            ("I didn't get you into trouble, {} I?", "did"),
            ("You weren't waiting for me, {} you?", "were"),
            ("Jill has finished her homework, {} she?", "hasn't"),
            ("You'll call me later, {} you?", "won't"),
            ("Let's go out tonight, {} we?", "shall"),
            ("I'm going to pass the exam, {} I?", "aren't")], 1):
        P.append(item(h, "2.2", n, text, box("2.2", n, "110px")))
        K[("2.2", n, 1)] = Q(a)

    # ---------------------------------------------------- 3 indirect questions
    P.append(bar(3, "Indirect questions", "asking politely"))
    P.append(panel("TUSHUNTIRISH — BILVOSITA SAVOL", [
        "Muloyimroq soʻrash uchun savolni ibora bilan boshlaymiz: *Can / Could you tell me…? · Can / Could "
        "you let me know…? · Do you know…? · I wonder if you could tell me… · I wonder if you know…*",
        "[[SOʻZ TARTIBI]] Iboradan keyingi qism **oddiy gap** tartibida — avval ega, keyin feʼl, *do / does / "
        "did* yoʻq: *Can you tell me where the bank **is**?* (✗ *where is the bank*) · *Can you let me know "
        "what time the film **starts**?* (✗ *what time does the film start*)",
        "[[HA / YOʻQ SAVOLI]] Soʻroq soʻzi boʻlmasa, *if* ishlatiladi: *Do you know if Alison lives there?*",
    ]))
    P.append(ex("3.1", "**E**  Choose the correct answer."))
    for n, (text, a_opt, b_opt, right) in enumerate([
            ("Excuse me. Could you tell me how much {} , please?", "are these jeans", "these jeans are", "B"),
            ("Can you let me know what time {} ?", "does the train arrive", "the train arrives", "B"),
            ("Do you know if {} at seven o'clock?", "the show starts", "does the show start", "A"),
            ("I wonder if you could tell me what {} .", "is the difference", "the difference is", "B"),
            ("I wonder if you know who {} ask.", "I should", "should I", "A")], 1):
        P.append(item(h, "3.1", n, text, box("3.1", n)))
        K[("3.1", n, 1)] = choose(["A", "B"], right, labels={"A": "A · " + a_opt, "B": "B · " + b_opt})

    P.append(ex("3.2", "**F**  Complete each second sentence so that it has a similar meaning to the first "
                "sentence."))
    for n, (first, start, end, a) in enumerate([
            ("Where's the post office?", "I wonder if you could tell me", ".", "where the post office is"),
            ("Why did you do that?", "Could you tell us", "?", "why you did that"),
            ("How much will the holiday cost?", "Can you let me know", "?", "how much the holiday will cost"),
            ("Are there any cafés near here?", "Could you tell me if", "?",
             "there are any cafés near here/there are any cafes near here"),
            ("Does Jim like jazz music?", "Do you know", "?",
             "if Jim likes jazz music/whether Jim likes jazz music")], 1):
        P.append(item(h, "3.2", n, "%s  →  %s {} %s" % (first, start, end),
                      box("3.2", n, W, "the rest of the sentence")))
        K[("3.2", n, 1)] = write(a)

    h.html = '<div class="booklet">' + "".join(P) + "</div>"
    for label, text in [
            ("1.1", "Har bir gapdagi qalin soʻz yoki ibora notoʻgʻri. Toʻgʻrisini yozing."),
            ("1.2", "Har bir boʻshliqqa bitta soʻz yozing."),
            ("2.1", "Gapni mos soʻroq qoʻshimchasi bilan moslashtiring: harfni tanlang."),
            ("2.2", "Soʻroq qoʻshimchalarini toʻldiring."),
            ("3.1", "Toʻgʻri javobni tanlang."),
            ("3.2", "Ikkinchi gapni birinchisiga maʼnodosh qilib toʻldiring.")]:
        h.say_also(label, text)
    return h.build(K, "Pre-Intermediate", 23,
                   "Destination B1 · Unit 23 — Questions, question tags, indirect questions")


if __name__ == "__main__":
    for code, make in (("dest_b1_12", unit12), ("dest_b1_23", unit23)):
        data = make()
        data["series"] = "destination"
        data["layout"] = data["layout"].replace('<div class="booklet">',
                                                '<div class="booklet" data-lang="uz">', 1)
        out = os.path.join(HERE, code + ".json")
        json.dump(data, open(out, "w"))
        print("\n==== %s: %s" % (code, data["title"]))
        report(data)
