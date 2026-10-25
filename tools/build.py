"""Render the clip pack described in clips.json, styled to the Redbelly DAO Task Board brand kit
(https://taskboard.redbellydao.network/brand): Be Vietnam Pro for all copy, JetBrains Mono for machine values
(episode and timestamp), slate surfaces, and #EF5350 as the single accent.

Look: the speaker fills the whole 9:16 frame. For the first seconds a solid slate sheet at the bottom carries
the DAO logo, the hook and the speaker's name and role, while the speaker stays visible above it. After that a
red topic tag, the name and role, and the source episode/timestamp sit at the top with a red progress bar, and
short phrase captions pop in over the lower third with Redbelly terms and figures in brand red.

For every clip this script
  1. plans a 9:16 crop per camera shot that keeps the speaker's face in frame (tools/faces.py data),
  2. aligns the proof-read subtitle text to Whisper word timestamps,
  3. writes an ASS overlay (opening sheet, tag, name line, source line, progress bar, captions) and an SRT,
  4. renders a 1080x1920, 30 fps H.264 MP4 with everything burned in and the logo on the opening sheet,
  5. normalises loudness to -14 LUFS / -1.5 dBTP with two-pass EBU R128 loudnorm.

usage: python3 tools/build.py [clip_id ...]        (WORK env var points at the work dir, default ./work)
"""
import difflib
import json
import os
import re
import statistics
import subprocess
import sys

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.environ.get("WORK", os.path.join(ROOT, "work"))
OUT_W, OUT_H, FPS = 1080, 1920, 30
CARD = 3.2                         # seconds the opening sheet stays up
SHEET_Y = 1100                     # top edge of the opening sheet (content stays above the platform UI zone)
LUFS, TRUE_PEAK, LRA = -14.0, -1.5, 11.0
FONT, MONO = "Be Vietnam Pro", "JetBrains Mono"
FONTS_DIR = os.path.join(ROOT, "assets", "fonts")
LOGO = os.path.join(ROOT, "assets", "brand", "dao-logo-on-dark.png")
LOGO_H = 132                       # logo file height on the sheet (the file carries its own clear space)

# Brand kit colours in ASS order (&HBBGGRR&).
RED = "&H5053EF&"                  # #EF5350 brand
TEXT = "&HF8F5F1&"                 # #f1f5f8 on-surface
TEXT2 = "&HD6CEC2&"                # #c2ced6 on-surface-variant
SURFACE = "&H17130C&"              # #0c1317 surface
EDGE = "&H413626&"                 # #263641 panel edge
INK = "&H0F0C07&"                  # #070c0f container lowest, used for caption outlines

# Terms drawn in brand red inside captions (matched case-sensitively on whole words/phrases).
EMPHASIS = ["Redbelly Network", "Redbelly", "Tokeniser", "Project Acacia", "Acacia", "AUDM", "PDTI", "MEV",
            "Open Markets", "RBA", "block explorer", "blockchain"]


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, text=True, **kw)


# ---------------------------------------------------------------- crop planning

def load_faces(clip):
    path = os.path.join(WORK, "faces", f"{clip['id']}.json")
    lo = min(p["start"] for p in clip["pieces"]) - 1
    hi = max(p["end"] for p in clip["pieces"]) + 1
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        run([sys.executable, os.path.join(ROOT, "tools", "faces.py"),
             os.path.join(WORK, "src", f"{clip['episode']}.mp4"), str(lo), str(hi), path])
    return json.load(open(path))


def pick_face(faces, rule):
    if not faces:
        return None
    big = max(f[2] for f in faces)
    cands = [f for f in faces if f[2] >= 0.6 * big]
    if rule == "left":
        return min(cands, key=lambda f: f[0])
    if rule == "right":
        return max(cands, key=lambda f: f[0])
    return max(faces, key=lambda f: f[2])


