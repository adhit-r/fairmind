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
  Progress,
  Alert,
  Badge,
  ActionIcon,
  Tabs,
} from '@mantine/core';
import {
  IconTarget,
  IconPlus,
  IconAlertCircle,
  IconRocket,
  IconShield,
  IconEye,
  IconBrain,
  IconUsers,
} from '@tabler/icons-react';
import { useApi } from '@/hooks/useApi';

const neo = {
  card: {
    background: 'linear-gradient(145deg, rgba(255, 255, 255, 0.95), rgba(248, 250, 252, 0.9))',
    backdropFilter: 'blur(20px)',
    border: '1px solid rgba(255, 255, 255, 0.3)',
    borderRadius: '20px',
    boxShadow: '12px 12px 24px rgba(163, 177, 198, 0.4), -12px -12px 24px rgba(255, 255, 255, 0.9)',
  },
};

const biasTests = [
  {
    id: 'demographic',
    name: 'Demographic Bias',
    description: 'Test for unfair treatment across demographic groups',
    icon: IconUsers,
    status: 'ready',
    lastRun: '2 hours ago',
    score: 85,
  },
  {
    id: 'representational',
    name: 'Representational Bias',
    description: 'Analyze representation fairness in model outputs',
    icon: IconEye,
    status: 'running',
    lastRun: 'Running now',
    score: null,
  },
  {
    id: 'allocational',
    name: 'Allocational Bias',
    description: 'Check resource allocation fairness',
    icon: IconTarget,
    status: 'ready',
    lastRun: '1 day ago',
    score: 92,
  },
  {
    id: 'contextual',
    name: 'Contextual Bias',
    description: 'Context-dependent bias detection',
    icon: IconBrain,
    status: 'ready',
    lastRun: '3 hours ago',
    score: 78,
  },
];

function getScoreColor(score: number | null) {
  if (!score) return 'gray';
  if (score >= 90) return 'green';
  if (score >= 80) return 'blue';
  if (score >= 70) return 'yellow';
  return 'red';
}

export default function BiasPage() {
  const { data: biasData, loading, error } = useApi('/api/v1/bias/health');

  return (
    <Container size="xl" py="xl">
      <Stack gap="xl">
        {/* Header */}
        <Card style={neo.card} p="xl">
          <Group justify="space-between" align="center">
            <div>
              <Title order={1} size="2rem" fw={700} c="#1e293b" mb="xs">
                Bias Detection Suite
              </Title>
              <Text c="dimmed" size="lg">
                Comprehensive bias analysis across multiple dimensions
              </Text>
            </div>
            <Button
              size="lg"
              radius="xl"
              leftSection={<IconRocket size={20} />}
              style={{
                background: 'linear-gradient(145deg, #dc2626, #b91c1c)',
                boxShadow: '6px 6px 12px rgba(220, 38, 38, 0.4), -4px -4px 8px rgba(248, 113, 113, 0.4)',
              }}
            >
              Run Full Analysis
            </Button>
          </Group>
        </Card>

        {error && (
          <Alert
            icon={<IconAlertCircle size={16} />}
            color="red"
            title="Connection Error"
            style={neo.card}
          >
            Unable to connect to bias detection service: {error}
          </Alert>
        )}

        {/* Bias Test Categories */}
        <Tabs defaultValue="overview" radius="lg">
          <Tabs.List>
            <Tabs.Tab value="overview">Overview</Tabs.Tab>
            <Tabs.Tab value="text">Text Bias</Tabs.Tab>
            <Tabs.Tab value="image">Image Bias</Tabs.Tab>
            <Tabs.Tab value="multimodal">Multimodal</Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="overview" pt="xl">
            <SimpleGrid cols={{ base: 1, md: 2 }} spacing="lg">
              {biasTests.map((test) => (
                <Card
                  key={test.id}
                  style={{
                    ...neo.card,
                    cursor: 'pointer',
                    transition: 'all 0.3s ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-4px)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)';
                  }}
                  p="xl"
                >
                  <Stack gap="md">
                    <Group justify="space-between">
                      <Group gap="sm">
                        <ActionIcon
                          size="lg"
                          radius="xl"
                          variant="light"
                          color={getScoreColor(test.score)}
                        >
                          <test.icon size={20} />
                        </ActionIcon>
                        <div>
                          <Title order={3} size="lg" fw={600}>
                            {test.name}
                          </Title>
                          <Text size="sm" c="dimmed">
                            {test.description}
                          </Text>
                        </div>
                      </Group>
                      <Badge
                        color={test.status === 'running' ? 'blue' : 'green'}
                        variant="light"
                        radius="xl"
                      >
                        {test.status}
                      </Badge>
                    </Group>

                    {test.score !== null && (
                      <div>
                        <Group justify="space-between" mb="xs">
                          <Text size="sm" fw={500}>Fairness Score</Text>
                          <Text size="sm" fw={700} c={getScoreColor(test.score)}>
                            {test.score}%
                          </Text>
                        </Group>
                        <Progress
                          value={test.score}
                          size="md"
                          radius="xl"
                          color={getScoreColor(test.score)}
                        />
                      </div>
                    )}

                    <Group justify="space-between" mt="md">
                      <Text size="xs" c="dimmed">
                        Last run: {test.lastRun}
                      </Text>
                      <Button
                        size="xs"
                        variant="light"
                        radius="xl"
                        disabled={test.status === 'running'}
                      >
                        {test.status === 'running' ? 'Running...' : 'Run Test'}
                      </Button>
                    </Group>
                  </Stack>
                </Card>
              ))}
            </SimpleGrid>
          </Tabs.Panel>

          <Tabs.Panel value="text" pt="xl">
            <Card style={neo.card} p="xl">
              <Stack align="center" gap="md" py="xl">
                <IconBrain size={64} color="#cbd5e1" />
                <Title order={3} c="dimmed">Text Bias Detection</Title>
                <Text c="dimmed" ta="center">
                  Advanced NLP bias detection for text generation models
                </Text>
                <Button leftSection={<IconPlus size={16} />}>
                  Configure Text Analysis
                </Button>
              </Stack>
            </Card>
          </Tabs.Panel>

          <Tabs.Panel value="image" pt="xl">
            <Card style={neo.card} p="xl">
              <Stack align="center" gap="md" py="xl">
                <IconEye size={64} color="#cbd5e1" />
                <Title order={3} c="dimmed">Image Bias Detection</Title>
                <Text c="dimmed" ta="center">
                  Computer vision bias analysis for image generation models
                </Text>
                <Button leftSection={<IconPlus size={16} />}>
                  Configure Image Analysis
                </Button>
              </Stack>
            </Card>
          </Tabs.Panel>

          <Tabs.Panel value="multimodal" pt="xl">
            <Card style={neo.card} p="xl">
              <Stack align="center" gap="md" py="xl">
                <IconTarget size={64} color="#cbd5e1" />
                <Title order={3} c="dimmed">Multimodal Bias Detection</Title>
                <Text c="dimmed" ta="center">
                  Cross-modal bias analysis for complex AI systems
                </Text>
                <Button leftSection={<IconPlus size={16} />}>
                  Configure Multimodal Analysis
                </Button>
              </Stack>
            </Card>
          </Tabs.Panel>
        </Tabs>
      </Stack>
    </Container>
  );
}