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
  Progress,
  ThemeIcon,
  ActionIcon,
  Tabs,
  Alert,
  List,
} from '@mantine/core';
import {
  IconShield,
  IconCheck,
  IconAlertTriangle,
  IconX,
  IconFileText,
  IconDownload,
  IconEye,
  IconRefresh,
  IconGavel,
  IconUsers,
  IconCalendar,
  IconTarget,
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

const complianceFrameworks = [
  {
    id: 1,
    name: 'GDPR Compliance',
    description: 'General Data Protection Regulation compliance for EU operations',
    status: 'compliant',
    score: 94,
    lastAudit: '2024-01-15',
    requirements: 12,
    completed: 11,
    violations: 0,
    category: 'Privacy',
  },
  {
    id: 2,
    name: 'ISO 27001',
    description: 'Information Security Management System standards',
    status: 'compliant',
    score: 88,
    lastAudit: '2024-01-10',
    requirements: 15,
    completed: 13,
    violations: 0,
    category: 'Security',
  },
  {
    id: 3,
    name: 'SOX Compliance',
    description: 'Sarbanes-Oxley Act financial reporting compliance',
    status: 'partial',
    score: 76,
    lastAudit: '2024-01-20',
    requirements: 8,
    completed: 6,
    violations: 1,
    category: 'Financial',
  },
  {
    id: 4,
    name: 'AI Ethics Guidelines',
    description: 'Internal AI ethics and responsible AI development standards',
    status: 'review',
    score: 82,
    lastAudit: '2024-01-18',
    requirements: 20,
    completed: 16,
    violations: 2,
    category: 'Ethics',
  },
];

const complianceStats = [
  {
    title: 'Frameworks Tracked',
    value: '12',
    icon: IconShield,
    color: 'blue',
  },
  {
    title: 'Overall Compliance',
    value: '85%',
    icon: IconCheck,
    color: 'green',
  },
  {
    title: 'Active Violations',
    value: '3',
    icon: IconAlertTriangle,
    color: 'red',
  },
  {
    title: 'Last Audit',
    value: '2 days ago',
    icon: IconCalendar,
    color: 'violet',
  },
];

const upcomingRequirements = [
  {
    framework: 'GDPR',
    requirement: 'Data Processing Impact Assessment Update',
    dueDate: '2024-02-15',
    priority: 'high',
  },
  {
    framework: 'ISO 27001',
    requirement: 'Security Control Review',
    dueDate: '2024-02-20',
    priority: 'medium',
  },
  {
    framework: 'AI Ethics',
    requirement: 'Bias Testing Report',
    dueDate: '2024-02-25',
    priority: 'high',
  },
];

function getStatusColor(status: string) {
  switch (status) {
    case 'compliant':
      return 'green';
    case 'partial':
      return 'yellow';
    case 'review':
      return 'blue';
    case 'violation':
      return 'red';
    default:
      return 'gray';
  }
}

function getStatusIcon(status: string) {
  switch (status) {
    case 'compliant':
      return <IconCheck size={16} />;
    case 'partial':
      return <IconAlertTriangle size={16} />;
    case 'review':
      return <IconEye size={16} />;
    case 'violation':
      return <IconX size={16} />;
    default:
      return <IconShield size={16} />;
  }
}

function getScoreColor(score: number) {
  if (score >= 90) return 'green';
  if (score >= 80) return 'blue';
  if (score >= 70) return 'yellow';
  return 'red';
}

function getPriorityColor(priority: string) {
  switch (priority) {
    case 'high':
      return 'red';
    case 'medium':
      return 'yellow';
    case 'low':
      return 'green';
    default:
      return 'gray';
  }
}

export default function CompliancePage() {
  const { data: complianceData, loading, error } = useApi('/api/v1/compliance');

  return (
    <Container size="xl" py="xl">
      <Stack gap="xl">
        {/* Header */}
        <Card style={neo.card} p="xl">
          <Group justify="space-between" align="center">
            <div>
              <Title order={1} size="2rem" fw={700} c="#1e293b" mb="xs">
                Compliance Frameworks
              </Title>
              <Text c="dimmed" size="lg">
                Monitor regulatory compliance and framework adherence
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
                leftSection={<IconDownload size={16} />}
                radius="xl"
                style={{
                  background: 'linear-gradient(145deg, #dc2626, #b91c1c)',
                  boxShadow: '6px 6px 12px rgba(220, 38, 38, 0.4), -4px -4px 8px rgba(248, 113, 113, 0.4)',
                }}
              >
                Export Report
              </Button>
            </Group>
          </Group>
        </Card>

        {/* Statistics */}
        <SimpleGrid cols={{ base: 2, md: 4 }} spacing="lg">
          {complianceStats.map((stat) => (
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

        {/* Compliance Overview */}
        <Tabs defaultValue="frameworks" radius="lg">
          <Tabs.List>
            <Tabs.Tab value="frameworks">Compliance Frameworks</Tabs.Tab>
            <Tabs.Tab value="requirements">Upcoming Requirements</Tabs.Tab>
            <Tabs.Tab value="violations">Violations & Issues</Tabs.Tab>
            <Tabs.Tab value="reports">Audit Reports</Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="frameworks" pt="xl">
            <SimpleGrid cols={{ base: 1, md: 2 }} spacing="lg">
              {complianceFrameworks.map((framework) => (
                <Card
                  key={framework.id}
                  style={{
                    ...neo.card,
                    cursor: 'pointer',
                    transition: 'all 0.3s ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-2px)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)';
                  }}
                  p="xl"
                >
                  <Stack gap="md">
                    <Group justify="space-between">
                      <Group gap="sm">
                        <ThemeIcon
                          size="lg"
                          radius="xl"
                          color={getStatusColor(framework.status)}
                          variant="light"
                        >
                          <IconShield size={20} />
                        </ThemeIcon>
                        <div>
                          <Title order={3} size="lg" fw={600}>
                            {framework.name}
                          </Title>
                          <Text size="sm" c="dimmed">
                            {framework.description}
                          </Text>
                        </div>
                      </Group>
                      <Badge
                        color={getStatusColor(framework.status)}
                        variant="light"
                        radius="xl"
                        leftSection={getStatusIcon(framework.status)}
                      >
                        {framework.status}
                      </Badge>
                    </Group>

                    <div>
                      <Group justify="space-between" mb="xs">
                        <Text size="sm" fw={500}>Compliance Score</Text>
                        <Text size="sm" fw={700} c={getScoreColor(framework.score)}>
                          {framework.score}%
                        </Text>
                      </Group>
                      <Progress
                        value={framework.score}
                        size="md"
                        radius="xl"
                        color={getScoreColor(framework.score)}
                      />
                    </div>

                    <Group justify="space-between">
                      <div>
                        <Text size="xs" c="dimmed">Requirements</Text>
                        <Text size="sm" fw={600}>
                          {framework.completed}/{framework.requirements}
                        </Text>
                      </div>
                      <div>
                        <Text size="xs" c="dimmed">Violations</Text>
                        <Text size="sm" fw={600} c={framework.violations > 0 ? 'red' : 'green'}>
                          {framework.violations}
                        </Text>
                      </div>
                      <div>
                        <Text size="xs" c="dimmed">Last Audit</Text>
                        <Text size="sm" fw={500}>
                          {new Date(framework.lastAudit).toLocaleDateString()}
                        </Text>
                      </div>
                    </Group>

                    <Badge size="sm" variant="light" color="gray">
                      {framework.category}
                    </Badge>
                  </Stack>
                </Card>
              ))}
            </SimpleGrid>
          </Tabs.Panel>

          <Tabs.Panel value="requirements" pt="xl">
            <Card style={neo.card} p="xl">
              <Title order={3} size="lg" fw={600} mb="lg">
                Upcoming Compliance Requirements
              </Title>
              <Stack gap="md">
                {upcomingRequirements.map((req, index) => (
                  <Card
                    key={index}
                    style={{
                      background: 'rgba(255, 255, 255, 0.6)',
                      border: '1px solid rgba(255, 255, 255, 0.2)',
                      borderRadius: '12px',
                    }}
                    p="md"
                  >
                    <Group justify="space-between" align="center">
                      <div>
                        <Text fw={600} size="sm">
                          {req.requirement}
                        </Text>
                        <Text size="xs" c="dimmed">
                          {req.framework} Framework
                        </Text>
                      </div>
                      <Group gap="sm">
                        <Badge
                          size="sm"
                          color={getPriorityColor(req.priority)}
                          variant="light"
                        >
                          {req.priority} priority
                        </Badge>
                        <Text size="xs" c="dimmed">
                          Due: {new Date(req.dueDate).toLocaleDateString()}
                        </Text>
                      </Group>
                    </Group>
                  </Card>
                ))}
              </Stack>
            </Card>
          </Tabs.Panel>

          <Tabs.Panel value="violations" pt="xl">
            <Card style={neo.card} p="xl">
              <Stack align="center" gap="md" py="xl">
                <IconAlertTriangle size={64} color="#f59e0b" />
                <Title order={3} c="dimmed">Active Compliance Issues</Title>
                <Text c="dimmed" ta="center">
                  Monitor and resolve compliance violations and policy breaches
                </Text>
                <Button leftSection={<IconEye size={16} />}>
                  View Issues
                </Button>
              </Stack>
            </Card>
          </Tabs.Panel>

          <Tabs.Panel value="reports" pt="xl">
            <Card style={neo.card} p="xl">
              <Stack align="center" gap="md" py="xl">
                <IconFileText size={64} color="#cbd5e1" />
                <Title order={3} c="dimmed">Compliance Audit Reports</Title>
                <Text c="dimmed" ta="center">
                  Generate comprehensive compliance reports for stakeholders
                </Text>
                <Button leftSection={<IconDownload size={16} />}>
                  Generate Report
                </Button>
              </Stack>
            </Card>
          </Tabs.Panel>
        </Tabs>
      </Stack>
    </Container>
  );
}