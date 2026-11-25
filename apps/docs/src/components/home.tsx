import { MEDIA_BASE, readDemo } from './media'

/** The front page's opening: what the docs are, two ways in, and the Getting around recording. */
export function HomeHero() {
  const page = 'app/getting-around'
  const demo = readDemo(page)
  const mins = `${Math.floor(demo.seconds / 60)}:${String(demo.seconds % 60).padStart(2, '0')}`
  return (
    <section className="fm-hero not-prose">
      <div>
        <p className="eyebrow">FairMind documentation</p>
        <h2>How to govern AI systems with FairMind, page by page.</h2>
        <p className="lede">Every page of the app explained: what it is for, how to use it and who can change things, with a narrated recording and a click-through you can step through here.</p>
        <div className="actions">
          <a className="pill pill-ink" href="/docs/get-started/quickstart">Start the quickstart</a>
          <a className="pill" href="/docs/app">Tour the app</a>
        </div>
      </div>
      <a className="shot" href="/docs/app">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={`${MEDIA_BASE}/${page}/${demo.steps[0]!.image}`} alt="FairMind Home, recorded in the demo" width={demo.width} height={demo.height} />
        <span>{demo.title} · {mins} · recorded in the FairMind demo</span>
      </a>
    </section>
  )
}

/** The demo, one line: what it holds and where it opens. */
export function DemoStrip() {
  return (
    <a className="fm-demo-strip not-prose" href="https://app.fairmind.xyz/login">
      <span className="dot" aria-hidden="true" />
      <span><strong>See it before you sign up.</strong> Try the demo opens a read-only organisation with real systems, a fairness test, evidence and a pending release decision.</span>
      <span className="go">Open the demo →</span>
    </a>
  )
}
