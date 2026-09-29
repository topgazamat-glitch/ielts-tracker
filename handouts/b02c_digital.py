"""B02C All about me - Azamat's Beginner booklet (2C), done on a phone.

His design is rendered as it is and this decides every box. The key is his
(B02C All about me - ANSWER KEY), joined box by box by hand. This one exists
only in the Material Bank (_NEW BOOKLET STYLE); it splits into its five parts
as it should.

As with the other Beginner booklets, every box that explains is told again
in Uzbek, as are the goals and every instruction; the English examples stay
English, as do the reading, the forms and the exercises.

2.3 is the four phrases of "When you don't hear it" to tap, and 4.2 a tap
between the two answers on each line; 2.6 is numbered 1-6 by tapping. In
2.1 item 5 the key allows I'm Sophia as well as It's, and so does this; in
3.7 item 3 (it rhymes with day) A is as right as J. 3.3 (letters the
teacher says) and the partner tasks are done in class.

    python3 handouts/b02c_digital.py            # writes handouts/b02c.json, lists every box
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

DOCX = ("~/Documents/Claude/Material Bank/General English/A1 Beginner/_NEW BOOKLET STYLE/"
        "B02C All about me — BOOKLET.docx")
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


def rows_as_lines(label, skip_header=True, joiner="  —  "):
    """A table of prompts and boxes as one line per row: each cell kept as it is."""
    a, b = table_after(label)
    rows = [re.findall(r"<td[^>]*>(.*?)</td>", r, re.S) for r in re.findall(r"<tr>(.*?)</tr>", h.html[a:b], re.S)]
    out = ""
    for row in rows[1:] if skip_header else rows:
        cells = [re.sub(r"</?p[^>]*>", "", c).strip() for c in row]
        out += '<p style="margin-bottom:8px">%s</p>' % joiner.join(c for c in cells if c)
    h.html = h.html[:a] + out + h.html[b:]


def people_rows(label, heads, count):
    """A survey table with nothing but boxes: one block per person."""
    a, b = table_after(label)
    tags = [t.group(0) for t in BLANK_TAG.finditer(h.html[a:b])]
    out = ""
    for k in range(count):
        mine = tags[k * len(heads):(k + 1) * len(heads)]
        out += ('<p style="margin-bottom:8px"><span style="font-weight:700">Person %d</span><br>%s</p>'
                % (k + 1, "<br>".join('<span style="color:#6E6E6E">%s</span> %s' % (html.escape(hd), t)
                                      for hd, t in zip(heads, mine))))
    h.html = h.html[:a] + out + h.html[b:]


def pairs_as_lines(label):
    """A four-column table - name, box, name, box - as one name a line."""
    a, b = table_after(label)
    rows = [re.findall(r"<td[^>]*>(.*?)</td>", r, re.S) for r in re.findall(r"<tr>(.*?)</tr>", h.html[a:b], re.S)]
    pairs = [(plain(r[k]), BLANK_TAG.search(r[k + 1])) for r in rows[1:] for k in (0, 2) if len(r) > k + 1]
    h.html = h.html[:a] + "".join('<p style="margin-bottom:8px">%s  %s</p>' % (html.escape(c), t.group(0))
                                  for c, t in sorted(pairs, key=lambda p: int(p[1].group(1)))) + h.html[b:]


def uzbek_after(containing, text):
    """An Uzbek line under a paragraph that is not an exercise's instruction."""
    at = h.html.index(containing)
    end = h.html.index("</p>", at) + len("</p>")
    h.html = h.html[:end] + '<p class="hx-uz" lang="uz">%s</p>' % told(text, bare=True) + h.html[end:]


# ------------------------------------------------------------ 1 Reading
h.item_box("1.5", 2, where="leader")
h.item_box("1.5", 3, where="leader")

# ------------------------------------------------------------ 2 Language
FORMS21 = {1: ["I'm", "It's"], 2: ["It's", "He's"], 3: ["They're", "It's"], 4: ["He's", "It's"], 5: ["It's", "I'm"]}
boxes_for("2.1", FORMS21)
rows_as_lines("2.2")
boxes_for("2.5", range(2, 7))                     # item 1 is the worked example
for q in range(43, 49):                            # 2.6: the line first, then its number
    h.html, moved = re.subn(re.escape(TAGS[q]) + r"(.*?)</p>", lambda m: m.group(1) + " " + TAGS[q] + "</p>",
                            h.html, count=1, flags=re.S)
    if not moved:
        raise SystemExit("2.6 box %d has moved" % q)
