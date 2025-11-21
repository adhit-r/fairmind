'use client';

import { Button, Group, Stack, Title, Text, Card, Input } from '@mantine/core';

export default function TestDesignSystemPage() {
  return (
    <Stack p="xl" gap="xl">
      <Title>Design System Test Page</Title>
      
      <Card withBorder shadow="brutal" p="lg">
        <Title order={2} mb="md">Button Variants</Title>
        
        <Stack gap="md">
          <Group>
            <Button variant="filled">Primary Button</Button>
            <Button variant="outline">Secondary Button</Button>
            <Button color="orange">Accent Button</Button>
          </Group>
          
          <Group>
            <Button size="xs">XS Button</Button>
            <Button size="sm">SM Button</Button>
            <Button size="md">MD Button</Button>
            <Button size="lg">LG Button</Button>
            <Button size="xl">XL Button</Button>
          </Group>
        </Stack>
      </Card>
      
      <Card withBorder shadow="brutal" p="lg">
        <Title order={2} mb="md">Input Fields</Title>
        
        <Stack gap="md">
          <Input placeholder="Default input" />
          <Input placeholder="Input with value" defaultValue="Sample value" />
        </Stack>
      </Card>
      
      <Card withBorder shadow="brutal" p="lg">
        <Title order={2} mb="md">Card Components</Title>
        
        <Stack gap="md">
          <Card withBorder shadow="brutal">
            <Title order={3} mb="sm">Sample Card</Title>
            <Text>This is a sample card with brutalist design.</Text>
            <Group mt="md">
              <Button variant="outline" size="sm">Action</Button>
            </Group>
          </Card>
        </Stack>
      </Card>
    </Stack>
  );
}