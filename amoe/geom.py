"""ZERO-process geometry overlay. Lines from edges, not a figure detector.

FIND_EDGES → content box → axis from vertical edge energy → nested frame,
axis mundi, mid horizontal, both diagonals, mid circle, lower circle.
invent_figures stays false. A hidden staff is not drawn when edges do not
support it.

Author: Aziel Eliab.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from amoe.paint import write_png
from amoe.wheel import GEOM_COLOR, hex_to_rgb


def _as_uint8(rgb: np.ndarray) -> np.ndarray:
    arr = np.nan_to_num(np.asarray(rgb, dtype=np.float32), nan=0.0, posinf=1.0, neginf=0.0)
    arr = np.clip(arr, 0.0, 1.0)
    return np.clip(np.round(arr * 255.0), 0, 255).astype(np.uint8)


def _vertical_energy(gray: Image.Image) -> np.ndarray:
    kernel = ImageFilter.Kernel(
        size=(3, 3),
        kernel=[-1, 0, 1, -2, 0, 2, -1, 0, 1],
        scale=1,
        offset=128,
    )
    response = np.asarray(gray.filter(kernel), dtype=np.float32)
    return np.abs(response - 128.0)


def overlay(rgb: np.ndarray, *, color: str = GEOM_COLOR) -> tuple[np.ndarray, dict]:
    """Draw the ZERO frame when edges support it. Otherwise return the page unchanged."""
    u8 = _as_uint8(rgb)
    image = Image.fromarray(u8, "RGB")
    edges = np.asarray(image.filter(ImageFilter.FIND_EDGES).convert("L"), dtype=np.float32)
    mask = edges >= 16.0
    meta: dict = {
        "invent_figures": False,
        "color": color,
        "drawn": False,
        "reason": "edges do not support a staff",
    }
    ys, xs = np.nonzero(mask)
    if ys.size < 8:
        return np.asarray(image, dtype=np.float32) / 255.0, meta

    y0 = int(ys.min())
    y1 = int(ys.max())
    x0 = int(xs.min())
    x1 = int(xs.max())
    if (x1 - x0) < 8 or (y1 - y0) < 8:
        return np.asarray(image, dtype=np.float32) / 255.0, meta

    energy = _vertical_energy(image.convert("L"))
    sub = energy[y0 : y1 + 1, x0 : x1 + 1]
    total = float(sub.sum())
    if total <= 1e-6:
        axis_x = (x0 + x1) / 2.0
    else:
        cols = np.arange(sub.shape[1], dtype=np.float64)
        axis_x = float(x0 + (sub.sum(axis=0) * cols).sum() / total)
    mid_y = (y0 + y1) / 2.0
    lower_y = y0 + 0.78 * (y1 - y0)
    span = float(min(x1 - x0, y1 - y0))
    radius = max(4.0, span * 0.18)
    lower_radius = max(3.0, radius * 0.72)

    canvas = image.copy()
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([x0, y0, x1, y1], outline=color, width=2)
    inset = max(4, int(round(span * 0.12)))
    if (x1 - x0) > inset * 2 + 4 and (y1 - y0) > inset * 2 + 4:
        draw.rectangle(
            [x0 + inset, y0 + inset, x1 - inset, y1 - inset],
            outline=color,
            width=1,
        )
    draw.line([(axis_x, y0), (axis_x, y1)], fill=color, width=2)
    draw.line([(x0, mid_y), (x1, mid_y)], fill=color, width=2)
    draw.line([(x0, y0), (x1, y1)], fill=color, width=2)
    draw.line([(x0, y1), (x1, y0)], fill=color, width=2)
    draw.ellipse(
        [axis_x - radius, mid_y - radius, axis_x + radius, mid_y + radius],
        outline=color,
        width=2,
    )
    draw.ellipse(
        [
            axis_x - lower_radius,
            lower_y - lower_radius,
            axis_x + lower_radius,
            lower_y + lower_radius,
        ],
        outline=color,
        width=2,
    )
    meta.update(
        {
            "drawn": True,
            "reason": "edges support the frame",
            "box": [x0, y0, x1, y1],
            "axis_x": axis_x,
            "mid_y": mid_y,
            "lower_y": lower_y,
            "color_rgb": list(hex_to_rgb(color)),
        }
    )
    return np.asarray(canvas, dtype=np.float32) / 255.0, meta


def save_overlay(rgb: np.ndarray, path: Path, *, color: str = GEOM_COLOR) -> dict:
    painted, meta = overlay(rgb, color=color)
    digest = write_png(painted, path)
    meta["path"] = path.name
    meta["sha256"] = digest
    meta["pigment_recovery"] = False
    meta["invent_letters"] = False
    return meta
