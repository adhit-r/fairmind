'use client';

import { DesignSystemDemo } from '@/components/demo/DesignSystemDemo';
import { GlassmorphicCard } from '@/components/GlassmorphicCard';
import { Title, Text, Container, Stack } from '@mantine/core';

export default function DesignSystemPage() {
  return (
    <Container size="lg" py="xl">
      <GlassmorphicCard>
        <Stack gap="xl">
          <Title order={1}>Fairmind Design System</Title>
          <Text size="lg">
            Implementation of the New Brutalist Professional design philosophy
          </Text>
          
          <DesignSystemDemo />
          
          <Stack gap="md" mt="xl">
            <Title order={2}>Design Principles</Title>
            <Text>
              The Fairmind Design System follows the "New Brutalist Professional" design philosophy, 
              which combines brutalist design principles with professional polish and enterprise-grade aesthetics.
            </Text>
            
            <Title order={3} mt="md">Key Principles</Title>
            <Text>
              1. <strong>High contrast for accessibility</strong> - Ensuring all text and UI elements 
              meet WCAG 2.1 AA standards
            </Text>
            <Text>
              2. <strong>Minimal border radius for sharp edges</strong> - Creating a distinctive 
              brutalist aesthetic with sharp, clean lines
            </Text>
            <Text>
              3. <strong>Bold typography with clear hierarchy</strong> - Using Space Grotesk for 
              headings and Inter for body text
            </Text>
            <Text>
              4. <strong>Consistent orange accent branding</strong> - Using #ff6b35 as the primary 
              accent color for actions and highlights
            </Text>
            <Text>
              5. <strong>Professional appearance without unnecessary decoration</strong> - 
              Focusing on functionality and clarity
            </Text>
            <Text>
              6. <strong>Functional over decorative design</strong> - Every design element serves 
              a purpose and enhances usability
            </Text>
          </Stack>
        </Stack>
      </GlassmorphicCard>
    </Container>
  );
}