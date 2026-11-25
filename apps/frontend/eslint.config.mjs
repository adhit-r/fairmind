import nextVitals from 'eslint-config-next/core-web-vitals'

// Next's recommended rules (React, hooks, Next.js, accessibility basics). CI fails
// on errors. The React Compiler readiness rules below are warnings for now: about
// 150 existing call sites need refactoring, not bug fixes, before they can be errors.
export default [
  ...nextVitals,
  {
    rules: {
      'react-hooks/refs': 'warn',
      'react-hooks/set-state-in-effect': 'warn',
      'react-hooks/immutability': 'warn',
      'react-hooks/static-components': 'warn',
    },
  },
  { ignores: ['.next/**', 'node_modules/**', 'public/**', 'next-env.d.ts'] },
]
