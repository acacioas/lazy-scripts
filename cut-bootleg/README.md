# cut-bootleg

Got a bootleg recording (a whole concert or DJ set as one big audio file) and want it split into the individual songs? This script cuts a big audio file into one file per track, using a plain-text tracklist for the timestamps, and tags each output file with title/artist/album/track number.

## What it does

1. **Reads a tracklist** text file with one song per line: a timestamp, and an optional artist and title.
2. **Cuts** the input audio at each timestamp (to the next song's timestamp, or the end of the file for the last one) using `ffmpeg -c copy` — fast, lossless, no re-encoding.
3. **Tags** each output file's metadata (title, artist, album, track number, and optionally year) so it shows up correctly in any music player.
4. **Saves** each track to the output directory as `<track number> - <title>.<original extension>`.

## Requirements

- Python 3
- [ffmpeg](https://ffmpeg.org/) on your `PATH`

```
brew install ffmpeg
```

> Tested on macOS only.

## Usage

```
python cut-bootleg.py INPUT_AUDIO TRACKLIST.txt OUTPUT_DIR --album "Live at X"
```

### Tracklist format

One song per line: `TIME [ARTIST -] TITLE`

```
# lines starting with # and blank lines are ignored
00:00:00 Intro
00:03:12 Radiohead - Airbag
00:07:45 Karma Police
01:02:30 Radiohead - Encore: Creep
```

- `TIME` can be `HH:MM:SS`, `MM:SS`, or just seconds, with optional decimals (e.g. `90.5`).
- `ARTIST - ` is optional per line; when omitted, `--artist` is used for that track.
- Track numbers are assigned in file order (1, 2, 3, ... or starting from `--start-index`).

### Options

| Flag | Default | Description |
|---|---|---|
| `--album` | *(required)* | Album/concert title, written to every track's tag |
| `--artist` | `""` | Default artist for lines without `ARTIST - ` |
| `--year` | none | Release year, written to every track's tag |
| `--start-index` | `1` | Starting track number |
| `--reencode` | off | Re-encode instead of stream-copy, for frame-accurate cuts (slower) |

Input formats: anything ffmpeg can read (mp3, aac, m4a, wav, flac, ...). Output keeps the same container/codec as the input (stream copy by default).

## Example

```
python cut-bootleg.py bootleg.mp3 tracklist.txt ./songs --album "Live at Wembley" --artist "Radiohead" --year 2003
```

```
Saved songs/1 - Intro.mp3 (192.0s)
Saved songs/2 - Airbag.mp3 (273.0s)
Saved songs/3 - Karma Police.mp3 (255.0s)
Done: 3 track(s) written to './songs'.
```

## Notes

- Stream-copy cuts snap to the nearest audio frame, which can shift a cut point by a few milliseconds — inaudible for splitting songs. Pass `--reencode` if you need sample-accurate cuts (slower, and lossy formats will be re-encoded).
