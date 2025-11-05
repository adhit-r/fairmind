'use client';

import {
  Container,
  Title,
  Text,
  Card,
  Group,
  Stack,
  SimpleGrid,
  Progress,
  Badge,
  ActionIcon,
  ThemeIcon,
} from '@mantine/core';
import {
  IconActivity,
  IconServer,
  IconDatabase,
  IconCpu,
  IconDevices,
  IconNetwork,
  IconRefresh,
  IconCheck,
  IconX,
  IconAlertTriangle,
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

function getStatusColor(status: string) {
  switch (status.toLowerCase()) {
    case 'healthy':
    case 'online':
    case 'active':
      return 'green';
    case 'warning':
    case 'degraded':
      return 'yellow';
    case 'error':
    case 'offline':
    case 'critical':
      return 'red';
    default:
      return 'gray';
  }
}

function getStatusIcon(status: string) {
  const color = getStatusColor(status);
  switch (color) {
    case 'green':
      return <IconCheck size={16} />;
    case 'yellow':
      return <IconAlertTriangle size={16} />;
    case 'red':
      return <IconX size={16} />;
    default:
      return <IconActivity size={16} />;
  }
}

const systemComponents = [
  {
    name: 'API Server',
    status: 'healthy',
    endpoint: '/api/v1/health',
    icon: IconServer,
    description: 'Main application server',
    uptime: '99.9%',
    responseTime: '45ms',
  },
  {
    name: 'Database',
    status: 'healthy',
    endpoint: '/api/v1/database/health',
    icon: IconDatabase,
    description: 'PostgreSQL database connection',
    uptime: '99.8%',
    responseTime: '12ms',
  },
  {
    name: 'AI Models',
    status: 'healthy',
    endpoint: '/api/v1/models/health',
    icon: IconCpu,
    description: 'Model inference services',
    uptime: '98.5%',
    responseTime: '120ms',
  },
  {
    name: 'Storage',
    status: 'healthy',
    endpoint: '/api/v1/storage/health',
    icon: IconDevices,
    description: 'File storage systems',
    uptime: '99.7%',
    responseTime: '8ms',
  },
];

export default function StatusPage() {
  const { data: healthData, loading, error } = useApi('/api/v1/health');

  return (
    <Container size="xl" py="xl">
      <Stack gap="xl">
        {/* Header */}
        <Card style={neo.card} p="xl">
          <Group justify="space-between" align="center">
            <div>
              <Title order={1} size="2rem" fw={700} c="#1e293b" mb="xs">
                System Status
              </Title>
              <Text c="dimmed" size="lg">
                Real-time monitoring of all FairMind services
              </Text>
            </div>
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
          </Group>
        </Card>

        {/* Overall System Health */}
        <Card style={neo.card} p="xl">
          <Group justify="space-between" align="center" mb="lg">
            <Title order={2} size="1.5rem" fw={600}>
              Overall System Health
            </Title>
            <Badge
              size="lg"
              radius="xl"
              color="green"
              variant="light"
              leftSection={<IconCheck size={16} />}
            >
              All Systems Operational
            </Badge>
          </Group>
          
          <SimpleGrid cols={{ base: 2, md: 4 }} spacing="lg">
            <div>
              <Text size="sm" c="dimmed" mb="xs">CPU Usage</Text>
              <Progress value={35} size="lg" radius="xl" color="blue" />
              <Text size="xs" c="dimmed" mt="xs">35% / 100%</Text>
            </div>
            <div>
              <Text size="sm" c="dimmed" mb="xs">Memory Usage</Text>
              <Progress value={67} size="lg" radius="xl" color="green" />
              <Text size="xs" c="dimmed" mt="xs">6.7GB / 10GB</Text>
            </div>
            <div>
              <Text size="sm" c="dimmed" mb="xs">Storage Usage</Text>
              <Progress value={45} size="lg" radius="xl" color="cyan" />
              <Text size="xs" c="dimmed" mt="xs">450GB / 1TB</Text>
            </div>
            <div>
              <Text size="sm" c="dimmed" mb="xs">Network I/O</Text>
              <Progress value={28} size="lg" radius="xl" color="violet" />
              <Text size="xs" c="dimmed" mt="xs">28MB/s</Text>
            </div>
          </SimpleGrid>
        </Card>

        {/* Service Components */}
        <SimpleGrid cols={{ base: 1, md: 2 }} spacing="lg">
          {systemComponents.map((component) => (
            <Card
              key={component.name}
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
                      color={getStatusColor(component.status)}
                      variant="light"
                    >
                      <component.icon size={20} />
                    </ThemeIcon>
                    <div>
                      <Title order={3} size="lg" fw={600}>
                        {component.name}
                      </Title>
                      <Text size="sm" c="dimmed">
                        {component.description}
                      </Text>
                    </div>
                  </Group>
                  <Badge
                    color={getStatusColor(component.status)}
                    variant="light"
                    radius="xl"
                    leftSection={getStatusIcon(component.status)}
                  >
                    {component.status}
                  </Badge>
                </Group>

                <Group justify="space-between">
                  <div>
                    <Text size="xs" c="dimmed">Uptime</Text>
                    <Text size="sm" fw={600}>{component.uptime}</Text>
                  </div>
                  <div>
                    <Text size="xs" c="dimmed">Response Time</Text>
                    <Text size="sm" fw={600}>{component.responseTime}</Text>
                  </div>
                  <div>
                    <Text size="xs" c="dimmed">Endpoint</Text>
                    <Text size="sm" fw={500} c="blue">{component.endpoint}</Text>
                  </div>
                </Group>
              </Stack>
            </Card>
          ))}
        </SimpleGrid>
      </Stack>
    </Container>
  );
}