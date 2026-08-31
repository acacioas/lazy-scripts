#!/usr/bin/env python3
"""
normalize-volume.py

Loudness-normalize every song in a folder (mp3, m4a, mp4, aac, flac, wav,
ogg, opus) so they all play back at roughly the same perceived volume, and
write the results to a destination folder. Each file is re-encoded at the
highest reasonable quality for its own format, and its metadata (ID3 tags,
cover art) is preserved.

Uses ffmpeg's loudnorm filter (EBU R128), two-pass: pass 1 measures the
input's loudness, pass 2 applies the correction using those measurements
for an accurate, single re-encode (no clipping/pumping from guessing).

Usage:
    python normalize-volume.py INPUT_DIR OUTPUT_DIR
    python normalize-volume.py INPUT_DIR OUTPUT_DIR --target-lufs -16
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Re-encode settings chosen per format for the highest quality that's still
# reasonable (near-transparent for lossy formats, lossless for the rest).
CODEC_ARGS = {
    ".mp3": ["-c:a", "libmp3lame", "-q:a", "0"],       # ~245-320kbps VBR
    ".m4a": ["-c:a", "aac", "-b:a", "256k"],
    ".mp4": ["-c:a", "aac", "-b:a", "256k"],
    ".aac": ["-c:a", "aac", "-b:a", "256k"],
    ".flac": ["-c:a", "flac", "-compression_level", "8"],
    ".wav": ["-c:a", "pcm_s24le"],                     # never downsamples bit depth
    ".ogg": ["-c:a", "libvorbis", "-q:a", "10"],
    ".opus": ["-c:a", "libopus", "-b:a", "192k"],
}

LOUDNORM_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def run_ffmpeg(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def measure_loudness(input_file: Path, target_i: float, true_peak: float, lra: float):
    filt = f"loudnorm=I={target_i}:TP={true_peak}:LRA={lra}:print_format=json"
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", str(input_file),
           "-af", filt, "-f", "null", "-"]
    result = run_ffmpeg(cmd)
    match = LOUDNORM_JSON_RE.search(result.stderr)
    if not match:
        raise SystemExit(f"Error: couldn't measure loudness for '{input_file.name}':\n{result.stderr}")
    return json.loads(match.group(0))


def normalize_file(input_file: Path, output_file: Path, target_i: float, true_peak: float, lra: float):
    stats = measure_loudness(input_file, target_i, true_peak, lra)
    filt = (
        f"loudnorm=I={target_i}:TP={true_peak}:LRA={lra}:"
        f"measured_I={stats['input_i']}:measured_TP={stats['input_tp']}:"
        f"measured_LRA={stats['input_lra']}:measured_thresh={stats['input_thresh']}:"
        f"offset={stats['target_offset']}:linear=true:print_format=summary"
    )
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-i", str(input_file), "-af", filt,
           "-map_metadata", "0", "-c:v", "copy"]
    cmd += CODEC_ARGS[output_file.suffix.lower()]
    if output_file.suffix.lower() == ".mp3":
        cmd += ["-id3v2_version", "3"]
    cmd.append(str(output_file))

    result = run_ffmpeg(cmd)
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    return float(stats["input_i"])


def main():
    parser = argparse.ArgumentParser(description="Loudness-normalize a folder of songs, preserving metadata.")
    parser.add_argument("input_dir", type=Path, help="folder of songs to normalize")
    parser.add_argument("output_dir", type=Path, help="folder to write normalized songs to")
    parser.add_argument("--target-lufs", type=float, default=-14.0,
                         help="integrated loudness target in LUFS (default: -14, common streaming target)")
    parser.add_argument("--true-peak", type=float, default=-1.0,
                         help="max true peak in dBTP, avoids clipping (default: -1.0)")
    parser.add_argument("--lra", type=float, default=11.0,
                         help="target loudness range in LU (default: 11.0)")
    args = parser.parse_args()

    if shutil.which("ffmpeg") is None:
        raise SystemExit("Error: ffmpeg not found on PATH. Install it (e.g. `brew install ffmpeg`).")
    if not args.input_dir.is_dir():
        raise SystemExit(f"Error: input folder not found: {args.input_dir}")

    files = sorted(
        f for f in args.input_dir.iterdir()
        if f.is_file() and f.suffix.lower() in CODEC_ARGS
    )
    if not files:
        raise SystemExit(f"Error: no supported audio files ({', '.join(CODEC_ARGS)}) found in {args.input_dir}")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    failures = []
    for f in files:
        output_file = args.output_dir / f.name
        try:
            before = normalize_file(f, output_file, args.target_lufs, args.true_peak, args.lra)
            print(f"Normalized {f.name} ({before:.1f} LUFS -> {args.target_lufs:.1f} LUFS)")
        except RuntimeError as e:
            print(f"FAILED {f.name}: {e}", file=sys.stderr)
            failures.append(f.name)

    print(f"Done: {len(files) - len(failures)}/{len(files)} file(s) written to '{args.output_dir}'.")
    if failures:
        raise SystemExit(f"{len(failures)} file(s) failed: {', '.join(failures)}")


if __name__ == "__main__":
    main()
