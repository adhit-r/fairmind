import { existsSync, readFileSync } from 'node:fs'
import { join } from 'node:path'

/** Where the recordings are served from: NEXT_PUBLIC_MEDIA_BASE when set (a bucket), this site's own files otherwise. */
export const MEDIA_BASE = (process.env.NEXT_PUBLIC_MEDIA_BASE ?? '/media').replace(/\/+$/, '')

export interface Demo {
  title: string
  width: number
  height: number
  seconds: number
  end: string
  steps: { image: string; text: string; box?: { x: number; y: number; w: number; h: number } }[]
}

/** A page's captured tour (`npm run capture`). A page that names a tour must have it: the build fails otherwise. */
export function readDemo(page: string): Demo {
  const file = join(process.cwd(), 'public/media', page, 'demo.json')
  if (!existsSync(file)) throw new Error(`no recording for "${page}": add tours/<name>.ts and run npm run capture -- ${page}`)
  return JSON.parse(readFileSync(file, 'utf8')) as Demo
}
