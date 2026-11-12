/**
 * Call fn every `ms` while the tab is visible. Hidden tabs make no requests; on
 * returning to the tab, fn runs at once if a tick was skipped. Returns a stop
 * function for an effect's cleanup.
 */
export function pollWhileVisible(fn: () => void, ms: number): () => void {
  let missed = false
  const tick = () => {
    if (document.hidden) missed = true
    else fn()
  }
  const onVisible = () => {
    if (!document.hidden && missed) {
      missed = false
      fn()
    }
  }
  const id = setInterval(tick, ms)
  document.addEventListener('visibilitychange', onVisible)
  return () => {
    clearInterval(id)
    document.removeEventListener('visibilitychange', onVisible)
  }
}
