"""E11BD Entertainment - Azamat's Elementary booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(E11BD Entertainment - answer key), joined box by box by hand. The Desktop
"new design" copy is used; it splits into its five parts as it should.

As with the other Elementary booklets, it speaks Uzbek wherever it
explains: every explanation box, the goals, the headings of the grammar
table, the "Why" column of the listening table, and a line under every
instruction. The English examples stay English, as do the reading text,
the dialogues, the model and the exercises.

3.3 asks for the number of syllables and the stressed one: each word gets
both. 3.5 item 1 is about how live is said, written between slashes, which
the marking cannot hold, so the teacher reads it (as with item 3, where
several fixes work). 2.5, 3.6 (the partner's column) and 4.7's questions are
done with a partner in class.

    python3 handouts/e11bd_digital.py            # writes handouts/e11bd.json, lists every box
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import (Handout, Q, choose, tick, own, write, fix, note, pair, report,   # noqa: E402
                     BLANK_TAG, LEADER_P, plain, told, ITEM_STYLE, NUM_SPAN, TEXT_SPAN)

DOCX = "~/Desktop/Handouts/A2 Elementary/E11BD Entertainment/E11BD Entertainment — handout (new design).docx"
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


def uzbek_after(containing, text):
    """An Uzbek line under a paragraph that is not an exercise's instruction."""
    at = h.html.index(containing)
    end = h.html.index("</p>", at) + len("</p>")
    h.html = h.html[:end] + '<p class="hx-uz" lang="uz">%s</p>' % told(text, bare=True) + h.html[end:]


# ------------------------------------------------------------ 1 Reading
boxes_for("1.3", range(1, 5), where="options")
h.options_on_lines("1.3")
boxes_for("1.4", range(1, 4), where="leader")
h.leaders("1.5", "1.6  </span>", [(1, W, "Three present perfect verbs, and why"),
                                  (2, W, "Three past simple verbs, and why")])
boxes_for("1.6", range(1, 4), where="leader")

# ------------------------------------------------------------ 2 Grammar
boxes_for("2.4", range(2, 9))                     # item 1 is the worked example

# ------------------------------------------------------------ 3 Vocabulary
WORDS31 = h.sort_words("3.1", ["a band", "classical", "a club", "a DJ", "a festival", "folk", "jazz", "a musician",
                               "an orchestra", "a theatre"], "Kinds of music")
SYLLABLES33 = {1: "sing-er", 2: "mu-sic-ian", 3: "class-ic-al", 4: "or-ches-tra", 5: "fes-ti-val", 6: "au-di-ence"}
for n in SYLLABLES33:
    h.item_box("3.3", n)                          # the stressed syllable, after the count
ODD34 = h.odd_one_out("3.4", why="Why is it different?")
boxes_for("3.5", range(1, 5), where="leader")
h.grid_rows("3.6")

# ------------------------------------------------------------ 4 Listening
h.leaders("4.1", "4.2  </span>", [(1, W, "Three places — and has Alana been?")])
h.grid_rows("4.2")
boxes_for("4.6", (1, 2, 3))
h.options_on_lines("4.6")
a, b = table_after("4.7")                         # one place a block: the place, then its three answers
tags = [t.group(0) for t in BLANK_TAG.finditer(h.html[a:b])]
blocks = ""
for k in range(3):
    place, been, when, liked = tags[4 * k:4 * k + 4]
    blocks += ('<p data-item="4.7:%d" style="margin-bottom:8px"><span style="font-weight:700">Place %d</span> %s<br>'
               '<span style="color:#6E6E6E">Been there?</span> %s<br><span style="color:#6E6E6E">When?</span> %s<br>'
               '<span style="color:#6E6E6E">Liked it?</span> %s</p>' % (20 + k, k + 1, place, been, when, liked))
h.html = h.html[:a] + blocks + h.html[b:]

# ------------------------------------------------------------ 5 Writing
boxes_for("5.1", (1, 2, 3), where="leader")
at = h.html.index("</table>", h.html.index("nobody knew Yalitza Aparicio at all")) + len("</table>")
h.html = (h.html[:at] + '<p style="margin-bottom:8px">{{box:5.3:1:95%:The paragraph again, without the repeated '
          'words}}</p>' + h.html[at:])
