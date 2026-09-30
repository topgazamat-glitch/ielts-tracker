/* The teacher's shell.
 *
 * The rail narrows to its icons and opens again - with its button or the [
 * key - and remembers how it was left. Each section's pages slide open under
 * it: the section you are in always, any other when its arrow is pressed
 * (remembered too). Narrowed, a section's pages come out beside its icon. On a
 * phone the rail is a drawer that slides over the page and goes away once a
 * page is chosen. The line under the current page glides to its new place
 * rather than jumping; nav.js swaps pages without a reload and calls
 * Shell.place() when it has.
 */
(function () {
  var root = document.documentElement;
  if (!document.querySelector(".side")) return;
  var phone = window.matchMedia ? window.matchMedia("(max-width: 860px)") : {matches: false};

  function label() {
    var b = document.getElementById("sidetoggle");
    if (!b) return;
    var narrow = root.classList.contains("rail") && !phone.matches;
    var text = phone.matches ? "Close the menu" : narrow ? "Show the menu" : "Hide the menu";
    b.setAttribute("aria-label", text);
    b.setAttribute("title", text + (phone.matches ? "" : "  ["));
    b.setAttribute("aria-expanded", narrow ? "false" : "true");
    var o = document.getElementById("sideopen");
    if (o) o.setAttribute("aria-expanded", root.classList.contains("drawer") ? "true" : "false");
  }

  function rail(on) {
    root.classList.toggle("rail", on);
    try { localStorage.setItem("side", on ? "rail" : "open"); } catch (e) {}
    label();
  }

  function drawer(open) {
    root.classList.toggle("drawer", open);
    label();
    if (open) {
      var here = document.querySelector(".side-nav a.on") || document.querySelector(".side-nav a");
      if (here) here.focus({preventScroll: true});
    }
  }

  // ---- the two markers
  function move(el, css, animate) {
    if (!animate) el.style.transition = "none";
    for (var k in css) el.style[k] = css[k];
    if (!animate) { void el.offsetWidth; el.style.transition = ""; }
  }

  // ---- a section's pages: open where you are, and wherever you opened them
  function opened() {
    try { return JSON.parse(localStorage.getItem("side.open") || "[]"); } catch (e) { return []; }
  }
  function remember(list) {
    try { localStorage.setItem("side.open", JSON.stringify(list)); } catch (e) {}
  }
  function openGroup(g, open) {
    g.classList.toggle("open", open);
    var b = g.querySelector(".side-more");
    if (b) b.setAttribute("aria-expanded", open ? "true" : "false");
  }
  function syncGroups() {
    var keep = opened();
    Array.prototype.forEach.call(document.querySelectorAll(".side-group[data-sec]"), function (g) {
      var here = !!g.querySelector(".side-row > a.on");
      openGroup(g, here || keep.indexOf(g.getAttribute("data-sec")) >= 0);
    });
  }

  function placeTab(animate) {
    var tabs = document.querySelector(".toptabs");
    var glide = tabs && tabs.querySelector(".tab-glide");
    if (!glide) return;
    var on = tabs.querySelector("a.on");
    if (!on) { glide.style.width = "0"; return; }
    move(glide, {transform: "translateX(" + on.offsetLeft + "px)", width: on.offsetWidth + "px"},
         animate && glide.style.width && glide.style.width !== "0px");
    tabs.classList.add("glides");
    // the current page in view, when the tabs are wider than the bar
    var left = on.offsetLeft - tabs.scrollLeft, right = left + on.offsetWidth;
    if (left < 0 || right > tabs.clientWidth) {
      tabs.scrollTo({left: on.offsetLeft - (tabs.clientWidth - on.offsetWidth) / 2,
                     behavior: animate ? "smooth" : "auto"});
    }
  }

  function place(animate) { syncGroups(); placeTab(animate); }
  window.Shell = {place: place, drawer: drawer};

  document.addEventListener("click", function (e) {
    var t = e.target && e.target.closest ? e.target : null;
    if (!t) return;
    if (t.closest("#sidetoggle")) {
      if (phone.matches) drawer(false); else rail(!root.classList.contains("rail"));
      return;
    }
    if (t.closest("#sideopen")) { drawer(true); return; }
    var more = t.closest(".side-more");
    if (more) {
      var g = more.closest(".side-group"), name = g.getAttribute("data-sec");
      var open = !g.classList.contains("open"), list = opened().filter(function (n) { return n !== name; });
      if (open) list.push(name);
      remember(list);
      openGroup(g, open);
      return;
    }
    if (t.closest("#sidescrim")) { drawer(false); return; }
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && root.classList.contains("drawer")) { drawer(false); return; }
    if (e.key !== "[" || e.metaKey || e.ctrlKey || e.altKey || phone.matches) return;
    var el = e.target;
    if (el && (el.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName))) return;
    rail(!root.classList.contains("rail"));
  });

  // a new page: the drawer has done its job, and the markers glide over
  document.addEventListener("pageswap", function () { drawer(false); });

  var wait = null;
  window.addEventListener("resize", function () {
    clearTimeout(wait);
    wait = setTimeout(function () { place(false); label(); }, 120);
  });
  if (phone.addEventListener) phone.addEventListener("change", function () { drawer(false); label(); });

  function boot() {
    label();
    place(false);
    // only now may things move: the first frame is drawn as it was left
    requestAnimationFrame(function () {
      requestAnimationFrame(function () { root.classList.remove("still"); });
    });
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { place(false); });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
