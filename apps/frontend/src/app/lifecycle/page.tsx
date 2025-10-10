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
  Timeline,
  ActionIcon,
  Modal,
  TextInput,
  Select,
  Textarea,
  Progress,
  Alert,
  Tabs,
  Table,
  Stepper,
  RingProgress,
} from '@mantine/core';
import {
  IconGitBranch,
  IconPlayerPlay,
  IconPlayerPause,
  IconRefresh,
  IconCheck,
  IconX,
  IconClock,
  IconDatabase,
  IconSettings,
  IconChartLine,
  IconDownload,
  IconUpload,
  IconEye,
  IconEdit,
  IconTrash,
  IconPlus,
  IconAlertTriangle,
  IconRocket,
  IconFlag,
  IconCode,
} from '@tabler/icons-react';
import { useApi } from '@/hooks/useApi';

interface LifecycleStage {
  id: string;
  name: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'skipped';
  startDate?: string;
  endDate?: string;
  duration?: number;
  artifacts: string[];
  metrics: Record<string, number>;
  issues: number;
  description: string;
}

interface MLProject {
  id: string;
  name: string;
  description: string;
  status: 'planning' | 'development' | 'testing' | 'staging' | 'production' | 'archived';
  currentStage: string;
  progress: number;
  owner: string;
  team: string[];
  createdAt: string;
  lastUpdated: string;
  stages: LifecycleStage[];
  compliance: string[];
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
}

interface LifecycleStats {
  totalProjects: number;
  activeProjects: number;
  completedProjects: number;
  failedProjects: number;
  averageDuration: number;
  successRate: number;
}

