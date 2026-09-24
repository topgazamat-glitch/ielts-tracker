"""B1 mid-course test 2 - Reading and Writing, for the Pre-Intermediate classes.

Built to the official Empower B1 Mid-Course Competency test. Long, plain
texts and short sentences; the language stays inside the first half of the
course. Checked by exams/check_paper.py.
"""

EXAM_SKILLS = [
    ("Part 1", "Five short messages. The wrong answers usually repeat a word "
               "from the text. Read all three before you choose."),
    ("Part 2", "YES or NO about a long text. Find the part of the text the "
               "sentence is about first; the order follows the text."),
    ("Part 3", "One article, five questions. The last question asks about the "
               "whole text, so leave it until the end."),
    ("Part 4", "Grammar in a text. Read the whole sentence, not just the gap - "
               "the word after the gap usually decides it."),
    ("Part 5", "One word in each gap, and it is almost always a small word: "
               "a preposition, an auxiliary, a pronoun."),
    ("Writing", "The short email must contain all three points. The long one "
                "is advice: say what you would do and why."),
]

R_PART1 = {
    "intro": "Look at the text in each question. What does it say? For each "
             "question, choose the correct answer A, B or C.",
    "questions": [
        {"q": 1,
         "text": "Jasur - the shop rang. Your jacket is ready but they "
                 "close at six today, not eight. If you can't get there, "
                 "they will keep it until Monday. Dad",
         "ask": "What is Jasur's father telling him?",
         "options": ["The jacket is not ready yet.",
                     "The shop is closing earlier than usual.",
                     "He has collected the jacket already."],
         "answer": "B"},
        {"q": 2,
         "text": "TO USE THE WASHING MACHINES YOU NEED A CARD, NOT COINS. "
                 "CARDS ARE SOLD AT RECEPTION UNTIL 9 P.M.",
         "ask": "What does the notice say?",
         "options": ["The machines take coins.",
                     "Cards can be bought at any time.",
                     "You must buy a card before nine."],
         "answer": "C"},
        {"q": 3,
         "text": "From: Nilufar. I can't come to the cinema on Friday - I "
                 "have to work. Don't buy me a ticket. But I'm free on "
                 "Sunday if you want to go then instead.",
         "ask": "What does Nilufar want?",
         "options": ["To go to the cinema on a different day.",
                     "Somebody to buy her a ticket.",
                     "To meet after work on Friday."],
         "answer": "A"},
        {"q": 4,
         "text": "The trip to the museum is free, but students must bring "
                 "their own lunch. There is nowhere to buy food and we will "
                 "not have time to stop on the way.",
         "ask": "What must students do?",
         "options": ["Pay for the trip.",
                     "Bring food with them.",
                     "Eat before they leave."],
         "answer": "B"},
        {"q": 5,
         "text": "I stayed there for three nights. The rooms are small and "
                 "the breakfast is nothing special, but it is two minutes "
                 "from the station and it cost half what the others cost.",
         "ask": "Why does the writer recommend the hotel?",
         "options": ["The rooms are comfortable.",
                     "It is cheap and well placed.",
                     "The breakfast is good."],
         "answer": "B"},
    ],
}

R_PART2 = {
    "intro": "Look at the sentences below about a mountain post office. Read "
             "the text to decide if each sentence is correct or incorrect. "
             "If it is correct, choose YES. If it is not correct, choose NO.",
    "title": "The highest post office in the country",
    "text": [
        "To reach it you leave the main road and drive for an hour up a "
        "track that is not really a road at all. In the winter the track is "
        "closed for weeks at a time. At the top there is a village of about "
        "sixty people, and in the middle of the village there is a small "
        "white building with a red door. It is a post office, and it is the "
        "highest one in the country.",
        "It opens three mornings a week. Zulfiya Karimova has run it for "
        "twenty-six years, which is longer than some of her customers have "
        "been alive. She took the job when her husband became ill and they "
        "needed the money, and she says she expected to do it for a year or "
        "two at the most.",
        "The work is not what people imagine. She sells stamps, of course, "
        "but she also pays out pensions, fills in forms for people who "
        "cannot read the small print, and keeps parcels behind the counter "
        "for families who are out with the animals all day. Once a month a "
        "van comes up the track with supplies, and if the weather is bad it "
        "does not come at all.",
        "Three years ago the postal service decided the office was too "
        "expensive and announced that it would close. The village wrote "
        "letters. A newspaper in the city heard about it and sent a "
        "photographer, and the photograph of Zulfiya standing in the snow "
        "outside the red door appeared on the front page. The decision was "
        "changed six weeks later.",
        "Zulfiya is not sentimental about any of this. She says the office "
        "will close one day. The village is getting smaller every year. "
        "Nobody younger wants the job. She would like it to stay open until "
        "she stops. She has not decided when that will be.",
        "I asked her what the hardest part was. I expected her to say the "
        "winter, or the track, or the long walk to the van. She thought "
        "about it for a while. Then she said it was the letters. Not "
        "carrying them, she explained, but knowing what is in them. In a "
        "village of sixty people you know whose son is in the army and "
        "whose daughter has gone to the city. You know which envelope is "
        "the one somebody has been waiting six weeks for. You hand it over "
        "and you watch their face. She said you never get used to that "
        "part, and she has been doing it for twenty-six years.",
        "In the meantime she opens the red door at nine o'clock on Monday, "
        "Wednesday and Friday. Somebody is usually waiting.",
    ],
    "statements": [
        {"q": 6, "text": "The post office is open every day.", "answer": "NO"},
        {"q": 7, "text": "Zulfiya expected to stay in the job for a long "
                         "time.",
         "answer": "NO"},
        {"q": 8, "text": "She does other things besides selling stamps.",
         "answer": "YES"},
        {"q": 9, "text": "A newspaper helped to keep the office open.",
         "answer": "YES"},
        {"q": 10, "text": "Somebody younger is ready to take over from her.",
         "answer": "NO"},
    ],
}

