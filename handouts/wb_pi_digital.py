"""Empower Pre-Intermediate Workbook, unit 1 - A & C and B & D - done on a phone.

The workbook is set every week beside the handout. Its PDF on Azamat's Mac
(Desktop / Empower Second Edition - Books / 3. B1 Pre-Intermediate) is a
scan, so the pages are written out again by hand from the page images -
page 4 (1A) and page 6 (1C) - in the booklet's markup: four parts, each
checked, then the next. Each exercise keeps the book's number and letter
(1a, 1b, 2a ...) so paper and screen match. The answers are the book's key
(page 87); the examples the book fills in are shown filled in.

The recordings are the workbook's own (tracks 01.03-01.05, from "Workbook
audio-2"), on a shelf of their own - "Pre-Intermediate Workbook" - since
the class audio numbers its tracks the same way.

The file carries series "workbook": it opens for the class it is set to,
never joins the chain of the course's booklets, and a homework line
"Workbook unit 1 A&C" set to a Pre-Intermediate class is linked to it.

Every instruction has a line in Uzbek under it, as in the Pre-Intermediate
handouts.

B & D (made 3 October 2026, at his request: "full unit 1 ... A/C and B/D
together") is page 5 (1B) and page 7 (1D) in six parts, the book's own
sections; key on page 87, every right form taken (variants.ok): short and full
forms, a corrected sentence whole or only the part that was wrong. The book's
key lists cinema (2a item 3) as a long vowel; its bold letter is the final a,
/ə/ - short - so it is marked short here (he was told). Its tracks 01.01 and
01.02 were checked against the key with an offline transcription before they
went on the workbook shelf.

The unit's last two pages - page 8 (Reading and listening extension) and
page 9 (Review and extension) - are a third handout, "Unit 1 ASRP", which a
homework line for the Academic Skills + Reading Plus + Review lesson finds by
itself ("Workbook unit 1 — Academic Skills, Reading Plus and Review"). Its
track 01.06 was checked the same way. The book's key corrects 1 Grammar item 2
to "at the café"; the sentence says "in", so both count. "I can..." is rated
3 / 2 / 1 with taps that are kept, never marked.

All three are on the students' "Workbook handouts" shelf (handout_shelf):
open to the level as practice, and linked from a homework line as before.

    python3 handouts/wb_pi_digital.py       # writes wb_pi_01ac.json, wb_pi_01bd.json and wb_pi_01asrp.json
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import Q, choose, report                                            # noqa: E402
from dest_b1_digital import md, bar, ex, box, item, para, word_box, cover, handout, panel, key_list  # noqa: E402
from variants import ok  # noqa: E402

W = "95%"


def example(n, html_text):
    """The book's example, shown done."""
    return para('<span style="color:#6E6E6E;font-size:9.5pt">%d  </span>%s  '
                '<span style="color:#6E6E6E;font-size:9.5pt">(example)</span>' % (n, html_text))


def done(word):
    return '<span style="font-weight:700;text-decoration:underline">%s</span>' % md(word)


def listen(track, what):
    """A line naming the track, which the page puts a player under."""
    return para('<span style="font-style:italic">%s — track %s</span>' % (what, track))


