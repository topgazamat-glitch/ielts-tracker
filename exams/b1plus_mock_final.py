"""An original B1+ mock final, built to the shape of the real Empower paper.

Azamat has the real B1+ Mid-Course and End-of-Course Competency papers and
cannot hand them out - they are what the Intermediate students will sit. This
is a new paper on the same skeleton, so practising on it rehearses the exam
rather than the answers:

    LISTENING            20 marks   four parts, each heard twice
      Part 1  1-5        five short recordings, three options
      Part 2  6-10       complete the notes with a word or a number
      Part 3  11-15      one longer talk, three options
      Part 4  16-20      a conversation: is each sentence YES or NO?

    READING              25 marks   thirty minutes
      Part 1  1-5        five short texts, four options
      Part 2  6-10       one long review: is each sentence YES or NO?
      Part 3  11-15      read an article, four options
      Part 4  16-20      vocabulary in a text, four options
      Part 5  21-25      write ONE word in each gap

    WRITING              two tasks, thirty minutes
      Question 1         a short email, 35-45 words, three things to include
      Question 2         a reply giving advice, about 100 words

One deliberate difference from the real paper. Its Listening Part 1 asks
students to choose between three *pictures*, and I cannot draw the fifteen
photographs that would need. The part here tests the same thing - listening
for one detail in a short recording, five marks, three options - with the
options written out in words. Everything else follows the real paper part for
part, including the four-option reading questions and the two writing tasks,
which are what make this paper B1+ rather than B1.

The language is kept at B1+: phrasal verbs, the passive, perfect forms, mild
opinion and inference. Harder than Pre-Intermediate on purpose, and no harder
than the real thing.
"""

# --------------------------------------------------------------- LISTENING

# Each line is (voice, words). British voices, so the paper sounds like the
# exam; a narrator reads the instructions and the question numbers.
NARRATOR = "Daniel"
MAN, WOMAN, MAN2, WOMAN2 = "Rocko", "Shelley", "Reed", "Flo (English (UK))"

PART1 = [
    {
        "q": 1, "ask": "Why has Martin decided to give up the gym?",
        "options": ["It costs too much.", "It is too far away.",
                    "He has hurt his knee."],
        "answer": "B",
        "lines": [
            (WOMAN, "I hear you've left the gym, Martin. Was it the price? "
                    "They did put the fees up."),
            (MAN, "They did, but I could just about manage that. And my knee's "
                  "completely better now, before you ask."),
            (WOMAN, "So what was it?"),
            (MAN, "They moved to the new building by the river. It's forty "
                  "minutes each way now, and I was never going to keep that up."),
        ],
    },
    {
        "q": 2, "ask": "What does the woman say about the film?",
        "options": ["The acting was disappointing.",
                    "It was longer than she expected.",
                    "The ending did not make sense."],
        "answer": "A",
        "lines": [
            (MAN, "So, was the film worth three hours of your life?"),
            (WOMAN, "Well, I knew what I was getting - I'd read that it was "
                    "long, so that didn't bother me."),
            (MAN, "And the story? People said the ending was confusing."),
            (WOMAN, "No, I followed it perfectly well. What let it down was the "
                    "cast. I've seen every one of them do far better work."),
        ],
    },
    {
        "q": 3, "ask": "What has changed about the man's job?",
        "options": ["He has been given a different manager.",
                    "He now works from home twice a week.",
                    "He has moved to a bigger team."],
        "answer": "C",
        "lines": [
            (WOMAN, "How's the new arrangement working out?"),
            (MAN, "Fine. I'm still in the office every day - they offered me "
                  "two days at home and I turned it down, believe it or not."),
            (WOMAN, "And is Sasha still in charge?"),
            (MAN, "She is, thankfully. The real difference is that we've taken "
                  "on six more people, so there are fourteen of us now instead "
                  "of eight."),
        ],
    },
    {
        "q": 4, "ask": "What does the woman recommend the man does first?",
        "options": ["Book the flights.", "Apply for the visa.",
                    "Find somewhere to stay."],
        "answer": "B",
        "lines": [
            (MAN, "Right, I'm finally organising this trip. I thought I'd get "
                  "the flights while they're cheap."),
            (WOMAN, "I wouldn't, honestly. Do the paperwork first - it took me "
                    "six weeks last year, and if it doesn't come through, "
                    "you've lost the money."),
            (MAN, "Fair point. And the hotel?"),
            (WOMAN, "That can wait. There's always somewhere."),
        ],
    },
    {
        "q": 5, "ask": "How does the man feel about moving to the countryside?",
        "options": ["He is worried about being bored.",
                    "He is looking forward to the quiet.",
                    "He is unsure whether he can afford it."],
        "answer": "A",
        "lines": [
            (WOMAN, "You must be pleased. A garden at last, and no traffic "
                    "outside the window."),
            (MAN, "The money side's all worked out, and yes, the peace will be "
                  "wonderful for about a fortnight."),
            (WOMAN, "And after that?"),
            (MAN, "That's exactly what keeps me awake. I've lived in cities all "
                  "my life. What on earth am I going to do on a wet Tuesday "
                  "in February?"),
        ],
    },
]

