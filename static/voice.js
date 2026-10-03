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
 *   var rec = Voice.start({
 *     onState: function (text, kind) {},   // kind: "ask" | "live" | "warn" | "error"
 *     onLevel: function (0..1) {},
 *     onTick:  function (ms) {},
 *     maxMs:   180000
 *   });
 *   rec.stop().then(function (got) { got.blob, got.mime, got.ms });
 */
(function () {
  function pickMime() {
    var M = window.MediaRecorder;
    if (!M || !M.isTypeSupported) return "";
    // Opus in WebM is what Chrome, Edge and Firefox record well; Safari gives mp4
    var tries = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg;codecs=opus"];
    for (var i = 0; i < tries.length; i++) if (M.isTypeSupported(tries[i])) return tries[i];
    return "";
  }

  function isMac() { return /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent || ""); }

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

  function start(o) {
    o = o || {};
    var say = o.onState || function () {};
    var ctl = { stopped: false, ready: false };
    var settle, done = new Promise(function (res) { settle = res; });
    var chunks = [], recorder = null, stream = null, t0 = 0, ticker = null, meterTimer = null;
    var audioCtx = null, heard = 0, quietSince = 0;

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

    function finish(err) {
      clearTimeout(waiting); clearInterval(ticker); clearInterval(meterTimer);
      if (stream) stream.getTracks().forEach(function (t) { t.stop(); });
      if (audioCtx && audioCtx.close) { try { audioCtx.close(); } catch (e) {} }
      if (err) { say(explain(err), "error"); settle(null); return; }
      var mime = (recorder && recorder.mimeType) || ctl.mime || "audio/webm";
      var blob = new Blob(chunks, { type: mime });
      var ms = Date.now() - t0;
      if (blob.size < 1000) {
        say("Nothing was recorded. Check that the right microphone is chosen in your sound settings, then try " +
            "again.", "error");
        settle({ blob: blob, mime: mime, ms: ms, empty: true });
        return;
      }
      // the meter only advises: a recording it did not hear is still kept
      settle({ blob: blob, mime: mime, ms: ms, quiet: !heard });
    }

    navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } })
      .then(function (s) {
        stream = s;
        if (ctl.stopped) { finish(); return; }
        ctl.ready = true;
        clearTimeout(waiting);
        var mime = pickMime();
        ctl.mime = mime;
        try { recorder = new MediaRecorder(s, mime ? { mimeType: mime } : undefined); }
        catch (e) { recorder = new MediaRecorder(s); ctl.mime = ""; }
        recorder.ondataavailable = function (ev) { if (ev.data && ev.data.size) chunks.push(ev.data); };
        recorder.onstop = function () { finish(); };
        recorder.start(1000);                       // a chunk a second: nothing is lost on stop
        t0 = Date.now(); quietSince = t0;
        say("Recording — speak now", "live");

        // the meter: how loud, ten times a second
        try {
          if (!audioCtx) throw new Error("no audio engine");
          if (audioCtx.resume) audioCtx.resume();
          var src = audioCtx.createMediaStreamSource(s), an = audioCtx.createAnalyser();
          an.fftSize = 512; src.connect(an);
          var buf = new Uint8Array(an.fftSize);
          meterTimer = setInterval(function () {
            an.getByteTimeDomainData(buf);
            var sum = 0;
            for (var i = 0; i < buf.length; i++) { var v = (buf[i] - 128) / 128; sum += v * v; }
            var level = Math.min(1, Math.sqrt(sum / buf.length) * 4);
            if (o.onLevel) o.onLevel(level);
            var now = Date.now();
            if (level > 0.06) { heard += 1; quietSince = now; }
            if (now - quietSince > 4000) {
              say(heard ? "It has gone quiet — still there?" :
                  "I can't hear anything. Speak a little louder, or check which microphone your computer is using.",
                  "warn");
            } else if (heard) {
              say("Recording — speak now", "live");
            }
          }, 100);
        } catch (e) { heard = 1; }                 // no meter on this browser: do not claim silence

        ticker = setInterval(function () {
          var ms = Date.now() - t0;
          if (o.onTick) o.onTick(ms);
          if (o.maxMs && ms >= o.maxMs) ctl.stop();
        }, 250);
      })
      .catch(function (err) { finish(err); });

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

  window.Voice = { start: start, supported: supported, clock: clock, explain: explain };
})();
