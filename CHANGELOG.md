# Changelog

## 1.0.0-beta.2 - 2026-09-17

### Look & feel
- New logo and app icon (window, taskbar, Windows .ico), README banner and GitHub social preview image
- Start page with four clear choices: connect to a printer, set up a new printer, open a file, fix a problem
- `run.bat` starts the app without a console window

### Motors & drivers
- Every motor is configured on its own: driver socket, driver type, current, hold current, microsteps, rotation distance, step angle (0.9°/1.8°), stealthChop threshold, interpolation, sense resistor
- Put any motor on any free driver socket; socket conflicts are reported
- Add motors: X2 / Y2 (AWD) and up to 4 Z motors
- Mixed drivers per motor: TMC2209, TMC2208, TMC2130, TMC5160, TMC2240, TMC2660, standalone
- Sensorless homing for X/Y (DIAG pin, StallGuard threshold, `homing_retract_dist: 0`), with checks from the Klipper docs
- TMC Autotune support (203 motors from the plugin database, tuning goal, supply voltage)
- Z leveling for 2-4 motors: `z_tilt` or `quad_gantry_level`, with pivot positions and probe points

### Troubleshooter (new page)
- Reads Klipper's state, config warnings and the last session of `klippy.log` (read-only)
- Recognises 31 common problems (serial, Timer too close, TMC UART, ADC out of range, heater rate, endstops, probes, unknown options/sections, pin conflicts...) and explains the cause and the fix in English and Arabic
- `python -m studio doctor klippy.log`

### Add-ons
- Firmware retraction, idle timeout, Raspberry Pi and board temperature sensors
- Optional START_PRINT / END_PRINT / M600 macros with adaptive mesh, leveling and purge line; macros you wrote yourself are never replaced

### Fixes (found by testing against all 206 config files shipped with Klipper)
- Printers without a heated bed or part fan no longer get sections with empty pins
- Delta, polar, winch and other unsupported machines are never rewritten
- A probe's `z_virtual_endstop` is no longer mistaken for sensorless homing; DIAG pins used for other purposes are kept
- TMC2660 (Duet 2) drivers are kept instead of being converted
- `uart_address: 0` on TMC2208 is accepted, as in Klipper
- Duplicate sections are a warning (Klipper merges them), and commented-out lines no longer trigger macro reference errors
- Beta 1 projects are converted automatically

### Testing
- `tools/corpus_check.py`: import, merge (idempotent) and validate every Klipper example config
- `tools/gui_e2e.py`: drives the real app window against a fake Moonraker (connect, import, upload guards, backup, restore, file editing, troubleshooter, language switch)

## 1.0.0-beta.1 - 2026-09-17

First public beta.

- Guided wizard: connection, board, machine, motors & drivers, hotend & bed, probe & leveling, LEDs & extras, pins, review & upload
- 83 controller boards imported from Klipper's official board files, with a `make menuconfig` summary per board
- Import from a running printer through Moonraker, including every included file and `SAVE_CONFIG` values; board auto-detection
- Line-level smart merge that keeps comments, formatting, macros and unknown keys
- Checks: pin conflicts, missing pins, placeholder serial, TMC bus, acceleration limits, mesh area, references from macros, Klipper warnings
- Safe upload with printing/paused guard, change detection, remote + local backup, `FIRMWARE_RESTART` and restore
- All config files page: include tree, section navigation, editor, safe save with the right service restart
- English and Arabic (RTL) interface
- Command line: `boards`, `check`, `generate`
