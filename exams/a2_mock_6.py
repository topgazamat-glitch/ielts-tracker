"""A2 mock final, paper 6. Same skeleton and same level as the real finals.

Checked by exams/check_paper.py against the measurements of Test 1 and Test 2.
"""

NARRATOR = "Daniel"
MAN, WOMAN, MAN2, WOMAN2 = "Rocko", "Shelley", "Reed", "Flo (English (UK))"

PART1 = [
    {
        "q": 1, "ask": "What is the man going to wear?",
        "options": ["A suit", "A jumper", "A jacket"], "answer": "C",
        "lines": [
            (WOMAN, "Are you wearing your suit tonight?"),
            (MAN2, "It's not that kind of dinner."),
            (WOMAN, "The blue jumper, then."),
            (MAN2, "It will be warm inside. Just a shirt and my jacket."),
        ],
    },
    {
        "q": 2, "ask": "What time does the lesson begin?",
        "options": ["At nine", "At quarter past nine", "At half past nine"],
        "answer": "B",
        "lines": [
            (MAN, "Does the lesson start at nine?"),
            (WOMAN2, "The building opens at nine."),
            (MAN, "And the lesson? Half past?"),
            (WOMAN2, "Quarter past nine. We finish at eleven."),
        ],
    },
    {
        "q": 3, "ask": "Which animal did they see?",
        "options": ["A fox", "A deer", "A bird"], "answer": "A",
        "lines": [
            (WOMAN2, "Was it a deer in the garden last night?"),
            (MAN, "Too small for a deer."),
            (WOMAN2, "A big bird?"),
            (MAN, "It ran across the grass. It was a fox, I'm sure."),
        ],
    },
    {
        "q": 4, "ask": "How much money did he spend?",
        "options": ["Twelve pounds", "Twenty pounds", "Twenty-two pounds"],
        "answer": "C",
        "lines": [
            (WOMAN, "Did you spend all twenty pounds?"),
            (MAN2, "More. The book was twelve."),
            (WOMAN, "And the rest?"),
            (MAN2, "Lunch was ten. So twenty-two altogether. I used my card."),
        ],
    },
    {
        "q": 5, "ask": "Who is ill?",
        "options": ["The woman", "Her son", "Her husband"], "answer": "B",
        "lines": [
            (MAN, "You look tired. Are you all right?"),
            (WOMAN2, "I'm fine. Nobody slept last night."),
            (MAN, "Is your husband ill again?"),
            (WOMAN2, "No, it's our little boy. He has a temperature."),
        ],
    },
]

PART2 = {
    "intro": "Listen to Yusuf telling a friend about the presents his family "
             "gave him. What did each person give him? For questions 6 to "
             "10, write a letter A to H next to each person.",
    "people": [("6", "His mother"), ("7", "His father"), ("8", "His sister"),
               ("9", "His grandmother"), ("10", "His friend Tim")],
    "options": [("A", "a watch"), ("B", "a book"), ("C", "money"),
                ("D", "a football shirt"), ("E", "a cake"), ("F", "gloves"),
                ("G", "a photograph"), ("H", "a plant")],
    "answers": {"6": "E", "7": "A", "8": "D", "9": "F", "10": "B"},
    "lines": [
        (WOMAN2, "Did you get nice presents, Yusuf?"),
        (MAN, "Very nice. My mother made a cake. She makes one every year "
              "and it is always chocolate."),
        (WOMAN2, "Did your father give you money?"),
        (MAN, "He usually does, but this year he gave me a watch. It was his "
              "father's watch, so it is quite old."),
        (WOMAN2, "And your sister?"),
        (MAN, "A football shirt, the right team and the right size. I was "
              "surprised, because she hates football."),
        (WOMAN2, "What about your grandmother?"),
        (MAN, "She knitted me a pair of gloves. It is April, so I will wear "
              "them in November."),
        (WOMAN2, "Did your friends give you anything?"),
        (MAN, "Tim gave me a book about mountains. He knows I want to climb "
              "one."),
    ],
}

