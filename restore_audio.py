"""Put a level's coursebook audio back on the Materials shelf.

The audio was taken off the volume to make room. Everything it needs is still
in Downloads, so putting it back is one command rather than an afternoon.

    export TEACHER_PASSWORD='...'
    python3 restore_audio.py --level Intermediate            # read the plan
    python3 restore_audio.py --level Intermediate --upload

A file already on that shelf is skipped, so running it twice adds nothing, and
a run that stops halfway can simply be run again.
"""
import argparse
import os
import re
import sys
import urllib.parse

SHELVES = {
    "Elementary": {
        "Listening audios": "~/Downloads/Download all Class Audio Files and Captions",
        "Workbook audios": "~/Downloads/Workbook audio-2",
    },
    "Pre-Intermediate": {
        "Listening audios": "~/Downloads/Download all Class Audio Files and Captions_B1",
        "Workbook audios": "~/Downloads/Workbook audio-3",
    },
    "Intermediate": {
        "Listening audios": "~/Downloads/Download all Class Audio Files and Captions_B1+",
        "Workbook audios": "~/Downloads/Workbook audio",
    },
}
UNIT = re.compile(r"(\d{1,2})[._-]\d{2}")


def already_there(opener, site, level_id, section):
    """Titles on that shelf now, so a second run adds nothing."""
    have = set()
    base = "%s/materials?level=%d&c=empower&s=%s" % (
        site, level_id, urllib.parse.quote(section))
    page = opener.open(base, timeout=180).read().decode("utf-8", "replace")
    for u in set(re.findall(r'href="([^"]*u=\d+[^"]*)"', page)):
        one = opener.open(site + re.sub(r"&amp;", "&", u),
                          timeout=180).read().decode("utf-8", "replace")
        have |= {t.strip() for t in
                 re.findall(r'<td[^>]*>\s*([^<]{1,60}?)\s*</td>', one)}
    return have


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", required=True, choices=sorted(SHELVES))
    ap.add_argument("--site",
                    default="https://ielts-tracker-production.up.railway.app")
    ap.add_argument("--upload", action="store_true")
    args = ap.parse_args()

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import upload_booklets as ub
    import upload_tests as ut
    password = os.environ.get("TEACHER_PASSWORD", "")
    if not password:
        sys.exit("Set TEACHER_PASSWORD first.")
    opener = ub.sign_in(args.site, password)

    page = opener.open(args.site + "/materials", timeout=120).read().decode(
        "utf-8", "replace")
    m = re.search(r'<option value="(\d+)"[^>]*>%s</option>' % args.level, page)
    level_id = int(m.group(1))

    sent = skipped = 0
    for section, folder in sorted(SHELVES[args.level].items()):
        have = already_there(opener, args.site, level_id, section)
        files = []
        for root, _dirs, names in os.walk(os.path.expanduser(folder)):
            for n in sorted(names):
                if n.lower().endswith(".mp3"):
                    files.append(os.path.join(root, n))
        print("%s - %d file(s) in %s" % (section, len(files), folder))
        for path in sorted(files):
            title = os.path.splitext(os.path.basename(path))[0]
            unit = UNIT.match(title)
            unit = int(unit.group(1)) if unit else ""
            if title in have:
                skipped += 1
                continue
            if not args.upload:
                print("   would send %-14s unit %s" % (title, unit))
                continue
            ut.post_file(opener, args.site, path, title, level_id,
                         "empower", section, unit)
            sent += 1
            if sent % 25 == 0:
                print("   sent %d..." % sent)
    print()
    print("%d sent, %d already there.%s"
          % (sent, skipped, "" if args.upload else " Add --upload to send them."))


if __name__ == "__main__":
    main()
