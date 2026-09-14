/* The writing paper: count the words, keep the time, and never lose the work.
 *
 * Saving happens while they type, because the worst thing this page could do is
 * lose an essay. A closed tab, a flat battery or a lost connection should cost a
 * few seconds of typing, not an hour of it.
 */
(function () {
  function wire() {
    var paper = document.getElementById("paper");
    var box = document.getElementById("answer");
    if (!paper || !box || paper.dataset.wired) return;
    paper.dataset.wired = "1";

    var sub = paper.getAttribute("data-sub");
    var least = +paper.getAttribute("data-min") || 0;
    var minutes = +paper.getAttribute("data-minutes") || 0;
    var counter = document.getElementById("wordcount");
    var clock = document.getElementById("clock");
    var saved = document.getElementById("saved");
    var started = Date.now();
    var lastSent = box.value;
    var dirty = false;

    function words(text) {
      var t = (text || "").trim();
      return t ? t.split(/\s+/).length : 0;
    }

    function paint() {
      var n = words(box.value);
      counter.textContent = n + (n === 1 ? " word" : " words");
      counter.classList.toggle("short", least > 0 && n < least);
      if (least > 0) {
        counter.title = "at least " + least + " words";
      }
    }

    function tick() {
      var secs = Math.floor((Date.now() - started) / 1000);
      if (minutes > 0) {
        var left = minutes * 60 - secs;
        var over = left < 0;
        var m = Math.floor(Math.abs(left) / 60), sec = Math.abs(left) % 60;
        clock.textContent = (over ? "+" : "") + m + ":" + (sec < 10 ? "0" : "") + sec;
        clock.classList.toggle("short", over || left < 120);
      } else {
        var m2 = Math.floor(secs / 60);
        clock.textContent = m2 + " min";
      }
    }

    function save(force) {
      if (!force && box.value === lastSent) return;
      lastSent = box.value;
      dirty = false;
      var body = "answer=" + encodeURIComponent(box.value) +
                 "&seconds=" + Math.floor((Date.now() - started) / 1000);
      fetch("/s/" + window.location.pathname.split("/")[2] + "/write/" + sub + "/save", {
        method: "POST",
        headers: {"Content-Type": "application/x-www-form-urlencoded"},
        body: body
      }).then(function () {
        saved.textContent = "saved";
        setTimeout(function () { if (!dirty) saved.textContent = "saved"; }, 10);
      }).catch(function () {
        saved.textContent = "not saved — check your connection";
      });
    }

    box.addEventListener("input", function () {
      paint();
      dirty = true;
      saved.textContent = "…";
    });
    setInterval(function () { if (dirty) save(false); }, 4000);
    setInterval(tick, 1000);
    // a closed tab should not cost the last few seconds either
    window.addEventListener("pagehide", function () { if (dirty) save(true); });
    document.addEventListener("visibilitychange", function () {
      if (document.visibilityState === "hidden" && dirty) save(true);
    });

    var form = document.getElementById("writeform");
    if (form) {
      form.addEventListener("submit", function (e) {
        var n = words(box.value);
        if (least > 0 && n < least) {
          if (!window.confirm("That is " + n + " words and the task asks for at least "
                              + least + ". Hand it in anyway?")) {
            e.preventDefault();
            return;
          }
        } else if (!window.confirm("Hand it in? You will not be able to change it.")) {
          e.preventDefault();
          return;
        }
        dirty = false;
      });
    }

    var toggle = document.getElementById("qtoggle");
    var qbody = document.getElementById("qbody");
    if (toggle && qbody) {
      toggle.addEventListener("click", function () {
        qbody.hidden = !qbody.hidden;
        toggle.classList.toggle("shut", qbody.hidden);
      });
    }

    paint();
    tick();
  }

  document.addEventListener("DOMContentLoaded", wire);
  document.addEventListener("pageswap", wire);
  wire();
})();
