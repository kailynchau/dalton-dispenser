# Dalton Lab – Automated Photopolymer Micro-Dispenser

A 3-axis dispensing system for coating solid microneedle arrays with SU-8 photopolymer (and dispensing PDMS), built on a modified Ender 3 frame. A Raspberry Pi runs a Tkinter GUI that drives an Arduino Mega over serial; the Arduino runs the steppers (X/Y/Z + syringe pump).

See the [technical design report](docs/Technical_Design_Report.pdf) for background, specs, and results.

## Repo layout

```
gui/main.py                        Tkinter GUI (runs on the Raspberry Pi)
firmware/SerialComm/SerialComm.ino Arduino Mega firmware (AccelStepper / MultiStepper)
docs/Technical_Design_Report.pdf   Full design report
docs/sop/                          Assembly, operation, and fluid loading SOPs
hardware/Bill_of_Materials.xlsx    Parts list with costs and links
hardware/Solenoid_Valve_Planning.pdf  Parts plan for the pneumatic (solenoid) dispensing head
```

## Quick start

1. **Firmware** – open `firmware/SerialComm/SerialComm.ino` in the Arduino IDE, install the **AccelStepper** library, and upload to the Arduino Mega.
2. **GUI** – on the Pi:
   ```bash
   pip install pyserial
   python3 gui/main.py
   ```
   The serial port is hardcoded to `/dev/ttyACM0` at 9600 baud in `main.py` — change it if your Arduino shows up elsewhere.
3. Follow the [Operation SOP](docs/sop/operation.md).

## Serial protocol (menu-driven)

The firmware is a text menu; the GUI sends newline-terminated numbers to navigate it.

| Main menu | | Manual submenu (`1`) | |
|---|---|---|---|
| `1` | Manual | `1` | Show position |
| `2` | Zeroing *(not implemented)* | `2` | Set zero |
| `3` | Mounting (raise plunger) | `3` | Move (x, y, z, p, then `1` to confirm) |
| `4` | Calibration *(not implemented)* | `4` | Multi-move |
| `5` | SU-8 *(not implemented)* | `7` | Set units (`1` step, `2` mm, `3` µm) |
| `6` | PDMS – Dowsil SE 1700 | `8` | Set max speed |
| `7` | PDMS – Sylgard 184 | `9` | Enable (`1`) / disable (`0`) motors |
| | | `-1` | Exit to main menu |

Sending anything while a move is running stops it.

**Steps/mm** (from firmware): X = Y = 80, Z = 400, syringe pump = 33,960.

## SOPs

- [Assembly](docs/sop/assembly.md)
- [Operation](docs/sop/operation.md)
- [Fluid loading](docs/sop/fluid-loading.md)

## Known limitations / next steps

- Homing with the end stops (`Zeroing()`) is written but disabled.
- Picopump / SU-8 automated profile isn't wired into the firmware yet (GUI "Activate Pico" is a stub).
- PDMS dispense paths are hardcoded step arrays in the firmware.
- Camera controls in the GUI are commented out.

See the report's *Future Improvements* section for more.

## Reference

- BigTreeTech SKR V1.3 docs and pin diagram (used for the solenoid/Marlin version): https://github.com/bigtreetech/BIGTREETECH-SKR-V1.3
