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
  Timeline,
  ThemeIcon,
  ActionIcon,
} from '@mantine/core';
import {
  IconGitBranch,
  IconHistory,
  IconDownload,
  IconEye,
  IconCode,
  IconDatabase,
  IconServer,
  IconFileText,
  IconUsers,
  IconCalendar,
} from '@tabler/icons-react';
import { useApi } from '@/hooks/useApi';

const neo = {
  card: {
    background: 'rgba(255, 255, 255, 0.9)',
    backdropFilter: 'blur(20px)',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '20px',
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
  },
};

const modelLineage = [
  {
    id: 1,
    modelName: 'Credit Risk Model v3.2',
    version: '3.2.0',
    parentVersion: '3.1.4',
    created: '2024-01-20',
    creator: 'Sarah Chen',
    changes: 'Updated feature engineering pipeline, improved accuracy by 2.3%',
    dataSource: 'Customer Data Warehouse v2.1',
    framework: 'TensorFlow 2.14',
    status: 'active',
  },
  {
    id: 2,
    modelName: 'Credit Risk Model v3.1',
    version: '3.1.4',
    parentVersion: '3.0.2',
    created: '2024-01-15',
    creator: 'Mike Rodriguez',
    changes: 'Added new risk indicators, bias reduction improvements',
    dataSource: 'Customer Data Warehouse v2.0',
    framework: 'TensorFlow 2.13',
    status: 'deprecated',
  },
  {
    id: 3,
    modelName: 'Credit Risk Model v3.0',
    version: '3.0.2',
    parentVersion: '2.8.1',
    created: '2024-01-10',
    creator: 'Alex Kim',
    changes: 'Major architecture upgrade, moved to ensemble methods',
    dataSource: 'Customer Data Warehouse v1.9',
    framework: 'TensorFlow 2.12',
    status: 'archived',
  },
];

const provenanceStats = [
  {
    title: 'Tracked Models',
    value: '247',
    icon: IconGitBranch,
    color: 'blue',
  },
  {
    title: 'Version History',
    value: '1,456',
    icon: IconHistory,
    color: 'green',
  },
  {
    title: 'Data Sources',
    value: '89',
    icon: IconDatabase,
    color: 'violet',
  },
  {
    title: 'Contributors',
    value: '23',
    icon: IconUsers,
    color: 'orange',
  },
];

export default function ProvenancePage() {
  const { data: provenanceData, loading, error } = useApi('/api/v1/provenance');

  return (
    <Container size="xl" py="xl">
      <Stack gap="xl">
        {/* Header */}
        <Card style={neo.card} p="xl">
          <Group justify="space-between" align="center">
            <div>
              <Title order={1} size="2rem" fw={700} c="#1e293b" mb="xs">
                Model Provenance & Lineage
              </Title>
              <Text c="dimmed" size="lg">
                Track model evolution, data lineage, and version history
              </Text>
            </div>
            <Button
              size="lg"
              radius="xl"
              leftSection={<IconDownload size={20} />}
              style={{
                background: 'linear-gradient(145deg, #7c3aed, #6d28d9)',
                boxShadow: '6px 6px 12px rgba(124, 58, 237, 0.4), -4px -4px 8px rgba(139, 92, 246, 0.4)',
              }}
            >
              Export Lineage
            </Button>
          </Group>
        </Card>

        {/* Statistics */}
        <SimpleGrid cols={{ base: 2, md: 4 }} spacing="lg">
          {provenanceStats.map((stat) => (
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

        {/* Model Lineage Timeline */}
        <Card style={neo.card} p="xl">
          <Group justify="space-between" align="center" mb="lg">
            <Title order={3} size="lg" fw={600}>
              Model Evolution Timeline
            </Title>
            <ActionIcon variant="light" radius="xl">
              <IconEye size={16} />
            </ActionIcon>
          </Group>

          <Timeline active={0} bulletSize={24} lineWidth={2}>
            {modelLineage.map((version, index) => (
              <Timeline.Item
                key={version.id}
                bullet={<IconGitBranch size={12} />}
                title={
                  <Group justify="space-between" align="center">
                    <Text fw={600} size="md">
                      {version.modelName}
                    </Text>
                    <Badge
                      size="sm"
                      radius="xl"
                      color={
                        version.status === 'active' ? 'green' :
                        version.status === 'deprecated' ? 'yellow' : 'gray'
                      }
                      variant="light"
                    >
                      {version.status}
                    </Badge>
                  </Group>
                }
              >
                <Stack gap="xs" mt="xs">
                  <Text size="sm" c="dimmed">
                    {version.changes}
                  </Text>
                  
                  <Group gap="lg">
                    <Group gap="xs" align="center">
                      <IconCode size={14} color="#6b7280" />
                      <Text size="xs" c="dimmed">
                        v{version.version}
                      </Text>
                    </Group>
                    <Group gap="xs" align="center">
                      <IconUsers size={14} color="#6b7280" />
                      <Text size="xs" c="dimmed">
                        {version.creator}
                      </Text>
                    </Group>
                    <Group gap="xs" align="center">
                      <IconCalendar size={14} color="#6b7280" />
                      <Text size="xs" c="dimmed">
                        {new Date(version.created).toLocaleDateString()}
                      </Text>
                    </Group>
                  </Group>

                  <Group gap="sm" mt="sm">
                    <Badge size="xs" variant="light" color="blue">
                      {version.framework}
                    </Badge>
                    <Badge size="xs" variant="light" color="cyan">
                      {version.dataSource}
                    </Badge>
                  </Group>
                </Stack>
              </Timeline.Item>
            ))}
          </Timeline>
        </Card>

        {/* Data Lineage Visualization */}
        <SimpleGrid cols={{ base: 1, lg: 2 }} spacing="lg">
          <Card style={neo.card} p="xl">
            <Stack align="center" gap="md" py="xl">
              <IconDatabase size={64} color="#cbd5e1" />
              <Title order={3} c="dimmed">Data Lineage Graph</Title>
              <Text c="dimmed" ta="center">
                Interactive visualization of data flow and transformations
              </Text>
              <Button leftSection={<IconEye size={16} />}>
                View Data Flow
              </Button>
            </Stack>
          </Card>

          <Card style={neo.card} p="xl">
            <Stack align="center" gap="md" py="xl">
              <IconFileText size={64} color="#cbd5e1" />
              <Title order={3} c="dimmed">Compliance Reports</Title>
              <Text c="dimmed" ta="center">
                Generate provenance reports for audit and compliance
              </Text>
              <Button leftSection={<IconDownload size={16} />}>
                Generate Report
              </Button>
            </Stack>
          </Card>
        </SimpleGrid>
      </Stack>
    </Container>
  );
}