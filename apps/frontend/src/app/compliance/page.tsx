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
} from '@mantine/core';
import {
  IconWorld,
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
  IconMapPin,
  IconFlag,
  IconScale,
  IconGavel,
  IconBuilding,
  IconUsers,
  IconCalendar,
} from '@tabler/icons-react';
import { useState, useEffect } from 'react';

// AI Laws and Regulations by Country
const aiLawsData = {
  'EU': {
    name: 'European Union',
    flag: '🇪🇺',
    status: 'active',
    laws: [
      { name: 'EU AI Act', status: 'enacted', effectiveDate: '2024-12-01', riskLevel: 'high' },
      { name: 'GDPR', status: 'enforced', effectiveDate: '2018-05-25', riskLevel: 'high' },
      { name: 'Digital Services Act', status: 'enacted', effectiveDate: '2024-02-17', riskLevel: 'medium' }
    ],
    complianceScore: 85,
    lastUpdated: '2024-01-15'
  },
  'US': {
    name: 'United States',
    flag: '🇺🇸',
    status: 'developing',
    laws: [
      { name: 'Executive Order 14110', status: 'enacted', effectiveDate: '2023-10-30', riskLevel: 'medium' },
      { name: 'NIST AI RMF', status: 'guidance', effectiveDate: '2023-01-26', riskLevel: 'low' },
      { name: 'State AI Laws (CA, NY, IL)', status: 'pending', effectiveDate: '2024-12-01', riskLevel: 'high' }
    ],
    complianceScore: 72,
    lastUpdated: '2024-01-10'
  },
  'CN': {
    name: 'China',
    flag: '🇨🇳',
    status: 'active',
    laws: [
      { name: 'Algorithmic Recommendation Provisions', status: 'enforced', effectiveDate: '2022-03-01', riskLevel: 'high' },
      { name: 'Deep Synthesis Provisions', status: 'enforced', effectiveDate: '2023-01-10', riskLevel: 'high' },
      { name: 'Generative AI Measures', status: 'enforced', effectiveDate: '2023-08-15', riskLevel: 'high' }
    ],
    complianceScore: 95,
    lastUpdated: '2024-01-12'
  },
  'UK': {
    name: 'United Kingdom',
    flag: '🇬🇧',
    status: 'developing',
    laws: [
      { name: 'AI White Paper', status: 'consultation', effectiveDate: '2024-06-01', riskLevel: 'medium' },
      { name: 'Data Protection Act 2018', status: 'enforced', effectiveDate: '2018-05-25', riskLevel: 'high' }
    ],
    complianceScore: 68,
    lastUpdated: '2024-01-08'
  },
  'CA': {
    name: 'Canada',
    flag: '🇨🇦',
    status: 'developing',
    laws: [
      { name: 'AIDA (Bill C-27)', status: 'pending', effectiveDate: '2024-12-01', riskLevel: 'high' },
      { name: 'PIPEDA', status: 'enforced', effectiveDate: '2000-04-13', riskLevel: 'medium' }
    ],
    complianceScore: 58,
    lastUpdated: '2024-01-05'
  },
  'JP': {
    name: 'Japan',
    flag: '🇯🇵',
    status: 'developing',
    laws: [
      { name: 'AI Strategy 2022', status: 'guidance', effectiveDate: '2022-12-01', riskLevel: 'low' },
      { name: 'Personal Information Protection Act', status: 'enforced', effectiveDate: '2003-05-30', riskLevel: 'medium' }
    ],
    complianceScore: 62,
    lastUpdated: '2024-01-03'
  },
  'AU': {
    name: 'Australia',
    flag: '🇦🇺',
    status: 'developing',
    laws: [
      { name: 'AI Action Plan', status: 'guidance', effectiveDate: '2021-06-01', riskLevel: 'low' },
      { name: 'Privacy Act 1988', status: 'enforced', effectiveDate: '1988-12-21', riskLevel: 'medium' }
    ],
    complianceScore: 55,
    lastUpdated: '2024-01-01'
  },
  'IN': {
    name: 'India',
    flag: '🇮🇳',
    status: 'developing',
    laws: [
      { name: 'Digital India Act', status: 'draft', effectiveDate: '2024-12-01', riskLevel: 'high' },
      { name: 'Personal Data Protection Bill', status: 'pending', effectiveDate: '2024-06-01', riskLevel: 'high' }
    ],
    complianceScore: 45,
    lastUpdated: '2023-12-28'
  }
};

