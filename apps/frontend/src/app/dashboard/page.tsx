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
  NumberFormatter,
  Tooltip,
  Skeleton,
} from '@mantine/core';
import { LineChart, BarChart, PieChart, AreaChart } from '@mantine/charts';
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
  IconRefresh,
  IconPlus,
  IconEye,
  IconTestPipe,
  IconSettings,
  IconClock,
  IconDots,
  IconFileText,
  IconLock,
  IconActivity,
  IconUsers,
  IconScale,
  IconUpload,
  IconDownload,
  IconEdit,
  IconTrash,
  IconCopy,
  IconGitBranch,
  IconTag,
  IconCalendar,
  IconCode,
  IconFileCode,
} from '@tabler/icons-react';
import { useState, useEffect, useCallback } from 'react';
// import { apiClient } from '@/config/api';

// Mock data for fallback
const mockGovernanceData = {
  totalModels: 12,
  activeModels: 8,
  criticalRisks: 2,
  llmSafetyScore: 85,
  nistCompliance: 78,
  biasAlerts: 3,
  fairnessScore: 87,
  totalDatasets: 15,
  totalSimulations: 24,
  lastUpdated: new Date().toISOString()
};

const mockModels = [
  {
    id: 'model-001',
    name: 'GPT-4 Vision',
    type: 'LLM',
    status: 'active',
    accuracy: 0.94,
    biasScore: 0.13,
    securityScore: 0.89,
    lastUpdated: '2024-01-15T10:30:00Z'
  },
  {
    id: 'model-002',
    name: 'ResNet-152',
    type: 'Deep Learning',
    status: 'active',
    accuracy: 0.91,
    biasScore: 0.11,
    securityScore: 0.91,
    lastUpdated: '2024-01-14T14:20:00Z'
  },
  {
    id: 'model-003',
    name: 'DALL-E 3',
    type: 'GenAI',
    status: 'testing',
    accuracy: 0.88,
    biasScore: 0.24,
    securityScore: 0.85,
    lastUpdated: '2024-01-13T09:15:00Z'
  }
];

const mockDatasets = [
  {
    id: 'dataset-001',
    name: 'Adult Income Dataset',
    type: 'CSV',
    size: '2.1 MB',
    rows: 48842,
    columns: 15,
    status: 'active'
  },
  {
    id: 'dataset-002',
    name: 'COMPAS Dataset',
    type: 'CSV',
    size: '1.8 MB',
    rows: 7214,
    columns: 21,
    status: 'active'
  }
];

const mockSimulations = [
  {
    id: 'sim-001',
    modelName: 'GPT-4 Vision',
    datasetName: 'Adult Income Dataset',
    status: 'completed',
    accuracy: 0.92,
    fairness: 0.85,
    startedAt: '2024-01-15T10:30:00Z'
  },
  {
    id: 'sim-002',
    modelName: 'ResNet-152',
    datasetName: 'COMPAS Dataset',
    status: 'running',
    accuracy: null,
    fairness: null,
    startedAt: '2024-01-15T11:00:00Z'
  }
];

const mockActivity = [
  {
    id: 'act-001',
    type: 'bias_detected',
    model: 'GPT-4 Vision',
    severity: 'warning',
    time: '30 minutes ago',
    user: 'AI System',
    biasType: 'Gender Bias'
  },
  {
    id: 'act-002',
    type: 'model_updated',
    model: 'ResNet-152',
    severity: 'info',
    time: '2 hours ago',
    user: 'Data Scientist',
    biasType: null
  },
  {
    id: 'act-003',
    type: 'bias_testing',
    model: 'DALL-E 3',
    severity: 'warning',
    time: '1 hour ago',
    user: 'System',
    biasType: 'Cultural Bias'
  }
];

