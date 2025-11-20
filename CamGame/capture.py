import time
from dataclasses import dataclass, field
from typing import Generator, Optional, Tuple

import cv2
import numpy as np
import sys


def _default_backends() -> Tuple[int, ...]:
    if sys.platform.startswith("win"):
        return (cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY)
    if sys.platform == "darwin":
        return (cv2.CAP_AVFOUNDATION, cv2.CAP_ANY)
    return (cv2.CAP_V4L2, cv2.CAP_ANY)


@dataclass
class CaptureConfig:
    index: int = 0
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = 30.0
    backend_fallback: Tuple[int, ...] = field(default_factory=_default_backends)


class CameraCapture:
    """Thin wrapper around OpenCV video capture with FPS throttling."""

    def __init__(self, config: Optional[CaptureConfig] = None) -> None:
        self.config = config or CaptureConfig()
        self._cap: Optional[cv2.VideoCapture] = None
        self._frame_interval: Optional[float] = None
        self._timestamp_next_frame: float = 0.0

        if self.config.fps and self.config.fps > 0:
            self._frame_interval = 1.0 / self.config.fps

    def open(self) -> None:
        if self._cap is not None:
            return
        last_error = None
        for backend in self.config.backend_fallback:
            cap = cv2.VideoCapture(self.config.index, backend)
            if cap is None or not cap.isOpened():
                last_error = RuntimeError(f"Unable to open camera {self.config.index} with backend {backend}.")
                continue
            self._cap = cap
            break
        if self._cap is None:
            if last_error:
                raise last_error
            raise RuntimeError("Unable to open camera.")

        if self.config.width:
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
        if self.config.height:
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
        if self.config.fps:
            self._cap.set(cv2.CAP_PROP_FPS, self.config.fps)

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        if self._cap is None:
            self.open()
        assert self._cap is not None
        if self._frame_interval:
            delay = self._timestamp_next_frame - time.time()
            if delay > 0:
                time.sleep(delay)
        ret, frame = self._cap.read()
        if ret and self._frame_interval:
            self._timestamp_next_frame = time.time() + self._frame_interval
        return ret, frame if ret else None

    def iter_frames(self) -> Generator[np.ndarray, None, None]:
        while True:
            ret, frame = self.read()
            if not ret or frame is None:
                break
            yield frame

    def release(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def __enter__(self) -> "CameraCapture":
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()
