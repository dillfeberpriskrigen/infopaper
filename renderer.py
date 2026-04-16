#!/usr/bin/python3

from __future__ import annotations

from pathlib import Path
from typing import Any

from adaptiverendering import draw_adaptive_text_block
from collectors import WallpaperData
from colors import colors
from config import ROOT
from draw import draw_calendar, draw_text, draw_text_lines, load_base_image, longest_text


def _resolve_color(color_value: Any):
    if isinstance(color_value, int):
        return colors[color_value]
    if isinstance(color_value, list) and len(color_value) == 3:
        return tuple(color_value)
    raise ValueError(f"Unsupported color value in layout.json: {color_value}")


def _resolve_x(position: dict[str, Any], width: int) -> float:
    mode = position.get("mode", "absolute")
    value = position.get("value", 0)
    margin = position.get("margin", 0)

    if mode == "absolute":
        return value
    if mode == "from_right_fraction":
        return width - (width / value) - margin
    if mode == "from_left_fraction":
        return width / value + margin
    if mode == "fraction":
        return width * value
    raise ValueError(f"Unsupported x position mode: {mode}")


def _resolve_y(position: dict[str, Any], height: int) -> float:
    mode = position.get("mode", "absolute")
    value = position.get("value", 0)
    margin = position.get("margin", 0)

    if mode == "absolute":
        return value
    if mode == "from_bottom_fraction":
        return height - (height / value) - margin
    if mode == "from_top_fraction":
        return height / value + margin
    if mode == "fraction":
        return height * value
    raise ValueError(f"Unsupported y position mode: {mode}")


def _draw_layout_text(image, content: str, block: dict[str, Any], files: dict[str, Any], rightalign: int = 0) -> None:
    x = _resolve_x(block["x"], image.size[0])
    y = _resolve_y(block["y"], image.size[1])
    draw_text(
        image,
        content,
        x,
        y,
        _resolve_color(block["color"]),
        block.get("font", files["font"]),
        block.get("fontsize", files["fontsize_normal"]),
        rightalign if block.get("use_rightalign", False) else 0,
    )


def _draw_layout_text_lines(
    image,
    lines: list[str],
    block: dict[str, Any],
    files: dict[str, Any],
    rightalign: int = 0,
) -> None:
    x = _resolve_x(block["x"], image.size[0])
    y = _resolve_y(block["y"], image.size[1])
    draw_text_lines(
        image,
        lines,
        x,
        y,
        _resolve_color(block["color"]),
        block.get("font", files["font"]),
        block.get("fontsize", files["fontsize_normal"]),
        block.get("line_spacing", 0),
        rightalign if block.get("use_rightalign", False) else 0,
    )


def _draw_custom_content(
    image,
    custom_content: dict[str, str | list[str]],
    layout: dict[str, Any],
    files: dict[str, Any],
) -> None:
    reserved_keys = {"text", "weather", "schedule", "calendar"}
    for key, content in custom_content.items():
        if key in reserved_keys or key not in layout:
            continue

        block = layout[key]
        if not isinstance(block, dict) or not block.get("visible", True):
            continue

        if block.get("render_mode") == "adaptive":
            draw_adaptive_text_block(
                image,
                content,
                block,
                _resolve_color(block["color"]),
                files["font"],
                files["fontsize_normal"],
            )
        elif isinstance(content, list):
            _draw_layout_text_lines(image, content, block, files)
        else:
            _draw_layout_text(image, content, block, files)


def _resolve_reboot_content(block: dict[str, Any], status: str) -> str:
    status_content = block.get("content_by_status", {})
    if isinstance(status_content, dict):
        content = status_content.get(status)
        if isinstance(content, str):
            return content

    if status == "reboot":
        return block.get("content", "Reboot required")
    if status == "unknown":
        return block.get("unknown_content", "")
    return block.get("ok_content", "")


def render_wallpaper(data: WallpaperData, config: dict, layout: dict) -> Path:
    files = config["files"]
    background_path = ROOT / files["infile_path"]
    output_path = ROOT / files["outfile_path"]
    image = load_base_image(background_path)

    text_blocks = layout["text"]
    weather_block = layout["weather"]
    schedule_block = layout.get("schedule", {})
    calendar_block = layout["calendar"]

    textlist = [data.date_label, data.weekday_label]
    if data.update_label:
        textlist.append(data.update_label)

    rightalign, _ = longest_text(
        image,
        textlist,
        text_blocks["date"].get("font", files["font"]),
        text_blocks["date"].get("fontsize", files["fontsize_big"]),
    )

    _draw_layout_text(image, data.date_label, text_blocks["date"], files, rightalign)
    _draw_layout_text(image, data.weekday_label, text_blocks["weekday"], files, rightalign)

    if data.update_label and text_blocks["updates"].get("visible", True):
        _draw_layout_text(image, data.update_label, text_blocks["updates"], files, rightalign)

    if weather_block.get("visible", True):
        _draw_layout_text_lines(image, data.weather_lines, weather_block, files, rightalign)

    if schedule_block.get("visible", True):
        _draw_layout_text_lines(image, data.schedule_lines, schedule_block, files)

    if text_blocks["reboot"].get("visible", True):
        reboot_content = _resolve_reboot_content(text_blocks["reboot"], data.reboot_status)
        if reboot_content:
            _draw_layout_text(image, reboot_content, text_blocks["reboot"], files)

    if calendar_block.get("visible", True):
        draw_calendar(
            image,
            _resolve_x(calendar_block["x"], image.size[0]),
            _resolve_y(calendar_block["y"], image.size[1]),
            calendar_block.get("fontsize", files["fontsize_small"]),
            _resolve_color(calendar_block["color"]),
        )

    _draw_custom_content(image, data.custom_content, layout, files)

    image.save(output_path)
    return output_path