def plan_shots(clip, fd):
    """Split each piece at camera cuts and choose one static 9:16 crop per shot."""
    W, H, samples = fd["W"], fd["H"], fd["samples"]
    cuts = [s["t"] for s in samples if s["cut"]]
    shots = []
    for p in clip["pieces"]:
        bounds = [p["start"]] + [c for c in cuts if p["start"] + 0.3 < c < p["end"] - 0.3] + [p["end"]]
        for a, b in zip(bounds, bounds[1:]):
            ov = [o for o in clip.get("shot_overrides", []) if o["from"] <= a + 0.01 and a < o.get("to", 1e9)]
            ov = ov[-1] if ov else {}
            rule = ov.get("target", clip["target"])
            # A held frame is framed on the second of picture just before it.
            lo, hi = (ov["freeze_at"] - 1, ov["freeze_at"] + 0.01) if "freeze_at" in ov else (a, b)
            picked = [f for f in (pick_face(s["faces"], rule) for s in samples if lo <= s["t"] < hi) if f]
            cx = statistics.median(f[0] + f[2] / 2 for f in picked)
            cy = statistics.median(f[1] + f[3] / 2 for f in picked)
            fh = statistics.median(f[3] for f in picked)
            # Close-ups use the full frame height; wide shots zoom in, but never past 0.7 of the height.
            h = H if fh * 6.5 >= H or clip.get("full_height") else max(0.7 * H, fh * 6.5)
            h = int(h) // 2 * 2
            w = int(h * 9 / 16) // 2 * 2
            x = int(min(max(cx - w / 2, 0), W - w))
            y = int(min(max(cy - 0.32 * h, 0), H - h))
            inside = sum(1 for f in picked
                         if f[0] >= x and f[0] + f[2] <= x + w and f[1] >= y and f[1] + f[3] <= y + h)
            shots.append({"start": a, "end": b, "crop": [w, h, x, y], "target": rule, "freeze_at": ov.get("freeze_at"),
                          "face_samples": len(picked), "face_in_crop": inside})
    return shots


# ---------------------------------------------------------------- subtitle alignment

def norm(tok):
    t = re.sub(r"[^a-z0-9]", "", tok.lower())
    return t.replace("iz", "is").replace("yz", "ys")


def episode_words(ep):
    return [w for seg in json.load(open(os.path.join(WORK, "tx", f"{ep}.json"))) for w in seg["words"]]


def align_piece(piece, words):
    """Give every token of the proof-read text a start/end time from Whisper's words."""
    asr = [w for w in words if piece["start"] - 0.05 <= w["s"] < piece["end"]]
    toks = piece["text"].split()
    sm = difflib.SequenceMatcher(a=[norm(w["w"]) for w in asr], b=[norm(t) for t in toks], autojunk=False)
    times = [None] * len(toks)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            w = asr[blk.a + k]
            times[blk.b + k] = [max(w["s"], piece["start"]), min(w["e"], piece["end"])]
    matched = sum(t is not None for t in times)
    i = 0
    while i < len(toks):
        if times[i] is not None:
            i += 1
            continue
        j = i
        while j < len(toks) and times[j] is None:
            j += 1
        lo = times[i - 1][1] if i > 0 else piece["start"]
        hi = times[j][0] if j < len(toks) else piece["end"]
        step = max(hi - lo, 0.01) / (j - i)
        for k in range(i, j):
            times[k] = [lo + (k - i) * step, lo + (k - i + 1) * step]
        i = j
    return [{"w": t, "s": s, "e": e} for t, (s, e) in zip(toks, times)], matched, len(toks)


def mark_host(words):
    """Text inside [[...]] is the host speaking: strip the brackets and flag those words."""
    host = False
    for w in words:
        if w["w"].startswith("[["):
            host, w["w"] = True, w["w"][2:]
        w["host"] = w.get("host", host)
        if w["w"].endswith("]]"):
            host, w["w"] = False, w["w"][:-2]


def phrases(words, max_chars=22, max_words=5):
    """Short caption phrases: break on punctuation, pauses, length and word count."""
    out, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        text = " ".join(x["w"] for x in cur)
        if (nxt is None or w["w"][-1] in ".?!,;:" or len(cur) >= max_words or nxt.get("host") != w.get("host")
                or len(text) + 1 + len(nxt["w"]) > max_chars or nxt["s"] - w["e"] > 0.5):
            out.append(cur)
            cur = []
    return out


