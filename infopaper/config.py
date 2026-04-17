#!/usr/bin/python3

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config.json"
LAYOUT_PATH = ROOT / "layout.json"
CALENDARS_PATH = ROOT / "calendars.json"


def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
        return json.load(config_file)


def load_layout() -> dict[str, Any]:
    with LAYOUT_PATH.open("r", encoding="utf-8") as layout_file:
        return json.load(layout_file)


def load_calendar_sources() -> list[dict[str, Any]]:
    if not CALENDARS_PATH.exists():
        return []

    with CALENDARS_PATH.open("r", encoding="utf-8") as calendars_file:
        data = json.load(calendars_file)

    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("sources", [])
    raise TypeError("calendars.json must be a list or an object with a 'sources' key")
