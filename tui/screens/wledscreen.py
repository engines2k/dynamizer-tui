from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalGroup, HorizontalGroup
from textual.widgets import Static, Label, Input, Footer
from outputs.light_buffer import LightBuffer, LightDevice
from outputs.wled import WLEDController
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
    def wled_client(self):
        return self.app.analyzer.outputs['wled']  # type: ignore
    
    def compose(self) -> ComposeResult:
        yield VerticalGroup(*[ControllerControls(i, controller) for (i, controller) in enumerate(self.wled_client.controllers)])


class ControllerControls(VerticalGroup):

    def __init__(self, idx, controller):
        super().__init__()
        self.idx = idx
        self._controller: WLEDController = controller

    def compose(self) -> ComposeResult:
        controller_hosts = ', '.join([d['host'] for d in self._controller.destinations ])
        yield Label(content=f"controller {self.idx} ({controller_hosts})")
        yield CtrlDestinationControls(self._controller.destinations)
        yield VerticalGroup(*[CtrlLightDeviceControls(device) for device in self._controller.light_devices])
        # buffers


class CtrlDestinationControls(HorizontalGroup):

    def __init__(self, destinations):
        super().__init__()
        self._destinations = destinations
    
    def compose(self) -> ComposeResult:
        for destination in self._destinations:
            yield Static(f'{destination['host']} {destination['port']}')


class CtrlLightDeviceControls(VerticalGroup):

    def __init__(self, device):
        super().__init__()
        self._device: LightDevice = device
    
    def compose(self) -> ComposeResult:
        yield Input(type='integer', value=str(self._device.n_leds), id='led-count')
        for (pos, buffer) in self._device.buffers:
            yield Static('position')
            yield Input(type='integer', value=str(pos))
            yield CtrlLightBufferControls(buffer)

    @on(Input.Changed)
    def on_led_count_changed(self, event: Input.Changed) -> None:
        if event.input.id == 'led-count':
            try:
                n_leds = int(event.value)
                if n_leds > 0:
                    self._device.set_n_leds(n_leds)
            except ValueError:
                pass


class CtrlLightBufferControls(VerticalGroup):

    def __init__(self, light_buffer):
        super().__init__()
        self._light_buffer: LightBuffer = light_buffer
    
    def compose(self) -> ComposeResult:
        for name, value in self._light_buffer.settings.items():
            yield Static(name)
            yield Input(type='integer', value=str(value), id=name)
