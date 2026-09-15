"""Write the Pre-Intermediate Unit 2 ASRP handout in Azamat's booklet style.

The Pre-intermediate Empower book on this machine is an image-only scan, so
the content here is written rather than lifted: it is built on what Unit 2
actually teaches in his own P02AC/P02BD booklets - past simple, past
continuous, tourism and travel collocations - and follows the shape of his
Unit 1 ASRP homework exactly: chunks, grammar in context, the strategy, a new
text, a short piece of writing, and a self-check.
"""
import html, json, re

TEAL, DEEP, SOFT, GREY, INK, RULE = ("#127D80", "#0B5456", "#F2F8F8",
                                     "#6E6E6E", "#1A1A1A", "#C9C9C9")
BLANK = "{}"
Q = []                                   # every blank, in reading order


def esc(t):
    return html.escape(t)


def gaps(text, answers, label, num):
    """Turn {} into boxes, and remember the answer each one wants."""
    parts = text.split(BLANK)
    out = parts[0]
    for i, tail in enumerate(parts[1:]):
        ans = answers[i] if i < len(answers) else None
        Q.append({"num": len(Q) + 1,
                  "kind": "typed" if ans else "open",
                  "prompt": "%s  %s" % (label, re.sub(r"\s+", " ", text)[:150]),
                  "answer": ans, "options": []})
        out += ('<input class="bk-blank" data-q="%d" style="width:%dpx" '
                'autocomplete="off" autocapitalize="off" spellcheck="false">'
                % (len(Q), 150 if ans and len(ans) > 9 else 110))
        out += tail
    return out


def eyebrow(t):
    return (f'<p style="margin-bottom:2px"><span style="font-weight:700;'
            f'color:{TEAL};font-size:8pt;letter-spacing:1.6px">{esc(t)}</span></p>')


def title(t):
    return (f'<p style="margin-bottom:4px"><span style="font-weight:700;'
            f'color:{DEEP};font-size:20pt">{esc(t)}</span></p>')


def strap(bold, rest):
    return (f'<p style="margin-bottom:6px;border-bottom:1px solid {TEAL};'
            f'padding-bottom:6px"><span style="font-weight:700;font-size:10pt">'
            f'{esc(bold)}</span> <span style="font-style:italic;color:{GREY};'
            f'font-size:10pt">{esc(rest)}</span></p>')


def sheetbar(n, name, skill):
    return (f'<table class="bk"><tr>'
            f'<td style="background:{TEAL};width:120px;vertical-align:middle;'
            f'border:0"><p style="text-align:center;margin:0"><span '
            f'style="font-weight:700;color:#fff;font-size:12pt">SHEET {n}</span>'
            f'</p></td><td style="vertical-align:middle;border:0;'
            f'border-bottom:1px solid {TEAL}"><p style="margin:0">'
            f'<span style="font-weight:700;color:{DEEP};font-size:12pt">'
            f'{esc(name)}</span> <span style="color:{GREY};font-size:10pt">'
            f'&nbsp;·&nbsp; {esc(skill)}</span></p></td></tr></table>')


def part(letter, instruction):
    return (f'<p style="margin-top:14px;margin-bottom:4px">'
            f'<span style="font-weight:700;color:{TEAL};font-size:11pt">'
            f'{letter}</span> <span style="font-weight:700;font-size:11pt">'
            f'{esc(instruction)}</span></p>')


def p(text, style=""):
    return f'<p style="{style}">{text}</p>'


def plain(text):
    return p(f'<span style="font-size:10.5pt">{esc(text)}</span>')


def note(head, lines, colour=TEAL, fill=SOFT):
    inner = "".join(
        f'<p style="margin-bottom:3px"><span style="font-size:10pt">{l}</span></p>'
        for l in lines)
    return (f'<table class="bk"><tr><td style="background:{fill};'
            f'border:1px solid {colour};padding:10px 12px">'
            f'<table class="bk"><tr><td style="background:{colour};border:0;'
            f'width:130px"><p style="margin:0"><span style="font-weight:700;'
            f'color:#fff;font-size:8pt;letter-spacing:1.2px">{esc(head)}</span>'
            f'</p></td></tr></table>{inner}</td></tr></table>')


def numbered(label, items):
    """items: list of (sentence with {}, [answers])"""
    rows = ""
    for i, (text, answers) in enumerate(items, 1):
        rows += (f'<p style="margin-bottom:5px;padding-left:18px">'
                 f'<span style="color:{GREY};font-size:10pt">{i}</span> '
                 f'<span style="font-size:10.5pt">'
                 f'{gaps(text, answers, label, i)}</span></p>')
    return rows


# ----------------------------------------------------------------- the paper

