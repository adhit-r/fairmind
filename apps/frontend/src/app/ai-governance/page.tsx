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
  ActionIcon,
  ThemeIcon,
  Timeline,
  Alert,
} from '@mantine/core';
import {
  IconShield,
  IconFileText,
  IconUsers,
  IconBell,
  IconActivity,
  IconCheck,
  IconClock,
  IconAlertTriangle,
  IconEye,
  IconSettings,
  IconChartBar,
  IconTarget,
  IconLock,
  IconGavel,
} from '@tabler/icons-react';
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

const governanceStats = [
  {
    title: 'Active Policies',
    value: '24',
    icon: IconFileText,
    color: 'blue',
    description: 'Governance policies in effect',
  },
  {
    title: 'Compliance Score',
    value: '87%',
    icon: IconShield,
    color: 'green',
    description: 'Overall regulatory compliance',
  },
  {
    title: 'Risk Incidents',
    value: '3',
    icon: IconAlertTriangle,
    color: 'red',
    description: 'Open risk incidents requiring attention',
  },
  {
    title: 'Model Audits',
    value: '156',
    icon: IconEye,
    color: 'violet',
    description: 'Completed model audits this quarter',
  },
];

const recentActivities = [
  {
    title: 'New GDPR Compliance Policy',
    description: 'Updated data privacy policy to align with latest GDPR requirements',
    time: '2 hours ago',
    type: 'policy',
    status: 'completed',
  },
  {
    title: 'Model Risk Assessment',
    description: 'Credit scoring model v3.2 completed risk evaluation',
    time: '4 hours ago',
    type: 'audit',
    status: 'completed',
  },
  {
    title: 'Bias Detection Alert',
    description: 'Potential bias detected in hiring recommendation model',
    time: '6 hours ago',
    type: 'alert',
    status: 'pending',
  },
  {
    title: 'Compliance Review',
    description: 'Quarterly compliance review scheduled for next week',
    time: '1 day ago',
    type: 'review',
    status: 'scheduled',
  },
];

const governanceAreas = [
  {
    title: 'Policy Management',
    description: 'Create and manage governance policies',
    icon: IconGavel,
    color: 'blue',
    route: '/policies',
    stats: { active: 24, pending: 3 },
  },
  {
    title: 'Risk Management',
    description: 'Monitor and mitigate AI risks',
    icon: IconTarget,
    color: 'red',
    route: '/risks',
    stats: { open: 3, resolved: 47 },
  },
  {
    title: 'Compliance Tracking',
    description: 'Track regulatory compliance status',
    icon: IconShield,
    color: 'green',
    route: '/compliance',
    stats: { compliant: 87, audits: 12 },
  },
  {
    title: 'Evidence Collection',
    description: 'Gather and organize compliance evidence',
    icon: IconFileText,
    color: 'cyan',
    route: '/evidence',
    stats: { collected: 234, verified: 198 },
  },
];

function getStatusColor(status: string) {
  switch (status) {
    case 'completed':
      return 'green';
    case 'pending':
      return 'yellow';
    case 'scheduled':
      return 'blue';
    case 'overdue':
      return 'red';
    default:
      return 'gray';
  }
}

function getActivityIcon(type: string) {
  switch (type) {
    case 'policy':
      return <IconFileText size={16} />;
    case 'audit':
      return <IconEye size={16} />;
    case 'alert':
      return <IconAlertTriangle size={16} />;
    case 'review':
      return <IconActivity size={16} />;
    default:
      return <IconSettings size={16} />;
  }
}

