/* The microphone, for the teacher's voice notes and the students' recordings.
 *
 * A recorder that only says something when it works leaves people guessing:
 * the teacher pressed Record, nothing visible happened, and the reason - a
 * permission box, a microphone the Mac had blocked, another app holding it -
 * was never said. So this says what it is doing at every step: asking for the
 * microphone, waiting for an answer, recording (with a meter that moves when
 * it hears you, and a warning when it hears nothing), and, when it cannot,
 * why and what to do about it.
 *
 * Which microphone matters too. A Mac can be set to listen to a camera, a
 * monitor without a microphone, a closed laptop or a Zoom device, and then
 * every recording is silence. So the recorder names the microphone it is
 * using, a list lets another be chosen (remembered on this device), and the
 * "I can't hear you" warning names it. Two things decide whether anything
 * was heard - the meter, and how much the recording itself grows each second
 * (an Opus recording of silence is tiny) - so a meter that cannot run never
 * claims silence on its own.
 *
 *   var rec = Voice.start({
 *     onState:  function (text, kind) {},   // kind: "ask" | "live" | "warn" | "error"
 *     onLevel:  function (0..1) {},
 *     onTick:   function (ms) {},
 *     onDevice: function (label) {},        // the microphone actually in use
 *     maxMs:    180000
 *   });
 *   rec.stop().then(function (got) { got.blob, got.mime, got.ms, got.quiet });
 *   Voice.devices().then(function (list) { [{id, label}] });   // names show once the microphone was allowed
 *   Voice.choose(id) / Voice.chosen()
 */
