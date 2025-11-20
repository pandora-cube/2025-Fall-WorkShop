import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import cv2
import numpy as np


@dataclass
class ROI:
    """Represents a rectangular region of interest bound to a key/action."""

    id: str
    label: str
    key: str
    x: int
    y: int
    width: int
    height: int
    threshold: float = 0.08  # minimum coverage ratio to consider active

    def rect(self) -> Tuple[int, int, int, int]:
        return self.x, self.y, self.width, self.height

    def contains_point(self, px: int, py: int) -> bool:
        x, y, w, h = self.rect()
        return x <= px <= x + w and y <= py <= y + h

    def coverage(self, mask: np.ndarray) -> float:
        x, y, w, h = self.rect()
        h_mask, w_mask = mask.shape[:2]
        if w == 0 or h == 0:
            return 0.0
        if x >= w_mask or y >= h_mask:
            return 0.0
        x_end = min(x + w, w_mask)
        y_end = min(y + h, h_mask)
        sub_mask = mask[y:y_end, x:x_end]
        if sub_mask.size == 0:
            return 0.0
        active_pixels = cv2.countNonZero(sub_mask)
        total_pixels = float(sub_mask.shape[0] * sub_mask.shape[1])
        return active_pixels / total_pixels

    def is_active(self, mask: np.ndarray) -> Tuple[bool, float]:
        ratio = self.coverage(mask)
        return ratio >= self.threshold, ratio

    def to_normalized(self, frame_width: int, frame_height: int) -> dict:
        if frame_width == 0 or frame_height == 0:
            raise ValueError("Frame dimensions must be non-zero.")
        payload = asdict(self)
        payload.update(
            {
                "x": self.x / frame_width,
                "y": self.y / frame_height,
                "width": self.width / frame_width,
                "height": self.height / frame_height,
            }
        )
        return payload

    @classmethod
    def from_normalized(cls, frame_width: int, frame_height: int, data: dict) -> "ROI":
        return cls(
            id=data["id"],
            label=data.get("label", data["id"]),
            key=data.get("key", ""),
            x=int(data["x"] * frame_width),
            y=int(data["y"] * frame_height),
            width=int(data["width"] * frame_width),
            height=int(data["height"] * frame_height),
            threshold=float(data.get("threshold", 0.08)),
        )


