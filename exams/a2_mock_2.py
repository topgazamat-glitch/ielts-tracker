"""A2 mock final, paper 2. Same skeleton and same level as the real finals.

    LISTENING            20 marks   four parts, each heard twice
    READING & WRITING    25 marks + the email

Built to the measurements of Azamat's Test 1 and Test 2 finals: the Part 3
article is 180-200 words at 10-15 words a sentence, and the words are the
words of those papers. Checked by exams/check_paper.py.
"""

NARRATOR = "Daniel"
MAN, WOMAN, MAN2, WOMAN2 = "Rocko", "Shelley", "Reed", "Flo (English (UK))"

PART1 = [
    {
        "q": 1, "ask": "What did the woman lose?",
        "options": ["Her keys", "Her umbrella", "Her gloves"], "answer": "B",
        "lines": [
            (MAN2, "Good morning. Did you leave something on the bus?"),
            (WOMAN, "Yes. I thought it was my gloves, but now I can't find my "
                    "umbrella either."),
            (MAN2, "We have two pairs of gloves here, but no umbrella."),
            (WOMAN, "Oh, the gloves are in my bag. So it's the umbrella."),
        ],
    },
    {
        "q": 2, "ask": "What will they buy for Grandad?",
        "options": ["A book", "A shirt", "A cake"], "answer": "A",
        "lines": [
            (WOMAN2, "Shall we get Grandad a shirt for his birthday?"),
            (MAN, "He has too many shirts. Mum is making the cake."),
            (WOMAN2, "Then what?"),
            (MAN, "He reads every evening. Let's find him a book about "
                  "old trains."),
        ],
    },
    {
        "q": 3, "ask": "What time does the shop close today?",
        "options": ["At five", "At six", "At eight"], "answer": "B",
        "lines": [
            (WOMAN, "Excuse me, do you close at eight?"),
            (MAN2, "Only on Fridays. Today we close at six."),
            (WOMAN, "Not five? The door says five."),
            (MAN2, "That's the old sign. Six, every day except Friday."),
        ],
    },
    {
        "q": 4, "ask": "Where will they meet?",
        "options": ["At the station", "Outside the cinema",
                    "In the café"], "answer": "C",
        "lines": [
            (MAN, "Shall I wait for you outside the cinema?"),
            (WOMAN2, "It's cold. Let's meet at the station instead."),
            (MAN, "The station is always full at six."),
            (WOMAN2, "True. The café next to it, then. I'll get us a table."),
        ],
    },
    {
        "q": 5, "ask": "How many people are coming to dinner?",
        "options": ["Six", "Eight", "Ten"], "answer": "B",
        "lines": [
            (WOMAN, "Is it ten people on Saturday?"),
            (MAN2, "It was, but the Petrovs can't come."),
            (WOMAN, "So six?"),
            (MAN2, "No, eight. Your sister is bringing her husband."),
        ],
    },
]

PART2 = {
    "intro": "Listen to Daniel telling a friend about the people in his "
             "family and their free time. What does each person do? For "
             "questions 6 to 10, write a letter A to H next to each person.",
    "people": [("6", "Daniel"), ("7", "His sister"), ("8", "His uncle"),
               ("9", "His mother"), ("10", "His cousin")],
    "options": [("A", "plays tennis"), ("B", "goes running"),
                ("C", "paints pictures"), ("D", "grows vegetables"),
                ("E", "sings in a group"), ("F", "rides a bicycle"),
                ("G", "takes photographs"), ("H", "plays the guitar")],
    "answers": {"6": "F", "7": "E", "8": "D", "9": "G", "10": "A"},
    "lines": [
        (WOMAN2, "Does everybody in your family do something, Daniel?"),
        (MAN, "More or less. I go running in the winter, but in the summer "
              "I'm on my bicycle every evening."),
        (WOMAN2, "And your sister? Does she run with you?"),
        (MAN, "Never. She sings in a group with four other girls. They "
              "practise on Thursdays."),
        (WOMAN2, "What about your uncle?"),
        (MAN, "He has a big garden behind his house and grows vegetables. "
              "He gives us tomatoes all summer."),
        (WOMAN2, "Does your mother help him in the garden?"),
        (MAN, "She doesn't like the garden. She takes photographs. There are "
              "hundreds of them on the walls at home."),
        (WOMAN2, "And your cousin? Does he paint like his father?"),
        (MAN, "His father paints, yes, but my cousin plays tennis. He's at "
              "the club every Saturday morning."),
    ],
}

