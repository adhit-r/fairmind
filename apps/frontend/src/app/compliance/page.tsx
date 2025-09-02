'use client';

import {
  Container,
  Title,
  Text,
  Card,
  SimpleGrid,
  Stack,
  Group,
  Button,
  Badge,
  ThemeIcon,
  Box,
  Progress,
  RingProgress,
  Tabs,
  Alert,
  Table,
  ActionIcon,
} from '@mantine/core';
import {
  IconShield,
  IconTarget,
  IconClock,
  IconCertificate,
  IconDownload,
  IconPlus,
  IconEye,
  IconAlertTriangle,
} from '@tabler/icons-react';
import { useState } from 'react';

export default function CompliancePage() {
  const [selectedFramework, setSelectedFramework] = useState<string | null>(null);

  return (
    <Container size="xl" py="xl">
      <Stack spacing="xl">
        {/* Header */}
        <Group position="apart">
          <Box>
            <Title order={1}>Compliance & Governance</Title>
            <Text color="dimmed" size="sm">
              Manage regulatory compliance and governance frameworks for AI systems
            </Text>
          </Box>
          <Group>
            <Button leftIcon={<IconDownload size={16} />} variant="outline">
              Export Report
            </Button>
            <Button leftIcon={<IconPlus size={16} />}>
              Add Framework
            </Button>
          </Group>
        </Group>

        {/* Compliance Overview */}
        <SimpleGrid cols={4} spacing="lg">
          <Card withBorder>
            <Group position="apart">
              <Box>
                <Text size="xs" color="dimmed" transform="uppercase">
                  Overall Compliance
                </Text>
                <Text size="xl" weight={700}>
                  88%
                </Text>
              </Box>
              <ThemeIcon size="xl" radius="md" color="blue">
                <IconShield size={24} />
              </ThemeIcon>
            </Group>
            <Progress value={88} color="blue" size="sm" mt="md" />
          </Card>

          <Card withBorder>
            <Group position="apart">
              <Box>
                <Text size="xs" color="dimmed" transform="uppercase">
                  Active Frameworks
                </Text>
                <Text size="xl" weight={700}>
                  4
                </Text>
              </Box>
              <ThemeIcon size="xl" radius="md" color="green">
                <IconTarget size={24} />
              </ThemeIcon>
            </Group>
            <Text size="sm" color="dimmed" mt="md">
              All frameworks active
            </Text>
          </Card>

          <Card withBorder>
            <Group position="apart">
              <Box>
                <Text size="xs" color="dimmed" transform="uppercase">
                  Upcoming Deadlines
                </Text>
                <Text size="xl" weight={700}>
                  2
                </Text>
              </Box>
              <ThemeIcon size="xl" radius="md" color="orange">
                <IconClock size={24} />
              </ThemeIcon>
            </Group>
            <Text size="sm" color="dimmed" mt="md">
              Within 60 days
            </Text>
          </Card>

          <Card withBorder>
            <Group position="apart">
              <Box>
                <Text size="xs" color="dimmed" transform="uppercase">
                  Audit Score
                </Text>
                <Text size="xl" weight={700}>
                  91.3
                </Text>
              </Box>
              <ThemeIcon size="xl" radius="md" color="green">
                <IconCertificate size={24} />
              </ThemeIcon>
            </Group>
            <Text size="sm" color="dimmed" mt="md">
              Average across audits
            </Text>
          </Card>
        </SimpleGrid>

        {/* Quick Actions */}
        <Card withBorder>
          <Title order={3} mb="md">Quick Actions</Title>
          <Group>
            <Button leftIcon={<IconPlus size={16} />} variant="outline">
              Schedule Audit
            </Button>
            <Button leftIcon={<IconDownload size={16} />} variant="outline">
              Generate Report
            </Button>
            <Button leftIcon={<IconTarget size={16} />} variant="outline">
              Set Goals
            </Button>
            <Button leftIcon={<IconEye size={16} />} variant="outline">
              View Details
            </Button>
          </Group>
        </Card>
      </Stack>
    </Container>
  );
}
