"""AMOE-1.3 paint law: pixel-scope Rosetta, Zen invert, defined hex sheets."""

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
from amoe.paint import (
    _pull_faint,
    _rosetta_fusion,
    _scope_from_pixels,
    _zen_balance,
    defined_paint,
    signal_means,
    weak_signal,
)
from amoe.path import audit, engine_opaque_refuse
from amoe.wheel import (
    ENGINE_HEX,
    GRID,
    PAINT_LAW,
    RING_CW_FROM_ZERO,
    WHEEL_HEX,
    amoe_scalar,
    empty_slots,
    hex_to_rgb,
    reject_name,
)
from amoe.wrap import process

ROOT = Path(__file__).resolve().parents[1]
ENGINE_SHA256 = "7e6bf472131131bedc75768db1059e83f6e2db0d237cd94b299a3109184d3d8f"
RETIRED_12 = {
    "zero": "#325767",
    "chaos": "#8D223D",
    "uv": "#9F3B2B",
    "tazel": "#797A2D",
    "rosetta": "#467542",
    "zen": "#DFD2B5",
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


def _folio() -> np.ndarray:
    """Boxed leaf with a column wash, a seal, and a yellow robe."""
    img = np.full((80, 80, 3), 0.78, dtype=np.float32)
    img[6:74, 6:10] = 0.12
    img[6:74, 70:74] = 0.12
    img[6:10, 6:74] = 0.12
    img[70:74, 6:74] = 0.12
    img[12:68, 18:28] = 0.62
    yy, xx = np.ogrid[:80, :80]
    seal = (yy - 40) ** 2 + (xx - 48) ** 2 < 12 ** 2
    img[seal] = 0.55
    img[20:48, 40:58] = (0.95, 0.82, 0.15)
    return img


def _ramp() -> np.ndarray:
    column = np.linspace(0.0, 1.0, 120, dtype=np.float32).reshape(120, 1, 1)
    return np.repeat(np.repeat(column, 36, axis=1), 3, axis=2)


def _luma(rgb: np.ndarray) -> np.ndarray:
    return 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]


def _chroma(rgb: np.ndarray) -> np.ndarray:
    return rgb - _luma(rgb)[..., None]


def _align(mean: np.ndarray, code: str) -> float:
    target = np.asarray(hex_to_rgb(code), dtype=np.float64)
    a = _chroma(mean)
    b = _chroma(target)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


def test_vendor_is_spectrallock_031_unmodified():
    engine = ROOT / "vendor" / "spectrallock" / "engine.py"
    digest = hashlib.sha256(engine.read_bytes()).hexdigest()
    assert digest == ENGINE_SHA256
    pin = (ROOT / "vendor" / "SPECTRALLOCK_0.3.1.pin").read_text(encoding="utf-8")
    assert "0.3.1" in pin
    assert "92fcc3b" in pin
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


def test_wheel_tables_match_the_13_plate():
    assert WHEEL_HEX == {
        "zero": "#2E5A8C",
        "chaos": "#7A2E5C",
        "vyrn": "#C00066",
        "uv": "#C45A2A",
        "tazel": "#8A9A2E",
    }
    assert RING_CW_FROM_ZERO["rosetta"] == "#2E7A4A"
    assert ENGINE_HEX["zero"] == "#6F6485"
    assert ENGINE_HEX["uv"] == "#8C73D9"
    assert ENGINE_HEX["rosetta"] == "#6B8A8A"
    assert ENGINE_HEX["zen"] == "#C9C4B8"
    assert ENGINE_HEX["vyrn"] == WHEEL_HEX["vyrn"]
    assert WHEEL_HEX["uv"] != ENGINE_HEX["uv"]
    for name, retired in RETIRED_12.items():
        if name in WHEEL_HEX:
            assert WHEEL_HEX[name] != retired
    folio = _folio()
    wheel = defined_paint(folio, "uv", palette="wheel")
    engine = defined_paint(folio, "uv", palette="engine")
    assert _align(wheel[30:38, 60:68].mean(axis=(0, 1)), "#C45A2A") > 0.9
    assert _align(engine[30:38, 60:68].mean(axis=(0, 1)), "#8C73D9") > 0.9


def test_zero_sheet_reads_blue_and_empty_paper_stays_empty():
    folio = _folio()
    zero = defined_paint(folio, "zero")
    paper = zero[30:38, 60:68].mean(axis=(0, 1))
    assert _align(paper, "#2E5A8C") > 0.9
    assert float(np.linalg.norm(_chroma(paper))) > 0.08
    assert paper[2] > paper[1] > paper[0]
    flat = defined_paint(_gray(), "zero")
    assert float(np.linalg.norm(_chroma(flat.mean(axis=(0, 1))))) < 0.02