PART3 = {
    "intro": "Listen to Mrs Carter talking to a man at a sports centre about "
             "joining. For questions 11 to 15, tick A, B or C.",
    "questions": [
        {"q": 11, "stem": "The sports centre opens at",
         "options": ["six.", "seven.", "eight."], "answer": "B"},
        {"q": 12, "stem": "Mrs Carter wants to",
         "options": ["swim.", "play tennis.", "use the gym."], "answer": "A"},
        {"q": 13, "stem": "A month costs",
         "options": ["twenty pounds.", "twenty-five pounds.",
                     "thirty pounds."], "answer": "C"},
        {"q": 14, "stem": "The swimming pool is closed on",
         "options": ["Monday.", "Wednesday.", "Sunday."], "answer": "B"},
        {"q": 15, "stem": "She must bring",
         "options": ["a towel.", "a photograph.", "a letter."], "answer": "B"},
    ],
    "lines": [
        (WOMAN, "Hello. I'd like to join the centre. What time do you open?"),
        (MAN2, "Seven in the morning, and we close at ten at night. The café "
               "opens at eight."),
        (WOMAN, "Good. I want to swim before work."),
        (MAN2, "Not the gym or the tennis courts?"),
        (WOMAN, "Only the pool. I swim every morning."),
        (MAN2, "Then that's thirty pounds a month. Twenty-five is the gym "
               "only, and twenty is for students."),
        (WOMAN, "Thirty is fine. Is the pool open every day?"),
        (MAN2, "Every day except Wednesday. We clean it on Wednesdays. The "
               "gym stays open, and on Monday everything is open."),
        (WOMAN, "I see. Do I need to bring anything?"),
        (MAN2, "A photograph for your card. We have towels here, and you "
               "don't need a letter from anybody."),
    ],
}

PART4 = {
    "intro": "You will hear a teacher telling students about a school trip. "
             "Listen and complete questions 16 to 20.",
    "title": "SCHOOL TRIP",
    "gaps": [
        {"q": 16, "label": "Day of the trip", "answer": "Thursday"},
        {"q": 17, "label": "The bus leaves at", "answer": "7.45"},
        {"q": 18, "label": "We are going to the", "answer": "castle"},
        {"q": 19, "label": "Bring money for", "answer": "lunch"},
        {"q": 20, "label": "Give the letter to Mr", "answer": "Dalton"},
    ],
    "lines": [
        (MAN, "Listen, everybody. The trip is next week."),
        (WOMAN2, "Is it Tuesday, sir?"),
        (MAN, "It was Tuesday, but the museum changed it. Thursday now. "
              "Write that down."),
        (WOMAN2, "What time do we meet?"),
        (MAN, "Be at school by half past seven. The bus leaves at quarter to "
              "eight and it will not wait."),
        (WOMAN2, "And where are we going?"),
        (MAN, "In the morning we visit the castle, and after that we walk "
              "down to the river."),
        (WOMAN2, "Do we need money?"),
        (MAN, "The trip is free, but bring money for lunch. There is a café, "
              "or you can bring sandwiches."),
        (WOMAN2, "Who do we give the letter to?"),
        (MAN, "Give it to Mr Dalton, not to me. D - A - L - T - O - N. "
              "Before Friday, please."),
    ],
}


# ----------------------------------------------------- READING AND WRITING

R_PART1 = {
    "intro": "Which notice (A-H) says this (1-5)? For questions 1 to 5, mark "
             "the correct letter A-H on the answer sheet.",
    "notices": [
        ("A", "PLEASE LEAVE YOUR BAGS AT THE DESK"),
        ("B", "NO PARKING IN FRONT OF THESE DOORS"),
        ("C", "THIS MACHINE DOES NOT GIVE CHANGE"),
        ("D", "SWIMMING POOL CLOSED FOR CLEANING"),
        ("E", "CHILDREN UNDER 12 MUST BE WITH AN ADULT"),
        ("F", "LAST TRAIN LEAVES AT 11.30 P.M."),
        ("G", "PLEASE DO NOT WALK ON THE GRASS"),
        ("H", "STAFF ONLY - DO NOT ENTER"),
    ],
    "items": [
        (1, "You must bring the right money for this.", "C"),
        (2, "A young child cannot come in here alone.", "E"),
        (3, "You cannot swim here today.", "D"),
        (4, "Only people who work here may go in.", "H"),
        (5, "You cannot leave your car here.", "B"),
    ],
}

