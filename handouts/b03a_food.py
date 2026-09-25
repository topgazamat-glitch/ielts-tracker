"""Beginner 3A - Say what you eat and drink. A twelve-page paper handout.

Follows Empower Starter (A1) Unit 3A: present simple I / you / we / they,
Food 1, syllables and word stress, and the sound and spelling of /ɪ/, /iː/
and /aɪ/. The listening is the coursebook's own track 03.07, and the reading
follows the Student's Book text Food for One Week.

Written in Azamat's design: see handouts/booklet_docx.py for the four things
he asked to be fixed and where each one lives.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import booklet_docx as B

UNIT, LEVEL = "UNIT 3  ·  FOOD AND DRINK", "A1 BEGINNER"
TITLE = "Food and drink"
LESSON = "Lesson 3A  ·  Say what you eat and drink"
STRAP = ("present simple I / you / we / they  ·  food  ·  "
         "syllables and word stress")

blocks = []
A = blocks.append

A(B.cover(
    UNIT, LEVEL, TITLE, LESSON, STRAP,
    # the pages the parts really start on, read back off the rendered PDF
    # by handouts/check_booklet.py
    contents=[("Reading — what three families eat in a week", 1),
              ("Language — I eat, you eat, we eat, they eat", 4),
              ("Vocabulary — food, and where the stress falls", 7),
              ("Listening — what does Rajit eat?", 9),
              ("Sound and spelling — /ɪ/, /iː/ and /aɪ/", 11)],
    learn=["name the food you eat and drink every week",
           "say I eat / I don't eat and I like / I don't like",
           "ask Do you eat …? and answer Yes, I do / No, I don't",
           "count the syllables in a food word and hear the strong one",
           "hear the difference between sit, seat and site"]))

# Part 1 opens on page one, under the cover - that is how his own booklet
# runs, and it is why his contents list starts at page 1 rather than page 2.

# ------------------------------------------------------------------ 1
A(B.section(1, "Reading  ·  what three families eat in a week"))
A(B.exercise("1.1", "Tick (✓) the food you ate yesterday."))
A(B.two_columns(["meat", "fish", "rice", "bread", "fruit", "vegetables",
                 "eggs", "cheese"], dotted=0))
A(B.panel("KEY WORDS", [
    ("a meal", "breakfast, lunch or dinner"),
    ("fresh", "not old — picked or made today"),
    ("a market", "a place outside where people sell food"),
    ("the same", "not different"),
]))
A(B.reading("FOOD FOR ONE WEEK", [
    "A photographer visits three families. Every family puts all its food "
    "for one week on the table. Then he takes a photograph. The three "
    "photographs are very different.",
    "THE AYUBOV FAMILY live in Uzbekistan. There are six people. On their "
    "table there is a lot of bread, rice, vegetables and fruit. There is "
    "meat, but not a lot. They buy everything at the market on Sunday "
    "morning. They do not buy food in boxes.",
    "THE BAKER FAMILY live in England. There are four people. On their "
    "table there is a lot of food in boxes and bottles. There is pizza, "
    "there is cola, and there are eleven bags of crisps. There is fruit "
    "too, but it is at the back of the table.",
    "THE SATO FAMILY live in Japan. There are five people. There is fish "
    "on their table, and rice, and a lot of small vegetables. There is not "
    "much bread. They eat fish four or five times a week.",
    "Three families, three tables, one week. Look at your own table. What "
    "does it say about you?",
]))
A(B.exercise("1.2", "Which family? Write A (Ayubov), B (Baker) or S (Sato)."))
A(B.two_columns(["They eat a lot of fish.",
                 "They buy food at the market.",
                 "They have a lot of food in boxes.",
                 "There are six people.",
                 "They do not eat much bread.",
                 "They have eleven bags of crisps."]))
A(B.exercise("1.3", "True (T) or false (F)?"))
A(B.two_columns(["The photographer takes three photographs.",
                 "The Ayubov family buy food on Monday.",
                 "The Baker family have no fruit.",
                 "The Sato family eat fish every day.",
                 "All three tables are the same.",
                 "The Ayubov family eat a lot of meat."]))
A(B.exercise("1.4", "Complete the sentences with a word from the text."))
A(B.questions(["The Ayubov family go to the ……………… on Sunday.",
               "The Baker family drink ……………… .",
               "The Sato family eat fish four or five ……………… a week.",
               "Fruit is at the ……………… of the Baker family's table.",
               "The photographer takes a ……………… of every family."], dotted=0))
A(B.exercise("1.5", "Complete the table about the three families."))
A(B.panel("WHAT IS ON THE TABLE?", [
    "Ayubov  ·  people: ……   ·  a lot of: …………………………  ·  not much: …………………",
    "Baker    ·  people: ……   ·  a lot of: …………………………  ·  not much: …………………",
    "Sato      ·  people: ……   ·  a lot of: …………………………  ·  not much: …………………",
], fill=B.PANEL2))
A(B.exercise("1.6", "Answer the questions. Then ask your partner."))
A(B.questions(["Which family eats like your family? Why?",
               "What is on your table every week?",
               "What is never on your table?"], dotted=26))

A(B.page_break())

# ------------------------------------------------------------------ 2
A(B.section(2, "Language  ·  I eat, you eat, we eat, they eat"))
A(B.panel("PRESENTATION", [
    "With I, you, we and they the verb does not change. Not one letter. "
    "I eat · you eat · we eat · they eat.",
    "✓ I eat bread every day.   ✓ We drink tea in the morning.   "
    "✓ They live in Japan.",
    "For NO, put don't in front of the verb. The verb still does not "
    "change. I don't eat fish. · We don't buy food in boxes.",
    "For a QUESTION, put Do in front. Do you eat meat? · Do they like "
    "rice? The verb stays the same again: eat, like, drink.",
    "Short answers: Yes, I do. / No, I don't. Do not say Yes, I eat.",
], fill=B.PANEL))
A(B.warning("ERROR WARNING", [
    "1  Do not add -s. ✗ I eats bread. → ✓ I eat bread. The -s is for "
    "he, she and it, and that is Unit 4.",
    "2  Do not forget don't. ✗ I no eat fish. → ✓ I don't eat fish.",
    "3  One verb only after don't. ✗ I don't eats. → ✓ I don't eat.",
    "4  Do, not Are. ✗ Are you eat meat? → ✓ Do you eat meat?",
]))
A(B.exercise("2.1", "Underline the correct word."))
A(B.questions(["I eat / eats rice every day.",
               "We don't / doesn't drink cola.",
               "Do / Are you like fish?",
               "They live / lives in England.",
               "I don't eat / eats vegetables.",
               "Do they buy / buys bread at the market?"], dotted=0))
A(B.exercise("2.2", "Write the sentence again with don't."))
A(B.questions(["I eat fish.  ……………………………………………………",
               "We buy food in boxes.  ……………………………………………………",
               "They drink coffee.  ……………………………………………………",
               "I like cheese.  ……………………………………………………"], dotted=0))
A(B.exercise("2.3", "Write the question with Do."))
A(B.questions(["you / eat / meat  ……………………………………………………… ?",
               "they / like / fruit  ……………………………………………………… ?",
               "we / need / bread  ……………………………………………………… ?",
               "you / drink / tea  ……………………………………………………… ?"], dotted=0))
A(B.exercise("2.4", "Complete the conversation."))
A(B.panel("AT LUNCH", [
    "A  ……………… (1) you like fish?    B  No, I ……………… (2). I don't eat "
    "fish at all.",
    "A  ……………… (3) you eat meat?    B  Yes, I ……………… (4). I eat meat "
    "two times a week.",
    "A  And your family? ……………… (5) they eat meat too?",
    "B  My brother ……………… (6). He ……………… (7) eat meat or fish. He eats "
    "vegetables and rice.",
], fill=B.PANEL2))
A(B.exercise("2.5", "Find and correct the mistake. TWO are correct — tick them."))
A(B.questions(["I eats bread every morning.",
               "We don't drink cola.",
               "Are you like vegetables?",
               "They don't eats fish.",
               "Do you buy fruit at the market?",
               "I no like cheese."], dotted=0))
A(B.exercise("2.6", "Write true sentences about you. Use eat, drink, like."))
A(B.questions(["Every day I ………………………………………………………………",
               "I don't ………………………………………………………………",
               "In my family we ………………………………………………………………",
               "My friends ………………………………………………………………"], dotted=0))
A(B.exercise("2.7", "Complete with eat, eats, don't or do."))
A(B.questions(["I ……………… bread every morning.",
               "……………… you like coffee?",
               "We ……………… eat meat on Friday.",
               "They ……………… a lot of fish in Japan.",
               "A  Do you drink tea?   B  Yes, I ……………… .",
               "A  Do they eat eggs?   B  No, they ……………… ."], dotted=0))
A(B.exercise("2.8", "Write about your family. Three sentences with we, one "
                    "with we don't."))
A(B.questions(["………………………………………………………………………………",
               "………………………………………………………………………………",
               "………………………………………………………………………………",
               "………………………………………………………………………………"], dotted=0))
A(B.exercise("2.9", "Work in pairs. Ask six Do you …? questions. Write your "
                    "partner's answers."))
A(B.two_columns(["meat", "fish", "eggs", "cheese", "fruit", "cola"], dotted=10))

A(B.page_break())

# ------------------------------------------------------------------ 3
A(B.section(3, "Vocabulary  ·  food, and where the stress falls"))
A(B.panel("FOOD 1", [
    "meat · fish · chicken · eggs · cheese · bread · rice · fruit · "
    "vegetables · water · tea · coffee",
    "We say a lot of with all of them: a lot of rice, a lot of eggs.",
    "Some of these words have no plural. ✓ rice   ✗ rices   ✓ bread   "
    "✗ breads   ✓ water   ✗ waters",
]))
A(B.exercise("3.1", "Food or drink? Write F or D."))
A(B.two_columns(["tea", "bread", "water", "rice", "coffee", "cheese"]))
A(B.exercise("3.2", "One word is different. Circle it."))
A(B.questions(["meat · chicken · fish · bread",
               "tea · coffee · water · rice",
               "apple · banana · egg · orange",
               "vegetables · fruit · cheese · carrot"], dotted=0))
A(B.panel("SYLLABLES AND WORD STRESS", [
    "A syllable is a beat. Clap the word. bread = 1 beat. chicken = 2 "
    "beats. vegetables = 3 beats.",
    "One beat in every word is STRONGER than the others. CHIcken, not "
    "chiCKEN. BAnana is wrong — it is baNAna.",
    "Get the strong beat wrong and people do not hear the word, even when "
    "every sound is correct. This is why stress matters.",
], fill=B.PANEL2))
A(B.exercise("3.3", "How many syllables? Write 1, 2 or 3."))
A(B.two_columns(["fish", "coffee", "vegetables", "rice", "chicken",
                 "banana"]))
A(B.exercise("3.4", "Which beat is strong? Underline it."))
A(B.questions(["cof-fee", "ba-na-na", "chick-en", "to-ma-to",
               "veg-e-ta-bles", "po-ta-to"], dotted=0))
A(B.exercise("3.5", "Listen and repeat. Then say them to your partner. "
                    "Track 03.02."))
A(B.two_columns(["water", "orange", "potato", "bread", "tomato",
                 "cheese"], dotted=0))
A(B.exercise("3.6", "Write the food. The first letter is there."))
A(B.questions(["It is white and we eat a lot of it in Uzbekistan.  r…………",
               "It comes from a chicken and it is small.  e…………",
               "It swims.  f…………",
               "It is yellow and it comes from milk.  c…………"], dotted=0))
A(B.exercise("3.7", "Put the words in the right group."))
A(B.panel("THREE GROUPS", [
    "bread · chicken · tea · apple · fish · water · rice · banana · "
    "coffee · meat · orange · milk",
    "FROM AN ANIMAL  ………………………………………………………………………",
    "FROM A PLANT  ………………………………………………………………………",
    "YOU DRINK IT  ………………………………………………………………………",
], fill=B.PANEL2))
A(B.exercise("3.8", "Correct the spelling."))
A(B.two_columns(["chiken  →  ………………", "vegatables  →  ………………",
                 "bananna  →  ………………", "potatos  →  ………………",
                 "brede  →  ………………", "coffe  →  ………………"], dotted=0))
A(B.exercise("3.9", "Work in pairs. Say a food word. Your partner claps the "
                    "syllables and says the strong one."))

A(B.page_break())

# ------------------------------------------------------------------ 4
A(B.section(4, "Listening  ·  what does Rajit eat?"))
A(B.listening("03.07", [
    "Rajit is talking to a friend about food. The friend asks him what he "
    "eats and what he does not eat.",
]))
A(B.exercise("4.1", "Listen once. What four things does Rajit eat?"))
A(B.two_columns(["……………………", "……………………", "……………………", "……………………"],
                dotted=0))
A(B.exercise("4.2", "Listen again. Tick (✓) YES or NO."))
A(B.panel("DOES RAJIT EAT IT?", [
    "meat           …… yes      …… no",
    "fish             …… yes      …… no",
    "vegetables  …… yes      …… no",
    "eggs            …… yes      …… no",
    "rice             …… yes      …… no",
], fill=B.PANEL2))
A(B.exercise("4.3", "Listen once more and complete the conversation. Track 03.08."))
A(B.questions(["A  ……………… you eat meat?",
               "B  No, I ……………… . I don't eat meat and I don't eat chicken.",
               "A  ……………… you like fish?",
               "B  Yes, I ……………… . I eat fish two or three ……………… a week.",
               "A  And ……………… ?",
               "B  Rice, vegetables, fruit. I eat a lot of ……………… ."],
              dotted=0))
A(B.panel("WHY YOU DIDN'T HEAR IT", [
    "In a question, do is very short and very quiet. Do you eat meat? "
    "sounds almost like d'you eat meat?",
    "So do not listen for do. Listen for the verb — eat, like, drink — and "
    "the question is already there.",
    "And don't sounds like doan in fast speech. The t almost disappears. "
    "I doan eat fish.",
], fill=B.PANEL))
A(B.exercise("4.4", "Now you. Ask your partner and complete the table."))
A(B.panel("MY PARTNER", [
    "Eats every day:  …………………………………………………………………",
    "Never eats:  …………………………………………………………………",
    "Drinks in the morning:  …………………………………………………………………",
    "Does not like:  …………………………………………………………………",
], fill=B.PANEL2))
A(B.exercise("4.5", "Listen again. Are the sentences true (T) or false (F)?"))
A(B.two_columns(["Rajit eats meat.",
                 "Rajit likes fish.",
                 "Rajit eats fish once a week.",
                 "Rajit eats a lot of fruit.",
                 "Rajit drinks coffee.",
                 "Rajit's family eat the same food."]))
A(B.exercise("4.6", "Tell the class about your partner. Use They eat / "
                    "They don't eat."))

A(B.page_break())

# ------------------------------------------------------------------ 5
A(B.section(5, "Sound and spelling  ·  /ɪ/, /iː/ and /aɪ/"))
A(B.panel("PRESENTATION", [
    "Three sounds, and the letter i can be all three of them.",
    "/ɪ/  short, quick — fish · chicken · milk · big · sit",
    "/iː/  long — eat · meat · cheese · tea · seat",
    "/aɪ/  two sounds together — rice · like · time · white · site",
    "sit · seat · site are three different words. The consonants are the "
    "same. Only the middle sound changes, and it changes everything.",
], fill=B.PANEL))
A(B.exercise("5.1", "Which sound? Write 1 (/ɪ/), 2 (/iː/) or 3 (/aɪ/). "
                    "Track 03.03."))
A(B.two_columns(["fish", "rice", "cheese", "milk", "like", "meat"]))
A(B.exercise("5.2", "One word is different. Circle it."))
A(B.questions(["fish · milk · rice · chicken",
               "eat · meat · sit · tea",
               "like · time · white · big",
               "cheese · seat · fish · tea"], dotted=0))
A(B.exercise("5.3", "Say these pairs out loud. Your partner says which one "
                    "you said."))
A(B.two_columns(["sit / seat", "fill / feel", "rich / reach",
                 "live / leave", "chip / cheap", "is / eyes"], dotted=0))
A(B.exercise("5.4", "Write the word. All of them have /iː/."))
A(B.two_columns(["m _ _ t  (you eat it)", "ch _ _ se  (from milk)",
                 "t _ _  (you drink it)", "_ _ t  (with your mouth)"],
                dotted=0))
A(B.exercise("5.5", "Read the sentence out loud. Be careful with the "
                    "underlined words."))
A(B.questions(["I eat fish, but I don't like chicken.",
               "We drink tea at six, not coffee.",
               "Rice is white and cheese is yellow.",
               "I like this, and I don't like that."], dotted=0))
A(B.panel("WRITING  ·  what you eat in a week", [
    "Write about the food in your home for one week. Use I eat, we eat, "
    "I don't eat, we buy.",
    "Say what you eat every day, what you eat two or three times a week, "
    "and one thing you never eat.",
    "Write about 60 words.",
], fill=B.PANEL2))
A(B.writing_lines(60))
A(B.exercise("5.6", "Read your writing to your partner. Your partner asks "
                    "you two questions with Do you …?"))

out = os.path.expanduser(
    "~/Desktop/Handouts/A1 Beginner/B03A Food and drink/"
    "B03A Food and drink — handout.docx")
B.write(out, blocks, "3", TITLE, "Lesson 3A", "A1 Beginner")
print("wrote", out)
print("blocks:", len(blocks))
