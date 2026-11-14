#!/bin/bash
# Render every composition in out/ to renders/, one at a time (memory), plus a cover JPG at 3s.
cd "$(dirname "$0")"; mkdir -p renders
for d in out/*/; do
  n=$(basename "$d"); o="renders/fairmind-$n.mp4"
  [ -s "$o" ] && continue
  (cd "$d" && HYPERFRAMES_RENDER_DETACHED=1 npx hyperframes render --quality delivery --output "../../$o" > /dev/null 2> "../../renders/$n.err") || { echo "FAILED $n"; tail -5 "renders/$n.err"; continue; }
  rm -f "renders/$n.err"
  ffmpeg -y -v error -ss 3 -i "$o" -frames:v 1 -q:v 2 "renders/fairmind-$n.jpg"
  echo "$n $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$o")s $(ffmpeg -i "$o" -af ebur128 -f null - 2>&1 | grep -E '^\s+I:' | tail -1 | xargs)"
done
