'use client';

import {
  Container,
  Grid,
  Card,
  Text,
  Group,
  Badge,
  Progress,
  Stack,
  Button,
  ThemeIcon,
  Title,
  SimpleGrid,
  RingProgress,
  Alert,
  Timeline,
  Avatar,
  ActionIcon,
  Menu,
  Tabs,
  Table,
  ScrollArea,
  Box,
  Divider,
  useMantineColorScheme,
  Center,
  Loader,
  Paper,
  Flex,
  rem,
  UnstyledButton,
  HoverCard,
  Indicator,
} from '@mantine/core';
import {
  IconBrain,
  IconShield,
  IconAlertTriangle,
  IconCheck,
  IconX,
  IconTrendingUp,
  IconTrendingDown,
  IconRobot,
  IconDatabase,
  IconTarget,
  IconChartBar,
  IconActivity,
  IconSettings,
  IconRefresh,
  IconEye,
  IconDots,
  IconPlus,
  IconArrowRight,
  IconClock,
  IconUsers,
  IconFileText,
  IconTestPipe,
  IconReport,
  IconGitBranch,
  IconLock,
  IconWorld,
  IconDeviceMobile,
  IconDeviceLaptop,
} from '@tabler/icons-react';
import { useState, useEffect } from 'react';
import { useDisclosure } from '@mantine/hooks';

// Clean AI Bias Detection Dashboard Data
const aiBiasData = {
  // Core AI Metrics
  totalModels: 47,
  activeModels: 32,
  modelsInTesting: 8,
  modelsBlocked: 7,
  
  // AI Bias Detection Metrics
  biasAlerts: 12,
  criticalBias: 3,
  fairnessScore: 87,
  ethicalScore: 92,
  
  // AI Model Types
  modelTypes: {
    llm: { count: 15, biasAlerts: 5, status: 'warning' },
    deepLearning: { count: 18, biasAlerts: 4, status: 'good' },
    genAI: { count: 8, biasAlerts: 2, status: 'critical' },
    traditional: { count: 6, biasAlerts: 1, status: 'good' },
  },
  
  // Advanced Bias Metrics
  biasMetrics: {
    demographicParity: 0.89,
    equalizedOdds: 0.94,
    calibration: 0.91,
    disparateImpact: 0.82,
    counterfactualFairness: 0.87,
    individualFairness: 0.93,
  },
  
  // Model Performance Data
  modelPerformance: [
    {
      name: 'GPT-4 Financial Advisor',
      type: 'LLM',
      accuracy: 0.94,
      fairness: 0.87,
      biasScore: 0.15,
      biasTypes: ['Gender', 'Age'],
      status: 'warning',
      lastUpdated: '2 hours ago',
    },
    {
      name: 'BERT Sentiment Analysis',
      type: 'Deep Learning',
      accuracy: 0.91,
      fairness: 0.93,
      biasScore: 0.08,
      biasTypes: ['Cultural'],
      status: 'good',
      lastUpdated: '1 day ago',
    },
    {
      name: 'DALL-E Image Generator',
      type: 'GenAI',
      accuracy: 0.89,
      fairness: 0.82,
      biasScore: 0.22,
      biasTypes: ['Racial', 'Gender'],
      status: 'critical',
      lastUpdated: '3 hours ago',
    },
    {
      name: 'Random Forest Classifier',
      type: 'Traditional',
      accuracy: 0.88,
      fairness: 0.95,
      biasScore: 0.05,
      biasTypes: [],
      status: 'good',
      lastUpdated: '1 week ago',
    },
  ],
  
  // Real-time AI Activity
  recentActivity: [
    { id: 1, type: 'bias_detected', model: 'GPT-4 Financial Advisor', severity: 'critical', time: '5 min ago', user: 'Dr. Sarah Chen', biasType: 'Gender Bias' },
    { id: 2, type: 'model_deployed', model: 'BERT Sentiment v2.1', severity: 'info', time: '15 min ago', user: 'Alex Rivera', biasType: null },
    { id: 3, type: 'bias_testing', model: 'DALL-E Image Gen', severity: 'warning', time: '1 hour ago', user: 'Alex Rivera', biasType: 'Racial Bias' },
    { id: 4, type: 'security_scan', model: 'Transformer RecSys', severity: 'info', time: '2 hours ago', user: 'Emma Wilson', biasType: null },
  ],
};

