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
  Alert,
  Badge,
  ActionIcon,
  Tabs,
  Progress,
  List,
} from '@mantine/core';
import {
  IconLock,
  IconShield,
  IconAlertCircle,
  IconScan,
  IconRobot,
  IconBug,
  IconCheck,
  IconX,
  IconRefresh,
} from '@tabler/icons-react';
import { useApi } from '@/hooks/useApi';

const neo = {
  card: {
    background: 'linear-gradient(145deg, rgba(255, 255, 255, 0.95), rgba(248, 250, 252, 0.9))',
    backdropFilter: 'blur(20px)',
    border: '1px solid rgba(255, 255, 255, 0.3)',
    borderRadius: '20px',
    boxShadow: '12px 12px 24px rgba(163, 177, 198, 0.4), -12px -12px 24px rgba(255, 255, 255, 0.9)',
  },
};

const securityScans = [
  {
    id: 'container',
    name: 'Container Security',
    description: 'Scan Docker containers for vulnerabilities using Grype',
    icon: IconShield,
    status: 'completed',
    lastRun: '1 hour ago',
    vulnerabilities: { critical: 0, high: 2, medium: 5, low: 12 },
  },
  {
    id: 'llm',
    name: 'LLM Security Testing',
    description: 'Test LLMs for prompt injection and jailbreak attempts',
    icon: IconRobot,
    status: 'running',
    lastRun: 'Running now',
    vulnerabilities: null,
  },
  {
    id: 'model',
    name: 'Model Analysis',
    description: 'Analyze ML models for backdoors and adversarial robustness',
    icon: IconBug,
    status: 'pending',
    lastRun: 'Never',
    vulnerabilities: null,
  },
];

function getVulnerabilityColor(severity: string) {
  switch (severity) {
    case 'critical': return 'red';
    case 'high': return 'orange';
    case 'medium': return 'yellow';
    case 'low': return 'blue';
    default: return 'gray';
  }
}