// Compliance requirements by AI use case
const complianceRequirements = [
  {
    useCase: 'High-Risk AI Systems',
    requirements: [
      'Risk management system',
      'Data governance',
      'Technical documentation',
      'Record keeping',
      'Transparency and provision of information',
      'Human oversight',
      'Accuracy, robustness and cybersecurity'
    ],
    applicableLaws: ['EU AI Act', 'AIDA (Canada)', 'State AI Laws (US)'],
    riskLevel: 'critical'
  },
  {
    useCase: 'Generative AI',
    requirements: [
      'Content labeling and disclosure',
      'Copyright compliance',
      'Bias and discrimination prevention',
      'Data protection compliance',
      'Transparency reporting'
    ],
    applicableLaws: ['EU AI Act', 'Deep Synthesis Provisions (China)', 'Executive Order 14110 (US)'],
    riskLevel: 'high'
  },
  {
    useCase: 'Automated Decision Making',
    requirements: [
      'Explainability and interpretability',
      'Human review rights',
      'Bias testing and monitoring',
      'Data minimization',
      'Consent management'
    ],
    applicableLaws: ['GDPR', 'Algorithmic Recommendation Provisions (China)', 'PIPEDA (Canada)'],
    riskLevel: 'high'
  },
  {
    useCase: 'AI in Healthcare',
    requirements: [
      'Medical device certification',
      'Clinical validation',
      'Patient safety monitoring',
      'Data privacy protection',
      'Professional oversight'
    ],
    applicableLaws: ['EU AI Act', 'FDA Guidelines (US)', 'Health Canada Regulations'],
    riskLevel: 'critical'
  }
];

