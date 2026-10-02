"""Every form of a right answer, so that a handout never marks a right answer wrong.

He found answers marked wrong that were right: a short form where the key had the
full one (*I'm* / *I am*), a number in figures where the key had words, an answer
with "a" in front. The site's marking (core.answer_matches) forgives case,
spaces, curly apostrophes and the full stop at the end, and a list of answers is
written with "/"; everything else has to be in that list. This builds the list.

    ok("am sitting", "'m sitting")          -> am sitting/'m sitting/...
    ok("24", numbers=True)                  -> 24/twenty-four/twenty four
    ok("florist", articles=True)            -> florist/a florist/the florist

Each switch is the script writer's decision, made per box: a spelling task wants
the one spelling, a "write the number in words" task wants words, a task about
short forms wants the short form - so nothing here is applied to every box.
"""
import itertools
import re

# short form -> the full forms it stands for
SHORT = {
    "i'm": ["i am"], "you're": ["you are"], "we're": ["we are"], "they're": ["they are"],
    "he's": ["he is"], "she's": ["she is"], "it's": ["it is"], "that's": ["that is"],
    "what's": ["what is"], "there's": ["there is"], "where's": ["where is"], "who's": ["who is"],
    "here's": ["here is"], "how's": ["how is"],
    "isn't": ["is not"], "aren't": ["are not"], "wasn't": ["was not"], "weren't": ["were not"],
    "don't": ["do not"], "doesn't": ["does not"], "didn't": ["did not"],
    "can't": ["cannot", "can not"], "won't": ["will not"], "couldn't": ["could not"],
    "shouldn't": ["should not"], "wouldn't": ["would not"], "mustn't": ["must not"],
    "haven't": ["have not"], "hasn't": ["has not"], "hadn't": ["had not"],
    "i'll": ["i will"], "you'll": ["you will"], "we'll": ["we will"], "they'll": ["they will"],
    "he'll": ["he will"], "she'll": ["she will"], "it'll": ["it will"],
    "i've": ["i have"], "you've": ["you have"], "we've": ["we have"], "they've": ["they have"],
    "let's": ["let us"],
    # a box that starts after the subject: "I ......... (sit)" -> 'm sitting
    "'m": ["am"], "'re": ["are"], "'s": ["is"],
}
FULL = {}
for short, fulls in SHORT.items():
    for f in fulls:
        if f not in ("am", "are", "is"):           # never "6 am" -> "6'm": the bare verbs only expand, never shrink
            FULL.setdefault(f, short)

ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
        "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]


def number_words(n):
    """1-100 in words: both spellings people use for the tens."""
    if n < 20:
        return [ONES[n]]
    if n == 100:
        return ["a hundred", "one hundred", "hundred"]
    t, o = divmod(n, 10)
    return [TENS[t]] if not o else ["%s-%s" % (TENS[t], ONES[o]), "%s %s" % (TENS[t], ONES[o])]


WORD_NUMBER = {}
for _n in range(0, 101):
    for _w in number_words(_n):
        WORD_NUMBER[_w] = _n

# British and American spellings - students meet both online
SPELL = [("travelling", "traveling"), ("travelled", "traveled"), ("traveller", "traveler"),
         ("travellers", "travelers"), ("centre", "center"), ("kilometres", "kilometers"),
         ("kilometre", "kilometer"), ("metres", "meters"), ("colour", "color"), ("colourful", "colorful"),
         ("favourite", "favorite"), ("organise", "organize"), ("organised", "organized"),
         ("theatre", "theater"), ("neighbour", "neighbor"), ("programme", "program"),
         ("cancelled", "canceled"), ("practise", "practice")]
SPELLING = {}
for gb, us in SPELL:
    SPELLING[gb], SPELLING[us] = us, gb

UNITS = {"kilometres": ["km"], "kilometre": ["km"], "kilometers": ["km"], "minutes": ["mins", "min"],
         "hours": ["hrs"], "euros": ["euro"]}


def _spots(text, contractions, numbers, spelling, units):
    """The text as a list of pieces; each piece is a list of the forms it may take."""
    pieces = []
    # two-word full forms first ("did not"), then single words, keeping what is between them
    pattern = r"(?i)\b(?:%s)\b|'(?:m|re|s)\b|[A-Za-z']+(?:-[A-Za-z]+)?|\d+|[^A-Za-z\d']+" % "|".join(
        re.escape(f) for f in sorted(FULL, key=len, reverse=True))
    for m in re.finditer(pattern, text):
        tok = m.group(0)
        low = tok.lower()
        forms = [tok]
        if contractions and low in SHORT:
            forms += SHORT[low]
        elif contractions and low in FULL:
            forms.append(FULL[low])
        if numbers and low.isdigit() and 0 <= int(low) <= 100 and not re.match(r"[.,]\d", text[m.end():m.end() + 2]):
            forms += number_words(int(low))
        elif numbers and low in WORD_NUMBER:
            forms.append(str(WORD_NUMBER[low]))
        if spelling and low in SPELLING:
            forms.append(SPELLING[low])
        if units and low in UNITS:
            forms += UNITS[low]
        pieces.append(forms)
    return pieces


def ok(*answers, contractions=True, numbers=False, articles=False, spelling=True, units=False, limit=60):
    """All the forms of the given answers, joined with "/" for the key."""
    out = []

    def add(s):
        s = re.sub(r"\s+", " ", s).strip()
        if s and s.lower() not in (o.lower() for o in out):
            out.append(s)

    for a in answers:
        pieces = _spots(a, contractions, numbers, spelling, units)
        for combo in itertools.islice(itertools.product(*pieces), limit):
            text = "".join(combo)
            text = re.sub(r"\s+'(m|re|s)\b", r"'\1", text)       # "I 'm" never; keep "I'm"
            add(text)
            if articles:
                bare = re.sub(r"(?i)^(a|an|the)\s+", "", text)
                add(bare)
                plural = bare.lower().endswith("s") and not bare.lower().endswith("ss")
                for art in (["the"] if plural else ["an" if bare[:1].lower() in "aeiou" else "a", "the"]):
                    add("%s %s" % (art, bare))
    if any("/" in o for o in out):
        raise ValueError("an answer may not contain '/': %r" % out)
    return "/".join(out)


if __name__ == "__main__":
    for args, kw in [(("am sitting", "'m sitting"), {}), (("is raining",), {}),
                     (("24",), {"numbers": True}), (("florist",), {"articles": True}),
                     (("I didn't know the way",), {}), (("100 kilometres",), {"numbers": True, "units": True}),
                     (("What's your new teacher like",), {}), (("travelling",), {})]:
        print(args, kw, "->", ok(*args, **kw))
