"""Empower Elementary Unit 1, as four Play lists - the way Azamat teaches it.

He takes A and C together and B and D together, so Unit 1 is two lessons, and
each lesson gets a vocabulary step and a grammar step.

What the book sets, from the Teacher's Book:
    1A  countries and nationalities; be, positive and negative
    1B  personality and opinion adjectives; be, questions and short answers
    1C  everyday English: asking for and giving information
    1D  writing a personal profile: capital letters and punctuation

The target language is the book's. The sentences are written fresh, so
students meet the language in new sentences rather than rehearsing the ones
already printed in their book.
"""

# ---- 1A&C vocabulary: country -> nationality ------------------------------
COUNTRIES = [
    ("Russia", "Russian"), ("Brazil", "Brazilian"), ("Spain", "Spanish"),
    ("Germany", "German"), ("Japan", "Japanese"), ("France", "French"),
    ("China", "Chinese"), ("Turkey", "Turkish"), ("Mexico", "Mexican"),
    ("Australia", "Australian"), ("Pakistan", "Pakistani"), ("Italy", "Italian"),
    ("Britain", "British"), ("Poland", "Polish"), ("Uzbekistan", "Uzbek"),
    ("Korea", "Korean"), ("Egypt", "Egyptian"), ("India", "Indian"),
    ("Portugal", "Portuguese"), ("Greece", "Greek"), ("Sweden", "Swedish"),
    ("Argentina", "Argentinian"), ("Canada", "Canadian"), ("Thailand", "Thai"),
    ("the USA", "American"),
]

# ---- 1B&D vocabulary: adjective -> what it means --------------------------
# Meanings are kept far apart on purpose: the game builds the wrong answers
# from the other meanings on the list, and two near-synonyms would make a
# question with no right answer.
ADJECTIVES = [
    ("friendly", "nice to other people and easy to talk to"),
    ("kind", "thinks about other people and helps them"),
    ("quiet", "does not talk very much"),
    ("talkative", "talks a lot"),
    ("popular", "a lot of people like this person"),
    ("well-known", "a lot of people know this person"),
    ("funny", "makes other people laugh"),
    ("clever", "learns and understands things quickly"),
    ("shy", "feels nervous with new people"),
    ("confident", "feels sure about what they can do"),
    ("polite", "says please and thank you"),
    ("patient", "can wait without getting angry"),
    ("hard-working", "works a lot and does not stop"),
    ("honest", "always tells the truth"),
    ("generous", "likes giving things to other people"),
    ("serious", "does not often laugh or make jokes"),
    ("lazy", "does not want to work"),
    ("calm", "does not get angry or worried"),
    ("helpful", "does things for other people"),
    ("brave", "is not afraid of difficult things"),
    ("tidy", "keeps everything in the right place"),
    ("careful", "does things slowly and does not make mistakes"),
    ("cheerful", "is usually happy"),
    ("strict", "makes people follow the rules"),
    ("curious", "wants to know about everything"),
]

# ---- 1A&C grammar: be, positive and negative + asking for information ------
# (question, right answer, three wrong ones)
GRAMMAR_AC = [
    ("I ___ from Uzbekistan.", "am", "is", "are", "be"),
    ("She ___ a teacher.", "is", "am", "are", "be"),
    ("They ___ from Brazil.", "are", "is", "am", "be"),
    ("My name ___ Dilnoza.", "is", "are", "am", "be"),
    ("We ___ in the same class.", "are", "is", "am", "be"),
    ("You ___ my best friend.", "are", "is", "am", "be"),
    ("Tokyo ___ in Japan.", "is", "are", "am", "be"),
    ("Aziz and I ___ students.", "are", "is", "am", "be"),
    ("Which is correct?", "I'm from Samarkand.", "I from Samarkand.",
     "I am from Samarkand?", "Am from Samarkand."),
    ("It ___ a very big city.", "is", "are", "am", "be"),
    ("I ___ French. I'm Uzbek.", "am not", "not am", "is not", "aren't"),
    ("He ___ at home today.", "isn't", "amn't", "aren't", "not is"),
    ("We ___ late. We're early.", "aren't", "isn't", "am not", "not are"),
    ("They ___ from Spain. They're from Mexico.", "aren't", "isn't",
     "am not", "not are"),
    ("Which is the short form of 'she is'?", "she's", "shes", "she're", "she'is"),
    ("Which is the short form of 'they are not'?", "they aren't", "they amn't",
     "they isn't", "they not are"),
    ("Sara ___ a doctor. She's a nurse.", "isn't", "aren't", "am not", "not is"),
    ("Which sentence is WRONG?", "He are my brother.", "He is my brother.",
     "He's my brother.", "He isn't my brother."),
    ("The receptionist asks: '___ can I help?'", "How", "What", "Where", "Who"),
    ("'___ your surname?' 'Karimova.'", "What's", "Where's", "How's", "Who's"),
    ("'Can you ___ that, please?' 'K-A-R-I-M-O-V-A.'", "spell", "say",
     "write", "tell"),
    ("'___ from?' 'I'm from Bukhara.'", "Where are you", "Where you are",
     "Where is you", "From where you"),
    ("'What's your phone ___?' '90 123 45 67.'", "number", "address",
     "letter", "name"),
    ("'I'd ___ to do an English class, please.'", "like", "want", "need", "am"),
    ("Sorry, I don't understand. Can you ___ that, please?", "repeat",
     "again", "spell it more", "say twice"),
]

