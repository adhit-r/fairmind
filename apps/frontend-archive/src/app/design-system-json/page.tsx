'use client';

import { Title, Text, Container, Box, Code, ScrollArea } from '@mantine/core';
import designSystemData from '@/data/design-system.json';

export default function DesignSystemJsonPage() {
  return (
    <Container size="lg" py="xl">
      <Title order={1} mb="md">Design System JSON</Title>
      <Text mb="xl">
        This page displays the Fairmind Design System configuration in JSON format.
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
        <Title order={2} mb="sm">Design System Configuration</Title>
        <Text mb="sm">
          The design system is configured with the following JSON structure:
        </Text>
        
        <ScrollArea h={400}>
          <Code block>
            {JSON.stringify(designSystemData, null, 2)}
          </Code>
        </ScrollArea>
      </Box>
    </Container>
  );
}