export default function ComplianceDashboard() {
  const { colorScheme } = useMantineColorScheme();
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [isLoading, setIsLoading] = useState(true);

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
            <IconScale size="2rem" />
          </ThemeIcon>
          <Text size="xl" fw={600}>
            Loading Compliance Dashboard...
          </Text>
          <Loader size="lg" />
        </Stack>
      </Center>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'enforced': return 'red';
      case 'enacted': return 'orange';
      case 'pending': return 'yellow';
      case 'guidance': return 'blue';
      case 'consultation': return 'grape';
      case 'draft': return 'gray';
      default: return 'gray';
    }
  };

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'critical': return 'red';
      case 'high': return 'orange';
      case 'medium': return 'yellow';
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
                AI Compliance Center
              </Title>
              <Text c="dimmed" size="lg" fw={500}>
                Global AI Laws, Regulations & Compliance Tracking
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
                Update Laws
              </Button>
              <Button
                variant="filled"
                leftSection={<IconPlus size="1rem" />}
                size="lg"
                style={{
                  borderRadius: '16px',
                  background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                  border: 'none',
                }}
              >
                Add Assessment
              </Button>
            </Group>
          </Group>

          {/* Global Compliance Overview */}
          <SimpleGrid cols={{ base: 2, sm: 4 }} mt="xl">
            {[
              { 
                label: 'Countries Monitored', 
                value: Object.keys(aiLawsData).length, 
                color: 'blue', 
                icon: IconWorld 
              },
              { 
                label: 'Active Laws', 
                value: Object.values(aiLawsData).flatMap(c => c.laws).filter(l => l.status === 'enforced' || l.status === 'enacted').length, 
                color: 'red', 
                icon: IconGavel 
              },
              { 
                label: 'Avg Compliance Score', 
                value: `${Math.round(Object.values(aiLawsData).reduce((acc, c) => acc + c.complianceScore, 0) / Object.keys(aiLawsData).length)}%`, 
                color: 'green', 
                icon: IconTarget 
              },
              { 
                label: 'Pending Regulations', 
                value: Object.values(aiLawsData).flatMap(c => c.laws).filter(l => l.status === 'pending' || l.status === 'draft').length, 
                color: 'orange', 
                icon: IconClock 
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
                        metric.color === 'green' ? '34, 197, 94' : '245, 158, 11'}, 0.1)`,
                      border: `1px solid rgba(${metric.color === 'blue' ? '59, 130, 246' : 
                        metric.color === 'red' ? '239, 68, 68' : 
                        metric.color === 'green' ? '34, 197, 94' : '245, 158, 11'}, 0.2)`,
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
                           metric.color === 'green' ? '#22c55e' : '#f59e0b',
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
          {/* World Map and Country Laws */}
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
                Global AI Laws & Regulations
              </Title>
              
              {/* Interactive World Map Representation */}
              <Box
                style={{
                  background: 'linear-gradient(135deg, #1e3a8a, #3730a3)',
                  borderRadius: '20px',
                  padding: '2rem',
                  position: 'relative',
                  overflow: 'hidden',
                  minHeight: '400px',
                }}
              >
                {/* Simplified World Map Grid */}
                <SimpleGrid cols={4} spacing="md">
                  {Object.entries(aiLawsData).map(([code, country]) => (
                    <Card
                      key={code}
                      p="md"
                      style={{
                        background: selectedCountry === code 
                          ? 'rgba(59, 130, 246, 0.2)' 
                          : 'rgba(255, 255, 255, 0.1)',
                        border: selectedCountry === code 
                          ? '2px solid #3b82f6' 
                          : '1px solid rgba(255, 255, 255, 0.2)',
                        borderRadius: '16px',
                        cursor: 'pointer',
                        transition: 'all 0.3s ease',
                        transform: selectedCountry === code ? 'scale(1.05)' : 'scale(1)',
                      }}
                      onClick={() => setSelectedCountry(selectedCountry === code ? null : code)}
                    >
                      <Stack align="center" gap="sm">
                        <Text size="2rem">{country.flag}</Text>
                        <Text fw={600} size="sm" ta="center">{country.name}</Text>
                        <Badge
                          color={getStatusColor(country.status)}
                          variant="light"
                          size="sm"
                          style={{ borderRadius: '12px' }}
                        >
                          {country.status}
                        </Badge>
                        <RingProgress
                          size={60}
                          thickness={6}
                          sections={[{ value: country.complianceScore, color: '#3b82f6' }]}
                          label={
                            <Text ta="center" size="xs" fw={600}>
                              {country.complianceScore}%
                            </Text>
                          }
                        />
                        <Text size="xs" c="dimmed" ta="center">
                          {country.laws.length} laws
                        </Text>
                      </Stack>
                    </Card>
                  ))}
                </SimpleGrid>
              </Box>
            </Card>
          </Grid.Col>

          {/* Country Details Panel */}
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
                {selectedCountry ? `${aiLawsData[selectedCountry as keyof typeof aiLawsData]?.name} Laws` : 'Select a Country'}
              </Title>
              
              {selectedCountry ? (
                <Stack gap="md">
                  {aiLawsData[selectedCountry as keyof typeof aiLawsData]?.laws.map((law, index) => (
                    <Card
                      key={index}
                      p="md"
                      style={{
                        background: 'rgba(255, 255, 255, 0.05)',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                        borderRadius: '12px',
                      }}
                    >
                      <Group justify="space-between" mb="xs">
                        <Text fw={600} size="sm">{law.name}</Text>
                        <Badge
                          color={getStatusColor(law.status)}
                          variant="light"
                          size="xs"
                        >
                          {law.status}
                        </Badge>
                      </Group>
                      <Group justify="space-between" mb="xs">
                        <Text size="xs" c="dimmed">Effective Date</Text>
                        <Text size="xs" fw={500}>{law.effectiveDate}</Text>
                      </Group>
                      <Group justify="space-between">
                        <Text size="xs" c="dimmed">Risk Level</Text>
                        <Badge
                          color={getRiskColor(law.riskLevel)}
                          variant="light"
                          size="xs"
                        >
                          {law.riskLevel}
                        </Badge>
                      </Group>
                    </Card>
                  ))}
                  
                  <Divider />
                  
                  <Group justify="space-between">
                    <Text size="sm" c="dimmed">Overall Compliance</Text>
                    <Text size="lg" fw={700} c="blue">
                      {aiLawsData[selectedCountry as keyof typeof aiLawsData]?.complianceScore}%
                    </Text>
                  </Group>
                  
                  <Progress
                    value={aiLawsData[selectedCountry as keyof typeof aiLawsData]?.complianceScore}
                    color="blue"
                    size="lg"
                    radius="xl"
                  />
                </Stack>
              ) : (
                <Center style={{ height: '300px' }}>
                  <Stack align="center" gap="md">
                    <ThemeIcon size="xl" radius="xl" color="gray" variant="light">
                      <IconMapPin size="2rem" />
                    </ThemeIcon>
                    <Text c="dimmed" ta="center">
                      Click on a country to view<br />its AI laws and regulations
                    </Text>
                  </Stack>
                </Center>
              )}
            </Card>
          </Grid.Col>
        </Grid>

        {/* Compliance Requirements by Use Case */}
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
            Compliance Requirements by AI Use Case
          </Title>
          
          <SimpleGrid cols={{ base: 1, md: 2 }} gap="xl">
            {complianceRequirements.map((requirement, index) => (
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
                  <Text fw={600} size="lg">{requirement.useCase}</Text>
                  <Badge
                    color={getRiskColor(requirement.riskLevel)}
                    variant="light"
                    size="lg"
                    style={{ borderRadius: '12px' }}
                  >
                    {requirement.riskLevel}
                  </Badge>
                </Group>
                
                <Stack gap="sm" mb="md">
                  <Text size="sm" fw={500} c="dimmed">Key Requirements:</Text>
                  <List size="sm" spacing="xs">
                    {requirement.requirements.map((req, reqIndex) => (
                      <List.Item key={reqIndex}>
                        <Text size="sm">{req}</Text>
                      </List.Item>
                    ))}
                  </List>
                </Stack>
                
                <Divider mb="md" />
                
                <Stack gap="xs">
                  <Text size="sm" fw={500} c="dimmed">Applicable Laws:</Text>
                  <Group gap="xs">
                    {requirement.applicableLaws.map((law, lawIndex) => (
                      <Badge
                        key={lawIndex}
                        variant="outline"
                        size="sm"
                        style={{ borderRadius: '8px' }}
                      >
                        {law}
                      </Badge>
                    ))}
                  </Group>
                </Stack>
              </Card>
            ))}
          </SimpleGrid>
        </Card>
      </Container>
    </Box>
  );
}