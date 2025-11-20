from typing import List

import cv2

from roi_manager import ROIManager


class SettingsPanel:
    """Simple OpenCV trackbar-based settings UI for ROI tuning."""

    WINDOW_NAME = "ROI Settings"
    KEY_CHOICES: List[str] = [
        "space",
        "enter",
        "up",
        "down",
        "left",
        "right",
        "z",
        "x",
        "c",
        "a",
        "s",
        "d",
        "w",
        "q",
        "e",
        "1",
        "2",
        "3",
        "4",
        "shift",
        "ctrl",
        "cmd",
        "alt",
        "tab",
    ]

    def __init__(self, roi_manager: ROIManager) -> None:
        self.roi_manager = roi_manager
        self._active = False
        self._selected_index = 0
        self._shared_threshold = self.roi_manager.threshold

    @property
    def is_active(self) -> bool:
        return self._active

    def show(self) -> None:
        if self._active:
            return
        if not self.roi_manager.rois or not self.roi_manager.frame_shape:
            return

        height, width = self.roi_manager.frame_shape
        self._shared_threshold = self.roi_manager.threshold
        cv2.namedWindow(self.WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.WINDOW_NAME, 400, 320)

        max_roi_index = max(0, len(self.roi_manager.rois) - 1)
        cv2.createTrackbar("ROI", self.WINDOW_NAME, self._selected_index, max(max_roi_index, 1), lambda _v: None)
        cv2.createTrackbar("Sensitivity", self.WINDOW_NAME, int(self._shared_threshold * 100), 100, lambda _v: None)
        cv2.createTrackbar("Width", self.WINDOW_NAME, 50, width, lambda _v: None)
        cv2.createTrackbar("Height", self.WINDOW_NAME, 50, height, lambda _v: None)
        cv2.createTrackbar("Key", self.WINDOW_NAME, 0, max(0, len(self.KEY_CHOICES) - 1), lambda _v: None)

        self._active = True
        self._sync_controls()

    def hide(self) -> None:
        if not self._active:
            return
        cv2.destroyWindow(self.WINDOW_NAME)
        self._active = False

    def update(self) -> None:
        if not self._active:
            return
        rois = self.roi_manager.rois
        if not rois or not self.roi_manager.frame_shape:
            return

        height, width = self.roi_manager.frame_shape

        roi_index = cv2.getTrackbarPos("ROI", self.WINDOW_NAME)
        roi_index = max(0, min(roi_index, len(rois) - 1))
        if roi_index != self._selected_index:
            self._selected_index = roi_index
            self._sync_controls()
            return

        roi = rois[self._selected_index]

        sensitivity_raw = cv2.getTrackbarPos("Sensitivity", self.WINDOW_NAME)
        sensitivity = max(0, min(sensitivity_raw, 100)) / 100.0
        if abs(sensitivity - self._shared_threshold) > 1e-5:
            self._shared_threshold = sensitivity
            self.roi_manager.set_threshold(self._shared_threshold)

        width_raw = cv2.getTrackbarPos("Width", self.WINDOW_NAME)
        height_raw = cv2.getTrackbarPos("Height", self.WINDOW_NAME)
        roi.width = max(10, min(width_raw, width))
        roi.height = max(10, min(height_raw, height))
        roi.x = max(0, min(roi.x, width - roi.width))
        roi.y = max(0, min(roi.y, height - roi.height))

        key_index = cv2.getTrackbarPos("Key", self.WINDOW_NAME)
        key_index = max(0, min(key_index, len(self.KEY_CHOICES) - 1))
        roi.key = self.KEY_CHOICES[key_index]

    def _sync_controls(self) -> None:
        if not self._active:
            return
        rois = self.roi_manager.rois
        if not rois or not self.roi_manager.frame_shape:
            return
        height, width = self.roi_manager.frame_shape

        self._selected_index = max(0, min(self._selected_index, len(rois) - 1))
        roi = rois[self._selected_index]

        self._shared_threshold = self.roi_manager.threshold
        cv2.setTrackbarPos("ROI", self.WINDOW_NAME, self._selected_index)
        cv2.setTrackbarPos("Sensitivity", self.WINDOW_NAME, int(max(0.0, min(self._shared_threshold, 1.0)) * 100))
        cv2.setTrackbarPos("Width", self.WINDOW_NAME, max(10, min(roi.width, width)))
        cv2.setTrackbarPos("Height", self.WINDOW_NAME, max(10, min(roi.height, height)))
        try:
            key_index = self.KEY_CHOICES.index(roi.key.lower())
        except ValueError:
            key_index = 0
        cv2.setTrackbarPos("Key", self.WINDOW_NAME, key_index)
