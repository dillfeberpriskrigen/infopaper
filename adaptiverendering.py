#!/usr/bin/python3

from __future__ import annotations

from typing import Any

from PIL import Image, ImageDraw

from draw import load_font


def _as_paragraphs(content: str | list[str]) -> list[str]:
    if isinstance(content, list):
        return [str(line).strip() for line in content if str(line).strip()]
    return [part.strip() for part in str(content).splitlines() if part.strip()] or [str(content)]


def _wrap_line(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]

    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        left, top, right, bottom = draw.textbbox((0, 0), candidate, font=font)
        if right - left <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _wrap_paragraphs(draw: ImageDraw.ImageDraw, paragraphs: list[str], font, max_width: int) -> list[str]:
    wrapped: list[str] = []
    for paragraph in paragraphs:
        wrapped.extend(_wrap_line(draw, paragraph, font, max_width))
    return wrapped


def _measure_lines(draw: ImageDraw.ImageDraw, lines: list[str], font, line_spacing: int) -> tuple[int, int]:
    max_width = 0
    total_height = 0

    for index, line in enumerate(lines):
        left, top, right, bottom = draw.textbbox((0, 0), line, font=font)
        max_width = max(max_width, right - left)
        total_height += bottom - top
        if index < len(lines) - 1:
            total_height += line_spacing

    return max_width, total_height


def draw_adaptive_text_block(
    image: Image.Image,
    content: str | list[str],
    block: dict[str, Any],
    color,
    default_font: str,
    default_fontsize: int,
) -> None:
    box = block.get("box", {})
    max_width = int(box.get("width", 0))
    max_height = int(box.get("height", 0))
    if max_width <= 0 or max_height <= 0:
        return

    x = int(block["x"]["value"])
    y = int(block["y"]["value"])
    font_name = block.get("font", default_font)
    max_fontsize = int(block.get("fontsize", default_fontsize))
    min_fontsize = int(block.get("min_fontsize", 12))
    line_spacing_ratio = float(block.get("line_spacing_ratio", 0.25))
    align = block.get("text_align", "left")

    draw = ImageDraw.Draw(image)
    paragraphs = _as_paragraphs(content)

    fitted_lines = paragraphs
    fitted_font = load_font(font_name, min_fontsize)
    fitted_spacing = 0

    for fontsize in range(max_fontsize, min_fontsize - 1, -1):
        font = load_font(font_name, fontsize)
        line_spacing = int(fontsize * line_spacing_ratio)
        lines = _wrap_paragraphs(draw, paragraphs, font, max_width)
        width, height = _measure_lines(draw, lines, font, line_spacing)
        if width <= max_width and height <= max_height:
            fitted_lines = lines
            fitted_font = font
            fitted_spacing = line_spacing
            break
    else:
        fitted_lines = _wrap_paragraphs(draw, paragraphs, fitted_font, max_width)
        fitted_spacing = int(min_fontsize * line_spacing_ratio)

    current_y = y
    for index, line in enumerate(fitted_lines):
        left, top, right, bottom = draw.textbbox((0, 0), line, font=fitted_font)
        line_width = right - left
        if align == "center":
            line_x = x + max((max_width - line_width) // 2, 0)
        elif align == "right":
            line_x = x + max_width - line_width
        else:
            line_x = x

        draw.text((line_x, current_y), line, font=fitted_font, fill=color)
        current_y += (bottom - top) + fitted_spacing
