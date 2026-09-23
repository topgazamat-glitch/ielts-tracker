"""B1+ mock final, paper 3 - Reading and Writing, for the Intermediate classes.

Same skeleton and same density as Azamat's own B1+ final.
Checked by exams/check_paper.py.
"""

R_PART1 = {
    "intro": "Look at the text in each question. What does it say? For each "
             "question, choose the correct answer A, B, C or D.",
    "questions": [
        {"q": 1,
         "text": "Sardor - I've left the car at the garage. They say it "
                 "needs a new part which won't arrive until Monday, so don't "
                 "expect it this weekend. Use mine, the keys are in the blue "
                 "bowl. Zarina",
         "ask": "What is Zarina telling Sardor?",
         "options": ["The car has been repaired.",
                     "He should collect the car on Monday.",
                     "He can borrow her car in the meantime.",
                     "The garage has lost the keys."],
         "answer": "C"},
        {"q": 2,
         "text": "PHOTOGRAPHY IS PERMITTED IN THE GALLERIES BUT NOT IN THE "
                 "TEMPORARY EXHIBITION ON THE LOWER FLOOR. FLASH MUST NOT BE "
                 "USED ANYWHERE IN THE BUILDING.",
         "ask": "What does the notice say about taking photographs?",
         "options": ["They are not allowed anywhere in the museum.",
                     "They are allowed everywhere if no flash is used.",
                     "One part of the museum does not allow them at all.",
                     "Flash may be used in the galleries only."],
         "answer": "C"},
        {"q": 3,
         "text": "To all staff: the lift will be out of use on Wednesday "
                 "while it is serviced. Anybody who cannot manage the stairs "
                 "should speak to their manager beforehand so that work can "
                 "be arranged on the ground floor.",
         "ask": "What are staff asked to do?",
         "options": ["Avoid coming into the office on Wednesday.",
                     "Tell their manager in advance if the stairs are a "
                     "problem.",
                     "Use the stairs rather than the lift all week.",
                     "Move their desks to the ground floor."],
         "answer": "B"},
        {"q": 4,
         "text": "From: Bekzod. I've read the report. The numbers are fine "
                 "but the ending simply stops - there's nothing telling the "
                 "reader what we want them to do. Add that before it goes to "
                 "the board on Friday.",
         "ask": "What does Bekzod want changed?",
         "options": ["The figures in the report.",
                     "The date of the board meeting.",
                     "The length of the report.",
                     "The conclusion, which needs a recommendation."],
         "answer": "D"},
        {"q": 5,
         "text": "TICKETS ARE VALID FOR THE DATE SHOWN ONLY. IF YOU CANNOT "
                 "ATTEND, CONTACT US AT LEAST 48 HOURS BEFOREHAND AND WE "
                 "WILL EXCHANGE YOUR TICKET FOR ANOTHER PERFORMANCE. NO "
                 "REFUNDS.",
         "ask": "What can customers do if they cannot come?",
         "options": ["Get their money back within 48 hours.",
                     "Change to a different date if they give enough notice.",
                     "Give the ticket to somebody else.",
                     "Use the ticket on any other day."],
         "answer": "B"},
    ],
}

R_PART2 = {
    "intro": "Look at the sentences below about a swimming coach. Read the "
             "text to decide if each sentence is correct or incorrect. If it "
             "is correct, choose YES. If it is not correct, choose NO.",
    "title": "The coach who teaches grown-ups to swim",
    "text": [
        "There are eight people in the shallow end and not one of them is "
        "under thirty. The youngest is a doctor of thirty-four who has "
        "avoided beaches for most of her adult life; the oldest is a retired "
        "builder of seventy-one who decided last year that he had left it "
        "long enough. All of them are here because Gulnora Ergasheva teaches "
        "adults who cannot swim, and she is one of very few people in the "
        "city who will.",
        "She came to it the long way round. For nine years she coached "
        "children, and she was good at it, but she noticed that the parents "
        "waiting at the side were often more frightened of the water than "
        "their sons and daughters. When she asked why they had never learned, "
        "the answers were remarkably similar: somebody had thrown them in, or "
        "laughed at them, and they had never gone back.",
        "The first lesson does not involve swimming at all. Nobody puts their "
        "face in the water and nobody lets go of the side. Gulnora says the "
        "single most useful thing she does is to explain that a human body "
        "floats whether or not its owner believes in it, and then prove it. "
        "Her classes are deliberately small and she will not take anybody who "
        "is being pushed into it by a husband or a daughter.",
        "Progress is slower than with children and the ending is usually "
        "better. Adults understand exactly why they are doing a particular "
        "exercise, so they practise it properly, and they remember how much "
        "it cost them to walk through the door in the first place. "
        "Approximately nine out of ten complete the course able to swim a "
        "length without stopping. The doctor managed hers in February, in "
        "front of nobody, and admitted afterwards that she had cried "
        "quietly in the changing room.",
    ],
    "statements": [
        {"q": 6, "text": "Everybody in the class is an adult.", "answer": "YES"},
        {"q": 7, "text": "Gulnora began her career teaching adults.",
         "answer": "NO"},
        {"q": 8, "text": "Most of her students had a bad experience with "
                         "water when they were younger.",
         "answer": "YES"},
        {"q": 9, "text": "Students are asked to put their faces in the water "
                         "in the first lesson.",
         "answer": "NO"},
        {"q": 10, "text": "Gulnora accepts students who have been persuaded "
                          "by their families.",
         "answer": "NO"},
    ],
}

