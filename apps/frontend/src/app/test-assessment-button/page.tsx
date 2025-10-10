'use client';

import { Title, Text, Container, Box } from '@mantine/core';

export default function TestAssessmentButtonPage() {
  return (
    <Container size="lg" py="xl">
      <Title order={1} mb="md">New Assessment Button Test</Title>
      <Text mb="xl">
        This page tests the "New Assessment" button in the side navigation bar to ensure it follows the design system.
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
        <Title order={2} mb="sm">Button Design Verification</Title>
        <Text>
          The "New Assessment" button should now feature:
        </Text>
        <Text mt="sm">
          • Orange background with white text
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
          • Plus icon with proper styling
        </Text>
        <Text mt="sm">
          • Hover effect with darker orange and elevated shadow
        </Text>
      </Box>
    </Container>
  );
}