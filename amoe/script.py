"""Script track and image recovery. Separate from the paint law.

Crop chrome, run ZERO, search with geometry, score lens residuals, then
contrast what is already there. No new strokes. No transcription is
declared as fact. The human still reads the page.

Author: Aziel Eliab.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from amoe import ensure_vendor
from amoe.geom import harmonic_mass, save_overlay
from amoe.paint import _faint_mask, _pull_faint, defined_paint, write_png
from amoe.wheel import GRID, WHEEL_LAW
from amoe.wrap import reading_card, write_card

ensure_vendor()


def _engine():
    from spectrallock import engine

    return engine


def crop_folio(rgb: np.ndarray) -> tuple[np.ndarray, dict]:
    """Drop viewer chrome at the rim. Leave the leaf when the rim is page."""
    eng = _engine()
    src = eng.finite01(rgb)
    lum = eng.luminance(src)
    height, width = lum.shape
    box = [0, 0, int(width), int(height)]
    if min(height, width) < 16:
        return src, {"cropped": False, "chrome": False, "box": box}

    limit = max(1, int(round(min(height, width) * 0.08)))

    def is_chrome(strip: np.ndarray, interior: np.ndarray) -> bool:
        if strip.size == 0 or float(strip.var()) > 0.003:
            return False
        mean = float(strip.mean())
        inn = float(interior.mean())
        if mean < 0.08 and inn > 0.40:
            return True
        if mean > 0.97 and inn < 0.92:
            return True
        return False

    y0 = 0
    for i in range(limit):
        if is_chrome(lum[i], lum[limit : height // 2]):
            y0 = i + 1
        else:
            break
    y1 = height
    for i in range(limit):
        row = height - 1 - i
        if is_chrome(lum[row], lum[height // 2 : height - limit]):
            y1 = row
        else:
            break
    x0 = 0
    for i in range(limit):
        if is_chrome(lum[:, i], lum[:, limit : width // 2]):
            x0 = i + 1
        else:
            break
    x1 = width
    for i in range(limit):
        col = width - 1 - i
        if is_chrome(lum[:, col], lum[:, width // 2 : width - limit]):
            x1 = col
        else:
            break
    if y1 - y0 < 8 or x1 - x0 < 8:
        return src, {"cropped": False, "chrome": False, "box": box}
    cropped = y0 > 0 or x0 > 0 or y1 < height or x1 < width
    if not cropped:
        return src, {"cropped": False, "chrome": False, "box": box}
    return src[y0:y1, x0:x1], {
        "cropped": True,
        "chrome": True,
        "box": [int(x0), int(y0), int(x1), int(y1)],
    }


def contrast_calibrate(rgb: np.ndarray) -> np.ndarray:
    """Stretch contrast of pixels already present. Does not add strokes."""
    eng = _engine()
    src = eng.finite01(rgb)
    lum = eng.luminance(src)
    lo = float(np.quantile(lum, 0.02))
    hi = float(np.quantile(lum, 0.98))
    if hi - lo < 1e-6:
        stretched = lum
    else:
        stretched = np.clip((lum - lo) / (hi - lo), 0.0, 1.0)
    residual = src - lum[..., None]
    return np.clip(stretched[..., None] + residual, 0.0, 1.0).astype(np.float32)


def score_lenses(rgb: np.ndarray) -> dict[str, float]:
    """Residual contrast of each SpectralLock lens. Not a letter score."""
    eng = _engine()
    scores: dict[str, float] = {}
    for mode in GRID:
        result = eng.analyze(rgb, mode, inject=False, target="ink")
        scores[mode] = float(np.std(eng.luminance(result.rgb)))
    return scores


def _winner(scores: dict[str, float]) -> str:
    return max(GRID, key=lambda mode: (scores.get(mode, 0.0), -GRID.index(mode)))


def preocr_image(rgb: np.ndarray) -> np.ndarray:
    """Darken and tighten residual strokes. Contrast shift only. No new strokes."""
    eng = _engine()
    pulled = _pull_faint(rgb)
    mask = _faint_mask(rgb)[..., None]
    darker = np.clip(pulled * (1.0 - 0.55 * mask), 0.0, 1.0)
    lum = eng.luminance(darker)
    sharp = eng.unsharp(lum, amount=0.8, radius=0.8)
    residual = darker - lum[..., None]
    tightened = np.clip(sharp[..., None] + residual, 0.0, 1.0)
    out = pulled * (1.0 - mask) + tightened * mask
    return np.clip(out, 0.0, 1.0).astype(np.float32)


def _geom(rgb: np.ndarray, path: Path, *, geom: bool, weight: bool) -> dict:
    if not geom:
        weighting = harmonic_mass(rgb) if weight else {"on": False}
        return {"on": False, "drawn": False, "invent_figures": False, "weighting": weighting}
    return save_overlay(rgb, path, weight=weight)


def recover_image(
    rgb: np.ndarray,
    *,
    src: str,
    out_dir: Path,
    sha256_in: str | None = None,
    geom: bool = True,
    weight: bool = True,
) -> dict:
    """Image track: pull, ZERO sheet, geom, and the grid when the page is faint."""
    from amoe.adapt import page_condition

    out_dir.mkdir(parents=True, exist_ok=True)
    condition = page_condition(rgb)
    pulled = _pull_faint(rgb)
    zero = defined_paint(rgb, "zero", palette="wheel")
    files = {
        "pull": {"path": "image_pull.png", "sha256": write_png(pulled, out_dir / "image_pull.png")},
        "zero": {"path": "image_zero.png", "sha256": write_png(zero, out_dir / "image_zero.png")},
    }
    if condition["reconstruct_ok"]:
        scaled = []
        for mode in GRID:
            if mode not in WHEEL_LAW and mode not in {"candle", "indent", "lemon"}:
                continue
            image = defined_paint(rgb, mode, palette="wheel")
            filename = f"image_{mode}.png"
            scaled.append(
                {"mode": mode, "path": filename, "sha256": write_png(image, out_dir / filename)}
            )
        files["grid"] = scaled
    geom_meta = _geom(zero, out_dir / "image_geom.png", geom=geom, weight=weight)
    card = reading_card(
        rgb,
        src=src,
        sha256_in=sha256_in,
        track="image",
        condition=condition,
        files=files,
        geom=geom_meta,
        weighting=geom_meta.get("weighting"),
        note=(
            "Structure only. No glyph invention. "
            "Pigment restore stays a SpectralLock product door."
        ),
    )
    write_card(card, out_dir / "amoe.json")
    return card


def recover_script(
    rgb: np.ndarray,
    *,
    src: str,
    out_dir: Path,
    sha256_in: str | None = None,
    mode: str | None = None,
    geom: bool = True,
    weight: bool = True,
) -> dict:
    """Script track. Residuals of marks already on the leaf. No recovered text."""
    eng = _engine()
    out_dir.mkdir(parents=True, exist_ok=True)
    cropped, crop_meta = crop_folio(rgb)
    zero = eng.analyze(cropped, "zero", target="ink", inject=False)
    files = {
        "zero_engine": {
            "path": "script_zero_engine.png",
            "sha256": write_png(zero.rgb, out_dir / "script_zero_engine.png"),
        },
        "zero": {
            "path": "script_zero.png",
            "sha256": write_png(
                defined_paint(cropped, "zero", palette="wheel"),
                out_dir / "script_zero.png",
            ),
        },
    }
    geom_meta = _geom(zero.rgb, out_dir / "script_geom.png", geom=geom, weight=weight)
    scores = score_lenses(cropped)
    winner = _winner(scores)
    focus = str(mode).strip().lower() if mode else winner
    try:
        focus = eng.resolve_mode(focus)
    except ValueError:
        focus = winner
    residual = eng.analyze(cropped, focus, target="ink", inject=False).rgb
    calibrated = contrast_calibrate(residual)
    back = eng.analyze(calibrated, "zero", target="ink", inject=False).rgb
    isolated = contrast_calibrate(back)
    files["residual"] = {
        "mode": focus,
        "path": "script_residual.png",
        "sha256": write_png(residual, out_dir / "script_residual.png"),
    }
    files["calibrated"] = {
        "path": "script_calibrated.png",
        "sha256": write_png(calibrated, out_dir / "script_calibrated.png"),
    }
    files["isolated"] = {
        "path": "script_isolated.png",
        "sha256": write_png(isolated, out_dir / "script_isolated.png"),
    }
    card = reading_card(
        cropped,
        src=src,
        sha256_in=sha256_in,
        track="script",
        crop=crop_meta,
        scores=scores,
        winner=winner,
        focus=focus,
        files=files,
        geom=geom_meta,
        weighting=geom_meta.get("weighting"),
        note=(
            "Readable contrast of existing marks. "
            "Runtime does not declare recovered letters as fact."
        ),
    )
    write_card(card, out_dir / "amoe.json")
    return card


def route_page(
    rgb: np.ndarray,
    *,
    src: str,
    out_dir: Path,
    sha256_in: str | None = None,
    geom: bool = True,
    weight: bool = True,
) -> dict:
    """Score every lens and paint the winner. The score is residual contrast."""
    out_dir.mkdir(parents=True, exist_ok=True)
    scores = score_lenses(rgb)
    winner = _winner(scores)
    plate = defined_paint(rgb, winner, palette="wheel")
    geom_meta = _geom(plate, out_dir / "route_geom.png", geom=geom, weight=weight)
    card = reading_card(
        rgb,
        src=src,
        sha256_in=sha256_in,
        track="route",
        scores=scores,
        winner=winner,
        files={
            "winner": {
                "mode": winner,
                "path": "route_winner.png",
                "sha256": write_png(plate, out_dir / "route_winner.png"),
            }
        },
        geom=geom_meta,
        weighting=geom_meta.get("weighting"),
        note="Winner is the highest residual contrast. Not a transcription.",
    )
    write_card(card, out_dir / "amoe.json")
    return card


def preocr_page(
    rgb: np.ndarray,
    *,
    src: str,
    out_dir: Path,
    sha256_in: str | None = None,
) -> dict:
    """Optional pre-OCR darkening. Contrast shift. No new strokes. No text."""
    out_dir.mkdir(parents=True, exist_ok=True)
    image = preocr_image(rgb)
    card = reading_card(
        rgb,
        src=src,
        sha256_in=sha256_in,
        track="preocr",
        files={
            "preocr": {
                "path": "preocr.png",
                "sha256": write_png(image, out_dir / "preocr.png"),
            }
        },
        note="Darken and tighten strokes already in the mask. No new strokes. No OCR text.",
    )
    write_card(card, out_dir / "amoe.json")
    return card


def together_page(
    rgb: np.ndarray,
    *,
    src: str,
    out_dir: Path,
    sha256_in: str | None = None,
    geom: bool = True,
    weight: bool = True,
) -> dict:
    """Script search, then image isolation, in the same directory."""
    out_dir.mkdir(parents=True, exist_ok=True)
    script_card = recover_script(
        rgb,
        src=src,
        out_dir=out_dir,
        sha256_in=sha256_in,
        geom=geom,
        weight=weight,
    )
    image_card = recover_image(
        rgb,
        src=src,
        out_dir=out_dir,
        sha256_in=sha256_in,
        geom=geom,
        weight=weight,
    )
    card = reading_card(
        rgb,
        src=src,
        sha256_in=sha256_in,
        track="together",
        order=["script", "image"],
        script={
            "winner": script_card.get("winner"),
            "focus": script_card.get("focus"),
            "files": script_card.get("files"),
            "crop": script_card.get("crop"),
        },
        image={
            "condition": image_card.get("condition"),
            "files": image_card.get("files"),
        },
        note=(
            "Script search, then image isolation. Same outdir. "
            "No recovered letters are declared as fact."
        ),
    )
    write_card(card, out_dir / "amoe.json")
    return card
