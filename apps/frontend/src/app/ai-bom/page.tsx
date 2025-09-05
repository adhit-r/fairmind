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
  Modal,
  FileInput,
} from '@mantine/core';
import {
  IconPackage,
  IconAlertTriangle,
  IconCheck,
  IconX,
  IconTrendingUp,
  IconTrendingDown,
  IconBrain,
  IconRobot,
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
  IconTarget,
  IconShield,
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
  IconTable,
  IconFileSpreadsheet,
  IconFileCsv,
  IconFile,
  IconSearch,
  IconFilter,
  IconVersions,
  IconGitCommit,
  IconGitPullRequest,
  IconGitMerge,
} from '@tabler/icons-react';
import { useState, useEffect } from 'react';

// AI/ML BOM data
const aiBomData = [
  {
    id: 'bom-001',
    name: 'GPT-4 Vision Model',
    version: '1.2.0',
    type: 'LLM',
    status: 'active',
    components: [
      {
        name: 'Transformers Library',
        version: '4.35.0',
        type: 'Framework',
        license: 'Apache 2.0',
        vulnerability: 'none',
        size: '45.2 MB'
      },
      {
        name: 'PyTorch',
        version: '2.1.0',
        type: 'Framework',
        license: 'BSD-3-Clause',
        vulnerability: 'low',
        size: '1.2 GB'
      },
      {
        name: 'Hugging Face Tokenizers',
        version: '0.15.0',
        type: 'Library',
        license: 'Apache 2.0',
        vulnerability: 'none',
        size: '12.8 MB'
      },
      {
        name: 'NumPy',
        version: '1.24.3',
        type: 'Library',
        license: 'BSD-3-Clause',
        vulnerability: 'medium',
        size: '8.5 MB'
      },
      {
        name: 'CUDA Toolkit',
        version: '12.1',
        type: 'Runtime',
        license: 'Proprietary',
        vulnerability: 'none',
        size: '3.2 GB'
      }
    ],
    datasets: [
      {
        name: 'LAION-5B',
        version: '1.0',
        size: '240 TB',
        license: 'Creative Commons',
        biasScore: 0.15
      },
      {
        name: 'Common Crawl',
        version: '2023-06',
        size: '320 TB',
        license: 'Creative Commons',
        biasScore: 0.22
      }
    ],
    totalSize: '4.5 GB',
    totalComponents: 5,
    vulnerabilities: {
      critical: 0,
      high: 0,
      medium: 1,
      low: 1,
      none: 3
    },
    lastUpdated: '2024-01-15T10:30:00Z',
    createdBy: 'AI Research Team'
  },
  {
    id: 'bom-002',
    name: 'ResNet-152 Model',
    version: '2.1.0',
    type: 'Deep Learning',
    status: 'active',
    components: [
      {
        name: 'TensorFlow',
        version: '2.13.0',
        type: 'Framework',
        license: 'Apache 2.0',
        vulnerability: 'none',
        size: '890 MB'
      },
      {
        name: 'Keras',
        version: '2.13.1',
        type: 'Library',
        license: 'Apache 2.0',
        vulnerability: 'none',
        size: '15.2 MB'
      },
      {
        name: 'OpenCV',
        version: '4.8.0',
        type: 'Library',
        license: 'Apache 2.0',
        vulnerability: 'low',
        size: '45.6 MB'
      },
      {
        name: 'Pillow',
        version: '10.0.0',
        type: 'Library',
        license: 'HPND',
        vulnerability: 'none',
        size: '2.1 MB'
      }
    ],
    datasets: [
      {
        name: 'ImageNet',
        version: '2012',
        size: '150 GB',
        license: 'Custom',
        biasScore: 0.08
      }
    ],
    totalSize: '950 MB',
    totalComponents: 4,
    vulnerabilities: {
      critical: 0,
      high: 0,
      medium: 0,
      low: 1,
      none: 3
    },
    lastUpdated: '2024-01-14T14:20:00Z',
    createdBy: 'Computer Vision Team'
  },
  {
    id: 'bom-003',
    name: 'DALL-E 3 Model',
    version: '1.0.0',
    type: 'GenAI',
    status: 'testing',
    components: [
      {
        name: 'Diffusers',
        version: '0.24.0',
        type: 'Library',
        license: 'Apache 2.0',
        vulnerability: 'none',
        size: '25.4 MB'
      },
      {
        name: 'PyTorch',
        version: '2.1.0',
        type: 'Framework',
        license: 'BSD-3-Clause',
        vulnerability: 'low',
        size: '1.2 GB'
      },
      {
        name: 'Accelerate',
        version: '0.24.0',
        type: 'Library',
        license: 'Apache 2.0',
        vulnerability: 'none',
        size: '8.9 MB'
      },
      {
        name: 'Safetensors',
        version: '0.4.0',
        type: 'Library',
        license: 'Apache 2.0',
        vulnerability: 'none',
        size: '1.2 MB'
      }
    ],
    datasets: [
      {
        name: 'LAION-400M',
        version: '1.0',
        size: '240 GB',
        license: 'Creative Commons',
        biasScore: 0.28
      },
      {
        name: 'Conceptual Captions',
        version: '3.0',
        size: '12 GB',
        license: 'Creative Commons',
        biasScore: 0.19
      }
    ],
    totalSize: '1.3 GB',
    totalComponents: 4,
    vulnerabilities: {
      critical: 0,
      high: 0,
      medium: 0,
      low: 1,
      none: 3
    },
    lastUpdated: '2024-01-13T09:15:00Z',
    createdBy: 'Generative AI Team'
  }
];

