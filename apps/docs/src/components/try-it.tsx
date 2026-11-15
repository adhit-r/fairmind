import { MEDIA_BASE, readDemo } from './media'
import { ClickThrough } from './click-through'

/** The click-through demo of the page's tour: the real screens, with the control to use at each step. */
export function TryIt({ page }: { page: string }) {
  return <ClickThrough base={`${MEDIA_BASE}/${page}`} demo={readDemo(page)} />
}
