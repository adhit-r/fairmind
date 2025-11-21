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
  Badge,
  ActionIcon,
  ThemeIcon,
  Tabs,
  Alert,
} from '@mantine/core';
import {
  IconScale,
  IconTarget,
  IconShield,
  IconChartBar,
  IconEye,
  IconRefresh,
  IconAlertTriangle,
  IconCheck,
  IconTrendingUp,
  IconUsers,
} from '@tabler/icons-react';
import { LineChart } from '@mantine/charts';
import { useApi } from '@/hooks/useApi';

const neo = {
  card: {
    background: 'rgba(255, 255, 255, 0.95)',
    backdropFilter: 'blur(20px)',
    border: '1px solid rgba(255, 255, 255, 0.3)',
    borderRadius: '20px',
    boxShadow: '12px 12px 24px rgba(163, 177, 198, 0.4), -12px -12px 24px rgba(255, 255, 255, 0.9)',
  },
};

const fairnessMetrics = [
  {
    name: 'Demographic Parity',
    score: 85,
    threshold: 80,
    status: 'pass',
    description: 'Equal positive prediction rates across groups',
    trend: [78, 80, 82, 85, 83, 85, 87],
  },
  {
    name: 'Equalized Odds',
    score: 72,
    threshold: 75,
    status: 'warning',
    description: 'Equal true positive and false positive rates',
    trend: [70, 68, 71, 72, 75, 72, 72],
  },
  {
    name: 'Calibration',
    score: 92,
    threshold: 85,
    status: 'pass',
    description: 'Predicted probabilities match observed frequencies',
    trend: [88, 90, 91, 92, 89, 92, 92],
  },
  {
    name: 'Individual Fairness',
    score: 67,
    threshold: 70,
    status: 'fail',
    description: 'Similar individuals receive similar treatment',
    trend: [65, 63, 67, 69, 66, 67, 67],
  },
];

const protectedAttributes = [
  {
    attribute: 'Gender',
    groups: ['Male', 'Female', 'Non-binary'],
    scores: { Male: 78, Female: 82, 'Non-binary': 75 },
    disparity: 7,
  },
  {
    attribute: 'Age',
    groups: ['18-30', '31-50', '51+'],
    scores: { '18-30': 85, '31-50': 79, '51+': 72 },
    disparity: 13,
  },
  {
    attribute: 'Race/Ethnicity',
    groups: ['White', 'Black', 'Hispanic', 'Asian', 'Other'],
    scores: { White: 81, Black: 74, Hispanic: 77, Asian: 83, Other: 76 },
    disparity: 9,
  },
  {
    attribute: 'Income Level',
    groups: ['Low', 'Medium', 'High'],
    scores: { Low: 71, Medium: 79, High: 86 },
    disparity: 15,
  },
];

function getScoreColor(score: number, threshold: number) {
  if (score >= threshold) return 'green';
  if (score >= threshold - 10) return 'yellow';
  return 'red';
}

function getStatusIcon(status: string) {
  switch (status) {
    case 'pass':
      return <IconCheck size={16} />;
    case 'warning':
      return <IconAlertTriangle size={16} />;
    case 'fail':
      return <IconAlertTriangle size={16} />;
    default:
      return <IconEye size={16} />;
  }
}

