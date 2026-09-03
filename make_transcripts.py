"""Turn a folder of .vtt caption files into one readable transcript booklet.

    python3 make_transcripts.py "~/Downloads/elementary audios" --title "Empower Elementary"

Reads every <unit>.<track>.vtt, strips the timings, joins the caption fragments
back into speech, and lays the lot out with a contents page and bookmarks.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pdfmake

INK = (0.09, 0.09, 0.07)
MUTED = (0.46, 0.46, 0.43)
ACCENT = (0.16, 0.40, 0.28)

TIME = re.compile(r"^\d{2}:\d{2}:\d{2}[.,]\d{3}\s*-->")
SPEAKER = re.compile(r"^([A-Z][\w'’.\- ]{0,24}):\s*(.*)$")


ANNOUNCE = re.compile(r"^Narrator:\s*Track\s*\d+[.\-]\d+\s*$", re.I)


def read_vtt(path):
    """Caption fragments -> blocks of (speaker, [lines]).

    Two things matter here. The opening "Narrator: Track 01.03" is only an
    announcement and is dropped - but the unlabelled lines that follow it are
    the transcript, so they must not be dropped with it. And a speaker who
    talks across several cues gets one block, not one per cue.
    """
    blocks = []
    speaker, lines = None, []

    def flush():
        text = [re.sub(r"\s+", " ", l).strip() for l in lines]
        text = [l for l in text if l]
        if text:
            blocks.append((speaker, text))

    with open(path, encoding="utf-8-sig", errors="replace") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("WEBVTT") or TIME.match(line) or line.isdigit():
                continue
            if ANNOUNCE.match(line):
                flush()
                speaker, lines = None, []
                continue
            m = SPEAKER.match(line)
            if m:
                name, rest = m.group(1), m.group(2)
                if name == speaker:
                    # same voice continuing: a new line, not a new block
                    if rest:
                        lines.append(rest)
                    continue
                flush()
                speaker, lines = name, ([rest] if rest else [])
            else:
                if speaker is None and not lines:
                    speaker = None
                lines.append(line)
    flush()

    # Two shapes appear in these files. A numbered or lettered list, where each
    # marker belongs with the item after it; and ordinary speech chopped into
    # one caption per breath, which reads far better joined back together.
    marker = re.compile(r"^[a-z0-9]{1,2}[.)]?$", re.I)
    shaped = []
    for sp, text in blocks:
        if sum(1 for l in text if marker.match(l)) >= 2:
            items, i = [], 0
            while i < len(text):
                if marker.match(text[i]) and i + 1 < len(text):
                    items.append(text[i].rstrip(".)") + "  " + text[i + 1])
                    i += 2
                else:
                    items.append(text[i])
                    i += 1
            shaped.append((sp, items))
        elif len(text) >= 3 and all(len(l.split()) <= 4 for l in text):
            # a vocabulary list read aloud: keep one item per line
            shaped.append((sp, text))
        else:
            shaped.append((sp, [" ".join(text)]))
    return shaped


def collect(folder):
    units = {}
    for entry in sorted(os.listdir(folder)):
        path = os.path.join(folder, entry)
        if not os.path.isdir(path):
            continue
        for name in sorted(os.listdir(path)):
            m = re.match(r"^(\d+)\.(\d+)\.vtt$", name)
            if not m:
                continue
            unit, track = int(m.group(1)), int(m.group(2))
            units.setdefault(unit, {"folder": entry, "tracks": []})
            units[unit]["tracks"].append(
                (track, "%d.%02d" % (unit, track), os.path.join(path, name)))
    for u in units.values():
        u["tracks"].sort()
    return dict(sorted(units.items()))


def build_unit(unit, data, course):
    """One booklet for one unit, to sit beside that unit's audio."""
    label = "Welcome unit" if unit == 0 else "Unit %d" % unit
    doc = pdfmake.Doc()
    doc.text(course, 11, colour=MUTED, gap_after=2)
    doc.text(label, 26, bold=True, colour=INK, gap_after=2)
    doc.text("Audio transcripts  ·  %d tracks" % len(data["tracks"]), 10.5, colour=MUTED)
    doc.rule()
    for _n, code, path in data["tracks"]:
        paragraphs = read_vtt(path)
        doc.space(8)
        doc.text(code, 13, bold=True, colour=ACCENT, gap_after=2)
        if not paragraphs:
            doc.text("(no speech on this track)", 10.5, colour=MUTED)
        for speaker, lines in paragraphs:
            if speaker:
                doc.text(speaker, 9.5, bold=True, colour=MUTED, indent=6)
            for line in lines:
                doc.text(line, 11, colour=INK, indent=6, leading=15.5)
            doc.space(4)
        doc.space(6)
    return doc.build("%s - %s transcripts" % (course, label),
                     footer=lambda i, n: "%s  ·  %d" % (label, i + 1))


