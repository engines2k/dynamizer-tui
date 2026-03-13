from textual.widgets import Static


class DynamizerLogo(Static):
    ASCII_ART = " ▌         𝅘𝅥      \n▛▌▌▌▛▌▀▌▛▛▌▌▀▌█▌▛▘\n▙▌▙▌▌▌█▌▌▌▌▌▙▖▙▖▌ \n⸱⸱▄▌⸱•⦁●⦁••⸱⸱⸱⸱⸱⸱⸱"

    def __init__(self):
        super().__init__(self.ASCII_ART, id='ascii-art')
