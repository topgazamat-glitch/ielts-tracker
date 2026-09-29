"""Draw the letters the report pictures need, once, into fonts/card.atlas.

    python3 make_font.py

The pictures sent to Telegram are drawn pixel by pixel (png.py), and the
block capitals there cannot write a name in Russian or an Uzbek oʻ. This asks
Chrome to draw Roboto - the Android font, so the pictures look like the
phones the parents read them on - letter by letter at the few sizes the
pictures use, and keeps how dark each pixel is. The server then only copies
those pixels; it needs no font library and nothing installed.

Run it again only to add a size or a letter. Needs Chrome and the internet
(the font comes from Google Fonts; Roboto is Apache-licensed).
"""
import json
import os
import sys
import tempfile
import time
import zlib

import look

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "fonts", "card.atlas")

# (name, weight, pixel size, only these letters) - the sizes card.py draws
# with. The pictures are 1080 wide and a phone shows them about 390 wide, so
# nothing is smaller than 28: that reads as 10 on the phone.
FIGURES = "0123456789+-–,.%/ "
SIZES = [("r28", 400, 28, None), ("m28", 500, 28, None), ("r32", 400, 32, None),
         ("m32", 500, 32, None), ("b32", 700, 32, None), ("b40", 700, 40, None),
         ("b56", 700, 56, None), ("b88", 700, 88, FIGURES)]

CHARS = ("".join(chr(c) for c in range(32, 127))
         + "".join(chr(c) for c in range(0x00C0, 0x0100))            # é, ö, ü ...
         + "ĞğİıŞşŌōŪū"
         + "".join(chr(c) for c in range(0x0400, 0x0460))            # Russian, Ё, Ў
         + "ҚқҒғҲҳ"                                                  # Uzbek Cyrillic
         + "ʻʼ‘’“”«»–—·•…№↑↓→←✓✗×−°★▲▼")

PAGE = """<!doctype html><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=block">
<body style="font-family:Roboto">%s</body>
<script>
async function atlas(sizes, chars) {
  for (const [_n, w, px, _o] of sizes) await document.fonts.load(w + " " + px + "px Roboto", chars);
  const out = {};
  for (const [name, weight, px, only] of sizes) {
    const c = document.createElement("canvas"), g = c.getContext("2d");
    const pad = Math.ceil(px * 0.6);
    g.font = weight + " " + px + "px Roboto";
    const m = g.measureText("ÁgЙ");
    const asc = Math.ceil(m.fontBoundingBoxAscent), desc = Math.ceil(m.fontBoundingBoxDescent);
    c.width = px * 3 + pad * 2; c.height = asc + desc + pad * 2;
    g.font = weight + " " + px + "px Roboto";
    const glyphs = {};
    for (const ch of (only || chars)) {
      g.clearRect(0, 0, c.width, c.height);
      g.fillStyle = "#000"; g.textBaseline = "alphabetic";
      g.fillText(ch, pad, pad + asc);
      const d = g.getImageData(0, 0, c.width, c.height).data;
      let x0 = c.width, y0 = c.height, x1 = -1, y1 = -1;
      for (let y = 0; y < c.height; y++) for (let x = 0; x < c.width; x++) {
        if (d[(y * c.width + x) * 4 + 3]) {
          if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
        }
      }
      const adv = Math.round(g.measureText(ch).width * 100) / 100;
      if (x1 < 0) { glyphs[ch] = [adv, 0, 0, 0, 0, ""]; continue; }
      const w = x1 - x0 + 1, h = y1 - y0 + 1;
      let s = "";
      for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++)
        s += String.fromCharCode(d[(y * c.width + x) * 4 + 3]);
      glyphs[ch] = [adv, x0 - pad, y0 - pad - asc, w, h, btoa(s)];
    }
    out[name] = {size: px, ascent: asc, descent: desc, glyphs: glyphs};
  }
  // a system font standing in would look nearly right and be wrong
  out.roboto = document.fonts.check("700 20px Roboto") && [...document.fonts].some(
    f => f.family.replace(/"/g, "") === "Roboto" && f.status === "loaded");
  return JSON.stringify(out);
}
</script>"""


def main():
    html = os.path.join(tempfile.mkdtemp(prefix="font-"), "atlas.html")
    open(html, "w", encoding="utf-8").write(PAGE % CHARS.replace("<", "&lt;").replace("&", "&amp;"))
    chrome = look.start_chrome()
    try:
        tab = look.open_page("file://" + html, 800, 600, False, settle=3.0)
        try:
            got = tab.call("Runtime.evaluate", awaitPromise=True, returnByValue=True,
                           expression="atlas(%s, %s)" % (json.dumps(SIZES), json.dumps(CHARS)))
        finally:
            tab.close()
    finally:
        chrome.kill()
    if "exceptionDetails" in got:
        sys.exit("Chrome could not draw the letters: %s" % got["exceptionDetails"])
    data = json.loads(got["result"]["value"])
    if not data.pop("roboto"):
        sys.exit("Roboto did not load - is the internet on? Nothing written.")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    blob = zlib.compress(json.dumps(data, ensure_ascii=False).encode("utf-8"), 9)
    open(OUT, "wb").write(blob)
    print("%s: %d sizes, %d letters each, %d KB" % (OUT, len(data), len(CHARS), len(blob) // 1024))


if __name__ == "__main__":
    main()