def unit1ac():
    h, P, K = handout(), [], {}
    P.append(cover("WORKBOOK  ·  PRE-INTERMEDIATE  ·  UNIT 1", "Communication",
                   "1A Do you play any sports?  ·  1C It was really nice to meet you",
                   ["odamlar, joylar va narsalarni tasvirlaydigan sifatlarni — *delicious, awful, strange, rude*",
                    "savolni toʻgʻri tartibda tuzishni — *Where did you meet…? What was the film like?*",
                    "salomlashish va suhbatni tugatish iboralarini — *Long time no see! I really must go.*",
                    "gapda qaysi soʻzlarga urgʻu tushishini eshitishni"]))

    # ------------------------------------------------ 1 1A vocabulary
    P.append(bar(1, "1A Vocabulary", "common adjectives"))
    P.append(ex("1.1", "**1a**  Choose the correct words to complete the sentences."))
    P.append(example(1, "The new building opposite the university is %s. I hate it!" % done("ugly")))
    for n, (text, opts, a) in enumerate([
            ("Our new teacher is always very {} . We work very hard in her lessons, and she never smiles "
             "or laughs.", ["serious", "silly", "rude"], "serious"),
            ("The cakes in the new bakery are {} !", ["silly", "serious", "delicious"], "delicious"),
            ("My brother's new girlfriend is {} . I think she's a model.", ["ugly", "beautiful", "delicious"],
             "beautiful"),
            ("We played a lot of {} games at Sarah's birthday party. I have some really funny photos on "
             "Facebook.", ["silly", "horrible", "perfect"], "silly"),
            ("Lily's a {} person. Her grandchildren love visiting her.", ["perfect", "strange", "lovely"],
             "lovely")], 2):
        P.append(item(h, "1.1", n, text, box("1.1", n)))
        K[("1.1", n, 1)] = choose(opts, a)

    P.append(ex("1.2", "**1b**  Complete the sentences with the adjectives in the box."))
    P.append(word_box(["all right", "awful", "amazing", "delicious", "rude", "strange", "perfect"]))
    P.append(example(1, "I'm not interested in football. It's so %s." % done("boring")))
    for n, (text, a) in enumerate([
            ("Thanks for the chocolates. They were {} !", "delicious"),
            ("Look at this beautiful weather – it's a {} day to go to the beach.", "perfect"),
            ("The film we watched last night was really {} . I didn't understand it at all.", "strange"),
            ("**A** How was the restaurant?  **B** Oh, it was {} . There are better Italian restaurants in "
             "my town.", "all right"),
            ("The weather in Scotland was {} . It rained every day.", "awful"),
            ("The band were {} ! It was the best concert I've ever been to.", "amazing"),
            ("The waiter at the hotel was {} . He said he couldn't help us because we're vegetarian.",
             "rude")], 2):
        P.append(item(h, "1.2", n, text, box("1.2", n)))
        K[("1.2", n, 1)] = Q(a)

    # ------------------------------------------------ 2 1A grammar
    P.append(bar(2, "1A Grammar", "question forms"))
    P.append(ex("2.1", "**2a**  Choose the correct words to complete the questions."))
    P.append(example(1, "How many children %s?" % done("does he have")))
    for n, (text, opts, a) in enumerate([
            ("Where {} your husband?", ["did you meet", "did meet you", "you met"], "did you meet"),
            ("{} in this area?", ["Did he grow up", "He grew up", "He did grow up"], "Did he grow up"),
            ("What {} ?", ["was like the film", "was the film like", "the film was like"], "was the film like"),
            ("How much {} for your smartphone?", ["paid you", "you did pay", "did you pay"], "did you pay"),
            ("{} to the USA?", ["Why she go", "Why she went", "Why did she go"], "Why did she go"),
            ("How many films {} last year?", ["he made", "did he make", "did make he"], "did he make"),
            ("How {} ?", ["was your holiday", "your holiday was", "did your holiday be"], "was your holiday")], 2):
        P.append(item(h, "2.1", n, text, box("2.1", n)))
        K[("2.1", n, 1)] = choose(opts, a)

    P.append(ex("2.2", "**2b**  Put the words in the correct order to make questions."))
    P.append(example(1, "you / Sarah's friend / are ?  →  %s" % done("Are you Sarah's friend?")))
    for n, (words, a) in enumerate([
            ("work / a bank / he / does / in ?", "Does he work in a bank?"),
            ("you / last month / to New York / go / did / why ?", "Why did you go to New York last month?"),
            ("like / that new Brazilian / what / restaurant / is ?",
             "What is that new Brazilian restaurant like?/What's that new Brazilian restaurant like?"),
            ("with your sister / who / that man / was ?", "Who was that man with your sister?"),
            ("TV programmes / you / do / watch / what type of ?", "What type of TV programmes do you watch?"),
            ("go to / did / which university / you ?", "Which university did you go to?"),
            ("did / how much / cost / the tickets ?", "How much did the tickets cost?")], 2):
        P.append(item(h, "2.2", n, words + "  {}", box("2.2", n, W, "the question")))
        K[("2.2", n, 1)] = Q(a)

    # ------------------------------------------------ 3 1C useful language
    P.append(bar(3, "1C Useful language", "greeting people, ending conversations"))
    P.append(ex("3.1", "**1a**  Choose the correct words to complete the conversation."))
    lines = [("SAM", "Hi, James! (1) %s time no see! How are you?" % done("Long"), None),
             ("JAMES", "Hi, Sam. I'm fine, thanks. (2) {} lovely surprise! Great to see you!",
              (["What a", "What", "How"], "What a")),
             ("SAM", "Yes, it's really nice (3) {} , too.", (["see you", "to see you", "you see"], "to see you")),
             ("JAMES", "Where are you living (4) {} ?", (["today", "this day", "these days"], "these days")),
             ("SAM", "Oh, not (5) {} here. In Park Road, near the sports centre.",
              (["far from", "far of", "far away"], "far from")),
             ("JAMES", "Oh, (6) {} nice!", (["what", "how", "who"], "how")),
             ("SAM", "And (7) {} my wife, Jackie.", (["she is", "it is", "this is"], "this is")),
             ("JAMES", "Your wife – wow! That's fantastic (8) {} !", (["new", "news", "notices"], "news")),
             ("JAMES", "Nice to (9) {} you, Jackie.", (["meet", "meat", "meeting"], "meet")),
             ("JACKIE", "Nice to meet you, (10) {} .", (["two", "too", "to"], "too"))]
    for who, said, pick in lines:
        if pick is None:
            P.append(para('<span style="font-weight:700">%s</span>  %s' % (who, said)))
            continue
        n = int(said.split("(")[1].split(")")[0])
        before, after = said.split("{}")
        h.texts[("3.1", n)] = "%s: %s …… %s" % (who, before.replace("(%d) " % n, ""), after)
        P.append(para('<span style="font-weight:700">%s</span>  %s<span style="font-weight:700">(%d)</span> %s%s'
                      % (who, md(before.replace("(%d) " % n, "")), n, box("3.1", n), md(after))))
        K[("3.1", n, 1)] = choose(pick[0], pick[1])
    P.append(listen("01.03", "1b  Listen and check"))

    P.append(ex("3.2", "**1c**  Complete the sentences with the words in the box."))
    P.append(word_box(["surprise", "hello", "meet", "news", "again", "time", "last", "must", "up"]))
    P.append(example(1, "Sea View Road? Oh, how %s!" % done("nice")))
    for n, (text, a) in enumerate([
            ("Your husband – wow! That's fantastic {} !", "news"), ("We really {} go. We're late.", "must"),
            ("What a lovely {} !", "surprise"), ("Say {} to Roger for me.", "hello"),
            ("Long {} no see!", "time"), ("It was really nice to {} you.", "meet"),
            ("We must meet {} soon.", "up"), ("It was great to see you {} .", "again"),
            ("When did we {} see each other?", "last")], 2):
        P.append(item(h, "3.2", n, text, box("3.2", n)))
        K[("3.2", n, 1)] = Q(a)
    P.append(listen("01.04", "1d  Listen and check"))

    # ------------------------------------------------ 4 1C pronunciation
    P.append(bar(4, "1C Pronunciation", "sentence stress"))
    P.append(ex("4.1", "**2a**  Listen to the sentences. Write the stressed words, in order, with commas."))
    P.append(listen("01.05", "Listen"))
    P.append(example(1, "I'm %s sure it was %s %s ago.  →  pretty, two, months"
                     % (done("pretty"), done("two"), done("months"))))
    for n, (text, a) in enumerate([
            ("What a lovely surprise!", "lovely, surprise"),
            ("It was really nice to meet you.", "really, nice, meet"),
            ("I'm sorry, but I really must go.", "sorry, must, go"),
            ("Where are you living these days?", "Where, living"),
            ("I'm late for a meeting.", "late, meeting")], 2):
        P.append(item(h, "4.1", n, text + "  {}", box("4.1", n, "220px", "stressed words")))
        K[("4.1", n, 1)] = Q(a)

    h.html = '<div class="booklet">' + "".join(P) + "</div>"
    for label, text in [
            ("1.1", "Gaplarni toʻldirish uchun toʻgʻri soʻzni tanlang."),
            ("1.2", "Gaplarni qutichadagi sifatlar bilan toʻldiring."),
            ("2.1", "Savollarni toʻldirish uchun toʻgʻri variantni tanlang."),
            ("2.2", "Soʻzlarni toʻgʻri tartibda qoʻyib, savol tuzing."),
            ("3.1", "Suhbatni toʻldirish uchun toʻgʻri soʻzlarni tanlang. Keyin tinglab tekshiring."),
            ("3.2", "Gaplarni qutichadagi soʻzlar bilan toʻldiring. Keyin tinglab tekshiring."),
            ("4.1", "Gaplarni tinglang va urgʻu tushgan soʻzlarni tartib bilan, vergul bilan ajratib yozing.")]:
        h.say_also(label, text)
    return h.build(K, "Pre-Intermediate", 1, "Workbook · Unit 1A & 1C — Communication")