h.texts[("5.3", 1)] = "The paragraph, rewritten"
boxes_for("5.5", range(1, 5), where="leader")
h.leaders("5.7", "CHECK BEFORE", [(20, W, "Write your review here")])
h.html = h.html.replace(TAGS[117], "", 1)         # the word count: the box counts them itself

# ------------------------------- every instruction, once more, in Uzbek
for label, text in [
        ("1.1", "Muhokama qiling. Shahringizda jonli musiqani qayerda eshitish mumkin? U yerdagi konsertga hech "
                "borganmisiz?"),
        ("1.2", "Qaysi joy? *C* (konsert zali), *O* (eski kafe), *F* (festival), *J* (jaz klubi) yoki *T* (teatr) ni "
                "tanlang."),
        ("1.3", "Eng toʻgʻri javobni tanlang: *A*, *B* yoki *C*."),
        ("1.4", "Matndan shu maʼnodagi soʻz yoki iborani toping."),
        ("1.5", "Uchta *present perfect* va uchta *past simple* feʼlini toping. Har biri nega ishlatilgan?"),
        ("1.6", "Savollarga javob bering."),
        ("2.1", "*Present perfect* (*PP*) mi yoki *past simple* (*PS*) mi? Faqat vaqt iborasiga qarang."),
        ("2.2", "*Present perfect* yoki *past simple* bilan toʻldiring."),
        ("2.3", "Suhbatni toʻldiring."),
        ("2.4", "Xatoni topib, toʻgʻrilang. IKKITA gap toʻgʻri — ular uchun *✓ It is correct* tugmasini bosing."),
        ("2.5", "Sherigingizdan soʻrang. *Present perfect* bilan boshlang, keyin *past simple* da ikkita savol bering. "
                "Buni sinfda bajarasiz."),
        ("2.6", "Tinglang va ayting. Qaysi zamon?"),
        ("3.1", "Har bir soʻzning guruhini tanlang: musiqa turi, odamlar yoki joylar."),
        ("3.2", "Har bir gapni musiqa soʻzi bilan toʻldiring."),
        ("3.3", "Nechta boʻgʻin bor? Keyin urgʻuli boʻgʻinni tanlang."),
        ("3.4", "Qaysi soʻz boshqacha? Uni tanlang va nega ekanini yozing."),
        ("3.5", "Har bir gapdagi xatoni topib, toʻgʻri gapni yozing."),
        ("3.6", "Hayotingizdagi musiqa. Jadvalni oʻzingiz uchun toʻldiring, keyin sherigingizdan soʻrang. Sherigingiz "
                "ustunini sinfda toʻldirasiz."),
        ("4.1", "Bir marta tinglang. Ular qaysi uchta joy haqida gapirishadi? Alana ularda boʻlganmi?"),
        ("4.2", "Yana tinglang va jadvalni toʻldiring."),
        ("4.3", "Yana bir marta tinglang va har bir qatorni toʻldiring."),
        ("4.4", "Tinglang va nima boʻlishiga eʼtibor bering."),
        ("4.5", "Har bir iborani ikki marta ayting — avval sekin, keyin tez."),
        ("4.6", "Gapiruvchi nima demoqchi? *A* yoki *B* ni tanlang."),
        ("4.7", "Endi siz ham shunday qiling. Shahringizda odamlar dam olishga boradigan uchta joyni yozing."),
        ("5.1", "Tinglang va javob bering."),
        ("5.2", "Buni kim aytadi — Melissa (*M*) mi yoki John (*J*) mi?"),
        ("5.3", "Paragrafni qayta yozing. Takrorlangan soʻzlarni almashtiring."),
        ("5.4", "Namunaviy taqrizni oʻqing, keyin javob bering."),
        ("5.5", "Namuna haqidagi savollarga javob bering."),
        ("5.6", "Avval reja tuzing. Ikki daqiqa, keyin yozing."),
        ("5.7", "Endi oʻzingiz koʻrgan film haqida taqriz yozing (100–120 soʻz).")]:
    h.say_also(label, text)
uzbek_after("Ask like this:", "Shunday soʻrang: *Have you ever seen …?* → *When did you see them? Who did you go with?* "
            "2-boʻlimdagidek, *present perfect* bilan boshlang, keyin *past simple* ga oʻting.")
