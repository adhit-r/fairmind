'use client';

import { Title, Text, Container, Box } from '@mantine/core';

export default function TestNavigationPage() {
  return (
    <Container size="lg" py="xl">
      <Title order={1} mb="md">Navigation Test Page</Title>
      <Text mb="xl">
        This page is used to test the navigation component and verify that it properly follows 
        the brutalist design system with the orange accent color.
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
        <Title order={2} mb="sm">Brutalist Design Test</Title>
        <Text>
          This box should have the brutalist design with sharp edges, black border, 
          and a brutal shadow effect.
        </Text>
      </Box>
    </Container>
  );
}