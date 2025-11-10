# Fairmind Design System Implementation Guide

## Overview

The Fairmind Design System is based on the "New Brutalist Professional" design philosophy, which combines brutalist design principles with professional polish and enterprise-grade aesthetics. This guide explains how to implement and use the design system in the Fairmind AI Governance Platform.

## Design Philosophy Principles

1. **High contrast for accessibility**
2. **Minimal border radius for sharp edges**
3. **Bold typography with clear hierarchy**
4. **Consistent orange accent branding**
5. **Professional appearance without unnecessary decoration**
6. **Functional over decorative design**

## Color Palette

### Primary Colors
- **Black**: `#000000` - Primary black for text and borders
- **White**: `#ffffff` - Primary white for backgrounds

### Accent Colors
- **Orange**: `#ff6b35` - Primary accent color for actions and branding
- **Orange Dark**: `#e55a2b` - Darker orange for hover states
- **Orange Light**: `#ff8c69` - Lighter orange for subtle accents

### Gray Scale
- **Gray 100**: `#f5f5f5` - Lightest gray for subtle backgrounds
- **Gray 200**: `#e5e5e5` - Light gray for borders and dividers
- **Gray 300**: `#d4d4d4` - Medium light gray
- **Gray 400**: `#a3a3a3` - Medium gray for secondary text
- **Gray 500**: `#737373` - Medium gray for body text
- **Gray 600**: `#525252` - Dark gray for emphasis
- **Gray 700**: `#404040` - Darker gray for headings
- **Gray 800**: `#262626` - Very dark gray
- **Gray 900**: `#171717` - Darkest gray

### Semantic Colors
- **Success**: `#22c55e` - Success state color
- **Warning**: `#f59e0b` - Warning state color
- **Error**: `#ef4444` - Error state color
- **Info**: `#3b82f6` - Info state color

## Typography

### Font Families
- **Primary**: `Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`
- **Display**: `Space Grotesk, Inter, sans-serif`
- **Mono**: `JetBrains Mono, 'Fira Code', 'Monaco', monospace`

### Font Sizes
- **XS**: `0.75rem` (12px) - Extra small text
- **SM**: `0.875rem` (14px) - Small text
- **Base**: `1rem` (16px) - Base text size
- **LG**: `1.125rem` (18px) - Large text
- **XL**: `1.25rem` (20px) - Extra large text
- **2XL**: `1.5rem` (24px) - 2X large text
- **3XL**: `1.875rem` (30px) - 3X large text
- **4XL**: `2.25rem` (36px) - 4X large text
- **5XL**: `3rem` (48px) - 5X large text
- **6XL**: `3.75rem` (60px) - 6X large text
- **7XL**: `4.5rem` (72px) - 7X large text

## Spacing System

The spacing system follows a "Brutalist Grid System" with a base unit of `0.25rem` (4px):

- **1**: `0.25rem` (4px) - Extra small spacing
- **2**: `0.5rem` (8px) - Small spacing
- **3**: `0.75rem` (12px) - Medium small spacing
- **4**: `1rem` (16px) - Base spacing
- **5**: `1.25rem` (20px) - Medium spacing
- **6**: `1.5rem` (24px) - Large spacing
- **8**: `2rem` (32px) - Extra large spacing
- **10**: `2.5rem` (40px) - 2X large spacing
- **12**: `3rem` (48px) - 3X large spacing
- **16**: `4rem` (64px) - 4X large spacing
- **20**: `5rem` (80px) - 5X large spacing
- **24**: `6rem` (96px) - 6X large spacing
- **32**: `8rem` (128px) - 8X large spacing

## Border Radius

Minimal border radius for sharp, brutalist edges:

- **None**: `0` - No border radius for sharp edges
- **SM**: `0.125rem` (2px) - Small border radius
- **Base**: `0.25rem` (4px) - Base border radius
- **MD**: `0.375rem` (6px) - Medium border radius
- **LG**: `0.5rem` (8px) - Large border radius
- **XL**: `0.75rem` (12px) - Extra large border radius

