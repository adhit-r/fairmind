'use client';

import { Title, Text, Container, Box, Group } from '@mantine/core';
import { OrangeLogo } from '@/components/OrangeLogo';

export default function TestOrangeLogoPage() {
  return (
    <Container size="lg" py="xl">
      <Title order={1} mb="md">Orange SVG Logo Test</Title>
      <Text mb="xl">
        This page tests the new orange SVG logo implementation that follows the brutalist design system.
      </Text>
      
      <Box 
        p="md" 
        style={{
          border: '2px solid var(--color-black)',
          borderRadius: 'var(--border-radius-none)',
          boxShadow: 'var(--shadow-brutal)',
          background: 'var(--color-white)',
        }}
      >
        <Title order={2} mb="sm">Logo Design Verification</Title>
        <Text mb="sm">
          The new orange SVG logo should feature:
        </Text>
        
        <Group mb="sm">
          <OrangeLogo size="lg" />
          <Text>Large size orange logo</Text>
        </Group>
        
        <Group mb="sm">
          <OrangeLogo size="md" />
          <Text>Medium size orange logo</Text>
        </Group>
        
        <Group mb="sm">
          <OrangeLogo size="sm" />
          <Text>Small size orange logo</Text>
        </Group>
        
        <Text mt="sm">
          Each logo should have:
        </Text>
        <Text mt="sm">
          • Orange background with black "F" shape
        </Text>
        <Text mt="sm">
          • Black border following brutalist design
        </Text>
        <Text mt="sm">
          • Sharp edges (no border-radius)
        </Text>
        <Text mt="sm">
          • Brutalist shadow effect
        </Text>
        <Text mt="sm">
          • Abstract "F" shape representing FairMind
        </Text>
      </Box>
    </Container>
  );
}