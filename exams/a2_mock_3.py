"""A2 mock final, paper 3. Same skeleton and same level as the real finals.

Checked by exams/check_paper.py against the measurements of Test 1 and Test 2.
"""

NARRATOR = "Daniel"
MAN, WOMAN, MAN2, WOMAN2 = "Rocko", "Shelley", "Reed", "Flo (English (UK))"

PART1 = [
    {
        "q": 1, "ask": "What is the weather like now?",
        "options": ["Sunny", "Raining", "Windy"], "answer": "C",
        "lines": [
            (WOMAN, "Do I need my coat? It was raining this morning."),
            (MAN, "It stopped an hour ago."),
            (WOMAN, "So it's sunny?"),
            (MAN, "No, but it's very windy. Hold on to your hat."),
        ],
    },
    {
        "q": 2, "ask": "Which sport does the boy play now?",
        "options": ["Football", "Basketball", "Tennis"], "answer": "B",
        "lines": [
            (WOMAN2, "Are you still in the football team, Karim?"),
            (MAN2, "I played football for three years, but I stopped."),
            (WOMAN2, "Tennis, then? Your sister plays tennis."),
            (MAN2, "No, basketball. I'm the tallest boy in my class."),
        ],
    },
    {
        "q": 3, "ask": "How much did the shoes cost?",
        "options": ["Twenty pounds", "Forty pounds", "Sixty pounds"],
        "answer": "B",
        "lines": [
            (MAN, "Are those new shoes? They look expensive."),
            (WOMAN, "They were sixty pounds last month."),
            (MAN, "You paid sixty pounds?"),
            (WOMAN, "No, I waited. I got them for forty in the sale."),
        ],
    },
    {
        "q": 4, "ask": "What did they forget?",
        "options": ["The bread", "The milk", "The eggs"], "answer": "C",
        "lines": [
            (WOMAN2, "Have we got everything? Bread, milk..."),
            (MAN2, "The bread is in the bag and I put the milk in the fridge."),
            (WOMAN2, "Then we can make the cake."),
            (MAN2, "We can't. There are no eggs. Nobody bought any."),
        ],
    },
    {
        "q": 5, "ask": "Where is the woman going?",
        "options": ["To the hospital", "To the library", "To the dentist"],
        "answer": "A",
        "lines": [
            (MAN, "Are you going to the library again?"),
            (WOMAN2, "Not today. My mother is ill."),
            (MAN, "Is she at home?"),
            (WOMAN2, "No, she's in hospital. I'm going to visit her now."),
        ],
    },
]

PART2 = {
    "intro": "Listen to Laura telling a friend about the people in her music "
             "class. What does each person play? For questions 6 to 10, "
             "write a letter A to H next to each person.",
    "people": [("6", "Laura"), ("7", "Tom"), ("8", "Elena"),
               ("9", "Mr Rossi"), ("10", "Sam")],
    "options": [("A", "the piano"), ("B", "the guitar"), ("C", "the violin"),
                ("D", "the drums"), ("E", "the flute"), ("F", "the trumpet"),
                ("G", "nothing - they sing"), ("H", "nothing - they write music")],
    "answers": {"6": "C", "7": "D", "8": "G", "9": "A", "10": "B"},
    "lines": [
        (MAN, "How many of you are there in the music class, Laura?"),
        (WOMAN, "Five students and the teacher. I started on the piano when "
                "I was six, but I play the violin now."),
        (MAN, "And Tom? Does he play the guitar?"),
        (WOMAN, "His brother plays the guitar. Tom plays the drums, and we "
                "can hear him from the street."),
        (MAN, "What about Elena?"),
        (WOMAN, "Elena doesn't play anything. She sings, and she has a "
                "beautiful voice."),
        (MAN, "Does your teacher play?"),
        (WOMAN, "Mr Rossi plays the piano for all of us. He writes music too, "
                "but he says that is only for himself."),
        (MAN, "And the fifth student?"),
        (WOMAN, "That's Sam. He plays the guitar, and he wants to be in a "
                "band when he leaves school."),
    ],
}

