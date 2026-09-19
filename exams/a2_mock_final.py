"""An original A2 mock final, built to the shape of the real papers.

Azamat has the real Test 1 and Test 2 finals and cannot hand them out - they
are what the students will sit. This is a new paper with the same skeleton, so
practising on it rehearses the exam rather than the answers:

    LISTENING            20 marks   four parts, each heard twice
      Part 1  1-5        five short conversations, three options
      Part 2  6-10       match five speakers to eight options
      Part 3  11-15      one longer conversation, three options
      Part 4  16-20      complete the notes with a word or a number

    READING & WRITING    25 marks + the email
      Part 1  1-5        match five sentences to eight notices
      Part 2  6-10       one word in each gap, three options
      Part 3  11-15      read an article, three options
      Part 4  16-20      grammar in a text, three options
      Part 5  21-25      write ONE word in each gap
      Writing            an email of about 50 words, four things to include

Vocabulary is kept inside A2: the language of the real papers, not harder.
"""

# --------------------------------------------------------------- LISTENING

# Each line is (voice, words). The voices are British so the paper sounds
# like the exam; a narrator reads the instructions and the question numbers.
NARRATOR = "Daniel"
MAN, WOMAN, MAN2, WOMAN2 = "Rocko", "Shelley", "Reed", "Flo (English (UK))"

PART1 = [
    {
        "q": 1, "ask": "What will Tom have for breakfast?",
        "options": ["Toast", "Eggs", "Fruit"], "answer": "C",
        "lines": [
            (WOMAN, "Tom, there's bread if you want toast."),
            (MAN, "Thanks, Mum, but I had toast yesterday and the day before."),
            (WOMAN, "There are eggs as well."),
            (MAN, "No, I'm late. I'll just take an apple and a banana."),
        ],
    },
    {
        "q": 2, "ask": "How will Sara go to the city centre?",
        "options": ["By bus", "By train", "On foot"], "answer": "B",
        "lines": [
            (MAN, "Are you walking to the centre, Sara?"),
            (WOMAN, "It's too far today. I wanted the bus, but there isn't one until four."),
            (MAN, "So what will you do?"),
            (WOMAN, "There's a train at half past two. I'll take that."),
        ],
    },
    {
        "q": 3, "ask": "How much does the small bag cost?",
        "options": ["Fifteen pounds", "Thirty pounds", "Fifty pounds"],
        "answer": "A",
        "lines": [
            (WOMAN, "Excuse me, how much is this black bag?"),
            (MAN2, "The big one is thirty pounds."),
            (WOMAN, "And the small one next to it?"),
            (MAN2, "That one is fifteen. The red bag is fifty, but it's leather."),
        ],
    },
    {
        "q": 4, "ask": "What time does the film start?",
        "options": ["Six o'clock", "Half past six", "Seven o'clock"],
        "answer": "C",
        "lines": [
            (MAN, "The film starts at half past six, doesn't it?"),
            (WOMAN2, "It did last week. They changed it."),
            (MAN, "Oh no. Is it six now?"),
            (WOMAN2, "No, later. Seven. We've got plenty of time."),
        ],
    },
    {
        "q": 5, "ask": "Where is the post office?",
        "options": ["Next to the bank", "Opposite the school",
                    "Behind the library"], "answer": "B",
        "lines": [
            (MAN2, "Excuse me, is the post office next to the bank?"),
            (WOMAN, "It was, but it moved in the summer."),
            (MAN2, "Is it behind the library now?"),
            (WOMAN, "No, it's opposite the school. Two minutes from here."),
        ],
    },
]

PART2 = {
    "intro": "Listen to Anna telling a friend about her family's weekend. "
             "What is each person going to do? For questions 6 to 10, write a "
             "letter A to H next to each person.",
    "people": [("6", "Anna"), ("7", "Her brother"), ("8", "Her mother"),
               ("9", "Her father"), ("10", "Her grandmother")],
    "options": [("A", "go swimming"), ("B", "visit a museum"),
                ("C", "play football"), ("D", "cook a big lunch"),
                ("E", "work in the garden"), ("F", "go shopping"),
                ("G", "stay at home and read"), ("H", "meet friends in a café")],
    "answers": {"6": "H", "7": "C", "8": "F", "9": "E", "10": "D"},
    "lines": [
        (MAN, "Are you all busy this weekend, Anna?"),
        (WOMAN, "Everybody is doing something different. I'm meeting friends "
                "in that new café near the station."),
        (MAN, "Nice. And your brother? Is he going swimming again?"),
        (WOMAN, "He wanted to, but his team has a match, so he's playing "
                "football instead."),
        (MAN, "What about your mother?"),
        (WOMAN, "She's going shopping in the morning. She says she needs "
                "shoes, but she always says that."),
        (MAN, "And your father? Is he going with her?"),
        (WOMAN, "No, he hates shopping. He's going to work in the garden all "
                "day. He loves it."),
        (MAN, "And your grandmother? Is she staying at home and reading?"),
        (WOMAN, "She's at home, yes, but she isn't reading. She's cooking a "
                "big lunch for all of us on Sunday."),
    ],
}