def spans(sentence, fix):
    """A corrected sentence, and every stretch of it that holds the correction:
    "Yesterday we visited ...", "we visited", "visited" - whichever a student
    writes."""
    words = sentence.split()
    want = fix.lower().split()
    clean = [w.lower().strip(".,!?") for w in words]
    for i in range(len(words) - len(want) + 1):
        if clean[i:i + len(want)] == want:
            break
    else:
        raise SystemExit("%r is not in %r" % (fix, sentence))
    out = []
    for a in range(0, i + 1):
        for b in range(i + len(want), len(words) + 1):
            out.append(" ".join(words[a:b]).strip(",") if b < len(words) else " ".join(words[a:b]))
    return out


def unit1bd():
    h, P, K = handout(), [], {}
    P.append(cover("WORKBOOK  ·  PRE-INTERMEDIATE  ·  UNIT 1", "Communication",
                   "1B I'm really into social media  ·  1D I'm sending you some photos",
                   ["*really, absolutely, hardly ever* kabi ravishlarni gapda toʻgʻri joyga qoʻyishni",
                    "uzun va qisqa unli tovushlarni eshitib farqlashni",
                    "Present Simple va Present Continuous ni farqlashni — *She loves… · She's studying…*",
                    "elektron xatni oʻqib tushunishni va gapdagi xatolarni topib tuzatishni",
                    "taʼtil haqida doʻstingizga xat yozishni"]))

    # ------------------------------------------------ 1 1B vocabulary
    P.append(bar(1, "1B Vocabulary", "adverbs"))
    P.append(ex("1.1", "**1a**  Put the words in brackets in the correct place in each sentence."))
    P.append(example(1, "They see their grandchildren now that they live in Australia. (hardly ever)  →  %s"
                     % done("They hardly ever see their grandchildren now that they live in Australia.")))
    for n, (text, answers) in enumerate([
            ("I enjoy watching old Hollywood films. (particularly)",
             ["I particularly enjoy watching old Hollywood films"]),
            ("She hates it when people are late for meetings. (absolutely)",
             ["She absolutely hates it when people are late for meetings"]),
            ("We go to Italian restaurants, but sometimes we go to Turkish ones. (usually)",
             ["We usually go to Italian restaurants, but sometimes we go to Turkish ones",
              "Usually we go to Italian restaurants, but sometimes we go to Turkish ones"]),
            ("We're sure his flight arrives at Terminal 2, but I need to check. (pretty)",
             ["We're pretty sure his flight arrives at Terminal 2, but I need to check"]),
            ("I hope he brings his beautiful sister to the party! (really)",
             ["I really hope he brings his beautiful sister to the party"])], 2):
        P.append(item(h, "1.1", n, text + "  {}", box("1.1", n, W, "the sentence")))
        K[("1.1", n, 1)] = Q(ok(*answers))

    P.append(ex("1.2", "**1b**  Choose the correct adverbs to complete the sentences."))
    P.append(example(1, "I love rock music, but I %s like the Foo Fighters. They're my favourite band."
                     % done("especially")))
    for n, (text, opts, a) in enumerate([
            ("He {} calls his mother – maybe once or twice a month.", ["hardly ever", "never", "especially"],
             "hardly ever"),
            ("I {} enjoy horror films, but this one was awful!", ["rarely", "pretty", "usually"], "usually"),
            ("She's {} good-looking, but I don't think she's beautiful.", ["fairly", "absolutely", "rarely"],
             "fairly"),
            ("I {} hate maths. I just don't understand it!", ["never", "absolutely", "hardly ever"], "absolutely"),
            ("She {} takes her family out for dinner – only when it's her birthday.",
             ["usually", "particularly", "rarely"], "rarely"),
            ("They love all sports, but they're {} interested in football. They watch all the matches on TV.",
             ["fairly", "really", "pretty"], "really"),
            ("It's {} cold today, so why don't you take your gloves?", ["pretty", "usually", "rarely"],
             "pretty")], 2):
        P.append(item(h, "1.2", n, text, box("1.2", n)))
        K[("1.2", n, 1)] = choose(opts, a)

    # ------------------------------------------------ 2 1B pronunciation
    P.append(bar(2, "1B Pronunciation", "long and short vowels"))
    P.append(ex("2.1", "**2a**  Listen to the words. Do the letters in **bold** make a long vowel sound? Choose "
                       "**yes** (long) or **no** (short)."))
    P.append(listen("01.01", "Listen"))
    P.append(example(1, "b**ir**thday  →  %s" % done("yes — long")))
    LONG = {"yes": "yes · long", "no": "no · short"}
    for n, (word, a) in enumerate([("b**a**nk", "no"), ("cinem**a**", "no"), ("f**oo**d", "yes"),
                                   ("p**ar**ty", "yes"), ("s**i**lly", "no"), ("m**u**sic", "yes"),
                                   ("sp**or**t", "yes"), ("fr**ie**ndly", "no"), ("bl**o**g", "no")], 2):
        P.append(item(h, "2.1", n, word + "  {}", box("2.1", n, "60px")))
        h.texts[("2.1", n)] = word.replace("**", "")       # "bank", not "b a nk", on his pages
        K[("2.1", n, 1)] = choose(["yes", "no"], a, labels=LONG)

    # ------------------------------------------------ 3 1B grammar
    P.append(bar(3, "1B Grammar", "present simple and present continuous"))
    P.append(ex("3.1", "**3a**  Choose the correct verb forms to complete the sentences."))
    P.append(example(1, "She %s reading fashion magazines at the hairdresser's." % done("loves")))
    for n, (text, opts, a) in enumerate([
            ("We usually {} to the café opposite the hotel.", ["are going", "goes", "go"], "go"),
            ("I {} a great book in English at the moment.", ["read", "'m reading", "reading"], "'m reading"),
            ("He {} to call his family in Tokyo. Can he use the wi-fi?", ["does want", "'s wanting", "wants"],
             "wants"),
            ("Why {} for the bus? Let's walk home.", ["are you waiting", "do you wait", "you waiting"],
             "are you waiting"),
            ("I hardly ever {} my cousins in Ireland.", ["am visiting", "visit", "visits"], "visit"),
            ("She {} French politics at university this term.", ["studies", "studying", "'s studying"],
             "'s studying"),
            ("Yes, they're here. They {} a video game in the living room.", ["play", "'re playing", "playing"],
             "'re playing")], 2):
        P.append(item(h, "3.1", n, text, box("3.1", n)))
        K[("3.1", n, 1)] = choose(opts, a)

    P.append(ex("3.2", "**3b**  Complete the conversation with the present simple or present continuous forms of "
                       "the verbs in brackets. Use contractions where possible."))
    lines = [("MEGAN", "What (1) %s (Andrea, do) in that shop?" % done("'s Andrea doing"), []),
             ("NAOMI", "She (2) {} (buy) some postcards to send to her family.", [(2, ok("'s buying"))]),
             ("MEGAN", "Really? I (3) {} usually (4) {} (not send) postcards. I usually (5) {} (write) a message on "
                       "Facebook. And sometimes I (6) {} (post) a few photos of my holiday on Instagram.",
              [(3, ok("don't")), (4, "send"), (5, "write"), (6, "post")]),
             ("NAOMI", "Yes, me too, but Andrea's grandparents (7) {} (not use) social media, so she (8) {} (send) "
                       "them postcards instead.", [(7, ok("don't use")), (8, "sends")]),
             ("MEGAN", "Oh, and what (9) {} (Marco and Jack, do) this morning?", [(9, "are Marco and Jack doing")]),
             ("NAOMI", "They (10) {} (spend) the day at the beach.", [(10, ok("'re spending"))]),
             ("MEGAN", "But Marco (11) {} (not like) swimming in the sea. He says the water's too cold.",
              [(11, ok("doesn't like"))]),
             ("NAOMI", "Yes, but it (12) {} (be) really hot today!", [(12, ok("'s"))])]
    for who, said, gaps in lines:
        if not gaps:
            P.append(para('<span style="font-weight:700">%s</span>  %s' % (who, said)))
            continue
        bits = said.split("{}")
        out = md(bits[0])
        for (n, a), tail in zip(gaps, bits[1:]):
            h.texts[("3.2", n)] = "%s: …(%d)… %s" % (who, n, tail.strip()[:60])
            out += box("3.2", n, "150px") + md(tail)
            K[("3.2", n, 1)] = Q(a)
        P.append(para('<span style="font-weight:700">%s</span>  %s' % (who, out)))
    P.append(listen("01.02", "3c  Listen and check"))

    # ------------------------------------------------ 4 1D reading
    P.append(bar(4, "1D Reading", "an email from India"))
    P.append(panel("NANDEEP'S EMAIL", [
        "Hi Hannah,",
        "I hope you're enjoying your stay in Boston.",
        "I'm spending a month in India on holiday. I'm staying with my aunt and uncle and my two cousins in Delhi. "
        "I don't speak much Hindi, but they all speak English very well, so communication isn't a problem. They're "
        "taking me to see a lot of really interesting places. Yesterday we drove to Agra and visited the Taj Mahal. "
        "It took two hours to get there. This is a photo I took – what an amazing building!",
        "It's really hot here all the time, but my aunt and uncle have a swimming pool, so we spend a lot of our "
        "time in the water – it's so relaxing! In the evening, I usually go to cafés with my cousins and their "
        "friends.",
        "I'm having a great time here in India!",
        "See you soon.",
        "Nandeep"]))
    P.append(ex("4.1", "**1a**  Read Nandeep's email to Hannah and choose the correct answer."))
    for letter, text in [("a", "Nandeep is staying at the Taj Mahal hotel in Delhi."),
                         ("b", "Nandeep is visiting his cousins in Boston."),
                         ("c", "Nandeep is on holiday at his aunt and uncle's house in Delhi.")]:
        P.append(para('<span style="font-weight:700">%s</span>  %s' % (letter, md(text))))
    P.append(item(h, "4.1", 1, "The correct answer:  {}", box("4.1", 1)))
    K[("4.1", 1, 1)] = choose(["a", "b", "c"], "c")
    P.append(ex("4.2", "**1b**  Read the email again. Are the sentences true (*T*) or false (*F*)?"))
    for n, (text, a) in enumerate([
            ("Nandeep mainly speaks in Hindi to his cousins.", "F"),
            ("He's visiting a lot of places while he's in India.", "T"),
            ("The Taj Mahal is in Delhi.", "F"),
            ("Nandeep didn't enjoy visiting the Taj Mahal.", "F"),
            ("Nandeep often uses his aunt and uncle's pool.", "T"),
            ("Nandeep isn't enjoying his holiday.", "F")], 1):
        P.append(item(h, "4.2", n, text + "  {}", box("4.2", n, "60px")))
        K[("4.2", n, 1)] = choose(["T", "F"], a, labels={"T": "T · true", "F": "F · false"})

    # ------------------------------------------------ 5 1D writing skills
    P.append(bar(5, "1D Writing skills", "correcting mistakes"))
    P.append(ex("5.1", "**2a**  Correct the sentences. Write the correct sentence, or the part that was wrong."))
    P.append(example(1, "I'm having a lovely time here in france.  →  %s"
                     % done("I'm having a lovely time here in France.")))
    for n, (wrong, right, fix) in enumerate([
            ("Yesterday we visitted the Palace of Versailles near Paris.",
             "Yesterday we visited the Palace of Versailles near Paris.", "visited"),
            ("In the mornings, I usually going to the beach with my Portuguese friends.",
             "In the mornings, I usually go to the beach with my Portuguese friends.", "go"),
            ("I hope your having a great time in Canada with your family.",
             "I hope you're having a great time in Canada with your family.", "you're"),
            ("Their English are very good, but we always speak in German.",
             "Their English is very good, but we always speak in German.", "is")], 2):
        P.append(item(h, "5.1", n, wrong + "  {}", box("5.1", n, W, "the correct sentence")))
        K[("5.1", n, 1)] = Q(ok(*spans(right.rstrip("."), fix), limit=400))

    # ------------------------------------------------ 6 1D writing
    P.append(bar(6, "1D Writing", "a holiday email"))
    P.append(panel("PAUL'S EMAIL", [
        "Hi Maria,",
        "Hope you're having a nice holiday. Tell me all about it! *(Describe my holiday)*",
        "What's the hotel like? *(Not in a hotel – staying with my family!)*",
        "What do you do every day? *(Explain and send a photo)*",
        "See you soon! *(He OK? Ask)*",
        "Love,  Paul"]))
    P.append(ex("6.1", "**3a**  Read the email from Paul. Use the notes in brackets to write Maria's reply."))
    P.append(item(h, "6.1", 1, "{}", box("6.1", 1, W, "Hi Paul, …")))
    K[("6.1", 1, 1)] = Q(None, control="essay")

    h.html = '<div class="booklet">' + "".join(P) + "</div>"
    for label, text in [
            ("1.1", "Qavsdagi soʻzlarni har bir gapda toʻgʻri joyga qoʻying. Butun gapni yozing."),
            ("1.2", "Gaplarni toʻldirish uchun toʻgʻri ravishni tanlang."),
            ("2.1", "Soʻzlarni tinglang. Qalin harflar uzun unli tovush beradimi? *yes* (uzun) yoki *no* (qisqa) ni "
                    "tanlang."),
            ("3.1", "Gaplarni toʻldirish uchun feʼlning toʻgʻri shaklini tanlang."),
            ("3.2", "Suhbatni qavsdagi feʼllarning Present Simple yoki Present Continuous shakli bilan toʻldiring. "
                    "Imkon boʻlsa, qisqa shaklni ishlating (*'s, don't*). Keyin tinglab tekshiring."),
            ("4.1", "Nandipning Hannaga yozgan xatini oʻqing va toʻgʻri javobni tanlang."),
            ("4.2", "Xatni yana oʻqing. Gaplar toʻgʻri (*T*) mi yoki notoʻgʻri (*F*) mi?"),
            ("5.1", "Gaplarni tuzating. Toʻgʻri gapni yoki notoʻgʻri boʻlgan qismini yozing."),
            ("6.1", "Pauldan kelgan xatni oʻqing. Qavsdagi qaydlardan foydalanib, Mariyaning javobini yozing.")]:
        h.say_also(label, text)
    return h.build(K, "Pre-Intermediate", 1, "Workbook · Unit 1B & 1D — Communication")


