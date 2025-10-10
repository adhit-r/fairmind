'use client';

import {
  Container,
  Title,
  Text,
  Button,
  Card,
  Group,
  Stack,
  SimpleGrid,
  Badge,
  Table,
  ActionIcon,
  ThemeIcon,
  Tabs,
} from '@mantine/core';
import {
  IconTrendingUp,
  IconTarget,
  IconCpu,
  IconShield,
  IconEye,
  IconDownload,
  IconRefresh,
  IconChartBar,
  IconPlaylist,
} from '@tabler/icons-react';
import { useApi } from '@/hooks/useApi';

const neo = {
  card: {
    background: 'rgba(255, 255, 255, 0.9)',
    backdropFilter: 'blur(20px)',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '20px',
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
  },
};

const benchmarkSuites = [
  {
    id: 1,
    name: 'Performance Benchmark Suite',
    description: 'Comprehensive performance testing across multiple model types',
    type: 'Performance',
    models: 24,
    lastRun: '2024-01-20',
    status: 'completed',
    avgScore: 87.5,
  },
  {
    id: 2,
    name: 'Fairness Assessment Battery',
    description: 'Bias and fairness evaluation across protected attributes',
    type: 'Fairness',
    models: 18,
    lastRun: '2024-01-22',
    status: 'running',
    avgScore: 82.3,
  },
  {
    id: 3,
    name: 'Security Vulnerability Tests',
    description: 'Adversarial attacks and security robustness testing',
    type: 'Security',
    models: 15,
    lastRun: '2024-01-19',
    status: 'completed',
    avgScore: 91.2,
  },
];

const benchmarkStats = [
  {
    title: 'Total Benchmarks',
    value: '156',
    icon: IconPlaylist,
    color: 'blue',
  },
  {
    title: 'Models Tested',
    value: '47',
    icon: IconCpu,
    color: 'green',
  },
  {
    title: 'Avg Performance',
    value: '87.2%',
    icon: IconTrendingUp,
    color: 'cyan',
  },
  {
    title: 'Running Tests',
    value: '8',
    icon: IconTarget,
    color: 'orange',
  },
];

export default function BenchmarksPage() {
  const { data: benchmarksData, loading, error } = useApi('/api/v1/benchmarks');

  return (
    <Container size="xl" py="xl">
      <Stack gap="xl">
        {/* Header */}
        <Card style={neo.card} p="xl">
          <Group justify="space-between" align="center">
            <div>
              <Title order={1} size="2rem" fw={700} c="#1e293b" mb="xs">
                AI Model Benchmarks
              </Title>
              <Text c="dimmed" size="lg">
                Comprehensive benchmarking and performance evaluation
              </Text>
            </div>
            <Group gap="sm">
              <ActionIcon size="lg" radius="xl" variant="light" color="blue">
                <IconRefresh size={20} />
              </ActionIcon>
              <Button
                leftSection={<IconTarget size={16} />}
                radius="xl"
                style={{
                  background: 'linear-gradient(145deg, #059669, #047857)',
                  boxShadow: '6px 6px 12px rgba(5, 150, 105, 0.4), -4px -4px 8px rgba(16, 185, 129, 0.4)',
                }}
              >
                Run Benchmark
              </Button>
            </Group>
          </Group>
        </Card>

        {/* Statistics */}
        <SimpleGrid cols={{ base: 2, md: 4 }} spacing="lg">
          {benchmarkStats.map((stat) => (
            <Card key={stat.title} style={neo.card} p="lg">
              <Stack gap="sm">
                <ThemeIcon size="lg" radius="xl" color={stat.color} variant="light">
                  <stat.icon size={20} />
                </ThemeIcon>
                <div>
                  <Text size="2xl" fw={700} c="#1e293b">
                    {stat.value}
                  </Text>
                  <Text size="sm" c="dimmed">
                    {stat.title}
                  </Text>
                </div>
              </Stack>
            </Card>
          ))}
        </SimpleGrid>

        {/* Benchmark Suites */}
        <Tabs defaultValue="suites">
          <Tabs.List>
            <Tabs.Tab value="suites">Benchmark Suites</Tabs.Tab>
            <Tabs.Tab value="performance">Performance Tests</Tabs.Tab>
            <Tabs.Tab value="fairness">Fairness Benchmarks</Tabs.Tab>
            <Tabs.Tab value="custom">Custom Benchmarks</Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="suites" pt="xl">
            <SimpleGrid cols={{ base: 1, md: 2, lg: 3 }} spacing="lg">
              {benchmarkSuites.map((suite) => (
                <Card key={suite.id} style={neo.card} p="xl">
                  <Stack gap="md">
                    <Group justify="space-between">
                      <ThemeIcon size="lg" radius="xl" color="blue" variant="light">
                        <IconChartBar size={20} />
                      </ThemeIcon>
                      <Badge color={suite.status === 'completed' ? 'green' : 'blue'} variant="light">
                        {suite.status}
                      </Badge>
                    </Group>
                    <div>
                      <Title order={3} size="lg" fw={600}>
                        {suite.name}
                      </Title>
                      <Text size="sm" c="dimmed" lineClamp={2}>
                        {suite.description}
                      </Text>
                    </div>
                    <Group justify="space-between">
                      <div>
                        <Text size="xs" c="dimmed">Models</Text>
                        <Text size="sm" fw={600}>{suite.models}</Text>
                      </div>
                      <div>
                        <Text size="xs" c="dimmed">Avg Score</Text>
                        <Text size="sm" fw={600}>{suite.avgScore}%</Text>
                      </div>
                    </Group>
                    <Badge size="sm" variant="light" color="gray">
                      {suite.type}
                    </Badge>
                  </Stack>
                </Card>
              ))}
            </SimpleGrid>
          </Tabs.Panel>

          <Tabs.Panel value="performance" pt="xl">
            <Card style={neo.card} p="xl">
              <Stack align="center" gap="md" py="xl">
                <IconTrendingUp size={64} color="#cbd5e1" />
                <Title order={3} c="dimmed">Performance Benchmarks</Title>
                <Text c="dimmed" ta="center">
                  Comprehensive performance testing and optimization insights
                </Text>
                <Button leftSection={<IconEye size={16} />}>
                  View Performance Tests
                </Button>
              </Stack>
            </Card>
          </Tabs.Panel>

          <Tabs.Panel value="fairness" pt="xl">
            <Card style={neo.card} p="xl">
              <Stack align="center" gap="md" py="xl">
                <IconShield size={64} color="#cbd5e1" />
                <Title order={3} c="dimmed">Fairness Benchmarks</Title>
                <Text c="dimmed" ta="center">
                  Bias detection and fairness evaluation benchmarks
                </Text>
                <Button leftSection={<IconEye size={16} />}>
                  View Fairness Tests
                </Button>
              </Stack>
            </Card>
          </Tabs.Panel>

          <Tabs.Panel value="custom" pt="xl">
            <Card style={neo.card} p="xl">
              <Stack align="center" gap="md" py="xl">
                <IconTarget size={64} color="#cbd5e1" />
                <Title order={3} c="dimmed">Custom Benchmarks</Title>
                <Text c="dimmed" ta="center">
                  Create and manage custom benchmark suites
                </Text>
                <Button leftSection={<IconTarget size={16} />}>
                  Create Benchmark
                </Button>
              </Stack>
            </Card>
          </Tabs.Panel>
        </Tabs>
      </Stack>
    </Container>
  );
}