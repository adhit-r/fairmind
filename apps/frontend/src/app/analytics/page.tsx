'use client';

import {
  Container,
  Title,
  Text,
  Card,
  SimpleGrid,
  Stack,
  Group,
  Button,
  Badge,
  ThemeIcon,
  Box,
  Table,
  ActionIcon,
  Progress,
  RingProgress,
  Tabs,
} from '@mantine/core';
import {
  IconChartBar,
  IconTrendingUp,
  IconShield,
  IconAlertTriangle,
  IconDownload,
  IconEye,
  IconRefresh,
  IconBrain,
  IconTarget,
} from '@tabler/icons-react';
import { useState } from 'react';

// Mock data - replace with real data from your backend
const mockAnalyticsData = {
  overallMetrics: {
    totalModels: 147,
    activeModels: 89,
    complianceRate: 94.2,
    riskScore: 23.1,
    biasIncidents: 2,
    securityVulnerabilities: 1,
  },
  trends: {
    monthly: [
      { month: 'Jan', models: 12, compliance: 89, risks: 15 },
      { month: 'Feb', models: 18, compliance: 91, risks: 12 },
      { month: 'Mar', models: 22, compliance: 93, risks: 10 },
      { month: 'Apr', models: 25, compliance: 94, risks: 8 },
      { month: 'May', models: 28, compliance: 95, risks: 6 },
      { month: 'Jun', models: 32, compliance: 96, risks: 4 },
    ],
  },
  topRisks: [
    { model: 'credit-scoring-v2.1', risk: 'High', category: 'Bias', score: 8.7 },
    { model: 'fraud-detection-ai', risk: 'Medium', category: 'Security', score: 6.3 },
    { model: 'recruitment-filter', risk: 'Medium', category: 'Bias', score: 5.9 },
    { model: 'loan-approval-v3', risk: 'Low', category: 'Transparency', score: 3.2 },
  ],
  complianceBreakdown: [
    { framework: 'EU AI Act', compliance: 87, status: 'In Progress' },
    { framework: 'NIST AI RMF', compliance: 92, status: 'Compliant' },
    { framework: 'GDPR', compliance: 95, status: 'Compliant' },
    { framework: 'ISO 42001', compliance: 78, status: 'In Progress' },
  ],
};

