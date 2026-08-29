#!/usr/bin/env python3
"""Self-check for the tracklist parsing logic (the part with actual branches)."""

import importlib.util
import tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location("cut_bootleg", Path(__file__).parent / "cut-bootleg.py")
cut_bootleg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cut_bootleg)
parse_timestamp = cut_bootleg.parse_timestamp
parse_tracklist = cut_bootleg.parse_tracklist


def test_parse_timestamp():
    assert parse_timestamp("5") == 5.0
    assert parse_timestamp("1:30") == 90.0
    assert parse_timestamp("1:00:00") == 3600.0
    assert parse_timestamp("0:03.5") == 3.5


def test_parse_tracklist(tmp_path: Path):
    tracklist = tmp_path / "tracklist.txt"
    tracklist.write_text(
        "# comment, should be skipped\n"
        "\n"
        "00:00 The Testers - Intro Jam\n"
        "00:03.5 Second Song\n"
        "00:07 Artist Two - Outro\n"
    )
    tracks = parse_tracklist(tracklist, default_artist="Default Artist")

    assert len(tracks) == 3
    assert tracks[0] == {"start": 0.0, "artist": "The Testers", "title": "Intro Jam", "end": 3.5}
    assert tracks[1] == {"start": 3.5, "artist": "Default Artist", "title": "Second Song", "end": 7.0}
    assert tracks[2] == {"start": 7.0, "artist": "Artist Two", "title": "Outro", "end": None}


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        test_parse_timestamp()
        test_parse_tracklist(Path(tmp))
    print("OK")
