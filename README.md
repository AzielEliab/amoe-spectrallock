# AMOE-1.2 + SpectralLock 0.3.1

AMOE is **wiring** on every cell of the SpectralLock color grid. It is **not a field** and **not a color**. Tazel stays Tazel. There is no `amoe.png` and no twelfth lens named AMOE. AMOE is not an alias of Rosetta.

Author: **Aziel Eliab**. Paper: AMOE-1.2. The human still reads the page.

Pigment restore stays a **SpectralLock** product door. AMOE sidecars keep `pigment_recovery` false and `invent_letters` false. This package does not reimplement that path.

## Two palettes

Do not mix these in one file without labeling the pass.

**Engine / densitometry** (SpectralLock `analyze`, in-band math, unchanged):

| lens | hex | role |
| --- | --- | --- |
| zero | `#6F6485` | structure / integrator, hue 260° |
| tazel | `#1EC9A5` | revelation / maker, hue 170° |
| vyrn | `#C00066` | pressure / guardian, hue 350° |
| uv | `#8C73D9` | synthetic 365–400 nm look |
| chaos | `#8C3861` | lens card; mix 0.40·UV + 0.35·V + 0.20·T + 0.05·Z |
| balance | `#8A8680` | reweight only |
| candle | `#FF9E38` | warm flame-side |
| indent | `#B8AD94` | relief heuristic; prefer `target=page` |
| lemon | `#9E6124` | browning already in the pixels |

Rosetta is the blend `0.40·Z + 0.35·T + 0.25·V`. Zen is `(Z + T + UV + V) / 4` using engine UV, not the wheel.

**Spectral Harmonic Wheel** (`--paint wheel` and `gallery` only). These are the live operator hexes:

| label | hex |
| --- | --- |
| zero | `#325767` |
| chaos | `#8D223D` |
| vyrn | `#A22639` |
| uv | `#9F3B2B` |
| tazel | `#797A2D` |
| rosetta | `#467542` |
| zen | `#DFD2B5` |

Wheel UV is burnt red. Engine UV is violet. Center of the wheel is Zen. Clockwise from the top: Zero → Chaos → Vyrn → UV → Tazel → Rosetta → Zero.

SpectralLock **0.3.1** inject ON paints membership inside the engine and still reports `tazel_inband_pct` and `vyrn_inband_pct`. Zero ignores the inject switch. AMOE calls that engine; it does not rewrite `analyze`, `apply_target`, inject, ink/page, `inband_pct`, or `OverlayResult`. An empty gate is a valid reading (`AMOE-EMPTY-HUE`), not a crash. Copy-of-copy works only while the hue is still in-band.

