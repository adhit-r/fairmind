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
} from '@mantine/core';
import {
  IconShield,
  IconScan,
  IconBug,
  IconAlertTriangle,
  IconCheck,
  IconX,
  IconEye,
  IconEdit,
  IconTrash,
  IconPlus,
  IconRefresh,
  IconDownload,
  IconClock,
  IconChartLine,
  IconSettings,
  IconCode,
  IconTarget,
  IconServer,
  IconDatabase,
} from '@tabler/icons-react';
import { useApi } from '@/hooks/useApi';

interface SecurityScan {
  id: string;
  name: string;
  target: string;
  type: 'sast' | 'dast' | 'dependency' | 'infrastructure';
  status: 'running' | 'completed' | 'failed';
  progress: number;
  startTime: string;
  vulnerabilities: number;
  riskScore: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
}

interface SecurityStats {
  totalScans: number;
  activeScans: number;
  totalVulnerabilities: number;
  criticalVulnerabilities: number;
  resolvedVulnerabilities: number;
  averageRiskScore: number;
}

export default function SecurityScansPage() {
  const [scans, setScans] = useState<SecurityScan[]>([]);
  const [stats, setStats] = useState<SecurityStats | null>(null);
  const [selectedScan, setSelectedScan] = useState<SecurityScan | null>(null);
  const [loading, setLoading] = useState(true);
  const [modalOpened, setModalOpened] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  
  const { data, loading: apiLoading, error } = useApi('/api/security');
  
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
    fetchSecurityData();
  }, []);

  const fetchSecurityData = async () => {
    try {
      setLoading(true);
      const [scansData, statsData] = await Promise.all([
        fetchData('/api/security/scans'),
        fetchData('/api/security/stats')
      ]);
      setScans(scansData || mockScans);
      setStats(statsData || mockStats);
    } catch (error) {
      console.error('Error fetching security data:', error);
      setScans(mockScans);
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

  const getScanTypeIcon = (type: string) => {
    switch (type) {
      case 'sast': return <IconCode size={16} />;
      case 'dast': return <IconTarget size={16} />;
      case 'dependency': return <IconDatabase size={16} />;
      case 'infrastructure': return <IconServer size={16} />;
      default: return <IconScan size={16} />;
    }
  };

  const mockStats: SecurityStats = {
    totalScans: 156,
    activeScans: 8,
    totalVulnerabilities: 47,
    criticalVulnerabilities: 3,
    resolvedVulnerabilities: 142,
    averageRiskScore: 6.8
  };

  const mockScans: SecurityScan[] = [
    {
      id: '1',
      name: 'Weekly SAST Scan - Main Branch',
      target: 'main-application',
      type: 'sast',
      status: 'completed',
      progress: 100,
      startTime: '2024-01-20T08:00:00Z',
      vulnerabilities: 12,
      riskScore: 7.2,
      critical: 1,
      high: 3,
      medium: 5,
      low: 3
    },
    {
      id: '2',
      name: 'Dependency Vulnerability Scan',
      target: 'ml-models',
      type: 'dependency',
      status: 'running',
      progress: 68,
      startTime: '2024-01-20T15:30:00Z',
      vulnerabilities: 0,
      riskScore: 0,
      critical: 0,
      high: 0,
      medium: 0,
      low: 0
    }
  ];

  if (loading) {
    return (
      <Container size="xl" py="xl">
        <Text>Loading Security Vulnerability Scans...</Text>
      </Container>
    );
  }

  return (
    <Container size="xl" py="xl">
      <Group justify="space-between" mb="xl">
        <div>
          <Title order={1} c="white" mb="xs">
            Security Vulnerability Scans
          </Title>
          <Text size="lg" c="dimmed">
            Monitor, scan, and remediate security vulnerabilities across AI systems
          </Text>
        </div>
        <Group>
          <Button
            leftSection={<IconRefresh size={16} />}
            variant="outline"
            onClick={fetchSecurityData}
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
            leftSection={<IconScan size={16} />}
            onClick={() => setModalOpened(true)}
          >
            New Scan
          </Button>
        </Group>
      </Group>

      {/* Statistics Cards */}
      <SimpleGrid cols={{ base: 1, md: 2, lg: 6 }} mb="xl">
        <Card className="neo-card" padding="lg">
          <Group justify="apart">
            <div>
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                Total Scans
              </Text>
              <Text fw={700} size="xl" c="white">
                {stats?.totalScans}
              </Text>
            </div>
            <IconScan size={24} color="var(--mantine-color-blue-6)" />
          </Group>
        </Card>

        <Card className="neo-card" padding="lg">
          <Group justify="apart">
            <div>
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                Active Scans
              </Text>
              <Text fw={700} size="xl" c="blue">
                {stats?.activeScans}
              </Text>
            </div>
            <IconClock size={24} color="var(--mantine-color-blue-6)" />
          </Group>
        </Card>

        <Card className="neo-card" padding="lg">
          <Group justify="apart">
            <div>
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                Vulnerabilities
              </Text>
              <Text fw={700} size="xl" c="orange">
                {stats?.totalVulnerabilities}
              </Text>
            </div>
            <IconBug size={24} color="var(--mantine-color-orange-6)" />
          </Group>
        </Card>

        <Card className="neo-card" padding="lg">
          <Group justify="apart">
            <div>
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                Critical Issues
              </Text>
              <Text fw={700} size="xl" c="red">
                {stats?.criticalVulnerabilities}
              </Text>
            </div>
            <IconAlertTriangle size={24} color="var(--mantine-color-red-6)" />
          </Group>
        </Card>

        <Card className="neo-card" padding="lg">
          <Group justify="apart">
            <div>
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                Resolved
              </Text>
              <Text fw={700} size="xl" c="green">
                {stats?.resolvedVulnerabilities}
              </Text>
            </div>
            <IconCheck size={24} color="var(--mantine-color-green-6)" />
          </Group>
        </Card>

        <Card className="neo-card" padding="lg">
          <Group justify="apart">
            <div>
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                Risk Score
              </Text>
              <Text fw={700} size="xl" c="white">
                {stats?.averageRiskScore}/10
              </Text>
            </div>
            <IconShield size={24} color="var(--mantine-color-yellow-6)" />
          </Group>
          <Progress value={(stats?.averageRiskScore || 0) * 10} size="sm" mt="xs" color="yellow" />
        </Card>
      </SimpleGrid>

      <Tabs value={activeTab} onChange={(value) => setActiveTab(value || 'overview')}>
        <Tabs.List>
          <Tabs.Tab value="overview" leftSection={<IconScan size={16} />}>
            Scan Overview
          </Tabs.Tab>
          <Tabs.Tab value="vulnerabilities" leftSection={<IconBug size={16} />}>
            Vulnerabilities
          </Tabs.Tab>
          <Tabs.Tab value="trends" leftSection={<IconChartLine size={16} />}>
            Security Trends
          </Tabs.Tab>
          <Tabs.Tab value="configuration" leftSection={<IconSettings size={16} />}>
            Configuration
          </Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="overview" pt="xl">
          <Card className="neo-card" padding="lg">
            <Group justify="space-between" mb="md">
              <Title order={3} c="white">Security Scans</Title>
              <Group>
                <Select
                  placeholder="Filter by type"
                  data={['All', 'SAST', 'DAST', 'Dependency', 'Infrastructure']}
                  w={150}
                />
                <Select
                  placeholder="Filter by status"
                  data={['All', 'Running', 'Completed', 'Failed']}
                  w={150}
                />
              </Group>
            </Group>

            <Table striped highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Scan Name</Table.Th>
                  <Table.Th>Type</Table.Th>
                  <Table.Th>Status</Table.Th>
                  <Table.Th>Progress</Table.Th>
                  <Table.Th>Vulnerabilities</Table.Th>
                  <Table.Th>Risk Score</Table.Th>
                  <Table.Th>Actions</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {scans.map((scan) => (
                  <Table.Tr key={scan.id}>
                    <Table.Td>
                      <div>
                        <Text fw={500} c="white">{scan.name}</Text>
                        <Text size="xs" c="dimmed">Target: {scan.target}</Text>
                      </div>
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs">
                        {getScanTypeIcon(scan.type)}
                        <Badge variant="light" size="sm">
                          {scan.type.toUpperCase()}
                        </Badge>
                      </Group>
                    </Table.Td>
                    <Table.Td>
                      <Badge color={getStatusColor(scan.status)} variant="light">
                        {scan.status}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <RingProgress
                        size={40}
                        thickness={4}
                        sections={[{ value: scan.progress, color: 'blue' }]}
                        label={
                          <Text size="xs" ta="center">
                            {scan.progress}%
                          </Text>
                        }
                      />
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs">
                        {scan.critical > 0 && (
                          <Badge size="xs" color="red" variant="light">
                            {scan.critical} Critical
                          </Badge>
                        )}
                        <Text size="sm" c="white">
                          {scan.vulnerabilities} total
                        </Text>
                      </Group>
                    </Table.Td>
                    <Table.Td>
                      <Text c={scan.riskScore > 7 ? 'red' : scan.riskScore > 4 ? 'orange' : 'green'} fw={500}>
                        {scan.riskScore}/10
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs">
                        <ActionIcon variant="subtle" onClick={() => { setSelectedScan(scan); setModalOpened(true); }}>
                          <IconEye size={16} />
                        </ActionIcon>
                        <ActionIcon variant="subtle">
                          <IconDownload size={16} />
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
          <Alert icon={<IconAlertTriangle size={16} />} color="red" mb="md">
            <Group justify="space-between">
              <div>
                <Text fw={500}>Critical SQL Injection Vulnerability</Text>
                <Text size="sm">Found in user authentication service - requires immediate attention</Text>
              </div>
              <Button size="xs" variant="light">View Details</Button>
            </Group>
          </Alert>
          
          <Alert icon={<IconBug size={16} />} color="orange" mb="md">
            <Group justify="space-between">
              <div>
                <Text fw={500}>Outdated TensorFlow Dependency</Text>
                <Text size="sm">Version 2.10.0 contains known security vulnerabilities</Text>
              </div>
              <Button size="xs" variant="light">Update</Button>
            </Group>
          </Alert>
        </Tabs.Panel>

        <Tabs.Panel value="trends" pt="xl">
          <SimpleGrid cols={{ base: 1, md: 2 }} spacing="md">
            <Card className="neo-card" padding="lg">
              <Title order={4} c="white" mb="md">Vulnerability Distribution</Title>
              <Stack>
                <Group justify="space-between">
                  <Text size="sm" c="white">Critical</Text>
                  <Group gap="xs">
                    <Progress value={15} w={100} size="sm" color="red" />
                    <Text size="sm" c="red">15%</Text>
                  </Group>
                </Group>
                <Group justify="space-between">
                  <Text size="sm" c="white">High</Text>
                  <Group gap="xs">
                    <Progress value={32} w={100} size="sm" color="orange" />
                    <Text size="sm" c="orange">32%</Text>
                  </Group>
                </Group>
                <Group justify="space-between">
                  <Text size="sm" c="white">Medium</Text>
                  <Group gap="xs">
                    <Progress value={43} w={100} size="sm" color="yellow" />
                    <Text size="sm" c="yellow">43%</Text>
                  </Group>
                </Group>
                <Group justify="space-between">
                  <Text size="sm" c="white">Low</Text>
                  <Group gap="xs">
                    <Progress value={10} w={100} size="sm" color="blue" />
                    <Text size="sm" c="blue">10%</Text>
                  </Group>
                </Group>
              </Stack>
            </Card>

            <Card className="neo-card" padding="lg">
              <Title order={4} c="white" mb="md">Scan Performance</Title>
              <Stack>
                <Group justify="space-between">
                  <Text size="sm" c="white">SAST Scans</Text>
                  <Text size="sm" c="white">45 completed</Text>
                </Group>
                <Group justify="space-between">
                  <Text size="sm" c="white">DAST Scans</Text>
                  <Text size="sm" c="white">28 completed</Text>
                </Group>
                <Group justify="space-between">
                  <Text size="sm" c="white">Dependency Scans</Text>
                  <Text size="sm" c="white">67 completed</Text>
                </Group>
                <Group justify="space-between">
                  <Text size="sm" c="white">Infrastructure Scans</Text>
                  <Text size="sm" c="white">16 completed</Text>
                </Group>
              </Stack>
            </Card>
          </SimpleGrid>
        </Tabs.Panel>

        <Tabs.Panel value="configuration" pt="xl">
          <Card className="neo-card" padding="lg">
            <Title order={3} c="white" mb="md">Scan Configuration</Title>
            <SimpleGrid cols={{ base: 1, md: 2 }} spacing="xl">
              <Stack>
                <Text fw={500} c="white">Automated Scanning</Text>
                <TextInput label="Daily Scan Time" defaultValue="02:00" />
                <Select
                  label="Scan Frequency"
                  data={['Daily', 'Weekly', 'Monthly']}
                  defaultValue="Weekly"
                />
                <Select
                  label="Default Scan Type"
                  data={['SAST', 'DAST', 'Dependency', 'Full Suite']}
                  defaultValue="Full Suite"
                />
              </Stack>
              <Stack>
                <Text fw={500} c="white">Notification Settings</Text>
                <Select
                  label="Alert Threshold"
                  data={['Critical Only', 'High and Above', 'Medium and Above', 'All']}
                  defaultValue="High and Above"
                />
                <TextInput
                  label="Notification Email"
                  defaultValue="security@company.com"
                />
                <Select
                  label="Report Format"
                  data={['JSON', 'PDF', 'CSV', 'SARIF']}
                  defaultValue="PDF"
                />
              </Stack>
            </SimpleGrid>
            <Group justify="flex-end" mt="xl">
              <Button variant="outline">Reset</Button>
              <Button>Save Configuration</Button>
            </Group>
          </Card>
        </Tabs.Panel>
      </Tabs>

      {/* Scan Modal */}
      <Modal
        opened={modalOpened}
        onClose={() => { setModalOpened(false); setSelectedScan(null); }}
        title={selectedScan ? "Scan Details" : "Create New Security Scan"}
        size="lg"
      >
        <Stack>
          <TextInput
            label="Scan Name"
            placeholder="Enter scan name"
            defaultValue={selectedScan?.name}
          />
          <Group grow>
            <Select
              label="Scan Type"
              data={['sast', 'dast', 'dependency', 'infrastructure']}
              defaultValue={selectedScan?.type}
            />
            <TextInput
              label="Target"
              placeholder="Enter target system/application"
              defaultValue={selectedScan?.target}
            />
          </Group>
          
          {selectedScan && (
            <Stack mt="md">
              <Group justify="space-between">
                <Text fw={500} c="white">Scan Results</Text>
                <Badge color={getStatusColor(selectedScan.status)}>
                  {selectedScan.status}
                </Badge>
              </Group>
              
              <SimpleGrid cols={4}>
                <Group justify="space-between">
                  <Text size="sm" c="white">Critical</Text>
                  <Text size="sm" c="red">{selectedScan.critical}</Text>
                </Group>
                <Group justify="space-between">
                  <Text size="sm" c="white">High</Text>
                  <Text size="sm" c="orange">{selectedScan.high}</Text>
                </Group>
                <Group justify="space-between">
                  <Text size="sm" c="white">Medium</Text>
                  <Text size="sm" c="yellow">{selectedScan.medium}</Text>
                </Group>
                <Group justify="space-between">
                  <Text size="sm" c="white">Low</Text>
                  <Text size="sm" c="blue">{selectedScan.low}</Text>
                </Group>
              </SimpleGrid>
            </Stack>
          )}
          
          <Group justify="flex-end">
            <Button variant="outline" onClick={() => setModalOpened(false)}>
              Cancel
            </Button>
            <Button>
              {selectedScan ? 'View Full Report' : 'Start Scan'}
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Container>
  );
}