"""B1 mid-course test 4 - Reading and Writing, for the Pre-Intermediate classes.

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
         "text": "Sevara - the electrician came early and has finished. He "
                 "says don't use the kitchen sockets until tomorrow "
                 "morning. Everything else is fine. Payment on Friday. Mum",
         "ask": "What must Sevara avoid doing?",
         "options": ["Using one part of the house tonight.",
                     "Paying the electrician today.",
                     "Turning on any electricity."],
         "answer": "A"},
        {"q": 2,
         "text": "LIBRARY BOOKS MAY BE RENEWED ONCE BY TELEPHONE. AFTER "
                 "THAT THE BOOK MUST BE BROUGHT IN.",
         "ask": "What does the notice say about renewing books?",
         "options": ["Books cannot be renewed at all.",
                     "You can only renew by phone one time.",
                     "You must always come to the library."],
         "answer": "B"},
        {"q": 3,
         "text": "From: Coach. Training on Saturday is at the sports hall, "
                 "not the field, because of the rain. Bring indoor shoes - "
                 "you will not be allowed on the floor without them.",
         "ask": "What must players remember?",
         "options": ["To come to the field as usual.",
                     "To bring the right shoes.",
                     "To arrive earlier than normal."],
         "answer": "B"},
        {"q": 4,
         "text": "We are sorry that your order arrived damaged. Please keep "
                 "the box. We will send a driver to collect it on Tuesday "
                 "and your money will be returned that week.",
         "ask": "What is the customer asked to do?",
         "options": ["Return the item to the shop.",
                     "Throw away the packaging.",
                     "Keep the box until Tuesday."],
         "answer": "C"},
        {"q": 5,
         "text": "We stayed for five nights. It rained for three of them, "
                 "so we saw less than we hoped, but the owner lent us a car "
                 "and refused to take anything for it. I would go back.",
         "ask": "What does the writer say about the holiday?",
         "options": ["The weather spoiled it completely.",
                     "The owner was very generous.",
                     "It was more expensive than expected."],
         "answer": "B"},
    ],
}

R_PART2 = {
    "intro": "Look at the sentences below about a town orchestra. Read the "
             "text to decide if each sentence is correct or incorrect. If it "
             "is correct, choose YES. If it is not correct, choose NO.",
    "title": "The orchestra that meets in a supermarket",
    "text": [
        "On Tuesday evenings, after the last customer has gone, about thirty "
        "people carry instruments through the doors of a supermarket in a "
        "small town and set up their chairs between the shelves. They start "
        "at half past eight. They finish at ten. It is the only orchestra in "
        "the country that rehearses in a food shop, and it exists because "
        "the town hall burned down.",
        "That was in 2019. The orchestra had used the hall for forty years "
        "and suddenly had nowhere to go. They tried the school, but the "
        "school needed its rooms in the evening. They tried a church, which "
        "was too cold. The conductor, a retired engineer called Rustam "
        "Olimov, was about to tell everybody that the orchestra would stop.",
        "The manager of the supermarket heard about it from a customer. She "
        "offered them the shop after closing time, for nothing, and she has "
        "never asked for anything since. The only rule is that the "
        "instruments must be off the floor by ten, because the cleaners "
        "come at quarter past.",
        "It is a strange place to make music. The ceiling is low and the "
        "sound is dry, which the violinists dislike and the drummer loves. "
        "There is a fridge at the back that hums in a key nobody can agree "
        "on. In December it is very cold near the door.",
        "But something unexpected has happened to the audience. When the "
        "orchestra played in the town hall, about forty people came, and "
        "most of them were relatives. Now they give two concerts a year in "
        "the supermarket car park, and last summer more than six hundred "
        "people came. Rustam thinks he understands why. A concert hall tells "
        "you to be quiet and sit still. A car park does not.",
        "The town has raised money to rebuild the hall and it will open "
        "next year. The orchestra has been offered its old room back. At "
        "the meeting where this was discussed, the vote was surprisingly "
        "close, and in the end they decided to stay exactly where they "
        "are.",
        "Rustam was disappointed, and he admits it openly. He had played in "
        "that hall since he was nineteen and he wanted to conduct there one "
        "more time before he stops. But he says the younger players were "
        "almost completely united, and they were right about the reason. "
        "The supermarket is where the orchestra survived. The hall is where "
        "it nearly died. He has agreed to organise one concert in the new "
        "building, in the spring, and then never mention it again.",
    ],
    "statements": [
        {"q": 6, "text": "The orchestra started rehearsing in the "
                         "supermarket by choice.",
         "answer": "NO"},
        {"q": 7, "text": "The supermarket charges them nothing.",
         "answer": "YES"},
        {"q": 8, "text": "Everybody in the orchestra dislikes the sound of "
                         "the building.",
         "answer": "NO"},
        {"q": 9, "text": "More people come to their concerts now than "
                         "before.",
         "answer": "YES"},
        {"q": 10, "text": "They have decided to return to the town hall.",
         "answer": "NO"},
    ],
}

R_PART3 = {
    "intro": "Read the text and questions below. For each question, choose "
             "the correct answer A, B or C.",
    "title": "I learned to cook at thirty-four",
    "text": [
        "I am not going to pretend this is an interesting story. I simply "
        "could not cook. I lived alone for eleven years and I ate bread, "
        "eggs and food from the shop on the corner. I was not proud of it "
        "and I was not ashamed of it either. It was just true.",
        "Then my sister came to stay for a month while her flat was being "
        "repaired. On the second evening she looked in my kitchen and asked "
        "me a question that I still think about. She did not ask why I could "
        "not cook. She asked what I ate when I was sad.",
        "I did not have an answer. She said that was the problem. Everybody "
        "should have one thing they can make when the day has gone wrong, "
        "and it does not matter what it is.",
        "She taught me one particular dish. It took an hour and we prepared "
        "it four times during that month. The fourth time she sat at the "
        "table and let me do the whole thing alone, and she corrected "
        "practically nothing. I have made it about sixty times since "
        "then.",
        "I still cannot really cook. I know four things and one of them is "
        "eggs. But last winter a friend arrived in a terrible state after "
        "losing his job, and I cooked for him almost automatically, without "
        "thinking about it at all. He ate two enormous plates and stayed "
        "until midnight. My sister was completely right, and I have never "
        "admitted it to her, because she would be unbearable.",
    ],
    "questions": [
        {"q": 11, "ask": "How did the writer feel about not cooking?",
         "options": ["Embarrassed by it.",
                     "Neither proud nor ashamed.",
                     "Determined to change it."], "answer": "B"},
        {"q": 12, "ask": "What was unusual about his sister's question?",
         "options": ["She asked about feelings, not skill.",
                     "She asked it in front of other people.",
                     "She had asked it many times before."], "answer": "A"},
        {"q": 13, "ask": "What happened the fourth time they made the dish?",
         "options": ["It went wrong.",
                     "His sister cooked it for him.",
                     "He cooked it almost without help."], "answer": "C"},
        {"q": 14, "ask": "Why does the writer mention his friend?",
         "options": ["To show that he now cooks for other people.",
                     "To explain why he learned to cook.",
                     "To say that his friend taught him more."],
         "answer": "A"},
        {"q": 15, "ask": "Which of these would be a good title for this text?",
         "options": ["How to become a good cook in a month",
                     "One dish, and why it was enough",
                     "Why living alone is difficult"], "answer": "B"},
    ],
}

R_PART4 = {
    "intro": "Read the text below and choose the correct answer for each gap.",
    "title": "Night classes for parents",
    "text": "A college in the east of the city (16) ......... started "
            "offering classes for parents while their children are at "
            "evening clubs in the same building. Parents "
            "(17) ......... wait in the car park for an hour, and many of "
            "them said they would rather be learning something. The classes "
            "are (18) ......... popular than the college expected, and two "
            "of them are already full. Parents (19) ......... to pay only "
            "three pounds a session. The college (20) ......... going to add "
            "two more classes in January.",
    "gaps": [
        {"q": 16, "options": ["has", "have", "had"], "answer": "A"},
        {"q": 17, "options": ["used to", "use to", "are used"],
         "answer": "A"},
        {"q": 18, "options": ["more", "most", "much"], "answer": "A"},
        {"q": 19, "options": ["have", "has", "having"], "answer": "A"},
        {"q": 20, "options": ["is", "are", "was"], "answer": "A"},
    ],
}

R_PART5 = {
    "intro": "Read the text. Think of the word which best fits each gap. "
             "Write ONE word for each gap.",
    "title": "From: Bekzod   To: Chris",
    "text": "Hi Chris,\n\nSorry for the late reply. I (21) ......... been "
            "helping my uncle on his farm for two weeks and there was no "
            "internet there at all.\n\nIt was harder work (22) ......... I "
            "imagined. We started at five every morning. I have never been "
            "so tired, (23) ......... I slept better than I do at home. I "
            "would go again.\n\nAre you still planning to visit? September "
            "is better (24) ......... me than October. Let me know "
            "(25) ......... you have decided.\n\nBekzod",
    "gaps": [
        {"q": 21, "answer": "have"},
        {"q": 22, "answer": "than"},
        {"q": 23, "answer": "but"},
        {"q": 24, "answer": "for"},
        {"q": 25, "answer": "when"},
    ],
}

WRITING1 = {
    "task": "You have found a job for the summer and you want to tell your "
            "English friend Jo. Write an email to Jo. In your email:",
    "points": ["say what the job is",
               "say when you start",
               "tell Jo one thing you are worried about."],
    "words": "Write 35-45 words.",
}

WRITING2 = {
    "task": "This is part of an email you receive from an English friend. "
            "Now write an email, giving your friend some advice.",
    "quote": "I have to give a presentation in English next month in front "
             "of my whole class. I know the subject well but I get very "
             "nervous and I am afraid I will forget everything. How can I "
             "prepare?",
    "words": "Write about 100 words.",
}
