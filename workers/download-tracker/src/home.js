/**
 * AMOE download landing.
 * Author: Aziel Eliab. Apache-2.0.
 * Ring hexes are catalog.json ring_cw_from_zero (also amoe/wheel.py RING).
 * Version is pyproject.toml / amoe.__version__. No other version is shown.
 */

const HOST = "https://amoe-spectrallock-download-tracker.vibelock.workers.dev";
const GITHUB_REPO = "https://github.com/AzielEliab/amoe-spectrallock";
const SPECTRAL_REPO = "https://github.com/AzielEliab/spectrallock";
const LICENSE = "https://www.apache.org/licenses/LICENSE-2.0";
const VERSION = "1.3.0";
const SPECTRAL_VERSION = "0.3.1";
const AUTHOR = "Aziel Eliab";
const TITLE = "AMOE — Aziel Eliab";
const PRODUCT = "AMOE";
export const DEFAULT_ASSET = "amoe-spectrallock-1.3.0.tar.gz";
const INSTALL_LINE = `curl -fsSL ${HOST}/install.sh | bash`;
const ONE_LINE = "Wiring on every cell of the SpectralLock 0.3.1 color grid.";
const MOTTO = "Pull what is faded. Color it with the wheel that was defined.";

/** Clockwise from zero. Same order and hexes as catalog.json ring_cw_from_zero. */
export const RING = [
  ["zero", "#2E5A8C"],
  ["chaos", "#7A2E5C"],
  ["vyrn", "#C00066"],
  ["uv", "#C45A2A"],
  ["tazel", "#8A9A2E"],
  ["rosetta", "#2E7A4A"],
];

const FEATURES = [
  "Overlay paints one lens. Grid paints the eleven-lens sheet.",
  "Wheel paint uses the defined hex. Engine paint is the membership hex only.",
  "Gallery, lift, geometry, adapt, and script read the page you give them.",
  "Path audits a card of steps 1–13. A weak page returns AMOE-WEAK-SIGNAL. Empty paper stays empty.",
];

function escapeHtml(value) {
  return String(value == null ? "" : value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function polar(cx, cy, r, deg) {
  const rad = ((deg - 90) * Math.PI) / 180;
  return [cx + r * Math.cos(rad), cy + r * Math.sin(rad)];
}

function wedgePath(cx, cy, r0, r1, a0, a1) {
  const [x0, y0] = polar(cx, cy, r1, a0);
  const [x1, y1] = polar(cx, cy, r1, a1);
  const [x2, y2] = polar(cx, cy, r0, a1);
  const [x3, y3] = polar(cx, cy, r0, a0);
  const large = a1 - a0 > 180 ? 1 : 0;
  const f = (n) => n.toFixed(2);
  return `M ${f(x0)} ${f(y0)} A ${r1} ${r1} 0 ${large} 1 ${f(x1)} ${f(y1)} L ${f(x2)} ${f(y2)} A ${r0} ${r0} 0 ${large} 0 ${f(x3)} ${f(y3)} Z`;
}

export function ringSvg() {
  const cx = 120;
  const cy = 120;
  const r1 = 108;
  const r0 = 64;
  const parts = RING.map(([name, hex], i) => {
    const a0 = i * 60 + 1.6;
    const a1 = (i + 1) * 60 - 1.6;
    return `<path fill="${hex}" d="${wedgePath(cx, cy, r0, r1, a0, a1)}"><title>${escapeHtml(name)} ${hex}</title></path>`;
  });
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" role="img" aria-labelledby="wheel-title">
  <title id="wheel-title">Ring bins clockwise from zero: ${RING.map(([name]) => name).join(", ")}.</title>
  ${parts.join("\n  ")}
</svg>`;
}

function swatchList() {
  return RING.map(
    ([name, hex]) =>
      `<li><span class="swatch" style="background:${hex}"></span><span class="swatch-name">${escapeHtml(name)}</span><span class="swatch-hex">${escapeHtml(hex)}</span></li>`,
  ).join("");
}

function formatBytes(n) {
  if (!Number.isFinite(n) || n <= 0) return "";
  if (n < 1024) return `${n} B`;
  const kb = n / 1024;
  if (kb < 1024) return `${kb >= 10 ? kb.toFixed(0) : kb.toFixed(1)} KB`;
  return `${(kb / 1024).toFixed(1)} MB`;
}

export function citePayload() {
  return {
    author: AUTHOR,
    title: PRODUCT,
    version: VERSION,
    paper: "AMOE-1.3",
    spectral_lock: SPECTRAL_VERSION,
    homepage: HOST + "/",
    github: GITHUB_REPO,
    download: HOST + "/download",
    asset: DEFAULT_ASSET,
    install: HOST + "/install.sh",
    openapi: HOST + "/openapi.json",
    license: "Apache-2.0",
    license_url: LICENSE,
    one_line: ONE_LINE,
    execution: "local",
    how_to_cite: `Eliab, Aziel. (2026). AMOE ${VERSION} [Software]. Apache-2.0. ${GITHUB_REPO}`,
    zenodo_status: "no_doi",
    note: "Local package and catalog fragment. Pigment restore stays on the SpectralLock door. No DOI is invented here.",
  };
}

export function openApi() {
  const path = (summary) => ({ get: { summary, responses: { "200": { description: "OK" } } } });
  return {
    openapi: "3.1.0",
    info: {
      title: "AMOE download tracker",
      version: VERSION,
      description: `${ONE_LINE} Local package ${VERSION}. Author ${AUTHOR}.`,
      license: { name: "Apache-2.0", url: LICENSE },
    },
    servers: [{ url: HOST }],
    paths: {
      "/": path("Product landing"),
      "/download": path(`Counted download of ${DEFAULT_ASSET}`),
      "/count": path("View and download totals"),
      "/stats": path("Totals plus per-repo, per-branch, and fork breakdown"),
      "/install.sh": path("Install script that curls /download"),
      "/cite.json": path("Citation record"),
      "/event": {
        post: {
          summary: "Record a download from another branch or fork",
          responses: { "200": { description: "Counted" } },
        },
      },
    },
  };
}

function sitemapXml() {
  const paths = ["/", "/download", "/install.sh", "/openapi.json", "/cite.json", "/llms.txt"];
  const urls = paths.map((p) => `  <url><loc>${HOST}${p === "/" ? "/" : p}</loc></url>`).join("\n");
  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls}
  <url><loc>${GITHUB_REPO}</loc></url>
</urlset>
`;
}

function robotsTxt() {
  return `User-agent: *
Allow: /

Sitemap: ${HOST}/sitemap.xml
`;
}

function llmsTxt() {
  return `# AMOE

Author: ${AUTHOR}
Version: ${VERSION}
One line: ${ONE_LINE}
Paper: AMOE-1.3
SpectralLock vendored: ${SPECTRAL_VERSION}
GitHub: ${GITHUB_REPO}
Homepage: ${HOST}/
Download: ${HOST}/download
Asset: ${DEFAULT_ASSET}
Install: ${HOST}/install.sh
OpenAPI: ${HOST}/openapi.json
Cite: ${HOST}/cite.json
Execution: local package. Run python3 run.py on the computer where it is installed.
Pigment restore: SpectralLock door (${SPECTRAL_REPO}).
License: Apache-2.0
`;
}

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, HEAD, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Accept, User-Agent",
  };
}

