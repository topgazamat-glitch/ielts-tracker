/* A handout, done on a phone.
 *
 * What the student types or taps is saved as they go; "Check" marks it
 * straight away; the boxes that hold a sentence grow as it is written; a
 * chip is a choice, a tick is a tick; Enter moves to the next gap; the bar at
 * the bottom says how much is done, jumps to the next empty box, and goes to
 * any exercise. In a file rather than inline, so the page can be swapped in
 * without a reload like every other page.
 */
(function () {
  var timer = null, dirty = false;

  function data() { return document.getElementById("handoutdata"); }
  function sheet() { return document.querySelector(".booksheet.handout"); }
  function note(t) { var el = document.getElementById("savenote"); if (el) el.textContent = t; }

  function fields() {
    var s = sheet();
    return s ? Array.prototype.slice.call(s.querySelectorAll('[name^="q"]')) : [];
  }

  function body() {
    var b = new URLSearchParams();
    fields().forEach(function (el) {
      if (el.type === "radio" || el.type === "checkbox") {
        if (el.checked) b.append(el.name, el.value);
      } else b.append(el.name, el.value);
    });
    return b;
  }

  // ---- saving
  function push() {
    var d = data();
    if (!dirty || !d) return;
    dirty = false;
    note("Saving…");
    fetch(d.getAttribute("data-save"), {method: "POST", body: body(),
      credentials: "same-origin",
      headers: {"Content-Type": "application/x-www-form-urlencoded"}})
      .then(function () { note("Saved"); })
      .catch(function () { note("Not saved — you are offline"); dirty = true; });
  }
  function changed() {
    dirty = true;
    note("Saving…");
    clearTimeout(timer);
    timer = setTimeout(push, 900);
    progress();
  }

  // ---- how much is done: every question once, ticks left out
  function groups() {
    var seen = {}, out = [];
    fields().forEach(function (el) {
      if (seen[el.name]) return;
      seen[el.name] = true;
      if (el.type === "hidden") return;                 // a tick is optional
      if (el.hasAttribute("data-optional")) return;     // so is "correct it if it is false"
      out.push(el.name);
    });
    return out;
  }
  function answered(name) {
    var s = sheet();
    var els = s.querySelectorAll('[name="' + name + '"]');
    for (var i = 0; i < els.length; i++) {
      var el = els[i];
      if (el.type === "radio") { if (el.checked) return true; }
      else if ((el.value || "").trim()) {
        // a sentence of your own needs a few words to be an answer, not "x"
        var least = parseInt(el.getAttribute("data-min-words") || "0", 10);
        if (!least || el.value.trim().split(/\s+/).length >= least) return true;
      }
    }
    return false;
  }
  function progress() {
    var s = sheet();
    if (!s) return;
    var all = groups(), done = 0;
    all.forEach(function (n) { if (answered(n)) done++; });
    var c = document.getElementById("sbcount");
    if (c) c.textContent = done + " of " + all.length;
    var f = document.getElementById("sbfill");
    if (f) f.style.width = (all.length ? Math.round(100 * done / all.length) : 0) + "%";
  }
  function target(name) {
    var s = sheet(), el = s.querySelector('[name="' + name + '"]');
    if (!el) return null;
    return el.type === "radio" ? el.closest(".bk-chips") || el : el;
  }
  function nextEmpty() {
    var s = sheet();
    if (!s) return;
    var names = groups().filter(function (n) { return !answered(n); });
    if (!names.length) { note("Everything is filled in — press Check"); return; }
    // the first empty box below what is on screen now, else the first of all
    var top = window.scrollY + 80, pick = null;
    names.some(function (n) {
      var t = target(n);
      if (t && t.getBoundingClientRect().top + window.scrollY > top) { pick = t; return true; }
      return false;
    });
    pick = pick || target(names[0]);
    if (!pick) return;
    pick.scrollIntoView({block: "center", behavior: "smooth"});
    if (pick.tagName === "INPUT" || pick.tagName === "TEXTAREA") {
      setTimeout(function () { pick.focus({preventScroll: true}); }, 350);
    }
  }

  // ---- a sentence box grows with what is written
  function grow(el) {
    if (!el || el.tagName !== "TEXTAREA") return;
    el.style.height = "auto";
    el.style.height = el.scrollHeight + 2 + "px";
    count(el);
  }
  // ---- a piece of writing says how long it is, so "60-80 words" can be kept to
  function count(el) {
    if (!el.classList.contains("bk-essay")) return;
    var out = el.nextElementSibling;
    if (!out || !out.classList.contains("bk-words")) return;
    var n = (el.value.match(/[A-Za-z0-9\u00C0-\u024F'’-]+/g) || []).length;
    out.textContent = n === 1 ? "1 word" : n + " words";
  }

  // ---- marks from the check
  function clearMark(el) {
    var box = el.closest(".bk-chips") || el;
    box.classList.remove("right", "wrong", "teacher");
    var tick = el.type === "hidden" ? el.previousElementSibling : null;
    if (tick) tick.classList.remove("right", "wrong", "teacher");
    var after = (el.type === "hidden" ? el : box).nextElementSibling;
    if (after && after.classList.contains("bk-answer")) after.remove();
  }
  // ---- a handout in parts: a part is checked once, when it is complete,
  // and then locks; the second tap is the confirmation, not a dialog
  var armed = null;
  function checkPart(d, part) {
    var mk = document.getElementById("marknote");
    var btn = document.getElementById("checkbtn");
    var left = groups().filter(function (n) { return !answered(n); });
    if (left.length) {
      var short = left.some(function (n) {
        var el = sheet().querySelector('[name="' + n + '"][data-min-words]');
        return el && (el.value || "").trim();
      });
      if (mk) mk.textContent = (left.length === 1 ? "1 box is" : left.length + " boxes are") +
        " still empty" + (short ? " or too short — write at least three words" : "") +
        ". Answer every box in this part first.";
      nextEmpty();
      return;
    }
    if (btn && !btn.classList.contains("armed")) {
      btn.classList.add("armed");
      btn.textContent = "Sure? Answers lock";
      if (mk) mk.textContent = "Tap again to check. After that the answers in this part can't be changed.";
      clearTimeout(armed);
      armed = setTimeout(function () {
        btn.classList.remove("armed");
        btn.textContent = btn.getAttribute("data-label") || "Check";
      }, 5000);
      return;
    }
    clearTimeout(armed);
    if (btn) { btn.disabled = true; btn.textContent = "Checking…"; }
    var b = body();
    b.append("part", part);
    fetch(d.getAttribute("data-check"), {method: "POST", body: b,
      credentials: "same-origin",
      headers: {"Content-Type": "application/x-www-form-urlencoded"}})
      .then(function (r) { return r.json(); })
      .then(function (out) {
        if (out.ok && out.go) {
          dirty = false;
          if (window.Nav && window.Nav.go) window.Nav.go(out.go, true);
          else window.location.href = out.go;
          return;
        }
        if (btn) { btn.disabled = false; btn.classList.remove("armed");
                   btn.textContent = btn.getAttribute("data-label") || "Check"; }
        if (out.missing && out.missing.length) {
          if (mk) mk.textContent = "Some boxes are still empty.";
          var first = sheet().querySelector('[data-q="' + out.missing[0] + '"]');
          if (first) first.scrollIntoView({block: "center", behavior: "smooth"});
        } else if (out.locked && mk) {
          mk.textContent = "Finish the booklet before this one first.";
        } else if (mk) mk.textContent = "Could not check just now. Try again in a moment.";
      })
      .catch(function () {
        if (btn) { btn.disabled = false; btn.classList.remove("armed");
                   btn.textContent = btn.getAttribute("data-label") || "Check"; }
        if (mk) mk.textContent = "Could not check just now — are you online?";
      });
  }

  function check() {
    var d = data();
    if (!d) return;
    if (d.getAttribute("data-part")) { checkPart(d, d.getAttribute("data-part")); return; }
    var mk = document.getElementById("marknote");
    if (mk) mk.textContent = "Checking…";
    fetch(d.getAttribute("data-check"), {method: "POST", body: body(),
      credentials: "same-origin",
      headers: {"Content-Type": "application/x-www-form-urlencoded"}})
      .then(function (r) { return r.json(); })
      .then(function (out) {
        if (!out.ok) throw new Error("no");
        var first = null, seen = {};
        fields().forEach(function (el) {
          if (seen[el.name]) return;
          seen[el.name] = true;
          clearMark(el);
          var m = out.marks[el.name.slice(1)];
          if (!m) return;
          var box = el.type === "radio" ? el.closest(".bk-chips")
                  : el.type === "hidden" ? el.previousElementSibling : el;
          if (!box) return;
          box.classList.add(m.state);
          if (m.state === "wrong") {
            first = first || box;
            var tag = document.createElement("button");
            tag.type = "button";
            tag.className = "bk-answer";
            tag.textContent = "answer";
            tag.onclick = function () { tag.textContent = m.answer; tag.disabled = true; };
            (el.type === "hidden" ? el : box).insertAdjacentElement("afterend", tag);
          }
        });
        var bits = [out.right + " right"];
        if (out.wrong) bits.push(out.wrong + " to look at again");
        if (out.blank) bits.push(out.blank + " still empty");
        if (out.teacher) bits.push(out.teacher + " for your teacher");
        if (mk) mk.textContent = bits.join(" · ");
        if (first) first.scrollIntoView({block: "center", behavior: "smooth"});
      })
      .catch(function () { if (mk) mk.textContent = "Could not check just now."; });
  }

  // ---- one set of listeners for the whole document
  document.addEventListener("input", function (e) {
    var el = e.target;
    if (!el.closest || !el.closest(".booksheet.handout")) return;
    clearMark(el);
    grow(el);
    changed();
  });
  document.addEventListener("change", function (e) {
    var el = e.target;
    if (el.type === "radio" && el.closest && el.closest(".booksheet.handout")) {
      clearMark(el);
      changed();
    }
    if (el.id === "bkjump" && el.value) {
      var to = document.getElementById(el.value);
      if (to) to.scrollIntoView({block: "start", behavior: "smooth"});
      el.value = "";
    }
  });
  document.addEventListener("click", function (e) {
    var t = e.target.closest ? e.target.closest(".bk-tick, .bk-tickfill, #sbnext, #checkbtn") : null;
    if (!t) return;
    if (t.id === "sbnext") { nextEmpty(); return; }
    if (t.id === "checkbtn") { check(); return; }
    var s = sheet();
    if (!s) return;
    if (t.classList.contains("bk-tick")) {
      var hidden = t.nextElementSibling;
      var on = !t.classList.contains("on");
      t.classList.toggle("on", on);
      t.setAttribute("aria-pressed", on ? "true" : "false");
      if (hidden) { hidden.value = on ? "✓" : ""; clearMark(hidden); }
      changed();
      return;
    }
    // "it is correct": the tick goes in the box beside it
    var box = s.querySelector('textarea[data-q="' + t.getAttribute("data-q") + '"]');
    if (box) {
      box.value = "✓";
      box.dispatchEvent(new Event("input", {bubbles: true}));
    }
  });
  // Enter in a gap goes to the next gap, the way a form on a phone should
  document.addEventListener("keydown", function (e) {
    var el = e.target;
    if (e.key !== "Enter" || el.tagName !== "INPUT" || !el.classList.contains("bk-blank")) return;
    e.preventDefault();
    var all = Array.prototype.slice.call(sheet().querySelectorAll(
      "input.bk-blank:not([readonly]), textarea.bk-blank:not([readonly])"));
    var next = all[all.indexOf(el) + 1];
    if (next) next.focus(); else el.blur();
  });
  // a tap on any link sends what is waiting before the page changes
  document.addEventListener("click", function (e) {
    if (e.target.closest && e.target.closest("a[href]")) push();
  }, true);
  window.addEventListener("beforeunload", push);
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "hidden") push();
  });

  function boot() {
    if (!sheet()) return;
    Array.prototype.forEach.call(sheet().querySelectorAll("textarea.bk-long"), grow);
    progress();
  }
  document.addEventListener("DOMContentLoaded", boot);
  document.addEventListener("pageswap", function () { dirty = false; clearTimeout(armed); boot(); });
  boot();
})();
