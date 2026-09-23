"""B1+ mock final, paper 4 - Reading and Writing, for the Intermediate classes.

Same skeleton and same density as Azamat's own B1+ final.
Checked by exams/check_paper.py.
"""

R_PART1 = {
    "intro": "Look at the text in each question. What does it say? For each "
             "question, choose the correct answer A, B, C or D.",
    "questions": [
        {"q": 1,
         "text": "Madina - the plumber came but couldn't get into the "
                 "bathroom because the cupboard is in front of the pipes. "
                 "He'll come back Thursday. Can you move it before then? I'm "
                 "away until Wednesday night. Jahongir",
         "ask": "What does Jahongir want Madina to do?",
         "options": ["Let the plumber in on Thursday.",
                     "Clear the way to the pipes before Thursday.",
                     "Telephone the plumber to rearrange.",
                     "Wait until he comes home on Wednesday."],
         "answer": "B"},
        {"q": 2,
         "text": "BAGS LARGER THAN 40 x 30 CM MUST BE LEFT IN THE LOCKERS. "
                 "LOCKERS ARE FREE BUT REQUIRE A COIN, WHICH IS RETURNED "
                 "WHEN THE LOCKER IS OPENED.",
         "ask": "What does the notice tell visitors?",
         "options": ["All bags must be left in a locker.",
                     "The lockers cost money to use.",
                     "They will get their coin back afterwards.",
                     "Lockers must be booked in advance."],
         "answer": "C"},
        {"q": 3,
         "text": "From: the course tutor. Your essay was handed in two days "
                 "late without an explanation, so under the rules I have to "
                 "reduce the mark. Please read the note on late work before "
                 "the next assignment; the deadline for that one cannot be "
                 "moved.",
         "ask": "What is the tutor telling the student?",
         "options": ["The essay will not be marked at all.",
                     "The mark has been lowered because the work was late.",
                     "The next deadline has been extended.",
                     "The student must rewrite the essay."],
         "answer": "B"},
        {"q": 4,
         "text": "Team - the software update happens tonight. Save anything "
                 "you are working on before you leave. Files left open will "
                 "not be recovered, and the help desk cannot do anything "
                 "about it in the morning.",
         "ask": "Why should staff save their work?",
         "options": ["The help desk closes early tonight.",
                     "Unsaved work will be lost permanently.",
                     "The update will delete all old files.",
                     "They will not be able to log in tomorrow."],
         "answer": "B"},
        {"q": 5,
         "text": "SEATS IN THE FRONT TWO ROWS ARE RESERVED FOR MEMBERS UNTIL "
                 "TEN MINUTES BEFORE THE START. AFTER THAT THEY ARE "
                 "AVAILABLE TO ANYONE.",
         "ask": "What is true about the front two rows?",
         "options": ["Only members may ever sit there.",
                     "They are kept for members until shortly before the "
                     "start.",
                     "Members must book them ten minutes beforehand.",
                     "They cost more than the other seats."],
         "answer": "B"},
    ],
}

R_PART2 = {
    "intro": "Look at the sentences below about a seed library. Read the "
             "text to decide if each sentence is correct or incorrect. If it "
             "is correct, choose YES. If it is not correct, choose NO.",
    "title": "The library where you borrow seeds",
    "text": [
        "In a wooden drawer at the back of a public library, between the "
        "large-print novels and the photocopier, there are about six hundred "
        "small paper envelopes. Each one holds seeds, and each one is free. "
        "You take what you need, you grow it during the summer, and in the "
        "autumn, if everything has gone to plan, you bring back rather more "
        "seed than you first borrowed.",
        "The drawer was started four years ago by a retired biology teacher "
        "who had grown tired of what the shops had to offer. Big companies, "
        "she explains, go for plants that travel well and look the same as "
        "each other, which makes sense for a supermarket and is dull for a "
        "gardener. Most of the kinds in the drawer are local ones, and "
        "several were given to her by people whose families had been saving "
        "them for years.",
        "The obvious problem is that not everybody brings anything back. "
        "About a third of borrowers do, which sounds like failure until you "
        "think about how seeds work: one good plant can make hundreds of "
        "them. The collection has grown every single year in spite of that "
        "poor-looking figure, and the volunteers have stopped worrying.",
        "What the founder did not expect was the teaching. Beginners turn up "
        "with no idea what to do, so the volunteers now run sessions on "
        "Saturday mornings, and these are busier than the drawer itself. She "
        "says the seeds are really an excuse. The thing that matters is that "
        "forty people who had never spoken to each other now argue "
        "cheerfully about tomatoes every weekend, and that several of them "
        "have become friends. The library, which had been quietly worried "
        "about its visitor numbers for years, now counts the seed drawer as "
        "one of the best decisions it has ever made, and has given the "
        "volunteers a second drawer for the overflow.",
    ],
    "statements": [
        {"q": 6, "text": "Borrowers are expected to return more seed than "
                         "they took.",
         "answer": "YES"},
        {"q": 7, "text": "The founder was unhappy with the choice of "
                         "varieties in shops.",
         "answer": "YES"},
        {"q": 8, "text": "Most of the borrowers bring seed back.",
         "answer": "NO"},
        {"q": 9, "text": "The volunteers are worried about the number of "
                         "seeds returned.",
         "answer": "NO"},
        {"q": 10, "text": "The Saturday sessions attract more people than "
                          "the seed drawer.",
         "answer": "YES"},
    ],
}

