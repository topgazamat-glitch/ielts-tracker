/* The Section list depends on the Collection chosen above it.
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

  function wire() {
    var coll = document.getElementById("coll");
    if (!coll || coll.dataset.wired) return;
    coll.dataset.wired = "1";
    coll.addEventListener("change", fill);
    fill();
  }

  document.addEventListener("DOMContentLoaded", wire);
  document.addEventListener("pageswap", wire);   // after a swapped navigation
  wire();
})();
