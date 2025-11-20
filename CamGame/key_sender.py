from typing import Optional, Union

try:
    from pynput.keyboard import Controller, Key
except ImportError as exc:  # pragma: no cover - handled at runtime
    Controller = None  # type: ignore[assignment]
    Key = None  # type: ignore[assignment]
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


class KeySender:
    """Wrapper around pynput to press/release keys across desktop platforms."""

    KEY_ALIASES = {
        "space": "space",
        "enter": "enter",
        "return": "enter",
        "windows": "cmd",
        "win": "cmd",
        "up": "up",
        "down": "down",
        "left": "left",
        "right": "right",
        "shift": "shift",
        "control": "ctrl",
        "ctrl": "ctrl",
        "command": "cmd",
        "cmd": "cmd",
        "option": "alt",
        "alt": "alt",
        "tab": "tab",
    }

    SPECIAL_KEYS = {
        "space": "space",
        "enter": "enter",
        "windows": "cmd",
        "win": "cmd",
        "up": "up",
        "down": "down",
        "left": "left",
        "right": "right",
        "shift": "shift",
        "ctrl": "ctrl",
        "cmd": "cmd",
        "alt": "alt",
        "tab": "tab",
    }

    def __init__(self) -> None:
        if Controller is None or Key is None:
            raise ImportError(
                "pynput is required for KeySender but is not installed. "
                "Install it with `pip install pynput` and grant accessibility permissions on macOS "
                "or enable keyboard control access on Windows."
            ) from _IMPORT_ERROR
        self._controller = Controller()
        self._pressed: set[str] = set()
        self._special_keys = {name: getattr(Key, attr) for name, attr in self.SPECIAL_KEYS.items()}

    def press(self, key: str) -> None:
        resolved = self._resolve_key(key)
        if resolved is None:
            return
        key_id = self._key_identifier(key)
        if key_id in self._pressed:
            return
        self._controller.press(resolved)
        self._pressed.add(key_id)

    def release(self, key: str) -> None:
        resolved = self._resolve_key(key)
        if resolved is None:
            return
        key_id = self._key_identifier(key)
        if key_id not in self._pressed:
            return
        self._controller.release(resolved)
        self._pressed.discard(key_id)

    def tap(self, key: str) -> None:
        self.press(key)
        self.release(key)

    def _resolve_key(self, key_name: str) -> Optional[Union[str, Key]]:
        normalized = key_name.lower()
        normalized = self.KEY_ALIASES.get(normalized, normalized)
        if len(normalized) == 1:
            return normalized
        special = self._special_keys.get(normalized)
        if special:
            return special
        return None

    def _key_identifier(self, key_name: str) -> str:
        normalized = key_name.lower()
        return self.KEY_ALIASES.get(normalized, normalized)

    def release_all(self) -> None:
        for key_id in list(self._pressed):
            resolved = self._resolve_key(key_id)
            if resolved is not None:
                self._controller.release(resolved)
            self._pressed.discard(key_id)
