/**
 * Records the documentation's tours: for each, a narrated video with captions and a click-through demo.
 *
 *   npm run capture                        # every tour
 *   npm run capture -- systems runs        # only tours whose page path contains one of these words
 *
 * Each tour runs in the FairMind demo (FAIRMIND_APP_URL, the live app by default), signed in the way a visitor is:
 * "Try the demo" on the sign-in page. The demo is read-only, so nothing a tour does changes it. Runs in the system
 * Chrome (never downloaded) and writes public/media/<page>/: video.mp4, captions.vtt, demo.json and the step images.
 */
import { spawnSync } from 'node:child_process'
import { existsSync, mkdirSync, mkdtempSync, readdirSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'
import { chromium, type Browser, type BrowserContext, type CDPSession, type Locator, type Page } from 'playwright-core'
import type { Step, Target, Tour } from './tour'
import { voiceLine } from './voice'

const DOCS = fileURLToPath(new URL('..', import.meta.url))
const MEDIA = join(DOCS, 'public/media')
export const APP = (process.env['FAIRMIND_APP_URL'] ?? 'https://app.fairmind.xyz').replace(/\/+$/, '')
export const VIEW = { width: 1280, height: 800 }
const FPS = 30
export const CHROME = [
  process.env['FAIRMIND_BROWSER_EXECUTABLE'],
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/usr/bin/google-chrome', '/usr/bin/chromium',
].find(p => p && existsSync(p))
const sleep = (ms: number) => new Promise(r => setTimeout(r, ms))

/** A browser context signed in to the demo, as a visitor is: the sign-in page's "Try the demo". */
export async function demoContext(browser: Browser): Promise<BrowserContext> {
  const context = await browser.newContext({ viewport: VIEW, deviceScaleFactor: 1.5, locale: 'en-GB' })
  const page = await context.newPage()
  await page.goto(`${APP}/login`)
  await page.getByRole('button', { name: 'Try the demo' }).click({ timeout: 15_000 })
  await page.waitForURL(/\/dashboard/, { timeout: 30_000 })
  await page.close()
  return context
}

// A visible pointer for the recording: the screencast has no cursor of its own. Drawn with the DOM, never in the
// click-through screenshots (hidden while they are taken). Plain JavaScript text: a function passed from here would be
// rewritten by the TypeScript loader with helpers the page does not have.
const CURSOR_SCRIPT = `(() => {
  const add = () => {
    if (document.getElementById('docs-cursor')) return
    const dot = document.createElement('div')
    dot.id = 'docs-cursor'
    Object.assign(dot.style, { position: 'fixed', left: '0', top: '0', width: '20px', height: '20px', margin: '-10px 0 0 -10px',
      borderRadius: '50%', background: 'rgba(21,23,26,.85)', border: '3px solid #fff', boxShadow: '0 2px 10px rgba(0,0,0,.35)',
      zIndex: '2147483647', pointerEvents: 'none', transform: 'translate(640px, 420px)', transition: 'transform .6s cubic-bezier(.4,0,.2,1)' })
    const ring = document.createElement('div')
    ring.id = 'docs-ring'
    Object.assign(ring.style, { position: 'fixed', left: '0', top: '0', width: '44px', height: '44px', margin: '-22px 0 0 -22px',
      borderRadius: '50%', border: '3px solid #ff6b35', zIndex: '2147483646', pointerEvents: 'none', opacity: '0' })
    document.documentElement.append(ring, dot)
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', add)
  else add()
})()`

interface Box { x: number; y: number; w: number; h: number }

async function locate(page: Page, t: Target): Promise<Locator> {
  const base = 'role' in t ? page.getByRole(t.role, { name: t.name, ...(t.exact ? { exact: true } : {}) })
    : 'text' in t ? page.getByText(t.text)
      : page.locator(t.css)
  const l = t.nth !== undefined ? base.nth(t.nth) : base.first()
  await l.waitFor({ state: 'visible', timeout: 10_000 })
  return l
}

async function settle(page: Page): Promise<void> {
  await page.waitForLoadState('networkidle', { timeout: 4000 }).catch(() => undefined)
  await page.waitForTimeout(700)
}

async function recordScreen(page: Page, dir: string) {
  const cdp: CDPSession = await page.context().newCDPSession(page)
  const t0 = Date.now() / 1000
  const frames: { file: string; t: number }[] = []
  mkdirSync(dir, { recursive: true })
  cdp.on('Page.screencastFrame', ({ data, metadata, sessionId }) => {
    const file = join(dir, `${String(frames.length).padStart(6, '0')}.jpg`)
    writeFileSync(file, Buffer.from(data, 'base64'))
    frames.push({ file, t: (metadata.timestamp ?? Date.now() / 1000) - t0 })
    void cdp.send('Page.screencastFrameAck', { sessionId }).catch(() => undefined)
  })
  await cdp.send('Page.startScreencast', { format: 'jpeg', quality: 92, maxWidth: VIEW.width * 1.5, maxHeight: VIEW.height * 1.5, everyNthFrame: 1 })
  return {
    now: () => Date.now() / 1000 - t0,
    async stop(out: string): Promise<number> {
      const end = Date.now() / 1000 - t0
      await cdp.send('Page.stopScreencast').catch(() => undefined)
      if (!frames.length) throw new Error('no frames recorded')
      const list = [`file '${frames[0]!.file}'`, `duration ${frames[0]!.t.toFixed(3)}`]
      frames.forEach((f, i) => list.push(`file '${f.file}'`, `duration ${Math.max((frames[i + 1]?.t ?? end) - f.t, 1 / FPS).toFixed(3)}`))
      list.push(`file '${frames[frames.length - 1]!.file}'`)
      writeFileSync(join(dir, 'list.txt'), list.join('\n'))
      ffmpeg(['-f', 'concat', '-safe', '0', '-i', join(dir, 'list.txt'), '-vf', `scale=1440:900:flags=lanczos,fps=${FPS}`,
        '-c:v', 'libx264', '-preset', 'slow', '-crf', '24', '-pix_fmt', 'yuv420p', out])
      return end
    },
  }
}

function ffmpeg(args: string[]): void {
  const r = spawnSync('ffmpeg', ['-loglevel', 'error', '-y', ...args], { encoding: 'utf8' })
  if (r.status !== 0) throw new Error(`ffmpeg ${args.slice(0, 6).join(' ')}…: ${r.stderr}`)
}

const vttTime = (s: number): string => {
  const ms = Math.round(s * 1000)
  const h = Math.floor(ms / 3600000), m = Math.floor(ms / 60000) % 60, sec = Math.floor(ms / 1000) % 60
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}.${String(ms % 1000).padStart(3, '0')}`
}

export async function captureTour(browser: Browser, tour: Tour): Promise<void> {
  const out = join(MEDIA, tour.page)
  const work = mkdtempSync(join(tmpdir(), 'fairmind-tour-'))
  const voices = tour.steps.map(s => voiceLine(s.say))
  let context: BrowserContext | null = null
  try {
    context = await demoContext(browser)
    await context.addInitScript({ content: CURSOR_SCRIPT })
    const page = await context.newPage()
    await page.goto(`${APP}/dashboard`)
    await settle(page)
    const rec = await recordScreen(page, join(work, 'frames'))
    const cues: { start: number; end: number; text: string; file: string }[] = []
    const shots: { image: string; text: string; box?: Box }[] = []
    rmSync(out, { recursive: true, force: true })
    mkdirSync(out, { recursive: true })

    const cursor = async (show: boolean) => page.evaluate(v => {
      for (const id of ['docs-cursor', 'docs-ring']) { const el = document.getElementById(id); if (el) el.style.visibility = v ? 'visible' : 'hidden' }
    }, show)
    const pointAt = async (b: Box, press: boolean) => page.evaluate(([x, y, p]) => {
      const dot = document.getElementById('docs-cursor')
      const ring = document.getElementById('docs-ring')
      if (dot) dot.style.transform = `translate(${x}px, ${y}px)`
      if (ring && p) {
        ring.style.transition = 'none'
        ring.style.transform = `translate(${x}px, ${y}px) scale(.4)`
        ring.style.opacity = '1'
        void ring.offsetWidth
        ring.style.transition = 'transform .5s ease-out .55s, opacity .5s ease-out .55s'
        ring.style.transform = `translate(${x}px, ${y}px) scale(1.6)`
        ring.style.opacity = '0'
      }
    }, [b.x + b.w / 2, b.y + b.h / 2, press] as const)

    for (const [i, step] of tour.steps.entries()) {
      try {
        await runStep(page, step, i)
      } catch (e) {
        throw new Error(`tour ${tour.page}, step ${i + 1} ("${step.say.slice(0, 50)}…"): ${(e as Error).message}`)
      }
    }

    async function runStep(p: Page, step: Step, i: number): Promise<void> {
      if (step.goto) {
        await p.goto(`${APP}${step.goto}`)
        await settle(p)
      }
      if (step.scroll) {
        await p.mouse.move(VIEW.width / 2, VIEW.height / 2)
        for (let k = 0; k < Math.abs(step.scroll) / 80; k++) { await p.mouse.wheel(0, Math.sign(step.scroll) * 80); await sleep(40) }
        await settle(p)
      }
      const fills = step.fill ? [step.fill].flat() : []
      const target = step.click ?? fills[0]?.target ?? step.select?.target ?? step.point
      const loc = target ? await locate(p, target) : null
      if (loc) await loc.scrollIntoViewIfNeeded()
      const bb = loc ? await loc.boundingBox() : null
      const box = bb ? { x: Math.round(bb.x), y: Math.round(bb.y), w: Math.round(bb.width), h: Math.round(bb.height) } : undefined
      await cursor(false)
      const image = `step-${i + 1}.jpg`
      await p.screenshot({ path: join(out, image), type: 'jpeg', quality: 82, scale: 'css' })
      await cursor(true)
      shots.push({ image, text: step.say, ...(box ? { box } : {}) })

      const start = rec.now()
      const voice = voices[i]!
      cues.push({ start: start + 0.2, end: start + 0.2 + voice.seconds, text: step.say, file: voice.file })
      if (box) {
        await pointAt(box, Boolean(step.click))
        await sleep(650)
        if (step.click) await loc!.click()
        for (const [k, f] of fills.entries()) {
          const field = k === 0 ? loc! : await locate(p, f.target)
          if (k > 0) await pointAt(await field.boundingBox().then(b => ({ x: b!.x, y: b!.y, w: b!.width, h: b!.height })), false)
          await field.click()
          await field.pressSequentially(f.text, { delay: 45 })
        }
        if (step.select) await loc!.selectOption({ label: step.select.option })
        if (step.press) await p.keyboard.press(step.press)
        await settle(p)
      }
      const left = start + 0.2 + voice.seconds + 0.6 - rec.now()
      await sleep(Math.max(left, 0.4) * 1000)
    }

    await cursor(false)
    await page.screenshot({ path: join(out, 'end.jpg'), type: 'jpeg', quality: 82, scale: 'css' })
    await sleep(1200)
    const total = await rec.stop(join(work, 'silent.mp4'))

    // Narration placed at each step's start, mixed into one track, then muxed with the picture.
    const inputs = cues.flatMap(c => ['-i', c.file])
    const delays = cues.map((c, k) => `[${k}:a]adelay=${Math.round(c.start * 1000)}:all=1[a${k}]`).join(';')
    ffmpeg([...inputs, '-filter_complex', `${delays};${cues.map((_, k) => `[a${k}]`).join('')}amix=inputs=${cues.length}:normalize=0,apad=whole_dur=${total.toFixed(2)}[out]`,
      '-map', '[out]', '-ar', '48000', join(work, 'voice.wav')])
    ffmpeg(['-i', join(work, 'silent.mp4'), '-i', join(work, 'voice.wav'), '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '96k', '-shortest', '-movflags', '+faststart', join(out, 'video.mp4')])
    writeFileSync(join(out, 'captions.vtt'), `WEBVTT\n\n${cues.map((c, k) => `${k + 1}\n${vttTime(c.start)} --> ${vttTime(c.end)}\n${c.text}\n`).join('\n')}`)
    writeFileSync(join(out, 'demo.json'), JSON.stringify({ title: tour.title, width: VIEW.width, height: VIEW.height, steps: shots, end: 'end.jpg', seconds: Math.round(total) }, null, 2))
    console.log(`✓ ${tour.page}: ${tour.steps.length} steps, ${total.toFixed(0)} s`)
  } finally {
    await context?.close()
    rmSync(work, { recursive: true, force: true })
  }
}

async function main(): Promise<void> {
  if (!CHROME) throw new Error('Chrome not found: set FAIRMIND_BROWSER_EXECUTABLE')
  const filters = process.argv.slice(2)
  const dir = join(DOCS, 'tours')
  const files = readdirSync(dir).filter(f => f.endsWith('.ts')).sort()
  const tours: Tour[] = []
  for (const f of files) tours.push((await import(pathToFileURL(join(dir, f)).href) as { default: Tour }).default)
  const chosen = tours.filter(t => !filters.length || filters.some(w => t.page.includes(w)))
  const browser = await chromium.launch({ executablePath: CHROME })
  const failed: string[] = []
  try {
    for (const t of chosen) {
      try { await captureTour(browser, t) } catch (e) { failed.push((e as Error).message); console.error(`✗ ${(e as Error).message}`) }
    }
  } finally {
    await browser.close()
  }
  console.log(`\n${chosen.length - failed.length} of ${chosen.length} tours captured`)
  if (failed.length) process.exit(1)
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) await main()
