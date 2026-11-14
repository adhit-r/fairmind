/**
 * The post-sign-in destination from ?next=, kept on this site, else the dashboard.
 * Compares the resolved origin: browsers drop tabs and newlines, so a string check
 * on "/\t/evil.com" passes but the URL resolves to evil.com.
 */
export function safeNextPath(next: string | null, origin: string): string {
  if (!next) return '/dashboard'
  const url = new URL(next, origin)
  return url.origin === origin ? url.pathname + url.search + url.hash : '/dashboard'
}