PART2 = {
    "intro": "You will hear a woman telling students about a new community "
             "library. For each question, write the correct answer in the gap. "
             "Write one or two words or a number.",
    "title": "The New Community Library",
    "gaps": [
        {"q": 6, "label": "Name of the library", "answer": "Riverside"},
        {"q": 7, "label": "Opens on", "answer": "14th March"},
        {"q": 8, "label": "Number of floors", "answer": "three"},
        {"q": 9, "label": "Quickest way to join", "answer": "online"},
        {"q": 10, "label": "Free for members every", "answer": "Thursday"},
    ],
    "lines": [
        (WOMAN2,
         "Good morning, everyone. I've come in to tell you about something "
         "opening just down the road from the college. For years people have "
         "been asking the council for a proper library in this part of town, "
         "and at last we've got one. It's going to be called the Riverside "
         "library - that's Riverside, one word - because of where it's been "
         "built, although I should warn you that you can't actually see the "
         "river from any of the windows."),
        (WOMAN2,
         "Now, the date. We had hoped to open at the end of February, but the "
         "building work ran late, as building work does. So the doors open on "
         "the fourteenth of March, which is a Saturday, and there'll be music "
         "and free coffee all day."),
        (WOMAN2,
         "It's a bigger building than people expect. The plans originally "
         "showed two floors, then somebody sensibly argued for more space, and "
         "what's been built has three. The ground floor is for children, the "
         "first floor is the main collection, and the top floor is a quiet "
         "study area, which I suspect is the one that will matter to you."),
        (WOMAN2,
         "To borrow anything you have to be a member, and it's free. You can "
         "fill in a form at the desk, or you can post one, but honestly the "
         "fastest way by a long way is to do it online - it takes about four "
         "minutes and your card is waiting for you when you walk in."),
        (WOMAN2,
         "And one last thing, which I think is rather good. Every Thursday "
         "evening there's a talk by a writer, and for members there's no "
         "charge at all. Non-members pay five pounds. So that's another reason "
         "to join before you come. Thank you, and do come on the fourteenth."),
    ],
}