R_PART3 = {
    "intro": "Read the text and questions below. For each question, choose "
             "the correct answer A, B or C.",
    "title": "I gave up my phone for a month",
    "text": [
        "I did not do it to prove anything. I lost my phone in a taxi in "
        "March and I could not afford a new one until my next pay day, "
        "which was four weeks later. So the month happened to me. I did not "
        "choose it.",
        "The first three days were the worst. I did not know what time it "
        "was. I could not tell anybody I was going to be late. Twice I "
        "stood at a bus stop and had no idea when the bus was coming, and I "
        "found that I had forgotten how to simply wait for something.",
        "Then some strange things started. I read two books, which I had "
        "not done in a year. I got lost in my own city and asked a man in a "
        "shop for directions, and we talked for ten minutes about his "
        "daughter. I started writing things on paper again and I noticed "
        "that my handwriting had become terrible.",
        "It was not all good. I missed my cousin's wedding photographs and "
        "nobody could reach me when my mother was in hospital, which "
        "frightened my whole family. I had to walk to my friend's flat "
        "twice to find out if he was at home. A phone is not a toy. It is "
        "how people find you.",
        "I bought a new phone on the first of April and I was glad to have "
        "it. But I have kept two things from that month. I do not take the "
        "phone to the table when I eat, and I still have a paper notebook "
        "in my bag. My sister says this is not very impressive after four "
        "weeks without one. She is probably right.",
    ],
    "questions": [
        {"q": 11, "ask": "Why did the writer live without a phone?",
         "options": ["To test himself.",
                     "Because he could not replace it immediately.",
                     "Because a friend suggested it."], "answer": "B"},
        {"q": 12, "ask": "What did the writer find difficult at first?",
         "options": ["Waiting without knowing how long.",
                     "Finding his way home.",
                     "Reading books again."], "answer": "A"},
        {"q": 13, "ask": "What happened when he got lost?",
         "options": ["He bought a map.",
                     "He had a long conversation with a stranger.",
                     "He waited until somebody found him."], "answer": "B"},
        {"q": 14, "ask": "What does the writer say was the real problem?",
         "options": ["He could not take photographs.",
                     "His handwriting got worse.",
                     "People could not contact him in an emergency."],
         "answer": "C"},
        {"q": 15, "ask": "Which of these would be a good title for this text?",
         "options": ["Why everybody should throw away their phone",
                     "Four weeks I did not plan, and what stayed",
                     "How to live without technology"], "answer": "B"},
    ],
}

R_PART4 = {
    "intro": "Read the text below and choose the correct answer for each gap.",
    "title": "Students build a weather station",
    "text": "A group of students at a school in the south (16) ......... "
            "built a weather station in the school garden. They "
            "(17) ......... measuring the temperature and the rainfall every "
            "morning since September, and they send the figures to a "
            "national website. The science teacher said the project was "
            "(18) ......... useful than any lesson she could have taught. "
            "The students (19) ......... to keep the records going for a "
            "whole year. Two other schools in the town (20) ......... going "
            "to build one as well.",
    "gaps": [
        {"q": 16, "options": ["have", "has", "had"], "answer": "A"},
        {"q": 17, "options": ["are", "have been", "were"], "answer": "B"},
        {"q": 18, "options": ["more", "most", "much"], "answer": "A"},
        {"q": 19, "options": ["hope", "hopes", "hoping"], "answer": "A"},
        {"q": 20, "options": ["is", "are", "was"], "answer": "B"},
    ],
}

R_PART5 = {
    "intro": "Read the text. Think of the word which best fits each gap. "
             "Write ONE word for each gap.",
    "title": "From: Aziz   To: Robin",
    "text": "Hi Robin,\n\nIt was good to see you last month. I am sorry I "
            "did not write sooner - I (21) ......... been very busy at "
            "work.\n\nI have started going to the gym, which is something I "
            "said I would never do. My friend takes me on Tuesdays and "
            "Thursdays. It is harder (22) ......... I expected and I cannot "
            "walk properly on Wednesdays, (23) ......... I feel better than "
            "I did.\n\nAre you coming here in the summer? If you are, come "
            "in July rather (24) ......... August, because it is too hot "
            "then. Let me know (25) ......... you decide.\n\nAziz",
    "gaps": [
        {"q": 21, "answer": "have"},
        {"q": 22, "answer": "than"},
        {"q": 23, "answer": "but"},
        {"q": 24, "answer": "than"},
        {"q": 25, "answer": "when"},
    ],
}

WRITING1 = {
    "task": "You have started a new class and you want to tell your English "
            "friend Alex about it. Write an email to Alex. In your email:",
    "points": ["say what the class is",
               "say when you go",
               "tell Alex one thing you like about it."],
    "words": "Write 35-45 words.",
}

WRITING2 = {
    "task": "This is part of an email you receive from an English friend. "
            "Now write an email, giving your friend some advice.",
    "quote": "My best friend has asked me to go on holiday with her for two "
             "weeks. I would love to go, but I have already promised my "
             "parents I would help in their shop that month. I don't want "
             "to upset anybody. What should I do?",
    "words": "Write about 100 words.",
}
