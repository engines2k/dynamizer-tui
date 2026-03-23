from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalGroup, HorizontalGroup
from textual.widget import Widget
from textual.widgets import Button, ContentSwitcher, Select, Static, Label, Input, Footer, Collapsible
from textual.binding import Binding
from textual.timer import Timer
from outputs.light_buffer import LightEffectBuffer
from outputs.light_device import LightDevice
from outputs.wled import WLEDController
from tui.screens.basescreen import BaseScreen, ScreenContent
from tui.widgets import DynamizerLogo


class EffectBufferPreview(Static):
    def __init__(self, effect_buffer: LightEffectBuffer, max_width: int = 60, **kwargs):
        super().__init__(**kwargs)
        self._effect_buffer = effect_buffer
        self._max_width = max_width
        self._last_frame = None
        self.layout_refresh = False
        self._cached_chars: list = [None] * max_width
        self._timer: Timer | None = None

    def on_mount(self) -> None:
        self._timer = self.app.set_interval(1 / 20, self._update_preview)
        self._update_preview()

    def on_unmount(self) -> None:
        if self._timer:
            self._timer.stop()
            self._timer = None

    def _update_preview(self) -> None:
        frame = self._effect_buffer.frame

        if frame is self._last_frame:
            return

        self._last_frame = frame
        self._render_preview(frame)

    def _render_preview(self, frame) -> None:
        frame_len = len(frame)
        if frame_len == 0:
            self.update("")
            return

        step = max(1, frame_len // self._max_width)
        chars = self._cached_chars
        count = 0

        for i in range(0, frame_len - 2, step * 3):
            if count >= self._max_width:
                break

            b, r, g = frame[i], frame[i + 1], frame[i + 2]
            chars[count] = f"[rgb({r},{g},{b})]▄[/]"
            count += 1

        result = "".join(chars[:count])
        self.update(result)


class WLED(BaseScreen):

    CSS_PATH = '../styles/wledscreen.tcss'
    BINDINGS = [Binding("escape", "collapse_focused", "collapse", priority=True)]

    def compose(self) -> ComposeResult:
        yield DynamizerLogo()
        yield ScreenContent(WLEDOptions())
        yield Footer()

    def action_collapse_focused(self) -> None:
        ele = self.focused
        if ele is None:
            return
        while ele:
            if isinstance(ele, Collapsible) and not ele.collapsed:
                ele.collapsed = True
                ele._title.focus()
                break
            ele = ele.parent


class WLEDOptions(VerticalGroup):

    @property
    def wled_client(self):
        return self.app.analyzer.outputs['wled'] # type: ignore
    
    def compose(self) -> ComposeResult:
        with VerticalGroup():
            with HorizontalGroup(id='content-buttons'):
                yield Button('controllers', id='view-controllers')
                yield Button('effects', id='view-effects')
            with ContentSwitcher(initial='view-controllers'):
                with VerticalGroup(id='view-controllers'):
                    for (i, controller) in enumerate(self.wled_client.controllers):
                        yield ControllerControls(i, controller) 
                with VerticalGroup(id='view-effects'):
                    for i, effect in enumerate(self.wled_client.effects):
                        yield EffectControls(i, effect)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.query_one(ContentSwitcher).current = event.button.id  


class EffectControls(VerticalGroup):

    def __init__(self, idx: int, effect: LightEffectBuffer):
        super().__init__()
        self.idx = idx
        self._effect = effect

    def compose(self) -> ComposeResult:
        with Collapsible(title=f"⚡ {self._effect.name} ({self._effect.feature})", collapsed=True, id=f"effect-{self.idx}"):
            yield EffectBufferPreview(self._effect, id=f"effect-preview-{self.idx}")
            with HorizontalGroup(classes='device-effect-settings'):
                yield Static(f"[b]feature:[/b]")
                yield EffectFeatureSelect(self.idx, self._effect)
            with HorizontalGroup():
                yield Static(f"[b]settings:[/b]")
                for name, value in self._effect.settings.items():
                    input_widget = self._make_input(name, value)
                    with VerticalGroup():
                        yield Static(name, id=f"effect-{self.idx}-{name}-label")
                        yield input_widget

    def _make_input(self, name: str, value):
        input_id = f"effect-{self.idx}-{name}"
        if name == 'color':
            display_value = ','.join(str(x) for x in value)
            return Input(value=display_value, id=input_id, classes="medium-input")
        elif name == 'multiplier':
            return Input(value=str(value), id=input_id, classes="compact-input")
        else:
            return Input(type='integer', value=str(value), id=input_id, classes="compact-input")

    @on(Input.Changed)
    def on_setting_changed(self, event: Input.Changed) -> None:
        if event.input.id and event.input.id.startswith(f"effect-{self.idx}-"):
            setting_name = event.input.id.replace(f"effect-{self.idx}-", "")
            try:
                if setting_name == 'feature':
                    self._effect.feature = event.value
                if setting_name == 'color':
                    parts = event.value.split(',')
                    if len(parts) == 3:
                        color = tuple(max(0, min(255, int(x.strip()))) for x in parts)
                        self._effect.settings[setting_name] = color
                elif setting_name == 'multiplier':
                    value = float(event.value)
                    if value >= 0:
                        self._effect.settings[setting_name] = value
                else:
                    value = int(event.value)
                    self._effect.settings[setting_name] = value
            except ValueError:
                pass

    @on(Collapsible.Expanded)
    def on_expanded(self, event: Collapsible.Expanded) -> None:
        collapse_others(self)


class EffectFeatureSelect(Widget):
    
    AVAILABLE_FEATURES = [
        "kick_signal",
        "kick_beat",
        "kick_harmony",
        "snare_signal",
        "snare_beat",
        "snare_harmony",
    ]
    
    def __init__(self, idx: int, effect: LightEffectBuffer):
        super().__init__()
        self.idx = idx
        self._effect = effect

    def compose(self) -> ComposeResult:
        current_feature = self._effect.feature
        yield Select(
            options= [(f, f) for f in self.AVAILABLE_FEATURES ],
            value=current_feature,
            id=f"effect-{self.idx}-feature",
            classes="medium-input"
        )

    @on(Select.Changed)
    def on_feature_changed(self, event: Select.Changed) -> None:
        if event.value:
            self._effect.feature = str(event.value)  # type: ignore[assignment]
            collapsible = self.ancestors[1]
            if collapsible and isinstance(collapsible, Collapsible):
                collapsible.title = f"⚡ {self._effect.name} ({self._effect.feature})"


class ControllerControls(VerticalGroup):

    def __init__(self, idx, controller):
        super().__init__()
        self.idx = idx
        self._controller: WLEDController = controller

    def compose(self) -> ComposeResult:
        n_devices = len(self._controller.devices)
        controller_hosts = ', '.join([f"{d['host']}:{d['port']}" for d in self._controller.destinations])
        
        with Collapsible(title=f"📟 controller {self.idx}: {self._controller.name}", collapsed=True, id=f"ctrl-{self.idx}"):
            yield Static(f"[b]hosts:[/b] {controller_hosts}", id=f"ctrl-summary-{self.idx}")
            yield Static(f"[b]devices:[/b] {n_devices}", id=f"ctrl-devices-count-{self.idx}")
            yield CtrlDestinationControls(self._controller.destinations)
            with VerticalGroup(id=f"ctrl-{self.idx}-devices"):
                for i, device in enumerate(self._controller.devices):
                    yield CtrlLightDeviceControls(i, device, self) 
                

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
        yield Static(f"[b]destinations:[/b] {hosts}")


class CtrlLightDeviceControls(VerticalGroup):

    def __init__(self, idx, device, parent_controller):
        super().__init__()
        self.idx = idx
        self._device: LightDevice = device
        self._parent_controller = parent_controller

    def compose(self) -> ComposeResult:
        n_buffers = len(self._device.buffers)
        
        with Collapsible(title=f"💡device {self.idx}", collapsed=True, id=f"device-{self.idx}"):
            yield Static(f"[b]buffers:[/b] {n_buffers}", id=f"device-summary-{self.idx}")
            with HorizontalGroup():
                Label("LEDs:")
                Input(type='integer', value=str(self._device.n_leds), id='led-count', classes="compact-input")
            with VerticalGroup(id=f"device-{self.idx}-buffers"):
                for i, (pos, buf) in enumerate(self._device.buffers):
                    yield DeviceBufferControls(i, pos, buf, self)


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
        summary.update(f"[b]buffers:[/b] {n_buffers}")

    @on(Collapsible.Expanded)
    def on_expanded(self, _) -> None:
        collapse_others(self)


class DeviceBufferControls(HorizontalGroup):

    def __init__(self, idx, position, light_buffer, parent_device):
        super().__init__()
        self.idx = idx
        self.position = position
        self._light_buffer: LightEffectBuffer = light_buffer
        self._parent_device = parent_device

    def compose(self) -> ComposeResult:
        with Collapsible(title=f"⊛ @{self.position} - {self._light_buffer.name}", collapsed=True, id=f"buffer-{self.idx}"):
            with HorizontalGroup():
                yield Static(f"[b]settings:[/b]")
                for name, value in self._light_buffer.settings.items():
                    input_widget = self._make_input(name, value)
                    with VerticalGroup(classes='device-buffer-settings'):
                        yield Static(name, id=f"buf-{self.idx}-{name}-label")
                        yield input_widget

    def _make_input(self, name: str, value):
        input_id = f"buf-{self.idx}-{name}"
        if name == 'color':
            display_value = ','.join(str(x) for x in value)
            return Input(value=display_value, id=input_id, classes="medium-input")
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
                elif setting_name == 'multiplier':
                    value = float(event.value)
                    if value >= 0:
                        self._light_buffer.settings[setting_name] = value
                else:
                    value = int(event.value)
                    self._light_buffer.settings[setting_name] = value
            except ValueError:
                pass

    @on(Collapsible.Expanded)
    def on_expanded(self, event: Collapsible.Expanded) -> None:
        collapse_others(self)


def collapse_others(self):
    container = self.parent
    if container:
        for sibling in container.query(type(self)):
            if sibling is not self:
                collapsible = sibling.query_one(Collapsible)
                if collapsible:
                    collapsible.collapsed = True

