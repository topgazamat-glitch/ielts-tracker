/* Swap the page instead of reloading it, so the music keeps playing.
 *
 * Every click used to tear the document down, and with it the <audio> element,
 * so the song stopped and restarted on every button - which is what sounded
 * like glitching. Fetching the next page and replacing <main> leaves the
 * header, the music button and the player itself untouched.
 *
 * The rule that keeps this safe: if the page being opened carries a script of
 * its own, this hands over to a normal navigation. Re-running an inline script
 * in a document that already ran one would redeclare its globals and break the
 * page - the live game boards are full of them. Anything unexpected at all
 * falls back the same way, so the worst case is exactly the old behaviour.
 */
(function () {
  if (!window.fetch || !window.history || !window.DOMParser) return;
  if (!document.querySelector("main")) return;

  var busy = 0;

  function full(href) { window.location.href = href; }

  function skip(url, a) {
    if (url.origin !== window.location.origin) return true;
    if (a && (a.target || a.hasAttribute("download"))) return true;
    if (a && a.getAttribute("href").charAt(0) === "#") return true;
    var p = url.pathname;
    return p.indexOf("/static/") === 0 || p.indexOf("/song") === 0 ||
           p.indexOf("/media/") === 0 || p.indexOf("/logout") === 0 ||
           /\/(file|photo|export|\.csv)$/.test(p) || /\.[a-z0-9]{2,4}$/i.test(p);
  }

  function bar(show) {
    var el = document.getElementById("navbar");
    if (!el) {
      el = document.createElement("div");
      el.id = "navbar";
      document.body.appendChild(el);
    }
    el.className = show ? "on" : "";
  }

  function go(href, push) {
    var mine = ++busy;
    bar(true);
    fetch(href, {credentials: "same-origin"})
      .then(function (r) {
        var type = r.headers.get("Content-Type") || "";
        if (!r.ok || type.indexOf("text/html") < 0) throw new Error("not a page");
        if (r.redirected && r.url !== href) throw new Error("redirected");
        return r.text();
      })
      .then(function (html) {
        if (mine !== busy) return;                 // a newer click won
        var doc = new DOMParser().parseFromString(html, "text/html");
        var fresh = doc.querySelector("main");
        if (!fresh) throw new Error("no main");
        // the one thing this must never do: run someone else's script twice
        if (fresh.querySelector("script")) throw new Error("page has its own script");

        var here = document.querySelector("main");
        here.parentNode.replaceChild(fresh, here);

        swapHeader(doc);
        if (doc.title) { document.title = doc.title; }

        if (push) { window.history.pushState({nav: 1}, "", href); }
        window.scrollTo(0, 0);
        bar(false);
        document.dispatchEvent(new CustomEvent("pageswap"));
      })
      .catch(function () { if (mine === busy) { full(href); } });
  }

  // The teacher's header is two rows: the sections, and the pages of the
  // current section. Both change from page to page, and the second row may
  // appear or vanish, so each is brought over from the new document. The
  // music button and the sign-out link live between them and are left alone.
  function swapHeader(doc) {
    var oldTop = document.querySelector("header.top");
    var newTop = doc.querySelector("header.top");
    var oldSec = oldTop && oldTop.querySelector("nav.sections");
    if (!oldSec) {
      var oldNav = document.querySelector("header nav");
      var newNav = doc.querySelector("header nav");
      if (oldNav && newNav) { oldNav.innerHTML = newNav.innerHTML; }
      return;
    }
    if (!newTop) return;
    var newSec = newTop.querySelector("nav.sections");
    if (newSec) { oldSec.innerHTML = newSec.innerHTML; }
    var oldBand = oldTop.querySelector(".pagesband");
    var newBand = newTop.querySelector(".pagesband");
    if (oldBand && newBand) { oldBand.innerHTML = newBand.innerHTML; }
    else if (oldBand) { oldBand.parentNode.removeChild(oldBand); }
    else if (newBand) { oldTop.appendChild(newBand); }
    var oldSet = oldTop.querySelector('.right a[href="/settings"]');
    var newSet = newTop.querySelector('.right a[href="/settings"]');
    if (oldSet && newSet) { oldSet.className = newSet.className; }
  }

  document.addEventListener("click", function (e) {
    if (e.defaultPrevented || e.button !== 0) return;
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    var a = e.target;
    while (a && a.nodeName !== "A") { a = a.parentNode; }
    if (!a || !a.getAttribute("href")) return;
    var url;
    try { url = new URL(a.href, window.location.href); } catch (err) { return; }
    if (skip(url, a)) return;
    if (url.href === window.location.href) return;
    e.preventDefault();
    go(url.href, true);
  });

  window.addEventListener("popstate", function (e) {
    if (e.state && e.state.nav) { go(window.location.href, false); }
  });
})();


/* On a phone there is no hover, so the arrow beside a section opens its
 * menu on a tap instead of leaving the page. The menu is pinned just under
 * the header, outside the strip that scrolls sideways, or the strip would
 * clip it. A second tap on the same section, or a tap anywhere else, closes
 * it. Registered on the capture phase so it runs before the page-swapping
 * handler above, which honours preventDefault.
 */
(function () {
  if (window.matchMedia && window.matchMedia("(hover: hover)").matches) return;
  if (!document.querySelector("nav.sections")) return;
  var open = null;
  function close() { if (open) { open.classList.remove("open"); open = null; } }
  document.addEventListener("click", function (e) {
    var t = e.target;
    if (!t || !t.closest) return;
    var a = t.closest("nav.sections a.has-menu");
    if (a) {
      e.preventDefault();
      var sec = a.parentNode;
      if (sec === open) { close(); return; }
      close();
      var head = document.querySelector("header.top");
      var menu = sec.querySelector(".menu");
      if (head && menu) {
        menu.style.top = Math.round(head.getBoundingClientRect().bottom) + "px";
      }
      sec.classList.add("open");
      open = sec;
      return;
    }
    if (!t.closest("nav.sections .menu")) close();
  }, true);
  document.addEventListener("pageswap", function () { open = null; });
})();
