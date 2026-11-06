"""Pwnagotchi plugin: display button action messages through its UI."""
import json
import logging
from pathlib import Path
import threading
import time

import pwnagotchi.plugins as plugins

STATUS = Path('/run/pwnagotchi-hgsec/status.json')


class HgsecStatus(plugins.Plugin):
    __author__ = 'Pwnagotchi HGSEC contributors'
    __version__ = '1.0.0'
    __license__ = 'GPL3'
    __description__ = 'Shows LCD HAT button action messages.'

    def on_ui_setup(self, ui):
        self.stop = threading.Event()
        self.worker = threading.Thread(target=self.watch, args=(ui,), daemon=True)
        self.worker.start()

    def watch(self, ui):
        previous_id = None
        previous_status = None
        shown = None
        expiry = 0
        while not self.stop.wait(0.25):
            try:
                data = json.loads(STATUS.read_text())
                if data['id'] != previous_id and data['until'] > time.time():
                    previous_id = data['id']
                    previous_status = ui.get('status')
                    shown = data['message']
                    expiry = data['until']
                    ui.update(force=True, new_data={'status': shown})
            except (OSError, ValueError, KeyError, TypeError):
                pass
            except Exception:
                logging.exception('HGSEC: unable to show status')
            if shown is not None and time.time() >= expiry:
                try:
                    if ui.get('status') == shown:
                        ui.update(force=True, new_data={'status': previous_status})
                except Exception:
                    logging.exception('HGSEC: unable to restore status')
                shown = None

    def on_unload(self, ui):
        if hasattr(self, 'stop'):
            self.stop.set()