(function () {
  var KEY = "voice-mic";

  function pickMime() {
    var M = window.MediaRecorder;
    if (!M || !M.isTypeSupported) return "";
    // Opus in WebM is what Chrome, Edge and Firefox record well; Safari gives mp4
    var tries = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg;codecs=opus"];
    for (var i = 0; i < tries.length; i++) if (M.isTypeSupported(tries[i])) return tries[i];
    return "";
  }

  function isMac() { return /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent || ""); }

  function chosen() { try { return localStorage.getItem(KEY) || ""; } catch (e) { return ""; } }
  function choose(id) { try { if (id) localStorage.setItem(KEY, id); else localStorage.removeItem(KEY); } catch (e) {} }

  function devices() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) return Promise.resolve([]);
    return navigator.mediaDevices.enumerateDevices().then(function (all) {
      return all.filter(function (d) { return d.kind === "audioinput"; })
                .map(function (d, i) { return { id: d.deviceId, label: d.label || ("Microphone " + (i + 1)) }; });
    }).catch(function () { return []; });
  }

  // what went wrong, in words a person can act on
  function explain(err) {
    var name = (err && err.name) || "";
    if (name === "NotAllowedError" || name === "SecurityError" || name === "PermissionDeniedError") {
      return "The microphone is blocked. Click the microphone (or lock) icon at the left of the address bar and " +
             "choose Allow, then press Record again." +
             (isMac() ? " On a Mac, also open System Settings → Privacy & Security → Microphone and switch your " +
                        "browser on." : "");
    }
    if (name === "NotFoundError" || name === "OverconstrainedError" || name === "DevicesNotFoundError") {
      return "No microphone was found. Plug one in, or choose one in your computer's sound settings.";
    }
    if (name === "NotReadableError" || name === "AbortError" || name === "TrackStartError") {
      return "The microphone is busy in another app — close Zoom, a Telegram call or anything else using it, " +
             "then press Record again.";
    }
    return "The microphone could not start (" + (name || "unknown") + "). Reload the page and try again.";
  }

  function supported() {
    return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && window.MediaRecorder);
  }

  function silentHelp(label) {
    return "I can't hear anything" + (label ? " from “" + label + "”" : "") + ". " +
           "Choose another microphone in the list, or check " +
           (isMac() ? "System Settings → Sound → Input (the bar there should move when you speak)."
                    : "your computer's sound settings.");
  }

  function start(o) {
    o = o || {};
    var say = o.onState || function () {};
    var ctl = { stopped: false, ready: false };
    var settle, done = new Promise(function (res) { settle = res; });
    var chunks = [], recorder = null, stream = null, t0 = 0, ticker = null, meterTimer = null;
    var audioCtx = null, meterHeard = 0, bytesHeard = 0, meterWorks = false, quietSince = 0, label = "";

    if (!supported()) {
      say("This browser cannot record. Use Chrome, Safari or Firefox, kept up to date.", "error");
      settle(null);
      ctl.stop = function () { return done; };
      return ctl;
    }

    // the meter's audio engine is made now, inside the tap: made later, after
    // the permission box, a browser may leave it paused and it would hear nothing
    try {
      var AC = window.AudioContext || window.webkitAudioContext;
      audioCtx = AC ? new AC() : null;
      if (audioCtx && audioCtx.resume) audioCtx.resume();
    } catch (e) { audioCtx = null; }

    say("Asking for the microphone…", "ask");
    var waiting = setTimeout(function () {
      if (!ctl.ready && !ctl.stopped) {
        say("Waiting for permission — look for a box asking to use the microphone (at the top of the window) and " +
            "choose Allow.", "ask");
      }
    }, 4000);

    function heard() { return meterHeard > 0 || bytesHeard > 0; }

    function finish(err) {
      clearTimeout(waiting); clearInterval(ticker); clearInterval(meterTimer);
      if (stream) stream.getTracks().forEach(function (t) { t.stop(); });
      if (audioCtx && audioCtx.close) { try { audioCtx.close(); } catch (e) {} }
      if (err) { say(explain(err), "error"); settle(null); return; }
      var mime = (recorder && recorder.mimeType) || ctl.mime || "audio/webm";
      var blob = new Blob(chunks, { type: mime });
      var ms = Date.now() - t0;
      if (blob.size < 1000) {
        say("Nothing was recorded. " + silentHelp(label), "error");
        settle({ blob: blob, mime: mime, ms: ms, empty: true });
        return;
      }
      // silent only when what can listen agrees: the meter that ran, or an Opus
      // recording that never grew - then it is not worth sending to anyone
      var quiet = !heard() && (meterWorks || opusLike);
      if (quiet) say("Nothing was heard, so it was not saved. " + silentHelp(label), "error");
      settle({ blob: blob, mime: mime, ms: ms, quiet: quiet });
    }

    var opusLike = /opus|webm|ogg/.test(pickMime());

    function begin(s) {
      stream = s;
      if (ctl.stopped) { finish(); return; }
      ctl.ready = true;
      clearTimeout(waiting);
      var track = s.getAudioTracks()[0];
      label = (track && track.label) || "";
      if (o.onDevice) o.onDevice(label);
      var mime = pickMime();
      ctl.mime = mime;
      try { recorder = new MediaRecorder(s, mime ? { mimeType: mime } : undefined); }
      catch (e) { recorder = new MediaRecorder(s); ctl.mime = ""; }
      recorder.ondataavailable = function (ev) {
        if (!ev.data || !ev.data.size) return;
        chunks.push(ev.data);
        // an Opus second of silence is a few hundred bytes; a second of speech is thousands
        if (opusLike && chunks.length > 1 && ev.data.size > 1800) bytesHeard += 1;
      };
      recorder.onstop = function () { finish(); };
      recorder.start(1000);                       // a chunk a second: nothing is lost on stop
      t0 = Date.now(); quietSince = t0;
      say("Recording" + (label ? " from “" + label + "”" : "") + " — speak now", "live");

      // the meter: how loud, ten times a second, by the loudest sample (a laptop
      // microphone with noise suppression on is quiet, and the average hides it)
      try {
        if (!audioCtx) throw new Error("no audio engine");
        if (audioCtx.resume) audioCtx.resume();
        var src = audioCtx.createMediaStreamSource(s), an = audioCtx.createAnalyser();
        an.fftSize = 1024; src.connect(an);
        var buf = new Float32Array(an.fftSize);
        meterTimer = setInterval(function () {
          if (audioCtx.state !== "running") return;          // a paused engine reads zeros: say nothing
          meterWorks = true;
          if (an.getFloatTimeDomainData) an.getFloatTimeDomainData(buf);
          var peak = 0;
          for (var i = 0; i < buf.length; i++) { var v = Math.abs(buf[i]); if (v > peak) peak = v; }
          var level = Math.min(1, Math.sqrt(peak) * 1.4);        // a gentle curve, so quiet speech still shows
          if (o.onLevel) o.onLevel(level);
          if (peak > 0.02) { meterHeard += 1; quietSince = Date.now(); }
        }, 100);
      } catch (e) { meterWorks = false; }

      ticker = setInterval(function () {
        var now = Date.now(), ms = now - t0;
        if (o.onTick) o.onTick(ms);
        if (o.maxMs && ms >= o.maxMs) { ctl.stop(); return; }
        if (bytesHeard) quietSince = Math.max(quietSince, now - 1500);
        if (ms > 5000 && !heard() && (meterWorks || opusLike)) {
          say(silentHelp(label), "warn");
        } else if (heard() && now - quietSince > 6000 && meterWorks) {
          say("It has gone quiet — still there?", "warn");
        } else if (heard()) {
          say("Recording" + (label ? " from “" + label + "”" : "") + " — speak now", "live");
        }
      }, 500);
    }

    function ask(useChosen) {
      var id = useChosen ? chosen() : "";
      var audio = { echoCancellation: true, noiseSuppression: true, autoGainControl: true };
      if (id) audio.deviceId = { exact: id };
      return navigator.mediaDevices.getUserMedia({ audio: audio });
    }

    ask(true).catch(function (err) {
      // the remembered microphone has gone (unplugged): fall back to the computer's own choice
      if (chosen() && err && (err.name === "OverconstrainedError" || err.name === "NotFoundError")) {
        choose("");
        return ask(false);
      }
      throw err;
    }).then(begin).catch(function (err) { finish(err); });

    ctl.stop = function () {
      if (!ctl.stopped) {
        ctl.stopped = true;
        if (recorder && recorder.state === "recording") recorder.stop();
        else if (!ctl.ready) { clearTimeout(waiting); say("", "ask"); settle(null); }
      }
      return done;
    };
    ctl.done = done;
    return ctl;
  }

  function clock(ms) {
    var s = Math.round(ms / 1000);
    return Math.floor(s / 60) + ":" + ("0" + s % 60).slice(-2);
  }

  // a <select> listing the microphones, kept in step with the chosen one
  function fillPicker(sel) {
    if (!sel) return Promise.resolve();
    return devices().then(function (list) {
      var named = list.filter(function (d) { return d.label && !/^Microphone \d+$/.test(d.label); });
      if (list.length < 2 || !named.length) { sel.hidden = true; return; }
      var pick = chosen();
      sel.innerHTML = "";
      var first = document.createElement("option");
      first.value = ""; first.textContent = "Microphone: the computer's choice";
      sel.appendChild(first);
      list.forEach(function (d) {
        if (d.id === "default" || d.id === "communications") return;   // Chrome's aliases for the same one
        var op = document.createElement("option");
        op.value = d.id; op.textContent = "Microphone: " + d.label;
        if (d.id === pick) op.selected = true;
        sel.appendChild(op);
      });
      sel.hidden = false;
    });
  }
  document.addEventListener("change", function (e) {
    if (e.target && e.target.matches && e.target.matches("select.mic-pick")) {
      choose(e.target.value);
      Array.prototype.forEach.call(document.querySelectorAll("select.mic-pick"), function (s) {
        if (s !== e.target) s.value = e.target.value;
      });
    }
  });
  function pickers() {
    Array.prototype.forEach.call(document.querySelectorAll("select.mic-pick"), fillPicker);
  }
  document.addEventListener("DOMContentLoaded", pickers);
  document.addEventListener("pageswap", pickers);
  if (navigator.mediaDevices && navigator.mediaDevices.addEventListener) {
    navigator.mediaDevices.addEventListener("devicechange", pickers);
  }

  window.Voice = { start: start, supported: supported, clock: clock, explain: explain,
                   devices: devices, chosen: chosen, choose: choose, pickers: pickers };
})();
