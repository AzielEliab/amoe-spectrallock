"""Spectral Harmonic Wheel, engine lens card, custodians, and path names.

Gallery paint uses WHEEL_HEX. Inject/membership uses ENGINE_HEX.
Do not swap the tables. Rosetta paint is a pixel-scope map, not a hex
sheet. Zen paint is the invert of that map. The engine notes for those
two lenses are membership colors only.

Author: Aziel Eliab.
"""

from __future__ import annotations

AUTHOR = "Aziel Eliab"
VERSION = "1.3.0"
PAPER = "AMOE-1.3"
PRODUCT = "amoe"
PAINT_LAW = (
    "Pull what is faded. Color it with the wheel that was defined. "
    "Rosetta maps every pixel onto that wheel. Zen inverts that map. "
    "AMOE rides every lens. Do not make the pattern. Draw the pattern out."
)

# Eleven lenses. Never add a twelfth named AMOE. Never alias AMOE to Rosetta.
GRID: tuple[str, ...] = (
    "zero",
    "tazel",
    "vyrn",
    "uv",
    "rosetta",
    "zen",
    "chaos",
    "balance",
    "candle",
    "indent",
    "lemon",
)

# Live means that enter the page scalar. Chaos is subtracted.
SCALAR_MODES: tuple[str, ...] = ("zero", "tazel", "vyrn", "uv", "zen", "chaos")

# Center ZEN. Clockwise from top: ZERO → CHAOS → VYRN → UV → TAZEL → ROSETTA → ZERO.
RING: tuple[str, ...] = ("zero", "chaos", "vyrn", "uv", "tazel", "rosetta")
CENTER = "zen"

# Engine / densitometry card. Rosetta and Zen hexes are membership notes.
# SpectralLock analyze() still blends those lenses inside the vendored engine.
ENGINE_HEX: dict[str, str] = {
    "zero": "#6F6485",
    "tazel": "#1EC9A5",
    "vyrn": "#C00066",
    "uv": "#8C73D9",
    "chaos": "#8C3861",
    "rosetta": "#6B8A8A",
    "zen": "#C9C4B8",
    "balance": "#8A8680",
    "candle": "#FF9E38",
    "indent": "#B8AD94",
    "lemon": "#9E6124",
}

ENGINE_HUE: dict[str, float] = {
    "zero": 260.0,
    "tazel": 170.0,
    "vyrn": 350.0,
}

ENGINE_BLEND: dict[str, str] = {
    "rosetta": "0.40·Z + 0.35·T + 0.25·V",
    "zen": "(Z + T + UV + V) / 4",
    "chaos_mix": "0.40·UV + 0.35·V + 0.20·T + 0.05·Z",
}

ENGINE_NOTE: dict[str, str] = {
    "rosetta": "membership #6B8A8A; paint is the pixel-scope map, not this hex",
    "zen": "membership #C9C4B8; paint is clip(1 - Rosetta_pixel_map), not a cream sheet",
}

# Operator plate. Single-hex sheets only. Rosetta and Zen are laws, not swatches.
WHEEL_HEX: dict[str, str] = {
    "zero": "#2E5A8C",
    "chaos": "#7A2E5C",
    "vyrn": "#C00066",
    "uv": "#C45A2A",
    "tazel": "#8A9A2E",
}

# Clockwise ring used by the Rosetta pixel map. Includes Rosetta green as one bin.
RING_CW_FROM_ZERO: dict[str, str] = {
    "zero": "#2E5A8C",
    "chaos": "#7A2E5C",
    "vyrn": "#C00066",
    "uv": "#C45A2A",
    "tazel": "#8A9A2E",
    "rosetta": "#2E7A4A",
}

WHEEL_LAW: dict[str, str] = {
    "zero": "single-hex",
    "chaos": "single-hex",
    "vyrn": "single-hex",
    "uv": "single-hex",
    "tazel": "single-hex",
    "rosetta": "pixel-scope",
    "zen": "invert",
    "balance": "bsa-mix",
}

PAPERS: dict[str, str] = {
    "zero": "ZSA-1.0",
    "tazel": "TSA-1.0",
    "vyrn": "VSA-1.0",
    "uv": "UVSA-1.0",
    "rosetta": "RSA-2.0",
    "zen": "ZENA-1.0",
    "chaos": "CSA-1.0",
    "balance": "BSA",
    "candle": "CLSA-1.0",
    "indent": "ISA-1.0",
    "lemon": "LISA-1.0",
}

ROLES: dict[str, str] = {
    "zero": "structure / integrator",
    "tazel": "revelation / maker",
    "vyrn": "pressure / guardian",
    "uv": "synthetic UV look",
    "rosetta": "full-scope pixel map",
    "zen": "invert of the rosetta pixel plate",
    "chaos": "single hex sheet",
    "balance": "reweight only",
    "candle": "warm flame-side",
    "indent": "relief heuristic",
    "lemon": "browning already present",
}

# SLOT indices default 0. Do not fabricate values.
SLOT: tuple[str, ...] = ("RS", "AA", "DR", "VC", "HL", "RSA")

