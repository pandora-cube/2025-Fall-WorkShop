from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple

from roi_manager import ROI


@dataclass
class _ROIState:
    key: str
    active_frames: int = 0
    inactive_frames: int = 0
    is_pressed: bool = False


class ActionMapper:
    """Converts ROI activation status into press/release events with debounce."""

    def __init__(
        self,
        activation_frames: int = 2,
        release_frames: int = 2,
    ) -> None:
        self.activation_frames = max(1, activation_frames)
        self.release_frames = max(1, release_frames)
        self._states: Dict[str, _ROIState] = {}

    def sync_from_rois(self, rois: Iterable[ROI]) -> None:
        known_ids = set(self._states.keys())
        incoming_ids = {roi.id for roi in rois}

        for roi in rois:
            if roi.id not in self._states:
                self._states[roi.id] = _ROIState(key=roi.key)
            else:
                self._states[roi.id].key = roi.key

        # Remove states no longer needed
        for stale_id in known_ids - incoming_ids:
            self._states.pop(stale_id, None)

    def update(self, roi_results: Sequence[Tuple[ROI, bool, float]]) -> List[Tuple[str, str]]:
        """Return a list of ('press'|'release', key) actions that should be fired."""
        actions: List[Tuple[str, str]] = []
        for roi, is_active, _coverage in roi_results:
            state = self._states.setdefault(roi.id, _ROIState(key=roi.key))
            state.key = roi.key  # keep key updated if config changed

            if is_active:
                state.active_frames += 1
                state.inactive_frames = 0
                if not state.is_pressed and state.active_frames >= self.activation_frames:
                    state.is_pressed = True
                    actions.append(("press", state.key))
            else:
                state.inactive_frames += 1
                state.active_frames = 0
                if state.is_pressed and state.inactive_frames >= self.release_frames:
                    state.is_pressed = False
                    actions.append(("release", state.key))
        return actions
