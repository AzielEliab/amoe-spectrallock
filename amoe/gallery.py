"""3×3 gallery sheet. Wheel pass only, each tile labeled.

Layout: source zero chaos / vyrn uv tazel / rosetta zen blend.
Blend is a wheel mix of zen and chaos. It is not a color named AMOE
and it is not Rosetta.

Author: Aziel Eliab.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from amoe import ensure_vendor
from amoe.paint import defined_paint, write_png
from amoe.wheel import AUTHOR, PAINT_LAW, VERSION, WHEEL_HEX, WHEEL_LAW

ensure_vendor()

LAYOUT: tuple[tuple[str, ...], ...] = (
    ("source", "zero", "chaos"),
    ("vyrn", "uv", "tazel"),
    ("rosetta", "zen", "blend"),
)


def _fit(rgb: np.ndarray, size: int) -> np.ndarray:
    u8 = np.clip(np.round(np.clip(rgb, 0.0, 1.0) * 255.0), 0, 255).astype(np.uint8)
    image = Image.fromarray(u8, "RGB")
    image.thumbnail((size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (size, size), (236, 230, 218))
    left = (size - image.width) // 2
    top = (size - image.height) // 2
    canvas.paste(image, (left, top))
    return np.asarray(canvas, dtype=np.float32) / 255.0


def _tile(rgb: np.ndarray, label: str) -> np.ndarray:
    fitted = _fit(rgb, 220)
    u8 = np.clip(np.round(fitted * 255.0), 0, 255).astype(np.uint8)
    image = Image.fromarray(u8, "RGB")
    bar = 22
    sheet = Image.new("RGB", (image.width, image.height + bar), (28, 26, 24))
    sheet.paste(image, (0, bar))
    draw = ImageDraw.Draw(sheet)
    draw.text((6, 4), label, fill=(223, 210, 181))
    return np.asarray(sheet, dtype=np.float32) / 255.0


def build_gallery(rgb: np.ndarray) -> tuple[np.ndarray, list[str]]:
    """Contact sheet. Source is the page. Other tiles are the 1.3 wheel law."""
    cells: dict[str, np.ndarray] = {"source": rgb}
    labels: list[str] = []
    for row in LAYOUT:
        for name in row:
            if name == "source":
                continue
            if name == "blend":
                cells[name] = defined_paint(rgb, "balance", palette="wheel")
            else:
                cells[name] = defined_paint(rgb, name, palette="wheel")
    tiles = []
    for row in LAYOUT:
        for name in row:
            if name == "source":
                label = "source"
            elif name == "blend":
                label = "blend · bsa"
            elif name == "rosetta":
                label = "rosetta · pixel-scope"
            elif name == "zen":
                label = "zen · invert"
            else:
                label = f"{name} · wheel"
            labels.append(label)
            tiles.append(_tile(cells[name], label))
    sample = tiles[0]
    th, tw = sample.shape[:2]
    gap = 8
    header = 28
    rows = len(LAYOUT)
    cols = len(LAYOUT[0])
    height = header + rows * th + (rows + 1) * gap
    width = cols * tw + (cols + 1) * gap
    canvas = Image.new("RGB", (width, height), (18, 17, 16))
    draw = ImageDraw.Draw(canvas)
    draw.text((gap, 6), "AMOE-1.3 gallery · wheel law", fill=(223, 210, 181))
    for index, tile in enumerate(tiles):
        y, x = divmod(index, cols)
        left = gap + x * (tw + gap)
        top = header + gap + y * (th + gap)
        u8 = np.clip(np.round(tile * 255.0), 0, 255).astype(np.uint8)
        canvas.paste(Image.fromarray(u8, "RGB"), (left, top))
    out = np.asarray(canvas, dtype=np.float32) / 255.0
    return out, labels


def save_gallery(rgb: np.ndarray, path: Path) -> dict:
    image, labels = build_gallery(rgb)
    digest = write_png(image, path)
    return {
        "product": "amoe",
        "version": VERSION,
        "author": AUTHOR,
        "path": path.name,
        "sha256": digest,
        "pass": "wheel",
        "layout": [list(row) for row in LAYOUT],
        "labels": labels,
        "amoe_is_field": False,
        "amoe_is_wiring": True,
        "pigment_recovery": False,
        "invent_letters": False,
        "wheel_hex": dict(WHEEL_HEX),
        "wheel_law": dict(WHEEL_LAW),
        "paint_law": PAINT_LAW,
    }
