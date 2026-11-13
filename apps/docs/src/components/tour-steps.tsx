import { MEDIA_BASE, readDemo } from './media'

/** The page's recorded tour as numbered steps, each with the real screen it was captured on. */
export function TourSteps({ page }: { page: string }) {
  const demo = readDemo(page)
  const base = `${MEDIA_BASE}/${page}`
  return (
    <ol className="fm-steps not-prose">
      {demo.steps.map((s, i) => (
        <li key={s.image}>
          <span className="n" aria-hidden="true">{i + 1}</span>
          <p>{s.text}</p>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={`${base}/${s.image}`} alt={`Step ${i + 1}: ${s.text}`} width={demo.width} height={demo.height} loading="lazy" />
        </li>
      ))}
    </ol>
  )
}
