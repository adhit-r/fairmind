"use client"

import { useEffect, useState } from "react"
import { createRealtimeClient, type SealedLiveQuery } from "@neon/realtime/client"
import { RealtimeProvider, useLiveQuery } from "@neon/realtime-react"
import type { LiveNote } from "@/app/api/live-notes/route"

const realtimeUrl = process.env.NEXT_PUBLIC_NEON_REALTIME_URL

async function fetchSealed(): Promise<SealedLiveQuery<LiveNote>> {
  const token = window.localStorage.getItem("access_token")
  const response = await fetch("/api/live-notes", {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(body.error ?? `Could not get a live query (${response.status})`)
  return body
}

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

function LiveNotes({ url }: { url: string }) {
  const [client] = useState(() => createRealtimeClient({ url }))
  const [sealedQuery, setSealedQuery] = useState<SealedLiveQuery<LiveNote>>()
  const [error, setError] = useState<string>()

  useEffect(() => {
    fetchSealed().then(setSealedQuery, (e: Error) => setError(e.message))
  }, [])

  if (error) return <p role="alert">{error}</p>
  return (
    <RealtimeProvider client={client}>
      {sealedQuery ? <Notes sealedQuery={sealedQuery} /> : <p>Loading notes</p>}
    </RealtimeProvider>
  )
}

export default function LiveNotesPage() {
  return (
    <main className="mx-auto max-w-xl p-8">
      <h1 className="mb-4 text-xl font-semibold tracking-tight text-[var(--fm-ink)]">Live notes</h1>
      {realtimeUrl ? <LiveNotes url={realtimeUrl} /> : <p role="alert">Realtime is not configured</p>}
    </main>
  )
}
