"""B1+ mock final, paper 2 - Reading and Writing, for the Intermediate classes.

The same skeleton as Azamat's own B1+ final: five reading parts for
twenty-five marks, then the short email and the longer one.

His real paper is denser than it looks - the Part 4 article runs 368 words at
21.6 words a sentence with 13.9% of words eight letters or longer. These
papers are written to those numbers and checked by exams/check_paper.py.

There is no listening here: he asked for Reading and Writing.
"""

R_PART1 = {
    "intro": "Look at the text in each question. What does it say? For each "
             "question, choose the correct answer A, B, C or D.",
    "questions": [
        {"q": 1,
         "text": "Nodira - the delivery came but two of the boxes are "
                 "damaged. I've signed for them anyway, otherwise they take "
                 "the whole lot back. Photograph them before you open "
                 "anything. Timur",
         "ask": "Why does Timur want Nodira to take photographs?",
         "options": ["To show the driver what arrived.",
                     "To keep evidence of the damage before the boxes are opened.",
                     "To prove that he signed for the delivery.",
                     "To decide which boxes to return."],
         "answer": "B"},
        {"q": 2,
         "text": "MEMBERS MAY BRING ONE GUEST AT WEEKENDS ONLY. GUESTS MUST "
                 "BE SIGNED IN AT RECEPTION AND CANNOT USE THE POOL AFTER "
                 "6 P.M.",
         "ask": "What are members told about guests?",
         "options": ["Guests are not allowed at weekends.",
                     "Guests must pay at reception.",
                     "A guest's use of the pool is limited to certain hours.",
                     "Members may bring several guests on Saturdays."],
         "answer": "C"},
        {"q": 3,
         "text": "Ali - I've moved your appointment to Thursday because the "
                 "specialist is away. If Thursday is impossible, ring the "
                 "surgery today; after today the slot goes to somebody else. "
                 "Reception",
         "ask": "What should Ali do if he cannot come on Thursday?",
         "options": ["Wait for the surgery to telephone him.",
                     "Come on the original day instead.",
                     "Telephone the surgery before the end of the day.",
                     "Ask the specialist to see him later."],
         "answer": "C"},
        {"q": 4,
         "text": "The evening class in photography is now full. Students who "
                 "have already paid will keep their place. Anybody else who "
                 "is interested should add their name to the list for "
                 "January rather than turning up on Tuesday.",
         "ask": "What is the notice telling people?",
         "options": ["The class has been cancelled.",
                     "People who have not paid should not come on Tuesday.",
                     "Students must pay again in January.",
                     "The class will be larger from January."],
         "answer": "B"},
        {"q": 5,
         "text": "From: Malika. Subject: Friday. I can do the presentation "
                 "but I'd rather not do it first - my figures depend on what "
                 "the finance team say in their part. Could you put me after "
                 "them? Otherwise I'll have to guess.",
         "ask": "What is Malika asking for?",
         "options": ["Permission to miss the meeting.",
                     "Help with preparing her figures.",
                     "A change to the order of the presentations.",
                     "More time to finish her work."],
         "answer": "C"},
    ],
}

R_PART2 = {
    "intro": "Look at the sentences below about a night bakery. Read the "
             "text to decide if each sentence is correct or incorrect. If it "
             "is correct, choose YES. If it is not correct, choose NO.",
    "title": "The bakery that opens when everything else closes",
    "text": [
        "The first thing I noticed was the queue, which is unusual at half "
        "past eleven on a Tuesday night. About twenty people were waiting "
        "outside a doorway that during the day belongs to a shoe shop. The "
        "bakery underneath it only exists between eleven and four in the "
        "morning, and by the time the shoe shop opens there is no evidence "
        "that it was ever there.",
        "Kamila Rashidova started it almost by accident. She had been "
        "working in a hotel kitchen for eleven years and was tired of the "
        "hours, which is a strange complaint from somebody who now finishes "
        "work at four in the morning. The difference, she explained, is that "
        "these are her hours. She rents the basement from the shoe shop "
        "owner, who had been using it for storage and was delighted to be "
        "paid for an empty room.",
        "I expected the customers to be people coming home from restaurants. "
        "Some are, but the majority turn out to be the people who keep the "
        "city running while it sleeps: taxi drivers, nurses finishing a "
        "shift, two security guards who arrive together every night and "
        "argue about football. Kamila knows most of them by name and several "
        "by order, which means she has already started wrapping the bread "
        "before they reach the counter.",
        "The economics are less romantic than the atmosphere. She sells "
        "between four and five hundred items a night, and the difficulty is "
        "not selling them but predicting how many to make. Anything left at "
        "four o'clock goes to a shelter near the station, which sounds "
        "generous until you understand that the alternative is throwing it "
        "away. She has been asked twice to open a second branch and has "
        "refused both times, because the whole arrangement depends on her "
        "being there. When I asked what would happen if she were ill, she "
        "laughed and said the sign on the door would simply say closed, "
        "and that nobody would come looking for an explanation.",
    ],
    "statements": [
        {"q": 6, "text": "The bakery uses a space that has another purpose "
                         "during the day.",
         "answer": "YES"},
        {"q": 7, "text": "Kamila left her hotel job because she wanted to "
                         "work fewer hours.",
         "answer": "NO"},
        {"q": 8, "text": "The owner of the shoe shop was reluctant to rent "
                         "her the basement.",
         "answer": "NO"},
        {"q": 9, "text": "Most of the customers are people who work at night.",
         "answer": "YES"},
        {"q": 10, "text": "Kamila has turned down the chance to open "
                          "elsewhere.",
         "answer": "YES"},
    ],
}

