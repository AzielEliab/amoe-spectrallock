"""Install check for the local AMOE package. No network. No score.

Author: Aziel Eliab.
"""

from __future__ import annotations

import json

from amoe import __author__, __paper__, __version__, ensure_vendor, package_root


def doctor_card() -> dict:
    checks: list[dict[str, object]] = []

    try:
        import numpy as np

        checks.append({"name": "numpy", "ok": True, "detail": np.__version__})
    except Exception as exc:  # noqa: BLE001
        checks.append({"name": "numpy", "ok": False, "detail": type(exc).__name__})

    try:
        import PIL

        checks.append({"name": "Pillow", "ok": True, "detail": PIL.__version__})
    except Exception as exc:  # noqa: BLE001
        checks.append({"name": "Pillow", "ok": False, "detail": type(exc).__name__})

    try:
        ensure_vendor()
        import spectrallock

        version_ok = spectrallock.__version__ == "0.3.1"
        author_ok = spectrallock.__author__ == __author__
        checks.append(
            {
                "name": "SpectralLock",
                "ok": bool(version_ok and author_ok),
                "detail": f"{spectrallock.__version__} · {spectrallock.__author__}",
            }
        )
    except Exception as exc:  # noqa: BLE001
        checks.append({"name": "SpectralLock", "ok": False, "detail": type(exc).__name__})

    catalog_path = package_root() / "catalog.json"
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        ok = (
            catalog.get("slug") == "amoe"
            and catalog.get("amoe_is_wiring") is True
            and catalog.get("pigment_recovery") is False
            and catalog.get("author") == __author__
        )
        checks.append(
            {
                "name": "catalog",
                "ok": bool(ok),
                "detail": f"{catalog.get('version')} · {catalog.get('depends')}",
            }
        )
    except Exception as exc:  # noqa: BLE001
        checks.append({"name": "catalog", "ok": False, "detail": type(exc).__name__})

    return {
        "product": "amoe",
        "version": __version__,
        "paper": __paper__,
        "author": __author__,
        "amoe_is_field": False,
        "amoe_is_wiring": True,
        "pigment_recovery": False,
        "invent_letters": False,
        "ok": all(bool(item.get("ok")) for item in checks),
        "checks": checks,
        "telemetry": False,
        "loopback_ui": "127.0.0.1:8871",
    }
