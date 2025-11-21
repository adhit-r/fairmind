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
  Menu,
  Progress,
  Timeline,
  Alert,
} from '@mantine/core';
import {
  IconTarget,
  IconAlertTriangle,
  IconCheck,
  IconClock,
  IconPlus,
  IconEdit,
  IconEye,
  IconDots,
  IconShield,
  IconTrendingUp,
  IconUsers,
  IconCalendar,
  IconX,
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

const riskIncidents = [
  {
    id: 1,
    title: 'High Bias Detected in Hiring Model',
    description: 'Gender bias exceeding 15% threshold in candidate screening algorithm',
    severity: 'critical',
    status: 'open',
    category: 'Bias & Fairness',
    assignedTo: 'Sarah Chen',
    createdDate: '2024-01-20',
    lastUpdate: '2024-01-22',
    affectedModels: ['Hiring Recommendation v2.1'],
    impact: 'Production systems affected',
    priority: 'urgent',
  },
  {
    id: 2,
    title: 'Data Privacy Compliance Issue',
    description: 'Personal data retention period exceeded GDPR requirements',
    severity: 'high',
    status: 'in-progress',
    category: 'Privacy',
    assignedTo: 'Mike Rodriguez',
    createdDate: '2024-01-18',
    lastUpdate: '2024-01-21',
    affectedModels: ['Customer Segmentation v1.8'],
    impact: 'Regulatory compliance risk',
    priority: 'high',
  },
  {
    id: 3,
    title: 'Model Performance Degradation',
    description: 'Accuracy dropped below acceptable threshold for credit risk model',
    severity: 'medium',
    status: 'investigating',
    category: 'Performance',
    assignedTo: 'Alex Kim',
    createdDate: '2024-01-15',
    lastUpdate: '2024-01-20',
    affectedModels: ['Credit Risk v3.2'],
    impact: 'Business operations impacted',
    priority: 'medium',
  },
  {
    id: 4,
    title: 'Security Vulnerability in Model API',
    description: 'Potential data exposure through model inference endpoint',
    severity: 'high',
    status: 'resolved',
    category: 'Security',
    assignedTo: 'Lisa Park',
    createdDate: '2024-01-12',
    lastUpdate: '2024-01-19',
    affectedModels: ['Fraud Detection v4.1'],
    impact: 'Security vulnerability',
    priority: 'urgent',
  },
];

const riskStats = [
  {
    title: 'Open Incidents',
    value: '7',
    icon: IconAlertTriangle,
    color: 'red',
  },
  {
    title: 'In Progress',
    value: '12',
    icon: IconClock,
    color: 'yellow',
  },
  {
    title: 'Resolved This Month',
    value: '24',
    icon: IconCheck,
    color: 'green',
  },
  {
    title: 'Risk Score',
    value: '6.8/10',
    icon: IconTarget,
    color: 'blue',
  },
];

const riskTrends = [
  {
    type: 'Bias Issues',
    thisMonth: 8,
    lastMonth: 12,
    trend: 'down',
  },
  {
    type: 'Security Risks',
    thisMonth: 3,
    lastMonth: 2,
    trend: 'up',
  },
  {
    type: 'Performance Issues',
    thisMonth: 5,
    lastMonth: 7,
    trend: 'down',
  },
  {
    type: 'Compliance Violations',
    thisMonth: 2,
    lastMonth: 1,
    trend: 'up',
  },
];

function getSeverityColor(severity: string) {
  switch (severity) {
    case 'critical':
      return 'red';
    case 'high':
      return 'orange';
    case 'medium':
      return 'yellow';
    case 'low':
      return 'green';
    default:
      return 'gray';
  }
}

function getStatusColor(status: string) {
  switch (status) {
    case 'open':
      return 'red';
    case 'in-progress':
      return 'blue';
    case 'investigating':
      return 'yellow';
    case 'resolved':
      return 'green';
    case 'closed':
      return 'gray';
    default:
      return 'gray';
  }
}

function getStatusIcon(status: string) {
  switch (status) {
    case 'open':
      return <IconAlertTriangle size={16} />;
    case 'in-progress':
      return <IconClock size={16} />;
    case 'investigating':
      return <IconEye size={16} />;
    case 'resolved':
      return <IconCheck size={16} />;
    case 'closed':
      return <IconX size={16} />;
    default:
      return <IconTarget size={16} />;
  }
}

function getTrendIcon(trend: string) {
  return trend === 'up' ? '↗️' : '↘️';
}

function getTrendColor(trend: string) {
  return trend === 'down' ? 'green' : 'red';
}

export default function RisksPage() {
  const { data: risksData, loading, error } = useApi('/api/v1/risks');

  return (
    <Container size="xl" py="xl">
      <Stack gap="xl">
        {/* Header */}
        <Card style={neo.card} p="xl">
          <Group justify="space-between" align="center">
            <div>
              <Title order={1} size="2rem" fw={700} c="#1e293b" mb="xs">
                Risk & Incident Management
              </Title>
              <Text c="dimmed" size="lg">
                Monitor, track, and resolve AI risks and incidents
              </Text>
            </div>
            <Button
              size="lg"
              radius="xl"
              leftSection={<IconPlus size={20} />}
              style={{
                background: 'linear-gradient(145deg, #dc2626, #b91c1c)',
                boxShadow: '6px 6px 12px rgba(220, 38, 38, 0.4), -4px -4px 8px rgba(248, 113, 113, 0.4)',
              }}
            >
              Report Incident
            </Button>
          </Group>
        </Card>

        {/* Statistics */}
        <SimpleGrid cols={{ base: 2, md: 4 }} spacing="lg">
          {riskStats.map((stat) => (
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
                  <Text size="sm" c="dimmed">
                    {stat.title}
                  </Text>
                </div>
              </Stack>
            </Card>
          ))}
        </SimpleGrid>

        {/* Risk Trends */}
        <Card style={neo.card} p="xl">
          <Title order={3} size="lg" fw={600} mb="lg">
            Risk Trends
          </Title>
          <SimpleGrid cols={{ base: 2, md: 4 }} spacing="lg">
            {riskTrends.map((trend, index) => (
              <Card
                key={index}
                style={{
                  background: 'rgba(255, 255, 255, 0.6)',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  borderRadius: '12px',
                }}
                p="md"
              >
                <Stack gap="xs">
                  <Text size="sm" fw={600}>
                    {trend.type}
                  </Text>
                  <Group justify="space-between" align="center">
                    <Text size="xl" fw={700}>
                      {trend.thisMonth}
                    </Text>
                    <Group gap="xs" align="center">
                      <Text size="xs" c={getTrendColor(trend.trend)}>
                        {getTrendIcon(trend.trend)}
                      </Text>
                      <Text size="xs" c="dimmed">
                        vs {trend.lastMonth}
                      </Text>
                    </Group>
                  </Group>
                </Stack>
              </Card>
            ))}
          </SimpleGrid>
        </Card>

        {/* Active Incidents */}
        <Card style={neo.card} p="xl">
          <Group justify="space-between" align="center" mb="lg">
            <Title order={3} size="lg" fw={600}>
              Active Risk Incidents
            </Title>
            <ActionIcon variant="light" radius="xl">
              <IconEye size={16} />
            </ActionIcon>
          </Group>

          <Table.ScrollContainer minWidth={800}>
            <Table>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Incident</Table.Th>
                  <Table.Th>Severity</Table.Th>
                  <Table.Th>Status</Table.Th>
                  <Table.Th>Category</Table.Th>
                  <Table.Th>Assigned To</Table.Th>
                  <Table.Th>Created</Table.Th>
                  <Table.Th>Actions</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {riskIncidents.map((incident) => (
                  <Table.Tr key={incident.id}>
                    <Table.Td>
                      <div>
                        <Text fw={600} size="sm">
                          {incident.title}
                        </Text>
                        <Text size="xs" c="dimmed" lineClamp={2}>
                          {incident.description}
                        </Text>
                        <Group gap="xs" mt="xs">
                          <Badge size="xs" variant="light" color="gray">
                            {incident.priority}
                          </Badge>
                          {incident.affectedModels.map((model, index) => (
                            <Badge key={index} size="xs" variant="light" color="blue">
                              {model}
                            </Badge>
                          ))}
                        </Group>
                      </div>
                    </Table.Td>
                    <Table.Td>
                      <Badge
                        size="sm"
                        radius="md"
                        color={getSeverityColor(incident.severity)}
                        variant="light"
                      >
                        {incident.severity}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <Badge
                        size="sm"
                        radius="md"
                        color={getStatusColor(incident.status)}
                        variant="light"
                        leftSection={getStatusIcon(incident.status)}
                      >
                        {incident.status}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <Badge
                        size="sm"
                        radius="md"
                        variant="light"
                        color="cyan"
                      >
                        {incident.category}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs" align="center">
                        <IconUsers size={14} color="#6b7280" />
                        <Text size="sm">
                          {incident.assignedTo}
                        </Text>
                      </Group>
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs" align="center">
                        <IconCalendar size={14} color="#6b7280" />
                        <Text size="xs" c="dimmed">
                          {new Date(incident.createdDate).toLocaleDateString()}
                        </Text>
                      </Group>
                    </Table.Td>
                    <Table.Td>
                      <Menu shadow="md" width={200}>
                        <Menu.Target>
                          <ActionIcon
                            variant="light"
                            size="sm"
                            radius="xl"
                          >
                            <IconDots size={14} />
                          </ActionIcon>
                        </Menu.Target>

                        <Menu.Dropdown style={neo.card}>
                          <Menu.Item leftSection={<IconEye size={14} />}>
                            View Details
                          </Menu.Item>
                          <Menu.Item leftSection={<IconEdit size={14} />}>
                            Update Status
                          </Menu.Item>
                          <Menu.Item leftSection={<IconUsers size={14} />}>
                            Reassign
                          </Menu.Item>
                        </Menu.Dropdown>
                      </Menu>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Table.ScrollContainer>
        </Card>

        {/* Recent Activity Timeline */}
        <Card style={neo.card} p="xl">
          <Title order={3} size="lg" fw={600} mb="lg">
            Recent Risk Activity
          </Title>
          
          <Timeline active={-1} bulletSize={24} lineWidth={2}>
            <Timeline.Item
              bullet={<IconAlertTriangle size={12} />}
              title="Critical Bias Issue Reported"
            >
              <Text size="sm" c="dimmed" mb="xs">
                High gender bias detected in hiring recommendation model
              </Text>
              <Text size="xs" c="dimmed">2 hours ago</Text>
            </Timeline.Item>

            <Timeline.Item
              bullet={<IconCheck size={12} />}
              title="Security Vulnerability Resolved"
            >
              <Text size="sm" c="dimmed" mb="xs">
                API security issue in fraud detection model has been patched
              </Text>
              <Text size="xs" c="dimmed">1 day ago</Text>
            </Timeline.Item>

            <Timeline.Item
              bullet={<IconClock size={12} />}
              title="Privacy Compliance Review Started"
            >
              <Text size="sm" c="dimmed" mb="xs">
                GDPR compliance review initiated for customer segmentation model
              </Text>
              <Text size="xs" c="dimmed">2 days ago</Text>
            </Timeline.Item>
          </Timeline>
        </Card>
      </Stack>
    </Container>
  );
}