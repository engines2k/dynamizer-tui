from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalGroup, HorizontalGroup
from textual.widget import Widget
from textual.widgets import Button, ContentSwitcher, Select, Static, Label, Input, Footer, Collapsible
from textual.binding import Binding
from textual.timer import Timer
from channelmanager import Channel
from outputs.light_buffer import LightEffectBuffer
from outputs.light_device import DeviceBuffer
from outputs.light_device import LightDevice
from outputs.wled import WLEDController
from tui.screens.basescreen import BaseScreen, ScreenContent
from tui.widgets import DynamizerLogo
from tui.widgets.settinginput import SettingInput, processors
from tui.widgets.settingselect import SettingSelect


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

    @property
    def n_channels(self):
        wled_client = self.app.analyzer.outputs['wled']  # type: ignore
        return wled_client.n_channels

    def compose(self) -> ComposeResult:
        if self.n_channels >= 2:
            channel_options = [(c.name, c) for c in Channel]
        else:
            channel_options = [(c.name, c) for c in [Channel.LEFT, Channel.RIGHT, Channel.MID]]
        
        with Collapsible(title=f"⚡ {self._effect.name} ({self._effect.feature})", collapsed=True, id=f"effect-{self.idx}"):
            yield EffectBufferPreview(self._effect, id=f"effect-preview-{self.idx}")
            with HorizontalGroup(classes='device-effect-settings'):
                yield Static(f"[b]channel:[/b]")
                yield Select(
                    options=channel_options,
                    value=Channel(int(self._effect.channel)),
                    id=f"effect-{self.idx}-channel",
                    classes="compact-input"
                )
            with HorizontalGroup(classes='device-effect-settings'):
                yield Static(f"[b]feature:[/b]")
                yield EffectFeatureSelect(self.idx, self._effect)
            with HorizontalGroup():
                yield Static(f"[b]settings:[/b]")
                for name, value in self._effect.settings.items():
                    processor = _get_setting_processor(name)
                    classes = "medium-input" if name == "color" else "compact-input"
                    with VerticalGroup():
                        yield Static(name, id=f"effect-{self.idx}-{name}-label")
                        yield SettingInput(self._effect.settings,
                                           name,
                                           processor=processor,
                                           classes=classes)

    @on(Select.Changed)
    def on_channel_changed(self, event: Select.Changed) -> None:
        if event.select.id == f"effect-{self.idx}-channel":
            if event.value is not None and hasattr(event.value, '__int__'):
                self._effect.channel = Channel(int(event.value))

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

    @property
    def n_channels(self):
        wled_client = self.app.analyzer.outputs['wled']  # type: ignore
        return wled_client.n_channels

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
                for i, device_buffer in enumerate(self._device.buffers):
                    yield DeviceBufferControls(i, device_buffer, self)


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

    def __init__(self, idx, device_buffer: DeviceBuffer, parent_device):
        super().__init__()
        self.idx = idx
        self._device_buffer = device_buffer
        self._parent_device = parent_device
        self._available_effects = self._get_available_effects()

    def _get_available_effects(self):
        wled_client = self.app.analyzer.outputs['wled'] # type: ignore
        return wled_client.effects

    @property
    def n_channels(self):
        wled_client = self.app.analyzer.outputs['wled']  # type: ignore
        return wled_client.n_channels

    def compose(self) -> ComposeResult:
        current_effect = self._device_buffer.effect
        effect_options = [(e.name, e) for e in self._available_effects]
        
        with Collapsible(title=f"⊛ @{self._device_buffer.start} - {self._device_buffer.name}", collapsed=True, id=f"buffer-{self.idx}"):
            with HorizontalGroup():
                yield Static(f"[b]effect:[/b]")
                yield Select(
                    options=effect_options,
                    value=current_effect,
                    id=f"buf-{self.idx}-effect",
                    classes="medium-input"
                )
            with HorizontalGroup():
                yield Static(f"[b]start:[/b]")
                yield SettingInput(
                    self._device_buffer.settings, # type: ignore
                    "start",
                    processor=int,
                    id=f"buf-{self.idx}-start",
                    classes="compact-input"
                )
            with HorizontalGroup():
                yield Static(f"[b]end:[/b]")
                yield Static(f"{self._device_buffer.end}", id=f"buf-{self.idx}-end")

    @on(Select.Changed)
    def on_effect_changed(self, event: Select.Changed) -> None:
        if event.select.id == f"buf-{self.idx}-effect":
            if event.value:
                self._device_buffer.effect = event.value  # type: ignore[assignment]
                self._update_title()

    @on(Input.Changed)
    def on_start_changed(self, event: Input.Changed) -> None:
        if event.input.id == f"buf-{self.idx}-start":
            try:
                int(event.value)
                self._update_title()
                self._update_end()
            except ValueError:
                pass

    def _update_title(self) -> None:
        collapsible = self.query_one(Collapsible)
        collapsible.title = f"⊛ @{self._device_buffer.start} - {self._device_buffer.name}"

    def _update_end(self) -> None:
        end_static = self.query_one(f"#buf-{self.idx}-end", Static)
        end_static.update(f"{self._device_buffer.end}")

    @on(Collapsible.Expanded)
    def on_expanded(self, event: Collapsible.Expanded) -> None:
        collapse_others(self)


def _get_setting_processor(name: str):
    if name == "color":
        return processors.color
    elif name == "multiplier":
        return processors.postive_float
    else:
        return int


def collapse_others(self):
    container = self.parent
    if container:
        for sibling in container.query(type(self)):
            if sibling is not self:
                collapsible = sibling.query_one(Collapsible)
                if collapsible:
                    collapsible.collapsed = True

