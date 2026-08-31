# normalize-volume

Got a folder of songs from all over (rips, downloads, different albums) that all play back at wildly different volumes? This script loudness-normalizes every song in a folder to the same target and writes the results to a destination folder, keeping ID3/metadata tags (and cover art) intact.

## What it does

1. **Scans** the input folder for supported audio files (mp3, m4a, mp4, aac, flac, wav, ogg, opus).
2. **Measures and normalizes** each file's loudness with ffmpeg's `loudnorm` filter (EBU R128), two-pass: pass 1 measures the input, pass 2 applies the correction using those measurements for an accurate single re-encode.
3. **Re-encodes** at the highest reasonable quality for that file's own format (see table below), so lossy re-encoding loses as little as possible.
4. **Preserves** all metadata tags and embedded cover art, and saves each file to the output folder under its original name.

## Requirements

- Python 3
- [ffmpeg](https://ffmpeg.org/) on your `PATH`

```
brew install ffmpeg
```

> Tested on macOS only.

## Usage

```
python normalize-volume.py INPUT_DIR OUTPUT_DIR
```

### Options

| Flag | Default | Description |
|---|---|---|
| `--target-lufs` | `-14.0` | Integrated loudness target in LUFS (`-14` is Spotify/YouTube Music's target; podcasts commonly use `-16`) |
| `--true-peak` | `-1.0` | Max true peak in dBTP, to avoid clipping |
| `--lra` | `11.0` | Target loudness range in LU |

Only files directly inside `INPUT_DIR` are processed (no subfolders).

### Output quality per format

| Format | Encoding |
|---|---|
| mp3 | libmp3lame, `-q:a 0` (~245-320kbps VBR) |
| m4a / mp4 / aac | AAC, 256kbps |
| flac | FLAC, max compression (lossless) |
| wav | 24-bit PCM (lossless) |
| ogg | Vorbis, `-q:a 10` (~500kbps) |
| opus | Opus, 192kbps |

## Example

```
python normalize-volume.py ./songs ./songs-normalized
```

```
Normalized track01.mp3 (-22.4 LUFS -> -14.0 LUFS)
Normalized track02.m4a (-9.1 LUFS -> -14.0 LUFS)
Done: 2/2 file(s) written to './songs-normalized'.
```

## Notes

- Normalizing a lossy file (mp3, aac, ...) means decoding then re-encoding, so it's not perfectly lossless — that's unavoidable once you touch the samples. The quality settings above aim for effectively transparent (inaudible) loss. flac and wav stay fully lossless.
- A file that fails to process doesn't stop the batch; it's reported at the end and the script exits non-zero if anything failed.