export default function AnalyticsPage() {
  const [selectedMetric, setSelectedMetric] = useState('compliance');
  const [selectedFramework, setSelectedFramework] = useState('all');

  return (
    <Container size="xl" py="xl">
      <Stack spacing="xl">
        {/* Header */}
        <Group position="apart">
          <Box>
            <Title order={1}>Analytics & Reporting</Title>
            <Text color="dimmed" size="sm">
              Comprehensive insights into your AI governance and compliance metrics
            </Text>
          </Box>
          <Group>
            <Button leftIcon={<IconDownload size={16} />} variant="outline">
              Export Report
            </Button>
            <Button leftIcon={<IconRefresh size={16} />}>
              Refresh Data
            </Button>
          </Group>
        </Group>

        {/* Filters */}
        <Card withBorder>
          <Group position="apart">
            <Text weight={500}>Filters & Date Range</Text>
            <Group>
              <Box>
                <Text size="sm" weight={500} mb="xs">Primary Metric</Text>
                <select
                  value={selectedMetric}
                  onChange={(e) => setSelectedMetric(e.target.value)}
                  style={{ 
                    width: 200, 
                    padding: '8px 12px', 
                    border: '1px solid #ced4da', 
                    borderRadius: '4px',
                    fontSize: '14px'
                  }}
                >
                  <option value="compliance">Compliance Rate</option>
                  <option value="risks">Risk Score</option>
                  <option value="bias">Bias Incidents</option>
                  <option value="security">Security Vulnerabilities</option>
                </select>
              </Box>
              <Box>
                <Text size="sm" weight={500} mb="xs">Framework</Text>
                <select
                  value={selectedFramework}
                  onChange={(e) => setSelectedFramework(e.target.value)}
                  style={{ 
                    width: 200, 
                    padding: '8px 12px', 
                    border: '1px solid #ced4da', 
                    borderRadius: '4px',
                    fontSize: '14px'
                  }}
                >
                  <option value="all">All Frameworks</option>
                  <option value="eu-ai-act">EU AI Act</option>
                  <option value="nist-ai-rmf">NIST AI RMF</option>
                  <option value="gdpr">GDPR</option>
                  <option value="iso-42001">ISO 42001</option>
                </select>
              </Box>
            </Group>
          </Group>
        </Card>

        {/* Key Metrics */}
        <SimpleGrid cols={3} spacing="lg">
          <Card withBorder>
            <Group position="apart">
              <Box>
                <Text size="xs" color="dimmed" transform="uppercase">
                  Overall Compliance
                </Text>
                <Text size="xl" weight={700}>
                  {mockAnalyticsData.overallMetrics.complianceRate}%
                </Text>
              </Box>
              <ThemeIcon size="xl" radius="md" color="blue">
                <IconShield size={24} />
              </ThemeIcon>
            </Group>
            <Progress
              value={mockAnalyticsData.overallMetrics.complianceRate}
              color="blue"
              size="sm"
              mt="md"
            />
          </Card>

          <Card withBorder>
            <Group position="apart">
              <Box>
                <Text size="xs" color="dimmed" transform="uppercase">
                  Risk Score
                </Text>
                <Text size="xl" weight={700}>
                  {mockAnalyticsData.overallMetrics.riskScore}
                </Text>
              </Box>
              <ThemeIcon size="xl" radius="md" color="orange">
                <IconAlertTriangle size={24} />
              </ThemeIcon>
            </Group>
            <Progress
              value={100 - mockAnalyticsData.overallMetrics.riskScore * 10}
              color="orange"
              size="sm"
              mt="md"
            />
          </Card>

          <Card withBorder>
            <Group position="apart">
              <Box>
                <Text size="xs" color="dimmed" transform="uppercase">
                  Active Models
                </Text>
                <Text size="xl" weight={700}>
                  {mockAnalyticsData.overallMetrics.activeModels}
                </Text>
              </Box>
              <ThemeIcon size="xl" radius="md" color="green">
                <IconBrain size={24} />
              </ThemeIcon>
            </Group>
            <Text size="sm" color="dimmed" mt="md">
              of {mockAnalyticsData.overallMetrics.totalModels} total
            </Text>
          </Card>
        </SimpleGrid>

        {/* Charts and Visualizations */}
        <Tabs defaultValue="trends">
          <Tabs.List>
            <Tabs.Tab value="trends" icon={<IconTrendingUp size={16} />}>
              Trends
            </Tabs.Tab>
            <Tabs.Tab value="risks" icon={<IconAlertTriangle size={16} />}>
              Risk Analysis
            </Tabs.Tab>
            <Tabs.Tab value="compliance" icon={<IconShield size={16} />}>
              Compliance
            </Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="trends" pt="md">
            <Card withBorder>
              <Title order={3} mb="md">Monthly Trends</Title>
              <SimpleGrid cols={2} spacing="lg">
                <Box>
                  <Text weight={500} mb="sm">Models Added</Text>
                  <div style={{ height: 200, display: 'flex', alignItems: 'end', gap: 8 }}>
                    {mockAnalyticsData.trends.monthly.map((item, index) => (
                      <div
                        key={index}
                        style={{
                          width: 30,
                          height: (item.models / 32) * 200,
                          backgroundColor: 'var(--mantine-color-blue-6)',
                          borderRadius: '4px 4px 0 0',
                        }}
                      />
                    ))}
                  </div>
                  <Group position="apart" mt="xs">
                    {mockAnalyticsData.trends.monthly.map((item, index) => (
                      <Text key={index} size="xs" color="dimmed">
                        {item.month}
                      </Text>
                    ))}
                  </Group>
                </Box>
                <Box>
                  <Text weight={500} mb="sm">Compliance Rate</Text>
                  <div style={{ height: 200, display: 'flex', alignItems: 'end', gap: 8 }}>
                    {mockAnalyticsData.trends.monthly.map((item, index) => (
                      <div
                        key={index}
                        style={{
                          width: 30,
                          height: (item.compliance / 100) * 200,
                          backgroundColor: 'var(--mantine-color-green-6)',
                          borderRadius: '4px 4px 0 0',
                        }}
                      />
                    ))}
                  </div>
                  <Group position="apart" mt="xs">
                    {mockAnalyticsData.trends.monthly.map((item, index) => (
                      <Text key={index} size="xs" color="dimmed">
                        {item.month}
                      </Text>
                    ))}
                  </Group>
                </Box>
              </SimpleGrid>
            </Card>
          </Tabs.Panel>

          <Tabs.Panel value="risks" pt="md">
            <Card withBorder>
              <Title order={3} mb="md">Top Risk Models</Title>
              <Table>
                <thead>
                  <tr>
                    <th>Model</th>
                    <th>Risk Level</th>
                    <th>Category</th>
                    <th>Risk Score</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {mockAnalyticsData.topRisks.map((risk, index) => (
                    <tr key={index}>
                      <td>
                        <Text weight={500}>{risk.model}</Text>
                      </td>
                      <td>
                        <Badge
                          color={
                            risk.risk === 'High' ? 'red' :
                            risk.risk === 'Medium' ? 'orange' : 'green'
                          }
                        >
                          {risk.risk}
                        </Badge>
                      </td>
                      <td>{risk.category}</td>
                      <td>
                        <Text weight={500} color="red">
                          {risk.score}
                        </Text>
                      </td>
                      <td>
                        <Group spacing="xs">
                          <ActionIcon size="sm" variant="subtle">
                            <IconEye size={16} />
                          </ActionIcon>
                          <ActionIcon size="sm" variant="subtle">
                            <IconDownload size={16} />
                          </ActionIcon>
                        </Group>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </Card>
          </Tabs.Panel>

          <Tabs.Panel value="compliance" pt="md">
            <Card withBorder>
              <Title order={3} mb="md">Compliance by Framework</Title>
              <SimpleGrid cols={2} spacing="lg">
                {mockAnalyticsData.complianceBreakdown.map((framework, index) => (
                  <Card key={index} withBorder p="md">
                    <Group position="apart" mb="md">
                      <Text weight={500}>{framework.framework}</Text>
                      <Badge
                        color={
                          framework.status === 'Compliant' ? 'green' :
                          framework.status === 'In Progress' ? 'orange' : 'red'
                        }
                      >
                        {framework.status}
                      </Badge>
                    </Group>
                    <Group position="apart" align="center">
                      <RingProgress
                        size={80}
                        thickness={8}
                        sections={[{ value: framework.compliance, color: 'blue' }]}
                        label={
                          <Text size="xs" align="center" weight={700}>
                            {framework.compliance}%
                          </Text>
                        }
                      />
                      <Box>
                        <Text size="sm" color="dimmed">
                          Target: 100%
                        </Text>
                        <Text size="sm" color="dimmed">
                          Gap: {100 - framework.compliance}%
                        </Text>
                      </Box>
                    </Group>
                  </Card>
                ))}
              </SimpleGrid>
            </Card>
          </Tabs.Panel>
        </Tabs>

        {/* Quick Actions */}
        <Card withBorder>
          <Title order={3} mb="md">Quick Actions</Title>
          <Group>
            <Button leftIcon={<IconDownload size={16} />} variant="outline">
              Generate Executive Report
            </Button>
            <Button leftIcon={<IconDownload size={16} />} variant="outline">
              Export Risk Assessment
            </Button>
            <Button leftIcon={<IconDownload size={16} />} variant="outline">
              Compliance Summary
            </Button>
            <Button leftIcon={<IconDownload size={16} />} variant="outline">
              Bias Analysis Report
            </Button>
          </Group>
        </Card>
      </Stack>
    </Container>
  );
}
