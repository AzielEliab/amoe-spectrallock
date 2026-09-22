"""AMOE-1.2 command line. Local execution. Catalog is not a Worker op.

Author: Aziel Eliab.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from amoe import AmoeError, __author__, __paper__, __version__, package_root
from amoe.adapt import adapt, reconstruct
from amoe.gallery import save_gallery
from amoe.geom import save_overlay
from amoe.paint import lift_gray, write_png
from amoe.path import audit, engine_opaque_refuse
from amoe.wheel import (
    CUSTODIAN,
    ENGINE_BLEND,
    ENGINE_HEX,
    ENGINE_HUE,
    GRID,
    REFUSE_INVENT_LETTER,
    REFUSE_INVENT_MARK,
    RING,
    WATERFALL,
    WHEEL_HEX,
    reject_name,
)
from amoe.wrap import _base_card, invention_card, load_page, paint_only, parse_indices, process, write_card


def _print(payload: dict) -> None:
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")


def _exit_code(payload: dict) -> int:
    code = payload.get("refuse")
    if not code or code == "AMOE-EMPTY-HUE":
        return 0
    if code == "AMOE-RECONSTRUCT-NOT-NEEDED":
        return 0
    return 2


def _add_page(parser: argparse.ArgumentParser, *, required: bool = True) -> None:
    parser.add_argument("page", nargs=None if required else "?")
    parser.add_argument("--out", type=Path, default=None)


def _add_lens_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--target", choices=["ink", "page"], default=None)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--inject", dest="inject", action="store_true")
    group.add_argument("--no-inject", dest="inject", action="store_false")
    parser.set_defaults(inject=True)
    parser.add_argument("--paint", choices=["wheel", "engine"], default="engine")
    parser.add_argument("--lift", action="store_true")
    parser.add_argument("--index", action="append", default=[], metavar="KEY=0..1")
    parser.add_argument("--invent-letters", action="store_true")
    parser.add_argument("--invent-mark", action="store_true")
    parser.add_argument("--operator-note", default=None)


def _out(page: str, out: Path | None, name: str) -> Path:
    if out is not None:
        return out
    stem = Path(page).stem or "page"
    return Path("amoe-out") / stem / name


def _guard_invention(args: argparse.Namespace, out: Path) -> dict | None:
    note = args.operator_note
    if args.invent_letters:
        card = invention_card(REFUSE_INVENT_LETTER, note or "invent_letters refused")
        write_card(card, out / "amoe.json")
        return card
    if args.invent_mark:
        card = invention_card(REFUSE_INVENT_MARK, note or "invent_mark refused")
        write_card(card, out / "amoe.json")
        return card
    return None


def _cmd_overlay(args: argparse.Namespace) -> int:
    code = reject_name(args.mode)
    out = _out(args.page, args.out, "overlay")
    if code:
        card = invention_card(code, args.operator_note)
        card["mode"] = args.mode
        write_card(card, out / "amoe.json")
        _print(card)
        return 2
    blocked = _guard_invention(args, out)
    if blocked:
        _print(blocked)
        return 2
    rgb, digest = load_page(Path(args.page))
    card = process(
        rgb,
        src=str(args.page),
        out_dir=out,
        modes=[args.mode],
        target=args.target,
        inject=args.inject,
        paint=args.paint,
        lift=args.lift,
        indices=parse_indices(args.index),
        sha256_in=digest,
    )
    _print(card)
    return _exit_code(card)


def _cmd_grid(args: argparse.Namespace) -> int:
    out = _out(args.page, args.out, "grid")
    blocked = _guard_invention(args, out)
    if blocked:
        _print(blocked)
        return 2
    rgb, digest = load_page(Path(args.page))
    card = process(
        rgb,
        src=str(args.page),
        out_dir=out,
        modes=list(GRID),
        target=args.target,
        inject=args.inject,
        paint=args.paint,
        lift=args.lift,
        indices=parse_indices(args.index),
        sha256_in=digest,
    )
    _print(card)
    return _exit_code(card)


def _cmd_paint(args: argparse.Namespace) -> int:
    code = reject_name(args.mode) if args.mode else None
    out = _out(args.page, args.out, "paint")
    if code:
        card = invention_card(code, args.operator_note)
        write_card(card, out / "paint.json")
        _print(card)
        return 2
    rgb, _digest = load_page(Path(args.page))
    if args.palette == "wheel":
        modes = [args.mode] if args.mode else list(RING) + ["zen"]
    else:
        modes = [args.mode] if args.mode else list(GRID)
    card = paint_only(rgb, out_dir=out, palette=args.palette, modes=modes)
    _print(card)
    return 0


def _cmd_gallery(args: argparse.Namespace) -> int:
    rgb, _digest = load_page(Path(args.page))
    out = _out(args.page, args.out, "gallery")
    out.mkdir(parents=True, exist_ok=True)
    card = save_gallery(rgb, out / "gallery.png")
    write_card(card, out / "gallery.json")
    _print(card)
    return 0


def _cmd_lift(args: argparse.Namespace) -> int:
    rgb, digest = load_page(Path(args.page))
    out = _out(args.page, args.out, "lift")
    out.mkdir(parents=True, exist_ok=True)
    sha = write_png(lift_gray(rgb), out / "lift.png")
    card = _base_card(
        src=str(args.page),
        sha256_in=digest,
        refuse=None,
        lift={"path": "lift.png", "sha256": sha},
        note="Percentile stretch, equalize, unsharp on present pixels. No new letters.",
    )
    write_card(card, out / "amoe.json")
    _print(card)
    return 0


def _cmd_geom(args: argparse.Namespace) -> int:
    rgb, digest = load_page(Path(args.page))
    out = _out(args.page, args.out, "geom")
    out.mkdir(parents=True, exist_ok=True)
    meta = save_overlay(rgb, out / "geom.png")
    card = {
        "product": "amoe",
        "version": __version__,
        "paper": __paper__,
        "author": __author__,
        "amoe_is_field": False,
        "amoe_is_wiring": True,
        "src": str(args.page),
        "sha256_in": digest,
        "invent_letters": False,
        "pigment_recovery": False,
        "invent_figures": False,
        "geom": meta,
        "refuse": None,
    }
    write_card(card, out / "geom.json")
    _print(card)
    return 0


def _cmd_adapt(args: argparse.Namespace) -> int:
    rgb, digest = load_page(Path(args.page))
    out = _out(args.page, args.out, "adapt")
    card = adapt(
        rgb,
        src=str(args.page),
        out_dir=out,
        sha256_in=digest,
        with_grid=args.grid,
        target=args.target,
        inject=args.inject,
        indices=parse_indices(args.index),
    )
    _print(card)
    return _exit_code(card)


def _cmd_reconstruct(args: argparse.Namespace) -> int:
    out = args.out or Path("amoe-out") / "reconstruct"
    if not args.page:
        card = reconstruct(None, out_dir=out)
        _print(card)
        return 2
    rgb, digest = load_page(Path(args.page))
    card = reconstruct(
        rgb,
        src=str(args.page),
        out_dir=_out(args.page, args.out, "adapt"),
        sha256_in=digest,
        with_grid=False,
        target=None,
        inject=False,
        indices=None,
    )
    _print(card)
    return _exit_code(card)


def _cmd_path(args: argparse.Namespace) -> int:
    payload = json.loads(Path(args.card).read_text(encoding="utf-8"))
    card = audit(payload)
    _print(card)
    return 0 if card["ok"] else 2


def _cmd_catalog(_args: argparse.Namespace) -> int:
    path = package_root() / "catalog.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    _print(payload)
    return 0


def _cmd_custodian(_args: argparse.Namespace) -> int:
    card = {
        "product": "amoe",
        "version": __version__,
        "paper": __paper__,
        "author": __author__,
        "amoe_is_field": False,
        "amoe_is_wiring": True,
        "custodians": CUSTODIAN,
        "waterfall": WATERFALL,
        "wheel_hex": WHEEL_HEX,
        "engine_hex": ENGINE_HEX,
        "engine_hue": ENGINE_HUE,
        "engine_blend": ENGINE_BLEND,
        "pigment_recovery": False,
        "invent_letters": False,
        "note": "Pigment restore is a SpectralLock product door. AMOE does not run it.",
        "engine_opaque_refuse": engine_opaque_refuse(),
    }
    _print(card)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run.py",
        description=(
            "AMOE-1.2 wiring on the SpectralLock 0.3.1 grid. "
            "Not a field and not a color. Author Aziel Eliab. "
            "The human still reads the page."
        ),
    )
    parser.add_argument("--version", action="version", version=f"AMOE {__version__} ({__paper__})")
    sub = parser.add_subparsers(dest="cmd", required=True)

    overlay = sub.add_parser("overlay", help="One SpectralLock lens plus an AMOE card")
    _add_page(overlay)
    overlay.add_argument("--mode", required=True)
    _add_lens_flags(overlay)
    overlay.set_defaults(func=_cmd_overlay)

    grid = sub.add_parser("grid", help="All eleven lenses. No twelfth color.")
    _add_page(grid)
    _add_lens_flags(grid)
    grid.set_defaults(func=_cmd_grid)

    paint = sub.add_parser("paint", help="False-color a luminance ink mask")
    _add_page(paint)
    paint.add_argument("--palette", choices=["wheel", "engine"], required=True)
    paint.add_argument("--mode", default=None)
    paint.set_defaults(func=_cmd_paint)

    gallery = sub.add_parser("gallery", help="Labeled 3×3 wheel sheet")
    _add_page(gallery)
    gallery.set_defaults(func=_cmd_gallery)

    lift = sub.add_parser("lift", help="Stretch, equalize, and unsharp present pixels")
    _add_page(lift)
    lift.set_defaults(func=_cmd_lift)

    geom = sub.add_parser("geom", help="ZERO geometry from edges")
    _add_page(geom)
    geom.set_defaults(func=_cmd_geom)

    adapt_p = sub.add_parser("adapt", help="Classify the page and reconstruct only if faint")
    _add_page(adapt_p)
    adapt_p.add_argument("--grid", action="store_true", help="Also write the eleven-lens grid")
    adapt_p.add_argument("--target", choices=["ink", "page"], default=None)
    group = adapt_p.add_mutually_exclusive_group()
    group.add_argument("--inject", dest="inject", action="store_true")
    group.add_argument("--no-inject", dest="inject", action="store_false")
    adapt_p.set_defaults(inject=True)
    adapt_p.add_argument("--index", action="append", default=[], metavar="KEY=0..1")
    adapt_p.set_defaults(func=_cmd_adapt)

    recon = sub.add_parser("reconstruct", help="Alias of adapt when a page is given")
    _add_page(recon, required=False)
    recon.set_defaults(func=_cmd_reconstruct)

    path = sub.add_parser("path", help="Audit a path card. Does not read pixels.")
    path.add_argument("--card", required=True)
    path.set_defaults(func=_cmd_path)

    catalog = sub.add_parser("catalog", help="Print the catalog fragment")
    catalog.set_defaults(func=_cmd_catalog)

    custodian = sub.add_parser("custodian", help="Print custodian bind and waterfall route")
    custodian.set_defaults(func=_cmd_custodian)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except AmoeError as exc:
        payload = invention_card(exc.code, str(exc.extra) if exc.extra else None)
        payload["extra"] = exc.extra
        _print(payload)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
