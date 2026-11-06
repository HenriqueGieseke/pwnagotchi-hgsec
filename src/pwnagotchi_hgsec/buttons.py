#!/usr/bin/env python3
"""Read the HAT buttons; dispatch one action after a continuous hold."""
import logging
import subprocess
import time

PINS = {20: 'toggle', 16: 'shutdown'}
HOLD_SECONDS = 2.0
POLL_SECONDS = 0.05


class HoldDetector:
    def __init__(self):
        self.started = {}
        self.fired = set()

    def update(self, pin, pressed, now):
        if not pressed:
            self.started.pop(pin, None)
            self.fired.discard(pin)
            return False
        if pin not in self.started:
            self.started[pin] = now
        if pin not in self.fired and now - self.started[pin] >= HOLD_SECONDS:
            self.fired.add(pin)
            return True
        return False


def main():
    import lgpio
    logging.basicConfig(level=logging.INFO)
    chip = lgpio.gpiochip_open(0)
    try:
        for pin in PINS:
            lgpio.gpio_claim_input(chip, pin, lgpio.SET_PULL_UP)
        detector = HoldDetector()
        active = None
        while True:
            for pin, action in PINS.items():
                if detector.update(pin, lgpio.gpio_read(chip, pin) == 0, time.monotonic()):
                    if active is not None and active.poll() is None:
                        logging.warning('Action already running; ignoring %s', action)
                        continue
                    active = subprocess.Popen(['/usr/bin/python3', '/usr/local/lib/pwnagotchi-hgsec/actions.py', action])
            time.sleep(POLL_SECONDS)
    finally:
        lgpio.gpiochip_close(chip)


if __name__ == '__main__':
    main()
