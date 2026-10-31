# GBoard PC + Avro Bangla (Windows prototype)

An original Windows desktop typing helper inspired by mobile keyboard workflows; it is **not** an official or pixel-perfect Google Gboard copy.

## Features
- Main window with **Apply** and **Disable**.
- Offline English typo correction when Space is pressed, using a bundled English dictionary plus common fixes.
- Avro phonetic Roman Bangla transliteration: enable **Avro Bangla mode**, click **Apply**, then type a Roman word and press Space or punctuation (e.g. `ami ` → `আমি `).
- Floating keyboard indicator: **On Display** appears on first keypress and stays visible until **Non-display** or **Disable** is selected.
- GitHub Actions builds a single-file Windows executable and publishes it as a downloadable workflow artifact.

## Build and download
1. Open the [latest Windows release](https://github.com/ridhwanbro/gboard-pc/releases/latest).
2. Download `GBoard_PC.exe` and double-click it. No ZIP extraction is needed.
3. For Bangla, check **Avro Bangla mode**, click **Apply**, then type `ami` and press Space in another app.

## Important limitations
- The app's global keyboard hook has not been tested on the user's Windows PC yet.
- This is a prototype; Microsoft Word and other apps need real-world testing.
- Bengali transliteration follows the Avro phonetic engine, but it is not the complete official Avro Windows keyboard or its selectable candidate dictionary UI.
- English correction is offline and dictionary-based; it does not learn the user's vocabulary or match Google's cloud-backed Gboard suggestions.
- It cannot provide the full Gboard suggestion bar, swipe typing, emoji catalogue, or pixel-identical phone UI.
- Pause/disable before typing passwords or sensitive text.
- Windows may show a security warning for an unsigned executable.

## Local tests
`python test_corrections.py`


Build workflow: `.github/workflows/build-windows.yml` runs on pushes to the default branch.

