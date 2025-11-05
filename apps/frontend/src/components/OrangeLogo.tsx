'use client';

import { Group } from '@mantine/core';

interface OrangeLogoProps {
  size?: 'sm' | 'md' | 'lg';
}

export function OrangeLogo({ size = 'md' }: OrangeLogoProps) {
  const sizeMap = {
    sm: { width: 24, height: 24 },
    md: { width: 32, height: 32 },
    lg: { width: 48, height: 48 },
  };

  const dimensions = sizeMap[size];

  return (
    <Group gap={6} align="center">
      <svg
        width={dimensions.width}
        height={dimensions.height}
        viewBox="0 0 48 48"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{
          border: '2px solid var(--color-black)',
          borderRadius: 'var(--border-radius-none)',
          boxShadow: 'var(--shadow-brutal)',
        }}
      >
        {/* Background orange square with brutalist border */}
        <rect
          x="4"
          y="4"
          width="40"
          height="40"
          fill="var(--color-orange)"
          stroke="var(--color-black)"
          strokeWidth="2"
        />
        
        {/* Abstract "FM" design in black */}
        {/* F shape */}
        <path
          d="M12 12H36V16H20V20H32V24H20V28H36V32H12V12Z"
          fill="var(--color-black)"
        />
        
        {/* Diagonal accent line for brutalist effect */}
        <rect
          x="36"
          y="12"
          width="4"
          height="20"
          fill="var(--color-black)"
          transform="rotate(45 36 12)"
        />
      </svg>
    </Group>
  );
}