#!/usr/bin/env python3
"""
combine_photos.py

Batch-combine photos from a directory, two at a time, into 1800x1200px
landscape JPEGs ready to print as 10x15cm (4x6") photos.

For each pair of images (taken in natural filename order):
  - Auto-rotate: if a photo is horizontally oriented (landscape), rotate it
    90 degrees to the left (counter-clockwise) first, so the later 2:3
    portrait crop doesn't have to cut away as much of the image.
  - Each photo is then center-cropped to a 2:3 ratio and scaled to exactly
    800x1200px (fills the slot completely -- no stretching).
  - The two photos are placed side by side with a gap, full-bleed top to
    bottom, on an 1800x1200px canvas.
  - Saved to the output directory as "<basename>_<index>.jpg".

Usage:
    python combine_photos.py INPUT_DIR OUTPUT_DIR --basename family_trip

    # -> OUTPUT_DIR/family_trip_01.jpg, family_trip_02.jpg, ...

Images are read from INPUT_DIR (non-recursive), sorted in natural order
(so "img2.jpg" sorts before "img10.jpg"), and paired up consecutively:
(1st,2nd), (3rd,4th), etc. If there's an odd one out, it's skipped with a
warning.

Optional:
    --basename     base name for output files            (default: combined)
    --start-index  numbering starts here                  (default: 1)
    --gap          gap between the two photos in px        (default: 100)
    --margin       margin on left/right edges in px        (default: 50)
    --bg-color     fill color for gap/margin/transparency  (default: white)
                   e.g. "white", "black", "#eeeeee"
    --dpi          DPI metadata embedded in the output JPEG (default: 300)
    --quality      JPEG quality 1-95                        (default: 95)

Canvas layout (defaults):
    margin(50) + slot(800) + gap(100) + slot(800) + margin(50) = 1800px wide
    slot height = 1200px = full canvas height
"""

import argparse
import re
import sys
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

CANVAS_W = 1800
CANVAS_H = 1200
SLOT_W = 800
SLOT_H = 1200

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}


def natural_key(path: Path):
    """Sort key so 'img2.jpg' comes before 'img10.jpg'."""
    return [int(tok) if tok.isdigit() else tok.lower() for tok in re.split(r"(\d+)", path.name)]


