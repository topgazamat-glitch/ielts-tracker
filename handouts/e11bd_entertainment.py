"""Elementary Unit 11 B+D - Entertainment, as a digital booklet.

Built on Azamat's own U11.2 (11B+11D) handout and its answer key, so the
syllabus and the answers are his: present perfect against past simple, music
and event words, opinion language, and a review to write. Laid out in one
column throughout, because these students read it on a phone.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import booklet_gen as g
from booklet_gen import (section, exercise, text_block, header, finish,
                         note, numbered, plain, p, TEAL, DEEP, GREY)

B = header(
    "UNIT 11 · ENTERTAINMENT", "A2 ELEMENTARY", "Entertainment",
    "Lessons 11B + 11D · I've been to a concert · present perfect or past "
    "simple · music and events · writing a review",
    ["1 <b>Reading</b> &mdash; the concert I nearly missed",
     "2 <b>Grammar</b> &mdash; present perfect or past simple",
     "3 <b>Vocabulary</b> &mdash; music and events",
     "4 <b>Everyday English</b> &mdash; saying what you thought",
     "5 <b>Writing</b> &mdash; a review"],
    ["use the <b>present perfect</b> for an experience and the "
     "<b>past simple</b> for the story of it",
     "hear which one a sentence needs from the time words in it",
     "name the people, the kinds of music and the places",
     "give an opinion, soften a criticism and recommend",
     "write a review in four parts, with no spoilers"],
    "Olimov Azamat")

# ------------------------------------------------------------------ 1 reading
B.append(section(1, "Reading", "the concert I nearly missed"))
B.append(exercise("1.1", "Before you read. Answer in one sentence."))
B.append(numbered("1.1", [
    ("What is the best live concert or event you have ever been to? {}", [None]),
]))
B.append(note("NEW WORDS", [
    "<b>live</b> (adjective) &mdash; performed in front of you, not recorded",
    "<b>a ticket office</b> &mdash; where you buy tickets",
    "<b>sold out</b> &mdash; there are no tickets left",
    "<b>an encore</b> &mdash; an extra song after the end",
]))
B.append(text_block("The Concert I Nearly Missed", [
    "I have been to about ten live concerts in my life, but I have never "
    "wanted to go to one as much as I wanted to go to this one.",
    "The tickets went on sale in March. I forgot. I remembered two days "
    "later, went to the website, and saw the two worst words in English: "
    "<b>sold out</b>. My friend Dilshod said he would find a ticket. He did "
    "not find a ticket.",
    "Then, three days before the concert, a colleague told me her sister "
    "could not go. I have never said yes to anything so fast.",
    "The concert was in an old theatre with terrible parking and perfect "
    "sound. The band played for two hours. They started quietly, with just a "
    "piano; by the third song the whole crowd was standing. They came back "
    "for two encores.",
    "When the lights came on, nobody moved for a moment; everybody looked "
    "slightly surprised to be in a theatre again. I sang every word that "
    "night, and I have listened to that album almost every day since.",
    "Dilshod, by the way, didn't go. He forgot too. Some things run in "
    "friendships.",
]))
B.append(exercise("1.2", "Choose the correct answer. Write a, b or c."))
B.append(numbered("1.2", [
    ("The writer did not buy a ticket in March because &mdash; "
     "a) they were expensive  b) he forgot  c) the site did not work. {}", ["b"]),
    ("He got a ticket in the end because &mdash; a) more tickets appeared  "
     "b) a colleague's sister could not go  c) Dilshod found one. {}", ["b"]),
    ("The theatre had &mdash; a) bad sound  b) bad parking but great sound  "
     "c) no seats. {}", ["b"]),
    ("During the concert the writer &mdash; a) stayed quiet  "
     "b) sang every word  c) left early. {}", ["b"]),
    ("&#9733; “Some things run in friendships” means &mdash; "
     "a) friends often run together  b) friends share the same habits  "
     "c) friendships end quickly. {}", ["b"]),
]))
B.append(exercise("1.3", "Answer in your own words."))
B.append(numbered("1.3", [
    ("How did the band begin, and what had changed by the third song? {}",
     [None]),
    ("Why did nobody move when the lights came on? {}", [None]),
]))
B.append(exercise("1.4", "Find a word in the text that means…"))
B.append(numbered("1.4", [
    ("there are no tickets left {}", ["sold out"]),
    ("an extra song after the end {}", ["an encore"]),
    ("performed in front of you {}", ["live"]),
]))

# ------------------------------------------------------------------ 2 grammar
B.append(section(2, "Grammar", "present perfect or past simple"))
B.append(note("THE TWO JOBS", [
    "<b>Present perfect</b> &mdash; the <b>experience</b>. WHEN is not said "
    "and does not matter. <i>I <b>have been</b> to ten concerts.</i>",
    "<b>Past simple</b> &mdash; the <b>story</b>. WHEN is said, or everybody "
    "knows it. <i>I <b>went</b> to a concert last Saturday.</i>",
    "Its words: <b>ever, never, before, already, yet, just</b>",
    "Its words: <b>yesterday, last week, in 2019, two days ago, then</b>",
]))
B.append(plain("The usual conversation starts with the experience and then "
               "moves to the story:"))
B.append(note("HOW IT GOES", [
    "A: <i>Have you ever been to a rock concert?</i> &nbsp; B: <i>Yes, I have.</i>",
    "A: <i>When did you go?</i> &nbsp; B: <i>I went last year with my brother.</i>",
], colour="#C0745F", fill="#FBF0EE"))
B.append(note("ERROR WARNING", [
    "A past time word <b>forces</b> the past simple.",
    "<i>I have gone there yesterday</i> &#10007; &rarr; "
    "<i>I <b>went</b> there yesterday</i> &#10003;",
], colour="#C0745F", fill="#FBF0EE"))
B.append(exercise("2.1", "Choose the correct form. Write it in the box."))
B.append(numbered("2.1", [
    ("I (have seen / saw) that film three times. {}", ["have seen"]),
    ("We (have watched / watched) it last night. {}", ["watched"]),
    ("(Have you ever been / Did you ever go) to Bukhara? {}",
     ["Have you ever been"]),
    ("She (has bought / bought) the tickets in March. {}", ["bought"]),
    ("They (have just arrived / just arrived) &mdash; they are taking their "
     "coats off. {}", ["have just arrived"]),
    ("My grandfather (has never flown / never flew) in a plane in his life. {}",
     ["has never flown"]),
]))
B.append(exercise("2.2", "Complete the conversation. One word in each box."))
B.append(numbered("2.2", [
    ("A: {} you ever {} (be) to a live concert?", ["Have", "been"]),
    ("B: Yes, I {}. I {} (go) to one last month, actually.", ["have", "went"]),
    ("A: Which band {} you {} (see)?", ["did", "see"]),
    ("B: A jazz group from Tashkent. They {} (play) for two hours, and they "
     "{} (be) fantastic.", ["played", "were"]),
    ("A: I {} never {} (hear) live jazz.", ["have", "heard"]),
    ("B: They {} just {} (announce) a new concert in May.",
     ["have", "announced"]),
]))
B.append(exercise("2.3", "Write about YOU."))
B.append(numbered("2.3", [
    ("Two things you have done (present perfect, no time word). {}", [None]),
    ("Two things you did, with when and where (past simple). {}", [None]),
]))

# --------------------------------------------------------------- 3 vocabulary
B.append(section(3, "Vocabulary", "music and events"))
B.append(exercise("3.1", "Complete the word. The first letter is given."))
B.append(numbered("3.1", [
    ("a person who sings = a s… {}", ["singer"]),
    ("a person who plays in a band = a m… {}", ["musician"]),
    ("a group of musicians = a b… {}", ["band"]),
    ("a person who writes songs = a s…writer {}", ["songwriter"]),
    ("the person who leads an orchestra = a c… {}", ["conductor"]),
    ("people who love a band = f… {}", ["fans"]),
]))
B.append(exercise("3.2", "Kinds of music and events. Write the letter."))
B.append(note("MEANINGS", [
    "<b>a)</b> music with a strong beat, guitars and drums",
    "<b>b)</b> Mozart, Beethoven &mdash; an orchestra",
    "<b>c)</b> the traditional music of a country or region",
    "<b>d)</b> several days of music, usually outside",
    "<b>e)</b> an informal word for a small concert",
]))
B.append(numbered("3.2", [
    ("classical {}", ["b"]),
    ("folk {}", ["c"]),
    ("rock {}", ["a"]),
    ("a festival {}", ["d"]),
    ("a gig {}", ["e"]),
]))
B.append(exercise("3.3", "Your perfect evening out."))
B.append(numbered("3.3", [
    ("What kind of music, where, with whom, and how much would you pay "
     "for a ticket? {}", [None]),
]))

# --------------------------------------------------------- 4 everyday english
B.append(section(4, "Everyday English", "saying what you thought"))
B.append(note("THREE MOVES", [
    "<b>Ask</b> &mdash; <i>What did you think of it? &middot; Did you like "
    "it? &middot; …don't you think?</i>",
    "<b>Say</b> &mdash; <i>I thought it was… &middot; In my opinion… &middot; "
    "I really enjoyed…</i>",
    "<b>Soften a criticism</b> &mdash; <i>It was <b>a bit</b> long. &middot; "
    "I didn't <b>really</b> like the ending. &middot; It wasn't <b>quite</b> "
    "what I expected.</i>",
    "Saying <i>It was bad</i> to somebody who loved it is rude in English. "
    "<i>a bit</i>, <i>really</i> and <i>quite</i> do the softening.",
]))
B.append(exercise("4.1", "Complete with ONE word."))
B.append(numbered("4.1", [
    ("What did you {} of it?", ["think"]),
    ("In my {}, the first half was better.", ["opinion"]),
    ("It was a {} too long for me.", ["bit"]),
    ("I didn't {} like the ending.", ["really"]),
    ("It wasn't {} what I expected.", ["quite"]),
    ("I really {} the songs in the middle.", ["enjoyed"]),
]))
B.append(exercise("4.2", "Make the criticism softer. Rewrite the sentence."))
B.append(numbered("4.2", [
    ("The film was boring. &rarr; {}", ["The film was a bit boring"]),
    ("I hated the ending. &rarr; {}", ["I didn't really like the ending"]),
]))
B.append(exercise("4.3", "Ask a friend about something you have both seen."))
B.append(numbered("4.3", [
    ("Write the question you would ask, and the answer you would expect. {}",
     [None]),
]))

# ------------------------------------------------------------------ 5 writing
B.append(section(5, "Writing", "a review"))
B.append(note("FOUR PARTS, IN ORDER", [
    "<b>1 Introduction</b> &mdash; what it is, where and when you saw it",
    "<b>2 Description</b> &mdash; the event or the plot, but "
    "<b>no ending, no spoilers</b>",
    "<b>3 Opinion</b> &mdash; what was good, and one thing that was not",
    "<b>4 Recommendation</b> &mdash; who should see it, and a rating",
]))
B.append(note("MODEL — do not copy, review something else", [
    "<i>“The Long Way Home” &mdash; a quiet film that stays with you "
    "&#9733;&#9733;&#9733;&#9733;&#9734;</i>",
    "<i>I saw this Uzbek film at the cinema last Saturday. It is about a "
    "driver who takes his mother back to the village she grew up in, and "
    "almost nothing happens, which is the point.</i>",
    "<i>I have seen a lot of road films and this is the gentlest one. The "
    "photography is beautiful and the two actors are very good together. It "
    "was a bit slow in the middle.</i>",
    "<i>I would recommend it to anybody who likes a quiet story. Four stars.</i>",
]))
B.append(exercise("5.1", "Write your review (9–11 sentences)."))
B.append(numbered("5.1", [
    ("A film, a series, a concert or a restaurant. Follow the four parts. {}",
     [None]),
]))
B.append(note("CHECK BEFORE YOU HAND IT IN", [
    "&#9744; all four parts, in order &nbsp; &#9744; no spoilers",
    "&#9744; at least two present perfect sentences",
    "&#9744; at least one criticism, softened",
    "&#9744; a recommendation and a rating",
]))
B.append(note("SELF-CHECK — SECTIONS 2, 3 AND 4", [
    "<b>2.1</b> 1 have seen &middot; 2 watched &middot; 3 Have you ever been "
    "&middot; 4 bought &middot; 5 have just arrived &middot; 6 has never flown",
    "<b>2.2</b> Have…been &middot; have / went &middot; did…see &middot; "
    "played / were &middot; have…heard &middot; have…announced",
    "<b>3.1</b> singer &middot; musician &middot; band &middot; songwriter "
    "&middot; conductor &middot; fans",
    "<b>3.2</b> classical b &middot; folk c &middot; rock a &middot; "
    "festival d &middot; gig e",
    "<b>4.1</b> think &middot; opinion &middot; bit &middot; really &middot; "
    "quite &middot; enjoyed",
]))

data, total, marked = finish(B, "Elementary", 11,
                             "E11BD Entertainment (booklet)")
json.dump(data, open("e11bd.json", "w"))
print("blanks: %d  (%d marked, %d their own words)" % (total, marked, total - marked))
print("layout bytes:", len(data["layout"]))
