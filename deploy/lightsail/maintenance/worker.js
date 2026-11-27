// Passes every request to the app. When the app is down (tunnel or container restarting),
// a browser page load gets a calm 503 page that retries on its own; API calls get the error as is.
// Temporary outage copy for the database move; restore the "updating" copy after cutover (README, Database).
// ponytail: free plan allows 100k Worker requests a day; past that, set the route to fail open.
const DOWN = new Set([502, 503, 504, 520, 521, 522, 523, 524, 530])

const PAGE = `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>FairMind is offline for maintenance</title>
<style>
:root{--bg:#f4f4f2;--card:#fff;--ink:#15171a;--ink2:#5a5f68;--line:rgba(21,23,26,.08);--brand:#ff6b35}
@media (prefers-color-scheme:dark){:root{--bg:#121315;--card:#1b1d20;--ink:#f1f1ef;--ink2:#a3a8b0;--line:rgba(255,255,255,.1)}}
*{box-sizing:border-box}
body{margin:0;min-height:100vh;display:grid;place-items:center;padding:16px;background:var(--bg);color:var(--ink);
font:15px/1.5 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:420px;width:100%;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:28px;
box-shadow:0 1px 2px rgba(21,23,26,.04),0 8px 24px rgba(21,23,26,.06)}
.mark{width:10px;height:10px;border-radius:50%;background:var(--brand);margin-bottom:18px}
h1{margin:0 0 6px;font-size:19px;font-weight:600;letter-spacing:-.01em}
p{margin:0;color:var(--ink2)}
small{display:block;margin-top:18px;color:var(--ink2);font-size:12px}
</style></head>
<body><main role="status" aria-live="polite">
<div class="mark" aria-hidden="true"></div>
<h1>FairMind is offline for maintenance</h1>
<p>We are moving our database to new hosting. We expect FairMind to be back on 1 December.</p>
<small id="s">This page reloads by itself when FairMind is back.</small>
</main>
<script>
setInterval(async()=>{try{const r=await fetch(location.href,{method:"HEAD",cache:"no-store"});if(r.ok)location.reload()}catch(e){}},10000)
</script>
</body></html>`

export default {
  async fetch(request) {
    let res = null
    try { res = await fetch(request) } catch {}
    if (res && !DOWN.has(res.status)) return res
    const page = request.method === 'GET' && (request.headers.get('accept') || '').includes('text/html')
    if (!page) return res || new Response('FairMind is restarting', { status: 503, headers: { 'retry-after': '30' } })
    return new Response(PAGE, {
      status: 503,
      headers: { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store', 'retry-after': '30' },
    })
  },
}
