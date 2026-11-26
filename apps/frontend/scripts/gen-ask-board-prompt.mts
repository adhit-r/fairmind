// Writes the widget library's prompt where the backend reads it. `--check` fails when the file is stale.
// Run from apps/frontend: npm run gen:ask-board | npm run check:ask-board
import { readFileSync, writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { BOARD_EXAMPLES, BOARD_RULES, buildAskLibrary } from '../src/astryx/ask/boardSpec.ts'

const none = () => null
const library = buildAskLibrary({ Board: none, ReleaseMatrix: none, WaitingOnYou: none, Note: none })
const prompt = library.prompt({
  preamble: 'The board field is an OpenUI Lang program.',
  additionalRules: BOARD_RULES,
  examples: BOARD_EXAMPLES,
  toolCalls: false,
  bindings: false,
  builtinFunctions: false,
})

const target = fileURLToPath(new URL('../../backend/src/api/routers/ask_board_prompt.txt', import.meta.url))
const text = `${prompt.trim()}\n`

if (process.argv.includes('--check')) {
  let current = ''
  try {
    current = readFileSync(target, 'utf8')
  } catch {}
  if (current !== text) {
    console.error('ask_board_prompt.txt is out of date: run npm run gen:ask-board in apps/frontend')
    process.exit(1)
  }
} else {
  writeFileSync(target, text)
  console.log(`wrote ${target}`)
}
