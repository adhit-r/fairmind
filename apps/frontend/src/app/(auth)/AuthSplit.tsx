import type { ReactNode } from 'react'
import { AuthDemo } from '@/components/stageshow/AuthDemo'
import { Illustration } from '@/components/stageshow/fm'

/** Sign-in and sign-up: the form on the left, on wide screens the product at work on the right. */
export function AuthSplit({ children }: { children: ReactNode }) {
  return (
    <div className="grid min-h-screen bg-background lg:grid-cols-2">
      <div className="flex items-center justify-center p-4">{children}</div>
      {/* The stage sits in the panel's bottom-right corner, so the app window runs off the screen edge. */}
      <aside className="hidden flex-col items-end justify-end overflow-hidden border-l border-[var(--fm-line)] bg-[var(--fm-bg)] lg:flex">
        <Illustration
          captionFirst
          className="w-full max-w-[720px]"
          label="FairMind discovers a model, adds it to the inventory, plans and runs its release checks, and the gate returns a verdict"
        >
          <AuthDemo />
        </Illustration>
      </aside>
    </div>
  )
}
