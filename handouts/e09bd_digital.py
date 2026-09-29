"""E09BD Clothes and shopping - Azamat's Elementary booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(E09BD Clothes and shopping - answer key), joined box by box by hand. The
Desktop "new design" copy is used; it splits into its five parts as it
should. E09AB covers 9B too; the one he sets is the one that counts.

As with the other Elementary booklets, it speaks Uzbek wherever it
explains: every explanation box, the goals, the headings of the grammar
table, the "Why" column of the listening table, and a line under every
instruction. The English examples stay English, as do the reading text,
the emails and the exercises.

Put right here: 2.4 says TWO sentences are correct, but three are (3, 5 and
8, as the key has it): it says THREE. In 1.2 the key has "studying" as Maria
only, but Arman studies Korean in his free time: B (both) is right too.
3.3 and 4.3 are tables of words with a box after each; a phone gets one word
a line, with the four sounds (3.3) as a key above them.

    python3 handouts/e09bd_digital.py            # writes handouts/e09bd.json, lists every box
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import (Handout, Q, choose, tick, own, write, fix, note, pair, report,   # noqa: E402
                     BLANK_TAG, LEADER_P, plain, ITEM_STYLE, NUM_SPAN, TEXT_SPAN)

DOCX = ("~/Desktop/Handouts/A2 Elementary/E09BD Clothes and shopping/"
        "E09BD Clothes and shopping — handout (new design).docx")
W = "95%"

h = Handout(DOCX)
TAGS = {int(m.group(1)): m.group(0) for m in BLANK_TAG.finditer(h.html)}


def section(label):
    return h.html.index("%s  </span>" % label)


def either(*forms):
    return "/".join(forms)


def item_p(label, n, text_html, token, number=True):
    h.texts[(label, n)] = plain(text_html)
    return ('<p data-item="%s:%d" %s>%s%s</p>'
            % (label, n, ITEM_STYLE, NUM_SPAN % n if number else "",
               TEXT_SPAN % ("%s  %s" % (text_html, token))))


def key_list(pairs):
    return ('<table class="bk"><tr><td style="vertical-align:top;background:#F2F8F8;'
            'border-left:3px solid #127D80">'
            + "".join('<p style="margin:0"><span style="font-weight:700;color:#127D80">%s</span>  %s</p>'
                      % (l, html.escape(t, quote=False)) for l, t in pairs)
            + "</td></tr></table>")


def table_after(label):
    a = h.html.index('<table class="bk">', section(label))
    return a, h.html.index("</table>", a) + len("</table>")


def halves(label, letters, token="{{box:%s:%s:60px:}}"):
    a, b = table_after(label)
    cells = [plain(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", h.html[a:b], re.S)]
    begins = [re.match(r"(\d+)\s+(.*)", c).groups() for c in cells if re.match(r"\d+\s", c)]
    ends = sorted(re.match(r"([%s])\s+(.*)" % letters, c).groups() for c in cells
                  if re.match(r"[%s]\s" % letters, c))
    h.html = h.html[:a] + key_list(ends) + "".join(
        item_p(label, int(n), html.escape(t, quote=False), token % (label, n)) for n, t in begins) + h.html[b:]
    return [l for l, _t in ends]


def in_order(label, lines):
    """"Number them 1-5": the paper's own numbers go, so the only numbers
    are the ones tapped."""
    a, b = table_after(label)
    h.html = h.html[:a] + "".join(
        item_p(label, n, "·  " + html.escape(t, quote=False), "{{box:%s:%d:60px:}}" % (label, n), number=False)
        for n, t in sorted(lines.items())) + h.html[b:]


def reword(label, old, new):
    at = section(label) + len("%s  </span>" % label)
    end = h.html.index("</p>", at)
    if plain(h.html[at:end]) != old:
        raise SystemExit("%s says %r" % (label, plain(h.html[at:end])))
    style = re.match(r'<span( style="[^"]*")?>', h.html[at:end])
    h.html = h.html[:at] + "<span%s>%s</span>" % (style.group(1) or "", html.escape(new)) + h.html[end:]


def words_between(label, n):
    """An item's choices, from "(a / b)" or "a / b" in its text."""
    m = next(m for m in h._items(label) if int(m.group(3)) == n)
    return plain(m.group(4))


