'use client';

import {
  Group,
  Button,
  Text,
  Box,
  Container,
  ThemeIcon,
  Paper,
} from '@mantine/core';
import { IconBrain, IconUser, IconSettings } from '@tabler/icons-react';

export function Header() {
  return (
    <Paper bg="white" py="md" withBorder>
      <Container size="lg">
        <Group justify="space-between">
          {/* Logo */}
          <Group>
            <ThemeIcon size="lg" radius="md" color="blue">
              <IconBrain size="1.5rem" />
            </ThemeIcon>
            <Text fw={600} size="lg" c="dark.8">
              FairMind
            </Text>
          </Group>

          {/* Navigation */}
          <Group gap="md">
            <Button variant="subtle" size="sm">
              Dashboard
            </Button>
            <Button variant="subtle" size="sm">
              Models
            </Button>
            <Button variant="subtle" size="sm">
              Analytics
            </Button>
            <Button variant="subtle" size="sm">
              Compliance
            </Button>
          </Group>

          {/* User Actions */}
          <Group gap="sm">
            <Button variant="subtle" size="sm" leftSection={<IconSettings size="1rem" />}>
              Settings
            </Button>
            <Button variant="outline" size="sm" leftSection={<IconUser size="1rem" />}>
              Profile
            </Button>
          </Group>
        </Group>
      </Container>
    </Paper>
  );
}
