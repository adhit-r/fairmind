'use client';

import {
  Container,
  Title,
  Text,
  Card,
  Group,
  Badge,
  Stack,
  Button,
  SimpleGrid,
  Box,
  ThemeIcon,
  Progress,
  Paper,
  ActionIcon,
  RingProgress,
  Center,
  Avatar,
  Divider,
  Flex,
  NumberFormatter,
  Grid,
} from '@mantine/core';

import {
  IconShield,
  IconBrain,
  IconTarget,
  IconLock,
  IconUsers,
  IconEye,
  IconRobot,
  IconChartBar,
  IconTrendingUp,
  IconTrendingDown,
  IconActivity,
  IconBell,
  IconArrowRight,
  IconStar,
  IconDatabase,
  IconRefresh,
  IconPlus,
  IconAlertTriangle,
  IconCheck,
  IconX,
  IconSettings,
} from '@tabler/icons-react';

import { useState, useEffect } from 'react';
import { useGlassmorphicTheme } from '@/providers/glassmorphic-theme-provider';

// Mock data for the AI governance dashboard
const mockDashboardData = {
  totalModels: 47,
  activeModels: 32,
  modelsInTesting: 8,
  criticalBiasAlerts: 3,
  fairnessScore: 87,
  reliabilityScore: 92,
  privacyScore: 88,
  transparencyScore: 85,
  overallCompliance: 88,
  lastUpdated: new Date().toISOString(),
};

const mockRecentActivity = [
  {
    id: 1,
    title: 'Bias Detection Completed',
    model: 'GPT-4 Vision',
    severity: 'low',
    time: '2 hours ago',
    type: 'Gender Bias Analysis',
    score: 92,
  },
  {
    id: 2,
    title: 'Security Assessment Alert',
    model: 'ResNet-152',
    severity: 'high',
    time: '4 hours ago',
    type: 'Data Leakage Detection',
    score: 67,
  },
  {
    id: 3,
    title: 'Fairness Check Passed',
    model: 'DALL-E 3',
    severity: 'medium',
    time: '6 hours ago',
    type: 'Cultural Bias Review',
    score: 85,
  },
  {
    id: 4,
    title: 'Privacy Audit Completed',
    model: 'Claude-3',
    severity: 'low',
    time: '8 hours ago',
    type: 'PII Detection',
    score: 94,
  },
];

const mockQuickStats = [
  {
    label: 'Models Monitored',
    value: 47,
    change: '+12%',
    positive: true,
    icon: IconBrain,
    color: 'blue',
  },
  {
    label: 'Active Assessments',
    value: 23,
    change: '+8%',
    positive: true,
    icon: IconActivity,
    color: 'blue',
  },
  {
    label: 'Bias Alerts',
    value: 3,
    change: '-15%',
    positive: true,
    icon: IconAlertTriangle,
    color: 'yellow',
  },
  {
    label: 'Compliance Score',
    value: 88,
    change: '+5%',
    positive: true,
    icon: IconShield,
    color: 'violet',
  },
];

const getScoreColor = (score: number) => {
  if (score >= 90) return 'green';
  if (score >= 80) return 'blue';
  if (score >= 70) return 'yellow';
  return 'red';
};

const getSeverityColor = (severity: string) => {
  switch (severity) {
    case 'low': return 'green';
    case 'medium': return 'yellow';
    case 'high': return 'red';
    default: return 'blue';
  }
};

