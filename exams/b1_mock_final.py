"""An original B1 mock final, built to the shape of the real Empower paper.

The Pre-Intermediate students will sit the real B1 End-of-Course Competency
paper, so it cannot be handed out. This is a new paper on the same skeleton:

    LISTENING            20 marks   four parts, each heard twice
      Part 1  1-5        five short recordings, three options
      Part 2  6-10       complete the notes with a word or a number
      Part 3  11-15      one longer talk, three options
      Part 4  16-20      a conversation: is each sentence YES or NO?

    READING              25 marks   thirty minutes
      Part 1  1-5        five short texts, three options
      Part 2  6-10       one factual text: is each sentence YES or NO?
      Part 3  11-15      read an article, three options
      Part 4  16-20      grammar and vocabulary in a text, three options
      Part 5  21-25      write ONE word in each gap

    WRITING              two tasks, thirty minutes
      Question 1         a short email, 35-45 words, three things to include
      Question 2         a reply giving advice, about 100 words

B1 is not B1+ with easier words: the real paper's reading questions offer
three options rather than four, and its texts are shorter and more concrete.
Both of those are kept here.

The same declared difference as the other mocks: the real Listening Part 1
asks students to choose between three photographs, and I cannot draw them.
That part tests the same skill - one detail, five marks, three options - with
the options written out in words.
"""

# --------------------------------------------------------------- LISTENING

NARRATOR = "Daniel"
MAN, WOMAN, MAN2, WOMAN2 = "Rocko", "Shelley", "Reed", "Flo (English (UK))"

PART1 = [
    {
        "q": 1, "ask": "What did the woman forget to bring?",
        "options": ["Her umbrella", "Her keys", "Her phone charger"],
        "answer": "C",
        "lines": [
            (MAN, "You look worried. Have you locked yourself out again?"),
            (WOMAN, "No, the keys are here, and it isn't raining, so I don't "
                    "need the umbrella."),
            (MAN, "So what is it?"),
            (WOMAN, "I'm on five per cent and the charger is sitting on my "
                    "kitchen table."),
        ],
    },
    {
        "q": 2, "ask": "Where are they going to meet?",
        "options": ["At the station", "Outside the cinema",
                    "In front of the library"],
        "answer": "C",
        "lines": [
            (WOMAN, "Shall we meet at the station? It's easy to find."),
            (MAN, "It's always so crowded at six. What about outside the "
                  "cinema?"),
            (WOMAN, "They're building something there, you can't stand "
                    "anywhere. Let's say the library. There's a bench."),
            (MAN, "Perfect. The library at six, then."),
        ],
    },
    {
        "q": 3, "ask": "Why is the man learning to cook?",
        "options": ["To save money", "Because he has moved house",
                    "Because his sister asked him to"],
        "answer": "A",
        "lines": [
            (WOMAN, "Since when do you cook?"),
            (MAN, "Since I added up what I spent on takeaway food last "
                  "month."),
            (WOMAN, "And is the new flat better for it? A bigger kitchen?"),
            (MAN, "The kitchen is tiny, actually. But a bag of rice costs "
                  "almost nothing, so I'm learning."),
        ],
    },
    {
        "q": 4, "ask": "What time does the train leave?",
        "options": ["Half past seven", "Quarter to eight", "Eight o'clock"],
        "answer": "B",
        "lines": [
            (MAN, "The website said half past seven, didn't it?"),
            (WOMAN, "It did, but they changed it. Look at the board."),
            (MAN, "Seven forty-five. And it says the eight o'clock one is "
                  "cancelled."),
            (WOMAN, "Then we should hurry."),
        ],
    },
    {
        "q": 5, "ask": "What does the woman say about her new job?",
        "options": ["The people are friendly.", "The hours are long.",
                    "The office is far from her home."],
        "answer": "A",
        "lines": [
            (MAN, "How's the new job? I heard it's a long day."),
            (WOMAN, "Nine to five, same as before. And it's two stops on the "
                    "bus, so I can't complain about that either."),
            (MAN, "So what's the best part?"),
            (WOMAN, "Honestly, the team. On my first morning three people "
                    "asked me to lunch. That never happened anywhere else."),
        ],
    },
]

