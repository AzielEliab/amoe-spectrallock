# AMOE 1.3 + SpectralLock 0.3.1

Pull what is faded. Color it with the wheel that was defined. Rosetta maps every pixel onto that wheel. Zen inverts that map. AMOE rides every lens. Do not make the pattern. Draw the pattern out.

AMOE is **wiring** on every cell of the SpectralLock color grid. It is **not a field** and **not a color**. Tazel stays Tazel. Zero stays Zero. There is no `amoe.png`, no `--mode amoe`, and no twelfth lens named AMOE. AMOE is not an alias of Rosetta.

Author: **Aziel Eliab**. Public pack: **aziel-runtime**. Paper: AMOE-1.3. Product: `amoe` 1.3.0. The human still reads the page.

Pigment restore stays a **SpectralLock** product door. AMOE sidecars keep `pigment_recovery` false and `invent_letters` false. This package does not reimplement that path.

Vendored tip: SpectralLock **0.3.1** at `92fcc3b031b3c6e1bf398d4263092e20d9bad3c5` in `vendor/spectrallock` ([github.com/AzielEliab/spectrallock](https://github.com/AzielEliab/spectrallock)). The 1.3 plate text also names 0.3.0; this tree was already on 0.3.1, so that tip is the one vendored. `analyze`, `apply_target`, and inject formulas are not rewritten.

## Paint law

Pull faded structure first. Color only what was pulled. Empty paper stays empty. Present paint (a yellow robe, a red robe) is brightened, not replaced.

| lens | wheel | engine | law |
| --- | --- | --- | --- |
| zero | `#2E5A8C` | `#6F6485` | single hex sheet, visible blue |
| chaos | `#7A2E5C` | `#8C3861` | single hex sheet, magenta |
| vyrn | `#C00066` | `#C00066` | single hex sheet, crimson |
| uv | `#C45A2A` | `#8C73D9` | orange wheel / violet engine |
| tazel | `#8A9A2E` | `#1EC9A5` | single hex sheet, olive-gold |
| rosetta | pixel-scope | `#6B8A8A` | full scope from pixelation, not a green sheet |
| zen | invert | `#C9C4B8` | `clip(1 − Rosetta pixel map)`, not a cream sheet |
| balance | BSA mix | `#8A8680` | α·Zen + (1−α)·Chaos |

Ring bins, clockwise from ZERO, also include Rosetta `#2E7A4A`. That green is one bin in the pixel map. It is not the Rosetta plate.

Gallery paint uses `WHEEL_HEX`. `--paint engine` is the membership hex only. Do not swap the tables. SpectralLock's own inject paint inside `analyze()` is the vendored 0.3.1 engine and is left alone.

Geometry and harmonic weighting (ASCENT / WEIGHT / EQUILIBRIUM along the S-curve) are on by default. `--no-geom` and `--no-weight` turn them off.

A weak page is a valid reading. The sidecar refuses `AMOE-WEAK-SIGNAL` when emergence and undertext means are empty. It does not invent undertext. ZE and CH already mix core channels; the `/12` double-counts, and the sidecar records that.

## Install

```bash
pip install -e .
python3 run.py --help
```

Runtime dependencies are `numpy` and `Pillow` (`requirements.txt`).

## CLI

```bash
python3 run.py overlay PAGE.jpg --mode tazel --paint wheel --lift
python3 run.py overlay PAGE.jpg --mode rosetta --paint wheel --lift
python3 run.py overlay PAGE.jpg --mode zen --paint wheel --lift
python3 run.py grid PAGE.jpg --paint wheel --lift
python3 run.py paint PAGE.jpg --palette wheel
python3 run.py lift PAGE.jpg
python3 run.py gallery PAGE.jpg
python3 run.py geom PAGE.jpg
python3 run.py adapt PAGE.jpg
python3 run.py recover-image PAGE.jpg
python3 run.py recover-script PAGE.jpg
python3 run.py script PAGE.jpg --mode tazel
python3 run.py route PAGE.jpg
python3 run.py preocr PAGE.jpg
python3 run.py together PAGE.jpg
python3 run.py path --card steps.json
python3 run.py catalog
python3 run.py custodian
```

`--paint wheel` is the operator plate and the default. `--paint engine` is membership hex only. `--no-geom` and `--no-weight` are accepted on overlay and grid. There is no `--mode amoe`.

`together` runs the script search, then image isolation, in the same directory. The script track may tighten marks that are already visible. It does not declare a transcription as fact.

## Page scalar

Wiring, not a painted field. The same scalar is attached to every emitted cell. No `amoe_field.png`.

```
AMOE(x) = ((Z0 + TZ + VY + UV + ZE − CH) + (RS + AA + DR + VC + HL + RSA)) / 12
```

SLOT indices stay 0 unless you pass `--index KEY=0..1`.

## Custodians

| code | role | lens |
| --- | --- | --- |
| MMI | Maker | tazel |
| WLW | Guardian | vyrn |
| AZI | Integrator | zero |

The Waterfall Guardian Plate is not on that list. It routes through adapt → ZERO geometry, not through Tazel.

## Path 1–13

`path` audits a card. It does not look for figures in pixels. Steps 1–13 keep their names: Apertio (Opening) through First Breath / Purpose.

## Refuse codes

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

Empty in-band hue is a valid reading. It is recorded. It is not a claim of concealed text.
