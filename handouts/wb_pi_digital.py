"""Empower Pre-Intermediate Workbook, unit 1 A & C - done on a phone.

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

    python3 handouts/wb_pi_digital.py       # writes handouts/wb_pi_01ac.json
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import Q, choose, report                                            # noqa: E402
from dest_b1_digital import md, bar, ex, box, item, para, word_box, cover, handout  # noqa: E402

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


if __name__ == "__main__":
    data = unit1ac()
    data["series"] = "workbook"
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "wb_pi_01ac.json")
    json.dump(data, open(out, "w"))
    report(data)
