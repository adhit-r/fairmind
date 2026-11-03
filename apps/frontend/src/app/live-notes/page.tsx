"use client"

import { useEffect, useState } from "react"
import { createRealtimeClient, type SealedLiveQuery } from "@neon/realtime/client"
import { RealtimeProvider, useLiveQuery } from "@neon/realtime-react"
import type { LiveNote } from "../api/live-notes/route"

const fetchSealed = (): Promise<SealedLiveQuery<LiveNote>> =>
  fetch("/api/live-notes", { method: "POST" }).then((r) => r.json())

function Notes({ sealedQuery }: { sealedQuery: SealedLiveQuery<LiveNote> }) {
  const { data, status, error } = useLiveQuery(sealedQuery, { refreshQuery: fetchSealed })

  if (status === "error") return <p role="alert">Live updates stopped: {error.message}</p>
  if (data === undefined) return <p>Loading notes</p>
  return (
    <ul className="space-y-2">
      {data.map((note) => (
        <li key={note.id} className="rounded-[10px] border border-[var(--fm-line)] bg-white px-4 py-3">
          <span className="text-[var(--fm-ink3)]">#{note.id}</span> {note.body}
        </li>
      ))}
    </ul>
  )
}

export default function LiveNotesPage() {
  const [client] = useState(() => createRealtimeClient({ url: process.env.NEXT_PUBLIC_NEON_REALTIME_URL! }))
  const [sealedQuery, setSealedQuery] = useState<SealedLiveQuery<LiveNote>>()

  useEffect(() => {
    fetchSealed().then(setSealedQuery)
  }, [])

  return (
    <RealtimeProvider client={client}>
      <main className="mx-auto max-w-xl p-8">
        <h1 className="mb-4 text-xl font-semibold tracking-tight text-[var(--fm-ink)]">Live notes</h1>
        {sealedQuery ? <Notes sealedQuery={sealedQuery} /> : <p>Loading notes</p>}
      </main>
    </RealtimeProvider>
  )
}
