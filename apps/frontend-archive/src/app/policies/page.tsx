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
  Badge,
  Table,
  ActionIcon,
  ThemeIcon,
  Menu,
  TextInput,
  Textarea,
  Select,
  Modal,
} from '@mantine/core';
import {
  IconGavel,
  IconPlus,
  IconEdit,
  IconTrash,
  IconDots,
  IconFileText,
  IconUsers,
  IconCalendar,
  IconCheck,
  IconAlertTriangle,
  IconClock,
  IconSearch,
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

const policies = [
  {
    id: 1,
    name: 'AI Model Bias Assessment Policy',
    description: 'Mandatory bias testing requirements for all production models',
    category: 'Bias & Fairness',
    status: 'active',
    version: '2.1',
    created: '2024-01-15',
    lastUpdated: '2024-01-20',
    author: 'AI Governance Team',
    scope: 'All Models',
    compliance: 95,
  },
  {
    id: 2,
    name: 'Data Privacy Protection Standard',
    description: 'Guidelines for handling sensitive data in ML pipelines',
    category: 'Privacy',
    status: 'active',
    version: '1.3',
    created: '2024-01-10',
    lastUpdated: '2024-01-18',
    author: 'Privacy Office',
    scope: 'Data Processing',
    compliance: 88,
  },
  {
    id: 3,
    name: 'Model Documentation Requirements',
    description: 'Mandatory documentation standards for model deployment',
    category: 'Documentation',
    status: 'draft',
    version: '3.0',
    created: '2024-01-22',
    lastUpdated: '2024-01-22',
    author: 'Documentation Team',
    scope: 'All Models',
    compliance: 0,
  },
  {
    id: 4,
    name: 'Automated Monitoring Standards',
    description: 'Requirements for continuous model performance monitoring',
    category: 'Monitoring',
    status: 'review',
    version: '1.8',
    created: '2024-01-12',
    lastUpdated: '2024-01-19',
    author: 'MLOps Team',
    scope: 'Production Models',
    compliance: 72,
  },
];

const policyStats = [
  {
    title: 'Active Policies',
    value: '24',
    icon: IconGavel,
    color: 'blue',
  },
  {
    title: 'In Review',
    value: '6',
    icon: IconClock,
    color: 'yellow',
  },
  {
    title: 'Compliance Rate',
    value: '89%',
    icon: IconCheck,
    color: 'green',
  },
  {
    title: 'Policy Violations',
    value: '3',
    icon: IconAlertTriangle,
    color: 'red',
  },
];

function getStatusColor(status: string) {
  switch (status) {
    case 'active':
      return 'green';
    case 'draft':
      return 'blue';
    case 'review':
      return 'yellow';
    case 'archived':
      return 'gray';
    default:
      return 'gray';
  }
}

function getComplianceColor(score: number) {
  if (score >= 90) return 'green';
  if (score >= 80) return 'blue';
  if (score >= 70) return 'yellow';
  return 'red';
}

export default function PoliciesPage() {
  const { data: policiesData, loading, error } = useApi('/api/v1/policies');
  const [opened, setOpened] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  const filteredPolicies = policies.filter(policy =>
    policy.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    policy.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Container size="xl" py="xl">
      <Stack gap="xl">
        {/* Header */}
        <Card style={neo.card} p="xl">
          <Group justify="space-between" align="center">
            <div>
              <Title order={1} size="2rem" fw={700} c="#1e293b" mb="xs">
                Policy Management
              </Title>
              <Text c="dimmed" size="lg">
                Create and manage AI governance policies and standards
              </Text>
            </div>
            <Button
              size="lg"
              radius="xl"
              leftSection={<IconPlus size={20} />}
              onClick={() => setOpened(true)}
              style={{
                background: 'linear-gradient(145deg, #059669, #047857)',
                boxShadow: '6px 6px 12px rgba(5, 150, 105, 0.4), -4px -4px 8px rgba(16, 185, 129, 0.4)',
              }}
            >
              Create Policy
            </Button>
          </Group>
        </Card>

        {/* Statistics */}
        <SimpleGrid cols={{ base: 2, md: 4 }} spacing="lg">
          {policyStats.map((stat) => (
            <Card
              key={stat.title}
              style={{
                ...neo.card,
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
              <Stack gap="sm">
                <ThemeIcon
                  size="lg"
                  radius="xl"
                  color={stat.color}
                  variant="light"
                >
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

        {/* Search and Filters */}
        <Card style={neo.card} p="lg">
          <Group gap="md">
            <TextInput
              placeholder="Search policies..."
              leftSection={<IconSearch size={16} />}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{ flex: 1 }}
            />
            <Select
              placeholder="Filter by category"
              data={[
                { value: '', label: 'All Categories' },
                { value: 'Bias & Fairness', label: 'Bias & Fairness' },
                { value: 'Privacy', label: 'Privacy' },
                { value: 'Documentation', label: 'Documentation' },
                { value: 'Monitoring', label: 'Monitoring' },
              ]}
              style={{ minWidth: 200 }}
            />
          </Group>
        </Card>

        {/* Policies Table */}
        <Card style={neo.card} p="xl">
          <Group justify="space-between" align="center" mb="lg">
            <Title order={3} size="lg" fw={600}>
              Policy Registry
            </Title>
          </Group>

          <Table.ScrollContainer minWidth={800}>
            <Table>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Policy</Table.Th>
                  <Table.Th>Category</Table.Th>
                  <Table.Th>Status</Table.Th>
                  <Table.Th>Version</Table.Th>
                  <Table.Th>Compliance</Table.Th>
                  <Table.Th>Last Updated</Table.Th>
                  <Table.Th>Actions</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {filteredPolicies.map((policy) => (
                  <Table.Tr key={policy.id}>
                    <Table.Td>
                      <div>
                        <Text fw={600} size="sm">
                          {policy.name}
                        </Text>
                        <Text size="xs" c="dimmed" lineClamp={2}>
                          {policy.description}
                        </Text>
                        <Group gap="xs" mt="xs">
                          <Badge size="xs" variant="light" color="gray">
                            {policy.scope}
                          </Badge>
                        </Group>
                      </div>
                    </Table.Td>
                    <Table.Td>
                      <Badge
                        size="sm"
                        radius="md"
                        variant="light"
                        color="blue"
                      >
                        {policy.category}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <Badge
                        size="sm"
                        radius="md"
                        color={getStatusColor(policy.status)}
                        variant="light"
                      >
                        {policy.status}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm" fw={500}>
                        v{policy.version}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs" align="center">
                        <Text
                          size="sm"
                          fw={600}
                          c={getComplianceColor(policy.compliance)}
                        >
                          {policy.compliance}%
                        </Text>
                      </Group>
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs" align="center">
                        <IconCalendar size={14} color="#6b7280" />
                        <Text size="xs" c="dimmed">
                          {new Date(policy.lastUpdated).toLocaleDateString()}
                        </Text>
                      </Group>
                    </Table.Td>
                    <Table.Td>
                      <Menu shadow="md" width={200}>
                        <Menu.Target>
                          <ActionIcon
                            variant="light"
                            size="sm"
                            radius="xl"
                          >
                            <IconDots size={14} />
                          </ActionIcon>
                        </Menu.Target>

                        <Menu.Dropdown style={neo.card}>
                          <Menu.Item leftSection={<IconFileText size={14} />}>
                            View Policy
                          </Menu.Item>
                          <Menu.Item leftSection={<IconEdit size={14} />}>
                            Edit Policy
                          </Menu.Item>
                          <Menu.Item leftSection={<IconUsers size={14} />}>
                            Assign Teams
                          </Menu.Item>
                          <Menu.Divider />
                          <Menu.Item
                            leftSection={<IconTrash size={14} />}
                            color="red"
                          >
                            Archive Policy
                          </Menu.Item>
                        </Menu.Dropdown>
                      </Menu>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Table.ScrollContainer>
        </Card>

        {/* Create Policy Modal */}
        <Modal
          opened={opened}
          onClose={() => setOpened(false)}
          title="Create New Policy"
          size="lg"
        >
          <Stack gap="md">
            <TextInput
              label="Policy Name"
              placeholder="Enter policy name"
              required
            />
            <Textarea
              label="Description"
              placeholder="Describe the policy purpose and scope"
              rows={3}
              required
            />
            <Select
              label="Category"
              placeholder="Select category"
              data={[
                { value: 'bias', label: 'Bias & Fairness' },
                { value: 'privacy', label: 'Privacy' },
                { value: 'documentation', label: 'Documentation' },
                { value: 'monitoring', label: 'Monitoring' },
                { value: 'security', label: 'Security' },
              ]}
              required
            />
            <Select
              label="Scope"
              placeholder="Select application scope"
              data={[
                { value: 'all', label: 'All Models' },
                { value: 'production', label: 'Production Models' },
                { value: 'training', label: 'Training Phase' },
                { value: 'data', label: 'Data Processing' },
              ]}
              required
            />
            <Group justify="flex-end" mt="md">
              <Button variant="light" onClick={() => setOpened(false)}>
                Cancel
              </Button>
              <Button>Create Policy</Button>
            </Group>
          </Stack>
        </Modal>
      </Stack>
    </Container>
  );
}