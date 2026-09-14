"""Look at the pages with a real browser, instead of reading the stylesheet
and hoping.

Every design decision in this project was made by reasoning about CSS. That is
how the navigation came to be cut off mid-word on every page at every screen
width for weeks: the stylesheet said `overflow-x: auto`, which is correct, and
the hidden scrollbar meant nobody could use it, which the stylesheet could not
say. This renders the pages in headless Chrome, at honest phone and laptop
sizes, and measures what actually came out.

    python3 look.py                     every page, four widths, report problems
    python3 look.py /championship       save a screenshot of one page
    python3 look.py /championship phone same page at iPhone size

It starts its own server on a throwaway copy of the data, so it never touches
the live site and never runs the Telegram bot. Screenshots land in `shots/`.

Needs Google Chrome installed. Nothing else - the DevTools client below is
about eighty lines of socket and struct, because adding a dependency to a
project that has none would be a worse trade than writing them.
"""
import base64
import json
import os
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
SHOT_DIR = os.path.join(ROOT, "shots")
DEBUG_PORT = 9222
SERVER_PORT = 8097
PASSWORD = "look-at-the-pages"

CHROMES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
]

# The sizes that matter: the laptop the teacher marks on, the smaller laptop a
# school might have, and the phone every student reads the site on.
SIZES = {
    "laptop": (1440, 900, False),
    "small": (1280, 800, False),
    "narrow": (1024, 800, False),
    "phone": (390, 844, True),
}

TEACHER_PAGES = [
    "/", "/queue", "/homework", "/ratings", "/championship", "/assignments",
    "/groups", "/roster", "/materials", "/vocab", "/tests", "/music",
    "/play", "/questions",
]

IPHONE_UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
             "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
             "Mobile/15E148 Safari/604.1")

# Asks the page three questions: is it wider than the window, is anything
# scrolling sideways inside a box that shows no scrollbar, and is any piece of
# text sitting past the right edge where nobody will ever read it.
# Asks the page three questions: is the page itself wider than the window, is
# anything cut off inside a box you cannot scroll, and is any piece of text
# sitting past the right edge with no way to reach it. A strip that scrolls
# sideways on purpose - the navigation on a phone - is not a fault, so the
# test is never "does it stick out" but "can a person get to it".
MEASURE = """(() => {
  const out = {w: innerWidth, sw: document.documentElement.scrollWidth,
               clipped: [], past: []};
  const scrolls = el => {
    const o = getComputedStyle(el).overflowX;
    return (o === 'auto' || o === 'scroll') && el.scrollWidth > el.clientWidth;
  };
  const reachable = el => {
    for (let p = el.parentElement; p && p !== document.body; p = p.parentElement)
      if (scrolls(p)) return true;
    return false;
  };
  document.querySelectorAll('header.top, header.top nav, main, .tabs, table, .card')
    .forEach(el => {
      if (el.scrollWidth - el.clientWidth > 2 && !scrolls(el))
        out.clipped.push(name(el) + ' shows ' + el.clientWidth
                         + 'px of ' + el.scrollWidth + 'px');
    });
  document.querySelectorAll('body *').forEach(el => {
    if (el.children.length) return;
    const r = el.getBoundingClientRect();
    if (r.width > 0 && r.right > innerWidth + 1 && !reachable(el))
      out.past.push(name(el) + ' ends at ' + Math.round(r.right) + 'px');
  });
  function name(el) {
    const c = (el.className && el.className.baseVal === undefined)
      ? String(el.className).trim().split(/\\s+/)[0] : '';
    const t = (el.textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 24);
    return el.tagName.toLowerCase() + (c ? '.' + c : '')
           + (t ? ' "' + t + '"' : '');
  }
  out.past = out.past.slice(0, 8);
  return JSON.stringify(out);
})()"""


# ------------------------------------------------------- devtools over a socket

