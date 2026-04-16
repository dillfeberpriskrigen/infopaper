#!/usr/bin/python3

from __future__ import annotations

import json
import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk
from typing import Any

from PIL import Image, ImageTk

from collectors import WallpaperData, collect_wallpaper_data
from config import LAYOUT_PATH, ROOT, load_config, load_layout
from draw import draw_calendar, load_base_image
from renderer import _resolve_color, _resolve_x, _resolve_y


PREVIEW_MAX_WIDTH = 1200
PREVIEW_MAX_HEIGHT = 780


@dataclass(frozen=True)
class CanvasItem:
    key: str
    kind: str
    content: str


FALLBACK_DATA = WallpaperData(
    date_label="Fallback data",
    weekday_label="Data import error",
    update_label="Collector preview unavailable",
    weather_lines=[
        "Fallback weather preview",
        "Real collector data could not be loaded",
        "Check your config or data sources",
    ],
    schedule_lines=[
        "--- Fallback schedule ---",
        "Data import error",
        "Real schedule data could not be loaded",
    ],
    custom_content={
        "hello_world": "Fallback custom content",
        "custom_lines": ["Data import error", "Using built-in preview values"],
    },
    reboot_required=True,
)


class PlacerApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Infopaper Placer")

        self.config = load_config()
        self.layout = load_layout()
        self.data = self._load_preview_data()
        self.files = self.config["files"]
        self.layout_items: list[CanvasItem] = []
        self.canvas_item_ids: dict[int, CanvasItem] = {}
        self.canvas_images: list[ImageTk.PhotoImage] = []
        self.selected_key: str | None = None
        self.drag_offset = (0.0, 0.0)

        self.background_image = load_base_image(ROOT / self.files["infile_path"]).convert("RGB")
        self.scale = min(
            PREVIEW_MAX_WIDTH / self.background_image.size[0],
            PREVIEW_MAX_HEIGHT / self.background_image.size[1],
            1.0,
        )
        self.preview_size = (
            int(self.background_image.size[0] * self.scale),
            int(self.background_image.size[1] * self.scale),
        )
        self.preview_background = self.background_image.resize(self.preview_size, Image.Resampling.LANCZOS)
        self.tk_background = ImageTk.PhotoImage(self.preview_background)

        self.selected_label_var = tk.StringVar(value="No selection")
        self.position_var = tk.StringVar(value="x: -, y: -")
        self.fontsize_var = tk.IntVar(value=20)
        self.line_spacing_var = tk.IntVar(value=0)
        self.visible_var = tk.BooleanVar(value=True)
        self.content_var = tk.StringVar(value="")

        self._build_ui()
        self.refresh_canvas()

    def _load_preview_data(self) -> WallpaperData:
        try:
            return collect_wallpaper_data(load_config())
        except Exception:
            return FALLBACK_DATA

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=12)
        container.pack(fill="both", expand=True)

        canvas_frame = ttk.Frame(container)
        canvas_frame.pack(side="left", fill="both", expand=True)

        sidebar = ttk.Frame(container, padding=(12, 0, 0, 0))
        sidebar.pack(side="right", fill="y")

        self.canvas = tk.Canvas(
            canvas_frame,
            width=self.preview_size[0],
            height=self.preview_size[1],
            highlightthickness=1,
            highlightbackground="#444444",
            bg="#111111",
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)

        ttk.Label(sidebar, text="Objects").pack(anchor="w")
        self.object_list = tk.Listbox(sidebar, exportselection=False, height=10)
        self.object_list.pack(fill="x", pady=(4, 10))
        self.object_list.bind("<<ListboxSelect>>", self.on_list_select)

        ttk.Label(sidebar, textvariable=self.selected_label_var).pack(anchor="w", pady=(0, 6))
        ttk.Label(sidebar, textvariable=self.position_var).pack(anchor="w", pady=(0, 10))

        ttk.Label(sidebar, text="Font size").pack(anchor="w")
        self.fontsize_spin = ttk.Spinbox(sidebar, from_=8, to=240, textvariable=self.fontsize_var, width=10)
        self.fontsize_spin.pack(anchor="w", pady=(4, 10))
        self.fontsize_spin.bind("<Return>", self.on_property_change)
        self.fontsize_spin.bind("<<Increment>>", self.on_property_change)
        self.fontsize_spin.bind("<<Decrement>>", self.on_property_change)
        self.fontsize_spin.bind("<FocusOut>", self.on_property_change)

        ttk.Label(sidebar, text="Line spacing").pack(anchor="w")
        self.line_spacing_spin = ttk.Spinbox(sidebar, from_=0, to=240, textvariable=self.line_spacing_var, width=10)
        self.line_spacing_spin.pack(anchor="w", pady=(4, 10))
        self.line_spacing_spin.bind("<Return>", self.on_property_change)
        self.line_spacing_spin.bind("<<Increment>>", self.on_property_change)
        self.line_spacing_spin.bind("<<Decrement>>", self.on_property_change)
        self.line_spacing_spin.bind("<FocusOut>", self.on_property_change)

        self.visible_check = ttk.Checkbutton(
            sidebar,
            text="Visible",
            variable=self.visible_var,
            command=self.on_property_change,
        )
        self.visible_check.pack(anchor="w", pady=(0, 10))

        ttk.Label(sidebar, text="Content").pack(anchor="w")
        self.content_entry = ttk.Entry(sidebar, textvariable=self.content_var, width=32)
        self.content_entry.pack(anchor="w", fill="x", pady=(4, 10))
        self.content_entry.bind("<Return>", self.on_property_change)
        self.content_entry.bind("<FocusOut>", self.on_property_change)

        ttk.Button(sidebar, text="Refresh Preview", command=self.refresh_preview_data).pack(fill="x", pady=(0, 6))
        ttk.Button(sidebar, text="Save Layout", command=self.save_layout).pack(fill="x", pady=(0, 6))
        ttk.Button(sidebar, text="Reload Layout", command=self.reload_layout).pack(fill="x")

    def _build_canvas_items(self) -> list[CanvasItem]:
        schedule_preview_lines = self.config.get("schedule", {}).get(
            "preview_lines",
            self.config.get("schedule", {}).get("max_lines", 8),
        )
        items = [
            CanvasItem("text.date", "text", self.data.date_label),
            CanvasItem("text.weekday", "text", self.data.weekday_label),
            CanvasItem("text.updates", "text", self.data.update_label or "Uppdateringar: 0"),
            CanvasItem("text.reboot", "text", self.layout["text"]["reboot"].get("content", "Reboot required")),
            CanvasItem("weather", "weather", "\n".join(self.data.weather_lines[:3]) or "Weather preview"),
            CanvasItem(
                "schedule",
                "schedule",
                "\n".join(self.data.schedule_lines[:schedule_preview_lines]) or "Schedule preview",
            ),
            CanvasItem("calendar", "calendar", "Calendar"),
        ]
        reserved_keys = {"text", "weather", "schedule", "calendar"}
        for key, value in self.data.custom_content.items():
            if key not in self.layout or key in reserved_keys:
                continue
            content = "\n".join(value) if isinstance(value, list) else value
            items.append(CanvasItem(key, "custom", content))
        return items

    def refresh_canvas(self) -> None:
        self.canvas.delete("all")
        self.canvas_item_ids.clear()
        self.canvas_images.clear()
        self.layout_items = self._build_canvas_items()
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_background)

        self.object_list.delete(0, tk.END)
        for item in self.layout_items:
            self.object_list.insert(tk.END, item.key)

        for item in self.layout_items:
            block = self._get_block(item.key)
            visible = block.get("visible", True)
            if not visible:
                continue

            x, y = self._scaled_coordinates(block)
            font_size = max(8, int(block.get("fontsize", self.files["fontsize_normal"]) * self.scale))
            color = self._color_to_hex(block.get("color", 1))

            if item.kind == "calendar":
                canvas_ids, bbox = self._create_calendar_canvas_block(x, y, block, item.key)
            else:
                canvas_ids = self._create_canvas_text_block(
                    x,
                    y,
                    item.content,
                    font_size,
                    color,
                    max(0, int(block.get("line_spacing", 0) * self.scale)),
                    item.key,
                )
                bbox = self._combined_bbox(canvas_ids)

            if bbox:
                rect_id = self.canvas.create_rectangle(
                    bbox[0] - 4,
                    bbox[1] - 4,
                    bbox[2] + 4,
                    bbox[3] + 4,
                    outline="#f0c674" if self.selected_key == item.key else "#666666",
                    width=2 if self.selected_key == item.key else 1,
                )
                self.canvas.tag_lower(rect_id)
                for canvas_id in canvas_ids:
                    self.canvas_item_ids[canvas_id] = item
                self.canvas_item_ids[rect_id] = item

        if self.selected_key:
            self._sync_selected_controls(self.selected_key, preserve_list=False)

    def _color_to_hex(self, color_value: Any) -> str:
        r, g, b = _resolve_color(color_value)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _get_block(self, key: str) -> dict[str, Any]:
        if key.startswith("text."):
            return self.layout["text"][key.split(".", 1)[1]]
        return self.layout[key]

    def _scaled_coordinates(self, block: dict[str, Any]) -> tuple[float, float]:
        x = _resolve_x(block["x"], self.background_image.size[0]) * self.scale
        y = _resolve_y(block["y"], self.background_image.size[1]) * self.scale
        return x, y

    def _create_canvas_text_block(
        self,
        x: float,
        y: float,
        content: str,
        font_size: int,
        color: str,
        line_spacing: int,
        key: str,
    ) -> list[int]:
        line_ids: list[int] = []
        lines = content.splitlines() or [content]
        line_height = font_size + line_spacing

        for index, line in enumerate(lines):
            canvas_id = self.canvas.create_text(
                x,
                y + (index * line_height),
                text=line,
                fill=color,
                font=("TkDefaultFont", font_size),
                anchor="nw",
                tags=("draggable", key),
            )
            line_ids.append(canvas_id)

        return line_ids

    def _combined_bbox(self, item_ids: list[int]) -> tuple[int, int, int, int] | None:
        boxes = [self.canvas.bbox(item_id) for item_id in item_ids]
        boxes = [box for box in boxes if box is not None]
        if not boxes:
            return None

        return (
            min(box[0] for box in boxes),
            min(box[1] for box in boxes),
            max(box[2] for box in boxes),
            max(box[3] for box in boxes),
        )

    def _create_calendar_canvas_block(
        self,
        x: float,
        y: float,
        block: dict[str, Any],
        key: str,
    ) -> tuple[list[int], tuple[int, int, int, int] | None]:
        overlay = Image.new("RGBA", self.preview_size, (0, 0, 0, 0))
        draw_calendar(
            overlay,
            x,
            y,
            max(8, int(block.get("fontsize", self.files["fontsize_small"]) * self.scale)),
            _resolve_color(block.get("color", 2)),
        )
        bbox = overlay.getbbox()
        if bbox is None:
            return [], None

        cropped = overlay.crop(bbox)
        tk_image = ImageTk.PhotoImage(cropped)
        self.canvas_images.append(tk_image)
        canvas_id = self.canvas.create_image(bbox[0], bbox[1], anchor="nw", image=tk_image, tags=("draggable", key))
        return [canvas_id], bbox

    def _select_by_key(self, key: str, preserve_list: bool = False) -> None:
        self.selected_key = key
        self._sync_selected_controls(key, preserve_list=preserve_list)
        self.refresh_canvas()

    def _sync_selected_controls(self, key: str, preserve_list: bool = False) -> None:
        block = self._get_block(key)
        self.selected_label_var.set(key)
        x = int(_resolve_x(block["x"], self.background_image.size[0]))
        y = int(_resolve_y(block["y"], self.background_image.size[1]))
        self.position_var.set(f"x: {x}, y: {y}")
        self.fontsize_var.set(block.get("fontsize", self.files["fontsize_normal"]))
        self.line_spacing_var.set(block.get("line_spacing", 0))
        self.visible_var.set(block.get("visible", True))
        self.content_var.set(block.get("content", ""))

        if not preserve_list:
            try:
                index = [item.key for item in self.layout_items].index(key)
            except ValueError:
                index = None
            if index is not None:
                self.object_list.selection_clear(0, tk.END)
                self.object_list.selection_set(index)
                self.object_list.activate(index)

    def on_list_select(self, _event) -> None:
        selection = self.object_list.curselection()
        if not selection:
            return
        self._select_by_key(self.object_list.get(selection[0]), preserve_list=True)

    def on_canvas_click(self, event) -> None:
        hit = self.canvas.find_closest(event.x, event.y)
        if not hit:
            return
        item = self.canvas_item_ids.get(hit[0])
        if item is None:
            return

        block = self._get_block(item.key)
        x = _resolve_x(block["x"], self.background_image.size[0]) * self.scale
        y = _resolve_y(block["y"], self.background_image.size[1]) * self.scale
        self.drag_offset = (event.x - x, event.y - y)
        self._select_by_key(item.key)

    def on_canvas_drag(self, event) -> None:
        if not self.selected_key:
            return

        block = self._get_block(self.selected_key)
        new_x = max(0, min(self.preview_size[0], event.x - self.drag_offset[0]))
        new_y = max(0, min(self.preview_size[1], event.y - self.drag_offset[1]))
        block["x"] = {"mode": "absolute", "value": round(new_x / self.scale)}
        block["y"] = {"mode": "absolute", "value": round(new_y / self.scale)}
        self.position_var.set(f"x: {int(new_x / self.scale)}, y: {int(new_y / self.scale)}")
        self.refresh_canvas()

    def on_property_change(self, _event=None) -> None:
        if not self.selected_key:
            return

        block = self._get_block(self.selected_key)
        block["fontsize"] = max(8, int(self.fontsize_var.get()))
        block["line_spacing"] = max(0, int(self.line_spacing_var.get()))
        block["visible"] = self.visible_var.get()
        if "content" in block:
            block["content"] = self.content_var.get()
        self.refresh_canvas()

    def refresh_preview_data(self) -> None:
        self.data = self._load_preview_data()
        self.refresh_canvas()

    def save_layout(self) -> None:
        with LAYOUT_PATH.open("w", encoding="utf-8") as layout_file:
            json.dump(self.layout, layout_file, indent=2)
            layout_file.write("\n")

    def reload_layout(self) -> None:
        self.layout = load_layout()
        self.refresh_canvas()

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    PlacerApp().run()


if __name__ == "__main__":
    main()
