"""Run SpectralLock on the grid and attach one AMOE wiring card.

process() does not reimplement analyze, apply_target, inject, in-band
math, or pigment restore. pigment_recovery stays false.

Author: Aziel Eliab.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from amoe import AmoeError, ensure_vendor
from amoe.paint import engine_paint, lift_gray, wheel_paint, write_png
from amoe.wheel import (
    AUTHOR,
    GRID,
    LENS_CUSTODIAN,
    PAPER,
    PAPERS,
    PRODUCT,
    REFUSE_AMOE_AS_COLOR,
    REFUSE_EMPTY_HUE,
    SCALAR_MODES,
    VERSION,
    WHEEL_HEX,
    amoe_scalar,
    empty_slots,
    reject_name,
)

ensure_vendor()


def _engine():
    from spectrallock import engine

    return engine


def parse_indices(items: list[str] | None) -> dict[str, float]:
    """SLOT keys only. Unknown keys are not added to the formula."""
    slots = empty_slots()
    for item in items or []:
        if "=" not in str(item):
            raise AmoeError("AMOE-BAD-INDEX", item=item)
        key, raw = str(item).split("=", 1)
        name = key.strip().upper()
        if name not in slots:
            raise AmoeError("AMOE-BAD-INDEX", key=name)
        value = float(raw)
        if value < 0.0 or value > 1.0:
            raise AmoeError("AMOE-BAD-INDEX", key=name, value=value)
        slots[name] = value
    return slots


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _target_for(mode: str, target: str | None) -> str:
    if target:
        return target
    if mode == "indent":
        return "page"
    return "ink"


def _json_ready(value: object) -> object:
    if isinstance(value, dict):
        return {str(k): _json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(v) for v in value]
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.integer):
        return int(value)
    return value


def write_card(card: dict, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_json_ready(card), indent=2) + "\n", encoding="utf-8")
    return path


def _base_card(**fields: object) -> dict:
    card = {
        "product": PRODUCT,
        "version": VERSION,
        "paper": PAPER,
        "author": AUTHOR,
        "amoe_is_field": False,
        "amoe_is_wiring": True,
        "invent_letters": False,
        "pigment_recovery": False,
        "reconstruct": False,
    }
    card.update(fields)
    return card


def invention_card(code: str, note: str | None = None) -> dict:
    """Keep the operator note. Do not write the glyphs."""
    return _base_card(
        refuse=code,
        refuses=[code],
        operator_note=note,
        grid=list(GRID),
        cells={},
        score=None,
    )


def process(
    source: np.ndarray,
    *,
    src: str,
    out_dir: Path,
    modes: list[str],
    target: str | None = None,
    inject: bool = True,
    paint: str = "engine",
    lift: bool = False,
    indices: dict[str, float] | None = None,
    sha256_in: str | None = None,
) -> dict:
    """Measure the requested cells and write amoe.json. Never amoe.png."""
    eng = _engine()
    out_dir.mkdir(parents=True, exist_ok=True)
    palette = str(paint or "engine").strip().lower()
    if palette not in {"engine", "wheel"}:
        raise AmoeError("AMOE-BAD-PAINT", paint=palette)

    selected: list[str] = []
    for name in modes:
        code = reject_name(name)
        if code:
            raise AmoeError(code, mode=name)
        key = eng.resolve_mode(name)
        if key not in selected:
            selected.append(key)

    slots = empty_slots()
    if indices:
        for key, value in indices.items():
            name = str(key).strip().upper()
            if name not in slots:
                raise AmoeError("AMOE-BAD-INDEX", key=name)
            slots[name] = float(value)

    measure: list[str] = []
    for name in [*selected, *SCALAR_MODES]:
        if name not in measure:
            measure.append(name)

    results = {}
    means: dict[str, float] = {}
    for mode in measure:
        dest = _target_for(mode, target)
        results[mode] = eng.analyze(source, mode, target=dest, inject=inject)
        means[mode] = float(eng.luminance(results[mode].rgb).mean())

    scalar = amoe_scalar(means, slots)
    probe = results[selected[0]]
    empty = probe.tazel_inband_pct == 0 and probe.vyrn_inband_pct == 0
    cells: dict[str, dict] = {}

    for mode in selected:
        result = results[mode]
        dest = result.target
        engine_rgb = result.rgb
        engine_name = f"{mode}.engine.png" if palette == "wheel" else f"{mode}.png"
        engine_digest = write_png(engine_rgb, out_dir / engine_name)
        lifted_name = None
        if lift:
            lifted_name = f"{mode}.lift.png"
            write_png(lift_gray(engine_rgb), out_dir / lifted_name)

        wheel_name = None
        primary = engine_name
        pass_name = "engine"
        if palette == "wheel" and mode in WHEEL_HEX:
            wheel_name = f"{mode}.png"
            # Mask comes from the engine cell. The file itself is wheel-only.
            write_png(wheel_paint(engine_rgb, mode), out_dir / wheel_name)
            primary = wheel_name
            pass_name = "wheel"
        elif palette == "wheel":
            pass_name = "engine"

        primary_digest = engine_digest
        if primary != engine_name:
            primary_digest = eng.sha256_hex((out_dir / primary).read_bytes())

        cells[mode] = {
            "paper": PAPERS[mode],
            "target": dest,
            "inject": bool(result.inject),
            "inject_applied": bool(result.inject_applied),
            "inband": {
                "tazel_inband_pct": float(result.tazel_inband_pct),
                "vyrn_inband_pct": float(result.vyrn_inband_pct),
            },
            "com": {"x": float(result.com[0]), "y": float(result.com[1])},
            "mean_luma": means[mode],
            "path": primary,
            "engine_path": engine_name,
            "sha256": primary_digest,
            "custodian": LENS_CUSTODIAN.get(mode),
            "wheel_path": wheel_name,
            "lift_path": lifted_name,
            "amoe_scalar": scalar,
            "pass": pass_name,
        }

    if sha256_in is None:
        sha256_in = eng.sha256_hex(eng.png_bytes(source))

    card = _base_card(
        src=src,
        sha256_in=sha256_in,
        target=target or "per-lens",
        inject=bool(inject),
        paint=palette,
        grid=list(GRID),
        cells=cells,
        score={
            "amoe_scalar": scalar,
            "wired_into": list(selected),
            "spectral_means": {mode: means[mode] for mode in measure},
            "indices_slot": slots,
        },
        refuse=REFUSE_EMPTY_HUE if empty else None,
        reconstruct=False,
    )
    write_card(card, out_dir / "amoe.json")
    return card


def load_page(path: Path) -> tuple[np.ndarray, str]:
    eng = _engine()
    rgb = eng.load_rgb(str(path))
    return rgb, _sha256_file(path)


def refuse_product(name: str) -> None:
    if name.lower() in {"amoe.png", "amoe_field.png"} or reject_name(name) == REFUSE_AMOE_AS_COLOR:
        raise AmoeError(REFUSE_AMOE_AS_COLOR, name=name)


def paint_only(
    source: np.ndarray,
    *,
    out_dir: Path,
    palette: str,
    modes: list[str],
) -> dict:
    """False-color pass. This is not SpectralLock analyze() and not pigment."""
    out_dir.mkdir(parents=True, exist_ok=True)
    kind = palette.strip().lower()
    if kind not in {"wheel", "engine"}:
        raise AmoeError("AMOE-BAD-PAINT", paint=kind)
    written = []
    for mode in modes:
        code = reject_name(mode)
        if code:
            raise AmoeError(code, mode=mode)
        if kind == "wheel" and mode not in WHEEL_HEX:
            written.append(
                {
                    "mode": mode,
                    "path": None,
                    "pass": "engine",
                    "note": "This lens has no wheel hex. It is not painted as a twelfth color.",
                }
            )
            continue
        if kind == "wheel":
            image = wheel_paint(source, mode)
        else:
            image = engine_paint(source, mode)
        filename = f"{mode}.{kind}.png"
        digest = write_png(image, out_dir / filename)
        written.append({"mode": mode, "path": filename, "sha256": digest, "pass": kind})
    card = _base_card(
        paint=kind,
        files=written,
        refuse=None,
        note="False-color of a luminance ink mask. Labeled pass. Not a field.",
    )
    write_card(card, out_dir / "paint.json")
    return card
