import logging
import pwnagotchi.ui.fonts as fonts
from pwnagotchi.ui.hw.base import DisplayImpl

class LcdHat(DisplayImpl):
    def __init__(self, config):
        super(LcdHat, self).__init__(config, 'lcdhat')

    def layout(self):
        fonts.setup(12, 11, 12, 37, 27, 11)
        self._layout['width'] = 240
        self._layout['height'] = 240
        self._layout['face'] = (30, 100)
        self._layout['name'] = (150, 40)
        self._layout['channel'] = (0, 0)
        self._layout['aps'] = (40, 0)
        self._layout['uptime'] = (0, 17)
        self._layout['line1'] = [0, 30, 240, 30]
        self._layout['line2'] = [0, 219, 240, 219]
        self._layout['friend_face'] = (0, 130)
        self._layout['friend_name'] = (40, 130)
        self._layout['shakes'] = (0, 220)
        self._layout['mode'] = (210, 220)
        self._layout['status'] = {
            'pos': (0, 100),
            'font': fonts.status_font(fonts.Medium),
            'max': 20
        }
        return self._layout

    def initialize(self):
        logging.info("initializing lcdhat display")
        from pwnagotchi.ui.hw.libs.waveshare.lcd.lcdhat.epd import EPD
        self._display = EPD()
        self._display.init()
        self._display.clear()

    def render(self, canvas):
        self._display.display(canvas)

    def clear(self):
        self._display.clear()
