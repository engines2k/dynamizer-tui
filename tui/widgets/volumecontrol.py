from textual.app import ComposeResult
from textual.widgets import Button, ProgressBar
from textual.containers import HorizontalGroup
from textual.reactive import reactive


class VolumeControl(HorizontalGroup):
    value = reactive(100)

    def __init__(self, total: int = 200, **kwargs):
        super().__init__(**kwargs)
        self.total = total
        self._sensitivity = 1.0

    def compose(self) -> ComposeResult:
        yield ProgressBar(total=self.total, show_eta=False, id='volume-bar')
        yield Button("-", id='decrement', variant='default')
        yield Button("+", id='increment', variant='default')

    def on_mount(self) -> None:
        self.query_one('#volume-bar', ProgressBar).advance(self.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'increment':
            self._sensitivity = self.app.analyzer.set_sensitivity(self._sensitivity + 0.1)
        elif event.button.id == 'decrement':
            self._sensitivity = self.app.analyzer.set_sensitivity(self._sensitivity - 0.1)
        self.value = int(self._sensitivity * 100)
        self.query_one('#volume-bar', ProgressBar).advance(10 if event.button.id == 'increment' else -10)
