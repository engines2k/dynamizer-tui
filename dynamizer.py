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

    BINDINGS = [('x', 'activate_analyzer', "activate")]

    def compose(self) -> ComposeResult:
        yield Switch()
        yield ProgressBar(total=50, show_eta=False)
        yield Select(options=[('hello', 'helloval'), ('world', 'worldval')])
        yield Select(options=[('inputr', 'helloval'), ('inputr2', 'worldval')])

    @on(Switch.Changed)
    def toggle_analyzer(self, message: Switch.Changed):
        if message.value == True:
            self.app.analyzer.activate()  # type: ignore
            self._update_status('Dynamizer core start')
        else:
            self._update_status('Dynamizer core stop')

    def _update_status(self, n_status: str) -> None:
        self._parent.query_one("#status", Static).update(n_status)

    def action_activate_analyzer(self) -> None:
        """Release the beast."""
        print("ACTIVATE!")

if __name__ == "__main__":
    app = DynamizerApp()
    app.run()
