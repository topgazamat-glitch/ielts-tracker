"""Mobile — the things that break a site on a phone.

Run me with:  python3 run_tests.py mobile
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

css = open(os.path.join(ROOT, "static", "style.css"), encoding="utf-8").read()
srv = open(os.path.join(ROOT, "server.py"), encoding="utf-8").read()

print("1. THE PAGE FITS THE SCREEN AT ALL")
shells = len(re.findall(r'name="viewport"[^>]*width=device-width', srv))
print("   page shells declaring the viewport:", shells)
assert shells >= 2, "both the teacher and the student shell need it"

print("\n2. WIDE THINGS SCROLL INSTEAD OF PUSHING THE PAGE SIDEWAYS")
for sel in (".tablewrap", ".cert-wrap", ".gcshots"):
    block = re.search(re.escape(sel) + r"\s*\{[^}]*\}", css)
    ok = block and "overflow-x: auto" in block.group(0)
    print("   %-12s scrolls on its own: %s" % (sel, bool(ok)))
    assert ok, sel + " must scroll rather than widen the page"
nav = re.search(r"header\.top nav\s*\{[^}]*\}", css)
print("   the nav scrolls too:", bool(nav and "overflow-x" in nav.group(0)))

print("\n3. A FINGER CAN HIT WHAT IT AIMS AT")
coarse = re.search(r"@media \(pointer: coarse\)\s*\{(.*?)\n\}", css, re.S)
assert coarse, "there should be a block for touch devices"
body = coarse.group(1)
for sel in ("button.mk", ".scorepad button", ".chip", ".tabs .tab"):
    print("   %-20s gets a bigger target: %s" % (sel, sel in body))
    assert sel in body
print("   the target size used:", re.search(r"min-height:\s*(\d+px)", body).group(1))
assert int(re.search(r"min-height:\s*(\d+)px", body).group(1)) >= 44

print("\n4. TYPING DOES NOT ZOOM THE PAGE ON AN IPHONE")
print("   inputs are raised to:", re.search(
    r"input, select, textarea,[^}]*?font-size:\s*(\d+)px", body).group(1) + "px")
assert int(re.search(r"input, select, textarea,[^}]*?font-size:\s*(\d+)px",
                     body).group(1)) >= 16

print("\n5. NOTHING IS PINNED WIDER THAN A PHONE OUTSIDE A SCROLLER")
# the certificate is deliberately 600px wide and lives inside .cert-wrap,
# which scrolls; anything else that wide would push the whole page sideways
wide = []
for m in re.finditer(r"([^{}]+)\{([^}]*)\}", css):
    whole = m.group(0)
    for w in re.findall(r"(?:^|[^-])min-width:\s*(\d{3,})px", m.group(2)):
        if int(w) > 360 and ".cert" not in whole:
            wide.append((" ".join(m.group(1).split())[:40], w))
print("   deliberately wide, inside a scroller: .cert (600px)")
print("   anything else wider than a phone:", wide or "none")
assert not wide

print("\nIt should behave on a phone.")