R_PART3 = {
    "intro": "Read the text and questions below. For each question, choose "
             "the correct answer A, B, C or D.",
    "title": "The hospital that put a musician on the ward",
    "text": [
        "The idea sounded, in the words of one doctor who was against it, "
        "like something out of a magazine. A regional hospital would employ "
        "a professional musician two days a week. She would not give "
        "concerts in the entrance hall. She would work on the wards "
        "themselves, including the ones where patients are most seriously "
        "ill. The money came from a charity, so nobody could say it had been "
        "taken from nursing.",
        "The musician they chose was a cellist in her forties who had never "
        "worked in a hospital. She spent her first fortnight playing nothing "
        "at all. Instead she followed the staff around, and she now says "
        "that was the most important thing she did. Wards have a rhythm of "
        "their own, and a cello arriving in the middle of the morning "
        "medicine round is not a comfort. It is an obstacle.",
        "The results are hard to measure and the hospital has been careful "
        "about what it claims. There is fair evidence, gathered over two "
        "years, that patients on her wards ask for a little less pain relief "
        "afterwards. The evidence that they sleep better is stronger. What "
        "the staff mention first, though, is not the patients but the "
        "relatives, who often have nothing to do through a long afternoon. "
        "Listening to something gives them permission to stop talking.",
        "Four other hospitals have since copied the scheme, with mixed "
        "results. Where it has worked, the musician has been treated as one "
        "of the team rather than a visitor. Where it has not, the cellist "
        "says the mistake has always been the same. Somebody decided in "
        "advance which music would be good for people, instead of asking "
        "them what they wanted to hear. The cellist is blunt about this, and "
        "says that a ward full of strangers has no more single taste in "
        "music than a street full of strangers does, which is obvious enough "
        "until somebody with a budget forgets it.",
    ],
    "questions": [
        {"q": 11, "ask": "Why does the writer mention the charity?",
         "options": ["To explain why the scheme was cheap.",
                     "To show that no nursing money was used.",
                     "To criticise the hospital's spending.",
                     "To explain who chose the musician."],
         "answer": "B"},
        {"q": 12, "ask": "What does the cellist say about her first two "
                         "weeks?",
         "options": ["They were wasted.",
                     "She learned the wards before she played.",
                     "She found the staff unwelcoming.",
                     "She gave several small concerts."],
         "answer": "B"},
        {"q": 13, "ask": "What does the writer say about the evidence?",
         "options": ["It proves the scheme reduces pain.",
                     "It is stronger for sleep than for pain relief.",
                     "It was collected over six months.",
                     "The hospital has exaggerated it."],
         "answer": "B"},
        {"q": 14, "ask": "What do the staff notice most?",
         "options": ["The effect on the relatives.",
                     "The effect on their own mood.",
                     "That patients ask for more music.",
                     "That the wards are quieter at night."],
         "answer": "A"},
        {"q": 15, "ask": "Why have some other hospitals failed?",
         "options": ["They employed the wrong musicians.",
                     "They spent too little money.",
                     "They chose the music for the patients.",
                     "They stopped the scheme too early."],
         "answer": "C"},
    ],
}

R_PART4 = {
    "intro": "Read the text below and choose the correct answer for each gap.",
    "title": "Bridge to reopen three months early",
    "text": "The footbridge across the river will reopen in March, three "
            "months (16) ......... of schedule, after engineers found that "
            "the damage was less serious than they had first "
            "(17) ......... . The bridge has been closed since August, "
            "forcing walkers to (18) ......... a detour of almost two "
            "kilometres. Shops on the far bank, several of which reported a "
            "sharp fall in customers, have (19) ......... the news. The "
            "council said the final cost would be published once the work "
            "had been (20) ......... out in full, and added that the "
            "contractor would not be paid a bonus for finishing early "
            "because no such clause existed in the agreement.",
    "gaps": [
        {"q": 16, "options": ["ahead", "front", "early", "forward"],
         "answer": "A"},
        {"q": 17, "options": ["feared", "frightened", "worried", "afraid"],
         "answer": "A"},
        {"q": 18, "options": ["do", "make", "take", "go"], "answer": "B"},
        {"q": 19, "options": ["greeted", "welcomed", "received", "accepted"],
         "answer": "B"},
        {"q": 20, "options": ["carried", "brought", "taken", "put"],
         "answer": "A"},
    ],
}

R_PART5 = {
    "intro": "Read the text. Think of the word which best fits each gap. "
             "Write ONE word for each gap.",
    "title": "From: Otabek   To: Jamie",
    "text": "Hi Jamie,\n\nIt was good to hear from you. I am glad the move "
            "went well - the photographs make the flat look much bigger "
            "(21) ......... I imagined from your description.\n\nI have "
            "(22) ......... studying for the exam in June, which is why I "
            "disappeared for a while. There is far more to learn "
            "(23) ......... I thought when I signed up, and I have had to "
            "give up football for the time being. My brother says I will "
            "regret it, (24) ......... he says that about most "
            "things.\n\nOnce it is over I would like to visit. Is July any "
            "good for you, (25) ......... would August be easier?\n\nOtabek",
    "gaps": [
        {"q": 21, "answer": "than"},
        {"q": 22, "answer": "been"},
        {"q": 23, "answer": "than"},
        {"q": 24, "answer": "but / though"},
        {"q": 25, "answer": "or"},
    ],
}

WRITING1 = {
    "task": "You are going to be away for two weeks and you want your "
            "English friend Sam to look after your cat. Write an email to "
            "Sam. In your email:",
    "points": ["ask Sam to look after the cat",
               "say when you will be away",
               "explain where the key is."],
    "words": "Write 35-45 words.",
}

WRITING2 = {
    "task": "This is part of an email you receive from an English friend. "
            "Now write an email, giving your friend some advice.",
    "quote": "My flatmate never cleans anything and I've started doing all "
             "of it myself just to avoid an argument. It's been six months "
             "and I'm getting angry about it. Should I say something, or is "
             "it not worth it?",
    "words": "Write about 100 words.",
}
