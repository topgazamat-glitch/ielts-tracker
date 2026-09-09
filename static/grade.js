/* The marking keypad, the quick notes, and the keyboard.
 *
 * In a file rather than inline so the page carries no script of its own and can
 * be swapped in without a reload - which is also what keeps the music playing.
 */
(function () {
  function G() {
    var el = document.getElementById("gradedata");
    if (!el) return {};
    var pre = [];
    try { pre = JSON.parse(el.getAttribute("data-prefetch") || "[]"); } catch (e) {}
    return {skip: el.getAttribute("data-skip"),
            regrade: el.getAttribute("data-regrade") === "1",
            prefetch: pre};
  }

  function field(name) { return document.getElementById("f_" + name); }

  function pick(name, value) {
    var f = field(name);
    if (!f) return;
    f.value = value;
    var pads = document.querySelectorAll('[data-for="' + name + '"]');
    for (var i = 0; i < pads.length; i++) {
      var v = parseFloat(pads[i].getAttribute("data-v"));
      pads[i].classList.toggle("sel", Math.abs(v - value) < 1e-9);
    }
    recalc();
    var save = document.getElementById("save");
    if (save) save.disabled = !ready();
  }

  function criteria() {
    return Array.prototype.map.call(
      document.querySelectorAll('input[id^="f_c_"]'), function (el) {
        return el.value === "" ? null : parseFloat(el.value);
      });
  }

  function ready() {
    var c = criteria();
    if (c.length) return c.some(function (v) { return v !== null; });
    var f = field("score");
    return !!(f && f.value !== "");
  }

  // the overall is the average of whatever is filled in, to the nearest half
  function recalc() {
    var out = document.getElementById("overall");
    if (!out) return;
    var got = criteria().filter(function (v) { return v !== null; });
    if (!got.length) {
      out.textContent = "The overall mark is the average of these four.";
      return;
    }
    var avg = got.reduce(function (a, b) { return a + b; }, 0) / got.length;
    avg = Math.round(avg * 2) / 2;
    out.innerHTML = "Overall <strong>" + avg + "</strong> out of 10" +
      (got.length < 4 ? " &mdash; from the " + got.length + " you have marked" : "");
  }

  document.addEventListener("click", function (e) {
    var b = e.target;
    while (b && b.nodeName !== "BUTTON") { b = b.parentNode; }
    if (!b || !b.hasAttribute("data-v")) return;
    e.preventDefault();
    pick(b.getAttribute("data-for"), parseFloat(b.getAttribute("data-v")));
  });

  window.useNote = function (btn) {
    var box = document.getElementById("note");
    if (!box) return;
    box.value = btn.textContent.trim();
    box.focus();
  };

  window.zoom = function (img) {
    if (img.dataset.full && img.src.indexOf(img.dataset.full) < 0) {
      img.src = img.dataset.full;
    }
    img.classList.toggle("zoom");
  };

  document.addEventListener("keydown", function (e) {
    var form = document.getElementById("gform");
    if (!form) return;
    var typing = e.target.tagName === "TEXTAREA" || e.target.tagName === "INPUT";
    if (e.key === "Enter" && ready() && !e.shiftKey) {
      e.preventDefault();
      form.submit();
      return;
    }
    if (typing) return;
    // a single mark: digits go to the score, or to whichever criterion is next
    var n = null;
    if (e.key >= "1" && e.key <= "9") n = +e.key;
    else if (e.key === "0") n = 10;
    if (n !== null) {
      e.preventDefault();
      if (e.shiftKey && n < 10) n += 0.5;      // Shift+7 is seven and a half
      var next = nextEmpty();
      pick(next, n);
      return;
    }
    if (e.key === "s" && !G().regrade) {
      window.location.href = "/skip?submission_id=" + G().skip;
    }
  });

  // with criteria on, successive digits fill Task, Coherence, Vocabulary, Grammar
  function nextEmpty() {
    var fields = document.querySelectorAll('input[id^="f_c_"]');
    for (var i = 0; i < fields.length; i++) {
      if (fields[i].value === "") return fields[i].id.slice(2);
    }
    return fields.length ? fields[fields.length - 1].id.slice(2) : "score";
  }

  function boot() {
    recalc();
    var save = document.getElementById("save");
    if (save && ready()) save.disabled = false;
    (G().prefetch || []).forEach(function (u) { new Image().src = u; });
  }
  document.addEventListener("DOMContentLoaded", boot);
  document.addEventListener("pageswap", boot);
  boot();
})();
