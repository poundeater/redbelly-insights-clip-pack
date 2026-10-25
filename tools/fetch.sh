#!/usr/bin/env bash
# Download the source episodes named in clips.json from redbelly.network's own hosting,
# extract 16 kHz mono audio and fetch the YuNet face-detection model.
set -euo pipefail
cd "$(dirname "$0")/.."
WORK=${WORK:-work}
mkdir -p "$WORK"/{src,aud,models,tx,faces}
python3 -c 'import json;[print(k,v["url"]) for k,v in json.load(open("clips.json"))["episodes"].items()]' |
while read -r ep url; do
  [ -s "$WORK/src/$ep.mp4" ] || curl -sSL "$url" -o "$WORK/src/$ep.mp4"
  [ -s "$WORK/aud/$ep.wav" ] || ffmpeg -v error -y -i "$WORK/src/$ep.mp4" -vn -ac 1 -ar 16000 "$WORK/aud/$ep.wav"
done
[ -s "$WORK/models/yunet.onnx" ] || curl -sSL -o "$WORK/models/yunet.onnx" \
  https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx
