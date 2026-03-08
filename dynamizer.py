from textual.app import App, ComposeResult
from textual.containers import HorizontalGroup, VerticalGroup
from textual.widgets import Static
from master_analyzer import masteranalyzer, MasterAnalyzer
from tui.screens import CORE, WLED


class DynamizerApp(App):
    """An app for realtime music visualization."""
    analyzer: MasterAnalyzer = masteranalyzer

    BINDINGS = [
        ('ctrl+z', 'core_screen', 'CORE'),
        ('ctrl+x', 'wled_screen', 'WLED'),
    ]

    CSS_PATH = "tui/styles/style.tcss"

    SCREENS = {
        'CORE': CORE,
        'WLED': WLED,
    }


    def action_core_screen(self):
        self.switch_screen('CORE')

    def action_wled_screen(self):
        self.switch_screen('WLED')

    def on_mount(self):
        self.push_screen('CORE')


if __name__ == "__main__":
    app = DynamizerApp()
    app.run()
