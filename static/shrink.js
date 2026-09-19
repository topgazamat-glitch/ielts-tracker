/* -------------------------------------------- shrink a photo before sending it
 * A page photographed on a phone arrives at two and a half megabytes, and the
 * teacher reads it on a screen. Nine hundred of them filled the server's disk
 * and none could ever be let go, because a photo sent from the web has no copy
 * anywhere else.
 *
 * So the browser does the work: the picture is drawn onto a canvas at a size
 * that is still comfortably readable, and sent as a smaller JPEG. The page
 * stays legible - 1600px across is more than a screen shows - and costs about
 * a tenth of what it did.
 *
 * If anything here fails, the original file is sent exactly as before.
 */
(function () {
  const MAX_EDGE = 1600;
  const QUALITY = 0.82;
  const WORTH_IT = 400 * 1024;      // leave small files alone

  const form = document.querySelector('form[action$="/upload"]');
  if (!form || !window.FileReader || !document.createElement("canvas").toBlob) return;
  const input = form.querySelector('input[type=file][name=photo]');
  const button = form.querySelector("button");
  if (!input) return;

  function shrink(file) {
    return new Promise((resolve) => {
      if (!file.type.startsWith("image/") || file.size < WORTH_IT) {
        resolve(file);
        return;
      }
      const url = URL.createObjectURL(file);
      const img = new Image();
      img.onload = () => {
        try {
          const scale = Math.min(1, MAX_EDGE / Math.max(img.width, img.height));
          if (scale === 1) { URL.revokeObjectURL(url); resolve(file); return; }
          const c = document.createElement("canvas");
          c.width = Math.round(img.width * scale);
          c.height = Math.round(img.height * scale);
          c.getContext("2d").drawImage(img, 0, 0, c.width, c.height);
          c.toBlob((blob) => {
            URL.revokeObjectURL(url);
            // never send something larger than what we started with
            resolve(blob && blob.size < file.size
              ? new File([blob], file.name.replace(/\.[^.]+$/, "") + ".jpg",
                         {type: "image/jpeg"})
              : file);
          }, "image/jpeg", QUALITY);
        } catch (e) {
          URL.revokeObjectURL(url);
          resolve(file);
        }
      };
      img.onerror = () => { URL.revokeObjectURL(url); resolve(file); };
      img.src = url;
    });
  }

  let busy = false;
  form.addEventListener("submit", async (e) => {
    if (busy || !input.files.length) return;
    e.preventDefault();
    busy = true;
    const was = button ? button.textContent : "";
    if (button) { button.disabled = true; button.textContent = "Preparing…"; }
    try {
      const body = new FormData(form);
      body.delete("photo");
      for (const file of input.files) {
        body.append("photo", await shrink(file));
      }
      const r = await fetch(form.action, {method: "POST", body});
      window.location.href = r.redirected ? r.url : window.location.href;
    } catch (err) {
      // anything at all goes wrong: send it the old way
      busy = false;
      if (button) { button.disabled = false; button.textContent = was; }
      form.submit();
    }
  });
})();