export default function HomePage() {
  const [isLoading, setIsLoading] = useState(true);
  const [data] = useState(mockDashboardData);
  const { colorScheme } = useGlassmorphicTheme();

  useEffect(() => {
    // Simulate loading
    const timer = setTimeout(() => setIsLoading(false), 1000);
    return () => clearTimeout(timer);
  }, []);

  if (isLoading) {
    return (
      <Container size="xl" py="xl">
        <Center style={{ height: '70vh' }}>
          <Stack align="center" gap="xl">
            <ThemeIcon size="80" radius="xl" variant="light" color="blue">
              <IconBrain size="2.5rem" />
            </ThemeIcon>
            <Title order={2} ta="center">Loading FairMind Platform...</Title>
            <Text size="lg" c="dimmed" ta="center">
              Initializing AI governance dashboard
            </Text>
          </Stack>
        </Center>
      </Container>
    );
  }

  return (
    <div style={{ minHeight: '100vh', padding: '2rem 0' }}>
      <Container size="xl">
        {/* Clean Hero Section */}
        <Paper p="2rem" mb="xl" radius="lg">
          <Stack align="center" gap="xl">
            <ThemeIcon size="80" radius="xl" variant="light" color="blue">
              <IconBrain size="2.5rem" />
            </ThemeIcon>
            <Title order={1} size="2.5rem" fw={700} ta="center">
              AI Governance Platform
            </Title>
            <Text size="lg" c="dimmed" ta="center" maw={600}>
              Professional AI governance with advanced bias detection and compliance monitoring
            </Text>
            <Group gap="md">
              <Button size="lg" leftSection={<IconPlus size="1.2rem" />}>
                New Assessment
              </Button>
              <Button size="lg" variant="outline" leftSection={<IconChartBar size="1.2rem" />}>
                View Analytics
              </Button>
            </Group>
          </Stack>
        </Paper>

        {/* Clean Metrics Grid */}
        <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }} mb="xl">
          {mockQuickStats.map((stat, index) => (
            <Card key={index} p="lg" radius="lg">
              <Group justify="space-between" mb="md">
                <ThemeIcon size="lg" radius="md" color={stat.color} variant="light">
                  <stat.icon size="1.5rem" />
                </ThemeIcon>
                <Group gap="xs">
                  {stat.positive ? (
                    <IconTrendingUp size={16} style={{ color: '#22c55e' }} />
                  ) : (
                    <IconTrendingDown size={16} style={{ color: '#ef4444' }} />
                  )}
                  <Text size="sm" c={stat.positive ? 'green' : 'red'} fw={600}>
                    {stat.change}
                  </Text>
                </Group>
              </Group>
              <Text size="sm" c="dimmed" mb="xs">
                {stat.label}
              </Text>
              <Text size="2rem" fw={800} c="dark">
                <NumberFormatter value={stat.value} />
                {stat.label.includes('Score') && '%'}
              </Text>
            </Card>
          ))}
        </SimpleGrid>

        <Grid>
          {/* Main Content */}
          <Grid.Col span={{ base: 12, lg: 8 }}>
            <Stack gap="xl">
              {/* AI Governance Metrics */}
              <Card p="xl" radius="lg">
                <Group justify="space-between" mb="xl">
                  <div>
                    <Title order={2} mb="xs">AI Governance Metrics</Title>
                    <Text c="dimmed">Core responsible AI principles assessment</Text>
                  </div>
                  <ActionIcon variant="light" size="lg" radius="md">
                    <IconRefresh size="1.2rem" />
                  </ActionIcon>
                </Group>

                <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="xl">
                  {[
                    { label: 'Fairness', value: data.fairnessScore, icon: IconTarget },
                    { label: 'Reliability', value: data.reliabilityScore, icon: IconShield },
                    { label: 'Privacy', value: data.privacyScore, icon: IconLock },
                    { label: 'Transparency', value: data.transparencyScore, icon: IconEye },
                  ].map((metric, index) => (
                    <Box key={index}>
                      <Group justify="space-between" mb="md">
                        <Group gap="sm">
                          <ThemeIcon
                            size="md"
                            radius="md"
                            color={getScoreColor(metric.value)}
                            variant="light"
                          >
                            <metric.icon size="1rem" />
                          </ThemeIcon>
                          <Text fw={600}>{metric.label}</Text>
                        </Group>
                        <Text size="lg" fw={700} c={getScoreColor(metric.value)}>
                          {metric.value}%
                        </Text>
                      </Group>
                      <Progress
                        value={metric.value}
                        size="lg"
                        radius="md"
                        color={getScoreColor(metric.value)}
                      />
                    </Box>
                  ))}
                </SimpleGrid>
              </Card>

              {/* Recent Activity */}
              <Card p="xl" radius="lg">
                <Group justify="space-between" mb="xl">
                  <div>
                    <Title order={2} mb="xs">Recent Activity</Title>
                    <Text c="dimmed">Latest AI governance assessments and alerts</Text>
                  </div>
                  <Button variant="light" size="sm" rightSection={<IconArrowRight size="1rem" />}>
                    View All
                  </Button>
                </Group>

                <Stack gap="md">
                  {mockRecentActivity.map((activity) => (
                    <Paper key={activity.id} p="lg" radius="md">
                      <Group justify="space-between" align="flex-start">
                        <Group gap="md">
                          <ThemeIcon
                            size="lg"
                            radius="md"
                            color={getSeverityColor(activity.severity)}
                            variant="light"
                          >
                            {activity.severity === 'low' ? <IconCheck size="1.2rem" /> :
                             activity.severity === 'medium' ? <IconAlertTriangle size="1.2rem" /> :
                             <IconX size="1.2rem" />}
                          </ThemeIcon>
                          <div>
                            <Text fw={600} mb="2px">{activity.title}</Text>
                            <Text size="sm" c="dimmed" mb="xs">
                              {activity.model} • {activity.type}
                            </Text>
                            <Text size="xs" c="dimmed">{activity.time}</Text>
                          </div>
                        </Group>
                        <Group gap="xs">
                          <Badge
                            color={getScoreColor(activity.score)}
                            variant="light"
                            size="lg"
                          >
                            {activity.score}%
                          </Badge>
                        </Group>
                      </Group>
                    </Paper>
                  ))}
                </Stack>
              </Card>
            </Stack>
          </Grid.Col>

          {/* Sidebar */}
          <Grid.Col span={{ base: 12, lg: 4 }}>
            <Stack gap="xl">
              {/* Overall Compliance */}
              <Card p="xl" radius="lg" ta="center">
                <Title order={3} mb="xl">Overall Compliance</Title>
                <RingProgress
                  size={180}
                  thickness={16}
                  sections={[
                    { value: data.overallCompliance, color: getScoreColor(data.overallCompliance) }
                  ]}
                  label={
                    <Center>
                      <div>
                        <Text size="2xl" fw={800} c={getScoreColor(data.overallCompliance)}>
                          {data.overallCompliance}%
                        </Text>
                        <Text size="sm" c="dimmed">Compliant</Text>
                      </div>
                    </Center>
                  }
                />
                <Text size="sm" c="dimmed" mt="md">
                  AI governance compliance across all principles
                </Text>
              </Card>

              {/* Quick Actions */}
              <Card p="xl" radius="lg">
                <Title order={3} mb="xl">Quick Actions</Title>
                <Stack gap="md">
                  <Button
                    variant="light"
                    fullWidth
                    leftSection={<IconTarget size="1rem" />}
                    color="blue"
                  >
                    Run Bias Analysis
                  </Button>
                  <Button
                    variant="light"
                    fullWidth
                    leftSection={<IconShield size="1rem" />}
                    color="green"
                  >
                    Security Assessment
                  </Button>
                  <Button
                    variant="light"
                    fullWidth
                    leftSection={<IconDatabase size="1rem" />}
                    color="violet"
                  >
                    Data Privacy Audit
                  </Button>
                  <Button
                    variant="light"
                    fullWidth
                    leftSection={<IconEye size="1rem" />}
                    color="yellow"
                  >
                    Transparency Report
                  </Button>
                </Stack>
              </Card>

              {/* System Status */}
              <Card p="xl" radius="lg">
                <Group justify="space-between" mb="xl">
                  <Title order={3}>System Status</Title>
                  <ActionIcon variant="light" size="sm">
                    <IconBell size="1rem" />
                  </ActionIcon>
                </Group>
                <Stack gap="md">
                  <Group justify="space-between">
                    <Text size="sm">Active Models</Text>
                    <Badge color="green" variant="light">
                      {data.activeModels} Running
                    </Badge>
                  </Group>
                  <Group justify="space-between">
                    <Text size="sm">In Testing</Text>
                    <Badge color="yellow" variant="light">
                      {data.modelsInTesting} Models
                    </Badge>
                  </Group>
                  <Group justify="space-between">
                    <Text size="sm">Critical Alerts</Text>
                    <Badge color="red" variant="light">
                      {data.criticalBiasAlerts} Active
                    </Badge>
                  </Group>
                  <Divider my="sm" />
                  <Text size="xs" c="dimmed">
                    Last updated: {new Date(data.lastUpdated).toLocaleTimeString()}
                  </Text>
                </Stack>
              </Card>
            </Stack>
          </Grid.Col>
        </Grid>
      </Container>
    </div>
  );
}