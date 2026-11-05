import { BACKEND_BASE_URL } from "@/lib/backend-url"

export type LiveNote = { id: number; body: string; created_at: Date }

// Checks the caller's bearer token against the backend, then refuses: live_notes has no
// organisation column (id, body, created_at), so no query over it can be scoped to the
// caller's org and sealing one would show every org's notes. Once the table has org_id,
// seal `... WHERE org_id = $1` here with NEON_REALTIME_SECRET (see a7ff29b for the sealing).
export async function POST(request: Request) {
  const authorization = request.headers.get("authorization")
  if (!authorization?.startsWith("Bearer ")) {
    return Response.json({ error: "Sign in to view live notes" }, { status: 401 })
  }

  let me: Response
  try {
    me = await fetch(`${BACKEND_BASE_URL}/api/v1/auth/me`, { headers: { authorization } })
  } catch {
    return Response.json({ error: "Could not verify the session" }, { status: 502 })
  }
  if (me.status >= 500) return Response.json({ error: "Could not verify the session" }, { status: 502 })
  if (!me.ok) return Response.json({ error: "Sign in to view live notes" }, { status: 401 })

  return Response.json(
    { error: "Live notes are not scoped to an organisation yet, so they are not served" },
    { status: 501 }
  )
}