PART3 = {
    "intro": "Listen to a woman asking about a bicycle in a shop. For "
             "questions 11 to 15, tick A, B or C.",
    "questions": [
        {"q": 11, "stem": "The woman wants a bicycle for",
         "options": ["her daughter.", "her son.", "herself."], "answer": "A"},
        {"q": 12, "stem": "The blue bicycle costs",
         "options": ["£90.", "£120.", "£150."], "answer": "B"},
        {"q": 13, "stem": "She decides to buy",
         "options": ["the blue one.", "the red one.",
                     "nothing today."], "answer": "B"},
        {"q": 14, "stem": "The bicycle will be ready on",
         "options": ["Tuesday.", "Thursday.", "Saturday."], "answer": "B"},
        {"q": 15, "stem": "The shop will also give her",
         "options": ["a light.", "a bag.", "a lock."], "answer": "C"},
    ],
    "lines": [
        (WOMAN, "I'm looking for a bicycle for my daughter. She's eleven."),
        (MAN2, "Is it her first one?"),
        (WOMAN, "She had a small one, but she's grown. My son has his "
                "already."),
        (MAN2, "This blue one is a good size. A hundred and twenty pounds."),
        (WOMAN, "And the red one next to it?"),
        (MAN2, "That's a hundred and fifty, but the brakes are better and "
               "it's lighter. The ninety-pound one is too small for her."),
        (WOMAN, "She will have it for years. I'll take the red one."),
        (MAN2, "We have to build it. It will be ready on Thursday."),
        (WOMAN, "Not before? Her birthday is Saturday."),
        (MAN2, "Thursday is fine, then. And we give you a lock with every "
               "bicycle. Lights and bags you buy separately."),
    ],
}

PART4 = {
    "intro": "You will hear a man leaving a message about a job interview. "
             "Listen and complete questions 16 to 20.",
    "title": "INTERVIEW",
    "gaps": [
        {"q": 16, "label": "Day", "answer": "Monday"},
        {"q": 17, "label": "Time", "answer": "11.20"},
        {"q": 18, "label": "Building: the ………… office", "answer": "north"},
        {"q": 19, "label": "Bring your", "answer": "passport"},
        {"q": 20, "label": "Ask for Mrs", "answer": "Underwood"},
    ],
    "lines": [
        (MAN2, "Good afternoon, this is Robert from Central Foods."),
        (MAN2, "We would like to see you about the job. Can you come on "
               "Monday? We said Wednesday on the telephone, but Monday is "
               "better for us."),
        (MAN2, "The time is twenty past eleven. Please come ten minutes "
               "early."),
        (MAN2, "We have two buildings in the same street. Come to the north "
               "office, not the south one. The north office is the newer "
               "building."),
        (MAN2, "Bring your passport, please. We cannot let anybody in "
               "without it. You do not need to bring your certificates."),
        (MAN2, "Ask for Mrs Underwood at the desk. That's U - N - D - E - R "
               "- W - O - O - D. Thank you, and see you on Monday."),
    ],
}


# ----------------------------------------------------- READING AND WRITING

R_PART1 = {
    "intro": "Which notice (A-H) says this (1-5)? For questions 1 to 5, mark "
             "the correct letter A-H on the answer sheet.",
    "notices": [
        ("A", "PLEASE DO NOT SIT ON THESE STAIRS"),
        ("B", "TRAINS TO THE AIRPORT EVERY 20 MINUTES"),
        ("C", "THIS WATER IS NOT FOR DRINKING"),
        ("D", "PLEASE BOOK A TABLE AT THE WEEKEND"),
        ("E", "HALF PRICE AFTER 5 P.M."),
        ("F", "PLEASE RETURN YOUR KEY WHEN YOU LEAVE"),
        ("G", "THE MUSEUM IS FREE ON THE FIRST SUNDAY OF THE MONTH"),
        ("H", "PLEASE WAIT HERE UNTIL YOUR NAME IS CALLED"),
    ],
    "items": [
        (1, "You must tell them you are coming on Saturday or Sunday.", "D"),
        (2, "You must give this back before you go.", "F"),
        (3, "You must not drink this.", "C"),
        (4, "It costs less if you come in the evening.", "E"),
        (5, "You must stay here until somebody says your name.", "H"),
    ],
}

R_PART2 = {
    "intro": "Read the sentences about a journey by train and choose the "
             "correct answer for each gap.",
    "items": [
        (6, "Nodir ……………… the train to Bukhara at eight o'clock.",
         ["caught", "held", "reached"], "A"),
        (7, "He found a seat by the ……………… and watched the fields.",
         ["door", "window", "wall"], "B"),
        (8, "A man came past and ……………… him a cup of tea.",
         ["asked", "offered", "gave up"], "B"),
        (9, "The journey ……………… four hours.",
         ["took", "spent", "made"], "A"),
        (10, "His cousin was ……………… for him at the station.",
         ["standing", "waiting", "staying"], "B"),
    ],
}

