"""B1+ mock final, paper 6 - Reading and Writing, for the Intermediate classes.

Same skeleton and same density as Azamat's own B1+ final.
Checked by exams/check_paper.py.
"""

R_PART1 = {
    "intro": "Look at the text in each question. What does it say? For each "
             "question, choose the correct answer A, B, C or D.",
    "questions": [
        {"q": 1,
         "text": "Shahnoza - I've put the parcel in the office next door "
                 "because nobody answered. They close at six. If you can't "
                 "get there today they'll keep it until Saturday but not "
                 "after that. Delivery driver",
         "ask": "What happens if Shahnoza does not collect the parcel today?",
         "options": ["It will be returned to the sender immediately.",
                     "It will be delivered again tomorrow.",
                     "It can still be collected until Saturday.",
                     "She will have to pay a fee."],
         "answer": "C"},
        {"q": 2,
         "text": "THE CAR PARK IS FOR CUSTOMERS OF THE SHOPPING CENTRE ONLY "
                 "AND IS FREE FOR THE FIRST THREE HOURS. VEHICLES LEFT "
                 "OVERNIGHT WILL BE REMOVED AT THE OWNER'S EXPENSE.",
         "ask": "What does the notice warn drivers about?",
         "options": ["Parking costs money from the first hour.",
                     "Cars left all night will be taken away and the owner "
                     "will pay.",
                     "The car park closes after three hours.",
                     "Only shoppers may park overnight."],
         "answer": "B"},
        {"q": 3,
         "text": "From: the editor. Thanks for the article - it's good, but "
                 "it's 1,400 words and I have room for 900. Rather than cut "
                 "it myself I'd like you to do it, since you'll know which "
                 "parts matter. Can you send it back by Thursday?",
         "ask": "What is the editor asking the writer to do?",
         "options": ["Write a longer version of the article.",
                     "Shorten the article herself.",
                     "Explain which parts are most important.",
                     "Agree to a later deadline."],
         "answer": "B"},
        {"q": 4,
         "text": "Notice to residents: the water will be turned off between "
                 "9 a.m. and 1 p.m. on Tuesday. Please fill containers the "
                 "night before. We cannot say exactly when the supply will "
                 "return, so do not rely on it before one o'clock.",
         "ask": "What are residents advised to do?",
         "options": ["Stay at home on Tuesday morning.",
                     "Store water in advance.",
                     "Report any problems before nine.",
                     "Use the supply before nine o'clock only."],
         "answer": "B"},
        {"q": 5,
         "text": "I went last weekend and would say go early. By eleven the "
                 "queue for the main hall was forty minutes and the smaller "
                 "rooms, which are honestly the better part, were too "
                 "crowded to see anything properly.",
         "ask": "What is the writer's main advice?",
         "options": ["Avoid the smaller rooms.",
                     "Book a ticket in advance.",
                     "Arrive before the crowds.",
                     "Visit during the week instead."],
         "answer": "C"},
    ],
}

R_PART2 = {
    "intro": "Look at the sentences below about a night watchman at a "
             "museum. Read the text to decide if each sentence is correct or "
             "incorrect. If it is correct, choose YES. If it is not correct, "
             "choose NO.",
    "title": "Eleven years of nights among the dinosaurs",
    "text": [
        "Anvar Sobirov has worked nights at the natural history museum for "
        "eleven years, which is considerably longer than anybody expected, "
        "including him. He applied for the position during a difficult "
        "period after his shop closed and assumed he would stay for a "
        "winter. The building, he explains, turned out to be unexpectedly "
        "good company.",
        "The job itself is mostly walking. He covers the entire museum four "
        "times between ten in the evening and six in the morning, checking "
        "doors and windows and the temperature in the rooms where the "
        "collections are particularly delicate. Almost nothing ever happens. "
        "In eleven years he has called the police exactly twice, and on both "
        "occasions the intruder was a bird.",
        "What he was not prepared for was the reading. The museum library is "
        "open to staff, and after his second winter he began taking a book "
        "with him on his rounds and stopping for twenty minutes in the "
        "gallery of fossils. He now knows a genuinely alarming amount about "
        "extinct animals, and the education department occasionally borrows "
        "him for school visits, which he describes as the strangest "
        "promotion anybody has ever received.",
        "He is sixty-three and has been asked repeatedly when he intends to "
        "retire. His answer has become a standing joke among the daytime "
        "staff, who report it to visitors with some pride. He says he will "
        "stop when somebody explains to him where else a man of his age can "
        "be paid to walk eight kilometres a night in comfortable shoes among "
        "the most interesting objects in the city. Privately he admits that "
        "the question worries him more than he lets on, because his knees "
        "have begun to complain on the stairs, and because he has no clear "
        "idea what a man does with an ordinary night after eleven years of "
        "extraordinary ones.",
    ],
    "statements": [
        {"q": 6, "text": "Anvar expected the job to be temporary.",
         "answer": "YES"},
        {"q": 7, "text": "He has often had to call the police.",
         "answer": "NO"},
        {"q": 8, "text": "He started reading about the collections in his "
                         "first few weeks.",
         "answer": "NO"},
        {"q": 9, "text": "He sometimes helps with visits from schools.",
         "answer": "YES"},
        {"q": 10, "text": "He has decided on a date to stop working.",
         "answer": "NO"},
    ],
}

