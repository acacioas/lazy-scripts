#!/usr/bin/env python3
"""Self-check: loudnorm JSON parsing, and a real end-to-end normalize on a generated tone."""

import importlib.util
import subprocess
import tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location("normalize_volume", Path(__file__).parent / "normalize-volume.py")
normalize_volume = importlib.util.module_from_spec(spec)
spec.loader.exec_module(normalize_volume)


def test_loudnorm_json_extraction():
    stderr = (
        "[Parsed_loudnorm_0 @ 0x0] some banner text\n"
        '{\n  "input_i" : "-30.00",\n  "input_tp" : "-10.00",\n'
        '  "input_lra" : "3.00",\n  "input_thresh" : "-40.00",\n'
        '  "target_offset" : "0.50"\n}\n'
    )
    match = normalize_volume.LOUDNORM_JSON_RE.search(stderr)
    assert match is not None
    stats = normalize_volume.json.loads(match.group(0))
    assert stats["input_i"] == "-30.00"
    assert stats["target_offset"] == "0.50"


def test_normalize_file_hits_target_and_keeps_metadata(tmp_path: Path):
    input_file = tmp_path / "quiet.mp3"
    output_file = tmp_path / "out" / "quiet.mp3"
    output_file.parent.mkdir()

    # A quiet sine tone, tagged with a title, well below the -14 LUFS target.
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
         "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
         "-af", "volume=-30dB", "-metadata", "title=Test Song",
         "-c:a", "libmp3lame", "-q:a", "4", str(input_file)],
        check=True,
    )

    before = normalize_volume.normalize_file(input_file, output_file, target_i=-14.0, true_peak=-1.0, lra=11.0)
    assert before < -20  # confirms the input really was quiet

    after_stats = normalize_volume.measure_loudness(output_file, target_i=-14.0, true_peak=-1.0, lra=11.0)
    after = float(after_stats["input_i"])
    assert abs(after - (-14.0)) < 1.5  # landed close to target, well above the original

    tags = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format_tags=title",
         "-of", "default=noprint_wrappers=1:nokey=1", str(output_file)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert tags == "Test Song"


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        test_loudnorm_json_extraction()
        test_normalize_file_hits_target_and_keeps_metadata(Path(tmp))
    print("OK")
