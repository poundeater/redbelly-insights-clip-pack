# Redbelly Insights: podcast clip pack

Six captioned vertical clips (9:16, 1080x1920, 30 fps, H.264/AAC MP4), 36 to 53 seconds each. They are cut from the latest official **Redbelly Insights** episodes, ready for the Redbelly and DAO accounts to post on X, YouTube Shorts and Instagram while the show relaunches as Off Paper - Powered by Tokeniser. Each clip is one continuous passage from the episode, with no cuts inside it.

**Review page:** open `index.html`, or deploy the repository root as a static site (see [Deploying the review page](#deploying-the-review-page)). The page has every player, the source range of each clip linked to the official episode, copyable post captions with their X character count, downloads, and the measured verification results.

| # | Clip | Speaker | The point | Topic |
|---|---|---|---|---|
| 1 | [`01_mev_attacks_get_caught.mp4`](clips/01_mev_attacks_get_caught.mp4) | Vincent Gramoli, Founder & Chief Science Officer, Redbelly Network | Sandwich and front-running (MEV) attacks are detected, and repeat offenders can be slashed | Redbelly tech |
| 2 | [`02_no_forks_no_double_spend.mp4`](clips/02_no_forks_no_double_spend.mp4) | Vincent Gramoli | No forks and no double-spend risk is why Redbelly suits high-value assets | Redbelly tech |
| 3 | [`03_what_pdti_means.mp4`](clips/03_what_pdti_means.mp4) | Vincent Gramoli | What being public digital token infrastructure (PDTI) means | Redbelly tech |
| 4 | [`04_acacia_investors_trade_directly.mp4`](clips/04_acacia_investors_trade_directly.mp4) | Matt Mills, Chief Customer Officer, Tokeniser | In Project Acacia, unit holders swapped units with each other, verifiable on Redbelly | Project Acacia |
| 5 | [`05_holdings_in_any_app.mp4`](clips/05_holdings_in_any_app.mp4) | Matt Mills | Units issued with Tokeniser show up in Open Markets straight from the block explorer | Tokeniser |
| 6 | [`06_acacia_regulatory_umbrella.mp4`](clips/06_acacia_regulatory_umbrella.mp4) | Alan Burt, Executive Chairman, Redbelly Network | The RBA's Project Acacia gave boards and regulators a regulatory umbrella to tokenise | Project Acacia |

## Deliverables

1. **Six vertical clips with subtitles.** They are in [`clips/`](clips/). Subtitles are burned in, and each clip also has a sidecar `.srt` file in [`subtitles/`](subtitles/).
2. **Source list with post captions.** [`CLIP_LIST.md`](CLIP_LIST.md) gives the source episode, the exact source timestamps, the speaker, the one point each clip makes, and a suggested one-line post caption. The same list, with one-click links to each source range, is on the review page.

Supporting material:

| Path | What it is |
|---|---|
| [`index.html`](index.html), [`assets/`](assets/), [`og.png`](og.png) | Static review page, its stylesheet and script, brand assets, fonts, poster frames and the 1200x630 link preview image |
| [`verification/REPORT.md`](verification/REPORT.md) | Automated check of every clip: specs, length, loudness, caption coverage, spelling of names and terms, speaker in frame, personal-credit scan, and the subtitle text compared with three independent transcripts |
| [`verification/report.json`](verification/report.json) | The same measurements as JSON. The review page is built from it |
| [`verification/contact_sheets/`](verification/contact_sheets/) | One frame every 4 seconds of each clip, for reviewing framing and captions without playing the videos |
| [`verification/transcripts/`](verification/transcripts/) | Full machine transcripts of Episodes 26 to 29, used to choose the moments |
| [`clips.json`](clips.json) | Single source of truth: episodes, cut points, proof-read subtitle text, hooks, topics, names, roles and captions |

## Brand

Clips and page follow the [Redbelly DAO Task Board brand kit](https://taskboard.redbellydao.network/brand) ("Kinetic Consensus"):

- **Colour:** one accent, brand red `#EF5350`, on slate surfaces (`#0c1317`, `#141f26`, `#1d3140`). Accent text is `#ffb3ae` on dark and `#B3272A` on light. The page ships the kit's dark theme by default and its light theme behind a toggle. The values are the kit's own `tokens.css`, copied to [`assets/brand/tokens.css`](assets/brand/tokens.css).
- **Type:** Be Vietnam Pro for all copy, JetBrains Mono only for machine values (episode numbers, timestamps, sizes, measurements). Both are SIL OFL fonts, in [`assets/fonts/`](assets/fonts/) with the licence.
- **Logo:** the kit's `dao-logo-on-dark.png` and `dao-logo-on-light.png`, never on a plate and never over a busy photograph. In the clips the logo sits only on the solid slate opening sheet.
- **Shape and voice:** 4px and 8px radii, no pill buttons, status shown as a dot plus a monospace label, tonal depth instead of shadows, no em or en dashes and no emoji.

## Look of the clips

- **Opening sheet (first 3.2 s):** a solid slate sheet at the bottom of the frame carries the DAO logo, the source (`REDBELLY INSIGHTS`, `EP28 16:05`), the hook, and the speaker's name and role. The speaker stays visible above it, and the content stays clear of the bottom band where TikTok, Reels and Shorts draw their own controls.
- **After the sheet:** a red topic tag, the speaker's name and role on a translucent slate box, the source episode and timestamp in JetBrains Mono, and a red progress bar along the top.
- **Captions:** short phrases of up to five words in Be Vietnam Pro Bold that pop in over the lower third. Redbelly terms and figures are in brand red. The one host line (clip 2) is in grey italics and marked `HOST:` in the `.srt`.
- **Framing:** the speaker fills the 9:16 frame. Faces are tracked every 0.2 s and the crop is set per camera shot. In wide two-shots the crop is locked onto the guest. Where the episode cuts away to the host mid-sentence (clip 5, 4.6 s), the speaker's last frame is held with a slow push-in while the audio carries on. Both are recorded in `clips.json` and `CLIP_LIST.md`.
- **Audio:** the episode audio only, loudness-normalised with two-pass EBU R128 to -14 LUFS integrated and -1.5 dBTP, so all six clips play at the same level.

## How the moments were chosen

- Episodes 26, 27, 28 and 29 (the four most recent on redbelly.network/ama) were transcribed in full. The transcripts are in `verification/transcripts/`.
- Only passages about Redbelly technology, Project Acacia or Tokeniser were considered. Each clip had to make one point that holds up for someone who has never heard of Redbelly, and no two clips could make the same point.
- Every clip is a single uninterrupted passage, so nothing a speaker said is joined to something said elsewhere.
- Names and roles come from official sources: [redbelly.network/about-us](https://redbelly.network/about-us) for Vincent Gramoli and Alan Burt, and [tokeniser.com/about](https://tokeniser.com/about) for Matt Mills.

## Subtitle accuracy

The subtitle text was proof-read against three separate Whisper transcriptions (small.en, medium.en and large-v3). Names and terms were fixed by hand: Redbelly, Redbelly Network, Tokeniser, Project Acacia, PDTI, MEV, RBA and Open Markets.

The subtitles are close to verbatim. Hesitations ("uh", "um"), stutters and host back-channel words are left out. Where the models disagreed, the reading shared by the majority, or by large-v3, was used. For example: "part of the stake that you have in the system will be slashed".

## Deploying the review page

The repository root is a static site with no build step.

- **Vercel:** import the repository, set Framework Preset to **Other**, leave Build Command and Output Directory empty, and keep Root Directory as `./`.
- **Netlify or Cloudflare Pages:** no build command, publish directory `/`.
- **GitHub Pages:** Settings, Pages, deploy from branch, folder `/ (root)`.

For link previews with an absolute image URL, rebuild the page with the live address: `SITE_URL=https://your-domain python3 tools/site.py`.

## Reproducing the pack

Requirements: `ffmpeg` with libass and libwebp, Python 3.10+, and `pip install faster-whisper opencv-python-headless numpy`. Fonts and brand assets are in `assets/`.

```bash
export WORK=$PWD/work                 # scratch space for sources and transcripts (not committed)
tools/fetch.sh                        # download the episodes from redbelly.network, extract audio, get face model
for ep in ep26 ep28; do               # word-timestamped transcripts
  python3 tools/transcribe.py small.en $WORK/aud/$ep.wav $WORK/tx/$ep.json
done
python3 tools/build.py                # render clips/*.mp4 and subtitles/*.srt
python3 tools/verify.py               # verification/REPORT.md and report.json (exit code 1 on any failed check)
python3 tools/clip_list.py            # CLIP_LIST.md
python3 tools/site.py                 # index.html, assets/posters/ and og.png
```

`python3 tools/build.py <clip_id>` re-renders a single clip.