export default function AIGovernancePage() {
  const { data: governanceData, loading, error } = useApi('/api/v1/ai-governance/status');

  return (
    <Container size="xl" py="xl">
      <Stack gap="xl">
        {/* Header */}
        <Card style={neo.card} p="xl">
          <Group justify="space-between" align="center">
            <div>
              <Title order={1} size="2rem" fw={700} c="#1e293b" mb="xs">
                AI Governance Hub
              </Title>
              <Text c="dimmed" size="lg">
                Central command center for AI governance, compliance, and risk management
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
                <IconBell size={20} />
              </ActionIcon>
              <Button
                leftSection={<IconChartBar size={16} />}
                radius="xl"
                style={{
                  background: 'linear-gradient(145deg, #7c3aed, #6d28d9)',
                  boxShadow: '6px 6px 12px rgba(124, 58, 237, 0.4), -4px -4px 8px rgba(139, 92, 246, 0.4)',
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
            Unable to connect to governance service: {error}
          </Alert>
        )}

        {/* Governance Statistics */}
        <SimpleGrid cols={{ base: 2, md: 4 }} spacing="lg">
          {governanceStats.map((stat) => (
            <Card
              key={stat.title}
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
              <Stack gap="sm">
                <ThemeIcon
                  size="lg"
                  radius="xl"
                  color={stat.color}
                  variant="light"
                >
                  <stat.icon size={20} />
                </ThemeIcon>
                
                <div>
                  <Text size="2xl" fw={700} c="#1e293b">
                    {stat.value}
                  </Text>
                  <Text size="sm" fw={600}>
                    {stat.title}
                  </Text>
                  <Text size="xs" c="dimmed">
                    {stat.description}
                  </Text>
                </div>
              </Stack>
            </Card>
          ))}
        </SimpleGrid>

        {/* Governance Areas */}
        <Card style={neo.card} p="xl">
          <Title order={3} size="lg" fw={600} mb="lg">
            Governance Areas
          </Title>
          <SimpleGrid cols={{ base: 1, md: 2 }} spacing="lg">
            {governanceAreas.map((area) => (
              <Card
                key={area.title}
                style={{
                  background: 'rgba(255, 255, 255, 0.8)',
                  backdropFilter: 'blur(10px)',
                  border: '1px solid rgba(255, 255, 255, 0.3)',
                  borderRadius: '16px',
                  boxShadow: '6px 6px 12px rgba(163, 177, 198, 0.3), -6px -6px 12px rgba(255, 255, 255, 0.8)',
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-2px)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                }}
                onClick={() => window.location.href = area.route}
                p="lg"
              >
                <Group justify="space-between" align="flex-start">
                  <Group gap="sm" align="flex-start">
                    <ThemeIcon
                      size="lg"
                      radius="xl"
                      color={area.color}
                      variant="light"
                    >
                      <area.icon size={20} />
                    </ThemeIcon>
                    <div>
                      <Text fw={600} size="md" mb="xs">
                        {area.title}
                      </Text>
                      <Text size="sm" c="dimmed" mb="md">
                        {area.description}
                      </Text>
                      <Group gap="sm">
                        {Object.entries(area.stats).map(([key, value]) => (
                          <Badge
                            key={key}
                            size="sm"
                            radius="md"
                            variant="light"
                            color={area.color}
                          >
                            {key}: {value}
                          </Badge>
                        ))}
                      </Group>
                    </div>
                  </Group>
                  <ActionIcon
                    variant="light"
                    size="sm"
                    radius="xl"
                    color={area.color}
                  >
                    <IconEye size={16} />
                  </ActionIcon>
                </Group>
              </Card>
            ))}
          </SimpleGrid>
        </Card>

        {/* Recent Activities */}
        <Card style={neo.card} p="xl">
          <Group justify="space-between" align="center" mb="lg">
            <Title order={3} size="lg" fw={600}>
              Recent Activities
            </Title>
            <Button variant="light" size="sm" radius="xl">
              View All
            </Button>
          </Group>
          
          <Timeline active={-1} bulletSize={24} lineWidth={2}>
            {recentActivities.map((activity, index) => (
              <Timeline.Item
                key={index}
                bullet={getActivityIcon(activity.type)}
                title={
                  <Group justify="space-between" align="center">
                    <Text fw={600} size="sm">
                      {activity.title}
                    </Text>
                    <Badge
                      size="xs"
                      radius="xl"
                      color={getStatusColor(activity.status)}
                      variant="light"
                    >
                      {activity.status}
                    </Badge>
                  </Group>
                }
              >
                <Text size="sm" c="dimmed" mb="xs">
                  {activity.description}
                </Text>
                <Text size="xs" c="dimmed">
                  {activity.time}
                </Text>
              </Timeline.Item>
            ))}
          </Timeline>
        </Card>
      </Stack>
    </Container>
  );
}