export default function FairnessPage() {
  const { data: fairnessData, loading, error } = useApi('/api/v1/fairness/metrics');

  return (
    <Container size="xl" py="xl">
      <Stack gap="xl">
        {/* Header */}
        <Card style={neo.card} p="xl">
          <Group justify="space-between" align="center">
            <div>
              <Title order={1} size="2rem" fw={700} c="#1e293b" mb="xs">
                Fairness Metrics
              </Title>
              <Text c="dimmed" size="lg">
                Comprehensive fairness measurement and monitoring tools
              </Text>
            </div>
            <Group gap="sm">
              <ActionIcon
                size="lg"
                radius="xl"
                variant="light"
                color="blue"
                style={{
                  background: 'rgba(59, 130, 246, 0.1)',
                  boxShadow: '4px 4px 8px rgba(59, 130, 246, 0.2), -4px -4px 8px rgba(255, 255, 255, 0.8)',
                }}
              >
                <IconRefresh size={20} />
              </ActionIcon>
              <Button
                leftSection={<IconChartBar size={16} />}
                radius="xl"
                style={{
                  background: 'linear-gradient(145deg, #059669, #047857)',
                  boxShadow: '6px 6px 12px rgba(5, 150, 105, 0.4), -4px -4px 8px rgba(16, 185, 129, 0.4)',
                }}
              >
                Generate Report
              </Button>
            </Group>
          </Group>
        </Card>

        {error && (
          <Alert
            icon={<IconAlertTriangle size={16} />}
            color="red"
            title="Connection Error"
            style={neo.card}
          >
            Unable to connect to fairness service: {error?.message || 'Unknown error'}
          </Alert>
        )}

        {/* Fairness Overview */}
        <SimpleGrid cols={{ base: 1, md: 2, lg: 4 }} spacing="lg">
          {fairnessMetrics.map((metric) => (
            <Card
              key={metric.name}
              style={{
                ...neo.card,
                transition: 'all 0.3s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
              }}
              p="lg"
            >
              <Stack gap="md">
                <Group justify="space-between">
                  <ThemeIcon
                    size="lg"
                    radius="xl"
                    color={getScoreColor(metric.score, metric.threshold)}
                    variant="light"
                  >
                    <IconScale size={20} />
                  </ThemeIcon>
                  <Badge
                    color={getScoreColor(metric.score, metric.threshold)}
                    variant="light"
                    radius="xl"
                    leftSection={getStatusIcon(metric.status)}
                  >
                    {metric.status}
                  </Badge>
                </Group>
                
                <div>
                  <Text size="lg" fw={700} c="#1e293b">
                    {metric.name}
                  </Text>
                  <Text size="xs" c="dimmed" mb="sm">
                    {metric.description}
                  </Text>
                </div>
                
                <div>
                  <Group justify="space-between" mb="xs">
                    <Text size="sm" fw={500}>Score</Text>
                    <Text size="sm" fw={700} c={getScoreColor(metric.score, metric.threshold)}>
                      {metric.score}%
                    </Text>
                  </Group>
                  <Progress
                    value={metric.score}
                    size="md"
                    radius="xl"
                    color={getScoreColor(metric.score, metric.threshold)}
                  />
                  <Text size="xs" c="dimmed" mt="xs">
                    Threshold: {metric.threshold}%
                  </Text>
                </div>

                <div style={{ height: 60 }}>
                  <LineChart
                    h={60}
                    data={metric.trend.map((value, index) => ({ day: index + 1, value }))}
                    dataKey="day"
                    series={[{ name: 'value', color: getScoreColor(metric.score, metric.threshold) }]}
                    gridAxis="none"
                    withXAxis={false}
                    withYAxis={false}
                    curveType="natural"
                  />
                </div>
              </Stack>
            </Card>
          ))}
        </SimpleGrid>

        {/* Detailed Analysis */}
        <Tabs defaultValue="protected-attributes" radius="lg">
          <Tabs.List>
            <Tabs.Tab value="protected-attributes">Protected Attributes</Tabs.Tab>
            <Tabs.Tab value="intersectional">Intersectional Analysis</Tabs.Tab>
            <Tabs.Tab value="temporal">Temporal Trends</Tabs.Tab>
            <Tabs.Tab value="recommendations">Recommendations</Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="protected-attributes" pt="xl">
            <SimpleGrid cols={{ base: 1, md: 2 }} spacing="lg">
              {protectedAttributes.map((attr) => (
                <Card key={attr.attribute} style={neo.card} p="xl">
                  <Stack gap="md">
                    <Group justify="space-between">
                      <Title order={3} size="lg" fw={600}>
                        {attr.attribute}
                      </Title>
                      <Badge
                        color={attr.disparity <= 5 ? 'green' : attr.disparity <= 10 ? 'yellow' : 'red'}
                        variant="light"
                        radius="xl"
                      >
                        {attr.disparity}% disparity
                      </Badge>
                    </Group>

                    <Stack gap="sm">
                      {attr.groups.map((group) => {
                        const score = attr.scores[group as keyof typeof attr.scores] || 0;
                        return (
                        <div key={group}>
                          <Group justify="space-between" mb="xs">
                            <Text size="sm" fw={500}>{group}</Text>
                            <Text size="sm" fw={700}>
                              {score}%
                            </Text>
                          </Group>
                          <Progress
                            value={score}
                            size="sm"
                            radius="xl"
                            color={
                              score >= 80 ? 'green' :
                              score >= 70 ? 'yellow' : 'red'
                            }
                          />
                        </div>
                        );
                      })}
                    </Stack>
                  </Stack>
                </Card>
              ))}
            </SimpleGrid>
          </Tabs.Panel>

          <Tabs.Panel value="intersectional" pt="xl">
            <Card style={neo.card} p="xl">
              <Stack align="center" gap="md" py="xl">
                <IconUsers size={64} color="#cbd5e1" />
                <Title order={3} c="dimmed">Intersectional Analysis</Title>
                <Text c="dimmed" ta="center">
                  Advanced analysis of fairness across multiple protected attributes simultaneously
                </Text>
                <Button leftSection={<IconTrendingUp size={16} />}>
                  Run Intersectional Analysis
                </Button>
              </Stack>
            </Card>
          </Tabs.Panel>

          <Tabs.Panel value="temporal" pt="xl">
            <Card style={neo.card} p="xl">
              <Stack align="center" gap="md" py="xl">
                <IconChartBar size={64} color="#cbd5e1" />
                <Title order={3} c="dimmed">Temporal Trends</Title>
                <Text c="dimmed" ta="center">
                  Monitor how fairness metrics change over time and identify patterns
                </Text>
                <Button leftSection={<IconEye size={16} />}>
                  View Temporal Analysis
                </Button>
              </Stack>
            </Card>
          </Tabs.Panel>

          <Tabs.Panel value="recommendations" pt="xl">
            <Card style={neo.card} p="xl">
              <Stack align="center" gap="md" py="xl">
                <IconTarget size={64} color="#cbd5e1" />
                <Title order={3} c="dimmed">Fairness Recommendations</Title>
                <Text c="dimmed" ta="center">
                  AI-powered recommendations to improve model fairness and reduce bias
                </Text>
                <Button leftSection={<IconShield size={16} />}>
                  Get Recommendations
                </Button>
              </Stack>
            </Card>
          </Tabs.Panel>
        </Tabs>
      </Stack>
    </Container>
  );
}