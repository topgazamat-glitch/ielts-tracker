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
            name: el.getAttribute("data-name") || "",
            back: el.getAttribute("data-back") || "",
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
    gridCount();
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
      if (form.requestSubmit) form.requestSubmit(); else form.submit();
      return;
    }
    if (typing) return;
    // the paper copy of a handout: y ticks it done, n says it is not complete
    if ((e.key === "y" || e.key === "n") && document.getElementById("tick-" + e.key)) {
      e.preventDefault();
      document.getElementById("tick-" + e.key).click();
      return;
    }
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
      // the set being marked travels in the address, so a skip stays in it
      var back = G().back, tail = "";
      var q = back.indexOf("?");
      if (q >= 0) tail = "&" + back.slice(q + 1);
      var url = "/skip?submission_id=" + G().skip + tail;
      if (window.Nav) window.Nav.go(url, true); else window.location.href = url;
    }
  });

  // ---- saving without a page load
  //
  // The form is posted in the background and the next piece put in place
  // of this one, the same way the links swap pages. Anything unexpected
  // falls back to the ordinary submit, so the worst case is the old
  // behaviour: a full reload.
  function toast(text) {
    var el = document.getElementById("toast");
    if (!el) {
      el = document.createElement("div");
      el.id = "toast";
      document.body.appendChild(el);
    }
    el.textContent = text;
    el.classList.add("on");
    clearTimeout(toast.timer);
    toast.timer = setTimeout(function () { el.classList.remove("on"); }, 1800);
  }

  // ---- a voice note, recorded here and kept beside the mark
  //
  // Uploaded the moment the recording stops, so the mark can then be saved
  // the ordinary way. The microphone itself is voice.js, which says what it
  // is doing - asking, waiting, recording, or why it cannot. The piece the
  // note belongs to is fixed when recording starts, because by the time the
  // upload finishes the page may already show the next student.
  var current = null;                        // the recording now running
  var voicePending = null;                   // resolves when the upload is done
  function recNote(text, kind) {
    var el = document.getElementById("rectime");
    if (!el) return;
    el.textContent = text;
    el.className = "rec-say" + (kind ? " " + kind : "");
  }
  function meter(level) {
    var bar = document.querySelector("#recvu i");
    if (bar) bar.style.width = Math.round(level * 100) + "%";
  }
  function recButton(live, label) {
    var btn = document.getElementById("rec");
    if (!btn) return;
    btn.classList.toggle("live", !!live);
    btn.innerHTML = '<i class="dot"></i>' + label;
    var vu = document.getElementById("recvu");
    if (vu) vu.hidden = !live;
  }
  function uploadVoice(got, sid) {
    if (!sid || !got || got.empty) return Promise.resolve();
    var fd = new FormData();
    fd.append("submission_id", sid);
    fd.append("kind", got.mime);
    var ext = got.mime.indexOf("mp4") >= 0 ? "m4a" : got.mime.indexOf("ogg") >= 0 ? "ogg" : "webm";
    fd.append("file", got.blob, "voice." + ext);
    recNote("Saving…");
    return fetch("/grade/voice", {method: "POST", body: fd, credentials: "same-origin"})
      .then(function (r) { return r.json(); })
      .then(function (out) {
        if (!out.ok) throw new Error(out.why || "no");
        var box = document.getElementById("voice");
        // only dress the page if it still shows the piece this note is for
        if (box && box.getAttribute("data-sid") === String(sid)) {
          var wrap = document.getElementById("recwrap"), play = document.getElementById("recplay");
          if (play) play.src = out.url;
          if (wrap) wrap.hidden = false;
          recNote("Voice note saved · " + Voice.clock(got.ms), "ok");
        }
        toast("Voice note saved · " + Voice.clock(got.ms));
      })
      .catch(function () { recNote("Could not save the recording — check the internet and record again.", "error"); });
  }
  function stopRecording() {
    if (!current) return;
    var rec = current, sid = rec._sid;
    current = null;
    recButton(false, "Record again");
    voicePending = rec.stop().then(function (got) { return uploadVoice(got, sid); })
      .then(function () { voicePending = null; });
  }
  function startRecording() {
    if (!window.Voice) { recNote("The recorder did not load — reload the page.", "error"); return; }
    var box = document.getElementById("voice");
    var sid = box ? box.getAttribute("data-sid") : null;
    recButton(true, "Stop");
    meter(0);
    current = Voice.start({
      maxMs: 180000,                         // three minutes is a lecture
      onState: function (text, kind) {
        if (kind === "error") { recButton(false, "Record a voice note"); current = null; }
        if (text) recNote(text, kind);
      },
      onLevel: meter,
      onTick: function (ms) {
        var el = document.getElementById("recclock");
        if (el) el.textContent = Voice.clock(ms);
        if (ms >= 180000) stopRecording();
      }
    });
    current._sid = sid;
  }
  document.addEventListener("click", function (e) {
    var t = e.target.closest ? e.target.closest("#rec, #recdel") : null;
    if (!t) return;
    e.preventDefault();
    if (t.id === "rec") {
      if (current) stopRecording(); else startRecording();
      return;
    }
    var box = document.getElementById("voice");
    if (!box) return;
    fetch("/grade/voice/delete", {method: "POST", credentials: "same-origin",
      headers: {"Content-Type": "application/x-www-form-urlencoded"},
      body: "submission_id=" + encodeURIComponent(box.getAttribute("data-sid"))})
      .then(function () {
        var wrap = document.getElementById("recwrap"), play = document.getElementById("recplay");
        if (play) play.removeAttribute("src");
        if (wrap) wrap.hidden = true;
        recButton(false, "Record a voice note");
        recNote("");
      });
  });
  document.addEventListener("pageswap", function () {
    if (current) { current.stop(); current = null; }
  });

  document.addEventListener("submit", function (e) {
    var form = e.target;
    if (!form || form.id !== "gform" || !window.Nav || !window.fetch) return;
    if (form.dataset.native === "1") return;        // the fallback resubmitting
    e.preventDefault();
    // a recording still running is finished first, and its upload waited for
    stopRecording();
    var sub = e.submitter;
    var action = (sub && sub.getAttribute("formaction")) || form.getAttribute("action");
    var body = new URLSearchParams(new FormData(form));
    if (sub && sub.name) body.append(sub.name, sub.value);
    var save = document.getElementById("save");
    if (save) save.disabled = true;
    var skipping = /\/skip$/.test(action);
    var score = field("score") ? field("score").value : "";
    var name = G().name || "";
    if (window.Nav.bar) window.Nav.bar(true);
    Promise.resolve(voicePending).then(function () {
      return fetch(action, {method: "POST", body: body, credentials: "same-origin",
                            headers: {"Content-Type": "application/x-www-form-urlencoded"}});
    })
      .then(function (r) {
        if (!r.ok) throw new Error("not saved");
        return r.text().then(function (html) { return {html: html, url: r.url}; });
      })
      .then(function (got) {
        try {
          window.Nav.swap(got.html, got.url, true);
        } catch (err) {
          window.location.href = got.url;          // saved; the page just cannot be swapped
          return;
        }
        if (window.Nav.bar) window.Nav.bar(false);
        if (skipping) toast("Skipped " + name);
        else if (sub && sub.name === "tick") toast((sub.value === "done" ? "Ticked \u00b7 " : "Not complete \u00b7 ") + name);
        else if (name) toast("Saved \u00b7 " + name + (score ? " \u00b7 " + score + "/10" : ""));
      })
      .catch(function () {
        if (window.Nav.bar) window.Nav.bar(false);
        form.dataset.native = "1";
        if (sub && sub.click) sub.click(); else form.submit();
      });
  });

  // ---- the split between the papers and the marking, dragged by hand
  var SPLIT = "queue.split";
  function applySplit() {
    var q = document.querySelector(".queue");
    if (!q) return;
    var saved = null;
    try { saved = localStorage.getItem(SPLIT); } catch (err) {}
    if (saved) q.style.setProperty("--split", saved);
  }
  document.addEventListener("pointerdown", function (e) {
    var bar = e.target.closest && e.target.closest(".splitter");
    if (!bar) return;
    var q = bar.parentNode;
    e.preventDefault();
    bar.setPointerCapture(e.pointerId);
    document.body.classList.add("dragging");
    function move(ev) {
      var box = q.getBoundingClientRect();
      var pct = Math.max(35, Math.min(80, 100 * (ev.clientX - box.left) / box.width));
      q.style.setProperty("--split", pct.toFixed(1) + "%");
    }
    function stop() {
      bar.removeEventListener("pointermove", move);
      bar.removeEventListener("pointerup", stop);
      bar.removeEventListener("pointercancel", stop);
      document.body.classList.remove("dragging");
      try { localStorage.setItem(SPLIT, q.style.getPropertyValue("--split")); } catch (err) {}
    }
    bar.addEventListener("pointermove", move);
    bar.addEventListener("pointerup", stop);
    bar.addEventListener("pointercancel", stop);
  });

  // with criteria on, successive digits fill Task, Coherence, Vocabulary, Grammar
  function nextEmpty() {
    var fields = document.querySelectorAll('input[id^="f_c_"]');
    for (var i = 0; i < fields.length; i++) {
      if (fields[i].value === "") return fields[i].id.slice(2);
    }
    return fields.length ? fields[fields.length - 1].id.slice(2) : "score";
  }

  // ---- the grid: everyone's work for one task on one page
  function gridCount() {
    var cards = document.querySelectorAll(".gradecard");
    if (!cards.length) return;
    var done = 0;
    cards.forEach(function (c) {
      var f = c.querySelector('input[type="hidden"]');
      if (f && f.value !== "") done++;
    });
    var el = document.getElementById("gridcount");
    if (el) el.textContent = done + " of " + cards.length + " marked";
  }

  function boot() {
    recalc();
    gridCount();
    applySplit();
    var save = document.getElementById("save");
    if (save && ready()) save.disabled = false;
    (G().prefetch || []).forEach(function (u) { new Image().src = u; });
  }
  document.addEventListener("DOMContentLoaded", boot);
  document.addEventListener("pageswap", boot);
  boot();
})();
