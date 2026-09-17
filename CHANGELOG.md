# Changelog

## 1.0.0-beta.4 - 2026-09-17

### Ready-to-run executable
- `python tools/build_exe.py --test` builds a single-file **KlipperStudio.exe** (~48 MB) with the 83 board files,
  icons and the TMC motor list bundled, then checks that it starts, finds the boards and can import / merge /
  validate a config. Windows users need neither Python nor Git.
- The file carries proper Windows properties - app name, version, author, licence and the project link - so it is
  not an anonymous binary in Properties -> Details or in the SmartScreen dialog. A `.sha256` is written next to it
  so a download can be verified, and `--version` answers with the version.
- `python tools/release.py` runs a whole release in one command: tests, end-to-end test, build, exe self-test and,
  with `--publish`, the GitHub release with the exe and its checksum attached. It refuses on a failed check, an
  uncommitted change, a branch other than main, or a tag that already exists.
- [RELEASING.md](RELEASING.md) documents the steps for every version. **Every version ships an executable.**

### Wiring map (new page)
- Your board in the middle and every connected device around it - motors with their driver sockets, heaters,
  thermistors, fans, probe, filament sensor, LED strip, and any section you added yourself - with each line
  labelled with the pin it uses.
- A second board ([mcu pico], a toolhead board...) is drawn as its own board, and pins like `pico:gpio1` are
  connected to it.
- Red marks a problem: an empty pin, the same pin used by two devices, or a pin on a board that is switched off.
- Click a device to see and edit its pins, drag devices to arrange them, scroll to zoom.
- **Add device** adds a motor, switches a feature on, or adds a section from the catalog.
- **Export image** saves the diagram as a PNG - useful for documenting your printer or when asking for help.
- Dragging a device moves its wires and pin labels live, boards can be dragged too, the arrangement is saved with
  the project, and **Reset layout** puts everything back. Dotted grid, wheel zoom, and the selected device's wires
  are highlighted.

## 1.0.0-beta.3 - 2026-09-17

### Features you can switch on and off
- New **Features** page with three parts:
  - **Built-in**: a switch per feature (probe, multiple Z, adaptive mesh, sensorless homing, AWD, TMC Autotune,
    input shaper, retraction, arcs, exclude object, print macros, filament sensor, LEDs, temperatures, idle timeout).
    Turning one on also turns on what it needs, and turning that off turns the dependent features off.
  - **In your file**: every section of your printer.cfg with a switch. Off comments the section out with `#`,
    on removes the `#` again - nothing is ever deleted. Sections you had already commented out show up as off.
  - **Add a feature**: a catalog of 22 well-known sections and plugins (Mainsail/Fluidd macros, Timelapse,
    Shake&Tune, ADXL345 on Pi/Pico/board, skew correction, axis twist, bed screws helpers, save variables,
    force move, filament motion sensor, electronics and chamber fans, chamber sensor, case light, beeper,
    G-code button, servo, or a blank section) with an editable template, added at the end of printer.cfg.
- Check: a pin like `pico:gpio1` whose `[mcu pico]` is switched off is reported before upload.

### Explanations everywhere
- **Help panel** next to the pages: what the page is for, and for the setting under the mouse what it does,
  typical values and the exact place it takes in printer.cfg. Tooltips everywhere, and it can be hidden.
- **Sidebar badges**: each page shows how many errors or warnings it has, and clicking a check on
  Review & upload opens the page that fixes it.
- **The generated file explains itself**: sections grouped under headings (board, motion, motors, heaters,
  probe and leveling, lights, extras, macros) with a one-line explanation above each section. Your own
  comments and sections are still untouched.
- **User guide** in English and Arabic (`docs/GUIDE.md`, `docs/GUIDE.ar.md`), generated from the same help
  source the app uses: install, the screen, seven common tasks, every page and setting, the feature catalog,
  file layout, safety and FAQ. Reachable from the app toolbar.

### Other
- Support link (Buy me a coffee) in the app, the README and the repository
- Tests: 36 unit tests, all 206 Klipper example configs, and 36 end-to-end checks against a fake Moonraker

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
