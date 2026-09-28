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
| `p04bd_digital.py` | Pre-Intermediate | 4B + 4D Celebrations | 152 | 100 |
| `p02ac_digital.py` | Pre-Intermediate | 2A + 2C Travel and tourism | 163 | 129 |

The keys are his answer keys, joined box by box by hand. Where his key gives
samples rather than one answer (2.7 in 2A & 2C, the listening questions), the
box is his to mark, not the computer's.
