#!/usr/bin/python3

from __future__ import annotations

import shutil
import subprocess

from infopaper.collectors import collect_wallpaper_data
from infopaper.config import load_config, load_layout
from infopaper.renderer import render_wallpaper


def apply_wallpaper(setter_command: list[str], output_path: str) -> None:
    if not setter_command:
        return

    executable = setter_command[0]
    if shutil.which(executable) is None:
        raise FileNotFoundError(f"Wallpaper setter not found: {executable}")

    subprocess.run([*setter_command, output_path], check=True)


def main() -> None:
    config = load_config()
    layout = load_layout()
    output_path = render_wallpaper(collect_wallpaper_data(config), config, layout)

    files = config["files"]
    apply_wallpaper(files.get("wallpaper_setter", []), str(output_path))


if __name__ == "__main__":
    main()
