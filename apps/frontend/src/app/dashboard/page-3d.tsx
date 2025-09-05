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

// 3D Futuristic AI Bias Detection Dashboard Data
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
      biasScore: 0.13,
      biasTypes: ['Gender', 'Age'],
      status: 'warning',
      lastUpdated: '2024-01-15 14:30',
    },
    {
      name: 'ResNet-152 Image Classifier',
      type: 'Deep Learning',
      accuracy: 0.91,
      fairness: 0.93,
      biasScore: 0.07,
      biasTypes: ['Cultural'],
      status: 'good',
      lastUpdated: '2024-01-15 12:15',
    },
    {
      name: 'DALL-E 3 Art Generator',
      type: 'GenAI',
      accuracy: 0.88,
      fairness: 0.76,
      biasScore: 0.24,
      biasTypes: ['Gender', 'Cultural', 'Age'],
      status: 'critical',
      lastUpdated: '2024-01-15 10:45',
    },
    {
      name: 'Random Forest Classifier',
      type: 'Traditional',
      accuracy: 0.89,
      fairness: 0.91,
      biasScore: 0.09,
      biasTypes: [],
      status: 'good',
      lastUpdated: '2024-01-15 09:20',
    },
  ],
  
  // Recent Activity
  recentActivity: [
    {
      id: 1,
      type: 'bias_detected',
      model: 'GPT-4 Financial Advisor',
      severity: 'critical',
      time: '2 minutes ago',
      user: 'Dr. Sarah Chen',
      biasType: 'Gender Bias'
    },
    {
      id: 2,
      type: 'model_deployed',
      model: 'ResNet-152 Image Classifier',
      severity: 'info',
      time: '15 minutes ago',
      user: 'AI Team',
      biasType: null
    },
    {
      id: 3,
      type: 'bias_testing',
      model: 'DALL-E 3 Art Generator',
      severity: 'warning',
      time: '1 hour ago',
      user: 'System',
      biasType: 'Cultural Bias'
    },
  ],
  
  // AI Compliance Status
  complianceStatus: [
    { framework: 'EU AI Act', status: 'compliant', score: 95 },
    { framework: 'NIST AI RMF', status: 'compliant', score: 88 },
    { framework: 'ISO/IEC 23053', status: 'partial', score: 72 },
    { framework: 'IEEE 2859', status: 'compliant', score: 91 },
  ],
};

