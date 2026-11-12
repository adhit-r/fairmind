# FairMind documentation site

How to use FairMind, page by page. Every app page has a narrated recording, captions and a click-through demo of the
same steps, captured from the read-only demo organisation that **Try the demo** on the sign-in page opens. Built with
[Fumadocs](https://fumadocs.dev), served at `docs.fairmind.xyz`.

```bash
npm run dev          # http://localhost:3333/docs
npm run build        # runs the coverage gate first
```

`build` first runs `scripts/coverage.ts`, which fails when an app route in `outline.json` has no doc page showing
`<PageAnatomy route="…" />`, when a page shows a recording no tour makes, or when a tour is shown on no page.

## Where things are

| Path | What it is |
|---|---|
| `content/docs/` | The pages (MDX). `app/` has one page per app page, grouped as the app's menu is |
| `outline.json` | What each app page holds (headings, sections, controls, tables, empty states, API calls), captured by `npm run outline` |
| `tours/*.ts` | One tour per recording: the steps a person takes, each with one or two spoken sentences |
| `capture/` | `outline.ts` captures the outline; `run.ts` records tours; `voice.ts` narrates (Kokoro); `tour.ts` is the tour format |
| `src/components/` | `Access`, `PageAnatomy`, `Watch`, `TryIt` and the click-through |
| `public/media/<page>/` | A tour's `video.mp4`, `captions.vtt`, step images and `demo.json` |

## A page

```mdx
<Access where="Inventory › AI systems" address="/systems" change="owner or admin" />

<Tabs items={['Watch', 'Try it']}>
  <Tab value="Watch"><Watch page="app/inventory/systems" /></Tab>
  <Tab value="Try it"><TryIt page="app/inventory/systems" /></Tab>
</Tabs>

## What it is for … ## How to use it … ## What's on the page

<PageAnatomy route="systems" />
```

## Recording

You need Google Chrome (or `FAIRMIND_BROWSER_EXECUTABLE`), ffmpeg, and the Kokoro voice: a Python with `kokoro-onnx`
and `soundfile` at `~/.cache/hyperframes/tts/venv` (or `HYPERFRAMES_PYTHON`). `hyperframes tts` fetches the model on
first use.

```bash
uv venv ~/.cache/hyperframes/tts/venv --python 3.12
VIRTUAL_ENV=~/.cache/hyperframes/tts/venv uv pip install kokoro-onnx soundfile
```

Both commands below sign in through **Try the demo** on `FAIRMIND_APP_URL` (the live app by default). The demo is
read-only, so tours open forms and drawers but never submit.

```bash
npm run outline                    # about a minute: every page in the menu, plus one system file
npm run capture                    # every tour (narration is cached in .capture/voice)
npm run capture -- systems runs    # only tours whose page contains one of these words
```

A step whose control no longer resolves fails the run and names the tour and step: that is how an app change finds
the docs it made stale. Tours address controls by accessible role and name, as a person would.
