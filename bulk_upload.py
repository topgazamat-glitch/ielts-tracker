"""Upload a folder of materials in one go, reading the unit and book from names.

    python3 bulk_upload.py "/path/to/Empower B1 audio" --level Intermediate
    python3 bulk_upload.py "/path/..." --level Intermediate --upload

Without --upload it only reports what it found, so the guesses can be checked
before anything is sent. Files go to the live dashboard over HTTPS, exactly as
if they had been chosen by hand on the Materials page.
"""
import argparse
import os
import re
import sys
import urllib.parse
import urllib.request
import uuid

import core

AUDIO = {".mp3", ".m4a", ".wav", ".ogg", ".oga", ".aac", ".mp4", ".m4b"}
DOCS = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".zip", ".jpg", ".jpeg", ".png"}

UNIT_PATTERNS = [
    re.compile(r"unit[\s_-]*0*(\d{1,2})", re.I),
    re.compile(r"\bu[\s_-]*0*(\d{1,2})\b", re.I),
    re.compile(r"(?:^|[^\d])0*(\d{1,2})[\s_-]*(?:track|audio|cd)", re.I),
    re.compile(r"^0*(\d{1,2})[\s._-]"),
]
CLASS_HINTS = ("class", "student", "coursebook", "course book", "sb", "cb")
WORK_HINTS = ("work", "workbook", "wb", "self study", "self-study")


def guess_unit(path):
    """Look in the file name first, then the folders above it."""
    if re.search(r"welcome", path, re.I):
        return 0
    parts = [os.path.basename(path)] + os.path.normpath(path).split(os.sep)[::-1]
    for part in parts:
        for pattern in UNIT_PATTERNS:
            m = pattern.search(part)
            if m:
                n = int(m.group(1))
                if n in core.UNITS or n == 0:      # 0 is the Welcome unit
                    return n
    return None


def guess_book(path):
    low = path.lower()
    hit_class = max((low.rfind(h) for h in CLASS_HINTS), default=-1)
    hit_work = max((low.rfind(h) for h in WORK_HINTS), default=-1)
    if hit_work > hit_class:
        return "work"
    if hit_class >= 0:
        return "class"
    return None


def clean_title(path, unit, book):
    stem = os.path.splitext(os.path.basename(path))[0]
    stem = re.sub(r"[_]+", " ", stem).strip()
    bits = []
    # do not repeat what the file name already says; the section a file sits in
    # already tells the student which book it is, so leave that out of the title
    if unit and not re.match(r"^(unit\s*)?0*%d\b" % unit, stem, re.I):
        bits.append("Unit %d" % unit)
    bits.append(stem)
    return " · ".join(bits)[:120]


def scan(folder):
    found = []
    for root, _dirs, files in os.walk(folder):
        for name in sorted(files):
            if name.startswith("."):
                continue
            path = os.path.join(root, name)
            ext = os.path.splitext(name)[1].lower()
            if ext not in AUDIO and ext not in DOCS:
                continue
            unit = guess_unit(path)
            book = guess_book(path)
            found.append({
                "path": path, "unit": unit, "book": book,
                "size": os.path.getsize(path),
                "title": clean_title(path, unit, book),
            })
    found.sort(key=lambda f: (f["unit"] or 99, f["book"] or "", f["title"]))
    return found


def sign_in(base, password):
    """One session for the whole run, rather than a login per file."""
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
    opener.open(base + "/login",
                urllib.parse.urlencode({"password": password}).encode(), timeout=60)
    return opener


def existing_titles(opener, base, level_id):
    """What is already there, so a re-run does not duplicate anything."""
    try:
        html = opener.open("%s/materials?level=%d" % (base, level_id),
                           timeout=120).read().decode()
    except Exception:
        return set()
    return set(re.findall(r"/materials/\d+/file\">([^<]+)</a>", html))