export default function Dashboard3D() {
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

  if (isLoading) {
    return (
      <Center h="100vh">
        <Stack align="center" gap="xl">
          <ThemeIcon size="xl" radius="md" color="blue" variant="light">
            <IconBrain size="2rem" />
          </ThemeIcon>
          <Text size="xl" fw={600}>Loading AI Governance Dashboard...</Text>
          <Loader size="lg" />
        </Stack>
      </Center>
    );
  }

  return (
    <Box
      style={{
        background: colorScheme === 'dark' 
          ? 'radial-gradient(ellipse at center, #0a0a0a 0%, #000000 100%)'
          : 'radial-gradient(ellipse at center, #f8f9fa 0%, #e9ecef 100%)',
        minHeight: '100vh',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* 3D Background Effects */}
      <Box
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: `
            radial-gradient(circle at 20% 80%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
            radial-gradient(circle at 80% 20%, rgba(255, 119, 198, 0.3) 0%, transparent 50%),
            radial-gradient(circle at 40% 40%, rgba(120, 219, 255, 0.2) 0%, transparent 50%)
          `,
          animation: 'float 20s ease-in-out infinite',
        }}
      />
      
      <Container size="xl" py="xl" style={{ position: 'relative', zIndex: 1 }}>
        {/* Futuristic Header */}
        <Group justify="space-between" mb="xl">
          <div>
            <Title 
              order={1} 
              size="h1" 
              mb="xs"
              style={{
                background: 'linear-gradient(45deg, #00d4ff, #ff00ff, #00ff88)',
                backgroundSize: '200% 200%',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                animation: 'gradientShift 3s ease-in-out infinite',
                textShadow: '0 0 30px rgba(0, 212, 255, 0.5)',
                fontFamily: 'monospace',
                letterSpacing: '2px',
              }}
            >
              AI GOVERNANCE CENTER
            </Title>
            <Text 
              c="dimmed" 
              size="lg"
              style={{
                textShadow: '0 0 10px rgba(255, 255, 255, 0.3)',
                fontFamily: 'monospace',
              }}
            >
              Neural Network Monitoring & Bias Detection
            </Text>
          </div>
          <Group>
            <Button
              variant="light"
              leftSection={<IconRefresh size="1rem" />}
              onClick={handleRunBiasTest}
              loading={isScanning}
              style={{
                background: 'linear-gradient(45deg, #00d4ff, #0099cc)',
                border: '1px solid rgba(0, 212, 255, 0.3)',
                boxShadow: '0 0 20px rgba(0, 212, 255, 0.4)',
                color: 'white',
                textShadow: '0 0 10px rgba(255, 255, 255, 0.8)',
              }}
            >
              SCAN NEURAL PATTERNS
            </Button>
            <Button
              variant="filled"
              leftSection={<IconPlus size="1rem" />}
              style={{
                background: 'linear-gradient(45deg, #ff00ff, #cc0099)',
                border: '1px solid rgba(255, 0, 255, 0.3)',
                boxShadow: '0 0 20px rgba(255, 0, 255, 0.4)',
                color: 'white',
                textShadow: '0 0 10px rgba(255, 255, 255, 0.8)',
              }}
            >
              DEPLOY MODEL
            </Button>
          </Group>
        </Group>

        {/* 3D Metrics Grid */}
        <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }} mb="xl">
          {/* Total Models - 3D Card */}
          <Card
            withBorder
            p="lg"
            style={{
              background: 'linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(0, 150, 255, 0.05) 100%)',
              border: '1px solid rgba(0, 212, 255, 0.3)',
              boxShadow: '0 8px 32px rgba(0, 212, 255, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.1)',
              transform: hoveredCard === 'total' ? 'translateY(-5px) scale(1.02)' : 'translateY(0)',
              transition: 'all 0.3s ease',
              backdropFilter: 'blur(10px)',
            }}
            onMouseEnter={() => setHoveredCard('total')}
            onMouseLeave={() => setHoveredCard(null)}
          >
            <Group justify="space-between" mb="md">
              <ThemeIcon
                size="lg"
                radius="md"
                style={{
                  background: 'linear-gradient(45deg, #00d4ff, #0099cc)',
                  boxShadow: '0 0 20px rgba(0, 212, 255, 0.5)',
                }}
              >
                <IconBrain size="1.5rem" />
              </ThemeIcon>
              <Badge
                color="blue"
                variant="light"
                style={{
                  background: 'rgba(0, 212, 255, 0.2)',
                  border: '1px solid rgba(0, 212, 255, 0.3)',
                }}
              >
                ACTIVE
              </Badge>
            </Group>
            <Text size="xs" tt="uppercase" fw={700} c="dimmed" mb="xs">
              TOTAL MODELS
            </Text>
            <Text size="2rem" fw={700} style={{ color: '#00d4ff' }}>
              {data.totalModels}
            </Text>
            <Text size="sm" c="dimmed">
              {data.activeModels} active, {data.modelsInTesting} testing
            </Text>
          </Card>

          {/* Bias Alerts - 3D Card */}
          <Card
            withBorder
            p="lg"
            style={{
              background: 'linear-gradient(135deg, rgba(255, 0, 255, 0.1) 0%, rgba(200, 0, 200, 0.05) 100%)',
              border: '1px solid rgba(255, 0, 255, 0.3)',
              boxShadow: '0 8px 32px rgba(255, 0, 255, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.1)',
              transform: hoveredCard === 'bias' ? 'translateY(-5px) scale(1.02)' : 'translateY(0)',
              transition: 'all 0.3s ease',
              backdropFilter: 'blur(10px)',
            }}
            onMouseEnter={() => setHoveredCard('bias')}
            onMouseLeave={() => setHoveredCard(null)}
          >
            <Group justify="space-between" mb="md">
              <ThemeIcon
                size="lg"
                radius="md"
                style={{
                  background: 'linear-gradient(45deg, #ff00ff, #cc0099)',
                  boxShadow: '0 0 20px rgba(255, 0, 255, 0.5)',
                }}
              >
                <IconAlertTriangle size="1.5rem" />
              </ThemeIcon>
              <Badge
                color="red"
                variant="light"
                style={{
                  background: 'rgba(255, 0, 255, 0.2)',
                  border: '1px solid rgba(255, 0, 255, 0.3)',
                }}
              >
                {data.criticalBias} CRITICAL
              </Badge>
            </Group>
            <Text size="xs" tt="uppercase" fw={700} c="dimmed" mb="xs">
              BIAS ALERTS
            </Text>
            <Text size="2rem" fw={700} style={{ color: '#ff00ff' }}>
              {data.biasAlerts}
            </Text>
            <Text size="sm" c="dimmed">
              {data.criticalBias} critical, {data.biasAlerts - data.criticalBias} warning
            </Text>
          </Card>

          {/* Fairness Score - 3D Card */}
          <Card
            withBorder
            p="lg"
            style={{
              background: 'linear-gradient(135deg, rgba(0, 255, 136, 0.1) 0%, rgba(0, 200, 100, 0.05) 100%)',
              border: '1px solid rgba(0, 255, 136, 0.3)',
              boxShadow: '0 8px 32px rgba(0, 255, 136, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.1)',
              transform: hoveredCard === 'fairness' ? 'translateY(-5px) scale(1.02)' : 'translateY(0)',
              transition: 'all 0.3s ease',
              backdropFilter: 'blur(10px)',
            }}
            onMouseEnter={() => setHoveredCard('fairness')}
            onMouseLeave={() => setHoveredCard(null)}
          >
            <Group justify="space-between" mb="md">
              <ThemeIcon
                size="lg"
                radius="md"
                style={{
                  background: 'linear-gradient(45deg, #00ff88, #00cc66)',
                  boxShadow: '0 0 20px rgba(0, 255, 136, 0.5)',
                }}
              >
                <IconTarget size="1.5rem" />
              </ThemeIcon>
              <Badge
                color="green"
                variant="light"
                style={{
                  background: 'rgba(0, 255, 136, 0.2)',
                  border: '1px solid rgba(0, 255, 136, 0.3)',
                }}
              >
                EXCELLENT
              </Badge>
            </Group>
            <Text size="xs" tt="uppercase" fw={700} c="dimmed" mb="xs">
              FAIRNESS SCORE
            </Text>
            <Text size="2rem" fw={700} style={{ color: '#00ff88' }}>
              {data.fairnessScore}%
            </Text>
            <Text size="sm" c="dimmed">
              Above industry average
            </Text>
          </Card>

          {/* Ethical Score - 3D Card */}
          <Card
            withBorder
            p="lg"
            style={{
              background: 'linear-gradient(135deg, rgba(255, 255, 0, 0.1) 0%, rgba(200, 200, 0, 0.05) 100%)',
              border: '1px solid rgba(255, 255, 0, 0.3)',
              boxShadow: '0 8px 32px rgba(255, 255, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.1)',
              transform: hoveredCard === 'ethical' ? 'translateY(-5px) scale(1.02)' : 'translateY(0)',
              transition: 'all 0.3s ease',
              backdropFilter: 'blur(10px)',
            }}
            onMouseEnter={() => setHoveredCard('ethical')}
            onMouseLeave={() => setHoveredCard(null)}
          >
            <Group justify="space-between" mb="md">
              <ThemeIcon
                size="lg"
                radius="md"
                style={{
                  background: 'linear-gradient(45deg, #ffff00, #cccc00)',
                  boxShadow: '0 0 20px rgba(255, 255, 0, 0.5)',
                }}
              >
                <IconShield size="1.5rem" />
              </ThemeIcon>
              <Badge
                color="yellow"
                variant="light"
                style={{
                  background: 'rgba(255, 255, 0, 0.2)',
                  border: '1px solid rgba(255, 255, 0, 0.3)',
                }}
              >
                COMPLIANT
              </Badge>
            </Group>
            <Text size="xs" tt="uppercase" fw={700} c="dimmed" mb="xs">
              ETHICAL SCORE
            </Text>
            <Text size="2rem" fw={700} style={{ color: '#ffff00' }}>
              {data.ethicalScore}%
            </Text>
            <Text size="sm" c="dimmed">
              Regulatory compliance
            </Text>
          </Card>
        </SimpleGrid>

        {/* 3D Model Type Cards */}
        <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }} mb="xl">
          {Object.entries(data.modelTypes).map(([type, info]) => (
            <Card
              key={type}
              withBorder
              p="lg"
              style={{
                background: `linear-gradient(135deg, ${
                  info.status === 'critical' ? 'rgba(255, 0, 0, 0.1)' :
                  info.status === 'warning' ? 'rgba(255, 165, 0, 0.1)' :
                  'rgba(0, 255, 0, 0.1)'
                } 0%, ${
                  info.status === 'critical' ? 'rgba(200, 0, 0, 0.05)' :
                  info.status === 'warning' ? 'rgba(200, 100, 0, 0.05)' :
                  'rgba(0, 200, 0, 0.05)'
                } 100%)`,
                border: `1px solid ${
                  info.status === 'critical' ? 'rgba(255, 0, 0, 0.3)' :
                  info.status === 'warning' ? 'rgba(255, 165, 0, 0.3)' :
                  'rgba(0, 255, 0, 0.3)'
                }`,
                boxShadow: `0 8px 32px ${
                  info.status === 'critical' ? 'rgba(255, 0, 0, 0.2)' :
                  info.status === 'warning' ? 'rgba(255, 165, 0, 0.2)' :
                  'rgba(0, 255, 0, 0.2)'
                }, inset 0 1px 0 rgba(255, 255, 255, 0.1)`,
                transform: hoveredCard === type ? 'translateY(-5px) scale(1.02)' : 'translateY(0)',
                transition: 'all 0.3s ease',
                backdropFilter: 'blur(10px)',
              }}
              onMouseEnter={() => setHoveredCard(type)}
              onMouseLeave={() => setHoveredCard(null)}
            >
              <Group justify="space-between" mb="md">
                <ThemeIcon
                  size="lg"
                  radius="md"
                  style={{
                    background: `linear-gradient(45deg, ${
                      info.status === 'critical' ? '#ff0000, #cc0000' :
                      info.status === 'warning' ? '#ffa500, #cc8400' :
                      '#00ff00, #00cc00'
                    })`,
                    boxShadow: `0 0 20px ${
                      info.status === 'critical' ? 'rgba(255, 0, 0, 0.5)' :
                      info.status === 'warning' ? 'rgba(255, 165, 0, 0.5)' :
                      'rgba(0, 255, 0, 0.5)'
                    }`,
                  }}
                >
                  <IconRobot size="1.5rem" />
                </ThemeIcon>
                <Badge
                  color={info.status === 'critical' ? 'red' : info.status === 'warning' ? 'orange' : 'green'}
                  variant="light"
                  style={{
                    background: `rgba(${
                      info.status === 'critical' ? '255, 0, 0' :
                      info.status === 'warning' ? '255, 165, 0' :
                      '0, 255, 0'
                    }, 0.2)`,
                    border: `1px solid rgba(${
                      info.status === 'critical' ? '255, 0, 0' :
                      info.status === 'warning' ? '255, 165, 0' :
                      '0, 255, 0'
                    }, 0.3)`,
                  }}
                >
                  {info.status.toUpperCase()}
                </Badge>
              </Group>
              <Text size="xs" tt="uppercase" fw={700} c="dimmed" mb="xs">
                {type.toUpperCase().replace(/([A-Z])/g, ' $1').trim()}
              </Text>
              <Text size="2rem" fw={700} style={{ 
                color: info.status === 'critical' ? '#ff0000' :
                       info.status === 'warning' ? '#ffa500' : '#00ff00'
              }}>
                {info.count}
              </Text>
              <Text size="sm" c="dimmed" mt="xs">
                {info.biasAlerts} bias alerts
              </Text>
            </Card>
          ))}
        </SimpleGrid>

        {/* 3D Holographic Charts Section */}
        <Grid mb="xl">
          {/* Neural Network Visualization */}
          <Grid.Col span={{ base: 12, md: 8 }}>
            <Card
              withBorder
              p="lg"
              mb="md"
              style={{
                background: 'linear-gradient(135deg, rgba(0, 0, 0, 0.8) 0%, rgba(20, 20, 40, 0.9) 100%)',
                border: '1px solid rgba(0, 212, 255, 0.3)',
                boxShadow: '0 8px 32px rgba(0, 212, 255, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1)',
                backdropFilter: 'blur(15px)',
                position: 'relative',
                overflow: 'hidden',
              }}
            >
              <Title order={3} mb="md" style={{ color: '#00d4ff', fontFamily: 'monospace' }}>
                NEURAL NETWORK BIAS ANALYSIS
              </Title>
              
              {/* 3D Neural Network Visualization */}
              <Box
                style={{
                  height: '300px',
                  background: `
                    radial-gradient(circle at 30% 30%, rgba(0, 212, 255, 0.3) 0%, transparent 50%),
                    radial-gradient(circle at 70% 70%, rgba(255, 0, 255, 0.3) 0%, transparent 50%),
                    radial-gradient(circle at 50% 50%, rgba(0, 255, 136, 0.2) 0%, transparent 50%)
                  `,
                  position: 'relative',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                {/* Animated Neural Nodes */}
                {Array.from({ length: 12 }).map((_, i) => (
                  <Box
                    key={i}
                    style={{
                      position: 'absolute',
                      width: '20px',
                      height: '20px',
                      borderRadius: '50%',
                      background: `linear-gradient(45deg, ${
                        i % 3 === 0 ? '#00d4ff' : i % 3 === 1 ? '#ff00ff' : '#00ff88'
                      }, ${
                        i % 3 === 0 ? '#0099cc' : i % 3 === 1 ? '#cc0099' : '#00cc66'
                      })`,
                      boxShadow: `0 0 20px ${
                        i % 3 === 0 ? 'rgba(0, 212, 255, 0.8)' : 
                        i % 3 === 1 ? 'rgba(255, 0, 255, 0.8)' : 
                        'rgba(0, 255, 136, 0.8)'
                      }`,
                      left: `${20 + (i % 4) * 20}%`,
                      top: `${20 + Math.floor(i / 4) * 20}%`,
                      animation: `pulse 2s ease-in-out infinite ${i * 0.2}s`,
                    }}
                  />
                ))}
                
                {/* Central AI Brain */}
                <Box
                  style={{
                    width: '80px',
                    height: '80px',
                    borderRadius: '50%',
                    background: 'linear-gradient(45deg, #00d4ff, #ff00ff, #00ff88)',
                    backgroundSize: '200% 200%',
                    animation: 'gradientShift 3s ease-in-out infinite',
                    boxShadow: '0 0 40px rgba(0, 212, 255, 0.8)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <IconBrain size="2rem" style={{ color: 'white' }} />
                </Box>
              </Box>
            </Card>
          </Grid.Col>

          {/* Real-time Metrics */}
          <Grid.Col span={{ base: 12, md: 4 }}>
            <Card
              withBorder
              p="lg"
              mb="md"
              style={{
                background: 'linear-gradient(135deg, rgba(0, 0, 0, 0.8) 0%, rgba(20, 20, 40, 0.9) 100%)',
                border: '1px solid rgba(255, 0, 255, 0.3)',
                boxShadow: '0 8px 32px rgba(255, 0, 255, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1)',
                backdropFilter: 'blur(15px)',
              }}
            >
              <Title order={3} mb="md" style={{ color: '#ff00ff', fontFamily: 'monospace' }}>
                REAL-TIME METRICS
              </Title>
              
              <Stack gap="md">
                {Object.entries(data.biasMetrics).map(([metric, value]) => (
                  <Box key={metric}>
                    <Group justify="space-between" mb="xs">
                      <Text size="sm" style={{ color: '#ff00ff', fontFamily: 'monospace' }}>
                        {metric.toUpperCase().replace(/([A-Z])/g, ' $1').trim()}
                      </Text>
                      <Text size="sm" fw={500} style={{ color: '#00ff88' }}>
                        {(value * 100).toFixed(1)}%
                      </Text>
                    </Group>
                    <Progress
                      value={value * 100}
                      color="grape"
                      size="sm"
                      style={{
                        background: 'rgba(255, 255, 255, 0.1)',
                        '& .mantine-Progress-bar': {
                          background: 'linear-gradient(90deg, #ff00ff, #00ff88)',
                          boxShadow: '0 0 10px rgba(255, 0, 255, 0.5)',
                        }
                      }}
                    />
                  </Box>
                ))}
              </Stack>
            </Card>
          </Grid.Col>
        </Grid>

        {/* 3D Model Performance Table */}
        <Card
          withBorder
          p="lg"
          mb="xl"
          style={{
            background: 'linear-gradient(135deg, rgba(0, 0, 0, 0.8) 0%, rgba(20, 20, 40, 0.9) 100%)',
            border: '1px solid rgba(0, 255, 136, 0.3)',
            boxShadow: '0 8px 32px rgba(0, 255, 136, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1)',
            backdropFilter: 'blur(15px)',
          }}
        >
          <Title order={3} mb="md" style={{ color: '#00ff88', fontFamily: 'monospace' }}>
            MODEL PERFORMANCE MATRIX
          </Title>
          
          <ScrollArea>
            <Table>
              <Table.Thead>
                <Table.Tr style={{ borderBottom: '1px solid rgba(0, 255, 136, 0.3)' }}>
                  <Table.Th style={{ color: '#00ff88', fontFamily: 'monospace' }}>MODEL</Table.Th>
                  <Table.Th style={{ color: '#00ff88', fontFamily: 'monospace' }}>TYPE</Table.Th>
                  <Table.Th style={{ color: '#00ff88', fontFamily: 'monospace' }}>ACCURACY</Table.Th>
                  <Table.Th style={{ color: '#00ff88', fontFamily: 'monospace' }}>FAIRNESS</Table.Th>
                  <Table.Th style={{ color: '#00ff88', fontFamily: 'monospace' }}>BIAS SCORE</Table.Th>
                  <Table.Th style={{ color: '#00ff88', fontFamily: 'monospace' }}>STATUS</Table.Th>
                  <Table.Th style={{ color: '#00ff88', fontFamily: 'monospace' }}>ACTIONS</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {data.modelPerformance.map((model, index) => (
                  <Table.Tr
                    key={index}
                    style={{
                      borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                      cursor: 'pointer',
                      transition: 'all 0.3s ease',
                    }}
                    onClick={() => handleModelClick(model.name)}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = 'rgba(0, 255, 136, 0.1)';
                      e.currentTarget.style.transform = 'translateX(5px)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'transparent';
                      e.currentTarget.style.transform = 'translateX(0)';
                    }}
                  >
                    <Table.Td style={{ color: 'white', fontFamily: 'monospace' }}>
                      {model.name}
                    </Table.Td>
                    <Table.Td>
                      <Badge
                        color="blue"
                        variant="light"
                        style={{
                          background: 'rgba(0, 212, 255, 0.2)',
                          border: '1px solid rgba(0, 212, 255, 0.3)',
                        }}
                      >
                        {model.type}
                      </Badge>
                    </Table.Td>
                    <Table.Td style={{ color: '#00d4ff' }}>
                      {(model.accuracy * 100).toFixed(1)}%
                    </Table.Td>
                    <Table.Td style={{ color: '#00ff88' }}>
                      {(model.fairness * 100).toFixed(1)}%
                    </Table.Td>
                    <Table.Td style={{ color: '#ff00ff' }}>
                      {(model.biasScore * 100).toFixed(1)}%
                    </Table.Td>
                    <Table.Td>
                      <Badge
                        color={model.status === 'critical' ? 'red' : model.status === 'warning' ? 'orange' : 'green'}
                        variant="light"
                        style={{
                          background: `rgba(${
                            model.status === 'critical' ? '255, 0, 0' :
                            model.status === 'warning' ? '255, 165, 0' :
                            '0, 255, 0'
                          }, 0.2)`,
                          border: `1px solid rgba(${
                            model.status === 'critical' ? '255, 0, 0' :
                            model.status === 'warning' ? '255, 165, 0' :
                            '0, 255, 0'
                          }, 0.3)`,
                        }}
                      >
                        {model.status.toUpperCase()}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs">
                        <ActionIcon
                          variant="light"
                          size="sm"
                          style={{
                            background: 'rgba(0, 212, 255, 0.2)',
                            border: '1px solid rgba(0, 212, 255, 0.3)',
                          }}
                        >
                          <IconEye size="1rem" />
                        </ActionIcon>
                        <ActionIcon
                          variant="light"
                          size="sm"
                          style={{
                            background: 'rgba(255, 0, 255, 0.2)',
                            border: '1px solid rgba(255, 0, 255, 0.3)',
                          }}
                        >
                          <IconDots size="1rem" />
                        </ActionIcon>
                      </Group>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </ScrollArea>
        </Card>
      </Container>

      {/* 3D CSS Animations */}
      <style jsx>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px) rotate(0deg); }
          50% { transform: translateY(-20px) rotate(180deg); }
        }
        
        @keyframes gradientShift {
          0% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
        }
        
        @keyframes pulse {
          0%, 100% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.2); opacity: 0.7; }
        }
        
        @keyframes glow {
          0%, 100% { box-shadow: 0 0 20px rgba(0, 212, 255, 0.5); }
          50% { box-shadow: 0 0 40px rgba(0, 212, 255, 0.8); }
        }
      `}</style>
    </Box>
  );
}