def test_tazel_sheet_and_yellow_robe_stay_yellow():
    folio = _folio()
    out = defined_paint(folio, "tazel")
    paper = out[30:38, 60:68].mean(axis=(0, 1))
    assert _align(paper, "#8A9A2E") > 0.9
    robe = out[20:48, 40:58]
    src = folio[20:48, 40:58]
    assert robe[..., 0].mean() > robe[..., 2].mean() + 0.4
    assert robe[..., 1].mean() > robe[..., 2].mean() + 0.4
    assert float(_luma(robe).mean()) > float(_luma(src).mean())


def test_chaos_vyrn_uv_are_distinct_hex_sheets():
    folio = _folio()
    means = {}
    for mode, code in (("chaos", "#7A2E5C"), ("vyrn", "#C00066"), ("uv", "#C45A2A")):
        paper = defined_paint(folio, mode)[30:38, 60:68].mean(axis=(0, 1))
        assert _align(paper, code) > 0.9
        means[mode] = paper
    pairs = (("chaos", "vyrn"), ("vyrn", "uv"), ("chaos", "uv"))
    for a, b in pairs:
        assert float(np.linalg.norm(means[a] - means[b])) > 0.12


def test_rosetta_is_multi_hue_and_zen_is_its_invert():
    leaf = _ramp()
    rosetta = _rosetta_fusion(leaf)
    zen = _zen_balance(leaf)
    assert np.allclose(zen, 1.0 - rosetta, atol=1e-6)
    assert np.allclose(_scope_from_pixels(leaf, invert=True), 1.0 - rosetta, atol=1e-6)
    assert float(rosetta.std(axis=(0, 1)).mean()) > 0.08
    green = np.asarray(hex_to_rgb("#2E7A4A"))
    assert float(np.linalg.norm(rosetta.mean(axis=(0, 1)) - green)) > 0.25
    other = _rosetta_fusion(1.0 - leaf)
    assert not np.allclose(rosetta, other)
    assert not np.allclose(zen, _zen_balance(1.0 - leaf))
    flat = _rosetta_fusion(_gray())
    assert float(np.linalg.norm(_chroma(flat.mean(axis=(0, 1))))) < 0.02


def test_pull_faint_drops_a_wash_and_does_not_hue_gray_paper():
    wash = np.full((48, 48, 3), 0.82, dtype=np.float32)
    wash[10:40, 8:14] = 0.70
    pulled = _pull_faint(wash)
    gap_in = float(wash[20, 4, 0] - wash[20, 10, 0])
    gap_out = float(pulled[20, 4, 0] - pulled[20, 10, 0])
    assert gap_out >= gap_in - 0.02
    assert pulled[20, 10, 0] < pulled[20, 4, 0]
    flat = _pull_faint(_gray())
    assert float(np.linalg.norm(_chroma(flat.mean(axis=(0, 1))))) < 0.02


def test_paint_source_has_no_ring_generator():
    text = (ROOT / "amoe" / "paint.py").read_text(encoding="utf-8")
    assert "def _rings" not in text
    assert "def _pull_faint" in text
    assert "def _overlay_hex" in text
    assert "def _scope_from_pixels" in text
    assert "def _rosetta_fusion" in text
    assert "def _zen_balance" in text
    assert "amoe.png" not in text.split("FORBIDDEN")[0]


def test_no_twelfth_color_and_no_rosetta_alias():
    assert "amoe" not in GRID
    assert len(GRID) == 11
    assert reject_name("amoe") == "amoe_as_color"
    assert reject_name("AMOE") == "amoe_as_color"
    assert reject_name("rosetta") is None
    assert reject_name("invent_letter") == "invent_letter"
    assert reject_name("invent_mark") == "invent_mark"


