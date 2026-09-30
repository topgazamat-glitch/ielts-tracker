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
        swapDocument(html, href, push);
        bar(false);
      })
      .catch(function () { if (mine === busy) { full(href); } });
  }

  // Put a fetched page in place of this one: its <main>, its header rows,
  // its title, its address. Throws if the page carries a script of its own,
  // and the caller then falls back to a real navigation.
  function swapDocument(html, href, push) {
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
    document.dispatchEvent(new CustomEvent("pageswap"));
  }

  // other scripts - the marking form - swap pages the same way
  window.Nav = {go: go, swap: swapDocument, bar: bar};

  // The students' pages have a header of their own, whose sections are
  // brought over as they are; the teacher's shell is handled below.
  function swapHeader(doc) {
    if (document.querySelector(".side")) { swapShell(doc); return; }
    var oldNav = document.querySelector("header nav");
    var newNav = doc.querySelector("header nav");
    if (oldNav && newNav) { oldNav.innerHTML = newNav.innerHTML; }
  }

  // The teacher's shell: the rail says which section is lit, the bar over
  // the work says which page. Inside one section only the lit page changes,
  // and its line glides across; another section brings its own name and
  // pages, which fade in. The rail itself is never replaced, so it does not
  // flicker, and whatever the music button is doing carries on.
  // the same links in the same order on every page, so the n-th here takes
  // the n-th there's state (a section and its first page share an address)
  function light(links, from) {
    Array.prototype.forEach.call(links, function (a, i) {
      var on = !!(from[i] && from[i].classList.contains("on"));
      a.classList.toggle("on", on);
      if (on && a.closest(".toptabs, .side-sub")) { a.setAttribute("aria-current", "page"); }
      else { a.removeAttribute("aria-current"); }
    });
  }

  function swapShell(doc) {
    light(document.querySelectorAll(".side a[href]"), doc.querySelectorAll(".side a[href]"));
    var here = document.querySelector(".topbar-in"), there = doc.querySelector(".topbar-in");
    var same = false;
    if (here && there) {
      var title = here.querySelector(".topbar-title"), newTitle = there.querySelector(".topbar-title");
      var tabs = here.querySelector(".toptabs"), newTabs = there.querySelector(".toptabs");
      same = !!(title && newTitle && title.textContent === newTitle.textContent && !!tabs === !!newTabs);
      if (same && tabs) {
        light(tabs.querySelectorAll("a[href]"), newTabs.querySelectorAll("a[href]"));
      } else if (!same) {
        if (title && newTitle) { title.textContent = newTitle.textContent; }
        if (tabs) { tabs.parentNode.removeChild(tabs); }
        if (newTabs) { here.appendChild(document.importNode(newTabs, true)); }
        here.classList.remove("fresh");
        void here.offsetWidth;
        here.classList.add("fresh");
      }
    }
    if (window.Shell) { window.Shell.place(true); }
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
