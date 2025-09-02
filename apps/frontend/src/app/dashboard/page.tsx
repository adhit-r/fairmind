'use client';

import {
  Container,
  Title,
  Text,
  Button,
  Group,
  Card,
  SimpleGrid,
  Stack,
  Badge,
  ThemeIcon,
  Box,
  Paper,
  Divider,
  Alert,
  RingProgress,
  Table,
  ActionIcon,
  Progress,
  Timeline,
  Modal,
  TextInput,
  Select,
  NumberInput,
  Checkbox,
  Textarea,
} from '@mantine/core';
import {
  IconBrain,
  IconShield,
  IconChartBar,
  IconSettings,
  IconArrowRight,
  IconUpload,
  IconTarget,
  IconAlertTriangle,
  IconCheck,
  IconX,
  IconEye,
  IconEdit,
  IconTrash,
  IconPlus,
  IconChevronUp,
  IconChevronDown,
  IconDatabase,
  IconFileText,
  IconClock,
  IconUser,
} from '@tabler/icons-react';
import { useState, useEffect } from 'react';

// Import API client for real data
import { apiClient, GovernanceMetrics, RecentActivity } from '@/lib/api'

// Dashboard data interface
interface DashboardData {
  stats: GovernanceMetrics
  alerts: Array<{ id: number; severity: string; message: string; model: string; timestamp: string }>
  recentModels: Array<{ id: number; name: string; status: string; riskScore: number; lastUpdated: string; type: string }>
  upcomingDeadlines: Array<{ id: number; title: string; deadline: string; priority: string; model: string }>
  recentActivity: RecentActivity[]
}

const mockAlerts = [
  {
    id: 1,
    severity: 'critical',
    message: 'Potential bias detected in credit-scoring-v2.1 model',
    model: 'credit-scoring-v2.1',
    timestamp: '2 hours ago',
  },
  {
    id: 2,
    severity: 'warning',
    message: 'Compliance deadline approaching for EU AI Act',
    model: 'fraud-detection-v3',
    timestamp: '1 day ago',
  },
  {
    id: 3,
    severity: 'info',
    message: 'New model assessment completed',
    model: 'recommendation-engine-v1',
    timestamp: '3 days ago',
  },
];

const mockRecentModels = [
  {
    id: 1,
    name: 'credit-scoring-v2.1',
    status: 'active',
    riskScore: 85,
    lastUpdated: '2 hours ago',
    type: 'Classification',
  },
  {
    id: 2,
    name: 'fraud-detection-v3',
    status: 'review',
    riskScore: 72,
    lastUpdated: '1 day ago',
    type: 'Anomaly Detection',
  },
  {
    id: 3,
    name: 'recommendation-engine-v1',
    status: 'active',
    riskScore: 45,
    lastUpdated: '3 days ago',
    type: 'Recommendation',
  },
];

const mockUpcomingDeadlines = [
  {
    id: 1,
    title: 'EU AI Act Compliance Review',
    deadline: '2024-02-15',
    priority: 'high',
    model: 'credit-scoring-v2.1',
  },
  {
    id: 2,
    title: 'NIST AI RMF Assessment',
    deadline: '2024-02-28',
    priority: 'medium',
    model: 'fraud-detection-v3',
  },
  {
    id: 3,
    title: 'GDPR Data Protection Audit',
    deadline: '2024-03-10',
    priority: 'high',
    model: 'all-models',
  },
];

