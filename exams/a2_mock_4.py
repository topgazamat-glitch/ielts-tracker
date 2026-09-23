"""A2 mock final, paper 4. Same skeleton and same level as the real finals.

Checked by exams/check_paper.py against the measurements of Test 1 and Test 2.
"""

NARRATOR = "Daniel"
MAN, WOMAN, MAN2, WOMAN2 = "Rocko", "Shelley", "Reed", "Flo (English (UK))"

PART1 = [
    {
        "q": 1, "ask": "What will the man have to drink?",
        "options": ["Tea", "Coffee", "Water"], "answer": "C",
        "lines": [
            (WOMAN, "Tea or coffee?"),
            (MAN, "I've had three coffees already today."),
            (WOMAN, "Tea, then. I'm making some."),
            (MAN, "No, thank you. Just some cold water, please."),
        ],
    },
    {
        "q": 2, "ask": "Which floor is the office on?",
        "options": ["The second", "The third", "The fifth"], "answer": "B",
        "lines": [
            (MAN2, "Is Mrs Khan's office on the fifth floor?"),
            (WOMAN2, "It was, but they all moved in September."),
            (MAN2, "The second, then?"),
            (WOMAN2, "One more. Third floor, the door at the end."),
        ],
    },
    {
        "q": 3, "ask": "What time did the train arrive?",
        "options": ["At two", "At half past two", "At three"], "answer": "A",
        "lines": [
            (WOMAN, "Was the train late again?"),
            (MAN, "It was early. Ten minutes early."),
            (WOMAN, "So half past two?"),
            (MAN, "No, the train is at ten past two. It came at two o'clock."),
        ],
    },
    {
        "q": 4, "ask": "What is the girl going to study?",
        "options": ["Medicine", "Languages", "Music"], "answer": "B",
        "lines": [
            (MAN2, "Your mother says you want to be a doctor, Sevara."),
            (WOMAN2, "She would like that. I don't."),
            (MAN2, "You play the piano so well. Music?"),
            (WOMAN2, "Music is my hobby. I'm going to study languages."),
        ],
    },
    {
        "q": 5, "ask": "Where did they leave the car?",
        "options": ["Near the hotel", "Behind the museum",
                    "In front of the park"], "answer": "B",
        "lines": [
            (WOMAN, "Did we leave the car near the hotel?"),
            (MAN2, "We couldn't. There was no space."),
            (WOMAN, "In front of the park?"),
            (MAN2, "No, behind the museum. There's a big car park there."),
        ],
    },
]

PART2 = {
    "intro": "Listen to Omar telling a friend about the people who work in "
             "his hotel. What does each person do? For questions 6 to 10, "
             "write a letter A to H next to each person.",
    "people": [("6", "Omar"), ("7", "Julia"), ("8", "Mr Ford"),
               ("9", "Anna"), ("10", "Peter")],
    "options": [("A", "cooks the food"), ("B", "cleans the rooms"),
                ("C", "carries the bags"), ("D", "works at the desk"),
                ("E", "looks after the garden"), ("F", "drives the guests"),
                ("G", "mends things"), ("H", "answers the telephone")],
    "answers": {"6": "D", "7": "A", "8": "G", "9": "E", "10": "F"},
    "lines": [
        (WOMAN2, "How many people work in the hotel, Omar?"),
        (MAN, "Eight of us. I'm at the desk from seven in the morning. I "
              "used to carry the bags, but not now."),
        (WOMAN2, "And Julia? Does she work with you at the desk?"),
        (MAN, "Julia is the cook. She makes breakfast for forty people every "
              "morning and she is never late."),
        (WOMAN2, "What about Mr Ford?"),
        (MAN, "If anything breaks, Mr Ford mends it. Last week it was a "
              "window and a door."),
        (WOMAN2, "Does Anna clean the rooms?"),
        (MAN, "Three other women do the rooms. Anna is outside all day. The "
              "garden is beautiful because of her."),
        (WOMAN2, "And Peter?"),
        (MAN, "Peter takes the guests to the airport in the hotel car. He "
              "answers the telephone in the evening as well, but the car is "
              "his real job."),
    ],
}

