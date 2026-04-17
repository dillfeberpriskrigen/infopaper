#!/usr/bin/python3

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
from icalendar import Calendar
from zoneinfo import ZoneInfo

from infopaper.config import ROOT, load_calendar_sources, load_config


CALENDAR_CACHE_DIR = ROOT / "data" / "calendars"
LEGACY_SCHEMA_PATH = ROOT / "schema.ics"


@dataclass(frozen=True)
class ScheduleEvent:
    start: dt.datetime
    end: dt.datetime
    all_day: bool
    summary: str
    location: str
    description_lines: list[str]


@dataclass(frozen=True)
class ScheduleDay:
    label: str
    date: dt.date
    events: list[ScheduleEvent]


def sync_public_calendars(sources: list[dict[str, Any]] | None = None) -> list[Path]:
    sources = sources if sources is not None else load_calendar_sources()
    CALENDAR_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    synced_paths: list[Path] = []

    for source in sources:
        url = source.get("url")
        slug = source.get("slug")
        enabled = source.get("enabled", True)
        if not enabled or not url or not slug:
            continue

        response = requests.get(url, timeout=20)
        response.raise_for_status()
        target_path = CALENDAR_CACHE_DIR / f"{slug}.ics"
        target_path.write_bytes(response.content)
        synced_paths.append(target_path)

    return synced_paths


def calendar_source_paths(sources: list[dict[str, Any]] | None = None) -> list[Path]:
    sources = sources if sources is not None else load_calendar_sources()
    paths: list[Path] = []

    for source in sources:
        if not source.get("enabled", True):
            continue

        if source.get("local_path"):
            paths.append(ROOT / source["local_path"])
            continue

        if source.get("slug"):
            paths.append(CALENDAR_CACHE_DIR / f"{source['slug']}.ics")

    if not paths and LEGACY_SCHEMA_PATH.exists():
        paths.append(LEGACY_SCHEMA_PATH)

    return [path for path in paths if path.exists()]


def _schedule_config(schedule_config: dict[str, Any] | None = None) -> dict[str, Any]:
    if schedule_config is not None:
        return schedule_config
    return load_config().get("schedule", {})


def _schedule_labels(schedule_config: dict[str, Any]) -> dict[str, Any]:
    return schedule_config.get("labels", {})


def _normalize_event_datetime(value: Any, timezone_name: str) -> dt.datetime:
    local_timezone = ZoneInfo(timezone_name)
    if isinstance(value, dt.datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=local_timezone)
        return value.astimezone(local_timezone)

    if isinstance(value, dt.date):
        return dt.datetime.combine(value, dt.time.min, tzinfo=local_timezone)

    raise TypeError(f"Unsupported calendar datetime type: {type(value)!r}")


def _event_from_component(component, timezone_name: str) -> ScheduleEvent | None:
    if component.name != "VEVENT":
        return None

    dtstart_raw = component.get("dtstart")
    if dtstart_raw is None:
        return None

    dtend_raw = component.get("dtend")
    start = _normalize_event_datetime(dtstart_raw.dt, timezone_name)
    end = _normalize_event_datetime(dtend_raw.dt, timezone_name) if dtend_raw is not None else start
    all_day = isinstance(dtstart_raw.dt, dt.date) and not isinstance(dtstart_raw.dt, dt.datetime)

    summary = str(component.get("summary", "Untitled event"))
    location = str(component.get("location", "")).strip()
    description = str(component.get("description", "")).replace("\r", "")
    description_lines = [part.strip() for part in description.split("\n") if part.strip()]

    return ScheduleEvent(
        start=start,
        end=end,
        all_day=all_day,
        summary=summary,
        location=location,
        description_lines=description_lines,
    )


def load_schedule_events(
    calendar_paths: list[Path] | None = None,
    timezone_name: str | None = None,
    schedule_config: dict[str, Any] | None = None,
) -> list[ScheduleEvent]:
    schedule_config = _schedule_config(schedule_config)
    timezone_name = timezone_name or schedule_config.get("timezone", "Europe/Stockholm")
    calendar_paths = calendar_paths if calendar_paths is not None else calendar_source_paths()

    events: list[ScheduleEvent] = []
    for path in calendar_paths:
        calendar = Calendar.from_ical(path.read_bytes())
        for component in calendar.walk():
            event = _event_from_component(component, timezone_name)
            if event is not None:
                events.append(event)

    return sorted(events, key=lambda event: (event.start, event.end, event.summary))


