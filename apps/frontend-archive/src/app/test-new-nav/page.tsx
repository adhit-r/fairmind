'use client';

import { Title, Text, Container, Box } from '@mantine/core';

export default function TestNewNavPage() {
  return (
    <Container size="lg" py="xl">
      <Title order={1} mb="md">New Navigation Test</Title>
      <Text mb="xl">
        This page tests the redesigned side navigation bar with orange buttons and proper text color.
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
        <Title order={2} mb="sm">Navigation Redesign Verification</Title>
        <Text>
          The side navigation bar should now feature:
        </Text>
        <Text mt="sm">
          • Orange buttons with proper text color
        </Text>
        <Text mt="sm">
          • No blue or purple gradients
        </Text>
        <Text mt="sm">
          • Brutalist design with sharp edges and black borders
        </Text>
        <Text mt="sm">
          • Orange accent color for active and hover states
        </Text>
      </Box>
    </Container>
  );
}