export default function Dashboard() {
  const { colorScheme } = useMantineColorScheme();
  const [activeTab, setActiveTab] = useState('overview');
  const [isLoading, setIsLoading] = useState(true);
  const [data, setData] = useState(mockGovernanceData);
  const [models, setModels] = useState(mockModels);
  const [datasets, setDatasets] = useState(mockDatasets);
  const [simulations, setSimulations] = useState(mockSimulations);
  const [activity, setActivity] = useState(mockActivity);

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      
      // Fetch governance metrics
      const metricsResponse = await apiClient.get('/api/v1/governance/metrics');
      if (metricsResponse.data?.success) {
        setData(metricsResponse.data.data);
      }

      // Fetch models
      const modelsResponse = await apiClient.get('/api/v1/models');
      if (modelsResponse.data?.success) {
        setModels(modelsResponse.data.data);
      }

      // Fetch datasets
      const datasetsResponse = await apiClient.get('/api/v1/datasets');
      if (datasetsResponse.data?.success) {
        setDatasets(datasetsResponse.data.data);
      }

      // Fetch simulations
      const simulationsResponse = await apiClient.get('/api/v1/simulations');
      if (simulationsResponse.data?.success) {
        setSimulations(simulationsResponse.data.simulations);
      }

      // Fetch recent activity
      const activityResponse = await apiClient.get('/api/v1/activity/recent');
      if (activityResponse.data?.success) {
        setActivity(activityResponse.data.data);
      }

    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      // Keep using mock data on error
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (isLoading) {
    return (
      <Center style={{ height: '100vh' }}>
        <Stack align="center" gap="xl">
          <ThemeIcon size="xl" radius="md" color="blue" variant="light">
            <IconBrain size="2rem" />
          </ThemeIcon>
          <Text size="xl" fw={600}>
            Loading AI Governance Dashboard...
          </Text>
          <Loader size="lg" />
        </Stack>
      </Center>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'green';
      case 'testing': return 'yellow';
      case 'completed': return 'blue';
      case 'running': return 'orange';
      case 'failed': return 'red';
      default: return 'gray';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'red';
      case 'warning': return 'orange';
      case 'info': return 'blue';
      default: return 'gray';
    }
  };

  return (
    <Box
      style={{
        background: colorScheme === 'dark' 
          ? 'linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%)'
          : 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 50%, #cbd5e1 100%)',
        minHeight: '100vh',
        position: 'relative',
      }}
    >
      <Container size="xl" py="xl" style={{ position: 'relative', zIndex: 1 }}>
        {/* Header */}
        <Paper 
          p="xl" 
          mb="xl" 
          style={{
            background: colorScheme === 'dark' 
              ? 'rgba(30, 30, 30, 0.8)' 
              : 'rgba(255, 255, 255, 0.8)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '24px',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
          }}
        >
          <Group justify="space-between" mb="md">
            <div>
              <Title 
                order={1} 
                mb="xs"
                style={{
                  background: colorScheme === 'dark' 
                    ? 'linear-gradient(135deg, #60a5fa, #a78bfa, #34d399)'
                    : 'linear-gradient(135deg, #1e40af, #7c3aed, #059669)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  fontSize: '2.5rem',
                  fontWeight: 800,
                }}
              >
                AI Governance Dashboard
              </Title>
              <Text c="dimmed" size="lg" fw={500}>
                Comprehensive AI Model Management & Bias Detection
              </Text>
            </div>
            <Group>
              <Button
                variant="light"
                leftSection={<IconRefresh size="1rem" />}
                size="lg"
                onClick={fetchData}
                style={{
                  borderRadius: '16px',
                  background: 'rgba(59, 130, 246, 0.1)',
                  border: '1px solid rgba(59, 130, 246, 0.2)',
                }}
              >
                Refresh
              </Button>
              <Button
                variant="filled"
                leftSection={<IconPlus size="1rem" />}
                size="lg"
                style={{
                  borderRadius: '16px',
                  background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                  border: 'none',
                }}
              >
                New Analysis
              </Button>
            </Group>
          </Group>

          {/* Key Metrics Overview */}
          <SimpleGrid cols={{ base: 2, sm: 4 }} mt="xl">
            {[
              { 
                label: 'Total Models', 
                value: data.totalModels, 
                color: 'blue', 
                icon: IconRobot,
                trend: '+2 this week'
              },
              { 
                label: 'Active Models', 
                value: data.activeModels, 
                color: 'green', 
                icon: IconCheck,
                trend: '67% of total'
              },
              { 
                label: 'Bias Alerts', 
                value: data.biasAlerts, 
                color: 'orange', 
                icon: IconAlertTriangle,
                trend: '-1 from yesterday'
              },
              { 
                label: 'Fairness Score', 
                value: `${data.fairnessScore}%`, 
                color: 'violet', 
                icon: IconTarget,
                trend: '+3% this month'
              },
            ].map((metric, index) => (
              <Card
                key={index}
                p="lg"
                style={{
                  background: colorScheme === 'dark' 
                    ? 'rgba(20, 20, 20, 0.6)' 
                    : 'rgba(255, 255, 255, 0.6)',
                  backdropFilter: 'blur(16px)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '20px',
                  boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
                  transform: 'perspective(1000px) rotateX(5deg)',
                  transition: 'all 0.3s ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'perspective(1000px) rotateX(0deg) translateY(-8px)';
                  e.currentTarget.style.boxShadow = '0 12px 40px rgba(0, 0, 0, 0.2)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'perspective(1000px) rotateX(5deg)';
                  e.currentTarget.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.1)';
                }}
              >
                <Group justify="space-between" mb="md">
                  <ThemeIcon
                    size="xl"
                    radius="xl"
                    color={metric.color}
                    variant="light"
                    style={{
                      background: `rgba(${metric.color === 'blue' ? '59, 130, 246' : 
                        metric.color === 'green' ? '34, 197, 94' : 
                        metric.color === 'orange' ? '245, 158, 11' : '139, 92, 246'}, 0.1)`,
                      border: `1px solid rgba(${metric.color === 'blue' ? '59, 130, 246' : 
                        metric.color === 'green' ? '34, 197, 94' : 
                        metric.color === 'orange' ? '245, 158, 11' : '139, 92, 246'}, 0.2)`,
                    }}
                  >
                    <metric.icon size="1.5rem" />
                  </ThemeIcon>
                </Group>
                <Text size="sm" c="dimmed" mb="xs" fw={500}>
                  {metric.label}
                </Text>
                <Text 
                  size="2.5rem" 
                  fw={800}
                  style={{
                    color: metric.color === 'blue' ? '#3b82f6' : 
                           metric.color === 'green' ? '#22c55e' : 
                           metric.color === 'orange' ? '#f59e0b' : '#8b5cf6',
                    textShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
                  }}
                >
                  {metric.value}
                </Text>
                <Text size="xs" c="dimmed" mt="xs">
                  {metric.trend}
                </Text>
              </Card>
            ))}
          </SimpleGrid>
        </Paper>

        <Grid>
          {/* Model Performance Chart */}
          <Grid.Col span={{ base: 12, md: 8 }}>
            <Card
              p="xl"
              mb="md"
              style={{
                background: colorScheme === 'dark' 
                  ? 'rgba(20, 20, 20, 0.6)' 
                  : 'rgba(255, 255, 255, 0.6)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '24px',
                boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
                transform: 'perspective(1000px) rotateY(-2deg)',
                transition: 'all 0.3s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'perspective(1000px) rotateY(0deg) translateY(-4px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'perspective(1000px) rotateY(-2deg)';
              }}
            >
              <Title order={3} mb="xl" style={{ 
                background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                fontSize: '1.8rem',
                fontWeight: 700,
              }}>
                Model Performance Trends
              </Title>
              
              <LineChart
                h={300}
                data={[
                  { month: 'Jan', accuracy: 85, fairness: 78, security: 82 },
                  { month: 'Feb', accuracy: 87, fairness: 81, security: 85 },
                  { month: 'Mar', accuracy: 89, fairness: 83, security: 87 },
                  { month: 'Apr', accuracy: 91, fairness: 85, security: 89 },
                  { month: 'May', accuracy: 88, fairness: 87, security: 91 },
                  { month: 'Jun', accuracy: 92, fairness: 89, security: 88 },
                ]}
                dataKey="month"
                series={[
                  { name: 'accuracy', color: '#3b82f6', label: 'Accuracy' },
                  { name: 'fairness', color: '#22c55e', label: 'Fairness' },
                  { name: 'security', color: '#f59e0b', label: 'Security' },
                ]}
                curveType="linear"
                withLegend
                legendProps={{ verticalAlign: 'bottom' }}
              />
            </Card>
          </Grid.Col>

          {/* Model Distribution */}
          <Grid.Col span={{ base: 12, md: 4 }}>
            <Card
              p="xl"
              mb="md"
              style={{
                background: colorScheme === 'dark' 
                  ? 'rgba(20, 20, 20, 0.6)' 
                  : 'rgba(255, 255, 255, 0.6)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '24px',
                boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
                transform: 'perspective(1000px) rotateY(2deg)',
                transition: 'all 0.3s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'perspective(1000px) rotateY(0deg) translateY(-4px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'perspective(1000px) rotateY(2deg)';
              }}
            >
              <Title order={3} mb="xl" style={{ 
                background: 'linear-gradient(135deg, #8b5cf6, #ec4899)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                fontSize: '1.8rem',
                fontWeight: 700,
              }}>
                Model Types
              </Title>
              
              <PieChart
                data={[
                  { name: 'LLM', value: 4, color: '#3b82f6' },
                  { name: 'Deep Learning', value: 3, color: '#22c55e' },
                  { name: 'GenAI', value: 2, color: '#f59e0b' },
                  { name: 'NLP', value: 3, color: '#8b5cf6' },
                ]}
                withTooltip
                tooltipDataSource="segment"
                size={200}
                thickness={40}
                withLabels
                labelsPosition="outside"
                labelsType="percent"
              />
            </Card>
          </Grid.Col>
        </Grid>

        {/* Recent Activity */}
        <Card
          p="xl"
          mb="xl"
          style={{
            background: colorScheme === 'dark' 
              ? 'rgba(20, 20, 20, 0.6)' 
              : 'rgba(255, 255, 255, 0.6)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '24px',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
            transform: 'perspective(1000px) rotateX(1deg)',
            transition: 'all 0.3s ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'perspective(1000px) rotateX(0deg) translateY(-4px)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'perspective(1000px) rotateX(1deg)';
          }}
        >
          <Title order={3} mb="xl" style={{ 
            background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            fontSize: '1.8rem',
            fontWeight: 700,
          }}>
            Recent Activity
          </Title>
          
          <Timeline active={activity.length} bulletSize={24} lineWidth={2}>
            {activity.map((item, index) => (
              <Timeline.Item
                key={index}
                bullet={
                  <ThemeIcon
                    size="lg"
                    radius="xl"
                    color={getSeverityColor(item.severity)}
                    variant="light"
                  >
                    {item.type === 'bias_detected' ? <IconAlertTriangle size="1rem" /> :
                     item.type === 'model_updated' ? <IconRobot size="1rem" /> :
                     <IconTestPipe size="1rem" />}
                  </ThemeIcon>
                }
                title={
                  <Text fw={600} size="sm">
                    {item.type === 'bias_detected' ? 'Bias Detected' :
                     item.type === 'model_updated' ? 'Model Updated' :
                     'Bias Testing'}
                  </Text>
                }
              >
                <Text size="sm" c="dimmed" mb="xs">
                  {item.model} • {item.time}
                </Text>
                {item.biasType && (
                  <Badge
                    color={getSeverityColor(item.severity)}
                    variant="light"
                    size="sm"
                    style={{ borderRadius: '8px' }}
                  >
                    {item.biasType}
                  </Badge>
                )}
              </Timeline.Item>
            ))}
          </Timeline>
        </Card>
      </Container>
    </Box>
  );
}