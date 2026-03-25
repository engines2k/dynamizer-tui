from typing import Any, Callable, Iterable
from textual import on
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Select


class SettingSelect(Widget):
    def __init__(self,
                 settings: Any,
                 key: str,
                 options: Iterable[tuple],
                 processor: Callable,
                 id: str | None = None,
                 classes: str = "compact-input"):
        super().__init__()
        self._settings = settings
        self._key = key
        self._options = options
        self._processor = processor
        self._id = id
        self._select_classes = classes

        initial_value = settings[key]
        for display, value in options:
            if value == initial_value:
                self._initial_value = value
                break
        else:
            self._initial_value = options[0][1] if options else None

    def compose(self) -> ComposeResult:
        yield Select(
            options=self._options,
            value=self._initial_value,
            id=self._id,
            classes=self._select_classes
        )

    @on(Select.Changed)
    def on_setting_changed(self, event: Select.Changed) -> None:
        if event.value is not None and event.value != Select.NoSelection:
            value = event.value
            if self._processor:
                value = self._processor(value)
            self._settings[self._key] = value
