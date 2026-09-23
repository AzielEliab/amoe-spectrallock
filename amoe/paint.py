"""AMOE 1.3 paint law.

Pull faded structure first. Color only what was pulled. Empty paper stays
empty. Present pigment is brightened, not replaced.

Rosetta is a per-pixel wheel map. Zen is the inversion of that plate.
There is no radial pattern generator and no ninth plate.

Author: Aziel Eliab.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from amoe import ensure_vendor
from amoe.wheel import (
    ENGINE_HEX,
    FORBIDDEN_PRODUCTS,
    RING,
    RING_CW_FROM_ZERO,
    WHEEL_HEX,
    WHEEL_LAW,
    engine_rgb,
    hex_to_rgb,
    wheel_rgb,
)

ensure_vendor()

# Opacity sits in the commissioned 0.58–0.74 band so the sheet stays visible.
_OPACITY = 0.70
_CHROMA_GAIN = 1.65
_PIGMENT_KEEP = 0.30
_SCOPE_PULL = 0.28
_SCOPE_MAP = 0.72
_LUMA_STEPS = 10
_WEAK_EPS = 0.012


def _engine():
    from spectrallock import engine

    return engine


def _finite(rgb: np.ndarray) -> np.ndarray:
    return _engine().finite01(rgb)


def _luma(rgb: np.ndarray) -> np.ndarray:
    return _engine().luminance(rgb)


def _saturation(rgb: np.ndarray) -> np.ndarray:
    mx = rgb.max(axis=-1)
    mn = rgb.min(axis=-1)
    return np.where(mx <= 1e-6, 0.0, (mx - mn) / np.maximum(mx, 1e-6)).astype(np.float32)


def _stretch(lum: np.ndarray, lo_q: float = 0.02, hi_q: float = 0.98) -> np.ndarray:
    lo = float(np.quantile(lum, lo_q))
    hi = float(np.quantile(lum, hi_q))
    if hi - lo < 1e-6:
        return lum.astype(np.float32)
    return np.clip((lum - lo) / (hi - lo), 0.0, 1.0).astype(np.float32)


def _local_radius(shape: tuple[int, ...]) -> float:
    short = float(min(shape[0], shape[1]))
    return float(np.clip(short / 12.0, 1.5, 12.0))


def _equalize_paint(gray: np.ndarray) -> np.ndarray:
    """Histogram equalize. A flat field stays flat.

    Bin index matches ``numpy.histogram`` (value * 256). A one-bin page has
    no darks to lift, so it is returned unchanged.
    """
    g = np.clip(gray.astype(np.float32), 0.0, 1.0)
    if float(g.max() - g.min()) < 1e-5:
        return g
    hist, _ = np.histogram(g.ravel(), bins=256, range=(0.0, 1.0))
    cdf = hist.cumsum().astype(np.float64)
    if cdf[-1] <= 0:
        return g
    cdf = cdf / cdf[-1]
    idx = np.clip(np.floor(g * 256.0).astype(np.int32), 0, 255)
    return cdf[idx].astype(np.float32)


def _faint_mask(rgb: np.ndarray) -> np.ndarray:
    """Marks darker than local paper, plus equalized darks.

    This is the wash / verso / thin-ink mask. It does not invent strokes.
    """
    eng = _engine()
    src = _finite(rgb)
    lum = _luma(src)
    stretched = _stretch(lum)
    equalized = _equalize_paint(stretched)
    local = eng.blur_gray(stretched, _local_radius(stretched.shape))
    darker = np.clip(local - stretched, 0.0, 1.0)
    darker = np.where(darker < 0.01, 0.0, darker)
    eq_dark = np.clip(0.45 - equalized, 0.0, 1.0)
    # Equalized darks only count where the page actually has spread.
    if float(stretched.max() - stretched.min()) < 1e-5:
        eq_dark = np.zeros_like(eq_dark)
    mask = np.clip(darker * 3.2 + eq_dark * 0.85, 0.0, 1.0)
    return mask.astype(np.float32)


def _has_structure(rgb: np.ndarray, mask: np.ndarray | None = None) -> bool:
    """True when the leaf has something to color. Flat paper does not."""
    src = _finite(rgb)
    marks = _faint_mask(src) if mask is None else mask
    if float(marks.mean()) >= 0.015:
        return True
    if float(marks.max()) >= 0.12:
        return True
    return float(np.std(_luma(src))) >= 0.03


def _pull_faint(rgb: np.ndarray) -> np.ndarray:
    """Stretch luma (p2–p98), equalize, lift paper, drop marks.

    Chroma already in those pixels is brightened (gain ~1.65).
    Gray paper does not receive a new hue at this step.
    """
    src = _finite(rgb)
    lum = _luma(src)
    stretched = _stretch(lum)
    equalized = _equalize_paint(stretched)
    # Equalize informs the mask; the working luma stays the stretch so a
    # flat field is not remapped into a false ramp.
    mask = _faint_mask(src)
    luma_out = np.clip(stretched + 0.08 * (1.0 - mask) - 0.28 * mask, 0.0, 1.0)
    # A touch of the equalized darks, only where the mask already agrees.
    luma_out = np.clip(luma_out - 0.06 * mask * (1.0 - equalized), 0.0, 1.0)
    residual = src - lum[..., None]
    sat = _saturation(src)[..., None]
    gate = np.clip((sat - 0.04) / 0.12, 0.0, 1.0)
    gain = 1.0 + (_CHROMA_GAIN - 1.0) * gate
    out = luma_out[..., None] + residual * gain
    return np.clip(out, 0.0, 1.0).astype(np.float32)


def signal_means(rgb: np.ndarray) -> dict[str, float]:
    """Emergence and undertext means. Empty is a valid reading."""
    src = _finite(rgb)
    mask = _faint_mask(src)
    stretched = _stretch(_luma(src))
    deep = stretched < 0.16
    wash = (mask > 0.04) & ~deep
    under = mask * wash.astype(np.float32)
    return {
        "emergence": float(mask.mean()),
        "undertext": float(under.mean()),
    }


def weak_signal(means: dict[str, float], eps: float = _WEAK_EPS) -> bool:
    return float(means["emergence"]) < eps and float(means["undertext"]) < eps


def _as_rgb(color: tuple[float, float, float] | str) -> np.ndarray:
    if isinstance(color, str):
        return np.asarray(hex_to_rgb(color), dtype=np.float32)
    return np.asarray(color, dtype=np.float32)


def _overlay_hex(rgb: np.ndarray, color: tuple[float, float, float] | str) -> np.ndarray:
    """Single-hex sheet on pulled structure. Empty paper stays empty.

    Paper is a mix of parchment and the wheel hex. Marks are a darker tint
    of the same hex. Original pigment above the saturation gate is partly
    kept so a painted robe stays its own color, brighter.
    """
    src = _finite(rgb)
    pulled = _pull_faint(src)
    mask = _faint_mask(src)
    if not _has_structure(src, mask):
        return pulled

    tint = _as_rgb(color).reshape(1, 1, 3)
    paper = pulled * (1.0 - _OPACITY) + tint * _OPACITY
    dark = tint * 0.38
    marks = dark * 0.82 + pulled * 0.18
    weight = mask[..., None]
    sheet = paper * (1.0 - weight) + marks * weight

    sat = _saturation(src)
    bright = pulled
    hi = sat > 0.35
    if np.any(hi):
        lum = _luma(bright)
        residual = bright - lum[..., None]
        lifted = np.clip(lum * 1.08 + 0.03, 0.0, 1.0)
        boosted = np.clip(lifted[..., None] + residual, 0.0, 1.0)
        bright = np.where(hi[..., None], boosted, bright)
    keep = np.where(sat > 0.35, 0.62, np.where(sat > 0.18, _PIGMENT_KEEP, 0.0)).astype(np.float32)
    out = sheet * (1.0 - keep[..., None]) + bright * keep[..., None]
    return np.clip(out, 0.0, 1.0).astype(np.float32)


def _ring_colors() -> np.ndarray:
    return np.stack(
        [np.asarray(hex_to_rgb(RING_CW_FROM_ZERO[name]), dtype=np.float32) for name in RING],
        axis=0,
    )


def _pixel_index(rgb: np.ndarray) -> np.ndarray:
    """Luma bins plus a small saturation-gated hue lean. Not a radial pattern."""
    src = _finite(rgb)
    lum = _luma(src)
    steps = float(_LUMA_STEPS)
    quant = np.clip(np.floor(np.clip(lum, 0.0, 0.999999) * steps), 0.0, steps - 1.0)
    base = quant * (5.0 / (steps - 1.0))
    sat = _saturation(src)
    gate = np.clip((sat - 0.08) / 0.20, 0.0, 1.0)
    red, green, blue = src[..., 0], src[..., 1], src[..., 2]
    # Opponent chroma. Gray paper has gate 0, so the lean adds nothing.
    ang = np.arctan2(green - blue, red - 0.5 * (green + blue))
    extra = (ang / np.pi) * 0.35 * gate
    return np.mod(base + extra, 6.0).astype(np.float32)


def _map_field(rgb: np.ndarray) -> np.ndarray:
    """Index the six ring colors and interpolate neighbors.

    Paper gets the mapped color light. Marks get it dark.
    Painted robes keep about 30% of their original pigment.
    """
    src = _finite(rgb)
    idx = _pixel_index(src)
    colors = _ring_colors()
    i0 = np.floor(idx).astype(np.int32) % 6
    frac = (idx - np.floor(idx))[..., None]
    i1 = (i0 + 1) % 6
    mapped = colors[i0] * (1.0 - frac) + colors[i1] * frac
    mask = _faint_mask(src)[..., None]
    light = np.clip(mapped + (1.0 - mapped) * 0.42, 0.0, 1.0)
    dark = np.clip(mapped * 0.40, 0.0, 1.0)
    field = light * (1.0 - mask) + dark * mask
    sat = _saturation(src)
    robe = (sat >= 0.22)[..., None]
    field = np.where(robe, (1.0 - _PIGMENT_KEEP) * field + _PIGMENT_KEEP * src, field)
    return np.clip(field, 0.0, 1.0).astype(np.float32)


def _rosetta_plate(rgb: np.ndarray) -> np.ndarray:
    """Pulled structure ~28% + mapped field ~72%. Empty paper stays empty."""
    src = _finite(rgb)
    pulled = _pull_faint(src)
    if not _has_structure(src):
        return pulled
    mapped = _map_field(src)
    return np.clip(_SCOPE_PULL * pulled + _SCOPE_MAP * mapped, 0.0, 1.0).astype(np.float32)


def _scope_from_pixels(rgb: np.ndarray, invert: bool = False) -> np.ndarray:
    """Full-scope color overlay from pixelation.

    invert flips that same plate. It does not build a second map.
    """
    plate = _rosetta_plate(rgb)
    if invert:
        return np.clip(1.0 - plate, 0.0, 1.0).astype(np.float32)
    return plate


def _rosetta_fusion(rgb: np.ndarray) -> np.ndarray:
    """Rosetta plate: the pixel-scope map, not a green sheet."""
    return _scope_from_pixels(rgb, invert=False)


def _zen_balance(rgb: np.ndarray) -> np.ndarray:
    """ZEN = clip(1 − Rosetta pixel map). Same leaf, inverted values."""
    return np.clip(1.0 - _rosetta_fusion(rgb), 0.0, 1.0).astype(np.float32)


def _balance_mix(rgb: np.ndarray) -> np.ndarray:
    """α·Zen + (1−α)·Chaos. Reweights the two plates. Never invents marks."""
    src = _finite(rgb)
    if not _has_structure(src):
        return _pull_faint(src)
    zen = _zen_balance(src)
    chaos = _overlay_hex(src, wheel_rgb("chaos"))
    zl = _luma(zen)
    cl = _luma(chaos)
    alpha = np.clip((1.0 + (zl - cl) / (zl + cl + 1e-6)) * 0.5, 0.0, 1.0)[..., None]
    return np.clip(alpha * zen + (1.0 - alpha) * chaos, 0.0, 1.0).astype(np.float32)


def defined_paint(rgb: np.ndarray, mode: str, *, palette: str = "wheel") -> np.ndarray:
    """Operator plate (`wheel`) or membership hex (`engine`)."""
    key = str(mode).strip().lower()
    kind = str(palette or "wheel").strip().lower()
    if kind == "wheel":
        law = WHEEL_LAW.get(key)
        if law == "single-hex":
            return _overlay_hex(rgb, wheel_rgb(key))
        if law == "pixel-scope" or key == "rosetta":
            return _rosetta_fusion(rgb)
        if law == "invert" or key == "zen":
            return _zen_balance(rgb)
        if law == "bsa-mix" or key == "balance":
            return _balance_mix(rgb)
        if key in ENGINE_HEX:
            return _overlay_hex(rgb, engine_rgb(key))
        raise KeyError(key)
    if kind == "engine":
        return _overlay_hex(rgb, engine_rgb(key))
    raise KeyError(kind)


def ink_mask(rgb: np.ndarray) -> np.ndarray:
    """Darker luminance is ink already in the picture. No new strokes."""
    eng = _engine()
    lum = eng.luminance(eng.finite01(rgb))
    return np.clip(1.0 - lum, 0.0, 1.0).astype(np.float32)


def false_color(rgb: np.ndarray, color: tuple[float, float, float]) -> np.ndarray:
    """Legacy luminance tint. The 1.3 operator path is defined_paint."""
    return _overlay_hex(rgb, color)


def wheel_paint(rgb: np.ndarray, mode: str) -> np.ndarray:
    """Operator plate for one lens label."""
    return defined_paint(rgb, mode, palette="wheel")


def engine_paint(rgb: np.ndarray, mode: str) -> np.ndarray:
    """Membership hex only. Not analyze() and not pigment restore."""
    return defined_paint(rgb, mode, palette="engine")


def lift_gray(rgb: np.ndarray) -> np.ndarray:
    """ZERO lift: percentile stretch, equalize, unsharp. Present pixels only.

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
