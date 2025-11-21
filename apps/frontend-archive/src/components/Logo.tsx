'use client';

import { Group, Text } from '@mantine/core';

interface LogoProps {
  size?: 'sm' | 'md' | 'lg';
}

export function Logo({ size = 'md' }: LogoProps) {
  const sizeMap = {
    sm: { text: 'sm' },
    md: { text: 'md' },
    lg: { text: 'lg' },
  };

  const currentSize = sizeMap[size];

  return (
    <Group gap={6} align="center">
      <Text 
        fw={700} 
        size={currentSize.text} 
        c="var(--color-orange)"
        style={{
          letterSpacing: '-0.02em',
          fontFamily: 'var(--font-family-display)',
        }}
      >
        FairMind
      </Text>
    </Group>
  );
}