export default function DashboardPage() {
  const [uploadModalOpened, setUploadModalOpened] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState<typeof mockAlerts[0] | null>(null);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch dashboard data from API
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        const [metrics, activity] = await Promise.all([
          apiClient.getGovernanceMetrics(),
          apiClient.getRecentActivity()
        ]);

        // Transform API data to dashboard format
        const transformedData: DashboardData = {
          stats: metrics,
          alerts: mockAlerts, // Keep mock alerts for now, replace with real API later
          recentModels: mockRecentModels, // Keep mock models for now, replace with real API later
          upcomingDeadlines: mockUpcomingDeadlines, // Keep mock deadlines for now, replace with real API later
          recentActivity: activity
        };

        setDashboardData(transformedData);
      } catch (err) {
        console.error('Failed to fetch dashboard data:', err);
        setError('Failed to load dashboard data');
        // Fallback to mock data
        setDashboardData({
          stats: {
            totalModels: 147,
            activeModels: 89,
            criticalRisks: 3,
            llmSafetyScore: 94,
            nistCompliance: 87
          },
          alerts: mockAlerts,
          recentModels: mockRecentModels,
          upcomingDeadlines: mockUpcomingDeadlines,
          recentActivity: []
        });
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'green';
      case 'review': return 'yellow';
      case 'inactive': return 'red';
      default: return 'gray';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'red';
      case 'medium': return 'yellow';
      case 'low': return 'green';
      default: return 'gray';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'red';
      case 'warning': return 'yellow';
      case 'info': return 'blue';
      default: return 'gray';
    }
  };

  if (loading) {
    return (
      <Box>
        <Paper bg="white" py="xl" mb="xl" withBorder>
          <Group justify="center" align="center">
            <Text size="lg" c="dark.6">Loading dashboard data...</Text>
          </Group>
        </Paper>
      </Box>
    );
  }

  if (error) {
    return (
      <Box>
        <Paper bg="white" py="xl" mb="xl" withBorder>
          <Group justify="center" align="center">
            <Alert color="red" title="Error" icon={<IconAlertTriangle size={16} />}>
              {error}
            </Alert>
          </Group>
        </Paper>
      </Box>
    );
  }

  return (
    <Box>
      {/* Page Header */}
      <Paper bg="white" py="xl" mb="xl" withBorder>
        <Group justify="space-between" align="center">
          <Stack gap="xs">
            <Title order={1} size="2.5rem" fw={600} c="dark.8">
              Dashboard
            </Title>
            <Text size="lg" c="dark.6">
              AI governance overview and quick actions
            </Text>
          </Stack>
          <Button 
            size="lg" 
            radius="sm" 
            leftSection={<IconUpload size="1.2rem" />}
            onClick={() => setUploadModalOpened(true)}
          >
            Upload New Model
          </Button>
        </Group>
      </Paper>

      {/* KPI Cards */}
      <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }} mb="xl">
        <Card withBorder p="md">
          <Group justify="space-between" mb="xs">
            <Text size="xs" c="dimmed">Total Models</Text>
            <IconChevronUp size={16} color="green" />
          </Group>
          <Text fw={700} size="xl">{dashboardData?.stats.totalModels || 0}</Text>
          <Text c="dimmed" size="xs">+12% this month</Text>
        </Card>

        <Card withBorder p="md">
          <Group justify="space-between" mb="xs">
            <Text size="xs" c="dimmed">Active Models</Text>
            <IconChevronUp size={16} color="green" />
          </Group>
          <Text fw={700} size="xl">{dashboardData?.stats.activeModels || 0}</Text>
          <Text c="dimmed" size="xs">Active in production</Text>
        </Card>

        <Card withBorder p="md">
          <Group justify="space-between" mb="xs">
            <Text size="xs" c="dimmed">Critical Risks</Text>
            <IconChevronDown size={16} color="red" />
          </Group>
          <Text fw={700} size="xl" c="red.7">{dashboardData?.stats.criticalRisks || 0}</Text>
          <Text c="dimmed" size="xs">-5% from last week</Text>
        </Card>

        <Card withBorder p="md">
          <Group justify="space-between" mb="xs">
            <Text size="xs" c="dimmed">LLM Safety Score</Text>
            <IconChevronUp size={16} color="green" />
          </Group>
          <Text fw={700} size="xl">{dashboardData?.stats.llmSafetyScore || 0}%</Text>
          <Text c="dimmed" size="xs">AI safety compliance</Text>
        </Card>
      </SimpleGrid>

      {/* Main Content Grid */}
      <SimpleGrid cols={{ base: 1, lg: 2 }} gap="xl" mb="xl">
        {/* Left Column - Priority Actions */}
        <Stack gap="xl">
          {/* Critical Alerts */}
          <Card withBorder>
            <Card.Section withBorder inheritPadding py="xs">
              <Group justify="space-between">
                <Text fw={500}>Critical Alerts</Text>
                <Badge color="red" variant="light">{mockAlerts.filter(a => a.severity === 'critical').length} Active</Badge>
              </Group>
            </Card.Section>
            <Stack gap="xs" p="md">
              {mockAlerts.map((alert) => (
                <Alert 
                  key={alert.id} 
                  color={getSeverityColor(alert.severity)} 
                  variant="light"
                  title={alert.model}
                  onClick={() => setSelectedAlert(alert)}
                  style={{ cursor: 'pointer' }}
                >
                  <Text size="sm">{alert.message}</Text>
                  <Text size="xs" c="dimmed" mt="xs">{alert.timestamp}</Text>
                </Alert>
              ))}
            </Stack>
          </Card>

          {/* Models Needing Review */}
          <Card withBorder>
            <Card.Section withBorder inheritPadding py="xs">
              <Group justify="space-between">
                <Text fw={500}>Models Needing Review</Text>
                <Button variant="subtle" size="sm">View All</Button>
              </Group>
            </Card.Section>
            <Table>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Model Name</Table.Th>
                  <Table.Th>Status</Table.Th>
                  <Table.Th>Risk Score</Table.Th>
                  <Table.Th>Actions</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {mockRecentModels.map((model) => (
                  <Table.Tr key={model.id}>
                    <Table.Td>
                      <Text fw={500} size="sm">{model.name}</Text>
                      <Text size="xs" c="dimmed">{model.type}</Text>
                    </Table.Td>
                    <Table.Td>
                      <Badge color={getStatusColor(model.status)} variant="light">
                        {model.status}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs">
                        <Text size="sm">{model.riskScore}</Text>
                        <RingProgress
                          size={24}
                          thickness={4}
                          sections={[{ value: model.riskScore, color: model.riskScore > 70 ? 'red' : 'green' }]}
                        />
                      </Group>
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs">
                        <ActionIcon variant="light" size="sm">
                          <IconEye size={16} />
                        </ActionIcon>
                        <ActionIcon variant="light" size="sm">
                          <IconEdit size={16} />
                        </ActionIcon>
                      </Group>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Card>

          {/* Upcoming Deadlines */}
          <Card withBorder>
            <Card.Section withBorder inheritPadding py="xs">
              <Group justify="space-between">
                <Text fw={500}>Upcoming Deadlines</Text>
                <Button variant="subtle" size="sm">View Calendar</Button>
              </Group>
            </Card.Section>
            <Stack gap="md" p="md">
              {mockUpcomingDeadlines.map((deadline) => (
                <Paper key={deadline.id} p="md" withBorder>
                  <Group justify="space-between" mb="xs">
                    <Text fw={500} size="sm">{deadline.title}</Text>
                    <Badge color={getPriorityColor(deadline.priority)} variant="light">
                      {deadline.priority}
                    </Badge>
                  </Group>
                  <Text size="sm" c="dark.6" mb="xs">
                    Due: {deadline.deadline}
                  </Text>
                  <Text size="xs" c="dimmed">
                    Model: {deadline.model}
                  </Text>
                </Paper>
              ))}
            </Stack>
          </Card>
        </Stack>

        {/* Right Column - Quick Access */}
        <Stack gap="xl">
          {/* Recent Activity */}
          <Card withBorder>
            <Card.Section withBorder inheritPadding py="xs">
              <Text fw={500}>Recent Activity</Text>
            </Card.Section>
            <Timeline p="md">
              {dashboardData?.recentActivity.slice(0, 3).map((activity, index) => (
                <Timeline.Item 
                  key={activity.id} 
                  bullet={<IconCheck size={12} />} 
                  title={activity.type}
                  color="green"
                >
                  <Text size="sm">{activity.description}</Text>
                  <Text size="xs" c="dimmed">{activity.timestamp}</Text>
                </Timeline.Item>
              )) || (
                <>
                  <Timeline.Item 
                    bullet={<IconCheck size={12} />} 
                    title="Model Assessment Completed"
                    color="green"
                  >
                    <Text size="sm">credit-scoring-v2.1 passed bias detection</Text>
                    <Text size="xs" c="dimmed">2 hours ago</Text>
                  </Timeline.Item>
                  <Timeline.Item 
                    bullet={<IconUpload size={12} />} 
                    title="New Model Uploaded"
                    color="blue"
                  >
                    <Text size="sm">fraud-detection-v3 uploaded for assessment</Text>
                    <Text size="xs" c="dimmed">1 day ago</Text>
                  </Timeline.Item>
                  <Timeline.Item 
                    bullet={<IconShield size={12} />} 
                    title="Security Scan Completed"
                    color="green"
                  >
                    <Text size="sm">All active models passed security validation</Text>
                    <Text size="xs" c="dimmed">3 days ago</Text>
                  </Timeline.Item>
                </>
              )}
            </Timeline>
          </Card>

          {/* Quick Actions */}
          <Card withBorder>
            <Card.Section withBorder inheritPadding py="xs">
              <Text fw={500}>Quick Actions</Text>
            </Card.Section>
            <Stack gap="md" p="md">
              <Button variant="light" fullWidth leftSection={<IconTarget size={16} />}>
                Run Bias Analysis
              </Button>
              <Button variant="light" fullWidth leftSection={<IconShield size={16} />}>
                Security Assessment
              </Button>
              <Button variant="light" fullWidth leftSection={<IconFileText size={16} />}>
                Generate Report
              </Button>
              <Button variant="light" fullWidth leftSection={<IconChartBar size={16} />}>
                View Analytics
              </Button>
            </Stack>
          </Card>

          {/* System Status */}
          <Card withBorder>
            <Card.Section withBorder inheritPadding py="xs">
              <Text fw={500}>System Status</Text>
            </Card.Section>
            <Stack gap="md" p="md">
              <Group justify="space-between">
                <Text size="sm">Database Connection</Text>
                <Badge color={dashboardData ? "green" : "red"} variant="light">
                  {dashboardData ? "Connected" : "Disconnected"}
                </Badge>
              </Group>
              <Group justify="space-between">
                <Text size="sm">Backend API</Text>
                <Badge color={dashboardData ? "green" : "red"} variant="light">
                  {dashboardData ? "Connected" : "Disconnected"}
                </Badge>
              </Group>
              <Group justify="space-between">
                <Text size="sm">AI Analysis Engine</Text>
                <Badge color="green" variant="light">Running</Badge>
              </Group>
              <Group justify="space-between">
                <Text size="sm">Security Scanner</Text>
                <Badge color="green" variant="light">Active</Badge>
              </Group>
            </Stack>
          </Card>
        </Stack>
      </SimpleGrid>

      {/* Upload Model Modal */}
      <Modal 
        opened={uploadModalOpened} 
        onClose={() => setUploadModalOpened(false)}
        title="Upload New Model"
        size="lg"
      >
        <Stack gap="md">
          <TextInput
            label="Model Name"
            placeholder="Enter model name"
            withAsterisk
          />
          <Select
            label="Model Type"
            placeholder="Select model type"
            data={['Classification', 'Regression', 'Anomaly Detection', 'Recommendation', 'Other']}
            withAsterisk
          />
          <TextInput
            label="Version"
            placeholder="e.g., 1.0.0"
            withAsterisk
          />
          <Textarea
            label="Description"
            placeholder="Brief description of the model"
            rows={3}
          />
          <NumberInput
            label="Fairness Threshold"
            placeholder="0.8"
            min={0}
            max={1}
            step={0.1}
            withAsterisk
          />
          <Checkbox
            label="I confirm this model complies with our ethical AI guidelines"
            withAsterisk
          />
          <Group justify="flex-end" mt="md">
            <Button variant="light" onClick={() => setUploadModalOpened(false)}>
              Cancel
            </Button>
            <Button leftSection={<IconUpload size={16} />}>
              Upload Model
            </Button>
          </Group>
        </Stack>
      </Modal>

      {/* Alert Detail Modal */}
      <Modal 
        opened={!!selectedAlert} 
        onClose={() => setSelectedAlert(null)}
        title="Alert Details"
        size="md"
      >
        {selectedAlert && (
          <Stack gap="md">
            <Alert 
              color={getSeverityColor(selectedAlert.severity)} 
              title={selectedAlert.model}
            >
              {selectedAlert.message}
            </Alert>
            <Text size="sm">
              <strong>Timestamp:</strong> {selectedAlert.timestamp}
            </Text>
            <Text size="sm">
              <strong>Severity:</strong> {selectedAlert.severity}
            </Text>
            <Group justify="flex-end" mt="md">
              <Button variant="light" onClick={() => setSelectedAlert(null)}>
                Close
              </Button>
              <Button leftSection={<IconEye size={16} />}>
                View Model
              </Button>
            </Group>
          </Stack>
        )}
      </Modal>
    </Box>
  );
}