def test_weak_signal_is_a_reading_and_writes_no_amoe_png(tmp_path: Path):
    assert weak_signal(signal_means(_gray())) is True
    card = process(
        _gray(),
        src="gray.png",
        out_dir=tmp_path,
        modes=["tazel"],
        target="ink",
        inject=False,
        paint="engine",
    )
    assert card["refuse"] == ["AMOE-WEAK-SIGNAL"]
    assert card["amoe_is_field"] is False
    assert card["amoe_is_wiring"] is True
    assert card["invent_letters"] is False
    assert card["pigment_recovery"] is False
    assert card["letters_recovered"] is False
    assert card["author"] == "Aziel Eliab"
    assert "amoe_scalar" in card
    assert "double-count" in card["scalar_note"]
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
    assert meta["weighting"]["on"] is True
    assert np.allclose(out, flat)

    framed = np.full((64, 64, 3), 0.92, dtype=np.float32)
    framed[8:56, 8:11] = 0.08
    framed[8:56, 53:56] = 0.08
    framed[8:11, 8:56] = 0.08
    framed[53:56, 8:56] = 0.08
    drawn, info = overlay(framed)
    assert info["drawn"] is True
    assert info["invent_figures"] is False
    assert {"ascent", "weight", "equilibrium"} <= set(info["weighting"])
    color = np.array([0x6E / 255.0, 0xA0 / 255.0, 0xD2 / 255.0], dtype=np.float32)
    distance = np.abs(drawn - color).sum(axis=-1)
    assert np.any(distance < 0.05)
    bare, off = overlay(framed, weight=False)
    assert off["weighting"]["on"] is False
    assert bare.shape == framed.shape


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
    assert catalog["version"] == "1.3.0"
    assert catalog["amoe_is_field"] is False
    assert catalog["amoe_is_wiring"] is True
    assert catalog["depends"] == "spectrallock@0.3.1"
    assert catalog["pigment_recovery"] is False
    assert catalog["invent_letters"] is False
    assert catalog["author"] == "Aziel Eliab"
    assert "amoe" not in catalog["grid"]
    assert catalog["wheel_hex"]["zero"] == "#2E5A8C"
    assert catalog["ring_cw_from_zero"]["rosetta"] == "#2E7A4A"
    assert catalog["wheel_law"]["zen"] == "invert"
    assert catalog["paint_law"] == PAINT_LAW
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert PAINT_LAW in readme
    assert "1.3.0" in readme
    assert "not a field" in readme.lower() or "not a field" in readme
    assert "wiring" in readme.lower()
    assert "SpectralLock" in readme
    assert "pigment" in readme.lower()
    assert "0.3.1" in readme
    assert "#2E5A8C" in readme
    assert "#8C73D9" in readme
    assert "#1EC9A5" in readme
    assert "#8A9A2E" in readme
    assert "Aziel Eliab" in readme
    assert "aziel-runtime" in readme
    assert "human still reads the page" in readme.lower()


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
        "lift",
        "gallery",
        "geom",
        "adapt",
        "recover-image",
        "recover-script",
        "script",
        "route",
        "preocr",
        "together",
        "path",
        "catalog",
        "custodian",
    ):
        assert name in help_run.stdout
    assert "--no-geom" in help_run.stdout
    assert "--no-weight" in help_run.stdout

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
    assert body["version"] == "1.3.0"

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
    overlay_amoe = subprocess.run(
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
    assert overlay_amoe.returncode == 2
    assert json.loads(overlay_amoe.stdout)["refuse"] == "amoe_as_color"
    assert not (tmp_path / "overlay" / "amoe.png").exists()


def test_cli_overlay_zero_geom_and_tracks(tmp_path: Path):
    page = tmp_path / "folio.png"
    _save(page, _folio())
    out = tmp_path / "zero"
    run = subprocess.run(
        [
            sys.executable,
            str(ROOT / "run.py"),
            "overlay",
            str(page),
            "--mode",
            "zero",
            "--paint",
            "wheel",
            "--out",
            str(out),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert run.returncode == 0, run.stderr
    card = json.loads(run.stdout)
    assert card["pigment_recovery"] is False
    assert card["geom"]["on"] is True
    assert card["weighting"]["on"] is True
    assert (out / "geom.png").is_file()
    assert not (out / "amoe.png").exists()
    plate = np.asarray(Image.open(out / "zero.png").convert("RGB"), dtype=np.float32) / 255.0
    paper = plate[30:38, 60:68].mean(axis=(0, 1))
    assert _align(paper, "#2E5A8C") > 0.85

    bare = subprocess.run(
        [
            sys.executable,
            str(ROOT / "run.py"),
            "overlay",
            str(page),
            "--mode",
            "zero",
            "--no-geom",
            "--no-weight",
            "--out",
            str(tmp_path / "bare"),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert bare.returncode == 0, bare.stderr
    bare_card = json.loads(bare.stdout)
    assert bare_card["geom"]["on"] is False
    assert bare_card["weighting"]["on"] is False
    assert not (tmp_path / "bare" / "geom.png").exists()

    for command in ("recover-image", "recover-script", "route", "preocr", "together"):
        dest = tmp_path / command
        result = subprocess.run(
            [sys.executable, str(ROOT / "run.py"), command, str(page), "--out", str(dest)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        body = json.loads(result.stdout)
        assert body["pigment_recovery"] is False
        assert body["letters_recovered"] is False
        assert body["transcription"] is None
        assert "amoe.png" not in {path.name for path in dest.rglob("*.png")}

    script = subprocess.run(
        [
            sys.executable,
            str(ROOT / "run.py"),
            "script",
            str(page),
            "--mode",
            "tazel",
            "--out",
            str(tmp_path / "script"),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert script.returncode == 0, script.stderr
    assert json.loads(script.stdout)["focus"] == "tazel"
