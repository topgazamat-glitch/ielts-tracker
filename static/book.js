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
  // Handing in an empty paper spends the sitting that counts. A student who
  // opened the booklet to look at it, and pressed the button to see what it
  // did, had a nought against their name for the season.
  form.addEventListener("submit", (e) => {
    const empty = boxes.filter((b) => !(b.value || "").trim()).length;
    if (empty > boxes.length / 2) {
      const ok = window.confirm(
        empty === boxes.length
          ? "You have not answered anything yet. Hand it in blank?"
          : empty + " of " + boxes.length + " boxes are still empty. "
            + "Hand it in anyway?");
      if (!ok) { e.preventDefault(); return; }
    }
    dirty = false;
  });
})();

/* ------------------------------------------------------- sitting it as an exam
 * A clock that does not stop, and a paper that hands itself in when the time
 * is up. Where the teacher has asked for it, leaving the page hands it in too:
 * that is the rule of the room, and the student is told before they start, on
 * the page and again the moment they are about to break it.
 *
 * Everything typed is already being saved every few seconds, so a paper handed
 * in by the clock is the paper as it stood, not an empty one.
 */
(function () {
  const form = document.querySelector('form[data-minutes]');
  if (!form) return;
  const minutes = parseInt(form.getAttribute("data-minutes") || "0", 10);
  if (!minutes) return;
  const strict = form.getAttribute("data-strict") === "1";
  const clock = document.getElementById("exclock");
  let left = parseInt(form.getAttribute("data-left") || "", 10);
  if (isNaN(left)) left = minutes * 60;
  let over = false;

  function handIn(why) {
    if (over) return;
    over = true;
    let field = form.querySelector('input[name="ended"]');
    if (!field) {
      field = document.createElement("input");
      field.type = "hidden";
      field.name = "ended";
      form.appendChild(field);
    }
    field.value = why;
    form.submit();
  }

  function paint() {
    if (!clock) return;
    const m = Math.floor(Math.max(0, left) / 60);
    const s = Math.max(0, left) % 60;
    clock.textContent = m + ":" + (s < 10 ? "0" : "") + s;
    clock.classList.toggle("soon", left <= 300);
    clock.classList.toggle("nearly", left <= 60);
  }

  paint();
  setInterval(function () {
    left -= 1;
    paint();
    if (left <= 0) handIn("time");
  }, 1000);

  if (strict) {
    // A tap on a notification is not cheating, so say what is about to happen
    // rather than ending the paper without a word.
    window.addEventListener("blur", function () {
      if (!over) handIn("left");
    });
    document.addEventListener("visibilitychange", function () {
      if (document.visibilityState === "hidden" && !over) handIn("left");
    });
  }
})();
