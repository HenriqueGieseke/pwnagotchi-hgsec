#!/usr/bin/env python3
"""Button actions. Requires root and an explicitly configured deauth value."""
import json
import logging
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import tomllib

CONFIG = Path('/etc/pwnagotchi/config.toml')
STATUS = Path('/run/pwnagotchi-hgsec/status.json')
ASSIGNMENT = re.compile(r'^([ \t]*personality\.deauth[ \t]*=[ \t]*)(true|false)([ \t]*(?:#[^\n]*)?)$', re.MULTILINE)


def notify(message, duration=8):
    STATUS.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    temporary = STATUS.with_suffix('.tmp')
    temporary.write_text(json.dumps({'message': message, 'until': time.time() + duration, 'id': time.time_ns()}))
    temporary.replace(STATUS)


def toggle_config(path):
    content = path.read_text()
    parsed = tomllib.loads(content)
    matches = list(ASSIGNMENT.finditer(content))
    value = parsed.get('personality', {}).get('deauth')
    if len(matches) != 1 or type(value) is not bool or matches[0].group(2) != str(value).lower():
        raise ValueError('Expected one explicit personality.deauth = true/false in config.toml')
    new_value = not value
    updated = ASSIGNMENT.sub(lambda m: m.group(1) + str(new_value).lower() + m.group(3), content, count=1)
    # Preserve mode and owner and atomically replace only after the entire file is written.
    st = path.stat()
    fd, name = tempfile.mkstemp(prefix='.hgsec-', dir=path.parent)
    try:
        os.fchmod(fd, st.st_mode & 0o7777)
        os.fchown(fd, st.st_uid, st.st_gid)
        with os.fdopen(fd, 'w') as out:
            fd = -1
            out.write(updated)
            out.flush()
            os.fsync(out.fileno())
        os.replace(name, path)
    finally:
        if fd >= 0:
            os.close(fd)
        if os.path.exists(name):
            os.unlink(name)
    return new_value


def run(*args):
    subprocess.run(args, check=True, timeout=60)


def main(action):
    if action == 'shutdown':
        notify('Shutting down...', 8)
        time.sleep(3)
        run('/usr/bin/systemctl', 'poweroff')
    elif action == 'toggle':
        if not Path('/etc/pwnagotchi/hgsec-deauth-enabled').is_file():
            raise RuntimeError('Deauthentication control is not enabled')
        enabled = toggle_config(CONFIG)
        notify('Applying deauth setting...', 8)
        time.sleep(3)
        # Mirrors the device's existing restart sequence; report command failures.
        run('/usr/bin/systemctl', 'stop', 'pwnagotchi', 'bettercap')
        run('/usr/bin/monstart')
        run('/usr/sbin/ip', 'link', 'set', 'wlan0', 'down')
        run('/usr/bin/systemctl', 'start', 'bettercap')
        time.sleep(5)
        run('/usr/bin/systemctl', 'start', 'pwnagotchi')
        notify('Deauthentication ' + ('enabled' if enabled else 'disabled'), 20)
    else:
        raise ValueError('Unknown action')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        main(sys.argv[1] if len(sys.argv) == 2 else '')
    except Exception:
        logging.exception('Button action failed')
        try:
            notify('Button action failed', 20)
        except Exception:
            logging.exception('Unable to display failure')
        sys.exit(1)
