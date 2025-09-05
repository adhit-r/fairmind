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
  List,
  Anchor,
  Select,
  TextInput,
  Textarea,
} from '@mantine/core';
import {
  IconTarget,
  IconAlertTriangle,
  IconCheck,
  IconX,
  IconTrendingUp,
  IconTrendingDown,
  IconRobot,
  IconDatabase,
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
  IconBrain,
  IconShield,
  IconUsers,
  IconScale,
  IconGenderMale,
  IconGenderFemale,
  IconWorld,
  IconFlag,
  IconCalendar,
  IconPlayerPlay,
  IconDownload,
  IconUpload,
} from '@tabler/icons-react';
import { useState, useEffect } from 'react';

// Bias detection results
const biasDetectionResults = [
  {
    id: 'bias-001',
    modelName: 'GPT-4 Vision',
    modelType: 'LLM',
    dataset: 'Professional Headshots Dataset',
    timestamp: '2024-01-15T10:30:00Z',
    status: 'completed',
    overallBiasScore: 0.23,
    riskLevel: 'high',
    metrics: {
      demographicParity: 0.15,
      equalizedOdds: 0.18,
      calibration: 0.12,
      disparateImpact: 0.22,
      counterfactualFairness: 0.28,
      individualFairness: 0.19,
    },
    biasTypes: [
      { type: 'Gender Bias', severity: 'high', impact: 0.25, description: 'Model shows preference for male-presenting individuals in professional contexts' },
      { type: 'Racial Bias', severity: 'medium', impact: 0.18, description: 'Lower accuracy for darker skin tones in image recognition' },
      { type: 'Age Bias', severity: 'low', impact: 0.12, description: 'Slight preference for younger age groups' },
    ],
    recommendations: [
      'Implement demographic parity constraints during training',
      'Use balanced datasets with equal representation',
      'Apply post-processing fairness techniques',
      'Regular bias monitoring and retraining'
    ]
  },
  {
    id: 'bias-002',
    modelName: 'ResNet-152',
    modelType: 'Deep Learning',
    dataset: 'Medical Imaging Dataset',
    timestamp: '2024-01-14T14:20:00Z',
    status: 'completed',
    overallBiasScore: 0.08,
    riskLevel: 'low',
    metrics: {
      demographicParity: 0.05,
      equalizedOdds: 0.07,
      calibration: 0.06,
      disparateImpact: 0.09,
      counterfactualFairness: 0.11,
      individualFairness: 0.08,
    },
    biasTypes: [
      { type: 'Geographic Bias', severity: 'low', impact: 0.08, description: 'Slight variation in performance across different geographic regions' },
    ],
    recommendations: [
      'Continue current training practices',
      'Monitor for emerging bias patterns',
      'Regular validation on diverse datasets'
    ]
  },
  {
    id: 'bias-003',
    modelName: 'DALL-E 3',
    modelType: 'GenAI',
    dataset: 'Art Generation Prompts',
    timestamp: '2024-01-13T09:15:00Z',
    status: 'completed',
    overallBiasScore: 0.31,
    riskLevel: 'critical',
    metrics: {
      demographicParity: 0.28,
      equalizedOdds: 0.32,
      calibration: 0.25,
      disparateImpact: 0.35,
      counterfactualFairness: 0.29,
      individualFairness: 0.33,
    },
    biasTypes: [
      { type: 'Cultural Bias', severity: 'critical', impact: 0.35, description: 'Strong Western cultural bias in generated content' },
      { type: 'Gender Bias', severity: 'high', impact: 0.28, description: 'Stereotypical gender representations in generated images' },
      { type: 'Racial Bias', severity: 'high', impact: 0.30, description: 'Underrepresentation of non-white individuals' },
    ],
    recommendations: [
      'Implement cultural diversity training data',
      'Use bias-aware generation techniques',
      'Human-in-the-loop validation for sensitive content',
      'Regular bias audits and model updates'
    ]
  }
];