R_PART3 = {
    "intro": "Read the text and questions below. For each question, choose "
             "the correct answer A, B, C or D.",
    "title": "The factory that let its workers set the hours",
    "text": [
        "Three years ago a furniture factory employing ninety people did "
        "something that its owner now describes as either brave or careless, "
        "depending on the day. It abolished fixed shifts. Workers would "
        "decide among themselves who came in when, provided the orders went "
        "out on time and somebody qualified was present whenever the "
        "machinery was running.",
        "The owner is clear that this was not generosity. The factory was "
        "losing people to a larger competitor twenty minutes away that paid "
        "slightly more, and he could not match the wages. What he could "
        "offer was something the competitor could not, because a company of "
        "four thousand employees cannot let its staff arrange their own "
        "week. He expected chaos for six months and got about nine weeks of "
        "it.",
        "The arrangement did not survive unchanged. Two rules had to be "
        "added within the first year, both suggested by the workers rather "
        "than imposed on them. Nobody may change the following week's "
        "arrangement after Thursday, because the people who organise the "
        "deliveries were being driven to despair. And every worker must "
        "cover at least one unpopular early shift a month, since a small "
        "number of people had quietly been taking all the comfortable hours.",
        "Whether it has worked depends on what is being measured. "
        "Productivity is almost exactly what it was, which disappointed the "
        "owner. Nobody has left for the competitor in two years, which did "
        "not. The one change nobody predicted is that the factory now "
        "employs eleven people who could not have taken an ordinary job "
        "there at all, most of them parents of young children, and the owner "
        "regards this as the only part of the experiment he would defend in "
        "public without any figures whatsoever. Two of them have since been "
        "promoted, and one now organises the weekly arrangement for the "
        "entire workshop, which the owner points out is an outcome no "
        "consultant would have predicted.",
    ],
    "questions": [
        {"q": 11, "ask": "Why did the owner change the shift system?",
         "options": ["To reward the workers for their loyalty.",
                     "To compete with a firm he could not match on pay.",
                     "Because the workers threatened to leave together.",
                     "Because the factory was too large to manage."],
         "answer": "B"},
        {"q": 12, "ask": "What does the writer say about the first months?",
         "options": ["They were calmer than the owner had feared.",
                     "They were worse than expected.",
                     "The system nearly collapsed.",
                     "Nothing changed at all."],
         "answer": "A"},
        {"q": 13, "ask": "Where did the two new rules come from?",
         "options": ["The delivery company.",
                     "The workers themselves.",
                     "The owner's advisers.",
                     "A government inspector."],
         "answer": "B"},
        {"q": 14, "ask": "Why was the second rule necessary?",
         "options": ["Some workers were avoiding the difficult hours.",
                     "The early shifts were dangerous.",
                     "The machinery needed more staff in the morning.",
                     "Deliveries arrived before anybody was there."],
         "answer": "A"},
        {"q": 15, "ask": "What does the owner value most about the change?",
         "options": ["The rise in productivity.",
                     "The saving in wages.",
                     "That it allowed him to employ people who could not "
                     "otherwise work there.",
                     "That the competitor has copied it."],
         "answer": "C"},
    ],
}

R_PART4 = {
    "intro": "Read the text below and choose the correct answer for each gap.",
    "title": "River swimming to be allowed again after sixty years",
    "text": "Swimming in the river through the city centre will be permitted "
            "again from June, sixty years after it was (16) ......... on "
            "health grounds. The decision (17) ......... after four years of "
            "testing showed that the water now meets the required standard "
            "on all but a handful of days each summer. Campaigners, who have "
            "been (18) ......... for the change since 2019, described the "
            "announcement as a turning point. The council warned that "
            "swimming would be (19) ......... again temporarily after heavy "
            "rain, and asked the public to (20) ......... notice of the "
            "flags at the entrance to the water.",
    "gaps": [
        {"q": 16, "options": ["banned", "refused", "denied", "closed"],
         "answer": "A"},
        {"q": 17, "options": ["arrived", "came", "reached", "got"],
         "answer": "B"},
        {"q": 18, "options": ["asking", "calling", "demanding", "requiring"],
         "answer": "B"},
        {"q": 19, "options": ["stopped", "suspended", "cut", "ended"],
         "answer": "B"},
        {"q": 20, "options": ["take", "make", "pay", "give"], "answer": "A"},
    ],
}

R_PART5 = {
    "intro": "Read the text. Think of the word which best fits each gap. "
             "Write ONE word for each gap.",
    "title": "From: Zarina   To: Pat",
    "text": "Hi Pat,\n\nI hope the summer has been kinder to you than it "
            "(21) ......... to us - it has rained almost every day since "
            "June and the garden has given up.\n\nThe course finished last "
            "week and I passed, (22) ......... was more of a surprise to me "
            "than to anybody else. I still do not know (23) ......... I want "
            "to do with it, but there is no hurry. My father keeps asking, "
            "(24) ......... I have learned to change the subject.\n\nAre you "
            "free at the end of September? I would rather come then "
            "(25) ......... wait until the winter.\n\nZarina",
    "gaps": [
        {"q": 21, "answer": "has"},
        {"q": 22, "answer": "which"},
        {"q": 23, "answer": "what"},
        {"q": 24, "answer": "but"},
        {"q": 25, "answer": "than"},
    ],
}

WRITING1 = {
    "task": "You have found a wallet belonging to your English friend Chris "
            "and you want to return it. Write an email to Chris. In your "
            "email:",
    "points": ["tell Chris you have found the wallet",
               "say where you found it",
               "suggest how to give it back."],
    "words": "Write 35-45 words.",
}

WRITING2 = {
    "task": "This is part of an email you receive from an English friend. "
             "Now write an email, giving your friend some advice.",
    "quote": "I've started a course online but I keep putting off the work "
             "and I'm now three weeks behind. Nobody is checking on me, "
             "which I thought I would enjoy. How do you make yourself study "
             "when nobody is waiting?",
    "words": "Write about 100 words.",
}
