from textual.app import ComposeResult
from textual.widgets import Button, ProgressBar, Static
from textual.containers import HorizontalGroup

class VolumeControl(HorizontalGroup):

    def __init__(self, total: int = 200, **kwargs):
        super().__init__(**kwargs)
        self.total = total
        self.value = 100
        self._sensitivity = 1.0

    def compose(self) -> ComposeResult:
        yield ProgressBar(total=self.total, show_eta=False, id='volume-bar', show_percentage=False)
        yield Button("-", id='decrement', variant='default')
        yield Button("+", id='increment', variant='default')
        yield Static(content=f'{self.value}%', id='percentage')

    def on_mount(self) -> None:
        self.query_one('#volume-bar', ProgressBar).advance(self.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'increment':
            self._sensitivity = self.app.analyzer.set_sensitivity(self._sensitivity + 0.1) # type: ignore
        elif event.button.id == 'decrement':
            self._sensitivity = self.app.analyzer.set_sensitivity(self._sensitivity - 0.1) # type: ignore
        self.value = int(self._sensitivity * 100)
        self.query_one('#volume-bar', ProgressBar).update(progress=self._sensitivity*100)
        self.query_one('#percentage', Static).content = f'{self.value}%'
