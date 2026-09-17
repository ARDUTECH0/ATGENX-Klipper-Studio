# Releasing a version

Every release ships **the source and a ready-to-run executable**, so a user on Windows needs neither Python nor Git.

## 1. Check everything

```bash
python -m unittest discover -s tests                      # core tests
python tools/corpus_check.py /path/to/klipper/config      # all Klipper example configs
QT_QPA_PLATFORM=offscreen python tools/gui_e2e.py         # the real window against a fake Moonraker
QT_QPA_PLATFORM=offscreen python tools/gui_e2e.py printer.cfg   # and against a real config
```

## 2. Refresh what is generated

```bash
python tools/boards_md.py       # docs/BOARDS.md
python tools/guide_md.py        # docs/GUIDE.md and docs/GUIDE.ar.md
python tools/make_brand.py      # icons, README banner, social preview
QT_QPA_PLATFORM=offscreen QT_QPA_FONTDIR=/usr/share/fonts python tools/screenshots.py en
QT_QPA_PLATFORM=offscreen QT_QPA_FONTDIR=/usr/share/fonts python tools/screenshots.py ar
```

On Windows use `QT_QPA_FONTDIR=C:/Windows/Fonts`.

## 3. Version and changelog

- `studio/__init__.py` -> `__version__` (for example `1.0.0-beta.5`)
- `CHANGELOG.md` -> a new section at the top, in the same style: what is new, what is fixed, what was tested

## 4. Build the executable

```bash
python tools/build_exe.py --test
```

Produces `dist/KlipperStudio.exe` (~48 MB) and checks that it starts, finds the bundled boards, and can
import / merge / validate a config. **Build it on the system you are releasing for** - a Windows exe must be
built on Windows, a Linux binary on Linux.

Before uploading, double-click it once yourself: the headless test proves the pages build, not that the window
looks right.

## 5. Publish

```bash
git add -A && git commit -m "..."        # on a branch, then open a PR
gh pr create --base main --head <branch> --title "..." --body-file <notes>
# after the PR is merged:
git checkout main && git pull
gh release create v1.0.0-beta.5 --target main --prerelease \
    --title "Klipper Studio 1.0.0 Beta 5" --notes-file <notes>
gh release upload v1.0.0-beta.5 dist/KlipperStudio.exe
```

Mention in the notes that Windows SmartScreen shows a warning for the exe (it is not code-signed):
**More info -> Run anyway**. Signing needs a paid certificate; until then, users who prefer it can run from source.

## 6. After publishing

- Check the release page: the exe is attached and the screenshots in the notes load.
- If the version is worth telling people about, use the ready posts in `../reddit-post/` and
  `../launch-posts-klipper-studio.md` - and keep replying to issues first.
