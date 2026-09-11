"""Build the few files some tests need, rather than committing megabytes of them.

The practice-test PDFs and the digital test carry real books in real life; here
they only need to be the right shape, so they are made on demand and thrown
away with the rest of the test's scratch space.
"""
import base64
import json
import os
import struct
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))


def tiny_png(width=40, height=24):
    """A grey rectangle, so a passage image has something to be."""
    rows = b"".join(b"\x00" + bytes([200] * width) for _ in range(height))

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b""))


def practice_pdfs(folder, count=20, prefix="B1 Practice Test"):
    """Twenty files named the way the uploader reads test numbers out of them."""
    os.makedirs(folder, exist_ok=True)
    body = b"%PDF-1.4\n% a stand-in, not a real book\n" + b"\0" * 2048
    made = []
    for n in range(1, count + 1):
        p = os.path.join(folder, "%s %02d.pdf" % (prefix, n))
        with open(p, "wb") as fh:
            fh.write(body)
        made.append(p)
    return made


def digital_test(path, answered=True, with_images=True):
    """The json the Tests page loads: fifteen questions in three shapes."""
    img = base64.b64encode(tiny_png()).decode()
    questions = []
    for n in range(11, 16):
        questions.append({"num": n, "kind": "yesno",
                          "prompt": "Statement %d about the passage." % n,
                          "options": [{"letter": "A", "text": "YES"},
                                      {"letter": "B", "text": "NO"}],
                          "answer": "A" if answered else None})
    for n in range(16, 21):
        questions.append({"num": n, "kind": "mcq",
                          "prompt": "Question %d about the text?" % n,
                          "options": [{"letter": L, "text": "Option %s" % L}
                                      for L in "ABCD"],
                          "answer": "C" if answered else None})
    for n in range(21, 26):
        questions.append({"num": n, "kind": "gap", "prompt": "Gap %d" % n,
                          "options": [{"letter": L, "text": "word%s" % L}
                                      for L in "ABCD"],
                          "answer": "B" if answered else None})
    if with_images:
        questions[0]["image_b64"] = img
        questions[5]["image_b64"] = img
    data = {"level": "Pre-Intermediate", "number": 1,
            "title": "Practice Test 1 — Reading",
            "passages": {"gap": "A short text with gaps in it.\n\nSecond paragraph."},
            "questions": questions}
    with open(path, "w") as fh:
        json.dump(data, fh)
    return path
