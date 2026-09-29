"""B01ABC Hello - Azamat's Beginner booklet (1A, 1B and 1C), done on a phone.

His design is rendered as it is and this decides every box. The key is his
(B01ABC Hello - answer key), joined box by box by hand. The Desktop "new
design" copy is used; it splits into its five parts as it should.

As with Beginner 3B, every box that explains is told again in Uzbek, as
are the goals and every instruction; the English examples stay English, as
do the reading, the dialogues, the model and the exercises.

Put right here: the stress box had JAP-a-nese and CHI-nese; both are
stressed on -nese (ja-pa-NESE, chi-NESE), and 3.4 is marked that way. 3.6
items 1, 2 and 4 and all of 5.5 are about capital letters, which marking
cannot see, so the teacher reads them. Tables of boxes (the short answers in
2.5, the survey in 2.8, the countries in 3.1) are one line per row.

    python3 handouts/b01abc_digital.py            # writes handouts/b01abc.json, lists every box
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

DOCX = "~/Desktop/Handouts/A1 Beginner/B01ABC Hello/B01ABC Hello — handout (new design).docx"
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


# ------------------------------------------------------------ 2 Grammar
rows_as_lines("2.5")
boxes_for("2.6", range(2, 9))                     # item 1 is the worked example
people_rows("2.8", ["Name", "Country", "Student or teacher?"], 3)

# ------------------------------------------------------------ 3 Vocabulary
a, b = table_after("3.1")                         # one country a line
rows = [re.findall(r"<td[^>]*>(.*?)</td>", r, re.S) for r in re.findall(r"<tr>(.*?)</tr>", h.html[a:b], re.S)]
pairs = [(plain(r[k]), BLANK_TAG.search(r[k + 1])) for r in rows[1:] for k in (0, 2)]
h.html = h.html[:a] + "".join('<p style="margin-bottom:8px">%s  →  %s</p>' % (html.escape(c), t.group(0))
                              for c, t in sorted(pairs, key=lambda p: int(p[1].group(1)))) + h.html[b:]
WORDS32 = h.sort_words("3.2", ["American", "British", "Brazilian", "Chinese", "Italian", "Japanese", "Mexican",
                               "Spanish", "Turkish", "Australian"], "-AN")
SYLLABLES34 = {1: "a-mer-i-can", 2: "ja-pa-nese", 3: "span-ish", 4: "i-tal-ian", 5: "chi-nese", 6: "mex-i-can"}
for n in SYLLABLES34:
    h.item_box("3.4", n)                          # the strong syllable, after the count
ODD35 = {n: [w for w in ws if not w.startswith("(")] for n, ws in h.odd_one_out("3.5", why="Why?").items()}
boxes_for("3.6", range(1, 5), where="leader")

# ------------------------------------------------------------ 4 Listening
h.after_instruction("4.1", [(1, "", "120px", "")])
h.grid_rows("4.2")

# ------------------------------------------------------ 5 Everyday English
boxes_for("5.5", range(1, 7), where="leader")
boxes_for("5.7", (1, 2, 3), where="leader")
h.leaders("5.8", "CHECK BEFORE", [(20, W, "Write your profile here")])
h.html = h.html.replace(TAGS[161], "", 1)         # the word count: the box counts them itself

# ------------------------------- every instruction, once more, in Uzbek
for label, text in [
        ("1.1", "Soʻzlarga qarang. Keyin ismingiz va davlatingizni ayting."),
        ("1.2", "Bu kim? Ismni tanlang."),
        ("1.3", "Toʻgʻri (*T*) mi yoki notoʻgʻri (*F*) mi?"),
        ("1.4", "Gaplarni davlat nomi bilan toʻldiring."),
        ("1.5", "Suhbatlardan shu soʻzlarni toping."),
        ("1.6", "Endi siz. Sinfingiz haqidagi gaplarni toʻldiring."),
        ("2.1", "Qisqa shaklini yozing."),
        ("2.2", "*'m*, *'s* yoki *'re* ni tanlang."),
        ("2.3", "Gaplarni inkor shaklda yozing."),
        ("2.4", "Savol tuzing. Ikki soʻzning oʻrnini almashtiring."),
        ("2.5", "Qisqa javoblarni toʻldiring."),
        ("2.6", "Xatoni topib, toʻgʻrilang. IKKITA gap toʻgʻri — ular uchun *✓ It is correct* tugmasini bosing."),
        ("2.7", "Tinglang va ayting. Qisqa shaklmi yoki uzun shaklmi?"),
        ("2.8", "Uch kishidan soʻrang. Javoblarini yozing. Buni sinfda bajarasiz."),
        ("3.1", "Jadvalni toʻldiring: millatni yozing."),
        ("3.2", "Millatlarni toʻgʻri guruhga qoʻying."),
        ("3.3", "Gaplarni toʻldiring."),
        ("3.4", "Nechta boʻgʻin bor? Sonni tanlang, keyin kuchli boʻgʻinni tanlang."),
        ("3.5", "Boshqacha soʻzni tanlang. Nega u boshqacha?"),
        ("3.6", "Har bir gapdagi xatoni toʻgʻrilang. Bosh harflarga eʼtibor bering."),
        ("4.1", "Bir marta tinglang. Rasmda nechta odam bor?"),
        ("4.2", "Yana tinglang. Jadvalni toʻldiring."),
        ("4.3", "Yana bir marta tinglang. Qatorlarni toʻldiring."),
        ("4.4", "*This is* mi yoki *These are* mi? Tanlang."),
        ("4.5", "Har birini ikki marta ayting — avval sekin, keyin tez."),
        ("4.6", "*Who's*, *Who are*, *Where's* yoki *Where are* ni tanlang."),
        ("4.7", "Endi siz. Tanigan uchta odamingizni oʻylang. Sherigingizga aytib bering."),
        ("5.1", "Nima deysiz? Salomni tanlang."),
        ("5.2", "Suhbatni tartib bilan raqamlang: 1, 2 va 3."),
        ("5.3", "Ofisdagi suhbatni toʻldiring."),
        ("5.4", "Tinglang. Ovoz koʻtariladimi (↗) yoki bir tekis qoladimi (→)?"),
        ("5.5", "Bosh harflar va nuqtalarni qoʻyib, gapni qayta yozing."),
        ("5.6", "Namunaviy profilni oʻqing."),
        ("5.7", "Namuna haqidagi savollarga javob bering."),
        ("5.8", "Endi oʻz profilingizni yozing (40–50 soʻz).")]:
    h.say_also(label, text)

# ------------------------------------------ the explanations, told in Uzbek
h.goals([
    "ismingiz va davlatingizni aytishni",
    "*am*, *is* va *are* ni ishlatishni — oltala shaxs bitta jadvalda",
    "ikki odatiy xatosiz savol va qisqa javob tuzishni",
    "odamlar qayerdan ekanini aytishni, *this* va *these* ni ishlatishni",
    "yangi odamlar bilan tanishish va salomlashishni, qisqa profil yozishni",
])
h.retell("KEY WORDS", "KALIT SOʻZLAR", [
    "**a name**  ism — *Kenji, Dilnoza, Mr Brown*",
    "**a country**  davlat — *Japan, Spain, Italy*",
    "**a student**  talaba, oʻquvchi — sinfdagi odam",
    "**a teacher**  oʻqituvchi — oldinda turgan odam",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — BE FEʼLI", [
    "Ingliz tilida birinchi kerak boʻladigan juda kichik bitta feʼl bor. Bu — *be* (boʻlmoq). Mana u olti marta:",
    "[[+]] *I'm Kenji. · You're a student. · We're in Room 3. · He's from Italy. · She's from Spain. · They're "
    "from Brazil.*",
    "[[−]] *I'm not a teacher. · You aren't late. · We aren't from one country. · He isn't British. · She isn't "
    "Italian. · They aren't here.*",
    "[[?]] *Are you from Japan? · Is he Italian? · Is she from Spain? · Are they students? · Am I right?*",
    "[[✓ ✗]] *Yes, I am. / No, I'm not. · Yes, he is. / No, he isn't. · Yes, they are. / No, they aren't.*",
    "**Savolda BE oldinga chiqadi.** *You are from Spain* — bu darak gap. *Are you from Spain?* — bu savol. Ikki "
    "soʻz oʻrin almashadi. Butun qoida shu.",
])
h.retell("ERROR WARNING", "DIQQAT — KOʻP UCHRAYDIGAN XATOLAR", [
    "1 **Savol — bu soʻroq belgili darak gap emas.** ✗ *You are from Spain?* → ✓ *Are you from Spain?*",
    "2 **HA javobida qisqa shakl yoʻq.** ✗ *Yes, I'm.* → ✓ *Yes, I am.* Lekin *No, I'm not* toʻgʻri. „Ha“ — "
    "uzun, „yoʻq“ — qisqa.",
    "3 **Feʼlni tushirib qoldirmang.** ✗ *He from Italy.* → ✓ *He's from Italy.* Har bir inglizcha gapga feʼl "
    "kerak, bu yerda esa feʼl — kichkina *'s*.",
    "4 **Shaxsni tushirib qoldirmang.** ✗ *Is Japanese?* → ✓ *Is he Japanese?* Ingliz tilida doim kim ekani "
    "aytiladi.",
    "**Ikki xil, ikkalasi ham toʻgʻri:** *He isn't British = He's not British. · We aren't late = We're not late.*",
])
h.retell("PRONUNCIATION", "TALAFFUZ — QISQA SHAKLLAR", [
    "Uzun shaklni deyarli hech qachon aytmaymiz. Birinchi kundanoq qisqasini ayting — inglizchangiz toʻgʻri "
    "eshitiladi.",
    "*I am → I'm* /aɪm/ · *we are → we're* /wɪə/ · *he is → he's* /hiːz/ · *she is → she's* /ʃiːz/ · *they are → "
    "they're* /ðeə/",
    "**Bitta istisno.** *Yes, I am* da uzun shakl qaytadi va *am* baland aytiladi. Shuning uchun *Yes, I'm* "
    "ingliz qulogʻiga notoʻgʻri eshitiladi — oxirida aytadigan hech narsa qolmaydi.",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — DAVLATLAR VA MILLATLAR", [
    "Oʻnta davlat: *Japan · China · Spain · Italy · Turkey · Brazil · Mexico · Australia · the UK (the United "
    "Kingdom) · the USA (the United States)*",
    "**Ikkita davlat THE oladi.** *I'm from the UK* va *I'm from the USA* deysiz, lekin *I'm from Japan* — *the* "
    "yoʻq. Bu roʻyxatda faqat shu ikkitasi.",
    "**Davlat — joy. Millat — odam.** *Japan* — davlat. *Japanese* — odam yoki til. *I'm from Japan = I'm "
    "Japanese.*",
    "**Doim bosh harf.** *japan* va *japanese* — notoʻgʻri. Davlat va millat nomlari gapning qayerida boʻlmasin, "
    "bosh harf bilan boshlanadi.",
])
h.retell("THREE ENDINGS", "UCHTA QOʻSHIMCHA", [
    "Millatlar qiyin emas. Uchta qoʻshimcha bor, koʻp davlatlar birinchisini oladi.",
    "[[-AN]] *Italy → Italian · Brazil → Brazilian · Mexico → Mexican · Australia → Australian · the USA → "
    "American*",
    "[[-ISH]] *Spain → Spanish · Turkey → Turkish · the UK → British*",
    "[[-ESE]] *Japan → Japanese · China → Chinese*",
    "**the UK va the USA bilan ehtiyot boʻling.** Millati — *British* va *American*; bu soʻzlar davlat nomiga "
    "umuman oʻxshamaydi. Bu ikkisini alohida yodlang.",
])
h.retell("PRONUNCIATION — SYLLABLES AND STRESS", "TALAFFUZ — BOʻGʻIN VA URGʻU", [
    "Soʻzni qarsak chalib ayting. Har bir qarsak — bitta boʻgʻin. Bitta qarsak kuchliroq — bu urgʻu.",
    "2 qarsak: *SPA-nish · BRIT-ish · TURK-ish · chi-NESE*",
    "3 qarsak: *i-TAL-ian · ja-pa-NESE · MEX-i-can · aus-TRAL-ian*",
    "4 qarsak: *a-MER-i-can · bra-ZIL-ian*",
    "**-ISH soʻzlariga qarang:** ularning hammasida urgʻu birinchi boʻgʻinda. *-IAN* soʻzlarida hech qachon "
    "birinchida emas. *-ESE* esa urgʻuni doim oʻziga oladi: *chi-NESE, ja-pa-NESE*.",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [
    "Nilufarning telefonida rasm bor. U ingliz tili sinfidan. Sam unga qarab, odamlar haqida soʻraydi.",
    "Beshta ismni eshitasiz: *Kenji, Elena, Marco, Amy* va *Mr Brown*.",
])
h.retell("THIS AND THESE", "THIS VA THESE", [
    "**THIS** = bitta. *This is Kenji. · This is my teacher. · This is my phone.*",
    "**THESE** = ikkita yoki koʻproq. *These are my friends Elena and Marco. · These are my books.*",
    "**Feʼlga qarang.** *This is …*, lekin *These are …* . Feʼl har safar oldidagi soʻzga qarab oʻzgaradi.",
])
h.retell("WHY YOU DIDN'T HEAR IT", "NEGA ESHITMADINGIZ?", [
    "**Kichik soʻzlar yoʻqolib ketadi.** *This is* bitta soʻzdek eshitiladi — /ðɪsɪz/. *These are* — /ðiːzə/. "
    "Hech kim oʻrtada toʻxtamaydi.",
    "**Choʻziq II ga quloq soling.** *these* da choʻziq /iː/, *this* da qisqa /ɪ/ bor. Bir odammi yoki "
    "ikkitami — shu bitta tovush aytib beradi.",
])
h.retell("TWO QUESTIONS YOU WILL NEED EVERY DAY", "HAR KUNI KERAK BOʻLADIGAN IKKI SAVOL", [
    "**WHO** — odam haqida soʻraydi. *Who's he? · Who's she? · Who are they?*",
    "**WHERE** — joy haqida soʻraydi. *Where's he from? · Where are they from?*",
    "*Who is → who's* va *Where is → where's*. *he's* dagi *'s* ning oʻzi — lekin bu yerda u odamni emas, *is* "
    "ni bildiradi.",
])
h.retell("SAYING HELLO", "SALOMLASHISH", [
    "**Istalgan vaqtda:** *Hi.* (doʻstlarga) · *Hello.* (hammaga)",
    "*7am – 12pm → Good morning. · 12pm – 5pm → Good afternoon. · 5pm – 10pm → Good evening.*",
    "**Ehtiyot boʻling:** *Good night* — salom emas. Uni ketayotganda yoki uxlashdan oldin aytasiz.",
])
h.retell("MEETING A NEW PERSON", "YANGI ODAM BILAN TANISHISH", [
    "Uchta qator. Ular har doim bir xil, shuning uchun ularni birga oʻrganing.",
    "[[A]] *Sophia, this is Megan Jackson.*",
    "[[B]] *Nice to meet you, Megan.*",
    "[[C]] *Nice to meet you too, Sophia.*",
    "**Hammasini TOO soʻzi qiladi.** Ikkinchi odam rozi boʻlgani uchun *too* qoʻshadi. Usiz javob sovuq "
    "eshitiladi.",
])
h.retell("PRONUNCIATION — UP OR FLAT?", "TALAFFUZ — KOʻTARILADIMI YOKI TEKISMI?", [
    "Savol oxirida ovozingiz koʻtariladi, javob oxirida esa bir tekis qoladi. Bu — ohang, ingliz tili qoʻshimcha "
    "soʻzlar oʻrniga shuni ishlatadi.",
    "**Koʻtariladi:** *How are you?* ↗ · *Are you OK?* ↗",
    "**Tekis:** *Hello.* → · *I'm good.* → · *Thank you.* → · *Nice to meet you.* →",
    "Savolni tekis ohangda aytsangiz, odamlar uni darak gap deb eshitadi va javob bermaydi. Ikkala usulda aytib, "
    "farqini eshiting.",
])
h.retell("CAPITAL LETTERS AND FULL STOPS", "BOSH HARFLAR VA NUQTALAR", [
    "**Bosh harf (A, B, C) ishlating:**",
    "· ismlar uchun — *Sophia Taylor, Mr Brown* · joylar uchun — *London, Japan, High Street*",
    "· millatlar uchun — *Italian, British* · gap boshida — *My name's …*",
    "· *I* soʻzi uchun — gapning qayerida boʻlmasin, doim",
    "Gap oxirida nuqta ( . ) qoʻying.",
])
h.retell("CHECK BEFORE YOU GIVE IT IN", "TOPSHIRISHDAN OLDIN TEKSHIRING", [
    "{box}  Har bir gap bosh harf bilan boshlanadi.   {box}  Har bir gap nuqta bilan tugaydi.",
    "{box}  Ismlar, joylar va millatlar bosh harf bilan.   {box}  *I* soʻzi hamma joyda bosh harf.",
    "{box}  Har bir gapda *am*, *is* yoki *are* bor.   {box}  Soʻzlarni sanadim.",
])
h.one_per_line("TOPSHIRISHDAN OLDIN TEKSHIRING", None, at="box")

# ------------------------------------------------------------------ the key
K = {}
K[("1.1", 1, 1)] = own(control=None)              # their name
K[("1.1", 2, 1)] = own(control=None)              # their country
NAMES = ["Kenji", "Elena", "Marco", "Tom", "Dilnoza", "Mr Brown", "Amy and Sofia"]
for n, a in enumerate(["Kenji", "Elena", "Tom", "Dilnoza", "Mr Brown", "Amy and Sofia"], 1):
    K[("1.2", n, 1)] = choose(NAMES, a)
TF = {"T": "T · true", "F": "F · false"}
for n, a in enumerate("TFFTTF", 1):
    K[("1.3", n, 1)] = choose(["T", "F"], a, labels=TF)
for n, a in enumerate(["Japan", "Italy", "Spain", "Uzbekistan", "Brazil",
                       "the UK/London/UK/the United Kingdom/England"], 1):
    K[("1.4", n, 1)] = Q(a)
for n, a in enumerate(["Hi, Hello/Hi Hello/Hello, Hi/Hello Hi/Hi and Hello/Hello and Hi/Hi / Hello/Hi/Hello",
                       "It's OK/It's ok/It is OK", "Nice to meet you", "Thank you/Thanks"], 1):
    K[("1.5", n, 1)] = Q(a)
for n in range(1, 5):                             # about their own class
    K[("1.6", n, 1)] = own(control=None)
for n, a in enumerate(["I'm", "he's", "she's", "they're", "we're", "you're", "he isn't/he's not", "I'm not"], 1):
    K[("2.1", n, 1)] = Q(a)
for n, a in enumerate(["'m", "'s", "'re", "'re", "'re", "'s"], 1):
    K[("2.2", n, 1)] = choose(["'m", "'s", "'re"], a)
for n, a in enumerate(["He isn't British/He's not British", "They aren't from Italy/They're not from Italy",
                       "I'm not a teacher", "We aren't late/We're not late", "She isn't from Japan/She's not from Japan",
                       "You aren't in Room 4/You're not in Room 4"], 1):
    K[("2.3", n, 1)] = write(a)
for n, a in enumerate(["Are you from Spain", "Is he a student", "Are they from Brazil", "Is she your teacher",
                       "Are we in Room 3"], 1):
    K[("2.4", n, 1)] = write(a)
for n, a in enumerate(["I am", "he isn't/he's not/he is not", "they are", "she isn't/she's not/she is not",
                       "I'm not/I am not"], 1):
    K[("2.5", n, 1)] = Q(a)
TICKED = "✓/correct/tick"
for n, a in zip(range(2, 9), [
        "Yes, I am",
        either("He's from Japan", "He is from Japan"),
        either("Is he Japanese", "Is she Japanese"),
        TICKED,
        either("She isn't Spanish", "She's not Spanish", "She is not Spanish"),
        TICKED,
        either("They are from Brazil", "They're from Brazil")]):
    K[("2.6", n, 1)] = fix(a)
SL = {"short": "short form", "long": "long form"}
for n, a in enumerate(["short", "long", "short", "short"], 1):
    K[("2.7", n, 1)] = choose(["short", "long"], a, labels=SL)
for n in range(1, 10):                            # the survey, in class
    K[("2.8", n, 1)] = pair()
for n, a in enumerate(["Japanese", "Brazilian", "Spanish", "Mexican", "Italian", "Turkish", "Chinese", "Australian",
                       "British", "American"], 1):
    K[("3.1", n, 1)] = Q(a)
GROUP32 = {"an": "-AN", "ish": "-ISH", "ese": "-ESE"}
for n, w in enumerate(WORDS32, 1):
    K[("3.2", n, 1)] = choose(["an", "ish", "ese"], "ese" if w.endswith("ese") else "ish" if w.endswith("ish") else "an",
                              labels=GROUP32)
for n, a in enumerate(["Japanese", "Spanish", "Brazilian", "British", "American"], 1):
    K[("3.3", n, 1)] = Q(a)
K[("3.3", 6, 1)] = own(control=None)
K[("3.3", 6, 2)] = own(control=None)
STRONG = {1: "mer", 2: "nese", 3: "span", 4: "tal", 5: "nese", 6: "mex"}
for n, word in SYLLABLES34.items():
    parts = word.split("-")
    K[("3.4", n, 1)] = choose(["1", "2", "3", "4"], str(len(parts)))
    K[("3.4", n, 2)] = choose(parts, STRONG[n])
for n, a in {1: "Spanish", 2: "Brazilian", 3: "Mexico", 4: "Mexican"}.items():
    K[("3.5", n, 1)] = choose(ODD35[n], a)
    K[("3.5", n, 2)] = own()
K[("3.6", 1, 1)] = own()                          # capital letters: the teacher reads them
K[("3.6", 2, 1)] = own()
K[("3.6", 3, 1)] = write("He's from Japan/He is from Japan/Japan")
K[("3.6", 4, 1)] = own()
K[("4.1", 1, 1)] = Q("Four/4/four people/4 people")
for n, a in enumerate(["Japan", "student/a student", "Spain", "student/a student", "Italy", "student/a student",
                       "the UK/UK/Britain/England/the United Kingdom", "teacher/a teacher"], 1):
    K[("4.2", n, 1)] = Q(a)
for key, a in (((1, 1), "Who's/Who is"), ((1, 2), "That's/This is/It's/That is/It is"), ((2, 1), "Is"),
               ((2, 2), "he isn't/he's not/he is not"), ((3, 1), "these"), ((4, 1), "Are"), ((4, 2), "they are"),
               ((5, 1), "isn't/is not"), ((5, 2), "He's/He is")):
    K[("4.3",) + key] = Q(a)
for n, a in enumerate(["This is", "These are", "This is", "These are", "This is", "These are"], 1):
    K[("4.4", n, 1)] = choose(["This is", "These are"], a)
WH = ["Who's", "Who are", "Where's", "Where are"]
for n, a in enumerate(["Who's", "Where's", "Who are", "Where are", "Who's", "Where are"], 1):
    K[("4.6", n, 1)] = choose(WH, a)
K[("4.6", 6, 2)] = own(control=None)              # where they are from
for n in range(1, 4):                             # three people they know
    K[("4.7", n, 1)] = own(control=None)
HELLO = ["Good morning", "Good afternoon", "Good evening", "Good night", "Hi"]
for n, a in enumerate(["Good morning", "Good afternoon", "Good evening", "Hi"], 1):
    K[("5.1", n, 1)] = choose(HELLO, a)
for n, a in enumerate("321", 1):                  # Megan, Sophia, David: David speaks first
    K[("5.2", n, 1)] = choose(["1", "2", "3"], a)
for n, a in enumerate(["morning", "Hello/Hi/Good morning", "Are", "am", "This", "meet", "too"], 1):
    K[("5.3", n, 1)] = Q(a)
UF = {"up": "↗ up", "flat": "→ flat"}
for n, a in enumerate(["flat", "up", "flat", "flat", "up", "flat"], 1):
    K[("5.4", n, 1)] = choose(["up", "flat"], a, labels=UF)
for n in range(1, 7):                             # capital letters and full stops: the teacher reads them
    K[("5.5", n, 1)] = own()
K[("5.7", 1, 1)] = Q("Six/6/six sentences")
K[("5.7", 2, 1)] = own()
K[("5.7", 3, 1)] = own()
K[("5.8", 20, 1)] = own(control="essay")
for n in range(1, 7):                             # the checklist
    K[("5.8", n, 1)] = tick()

if __name__ == "__main__":
    data = h.build(K, "Beginner", 1, "Unit 1A, 1B & 1C — Hello!")
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "b01abc.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