def corrected(*pairs, limit=400):
    """Every right way to give a corrected sentence: (sentence, the words put
    right) for each acceptable version."""
    forms = []
    for sentence, fix in pairs:
        forms += spans(sentence, fix)
    return ok(*forms, limit=limit)


def unit1review():
    h, P, K = handout(), [], {}
    P.append(cover("WORKBOOK  ·  PRE-INTERMEDIATE  ·  UNIT 1", "Communication",
                   "Reading and listening extension  ·  Review and extension",
                   ["chet elda ishlash haqidagi maqolani oʻqib tushunishni",
                    "talabalar qanday doʻst orttirishi haqidagi podkastni tinglab tushunishni",
                    "1-unitdagi grammatika va soʻz xatolarini topib tuzatishni",
                    "*like* ning turli maʼnolarini — *It looks like… · if you like · like Batman*",
                    "oʻz yutuqlaringizni baholashni"]))

    # ------------------------------------------------ 1 extension reading
    P.append(bar(1, "Extension Reading", "working abroad"))
    P.append(panel("WORKING ABROAD: IS IT FOR YOU?", [
        "Are you looking for a new challenge at work? Do you want to meet new people and travel? Lots of people "
        "work abroad to experience a new culture. British people especially have a positive experience – 74% of "
        "Brits who live abroad say they feel at home in their new country! I talked to some young people from the "
        "UK about their experiences.",
        "**EMMA, 27, MEXICO CITY**  I work as an English teacher in Mexico City. It's an amazing city! It's cheap to "
        "live here, so I'm saving quite a lot of money. Working abroad is not for everyone. I love Mexico, but I "
        "miss home too. My plan is to return home in three months. One year abroad is enough for me!",
        "**VANESSA, 25, BERLIN**  I've been in Berlin for two years. I work in IT. My job is sometimes boring, but "
        "the city is exciting! I've also travelled to other parts of the country. It's easy to travel around "
        "Germany, so I try to see a new city or town once a month. I'd like to stay here for a long time and never "
        "stop seeing new places.",
        "**TONY, 24, PARIS**  Living in Paris is very different from back home, but I love my life here. I'm "
        "studying basic French and working as an event planner for a British company. I travel all over Europe "
        "for work and have friends and colleagues in many countries – my life is very exciting!",
        "You might face some problems living abroad, but a lot of people are doing it these days. It helps you "
        "grow professionally and personally. Why don't you see what opportunities are outside your country?"]))
    P.append(ex("1.1", "**1a**  Read the article. Match the statements 1–3 with the people a–c."))
    P.append(key_list([("a", "Vanessa"), ("b", "Tony"), ("c", "Emma")]))
    P.append(example(1, "Living abroad is different from living in the UK.  →  %s" % done("b")))
    PEOPLE = {"a": "a · Vanessa", "b": "b · Tony", "c": "c · Emma"}
    for n, (text, a) in enumerate([("Not everyone would love working abroad.", "c"),
                                   ("It's important to see new places often.", "a")], 2):
        P.append(item(h, "1.1", n, text + "  {}", box("1.1", n, "60px")))
        K[("1.1", n, 1)] = choose(["a", "b", "c"], a, labels=PEOPLE)

    P.append(ex("1.2", "**1b**  Read the article again and choose the best endings for the sentences."))
    P.append(example(1, "British people living abroad … %s" % done("b  often have a positive experience.")))
    for n, (stem, opts, a) in enumerate([
            ("Emma …", ["has been in Mexico for three months.", "thinks Mexico City is wonderful.",
                        "wants to stay abroad more than a year."], "b"),
            ("Vanessa …", ["thinks that Berlin is a cheap city.", "thinks her job is exciting.",
                           "often travels outside Berlin."], "c"),
            ("Tony …", ["doesn't speak a lot of French.", "works with only British people.",
                        "travels outside Europe for work."], "a"),
            ("The writer of the article thinks that …", ["living abroad is easy.",
                                                         "living abroad can help you with future jobs.",
                                                         "there are many opportunities to work abroad."], "b")], 2):
        P.append(item(h, "1.2", n, stem + "  {}", box("1.2", n, "60px")))
        for letter, o in zip("abc", opts):
            P.append(para('<span style="font-weight:700">%s</span>  %s' % (letter, md(o)),
                          style="margin-bottom:2px;line-height:1.4;padding-left:72px"))
        K[("1.2", n, 1)] = choose(["a", "b", "c"], a)

    P.append(ex("1.3", "**1c**  Write a paragraph about the advantages and disadvantages of living and working "
                       "abroad. Think about: family and friends · possible problems with the new language and "
                       "culture · the stories in the article · your own experience."))
    P.append(item(h, "1.3", 1, "{}", box("1.3", 1, W, "Your paragraph")))
    K[("1.3", 1, 1)] = Q(None, control="essay")

    # ------------------------------------------------ 2 extension listening
    P.append(bar(2, "Extension Listening", "making friends at university"))
    P.append(ex("2.1", "**2a**  Listen to the podcast. Match 1–3 with a–c to make true sentences."))
    P.append(listen("01.06", "Listen"))
    P.append(key_list([("a", "goes to a club every week."), ("b", "is friends with the people he lives with."),
                       ("c", "meets people in a café every week.")]))
    P.append(example(1, "Sophia  →  %s" % done("c")))
    for n, (who, a) in enumerate([("Ollie", "a"), ("Ethan", "b")], 2):
        P.append(item(h, "2.1", n, who + "  {}", box("2.1", n, "60px")))
        K[("2.1", n, 1)] = choose(["a", "b", "c"], a)

    P.append(ex("2.2", "**2b**  Listen to the podcast again and choose the best endings for the sentences."))
    P.append(example(1, "The podcast is about … %s" % done("c  how people make friends.")))
    for n, (stem, opts, a) in enumerate([
            ("Ollie doesn't …", ["usually go to bars.", "like making friends with new people.",
                                 "find it difficult to meet people at university."], "a"),
            ("Ollie likes …", ["going to parties with his friends.", "people who like similar things to him.",
                               "the countryside near where he lives."], "b"),
            ("Sophia is interested in …", ["making friends with people studying drama.", "joining a club.",
                                           "meeting a lot of different people."], "c"),
            ("Ethan doesn't …", ["use the Internet to meet people.", "like the people he lives with.",
                                 "usually go out in the evening."], "a"),
            ("Which of the sentences is true about the students?",
             ["The university is helping all the students make friends.",
              "The students are making friends in different ways."], "b")], 2):
        P.append(item(h, "2.2", n, stem + "  {}", box("2.2", n, "60px")))
        for letter, o in zip("abc", opts):
            P.append(para('<span style="font-weight:700">%s</span>  %s' % (letter, md(o)),
                          style="margin-bottom:2px;line-height:1.4;padding-left:72px"))
        K[("2.2", n, 1)] = choose(list("abc"[:len(opts)]), a)

    P.append(ex("2.3", "**2c**  Write questions and answers about what you do in your free time and who you spend "
                       "it with. Think about: Where do you spend your free time? · What do you do and how often? · "
                       "Who do you spend your free time with?"))
    P.append(item(h, "2.3", 1, "{}", box("2.3", 1, W, "Your questions and answers")))
    K[("2.3", 1, 1)] = Q(None, control="essay")

    # ------------------------------------------------ 3 review grammar
    P.append(bar(3, "Review Grammar", "question forms · present simple and continuous"))
    P.append(ex("3.1", "**1**  Correct the sentences. Write the correct sentence, or the part that was wrong."))
    P.append(example(1, "Where you went on holiday last year?  →  %s" % done("Where did you go on holiday last year?")))
    for n, (wrong, answers) in enumerate([
            ("At the moment, she works in the café by the bus station.",
             [("At the moment, she's working in the café by the bus station", "she's working"),
              ("At the moment, she's working at the café by the bus station", "she's working")]),
            ("Why you missed the bus?", [("Why did you miss the bus?", "did you miss")]),
            ("I can't talk to you now because I do my homework.",
             [("I can't talk to you now because I'm doing my homework", "I'm doing")]),
            ("What kind of music you usually listen to?",
             [("What kind of music do you usually listen to?", "do you usually listen")]),
            ("They waiting for the coach to London.", [("They're waiting for the coach to London", "They're waiting")])],
            2):
        P.append(item(h, "3.1", n, wrong + "  {}", box("3.1", n, W, "the correct sentence")))
        K[("3.1", n, 1)] = Q(corrected(*answers))

    # ------------------------------------------------ 4 review vocabulary
    P.append(bar(4, "Review Vocabulary", "adjectives and adverbs"))
    P.append(ex("4.1", "**2**  Correct the sentences. Write the correct sentence, or the word that was wrong."))
    P.append(example(1, "The new Batman film is amaizing!  →  %s" % done("The new Batman film is amazing!")))
    for n, (wrong, answers) in enumerate([
            ("We very enjoyed the film last night.",
             [("We really enjoyed the film last night", "really"),
              ("We enjoyed the film very much last night", "very much")]),
            ("We had a luvly time at the party last night.",
             [("We had a lovely time at the party last night", "lovely")]),
            ("I think our history lessons are so borring.",
             [("I think our history lessons are so boring", "boring")]),
            ("I think that man's a bit extrange. Look, he's talking to himself.",
             [("I think that man's a bit strange. Look, he's talking to himself", "strange")]),
            ("New York's allright, but I prefer living in London, actually.",
             [("New York's all right, but I prefer living in London, actually", "all right"),
              ("New York's alright, but I prefer living in London, actually", "alright")])], 2):
        P.append(item(h, "4.1", n, wrong + "  {}", box("4.1", n, W, "the correct sentence")))
        K[("4.1", n, 1)] = Q(corrected(*answers))

    # ------------------------------------------------ 5 wordpower and progress
    P.append(bar(5, "Review Wordpower", "like  ·  review your progress"))
    P.append(ex("5.1", "**3**  Match 1–8 with a–h to make sentences."))
    P.append(key_list([("a", "like a perfect day for the beach."), ("b", "like this one. How much is it?"),
                       ("c", "like Jacob. They've got the same smile."), ("d", "like you're having a great holiday."),
                       ("e", "if you like."), ("f", "like Katy Perry."), ("g", "like Batman and Spider-Man."),
                       ("h", "like last night?")]))
    P.append(example(1, "We can go for a walk in the park  →  %s" % done("e")))
    for n, (text, a) in enumerate([("What was the party", "h"), ("What amazing weather! It looks", "a"),
                                   ("The boy in the white T-shirt looks", "c"),
                                   ("He loves films with superheroes, you know,", "g"),
                                   ("I absolutely love this singer. She sounds", "f"),
                                   ("I want to buy a computer", "b"), ("Thanks for your email. It sounds", "d")], 2):
        P.append(item(h, "5.1", n, text + "  {}", box("5.1", n, "60px")))
        K[("5.1", n, 1)] = choose(list("abcdefgh"), a)
    P.append(ex("5.2", "**Review your progress**  How well can you do these things now? 3 = very well · 2 = well · "
                       "1 = not so well"))
    RATE = {"3": "3 · very well", "2": "2 · well", "1": "1 · not so well"}
    for n, text in enumerate(["ask and answer personal questions", "talk about how I communicate",
                              "greet people and end conversations", "write a personal email"], 1):
        P.append(item(h, "5.2", n, "I can " + text + "  {}", box("5.2", n, "60px")))
        K[("5.2", n, 1)] = Q(None, options=["3", "2", "1"], labels=RATE)   # theirs: kept, not marked

    h.html = '<div class="booklet">' + "".join(P) + "</div>"
    for label, text in [
            ("1.1", "Maqolani oʻqing. 1–3 gaplarni a–c odamlar bilan moslang."),
            ("1.2", "Maqolani yana oʻqing va gaplarning eng toʻgʻri davomini tanlang."),
            ("1.3", "Chet elda yashash va ishlashning yaxshi va yomon tomonlari haqida bitta xatboshi yozing. Oila va "
                    "doʻstlar, yangi til va madaniyatdagi qiyinchiliklar, maqoladagi hikoyalar va oʻz tajribangiz "
                    "haqida oʻylang."),
            ("2.1", "Podkastni tinglang. Toʻgʻri gap hosil qilish uchun 1–3 ni a–c bilan moslang."),
            ("2.2", "Podkastni yana tinglang va gaplarning eng toʻgʻri davomini tanlang."),
            ("2.3", "Boʻsh vaqtingizda nima qilishingiz va uni kim bilan oʻtkazishingiz haqida savollar va javoblar "
                    "yozing."),
            ("3.1", "Gaplarni tuzating. Toʻgʻri gapni yoki notoʻgʻri boʻlgan qismini yozing."),
            ("4.1", "Gaplarni tuzating. Toʻgʻri gapni yoki notoʻgʻri yozilgan soʻzni yozing."),
            ("5.1", "Gap hosil qilish uchun 1–8 ni a–h bilan moslang."),
            ("5.2", "Oʻz yutuqlaringizni baholang. Endi bularni qanchalik yaxshi qila olasiz? 3 — juda yaxshi, "
                    "2 — yaxshi, 1 — unchalik emas.")]:
        h.say_also(label, text)
    return h.build(K, "Pre-Intermediate", 1, "Workbook · Unit 1 ASRP — Extension and review")


if __name__ == "__main__":
    for build, name in [(unit1ac, "wb_pi_01ac.json"), (unit1bd, "wb_pi_01bd.json"),
                        (unit1review, "wb_pi_01asrp.json")]:
        data = build()
        data["series"] = "workbook"
        data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
        out = os.path.join(HERE, name)
        json.dump(data, open(out, "w"))
        print("==", name)
        report(data)