PART3 = {
    "intro": "Listen to a woman talking to a man about renting a flat. For "
             "questions 11 to 15, tick A, B or C.",
    "questions": [
        {"q": 11, "stem": "The flat has",
         "options": ["one bedroom.", "two bedrooms.",
                     "three bedrooms."], "answer": "B"},
        {"q": 12, "stem": "The flat is",
         "options": ["above a shop.", "near the park.",
                     "next to the station."], "answer": "A"},
        {"q": 13, "stem": "The rent is",
         "options": ["£400 a month.", "£450 a month.",
                     "£500 a month."], "answer": "B"},
        {"q": 14, "stem": "The woman can move in on",
         "options": ["the first of May.", "the tenth of May.",
                     "the first of June."], "answer": "C"},
        {"q": 15, "stem": "The flat does not have",
         "options": ["a cooker.", "a fridge.", "a washing machine."],
         "answer": "C"},
    ],
    "lines": [
        (WOMAN, "I'm calling about the flat in the newspaper. How many "
                "bedrooms are there?"),
        (MAN2, "Two. There was a three-bedroom flat, but somebody took it "
               "yesterday."),
        (WOMAN, "Where exactly is it?"),
        (MAN2, "Above a shop in the main street. It's ten minutes from the "
               "park and about twenty from the station."),
        (WOMAN, "Is it noisy?"),
        (MAN2, "The shop closes at six, so the evenings are quiet."),
        (WOMAN, "And how much is the rent?"),
        (MAN2, "Four hundred and fifty pounds a month. The small flats are "
               "four hundred, and five hundred is the one with the garden."),
        (WOMAN, "When can I move in?"),
        (MAN2, "The students leave on the tenth of May, and we paint it "
               "after that. So the first of June."),
        (WOMAN, "Is there a cooker?"),
        (MAN2, "A cooker and a fridge, both new. There's no washing machine, "
               "but there is one downstairs that everybody uses."),
    ],
}

PART4 = {
    "intro": "You will hear a man telling his colleague about a meeting. "
             "Listen and complete questions 16 to 20.",
    "title": "MEETING",
    "gaps": [
        {"q": 16, "label": "Day", "answer": "Wednesday"},
        {"q": 17, "label": "Time", "answer": "2.15"},
        {"q": 18, "label": "Room number", "answer": "203"},
        {"q": 19, "label": "Bring the", "answer": "photographs"},
        {"q": 20, "label": "Ask for Miss", "answer": "Brennan"},
    ],
    "lines": [
        (MAN, "Can you come to the meeting about the new shop?"),
        (WOMAN2, "Of course. It's Tuesday, isn't it?"),
        (MAN, "It was, but two people can't come on Tuesday, so it's "
              "Wednesday now."),
        (WOMAN2, "What time?"),
        (MAN, "Quarter past two. Not two o'clock. People always arrive late, "
              "so we start at quarter past."),
        (WOMAN2, "Which room?"),
        (MAN, "Two oh three, on the second floor. The big room, not the "
              "little one we used last time."),
        (WOMAN2, "Do I need to bring anything?"),
        (MAN, "Bring the photographs of the old shop. Everybody wants to see "
              "them. I'll bring the numbers."),
        (WOMAN2, "And who do I ask for at the desk?"),
        (MAN, "Miss Brennan. B - R - E - N - N - A - N. She has the key to "
              "the room."),
    ],
}


# ----------------------------------------------------- READING AND WRITING

R_PART1 = {
    "intro": "Which notice (A-H) says this (1-5)? For questions 1 to 5, mark "
             "the correct letter A-H on the answer sheet.",
    "notices": [
        ("A", "PLEASE SHOW YOUR TICKET TO THE DRIVER"),
        ("B", "NO BICYCLES BEYOND THIS POINT"),
        ("C", "FRESH BREAD EVERY MORNING AT 7"),
        ("D", "ROOM FULL - PLEASE WAIT OUTSIDE"),
        ("E", "PLEASE TAKE OFF YOUR SHOES"),
        ("F", "DOCTOR AWAY UNTIL 14 MARCH"),
        ("G", "MOBILE PHONES MUST BE SWITCHED OFF"),
        ("H", "PAY AT THE MACHINE BEFORE YOU RETURN TO YOUR CAR"),
    ],
    "items": [
        (1, "You cannot see this person for two weeks.", "F"),
        (2, "You must pay for your parking first.", "H"),
        (3, "You must let the driver see this.", "A"),
        (4, "You cannot ride here.", "B"),
        (5, "You cannot go in until somebody comes out.", "D"),
    ],
}

