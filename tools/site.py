"""Build the static review page: index.html, assets/posters/*.webp and og.png.

Everything on the page is read from clips.json, subtitles/*.srt and verification/report.json (written by
tools/verify.py), so the page never drifts from the files it describes. The page follows the Redbelly DAO
Task Board brand kit (assets/site.css). No build step is needed to host it: deploy the repository root.

usage: python3 tools/site.py            (SITE_URL=https://example.org makes og:image an absolute URL)
"""
import html
import json
import os
import subprocess
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.environ.get("WORK", os.path.join(ROOT, "work"))
SITE_URL = os.environ.get("SITE_URL", "").rstrip("/")
POSTER_AT = 1.7                       # seconds into each clip: the opening sheet with logo and hook is up
FONT_BOLD = os.path.join(ROOT, "assets", "fonts", "BeVietnamPro-Bold.ttf")
FONT_REG = os.path.join(ROOT, "assets", "fonts", "BeVietnamPro-Regular.ttf")
FONT_MONO = os.path.join(ROOT, "assets", "fonts", "JetBrainsMono-Medium.ttf")
LOGO_DARK = os.path.join(ROOT, "assets", "brand", "dao-logo-on-dark.png")

e = html.escape

ICON_DOWNLOAD = ('<svg viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M8 2v8m0 0L5 7m3 3 3-3M3 13h10" '
                 'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>')
ICON_PLAY = ('<svg viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M5 3.5v9l7-4.5-7-4.5Z" '
             'stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>')
ICON_COPY = ('<svg viewBox="0 0 16 16" fill="none" aria-hidden="true"><rect x="5" y="5" width="8" height="8" rx="1" '
             'stroke="currentColor" stroke-width="1.6"/><path d="M3 11V4a1 1 0 0 1 1-1h7" stroke="currentColor" '
             'stroke-width="1.6" stroke-linecap="round"/></svg>')
ICON_THEME = ('<svg viewBox="0 0 16 16" fill="none" aria-hidden="true"><circle cx="8" cy="8" r="5.5" stroke="currentColor" '
              'stroke-width="1.6"/><path d="M8 2.5v11a5.5 5.5 0 0 0 0-11Z" fill="currentColor"/></svg>')


def mmss(t):
    s = int(round(t))
    return f"{s // 60}:{s % 60:02d}"


def run(cmd):
    subprocess.run(cmd, check=True)


def srt_text(path):
    lines = []
    for block in open(path).read().strip().split("\n\n"):
        lines.append(" ".join(block.split("\n")[2:]))
    return " ".join(lines)


def make_posters(clips):
    os.makedirs(os.path.join(ROOT, "assets", "posters"), exist_ok=True)
    for c in clips:
        out = os.path.join(ROOT, "assets", "posters", f"{c['id']}.webp")
        run(["ffmpeg", "-v", "error", "-y", "-ss", str(POSTER_AT), "-i", os.path.join(ROOT, "clips", f"{c['id']}.mp4"),
             "-frames:v", "1", "-vf", "scale=540:960:flags=lanczos", "-c:v", "libwebp", "-quality", "86", out])