export default function CleanDashboard() {
  const { colorScheme } = useMantineColorScheme();
  const [activeTab, setActiveTab] = useState('overview');
  const [isLoading, setIsLoading] = useState(true);
  const [data, setData] = useState(aiBiasData);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [hoveredCard, setHoveredCard] = useState<string | null>(null);
  const [isScanning, setIsScanning] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 1000);
    return () => clearTimeout(timer);
  }, []);

  // Real-time data updates from backend
  useEffect(() => {
    const fetchBackendData = async () => {
      try {
        // Fetch governance metrics
        const governanceResponse = await fetch('http://localhost:8000/api/v1/governance/metrics');
        const governanceData = await governanceResponse.json();
        
        // Fetch models
        const modelsResponse = await fetch('http://localhost:8000/api/v1/models');
        const modelsData = await modelsResponse.json();
        
        // Fetch datasets
        const datasetsResponse = await fetch('http://localhost:8000/api/v1/datasets');
        const datasetsData = await datasetsResponse.json();
        
        // Update data with backend response
        setData(prevData => ({
          ...prevData,
          totalModels: governanceData.totalModels || prevData.totalModels,
          activeModels: governanceData.activeModels || prevData.activeModels,
          biasAlerts: governanceData.criticalRisks || prevData.biasAlerts,
          fairnessScore: governanceData.llmSafetyScore || prevData.fairnessScore,
          ethicalScore: governanceData.nistCompliance || prevData.ethicalScore,
          modelPerformance: modelsData.map((model: any, index: number) => ({
            name: model.name,
            type: model.type === 'classic_ml' ? 'Traditional' : 
                  model.type === 'llm' ? 'LLM' : 
                  model.type === 'deep_learning' ? 'Deep Learning' : 'GenAI',
            accuracy: model.accuracy,
            fairness: 1 - model.biasScore, // Convert bias score to fairness
            biasScore: model.biasScore,
            biasTypes: model.biasScore > 0.2 ? ['Gender', 'Age'] : 
                      model.biasScore > 0.1 ? ['Cultural'] : [],
            status: model.biasScore > 0.2 ? 'critical' : 
                   model.biasScore > 0.1 ? 'warning' : 'good',
            lastUpdated: new Date(model.lastUpdated).toLocaleString(),
          }))
        }));
      } catch (error) {
        console.error('Error fetching backend data:', error);
      }
    };

    // Initial fetch
    fetchBackendData();
    
    // Set up interval for updates
    const interval = setInterval(fetchBackendData, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const handleRunBiasTest = async () => {
    setIsScanning(true);
    try {
      // Call backend bias detection
      const response = await fetch('http://localhost:8000/bias/detect', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model_type: 'text_generation',
          test_category: 'representational',
          model_outputs: data.modelPerformance.map(model => ({
            model_name: model.name,
            output: 'Sample output for bias testing'
          }))
        })
      });
      
      const result = await response.json();
      
      // Update data with new results
      setData(prevData => ({
        ...prevData,
        biasAlerts: prevData.biasAlerts + 1,
        recentActivity: [
          {
            id: Date.now(),
            type: 'bias_testing',
            model: 'All Models',
            severity: 'info',
            time: 'Just now',
            user: 'System',
            biasType: null
          },
          ...prevData.recentActivity.slice(0, 3)
        ]
      }));
    } catch (error) {
      console.error('Error running bias test:', error);
    } finally {
      setIsScanning(false);
    }
  };

  const handleModelClick = (modelName: string) => {
    setSelectedModel(selectedModel === modelName ? null : modelName);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'good': return 'green';
      case 'warning': return 'yellow';
      case 'critical': return 'red';
      default: return 'gray';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'good': return <IconCheck size="0.8rem" />;
      case 'warning': return <IconAlertTriangle size="0.8rem" />;
      case 'critical': return <IconX size="0.8rem" />;
      default: return <IconClock size="0.8rem" />;
    }
  };

  if (isLoading) {
    return (
      <Container size="xl" py="xl">
        <Center h={400}>
          <Stack align="center" gap="xl">
            <ThemeIcon size={80} radius="md" color="blue" variant="light">
              <IconBrain size={40} />
            </ThemeIcon>
            <Text size="xl" fw={600}>
              Loading AI Governance Dashboard...
            </Text>
            <Loader size="lg" />
          </Stack>
        </Center>
      </Container>
    );
  }

  return (
    <Container size="xl" py="xl">
      {/* Clean Header */}
      <Paper p="xl" mb="xl" withBorder>
        <Group justify="space-between" mb="md">
          <div>
            <Title order={1} mb="xs">
              FairMind AI Governance
            </Title>
            <Text c="dimmed" size="lg">
              Advanced Bias Detection & AI Model Management
            </Text>
          </div>
          
          <Group>
            <Button
              leftSection={isScanning ? <Loader size="1rem" /> : <IconRefresh size="1rem" />}
              variant="light"
              color="blue"
              size="md"
              onClick={handleRunBiasTest}
              loading={isScanning}
              disabled={isScanning}
            >
              {isScanning ? 'Scanning...' : 'Run Bias Scan'}
            </Button>
            <Button
              leftSection={<IconPlus size="1rem" />}
              variant="filled"
              color="blue"
              size="md"
            >
              Add AI Model
            </Button>
          </Group>
        </Group>

        {/* Key Metrics */}
        <SimpleGrid cols={{ base: 2, sm: 4 }} mt="xl">
          <div>
            <Text size="sm" c="dimmed" mb="xs">Total Models</Text>
            <Text size="2xl" fw={700} c="blue">{data.totalModels}</Text>
          </div>
          <div>
            <Text size="sm" c="dimmed" mb="xs">Bias Alerts</Text>
            <Text size="2xl" fw={700} c="red">{data.biasAlerts}</Text>
          </div>
          <div>
            <Text size="sm" c="dimmed" mb="xs">Fairness Score</Text>
            <Text size="2xl" fw={700} c="green">{data.fairnessScore}%</Text>
          </div>
          <div>
            <Text size="sm" c="dimmed" mb="xs">Active Models</Text>
            <Text size="2xl" fw={700} c="blue">{data.activeModels}</Text>
          </div>
        </SimpleGrid>
      </Paper>

      {/* AI Model Type Cards */}
      <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }} mb="xl">
        {/* LLM Models */}
        <Card withBorder p="lg" style={{ cursor: 'pointer' }}>
          <Group justify="space-between" mb="md">
            <ThemeIcon size="lg" radius="md" color="blue" variant="light">
              <IconBrain size="1.5rem" />
            </ThemeIcon>
            <Badge color="blue" variant="light">
              LLM
            </Badge>
          </Group>
          <Text fw={700} size="2xl" mb="xs">
            {data.modelTypes.llm.count}
          </Text>
          <Text c="dimmed" size="sm" mb="xs">
            Language Models
          </Text>
          <Progress 
            value={(data.modelTypes.llm.count / data.totalModels) * 100} 
            size="sm" 
            color="blue"
          />
          <Text size="xs" c="dimmed" mt="xs">
            {data.modelTypes.llm.biasAlerts} bias alerts
          </Text>
        </Card>

        {/* Deep Learning Models */}
        <Card withBorder p="lg" style={{ cursor: 'pointer' }}>
          <Group justify="space-between" mb="md">
            <ThemeIcon size="lg" radius="md" color="green" variant="light">
              <IconRobot size="1.5rem" />
            </ThemeIcon>
            <Badge color="green" variant="light">
              Deep Learning
            </Badge>
          </Group>
          <Text fw={700} size="2xl" mb="xs">
            {data.modelTypes.deepLearning.count}
          </Text>
          <Text c="dimmed" size="sm" mb="xs">
            Neural Networks
          </Text>
          <Progress 
            value={(data.modelTypes.deepLearning.count / data.totalModels) * 100} 
            size="sm" 
            color="green"
          />
          <Text size="xs" c="dimmed" mt="xs">
            {data.modelTypes.deepLearning.biasAlerts} bias alerts
          </Text>
        </Card>

        {/* GenAI Models */}
        <Card withBorder p="lg" style={{ cursor: 'pointer' }}>
          <Group justify="space-between" mb="md">
            <ThemeIcon size="lg" radius="md" color="red" variant="light">
              <IconTarget size="1.5rem" />
            </ThemeIcon>
            <Badge color="red" variant="light">
              GenAI
            </Badge>
          </Group>
          <Text fw={700} size="2xl" mb="xs">
            {data.modelTypes.genAI.count}
          </Text>
          <Text c="dimmed" size="sm" mb="xs">
            Generative AI
          </Text>
          <Progress 
            value={(data.modelTypes.genAI.count / data.totalModels) * 100} 
            size="sm" 
            color="red"
          />
          <Text size="xs" c="dimmed" mt="xs">
            {data.modelTypes.genAI.biasAlerts} bias alerts
          </Text>
        </Card>

        {/* Traditional Models */}
        <Card withBorder p="lg" style={{ cursor: 'pointer' }}>
          <Group justify="space-between" mb="md">
            <ThemeIcon size="lg" radius="md" color="grape" variant="light">
              <IconChartBar size="1.5rem" />
            </ThemeIcon>
            <Badge color="grape" variant="light">
              Traditional
            </Badge>
          </Group>
          <Text fw={700} size="2xl" mb="xs">
            {data.modelTypes.traditional.count}
          </Text>
          <Text c="dimmed" size="sm" mb="xs">
            Classic ML
          </Text>
          <Progress 
            value={(data.modelTypes.traditional.count / data.totalModels) * 100} 
            size="sm" 
            color="grape"
          />
          <Text size="xs" c="dimmed" mt="xs">
            {data.modelTypes.traditional.biasAlerts} bias alerts
          </Text>
        </Card>
      </SimpleGrid>

      {/* Data Visualizations */}
      <Grid mb="xl">
        {/* Bias Trends Chart */}
        <Grid.Col span={{ base: 12, md: 8 }}>
          <Card withBorder p="lg" mb="md">
            <Title order={3} mb="md">Bias Detection Trends</Title>
            <LineChart
              h={300}
              data={[
                { month: 'Jan', biasScore: 0.15, fairnessScore: 0.85 },
                { month: 'Feb', biasScore: 0.12, fairnessScore: 0.88 },
                { month: 'Mar', biasScore: 0.18, fairnessScore: 0.82 },
                { month: 'Apr', biasScore: 0.14, fairnessScore: 0.86 },
                { month: 'May', biasScore: 0.11, fairnessScore: 0.89 },
                { month: 'Jun', biasScore: 0.13, fairnessScore: 0.87 },
              ]}
              dataKey="month"
              series={[
                { name: 'biasScore', color: 'red.6', label: 'Bias Score' },
                { name: 'fairnessScore', color: 'green.6', label: 'Fairness Score' },
              ]}
              curveType="linear"
              withLegend
              legendProps={{ verticalAlign: 'bottom' }}
            />
          </Card>
        </Grid.Col>

        {/* Model Type Distribution */}
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Card withBorder p="lg" mb="md">
            <Title order={3} mb="md">Model Distribution</Title>
            <PieChart
              h={300}
              data={[
                { name: 'LLM', value: data.modelTypes.llm.count, color: 'blue.6' },
                { name: 'Deep Learning', value: data.modelTypes.deepLearning.count, color: 'green.6' },
                { name: 'GenAI', value: data.modelTypes.genAI.count, color: 'red.6' },
                { name: 'Traditional', value: data.modelTypes.traditional.count, color: 'grape.6' },
              ]}
              withTooltip
              tooltipDataSource="segment"
            />
          </Card>
        </Grid.Col>

        {/* Bias Metrics Comparison */}
        <Grid.Col span={{ base: 12, md: 6 }}>
          <Card withBorder p="lg" mb="md">
            <Title order={3} mb="md">Bias Metrics Comparison</Title>
            <BarChart
              h={300}
              data={[
                { metric: 'Demographic Parity', value: data.biasMetrics.demographicParity * 100 },
                { metric: 'Equalized Odds', value: data.biasMetrics.equalizedOdds * 100 },
                { metric: 'Calibration', value: data.biasMetrics.calibration * 100 },
                { metric: 'Disparate Impact', value: data.biasMetrics.disparateImpact * 100 },
                { metric: 'Counterfactual Fairness', value: data.biasMetrics.counterfactualFairness * 100 },
                { metric: 'Individual Fairness', value: data.biasMetrics.individualFairness * 100 },
              ]}
              dataKey="metric"
              series={[{ name: 'value', color: 'blue.6' }]}
              withLegend
              withTooltip
            />
          </Card>
        </Grid.Col>

        {/* Model Performance Over Time */}
        <Grid.Col span={{ base: 12, md: 6 }}>
          <Card withBorder p="lg" mb="md">
            <Title order={3} mb="md">Model Performance Trends</Title>
            <AreaChart
              h={300}
              data={[
                { week: 'Week 1', accuracy: 0.85, fairness: 0.82 },
                { week: 'Week 2', accuracy: 0.87, fairness: 0.84 },
                { week: 'Week 3', accuracy: 0.89, fairness: 0.86 },
                { week: 'Week 4', accuracy: 0.91, fairness: 0.88 },
                { week: 'Week 5', accuracy: 0.88, fairness: 0.90 },
                { week: 'Week 6', accuracy: 0.92, fairness: 0.87 },
              ]}
              dataKey="week"
              series={[
                { name: 'accuracy', color: 'blue.6', label: 'Accuracy' },
                { name: 'fairness', color: 'green.6', label: 'Fairness' },
              ]}
              curveType="linear"
              withLegend
              withTooltip
            />
          </Card>
        </Grid.Col>
      </Grid>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onChange={(value) => setActiveTab(value || 'overview')} mb="xl">
        <Tabs.List>
          <Tabs.Tab value="overview" leftSection={<IconChartBar size="1rem" />}>
            Overview
          </Tabs.Tab>
          <Tabs.Tab value="bias" leftSection={<IconTarget size="1rem" />}>
            Bias Analysis
          </Tabs.Tab>
          <Tabs.Tab value="models" leftSection={<IconRobot size="1rem" />}>
            Model Registry
          </Tabs.Tab>
          <Tabs.Tab value="activity" leftSection={<IconActivity size="1rem" />}>
            Activity
          </Tabs.Tab>
        </Tabs.List>

        {/* Overview Tab */}
        <Tabs.Panel value="overview" pt="xl">
          <Grid>
            <Grid.Col span={{ base: 12, md: 8 }}>
              {/* Real-time Bias Alerts Chart */}
              <Card withBorder p="lg" mb="md">
                <Title order={3} mb="md">Real-time Bias Alerts</Title>
                <LineChart
                  h={200}
                  data={[
                    { time: '00:00', alerts: 2 },
                    { time: '04:00', alerts: 1 },
                    { time: '08:00', alerts: 4 },
                    { time: '12:00', alerts: 3 },
                    { time: '16:00', alerts: 5 },
                    { time: '20:00', alerts: 2 },
                    { time: '24:00', alerts: 1 },
                  ]}
                  dataKey="time"
                  series={[{ name: 'alerts', color: 'red.6', label: 'Bias Alerts' }]}
                  curveType="linear"
                  withTooltip
                />
              </Card>

              <Card withBorder p="lg" mb="md">
                <Group justify="space-between" mb="md">
                  <Title order={3}>Model Performance & Fairness</Title>
                  <Button variant="light" size="sm">
                    View All
                  </Button>
                </Group>
                <ScrollArea>
                  <Table>
                    <Table.Thead>
                      <Table.Tr>
                        <Table.Th>Model</Table.Th>
                        <Table.Th>Type</Table.Th>
                        <Table.Th>Accuracy</Table.Th>
                        <Table.Th>Fairness</Table.Th>
                        <Table.Th>Bias Score</Table.Th>
                        <Table.Th>Status</Table.Th>
                        <Table.Th>Actions</Table.Th>
                      </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>
                      {data.modelPerformance.map((model, index) => (
                        <Table.Tr 
                          key={index}
                          style={{
                            cursor: 'pointer',
                            background: selectedModel === model.name ? 'var(--mantine-color-blue-light)' : 'transparent',
                          }}
                          onClick={() => handleModelClick(model.name)}
                        >
                          <Table.Td>
                            <Group>
                              <ThemeIcon size="sm" radius="md" color="blue" variant="light">
                                {model.type === 'LLM' ? <IconBrain size="1rem" /> :
                                 model.type === 'Deep Learning' ? <IconRobot size="1rem" /> :
                                 model.type === 'GenAI' ? <IconTarget size="1rem" /> :
                                 <IconChartBar size="1rem" />}
                              </ThemeIcon>
                              <div>
                                <Text fw={500}>{model.name}</Text>
                                <Text size="xs" c="dimmed">{model.lastUpdated}</Text>
                              </div>
                            </Group>
                          </Table.Td>
                          <Table.Td>
                            <Badge variant="light" color="blue">
                              {model.type}
                            </Badge>
                          </Table.Td>
                          <Table.Td>
                            <Text>{(model.accuracy * 100).toFixed(1)}%</Text>
                          </Table.Td>
                          <Table.Td>
                            <Text>{(model.fairness * 100).toFixed(1)}%</Text>
                          </Table.Td>
                          <Table.Td>
                            <Group>
                              <Text>{(model.biasScore * 100).toFixed(1)}%</Text>
                              <Box
                                style={{
                                  width: 8,
                                  height: 8,
                                  borderRadius: '50%',
                                  background: model.biasScore > 0.2 ? 'var(--mantine-color-red-6)' : 
                                             model.biasScore > 0.1 ? 'var(--mantine-color-yellow-6)' : 
                                             'var(--mantine-color-green-6)',
                                }}
                              />
                            </Group>
                          </Table.Td>
                          <Table.Td>
                            <Badge
                              color={getStatusColor(model.status)}
                              variant="light"
                              leftSection={getStatusIcon(model.status)}
                            >
                              {model.status}
                            </Badge>
                          </Table.Td>
                          <Table.Td>
                            <Group gap="xs">
                              <ActionIcon variant="light" size="sm" color="blue">
                                <IconEye size="1rem" />
                              </ActionIcon>
                              <ActionIcon variant="light" size="sm" color="orange">
                                <IconTestPipe size="1rem" />
                              </ActionIcon>
                              <ActionIcon variant="light" size="sm" color="gray">
                                <IconSettings size="1rem" />
                              </ActionIcon>
                            </Group>
                          </Table.Td>
                        </Table.Tr>
                      ))}
                    </Table.Tbody>
                  </Table>
                </ScrollArea>
              </Card>
            </Grid.Col>

            <Grid.Col span={{ base: 12, md: 4 }}>
              <Card withBorder p="lg" mb="md">
                <Title order={3} mb="md">System Health</Title>
                <Stack align="center" mb="md">
                  <RingProgress
                    size={120}
                    thickness={12}
                    sections={[{ value: data.fairnessScore, color: 'blue' }]}
                    label={
                      <Text ta="center" size="xl" fw={700}>
                        {data.fairnessScore}%
                      </Text>
                    }
                  />
                  <Text ta="center" c="dimmed">
                    Overall Fairness Score
                  </Text>
                </Stack>
                <Stack gap="sm">
                  <Group justify="space-between">
                    <Text size="sm">Models Active</Text>
                    <Text size="sm" fw={500}>{data.activeModels}/{data.totalModels}</Text>
                  </Group>
                  <Group justify="space-between">
                    <Text size="sm">In Testing</Text>
                    <Text size="sm" fw={500}>{data.modelsInTesting}</Text>
                  </Group>
                  <Group justify="space-between">
                    <Text size="sm">Blocked</Text>
                    <Text size="sm" fw={500} c="red">{data.modelsBlocked}</Text>
                  </Group>
                </Stack>
              </Card>

              <Card withBorder p="lg">
                <Title order={3} mb="md">Recent Activity</Title>
                <Timeline active={-1} bulletSize={24} lineWidth={2}>
                  {data.recentActivity.slice(0, 4).map((activity) => (
                    <Timeline.Item
                      key={activity.id}
                      bullet={
                        <ThemeIcon size="sm" radius="xl" color={
                          activity.severity === 'critical' ? 'red' :
                          activity.severity === 'warning' ? 'yellow' : 'blue'
                        } variant="light">
                          {activity.type === 'bias_detected' ? <IconAlertTriangle size="0.8rem" /> :
                           activity.type === 'model_deployed' ? <IconCheck size="0.8rem" /> :
                           activity.type === 'bias_testing' ? <IconTestPipe size="0.8rem" /> :
                           <IconShield size="0.8rem" />}
                        </ThemeIcon>
                      }
                      title={
                        <Text size="sm" fw={500}>
                          {activity.type === 'bias_detected' ? 'Bias Detected' :
                           activity.type === 'model_deployed' ? 'Model Deployed' :
                           activity.type === 'bias_testing' ? 'Bias Testing' :
                           'Security Scan'}
                        </Text>
                      }
                    >
                      <Text size="xs" c="dimmed" mb="xs">
                        {activity.model}
                      </Text>
                      {activity.biasType && (
                        <Badge size="sm" color="red" variant="light" mb="xs">
                          {activity.biasType}
                        </Badge>
                      )}
                      <Group justify="space-between">
                        <Text size="xs" c="dimmed">
                          {activity.user}
                        </Text>
                        <Text size="xs" c="dimmed">
                          {activity.time}
                        </Text>
                      </Group>
                    </Timeline.Item>
                  ))}
                </Timeline>
              </Card>
            </Grid.Col>
          </Grid>
        </Tabs.Panel>

        {/* Bias Analysis Tab */}
        <Tabs.Panel value="bias" pt="xl">
          <Grid>
            <Grid.Col span={{ base: 12, md: 8 }}>
              <Card withBorder p="lg" mb="md">
                <Title order={3} mb="md">Bias Metrics Heatmap</Title>
                <BarChart
                  h={400}
                  data={[
                    { metric: 'Demographic Parity', value: data.biasMetrics.demographicParity * 100, color: data.biasMetrics.demographicParity > 0.8 ? 'green.6' : data.biasMetrics.demographicParity > 0.6 ? 'yellow.6' : 'red.6' },
                    { metric: 'Equalized Odds', value: data.biasMetrics.equalizedOdds * 100, color: data.biasMetrics.equalizedOdds > 0.8 ? 'green.6' : data.biasMetrics.equalizedOdds > 0.6 ? 'yellow.6' : 'red.6' },
                    { metric: 'Calibration', value: data.biasMetrics.calibration * 100, color: data.biasMetrics.calibration > 0.8 ? 'green.6' : data.biasMetrics.calibration > 0.6 ? 'yellow.6' : 'red.6' },
                    { metric: 'Disparate Impact', value: data.biasMetrics.disparateImpact * 100, color: data.biasMetrics.disparateImpact > 0.8 ? 'green.6' : data.biasMetrics.disparateImpact > 0.6 ? 'yellow.6' : 'red.6' },
                    { metric: 'Counterfactual Fairness', value: data.biasMetrics.counterfactualFairness * 100, color: data.biasMetrics.counterfactualFairness > 0.8 ? 'green.6' : data.biasMetrics.counterfactualFairness > 0.6 ? 'yellow.6' : 'red.6' },
                    { metric: 'Individual Fairness', value: data.biasMetrics.individualFairness * 100, color: data.biasMetrics.individualFairness > 0.8 ? 'green.6' : data.biasMetrics.individualFairness > 0.6 ? 'yellow.6' : 'red.6' },
                  ]}
                  dataKey="metric"
                  series={[{ name: 'value', color: 'blue.6' }]}
                  withTooltip
                  withLegend
                />
              </Card>
            </Grid.Col>

            <Grid.Col span={{ base: 12, md: 4 }}>
              <Card withBorder p="lg" mb="md">
                <Title order={3} mb="md">Bias Metrics</Title>
                <Stack gap="md">
                  <div>
                    <Group justify="space-between" mb="xs">
                      <Text size="sm">Demographic Parity</Text>
                      <Text size="sm" fw={500}>{(data.biasMetrics.demographicParity * 100).toFixed(1)}%</Text>
                    </Group>
                    <Progress value={data.biasMetrics.demographicParity * 100} color="blue" size="sm" />
                  </div>
                  <div>
                    <Group justify="space-between" mb="xs">
                      <Text size="sm">Equalized Odds</Text>
                      <Text size="sm" fw={500}>{(data.biasMetrics.equalizedOdds * 100).toFixed(1)}%</Text>
                    </Group>
                    <Progress value={data.biasMetrics.equalizedOdds * 100} color="green" size="sm" />
                  </div>
                  <div>
                    <Group justify="space-between" mb="xs">
                      <Text size="sm">Calibration</Text>
                      <Text size="sm" fw={500}>{(data.biasMetrics.calibration * 100).toFixed(1)}%</Text>
                    </Group>
                    <Progress value={data.biasMetrics.calibration * 100} color="yellow" size="sm" />
                  </div>
                  <div>
                    <Group justify="space-between" mb="xs">
                      <Text size="sm">Disparate Impact</Text>
                      <Text size="sm" fw={500}>{(data.biasMetrics.disparateImpact * 100).toFixed(1)}%</Text>
                    </Group>
                    <Progress value={data.biasMetrics.disparateImpact * 100} color="red" size="sm" />
                  </div>
                </Stack>
              </Card>
            </Grid.Col>

            <Grid.Col span={{ base: 12, md: 6 }}>
              <Card withBorder p="lg" mb="md">
                <Title order={3} mb="md">Bias Alerts</Title>
                <Stack gap="md">
                  <Alert icon={<IconAlertTriangle size="1rem" />} title="High Bias Detected" color="red">
                    GPT-4 Financial Advisor shows significant bias against protected groups
                  </Alert>
                  <Alert icon={<IconAlertTriangle size="1rem" />} title="Fairness Warning" color="yellow">
                    DALL-E Image Generator requires fairness review
                  </Alert>
                  <Alert icon={<IconCheck size="1rem" />} title="Fairness Passed" color="green">
                    BERT Sentiment Analysis meets all fairness criteria
                  </Alert>
                </Stack>
              </Card>
            </Grid.Col>
          </Grid>
        </Tabs.Panel>

        {/* Model Registry Tab */}
        <Tabs.Panel value="models" pt="xl">
          <Card withBorder p="lg">
            <Group justify="space-between" mb="md">
              <Title order={3}>Model Registry</Title>
              <Button leftSection={<IconPlus size="1rem" />}>
                Register New Model
              </Button>
            </Group>
            <ScrollArea>
              <Table>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Model</Table.Th>
                    <Table.Th>Type</Table.Th>
                    <Table.Th>Status</Table.Th>
                    <Table.Th>Accuracy</Table.Th>
                    <Table.Th>Fairness</Table.Th>
                    <Table.Th>Last Updated</Table.Th>
                    <Table.Th>Actions</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {data.modelPerformance.map((model, index) => (
                    <Table.Tr key={index}>
                      <Table.Td>
                        <Group>
                          <Avatar size="sm" color="blue">
                            {model.type === 'LLM' ? <IconBrain size="1rem" /> :
                             model.type === 'Deep Learning' ? <IconRobot size="1rem" /> :
                             model.type === 'GenAI' ? <IconTarget size="1rem" /> :
                             <IconChartBar size="1rem" />}
                          </Avatar>
                          <div>
                            <Text fw={500}>{model.name}</Text>
                            <Text size="xs" c="dimmed">AI Model</Text>
                          </div>
                        </Group>
                      </Table.Td>
                      <Table.Td>
                        <Badge variant="light" color="blue">{model.type}</Badge>
                      </Table.Td>
                      <Table.Td>
                        <Badge color={getStatusColor(model.status)} variant="light">
                          {model.status}
                        </Badge>
                      </Table.Td>
                      <Table.Td>
                        <Text>{(model.accuracy * 100).toFixed(1)}%</Text>
                      </Table.Td>
                      <Table.Td>
                        <Text>{(model.fairness * 100).toFixed(1)}%</Text>
                      </Table.Td>
                      <Table.Td>
                        <Text size="sm" c="dimmed">{model.lastUpdated}</Text>
                      </Table.Td>
                      <Table.Td>
                        <Group gap="xs">
                          <ActionIcon variant="light" size="sm">
                            <IconEye size="1rem" />
                          </ActionIcon>
                          <ActionIcon variant="light" size="sm">
                            <IconTestPipe size="1rem" />
                          </ActionIcon>
                          <ActionIcon variant="light" size="sm">
                            <IconSettings size="1rem" />
                          </ActionIcon>
                        </Group>
                      </Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            </ScrollArea>
          </Card>
        </Tabs.Panel>

        {/* Activity Tab */}
        <Tabs.Panel value="activity" pt="xl">
          <Card withBorder p="lg">
            <Title order={3} mb="md">Real-time AI Activity</Title>
            <Timeline active={-1} bulletSize={24} lineWidth={2}>
              {data.recentActivity.map((activity) => (
                <Timeline.Item
                  key={activity.id}
                  bullet={
                    <ThemeIcon size="sm" radius="xl" color={
                      activity.severity === 'critical' ? 'red' :
                      activity.severity === 'warning' ? 'yellow' : 'blue'
                    } variant="light">
                      {activity.type === 'bias_detected' ? <IconAlertTriangle size="0.8rem" /> :
                       activity.type === 'model_deployed' ? <IconCheck size="0.8rem" /> :
                       activity.type === 'bias_testing' ? <IconTestPipe size="0.8rem" /> :
                       <IconShield size="0.8rem" />}
                    </ThemeIcon>
                  }
                  title={
                    <Text fw={500}>
                      {activity.type === 'bias_detected' ? 'Bias Detected' :
                       activity.type === 'model_deployed' ? 'Model Deployed' :
                       activity.type === 'bias_testing' ? 'Bias Testing' :
                       'Security Scan'}
                    </Text>
                  }
                >
                  <Text c="dimmed" size="sm" mb="xs">
                    {activity.model}
                  </Text>
                  {activity.biasType && (
                    <Badge size="sm" color="red" variant="light" mb="xs">
                      {activity.biasType}
                    </Badge>
                  )}
                  <Group justify="space-between">
                    <Text size="sm" c="dimmed">
                      {activity.user}
                    </Text>
                    <Text size="sm" c="dimmed">
                      {activity.time}
                    </Text>
                  </Group>
                </Timeline.Item>
              ))}
            </Timeline>
          </Card>
        </Tabs.Panel>
      </Tabs>

      {/* Model Details Panel */}
      {selectedModel && (
        <Card withBorder p="lg" mt="xl" style={{ background: 'var(--mantine-color-blue-light)' }}>
          <Group justify="space-between" mb="md">
            <Title order={3}>
              Model Details: {selectedModel}
            </Title>
            <Button
              variant="subtle"
              color="gray"
              size="sm"
              onClick={() => setSelectedModel(null)}
            >
              Close
            </Button>
          </Group>
          
          <Grid>
            <Grid.Col span={{ base: 12, md: 6 }}>
              <Stack gap="md">
                <div>
                  <Text size="sm" c="dimmed" mb="xs">Model Type</Text>
                  <Badge variant="light" color="blue">
                    {data.modelPerformance.find(m => m.name === selectedModel)?.type}
                  </Badge>
                </div>
                <div>
                  <Text size="sm" c="dimmed" mb="xs">Accuracy</Text>
                  <Text size="lg" fw={600}>
                    {(data.modelPerformance.find(m => m.name === selectedModel)?.accuracy! * 100).toFixed(1)}%
                  </Text>
                </div>
                <div>
                  <Text size="sm" c="dimmed" mb="xs">Fairness Score</Text>
                  <Text size="lg" fw={600}>
                    {(data.modelPerformance.find(m => m.name === selectedModel)?.fairness! * 100).toFixed(1)}%
                  </Text>
                </div>
              </Stack>
            </Grid.Col>
            
            <Grid.Col span={{ base: 12, md: 6 }}>
              <Stack gap="md">
                <div>
                  <Text size="sm" c="dimmed" mb="xs">Bias Types Detected</Text>
                  <Group gap="xs">
                    {data.modelPerformance.find(m => m.name === selectedModel)?.biasTypes.map((bias, idx) => (
                      <Badge key={idx} color="red" variant="light">
                        {bias}
                      </Badge>
                    ))}
                  </Group>
                </div>
                <div>
                  <Text size="sm" c="dimmed" mb="xs">Last Updated</Text>
                  <Text>
                    {data.modelPerformance.find(m => m.name === selectedModel)?.lastUpdated}
                  </Text>
                </div>
              </Stack>
            </Grid.Col>
          </Grid>
          
          <Group mt="xl" gap="md">
            <Button
              leftSection={<IconTestPipe size="1rem" />}
              variant="light"
              color="orange"
            >
              Run Detailed Analysis
            </Button>
            <Button
              leftSection={<IconEye size="1rem" />}
              variant="light"
              color="blue"
            >
              View Full Report
            </Button>
            <Button
              leftSection={<IconSettings size="1rem" />}
              variant="light"
              color="gray"
            >
              Configure Model
            </Button>
          </Group>
        </Card>
      )}
    </Container>
  );
}
