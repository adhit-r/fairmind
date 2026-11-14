/**
 * Narration for the tours: the offline Kokoro voice (af_heart) through `hyperframes tts`, one file per line, cached by
 * its text. Needs a Python with kokoro-onnx and soundfile (HYPERFRAMES_PYTHON, or ~/.cache/hyperframes/tts/venv).
 */
import { spawnSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { homedir } from 'node:os'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'

const DIR = join(fileURLToPath(new URL('..', import.meta.url)), '.capture/voice')
const TTS = join(homedir(), '.cache/hyperframes/tts')
const PY = process.env['HYPERFRAMES_PYTHON'] ?? join(TTS, 'venv/bin/python')
const VOICE = 'af_heart'
const HYPERFRAMES = 'hyperframes@0.9.39'

// How the voice should say names it would otherwise mispronounce. Captions keep the real spelling.
const SAY: [RegExp, string][] = [
  [/\bFairMind\b/g, 'Fair Mind'], [/\bLLM\b/g, 'L L M'], [/\bAI\b/g, 'A I'],
  [/\bDPO\b/g, 'D P O'], [/\bAPI\b/g, 'A P I'], [/\bDPDP\b/g, 'D P D P'],
  [/\bROPA\b/g, 'ropa'], [/\bJSON\b/g, 'jay-son'], [/\bCSV\b/g, 'C S V'], [/\be-mail\b/g, 'email'],
]
const spoken = (text: string): string => SAY.reduce((t, [re, to]) => t.replace(re, to), text)

export function voiceLine(text: string): { file: string; seconds: number } {
  mkdirSync(DIR, { recursive: true })
  const key = createHash('sha256').update(`${VOICE}|${spoken(text)}`).digest('hex').slice(0, 16)
  const file = join(DIR, `${key}.wav`)
  const meta = join(DIR, `${key}.json`)
  if (existsSync(file) && existsSync(meta)) return { file, seconds: (JSON.parse(readFileSync(meta, 'utf8')) as { seconds: number }).seconds }
  if (!existsSync(PY)) throw new Error(`narration needs ${PY} with kokoro-onnx and soundfile (see apps/docs/README.md)`)
  const r = spawnSync('npx', ['-y', HYPERFRAMES, 'tts', spoken(text), '--voice', VOICE, '-o', file, '--json'], {
    encoding: 'utf8', env: { ...process.env, HYPERFRAMES_PYTHON: PY },
  })
  const answer = JSON.parse(r.stdout.trim().split('\n').pop() || '{}') as { ok?: boolean; durationSeconds?: number; error?: { message: string } }
  if (!answer.ok || !answer.durationSeconds) throw new Error(`narration failed: ${answer.error?.message ?? r.stderr}`)
  writeFileSync(meta, JSON.stringify({ text, seconds: answer.durationSeconds }))
  return { file, seconds: answer.durationSeconds }
}
