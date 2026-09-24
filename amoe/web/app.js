const chooseBtn = document.getElementById("choose");
const fileInput = document.getElementById("file");
const sampleBtn = document.getElementById("sample");
const runBtn = document.getElementById("run");
const galleryBtn = document.getElementById("gallery");
const lens = document.getElementById("lens");
const paint = document.getElementById("paint");
const lift = document.getElementById("lift");
const geom = document.getElementById("geom");
const fname = document.getElementById("fname");
const status = document.getElementById("status");
const density = document.getElementById("density");
const result = document.getElementById("result");
const caption = document.getElementById("caption");
const preview = document.getElementById("preview");

let sourceFile = null;
let previewUrl = "";

function setStatus(text) {
  status.textContent = text;
}

function remember(file) {
  sourceFile = file;
  fname.textContent = file ? file.name : "No page yet.";
  const ready = Boolean(file);
  runBtn.disabled = !ready;
  galleryBtn.disabled = !ready;
}

chooseBtn.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", () => remember(fileInput.files && fileInput.files[0]));

sampleBtn.addEventListener("click", async () => {
  setStatus("Loading a sample page…");
  try {
    const res = await fetch("/api/sample");
    if (!res.ok) {
      setStatus("The sample page did not load. Choose a PNG or JPEG instead.");
      return;
    }
    const blob = await res.blob();
    remember(new File([blob], "sample-page.png", { type: "image/png" }));
    setStatus("Sample page ready. Color it when you want.");
  } catch (err) {
    setStatus("The sample page did not load. Choose a PNG or JPEG instead.");
  }
});

function paintLabel() {
  return paint.value === "engine" ? "engine membership" : "wheel plate";
}

function showImage(blob, title) {
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  previewUrl = URL.createObjectURL(blob);
  preview.src = previewUrl;
  caption.textContent = title;
  result.hidden = false;
}

async function postPage(url) {
  const body = new FormData();
  body.append("file", sourceFile, sourceFile.name || "page.png");
  body.append("mode", lens.value);
  body.append("paint", paint.value);
  body.append("lift", lift.checked ? "1" : "0");
  body.append("geom", geom.checked ? "1" : "0");
  return fetch(url, { method: "POST", body });
}

function readDensity(res) {
  const tazel = res.headers.get("X-Amoe-Tazel-Inband");
  const vyrn = res.headers.get("X-Amoe-Vyrn-Inband");
  if (!tazel && !vyrn) {
    density.textContent = "";
    return;
  }
  density.textContent = "Densitometry — Tazel in-band " + tazel + "%, Vyrn in-band " + vyrn + "%.";
}

function refuseLine(code) {
  if (!code) return "";
  if (code.indexOf("AMOE-WEAK-SIGNAL") !== -1) return " Weak reading. Nothing was invented.";
  return " " + code;
}

runBtn.addEventListener("click", async () => {
  if (!sourceFile) return;
  runBtn.disabled = true;
  setStatus("Coloring…");
  try {
    const res = await postPage("/api/color");
    if (!res.ok) {
      let message = "That page could not be colored. Try a PNG or JPEG.";
      try {
        const err = await res.json();
        if (err.message) message = err.message;
      } catch (_) {}
      setStatus(message);
      return;
    }
    showImage(await res.blob(), lens.options[lens.selectedIndex].text + " · " + paintLabel());
    readDensity(res);
    setStatus("Colored with the " + lens.value + " " + paintLabel() + "." + refuseLine(res.headers.get("X-Amoe-Refuse") || ""));
  } catch (err) {
    setStatus("That page could not be colored. Try a PNG or JPEG.");
  } finally {
    runBtn.disabled = !sourceFile;
  }
});

galleryBtn.addEventListener("click", async () => {
  if (!sourceFile) return;
  galleryBtn.disabled = true;
  setStatus("Making the wheel sheet…");
  try {
    const res = await postPage("/api/gallery");
    if (!res.ok) {
      setStatus("The wheel sheet needs a PNG or JPEG page.");
      return;
    }
    showImage(await res.blob(), "Wheel sheet");
    density.textContent = "";
    setStatus("Wheel sheet ready.");
  } catch (err) {
    setStatus("The wheel sheet needs a PNG or JPEG page.");
  } finally {
    galleryBtn.disabled = !sourceFile;
  }
});
