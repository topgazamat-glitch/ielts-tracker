"""B1+ mock final, paper 5 - Reading and Writing, for the Intermediate classes.

Same skeleton and same density as Azamat's own B1+ final.
Checked by exams/check_paper.py.
"""

R_PART1 = {
    "intro": "Look at the text in each question. What does it say? For each "
             "question, choose the correct answer A, B, C or D.",
    "questions": [
        {"q": 1,
         "text": "Aziza - the printer is out of paper and I've used the last "
                 "of the spare box. There's more in the store room but it's "
                 "locked and Rustam has the key. Could you catch him before "
                 "he goes at four? Sanjar",
         "ask": "What does Sanjar want Aziza to do?",
         "options": ["Buy more paper this afternoon.",
                     "Speak to Rustam before he leaves.",
                     "Fix the printer herself.",
                     "Open the store room for him."],
         "answer": "B"},
        {"q": 2,
         "text": "THIS TRAIN WILL NOT STOP AT GREENFIELD OR HARTON TODAY "
                 "BECAUSE OF ENGINEERING WORK. PASSENGERS FOR THOSE STATIONS "
                 "SHOULD CHANGE AT WESTBROOK.",
         "ask": "What are passengers for Harton told?",
         "options": ["Their journey has been cancelled.",
                     "They must get off and take another train.",
                     "They should travel tomorrow instead.",
                     "They will be taken there by bus."],
         "answer": "B"},
        {"q": 3,
         "text": "From: Dr Ismoilova. I have looked at your results and there "
                 "is nothing to worry about. I would still like to see you, "
                 "but there is no hurry - make an appointment for some time "
                 "in the next month rather than this week.",
         "ask": "What is the doctor telling the patient?",
         "options": ["The results show a problem.",
                     "There is no need to come in again.",
                     "A visit is wanted but is not urgent.",
                     "The patient should come in this week."],
         "answer": "C"},
        {"q": 4,
         "text": "Reminder to all members: the annual fee rises on 1 April. "
                 "Anybody who renews before that date pays this year's price "
                 "for another twelve months, whichever month their "
                 "membership currently ends.",
         "ask": "What is the advantage of renewing before April?",
         "options": ["Members get an extra month free.",
                     "Members keep the lower price for a year.",
                     "Members can change their membership type.",
                     "Members avoid paying a joining fee."],
         "answer": "B"},
        {"q": 5,
         "text": "The recipe says two hours but mine took nearly three, so "
                 "start early if people are coming at seven. Also, ignore "
                 "what it says about the oven - ours runs hot and it was "
                 "burnt on top long before the middle was done.",
         "ask": "What is the writer warning the reader about?",
         "options": ["The dish is difficult to prepare.",
                     "The ingredients are expensive.",
                     "The stated time and temperature are unreliable.",
                     "The recipe serves fewer people than it claims."],
         "answer": "C"},
    ],
}

R_PART2 = {
    "intro": "Look at the sentences below about a bookshop on a boat. Read "
             "the text to decide if each sentence is correct or incorrect. "
             "If it is correct, choose YES. If it is not correct, choose NO.",
    "title": "Three thousand books and nowhere to put them",
    "text": [
        "The boat is twenty metres long, painted dark green, and holds "
        "rather more books than seems reasonable. Farrukh Nazarov bought it "
        "nine years ago with the money he had been saving for a flat, which "
        "his mother has still not entirely forgiven, and he has lived and "
        "worked on it ever since. It moves about twice a month, which means "
        "his customers have to find him.",
        "He was a teacher before this, and he is careful to say that he did "
        "not hate the job. What he disliked was the building: the same room, "
        "the same window, the same view of the car park for eleven years. "
        "The boat solves that problem completely. In summer he moors near "
        "the park and sells almost nothing but novels; in winter he moves "
        "considerably closer to the university and sells textbooks to "
        "students who cannot possibly afford new ones.",
        "The practical difficulties are considerable and he describes them "
        "cheerfully. Books are surprisingly heavy, and a boat carrying too "
        "many of them sits dangerously low in the water. Dampness is a "
        "constant enemy, so he runs a small heater throughout the winter "
        "and still loses several books every year. There is no room "
        "whatever for a stockroom, which means that every book he purchases "
        "has to replace another one that he has already sold.",
        "He makes less than he did teaching and says he has never once "
        "regretted it, which is the sort of thing people say to visiting "
        "writers. But the figures support him: he owns the boat, he has no "
        "rent to pay, and his only real expense is the diesel. He admits "
        "that the arrangement would collapse the moment he wanted a family, "
        "and that he thinks about this considerably more than he used to. "
        "His mother, who has apparently forgiven the flat business without "
        "ever saying so, now spends most of August on board, and reorganises "
        "the poetry section every single year without being asked.",
    ],
    "statements": [
        {"q": 6, "text": "Farrukh used the money he had saved for somewhere "
                         "to live.",
         "answer": "YES"},
        {"q": 7, "text": "He left teaching because he disliked the work "
                         "itself.",
         "answer": "NO"},
        {"q": 8, "text": "He sells different kinds of book at different times "
                         "of year.",
         "answer": "YES"},
        {"q": 9, "text": "He has space on board to store books he is not "
                         "selling.",
         "answer": "NO"},
        {"q": 10, "text": "He earns more now than he did as a teacher.",
         "answer": "NO"},
    ],
}