export function handleSeoRoutes(request, url) {
  if (request.method !== "GET" && request.method !== "HEAD") return null;
  const headers = { ...corsHeaders(), "Cache-Control": "private, no-store" };
  if (url.pathname === "/cite.json") {
    return new Response(JSON.stringify(citePayload(), null, 2), {
      status: 200,
      headers: { "Content-Type": "application/json; charset=utf-8", ...headers },
    });
  }
  if (url.pathname === "/openapi.json") {
    return new Response(JSON.stringify(openApi(), null, 2), {
      status: 200,
      headers: { "Content-Type": "application/json; charset=utf-8", ...headers },
    });
  }
  if (url.pathname === "/sitemap.xml") {
    return new Response(sitemapXml(), {
      status: 200,
      headers: { "Content-Type": "application/xml; charset=utf-8", ...headers },
    });
  }
  if (url.pathname === "/robots.txt") {
    return new Response(robotsTxt(), {
      status: 200,
      headers: { "Content-Type": "text/plain; charset=utf-8", ...headers },
    });
  }
  if (url.pathname === "/llms.txt") {
    return new Response(llmsTxt(), {
      status: 200,
      headers: { "Content-Type": "text/plain; charset=utf-8", ...headers },
    });
  }
  if (url.pathname === "/wheel.svg") {
    return new Response(ringSvg(), {
      status: 200,
      headers: { "Content-Type": "image/svg+xml; charset=utf-8", "Cache-Control": "public, max-age=3600", ...corsHeaders() },
    });
  }
  return null;
}

function breakdownList(stats) {
  const rows = Array.isArray(stats.breakdown) ? stats.breakdown : [];
  if (!rows.length) {
    return `<li>No counted downloads yet.</li>`;
  }
  return rows
    .map((row) => {
      const who = `${row.owner}/${row.repo}`;
      const where = row.fork === "1" ? "fork" : "this repo";
      return `<li>${escapeHtml(who)} · ${escapeHtml(row.branch)} · ${where} · ${Number(row.count) || 0}</li>`;
    })
    .join("");
}