def build(units, title, subtitle):
    doc = pdfmake.Doc()

    # cover
    doc.space(150)
    doc.text(title, 30, bold=True, colour=INK, gap_after=6)
    doc.text(subtitle, 14, colour=MUTED, gap_after=26)
    total = sum(len(u["tracks"]) for u in units.values())
    doc.text("%d units  ·  %d audio tracks" % (len(units), total), 11, colour=MUTED)
    doc.text("Each transcript is headed with its track number, so 1.02 here is the "
             "file 1.02 in the Unit 1 folder.", 11, colour=MUTED, gap_after=0)
    doc.new_page()

    # contents, filled in after the body is laid out
    doc.text("Contents", 20, bold=True, colour=INK, gap_after=10)
    contents_ops, contents_page = doc.pages[-1], doc.page_no
    contents_slots = []
    for unit in units:
        label = "Welcome unit" if unit == 0 else "Unit %d" % unit
        doc.text(label, 11.5, colour=INK)
        contents_slots.append((unit, len(doc.pages[-1]) - 1, contents_page))
    doc.new_page()

    starts = {}
    for unit, data in units.items():
        label = "Welcome unit" if unit == 0 else "Unit %d" % unit
        if doc.y < pdfmake.PAGE_H - doc.margin - 1:
            doc.new_page()
        starts[unit] = doc.page_no
        doc.bookmark(label)
        doc.text(label, 22, bold=True, colour=INK, gap_after=2)
        doc.text("%d tracks" % len(data["tracks"]), 10.5, colour=MUTED)
        doc.rule()
        for _n, code, path in data["tracks"]:
            paragraphs = read_vtt(path)
            doc.space(8)
            doc.text(code, 13, bold=True, colour=ACCENT, gap_after=2)
            if not paragraphs:
                doc.text("(no speech on this track)", 10.5, colour=MUTED)
            for speaker, speech_lines in paragraphs:
                if speaker:
                    doc.text(speaker, 9.5, bold=True, colour=MUTED, indent=6)
                for line in speech_lines:
                    doc.text(line, 11, colour=INK, indent=6, leading=15.5)
                doc.space(4)
            doc.space(6)

    # write the page numbers into the slots kept above
    for unit, op_index, page_index in contents_slots:
        op = doc.pages[page_index][op_index]
        page_label = str(starts[unit] + 1)
        x = pdfmake.PAGE_W - doc.margin - pdfmake.width(page_label, 11.5)
        doc.pages[page_index].append(("text", x, op[2], page_label, 11.5, False, MUTED))
        doc.pages[page_index].append(
            ("rule", doc.margin + pdfmake.width(op[3], 11.5) + 8, op[2] + 3,
             x - 8, (0.87, 0.87, 0.84)))

    def footer(index, count):
        return "" if index == 0 else "%d" % (index + 1)

    return doc.build(title, footer=footer)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--title", default="Audioscripts")
    ap.add_argument("--subtitle", default="Class audio transcripts")
    ap.add_argument("--out", default=None)
    ap.add_argument("--per-unit", action="store_true",
                    help="also write one PDF inside each unit folder")
    ap.add_argument("--only-per-unit", action="store_true",
                    help="write only the per-unit PDFs, not the combined one")
    args = ap.parse_args()

    folder = os.path.expanduser(args.folder)
    units = collect(folder)
    if not units:
        print("No .vtt files found under", folder)
        return 1
    if args.per_unit or args.only_per_unit:
        for unit, data in units.items():
            label = "Welcome unit" if unit == 0 else "Unit %d" % unit
            blob = build_unit(unit, data, args.title)
            path = os.path.join(folder, data["folder"], "%s transcripts.pdf" % label)
            with open(path, "wb") as fh:
                fh.write(blob)
            print("  %-16s %3d tracks  %5.0f KB  ->  %s/%s" % (
                label, len(data["tracks"]), len(blob) / 1024,
                data["folder"], os.path.basename(path)))
    if args.only_per_unit:
        return 0

    data = build(units, args.title, args.subtitle)
    out = args.out or os.path.join(folder, "%s Audioscripts.pdf" % args.title)
    with open(out, "wb") as fh:
        fh.write(data)
    print("%s\n%d units, %d tracks, %.1f MB" % (
        out, len(units), sum(len(u["tracks"]) for u in units.values()),
        len(data) / 1024 / 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
