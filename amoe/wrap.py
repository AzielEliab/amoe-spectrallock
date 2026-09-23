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
from amoe.paint import defined_paint, lift_gray, signal_means, weak_signal, write_png
from amoe.wheel import (
    AUTHOR,
    GRID,
    LENS_CUSTODIAN,
    PAPER,
    PAPERS,
    PRODUCT,
    REFUSE_AMOE_AS_COLOR,
    REFUSE_WEAK_SIGNAL,
    SCALAR_MODES,
    SCALAR_NOTE,
    VERSION,
    WHEEL_LAW,
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


def _paint_plate(source: np.ndarray, mode: str, palette: str) -> np.ndarray | None:
    """1.3 plate for a lens. None when the label has no paint law and no membership hex."""
    key = str(mode).strip().lower()
    if palette == "wheel" and key not in WHEEL_LAW and key not in ("candle", "indent", "lemon"):
        return None
    try:
        return defined_paint(source, key, palette=palette if key in WHEEL_LAW or palette == "engine" else "wheel")
    except KeyError:
        return None


def process(
    source: np.ndarray,
    *,
    src: str,
    out_dir: Path,
    modes: list[str],
    target: str | None = None,
    inject: bool = True,
    paint: str = "wheel",
    lift: bool = False,
    indices: dict[str, float] | None = None,
    sha256_in: str | None = None,
    geom: bool = True,
    weight: bool = True,
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
    sig = signal_means(source)
    refuses: list[str] = []
    if weak_signal(sig):
        refuses.append(REFUSE_WEAK_SIGNAL)
    cells: dict[str, dict] = {}
    plates: dict[str, np.ndarray] = {}

    for mode in selected:
        result = results[mode]
        dest = result.target
        engine_name = f"{mode}.engine.png"
        engine_digest = write_png(result.rgb, out_dir / engine_name)
        lifted_name = None
        if lift:
            lifted_name = f"{mode}.lift.png"
            write_png(lift_gray(source), out_dir / lifted_name)

        plate = _paint_plate(source, mode, palette)
        wheel_name = None
        primary = engine_name
        primary_digest = engine_digest
        pass_name = "engine"
        if plate is not None:
            primary = f"{mode}.png"
            primary_digest = write_png(plate, out_dir / primary)
            plates[mode] = plate
            if palette == "wheel" and mode in WHEEL_LAW:
                wheel_name = primary
                pass_name = "wheel"
            else:
                pass_name = palette

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

    inband = {
        "tazel_inband_pct": float(probe.tazel_inband_pct),
        "vyrn_inband_pct": float(probe.vyrn_inband_pct),
    }
    geom_meta: dict | None = None
    if geom:
        from amoe.geom import save_overlay

        host = plates.get("zero")
        if host is None and plates:
            host = next(iter(plates.values()))
        if host is None:
            host = source
        geom_meta = save_overlay(host, out_dir / "geom.png", weight=weight)
    weighting = None if geom_meta is None else geom_meta.get("weighting")
    if weighting is None:
        if weight:
            from amoe.geom import harmonic_mass

            weighting = harmonic_mass(source)
        else:
            weighting = {"on": False}

    card = _base_card(
        src=src,
        sha256_in=sha256_in,
        target=target or "per-lens",
        inject=bool(inject),
        paint=palette,
        grid=list(GRID),
        cells=cells,
        amoe_scalar=scalar,
        inband=inband,
        emergence=sig["emergence"],
        undertext=sig["undertext"],
        empty_inband_hue=inband["tazel_inband_pct"] == 0 and inband["vyrn_inband_pct"] == 0,
        scalar_note=SCALAR_NOTE,
        letters_recovered=False,
        geom={"on": False} if not geom else geom_meta,
        weighting=weighting,
        score={
            "amoe_scalar": scalar,
            "wired_into": list(selected),
            "spectral_means": {mode: means[mode] for mode in measure},
            "indices_slot": slots,
        },
        refuse=refuses,
        refuses=list(refuses),
        reconstruct=False,
    )
    write_card(card, out_dir / "amoe.json")
    return card


def reading_card(source: np.ndarray, **fields: object) -> dict:
    """Scalar, in-band percents, and weak-signal refuse for one sidecar."""
    eng = _engine()
    means: dict[str, float] = {}
    inband = {"tazel_inband_pct": 0.0, "vyrn_inband_pct": 0.0}
    for mode in SCALAR_MODES:
        result = eng.analyze(source, mode, target="ink", inject=False)
        means[mode] = float(eng.luminance(result.rgb).mean())
        inband = {
            "tazel_inband_pct": float(result.tazel_inband_pct),
            "vyrn_inband_pct": float(result.vyrn_inband_pct),
        }
    sig = signal_means(source)
    refuses = [REFUSE_WEAK_SIGNAL] if weak_signal(sig) else []
    card = _base_card(
        amoe_scalar=amoe_scalar(means, empty_slots()),
        inband=inband,
        emergence=sig["emergence"],
        undertext=sig["undertext"],
        empty_inband_hue=inband["tazel_inband_pct"] == 0 and inband["vyrn_inband_pct"] == 0,
        scalar_note=SCALAR_NOTE,
        letters_recovered=False,
        transcription=None,
        spectral_means=means,
        refuse=refuses,
        refuses=list(refuses),
    )
    card.update(fields)
    card["pigment_recovery"] = False
    card["invent_letters"] = False
    card["amoe_is_field"] = False
    card["amoe_is_wiring"] = True
    card["letters_recovered"] = False
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
        try:
            image = defined_paint(source, mode, palette=kind)
        except KeyError:
            written.append(
                {
                    "mode": mode,
                    "path": None,
                    "pass": kind,
                    "note": "This lens has no paint law. It is not painted as a twelfth color.",
                }
            )
            continue
        filename = f"{mode}.{kind}.png"
        digest = write_png(image, out_dir / filename)
        written.append({"mode": mode, "path": filename, "sha256": digest, "pass": kind})
    sig = signal_means(source)
    refuses = [REFUSE_WEAK_SIGNAL] if weak_signal(sig) else []
    card = _base_card(
        paint=kind,
        files=written,
        amoe_scalar=None,
        emergence=sig["emergence"],
        undertext=sig["undertext"],
        refuse=refuses,
        refuses=list(refuses),
        letters_recovered=False,
        scalar_note=SCALAR_NOTE,
        note="Pulled structure, then the defined plate. Not a field. Not a transcription.",
    )
    write_card(card, out_dir / "paint.json")
    write_card(card, out_dir / "amoe.json")
    return card
