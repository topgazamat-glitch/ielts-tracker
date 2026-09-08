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

        var oldNav = document.querySelector("header nav");
        var newNav = doc.querySelector("header nav");
        if (oldNav && newNav) { oldNav.innerHTML = newNav.innerHTML; }
        if (doc.title) { document.title = doc.title; }

        if (push) { window.history.pushState({nav: 1}, "", href); }
        window.scrollTo(0, 0);
        bar(false);
        document.dispatchEvent(new CustomEvent("pageswap"));
      })
      .catch(function () { if (mine === busy) { full(href); } });
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
