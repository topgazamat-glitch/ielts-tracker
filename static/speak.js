/* The recorder in a handout's speaking task.
 *
 * The booklet says "record yourself for about a minute and send it to your
 * teacher"; on the site that happens here. The microphone is voice.js - it
 * says what it is doing and why it cannot. A recording shorter than the task
 * asks for is not sent, and says how much is missing; a long enough one is
 * sent the moment it stops and the box counts as answered, so the part can be
 * checked. A student whose phone cannot record says so, and the teacher sees
 * who did.
 */
(function () {
  var live = null;               // { box, rec }

  function sheetData(box) {
    var s = box.closest(".booksheet");
    return s ? s.dataset : {};
  }
  function say(box, text, kind) {
    var el = box.querySelector(".rec-say");
    if (!el) return;
    el.textContent = text || "";
    el.className = "rec-say" + (kind ? " " + kind : "");
  }
  function button(box, label, on) {
    var b = box.querySelector(".bk-rec-go");
    if (!b) return;
    b.classList.toggle("live", !!on);
    b.querySelector("span").textContent = label;
    var vu = box.querySelector(".rec-vu");
    if (vu) vu.hidden = !on;
  }
  function setValue(box, value) {
    var input = box.querySelector('input[type="hidden"]');
    if (!input) return;
    input.value = value;
    input.dispatchEvent(new Event("input", { bubbles: true }));   // handout.js saves and counts it
  }
  function showHave(box, src, secs) {
    var have = box.querySelector(".bk-rec-have");
    if (!have) return;
    var audio = have.querySelector("audio");
    if (audio && src) audio.src = src;
    var len = have.querySelector(".bk-rec-len");
    if (len) len.textContent = Voice.clock(secs * 1000) + " · sent to your teacher ✓";
    have.hidden = false;
    box.classList.add("has");
    var cant = box.querySelector(".bk-rec-cant");
    if (cant) cant.hidden = true;
  }

  function start(box) {
    var d = sheetData(box);
    if (!d.speak) {
      say(box, "Students record here. Their recordings come to your Speaking page.", "ask");
      return;
    }
    if (!window.Voice) { say(box, "The recorder did not load — reload the page.", "error"); return; }
    var need = parseInt(box.getAttribute("data-min") || "45", 10) * 1000;
    button(box, "Stop", true);
    var rec = Voice.start({
      maxMs: 5 * 60 * 1000,
      onState: function (text, kind) {
        if (kind === "error") { button(box, "Start recording", false); live = null; }
        if (text) say(box, text, kind);
      },
      onDevice: function () { if (Voice.pickers) Voice.pickers(); },
      onLevel: function (level) {
        var bar = box.querySelector(".rec-vu i");
        if (bar) bar.style.width = Math.round(level * 100) + "%";
      },
      onTick: function (ms) {
        var c = box.querySelector(".bk-rec-clock");
        if (c) c.textContent = Voice.clock(ms);
        box.classList.toggle("enough", ms >= need);
      }
    });
    live = { box: box, rec: rec };
  }

  function stop(box) {
    if (!live) return;
    var rec = live.rec;
    live = null;
    button(box, "Record again", false);
    var need = parseInt(box.getAttribute("data-min") || "45", 10);
    rec.stop().then(function (got) {
      if (!got || got.empty || got.quiet) return;              // voice.js has said why
      var secs = Math.round(got.ms / 1000);
      if (secs < need) {
        say(box, "That was " + Voice.clock(got.ms) + ". Talk for at least " + Voice.clock(need * 1000) +
            " — record again and say a little more.", "warn");
        return;
      }
      var d = sheetData(box);
      var fd = new FormData();
      fd.append("q", box.getAttribute("data-qid"));
      fd.append("seconds", String(secs));
      fd.append("kind", got.mime);
      var ext = got.mime.indexOf("mp4") >= 0 ? "m4a" : got.mime.indexOf("ogg") >= 0 ? "ogg" : "webm";
      fd.append("file", got.blob, "speak." + ext);
      say(box, "Sending to your teacher…", "ask");
      fetch(d.speak, { method: "POST", body: fd, credentials: "same-origin" })
        .then(function (r) { return r.json(); })
        .then(function (out) {
          if (!out.ok) {
            say(box, out.why === "short" ? "That recording is too short." :
                     out.why === "locked" ? "This part is already checked." :
                     "Could not send the recording — try again.", "error");
            return;
          }
          setValue(box, out.value);
          showHave(box, out.url, secs);
          say(box, "Sent ✓ Your teacher will listen to it.", "ok");
          var msg = box.querySelector(".bk-rec-cantmsg");
          if (msg) msg.hidden = true;
        })
        .catch(function () { say(box, "Could not send the recording — are you online? Record again.", "error"); });
    });
  }

  document.addEventListener("click", function (e) {
    var t = e.target.closest ? e.target.closest(".bk-rec-go, .bk-rec-cant, .bk-rec-try") : null;
    if (!t) return;
    var box = t.closest(".bk-rec");
    if (!box || box.classList.contains("locked")) return;
    e.preventDefault();
    if (t.classList.contains("bk-rec-go")) {
      if (live && live.box === box) stop(box);
      else if (!live) start(box);
      return;
    }
    if (t.classList.contains("bk-rec-cant")) {
      // asked twice, without a dialog: the first tap explains, the second sends
      if (!t.classList.contains("armed")) {
        t.classList.add("armed");
        t.textContent = "Tap again: tell my teacher I can't record";
        setTimeout(function () { t.classList.remove("armed"); t.textContent = "I can't record"; }, 5000);
        return;
      }
      setValue(box, "cant");
      t.hidden = true;
      var msg = box.querySelector(".bk-rec-cantmsg");
      if (msg) msg.hidden = false;
      say(box, "");
      return;
    }
    // try again after "I can't record"
    setValue(box, "");
    var m = box.querySelector(".bk-rec-cantmsg");
    if (m) m.hidden = true;
    var c = box.querySelector(".bk-rec-cant");
    if (c) { c.hidden = false; c.classList.remove("armed"); c.textContent = "I can't record"; }
  });

  // ---- the teacher's spoken reply, on the Speaking page
  var reply = null;              // { btn, rec }
  function replySay(btn, text, kind) {
    var el = btn.closest(".sp-form").querySelector(".rec-say");
    if (el) { el.textContent = text || ""; el.className = "rec-say" + (kind ? " " + kind : ""); }
  }
  document.addEventListener("click", function (e) {
    var btn = e.target.closest ? e.target.closest(".sp-rec") : null;
    if (!btn) return;
    e.preventDefault();
    var form = btn.closest(".sp-form");
    var vu = form.querySelector(".rec-vu"), clock = form.querySelector(".rec-clock");
    if (reply && reply.btn === btn) {
      var r = reply.rec;
      reply = null;
      btn.classList.remove("live");
      btn.querySelector("span").textContent = "Record a reply";
      if (vu) vu.hidden = true;
      r.stop().then(function (got) {
        if (!got || got.empty || got.quiet) return;
        var fd = new FormData();
        fd.append("attempt", btn.getAttribute("data-attempt"));
        fd.append("question", btn.getAttribute("data-question"));
        fd.append("kind", got.mime);
        var ext = got.mime.indexOf("mp4") >= 0 ? "m4a" : got.mime.indexOf("ogg") >= 0 ? "ogg" : "webm";
        fd.append("file", got.blob, "reply." + ext);
        replySay(btn, "Saving…", "ask");
        fetch("/speaking/voice", { method: "POST", body: fd, credentials: "same-origin" })
          .then(function (res) { return res.json(); })
          .then(function (out) {
            if (!out.ok) throw new Error("no");
            replySay(btn, "Reply saved · " + Voice.clock(got.ms) + " — the student will hear it.", "ok");
            var card = btn.closest(".sp-card"), have = card.querySelector(".sp-fbv audio");
            if (have) have.src = out.url;
            else {
              var div = document.createElement("div");
              div.className = "sp-fbv";
              div.innerHTML = '<audio controls preload="none"></audio>';
              div.querySelector("audio").src = out.url;
              card.appendChild(div);
            }
          })
          .catch(function () { replySay(btn, "Could not save the reply — record it again.", "error"); });
      });
      return;
    }
    if (reply || live || !window.Voice) return;
    btn.classList.add("live");
    btn.querySelector("span").textContent = "Stop";
    if (vu) vu.hidden = false;
    var rec = Voice.start({
      maxMs: 3 * 60 * 1000,
      onState: function (text, kind) {
        if (kind === "error") { btn.classList.remove("live"); btn.querySelector("span").textContent = "Record a reply";
                                if (vu) vu.hidden = true; reply = null; }
        if (text) replySay(btn, text, kind);
      },
      onDevice: function () { if (Voice.pickers) Voice.pickers(); },
      onLevel: function (level) { var i = vu && vu.querySelector("i"); if (i) i.style.width = Math.round(level * 100) + "%"; },
      onTick: function (ms) { if (clock) clock.textContent = Voice.clock(ms); }
    });
    reply = { btn: btn, rec: rec };
  });

  // a recording already kept: its player gets its address
  function boot() {
    Array.prototype.forEach.call(document.querySelectorAll(".bk-rec[data-file]"), function (box) {
      var d = sheetData(box), audio = box.querySelector(".bk-rec-have audio");
      if (audio && d.speakfile && !audio.getAttribute("src")) audio.src = d.speakfile + box.getAttribute("data-file");
    });
  }
  document.addEventListener("DOMContentLoaded", boot);
  document.addEventListener("pageswap", function () {
    if (live) { live.rec.stop(); live = null; }
    if (reply) { reply.rec.stop(); reply = null; }
    boot();
  });
  boot();
})();
