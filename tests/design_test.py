"""Design — the stylesheet stays a system rather than a pile of patches.

Run me with:  python3 run_tests.py design
"""
import collections
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

css = open(os.path.join(ROOT, "static", "style.css"), encoding="utf-8").read()
srv = open(os.path.join(ROOT, "server.py"), encoding="utf-8").read()

print("1. EVERY TOKEN RESOLVES")
used = set(re.findall(r"var\(--([a-z0-9-]+)\)", css))
defined = set(re.findall(r"--([a-z0-9-]+)\s*:", css))
missing = sorted(used - defined)
print("   %d used, %d defined, missing: %s" % (len(used), len(defined), missing or "none"))
assert not missing

print("\n2. SPACING COMES FROM THE SCALE")
# The booklet block is exempt on purpose: it reproduces a printed handout, and
# its measurements are Word's, in the document's own units. Forcing them onto
# the site's spacing scale would move the boxes off the page they came from.
site_css = css.split("/* ------------------------------------------------------------- the booklet")[0]
raw = [int(x) for x in re.findall(
    r"\b(?:margin|padding|gap)[a-z-]*:\s*[^;{}]*?(\d+)px", site_css)]
stray = sorted(n for n in set(raw) if n and n <= 60)
print("   raw spacing values between 1 and 60px:", stray or "none")
assert not stray, "spacing should use --sp-*, not bare pixels"

print("\n3. THE TYPE SCALE IS SMALL")
sizes = sorted(set(float(x) for x in re.findall(r"font-size:\s*([0-9.]+)px", site_css)))
print("   sizes in use:", ", ".join("%g" % s for s in sizes))
assert len(sizes) <= 12, "a type scale should be a handful of sizes, not a spectrum"
assert not [s for s in sizes if s != int(s)], "no half pixels"

print("\n4. THE MARKUP IS NOT FULL OF PATCHES")
inline = re.findall(r'style="([^"]*)"', srv)
counts = collections.Counter(inline)
print("   inline styles left: %d" % len(inline))
worst = counts.most_common(3)
for what, n in worst:
    print("      %2dx  %s" % (n, what[:56]))
assert len(inline) < 100, "design decisions belong in the stylesheet"
assert 'margin:0' not in counts, "a card already gives its own padding"

print("\n5. COLOURS COME FROM THE PALETTE")
# entity codes like &#129351; are medals, not colours
hexes = set(re.findall(r"[^&]#([0-9a-fA-F]{6})\b", srv))
named = set(re.findall(r'"#([0-9a-fA-F]{6})"', srv.split("FOIL = ")[1].split("}")[0]))
loose = sorted(hexes - named)
print("   named once as the certificate foil:", sorted(named))
print("   loose colour literals in the markup:", loose or "none")
assert not loose, "a colour in the markup belongs in the palette or a named constant"

print("\nThe stylesheet is a system.")
