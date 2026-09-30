"""A listening section gets a Listen button when its recording is on the site.

The booklets name their track in several ways - "track 10.02", "track 4.8"
for 4.08, and the Uzbek retellings "bu 3.18-trek" - and the shelf has files
uploaded as both 4.08 and 04.08. A track that is not there gives students no
button at all (the booklet says the teacher will read the script), and tells
the teacher looking through that it is missing.

Run me with:  python3 run_tests.py listen
"""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["DATA_DIR"] = tempfile.mkdtemp(); os.environ.pop("TELEGRAM_TOKEN", None)
import core, server

core.init_db()

fails, checks = [], 0


def check(what, cond):
    global checks
    checks += 1
    print(("  ok  " if cond else "  FAIL") + "  " + what)
    if not cond:
        fails.append(what)


for level, name in (("Beginner", "4.04"), ("Intermediate", "06.02"), ("Intermediate", "10.02"),
                    ("Pre-Intermediate Workbook", "1.03")):
    os.makedirs(os.path.join(core.AUDIO_DIR, level), exist_ok=True)
    open(os.path.join(core.AUDIO_DIR, level, name + ".mp3"), "wb").write(b"ID3")

print("1. EVERY WAY A BOOKLET NAMES ITS TRACK")
got = server.add_players("<p><span>Agar audio boʻlsa, bu 4.4-trek.</span></p>", "Beginner", "tok")
check("the Uzbek '4.4-trek' finds 4.04", 'data-src="/audio/Beginner/4.04.mp3?s=tok"' in got)
got = server.add_players("<p>If your class has the audio, this is track 6.02.</p>", "Intermediate", "tok")
check("a shelf that has it as 06.02 is found from 6.02", "/audio/Intermediate/06.02.mp3" in got)
got = server.add_players("<p><span>this is track 1</span><span>0.02</span></p>", "Intermediate", "tok")
check("a track number Word split in two is still read", "/audio/Intermediate/10.02.mp3" in got)
got = server.add_players("<p>track 01.03</p>", "Pre-Intermediate Workbook", "tok")
check("a workbook shelf, its name quoted in the address",
      "/audio/Pre-Intermediate%20Workbook/1.03.mp3" in got)
got = server.add_players("<p>track 4.04</p><p>Play track 4.04 again.</p>", "Beginner", "tok")
check("a track named twice gets one button", got.count('class="lx"') == 1)
check("the button is put after the paragraph that names it",
      got.index("track 4.04</p>") < got.index('class="lx"') < got.index("Play track"))

check("a range names every track in it",
      server.named_tracks("bu 09.03–09.05-treklar.") == [(9, 3), (9, 4), (9, 5)])
check("two joined with va are both named",
      server.named_tracks("bu 10.10 va 10.13-treklar.") == [(10, 10), (10, 13)])
for n in ("4.05", "4.06"):
    open(os.path.join(core.AUDIO_DIR, "Beginner", n + ".mp3"), "wb").write(b"ID3")
got = server.add_players("<p>bu 4.4–4.6-treklar.</p>", "Beginner", "tok")
check("several recordings, one button each, each saying which",
      got.count('class="lx"') == 3 and "Listen · 4.05" in got)

print("\n2. A BOOKLET THAT NAMES THE WRONG RECORDING")
os.makedirs(os.path.join(core.AUDIO_DIR, "Pre-Intermediate"), exist_ok=True)
for n in ("4.06", "4.08"):
    open(os.path.join(core.AUDIO_DIR, "Pre-Intermediate", n + ".mp3"), "wb").write(b"ID3")
got = server.add_players("<p>this is track 4.8.</p>", "Pre-Intermediate", "tok", "Unit 4B & 4D — Celebrations")
check("4B&D's Tokyo conversation plays 4.06, not the drill it names",
      "/4.06.mp3" in got and "/4.08.mp3" not in got)
got = server.add_players("<p>this is track 4.8.</p>", "Pre-Intermediate", "tok", "Some other handout")
check("another handout naming 4.08 still gets 4.08", "/4.08.mp3" in got)
got = server.add_players("<p>bu 4.4-trek.</p>", "Beginner", "tok", "Unit 9A & 9B — Clothes and shopping")
check("a correction for one handout touches no other track", "/4.04.mp3" in got)

print("\n3. A TRACK THAT IS NOT ON THE SITE")
got = server.add_players("<p>this is track 3.18</p>", "Beginner", "tok")
check("a student gets no button", 'class="lx' not in got)
got = server.add_players("<p>this is track 3.18</p>", "Beginner")
check("the teacher is told it is missing", "Track 3.18 is not on the site yet" in got)
check("no level, nothing added", server.add_players("<p>track 4.04</p>", None) == "<p>track 4.04</p>")
check("a price is not a track", 'class="lx' not in server.add_players("<p>It costs 4.04 pounds.</p>",
                                                                       "Beginner", "tok"))

print("\n4. THE PAGES LOAD THE PLAYER")
check("a student's page", "/static/listen.js" in server.student_page("x", "<p>x</p>"))
check("the teacher's pages", "/static/listen.js" in server.page("x", "<p>x</p>"))

print()
print("listen: %d checks, %d failed" % (checks, len(fails)))
sys.exit(1 if fails else 0)
