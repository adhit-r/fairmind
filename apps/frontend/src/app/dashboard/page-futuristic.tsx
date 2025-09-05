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

// Futuristic AI Bias Detection Dashboard Data
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
  
  // AI Model Performance
  modelPerformance: [
    { 
      name: 'GPT-4 Financial Advisor', 
      type: 'LLM', 
      accuracy: 0.96, 
      fairness: 0.78, 
      biasScore: 0.22,
      status: 'critical', 
      lastUpdated: '5 min ago',
      biasTypes: ['Gender', 'Age', 'Socioeconomic']
    },
    { 
      name: 'BERT Sentiment Analysis', 
      type: 'Deep Learning', 
      accuracy: 0.94, 
      fairness: 0.91, 
      biasScore: 0.09,
      status: 'good', 
      lastUpdated: '1 hour ago',
      biasTypes: ['Cultural']
    },
    { 
      name: 'DALL-E Image Generator', 
      type: 'GenAI', 
      accuracy: 0.89, 
      fairness: 0.73, 
      biasScore: 0.27,
      status: 'warning', 
      lastUpdated: '2 hours ago',
      biasTypes: ['Racial', 'Gender', 'Cultural']
    },
    { 
      name: 'Transformer Recommendation', 
      type: 'Deep Learning', 
      accuracy: 0.92, 
      fairness: 0.88, 
      biasScore: 0.12,
      status: 'good', 
      lastUpdated: '3 hours ago',
      biasTypes: ['Age']
    },
  ],
  
  // Real-time AI Activity
  recentActivity: [
    { id: 1, type: 'bias_detected', model: 'GPT-4 Financial Advisor', severity: 'critical', time: '2 min ago', user: 'Dr. Sarah Chen', biasType: 'Gender Bias' },
    { id: 2, type: 'model_deployed', model: 'BERT Sentiment v2.1', severity: 'info', time: '15 min ago', user: 'Mike Johnson', biasType: null },
    { id: 3, type: 'bias_testing', model: 'DALL-E Image Gen', severity: 'warning', time: '1 hour ago', user: 'Alex Rivera', biasType: 'Racial Bias' },
    { id: 4, type: 'security_scan', model: 'Transformer RecSys', severity: 'info', time: '2 hours ago', user: 'Emma Wilson', biasType: null },
  ],
};

