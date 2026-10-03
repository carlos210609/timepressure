#!/usr/bin/env python3
"""
TimePressure zero-setup launcher.

After cloning the repository, run:
    python3 timepressure.py

It installs the Python dependencies and Playwright Chromium on first run.
No virtual environment, Node.js or npm is required.
"""
from __future__ import annotations

import importlib.util
import os
import platform
import subprocess
import sys


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

    print("[TimePressure] Instalando dependências automaticamente...", flush=True)
    base = [sys.executable, "-m", "pip", "install", *missing]
    try:
        _run(base)
    except subprocess.CalledProcessError:
        # Useful on Linux distributions with a system-managed Python.
        if platform.system() == "Linux":
            _run([sys.executable, "-m", "pip", "install", "--user", *missing])
        else:
            raise


def _ensure_tkinter() -> None:
    if importlib.util.find_spec("tkinter") is not None:
        return

    if platform.system() == "Linux":
        print("[TimePressure] Tkinter não encontrado. Tentando instalar python3-tk...", flush=True)
        sudo = "sudo" if os.geteuid() != 0 else ""
        cmd = ([sudo] if sudo else []) + ["apt-get", "update"]
        try:
            _run(cmd)
            cmd = ([sudo] if sudo else []) + ["apt-get", "install", "-y", "python3-tk"]
            _run(cmd)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise SystemExit(
                "Tkinter não pôde ser instalado automaticamente. "
                "Em Debian/Ubuntu/Mint, execute: sudo apt install python3-tk"
            )
        if importlib.util.find_spec("tkinter") is None:
            raise SystemExit("Tkinter continua indisponível após a instalação.")
        return

    raise SystemExit(
        "Tkinter não está disponível neste Python. Instale o suporte Tk da sua distribuição "
        "e execute novamente."
    )


def _ensure_chromium() -> None:
    if importlib.util.find_spec("playwright") is None:
        return

    marker = os.path.join(os.path.expanduser("~"), ".cache", "ms-playwright")
    # Avoid downloading Chromium on every launch. Playwright itself decides whether
    # a browser executable is available; this command is cheap when already installed.
    try:
        _run([sys.executable, "-m", "playwright", "install", "chromium"])
    except subprocess.CalledProcessError as exc:
        raise SystemExit(
            "Não foi possível instalar o Chromium do Playwright automaticamente. "
            "Verifique sua conexão com a internet e execute novamente."
        ) from exc


def bootstrap() -> None:
    _pip_install()
    _ensure_tkinter()
    _ensure_chromium()


if __name__ == "__main__":
    bootstrap()
    from timepressure.cli import main
    raise SystemExit(main())
