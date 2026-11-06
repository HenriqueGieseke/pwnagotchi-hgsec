# Installation and recovery

These steps target the reference Raspberry Pi Zero 2 W, Waveshare 1.3-inch LCD HAT and Pwnagotchi 2.8.9. The device owner tested the revised controls on this hardware after an offline card installation; the manual installation steps below have not been separately verified. Work on a backup or spare SD card first, keep SSH or another recovery method available, and use only in explicitly authorized environments. The commands modify the device when run there, not the card inspected for this repository.

## Prepare

Install a compatible Pwnagotchi image and configure its LCD HAT according to its documentation. Enable SPI, ensure `lgpio` is importable by `/usr/bin/python3`, and confirm the existing LCD driver works. The display adaptation relies on the package's existing `pwnagotchi.ui.hw.libs.waveshare.lcd.lcdhat` driver. Back up `/etc/pwnagotchi/config.toml` and the installed `pwnagotchi/ui/hw/lcdhat.py` before changing them. Do not copy personal credentials into this repository.

The card's observed configuration uses `ui.display.enabled = true`, `ui.display.type = "lcdhat"`, `ui.display.color = "black"`, and `ui.display.rotation = 0`. Review existing values instead of replacing your configuration. Find the installed display file with:

```sh
python3 -c 'import pwnagotchi.ui.hw.lcdhat as m; print(m.__file__)'
```

To apply the adapted layout, back up the printed file and copy `src/lcdhat.py` over it using `sudo install -m 644`; a package upgrade can replace it. Verify the correct destination before copying.

## Install, then explicitly enable

From a checked-out copy of this repository on the Pi:

```sh
sudo install -d -m 755 /usr/local/lib/pwnagotchi-hgsec /usr/local/share/pwnagotchi/custom-plugins
sudo install -m 644 src/pwnagotchi_hgsec/buttons.py src/pwnagotchi_hgsec/actions.py /usr/local/lib/pwnagotchi-hgsec/
sudo install -m 644 src/hgsec_status.py /usr/local/share/pwnagotchi/custom-plugins/hgsec_status.py
sudo install -m 644 systemd/pwnagotchi-hgsec-buttons.service /etc/systemd/system/
sudo systemctl daemon-reload
```

In `/etc/pwnagotchi/config.toml`, enable the plugin with `main.plugins.hgsec_status.enabled = true` and ensure `main.custom_plugins` points to `/usr/local/share/pwnagotchi/custom-plugins/`. Restart Pwnagotchi and verify the display. If the original `lcdhat-buttons.service` exists, stop and disable it before enabling the new service, to avoid two processes claiming the same pins:

```sh
sudo systemctl disable --now lcdhat-buttons.service
sudo systemctl enable --now pwnagotchi-hgsec-buttons.service
```

If the original unit does not exist, skip its disable command. KEY3 is active once the new service is started. KEY2 remains disabled until the following separate step.

## Opt in to KEY2

Only for explicitly authorized active testing, add exactly one top-level line `personality.deauth = false` to `/etc/pwnagotchi/config.toml` (before any TOML table headings), if it does not already have an explicit top-level true/false setting. The action refuses missing, ambiguous, or table-style settings. Do not duplicate existing settings. Then opt in:

```sh
sudo touch /etc/pwnagotchi/hgsec-deauth-enabled
```

Hold KEY2 for two seconds. The action updates that line, stops Pwnagotchi and bettercap, runs `/usr/bin/monstart`, brings `wlan0` down, then starts bettercap and Pwnagotchi, following the original device's sequence. It does not verify successful radio operation, and a failed command can leave services stopped or the setting changed. Check `journalctl -u pwnagotchi-hgsec-buttons -b`, `systemctl status pwnagotchi bettercap`, and the configuration. Do not assume a displayed setting proves the actual radio behavior.

## Disable or recover

Remove `/etc/pwnagotchi/hgsec-deauth-enabled` to prevent future KEY2 toggles; this does **not** change an already enabled deauthentication setting. Set `personality.deauth = false` explicitly and restart Pwnagotchi according to your installation's procedure if required. Disable the service with `sudo systemctl disable --now pwnagotchi-hgsec-buttons.service`. If needed, restore backed-up configuration and display file, restart Pwnagotchi and bettercap, and inspect their journals. The old button service should only be re-enabled intentionally; it has different hold and state behavior.

## Reference card installer

`tools/card-install.py` is a one-off recovery artifact for the original card, not a general installer: it expects `/dev/sdc2` mounted at `/tmp/pwnagotchi-sd`, uses root, and enables the deauthentication button while preserving the existing setting. Device names can change and identify a different disk on another computer. Do not run it without checking the target and adapting it to your system. Its backup includes the device configuration and must remain private. Rollback restores the saved configuration in full and overwrites later configuration changes.
