"""AMOE-1.3 command line. Local execution. Catalog is not a Worker op.

People get a short reading. Machines pass --json and receive the same card.

Author: Aziel Eliab.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from amoe import AmoeError, __author__, __paper__, __version__, package_root
from amoe.adapt import adapt, reconstruct
from amoe.doctor import doctor_card
from amoe.gallery import save_gallery
from amoe.geom import save_overlay
from amoe.human import help_text, summarize, usage_hint, welcome_card, welcome_text
from amoe.paint import lift_gray, write_png
from amoe.path import audit, engine_opaque_refuse
from amoe.script import preocr_page, recover_image, recover_script, route_page, together_page
from amoe.wheel import (
    CUSTODIAN,
    ENGINE_BLEND,
    ENGINE_HEX,
    ENGINE_HUE,
    ENGINE_NOTE,
    GRID,
    PAINT_LAW,
    REFUSE_INVENT_LETTER,
    REFUSE_INVENT_MARK,
    REFUSE_WEAK_SIGNAL,
    RING,
    RING_CW_FROM_ZERO,
    WATERFALL,
    WHEEL_HEX,
    WHEEL_LAW,
    reject_name,
)
from amoe.wrap import invention_card, load_page, paint_only, parse_indices, process, reading_card, write_card


class AmoeParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        sys.stderr.write(usage_hint(self.prog, message) + "\n")
        self.exit(2)


def _print(payload: dict) -> None:
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")


def emit(card: dict, *, as_json: bool, folder: Path | None = None) -> None:
    if as_json:
        _print(card)
        return
    sys.stdout.write(summarize(card, folder=folder))


def _wants_json(argv: list[str]) -> tuple[bool, list[str]]:
    return "--json" in argv, [item for item in argv if item != "--json"]


def _exit_code(payload: dict) -> int:
    raw = payload.get("refuse")
    if raw is None or raw == [] or raw == "":
        return 0
    codes = list(raw) if isinstance(raw, (list, tuple)) else [raw]
    soft = {
        "AMOE-EMPTY-HUE",
        REFUSE_WEAK_SIGNAL,
        "AMOE-RECONSTRUCT-NOT-NEEDED",
    }
    if all(code in soft for code in codes):
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
    parser.add_argument("--paint", choices=["wheel", "engine"], default="wheel")
    parser.add_argument("--lift", action="store_true")
    parser.add_argument("--index", action="append", default=[], metavar="KEY=0..1")
    parser.add_argument("--no-geom", action="store_true", help="Geometry is on unless this is set")
    parser.add_argument("--no-weight", action="store_true", help="Harmonic weighting is on unless this is set")
    parser.add_argument("--invent-letters", action="store_true")
    parser.add_argument("--invent-mark", action="store_true")
    parser.add_argument("--operator-note", default=None)


def _out(page: str, out: Path | None, name: str) -> Path:
    if out is not None:
        return out
    stem = Path(page).stem or "page"
    return Path("amoe-out") / stem / name


def _load(page: str):
    path = Path(page)
    if not path.is_file():
        raise AmoeError("AMOE-NO-PAGE", path=str(page))
    try:
        return load_page(path)
    except ValueError as exc:
        raise AmoeError("AMOE-NOT-PICTURE", path=str(page), detail=str(exc)) from exc


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
        emit(card, as_json=args.as_json, folder=out)
        return 2
    blocked = _guard_invention(args, out)
    if blocked:
        emit(blocked, as_json=args.as_json, folder=out)
        return 2
    rgb, digest = _load(args.page)
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
        geom=not args.no_geom,
        weight=not args.no_weight,
    )
    emit(card, as_json=args.as_json, folder=out)
    return _exit_code(card)


def _cmd_grid(args: argparse.Namespace) -> int:
    out = _out(args.page, args.out, "grid")
    blocked = _guard_invention(args, out)
    if blocked:
        emit(blocked, as_json=args.as_json, folder=out)
        return 2
    rgb, digest = _load(args.page)
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
        geom=not args.no_geom,
        weight=not args.no_weight,
    )
    emit(card, as_json=args.as_json, folder=out)
    return _exit_code(card)


def _cmd_paint(args: argparse.Namespace) -> int:
    code = reject_name(args.mode) if args.mode else None
    out = _out(args.page, args.out, "paint")
    if code:
        card = invention_card(code, args.operator_note)
        write_card(card, out / "paint.json")
        emit(card, as_json=args.as_json, folder=out)
        return 2
    rgb, _digest = _load(args.page)
    if args.palette == "wheel":
        modes = [args.mode] if args.mode else [*RING, "zen", "balance"]
    else:
        modes = [args.mode] if args.mode else list(GRID)
    card = paint_only(rgb, out_dir=out, palette=args.palette, modes=modes)
    emit(card, as_json=args.as_json, folder=out)
    return 0


def _cmd_gallery(args: argparse.Namespace) -> int:
    rgb, _digest = _load(args.page)
    out = _out(args.page, args.out, "gallery")
    out.mkdir(parents=True, exist_ok=True)
    card = save_gallery(rgb, out / "gallery.png")
    card = reading_card(rgb, **card)
    write_card(card, out / "gallery.json")
    write_card(card, out / "amoe.json")
    emit(card, as_json=args.as_json, folder=out)
    return _exit_code(card)


def _cmd_lift(args: argparse.Namespace) -> int:
    rgb, digest = _load(args.page)
    out = _out(args.page, args.out, "lift")
    out.mkdir(parents=True, exist_ok=True)
    sha = write_png(lift_gray(rgb), out / "lift.png")
    card = reading_card(
        rgb,
        src=str(args.page),
        sha256_in=digest,
        lift={"path": "lift.png", "sha256": sha},
        note="Percentile stretch, equalize, unsharp on present pixels. No new letters.",
    )
    write_card(card, out / "amoe.json")
    emit(card, as_json=args.as_json, folder=out)
    return _exit_code(card)


def _cmd_geom(args: argparse.Namespace) -> int:
    rgb, digest = _load(args.page)
    out = _out(args.page, args.out, "geom")
    out.mkdir(parents=True, exist_ok=True)
    if args.no_geom:
        meta = {
            "on": False,
            "drawn": False,
            "invent_figures": False,
            "path": "geom.png",
            "sha256": write_png(rgb, out / "geom.png"),
            "weighting": {"on": False} if args.no_weight else None,
        }
    else:
        meta = save_overlay(rgb, out / "geom.png", weight=not args.no_weight)
    card = reading_card(
        rgb,
        src=str(args.page),
        sha256_in=digest,
        invent_figures=False,
        geom=meta,
        weighting=meta.get("weighting"),
    )
    write_card(card, out / "geom.json")
    write_card(card, out / "amoe.json")
    emit(card, as_json=args.as_json, folder=out)
    return _exit_code(card)


def _cmd_adapt(args: argparse.Namespace) -> int:
    rgb, digest = _load(args.page)
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
    emit(card, as_json=args.as_json, folder=out)
    return _exit_code(card)


def _cmd_reconstruct(args: argparse.Namespace) -> int:
    out = args.out or Path("amoe-out") / "reconstruct"
    if not args.page:
        card = reconstruct(None, out_dir=out)
        emit(card, as_json=args.as_json, folder=out)
        return 2
    rgb, digest = _load(args.page)
    folder = _out(args.page, args.out, "adapt")
    card = reconstruct(
        rgb,
        src=str(args.page),
        out_dir=folder,
        sha256_in=digest,
        with_grid=False,
        target=None,
        inject=False,
        indices=None,
    )
    emit(card, as_json=args.as_json, folder=folder)
    return _exit_code(card)


def _cmd_path(args: argparse.Namespace) -> int:
    path = Path(args.card)
    if not path.is_file():
        card = invention_card("AMOE-NO-CARD")
        card["extra"] = {"path": str(path)}
        emit(card, as_json=args.as_json)
        return 2
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        card = invention_card("AMOE-BAD-JSON")
        emit(card, as_json=args.as_json)
        return 2
    if not isinstance(payload, dict):
        card = invention_card("AMOE-BAD-JSON")
        emit(card, as_json=args.as_json)
        return 2
    card = audit(payload)
    emit(card, as_json=args.as_json)
    return 0 if card["ok"] else 2


def _cmd_catalog(_args: argparse.Namespace) -> int:
    path = package_root() / "catalog.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    emit(payload, as_json=_args.as_json)
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
        "wheel_law": WHEEL_LAW,
        "ring_cw_from_zero": RING_CW_FROM_ZERO,
        "engine_hex": ENGINE_HEX,
        "engine_hue": ENGINE_HUE,
        "engine_blend": ENGINE_BLEND,
        "engine_note": ENGINE_NOTE,
        "paint_law": PAINT_LAW,
        "pigment_recovery": False,
        "invent_letters": False,
        "note": "Pigment restore is a SpectralLock product door. AMOE does not run it.",
        "engine_opaque_refuse": engine_opaque_refuse(),
    }
    emit(card, as_json=_args.as_json)
    return 0


def _cmd_recover_image(args: argparse.Namespace) -> int:
    rgb, digest = _load(args.page)
    out = _out(args.page, args.out, "recover-image")
    card = recover_image(
        rgb,
        src=str(args.page),
        out_dir=out,
        sha256_in=digest,
        geom=not args.no_geom,
        weight=not args.no_weight,
    )
    emit(card, as_json=args.as_json, folder=out)
    return _exit_code(card)


def _cmd_recover_script(args: argparse.Namespace) -> int:
    rgb, digest = _load(args.page)
    out = _out(args.page, args.out, "recover-script")
    card = recover_script(
        rgb,
        src=str(args.page),
        out_dir=out,
        sha256_in=digest,
        geom=not args.no_geom,
        weight=not args.no_weight,
    )
    emit(card, as_json=args.as_json, folder=out)
    return _exit_code(card)


def _cmd_script(args: argparse.Namespace) -> int:
    code = reject_name(args.mode)
    out = _out(args.page, args.out, "script")
    if code:
        card = invention_card(code, None)
        card["mode"] = args.mode
        write_card(card, out / "amoe.json")
        emit(card, as_json=args.as_json, folder=out)
        return 2
    rgb, digest = _load(args.page)
    card = recover_script(
        rgb,
        src=str(args.page),
        out_dir=out,
        sha256_in=digest,
        mode=args.mode,
        geom=not args.no_geom,
        weight=not args.no_weight,
    )
    emit(card, as_json=args.as_json, folder=out)
    return _exit_code(card)


def _cmd_route(args: argparse.Namespace) -> int:
    rgb, digest = _load(args.page)
    out = _out(args.page, args.out, "route")
    card = route_page(
        rgb,
        src=str(args.page),
        out_dir=out,
        sha256_in=digest,
        geom=not args.no_geom,
        weight=not args.no_weight,
    )
    emit(card, as_json=args.as_json, folder=out)
    return _exit_code(card)


def _cmd_preocr(args: argparse.Namespace) -> int:
    rgb, digest = _load(args.page)
    out = _out(args.page, args.out, "preocr")
    card = preocr_page(rgb, src=str(args.page), out_dir=out, sha256_in=digest)
    emit(card, as_json=args.as_json, folder=out)
    return _exit_code(card)


def _cmd_together(args: argparse.Namespace) -> int:
    rgb, digest = _load(args.page)
    out = _out(args.page, args.out, "together")
    card = together_page(
        rgb,
        src=str(args.page),
        out_dir=out,
        sha256_in=digest,
        geom=not args.no_geom,
        weight=not args.no_weight,
    )
    emit(card, as_json=args.as_json, folder=out)
    return _exit_code(card)


def _cmd_doctor(args: argparse.Namespace) -> int:
    card = doctor_card()
    emit(card, as_json=args.as_json)
    return 0 if card["ok"] else 1


def _cmd_ui(args: argparse.Namespace) -> int:
    from amoe.ui import serve

    try:
        serve(host=args.host, port=args.port)
    except ValueError as exc:
        sys.stderr.write(str(exc) + "\nTry: amoe ui\n")
        return 2
    return 0


def _add_ui(sub: argparse._SubParsersAction, name: str, help_line: str) -> None:
    parser = sub.add_parser(name, help=help_line)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8871)
    parser.set_defaults(func=_cmd_ui)


def build_parser() -> AmoeParser:
    parser = AmoeParser(prog="amoe", add_help=True)
    parser.format_help = lambda: help_text()  # type: ignore[method-assign]
    parser.add_argument("--version", action="version", version=f"AMOE {__version__} ({__paper__})")
    sub = parser.add_subparsers(dest="cmd", required=False, parser_class=AmoeParser)

    overlay = sub.add_parser("overlay", help="Color one lens on a page")
    _add_page(overlay)
    overlay.add_argument("--mode", required=True)
    _add_lens_flags(overlay)
    overlay.set_defaults(func=_cmd_overlay)

    grid = sub.add_parser("grid", help="All eleven lenses")
    _add_page(grid)
    _add_lens_flags(grid)
    grid.set_defaults(func=_cmd_grid)

    paint = sub.add_parser("paint", help="False-color a luminance ink mask")
    _add_page(paint)
    paint.add_argument("--palette", choices=["wheel", "engine"], required=True)
    paint.add_argument("--mode", default=None)
    paint.set_defaults(func=_cmd_paint)

    gallery = sub.add_parser("gallery", help="Labeled wheel sheet")
    _add_page(gallery)
    gallery.set_defaults(func=_cmd_gallery)

    lift = sub.add_parser("lift", help="Stretch pixels already on the page")
    _add_page(lift)
    lift.set_defaults(func=_cmd_lift)

    geom = sub.add_parser("geom", help="ZERO geometry from edges")
    _add_page(geom)
    geom.add_argument("--no-geom", action="store_true", help="Geometry is on unless this is set")
    geom.add_argument("--no-weight", action="store_true", help="Harmonic weighting is on unless this is set")
    geom.set_defaults(func=_cmd_geom)

    adapt_p = sub.add_parser("adapt", help="Read the page and rebuild only if it is faint")
    _add_page(adapt_p)
    adapt_p.add_argument("--grid", action="store_true", help="Also write the eleven-lens grid")
    adapt_p.add_argument("--target", choices=["ink", "page"], default=None)
    group = adapt_p.add_mutually_exclusive_group()
    group.add_argument("--inject", dest="inject", action="store_true")
    group.add_argument("--no-inject", dest="inject", action="store_false")
    adapt_p.set_defaults(inject=True)
    adapt_p.add_argument("--index", action="append", default=[], metavar="KEY=0..1")
    adapt_p.set_defaults(func=_cmd_adapt)

    recon = sub.add_parser("reconstruct", help="Same path as adapt when a page is given")
    _add_page(recon, required=False)
    recon.set_defaults(func=_cmd_reconstruct)

    path = sub.add_parser("path", help="Audit a path card")
    path.add_argument("--card", required=True)
    path.set_defaults(func=_cmd_path)

    catalog = sub.add_parser("catalog", help="Show the catalog card")
    catalog.set_defaults(func=_cmd_catalog)

    custodian = sub.add_parser("custodian", help="Show the custodian bind")
    custodian.set_defaults(func=_cmd_custodian)

    recover_i = sub.add_parser("recover-image", help="Pull, ZERO sheet, geometry")
    _add_page(recover_i)
    recover_i.add_argument("--no-geom", action="store_true")
    recover_i.add_argument("--no-weight", action="store_true")
    recover_i.set_defaults(func=_cmd_recover_image)

    recover_s = sub.add_parser("recover-script", help="Script track on marks already visible")
    _add_page(recover_s)
    recover_s.add_argument("--no-geom", action="store_true")
    recover_s.add_argument("--no-weight", action="store_true")
    recover_s.set_defaults(func=_cmd_recover_script)

    script = sub.add_parser("script", help="Script track focused on one lens")
    _add_page(script)
    script.add_argument("--mode", required=True)
    script.add_argument("--no-geom", action="store_true")
    script.add_argument("--no-weight", action="store_true")
    script.set_defaults(func=_cmd_script)

    route = sub.add_parser("route", help="Paint the lens with the strongest residual contrast")
    _add_page(route)
    route.add_argument("--no-geom", action="store_true")
    route.add_argument("--no-weight", action="store_true")
    route.set_defaults(func=_cmd_route)

    pre = sub.add_parser("preocr", help="Darken strokes already on the page")
    _add_page(pre)
    pre.set_defaults(func=_cmd_preocr)

    both = sub.add_parser("together", help="Script search, then image isolation")
    _add_page(both)
    both.add_argument("--no-geom", action="store_true")
    both.add_argument("--no-weight", action="store_true")
    both.set_defaults(func=_cmd_together)

    doctor = sub.add_parser("doctor", help="Check this install")
    doctor.set_defaults(func=_cmd_doctor)

    _add_ui(sub, "ui", "Open the local page on 127.0.0.1")
    _add_ui(sub, "serve", "Same as ui")
    return parser


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    as_json, raw = _wants_json(raw)
    if not raw:
        if as_json:
            _print(welcome_card())
        else:
            sys.stdout.write(welcome_text())
        return 0
    parser = build_parser()
    args = parser.parse_args(raw)
    if not getattr(args, "cmd", None):
        if as_json:
            _print(welcome_card())
        else:
            sys.stdout.write(welcome_text())
        return 0
    args.as_json = as_json
    try:
        return int(args.func(args))
    except AmoeError as exc:
        payload = invention_card(exc.code, str(exc.extra) if exc.extra else None)
        payload["extra"] = exc.extra
        emit(payload, as_json=as_json)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
