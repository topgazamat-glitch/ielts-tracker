/* "Suggest a question" on the assignment form.
 *
 * The site has no model behind it, so nothing is invented here: it asks the
 * question bank for the least-used question at that level and kind, and drops
 * it into the box where it can be edited before anyone sees it.
 */
(function () {
  function wire() {
    var btn = document.getElementById("suggest");
    if (!btn || btn.dataset.wired) return;
    btn.dataset.wired = "1";

    var levelBox = document.getElementById("sug_level");
    var unitBox = document.getElementById("sug_unit");

    // which units of this level have a writing lesson, and what it is about
    function loadUnits() {
      if (!levelBox || !unitBox) return;
      fetch("/prompts/units?level=" + encodeURIComponent(levelBox.value),
            {cache: "no-store"})
        .then(function (r) { return r.json(); })
        .then(function (d) {
          unitBox.innerHTML = '<option value="">any unit</option>';
          (d.units || []).forEach(function (u) {
            var o = document.createElement("option");
            o.value = u.unit;
            o.textContent = "Unit " + u.unit + (u.topic ? " — " + u.topic : "");
            if (u.lesson) o.title = "taught in " + u.lesson;
            unitBox.appendChild(o);
          });
          unitBox.disabled = !(d.units || []).length;
          if (unitBox.dataset.want) unitBox.value = unitBox.dataset.want;
        })
        .catch(function () {});
    }
    if (levelBox) {
      levelBox.addEventListener("change", loadUnits);
      loadUnits();
    }

    btn.addEventListener("click", function () {
      var level = document.getElementById("sug_level").value;
      var kind = document.getElementById("sug_kind").value;
      var box = document.querySelector('textarea[name="prompt"]');
      if (!box) return;
      var was = btn.textContent;
      btn.textContent = "…";
      btn.disabled = true;
      var unit = unitBox ? unitBox.value : "";
      fetch("/prompts/suggest?level=" + encodeURIComponent(level) +
            "&kind=" + encodeURIComponent(kind) +
            (unit ? "&unit=" + encodeURIComponent(unit) : ""), {cache: "no-store"})
        .then(function (r) { return r.json(); })
        .then(function (d) {
          btn.textContent = was;
          btn.disabled = false;
          if (!d.ok) {
            btn.textContent = d.why || "nothing for that yet";
            setTimeout(function () { btn.textContent = was; }, 2500);
            return;
          }
          box.value = d.text;
          box.focus();
          if (d.where) {
            btn.textContent = d.where.slice(0, 34);
            setTimeout(function () { btn.textContent = was; }, 3000);
          }
          // the level's usual length and timing, unless something is typed already
          var words = document.querySelector('input[name="min_words"]');
          var mins = document.querySelector('input[name="minutes"]');
          if (words && !words.value && d.min_words) words.value = d.min_words;
          if (mins && !mins.value && d.minutes) mins.value = d.minutes;
        })
        .catch(function () {
          btn.textContent = was;
          btn.disabled = false;
        });
    });
  }
  document.addEventListener("DOMContentLoaded", wire);
  document.addEventListener("pageswap", wire);
  wire();
})();

/* ------------------------------------------------- a unit's homework, in the form
 *
 * Picking the unit and the lessons fills the form in: the workbook line, the
 * Destination unit remembered for that unit, and the handout from the class's
 * shelf. Lines the teacher has typed over are left alone, and a Destination
 * unit typed in the box goes straight into the lines.
 */
