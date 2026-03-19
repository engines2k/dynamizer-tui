from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalGroup, HorizontalGroup, Grid
from textual.widgets import Static, Label, Input, Footer, Collapsible
from outputs.light_buffer import LightBuffer, LightDevice
from outputs.wled import WLEDController
from tui.screens.basescreen import BaseScreen
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
        return self.app.analyzer.outputs['wled']
    
    def compose(self) -> ComposeResult:
        yield VerticalGroup(*[
            ControllerControls(i, controller) 
            for (i, controller) in enumerate(self.wled_client.controllers)
        ])


class ControllerControls(VerticalGroup):

    def __init__(self, idx, controller):
        super().__init__()
        self.idx = idx
        self._controller: WLEDController = controller

    def compose(self) -> ComposeResult:
        n_devices = len(self._controller.light_devices)
        controller_hosts = ', '.join([f"{d['host']}:{d['port']}" for d in self._controller.destinations])
        
        with Collapsible(title=f"Controller {self.idx}", collapsed=True, id=f"ctrl-{self.idx}"):
            yield Static(f"[b]Hosts:[/b] {controller_hosts}", id=f"ctrl-summary-{self.idx}")
            yield Static(f"[b]Devices:[/b] {n_devices}", id=f"ctrl-devices-count-{self.idx}")
            yield CtrlDestinationControls(self._controller.destinations)
            yield VerticalGroup(
                *[CtrlLightDeviceControls(i, device, self) for i, device in enumerate(self._controller.light_devices)],
                id=f"ctrl-{self.idx}-devices"
            )

    @on(Collapsible.Expanded)
    def on_expanded(self, event: Collapsible.Expanded) -> None:
        parent = self.parent
        if parent:
            for sibling in parent.query(ControllerControls):
                if sibling is not self:
                    collapsible = sibling.query_one(Collapsible)
                    if collapsible:
                        collapsible.collapsed = True


class CtrlDestinationControls(VerticalGroup):

    def __init__(self, destinations):
        super().__init__()
        self._destinations = destinations
    
    def compose(self) -> ComposeResult:
        hosts = ', '.join([f"{d['host']}:{d['port']}" for d in self._destinations])
        yield Static(f"[b]Destinations:[/b] {hosts}")


class CtrlLightDeviceControls(VerticalGroup):

    def __init__(self, idx, device, parent_controller):
        super().__init__()
        self.idx = idx
        self._device: LightDevice = device
        self._parent_controller = parent_controller

    def compose(self) -> ComposeResult:
        n_buffers = len(self._device.buffers)
        
        with Collapsible(title=f"Device {self.idx}", collapsed=True, id=f"device-{self.idx}"):
            yield Static(f"[b]Buffers:[/b] {n_buffers}", id=f"device-summary-{self.idx}")
            yield HorizontalGroup(
                Label("LEDs:"),
                Input(type='integer', value=str(self._device.n_leds), id='led-count', classes="compact-input"),
            )
            yield VerticalGroup(
                *[CtrlLightBufferControls(i, pos, buf, self) for i, (pos, buf) in enumerate(self._device.buffers)],
                id=f"device-{self.idx}-buffers"
            )

    @on(Input.Changed)
    def on_led_count_changed(self, event: Input.Changed) -> None:
        if event.input.id == 'led-count':
            try:
                n_leds = int(event.value)
                if n_leds > 0:
                    self._device.set_n_leds(n_leds)
                    self._update_summary()
            except ValueError:
                pass

    def _update_summary(self) -> None:
        n_buffers = len(self._device.buffers)
        summary = self.query_one(f"#device-summary-{self.idx}", Static)
        summary.update(f"[b]Buffers:[/b] {n_buffers}")

    @on(Collapsible.Expanded)
    def on_expanded(self, event: Collapsible.Expanded) -> None:
        parent_containers = self.parent
        if parent_containers:
            for sibling in parent_containers.query(CtrlLightDeviceControls):
                if sibling is not self:
                    collapsible = sibling.query_one(Collapsible)
                    if collapsible:
                        collapsible.collapsed = True


class CtrlLightBufferControls(VerticalGroup):

    def __init__(self, idx, position, light_buffer, parent_device):
        super().__init__()
        self.idx = idx
        self.position = position
        self._light_buffer: LightBuffer = light_buffer
        self._parent_device = parent_device

    def compose(self) -> ComposeResult:
        settings_summary = ', '.join([f"{k}={v}" for k, v in self._light_buffer.settings.items()])
        
        with Collapsible(title=f"Buffer {self.idx} (pos={self.position})", collapsed=True, id=f"buffer-{self.idx}"):
            yield Static(f"[b]Settings:[/b] {settings_summary}", id=f"buffer-summary-{self.idx}")
            for name, value in self._light_buffer.settings.items():
                input_widget = self._make_input(name, value)
                yield HorizontalGroup(
                    Static(name, id=f"buf-{self.idx}-{name}-label"),
                    input_widget,
                )

    def _make_input(self, name: str, value):
        input_id = f"buf-{self.idx}-{name}"
        if name == 'color':
            display_value = ','.join(str(x) for x in value)
            return Input(value=display_value, id=input_id, classes="compact-input")
        elif name == 'multiplier':
            return Input(value=str(value), id=input_id, classes="compact-input")
        else:
            return Input(type='integer', value=str(value), id=input_id, classes="compact-input")

    @on(Input.Changed)
    def on_setting_changed(self, event: Input.Changed) -> None:
        if event.input.id and event.input.id.startswith(f"buf-{self.idx}-"):
            setting_name = event.input.id.replace(f"buf-{self.idx}-", "")
            try:
                if setting_name == 'color':
                    parts = event.value.split(',')
                    if len(parts) == 3:
                        color = tuple(max(0, min(255, int(x.strip()))) for x in parts)
                        self._light_buffer.settings[setting_name] = color
                        self._update_summary()
                elif setting_name == 'multiplier':
                    value = float(event.value)
                    if value >= 0:
                        self._light_buffer.settings[setting_name] = value
                        self._update_summary()
                else:
                    value = int(event.value)
                    self._light_buffer.settings[setting_name] = value
                    self._update_summary()
            except ValueError:
                pass

    def _update_summary(self) -> None:
        settings_summary = ', '.join([f"{k}={v}" for k, v in self._light_buffer.settings.items()])
        summary = self.query_one(f"#buffer-summary-{self.idx}", Static)
        summary.update(f"[b]Settings:[/b] {settings_summary}")

    @on(Collapsible.Expanded)
    def on_expanded(self, event: Collapsible.Expanded) -> None:
        buffers_container = self.parent
        if buffers_container:
            for sibling in buffers_container.query(CtrlLightBufferControls):
                if sibling is not self:
                    collapsible = sibling.query_one(Collapsible)
                    if collapsible:
                        collapsible.collapsed = True
