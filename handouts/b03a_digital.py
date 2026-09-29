"""B03A Food and drink - Azamat's Beginner booklet (3A), done on a phone.

His design is rendered as it is and this decides every box. The key is his
(B03A Food and drink - ANSWER KEY), joined box by box by hand. This is the
Material Bank copy (_NEW BOOKLET STYLE), the fuller "grammar-weighted"
edition; it splits into its five parts as it should.

As with the other Beginner booklets, every box that explains is told again
in Uzbek, as are the goals and every instruction; the English examples stay
English, as do the reading and the exercises.

Put right here: 3.9 says TWO sentences are correct; four are (4, 6, 7 and 8,
as the key itself says): it says FOUR. In 4.6, where the key wants a number
before eggs and some before vegetables, some and a number both count for
those two lines - both are good English. 3.3 is a tap between a and b on
each line; 3.4's adverbs are the student's own, so any of the four counts.
4.4 (words the teacher says) and the partner tables are done in class; 3.7 is one
tap a habit for the partner's answer.

    python3 handouts/b03a_digital.py            # writes handouts/b03a.json, lists every box
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
        "B03A Food and drink — BOOKLET.docx")
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
h.leaders("1.6", "1.7  </span>", [(1, W, "Three sentences about one family")])

# ------------------------------------------------------------ 2 Grammar 1
rows_as_lines("2.3")
boxes_for("2.5", range(2, 9))                     # item 1 is the worked example
h.grid_rows("2.6")
h.leaders("2.9", "3.1  </span>", [(1, W, "Three true sentences and one false one")])

# ------------------------------------------------------------ 3 Grammar 2
a, b = table_after("3.3")                         # a and b on one line each, then the tap
rows = [[plain(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)]
        for r in re.findall(r"<tr>(.*?)</tr>", h.html[a:b], re.S)]
h.html = h.html[:a] + "".join(
    item_p("3.3", int(r[0]), "<b>a</b> %s<br><b>b</b> %s<br>" % (html.escape(r[1]), html.escape(r[2])),
           "{{box:3.3:%s:60px:}}" % r[0]) for r in rows if r and r[0].isdigit()) + h.html[b:]
reword("3.9", "Find and correct the mistake. TWO sentences are correct — tick them.",
       "Find and correct the mistake. FOUR sentences are correct — tick them.")
boxes_for("3.9", range(2, 9))                     # item 1 is the worked example
HABITS37 = ["eat breakfast", "eat fish", "drink coffee", "eat vegetables"]
a, b = table_after("3.7")                         # one tap a habit: how often your partner does it
h.html = h.html[:a] + "".join(item_p("3.7", n, html.escape(w), "{{box:3.7:%d:60px:}}" % n)
                              for n, w in enumerate(HABITS37, 1)) + h.html[b:]

# ------------------------------------------------------------ 4 Vocabulary
WORDS43 = h.sort_words("4.3", ["big", "eat", "nine", "sister", "it's", "me", "china", "five", "his", "teacher", "hi",
                               "milk"], "/iː/")
ODD47 = h.odd_one_out("4.7", why="Why is it different?")

# ------------------------------------------------------------ 5 Listening
h.grid_rows("5.4")
h.leaders("5.5", "CHECK BEFORE", [(20, W, "Write about your week here")])
h.html = h.html.replace(TAGS[181], "", 1)         # the word count: the box counts them itself
FACES, CAN_DO = h.can_do_grid("5.6")

# ------------------------------- every instruction, once more, in Uzbek
for label, text in [
        ("1.1", "Har hafta qanday ovqatlar yeysiz? Belgilang."),
        ("1.2", "Qaysi oila? *A*, *B* yoki *C* ni tanlang."),
        ("1.3", "Toʻgʻri (*T*) mi yoki notoʻgʻri (*F*) mi?"),
        ("1.4", "Gaplarni matndagi soʻz bilan toʻldiring."),
        ("1.5", "Endi siz. Gaplarni toʻldiring."),
        ("1.6", "Matndagi bitta oila haqida uchta gap yozing."),
        ("1.7", "Qaysi oila sizning oilangizga eng yaqin? Sherigingizga nega ekanini ayting."),
        ("2.1", "Feʼlni toʻgʻri shaklda yozing."),
        ("2.2", "*Do* bilan savol tuzing."),
        ("2.3", "Qisqa javoblarni toʻldiring."),
        ("2.4", "Suhbatni toʻldiring."),
        ("2.5", "Xatoni topib, toʻgʻrilang. IKKITA gap toʻgʻri — ular uchun *✓ It is correct* tugmasini bosing."),
        ("2.6", "Uch kishidan soʻrang. *✓* yoki *✗* yozing. Buni sinfda bajarasiz."),
        ("2.7", "Tinglang va ayting. Tasdiq (+) mi yoki inkor (−) mi?"),
        ("2.8", "Gapni inkor shaklda yozing."),
        ("2.9", "Oʻzingiz haqingizda uchta rost va bitta yolgʻon gap yozing."),
        ("3.1", "Soʻzlarni 100% dan 0% gacha tartib bilan joylang."),
        ("3.2", "Ravishni toʻgʻri joyga qoʻyib, gapni toʻliq yozing."),
        ("3.3", "Qaysi gap toʻgʻri — *a* mi yoki *b* mi?"),
        ("3.4", "Siz uchun toʻgʻri boʻlgan ravishni tanlang."),
        ("3.5", "Gapni *Sometimes* bilan boshlab qayta yozing."),
        ("3.6", "Gapni *never* bilan inkor qiling."),
        ("3.7", "Sherigingizdan soʻrang. Keyin u haqida ikkita gap yozing. Buni sinfda bajarasiz."),
        ("3.8", "Soʻzlarni tartib bilan yozib, gap tuzing."),
        ("3.9", "Xatoni topib, toʻgʻrilang. TOʻRTTA gap toʻgʻri — ular uchun *✓ It is correct* tugmasini bosing."),
        ("4.1", "Ovqat nomini yozing."),
        ("4.2", "Sanaladimi (*C*) yoki sanalmaydimi (*N*)?"),
        ("4.3", "Har bir soʻzning tovush guruhini tanlang."),
        ("4.4", "Qaysi birini eshityapsiz? Belgilang. Buni sinfda bajarasiz."),
        ("4.5", "Yoqtiradigan ikkita va yoqtirmaydigan ikkita narsani ayting."),
        ("4.6", "*some* yoki son bilan toʻldiring."),
        ("4.7", "Qaysi soʻz boshqacha? Uni tanlang va nega ekanini yozing."),
        ("5.1", "Bir marta tinglang. Rajit yeydigan ovqatlarni belgilang: *✓* yoki *✗*."),
        ("5.2", "Yana tinglang. Qanchalik tez-tez? *always*, *usually*, *sometimes* yoki *never* ni tanlang."),
        ("5.3", "Yana bir marta tinglang. Toʻgʻri (*T*) mi yoki notoʻgʻri (*F*) mi?"),
        ("5.4", "Endi siz. Sherigingizdan soʻrang va jadvalni toʻldiring. Sherigingiz ustunini sinfda toʻldirasiz."),
        ("5.5", "Haftangiz haqida yozing (50–60 soʻz). Toʻrtta chastota ravishini ishlating."),
        ("5.6", "Butun darsni eslang. Har bir ish uchun qanchalik qila olishingizni tanlang.")]:
    h.say_also(label, text)
uzbek_after("Your partner reads them and says", "Sherigingiz ularni oʻqib, qaysi biri yolgʻon ekanini aytadi.")
uzbek_after("Then report:", "Keyin sinfga aytib bering: *Dilnoza always has breakfast, but she never eats fish. I "
            "sometimes eat fish.*")

# ------------------------------------------ the explanations, told in Uzbek
h.goals([
    "nima yeyishingiz va nima yemasligingizni aytishni",
    "*Do you like…?* deb soʻrashni va *Yes, I do / No, I don't* deb javob berishni",
    "*always, usually, sometimes, never* ni toʻgʻri joyga qoʻyishni — feʼldan oldin, *be* dan keyin",
    "*never* ni *don't* qoʻshmasdan ishlatishni",
    "yetti xil ovqatni nomlashni va qaysilarining koʻpligi yoʻqligini aytishni",
    "/iː/, /ɪ/ va /aɪ/ orasidagi farqni eshitishni",
])
h.retell("KEY WORDS", "KALIT SOʻZLAR", [
    "**every day**  har kuni — hamma kunlar",
    "**a lot of**  koʻp — katta miqdor",
    "**a vegetarian**  goʻsht yemaydigan odam",
    "**the same**  bir xil — farqi yoʻq",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — PRESENT SIMPLE: I, YOU, WE, THEY", [
    "Bu zamon doim toʻgʻri boʻlgan yoki qayta-qayta boʻladigan narsalar uchun. Hozir emas — odatda. *I eat rice. · "
    "We drink tea. · They like fish.*",
    "[[+]] **Feʼl oʻzgarmaydi.** *I eat meat. · You eat meat. · We eat meat. · They eat meat.* Toʻrt shaxs uchun "
    "bitta shakl — bu oson qismi.",
    "[[−]] ***DON'T* + feʼl ishlating.** *I don't eat fish. · They don't like bread.* *don't* dan keyingi feʼl hech "
    "qachon oʻzgarmaydi va *-s* olmaydi.",
    "[[?]] ***DO* + shaxs + feʼl ishlating.** *Do you like fish? · Do they eat meat?* *do* oldinga chiqadi, feʼl "
    "esa oʻzgarmaydi.",
    "[[✓ ✗]] **Qisqa javoblar.** *Yes, I do. / No, I don't. · Yes, they do. / No, they don't.* Hech qachon *Yes, "
    "I like.*",
    "**2-boʻlim bilan solishtiring.** *Do you have a phone?* va *Do you like fish?* bir xil tuzilgan. *DO* + shaxs "
    "+ feʼl qolipini bilsangiz, u ingliz tilidagi *be* dan boshqa hamma feʼlga ishlaydi.",
])
h.retell("ERROR WARNING", "DIQQAT — KOʻP UCHRAYDIGAN XATOLAR", [
    "1 **I, you, we, they bilan -s yoʻq.** ✗ *I eats rice.* ✗ *They likes fish.* → ✓ *I eat rice. They like fish.* "
    "*-s* *he, she* va *it* ga tegishli — uni keyinroq oʻrganasiz.",
    "2 **Savolga DO kerak.** ✗ *You like fish?* ✗ *Like you fish?* → ✓ *Do you like fish?*",
    "3 **Inkorga NO emas, DON'T kerak.** ✗ *I no eat fish.* ✗ *I not eat fish.* → ✓ *I don't eat fish.*",
    "4 **Qisqa javob DO bilan.** ✗ *Yes, I like.* ✗ *Yes, I am.* → ✓ *Yes, I do.* Savolda *Do…?* bor edi, "
    "demak javobda *do*.",
])
h.retell("PRONUNCIATION — DO YOU DISAPPEARS AGAIN", "TALAFFUZ — DO YOU YANA YOʻQOLADI", [
    "*Do you* → /dʒə/. *Do you like fish?* → /dʒə laɪk fɪʃ/. Savolda grammatika eng jim qism, feʼl esa eng baland.",
    "**Lekin DON'T baland.** *I don't eat fish.* — inkor urgʻu oladi, chunki u yangilik. *don't* ni eshitmasangiz, "
    "gap odatda tasdiq boʻlgan.",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — ALWAYS, USUALLY, SOMETIMES, NEVER", [
    "Bu soʻzlar QANCHALIK TEZ-TEZ ekanini aytadi. Ularni „har doim“ dan „hech qachon“ gacha chiziqqa qoʻying.",
    "*always* (100%) → *usually* (koʻp kunlari) → *sometimes* (baʼzi kunlari) → *never* (0%)",
    "[[QAYERDA]] **Asosiy feʼldan oldin.** *We always have breakfast at seven. · I usually have a sandwich for "
    "lunch. · We sometimes eat fish for dinner. · I never eat cake.*",
    "[[LEKIN]] **BE feʼlidan keyin.** *I'm always late. · They're never hungry in the morning. · She's usually at "
    "home.* *be* bilan ravish oldin emas, keyin keladi. Bu yagona istisno, va u hammani adashtiradi.",
    "[[YANA]] **SOMETIMES gapni boshlashi ham mumkin.** *We sometimes eat fish for dinner. = Sometimes we eat fish "
    "for dinner.* Ikkalasi ham toʻgʻri. *Always* va *never* bunday qila olmaydi.",
    "**Va NEVER ning oʻzi inkor.** *I never eat cake* — bu inkor gap. *don't* qoʻshmang: ✗ *I don't never eat "
    "cake.* Ingliz tilida bir gapda bitta inkor.",
])
h.retell("ERROR WARNING", "DIQQAT — RAVISH QAYERDA TURADI", [
    "1 **Asosiy feʼldan keyin emas.** ✗ *I eat always breakfast.* → ✓ *I always eat breakfast.* Ravish feʼlning "
    "orqasida emas, oldida turadi.",
    "2 **BE dan oldin emas.** ✗ *I always am late.* → ✓ *I'm always late.* Oddiy feʼl → oldin. *Be* → keyin.",
    "3 **Ikki inkor yoʻq.** ✗ *I don't never eat fish.* → ✓ *I never eat fish.*",
    "4 **ALWAYS va NEVER gap boshida kelmaydi.** ✗ *Never I eat cake.* ✗ *Always we have breakfast.* → ✓ *I never "
    "eat cake. We always have breakfast.* Faqat *sometimes* va *usually* oldinga chiqa oladi.",
    "5 **Savolda u shaxsdan keyin keladi.** *Do you always have breakfast?* · ✗ *Do always you have breakfast?*",
])
h.retell("REMEMBER THE TWO POSITIONS", "IKKI JOYNI ESLANG", [
    "**Oddiy feʼl → ravish uning OLDIDA.** *I always eat · We never drink · They sometimes have*",
    "**BE feʼli → ravish uning KEYINIDA.** *I'm always · We're never · She's sometimes*",
    "**Bitta tekshiruv.** Gapni ravishsiz ayting. Qolgan yagona feʼl *am*, *is* yoki *are* boʻlsa, ravish undan "
    "keyin keladi. Qolgan hamma holatda — oldin.",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — OVQATLAR", [
    "**Ovqatlar 1:** *fruit · rice · meat · bread · vegetables · eggs · fish*",
    "**Soʻz urgʻusi.** Yettitadan oltitasi bir boʻgʻinli, tanlaydigan narsa yoʻq. Faqat *vegetables* uzunroq — unda "
    "yozilishda toʻrtta boʻgʻin bor, lekin aytilishda uchta: *VEJ-ta-bulz*. Ikkinchi *e* umuman aytilmaydi.",
    "**Baʼzi ovqat nomlarining koʻpligi yoʻq.** *rice, bread, fruit, meat, fish* — *some rice* yeysiz, *three rices* "
    "emas. Lekin *eggs* va *vegetables* sanaladi va deyarli doim koʻplikda keladi.",
])
h.retell("PRONUNCIATION — /Iː/, /Ɪ/ AND /AꞮ/", "TALAFFUZ — /iː/, /ɪ/ VA /aɪ/", [
    "[[/iː/]] choʻziq, *meat* dagi kabi — *meat · teacher · me · eat*",
    "[[/ɪ/]] qisqa, *fish* dagi kabi — *fish · big · milk · sister · it's · his*",
    "[[/aɪ/]] ikki tovush birga, *I'm* dagi kabi — *I'm · nine · five · china · hi*",
    "**Nega /iː/ va /ɪ/ boshqalaridan muhimroq.** Ular haqiqiy soʻz juftliklarini ajratadi: *eat* va *it*, *sheep* "
    "va *ship*, *feel* va *fill*. Adashtirsangiz, faqat talaffuz emas, gapning maʼnosi oʻzgaradi.",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [
    "Rajit haftasidagi ovqatlari haqida gapiradi. U nima yeyishiga va qanchalik tez-tez yeyishiga quloq soling.",
    "Agar sinfingizda audio boʻlsa, bu 3.6-trek. Boʻlmasa, oʻqituvchingiz matnni oʻqib beradi — topshiriqlar bir "
    "xil.",
])
h.retell("WHY YOU DIDN'T HEAR IT", "NEGA ESHITMADINGIZ?", [
    "**Chastota soʻzi maʼnoni beradi, shuning uchun odatda urgʻu oladi.** *I NEVer eat meat.* Feʼl oldidagi baland, "
    "ikki boʻgʻinli soʻzga quloq soling.",
    "**Lekin USUALLY koʻpincha ikki boʻgʻinga qisqaradi** — /ˈjuːʒli/, /ˈjuːʒuəli/ emas. U yozilishiga umuman "
    "oʻxshamaydi. Yozilishini emas, tovushini oʻrganing.",
])
h.retell("CHECK BEFORE YOU GIVE IT IN", "TOPSHIRISHDAN OLDIN TEKSHIRING", [
    "{box}  Toʻrttala ravishni ishlatdim: *always, usually, sometimes, never*.",
    "{box}  Har bir ravish feʼldan oldin — yoki *I'm* dan keyin.",
    "{box}  *never* bilan *don't* yoʻq.   {box}  *I* yoki *we* dan keyingi feʼlda *-s* yoʻq.",
    "{box}  Soʻzlarni sanadim.",
])
h.one_per_line("TOPSHIRISHDAN OLDIN TEKSHIRING", None, at="box")
h.retell_cells({"with a normal verb": "oddiy feʼl bilan", "with BE": "<i>BE</i> bilan"})

# ------------------------------------------------------------------ the key
K = {}
for n in range(1, 8):                             # what they eat
    K[("1.1", n, 1)] = tick()
ABC = {"A": "A · the Tangs", "B": "B · the Novaks", "C": "C · the Patels"}
for n, a in enumerate("CBABAC", 1):
    K[("1.2", n, 1)] = choose(["A", "B", "C"], a, labels=ABC)
TF = {"T": "T · true", "F": "F · false"}
for n, a in enumerate("FTFTFT", 1):
    K[("1.3", n, 1)] = choose(["T", "F"], a, labels=TF)
for n, a in enumerate(["or", "every", "vegetarians", "fruit", "water"], 1):
    K[("1.4", n, 1)] = Q(a)
for key in ((1, 1), (2, 1), (3, 1), (3, 2), (4, 1)):   # their own food
    K[("1.5",) + key] = own(control=None)
K[("1.6", 1, 1)] = own()
for n, a in enumerate(["eat", "don't like/do not like", "drink", "don't eat/do not eat", "like",
                       "don't drink/do not drink"], 1):
    K[("2.1", n, 1)] = Q(a)
for n, a in enumerate(["Do you like fish", "Do they eat meat", "Do we have eggs", "Do you drink coffee",
                       "Do they like vegetables"], 1):
    K[("2.2", n, 1)] = write(a)
for n, a in enumerate(["I don't/I do not", "they do", "we do/you do", "I don't/I do not"], 1):
    K[("2.3", n, 1)] = Q(a)
for n, a in enumerate(["Do", "like", "don't/do not", "don't like/do not like", "Do", "like/eat", "do", "eat", "eat",
                       "don't eat/do not eat"], 1):
    K[("2.4", n, 1)] = Q(a)
TICKED = "✓/correct/tick"
for n, a in zip(range(2, 9), [
        either("They like fish", "like"),
        either("Do you like fish", "Do you"),
        either("I don't eat meat", "I do not eat meat", "don't"),
        TICKED,
        "Yes, I do",
        TICKED,
        either("I don't drink coffee", "I do not drink coffee", "don't")]):
    K[("2.5", n, 1)] = fix(a)
for n in range(1, 13):                            # the survey, in class
    K[("2.6", n, 1)] = pair()
PM = {"+": "+ positive", "−": "− negative"}
for n, a in enumerate(["+", "−", "+", "−"], 1):
    K[("2.7", n, 1)] = choose(["+", "−"], a, labels=PM)
for n, a in enumerate(["I don't eat meat/I do not eat meat", "They don't like vegetables/They do not like vegetables",
                       "We don't drink coffee/We do not drink coffee", "You don't eat bread/You do not eat bread"], 1):
    K[("2.8", n, 1)] = write(a)
K[("2.9", 1, 1)] = own()
ADV = ["always", "usually", "sometimes", "never"]
for n, a in enumerate(ADV, 1):
    K[("3.1", n, 1)] = choose(ADV, a)
for n, a in enumerate(["I always eat breakfast at seven", "We usually drink tea in the evening",
                       "They sometimes eat fish/Sometimes they eat fish", "I never eat cake",
                       "I'm always late for class/I am always late for class",
                       "They're never hungry in the morning/They are never hungry in the morning"], 1):
    K[("3.2", n, 1)] = write(a)
for n, a in enumerate("baaab", 1):
    K[("3.3", n, 1)] = choose(["a", "b"], a)
for n in range(1, 7):                             # true for them: any of the four
    K[("3.4", n, 1)] = choose(ADV)
for n, a in enumerate(["Sometimes we eat rice for lunch", "Sometimes they drink coffee after dinner",
                       "Sometimes I have eggs for breakfast"], 1):
    K[("3.5", n, 1)] = write(a)
for n, a in enumerate(["I never eat meat", "They never drink milk", "We never have bread for breakfast",
                       "I'm never hungry in the evening/I am never hungry in the evening"], 1):
    K[("3.6", n, 1)] = write(a)
for n in range(1, 5):                             # a partner's habits, in class
    K[("3.7", n, 1)] = Q(None, options=ADV, control="pair")
K[("3.7", 1, 2)] = pair()
K[("3.7", 2, 2)] = pair()
for n, a in enumerate(["We always have breakfast at seven", "I never eat fish",
                       "I'm usually late for class/I am usually late for class",
                       "They sometimes drink coffee/Sometimes they drink coffee",
                       "We're never hungry in the morning/We are never hungry in the morning"], 1):
    K[("3.8", n, 1)] = write(a)
for n, a in zip(range(2, 9), [
        either("I never drink coffee", "never drink"),
        either("I'm always late", "I am always late", "I'm always"),
        TICKED,
        either("They never eat meat", "never eat"),
        TICKED, TICKED, TICKED]):
    K[("3.9", n, 1)] = fix(a)
for n, a in enumerate(["meat", "rice", "fruit", "fish", "vegetables", "bread"], 1):
    K[("4.1", n, 1)] = Q(a)
CN = {"C": "C · countable", "N": "N · not countable"}
for n, a in enumerate("NCNCNN", 1):
    K[("4.2", n, 1)] = choose(["C", "N"], a, labels=CN)
GROUP43 = {"ee": "/iː/ (meat)", "i": "/ɪ/ (fish)", "ai": "/aɪ/ (I'm)"}
SORT43 = {"eat": "ee", "me": "ee", "teacher": "ee", "big": "i", "sister": "i", "it's": "i", "his": "i",
          "milk": "i", "nine": "ai", "china": "ai", "five": "ai", "hi": "ai"}
for n, w in enumerate(WORDS43, 1):
    K[("4.3", n, 1)] = choose(["ee", "i", "ai"], SORT43[w], labels=GROUP43)
NUMBERS = "two/three/four/five/2/3/4/5/some"
for n, a in enumerate(["some", NUMBERS, "some", "some/" + NUMBERS], 1):
    K[("4.6", n, 1)] = Q(a)
for n, a in {1: "rice", 2: "me", 3: "nine", 4: "vegetables"}.items():
    K[("4.7", n, 1)] = choose(ODD47[n], a)
    K[("4.7", n, 2)] = own()
EATS = {"yes": "✓ he eats it", "no": "✗ not"}
for n, a in enumerate(["yes", "yes", "yes", "no", "yes", "no", "yes", "no"], 1):
    K[("5.1", n, 1)] = choose(["yes", "no"], a, labels=EATS)
for n, a in enumerate(["always", "sometimes", "usually", "never", "always", "never"], 1):
    K[("5.2", n, 1)] = choose(ADV, a)
for n, a in enumerate("FTTFTT", 1):
    K[("5.3", n, 1)] = choose(["T", "F"], a, labels=TF)
for n in range(1, 9):                             # theirs on the left, a partner's on the right
    K[("5.4", n, 1)] = own(control=None) if n % 2 else pair()
K[("5.5", 20, 1)] = own(control="essay")
for n in range(1, 6):                             # the checklist
    K[("5.5", n, 1)] = tick()
FACE_SAYS = dict(zip(FACES, ["🙂 Ha", "😐 Qisman", "🙁 Hali yoʻq"]))
for n in CAN_DO:
    K[("5.6", n, 1)] = choose(FACES, labels=FACE_SAYS)

if __name__ == "__main__":
    data = h.build(K, "Beginner", 3, "Unit 3A — Food and drink")
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "b03a.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