R_PART3 = {
    "intro": "Read the article about Karim and answer the questions. For "
             "each question, mark A, B or C on the answer sheet.",
    "title": "THE TAXI DRIVER WHO PAINTS",
    "text": [
        "Karim Tashev has driven a taxi in Tashkent for eleven years. He "
        "works at night, from eight in the evening until four in the "
        "morning, and he sleeps in the afternoon.",
        "He also paints. There are more than two hundred of his pictures in "
        "his flat, and almost all of them show the city at night: empty "
        "streets, wet roads, the lights of other cars. He paints what he "
        "sees from the taxi.",
        "Karim went to an art school for one year when he was eighteen. "
        "Then his father died and he needed money, so he stopped. He did "
        "not paint anything for nine years, and he says he thought about it "
        "every single day.",
        "A customer saw the pictures last spring and photographed one for "
        "a small gallery. Somebody bought it immediately, for more than "
        "Karim earns in a month. He is still driving at night, because one "
        "picture is not a job. But he has stopped saying that he used to "
        "paint, and now says that he is a painter.",
    ],
    "questions": [
        {"q": 11, "stem": "Karim works",
         "options": ["in the morning.", "in the afternoon.",
                     "at night."], "answer": "C"},
        {"q": 12, "stem": "Most of his pictures show",
         "options": ["the city at night.", "people in his taxi.",
                     "the countryside."], "answer": "A"},
        {"q": 13, "stem": "Karim left art school because",
         "options": ["he was not good enough.", "his family needed money.",
                     "he moved to another city."], "answer": "B"},
        {"q": 14, "stem": "For nine years Karim",
         "options": ["painted every day.", "did not paint.",
                     "sold his pictures."], "answer": "B"},
        {"q": 15, "stem": "Karim still drives a taxi because",
         "options": ["he enjoys it more than painting.",
                     "one picture is not enough money.",
                     "the gallery is closed."], "answer": "B"},
    ],
}

R_PART4 = {
    "intro": "Read the article about the desert and answer the questions. "
             "For each question, mark A, B or C on the answer sheet.",
    "title": "LIFE IN THE DESERT",
    "text": ("A desert is a place 16 …………… almost no rain falls. It is not "
             "always hot: some deserts are extremely cold 17 …………… night, "
             "and a few of them are covered in snow. Plants and animals in "
             "the desert are very good 18 …………… saving water. The cactus "
             "keeps water inside it, and some small animals never drink at "
             "all, because they take water from their food. People have "
             "lived in deserts 19 …………… thousands of years, and they "
             "20 …………… how to find water under the sand."),
    "items": [
        (16, ["which", "where", "when"], "B"),
        (17, ["at", "in", "on"], "A"),
        (18, ["at", "in", "for"], "A"),
        (19, ["since", "for", "during"], "B"),
        (20, ["know", "knows", "knowing"], "A"),
    ],
}

R_PART5 = {
    "intro": "Read the text. Think of the word which fits each gap. Write ONE "
             "word for each gap.",
    "letters": [
        ("Dear Mrs Price,",
         "I am writing (Example: about) the flat I rent from you. The "
         "washing machine stopped working 21 …………… Monday and there is water "
         "22 …………… the kitchen floor. I telephoned the office twice, "
         "23 …………… nobody answered. Could somebody come this week?",
         "Yours sincerely,\nFarrukh Qodirov"),
        ("Dear Mr Qodirov,",
         "I am sorry 24 …………… hear about the washing machine. A man will "
         "come on Thursday morning between nine and twelve. Please telephone "
         "me if you 25 …………… not be at home.",
         "Yours sincerely,\nJane Price"),
    ],
    "answers": {21: "on", 22: "on", 23: "but", 24: "to", 25: "will / can"},
}

WRITING = {
    "task": "Write an email to an English friend. You are going to start a "
            "new job next month. Include:",
    "points": ["what the job is",
               "where you will work",
               "how you feel about it",
               "ask your friend to visit you there"],
    "words": "Write at least 50 words.",
}
