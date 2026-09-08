/* Classical background music, played rather than downloaded.
 *
 * The compositions are public domain - Beethoven, Mozart and Chopin have been
 * dead a long time - but recordings of them are not, so a file would need
 * licensing and would cost every student two or three megabytes on classroom
 * data. These are the actual notes, synthesised here: nothing to download,
 * nothing to license, and it works with no connection at all.
 *
 * It will not be mistaken for a concert pianist. It is a clean electric piano.
 */
(function () {
  var ac = null, master = null, timer = null, on = true;
  var piece = null, beat = 0, nextAt = 0;

  try { on = localStorage.getItem("music") !== "off"; } catch (e) {}

  function hz(m) { return 440 * Math.pow(2, (m - 69) / 12); }

  // ---- the pieces. [midi, beat, beats] with beat 0 at the start of the loop.
  function melody(list, offset, octave) {
    var out = [], t = offset || 0;
    for (var i = 0; i < list.length; i += 2) {
      if (list[i] !== null) out.push([list[i] + (octave || 0), t, list[i + 1]]);
      t += list[i + 1];
    }
    return out;
  }

  // Beethoven - Fur Elise, the opening. Sixteenths, so one beat is four notes.
  var ELISE = (function () {
    var q = 0.25;                      // the running sixteenth
    var rh = melody([
      76, q, 75, q, 76, q, 75, q, 76, q, 71, q, 74, q, 72, q,
      69, q * 2, null, q, 60, q, 64, q, 69, q,
      71, q * 2, null, q, 64, q, 68, q, 71, q,
      72, q * 2, null, q, 64, q,
      76, q, 75, q, 76, q, 75, q, 76, q, 71, q, 74, q, 72, q,
      69, q * 2, null, q, 60, q, 64, q, 69, q,
      71, q * 2, null, q, 64, q, 72, q, 71, q,
      69, q * 4
    ]);
    var lh = [[45, 2.0, 0.5], [52, 2.25, 0.5], [57, 2.5, 0.5],
              [40, 3.5, 0.5], [52, 3.75, 0.5], [56, 4.0, 0.5],
              [45, 5.0, 0.5], [52, 5.25, 0.5], [57, 5.5, 0.5],
              [45, 8.0, 0.5], [52, 8.25, 0.5], [57, 8.5, 0.5],
              [40, 9.5, 0.5], [52, 9.75, 0.5], [56, 10.0, 0.5],
              [45, 11.0, 0.5], [52, 11.25, 0.5], [57, 11.5, 0.5]];
    return {name: "Beethoven — Für Elise", bpm: 76,
            notes: rh.concat(lh), bars: 13};
  })();

  // Mozart - Sonata K.545, the opening. Alberti bass under a plain tune.
  var MOZART = (function () {
    var rh = melody([
      72, 1, 76, 1, 79, 0.5, 71, 0.5, 72, 0.5, 74, 0.5,
      72, 2, null, 2,
      74, 0.5, 72, 0.5, 74, 0.5, 76, 0.5, 74, 0.5, 72, 0.5, 71, 0.5, 69, 0.5,
      71, 2, null, 2
    ]);
    var lh = [], bass = [48, 55, 52, 55];
    for (var b = 0; b < 16; b++) {
      lh.push([bass[b % 4] - (b >= 8 ? 5 : 0), b * 0.5, 0.5]);
    }
    return {name: "Mozart — Sonata K.545", bpm: 104,
            notes: rh.concat(lh), bars: 8};
  })();

  // Chopin - Prelude Op. 28 No. 7. Sixteen bars of three, and barely moves.
  var CHOPIN = (function () {
    var rh = melody([
      73, 0.5, 75, 0.25, 76, 1.25, 73, 0.5, 76, 0.5,
      81, 1.5, 78, 0.5, 76, 1,
      73, 0.5, 75, 0.25, 76, 1.25, 73, 0.5, 76, 0.5,
      80, 1.5, 76, 0.5, 73, 1
    ]);
    var chords = [[45, 61, 64], [45, 61, 64], [40, 59, 64], [40, 59, 64],
                  [45, 61, 64], [45, 61, 64], [42, 57, 61], [42, 57, 61]];
    var lh = [];
    chords.forEach(function (c, i) {
      lh.push([c[0] - 12, i * 1.5, 1.4]);
      lh.push([c[1], i * 1.5 + 0.5, 0.9]);
      lh.push([c[2], i * 1.5 + 0.5, 0.9]);
    });
    return {name: "Chopin — Prelude Op. 28 No. 7", bpm: 60,
            notes: rh.concat(lh), bars: 12};
  })();

  var PIECES = [CHOPIN, MOZART, ELISE];

  function ensure(again) {
    if (!ac) {
      var Ctx = window.AudioContext || window.webkitAudioContext;
      if (!Ctx) return false;
      ac = new Ctx();
      master = ac.createGain();
      master.gain.value = 0.09;
      var soft = ac.createBiquadFilter();
      soft.type = "lowpass"; soft.frequency.value = 2600;
      master.connect(soft); soft.connect(ac.destination);
    }
    if (ac.state === "suspended") {
      // resume() is a promise: the state is still "suspended" on the very next
      // line, so the caller has to be told to come back rather than be told no
      ac.resume().then(function () {
        nextAt = ac.currentTime + 0.08;
        if (again) { again(); }
      });
      return false;
    }
    return true;
  }

  // one struck string: two detuned voices, quick on, long off
  function strike(midi, at, beats, spb) {
    var dur = Math.max(0.35, beats * spb * 1.8);
    var g = ac.createGain();
    g.gain.setValueAtTime(0.0001, at);
    g.gain.exponentialRampToValueAtTime(midi > 64 ? 0.5 : 0.35, at + 0.008);
    g.gain.exponentialRampToValueAtTime(0.0001, at + dur);
    g.connect(master);
    [0, 0.4].forEach(function (cents, i) {
      var o = ac.createOscillator();
      o.type = i ? "sine" : "triangle";
      o.frequency.value = hz(midi) * (1 + cents / 1200);
      o.connect(g); o.start(at); o.stop(at + dur + 0.05);
    });
  }

  // notes are not in time order once both hands are merged, so index them once
  function indexed(p) {
    if (p.grid) return p;
    p.grid = {};
    p.span = 0;
    p.notes.forEach(function (n) {
      var key = Math.round(n[1] * 4);
      (p.grid[key] = p.grid[key] || []).push(n);
      p.span = Math.max(p.span, n[1] + n[2]);
    });
    p.span = Math.ceil(p.span * 4) / 4;
    return p;
  }

  function schedule() {
    if (!ac || !piece) return;
    var spb = 60 / piece.bpm;
    while (nextAt < ac.currentTime + 0.6) {
      var due = piece.grid[Math.round(beat * 4)];
      if (due) {
        due.forEach(function (n) { strike(n[0], nextAt, n[2], spb); });
      }
      beat = Math.round((beat + 0.25) * 4) / 4;
      nextAt += spb * 0.25;
      if (beat >= piece.span) {
        beat = 0;
        pick();                       // a different composer next time round
        spb = 60 / piece.bpm;
      }
    }
  }

  function pick() {
    piece = indexed(PIECES[Math.floor(Math.random() * PIECES.length)]);
    // start somewhere inside it, so moving between pages does not sound like
    // the same four bars beginning again and again
    beat = Math.floor(Math.random() * (piece.span * 2)) * 0.5;
  }

  // ---- the song of the day, when the teacher has set one.
  //
  // A real file beats the synthesiser whenever there is one, so the whole
  // school hears the same track that day. The synth stays as the fallback for
  // days nobody has chosen anything.
  var song = null;

  function songEl() {
    if (song || !window.SONG || !window.SONG.url) return song;
    song = new Audio();
    song.loop = true;
    // buffer ahead rather than fetching just in time: the track is small and
    // the round trip to the server is long, so trickling it is what stutters
    song.preload = "auto";
    song.volume = 0.55;
    song.src = window.SONG.url;

    // every page here is a full navigation, so without this the song restarted
    // from the beginning each time a tab was clicked
    var key = "songat:" + window.SONG.url;
    var at = 0;
    try { at = parseFloat(sessionStorage.getItem(key)) || 0; } catch (e) {}
    song.addEventListener("loadedmetadata", function () {
      if (at > 0 && at < song.duration - 1) {
        try { song.currentTime = at; } catch (e) {}
      }
    });
    var wrote = 0;
    song.addEventListener("timeupdate", function () {
      // timeupdate fires several times a second; remembering the place that
      // often is pointless work on the thread that also runs the page
      var t = song.currentTime;
      if (Math.abs(t - wrote) < 5) return;
      wrote = t;
      try { sessionStorage.setItem(key, t); } catch (e) {}
    });

    // A stall is the network being slow, and the cure is to wait. Calling
    // load() here tears the element down and starts it again from nothing,
    // which turns a pause into a restart - much worse than the stall.
    ["stalled", "waiting"].forEach(function (ev) {
      song.addEventListener(ev, function () {
        if (!on || song.paused) return;
        clearTimeout(song._poke);
        song._poke = setTimeout(function () {
          if (!on || song.paused) return;
          var p = song.play();
          if (p && p.catch) { p.catch(function () {}); }
        }, 6000);
      });
    });
    return song;
  }

  function start() {
    if (!on) return;
    var el = songEl();
    if (el) {
      // play() rejects until the visitor has interacted with the page; the
      // first pointerdown below calls straight back in, so this is not an error
      var p = el.play();
      if (p && p.catch) { p.catch(function () {}); }
      return;
    }
    if (!ensure(start)) return;      // called back once the context is awake
    if (!piece) pick();
    if (!timer) {
      nextAt = ac.currentTime + 0.08;
      timer = setInterval(schedule, 60);
      schedule();
    }
  }

  function stop() {
    if (song) { song.pause(); clearTimeout(song._poke); }
    if (timer) { clearInterval(timer); timer = null; }
    piece = null;
  }

  function paint() {
    var b = document.getElementById("musicbtn");
    if (b) {
      var name = window.SONG && window.SONG.name;
      b.textContent = on ? "♪" : "♪̸";
      b.title = (name ? name + " — " : "") +
                (on ? "playing, click to silence" : "click to play");
      b.className = "musicbtn" + (on ? " on" : "");
    }
    var t = document.getElementById("songname");
    if (t) {
      var n = window.SONG && window.SONG.name;
      t.textContent = n || "";
      t.hidden = !n;
      t.className = "songname" + (on ? " on" : "");
    }
  }

  window.Music = {
    toggle: function () {
      on = !on;
      try { localStorage.setItem("music", on ? "on" : "off"); } catch (e) {}
        if (on) { if (!songEl()) { pick(); } start(); } else stop();
      paint();
    },
    nudge: function () { if (on) start(); },      // called on the first click
    state: function () {
      return {on: on, audio: ac ? ac.state : "none",
              song: window.SONG ? window.SONG.name : null,
              piece: piece ? piece.name : "none",
              playing: song ? !song.paused : !!timer};
    }
  };

  document.addEventListener("DOMContentLoaded", paint);
  // browsers refuse sound until somebody interacts, so wait for that
  ["pointerdown", "keydown"].forEach(function (ev) {
    document.addEventListener(ev, function once() {
      document.removeEventListener(ev, once);
      start();
    }, {once: true});
  });
})();
