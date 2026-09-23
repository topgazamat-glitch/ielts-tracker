"""A2 mock final, paper 5. Same skeleton and same level as the real finals.

Checked by exams/check_paper.py against the measurements of Test 1 and Test 2.
"""

NARRATOR = "Daniel"
MAN, WOMAN, MAN2, WOMAN2 = "Rocko", "Shelley", "Reed", "Flo (English (UK))"

PART1 = [
    {
        "q": 1, "ask": "What is the girl looking for?",
        "options": ["Her phone", "Her bag", "Her coat"], "answer": "A",
        "lines": [
            (MAN, "Is that your bag by the door?"),
            (WOMAN2, "Yes, thank you, but that isn't the problem."),
            (MAN, "Your coat is on the chair."),
            (WOMAN2, "I can see it. I can't find my phone anywhere."),
        ],
    },
    {
        "q": 2, "ask": "How did they travel?",
        "options": ["By car", "By bus", "By plane"], "answer": "B",
        "lines": [
            (WOMAN, "Did you drive all the way to the coast?"),
            (MAN2, "We wanted to, but the car broke down on Friday."),
            (WOMAN, "So you flew?"),
            (MAN2, "Too expensive. We went by bus. Six hours."),
        ],
    },
    {
        "q": 3, "ask": "When is the exam?",
        "options": ["On Monday", "On Wednesday", "On Friday"], "answer": "C",
        "lines": [
            (MAN2, "The exam is on Monday, isn't it?"),
            (WOMAN2, "Monday is the last lesson. The exam is later."),
            (MAN2, "Wednesday?"),
            (WOMAN2, "Friday morning, nine o'clock. Don't be late."),
        ],
    },
    {
        "q": 4, "ask": "What will the woman order?",
        "options": ["Soup", "Fish", "Chicken"], "answer": "A",
        "lines": [
            (MAN, "The fish here is very good."),
            (WOMAN, "I had fish yesterday."),
            (MAN, "The chicken, then?"),
            (WOMAN, "I'm not very hungry. I'll just have the soup and bread."),
        ],
    },
    {
        "q": 5, "ask": "How old is the boy's brother?",
        "options": ["Nine", "Eleven", "Fourteen"], "answer": "B",
        "lines": [
            (WOMAN2, "Is your brother fourteen now?"),
            (MAN2, "That's my sister. She had a party last week."),
            (WOMAN2, "So your brother is nine?"),
            (MAN2, "He was nine two years ago. He's eleven."),
        ],
    },
]

PART2 = {
    "intro": "Listen to Nina telling a friend what the people in her office "
             "are doing next week. For questions 6 to 10, write a letter A "
             "to H next to each person.",
    "people": [("6", "Nina"), ("7", "Sam"), ("8", "Mrs Webb"),
               ("9", "Carlos"), ("10", "Ruth")],
    "options": [("A", "going on holiday"), ("B", "working at home"),
                ("C", "visiting another office"), ("D", "starting a course"),
                ("E", "moving house"), ("F", "going to hospital"),
                ("G", "staying in the office"), ("H", "leaving the company")],
    "answers": {"6": "D", "7": "E", "8": "C", "9": "A", "10": "H"},
    "lines": [
        (MAN, "Will anybody be in the office next week, Nina?"),
        (WOMAN, "Not many of us. I'm here on Monday, but after that I start "
                "a computer course for four days."),
        (MAN, "And Sam? Is he on holiday?"),
        (WOMAN, "Sam is moving house. He's found a flat near the park and "
                "he's taking the whole week."),
        (MAN, "What about Mrs Webb?"),
        (WOMAN, "She's visiting our other office in Bristol. She goes twice "
                "a year."),
        (MAN, "Is Carlos going with her?"),
        (WOMAN, "No, Carlos is the lucky one. Two weeks in Spain with his "
                "family."),
        (MAN, "So only Ruth is left."),
        (WOMAN, "Friday is her last day. She's found a job in a bigger "
                "company and we are all very sad about it."),
    ],
}