class Tab:
    """One Chrome tab, spoken to over a WebSocket we frame by hand."""

    def __init__(self, url):
        req = urllib.request.Request(
            f"http://127.0.0.1:{DEBUG_PORT}/json/new?{urllib.parse.quote(url)}",
            method="PUT")
        self.info = json.loads(urllib.request.urlopen(req, timeout=10).read())
        ws = self.info["webSocketDebuggerUrl"]
        hostport, path = ws.split("://", 1)[1].split("/", 1)
        host, port = hostport.split(":")
        self.sock = socket.create_connection((host, int(port)), timeout=30)
        key = base64.b64encode(os.urandom(16)).decode()
        self.sock.sendall((
            f"GET /{path} HTTP/1.1\r\nHost: {hostport}\r\n"
            f"Upgrade: websocket\r\nConnection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
        ).encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            buf += self.sock.recv(4096)
        self.buf = buf.split(b"\r\n\r\n", 1)[1]
        self.seq = 0

    def _take(self, n):
        while len(self.buf) < n:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise EOFError("Chrome closed the connection")
            self.buf += chunk
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def call(self, method, **params):
        self.seq += 1
        body = json.dumps({"id": self.seq, "method": method,
                           "params": params}).encode()
        mask = os.urandom(4)
        head = b"\x81"
        if len(body) < 126:
            head += bytes([0x80 | len(body)])
        elif len(body) < 65536:
            head += b"\xfe" + struct.pack(">H", len(body))
        else:
            head += b"\xff" + struct.pack(">Q", len(body))
        self.sock.sendall(head + mask
                          + bytes(b ^ mask[i % 4] for i, b in enumerate(body)))
        while True:
            _flags, second = self._take(2)
            length = second & 0x7F
            if length == 126:
                length = struct.unpack(">H", self._take(2))[0]
            elif length == 127:
                length = struct.unpack(">Q", self._take(8))[0]
            msg = json.loads(self._take(length))
            if msg.get("id") != self.seq:
                continue                      # an event; we only want answers
            if "error" in msg:
                raise RuntimeError(f"{method}: {msg['error']}")
            return msg.get("result", {})

    def close(self):
        try:
            urllib.request.urlopen(
                f"http://127.0.0.1:{DEBUG_PORT}/json/close/{self.info['id']}",
                timeout=5).read()
        except Exception:
            pass
        self.sock.close()


def open_page(url, width, height, mobile, cookie="", settle=1.4):
    tab = Tab("about:blank")
    tab.call("Emulation.setDeviceMetricsOverride", width=width, height=height,
             deviceScaleFactor=2, mobile=mobile,
             screenWidth=width, screenHeight=height)
    if mobile:
        tab.call("Emulation.setTouchEmulationEnabled", enabled=True,
                 maxTouchPoints=5)
        tab.call("Emulation.setUserAgentOverride", userAgent=IPHONE_UA)
    if cookie:
        tab.call("Network.setCookie", name="ta_session", value=cookie,
                 domain="localhost", path="/")
    tab.call("Page.enable")
    tab.call("Page.navigate", url=url)
    time.sleep(settle)
    return tab


def start_chrome():
    binary = next((c for c in CHROMES if os.path.exists(c)), None)
    if not binary:
        sys.exit("Google Chrome not found - install it, or add its path to "
                 "CHROMES at the top of look.py.")
    proc = subprocess.Popen(
        [binary, "--headless=new", "--disable-gpu", "--no-first-run",
         "--no-default-browser-check", "--disable-extensions",
         "--disable-background-networking", "--disable-sync",
         f"--remote-debugging-port={DEBUG_PORT}",
         f"--user-data-dir={tempfile.mkdtemp(prefix='look-chrome-')}",
         "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        try:
            urllib.request.urlopen(
                f"http://127.0.0.1:{DEBUG_PORT}/json/version", timeout=1).read()
            return proc
        except Exception:
            time.sleep(0.5)
    proc.kill()
    sys.exit("Chrome started but never answered on its debugging port.")


# ------------------------------------------------- a server of our very own

def start_server():
    """A copy of the data, a password we know, and no Telegram token.

    Two pollers make the bot answer every student twice, so this must never
    be the real thing - it is a throwaway directory that gets deleted after.
    """
    work = tempfile.mkdtemp(prefix="look-data-")
    live = os.environ.get("DATA_DIR") or os.path.join(ROOT, "data")
    for name in ("app.db",):
        src = os.path.join(live, name)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(work, name))
    for name in ("uploads", "materials", "music"):
        src = os.path.join(live, name)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(work, name))
    config = {}
    real = os.path.join(ROOT, "config.json")
    if os.path.exists(real):
        config = json.load(open(real))
    config.pop("telegram_token", None)
    config["teacher_password"] = PASSWORD
    config["port"] = SERVER_PORT
    config["automation"] = False
    json.dump(config, open(os.path.join(work, "config.json"), "w"), indent=2)

    env = dict(os.environ, DATA_DIR=work)
    env.pop("TELEGRAM_TOKEN", None)
    proc = subprocess.Popen([sys.executable, os.path.join(ROOT, "server.py")],
                            env=env, stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE)
    base = f"http://localhost:{SERVER_PORT}"
    for _ in range(60):
        try:
            urllib.request.urlopen(base + "/login", timeout=1).read()
            return proc, work, base
        except Exception:
            time.sleep(0.5)
    proc.kill()
    sys.exit("The site did not start. Try `python3 server.py` to see why.")


def sign_in(base):
    import http.cookiejar
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(jar))
    opener.open(base + "/login",
                urllib.parse.urlencode({"password": PASSWORD}).encode())
    for c in jar:
        if c.name == "ta_session":
            return c.value
    sys.exit("Could not sign in to the throwaway copy.")


