'use client';

import {
  Container,
  Title,
  Text,
  Button,
  Card,
  Group,
  Stack,
  SimpleGrid,
  Table,
  ActionIcon,
  ThemeIcon,
  Badge,
  Select,
  TextInput,
} from '@mantine/core';
import {
  IconFileText,
  IconDownload,
  IconEye,
  IconCalendar,
  IconChartBar,
  IconUsers,
  IconShield,
  IconTarget,
  IconRefresh,
} from '@tabler/icons-react';
import { useApi } from '@/hooks/useApi';
import { useState } from 'react';

const neo = {
  card: {
    background: 'rgba(255, 255, 255, 0.9)',
    backdropFilter: 'blur(20px)',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '20px',
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
  },
};

const reports = [
  {
    id: 1,
    name: 'Monthly Bias Assessment Report',
    description: 'Comprehensive bias analysis across all production models',
    type: 'Bias Analysis',
    format: 'PDF',
    size: '2.4 MB',
    generated: '2024-01-22',
    author: 'AI Governance Team',
    models: 24,
    status: 'completed',
  },
  {
    id: 2,
    name: 'Quarterly Compliance Dashboard',
    description: 'Regulatory compliance status and framework adherence',
    type: 'Compliance',
    format: 'Excel',
    size: '1.8 MB',
    generated: '2024-01-20',
    author: 'Compliance Office',
    models: 47,
    status: 'completed',
  },
  {
    id: 3,
    name: 'Model Performance Summary',
    description: 'Performance metrics and benchmarking results',
    type: 'Performance',
    format: 'PDF',
    size: '3.2 MB',
    generated: '2024-01-19',
    author: 'MLOps Team',
    models: 35,
    status: 'completed',
  },
  {
    id: 4,
    name: 'Risk Assessment Report',
    description: 'Current risk landscape and incident summary',
    type: 'Risk Management',
    format: 'PDF',
    size: '1.9 MB',
    generated: '2024-01-18',
    author: 'Risk Management',
    models: 18,
    status: 'completed',
  },
];

const reportStats = [
  {
    title: 'Generated Reports',
    value: '127',
    icon: IconFileText,
    color: 'blue',
  },
  {
    title: 'This Month',
    value: '24',
    icon: IconCalendar,
    color: 'green',
  },
  {
    title: 'Total Downloads',
    value: '1,456',
    icon: IconDownload,
    color: 'violet',
  },
  {
    title: 'Automated Reports',
    value: '89%',
    icon: IconChartBar,
    color: 'orange',
  },
];

const reportTemplates = [
  {
    name: 'Executive Summary',
    description: 'High-level overview for stakeholders',
    icon: IconUsers,
    color: 'blue',
  },
  {
    name: 'Technical Deep Dive',
    description: 'Detailed technical analysis and metrics',
    icon: IconChartBar,
    color: 'green',
  },
  {
    name: 'Compliance Report',
    description: 'Regulatory compliance and audit trail',
    icon: IconShield,
    color: 'yellow',
  },
  {
    name: 'Risk Assessment',
    description: 'Risk analysis and mitigation strategies',
    icon: IconTarget,
    color: 'red',
  },
];

function getStatusColor(status: string) {
  switch (status) {
    case 'completed':
      return 'green';
    case 'generating':
      return 'blue';
    case 'failed':
      return 'red';
    default:
      return 'gray';
  }
}

