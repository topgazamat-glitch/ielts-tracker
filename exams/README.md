# Mock exams

The real Test 1 and Test 2 finals cannot be handed out — they are what the
students will sit. This is an original paper built to the same skeleton, so
practising on it rehearses the exam rather than the answers.

    python3 exams/make_paper.py --out ~/Desktop/"A2 Mock Final"
    python3 exams/make_audio.py --out ~/Desktop/"A2 Mock Final"

`a2_mock_final.py` holds the content and nothing else — every question, every
answer and every line of the recording. The paper, the key and the audioscript
are all generated from it, so they cannot drift apart, and the audio is spoken
from the same lines the script prints.

## The shape it copies

| | Real paper | This one |
|---|---|---|
| Listening Part 1 | 5 short conversations, 3 options | same |
| Listening Part 2 | match 5 to A–H | same |
| Listening Part 3 | one conversation, A/B/C | same |
| Listening Part 4 | complete the notes | same |
| Reading Part 1 | match 5 sentences to 8 notices | same |
| Reading Part 2 | vocabulary gap, A/B/C | same |
| Reading Part 3 | article, A/B/C | same |
| Reading Part 4 | grammar in a text, A/B/C | same |
| Reading Part 5 | open cloze, ONE word | same |
| Writing | email, ~50 words, 4 points | same |
| **Marks** | 20 + 25 | 20 + 25 |

## The recording

Made with the voices built into the Mac: a narrator reads the instructions and
the question numbers, and each speaker has a different British voice. Every
part is heard twice, as in the exam. Ten minutes in all.

It is a synthetic voice, not an actor. It is clear and steady, which is the
point for a mock — but do play a real recording at least once before the exam
so the students have heard a human being too.
