'use client';

import { useState, useEffect } from 'react';
import {
  Container,
  Title,
  Text,
  Card,
  Group,
  Stack,
  Badge,
  Button,
  SimpleGrid,
  Table,
  ActionIcon,
  Modal,
  TextInput,
  Select,
  Progress,
  Alert,
  Tabs,
  RingProgress,
  Slider,
  NumberInput,
  Switch,
} from '@mantine/core';
import {
  IconBrain,
  IconChartLine,
  IconSettings,
  IconAlertTriangle,
  IconCheck,
  IconX,
  IconEye,
  IconEdit,
  IconTrash,
  IconPlus,
  IconRefresh,
  IconScale,
  IconTarget,
  IconAnalyze,
  IconAdjustments,
} from '@tabler/icons-react';
import { useApi } from '@/hooks/useApi';

interface BiasTest {
  id: string;
  name: string;
  model: string;
  algorithm: string;
  status: 'running' | 'completed' | 'failed';
  progress: number;
  startTime: string;
  fairnessScore?: number;
  passedMetrics?: number;
  failedMetrics?: number;
}

interface BiasStats {
  totalTests: number;
  activeTests: number;
  passedTests: number;
  failedTests: number;
  averageFairnessScore: number;
  modelsWithBias: number;
}

export default function AdvancedBiasPage() {
  const [tests, setTests] = useState<BiasTest[]>([]);
  const [stats, setStats] = useState<BiasStats | null>(null);
  const [selectedTest, setSelectedTest] = useState<BiasTest | null>(null);
  const [loading, setLoading] = useState(true);
  const [modalOpened, setModalOpened] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  
  const { data, loading: apiLoading, error } = useApi('/api/bias');
  
  const fetchData = async (endpoint: string) => {
    try {
      const response = await fetch(`http://localhost:8000${endpoint}`);
      if (!response.ok) throw new Error('API call failed');
      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      return null;
    }
  };

  useEffect(() => {
    fetchBiasData();
  }, []);

  const fetchBiasData = async () => {
    try {
      setLoading(true);
      const [testsData, statsData] = await Promise.all([
        fetchData('/api/bias/tests'),
        fetchData('/api/bias/stats')
      ]);
      setTests(testsData || mockTests);
      setStats(statsData || mockStats);
    } catch (error) {
      console.error('Error fetching bias data:', error);
      setTests(mockTests);
      setStats(mockStats);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'green';
      case 'running': return 'blue';
      case 'failed': return 'red';
      default: return 'gray';
    }
  };

  const mockStats: BiasStats = {
    totalTests: 45,
    activeTests: 8,
    passedTests: 32,
    failedTests: 5,
    averageFairnessScore: 78.5,
    modelsWithBias: 3
  };

  const mockTests: BiasTest[] = [
    {
      id: '1',
      name: 'Sentiment Analysis Fairness Test',
      model: 'sentiment-analysis-v1',
      algorithm: 'demographic_parity',
      status: 'completed',
      progress: 100,
      startTime: '2024-01-20T09:00:00Z',
      fairnessScore: 82,
      passedMetrics: 3,
      failedMetrics: 1
    },
    {
      id: '2',
      name: 'Fraud Detection Bias Analysis',
      model: 'fraud-detection-v2',
      algorithm: 'equalized_odds',
      status: 'running',
      progress: 65,
      startTime: '2024-01-20T14:30:00Z'
    }
  ];

  if (loading) {
    return (
      <Container size="xl" py="xl">
        <Text>Loading Advanced Bias Detection...</Text>
      </Container>
    );
  }

  return (
    <Container size="xl" py="xl">
      <Group justify="space-between" mb="xl">
        <div>
          <Title order={1} c="white" mb="xs">
            Advanced Bias Detection
          </Title>
          <Text size="lg" c="dimmed">
            Configure and run sophisticated bias detection algorithms on AI models
          </Text>
        </div>
        <Group>
          <Button
            leftSection={<IconRefresh size={16} />}
            variant="outline"
            onClick={fetchBiasData}
          >
            Refresh Tests
          </Button>
          <Button
            leftSection={<IconPlus size={16} />}
            onClick={() => setModalOpened(true)}
          >
            New Bias Test
          </Button>
        </Group>
      </Group>

      {/* Statistics Cards */}
      <SimpleGrid cols={{ base: 1, md: 2, lg: 6 }} mb="xl">
        <Card className="neo-card" padding="lg">
          <Group justify="apart">
            <div>
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                Total Tests
              </Text>
              <Text fw={700} size="xl" c="white">
                {stats?.totalTests}
              </Text>
            </div>
            <IconBrain size={24} color="var(--mantine-color-blue-6)" />
          </Group>
        </Card>

        <Card className="neo-card" padding="lg">
          <Group justify="apart">
            <div>
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                Active Tests
              </Text>
              <Text fw={700} size="xl" c="blue">
                {stats?.activeTests}
              </Text>
            </div>
            <IconAnalyze size={24} color="var(--mantine-color-blue-6)" />
          </Group>
        </Card>

        <Card className="neo-card" padding="lg">
          <Group justify="apart">
            <div>
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                Passed Tests
              </Text>
              <Text fw={700} size="xl" c="green">
                {stats?.passedTests}
              </Text>
            </div>
            <IconCheck size={24} color="var(--mantine-color-green-6)" />
          </Group>
        </Card>

        <Card className="neo-card" padding="lg">
          <Group justify="apart">
            <div>
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                Failed Tests
              </Text>
              <Text fw={700} size="xl" c="red">
                {stats?.failedTests}
              </Text>
            </div>
            <IconX size={24} color="var(--mantine-color-red-6)" />
          </Group>
        </Card>

        <Card className="neo-card" padding="lg">
          <Group justify="apart">
            <div>
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                Avg Fairness Score
              </Text>
              <Text fw={700} size="xl" c="white">
                {stats?.averageFairnessScore}%
              </Text>
            </div>
            <IconScale size={24} color="var(--mantine-color-yellow-6)" />
          </Group>
          <Progress value={stats?.averageFairnessScore || 0} size="sm" mt="xs" color="yellow" />
        </Card>

        <Card className="neo-card" padding="lg">
          <Group justify="apart">
            <div>
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                Models with Bias
              </Text>
              <Text fw={700} size="xl" c="orange">
                {stats?.modelsWithBias}
              </Text>
            </div>
            <IconAlertTriangle size={24} color="var(--mantine-color-orange-6)" />
          </Group>
        </Card>
      </SimpleGrid>

      <Tabs value={activeTab} onChange={(value) => setActiveTab(value || 'overview')}>
        <Tabs.List>
          <Tabs.Tab value="overview" leftSection={<IconBrain size={16} />}>
            Test Overview
          </Tabs.Tab>
          <Tabs.Tab value="algorithms" leftSection={<IconSettings size={16} />}>
            Algorithms
          </Tabs.Tab>
          <Tabs.Tab value="metrics" leftSection={<IconChartLine size={16} />}>
            Metrics Dashboard
          </Tabs.Tab>
          <Tabs.Tab value="configuration" leftSection={<IconAdjustments size={16} />}>
            Configuration
          </Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="overview" pt="xl">
          <Card className="neo-card" padding="lg">
            <Group justify="space-between" mb="md">
              <Title order={3} c="white">Bias Detection Tests</Title>
              <Group>
                <Select
                  placeholder="Filter by status"
                  data={['All', 'Running', 'Completed', 'Failed']}
                  w={150}
                />
                <Select
                  placeholder="Filter by model"
                  data={['All', 'sentiment-analysis-v1', 'fraud-detection-v2']}
                  w={200}
                />
              </Group>
            </Group>

            <Table striped highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Test Name</Table.Th>
                  <Table.Th>Model</Table.Th>
                  <Table.Th>Algorithm</Table.Th>
                  <Table.Th>Status</Table.Th>
                  <Table.Th>Progress</Table.Th>
                  <Table.Th>Fairness Score</Table.Th>
                  <Table.Th>Actions</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {tests.map((test) => (
                  <Table.Tr key={test.id}>
                    <Table.Td>
                      <Text fw={500} c="white">{test.name}</Text>
                    </Table.Td>
                    <Table.Td>
                      <Text c="white">{test.model}</Text>
                    </Table.Td>
                    <Table.Td>
                      <Badge variant="light" size="sm">
                        {test.algorithm.replace('_', ' ')}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <Badge color={getStatusColor(test.status)} variant="light">
                        {test.status}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <RingProgress
                        size={40}
                        thickness={4}
                        sections={[{ value: test.progress, color: 'blue' }]}
                        label={
                          <Text size="xs" ta="center">
                            {test.progress}%
                          </Text>
                        }
                      />
                    </Table.Td>
                    <Table.Td>
                      <Text c={test.fairnessScore ? (test.fairnessScore > 70 ? 'green' : 'orange') : 'dimmed'} fw={500}>
                        {test.fairnessScore || 'N/A'}
                        {test.fairnessScore && '%'}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs">
                        <ActionIcon variant="subtle" onClick={() => { setSelectedTest(test); setModalOpened(true); }}>
                          <IconEye size={16} />
                        </ActionIcon>
                        <ActionIcon variant="subtle">
                          <IconEdit size={16} />
                        </ActionIcon>
                        <ActionIcon variant="subtle" color="red">
                          <IconTrash size={16} />
                        </ActionIcon>
                      </Group>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Card>
        </Tabs.Panel>

        <Tabs.Panel value="algorithms" pt="xl">
          <SimpleGrid cols={{ base: 1, md: 2 }} spacing="md">
            <Card className="neo-card" padding="lg">
              <Group justify="space-between" mb="md">
                <div>
                  <Text fw={500} c="white" size="lg">Demographic Parity</Text>
                  <Text c="dimmed" size="sm">Equal positive prediction rates across groups</Text>
                </div>
                <IconBrain size={32} color="var(--mantine-color-blue-6)" />
              </Group>
              <Group justify="space-between" mt="md">
                <Button variant="outline" size="sm" leftSection={<IconSettings size={14} />}>
                  Configure
                </Button>
                <Button variant="light" size="sm" leftSection={<IconTarget size={14} />}>
                  Run Test
                </Button>
              </Group>
            </Card>

            <Card className="neo-card" padding="lg">
              <Group justify="space-between" mb="md">
                <div>
                  <Text fw={500} c="white" size="lg">Equalized Odds</Text>
                  <Text c="dimmed" size="sm">Equal TPR and FPR across groups</Text>
                </div>
                <IconBrain size={32} color="var(--mantine-color-blue-6)" />
              </Group>
              <Group justify="space-between" mt="md">
                <Button variant="outline" size="sm" leftSection={<IconSettings size={14} />}>
                  Configure
                </Button>
                <Button variant="light" size="sm" leftSection={<IconTarget size={14} />}>
                  Run Test
                </Button>
              </Group>
            </Card>
          </SimpleGrid>
        </Tabs.Panel>

        <Tabs.Panel value="metrics" pt="xl">
          <Card className="neo-card" padding="lg">
            <Title order={4} c="white" mb="md">Model Fairness Scores</Title>
            <Stack>
              <Group justify="space-between">
                <Text size="sm" c="white">Sentiment Analysis</Text>
                <Group gap="xs">
                  <Progress value={82} w={100} size="sm" color="green" />
                  <Text size="sm" c="green">82%</Text>
                </Group>
              </Group>
              <Group justify="space-between">
                <Text size="sm" c="white">Fraud Detection</Text>
                <Group gap="xs">
                  <Progress value={65} w={100} size="sm" color="orange" />
                  <Text size="sm" c="orange">65%</Text>
                </Group>
              </Group>
            </Stack>
          </Card>
        </Tabs.Panel>

        <Tabs.Panel value="configuration" pt="xl">
          <Card className="neo-card" padding="lg">
            <Title order={3} c="white" mb="md">Global Configuration</Title>
            <SimpleGrid cols={{ base: 1, md: 2 }} spacing="xl">
              <Stack>
                <Text fw={500} c="white">Default Thresholds</Text>
                <Group justify="space-between">
                  <Text size="sm" c="white">Demographic Parity</Text>
                  <Slider defaultValue={10} min={1} max={20} w={200} />
                </Group>
                <Group justify="space-between">
                  <Text size="sm" c="white">Equalized Odds</Text>
                  <Slider defaultValue={8} min={1} max={20} w={200} />
                </Group>
              </Stack>
              <Stack>
                <NumberInput label="Default Sample Size" defaultValue={10000} min={1000} />
                <NumberInput label="Cross-validation Folds" defaultValue={5} min={3} max={10} />
                <Switch label="Auto-remediation" defaultChecked={false} />
              </Stack>
            </SimpleGrid>
            <Group justify="flex-end" mt="xl">
              <Button variant="outline">Reset</Button>
              <Button>Save</Button>
            </Group>
          </Card>
        </Tabs.Panel>
      </Tabs>

      {/* Test Modal */}
      <Modal
        opened={modalOpened}
        onClose={() => { setModalOpened(false); setSelectedTest(null); }}
        title={selectedTest ? "Test Details" : "Create New Bias Test"}
        size="lg"
      >
        <Stack>
          <TextInput label="Test Name" placeholder="Enter test name" defaultValue={selectedTest?.name} />
          <Group grow>
            <Select label="Model" data={['sentiment-analysis-v1', 'fraud-detection-v2']} defaultValue={selectedTest?.model} />
            <Select label="Algorithm" data={['demographic_parity', 'equalized_odds']} defaultValue={selectedTest?.algorithm} />
          </Group>
          {selectedTest?.fairnessScore && (
            <Alert icon={<IconCheck size={16} />} color="green">
              Fairness Score: {selectedTest.fairnessScore}% | Passed: {selectedTest.passedMetrics} | Failed: {selectedTest.failedMetrics}
            </Alert>
          )}
          <Group justify="flex-end">
            <Button variant="outline" onClick={() => setModalOpened(false)}>Cancel</Button>
            <Button>{selectedTest ? 'Update Test' : 'Create Test'}</Button>
          </Group>
        </Stack>
      </Modal>
    </Container>
  );
}