"""Plain language for the AMOE command. Machine cards stay on --json.

Author: Aziel Eliab.
"""

from __future__ import annotations

from pathlib import Path

from amoe import __author__, __paper__, __version__

SOFT_REFUSE = frozenset(
    {
        "AMOE-EMPTY-HUE",
        "AMOE-WEAK-SIGNAL",
        "AMOE-RECONSTRUCT-NOT-NEEDED",
    }
)


def welcome_text() -> str:
    return (
        f"AMOE {__version__}\n"
        "\n"
        "Pull faded structure from a page picture, then color what was pulled\n"
        "with the defined wheel. You still read the page.\n"
        "\n"
        "  amoe overlay page.jpg --mode tazel\n"
        "  amoe ui\n"
        "  amoe doctor\n"
        "  amoe --help\n"
        "\n"
        f"Author: {__author__}\n"
    )


def welcome_card() -> dict:
    return {
        "product": "amoe",
        "version": __version__,
        "paper": __paper__,
        "author": __author__,
        "amoe_is_field": False,
        "amoe_is_wiring": True,
        "pigment_recovery": False,
        "invent_letters": False,
        "next": [
            "amoe overlay page.jpg --mode tazel",
            "amoe ui",
            "amoe doctor",
            "amoe --help",
        ],
    }


def help_text() -> str:
    return f"""amoe — color a page with the defined wheel

usage: amoe <command> [options]

Pull faded structure from a page picture, then color what was pulled.
You still read the page. Author: {__author__}.

Start
  overlay PAGE --mode LENS     Color one lens
  gallery PAGE                 Labeled wheel sheet
  lift PAGE                    Stretch pixels already on the page
  adapt PAGE                   Read the page; rebuild only if it is faint
  ui                           Open the local page

Also
  doctor                       Check this install
  catalog                      Show the catalog card
  --help                       Show this message
  --json                       Print the machine card
  --version                    Print {__version__}

Advanced
  grid PAGE                    All eleven lenses
  paint PAGE --palette wheel|engine
  geom PAGE                    ZERO geometry from edges
  path --card FILE             Audit a path card
  custodian                    Custodian bind
  recover-image PAGE
  recover-script PAGE
  script PAGE --mode LENS
  route PAGE
  preocr PAGE
  together PAGE
  reconstruct PAGE             Same path as adapt when a page is given

Examples
  amoe overlay page.jpg --mode tazel
  amoe gallery page.jpg
  amoe overlay page.jpg --mode tazel --json

Geometry and weighting are on unless you pass --no-geom or --no-weight.
--paint wheel is the operator plate. --paint engine is the membership hex.
python3 run.py is the same command as amoe.
"""


def usage_hint(prog: str, message: str) -> str:
    text = str(message or "")
    command = _command_from_prog(prog)
    if "invalid choice" in text:
        name = _quoted(text) or "that"
        return (
            f'Unknown command "{name}". '
            "Try: amoe overlay PAGE.jpg --mode tazel   or   amoe --help"
        )
    if "unrecognized arguments" in text:
        extra = text.split(":", 1)[-1].strip()
        return f"Unknown option {extra}. Try: amoe --help"
    if command == "overlay" and "--mode" in text:
        return "overlay needs a lens. Try: amoe overlay PAGE.jpg --mode tazel"
    if command == "overlay" and "page" in text:
        return "overlay needs a page picture. Try: amoe overlay PAGE.jpg --mode tazel"
    if command == "paint" and "--palette" in text:
        return "paint needs a palette. Try: amoe paint PAGE.jpg --palette wheel"
    if command == "script" and "--mode" in text:
        return "script needs a lens. Try: amoe script PAGE.jpg --mode tazel"
    if command == "path" and "--card" in text:
        return "path needs a card file. Try: amoe path --card steps.json"
    if command in {"grid", "gallery", "lift", "geom", "adapt", "recover-image", "recover-script", "route", "preocr", "together"} and "page" in text:
        return f"{command} needs a page picture. Try: amoe {command} PAGE.jpg"
    if "required" in text and command:
        return f"{command} is missing something. Try: amoe {command} --help"
    if "required" in text:
        return "Try: amoe overlay PAGE.jpg --mode tazel   or   amoe --help"
    return f"{text}. Try: amoe --help"