uzbek_after("Now ask your partner about ", "Endi sherigingizdan uning uchta joyi haqida soʻrang. Har "
            "bir savolingiz *Have you ever…?* bilan boshlansin — lekin „ha“ degan har bir javobdan keyin ikkita *past "
            "simple* savol bering. Sherigingiz necha marta zamonni almashtirishini sanang.")

# ------------------------------------------ the explanations, told in Uzbek
h.goals([
    "bitta savol yordamida *present perfect* va *past simple* orasida tanlashni",
    "*past simple* ni talab qiladigan vaqt iboralarini topishni",
    "musiqa haqidagi soʻzlarni ishlatishni — turlari, odamlar va joylar",
    "odamlarning borgan va bormagan joylari haqidagi gaplarini tushunishni",
    "taqrizni tartibli tuzishni va nomni takrorlamaslikni",
])
h.retell("KEY WORDS", "KALIT SOʻZLAR", [
    "**live music**  jonli musiqa — yozib olingan emas, hozir chalinayotgan",
    "**a venue**  musiqa boʻladigan joy",
    "**a band**  kichik musiqa guruhi",
    "**an audience**  tomoshabinlar",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — PRESENT PERFECT YOKI PAST SIMPLE?", [
    "Ikkala zamonni ham bilasiz. Bu dars ular orasida tanlash haqida — va buni har safar bitta savol hal qiladi.",
    "[[Q]] **QACHON ekanini aytyapmanmi?** Qachon ekanini aytsangiz, *past simple* ishlatishingiz shart. "
    "Aytmasangiz, *present perfect* ishlating.",
    "[[PP]] **Present perfect = tajriba.** *I've been to the concert hall. · I've never been to the festival.* "
    "Savolda: *Have you ever been there?* Gap qachon ekanida emas, boʻlganida.",
    "[[PS]] **Past simple = tafsilotlar.** *I went last spring. · We heard an orchestra. · I didn't like it.* "
    "Boʻlganini bilganingizdan keyin qolgan hammasi *past simple*.",
    "[[→]] **Ular birga ishlaydi.** *Have you ever been to Szimpla Kert? — Yes, I have. I went two weeks ago and "
    "they had a really good band.* Savol *present perfect* bilan ochiladi; javob *past simple* ga oʻtadi.",
    "**Past simple ni talab qiladigan vaqt soʻzlari:** *yesterday · last week · in 2019 · two weeks ago · when I "
    "was fifteen*. **Present perfect bilan keladigan vaqt soʻzlari:** *ever · never · before · in my life · this "
    "month* (oy hali tugamagan).",
])
h.retell("ERROR WARNING", "DIQQAT — IKKI TOMONLAMA XATO", [
    "Xato ikkala tomonga ham ketadi, shuning uchun ikkala yoʻnalishda ham tekshiring:",
    "1 **Present perfect kerak joyda past simple.** ✗ *I didn't buy new clothes this month.* → ✓ *I haven't bought "
    "new clothes this month.* Bu oy hali tugamagan.",
    "2 **Past simple kerak joyda present perfect.** ✗ *Last year I've been to the National Concert Hall.* → ✓ "
    "*Last year I went to the National Concert Hall.* Oʻtgan yil tugagan.",
    "3 **Present perfect gapda vaqt soʻzi.** ✗ *I've seen that film yesterday.* → ✓ *I saw that film yesterday.*",
    "**Bir soniyalik tekshiruv.** Vaqt iborasini qidiring. Agar u bor va tugagan boʻlsa, feʼl *past simple* "
    "boʻlishi shart. Vaqt iborasi umuman boʻlmasa, deyarli har doim *present perfect*.",
])
h.retell("PRONUNCIATION", "TALAFFUZ — IKKI ZAMON", [
    "Ikki zamon butunlay boshqacha eshitiladi, farq esa /v/ yoki /z/ da. *I've been* → /aɪv biːn/ · *I went* → "
    "/aɪ went/. Feʼldan oldingi oʻsha kichik tovushga quloq soling.",
    "Savolda ham: *Have you been…?* → /əvju biːn/ · *Did you go…?* → /dɪdʒə gəʊ/. Yordamchi feʼllarning hech biri "
    "urgʻu olmaydi, shuning uchun aniq eshitiladigan yagona soʻz — feʼl, u qaysi zamon ekanini aytadi.",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — MUSIQA", [
    "**Musiqa turlari:** *classical · jazz · opera · rock · pop · folk · dance · world music*",
    "**Musiqa yaratadigan odamlar:** *an orchestra · a musician · a band · a DJ · a singer · a rock star*",
    "**Musiqa eshitiladigan joylar:** *a concert hall · a club · a music venue · a theatre · a festival*",
    "**LIVE soʻzi ikki xil aytiladi.** *I live /lɪv/ in Tashkent* — bu feʼl. · *live /laɪv/ music* — bu sifat, "
    "„yozib olinmagan“ degani. Yozilishi bir xil, soʻz boshqa.",
    "**Ehtiyot boʻling:** *an orchestra* — katta klassik guruh; *a band* — kichik va odatda klassik emas. *A DJ* "
    "boshqalarning musiqasini qoʻyadi — *a musician* esa oʻz musiqasini chaladi.",
])
h.retell("PRONUNCIATION — SYLLABLES AND STRESS", "TALAFFUZ — BOʻGʻINLAR VA URGʻU", [
    "Boʻgʻinlarni sanang, keyin kuchlisini toping. Ikkalasi ham muhim: urgʻusi notoʻgʻri joyda boʻlgan soʻz "
    "koʻpincha umuman tushunilmaydi.",
    "2 boʻgʻin: *SING-er* · 3 boʻgʻin: *mu-SIC-ian · CLASS-ic-al · OR-ches-tra · FES-ti-val*",
    "**MUSIC soʻziga nima boʻlishiga qarang.** *MU-sic* da urgʻu boshida; *mu-SIC-ian* da oʻrtaga koʻchadi. "
    "*-ian* qoʻshilsa, urgʻu oldinga tortiladi — bu tasodif emas, qoida.",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [
    "Max shaharda bir yildan beri yashaydi va hech qayerga bormagan. Alana esa bu yerda oʻn uch yoshidan beri "
    "yashaydi. Max hozirgina shahardagi musiqa qanchalik yaxshi ekani haqida maqola oʻqidi.",
    "Agar sinfingizda audio boʻlsa, bu 11.11-trek. Boʻlmasa, oʻqituvchingiz matnni oʻqib beradi — topshiriqlar "
    "bir xil.",
])
h.retell("WHY YOU DIDN'T HEAR IT", "NEGA ESHITMADINGIZ?", [
    "**Yordamchi feʼllar juda kichik, lekin butun maʼno ularda.** *I've never been* → /aɪv nevəbɪn/ · *I went "
    "there* → /aɪ wentðeə/. Ikkalasi ham uch soʻz; birida /v/ bor, ikkinchisida yoʻq.",
    "**Buning oʻrniga vaqt iborasiga quloq soling.** U doim urgʻuli — *two weeks ago, last year, never* — va "
    "yordamchi feʼl butunlay yoʻqolib ketganda ham zamonni aytib beradi.",
])
h.retell("LISTENING INTO WRITING", "TINGLASHDAN YOZISHGA", [
    "Avval: Melissa va John ikkalasi bir filmni koʻrishgan. Ular u haqida umuman kelisha olmaydi.",
])
h.retell("HOW A REVIEW IS ORGANISED", "TAQRIZ QANDAY TUZILADI", [
    "Qisqa taqriz taxminan shu tartibda quyidagi savollarga javob beradi:",
    "1 **Bu nima va uni kim yaratgan?** Film nomi va rejissyori. Nomni bir marta, boshida ayting.",
    "2 **U nima haqida?** Ikki gap. Oxirini aytmang.",
    "3 **Filmning oʻzi haqida nima deb oʻylaysiz?** Voqea, tasvir, musiqa.",
    "4 **Aktyorlar haqida nima deb oʻylaysiz?** Bittasining nomini ayting va nega ekanini tushuntiring.",
    "5 **Uni tavsiya qilasizmi?** Oxirida bitta aniq gap.",
    "**Ehtiyot boʻling:** 3- va 4-qismlar alohida. Film va aktyorlar orasida sakrab yuradigan taqrizni kuzatish "
    "qiyin.",
])
h.retell("AVOIDING REPETITION", "TAKRORLASHDAN QOCHISH", [
    "Ingliz tilida nom qayta-qayta takrorlanmaydi. Bir marta aytganingizdan keyin qisqaroq soʻz ishlating.",
    "**Film** → *it · the film · this film*. *Roma … Roma … Roma* emas.",
    "**Odam** → *she · her · he · his*. *Yalitza Aparicio … Yalitza Aparicio* emas.",
    "**Nega muhim.** Nomni takrorlash taqrizni boshlovchi yozgandek qilishning eng tez yoʻli. Uni almashtirish — "
    "buni tuzatishning eng tez yoʻli.",
])
h.retell("CHECK BEFORE YOU HAND IT IN", "TOPSHIRISHDAN OLDIN TEKSHIRING", [
    "{box}  Beshala qism, tartib bilan.   {box}  Nom bir marta, boshida.   {box}  Keyin *it, the film* yoki "
    "*this film* ishlatdim.",
    "{box}  Aktyor nomini takrorlash oʻrniga *she / he / her / his* ishlatdim.   {box}  Film va aktyorlar alohida "
    "xatboshilarda.",
    "{box}  Bitta *present perfect* (*I've seen it…*) va tafsilotlar uchun *past simple*.   {box}  Oxirini "
    "aytmadim.   {box}  Soʻzlarni sanadim.",
])
h.one_per_line("TOPSHIRISHDAN OLDIN TEKSHIRING", None, at="box")
h.retell_cells({"Present perfect — did it happen?": "Present perfect — boʻlganmi?",
                "Past simple — tell me about it": "Past simple — tafsilotini ayting"})
h.retell_cells({"What is written": "Yozilishi", "What you hear": "Eshitilishi", "Why": "Nega",
                "I have is one /v/": "<i>I have</i> bitta /v/ boʻlib qoladi",
                "have you almost vanishes": "<i>have you</i> deyarli yoʻqoladi",
                "no /v/ — it's the past simple": "/v/ yoʻq — bu <i>past simple</i>",
                "the negative is stressed": "inkor urgʻu oladi"},
               after="4.4  </span>")

# ------------------------------------------------------------------ the key
K = {}
PLACE = {"C": "C · concert hall", "O": "O · old café", "F": "F · festival", "J": "J · jazz club", "T": "T · theatre"}
for n, a in enumerate("OFTJCF", 1):
    K[("1.2", n, 1)] = choose(["C", "O", "F", "J", "T"], a, labels=PLACE)
for n in range(1, 5):
    K[("1.3", n, 1)] = choose(["A", "B", "C"], "B")
for n, a in enumerate(["live music/live", "an orchestra/orchestra", "keep meaning to/I keep meaning to"], 1):
    K[("1.4", n, 1)] = Q(a)
K[("1.5", 1, 1)] = own()
K[("1.5", 2, 1)] = own()
for n in range(1, 4):
    K[("1.6", n, 1)] = own()
TENSE = {"PP": "PP · present perfect", "PS": "PS · past simple"}
for n, a in enumerate(["PS", "PP", "PS", "PP", "PS", "PP", "PS", "PP"], 1):
    K[("2.1", n, 1)] = choose(["PP", "PS"], a, labels=TENSE)
for key, a in (((1, 1), "Have"), ((1, 2), "been"), ((2, 1), "went"),
               ((3, 1), either("have never seen", "'ve never seen", "had never seen", "'d never seen")),
               ((4, 1), either("has played", "'s played", "has been playing", "'s been playing")),
               ((5, 1), either("didn't enjoy", "did not enjoy")), ((5, 2), "sat"),
               ((6, 1), either("haven't bought", "have not bought"))):
    K[("2.2",) + key] = Q(a)
for n, a in enumerate(["Have you seen", either("didn't know", "did not know"), either("didn't know", "did not know"),
                       either("haven't been", "have not been"),
                       either("'ve lived", "have lived", "'ve been living", "have been living"), "Have you ever been",
                       "went", "had", either("have never been", "'ve never been"), "have", "went", "saw",
                       "did you think", either("didn't like", "did not like")], 1):
    K[("2.3", n, 1)] = Q(a)
TICKED = "✓/correct/tick"
for n, a in zip(range(2, 9), [
        either("Last year I went to the concert hall", "went"),
        either("I saw that film yesterday", "saw"),
        TICKED,
        either("She started working there in 2018", "started"),
        TICKED,
        either("I never went to the opera when I was a child", "I didn't go to the opera when I was a child",
               "never went"),
        either("Have you ever seen an opera in your life", "Have you ever seen")]):
    K[("2.4", n, 1)] = fix(a)
for n in range(1, 7):                             # questions for a partner, in class
    K[("2.5", n, 1)] = pair()
for n, a in enumerate(["PP", "PS", "PP", "PS"], 1):
    K[("2.6", n, 1)] = choose(["PP", "PS"], a, labels=TENSE)
GROUP31 = {"music": "Kinds of music", "people": "People", "places": "Places"}
SORT31 = {"classical": "music", "folk": "music", "jazz": "music", "a band": "people", "a DJ": "people",
          "a musician": "people", "an orchestra": "people", "a club": "places", "a festival": "places",
          "a theatre": "places"}
for n, w in enumerate(WORDS31, 1):
    K[("3.1", n, 1)] = choose(["music", "people", "places"], SORT31[w], labels=GROUP31)
for n, a in enumerate(["orchestra", "band", "musician", "DJ/band", "festival", "theatre"], 1):
    K[("3.2", n, 1)] = Q(a)
STRESSED33 = {1: "sing", 2: "sic", 3: "class", 4: "or", 5: "fes", 6: "au"}
for n, word in SYLLABLES33.items():
    parts = word.split("-")
    K[("3.3", n, 1)] = choose(["1", "2", "3", "4"], str(len(parts)))
    K[("3.3", n, 2)] = choose(parts, STRESSED33[n])
for n, a in {1: "orchestra", 2: "a theatre", 3: "a musician", 4: "a rock star"}.items():
    K[("3.4", n, 1)] = choose(ODD34[n], a)
    K[("3.4", n, 2)] = own()
K[("3.5", 1, 1)] = own()                          # /laɪv/ between slashes: the teacher reads it
K[("3.5", 2, 1)] = write(either("An orchestra played classical music all night", "A band played rock music all night",
                                "classical music", "classical"))
K[("3.5", 3, 1)] = own()
K[("3.5", 4, 1)] = write(either("We went to a concert hall to hear classical music",
                                "We went to a festival to hear classical music", "a concert hall", "concert hall"))
for n in range(1, 9):                             # 3.6: theirs in the left column, a partner's on the right
    K[("3.6", n, 1)] = own(control=None) if n % 2 else pair()
K[("4.1", 1, 1)] = own()
for n, a in enumerate(["two weeks ago", "yes/Yes, there was a really good band",
                       "for Zoltan's birthday/Zoltan's birthday/at Zoltan's birthday/on Zoltan's birthday",
                       "yes/Yes, they had a fantastic time",
                       "last year/last year, for her father's birthday/last year, her father's fiftieth birthday/"
                       "for her dad's fiftieth birthday", "no/No, not much/not much"], 1):
    K[("4.2", n, 1)] = Q(a)
for key, a in (((1, 1), either("haven't been", "have not been")), ((1, 2), either("'ve lived", "have lived")),
               ((2, 1), "Have"), ((2, 2), "been"), ((3, 1), "went"), ((4, 1), either("have never", "'ve never")),
               ((5, 1), "went")):
    K[("4.3",) + key] = Q(a)
for n in (1, 2, 3):
    K[("4.6", n, 1)] = choose(["A", "B"], "B")
for n in range(1, 13):                            # their own three places
    K[("4.7", n, 1)] = own(control=None)
K[("5.1", 1, 1)] = write("A James Bond film/a James Bond film/James Bond/the new James Bond film/a Bond film")
K[("5.1", 2, 1)] = own()
K[("5.1", 3, 1)] = own()
MJ = {"M": "M · Melissa", "J": "J · John"}
for n, a in enumerate("MJMJ", 1):
    K[("5.2", n, 1)] = choose(["M", "J"], a, labels=MJ)
K[("5.3", 1, 1)] = own()
for n in range(1, 5):
    K[("5.5", n, 1)] = own()
for n in range(1, 6):                             # the plan: notes
    K[("5.6", n, 1)] = own(control=None)
K[("5.7", 20, 1)] = own(control="essay")
for n in range(1, 9):                             # the checklist
    K[("5.7", n, 1)] = tick()

if __name__ == "__main__":
    data = h.build(K, "Elementary", 11, "Unit 11B & 11D — Entertainment")
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "e11bd.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
