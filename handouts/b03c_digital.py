"""B03C Food and drink - Azamat's Beginner booklet (3C), done on a phone.

His design is rendered as it is and this decides every box. The key is his
(B03C Food and drink - ANSWER KEY), joined box by box by hand. This is the
Material Bank copy (_NEW BOOKLET STYLE); it splits into its five parts.

As with the other Beginner booklets, every box that explains is told again
in Uzbek, as are the goals and every instruction; the English examples stay
English, as do the reading and the exercises.

Put right here: 2.6 says TWO sentences are correct; three are (3, 6 and 7 -
the key says so itself): it says THREE. What the paper has students
underline is tapped or typed instead: 3.4's stress is a tap between the
word's stress patterns, 3.5's two loud words are typed with a comma. 3.2's
menu and 4.7's bill are tables whose prices the page reader took for
exercise numbers; their boxes are put back under 3.2 and 4.7. 5.3 is
rewritten a sentence at a time, so each contraction is marked. In 4.6 "Here
you are" is said by Sophia and by the server (the key says so): either
counts. The speaking tasks, the survey and the roleplay are done in class.

    python3 handouts/b03c_digital.py            # writes handouts/b03c.json, lists every box
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digital import (Handout, Q, choose, tick, own, write, fix, report,   # noqa: E402
                     BLANK_TAG, plain, told, ITEM_STYLE, NUM_SPAN, TEXT_SPAN)

DOCX = ("~/Documents/Claude/Material Bank/General English/A1 Beginner/_NEW BOOKLET STYLE/"
        "B03C Food and drink — BOOKLET.docx")
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


def table_after(label):
    a = h.html.index('<table class="bk">', section(label))
    return a, h.html.index("</table>", a) + len("</table>")


def table_end(a):
    """Where the table opened at a closes, tables inside it included."""
    depth, at = 0, a
    for m in re.compile(r"<table\b|</table>").finditer(h.html, a):
        depth += 1 if m.group(0) != "</table>" else -1
        if depth == 0:
            return m.end()
    raise SystemExit("a table that never closes")


def reword(label, old, new):
    at = section(label) + len("%s  </span>" % label)
    end = h.html.index("</p>", at)
    if plain(h.html[at:end]) != old:
        raise SystemExit("%s says %r" % (label, plain(h.html[at:end])))
    style = re.match(r'<span( style="[^"]*")?>', h.html[at:end])
    h.html = h.html[:at] + "<span%s>%s</span>" % (style.group(1) or "", html.escape(new)) + h.html[end:]


def boxes_for(label, nums, width="95%", placeholder=""):
    for n in nums:
        h.item_box(label, n, width=width, placeholder=placeholder)


def put_box(tag_no, label, n, text, width="130px"):
    """A box the page reader filed under the wrong exercise, put back under its own."""
    h.texts[(label, n)] = text
    h.html = h.html.replace(TAGS[tag_no], "{{box:%s:%d:%s:}}" % (label, n, width), 1)


# ------------------------------------------------------------ 2 Language
for k in range(46, 52):                            # 2.4: each line first, then its place - not the other way round
    h.html = re.sub(re.escape(TAGS[k]) + r"\s*([^<]*)", lambda m, t=TAGS[k]: m.group(1) + "  " + t, h.html, 1)
reword("2.6", "Find and correct the mistake. TWO sentences are correct — tick them.",
       "Find and correct the mistake. THREE sentences are correct — tick them.")
boxes_for("2.6", range(2, 9))                     # item 1 is the worked example

# ------------------------------------------------------------ 3 Vocabulary
for n, what in enumerate(["Sandwiches", "Drinks", "a … of chocolate cake", "a … of water"], 1):
    put_box(75 + n, "3.2", n, what)
ODD33 = h.odd_one_out("3.3", why="Why is it different?")
reword("3.4", "Underline the stressed syllable.", "Choose where the stress is.")
boxes_for("3.4", range(1, 7), width="60px")
reword("3.5", "Say each phrase. Make of very small. Underline the two loud words.",
       "Say each phrase. Make of very small. Write the two loud words, with a comma.")
boxes_for("3.5", range(1, 5), width="180px", placeholder="loud, words")

# ------------------------------------------------------------ 4 Listening
put_box(106, "4.7", 1, "Right or wrong?", "60px")
put_box(107, "4.7", 2, "The correct total is")
h.html = h.html.replace("{{box:4.7:1:60px:}}", "{{box:4.7:1:60px:}}<br>", 1)

# ------------------------------------------------------------ 5 Writing
MESSAGE = ["I am in a café with Megan.", "She is my friend from work.", "She is very nice.",
           "We are near the office.", "It is a small café but the cake is great.",
           "I do not have a lot of time."]
b = table_end(table_after("5.3")[0])             # Sophia's message stays; under it, a sentence at a time
h.html = (h.html[:b]
          + "".join(item_p("5.3", n, html.escape(t), "{{box:5.3:%d:%s:with contractions}}" % (n, W))
                    for n, t in enumerate(MESSAGE, 1))
          + h.html[b:])
boxes_for("5.4", range(1, 5))
h.leaders("5.5", "CHECK BEFORE", [(20, W, "Write your message here")])
h.html = h.html.replace(TAGS[129], "", 1)          # the word count: the box counts them itself
h.leaders("5.7", "5.8  </span>", [(1, W, "Hi, Megan. …")])
FACES, CAN_DO = h.can_do_grid("5.9")

# ------------------------------- every instruction, once more, in Uzbek
for label, text in [
        ("1.1", "Kafega borasizmi? U yerda nima olasiz? Belgilang."),
        ("1.2", "Qaysi kafe? *1*, *2* yoki *3* ni tanlang."),
        ("1.3", "Toʻgʻri (*T*) mi yoki notoʻgʻri (*F*) mi?"),
        ("1.4", "Narxni yozing."),
        ("1.5", "Gaplarni matndagi soʻz bilan toʻldiring."),
        ("1.6", "Qaysi kafe sizga yoqadi? Sherigingizga nega ekanini ayting."),
        ("2.1", "Kerak joyda *of* ni, kerak boʻlmasa *–* ni tanlang."),
        ("2.2", "Soʻzlarni tartib bilan qoʻyib, gap tuzing."),
        ("2.3", "Narxni soʻz bilan yozing."),
        ("2.4", "Suhbatni tartibga keltiring: har bir qatorning oʻrnini (1–6) tanlang."),
        ("2.5", "Suhbatni toʻldiring."),
        ("2.6", "Xatoni topib, toʻgʻrilang. UCHTA gap toʻgʻri — ular uchun *✓ It is correct* tugmasini bosing."),
        ("2.7", "Siz xizmatchisiz. Umumiy narxni soʻz bilan ayting."),
        ("2.8", "Mijozning gapini yozing. *I'd like* yoki *Can I have* ishlating."),
        ("2.9", "Uch kishilik guruhda ishlang: xizmatchi, mijoz, mijoz. Buyurtma bering, toʻlang, rollarni "
                "almashtiring. Buni sinfda bajarasiz."),
        ("3.1", "Chashkami yoki stakanmi? *a cup of* yoki *a glass of* ni tanlang."),
        ("3.2", "Menyuni toʻldiring. Tushuntirishdagi soʻzlardan foydalaning."),
        ("3.3", "Qaysi soʻz boshqacha? Uni tanlang va nega ekanini yozing."),
        ("3.4", "Urgʻu qaysi boʻgʻinga tushadi? Tanlang."),
        ("3.5", "Har bir iborani ayting, *of* ni juda kichik qiling. Ikki baland soʻzni vergul bilan yozing."),
        ("3.6", "Sherigingiz bilan ishlang. 3.2 dagi menyudan uchta narsa buyuring. Sherigingiz umumiy narxni "
                "aytadi."),
        ("4.1", "Bir marta tinglang. Ular nimani buyurdi? *✓* yoki *✗* ni tanlang."),
        ("4.2", "Yana tinglang. Toʻgʻri (*T*) mi yoki notoʻgʻri (*F*) mi?"),
        ("4.3", "Yana bir marta tinglang. Gaplarni toʻldiring."),
        ("4.4", "Endi siz. Sherigingiz bilan rolli oʻyin — sxemadan foydalaning. Buni sinfda bajarasiz."),
        ("4.5", "Sofiyaning yangiligi nima? Bitta gap yozing."),
        ("4.6", "Buni kim aytadi — xizmatchi (*S*), Megan (*M*) yoki Sofiya (*SO*)?"),
        ("4.7", "Hisobni tekshiring. Umumiy narx toʻgʻrimi? 3.2 dagi menyudan foydalaning."),
        ("5.1", "Meganning xabarini yana oʻqing. Javob bering."),
        ("5.2", "Qisqartmasini yozing."),
        ("5.3", "Xabarni qisqartmalar bilan qayta yozing — har bir gapni alohida."),
        ("5.4", "Har bir qatordagi xatoni topib, toʻgʻri gapni yozing."),
        ("5.5", "Doʻstingizga SMS yozing (30–40 soʻz). Toʻrt qismni va kamida UCHTA qisqartmani ishlating."),
        ("5.6", "Sherigingizning xabarini oʻqing. U kim haqida yozgan? Sinfga ayting."),
        ("5.7", "Meganga javob yozing. Siz Jeymssiz. Ikkita qisqartma bilan ikki qator yozing."),
        ("5.8", "Qisqartmami yoki yoʻqmi? SMS da (*T*) ishlatamiz, rasmiy xatda (*L*) ishlatmaymiz. *T* yoki "
                "*L* ni tanlang."),
        ("5.9", "Butun darsni eslang. Har bir ish uchun qanchalik qila olishingizni tanlang.")]:
    h.say_also(label, text)

# ------------------------------------------ the explanations, told in Uzbek
h.goals([
    "*I'd like…* va *Can I have…?* bilan — *please* qoʻshib — buyurtma berishni",
    "*a cup of, a glass of, a piece of, a bottle of* ni ishlatishni",
    "funtdagi narxni tushunish va aytishni",
    "*COFfee* va *baNAna* da urgʻuni toʻgʻri boʻgʻinga qoʻyishni va *of* ni yoʻqotishni",
    "toʻrt qismdan iborat qisqa SMS yozishni",
    "*I'm, she's, it's, don't* kabi qisqartmalarni apostrofni toʻgʻri joyga qoʻyib ishlatishni",
])
h.retell("KEY WORDS", "KALIT SOʻZLAR", [
    "**a menu**  menyu — ovqat, ichimlik va narxlar roʻyxati",
    "**a customer**  mijoz — biror narsa sotib oladigan odam",
    "**cheap**  arzon — qimmat emas",
    "**a piece**  boʻlak — tortning bir qismi",
])
h.retell("PRESENTATION — THE CONVERSATION HAS A SHAPE", "TUSHUNTIRISH — SUHBATNING SHAKLI BOR", [
    "Ingliz tilidagi har bir kafe suhbati bir xil besh qadamdan iborat. Qadamlarni oʻrganing — istalgan "
    "joyda buyurtma bera olasiz.",
    "[[1]] **Mijoz soʻraydi.** *I'd like a cup of tea, please. · Can I have a cup of coffee, please?* Ikki "
    "xil usul, maʼnosi bir xil. Ikkalasi ham *please* bilan tugaydi.",
    "[[2]] **Xizmatchi „ha“ deb, ovqat haqida soʻraydi.** *Of course. / Certainly.* Keyin: *And to eat? / "
    "And something to eat?*",
    "[[3]] **Mijoz ovqat buyuradi — yoki „yoʻq“ deydi.** *A cheese sandwich, please. · No, thanks. Just the "
    "tea.*",
    "[[4]] **Xizmatchi narxni aytadi.** *That's £5.00, please. · That's six pounds fifty.*",
    "[[5]] **Toʻlash, olish, rahmat.** *Here you are. — Thank you.* *Here you are* ni ikkalasi ham aytadi — "
    "pul berayotganda ham, choy berayotganda ham.",
    "**I'D LIKE = I would like.** Bu muloyim. *I want* xato emas, lekin kafeda bolaning gapiga oʻxshaydi. "
    "*I'd like* yoki *Can I have* ishlating.",
])
h.retell("PRESENTATION — A CUP OF", "TUSHUNTIRISH — A CUP OF", [
    "Ichimlik va tortga idish soʻzi + **OF** kerak. *a tea* deb buyurtma bersangiz, kerakli narsani "
    "olmasligingiz mumkin. *a cup of tea* deb buyurtma berasiz.",
    "*a cup of tea / coffee · a glass of cola / orange juice / water · a bottle of water · a piece of cake*",
    "**Sendvichga OF kerak emas** — u bitta butun narsa: *a cheese sandwich, two egg sandwiches.*",
    "[[NARXLAR]] *£2.50 = two pounds fifty · £3.00 = three pounds · £6.00 = six pounds.* *pounds* deysiz, "
    "pensni tushirib qoldirsa ham boʻladi: *two fifty* ham toʻgʻri.",
])
h.retell("ERROR WARNING", "DIQQAT — KOʻP UCHRAYDIGAN XATOLAR", [
    "1 **OF ni unutmang.** ✗ *a cup tea* ✗ *a glass cola* → ✓ *a cup of tea* ✓ *a glass of cola*",
    "2 **I like emas, I'D like.** ✗ *I like a coffee, please.* → ✓ *I'd like a coffee, please.* *I like "
    "coffee* — umuman qahvani yoqtiraman degani. *I'd like* — hozir bittasini bering degani.",
    "3 **Can I take / Can I get emas, CAN I HAVE.** ✗ *Can I take a tea?* → ✓ *Can I have a cup of tea?* "
    "(*Can I get* — Amerika inglizchasi, u ham toʻgʻri, lekin avval *have* ni oʻrganing.)",
    "4 **Narxni POUNDS bilan ayting.** ✗ *That's two point five.* → ✓ *That's two pounds fifty.*",
    "5 **PLEASE ni unutmang.** *please* siz buyurtma buyruqdek eshitiladi. Har bir buyurtmada, har safar.",
])
h.retell("PRESENTATION", "TUSHUNTIRISH — KAFE SOʻZLARI", [
    "**Ichimliklar:** *tea · coffee · orange juice · cola · water*",
    "**Ovqatlar:** *a cheese sandwich · an egg sandwich · a tomato sandwich · a banana sandwich · chocolate "
    "cake · banana cake*",
    "**Idishlar:** *a cup · a glass · a bottle · a piece*",
    "**Odamlar va narsalar:** *a customer · a server* (ovqatingizni olib keladigan odam) *· the menu · the "
    "bill* (narx yozilgan qogʻoz)",
    "Issiq ichimlik chashkada (*cup*), sovuq ichimlik stakanda (*glass*) boʻladi. Demak *a cup of tea, a cup "
    "of coffee* — lekin *a glass of cola, a glass of juice, a glass of water*. *a cup of cola* deb hech kim "
    "aytmaydi.",
])
h.retell("PRONUNCIATION — TWO SYLLABLES, ONE STRESS", "TALAFFUZ — IKKI BOʻGʻIN, BITTA URGʻU", [
    "Kafe soʻzlarining koʻpi ikki boʻgʻinli, urgʻu esa har doim bir joyda emas.",
    "[[BIRINCHI BOʻGʻIN]] *COFfee · SANDwich · ORange · WAter · CUStomer*",
    "[[IKKINCHI BOʻGʻIN]] *baNAna · toMAto* (*banana* da uchta boʻgʻin bor)",
    "**Nega muhim.** Urgʻuni oxiriga qoʻyib *cofFEE* desangiz, inglizlar bu soʻzni tanimaydi — xizmatchi hech "
    "narsa eshitmaydi. Baland boʻgʻinda qarsak chaling.",
])
h.retell("PRONUNCIATION — OF DISAPPEARS", "TALAFFUZ — OF YOʻQOLADI", [
    "*a cup of tea* da *of* deyarli eshitilmaydi. U /ə/ — ingliz tilidagi eng kichik tovush. *A cup of tea* → "
    "/ə kʌp ə tiː/. *A piece of cake* → /ə piːs ə keɪk/.",
    "Baland soʻzlar — idish va narsa: *CUP … TEA. GLASS … COLA. PIECE … CAKE.* Ularning orasidagi hamma "
    "narsa jim.",
])
h.retell("BEFORE YOU LISTEN", "TINGLASHDAN OLDIN", [
    "Megan Londonda ishlaydi. Uning yangi dugonasi Sofiya Kanadadan. Ular kafega boradi. Nima buyurishiga, "
    "narxga va bitta yangilikka quloq soling.",
    "Agar sinfingizda audio boʻlsa, bu 3.18-trek. Boʻlmasa, oʻqituvchingiz matnni oʻqib beradi — "
    "topshiriqlar bir xil.",
])
h.retell("WHY YOU DIDN'T HEAR IT", "NEGA ESHITMADINGIZ?", [
    "**Narx — eng tez qism.** *Nine pounds fifty* /naɪn pəunz fɪfti/ boʻlib chiqadi — *pounds* oʻzining *d* "
    "sini yoʻqotadi. Ikki raqamga quloq soling, oʻrtadagi soʻzga eʼtibor bermang.",
    "**I'd like esa I like ga oʻxshab eshitiladi.** *'d* — /l/ oldidagi bitta kichik /d/. Kafeda bu muhim "
    "emas — *please* buyurtma ekanini bildiradi. Lekin 4.3 da *I'd* deb yozing.",
])
h.retell("PRESENTATION — THE TEXT MESSAGE", "TUSHUNTIRISH — SMS XABAR", [
    "Megan kafedan doʻsti Jeymsga yozadi:",
    "*Hi, James. I'm in a café with Sophia. She's my new friend at work. She's from Canada. She has a new "
    "flat here in London! Talk to you later. Megan.*",
    "SMS qisqa boʻladi va toʻrt qismdan iborat: *Hi* + ism · qayerdasiz va kim bilan · u odam haqida bir-ikki "
    "fakt · xayrlashuv + ismingiz.",
    "[[XAYRLASHUVLAR]] *Talk to you later. · See you soon. · See you later. · Talk soon.*",
])
h.retell("PRESENTATION — CONTRACTIONS", "TUSHUNTIRISH — QISQARTMALAR", [
    "Ogʻzaki nutqda va xabarlarda ingliz tili ikki soʻzni bittaga qoʻshadi. Apostrof ' qaysi harf tushib "
    "qolganini koʻrsatadi.",
    "*I am → I'm · you are → you're · he is → he's · she is → she's · it is → it's · we are → we're · they "
    "are → they're*",
    "*is not → isn't · are not → aren't · do not → don't · I would → I'd*",
    "Qisqartmalarni SMS da va kafeda ishlating, rasmiy xatda ishlatmang. Bitta ogohlantirish: *it's = it is*. "
    "*its* (apostrofsiz) esa „uniki“ degani. SMS da sizga deyarli har doim *it's* kerak.",
])
h.retell("CHECK BEFORE YOU SEND IT", "YUBORISHDAN OLDIN TEKSHIRING", [
    "{box}  Boshida *Hi* + ism.",
    "{box}  Qayerdasiz va kim bilan.",
    "{box}  Kamida uchta qisqartma, apostrof ' toʻgʻri joyda.",
    "{box}  *its* emas, *it's*.",
    "{box}  Xayrlashuv + ismingiz.",
    "{box}  Soʻzlarni sanadim.",
])
h.one_per_line("YUBORISHDAN OLDIN TEKSHIRING", None, at="box")

# ------------------------------------------------------------------ the key
K = {}
for n in range(1, 8):                             # what they have at a café
    K[("1.1", n, 1)] = tick()
CAFE = {"1": "1 · Rosa's", "2": "2 · The Corner", "3": "3 · Ali's"}
for n, a in enumerate("312132", 1):
    K[("1.2", n, 1)] = choose(["1", "2", "3"], a, labels=CAFE)
TF = {"T": "T · true", "F": "F · false"}
for n, a in enumerate("FTFTFF", 1):
    K[("1.3", n, 1)] = choose(["T", "F"], a, labels=TF)
for n, a in enumerate([either("£2.00", "£2", "2.00", "2", "two pounds"),
                       either("£3.50", "3.50", "three pounds fifty", "three fifty"),
                       either("£4.00", "£4", "4.00", "4", "four pounds"),
                       either("£2.50", "2.50", "two pounds fifty", "two fifty"),
                       either("£3.00", "£3", "3.00", "3", "three pounds"),
                       either("free", "it's free", "it is free", "£0", "0", "nothing", "£0.00")], 1):
    K[("1.4", n, 1)] = Q(a)
for n, a in enumerate(["short", "long", "laptops", "makes", "cheap"], 1):
    K[("1.5", n, 1)] = Q(a)
OF = ["of", "–"]
for n, a in enumerate(["of", "–", "of", "of", "of", "–"], 1):
    K[("2.1", n, 1)] = choose(OF, a)
for n, a in enumerate(["Can I have a cup of coffee, please",
                       "I'd like an egg sandwich, please/I would like an egg sandwich, please",
                       "Can we have two tomato sandwiches, please",
                       "I'd like a glass of cola, please/I would like a glass of cola, please"], 1):
    K[("2.2", n, 1)] = write(a)
for n, a in enumerate(["two pounds fifty/two fifty", "three pounds", "six pounds", "four pounds fifty/four fifty",
                       "one pound twenty/one twenty", "ten pounds"], 1):
    K[("2.3", n, 1)] = Q(a)
PLACES = [str(k) for k in range(1, 7)]
for n, a in enumerate("342516", 1):               # the lines as the booklet lists them, and where each goes
    K[("2.4", n, 1)] = choose(PLACES, a)
for n, a in enumerate(["I'd/I would", "cup", "Of", "to", "have", "of", "That's/That is", "please", "are",
                       "you"], 1):
    K[("2.5", n, 1)] = Q(a)
TICKED = "✓/correct/tick"
for n, a in zip(range(2, 9), [
        either("I'd like a coffee, please", "I would like a coffee, please", "I'd like"),
        TICKED,
        either("Can I have a glass of cola", "Can I have"),
        either("That's two pounds fifty", "That is two pounds fifty", "two pounds fifty"),
        TICKED, TICKED,
        either("I'd like two cheese sandwiches", "I would like two cheese sandwiches", "two cheese sandwiches",
               "sandwiches")]):
    K[("2.6", n, 1)] = fix(a)
for n, a in enumerate([either("five pounds", "£5", "£5.00", "5 pounds"),
                       either("seven pounds fifty", "seven fifty", "£7.50", "7.50"),
                       either("five pounds", "£5", "£5.00", "5 pounds"),
                       either("four pounds fifty", "four fifty", "£4.50", "4.50")], 1):
    K[("2.7", n, 1)] = Q(a)
COFFEE, TEA = "a cup of coffee", "a cup of tea"
for n, a in enumerate([
        either("Can I have a cup of coffee, please", "I'd like a cup of coffee, please",
               "Can I have a coffee, please", "I'd like a coffee, please", "I would like a cup of coffee, please"),
        either("Can I have a cup of tea and a cheese sandwich, please",
               "I'd like a cup of tea and a cheese sandwich, please",
               "Can I have a tea and a cheese sandwich, please", "I'd like a tea and a cheese sandwich, please"),
        either("I'd like two glasses of cola, please", "Can I have two glasses of cola, please",
               "I would like two glasses of cola, please"),
        either("I'd like a bottle of water and a piece of cake, please",
               "Can I have a bottle of water and a piece of cake, please",
               "I would like a bottle of water and a piece of cake, please")], 1):
    K[("2.8", n, 1)] = write(a)
CG = ["a cup of", "a glass of"]
for n, a in enumerate(["a cup of", "a glass of", "a glass of", "a cup of", "a glass of", "a cup of"], 1):
    K[("3.1", n, 1)] = choose(CG, a)
for n, a in enumerate(["Sandwiches/sandwich", "Drinks/drink/hot drinks", "piece", "bottle"], 1):
    K[("3.2", n, 1)] = Q(a)
for n, a in {1: "cake", 2: "cheese", 3: "water", 4: "menu"}.items():
    K[("3.3", n, 1)] = choose(ODD33[n], a)
    K[("3.3", n, 2)] = own()
STRESS = {1: (["COFfee", "cofFEE"], "COFfee"), 2: (["BAnana", "baNAna", "banaNA"], "baNAna"),
          3: (["SANDwich", "sandWICH"], "SANDwich"), 4: (["TOmato", "toMAto", "tomaTO"], "toMAto"),
          5: (["ORange", "orANGE"], "ORange"), 6: (["WAter", "waTER"], "WAter")}
for n, (opts, a) in STRESS.items():
    K[("3.4", n, 1)] = choose(opts, a)
for n, a in enumerate(["cup, coffee", "glass, cola", "piece, cake", "bottle, water"], 1):
    K[("3.5", n, 1)] = Q(a)
ORDERED = {"yes": "✓ they order it", "no": "✗ not"}
for n, a in enumerate(["yes", "yes", "no", "yes", "no", "no"], 1):
    K[("4.1", n, 1)] = choose(["yes", "no"], a, labels=ORDERED)
for n, a in enumerate("TFTFFF", 1):
    K[("4.2", n, 1)] = choose(["T", "F"], a, labels=TF)
K[("4.3", 1, 1)] = Q("like")
K[("4.3", 1, 2)] = Q("coffee")
K[("4.3", 2, 1)] = Q("have")
K[("4.3", 2, 2)] = Q("piece")
K[("4.3", 3, 1)] = Q(either("nine pounds fifty", "£9.50", "9.50", "nine fifty"))
K[("4.3", 4, 1)] = Q("are")
K[("4.3", 5, 1)] = Q("like")
K[("4.5", 1, 1)] = write(either("She has a new flat in London", "She has a new flat", "Sophia has a new flat",
                                "Sophia has a new flat in London", "She's got a new flat", "She has a new flat here"))
WHO = {"S": "S · the server", "M": "M · Megan", "SO": "SO · Sophia"}
for n, a in enumerate(["S", "M", "S", "SO/S", "SO", "M"], 1):
    K[("4.6", n, 1)] = choose(["S", "M", "SO"], a, labels=WHO)
K[("4.7", 1, 1)] = choose(["right", "wrong"], "wrong")
K[("4.7", 2, 1)] = Q(either("£9.00", "£9", "9.00", "9", "nine pounds"))
K[("5.1", 1, 1)] = Q("Megan/from Megan")
K[("5.1", 1, 2)] = Q("James/to James")
K[("5.1", 2, 1)] = Q(either("in a café", "in a cafe", "in a café with Sophia", "in a cafe with Sophia", "a café",
                            "at a café", "at a cafe"))
for k in (1, 2, 3):                               # I'm, She's, She's - in any order
    K[("5.1", 3, k)] = Q("I'm/She's")
K[("5.1", 4, 1)] = own()                          # two facts, in their own words
for n, a in enumerate(["I'm", "she's", "we're", "it's", "they're", "don't", "isn't", "I'd"], 1):
    K[("5.2", n, 1)] = Q(a)
for n, a in enumerate(["I'm in a café with Megan", "She's my friend from work", "She's very nice",
                       "We're near the office", "It's a small café but the cake is great",
                       "I don't have a lot of time"], 1):
    K[("5.3", n, 1)] = write(a + "/" + a.replace("café", "cafe"))
for n, a in enumerate([either("Hi James. I'm in a café with Tom", "Hi James, I'm in a café with Tom",
                              "Hi, James. I'm in a café with Tom", "I'm in a café with Tom", "I'm"),
                       either("He's my friend from school", "He's"),
                       either("It's a nice café near the station", "It's"),
                       either("We don't have a lot of time — see you later!", "We don't have a lot of time",
                              "We don't have", "don't have")], 1):
    K[("5.4", n, 1)] = write(a)
K[("5.5", 20, 1)] = own(control="essay")
for n in range(1, 7):                             # the checklist
    K[("5.5", n, 1)] = tick()
K[("5.7", 1, 1)] = own()
TL = {"T": "T · text message", "L": "L · formal letter"}
for n, a in enumerate("TLTL", 1):
    K[("5.8", n, 1)] = choose(["T", "L"], a, labels=TL)
FACE_SAYS = dict(zip(FACES, ["🙂 Ha", "😐 Qisman", "🙁 Hali yoʻq"]))
for n in CAN_DO:
    K[("5.9", n, 1)] = choose(FACES, labels=FACE_SAYS)

if __name__ == "__main__":
    data = h.build(K, "Beginner", 3, "Unit 3C — Food and drink")
    data["layout"] = data["layout"].replace('<div class="booklet">', '<div class="booklet" data-lang="uz">', 1)
    out = os.path.join(HERE, "b03c.json")
    json.dump(data, open(out, "w"))
    report(data)
    print("layout bytes:", len(data["layout"]), "->", out)
