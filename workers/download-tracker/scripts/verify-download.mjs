/**
 * Local check for the AMOE download tracker. No network. No deploy.
 */
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import worker from "../src/index.js";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const repo = path.resolve(root, "../..");
const publicDir = path.join(root, "public");
const assetName = "amoe-spectrallock-1.3.0.tar.gz";
const assetPath = path.join(publicDir, assetName);
const catalog = JSON.parse(fs.readFileSync(path.join(repo, "catalog.json"), "utf8"));

const fileBytes = fs.readFileSync(assetPath);
assert.equal(fileBytes[0], 0x1f);
assert.equal(fileBytes[1], 0x8b);

function memoryKv() {
  const store = new Map();
  return {
    async get(key) {
      return store.has(key) ? store.get(key) : null;
    },
    async put(key, value) {
      store.set(key, String(value));
    },
    async list() {
      return { keys: [...store.keys()].map((name) => ({ name })), list_complete: true };
    },
  };
}

function envWith(kv) {
  return {
    DOWNLOADS: kv,
    SKIP_GITHUB: "1",
    ASSETS: {
      async fetch(request) {
        const url = new URL(request.url);
        const name = url.pathname.replace(/^\//, "");
        const file = path.join(publicDir, name);
        if (file !== assetPath) return new Response("missing", { status: 404 });
        return new Response(fs.readFileSync(file));
      },
    },
  };
}

async function call(kv, pathname, { method = "GET", headers = {}, body = null } = {}) {
  const request = new Request("https://amoe-spectrallock-download-tracker.vibelock.workers.dev" + pathname, {
    method,
    headers,
    body,
  });
  return worker.fetch(request, envWith(kv));
}

const kv = memoryKv();
const human = { "User-Agent": "Mozilla/5.0 (verification)" };

const page = await call(kv, "/", { headers: human });
assert.equal(page.status, 200);
const html = await page.text();
assert.match(html, /<h1>AMOE<\/h1>/);
assert.match(html, /prefers-color-scheme:\s*dark/);
assert.match(html, /:focus-visible/);
assert.match(html, />Download</);
assert.match(html, /1\.3\.0/);
assert.match(html, /SpectralLock 0\.3\.1/);
assert.doesNotMatch(html, /0\.3\.0/);
assert.doesNotMatch(html, /identity-lock/i);
assert.doesNotMatch(html, /1\.4\.0/);
for (const [name, hex] of Object.entries(catalog.ring_cw_from_zero)) {
  assert.ok(html.includes(hex), `${name} ${hex} missing from landing`);
  assert.ok(html.includes(name), `${name} missing from landing`);
}
assert.match(html, /Counted downloads: 0/);

const first = await call(kv, "/download", { headers: human });
assert.equal(first.status, 200);
assert.equal(first.headers.get("content-type"), "application/gzip");
assert.match(first.headers.get("content-disposition") || "", /amoe-spectrallock-1\.3\.0\.tar\.gz/);
const got = new Uint8Array(await first.arrayBuffer());
assert.equal(Buffer.compare(Buffer.from(got), fileBytes), 0);

const dev = await call(kv, "/download?branch=dev", { headers: human });
assert.equal(dev.status, 200);
await dev.arrayBuffer();

const fork = await call(kv, "/download?repo=octo/amoe-spectrallock&branch=main", { headers: human });
assert.equal(fork.status, 200);
await fork.arrayBuffer();

const event = await call(kv, "/event", {
  method: "POST",
  headers: { "Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (verification)" },
  body: JSON.stringify({ owner: "octo", repo: "amoe-spectrallock", branch: "feature", fork: "1" }),
});
assert.equal(event.status, 200);

const head = await call(kv, "/download", { method: "HEAD", headers: human });
assert.equal(head.status, 200);
assert.equal(await head.text(), "");

const missing = await call(kv, "/download?asset=not-real.tar.gz", { headers: human });
assert.equal(missing.status, 404);

const sneak = await call(kv, "/download/..%2Fpyproject.toml", { headers: human });
assert.equal(sneak.status, 404);

const install = await call(kv, "/install.sh");
assert.equal(install.status, 200);
const script = await install.text();
assert.match(script, /amoe-spectrallock-1\.3\.0\.tar\.gz/);
assert.match(script, /\/download\?asset=/);

const statsRes = await call(kv, "/stats");
const stats = await statsRes.json();
assert.equal(stats.project, "amoe-spectrallock");
assert.equal(stats.downloads, 4);
assert.equal(stats.total, 4);
assert.equal(stats.views, 1);
assert.equal(stats.by_branch.main, 2);
assert.equal(stats.by_branch.dev, 1);
assert.equal(stats.by_branch.feature, 1);
assert.equal(stats.by_fork["0"], 2);
assert.equal(stats.by_fork["1"], 2);
assert.equal(stats.by_repo["AzielEliab/amoe-spectrallock"], 2);
assert.equal(stats.by_repo["octo/amoe-spectrallock"], 2);
assert.equal(stats.views, stats.views_human + stats.views_bot);
assert.equal(stats.downloads, stats.downloads_human + stats.downloads_bot);

const count = await (await call(kv, "/count")).json();
assert.equal(count.total, count.downloads);
assert.equal(count.downloads, 4);
assert.equal(count.views, 1);

const again = await (await call(kv, "/", { headers: human })).text();
assert.match(again, /Counted downloads: 4/);

console.log("verify-download: ok");
