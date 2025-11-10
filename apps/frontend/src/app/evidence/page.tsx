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
  FileInput,
  Alert,
  Tabs,
  Timeline,
  Anchor,
  Tooltip,
  Menu,
  Divider,
} from '@mantine/core';
import { CardSkeleton } from '@/components/LoadingSkeleton';
import {
  IconShield,
  IconFileText,
  IconCloudUpload,
  IconDownload,
  IconEye,
  IconEdit,
  IconTrash,
  IconPlus,
  IconSearch,
  IconFilter,
  IconCheck,
  IconX,
  IconClock,
  IconAlertTriangle,
  IconDatabase,
  IconGavel,
  IconCertificate,
  IconArchive,
  IconHistory,
  IconLock,
  IconShare,
  IconDots,
} from '@tabler/icons-react';
import { useApi } from '@/hooks/useApi';

interface Evidence {
  id: string;
  title: string;
  description: string;
  type: 'document' | 'audit_log' | 'test_result' | 'certification' | 'policy' | 'screenshot';
  framework: string;
  requirement: string;
  status: 'draft' | 'submitted' | 'approved' | 'rejected' | 'archived';
  confidence: number;
  tags: string[];
  createdBy: string;
  createdAt: string;
  lastModified: string;
  fileUrl?: string;
  fileSize?: number;
  relatedModel?: string;
  auditTrail: AuditEvent[];
}

interface AuditEvent {
  id: string;
  action: string;
  user: string;
  timestamp: string;
  details: string;
  oldValue?: string;
  newValue?: string;
}

interface EvidenceStats {
  totalEvidence: number;
  approvedEvidence: number;
  pendingReview: number;
  rejectedEvidence: number;
  complianceGaps: number;
  averageConfidence: number;
}