PART3 = {
    "intro": "Listen to a man asking about tickets at a theatre. For "
             "questions 11 to 15, tick A, B or C.",
    "questions": [
        {"q": 11, "stem": "The play starts at",
         "options": ["seven.", "half past seven.",
                     "eight."], "answer": "B"},
        {"q": 12, "stem": "The man wants tickets for",
         "options": ["Thursday.", "Friday.", "Saturday."], "answer": "C"},
        {"q": 13, "stem": "He buys",
         "options": ["two tickets.", "three tickets.",
                     "four tickets."], "answer": "C"},
        {"q": 14, "stem": "The seats are",
         "options": ["at the front.", "in the middle.",
                     "at the back."], "answer": "B"},
        {"q": 15, "stem": "He will pay",
         "options": ["by card.", "with cash.", "on the night."],
         "answer": "A"},
    ],
    "lines": [
        (MAN2, "Hello. What time does the play start?"),
        (WOMAN2, "Half past seven. The doors open at seven."),
        (MAN2, "Have you got tickets for Friday?"),
        (WOMAN2, "Friday is full, I'm afraid. There are seats on Thursday "
                 "and a few on Saturday."),
        (MAN2, "Saturday, then. My son is here on Saturday."),
        (WOMAN2, "How many would you like?"),
        (MAN2, "Two adults and two children. Four altogether."),
        (WOMAN2, "I have four seats together in the middle of the theatre. "
                 "The front row is empty, but you are too close there."),
        (MAN2, "The middle is fine."),
        (WOMAN2, "How would you like to pay? You can pay on the night, but "
                 "then I cannot keep the seats."),
        (MAN2, "I'll pay now, by card."),
    ],
}

PART4 = {
    "intro": "You will hear a woman telling her friend about a new sports "
             "club. Listen and complete questions 16 to 20.",
    "title": "SPORTS CLUB",
    "gaps": [
        {"q": 16, "label": "Club night", "answer": "Tuesday"},
        {"q": 17, "label": "Meet at", "answer": "5.45"},
        {"q": 18, "label": "In the old", "answer": "school"},
        {"q": 19, "label": "First month is", "answer": "free"},
        {"q": 20, "label": "Coach's name: Mr", "answer": "Whitmore"},
    ],
    "lines": [
        (WOMAN, "You should come to the new club with me."),
        (WOMAN2, "Which night is it?"),
        (WOMAN, "Tuesday. It was Thursday in the summer, but everybody "
                "wanted Tuesday, so they changed it."),
        (WOMAN2, "What time?"),
        (WOMAN, "We meet at quarter to six and start at six. Come early the "
                "first time."),
        (WOMAN2, "Where is it? The sports centre?"),
        (WOMAN, "In the old school, behind the library. The sports centre "
                "was too expensive for us."),
        (WOMAN2, "How much does it cost?"),
        (WOMAN, "Ten pounds a month, but the first month is free, so you can "
                "try it."),
        (WOMAN2, "Who runs it?"),
        (WOMAN, "Mr Whitmore. W - H - I - T - M - O - R - E. He played for a "
                "real team when he was young."),
    ],
}


# ----------------------------------------------------- READING AND WRITING

R_PART1 = {
    "intro": "Which notice (A-H) says this (1-5)? For questions 1 to 5, mark "
             "the correct letter A-H on the answer sheet.",
    "notices": [
        ("A", "PLEASE KEEP THIS DOOR CLOSED"),
        ("B", "TODAY'S SOUP: TOMATO"),
        ("C", "NO ENTRY BETWEEN 8 A.M. AND 6 P.M."),
        ("D", "PLEASE WRITE YOUR NAME IN THE BOOK"),
        ("E", "CAFÉ CLOSED - OPENING AGAIN IN APRIL"),
        ("F", "CHEAPER TICKETS FOR STUDENTS"),
        ("G", "PLEASE DO NOT FEED THE BIRDS"),
        ("H", "LOST SOMETHING? ASK AT THE OFFICE"),
    ],
    "items": [
        (1, "You pay less here if you study.", "F"),
        (2, "You cannot buy anything here for some months.", "E"),
        (3, "You should go here if you cannot find your things.", "H"),
        (4, "You must not give these animals any food.", "G"),
        (5, "You must sign this when you arrive.", "D"),
    ],
}

R_PART2 = {
    "intro": "Read the sentences about a day at the beach and choose the "
             "correct answer for each gap.",
    "items": [
        (6, "The children were ……………… to see the sea for the first time.",
         ["excited", "worried", "boring"], "A"),
        (7, "They ……………… their shoes off and ran across the sand.",
         ["put", "took", "got"], "B"),
        (8, "The water was too ……………… for swimming in April.",
         ["hot", "cold", "wet"], "B"),
        (9, "Their father ……………… them an ice cream each.",
         ["bought", "paid", "spent"], "A"),
        (10, "They went home ……………… but very happy.",
         ["tired", "sleep", "rest"], "A"),
    ],
}

