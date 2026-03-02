from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Footer, Static, Switch, ProgressBar, Select, TextArea
from textual.containers import HorizontalGroup, VerticalGroup
from master_analyzer import masteranalyzer, MasterAnalyzer


class DynamizerApp(App):
    """An app for realtime music visualization."""
    analyzer: MasterAnalyzer = masteranalyzer

    CSS_PATH = "tui/styles.tcss"

    def compose(self) -> ComposeResult:
        yield CoreOptions()
        yield Footer()

class CoreOptions(VerticalGroup):
    """Core options plus status bar"""

    def compose(self) -> ComposeResult:
        yield CoreOptionsControls(self)
        yield Static("Status text here", id='status')

class CoreOptionsControls(HorizontalGroup):
    """Selector for input(s) into analyzer."""

    def __init__(self, parent):
        super().__init__()
        self._parent = parent
        self._port_options = self.app.analyzer.get_available_ports() # type: ignore

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