## Shadows

Brutalist shadows with hard edges and strong contrast:

- **SM**: `0 1px 2px 0 rgba(0, 0, 0, 0.05)` - Small subtle shadow
- **Base**: `0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)` - Base shadow
- **MD**: `0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)` - Medium shadow
- **LG**: `0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)` - Large shadow
- **Brutal**: `4px 4px 0px 0px #000000` - Signature brutalist shadow
- **Brutal LG**: `8px 8px 0px 0px #000000` - Large brutalist shadow
- **Brutal SM**: `2px 2px 0px 0px #000000` - Small brutalist shadow

## Implementation

### CSS Custom Properties

All design tokens are available as CSS custom properties in the `design-system.css` file. You can use them directly in your components:

```css
.my-component {
  background-color: var(--color-orange);
  color: var(--color-white);
  padding: var(--spacing-4);
  border-radius: var(--border-radius-base);
  box-shadow: var(--shadow-brutal);
  font-family: var(--font-family-primary);
  font-size: var(--font-size-base);
}
```

### Mantine Theme

The design system is implemented as a Mantine theme in the `glassmorphic-theme-provider.tsx` file. The theme provider should wrap your entire application:

```tsx
// In your root layout or _app.tsx
import { GlassmorphicThemeProvider } from '@/providers/glassmorphic-theme-provider';

export default function App({ Component, pageProps }: AppProps) {
  return (
    <GlassmorphicThemeProvider>
      <Component {...pageProps} />
    </GlassmorphicThemeProvider>
  );
}
```

### Component Usage

#### Buttons
```tsx
import { Button } from '@mantine/core';

function MyComponent() {
  return (
    <Button 
      variant="filled" 
      color="orange"
      size="md"
    >
      Brutalist Button
    </Button>
  );
}
```

#### Cards
```tsx
import { Card, Text } from '@mantine/core';

function MyComponent() {
  return (
    <Card 
      shadow="brutal"
      radius="sm"
      withBorder
    >
      <Text>Brutalist Card</Text>
    </Card>
  );
}
```

## Usage Guidelines

### Do
- Use black borders on all cards and components
- Apply brutalist shadows for depth
- Use orange for primary actions and branding
- Maintain high contrast ratios
- Use consistent spacing from the grid system
- Apply sharp, minimal border radius

### Don't
- Use excessive border radius
- Mix different shadow styles
- Use low contrast color combinations
- Overuse the orange accent color
- Use decorative elements without purpose
- Ignore accessibility guidelines

## Accessibility

The design system follows WCAG 2.1 AA standards with a minimum contrast ratio of 4.5:1 for normal text and 3:1 for large text. Focus states are clearly defined with a 2px solid orange outline and 2px offset.

## Component Library

The component library includes:
- Buttons with brutalist styling
- Cards with brutalist shadows
- Inputs with high-contrast borders
- Navigation with clear hierarchy
- All components follow the brutalist design principles

## Breakpoints

- **SM**: `640px` - Small screens and up
- **MD**: `768px` - Medium screens and up
- **LG**: `1024px` - Large screens and up
- **XL**: `1280px` - Extra large screens and up
- **2XL**: `1536px` - 2X large screens and up

## Animations

- **Fade In**: Opacity transition over 0.3s with ease-out easing
- **Slide Up**: TranslateY transition over 0.3s with ease-out easing
- **Slide Down**: TranslateY transition over 0.3s with ease-out easing
- **Scale In**: Scale transition over 0.2s with ease-out easing

## Conclusion

The Fairmind Design System provides a consistent, accessible, and professional brutalist aesthetic for the AI Governance Platform. By following these guidelines and using the provided components and tokens, you can create a cohesive user experience that aligns with the brand and design principles.