R_PART3 = {
    "intro": "Read the article about Ayesha and answer the questions. For "
             "each question, mark A, B or C on the answer sheet.",
    "title": "THE GIRL WHO SELLS FLOWERS",
    "text": [
        "Ayesha Rahman is nineteen and she sells flowers from a small shop "
        "beside the market. She opens at seven in the morning, because "
        "people buy flowers on their way to work.",
        "The shop belonged to her mother, who sold flowers in the same place "
        "for twenty years. Ayesha helped her after school when she was a "
        "little girl. She did not think about it as work then; it was a "
        "wonderful game with water and colour, and she remembers it "
        "perfectly.",
        "Two years ago her mother became ill and could not stand for long. "
        "Ayesha was studying business at college and she left after one "
        "term. Her friends were surprised, and her teacher telephoned her "
        "twice.",
        "The best day is Friday, when people buy flowers for the weekend, "
        "and the worst is Monday, when almost nobody comes. Ayesha says she "
        "will go back to college one day, in the evening. For the "
        "moment she is here at seven every morning, and "
        "her mother sits by the window and tells her which flowers to buy.",
    ],
    "questions": [
        {"q": 11, "stem": "Ayesha opens the shop early because",
         "options": ["the market opens then.",
                     "people buy flowers before work.",
                     "the flowers arrive then."], "answer": "B"},
        {"q": 12, "stem": "When she was a child, Ayesha thought the shop was",
         "options": ["hard work.", "boring.", "a game."], "answer": "C"},
        {"q": 13, "stem": "Ayesha left college because",
         "options": ["her mother was ill.", "she did not like it.",
                     "it was expensive."], "answer": "A"},
        {"q": 14, "stem": "The quietest day in the shop is",
         "options": ["Monday.", "Friday.", "Sunday."], "answer": "A"},
        {"q": 15, "stem": "Ayesha would like to",
         "options": ["open a bigger shop.", "study again.",
                     "work with her mother."], "answer": "B"},
    ],
}

R_PART4 = {
    "intro": "Read the article about elephants and answer the questions. For "
             "each question, mark A, B or C on the answer sheet.",
    "title": "ELEPHANTS",
    "text": ("The elephant is the largest animal 16 …………… land. An adult can "
             "weigh six thousand kilos and eats for sixteen hours 17 "
             "…………… day. Elephants live in family groups, and the oldest "
             "female leads them. She remembers where the water is, even "
             "18 …………… she has not been there for many years. Baby "
             "elephants stay close to their mothers 19 …………… about ten "
             "years. Elephants 20 …………… talk to each other over long "
             "distances with a sound that people cannot hear. Scientists "
             "say an elephant never forgets another elephant's face."),
    "items": [
        (16, ["in", "on", "at"], "B"),
        (17, ["a", "an", "the"], "A"),
        (18, ["if", "so", "but"], "A"),
        (19, ["since", "during", "for"], "C"),
        (20, ["can", "must", "should"], "A"),
    ],
}

R_PART5 = {
    "intro": "Read the text. Think of the word which fits each gap. Write ONE "
             "word for each gap.",
    "letters": [
        ("Dear Ms Clark,",
         "I am writing (Example: to) ask about the English classes at your "
         "school. My son is twelve years old and he has studied English "
         "21 …………… three years. He is good at reading 22 …………… he is shy "
         "when he speaks. Do you have a class 23 …………… children of his age?",
         "Yours sincerely,\nGulnora Ismoilova"),
        ("Dear Mrs Ismoilova,",
         "Thank you for your letter. We have a class 24 …………… Saturday "
         "mornings for students between eleven and thirteen. There "
         "25 …………… eight children in it at the moment. Please bring your son "
         "to meet the teacher.",
         "Yours sincerely,\nSarah Clark"),
    ],
    "answers": {21: "for", 22: "but", 23: "for", 24: "on", 25: "are"},
}

WRITING = {
    "task": "Write an email to an English friend. You want to buy a present "
            "for somebody in your family. Include:",
    "points": ["who the present is for",
               "why you are buying it",
               "what you want to buy",
               "ask your friend what they think"],
    "words": "Write at least 50 words.",
}