CUSTODIAN: dict[str, dict[str, object]] = {
    "MMI": {
        "role": "Maker",
        "lens": "tazel",
        "hue": "green/gold",
        "plates": [
            "Child",
            "Chalice/Offering",
            "Serpent/Builder",
            "Foundation Stones",
        ],
    },
    "WLW": {
        "role": "Guardian",
        "lens": "vyrn",
        "hue": "magenta/crimson",
        "plates": [
            "Wheel of Fortune",
            "Lion-Handler",
            "Red-Robe Distracted Man",
            "Snake-Handler",
        ],
    },
    "AZI": {
        "role": "Integrator",
        "lens": "zero",
        "hue": "blue/violet",
        "plates": [
            "Angel Crowning Pope",
            "Angel Giving Keys",
            "Papal Illumination/Enthronement",
            "Teacher/Scroll/Insight",
        ],
    },
}

LENS_CUSTODIAN: dict[str, str] = {
    "tazel": "MMI",
    "vyrn": "WLW",
    "zero": "AZI",
}

# Not on the three-custodian list. Route through adapt → ZERO geom, not Tazel.
WATERFALL: dict[str, object] = {
    "name": "Waterfall Guardian Plate",
    "plates": "A–G / Zero-night",
    "on_three_custodian_list": False,
    "route": "adapt → ZERO geom",
    "not_lens": "tazel",
}

PATH_STEPS: dict[int, str] = {
    1: "Apertio (Opening)",
    2: "Herald selection",
    3: "First Sight",
    4: "Rider (motion)",
    5: "First Message",
    6: "First Division (Two Birds)",
    7: "Choosing the Correct Bird",
    8: "Warning (Distracted Man)",
    9: "Inner Engagement",
    10: "First Re-alignment",
    11: "First True Conflict",
    12: "First Gate (Twin Pillars)",
    13: "First Breath / Purpose",
}

PATH_AXES: tuple[str, ...] = ("vector", "lens", "conflict", "gate")
GATE_OK: frozenset[str] = frozenset({"gate", "post-gate"})

GEOM_COLOR = "#6EA0D2"

REFUSE_EMPTY_HUE = "AMOE-EMPTY-HUE"
REFUSE_WEAK_SIGNAL = "AMOE-WEAK-SIGNAL"
SCALAR_NOTE = (
    "ZE and CH already mix core channels; the /12 double-counts. "
    "The paper is followed and the double-count is recorded."
)
REFUSE_NO_FIGURE = "AMOE-NO-FIGURE"
REFUSE_BAD_STEP = "AMOE-BAD-STEP"
REFUSE_GATE_MISALIGN = "AMOE-GATE-MISALIGN"
REFUSE_RECONSTRUCT_NOT_NEEDED = "AMOE-RECONSTRUCT-NOT-NEEDED"
REFUSE_RECONSTRUCT_USE_ADAPT = "AMOE-RECONSTRUCT-USE-ADAPT"
REFUSE_AMOE_AS_COLOR = "amoe_as_color"
REFUSE_INVENT_MARK = "invent_mark"
REFUSE_INVENT_LETTER = "invent_letter"

FORBIDDEN_PRODUCTS: frozenset[str] = frozenset(
    {"amoe.png", "amoe_field.png", "amoe.jpg", "amoe.jpeg"}
)


def hex_to_rgb(code: str) -> tuple[float, float, float]:
    h = str(code).strip().lstrip("#")
    return (
        int(h[0:2], 16) / 255.0,
        int(h[2:4], 16) / 255.0,
        int(h[4:6], 16) / 255.0,
    )


def engine_rgb(mode: str) -> tuple[float, float, float]:
    """Membership hex. Rosetta and Zen are the 1.3 notes, not the analyze blends."""
    key = str(mode).strip().lower()
    if key not in ENGINE_HEX:
        raise KeyError(key)
    return hex_to_rgb(ENGINE_HEX[key])


def wheel_rgb(mode: str) -> tuple[float, float, float]:
    key = str(mode).strip().lower()
    if key not in WHEEL_HEX:
        raise KeyError(key)
    return hex_to_rgb(WHEEL_HEX[key])


def empty_slots() -> dict[str, float]:
    return {key: 0.0 for key in SLOT}


def amoe_scalar(means: dict[str, float], slots: dict[str, float] | None = None) -> float:
    """Page scalar. Wiring on the cells, not a painted field.

    clip( (Z0 + TZ + VY + UV + ZE - CH + RS+AA+DR+VC+HL+RSA) / 12 , 0, 1)
    """
    held = empty_slots()
    if slots:
        for key, value in slots.items():
            name = str(key).strip().upper()
            if name not in held:
                raise KeyError(name)
            held[name] = float(value)
    raw = (
        float(means["zero"])
        + float(means["tazel"])
        + float(means["vyrn"])
        + float(means["uv"])
        + float(means["zen"])
        - float(means["chaos"])
        + sum(held[key] for key in SLOT)
    ) / 12.0
    if raw < 0.0:
        return 0.0
    if raw > 1.0:
        return 1.0
    return float(raw)


def reject_name(name: str) -> str | None:
    """Refuse a twelfth color, an AMOE→Rosetta alias, or an invent request.

    Returns a refuse code, or None when the name may proceed to SpectralLock.
    """
    key = str(name or "").strip().lower()
    if key in {"amoe", "amoe.png", "amoe_field", "amoe-field"}:
        return REFUSE_AMOE_AS_COLOR
    if key in {"invent_letter", "invent_letters"}:
        return REFUSE_INVENT_LETTER
    if key in {"invent_mark", "invent", "invent_marks"}:
        return REFUSE_INVENT_MARK
    return None
