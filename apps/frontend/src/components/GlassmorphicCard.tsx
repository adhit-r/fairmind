import React from 'react';
import { Card, CardProps } from '@mantine/core';
import { glassmorphicUtils } from '../lib/mantine';

interface GlassmorphicCardProps extends Omit<CardProps, 'style'> {
  variant?: 'elevated' | 'floating' | 'subtle' | 'interactive';
  intensity?: 'light' | 'medium' | 'strong';
  glowColor?: string;
  interactive?: boolean;
  animated?: boolean;
  style?: React.CSSProperties;
}

export const GlassmorphicCard: React.FC<GlassmorphicCardProps> = ({
  variant = 'elevated',
  intensity = 'medium',
  glowColor,
  interactive = false,
  animated = true,
  children,
  style = {},
  ...props
}) => {
  const getVariantStyles = () => {
    const baseStyle = glassmorphicUtils.createGlassmorphicStyle(intensity, {
      interactive,
      borderRadius: '16px'
    });

    switch (variant) {
      case 'floating':
        return {
          ...baseStyle,
          transform: 'translateY(-4px)',
          boxShadow: glassmorphicUtils.getShadow('strong'),
        };

      case 'subtle':
        return glassmorphicUtils.createGlassmorphicStyle('light', {
          interactive,
          borderRadius: '12px'
        });

      case 'interactive':
        return glassmorphicUtils.createGlassmorphicStyle(intensity, {
          interactive: true,
          hover: true,
          borderRadius: '16px'
        });

      case 'elevated':
      default:
        return baseStyle;
    }
  };

  const getGlowStyles = () => {
    if (!glowColor) return {};
    
    return {
      '&:hover': {
        boxShadow: `0 0 20px ${glowColor}40, ${glassmorphicUtils.getShadow('strong')}`,
      },
    };
  };

  const getAnimationStyles = () => {
    if (!animated) return {};
    
    return {
      transition: glassmorphicUtils.getTransition('smooth'),
    };
  };

  const combinedStyles = {
    ...getVariantStyles(),
    ...getGlowStyles(),
    ...getAnimationStyles(),
    ...style,
  };

  return (
    <Card
      style={combinedStyles}
      radius="md"
      p="lg"
      {...props}
    >
      {children}
    </Card>
  );
};

export default GlassmorphicCard;