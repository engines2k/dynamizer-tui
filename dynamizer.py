from textual.app import App
from featureengine import FeatureEngine, featureengine
from tui.screens import CORE, WLED


class DynamizerApp(App):
    """An app for realtime music visualization."""
    analyzer: FeatureEngine = featureengine

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

    def __init__(self):
        super().__init__()
        self._port_options = self.app.analyzer.audio_connector.get_inputs() # type: ignore

    def on_mount(self):
        self.push_screen('CORE')


if __name__ == "__main__":
    app = DynamizerApp()
    app.run()
