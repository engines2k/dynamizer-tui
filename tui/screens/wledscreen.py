from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalGroup, HorizontalGroup
from textual.widgets import Static, Label, Input, Footer
from tui.screens.basescreen import BaseScreen, ScreenContent
from tui.widgets import DynamizerLogo


class WLED(BaseScreen):

    CSS_PATH = '../styles/wledscreen.tcss'

    def compose(self) -> ComposeResult:
        yield DynamizerLogo()
        yield WLEDOptions()
        yield Footer()


class WLEDOptions(VerticalGroup):

    @property
    def wled_output(self):
        return self.app.analyzer._outputs['wled']  # type: ignore
    
    def compose(self) -> ComposeResult:
        for (i, device) in enumerate(self.wled_output.light_devices):
            yield WLEDLightDeviceControls(i, device)


class WLEDLightDeviceControls(HorizontalGroup):

    def __init__(self, idx, device):
        super().__init__()
        self.idx = idx
        self._device = device

    def compose(self) -> ComposeResult:
        yield Label(content=f"Device {self.idx}")
        yield Input(type='integer', value=str(self._device.n_leds), id='led-count')

    @on(Input.Changed)
    def on_led_count_changed(self, event: Input.Changed) -> None:
        if event.input.id == 'led-count':
            try:
                n_leds = int(event.value)
                if n_leds > 0:
                    self._device.set_n_leds(n_leds)
            except ValueError:
                pass