def boxes_for(label, groups, where="first"):
    for n in groups:
        h.item_box(label, n, where=where)


def lines_for_table(label, lines, width=W):
    a, b = table_after(label)
    h.html = h.html[:a] + "".join(item_p(label, n, html.escape(t), "{{box:%s:%d:%s:}}" % (label, n, width))
                                  for n, t in enumerate(lines, 1)) + h.html[b:]


def lines_instead_of_table(label, lines, nth=0, before=""):
    """The table after an exercise becomes one line per box: lines are
    [(n, text)], and `before` is anything to show above them."""
    a, b = table_after(label)
    for _ in range(nth):
        a = h.html.index('<table class="bk">', b)
        b = h.html.index("</table>", a) + len("</table>")
    h.html = h.html[:a] + before + "".join(item_p(label, n, html.escape(t), "{{box:%s:%d:60px:}}" % (label, n),
                                                  number=False)
                                           for n, t in lines) + h.html[b:]


def wearing(*things):
    """Every way of starting "is wearing" for a person the picture does not name."""
    out = []
    for text in things:
        for s in ("He's", "She's", "He is", "She is"):
            out.append("%s wearing %s" % (s, text))
    return "/".join(out)


# ------------------------------------------------------------ 1 Reading
for n in range(1, 7):
    h.item_box("1.3", n, placeholder="If it is false, correct it")
a, b = section("1.3"), section("1.4")             # the ruled lines the boxes replace
h.html = h.html[:a] + LEADER_P.sub("", h.html[a:b]) + h.html[b:]
boxes_for("1.4", range(1, 5), where="leader")

# ------------------------------------------------------------ 2 Grammar
reword("2.4", "Find and correct the mistake. TWO sentences are correct — tick them.",
       "Find and correct the mistake. THREE sentences are correct — tick them.")
boxes_for("2.4", range(2, 9))                     # item 1 is the worked example
FORMS27 = {1: ["wear", "'m wearing"], 2: ["works", "is working"], 3: ["rains", "is raining"],
           4: ["never eat", "are never eating"], 5: ["do you do", "are you doing"], 6: ["studies", "is studying"]}
boxes_for("2.7", FORMS27)
h.options_on_lines("2.8")
h.leaders("2.9", "3.1  </span>", [(1, W, "Two sentences with usually, two with right now")])

# ------------------------------------------------------------ 3 Vocabulary
WORDS31 = h.sort_words("3.1", ["boots", "a dress", "gloves", "earrings", "a belt", "socks", "a skirt", "a ring",
                               "trainers", "a scarf", "jeans", "a necklace"], "On your body")
WORDS33 = ["shoe", "come", "know", "box", "two", "mother", "phone", "coffee", "group", "gloves", "clothes", "shop"]
lines_instead_of_table("3.3", list(enumerate(WORDS33, 1)),
                       before=key_list([("1", "/ɒ/ sock"), ("2", "/uː/ boot"), ("3", "/ʌ/ glove"),
                                        ("4", "/əʊ/ coat")]))
PUT = ["put on", "take off", "try on"]
boxes_for("3.5", range(1, 5), where="leader")

# ------------------------------------------------------------ 4 Listening
h.leaders("4.1", "4.2  </span>", [(1, W, "What is each person wearing?")])
boxes_for("4.2", (1, 2))
HEARD43 = [("Conversation 1", ["socks", "scarf", "shoes", "boots", "belt", "hat"]),
           ("Conversation 2", ["gloves", "dress", "earrings", "jeans", "jumper", "ring"])]
a, b = table_after("4.3")
rows, n = "", 0
for heading, words in HEARD43:
    rows += '<p style="margin:10px 0 4px"><span style="font-weight:700">%s</span></p>' % heading
    for w in words:
        n += 1
        rows += item_p("4.3", n, "%s — %s" % (heading[-1], w), "{{box:4.3:%d:60px:}}" % n, number=False)
