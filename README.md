# Redbelly Insights: podcast clip pack

Six captioned vertical clips (9:16, 1080x1920, 30 fps, H.264/AAC MP4), 36 to 53 seconds each. They come from the latest official **Redbelly Insights** episodes and are ready to post on X, YouTube Shorts, Instagram Reels and TikTok. Each clip is one continuous passage from the episode, with no cuts inside it.

| # | Clip | Speaker | The point | Tag |
|---|---|---|---|---|
| 1 | [`01_mev_attacks_get_caught.mp4`](clips/01_mev_attacks_get_caught.mp4) | Vincent Gramoli, Founder & Chief Science Officer, Redbelly Network | Sandwich and front-running (MEV) attacks are detected, and repeat offenders can be slashed | Redbelly tech |
| 2 | [`02_no_forks_no_double_spend.mp4`](clips/02_no_forks_no_double_spend.mp4) | Vincent Gramoli | No forks and no double-spend risk is why Redbelly suits high-value assets | Redbelly tech |
| 3 | [`03_what_pdti_means.mp4`](clips/03_what_pdti_means.mp4) | Vincent Gramoli | What being public digital token infrastructure (PDTI) means | Redbelly tech |
| 4 | [`04_acacia_investors_trade_directly.mp4`](clips/04_acacia_investors_trade_directly.mp4) | Matt Mills, Chief Customer Officer, Tokeniser | In Project Acacia, unit holders swapped units with each other, verifiable on Redbelly | Project Acacia |
| 5 | [`05_holdings_in_any_app.mp4`](clips/05_holdings_in_any_app.mp4) | Matt Mills | Units issued with Tokeniser show up in Open Markets straight from the block explorer | Tokeniser |
| 6 | [`06_acacia_regulatory_umbrella.mp4`](clips/06_acacia_regulatory_umbrella.mp4) | Alan Burt, Executive Chairman, Redbelly Network | The RBA's Project Acacia gave boards and regulators a regulatory umbrella to tokenise | Project Acacia |

## Deliverables

1. **Six vertical clips with subtitles.** They are in [`clips/`](clips/). Subtitles are burned in, and each clip also has a sidecar `.srt` file in [`subtitles/`](subtitles/).
2. **Source list with post captions.** [`CLIP_LIST.md`](CLIP_LIST.md) gives the source episode, exact source timestamps, speaker, topic, the one point each clip makes, and a suggested one-line post caption.

Supporting material:

- [`verification/REPORT.md`](verification/REPORT.md) is the automated check of every clip against the brief: specs, duration, loudness, subtitle coverage, spelling of names and terms, speaker-in-frame coverage, a personal-credit scan, and the subtitle text compared with three independent transcripts.
- [`verification/contact_sheets/`](verification/contact_sheets/) has one frame every 4 seconds of each clip, so framing and subtitles can be reviewed without playing the videos.
- [`verification/transcripts/`](verification/transcripts/) has full machine transcripts of Episodes 26 to 29, used to choose the moments.
- [`clips.json`](clips.json) is the single source of truth: episodes, cut points, proof-read subtitle text, hooks, tags, names, roles and captions.

## Look of the clips

- **Full-frame speaker:** the speaker fills the whole 9:16 frame. Faces are tracked every 0.2 s, and the crop is set per camera shot so the speaker stays in frame. In wide two-shots the crop is locked onto the guest, as recorded in `clips.json`.
- **Opening title card (0–3 s):** the hook in large type over a dimmed picture, then the speaker's name and role.
- **After the card:** a topic pill at the top (REDBELLY TECH, PROJECT ACACIA or TOKENISER), the speaker's name and role, the source episode, and a thin progress bar.
- **Captions:** short phrases of up to five words that pop in over the lower third. Redbelly terms and figures are in amber. The one host line (clip 2) is in grey italics and marked `HOST:` in the `.srt`.
- **No added music or footage.** The audio is the episode audio, loudness-normalised (two-pass EBU R128) to -14 LUFS integrated and -1.5 dBTP, so all six play at the same level.

## How the moments were chosen

- Episodes 26, 27, 28 and 29 (the four most recent on redbelly.network/ama) were transcribed in full. The transcripts are in `verification/transcripts/`.
- Only passages about Redbelly technology, Project Acacia or Tokeniser were considered. Each clip had to make one point that holds up for someone who has never heard of Redbelly, and no two clips could make the same point.
- Every clip is a single uninterrupted passage, so nothing a speaker said is joined to something said elsewhere.
- Names and roles come from official sources: [redbelly.network/about-us](https://redbelly.network/about-us) for Vincent Gramoli and Alan Burt, and [tokeniser.com/about](https://tokeniser.com/about) for Matt Mills.

## Subtitle accuracy

The subtitle text was proof-read against three separate Whisper transcriptions (small.en, medium.en and large-v3). Names and terms were corrected by hand: Redbelly, Redbelly Network, Tokeniser, Project Acacia, PDTI, MEV, RBA, Open Markets.

The subtitles are close to verbatim. Hesitations ("uh", "um"), stutters and host back-channel words are left out. Where the models disagreed, the reading shared by the majority, or by large-v3, was used; for example, "part of the stake that you have in the system will be slashed".

## Reproducing the pack

Requirements: `ffmpeg` (with libass), Python 3.10+, `pip install faster-whisper opencv-python-headless numpy`, and the Inter font installed.

```bash
export WORK=$PWD/work                 # scratch space for sources and transcripts (not committed)
tools/fetch.sh                        # download the episodes from redbelly.network, extract audio, get face model
for ep in ep26 ep28; do               # word-timestamped transcripts
  python3 tools/transcribe.py small.en $WORK/aud/$ep.wav $WORK/tx/$ep.json
done
python3 tools/build.py                # render clips/*.mp4 and subtitles/*.srt
python3 tools/clip_list.py            # write CLIP_LIST.md
python3 tools/verify.py               # write verification/REPORT.md (exit code 1 on any failed check)
```

`python3 tools/build.py <clip_id>` re-renders a single clip.
