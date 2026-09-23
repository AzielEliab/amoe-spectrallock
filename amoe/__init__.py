"""AMOE-1.3 — wiring on every cell of the SpectralLock color grid.

AMOE is not a field and not a color. There is no twelfth lens named AMOE
and AMOE is not an alias of Rosetta. Pigment restore stays a SpectralLock
product door. The human still reads the page.

Author: Aziel Eliab.
"""

from __future__ import annotations

import sys
from pathlib import Path

__version__ = "1.3.0"
__paper__ = "AMOE-1.3"
__author__ = "Aziel Eliab"

__all__ = [
    "__author__",
    "__paper__",
    "__version__",
    "AmoeError",
    "ensure_vendor",
    "package_root",
    "vendor_root",
]


class AmoeError(Exception):
    """A named AMOE refuse. Valid readings still return a card; this is for hard refuses."""

    def __init__(self, code: str, **extra: object) -> None:
        self.code = code
        self.extra = extra
        super().__init__(code)


def package_root() -> Path:
    return Path(__file__).resolve().parents[1]


def vendor_root() -> Path:
    return package_root() / "vendor"


def ensure_vendor() -> None:
    """Prefer the vendored SpectralLock 0.3.1 tree over any other install."""
    vendor = vendor_root()
    if vendor.is_dir():
        entry = str(vendor)
        if entry not in sys.path:
            sys.path.insert(0, entry)
