from textual.app import ComposeResult
from textual.widgets import Button, ProgressBar
from textual.containers import HorizontalGroup
from textual.reactive import reactive


class VolumeControl(HorizontalGroup):
    value = reactive(100)

    def __init__(self, total: int = 100, **kwargs):
        super().__init__(**kwargs)
        self.total = total

    def compose(self) -> ComposeResult:
        yield ProgressBar(total=self.total, show_eta=False, id='volume-bar')
        yield Button("-", id='decrement', variant='default')
        yield Button("+", id='increment', variant='default')

    def on_mount(self) -> None:
        self.query_one('#volume-bar', ProgressBar).advance(self.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'increment':
            self.value = min(self.value + 10, self.total)
        elif event.button.id == 'decrement':
            self.value = max(self.value - 10, 0)
        self.query_one('#volume-bar', ProgressBar).advance(10 if event.button.id == 'increment' else -10)
