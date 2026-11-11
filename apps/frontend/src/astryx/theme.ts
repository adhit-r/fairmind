import { defineTheme } from '@astryxdesign/core/theme'

/**
 * FairMind on Astryx. Warm grey paper, ink for text and actions, and the logo's orange for one job:
 * AI that was found but nobody has registered. Green marks what is approved and watched.
 * The rail is ink, so the three inventory columns carry the colour of the page.
 */
type Pair = [light: string, dark: string]
const paper: Pair = ['#f4f4f2', '#121315']
const card: Pair = ['#ffffff', '#1b1d20']
const sunken: Pair = ['#ebebe7', '#0d0e10']
const ink: Pair = ['#15171a', '#ecedef']
const inkMuted: Pair = ['#5a5f68', '#a9aeb7']
const inkFaint: Pair = ['#6a707c', '#8a909b']
const rule: Pair = ['#dcdcd6', '#2a2d32']
const ruleStrong: Pair = ['#7a7f88', '#70767f']
const onInk: Pair = ['#ffffff', '#15171a']

export const fairmindTheme = defineTheme({
  name: 'fairmind',
  typography: {
    scale: { base: 14, ratio: 1.2 },
    body: { family: 'var(--font-figtree)', fallbacks: 'system-ui, -apple-system, "Segoe UI", sans-serif' },
    heading: { family: 'var(--font-figtree)', fallbacks: 'system-ui, -apple-system, "Segoe UI", sans-serif', weight: 'bold' },
    code: { family: 'var(--font-mono)', fallbacks: 'ui-monospace, "SF Mono", Menlo, monospace' },
  },
  tokens: {
    // Ink is the action colour. Orange stays a small accent for what is not registered or needs a person.
    '--color-accent': ink,
    '--color-accent-muted': sunken,
    '--color-on-accent': onInk,
    '--color-text-accent': ink,
    '--color-icon-accent': ink,

    '--color-background-body': paper,
    '--color-background-surface': card,
    '--color-background-card': card,
    '--color-background-popover': card,
    '--color-background-muted': sunken,
    '--color-background-inverted': ['#15171a', '#ecedef'],
    '--color-overlay': ['#15171a66', '#000000a6'],
    '--color-overlay-hover': ['#15171a0a', '#ffffff0f'],
    '--color-overlay-pressed': ['#15171a14', '#ffffff1a'],

    '--color-text-primary': ink,
    '--color-text-secondary': inkMuted,
    '--color-text-disabled': inkFaint,
    '--color-icon-primary': ink,
    '--color-icon-secondary': inkMuted,
    '--color-icon-disabled': inkFaint,

    '--color-border': rule,
    '--color-border-emphasized': ruleStrong,
    '--color-skeleton': rule,
    '--color-track': rule,
    '--color-shadow': ['#15171a1f', '#00000080'],

    '--color-success': ['#12805f', '#4cc9a4'],
    '--color-on-success': onInk,
    '--color-success-muted': ['#dcf3e8', '#0f2e26'],
    '--color-on-success-muted': ['#0c5a43', '#8be0c4'],
    '--color-text-success': ['#0c6b52', '#4cc9a4'],
    // Found, not registered: the logo's orange.
    '--color-warning': ['#ff6b35', '#ff7d4d'],
    '--color-on-warning': ['#15171a', '#15171a'],
    '--color-warning-muted': ['#ffe3d6', '#3a1e12'],
    '--color-on-warning-muted': ['#8f2f0b', '#ffb597'],
    '--color-text-warning': ['#b23c0f', '#ff9a73'],
    '--color-error': ['#b4232c', '#ff8a80'],
    '--color-on-error': onInk,
    '--color-error-muted': ['#fbe4de', '#3a1512'],
    '--color-on-error-muted': ['#8a1f2b', '#ffa9a1'],
    '--color-text-error': ['#b4232c', '#ff8a80'],
    '--color-info': ['#1f5fae', '#8cc0f5'],
    '--color-on-info': onInk,
    '--color-info-muted': ['#e6f1fb', '#10263d'],
    '--color-on-info-muted': ['#0c447c', '#b5d8fa'],
    '--color-text-info': ['#0c447c', '#8cc0f5'],

    '--focus-outline-color': ink,

    '--radius-inner': '6px',
    '--radius-element': '10px',
    '--radius-container': '14px',
    '--radius-page': '16px',
  },
  localTokens: {
    '--fm-on-rail': ['#ffffff', '#ecedef'],
    '--fm-on-rail-muted': ['#a9aeb7', '#9aa0aa'],
    '--fm-found': ['#ff6b35', '#ff7d4d'],
    '--fm-found-wash': ['#ffe9df', '#2e1a11'],
    '--fm-found-ink': ['#15171a', '#15171a'],
    '--fm-ok': ['#12805f', '#1f8f6c'],
    '--fm-ok-wash': ['#e3f5ec', '#0f2a22'],
    '--fm-on-ok': ['#ffffff', '#ffffff'],
  },
  components: {
    card: {
      base: { boxShadow: 'none', borderWidth: '1px', borderStyle: 'solid', borderColor: 'var(--color-border)' },
    },
  },
})
