import * as React from 'react'

/** Test-only: replaces a method until the returned restore function is called. */
export function stub<T extends object>(target: T, key: keyof T, impl: (...args: any[]) => unknown) {
  const original = target[key]
  ;(target as any)[key] = impl
  return () => {
    target[key] = original
  }
}

/**
 * Test-only: runs a hook once outside a renderer. State setters write into `states` (in hook call
 * order), so a test reads the hook's state after awaiting one of its callbacks. Effects do not run.
 */
export function runHook<T>(hook: () => T) {
  const states: any[] = []
  const internals = (React as any).__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED.ReactCurrentDispatcher
  const previous = internals.current
  internals.current = {
    useState: (initial: unknown) => {
      const index = states.push(typeof initial === 'function' ? (initial as () => unknown)() : initial) - 1
      return [states[index], (next: unknown) => {
        states[index] = typeof next === 'function' ? (next as (value: unknown) => unknown)(states[index]) : next
      }]
    },
    useRef: (current: unknown) => ({ current }),
    useCallback: (callback: unknown) => callback,
    useMemo: (factory: () => unknown) => factory(),
    useEffect: () => {},
  }
  try {
    return { result: hook(), states }
  } finally {
    internals.current = previous
  }
}
