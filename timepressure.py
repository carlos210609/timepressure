#!/usr/bin/env python3
"""TimePressure zero-setup CLI launcher. No GUI or Tkinter required."""
from __future__ import annotations
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

REQUIREMENTS = ["PyJWT[crypto]>=2.10,<3", "playwright>=1.50,<2"]


def _run(cmd):
    print("\n[TimePressure] $ " + " ".join(cmd), flush=True)
    return subprocess.run(cmd, check=True)


def _ensure_pip():
    if importlib.util.find_spec("pip") is not None:
        return True
    print("[TimePressure] pip is missing; bootstrapping with ensurepip...", flush=True)
    try:
        _run([sys.executable, "-m", "ensurepip", "--upgrade", "--user"])
    except subprocess.CalledProcessError:
        try:
            _run([sys.executable, "-m", "ensurepip", "--upgrade"])
        except subprocess.CalledProcessError:
            return False
    return importlib.util.find_spec("pip") is not None


def _pip_install():
    if not _ensure_pip():
        raise RuntimeError(
            "Python pip is unavailable and ensurepip is disabled. "
            "Install the OS package python3-pip, then rerun TimePressure."
        )
    missing = []
    if importlib.util.find_spec("jwt") is None:
        missing.append(REQUIREMENTS[0])
    if importlib.util.find_spec("playwright") is None:
        missing.append(REQUIREMENTS[1])
    if not missing:
        return
    print("[TimePressure] Installing Python dependencies...", flush=True)
    try:
        _run([sys.executable, "-m", "pip", "install", "--user", *missing])
    except subprocess.CalledProcessError:
        _run([sys.executable, "-m", "pip", "install", "--break-system-packages", *missing])


def _ensure_chromium():
    if importlib.util.find_spec("playwright") is None:
        return
    marker = Path(os.getenv("TIMEPRESSURE_DATA_DIR", ".data")) / ".chromium-ready"
    if marker.exists():
        return
    print("[TimePressure] Installing Playwright Chromium (first run)...", flush=True)
    _run([sys.executable, "-m", "playwright", "install", "chromium"])
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("installed\n")


if __name__ == "__main__":
    _pip_install()
    _ensure_chromium()
    if len(sys.argv) > 1 and sys.argv[1] == "start":
        from timepressure.cli import main
        raise SystemExit(main(["start", *sys.argv[2:]]))
    if len(sys.argv) > 1 and sys.argv[1] == "marketplaces":
        from marketplace_runner import main as marketplace_main
        raise SystemExit(marketplace_main(sys.argv[2:]))
    from timepressure.cli import main
    raise SystemExit(main())
