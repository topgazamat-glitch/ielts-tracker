"""Upload a folder of practice-test PDFs to one level's Practice tests shelf.

    export TEACHER_PASSWORD='...'
    python3 upload_tests.py "/path/to/tests" --level Pre-Intermediate

Add --section "Answer keys" or "Audios" for those, later. Nothing is sent
without --upload, so the plan can be read first. A file whose title is already
on that shelf is skipped, so running it twice does not duplicate anything.
"""
import argparse
import os
import re
import sys
import urllib.parse
import urllib.request
import uuid

import core

SITE = "https://ielts-tracker-production.up.railway.app"
TYPES = {".pdf": "application/pdf", ".mp3": "audio/mpeg", ".m4a": "audio/mp4",
         ".wav": "audio/wav", ".ogg": "audio/ogg", ".docx":
         "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}


def sign_in(base, password):
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(__import__("http.cookiejar",
                                                      fromlist=["x"]).CookieJar()))
    opener.open(base + "/login",
                urllib.parse.urlencode({"password": password}).encode(), timeout=60)
    return opener


def post_file(opener, base, path, title, level_id, collection, section, unit=""):
    boundary = "----ta" + uuid.uuid4().hex
    ext = os.path.splitext(path)[1].lower()
    with open(path, "rb") as fh:
        blob = fh.read()
    parts = []
    for key, value in (("title", title), ("level_id", str(level_id)),
                       ("collection", collection), ("category", section),
                       ("group_id", ""), ("unit", str(unit)), ("book", "")):
        parts.append(("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n"
                      % (boundary, key, value)).encode("utf-8"))
    parts.append(("--%s\r\nContent-Disposition: form-data; name=\"file\"; "
                  "filename=\"%s\"\r\nContent-Type: %s\r\n\r\n"
                  % (boundary, os.path.basename(path),
                     TYPES.get(ext, "application/octet-stream"))).encode("utf-8"))
    parts.append(blob)
    parts.append(("\r\n--%s--\r\n" % boundary).encode("utf-8"))
    body = b"".join(parts)
    req = urllib.request.Request(base + "/materials/new", data=body)
    req.add_header("Content-Type", "multipart/form-data; boundary=" + boundary)
    return opener.open(req, timeout=600).status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--level", required=True)
    ap.add_argument("--collection", default="practice")
    ap.add_argument("--section", default="Paper")
    ap.add_argument("--site", default=os.environ.get("SITE", SITE))
    ap.add_argument("--password", default=os.environ.get("TEACHER_PASSWORD", ""))
    ap.add_argument("--upload", action="store_true")
    args = ap.parse_args()

    files = sorted(f for f in os.listdir(args.folder)
                   if os.path.splitext(f)[1].lower() in TYPES)
    if not files:
        print("Nothing to send in", args.folder)
        return 1

    if not args.password:
        print("Set TEACHER_PASSWORD first.")
        return 1
    opener = sign_in(args.site, args.password)

    # the level id has to come from the site being written to, not from a local
    # copy of the database, where the numbering may well be different
    page = opener.open(args.site + "/materials", timeout=60).read().decode("utf-8", "replace")
    levels = dict((name.strip(), int(num)) for num, name in
                  re.findall(r'<option value="(\d+)">([^<]+)</option>', page))
    lid = levels.get(args.level)
    if lid is None:
        print("No level called %r on the site. It offers: %s"
              % (args.level, ", ".join(sorted(levels)) or "nothing"))
        return 1
    if args.section not in core.sections(args.collection):
        print("No section %r in %s. It has: %s"
              % (args.section, args.collection, ", ".join(core.sections(args.collection))))
        return 1

    print("%s -> %s / %s / %s" % (args.folder, args.level,
                                  core.collection_label(args.collection), args.section))
    plan = []
    for f in files:
        title = re.sub(r"\.[A-Za-z0-9]+$", "", f).replace("_", " ").strip()
        # the test number in the name is what files the paper, its audio and its
        # answers together under one button
        m = re.search(r"(?i)test[\s_-]*0*(\d{1,2})", title)
        unit = m.group(1) if m else ""
        if core.is_test_shelf(args.collection) and not unit:
            print("   SKIPPED %s - no test number in the name" % title)
            continue
        plan.append((os.path.join(args.folder, f), title, unit))
        print("   %-34s %-9s %6.1f MB" % (title, "Test " + unit if unit else "no test",
              os.path.getsize(os.path.join(args.folder, f)) / 1048576))
    if not args.upload:
        print("\n%d file(s). Add --upload to send them." % len(plan))
        return 0
    sent = 0
    for path, title, unit in plan:
        try:
            post_file(opener, args.site, path, title, lid,
                      args.collection, args.section, unit)
            sent += 1
            print("   sent %s" % title)
        except Exception as exc:
            print("   FAILED %s -> %s" % (title, exc))
    print("\n%d of %d uploaded." % (sent, len(plan)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