def summarize(card: dict, *, folder: Path | None = None) -> str:
    """Short reading of a card. The card itself is unchanged for --json."""
    if card.get("checks"):
        return _doctor_lines(card)
    if card.get("slug") == "amoe" and "grid" in card and "cells" not in card:
        return _catalog_lines(card)
    if card.get("custodians") and "cells" not in card:
        return _custodian_lines(card)

    refuse = _codes(card)
    hard = [code for code in refuse if code not in SOFT_REFUSE]
    worked = bool(
        card.get("cells")
        or card.get("files")
        or card.get("layout")
        or card.get("lift")
        or card.get("condition")
        or card.get("track")
        or card.get("geom")
        or card.get("step_names")
        or card.get("ok") is True
    )
    if hard and not worked:
        return "\n".join(_refuse_sentence(code) for code in hard) + "\n"

    lines: list[str] = []
    cells = card.get("cells") or {}
    if cells:
        names = ", ".join(cells)
        paint = card.get("paint") or "wheel"
        lines.append(f"Colored {names} with the {paint} plate.")
        files = [f"{name}: {cell.get('path')}" for name, cell in cells.items() if cell.get("path")]
        if files:
            lines.append("Files: " + ", ".join(files))
    elif isinstance(card.get("files"), list):
        paint = card.get("paint") or "wheel"
        lines.append(f"Painted with the {paint} plate.")
        names = [row.get("path") for row in card["files"] if isinstance(row, dict) and row.get("path")]
        if names:
            lines.append("Files: " + ", ".join(str(name) for name in names))
    elif card.get("track") == "route" and card.get("winner"):
        lines.append(f"Painted the strongest residual contrast: {card['winner']}.")
        winner = (card.get("files") or {}).get("winner") if isinstance(card.get("files"), dict) else None
        if isinstance(winner, dict) and winner.get("path"):
            lines.append(f"File: {winner['path']}")
    elif card.get("track"):
        lines.append(f"{_track_label(str(card['track']))}.")
        names = _file_names(card.get("files"))
        if names:
            lines.append("Files: " + ", ".join(names))
        if card.get("focus"):
            lines.append(f"Focus: {card['focus']}")
        if card.get("transcription") is None and card["track"] in {"script", "together", "preocr", "image"}:
            lines.append("No transcription was declared.")
    elif card.get("layout") and card.get("path"):
        lines.append(f"Gallery sheet: {card['path']}")
    elif isinstance(card.get("lift"), dict):
        lines.append(f"Lifted pixels already on the page: {card['lift'].get('path', 'lift.png')}")
    elif isinstance(card.get("condition"), dict):
        lines.append(_condition_line(card))
    elif card.get("paper") == "AMOE-PATH-1.0":
        if card.get("ok"):
            pairs = [f"{number} {name}" for number, name in zip(card.get("steps") or [], card.get("step_names") or [])]
            lines.append("Path card accepted.")
            if pairs:
                lines.append("Steps: " + ", ".join(pairs) + ".")
        else:
            lines.append(_refuse_sentence(str(card.get("refuse") or "AMOE-NO-FIGURE")))
    elif isinstance(card.get("geom"), dict) and card.get("src"):
        if card["geom"].get("on") is False:
            lines.append("Geometry is off. The picture was passed through.")
        elif card["geom"].get("drawn") is False:
            lines.append("No edge frame to draw. The picture was left as it is.")
        else:
            lines.append(f"Geometry: {card['geom'].get('path', 'geom.png')}")
    elif card.get("next"):
        return welcome_text()
    else:
        lines.append(f"AMOE {card.get('version', __version__)} recorded the reading.")

    if folder is not None:
        lines.append(f"Folder: {folder}")
    for code in refuse:
        sentence = _refuse_sentence(code)
        if sentence and sentence not in lines and not any(sentence in line for line in lines):
            lines.append(sentence)
    return "\n".join(lines) + "\n"


def _doctor_lines(card: dict) -> str:
    lines = [f"AMOE {card.get('version', __version__)}"]
    for check in card.get("checks") or []:
        mark = "pass" if check.get("ok") else "fail"
        detail = check.get("detail") or ""
        lines.append(f"{check.get('name')}: {mark}" + (f" — {detail}" if detail else ""))
    lines.append("telemetry: none")
    lines.append("ok" if card.get("ok") else "fail")
    return "\n".join(lines) + "\n"


def _catalog_lines(card: dict) -> str:
    return (
        f"AMOE {card.get('version', __version__)}\n"
        f"Paper: {card.get('paper', __paper__)}\n"
        f"Author: {card.get('author', __author__)}\n"
        f"Depends: {card.get('depends', 'spectrallock@0.3.1')}\n"
        "Wiring on the SpectralLock color grid.\n"
        "Machine card: amoe catalog --json\n"
    )


def _custodian_lines(card: dict) -> str:
    lines = ["Custodians"]
    for code, row in (card.get("custodians") or {}).items():
        if isinstance(row, dict):
            lines.append(f"  {code}  {row.get('role')}  {row.get('lens')}")
    waterfall = card.get("waterfall") or {}
    route = waterfall.get("route") if isinstance(waterfall, dict) else None
    if route:
        lines.append(f"Waterfall Guardian Plate: {route}.")
    return "\n".join(lines) + "\n"


