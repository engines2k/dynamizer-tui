from textual.screen import Screen
from outputs.terminalwave import SignalAnalyzer
from textual import on
from textual.widgets import Header, Static, Label, Select, Switch, Footer
from textual.app import ComposeResult
from textual.containers import VerticalGroup, HorizontalGroup
from textual.reactive import reactive
from tui.screens.basescreen import BaseScreen, ScreenContent
from tui.widgets import DynamizerLogo
from tui.widgets.volumecontrol import VolumeControl


class CORE(BaseScreen):

    CSS_PATH = '../styles/corescreen.tcss'

    def compose(self) -> ComposeResult:
        yield DynamizerLogo()
        yield ScreenContent(CoreOptions())
        yield Footer()

class CoreOptions(VerticalGroup):
    """Core options plus status bar"""

    def compose(self) -> ComposeResult:
        yield VisualizerDisplay(id='analyzer-display')  # type: ignore
        yield CoreOptionsControls(self)
        yield Static("", id='status')


class VisualizerDisplay(Static):
    """Displays analyzer results reactively."""

    kick_signal = reactive("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app.analyzer.subscribe(self._on_result) # type: ignore
        self.visualizer = SignalAnalyzer('kick_signal')

    def _on_result(self, features) -> None:
        self.visualizer.send(features)
        self.kick_signal = self.visualizer.result

    def watch_kick_signal(self, value: str) -> None:
        self.update(value)


class CoreOptionsControls(HorizontalGroup):
    """Selector for input(s) into analyzer."""

    def __init__(self, parent):
        super().__init__()
        self._parent = parent
        self._port_options = self.app.analyzer.audio_connector.get_available_ports() # type: ignore


    def compose(self) -> ComposeResult:
        input_items = self._port_options.items()
        first_value = list(self._port_options.values())[0] if self._port_options else None
        power_switch = Switch(id="power")
        power_switch.border_subtitle = '⏻'
        input_select = Select(options=input_items, value=first_value)
        input_select.border_title = 'audio src'
        volume_control = VolumeControl(total=100)
        volume_control.border_subtitle = 'sensitivity'
        volume_control.styles.border_subtitle_align = 'right'

        yield power_switch
        yield input_select
        yield volume_control

    @on(Switch.Changed)
    def toggle_analyzer(self, event: Switch.Changed):
        if event.value == False:
            self._update_status('Dynamizer core paused')
            self.app.analyzer.toggle_pause() #type: ignore

        elif self.app.analyzer.active: #type: ignore
            self.app.analyzer.toggle_pause() #type: ignore
            self._update_status('Dynamizer core resumed')

        else:
            self._update_status('Dynamizer core ON')
            self.app.analyzer.activate()  # type: ignore

    @on(Select.Changed)
    def switch_analyzer_input(self, event: Select.Changed):
        self.app.analyzer.audio_connector.change_input(event.value) # type: ignore

    def _update_status(self, n_status: str) -> None:
        self._parent.query_one("#status", Static).update(n_status)

    def action_activate_analyzer(self) -> None:
        """Release the beast."""
        print("ACTIVATE!")