export default function LifecyclePage() {
  const [projects, setProjects] = useState<MLProject[]>([]);
  const [stats, setStats] = useState<LifecycleStats | null>(null);
  const [selectedProject, setSelectedProject] = useState<MLProject | null>(null);
  const [loading, setLoading] = useState(true);
  const [modalOpened, setModalOpened] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const { data, loading: apiLoading, error } = useApi('/api/lifecycle');
  
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
    fetchLifecycleData();
  }, []);

  const fetchLifecycleData = async () => {
    try {
      setLoading(true);
      const [projectsData, statsData] = await Promise.all([
        fetchData('/api/lifecycle/projects'),
        fetchData('/api/lifecycle/stats')
      ]);
      setProjects(projectsData || mockProjects);
      setStats(statsData || mockStats);
    } catch (error) {
      console.error('Error fetching lifecycle data:', error);
      setProjects(mockProjects);
      setStats(mockStats);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'planning': return 'blue';
      case 'development': return 'orange';
      case 'testing': return 'yellow';
      case 'staging': return 'grape';
      case 'production': return 'green';
      case 'archived': return 'gray';
      default: return 'gray';
    }
  };

  const getStageStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'green';
      case 'in_progress': return 'blue';
      case 'failed': return 'red';
      case 'pending': return 'gray';
      case 'skipped': return 'yellow';
      default: return 'gray';
    }
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low': return 'green';
      case 'medium': return 'yellow';
      case 'high': return 'orange';
      case 'critical': return 'red';
      default: return 'gray';
    }
  };

  const mockStats: LifecycleStats = {
    totalProjects: 84,
    activeProjects: 23,
    completedProjects: 47,
    failedProjects: 8,
    averageDuration: 128,
    successRate: 85.5
  };

  const mockProjects: MLProject[] = [
    {
      id: '1',
      name: 'Customer Sentiment Analysis',
      description: 'ML model to analyze customer sentiment from reviews and feedback',
      status: 'production',
      currentStage: 'monitoring',
      progress: 100,
      owner: 'Sarah Chen',
      team: ['Sarah Chen', 'Mike Johnson', 'Lisa Wang'],
      createdAt: '2024-01-01T09:00:00Z',
      lastUpdated: '2024-01-20T14:30:00Z',
      compliance: ['GDPR', 'SOX'],
      riskLevel: 'low',
      stages: [
        {
          id: 'data_collection',
          name: 'Data Collection',
          status: 'completed',
          startDate: '2024-01-01T09:00:00Z',
          endDate: '2024-01-05T17:00:00Z',
          duration: 4,
          artifacts: ['dataset_v1.csv', 'data_quality_report.pdf'],
          metrics: { quality_score: 0.95, completeness: 0.98 },
          issues: 0,
          description: 'Collect and validate customer review data'
        },
        {
          id: 'preprocessing',
          name: 'Data Preprocessing',
          status: 'completed',
          startDate: '2024-01-06T09:00:00Z',
          endDate: '2024-01-10T17:00:00Z',
          duration: 4,
          artifacts: ['processed_dataset.csv', 'preprocessing_pipeline.py'],
          metrics: { cleaned_records: 50000, feature_count: 25 },
          issues: 2,
          description: 'Clean and preprocess the collected data'
        },
        {
          id: 'model_training',
          name: 'Model Training',
          status: 'completed',
          startDate: '2024-01-11T09:00:00Z',
          endDate: '2024-01-15T17:00:00Z',
          duration: 4,
          artifacts: ['model_v1.pkl', 'training_metrics.json'],
          metrics: { accuracy: 0.92, f1_score: 0.89 },
          issues: 1,
          description: 'Train and validate the sentiment analysis model'
        }
      ]
    },
    {
      id: '2',
      name: 'Fraud Detection System',
      description: 'Real-time fraud detection for financial transactions',
      status: 'testing',
      currentStage: 'validation',
      progress: 75,
      owner: 'David Rodriguez',
      team: ['David Rodriguez', 'Emma Thompson', 'Alex Kim'],
      createdAt: '2024-01-10T10:00:00Z',
      lastUpdated: '2024-01-20T16:45:00Z',
      compliance: ['PCI DSS', 'SOX', 'GDPR'],
      riskLevel: 'high',
      stages: [
        {
          id: 'data_collection',
          name: 'Data Collection',
          status: 'completed',
          startDate: '2024-01-10T10:00:00Z',
          endDate: '2024-01-12T18:00:00Z',
          duration: 2,
          artifacts: ['transaction_data.csv', 'fraud_labels.csv'],
          metrics: { total_transactions: 1000000, fraud_rate: 0.02 },
          issues: 0,
          description: 'Collect historical transaction and fraud data'
        },
        {
          id: 'feature_engineering',
          name: 'Feature Engineering',
          status: 'in_progress',
          startDate: '2024-01-13T09:00:00Z',
          artifacts: ['feature_pipeline.py'],
          metrics: { features_created: 150 },
          issues: 3,
          description: 'Create and validate fraud detection features'
        }
      ]
    }
  ];

  if (loading) {
    return (
      <Container size="xl" py="xl">
        <Text>Loading ML Lifecycle Management...</Text>
      </Container>
    );
  }

  return (
    <Container size="xl" py="xl">
      <Group justify="space-between" mb="xl">
        <div>
          <Title order={1} c="white" mb="xs">
            ML Lifecycle Management
          </Title>
          <Text size="lg" c="dimmed">
            Track and manage machine learning project lifecycles from development to production
          </Text>
        </div>
        <Group>
          <Button
            leftSection={<IconRefresh size={16} />}
            variant="outline"
            onClick={fetchLifecycleData}
          >
            Refresh
          </Button>
          <Button
            leftSection={<IconDownload size={16} />}
            variant="light"
          >
            Export Report
          </Button>
          <Button
            leftSection={<IconPlus size={16} />}
            onClick={() => setModalOpened(true)}
          >
            New Project
          </Button>
        </Group>
      </Group>

      {/* Statistics Cards */}
      <SimpleGrid cols={{ base: 1, md: 2, lg: 6 }} mb="xl">
        <Card className="neo-card" padding="lg">
          <Group justify="apart">
            <div>
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                Total Projects
              </Text>
              <Text fw={700} size="xl" c="white">
                {stats?.totalProjects}
              </Text>
            </div>
            <IconGitBranch size={24} color="var(--mantine-color-blue-6)" />
          </Group>
        </Card>

        <Card className="neo-card" padding="lg">
          <Group justify="apart">
            <div>
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                Active Projects
              </Text>
              <Text fw={700} size="xl" c="blue">
                {stats?.activeProjects}
              </Text>
            </div>
            <IconPlayerPlay size={24} color="var(--mantine-color-blue-6)" />
          </Group>
        </Card>

        <Card className="neo-card" padding="lg">
          <Group justify="apart">
            <div>
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                Completed
              </Text>
              <Text fw={700} size="xl" c="green">
                {stats?.completedProjects}
              </Text>
            </div>
            <IconCheck size={24} color="var(--mantine-color-green-6)" />
          </Group>
        </Card>

        <Card className="neo-card" padding="lg">
          <Group justify="apart">
            <div>
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                Failed Projects
              </Text>
              <Text fw={700} size="xl" c="red">
                {stats?.failedProjects}
              </Text>
            </div>
            <IconX size={24} color="var(--mantine-color-red-6)" />
          </Group>
        </Card>

        <Card className="neo-card" padding="lg">
          <Group justify="apart">
            <div>
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                Avg Duration
              </Text>
              <Text fw={700} size="xl" c="white">
                {stats?.averageDuration}d
              </Text>
            </div>
            <IconClock size={24} color="var(--mantine-color-orange-6)" />
          </Group>
        </Card>

        <Card className="neo-card" padding="lg">
          <Group justify="apart">
            <div>
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                Success Rate
              </Text>
              <Text fw={700} size="xl" c="green">
                {stats?.successRate}%
              </Text>
            </div>
            <IconChartLine size={24} color="var(--mantine-color-green-6)" />
          </Group>
          <Progress value={stats?.successRate || 0} size="sm" mt="xs" color="green" />
        </Card>
      </SimpleGrid>

      <Tabs value={activeTab} onChange={(value) => setActiveTab(value || 'overview')}>
        <Tabs.List>
          <Tabs.Tab value="overview" leftSection={<IconGitBranch size={16} />}>
            Projects Overview
          </Tabs.Tab>
          <Tabs.Tab value="stages" leftSection={<IconFlag size={16} />}>
            Stage Management
          </Tabs.Tab>
          <Tabs.Tab value="workflows" leftSection={<IconSettings size={16} />}>
            Workflows
          </Tabs.Tab>
          <Tabs.Tab value="analytics" leftSection={<IconChartLine size={16} />}>
            Analytics
          </Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="overview" pt="xl">
          <Card className="neo-card" padding="lg">
            <Group justify="space-between" mb="md">
              <Title order={3} c="white">Active Projects</Title>
              <Group>
                <Select
                  placeholder="Filter by status"
                  data={['All', 'Planning', 'Development', 'Testing', 'Staging', 'Production']}
                  w={150}
                />
                <Select
                  placeholder="Filter by owner"
                  data={['All', 'Sarah Chen', 'David Rodriguez', 'Emma Thompson']}
                  w={150}
                />
              </Group>
            </Group>

            <Table striped highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Project</Table.Th>
                  <Table.Th>Owner</Table.Th>
                  <Table.Th>Status</Table.Th>
                  <Table.Th>Progress</Table.Th>
                  <Table.Th>Current Stage</Table.Th>
                  <Table.Th>Risk Level</Table.Th>
                  <Table.Th>Last Updated</Table.Th>
                  <Table.Th>Actions</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {projects.map((project) => (
                  <Table.Tr key={project.id}>
                    <Table.Td>
                      <div>
                        <Text fw={500} c="white">{project.name}</Text>
                        <Text size="xs" c="dimmed">{project.description}</Text>
                      </div>
                    </Table.Td>
                    <Table.Td>
                      <Text c="white">{project.owner}</Text>
                    </Table.Td>
                    <Table.Td>
                      <Badge color={getStatusColor(project.status)} variant="light">
                        {project.status}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <Group>
                        <RingProgress
                          size={40}
                          thickness={4}
                          sections={[{ value: project.progress, color: 'blue' }]}
                          label={
                            <Text size="xs" ta="center">
                              {project.progress}%
                            </Text>
                          }
                        />
                      </Group>
                    </Table.Td>
                    <Table.Td>
                      <Text c="white">{project.currentStage}</Text>
                    </Table.Td>
                    <Table.Td>
                      <Badge color={getRiskColor(project.riskLevel)} variant="light">
                        {project.riskLevel}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <Text c="white" size="sm">
                        {new Date(project.lastUpdated).toLocaleDateString()}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs">
                        <ActionIcon
                          variant="subtle"
                          onClick={() => {
                            setSelectedProject(project);
                            setModalOpened(true);
                          }}
                        >
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

        <Tabs.Panel value="stages" pt="xl">
          <Card className="neo-card" padding="lg">
            <Title order={3} c="white" mb="md">Project Stages</Title>
            
            {selectedProject ? (
              <Stack>
                <Group justify="space-between">
                  <Title order={4} c="white">{selectedProject.name}</Title>
                  <Badge color={getStatusColor(selectedProject.status)}>
                    {selectedProject.status}
                  </Badge>
                </Group>
                
                <Timeline active={-1} bulletSize={24} lineWidth={2}>
                  {selectedProject.stages.map((stage, index) => (
                    <Timeline.Item
                      key={stage.id}
                      bullet={
                        stage.status === 'completed' ? <IconCheck size={16} /> :
                        stage.status === 'in_progress' ? <IconPlayerPlay size={16} /> :
                        stage.status === 'failed' ? <IconX size={16} /> :
                        <IconClock size={16} />
                      }
                      title={stage.name}
                    >
                      <Text c="dimmed" size="sm" mb="xs">
                        {stage.description}
                      </Text>
                      <Group gap="lg">
                        <Badge color={getStageStatusColor(stage.status)} variant="light">
                          {stage.status}
                        </Badge>
                        {stage.duration && (
                          <Text size="xs" c="dimmed">
                            Duration: {stage.duration} days
                          </Text>
                        )}
                        {stage.issues > 0 && (
                          <Text size="xs" c="red">
                            {stage.issues} issues
                          </Text>
                        )}
                      </Group>
                      {stage.artifacts.length > 0 && (
                        <Text size="xs" mt="xs" c="dimmed">
                          Artifacts: {stage.artifacts.join(', ')}
                        </Text>
                      )}
                    </Timeline.Item>
                  ))}
                </Timeline>
              </Stack>
            ) : (
              <Alert icon={<IconAlertTriangle size={16} />}>
                Select a project from the overview tab to view its stages.
              </Alert>
            )}
          </Card>
        </Tabs.Panel>

        <Tabs.Panel value="workflows" pt="xl">
          <Card className="neo-card" padding="lg">
            <Title order={3} c="white" mb="md">Workflow Templates</Title>
            
            <SimpleGrid cols={{ base: 1, md: 2 }} spacing="md">
              <Card className="neo-card" padding="md">
                <Group justify="space-between" mb="md">
                  <Text fw={500} c="white">Standard ML Pipeline</Text>
                  <Badge variant="light">Default</Badge>
                </Group>
                
                <Stepper active={-1} orientation="vertical" size="sm">
                  <Stepper.Step label="Data Collection" description="Gather and validate data" />
                  <Stepper.Step label="Data Preprocessing" description="Clean and prepare data" />
                  <Stepper.Step label="Feature Engineering" description="Create model features" />
                  <Stepper.Step label="Model Training" description="Train and validate model" />
                  <Stepper.Step label="Model Evaluation" description="Test model performance" />
                  <Stepper.Step label="Deployment" description="Deploy to production" />
                  <Stepper.Step label="Monitoring" description="Monitor performance" />
                </Stepper>
                
                <Button variant="light" fullWidth mt="md" size="sm">
                  Use Template
                </Button>
              </Card>

              <Card className="neo-card" padding="md">
                <Group justify="space-between" mb="md">
                  <Text fw={500} c="white">Computer Vision Pipeline</Text>
                  <Badge variant="light" color="orange">Specialized</Badge>
                </Group>
                
                <Stepper active={-1} orientation="vertical" size="sm">
                  <Stepper.Step label="Image Collection" description="Gather image datasets" />
                  <Stepper.Step label="Image Preprocessing" description="Resize and augment images" />
                  <Stepper.Step label="Annotation" description="Label image data" />
                  <Stepper.Step label="Model Architecture" description="Design CNN architecture" />
                  <Stepper.Step label="Training" description="Train vision model" />
                  <Stepper.Step label="Validation" description="Test on validation set" />
                  <Stepper.Step label="Optimization" description="Optimize for inference" />
                  <Stepper.Step label="Deployment" description="Deploy vision API" />
                </Stepper>
                
                <Button variant="light" fullWidth mt="md" size="sm">
                  Use Template
                </Button>
              </Card>
            </SimpleGrid>
          </Card>
        </Tabs.Panel>

        <Tabs.Panel value="analytics" pt="xl">
          <SimpleGrid cols={{ base: 1, md: 2 }} spacing="md">
            <Card className="neo-card" padding="lg">
              <Title order={4} c="white" mb="md">Project Success Rate by Stage</Title>
              <Text c="dimmed" size="sm" mb="md">
                Percentage of projects that successfully complete each stage
              </Text>
              <Stack>
                <Group justify="space-between">
                  <Text size="sm" c="white">Data Collection</Text>
                  <Text size="sm" c="green">98%</Text>
                </Group>
                <Progress value={98} color="green" size="sm" />
                
                <Group justify="space-between">
                  <Text size="sm" c="white">Preprocessing</Text>
                  <Text size="sm" c="green">94%</Text>
                </Group>
                <Progress value={94} color="green" size="sm" />
                
                <Group justify="space-between">
                  <Text size="sm" c="white">Model Training</Text>
                  <Text size="sm" c="yellow">87%</Text>
                </Group>
                <Progress value={87} color="yellow" size="sm" />
                
                <Group justify="space-between">
                  <Text size="sm" c="white">Production Deploy</Text>
                  <Text size="sm" c="orange">73%</Text>
                </Group>
                <Progress value={73} color="orange" size="sm" />
              </Stack>
            </Card>

            <Card className="neo-card" padding="lg">
              <Title order={4} c="white" mb="md">Average Stage Duration</Title>
              <Text c="dimmed" size="sm" mb="md">
                Typical time spent in each lifecycle stage
              </Text>
              <Stack>
                <Group justify="space-between">
                  <Text size="sm" c="white">Data Collection</Text>
                  <Text size="sm" c="white">5.2 days</Text>
                </Group>
                
                <Group justify="space-between">
                  <Text size="sm" c="white">Preprocessing</Text>
                  <Text size="sm" c="white">8.7 days</Text>
                </Group>
                
                <Group justify="space-between">
                  <Text size="sm" c="white">Feature Engineering</Text>
                  <Text size="sm" c="white">12.3 days</Text>
                </Group>
                
                <Group justify="space-between">
                  <Text size="sm" c="white">Model Training</Text>
                  <Text size="sm" c="white">15.8 days</Text>
                </Group>
                
                <Group justify="space-between">
                  <Text size="sm" c="white">Testing & Validation</Text>
                  <Text size="sm" c="white">9.4 days</Text>
                </Group>
                
                <Group justify="space-between">
                  <Text size="sm" c="white">Deployment</Text>
                  <Text size="sm" c="white">6.1 days</Text>
                </Group>
              </Stack>
            </Card>
          </SimpleGrid>
        </Tabs.Panel>
      </Tabs>

      {/* Project Details Modal */}
      <Modal
        opened={modalOpened}
        onClose={() => {
          setModalOpened(false);
          setSelectedProject(null);
        }}
        title={selectedProject ? "Project Details" : "Create New Project"}
        size="lg"
      >
        <Stack>
          <TextInput
            label="Project Name"
            placeholder="Enter project name"
            defaultValue={selectedProject?.name}
          />
          <Textarea
            label="Description"
            placeholder="Enter project description"
            rows={3}
            defaultValue={selectedProject?.description}
          />
          <Group grow>
            <Select
              label="Status"
              placeholder="Select status"
              data={['planning', 'development', 'testing', 'staging', 'production']}
              defaultValue={selectedProject?.status}
            />
            <Select
              label="Risk Level"
              placeholder="Select risk level"
              data={['low', 'medium', 'high', 'critical']}
              defaultValue={selectedProject?.riskLevel}
            />
          </Group>
          <Group grow>
            <TextInput
              label="Owner"
              placeholder="Enter project owner"
              defaultValue={selectedProject?.owner}
            />
            <Select
              label="Workflow Template"
              placeholder="Select template"
              data={['Standard ML Pipeline', 'Computer Vision Pipeline', 'NLP Pipeline', 'Custom']}
            />
          </Group>
          <Group justify="flex-end">
            <Button variant="outline" onClick={() => setModalOpened(false)}>
              Cancel
            </Button>
            <Button>Save Project</Button>
          </Group>
        </Stack>
      </Modal>
    </Container>
  );
}