PART3 = {
    "intro": "You will hear an interview with Rana Aliyeva, who left her job "
             "in a bank to open a bakery. For each question, choose the "
             "correct answer A, B or C.",
    "questions": [
        {"q": 11, "ask": "Why did Rana leave the bank?",
         "options": ["She was asked to move to another city.",
                     "She realised she dreaded every Monday.",
                     "She was offered money to leave."],
         "answer": "B"},
        {"q": 12, "ask": "What was the hardest part of the first year?",
         "options": ["Getting up at four in the morning.",
                     "Finding customers.",
                     "Working without anyone to ask for advice."],
         "answer": "C"},
        {"q": 13, "ask": "What does Rana say about her prices?",
         "options": ["They are higher than she would like.",
                     "She lowered them after the first month.",
                     "They are the same as the supermarket's."],
         "answer": "A"},
        {"q": 14, "ask": "What surprised Rana most about running a business?",
         "options": ["How much of the day is spent on paperwork.",
                     "How quickly the bread sells out.",
                     "How friendly her competitors are."],
         "answer": "A"},
        {"q": 15, "ask": "What does Rana plan to do next?",
         "options": ["Open a second bakery.",
                     "Teach other people to bake.",
                     "Sell to restaurants."],
         "answer": "B"},
    ],
    "lines": [
        (MAN, "Rana, you had a good job in a bank. What made you walk away "
              "from it?"),
        (WOMAN,
         "People always assume there was some dramatic moment. There wasn't. "
         "They did offer me a transfer to Samarkand, and there was a payment "
         "on the table if I wanted to go quietly - but neither of those was "
         "it. It was noticing that by Sunday afternoon I already felt heavy "
         "about the morning. Eleven years of that is enough."),
        (MAN, "And the first year of the bakery - what was the worst of it?"),
        (WOMAN,
         "Not the hours, oddly. Four o'clock becomes normal faster than you'd "
         "think. And the customers came, slowly but they came. What I wasn't "
         "ready for was that there was nobody above me. In the bank, if I "
         "didn't know something, I asked. Suddenly every decision, good or "
         "terrible, was mine, and there was no one in the building who knew "
         "more than I did."),
        (MAN, "Your bread isn't the cheapest in the street."),
        (WOMAN,
         "No, and I'm not comfortable about that. I'd love to charge less. But "
         "flour costs what it costs, and I pay two people properly. The "
         "supermarket sells a loaf for less than my ingredients. I put my "
         "prices up in the second month, not down, and I lost a few regulars, "
         "which still bothers me."),
        (MAN, "Has anything about running a business genuinely surprised you?"),
        (WOMAN,
         "The forms. Nobody tells you. I imagined I'd spend my days baking. I "
         "spend a remarkable amount of them at a desk with tax papers and "
         "orders and licences. The bread is maybe half the job, if that. The "
         "other bakers, by the way, have been lovely - I expected them to see "
         "me as a threat and they simply didn't."),
        (MAN, "And what's next? Another shop?"),
        (WOMAN,
         "Everyone asks that, and no. One is quite enough to worry about, and "
         "restaurants want deliveries at hours I can't manage. What I am doing "
         "is starting classes on Sunday mornings, upstairs. Fifteen people at "
         "a time, learning to make a decent loaf. That's the part I'm excited "
         "about."),
    ],
}

PART4 = {
    "intro": "You will hear a conversation between Omar and Lena about "
             "learning to drive. Decide if each sentence is correct or "
             "incorrect. If it is correct, choose YES. If it is incorrect, "
             "choose NO.",
    "statements": [
        {"q": 16, "text": "Lena passed her driving test at the first attempt.",
         "answer": "NO"},
        {"q": 17, "text": "Omar and Lena agree that lessons are expensive.",
         "answer": "YES"},
        {"q": 18, "text": "Lena thinks learning in a city is easier.",
         "answer": "NO"},
        {"q": 19, "text": "Omar is nervous about the theory part of the test.",
         "answer": "NO"},
        {"q": 20, "text": "Lena offers to let Omar practise in her car.",
         "answer": "YES"},
    ],
    "lines": [
        (MAN, "Lena, you've got your licence now, haven't you? First time, I "
              "suppose."),
        (WOMAN,
         "I wish. Third. I failed the first one for going too slowly, which I "
         "still think is unfair, and the second time I stopped in the wrong "
         "place. Third time everything went right."),
        (MAN, "That's three lots of fees, then. I've worked out that the "
              "lessons alone are going to cost me more than my holiday."),
        (WOMAN,
         "Oh, it's ridiculous. Forty pounds an hour where I went, and you need "
         "far more hours than they tell you at the start. I don't know how "
         "anyone manages it."),
        (MAN, "At least you learned here in town. I'm told the city's the place "
              "to do it - you get used to the traffic."),
        (WOMAN,
         "That's what people say, and I don't agree at all. In the city you "
         "spend the whole lesson sitting still in a queue. My cousin learned in "
         "a village and drove a hundred kilometres in her first month. She was "
         "a far better driver than me by the end."),
        (MAN, "Well. I've got the theory next week."),
        (WOMAN, "Are you worried?"),
        (MAN,
         "Honestly, no. I've done the practice questions about nine times and "
         "I'm getting nearly all of them. It's the parking that keeps me "
         "awake, not the theory."),
        (WOMAN,
         "Then here's an idea. My car's sitting outside doing nothing most "
         "weekends. Come out with me on a Sunday and we'll find an empty car "
         "park somewhere and you can practise until you're sick of it."),
        (MAN, "Would you really? That would make an enormous difference."),
    ],
}

