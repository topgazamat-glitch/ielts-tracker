"""Load the converted Empower booklets onto the site as digital tests.

    python3 convert_booklet.py ...            (writes the json files)
    export TEACHER_PASSWORD='...'
    python3 upload_booklets.py ~/booklets --level Intermediate
    python3 upload_booklets.py ~/booklets --level Intermediate --upload

Nothing is sent without --upload, so the plan can be read first. A test whose
title is already on the site is skipped, so running it twice adds nothing.

Uploaded tests arrive **unpublished**: they sit on your Tests page until you
open one and publish it, and no student sees a test before then.
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
import uuid

SITE = "https://ielts-tracker-production.up.railway.app"


def sign_in(base, password):
    import http.cookiejar
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    opener.open(base + "/login",
                urllib.parse.urlencode({"password": password}).encode(),
                timeout=60)
    return opener


def existing_titles(opener, base):
    """What is already there, so a second run adds nothing."""
    import re
    page = opener.open(base + "/tests", timeout=60).read().decode(
        "utf-8", "replace")
    rows = re.findall(r"<td[^>]*>\s*<a href=\"/tests/\d+\">([^<]+)</a>", page)
    return {r.strip() for r in rows}


def post_json(opener, base, path):
    boundary = "----booklet" + uuid.uuid4().hex
    name = os.path.basename(path)
    body = b"".join([
        ("--%s\r\nContent-Disposition: form-data; name=\"file\"; "
         "filename=\"%s\"\r\nContent-Type: application/json\r\n\r\n"
         % (boundary, name)).encode(),
        open(path, "rb").read(),
        ("\r\n--%s--\r\n" % boundary).encode(),
    ])
    req = urllib.request.Request(base + "/tests/new", data=body, method="POST")
    req.add_header("Content-Type",
                   "multipart/form-data; boundary=" + boundary)
    return opener.open(req, timeout=180).status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", help="folder of .json files from convert_booklet")
    ap.add_argument("--level", default="", help="only this level")
    ap.add_argument("--site", default=SITE)
    ap.add_argument("--upload", action="store_true", help="actually send them")
    args = ap.parse_args()

    folder = os.path.expanduser(args.folder)
    picked = []
    for f in sorted(os.listdir(folder)):
        if not f.endswith(".json"):
            continue
        data = json.load(open(os.path.join(folder, f)))
        if args.level and data.get("level") != args.level:
            continue
        picked.append((os.path.join(folder, f), data))
    if not picked:
        sys.exit("Nothing matched.")

    password = os.environ.get("TEACHER_PASSWORD", "")
    if not password:
        sys.exit("Set TEACHER_PASSWORD first.")
    opener = sign_in(args.site, password)
    already = existing_titles(opener, args.site)

    sent = skipped = 0
    for path, data in picked:
        title = data.get("title") or os.path.basename(path)
        n = len(data.get("questions") or [])
        if title in already:
            print("  skip     %-34s already there" % title[:34])
            skipped += 1
            continue
        if not args.upload:
            print("  would send %-32s %s, %d questions"
                  % (title[:32], data.get("level"), n))
            continue
        status = post_json(opener, args.site, path)
        print("  sent     %-34s %s, %d questions (%s)"
              % (title[:34], data.get("level"), n, status))
        sent += 1

    print()
    if args.upload:
        print("%d sent, %d already there. They are unpublished - open each on "
              "the Tests page to publish it." % (sent, skipped))
    else:
        print("%d to send, %d already there. Add --upload to do it."
              % (len(picked) - skipped, skipped))


if __name__ == "__main__":
    main()
