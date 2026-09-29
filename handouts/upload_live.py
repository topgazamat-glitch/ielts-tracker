"""Put a built handout on the live site and open it to its level.

    python3 handouts/upload_live.py handouts/p01bd.json            refuses if a handout has that title
    python3 handouts/upload_live.py handouts/p01bd.json --again    a new version beside the old
    python3 handouts/upload_live.py handouts/p01bd.json --hidden   uploaded, not opened

The password is read from config.json and never printed. Publishing on the
site is a switch, so this looks at the handout's state before pressing it,
and again after, rather than pressing it twice by accident.
"""
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import uuid
import http.cookiejar

SITE = "https://ielts-tracker-production.up.railway.app"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def opener():
    """Signed in as the teacher. A push to main restarts the site for about a
    minute, so a 502 is waited out rather than taken as an answer."""
    pw = json.load(open(os.path.join(ROOT, "config.json")))["teacher_password"]
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    for _try in range(30):
        try:
            op.open(SITE + "/login", urllib.parse.urlencode({"password": pw}).encode(), timeout=30).read()
            return op
        except urllib.error.HTTPError as e:
            if e.code not in (502, 503):
                raise
            time.sleep(10)
    sys.exit("the site has not come back after five minutes")


def menu(op):
    """{title: (id, open to the level?)} from the Digital handout menu on Set homework."""
    pg = html.unescape(op.open(SITE + "/assignments", timeout=60).read().decode())
    out = {}
    for tid, title in re.findall(r'<option value="(\d+)"[^>]*>([^<]*)</option>', pg):
        hidden = title.endswith("(opens only for this class)")
        out[title.replace(" (opens only for this class)", "")] = (int(tid), not hidden)
    return out


def main():
    path = sys.argv[1]
    data = json.load(open(path))
    op = opener()
    if data["title"] in menu(op) and "--again" not in sys.argv:
        sys.exit("already there: %s (pass --again to upload a new version)" % data["title"])
    boundary = "----b" + uuid.uuid4().hex
    body = b"".join([("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"h.json\"\r\n"
                      "Content-Type: application/json\r\n\r\n" % boundary).encode(),
                     open(path, "rb").read(), ("\r\n--%s--\r\n" % boundary).encode()])
    req = urllib.request.Request(SITE + "/tests/new", data=body, method="POST")
    req.add_header("Content-Type", "multipart/form-data; boundary=" + boundary)
    tid = int(re.search(r"/tests/(\d+)", op.open(req, timeout=180).geturl()).group(1))
    print("uploaded as test", tid)
    if "--hidden" in sys.argv:
        return
    for _try in range(3):
        state = {i: shown for i, shown in menu(op).values()}
        if state.get(tid):
            print("open to its level")
            return
        try:
            op.open(SITE + "/tests/%d/publish" % tid, b"", timeout=60).read()
        except OSError as e:                  # the switch may have been pressed; look again
            print("publish did not answer (%s); checking" % e)
            time.sleep(5)
    sys.exit("test %d is uploaded but not open - publish it on its page" % tid)


if __name__ == "__main__":
    main()
