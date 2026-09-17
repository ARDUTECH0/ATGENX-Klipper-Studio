# Changelog

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
