#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import random
from datetime import date
from pathlib import Path
from typing import Any

from infopaper.config import ROOT


DEFAULT_CONFIG_PATH = ROOT / "data" / "quotes" / "qotd_config.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def normalize_quote(entry: Any) -> dict[str, str]:
    if isinstance(entry, str):
        return {"text": entry, "author": ""}
    if isinstance(entry, dict):
        return {
            "text": str(entry.get("text", "")).strip(),
            "author": str(entry.get("author", "")).strip(),
        }
    raise TypeError("Quotes must be strings or objects with text/author")


def quote_order(count: int, mode: str) -> list[int]:
    order = list(range(count))
    if mode == "random_no_repeat":
        random.shuffle(order)
        return order
    if mode == "in_order_no_repeat":
        return order
    raise ValueError(f"Unsupported qotd mode: {mode}")


def select_quote(config: dict[str, Any], force_next: bool = False) -> tuple[dict[str, str], dict[str, Any]]:
    quotes_path = ROOT / config["quotes_path"]
    state_path = ROOT / config["state_path"]
    mode = config.get("mode", "random_no_repeat")
    today = date.today().isoformat()

    quotes_data = load_json(quotes_path)
    if not isinstance(quotes_data, list) or not quotes_data:
        raise ValueError("Quote file must contain a non-empty list")
    quotes = [normalize_quote(entry) for entry in quotes_data]

    if state_path.exists():
        state = load_json(state_path)
        if not isinstance(state, dict):
            state = {}
    else:
        state = {}

    current_index = state.get("current_index")
    selected_on = state.get("selected_on")
    remaining = state.get("remaining_indices")

    if (
        not force_next
        and selected_on == today
        and isinstance(current_index, int)
        and 0 <= current_index < len(quotes)
    ):
        return quotes[current_index], state

    if not isinstance(remaining, list) or any(not isinstance(item, int) for item in remaining):
        remaining = quote_order(len(quotes), mode)

    remaining = [index for index in remaining if 0 <= index < len(quotes)]
    if not remaining:
        remaining = quote_order(len(quotes), mode)

    current_index = remaining.pop(0)
    state = {
        "mode": mode,
        "current_index": current_index,
        "selected_on": today,
        "remaining_indices": remaining,
    }
    save_json(state_path, state)
    return quotes[current_index], state


def build_output(config: dict[str, Any], quote: dict[str, str]) -> dict[str, Any]:
    output_keys = config.get(
        "output_keys",
        {
            "quote": "qotd_quote",
            "author": "qotd_author",
            "combined": "qotd_lines",
        },
    )
    include_author = config.get("include_author", True)
    author_prefix = config.get("author_prefix", "— ")

    result: dict[str, Any] = {
        output_keys["quote"]: quote["text"],
    }

    lines = [quote["text"]]
    if include_author and quote["author"]:
        author_line = f"{author_prefix}{quote['author']}"
        result[output_keys["author"]] = author_line
        lines.append(author_line)

    result[output_keys["combined"]] = lines
    return result


def run(config_path: Path, force_next: bool = False) -> Path:
    config = load_json(config_path)
    if not isinstance(config, dict):
        raise ValueError("qotd config must be a JSON object")

    quote, _state = select_quote(config, force_next=force_next)
    output = build_output(config, quote)
    output_path = ROOT / config["output_path"]
    save_json(output_path, output)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate quote-of-the-day JSON output")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Path to qotd config JSON")
    parser.add_argument("--force-next", action="store_true", help="Advance to the next quote even if already selected today")
    args = parser.parse_args()

    output_path = run(Path(args.config), force_next=args.force_next)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