export function renderHome(stats) {
  const views = Number(stats.views) || 0;
  const downloads = Number(stats.downloads != null ? stats.downloads : stats.total) || 0;
  const ready = stats.assetReady !== false;
  const size = formatBytes(Number(stats.assetBytes));
  const sizeBit = size ? ` · ${size}` : "";
  const countLine = stats.unbound
    ? "Counter not bound."
    : `Counted downloads: ${downloads.toLocaleString("en-US")}. Page views: ${views.toLocaleString("en-US")}.`;
  const features = FEATURES.map((line) => `<li>${escapeHtml(line)}</li>`).join("");
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${TITLE}</title>
<meta name="description" content="${escapeHtml(ONE_LINE)}">
<meta name="author" content="${AUTHOR}">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#f4f1ea" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#12110f" media="(prefers-color-scheme: dark)">
<link rel="canonical" href="${HOST}/">
<link rel="icon" href="/wheel.svg" type="image/svg+xml">
<style>
  :root {
    color-scheme: light;
    --bg: #f4f1ea;
    --card: #fffcf7;
    --ink: #1b1916;
    --muted: #4e4940;
    --line: #d9d2c4;
    --accent: #6b5310;
    --link: #1e4a78;
    --btn-bg: #1b1916;
    --btn-ink: #f7f4ee;
    --focus: #1e4a78;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      color-scheme: dark;
      --bg: #12110f;
      --card: #1c1b17;
      --ink: #f3eee4;
      --muted: #c9c0b2;
      --line: #3a3428;
      --accent: #e6c56a;
      --link: #f0d78c;
      --btn-bg: #f0e2b6;
      --btn-ink: #1b1916;
      --focus: #f0e2b6;
    }
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; background: var(--bg); color: var(--ink); }
  body {
    font: 1.05rem/1.5 system-ui, "Segoe UI", sans-serif;
    min-height: 100vh;
  }
  a { color: var(--link); }
  a:focus-visible, button:focus-visible, summary:focus-visible {
    outline: 3px solid var(--focus);
    outline-offset: 3px;
  }
  .wrap { max-width: 40rem; margin: 0 auto; padding: 1.25rem 1rem 3rem; }
  .stamp {
    margin: 0 0 .35rem;
    color: var(--accent);
    font: 600 .78rem/1.2 ui-monospace, Menlo, Consolas, monospace;
    letter-spacing: .08em;
    text-transform: uppercase;
  }
  h1 {
    margin: 0;
    font-size: clamp(2.5rem, 10vw, 3.5rem);
    line-height: 1.02;
    letter-spacing: -0.03em;
    font-weight: 640;
  }
  .motto { margin: .7rem 0 0; font-size: 1.2rem; }
  .lede { margin: .45rem 0 0; color: var(--muted); max-width: 36rem; }
  .cta { margin: 1.35rem 0 0; max-width: 22rem; }
  a.download {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 3.25rem;
    padding: .9rem 1.2rem;
    border-radius: 12px;
    background: var(--btn-bg);
    color: var(--btn-ink);
    text-decoration: none;
    font-weight: 700;
    font-size: 1.15rem;
    letter-spacing: .01em;
  }
  a.download:hover { filter: brightness(1.08); }
  .file {
    margin: .7rem 0 0;
    color: var(--muted);
    font: .92rem/1.4 ui-monospace, Menlo, Consolas, monospace;
    word-break: break-all;
  }
  .countline { margin: .85rem 0 0; color: var(--muted); font-size: .95rem; }
  section {
    margin-top: 1.75rem;
    padding-top: 1.25rem;
    border-top: 1px solid var(--line);
  }
  h2 { margin: 0 0 .7rem; font-size: 1.05rem; letter-spacing: .02em; }
  ul.features, ul.swatches, ul.break { margin: 0; padding: 0; list-style: none; }
  ul.features li {
    margin: 0 0 .55rem;
    padding-left: .9rem;
    position: relative;
  }
  ul.features li::before {
    content: "";
    position: absolute;
    left: 0;
    top: .55rem;
    width: .4rem;
    height: .4rem;
    border-radius: 99px;
    background: var(--accent);
  }
  figure { margin: 0; }
  figure svg { width: min(100%, 16rem); height: auto; display: block; }
  figcaption { margin: .7rem 0 .85rem; color: var(--muted); font-size: .95rem; }
  ul.swatches li {
    display: grid;
    grid-template-columns: 1.15rem 6.5rem 1fr;
    gap: .6rem;
    align-items: center;
    margin: 0 0 .4rem;
    font-size: .95rem;
  }
  .swatch {
    width: 1.15rem;
    height: 1.15rem;
    border-radius: 4px;
    border: 1px solid var(--line);
  }
  .swatch-hex {
    font: .88rem/1.2 ui-monospace, Menlo, Consolas, monospace;
    color: var(--muted);
  }
  pre {
    margin: 0;
    padding: .85rem .9rem;
    overflow: auto;
    border-radius: 10px;
    border: 1px solid var(--line);
    background: var(--card);
    color: var(--ink);
    font: .82rem/1.45 ui-monospace, Menlo, Consolas, monospace;
    white-space: pre-wrap;
    word-break: break-all;
  }
  .install-note { margin: .75rem 0 0; color: var(--muted); font-size: .95rem; }
  details { margin-top: 1rem; }
  summary { cursor: pointer; color: var(--link); }
  ul.break li { margin: .35rem 0; color: var(--muted); font-size: .92rem; word-break: break-word; }
  footer {
    margin-top: 2rem;
    color: var(--muted);
    font-size: .9rem;
  }
  footer p { margin: .25rem 0; }
  @media (min-width: 720px) {
    .wrap { padding: 2.5rem 1.5rem 4rem; }
    .hero-grid {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 15rem;
      gap: 1.5rem 1.75rem;
      align-items: center;
    }
    .hero-grid figure svg { width: 15rem; }
  }
