#!/usr/bin/env python3

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "data" / "daodejing"
OUTPUT_DIR = ROOT / "data" / "daodejing_chapters"
CHAPTER_PATTERN = re.compile(r"^\s*(\d+)\s*$")


def trim_outer_blank_lines(lines: list[str]) -> list[str]:
    start = 0
    end = len(lines)

    while start < end and not lines[start].strip():
        start += 1
    while end > start and not lines[end - 1].strip():
        end -= 1

    return lines[start:end]


def parse_chapters(text: str) -> list[tuple[int, str]]:
    chapters: list[tuple[int, str]] = []
    current_number: int | None = None
    current_lines: list[str] = []

    for line in text.splitlines():
        match = CHAPTER_PATTERN.match(line)
        if match:
            if current_number is not None:
                chapter_lines = trim_outer_blank_lines(current_lines)
                chapters.append((current_number, "\n".join(chapter_lines)))
            current_number = int(match.group(1))
            current_lines = []
            continue

        if current_number is not None:
            current_lines.append(line.rstrip())

    if current_number is not None:
        chapter_lines = trim_outer_blank_lines(current_lines)
        chapters.append((current_number, "\n".join(chapter_lines)))

    return chapters


def write_chapters(chapters: list[tuple[int, str]]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for number, text in chapters:
        payload = {
            "chapter": number,
            "source": "Dao De Jing",
            "author": "Lao Zi",
            "text": text,
        }
        output_path = OUTPUT_DIR / f"chapter_{number:03}.json"
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def missing_chapter_numbers(chapters: list[tuple[int, str]]) -> list[int]:
    numbers = [number for number, _text in chapters]
    if not numbers:
        return []
    expected = set(range(min(numbers), max(numbers) + 1))
    return sorted(expected - set(numbers))


def main() -> None:
    source_text = SOURCE_PATH.read_text(encoding="utf-8")
    chapters = parse_chapters(source_text)
    write_chapters(chapters)
    print(f"Wrote {len(chapters)} chapters to {OUTPUT_DIR}")
    missing = missing_chapter_numbers(chapters)
    if missing:
        print(f"Warning: missing numbered chapter markers in source for: {missing}")


if __name__ == "__main__":
    main()
