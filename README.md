# AMOE

Pull faded structure from a page picture, then color what was pulled with the defined wheel. You still read the page.

Author: **Aziel Eliab**.

## Start

1. `pip install -e .`
2. `amoe overlay page.jpg --mode tazel`
3. Open `amoe-out/page/overlay/tazel.png`

`python3 run.py` is the same command. With no arguments it prints the next step. `amoe ui` opens the local page at `http://127.0.0.1:8871/`. Add `--json` when a program should read the card.

## Notes

AMOE 1.3.0 is wiring on every cell of the SpectralLock 0.3.1 color grid. Paper: AMOE-1.3. Public pack: aziel-runtime. The human still reads the page.

AMOE is wiring. It is not a field and not a color. Tazel stays Tazel. Zero stays Zero. There is no `amoe.png`, no twelfth lens named AMOE, and AMOE is not an alias of Rosetta. `--mode amoe` is refused.

Pigment restore stays a SpectralLock product door. AMOE sidecars keep `pigment_recovery` false and `invent_letters` false. This package does not reimplement that path.

Vendored tip: SpectralLock **0.3.1** at `92fcc3b031b3c6e1bf398d4263092e20d9bad3c5` in `vendor/spectrallock` ([github.com/AzielEliab/spectrallock](https://github.com/AzielEliab/spectrallock)). The 1.3 plate text also names 0.3.0; this tree was already on 0.3.1, so that tip is the one vendored. `analyze`, `apply_target`, and inject formulas are not rewritten. The local SpectralLock page shell was adjusted for reading.

### Paint law

Pull what is faded. Color it with the wheel that was defined. Rosetta maps every pixel onto that wheel. Zen inverts that map. AMOE rides every lens. Do not make the pattern. Draw the pattern out.

Pull faded structure first. Color only what was pulled. Empty paper stays empty. Present paint (a yellow robe, a red robe) is brightened, not replaced.

| lens | wheel | engine | law |
| --- | --- | --- | --- |
| zero | `#2E5A8C` | `#6F6485` | single hex sheet, visible blue |
| chaos | `#7A2E5C` | `#8C3861` | single hex sheet, magenta |
| vyrn | `#C00066` | `#C00066` | single hex sheet, crimson |
| uv | `#C45A2A` | `#8C73D9` | orange wheel / violet engine |
| tazel | `#8A9A2E` | `#1EC9A5` | single hex sheet, olive-gold |
| rosetta | pixel-scope | `#6B8A8A` | full scope from pixelation |
| zen | invert | `#C9C4B8` | invert of the Rosetta pixel map |
| balance | BSA mix | `#8A8680` | α·Zen + (1−α)·Chaos |

Ring bins, clockwise from ZERO, also include Rosetta `#2E7A4A`. That green is one bin in the pixel map. The Rosetta plate is the pixel-scope map.

Gallery paint uses `WHEEL_HEX`. `--paint wheel` is the operator plate and the default. `--paint engine` is the membership hex only. Keep the tables separate. SpectralLock's own inject paint inside `analyze()` is the vendored 0.3.1 engine and is left alone. In-band densitometry stays on that engine measurement.

Geometry and harmonic weighting (ASCENT / WEIGHT / EQUILIBRIUM along the S-curve) are on by default. `--no-geom` and `--no-weight` turn them off.

A weak page is a valid reading. The sidecar refuses `AMOE-WEAK-SIGNAL` when emergence and undertext means are empty. It does not invent undertext. ZE and CH already mix core channels; the `/12` double-counts, and the sidecar records that.

### Commands

```bash
amoe overlay PAGE.jpg --mode tazel
amoe gallery PAGE.jpg
amoe lift PAGE.jpg
amoe adapt PAGE.jpg
amoe ui
amoe doctor
amoe --help
```

Further commands stay available: `grid`, `paint`, `geom`, `path`, `catalog`, `custodian`, `recover-image`, `recover-script`, `script`, `route`, `preocr`, `together`, `reconstruct`.

`together` runs the script search, then image isolation, in the same directory. The script track may tighten marks that are already visible. It does not declare a transcription as fact.

### Page scalar

Wiring on the cells. The same scalar is attached to every emitted cell.

```
AMOE(x) = ((Z0 + TZ + VY + UV + ZE − CH) + (RS + AA + DR + VC + HL + RSA)) / 12
```

SLOT indices stay 0 unless you pass `--index KEY=0..1`.

### Custodians

| code | role | lens |
| --- | --- | --- |
| MMI | Maker | tazel |
| WLW | Guardian | vyrn |
| AZI | Integrator | zero |

The Waterfall Guardian Plate routes through adapt → ZERO geometry.

### Path 1–13

`path` audits a card. It does not look for figures in pixels. Steps 1–13 keep their names: Apertio (Opening) through First Breath / Purpose.

### Refuse codes

| code | when |
| --- | --- |
| `AMOE-WEAK-SIGNAL` | emergence and undertext means are empty. Valid. No invented undertext. |
| `AMOE-NO-FIGURE` | path card has no steps |
| `AMOE-BAD-STEP:n` | step n is outside 1–13 |
| `AMOE-GATE-MISALIGN` | step 12 is present and gate is not `gate` or `post-gate` |
| `AMOE-RECONSTRUCT-NOT-NEEDED` | page state is present |
| `AMOE-RECONSTRUCT-USE-ADAPT` | reconstruct was called with no page |
| `amoe_as_color` | a twelfth overlay named amoe was requested |
| `invent_mark` / `invent_letter` | a request to write glyphs that are not in the pixels |

Empty in-band hue is a valid reading. It is recorded.

Runtime dependencies are `numpy` and `Pillow` (`requirements.txt`).
