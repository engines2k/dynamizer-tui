from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Button, Footer, Input, Label, Static, Switch, ProgressBar, Select
from textual.containers import HorizontalGroup, VerticalGroup
from textual.widget import Widget
from textual.reactive import reactive
from master_analyzer import masteranalyzer, MasterAnalyzer
from outputs.terminalwave import SignalAnalyzer
from outputs.wled import LightBuffer


class DynamizerApp(App):
    """An app for realtime music visualization."""
    analyzer: MasterAnalyzer = masteranalyzer

    CSS_PATH = "tui/styles.tcss"

    def compose(self) -> ComposeResult:
        yield CoreOptions()
        yield Footer()

class WLEDOptions(VerticalGroup):

    buffers = [LightBuffer(100, {}), LightBuffer(100, {})]

    def __init__(self):
        super().__init__()
    
    def on_mount(self) -> None:
        self.wled_output = self.app.analyzer._outputs['wled']  # type: ignore
    
    def compose(self) -> ComposeResult:
        for (i, buffer) in enumerate(self.buffers):
            yield WLEDBufferControls(i, buffer)

class WLEDBufferControls(HorizontalGroup):

    def __init__(self, idx, buffer):
        super().__init__()
        self.idx = idx
        self._buffer = buffer

    def compose(self) -> ComposeResult:
        yield Label(content=str(self.idx))
        yield Input(type='integer', value=str(self._buffer.size))

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

class CoreOptions(VerticalGroup):
    """Core options plus status bar"""

    ASCII_ART = " ▌         𝅘𝅥      \n▛▌▌▌▛▌▀▌▛▛▌▌▀▌█▌▛▘\n▙▌▙▌▌▌█▌▌▌▌▌▙▖▙▖▌ \n⸱⸱▄▌⸱•⦁●⦁••⸱⸱⸱⸱⸱⸱⸱"

    def compose(self) -> ComposeResult:
        yield Static(self.ASCII_ART, id='ascii-art')
        yield VisualizerDisplay(id='analyzer-display')  # type: ignore
        yield WLEDOptions()
        yield CoreOptionsControls(self)
        yield Static("Status text here", id='status')

class CoreOptionsControls(HorizontalGroup):
    """Selector for input(s) into analyzer."""

    def __init__(self, parent):
        super().__init__()
        self._parent = parent
        self._port_options = self.app.analyzer.audio_connector.get_available_ports() # type: ignore

    BINDINGS = [('x', 'activate_analyzer', "activate")]

    def compose(self) -> ComposeResult:
        yield Switch()
        yield ProgressBar(total=50, show_eta=False)
        yield Select(options=self._port_options.items())

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

if __name__ == "__main__":
    app = DynamizerApp()
    app.run()
