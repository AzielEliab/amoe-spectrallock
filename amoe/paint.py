"""Luminance ink mask, wheel/engine false-color, and lift.

Wheel paint recolors a luminance ink mask. It does not recover pigment
and it does not write letters that are not already in the pixels.
Engine analyze() is a different pass and is not reimplemented here.

Author: Aziel Eliab.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from amoe import ensure_vendor
from amoe.wheel import FORBIDDEN_PRODUCTS, engine_rgb, wheel_rgb

ensure_vendor()


def _engine():
    from spectrallock import engine

    return engine


def ink_mask(rgb: np.ndarray) -> np.ndarray:
    """Darker luminance is ink already in the picture. No new strokes."""
    eng = _engine()
    lum = eng.luminance(eng.finite01(rgb))
    return np.clip(1.0 - lum, 0.0, 1.0).astype(np.float32)


def false_color(rgb: np.ndarray, color: tuple[float, float, float]) -> np.ndarray:
    """False-color a luminance ink mask with one labeled palette color."""
    eng = _engine()
    lum = eng.luminance(eng.finite01(rgb))
    mask = np.clip(1.0 - lum, 0.0, 1.0).astype(np.float32)[..., None]
    gray = np.stack([lum, lum, lum], axis=-1)
    tint = np.asarray(color, dtype=np.float32).reshape(1, 1, 3)
    out = gray * (1.0 - mask) + tint * mask
    return np.clip(out, 0.0, 1.0).astype(np.float32)


def wheel_paint(rgb: np.ndarray, mode: str) -> np.ndarray:
    """Gallery / --paint wheel. Uses the live wheel hex for this label only."""
    return false_color(rgb, wheel_rgb(mode))


def engine_paint(rgb: np.ndarray, mode: str) -> np.ndarray:
    """Lens-card false-color. Display palette only — not analyze() and not pigment."""
    return false_color(rgb, engine_rgb(mode))


def lift_gray(rgb: np.ndarray) -> np.ndarray:
    """Percentile stretch, equalize, unsharp. Present pixels only.

    Lift ruling and foxing. It does not transcribe missing text.
    """
    eng = _engine()
    lum = eng.luminance(eng.finite01(rgb))
    lo = float(np.quantile(lum, 0.01))
    hi = float(np.quantile(lum, 0.99))
    if hi - lo < 1e-6:
        stretched = lum.astype(np.float32)
    else:
        stretched = np.clip((lum - lo) / (hi - lo), 0.0, 1.0).astype(np.float32)
    sharpened = eng.unsharp(eng.equalize(stretched))
    return eng.gray_to_rgb(sharpened)


def write_png(rgb: np.ndarray, path: Path) -> str:
    """Write one PNG. Refuses amoe.png / amoe_field.png as products."""
    name = path.name.lower()
    if name in FORBIDDEN_PRODUCTS:
        from amoe import AmoeError
        from amoe.wheel import REFUSE_AMOE_AS_COLOR

        raise AmoeError(REFUSE_AMOE_AS_COLOR, path=str(path))
    eng = _engine()
    data = eng.png_bytes(rgb)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return eng.sha256_hex(data)
