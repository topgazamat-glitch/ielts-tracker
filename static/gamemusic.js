/* Music for the game, generated rather than downloaded.
 *
 * A backing track would be two or three megabytes and would need licensing.
 * A handful of oscillators cost nothing, work with no connection at all, and
 * can follow the game: calm while the room fills, urgent while the clock runs.
 * It plays only here, on the machine with the speakers - fifteen phones all
 * playing the same loop slightly out of step would be unbearable.
 */
(function () {
  var ac = null, timer = null, nextAt = 0, step = 0, mode = null;
  var master = null, on = true;

  try { on = localStorage.getItem("gamemusic") !== "off"; } catch (e) {}

  // A minor, F, C, G - four bars that go round without asking for attention
  var CHORDS = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]];
  var SPB = { lobby: 0.46, question: 0.26, reveal: 0.46 };

  function hz(midi) { return 440 * Math.pow(2, (midi - 69) / 12); }

  function ensure() {
    if (!ac) {
      var Ctx = window.AudioContext || window.webkitAudioContext;
      if (!Ctx) return false;
      ac = new Ctx();
      master = ac.createGain();
      master.gain.value = 0.075;          // under a speaking voice, not over it
      master.connect(ac.destination);
    }
    if (ac.state === "suspended") ac.resume();
    return true;
  }

  function note(midi, at, dur, type, level) {
    var o = ac.createOscillator(), g = ac.createGain();
    o.type = type; o.frequency.value = hz(midi);
    g.gain.setValueAtTime(0.0001, at);
    g.gain.exponentialRampToValueAtTime(level, at + 0.02);
    g.gain.exponentialRampToValueAtTime(0.0001, at + dur);
    o.connect(g); g.connect(master);
    o.start(at); o.stop(at + dur + 0.02);
  }

  function schedule() {
    if (!ac || !mode) return;
    var spb = SPB[mode] || 0.46;
    while (nextAt < ac.currentTime + 0.2) {
      var chord = CHORDS[Math.floor(step / 4) % CHORDS.length];
      var beat = step % 4;
      if (beat === 0) note(chord[0] - 12, nextAt, spb * 2.6, "sine", 0.5);
      var tone = chord[[0, 2, 1, 2][beat]];
      note(tone + 12, nextAt, spb * 1.5, "triangle", mode === "question" ? 0.3 : 0.22);
      if (mode === "question" && beat % 2 === 0) {
        note(chord[0] + 24, nextAt, 0.05, "square", 0.06);
      }
      nextAt += spb;
      step++;
    }
  }

  function start(which) {
    if (!on || mode === which) return;
    if (!ensure()) return;
    mode = which;
    if (!timer) {
      nextAt = ac.currentTime + 0.06;
      timer = setInterval(schedule, 25);
    }
    schedule();
  }

  function stop() {
    mode = null;
    if (timer) { clearInterval(timer); timer = null; }
  }

  function label(btn) {
    if (btn) btn.textContent = on ? "Music on" : "Music off";
  }

  window.GameMusic = {
    play: function (which) { if (on) start(which); else stop(); },
    stop: stop,
    armed: function () { return on; },
    toggle: function (btn) {
      on = !on;
      try { localStorage.setItem("gamemusic", on ? "on" : "off"); } catch (e) {}
      if (!on) stop(); else ensure();
      label(btn);
    },
    label: label
  };
})();
