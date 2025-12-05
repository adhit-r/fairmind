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
    Paper,
    RingProgress,
    ThemeIcon,
    SimpleGrid,
    Timeline,
    Alert,
} from '@mantine/core';
import {
    IconShieldCheck,
    IconAlertTriangle,
    IconTrendingUp,
    IconTrendingDown,
    IconRefresh,
    IconDownload,
    IconScale,
    IconChecklist,
    IconClock,
    IconAlertCircle,
} from '@tabler/icons-react';

interface DashboardData {
    system_id: string;
    last_updated: string;
    compliance_overview: {
        overall_score: number;
        frameworks: Array<{
            name: string;
            status: string;
            score: number;
        }>;
    };
    risk_indicators: {
        high_priority_issues: number;
        open_recommendations: number;
    };
    trends: {
        compliance_trend: string;
        last_assessment_date: string;
    };
    key_metrics: {
        total_requirements: number;
        met_requirements: number;
    };
}

export default function StakeholderDashboardPage() {
    const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchDashboardData();
    }, []);

    const fetchDashboardData = async () => {
        setLoading(true);
        try {
            // Sample compliance results for dashboard
            const sampleComplianceResults = [
                {
                    framework: 'eu_ai_act',
                    compliance_score: 87.5,
                    overall_status: 'compliant',
                    total_requirements: 8,
                    compliant_requirements: 7,
                    recommendations: ['Address human oversight measures'],
                },
                {
                    framework: 'gdpr',
                    compliance_score: 92.0,
                    overall_status: 'compliant',
                    total_requirements: 5,
                    compliant_requirements: 5,
                    recommendations: [],
                },
                {
                    framework: 'iso_iec_42001',
                    compliance_score: 83.3,
                    overall_status: 'partially_compliant',
                    total_requirements: 3,
                    compliant_requirements: 2,
                    recommendations: ['Improve personnel competence documentation'],
                },
                {
                    framework: 'nist_ai_rmf',
                    compliance_score: 90.0,
                    overall_status: 'compliant',
                    total_requirements: 4,
                    compliant_requirements: 4,
                    recommendations: [],
                },
            ];

            const response = await fetch(
                'http://localhost:8000/api/v1/compliance/stakeholder-dashboard',
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        system_id: 'SYS-001',
                    }),
                }
            );

            const data = await response.json();
            setDashboardData(data);
        } catch (error) {
            console.error('Error fetching dashboard data:', error);
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

    const getTrendIcon = (trend: string) => {
        switch (trend) {
            case 'improving':
                return <IconTrendingUp size={20} />;
            case 'declining':
                return <IconTrendingDown size={20} />;
            default:
                return <IconClock size={20} />;
        }
    };

    const getTrendColor = (trend: string) => {
        switch (trend) {
            case 'improving':
                return 'green';
            case 'declining':
                return 'red';
            default:
                return 'gray';
        }
    };

    return (
        <Container size="xl" py="xl">
            <Stack gap="xl">
                {/* Header */}
                <div>
                    <Group justify="space-between" mb="md">
                        <div>
                            <Title order={1}>Stakeholder Dashboard</Title>
                            <Text c="dimmed" size="sm">
                                Executive overview of AI compliance and governance
                            </Text>
                        </div>
                        <Group>
                            <Button
                                leftSection={<IconRefresh size={16} />}
                                variant="light"
                                onClick={fetchDashboardData}
                                loading={loading}
                            >
                                Refresh
                            </Button>
                            <Button leftSection={<IconDownload size={16} />} variant="filled">
                                Export Report
                            </Button>
                        </Group>
                    </Group>
                </div>

                {dashboardData && (
                    <>
                        {/* Key Metrics */}
                        <Grid>
                            <Grid.Col span={{ base: 12, md: 3 }}>
                                <Card shadow="sm" padding="lg" radius="md" withBorder>
                                    <Stack gap="xs" align="center">
                                        <ThemeIcon
                                            variant="light"
                                            color={
                                                dashboardData.compliance_overview.overall_score >= 90
                                                    ? 'green'
                                                    : dashboardData.compliance_overview.overall_score >= 70
                                                        ? 'yellow'
                                                        : 'red'
                                            }
                                            size={60}
                                        >
                                            <IconShieldCheck size={32} />
                                        </ThemeIcon>
                                        <Text size="sm" c="dimmed" ta="center">
                                            Overall Compliance
                                        </Text>
                                        <RingProgress
                                            size={140}
                                            thickness={14}
                                            sections={[
                                                {
                                                    value: dashboardData.compliance_overview.overall_score,
                                                    color:
                                                        dashboardData.compliance_overview.overall_score >= 90
                                                            ? 'green'
                                                            : dashboardData.compliance_overview.overall_score >= 70
                                                                ? 'yellow'
                                                                : 'red',
                                                },
                                            ]}
                                            label={
                                                <Text ta="center" fw={700} size="xl">
                                                    {dashboardData.compliance_overview.overall_score.toFixed(0)}%
                                                </Text>
                                            }
                                        />
                                    </Stack>
                                </Card>
                            </Grid.Col>

                            <Grid.Col span={{ base: 12, md: 3 }}>
                                <Card shadow="sm" padding="lg" radius="md" withBorder>
                                    <Stack gap="md">
                                        <Group>
                                            <ThemeIcon variant="light" color="blue" size="lg">
                                                <IconChecklist size={24} />
                                            </ThemeIcon>
                                            <div>
                                                <Text size="xs" c="dimmed">
                                                    Requirements Met
                                                </Text>
                                                <Text size="xl" fw={700}>
                                                    {dashboardData.key_metrics.met_requirements} /{' '}
                                                    {dashboardData.key_metrics.total_requirements}
                                                </Text>
                                            </div>
                                        </Group>
                                        <Progress
                                            value={
                                                (dashboardData.key_metrics.met_requirements /
                                                    dashboardData.key_metrics.total_requirements) *
                                                100
                                            }
                                            color="blue"
                                            size="lg"
                                        />
                                        <Text size="xs" c="dimmed">
                                            {(
                                                (dashboardData.key_metrics.met_requirements /
                                                    dashboardData.key_metrics.total_requirements) *
                                                100
                                            ).toFixed(0)}
                                            % of all requirements
                                        </Text>
                                    </Stack>
                                </Card>
                            </Grid.Col>

                            <Grid.Col span={{ base: 12, md: 3 }}>
                                <Card shadow="sm" padding="lg" radius="md" withBorder>
                                    <Stack gap="md">
                                        <Group>
                                            <ThemeIcon variant="light" color="orange" size="lg">
                                                <IconAlertTriangle size={24} />
                                            </ThemeIcon>
                                            <div>
                                                <Text size="xs" c="dimmed">
                                                    High Priority Issues
                                                </Text>
                                                <Text size="xl" fw={700}>
                                                    {dashboardData.risk_indicators.high_priority_issues}
                                                </Text>
                                            </div>
                                        </Group>
                                        {dashboardData.risk_indicators.high_priority_issues > 0 ? (
                                            <Alert icon={<IconAlertCircle size={16} />} color="orange">
                                                Requires immediate attention
                                            </Alert>
                                        ) : (
                                            <Alert icon={<IconShieldCheck size={16} />} color="green">
                                                No critical issues
                                            </Alert>
                                        )}
                                    </Stack>
                                </Card>
                            </Grid.Col>

                            <Grid.Col span={{ base: 12, md: 3 }}>
                                <Card shadow="sm" padding="lg" radius="md" withBorder>
                                    <Stack gap="md">
                                        <Group>
                                            <ThemeIcon
                                                variant="light"
                                                color={getTrendColor(dashboardData.trends.compliance_trend)}
                                                size="lg"
                                            >
                                                {getTrendIcon(dashboardData.trends.compliance_trend)}
                                            </ThemeIcon>
                                            <div>
                                                <Text size="xs" c="dimmed">
                                                    Compliance Trend
                                                </Text>
                                                <Text size="lg" fw={700} tt="capitalize">
                                                    {dashboardData.trends.compliance_trend}
                                                </Text>
                                            </div>
                                        </Group>
                                        <Text size="xs" c="dimmed">
                                            Last assessed:{' '}
                                            {new Date(dashboardData.trends.last_assessment_date).toLocaleDateString()}
                                        </Text>
                                    </Stack>
                                </Card>
                            </Grid.Col>
                        </Grid>

                        {/* Framework Compliance */}
                        <Card shadow="sm" padding="lg" radius="md" withBorder>
                            <Group mb="md">
                                <ThemeIcon variant="light" size="lg" color="violet">
                                    <IconScale size={24} />
                                </ThemeIcon>
                                <Text fw={600} size="lg">
                                    Framework Compliance
                                </Text>
                            </Group>

                            <SimpleGrid cols={{ base: 1, md: 2 }} spacing="md">
                                {dashboardData.compliance_overview.frameworks.map((framework, index) => (
                                    <Paper key={index} p="md" withBorder>
                                        <Group justify="space-between" mb="xs">
                                            <Text fw={600}>{framework.name.replace('_', ' ').toUpperCase()}</Text>
                                            <Badge color={getStatusColor(framework.status)}>
                                                {framework.status.replace('_', ' ')}
                                            </Badge>
                                        </Group>
                                        <Group justify="space-between" mb="xs">
                                            <Text size="sm" c="dimmed">
                                                Compliance Score
                                            </Text>
                                            <Text fw={700} size="lg">
                                                {framework.score.toFixed(0)}%
                                            </Text>
                                        </Group>
                                        <Progress
                                            value={framework.score}
                                            color={getStatusColor(framework.status)}
                                            size="md"
                                        />
                                    </Paper>
                                ))}
                            </SimpleGrid>
                        </Card>

                        {/* Action Items */}
                        <Card shadow="sm" padding="lg" radius="md" withBorder>
                            <Group mb="md">
                                <ThemeIcon variant="light" size="lg" color="orange">
                                    <IconAlertTriangle size={24} />
                                </ThemeIcon>
                                <div>
                                    <Text fw={600} size="lg">
                                        Action Items
                                    </Text>
                                    <Text size="sm" c="dimmed">
                                        {dashboardData.risk_indicators.open_recommendations} open recommendations
                                    </Text>
                                </div>
                            </Group>

                            <Timeline active={-1} bulletSize={24} lineWidth={2}>
                                <Timeline.Item
                                    bullet={<IconAlertTriangle size={12} />}
                                    title="High Priority"
                                    color="red"
                                >
                                    <Text c="dimmed" size="sm">
                                        {dashboardData.risk_indicators.high_priority_issues} critical issues
                                        requiring immediate attention
                                    </Text>
                                    <Text size="xs" mt={4} c="dimmed">
                                        Review and address within 7 days
                                    </Text>
                                </Timeline.Item>

                                <Timeline.Item
                                    bullet={<IconClock size={12} />}
                                    title="Medium Priority"
                                    color="yellow"
                                >
                                    <Text c="dimmed" size="sm">
                                        {Math.max(
                                            0,
                                            dashboardData.risk_indicators.open_recommendations -
                                            dashboardData.risk_indicators.high_priority_issues
                                        )}{' '}
                                        recommendations for improvement
                                    </Text>
                                    <Text size="xs" mt={4} c="dimmed">
                                        Address within 30 days
                                    </Text>
                                </Timeline.Item>

                                <Timeline.Item
                                    bullet={<IconShieldCheck size={12} />}
                                    title="Monitoring"
                                    color="green"
                                >
                                    <Text c="dimmed" size="sm">
                                        Continue monitoring compliant frameworks
                                    </Text>
                                    <Text size="xs" mt={4} c="dimmed">
                                        Next review:{' '}
                                        {new Date(
                                            new Date(dashboardData.last_updated).getTime() + 180 * 24 * 60 * 60 * 1000
                                        ).toLocaleDateString()}
                                    </Text>
                                </Timeline.Item>
                            </Timeline>
                        </Card>

                        {/* Executive Summary */}
                        <Card shadow="sm" padding="lg" radius="md" withBorder>
                            <Text fw={600} size="lg" mb="md">
                                Executive Summary
                            </Text>
                            <Stack gap="md">
                                <Paper p="md" withBorder>
                                    <Text size="sm">
                                        Your AI system demonstrates{' '}
                                        <Text span fw={700}>
                                            {dashboardData.compliance_overview.overall_score >= 90
                                                ? 'strong'
                                                : dashboardData.compliance_overview.overall_score >= 70
                                                    ? 'good'
                                                    : 'developing'}{' '}
                                            compliance
                                        </Text>{' '}
                                        across {dashboardData.compliance_overview.frameworks.length} regulatory
                                        frameworks with an overall score of{' '}
                                        <Text span fw={700}>
                                            {dashboardData.compliance_overview.overall_score.toFixed(1)}%
                                        </Text>
                                        .
                                    </Text>
                                </Paper>

                                <Paper p="md" withBorder>
                                    <Text size="sm">
                                        <Text span fw={700}>
                                            {dashboardData.key_metrics.met_requirements}
                                        </Text>{' '}
                                        out of{' '}
                                        <Text span fw={700}>
                                            {dashboardData.key_metrics.total_requirements}
                                        </Text>{' '}
                                        requirements have been met. The compliance trend is{' '}
                                        <Text
                                            span
                                            fw={700}
                                            c={getTrendColor(dashboardData.trends.compliance_trend)}
                                        >
                                            {dashboardData.trends.compliance_trend}
                                        </Text>
                                        .
                                    </Text>
                                </Paper>

                                {dashboardData.risk_indicators.high_priority_issues > 0 && (
                                    <Alert icon={<IconAlertTriangle size={16} />} color="orange">
                                        <Text size="sm">
                                            There are{' '}
                                            <Text span fw={700}>
                                                {dashboardData.risk_indicators.high_priority_issues}
                                            </Text>{' '}
                                            high-priority issues that require immediate attention to maintain
                                            compliance.
                                        </Text>
                                    </Alert>
                                )}

                                {dashboardData.risk_indicators.high_priority_issues === 0 && (
                                    <Alert icon={<IconShieldCheck size={16} />} color="green">
                                        <Text size="sm">
                                            No critical compliance issues detected. Continue monitoring and
                                            maintaining current practices.
                                        </Text>
                                    </Alert>
                                )}
                            </Stack>
                        </Card>

                        {/* Last Updated */}
                        <Paper p="md" withBorder>
                            <Group justify="space-between">
                                <Text size="sm" c="dimmed">
                                    Last updated: {new Date(dashboardData.last_updated).toLocaleString()}
                                </Text>
                                <Text size="sm" c="dimmed">
                                    System ID: {dashboardData.system_id}
                                </Text>
                            </Group>
                        </Paper>
                    </>
                )}
            </Stack>
        </Container>
    );
}
