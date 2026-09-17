# Contributing

Thanks for helping! Anyone can propose changes. **Nothing is merged until the maintainer reviews and approves it.**

## How it works

1. **Fork** the repository and create a branch: `git checkout -b board/fysetc-spider-v3`
2. Make your change and run the tests: `python -m unittest discover -s tests`
3. Open a **Pull Request** against `main` and fill in the template.
4. The maintainer reviews it. You may be asked for changes or for a photo or log from a real printer.
5. Once approved, the maintainer merges it.

Small, focused pull requests are reviewed fastest. For bigger features, open an issue first so we can agree on the approach.

## Adding or fixing a board

Board definitions live in `boards/<id>.json`. Most of them are generated from Klipper's official files:

```bash
git clone --depth 1 https://github.com/Klipper3d/klipper.git /tmp/klipper
python tools/import_klipper_boards.py /tmp/klipper/config boards
python tools/boards_md.py          # refresh docs/BOARDS.md
python -m unittest discover -s tests
```

For a board Klipper doesn't ship, copy a similar JSON file and edit it:

| Field | Meaning |
|---|---|
| `id` | file name without `.json`, lowercase with dashes |
| `mcu.processors` | as Klipper names them: `stm32f446`, `lpc1769`, `rp2040` |
| `drivers[]` | one entry per stepper socket: `slot` (`stepper_x`, `extruder1`...), `step_pin`, `dir_pin`, `enable_pin`, `endstop_pin`, `tmc` (`uart_pin`/`tx_pin`/`uart_address` or `cs_pin`/`spi_bus`) |
| `heaters` | `extruder`, `extruder1`..., `heater_bed` with `heater_pin` and `sensor_pin` |
| `fans[]` | `fan` is the part fan; `heater_fan ...` / `controller_fan ...` are the others |
| `probe` | `pin` (probe port), `bl_sensor`, `bl_control` |
| `extra_sections[]` | sections the board needs to work (USB pull-up, digipot, ...) |

Please include **where the pins come from**: the vendor's pinout PDF, schematic, or a config you tested on a real board.

## Testing

```bash
python -m unittest discover -s tests                   # core tests (no Qt, no network)
python tools/corpus_check.py /path/to/klipper/config   # every Klipper example config must pass
QT_QPA_PLATFORM=offscreen python tools/gui_e2e.py      # the real app window against a fake Moonraker
```

## Adding a troubleshooter rule

Rules live in `studio/doctor.py` (id, regular expression, page to open). Add `doc.<id>.title`, `doc.<id>.cause` and
`doc.<id>.fix` to `studio/i18n.py` in every language, and a sample message to `TestDoctor` in `tests/test_core.py`.

## Adding a feature to the catalog

`studio/features.py` -> `CATALOG`: an id, icon, category, the plugin it needs (or "") and a template. Add
`cat.<id>.title` and `cat.<id>.desc` to `studio/i18n.py` in every language. Templates must be valid Klipper
config - the test suite parses every one of them.

## Adding an explanation

`studio/help.py` -> `HELP`: the page it belongs to, the exact place in printer.cfg, and the English and Arabic
text. It then shows in the app's help panel, in the tooltip, and in `docs/GUIDE*.md` (`python tools/guide_md.py`).

## Translations

UI strings live in `studio/i18n.py`. Every entry has an `en` and an `ar` text; keep `{placeholders}` identical.
To add a language, add its code to `LANGS` and a column to every entry. The test suite checks that nothing is missing.

## Code style

- Python 3.9+, standard library only in `studio/` (except `studio/gui`, which uses PySide6).
- The core (`boards`, `importer`, `generator`, `merge`, `validate`, `configset`) must not import Qt, so it stays testable.
- Anything that can change a printer must keep the safety rules: never while printing, check the file didn't change, back up first.
- Add or update tests for behaviour changes.

## Reporting a problem

Open an issue with your board, Klipper and Moonraker versions, what you expected, and the relevant part of the *Differences* or *Checks* tab.
**Remove serial numbers, API keys and IP addresses you don't want to share.**

## License of contributions

By submitting a pull request you agree that your contribution is licensed under the project's
[PolyForm Noncommercial 1.0.0](LICENSE) license, and that the maintainer may also offer it under other terms
(for example a commercial license) together with the rest of the project.
