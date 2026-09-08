/* Make the student page behave like a Telegram app when it is opened inside one.
 *
 * Telegram hands the page a small api: it tells us the app is ready, how tall
 * the sheet is, and what colours the person's Telegram is using. Without this
 * the page opens as a short scrollable panel in the wrong colours, which is
 * what a web page in a box looks like. With it, it is an app.
 *
 * Everything here is guarded: opened in an ordinary browser, window.Telegram
 * is absent and the page is left exactly as it was.
 */
(function () {
  var tg = window.Telegram && window.Telegram.WebApp;
  if (!tg || !tg.initData && !tg.platform) return;

  document.documentElement.classList.add("in-telegram");

  try { tg.ready(); } catch (e) {}
  try { tg.expand(); } catch (e) {}                 // full height, not a peek
  try { tg.disableVerticalSwipes(); } catch (e) {}  // so scrolling never closes it

  // follow the colours the student already chose in Telegram
  function paint() {
    var p = (tg.themeParams || {});
    var root = document.documentElement;
    if (p.bg_color) { root.style.setProperty("--bg", p.bg_color); }
    if (p.secondary_bg_color) { root.style.setProperty("--surface", p.secondary_bg_color); }
    if (p.text_color) { root.style.setProperty("--ink", p.text_color); }
    if (p.hint_color) { root.style.setProperty("--ink-3", p.hint_color); }
    if (p.link_color) { root.style.setProperty("--brand", p.link_color); }
    if (tg.colorScheme) { root.setAttribute("data-theme", tg.colorScheme); }
  }
  paint();
  try { tg.onEvent("themeChanged", paint); } catch (e) {}

  // Telegram draws its own back arrow; wire it to the page's own history
  function back() {
    try {
      if (window.history.length > 1) { window.history.back(); }
      else { tg.close(); }
    } catch (e) {}
  }
  try {
    tg.BackButton.onClick(back);
    tg.BackButton.show();
  } catch (e) {}

  // a tap ought to feel like a tap
  document.addEventListener("click", function (e) {
    var el = e.target;
    while (el && el.nodeName !== "A" && el.nodeName !== "BUTTON") { el = el.parentNode; }
    if (!el) return;
    try { tg.HapticFeedback.impactOccurred("light"); } catch (err) {}
  });
})();