ANSWERS27 = halves("2.7", "a-d")

# ------------------------------------------------------------ 3 The alphabet
ODD32 = {1: ["A", "H", "E", "J"], 2: ["B", "C", "D", "L"], 3: ["F", "M", "N", "I"], 4: ["Q", "U", "W", "O"]}
boxes_for("3.2", ODD32)

# ------------------------------------------------------------ 4 Listening
TICK42 = [("Her surname", ["Tailor", "Taylor"]), ("Her address in London", ["Alpha Hotel", "Rita Hotel"]),
          ("Her phone number", ["07832 674893", "07532 647893"])]
a, b = table_after("4.2")
h.html = h.html[:a] + "".join(item_p("4.2", n, html.escape(what), "{{box:4.2:%d:60px:}}" % n, number=False)
                              for n, (what, _o) in enumerate(TICK42, 1)) + h.html[b:]
rows_as_lines("4.5", skip_header=False)

# ------------------------------------------------------------ 5 Everyday English
EMAILS52 = {1: "ali dot karimov at mailbox dot com", 2: "sophia underscore t at fastmail dot com",
            3: "j dash smith at workmail dot co dot uk", 4: "capital M then alik at post dot com"}
boxes_for("5.2", EMAILS52)
h.leaders("5.6", "CHECK BEFORE", [(20, W, "Write the conversation here")])
h.html = h.html.replace(TAGS[129], "", 1)         # the word count: the box counts them itself
FACES, CAN_DO = h.can_do_grid("5.7")
h.grid_rows("5.8")

# ------------------------------- every instruction, once more, in Uzbek
for label, text in [
        ("1.1", "Anketada nima boʻladi? Bilganlaringizni belgilang."),
        ("1.2", "Qaysi anketa? *1*, *2* yoki *3* ni tanlang."),
        ("1.3", "Toʻgʻri (*T*) mi yoki notoʻgʻri (*F*) mi?"),
        ("1.4", "Gaplarni matndagi soʻz bilan toʻldiring."),
        ("1.5", "Savollarga javob bering."),
        ("2.1", "Toʻgʻri javobni tanlang."),
        ("2.2", "Savolni yozing."),
        ("2.3", "Eng toʻgʻri gapni tanlang."),
        ("2.4", "Suhbatni toʻldiring."),
        ("2.5", "Xatoni topib, toʻgʻrilang. IKKITASI toʻgʻri — ular uchun *✓ It is correct* tugmasini bosing."),
        ("2.6", "Suhbatni tartib bilan raqamlang (1–6)."),
        ("2.7", "Savolni javob bilan moslang: harfni tanlang."),
        ("2.8", "Oʻzingizning javoblaringizni yozing. Har safar *It's* ishlating."),
        ("2.9", "Juftlikda ishlang. A oʻquvchi toʻrtala savolni beradi, B oʻquvchi javob beradi. Keyin almashing."),
        ("3.1", "Qaysi guruh? Tovushni tanlang."),
        ("3.2", "Bitta harf boshqa guruhda. Uni tanlang."),
        ("3.3", "Tinglang va eshitgan harfingizni yozing. Buni sinfda bajarasiz."),
        ("3.4", "Ismni yozing."),
        ("3.5", "Bularni sherigingizga ovoz chiqarib harflab ayting. Sherigingiz ularni yozadi."),
        ("3.6", "Soʻzni yozing."),
        ("3.7", "Qaysi harf? *E* yoki *I*, *G* yoki *J*, *A* yoki *R* ni tanlang."),
        ("3.8", "Imloni toʻgʻrilang."),
        ("3.9", "Sherigingiz bilan ishlang. Soʻzni harflab ayting. Sherigingiz uni yozib, aytadi."),
        ("4.1", "Bir marta tinglang. Ikki savolga javob bering."),
        ("4.2", "Yana tinglang. Toʻgʻri javobni tanlang."),
        ("4.3", "Yana bir marta tinglang va anketani toʻldiring."),
        ("4.4", "Qayta soʻrashga quloq soling. Ayol Sophiadan qaysi uchta narsani qayta aytishni soʻraydi?"),
        ("4.5", "Endi siz. Sherigingizdan soʻrang va anketani toʻldiring. Buni sinfda bajarasiz."),
        ("4.6", "Sherigingizning anketasini unga oʻqib bering. Toʻgʻri yozdingizmi?"),
        ("4.7", "Sophia nima deydi? Tinglaganingizdan toʻldiring."),
        ("5.1", "Sonni raqam bilan yozing."),
        ("5.2", "Email manzilni yozing."),
        ("5.3", "Bularni ovoz chiqarib ayting. Sherigingiz ularni yozib oladi."),
        ("5.4", "Tinglang. Ovoz koʻtariladimi (↗) yoki pasayadimi (↘)?"),
        ("5.5", "Anketani oʻzingiz haqingizdagi maʼlumot bilan toʻldiring."),
        ("5.6", "Endi suhbatni yozing. Sherigingizdan beshala narsani soʻrang (60–70 soʻz)."),
        ("5.7", "Butun darsni eslang. Har bir ish uchun qanchalik qila olishingizni tanlang."),
        ("5.8", "Sinf soʻrovi. Toʻrt kishidan soʻrang va maʼlumotlarini yozing. Buni sinfda bajarasiz."),
        ("5.9", "Sinfdan tashqarida. Bularni ingliz tilida topib, yozib qoʻying.")]:
    h.say_also(label, text)