export default function SecurityPage() {
  const { data: securityData, loading, error } = useApi('/api/v1/security/health');

  return (
    <Container size="xl" py="xl">
      <Stack gap="xl">
        {/* Header */}
        <Card style={neo.card} p="xl">
          <Group justify="space-between" align="center">
            <div>
              <Title order={1} size="2rem" fw={700} c="#1e293b" mb="xs">
                AI Security Center
              </Title>
              <Text c="dimmed" size="lg">
                Comprehensive security testing for AI systems and infrastructure
              </Text>
            </div>
            <Button
              size="lg"
              radius="xl"
              leftSection={<IconScan size={20} />}
              style={{
                background: 'linear-gradient(145deg, #dc2626, #b91c1c)',
                boxShadow: '6px 6px 12px rgba(220, 38, 38, 0.4), -4px -4px 8px rgba(248, 113, 113, 0.4)',
              }}
            >
              Run Full Security Scan
            </Button>
          </Group>
        </Card>

        {error && (
          <Alert
            icon={<IconAlertCircle size={16} />}
            color="red"
            title="Connection Error"
            style={neo.card}
          >
            Unable to connect to security service: {error?.message || 'Unknown error'}
          </Alert>
        )}

        {/* Security Overview */}
        <SimpleGrid cols={{ base: 1, md: 3 }} spacing="lg">
          {securityScans.map((scan) => (
            <Card
              key={scan.id}
              style={{
                ...neo.card,
                cursor: 'pointer',
                transition: 'all 0.3s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-4px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
              }}
              p="xl"
            >
              <Stack gap="md">
                <Group justify="space-between">
                  <Group gap="sm">
                    <ActionIcon
                      size="lg"
                      radius="xl"
                      variant="light"
                      color={scan.status === 'completed' ? 'green' : scan.status === 'running' ? 'blue' : 'gray'}
                    >
                      <scan.icon size={20} />
                    </ActionIcon>
                    <div>
                      <Title order={3} size="lg" fw={600}>
                        {scan.name}
                      </Title>
                      <Text size="sm" c="dimmed">
                        {scan.description}
                      </Text>
                    </div>
                  </Group>
                </Group>

                <Badge
                  color={scan.status === 'completed' ? 'green' : scan.status === 'running' ? 'blue' : 'gray'}
                  variant="light"
                  radius="xl"
                  size="sm"
                >
                  {scan.status}
                </Badge>

                {scan.vulnerabilities && (
                  <Stack gap="xs">
                    <Text size="sm" fw={500}>Vulnerabilities Found:</Text>
                    <Group gap="xs">
                      {Object.entries(scan.vulnerabilities).map(([severity, count]) => (
                        <Badge
                          key={severity}
                          color={getVulnerabilityColor(severity)}
                          variant="light"
                          size="xs"
                        >
                          {count} {severity}
                        </Badge>
                      ))}
                    </Group>
                  </Stack>
                )}

                <Group justify="space-between" mt="md">
                  <Text size="xs" c="dimmed">
                    Last run: {scan.lastRun}
                  </Text>
                  <ActionIcon
                    variant="light"
                    size="sm"
                    radius="xl"
                    color="blue"
                    disabled={scan.status === 'running'}
                  >
                    <IconRefresh size={16} />
                  </ActionIcon>
                </Group>
              </Stack>
            </Card>
          ))}
        </SimpleGrid>

        {/* Detailed Security Reports */}
        <Tabs defaultValue="overview" radius="lg">
          <Tabs.List>
            <Tabs.Tab value="overview">Overview</Tabs.Tab>
            <Tabs.Tab value="vulnerabilities">Vulnerabilities</Tabs.Tab>
            <Tabs.Tab value="recommendations">Recommendations</Tabs.Tab>
            <Tabs.Tab value="compliance">Compliance</Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="overview" pt="xl">
            <Card style={neo.card} p="xl">
              <Title order={3} mb="md">Security Score</Title>
              <Group gap="xl">
                <div style={{ flex: 1 }}>
                  <Text size="sm" mb="xs">Overall Security Score</Text>
                  <Progress value={78} size="xl" radius="xl" color="blue" />
                  <Text size="xs" c="dimmed" mt="xs">78/100 - Good security posture</Text>
                </div>
                <div style={{ flex: 1 }}>
                  <Text size="sm" mb="xs">Critical Issues</Text>
                  <Progress value={5} size="xl" radius="xl" color="red" />
                  <Text size="xs" c="dimmed" mt="xs">5 critical issues found</Text>
                </div>
              </Group>
            </Card>
          </Tabs.Panel>

          <Tabs.Panel value="vulnerabilities" pt="xl">
            <Card style={neo.card} p="xl">
              <Title order={3} mb="md">Recent Vulnerabilities</Title>
              <List spacing="md">
                <List.Item
                  icon={<IconAlertCircle color="red" size={16} />}
                >
                  <Group justify="space-between">
                    <div>
                      <Text fw={500}>CVE-2024-0001: Container privilege escalation</Text>
                      <Text size="sm" c="dimmed">Critical severity - requires immediate attention</Text>
                    </div>
                    <Badge color="red" size="sm">Critical</Badge>
                  </Group>
                </List.Item>
                <List.Item
                  icon={<IconAlertCircle color="orange" size={16} />}
                >
                  <Group justify="space-between">
                    <div>
                      <Text fw={500}>Prompt injection vulnerability detected</Text>
                      <Text size="sm" c="dimmed">LLM bypass attempt successful</Text>
                    </div>
                    <Badge color="orange" size="sm">High</Badge>
                  </Group>
                </List.Item>
              </List>
            </Card>
          </Tabs.Panel>

          <Tabs.Panel value="recommendations" pt="xl">
            <Card style={neo.card} p="xl">
              <Title order={3} mb="md">Security Recommendations</Title>
              <List spacing="md">
                <List.Item icon={<IconCheck color="green" size={16} />}>
                  Update container base images to latest secure versions
                </List.Item>
                <List.Item icon={<IconCheck color="green" size={16} />}>
                  Implement additional prompt injection safeguards
                </List.Item>
                <List.Item icon={<IconCheck color="green" size={16} />}>
                  Enable real-time vulnerability monitoring
                </List.Item>
              </List>
            </Card>
          </Tabs.Panel>

          <Tabs.Panel value="compliance" pt="xl">
            <Card style={neo.card} p="xl">
              <Title order={3} mb="md">Compliance Status</Title>
              <Stack gap="md">
                <Group justify="space-between">
                  <Text>SOC 2 Type II</Text>
                  <Badge color="green" leftSection={<IconCheck size={12} />}>Compliant</Badge>
                </Group>
                <Group justify="space-between">
                  <Text>ISO 27001</Text>
                  <Badge color="yellow" leftSection={<IconAlertCircle size={12} />}>Partial</Badge>
                </Group>
                <Group justify="space-between">
                  <Text>GDPR</Text>
                  <Badge color="green" leftSection={<IconCheck size={12} />}>Compliant</Badge>
                </Group>
              </Stack>
            </Card>
          </Tabs.Panel>
        </Tabs>
      </Stack>
    </Container>
  );
}