'use client';

import { 
  Card, 
  Button, 
  Input, 
  Title, 
  Text, 
  Group, 
  Stack, 
  Badge,
  Divider,
  Box
} from '@mantine/core';
import { useDesignSystem } from '@/hooks/use-design-system';

export function DesignSystemDemo() {
  const designSystem = useDesignSystem();
  
  return (
    <Stack gap="xl" p="xl">
      <Title order={1} style={{ fontFamily: designSystem.typography.fontFamilies.display }}>
        Fairmind Design System
      </Title>
      
      <Text size="lg" c="dimmed">
        Implementation of the New Brutalist Professional design philosophy
      </Text>
      
      <Divider my="md" />
      
      {/* Color Palette Showcase */}
      <Card withBorder shadow="brutal">
        <Title order={2} mb="md">Color Palette</Title>
        
        <Stack gap="md">
          <Group>
            <Badge color="black" size="lg">Black: {designSystem.colors.primary.black}</Badge>
            <Badge color="gray" size="lg">White: {designSystem.colors.primary.white}</Badge>
          </Group>
          
          <Group>
            <Badge color="orange" size="lg">Orange: {designSystem.colors.accent.orange}</Badge>
            <Badge color="orange" variant="light" size="lg">Orange Dark: {designSystem.colors.accent.orangeDark}</Badge>
            <Badge color="orange" variant="outline" size="lg">Orange Light: {designSystem.colors.accent.orangeLight}</Badge>
          </Group>
          
          <Group>
            <Badge color="green" size="lg">Success: {designSystem.colors.semantic.success}</Badge>
            <Badge color="yellow" size="lg">Warning: {designSystem.colors.semantic.warning}</Badge>
            <Badge color="red" size="lg">Error: {designSystem.colors.semantic.error}</Badge>
            <Badge color="blue" size="lg">Info: {designSystem.colors.semantic.info}</Badge>
          </Group>
        </Stack>
      </Card>
      
      {/* Typography Showcase */}
      <Card withBorder shadow="brutal">
        <Title order={2} mb="md">Typography</Title>
        
        <Stack gap="md">
          <Title order={1} style={{ fontFamily: designSystem.typography.fontFamilies.display }}>
            Heading 1 - Space Grotesk
          </Title>
          <Title order={2} style={{ fontFamily: designSystem.typography.fontFamilies.display }}>
            Heading 2 - Space Grotesk
          </Title>
          <Title order={3} style={{ fontFamily: designSystem.typography.fontFamilies.display }}>
            Heading 3 - Space Grotesk
          </Title>
          <Text size="lg">
            Body Text - Inter (This is the primary font for body text and UI elements)
          </Text>
          <Text size="sm" c="dimmed">
            Secondary Text - Inter (Used for captions, fine print, and labels)
          </Text>
        </Stack>
      </Card>
      
      {/* Component Showcase */}
      <Card withBorder shadow="brutal">
        <Title order={2} mb="md">Brutalist Components</Title>
        
        <Stack gap="xl">
          {/* Buttons */}
          <Stack gap="md">
            <Title order={3}>Buttons</Title>
            <Group>
              <Button variant="filled">Primary</Button>
              <Button variant="outline">Secondary</Button>
              <Button color="orange">Accent</Button>
            </Group>
            
            {/* Button sizes */}
            <Group mt="md">
              <Button size="xs">XS Button</Button>
              <Button size="sm">SM Button</Button>
              <Button size="md">MD Button</Button>
              <Button size="lg">LG Button</Button>
              <Button size="xl">XL Button</Button>
            </Group>
          </Stack>
          
          {/* Inputs */}
          <Stack gap="md">
            <Title order={3}>Inputs</Title>
            <Input placeholder="Brutalist input" />
            <Input placeholder="With value" defaultValue="Input value" />
          </Stack>
          
          {/* Cards */}
          <Stack gap="md">
            <Title order={3}>Cards</Title>
            <Group>
              <Card withBorder shadow="brutal" style={{ maxWidth: 300 }}>
                <Title order={4} mb="sm">Brutalist Card</Title>
                <Text size="sm">
                  This card follows the brutalist design principles with sharp edges and strong shadows.
                </Text>
                <Group mt="md">
                  <Button variant="outline" size="xs">Action</Button>
                </Group>
              </Card>
            </Group>
          </Stack>
        </Stack>
      </Card>
      
      {/* Spacing System */}
      <Card withBorder shadow="brutal">
        <Title order={2} mb="md">Spacing System</Title>
        
        <Stack gap="md">
          <Text>
            The spacing system follows a "Brutalist Grid System" with a base unit of 0.25rem (4px)
          </Text>
          
          <Group>
            <Badge>1: {designSystem.spacing.values[1]} (4px)</Badge>
            <Badge>2: {designSystem.spacing.values[2]} (8px)</Badge>
            <Badge>4: {designSystem.spacing.values[4]} (16px)</Badge>
            <Badge>8: {designSystem.spacing.values[8]} (32px)</Badge>
          </Group>
        </Stack>
      </Card>
      
      {/* Border Radius */}
      <Card withBorder shadow="brutal">
        <Title order={2} mb="md">Border Radius</Title>
        
        <Stack gap="md">
          <Text>
            Minimal border radius for sharp, brutalist edges
          </Text>
          
          <Group>
            <Box style={{ 
              width: 50, 
              height: 50, 
              border: '2px solid #000000',
              borderRadius: designSystem.borderRadius.values.none
            }} />
            <Box style={{ 
              width: 50, 
              height: 50, 
              border: '2px solid #000000',
              borderRadius: designSystem.borderRadius.values.sm
            }} />
            <Box style={{ 
              width: 50, 
              height: 50, 
              border: '2px solid #000000',
              borderRadius: designSystem.borderRadius.values.base
            }} />
            <Box style={{ 
              width: 50, 
              height: 50, 
              border: '2px solid #000000',
              borderRadius: designSystem.borderRadius.values.md
            }} />
          </Group>
        </Stack>
      </Card>
      
      {/* Shadows */}
      <Card withBorder shadow="brutal">
        <Title order={2} mb="md">Shadows</Title>
        
        <Stack gap="md">
          <Text>
            Brutalist shadows with hard edges and strong contrast
          </Text>
          
          <Group>
            <Box style={{ 
              width: 100, 
              height: 100, 
              border: '2px solid #000000',
              boxShadow: designSystem.shadows.values.brutal,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Text size="xs">Brutal</Text>
            </Box>
            <Box style={{ 
              width: 100, 
              height: 100, 
              border: '2px solid #000000',
              boxShadow: designSystem.shadows.values.brutalLg,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Text size="xs">Brutal LG</Text>
            </Box>
            <Box style={{ 
              width: 100, 
              height: 100, 
              border: '2px solid #000000',
              boxShadow: designSystem.shadows.values.brutalSm,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Text size="xs">Brutal SM</Text>
            </Box>
          </Group>
        </Stack>
      </Card>
    </Stack>
  );
}