export default function FuturisticDashboard() {
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

  // Real-time data updates
  useEffect(() => {
    const interval = setInterval(() => {
      // Simulate real-time updates
      setData(prevData => ({
        ...prevData,
        biasAlerts: prevData.biasAlerts + Math.floor(Math.random() * 2),
        recentActivity: [
          {
            id: Date.now(),
            type: 'bias_detected',
            model: 'GPT-4 Financial Advisor',
            severity: 'critical',
            time: 'Just now',
            user: 'Dr. Sarah Chen',
            biasType: 'Gender Bias'
          },
          ...prevData.recentActivity.slice(0, 3)
        ]
      }));
    }, 10000); // Update every 10 seconds

    return () => clearInterval(interval);
  }, []);

  const handleRunBiasTest = async () => {
    setIsScanning(true);
    // Simulate bias testing
    await new Promise(resolve => setTimeout(resolve, 2000));
    setIsScanning(false);
    
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
  };

  const handleModelClick = (modelName: string) => {
    setSelectedModel(selectedModel === modelName ? null : modelName);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'good': return 'green';
      case 'warning': return 'yellow';
      case 'critical': return 'red';
      case 'info': return 'blue';
      default: return 'gray';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'good': return <IconCheck size="1rem" />;
      case 'warning': return <IconAlertTriangle size="1rem" />;
      case 'critical': return <IconX size="1rem" />;
      default: return <IconClock size="1rem" />;
    }
  };

  if (isLoading) {
    return (
      <Box
        style={{
          background: 'linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%)',
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Stack align="center" gap="xl">
          <Box
            style={{
              width: 80,
              height: 80,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 40px rgba(102, 126, 234, 0.5)',
              animation: 'pulse 2s ease-in-out infinite',
            }}
          >
            <IconBrain size={40} color="white" />
          </Box>
          <Text size="xl" c="white" fw={600}>
            Initializing AI Bias Detection...
          </Text>
          <Loader size="lg" color="blue" />
        </Stack>
      </Box>
    );
  }

  return (
    <Box
      style={{
        background: 'linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%)',
        minHeight: '100vh',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Animated Background Elements */}
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
          animation: 'pulse 4s ease-in-out infinite alternate',
        }}
      />
      
      <Container size="xl" py="xl" style={{ position: 'relative', zIndex: 1 }}>
        <style jsx>{`
          @keyframes slideIn {
            from {
              opacity: 0;
              transform: translateY(20px);
            }
            to {
              opacity: 1;
              transform: translateY(0);
            }
          }
          
          @keyframes pulse {
            0%, 100% {
              opacity: 1;
            }
            50% {
              opacity: 0.7;
            }
          }
          
          @keyframes glow {
            0%, 100% {
              box-shadow: 0 0 20px rgba(102, 126, 234, 0.5);
            }
            50% {
              box-shadow: 0 0 30px rgba(102, 126, 234, 0.8);
            }
          }
        `}</style>
        {/* Futuristic Header */}
        <Paper
          p="xl"
          mb="xl"
          style={{
            background: 'rgba(255, 255, 255, 0.05)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '20px',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
          }}
        >
          <Group justify="space-between" align="flex-start">
            <div>
              <Group align="center" mb="md">
                <Box
                  style={{
                    width: 60,
                    height: 60,
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: '0 0 30px rgba(102, 126, 234, 0.5)',
                  }}
                >
                  <IconBrain size={30} color="white" />
                </Box>
                <div>
                  <Title order={1} size="h1" c="white" mb="xs">
                    FairMind AI
                  </Title>
                  <Text c="rgba(255, 255, 255, 0.8)" size="lg" fw={500}>
                    Advanced Bias Detection & AI Governance
                  </Text>
                </div>
              </Group>
              
              <Group gap="md">
                <Badge
                  size="lg"
                  variant="gradient"
                  gradient={{ from: 'blue', to: 'cyan' }}
                  style={{ backdropFilter: 'blur(10px)' }}
                >
                  {data.totalModels} AI Models
                </Badge>
                <Badge
                  size="lg"
                  variant="gradient"
                  gradient={{ from: 'red', to: 'pink' }}
                  style={{ backdropFilter: 'blur(10px)' }}
                >
                  {data.biasAlerts} Bias Alerts
                </Badge>
                <Badge
                  size="lg"
                  variant="gradient"
                  gradient={{ from: 'green', to: 'teal' }}
                  style={{ backdropFilter: 'blur(10px)' }}
                >
                  {data.fairnessScore}% Fairness Score
                </Badge>
              </Group>
            </div>
            
            <Group>
              <Button
                leftSection={isScanning ? <Loader size="1rem" /> : <IconRefresh size="1rem" />}
                variant="gradient"
                gradient={{ from: 'blue', to: 'cyan' }}
                size="md"
                style={{ 
                  backdropFilter: 'blur(10px)',
                  transform: isScanning ? 'scale(0.95)' : 'scale(1)',
                  transition: 'all 0.2s ease'
                }}
                onClick={handleRunBiasTest}
                loading={isScanning}
                disabled={isScanning}
              >
                {isScanning ? 'Scanning...' : 'Real-time Scan'}
              </Button>
              <Button
                leftSection={<IconPlus size="1rem" />}
                variant="gradient"
                gradient={{ from: 'purple', to: 'pink' }}
                size="md"
                style={{ 
                  backdropFilter: 'blur(10px)',
                  transition: 'all 0.2s ease'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'scale(1.05)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'scale(1)';
                }}
              >
                Add AI Model
              </Button>
            </Group>
          </Group>
        </Paper>

        {/* Futuristic AI Model Type Cards */}
        <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }} mb="xl">
          {/* LLM Models */}
          <Paper
            p="xl"
            style={{
              background: hoveredCard === 'llm' ? 'rgba(255, 255, 255, 0.08)' : 'rgba(255, 255, 255, 0.05)',
              backdropFilter: 'blur(20px)',
              border: hoveredCard === 'llm' ? '1px solid rgba(102, 126, 234, 0.3)' : '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '20px',
              boxShadow: hoveredCard === 'llm' ? '0 12px 40px rgba(102, 126, 234, 0.2)' : '0 8px 32px rgba(0, 0, 0, 0.1)',
              position: 'relative',
              overflow: 'hidden',
              cursor: 'pointer',
              transform: hoveredCard === 'llm' ? 'translateY(-5px)' : 'translateY(0)',
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            }}
            onMouseEnter={() => setHoveredCard('llm')}
            onMouseLeave={() => setHoveredCard(null)}
            onClick={() => handleModelClick('llm')}
          >
            <Box
              style={{
                position: 'absolute',
                top: 0,
                right: 0,
                width: 100,
                height: 100,
                background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.3) 0%, transparent 70%)',
                borderRadius: '50%',
                transform: 'translate(30px, -30px)',
              }}
            />
            <Group justify="space-between" mb="md" style={{ position: 'relative', zIndex: 1 }}>
              <Box
                style={{
                  width: 50,
                  height: 50,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  borderRadius: '15px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 0 20px rgba(102, 126, 234, 0.5)',
                }}
              >
                <IconBrain size={24} color="white" />
              </Box>
              <Badge
                variant="gradient"
                gradient={{ from: 'blue', to: 'cyan' }}
                style={{ backdropFilter: 'blur(10px)' }}
              >
                LLM
              </Badge>
            </Group>
            <Text fw={700} size="2xl" mb="xs" c="white" style={{ position: 'relative', zIndex: 1 }}>
              {data.modelTypes.llm.count}
            </Text>
            <Text c="rgba(255, 255, 255, 0.7)" size="sm" mb="xs" style={{ position: 'relative', zIndex: 1 }}>
              Large Language Models
            </Text>
            <Progress 
              value={(data.modelTypes.llm.count / data.totalModels) * 100} 
              size="sm" 
              color="blue"
              style={{ position: 'relative', zIndex: 1 }}
            />
            <Text size="xs" c="rgba(255, 255, 255, 0.6)" mt="xs" style={{ position: 'relative', zIndex: 1 }}>
              {data.modelTypes.llm.biasAlerts} bias alerts
            </Text>
            {hoveredCard === 'llm' && (
              <Box
                style={{
                  position: 'absolute',
                  bottom: 10,
                  right: 10,
                  background: 'rgba(102, 126, 234, 0.2)',
                  borderRadius: '8px',
                  padding: '4px 8px',
                  backdropFilter: 'blur(10px)',
                  border: '1px solid rgba(102, 126, 234, 0.3)',
                }}
              >
                <Text size="xs" c="white" fw={500}>
                  Click to explore
                </Text>
              </Box>
            )}
          </Paper>

          {/* Deep Learning Models */}
          <Paper
            p="xl"
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '20px',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            <Box
              style={{
                position: 'absolute',
                top: 0,
                right: 0,
                width: 100,
                height: 100,
                background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.3) 0%, transparent 70%)',
                borderRadius: '50%',
                transform: 'translate(30px, -30px)',
              }}
            />
            <Group justify="space-between" mb="md" style={{ position: 'relative', zIndex: 1 }}>
              <Box
                style={{
                  width: 50,
                  height: 50,
                  background: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)',
                  borderRadius: '15px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 0 20px rgba(34, 197, 94, 0.5)',
                }}
              >
                <IconRobot size={24} color="white" />
              </Box>
              <Badge
                variant="gradient"
                gradient={{ from: 'green', to: 'teal' }}
                style={{ backdropFilter: 'blur(10px)' }}
              >
                Deep Learning
              </Badge>
            </Group>
            <Text fw={700} size="2xl" mb="xs" c="white" style={{ position: 'relative', zIndex: 1 }}>
              {data.modelTypes.deepLearning.count}
            </Text>
            <Text c="rgba(255, 255, 255, 0.7)" size="sm" mb="xs" style={{ position: 'relative', zIndex: 1 }}>
              Neural Networks
            </Text>
            <Progress 
              value={(data.modelTypes.deepLearning.count / data.totalModels) * 100} 
              size="sm" 
              color="green"
              style={{ position: 'relative', zIndex: 1 }}
            />
            <Text size="xs" c="rgba(255, 255, 255, 0.6)" mt="xs" style={{ position: 'relative', zIndex: 1 }}>
              {data.modelTypes.deepLearning.biasAlerts} bias alerts
            </Text>
          </Paper>

          {/* GenAI Models */}
          <Paper
            p="xl"
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '20px',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            <Box
              style={{
                position: 'absolute',
                top: 0,
                right: 0,
                width: 100,
                height: 100,
                background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.3) 0%, transparent 70%)',
                borderRadius: '50%',
                transform: 'translate(30px, -30px)',
              }}
            />
            <Group justify="space-between" mb="md" style={{ position: 'relative', zIndex: 1 }}>
              <Box
                style={{
                  width: 50,
                  height: 50,
                  background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                  borderRadius: '15px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 0 20px rgba(239, 68, 68, 0.5)',
                }}
              >
                <IconTarget size={24} color="white" />
              </Box>
              <Badge
                variant="gradient"
                gradient={{ from: 'red', to: 'pink' }}
                style={{ backdropFilter: 'blur(10px)' }}
              >
                GenAI
              </Badge>
            </Group>
            <Text fw={700} size="2xl" mb="xs" c="white" style={{ position: 'relative', zIndex: 1 }}>
              {data.modelTypes.genAI.count}
            </Text>
            <Text c="rgba(255, 255, 255, 0.7)" size="sm" mb="xs" style={{ position: 'relative', zIndex: 1 }}>
              Generative AI
            </Text>
            <Progress 
              value={(data.modelTypes.genAI.count / data.totalModels) * 100} 
              size="sm" 
              color="red"
              style={{ position: 'relative', zIndex: 1 }}
            />
            <Text size="xs" c="rgba(255, 255, 255, 0.6)" mt="xs" style={{ position: 'relative', zIndex: 1 }}>
              {data.modelTypes.genAI.biasAlerts} bias alerts
            </Text>
          </Paper>

          {/* Traditional Models */}
          <Paper
            p="xl"
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '20px',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            <Box
              style={{
                position: 'absolute',
                top: 0,
                right: 0,
                width: 100,
                height: 100,
                background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.3) 0%, transparent 70%)',
                borderRadius: '50%',
                transform: 'translate(30px, -30px)',
              }}
            />
            <Group justify="space-between" mb="md" style={{ position: 'relative', zIndex: 1 }}>
              <Box
                style={{
                  width: 50,
                  height: 50,
                  background: 'linear-gradient(135deg, #a855f7 0%, #9333ea 100%)',
                  borderRadius: '15px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 0 20px rgba(168, 85, 247, 0.5)',
                }}
              >
                <IconChartBar size={24} color="white" />
              </Box>
              <Badge
                variant="gradient"
                gradient={{ from: 'purple', to: 'pink' }}
                style={{ backdropFilter: 'blur(10px)' }}
              >
                Traditional
              </Badge>
            </Group>
            <Text fw={700} size="2xl" mb="xs" c="white" style={{ position: 'relative', zIndex: 1 }}>
              {data.modelTypes.traditional.count}
            </Text>
            <Text c="rgba(255, 255, 255, 0.7)" size="sm" mb="xs" style={{ position: 'relative', zIndex: 1 }}>
              Classic ML
            </Text>
            <Progress 
              value={(data.modelTypes.traditional.count / data.totalModels) * 100} 
              size="sm" 
              color="purple"
              style={{ position: 'relative', zIndex: 1 }}
            />
            <Text size="xs" c="rgba(255, 255, 255, 0.6)" mt="xs" style={{ position: 'relative', zIndex: 1 }}>
              {data.modelTypes.traditional.biasAlerts} bias alerts
            </Text>
          </Paper>
        </SimpleGrid>

        {/* AI Model Performance Table */}
        <Paper
          p="xl"
          mb="xl"
          style={{
            background: 'rgba(255, 255, 255, 0.05)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '20px',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
          }}
        >
          <Group justify="space-between" mb="xl">
            <Title order={2} c="white">
              AI Model Performance & Bias Analysis
            </Title>
                         <Button
               leftSection={isScanning ? <Loader size="1rem" /> : <IconTestPipe size="1rem" />}
               variant="gradient"
               gradient={{ from: 'orange', to: 'red' }}
               style={{ 
                 backdropFilter: 'blur(10px)',
                 transform: isScanning ? 'scale(0.95)' : 'scale(1)',
                 transition: 'all 0.2s ease'
               }}
               onClick={handleRunBiasTest}
               loading={isScanning}
               disabled={isScanning}
             >
               {isScanning ? 'Testing...' : 'Run Bias Tests'}
             </Button>
          </Group>
          
          <ScrollArea>
            <Table>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th c="rgba(255, 255, 255, 0.8)">Model</Table.Th>
                  <Table.Th c="rgba(255, 255, 255, 0.8)">Type</Table.Th>
                  <Table.Th c="rgba(255, 255, 255, 0.8)">Accuracy</Table.Th>
                  <Table.Th c="rgba(255, 255, 255, 0.8)">Fairness</Table.Th>
                  <Table.Th c="rgba(255, 255, 255, 0.8)">Bias Score</Table.Th>
                  <Table.Th c="rgba(255, 255, 255, 0.8)">Bias Types</Table.Th>
                  <Table.Th c="rgba(255, 255, 255, 0.8)">Status</Table.Th>
                  <Table.Th c="rgba(255, 255, 255, 0.8)">Actions</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                                 {data.modelPerformance.map((model, index) => (
                   <Table.Tr 
                     key={index}
                     style={{
                       cursor: 'pointer',
                       transition: 'all 0.2s ease',
                       background: selectedModel === model.name ? 'rgba(102, 126, 234, 0.1)' : 'transparent',
                       border: selectedModel === model.name ? '1px solid rgba(102, 126, 234, 0.3)' : '1px solid transparent',
                     }}
                     onClick={() => handleModelClick(model.name)}
                     onMouseEnter={(e) => {
                       if (selectedModel !== model.name) {
                         e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
                       }
                     }}
                     onMouseLeave={(e) => {
                       if (selectedModel !== model.name) {
                         e.currentTarget.style.background = 'transparent';
                       }
                     }}
                   >
                    <Table.Td>
                      <Group>
                        <Box
                          style={{
                            width: 40,
                            height: 40,
                            background: `linear-gradient(135deg, ${
                              model.type === 'LLM' ? '#667eea, #764ba2' :
                              model.type === 'Deep Learning' ? '#22c55e, #16a34a' :
                              model.type === 'GenAI' ? '#ef4444, #dc2626' :
                              '#a855f7, #9333ea'
                            })`,
                            borderRadius: '10px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                          }}
                        >
                          {model.type === 'LLM' ? <IconBrain size={20} color="white" /> :
                           model.type === 'Deep Learning' ? <IconRobot size={20} color="white" /> :
                           model.type === 'GenAI' ? <IconTarget size={20} color="white" /> :
                           <IconChartBar size={20} color="white" />}
                        </Box>
                        <div>
                          <Text fw={500} c="white">{model.name}</Text>
                          <Text size="xs" c="rgba(255, 255, 255, 0.6)">{model.lastUpdated}</Text>
                        </div>
                      </Group>
                    </Table.Td>
                    <Table.Td>
                      <Badge
                        variant="gradient"
                        gradient={{
                          from: model.type === 'LLM' ? 'blue' :
                                model.type === 'Deep Learning' ? 'green' :
                                model.type === 'GenAI' ? 'red' : 'purple',
                          to: model.type === 'LLM' ? 'cyan' :
                              model.type === 'Deep Learning' ? 'teal' :
                              model.type === 'GenAI' ? 'pink' : 'pink'
                        }}
                        style={{ backdropFilter: 'blur(10px)' }}
                      >
                        {model.type}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <Text c="white">{(model.accuracy * 100).toFixed(1)}%</Text>
                    </Table.Td>
                    <Table.Td>
                      <Text c="white">{(model.fairness * 100).toFixed(1)}%</Text>
                    </Table.Td>
                    <Table.Td>
                      <Group>
                        <Text c="white">{(model.biasScore * 100).toFixed(1)}%</Text>
                        <Box
                          style={{
                            width: 8,
                            height: 8,
                            borderRadius: '50%',
                            background: model.biasScore > 0.2 ? '#ef4444' : model.biasScore > 0.1 ? '#f59e0b' : '#22c55e',
                            boxShadow: `0 0 10px ${model.biasScore > 0.2 ? '#ef4444' : model.biasScore > 0.1 ? '#f59e0b' : '#22c55e'}`,
                          }}
                        />
                      </Group>
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs">
                        {model.biasTypes.map((bias, idx) => (
                          <Badge key={idx} size="sm" variant="light" color="red">
                            {bias}
                          </Badge>
                        ))}
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
                 </Paper>

         {/* Model Details Panel */}
         {selectedModel && (
           <Paper
             p="xl"
             mb="xl"
             style={{
               background: 'rgba(102, 126, 234, 0.1)',
               backdropFilter: 'blur(20px)',
               border: '1px solid rgba(102, 126, 234, 0.3)',
               borderRadius: '20px',
               boxShadow: '0 8px 32px rgba(102, 126, 234, 0.2)',
               animation: 'slideIn 0.3s ease-out',
             }}
           >
             <Group justify="space-between" mb="md">
               <Title order={3} c="white">
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
                     <Text size="sm" c="rgba(255, 255, 255, 0.7)" mb="xs">Model Type</Text>
                     <Badge variant="gradient" gradient={{ from: 'blue', to: 'cyan' }}>
                       {data.modelPerformance.find(m => m.name === selectedModel)?.type}
                     </Badge>
                   </div>
                   <div>
                     <Text size="sm" c="rgba(255, 255, 255, 0.7)" mb="xs">Accuracy</Text>
                     <Text size="lg" c="white" fw={600}>
                       {(data.modelPerformance.find(m => m.name === selectedModel)?.accuracy! * 100).toFixed(1)}%
                     </Text>
                   </div>
                   <div>
                     <Text size="sm" c="rgba(255, 255, 255, 0.7)" mb="xs">Fairness Score</Text>
                     <Text size="lg" c="white" fw={600}>
                       {(data.modelPerformance.find(m => m.name === selectedModel)?.fairness! * 100).toFixed(1)}%
                     </Text>
                   </div>
                 </Stack>
               </Grid.Col>
               
               <Grid.Col span={{ base: 12, md: 6 }}>
                 <Stack gap="md">
                   <div>
                     <Text size="sm" c="rgba(255, 255, 255, 0.7)" mb="xs">Bias Types Detected</Text>
                     <Group gap="xs">
                       {data.modelPerformance.find(m => m.name === selectedModel)?.biasTypes.map((bias, idx) => (
                         <Badge key={idx} color="red" variant="light">
                           {bias}
                         </Badge>
                       ))}
                     </Group>
                   </div>
                   <div>
                     <Text size="sm" c="rgba(255, 255, 255, 0.7)" mb="xs">Last Updated</Text>
                     <Text c="white">
                       {data.modelPerformance.find(m => m.name === selectedModel)?.lastUpdated}
                     </Text>
                   </div>
                 </Stack>
               </Grid.Col>
             </Grid>
             
             <Group mt="xl" gap="md">
               <Button
                 leftSection={<IconTestPipe size="1rem" />}
                 variant="gradient"
                 gradient={{ from: 'orange', to: 'red' }}
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
           </Paper>
         )}

         {/* Real-time Activity Feed */}
        <Paper
          p="xl"
          style={{
            background: 'rgba(255, 255, 255, 0.05)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '20px',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
          }}
        >
          <Title order={2} c="white" mb="xl">
            Real-time AI Activity
          </Title>
          
          <Timeline active={-1} bulletSize={24} lineWidth={2}>
            {data.recentActivity.map((activity) => (
              <Timeline.Item
                key={activity.id}
                bullet={
                  <Box
                    style={{
                      width: 24,
                      height: 24,
                      background: `linear-gradient(135deg, ${
                        activity.severity === 'critical' ? '#ef4444, #dc2626' :
                        activity.severity === 'warning' ? '#f59e0b, #d97706' :
                        activity.severity === 'info' ? '#3b82f6, #2563eb' : '#6b7280, #4b5563'
                      })`,
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      boxShadow: `0 0 15px ${
                        activity.severity === 'critical' ? 'rgba(239, 68, 68, 0.5)' :
                        activity.severity === 'warning' ? 'rgba(245, 158, 11, 0.5)' :
                        activity.severity === 'info' ? 'rgba(59, 130, 246, 0.5)' : 'rgba(107, 114, 128, 0.5)'
                      }`,
                    }}
                  >
                    {activity.type === 'bias_detected' ? <IconAlertTriangle size={12} color="white" /> :
                     activity.type === 'model_deployed' ? <IconCheck size={12} color="white" /> :
                     activity.type === 'bias_testing' ? <IconTestPipe size={12} color="white" /> :
                     <IconShield size={12} color="white" />}
                  </Box>
                }
                title={
                  <Text c="white" fw={500}>
                    {activity.type === 'bias_detected' ? 'Bias Detected' :
                     activity.type === 'model_deployed' ? 'Model Deployed' :
                     activity.type === 'bias_testing' ? 'Bias Testing' :
                     'Security Scan'}
                  </Text>
                }
              >
                <Text c="rgba(255, 255, 255, 0.8)" size="sm" mb="xs">
                  {activity.model}
                </Text>
                {activity.biasType && (
                  <Badge size="sm" color="red" variant="light" mb="xs">
                    {activity.biasType}
                  </Badge>
                )}
                <Group justify="space-between">
                  <Text size="xs" c="rgba(255, 255, 255, 0.6)">
                    {activity.user}
                  </Text>
                  <Text size="xs" c="rgba(255, 255, 255, 0.6)">
                    {activity.time}
                  </Text>
                </Group>
              </Timeline.Item>
            ))}
          </Timeline>
        </Paper>
      </Container>
    </Box>
  );
}
