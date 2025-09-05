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
  IconShield,
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
  IconTarget,
  IconUsers,
  IconScale,
  IconWorld,
  IconFlag,
  IconCalendar,
  IconPlayerPlay,
  IconDownload,
  IconUpload,
  IconBug,
  IconShieldCheck,
  IconShieldX,
  IconAlertCircle,
  IconInfoCircle,
} from '@tabler/icons-react';
import { useState, useEffect } from 'react';

// Security scan results
const securityScanResults = [
  {
    id: 'scan-001',
    type: 'Container Vulnerability',
    target: 'nginx:latest',
    timestamp: '2024-01-15T10:30:00Z',
    status: 'completed',
    securityScore: 92,
    riskLevel: 'low',
    vulnerabilities: [
      { id: 'CVE-2023-1234', severity: 'medium', description: 'Buffer overflow in nginx', package: 'nginx', version: '1.21.0' },
      { id: 'CVE-2023-5678', severity: 'low', description: 'Information disclosure', package: 'openssl', version: '1.1.1' },
    ],
    recommendations: [
      'Update nginx to version 1.21.1 or later',
      'Update OpenSSL to latest version',
      'Review container base image for additional vulnerabilities'
    ]
  },
  {
    id: 'scan-002',
    type: 'LLM Security Test',
    target: 'gpt-4',
    timestamp: '2024-01-14T14:20:00Z',
    status: 'completed',
    securityScore: 88,
    riskLevel: 'medium',
    vulnerabilities: [
      { id: 'PROMPT-001', severity: 'high', description: 'Prompt injection vulnerability detected', package: 'prompt_injection', version: 'N/A' },
      { id: 'BIAS-001', severity: 'medium', description: 'Gender bias in responses', package: 'bias_detection', version: 'N/A' },
    ],
    recommendations: [
      'Implement input validation and sanitization',
      'Add bias detection and mitigation',
      'Use prompt engineering best practices'
    ]
  },
  {
    id: 'scan-003',
    type: 'Model Security Analysis',
    target: 'resnet50.pkl',
    timestamp: '2024-01-13T09:15:00Z',
    status: 'completed',
    securityScore: 95,
    riskLevel: 'low',
    vulnerabilities: [
      { id: 'ADV-001', severity: 'low', description: 'Minor adversarial robustness issue', package: 'adversarial', version: 'N/A' },
    ],
    recommendations: [
      'Implement adversarial training',
      'Add input preprocessing for robustness',
      'Regular model security audits'
    ]
  }
];

// Compliance frameworks
const complianceFrameworks = [
  {
    name: 'NIST AI RMF',
    version: '1.0',
    description: 'Framework for managing AI risks',
    compliance: 85,
    categories: ['governance', 'mapping', 'measuring', 'managing'],
    status: 'in_progress'
  },
  {
    name: 'EU AI Act',
    version: '2024',
    description: 'European Union AI regulation',
    compliance: 72,
    categories: ['prohibited_ai', 'high_risk_ai', 'limited_risk_ai', 'minimal_risk_ai'],
    status: 'in_progress'
  },
  {
    name: 'OECD AI Principles',
    version: '2019',
    description: 'Principles for responsible AI',
    compliance: 90,
    categories: ['inclusive_growth', 'human_centered_values', 'transparency', 'robustness', 'accountability'],
    status: 'compliant'
  }
];

// Security tools status
const securityTools = [
  {
    name: 'Grype',
    version: '0.74.0',
    description: 'Container vulnerability scanner',
    status: 'active',
    lastScan: '2024-01-15T10:30:00Z',
    scansCount: 45
  },
  {
    name: 'Garak',
    version: '0.1.0',
    description: 'LLM security testing framework',
    status: 'active',
    lastScan: '2024-01-14T14:20:00Z',
    scansCount: 23
  },
  {
    name: 'Nemo',
    version: '0.1.0',
    description: 'Model security analysis tool',
    status: 'active',
    lastScan: '2024-01-13T09:15:00Z',
    scansCount: 12
  }
];

