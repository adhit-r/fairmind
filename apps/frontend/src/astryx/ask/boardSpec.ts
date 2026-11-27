// The widgets an Ask FairMind answer may use. Props are fixed options and short words, never figures:
// each widget reads its own data from the signed-in user's endpoints, so the model cannot state a number.
// No React here: scripts/gen-ask-board-prompt.mts builds the model's prompt from this file with empty renderers.
import { createLibrary, defineComponent } from '@openuidev/react-lang'
import { z } from 'zod/v4'

export const RELEASE_FILTERS = ['failing', 'waiting_decision', 'all'] as const
export const FRAMEWORK_SCOPES = ['all', 'needs_attention'] as const
export const WAITING_KINDS = ['all', 'approval', 'run', 'audit', 'policy'] as const

// ponytail: loose on purpose, the real renderers are typed where they are written (AskBoard.tsx).
export type BoardRenderers = Record<'Board' | 'ReleaseMatrix' | 'WaitingOnYou' | 'FrameworkReadiness' | 'FailedRunsTrend' | 'EvalCompare' | 'SystemTimeline' | 'Note', (arg: { props: any; renderNode: any }) => any>

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
  const FailedRunsTrend = defineComponent({
    name: 'FailedRunsTrend',
    description: 'A bar chart of how many fairness, monitoring and evaluation runs failed in each of the last eight weeks, across all systems. It counts failed runs, not failing checks.',
    props: z.object({}),
    component: r.FailedRunsTrend,
  })
  // A system is named by the id given in the facts, never by name. The widget reads that system through the
  // signed-in user's own organisation, so an id from another organisation or a made-up one finds nothing.
  const EvalCompare = defineComponent({
    name: 'EvalCompare',
    description:
      'One system\'s latest fairness run and catalogue evaluations against the run before each, as a table of before, now and state. systemId is the id of the system from the facts.',
    props: z.object({ systemId: z.string().max(80) }),
    component: r.EvalCompare,
  })
  const SystemTimeline = defineComponent({
    name: 'SystemTimeline',
    description:
      'One system\'s recent history, newest first: fairness runs, monitoring runs, evaluations and release decisions. systemId is the id of the system from the facts.',
    props: z.object({ systemId: z.string().max(80) }),
    component: r.SystemTimeline,
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
    props: z.object({ widgets: z.array(z.union([ReleaseMatrix.ref, WaitingOnYou.ref, FrameworkReadiness.ref, FailedRunsTrend.ref, EvalCompare.ref, SystemTimeline.ref, Note.ref])).max(4) }),
    component: r.Board,
  })
  return createLibrary({ root: 'Board', components: [Board, ReleaseMatrix, WaitingOnYou, FrameworkReadiness, FailedRunsTrend, EvalCompare, SystemTimeline, Note] })
}

export const BOARD_EXAMPLES = [
  'root = Board([m, w])\nm = ReleaseMatrix("failing")\nw = WaitingOnYou("all")',
  'root = Board([f])\nf = FrameworkReadiness("needs_attention")',
  'root = Board([m, k])\nm = ReleaseMatrix("failing")\nk = FailedRunsTrend()',
  'root = Board([c, t])\nc = EvalCompare("<system id from the facts>")\nt = SystemTimeline("<system id from the facts>")',
  'root = Board([w, n])\nw = WaitingOnYou("approval")\nn = Note("Decisions open on each system\'s own page.")',
]

export const BOARD_RULES = [
  'Use at most 4 widgets. Use only the widgets listed here.',
  'Never write a number, a system name or a verdict anywhere, including in Note: the widgets show the figures. A system is named only by its id from the facts, as the argument of EvalCompare or SystemTimeline.',
  'If no widget fits the question, leave the board empty rather than forcing one.',
]