export default function ReportsPage() {
  const { data: reportsData, loading, error } = useApi('/api/v1/reports');
  const [dateRange, setDateRange] = useState('');

  return (
    <Container size="xl" py="xl">
      <Stack gap="xl">
        {/* Header */}
        <Card style={neo.card} p="xl">
          <Group justify="space-between" align="center">
            <div>
              <Title order={1} size="2rem" fw={700} c="#1e293b" mb="xs">
                Automated Reporting
              </Title>
              <Text c="dimmed" size="lg">
                Generate comprehensive AI governance and compliance reports
              </Text>
            </div>
            <Group gap="sm">
              <ActionIcon size="lg" radius="xl" variant="light" color="blue">
                <IconRefresh size={20} />
              </ActionIcon>
              <Button
                leftSection={<IconFileText size={16} />}
                radius="xl"
                style={{
                  background: 'linear-gradient(145deg, #7c3aed, #6d28d9)',
                  boxShadow: '6px 6px 12px rgba(124, 58, 237, 0.4), -4px -4px 8px rgba(139, 92, 246, 0.4)',
                }}
              >
                Generate Report
              </Button>
            </Group>
          </Group>
        </Card>

        {/* Statistics */}
        <SimpleGrid cols={{ base: 2, md: 4 }} spacing="lg">
          {reportStats.map((stat) => (
            <Card key={stat.title} style={neo.card} p="lg">
              <Stack gap="sm">
                <ThemeIcon size="lg" radius="xl" color={stat.color} variant="light">
                  <stat.icon size={20} />
                </ThemeIcon>
                <div>
                  <Text size="2xl" fw={700} c="#1e293b">
                    {stat.value}
                  </Text>
                  <Text size="sm" c="dimmed">
                    {stat.title}
                  </Text>
                </div>
              </Stack>
            </Card>
          ))}
        </SimpleGrid>

        {/* Report Templates */}
        <Card style={neo.card} p="xl">
          <Title order={3} size="lg" fw={600} mb="lg">
            Report Templates
          </Title>
          <SimpleGrid cols={{ base: 2, md: 4 }} spacing="lg">
            {reportTemplates.map((template, index) => (
              <Card
                key={index}
                style={{
                  background: 'rgba(255, 255, 255, 0.6)',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  borderRadius: '12px',
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-2px)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                }}
                p="lg"
              >
                <Stack gap="sm" align="center">
                  <ThemeIcon size="xl" radius="xl" color={template.color} variant="light">
                    <template.icon size={24} />
                  </ThemeIcon>
                  <div style={{ textAlign: 'center' }}>
                    <Text fw={600} size="sm">
                      {template.name}
                    </Text>
                    <Text size="xs" c="dimmed">
                      {template.description}
                    </Text>
                  </div>
                </Stack>
              </Card>
            ))}
          </SimpleGrid>
        </Card>

        {/* Filters */}
        <Card style={neo.card} p="lg">
          <Group gap="md">
            <Select
              placeholder="Report Type"
              data={[
                { value: 'all', label: 'All Reports' },
                { value: 'bias', label: 'Bias Analysis' },
                { value: 'compliance', label: 'Compliance' },
                { value: 'performance', label: 'Performance' },
                { value: 'risk', label: 'Risk Management' },
              ]}
              style={{ minWidth: 150 }}
            />
            <Select
              placeholder="Format"
              data={[
                { value: 'all', label: 'All Formats' },
                { value: 'pdf', label: 'PDF' },
                { value: 'excel', label: 'Excel' },
                { value: 'csv', label: 'CSV' },
              ]}
              style={{ minWidth: 120 }}
            />
            <TextInput
              placeholder="Date Range"
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              style={{ minWidth: 200 }}
            />
          </Group>
        </Card>

        {/* Reports Table */}
        <Card style={neo.card} p="xl">
          <Group justify="space-between" align="center" mb="lg">
            <Title order={3} size="lg" fw={600}>
              Generated Reports
            </Title>
          </Group>

          <Table.ScrollContainer minWidth={800}>
            <Table>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Report</Table.Th>
                  <Table.Th>Type</Table.Th>
                  <Table.Th>Format</Table.Th>
                  <Table.Th>Size</Table.Th>
                  <Table.Th>Generated</Table.Th>
                  <Table.Th>Models</Table.Th>
                  <Table.Th>Actions</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {reports.map((report) => (
                  <Table.Tr key={report.id}>
                    <Table.Td>
                      <div>
                        <Text fw={600} size="sm">
                          {report.name}
                        </Text>
                        <Text size="xs" c="dimmed" lineClamp={2}>
                          {report.description}
                        </Text>
                        <Text size="xs" c="dimmed" mt="xs">
                          By {report.author}
                        </Text>
                      </div>
                    </Table.Td>
                    <Table.Td>
                      <Badge size="sm" radius="md" variant="light" color="blue">
                        {report.type}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <Badge size="sm" radius="md" variant="light" color="gray">
                        {report.format}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">{report.size}</Text>
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs" align="center">
                        <IconCalendar size={14} color="#6b7280" />
                        <Text size="xs" c="dimmed">
                          {new Date(report.generated).toLocaleDateString()}
                        </Text>
                      </Group>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm" fw={500}>
                        {report.models} models
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs">
                        <ActionIcon size="sm" variant="light" radius="xl">
                          <IconEye size={14} />
                        </ActionIcon>
                        <ActionIcon size="sm" variant="light" radius="xl">
                          <IconDownload size={14} />
                        </ActionIcon>
                      </Group>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Table.ScrollContainer>
        </Card>
      </Stack>
    </Container>
  );
}