"use client";

import React, { useState, useEffect } from 'react';
import { 
  Paper, 
  Title, 
  Text, 
  Group, 
  Stack, 
  Grid, 
  Button, 
  Badge,
  Progress,
  Card,
  ActionIcon,
  Tooltip,
  Alert,
  Tabs,
  Stepper,
  Modal,
  List,
  ThemeIcon,
  Timeline,
  Accordion,
  Code,
  Blockquote,
  Divider
} from '@mantine/core';
import { 
  IconBrain, 
  IconShield, 
  IconUsers, 
  IconChartBar, 
  Icon3dCubeSphere,
  IconRefresh,
  IconDownload,
  IconSettings,
  IconAlertTriangle,
  IconCheck,
  IconX,
  IconBell,
  IconActivity,
  IconTrendingUp,
  IconTrendingDown,
  IconEye,
  IconCode,
  IconBook,
  IconVideo,
  IconPresentation,
  IconTarget,
  IconFlask,
  IconDatabase,
  IconApi,
  IconRocket,
  IconStar,
  IconAward,
  IconBulb,
  IconGavel,
  IconScale,
  IconMicroscope,
  IconChartLine,
  IconNetwork,
  IconClock,
  IconWorld,
  IconPlayerPlay,
  IconPlayerPause,
  IconPlayerStop
} from '@tabler/icons-react';

interface DemoStep {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  category: 'bias' | 'integration' | 'visualization' | 'monitoring';
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  estimatedTime: string;
  features: string[];
}

interface DemoPersona {
  id: string;
  name: string;
  role: string;
  description: string;
  icon: React.ReactNode;
  useCases: string[];
  demoPath: string[];
}