PART2 = {
    "intro": "You will hear a woman on the radio talking about a sports day "
             "in her town. For each question, write the correct answer in the "
             "gap. Write one or two words or a number.",
    "title": "Town Sports Day",
    "gaps": [
        {"q": 6, "label": "Date of the sports day", "answer": "20th May"},
        {"q": 7, "label": "Place if the weather is bad",
         "answer": "the sports hall"},
        {"q": 8, "label": "Starts at", "answer": "10 o'clock"},
        {"q": 9, "label": "Cost for children", "answer": "free"},
        {"q": 10, "label": "Money will be used for", "answer": "a new pool"},
    ],
    "lines": [
        (WOMAN2,
         "Now, before the news, a word about something happening in town. Our "
         "sports day is back. Last year we held it in April and it rained for "
         "six hours, so this time we have moved it later, to the twentieth of "
         "May. That's a Saturday, and the weather people are promising sun, "
         "although they promised that last year too."),
        (WOMAN2,
         "If it does rain, don't stay at home. Everything moves indoors to the "
         "sports hall next to the school. It's smaller, so there'll be no "
         "football, but everything else will go ahead."),
        (WOMAN2,
         "We start at ten o'clock. The gates open at half past nine, and there "
         "is tea and cake from nine, but the first race is at ten. Please be "
         "early if your child is running."),
        (WOMAN2,
         "Tickets are three pounds for adults. For children it costs nothing "
         "at all - they come in free - and that includes every race and every "
         "game. Families, please note that."),
        (WOMAN2,
         "And why are we doing it? Every penny goes towards a new pool for the "
         "town. The old one closed two years ago and the children have been "
         "travelling to Green Park ever since. So come along on the twentieth "
         "and bring your friends."),
    ],
}

PART3 = {
    "intro": "You will hear a man called Timur talking about a long walk he "
             "did last summer. For each question, choose the correct answer "
             "A, B or C.",
    "questions": [
        {"q": 11, "ask": "Why did Timur decide to do the walk?",
         "options": ["A friend suggested it.", "He read about it in a "
                     "magazine.", "He wanted to get fit."],
         "answer": "A"},
        {"q": 12, "ask": "How long did the walk take?",
         "options": ["Four days", "Six days", "Nine days"],
         "answer": "B"},
        {"q": 13, "ask": "What was the worst part for Timur?",
         "options": ["The heat", "The weight of his bag", "Being alone"],
         "answer": "B"},
        {"q": 14, "ask": "What does Timur say about the food?",
         "options": ["He carried all of it with him.",
                     "He bought it in villages along the way.",
                     "He ate in restaurants every evening."],
         "answer": "B"},
        {"q": 15, "ask": "What will Timur do differently next time?",
         "options": ["Take a friend", "Walk a shorter distance",
                     "Carry less"],
         "answer": "C"},
    ],
    "lines": [
        (WOMAN, "Timur, a hundred and forty kilometres on foot. Whose idea "
                "was that?"),
        (MAN,
         "Not mine! My friend Jasur had done it the year before and he would "
         "not stop talking about it. I read a few articles afterwards, but it "
         "was Jasur. He asked me in January and by March I had said yes."),
        (WOMAN, "And how long were you walking?"),
        (MAN,
         "The guidebook says four days if you are fast. I am not fast. I "
         "planned nine, because I wanted to enjoy it, and in the end it took "
         "six - the middle section was flatter than I expected."),
        (WOMAN, "What was the hardest part?"),
        (MAN,
         "Everyone assumes the heat, and yes, the afternoons were hot. But I "
         "started early each day so that was manageable. What nearly stopped "
         "me was my rucksack. I had packed for every possible situation and it "
         "weighed eighteen kilos. By day two my shoulders were in a terrible "
         "state. And I was walking alone, which I liked, actually."),
        (WOMAN, "Did you carry all your food as well?"),
        (MAN,
         "No, and that was the one clever decision I made. There is a village "
         "every fifteen kilometres or so, with a small shop, so I bought bread "
         "and fruit as I went. There were no restaurants - I cooked in the "
         "evenings - but I never went hungry."),
        (WOMAN, "Would you do it again?"),
        (MAN,
         "Tomorrow. Alone again, I think, and the same route, because I want "
         "to see the parts I walked past in the rain. But my bag will weigh "
         "eight kilos, not eighteen. I have already given half of that "
         "equipment away."),
    ],
}

