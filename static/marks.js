/* Marking a lesson: start everyone somewhere, change who was different.
 *
 * The three marks a student gets are almost always the same number, so one tap
 * sets all three and "split" opens them separately for the student who was late
 * but worked well. The presets and "same as last lesson" exist because the
 * fastest honest answer for most of a class is "the same as usual".
 */
(function () {
  var FIELDS = ["punctuality", "behaviour", "participation"];

  function field(sid, name) {
    return document.getElementById("f_" + name + "_" + sid);
  }

  function setAll(sid, value) {
    FIELDS.forEach(function (f) {
      var el = field(sid, f);
      if (el) el.value = value === null ? "" : value;
    });
    paint(sid);
  }

  function setOne(sid, name, value) {
    var el = field(sid, name);
    if (el) el.value = value === null ? "" : value;
    paint(sid);
  }

  function values(sid) {
    return FIELDS.map(function (f) {
      var el = field(sid, f);
      return el && el.value !== "" ? +el.value : null;
    });
  }

  function paint(sid) {
    var v = values(sid);
    var same = v[0] !== null && v.every(function (x) { return x === v[0]; });
    var row = document.querySelector('tr[data-sid="' + sid + '"]');
    if (!row) return;
    row.querySelectorAll(".mk").forEach(function (b) {
      var want = b.getAttribute("data-v");
      var f = b.getAttribute("data-field");
      if (f) {
        var i = FIELDS.indexOf(f);
        b.classList.toggle("on", want !== "" && v[i] === +want);
      } else if (want === "") {
        b.classList.toggle("on", v.every(function (x) { return x === null; }));
      } else {
        b.classList.toggle("on", same && v[0] === +want);
      }
    });
    // a student marked unevenly should show it without opening the split
    row.classList.toggle("mixed", !same && v.some(function (x) { return x !== null; }));
    count();
  }

  function count() {
    var rows = document.querySelectorAll("#marks tr[data-sid]");
    var done = 0;
    rows.forEach(function (r) {
      var v = values(r.getAttribute("data-sid"));
      if (v.some(function (x) { return x !== null; })) done++;
    });
    var el = document.getElementById("markcount");
    if (el) {
      el.textContent = done + " of " + rows.length + " marked";
    }
  }

  function eachRow(fn) {
    document.querySelectorAll("#marks tr[data-sid]").forEach(function (r) {
      fn(r, r.getAttribute("data-sid"));
    });
  }

  function wire() {
    var table = document.getElementById("marks");
    if (!table || table.dataset.wired) return;
    table.dataset.wired = "1";

    table.addEventListener("click", function (e) {
      var b = e.target;
      if (b.classList.contains("split")) {
        e.preventDefault();
        var d = document.getElementById("d_" + b.getAttribute("data-sid"));
        if (d) d.hidden = !d.hidden;
        return;
      }
      if (!b.classList.contains("mk")) return;
      e.preventDefault();
      var sid = b.getAttribute("data-sid");
      var raw = b.getAttribute("data-v");
      var value = raw === "" ? null : +raw;
      var f = b.getAttribute("data-field");
      if (f) { setOne(sid, f, value); } else { setAll(sid, value); }
    });

    document.querySelectorAll(".preset").forEach(function (p) {
      p.addEventListener("click", function (e) {
        e.preventDefault();
        var v = +p.getAttribute("data-all");
        eachRow(function (_r, sid) { setAll(sid, v); });
      });
    });

    var clear = document.getElementById("clearall");
    if (clear) clear.addEventListener("click", function (e) {
      e.preventDefault();
      eachRow(function (_r, sid) { setAll(sid, null); });
    });

    var last = document.getElementById("copylast");
    if (last) last.addEventListener("click", function (e) {
      e.preventDefault();
      eachRow(function (r, sid) {
        var was = (r.getAttribute("data-last") || "").split(",");
        if (was.length !== 3 || was[0] === "") return;
        FIELDS.forEach(function (f, i) {
          var el = field(sid, f);
          if (el) el.value = was[i];
        });
        paint(sid);
      });
    });

    eachRow(function (_r, sid) { paint(sid); });
  }

  document.addEventListener("DOMContentLoaded", wire);
  document.addEventListener("pageswap", wire);
  wire();
})();
