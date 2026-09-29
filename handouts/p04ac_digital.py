"""P04AC Celebrations - Azamat's Pre-Intermediate booklet, done on a phone.

His design is rendered as it is and this decides every box. The key is his
(P04AC Celebrations - ANSWER KEY), joined box by box by hand. Every
explanation is told again in Uzbek, with the English examples kept, and
every instruction has a line in Uzbek under it; the reading, the texts to
fill in and the exercises stay English.

Put right here, since a page that marks itself cannot be wrong about its
own answers:
  - 4.1: the key gives "My friends are arriving early tomorrow" to Craig,
    but in the script it is Marta's line - M;
  - 5.2: "What about the weekend?" is as right as "How about", and what
    about is in the box, so both are right.

What a phone gets that paper does not:
  - taps for every choice: L/J/V, T/F/DS, plan or arrangement, G or X, the
    four clothes groups, the other half of each sentence, the stress, Marta
    or Craig, I or R, the words in the box, the thinking phrase, what you
    would say to a friend and to your boss, the can-do faces;
  - boxes where paper has none: 2.5's corrections, 3.2, 5.3.
The pair work in 4.4 keeps its boxes; they do not hold the part back.

    python3 handouts/p04ac_digital.py            # writes handouts/p04ac.json, lists every box
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import (Handout, Q, choose, tick, own, write, fix, pair, report,   # noqa: E402
                     BLANK_TAG, plain, ITEM_STYLE, NUM_SPAN, TEXT_SPAN)

DOCX = ("~/Documents/Claude/Material Bank/General English/B1 Pre-intermediate/"
        "P04AC Celebrations — BOOKLET.docx")
W = "95%"
YES_NO = ["✓", "✗"]

h = Handout(DOCX)
TAGS = {int(m.group(1)): m.group(0) for m in BLANK_TAG.finditer(h.html)}


def section(label):
    return h.html.index("%s  </span>" % label)


def either(*forms):
    return "/".join(forms)


def be(subject_forms, rest):
    """'m / am + rest, and the like."""
    return either(*[s + rest for s in subject_forms])


def item_p(label, n, text_html, token):
    h.texts[(label, n)] = plain(text_html)
    return ('<p data-item="%s:%d" %s>%s%s</p>'
            % (label, n, ITEM_STYLE, NUM_SPAN % n, TEXT_SPAN % ("%s  %s" % (text_html, token))))


def key_list(pairs):
    return ('<table class="bk"><tr><td style="vertical-align:top;background:#F2F8F8;'
            'border-left:3px solid #127D80">'
            + "".join('<p style="margin:0"><span style="font-weight:700;color:#127D80">%s</span>  %s</p>'
                      % (l, html.escape(t, quote=False)) for l, t in pairs)
            + "</td></tr></table>")


