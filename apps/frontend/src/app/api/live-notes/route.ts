import { createRealtime, rawSql } from "@neon/realtime/server"

export type LiveNote = { id: number; body: string; created_at: Date }

const liveNotesQuery = rawSql<LiveNote>(
  `SELECT id, body, created_at FROM live_notes ORDER BY id DESC LIMIT 50`
)

// Seals the fixed query; called on mount and again by useLiveQuery's refreshQuery before expiry.
// ponytail: no auth check, live_notes holds no user data; add a session check and scope the query once it does.
// Created per request, not at module load: `next build` imports this file without the secret.
export async function POST() {
  const secret = process.env.NEON_REALTIME_SECRET
  if (!secret) return Response.json({ error: "Realtime is not configured" }, { status: 503 })
  const realtime = createRealtime({ secret, db: "neondb" })
  return Response.json(await realtime.seal({ query: liveNotesQuery }))
}
