A collection of scripts that renders useful daily info onto a wallpaper image and sets it as the desktop background.

It has been reliable enough for personal use, but the codebase still reflects its proof-of-concept origins. This repository is now being cleaned up so the project is easier to maintain, reason about, and extend.

The current structure is split into three main parts:

- `infopaper/collectors.py` gathers external data
- `infopaper/renderer.py` turns that data into a wallpaper image
- `main.py` coordinates the run and applies the finished wallpaper

Reusable application code now lives in the `infopaper/` package. Runnable helper tools live in `scripts/`. Keeping `scripts/` plural is the conventional naming, and it makes the intent a bit clearer than `script/`.

Layout is now stored separately in `layout.json`, so positioning and sizing can evolve independently from runtime behavior in `config.json`.

Current features:

- Render date and week number onto an image
- Fetch a short weather summary from `wttr.in`
- Check whether the system kernel requires a reboot
- Draw the current month calendar and highlight today
- Optionally parse schedule data from an `.ics` file

Current rough edges:

- Layout and font tuning are still mostly hardcoded
- Some behavior is Linux and Arch specific
- External commands are still used for a few system integrations
- Configuration is local-file driven rather than validated

The reboot check is signal-based rather than message-based. `scripts/rebootcheck.sh` exits with `0` for `ok`, `1` for `reboot`, and `2` for `unknown`. `infopaper` maps that status to text in `layout.json`, so the script does not need to print user-facing strings.

Dependencies:

- `Pillow`
- `requests`
- `icalendar`


Expected local files:

- `config.json`
- `layout.json`
- `calendars.json`
- `data/custom/*.json`
- `resources/background.png`
- `resources/DejaVuSans-Bold.ttf`

Run:

```bash
python3 main.py
```

Layout editor:

```bash
python3 scripts/placer.py
```

Calendar sync:

```bash
python3 scripts/sync_calendars.py
python3 scripts/schema.py
```

Quote of the day:

```bash
python3 scripts/qotd.py
```

Wallpaper setter configuration lives in `config.json` as a command list, for example:

```json
"wallpaper_setter": ["feh", "--bg-max"]
```

This keeps wallpaper application user-configurable without using shell execution. If you prefer to only render the image and not auto-apply it, set:

```json
"wallpaper_setter": []
```

Custom script output is configured in `config.json` under `custom_content.sources`. The app reads those JSON files, merges their keys into the collected content, and draws any keys that also exist in `layout.json`.

Schedule rendering is configured in `config.json` under `schedule`, including whether the block is enabled, which timezone to use, whether public subscriptions should be synced automatically, how many schedule lines should be shown on the wallpaper, how many lines `scripts/placer.py` should preview, and the `strftime` time format used for event times.

`layout.json` controls where objects are drawn. It currently supports relative placement modes such as `from_right_fraction` and `from_bottom_fraction`, plus per-block font size, color, visibility, and weather line spacing.
Dragging an object in `scripts/placer.py` saves that block back as an absolute position so the editor can place it directly.
The reboot text block can use `content` as the default reboot message, plus optional `ok_content`, `unknown_content`, or a `content_by_status` map like this:

```json
"reboot": {
  "x": { "mode": "from_left_fraction", "value": 16, "margin": 0 },
  "y": { "mode": "from_bottom_fraction", "value": 15, "margin": 0 },
  "font": "DejaVuSans-Bold.ttf",
  "fontsize": 20,
  "color": 2,
  "content": "Reboot required",
  "content_by_status": {
    "ok": "",
    "reboot": "Reboot required",
    "unknown": "Reboot status unknown"
  },
  "visible": true
}
```

`calendars.json` controls schedule subscriptions. You can point a source at a local ICS file with `local_path`, or at a public ICS URL with `slug` and `url`. Public calendars are downloaded into `data/calendars/` and then read by `scripts/schema.py`.

For custom content, a script can write JSON like this:

```json
{
  "hello_world": "Hello world from JSON",
  "custom_lines": ["First custom line", "Second custom line"]
}
```

If `layout.json` contains matching keys like `hello_world` or `custom_lines`, they will be rendered automatically. The app never executes those scripts itself; it only reads their JSON output.

Minimal example:

1. Make a script write `data/custom/example_blocks.json`:

```json
{
  "hello_world": "Hello world from JSON"
}
```

2. Point `config.json` at that file:

```json
"custom_content": {
  "sources": [
    "data/custom/example_blocks.json"
  ]
}
```

3. Add a matching key to `layout.json`:

```json
"hello_world": {
  "x": { "mode": "absolute", "value": 120 },
  "y": { "mode": "absolute", "value": 120 },
  "font": "DejaVuSans-Bold.ttf",
  "fontsize": 20,
  "color": 5,
  "visible": true
}
```

After that, `python3 main.py` will render the value from the JSON file at the position defined in `layout.json`.

Quote-of-the-day example:

1. Put quotes in `data/quotes/qotd_quotes.json`.
2. Configure selection mode and output in `data/quotes/qotd_config.json`.
3. Run:

```bash
python3 scripts/qotd.py
```

That writes `data/custom/qotd.json`, which is already listed in `config.json` as a custom content source. Matching layout keys such as `qotd_quote`, `qotd_author`, or `qotd_lines` can then be enabled in `layout.json`.

`qotd_lines` is set up for adaptive rendering. If you enable it in `layout.json`, the renderer will wrap the quote text inside its configured `box.width` and `box.height`, and reduce the font size down to `min_fontsize` until it fits.

`scripts/qotd.py` remembers the selected quote in `data/quotes/qotd_state.json`. It supports:

- `random_no_repeat`: random order without repeating until the pool is exhausted
- `in_order_no_repeat`: quote 1, then 2, then 3, looping only after all quotes were used

If you rerun it on the same day, it keeps the same quote unless you pass `--force-next`.

Suggested next refactors:

1. Move config loading to a typed config object with validation and defaults.
2. Replace shell-based integrations with safer Python implementations where practical.
3. Add a minimal test suite around layout helpers and data formatting.
4. Feed the new schedule subscriptions into the wallpaper renderer once the schedule block layout is ready.