h.html = h.html[:a] + rows + h.html[b:]
h.html = re.sub(r"(<p data-item=\"4\.3:\d+\"[^>]*>.*?<span[^>]*>)[12] — ", r"\1", h.html)   # the word alone
a, b = section("4.4"), section("4.5")             # True or false only: no lines to write on
h.html = h.html[:a] + LEADER_P.sub("", h.html[a:b]) + h.html[b:]
boxes_for("4.8", (1, 2, 3))
h.options_on_lines("4.8")

# ------------------------------------------------------------ 5 Writing
PRESENTS51 = halves("5.1", "a-d")
boxes_for("5.4", range(1, 5), where="leader")
h.leaders("5.5", "CHECK BEFORE", [(20, W, "Email 1 — to a friend"), (21, W, "Email 2 — to somebody you don't know well")])
for i in (142, 143):                              # the word counts: the boxes count them themselves
    h.html = h.html.replace(TAGS[i], "", 1)

# ------------------------------- every instruction, once more, in Uzbek
for label, text in [
        ("1.1", "Muhokama qiling. Mamlakatingizda qanday bayramlar bor? Odamlar nima kiyishadi?"),
        ("1.2", "Kim bu haqda yozadi? *A* (Arman), *M* (Maria) yoki *B* (ikkalasi) ni tanlang."),
        ("1.3", "Toʻgʻri (*T*) mi yoki notoʻgʻri (*F*) mi? Notoʻgʻrilarini toʻgʻrilab yozing."),
        ("1.4", "Matndan shu maʼnodagi soʻzni toping."),
        ("1.5", "Odatda (*U*) mi yoki hozir (*N*) mi? Tanlang."),
        ("1.6", "Matndagi har bir gapni BITTA soʻz bilan toʻldiring."),
        ("2.1", "*-ing* shaklini yozing."),
        ("2.2", "*Simple* (*S*) mi yoki *continuous* (*C*) mi? Vaqt soʻziga qarang."),
        ("2.3", "Qavs ichidagi feʼlning toʻgʻri shakli bilan toʻldiring."),
        ("2.4", "Xatoni topib, toʻgʻrilang. UCHTA gap toʻgʻri — ular uchun *✓ It is correct* tugmasini bosing."),
        ("2.5", "Xabarni toʻgʻri shakl bilan toʻldiring."),
        ("2.6", "Gapni boshqa zamonda qayta yozing."),
        ("2.7", "Toʻgʻri variantni tanlang."),
        ("2.8", "Toʻgʻri javobni tanlang: *A*, *B* yoki *C*."),
        ("2.9", "Oʻzingiz haqingizda toʻrtta gap yozing — ikkitasi *usually* bilan, ikkitasi *right now* bilan."),
        ("3.1", "Har bir soʻzning guruhini tanlang: tanada, oyoqda, mayda narsalar yoki taqinchoqlar."),
        ("3.2", "*a*, *a pair of* yoki hech narsa (*–*)? Tanlang."),
        ("3.3", "Talaffuz. Qaysi tovush? *1*, *2*, *3* yoki *4* ni tanlang."),
        ("3.4", "*put on*, *take off* mi yoki *try on*? Tanlang."),
        ("3.5", "Har bir gapdagi xatoni topib, toʻgʻri gapni yozing."),
        ("3.6", "Kiyim doʻkonidagi suhbatni toʻldiring."),
        ("3.7", "Odam nima kiygan? Toʻliq gaplar yozing."),
        ("4.1", "Tinglashdan oldin taxmin qiling. Sizningcha, har bir kishi nima kiygan?"),
        ("4.2", "Bir marta tinglang. Toʻgʻri javobni tanlang."),
        ("4.3", "Yana tinglang. Har bir kiyim soʻzini eshitdingizmi? *✓* yoki *✗* ni tanlang."),
        ("4.4", "Yana bir marta tinglang. Toʻgʻri (*T*) mi yoki notoʻgʻri (*F*) mi?"),
        ("4.5", "Eshitgan qatorlaringizni toʻldiring."),
        ("4.6", "Tinglang va nima boʻlishiga eʼtibor bering."),
        ("4.7", "Har bir qatorni ikki marta ayting — avval sekin, keyin tez."),
        ("4.8", "Gapiruvchi nima demoqchi? *A* yoki *B* ni tanlang."),
        ("5.1", "Tinglang. Kim nima sovgʻa qiladi? Odamni sovgʻa bilan moslang: harfni tanlang."),
        ("5.2", "Norasmiy (*I*) mi yoki rasmiy (*F*) mi?"),
        ("5.3", "Ikkala emailni oʻqing. Keyin savollarga javob bering."),
        ("5.4", "Ikkala email haqidagi savollarga javob bering."),
        ("5.5", "IKKITA email yozing (har biri 50–60 soʻz). Sovgʻa bir xil, lekin biri doʻstingizga, biri yaxshi "
                "tanimaydigan odamingizga.")]:
    h.say_also(label, text)