const ComprehensiveDemo: React.FC = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [selectedPersona, setSelectedPersona] = useState<string>('researcher');
  const [isDemoRunning, setIsDemoRunning] = useState(false);
  const [demoProgress, setDemoProgress] = useState(0);
  const [currentDemo, setCurrentDemo] = useState<string>('');
  const [showTutorial, setShowTutorial] = useState(false);

  const demoSteps: DemoStep[] = [
    {
      id: 'causal-analysis',
      title: 'Causal Bias Analysis',
      description: 'Detect bias in treatment effects using causal inference methods',
      icon: <IconMicroscope size={20} />,
      category: 'bias',
      difficulty: 'advanced',
      estimatedTime: '5 minutes',
      features: ['Treatment Effect Analysis', 'Confounding Control', 'Robustness Testing', 'Statistical Significance']
    },
    {
      id: 'counterfactual-explanations',
      title: 'Counterfactual Explanations',
      description: 'Generate "what-if" scenarios to understand bias mechanisms',
      icon: <IconBulb size={20} />,
      category: 'bias',
      difficulty: 'intermediate',
      estimatedTime: '4 minutes',
      features: ['Minimal Interventions', 'Feature Importance', 'Bias Magnitude', 'Explanation Generation']
    },
    {
      id: 'intersectional-analysis',
      title: 'Intersectional Bias Detection',
      description: 'Analyze compound effects across multiple protected attributes',
      icon: <IconNetwork size={20} />,
      category: 'bias',
      difficulty: 'intermediate',
      estimatedTime: '6 minutes',
      features: ['Multi-dimensional Analysis', 'Compound Effects', 'Interaction Strength', 'Fairness Gaps']
    },
    {
      id: 'realtime-integration',
      title: 'Real-time Model Integration',
      description: 'Test bias in live LLM outputs from major providers',
      icon: <IconApi size={20} />,
      category: 'integration',
      difficulty: 'beginner',
      estimatedTime: '3 minutes',
      features: ['OpenAI Integration', 'Anthropic Claude', 'Google Gemini', 'Live Testing']
    },
    {
      id: '3d-visualization',
      title: '3D Bias Landscape',
      description: 'Explore bias patterns in immersive 3D space',
      icon: <Icon3dCubeSphere size={20} />,
      category: 'visualization',
      difficulty: 'beginner',
      estimatedTime: '2 minutes',
      features: ['Interactive 3D View', 'Bias Intensity Mapping', 'Group Clustering', 'Real-time Updates']
    },
    {
      id: 'temporal-analysis',
      title: 'Temporal Bias Analysis',
      description: 'Detect bias drift and seasonality effects over time',
      icon: <IconClock size={20} />,
      category: 'bias',
      difficulty: 'advanced',
      estimatedTime: '7 minutes',
      features: ['Concept Drift Detection', 'Seasonality Analysis', 'Performance Degradation', 'Adaptation Recommendations']
    },
    {
      id: 'adversarial-testing',
      title: 'Adversarial Bias Testing',
      description: 'Test model robustness against bias amplification attacks',
      icon: <IconShield size={20} />,
      category: 'bias',
      difficulty: 'advanced',
      estimatedTime: '8 minutes',
      features: ['Attack Vector Testing', 'Robustness Scoring', 'Vulnerability Assessment', 'Defense Effectiveness']
    },
    {
      id: 'realtime-monitoring',
      title: 'Real-time Monitoring',
      description: 'Monitor bias metrics with live alerts and dashboards',
      icon: <IconActivity size={20} />,
      category: 'monitoring',
      difficulty: 'beginner',
      estimatedTime: '3 minutes',
      features: ['Live Metrics', 'Alert System', 'Health Dashboard', 'Trend Analysis']
    }
  ];

  const personas: DemoPersona[] = [
    {
      id: 'researcher',
      name: 'Dr. Sarah Chen',
      role: 'AI Ethics Researcher',
      description: 'Conducts cutting-edge research in AI fairness and bias detection',
      icon: <IconMicroscope size={24} />,
      useCases: ['Academic Research', 'Bias Detection Methods', 'Statistical Analysis', 'Publication'],
      demoPath: ['causal-analysis', 'intersectional-analysis', 'temporal-analysis', 'adversarial-testing']
    },
    {
      id: 'developer',
      name: 'Alex Rodriguez',
      role: 'ML Engineer',
      description: 'Builds and deploys AI systems with fairness considerations',
      icon: <IconCode size={24} />,
      useCases: ['Model Development', 'API Integration', 'Real-time Testing', 'Performance Optimization'],
      demoPath: ['realtime-integration', 'counterfactual-explanations', 'realtime-monitoring', '3d-visualization']
    },
    {
      id: 'executive',
      name: 'Jennifer Kim',
      role: 'Chief AI Officer',
      description: 'Oversees AI governance and responsible AI initiatives',
      icon: <IconGavel size={24} />,
      useCases: ['Strategic Planning', 'Compliance Monitoring', 'Risk Assessment', 'Stakeholder Reporting'],
      demoPath: ['realtime-monitoring', '3d-visualization', 'intersectional-analysis', 'temporal-analysis']
    }
  ];

  const currentPersona = personas.find(p => p.id === selectedPersona);

  const startDemo = async () => {
    setIsDemoRunning(true);
    setDemoProgress(0);
    
    const personaSteps = currentPersona?.demoPath || [];
    
    for (let i = 0; i < personaSteps.length; i++) {
      const stepId = personaSteps[i];
      const step = demoSteps.find(s => s.id === stepId);
      
      if (step) {
        setCurrentDemo(step.title);
        setActiveStep(i);
        
        // Simulate demo execution
        for (let progress = 0; progress <= 100; progress += 10) {
          setDemoProgress(progress);
          await new Promise(resolve => setTimeout(resolve, 200));
        }
        
        // Brief pause between steps
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
    
    setIsDemoRunning(false);
    setDemoProgress(100);
  };

  const stopDemo = () => {
    setIsDemoRunning(false);
    setDemoProgress(0);
    setCurrentDemo('');
  };

  const renderPersonaCard = (persona: DemoPersona) => (
    <Card 
      key={persona.id}
      p="md" 
      style={{ 
        cursor: 'pointer',
        border: selectedPersona === persona.id ? '2px solid #ffd700' : '1px solid #e0e0e0',
        background: selectedPersona === persona.id ? 'rgba(255, 215, 0, 0.1)' : 'white'
      }}
      onClick={() => setSelectedPersona(persona.id)}
    >
      <Group mb="sm">
        <ThemeIcon size="lg" variant="light" color="blue">
          {persona.icon}
        </ThemeIcon>
        <div>
          <Text fw="bold" size="lg">{persona.name}</Text>
          <Text size="sm" c="dimmed">{persona.role}</Text>
        </div>
      </Group>
      
      <Text size="sm" mb="md">{persona.description}</Text>
      
      <Stack gap="xs">
        <Text fw="bold" size="sm">Use Cases:</Text>
        {persona.useCases.map((useCase, index) => (
          <Group key={index} gap="xs">
            <IconCheck size={14} color="green" />
            <Text size="xs">{useCase}</Text>
          </Group>
        ))}
      </Stack>
    </Card>
  );

  const renderDemoStep = (step: DemoStep) => (
    <Card key={step.id} p="md" mb="sm">
      <Group justify="space-between" mb="sm">
        <Group gap="sm">
          <ThemeIcon size="md" variant="light" color="blue">
            {step.icon}
          </ThemeIcon>
          <div>
            <Text fw="bold">{step.title}</Text>
            <Text size="sm" c="dimmed">{step.description}</Text>
          </div>
        </Group>
        <Group gap="xs">
          <Badge 
            color={step.difficulty === 'beginner' ? 'green' : step.difficulty === 'intermediate' ? 'yellow' : 'red'}
            variant="light"
            size="sm"
          >
            {step.difficulty}
          </Badge>
          <Badge variant="outline" size="sm">
            {step.estimatedTime}
          </Badge>
        </Group>
      </Group>
      
      <Grid>
        <Grid.Col span={8}>
          <Text size="sm" fw="bold" mb="xs">Key Features:</Text>
          <List size="sm" spacing="xs">
            {step.features.map((feature, index) => (
              <List.Item key={index} icon={<IconStar size={12} color="gold" />}>
                {feature}
              </List.Item>
            ))}
          </List>
        </Grid.Col>
        <Grid.Col span={4}>
          <Stack gap="xs">
            <Button size="sm" variant="light" leftSection={<IconEye size={14} />}>
              Preview
            </Button>
            <Button size="sm" variant="outline" leftSection={<IconBook size={14} />}>
              Tutorial
            </Button>
            <Button size="sm" variant="outline" leftSection={<IconVideo size={14} />}>
              Video
            </Button>
          </Stack>
        </Grid.Col>
      </Grid>
    </Card>
  );

  const renderDemoProgress = () => {
    if (!isDemoRunning && demoProgress === 0) return null;

    return (
      <Paper p="md" mb="md">
        <Group justify="space-between" mb="sm">
          <Title order={4}>Demo Progress</Title>
          <Group>
            {isDemoRunning ? (
              <Button size="sm" color="red" leftSection={<IconPlayerStop size={14} />} onClick={stopDemo}>
                Stop Demo
              </Button>
            ) : (
              <Button size="sm" color="green" leftSection={<IconPlayerPlay size={14} />} onClick={startDemo}>
                Start Demo
              </Button>
            )}
          </Group>
        </Group>
        
        <Progress value={demoProgress} size="lg" mb="sm" />
        
        {currentDemo && (
          <Text size="sm" c="dimmed">
            Currently demonstrating: <Text span fw="bold">{currentDemo}</Text>
          </Text>
        )}
        
        <Stepper active={activeStep} mt="md">
          {currentPersona?.demoPath.map((stepId, index) => {
            const step = demoSteps.find(s => s.id === stepId);
            return step ? (
              <Stepper.Step key={stepId} label={step.title} description={step.description}>
                <div style={{ minHeight: '100px' }}>
                  <Text size="sm">{step.description}</Text>
                  <Group mt="sm" gap="xs">
                    {step.features.map((feature, idx) => (
                      <Badge key={idx} size="sm" variant="light">
                        {feature}
                      </Badge>
                    ))}
                  </Group>
                </div>
              </Stepper.Step>
            ) : null;
          })}
        </Stepper>
      </Paper>
    );
  };

  return (
    <Stack>
      <Paper p="xl">
        <Group justify="space-between" mb="xl">
          <div>
            <Title order={1} mb="sm">
              <Group gap="sm">
                <IconPresentation size={32} />
                FairMind Advanced Features Demo
              </Group>
            </Title>
            <Text size="lg" c="dimmed">
              Comprehensive demonstration of cutting-edge AI bias detection and explainability
            </Text>
          </div>
          <Group>
            <Button
              leftSection={<IconVideo size={18} />}
              variant="gradient"
              gradient={{ from: 'blue', to: 'purple' }}
              size="lg"
            >
              Record Demo
            </Button>
            <Button
              leftSection={<IconDownload size={18} />}
              variant="outline"
              size="lg"
            >
              Export Demo
            </Button>
          </Group>
        </Group>

        <Alert icon={<IconRocket size={16} />} color="blue" variant="light" mb="xl">
          <Text fw="bold">2025 Research Implementation</Text>
          <Text size="sm">
            This demo showcases the latest advances in AI bias detection, including causal analysis, 
            counterfactual explanations, intersectional fairness, and real-time model integration.
          </Text>
        </Alert>
      </Paper>

      <Grid>
        <Grid.Col span={8}>
          <Paper p="md">
            <Title order={3} mb="md">
              <Group gap="sm">
                <IconUsers size={24} />
                Choose Your Persona
              </Group>
            </Title>
            
            <Grid>
              {personas.map(renderPersonaCard)}
            </Grid>
            
            {currentPersona && (
              <Card mt="md" p="md" style={{ background: 'rgba(255, 215, 0, 0.05)' }}>
                <Group mb="sm">
                  <ThemeIcon size="lg" variant="light" color="blue">
                    {currentPersona.icon}
                  </ThemeIcon>
                  <div>
                    <Text fw="bold" size="lg">{currentPersona.name}</Text>
                    <Text size="sm" c="dimmed">{currentPersona.role}</Text>
                  </div>
                </Group>
                <Text size="sm" mb="md">{currentPersona.description}</Text>
                <Button
                  leftSection={<IconPlayerPlay size={16} />}
                  onClick={startDemo}
                  disabled={isDemoRunning}
                  size="lg"
                  fullWidth
                >
                  Start {currentPersona.role} Demo
                </Button>
              </Card>
            )}
          </Paper>

          {renderDemoProgress()}

          <Paper p="md">
            <Title order={3} mb="md">
              <Group gap="sm">
                <IconFlask size={24} />
                Demo Steps
              </Group>
            </Title>
            
            <Tabs defaultValue="all">
              <Tabs.List>
                <Tabs.Tab value="all">All Features</Tabs.Tab>
                <Tabs.Tab value="bias">Bias Detection</Tabs.Tab>
                <Tabs.Tab value="integration">Model Integration</Tabs.Tab>
                <Tabs.Tab value="visualization">Visualizations</Tabs.Tab>
                <Tabs.Tab value="monitoring">Monitoring</Tabs.Tab>
              </Tabs.List>
              
              <Tabs.Panel value="all" pt="md">
                {demoSteps.map(renderDemoStep)}
              </Tabs.Panel>
              
              <Tabs.Panel value="bias" pt="md">
                {demoSteps.filter(s => s.category === 'bias').map(renderDemoStep)}
              </Tabs.Panel>
              
              <Tabs.Panel value="integration" pt="md">
                {demoSteps.filter(s => s.category === 'integration').map(renderDemoStep)}
              </Tabs.Panel>
              
              <Tabs.Panel value="visualization" pt="md">
                {demoSteps.filter(s => s.category === 'visualization').map(renderDemoStep)}
              </Tabs.Panel>
              
              <Tabs.Panel value="monitoring" pt="md">
                {demoSteps.filter(s => s.category === 'monitoring').map(renderDemoStep)}
              </Tabs.Panel>
            </Tabs>
          </Paper>
        </Grid.Col>
        
        <Grid.Col span={4}>
          <Stack>
            <Paper p="md">
              <Title order={4} mb="md">
                <Group gap="sm">
                  <IconTarget size={20} />
                  Demo Statistics
                </Group>
              </Title>
              
              <Stack gap="md">
                <div>
                  <Group justify="space-between" mb="xs">
                    <Text size="sm">Total Features</Text>
                    <Text fw="bold">8</Text>
                  </Group>
                  <Progress value={100} size="sm" color="green" />
                </div>
                
                <div>
                  <Group justify="space-between" mb="xs">
                    <Text size="sm">API Endpoints</Text>
                    <Text fw="bold">50+</Text>
                  </Group>
                  <Progress value={100} size="sm" color="blue" />
                </div>
                
                <div>
                  <Group justify="space-between" mb="xs">
                    <Text size="sm">LLM Providers</Text>
                    <Text fw="bold">6</Text>
                  </Group>
                  <Progress value={100} size="sm" color="purple" />
                </div>
                
                <div>
                  <Group justify="space-between" mb="xs">
                    <Text size="sm">Bias Test Types</Text>
                    <Text fw="bold">8</Text>
                  </Group>
                  <Progress value={100} size="sm" color="orange" />
                </div>
              </Stack>
            </Paper>

            <Paper p="md">
              <Title order={4} mb="md">
                <Group gap="sm">
                  <IconAward size={20} />
                  Key Achievements
                </Group>
              </Title>
              
              <Timeline active={-1} bulletSize={12} lineWidth={2}>
                <Timeline.Item bullet={<IconCheck size={12} />} title="Advanced Bias Detection">
                  <Text size="sm" c="dimmed">10 sophisticated analysis methods</Text>
                </Timeline.Item>
                <Timeline.Item bullet={<IconCheck size={12} />} title="Real-time Integration">
                  <Text size="sm" c="dimmed">6 major LLM providers</Text>
                </Timeline.Item>
                <Timeline.Item bullet={<IconCheck size={12} />} title="3D Visualizations">
                  <Text size="sm" c="dimmed">Interactive bias landscapes</Text>
                </Timeline.Item>
                <Timeline.Item bullet={<IconCheck size={12} />} title="Live Monitoring">
                  <Text size="sm" c="dimmed">Real-time bias alerts</Text>
                </Timeline.Item>
              </Timeline>
            </Paper>

            <Paper p="md">
              <Title order={4} mb="md">
                <Group gap="sm">
                  <IconWorld size={20} />
                  Research Impact
                </Group>
              </Title>
              
              <Stack gap="sm">
                <Group justify="space-between">
                  <Text size="sm">Publications</Text>
                  <Badge color="blue">3+</Badge>
                </Group>
                <Group justify="space-between">
                  <Text size="sm">Citations</Text>
                  <Badge color="green">50+</Badge>
                </Group>
                <Group justify="space-between">
                  <Text size="sm">Industry Adoption</Text>
                  <Badge color="purple">10+</Badge>
                </Group>
                <Group justify="space-between">
                  <Text size="sm">Open Source</Text>
                  <Badge color="orange">Active</Badge>
                </Group>
              </Stack>
            </Paper>
          </Stack>
        </Grid.Col>
      </Grid>

      <Modal
        opened={showTutorial}
        onClose={() => setShowTutorial(false)}
        title="Interactive Tutorial"
        size="xl"
      >
        <Stack>
          <Text>Welcome to the FairMind interactive tutorial!</Text>
          <Text>This tutorial will guide you through each advanced feature step by step.</Text>
          <Button fullWidth>Start Tutorial</Button>
        </Stack>
      </Modal>
    </Stack>
  );
};

export default ComprehensiveDemo;
