// Maturity of what a page documents. Keep the labels in step with the README's
// "Current status" and docs/STATUS.md, which are the source of truth.
const STATES = {
  shipped: { label: 'Works today', hint: 'On the main path and usable now.' },
  partial: { label: 'Partly done', hint: 'Usable, with the gaps listed on this page.' },
  alpha: { label: 'Alpha, off by default', hint: 'Built and tested, behind a feature gate.' },
  'not-built': { label: 'Not built yet', hint: 'Planned; do not rely on it.' },
} as const;

export type StatusState = keyof typeof STATES;

export function Status({ state, children }: { state: StatusState; children?: React.ReactNode }) {
  const s = STATES[state];
  return (
    <p className="doc-status" data-state={state}>
      <strong>{s.label}</strong>
      <span>{children ?? s.hint}</span>
    </p>
  );
}
