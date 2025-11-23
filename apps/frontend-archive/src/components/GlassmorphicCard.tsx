import React from 'react';
import { Card, CardProps } from '@mantine/core';
import { glassmorphicUtils } from '../lib/mantine';

interface GlassmorphicCardProps extends CardProps {
  variant?: 'elevated' | 'floating' | 'subtle' | 'interactive';
  intensity?: 'light' | 'medium' | 'strong';
  glowColor?: string;
  interactive?: boolean;
  animated?: boolean;
}

export const GlassmorphicCard: React.FC<GlassmorphicCardProps> = ({
  variant = 'elevated',
  intensity = 'medium',
  glowColor,
  interactive = false,
  animated = true,
  children,
  style,
  ...props
}) => {
  const getVariantStyles = (): React.CSSProperties => {
    const baseStyle: React.CSSProperties = {
      background: glassmorphicUtils.getBackground(intensity),
      backdropFilter: glassmorphicUtils.getBlur(intensity),
      border: glassmorphicUtils.getBorder(intensity),
      boxShadow: glassmorphicUtils.getShadow(intensity),
      borderRadius: '16px',
      transition: glassmorphicUtils.getTransition('smooth'),
      ...(interactive && {
        cursor: 'pointer',
      }),
    };

    switch (variant) {
      case 'floating':
        return {
          ...baseStyle,
          transform: 'translateY(-4px)',
          boxShadow: glassmorphicUtils.getShadow('strong'),
        };

      case 'subtle':
        return {
          background: glassmorphicUtils.getBackground('light'),
          backdropFilter: glassmorphicUtils.getBlur('light'),
          border: glassmorphicUtils.getBorder('light'),
          boxShadow: glassmorphicUtils.getShadow('light'),
          borderRadius: '12px',
          transition: glassmorphicUtils.getTransition('smooth'),
          ...(interactive && {
            cursor: 'pointer',
          }),
        };

      case 'interactive':
        return {
          ...baseStyle,
          cursor: 'pointer',
        };

      case 'elevated':
      default:
        return baseStyle;
    }
  };

  const baseStyles = getVariantStyles();

  return (
    <Card
      style={{
        ...baseStyles,
        ...style,
      }}
      onMouseEnter={interactive ? (e) => {
        const target = e.currentTarget;
        target.style.background = glassmorphicUtils.getBackground('strong');
        target.style.boxShadow = glassmorphicUtils.getShadow('strong');
        target.style.transform = 'translateY(-2px)';
        if (glowColor) {
          target.style.boxShadow = `0 0 20px ${glowColor}40, ${glassmorphicUtils.getShadow('strong')}`;
        }
      } : undefined}
      onMouseLeave={interactive ? (e) => {
        const target = e.currentTarget;
        target.style.background = baseStyles.background as string;
        target.style.boxShadow = baseStyles.boxShadow as string;
        target.style.transform = variant === 'floating' ? 'translateY(-4px)' : 'translateY(0)';
      } : undefined}
      onMouseDown={interactive ? (e) => {
        e.currentTarget.style.transform = 'translateY(0)';
      } : undefined}
      onMouseUp={interactive ? (e) => {
        e.currentTarget.style.transform = 'translateY(-2px)';
      } : undefined}
      radius="md"
      p="lg"
      {...props}
    >
      {children}
    </Card>
  );
};

export default GlassmorphicCard;