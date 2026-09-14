"""The writing questions the site can suggest.

Written to be used, not to look thorough: each one names a situation a student
can picture, asks for something they could actually say at that level, and is
phrased the way a real paper phrases it. The word counts and times are the ones
the level expects.

The teacher adds their own from the Writing questions page; these are only a
starting shelf so the box is never empty.
"""

# (kind, label, min_words, minutes)
KINDS = [
    ("email", "Email", None, None),
    ("letter", "Letter", None, None),
    ("describe", "Describe something", None, None),
    ("story", "Tell a story", None, None),
    ("opinion", "Opinion", None, None),
    ("task1", "IELTS Task 1", 150, 20),
    ("task2", "IELTS Task 2", 250, 40),
]

BANK = {
    "Beginner": {
        "email": [
            "Write an email to your new friend. Tell them your name, where you live, and what you do every day.",
            "Write an email to a friend about your family. Who is in your family? What do they like?",
            "Your friend wants to visit your city. Write an email. Say when to come and what you can do together.",
        ],
        "describe": [
            "Describe your room. What is in it? What colour is it? What do you do there?",
            "Describe your best friend. What do they look like? What do they like doing?",
            "Describe your favourite food. What is it? When do you eat it? Why do you like it?",
        ],
        "story": [
            "Write about last weekend. Where did you go? Who were you with? What did you do?",
            "Write about your last birthday. What happened? How did you feel?",
        ],
    },
    "Elementary": {
        "email": [
            "Write an email to a friend about a film you watched. Say what it was about and whether you liked it.",
            "You are going to move to a new flat. Write an email to a friend describing it and inviting them to visit.",
            "Write an email to your teacher. Say you cannot come to class tomorrow and explain why.",
        ],
        "letter": [
            "You bought something online and it arrived broken. Write a letter to the shop. Say what you bought, what is wrong, and what you want them to do.",
            "Write a letter to a hotel. You want to book a room for two nights. Say when you are coming and what you need.",
        ],
        "describe": [
            "Describe a place you like going to. Where is it? Why do you go there? What do you do?",
            "Describe a person who is important to you. Who are they and why do they matter?",
        ],
        "opinion": [
            "Some people like living in a city. Others prefer the countryside. Which do you prefer, and why?",
            "Do you think children should have a mobile phone? Say what you think and why.",
        ],
    },
    "Pre-Intermediate": {
        "email": [
            "A friend from another country is coming to stay for a week. Write an email telling them what to bring, what you have planned, and what the weather will be like.",
            "You saw an advertisement for a summer job. Write an email asking about the hours, the pay, and whether you need experience.",
        ],
        "letter": [
            "You stayed at a hotel and the room was not clean. Write a letter to the manager explaining what happened and what you would like them to do.",
            "Write a letter to your local council. There is nowhere for young people to play sport in your area. Explain the problem and suggest a solution.",
        ],
        "opinion": [
            "Some people think students should wear a school uniform. Others disagree. Discuss both views and say what you think.",
            "Many people now work from home. What are the good things about this, and what are the problems?",
            "Some people say learning a language is easier when you are young. Do you agree?",
        ],
        "story": [
            "Write about a time you helped somebody. What happened, and how did you feel afterwards?",
            "Write about a journey that did not go as planned.",
        ],
    },
    "Intermediate": {
        "opinion": [
            "Some people believe that examinations are the best way to measure a student's ability. Others think continuous assessment is fairer. Discuss both views and give your own opinion.",
            "In many countries young people are leaving small towns for the cities. Why is this happening, and what problems does it cause?",
            "Some people think governments should spend money on public transport rather than on new roads. To what extent do you agree?",
            "Social media has changed the way we make friends. Is this a positive or a negative development?",
        ],
        "letter": [
            "You recently attended a course that was not what the advertisement promised. Write a letter to the organisers. Explain what you expected, what actually happened, and what you want them to do.",
            "A friend is thinking of moving to your city for work. Write a letter giving them advice about where to live, how to get around, and what to expect.",
        ],
        "task2": [
            "Some people think that the best way to reduce crime is to give longer prison sentences. Others believe there are better alternatives. Discuss both views and give your own opinion.",
            "Many students choose to study abroad. What are the advantages and disadvantages of this?",
        ],
    },
    "IELTS Novice": {
        "task1": [
            "The chart below shows the number of people who visited three museums in London between 2007 and 2012. Summarise the information by selecting and reporting the main features, and make comparisons where relevant.",
            "The table below gives information about the daily cost of water in four countries. Summarise the information by selecting and reporting the main features, and make comparisons where relevant.",
            "You recently stayed at a friend's house while they were away. Write a letter to your friend. Thank them, explain a small problem that happened, and say what you did about it.",
        ],
        "task2": [
            "Some people think that children should begin learning a foreign language at primary school rather than secondary school. Do the advantages outweigh the disadvantages?",
            "In some countries, people work long hours and have little free time. What are the causes of this, and what can be done about it?",
            "Some people believe that university education should be free for everyone. To what extent do you agree or disagree?",
        ],
    },
    "IELTS Standard": {
        "task1": [
            "The graph below shows the average monthly temperature and rainfall in three cities. Summarise the information by selecting and reporting the main features, and make comparisons where relevant.",
            "The diagram below shows how rainwater is collected and treated for drinking. Summarise the information by selecting and reporting the main features.",
            "The charts below show the proportion of household income spent on food, housing and transport in 1990 and 2020. Summarise the information and make comparisons where relevant.",
        ],
        "task2": [
            "Some people argue that the money spent on space exploration would be better used solving problems on Earth. To what extent do you agree or disagree?",
            "In many countries the gap between the rich and the poor is widening. What problems does this cause, and what measures could reduce it?",
            "Some believe that technology has made our lives more complicated rather than simpler. Discuss both views and give your own opinion.",
            "Governments should discourage people from driving by making fuel more expensive. To what extent do you agree or disagree?",
        ],
    },
}

DEFAULTS = {
    "Beginner": (60, 20), "Elementary": (80, 25),
    "Pre-Intermediate": (140, 30), "Intermediate": (180, 35),
    "IELTS Novice": (250, 40), "IELTS Standard": (250, 40),
}