def build_schedule_days(
    events: list[ScheduleEvent] | None = None,
    calendar_paths: list[Path] | None = None,
    timezone_name: str | None = None,
    schedule_config: dict[str, Any] | None = None,
) -> list[ScheduleDay]:
    schedule_config = _schedule_config(schedule_config)
    labels = _schedule_labels(schedule_config)
    timezone_name = timezone_name or schedule_config.get("timezone", "Europe/Stockholm")
    days_ahead = schedule_config.get("days_ahead", 1)
    day_names = labels.get("day_names", ["Dagens Schema", "Morgondagens Schema"])

    events = events if events is not None else load_schedule_events(calendar_paths, timezone_name, schedule_config)
    start_day = dt.datetime.now(ZoneInfo(timezone_name)).date()

    days: list[ScheduleDay] = []
    for day_index in range(days_ahead + 1):
        current_day = start_day + dt.timedelta(days=day_index)
        label = day_names[day_index] if day_index < len(day_names) else f"Schema +{day_index}"
        day_events = [event for event in events if event.start.date() == current_day]
        days.append(ScheduleDay(label=label, date=current_day, events=day_events))

    return days


def format_schedule_days(days: list[ScheduleDay], schedule_config: dict[str, Any] | None = None) -> list[str]:
    schedule_config = _schedule_config(schedule_config)
    labels = _schedule_labels(schedule_config)
    description_limit = schedule_config.get("description_lines", 3)
    time_format = schedule_config.get("time_format", "%H:%M")
    show_location = schedule_config.get("show_location", True)
    show_description = schedule_config.get("show_description", True)
    empty_day = labels.get("empty_day", "Inget denna dag! :D")
    missing_calendars = labels.get("missing_calendars", "Ingen kalender hittades.")
    empty_message = schedule_config.get("empty_message", "Amen va tomt det är, går man filfack eller!")
    all_day_label = labels.get("all_day", "Heldag")
    time_prefix = labels.get("time_prefix", "Tid:")
    time_separator = labels.get("time_separator", "till")
    location_prefix = labels.get("location_prefix", "@")

    result: list[str] = []
    any_events = False

    for day in days:
        result.append(f"--- {day.label} ---")
        if not day.events:
            result.append(empty_day if days else missing_calendars)
            continue

        any_events = True
        for event in day.events:
            if event.all_day:
                timing = all_day_label
            else:
                timing = f"{event.start.strftime(time_format)} {time_separator} {event.end.strftime(time_format)}"

            first_line = f"{time_prefix} {timing} {event.summary}".strip()
            if show_location and event.location:
                first_line = f"{first_line} {location_prefix} {event.location}"
            result.append(first_line)

            if show_description and event.description_lines:
                description_lines = event.description_lines
                if isinstance(description_limit, int) and description_limit > 0:
                    description_lines = description_lines[:description_limit]
                result.append(" || ".join(description_lines))

    if not days:
        return [missing_calendars]
    if not any_events and empty_message:
        result.append(empty_message)
    return result


def schema(
    calendar_paths: list[Path] | None = None,
    timezone_name: str | None = None,
    schedule_config: dict[str, Any] | None = None,
) -> list[str]:
    schedule_config = _schedule_config(schedule_config)
    timezone_name = timezone_name or schedule_config.get("timezone", "Europe/Stockholm")
    paths = calendar_paths if calendar_paths is not None else calendar_source_paths()

    if not paths:
        labels = _schedule_labels(schedule_config)
        missing_calendars = labels.get("missing_calendars", "Ingen kalender hittades.")
        days = build_schedule_days(events=[], timezone_name=timezone_name, schedule_config=schedule_config)
        if not days:
            return [missing_calendars]
        result: list[str] = []
        for day in days:
            result.extend([f"--- {day.label} ---", missing_calendars])
        return result

    days = build_schedule_days(calendar_paths=paths, timezone_name=timezone_name, schedule_config=schedule_config)
    return format_schedule_days(days, schedule_config)


def main() -> None:
    for line in schema():
        print(line)


if __name__ == "__main__":
    main()