export default function EvidencePage() {
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [stats, setStats] = useState<EvidenceStats | null>(null);
  const [selectedEvidence, setSelectedEvidence] = useState<Evidence | null>(null);
  const [loading, setLoading] = useState(true);
  const [modalOpened, setModalOpened] = useState(false);
  const [auditModalOpened, setAuditModalOpened] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  
  const { data, loading: apiLoading, error } = useApi('/api/evidence');
  
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
    fetchEvidenceData();
  }, []);

  const fetchEvidenceData = async () => {
    try {
      setLoading(true);
      const [evidenceData, statsData] = await Promise.all([
        fetchData('/api/evidence/list'),
        fetchData('/api/evidence/stats')
      ]);
      setEvidence(evidenceData || mockEvidence);
      setStats(statsData || mockStats);
    } catch (error) {
      console.error('Error fetching evidence data:', error);
      setEvidence(mockEvidence);
      setStats(mockStats);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved': return 'green';
      case 'submitted': return 'blue';
      case 'draft': return 'gray';
      case 'rejected': return 'red';
      case 'archived': return 'orange';
      default: return 'gray';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'document': return <IconFileText size={16} />;
      case 'audit_log': return <IconHistory size={16} />;
      case 'test_result': return <IconCheck size={16} />;
      case 'certification': return <IconCertificate size={16} />;
      case 'policy': return <IconGavel size={16} />;
      case 'screenshot': return <IconEye size={16} />;
      default: return <IconFileText size={16} />;
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 90) return 'green';
    if (confidence >= 70) return 'yellow';
    if (confidence >= 50) return 'orange';
    return 'red';
  };

  const mockStats: EvidenceStats = {
    totalEvidence: 156,
    approvedEvidence: 124,
    pendingReview: 18,
    rejectedEvidence: 8,
    complianceGaps: 6,
    averageConfidence: 87.3
  };

  const mockEvidence: Evidence[] = [
    {
      id: '1',
      title: 'Model Training Documentation',
      description: 'Comprehensive documentation of the sentiment analysis model training process',
      type: 'document',
      framework: 'GDPR',
      requirement: 'Article 22 - Automated Decision Making',
      status: 'approved',
      confidence: 95,
      tags: ['training', 'documentation', 'gdpr'],
      createdBy: 'Sarah Chen',
      createdAt: '2024-01-15T09:00:00Z',
      lastModified: '2024-01-18T14:30:00Z',
      fileUrl: '/evidence/model-training-doc.pdf',
      fileSize: 2048000,
      relatedModel: 'sentiment-analysis-v1',
      auditTrail: [
        {
          id: 'a1',
          action: 'Created',
          user: 'Sarah Chen',
          timestamp: '2024-01-15T09:00:00Z',
          details: 'Initial evidence submission'
        },
        {
          id: 'a2',
          action: 'Approved',
          user: 'Compliance Team',
          timestamp: '2024-01-18T14:30:00Z',
          details: 'Evidence meets GDPR Article 22 requirements'
        }
      ]
    },
    {
      id: '2',
      title: 'Bias Testing Results',
      description: 'Fairness evaluation results for the fraud detection model',
      type: 'test_result',
      framework: 'EU AI Act',
      requirement: 'High-Risk AI Systems Testing',
      status: 'submitted',
      confidence: 78,
      tags: ['bias', 'testing', 'fairness', 'eu-ai-act'],
      createdBy: 'David Rodriguez',
      createdAt: '2024-01-20T11:30:00Z',
      lastModified: '2024-01-20T11:30:00Z',
      fileUrl: '/evidence/bias-test-results.json',
      fileSize: 512000,
      relatedModel: 'fraud-detection-v2',
      auditTrail: [
        {
          id: 'a3',
          action: 'Created',
          user: 'David Rodriguez',
          timestamp: '2024-01-20T11:30:00Z',
          details: 'Bias testing evidence submitted for review'
        }
      ]
    },
    {
      id: '3',
      title: 'Data Processing Agreement',
      description: 'Legal agreement for customer data processing',
      type: 'certification',
      framework: 'GDPR',
      requirement: 'Article 28 - Processor Obligations',
      status: 'draft',
      confidence: 85,
      tags: ['dpa', 'legal', 'data-processing'],
      createdBy: 'Legal Team',
      createdAt: '2024-01-19T16:00:00Z',
      lastModified: '2024-01-19T16:00:00Z',
      relatedModel: 'customer-analytics-v1',
      auditTrail: [
        {
          id: 'a4',
          action: 'Created',
          user: 'Legal Team',
          timestamp: '2024-01-19T16:00:00Z',
          details: 'Draft DPA created for review'
        }
      ]
    }
  ];

  const filteredEvidence = evidence.filter(item => {
    const matchesSearch = item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         item.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         item.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesType = filterType === 'all' || item.type === filterType;
    const matchesStatus = filterStatus === 'all' || item.status === filterStatus;
    return matchesSearch && matchesType && matchesStatus;
  });

  if (loading) {
    return (
      <Container size="xl" py="xl">
        <CardSkeleton count={3} />
      </Container>
    );
  }

  return (
    <Container size="xl" py="xl">
      <Group justify="space-between" mb="xl">
        <div>
          <Title order={1} c="white" mb="xs">
            Evidence Collection
          </Title>
          <Text size="lg" c="dimmed">
            Collect, manage, and track compliance evidence and audit trails
          </Text>
        </div>
        <Group>
          <Button
            leftSection={<IconCloudUpload size={16} />}
            variant="outline"
          >
            Bulk Upload
          </Button>
          <Button
            leftSection={<IconDownload size={16} />}
            variant="light"
          >
            Export Evidence
          </Button>
          <Button
            leftSection={<IconPlus size={16} />}
            onClick={() => setModalOpened(true)}
          >
            Add Evidence
          </Button>
        </Group>
      </Group>

      {/* Statistics Cards */}
      <SimpleGrid cols={{ base: 1, md: 2, lg: 6 }} mb="xl">
        <Card className="neo-card" padding="lg">
          <Group justify="apart">
            <div>
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                Total Evidence
              </Text>
              <Text fw={700} size="xl" c="white">
                {stats?.totalEvidence}
              </Text>
            </div>
            <IconFileText size={24} color="var(--mantine-color-blue-6)" />
          </Group>
        </Card>

        <Card className="neo-card" padding="lg">
          <Group justify="apart">
            <div>
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                Approved
              </Text>
              <Text fw={700} size="xl" c="green">
                {stats?.approvedEvidence}
              </Text>
            </div>
            <IconCheck size={24} color="var(--mantine-color-green-6)" />
          </Group>
        </Card>

        <Card className="neo-card" padding="lg">
          <Group justify="apart">
            <div>
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                Pending Review
              </Text>
              <Text fw={700} size="xl" c="blue">
                {stats?.pendingReview}
              </Text>
            </div>
            <IconClock size={24} color="var(--mantine-color-blue-6)" />
          </Group>
        </Card>

        <Card className="neo-card" padding="lg">
          <Group justify="apart">
            <div>
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                Rejected
              </Text>
              <Text fw={700} size="xl" c="red">
                {stats?.rejectedEvidence}
              </Text>
            </div>
            <IconX size={24} color="var(--mantine-color-red-6)" />
          </Group>
        </Card>

        <Card className="neo-card" padding="lg">
          <Group justify="apart">
            <div>
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                Compliance Gaps
              </Text>
              <Text fw={700} size="xl" c="orange">
                {stats?.complianceGaps}
              </Text>
            </div>
            <IconAlertTriangle size={24} color="var(--mantine-color-orange-6)" />
          </Group>
        </Card>

        <Card className="neo-card" padding="lg">
          <Group justify="apart">
            <div>
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                Avg Confidence
              </Text>
              <Text fw={700} size="xl" c="blue">
                {stats?.averageConfidence}%
              </Text>
            </div>
            <IconShield size={24} color="var(--mantine-color-blue-6)" />
          </Group>
        </Card>
      </SimpleGrid>

      <Tabs value={activeTab} onChange={(value) => setActiveTab(value || 'overview')}>
        <Tabs.List>
          <Tabs.Tab value="overview" leftSection={<IconFileText size={16} />}>
            Evidence Library
          </Tabs.Tab>
          <Tabs.Tab value="compliance" leftSection={<IconShield size={16} />}>
            Compliance Mapping
          </Tabs.Tab>
          <Tabs.Tab value="audit" leftSection={<IconHistory size={16} />}>
            Audit Trails
          </Tabs.Tab>
          <Tabs.Tab value="gaps" leftSection={<IconAlertTriangle size={16} />}>
            Compliance Gaps
          </Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="overview" pt="xl">
          <Card className="neo-card" padding="lg">
            <Group justify="space-between" mb="md">
              <Title order={3} c="white">Evidence Repository</Title>
              <Group>
                <TextInput
                  placeholder="Search evidence..."
                  leftSection={<IconSearch size={16} />}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  w={250}
                />
                <Select
                  placeholder="Type"
                  data={['all', 'document', 'audit_log', 'test_result', 'certification', 'policy', 'screenshot']}
                  value={filterType}
                  onChange={(value) => setFilterType(value || 'all')}
                  w={120}
                />
                <Select
                  placeholder="Status"
                  data={['all', 'draft', 'submitted', 'approved', 'rejected', 'archived']}
                  value={filterStatus}
                  onChange={(value) => setFilterStatus(value || 'all')}
                  w={120}
                />
              </Group>
            </Group>

            <Table striped highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Evidence</Table.Th>
                  <Table.Th>Type</Table.Th>
                  <Table.Th>Framework</Table.Th>
                  <Table.Th>Status</Table.Th>
                  <Table.Th>Confidence</Table.Th>
                  <Table.Th>Created By</Table.Th>
                  <Table.Th>Last Modified</Table.Th>
                  <Table.Th>Actions</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {filteredEvidence.map((item) => (
                  <Table.Tr key={item.id}>
                    <Table.Td>
                      <Group>
                        {getTypeIcon(item.type)}
                        <div>
                          <Text fw={500} c="white">{item.title}</Text>
                          <Text size="xs" c="dimmed">{item.description}</Text>
                          <Group gap="xs" mt="xs">
                            {item.tags.map((tag) => (
                              <Badge key={tag} size="xs" variant="light">
                                {tag}
                              </Badge>
                            ))}
                          </Group>
                        </div>
                      </Group>
                    </Table.Td>
                    <Table.Td>
                      <Badge variant="light" size="sm">
                        {item.type.replace('_', ' ')}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <Text c="white" size="sm">{item.framework}</Text>
                      <Text c="dimmed" size="xs">{item.requirement}</Text>
                    </Table.Td>
                    <Table.Td>
                      <Badge color={getStatusColor(item.status)} variant="light">
                        {item.status}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <Group>
                        <Text c={getConfidenceColor(item.confidence)} fw={500}>
                          {item.confidence}%
                        </Text>
                      </Group>
                    </Table.Td>
                    <Table.Td>
                      <Text c="white">{item.createdBy}</Text>
                    </Table.Td>
                    <Table.Td>
                      <Text c="white" size="sm">
                        {new Date(item.lastModified).toLocaleDateString()}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs">
                        <ActionIcon
                          variant="subtle"
                          onClick={() => {
                            setSelectedEvidence(item);
                            setModalOpened(true);
                          }}
                        >
                          <IconEye size={16} />
                        </ActionIcon>
                        <ActionIcon
                          variant="subtle"
                          onClick={() => {
                            setSelectedEvidence(item);
                            setAuditModalOpened(true);
                          }}
                        >
                          <IconHistory size={16} />
                        </ActionIcon>
                        <Menu>
                          <Menu.Target>
                            <ActionIcon variant="subtle">
                              <IconDots size={16} />
                            </ActionIcon>
                          </Menu.Target>
                          <Menu.Dropdown>
                            <Menu.Item leftSection={<IconDownload size={14} />}>
                              Download
                            </Menu.Item>
                            <Menu.Item leftSection={<IconShare size={14} />}>
                              Share
                            </Menu.Item>
                            <Menu.Item leftSection={<IconEdit size={14} />}>
                              Edit
                            </Menu.Item>
                            <Menu.Divider />
                            <Menu.Item leftSection={<IconTrash size={14} />} color="red">
                              Delete
                            </Menu.Item>
                          </Menu.Dropdown>
                        </Menu>
                      </Group>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Card>
        </Tabs.Panel>

        <Tabs.Panel value="compliance" pt="xl">
          <SimpleGrid cols={{ base: 1, md: 2 }} spacing="md">
            <Card className="neo-card" padding="lg">
              <Title order={4} c="white" mb="md">GDPR Compliance Evidence</Title>
              <Stack>
                {evidence.filter(e => e.framework === 'GDPR').map((item) => (
                  <Group key={item.id} justify="space-between">
                    <div>
                      <Text size="sm" c="white">{item.requirement}</Text>
                      <Text size="xs" c="dimmed">{item.title}</Text>
                    </div>
                    <Badge color={getStatusColor(item.status)} size="sm">
                      {item.status}
                    </Badge>
                  </Group>
                ))}
              </Stack>
            </Card>

            <Card className="neo-card" padding="lg">
              <Title order={4} c="white" mb="md">EU AI Act Evidence</Title>
              <Stack>
                {evidence.filter(e => e.framework === 'EU AI Act').map((item) => (
                  <Group key={item.id} justify="space-between">
                    <div>
                      <Text size="sm" c="white">{item.requirement}</Text>
                      <Text size="xs" c="dimmed">{item.title}</Text>
                    </div>
                    <Badge color={getStatusColor(item.status)} size="sm">
                      {item.status}
                    </Badge>
                  </Group>
                ))}
              </Stack>
            </Card>
          </SimpleGrid>
        </Tabs.Panel>

        <Tabs.Panel value="audit" pt="xl">
          <Card className="neo-card" padding="lg">
            <Title order={3} c="white" mb="md">Recent Audit Activities</Title>
            
            <Timeline active={-1} bulletSize={24} lineWidth={2}>
              {evidence.flatMap(item => 
                item.auditTrail.map(event => ({
                  ...event,
                  evidenceTitle: item.title
                }))
              )
              .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
              .slice(0, 10)
              .map((event) => (
                <Timeline.Item
                  key={event.id}
                  bullet={
                    event.action === 'Approved' ? <IconCheck size={16} /> :
                    event.action === 'Rejected' ? <IconX size={16} /> :
                    event.action === 'Created' ? <IconPlus size={16} /> :
                    <IconEdit size={16} />
                  }
                  title={`${event.action}: ${event.evidenceTitle}`}
                >
                  <Text c="dimmed" size="sm" mb="xs">
                    {event.details}
                  </Text>
                  <Group gap="lg">
                    <Text size="xs" c="dimmed">
                      By: {event.user}
                    </Text>
                    <Text size="xs" c="dimmed">
                      {new Date(event.timestamp).toLocaleString()}
                    </Text>
                  </Group>
                </Timeline.Item>
              ))}
            </Timeline>
          </Card>
        </Tabs.Panel>

        <Tabs.Panel value="gaps" pt="xl">
          <Card className="neo-card" padding="lg">
            <Title order={3} c="white" mb="md">Compliance Gaps Analysis</Title>
            
            <Stack>
              <Alert icon={<IconAlertTriangle size={16} />} color="orange">
                <Group justify="space-between">
                  <div>
                    <Text fw={500}>GDPR Article 35 - DPIA</Text>
                    <Text size="sm">Data Protection Impact Assessment missing for high-risk processing</Text>
                  </div>
                  <Button size="xs" variant="light">
                    Create Evidence
                  </Button>
                </Group>
              </Alert>

              <Alert icon={<IconAlertTriangle size={16} />} color="red">
                <Group justify="space-between">
                  <div>
                    <Text fw={500}>EU AI Act - Risk Assessment</Text>
                    <Text size="sm">Risk assessment documentation required for high-risk AI system</Text>
                  </div>
                  <Button size="xs" variant="light">
                    Create Evidence
                  </Button>
                </Group>
              </Alert>

              <Alert icon={<IconAlertTriangle size={16} />} color="yellow">
                <Group justify="space-between">
                  <div>
                    <Text fw={500}>SOX Section 404 - Internal Controls</Text>
                    <Text size="sm">Updated internal control documentation needed for Q1</Text>
                  </div>
                  <Button size="xs" variant="light">
                    Create Evidence
                  </Button>
                </Group>
              </Alert>
            </Stack>
          </Card>
        </Tabs.Panel>
      </Tabs>

      {/* Evidence Details Modal */}
      <Modal
        opened={modalOpened}
        onClose={() => {
          setModalOpened(false);
          setSelectedEvidence(null);
        }}
        title={selectedEvidence ? "Evidence Details" : "Add New Evidence"}
        size="lg"
      >
        <Stack>
          <TextInput
            label="Title"
            placeholder="Enter evidence title"
            defaultValue={selectedEvidence?.title}
          />
          <Textarea
            label="Description"
            placeholder="Enter evidence description"
            rows={3}
            defaultValue={selectedEvidence?.description}
          />
          <Group grow>
            <Select
              label="Type"
              placeholder="Select type"
              data={['document', 'audit_log', 'test_result', 'certification', 'policy', 'screenshot']}
              defaultValue={selectedEvidence?.type}
            />
            <Select
              label="Framework"
              placeholder="Select framework"
              data={['GDPR', 'EU AI Act', 'SOX', 'PCI DSS', 'ISO 27001', 'NIST']}
              defaultValue={selectedEvidence?.framework}
            />
          </Group>
          <TextInput
            label="Requirement"
            placeholder="Enter specific requirement"
            defaultValue={selectedEvidence?.requirement}
          />
          <FileInput
            label="Upload File"
            placeholder="Choose file"
            accept=".pdf,.doc,.docx,.json,.csv,.png,.jpg"
          />
          <TextInput
            label="Tags"
            placeholder="Enter tags (comma separated)"
            defaultValue={selectedEvidence?.tags.join(', ')}
          />
          <Group justify="flex-end">
            <Button variant="outline" onClick={() => setModalOpened(false)}>
              Cancel
            </Button>
            <Button>Save Evidence</Button>
          </Group>
        </Stack>
      </Modal>

      {/* Audit Trail Modal */}
      <Modal
        opened={auditModalOpened}
        onClose={() => {
          setAuditModalOpened(false);
          setSelectedEvidence(null);
        }}
        title="Audit Trail"
        size="md"
      >
        {selectedEvidence && (
          <Stack>
            <Group justify="space-between">
              <Text fw={500} c="white">{selectedEvidence.title}</Text>
              <Badge color={getStatusColor(selectedEvidence.status)}>
                {selectedEvidence.status}
              </Badge>
            </Group>
            
            <Divider />
            
            <Timeline active={-1} bulletSize={20} lineWidth={2}>
              {selectedEvidence.auditTrail.map((event) => (
                <Timeline.Item
                  key={event.id}
                  bullet={
                    event.action === 'Approved' ? <IconCheck size={12} /> :
                    event.action === 'Rejected' ? <IconX size={12} /> :
                    event.action === 'Created' ? <IconPlus size={12} /> :
                    <IconEdit size={12} />
                  }
                  title={event.action}
                >
                  <Text c="dimmed" size="sm" mb="xs">
                    {event.details}
                  </Text>
                  <Group gap="lg">
                    <Text size="xs" c="dimmed">
                      By: {event.user}
                    </Text>
                    <Text size="xs" c="dimmed">
                      {new Date(event.timestamp).toLocaleString()}
                    </Text>
                  </Group>
                </Timeline.Item>
              ))}
            </Timeline>
          </Stack>
        )}
      </Modal>
    </Container>
  );
}