PART4 = {
    "intro": "You will hear a conversation between Aziza and Pavel about "
             "shopping online. Decide if each sentence is correct or "
             "incorrect. If it is correct, choose YES. If it is incorrect, "
             "choose NO.",
    "statements": [
        {"q": 16, "text": "Aziza buys most of her clothes online.",
         "answer": "NO"},
        {"q": 17, "text": "Pavel and Aziza agree that returning things is "
                          "difficult.", "answer": "YES"},
        {"q": 18, "text": "Pavel thinks online shopping saves him money.",
         "answer": "NO"},
        {"q": 19, "text": "Aziza has had a parcel go missing.",
         "answer": "YES"},
        {"q": 20, "text": "Pavel offers to show Aziza a better website.",
         "answer": "YES"},
    ],
    "lines": [
        (MAN, "You've got another parcel, Aziza. You must buy everything "
              "online."),
        (WOMAN,
         "Books, yes. Anything electrical, yes. But not clothes - I have to "
         "try things on, so I still go into town for that. My sister is the "
         "opposite, she buys dresses she has never seen."),
        (MAN, "And when they don't fit? Sending things back is such a job."),
        (WOMAN,
         "It really is. You need the box, you need the label, then you queue "
         "at the post office. I have kept things I didn't want just to avoid "
         "it."),
        (MAN, "Exactly. Though at least it's cheaper online."),
        (WOMAN, "Is it? You always say that."),
        (MAN,
         "I say it, but I'm not sure I believe it any more. I buy far more "
         "than I used to, because it takes four seconds. I think I spend more "
         "now, not less."),
        (WOMAN,
         "Well, the worst thing that happened to me wasn't the money. A parcel "
         "simply never arrived - they said it was delivered, and it wasn't. It "
         "took eleven days and about nine messages to get anything back."),
        (MAN,
         "Which company was that? Actually, never mind - let me send you the "
         "site I use now. They're a bit slower but they have never once lost "
         "anything of mine, and you can return things in any shop."),
        (WOMAN, "Please do. I'd like to stop worrying every time I order "
                "something."),
    ],
}

# ----------------------------------------------------------------- READING

R_PART1 = {
    "intro": "Look at the text in each question. What does it say? For each "
             "question, choose the correct answer A, B or C.",
    "questions": [
        {"q": 1,
         "text": "LIBRARY COMPUTERS MAY BE USED FOR 30 MINUTES WHEN OTHERS "
                 "ARE WAITING",
         "ask": "What does the notice mean?",
         "options": ["You can never use a computer for more than 30 minutes.",
                     "There is a time limit only when the computers are busy.",
                     "You must book a computer 30 minutes in advance."],
         "answer": "B"},
        {"q": 2,
         "text": "Nodira - the delivery came but one box is missing. I've "
                 "signed for the rest. Don't pay the invoice until the last "
                 "box arrives. Rustam",
         "ask": "What does Rustam want Nodira to do?",
         "options": ["Sign for the delivery.",
                     "Wait before paying.",
                     "Order another box."],
         "answer": "B"},
        {"q": 3,
         "text": "Because of the concert, buses will not stop on Park Street "
                 "after 6 p.m. today. Please use the stop on Green Street.",
         "ask": "What are passengers told?",
         "options": ["No buses will run this evening.",
                     "They should get on at a different stop this evening.",
                     "Park Street is closed to traffic all day."],
         "answer": "B"},
        {"q": 4,
         "text": "Sara - I've booked the table for 8, not 7. Malika can't "
                 "finish work early after all. I'll still pick you up at "
                 "half past six so we can walk. Dad",
         "ask": "What has changed?",
         "options": ["The time of the meal.",
                     "The time Sara will be collected.",
                     "The way they will travel."],
         "answer": "A"},
        {"q": 5,
         "text": "SPECIAL OFFER: BUY ANY TWO JACKETS AND TAKE 20% OFF THE "
                 "CHEAPER ONE. OFFER ENDS SUNDAY.",
         "ask": "What does the offer say?",
         "options": ["Both jackets cost 20% less.",
                     "The discount applies to one jacket only.",
                     "You must spend 20 pounds to get the offer."],
         "answer": "B"},
    ],
}