def make_og(clips, total_s):
    """1200x630 Open Graph card (the brand kit's size for linked pages), drawn with ffmpeg."""
    os.makedirs(WORK, exist_ok=True)
    texts = {"t1": "Redbelly Insights", "t2": "Podcast clip pack",
             "t3": "Six captioned vertical clips on Redbelly",
             "t4": "technology, Project Acacia and Tokeniser.",
             "t5": f"6 CLIPS   1080x1920   30 FPS   {mmss(total_s)} TOTAL"}
    for k, v in texts.items():
        open(os.path.join(WORK, f"og_{k}.txt"), "w").write(v)
    posters = [os.path.join(ROOT, "assets", "posters", f"{c['id']}.webp") for c in clips[:3]]
    inputs = ["-f", "lavfi", "-i", "color=c=0x0c1317:s=1200x630:d=1", "-i", LOGO_DARK]
    for p in posters:
        inputs += ["-i", p]

    def dt(k, font, size, color, x, y):
        return (f"drawtext=fontfile={font}:textfile={os.path.join(WORK, f'og_{k}.txt')}:fontsize={size}:"
                f"fontcolor={color}:x={x}:y={y}")
    f = ["[1:v]scale=-1:120[logo]"]
    for i in range(3):
        f.append(f"[{i + 2}:v]scale=176:313,pad=178:315:1:1:color=0x34444f[p{i}]")
    chain = ("[0:v][logo]overlay=56:48,"
             "drawbox=x=64:y=196:w=96:h=6:color=0xEF5350:t=fill,"
             + ",".join([dt("t1", FONT_BOLD, 54, "0xf1f5f8", 64, 226), dt("t2", FONT_BOLD, 54, "0xffb3ae", 64, 292),
                         dt("t3", FONT_REG, 26, "0xc2ced6", 64, 384), dt("t4", FONT_REG, 26, "0xc2ced6", 64, 420),
                         dt("t5", FONT_MONO, 20, "0x8fa1ad", 64, 540)]) + "[base]")
    f.append(chain)
    f.append("[base][p0]overlay=640:180[a];[a][p1]overlay=824:140[b];[b][p2]overlay=1008:180,"
             "drawbox=x=823:y=139:w=180:h=317:color=0xEF5350:t=2[out]")
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(f), "-map", "[out]", "-frames:v", "1",
         os.path.join(ROOT, "og.png")])


def card(n, c, ep, rep):
    p0, p1 = c["pieces"][0]["start"], c["pieces"][-1]["end"]
    ep_no = ep["title"].rsplit(" ", 1)[-1]
    src_url = f"{ep['url']}#t={p0:.1f},{p1:.1f}"
    x_url = "https://x.com/intent/post?text=" + urllib.parse.quote(c["caption"])
    transcript = srt_text(os.path.join(ROOT, "subtitles", f"{c['id']}.srt"))
    tag_key = c["tag"].lower().replace(" ", "-")
    return f"""
      <article class="card" data-tag="{tag_key}" id="clip-{n:02d}">
        <div class="player">
          <video src="clips/{c['id']}.mp4" poster="assets/posters/{c['id']}.webp" controls playsinline preload="none"
                 aria-label="Clip {n:02d}: {e(c['hook'].replace(chr(10), ' '))}"></video>
        </div>
        <div class="card-head"><span class="num">{n:02d}</span><span class="caps">{e(c['tag'])}</span><span class="len">{mmss(rep['duration'])}</span></div>
        <div class="card-body">
          <h3>{e(c['hook'].replace(chr(10), ' '))}</h3>
          <p class="speaker"><b>{e(c['speaker'])}</b><br>{e(c['role'])}</p>
          <p class="point">{e(c['point'])}</p>
          <div class="source">
            <span>{e(ep['title'])}</span>
            <span class="mono">EP{ep_no} {mmss(p0)} to {mmss(p1)}</span>
            <a href="{e(src_url)}" target="_blank" rel="noopener">Play in source episode</a>
          </div>
          <div class="post">
            <div class="post-top"><span class="caps">Post caption</span><span class="mono">{len(c['caption'])}/280</span></div>
            <p>{e(c['caption'])}</p>
            <div class="row">
              <button type="button" class="btn btn-ghost btn-sm" data-copy="{e(c['caption'])}">{ICON_COPY}Copy</button>
              <a class="btn btn-ghost btn-sm" href="{e(x_url)}" target="_blank" rel="noopener">Post on X</a>
            </div>
          </div>
          <div class="card-foot">
            <a class="btn btn-primary btn-sm" href="clips/{c['id']}.mp4" download>{ICON_DOWNLOAD}MP4 <span class="mono">{rep['size_mb']:.0f} MB</span></a>
            <a class="btn btn-ghost btn-sm" href="subtitles/{c['id']}.srt" download>{ICON_DOWNLOAD}SRT</a>
          </div>
        </div>
        <details class="transcript"><summary>Transcript</summary><p>{e(transcript)}</p></details>
      </article>"""


