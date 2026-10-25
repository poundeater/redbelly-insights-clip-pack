"""Transcribe a 16 kHz mono WAV with faster-whisper and keep word timestamps.

usage: transcribe.py MODEL in.wav out.json [threads]
"""
import json
import sys
import wave

import numpy as np
from faster_whisper import WhisperModel

PROMPT = ("Redbelly Network, Redbelly Insights, RBNT, Tokeniser, Project Acacia, Vincent Gramoli, "
          "Alan Burt, Matt Mills, Drew Bradford, Effie Dimitropoulos, tokenisation, RWA, blockchain, consensus.")

model = WhisperModel(sys.argv[1], device="cpu", compute_type="int8",
                     cpu_threads=int(sys.argv[4]) if len(sys.argv) > 4 else 4)
wf = wave.open(sys.argv[2])
audio = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(np.float32) / 32768
segs, _ = model.transcribe(audio, language="en", word_timestamps=True, vad_filter=True, initial_prompt=PROMPT)
out = []
for s in segs:
    out.append({"start": s.start, "end": s.end, "text": s.text,
                "words": [{"s": w.start, "e": w.end, "w": w.word} for w in s.words]})
    print(f"[{s.start:8.1f}] {s.text}", flush=True)
json.dump(out, open(sys.argv[3], "w"))
