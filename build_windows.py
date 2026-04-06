r"""Build Snake Legends for Windows with PyInstaller.

Usage:
    .\.venv\Scripts\python.exe build_windows.py
    .\.venv\Scripts\python.exe build_windows.py --onefile
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import PyInstaller.__main__
from PyInstaller.utils.hooks import collect_submodules


PROJECT_ROOT = Path(__file__).resolve().parent
GAME_DIR = PROJECT_ROOT / "snake_game"
ENTRY_FILE = GAME_DIR / "main.py"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
SPEC_FILE = PROJECT_ROOT / "SnakeLegends.spec"

if str(GAME_DIR) not in sys.path:
    sys.path.insert(0, str(GAME_DIR))


def _add_data(source: Path, target: str) -> str:
    return f"{source}{';'}{target}"


def build(onefile: bool = False) -> None:
    hidden_imports = sorted(
        set(
            collect_submodules("systems")
            + collect_submodules("entities")
            + collect_submodules("utils")
        )
    )

    args = [
        str(ENTRY_FILE),
        "--noconfirm",
        "--clean",
        "--name",
        "SnakeLegends",
        "--paths",
        str(GAME_DIR),
        "--distpath",
        str(DIST_DIR),
        "--workpath",
        str(BUILD_DIR),
        "--specpath",
        str(PROJECT_ROOT),
        "--windowed",
        "--collect-all",
        "pygame",
        "--add-data",
        _add_data(GAME_DIR / "assets", "assets"),
        "--add-data",
        _add_data(GAME_DIR / "data", "data"),
    ]

    if onefile:
        args.append("--onefile")

    for module_name in hidden_imports:
        args.extend(["--hidden-import", module_name])

    PyInstaller.__main__.run(args)


def clean() -> None:
    for path in (DIST_DIR, BUILD_DIR, SPEC_FILE):
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        elif path.exists():
            path.unlink()


def main() -> None:
    onefile = "--onefile" in sys.argv[1:]
    clean()
    build(onefile=onefile)


if __name__ == "__main__":
    main()
