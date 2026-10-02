/* The class recording, played on the page where it is needed.
 *
 * A listening section carries a Listen button where the booklet names its
 * track. Once it is playing, a small player stays under the top bar while the
 * student scrolls down to the questions, so they can answer as they listen
 * and go back five seconds without scrolling up again. One recording plays at
 * a time, the background music keeps quiet while it does, and leaving the
 * page stops it.
 */
(function () {
  var audio = null, card = null, dock = null, seen = true, closed = false, watch = null;

  function clock(t) {
    t = Math.max(0, Math.floor(t || 0));
    return Math.floor(t / 60) + ":" + ("0" + (t % 60)).slice(-2);
  }

  function hush(on) {
    if (window.Music && window.Music.hush) window.Music.hush(on);
  }

  function makeDock() {
    if (dock) return dock;
    var top = document.querySelector(".topbar") || document.querySelector("header.top");
    if (!top) return null;
    dock = document.createElement("div");
    dock.className = "lx lx-dock";
    dock.hidden = true;
    dock.innerHTML = card.querySelector(".lx-play").outerHTML +
      '<div class="lx-mid"><span class="lx-row"><span class="lx-label"></span>' +
      '<span class="lx-time"></span></span>' +
      card.querySelector(".lx-bar").outerHTML + "</div>" +
      card.querySelector(".lx-back").outerHTML +
      '<button type="button" class="lx-close" aria-label="Stop the recording">' +
      '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg></button>';
    top.appendChild(dock);
    return dock;
  }

  function paint() {
    if (!card || !audio) return;
    var d = audio.duration, t = audio.currentTime;
    var share = d ? Math.min(100, 100 * t / d) : 0;
    var playing = !audio.paused && !audio.ended;
    [card, dock].forEach(function (el) {
      if (!el) return;
      el.classList.toggle("on", playing);
      el.querySelector(".lx-bar i").style.width = share + "%";
      el.querySelector(".lx-bar").setAttribute("aria-valuenow", Math.round(share));
      el.querySelector(".lx-time").textContent = clock(t) + (d ? " / " + clock(d) : "");
      el.querySelector(".lx-play").setAttribute("aria-label",
        (playing ? "Pause" : "Play") + " track " + card.getAttribute("data-track"));
    });
    // the small player: once something has played, while the button is out of sight
    if (dock) dock.hidden = seen || closed || (audio.paused && !audio.currentTime);
  }

  function stop() {
    if (audio) { audio.pause(); }
    hush(false);
  }

  // a different Listen button: the one before stops where it is
  function take(el) {
    if (card === el && audio) return audio;
    stop();
    if (card) card.classList.remove("on");
    card = el;
    audio = new Audio();
    audio.preload = "auto";
    audio.src = el.getAttribute("data-src");
    ["timeupdate", "loadedmetadata", "play", "pause", "ended"].forEach(function (ev) {
      audio.addEventListener(ev, paint);
    });
    audio.addEventListener("pause", function () { hush(false); });
    audio.addEventListener("ended", function () { hush(false); });
    audio.addEventListener("error", function () {
      el.querySelector(".lx-time").textContent = "Could not load";
      hush(false);
    });
    if (dock) { dock.remove(); dock = null; }
    makeDock();
    if (dock) dock.querySelector(".lx-label").textContent =
      el.getAttribute("data-label") || "Track " + el.getAttribute("data-track");
    // the small player shows only while the button itself is off the screen
    if (watch) watch.disconnect();
    seen = true;
    if (window.IntersectionObserver) {
      watch = new IntersectionObserver(function (entries) {
        seen = entries[0].isIntersecting;
        paint();
      }, {rootMargin: "-60px 0px 0px 0px"});
      watch.observe(el);
    }
    return audio;
  }

  function toggle(el) {
    var a = take(el);
    if (a.paused || a.ended) {
      closed = false;
      hush(true);
      var p = a.play();
      if (p && p.catch) p.catch(function () { hush(false); paint(); });
    } else {
      a.pause();
    }
  }

  function seek(bar, x) {
    if (!audio || !audio.duration) return;
    var r = bar.getBoundingClientRect();
    audio.currentTime = Math.max(0, Math.min(1, (x - r.left) / r.width)) * audio.duration;
    paint();
  }

  // the music would otherwise start on this very tap, for the first tap on a page
  document.addEventListener("pointerdown", function (e) {
    var b = e.target.closest && e.target.closest(".lx-play");
    if (b && (!audio || audio.paused)) hush(true);
  }, true);

  document.addEventListener("click", function (e) {
    var t = e.target.closest ? e.target.closest(".lx-play, .lx-back, .lx-close, .lx-bar") : null;
    if (!t) return;
    var box = t.closest(".lx");
    var el = box.classList.contains("lx-dock") ? card : box;
    if (!el) return;
    if (t.classList.contains("lx-play")) { toggle(el); return; }
    if (t.classList.contains("lx-close")) {
      closed = true;
      stop();
      if (audio) audio.currentTime = 0;
      paint();
      return;
    }
    var a = take(el);
    if (t.classList.contains("lx-back")) {
      a.currentTime = Math.max(0, a.currentTime - 5);
      paint();
      return;
    }
    seek(t, e.clientX);
  });

  document.addEventListener("keydown", function (e) {
    var bar = e.target.classList && e.target.classList.contains("lx-bar") ? e.target : null;
    if (!bar || !audio || (e.key !== "ArrowLeft" && e.key !== "ArrowRight")) return;
    e.preventDefault();
    audio.currentTime = Math.max(0, audio.currentTime + (e.key === "ArrowLeft" ? -5 : 5));
    paint();
  });

  // another page: the recording and its player go with the old one
  document.addEventListener("pageswap", function () {
    stop();
    if (watch) watch.disconnect();
    if (dock) dock.remove();
    audio = card = dock = watch = null;
    seen = true;
    closed = false;
  });
})();
