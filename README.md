# Pwnagotchi HGSEC

A Raspberry Pi Zero 2 W Pwnagotchi customization for the [Waveshare 1.3-inch LCD HAT](https://www.waveshare.com/wiki/1.3inch_LCD_HAT). It documents a real device and provides a safer physical control interface for authorized wireless security research. The repository is intended to grow as more customizations are developed.

The device collects packet captures; its companion [Pwnabase](https://github.com/HenriqueGieseke/pwnabase) can process supported captures offline to study WPA/WPA2 password recovery. A capture is not itself a password and may not contain a usable handshake. Use these tools only with explicit authorization for the networks and activity involved.

## Hardware and controls

The reference device runs Pwnagotchi 2.8.9 on a Raspberry Pi Zero 2 W with the 240 × 240 ST7789 LCD HAT. The original SD card supplied the display layout and the button service's GPIO assignments. This repository replaces its button handler with the controls below; it does not contain the card's credentials, captures, or personal configuration.

| Control | BCM pin | Action |
| --- | --- | --- |
| KEY2 | 20 | Hold for 2 seconds to toggle the explicitly configured deauthentication setting. Disabled until separately enabled. |
| KEY3 | 16 | Hold for 2 seconds to request shutdown. |
| KEY1 and joystick | 21, 6, 19, 5, 26, 13 | Unassigned. |

Each action fires once per hold; release before triggering it again. A Pwnagotchi plugin displays action and error messages on the existing LCD UI. KEY2 announces that it is applying the setting before services restart, then announces the configured setting after restart commands complete. KEY3 displays “Shutting down...” before requesting poweroff. The display cannot report an error if Pwnagotchi itself is stopped or unable to render; inspect the service journal in that case. A successful start command does not prove that wireless operations are healthy.

**Compatibility:** the revised button controls and LCD feedback were tested successfully by the device owner on the reference Raspberry Pi Zero 2 W and Waveshare HAT. Other Pwnagotchi versions and HATs are unverified; recovery from service failures has not been independently validated.

## Setup

Read [installation and recovery](docs/installation.md) before copying anything to the device. The service and the deauthentication action require separate, explicit enablement. These operations use root privileges; back up configuration and keep another way to access the Pi. The deauthentication toggle is an active wireless operation, not a passive capture setting.

## Development

Run the hardware-independent checks on Python 3.11 or later:

```sh
python3 -m unittest discover -s tests -v
python3 -m compileall -q src
```

They cover hold timing and safe configuration editing; they do not exercise real GPIO, systemd, radio interfaces or the LCD.

## Origins and license

The reference device uses Pwnagotchi 2.8.9. `src/lcdhat.py` is the modified display implementation found on its SD card; the installed package's recorded hash differs from that file, so it is presented as an adaptation rather than wholly original work. It relies on the Pwnagotchi LCD driver already installed on the device. Button mappings and the restart sequence are based on the device's scripts; the handler and status plugin in this repository are a new implementation. Pwnagotchi and its contributors retain credit for their work. See [NOTICE](NOTICE) and [LICENSE](LICENSE); the included Pwnagotchi package identified its license as GPL version 3.