def a_student(work):
    """A portal link, so the students' own page gets looked at too."""
    import sqlite3
    db = sqlite3.connect(os.path.join(work, "app.db"))
    try:
        row = db.execute("SELECT token FROM students "
                         "WHERE token IS NOT NULL AND active=1 "
                         "ORDER BY id LIMIT 1").fetchone()
    except sqlite3.Error:
        return None
    finally:
        db.close()
    return row[0] if row else None


# ------------------------------------------------------------------ commands

def check():
    server, work, base = start_server()
    chrome = start_chrome()
    trouble = 0
    try:
        cookie = sign_in(base)
        pages = list(TEACHER_PAGES)
        token = a_student(work)
        if token:
            pages += [f"/s/{token}?tab={t}" for t in
                      ("home", "write", "progress", "class", "profile")]
        for size, (w, h, mobile) in SIZES.items():
            print(f"\n{size}  {w}x{h}")
            clean = True
            for path in pages:
                tab = open_page(base + path, w, h, mobile, cookie)
                try:
                    found = json.loads(tab.call(
                        "Runtime.evaluate", expression=MEASURE,
                        returnByValue=True)["result"]["value"])
                finally:
                    tab.close()
                notes = []
                if found["sw"] > found["w"] + 1:
                    notes.append(f"page is {found['sw']}px wide in a "
                                 f"{found['w']}px window - it scrolls sideways")
                notes += [f"cut off: {c}" for c in found["clipped"]]
                notes += [f"past the edge: {p}" for p in found["past"]]
                if notes:
                    clean = False
                    trouble += len(notes)
                    label = path if len(path) < 40 else path[:37] + "..."
                    print(f"  {label}")
                    for n in notes:
                        print(f"      {n}")
            if clean:
                print("  nothing cut off, nothing past the edge")
    finally:
        chrome.kill()
        server.kill()
        shutil.rmtree(work, ignore_errors=True)
    print()
    if trouble:
        print(f"{trouble} thing(s) to look at. A screenshot of any page:")
        print("    python3 look.py /championship phone")
        return 1
    print("Every page fits, at every size.")
    return 0


def shot(path, size):
    if size not in SIZES:
        sys.exit(f"Sizes are: {', '.join(SIZES)}")
    w, h, mobile = SIZES[size]
    server, work, base = start_server()
    chrome = start_chrome()
    try:
        cookie = sign_in(base)
        os.makedirs(SHOT_DIR, exist_ok=True)
        name = (path.strip("/").replace("/", "-").replace("?", "-")
                or "overview")
        out = os.path.join(SHOT_DIR, f"{name}-{size}.png")
        tab = open_page(base + path, w, h, mobile, cookie, settle=2.2)
        try:
            data = tab.call("Page.captureScreenshot", format="png",
                            captureBeyondViewport=True)["data"]
        finally:
            tab.close()
        open(out, "wb").write(base64.b64decode(data))
        print(out)
    finally:
        chrome.kill()
        server.kill()
        shutil.rmtree(work, ignore_errors=True)
    return 0


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("check", "-h", "--help"):
        if args and args[0] in ("-h", "--help"):
            print(__doc__)
            return 0
        return check()
    path = args[0] if args[0].startswith("/") else "/" + args[0]
    size = args[1] if len(args) > 1 else "laptop"
    return shot(path, size)


if __name__ == "__main__":
    sys.exit(main())