PART3 = {
    "intro": "Listen to Mr Blake talking to a woman at a hotel about his stay. "
             "For questions 11 to 15, tick A, B or C.",
    "questions": [
        {"q": 11, "stem": "Mr Blake is staying for",
         "options": ["two nights.", "three nights.", "four nights."],
         "answer": "B"},
        {"q": 12, "stem": "His room is on the",
         "options": ["first floor.", "second floor.", "third floor."],
         "answer": "C"},
        {"q": 13, "stem": "Breakfast finishes at",
         "options": ["nine o'clock.", "half past nine.", "ten o'clock."],
         "answer": "B"},
        {"q": 14, "stem": "The swimming pool is",
         "options": ["next to the restaurant.", "under the hotel.",
                     "closed this week."], "answer": "C"},
        {"q": 15, "stem": "He wants the hotel to",
         "options": ["book a taxi.", "carry his bags.", "wash his clothes."],
         "answer": "A"},
    ],
    "lines": [
        (WOMAN2, "Good evening, sir. Do you have a booking?"),
        (MAN, "Yes, Blake. I booked two nights, but I'd like to stay one more, "
              "so three altogether."),
        (WOMAN2, "That's fine, Mr Blake. Room 312, on the third floor. The "
                 "lift is behind you."),
        (MAN, "Thank you. What time is breakfast?"),
        (WOMAN2, "From seven until half past nine. Some hotels finish at nine, "
                 "but we give you the extra half hour."),
        (MAN, "Good. And is there a swimming pool? I read about one."),
        (WOMAN2, "There is, next to the restaurant, but I'm afraid it's closed "
                 "this week. They're cleaning it."),
        (MAN, "Never mind. One more thing - I have a train early on Friday. "
              "Could you book me a taxi for six in the morning?"),
        (WOMAN2, "Of course. Would you like someone to carry your bags up now?"),
        (MAN, "No, thank you, they're light. Just the taxi, please."),
    ],
}

PART4 = {
    "intro": "You will hear a woman asking about English classes at a language "
             "school. Listen and complete questions 16 to 20.",
    "title": "RIVERSIDE LANGUAGE SCHOOL",
    "gaps": [
        {"q": 16, "label": "Classes start on", "answer": "Monday"},
        {"q": 17, "label": "Lessons begin at", "answer": "6.30"},
        {"q": 18, "label": "The course is", "answer": "(eight) weeks",
         "hint": "…………… weeks"},
        {"q": 19, "label": "Teacher's name", "answer": "Ferrari"},
        {"q": 20, "label": "Students must bring a", "answer": "dictionary"},
    ],
    "lines": [
        (WOMAN, "Good afternoon. I'd like to ask about your evening English "
                "classes."),
        (MAN2, "Certainly. The new group starts next Monday."),
        (WOMAN, "Not Tuesday? My friend said Tuesday."),
        (MAN2, "Tuesday was the old group. This one is Monday."),
        (WOMAN, "And what time do the lessons begin?"),
        (MAN2, "Half past six, and they finish at eight."),
        (WOMAN, "How long is the course?"),
        (MAN2, "Eight weeks. There's a longer course of twelve weeks in "
               "January, but this one is eight."),
        (WOMAN, "Who is the teacher?"),
        (MAN2, "Her name is Miss Ferrari. That's F - E - R - R - A - R - I."),
        (WOMAN, "Thank you. Do I need a book?"),
        (MAN2, "We give you the book. But please bring a dictionary. Every "
               "student needs one."),
    ],
}


# ----------------------------------------------------- READING AND WRITING

R_PART1 = {
    "intro": "Which notice (A-H) says this (1-5)? For questions 1 to 5, mark "
             "the correct letter A-H on the answer sheet.",
    "notices": [
        ("A", "PLEASE PAY HERE BEFORE YOU SIT DOWN"),
        ("B", "NO FOOD OR DRINK IN THE COMPUTER ROOM"),
        ("C", "LIFT OUT OF ORDER - PLEASE USE THE STAIRS"),
        ("D", "CLOSED FOR LUNCH 1 - 2 P.M."),
        ("E", "BOOKS MUST BE RETURNED WITHIN TWO WEEKS"),
        ("F", "TICKETS ARE CHEAPER IF YOU BUY THEM ONLINE"),
        ("G", "PLEASE TURN OFF YOUR PHONE DURING THE FILM"),
        ("H", "WET PAINT - DO NOT TOUCH"),
    ],
    "items": [
        (1, "You cannot use this to go upstairs today.", "C"),
        (2, "You must keep this book for fourteen days only.", "E"),
        (3, "You will pay less if you do not buy your ticket at the door.", "F"),
        (4, "You cannot come in at this time in the middle of the day.", "D"),
        (5, "You must not eat in this room.", "B"),
    ],
}

