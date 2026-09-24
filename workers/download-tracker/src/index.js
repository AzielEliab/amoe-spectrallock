import { classifyRequest, readBotManagement } from "./classify.js";
import {
  DEFAULT_ASSET,
  handleSeoRoutes,
  installScript,
  renderHome,
} from "./home.js";
import {
  isolatedKeys,
  isReservedCounterKey,
  shapeCountBody,
  shapeHumanBotFields,
} from "./stats-shape.js";

/**
 * AMOE download tracker.
 *
 * GET  /download   increments KV, serves the source package (HTTP 200, no 302)
 * GET  /count      {project, views, downloads, total} — total = downloads
 * GET  /stats      totals + per-repo + per-branch + fork breakdown
 * POST /event      another branch or fork reports a download
 *
 * KV keys: project|owner|repo|branch|fork
 * Author: Aziel Eliab.
 */

const PROJECT = "amoe-spectrallock";
const KEYS = isolatedKeys(PROJECT);
const DEFAULT_OWNER = "AzielEliab";
const DEFAULT_REPO = "amoe-spectrallock";
const DEFAULT_BRANCH = "main";
const ASSET_NAME = /^[A-Za-z0-9._-]+$/;

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, HEAD, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Accept, User-Agent",
  };
}

function json(body, status = 200) {
  return new Response(JSON.stringify(body, null, 2), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", ...corsHeaders() },
  });
}

function splitOwnerRepo(value, fallbackOwner, fallbackRepo) {
  if (typeof value === "string" && value.includes("/")) {
    const [o, r] = value.split("/").filter(Boolean);
    if (o && r) return { owner: o, repo: r };
  }
  return { owner: fallbackOwner, repo: fallbackRepo };
}

export function parseDims(src) {
  const get = (k) => {
    if (src == null) return null;
    if (typeof src.get === "function") {
      const v = src.get(k);
      return v == null || v === "" ? null : v;
    }
    const v = src[k];
    return v == null || v === "" ? null : v;
  };

  let owner = get("owner") || DEFAULT_OWNER;
  let repo = get("repo") || DEFAULT_REPO;
  if (typeof repo === "string" && repo.includes("/")) {
    const split = splitOwnerRepo(repo, owner, DEFAULT_REPO);
    owner = split.owner;
    repo = split.repo;
  }

  const branch = String(get("branch") || DEFAULT_BRANCH);
  const tag = get("tag") || "latest";
  const asset = get("asset") || "";

  const forkRaw = get("fork");
  let fork = "0";
  if (forkRaw === 1 || forkRaw === true || forkRaw === "1" || forkRaw === "true") {
    fork = "1";
  } else if (typeof forkRaw === "string" && forkRaw.includes("/")) {
    const split = splitOwnerRepo(forkRaw, owner, repo);
    owner = split.owner;
    repo = split.repo;
    fork = "1";
  } else if (forkRaw != null && forkRaw !== 0 && forkRaw !== false && forkRaw !== "0" && forkRaw !== "false") {
    fork = "1";
  }

  if (`${owner}/${repo}`.toLowerCase() !== `${DEFAULT_OWNER}/${DEFAULT_REPO}`.toLowerCase()) {
    fork = "1";
  }

  return { project: PROJECT, owner, repo, branch, fork, tag, asset };
}

export function kvKey(dims) {
  return `${dims.project}|${dims.owner}|${dims.repo}|${dims.branch}|${dims.fork}`;
}

function safeAssetName(name) {
  if (typeof name !== "string" || !ASSET_NAME.test(name) || name !== DEFAULT_ASSET) return null;
  return name;
}

async function bump(env, key) {
  const n = parseInt((await env.DOWNLOADS.get(key)) || "0", 10) + 1;
  await env.DOWNLOADS.put(key, String(n));
  return n;
}

async function incrementSplit(env, humanKey, botKey, request) {
  const cls = classifyRequest(request);
  const splitKey = cls.bucket === "human" ? humanKey : botKey;
  await bump(env, splitKey);
  return cls;
}

async function increment(env, dims, request) {
  const key = kvKey(dims);
  const n = await bump(env, key);
  await bump(env, KEYS.total);
  if (request) await incrementSplit(env, KEYS.downloads_human, KEYS.downloads_bot, request);
  return n;
}

async function incrementViews(env, request) {
  const n = await bump(env, KEYS.views);
  if (request) await incrementSplit(env, KEYS.views_human, KEYS.views_bot, request);
  return n;
}

async function listAllKeys(env) {
  const keys = [];
  let cursor;
  do {
    const page = await env.DOWNLOADS.list(cursor ? { cursor } : {});
    keys.push(...page.keys);
    cursor = page.list_complete ? undefined : page.cursor;
  } while (cursor);
  return keys;
}

