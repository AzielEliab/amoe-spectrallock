"""AMOE-1.2 locks: empty hue, reconstruct gate, path refuse, wheel ≠ engine UV, no amoe.png."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from amoe import AmoeError, ensure_vendor
from amoe.adapt import adapt, page_condition, reconstruct
from amoe.geom import overlay
from amoe.paint import engine_paint, wheel_paint
from amoe.path import audit, engine_opaque_refuse
from amoe.wheel import (
    ENGINE_HEX,
    GRID,
    WHEEL_HEX,
    amoe_scalar,
    empty_slots,
    reject_name,
)
from amoe.wrap import process

ROOT = Path(__file__).resolve().parents[1]
ENGINE_SHA256 = "7e6bf472131131bedc75768db1059e83f6e2db0d237cd94b299a3109184d3d8f"
RETIRED_WHEEL = {
    "zero": "#2E5A8C",
    "chaos": "#7A2E5C",
    "uv": "#C45A2A",
    "tazel": "#8A9A2E",
    "rosetta": "#2E7A4A",
    "zen": "#F2EBD8",
}


def _save(path: Path, rgb: np.ndarray) -> None:
    u8 = np.clip(np.round(np.clip(rgb, 0.0, 1.0) * 255.0), 0, 255).astype(np.uint8)
    Image.fromarray(u8, "RGB").save(path)


def _gray(value: float = 0.45, size: int = 24) -> np.ndarray:
    return np.full((size, size, 3), value, dtype=np.float32)


def _present() -> np.ndarray:
    img = np.zeros((32, 32, 3), dtype=np.float32)
    img[:, :16] = 1.0
    return img


def _faint() -> np.ndarray:
    shape = (40, 40)
    mid = 131 / 255.0
    img = np.full((*shape, 3), mid, dtype=np.float32)
    flat = img.reshape(-1, 3)
    n_tail = int(round(flat.shape[0] * 0.15))
    flat[:n_tail] = 80 / 255.0
    flat[-n_tail:] = 182 / 255.0
    return img


def test_vendor_is_spectrallock_031_unmodified():
    engine = ROOT / "vendor" / "spectrallock" / "engine.py"
    digest = hashlib.sha256(engine.read_bytes()).hexdigest()
    assert digest == ENGINE_SHA256
    ensure_vendor()
    import spectrallock
    from spectrallock.engine import (
        ZERO_HEX,
        TAZEL_HEX,
        VYRN_HEX,
        OverlayResult,
        analyze,
        apply_target,
        inband_pct,
    )

    assert spectrallock.__version__ == "0.3.1"
    assert spectrallock.__author__ == "Aziel Eliab"
    assert TAZEL_HEX == "#1EC9A5"
    assert VYRN_HEX == "#C00066"
    assert ZERO_HEX == "#6F6485"
    assert callable(analyze) and callable(apply_target) and callable(inband_pct)
    assert OverlayResult is not None


def test_wheel_uv_is_not_engine_uv_or_retired_gallery():
    assert WHEEL_HEX["uv"].upper() == "#9F3B2B"
    assert ENGINE_HEX["uv"].upper() == "#8C73D9"
    assert WHEEL_HEX["uv"].upper() != ENGINE_HEX["uv"].upper()
    assert WHEEL_HEX == {
        "zero": "#325767",
        "chaos": "#8D223D",
        "vyrn": "#A22639",
        "uv": "#9F3B2B",
        "tazel": "#797A2D",
        "rosetta": "#467542",
        "zen": "#DFD2B5",
    }
    for name, retired in RETIRED_WHEEL.items():
        assert WHEEL_HEX[name].upper() != retired.upper()
    dark = np.full((12, 12, 3), 0.05, dtype=np.float32)
    wheel = wheel_paint(dark, "uv")
    engine = engine_paint(dark, "uv")
    assert wheel[..., 0].mean() > wheel[..., 2].mean()
    assert engine[..., 2].mean() > engine[..., 0].mean()


def test_no_twelfth_color_and_no_rosetta_alias():
    assert "amoe" not in GRID
    assert len(GRID) == 11
    assert reject_name("amoe") == "amoe_as_color"
    assert reject_name("AMOE") == "amoe_as_color"
    assert reject_name("rosetta") is None
    assert reject_name("invent_letter") == "invent_letter"
    assert reject_name("invent_mark") == "invent_mark"


def test_empty_hue_is_a_reading_and_writes_no_amoe_png(tmp_path: Path):
    card = process(
        _gray(),
        src="gray.png",
        out_dir=tmp_path,
        modes=["tazel"],
        target="ink",
        inject=False,
        paint="engine",
    )
    assert card["refuse"] == "AMOE-EMPTY-HUE"
    assert card["amoe_is_field"] is False
    assert card["amoe_is_wiring"] is True
    assert card["invent_letters"] is False
    assert card["pigment_recovery"] is False
    assert card["author"] == "Aziel Eliab"
    assert card["cells"]["tazel"]["inband"]["tazel_inband_pct"] == 0
    assert card["cells"]["tazel"]["inband"]["vyrn_inband_pct"] == 0
    assert card["cells"]["tazel"]["custodian"] == "MMI"
    names = {path.name.lower() for path in tmp_path.rglob("*")}
    assert "amoe.png" not in names
    assert "amoe_field.png" not in names
    assert (tmp_path / "amoe.json").is_file()
    with pytest.raises(AmoeError) as raised:
        process(_gray(), src="x", out_dir=tmp_path / "bad", modes=["amoe"])
    assert raised.value.code == "amoe_as_color"
    assert not (tmp_path / "bad" / "amoe.png").exists()


def test_reconstruct_gate(tmp_path: Path):
    missing = reconstruct(None)
    assert missing["refuse"] == "AMOE-RECONSTRUCT-USE-ADAPT"
    assert missing["reconstruct"] is False

    near = page_condition(_gray())
    assert near["state"] == "near_gone"
    assert near["reconstruct_ok"] is True

    faint = page_condition(_faint())
    assert faint["state"] == "faint"
    assert faint["reconstruct_ok"] is True

    present = page_condition(_present())
    assert present["state"] == "present"
    assert present["reconstruct_ok"] is False

    held = adapt(_present(), src="present.png", out_dir=tmp_path / "present")
    assert held["refuse"] == "AMOE-RECONSTRUCT-NOT-NEEDED"
    assert held["reconstruct"] is False
    assert not (tmp_path / "present" / "reconstruct_zero.png").exists()
    assert (tmp_path / "present" / "geom.png").is_file()

    built = adapt(_gray(size=28), src="flat.png", out_dir=tmp_path / "flat")
    assert built["refuse"] is None
    assert built["reconstruct"] is True
    assert built["route"] == "ZERO geom"
    assert (tmp_path / "flat" / "reconstruct_zero.png").is_file()
    assert (tmp_path / "flat" / "gallery.png").is_file()
    assert (tmp_path / "flat" / "wheel_zero.png").is_file()
    assert (tmp_path / "flat" / "wheel_zen.png").is_file()
    assert "amoe.png" not in {p.name for p in (tmp_path / "flat").rglob("*.png")}
    assert built["pigment_recovery"] is False


def test_path_refuses_without_reading_pixels():
    assert audit({"steps": []})["refuse"] == "AMOE-NO-FIGURE"
    assert audit({})["refuse"] == "AMOE-NO-FIGURE"
    assert audit({"steps": [0]})["refuse"] == "AMOE-BAD-STEP:0"
    assert audit({"steps": [14]})["refuse"] == "AMOE-BAD-STEP:14"
    assert audit({"steps": ["bird"]})["refuse"] == "AMOE-BAD-STEP:bird"
    mis = audit({"steps": [1, 12], "gate": "open", "vector": "east"})
    assert mis["refuse"] == "AMOE-GATE-MISALIGN"
    assert mis["figures_from_pixels"] is False
    ok = audit(
        {
            "steps": [1, 12, 13],
            "vector": "north",
            "lens": "zero",
            "conflict": "twin pillars",
            "gate": "post-gate",
        }
    )
    assert ok["ok"] is True
    assert ok["refuse"] is None
    assert ok["step_names"][0] == "Apertio (Opening)"
    assert engine_opaque_refuse() == "SL-UNREDACT-OPAQUE"


def test_scalar_clips_and_slots_default_zero():
    means = {mode: 0.0 for mode in GRID}
    means.update(zero=1, tazel=1, vyrn=1, uv=1, zen=1, chaos=1)
    assert amoe_scalar(means, empty_slots()) == pytest.approx(4 / 12)
    slots = empty_slots()
    slots["RS"] = 1
    assert amoe_scalar(means, slots) == pytest.approx(5 / 12)
    sunk = {mode: 0.0 for mode in GRID}
    sunk["chaos"] = 1
    assert amoe_scalar(sunk, empty_slots()) == 0.0


def test_geom_does_not_invent_a_staff_on_a_blank_page():
    flat = _gray(0.8, 32)
    out, meta = overlay(flat)
    assert meta["drawn"] is False
    assert meta["invent_figures"] is False
    assert np.allclose(out, flat)

    framed = np.full((64, 64, 3), 0.92, dtype=np.float32)
    framed[8:56, 8:11] = 0.08
    framed[8:56, 53:56] = 0.08
    framed[8:11, 8:56] = 0.08
    framed[53:56, 8:56] = 0.08
    drawn, info = overlay(framed)
    assert info["drawn"] is True
    assert info["invent_figures"] is False
    color = np.array([0x6E / 255.0, 0xA0 / 255.0, 0xD2 / 255.0], dtype=np.float32)
    distance = np.abs(drawn - color).sum(axis=-1)
    assert np.any(distance < 0.05)


def test_amoe_modules_do_not_reimplement_engine_or_pigment():
    for path in (ROOT / "amoe").glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "def analyze(" not in text
        assert "def apply_target(" not in text
        assert "def inband_pct(" not in text
        assert "def analyze_pigment" not in text


def test_catalog_and_readme_state_the_locks():
    catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
    assert catalog["slug"] == "amoe"
    assert catalog["amoe_is_field"] is False
    assert catalog["amoe_is_wiring"] is True
    assert catalog["depends"] == "spectrallock@0.3.1"
    assert catalog["pigment_recovery"] is False
    assert catalog["invent_letters"] is False
    assert catalog["author"] == "Aziel Eliab"
    assert "amoe" not in catalog["grid"]
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "not a field" in readme.lower() or "not a field" in readme
    assert "wiring" in readme.lower()
    assert "SpectralLock" in readme
    assert "pigment" in readme.lower()
    assert "#9F3B2B" in readme
    assert "#8C73D9" in readme
    assert "#1EC9A5" in readme
    assert "Aziel Eliab" in readme
    assert "human still reads the page" in readme.lower()
    assert "#2E5A8C" not in readme


def test_cli_help_catalog_and_path(tmp_path: Path):
    help_run = subprocess.run(
        [sys.executable, str(ROOT / "run.py"), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert help_run.returncode == 0
    for name in (
        "overlay",
        "grid",
        "paint",
        "gallery",
        "lift",
        "geom",
        "adapt",
        "reconstruct",
        "path",
        "catalog",
        "custodian",
    ):
        assert name in help_run.stdout

    catalog = subprocess.run(
        [sys.executable, str(ROOT / "run.py"), "catalog"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert catalog.returncode == 0
    body = json.loads(catalog.stdout)
    assert body["amoe_is_wiring"] is True
    assert body["depends"] == "spectrallock@0.3.1"

    card = tmp_path / "steps.json"
    card.write_text(json.dumps({"steps": []}), encoding="utf-8")
    refused = subprocess.run(
        [sys.executable, str(ROOT / "run.py"), "path", "--card", str(card)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert refused.returncode == 2
    assert json.loads(refused.stdout)["refuse"] == "AMOE-NO-FIGURE"

    bare = subprocess.run(
        [sys.executable, str(ROOT / "run.py"), "reconstruct", "--out", str(tmp_path / "recon")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert bare.returncode == 2
    assert json.loads(bare.stdout)["refuse"] == "AMOE-RECONSTRUCT-USE-ADAPT"

    page = tmp_path / "blank.png"
    _save(page, _gray())
    overlay = subprocess.run(
        [
            sys.executable,
            str(ROOT / "run.py"),
            "overlay",
            str(page),
            "--mode",
            "amoe",
            "--out",
            str(tmp_path / "overlay"),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert overlay.returncode == 2
    assert json.loads(overlay.stdout)["refuse"] == "amoe_as_color"
    assert not (tmp_path / "overlay" / "amoe.png").exists()
