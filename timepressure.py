#!/usr/bin/env python3
"""
TimePressure zero-setup launcher.

After cloning:
    cd timepressure
    python3 timepressure.py

The first run installs the Python dependencies and Playwright Chromium.
No virtual environment, Node.js or npm is required.
"""
from __future__ import annotations

import importlib.util
import os
import platform
import subprocess
import sys
from pathlib import Path

REQUIREMENTS = [
    "PyJWT[crypto]>=2.10,<3",
    "playwright>=1.50,<2",
]


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess:
    print("\n[TimePressure] $ " + " ".join(cmd), flush=True)
    return subprocess.run(cmd, check=check)


def _pip_install() -> None:
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
        # Some managed Linux installations reject user installs. The user
        # explicitly chose a no-venv setup, so offer the system-pip fallback.
        _run([
            sys.executable, "-m", "pip", "install",
            "--break-system-packages", *missing,
        ])


def _ensure_tkinter() -> None:
    if importlib.util.find_spec("tkinter") is not None:
        return

    if platform.system() == "Linux":
        print("[TimePressure] Tkinter is missing; attempting python3-tk...", flush=True)
        prefix = [] if os.geteuid() == 0 else ["sudo"]
        try:
            _run(prefix + ["apt-get", "update"])
            _run(prefix + ["apt-get", "install", "-y", "python3-tk"])
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            raise SystemExit(
                "Could not install Tkinter automatically. On Debian/Ubuntu/Mint run: "
                "sudo apt install python3-tk"
            ) from exc
        if importlib.util.find_spec("tkinter") is None:
            raise SystemExit("Tkinter is still unavailable after installation.")
        return

    raise SystemExit(
        "Tkinter is not available in this Python installation. "
        "Install the platform's Tk support and run again."
    )


def _ensure_chromium() -> None:
    if importlib.util.find_spec("playwright") is None:
        return

    marker = Path(os.getenv("TIMEPRESSURE_DATA_DIR", ".data")) / ".chromium-ready"
    if marker.exists():
        return

    print("[TimePressure] Installing Playwright Chromium (first run)...", flush=True)
    try:
        _run([sys.executable, "-m", "playwright", "install", "chromium"])
    except subprocess.CalledProcessError as exc:
        raise SystemExit(
            "Could not install Playwright Chromium automatically. "
            "Check your internet connection and run again."
        ) from exc

    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("installed\n")


def bootstrap() -> None:
    _pip_install()
    _ensure_tkinter()
    _ensure_chromium()


if __name__ == "__main__":
    bootstrap()
    from timepressure.cli import main
    raise SystemExit(main())
