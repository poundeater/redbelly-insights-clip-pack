"""Sample a stretch of video every 0.2 s, detect faces (OpenCV YuNet) and flag camera cuts.

usage: faces.py src.mp4 start end out.json

Output: {"W", "H", "samples": [{"t", "cut", "faces": [[x, y, w, h, score], ...]}]}
"""
import json
import os
import sys

import cv2
import numpy as np

src, start, end, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
model = os.environ.get("YUNET", os.path.join(os.environ.get("WORK", "work"), "models", "yunet.onnx"))

cap = cv2.VideoCapture(src)
W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
detector = cv2.FaceDetectorYN.create(model, "", (W // 2, H // 2), 0.6)
step = max(1, round(cap.get(cv2.CAP_PROP_FPS) * 0.2))
cap.set(cv2.CAP_PROP_POS_MSEC, start * 1000)

samples, prev, i = [], None, 0
while True:
    ok, frame = cap.read()
    if not ok:
        break
    t = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
    if t > end:
        break
    # A camera cut shows up as a large mean change in a tiny greyscale thumbnail.
    thumb = cv2.cvtColor(cv2.resize(frame, (64, 36)), cv2.COLOR_BGR2GRAY).astype(float)
    cut = prev is not None and np.abs(thumb - prev).mean() > 25
    prev = thumb
    if i % step == 0 or cut:
        _, found = detector.detect(cv2.resize(frame, (W // 2, H // 2)))
        faces = [] if found is None else [[float(v * 2) for v in r[:4]] + [float(r[14])] for r in found]
        samples.append({"t": round(t, 3), "cut": bool(cut), "faces": faces})
    i += 1

json.dump({"W": W, "H": H, "samples": samples}, open(out, "w"))
