---
name: effects
description: Video effects for talking-head reels — /effects <name> applies one look (glass-widgets, documentary, orbit, chart-split, spotlight, checklist, timeline) to the user's clip, or /effects reel builds the "one clip, 7 edits" showcase. Use when the user drops a video and types /effects.
---

# /effects — one command, one edit

Usage the user types:

```
/effects glass-widgets      (+ a video attached or a path)
/effects list
/effects reel               — showcase: one clip → 7 edits, music + UI sounds, no voice
```

All scripts live next to this file — in Claude Code that is `~/.claude/skills/effects/`; when the skill
was uploaded in the Claude app (Settings → Skills) it is wherever this SKILL.md sits in the sandbox, so
`cd` to this file's folder first. Python 3.10+, ffmpeg, `pip install -r requirements.txt`
(add `--break-system-packages` if pip refuses). First run downloads a person-segmentation model
(~170 MB, once, from github.com). In the Claude app the video comes as a chat attachment: make a
1080x1920 proxy first, render, then hand the mp4 back as a file.

## Effects

| name | what it does |
|---|---|
| `glass-widgets` | frosted-glass app widgets (counter, render bar, profile, chart, 4K ring) around the speaker, placed behind the head |
| `documentary` | B&W doc-series grade, pink glow + 3-line title behind the head, lower third, “Подписаться” click |
| `orbit` | mini reels orbit around the speaker, passing behind and in front |
| `chart-split` | top half: bar chart that grows on paper; bottom half: the speaker |
| `spotlight` | dark room, spotlight on the speaker, neon word flickers on behind the head |
| `checklist` | glass card where Claude ticks off five editing steps |
| `timeline` | mini editor window renders live above the speaker |

## How to run it (you, Claude)

1. Find the clip. If it is bigger than ~100 MB or 4K, make a 1080x1920 proxy first:
   `ffmpeg -i in.mp4 -vf scale=1080:1920 -c:v libx264 -crf 18 -an proxy.mp4`.
2. Ask (once) for the name and @handle to show on screen, or read them from `config.json`.
3. **Preview first — the user approves every look:**
   `python3 run.py <effect> <video> --preview 1.0,2.5,5`
   Show the PNGs. Adjust texts in `effects/<effect>.py` (all on-screen copy is at the top of each file) if asked.
4. Full render: `python3 run.py <effect> <video> -o out.mp4`  
   (`--no-voice --music` for a music-only version; `--start 3` to start the effect at 3 s.)
5. Showcase reel: `python3 reel.py <video> -o reel.mp4 [--effects glass-widgets,orbit,…]`.
   Picture is rendered at 1080x1920/30fps; audio is synthesized (no licensed music), loudness −14 LUFS.
6. Before handing over: check a few frames and run `ffmpeg -i out.mp4 -vf blackdetect -f null -`.

Texts are Russian by default; to localise, edit the strings at the top of each effect file and `config.json`.
