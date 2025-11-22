'use client';

import { useState, useEffect } from 'react';
import {
    Container,
    Title,
    Text,
    Card,
    Grid,
    Badge,
    Progress,
    Stack,
    Group,
    Button,
    Select,
    Paper,
    Tabs,
    Table,
    ActionIcon,
    Tooltip,
    RingProgress,
    ThemeIcon,
} from '@mantine/core';
import {
    IconShieldCheck,
    IconAlertTriangle,
    IconFileText,
    IconDownload,
    IconRefresh,
    IconChecklist,
    IconScale,
    IconBook,
} from '@tabler/icons-react';

interface Framework {
    id: string;
    name: string;
    description: string;
    region: string;
    status: string;
}

interface ComplianceResult {
    framework: string;
    compliance_score: number;
    overall_status: string;
    total_requirements: number;
    compliant_requirements: number;
    results: Array<{
        requirement_id: string;
        category: string;
        requirement: string;
        status: string;
        gaps: string[];
    }>;
}

export default function ComplianceDashboardPage() {
    const [frameworks, setFrameworks] = useState<Framework[]>([]);
    const [selectedFramework, setSelectedFramework] = useState<string>('');
    const [complianceResults, setComplianceResults] = useState<ComplianceResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [activeTab, setActiveTab] = useState<string | null>('overview');

    useEffect(() => {
        fetchFrameworks();
    }, []);

    const fetchFrameworks = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/v1/compliance/frameworks');
            const data = await response.json();
            setFrameworks(data.frameworks || []);
            if (data.frameworks && data.frameworks.length > 0) {
                setSelectedFramework(data.frameworks[0].id);
            }
        } catch (error) {
            console.error('Error fetching frameworks:', error);
        }
    };

    const checkCompliance = async () => {
        if (!selectedFramework) return;

        setLoading(true);
        try {
            // Sample system data - in production, this would come from your actual system
            const systemData = {
                name: 'Sample AI System',
                description: 'AI-powered recommendation system',
                risk_level: 'high',
                evidence_EU_AI_1: [{ quality: 0.9, description: 'Risk classification completed' }],
                evidence_EU_AI_2: [{ quality: 0.85, description: 'Transparency measures implemented' }],
                evidence_EU_AI_3: [{ quality: 0.8, description: 'Human oversight in place' }],
                evidence_EU_AI_4: [{ quality: 0.9, description: 'Data governance established' }],
                evidence_EU_AI_5: [{ quality: 0.95, description: 'Technical documentation maintained' }],
                evidence_EU_AI_6: [{ quality: 0.88, description: 'Logging system active' }],
                evidence_EU_AI_7: [{ quality: 0.82, description: 'Accuracy monitoring in place' }],
                evidence_GDPR_1: [{ quality: 0.9, description: 'Legal basis established' }],
                evidence_GDPR_2: [{ quality: 0.85, description: 'Data minimization applied' }],
                evidence_GDPR_3: [{ quality: 0.8, description: 'Automated decision safeguards' }],
                evidence_GDPR_4: [{ quality: 0.9, description: 'DPIA conducted' }],
                evidence_ISO_1: [{ quality: 0.85, description: 'AI management system established' }],
                evidence_ISO_2: [{ quality: 0.88, description: 'Risk management implemented' }],
                evidence_NIST_1: [{ quality: 0.9, description: 'Governance structure in place' }],
                evidence_NIST_2: [{ quality: 0.85, description: 'Risk mapping completed' }],
                evidence_NIST_3: [{ quality: 0.87, description: 'Performance measurement active' }],
                evidence_IEEE_1: [{ quality: 0.83, description: 'Value-based design applied' }],
            };

            const response = await fetch('http://localhost:8000/api/v1/compliance/check', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    framework: selectedFramework,
                    system_data: systemData,
                }),
            });

            const data = await response.json();
            setComplianceResults(data);
        } catch (error) {
            console.error('Error checking compliance:', error);
        } finally {
            setLoading(false);
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'compliant':
                return 'green';
            case 'partially_compliant':
                return 'yellow';
            case 'non_compliant':
                return 'red';
            default:
                return 'gray';
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'compliant':
                return <IconShieldCheck size={20} />;
            case 'partially_compliant':
                return <IconAlertTriangle size={20} />;
            case 'non_compliant':
                return <IconAlertTriangle size={20} />;
            default:
                return <IconFileText size={20} />;
        }
    };

    return (
        <Container size="xl" py="xl">
            <Stack gap="xl">
                {/* Header */}
                <div>
                    <Group justify="space-between" mb="md">
                        <div>
                            <Title order={1}>Compliance Dashboard</Title>
                            <Text c="dimmed" size="sm">
                                Regulatory compliance checks and audit reporting
                            </Text>
                        </div>
                        <Group>
                            <Button
                                leftSection={<IconRefresh size={16} />}
                                variant="light"
                                onClick={fetchFrameworks}
                            >
                                Refresh
                            </Button>
                            <Button
                                leftSection={<IconDownload size={16} />}
                                variant="filled"
                                disabled={!complianceResults}
                            >
                                Export Report
                            </Button>
                        </Group>
                    </Group>
                </div>

                {/* Framework Selection */}
                <Card shadow="sm" padding="lg" radius="md" withBorder>
                    <Stack gap="md">
                        <Group justify="space-between">
                            <div>
                                <Text fw={600} size="lg">
                                    Select Regulatory Framework
                                </Text>
                                <Text size="sm" c="dimmed">
                                    Choose a framework to check compliance against
                                </Text>
                            </div>
                        </Group>

                        <Grid>
                            <Grid.Col span={{ base: 12, md: 8 }}>
                                <Select
                                    label="Framework"
                                    placeholder="Select a regulatory framework"
                                    value={selectedFramework}
                                    onChange={(value) => setSelectedFramework(value || '')}
                                    data={frameworks.map((f) => ({
                                        value: f.id,
                                        label: `${f.name} - ${f.description}`,
                                    }))}
                                />
                            </Grid.Col>
                            <Grid.Col span={{ base: 12, md: 4 }}>
                                <Button
                                    fullWidth
                                    size="md"
                                    mt={24}
                                    onClick={checkCompliance}
                                    loading={loading}
                                    disabled={!selectedFramework}
                                    leftSection={<IconChecklist size={16} />}
                                >
                                    Check Compliance
                                </Button>
                            </Grid.Col>
                        </Grid>
                    </Stack>
                </Card>

                {/* Results */}
                {complianceResults && (
                    <>
                        {/* Overview Cards */}
                        <Grid>
                            <Grid.Col span={{ base: 12, md: 3 }}>
                                <Card shadow="sm" padding="lg" radius="md" withBorder>
                                    <Stack gap="xs">
                                        <Group justify="space-between">
                                            <Text size="sm" c="dimmed">
                                                Overall Score
                                            </Text>
                                            <ThemeIcon
                                                variant="light"
                                                color={getStatusColor(complianceResults.overall_status)}
                                                size="lg"
                                            >
                                                {getStatusIcon(complianceResults.overall_status)}
                                            </ThemeIcon>
                                        </Group>
                                        <RingProgress
                                            size={120}
                                            thickness={12}
                                            sections={[
                                                {
                                                    value: complianceResults.compliance_score,
                                                    color: getStatusColor(complianceResults.overall_status),
                                                },
                                            ]}
                                            label={
                                                <Text ta="center" fw={700} size="xl">
                                                    {complianceResults.compliance_score.toFixed(0)}%
                                                </Text>
                                            }
                                        />
                                    </Stack>
                                </Card>
                            </Grid.Col>

                            <Grid.Col span={{ base: 12, md: 3 }}>
                                <Card shadow="sm" padding="lg" radius="md" withBorder>
                                    <Stack gap="xs">
                                        <Text size="sm" c="dimmed">
                                            Status
                                        </Text>
                                        <Badge
                                            size="xl"
                                            variant="filled"
                                            color={getStatusColor(complianceResults.overall_status)}
                                        >
                                            {complianceResults.overall_status.replace('_', ' ').toUpperCase()}
                                        </Badge>
                                        <Text size="xs" c="dimmed" mt="md">
                                            Framework: {complianceResults.framework}
                                        </Text>
                                    </Stack>
                                </Card>
                            </Grid.Col>

                            <Grid.Col span={{ base: 12, md: 3 }}>
                                <Card shadow="sm" padding="lg" radius="md" withBorder>
                                    <Stack gap="xs">
                                        <Text size="sm" c="dimmed">
                                            Requirements Met
                                        </Text>
                                        <Text size="xl" fw={700}>
                                            {complianceResults.compliant_requirements} /{' '}
                                            {complianceResults.total_requirements}
                                        </Text>
                                        <Progress
                                            value={
                                                (complianceResults.compliant_requirements /
                                                    complianceResults.total_requirements) *
                                                100
                                            }
                                            color={getStatusColor(complianceResults.overall_status)}
                                            size="md"
                                            mt="xs"
                                        />
                                    </Stack>
                                </Card>
                            </Grid.Col>

                            <Grid.Col span={{ base: 12, md: 3 }}>
                                <Card shadow="sm" padding="lg" radius="md" withBorder>
                                    <Stack gap="xs">
                                        <Text size="sm" c="dimmed">
                                            Total Requirements
                                        </Text>
                                        <Text size="xl" fw={700}>
                                            {complianceResults.total_requirements}
                                        </Text>
                                        <Text size="xs" c="dimmed" mt="md">
                                            Assessed requirements
                                        </Text>
                                    </Stack>
                                </Card>
                            </Grid.Col>
                        </Grid>

                        {/* Detailed Results */}
                        <Card shadow="sm" padding="lg" radius="md" withBorder>
                            <Tabs value={activeTab} onChange={setActiveTab}>
                                <Tabs.List>
                                    <Tabs.Tab value="overview" leftSection={<IconScale size={16} />}>
                                        Overview
                                    </Tabs.Tab>
                                    <Tabs.Tab value="requirements" leftSection={<IconChecklist size={16} />}>
                                        Requirements
                                    </Tabs.Tab>
                                    <Tabs.Tab value="recommendations" leftSection={<IconBook size={16} />}>
                                        Recommendations
                                    </Tabs.Tab>
                                </Tabs.List>

                                <Tabs.Panel value="overview" pt="md">
                                    <Stack gap="md">
                                        <Text size="lg" fw={600}>
                                            Compliance Overview
                                        </Text>
                                        <Text>
                                            Your system has been assessed against the {complianceResults.framework}{' '}
                                            framework. The overall compliance score is{' '}
                                            {complianceResults.compliance_score.toFixed(1)}%.
                                        </Text>
                                        <Grid>
                                            {complianceResults.results.map((result, index) => (
                                                <Grid.Col key={index} span={{ base: 12, md: 6 }}>
                                                    <Paper p="md" withBorder>
                                                        <Group justify="space-between" mb="xs">
                                                            <Text fw={600} size="sm">
                                                                {result.category}
                                                            </Text>
                                                            <Badge color={getStatusColor(result.status)} size="sm">
                                                                {result.status.replace('_', ' ')}
                                                            </Badge>
                                                        </Group>
                                                        <Text size="xs" c="dimmed">
                                                            {result.requirement}
                                                        </Text>
                                                    </Paper>
                                                </Grid.Col>
                                            ))}
                                        </Grid>
                                    </Stack>
                                </Tabs.Panel>

                                <Tabs.Panel value="requirements" pt="md">
                                    <Table striped highlightOnHover>
                                        <Table.Thead>
                                            <Table.Tr>
                                                <Table.Th>ID</Table.Th>
                                                <Table.Th>Category</Table.Th>
                                                <Table.Th>Requirement</Table.Th>
                                                <Table.Th>Status</Table.Th>
                                                <Table.Th>Gaps</Table.Th>
                                            </Table.Tr>
                                        </Table.Thead>
                                        <Table.Tbody>
                                            {complianceResults.results.map((result, index) => (
                                                <Table.Tr key={index}>
                                                    <Table.Td>
                                                        <Text size="sm" fw={600}>
                                                            {result.requirement_id}
                                                        </Text>
                                                    </Table.Td>
                                                    <Table.Td>
                                                        <Text size="sm">{result.category}</Text>
                                                    </Table.Td>
                                                    <Table.Td>
                                                        <Text size="sm">{result.requirement}</Text>
                                                    </Table.Td>
                                                    <Table.Td>
                                                        <Badge color={getStatusColor(result.status)} size="sm">
                                                            {result.status.replace('_', ' ')}
                                                        </Badge>
                                                    </Table.Td>
                                                    <Table.Td>
                                                        {result.gaps.length > 0 ? (
                                                            <Tooltip label={result.gaps.join(', ')}>
                                                                <Badge color="red" size="sm">
                                                                    {result.gaps.length} gap(s)
                                                                </Badge>
                                                            </Tooltip>
                                                        ) : (
                                                            <Badge color="green" size="sm">
                                                                No gaps
                                                            </Badge>
                                                        )}
                                                    </Table.Td>
                                                </Table.Tr>
                                            ))}
                                        </Table.Tbody>
                                    </Table>
                                </Tabs.Panel>

                                <Tabs.Panel value="recommendations" pt="md">
                                    <Stack gap="md">
                                        <Text size="lg" fw={600}>
                                            Recommendations
                                        </Text>
                                        {complianceResults.results
                                            .filter((r) => r.status !== 'compliant')
                                            .map((result, index) => (
                                                <Paper key={index} p="md" withBorder>
                                                    <Group justify="space-between" mb="xs">
                                                        <Text fw={600}>{result.category}</Text>
                                                        <Badge color="orange">Action Required</Badge>
                                                    </Group>
                                                    <Text size="sm" mb="xs">
                                                        {result.requirement}
                                                    </Text>
                                                    {result.gaps.map((gap, gapIndex) => (
                                                        <Text key={gapIndex} size="xs" c="dimmed">
                                                            • {gap}
                                                        </Text>
                                                    ))}
                                                </Paper>
                                            ))}
                                        {complianceResults.results.filter((r) => r.status !== 'compliant')
                                            .length === 0 && (
                                                <Paper p="md" withBorder>
                                                    <Text ta="center" c="dimmed">
                                                        No recommendations - all requirements are met!
                                                    </Text>
                                                </Paper>
                                            )}
                                    </Stack>
                                </Tabs.Panel>
                            </Tabs>
                        </Card>
                    </>
                )}
            </Stack>
        </Container>
    );
}