The vendored tree is `vendor/spectrallock` from [github.com/AzielEliab/spectrallock](https://github.com/AzielEliab/spectrallock) at **0.3.1** (`92fcc3b`, pigment doors on the engine). AMOE depends on `spectrallock@0.3.1`.

## Install

```bash
pip install -e .
python3 run.py --help
```

Runtime dependencies are `numpy` and `Pillow` (`requirements.txt`).

## CLI

```bash
python3 run.py overlay PAGE.jpg --mode tazel --target ink|page [--inject] [--paint wheel|engine] [--lift]
python3 run.py grid PAGE.jpg --target ink|page [--inject] [--paint wheel] [--lift]
python3 run.py paint PAGE.jpg --palette wheel|engine [--mode MODE]
python3 run.py gallery PAGE.jpg
python3 run.py lift PAGE.jpg
python3 run.py geom PAGE.jpg
python3 run.py adapt PAGE.jpg
python3 run.py reconstruct PAGE.jpg
python3 run.py path --card steps.json
python3 run.py catalog
python3 run.py custodian
```

`--inject` defaults on, matching the engine. `--no-inject` is the luminance of the same gate. `--paint engine` keeps the SpectralLock preview. `--paint wheel` writes a separate false-color of the luminance ink mask and labels that pass `wheel`. `paint --palette engine` is the lens-card false-color, not a second copy of `analyze()`.

`indent` uses `target=page` when no target is given. SLOT indices (`RS`, `AA`, `DR`, `VC`, `HL`, `RSA`) stay 0 unless you pass `--index KEY=0..1`. They are not fabricated.

`gallery` is a labeled 3×3 wheel sheet: source, zero, chaos / vyrn, uv, tazel / rosetta, zen, blend. Blend is a wheel mix of zen and chaos. It is not AMOE and it is not Rosetta.

## Page scalar

Wiring, not a painted field. The same scalar is attached to every emitted cell. No `amoe_field.png`.

```
AMOE_scalar = clip( (Z0 + TZ + VY + UV + ZE - CH + RS+AA+DR+VC+HL+RSA) / 12 , 0, 1)
```

Live terms are the mean luminance of each engine cell after the ink/page target.

## Adaptive route and geometry

```
contrast = std(luma) / 255
span = (p90 - p10) / 255
near_gone if contrast < 0.14 and span < 0.35
faint if contrast < 0.18 and span < 0.45
else present
```

Faint and near-gone pages may be reconstructed: Zero engine with inject off, lift, geometry, `reconstruct_zero.png` as wheel-painted Zero labeled `reconstruct`, then the ring, Zen, and the gallery. A present page returns `AMOE-RECONSTRUCT-NOT-NEEDED` and can still write geometry, or the grid when `--grid` is set. `reconstruct` with no page returns `AMOE-RECONSTRUCT-USE-ADAPT`.

Geometry is a ZERO process: edge mask, content box, vertical-edge axis, nested frame, axis mundi, mid line, both diagonals, a circle on that axis, and a second circle at 78% of the box. Default color `#6EA0D2`. `invent_figures` is false. If the edges do not support a frame, the page is returned unchanged.

Lift is percentile stretch, equalize, and unsharp on pixels that are already there. It does not transcribe missing text.

## Custodians

| code | role | lens |
| --- | --- | --- |
| MMI | Maker | tazel |
| WLW | Guardian | vyrn |
| AZI | Integrator | zero |

The Waterfall Guardian Plate (A–G / Zero-night) is not on that list. It routes through adapt → ZERO geometry, not through Tazel.

## Path 1–13

`path` audits a card. It does not look for figures in pixels. Axes are vector, lens, conflict, and gate. Steps:

1. Apertio (Opening)
2. Herald selection
3. First Sight
4. Rider (motion)
5. First Message
6. First Division (Two Birds)
7. Choosing the Correct Bird
8. Warning (Distracted Man)
9. Inner Engagement
10. First Re-alignment
11. First True Conflict
12. First Gate (Twin Pillars)
13. First Breath / Purpose

## Refuse codes

| code | when |
| --- | --- |
| `AMOE-EMPTY-HUE` | `tazel_inband_pct` and `vyrn_inband_pct` are both 0. Valid reading. |
| `AMOE-NO-FIGURE` | path card has no steps |
| `AMOE-BAD-STEP:n` | step n is outside 1–13 |
| `AMOE-GATE-MISALIGN` | step 12 is present and gate is not `gate` or `post-gate` |
| `AMOE-RECONSTRUCT-NOT-NEEDED` | page state is present |
| `AMOE-RECONSTRUCT-USE-ADAPT` | reconstruct was called with no page |
| `amoe_as_color` | a twelfth overlay named amoe was requested |
| `invent_mark` / `invent_letter` | a request to write glyphs that are not in the pixels |
| `SL-UNREDACT-OPAQUE` | engine code for an opaque replace with no leftover container bytes |

If a note asks AMOE to invent letters, the invention is refused and the note is kept on the sidecar. `invent_letters` stays false.

## Catalog

`catalog.json` is the fragment for the suite map. Execution stays local. The runtime may catalog this object; it does not run an overlay unless that op is commissioned. This repository does not add a Worker execution path.

## Layout

```
run.py
README.md
LICENSE
requirements.txt
catalog.json
amoe/
vendor/spectrallock/
```

Grid, in order: zero, tazel, vyrn, uv, rosetta, zen, chaos, balance, candle, indent, lemon.
