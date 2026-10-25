"""Write CLIP_LIST.md (source episode, timestamps and post caption for every clip) from clips.json."""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def mmss(t):
    return f"{int(t // 60)}:{t % 60:05.2f}"


def main():
    cfg = json.load(open(os.path.join(ROOT, "clips.json")))
    out = ["# Clip list", "",
           "Six vertical clips from the latest official Redbelly Insights episodes (https://redbelly.network/ama). "
           "Each clip is one continuous passage from the episode, with no cuts inside it.", "",
           "Timestamps are `m:ss.ss` from the start of the official episode video linked in each entry.", "",
           "| # | File | Source episode | Source timestamp | Length | Speaker | Suggested post caption |",
           "|---|---|---|---|---|---|---|"]
    for n, c in enumerate(cfg["clips"], 1):
        ep = cfg["episodes"][c["episode"]]
        ts = " + ".join(f"{mmss(p['start'])}-{mmss(p['end'])}" for p in c["pieces"])
        dur = sum(p["end"] - p["start"] for p in c["pieces"])
        out.append(f"| {n} | `clips/{c['id']}.mp4` | {ep['title']} ({ep['date']}) | {ts} | {dur:.0f} s | "
                   f"{c['speaker']}, {c['role']} | {c['caption']} |")
    out += ["", "## Details", ""]
    for n, c in enumerate(cfg["clips"], 1):
        ep = cfg["episodes"][c["episode"]]
        out += [f"### {n}. {c['hook'].replace(chr(10), ' ')}", "",
                f"- **File:** `clips/{c['id']}.mp4`. Subtitles are burned in and also in `subtitles/{c['id']}.srt`.",
                f"- **Source:** {ep['title']}, {ep['date']}. Video: {ep['url']}",
                "- **Timestamp:** " + "; ".join(f"{mmss(p['start'])} to {mmss(p['end'])}" for p in c["pieces"]),
                f"- **Speaker:** {c['speaker']}, {c['role']}",
                f"- **Topic:** {c['topic']}",
                f"- **The one point:** {c['point']}",
                f"- **Suggested post caption:** {c['caption']}"]
        for note in c.get("omitted", []):
            out.append(f"- **Note:** {note}")
        out.append("")
    open(os.path.join(ROOT, "CLIP_LIST.md"), "w").write("\n".join(out))


if __name__ == "__main__":
    main()