PART3 = {
    "intro": "Listen to a man asking about a cooking course at a college. "
             "For questions 11 to 15, tick A, B or C.",
    "questions": [
        {"q": 11, "stem": "The course is on",
         "options": ["Monday evenings.", "Tuesday evenings.",
                     "Saturday mornings."], "answer": "C"},
        {"q": 12, "stem": "The course lasts",
         "options": ["four weeks.", "six weeks.", "ten weeks."], "answer": "B"},
        {"q": 13, "stem": "In the first lesson they will make",
         "options": ["soup.", "bread.", "cakes."], "answer": "B"},
        {"q": 14, "stem": "Students must bring",
         "options": ["food.", "a knife.", "an apron."], "answer": "B"},
        {"q": 15, "stem": "The course costs",
         "options": ["forty pounds.", "sixty pounds.",
                     "eighty pounds."], "answer": "C"},
    ],
    "lines": [
        (MAN2, "Hello. I saw your advertisement for the cooking course."),
        (WOMAN2, "Yes, of course. It's on Saturday mornings, from ten "
                 "until one."),
        (MAN2, "Not in the evening? A friend told me Tuesday."),
        (WOMAN2, "Tuesday evening is the Italian course. This one is "
                 "Saturday."),
        (MAN2, "How long is it?"),
        (WOMAN2, "Six weeks. There was a four-week course in the spring and "
                 "a longer one of ten weeks, but this is six."),
        (MAN2, "What do we learn first?"),
        (WOMAN2, "Bread, in the first lesson. Soup is the second week and "
                 "cakes are at the end."),
        (MAN2, "Do I need to bring anything?"),
        (WOMAN2, "We give you an apron and all the food. Please bring your "
                 "own knife. A good cook needs a good knife."),
        (MAN2, "And how much is it?"),
        (WOMAN2, "Eighty pounds for the six weeks. That includes everything "
                 "you cook, and you take it home."),
    ],
}

PART4 = {
    "intro": "You will hear a woman leaving a message about a party. Listen "
             "and complete questions 16 to 20.",
    "title": "MESSAGE ABOUT THE PARTY",
    "gaps": [
        {"q": 16, "label": "Party is on", "answer": "Saturday"},
        {"q": 17, "label": "Starts at", "answer": "6.30"},
        {"q": 18, "label": "Address: 14 ………… Road", "answer": "Green"},
        {"q": 19, "label": "Please bring some", "answer": "fruit"},
        {"q": 20, "label": "Telephone", "answer": "07766 431"},
    ],
    "lines": [
        (WOMAN, "Hi, it's Marta. I'm calling about the party."),
        (WOMAN, "It was Friday, but Ben is working, so now it's Saturday. "
                "Saturday, not Friday."),
        (WOMAN, "Come at half past six. Dinner is at seven and we don't want "
                "to start without you."),
        (WOMAN, "You haven't been to the new house. It's fourteen Green Road. "
                "G - R - E - E - N. The green door, which is easy to "
                "remember."),
        (WOMAN, "Don't bring a cake. My mother is making two. Could you "
                "bring some fruit? Anything you like."),
        (WOMAN, "Call me if you are lost. My new number is oh seven seven "
                "six six, four three one. Bye."),
    ],
}


# ----------------------------------------------------- READING AND WRITING

R_PART1 = {
    "intro": "Which notice (A-H) says this (1-5)? For questions 1 to 5, mark "
             "the correct letter A-H on the answer sheet.",
    "notices": [
        ("A", "PLEASE BE QUIET - EXAM IN PROGRESS"),
        ("B", "BUY TWO, GET ONE FREE"),
        ("C", "OUT OF ORDER - USE THE MACHINE UPSTAIRS"),
        ("D", "OPEN 24 HOURS"),
        ("E", "PLEASE PUT RUBBISH IN THE BIN"),
        ("F", "NO PHOTOGRAPHS IN THIS ROOM"),
        ("G", "SALE ENDS ON SUNDAY"),
        ("H", "PLEASE RING THE BELL FOR SERVICE"),
    ],
    "items": [
        (1, "You can get three of these and pay for two.", "B"),
        (2, "You cannot come in here and make a noise.", "A"),
        (3, "You can come here at any time of the day or night.", "D"),
        (4, "You must not take pictures here.", "F"),
        (5, "You must make a sound if you want help.", "H"),
    ],
}

