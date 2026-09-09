/* Finding a name among fifty-seven, and doing one thing to several at once.
 *
 * The search box also submits to the server, so this only makes it instant
 * rather than making it work; with scripting off the page is unchanged.
 */
(function () {
  function rows() {
    var t = document.getElementById("roster");
    return t ? Array.prototype.slice.call(t.rows, 1) : [];
  }

  function filter() {
    var box = document.getElementById("rq");
    if (!box) return;
    var q = box.value.trim().toLowerCase();
    rows().forEach(function (tr) {
      var cell = tr.cells[1];
      var name = cell ? cell.textContent.toLowerCase() : "";
      tr.hidden = q && name.indexOf(q) < 0;
    });
  }

  function counted() {
    var picks = document.querySelectorAll(".pick:checked");
    var bar = document.getElementById("bulkbar");
    var n = document.getElementById("npicked");
    if (n) n.textContent = picks.length;
    if (bar) bar.hidden = picks.length === 0;
  }

  function wire() {
    var box = document.getElementById("rq");
    if (box && !box.dataset.wired) {
      box.dataset.wired = "1";
      box.addEventListener("input", filter);
      // a live list makes the button redundant, so Enter must not reload
      var form = box.form;
      if (form) {
        form.addEventListener("submit", function (e) {
          if (rows().some(function (tr) { return !tr.hidden; })) e.preventDefault();
        });
      }
    }
    var all = document.getElementById("pickall");
    if (all && !all.dataset.wired) {
      all.dataset.wired = "1";
      all.addEventListener("change", function () {
        rows().forEach(function (tr) {
          if (tr.hidden) return;
          var c = tr.querySelector(".pick");
          if (c) c.checked = all.checked;
        });
        counted();
      });
    }
    document.querySelectorAll(".pick").forEach(function (c) {
      if (c.dataset.wired) return;
      c.dataset.wired = "1";
      c.addEventListener("change", counted);
    });
    counted();
  }

  document.addEventListener("DOMContentLoaded", wire);
  document.addEventListener("pageswap", wire);
  wire();
})();
