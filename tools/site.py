"""Write index.html: a static review page for the clip pack (players, sources, captions, downloads).

The page has no build step, so the repository root can be deployed as-is (Vercel, Netlify, GitHub Pages).
"""
import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def mmss(t):
    return f"{int(t // 60)}:{int(t % 60):02d}"


def card(n, c, ep):
    p = c["pieces"][0]
    dur = sum(x["end"] - x["start"] for x in c["pieces"])
    e = html.escape
    return f"""
    <article class="clip">
      <div class="phone"><video src="clips/{c['id']}.mp4#t=1.5" controls playsinline preload="metadata"></video></div>
      <div class="meta">
        <div class="row"><span class="num">{n:02d}</span><span class="tag">{e(c['tag'])}</span><span class="len">{dur:.0f}s</span></div>
        <h2>{e(c['hook'].replace(chr(10), ' '))}</h2>
        <p class="who"><strong>{e(c['speaker'])}</strong><br>{e(c['role'])}</p>
        <p class="point">{e(c['point'])}</p>
        <dl>
          <dt>Source</dt><dd><a href="{e(ep['url'])}" target="_blank" rel="noopener">{e(ep['title'])}</a> &middot; {e(ep['date'])}</dd>
          <dt>Timestamp</dt><dd>{mmss(p['start'])} &ndash; {mmss(c['pieces'][-1]['end'])}</dd>
        </dl>
        <div class="caption">
          <span class="label">Post caption</span>
          <p>{e(c['caption'])}</p>
          <button type="button" data-copy="{e(c['caption'])}">Copy caption</button>
        </div>
        <p class="dl"><a href="clips/{c['id']}.mp4" download>Download MP4</a><a href="subtitles/{c['id']}.srt" download>Download SRT</a></p>
      </div>
    </article>"""


def main():
    cfg = json.load(open(os.path.join(ROOT, "clips.json")))
    cards = "".join(card(n, c, cfg["episodes"][c["episode"]]) for n, c in enumerate(cfg["clips"], 1))
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Redbelly Insights Clip Pack</title>
<meta name="description" content="Six captioned vertical clips from Redbelly Insights on Redbelly technology, Project Acacia and Tokeniser.">
<style>
  :root {{ --bg:#f6f4f1; --card:#ffffff; --ink:#16161a; --muted:#5d5d66; --line:#e4e0da; --amber:#d9661f; --chip:#fff1e6; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg:#0f0f12; --card:#18181d; --ink:#f2f2f4; --muted:#a3a3ad; --line:#2a2a31; --amber:#ff8a3d; --chip:#2b1d14; }}
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink); font:16px/1.55 Inter, system-ui, -apple-system, "Segoe UI", sans-serif; }}
  header, main, footer {{ max-width:1120px; margin:0 auto; padding:0 16px; }}
  header {{ padding-top:48px; padding-bottom:24px; }}
  .kicker {{ color:var(--amber); font-weight:700; letter-spacing:.12em; font-size:13px; text-transform:uppercase; }}
  h1 {{ font-size:clamp(28px,5vw,44px); line-height:1.1; margin:8px 0 12px; }}
  header p {{ color:var(--muted); max-width:720px; margin:0; }}
  .facts {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:20px; padding:0; list-style:none; }}
  .facts li {{ background:var(--card); border:1px solid var(--line); border-radius:999px; padding:6px 12px; font-size:14px; }}
  .clip {{ display:grid; grid-template-columns:minmax(0,300px) 1fr; gap:28px; background:var(--card); border:1px solid var(--line);
          border-radius:20px; padding:20px; margin:20px 0; }}
  .phone {{ aspect-ratio:9/16; border-radius:16px; overflow:hidden; background:#000; }}
  .phone video {{ width:100%; height:100%; display:block; object-fit:cover; background:#000; }}
  .row {{ display:flex; align-items:center; gap:10px; font-size:13px; }}
  .num {{ font-weight:800; color:var(--amber); }}
  .tag {{ background:var(--chip); color:var(--amber); font-weight:700; text-transform:uppercase; letter-spacing:.08em; padding:3px 8px; border-radius:6px; }}
  .len {{ color:var(--muted); margin-left:auto; }}
  h2 {{ font-size:24px; line-height:1.25; margin:12px 0 8px; }}
  .who {{ margin:0 0 12px; color:var(--muted); }} .who strong {{ color:var(--ink); }}
  .point {{ margin:0 0 16px; }}
  dl {{ display:grid; grid-template-columns:auto 1fr; gap:4px 16px; margin:0 0 16px; font-size:14px; }}
  dt {{ color:var(--muted); }} dd {{ margin:0; overflow-wrap:anywhere; }}
  a {{ color:var(--amber); }}
  .caption {{ border-left:3px solid var(--amber); padding:4px 0 4px 14px; margin-bottom:16px; }}
  .caption .label {{ font-size:12px; text-transform:uppercase; letter-spacing:.1em; color:var(--muted); }}
  .caption p {{ margin:4px 0 10px; }}
  button {{ font:inherit; font-size:14px; padding:6px 12px; border-radius:8px; border:1px solid var(--line); background:var(--bg); color:var(--ink); cursor:pointer; }}
  .dl {{ display:flex; flex-wrap:wrap; gap:16px; margin:0; font-size:14px; font-weight:600; }}
  footer {{ color:var(--muted); font-size:14px; padding-top:12px; padding-bottom:48px; }}
  @media (max-width:720px) {{ .clip {{ grid-template-columns:1fr; }} .phone {{ max-width:320px; width:100%; margin:0 auto; }} }}
</style>
</head>
<body>
<header>
  <div class="kicker">Redbelly Insights &middot; Clip pack</div>
  <h1>Six moments on Redbelly technology, Project Acacia and Tokeniser</h1>
  <p>Captioned vertical clips cut from the latest official Redbelly Insights episodes, ready for X, YouTube Shorts and Instagram. Each clip is one continuous passage from the episode.</p>
  <ul class="facts"><li>9:16 &middot; 1080&times;1920</li><li>30 fps &middot; H.264 + AAC</li><li>Burned-in captions + SRT</li><li>&minus;14 LUFS</li></ul>
</header>
<main>{cards}
</main>
<footer>Source list with timestamps: <a href="CLIP_LIST.md">CLIP_LIST.md</a> &middot; Checks: <a href="verification/REPORT.md">verification/REPORT.md</a></footer>
<script>
  document.querySelectorAll('button[data-copy]').forEach(function (b) {{
    b.addEventListener('click', function () {{
      var done = function () {{ b.textContent = 'Copied'; setTimeout(function () {{ b.textContent = 'Copy caption'; }}, 1500); }};
      try {{ navigator.clipboard.writeText(b.dataset.copy).then(done, function () {{}}); }} catch (e) {{}}
    }});
  }});
</script>
</body>
</html>
"""
    open(os.path.join(ROOT, "index.html"), "w").write(page)


if __name__ == "__main__":
    main()