R_PART2 = {
    "intro": "Read the sentences about a visit to the doctor and choose the "
             "correct answer for each gap.",
    "items": [
        (6, "Marta did not feel well, so she ……………… an appointment.",
         ["did", "made", "took"], "B"),
        (7, "She waited for twenty minutes and then the doctor ……………… her in.",
         ["called", "shouted", "spoke"], "A"),
        (8, "The doctor said she had a ……………… and must stay at home.",
         ["pain", "cold", "hurt"], "B"),
        (9, "He gave her some ……………… to take twice a day.",
         ["medicine", "food", "water"], "A"),
        (10, "After three days she felt much ……………… .",
         ["good", "well", "better"], "C"),
    ],
}

R_PART3 = {
    "intro": "Read the article about Helen and answer the questions. For each "
             "question, mark A, B or C on the answer sheet.",
    "title": "THE WOMAN WHO BRINGS THE POST",
    "text": [
        "Helen Doyle has carried the post in a small village in Ireland for "
        "eighteen years. She begins at six in the morning, when the streets "
        "are empty, and she finishes at about one in the afternoon.",
        "Helen did not want this job at the beginning. She worked in a shop "
        "in the city and travelled an hour on the bus every morning. Then "
        "her husband found work in the village, and they moved. There were "
        "not many jobs, and somebody told her about the post.",
        "She walks about fifteen kilometres every day, in all weathers. In "
        "winter it is dark until eight o'clock and sometimes there is snow, "
        "but she says the worst weather is heavy rain. Her dog Bella walks "
        "with her and knows every house in the village.",
        "Helen knows everybody, and that is her favourite part of the job. "
        "There are old people who see nobody else before lunch, so she stops "
        "and talks. Next year she will be sixty, and her daughter says it is "
        "time to stop walking. Helen is not listening.",
    ],
    "questions": [
        {"q": 11, "stem": "Before this job, Helen worked",
         "options": ["in a shop.", "in an office.",
                     "on a farm."], "answer": "A"},
        {"q": 12, "stem": "Helen moved to the village because",
         "options": ["she wanted this job.", "her husband found work there.",
                     "the city was expensive."], "answer": "B"},
        {"q": 13, "stem": "Helen says the hardest weather is",
         "options": ["the snow.", "the dark.", "the rain."], "answer": "C"},
        {"q": 14, "stem": "Bella is",
         "options": ["her dog.", "her daughter.",
                     "a woman in the village."], "answer": "A"},
        {"q": 15, "stem": "Helen likes the job most because",
         "options": ["she walks every day.", "she starts early.",
                     "she talks to people."], "answer": "C"},
    ],
}

R_PART4 = {
    "intro": "Read the article about penguins and answer the questions. For "
             "each question, mark A, B or C on the answer sheet.",
    "title": "PENGUINS",
    "text": ("Penguins are birds, 16 …………… they cannot fly. They use their "
             "wings to swim, and they are faster in the water 17 …………… most "
             "fish. Penguins live in the southern half of the world, and "
             "some of them live 18 …………… places where it is extremely cold "
             "all year. A penguin can stay under the water for twenty "
             "minutes. Parents take turns: one looks after the baby while "
             "the other 19 …………… to the sea for food. Many penguins return "
             "to the same beach 20 …………… year, and they find it without a "
             "map."),
    "items": [
        (16, ["so", "but", "or"], "B"),
        (17, ["than", "then", "that"], "A"),
        (18, ["on", "at", "in"], "C"),
        (19, ["go", "goes", "going"], "B"),
        (20, ["all", "every", "each of"], "B"),
    ],
}

R_PART5 = {
    "intro": "Read the text. Think of the word which fits each gap. Write ONE "
             "word for each gap.",
    "letters": [
        ("Dear Mr Owen,",
         "I am writing (Example: about) the bicycle I bought in your shop "
         "21 …………… Saturday. After two days the light stopped working. I "
         "took it back 22 …………… the shop, but it was closed. Could you tell "
         "me 23 …………… you are open this week?",
         "Yours sincerely,\nNilufar Sodiqova"),
        ("Dear Ms Sodiqova,",
         "I am sorry 24 …………… the trouble. We are open from nine until six "
         "every day 25 …………… Sunday. Please bring the bicycle in and we will "
         "mend the light while you wait.",
         "Yours sincerely,\nDavid Owen"),
    ],
    "answers": {21: "on", 22: "to", 23: "when", 24: "about / for", 25: "except"},
}

WRITING = {
    "task": "Write an email to an English friend. You went on a school trip "
            "last week. Include:",
    "points": ["where you went",
               "who you went with",
               "what the weather was like",
               "one thing you enjoyed"],
    "words": "Write at least 50 words.",
}