def main():
    cfg = json.load(open(os.path.join(ROOT, "clips.json")))
    report = json.load(open(os.path.join(ROOT, "verification", "report.json")))
    clips, eps, reps = cfg["clips"], cfg["episodes"], report["clips"]
    total = sum(reps[c["id"]]["duration"] for c in clips)
    n_checks = sum(len(reps[c["id"]]["checks"]) for c in clips)
    n_pass = sum(sum(1 for v in reps[c["id"]]["checks"].values() if v) for c in clips)
    lufs = [reps[c["id"]]["lufs"] for c in clips]
    face_in = sum(reps[c["id"]]["face_in_crop"] for c in clips)
    face_all = sum(reps[c["id"]]["face_samples"] for c in clips)
    tags = []
    for c in clips:
        if c["tag"] not in tags:
            tags.append(c["tag"])

    make_posters(clips)
    make_og(clips, total)

    cards = "".join(card(n, c, eps[c["episode"]], reps[c["id"]]) for n, c in enumerate(clips, 1))
    filters = '<button type="button" data-filter="all" aria-pressed="true">All 6</button>' + "".join(
        f'<button type="button" data-filter="{t.lower().replace(" ", "-")}" aria-pressed="false">{e(t)} '
        f'<span class="mono">{sum(1 for c in clips if c["tag"] == t)}</span></button>' for t in tags)
    source_rows = "".join(
        f"<tr><td class=\"mono\">{n:02d}</td><td><a href=\"#clip-{n:02d}\">{e(c['hook'].replace(chr(10), ' '))}</a></td>"
        f"<td>{e(eps[c['episode']]['title'])}<br><span class=\"mono\" style=\"color:var(--outline)\">{e(eps[c['episode']]['date'])}</span></td>"
        f"<td><a class=\"mono\" href=\"{e(eps[c['episode']]['url'])}#t={c['pieces'][0]['start']:.1f},{c['pieces'][-1]['end']:.1f}\" target=\"_blank\" rel=\"noopener\">"
        f"{mmss(c['pieces'][0]['start'])} to {mmss(c['pieces'][-1]['end'])}</a></td>"
        f"<td>{e(c['speaker'])}<br><span style=\"color:var(--outline)\">{e(c['role'])}</span></td>"
        f"<td>{e(c['caption'])}</td></tr>"
        for n, c in enumerate(clips, 1))
    check_rows = "".join(
        f"<tr><td class=\"mono\">{n:02d}</td><td>{e(c['hook'].replace(chr(10), ' '))}</td>"
        f"<td class=\"mono\">{r['width']}x{r['height']} {r['fps']:.0f} fps</td><td class=\"mono\">{r['duration']:.1f} s</td>"
        f"<td class=\"mono\">{r['lufs']:.1f} LUFS</td><td class=\"mono\">{r['true_peak']:.1f} dBTP</td>"
        f"<td class=\"mono\">{r['cues']} cues</td><td class=\"mono\">{r['face_in_crop']}/{r['face_samples']}</td>"
        f"<td><span class=\"status{'' if all(r['checks'].values()) else ' fail'}\">"
        f"{sum(r['checks'].values())}/{len(r['checks'])} PASS</span></td></tr>"
        for n, c in enumerate(clips, 1) for r in [reps[c["id"]]])
    stack = "".join(f'<img src="assets/posters/{c["id"]}.webp" alt="" width="540" height="960">'
                    for c in [clips[0], clips[3], clips[4]])
    og = f"{SITE_URL}/og.png" if SITE_URL else "og.png"
    checks_list = ", ".join(k.lower() for k in next(iter(reps.values()))["checks"])
    title = "Redbelly Insights Clip Pack"
    desc = "Six captioned vertical clips from Redbelly Insights on Redbelly technology, Project Acacia and Tokeniser."

    page = f"""<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{og}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0c1317">
<link rel="icon" href="assets/brand/icon.png">
<link rel="preload" href="assets/fonts/BeVietnamPro-Bold.ttf" as="font" type="font/ttf" crossorigin>
<link rel="stylesheet" href="assets/site.css">
<script>try{{if(localStorage.getItem('theme')==='light')document.documentElement.setAttribute('data-theme','light')}}catch(e){{}}</script>
</head>
<body>
<a class="sr-only" href="#clips">Skip to clips</a>
<header class="site-header">
  <div class="wrap">
    <a class="brand-link" href="#top" aria-label="Redbelly DAO, clip pack home">
      <img class="logo-dark" src="assets/brand/dao-logo-on-dark.png" alt="Redbelly DAO" width="62" height="44">
      <img class="logo-light" src="assets/brand/dao-logo-on-light.png" alt="Redbelly DAO" width="62" height="44">
      <span>Insights clip pack</span>
    </a>
    <nav class="nav" aria-label="Sections">
      <a href="#clips">Clips</a><a href="#sources">Sources</a><a href="#checks">Checks</a><a href="#method">Method</a>
    </nav>
    <button type="button" class="btn btn-ghost btn-sm theme-toggle" aria-pressed="false">{ICON_THEME}<span>Light theme</span></button>
  </div>
</header>

<main id="top">
  <div class="band">
    <div class="wrap hero">
      <div>
        <div class="caps">Redbelly Insights &middot; Podcast clip pack</div>
        <h1>Six clips from Redbelly Insights. <em>One clear point each.</em></h1>
        <p class="lede">Cut from the latest official episodes for people who will not sit through a full interview.
          Every clip is one continuous passage about Redbelly technology, Project Acacia or Tokeniser, with burned-in
          captions, the speaker's name and role, and a post caption ready for X, YouTube Shorts and Instagram.</p>
        <div class="cta">
          <a class="btn btn-primary" href="#clips">{ICON_PLAY}Watch the clips</a>
          <a class="btn btn-ghost" href="#sources">Sources and captions</a>
        </div>
        <div class="stats">
          <div class="stat"><b>6</b><span>vertical clips</span></div>
          <div class="stat"><b>{mmss(total)}</b><span>total runtime</span></div>
          <div class="stat"><b>1080x1920</b><span>9:16, 30 fps, MP4</span></div>
          <div class="stat"><b>{n_pass}/{n_checks}</b><span>automated checks passed</span></div>
        </div>
      </div>
      <div class="stack" aria-hidden="true">{stack}</div>
    </div>
  </div>

  <section id="clips">
    <div class="wrap">
      <div class="section-head">
        <div>
          <div class="caps">The clips</div>
          <h2>Watch, copy the caption, download</h2>
          <p>Each card has the clip, the one point it makes, the exact source range, a post caption with its X character
            count, and the MP4 and SRT files. Captions are burned in; the SRT is there for platforms that take uploads.</p>
        </div>
        <div class="filters" role="group" aria-label="Filter by topic">{filters}</div>
      </div>
      <div class="grid">{cards}
      </div>
    </div>
  </section>

  <section id="sources">
    <div class="wrap">
      <div class="section-head">
        <div>
          <div class="caps">Deliverable 2</div>
          <h2>Source episode, timestamp and post caption</h2>
          <p>Every timestamp links to the official episode file at that range, so each quote can be checked against the
            original in one click. The same list is in <a href="CLIP_LIST.md">CLIP_LIST.md</a>.</p>
        </div>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>#</th><th>Clip</th><th>Episode</th><th>Source range</th><th>Speaker</th><th>Post caption</th></tr></thead>
          <tbody>{source_rows}</tbody>
        </table>
      </div>
    </div>
  </section>

  <section id="checks">
    <div class="wrap">
      <div class="section-head">
        <div>
          <div class="caps">Verification</div>
          <h2>Measured from the files</h2>
          <p>These numbers come from <span class="mono">tools/verify.py</span>, which reads every MP4 and SRT and fails
            on any problem. Full results, including the subtitle cross-check against three transcripts, are in
            <a href="verification/REPORT.md">verification/REPORT.md</a>.</p>
        </div>
      </div>
      <div class="summary">
        <div class="panel"><span class="caps">Checks passed</span><b>{n_pass}/{n_checks}</b>
          <p>Per clip: {e(checks_list)}.</p></div>
        <div class="panel"><span class="caps">Even audio</span><b>{sum(lufs) / len(lufs):.1f} LUFS</b>
          <p>Average integrated loudness. The six clips are within {report['loudness_spread_lu']:.1f} LU of each other.</p></div>
        <div class="panel"><span class="caps">Speaker in frame</span><b>{face_in}/{face_all}</b>
          <p>Face samples, taken every 0.2 s of source video, that sit inside the crop used for that shot.</p></div>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>#</th><th>Clip</th><th>Video</th><th>Length</th><th>Loudness</th><th>True peak</th><th>Captions</th><th>Face in frame</th><th>Result</th></tr></thead>
          <tbody>{check_rows}</tbody>
        </table>
      </div>
      <p class="note">Last verified <span class="mono">{report['date']}</span>.</p>
    </div>
  </section>

  <section id="method">
    <div class="wrap">
      <div class="section-head">
        <div>
          <div class="caps">Method</div>
          <h2>How the pack was made</h2>
          <p>Every step is a script in <span class="mono">tools/</span>, driven by <span class="mono">clips.json</span>,
            so the whole pack can be rebuilt and checked from the official episodes.</p>
        </div>
      </div>
      <div class="steps">
        <div class="step"><span class="mono">01 SOURCES</span><h3>Official episodes only</h3>
          <p>The episode files linked from redbelly.network/ama. Episodes 26 to 29 were transcribed in full. No music,
            stock footage or third party material is added.</p></div>
        <div class="step"><span class="mono">02 SELECTION</span><h3>One passage, one point</h3>
          <p>Each clip is a single uninterrupted passage about Redbelly technology, Project Acacia or Tokeniser. No
            internal cuts, so no quote is joined to words said elsewhere. No two clips make the same point.</p></div>
        <div class="step"><span class="mono">03 FRAMING AND CAPTIONS</span><h3>Speaker in shot, words checked</h3>
          <p>Faces are tracked every 0.2 s to set a 9:16 crop per camera shot. Caption text is proof-read against three
            separate Whisper transcripts, and names and terms are fixed by hand.</p></div>
        <div class="step"><span class="mono">04 AUDIO AND CHECKS</span><h3>Even loudness, measured output</h3>
          <p>Two-pass EBU R128 normalisation to -14 LUFS. The verify step measures specs, length, caption coverage,
            spelling, framing, loudness and a personal-credit scan for every file.</p></div>
      </div>
<pre><code>export WORK=$PWD/work
tools/fetch.sh                                   # official episodes, audio, face model
python3 tools/transcribe.py small.en $WORK/aud/ep26.wav $WORK/tx/ep26.json
python3 tools/transcribe.py small.en $WORK/aud/ep28.wav $WORK/tx/ep28.json
python3 tools/build.py                           # clips/*.mp4 and subtitles/*.srt
python3 tools/verify.py                          # verification/REPORT.md and report.json
python3 tools/clip_list.py                       # CLIP_LIST.md
python3 tools/site.py                            # this page, posters and og.png</code></pre>
    </div>
  </section>
</main>

<footer class="site-footer">
  <div class="wrap">
    <img class="logo-dark" src="assets/brand/dao-logo-on-dark.png" alt="Redbelly DAO" width="62" height="44">
    <img class="logo-light" src="assets/brand/dao-logo-on-light.png" alt="Redbelly DAO" width="62" height="44">
    <p>All footage and audio comes from official Redbelly Insights episodes at
      <a href="https://redbelly.network/ama" target="_blank" rel="noopener">redbelly.network/ama</a>. No music or third
      party material is added. Last verified <span class="mono">{report['date']}</span>.</p>
    <nav aria-label="Files"><a href="README.md">README</a><a href="CLIP_LIST.md">Clip list</a>
      <a href="verification/REPORT.md">Verification report</a><a href="clips.json">clips.json</a></nav>
  </div>
</footer>
<div class="toast" role="status" aria-live="polite"></div>
<script src="assets/site.js"></script>
</body>
</html>
"""
    open(os.path.join(ROOT, "index.html"), "w").write(page)


if __name__ == "__main__":
    main()
