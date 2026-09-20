"""Make a booklet fit twelve pages without taking anything out of it.

The booklets are generated as Word files, and a few of them run to sixteen
pages. Reprinting sixteen pages when the rest of the course is twelve is
awkward to staple, awkward to file and a third more paper for every student.

Nothing here touches a word of the content. It tightens the typography -
line spacing, the space between paragraphs, the body size by half a point,
the page margins - by the smallest amount that gets the booklet onto twelve
pages, and stops there. The steps are tried mildest first, so a booklet that
only needs a nudge only gets a nudge.

Word does the page counting, because Word is what laid the booklet out in
the first place and any other renderer would give a different answer.

    python3 handouts/fit_to_12.py "in.docx" --out "out.docx"
    python3 handouts/fit_to_12.py --folder "…/_NEW BOOKLET STYLE" --into "…/dest"
"""
import argparse
import os
import re
import shutil
import subprocess
import zipfile

# Mildest first. Each step is (line spacing, space between paragraphs,
# change in half-points of body size, page margin) as a multiplier or delta.
STEPS = [
    dict(line=1.00, gap=1.00, size=0, margin=1.00),   # 0: untouched
    dict(line=0.96, gap=0.85, size=0, margin=1.00),
    dict(line=0.93, gap=0.74, size=0, margin=0.94),
    dict(line=0.93, gap=0.66, size=-1, margin=0.90),
    dict(line=0.90, gap=0.58, size=-1, margin=0.86),
    dict(line=0.88, gap=0.50, size=-2, margin=0.82),
    dict(line=0.86, gap=0.44, size=-2, margin=0.78),
]

# Floors, so tightening can never become unreadable.
MIN_LINE, MIN_SIZE = 220, 19          # 1.1 line spacing, 9.5pt type
MIN_TB, MIN_LR = 620, 720             # ~1.1cm top/bottom, ~1.3cm sides


def squeeze(xml, step):
    """Apply one step of tightening to a document.xml."""
    def line(m):
        return 'w:line="%d"' % max(MIN_LINE, round(int(m.group(1)) * step["line"]))
    xml = re.sub(r'w:line="(\d+)"', line, xml)

    def gap(m):
        return '%s="%d"' % (m.group(1), round(int(m.group(2)) * step["gap"]))
    xml = re.sub(r'(w:after|w:before)="(\d+)"', gap, xml)

    if step["size"]:
        def sz(m):
            n = int(m.group(2))
            # headings and the cover carry the design; only body-sized type
            # is reduced, and never below the floor
            return '<%s w:val="%d"/>' % (
                m.group(1), max(MIN_SIZE, n + step["size"]) if n >= 21 else n)
        xml = re.sub(r'<(w:sz|w:szCs) w:val="(\d+)"/>', sz, xml)

    if step["margin"] != 1.0:
        def mar(m):
            vals = dict(re.findall(r'(w:\w+)="(\d+)"', m.group(0)))
            for k, floor in (("w:top", MIN_TB), ("w:bottom", MIN_TB),
                             ("w:left", MIN_LR), ("w:right", MIN_LR)):
                if k in vals:
                    vals[k] = str(max(floor,
                                      round(int(vals[k]) * step["margin"])))
            return "<w:pgMar %s/>" % " ".join(
                '%s="%s"' % kv for kv in vals.items())
        xml = re.sub(r'<w:pgMar[^/]*/>', mar, xml)
    return xml


def rewrite(src, dest, step):
    """Copy a .docx, replacing only the laid-out text of the body."""
    zin = zipfile.ZipFile(src)
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename in ("word/document.xml", "word/styles.xml"):
                data = squeeze(data.decode("utf-8"), step).encode("utf-8")
            zout.writestr(item, data)
    zin.close()


# Bound by name to the document this script opened, never to "active
# document".
# If an open ever failed, "active document" would be whatever the teacher had
# in front of them - and the next two lines would save it as a PDF and close
# it without saving. There is unsaved work in that Word window.
# The timeout matters: exporting sixteen pages takes Word longer than
# AppleScript waits by default, and the failure it gives back is a bare
# "AppleEvent timed out" with the PDF half written.
SCRIPT = '''with timeout of 600 seconds
  tell application "Microsoft Word"
    open POSIX file "%s"
    set theDoc to document "%s"
    save as theDoc file name (POSIX file "%s") file format format PDF
    close theDoc saving no
  end tell
end timeout'''


def to_pdf(docx, pdf):
    """Word lays it out; anything else would paginate differently."""
    if os.path.exists(pdf):
        os.remove(pdf)
    subprocess.run(
        ["osascript", "-e", SCRIPT % (docx, os.path.basename(docx), pdf)],
        check=True, capture_output=True)
    return pdf


def page_count(pdf):
    data = open(pdf, "rb").read()
    counts = [int(n) for n in re.findall(rb"/Count\s+(\d+)", data)]
    return (max(counts) if counts
            else len(re.findall(rb"/Type\s*/Page[^s]", data)))


def fit(src, out_docx, out_pdf, target=12, work=None):
    """Try the steps mildest first; keep the first that fits.

    The scratch files sit beside the finished ones rather than in the system
    temporary folder, because Word is sandboxed and cannot open anything in
    /var/folders - it fails with no message at all.
    """
    work = work or os.path.join(os.path.dirname(out_docx), "_work")
    os.makedirs(work, exist_ok=True)
    for i, step in enumerate(STEPS):
        tmp_docx = os.path.join(work, "try%d.docx" % i)
        tmp_pdf = os.path.join(work, "try%d.pdf" % i)
        rewrite(src, tmp_docx, step)
        n = page_count(to_pdf(tmp_docx, tmp_pdf))
        if n <= target:
            shutil.copy(tmp_docx, out_docx)
            shutil.copy(tmp_pdf, out_pdf)
            return i, n
    return None, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docx", nargs="?")
    ap.add_argument("--out")
    ap.add_argument("--pdf")
    ap.add_argument("--target", type=int, default=12)
    args = ap.parse_args()
    step, n = fit(os.path.abspath(args.docx), os.path.abspath(args.out),
                  os.path.abspath(args.pdf), args.target)
    print("step %s -> %d pages" % (step, n))


if __name__ == "__main__":
    main()
