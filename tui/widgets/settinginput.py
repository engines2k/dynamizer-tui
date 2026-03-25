
from typing import Any, Callable
from textual import on
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Input

class processors():

    @staticmethod
    def color(input: str):
        parts = input.split(',')
        if len(parts) != 3:
            raise ValueError(f'Invalid input "{input}" for color')
        color = tuple(max(0, min(255, int(x.strip()))) for x in parts)
        return color

    @staticmethod
    def postive_float(input: str):
        finput = float(input)
        if finput < 0:
            raise ValueError(f'Multiplier value "{input}" invalid: must be positive')
        return finput


class SettingInput(Widget):
    def __init__(self, settings: Any, key: str, processor: Callable, id: str | None = None, classes: str = "compact-input"):
        super().__init__()
        self._settings = settings
        self._processor = processor
        self._key = key
        self._id = id
        self._input_classes = classes
        self._initial_value = str(settings[key])

    def compose(self) -> ComposeResult:
        yield Input(value=self._initial_value, id=self._id, classes=self._input_classes)

    @on(Input.Changed)
    def on_setting_changed(self, event: Input.Changed) -> None:
        try:
            self._settings[self._key] = self._processor(event.value)
        except ValueError:
            pass