# ------------------------------------------ the explanations, told in Uzbek
h.goals([
    "odamlar odatda nima qilishini va hozir nima qilayotganini aytishni",
    "odam nima kiyganini tasvirlashni",
    "mamlakatingizdagi bayramlar haqida gapirishni",
    "kiyim va sovgʻalar haqida gapirayotgan odamlarni tushunishni",
    "rasmiy va norasmiy minnatdorchilik emaili yozishni",
])
h.retell("KEY WORDS", "KALIT SOʻZLAR", [
    "**a festival**  bayram — musiqa va taomlar bilan oʻtadigan maxsus vaqt",
    "**a colleague**  hamkasb — birga ishlaydigan odam",
    "**a costume**  bayram uchun maxsus kiyim",
    "**a square**  maydon — shahardagi ochiq joy",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — PRESENT SIMPLE YOKI PRESENT CONTINUOUS", [
    "Ikki zamon, ikki vazifa. Shaklni tanlashdan oldin ish qachon boʻlayotganini hal qiling.",
    "[[A]] **Present simple** — odatda qiladigan ishlarimiz yoki doim toʻgʻri boʻlgan narsalar. *I study Korean. "
    "· My colleagues are kind. · She goes to the market on Sundays.*",
    "[[B]] **Present continuous** — hozir, shu daqiqada boʻlayotgan narsalar. *I'm sitting in the kitchen. · "
    "They're dancing in the square.*",
    "[[C]] *Present simple* bilan keladigan soʻzlar: *always · usually · often · sometimes · never · every day · "
    "at weekends*",
    "[[D]] *Present continuous* bilan keladigan soʻzlar: *now · right now · at the moment · today · this week*",
    "**Shakli:** *present continuous* = *am / is / are* + feʼl + *-ing*. Inkor: *I'm not wearing…* Soʻroq: *Are "
    "you wearing…?*",
])
h.retell("ERROR WARNING", "DIQQAT — ZAMONLARNI ARALASHTIRISH", [
    "Oʻquvchilar ikki shaklni ikkala tomonga ham adashtiradi. Darslik ogohlantiradigan ikkitasi:",
    "✗ *All the masks are being really beautiful.* → ✓ *All the masks are really beautiful.* Niqoblar faqat shu "
    "daqiqada emas, doim chiroyli. Bu — *present simple*.",
    "✗ *I stand in the middle of the square.* → ✓ *I'm standing in the middle of the square.* U yerda har kuni "
    "emas, faqat hozir turibdi. Bu — *present continuous*.",
    "Va *be* ni hech qachon unutmang: ✗ *I wearing a coat.* → ✓ *I'm wearing a coat.*",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — KIYIMLAR", [
    "Kiyimlarni guruh-guruh qilib oʻrganing va har bir guruhga mos feʼlni ham oʻrganing.",
    "[[A]] Tanada: *a dress · a skirt · a T-shirt · a jumper · a coat · a shirt · jeans · shorts · trousers*",
    "[[B]] Oyoqda: *shoes · boots · trainers · socks*",
    "[[C]] Mayda narsalar: *a belt · a scarf · gloves · a hat · a watch*. Taqinchoqlar: *a ring · a necklace · "
    "earrings*",
    "[[D]] Feʼllar: *I'm wearing a coat. · I put on my boots. · I take off my hat. · Can I try on this jumper?*",
    "**Ehtiyot boʻling — doim koʻplikda:** *jeans · shorts · trousers · gloves · trainers · earrings*. *a pair of "
    "jeans* deng, hech qachon *a jean* demang.",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [
    "Ikkita telefon suhbatini eshitasiz. Har birida bir doʻst boshqa mamlakatdagi bayramda boʻlgan odamga qoʻngʻiroq "
    "qiladi.",
    "Agar sinfingizda audio boʻlsa, bu 09.10-trek. Boʻlmasa, oʻqituvchingiz matnni oʻqib beradi — topshiriqlar "
    "bir xil.",
])
h.retell("WHY YOU DIDN'T HEAR IT", "NEGA ESHITMADINGIZ?", [
    "*Present continuous* da *am*, *is* va *are* juda qisqa. *You're wearing* /jɔː weərɪŋ/ — deyarli bitta soʻzdek, "
    "*I'm having* esa /aɪm hævɪŋ/ boʻlib eshitiladi.",
    "Baland qismi — *-ing* li feʼl. Avval oʻshanga quloq soling, uning oldidagi kichik soʻz ham oʻsha yerda "
    "boʻladi.",
])
h.retell("LISTENING INTO WRITING", "TINGLASHDAN YOZISHGA", [
    "Avval toʻrt kishining qanday sovgʻalar berishi haqidagi gapini tinglang. Agar sinfingizda audio boʻlsa, bu "
    "09.20-trek.",
])
h.retell("FORMAL OR INFORMAL?", "RASMIYMI YOKI NORASMIYMI?", [
    "Doʻstga va boshliqqa yoziladigan minnatdorchilik emaillari bir xil uchta joyda har xil soʻzlarni ishlatadi:",
    "**Boshlanishi:** norasmiy — *Hi there! · Hi Marie,* · rasmiy — *Dear Mr Parker, · Hello, Mrs Finch.*",
    "**Minnatdorchilik:** norasmiy — *Thanks so much for the… · Thank you for the…* · rasmiy — *I'd just like to "
    "say thank you very much for the…*",
    "**Tugashi:** norasmiy — *Love, · Thanks, · See you,* · rasmiy — *Best wishes, · Regards,*",
])
h.retell("ERROR WARNING", "DIQQAT — MINNATDORCHILIK EMAILIDAGI XATOLAR", [
    "Minnatdorchilik emailida uch narsa notoʻgʻri ketadi:",
    "1 **Rasmiy va norasmiyni aralashtirish.** ✗ *Dear Mr Parker, … Love, Sara* — bittasini tanlang va oxirigacha "
    "shunday davom eting.",
    "2 **Faqat rahmat deyish.** Bir qatorli email yetarli emas. Sovgʻa bilan nima qilishingizni ayting — *I'm going "
    "to wear them to the party* — shunda u haqiqiy xabarga aylanadi.",
    "3 **Hozirgi zamonlarni unutish.** *I'm wearing them right now* va *I wear it every day* har xil narsani "
    "aytadi. Ikkalasi ham shu yerda foydali.",
])
h.retell("PLAN", "REJA", [
    "1 Boshlang — *Hi …,* yoki *Dear Mr/Mrs …,*   2 Sovgʻa uchun rahmat ayting.   3 U haqida yoqimli gap ayting.",
    "4 Hozir u bilan nima qilayotganingizni yoki odatda nima qilishingizni ayting.   5 Bitta doʻstona oxirgi qator. "
    "  6 Tugating — *Love,* yoki *Best wishes,*",
])
h.retell("CHECK BEFORE YOU HAND IT IN", "TOPSHIRISHDAN OLDIN TEKSHIRING", [
    "{box}  1-email boshidan oxirigacha norasmiy.   {box}  2-email boshidan oxirigacha rasmiy.   {box}  Ularni "
    "aralashtirmadim.",
    "{box}  Rahmat aytdim va sovgʻa haqida yoqimli gap aytdim.   {box}  U bilan nima qilayotganimni yoki odatda "
    "nima qilishimni aytdim.",
    "{box}  Har bir emailda bitta *present simple* va bitta *present continuous* ishlatdim.   {box}  Soʻzlarimni "
    "sanadim.",
])
h.one_per_line("TOPSHIRISHDAN OLDIN TEKSHIRING", None, at="box")
h.retell_cells({"Present simple — usually": "Present simple — odatda",
                "Present continuous — now": "Present continuous — hozir"})
h.retell_cells({"What is written": "Yozilishi", "What you hear": "Eshitilishi", "Why": "Nega",
                "you are → /jɔː/, joined": "<i>you are</i> → /jɔː/, qoʻshilib ketadi",
                "I am → /aɪm/, joined to even": "<i>I am</i> → /aɪm/, <i>even</i> ga qoʻshiladi",
                "not takes the stress": "urgʻu <i>not</i> ga tushadi",
                "I am → /aɪm/": "<i>I am</i> → /aɪm/"},
               after="4.6  </span>")

# ------------------------------------------------------------------ the key
K = {}
AMB = {"A": "A · Arman", "M": "M · Maria", "B": "B · both"}
for n, a in enumerate(["A", "M/B", "M", "B", "A", "M"], 1):
    K[("1.2", n, 1)] = choose(["A", "M", "B"], a, labels=AMB)
TF = {"T": "T · true", "F": "F · false"}
for n, a in enumerate("FTFTFF", 1):
    K[("1.3", n, 1)] = choose(["T", "F"], a, labels=TF)
    K[("1.3", n, 2)] = note()
for n, a in enumerate(["a colleague/colleague/colleagues", "a costume/costume/hanbok", "a square/square",
                       "a flea market/flea market"], 1):
    K[("1.4", n, 1)] = Q(a)
UN = {"U": "U · usually", "N": "N · now"}
for n, a in enumerate("UNUNUN", 1):
    K[("1.5", n, 1)] = choose(["U", "N"], a, labels=UN)
for n, a in enumerate(["kind", "time", "laughing", "much", "smells", "carrying"], 1):
    K[("1.6", n, 1)] = Q(a)
for n, a in zip(range(2, 9), ["sitting", "dancing", "having", "shopping", "making", "studying", "getting"]):
    K[("2.1", n, 1)] = Q(a)
SC = {"S": "S · simple", "C": "C · continuous"}
for n, a in zip(range(2, 9), "CSCSCSC"):
    K[("2.2", n, 1)] = choose(["S", "C"], a, labels=SC)
for key, a in (((1, 1), "study"), ((2, 1), either("'m sitting", "am sitting")), ((3, 1), "walks"),
               ((4, 1), either("is wearing", "'s wearing")), ((5, 1), either("don't go", "do not go")),
               ((6, 1), either("is singing", "'s singing")), ((7, 1), "are"), ((8, 1), "Are"), ((8, 2), "enjoying")):
    K[("2.3",) + key] = Q(a)
TICKED = "✓/correct/tick"
for n, a in zip(range(2, 9), [
        either("I'm standing in the middle of the square right now", "I am standing in the middle of the square right now",
               "I'm standing"),
        TICKED,
        either("I'm wearing a red scarf today", "I am wearing a red scarf today", "I'm wearing"),
        TICKED,
        either("He works in a bank every day", "works"),
        either("What are you doing at the moment", "are you doing"),
        TICKED]):
    K[("2.4", n, 1)] = fix(a)
for n, a in enumerate([either("'m", "am"), "work", either("'m standing", "am standing"), "are dancing",
                       either("is buying", "'s buying"), "always buys",
                       either("don't usually like", "do not usually like"), either("'m enjoying", "am enjoying")], 1):
    K[("2.5", n, 1)] = Q(a)
for n, a in enumerate([either("I'm wearing jeans", "I am wearing jeans", "I'm not wearing jeans",
                              "I am not wearing jeans", "I'm wearing a dress", "I am wearing a dress"),
                       "cooks dinner", "watch a film",
                       either("'re going to the market", "are going to the market")], 1):
    K[("2.6", n, 1)] = Q(a)
for n, a in enumerate(["'m wearing", "works", "is raining", "never eat", "are you doing", "studies"], 1):
    K[("2.7", n, 1)] = choose(FORMS27[n], a)
for n, a in enumerate("BABB", 1):
    K[("2.8", n, 1)] = choose(["A", "B", "C"], a)
K[("2.9", 1, 1)] = own()
GROUP31 = {"body": "On your body", "feet": "On your feet", "small": "Small things", "jewellery": "Jewellery"}
SORT31 = {"a dress": "body", "a skirt": "body", "jeans": "body", "boots": "feet", "socks": "feet", "trainers": "feet",
          "gloves": "small", "a belt": "small", "a scarf": "small", "earrings": "jewellery", "a ring": "jewellery",
          "a necklace": "jewellery"}
for n, w in enumerate(WORDS31, 1):
    K[("3.1", n, 1)] = choose(["body", "feet", "small", "jewellery"], SORT31[w], labels=GROUP31)
PAIR = ["a", "a pair of", "–"]
for n, a in enumerate(["a pair of", "a", "a pair of", "a", "a pair of", "a"], 1):
    K[("3.2", n, 1)] = choose(PAIR, a)
SOUND = {"1": "1 /ɒ/", "2": "2 /uː/", "3": "3 /ʌ/", "4": "4 /əʊ/"}
for n, a in enumerate("234123412341", 1):
    K[("3.3", n, 1)] = choose(["1", "2", "3", "4"], a, labels=SOUND)
for n, a in enumerate(["take off", "try on", "put on", "take off"], 1):
    K[("3.4", n, 1)] = choose(PUT, a)
for n, a in enumerate([
        either("I'm wearing jeans today", "I am wearing jeans today", "I'm wearing a pair of jeans today",
               "I am wearing a pair of jeans today", "jeans", "a pair of jeans"),
        either("She is wearing earrings", "She's wearing earrings", "earrings"),
        either("He put on his coat and went out", "went"),
        either("Can I try this jumper on", "Can I try on this jumper", "Can I try it on")], 1):
    K[("3.5", n, 1)] = write(a)
for n, a in enumerate(["try", "size", "have", "off"], 1):
    K[("3.6", n, 1)] = Q(a)
K[("3.7", 1, 1)] = write(wearing("black boots, a long coat and a grey scarf", "black boots, a long coat, a grey scarf"))
K[("3.7", 2, 1)] = write(wearing("jeans, a white T-shirt and trainers", "jeans, a white T-shirt, trainers"))
K[("3.7", 3, 1)] = own()
K[("4.1", 1, 1)] = own()
for n in (1, 2):
    K[("4.2", n, 1)] = choose(["a", "b", "c"], "b")
HEARD = {"yes": "✓ heard", "no": "✗ not heard"}
for n, a in enumerate(["yes"] * 5 + ["no"] + ["yes"] * 5 + ["no"], 1):
    K[("4.3", n, 1)] = choose(["yes", "no"], a, labels=HEARD)
for n, a in enumerate("FFTFTF", 1):
    K[("4.4", n, 1)] = choose(["T", "F"], a, labels=TF)
for n, a in enumerate(["having", "not", "believe", "never", "so"], 1):
    K[("4.5", n, 1)] = Q(a)
for n, a in enumerate("BBA", 1):
    K[("4.8", n, 1)] = choose(["A", "B"], a)
for n, a in enumerate("bdac", 1):
    K[("5.1", n, 1)] = choose(PRESENTS51, a)
IF = {"I": "I · informal", "F": "F · formal"}
for n, a in enumerate("IFIFFIIF", 1):
    K[("5.2", n, 1)] = choose(["I", "F"], a, labels=IF)
for n in range(1, 5):
    K[("5.4", n, 1)] = own()
K[("5.5", 20, 1)] = own(control="essay")
K[("5.5", 21, 1)] = own(control="essay")
for n in range(1, 8):                             # the checklist
    K[("5.5", n, 1)] = tick()

if __name__ == "__main__":
    data = h.build(K, "Elementary", 9, "Unit 9B & 9D — Clothes and shopping")
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "e09bd.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
