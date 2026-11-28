import type { Metadata } from 'next'

// The link names a sealed board; never index it and never send its address on to another site.
export const metadata: Metadata = { title: 'Shared view | FairMind', referrer: 'no-referrer', robots: { index: false, follow: false } }

export default function SharedViewLayout({ children }: { children: React.ReactNode }) {
  return children
}
