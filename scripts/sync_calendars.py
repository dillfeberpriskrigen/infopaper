#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from infopaper.schema import sync_public_calendars


def main() -> None:
    synced_paths = sync_public_calendars()
    if not synced_paths:
        print("No enabled public calendar subscriptions were synced.")
        return

    for path in synced_paths:
        print(f"Synced {path}")


if __name__ == "__main__":
    main()
