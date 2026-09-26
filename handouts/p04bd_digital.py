"""P04BD Celebrations - Azamat's own booklet, as a page that marks itself.

The booklet exists in Word, so its design is rendered as it is by
booklet_html rather than rebuilt. What this adds is the answer key by hand:
the key document is written for a teacher - "1.2 8 am c · midday d", a note
on item 4, suggested answers, a read-aloud script - and the automatic reader
mis-joined it in places. Every box below is named by exercise, item and
position, and given the answer the key gives it, or None where the answer
is the student's own words.

Four exercises have their answer lines drawn as Word tab leaders rather than
dots, so the renderer saw no blank there at all; they get a box here. 2.5
prints nothing to write on - on paper you correct the sentence beside it -
so it gets one too.

    python3 handouts/p04bd_digital.py            # writes p04bd.json, lists every box
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import booklet_html as bh

BANK = os.path.expanduser("~/Documents/Claude/Material Bank/General English/"
                          "B1 Pre-intermediate/")
BOOKLET = BANK + "P04BD Celebrations — BOOKLET.docx"

TICK, CROSS = "✓/yes/tick", "✗/no/cross"
NOTE = None                                     # the student's own words

# (exercise, item, nth box in the item) -> what the key says
KEY = {
    # 1 Reading
    ("1.2", 1, 1): "c", ("1.2", 2, 1): "d", ("1.2", 3, 1): "a", ("1.2", 4, 1): "b",
    ("1.3", 1, 1): "F", ("1.3", 2, 1): "F", ("1.3", 3, 1): "T",
    ("1.3", 4, 1): "DS", ("1.3", 5, 1): "F", ("1.3", 6, 1): "T",
    ("1.4", 1, 1): "crowded", ("1.4", 2, 1): "ugly", ("1.4", 3, 1): "narrow",
    ("1.4", 4, 1): "ancient", ("1.4", 5, 1): "noisy", ("1.4", 6, 1): "huge",
    ("1.5", 1, 1): NOTE, ("1.5", 2, 1): NOTE, ("1.5", 3, 1): NOTE,
    # 2 Grammar
    ("2.1", 1, 1): "D/O", ("2.1", 2, 1): "S", ("2.1", 3, 1): "P",
    ("2.1", 4, 1): "O", ("2.1", 5, 1): "D", ("2.1", 6, 1): "P",
    ("2.2", 1, 1): "Shall", ("2.2", 2, 1): "'ll/will", ("2.2", 3, 1): "'ll/will",
    ("2.2", 4, 1): "Shall", ("2.2", 5, 1): "won't/will not", ("2.2", 6, 1): "shall",
    ("2.3", 1, 1): NOTE, ("2.3", 2, 1): NOTE, ("2.3", 3, 1): NOTE, ("2.3", 4, 1): NOTE,
    ("2.4", 1, 1): "'m meeting/am meeting",
    ("2.4", 2, 1): "'m going to visit/am going to visit",
    ("2.4", 3, 1): "'ll get/will get",
    ("2.4", 4, 1): "'re having/are having",
    ("2.4", 5, 1): "'ll drive/will drive",
    ("2.4", 6, 1): "'m not going to eat/am not going to eat",
    ("2.5", 2, 1): "✓/correct/tick",
    ("2.5", 3, 1): "I'm meeting Anna on Tuesday",
    ("2.5", 4, 1): "Yes, let's",
    ("2.5", 5, 1): "✓/correct/tick",
    ("2.5", 6, 1): "Let's visit the museum this afternoon/"
                   "Shall we visit the museum this afternoon",
    ("2.6", 1, 1): "shall", ("2.6", 2, 1): "Let's", ("2.6", 3, 1): "Shall",
    ("2.6", 4, 1): "won't/will not", ("2.6", 5, 1): "'ll/will",
    ("2.6", 6, 1): "won't/will not", ("2.6", 7, 1): "shall", ("2.6", 8, 1): "let's",
    ("2.7", 1, 1): NOTE, ("2.7", 2, 1): NOTE, ("2.7", 3, 1): NOTE, ("2.7", 4, 1): NOTE,
    # 3 Vocabulary
    ("3.1", 1, 1): "ancient", ("3.1", 2, 1): "empty", ("3.1", 3, 1): "wide",
    ("3.1", 4, 1): "noisy", ("3.1", 5, 1): "outdoor", ("3.1", 6, 1): "ordinary",
    ("3.1", 7, 1): "tiny", ("3.1", 8, 1): "ugly",
    ("3.2", 1, 1): "crowded", ("3.2", 2, 1): "huge", ("3.2", 3, 1): "ancient",
    ("3.2", 4, 1): "narrow", ("3.2", 5, 1): "outdoor", ("3.2", 6, 1): "noisy",
    ("3.3", 1, 1): "absolutely", ("3.3", 2, 1): "very", ("3.3", 3, 1): "absolutely",
    ("3.3", 4, 1): "very/absolutely", ("3.3", 5, 1): "absolutely", ("3.3", 6, 1): "very",
    # 4 Listening
    ("4.1", 1, 1): CROSS, ("4.1", 2, 1): TICK, ("4.1", 3, 1): TICK,
    ("4.1", 4, 1): CROSS, ("4.1", 5, 1): TICK, ("4.1", 6, 1): NOTE,
    ("4.2", 1, 1): NOTE, ("4.2", 2, 1): NOTE, ("4.2", 3, 1): NOTE,
    ("4.2", 4, 1): NOTE, ("4.2", 5, 1): NOTE, ("4.2", 6, 1): NOTE,
    ("4.3", 1, 1): "won't/will not", ("4.3", 2, 1): "Shall", ("4.3", 3, 1): "'ll/will",
    ("4.3", 4, 1): "won't/will not", ("4.3", 5, 1): "Shall",
    ("4.4", 1, 1): NOTE, ("4.4", 1, 2): NOTE, ("4.4", 2, 1): NOTE, ("4.4", 2, 2): NOTE,
    ("4.5", 1, 1): NOTE, ("4.5", 2, 1): NOTE, ("4.5", 3, 1): NOTE, ("4.5", 4, 1): NOTE,
    ("4.6", 1, 1): TICK, ("4.6", 2, 1): TICK, ("4.6", 3, 1): TICK,
    ("4.6", 4, 1): TICK, ("4.6", 5, 1): TICK, ("4.6", 6, 1): TICK, ("4.6", 6, 2): NOTE,
    # 5 Writing
    ("5.1", 1, 1): NOTE, ("5.1", 2, 1): "fruit", ("5.1", 2, 2): "bread",
    ("5.1", 3, 1): NOTE, ("5.1", 3, 2): NOTE, ("5.1", 3, 3): NOTE, ("5.1", 3, 4): NOTE,
    ("5.2", 1, 1): "Kamola", ("5.2", 1, 2): "Bek", ("5.2", 1, 3): "Kamola",
    ("5.3", 1, 1): "Would you like to come to my birthday party",
    ("5.3", 2, 1): "Thanks for inviting me to your wedding",
    ("5.3", 3, 1): "I'm afraid I can't go to the cinema with you",
    ("5.3", 4, 1): "I'd love to come, but I'm busy that weekend",
}
# the rest of the writing section is the student's own: 5.4 (six lines),
# 5.5 (eight) and the 5.6 self-check (fifteen ticks)
for n in range(1, 7):
    KEY[("5.4", n, 1)] = NOTE
for n in range(1, 15):          # 1-8 are the CHECK BEFORE YOU HAND IT IN ticks, 9-14 the reply
    KEY[("5.5", n, 1)] = NOTE
for n in range(1, 16):
    KEY[("5.6", n, 1)] = NOTE

# items whose answer line is a tab leader, so the renderer gave them no box
LEADER_ITEMS = [("1.5", n) for n in (1, 2, 3)] + [("4.2", n) for n in range(1, 7)] \
    + [("5.3", n) for n in (1, 2, 3, 4)]
# items with nowhere at all to write
BESIDE_ITEMS = [("2.5", n) for n in (2, 3, 4, 5, 6)]

ITEM_P = re.compile(r'(<p data-item="([0-9.]+):(\d+)"[^>]*>)(.*?)</p>', re.S)
LEADER_P = re.compile(r"<p style=\"[^\"]*\"><span class='tab'></span></p>")


def place_boxes(inner):
    """Give the leader-line items and 2.5 somewhere to type.

    The renderer tags every paragraph with the item last seen, so the note
    box after 5.3 is still "5.3 item 4" and its own numbered lines read as
    items 1 to 4 again. Only the item's first paragraph gets a box, and a
    leader item only where the leader actually is.
    """
    done = set()

    def item(m):
        label, num, guts = m.group(2), int(m.group(3)), m.group(4)
        if (label, num) in done:
            return m.group(0)
        if (label, num) in LEADER_ITEMS and guts.endswith("<span class='tab'></span>"):
            done.add((label, num))
            guts = guts[:-len("<span class='tab'></span>")]
            return "%s%s {{box:%s:%d:wide}}</p>" % (m.group(1), guts, label, num)
        if (label, num) in BESIDE_ITEMS:
            done.add((label, num))
            return "%s%s {{box:%s:%d:wide}}</p>" % (m.group(1), guts, label, num)
        return m.group(0)
    inner = ITEM_P.sub(item, inner)
    missing = set(LEADER_ITEMS + BESIDE_ITEMS) - done
    if missing:
        raise SystemExit("no place found for %s" % sorted(missing))
    # 5.4 and 5.5: the empty ruled lines under each writing task. Six boxes
    # each; the rest of the ruled page is dropped, since a box grows with
    # what is typed and a screen does not need the paper's blank lines.
    for label, start, stop, first in (("5.4", "5.4  </span>", "5.5  </span>", 1),
                                      ("5.5", "5.5  </span>", "CHECK BEFORE", 9)):
        head = inner.index(start)
        tail = inner.index(stop, head)
        part = inner[head:tail]
        count = [0]

        def line(m, label=label, first=first):
            count[0] += 1
            if count[0] <= 6:
                return ('<p style="margin-bottom:8px">{{box:%s:%d:wide}}</p>'
                        % (label, first + count[0] - 1))
            return ""
        part = LEADER_P.sub(line, part)
        if not count[0]:
            raise SystemExit("no ruled lines found under " + label)
        inner = inner[:head] + part + inner[tail:]
    return inner


def build():
    inner, blanks = bh.render(BOOKLET, fillable=True)
    inner = place_boxes(inner)
    by_blank = {i: b for i, b in enumerate(blanks)}
    questions = []

    def question(label, num, nth, text):
        want = KEY.get((label, num, nth), "MISSING")
        if want == "MISSING":
            raise SystemExit("no answer decided for %s item %s box %d" % (label, num, nth))
        questions.append({"num": len(questions) + 1,
                          "kind": "typed" if want else "open",
                          "prompt": "%s  %s" % (label, re.sub(r"\s+", " ", text)[:160]),
                          "answer": want, "options": []})
        return len(questions)

    TOKEN = re.compile(r'data-blank="(\d+)"|\{\{box:([0-9.]+):(\d+):wide\}\}')

    def number(m):
        if m.group(1) is not None:
            b = by_blank[int(m.group(1))]
            n = question(b["label"], b["num"], b["nth"], b["text"])
            return 'data-q="%d"' % n
        label, num = m.group(2), int(m.group(3))
        n = question(label, num, 1, "%s item %d" % (label, num))
        return ('<input class="bk-blank" data-q="%d" style="width:95%%" '
                'autocomplete="off" autocapitalize="off" spellcheck="false">' % n)
    layout = TOKEN.sub(number, inner)
    return {"level": "Pre-Intermediate", "number": 4, "kind": "handout",
            "title": "P04BD Celebrations (booklet)",
            "passages": {}, "layout": layout, "questions": questions}


if __name__ == "__main__":
    data = build()
    qs = data["questions"]
    out = os.path.join(ROOT, "p04bd.json")
    json.dump(data, open(out, "w"))
    marked = sum(1 for q in qs if q["kind"] == "typed")
    for q in qs:
        print("%-5s %3d  %-64s => %s" % ("MARK" if q["kind"] == "typed" else "",
                                         q["num"], q["prompt"][:64], q["answer"]))
    print("\nboxes: %d  (%d marked, %d their own words)" % (len(qs), marked, len(qs) - marked))
    print("layout bytes:", len(data["layout"]), "->", out)
