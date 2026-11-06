#!/usr/bin/env python3
"""Install or roll back HGSEC on an offline, writable Linux root partition."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time
import tomllib

ROOT = Path('/tmp/pwnagotchi-sd')
PROJECT = Path(__file__).resolve().parent.parent
BACKUP = ROOT / 'var/backups/pwnagotchi-hgsec-install'
CONFIG = 'etc/pwnagotchi/config.toml'
OLD_LINK = 'etc/systemd/system/multi-user.target.wants/lcdhat-buttons.service'
NEW_LINK = 'etc/systemd/system/multi-user.target.wants/pwnagotchi-hgsec-buttons.service'
FILES = {
    'src/pwnagotchi_hgsec/buttons.py': 'usr/local/lib/pwnagotchi-hgsec/buttons.py',
    'src/pwnagotchi_hgsec/actions.py': 'usr/local/lib/pwnagotchi-hgsec/actions.py',
    'src/hgsec_status.py': 'usr/local/share/pwnagotchi/custom-plugins/hgsec_status.py',
    'systemd/pwnagotchi-hgsec-buttons.service': 'etc/systemd/system/pwnagotchi-hgsec-buttons.service',
}
MARKER = 'etc/pwnagotchi/hgsec-deauth-enabled'
PATHS = [CONFIG, OLD_LINK, NEW_LINK, MARKER, *FILES.values()]


def exists(path):
    return path.exists() or path.is_symlink()


def verify_target():
    if os.geteuid() != 0:
        raise RuntimeError('Run with sudo on the computer, not on the Pi.')
    import subprocess
    result = subprocess.run(['findmnt', '-n', '-o', 'SOURCE,OPTIONS', '--mountpoint', str(ROOT)], text=True, capture_output=True, check=True)
    source, options = result.stdout.strip().split(None, 1)
    if os.path.realpath(source) != os.path.realpath('/dev/sdc2') or 'rw' not in options.split(','):
        raise RuntimeError('Expected /dev/sdc2 mounted read-write at /tmp/pwnagotchi-sd; check lsblk first.')
    if not (ROOT / CONFIG).is_file() or not (ROOT / 'usr/local/bin/lcdhat-buttons').is_file():
        raise RuntimeError('Expected Pwnagotchi card files were not found.')


def save():
    BACKUP.mkdir(mode=0o700, parents=True, exist_ok=False)
    records = {}
    for rel in PATHS:
        original = ROOT / rel
        if original.is_symlink():
            records[rel] = {'kind': 'link', 'target': os.readlink(original)}
        elif original.is_file():
            copy = BACKUP / 'files' / rel
            copy.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            shutil.copy2(original, copy)
            records[rel] = {'kind': 'file'}
        elif not exists(original):
            records[rel] = {'kind': 'missing'}
        else:
            raise RuntimeError('Unexpected non-file at ' + rel)
    (BACKUP / 'manifest.json').write_text(json.dumps(records, indent=2))
    return records


def restore(records):
    for rel, info in records.items():
        dest = ROOT / rel
        if exists(dest):
            if dest.is_dir() and not dest.is_symlink():
                raise RuntimeError('Refusing to replace directory ' + str(dest))
            dest.unlink()
        if info['kind'] == 'link':
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.symlink_to(info['target'])
        elif info['kind'] == 'file':
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(BACKUP / 'files' / rel, dest)


def install():
    if BACKUP.exists():
        raise RuntimeError('Backup already exists; do not install twice. Roll back first if needed.')
    config = ROOT / CONFIG
    text = config.read_text()
    data = tomllib.loads(text)
    matches = re.findall(r'^[ \t]*personality\.deauth[ \t]*=[ \t]*(true|false)[ \t]*(?:#[^\n]*)?$', text, re.MULTILINE)
    if len(matches) != 1 or type(data.get('personality', {}).get('deauth')) is not bool:
        raise RuntimeError('Expected exactly one explicit top-level personality.deauth value.')
    if 'hgsec_status' in data.get('main', {}).get('plugins', {}):
        raise RuntimeError('HGSEC plugin already configured; manual review required.')
    for rel in [NEW_LINK, MARKER, *FILES.values()]:
        if exists(ROOT / rel):
            raise RuntimeError('Destination already exists: ' + rel)
    if not (ROOT / OLD_LINK).is_symlink():
        raise RuntimeError('Expected original lcdhat-buttons service enablement symlink.')
    records = save()
    try:
        for src, dest in FILES.items():
            target = ROOT / dest
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(PROJECT / src, target)
            target.chmod(0o644)
        config.write_text('main.plugins.hgsec_status.enabled = true\n' + text)
        tomllib.loads(config.read_text())
        (ROOT / MARKER).touch(mode=0o600)
        (ROOT / OLD_LINK).unlink()
        (ROOT / NEW_LINK).symlink_to('/etc/systemd/system/pwnagotchi-hgsec-buttons.service')
        os.sync()
    except BaseException:
        restore(records)
        os.sync()
        raise
    print('Installed. Original files and service state backed up at ' + str(BACKUP))
    print('The existing deauthentication setting was preserved.')


def rollback():
    records = json.loads((BACKUP / 'manifest.json').read_text())
    if set(records) != set(PATHS):
        raise RuntimeError('Unexpected backup manifest; refusing rollback.')
    restore(records)
    os.sync()
    print('Original files and service state restored. Backup remains at ' + str(BACKUP))
    print('Any config changes made since installation were replaced by the saved config.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['install', 'rollback'])
    args = parser.parse_args()
    verify_target()
    (install if args.operation == 'install' else rollback)()


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('Error:', error, file=sys.stderr)
        sys.exit(1)
