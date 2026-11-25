import { MEDIA_BASE, readDemo } from './media'

/** The page's narrated recording, captions on. */
export function Watch({ page }: { page: string }) {
  const demo = readDemo(page)
  const base = `${MEDIA_BASE}/${page}`
  return (
    <figure className="fm-media">
      <video
        controls
        preload="metadata"
        playsInline
        crossOrigin="anonymous"
        poster={`${base}/${demo.steps[0]?.image ?? demo.end}`}
        width={1440}
        height={900}
      >
        <source src={`${base}/video.mp4`} type="video/mp4" />
        <track kind="captions" src={`${base}/captions.vtt`} srcLang="en" label="English" default />
      </video>
      <figcaption >
        {demo.title} · {Math.floor(demo.seconds / 60)}:{String(demo.seconds % 60).padStart(2, '0')} · recorded in the FairMind demo
      </figcaption>
    </figure>
  )
}
