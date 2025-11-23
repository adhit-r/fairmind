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
  Alert,
} from '@mantine/core';
import { LineChart, AreaChart } from '@mantine/charts';
import {
  IconActivity,
  IconTrendingUp,
  IconTrendingDown,
  IconRefresh,
  IconEye,
  IconBell,
  IconShield,
  IconCpu,
  IconServer,
  IconAlertTriangle,
  IconCheck,
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

// Mock real-time data - in production this would come from WebSocket or polling
const performanceData = [
  { time: '00:00', requests: 120, latency: 45, errors: 2 },
  { time: '00:05', requests: 134, latency: 52, errors: 1 },
  { time: '00:10', requests: 145, latency: 48, errors: 3 },
  { time: '00:15', requests: 156, latency: 41, errors: 0 },
  { time: '00:20', requests: 142, latency: 55, errors: 1 },
  { time: '00:25', requests: 167, latency: 43, errors: 2 },
];

const biasMetrics = [
  { time: '00:00', fairness: 85, bias: 15 },
  { time: '00:05', fairness: 87, bias: 13 },
  { time: '00:10', fairness: 84, bias: 16 },
  { time: '00:15', fairness: 89, bias: 11 },
  { time: '00:20', fairness: 86, bias: 14 },
  { time: '00:25', fairness: 91, bias: 9 },
];

const activeAlerts = [
  {
    id: 1,
    type: 'warning',
    title: 'Model Latency Increase',
    description: 'Response time increased by 15% in the last hour',
    time: '5 minutes ago',
    severity: 'medium',
  },
  {
    id: 2,
    type: 'info',
    title: 'New Model Deployed',
    description: 'Credit Risk Model v2.1 has been successfully deployed',
    time: '1 hour ago',
    severity: 'low',
  },
  {
    id: 3,
    type: 'error',
    title: 'Bias Threshold Exceeded',
    description: 'Gender bias detected in hiring model above 5% threshold',
    time: '2 hours ago',
    severity: 'high',
  },
];

const metrics = [
  {
    title: 'Active Models',
    value: '23',
    change: '+2',
    trend: 'up',
    icon: IconServer,
    color: 'blue',
  },
  {
    title: 'Requests/Min',
    value: '1,247',
    change: '+8.5%',
    trend: 'up',
    icon: IconActivity,
    color: 'green',
  },
  {
    title: 'Avg Latency',
    value: '47ms',
    change: '-3ms',
    trend: 'down',
    icon: IconCpu,
    color: 'cyan',
  },
  {
    title: 'Error Rate',
    value: '0.12%',
    change: '-0.05%',
    trend: 'down',
    icon: IconShield,
    color: 'red',
  },
];

export default function MonitoringPage() {
  const { data: monitoringData, loading, error } = useApi('/api/v1/monitoring/metrics');

  return (
    <Container size="xl" py="xl">
      <Stack gap="xl">
        {/* Header */}
        <Card style={neo.card} p="xl">
          <Group justify="space-between" align="center">
            <div>
              <Title order={1} size="2rem" fw={700} c="#1e293b" mb="xs">
                Real-time Monitoring
              </Title>
              <Text c="dimmed" size="lg">
                Live performance metrics and bias detection monitoring
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
              <ActionIcon
                size="lg"
                radius="xl"
                variant="light"
                color="green"
                style={{
                  background: 'rgba(34, 197, 94, 0.1)',
                  boxShadow: '4px 4px 8px rgba(34, 197, 94, 0.2), -4px -4px 8px rgba(255, 255, 255, 0.8)',
                }}
              >
                <IconEye size={20} />
              </ActionIcon>
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
            Unable to connect to monitoring service: {error?.message || 'Unknown error'}
          </Alert>
        )}

        {/* Key Metrics */}
        <SimpleGrid cols={{ base: 2, md: 4 }} spacing="lg">
          {metrics.map((metric) => (
            <Card
              key={metric.title}
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
                <Group justify="space-between">
                  <ThemeIcon
                    size="lg"
                    radius="xl"
                    color={metric.color}
                    variant="light"
                  >
                    <metric.icon size={20} />
                  </ThemeIcon>
                  {metric.trend === 'up' ? (
                    <IconTrendingUp size={16} color="green" />
                  ) : (
                    <IconTrendingDown size={16} color="red" />
                  )}
                </Group>
                
                <div>
                  <Text size="2xl" fw={700} c="#1e293b">
                    {metric.value}
                  </Text>
                  <Text size="sm" c="dimmed">
                    {metric.title}
                  </Text>
                </div>
                
                <Text
                  size="sm"
                  c={metric.trend === 'up' ? 'green' : 'red'}
                  fw={600}
                >
                  {metric.change}
                </Text>
              </Stack>
            </Card>
          ))}
        </SimpleGrid>

        {/* Performance Charts */}
        <SimpleGrid cols={{ base: 1, lg: 2 }} spacing="lg">
          <Card style={neo.card} p="xl">
            <Title order={3} size="lg" fw={600} mb="lg">
              Request Performance
            </Title>
            <AreaChart
              h={250}
              data={performanceData}
              dataKey="time"
              series={[
                { name: 'requests', color: 'blue.6' },
                { name: 'latency', color: 'cyan.6' },
              ]}
              curveType="natural"
              gridAxis="xy"
              withGradient
            />
          </Card>

          <Card style={neo.card} p="xl">
            <Title order={3} size="lg" fw={600} mb="lg">
              Bias & Fairness Metrics
            </Title>
            <LineChart
              h={250}
              data={biasMetrics}
              dataKey="time"
              series={[
                { name: 'fairness', color: 'green.6' },
                { name: 'bias', color: 'red.6' },
              ]}
              curveType="natural"
              gridAxis="xy"
            />
          </Card>
        </SimpleGrid>

        {/* Active Alerts */}
        <Card style={neo.card} p="xl">
          <Group justify="space-between" align="center" mb="lg">
            <Title order={3} size="lg" fw={600}>
              Active Alerts
            </Title>
            <ActionIcon
              size="sm"
              radius="xl"
              variant="light"
              color="blue"
            >
              <IconBell size={16} />
            </ActionIcon>
          </Group>
          
          <Stack gap="sm">
            {activeAlerts.map((alert) => (
              <Card
                key={alert.id}
                style={{
                  background: 'rgba(255, 255, 255, 0.8)',
                  backdropFilter: 'blur(10px)',
                  border: '1px solid rgba(255, 255, 255, 0.3)',
                  borderRadius: '12px',
                  boxShadow: '4px 4px 8px rgba(163, 177, 198, 0.2), -4px -4px 8px rgba(255, 255, 255, 0.8)',
                }}
                p="md"
              >
                <Group justify="space-between" align="flex-start">
                  <Group gap="sm" align="flex-start">
                    <ThemeIcon
                      size="sm"
                      radius="xl"
                      color={
                        alert.severity === 'high' ? 'red' :
                        alert.severity === 'medium' ? 'yellow' : 'blue'
                      }
                      variant="light"
                    >
                      {alert.type === 'error' ? (
                        <IconAlertTriangle size={14} />
                      ) : (
                        <IconCheck size={14} />
                      )}
                    </ThemeIcon>
                    <div>
                      <Text fw={600} size="sm">
                        {alert.title}
                      </Text>
                      <Text size="xs" c="dimmed">
                        {alert.description}
                      </Text>
                    </div>
                  </Group>
                  <Group gap="xs">
                    <Badge
                      size="xs"
                      radius="xl"
                      color={
                        alert.severity === 'high' ? 'red' :
                        alert.severity === 'medium' ? 'yellow' : 'blue'
                      }
                      variant="light"
                    >
                      {alert.severity}
                    </Badge>
                    <Text size="xs" c="dimmed">
                      {alert.time}
                    </Text>
                  </Group>
                </Group>
              </Card>
            ))}
          </Stack>
        </Card>
      </Stack>
    </Container>
  );
}