# ---- 1B&D grammar: be questions and short answers + capital letters --------
GRAMMAR_BD = [
    ("___ you from Turkey?", "Are", "Is", "Am", "Do"),
    ("___ she a teacher?", "Is", "Are", "Am", "Does"),
    ("___ I late?", "Am", "Is", "Are", "Do"),
    ("___ they married?", "Are", "Is", "Am", "Do"),
    ("'Are you Brazilian?' 'Yes, ___.'", "I am", "I'm", "I are", "am I"),
    ("'Is he Turkish?' 'No, ___.'", "he isn't", "he not", "he doesn't",
     "isn't he"),
    ("'Are they friends?' 'Yes, ___.'", "they are", "they're", "they is",
     "are they"),
    ("'Are we in Room 6?' 'No, ___.'", "we aren't", "we not", "we don't",
     "aren't we"),
    ("Put in order: Spanish / she / is / ?", "Is she Spanish?",
     "She is Spanish?", "Spanish is she?", "Is Spanish she?"),
    ("Put in order: are / where / from / you / ?", "Where are you from?",
     "Where you are from?", "Where from are you?", "You are from where?"),
    ("'___ your teacher's name?' 'Mr Olimov.'", "What's", "Where's",
     "Who's she", "How's"),
    ("'___ old are you?' 'I'm fifteen.'", "How", "What", "Which", "Who"),
    ("Which question is correct?", "Is your sister at home?",
     "Your sister is at home?", "Is at home your sister?",
     "Does your sister at home?"),
    ("'Is this your bag?' 'Yes, ___.'", "it is", "it's", "is it", "this is"),
    ("'Are you tired?' 'No, ___.'", "I'm not", "I amn't", "I not", "not I am"),
    ("'___ your friends here?' 'Yes, they are.'", "Are", "Is", "Am", "Do"),
    ("My friend Roman is really ___ — everybody likes him.", "friendly",
     "friend", "friendship", "friendly's"),
    ("The film is ___. We all like it.", "great", "greatly", "greater",
     "the great"),
    ("Which needs a capital letter?", "monday", "table", "chair", "window"),
    ("Which sentence is punctuated correctly?", "I'm from Tashkent.",
     "i'm from Tashkent.", "I'm from tashkent.", "I'm from Tashkent"),
    ("Which is correct?", "She speaks English and Russian.",
     "She speaks english and russian.", "she speaks English and Russian.",
     "She Speaks English And Russian."),
    ("Which sentence uses commas correctly?",
     "I like music, films and sport.", "I like music films and sport.",
     "I like, music, films and sport.", "I like music and, films and sport."),
    ("Which word always has a capital letter?", "I", "me", "my", "we"),
    ("Where does the full stop go?", "My name is Aziz.", "My name is Aziz",
     "My. name is Aziz", "My name. is Aziz"),
    ("Which is correct in a profile?", "I'm from Nukus, in Uzbekistan.",
     "I'm from nukus, in uzbekistan.", "i'm from Nukus in Uzbekistan",
     "I'm From Nukus In Uzbekistan."),
]


def lines_vocab(pairs):
    return "\n".join("%s = %s" % (a, b) for a, b in pairs)


def lines_grammar(items):
    return "\n".join("%s = %s | %s | %s | %s" % it for it in items)


LISTS = [
    ("Unit 1A&C · Vocabulary — countries and nationalities",
     "vocab", 1, lines_vocab(COUNTRIES)),
    ("Unit 1A&C · Grammar — be, and asking for information",
     "grammar", 1, lines_grammar(GRAMMAR_AC)),
    ("Unit 1B&D · Vocabulary — what people are like",
     "vocab", 2, lines_vocab(ADJECTIVES)),
    ("Unit 1B&D · Grammar — be questions, and writing about yourself",
     "grammar", 2, lines_grammar(GRAMMAR_BD)),
]

if __name__ == "__main__":
    for title, kind, step, body in LISTS:
        n = len([l for l in body.splitlines() if l.strip()])
        print("%-62s %-8s step %d  %d questions" % (title, kind, step, n))
