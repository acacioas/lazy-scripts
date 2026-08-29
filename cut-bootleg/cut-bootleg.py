#!/usr/bin/env python3
"""
cut-bootleg.py

Split one big audio file (a bootleg/concert recording) into individual
song files using a tracklist text file, and tag each output with the
right ID3 (or equivalent) metadata.

Tracklist format, one line per song:
    TIME [ARTIST -] TITLE

    00:00:00 Intro
    00:03:12 Radiohead - Airbag
    00:07:45 Karma Police

- TIME can be HH:MM:SS, MM:SS, or just SS (fractional seconds allowed).
- "ARTIST - TITLE" is optional per line; if omitted, --artist is used.
- Blank lines and lines starting with # are ignored.
- Each song runs from its timestamp to the next song's timestamp (or to
  the end of the file for the last entry).

Usage:
    python cut-bootleg.py INPUT_AUDIO TRACKLIST.txt OUTPUT_DIR --album "Live at X"

Cutting is done with ffmpeg stream copy (-c copy): fast and lossless,
cut points snap to the nearest audio frame (imperceptible for music).
"""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

TIME_RE = re.compile(r"^(\d+(?::\d+){0,2}(?:\.\d+)?)\s+(.+)$")


def parse_timestamp(text: str) -> float:
    parts = text.split(":")
    seconds = 0.0
    for part in parts:
        seconds = seconds * 60 + float(part)
    return seconds


def parse_tracklist(path: Path, default_artist: str):
    tracks = []
    for lineno, raw in enumerate(path.read_text().splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = TIME_RE.match(line)
        if not m:
            raise SystemExit(f"Error: {path}:{lineno}: can't parse line: {raw!r}")
        start = parse_timestamp(m.group(1))
        rest = m.group(2).strip()
        if " - " in rest:
            artist, title = rest.split(" - ", 1)
        else:
            artist, title = default_artist, rest
        tracks.append({"start": start, "artist": artist.strip(), "title": title.strip()})

    for i, track in enumerate(tracks):
        track["end"] = tracks[i + 1]["start"] if i + 1 < len(tracks) else None
    return tracks


def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "-", name).strip()


def cut_track(input_file: Path, output_file: Path, start: float, end, reencode: bool, metadata: dict):
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-ss", str(start), "-i", str(input_file)]
    if end is not None:
        cmd += ["-t", str(end - start)]
    cmd += ["-c", "copy"] if not reencode else []
    for key, value in metadata.items():
        cmd += ["-metadata", f"{key}={value}"]
    cmd.append(str(output_file))

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(f"Error: ffmpeg failed on '{output_file.name}':\n{result.stderr}")


def main():
    parser = argparse.ArgumentParser(description="Cut a bootleg/concert audio file into individual songs.")
    parser.add_argument("input_file", type=Path, help="big audio file to cut (mp3, aac, m4a, ...)")
    parser.add_argument("tracklist", type=Path, help="text file with 'TIME [ARTIST -] TITLE' per line")
    parser.add_argument("output_dir", type=Path, help="directory to write the individual songs to")
    parser.add_argument("--album", required=True, help="album/concert title, written to each track's tag")
    parser.add_argument("--artist", default="", help="default artist for lines without 'ARTIST - '")
    parser.add_argument("--year", default=None, help="release year, written to each track's tag")
    parser.add_argument("--start-index", type=int, default=1, help="starting track number (default: 1)")
    parser.add_argument("--reencode", action="store_true",
                         help="re-encode instead of stream-copy for frame-accurate cuts (slower)")
    args = parser.parse_args()

    if shutil.which("ffmpeg") is None:
        raise SystemExit("Error: ffmpeg not found on PATH. Install it (e.g. `brew install ffmpeg`).")
    if not args.input_file.is_file():
        raise SystemExit(f"Error: input file not found: {args.input_file}")
    if not args.tracklist.is_file():
        raise SystemExit(f"Error: tracklist not found: {args.tracklist}")

    tracks = parse_tracklist(args.tracklist, args.artist)
    if not tracks:
        raise SystemExit(f"Error: no tracks found in {args.tracklist}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    ext = args.input_file.suffix
    total = len(tracks)
    width = len(str(total + args.start_index - 1))

    for i, track in enumerate(tracks):
        track_num = args.start_index + i
        filename = f"{str(track_num).zfill(width)} - {sanitize_filename(track['title'])}{ext}"
        output_file = args.output_dir / filename

        metadata = {
            "title": track["title"],
            "artist": track["artist"],
            "album": args.album,
            "track": f"{track_num}/{total}",
        }
        if args.year:
            metadata["date"] = args.year

        cut_track(args.input_file, output_file, track["start"], track["end"], args.reencode, metadata)
        duration = f"{track['end'] - track['start']:.1f}s" if track["end"] else "to end"
        print(f"Saved {output_file} ({duration})")

    print(f"Done: {total} track(s) written to '{args.output_dir}'.")


if __name__ == "__main__":
    main()
