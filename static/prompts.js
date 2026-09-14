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

    btn.addEventListener("click", function () {
      var level = document.getElementById("sug_level").value;
      var kind = document.getElementById("sug_kind").value;
      var box = document.querySelector('textarea[name="prompt"]');
      if (!box) return;
      var was = btn.textContent;
      btn.textContent = "…";
      btn.disabled = true;
      fetch("/prompts/suggest?level=" + encodeURIComponent(level) +
            "&kind=" + encodeURIComponent(kind), {cache: "no-store"})
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
