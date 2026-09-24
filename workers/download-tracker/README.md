# AMOE download tracker

Isolated Worker `amoe-spectrallock-download-tracker`.
Project key prefix `amoe-spectrallock`.
Package **AMOE 1.3.0** (local wiring on vendored SpectralLock 0.3.1).

This Worker is source in the repo. It is not deployed from here.
A teammate deploys it after merge. Do not point DNS at it from this tree.

Host after deploy: https://amoe-spectrallock-download-tracker.vibelock.workers.dev

There is no GitHub release asset. `GET /download` serves
`public/amoe-spectrallock-1.3.0.tar.gz`, built from this repository
by `scripts/build-asset.sh`. HTTP 200, `Content-Disposition: attachment`,
no redirect. Each GET increments the counter. HEAD does not.

## Deploy

The KV id in `wrangler.toml` is a placeholder so a deploy cannot write
into another product's namespace.

```bash
cd workers/download-tracker
npm install
npx wrangler kv namespace create AMOE_SPECTRALLOCK_DOWNLOADS
```

Paste the new id into `wrangler.toml` (`binding = "DOWNLOADS"`), then:

```bash
npx wrangler deploy
```

Account `ac575a9b822bea2bed97d0ab73aed238` is the same public workers.dev
account the other product trackers use (`*.vibelock.workers.dev`).

## Routes

| Route | Behavior |
| --- | --- |
| `GET /` | Landing. Increments page views, not downloads. |
| `GET /download` | Serves the 1.3.0 source package and counts it. |
| `GET /count` | `{project, views, downloads, total}` with `total` = downloads. |
| `GET /stats` | Totals plus `by_repo`, `by_branch`, `by_fork`, and `breakdown`. |
| `POST /event` | A fork or branch reports `{owner, repo, branch, fork}`. |
| `GET /install.sh` | Bash install. Does not increment; the script curls `/download`. |

Query `owner`, `repo`, `branch`, and `fork` on `/download`. A repo other
than `AzielEliab/amoe-spectrallock` is stored as a fork. Key layout:
`amoe-spectrallock|owner|repo|branch|fork`.

Human/bot fields on `/count` and `/stats` follow the shared tracker
schema (`src/classify.js`, `src/stats-shape.js`). The landing does not
show a score.

AMOE stays a local package. This Worker does not add runtime tools.
