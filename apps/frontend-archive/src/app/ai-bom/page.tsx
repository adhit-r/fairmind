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
  Textarea,
  Progress,
  Alert,
  Tabs,
  Timeline,
} from '@mantine/core';
import {
  IconPackage,
  IconGitBranch,
  IconShield,
  IconAlertTriangle,
  IconDownload,
  IconUpload,
  IconRefresh,
  IconEye,
  IconEdit,
  IconTrash,
  IconPlus,
  IconCheck,
  IconX,
  IconClock,
  IconTrendingUp,
  IconDatabase,
  IconCode,
} from '@tabler/icons-react';
import { useApi } from '@/hooks/useApi';

interface BOMComponent {
  id: string;
  name: string;
  version: string;
  type: 'model' | 'dataset' | 'library' | 'framework' | 'tool';
  vendor: string;
  license: string;
  status: 'active' | 'deprecated' | 'vulnerable' | 'updated';
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  lastUpdated: string;
  dependencies: string[];
  vulnerabilities: number;
  compliance: string;
  description: string;
}

interface BOMStats {
  totalComponents: number;
  vulnerableComponents: number;
  outdatedComponents: number;
  complianceScore: number;
  licenseIssues: number;
  lastScan: string;
}

export default function AIBOMPage() {
  const [components, setComponents] = useState<BOMComponent[]>([]);
  const [stats, setStats] = useState<BOMStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedComponent, setSelectedComponent] = useState<BOMComponent | null>(null);
  const [modalOpened, setModalOpened] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const { data, loading: apiLoading, error } = useApi('/api/ai-bom');
  
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
    fetchBOMData();
  }, []);

  const fetchBOMData = async () => {
    try {
      setLoading(true);
      const [componentsData, statsData] = await Promise.all([
        fetchData('/api/ai-bom/components'),
        fetchData('/api/ai-bom/stats')
      ]);
      setComponents(componentsData || mockComponents);
      setStats(statsData || mockStats);
    } catch (error) {
      console.error('Error fetching BOM data:', error);
      setComponents(mockComponents);
      setStats(mockStats);
    } finally {
      setLoading(false);
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'green';
      case 'deprecated': return 'orange';
      case 'vulnerable': return 'red';
      case 'updated': return 'blue';
      default: return 'gray';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'model': return <IconGitBranch size={16} />;
      case 'dataset': return <IconDatabase size={16} />;
      case 'library': return <IconCode size={16} />;
      case 'framework': return <IconPackage size={16} />;
      case 'tool': return <IconShield size={16} />;
      default: return <IconPackage size={16} />;
    }
  };

  const mockStats: BOMStats = {
    totalComponents: 247,
    vulnerableComponents: 12,
    outdatedComponents: 34,
    complianceScore: 87,
    licenseIssues: 3,
    lastScan: '2024-01-20T10:30:00Z'
  };

  const mockComponents: BOMComponent[] = [
    {
      id: '1',
      name: 'TensorFlow',
      version: '2.13.0',
      type: 'framework',
      vendor: 'Google',
      license: 'Apache 2.0',
      status: 'active',
      riskLevel: 'low',
      lastUpdated: '2024-01-15T09:00:00Z',
      dependencies: ['NumPy', 'Protobuf', 'gRPC'],
      vulnerabilities: 0,
      compliance: 'SOX, GDPR',
      description: 'Machine learning framework for model training and inference'
    },
    {
      id: '2',
      name: 'scikit-learn',
      version: '1.3.0',
      type: 'library',
      vendor: 'scikit-learn',
      license: 'BSD-3-Clause',
      status: 'vulnerable',
      riskLevel: 'medium',
      lastUpdated: '2024-01-10T14:30:00Z',
      dependencies: ['NumPy', 'SciPy', 'joblib'],
      vulnerabilities: 2,
      compliance: 'GDPR',
      description: 'Machine learning library with classification and regression algorithms'
    },
    {
      id: '3',
      name: 'BERT Base Model',
      version: '1.0.0',
      type: 'model',
      vendor: 'Hugging Face',
      license: 'Apache 2.0',
      status: 'active',
      riskLevel: 'low',
      lastUpdated: '2024-01-18T11:15:00Z',
      dependencies: ['transformers', 'torch'],
      vulnerabilities: 0,
      compliance: 'EU AI Act, GDPR',
      description: 'Pre-trained BERT model for natural language processing tasks'
    }
  ];

  if (loading) {
    return (
      <Container size="xl" py="xl">
        <Text>Loading AI Bill of Materials...</Text>
      </Container>
    );
  }

  return (
    <Container size="xl" py="xl">
      <Group justify="space-between" mb="xl">
        <div>
          <Title order={1} c="white" mb="xs">
            AI Bill of Materials
          </Title>
          <Text size="lg" c="dimmed">
            Track and manage AI system components, dependencies, and vulnerabilities
          </Text>
        </div>
        <Group>
          <Button
            leftSection={<IconRefresh size={16} />}
            variant="outline"
            onClick={fetchBOMData}
          >
            Scan Components
          </Button>
          <Button
            leftSection={<IconDownload size={16} />}
            variant="light"
          >
            Export BOM
          </Button>
          <Button
            leftSection={<IconPlus size={16} />}
            onClick={() => setModalOpened(true)}
          >
            Add Component
          </Button>
        </Group>
      </Group>

      {/* Statistics Cards */}
      <SimpleGrid cols={{ base: 1, md: 2, lg: 6 }} mb="xl">
        <Card className="neo-card" padding="lg">
          <Group justify="apart">
            <div>
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                Total Components
              </Text>
              <Text fw={700} size="xl" c="white">
                {stats?.totalComponents}
              </Text>
            </div>
            <IconPackage size={24} color="var(--mantine-color-blue-6)" />
          </Group>
        </Card>

        <Card className="neo-card" padding="lg">
          <Group justify="apart">
            <div>
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                Vulnerabilities
              </Text>
              <Text fw={700} size="xl" c="red">
                {stats?.vulnerableComponents}
              </Text>
            </div>
            <IconAlertTriangle size={24} color="var(--mantine-color-red-6)" />
          </Group>
        </Card>

        <Card className="neo-card" padding="lg">
          <Group justify="apart">
            <div>
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                Outdated
              </Text>
              <Text fw={700} size="xl" c="orange">
                {stats?.outdatedComponents}
              </Text>
            </div>
            <IconClock size={24} color="var(--mantine-color-orange-6)" />
          </Group>
        </Card>

        <Card className="neo-card" padding="lg">
          <Group justify="apart">
            <div>
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                Compliance Score
              </Text>
              <Text fw={700} size="xl" c="green">
                {stats?.complianceScore}%
              </Text>
            </div>
            <IconShield size={24} color="var(--mantine-color-green-6)" />
          </Group>
          <Progress value={stats?.complianceScore || 0} size="sm" mt="xs" />
        </Card>

        <Card className="neo-card" padding="lg">
          <Group justify="apart">
            <div>
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                License Issues
              </Text>
              <Text fw={700} size="xl" c="yellow">
                {stats?.licenseIssues}
              </Text>
            </div>
            <IconX size={24} color="var(--mantine-color-yellow-6)" />
          </Group>
        </Card>

        <Card className="neo-card" padding="lg">
          <Group justify="apart">
            <div>
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                Last Scan
              </Text>
              <Text fw={700} size="xs" c="white">
                {stats?.lastScan ? new Date(stats.lastScan).toLocaleDateString() : 'Never'}
              </Text>
            </div>
            <IconTrendingUp size={24} color="var(--mantine-color-blue-6)" />
          </Group>
        </Card>
      </SimpleGrid>

      <Tabs value={activeTab} onChange={(value) => setActiveTab(value || 'overview')}>
        <Tabs.List>
          <Tabs.Tab value="overview" leftSection={<IconPackage size={16} />}>
            Overview
          </Tabs.Tab>
          <Tabs.Tab value="vulnerabilities" leftSection={<IconAlertTriangle size={16} />}>
            Vulnerabilities
          </Tabs.Tab>
          <Tabs.Tab value="dependencies" leftSection={<IconGitBranch size={16} />}>
            Dependencies
          </Tabs.Tab>
          <Tabs.Tab value="compliance" leftSection={<IconShield size={16} />}>
            Compliance
          </Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="overview" pt="xl">
          <Card className="neo-card" padding="lg">
            <Group justify="space-between" mb="md">
              <Title order={3} c="white">Component Inventory</Title>
              <Group>
                <Select
                  placeholder="Filter by type"
                  data={['All', 'Model', 'Dataset', 'Library', 'Framework', 'Tool']}
                  w={150}
                />
                <Select
                  placeholder="Filter by status"
                  data={['All', 'Active', 'Deprecated', 'Vulnerable', 'Updated']}
                  w={150}
                />
              </Group>
            </Group>

            <Table striped highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Component</Table.Th>
                  <Table.Th>Type</Table.Th>
                  <Table.Th>Version</Table.Th>
                  <Table.Th>Vendor</Table.Th>
                  <Table.Th>Status</Table.Th>
                  <Table.Th>Risk Level</Table.Th>
                  <Table.Th>Vulnerabilities</Table.Th>
                  <Table.Th>Actions</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {components.map((component) => (
                  <Table.Tr key={component.id}>
                    <Table.Td>
                      <Group>
                        {getTypeIcon(component.type)}
                        <div>
                          <Text fw={500} c="white">{component.name}</Text>
                          <Text size="xs" c="dimmed">{component.description}</Text>
                        </div>
                      </Group>
                    </Table.Td>
                    <Table.Td>
                      <Badge variant="light" size="sm">
                        {component.type}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <Text c="white">{component.version}</Text>
                    </Table.Td>
                    <Table.Td>
                      <Text c="white">{component.vendor}</Text>
                    </Table.Td>
                    <Table.Td>
                      <Badge color={getStatusColor(component.status)} variant="light">
                        {component.status}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <Badge color={getRiskColor(component.riskLevel)} variant="light">
                        {component.riskLevel}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <Text c={component.vulnerabilities > 0 ? "red" : "green"}>
                        {component.vulnerabilities}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs">
                        <ActionIcon
                          variant="subtle"
                          onClick={() => {
                            setSelectedComponent(component);
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

        <Tabs.Panel value="vulnerabilities" pt="xl">
          <Card className="neo-card" padding="lg">
            <Title order={3} c="white" mb="md">Security Vulnerabilities</Title>
            
            {components.filter(c => c.vulnerabilities > 0).length === 0 ? (
              <Alert icon={<IconCheck size={16} />} color="green">
                No vulnerabilities detected in current component inventory.
              </Alert>
            ) : (
              <Stack>
                {components
                  .filter(c => c.vulnerabilities > 0)
                  .map((component) => (
                    <Alert key={component.id} icon={<IconAlertTriangle size={16} />} color="red">
                      <Group justify="space-between">
                        <div>
                          <Text fw={500}>{component.name} v{component.version}</Text>
                          <Text size="sm">{component.vulnerabilities} vulnerabilities found</Text>
                        </div>
                        <Button size="xs" variant="light">
                          View Details
                        </Button>
                      </Group>
                    </Alert>
                  ))}
              </Stack>
            )}
          </Card>
        </Tabs.Panel>

        <Tabs.Panel value="dependencies" pt="xl">
          <Card className="neo-card" padding="lg">
            <Title order={3} c="white" mb="md">Dependency Graph</Title>
            <Text c="dimmed" mb="xl">
              Visualize component dependencies and identify potential risks in the supply chain.
            </Text>
            
            <Timeline active={-1} bulletSize={24} lineWidth={2}>
              {components.map((component, index) => (
                <Timeline.Item
                  key={component.id}
                  bullet={getTypeIcon(component.type)}
                  title={component.name}
                >
                  <Text c="dimmed" size="sm">
                    Dependencies: {component.dependencies.join(', ')}
                  </Text>
                  <Text size="xs" mt={4}>
                    License: {component.license}
                  </Text>
                </Timeline.Item>
              ))}
            </Timeline>
          </Card>
        </Tabs.Panel>

        <Tabs.Panel value="compliance" pt="xl">
          <Card className="neo-card" padding="lg">
            <Title order={3} c="white" mb="md">Compliance Overview</Title>
            
            <SimpleGrid cols={{ base: 1, md: 3 }} mb="xl">
              <Card className="neo-card" padding="md">
                <Text size="sm" c="dimmed" mb="xs">GDPR Compliance</Text>
                <Progress value={92} color="green" size="lg" />
                <Text size="xs" mt="xs" c="green">92% Compliant</Text>
              </Card>
              
              <Card className="neo-card" padding="md">
                <Text size="sm" c="dimmed" mb="xs">SOX Compliance</Text>
                <Progress value={78} color="yellow" size="lg" />
                <Text size="xs" mt="xs" c="yellow">78% Compliant</Text>
              </Card>
              
              <Card className="neo-card" padding="md">
                <Text size="sm" c="dimmed" mb="xs">EU AI Act</Text>
                <Progress value={85} color="blue" size="lg" />
                <Text size="xs" mt="xs" c="blue">85% Compliant</Text>
              </Card>
            </SimpleGrid>

            <Table striped highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Component</Table.Th>
                  <Table.Th>Compliance Frameworks</Table.Th>
                  <Table.Th>License</Table.Th>
                  <Table.Th>Risk Assessment</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {components.map((component) => (
                  <Table.Tr key={component.id}>
                    <Table.Td>
                      <Text c="white">{component.name}</Text>
                    </Table.Td>
                    <Table.Td>
                      <Text c="white">{component.compliance}</Text>
                    </Table.Td>
                    <Table.Td>
                      <Badge variant="light">{component.license}</Badge>
                    </Table.Td>
                    <Table.Td>
                      <Badge color={getRiskColor(component.riskLevel)} variant="light">
                        {component.riskLevel}
                      </Badge>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Card>
        </Tabs.Panel>
      </Tabs>

      {/* Component Details Modal */}
      <Modal
        opened={modalOpened}
        onClose={() => {
          setModalOpened(false);
          setSelectedComponent(null);
        }}
        title={selectedComponent ? "Component Details" : "Add New Component"}
        size="lg"
      >
        <Stack>
          <TextInput
            label="Component Name"
            placeholder="Enter component name"
            defaultValue={selectedComponent?.name}
          />
          <Group grow>
            <Select
              label="Type"
              placeholder="Select type"
              data={['model', 'dataset', 'library', 'framework', 'tool']}
              defaultValue={selectedComponent?.type}
            />
            <TextInput
              label="Version"
              placeholder="Enter version"
              defaultValue={selectedComponent?.version}
            />
          </Group>
          <Group grow>
            <TextInput
              label="Vendor"
              placeholder="Enter vendor"
              defaultValue={selectedComponent?.vendor}
            />
            <Select
              label="License"
              placeholder="Select license"
              data={['Apache 2.0', 'MIT', 'BSD-3-Clause', 'GPL-3.0', 'Proprietary']}
              defaultValue={selectedComponent?.license}
            />
          </Group>
          <Textarea
            label="Description"
            placeholder="Enter component description"
            defaultValue={selectedComponent?.description}
            rows={3}
          />
          <Group justify="flex-end">
            <Button variant="outline" onClick={() => setModalOpened(false)}>
              Cancel
            </Button>
            <Button>Save Component</Button>
          </Group>
        </Stack>
      </Modal>
    </Container>
  );
}