R_PART2 = {
    "intro": "Look at the sentences below about research into sleep. Read the "
             "text to decide if each sentence is correct or incorrect. If it "
             "is correct, choose YES. If it is not correct, choose NO.",
    "title": "Why we sleep badly in a new place",
    "text": [
        "Almost everybody has had the experience of sleeping badly on the "
        "first night in a hotel, in a friend's house, or in a new flat. For a "
        "long time people believed this was simply because a strange bed feels "
        "uncomfortable, or because the room is too hot or too noisy.",

        "In 2016, a team of researchers in the United States decided to test "
        "this. They asked thirty-five volunteers to sleep in a laboratory for "
        "two nights, a week apart, and measured what happened in their brains "
        "while they slept. On the second night everybody slept normally. On "
        "the first night, something unusual was happening.",

        "The measurements showed that one side of the brain stayed more awake "
        "than the other. The volunteers were not conscious of this at all, but "
        "when the researchers played a quiet sound during the night, the group "
        "woke far more easily on the first night than on the second. Birds and "
        "dolphins do something similar, and in their case scientists have "
        "known about it for years.",

        "The researchers think the explanation is old. For most of human "
        "history, a new place was a dangerous place, and something in us has "
        "not forgotten that. The advice that follows is simple enough: take "
        "your own pillow if you can, and do not worry about the first night, "
        "because the second one is almost always better.",
    ],
    "statements": [
        {"q": 6, "text": "People used to think an uncomfortable bed was the "
                         "reason for sleeping badly.", "answer": "YES"},
        {"q": 7, "text": "The volunteers slept in the laboratory on two nights "
                         "in a row.", "answer": "NO"},
        {"q": 8, "text": "The volunteers knew that half of their brain was "
                         "staying awake.", "answer": "NO"},
        {"q": 9, "text": "The volunteers woke up more easily on the first "
                         "night.", "answer": "YES"},
        {"q": 10, "text": "The researchers believe the reason for this is very "
                          "old.", "answer": "YES"},
    ],
}

