/**
 * The facts strip at the top of an app page: where it is in the menu, its address, who can change things there, and
 * whether it works today. Every member of an organisation can open every page; what a person may change is checked by
 * the server against their role's permissions.
 */
const STATUS = {
  shipped: { label: 'Works today', tone: '#12805f' },
  partial: { label: 'Partly done', tone: '#b45309' },
  alpha: { label: 'Alpha, off by default', tone: '#6d28d9' },
  'not-built': { label: 'Not built yet', tone: '#b91c1c' },
} as const

export function Access({ where, address, change, status = 'shipped' }: {
  where: string; address: string; change?: string; status?: keyof typeof STATUS
}) {
  const s = STATUS[status]
  return (
    <dl className="fm-facts not-prose">
      <div><dt>In the menu</dt><dd>{where}</dd></div>
      <div><dt>Address</dt><dd className="mono">{address}</dd></div>
      <div><dt>Who can change it</dt><dd>{change ?? 'Any member'}</dd></div>
      <div><dt>Status</dt><dd><span className="dot" style={{ background: s.tone }} aria-hidden="true" />{s.label}</dd></div>
      <p className="fm-facts-note">Every member of the organisation can open this page. In the <a href="https://app.fairmind.xyz/login">demo</a> it is read-only.</p>
    </dl>
  )
}
