"""Interpreter path 1–13. Card audit only.

Does not detect figures from pixels. Axes are vector, lens, conflict, gate.

Author: Aziel Eliab.
"""

from __future__ import annotations

from amoe import ensure_vendor
from amoe.wheel import (
    AUTHOR,
    GATE_OK,
    PAPER,
    PATH_AXES,
    PATH_STEPS,
    PRODUCT,
    REFUSE_BAD_STEP,
    REFUSE_GATE_MISALIGN,
    REFUSE_NO_FIGURE,
    VERSION,
)


def _step_token(item: object) -> object:
    if isinstance(item, dict):
        if "n" in item:
            return item["n"]
        if "step" in item:
            return item["step"]
    return item


def _as_step(token: object) -> int | None:
    if isinstance(token, bool):
        return None
    if isinstance(token, int):
        return token
    if isinstance(token, float) and token.is_integer():
        return int(token)
    text = str(token).strip()
    if text.isdigit() or (text.startswith("-") and text[1:].isdigit()):
        return int(text)
    return None


def engine_opaque_refuse() -> str:
    """Cite the SpectralLock engine code. AMOE does not reimplement unredact."""
    ensure_vendor()
    from spectrallock.unredact import REFUSE_OPAQUE

    return str(REFUSE_OPAQUE)


def audit(card: dict | None) -> dict:
    """Audit a path card. Refuses are named. No pixel figure finding."""
    body = card or {}
    raw = body.get("steps")
    tokens = [] if raw is None else list(raw)
    steps: list[int] = []
    refuses: list[str] = []
    if not tokens:
        refuses.append(REFUSE_NO_FIGURE)
    else:
        for item in tokens:
            token = _step_token(item)
            number = _as_step(token)
            if number is None or number not in PATH_STEPS:
                label = token if token is not None else item
                refuses.append(f"{REFUSE_BAD_STEP}:{label}")
                continue
            steps.append(number)
        gate = str(body.get("gate") or "").strip().lower()
        if 12 in steps and gate not in GATE_OK:
            refuses.append(REFUSE_GATE_MISALIGN)

    axes = {name: body.get(name) for name in PATH_AXES}
    return {
        "product": PRODUCT,
        "version": VERSION,
        "paper": "AMOE-PATH-1.0",
        "author": AUTHOR,
        "amoe_is_field": False,
        "amoe_is_wiring": True,
        "ok": not refuses,
        "refuse": refuses[0] if refuses else None,
        "refuses": refuses,
        "steps": steps,
        "step_names": [PATH_STEPS[n] for n in steps],
        "axes": axes,
        "invent_letters": False,
        "pigment_recovery": False,
        "figures_from_pixels": False,
        "parent_paper": PAPER,
    }
