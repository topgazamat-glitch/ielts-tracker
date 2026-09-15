/* ------------------------------------------- the booklet keeps what is typed
 * A hundred boxes, filled in on a phone, where a call or a flat battery is
 * ordinary. Everything typed is sent back every few seconds and whenever the
 * page is hidden, so closing the tab costs nothing. Nothing is marked until
 * the paper is handed in.
 */
(function () {
  const form = document.querySelector("form[data-save]");
  if (!form) return;
  const where = form.getAttribute("data-save");
  const note = document.getElementById("booksaved");
  const boxes = [...form.querySelectorAll("input.bk-blank")];
  if (!boxes.length) return;

  let dirty = false, sending = false;
  const last = new Map(boxes.map((b) => [b.name, b.value]));

  function changed() {
    const out = [];
    boxes.forEach((b) => {
      if (b.value !== last.get(b.name)) out.push(b);
    });
    return out;
  }

  async function save(useBeacon) {
    const mine = changed();
    if (!mine.length || sending) return;
    const body = new URLSearchParams();
    mine.forEach((b) => body.append(b.name, b.value));
    mine.forEach((b) => last.set(b.name, b.value));
    dirty = false;
    if (useBeacon && navigator.sendBeacon) {
      // the page is going away; a beacon still gets there
      navigator.sendBeacon(where, body);
      return;
    }
    sending = true;
    if (note) note.textContent = "saving…";
    try {
      await fetch(where, {
        method: "POST",
        headers: {"Content-Type": "application/x-www-form-urlencoded"},
        body: body.toString(),
      });
      if (note) note.textContent = "saved";
    } catch (e) {
      mine.forEach((b) => last.set(b.name, null));   // try again next time
      if (note) note.textContent = "not saved — check your connection";
    } finally {
      sending = false;
    }
  }

  form.addEventListener("input", (e) => {
    if (!e.target.classList.contains("bk-blank")) return;
    dirty = true;
    if (note) note.textContent = "…";
  });
  form.addEventListener("focusout", (e) => {
    if (e.target.classList.contains("bk-blank")) save(false);
  });
  setInterval(() => { if (dirty) save(false); }, 5000);
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") save(true);
  });
  window.addEventListener("pagehide", () => save(true));
  form.addEventListener("submit", () => { dirty = false; });
})();