def halves(label):
    """"Match the halves" with no boxes on paper: the endings go first, as a
    key; then each beginning, with the letters to tap."""
    a = h.html.index('<table class="bk">', section(label))
    b = h.html.index("</table>", a) + len("</table>")
    cells = [plain(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", h.html[a:b], re.S)]
    begins = [re.match(r"(\d+)\s+(.*)", c).groups() for c in cells if re.match(r"\d+\s", c)]
    ends = sorted(re.match(r"([a-f])\s+(.*)", c).groups() for c in cells if re.match(r"[a-f]\s", c))
    h.html = h.html[:a] + key_list(ends) + "".join(
        item_p(label, int(n), html.escape(t, quote=False), "{{box:%s:%s:60px:}}" % (label, n))
        for n, t in begins) + h.html[b:]
    return [l for l, _t in ends]


# ------------------------------------------------------------ 1 Reading
for n in range(1, 4):
    h.item_box("1.5", n, where="leader")

# ------------------------------------------------------------ 2 Grammar
for n in range(2, 7):                             # item 1 is the worked example
    h.item_box("2.5", n)

# ------------------------------------------------------------ 3 Vocabulary
WORDS31 = h.sort_words("3.1", ["belt", "boots", "tights", "scarf", "sweatshirt", "high heels", "socks", "tie",
                               "shorts", "sandals", "earrings", "underwear"], "Clothing")
ENDS32 = halves("3.2")
for n in range(1, 4):
    h.item_box("3.5", n, where="leader")

# ------------------------------------------------------------ 4 Listening
for n in range(1, 7):
    h.item_box("4.2", n, where="leader")
h.grid_rows("4.4")
for n in range(1, 4):
    h.item_box("4.5", n, where="leader")

# ------------------------------------------------------------ 5 Everyday English
PHRASES53 = {1: ["Oh, that sounds nice", "I'll just check", "No, we can't do Wednesday", "Sorry"],
             2: ["Thursday", "hang on a minute", "no, sorry"],
             3: ["Just a moment", "Nothing!", "We can do Monday"],
             4: ["Saturday?", "Ooh … let me think", "Yes, that's fine"]}
for n in PHRASES53:
    h.item_box("5.3", n)
h.leaders("5.5", "CHECK BEFORE", [(20, W, "Write your conversation here")])
h.html = h.html.replace(TAGS[108], "", 1)         # the word count: the box counts them itself
h.grid_rows("5.7")
FACES, CAN_DO = h.can_do_grid("5.8")

# ------------------------------- every instruction, once more, in Uzbek
for label, text, *after in [
        ("1.1", "Sherigingiz bilan muhokama qiling. 1 Mamlakatingizda odam necha yoshda voyaga yetgan "
                "hisoblanadi? 2 Buning uchun bayram bormi? Nima boʻladi? 3 Odamlar buning uchun yangi kiyim sotib "
                "oladimi?", "Do people buy new clothes for it?"),
        ("1.2", "Qaysi mamlakat? *L* (Lotin Amerikasi), *J* (Yaponiya) yoki *V* (Vyetnam) ni tanlang."),
        ("1.3", "Toʻgʻri (*T*), notoʻgʻri (*F*) yoki matnda aytilmagan (*DS*)?"),
        ("1.4", "Matndan shu maʼnodagi soʻz yoki iborani toping."),
        ("1.5", "Savollarga javob bering."),
        ("2.1", "Reja (*P*) mi yoki kelishilgan ish (*A*) mi?"),
        ("2.2", "Present continuous yoki *be going to* bilan toʻldiring."),
        ("2.3", "Gapni kelishilgan ish maʼnosini beradigan qilib qayta yozing — aniq vaqt bilan."),
        ("2.4", "Suhbatni toʻldiring."),
        ("2.5", "Xatoni topib, toʻgʻrilang. IKKITA gap toʻgʻri — ular uchun *✓ It is correct* tugmasini bosing."),
        ("2.6", "Tinglang. *Gonna* mumkinmi (*G*) yoki mumkin emasmi (*X*)?"),
        ("2.7", "Oʻzingiz haqingizda yozing. Vaziyat talab qiladigan shaklni ishlating."),
        ("2.8", "Sherigingizning gaplarini oʻqing. Qaysilari kelishilgan, qaysilari faqat rejalashtirilganini "
                "ajrata olasizmi? Ajrata olmasangiz, shakl oʻz ishini yomon bajaryapti — buni ayting va "
                "toʻgʻrilashga yordam bering.", "help them fix it."),
        ("3.1", "Soʻzlarni toʻrt guruhga joylang."),
        ("3.2", "Gap yarimlarini moslang: harfni tanlang."),
        ("3.3", "Tushuntirishdagi soʻz bilan toʻldiring."),
        ("3.4", "Urgʻuni belgilang: birinchi soʻzdami (*1*) yoki ikkinchi soʻzdami (*2*)?"),
        ("3.5", "Sherigingiz bilan gaplashing. Oʻz javoblaringizni yozing."),
        ("4.1", "Bir marta tinglang. Buni kim aytadi — *M* (Marta) mi yoki *C* (Craig) mi?"),
        ("4.2", "Yana tinglang. Savollarga javob bering."),
        ("4.3", "Yana bir marta tinglang. Eshitgan feʼl shaklingizni yozing."),
        ("4.4", "Endi siz. Sherigingizdan shu vaqtlar haqida soʻrang."),
        ("4.5", "Ikki gapiruvchini solishtiring."),
        ("5.1", "Taklif qilyaptimi (*I*) yoki javob beryaptimi (*R*)?"),
        ("5.2", "Suhbatni ramkadagi soʻzlar bilan toʻldiring: tanlang."),
        ("5.3", "Gapiruvchiga oʻylash uchun vaqt beradigan iborani tanlang."),
        ("5.4", "Asosiy urgʻu qayerga tushadi? Belgilang, keyin ovoz chiqarib ayting."),
        ("5.5", "Suhbatni yozing (70–90 soʻz). Doʻstingizni ovqatga taklif qilmoqchisiz. Avval nima qilayotganini "
                "soʻrang. Sizning kuningiz unga toʻgʻri kelmaydi. Boshqa kun taklif qiling. U oʻylab olish uchun "
                "bir lahza soʻraydi. Vaqtni kelishib oling. U biror narsa olib kelishni taklif qiladi.",
         "offer to bring something."),
        ("5.6", "Rolli oʻyin. Navbat bilan taklif qiling. Javob berishdan oldin telefoningizni tekshiring.",
         "already know the answer."),
        ("5.7", "Sababini aytmasdan rad etish. Bularning qaysi birini yaqin doʻstingizga, qaysi birini "
                "boshligʻingizga aytasiz? *✓* yoki *✗* ni tanlang."),
        ("5.8", "Ikkala darsga qaytib qarang. Nima qila olishingizni belgilang.")]:
    h.say_also(label, text, after=after[0] if after else None)

# ------------------------------------------ the explanations, told in Uzbek
h.goals([
    "reja kelishilganmi yoki yoʻqmi deb soʻrab, present continuous va *be going to* orasida tanlashni",
    "*gonna* ni eshitib tushunishni va u qachon mumkin emasligini bilishni",
    "kiyim, poyabzal, aksessuarlar nomlarini va „eng yaxshi koʻrinish“ iboralarini",
    "qoʻshma otlarda urgʻuni birinchi soʻzga, sifat + otda esa ikkinchi soʻzga qoʻyishni",
    "odamni inglizcha taklif qilishni — avval uning kuni haqida soʻrab",
    "*I'll just check* va *hang on a minute* bilan oʻylab olish uchun vaqt yutishni",
])
h.retell("KEY WORDS", "KALIT SOʻZLAR", [
    "**come of age**  rasman voyaga yetmoq",
    "**a ceremony**  belgilangan tartibli rasmiy tadbir (marosim)",
    "**a relative**  oila aʼzosi, qarindosh",
    "**mark (a day)**  kun muhimligini koʻrsatish uchun biror narsa qilmoq, nishonlamoq",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — PRESENT CONTINUOUS VA BE GOING TO", [
    "Ikkalasi ham kelajak haqida. Farqi — u qanchalik aniq belgilanganida.",
    "[[BE GOING TO]] **reja yoki niyat — qaror qilingan, lekin tashkil qilinmagan.** *We're going to get "
    "married next year.* (Qaror qildik. Hech narsa band qilinmagan.) · *After the exams we're going to "
    "celebrate.* (Qayerda yoki qachon — hali bilmaymiz.)",
    "[[PRESENT CONT.]] **kelishilgan ish — boshqalar bilan kelishilgan yoki puli toʻlangan.** *I'm getting "
    "married next week.* (Joy band, ovqat buyurtma qilingan, taklifnomalar yuborilgan.) · *I'm meeting Mary at "
    "the library tomorrow.* (Vaqt va joyni kelishib oldik.)",
    "**Sinov savoli: boshqa birovga aytilganmi?** Agar boshqa odam rozi boʻlgan boʻlsa yoki hisobingizdan pul "
    "ketgan boʻlsa — bu kelishilgan ish, present continuous. Agar hali faqat boshingizda boʻlsa — *be going to*.",
    "**Vaqt ifodasi haqida bitta ogohlantirish.** Present continuous bilan deyarli doim vaqt ifodasi kerak — "
    "*tomorrow, next week, on Friday* — aks holda gap „hozir“ degan maʼnoni beradi. *She's leaving.* = aynan "
    "hozir. *She's leaving tomorrow.* = kelishilgan kelajak. *She's going to leave.* = reja, vaqt soʻzi shart "
    "emas.",
])
h.retell("ERROR WARNING", "DIQQAT — KELAJAK ZAMONDAGI XATOLAR", [
    "1 **Allaqachon tuzilgan reja uchun will ishlatmang.** ✗ *I will meet Mary tomorrow, we agreed yesterday.* → "
    "✓ *I'm meeting Mary tomorrow.* *Will* — gapirayotgan paytda qabul qilingan qarorlar uchun.",
    "2 **to ni tushirib qoldirmang.** ✗ *We're going get married.* → ✓ *We're going to get married.*",
    "3 **Present simple ishlatmang.** ✗ *Tomorrow I go to the hairdresser's.* → ✓ *I'm going to the "
    "hairdresser's tomorrow.* Kelajak uchun present simple faqat jadvallarda ishlatiladi: *the train leaves at "
    "six*.",
    "4 **Going to go — toʻgʻri.** Gʻalati koʻrinadi va oʻquvchilar undan qochadi, lekin *We're going to go to "
    "Spain* — oddiy ingliz tili. *We're going to Spain* ham toʻgʻri — va band qilinganini bildiradi.",
])
h.retell("PRONUNCIATION — GOING TO BECOMES GONNA", "TALAFFUZ — GOING TO GONNA GA AYLANADI", [
    "Tez nutqda *going to* + feʼl /ˈɡənə/ ga aylanadi. *I'm going to call him* → *I'm gonna call him*. Ikki "
    "boʻgʻin yoʻqoladi va buni hech kim sezmaydi.",
    "**Lekin faqat feʼldan oldin.** *I'm going to the hairdresser's* — bu yerda *to* predlog, *going* esa "
    "haqiqiy harakat feʼli, shuning uchun *going to* boʻlib qoladi. *I'm gonna the hairdresser's* deb "
    "boʻlmaydi.",
    "**Eshiting, lekin yozmang.** *Gonna* ogʻzaki nutqqa tegishli. Email yoki imtihonda xato koʻrinadi, "
    "shuning uchun uni tanib oling, qogʻozda esa toʻliq shaklni yozing.",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — KIYIM VA KOʻRINISH", [
    "[[KIYIM]] *jumper · suit · raincoat · top · tracksuit · sweatshirt · shorts*",
    "[[POYABZAL]] *trainers · boots · flat shoes · high heels · sandals*",
    "[[AKSESSUARLAR]] *necklace · sunglasses · belt · scarf · handbag · bracelet · earrings · tie · gloves*",
    "[[ICH KIYIM]] *socks · underwear · tights*",
    "**Katta kun uchun iboralar:** *look your best · get a new outfit · have a shave · go to the hairdresser's · "
    "go to the beautician's · need a haircut*",
    "**Joy nomlaridagi apostrof-s ga eʼtibor bering:** *the hairdresser's, the beautician's, the dentist's* — "
    "doʻkon oʻsha odamga tegishli. Shuning uchun *go to the hairdresser's* deyiladi, *go to the hairdresser* "
    "emas — u sartaroshning oʻzining yoniga borib turishni bildiradi.",
])
h.retell("PRONUNCIATION — WHERE THE STRESS GOES IN A TWO-WORD THING",
         "TALAFFUZ — IKKI SOʻZLI NARSADA URGʻU QAYERDA", [
             "[[BIRINCHI]] **Qoʻshma otlar** — bir-biriga yopishgan ikki ot — urgʻuni BIRINCHI qismga oladi: "
             "*SUNglasses · HANDbag · TRACKsuit · SWEATshirt · RAINcoat · NECKlace · EARrings*",
             "[[IKKINCHI]] **Sifat + ot** urgʻuni IKKINCHI qismga oladi: *flat SHOES · high HEELS · black BOOTS · "
             "long GLOVES*",
             "**Bu maʼnoni oʻzgartiradi.** *A GREENhouse* — oʻsimliklar uchun oynali bino (issiqxona). *A green "
             "HOUSE* — yashil rangga boʻyalgan uy. Bir xil ikki soʻz, ularni faqat urgʻu ajratadi.",
         ])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [
    "Marta — talaba. Ertaga uning kollejida yozgi bal — yiliga bir kecha, u nonushtagacha davom etadi. Craig "
    "shanba kuni uylanyapti, va uning toʻyi ikki kunlik marosimlardan iborat.",
    "Agar sinfingizda audio boʻlsa, bu 4.3-trek. Boʻlmasa, oʻqituvchingiz matnni oʻqib beradi — topshiriqlar bir "
    "xil.",
])
h.retell("WHY YOU DIDN'T HEAR IT", "NEGA ESHITMADINGIZ?", [
    "**Ikkala shaklni eshitish qiyin, chunki grammatika eng kuchsiz boʻgʻinlarda.** *'re going to* — ingliz "
    "tilidagi eng past ovozli qismlardan biri, yolgʻiz *'re* esa deyarli hech narsa.",
    "**Shuning uchun undan keyingi asosiy soʻzga quloq soling.** *I'm meeting the others* da baland soʻz — "
    "*meeting*; *We're gonna stay* da — *stay*. Feʼlni ushlang, keyin uni qaysi shakl olib kelganini aniqlang.",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — UCHRASHUVNI KELISHISH", [
    "[[TAKLIF QILISH]] *Would you like to come round for a meal? · Are you doing anything on Wednesday? · What "
    "are you doing on Monday? · How about Thursday? Is that OK for you?*",
    "[[JAVOB BERISH]] *We can't do Wednesday, sorry. · This week's really busy for us. · Nothing — I'm free. · "
    "What time shall we come round? · Would you like us to bring anything?*",
    "**Ikki bosqichli taklifga eʼtibor bering.** Inglizlar kamdan-kam toʻgʻridan-toʻgʻri taklif qiladi. Avval "
    "nima qilayotganingizni soʻrashadi — *Are you doing anything on Wednesday?* — va boʻsh ekaningizni "
    "bilgandan keyingina taklif qilishadi. Bu ikkala odamni ham rad etishdan qutqaradi.",
    "**Kun bilan kelgan do ga eʼtibor bering.** *We can't do Wednesday* — „chorshanba bizga toʻgʻri kelmaydi“ "
    "degani. Bu juda keng tarqalgan va juda norasmiy ibora, biror ish qilish bilan aloqasi yoʻq.",
])
h.retell("CONVERSATION SKILLS — MAKING TIME TO THINK", "SUHBAT KOʻNIKMASI — OʻYLASH UCHUN VAQT", [
    "Pauza qilishingiz mumkin. Jim qolishingiz mumkin emas. Kimdir sizni taklif qilsa, tekshirish uchun bir "
    "lahza kerak — shu lahzani ovoz chiqarib toʻldiring.",
    "*I'll just check. · Hang on a minute. · Just a moment… · Let me think. · Ooh, that sounds nice…*",
    "**Nega bu koʻrinishidan muhimroq.** Telefonda jimlik xohlamaslikdek eshitiladi — suhbatdoshingiz siz "
    "bahona oʻylab topyapsiz deb oʻylay boshlaydi. Ovoz chiqarib oʻylayotgan toʻrt soʻz buni butunlay "
    "toʻxtatadi. Bu lugʻat emas, xushmuomalalik vositasi.",
])
h.retell("PRONUNCIATION — SENTENCE STRESS", "TALAFFUZ — GAP URGʻUSI", [
    "Ingliz tili yangilikni olib yuradigan soʻzlarga urgʻu beradi, qolganini yutib yuboradi. *Are you doing "
    "anything on Wednesday?* — uchta urgʻu, qolgani tez va past.",
    "**Urgʻuni koʻchirish maʼnoni oʻzgartiradi.** *I can't do WEDnesday* = boshqa kunni sinab koʻring. · *I CAN'T "
    "do Wednesday* = soʻrashni bas qiling. · *I can't do Wednesday*, urgʻu *I* da = lekin boshqa birov qila "
    "oladi.",
])
h.retell("CHECK BEFORE YOU HAND IT IN", "TOPSHIRISHDAN OLDIN TEKSHIRING", [
    "{box}  Taklif qilishdan oldin *Are you doing anything…?* deb soʻradim.",
    "{box}  Bitta oʻylash iborasini ishlatdim — *I'll just check / hang on a minute*.",
    "{box}  Kelishilgan kun uchun *will* emas, present continuous ishlatdim.",
    "{box}  Faqat kunni emas, vaqtni ham kelishdik.   {box}  Soʻzlar soni: 70–90.",
])
h.one_per_line("TOPSHIRISHDAN OLDIN TEKSHIRING", None, at="box")
h.retell_cells({"short answer": "qisqa javob"})

# ------------------------------------------------------------------ the key
K = {}
LJV = {"L": "L · Latin America", "J": "J · Japan", "V": "V · Vietnam"}
for n, a in enumerate("VLJLJV", 1):
    K[("1.2", n, 1)] = choose(["L", "J", "V"], a, labels=LJV)
TFDS = {"T": "T · true", "F": "F · false", "DS": "DS · doesn't say"}
for n, a in enumerate(["F", "T", "T", "T", "DS", "F"], 1):
    K[("1.3", n, 1)] = choose(["T", "F", "DS"], a, labels=TFDS)
for n, a in enumerate(["rent/to rent", "a month's salary/month's salary/salary", "a speech/speech",
                       "the big one/big one"], 1):
    K[("1.4", n, 1)] = Q(a)
for n in range(1, 4):
    K[("1.5", n, 1)] = own()
PA = {"P": "P · plan", "A": "A · arrangement"}
for n, a in enumerate("APPAAP", 1):
    K[("2.1", n, 1)] = choose(["P", "A"], a, labels=PA)
for key, a in (((1, 1), either("'m seeing", "am seeing")), ((2, 1), either("'re going to buy", "are going to buy")),
               ((3, 1), "Are"), ((3, 2), "coming"), ((4, 1), either("'m not working", "am not working")),
               ((5, 1), either("'s going to study", "is going to study")),
               ((6, 1), either("'re having", "are having"))):
    K[("2.2",) + key] = Q(a)
for n in range(1, 5):                             # any answer with a time is right: his to read
    K[("2.3", n, 1)] = own()
for n, a in enumerate(["are you doing", either("'s getting", "is getting"),
                       either("Are you wearing", "Are you going to wear"),
                       either("'m going to buy", "am going to buy"),
                       either("'re just going to rest", "are just going to rest", "'re going to just rest",
                              "are going to just rest"),
                       either("'s coming", "is coming")], 1):
    K[("2.4", n, 1)] = Q(a)
TICKED = "✓/correct/tick"
for n, a in zip(range(2, 7), [
        either("We're going to get married in June", "We are going to get married in June"),
        TICKED,
        either(*[s + r for s in ("I'm meeting Ali on Friday", "I am meeting Ali on Friday")
                 for r in ("", " — we arranged it last week", " - we arranged it last week",
                           ", we arranged it last week")]),
        TICKED,
        either(*[s + r for s in ("She's leaving tomorrow", "She is leaving tomorrow")
                 for r in ("", ". She has a ticket for the 6.15 train", ". She has a ticket for the 6.15 train "
                                                                       "tomorrow")])]):
    K[("2.5", n, 1)] = fix(a)
GX = {"G": "G · gonna possible", "X": "X · impossible"}
for n, a in enumerate("GXGX", 1):
    K[("2.6", n, 1)] = choose(["G", "X"], a, labels=GX)
for n in range(1, 5):
    K[("2.7", n, 1)] = own()
GROUPS = ["Clothing", "Footwear", "Accessories", "Underclothes"]
SORT = {"belt": "Accessories", "boots": "Footwear", "tights": "Underclothes", "scarf": "Accessories",
        "sweatshirt": "Clothing", "high heels": "Footwear", "socks": "Underclothes", "tie": "Accessories",
        "shorts": "Clothing", "sandals": "Footwear", "earrings": "Accessories", "underwear": "Underclothes"}
for n, w in enumerate(WORDS31, 1):
    K[("3.1", n, 1)] = choose(GROUPS, SORT[w])
for n, a in enumerate("caedbf", 1):
    K[("3.2", n, 1)] = choose(ENDS32, a)
for n, a in enumerate(["raincoat/a raincoat", "a tracksuit/tracksuit/shorts/trainers", "tie/a tie",
                       "heels/high heels", "handbag/a handbag"], 1):
    K[("3.3", n, 1)] = Q(a)
FIRST_SECOND = {"1": "1 · first word", "2": "2 · second word"}
# as numbered: 1 sunglasses 2 high heels 3 handbag 4 flat shoes 5 raincoat 6 black tie
for n, a in enumerate("121212", 1):
    K[("3.4", n, 1)] = choose(["1", "2"], a, labels=FIRST_SECOND)
for n in range(1, 4):                             # about themselves
    K[("3.5", n, 1)] = own()
MC = {"M": "M · Marta", "C": "C · Craig"}
for n, a in enumerate("MMCCMM", 1):             # 6 is Marta's line in the script, not Craig's
    K[("4.1", n, 1)] = choose(["M", "C"], a, labels=MC)
for n in range(1, 7):
    K[("4.2", n, 1)] = own()
for n, a in enumerate([either("are arriving", "'re arriving"), either("is playing", "'s playing"),
                       either("'re going to stay", "are going to stay", "'re gonna stay"),
                       either("'m meeting", "am meeting"),
                       either("'re going to make", "are going to make", "'re gonna make"),
                       either("'m not going to see", "am not going to see", "'m not gonna see")], 1):
    K[("4.3", n, 1)] = Q(a)
for n in range(1, 9):                             # asked of a partner, in class
    K[("4.4", n, 1)] = pair()
for n in range(1, 4):
    K[("4.5", n, 1)] = own()
IR = {"I": "I · inviting", "R": "R · responding"}
for n, a in enumerate("IRIRIR", 1):
    K[("5.1", n, 1)] = choose(["I", "R"], a, labels=IR)
BOX52 = ["are you doing", "would you like", "can't", "how about", "is that OK", "busy", "shall", "what about"]
for n, a in enumerate(["are you doing", "would you like", "can't", "how about/what about", "is that OK", "busy",
                       "shall"], 1):
    K[("5.2", n, 1)] = choose(BOX52, a)
THINK = {1: "I'll just check/Oh, that sounds nice", 2: "hang on a minute", 3: "Just a moment",
         4: "Ooh … let me think"}
for n, a in THINK.items():
    K[("5.3", n, 1)] = choose(PHRASES53[n], a)
K[("5.5", 20, 1)] = own(control="essay")
for n in range(1, 6):                             # the checklist
    K[("5.5", n, 1)] = tick()
# a close friend: any of the four; your boss: the two with I'm afraid, never Nah
for n, (friend, boss) in enumerate([(None, None), (None, "✓"), (None, "✗"), (None, "✓")]):
    K[("5.7", 2 * n + 1, 1)] = choose(YES_NO, friend)
    K[("5.7", 2 * n + 2, 1)] = choose(YES_NO, boss)
FACE_SAYS = dict(zip(FACES, ["🙂 Yes", "😐 Nearly", "🙁 Not yet"]))
for n in CAN_DO:                                  # the self-check: one face a row
    K[("5.8", n, 1)] = choose(FACES, labels=FACE_SAYS)

if __name__ == "__main__":
    data = h.build(K, "Pre-Intermediate", 4, "Unit 4A & 4C — Celebrations")
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "p04ac.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
