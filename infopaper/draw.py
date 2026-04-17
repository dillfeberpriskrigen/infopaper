#!/usr/bin/python3

from __future__ import annotations

import calendar
import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from infopaper.colors import colors
from infopaper.config import ROOT


RESOURCES_DIR = ROOT / "resources"
DEFAULT_BACKGROUND = RESOURCES_DIR / "background.png"


def dimensions(wallpaper: Path | str = DEFAULT_BACKGROUND) -> tuple[int, int]:
    image = Image.open(wallpaper)
    return image.size


def load_base_image(wallpaper: Path | str = DEFAULT_BACKGROUND) -> Image.Image:
    return Image.open(wallpaper).copy()


def load_font(font_name: str, fontsize: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(RESOURCES_DIR / font_name), fontsize)


def longest_text(image: Image.Image, textlist: list[str], font_name: str, fontsize: int) -> tuple[int, int]:
    font = load_font(font_name, fontsize)
    draw = ImageDraw.Draw(image)
    largest_x = 0
    largest_y = 0

    for entry in textlist:
        left, top, right, bottom = draw.textbbox((0, 0), entry, font)
        largest_x = max(largest_x, right - left)
        largest_y = max(largest_y, bottom - top)

    return largest_x, largest_y


def draw_text(
    image: Image.Image,
    content: str,
    x: float,
    y: float,
    color,
    font_name: str,
    fontsize: int = 65,
    rightalign: int = 0,
    heightalign: int = 0,
) -> None:
    w, h = image.size
    if rightalign:
        x = w - rightalign - (x - w)

    font = load_font(font_name, fontsize)
    draw = ImageDraw.Draw(image)
    left, top, right, bottom = draw.textbbox((0, 0), content, font)
    text_width = right - left
    text_height = bottom - top

    if x + text_width > w:
        x = w - text_width - 65
    if y + text_height > h:
        y -= text_height

    draw.text((x, y + heightalign), str(content), font=font, fill=color)


def draw_text_lines(
    image: Image.Image,
    lines: list[str],
    x: float,
    y: float,
    color,
    font_name: str,
    fontsize: int,
    line_spacing: int = 0,
    rightalign: int = 0,
) -> None:
    for index, line in enumerate(lines):
        draw_text(
            image,
            line,
            x,
            y + (line_spacing * index),
            color,
            font_name,
            fontsize,
            rightalign,
        )


def draw_calendar(image: Image.Image, posx: float = 200, posy: float = 200, fontsize: int = 20, color=colors[2]) -> None:
    today = datetime.date.today()
    day = int(today.strftime("%d"))
    fontwidth = fontsize * 1.83
    fontheight = fontsize * 1.15

    ascii_calendar = calendar.month(today.year, today.month)
    weekday_number = today.weekday()
    day_with_offset = day + datetime.date(today.year, today.month, 1).weekday() - 1
    weeknum = int(day_with_offset / 7) if day_with_offset > 7 else 0
    weeknum += 2

    draw = ImageDraw.Draw(image)
    x_marker = posx + (fontwidth * weekday_number)
    y_marker = posy + fontheight * weeknum

    shape = [
        (x_marker - 2, y_marker - 2),
        (x_marker + fontsize + 2, y_marker + fontsize + 2),
    ]

    font = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSansMono.ttf", fontsize)
    draw.rounded_rectangle(shape)
    draw.text((posx, posy), str(ascii_calendar), font=font, fill=color)
