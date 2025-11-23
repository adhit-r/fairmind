# Fairmind Design System Implementation

## Overview

This document describes the implementation of the Fairmind Design System, which follows the "New Brutalist Professional" design philosophy. The design system has been implemented using Mantine UI components with custom theming and CSS variables.

## Implementation Details

### 1. Theme Provider

The design system is implemented through the `GlassmorphicThemeProvider` component located at `src/providers/glassmorphic-theme-provider.tsx`. This provider:

- Configures Mantine theme with brutalist design principles
- Defines the color palette based on the design system specifications
- Sets typography using Inter and Space Grotesk fonts
- Configures spacing, border radius, and shadows
- Provides a consistent design language across the application

### 2. CSS Custom Properties

CSS custom properties have been defined in `src/styles/design-system.css` for all design tokens:

- Colors (primary, accent, gray scale, semantic)
- Typography (font families, sizes, weights, line heights)
- Spacing system (brutalist grid)
- Border radius
- Shadows
- Transitions
- Z-index scale
- Breakpoints

### 3. Design Tokens Hook

A custom hook `useDesignSystem` has been created at `src/hooks/use-design-system.ts` to easily access design tokens in components.

### 4. Brutalist Component Styles

Brutalist styles have been applied to core components:

- Buttons with sharp edges and strong shadows
- Cards with brutalist design principles
- Inputs with high-contrast borders
- Global styles for consistent application appearance

## Key Features

### Color Palette

The design system implements a high-contrast color palette with:
- Primary black (`#000000`) and white (`#ffffff`)
- Accent orange (`#ff6b35`) for branding and actions
- Comprehensive gray scale from 100-900
- Semantic colors for success, warning, error, and info states

### Typography

Typography follows a clear hierarchy with:
- Primary font: Inter for body text and UI elements
- Display font: Space Grotesk for headings and branding
- Monospace font: JetBrains Mono for technical content
- Consistent font sizing from XS (12px) to 7XL (72px)

### Spacing System

The spacing system follows a "Brutalist Grid System" with a base unit of 0.25rem (4px):
- Consistent spacing scale from 1 (4px) to 32 (128px)
- Applied throughout the application for consistent layout

### Border Radius

Minimal border radius for sharp, brutalist edges:
- None (0px) for sharp edges
- Small (2px) for subtle rounding
- Base (4px) for standard components
- Medium (6px) and larger for special cases

### Shadows

Brutalist shadows with hard edges and strong contrast:
- Small, base, and medium standard shadows
- Signature brutalist shadows (4px 4px 0px 0px #000000)
- Large brutalist shadows for emphasis

## Components

### GlassmorphicCard

Updated to align with brutalist design principles while maintaining glassmorphic effects where appropriate.

### DesignSystemDemo

A demo component showcasing the design system implementation is available at `src/components/demo/DesignSystemDemo.tsx`.

## Usage

To use the design system in your components:

1. Wrap your application with the `GlassmorphicThemeProvider`
2. Use the `useDesignSystem` hook to access design tokens
3. Apply CSS custom properties directly in your styles
4. Use Mantine components which automatically inherit the theme

## Design System Page

A dedicated design system page is available at `/design-system` to showcase all implemented components and tokens.

## Accessibility

The design system follows WCAG 2.1 AA standards with:
- Minimum contrast ratio of 4.5:1 for normal text
- Focus states with 2px solid orange outline
- Semantic color coding with text indicators

## Future Enhancements

- Expand component library with more brutalist-styled components
- Add animation guidelines and implementations
- Create comprehensive documentation site
- Implement theme switching for different brutalist variations