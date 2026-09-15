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
