from dataclasses import dataclass

import cv2
import numpy as np

from capture import CameraCapture, CaptureConfig
from color_detect import GreenConfig, GreenDetector
from key_sender import KeySender
from mapper import ActionMapper
from roi_manager import ROIManager
from settings_panel import SettingsPanel


@dataclass
class AppConfig:
    camera_index: int = 0
    target_fps: float = 30.0
    display_window: str = "CamGame"
    mask_window: str = "Cam Mask"
    show_mask: bool = False
    activation_frames: int = 3
    release_frames: int = 3
    edit_mode: bool = False


class CamGameApp:
    """Main orchestrator tying capture, detection, ROI hits, and key events together."""

    def __init__(self, app_config: AppConfig, green_config: GreenConfig) -> None:
        self.app_config = app_config
        self.capture = CameraCapture(
            CaptureConfig(index=app_config.camera_index, fps=app_config.target_fps)
        )
        self.detector = GreenDetector(green_config)
        self.roi_manager = ROIManager()
        self.settings_panel = SettingsPanel(self.roi_manager)
        self.mapper = ActionMapper(
            activation_frames=app_config.activation_frames,
            release_frames=app_config.release_frames,
        )
        self.key_sender = KeySender()
        self._show_mask = app_config.show_mask

    def run(self) -> None:
        cv2.namedWindow(self.app_config.display_window, cv2.WINDOW_NORMAL)
        self.roi_manager.register_window(self.app_config.display_window)
        self.roi_manager.set_edit_mode(self.app_config.edit_mode)
        mask_window_created = False

        with self.capture as cam:
            for frame in cam.iter_frames():
                if frame is None:
                    continue
                frame = cv2.flip(frame, 1)
                self.roi_manager.ensure_initialized(frame)
                # keep mapper state aligned with ROI list (keys may change via configuration)
                self.mapper.sync_from_rois(self.roi_manager.rois)

                if self.roi_manager.edit_mode and not self.settings_panel.is_active:
                    self.settings_panel.show()
                elif not self.roi_manager.edit_mode and self.settings_panel.is_active:
                    self.settings_panel.hide()

                mask = self.detector.detect(frame)
                evaluations = self.roi_manager.evaluate(mask)
                active_ids = [roi.id for roi, active, _ in evaluations if active]
                actions = self.mapper.update(evaluations)

                for action, key in actions:
                    if action == "press":
                        self.key_sender.press(key)
                    elif action == "release":
                        self.key_sender.release(key)

                overlay = frame.copy()
                self.roi_manager.draw(overlay, active_ids)
                self._draw_overlay_text(overlay)

                cv2.imshow(self.app_config.display_window, overlay)

                if self.roi_manager.edit_mode:
                    self.settings_panel.update()

                if self._show_mask:
                    cv2.imshow(self.app_config.mask_window, mask)
                    mask_window_created = True
                elif mask_window_created:
                    cv2.destroyWindow(self.app_config.mask_window)
                    mask_window_created = False

                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                elif key == ord("m"):
                    self._show_mask = not self._show_mask
                elif key == ord("e"):
                    self.roi_manager.set_edit_mode(not self.roi_manager.edit_mode)
                    if self.roi_manager.edit_mode:
                        self.settings_panel.show()
                    else:
                        self.settings_panel.hide()
                elif key == ord("s"):
                    self.roi_manager.save_config()
                elif key == ord("t"):
                    self.detector.set_tuner_enabled(not self.detector.config.enable_tuner)

            if self.roi_manager.edit_mode:
                self.settings_panel.hide()

        self.key_sender.release_all()
        cv2.destroyAllWindows()

    def _draw_overlay_text(self, frame: np.ndarray) -> None:
        lines = [
            "Controls: [Q]uit  [E]dit ROI  [S]ave ROI  [M]ask  [T]une HSV",
            f"Edit mode: {'ON' if self.roi_manager.edit_mode else 'OFF'}",
            f"HSV tuner: {'ON' if self.detector.config.enable_tuner else 'OFF'}",
        ]
        for idx, line in enumerate(lines):
            cv2.putText(
                frame,
                line,
                (10, 25 + idx * 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                1,
                cv2.LINE_AA,
            )


def main() -> None:
    app_config = AppConfig()
    green_config = GreenConfig()
    try:
        app = CamGameApp(app_config, green_config)
    except ImportError as exc:
        print(f"[ERROR] {exc}")
        return
    app.run()


if __name__ == "__main__":
    main()