def build():
    h = []
    h.append(eyebrow("UNIT 2 · TRAVEL AND TOURISM        B1 PRE-INTERMEDIATE"))
    h.append(title("Academic Skills Plus & Reading Plus"))
    h.append(strap("Homework, Unit 2",
                   "chunks · grammar in context · the strategy · a new text · "
                   "a short piece of writing"))
    h.append(note("IN THIS HOMEWORK", [
        "<b>Sheet 1</b> &mdash; telling what happened &middot; putting events in order",
        "<b>Sheet 2</b> &mdash; reading a travel review &middot; fact and opinion",
        "Neither sheet needs the recording. Both are built on the language of "
        "Unit 2: the past simple, the past continuous, and the words we use "
        "about travel and tourism.",
    ]))
    h.append(p(f'<span style="font-weight:700;color:{GREY};font-size:9pt;'
               f'letter-spacing:1.4px">NAME</span> '
               f'<span style="color:{RULE}">………………………………</span> '
               f'<span style="font-weight:700;color:{GREY};font-size:9pt;'
               f'letter-spacing:1.4px">CLASS</span> '
               f'<span style="color:{RULE}">…………………</span> '
               f'<span style="font-weight:700;color:{GREY};font-size:9pt;'
               f'letter-spacing:1.4px">DATE</span> '
               f'<span style="color:{RULE}">…………………</span>'
               f'&nbsp;&nbsp;&nbsp;<span style="font-size:9pt;color:{GREY}">'
               f'Prepared by </span><span style="font-weight:700;color:{DEEP};'
               f'font-size:9pt">Olimov Azamat</span>',
               f"border-top:1px solid {RULE};padding-top:6px;margin-bottom:10px"))

    # ------------------------------------------------------------- sheet one
    h.append(sheetbar(1, "TELLING WHAT HAPPENED", "putting events in order"))
    h.append(part("A", "Chunks from travel stories. Complete each phrase with ONE word."))
    h.append(numbered("A1", [
        ("We {} an adventure on the second day.", ["had"]),
        ("We were nearly {} when the bus stopped.", ["there"]),
        ("I was standing {} the queue when they called my name.", ["in"]),
        ("It {} out to be the best day of the trip.", ["turned"]),
        ("We {} the last bus by two minutes.", ["missed"]),
        ("At {} we thought it was a joke.", ["first"]),
        ("In the {}, we walked.", ["end"]),
        ("Looking {}, it was the right decision.", ["back"]),
    ]))
    h.append(plain("Now use three of these chunks to tell the story of a "
                   "journey of your own."))
    h.append(numbered("A2", [("{}", [None]), ("{}", [None]), ("{}", [None])]))

    h.append(part("B", "Grammar in context: the long action and the short one"))
    h.append(plain("A travel story almost always needs both past tenses, and "
                   "they do two different jobs."))
    h.append(note("THE TWO JOBS", [
        "<b>Past continuous</b> &mdash; the longer action, already going on. "
        "<i>We <b>were waiting</b> at the gate.</i>",
        "<b>Past simple</b> &mdash; the shorter action that interrupts it. "
        "<i>They <b>announced</b> the delay.</i>",
        "Put together: <i>We <b>were waiting</b> at the gate when they "
        "<b>announced</b> the delay.</i>",
        "<b>when</b> is followed by the short action; <b>while</b> is followed "
        "by the long one.",
    ]))
    h.append(plain("Complete with the past simple or the past continuous."))
    h.append(numbered("B1", [
        ("While we {} (drive) through the mountains, the engine {} (stop).",
         ["were driving", "stopped"]),
        ("I {} (lose) my passport while I {} (look) for my ticket.",
         ["lost", "was looking"]),
        ("They {} (swim) when the storm {} (begin).",
         ["were swimming", "began"]),
        ("She {} (take) a photograph when the bird {} (fly) away.",
         ["was taking", "flew"]),
        ("We {} (not expect) rain, so nobody {} (bring) a coat.",
         ["did not expect", "brought"]),
        ("While I {} (wait) for the guide, I {} (meet) an old friend.",
         ["was waiting", "met"]),
    ]))
    h.append(plain("Now find and correct the mistake in each sentence."))
    h.append(numbered("B2", [
        ("While I was walking, I was seeing the castle. &rarr; {}",
         ["While I was walking, I saw the castle"]),
        ("When we were leaving the hotel, it started to rain heavily and we "
         "were running. &rarr; {}",
         ["we ran"]),
        ("I was losing my bag while I was getting off the train. &rarr; {}",
         ["I lost my bag"]),
        ("They were arriving at six o'clock yesterday. &rarr; {}",
         ["They arrived at six o'clock yesterday"]),
    ]))

    h.append(part("C", "The strategy: putting events in order"))
    h.append(plain("A reader can follow a story with no dates in it, as long "
                   "as the order words are doing their work. Three families, "
                   "and they are not interchangeable."))
    h.append(note("ORDER WORDS", [
        "<b>Starting</b> &mdash; at first &middot; to begin with &middot; "
        "on the first day",
        "<b>Going on</b> &mdash; then &middot; after that &middot; later "
        "&middot; the next morning",
        "<b>Finishing</b> &mdash; in the end &middot; finally &middot; "
        "eventually",
        "<b>Careful:</b> <i>at last</i> is not <i>at the end</i>. "
        "<i>At last</i> means the wait was long and you are relieved.",
    ]))
    h.append(plain("Complete the story. Use each phrase once: at first · "
                   "then · the next morning · in the end."))
    h.append(numbered("C1", [
        ("{} we could not find the station at all.", ["At first"]),
        ("{} a woman drew us a map on the back of a receipt.", ["Then"]),
        ("We slept in a room above a bakery. {} the whole town smelled of "
         "bread.", ["The next morning"]),
        ("{} we stayed three days longer than we had planned.", ["In the end"]),
    ]))
    h.append(plain("Pronunciation. In each pair the two words join. What "
                   "happens to the sound?"))
    h.append(numbered("C2", [
        ("was I &rarr; {}", ["wazai"]),
        ("did you &rarr; {}", ["didjou"]),
        ("went to &rarr; {}", ["wenta"]),
        ("last year &rarr; {}", ["lascheer"]),
    ]))

    h.append(part("D", "A new text. Read it and complete the notes."))
    h.append(note("THE LAST BUS FROM SAMARKAND", [
        "We had four hours before the night train and somebody said the "
        "observatory was worth seeing, so we went. It was further out of "
        "town than the map suggested.",
        "While we were walking back down the hill, the last bus passed us. "
        "It did not stop. At first we laughed about it. Then it got dark, "
        "and we stopped laughing.",
        "A man with a van full of melons was going our way and took us as far "
        "as the market. We ran the rest. We reached the platform four minutes "
        "before the train left, and the guard was already closing the doors.",
        "In the end the observatory was not the thing I remember. I remember "
        "the melons, and running, and the exact face of the guard when he "
        "decided to let us on.",
    ], colour="#C0745F", fill="#FBF0EE"))
    h.append(numbered("D1", [
        ("What were they doing when the last bus passed? {}",
         ["They were walking back down the hill"]),
        ("Who helped them, and how far? {}",
         ["A man with a van full of melons, as far as the market"]),
        ("How long before the train left did they reach the platform? {}",
         ["Four minutes"]),
        ("Find one past continuous verb in the last paragraph. {}",
         ["was closing"]),
        ("The writer says the observatory is not what they remember. Why not? {}",
         [None]),
    ]))

    h.append(part("E", "Write a short travel story (70–90 words)."))
    h.append(plain("Something that went wrong on a journey. Use the past "
                   "continuous at least twice, and two order words from part C."))
    h.append(numbered("E1", [("{}", [None])]))

    h.append(note("SELF-CHECK — PARTS A, B AND C ONLY", [
        "<b>A</b> 1 had · 2 there · 3 in · 4 turned · 5 missed · 6 first · "
        "7 end · 8 back",
        "<b>B1</b> 1 were driving / stopped · 2 lost / was looking · "
        "3 were swimming / began · 4 was taking / flew · "
        "5 did not expect / brought · 6 was waiting / met",
        "<b>B2</b> 1 I saw the castle · 2 we ran · 3 I lost my bag · "
        "4 They arrived at six o'clock yesterday",
        "<b>C1</b> 1 At first · 2 Then · 3 The next morning · 4 In the end",
    ]))
    return h


