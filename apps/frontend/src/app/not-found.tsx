import Link from 'next/link'
import { OrangeLogo } from '@/components/OrangeLogo'
import { Card } from '@/components/ui/card'

export const metadata = { title: 'Page not found | FairMind' }

/** Unknown addresses get a FairMind page with a way back, not the framework default. */
export default function NotFound() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[var(--fm-bg)] px-4">
      <Card className="w-full max-w-md p-8 fm-card">
        <div className="flex flex-col items-center text-center">
          <OrangeLogo size="lg" />
          <h1 className="mt-4 text-[22px] font-semibold tracking-tight text-[var(--fm-ink)]">Page not found</h1>
          <p className="mt-2 text-sm text-[var(--fm-ink2)]">
            This address does not match a page. It may have moved, or the link is incomplete.
          </p>
          <Link
            href="/dashboard"
            className="mt-6 inline-flex h-9 items-center rounded-full bg-[var(--fm-ink)] px-4 text-[13px] font-semibold text-white"
          >
            Go to Home
          </Link>
        </div>
      </Card>
    </main>
  )
}
