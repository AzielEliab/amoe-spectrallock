"""Adaptive route. Reconstruct only when the page is faint or near-gone.

contrast = std(luma)/255
span = (p90-p10)/255
near_gone if contrast < 0.14 and span < 0.35
faint if contrast < 0.18 and span < 0.45
else present

A present page refuses AMOE-RECONSTRUCT-NOT-NEEDED.
A call with no page refuses AMOE-RECONSTRUCT-USE-ADAPT.
Waterfall plates route here, then ZERO geometry — not through Tazel.

Author: Aziel Eliab.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from amoe import ensure_vendor
from amoe.gallery import save_gallery
from amoe.geom import save_overlay
from amoe.paint import defined_paint, lift_gray, write_png
from amoe.wheel import (
    AUTHOR,
    CENTER,
    GRID,
    PAPER,
    REFUSE_RECONSTRUCT_NOT_NEEDED,
    REFUSE_RECONSTRUCT_USE_ADAPT,
    RING,
    VERSION,
    WHEEL_LAW,
)
from amoe.wrap import _base_card, process, write_card

ensure_vendor()


def page_condition(rgb: np.ndarray) -> dict:
    """Classify the page from luminance contrast and percentile span."""
    from spectrallock.engine import finite01, luminance

    luma = luminance(finite01(rgb)) * 255.0
    contrast = float(np.std(luma) / 255.0)
    p10, p90 = np.percentile(luma, [10, 90])
    span = float((float(p90) - float(p10)) / 255.0)
    if contrast < 0.14 and span < 0.35:
        state = "near_gone"
    elif contrast < 0.18 and span < 0.45:
        state = "faint"
    else:
        state = "present"
    return {
        "state": state,
        "contrast": contrast,
        "span": span,
        "reconstruct_ok": state in {"faint", "near_gone"},
    }


def _caption(rgb: np.ndarray, text: str) -> np.ndarray:
    from PIL import Image, ImageDraw

    u8 = np.clip(np.round(np.clip(rgb, 0.0, 1.0) * 255.0), 0, 255).astype(np.uint8)
    image = Image.fromarray(u8, "RGB")
    bar = 22
    canvas = Image.new("RGB", (image.width, image.height + bar), (28, 26, 24))
    canvas.paste(image, (0, bar))
    draw = ImageDraw.Draw(canvas)
    draw.text((6, 4), text, fill=(223, 210, 181))
    return np.asarray(canvas, dtype=np.float32) / 255.0


def reconstruct(page: np.ndarray | None, **kwargs: object) -> dict:
    """Alias of adapt when a page is given. No page is a hard refuse."""
    if page is None:
        card = _base_card(
            refuse=REFUSE_RECONSTRUCT_USE_ADAPT,
            reconstruct=False,
            condition=None,
        )
        out = kwargs.get("out_dir")
        if isinstance(out, Path):
            write_card(card, out / "adapt.json")
        return card
    return adapt(page, **kwargs)  # type: ignore[arg-type]


def adapt(
    rgb: np.ndarray,
    *,
    src: str,
    out_dir: Path,
    sha256_in: str | None = None,
    with_grid: bool = False,
    target: str | None = None,
    inject: bool = True,
    indices: dict[str, float] | None = None,
) -> dict:
    """Preferred entry for an unknown page."""
    out_dir.mkdir(parents=True, exist_ok=True)
    condition = page_condition(rgb)
    card = _base_card(
        src=src,
        sha256_in=sha256_in,
        paper=PAPER,
        author=AUTHOR,
        version=VERSION,
        condition=condition,
        reconstruct=bool(condition["reconstruct_ok"]),
        route="ZERO geom" if condition["reconstruct_ok"] else None,
        waterfall="Waterfall Guardian Plate routes through adapt → ZERO geom, not Tazel.",
    )

    if condition["state"] == "present":
        card["refuse"] = REFUSE_RECONSTRUCT_NOT_NEEDED
        card["reconstruct"] = False
        geom = save_overlay(rgb, out_dir / "geom.png")
        card["geom"] = geom
        if with_grid:
            grid = process(
                rgb,
                src=src,
                out_dir=out_dir / "grid",
                modes=list(GRID),
                target=target,
                inject=inject,
                paint="wheel",
                indices=indices,
                sha256_in=sha256_in,
            )
            card["grid"] = "grid/amoe.json"
            card["grid_refuse"] = grid.get("refuse")
        write_card(card, out_dir / "adapt.json")
        return card

    from spectrallock.engine import analyze

    zero = analyze(rgb, "zero", target="page", inject=False)
    lifted = lift_gray(zero.rgb)
    card["geom"] = save_overlay(lifted, out_dir / "geom.png")
    recon = defined_paint(rgb, "zero", palette="wheel")
    labeled = _caption(recon, "reconstruct · wheel:zero")
    card["reconstruct_zero"] = {
        "path": "reconstruct_zero.png",
        "sha256": write_png(labeled, out_dir / "reconstruct_zero.png"),
        "pass": "wheel",
        "label": "reconstruct",
        "mode": "zero",
        "inject": False,
    }
    ring_files = []
    for mode in [*RING, CENTER, "balance"]:
        if mode not in WHEEL_LAW:
            continue
        painted = defined_paint(rgb, mode, palette="wheel")
        filename = f"wheel_{mode}.png"
        digest = write_png(painted, out_dir / filename)
        ring_files.append({"mode": mode, "path": filename, "sha256": digest, "pass": "wheel"})
    card["ring"] = ring_files
    gallery = save_gallery(rgb, out_dir / "gallery.png")
    card["gallery"] = gallery["path"]
    card["refuse"] = None
    if with_grid:
        process(
            rgb,
            src=src,
            out_dir=out_dir / "grid",
            modes=list(GRID),
            target=target,
            inject=inject,
            paint="wheel",
            indices=indices,
            sha256_in=sha256_in,
        )
        card["grid"] = "grid/amoe.json"
    write_card(card, out_dir / "adapt.json")
    return card
