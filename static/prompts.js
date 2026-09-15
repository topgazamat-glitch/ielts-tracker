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

/* ------------------------------------------------- a unit's homework, in one go
 * The four things a unit always needs were being typed by hand every week, and
 * the writing question was then typed a second time to make it digital. This
 * asks the server what that unit's homework is - the booklet is already on the
 * shelf, the question is already in the bank - and fills the form in.
 */
(function () {
  const build = document.getElementById("u_build");
  if (!build) return;
  const $ = (id) => document.getElementById(id);

  build.addEventListener("click", async () => {
    const unit = ($("u_unit").value || "").trim();
    const note = $("u_note");
    if (!unit) { note.textContent = "Which unit?"; return; }
    build.disabled = true;
    note.textContent = "Looking…";
    try {
      const q = new URLSearchParams({
        group_id: $("u_group").value, unit: unit,
        pair: $("u_pair").value, kind: $("u_kind").value,
        practice: ($("u_practice").value || "").trim(),
      });
      const r = await fetch("/assignments/unit.json?" + q.toString());
      const plan = await r.json();
      const items = plan.items || [];
      if (!items.length) { note.textContent = "Nothing found for that unit."; return; }

      const form = document.querySelector('form[action="/assignments/list"]');
      form.querySelector('select[name=group_id]').value = $("u_group").value;
      form.querySelector('textarea[name=items]').value =
        items.map((i) => i.title).join("\n");

      const writing = items.find((i) => i.kind === "writing");
      const promptBox = form.querySelector('textarea[name=prompt]');
      if (writing && writing.prompt && promptBox) {
        promptBox.value = writing.prompt;
        const details = promptBox.closest("details");
        if (details) details.open = true;
        if (writing.minutes) {
          const m = form.querySelector('input[name=minutes]');
          if (m && !m.value) m.value = writing.minutes;
        }
      }
      const booklet = items.find((i) => i.kind === "booklet");
      note.textContent = booklet && booklet.test_id
        ? "Ready. The handout is on the site, so that line opens the booklet itself."
        : "Ready. No digital handout for that unit yet — that line is just a note.";
    } catch (e) {
      note.textContent = "Could not build it.";
    } finally {
      build.disabled = false;
    }
  });
})();
