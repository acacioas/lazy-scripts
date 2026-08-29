# combine-photos

The objective of this script is to (ab)use Photo printing kiosks to print smaller photos, so this combines 2 photos in 1 for printing.

Photo kiosks (and most consumer photo labs) charge per print, with the print size fixed at 10x15cm (4x6"). This script pairs up your photos two at a time and lays them side by side onto a single 10x15cm canvas, so you can order one print and cut it in half to get two smaller photos for the price of one.

## What it does

For each pair of images (taken in natural filename order):

1. **Auto-rotate** — if a photo is landscape (wider than tall), it's rotated 90° counter-clockwise first, so the portrait crop in the next step doesn't have to cut away as much of the image.
2. **Center-crop + resize** — each photo is cropped to a 2:3 ratio and scaled to exactly 800x1200px, filling its slot completely (no stretching, no letterboxing).
3. **Compose** — the two photos are placed side by side, full-bleed top to bottom, with a gap and margins, on a single 1800x1200px canvas (10x15cm @ 300 DPI).
4. **Save** — written to the output directory as `<basename>_<index>.jpg`.

Canvas layout (with defaults):

```
margin(50) + slot(800) + gap(100) + slot(800) + margin(50) = 1800px wide
slot height = 1200px = full canvas height
```

Images are read from the input directory (non-recursive), sorted in natural order (so `img2.jpg` sorts before `img10.jpg`), and paired up consecutively: (1st, 2nd), (3rd, 4th), etc. If there's an odd one out, it's skipped with a warning.

## Requirements

- Python 3
- [Pillow](https://pypi.org/project/Pillow/)

```
pip install Pillow
```

> Tested on macOS only.

## Usage

```
python combine-photos.py INPUT_DIR OUTPUT_DIR --basename family_trip
```

This writes `OUTPUT_DIR/family_trip_01.jpg`, `family_trip_02.jpg`, etc.

### Options

| Flag | Default | Description |
|---|---|---|
| `-b`, `--basename` | `combined` | Base name for output files, e.g. `trip` -> `trip_01.jpg` |
| `--start-index` | `1` | Starting number for output filenames |
| `--gap` | `100` | Gap between the two photos in px |
| `--margin` | `50` | Left/right margin in px |
| `--bg-color` | `white` | Fill color for gap/margin/transparency, e.g. `white`, `black`, `#eeeeee` |
| `--dpi` | `300` | DPI metadata embedded in the output JPEG |
| `--quality` | `95` | JPEG quality (1-95) |

Supported input formats: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.tif`, `.webp`. Output is always JPEG.

## Example

```
python combine-photos.py ./photos ./output --basename family_trip --start-index 1
```

```
Saved output/family_trip_01.jpg (1800x1200px @ 300 dpi)  <-  IMG_001.jpg + IMG_002.jpg
Saved output/family_trip_02.jpg (1800x1200px @ 300 dpi)  <-  IMG_003.jpg + IMG_004.jpg
Done: 2 combined image(s) written to 'output'.
```

Send the resulting JPEGs to your photo kiosk of choice as regular 10x15cm (4x6") prints, then cut each print down the middle to get your individual photos.
