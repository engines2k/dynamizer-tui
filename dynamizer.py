from textual.app import App, ComposeResult
from textual.widgets import Footer, Switch, ProgressBar, Select
from textual.containers import HorizontalGroup

class CoreOptions(HorizontalGroup):
    """Selector for input(s) into analyzer."""

    BINDINGS = [('x', 'activate_analyzer', "activate")]

    def compose(self) -> ComposeResult:
        yield Switch()
        yield ProgressBar(total=50, show_eta=False)
        yield Select(options=[('hello', 'helloval'), ('world', 'worldval')])
        yield Select(options=[('inputr', 'helloval'), ('inputr2', 'worldval')])

    def action_activate_analyzer(self) -> None:
        """Release the beast."""
        print("ACTIVATE!")


class DynamizerApp(App):
    """An app for realtime music visualization."""

    CSS_PATH = "tui/styles.tcss"

    def compose(self) -> ComposeResult:
        yield CoreOptions()
        yield Footer()

if __name__ == "__main__":
    app = DynamizerApp()
    app.run()