R_PART3 = {
    "intro": "Read the text and questions below. For each question, choose "
             "the correct answer A, B, C or D.",
    "title": "The town that turned off its street lights",
    "text": [
        "When the council in a small town in the north said it would switch "
        "off two thirds of the street lights between midnight and five in "
        "the morning, almost nobody was in favour. A petition against the "
        "plan collected four thousand names in a fortnight, which is a lot "
        "in a town of eleven thousand people. The council said, without much "
        "success, that the money saved was the same as the wages of two "
        "teachers.",
        "The arguments against were mostly about safety, and they came in "
        "two kinds. The first was about crime, and it turned out to be "
        "wrong: police figures for the next eighteen months showed no real "
        "rise in burglary or attacks, which is what has happened in every "
        "other town that has tried this. The second was about traffic, and "
        "it was more serious. Two junctions really were unsafe in the dark, "
        "and the lights there were switched back on within a month.",
        "What nobody had expected was the stargazing. A teacher at the "
        "secondary school, who had spent years describing stars his students "
        "could not actually see, began running evenings in the park with a "
        "telescope. Sixty people came, on average, through that first "
        "winter, among them parents who said they had never seen the Milky "
        "Way in their lives. The club they started now owns two telescopes "
        "and has a waiting list of forty.",
        "Four years later the arrangement is still in place, though not "
        "because everybody likes it. A survey last year found the town "
        "almost exactly divided, with older people much more likely to "
        "object. The council's own view is a practical one rather than a "
        "green one: the saving is real, the disasters people predicted did "
        "not happen, and turning the lights back on would cost money they "
        "have already spent on something else.",
    ],
    "questions": [
        {"q": 11, "ask": "What does the writer suggest about the petition?",
         "options": ["It was organised by the council's opponents.",
                     "The number of signatures was unusually high for the "
                     "size of the town.",
                     "It persuaded the council to change its mind.",
                     "Most of the signatures came from outside the town."],
         "answer": "B"},
        {"q": 12, "ask": "What happened to the fear about crime?",
         "options": ["It proved to be justified.",
                     "It was never properly investigated.",
                     "The figures did not support it.",
                     "It applied only to certain streets."],
         "answer": "C"},
        {"q": 13, "ask": "Why were some lights switched back on?",
         "options": ["Because of pressure from the petition.",
                     "Because two junctions were genuinely unsafe.",
                     "Because the saving was smaller than expected.",
                     "Because the police requested it."],
         "answer": "B"},
        {"q": 14, "ask": "What does the writer find surprising about the "
                         "astronomy society?",
         "options": ["That a teacher started it.",
                     "That it owns expensive equipment.",
                     "That nobody had expected this result.",
                     "That it meets in the park."],
         "answer": "C"},
        {"q": 15, "ask": "What is the council's present attitude?",
         "options": ["They regret the decision.",
                     "They are proud of the environmental benefit.",
                     "They keep it because undoing it would be expensive.",
                     "They intend to switch off more lights."],
         "answer": "C"},
    ],
}

R_PART4 = {
    "intro": "Read the text below and choose the correct answer for each gap.",
    "title": "Museum returns painting after forty years",
    "text": "A painting that has hung in a regional museum since 1984 is to "
            "be (16) ......... to the family it was taken from during the "
            "war. The museum said it had acted as soon as the evidence "
            "(17) ......... clear, although researchers first raised "
            "questions about the painting's history more than a decade ago. "
            "The family, who now live in three different countries, have "
            "(18) ......... not to sell it and are discussing where it might "
            "be displayed. The director admitted that the case had "
            "(19) ......... the museum to examine the origins of several "
            "other works, and that this process was likely to "
            "(20) ......... several years.",
    "gaps": [
        {"q": 16, "options": ["given back", "put back", "taken back",
                              "brought back"], "answer": "A"},
        {"q": 17, "options": ["turned", "became", "went", "grew"],
         "answer": "B"},
        {"q": 18, "options": ["decided", "insisted", "refused", "agreed"],
         "answer": "D"},
        {"q": 19, "options": ["made", "led", "caused", "forced"],
         "answer": "B"},
        {"q": 20, "options": ["last", "take", "spend", "hold"],
         "answer": "B"},
    ],
}

R_PART5 = {
    "intro": "Read the text. Think of the word which best fits each gap. "
             "Write ONE word for each gap.",
    "title": "From: Dilshod   To: Sam",
    "text": "Hi Sam,\n\nThanks for the photographs - the house looks much "
            "better than it (21) ......... in the ones you sent in March. I "
            "can't believe you did the kitchen yourselves. How long "
            "(22) ......... it take in the end?\n\nWork is busy. I've been "
            "asked to run the training programme from September, "
            "(23) ......... means I'll be travelling to the other offices "
            "once a month. I said yes before I had properly thought about "
            "it, which is (24) ......... I usually do.\n\nIf the spare room "
            "is finished by October, I'd love to come. Let me know "
            "(25) ......... suits you.\n\nDilshod",
    "gaps": [
        {"q": 21, "answer": "did"},
        {"q": 22, "answer": "did"},
        {"q": 23, "answer": "which"},
        {"q": 24, "answer": "what"},
        {"q": 25, "answer": "what / whatever / whichever"},
    ],
}

WRITING1 = {
    "task": "You borrowed a book from your English friend Alex and you have "
            "damaged it. Write an email to Alex. In your email:",
    "points": ["explain what happened to the book",
               "apologise",
               "say what you are going to do about it."],
    "words": "Write 35-45 words.",
}

WRITING2 = {
    "task": "This is part of an email you receive from an English friend. "
            "Now write an email, giving your friend some advice.",
    "quote": "My parents want me to study in the capital because they say "
             "the universities are better, but all my friends are staying "
             "here and the course here is good too. I keep changing my mind. "
             "What would you do?",
    "words": "Write about 100 words.",
}
