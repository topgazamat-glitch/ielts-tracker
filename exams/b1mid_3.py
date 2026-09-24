"""B1 mid-course test 3 - Reading and Writing, for the Pre-Intermediate classes.

Built to the official Empower B1 Mid-Course Competency test.
Checked by exams/check_paper.py.
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
         "text": "Malika - I've taken your bike because mine has a flat "
                 "tyre. I'll bring it back before seven. I've left mine in "
                 "the yard if you want to mend it. Otabek",
         "ask": "Why is Otabek writing?",
         "options": ["To ask to borrow a bike.",
                     "To say he has taken a bike.",
                     "To ask Malika to mend his bike."],
         "answer": "B"},
        {"q": 2,
         "text": "THE LIFT IS FOR STAFF AND VISITORS WITH HEAVY BAGS ONLY. "
                 "OTHER VISITORS SHOULD USE THE STAIRS ON THE LEFT.",
         "ask": "Who can use the lift?",
         "options": ["Anybody in the building.",
                     "Only people who work here.",
                     "Staff, and visitors carrying a lot."],
         "answer": "C"},
        {"q": 3,
         "text": "From: the teacher. I have marked your test. You passed, "
                 "but there were a lot of small mistakes with articles. "
                 "Look at page 42 again before Thursday's lesson.",
         "ask": "What is the teacher telling the student?",
         "options": ["The student failed the test.",
                     "The student should revise one area.",
                     "The test will be repeated on Thursday."],
         "answer": "B"},
        {"q": 4,
         "text": "Because of the storm, the bus to the airport will leave "
                 "from the main square this week, not from the station. The "
                 "times have not changed.",
         "ask": "What has changed?",
         "options": ["The time of the bus.",
                     "Where the bus starts from.",
                     "The price of the ticket."],
         "answer": "B"},
        {"q": 5,
         "text": "I bought one last year and I have used it almost every "
                 "day. It is not the cheapest, and the instructions are "
                 "useless, but it still works perfectly and I would buy it "
                 "again.",
         "ask": "What does the writer think about the product?",
         "options": ["It is good value despite one problem.",
                     "It broke after a year.",
                     "It is too expensive to recommend."],
         "answer": "A"},
    ],
}

R_PART2 = {
    "intro": "Look at the sentences below about a school swimming pool. Read "
             "the text to decide if each sentence is correct or incorrect. "
             "If it is correct, choose YES. If it is not correct, choose NO.",
    "title": "The pool the village built itself",
    "text": [
        "The school in the village had an old swimming pool. It was built in "
        "1974 and it had not worked properly since 2015. The water was cold. "
        "The roof leaked. In the end the school closed it, put a lock on the "
        "door, and told the children they would swim at the pool in the town "
        "instead, which was a forty minute bus ride away.",
        "That arrangement lasted one term. The bus cost money and the "
        "journey took most of the afternoon, so in practice the children "
        "swam less and less. By the summer, most classes had stopped going "
        "at all.",
        "A parent called Dilorom Nazarova asked the school how much it would "
        "cost to repair the old pool. The answer was a large number. She "
        "asked what the parts of that number were, and this turned out to be "
        "the important question. Most of it was labour. The materials "
        "themselves were not expensive.",
        "So the village did the labour. Over two summers, a group of parents "
        "and older students took out the broken heater, mended the roof, "
        "cleaned and painted the whole building, and laid a new floor around "
        "the edge. A builder in the village gave his time on Saturdays. An "
        "electrician who had gone to that school in the 1980s did the wiring "
        "and refused to be paid.",
        "The pool opened again in September. It is small and it is not "
        "beautiful, and the changing rooms are still cold. But the children "
        "swim twice a week now instead of once a month, and they do it in "
        "their own village. Dilorom says the best part is not the swimming. "
        "It is that about forty people worked on the building, and all of "
        "them walk past it every day and know which part is theirs.",
        "There is one difficulty nobody predicted. The pool now costs money "
        "to heat, and the school budget has not changed. For the moment the "
        "village pays for the electricity out of a fund it started during "
        "the repairs. That fund will not last for ever. Dilorom is "
        "completely relaxed about this, which surprised me. She said the "
        "hard part was never the money. The hard part was getting forty "
        "people to give up their Saturdays, and that has already "
        "happened. A village that has mended one thing together finds the "
        "next thing easier.",
    ],
    "statements": [
        {"q": 6, "text": "The old pool stopped working long before it was "
                         "closed.",
         "answer": "YES"},
        {"q": 7, "text": "Going to the town pool worked well for the school.",
         "answer": "NO"},
        {"q": 8, "text": "Most of the cost of the repair was for materials.",
         "answer": "NO"},
        {"q": 9, "text": "Some of the work was done by people who were not "
                         "paid.",
         "answer": "YES"},
        {"q": 10, "text": "The pool is now in perfect condition.",
         "answer": "NO"},
    ],
}

R_PART3 = {
    "intro": "Read the text and questions below. For each question, choose "
             "the correct answer A, B or C.",
    "title": "I worked in my parents' shop for a summer",
    "text": [
        "My parents have had the same small shop for twenty years. I grew up "
        "behind the counter. When I was a child I thought the shop was "
        "boring, and when I was a teenager I was slightly ashamed of it. "
        "Last summer I worked there full time for the first time.",
        "I thought I knew the job. I did not. In the first week I made three "
        "mistakes with the till and gave a woman too much change twice. My "
        "father did not say anything. He just stood next to me for two days "
        "and let me watch him.",
        "The thing nobody tells you is how much of a shop is remembering. My "
        "mother knows that the man who comes in at eight takes his coffee "
        "without sugar. She knows which customers are waiting for money at "
        "the end of the month and she lets them pay later without either of "
        "them ever mentioning it. None of this is written down anywhere.",
        "The hours are long. We opened at seven and closed at nine, six days "
        "a week, and my feet hurt in a way I had not expected. I understand "
        "now why my father never came to my football matches. I used to "
        "think he did not want to.",
        "I am going back to university in September and I am not going to "
        "run a shop. My parents understand this completely and they are "
        "glad. But I am not embarrassed about it any more, which is not the "
        "same thing as wanting it, and I explained that to my father on my "
        "last afternoon. He said he already knew.",
    ],
    "questions": [
        {"q": 11, "ask": "How did the writer feel about the shop as a "
                         "teenager?",
         "options": ["Proud of it.", "A little embarrassed.",
                     "Interested in running it."], "answer": "B"},
        {"q": 12, "ask": "What did the writer's father do after the "
                         "mistakes?",
         "options": ["He asked her to stop working.",
                     "He explained the rules carefully.",
                     "He let her learn by watching him."], "answer": "C"},
        {"q": 13, "ask": "What surprised the writer most about the work?",
         "options": ["How much her mother remembered about people.",
                     "How little money the shop made.",
                     "How few customers came in."], "answer": "A"},
        {"q": 14, "ask": "What does the writer now understand about her "
                         "father?",
         "options": ["Why he never sold the shop.",
                     "Why he missed her football matches.",
                     "Why he wanted her to study."], "answer": "B"},
        {"q": 15, "ask": "Which of these would be a good title for this text?",
         "options": ["Why I am going to take over the shop",
                     "The summer I stopped being ashamed",
                     "How to run a successful small business"],
         "answer": "B"},
    ],
}

R_PART4 = {
    "intro": "Read the text below and choose the correct answer for each gap.",
    "title": "A free bus for the hospital",
    "text": "A bus service that takes patients to the hospital for free "
            "(16) ......... started in the north of the city last month. The "
            "bus runs four times a day and anybody with an appointment "
            "(17) ......... use it. The council said that many patients "
            "(18) ......... missing appointments simply because the journey "
            "was too expensive. In the first month the bus carried nine "
            "hundred people, which is far (19) ......... than anybody "
            "expected. The service (20) ......... going to continue until at "
            "least June.",
    "gaps": [
        {"q": 16, "options": ["has", "have", "had"], "answer": "A"},
        {"q": 17, "options": ["must", "can", "should"], "answer": "B"},
        {"q": 18, "options": ["are", "have", "were"], "answer": "C"},
        {"q": 19, "options": ["more", "most", "much"], "answer": "A"},
        {"q": 20, "options": ["is", "are", "was"], "answer": "A"},
    ],
}

R_PART5 = {
    "intro": "Read the text. Think of the word which best fits each gap. "
             "Write ONE word for each gap.",
    "title": "From: Shahnoza   To: Jo",
    "text": "Hi Jo,\n\nThank you for the photographs. Your new flat looks "
            "much bigger (21) ......... the old one.\n\nI have some news. I "
            "(22) ......... changed jobs. I am working at a school now, "
            "which I never thought I would do. The children are noisy "
            "(23) ......... they are very funny, and I come home tired "
            "every day.\n\nMy sister is getting married in October, so I "
            "will be busy then. Could you come (24) ......... November "
            "instead? Tell me (25) ......... soon as you know.\n\nShahnoza",
    "gaps": [
        {"q": 21, "answer": "than"},
        {"q": 22, "answer": "have"},
        {"q": 23, "answer": "but"},
        {"q": 24, "answer": "in"},
        {"q": 25, "answer": "as"},
    ],
}

WRITING1 = {
    "task": "You cannot come to your English friend Robin's birthday party. "
            "Write an email to Robin. In your email:",
    "points": ["say that you cannot come",
               "explain why",
               "suggest another day to meet."],
    "words": "Write 35-45 words.",
}

WRITING2 = {
    "task": "This is part of an email you receive from an English friend. "
            "Now write an email, giving your friend some advice.",
    "quote": "I have been offered a place at a university in another city. "
             "It is a good course, but it is expensive and I would have to "
             "live alone for the first time. My parents say it is my "
             "decision. What would you do?",
    "words": "Write about 100 words.",
}