uzbek_after(" do not answer the first time", "B oʻquvchi: birinchi marta javob bermang. *Sorry?* deng va sherigingiz "
            "qayta soʻrasin. Keyin javob bering.")
uzbek_after("So — your surname is", "Shunday deng: *So — your surname is …, you live at …, your number is … . Is that "
            "right?* Sherigingiz *Yes, that's right* yoki *No, sorry — it's …* deydi.")
uzbek_after("One thing I still want to practise:", "Hali ham mashq qilmoqchi boʻlgan bitta narsa:")
uzbek_after("  Read one row back to that person", "Keyin tekshiring. Bitta qatorni oʻsha odamga oʻqib bering. U *No, "
            "sorry* desa, siz uni qayta aytishga soʻramagansiz. Keyingi safar soʻrang.")

# ------------------------------------------ the explanations, told in Uzbek
h.goals([
    "*What's your surname / address / phone number / email address?* deb soʻrashni",
    "*It's* bilan javob berishni — har safar",
    "alifboni yettita tovush guruhida aytishni va ismingizni harflab aytishni",
    "telefon raqami va email manzilni ovoz chiqarib aytish va yozishni",
    "kimdandir qayta aytishni yoki harflab berishni soʻrashni",
    "pasayuvchi va koʻtariluvchi savol orasidagi farqni eshitishni",
])
h.retell("KEY WORDS", "KALIT SOʻZLAR", [
    "**a form**  anketa — savollar yozilgan qogʻoz",
    "**a surname**  familiya — oilangiz ismi",
    "**to spell**  harflab aytmoq — *T-A-Y-L-O-R*",
    "**a mistake**  xato — notoʻgʻri narsa",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — WHAT'S YOUR…?", [
    "**Savollarning hammasi bir xil shaklda.** *What's your* + *surname? / address? / phone number? / email "
    "address?* Toʻrt savol, bitta qolip. Qolipni oʻrgansangiz, toʻrttasini ham bilasiz.",
    "**Javob esa doim IT'S.** *I'm* emas, *He's* emas, *They're* emas. Maʼlumot — bu narsa, narsa esa *it*.",
    "[[✓]] *What's your surname? — It's Robinson. · What's your address? — It's 7 King Street.*",
    "[[✓]] *What's your phone number? — It's 0124 352738. · What's your email address? — It's chris@powermail.com.*",
    "**Telefon raqami koʻp sonlarga oʻxshaydi, lekin u BITTA raqam.** Shuning uchun *It's*, hech qachon *They're* "
    "emas. Manzil ham shunday: koʻp soʻz, lekin bitta manzil.",
])
h.retell("ERROR WARNING", "DIQQAT — KOʻP UCHRAYDIGAN XATOLAR", [
    "1 **I'M emas.** ✗ *What's your surname? — I'm Robinson.* → ✓ *It's Robinson.* *I'm* — siz haqingizda, "
    "ismingiz haqida emas.",
    "2 **THEY'RE emas.** ✗ *It's my phone number — they're 0124 352738.* → ✓ *It's 0124 352738.*",
    "3 **HE'S emas.** ✗ *What's your email address? — He's chris@…* → ✓ *It's chris@…*",
    "4 **HOW IS emas, WHAT'S deng.** ✗ *How is your name?* → ✓ *What's your name?* *how* ni faqat imlo uchun "
    "ishlating: *How do you spell that?*",
])
h.retell("WHEN YOU DON'T HEAR IT", "ESHITMAY QOLSANGIZ", [
    "*Sorry?* — eng qisqasi va eng foydalisi. Uni ovozingizni koʻtarib ayting.",
    "*Can you repeat that, please?* — hammasini qayta ayting.",
    "*How do you spell that? / Can you spell that? / Sorry, what's the spelling?* — ism uchun.",
    "*Sorry, more slowly, please.* — raqam uchun. *more slow* emas.",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — ALIFBO", [
    "Siz 26 ta harfni emas, 7 ta tovushni oʻrganasiz. Har bir harf yetti guruhdan biriga kiradi va guruh ichidagi "
    "harflar ohangdosh.",
    "/eɪ/ (*day* dagi kabi) *A H J K*",
    "/iː/ (*see* dagi kabi) *B C D E G P T V*",
    "/e/ (*ten* dagi kabi) *F L M N S X Z*",
    "/aɪ/ (*my* dagi kabi) *I Y* · /əʊ/ (*no* dagi kabi) *O*",
    "/uː/ (*you* dagi kabi) *Q U W* · /ɑː/ (*car* dagi kabi) *R*",
    "**Xavflilari har xil guruhda.** *E* va *I* · *G* va *J* · *A* va *R*. Har bir juftlikni hozir ikki marta ovoz "
    "chiqarib ayting.",
])
h.retell("DOUBLE LETTERS", "IKKILANGAN HARFLAR", [
    "Ikkita bir xil harf uchun *DOUBLE* deymiz. *Anna* — *A - double N - A*. · *Green Street* — *G - R - double E "
    "- N*.",
    "Har bir harfni aytsangiz ham boʻladi — *A - N - N - A* — hech kim qarshi emas. Lekin *double* ni eshitasiz, "
    "shuning uchun uni bilishingiz kerak.",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [
    "Sophia Londonda. U kvartira qidiryapti. U ofisda, bir ayol undan savollar soʻrab, javoblarni anketaga "
    "yozyapti.",
    "Agar sinfingizda audio boʻlsa, bu 2.20-trek. Boʻlmasa, oʻqituvchingiz matnni oʻqib beradi — topshiriqlar bir "
    "xil.",
])
h.retell("WHY YOU DIDN'T HEAR IT", "NEGA ESHITMADINGIZ?", [
    "**Hech kim telefon raqamini bitta uzun qator qilib aytmaydi.** U pauzali kichik guruhlarda keladi: *07532 … "
    "647 … 893*. Siz ham guruh-guruh qilib yozing va oraliq qoldiring.",
    "**Odamlar harflab aytganda ham toʻxtab-toʻxtab aytadi.** Uch-toʻrt harfdan keyin toʻxtashadi. Oʻsha "
    "toʻxtashlar — yozish imkoniyatingiz; oxirini kutmang.",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — RAQAMLAR, MANZILLAR", [
    "**Telefon raqamlari:** har bir raqamni alohida ayting. *0124 352738* — *oh - one - two - four …*, hech qachon "
    "*one hundred and twenty-four* emas.",
    "Telefon raqamida *0* — *OH*, *zero* ham, *nought* ham emas. · Ikkita bir xil raqam = *DOUBLE*. *55* — *double "
    "five*.",
    "**Email manzillar:** *@* — *AT*, *.* — *DOT*. *chris@powermail.com* — *chris at powermail dot com*.",
    "Belgilarning ham nomi bor. *_* — *underscore* · *-* — *dash* yoki *hyphen* · bosh harf — *capital A*.",
    "**Manzillar:** ingliz tilida raqam oldin keladi. *7 King Street*, *King Street 7* emas. Keyin shahar, keyin "
    "davlat.",
])
h.retell("PRONUNCIATION — THE VOICE AT THE END OF A QUESTION", "TALAFFUZ — SAVOL OXIRIDAGI OVOZ", [
    "**Soʻroq soʻzli savolda ovoz PASAYADI.** *What's your name?* ↘ · *How do you spell that?* ↘ *what* soʻzining "
    "oʻzi tinglovchiga bu savol ekanini aytadi, shuning uchun ovoz pasaya oladi.",
    "**Soʻroq soʻzi yoʻq savolda ovoz KOʻTARILADI.** *Is that right?* ↗ · *Sorry?* ↗ · *Taylor?* ↗ Bu yerda savol "
    "ekanini faqat ovoz bildiradi, shuning uchun u koʻtarilishi shart.",
    "**Bu bezak emas.** Pasayuvchi *Sorry.* — „kechirasiz“ degani. Koʻtariluvchi *Sorry?* — „qayta ayting“ degani. "
    "Bir soʻz, ikki maʼno — hammasini ovoz qiladi.",
])
h.retell("CHECK BEFORE YOU GIVE IT IN", "TOPSHIRISHDAN OLDIN TEKSHIRING", [
    "{box}  Har bir javob *It's* bilan boshlanadi — *I'm*, *He's* yoki *They're* yoʻq.",
    "{box}  *How is* emas, *What's* deb yozdim.   {box}  Bir marta harflab berishni soʻradim.",
    "{box}  Ismlar va koʻcha nomlari bosh harf bilan.   {box}  Soʻzlarni sanadim.",
])
h.one_per_line("TOPSHIRISHDAN OLDIN TEKSHIRING", None, at="box")

# ------------------------------------------------------------------ the key
K = {}
for n in range(1, 6):                             # what they know
    K[("1.1", n, 1)] = tick()
FORM = {"1": "Form 1", "2": "Form 2", "3": "Form 3"}
for n, a in enumerate("231321", 1):
    K[("1.2", n, 1)] = choose(["1", "2", "3"], a, labels=FORM)
TF = {"T": "T · true", "F": "F · false"}
for n, a in enumerate("TFFFTF", 1):
    K[("1.3", n, 1)] = choose(["T", "F"], a, labels=TF)
for n, a in enumerate(["surname", "form", "missing", "fast", "taxi"], 1):
    K[("1.4", n, 1)] = Q(a)
THREE = "say it slowly/spell it/read it again/say it slowly, spell it, read it again"
for k in (1, 2, 3):                               # the three things, in any order
    K[("1.5", 1, k)] = Q(THREE)
K[("1.5", 2, 1)] = own()
K[("1.5", 3, 1)] = pair()
for n in range(1, 6):
    K[("2.1", n, 1)] = choose(FORMS21[n], "It's/I'm" if n == 5 else "It's")
for n, a in enumerate(["What's your surname/What is your surname", "What's your address/What is your address",
                       "What's your phone number/What is your phone number/What's your number",
                       "What's your email address/What is your email address/What's your email"], 1):
    K[("2.2", n, 1)] = write(a)
PHRASES = ["Sorry?", "Can you repeat that, please?", "How do you spell that?", "Sorry, more slowly, please."]
for n, a in enumerate(["How do you spell that?/Can you repeat that, please?/Sorry?", "Sorry, more slowly, please.",
                       "How do you spell that?", "Sorry?/Can you repeat that, please?"], 1):
    K[("2.3", n, 1)] = choose(PHRASES, a)
for n, a in enumerate(["What's/What is", "It's/It is", "how", "spell", "what's/what is", "It's/It is", "Sorry",
                       "repeat", "What's/What is", "It's/It is"], 1):
    K[("2.4", n, 1)] = Q(a)
TICKED = "✓/correct/tick"
for n, a in zip(range(2, 7), [
        either("What's your name", "What is your name"),
        TICKED,
        either("It's 0124 352738", "What's your phone number? — It's 0124 352738", "It's"),
        TICKED,
        either("It's chris@powermail.com", "What's your email address? — It's chris@powermail.com", "It's")]):
    K[("2.5", n, 1)] = fix(a)
for n, a in enumerate("615243", 1):               # the lines as printed, in the order said
    K[("2.6", n, 1)] = choose(["1", "2", "3", "4", "5", "6"], a)
for n, a in enumerate("cabd", 1):
    K[("2.7", n, 1)] = choose(ANSWERS27, a)
for n in range(1, 5):                             # their own answers
    K[("2.8", n, 1)] = own(control=None)
SOUNDS = ["/eɪ/", "/iː/", "/e/", "/aɪ/", "/əʊ/", "/uː/", "/ɑː/"]
for n, a in enumerate(["/eɪ/", "/iː/", "/aɪ/", "/e/", "/uː/", "/ɑː/"], 1):
    K[("3.1", n, 1)] = choose(SOUNDS, a)
for n, a in {1: "E", 2: "L", 3: "I", 4: "O"}.items():
    K[("3.2", n, 1)] = choose(ODD32[n], a)
for n in range(1, 7):                             # letters the teacher says, in class
    K[("3.3", n, 1)] = pair()
for n, a in enumerate(["Beer", "Soon", "Kelly", "Lloyd"], 1):
    K[("3.4", n, 1)] = Q(a)
for n, a in enumerate(["phone", "address", "city", "email"], 1):
    K[("3.6", n, 1)] = Q(a)
LETTERS37 = ["E", "I", "G", "J", "A", "R"]
for n, a in enumerate(["E", "I", "J/A", "R"], 1):
    K[("3.7", n, 1)] = choose(LETTERS37, a)
for n, a in enumerate(["address", "email", "surname", "number"], 1):
    K[("3.8", n, 1)] = Q(a)
K[("4.1", 1, 1)] = choose(["Sophia", "the woman"], "the woman")
K[("4.1", 2, 1)] = choose(["a flat", "a house"], "a flat")
for n, (_what, options) in enumerate(TICK42, 1):
    K[("4.2", n, 1)] = choose(options, options[1])
for n, a in enumerate(["Sophia", "Taylor",
                       "Rita Hotel, Green Street/Rita Hotel/the Rita Hotel/the Rita Hotel, Green Street/"
                       "Rita Hotel Green Street",
                       "07532 647893/07532647893", "sophia.taylor@mailbox.com"], 1):
    K[("4.3", n, 1)] = Q(a)
AGAIN = {"yes": "✓ said again", "no": "✗ not"}
for n, a in enumerate(["no", "yes", "yes", "yes", "no", "no"], 1):
    K[("4.4", n, 1)] = choose(["yes", "no"], a, labels=AGAIN)
for n in range(1, 6):                             # a partner's form, in class
    K[("4.5", n, 1)] = pair()
K[("4.7", 1, 1)] = Q("Y/a Y")
K[("4.7", 2, 1)] = Q("Rita")
K[("4.7", 3, 1)] = own()
for n, a in enumerate(["07532", "441 06/44106", "901 123/901123", "0124 352/0124352"], 1):
    K[("5.1", n, 1)] = Q(a)
for n, a in enumerate(["ali.karimov@mailbox.com", "sophia_t@fastmail.com", "j-smith@workmail.co.uk",
                       "Malik@post.com"], 1):
    K[("5.2", n, 1)] = Q(a)
UD = {"up": "↗ up", "down": "↘ down"}
for n, a in enumerate(["down", "up", "up", "up", "down", "up"], 1):
    K[("5.4", n, 1)] = choose(["up", "down"], a, labels=UD)
for n in range(1, 7):                             # their own information
    K[("5.5", n, 1)] = own(control=None)
K[("5.6", 20, 1)] = own(control="essay")
for n in range(1, 6):                             # the checklist
    K[("5.6", n, 1)] = tick()
FACE_SAYS = dict(zip(FACES, ["🙂 Ha", "😐 Qisman", "🙁 Hali yoʻq"]))
for n in CAN_DO:
    K[("5.7", n, 1)] = choose(FACES, labels=FACE_SAYS)
K[("5.7", 19, 1)] = note()                        # one thing to practise: may stay empty
for n in range(1, 13):                            # the class survey
    K[("5.8", n, 1)] = pair()
for n in range(1, 4):                             # found outside class
    K[("5.9", n, 1)] = own(control=None)

if __name__ == "__main__":
    data = h.build(K, "Beginner", 2, "Unit 2C — All about me")
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "b02c.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
