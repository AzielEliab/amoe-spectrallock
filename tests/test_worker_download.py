"""The download tracker serves the 1.3.0 source package and counts branches and forks."""

from __future__ import annotations

import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "workers" / "download-tracker" / "public" / "amoe-spectrallock-1.3.0.tar.gz"
VERIFY = ROOT / "workers" / "download-tracker" / "scripts" / "verify-download.mjs"


def test_asset_is_gzip_of_this_tree() -> None:
    assert ASSET.is_file()
    with tarfile.open(ASSET, "r:gz") as tar:
        names = tar.getnames()
        assert "amoe-spectrallock-1.3.0/pyproject.toml" in names
        assert "amoe-spectrallock-1.3.0/amoe/__init__.py" in names
        assert "amoe-spectrallock-1.3.0/catalog.json" in names
        text = tar.extractfile("amoe-spectrallock-1.3.0/pyproject.toml").read().decode()
        assert 'version = "1.3.0"' in text
        init = tar.extractfile("amoe-spectrallock-1.3.0/amoe/__init__.py").read().decode()
        assert '__version__ = "1.3.0"' in init
        packed = [name for name in names if name.endswith(".tar.gz")]
        assert packed == []


def test_tracker_counts_downloads_across_branches_and_forks() -> None:
    proc = subprocess.run(
        ["node", str(VERIFY)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
