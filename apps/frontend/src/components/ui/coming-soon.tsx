import { Card } from "@/components/ui/card"

export function ComingSoon({ title, children }: { title: string; children?: React.ReactNode }) {
  return (
    <div className="mx-auto max-w-3xl px-6 py-10">
      <Card className="p-8">
        <span className="rounded-full bg-[var(--fm-bg)] px-3 py-1.5 text-[11.5px] font-semibold text-[var(--fm-ink2)]">
          Coming soon
        </span>
        <h1 className="mt-4 text-2xl font-semibold tracking-tight text-[var(--fm-ink)]">{title}</h1>
        {children && <p className="mt-2 text-sm text-[var(--fm-ink2)]">{children}</p>}
      </Card>
    </div>
  )
}
