from textual.app import ComposeResult
from textual.containers import HorizontalGroup
from textual.widgets import Sparkline

class Visualizers(HorizontalGroup):

    def compose(self) -> ComposeResult:
        yield VisualizerDisplay(id='analyze-low', feature='kick_harmony', channel=0)
        yield VisualizerDisplay(id='analyze-hi-beat', feature='snare_beat', summary_function=max, channel=0)
        yield VisualizerDisplay(id='analyze-hi', feature='snare_signal', summary_function=max, channel=0)

class VisualizerDisplay(Sparkline):
    """Displays analyzer results reactively."""

    _max_points = 20
    _data_points = []

    def __init__(self, **kwargs):
        self.feature = kwargs.pop('feature')
        self._channel = kwargs.pop('channel', 0)
        super().__init__(**kwargs)
        self._data_points = [0.0] * self._max_points
        self.data = self._data_points
        self.border_title = self.feature
        self.app.analyzer.subscribe(self._on_result)  # type: ignore

    def _on_result(self, features) -> None:
        if isinstance(features, list):
            features = features[self._channel]
        signal = features.get(self.feature, 0)
        self._data_points = self._data_points[1:] + [float(signal)]
        self.data = self._data_points
        self.border_subtitle = f"{float(signal):.2f}"