R_PART3 = {
    "intro": "Read the text and questions below. For each question, choose "
             "the correct answer A, B, C or D.",
    "title": "Why the post office stayed open",
    "text": [
        "The post office in the village had been losing money for eleven "
        "years when the company finally announced that it would close. What "
        "happened next was not a protest, or at least not only a protest. "
        "Within a fortnight a group of residents had worked out roughly what "
        "the building cost to run, decided the figure was not impossible, "
        "and begun asking whether the village could simply buy it.",
        "The idea was not new. Around four hundred shops and post offices in "
        "the country are now owned by the communities they serve, and there "
        "is a well-worn path to follow: form a society, sell shares to "
        "residents at a price nobody will miss, and accept that the thing "
        "will never make a profit. What surprised the organisers was how "
        "much of the work was paperwork rather than persuasion. Raising the "
        "money took nine weeks. The legal arrangements took eight months.",
        "It opens six days a week and is run by two paid staff and a rota of "
        "volunteers, which is where the arrangement becomes interesting. The "
        "shop sells the ordinary things, but the volunteers also notice "
        "things. If a customer who comes in every day has not appeared by "
        "Thursday, somebody telephones. This was nobody's plan and does not "
        "appear in the business documents, and the chair of the society "
        "argues that it is now the most valuable service the building "
        "provides.",
        "The accounts are not comfortable reading. The shop broke even in "
        "its second year and lost money in its third, and the society has "
        "already had to ask its members for more. Nobody involved describes "
        "the experiment as a success in the way a company would use the "
        "word. They describe it instead as the price of having somewhere to "
        "go, which is a different kind of calculation altogether.",
    ],
    "questions": [
        {"q": 11, "ask": "What was the villagers' first reaction to the "
                         "closure?",
         "options": ["They organised a protest and nothing else.",
                     "They looked into whether they could buy the building "
                     "themselves.",
                     "They asked the company to reconsider.",
                     "They looked for another site in the village."],
         "answer": "B"},
        {"q": 12, "ask": "What does the writer say about community shops?",
         "options": ["They are rare in this country.",
                     "They usually make a small profit.",
                     "There is an established way of setting one up.",
                     "They are always run entirely by volunteers."],
         "answer": "C"},
        {"q": 13, "ask": "What surprised the organisers?",
         "options": ["How hard it was to persuade residents.",
                     "How much of the delay was legal rather than financial.",
                     "How little money they raised.",
                     "How few people bought shares."],
         "answer": "B"},
        {"q": 14, "ask": "Why does the writer mention the telephone calls?",
         "options": ["To show that the volunteers are poorly trained.",
                     "To explain how the shop makes money.",
                     "To give an example of a benefit nobody planned.",
                     "To criticise the local health service."],
         "answer": "C"},
        {"q": 15, "ask": "How does the writer describe the finances?",
         "options": ["They are healthier than expected.",
                     "They are difficult, and the members accept this.",
                     "They will improve in the fourth year.",
                     "They are hidden from the members."],
         "answer": "B"},
    ],
}

R_PART4 = {
    "intro": "Read the text below and choose the correct answer for each gap.",
    "title": "Library opens at night during exam season",
    "text": "The city library will stay open until two in the morning for "
            "six weeks, after students (16) ......... out that there was "
            "nowhere quiet to work once the university buildings closed. The "
            "trial was (17) ......... last spring and proved far more "
            "popular than the council had expected, with more than four "
            "hundred people using the building after midnight in the first "
            "month alone. Staff say the late hours (18) ......... them to "
            "rearrange shifts, and two extra security staff have been "
            "(19) ......... on for the period. The council has not yet "
            "decided whether the scheme will (20) ......... beyond the exam "
            "season.",
    "gaps": [
        {"q": 16, "options": ["pointed", "showed", "told", "spoke"],
         "answer": "A"},
        {"q": 17, "options": ["run", "held", "made", "taken"],
         "answer": "A"},
        {"q": 18, "options": ["forced", "made", "let", "obliged"],
         "answer": "A"},
        {"q": 19, "options": ["put", "taken", "signed", "brought"],
         "answer": "B"},
        {"q": 20, "options": ["continue", "keep", "remain", "follow"],
         "answer": "A"},
    ],
}

R_PART5 = {
    "intro": "Read the text. Think of the word which best fits each gap. "
             "Write ONE word for each gap.",
    "title": "From: Nilufar   To: Chris",
    "text": "Hi Chris,\n\nSorry it has taken me so long to reply. I "
            "(21) ......... been meaning to write since the wedding and "
            "somehow a month has gone past.\n\nThe new job is going well, "
            "better (22) ......... I expected. The building is enormous and "
            "for the first fortnight I had no idea (23) ......... anything "
            "was, but people have been kind about it. The only problem is "
            "the journey, (24) ......... takes me an hour each way.\n\nAre "
            "you still coming in November? If so, tell me early "
            "(25) ......... that I can book the days off.\n\nNilufar",
    "gaps": [
        {"q": 21, "answer": "have"},
        {"q": 22, "answer": "than"},
        {"q": 23, "answer": "where"},
        {"q": 24, "answer": "which"},
        {"q": 25, "answer": "so"},
    ],
}

WRITING1 = {
    "task": "You have been given two tickets to a concert next Saturday and "
            "you want your English friend Robin to come. Write an email to "
            "Robin. In your email:",
    "points": ["tell Robin about the concert",
               "explain how you got the tickets",
               "suggest where to meet."],
    "words": "Write 35-45 words.",
}

WRITING2 = {
    "task": "This is part of an email you receive from an English friend. "
            "Now write an email, giving your friend some advice.",
    "quote": "I've been offered a job in another city. The money is much "
             "better but I'd have to leave my family and start again "
             "somewhere I don't know anybody. I have to answer by Friday. "
             "What would you do?",
    "words": "Write about 100 words.",
}