def list_images(input_dir: Path):
    files = [p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
    return sorted(files, key=natural_key)


def load_and_flatten(path: Path, bg_color) -> Image.Image:
    """Open an image, auto-rotate per EXIF, and flatten any transparency onto bg_color."""
    try:
        img = Image.open(path)
    except (FileNotFoundError, UnidentifiedImageError) as e:
        raise SystemExit(f"Error: could not open image '{path}': {e}")

    img = ImageOps.exif_transpose(img)  # respect camera/phone orientation

    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        img = img.convert("RGBA")
        background = Image.new("RGB", img.size, bg_color)
        background.paste(img, mask=img.split()[-1])
        return background

    return img.convert("RGB")


def auto_rotate_landscape(img: Image.Image) -> Image.Image:
    """If the image is horizontally oriented (wider than tall), rotate it 90
    degrees to the left (counter-clockwise) so more of it survives the 2:3
    portrait crop instead of being cut off the sides."""
    w, h = img.size
    if w > h:
        return img.rotate(90, expand=True)
    return img


def cover_crop_resize(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Center-crop + resize an image to exactly fill (cover) target_w x target_h.
    Crops off whatever doesn't fit the target aspect ratio -- no distortion,
    no letterboxing, slot is filled edge to edge."""
    src_w, src_h = img.size
    target_ratio = target_w / target_h
    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        # source is relatively wider than target -> crop left/right
        new_w = int(round(src_h * target_ratio))
        left = (src_w - new_w) // 2
        box = (left, 0, left + new_w, src_h)
    else:
        # source is relatively taller than target -> crop top/bottom
        new_h = int(round(src_w / target_ratio))
        top = (src_h - new_h) // 2
        box = (0, top, src_w, top + new_h)

    cropped = img.crop(box)
    return cropped.resize((target_w, target_h), Image.LANCZOS)


def build_canvas(img1: Image.Image, img2: Image.Image, gap: int, margin: int, bg_color) -> Image.Image:
    total_w = margin + SLOT_W + gap + SLOT_W + margin
    if total_w != CANVAS_W:
        print(
            f"Warning: margin*2 + gap + 2*{SLOT_W} = {total_w}px, which isn't "
            f"exactly the {CANVAS_W}px canvas width. The pair will still be "
            f"centered, but adjust --gap/--margin for an exact edge-to-edge fit.",
            file=sys.stderr,
        )

    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), bg_color)

    # Center the whole (margin+slot+gap+slot+margin) block horizontally,
    # in case gap/margin don't add up exactly to CANVAS_W.
    start_x = (CANVAS_W - total_w) // 2 + margin
    y = (CANVAS_H - SLOT_H) // 2  # 0 by default, since SLOT_H == CANVAS_H

    canvas.paste(img1, (start_x, y))
    canvas.paste(img2, (start_x + SLOT_W + gap, y))
    return canvas


def process_pair(path1: Path, path2: Path, args) -> Image.Image:
    img1 = auto_rotate_landscape(load_and_flatten(path1, args.bg_color))
    img2 = auto_rotate_landscape(load_and_flatten(path2, args.bg_color))

    slot1 = cover_crop_resize(img1, SLOT_W, SLOT_H)
    slot2 = cover_crop_resize(img2, SLOT_W, SLOT_H)

    return build_canvas(slot1, slot2, args.gap, args.margin, args.bg_color)


def main():
    parser = argparse.ArgumentParser(
        description="Batch-combine photos from a directory, 2 at a time, into 1800x1200 print-ready JPEGs (10x15cm photos)."
    )
    parser.add_argument("input_dir", type=Path, help="Directory containing source images")
    parser.add_argument("output_dir", type=Path, help="Directory to write combined images to")
    parser.add_argument("-b", "--basename", type=str, default="combined",
                         help="Base name for output files, e.g. 'trip' -> trip_01.jpg (default: combined)")
    parser.add_argument("--start-index", type=int, default=1, help="Starting number for output filenames (default: 1)")
    parser.add_argument("--gap", type=int, default=100, help="Gap between photos in px (default: 100)")
    parser.add_argument("--margin", type=int, default=50, help="Left/right margin in px (default: 50)")
    parser.add_argument("--bg-color", type=str, default="white",
                         help="Background color for gap/margin/transparency, e.g. 'white', '#000000' (default: white)")
    parser.add_argument("--dpi", type=int, default=300, help="DPI metadata to embed in output (default: 300)")
    parser.add_argument("--quality", type=int, default=95, help="JPEG quality 1-95 (default: 95)")

    args = parser.parse_args()

    if not args.input_dir.is_dir():
        raise SystemExit(f"Error: input directory '{args.input_dir}' does not exist.")

    images = list_images(args.input_dir)
    if len(images) < 2:
        raise SystemExit(f"Error: need at least 2 images in '{args.input_dir}', found {len(images)}.")

    num_pairs = len(images) // 2
    pairs = [images[i:i + 2] for i in range(0, num_pairs * 2, 2)]

    leftover = images[num_pairs * 2:]
    if leftover:
        print(f"Warning: {len(leftover)} leftover image(s) with no pair, skipped: "
              f"{[p.name for p in leftover]}", file=sys.stderr)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    pad_width = max(2, len(str(args.start_index + num_pairs - 1)))

    for offset, (path1, path2) in enumerate(pairs):
        idx = args.start_index + offset
        canvas = process_pair(path1, path2, args)

        out_name = f"{args.basename}_{idx:0{pad_width}d}.jpg"
        out_path = args.output_dir / out_name
        canvas.save(out_path, "JPEG", quality=args.quality, dpi=(args.dpi, args.dpi))
        print(f"Saved {out_path} ({canvas.size[0]}x{canvas.size[1]}px @ {args.dpi} dpi)  <-  {path1.name} + {path2.name}")

    print(f"Done: {len(pairs)} combined image(s) written to '{args.output_dir}'.")


if __name__ == "__main__":
    main()