def post(opener, base, item, level_id, collection, category, group_id=""):
    boundary = "b" + uuid.uuid4().hex
    parts = []
    fields = {
        "title": item["title"], "level_id": str(level_id or ""),
        "collection": collection, "category": category,
        "group_id": group_id, "note": "",
        "unit": str(item["unit"] or ""), "book": item["book"] or "",
    }
    for key, value in fields.items():
        parts.append(('--%s\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n'
                      % (boundary, key, value)).encode())
    with open(item["path"], "rb") as fh:
        blob = fh.read()
    parts.append(('--%s\r\nContent-Disposition: form-data; name="file"; filename="%s"\r\n'
                  'Content-Type: application/octet-stream\r\n\r\n'
                  % (boundary, os.path.basename(item["path"]))).encode()
                 + blob + b"\r\n")
    parts.append(("--%s--\r\n" % boundary).encode())
    req = urllib.request.Request(base + "/materials/new", data=b"".join(parts),
        headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
    opener.open(req, timeout=900)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--level", required=True, help="level name, e.g. Intermediate")
    ap.add_argument("--collection", default="empower")
    ap.add_argument("--section", default="Listening audios")
    ap.add_argument("--site", default="https://ielts-tracker-production.up.railway.app")
    ap.add_argument("--password", default=os.environ.get("TEACHER_PASSWORD", ""))
    ap.add_argument("--upload", action="store_true", help="actually send them")
    ap.add_argument("--keep-unfiled", action="store_true",
                    help="upload files with no unit number too")
    args = ap.parse_args()

    items = scan(args.folder)
    if not args.keep_unfiled:
        unfiled = [i for i in items if i["unit"] is None]
        items = [i for i in items if i["unit"] is not None]
    if not items:
        print("No audio or document files found in", args.folder)
        return 1

    too_big = [i for i in items if i["size"] > 45 * 1024 * 1024]
    unknown = [i for i in items if i["unit"] is None]
    total = sum(i["size"] for i in items)

    print("%d file(s), %s in total" % (len(items), core.human_size(total)))
    print()
    print("%-5s %-11s %-9s %s" % ("UNIT", "BOOK", "SIZE", "TITLE"))
    for i in items:
        print("%-5s %-11s %-9s %s" % (
            i["unit"] or "?", core.book_label(i["book"]) if i["book"] else "?",
            core.human_size(i["size"]), i["title"][:60]))
    if unknown:
        print()
        print("!! %d file(s) have no unit number" % len(unknown))
    if not args.keep_unfiled and unfiled:
        print()
        print("skipped, no unit number (add --keep-unfiled to include them):")
        for i in unfiled:
            print("   ", os.path.basename(i["path"]))
    if too_big:
        print()
        print("!! %d file(s) are over 45 MB and cannot be sent by a bot:" % len(too_big))
        for i in too_big:
            print("   ", os.path.basename(i["path"]), core.human_size(i["size"]))

    if not args.upload:
        print()
        print("Nothing sent. Re-run with --upload once the table looks right.")
        return 0
    if not args.password:
        print("Set --password or TEACHER_PASSWORD first.")
        return 1

    db = core.connect()
    row = db.execute("SELECT id FROM levels WHERE name=?", (args.level,)).fetchone()
    level_id = row["id"] if row else None
    if level_id is None:
        print("Unknown level:", args.level)
        return 1

    opener = sign_in(args.site, args.password)
    already = existing_titles(opener, args.site, level_id)
    todo = [i for i in items
            if i["size"] <= 45 * 1024 * 1024 and i["title"] not in already]
    if already:
        print("already on the site: %d - skipping those" % (len(items) - len(todo)))

    sent, failed = 0, []
    for i in todo:
        for attempt in (1, 2, 3):
            try:
                post(opener, args.site, i, level_id, args.collection, args.section)
                sent += 1
                break
            except Exception as exc:
                if attempt == 3:
                    failed.append((i["title"], str(exc)[:60]))
                else:
                    import time
                    time.sleep(3 * attempt)
                    opener = sign_in(args.site, args.password)
        if sent and sent % 10 == 0:
            print("  %d/%d uploaded" % (sent, len(todo)), flush=True)
    print("Done: %d uploaded, %d failed." % (sent, len(failed)))
    for title, why in failed:
        print("   failed:", title, "-", why)
    return 0


if __name__ == "__main__":
    sys.exit(main())
