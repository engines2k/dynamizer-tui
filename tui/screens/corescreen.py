from textual import on
from textual.widgets import Static, Label, Select, Switch, Footer, Sparkline
from textual.app import ComposeResult
from textual.containers import VerticalGroup, HorizontalGroup
from tui.screens.basescreen import BaseScreen, ScreenContent
from tui.widgets import AuxControl, VolumeControl, DynamizerLogo


class CORE(BaseScreen):

    CSS_PATH = '../styles/corescreen.tcss'

    def compose(self) -> ComposeResult:
        yield DynamizerLogo()
        yield ScreenContent(CoreOptions())
        yield Footer()

class CoreOptions(VerticalGroup):
    """Core options plus status bar"""

    def compose(self) -> ComposeResult:
        #disabled for better perf on laptop
        #yield Visualizers()
        yield CoreOptionsControls(self)
        yield Static("", id='status')

class Visualizers(HorizontalGroup):

    def compose(self) -> ComposeResult:
        yield VisualizerDisplay(id='analyze-low', feature='kick_harmony')  # type: ignore
        yield VisualizerDisplay(id='analyze-hi-beat', feature='snare_beat', summary_function=max)  # type: ignore
        yield VisualizerDisplay(id='analyze-hi', feature='snare_signal', summary_function=max)  # type: ignore

class VisualizerDisplay(Sparkline):
    """Displays analyzer results reactively."""

    _max_points = 20
    _data_points = []

    def __init__(self, **kwargs):
        self.feature = kwargs.pop('feature')
        super().__init__(**kwargs)
        self._data_points = [0.0] * self._max_points
        self.data = self._data_points
        self.border_title = self.feature
        self.app.analyzer.subscribe(self._on_result)  # type: ignore

    def _on_result(self, features) -> None:
        signal = features.get(self.feature, 0)
        self._data_points = self._data_points[1:] + [float(signal)]
        self.data = self._data_points
        self.border_subtitle = f"{float(signal):.2f}"


class CoreOptionsControls(HorizontalGroup):
    """Selector for input(s) into analyzer."""

    def __init__(self, parent):
        super().__init__()
        self._parent = parent
        self._port_options = self.app.analyzer.audio_connector.get_inputs() # type: ignore


    def compose(self) -> ComposeResult:
        input_items = self._port_options
        power_switch = Switch(id="power")
        power_switch.border_subtitle = '⏻'

        input_select = Select(options=[(i, i) for i in input_items], value=input_items[0])
        input_select.border_title = 'audio src'

        aux_switch = AuxControl(id='aux-mode')
        aux_switch.border_title = '-'

        volume_control = VolumeControl(total=200)
        volume_control.border_subtitle = 'sensitivity'
        volume_control.styles.border_subtitle_align = 'right'

        yield power_switch
        yield input_select
        yield aux_switch
        yield volume_control

    @on(Switch.Changed, '#power')
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
        self.app.analyzer.audio_connector.switch_input(event.value) # type: ignore

    def _update_status(self, n_status: str) -> None:
        self._parent.query_one("#status", Static).update(n_status)

    def action_activate_analyzer(self) -> None:
        """Release the beast."""
        print("ACTIVATE!")