def sheet_two(h):
    h.append(sheetbar(2, "READING A TRAVEL REVIEW", "fact and opinion"))
    h.append(part("A", "Chunks from online reviews. Complete each phrase with ONE word."))
    h.append(numbered("F1", [
        ("The room was smaller than it {} in the photographs.", ["looked"]),
        ("It is within walking {} of the old town.", ["distance"]),
        ("The staff could not have been more {}.", ["helpful"]),
        ("Breakfast is {} in the price.", ["included"]),
        ("We were {} for a room with a view and did not get one.", ["charged"]),
        ("It is worth {} out of season.", ["going"]),
        ("I would not stay there {}.", ["again"]),
        ("Do not let the reviews {} you off &mdash; it was fine.", ["put"]),
    ]))
    h.append(plain("Now use three of these chunks to review a place you have "
                   "stayed in or visited."))
    h.append(numbered("F2", [("{}", [None]), ("{}", [None]), ("{}", [None])]))

    h.append(part("B", "Grammar in context: comparing what you expected"))
    h.append(note("TWO PATTERNS", [
        "<b>than</b> compares two different things. "
        "<i>The room was <b>smaller than</b> the photographs.</i>",
        "<b>as ... as</b> says they are the same, and with <b>not</b> it says "
        "one is less. <i>It was <b>not as clean as</b> we hoped.</i>",
        "A review very often compares the place with the <b>expectation</b>, "
        "not with another place: <i>quieter than we expected</i>, "
        "<i>not as far as it looks</i>.",
        "<b>Careful:</b> never <i>more cheaper</i>, and never "
        "<i>as cheaper as</i>.",
    ]))
    h.append(plain("Complete with the right form of the word in brackets."))
    h.append(numbered("G1", [
        ("The beach was {} (crowded) than we expected.", ["more crowded"]),
        ("The second hotel was not as {} (expensive) as the first.",
         ["expensive"]),
        ("The journey was {} (short) than the website said.", ["shorter"]),
        ("The food was {} (good) than anything we ate in the capital.",
         ["better"]),
        ("The old town is not as {} (far) from the airport as it looks.",
         ["far"]),
        ("It was the {} (bad) night's sleep of the whole holiday.", ["worst"]),
    ]))

    h.append(part("C", "The strategy: telling fact from opinion"))
    h.append(plain("A review mixes the two in the same sentence, and a reader "
                   "who cannot separate them books the wrong hotel. Two tests:"))
    h.append(note("HOW TO TELL", [
        "<b>1 Could somebody check it?</b> <i>It is 300 metres from the "
        "station</i> can be checked. <i>It is close to everything</i> cannot.",
        "<b>2 Does the word carry a feeling?</b> <i>small</i> is closer to a "
        "fact than <i>cramped</i>. <i>Cheap</i> and <i>good value</i> are the "
        "same price and a different opinion.",
        "Useful move: a review you can trust gives the fact <b>and</b> the "
        "opinion &mdash; <i>a ten-minute walk uphill, which was harder than "
        "it sounds</i>.",
    ]))
    h.append(plain("Write F (fact) or O (opinion)."))
    h.append(numbered("H1", [
        ("The hotel has forty rooms. {}", ["F"]),
        ("The breakfast was disappointing. {}", ["O"]),
        ("It is a fifteen-minute walk from the museum. {}", ["F"]),
        ("The area feels unsafe after dark. {}", ["O"]),
        ("There is no lift. {}", ["F"]),
        ("The rooms are excellent value. {}", ["O"]),
    ]))

    h.append(part("D", "A new text. Read the review and complete the notes."))
    h.append(note("HOTEL ARAL — TWO NIGHTS IN MARCH", [
        "The building is on the main road, ten minutes from the bus station "
        "on foot. Our room was on the third floor and there is no lift, which "
        "the website does not mention.",
        "The room was clean and much quieter than I expected for a main road; "
        "the windows are new. It was also colder than we would have liked, "
        "and the heating goes off at eleven.",
        "Breakfast is included and is served until nine. It is bread, eggs "
        "and tea &mdash; nothing more, but nobody hurried us.",
        "For 200,000 som a night I think it is good value, as long as you can "
        "carry your own bag up three flights. I would stay again in summer.",
    ]))
    h.append(numbered("I1", [
        ("How far is the hotel from the bus station? {}", ["Ten minutes on foot"]),
        ("Write one fact the website leaves out. {}", ["There is no lift"]),
        ("Find a comparison with an expectation. {}",
         ["quieter than I expected"]),
        ("Until what time is breakfast served? {}", ["Nine"]),
        ("Why would the writer not stay again in winter? {}", [None]),
    ]))

    h.append(part("E", "Write a review of a place you know (70–90 words)."))
    h.append(plain("Give at least two facts somebody could check and two "
                   "opinions. Use one comparison with an expectation."))
    h.append(numbered("J1", [("{}", [None])]))

    h.append(note("SELF-CHECK — PARTS A, B AND C ONLY", [
        "<b>A</b> 1 looked · 2 distance · 3 helpful · 4 included · 5 charged · "
        "6 going · 7 again · 8 put",
        "<b>B</b> 1 more crowded · 2 expensive · 3 shorter · 4 better · "
        "5 far · 6 worst",
        "<b>C</b> 1 F · 2 O · 3 F · 4 O · 5 F · 6 O",
    ]))
    return h


if __name__ == "__main__":
    blocks = sheet_two(build())
    layout = '<div class="booklet">%s</div>' % "".join(blocks)
    data = {"level": "Pre-Intermediate", "number": 2,
            "title": "P02 ASRP Travel and tourism (booklet)",
            "passages": {}, "layout": layout, "questions": Q}
    json.dump(data, open("p02asrp.json", "w"))
    marked = sum(1 for q in Q if q["kind"] == "typed")
    print("blanks: %d  (%d marked, %d their own words)"
          % (len(Q), marked, len(Q) - marked))
    print("layout bytes:", len(layout))