# ----------------------------------------------------------------- READING

R_PART1 = {
    "intro": "Look at the text in each question. What does it say? For each "
             "question, choose the correct answer A, B, C or D.",
    "questions": [
        {"q": 1,
         "text": "Dad - the plumber is coming between 10 and 12. I can't be "
                 "here. Don't let him start until he's given you a price in "
                 "writing. Mum will pay him when she's back. Leyla",
         "ask": "What does Leyla want her father to do?",
         "options": ["Pay the plumber himself.",
                     "Get the cost from the plumber before any work begins.",
                     "Ask the plumber to come back later.",
                     "Tell the plumber that Mum is out."],
         "answer": "B"},
        {"q": 2,
         "text": "TICKETS BOUGHT ONLINE MUST BE COLLECTED FROM THE DESK AT "
                 "LEAST 30 MINUTES BEFORE THE PERFORMANCE",
         "ask": "What are customers told?",
         "options": ["Tickets cannot be bought online.",
                     "Tickets are cheaper at the desk.",
                     "Online tickets must be picked up in good time.",
                     "The desk closes 30 minutes before the performance."],
         "answer": "C"},
        {"q": 3,
         "text": "Sam - I've left the report on your desk. I've marked the "
                 "two paragraphs I'm not happy with. No need to rewrite them "
                 "today, but I'd rather Ahmed didn't see it before we've "
                 "talked. Priya",
         "ask": "What does Priya want Sam to do?",
         "options": ["Rewrite two paragraphs immediately.",
                     "Show the report to Ahmed.",
                     "Keep the report from Ahmed until they have spoken.",
                     "Mark the paragraphs he dislikes."],
         "answer": "C"},
        {"q": 4,
         "text": "The 18:40 to Tashkent will depart from Platform 3, not "
                 "Platform 1. Passengers already on Platform 1 should use the "
                 "bridge. The train will not be held.",
         "ask": "What should passengers on Platform 1 understand?",
         "options": ["The train has been cancelled.",
                     "They must move quickly to another platform.",
                     "The train will wait for them.",
                     "The bridge is closed."],
         "answer": "B"},
        {"q": 5,
         "text": "STAFF ONLY BEYOND THIS POINT. Visitors waiting for an "
                 "appointment should remain in reception, where they will be "
                 "collected.",
         "ask": "What does the notice tell visitors?",
         "options": ["They may go through if they have an appointment.",
                     "Somebody will come to reception for them.",
                     "They should report to a member of staff beyond the door.",
                     "Appointments must be made in reception."],
         "answer": "B"},
    ],
}

