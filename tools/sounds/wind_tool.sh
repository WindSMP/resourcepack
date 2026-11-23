#!/usr/bin/env bash
# The wind tools' mining sound (assets/windsmp/sounds/tool/wind1-4.ogg): a wind strike (strike.py), four slightly
# different takes so it never repeats exactly. Needs python3 and ffmpeg. Run from the pack root.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"; out=assets/windsmp/sounds/tool; tmp="$(mktemp -d)"
mkdir -p "$out"
i=0
for spec in "11 0.26 1500 320 2.6 95" "23 0.28 1300 280 2.8 85" "37 0.24 1700 360 2.4 105" "51 0.27 1400 300 2.7 90"; do
  set -- $spec   # seed, length (s), gust band from and to (Hz), resonance, thump (Hz)
  i=$((i+1))
  python3 "$here/strike.py" "$tmp/raw$i.wav" "$@"
  ffmpeg -loglevel error -y -i "$tmp/raw$i.wav" -af "loudnorm=I=-22:TP=-5:LRA=7,aresample=44100" -ac 1 -c:a libvorbis -q:a 5 "$out/wind$i.ogg"
done
rm -rf "$tmp"
