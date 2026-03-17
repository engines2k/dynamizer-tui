from textual import on
from textual.app import ComposeResult
from textual.widgets import Button, ProgressBar, Static, Switch
from textual.containers import VerticalGroup

class AuxControl(VerticalGroup):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.value = 100

    def compose(self) -> ComposeResult:
        yield Static(content=f'aux')
        yield Switch(id='aux-mode')

    @on(Switch.Changed, '#aux-mode')
    def toggle_connector_aux_mode(self, event: Switch.Changed):
        if event.value == False:
            self.app.analyzer.audio_connector.input_is_aux = False #type: ignore
        else:
            self.app.analyzer.audio_connector.input_is_aux = True #type: ignore


    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'increment':
            self._sensitivity = self.app.analyzer.set_sensitivity(self._sensitivity + 0.1) # type: ignore
        elif event.button.id == 'decrement':
            self._sensitivity = self.app.analyzer.set_sensitivity(self._sensitivity - 0.1) # type: ignore
        self.value = int(self._sensitivity * 100)
        self.query_one('#volume-bar', ProgressBar).update(progress=self._sensitivity*100)
        self.query_one('#percentage', Static).content = f'{self.value}%'