R_PART2 = {
    "intro": "Read the sentences about a birthday and choose the correct "
             "answer for each gap.",
    "items": [
        (6, "Dilnoza ……………… twenty on the fourth of April.",
         ["had", "was", "did"], "B"),
        (7, "Her friends ……………… a party for her at their house.",
         ["made", "did", "held"], "C"),
        (8, "Everybody brought a small ……………… .",
         ["present", "money", "shop"], "A"),
        (9, "They ……………… photographs all evening.",
         ["made", "took", "did"], "B"),
        (10, "It was the ……………… birthday she has ever had.",
         ["good", "better", "best"], "C"),
    ],
}

R_PART3 = {
    "intro": "Read the article about Marco and answer the questions. For each "
             "question, mark A, B or C on the answer sheet.",
    "title": "A TEACHER IN THE MOUNTAINS",
    "text": [
        "Marco Belli teaches in a very small school in the mountains in the "
        "north of Italy. There are only nine children in the school, and "
        "they are between six and eleven years old. They sit in one "
        "classroom, and Marco teaches all of them together.",
        "Marco grew up in Milan, a city of more than a million people. He "
        "studied there and taught in a large school with two thousand "
        "students. He says the job was easy but he was not happy, because "
        "he never learned all their names.",
        "Six years ago he saw an advertisement for the mountain school. His "
        "friends thought it was a terrible idea. The village is forty "
        "minutes from the nearest town and in winter the road is sometimes "
        "closed for several days.",
        "Marco says the difficult part is not the snow but the planning. "
        "Every lesson must work for a child of six and a child of eleven at "
        "the same time. The easy part is everything else. He knows all nine "
        "families, and after lessons the children show him where the best "
        "mushrooms grow.",
    ],
    "questions": [
        {"q": 11, "stem": "In Marco's school there are",
         "options": ["nine children.", "nine classes.",
                     "nine teachers."], "answer": "A"},
        {"q": 12, "stem": "In Milan, Marco was not happy because",
         "options": ["the school was old.", "he did not know the students.",
                     "the work was hard."], "answer": "B"},
        {"q": 13, "stem": "Marco's friends thought the new job was",
         "options": ["interesting.", "a bad idea.",
                     "well paid."], "answer": "B"},
        {"q": 14, "stem": "Marco says the hardest part of the job is",
         "options": ["the snow.", "the long road.",
                     "preparing the lessons."], "answer": "C"},
        {"q": 15, "stem": "In the afternoon the children",
         "options": ["stay in the classroom.", "go to the town.",
                     "take him into the forest."], "answer": "C"},
    ],
}

R_PART4 = {
    "intro": "Read the article about rice and answer the questions. For each "
             "question, mark A, B or C on the answer sheet.",
    "title": "RICE",
    "text": ("More people eat rice 16 …………… any other food in the world. "
             "Farmers have grown it for thousands 17 …………… years, and in "
             "some countries a family eats rice three times a day. Rice "
             "needs a great deal of water, 18 …………… farmers often grow it in "
             "fields that are under water. The work is difficult and much of "
             "it is 19 …………… by hand. When the rice is ready, the fields "
             "become dry and golden. There 20 …………… more than forty thousand "
             "different kinds of rice, and some of them are black or red."),
    "items": [
        (16, ["that", "than", "then"], "B"),
        (17, ["of", "from", "in"], "A"),
        (18, ["but", "so", "or"], "B"),
        (19, ["do", "did", "done"], "C"),
        (20, ["is", "are", "was"], "B"),
    ],
}

R_PART5 = {
    "intro": "Read the text. Think of the word which fits each gap. Write ONE "
             "word for each gap.",
    "letters": [
        ("Dear Sir or Madam,",
         "I stayed (Example: at) your hotel last weekend with my family. "
         "When we got home, I found that I 21 …………… left a camera in room "
         "twelve. It is small and black, 22 …………… it is very important to "
         "me. Could you tell me 23 …………… anybody has found it?",
         "Yours faithfully,\nPeter Lang"),
        ("Dear Mr Lang,",
         "Thank you for your letter. I am pleased 24 …………… tell you that we "
         "have your camera. We will keep it here 25 …………… you come. The desk "
         "is open every day until nine in the evening.",
         "Yours sincerely,\nHelena Marsh"),
    ],
    "answers": {21: "had", 22: "but", 23: "if / whether", 24: "to",
                25: "until / till"},
}

WRITING = {
    "task": "Write an email to an English friend. You have moved to a new "
            "town. Include:",
    "points": ["where the town is",
               "when you moved",
               "one thing you like and one thing you do not like",
               "invite your friend to visit"],
    "words": "Write at least 50 words.",
}