export default function SecurityDashboard() {
  const { colorScheme } = useMantineColorScheme();
  const [selectedScan, setSelectedScan] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [isLoading, setIsLoading] = useState(true);
  const [isRunningScan, setIsRunningScan] = useState(false);
  const [scanModalOpen, setScanModalOpen] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 1500);
    return () => clearTimeout(timer);
  }, []);

  const handleRunScan = async () => {
    setIsRunningScan(true);
    // Simulate scan
    await new Promise(resolve => setTimeout(resolve, 3000));
    setIsRunningScan(false);
  };

  if (isLoading) {
    return (
      <Center style={{ height: '100vh' }}>
        <Stack align="center" gap="xl">
          <ThemeIcon size="xl" radius="md" color="blue" variant="light">
            <IconShield size="2rem" />
          </ThemeIcon>
          <Text size="xl" fw={600}>
            Loading Security Dashboard...
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

  const getComplianceColor = (compliance: number) => {
    if (compliance >= 90) return 'green';
    if (compliance >= 75) return 'yellow';
    return 'red';
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
                    ? 'linear-gradient(135deg, #3b82f6, #1d4ed8, #1e40af)'
                    : 'linear-gradient(135deg, #1e40af, #1d4ed8, #1e3a8a)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  fontSize: '2.5rem',
                  fontWeight: 800,
                }}
              >
                Security Center
              </Title>
              <Text c="dimmed" size="lg" fw={500}>
                AI Security Scanning & Compliance Monitoring
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
                Refresh Scans
              </Button>
              <Button
                variant="filled"
                leftSection={<IconPlayerPlay size="1rem" />}
                size="lg"
                loading={isRunningScan}
                onClick={() => setScanModalOpen(true)}
                style={{
                  borderRadius: '16px',
                  background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
                  border: 'none',
                }}
              >
                Run Security Scan
              </Button>
            </Group>
          </Group>

          {/* Security Overview */}
          <SimpleGrid cols={{ base: 2, sm: 4 }} mt="xl">
            {[
              { 
                label: 'Security Scans', 
                value: securityScanResults.length, 
                color: 'blue', 
                icon: IconShield 
              },
              { 
                label: 'Critical Issues', 
                value: securityScanResults.filter(s => s.riskLevel === 'critical').length, 
                color: 'red', 
                icon: IconAlertTriangle 
              },
              { 
                label: 'Avg Security Score', 
                value: `${(securityScanResults.reduce((acc, s) => acc + s.securityScore, 0) / securityScanResults.length).toFixed(0)}%`, 
                color: 'green', 
                icon: IconShieldCheck 
              },
              { 
                label: 'Compliance Frameworks', 
                value: complianceFrameworks.length, 
                color: 'violet', 
                icon: IconScale 
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
                        metric.color === 'green' ? '34, 197, 94' : '139, 92, 246'}, 0.1)`,
                      border: `1px solid rgba(${metric.color === 'blue' ? '59, 130, 246' : 
                        metric.color === 'red' ? '239, 68, 68' : 
                        metric.color === 'green' ? '34, 197, 94' : '139, 92, 246'}, 0.2)`,
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
                           metric.color === 'green' ? '#22c55e' : '#8b5cf6',
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
          {/* Security Scan Results */}
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
                background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                fontSize: '1.8rem',
                fontWeight: 700,
              }}>
                Recent Security Scans
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
                        <Text fw={600} c="blue">Target</Text>
                      </Table.Th>
                      <Table.Th style={{ 
                        background: 'rgba(59, 130, 246, 0.1)',
                        border: 'none',
                        padding: '16px',
                      }}>
                        <Text fw={600} c="blue">Security Score</Text>
                      </Table.Th>
                      <Table.Th style={{ 
                        background: 'rgba(59, 130, 246, 0.1)',
                        border: 'none',
                        padding: '16px',
                      }}>
                        <Text fw={600} c="blue">Risk Level</Text>
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
                        borderRadius: '0 12px 12px 0',
                        border: 'none',
                        padding: '16px',
                      }}>
                        <Text fw={600} c="blue">Actions</Text>
                      </Table.Th>
                    </Table.Tr>
                  </Table.Thead>
                  <Table.Tbody>
                    {securityScanResults.map((scan, index) => (
                      <Table.Tr 
                        key={index}
                        style={{
                          cursor: 'pointer',
                          background: selectedScan === scan.id 
                            ? 'rgba(59, 130, 246, 0.1)' 
                            : 'transparent',
                          borderRadius: '12px',
                          margin: '8px 0',
                          transform: 'perspective(1000px) rotateX(2deg)',
                          transition: 'all 0.3s ease',
                        }}
                        onClick={() => setSelectedScan(selectedScan === scan.id ? null : scan.id)}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.transform = 'perspective(1000px) rotateX(0deg) translateY(-2px)';
                          e.currentTarget.style.background = 'rgba(59, 130, 246, 0.05)';
                          e.currentTarget.style.boxShadow = '0 4px 16px rgba(0, 0, 0, 0.1)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.transform = 'perspective(1000px) rotateX(2deg)';
                          e.currentTarget.style.background = selectedScan === scan.id 
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
                              {scan.type === 'Container Vulnerability' ? <IconDatabase size="1.2rem" /> :
                               scan.type === 'LLM Security Test' ? <IconBrain size="1.2rem" /> :
                               <IconRobot size="1.2rem" />}
                            </ThemeIcon>
                            <div>
                              <Text fw={600} size="sm">{scan.target}</Text>
                              <Text size="xs" c="dimmed">{scan.type}</Text>
                            </div>
                          </Group>
                        </Table.Td>
                        <Table.Td style={{ padding: '16px' }}>
                          <Group>
                            <Text fw={600} c="green">{scan.securityScore}%</Text>
                            <Box
                              style={{
                                width: 12,
                                height: 12,
                                borderRadius: '50%',
                                background: scan.securityScore >= 90 ? '#22c55e' : 
                                           scan.securityScore >= 75 ? '#eab308' : 
                                           scan.securityScore >= 50 ? '#f59e0b' : '#ef4444',
                                transform: 'perspective(100px) rotateX(45deg)',
                                boxShadow: '0 2px 4px rgba(0, 0, 0, 0.2)',
                              }}
                            />
                          </Group>
                        </Table.Td>
                        <Table.Td style={{ padding: '16px' }}>
                          <Badge
                            color={getRiskColor(scan.riskLevel)}
                            variant="light"
                            size="lg"
                            style={{
                              borderRadius: '12px',
                              background: scan.riskLevel === 'critical' ? 'rgba(239, 68, 68, 0.1)' :
                                         scan.riskLevel === 'high' ? 'rgba(245, 158, 11, 0.1)' :
                                         scan.riskLevel === 'medium' ? 'rgba(234, 179, 8, 0.1)' :
                                         'rgba(34, 197, 94, 0.1)',
                              border: scan.riskLevel === 'critical' ? '1px solid rgba(239, 68, 68, 0.2)' :
                                      scan.riskLevel === 'high' ? '1px solid rgba(245, 158, 11, 0.2)' :
                                      scan.riskLevel === 'medium' ? '1px solid rgba(234, 179, 8, 0.2)' :
                                      '1px solid rgba(34, 197, 94, 0.2)',
                            }}
                          >
                            {scan.riskLevel}
                          </Badge>
                        </Table.Td>
                        <Table.Td style={{ padding: '16px' }}>
                          <Group gap="xs">
                            {scan.vulnerabilities.slice(0, 2).map((vuln, vulnIndex) => (
                              <Badge
                                key={vulnIndex}
                                color={getSeverityColor(vuln.severity)}
                                variant="light"
                                size="sm"
                                style={{ borderRadius: '8px' }}
                              >
                                {vuln.severity}
                              </Badge>
                            ))}
                            {scan.vulnerabilities.length > 2 && (
                              <Badge variant="outline" size="sm" style={{ borderRadius: '8px' }}>
                                +{scan.vulnerabilities.length - 2}
                              </Badge>
                            )}
                          </Group>
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
                          </Group>
                        </Table.Td>
                      </Table.Tr>
                    ))}
                  </Table.Tbody>
                </Table>
              </ScrollArea>
            </Card>
          </Grid.Col>

          {/* Security Details Panel */}
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
                {selectedScan ? 'Scan Details' : 'Select a Scan'}
              </Title>
              
              {selectedScan ? (
                (() => {
                  const scan = securityScanResults.find(s => s.id === selectedScan);
                  if (!scan) return null;
                  
                  return (
                    <Stack gap="md">
                      {/* Security Score */}
                      <div>
                        <Text fw={600} size="sm" mb="md">Security Score</Text>
                        <RingProgress
                          size={120}
                          thickness={12}
                          sections={[{ value: scan.securityScore, color: getComplianceColor(scan.securityScore) }]}
                          label={
                            <Text ta="center" size="lg" fw={700}>
                              {scan.securityScore}%
                            </Text>
                          }
                        />
                      </div>
                      
                      <Divider />
                      
                      {/* Vulnerabilities */}
                      <div>
                        <Text fw={600} size="sm" mb="md">Vulnerabilities</Text>
                        <Stack gap="sm">
                          {scan.vulnerabilities.map((vuln, index) => (
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
                                <Text fw={600} size="sm">{vuln.id}</Text>
                                <Badge
                                  color={getSeverityColor(vuln.severity)}
                                  variant="light"
                                  size="xs"
                                >
                                  {vuln.severity}
                                </Badge>
                              </Group>
                              <Text size="xs" c="dimmed" mb="xs">
                                {vuln.package} {vuln.version}
                              </Text>
                              <Text size="xs">{vuln.description}</Text>
                            </Card>
                          ))}
                        </Stack>
                      </div>
                      
                      <Divider />
                      
                      {/* Recommendations */}
                      <div>
                        <Text fw={600} size="sm" mb="md">Recommendations</Text>
                        <List size="sm" spacing="xs">
                          {scan.recommendations.map((rec, index) => (
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
                      <IconShield size="2rem" />
                    </ThemeIcon>
                    <Text c="dimmed" ta="center">
                      Click on a scan to view<br />detailed security information
                    </Text>
                  </Stack>
                </Center>
              )}
            </Card>
          </Grid.Col>
        </Grid>

        {/* Compliance Frameworks */}
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
            Compliance Frameworks
          </Title>
          
          <SimpleGrid cols={{ base: 1, md: 3 }} gap="xl">
            {complianceFrameworks.map((framework, index) => (
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
                  <Text fw={600} size="lg">{framework.name}</Text>
                  <Badge
                    color={getComplianceColor(framework.compliance)}
                    variant="light"
                    size="lg"
                    style={{ borderRadius: '12px' }}
                  >
                    {framework.compliance}%
                  </Badge>
                </Group>
                
                <Text size="sm" c="dimmed" mb="md">
                  {framework.description}
                </Text>
                
                <Progress
                  value={framework.compliance}
                  color={getComplianceColor(framework.compliance)}
                  size="lg"
                  radius="xl"
                  mb="md"
                />
                
                <Group gap="xs">
                  {framework.categories.slice(0, 2).map((category, catIndex) => (
                    <Badge
                      key={catIndex}
                      variant="outline"
                      size="xs"
                      style={{ borderRadius: '8px' }}
                    >
                      {category}
                    </Badge>
                  ))}
                  {framework.categories.length > 2 && (
                    <Badge variant="outline" size="xs" style={{ borderRadius: '8px' }}>
                      +{framework.categories.length - 2}
                    </Badge>
                  )}
                </Group>
              </Card>
            ))}
          </SimpleGrid>
        </Card>
      </Container>

      {/* Security Scan Modal */}
      <Modal
        opened={scanModalOpen}
        onClose={() => setScanModalOpen(false)}
        title="Run Security Scan"
        size="lg"
      >
        <Stack gap="md">
          <Select
            label="Scan Type"
            placeholder="Select scan type"
            data={[
              { value: 'container', label: 'Container Vulnerability Scan (Grype)' },
              { value: 'llm', label: 'LLM Security Test (Garak)' },
              { value: 'model', label: 'Model Security Analysis (Nemo)' }
            ]}
            required
          />
          <TextInput
            label="Target"
            placeholder="Enter target (image name, model name, or file path)"
            required
          />
          <Textarea
            label="Additional Options"
            placeholder="Enter additional scan options (JSON format)"
            rows={3}
          />
          <Group justify="flex-end" gap="md">
            <Button variant="light" onClick={() => setScanModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleRunScan} loading={isRunningScan}>
              Run Scan
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Box>
  );
}
