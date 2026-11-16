import type { Config } from "tailwindcss"

/**
 * Colour tokens come from CSS variables in src/app/globals.css. The color-mix
 * wrapper keeps Tailwind opacity modifiers (bg-primary/10) working with any
 * colour format (hex or oklch) and in both light and dark mode.
 */
const token = (name: string) =>
	`color-mix(in srgb, var(--${name}) calc(<alpha-value> * 100%), transparent)`

const tone = (name: string) => ({
	DEFAULT: token(name),
	foreground: token(`${name}-foreground`),
	subtle: token(`${name}-subtle`),
	strong: token(`${name}-strong`),
})

const config: Config = {
	darkMode: ["class"],
	content: [
		"./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
		"./src/components/**/*.{js,ts,jsx,tsx,mdx}",
		"./src/app/**/*.{js,ts,jsx,tsx,mdx}",
	],
	theme: {
		extend: {
			colors: {
				border: token('border'),
				input: token('input'),
				ring: token('ring'),
				background: token('background'),
				foreground: token('foreground'),
				primary: {
					DEFAULT: token('primary'),
					foreground: token('primary-foreground'),
					strong: token('primary-strong'),
					subtle: token('primary-subtle'),
				},
				secondary: {
					DEFAULT: token('secondary'),
					foreground: token('secondary-foreground'),
				},
				destructive: tone('destructive'),
				success: tone('success'),
				warning: tone('warning'),
				info: tone('info'),
				attention: tone('attention'),
				muted: {
					DEFAULT: token('muted'),
					foreground: token('muted-foreground'),
				},
				accent: {
					DEFAULT: token('accent'),
					foreground: token('accent-foreground'),
				},
				'accent-action': {
					DEFAULT: token('accent-action'),
					foreground: token('accent-action-foreground'),
				},
				popover: {
					DEFAULT: token('popover'),
					foreground: token('popover-foreground'),
				},
				card: {
					DEFAULT: token('card'),
					foreground: token('card-foreground'),
				},
				chart: {
					1: token('chart-1'),
					2: token('chart-2'),
					3: token('chart-3'),
					4: token('chart-4'),
					5: token('chart-5'),
					6: token('chart-6'),
				},
				sidebar: {
					DEFAULT: token('sidebar-background'),
					foreground: token('sidebar-foreground'),
					primary: token('sidebar-primary'),
					'primary-foreground': token('sidebar-primary-foreground'),
					accent: token('sidebar-accent'),
					'accent-foreground': token('sidebar-accent-foreground'),
					border: token('sidebar-border'),
					ring: token('sidebar-ring'),
				},
				/* legacy - remove after migration */
				main: token('main'),
				'main-foreground': token('main-foreground'),
				'secondary-background': token('secondary-background'),
				orange: {
					DEFAULT: token('accent-action'),
					dark: token('attention-strong'),
				},
				black: {
					DEFAULT: token('foreground'),
				},
			},
			borderRadius: {
				lg: 'calc(var(--radius) + 2px)',
				md: 'var(--radius)',
				sm: 'calc(var(--radius) - 2px)',
				/* legacy - remove after migration */
				base: 'var(--radius)',
			},
			fontFamily: {
				sans: ['var(--font-raleway)', 'system-ui', 'sans-serif'],
			},
			boxShadow: {
				/* legacy - remove after migration: hard offset shadows are gone */
				brutal: 'none',
				shadow: 'none',
				'brutal-lg': 'none',
				'brutal-xl': 'none',
			},
			keyframes: {
				'accordion-down': {
					from: {
						height: '0'
					},
					to: {
						height: 'var(--radix-accordion-content-height)'
					}
				},
				'accordion-up': {
					from: {
						height: 'var(--radix-accordion-content-height)'
					},
					to: {
						height: '0'
					}
				}
			},
			animation: {
				'accordion-down': 'accordion-down 0.2s ease-out',
				'accordion-up': 'accordion-up 0.2s ease-out'
			}
		}
	},
	plugins: [require("tailwindcss-animate")],
}

export default config
