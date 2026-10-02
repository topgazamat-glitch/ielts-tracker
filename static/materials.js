/* The Materials page.
 *
 *  - The Section list depends on the Collection chosen above it.
 *  - Files can be ticked, all at once or a run with Shift, and the ticked ones
 *    deleted with one button; the button says how many and how much room.
 *  - Every delete asks twice, without a browser dialog (those freeze the page):
 *    the first tap turns the button red and asks; the second, within a few
 *    seconds, sends it. Without this script the site asks on a page instead.
 *
 * This lives in a file rather than inline in the page so the page carries no
 * script of its own, which is what lets it be swapped in without a reload -
 * and so the music does not stop when you open Materials.
 */
(function () {
  function fill() {
    var coll = document.getElementById("coll");
    var sect = document.getElementById("sect");
    if (!coll || !sect) return;
    var map = {};
    try { map = JSON.parse(coll.getAttribute("data-sections") || "{}"); }
    catch (e) { return; }
    sect.innerHTML = "";
    (map[coll.value] || []).forEach(function (name) {
      var o = document.createElement("option");
      o.value = name;
      o.textContent = name;
      sect.appendChild(o);
    });
  }

  function size(n) {
    if (n < 1024) return n + " B";
    var units = ["KB", "MB", "GB"], i = -1;
    do { n /= 1024; i++; } while (n >= 1024 && i < units.length - 1);
    return n.toFixed(1) + " " + units[i];
  }

  // the bar over the files: how many are ticked, and the button's words
  function count(form) {
    var boxes = form.querySelectorAll('input[name="id"]');
    var ticked = form.querySelectorAll('input[name="id"]:checked');
    var bytes = 0;
    Array.prototype.forEach.call(ticked, function (b) { bytes += parseInt(b.getAttribute("data-size") || "0", 10); });
    var all = form.querySelector("[data-all]");
    if (all) {
      all.checked = ticked.length > 0 && ticked.length === boxes.length;
      all.indeterminate = ticked.length > 0 && ticked.length < boxes.length;
    }
    var label = form.querySelector("[data-count]");
    if (label) {
      label.textContent = ticked.length
        ? ticked.length + " of " + boxes.length + " ticked · " + size(bytes)
        : label.getAttribute("data-total");
    }
    var btn = form.querySelector("[data-picked]");
    if (btn) {
      btn.disabled = !ticked.length;
      var words = btn.querySelector("[data-label]");
      if (words) {
        words.textContent = ticked.length ? "Delete " + ticked.length + " selected" : "Delete selected";
      }
      btn.setAttribute("data-arm", "Delete " + ticked.length + " file" + (ticked.length === 1 ? "" : "s") +
                       " for good? Tap again");
      disarm(btn);
    }
    Array.prototype.forEach.call(boxes, function (b) {
      var row = b.closest(".frow");
      if (row) row.classList.toggle("ticked", b.checked);
    });
  }

  function disarm(btn) {
    if (!btn.classList.contains("armed")) return;
    btn.classList.remove("armed");
    if (btn._was !== undefined) { btn.innerHTML = btn._was; }
    clearTimeout(btn._t);
  }

  // first tap asks, second tap sends
  function arm(e) {
    var btn = e.target.closest ? e.target.closest("button[data-arm]") : null;
    if (!btn || btn.disabled) return;
    var form = btn.form;
    if (!form) return;
    if (btn.classList.contains("armed")) {
      var c = form.querySelector('input[name="confirm"]');
      if (!c) {
        c = document.createElement("input");
        c.type = "hidden"; c.name = "confirm";
        form.appendChild(c);
      }
      c.value = "yes";
      btn.classList.add("going");
      return;                                    // let the form go, with this button's name and value
    }
    e.preventDefault();
    Array.prototype.forEach.call(document.querySelectorAll("button.armed"), disarm);
    btn._was = btn.innerHTML;
    btn.classList.add("armed");
    if (btn.classList.contains("f-del")) {
      btn.innerHTML = '<span class="arm-word">' + btn.getAttribute("data-arm") + "</span>";
    } else {
      btn.textContent = btn.getAttribute("data-arm");
    }
    btn._t = setTimeout(function () { disarm(btn); }, 4500);
  }

  function wire() {
    // the level strip slides on a phone: start it at the level you are on
    var strip = document.querySelector(".tabs.levels"), on = strip && strip.querySelector(".tab.on");
    if (strip && on && strip.scrollWidth > strip.clientWidth) {
      strip.scrollLeft = Math.max(0, on.offsetLeft - strip.offsetLeft - 24);
    }
    var coll = document.getElementById("coll");
    if (coll && !coll.dataset.wired) {
      coll.dataset.wired = "1";
      coll.addEventListener("change", fill);
      fill();
    }
    Array.prototype.forEach.call(document.querySelectorAll("form[data-files]"), function (form) {
      if (form.dataset.wired) return;
      form.dataset.wired = "1";
      var last = null;
      form.addEventListener("click", function (e) {
        var box = e.target;
        if (!box || box.nodeName !== "INPUT" || box.type !== "checkbox") return;
        if (box.hasAttribute("data-all")) {
          Array.prototype.forEach.call(form.querySelectorAll('input[name="id"]'), function (b) { b.checked = box.checked; });
        } else if (e.shiftKey && last && last !== box) {
          var list = Array.prototype.slice.call(form.querySelectorAll('input[name="id"]'));
          var a = list.indexOf(last), b = list.indexOf(box);
          list.slice(Math.min(a, b), Math.max(a, b) + 1).forEach(function (x) { x.checked = box.checked; });
        }
        if (!box.hasAttribute("data-all")) last = box;
        count(form);
      });
      count(form);
    });
  }

  // a recording plays in its own row; one at a time
  function play(e) {
    var btn = e.target.closest ? e.target.closest("[data-play]") : null;
    if (!btn) return;
    var audio = btn.parentNode.querySelector("audio");
    if (!audio) return;
    Array.prototype.forEach.call(document.querySelectorAll("audio.f-audio"), function (a) {
      if (a !== audio && !a.paused) { a.pause(); }
    });
    if (audio.paused) { audio.play(); } else { audio.pause(); }
  }
  function playing(e) {
    if (!e.target.classList || !e.target.classList.contains("f-audio")) return;
    var btn = e.target.parentNode.querySelector("[data-play]");
    if (btn) btn.classList.toggle("playing", e.type === "play");
  }
  document.addEventListener("play", playing, true);
  document.addEventListener("pause", playing, true);
  document.addEventListener("ended", playing, true);

  document.addEventListener("click", function (e) {
    play(e);
    arm(e);
    var open = e.target.closest ? e.target.closest("[data-open]") : null;
    if (open) {
      var d = document.getElementById(open.getAttribute("data-open"));
      if (d) {
        e.preventDefault();
        d.open = true;
        d.scrollIntoView({behavior: "smooth", block: "start"});
      }
    }
  }, true);

  document.addEventListener("DOMContentLoaded", wire);
  document.addEventListener("pageswap", wire);   // after a swapped navigation
  wire();
})();