</style>
</head>
<body>
  <div class="wrap">
    <header class="hero-grid">
      <div>
        <p class="stamp">${AUTHOR}</p>
        <h1>${PRODUCT}</h1>
        <p class="motto">${escapeHtml(MOTTO)}</p>
        <p class="lede">${escapeHtml(ONE_LINE)} Version ${VERSION}. Python 3.10+.</p>
        <div class="cta">
          <a class="download" id="download" href="/download">${ready ? "Download" : "Download unavailable"}</a>
          <p class="file">${escapeHtml(DEFAULT_ASSET)}${sizeBit}</p>
        </div>
        <p class="countline">${escapeHtml(countLine)} Counts include every branch and fork that uses this route.</p>
      </div>
      <figure>
        ${ringSvg()}
        <figcaption>Ring bins, clockwise from zero.</figcaption>
      </figure>
    </header>

    <main>
      <section aria-labelledby="features-title">
        <h2 id="features-title">On the page</h2>
        <ul class="features">${features}</ul>
      </section>

      <section aria-labelledby="wheel-heading">
        <h2 id="wheel-heading">Defined wheel</h2>
        <ul class="swatches">${swatchList()}</ul>
        <p class="install-note">Rosetta maps every pixel onto that wheel. Zen inverts that map.</p>
      </section>

      <section id="install" aria-labelledby="install-title">
        <h2 id="install-title">Install</h2>
        <pre>${escapeHtml(INSTALL_LINE)}</pre>
        <p class="install-note">The same source package is for Linux, macOS, and Windows. The script uses bash and Python 3. On Windows, download the archive and run <code>pip install -e .</code> inside it. Then <code>python3 run.py --help</code>.</p>
        <details>
          <summary>Per branch and fork</summary>
          <ul class="break">${breakdownList(stats)}</ul>
          <p class="install-note"><a href="/stats">JSON stats</a> · <a href="/count">Count</a> · <a href="/openapi.json">OpenAPI</a></p>
        </details>
      </section>
    </main>

    <footer>
      <p>Apache-2.0 · ${AUTHOR} · AMOE ${VERSION}</p>
      <p>Local package. SpectralLock ${SPECTRAL_VERSION} is vendored. Pigment restore stays on the <a href="${SPECTRAL_REPO}">SpectralLock</a> door.</p>
      <p><a href="${GITHUB_REPO}">GitHub</a> · <a href="${LICENSE}">Apache-2.0</a> · <a href="/cite.json">Cite</a></p>
    </footer>
  </div>
</body>
</html>
`;
}

export function installScript() {
  return `#!/usr/bin/env bash
# AMOE ${VERSION} install. The download is counted by this Worker.
set -euo pipefail
HOST="${HOST}"
ASSET="${DEFAULT_ASSET}"
WORKDIR="\${AMOE_HOME:-\$HOME/amoe-spectrallock}"
mkdir -p "\$WORKDIR"
cd "\$WORKDIR"
echo "Downloading \${ASSET}"
curl -fsSL -A 'Mozilla/5.0' "\${HOST}/download?asset=\${ASSET}" -o "\${ASSET}"
tar -xzf "\${ASSET}"
DIR="\$(find . -maxdepth 1 -type d -name 'amoe-spectrallock-*' | head -n 1)"
if [ -n "\${DIR}" ]; then
  cd "\${DIR}"
fi
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .
echo
echo "Installed AMOE ${VERSION}."
echo "Run: python3 run.py --help"
`;
}
