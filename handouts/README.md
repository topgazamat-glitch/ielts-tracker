# Handouts written from scratch

`booklet_html.py` renders a handout that already exists as a Word file.
These are handouts that did not exist: each script is one booklet, written in
the same style, and produces the json the Tests page loads.

    python3 handouts/e11bd_entertainment.py     # writes e11bd.json
    python3 upload_booklets.py <folder> --level Elementary --upload

`booklet_gen.py` holds the shared pieces - the teal section bars, the pale
panels, the reading-text blocks, and `gaps()`, which turns every `{}` into a
box and remembers the answer it wants. An answer of `None` means the box is
the student's own words: saved and shown back, never scored.

Written in one column on purpose. Most of these students read on a phone,
where a side-by-side exercise table becomes two columns wrapping every three
words.

| Script | Level | Unit | Boxes | Marked |
|---|---|---|---|---|
| `e11bd_entertainment.py` | Elementary | 11B + 11D | 53 | 45 |
| `p02_asrp_travel.py` | Pre-Intermediate | 2 ASRP | 70 | 60 |

The Elementary one follows Azamat's own `U11.2 (11B+11D)` handout and its
answer key, so its syllabus and answers are his. The Pre-Intermediate one is
written rather than lifted: that book is an image-only scan on this machine,
so the content is built on what his own P02AC/P02BD booklets say Unit 2
teaches. Read it before publishing.

# His own booklets, done on a phone

`digital.py` takes one of Azamat's Word booklets as it is - his design,
rendered by `booklet_html` - and decides how every box is answered on a
phone: chips to tap for a choice, a tick, the number pad, a gap left inside
its sentence, a growing box for a sentence, a big box with a word count for
a piece of writing. It also adds boxes where the paper has only ruled lines
or "circle", and the build stops if any box has no decision.

    python3 handouts/p04bd_digital.py      # writes handouts/p04bd.json
    python3 handouts/p02ac_digital.py      # writes handouts/p02ac.json

Upload the json on the Tests page (it arrives as a handout) and publish it.

| Script | Level | Unit | Boxes | Marked on the spot |
|---|---|---|---|---|
| `b01abc_digital.py` | Beginner | 1A + 1B + 1C Hello! | 199 | 156 |
| `b02a_digital.py` | Beginner | 2A All about me | 180 | 133 |
| `b02b_digital.py` | Beginner | 2B All about me | 196 | 137 |
| `b02c_digital.py` | Beginner | 2C All about me | 173 | 116 |
| `b03a_digital.py` | Beginner | 3A Food and drink | 204 | 143 |
| `b03b_digital.py` | Beginner | 3B Food and drink | 188 | 116 |
| `u011_digital.py` | Elementary | 1.1 People | 68 | 55 |
| `e07bd_digital.py` | Elementary | 7B + 7D Transport | 282 | 251 |
| `e09ab_digital.py` | Elementary | 9A + 9B Clothes and shopping | 293 | 237 |
| `e09ac_digital.py` | Elementary | 9A + 9C Clothes and shopping | 252 | 208 |
| `e09bd_digital.py` | Elementary | 9B + 9D Clothes and shopping | 186 | 164 |
| `e10ac_digital.py` | Elementary | 10A + 10C Communication | 162 | 143 |
| `e10bd_digital.py` | Elementary | 10B + 10D Communication | 160 | 125 |
| `e11ac_digital.py` | Elementary | 11A + 11C Entertainment | 160 | 137 |
| `e11bd_digital.py` | Elementary | 11B + 11D Entertainment | 168 | 109 |
| `e12ac_digital.py` | Elementary | 12A + 12C Travel | 155 | 110 |
| `e12bd_digital.py` | Elementary | 12B + 12D Travel | 153 | 116 |
| `p01ac_digital.py` | Pre-Intermediate | 1A + 1C Communication | 191 | 159 |
| `p01bd_digital.py` | Pre-Intermediate | 1B + 1D Communication | 192 | 145 |
| `p02ac_digital.py` | Pre-Intermediate | 2A + 2C Travel and tourism | 163 | 129 |
| `p02bd_digital.py` | Pre-Intermediate | 2B + 2D Travel and tourism | 154 | 123 |
| `p03ac_digital.py` | Pre-Intermediate | 3A + 3C Money | 154 | 129 |
| `p03bd_digital.py` | Pre-Intermediate | 3B + 3D Money | 152 | 120 |
| `asrp4_digital.py` | Pre-Intermediate | 4 ASP + RP homework | 86 | 69 |
| `p04ac_digital.py` | Pre-Intermediate | 4A + 4C Celebrations | 151 | 105 |
| `p04bd_digital.py` | Pre-Intermediate | 4B + 4D Celebrations | 152 | 100 |
| `i011_digital.py` | Intermediate | 1.1 Talk | 185 | 159 |
| `i012_digital.py` | Intermediate | 1.2 Talk | 173 | 150 |
| `i021_digital.py` | Intermediate | 2.1 Modern life | 221 | 206 |
| `i022_digital.py` | Intermediate | 2.2 Modern life | 204 | 178 |
| `i031_digital.py` | Intermediate | 3.1 Relationships | 227 | 203 |
| `i032_digital.py` | Intermediate | 3.2 Relationships | 198 | 179 |
| `i041_digital.py` | Intermediate | 4.1 Personality | 212 | 197 |
| `i042_digital.py` | Intermediate | 4.2 Personality | 224 | 205 |
| `i051_digital.py` | Intermediate | 5.1 The natural world | 208 | 193 |
| `i052_digital.py` | Intermediate | 5.2 The natural world | 221 | 202 |
| `i061_digital.py` | Intermediate | 6A + 6C Different cultures | 233 | 207 |
| `i062_digital.py` | Intermediate | 6B + 6D Different cultures | 292 | 248 |
| `i07a_digital.py` | Intermediate | 7A House and home | 259 | 220 |
| `i07b_digital.py` | Intermediate | 7B House and home | 294 | 254 |
| `i08b_digital.py` | Intermediate | 8B Information | 279 | 220 |
| `i09ac_digital.py` | Intermediate | 9A + 9C Entertainment | 230 | 184 |
| `i09bd_digital.py` | Intermediate | 9B + 9D Entertainment | 133 | 100 |
| `i10ac_digital.py` | Intermediate | 10A + 10C Opportunities | 158 | 121 |
| `i10bd_digital.py` | Intermediate | 10B + 10D Opportunities | 155 | 108 |

