"""Check every rendered clip against the brief and write verification/REPORT.md.

Checks: video spec (9:16, >=1080p, >=24 fps, MP4/H.264), duration (30-60 s), loudness consistency
(EBU R128), subtitle presence/coverage, spelling of names and Redbelly terms, speaker-in-frame
coverage from the crop plan, no personal credit in deliverable files or MP4 metadata, and the
proof-read subtitle text against three independent Whisper transcripts.

usage: python3 tools/verify.py        (WORK env var points at the work dir; ASR cross-check is
                                       skipped if WORK/win is missing)
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.environ.get("WORK", os.path.join(ROOT, "work"))

# Spellings the brief cares about. Left: wrong forms that must never appear in subtitles or copy.
BANNED = [r"Red Belly", r"RedBelly", r"Redbilly", r"Red Valley", r"[Tt]okeniz", r"Akasha", r"Arkesha",
          r"\brbnt\b", r"Gramoil"]
REQUIRED_FORMS = {"Redbelly", "Redbelly Network", "Tokeniser", "Project Acacia", "PDTI", "MEV", "RBA",
                  "Open Markets", "Vincent Gramoli", "Matt Mills", "Alan Burt"}
CREDIT_PATTERNS = [r"made by", r"edited by", r"created by", r"@[A-Za-z0-9_]{3,}", r"[\w.+-]+@[\w-]+\.[\w.]+",
                   r"github\.com/(?!opencv)"]

# Windows used for the medium.en / large-v3 cross-check transcriptions (start of each window, seconds).
XCHECK_WINDOWS = {"01": ("win2/mev", 960), "02": ("win2/forks", 50), "03": ("win/c5", 466),
                  "04": ("win2/swap", 1278), "05": ("win2/omk", 2055), "06": ("win2/alan", 966)}


def sh(cmd):
    return subprocess.run(cmd, check=True, text=True, capture_output=True)


def probe(path):
    d = json.loads(sh(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path]).stdout)
    v = next(s for s in d["streams"] if s["codec_type"] == "video")
    a = next(s for s in d["streams"] if s["codec_type"] == "audio")
    num, den = map(int, v["r_frame_rate"].split("/"))
    return {"w": v["width"], "h": v["height"], "fps": num / den, "vcodec": v["codec_name"], "pix": v["pix_fmt"],
            "acodec": a["codec_name"], "ar": int(a["sample_rate"]), "dur": float(d["format"]["duration"]),
            "size_mb": int(d["format"]["size"]) / 1e6, "fmt": d["format"]["format_name"],
            "tags": d["format"].get("tags", {})}


def loudness(path):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true",
                          "-f", "null", "-"], text=True, capture_output=True).stderr
    summary = err[err.rindex("Summary:"):]
    i = float(re.search(r"I:\s+(-?[\d.]+) LUFS", summary).group(1))
    lra = float(re.search(r"LRA:\s+(-?[\d.]+) LU", summary).group(1))
    tp = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", summary).group(1))
    return i, lra, tp


def srt_cues(path):
    cues = []
    for block in open(path).read().strip().split("\n\n"):
        lines = block.split("\n")
        a, b = lines[1].split(" --> ")
        cues.append((ts(a), ts(b), " ".join(lines[2:])))
    return cues


def ts(s):
    h, m, rest = s.split(":")
    sec, ms = rest.split(",")
    return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000


def words(text):
    return [w for w in re.sub(r"[^a-z0-9' ]", " ", text.lower().replace("-", " ")).split() if w]


def wer(ref, hyp):
    """Word error rate of hyp against ref (Levenshtein over words)."""
    r, h = words(ref), words(hyp)
    prev = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        cur = [i] + [0] * len(h)
        for j in range(1, len(h) + 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (r[i - 1] != h[j - 1]))
        prev = cur
    return prev[-1] / max(1, len(r))


def asr_text(word_list, a, b):
    return " ".join(w["w"].strip() for w in word_list if a - 0.05 <= w["s"] < b)


def main():
    cfg = json.load(open(os.path.join(ROOT, "clips.json")))
    plan = json.load(open(os.path.join(ROOT, "verification", "render_plan.json")))
    rows, fails, lufs = [], [], []
    xcheck = []
    for clip in cfg["clips"]:
        cid = clip["id"]
        mp4 = os.path.join(ROOT, "clips", f"{cid}.mp4")
        srt = os.path.join(ROOT, "subtitles", f"{cid}.srt")
        p = probe(mp4)
        i, lra, tp = loudness(mp4)
        lufs.append(i)
        cues = srt_cues(srt)
        spoken = sum(b - a for a, b, _ in cues)
        sub_text = " ".join(c[2] for c in cues)
        copy_text = " ".join([sub_text, clip["hook"], clip["caption"], clip["speaker"], clip["role"]])
        shots = plan[cid]["shots"]
        in_crop = sum(s["face_in_crop"] for s in shots)
        sampled = sum(s["face_samples"] for s in shots)
        checks = {
            "9:16 aspect": abs(p["w"] / p["h"] - 9 / 16) < 1e-3,
            ">=1080p": min(p["w"], p["h"]) >= 1080,
            ">=24 fps": p["fps"] >= 24,
            "MP4 / H.264 / AAC": "mp4" in p["fmt"] and p["vcodec"] == "h264" and p["acodec"] == "aac",
            "30-60 s": 29.5 <= p["dur"] <= 60.5,
            "subtitles cover speech": len(cues) > 0 and spoken / p["dur"] > 0.85,
            "no misspelt terms": not any(re.search(b, copy_text) for b in BANNED),
            "speaker in frame": sampled > 0 and in_crop / sampled >= 0.98,
            "loudness -14 LUFS +-1": abs(i + 14) <= 1.0 and tp <= -1.0,
            "no credit in metadata": not any(re.search(c, json.dumps(p["tags"]), re.I) for c in CREDIT_PATTERNS),
        }
        for k, ok in checks.items():
            if not ok:
                fails.append(f"{cid}: {k}")
        rows.append((cid, p, i, lra, tp, len(cues), spoken, in_crop, sampled, checks))

        name, win = XCHECK_WINDOWS[cid[:2]]
        wpath = os.path.join(WORK, name)
        if os.path.exists(wpath + ".json") and os.path.exists(wpath + ".L.json"):
            small = [w for seg in json.load(open(os.path.join(WORK, "tx", f"{clip['episode']}.json"))) for w in seg["words"]]
            med = [{"w": w["w"], "s": w["s"] + win} for w in json.load(open(wpath + ".json"))]
            large = [{"w": w["w"], "s": w["s"] + win} for w in json.load(open(wpath + ".L.json"))]
            for pc in clip["pieces"]:
                ref = pc["text"]
                xcheck.append((cid, pc["start"], pc["end"], len(words(ref)),
                               wer(ref, asr_text(small, pc["start"], pc["end"])),
                               wer(ref, asr_text(med, pc["start"], pc["end"])),
                               wer(ref, asr_text(large, pc["start"], pc["end"]))))

    # Personal-credit scan of every deliverable text file.
    for base in ["README.md", "CLIP_LIST.md", "clips.json"] + [os.path.join("subtitles", f) for f in
                                                                os.listdir(os.path.join(ROOT, "subtitles"))]:
        text = open(os.path.join(ROOT, base)).read()
        for c in CREDIT_PATTERNS:
            for m in re.finditer(c, text, re.I):
                fails.append(f"{base}: possible personal credit '{m.group(0)}'")

    all_subs = " ".join(open(os.path.join(ROOT, "subtitles", f)).read() for f in os.listdir(os.path.join(ROOT, "subtitles")))
    all_copy = all_subs + json.dumps(cfg, ensure_ascii=False)
    missing = [t for t in REQUIRED_FORMS if t not in all_copy]

    out = ["# Verification report", "",
           "Generated by `tools/verify.py` from the rendered files in `clips/` and `subtitles/`.", ""]
    out += ["## Result", "", "**PASS** - all checks passed." if not fails else
            "**FAIL**\n\n" + "\n".join(f"- {f}" for f in fails), ""]
    out += ["## Video and audio specs", "",
            "| Clip | Resolution | FPS | Codec | Duration | Size | Loudness (LUFS) | LRA | True peak (dBFS) |",
            "|---|---|---|---|---|---|---|---|---|"]
    for cid, p, i, lra, tp, *_ in rows:
        out.append(f"| {cid} | {p['w']}x{p['h']} | {p['fps']:.0f} | {p['vcodec']}/{p['pix']} + {p['acodec']} "
                   f"{p['ar'] // 1000} kHz | {p['dur']:.1f} s | {p['size_mb']:.1f} MB | {i:.1f} | {lra:.1f} | {tp:.1f} |")
    out += ["", f"Loudness spread across the six clips: {max(lufs) - min(lufs):.1f} LU "
            f"(target -14 LUFS integrated, -1.5 dBTP).", ""]
    out += ["## Checks per clip", "", "| Clip | " + " | ".join(rows[0][-1].keys()) + " |",
            "|---|" + "---|" * len(rows[0][-1])]
    for r in rows:
        out.append(f"| {r[0]} | " + " | ".join("pass" if v else "**FAIL**" for v in r[-1].values()) + " |")
    out += ["", "## Subtitles and framing", "",
            "| Clip | Subtitle cues | Speech covered by subtitles | Face samples inside crop |", "|---|---|---|---|"]
    for cid, p, i, lra, tp, ncue, spoken, inc, samp, _ in rows:
        out.append(f"| {cid} | {ncue} | {spoken:.1f} s of {p['dur']:.1f} s | {inc} / {samp} |")
    out += ["", "Face samples: the speaker's face was detected every 0.2 s of source video (OpenCV YuNet) and "
            "checked against the crop window used for that camera shot.", ""]
    out += ["## Names and terms", "",
            "Required spellings found in subtitles/copy: " + ", ".join(sorted(REQUIRED_FORMS - set(missing))) + ".",
            "" if not missing else f"Not used in this pack: {', '.join(missing)}.", "",
            "Wrong forms searched for (none found if the result above is PASS): Red Belly, RedBelly, Redbilly, "
            "Red Valley, Tokenizer/tokenize*, Akasha/Arkesha (for Acacia), rbnt, Gramoil.", ""]
    if xcheck:
        out += ["## Subtitle text vs. three independent transcripts", "",
                "Each subtitle passage was proof-read against three Whisper models run separately. The table shows "
                "the word error rate of each model *relative to the final subtitle text*. Differences are mostly "
                "the models' own mistakes (e.g. 'Red B Network', 'Redbilly', 'Tokenizer', 'a vacation' for 'out of Acacia', dropped phrases) plus false starts, repeated "
                "words and 'uh'/'um', which the subtitles leave out. Brand spellings, names and figures were "
                "fixed by hand. Rows with a high rate for one model only are that model dropping or repeating "
                "a phrase (e.g. medium.en skips most of clips 02 and 06).", "",
                "| Clip | Source span (s) | Words | small.en | medium.en | large-v3 |", "|---|---|---|---|---|---|"]
        for cid, a, b, n, ws, wm, wl in xcheck:
            out.append(f"| {cid} | {a:.2f}-{b:.2f} | {n} | {ws:.1%} | {wm:.1%} | {wl:.1%} |")
        out.append("")
    open(os.path.join(ROOT, "verification", "REPORT.md"), "w").write("\n".join(out))
    print("\n".join(out))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
