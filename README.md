# lazy-scripts

Do you know when you need to do something that will take a lot of time and you are too lazy to do?

> **Note:** these scripts are written and tested on macOS. They may work elsewhere, but paths, dependencies (e.g. `brew install ...`), and behavior are only verified on macOS.

## Scripts

| Script | Description |
|---|---|
| [combine-photos](combine-photos/) | Pairs up photos and lays them side by side onto a single 10x15cm canvas, so photo kiosks print two smaller photos for the price of one. |
| [cut-bootleg](cut-bootleg/) | Cuts a big bootleg/concert audio file into individual song files using a tracklist text file, tagging each with title/artist/album/track number. |
| [normalize-volume](normalize-volume/) | Loudness-normalizes a folder of songs (mp3, m4a, aac, flac, wav, ...) to a consistent volume, re-encoding at the best quality per format and preserving metadata/cover art. |

## License

[MIT](LICENSE)

---
<!--
AGENT NOTE: Keep the "Scripts" table above in sync with the repo.
When a script is added, removed, or renamed (its own folder + README),
update this table to match: one row per script folder, linking to the
folder and summarizing what it does (pull the summary from that
script's own README).
-->