R_PART3 = {
    "intro": "Read the text and questions below. For each question, choose "
             "the correct answer A, B or C.",
    "title": "Working from home - two opinions",
    "text": [
        "When her company told everyone to work from home, Gulnora Saidova "
        "expected to hate it. She had always liked the office: the walk there, "
        "the coffee at eleven, the noise. Three years later she has no "
        "intention of going back. What changed her mind was not the extra hour "
        "in bed, which she says she stopped enjoying after a fortnight, but "
        "her daughter. She is there when the school bus arrives, every single "
        "day, and no job is worth giving that up again.",

        "It is not all easy. Gulnora admits that she finds it hard to stop "
        "working. In the office, people got up and left at six and she left "
        "with them. At home the laptop is always on the table, and she has "
        "answered messages at eleven at night more often than she would like. "
        "Her solution is to put the laptop in a cupboard at the end of the "
        "day, which sounds silly, she says, and works.",

        "Davron Umarov tried it for a year and went back. He lives alone, and "
        "by the third month he realised he was going whole days without "
        "speaking to anybody. The work itself was fine - better, if anything, "
        "because nobody interrupted him. But he began to feel he was "
        "disappearing. He now goes into the office three days a week and works "
        "at home on the other two, and says that this is the arrangement he "
        "would recommend to anyone.",

        "Both of them agree on one thing. Whatever you choose, do not decide "
        "in the first month. Gulnora hated it at first and Davron loved it, "
        "and by the end of the year each of them thought the opposite.",
    ],
    "questions": [
        {"q": 11, "ask": "Why does Gulnora want to keep working from home?",
         "options": ["She can sleep longer.", "She can see her daughter more.",
                     "She dislikes her office."],
         "answer": "B"},
        {"q": 12, "ask": "What problem does Gulnora have?",
         "options": ["She finds it difficult to finish work.",
                     "She misses her colleagues.",
                     "Her laptop is often broken."],
         "answer": "A"},
        {"q": 13, "ask": "Why did Davron go back to the office?",
         "options": ["His work was getting worse.",
                     "He was too often interrupted at home.",
                     "He was lonely."],
         "answer": "C"},
        {"q": 14, "ask": "What does Davron do now?",
         "options": ["He works at home two days a week.",
                     "He works in the office every day.",
                     "He works at home every day."],
         "answer": "A"},
        {"q": 15, "ask": "What do both of them advise?",
         "options": ["Work from home if you can.",
                     "Do not judge it too quickly.",
                     "Always keep an office desk."],
         "answer": "B"},
    ],
}

R_PART4 = {
    "intro": "Read the text below and choose the correct answer for each gap.",
    "title": "Drinking enough water",
    "text": "Most people know that they (16) ......... drink water during the "
            "day, but few of us drink as much as we should. The amount a "
            "person needs depends (17) ......... how active they are and on "
            "the weather. People (18) ......... work outside in summer need "
            "much more than the rest of us. If you feel tired in the "
            "afternoon, it may (19) ......... be because you are thirsty "
            "rather than hungry. A simple way to check is to keep a bottle on "
            "your desk and to (20) ......... how often you fill it.",
    "gaps": [
        {"q": 16, "options": ["should", "would", "could"], "answer": "A"},
        {"q": 17, "options": ["of", "on", "from"], "answer": "B"},
        {"q": 18, "options": ["what", "which", "who"], "answer": "C"},
        {"q": 19, "options": ["simply", "hardly", "nearly"], "answer": "A"},
        {"q": 20, "options": ["notice", "look", "watch"], "answer": "A"},
    ],
}

R_PART5 = {
    "intro": "Read the text. Think of the word which best fits each gap. "
             "Write ONE word for each gap.",
    "title": "From: Madina   To: Sevara",
    "text": "Hi Sevara,\n\nIt feels (21) ......... ages since we last spoke! "
            "I've been so busy (22) ......... the new course started. There "
            "are three essays to write before the end of the month and I "
            "haven't begun (23) ......... of them.\n\nAnyway, are you free on "
            "Sunday? If you (24) ......... , come round in the afternoon and "
            "we can cook something. I've got a recipe I want to try, and it's "
            "much easier (25) ......... the one we attempted last "
            "time!\n\nMadina",
    "gaps": [
        {"q": 21, "answer": "like"},
        {"q": 22, "answer": "since"},
        {"q": 23, "answer": "any"},
        {"q": 24, "answer": "are"},
        {"q": 25, "answer": "than"},
    ],
}

# ----------------------------------------------------------------- WRITING

WRITING1 = {
    "task": "Your English friend, Robin, is coming to your town next month "
            "and wants to know about a museum you have visited. Write an "
            "email to Robin. In your email:",
    "points": ["say which museum you visited and when",
               "explain what you liked about it",
               "suggest a day to go there together."],
    "words": "Write 35-45 words.",
}

WRITING2 = {
    "task": "This is part of an email you receive from an English friend. Now "
            "write an email, giving your friend some advice.",
    "quote": "I've been offered a place at a university in another city, but "
             "it means leaving my family and all my friends. My parents think "
             "I should stay here. I don't know what to do. What would you do?",
    "words": "Write about 100 words.",
}