def ts_ass(t):
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def ts_srt(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def esc(s):
    return s.replace("\\", "\\\\").replace("{", "(").replace("}", ")")


def emphasise(text):
    out = esc(text)
    for term in EMPHASIS:
        out = re.sub(rf"(?<![\w{{]){re.escape(term)}(?!\w)", lambda m: f"{{\\c{RED}}}{m.group(0)}{{\\c{TEXT}}}", out)
    # Figures (e.g. 2019, 20 billion) are brand red too.
    out = re.sub(r"(?<![\w&])(\d[\d,.]*( billion| million| trillion)?)",
                 lambda m: f"{{\\c{RED}}}{m.group(0)}{{\\c{TEXT}}}", out)
    return out


def mmss(t):
    return f"{int(t // 60)}:{int(t % 60):02d}"


def write_subs(clip, episode, words, duration, ass_path, srt_path):
    ep_no = re.search(r"(\d+)$", episode["title"]).group(1)
    source = f"EP{ep_no} {mmss(clip['pieces'][0]['start'])}"
    hook = esc(clip["hook"]).replace("\n", "\\N")
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {OUT_W}
PlayResY: {OUT_H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{FONT},76,&H00F8F5F1,&H00F8F5F1,&H000F0C07,&H000F0C07,-1,0,0,0,100,100,0,0,1,6,0,5,64,64,0,1
Style: Hook,{FONT},64,&H00F8F5F1,&H00F8F5F1,&H00000000,&H00000000,-1,0,0,0,100,100,-1,0,1,0,0,7,72,72,0,1
Style: Name,{FONT},38,&H00F8F5F1,&H00F8F5F1,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,7,72,72,0,1
Style: Role,{FONT},30,&H00D6CEC2,&H00D6CEC2,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,72,72,0,1
Style: Tag,{FONT},28,&H00FFFFFF,&H00FFFFFF,&H005053EF,&H005053EF,-1,0,0,0,100,100,3,0,3,9,0,7,64,64,0,1
Style: Who,{FONT},38,&H00F8F5F1,&H00F8F5F1,&H3017130C,&H3017130C,-1,0,0,0,100,100,0,0,3,8,0,7,64,64,0,1
Style: Mono,{MONO},28,&H00D6CEC2,&H00D6CEC2,&H3017130C,&H3017130C,0,0,0,0,100,100,1,0,3,8,0,9,64,64,0,1
Style: Draw,{FONT},20,&H005053EF,&H005053EF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    end, card_end = ts_ass(duration), ts_ass(CARD)
    fade = "\\fad(220,280)"
    sheet = f"m 0 0 l {OUT_W} 0 {OUT_W} {OUT_H - SHEET_Y} 0 {OUT_H - SHEET_Y}"
    logo_w = round(LOGO_H * 1434 / 1024)
    hook_y = SHEET_Y + 36 + LOGO_H + 22
    ev = [
        # Opening sheet: solid slate, 1px panel edge, a red brand bar, then label, hook, name and role.
        f"Dialogue: 2,0:00:00.00,{card_end},Draw,,0,0,0,,{{\\an7\\pos(0,{SHEET_Y})\\1c{SURFACE}{fade}\\p1}}{sheet}",
        f"Dialogue: 3,0:00:00.00,{card_end},Draw,,0,0,0,,{{\\an7\\pos(0,{SHEET_Y})\\1c{EDGE}{fade}\\p1}}m 0 0 l {OUT_W} 0 {OUT_W} 2 0 2",
        f"Dialogue: 3,0:00:00.00,{card_end},Draw,,0,0,0,,{{\\an7\\pos(72,{SHEET_Y})\\1c{RED}{fade}\\p1}}m 0 0 l 120 0 120 8 0 8",
        f"Dialogue: 3,0:00:00.00,{card_end},Mono,,0,0,0,,{{\\an9\\pos(1008,{SHEET_Y + 60}){fade}\\bord0}}REDBELLY INSIGHTS\\N{source}",
        f"Dialogue: 3,0:00:00.10,{card_end},Hook,,0,0,0,,{{\\an7\\pos(72,{hook_y}){fade}}}{hook}",
        f"Dialogue: 3,0:00:00.35,{card_end},Name,,0,0,0,,{{\\an7\\pos(72,{hook_y + 196}){fade}}}{esc(clip['speaker'])}",
        f"Dialogue: 3,0:00:00.35,{card_end},Role,,0,0,0,,{{\\an7\\pos(72,{hook_y + 246}){fade}}}{esc(clip['role'])}",
        # After the sheet: red topic tag, name and role, source episode and timestamp, progress bar.
        f"Dialogue: 1,{card_end},{end},Tag,,0,0,0,,{{\\an7\\pos(64,92)\\fad(250,0)}}{esc(clip['tag'].upper())}",
        f"Dialogue: 1,{card_end},{end},Who,,0,0,0,,{{\\an7\\pos(64,156)\\fad(250,0)}}{esc(clip['speaker'])}"
        f"{{\\b0\\fs30\\c{TEXT2}}}\\N{esc(clip['role'])}",
        f"Dialogue: 1,{card_end},{end},Mono,,0,0,0,,{{\\an9\\pos(1016,96)\\fad(250,0)}}{source}",
        f"Dialogue: 4,0:00:00.00,{end},Draw,,0,0,0,,{{\\an7\\pos(0,0)\\clip(0,0,0,{OUT_H})"
        f"\\t(0,{int(duration * 1000)},\\clip(0,0,{OUT_W},{OUT_H}))\\p1}}m 0 0 l {OUT_W} 0 {OUT_W} 8 0 8",
    ]
    srt = []
    groups = phrases(words)
    for n, g in enumerate(groups):
        e = groups[n + 1][0]["s"] if n + 1 < len(groups) else min(duration, g[-1]["e"] + 0.5)
        e = min(e, g[-1]["e"] + 0.7)
        text = " ".join(w["w"] for w in g)
        # While the opening sheet is up, captions sit just above it.
        y = SHEET_Y - 110 if g[0]["s"] < CARD else 1400
        if g[0].get("host"):
            body = f"{{\\i1\\c{TEXT2}\\fs62}}{esc(text)}"
            text = "HOST: " + text
        else:
            body = emphasise(text)
        ev.append(f"Dialogue: 5,{ts_ass(g[0]['s'])},{ts_ass(e)},Cap,,0,0,0,,"
                  f"{{\\an5\\pos(540,{y})\\fscx90\\fscy90\\t(0,90,\\fscx100\\fscy100)}}{body}")
        srt.append(f"{n + 1}\n{ts_srt(g[0]['s'])} --> {ts_srt(e)}\n{text}\n")
    open(ass_path, "w").write(head + "\n".join(ev) + "\n")
    open(srt_path, "w").write("\n".join(srt))
    return len(groups), (64, SHEET_Y + 36, logo_w)


# ---------------------------------------------------------------- rendering

def shade_png(path):
    """Top and bottom shading so the white text reads on any background."""
    yy = np.linspace(0, 1, OUT_H)[:, None]
    alpha = np.clip(np.maximum((0.20 - yy) / 0.20 * 0.80, (yy - 0.58) / 0.42 * 0.78), 0, 1)
    img = np.zeros((OUT_H, OUT_W, 4), np.uint8)
    img[..., :3] = (23, 19, 12)    # #0c1317 (BGR): slate, never pure black
    img[..., 3] = (np.repeat(alpha, OUT_W, axis=1) * 255).astype(np.uint8)
    cv2.imwrite(path, img)


def render(clip, shots, ass_path, logo_box, out_path):
    src = os.path.join(WORK, "src", f"{clip['episode']}.mp4")
    duration = sum(p["end"] - p["start"] for p in clip["pieces"])
    shade = os.path.join(WORK, "shade.png")
    if not os.path.exists(shade):
        shade_png(shade)
    f = []
    for k, s in enumerate(shots):
        w, h, x, y = s["crop"]
        d = s["end"] - s["start"]
        if s.get("freeze_at") is not None:
            # Hold one frame of the speaker over a cutaway, with a slow push-in so it doesn't read as frozen.
            f.append(f"[0:v]trim=start={s['freeze_at']:.3f}:duration=0.04,setpts=PTS-STARTPTS,"
                     f"crop={w}:{h}:{x}:{y},scale={OUT_W}:{OUT_H}:flags=lanczos,unsharp=5:5:0.6,setsar=1,"
                     f"zoompan=z='1+0.06*on/{int(d * FPS)}':x='iw/2-iw/zoom/2':y='ih/3-ih/zoom/3':"
                     f"d={int(round(d * FPS))}:s={OUT_W}x{OUT_H}:fps={FPS},trim=duration={d:.3f}[v{k}]")
            continue
        f.append(f"[0:v]trim=start={s['start']:.3f}:end={s['end']:.3f},setpts=PTS-STARTPTS,"
                 f"crop={w}:{h}:{x}:{y},scale={OUT_W}:{OUT_H}:flags=lanczos,unsharp=5:5:0.6,"
                 f"setsar=1,fps={FPS}[v{k}]")
    f.append("".join(f"[v{k}]" for k in range(len(shots))) + f"concat=n={len(shots)}:v=1:a=0[pic]")
    for k, p in enumerate(clip["pieces"]):
        d = p["end"] - p["start"]
        f.append(f"[0:a]atrim=start={p['start']:.3f}:end={p['end']:.3f},asetpts=PTS-STARTPTS,"
                 f"aformat=sample_rates=48000:channel_layouts=stereo,"
                 f"afade=t=in:d=0.03,afade=t=out:st={d - 0.05:.3f}:d=0.05[a{k}]")
    f.append("".join(f"[a{k}]" for k in range(len(clip["pieces"]))) +
             f"concat=n={len(clip['pieces'])}:v=0:a=1[aud]")
    lx, ly, lw = logo_box
    f.append(f"[2:v]scale={lw}:{LOGO_H}:flags=lanczos,format=rgba,fade=t=in:st=0:d=0.22:alpha=1,"
             f"fade=t=out:st={CARD - 0.28:.2f}:d=0.28:alpha=1[logo]")
    f.append(f"[pic][1:v]overlay=0:0,ass={ass_path}:fontsdir={FONTS_DIR}[txt]")
    f.append(f"[txt][logo]overlay={lx}:{ly}:enable='lt(t,{CARD})',format=yuv420p[vout]")
    tmp = out_path + ".tmp.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-loop", "1", "-i", shade,
         "-loop", "1", "-t", f"{CARD + 0.5:.2f}", "-i", LOGO, "-filter_complex", ";".join(f),
         "-map", "[vout]", "-map", "[aud]", "-t", f"{duration:.3f}", "-c:v", "libx264", "-preset", "slow",
         "-crf", "18", "-profile:v", "high", "-r", str(FPS), "-c:a", "pcm_s16le", tmp])

    # Two-pass loudnorm so all six clips sit at the same loudness.
    meas = run(["ffmpeg", "-hide_banner", "-i", tmp, "-af",
                f"loudnorm=I={LUFS}:TP={TRUE_PEAK}:LRA={LRA}:print_format=json", "-f", "null", "-"],
               capture_output=True).stderr
    m = json.loads(meas[meas.rindex("{"):meas.rindex("}") + 1])
    af = (f"loudnorm=I={LUFS}:TP={TRUE_PEAK}:LRA={LRA}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:"
          f"linear=true,aresample=48000")
    run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-map", "0:v", "-map", "0:a", "-c:v", "copy",
         "-af", af, "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart",
         "-metadata", f"title={clip['speaker']} - {clip['tag']}", out_path])
    os.remove(tmp)


