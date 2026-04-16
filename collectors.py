#!/usr/bin/python3

from __future__ import annotations

import datetime as dt
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

import requests

from config import ROOT
from schema import build_schedule_days, format_schedule_days, sync_public_calendars


@dataclass(frozen=True)
class WallpaperData:
    date_label: str
    weekday_label: str
    update_label: str
    weather_lines: list[str]
    schedule_lines: list[str]
    custom_content: dict[str, str | list[str]]
    reboot_required: bool


def collect_wallpaper_data(config: dict) -> WallpaperData:
    scripts_dir = ROOT / "scripts"

    now = dt.datetime.now()
    date_label = now.strftime("%d/%m/%y")
    weekday_label = now.strftime("%A vecka %V")

    reboot_output = subprocess.check_output([str(scripts_dir / "rebootcheck.sh")], text=True).strip()
    update_label = checkupdate()
    weather_lines = wttr(config["wttr"])
    schedule_lines = collect_schedule_lines(config.get("schedule", {}))
    custom_content = load_custom_content(config.get("custom_content", {}))

    return WallpaperData(
        date_label=date_label,
        weekday_label=weekday_label,
        update_label=update_label,
        weather_lines=weather_lines,
        schedule_lines=schedule_lines,
        custom_content=custom_content,
        reboot_required=reboot_output != "No reboot required.",
    )


def load_custom_content(config: dict) -> dict[str, str | list[str]]:
    merged: dict[str, str | list[str]] = {}
    for source_path in config.get("sources", []):
        path = ROOT / source_path
        if not path.exists():
            continue
        merged.update(_load_custom_content_file(path))
    return merged


def _load_custom_content_file(path: Path) -> dict[str, str | list[str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}

    content: dict[str, str | list[str]] = {}
    for key, value in data.items():
        if isinstance(value, str):
            content[key] = value
        elif isinstance(value, list) and all(isinstance(item, str) for item in value):
            content[key] = value
    return content


def collect_schedule_lines(config: dict) -> list[str]:
    if not config.get("enabled", False):
        return []

    timezone_name = config.get("timezone", "Europe/Stockholm")
    max_lines = config.get("max_lines")

    try:
        if config.get("auto_sync_public", False):
            sync_public_calendars()
        days = build_schedule_days(timezone_name=timezone_name, schedule_config=config)
        lines = format_schedule_days(days, config)
    except Exception as exc:
        error_prefix = config.get("labels", {}).get("error_prefix", "Kalenderfel:")
        first_day_label = config.get("labels", {}).get("day_names", ["Dagens Schema"])[0]
        lines = [f"--- {first_day_label} ---", f"{error_prefix} {exc}"]

    if isinstance(max_lines, int) and max_lines > 0:
        return lines[:max_lines]
    return lines


def checkupdate() -> str:
    try:
        updates = subprocess.check_output(["checkupdates"], text=True)
    except FileNotFoundError:
        return ""
    except subprocess.CalledProcessError:
        return ""

    count = len([line for line in updates.splitlines() if line.strip()])
    return f"Uppdateringar: {count}" if count else ""


def wttr(config: dict) -> list[str]:
    city = config.get("city", "Linkoping")
    hours = config.get("hours", [3, 4, 5, 6])
    property_list = config.get(
        "properties",
        ["time", "tempC", "FeelsLikeC", "chanceofrain", "precipMM", "humidity", "windspeedKmph"],
    )
    transpose_times = config.get("transpose_times", ["09:00", "12:00", "15:00", "18:00"])

    try:
        response = requests.get(f"http://wttr.in/{city}?format=j1", timeout=10)
        response.raise_for_status()
        weather_json = response.json()
    except requests.RequestException:
        return []

    result = [["Desc", "Time", "Temp", "Feels like", "% rain", "Precipitation", "Humidity", "Windspeed"]]
    for hour in hours:
        hourly = weather_json["weather"][0]["hourly"][hour]
        result.append([hourly["weatherDesc"][0]["value"]] + [hourly[prop] for prop in property_list])

    transpose = [list(column) for column in zip(*result)]
    transpose[1] = ["Time"] + transpose_times

    lines = []
    for index in range(1, len(transpose[0])):
        lines.append(
            f"{transpose[0][index]} at {transpose[1][index]}. "
            f"Temp: {transpose[2][index]} Feels like: {transpose[3][index]}. "
            f"%-rain: {transpose[4][index]} rain: {transpose[5][index]}"
        )
    return lines