// Vulnerability summary
const vulnerabilitySummary = {
  totalComponents: 13,
  critical: 0,
  high: 0,
  medium: 1,
  low: 3,
  none: 9,
  lastScan: '2024-01-15T10:30:00Z'
};

// License summary
const licenseSummary = [
  { license: 'Apache 2.0', count: 8, risk: 'low' },
  { license: 'BSD-3-Clause', count: 2, risk: 'low' },
  { license: 'Creative Commons', count: 2, risk: 'medium' },
  { license: 'Proprietary', count: 1, risk: 'high' },
];

export default function AiBomDashboard() {
  const { colorScheme } = useMantineColorScheme();
  const [selectedBom, setSelectedBom] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [isLoading, setIsLoading] = useState(true);
  const [scanModalOpen, setScanModalOpen] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 1500);
    return () => clearTimeout(timer);
  }, []);

  if (isLoading) {
    return (
      <Center style={{ height: '100vh' }}>
        <Stack align="center" gap="xl">
          <ThemeIcon size="xl" radius="md" color="blue" variant="light">
            <IconPackage size="2rem" />
          </ThemeIcon>
          <Text size="xl" fw={600}>
            Loading AI/ML BOM Dashboard...
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
      case 'deprecated': return 'red';
      case 'archived': return 'gray';
      default: return 'gray';
    }
  };

  const getVulnerabilityColor = (vulnerability: string) => {
    switch (vulnerability) {
      case 'critical': return 'red';
      case 'high': return 'orange';
      case 'medium': return 'yellow';
      case 'low': return 'blue';
      case 'none': return 'green';
      default: return 'gray';
    }
  };

  const getLicenseRiskColor = (risk: string) => {
    switch (risk) {
      case 'high': return 'red';
      case 'medium': return 'orange';
      case 'low': return 'green';
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
                AI/ML Bill of Materials
              </Title>
              <Text c="dimmed" size="lg" fw={500}>
                Component Tracking, Vulnerability Management & License Compliance
              </Text>
            </div>
            <Group>
              <Button
                variant="light"
                leftSection={<IconRefresh size="1rem" />}
                size="lg"
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
                leftSection={<IconShield size="1rem" />}
                size="lg"
                onClick={() => setScanModalOpen(true)}
                style={{
                  borderRadius: '16px',
                  background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                  border: 'none',
                }}
              >
                Scan Vulnerabilities
              </Button>
            </Group>
          </Group>

          {/* BOM Overview */}
          <SimpleGrid cols={{ base: 2, sm: 4 }} mt="xl">
            {[
              { 
                label: 'Total Models', 
                value: aiBomData.length, 
                color: 'blue', 
                icon: IconPackage 
              },
              { 
                label: 'Total Components', 
                value: vulnerabilitySummary.totalComponents, 
                color: 'green', 
                icon: IconCode 
              },
              { 
                label: 'Vulnerabilities', 
                value: vulnerabilitySummary.critical + vulnerabilitySummary.high + vulnerabilitySummary.medium, 
                color: 'orange', 
                icon: IconAlertTriangle 
              },
              { 
                label: 'License Risks', 
                value: licenseSummary.filter(l => l.risk === 'high' || l.risk === 'medium').length, 
                color: 'red', 
                icon: IconShield 
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
                        metric.color === 'orange' ? '245, 158, 11' : '239, 68, 68'}, 0.1)`,
                      border: `1px solid rgba(${metric.color === 'blue' ? '59, 130, 246' : 
                        metric.color === 'green' ? '34, 197, 94' : 
                        metric.color === 'orange' ? '245, 158, 11' : '239, 68, 68'}, 0.2)`,
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
                           metric.color === 'orange' ? '#f59e0b' : '#ef4444',
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
          {/* BOM Registry Table */}
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
                AI/ML BOM Registry
              </Title>
              
              <ScrollArea>
                <Table>
                  <Table.Thead>
                    <Table.Tr>
                      <Table.Th style={{ 
                        background: 'rgba(59, 130, 246, 0.1)',
                        borderRadius: '12px 12px 0 0',
                        border: 'none',
                        padding: '16px',
                      }}>
                        <Text fw={600} c="blue">Model</Text>
                      </Table.Th>
                      <Table.Th style={{ 
                        background: 'rgba(59, 130, 246, 0.1)',
                        border: 'none',
                        padding: '16px',
                      }}>
                        <Text fw={600} c="blue">Components</Text>
                      </Table.Th>
                      <Table.Th style={{ 
                        background: 'rgba(59, 130, 246, 0.1)',
                        border: 'none',
                        padding: '16px',
                      }}>
                        <Text fw={600} c="blue">Vulnerabilities</Text>
                      </Table.Th>
                      <Table.Th style={{ 
                        background: 'rgba(59, 130, 246, 0.1)',
                        border: 'none',
                        padding: '16px',
                      }}>
                        <Text fw={600} c="blue">Size</Text>
                      </Table.Th>
                      <Table.Th style={{ 
                        background: 'rgba(59, 130, 246, 0.1)',
                        border: 'none',
                        padding: '16px',
                      }}>
                        <Text fw={600} c="blue">Status</Text>
                      </Table.Th>
                      <Table.Th style={{ 
                        background: 'rgba(59, 130, 246, 0.1)',
                        borderRadius: '0 12px 12px 0',
                        border: 'none',
                        padding: '16px',
                      }}>
                        <Text fw={600} c="blue">Actions</Text>
                      </Table.Th>
                    </Table.Tr>
                  </Table.Thead>
                  <Table.Tbody>
                    {aiBomData.map((bom, index) => (
                      <Table.Tr 
                        key={index}
                        style={{
                          cursor: 'pointer',
                          background: selectedBom === bom.id 
                            ? 'rgba(59, 130, 246, 0.1)' 
                            : 'transparent',
                          borderRadius: '12px',
                          margin: '8px 0',
                          transform: 'perspective(1000px) rotateX(2deg)',
                          transition: 'all 0.3s ease',
                        }}
                        onClick={() => setSelectedBom(selectedBom === bom.id ? null : bom.id)}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.transform = 'perspective(1000px) rotateX(0deg) translateY(-2px)';
                          e.currentTarget.style.background = 'rgba(59, 130, 246, 0.05)';
                          e.currentTarget.style.boxShadow = '0 4px 16px rgba(0, 0, 0, 0.1)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.transform = 'perspective(1000px) rotateX(2deg)';
                          e.currentTarget.style.background = selectedBom === bom.id 
                            ? 'rgba(59, 130, 246, 0.1)' 
                            : 'transparent';
                          e.currentTarget.style.boxShadow = 'none';
                        }}
                      >
                        <Table.Td style={{ padding: '16px' }}>
                          <Group>
                            <ThemeIcon 
                              size="lg" 
                              radius="xl" 
                              color="blue" 
                              variant="light"
                              style={{
                                background: 'rgba(59, 130, 246, 0.1)',
                                border: '1px solid rgba(59, 130, 246, 0.2)',
                                transform: 'perspective(200px) rotateX(45deg)',
                              }}
                            >
                              <IconPackage size="1.2rem" />
                            </ThemeIcon>
                            <div>
                              <Text fw={600} size="sm">{bom.name}</Text>
                              <Text size="xs" c="dimmed">v{bom.version} • {bom.type}</Text>
                            </div>
                          </Group>
                        </Table.Td>
                        <Table.Td style={{ padding: '16px' }}>
                          <Stack gap="xs">
                            <Text size="xs" fw={500}>{bom.totalComponents} components</Text>
                            <Group gap="xs">
                              {bom.components.slice(0, 2).map((comp, compIndex) => (
                                <Badge
                                  key={compIndex}
                                  variant="outline"
                                  size="xs"
                                  style={{ borderRadius: '6px' }}
                                >
                                  {comp.name}
                                </Badge>
                              ))}
                              {bom.components.length > 2 && (
                                <Badge variant="outline" size="xs" style={{ borderRadius: '6px' }}>
                                  +{bom.components.length - 2}
                                </Badge>
                              )}
                            </Group>
                          </Stack>
                        </Table.Td>
                        <Table.Td style={{ padding: '16px' }}>
                          <Stack gap="xs">
                            <Group gap="xs">
                              {bom.vulnerabilities.critical > 0 && (
                                <Badge color="red" variant="light" size="xs">Critical: {bom.vulnerabilities.critical}</Badge>
                              )}
                              {bom.vulnerabilities.high > 0 && (
                                <Badge color="orange" variant="light" size="xs">High: {bom.vulnerabilities.high}</Badge>
                              )}
                              {bom.vulnerabilities.medium > 0 && (
                                <Badge color="yellow" variant="light" size="xs">Medium: {bom.vulnerabilities.medium}</Badge>
                              )}
                              {bom.vulnerabilities.low > 0 && (
                                <Badge color="blue" variant="light" size="xs">Low: {bom.vulnerabilities.low}</Badge>
                              )}
                            </Group>
                            {bom.vulnerabilities.critical + bom.vulnerabilities.high + bom.vulnerabilities.medium + bom.vulnerabilities.low === 0 && (
                              <Badge color="green" variant="light" size="xs">No vulnerabilities</Badge>
                            )}
                          </Stack>
                        </Table.Td>
                        <Table.Td style={{ padding: '16px' }}>
                          <Text size="xs" fw={500}>{bom.totalSize}</Text>
                        </Table.Td>
                        <Table.Td style={{ padding: '16px' }}>
                          <Badge
                            color={getStatusColor(bom.status)}
                            variant="light"
                            size="lg"
                            style={{
                              borderRadius: '12px',
                              background: bom.status === 'active' ? 'rgba(34, 197, 94, 0.1)' :
                                         bom.status === 'testing' ? 'rgba(245, 158, 11, 0.1)' :
                                         'rgba(239, 68, 68, 0.1)',
                              border: bom.status === 'active' ? '1px solid rgba(34, 197, 94, 0.2)' :
                                      bom.status === 'testing' ? '1px solid rgba(245, 158, 11, 0.2)' :
                                      '1px solid rgba(239, 68, 68, 0.2)',
                            }}
                          >
                            {bom.status}
                          </Badge>
                        </Table.Td>
                        <Table.Td style={{ padding: '16px' }}>
                          <Group gap="xs">
                            <ActionIcon 
                              variant="light" 
                              size="lg" 
                              color="blue"
                              style={{
                                borderRadius: '12px',
                                background: 'rgba(59, 130, 246, 0.1)',
                                border: '1px solid rgba(59, 130, 246, 0.2)',
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
                            <ActionIcon 
                              variant="light" 
                              size="lg" 
                              color="gray"
                              style={{
                                borderRadius: '12px',
                                background: 'rgba(107, 114, 128, 0.1)',
                                border: '1px solid rgba(107, 114, 128, 0.2)',
                                transform: 'perspective(200px) rotateX(45deg)',
                              }}
                            >
                              <IconDots size="1.2rem" />
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

          {/* BOM Details Panel */}
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
                {selectedBom ? 'BOM Details' : 'Select a BOM'}
              </Title>
              
              {selectedBom ? (
                (() => {
                  const bom = aiBomData.find(b => b.id === selectedBom);
                  if (!bom) return null;
                  
                  return (
                    <Stack gap="md">
                      {/* Components */}
                      <div>
                        <Text fw={600} size="sm" mb="md">Components ({bom.totalComponents})</Text>
                        <ScrollArea h={200}>
                          <Stack gap="sm">
                            {bom.components.map((component, index) => (
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
                                  <Text fw={600} size="sm">{component.name}</Text>
                                  <Badge
                                    color={getVulnerabilityColor(component.vulnerability)}
                                    variant="light"
                                    size="xs"
                                  >
                                    {component.vulnerability}
                                  </Badge>
                                </Group>
                                <Text size="xs" c="dimmed" mb="xs">
                                  v{component.version} • {component.type}
                                </Text>
                                <Group justify="space-between">
                                  <Text size="xs" c="dimmed">{component.license}</Text>
                                  <Text size="xs" fw={500}>{component.size}</Text>
                                </Group>
                              </Card>
                            ))}
                          </Stack>
                        </ScrollArea>
                      </div>
                      
                      <Divider />
                      
                      {/* Datasets */}
                      <div>
                        <Text fw={600} size="sm" mb="md">Training Datasets</Text>
                        <Stack gap="sm">
                          {bom.datasets.map((dataset, index) => (
                            <Card
                              key={index}
                              p="sm"
                              style={{
                                background: 'rgba(255, 255, 255, 0.05)',
                                border: '1px solid rgba(255, 255, 255, 0.1)',
                                borderRadius: '8px',
                              }}
                            >
                              <Text fw={600} size="sm" mb="xs">{dataset.name}</Text>
                              <Group justify="space-between" mb="xs">
                                <Text size="xs" c="dimmed">v{dataset.version}</Text>
                                <Text size="xs" fw={500}>{dataset.size}</Text>
                              </Group>
                              <Group justify="space-between">
                                <Text size="xs" c="dimmed">{dataset.license}</Text>
                                <Badge
                                  color={dataset.biasScore > 0.2 ? 'orange' : 'green'}
                                  variant="light"
                                  size="xs"
                                >
                                  Bias: {(dataset.biasScore * 100).toFixed(0)}%
                                </Badge>
                              </Group>
                            </Card>
                          ))}
                        </Stack>
                      </div>
                      
                      <Divider />
                      
                      {/* Actions */}
                      <div>
                        <Text fw={600} size="sm" mb="md">Actions</Text>
                        <Stack gap="sm">
                          <Button variant="light" size="sm" leftSection={<IconShield size="1rem" />}>
                            Security Scan
                          </Button>
                          <Button variant="light" size="sm" leftSection={<IconDownload size="1rem" />}>
                            Export BOM
                          </Button>
                          <Button variant="light" size="sm" leftSection={<IconVersions size="1rem" />}>
                            Version History
                          </Button>
                        </Stack>
                      </div>
                    </Stack>
                  );
                })()
              ) : (
                <Center style={{ height: '300px' }}>
                  <Stack align="center" gap="md">
                    <ThemeIcon size="xl" radius="xl" color="gray" variant="light">
                      <IconPackage size="2rem" />
                    </ThemeIcon>
                    <Text c="dimmed" ta="center">
                      Click on a BOM to view<br />detailed component information
                    </Text>
                  </Stack>
                </Center>
              )}
            </Card>
          </Grid.Col>
        </Grid>

        {/* Vulnerability & License Summary */}
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
            Security & License Overview
          </Title>
          
          <SimpleGrid cols={{ base: 1, md: 2 }} gap="xl">
            {/* Vulnerability Summary */}
            <Card
              p="lg"
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '16px',
              }}
            >
              <Text fw={600} size="lg" mb="md">Vulnerability Summary</Text>
              <Stack gap="sm">
                {[
                  { level: 'Critical', count: vulnerabilitySummary.critical, color: 'red' },
                  { level: 'High', count: vulnerabilitySummary.high, color: 'orange' },
                  { level: 'Medium', count: vulnerabilitySummary.medium, color: 'yellow' },
                  { level: 'Low', count: vulnerabilitySummary.low, color: 'blue' },
                  { level: 'None', count: vulnerabilitySummary.none, color: 'green' },
                ].map((vuln, index) => (
                  <Group key={index} justify="space-between">
                    <Text size="sm" c="dimmed">{vuln.level}</Text>
                    <Badge
                      color={vuln.color}
                      variant="light"
                      size="lg"
                      style={{ borderRadius: '12px' }}
                    >
                      {vuln.count}
                    </Badge>
                  </Group>
                ))}
              </Stack>
            </Card>

            {/* License Summary */}
            <Card
              p="lg"
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '16px',
              }}
            >
              <Text fw={600} size="lg" mb="md">License Distribution</Text>
              <Stack gap="sm">
                {licenseSummary.map((license, index) => (
                  <Group key={index} justify="space-between">
                    <div>
                      <Text size="sm" fw={500}>{license.license}</Text>
                      <Text size="xs" c="dimmed">{license.count} components</Text>
                    </div>
                    <Badge
                      color={getLicenseRiskColor(license.risk)}
                      variant="light"
                      size="lg"
                      style={{ borderRadius: '12px' }}
                    >
                      {license.risk}
                    </Badge>
                  </Group>
                ))}
              </Stack>
            </Card>
          </SimpleGrid>
        </Card>
      </Container>

      {/* Vulnerability Scan Modal */}
      <Modal
        opened={scanModalOpen}
        onClose={() => setScanModalOpen(false)}
        title="Vulnerability Scan"
        size="lg"
      >
        <Stack gap="md">
          <Alert
            icon={<IconShield size="1rem" />}
            title="Security Scan"
            color="blue"
            variant="light"
          >
            This will scan all components in your AI/ML models for known vulnerabilities and security issues.
          </Alert>
          
          <Select
            label="Scan Type"
            placeholder="Select scan type"
            data={['Full Scan', 'Quick Scan', 'Custom Scan']}
            required
          />
          
          <Select
            label="Target Models"
            placeholder="Select models to scan"
            data={['All Models', 'Active Models Only', 'Custom Selection']}
            required
          />
          
          <Group justify="flex-end" gap="md">
            <Button variant="light" onClick={() => setScanModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={() => setScanModalOpen(false)}>
              Start Scan
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Box>
  );
}