def main():
    cfg = json.load(open(os.path.join(ROOT, "clips.json")))
    want = set(sys.argv[1:])
    plan = {}
    for clip in cfg["clips"]:
        if want and clip["id"] not in want:
            continue
        ep = cfg["episodes"][clip["episode"]]
        shots = plan_shots(clip, load_faces(clip))
        words_all = episode_words(clip["episode"])
        words, offset, align = [], 0.0, []
        for p in clip["pieces"]:
            pw, matched, total = align_piece(p, words_all)
            align.append({"piece": [p["start"], p["end"]], "matched_tokens": matched, "tokens": total})
            for w in pw:
                words.append({"w": w["w"], "s": w["s"] - p["start"] + offset, "e": w["e"] - p["start"] + offset})
            mark_host(words)
            offset += p["end"] - p["start"]
        ass_path = os.path.join(WORK, f"{clip['id']}.ass")
        srt_path = os.path.join(ROOT, "subtitles", f"{clip['id']}.srt")
        n, logo_box = write_subs(clip, ep, words, offset, ass_path, srt_path)
        render(clip, shots, ass_path, logo_box, os.path.join(ROOT, "clips", f"{clip['id']}.mp4"))
        plan[clip["id"]] = {"duration": round(offset, 3), "shots": shots, "alignment": align, "subtitle_cues": n}
        print(clip["id"], f"{offset:.1f}s", f"{len(shots)} shots", align, flush=True)
    path = os.path.join(ROOT, "verification", "render_plan.json")
    old = json.load(open(path)) if os.path.exists(path) and want else {}
    old.update(plan)
    json.dump(old, open(path, "w"), indent=2)


if __name__ == "__main__":
    main()
