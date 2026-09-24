"""B1 mid-course test 5 - Reading and Writing, for the Pre-Intermediate classes.

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
         "text": "Rustam - I've paid the deposit for the hall but they want "
                 "the rest a week before, not on the day. Can you transfer "
                 "your half by Friday? Otherwise we lose the booking. Kamola",
         "ask": "What does Kamola need from Rustam?",
         "options": ["His share of the money soon.",
                     "Help with booking the hall.",
                     "A decision about the date."],
         "answer": "A"},
        {"q": 2,
         "text": "PLEASE DO NOT LEAVE BAGS ON THE SEATS. THE TRAIN IS BUSY "
                 "AND OTHER PASSENGERS NEED SOMEWHERE TO SIT.",
         "ask": "What are passengers asked to do?",
         "options": ["Keep bags off the seats.",
                     "Move to another carriage.",
                     "Buy a ticket for their luggage."],
         "answer": "A"},
        {"q": 3,
         "text": "From: the dentist. Your appointment on the 12th has been "
                 "moved to the 19th at the same time. If that does not suit "
                 "you, call us; otherwise we will see you then.",
         "ask": "What should the patient do if the new date is fine?",
         "options": ["Telephone to confirm.",
                     "Do nothing.",
                     "Come on the 12th as planned."],
         "answer": "B"},
        {"q": 4,
         "text": "The pool is closed for repairs. Members can use the pool "
                 "at the sports centre in the next street free of charge - "
                 "just show your card at their reception.",
         "ask": "What can members do while the pool is closed?",
         "options": ["Get their money back.",
                     "Swim somewhere else without paying.",
                     "Use the pool at certain hours."],
         "answer": "B"},
        {"q": 5,
         "text": "I read it in two evenings, which tells you something. The "
                 "ending is weak and one character is unnecessary, but I "
                 "have thought about it every day since I finished it.",
         "ask": "What is the writer's opinion of the book?",
         "options": ["It is perfect.",
                     "It has faults but stayed with her.",
                     "It is too long."],
         "answer": "B"},
    ],
}

R_PART2 = {
    "intro": "Look at the sentences below about a repair café. Read the text "
             "to decide if each sentence is correct or incorrect. If it is "
             "correct, choose YES. If it is not correct, choose NO.",
    "title": "Bring it in and we will try",
    "text": [
        "On the first Saturday of every month, a room above a bakery fills "
        "up with broken things. People arrive carrying toasters, lamps, "
        "radios, a chair with a wobbly leg, a child's bicycle. There are six "
        "volunteers with tools. There is a queue by half past nine. Nobody "
        "pays anything.",
        "The rule is that the owner has to stay. You cannot leave your "
        "toaster and come back at twelve. You sit next to the volunteer and "
        "you watch, and if you can hold something or pass something you are "
        "asked to do it. Gulnora Sattorova, who started the café three years "
        "ago, is firm about this. She says the point is not the toaster.",
        "About half of what arrives can be mended, which is lower than "
        "visitors expect. Some things are genuinely broken. Some things are "
        "made so that they cannot be opened at all without breaking them "
        "further, and the volunteers have a particular dislike of those.",
        "What surprises people most is how small the problems usually are. A "
        "wire has come loose. A switch is dirty. Something needs tightening "
        "with a tool that costs very little. Gulnora says that most of the "
        "objects in the room are not broken in any serious sense. They have "
        "simply stopped, and nobody has looked inside.",
        "The volunteers are not engineers, or at least most of them are not. "
        "There is a retired teacher who is the best person in the room with "
        "electrical things. There is a nurse who is good with anything "
        "mechanical. Two of them learned everything they know in this room, "
        "as visitors, over the past two years.",
        "The café has been asked to open more often and has refused every "
        "time. Once a month means that the volunteers still want to come. "
        "Gulnora says that something everybody enjoys can be ruined "
        "remarkably quickly by asking for more of it, and she has watched "
        "exactly that happen to two other good ideas in the town.",
        "There is one thing she did not expect at all. People arrive with a "
        "broken object and they stay for two hours, long after their own "
        "repair is finished. They drink tea and they watch somebody else's "
        "radio being taken apart. A man came in September with a lamp and "
        "has been every month since, and he now mends the kettles. Gulnora "
        "says she thought she was starting a repair service. What she "
        "actually started was a room where people sit together on a "
        "Saturday morning, and the toasters are the excuse.",
    ],
    "statements": [
        {"q": 6, "text": "Visitors must stay while their object is repaired.",
         "answer": "YES"},
        {"q": 7, "text": "Most of the things brought in can be mended.",
         "answer": "NO"},
        {"q": 8, "text": "The faults are usually serious.", "answer": "NO"},
        {"q": 9, "text": "All the volunteers trained as engineers.",
         "answer": "NO"},
        {"q": 10, "text": "The café has decided not to open more often.",
         "answer": "YES"},
    ],
}

R_PART3 = {
    "intro": "Read the text and questions below. For each question, choose "
             "the correct answer A, B or C.",
    "title": "Six months as the only English speaker",
    "text": [
        "I took a job in a small town where nobody spoke English. I had "
        "studied the local language for about four months, which I now know "
        "is nothing at all. I arrived with a dictionary and a great deal of "
        "confidence.",
        "The confidence lasted two days. On the third day I went to buy "
        "bread and could not understand the price. The woman said it three "
        "times, more slowly each time, and I still could not understand. In "
        "the end she wrote it on her hand and showed me. I was thirty-one "
        "years old and I wanted to cry.",
        "What helped was not studying harder. It was accepting that I was "
        "going to sound stupid for a long time. Once I stopped trying to say "
        "correct sentences and started saying any sentence at all, people "
        "began talking to me properly. They corrected me constantly and "
        "nobody was unkind about it.",
        "The strangest part was what happened to my own language. After four "
        "months I started forgetting simple English words in the middle of "
        "sentences. I rang my mother and could not remember the word for a "
        "thing you keep milk in. She thought I was joking.",
        "I am home now and I can have a proper conversation in a language I "
        "could not order bread in. People ask me what the secret is, and "
        "they want me to say something about apps or grammar books. The "
        "honest answer is that I was alone and I had no choice, and I do "
        "not recommend it to anybody who has one.",
    ],
    "questions": [
        {"q": 11, "ask": "How well prepared was the writer when he arrived?",
         "options": ["He spoke the language well.",
                     "He knew much less than he thought.",
                     "He had lived there before."], "answer": "B"},
        {"q": 12, "ask": "How did the woman in the shop help him?",
         "options": ["She wrote the number down.",
                     "She spoke English to him.",
                     "She gave him the bread free."], "answer": "A"},
        {"q": 13, "ask": "What made the difference for the writer?",
         "options": ["Studying more in the evenings.",
                     "Being willing to make mistakes.",
                     "Finding another English speaker."], "answer": "B"},
        {"q": 14, "ask": "What surprised him after four months?",
         "options": ["His own English got worse.",
                     "He stopped making mistakes.",
                     "He no longer needed a dictionary."], "answer": "A"},
        {"q": 15, "ask": "Which of these would be a good title for this text?",
         "options": ["The best way to learn a language",
                     "Why I will never travel again",
                     "It worked, and I would not advise it"],
         "answer": "C"},
    ],
}

R_PART4 = {
    "intro": "Read the text below and choose the correct answer for each gap.",
    "title": "A shop with no packaging",
    "text": "A shop that sells food without any packaging "
            "(16) ......... opened in the centre of town. Customers "
            "(17) ......... bring their own jars and bottles and fill them "
            "themselves. The owner said she (18) ......... going to open a "
            "second shop if the first one works. Prices are slightly "
            "(19) ......... than in the supermarket, but customers say they "
            "throw away far less rubbish at the end of the week. The shop "
            "(20) ......... been extremely busy every Saturday since it "
            "opened, and the owner has had to ask two friends to help her "
            "behind the counter.",
    "gaps": [
        {"q": 16, "options": ["has", "have", "had"], "answer": "A"},
        {"q": 17, "options": ["must", "have to", "should"], "answer": "B"},
        {"q": 18, "options": ["is", "was", "will"], "answer": "A"},
        {"q": 19, "options": ["high", "higher", "highest"], "answer": "B"},
        {"q": 20, "options": ["is", "has", "was"], "answer": "B"},
    ],
}

R_PART5 = {
    "intro": "Read the text. Think of the word which best fits each gap. "
             "Write ONE word for each gap.",
    "title": "From: Nodira   To: Alex",
    "text": "Hi Alex,\n\nThank you for your last message. Sorry I "
            "(21) ......... not written for so long - the exams have taken "
            "over my life.\n\nThey finish on the fourteenth. After that I "
            "am free for six weeks, which is longer (22) ......... last "
            "year. I want to learn to swim properly. I can swim a little, "
            "(23) ......... not well enough to be useful.\n\nIf you come in "
            "July we could go to the lake. Tell me (24) ......... you think. "
            "I hope everything is going well (25) ......... you.\n\nNodira",
    "gaps": [
        {"q": 21, "answer": "have"},
        {"q": 22, "answer": "than"},
        {"q": 23, "answer": "but"},
        {"q": 24, "answer": "what"},
        {"q": 25, "answer": "for / with"},
    ],
}

WRITING1 = {
    "task": "You are going to move to a new flat and you want your English "
            "friend Sam to help you. Write an email to Sam. In your email:",
    "points": ["say when you are moving",
               "ask Sam to help",
               "say what you would like Sam to do."],
    "words": "Write 35-45 words.",
}

WRITING2 = {
    "task": "This is part of an email you receive from an English friend. "
            "Now write an email, giving your friend some advice.",
    "quote": "I want to start running but I have tried three times and "
             "given up after a week each time. My friend says I should join "
             "a club, but I would be the slowest person there. What would "
             "you do?",
    "words": "Write about 100 words.",
}
