# Launch video

`demo.mp4` is the 76-second launch film for Free-Research-Crew v0.5 (1920 x 1080, 30 fps,
H.264, silent, English on-screen text with Chinese subtitles). `poster.png` is its poster frame
(t = 4.5 s). The film is a [HyperFrames](https://hyperframes.heygen.com/) composition: HTML
scenes seeked frame by frame, so every render is identical.

| Scene | Time | File |
|---|---|---|
| Hook | 0–5.5 s | [`compositions/hook.html`](compositions/hook.html) |
| The crew and the workspace files | 5.5–16 s | [`compositions/crew.html`](compositions/crew.html) |
| The four gates; run record to macro | 16–32 s | [`compositions/flow.html`](compositions/flow.html) |
| The Reviewer's catches | 31.5–53 s | [`compositions/reviewer.html`](compositions/reviewer.html) |
| Six papers and totals | 53–67 s | [`compositions/proof.html`](compositions/proof.html) |
| Install and repo | 66.5–76 s | [`compositions/close.html`](compositions/close.html) |

[`index.html`](index.html) mounts the scenes; [`assets/crew.css`](assets/crew.css) holds the
palette from [`assets/poster/build_poster.py`](../../../assets/poster/build_poster.py);
[`SPEC.md`](SPEC.md) is the design brief and [`REVIEW.md`](REVIEW.md) the review notes.

Every number and quotation on screen comes from the repo: [`release-v0.5.md`](../release-v0.5.md),
[`gallery/README.md`](../../../gallery/README.md), the review files under
`gallery/<paper>/reviews/` and `gallery/ss-lalonde-observational/runs/main-aipw/` and `paper/`.
If a number changes there, change it in the scene file and re-render.

## Re-render

Needs Node.js 22+, FFmpeg and network access (the CLI fetches Chrome on first use, and GSAP and
the Latin fonts at render time).

```bash
cd docs/launch/video
npx --yes hyperframes@0.9.71 check                       # lint, layout and contrast audit
npx --yes hyperframes@0.9.71 preview                     # optional: live preview to edit in
npx --yes hyperframes@0.9.71 render --crf 20 --output demo.mp4
ffmpeg -y -ss 4.5 -i demo.mp4 -frames:v 1 poster.png
```

A render takes about a minute on a laptop and gives a file of about 9–10 MB. Snapshots and
render caches go to `.hyperframes/`, which is not committed.

## Chinese font

The subtitles use a subset of Noto Sans SC (SIL Open Font License) holding only the characters
in the scenes, `assets/fonts/crew-sc.woff`. After changing any Chinese text, rebuild it from a
local copy of `NotoSansSC.ttf` (needs `pip install fonttools`):

```bash
cd docs/launch/video
python3 -c "import glob; s=set(''.join(open(f).read() for f in glob.glob('compositions/*.html'))); print(''.join(sorted(c for c in s if ord(c) > 0x2000)) + '0123456789 .\$/:-()abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')" > /tmp/zh.txt
pyftsubset /path/to/NotoSansSC.ttf --text-file=/tmp/zh.txt --flavor=woff \
  --layout-features='*' --output-file=assets/fonts/crew-sc.woff
```

## Sound

The film is silent: no music source was available when it was made. To add a bed, place an
`<audio id="bed" data-start="0" data-volume="0.5" src="assets/bed.mp3">` in `index.html`
and re-render.
