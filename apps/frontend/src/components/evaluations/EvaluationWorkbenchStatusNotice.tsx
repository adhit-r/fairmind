import { EvaluationWorkbenchRequestError } from '@/lib/api/hooks/useEvaluationWorkbenchV2'

export type EvaluationWorkbenchFailureState = {
  kind: 'denied' | 'unavailable'
  title: string
  message: string
}

export function evaluationWorkbenchFailureState(error: Error): EvaluationWorkbenchFailureState {
  if (error instanceof EvaluationWorkbenchRequestError && error.status === 403) {
    return {
      kind: 'denied',
      title: 'Evaluation access denied',
      message: 'You do not have permission to view this scoped evaluation data. No records were displayed.',
    }
  }
  return {
    kind: 'unavailable',
    title: 'Evaluation data unavailable',
    message: error.message,
  }
}

export function EvaluationWorkbenchStatusNotice({
  error,
  onRetry,
}: {
  error: Error
  onRetry?: () => void
}) {
  const state = evaluationWorkbenchFailureState(error)
  const denied = state.kind === 'denied'
  return (
    <section role="alert" className={`border-4 p-4 ${denied ? 'border-[#0F1412] bg-[#FFF1D6]' : 'border-[#D83A2E] bg-red-50'}`}>
      <h2 className={`text-lg font-black ${denied ? 'text-[#0F1412]' : 'text-[#8F2019]'}`}>{state.title}</h2>
      <p className={`mt-1 max-w-[70ch] text-sm font-semibold ${denied ? 'text-[#5B492E]' : 'text-[#5B211D]'}`}>{state.message}</p>
      {onRetry && !denied ? (
        <button type="button" onClick={onRetry} className="mt-4 inline-flex min-h-11 items-center border-2 border-[#0F1412] bg-[#FCFDF8] px-4 font-black shadow-[3px_3px_0_0_#0F1412] outline outline-0 outline-offset-2 transition-[transform,box-shadow] duration-150 hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-none focus:outline-2 focus:outline-[#0F1412] motion-reduce:transition-none motion-reduce:transform-none">Retry loading evaluations</button>
      ) : null}
    </section>
  )
}