(function () {
  function wire() {
    const unit = document.getElementById("u_unit");
    if (!unit || unit.dataset.wired) return;
    unit.dataset.wired = "1";
    const $ = (id) => document.getElementById(id);
    const form = unit.form;
    const items = $("u_items"), dest = $("u_dest"), pair = $("u_pair"), note = $("u_note");
    const group = form.querySelector("select[name=group_id]");
    let auto = items.value;        // what was last filled in, so typing over it is respected
    let plan = null, picked = false, where = "";

    function lines() {
      const out = [];
      (plan ? plan.items : []).forEach((i) => {
        if (i.kind === "destination") return;           // the box says it, below
        if (i.kind === "booklet" && picked) return;     // the handout box says it
        out.push(i.title);
        if (i.kind === "workbook" && (dest.value || "").trim()) out.push(dest.value.trim());
      });
      return out.join("\n");
    }
    function write() {
      if (items.value.trim() && items.value !== auto) {
        note.textContent = "Your own lines are kept. Empty the box to have it filled in again.";
        return;
      }
      items.value = auto = lines();
    }
    async function fill() {
      const u = (unit.value || "").trim();
      if (!u) return;
      const q = new URLSearchParams({group_id: group.value, unit: u, pair: pair.value, kind: "none"});
      try {
        const r = await fetch("/assignments/unit.json?" + q.toString(), {cache: "no-store"});
        plan = await r.json();
        if (!plan.items) return;
        // a new unit (or class) brings its own Destination unit; new lessons keep the one typed
        const key = group.value + ":" + u;
        if (key !== where || !(dest.value || "").trim()) dest.value = plan.destination || "";
        where = key;
        if (typeof handoutsForLevel === "function") handoutsForLevel();
        const shelf = $("hwhandout");
        const book = plan.items.find((i) => i.kind === "booklet");
        const box = shelf && book && book.test_id &&
                    shelf.querySelector('fieldset:not([hidden]) input[value="' + book.test_id + '"]');
        // the unit's handout is ticked; one ticked for the last unit chosen is let go,
        // and any the teacher ticked by hand stay
        if (shelf && shelf.dataset.auto && shelf.dataset.auto !== String(book && book.test_id)) {
          const was = shelf.querySelector('input[value="' + shelf.dataset.auto + '"]');
          if (was) was.checked = false;
        }
        picked = !!box;
        if (box) { box.checked = true; shelf.dataset.auto = String(book.test_id); }
        write();
        const destOn = plan.items.some((i) => i.kind === "destination" && i.test_id);
        const wbOn = plan.items.some((i) => i.kind === "workbook" && i.test_id);
        note.textContent = (picked
          ? "Filled in. Students do the handout on the site, or send photos of the paper."
          : "Filled in. There is no digital handout for this unit yet, so it is a line to tick.")
          + (wbOn ? " The workbook unit is on the site too." : "")
          + (destOn ? " The Destination unit is on the site too." : "");
        // the writing question's level and unit, already chosen
        const lvl = group.selectedOptions[0] && group.selectedOptions[0].getAttribute("data-level-name");
        const sl = $("sug_level"), su = $("sug_unit");
        if (sl && lvl && sl.value !== lvl) { sl.value = lvl; sl.dispatchEvent(new Event("change")); }
        if (su) { su.dataset.want = u; su.value = u; }
      } catch (e) { /* the form stays as it was */ }
    }
    unit.addEventListener("change", fill);
    pair.addEventListener("change", fill);
    group.addEventListener("change", () => { if ((unit.value || "").trim()) fill(); });
    dest.addEventListener("input", () => { if (plan) write(); });
    // a Destination unit on the site, put in the box with a tap
    form.querySelectorAll(".destpick").forEach((b) => b.addEventListener("click", () => {
      dest.value = b.getAttribute("data-dest");
      if (plan) write();
      else if (!(items.value || "").trim()) items.value = auto = dest.value;
      note.textContent = dest.value + " is on the site: students do it there, or send photos of the pages.";
    }));
  }
  document.addEventListener("DOMContentLoaded", wire);
  document.addEventListener("pageswap", wire);
  wire();
})();

/* ------------------------------------------------- the handout to open
 * Only the handouts on the chosen class's level are offered; changing the
 * class changes the list.
 */
function handoutsForLevel() {
  const box = document.getElementById("hwhandout");
  if (!box) return;
  const group = box.closest("form").querySelector('select[name="group_id"]');
  const lv = group.options[group.selectedIndex].getAttribute("data-level");
  box.querySelectorAll("fieldset").forEach((fs) => {
    const mine = !lv || fs.getAttribute("data-level") === lv;
    fs.hidden = !mine;
    // a handout of another level cannot be set to this class: untick it
    if (!mine) fs.querySelectorAll("input:checked").forEach((c) => { c.checked = false; });
  });
}
document.addEventListener("change", (e) => {
  if (e.target.name === "group_id") handoutsForLevel();
});
document.addEventListener("pageswap", handoutsForLevel);
handoutsForLevel();
