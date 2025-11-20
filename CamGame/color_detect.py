from dataclasses import dataclass
from typing import Optional, Tuple

import cv2
import numpy as np


HSVBounds = Tuple[int, int, int]


@dataclass
class GreenConfig:
    lower: HSVBounds = (40, 40, 40)
    upper: HSVBounds = (85, 255, 255)
    blur_kernel: Tuple[int, int] = (5, 5)
    morph_kernel: int = 5
    enable_tuner: bool = False
    tuner_window: str = "HSV Tuner"


class HSVRangeTuner:
    """Interactive trackbar window for tweaking HSV bounds at runtime."""

    def __init__(self, window_name: str, lower: HSVBounds, upper: HSVBounds) -> None:
        self.window_name = window_name
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, 400, 240)
        bounds = list(lower + upper)
        labels = ["H min", "S min", "V min", "H max", "S max", "V max"]
        limits = [180, 255, 255, 180, 255, 255]
        for i, label in enumerate(labels):
            cv2.createTrackbar(label, self.window_name, bounds[i], limits[i], lambda _v: None)
        self.set_bounds(lower, upper)

    def get_bounds(self) -> Tuple[HSVBounds, HSVBounds]:
        h_min = cv2.getTrackbarPos("H min", self.window_name)
        s_min = cv2.getTrackbarPos("S min", self.window_name)
        v_min = cv2.getTrackbarPos("V min", self.window_name)
        h_max = cv2.getTrackbarPos("H max", self.window_name)
        s_max = cv2.getTrackbarPos("S max", self.window_name)
        v_max = cv2.getTrackbarPos("V max", self.window_name)
        lower = (h_min, s_min, v_min)
        upper = (h_max, s_max, v_max)
        return lower, upper

    def set_bounds(self, lower: HSVBounds, upper: HSVBounds) -> None:
        labels = ["H min", "S min", "V min", "H max", "S max", "V max"]
        values = list(lower + upper)
        for label, value in zip(labels, values):
            cv2.setTrackbarPos(label, self.window_name, int(value))


class GreenDetector:
    """Detects green regions in a frame and returns a cleaned binary mask."""

    def __init__(self, config: Optional[GreenConfig] = None) -> None:
        self.config = config or GreenConfig()
        kernel_size = max(1, int(self.config.morph_kernel))
        self._kernel = np.ones((kernel_size, kernel_size), np.uint8) if kernel_size > 1 else None
        self._tuner: Optional[HSVRangeTuner] = None

    def detect(self, frame: np.ndarray) -> np.ndarray:
        if frame is None:
            raise ValueError("Frame is None.")
        blurred = cv2.GaussianBlur(frame, self.config.blur_kernel, 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
        lower, upper = self._get_bounds()
        self.config.lower, self.config.upper = lower, upper
        mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
        if self._kernel is not None and self._kernel.size > 1:
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self._kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, self._kernel)
        return mask

    def _get_bounds(self) -> Tuple[HSVBounds, HSVBounds]:
        if self.config.enable_tuner:
            if self._tuner is None:
                self._tuner = HSVRangeTuner(self.config.tuner_window, self.config.lower, self.config.upper)
            return self._tuner.get_bounds()
        return self.config.lower, self.config.upper

    def set_tuner_enabled(self, enabled: bool) -> None:
        if enabled == self.config.enable_tuner:
            return
        self.config.enable_tuner = enabled
        if enabled:
            self._tuner = HSVRangeTuner(self.config.tuner_window, self.config.lower, self.config.upper)
        else:
            if self._tuner is not None:
                cv2.destroyWindow(self._tuner.window_name)
            self._tuner = None
