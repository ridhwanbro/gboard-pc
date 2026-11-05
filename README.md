# Gboard PC

An offline Bangla (Bengali) keyboard for Windows 10 and 11, using Avro Phonetic transliteration.

## Download

Download **Gboard_PC.exe** from the latest GitHub Release and run it directly. It is a single-file app and does not require Python or an installer.

## Features

- Apply and Disable controls, with English and Avro Phonetic (বাংলা) modes.
- Global mode toggle: Ctrl+Alt+Shift+Space.
- Floating QWERTY keyboard with Bangla letters, or tray-only mode.
- Up to three suggestions; Ctrl+Alt+Shift+Q/W/E selects them.
- Offline dictionary and word correction.
- Text box with copy, clipboard, save-as-text and clear controls.
- Typed text is handled locally; the app makes no network requests or input history.

## Source and license

The Windows app source is `GboardPC.py`. The release includes the matching source and GPL-3.0 license as separate assets. Avro patterns are based on OmicronLab's Avro Phonetic implementation; dictionary seed data is from Minhas Kamal's BengaliDictionary.

## Build from source

Use Python 3.12, then install `pyinstaller`, `pystray` and `pillow`. Build with:

```text
python -m PyInstaller --noconfirm --clean --onefile --windowed --name Gboard_PC --collect-all pystray --collect-all PIL GboardPC.py
```