R_PART3 = {
    "intro": "Read the text and questions below. For each question, choose "
             "the correct answer A, B, C or D.",
    "title": "What happened when the school threw away the timetable",
    "text": [
        "For one week every February, a secondary school in the east of the "
        "country stops teaching its ordinary lessons. There is no maths, no "
        "history and no chemistry. Instead the whole school, from eleven "
        "year olds to eighteen year olds, works in mixed groups on a single "
        "problem set by somebody from outside. Last year it was the local "
        "bus company, which wanted to know why so few teenagers used the "
        "evening services.",
        "The head teacher is honest about where the idea came from. It was "
        "not a grand theory about education. The school had been told to "
        "reduce the amount of time senior staff spent on cover, and somebody "
        "pointed out, half as a joke, that a week without a timetable would "
        "need no cover at all. The educational arguments, she says, were "
        "found afterwards, which she thinks is how most school policy "
        "actually works.",
        "Parents were not enthusiastic. A number wrote to complain that a "
        "week was being wasted in an examination year, and the school agreed "
        "to let any student in the final year work in the library instead. "
        "In the first February, forty of them did. Last year the number was "
        "four, and the head teacher regards that fall as the clearest "
        "evidence she has that the week is working.",
        "The results the school can measure are modest. Attendance during "
        "the week is higher than in a normal February, and that is about it. "
        "What the staff describe instead is harder to put in a report: "
        "quiet students who turn out to be organisers, older ones who "
        "discover they can explain things, and the bus company, which "
        "adopted two of the suggestions and now sends somebody back every "
        "year. The head teacher keeps a folder of these stories for the "
        "governors, and admits that it is the least scientific document she "
        "has ever produced.",
    ],
    "questions": [
        {"q": 11, "ask": "What is unusual about the week in February?",
         "options": ["Only the older students take part.",
                     "Students of all ages work together.",
                     "The students choose the problem themselves.",
                     "Lessons are taught by visitors."],
         "answer": "B"},
        {"q": 12, "ask": "What does the head teacher say about the origin of "
                         "the idea?",
         "options": ["It came from a conference on education.",
                     "It began as a practical way to save staff time.",
                     "It was suggested by the bus company.",
                     "It was copied from another school."],
         "answer": "B"},
        {"q": 13, "ask": "How did the school respond to the parents?",
         "options": ["It ignored the complaints.",
                     "It cancelled the week for one year.",
                     "It allowed final-year students to opt out.",
                     "It moved the week to a different month."],
         "answer": "C"},
        {"q": 14, "ask": "Why does the head teacher mention the number four?",
         "options": ["It shows that fewer students now choose to miss the "
                     "week.",
                     "It shows that the school is smaller than it was.",
                     "It is the number of complaints received last year.",
                     "It is the number of problems the students solved."],
         "answer": "A"},
        {"q": 15, "ask": "What does the writer suggest about the results?",
         "options": ["They are impressive but hard to believe.",
                     "The measurable gains are small.",
                     "The school has stopped measuring them.",
                     "They are better in examination years."],
         "answer": "B"},
    ],
}

R_PART4 = {
    "intro": "Read the text below and choose the correct answer for each gap.",
    "title": "Old cinema to become a food market",
    "text": "The cinema on Market Street, which has stood empty since 2011, "
            "will (16) ......... as a food market next spring. The owners "
            "said they had (17) ......... several offers from developers who "
            "wanted to knock the building down, but had preferred a plan "
            "that kept the original front. Twenty small traders have already "
            "(18) ......... up for a stall, and the organisers expect the "
            "rest to be (19) ......... by Christmas. Local historians "
            "welcomed the decision, pointing (20) ......... that very few "
            "buildings of this age remain in the city centre, and that the "
            "cinema had been the first in the county to show a film with "
            "sound.",
    "gaps": [
        {"q": 16, "options": ["reopen", "restart", "return", "renew"],
         "answer": "A"},
        {"q": 17, "options": ["turned down", "put down", "let down",
                              "cut down"], "answer": "A"},
        {"q": 18, "options": ["written", "signed", "put", "given"],
         "answer": "B"},
        {"q": 19, "options": ["taken", "held", "made", "kept"],
         "answer": "A"},
        {"q": 20, "options": ["out", "at", "to", "over"], "answer": "A"},
    ],
}

R_PART5 = {
    "intro": "Read the text. Think of the word which best fits each gap. "
             "Write ONE word for each gap.",
    "title": "From: Kamola   To: Alex",
    "text": "Hi Alex,\n\nThank you for the parcel, which arrived on "
            "Saturday. The children opened it before I (21) ......... a "
            "chance to take a photograph, so you will have to imagine their "
            "faces.\n\nWe are all well. Dilshod has started a new job, "
            "(22) ......... means he leaves the house at six every morning "
            "and is not much use to anybody by eight in the evening. I keep "
            "telling him it will get easier, (23) ......... I am not sure I "
            "believe it.\n\nIf you are still thinking (24) ......... coming "
            "in the spring, April is better for us (25) ......... May. Let "
            "me know.\n\nKamola",
    "gaps": [
        {"q": 21, "answer": "had"},
        {"q": 22, "answer": "which"},
        {"q": 23, "answer": "but / though"},
        {"q": 24, "answer": "of / about"},
        {"q": 25, "answer": "than"},
    ],
}

WRITING1 = {
    "task": "You have just moved to a new flat and you want your English "
            "friend Jo to come and see it. Write an email to Jo. In your "
            "email:",
    "points": ["tell Jo that you have moved",
               "describe one thing you like about the flat",
               "invite Jo to visit."],
    "words": "Write 35-45 words.",
}

WRITING2 = {
    "task": "This is part of an email you receive from an English friend. "
            "Now write an email, giving your friend some advice.",
    "quote": "I've been asked to give a talk at work in front of about fifty "
             "people and I've never done anything like it. Part of me wants "
             "to say no, but I think it would help my career. How should I "
             "prepare?",
    "words": "Write about 100 words.",
}
