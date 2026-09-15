"""Send the coursebook tracks the booklets actually ask for.

Each booklet says which track its listening section needs - "this is track
10.02" - and the coursebook names its files the same way, so nothing has to be
matched by hand.

    export TEACHER_PASSWORD='...'
    python3 upload_audio.py                 # read the plan
    python3 upload_audio.py --upload        # send them

Only the tracks named by a booklet already on the site are sent, so this does
not push four hundred files at a level that needs six.
"""
import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import uuid

SITE = "https://ielts-tracker-production.up.railway.app"

# where each level's class audio lives on this machine
# The same tracks were downloaded more than once, and the naming is not
# consistent between the downloads: 10.02.mp3 in one, 7.16.mp3 in another,
# 07-20.mp3 in a third. Each level lists everywhere worth looking.
SHELVES = {
    "Elementary": [
        "~/Downloads/Download all Class Audio Files and Captions",
        "~/Downloads/elementary audios",
        "~/Downloads/A2+ coursebook & audios",
    ],
    "Pre-Intermediate": [
        "~/Downloads/Download all Class Audio Files and Captions_B1",
    ],
    "Intermediate": [
        "~/Downloads/Download all Class Audio Files and Captions_B1+",
    ],
}

TRACK = re.compile(r"track\s+(\d{1,2}\.\d{2})", re.I)
BANK = "~/Documents/Claude/Material Bank/General English"
FOLDER_LEVELS = [("b1 pre-intermediate", "Pre-Intermediate"),
                 ("b1 intermediate", "Intermediate"),
                 ("a2 elementary", "Elementary")]


def spellings(track):
    """07.10 is also written 7.10, 07-10 and 7-10, depending on the download."""
    unit, num = track.split(".")
    out = []
    for u in {unit, unit.lstrip("0") or "0"}:
        for sep in (".", "-"):
            out.append("%s%s%s.mp3" % (u, sep, num))
    return {n.lower() for n in out}


def find_track(folders, track):
    names = spellings(track)
    for folder in folders:
        for root, _dirs, files in os.walk(os.path.expanduser(folder)):
            for f in files:
                if f.lower() in names:
                    return os.path.join(root, f)
    return None


def post_track(opener, base, level, path, track):
    boundary = "----track" + uuid.uuid4().hex
    body = b"".join([
        ('--%s\r\nContent-Disposition: form-data; name="level"\r\n\r\n%s\r\n'
         % (boundary, level)).encode(),
        ('--%s\r\nContent-Disposition: form-data; name="file"; '
         'filename="%s.mp3"\r\nContent-Type: audio/mpeg\r\n\r\n'
         % (boundary, track)).encode(),
        open(path, "rb").read(),
        ("\r\n--%s--\r\n" % boundary).encode(),
    ])
    req = urllib.request.Request(base + "/audio/new", data=body, method="POST")
    req.add_header("Content-Type", "multipart/form-data; boundary=" + boundary)
    return opener.open(req, timeout=300).status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default=SITE)
    ap.add_argument("--upload", action="store_true")
    args = ap.parse_args()

    import upload_booklets as ub
    password = os.environ.get("TEACHER_PASSWORD", "")
    if not password:
        sys.exit("Set TEACHER_PASSWORD first.")
    opener = ub.sign_in(args.site, password)

    # The track is named inside the booklet, which the teacher's page does not
    # show - it lists the questions, not the layout. So the booklets themselves
    # are the source of truth.
    import convert_booklet as cb
    bank = os.path.expanduser(BANK)
    wanted = {}
    for root, _dirs, files in os.walk(bank):
        for f in sorted(files):
            if "BOOKLET" not in f.upper() or not f.endswith(".docx") \
                    or f.startswith("~$"):
                continue
            level = next((lv for needle, lv in FOLDER_LEVELS
                          if needle in root.lower()), None)
            if not level:
                continue
            text = " ".join(cb.paragraphs(os.path.join(root, f)))
            for track in set(TRACK.findall(text)):
                wanted.setdefault(level, {}).setdefault(track, []).append(
                    f.split("—")[0].strip())

    if not wanted:
        print("No booklet on the site names a track.")
        return
    sent = missing = 0
    for level, tracks in sorted(wanted.items()):
        shelf = SHELVES.get(level)
        print("%s — %d track(s)" % (level, len(tracks)))
        for track in sorted(tracks):
            asked_by = ", ".join(sorted(set(tracks[track])))[:44]
            path = find_track(shelf, track) if shelf else None
            if not path:
                print("   missing   %s  %s  (no file here)" % (track, asked_by))
                missing += 1
                continue
            if not args.upload:
                print("   would send %s  for %s" % (track, asked_by))
                continue
            status = post_track(opener, args.site, level, path, track)
            print("   sent      %s  (%s)" % (track, status))
            sent += 1
    print()
    print("%d sent, %d not on this machine.%s"
          % (sent, missing, "" if args.upload else " Add --upload to send them."))


if __name__ == "__main__":
    main()