async function githubStats(env) {
  const empty = { stars: 0, forks: 0, watchers: 0, release_download_count: 0, fetched_at: Date.now() };
  if (!env.DOWNLOADS || env.SKIP_GITHUB === "1") return empty;
  const cached = await env.DOWNLOADS.get(KEYS.github);
  if (cached) {
    try {
      const obj = JSON.parse(cached);
      if (obj && obj.fetched_at && Date.now() - obj.fetched_at < 5 * 60 * 1000) return obj;
    } catch {
      /* ignore stale cache */
    }
  }
  const headers = {
    "User-Agent": "Mozilla/5.0 AMOE-download-tracker",
    Accept: "application/vnd.github+json",
  };
  let stars = 0;
  let forks = 0;
  let watchers = 0;
  let release_download_count = 0;
  try {
    const repoRes = await fetch("https://api.github.com/repos/AzielEliab/amoe-spectrallock", { headers });
    if (repoRes.ok) {
      const repo = await repoRes.json();
      stars = Number(repo.stargazers_count) || 0;
      forks = Number(repo.forks_count) || 0;
      watchers = Number(repo.subscribers_count != null ? repo.subscribers_count : repo.watchers_count) || 0;
    }
    const relRes = await fetch("https://api.github.com/repos/AzielEliab/amoe-spectrallock/releases/latest", { headers });
    if (relRes.ok) {
      const rel = await relRes.json();
      const assets = Array.isArray(rel.assets) ? rel.assets : [];
      release_download_count = assets.reduce((sum, asset) => sum + (Number(asset.download_count) || 0), 0);
    }
  } catch {
    /* public API; empty is fine */
  }
  const out = { stars, forks, watchers, release_download_count, fetched_at: Date.now() };
  try {
    await env.DOWNLOADS.put(KEYS.github, JSON.stringify(out));
  } catch {
    /* ignore */
  }
  return out;
}

export async function collectStats(env, request) {
  if (!env.DOWNLOADS) {
    return {
      project: PROJECT,
      total: 0,
      views: 0,
      downloads: 0,
      by_repo: {},
      by_branch: {},
      by_fork: { "0": 0, "1": 0 },
      breakdown: [],
      github: { stars: 0, forks: 0, watchers: 0, release_download_count: 0 },
      unbound: true,
      ...shapeHumanBotFields({ views: 0, downloads: 0, views_human: 0, downloads_human: 0, botManagementAvailable: false }),
    };
  }

  const keys = await listAllKeys(env);
  let summed = 0;
  const by_repo = {};
  const by_branch = {};
  const by_fork = { "0": 0, "1": 0 };
  const breakdown = [];

  for (const k of keys) {
    const name = k.name;
    if (isReservedCounterKey(name, PROJECT)) continue;
    const n = parseInt((await env.DOWNLOADS.get(name)) || "0", 10);
    if (!Number.isFinite(n) || n <= 0) continue;
    const parts = name.split("|");
    if (parts.length < 5) continue;
    const [project, owner, repo, branch, fork] = parts;
    summed += n;
    const repoId = `${owner}/${repo}`;
    by_repo[repoId] = (by_repo[repoId] || 0) + n;
    by_branch[branch] = (by_branch[branch] || 0) + n;
    const forkFlag = fork === "1" ? "1" : "0";
    by_fork[forkFlag] = (by_fork[forkFlag] || 0) + n;
    breakdown.push({ project, owner, repo, branch, fork: forkFlag, count: n });
  }

  const totalDirect = parseInt((await env.DOWNLOADS.get(KEYS.total)) || "0", 10);
  const views = parseInt((await env.DOWNLOADS.get(KEYS.views)) || "0", 10) || 0;
  const shown = Number.isFinite(totalDirect) && totalDirect > 0 ? totalDirect : summed;
  const viewsHuman = parseInt((await env.DOWNLOADS.get(KEYS.views_human)) || "0", 10) || 0;
  const downloadsHuman = parseInt((await env.DOWNLOADS.get(KEYS.downloads_human)) || "0", 10) || 0;
  const github = await githubStats(env);
  const botManagementAvailable = request ? readBotManagement(request).available : false;

  return {
    project: PROJECT,
    total: shown,
    views,
    downloads: shown,
    by_repo,
    by_branch,
    by_fork,
    breakdown,
    github: {
      stars: github.stars || 0,
      forks: github.forks || 0,
      watchers: github.watchers || 0,
      release_download_count: github.release_download_count || 0,
    },
    unbound: false,
    note: "Key layout: project|owner|repo|branch|fork. Views are separate from downloads.",
    ...shapeHumanBotFields({
      views,
      downloads: shown,
      views_human: viewsHuman,
      downloads_human: downloadsHuman,
      botManagementAvailable,
    }),
  };
}