R_PART2 = {
    "intro": "Read the sentences about a day at the market and choose the "
             "correct answer for each gap.",
    "items": [
        (6, "Aziz went to the market early to ……………… some fruit.",
         ["buy", "pay", "spend"], "A"),
        (7, "He ……………… his bag at home, so he carried everything in his arms.",
         ["forgot", "lost", "left"], "C"),
        (8, "The apples were very ……………… , so he bought two kilos.",
         ["cheap", "poor", "low"], "A"),
        (9, "A woman ……………… him the way to the bus stop.",
         ["said", "told", "spoke"], "B"),
        (10, "He was ……………… when he got home, so he drank a glass of water.",
         ["hungry", "thirsty", "tired"], "B"),
    ],
}

R_PART3 = {
    "intro": "Read the article about Samir and answer the questions. For each "
             "question, mark A, B or C on the answer sheet.",
    "title": "THE MAN WHO MENDS BICYCLES",
    "text": [
        "Samir Aliyev is thirty years old and he mends bicycles in a small "
        "shop near the station. He works alone, and on a busy afternoon "
        "fifteen customers bring him a bicycle.",
        "Samir did not plan to do this work. He studied computers at college "
        "for two years and then worked in an office in the city centre. He "
        "was not happy there. He sat at a computer all day, and he says he "
        "was always tired, even at the weekend.",
        "One winter his own bicycle broke. He carried it to an old man in "
        "his street and watched him mend it. It was interesting, and he went "
        "back the next week, and the week afterwards. Six months later the "
        "old man asked him an important question: did he want to work "
        "together?",
        "The old man is not well now and stays at home, and Samir has the "
        "shop. He opens at eight in the morning and closes at six, and he "
        "earns less money than he did in the office. He does not mind. He "
        "says he sleeps beautifully, and his favourite part of the job is "
        "seeing the same customers every week.",
    ],
    "questions": [
        {"q": 11, "stem": "Samir studied",
         "options": ["computers.", "engineering.", "business."], "answer": "A"},
        {"q": 12, "stem": "In the office, Samir was",
         "options": ["busy.", "tired.", "poor."], "answer": "B"},
        {"q": 13, "stem": "Samir first met the old man when",
         "options": ["he needed a job.", "his bicycle broke.",
                     "he moved to the street."], "answer": "B"},
        {"q": 14, "stem": "The old man does not work now because",
         "options": ["he is ill.", "he moved away.",
                     "he sold the shop."], "answer": "A"},
        {"q": 15, "stem": "Samir says that now he",
         "options": ["earns more money.", "works fewer hours.",
                     "sleeps well."], "answer": "C"},
    ],
}

R_PART4 = {
    "intro": "Read the article about bees and answer the questions. For each "
             "question, mark A, B or C on the answer sheet.",
    "title": "BEES",
    "text": ("A bee is a small insect, 16 …………… it is very important to "
             "farmers. Bees travel from flower to flower, and 17 …………… this "
             "way they help fruit and vegetables to grow. A single bee can "
             "visit five thousand flowers in one afternoon. Bees live "
             "together in large groups, and one group can have sixty "
             "thousand bees 18 …………… it. There are 19 …………… bees in the "
             "world today than there were fifty years ago, and scientists "
             "20 …………… worried about this. Farmers are worried too, because "
             "without bees many of our favourite vegetables would disappear."),
    "items": [
        (16, ["but", "so", "or"], "A"),
        (17, ["on", "at", "in"], "C"),
        (18, ["on", "in", "at"], "B"),
        (19, ["few", "fewer", "fewest"], "B"),
        (20, ["is", "are", "were"], "B"),
    ],
}

R_PART5 = {
    "intro": "Read the text. Think of the word which fits each gap. Write ONE "
             "word for each gap.",
    "letters": [
        ("Dear Sir or Madam,",
         "I (Example: saw) your advertisement for a Saturday job in the "
         "bookshop. I am seventeen years old and I am still 21 …………… school. "
         "I have worked in a shop before, 22 …………… only for two weeks in the "
         "summer. Could you tell me what time the shop opens 23 …………… "
         "Saturdays? I am free all day.",
         "Yours faithfully,\nOybek Yusupov"),
        ("Dear Mr Yusupov,",
         "Thank you 24 …………… your letter. We would like to meet you next "
         "week. Please come 25 …………… the shop on Tuesday at four o'clock and "
         "ask for Mrs Hill. The job is from nine until five.",
         "Yours sincerely,\nAnna Hill"),
    ],
    "answers": {21: "at", 22: "but", 23: "on", 24: "for", 25: "to"},
}

WRITING = {
    "task": "Write an email to an English friend. You have started a new "
            "class. Include:",
    "points": ["what the class is",
               "which days you go",
               "one thing you like about it",
               "ask your friend about their week"],
    "words": "Write at least 50 words.",
}