The ASRP pack is not drawn in the booklet style - its gaps are dotted text
and it has no section bars - so `asrp4_digital.py` writes it out again in the
booklet's markup rather than reading the Word file, in four parts that
follow the pack's own seam between the self-checked and teacher-marked parts.

Intermediate explanations stay English. The Intermediate and E12BD booklets
come from the Material Bank `_NEW BOOKLET STYLE` copies: the Desktop
"redesigns" have the same exercises, but their section bars share a table
with what follows, so they would not split into parts. The other Elementary
and Beginner booklets are the Desktop new-design copies, which split cleanly;
E11AC, B02B, B02C and B03A are only in the Material Bank. A booklet with the
older cover (the unit number in a box, the goals under "By the end of this
booklet") calls `Handout.cover(...)` so the page reads its name and goals.

Each script's docstring lists what it puts right: places where the key and
the booklet disagree (a "TWO sentences are correct" that the key ticks three
of, a listening line the key gives to the wrong speaker), since a page that
marks itself cannot be wrong about its own answers. The marking forgives
case and commas, so a correction that is only a capital letter or a comma
is left for the teacher rather than marked right when copied out unchanged.

The Beginner and Elementary ones tell their explanations again in Uzbek (`Handout.retell`):
at that level most students cannot read a grammar box in English. The
examples inside stay English, and so do the reading text and the exercises.
Its class and pair tasks - surveys, a partner's answers - keep their boxes
but are marked `pair()`, so they never hold a part back at home.

The keys are his answer keys, joined box by box by hand. Where his key gives
samples rather than one answer (2.7 in 2A & 2C, the listening questions), the
box is his to mark, not the computer's.

# A handout as homework

On Set homework, "Digital handout" opens one of these for a class with the
set's deadline. It is one piece of that homework and marks itself, out of
ten: half for the parts checked by the deadline (a point a part, out of
five), half for the right answers over every box the key can mark. The
listening part counts for doing, not for right, since at home it can only
be guessed. A written answer needs three words, and the teacher can mark
one as not counting on the handout's writing page - the part it is in then
stops counting as done. The mark is averaged with the teacher's marks for
the rest of the set, like any other piece, into the league.

A handout open to the whole level is practice and earns nothing; one that
is not open opens only for the class it is set to.

# One booklet after another

A student's Handouts page lists the level's booklets in the order of the
course - by unit, the A & C lessons before B & D, the unit's ASRP pack last
(`core.lesson_order`). A booklet set as homework to the class has to have
every part checked before anything after it opens: the list shows the later
ones locked, their address shows which booklet to finish first, and saving
or checking into them is refused (`core.handout_shelf`,
`core.handout_blocked_by`). Booklets before the first one set to the class
stay open as practice, so a class that starts using them at Unit 4 is not
sent back to Unit 1, and a booklet never set holds nobody up. A written
answer the teacher later marks as not counting lowers the mark but does not
shut the student out again.

## Destination units

`dest_b1_digital.py` writes Destination B1 units as handouts from the scanned
book (`~/Downloads/Destination B1.pdf`, pages rendered with `sips` to read
them): units 12 and 23 so far, live as tests 126 and 127. They carry
`"series": "destination"`, so a unit:

- opens only for a class it is set to, whatever that class's level (upload
  with `upload_live.py … --hidden`);
- is linked from a homework line naming it - "Destination B1, Unit 12" -
  by `core.destination_test`;
- never joins the chain of course booklets, nor the handout list on Set homework.

Each exercise keeps the book's letter (A, B, C …) beside its number, so paper
and screen match. The answers are the book's key (PDF pages 232-254). The
docstring lists where the key was put right.

## Workbook units

`wb_pi_digital.py` writes the Empower Pre-Intermediate Workbook (the scan in
`~/Desktop/Empower Second Edition - Books/3. B1 Pre-Intermediate/`, its key on
page 87) as handouts: unit 1 A & C so far, live as test 128. They carry
`"series": "workbook"`:

- a homework line "Workbook unit 1 A&C", set to a class of that level, links
  to it by itself (`core.workbook_test`);
- it opens only where it is set, and is never in the booklet chain.

Its recordings are the workbook's own, uploaded to `/audio/new` under the
level "Pre-Intermediate Workbook". They are kept apart from the class tracks,
which are numbered the same way. The tracks are in
`~/Downloads/Workbook audio-2/…_B1.zip`, with transcripts (.vtt).