async function readAsset(request, env, asset) {
  if (!env.ASSETS || typeof env.ASSETS.fetch !== "function") return null;
  const assetUrl = new URL("/" + asset, request.url);
  const assetRes = await env.ASSETS.fetch(new Request(assetUrl.toString(), { method: "GET" }));
  if (!assetRes.ok) return null;
  const bytes = new Uint8Array(await assetRes.arrayBuffer());
  if (!bytes.byteLength) return null;
  return bytes;
}

async function pageStats(request, env) {
  const stats = await collectStats(env, request);
  const bytes = await readAsset(request, env, DEFAULT_ASSET);
  return {
    ...stats,
    assetReady: !!bytes,
    assetBytes: bytes ? bytes.byteLength : 0,
  };
}

async function serveDownload(request, env, asset, { head = false, count = false } = {}) {
  const safe = safeAssetName(asset);
  if (!safe) {
    return json({ error: "asset not hosted", asset: asset || null }, 404);
  }
  if (!env.DOWNLOADS) {
    return json(
      {
        error: "DOWNLOADS binding missing",
        reason: "Create the isolated KV namespace and bind it as DOWNLOADS before serving a counted download.",
      },
      503,
    );
  }
  const bytes = await readAsset(request, env, safe);
  if (!bytes) {
    return json({ error: "asset not hosted", asset: safe }, 404);
  }
  if (count) {
    const dims = parseDims(new URL(request.url).searchParams);
    dims.asset = safe;
    await increment(env, dims, request);
  }
  const headers = new Headers();
  headers.set("Content-Type", "application/gzip");
  headers.set("Content-Disposition", `attachment; filename="${safe}"`);
  headers.set("Content-Length", String(bytes.byteLength));
  headers.set("Cache-Control", "private, no-store");
  headers.set("X-Content-Type-Options", "nosniff");
  for (const [k, v] of Object.entries(corsHeaders())) headers.set(k, v);
  if (head) return new Response(null, { status: 200, headers });
  return new Response(bytes, { status: 200, headers });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders() });
    }

    const seo = handleSeoRoutes(request, url);
    if (seo) return seo;

    if ((url.pathname === "/install.sh" || url.pathname === "/install.sh/") && request.method === "GET") {
      return new Response(installScript(), {
        status: 200,
        headers: {
          "Content-Type": "text/x-shellscript; charset=utf-8",
          "Cache-Control": "private, no-store",
          ...corsHeaders(),
        },
      });
    }

    if (url.pathname === "/" && request.method === "GET") {
      if (env.DOWNLOADS) await incrementViews(env, request);
      const stats = await pageStats(request, env);
      return new Response(renderHome(stats), {
        headers: {
          "Content-Type": "text/html; charset=utf-8",
          "Cache-Control": "private, no-store",
          ...corsHeaders(),
        },
      });
    }

    if (url.pathname === "/count" && request.method === "GET") {
      const stats = await collectStats(env, request);
      return json(
        shapeCountBody({
          project: PROJECT,
          views: stats.views || 0,
          downloads: stats.downloads || 0,
          total: stats.total || 0,
          views_human: stats.views_human,
          downloads_human: stats.downloads_human,
          botManagementAvailable: readBotManagement(request).available,
        }),
      );
    }

    if (url.pathname === "/stats" && request.method === "GET") {
      return json(await collectStats(env, request));
    }

    if (url.pathname === "/event" && request.method === "POST") {
      if (!env.DOWNLOADS) {
        return json({ error: "DOWNLOADS binding missing" }, 503);
      }
      let body;
      try {
        body = await request.json();
      } catch {
        return json({ error: "JSON body required" }, 400);
      }
      const dims = parseDims(body || {});
      const count = await increment(env, dims, request);
      return json({
        ok: true,
        key: kvKey(dims),
        count,
        owner: dims.owner,
        repo: dims.repo,
        branch: dims.branch,
        fork: dims.fork,
        asset: dims.asset || null,
      });
    }

    const downloadPath =
      url.pathname === "/download" ||
      url.pathname.startsWith("/download/") ||
      url.pathname === "/go" ||
      url.pathname === `/${DEFAULT_ASSET}`;

    if (downloadPath && (request.method === "GET" || request.method === "HEAD")) {
      const dims = parseDims(url.searchParams);
      let asset = dims.asset || DEFAULT_ASSET;
      if (!dims.asset && url.pathname.startsWith("/download/")) {
        asset = decodeURIComponent(url.pathname.slice("/download/".length));
      }
      if (url.pathname === `/${DEFAULT_ASSET}`) asset = DEFAULT_ASSET;
      return serveDownload(request, env, asset, {
        head: request.method === "HEAD",
        count: request.method === "GET",
      });
    }

    return json({ error: "not found" }, 404);
  },
};