def _condition_line(card: dict) -> str:
    state = str((card.get("condition") or {}).get("state") or "")
    if state == "present":
        line = "The page is still clear, so it was left in place."
    elif state == "faint":
        line = "The page is faint. A ZERO plate was written."
    elif state == "near_gone":
        line = "The page is near gone. A ZERO plate was written."
    else:
        line = "The page was read."
    extra = ""
    recon = card.get("reconstruct_zero")
    if isinstance(recon, dict) and recon.get("path"):
        extra = f" File: {recon['path']}."
    elif isinstance(card.get("geom"), dict) and card["geom"].get("path"):
        extra = f" Geometry: {card['geom']['path']}."
    return line + extra


def _track_label(track: str) -> str:
    labels = {
        "image": "Image track written",
        "script": "Script track written",
        "route": "Route written",
        "preocr": "Pre-OCR darkening written",
        "together": "Script search, then image isolation",
    }
    return labels.get(track, f"{track} written")


def _file_names(files: object) -> list[str]:
    names: list[str] = []
    if isinstance(files, dict):
        for value in files.values():
            if isinstance(value, dict) and value.get("path"):
                names.append(str(value["path"]))
            elif isinstance(value, list):
                for row in value:
                    if isinstance(row, dict) and row.get("path"):
                        names.append(str(row["path"]))
    elif isinstance(files, list):
        for row in files:
            if isinstance(row, dict) and row.get("path"):
                names.append(str(row["path"]))
    return names


def _codes(card: dict) -> list[str]:
    raw = card.get("refuse")
    if raw is None or raw == "" or raw == []:
        return []
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, (list, tuple)):
        return [str(item) for item in raw if item]
    return [str(raw)]


def _refuse_sentence(code: str) -> str:
    text = str(code or "")
    if text == "amoe_as_color":
        return (
            'A lens named "amoe" is refused. Choose tazel, zero, rosetta, or another lens.\n'
            "Try: amoe overlay PAGE.jpg --mode tazel"
        )
    if text == "invent_letter":
        return (
            "Letters that are not in the pixels are refused.\n"
            "Try: amoe lift PAGE.jpg"
        )
    if text == "invent_mark":
        return (
            "Marks that are not in the pixels are refused.\n"
            "Try: amoe lift PAGE.jpg"
        )
    if text == "AMOE-WEAK-SIGNAL":
        return "Weak reading. The page was recorded. Nothing was invented."
    if text == "AMOE-EMPTY-HUE":
        return "Empty in-band hue. The reading was recorded."
    if text == "AMOE-NO-FIGURE":
        return (
            "That path card has no steps.\n"
            "Try: amoe path --card steps.json"
        )
    if text.startswith("AMOE-BAD-STEP:"):
        step = text.split(":", 1)[1]
        return (
            f"Step {step} is outside 1–13.\n"
            "Try: amoe path --card steps.json"
        )
    if text == "AMOE-GATE-MISALIGN":
        return (
            "Step 12 needs gate set to gate or post-gate.\n"
            "Try: amoe path --card steps.json"
        )
    if text == "AMOE-RECONSTRUCT-NOT-NEEDED":
        return "The page still has a clear picture, so it was left as it is."
    if text == "AMOE-RECONSTRUCT-USE-ADAPT":
        return (
            "Reconstruct needs a page picture.\n"
            "Try: amoe adapt PAGE.jpg"
        )
    if text == "AMOE-NO-PAGE":
        return (
            "No picture at that path.\n"
            "Try: amoe overlay PAGE.jpg --mode tazel"
        )
    if text == "AMOE-NOT-PICTURE":
        return (
            "That file is not a PNG or JPEG.\n"
            "Try: amoe overlay PAGE.jpg --mode tazel"
        )
    if text == "AMOE-BAD-JSON":
        return (
            "That card is not JSON.\n"
            "Try: amoe path --card steps.json"
        )
    if text == "AMOE-NO-CARD":
        return (
            "No card file at that path.\n"
            "Try: amoe path --card steps.json"
        )
    if text == "AMOE-BAD-PAINT":
        return "Paint is wheel or engine. Try: amoe paint PAGE.jpg --palette wheel"
    if text == "AMOE-BAD-INDEX":
        return "An index looks like RS=0.5, from 0 to 1. Try: amoe overlay PAGE.jpg --mode tazel --index RS=0.5"
    if text == "SL-UNREDACT-OPAQUE":
        return "The page cover is opaque. Leftover bytes were not invented."
    return text


def _command_from_prog(prog: str) -> str | None:
    parts = str(prog or "").split()
    if len(parts) >= 2:
        return parts[-1]
    return None


def _quoted(text: str) -> str | None:
    if "'" not in text:
        return None
    start = text.find("'")
    end = text.find("'", start + 1)
    if end <= start:
        return None
    return text[start + 1 : end]
