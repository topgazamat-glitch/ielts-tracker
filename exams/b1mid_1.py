"""B1 mid-course test 1 - Reading and Writing, for the Pre-Intermediate classes.

Built to the official Empower B1 Mid-Course Competency test, which is a
different animal from the final. Its texts are long but plain: the YES/NO
passage runs 459 words at 15.3 words a sentence with 7% long words, and the
article is 279 words at 10.7 words a sentence. Long and plain, not short and
dense. exams/check_paper.py holds those bands.

Half way through the course, so the language stays inside what has been
taught by then: present and past simple, present continuous, present perfect
for experience, comparatives, going to, have to, should. No conditionals, no
passive, no reported speech.

EXAM_SKILLS is shown at the top of the paper, before the questions. A mid
test is a teaching instrument as much as a measurement, and the part that
students most often lose marks to is not the language but not knowing how
the paper works.
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
         "text": "Dilnoza - I'm at the library until five. Your book is on "
                 "the kitchen table, not in my bag. Don't wait for me to "
                 "get home before you leave. Mum",
         "ask": "What does Dilnoza's mother want her to do?",
         "options": ["Bring the book to the library.",
                     "Go out without waiting for her.",
                     "Wait at home until five."],
         "answer": "B"},
        {"q": 2,
         "text": "SWIMMING LESSONS FOR BEGINNERS START AGAIN ON 6 MARCH. "
                 "BOOK BY 1 MARCH - WE CANNOT ACCEPT LATE BOOKINGS.",
         "ask": "What does the notice tell people?",
         "options": ["The lessons begin on 1 March.",
                     "They must book before a certain date.",
                     "Beginners cannot join this course."],
         "answer": "B"},
        {"q": 3,
         "text": "From: Bek. The match is still on, but they have moved it "
                 "to the other pitch, the one behind the school. Same time. "
                 "Tell Jasur - I haven't got his number.",
         "ask": "Why is Bek writing?",
         "options": ["To say the match has been cancelled.",
                     "To say the place has changed.",
                     "To ask for Jasur's number."],
         "answer": "B"},
        {"q": 4,
         "text": "Please leave the key with the neighbour at number 14 when "
                 "you go. Do not post it through our door - we will not be "
                 "back for two weeks and we need it before then.",
         "ask": "What are the guests asked to do with the key?",
         "options": ["Put it through the door.",
                     "Keep it for two weeks.",
                     "Give it to somebody nearby."],
         "answer": "C"},
        {"q": 5,
         "text": "I went last Saturday. The food was good and it wasn't "
                 "expensive, but we waited fifty minutes for it. Go early "
                 "or go somewhere else if you are hungry.",
         "ask": "What is the writer's opinion of the restaurant?",
         "options": ["The food is poor.",
                     "It is too expensive.",
                     "The service is slow."],
         "answer": "C"},
    ],
}

R_PART2 = {
    "intro": "Look at the sentences below about a village market. Read the "
             "text to decide if each sentence is correct or incorrect. If it "
             "is correct, choose YES. If it is not correct, choose NO.",
    "title": "The market that comes back every Saturday",
    "text": [
        "If you drive out of the city on a Saturday morning and keep going "
        "for about forty minutes, you come to a small village with one "
        "street and a square in the middle. For six days of the week the "
        "square is a car park. On the seventh it is a market, and it has "
        "been a market on that same day for more than two hundred years.",
        "There are usually about thirty stalls. Some of them sell things you "
        "would expect: fruit, vegetables, bread, cheese, eggs. Others are "
        "harder to explain. One man sells only honey, and he has sold only "
        "honey since 1998. Another sells old tools. There is a woman who "
        "mends chairs while you wait, and a boy of sixteen who repairs "
        "phones at a table with a paper sign on it.",
        "The prices are not always cheaper than the supermarket in town, and "
        "the people who come know this. They come because they like talking "
        "to the person who grew the food. Farkhod Yusupov has had the "
        "vegetable stall for nineteen years and says he knows the names of "
        "perhaps half his customers, and the names of their children too.",
        "It is busiest between nine and eleven. After that the crowd thins "
        "out, and by one o'clock the stalls are coming down. There is no "
        "music and there are no tourists. The village is too far from the "
        "main road for that, which the traders say is exactly why it still "
        "works. A market that becomes famous stops being a market and starts "
        "being a show.",
        "In the winter it is cold and wet and fewer people come, but nobody "
        "has ever suggested stopping for those months. The honey man puts up "
        "a small tent. The chair woman brings an electric heater and an "
        "enormous flask of tea. They open at eight, exactly as they always "
        "have, and they will be there next Saturday too.",
        "The council has twice offered to build a permanent covered "
        "building, with electricity and proper toilets and somewhere "
        "comfortable to sit. On both occasions the traders themselves said "
        "no. Farkhod explained their reasoning to me carefully, and it was "
        "not what I expected. A building has to be paid for, he said, and "
        "then the rent goes up, and then only the stalls that sell the "
        "popular things can afford to stay. The honey would go first. "
        "Nobody wants a market where everything sells equally well, because "
        "that is a supermarket with worse parking.",
    ],
    "statements": [
        {"q": 6, "text": "The square is used for parking during the week.",
         "answer": "YES"},
        {"q": 7, "text": "All the stalls sell food.", "answer": "NO"},
        {"q": 8, "text": "Everything at the market costs less than in the "
                         "supermarket.",
         "answer": "NO"},
        {"q": 9, "text": "Farkhod Yusupov knows all of his customers by name.",
         "answer": "NO"},
        {"q": 10, "text": "The market continues through the winter.",
         "answer": "YES"},
    ],
}

R_PART3 = {
    "intro": "Read the text and questions below. For each question, choose "
             "the correct answer A, B or C.",
    "title": "My first week as a tour guide",
    "text": [
        "I have had a lot of jobs, but I have never had one like this. Last "
        "month I started work as a tour guide in my own city. I thought it "
        "would be easy. I was born here. I know every street.",
        "On my first morning there were eleven people waiting for me. They "
        "were from five different countries. One man asked me how old the "
        "old bridge was, and I did not know. I said I would find out. That "
        "night I read for three hours.",
        "The hardest part is not the history. It is walking backwards. A "
        "guide has to walk backwards to talk to the group, and on my second "
        "day I walked into a bin. Everybody laughed, including me, and after "
        "that the tour went better. I have learned that a small accident "
        "early is not a problem. It makes people relax.",
        "People ask about strange things. They do not ask about kings. They "
        "ask what I eat for breakfast, how much my flat costs, whether I am "
        "married. At first I thought this was rude. Now I think they want a "
        "real person, not a book.",
        "I have done nine tours now. I am tired every evening and my feet "
        "hurt, but I have not been bored once. Last week a woman from "
        "Germany sent me a photograph of her family on the old bridge, with "
        "a short message underneath. She had remembered my name. I have had "
        "better paid jobs, certainly, but nobody ever sent me a photograph "
        "afterwards.",
        "My sister asked me on Sunday whether I was going to continue. I "
        "said yes before she had finished the question.",
    ],
    "questions": [
        {"q": 11, "ask": "Why did the writer think the job would be easy?",
         "options": ["He had done it before.",
                     "He knows the city well.",
                     "He had studied history."], "answer": "B"},
        {"q": 12, "ask": "What did the writer do after the first tour?",
         "options": ["He looked for another job.",
                     "He apologised to the group.",
                     "He spent the evening reading."], "answer": "C"},
        {"q": 13, "ask": "What does the writer say about the accident on the "
                         "second day?",
         "options": ["It helped the group feel comfortable.",
                     "It made him stop walking backwards.",
                     "It stopped him finishing the tour."], "answer": "A"},
        {"q": 14, "ask": "How does the writer feel now about personal "
                         "questions?",
         "options": ["He finds them rude.",
                     "He understands why people ask them.",
                     "He refuses to answer them."], "answer": "B"},
        {"q": 15, "ask": "Which of these would be a good title for this text?",
         "options": ["Why I left my job in the city",
                     "The history every guide must know",
                     "What nobody told me about being a guide"],
         "answer": "C"},
    ],
}

R_PART4 = {
    "intro": "Read the text below and choose the correct answer for each gap.",
    "title": "A library for bicycles",
    "text": "A town in the north has opened what it calls a bicycle library, "
            "where children can borrow a bicycle (16) ......... three months "
            "and then change it for a bigger one. Children grow quickly, and "
            "parents (17) ......... to buy a new bicycle every year or two. "
            "The library has ninety bicycles and there is already a waiting "
            "list. Families (18) ......... five pounds a month, and the "
            "council says the scheme (19) ......... much cheaper than it "
            "expected. Other towns have (20) ......... asked how it works.",
    "gaps": [
        {"q": 16, "options": ["for", "since", "during"], "answer": "A"},
        {"q": 17, "options": ["must", "have", "should"], "answer": "B"},
        {"q": 18, "options": ["pay", "pays", "are paying"], "answer": "A"},
        {"q": 19, "options": ["has been", "is being", "was being"],
         "answer": "A"},
        {"q": 20, "options": ["yet", "still", "already"], "answer": "C"},
    ],
}

R_PART5 = {
    "intro": "Read the text. Think of the word which best fits each gap. "
             "Write ONE word for each gap.",
    "title": "From: Madina   To: Sam",
    "text": "Hi Sam,\n\nThank you (21) ......... the birthday message. Sorry "
            "I did not answer sooner - I (22) ......... been away with my "
            "family.\n\nWe went to the mountains for a week. It was colder "
            "(23) ......... we expected and I did not take a warm coat, so I "
            "wore my brother's. There were no shops, so we cooked everything "
            "ourselves.\n\nAre you still coming in May? If you are, tell me "
            "early (24) ......... I can ask for the days off. I would like "
            "(25) ......... show you the mountains too.\n\nMadina",
    "gaps": [
        {"q": 21, "answer": "for"},
        {"q": 22, "answer": "have"},
        {"q": 23, "answer": "than"},
        {"q": 24, "answer": "so"},
        {"q": 25, "answer": "to"},
    ],
}

WRITING1 = {
    "task": "Your English friend Sam is coming to your city next month. "
            "Write an email to Sam. In your email:",
    "points": ["say which month is best to come",
               "tell Sam one place you will take them",
               "say what clothes to bring."],
    "words": "Write 35-45 words.",
}

WRITING2 = {
    "task": "This is part of an email you receive from an English friend. "
            "Now write an email, giving your friend some advice.",
    "quote": "I want to learn to drive but lessons here are expensive and my "
             "brother says he can teach me for free. My mother thinks that "
             "is a bad idea. I can't decide. What would you do?",
    "words": "Write about 100 words.",
}
