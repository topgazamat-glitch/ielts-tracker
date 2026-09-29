"""E11AC Entertainment - Azamat's Elementary booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(E11AC Entertainment - ANSWER KEY), joined box by box by hand. The Desktop
copy of this booklet has its section bars run into the boxes that follow
them, which would make the whole booklet one part; the Material Bank copy
is built as the others are, so it is the one used here.

As with the other Elementary booklets, it speaks Uzbek wherever it
explains: every explanation box, the goals, the headings of the grammar
table, the "Why" column of the listening table, and a line under every
instruction. The English examples stay English, as do the reading text,
the dialogues, the model and the exercises.

5.2 numbers its lines and then asks for the order 1-5; the lines lose their
numbers, so the only numbers are the ones tapped. 3.6 and 5.8 are done with
a partner in class.

    python3 handouts/e11ac_digital.py            # writes handouts/e11ac.json, lists every box
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

DOCX = ("~/Documents/Claude/Material Bank/General English/A2 Elementary/_NEW BOOKLET STYLE/"
        "E11AC Entertainment — BOOKLET.docx")
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


# ------------------------------------------------------------ 1 Reading
boxes_for("1.3", range(1, 5))
h.options_on_lines("1.3")
boxes_for("1.4", range(1, 4), where="leader")
h.leaders("1.5", "1.6  </span>", [(1, W, "Six present perfect verbs"), (2, W, "The two negative ones")])
boxes_for("1.6", range(1, 4), where="leader")

# ------------------------------------------------------------ 2 Grammar
FORMS22 = {1: ["'ve seen", "saw"], 2: ["'ve seen", "saw"], 3: ["Have you ever been", "Did you go"],
           4: ["Have you been", "Did you go"], 5: ["'s worked", "worked"], 6: ["'s started", "started"]}
boxes_for("2.2", FORMS22)
for q, a in ((13, 14), (15, 16), (17, 18)):      # 2.3: the question, then the short answer under it
    h.hints[q], h.hints[a] = "Your question", "Short answer"
    h.html = h.html.replace(TAGS[q], TAGS[q] + "<br>", 1)
    h.html = h.html.replace(TAGS[a], re.sub(r"width:[0-9.]+(px|pt|em)", "width:180px", TAGS[a]), 1)
boxes_for("2.4", range(2, 9))                     # item 1 is the worked example
STRESS26 = {1: "I've seen that film.", 2: "I've never seen it.", 3: "Have you read the book?",
            4: "She's worked here for years."}
boxes_for("2.6", STRESS26)
h.leaders("2.8", "3.1  </span>", [(1, W, "Two positive sentences, two with never")])

# ------------------------------------------------------------ 3 Vocabulary
a, b = table_after("3.1")                         # one block per verb, with the forms it gives
rows = [re.findall(r"<td[^>]*>(.*?)</td>", r, re.S) for r in re.findall(r"<tr>(.*?)</tr>", h.html[a:b], re.S)]
names = [plain(c) for c in rows[0][1:]]
grid = ""
for k, row in enumerate(rows[1:], 1):
    bits = []
    for name, cell in zip(names, row[1:]):
        tag = BLANK_TAG.search(cell)
        if tag:
            h.blanks[int(tag.group(1))]["text"] = "%s — %s" % (plain(row[0]), name)
            bits.append('<span style="color:#6E6E6E">%s</span> %s' % (html.escape(name), tag.group(0)))
        else:
            bits.append('<span style="color:#6E6E6E">%s</span> %s' % (html.escape(name), html.escape(plain(cell))))
    grid += ('<p data-item="3.1:%d" style="margin-bottom:8px"><span style="font-weight:700">%s</span><br>%s</p>'
             % (k + 20, html.escape(plain(row[0])), "<br>".join(bits)))
h.html = h.html[:a] + grid + h.html[b:]
boxes_for("3.3", range(1, 5), where="leader")

# ------------------------------------------------------------ 4 Listening
boxes_for("4.1", (1, 2))
h.grid_rows("4.2")
for n in range(1, 6):
    h.item_box("4.6", n, placeholder="If it is false, correct it")
boxes_for("4.7", (1, 2, 3))
h.options_on_lines("4.7")

# ------------------------------------------------------ 5 Everyday English
boxes_for("5.1", (1, 2, 3))
LINES52 = {1: "Did you enjoy it?", 2: "How about you?", 3: "I really liked it.", 4: "So, what did you think of it?",
           5: "Yeah, it was a good concert."}
in_order("5.2", LINES52)
REASONS53 = h.key_first("5.3")
boxes_for("5.7", range(1, 5), where="leader")

# ------------------------------- every instruction, once more, in Uzbek
for label, text in [
        ("1.1", "Muhokama qiling. Oxirgi koʻrgan filmingiz qaysi edi? Kinoteatrdami yoki uydami?"),
        ("1.2", "Buni kim aytadi? *Z* (Zuhra), *K* (Kamol) yoki *M* (Madina) ni tanlang."),
        ("1.3", "Eng toʻgʻri javobni tanlang: *A*, *B* yoki *C*."),
        ("1.4", "Matndan shu maʼnodagi soʻzni toping."),
        ("1.5", "Matndan oltita *present perfect* feʼlini toping. Qaysi ikkitasi inkor shaklda?"),
        ("1.6", "Savollarga javob bering."),
        ("2.1", "*Present perfect* bilan toʻldiring."),
        ("2.2", "*Present perfect* mi yoki *past simple* mi? Tanlang."),
        ("2.3", "Savolni yozing, keyin oʻzingiz haqingizda javob bering."),
        ("2.4", "Xatoni topib, toʻgʻrilang. IKKITA gap toʻgʻri — ular uchun *✓ It is correct* tugmasini bosing."),
        ("2.5", "Suhbatni toʻldiring."),
        ("2.6", "Urgʻuli soʻzni tanlang, keyin har bir gapni ovoz chiqarib ayting."),
        ("2.7", "Har bir gapni maʼnosi oʻzgarmaydigan qilib qayta yozing. Qavs ichidagi soʻzni ishlating."),
        ("2.8", "Oʻzingiz haqingizda toʻrtta rost gap yozing — ikkitasi tasdiq, ikkitasi *never* bilan."),
        ("3.1", "Jadvalni toʻldiring."),
        ("3.2", "Har bir gapni qutidagi *past participle* bilan toʻldiring."),
        ("3.3", "Har bir gapdagi xatoni topib, toʻgʻri gapni yozing."),
        ("3.4", "Qaysi soʻzlarda /ɜː/ tovushi bor? *✓* yoki *✗* ni tanlang, keyin hammasini ovoz chiqarib ayting."),
        ("3.5", "Matnni *present perfect* bilan toʻldiring."),
        ("3.6", "Sherigingizga *Have you ever…?* bilan toʻrtta savol bering. Toʻrt xil *past participle* ishlating. "
                "Buni sinfda bajarasiz."),
        ("4.1", "Bir marta tinglang va javob bering."),
        ("4.2", "Yana tinglang. Kim qaysi aktyorning filmlarini koʻrgan? *✓* yoki *✗* ni tanlang."),
        ("4.3", "Yana tinglang va har bir qatorni toʻldiring."),
        ("4.4", "Tinglang va nima boʻlishiga eʼtibor bering."),
        ("4.5", "Har bir iborani ikki marta ayting — avval sekin, keyin tez."),
        ("4.6", "Toʻgʻri (*T*) mi yoki notoʻgʻri (*F*) mi? Notoʻgʻrilarini toʻgʻrilab yozing."),
        ("4.7", "Gapiruvchi nima demoqchi? *A* yoki *B* ni tanlang."),
        ("5.1", "Tinglang va javob bering."),
        ("5.2", "Suhbatni tartib bilan raqamlang (1–5)."),
        ("5.3", "Fikrni sababi bilan moslang: harfni tanlang."),
        ("5.4", "Javobni yozing. Koʻrsatilganidek rozi boʻling (*A*) yoki hayratingizni bildiring (*S*)."),
        ("5.5", "Koʻtariladimi (↗) yoki pasayadimi (↘)? Keyin har birini ayting."),
        ("5.6", "Namunani oʻqing, keyin javob bering."),
        ("5.7", "Namuna haqidagi savollarga javob bering."),
        ("5.8", "Juftlikda ishlang. Suhbatni oʻtkazing, keyin rollarni almashing. Buni sinfda bajarasiz.")]:
    h.say_also(label, text)

# ------------------------------------------ the explanations, told in Uzbek
h.goals([
    "tajriba haqida gapirish uchun *present perfect* ni ishlatishni va qachon uning oʻrniga *past simple* "
    "kerakligini bilishni",
    "*ever* va *never* ni toʻgʻri joyga qoʻyishni",
    "notoʻgʻri feʼllarning *past participle* shakllarini ishlatishni — *seen, been, written, flown, heard*",
    "odamlarning koʻrgan va koʻrmagan filmlari haqidagi gaplarini tushunishni",
    "fikr soʻrash va bildirishni, *Me too, Me neither, Do you?* bilan javob berishni",
])
h.retell("KEY WORDS", "KALIT SOʻZLAR", [
    "**an usher**  kinoteatrda oʻrningizni koʻrsatadigan xodim",
    "**the screen**  ekran — film koʻrsatiladigan katta oq devor",
    "**an interval**  tanaffus — oʻrtadagi qisqa dam",
    "**the credits**  titrlar — oxiridagi ismlar",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — PRESENT PERFECT", [
    "*Present perfect* ni tajriba haqida gapirish uchun ishlatamiz — hayotingizda qachondir boʻlgan, lekin "
    "qachon ekanini aytmaydigan narsa.",
    "[[+]] *have / has* + *past participle*. *They have acted in some very popular films. · Rose has worked for "
    "UNICEF.* Qisqa shakllar: *I've seen it · She's seen it.*",
    "[[−]] Inkor — *not* *have / has* dan KEYIN keladi. *I haven't seen the film. · He hasn't read the book.*",
    "[[?]] Soʻroq — *have / has* oldin keladi. *Have you seen any of her films? · Has he visited Australia?* "
    "Qisqa javoblar: *Yes, I have. / No, I haven't.*",
    "[[ever]] *ever* va *never* *past participle* dan OLDIN keladi. *Have you ever been to a concert? · I've never "
    "seen a whole film here.*",
    "**Qachon ekanini aytmaymiz.** ✓ *I've seen that film* · ✗ *I've seen that film last year* → *I saw that film "
    "last year.* Vaqtni aytishingiz bilan *past simple* kerak boʻladi.",
])
h.retell("ERROR WARNING", "DIQQAT — KOʻP UCHRAYDIGAN XATOLAR", [
    "Besh narsa notoʻgʻri ketadi, oxirgi uchtasi *never* haqida:",
    "1 **Oʻrniga present simple.** ✗ *I see all of Brad Pitt's films.* → ✓ *I've seen all of Brad Pitt's films.*",
    "2 **Notoʻgʻri yordamchi feʼl.** ✗ *I hasn't been to the USA.* → ✓ *I haven't been to the USA.* *I, you, we, "
    "they* → *have*. *He, she, it* → *has*.",
    "3 **ever va never birga.** ✗ *It's the best film I never ever see.* → ✓ *It's the best film I have ever "
    "seen.*",
    "4 **never bilan yordamchi feʼlsiz.** ✗ *I never see a film with Rose Byrne.* → ✓ *I've never seen a film "
    "with Rose Byrne.*",
    "5 **Ikki inkor.** ✗ *I never don't see a city like it.* → ✓ *I've never seen a city like it.* *never* ning "
    "oʻzi inkor — unga *don't* kerak emas.",
])
h.retell("PRONUNCIATION", "TALAFFUZ — PRESENT PERFECT", [
    "Urgʻu *have* yoki *has* ga emas, *past participle* ga tushadi: *I've SEEN it. · I've NEVer seen it. · Have "
    "you SEEN it?*",
    "*have* esa deyarli yoʻqoladi. *I have seen* → /aɪv siːn/ · *she has worked* → /ʃiːz wɜːkt/. *have* ga urgʻu "
    "bersangiz, kim bilandir bahslashayotgandek eshitilasiz.",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — NOTOʻGʻRI FEʼLLAR", [
    "Toʻgʻri feʼllarga *-ed* qoʻshiladi: *work → worked → worked*. Notoʻgʻri feʼllarga qoʻshilmaydi — ularni "
    "yodlash kerak.",
    "**Uch shakli bir xil:** *read → read → read* /red/ · *had → had · caught → caught · bought → bought · heard "
    "→ heard*",
    "**Baʼzilari -en yoki -n bilan tugaydi:** *break → broke → broken · write → wrote → written · see → saw → "
    "seen · eat → ate → eaten · fly → flew → flown · forget → forgot → forgotten · fall → fell → fallen · grow "
    "→ grew → grown*",
    "**Va har kuni ishlatadiganingiz:** *be → was/were → been. I've been to Italy.*",
    "**read bilan ehtiyot boʻling.** U uch marta bir xil yoziladi, lekin oʻtgan shakllari /red/ — rang kabi — "
    "aytiladi. *I read a lot* /riːd/ — har kuni. *I've read it* /red/ — qachondir.",
])
h.retell("PRONUNCIATION — THE /Ɜː/ SOUND", "TALAFFUZ — /ɜː/ TOVUSHI", [
    "Bitta tovush, besh xil yozilish. Bu *bird* dagi unli, va u choʻziq:",
    "*ir* — *girl, bird* · *ear* — *learn, heard* · *ur* — *nurse, turn* · *er* — *German, person* · *or* — "
    "*work, word*",
    "**Ehtiyot boʻling:** *heard* /hɜːd/, /hiːəd/ emas — u *hear* ga oʻxshab aytilmaydi. Yozilishi juda oʻxshash "
    "boʻlgani uchun bu hammani adashtiradi.",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [
    "Maggie va Stephen hozirgina uchta aktyor haqidagi jurnal viktorinasini yechishdi. Endi javoblarini "
    "solishtirishyapti — va filmlardan qaysilarini haqiqatan koʻrganlari haqida gaplashishyapti.",
    "Agar sinfingizda audio boʻlsa, bu 11.01-trek. Boʻlmasa, oʻqituvchingiz matnni oʻqib beradi — topshiriqlar "
    "bir xil.",
])
h.retell("WHY YOU DIDN'T HEAR IT", "NEGA ESHITMADINGIZ?", [
    "*have* va *has* deyarli yoʻqoladi. *I've seen* → /aɪv siːn/ · *Have you seen…?* → /əvju siːn/ · *she's a "
    "good actor* → /ʃiːzə/. Baland soʻz doim *past participle*.",
    "Shuning uchun oʻquvchiga *I've seen* va *I seen* deyarli bir xil eshitiladi — lekin ulardan faqat bittasi "
    "inglizcha. *Past participle* ga quloq soling, keyin yordamchi feʼlni oldiga oʻzingiz qoʻying.",
])
h.retell("LISTENING INTO SPEAKING", "TINGLASHDAN GAPIRISHGA", [
    "Dan va Martina konsertdan uyga taksida qaytishyapti. Kechadan zavqlanishdi — lekin uning har xil "
    "qismlaridan.",
])
h.retell("ASKING FOR AND EXPRESSING OPINIONS", "FIKR SOʻRASH VA BILDIRISH", [
    "**Soʻrash:** *So, what did you think of it? · Did you enjoy it? · How about you?*",
    "**Javob berish:** *Yeah, it was a good concert. · I really liked it.*",
    "Eng yaxshidan eng yomongacha uch daraja:",
    "*I really liked the first band.* → *I didn't like the first band very much.* → *I didn't like the first band "
    "at all.*",
    "**Keyin sabab ayting.** Yolgʻiz fikr suhbatni toʻxtatadi; *I thought…* bilan aytilgan fikr esa uni davom "
    "ettiradi. *I really liked them — I thought the singer was great.*",
])
h.retell("RESPONDING TO AN OPINION", "FIKRGA JAVOB BERISH", [
    "Kimdir fikr bildiradi. Munosabat bildirishga taxminan bir soniyangiz bor, shuning uchun ingliz tilida ikki "
    "soʻzli javoblar ishlatiladi:",
    "**Rozi boʻlsangiz** — *I liked it.* → *Me too.* · *I didn't like it.* → *Me neither.*",
    "**Hayron boʻlsangiz va unchalik rozi boʻlmasangiz** — *I liked it.* → *Did you?* · *I think they're great.* "
    "→ *Do you?*",
    "*have* emas, *do* yoki *did* ishlating. Va javob berayotgan gapingizdagi zamonni ishlating: *I liked it.* → "
    "*Did you?* · *I like them.* → *Do you?*",
    "**Ehtiyot boʻling:** *Me neither* inkorga javob beradi. Kimdir *I didn't like it* desa va siz *Me too* desangiz, "
    "uning aytganining teskarisiga rozi boʻlgan boʻlasiz.",
])
h.retell("PRONUNCIATION — MAIN STRESS AND INTONATION", "TALAFFUZ — ASOSIY URGʻU VA OHANG", [
    "Bu javoblarda ikkala soʻz ham urgʻuli — *DO YOU? · DID YOU? · ME TOO. · ME NEITHER.*",
    "**Yoʻnalish — maʼno.** *Do you?* ↗ va *Did you?* ↗ koʻtariladi — siz hayronsiz. *Me too.* ↘ va *Me "
    "neither.* ↘ pasayadi — siz rozisiz.",
    "*Did you?* ni pasayuvchi ovoz bilan aytsangiz, zerikkan yoki jahli chiqqandek eshitilasiz — siz buni "
    "nazarda tutmagansiz. Barcha xushmuomalalikni koʻtarilish bajaradi.",
])
h.retell("CHECK YOUR CONVERSATION", "SUHBATINGIZNI TEKSHIRING", [
    "{box}  Faqat oʻz fikrimni aytmay, sherigimning fikrini ham soʻradim.   {box}  Uchala darajani ham ishlatdim "
    "— *really liked / didn't like very much / didn't like at all*.",
    "{box}  Har safar *I thought…* bilan sabab aytdim.   {box}  Kamida ikki marta *Me too, Me neither, Do you?* "
    "yoki *Did you?* bilan javob berdim.",
    "{box}  *Did you?* im koʻtarildi, *Me too* m pasaydi.   {box}  Inkordan keyin *Me too* emas, *Me neither* "
    "ishlatdim.",
])
h.one_per_line("SUHBATINGIZNI TEKSHIRING", None, at="box")
h.retell_cells({"Present perfect — experience, no time said": "Present perfect — tajriba, vaqt aytilmaydi",
                "Past simple — a finished time": "Past simple — tugagan vaqt"})
h.retell_cells({"What is written": "Yozilishi", "What you hear": "Eshitilishi", "Why": "Nega",
                "have you becomes one weak sound": "<i>have you</i> bitta kuchsiz tovushga aylanadi",
                "the negative is stressed": "inkor urgʻu oladi",
                "I've only runs together": "<i>I've only</i> qoʻshilib ketadi",
                "she's a is one sound": "<i>she's a</i> bitta tovush"},
               after="4.4  </span>")

# ------------------------------------------------------------------ the key
K = {}
ZKM = {"Z": "Z · Zuhra", "K": "K · Kamol", "M": "M · Madina"}
for n, a in enumerate("KMZKMZ", 1):
    K[("1.2", n, 1)] = choose(["Z", "K", "M"], a, labels=ZKM)
for n in range(1, 5):
    K[("1.3", n, 1)] = choose(["A", "B", "C"], "B")
for n, a in enumerate(["an usher/usher", "a projectionist/projectionist", "a recommendation/recommendation"], 1):
    K[("1.4", n, 1)] = Q(a)
K[("1.5", 1, 1)] = own()
K[("1.5", 2, 1)] = own()
for n in range(1, 4):
    K[("1.6", n, 1)] = own()
for key, a in (((1, 1), either("have acted", "'ve acted")), ((2, 1), either("has worked", "'s worked")),
               ((3, 1), either("has directed", "'s directed")), ((4, 1), either("haven't seen", "have not seen")),
               ((5, 1), "Have"), ((5, 2), "read"), ((6, 1), either("has never been", "'s never been"))):
    K[("2.1",) + key] = Q(a)
for n, a in enumerate(["saw", "'ve seen", "Have you ever been", "Did you go", "'s worked", "started"], 1):
    K[("2.2", n, 1)] = choose(FORMS22[n], a)
for n, (question, short) in enumerate([
        ("Have you ever been to a concert", "Yes, I have/No, I haven't/No, I have not/No, never"),
        ("Have you ever eaten sushi", "Yes, I have/No, I haven't/No, I have not/No, never"),
        ("Has your family ever flown to another country",
         "Yes, it has/No, it hasn't/Yes, they have/No, they haven't/No, never")], 1):
    K[("2.3", n, 1)] = write(question)
    K[("2.3", n, 2)] = Q(short)
TICKED = "✓/correct/tick"
for n, a in zip(range(2, 9), [
        either("I haven't been to the USA", "haven't"),
        either("It's the best film I have ever seen", "It's the best film I've ever seen", "I have ever seen",
               "I've ever seen"),
        either("I've never seen a film with Rose Byrne", "I have never seen a film with Rose Byrne", "I've never seen"),
        TICKED,
        either("I never eat fish", "I've never eaten fish", "I have never eaten fish"),
        TICKED,
        either("She worked here last year", "worked")]):
    K[("2.4", n, 1)] = fix(a)
for n, a in enumerate(["Have you seen", either("haven't seen", "have not seen"), either("'ve read", "have read"),
                       "Have you ever read", "Have they made", either("'ve made", "have made"),
                       either("'ve heard", "have heard"), either("haven't watched", "have not watched")], 1):
    K[("2.5", n, 1)] = Q(a)
STRESSED26 = {1: "seen", 2: "never", 3: "read", 4: "worked"}
for n, sentence in STRESS26.items():
    K[("2.6", n, 1)] = choose(sentence.rstrip(".?").split(), STRESSED26[n])
for n, a in enumerate(["ever eaten sushi", "been to Turkey/been to Turkey before",
                       "worked here since 2021/been working here since 2021",
                       either("haven't seen that film", "have not seen that film", "haven't seen it")], 1):
    K[("2.7", n, 1)] = Q(a)
K[("2.8", 1, 1)] = own()
for n, a in enumerate(["broken", "saw", "seen", "wrote", "written", "caught", "caught", "flew", "flown", "forgot",
                       "forgotten", "grew", "grown", "was/were/was, were/was / were", "been"], 1):
    K[("3.1", n, 1)] = Q(a)
BOX32 = ["been", "bought", "broken", "eaten", "fallen", "flown", "heard", "read", "seen", "written"]
for n, a in enumerate(["seen", "bought", "been", "broken", "read", "flown", "heard", "fallen"], 1):
    K[("3.2", n, 1)] = choose(BOX32, a)
for n, a in enumerate([either("I've seen that film before", "I have seen that film before", "seen"),
                       either("She's written three books", "She has written three books", "written"),
                       either("Have you ever been to a concert", "been"),
                       either("I've never eaten sushi", "I have never eaten sushi", "eaten")], 1):
    K[("3.3", n, 1)] = write(a)
ER = {"yes": "✓ /ɜː/", "no": "✗ not /ɜː/"}
for n, a in enumerate(["yes", "no", "yes", "yes", "yes", "no", "yes", "yes"], 1):
    K[("3.4", n, 1)] = choose(["yes", "no"], a, labels=ER)
for n, a in enumerate([either("has been", "'s been"), either("has flown", "'s flown"),
                       either("has never liked", "'s never liked"), either("has read", "'s read"),
                       either("has written", "'s written"), either("has never shown", "'s never shown"), "saw",
                       either("hasn't forgotten", "has not forgotten")], 1):
    K[("3.5", n, 1)] = Q(a)
K[("4.1", 1, 1)] = choose(["Yes", "No"], "No")
K[("4.1", 2, 1)] = choose(["Maggie", "Stephen", "neither"], "neither",
                          labels={"neither": "neither — two wrong each"})
SEEN = {"yes": "✓ seen", "no": "✗ not seen"}
for n, a in enumerate(["no", "yes", "yes", "yes", "no", "yes"], 1):   # Maggie, then Stephen: Rose, Mia, Margot
    K[("4.2", n, 1)] = choose(["yes", "no"], a, labels=SEEN)
for key, a in (((1, 1), either("haven't seen", "have not seen")), ((2, 1), "have"), ((2, 2), "seen"),
               ((3, 1), "never"), ((4, 1), either("haven't seen", "have not seen")), ((5, 1), "heard")):
    K[("4.3",) + key] = Q(a)
TF = {"T": "T · true", "F": "F · false"}
for n, a in enumerate("FTTTF", 1):
    K[("4.6", n, 1)] = choose(["T", "F"], a, labels=TF)
    K[("4.6", n, 2)] = note()
for n, a in enumerate("BBA", 1):
    K[("4.7", n, 1)] = choose(["A", "B"], a)
K[("5.1", 1, 1)] = own()
K[("5.1", 2, 1)] = choose(["Yes", "No"], "No")
K[("5.1", 3, 1)] = own()
# in order: So what did you think, Did you enjoy it, Yeah it was a good concert, I really liked it, How about you
for n, a in {1: "2", 2: "5", 3: "4", 4: "1", 5: "3"}.items():
    K[("5.2", n, 1)] = choose(["1", "2", "3", "4", "5"], a)
for n, a in enumerate("bca", 1):
    K[("5.3", n, 1)] = choose(REASONS53, a)
for n, a in enumerate(["Me too", "Me neither", "Did you/Do you", "Do you"], 1):
    K[("5.4", n, 1)] = Q(a)
UPDOWN = {"up": "↗ up", "down": "↘ down"}
for n, a in enumerate(["up", "up", "down", "down"], 1):
    K[("5.5", n, 1)] = choose(["up", "down"], a, labels=UPDOWN)
for n in range(1, 5):
    K[("5.7", n, 1)] = own()
for n in range(1, 7):                             # the checklist, after the pair work
    K[("5.8", n, 1)] = tick()

if __name__ == "__main__":
    data = h.build(K, "Elementary", 11, "Unit 11A & 11C — Entertainment")
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "e11ac.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