class ROIManager:
    """Maintains ROI definitions, hit-testing, drawing, and persistence."""

    def __init__(
        self,
        config_path: str = "roi_config.json",
        default_keys: Optional[Iterable[str]] = None,
    ) -> None:
        self._config_path = Path(config_path)
        self._frame_shape: Optional[Tuple[int, int]] = None  # (height, width)
        self._rois: List[ROI] = []
        self._dragging_roi_id: Optional[str] = None
        self._drag_offset: Tuple[int, int] = (0, 0)
        self._edit_mode: bool = False
        self._default_keys = list(default_keys or ["space", "up", "down", "left", "right", "z", "x", "c"])
        self._threshold: float = 0.08

    @property
    def rois(self) -> List[ROI]:
        return self._rois

    @property
    def frame_shape(self) -> Optional[Tuple[int, int]]:
        return self._frame_shape

    @property
    def edit_mode(self) -> bool:
        return self._edit_mode

    @property
    def threshold(self) -> float:
        return self._threshold

    def set_edit_mode(self, enabled: bool) -> None:
        self._edit_mode = enabled
        if not enabled:
            self._dragging_roi_id = None

    def register_window(self, window_name: str) -> None:
        cv2.setMouseCallback(window_name, self._handle_mouse_event)

    def ensure_initialized(self, frame: np.ndarray) -> None:
        height, width = frame.shape[:2]
        self._frame_shape = (height, width)
        if self._rois:
            return
        if self._config_path.exists():
            self._load_config(width, height)
        else:
            self._create_default_layout(width, height)

    def evaluate(self, mask: np.ndarray) -> List[Tuple[ROI, bool, float]]:
        results: List[Tuple[ROI, bool, float]] = []
        for roi in self._rois:
            active, ratio = roi.is_active(mask)
            results.append((roi, active, ratio))
        return results

    def draw(self, frame: np.ndarray, active_ids: Optional[Iterable[str]] = None) -> None:
        active_set = set(active_ids or [])
        for roi in self._rois:
            x, y, w, h = roi.rect()
            color = (0, 255, 0) if roi.id in active_set else (0, 128, 255)
            if self._edit_mode:
                color = (255, 0, 0)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            label = f"{roi.label} ({roi.key})"
            cv2.putText(
                frame,
                label,
                (x + 4, y + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2,
                cv2.LINE_AA,
            )

    def save_config(self) -> None:
        if not self._frame_shape:
            return
        height, width = self._frame_shape
        payload = {
            "rois": [roi.to_normalized(width, height) for roi in self._rois],
            "frame_size": {"width": width, "height": height},
            "threshold": self._threshold,
        }
        self._config_path.write_text(json.dumps(payload, indent=2))

    def set_threshold(self, value: float) -> None:
        self._threshold = max(0.0, min(value, 1.0))
        for roi in self._rois:
            roi.threshold = self._threshold

    def _load_config(self, width: int, height: int) -> None:
        data = json.loads(self._config_path.read_text())
        if "threshold" in data:
            self._threshold = float(data["threshold"])
        rois: List[ROI] = []
        for idx, item in enumerate(data.get("rois", [])):
            roi = ROI.from_normalized(width, height, item)
            # ensure unique ids even if config is stale
            if not roi.id:
                roi.id = f"roi_{idx}"
            rois.append(roi)
        self._rois = rois
        if self._rois:
            self._threshold = self._rois[0].threshold
            self.set_threshold(self._threshold)
        if not self._rois:
            self._create_default_layout(width, height)

    def _create_default_layout(self, width: int, height: int) -> None:
        rows, cols = 2, 4
        margin_ratio = 0.08
        cell_w = width / cols
        cell_h = height / rows
        roi_w = int(cell_w * (1 - margin_ratio))
        roi_h = int(cell_h * (1 - margin_ratio))
        rois: List[ROI] = []
        key_cycle = self._default_keys or ["space"]
        for row in range(rows):
            for col in range(cols):
                idx = row * cols + col
                if idx >= 8:
                    break
                x = int(col * cell_w + (cell_w - roi_w) / 2)
                y = int(row * cell_h + (cell_h - roi_h) / 2)
                key = key_cycle[idx % len(key_cycle)]
                rois.append(
                    ROI(
                        id=f"roi_{idx}",
                        label=f"Slot {idx + 1}",
                        key=key,
                        x=x,
                        y=y,
                        width=roi_w,
                        height=roi_h,
                        threshold=self._threshold,
                    )
                )
        self._rois = rois

    def _handle_mouse_event(self, event: int, x: int, y: int, flags: int, _param) -> None:
        if not self._edit_mode or not self._frame_shape:
            return
        height, width = self._frame_shape
        if event == cv2.EVENT_LBUTTONDOWN:
            for roi in reversed(self._rois):
                if roi.contains_point(x, y):
                    self._dragging_roi_id = roi.id
                    self._drag_offset = (x - roi.x, y - roi.y)
                    break
        elif event == cv2.EVENT_MOUSEMOVE and self._dragging_roi_id and (flags & cv2.EVENT_FLAG_LBUTTON):
            roi = self._get_roi(self._dragging_roi_id)
            if not roi:
                return
            offset_x, offset_y = self._drag_offset
            new_x = x - offset_x
            new_y = y - offset_y
            new_x = max(0, min(new_x, width - roi.width))
            new_y = max(0, min(new_y, height - roi.height))
            roi.x = new_x
            roi.y = new_y
        elif event == cv2.EVENT_LBUTTONUP:
            self._dragging_roi_id = None

    def _get_roi(self, roi_id: str) -> Optional[ROI]:
        for roi in self._rois:
            if roi.id == roi_id:
                return roi
        return None
