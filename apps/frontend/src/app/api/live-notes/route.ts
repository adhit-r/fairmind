import { createRealtime, rawSql } from "@neon/realtime/server"

export type LiveNote = { id: number; body: string; created_at: Date }

const realtime = createRealtime({ secret: process.env.NEON_REALTIME_SECRET!, db: "neondb" })

const liveNotesQuery = rawSql<LiveNote>(
  `SELECT id, body, created_at FROM live_notes ORDER BY id DESC LIMIT 50`
)

// Seals the fixed query; called on mount and again by useLiveQuery's refreshQuery before expiry.
// ponytail: no auth check, live_notes holds no user data; add a session check and scope the query once it does.
export async function POST() {
  return Response.json(await realtime.seal({ query: liveNotesQuery }))
}
