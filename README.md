# GBoard PC + Avro Bangla (Windows prototype)

An original Windows desktop typing helper inspired by mobile keyboard workflows; it is **not** an official or pixel-perfect Google Gboard copy.

## Features
- Main window with **Apply** and **Disable**.
- Basic English typo correction when Space is pressed.
- Roman Bangla transliteration for a small offline starter dictionary (e.g. `ami` → `আমি`); this is not yet a full Avro engine.
- Floating keyboard indicator: **On Display** shows while keys are being pressed and hides after idle; **Non-display** keeps it hidden.
- GitHub Actions builds a single-file Windows executable and publishes it as a downloadable workflow artifact.

## Build and download
1. Open the **Actions** tab.
2. Select **Build GBoard PC for Windows** and click **Run workflow** (or wait for the push-triggered build).
3. Open the successful run and download the `GBoard_PC-Windows-x64` artifact.
4. GitHub stores workflow artifacts as a ZIP; extract the ZIP and double-click `GBoard_PC.exe`.

## Important limitations
- The app's global keyboard hook has not been tested on the user's Windows PC yet.
- This is a prototype; Microsoft Word and other apps need real-world testing.
- Avro support currently uses a starter dictionary, not the complete Avro phonetic engine.
- It cannot provide the full Gboard suggestion bar, swipe typing, emoji catalogue, or pixel-identical phone UI.
- Pause/disable before typing passwords or sensitive text.
- Windows may show a security warning for an unsigned executable.

## Local tests
`python test_corrections.py`