R_PART2 = {
    "intro": "Look at the sentences below about a cycling holiday. Read the "
             "text to decide if each sentence is correct or incorrect. If it "
             "is correct, choose YES. If it is not correct, choose NO.",
    "title": "Eight days on two wheels - by Nadia Yusupova",
    "text": [
        "I am not a cyclist. I want to be clear about that before anyone reads "
        "this and decides I am the sort of person who owns special trousers. I "
        "had ridden a bicycle perhaps four times in ten years when a friend "
        "talked me into eight days riding through the hills, and I said yes "
        "mostly because saying no would have required a conversation.",

        "The company had warned us that the first two days were the hardest, "
        "and they were not exaggerating. What they had not mentioned, and what "
        "I would have liked to know, was that the third day was almost entirely "
        "downhill. I spent the first two evenings quietly deciding to go home, "
        "and the third afternoon laughing out loud on a mountain road. Had "
        "somebody told me that was coming, I would have suffered rather less.",

        "The bicycles themselves were far better than anything I could have "
        "hired at home, and were included in the price, which I had assumed "
        "would be extra. The food was included too, and there was a great deal "
        "of it. What was not included was the one thing everybody forgets: "
        "getting yourself to the starting point. My flights cost nearly as "
        "much as the holiday, and I would tell anyone thinking of going to add "
        "that to the price before they decide.",

        "Our guide, Tomas, was twenty-four and could ride up anything without "
        "appearing to breathe. I had expected to find this annoying. In fact "
        "he had a gift for staying exactly far enough behind the slowest person "
        "- usually me - that I never felt I was holding anyone up. Whether he "
        "learned that or was born with it, every company should hire for it.",

        "Would I go again? I have already booked. Not the same route, because "
        "I would like to see somewhere new, and not in August, because the heat "
        "in the afternoons was genuinely difficult. But yes. It turns out you "
        "do not have to be a cyclist.",
    ],
    "statements": [
        {"q": 6, "text": "Nadia had cycled regularly before this holiday.",
         "answer": "NO"},
        {"q": 7, "text": "Nadia wishes she had been told what the third day "
                         "would be like.",
         "answer": "YES"},
        {"q": 8, "text": "Nadia had to pay extra to hire a bicycle.",
         "answer": "NO"},
        {"q": 9, "text": "Nadia thinks Tomas judged his speed well.",
         "answer": "YES"},
        {"q": 10, "text": "Nadia intends to take the same holiday again next "
                          "August.",
         "answer": "NO"},
    ],
}

R_PART3 = {
    "intro": "Read the text and questions below. For each question, choose the "
             "correct answer A, B, C or D.",
    "title": "The repair shop that will not sell you anything",
    "text": [
        "On the last Saturday of every month, a hall in the east of the city "
        "fills up with broken things. People arrive carrying toasters, lamps, "
        "bicycles, a chair with three legs, and once, memorably, a piano "
        "accordion. Nobody pays anything. Nobody buys anything either, which is "
        "rather the point.",

        "The Repair Cafe was started four years ago by Dilshod Rakhimov, who "
        "had spent twenty years fixing washing machines for a living and had "
        "grown tired of telling customers that it would be cheaper to buy a new "
        "one. 'That sentence is a lie we have all agreed to believe,' he says. "
        "'It is cheaper for the shop. It is not cheaper for you, and it is "
        "certainly not cheaper for anybody else.'",

        "Eleven volunteers now turn up each month. They are not all engineers: "
        "there is a retired tailor who handles anything made of cloth, a "
        "seventeen-year-old who is better with laptops than everyone else "
        "combined, and a woman who was a dentist and who turns out to be "
        "remarkably good with small metal parts. The rule is that the owner "
        "stays and watches, and where possible holds the screwdriver. Dilshod "
        "is firm about this. Handing the object back mended, he says, teaches "
        "nobody anything, and next month they are back with something else.",

        "Not everything can be saved. Roughly a third of what arrives leaves "
        "broken, usually because a part is no longer made, and the volunteers "
        "have learned to say so early rather than spend an hour being kind. "
        "What surprises visitors is how often the fault is something trivial - "
        "a loose wire, a blocked filter - on a machine the owner had already "
        "decided was finished.",

        "The cafe costs almost nothing to run; the hall is lent free and the "
        "tools were donated. Dilshod has been asked more than once to open a "
        "shop and charge for repairs, and refuses every time. 'The moment I "
        "take money, I have to be quick,' he says. 'And the moment I have to be "
        "quick, you go home and I keep the screwdriver.'",
    ],
    "questions": [
        {"q": 11, "ask": "Why did Dilshod start the Repair Cafe?",
         "options": ["He had lost his job fixing washing machines.",
                     "He no longer believed the advice he had been giving.",
                     "He wanted to sell second-hand machines.",
                     "A customer suggested it to him."],
         "answer": "B"},
        {"q": 12, "ask": "What does the writer say about the volunteers?",
         "options": ["They all have a technical background.",
                     "Most of them are retired.",
                     "Their useful skills come from very different lives.",
                     "They are trained by Dilshod before they start."],
         "answer": "C"},
        {"q": 13, "ask": "Why must owners stay while their object is repaired?",
         "options": ["So that they learn to do it themselves next time.",
                     "Because the volunteers need someone to hold the tools.",
                     "So that nobody leaves without paying.",
                     "Because the hall cannot be left empty."],
         "answer": "A"},
        {"q": 14, "ask": "What do visitors find surprising?",
         "options": ["How many objects cannot be mended.",
                     "How long each repair takes.",
                     "How minor the problem often is.",
                     "How quickly the volunteers give up."],
         "answer": "C"},
        {"q": 15, "ask": "Why does Dilshod refuse to charge for repairs?",
         "options": ["He does not need the money.",
                     "The tools were given to him for free.",
                     "He would then have to work in a way he disagrees with.",
                     "It would be against the rules of the hall."],
         "answer": "C"},
    ],
}

