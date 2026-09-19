"""Record the listening paper with the voices built into this Mac.

Each speaker gets a different British voice, the narrator reads the
instructions and the question numbers, and every conversation is played twice,
as the real paper does. The pieces are spoken one at a time and joined here,
because `say` speaks in one voice per run.

    python3 exams/make_audio.py --out ~/Desktop/A2\\ Mock\\ Final

Needs nothing that is not already on a Mac: `say` to speak, `afconvert` to
make the mp4 audio, and the standard library to join the pieces.
"""
import argparse
import wave
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import a2_mock_final as paper


def speak(voice, text, dest, rate=160):
    # WAVE, not the AIFF `say` prefers: its AIFF is compressed and the
    # standard library cannot read it back to join the pieces.
    subprocess.run(["say", "-v", voice, "-r", str(rate),
                    "--file-format=WAVE", "--data-format=LEI16@22050",
                    "-o", dest, text], check=True)


def silence(seconds, dest, params):
    out = wave.open(dest, "wb")
    out.setnchannels(params.nchannels)
    out.setsampwidth(params.sampwidth)
    out.setframerate(params.framerate)
    out.writeframes(b"\x00" * int(params.framerate * seconds)
                    * params.nchannels * params.sampwidth)
    out.close()


def join(pieces, dest):
    """Glue the spoken pieces into one file."""
    first = wave.open(pieces[0], "rb")
    params = first.getparams()
    first.close()
    out = wave.open(dest, "wb")
    out.setnchannels(params.nchannels)
    out.setsampwidth(params.sampwidth)
    out.setframerate(params.framerate)
    for p in pieces:
        r = wave.open(p, "rb")
        out.writeframes(r.readframes(r.getnframes()))
        r.close()
    out.close()
    return params


def build(lines, work, tag, gap=0.45):
    """Speak a list of (voice, words) and return the file paths, in order."""
    out = []
    for i, (voice, words) in enumerate(lines):
        f = os.path.join(work, "%s_%03d.wav" % (tag, i))
        speak(voice, words, f)
        out.append(f)
        pause = os.path.join(work, "%s_%03d_gap.wav" % (tag, i))
        r = wave.open(f, "rb"); params = r.getparams(); r.close()
        silence(gap, pause, params)
        out.append(pause)
    return out


def part1(work):
    n = paper.NARRATOR
    seq = [(n, "Part one. Questions one to five. You will hear five short "
               "conversations. You will hear each conversation twice. For each "
               "question, choose A, B or C.")]
    pieces = build(seq, work, "p1_intro", gap=1.2)
    for item in paper.PART1:
        pieces += build([(n, "Question %d." % item["q"])], work,
                        "p1_%dq" % item["q"], gap=1.0)
        pieces += build(item["lines"], work, "p1_%da" % item["q"])
        pieces += build([(n, "Now listen again.")], work,
                        "p1_%dr" % item["q"], gap=1.0)
        pieces += build(item["lines"], work, "p1_%db" % item["q"])
        r = wave.open(pieces[0], "rb"); params = r.getparams(); r.close()
        wait = os.path.join(work, "p1_%d_wait.wav" % item["q"])
        silence(3.0, wait, params)
        pieces.append(wait)
    return pieces


def part2(work):
    n = paper.NARRATOR
    pieces = build([(n, "Part two. Questions six to ten. " + paper.PART2["intro"]
                     + " You will hear the conversation twice.")],
                   work, "p2_intro", gap=1.5)
    for round_ in ("a", "b"):
        if round_ == "b":
            pieces += build([(n, "Now listen again.")], work, "p2_again", gap=1.0)
        pieces += build(paper.PART2["lines"], work, "p2_" + round_)
    r = wave.open(pieces[0], "rb"); params = r.getparams(); r.close()
    wait = os.path.join(work, "p2_wait.wav")
    silence(5.0, wait, params)
    return pieces + [wait]


def part3(work):
    n = paper.NARRATOR
    pieces = build([(n, "Part three. Questions eleven to fifteen. "
                     + paper.PART3["intro"]
                     + " You will hear the conversation twice.")],
                   work, "p3_intro", gap=1.5)
    for round_ in ("a", "b"):
        if round_ == "b":
            pieces += build([(n, "Now listen again.")], work, "p3_again", gap=1.0)
        pieces += build(paper.PART3["lines"], work, "p3_" + round_)
    r = wave.open(pieces[0], "rb"); params = r.getparams(); r.close()
    wait = os.path.join(work, "p3_wait.wav")
    silence(5.0, wait, params)
    return pieces + [wait]


def part4(work):
    n = paper.NARRATOR
    pieces = build([(n, "Part four. Questions sixteen to twenty. "
                     + paper.PART4["intro"]
                     + " You will hear the conversation twice.")],
                   work, "p4_intro", gap=1.5)
    for round_ in ("a", "b"):
        if round_ == "b":
            pieces += build([(n, "Now listen again.")], work, "p4_again", gap=1.0)
        pieces += build(paper.PART4["lines"], work, "p4_" + round_)
    r = wave.open(pieces[0], "rb"); params = r.getparams(); r.close()
    wait = os.path.join(work, "p4_wait.wav")
    silence(5.0, wait, params)
    pieces.append(wait)
    pieces += build([(n, "That is the end of the listening test.")], work,
                    "p4_end", gap=0.5)
    return pieces


def to_m4a(wav, dest):
    subprocess.run(["afconvert", "-f", "mp4f", "-d", "aac", "-b", "64000",
                    wav, dest], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.expanduser("~/Desktop/A2 Mock Final"))
    args = ap.parse_args()
    out = os.path.expanduser(args.out)
    os.makedirs(out, exist_ok=True)
    work = tempfile.mkdtemp(prefix="a2audio-")

    whole = []
    for i, maker in enumerate((part1, part2, part3, part4), 1):
        print("  part %d ..." % i, flush=True)
        pieces = maker(work)
        one = os.path.join(work, "part%d.wav" % i)
        join(pieces, one)
        to_m4a(one, os.path.join(out, "Mock Final - Part %d.m4a" % i))
        whole += pieces
    print("  the whole paper ...", flush=True)
    every = os.path.join(work, "full.wav")
    join(whole, every)
    to_m4a(every, os.path.join(out, "Mock Final - Full listening.m4a"))

    for f in sorted(os.listdir(out)):
        if f.endswith(".m4a"):
            print("   %-38s %.1f MB"
                  % (f, os.path.getsize(os.path.join(out, f)) / 1048576))


if __name__ == "__main__":
    main()
