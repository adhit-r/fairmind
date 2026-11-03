import './iso.css'
import type { Figure } from './iso'

/** Renders a built isometric figure: one ordered list, so labels keep true depth. */
export function IsoFigure({ figure, label, className = '' }: { figure: Figure; label: string; className?: string }) {
  return (
    <div className={`fm-iso ${className}`}>
      <svg viewBox={figure.viewBox} role="img" aria-label={label}>
        {figure.items.map((it, i) =>
          it.kind === 'path' ? (
            <path key={i} d={it.d} fill={it.fill} className={it.cls} />
          ) : (
            <text key={i} transform={it.tr} className={it.cls}>
              {it.text}
            </text>
          ),
        )}
      </svg>
    </div>
  )
}