R_PART4 = {
    "intro": "Read the text below and choose the correct answer for each gap.",
    "title": "Lost walker found after two nights on the mountain",
    "text": "A walker who went missing on Thursday has been found alive after "
            "spending two nights on the mountain. Rescue teams had been "
            "searching since Friday morning and had almost (16) ......... hope "
            "when a farmer reported seeing a light. The man, who has not been "
            "named, had (17) ......... to tell anyone which route he was "
            "taking. He was suffering from cold but was otherwise well, and "
            "was able to (18) ......... down to the road with help. Walkers "
            "are (19) ......... to leave their plans with somebody before "
            "setting out. The rescue team said they would (20) ......... the "
            "public informed about the man's condition.",
    "gaps": [
        {"q": 16, "options": ["given up", "put off", "taken out", "brought in"],
         "answer": "A"},
        {"q": 17, "options": ["missed", "lost", "failed", "refused"],
         "answer": "C"},
        {"q": 18, "options": ["make", "walk", "take", "go"], "answer": "B"},
        {"q": 19, "options": ["ordered", "advised", "insisted", "demanded"],
         "answer": "B"},
        {"q": 20, "options": ["keep", "hold", "stay", "leave"], "answer": "A"},
    ],
}

R_PART5 = {
    "intro": "Read the text. Think of the word which best fits each gap. "
             "Write ONE word for each gap.",
    "title": "From: Bekzod   To: Anna",
    "text": "Hi Anna,\n\nSorry for the slow reply - I have (21) ......... "
            "working every evening this month. The course is going well, "
            "although it is harder (22) ......... I expected. There are "
            "twenty of us and I think I am the (23) ......... one who has "
            "never studied economics before, which was a shock in the first "
            "week.\n\nThe good news is that if I pass in June, the company "
            "will pay (24) ......... the second year. So there is no chance "
            "of me coming to Bukhara before the summer, I'm afraid. Let's "
            "arrange something (25) ......... the exams are over.\n\nBekzod",
    "gaps": [
        {"q": 21, "answer": "been"},
        {"q": 22, "answer": "than"},
        {"q": 23, "answer": "only"},
        {"q": 24, "answer": "for"},
        {"q": 25, "answer": "when / once / after"},
    ],
}

# ----------------------------------------------------------------- WRITING

WRITING1 = {
    "task": "A new sports centre has just opened near where you live and you "
            "want to go with your English friend, Chris. Write an email to "
            "Chris. In your email:",
    "points": ["tell Chris about the new sports centre",
               "suggest a day and a time to go",
               "ask Chris to book the court."],
    "words": "Write 35-45 words.",
}

WRITING2 = {
    "task": "This is part of an email you receive from an English friend. Now "
            "write an email, giving your friend some advice.",
    "quote": "I really want to improve my English before I start university "
             "next year, but I only have about an hour a day. Should I take a "
             "class, or is it better to study on my own? What would you do?",
    "words": "Write about 100 words.",
}