R_PART2 = {
    "intro": "Read the sentences about a train journey and choose the correct "
             "answer for each gap.",
    "items": [
        (6, "You must ……………… your ticket before you get on the train.",
         ["buy", "pay", "take"], "A"),
        (7, "The train to Bukhara ……………… from platform four.",
         ["goes", "leaves", "starts"], "B"),
        (8, "Please do not ……………… your bags on the seat.",
         ["put", "give", "bring"], "A"),
        (9, "If the train is late, you can ……………… for your money back.",
         ["tell", "say", "ask"], "C"),
        (10, "There is a café at the ……………… of the train.",
         ["front", "first", "beginning"], "A"),
    ],
}

R_PART3 = {
    "intro": "Read the article about Nodira and answer the questions. For each "
             "question, mark A, B or C on the answer sheet.",
    "title": "THE YOUNGEST COOK IN THE KITCHEN",
    "text": [
        "Nodira Rashidova is twenty-two, and she is the youngest cook in one "
        "of the busiest restaurants in Tashkent. She did not go to a cooking "
        "school. She learned everything from her grandmother, who cooked for "
        "a large family every day for forty years.",
        "When Nodira left school she wanted to be a doctor, and she studied "
        "for a year at university. Then her grandmother became ill, and "
        "Nodira cooked for the family for six months. She says those six "
        "months changed her life. She left the university and asked for work "
        "in a restaurant. At first they gave her the vegetables to wash.",
        "Now she makes the soup for two hundred people a day. She arrives at "
        "six in the morning, before anybody else, because she likes the "
        "kitchen when it is quiet. She says the hardest part of the job is "
        "not the cooking; it is standing up for ten hours.",
        "Her grandmother is well again and comes to the restaurant once a "
        "month. She always orders the soup, and she always says it needs a "
        "little more salt.",
    ],
    "questions": [
        {"q": 11, "stem": "Nodira learned to cook",
         "options": ["at a cooking school.", "from her grandmother.",
                     "at the restaurant."], "answer": "B"},
        {"q": 12, "stem": "Before she cooked, Nodira wanted to be",
         "options": ["a doctor.", "a teacher.", "a cook."], "answer": "A"},
        {"q": 13, "stem": "Her first job in the restaurant was",
         "options": ["making soup.", "washing vegetables.",
                     "serving customers."], "answer": "B"},
        {"q": 14, "stem": "Nodira comes to work early because",
         "options": ["the buses are empty.", "the kitchen is quiet.",
                     "she starts the soup."], "answer": "B"},
        {"q": 15, "stem": "Nodira says the most difficult thing is",
         "options": ["cooking for many people.", "working with her family.",
                     "being on her feet all day."], "answer": "C"},
    ],
}

R_PART4 = {
    "intro": "Read the article about camels and answer the questions. For each "
             "question, mark A, B or C on the answer sheet.",
    "title": "THE CAMEL",
    "text": ("A camel can walk 16 …………… the desert for two weeks without "
             "water. People often think that a camel keeps water 17 …………… its "
             "back, but this is not true. The thing on its back is fat, and "
             "the fat gives the camel energy 18 …………… there is no food. A "
             "camel can drink a hundred litres of water in ten minutes, which "
             "is 19 …………… than most animals can drink in a day. Long ago, "
             "people 20 …………… camels to carry salt and cloth across Asia, and "
             "in some places they still do."),
    "items": [
        (16, ["across", "between", "along"], "A"),
        (17, ["on", "in", "at"], "B"),
        (18, ["so", "when", "because"], "B"),
        (19, ["much", "more", "most"], "B"),
        (20, ["use", "used", "using"], "B"),
    ],
}

R_PART5 = {
    "intro": "Read the text. Think of the word which fits each gap. Write ONE "
             "word for each gap.",
    "letters": [
        ("Dear Sir or Madam,",
         "I (Example: saw) your advertisement for summer jobs at the hotel. "
         "I am a student 21 …………… Samarkand and I am free from June 22 "
         "…………… the end of August. I have worked in a café, 23 …………… I have "
         "never worked in a hotel. Could you tell me 24 …………… much the work "
         "is each week? I hope to hear from you soon.",
         "Yours faithfully,\nDilnoza Karimova"),
        ("Dear Miss Karimova,",
         "Thank you 25 …………… your letter. We need three students this summer. "
         "The work is thirty hours a week and we will show you everything on "
         "the first day. Please telephone me on Monday morning.",
         "Yours sincerely,\nJames Porter"),
    ],
    "answers": {21: "in / from", 22: "until / till / to", 23: "but",
                24: "how", 25: "for"},
}

WRITING = {
    "task": "Write an email to an English friend. You are going to move to a "
            "new flat. Include:",
    "points": ["where the new flat is",
               "when you are moving",
               "what you like about it",
               "invite your friend to come and see it"],
    "words": "Write at least 50 words.",
}