// Bias metrics definitions
const biasMetrics = [
  {
    name: 'Demographic Parity',
    description: 'Equal positive prediction rates across groups',
    formula: 'P(Ŷ=1|A=a) = P(Ŷ=1|A=b)',
    ideal: 0.0,
    current: 0.16,
    status: 'warning'
  },
  {
    name: 'Equalized Odds',
    description: 'Equal true positive and false positive rates',
    formula: 'TPR(A=a) = TPR(A=b) and FPR(A=a) = FPR(A=b)',
    ideal: 0.0,
    current: 0.19,
    status: 'warning'
  },
  {
    name: 'Calibration',
    description: 'Predicted probabilities match actual outcomes',
    formula: 'P(Y=1|Ŷ=p, A=a) = P(Y=1|Ŷ=p, A=b)',
    ideal: 0.0,
    current: 0.14,
    status: 'good'
  },
  {
    name: 'Disparate Impact',
    description: 'Ratio of positive outcomes between groups',
    formula: 'P(Ŷ=1|A=a) / P(Ŷ=1|A=b)',
    ideal: 1.0,
    current: 0.22,
    status: 'critical'
  }
];

export default function BiasAnalysisDashboard() {
  const { colorScheme } = useMantineColorScheme();
  const [selectedAnalysis, setSelectedAnalysis] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [isLoading, setIsLoading] = useState(true);
  const [isRunningAnalysis, setIsRunningAnalysis] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 1500);
    return () => clearTimeout(timer);
  }, []);

  const handleRunAnalysis = async () => {
    setIsRunningAnalysis(true);
    // Simulate analysis
    await new Promise(resolve => setTimeout(resolve, 3000));
    setIsRunningAnalysis(false);
  };

  if (isLoading) {
    return (
      <Center style={{ height: '100vh' }}>
        <Stack align="center" gap="xl">
          <ThemeIcon size="xl" radius="md" color="red" variant="light">
            <IconTarget size="2rem" />
          </ThemeIcon>
          <Text size="xl" fw={600}>
            Loading Bias Analysis Dashboard...
          </Text>
          <Loader size="lg" />
        </Stack>
      </Center>
    );
  }

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'critical': return 'red';
      case 'high': return 'orange';
      case 'medium': return 'yellow';
      case 'low': return 'green';
      default: return 'gray';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'red';
      case 'high': return 'orange';
      case 'medium': return 'yellow';
      case 'low': return 'green';
      default: return 'gray';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'good': return 'green';
      case 'warning': return 'yellow';
      case 'critical': return 'red';
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
                    ? 'linear-gradient(135deg, #ef4444, #f97316, #eab308)'
                    : 'linear-gradient(135deg, #dc2626, #ea580c, #ca8a04)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  fontSize: '2.5rem',
                  fontWeight: 800,
                }}
              >
                Bias Detection Center
              </Title>
              <Text c="dimmed" size="lg" fw={500}>
                AI Model Fairness Analysis & Bias Monitoring
              </Text>
            </div>
            <Group>
              <Button
                variant="light"
                leftSection={<IconRefresh size="1rem" />}
                size="lg"
                style={{
                  borderRadius: '16px',
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.2)',
                }}
              >
                Refresh Results
              </Button>
              <Button
                variant="filled"
                leftSection={<IconPlayerPlay size="1rem" />}
                size="lg"
                loading={isRunningAnalysis}
                onClick={handleRunAnalysis}
                style={{
                  borderRadius: '16px',
                  background: 'linear-gradient(135deg, #ef4444, #f97316)',
                  border: 'none',
                }}
              >
                Run New Analysis
              </Button>
            </Group>
          </Group>

          {/* Bias Detection Overview */}
          <SimpleGrid cols={{ base: 2, sm: 4 }} mt="xl">
            {[
              { 
                label: 'Models Analyzed', 
                value: biasDetectionResults.length, 
                color: 'blue', 
                icon: IconRobot 
              },
              { 
                label: 'Critical Bias Alerts', 
                value: biasDetectionResults.filter(r => r.riskLevel === 'critical').length, 
                color: 'red', 
                icon: IconAlertTriangle 
              },
              { 
                label: 'Avg Bias Score', 
                value: `${(biasDetectionResults.reduce((acc, r) => acc + r.overallBiasScore, 0) / biasDetectionResults.length * 100).toFixed(1)}%`, 
                color: 'orange', 
                icon: IconTarget 
              },
              { 
                label: 'Bias Types Detected', 
                value: new Set(biasDetectionResults.flatMap(r => r.biasTypes.map(bt => bt.type))).size, 
                color: 'violet', 
                icon: IconBrain 
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
                        metric.color === 'red' ? '239, 68, 68' : 
                        metric.color === 'orange' ? '245, 158, 11' : '139, 92, 246'}, 0.1)`,
                      border: `1px solid rgba(${metric.color === 'blue' ? '59, 130, 246' : 
                        metric.color === 'red' ? '239, 68, 68' : 
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
                           metric.color === 'red' ? '#ef4444' : 
                           metric.color === 'orange' ? '#f59e0b' : '#8b5cf6',
                    textShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
                  }}
                >
                  {metric.value}
                </Text>
              </Card>
            ))}
          </SimpleGrid>
        </Paper>

        <Grid>
          {/* Bias Analysis Results */}
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
                background: 'linear-gradient(135deg, #ef4444, #f97316)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                fontSize: '1.8rem',
                fontWeight: 700,
              }}>
                Recent Bias Analysis Results
              </Title>
              
              <ScrollArea>
                <Table>
                  <Table.Thead>
                    <Table.Tr>
                      <Table.Th style={{ 
                        background: 'rgba(239, 68, 68, 0.1)',
                        borderRadius: '12px 12px 0 0',
                        border: 'none',
                        padding: '16px',
                      }}>
                        <Text fw={600} c="red">Model</Text>
                      </Table.Th>
                      <Table.Th style={{ 
                        background: 'rgba(239, 68, 68, 0.1)',
                        border: 'none',
                        padding: '16px',
                      }}>
                        <Text fw={600} c="red">Bias Score</Text>
                      </Table.Th>
                      <Table.Th style={{ 
                        background: 'rgba(239, 68, 68, 0.1)',
                        border: 'none',
                        padding: '16px',
                      }}>
                        <Text fw={600} c="red">Risk Level</Text>
                      </Table.Th>
                      <Table.Th style={{ 
                        background: 'rgba(239, 68, 68, 0.1)',
                        border: 'none',
                        padding: '16px',
                      }}>
                        <Text fw={600} c="red">Bias Types</Text>
                      </Table.Th>
                      <Table.Th style={{ 
                        background: 'rgba(239, 68, 68, 0.1)',
                        borderRadius: '0 12px 12px 0',
                        border: 'none',
                        padding: '16px',
                      }}>
                        <Text fw={600} c="red">Actions</Text>
                      </Table.Th>
                    </Table.Tr>
                  </Table.Thead>
                  <Table.Tbody>
                    {biasDetectionResults.map((result, index) => (
                      <Table.Tr 
                        key={index}
                        style={{
                          cursor: 'pointer',
                          background: selectedAnalysis === result.id 
                            ? 'rgba(239, 68, 68, 0.1)' 
                            : 'transparent',
                          borderRadius: '12px',
                          margin: '8px 0',
                          transform: 'perspective(1000px) rotateX(2deg)',
                          transition: 'all 0.3s ease',
                        }}
                        onClick={() => setSelectedAnalysis(selectedAnalysis === result.id ? null : result.id)}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.transform = 'perspective(1000px) rotateX(0deg) translateY(-2px)';
                          e.currentTarget.style.background = 'rgba(239, 68, 68, 0.05)';
                          e.currentTarget.style.boxShadow = '0 4px 16px rgba(0, 0, 0, 0.1)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.transform = 'perspective(1000px) rotateX(2deg)';
                          e.currentTarget.style.background = selectedAnalysis === result.id 
                            ? 'rgba(239, 68, 68, 0.1)' 
                            : 'transparent';
                          e.currentTarget.style.boxShadow = 'none';
                        }}
                      >
                        <Table.Td style={{ padding: '16px' }}>
                          <Group>
                            <ThemeIcon 
                              size="lg" 
                              radius="xl" 
                              color="red" 
                              variant="light"
                              style={{
                                background: 'rgba(239, 68, 68, 0.1)',
                                border: '1px solid rgba(239, 68, 68, 0.2)',
                                transform: 'perspective(200px) rotateX(45deg)',
                              }}
                            >
                              {result.modelType === 'LLM' ? <IconBrain size="1.2rem" /> :
                               result.modelType === 'Deep Learning' ? <IconRobot size="1.2rem" /> :
                               <IconTarget size="1.2rem" />}
                            </ThemeIcon>
                            <div>
                              <Text fw={600} size="sm">{result.modelName}</Text>
                              <Text size="xs" c="dimmed">{result.dataset}</Text>
                            </div>
                          </Group>
                        </Table.Td>
                        <Table.Td style={{ padding: '16px' }}>
                          <Group>
                            <Text fw={600} c="red">{(result.overallBiasScore * 100).toFixed(1)}%</Text>
                            <Box
                              style={{
                                width: 12,
                                height: 12,
                                borderRadius: '50%',
                                background: result.overallBiasScore > 0.3 ? '#ef4444' : 
                                           result.overallBiasScore > 0.2 ? '#f59e0b' : 
                                           result.overallBiasScore > 0.1 ? '#eab308' : '#22c55e',
                                transform: 'perspective(100px) rotateX(45deg)',
                                boxShadow: '0 2px 4px rgba(0, 0, 0, 0.2)',
                              }}
                            />
                          </Group>
                        </Table.Td>
                        <Table.Td style={{ padding: '16px' }}>
                          <Badge
                            color={getRiskColor(result.riskLevel)}
                            variant="light"
                            size="lg"
                            style={{
                              borderRadius: '12px',
                              background: result.riskLevel === 'critical' ? 'rgba(239, 68, 68, 0.1)' :
                                         result.riskLevel === 'high' ? 'rgba(245, 158, 11, 0.1)' :
                                         result.riskLevel === 'medium' ? 'rgba(234, 179, 8, 0.1)' :
                                         'rgba(34, 197, 94, 0.1)',
                              border: result.riskLevel === 'critical' ? '1px solid rgba(239, 68, 68, 0.2)' :
                                      result.riskLevel === 'high' ? '1px solid rgba(245, 158, 11, 0.2)' :
                                      result.riskLevel === 'medium' ? '1px solid rgba(234, 179, 8, 0.2)' :
                                      '1px solid rgba(34, 197, 94, 0.2)',
                            }}
                          >
                            {result.riskLevel}
                          </Badge>
                        </Table.Td>
                        <Table.Td style={{ padding: '16px' }}>
                          <Group gap="xs">
                            {result.biasTypes.slice(0, 2).map((bias, biasIndex) => (
                              <Badge
                                key={biasIndex}
                                color={getSeverityColor(bias.severity)}
                                variant="light"
                                size="sm"
                                style={{ borderRadius: '8px' }}
                              >
                                {bias.type}
                              </Badge>
                            ))}
                            {result.biasTypes.length > 2 && (
                              <Badge variant="outline" size="sm" style={{ borderRadius: '8px' }}>
                                +{result.biasTypes.length - 2}
                              </Badge>
                            )}
                          </Group>
                        </Table.Td>
                        <Table.Td style={{ padding: '16px' }}>
                          <Group gap="xs">
                            <ActionIcon 
                              variant="light" 
                              size="lg" 
                              color="red"
                              style={{
                                borderRadius: '12px',
                                background: 'rgba(239, 68, 68, 0.1)',
                                border: '1px solid rgba(239, 68, 68, 0.2)',
                                transform: 'perspective(200px) rotateX(45deg)',
                              }}
                            >
                              <IconEye size="1.2rem" />
                            </ActionIcon>
                            <ActionIcon 
                              variant="light" 
                              size="lg" 
                              color="orange"
                              style={{
                                borderRadius: '12px',
                                background: 'rgba(245, 158, 11, 0.1)',
                                border: '1px solid rgba(245, 158, 11, 0.2)',
                                transform: 'perspective(200px) rotateX(45deg)',
                              }}
                            >
                              <IconDownload size="1.2rem" />
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

          {/* Analysis Details Panel */}
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
                {selectedAnalysis ? 'Analysis Details' : 'Select an Analysis'}
              </Title>
              
              {selectedAnalysis ? (
                (() => {
                  const result = biasDetectionResults.find(r => r.id === selectedAnalysis);
                  if (!result) return null;
                  
                  return (
                    <Stack gap="md">
                      {/* Bias Metrics */}
                      <div>
                        <Text fw={600} size="sm" mb="md">Bias Metrics</Text>
                        <Stack gap="sm">
                          {Object.entries(result.metrics).map(([metric, value]) => (
                            <Box key={metric}>
                              <Group justify="space-between" mb="xs">
                                <Text size="xs" c="dimmed" style={{ textTransform: 'capitalize' }}>
                                  {metric.replace(/([A-Z])/g, ' $1').trim()}
                                </Text>
                                <Text size="xs" fw={600}>{(value * 100).toFixed(1)}%</Text>
                              </Group>
                              <Progress
                                value={value * 100}
                                color={value > 0.2 ? 'red' : value > 0.1 ? 'orange' : 'green'}
                                size="sm"
                                radius="xl"
                              />
                            </Box>
                          ))}
                        </Stack>
                      </div>
                      
                      <Divider />
                      
                      {/* Bias Types */}
                      <div>
                        <Text fw={600} size="sm" mb="md">Detected Bias Types</Text>
                        <Stack gap="sm">
                          {result.biasTypes.map((bias, index) => (
                            <Card
                              key={index}
                              p="sm"
                              style={{
                                background: 'rgba(255, 255, 255, 0.05)',
                                border: '1px solid rgba(255, 255, 255, 0.1)',
                                borderRadius: '8px',
                              }}
                            >
                              <Group justify="space-between" mb="xs">
                                <Text fw={600} size="sm">{bias.type}</Text>
                                <Badge
                                  color={getSeverityColor(bias.severity)}
                                  variant="light"
                                  size="xs"
                                >
                                  {bias.severity}
                                </Badge>
                              </Group>
                              <Text size="xs" c="dimmed" mb="xs">
                                Impact: {(bias.impact * 100).toFixed(1)}%
                              </Text>
                              <Text size="xs">{bias.description}</Text>
                            </Card>
                          ))}
                        </Stack>
                      </div>
                      
                      <Divider />
                      
                      {/* Recommendations */}
                      <div>
                        <Text fw={600} size="sm" mb="md">Recommendations</Text>
                        <List size="sm" spacing="xs">
                          {result.recommendations.map((rec, index) => (
                            <List.Item key={index}>
                              <Text size="xs">{rec}</Text>
                            </List.Item>
                          ))}
                        </List>
                      </div>
                    </Stack>
                  );
                })()
              ) : (
                <Center style={{ height: '300px' }}>
                  <Stack align="center" gap="md">
                    <ThemeIcon size="xl" radius="xl" color="gray" variant="light">
                      <IconTarget size="2rem" />
                    </ThemeIcon>
                    <Text c="dimmed" ta="center">
                      Click on an analysis to view<br />detailed bias metrics and recommendations
                    </Text>
                  </Stack>
                </Center>
              )}
            </Card>
          </Grid.Col>
        </Grid>

        {/* Bias Metrics Definitions */}
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
            Bias Metrics & Definitions
          </Title>
          
          <SimpleGrid cols={{ base: 1, md: 2 }} gap="xl">
            {biasMetrics.map((metric, index) => (
              <Card
                key={index}
                p="lg"
                style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '16px',
                }}
              >
                <Group justify="space-between" mb="md">
                  <Text fw={600} size="lg">{metric.name}</Text>
                  <Badge
                    color={getStatusColor(metric.status)}
                    variant="light"
                    size="lg"
                    style={{ borderRadius: '12px' }}
                  >
                    {metric.status}
                  </Badge>
                </Group>
                
                <Text size="sm" c="dimmed" mb="md">
                  {metric.description}
                </Text>
                
                <Box mb="md">
                  <Text size="xs" fw={500} c="dimmed" mb="xs">Formula:</Text>
                  <Text size="sm" style={{ 
                    fontFamily: 'monospace',
                    background: 'rgba(255, 255, 255, 0.1)',
                    padding: '8px',
                    borderRadius: '8px',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                  }}>
                    {metric.formula}
                  </Text>
                </Box>
                
                <Group justify="space-between">
                  <div>
                    <Text size="xs" c="dimmed">Ideal Value</Text>
                    <Text size="sm" fw={600} c="green">{metric.ideal}</Text>
                  </div>
                  <div>
                    <Text size="xs" c="dimmed">Current Value</Text>
                    <Text size="sm" fw={600} c={metric.status === 'good' ? 'green' : metric.status === 'warning' ? 'orange' : 'red'}>
                      {metric.current}
                    </Text>
                  </div>
                </Group>
              </Card>
            ))}
          </SimpleGrid>
        </Card>
      </Container>
    </Box>
  );
}
