import type { Metadata } from 'next'

// The link carries its own token; never send it on to another site.
export const metadata: Metadata = { title: 'Is this yours? | FairMind', referrer: 'no-referrer', robots: { index: false, follow: false } }

export default function OwnerCheckLayout({ children }: { children: React.ReactNode }) {
  return children
}
