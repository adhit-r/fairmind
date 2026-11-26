// The widgets an Ask FairMind answer may use. Props are fixed options and short words, never figures:
// each widget reads its own data from the signed-in user's endpoints, so the model cannot state a number.
// No React here: scripts/gen-ask-board-prompt.mts builds the model's prompt from this file with empty renderers.
import { createLibrary, defineComponent } from '@openuidev/react-lang'
import { z } from 'zod/v4'

export const RELEASE_FILTERS = ['failing', 'waiting_decision', 'all'] as const
export const FRAMEWORK_SCOPES = ['all', 'needs_attention'] as const
export const WAITING_KINDS = ['all', 'approval', 'run', 'audit', 'policy'] as const

// ponytail: loose on purpose, the real renderers are typed where they are written (AskBoard.tsx).
export type BoardRenderers = Record<'Board' | 'ReleaseMatrix' | 'WaitingOnYou' | 'FrameworkReadiness' | 'Note', (arg: { props: any; renderNode: any }) => any>

export function buildAskLibrary(r: BoardRenderers) {
  const ReleaseMatrix = defineComponent({
    name: 'ReleaseMatrix',
    description:
      'A table of systems against their release checks. filter "failing" lists systems with a failing check, "waiting_decision" those whose release decision waits on a person, "all" every system.',
    props: z.object({ filter: z.enum(RELEASE_FILTERS) }),
    component: r.ReleaseMatrix,
  })
  const WaitingOnYou = defineComponent({
    name: 'WaitingOnYou',
    description: 'The list of things that wait on the signed-in person. kind narrows it, "all" lists everything.',
    props: z.object({ kind: z.enum(WAITING_KINDS) }),
    component: r.WaitingOnYou,
  })
  const FrameworkReadiness = defineComponent({
    name: 'FrameworkReadiness',
    description:
      'The frameworks the organisation follows, each with a bar of how many of its requirements are met, in progress, need attention or not started. scope "needs_attention" keeps only frameworks with requirements that need attention.',
    props: z.object({ scope: z.enum(FRAMEWORK_SCOPES) }),
    component: r.FrameworkReadiness,
  })
  const Note = defineComponent({
    name: 'Note',
    description: 'One short plain sentence under the widgets, for what they do not show. Never a figure, a system name or a verdict.',
    props: z.object({ text: z.string().max(240) }),
    component: r.Note,
  })
  const Board = defineComponent({
    name: 'Board',
    description: 'The root. Widgets stack top to bottom, so put the one that answers the question first.',
    props: z.object({ widgets: z.array(z.union([ReleaseMatrix.ref, WaitingOnYou.ref, FrameworkReadiness.ref, Note.ref])).max(4) }),
    component: r.Board,
  })
  return createLibrary({ root: 'Board', components: [Board, ReleaseMatrix, WaitingOnYou, FrameworkReadiness, Note] })
}

export const BOARD_EXAMPLES = [
  'root = Board([m, w])\nm = ReleaseMatrix("failing")\nw = WaitingOnYou("all")',
  'root = Board([f])\nf = FrameworkReadiness("needs_attention")',
  'root = Board([w, n])\nw = WaitingOnYou("approval")\nn = Note("Decisions open on each system\'s own page.")',
]

export const BOARD_RULES = [
  'Use at most 4 widgets. Use only the widgets listed here.',
  'Never write a number, a system name or a verdict anywhere, including in Note: the widgets show the figures.',
  'If no widget fits the question, leave the board empty rather than forcing one.',
]
