'use client';

import { useState } from 'react';
import {
    Container,
    Title,
    Text,
    Card,
    Grid,
    Badge,
    Stack,
    Group,
    Button,
    TextInput,
    Textarea,
    Select,
    Paper,
    List,
    ThemeIcon,
    Alert,
    Loader,
    Divider,
    Code,
} from '@mantine/core';
import {
    IconFileText,
    IconDownload,
    IconScale,
    IconShieldCheck,
    IconAlertTriangle,
    IconCheck,
    IconEye,
    IconUsers,
    IconChartBar,
} from '@tabler/icons-react';

interface FairnessDocumentation {
    document_id: string;
    generated_date: string;
    model_info: {
        name: string;
        version: string;
        type: string;
        purpose: string;
    };
    fairness_assessment: {
        metrics_evaluated: string[];
        protected_attributes: string[];
        fairness_scores: Record<string, number>;
        bias_detected: boolean;
    };
    mitigation_strategies: Array<{
        strategy: string;
        description: string;
        priority: string;
    }>;
    monitoring_plan: {
        frequency: string;
        metrics_to_track: string[];
        alert_thresholds: Record<string, number>;
        review_process: string;
    };
    stakeholder_communication: {
        target_audiences: string[];
        key_messages: string[];
        transparency_measures: string[];
    };
}

export default function FairnessDocumentationPage() {
    const [modelName, setModelName] = useState('');
    const [modelVersion, setModelVersion] = useState('');
    const [modelType, setModelType] = useState('');
    const [modelPurpose, setModelPurpose] = useState('');
    const [protectedAttributes, setProtectedAttributes] = useState('');
    const [documentation, setDocumentation] = useState<FairnessDocumentation | null>(null);
    const [loading, setLoading] = useState(false);

    const modelTypes = [
        { value: 'classification', label: 'Classification' },
        { value: 'regression', label: 'Regression' },
        { value: 'llm', label: 'Large Language Model' },
        { value: 'recommendation', label: 'Recommendation System' },
        { value: 'computer_vision', label: 'Computer Vision' },
    ];

    const generateDocumentation = async () => {
        if (!modelName) {
            alert('Please enter a model name');
            return;
        }

        setLoading(true);
        try {
            const modelData = {
                name: modelName,
                version: modelVersion || '1.0',
                type: modelType || 'classification',
                purpose: modelPurpose,
            };

            // Sample bias test results
            const biasTestResults = {
                metrics: [
                    'Statistical Parity',
                    'Equal Opportunity',
                    'Predictive Parity',
                    'Calibration',
                ],
                protected_attributes: protectedAttributes
                    .split(',')
                    .map((a) => a.trim())
                    .filter((a) => a.length > 0) || ['gender', 'race', 'age'],
                scores: {
                    statistical_parity: 0.85,
                    equal_opportunity: 0.82,
                    predictive_parity: 0.88,
                    calibration: 0.90,
                },
                bias_detected: true,
            };

            const response = await fetch(
                'http://localhost:8000/api/v1/compliance/fairness-documentation',
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        model_data: modelData,
                        bias_test_results: biasTestResults,
                    }),
                }
            );

            const data = await response.json();
            setDocumentation(data);
        } catch (error) {
            console.error('Error generating documentation:', error);
            alert('Error generating documentation');
        } finally {
            setLoading(false);
        }
    };

    const downloadDocumentation = () => {
        if (!documentation) return;

        const docText = `
FAIRNESS DOCUMENTATION
======================

Document ID: ${documentation.document_id}
Generated: ${new Date(documentation.generated_date).toLocaleDateString()}

MODEL INFORMATION
-----------------
Name: ${documentation.model_info.name}
Version: ${documentation.model_info.version}
Type: ${documentation.model_info.type}
Purpose: ${documentation.model_info.purpose}

FAIRNESS ASSESSMENT
-------------------
Metrics Evaluated:
${documentation.fairness_assessment.metrics_evaluated.map((m) => `- ${m}`).join('\n')}

Protected Attributes:
${documentation.fairness_assessment.protected_attributes.map((a) => `- ${a}`).join('\n')}

Fairness Scores:
${Object.entries(documentation.fairness_assessment.fairness_scores)
                .map(([key, value]) => `- ${key}: ${value}`)
                .join('\n')}

Bias Detected: ${documentation.fairness_assessment.bias_detected ? 'Yes' : 'No'}

MITIGATION STRATEGIES
---------------------
${documentation.mitigation_strategies
                .map(
                    (s) => `
[${s.priority.toUpperCase()}] ${s.strategy}
${s.description}
`
                )
                .join('\n')}

MONITORING PLAN
---------------
Frequency: ${documentation.monitoring_plan.frequency}
Metrics to Track:
${documentation.monitoring_plan.metrics_to_track.map((m) => `- ${m}`).join('\n')}

Alert Thresholds:
${Object.entries(documentation.monitoring_plan.alert_thresholds)
                .map(([key, value]) => `- ${key}: ${value}`)
                .join('\n')}

Review Process: ${documentation.monitoring_plan.review_process}

STAKEHOLDER COMMUNICATION
-------------------------
Target Audiences:
${documentation.stakeholder_communication.target_audiences.map((a) => `- ${a}`).join('\n')}

Key Messages:
${documentation.stakeholder_communication.key_messages.map((m) => `- ${m}`).join('\n')}

Transparency Measures:
${documentation.stakeholder_communication.transparency_measures.map((m) => `- ${m}`).join('\n')}
    `;

        const blob = new Blob([docText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `fairness-documentation-${documentation.document_id}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    const getPriorityColor = (priority: string) => {
        switch (priority) {
            case 'high':
                return 'red';
            case 'medium':
                return 'yellow';
            case 'low':
                return 'blue';
            default:
                return 'gray';
        }
    };

    return (
        <Container size="xl" py="xl">
            <Stack gap="xl">
                {/* Header */}
                <div>
                    <Title order={1}>Fairness Documentation Generator</Title>
                    <Text c="dimmed" size="sm">
                        Generate comprehensive fairness documentation for your AI models
                    </Text>
                </div>

                {/* Generation Form */}
                <Card shadow="sm" padding="lg" radius="md" withBorder>
                    <Stack gap="md">
                        <Text fw={600} size="lg">
                            Model Information
                        </Text>

                        <Grid>
                            <Grid.Col span={{ base: 12, md: 6 }}>
                                <TextInput
                                    label="Model Name"
                                    placeholder="e.g., Credit Scoring Model"
                                    value={modelName}
                                    onChange={(e) => setModelName(e.currentTarget.value)}
                                    required
                                />
                            </Grid.Col>
                            <Grid.Col span={{ base: 12, md: 6 }}>
                                <TextInput
                                    label="Model Version"
                                    placeholder="e.g., 1.0"
                                    value={modelVersion}
                                    onChange={(e) => setModelVersion(e.currentTarget.value)}
                                />
                            </Grid.Col>
                            <Grid.Col span={{ base: 12, md: 6 }}>
                                <Select
                                    label="Model Type"
                                    placeholder="Select model type"
                                    value={modelType}
                                    onChange={(value) => setModelType(value || '')}
                                    data={modelTypes}
                                />
                            </Grid.Col>
                            <Grid.Col span={{ base: 12, md: 6 }}>
                                <TextInput
                                    label="Protected Attributes"
                                    placeholder="e.g., gender, race, age (comma-separated)"
                                    value={protectedAttributes}
                                    onChange={(e) => setProtectedAttributes(e.currentTarget.value)}
                                />
                            </Grid.Col>
                            <Grid.Col span={12}>
                                <Textarea
                                    label="Model Purpose"
                                    placeholder="Describe the purpose and use case of this model..."
                                    value={modelPurpose}
                                    onChange={(e) => setModelPurpose(e.currentTarget.value)}
                                    minRows={3}
                                />
                            </Grid.Col>
                        </Grid>

                        <Button
                            leftSection={<IconFileText size={16} />}
                            onClick={generateDocumentation}
                            loading={loading}
                            size="md"
                        >
                            Generate Documentation
                        </Button>
                    </Stack>
                </Card>

                {/* Loading State */}
                {loading && (
                    <Card shadow="sm" padding="lg" radius="md" withBorder>
                        <Stack align="center" gap="md">
                            <Loader size="lg" />
                            <Text>Generating fairness documentation...</Text>
                        </Stack>
                    </Card>
                )}

                {/* Documentation */}
                {documentation && !loading && (
                    <>
                        {/* Header */}
                        <Card shadow="sm" padding="lg" radius="md" withBorder>
                            <Group justify="space-between">
                                <div>
                                    <Text size="xs" c="dimmed">
                                        Document ID
                                    </Text>
                                    <Code>{documentation.document_id}</Code>
                                    <Text size="xs" c="dimmed" mt="xs">
                                        Generated: {new Date(documentation.generated_date).toLocaleString()}
                                    </Text>
                                </div>
                                <Button
                                    leftSection={<IconDownload size={16} />}
                                    onClick={downloadDocumentation}
                                    variant="light"
                                >
                                    Download Documentation
                                </Button>
                            </Group>
                        </Card>

                        {/* Model Information */}
                        <Card shadow="sm" padding="lg" radius="md" withBorder>
                            <Group mb="md">
                                <ThemeIcon variant="light" size="lg">
                                    <IconChartBar size={20} />
                                </ThemeIcon>
                                <Text fw={600} size="lg">
                                    Model Information
                                </Text>
                            </Group>
                            <Grid>
                                <Grid.Col span={{ base: 12, md: 6 }}>
                                    <Text size="xs" c="dimmed">
                                        Name
                                    </Text>
                                    <Text fw={600}>{documentation.model_info.name}</Text>
                                </Grid.Col>
                                <Grid.Col span={{ base: 12, md: 6 }}>
                                    <Text size="xs" c="dimmed">
                                        Version
                                    </Text>
                                    <Text fw={600}>{documentation.model_info.version}</Text>
                                </Grid.Col>
                                <Grid.Col span={{ base: 12, md: 6 }}>
                                    <Text size="xs" c="dimmed">
                                        Type
                                    </Text>
                                    <Badge>{documentation.model_info.type}</Badge>
                                </Grid.Col>
                                <Grid.Col span={12}>
                                    <Text size="xs" c="dimmed">
                                        Purpose
                                    </Text>
                                    <Text>{documentation.model_info.purpose || 'Not specified'}</Text>
                                </Grid.Col>
                            </Grid>
                        </Card>

                        {/* Fairness Assessment */}
                        <Card shadow="sm" padding="lg" radius="md" withBorder>
                            <Group mb="md">
                                <ThemeIcon variant="light" size="lg" color="blue">
                                    <IconScale size={20} />
                                </ThemeIcon>
                                <Text fw={600} size="lg">
                                    Fairness Assessment
                                </Text>
                            </Group>

                            {documentation.fairness_assessment.bias_detected && (
                                <Alert
                                    icon={<IconAlertTriangle size={16} />}
                                    color="yellow"
                                    mb="md"
                                    title="Bias Detected"
                                >
                                    This model has been identified as having potential bias. Review the
                                    mitigation strategies below.
                                </Alert>
                            )}

                            <Grid>
                                <Grid.Col span={{ base: 12, md: 6 }}>
                                    <Paper p="md" withBorder>
                                        <Text size="sm" fw={600} mb="xs">
                                            Metrics Evaluated
                                        </Text>
                                        <List size="sm">
                                            {documentation.fairness_assessment.metrics_evaluated.map(
                                                (metric, index) => (
                                                    <List.Item key={index}>{metric}</List.Item>
                                                )
                                            )}
                                        </List>
                                    </Paper>
                                </Grid.Col>
                                <Grid.Col span={{ base: 12, md: 6 }}>
                                    <Paper p="md" withBorder>
                                        <Text size="sm" fw={600} mb="xs">
                                            Protected Attributes
                                        </Text>
                                        <Group gap="xs">
                                            {documentation.fairness_assessment.protected_attributes.map(
                                                (attr, index) => (
                                                    <Badge key={index} variant="light">
                                                        {attr}
                                                    </Badge>
                                                )
                                            )}
                                        </Group>
                                    </Paper>
                                </Grid.Col>
                                <Grid.Col span={12}>
                                    <Paper p="md" withBorder>
                                        <Text size="sm" fw={600} mb="xs">
                                            Fairness Scores
                                        </Text>
                                        <Grid>
                                            {Object.entries(documentation.fairness_assessment.fairness_scores).map(
                                                ([metric, score]) => (
                                                    <Grid.Col key={metric} span={{ base: 12, md: 6 }}>
                                                        <Group justify="space-between">
                                                            <Text size="sm">{metric.replace('_', ' ')}</Text>
                                                            <Badge
                                                                color={score >= 0.8 ? 'green' : score >= 0.6 ? 'yellow' : 'red'}
                                                            >
                                                                {(score * 100).toFixed(0)}%
                                                            </Badge>
                                                        </Group>
                                                    </Grid.Col>
                                                )
                                            )}
                                        </Grid>
                                    </Paper>
                                </Grid.Col>
                            </Grid>
                        </Card>

                        {/* Mitigation Strategies */}
                        <Card shadow="sm" padding="lg" radius="md" withBorder>
                            <Group mb="md">
                                <ThemeIcon variant="light" size="lg" color="orange">
                                    <IconShieldCheck size={20} />
                                </ThemeIcon>
                                <Text fw={600} size="lg">
                                    Mitigation Strategies
                                </Text>
                            </Group>

                            <Stack gap="md">
                                {documentation.mitigation_strategies.map((strategy, index) => (
                                    <Paper key={index} p="md" withBorder>
                                        <Group justify="space-between" mb="xs">
                                            <Text fw={600}>{strategy.strategy}</Text>
                                            <Badge color={getPriorityColor(strategy.priority)}>
                                                {strategy.priority.toUpperCase()} PRIORITY
                                            </Badge>
                                        </Group>
                                        <Text size="sm" c="dimmed">
                                            {strategy.description}
                                        </Text>
                                    </Paper>
                                ))}
                            </Stack>
                        </Card>

                        {/* Monitoring Plan */}
                        <Card shadow="sm" padding="lg" radius="md" withBorder>
                            <Group mb="md">
                                <ThemeIcon variant="light" size="lg" color="violet">
                                    <IconEye size={20} />
                                </ThemeIcon>
                                <Text fw={600} size="lg">
                                    Monitoring Plan
                                </Text>
                            </Group>

                            <Stack gap="md">
                                <Paper p="md" withBorder>
                                    <Text size="sm" fw={600} mb="xs">
                                        Monitoring Frequency
                                    </Text>
                                    <Badge size="lg">{documentation.monitoring_plan.frequency}</Badge>
                                </Paper>

                                <Paper p="md" withBorder>
                                    <Text size="sm" fw={600} mb="xs">
                                        Metrics to Track
                                    </Text>
                                    <List size="sm">
                                        {documentation.monitoring_plan.metrics_to_track.map((metric, index) => (
                                            <List.Item key={index}>{metric}</List.Item>
                                        ))}
                                    </List>
                                </Paper>

                                <Paper p="md" withBorder>
                                    <Text size="sm" fw={600} mb="xs">
                                        Alert Thresholds
                                    </Text>
                                    <Grid>
                                        {Object.entries(documentation.monitoring_plan.alert_thresholds).map(
                                            ([metric, threshold]) => (
                                                <Grid.Col key={metric} span={{ base: 12, md: 6 }}>
                                                    <Group justify="space-between">
                                                        <Text size="sm">{metric.replace('_', ' ')}</Text>
                                                        <Code>{threshold}</Code>
                                                    </Group>
                                                </Grid.Col>
                                            )
                                        )}
                                    </Grid>
                                </Paper>

                                <Paper p="md" withBorder>
                                    <Text size="sm" fw={600} mb="xs">
                                        Review Process
                                    </Text>
                                    <Text size="sm">{documentation.monitoring_plan.review_process}</Text>
                                </Paper>
                            </Stack>
                        </Card>

                        {/* Stakeholder Communication */}
                        <Card shadow="sm" padding="lg" radius="md" withBorder>
                            <Group mb="md">
                                <ThemeIcon variant="light" size="lg" color="teal">
                                    <IconUsers size={20} />
                                </ThemeIcon>
                                <Text fw={600} size="lg">
                                    Stakeholder Communication
                                </Text>
                            </Group>

                            <Grid>
                                <Grid.Col span={{ base: 12, md: 4 }}>
                                    <Paper p="md" withBorder>
                                        <Text size="sm" fw={600} mb="xs">
                                            Target Audiences
                                        </Text>
                                        <Stack gap="xs">
                                            {documentation.stakeholder_communication.target_audiences.map(
                                                (audience, index) => (
                                                    <Badge key={index} variant="light">
                                                        {audience}
                                                    </Badge>
                                                )
                                            )}
                                        </Stack>
                                    </Paper>
                                </Grid.Col>
                                <Grid.Col span={{ base: 12, md: 4 }}>
                                    <Paper p="md" withBorder>
                                        <Text size="sm" fw={600} mb="xs">
                                            Key Messages
                                        </Text>
                                        <List size="sm">
                                            {documentation.stakeholder_communication.key_messages.map(
                                                (message, index) => (
                                                    <List.Item key={index}>{message}</List.Item>
                                                )
                                            )}
                                        </List>
                                    </Paper>
                                </Grid.Col>
                                <Grid.Col span={{ base: 12, md: 4 }}>
                                    <Paper p="md" withBorder>
                                        <Text size="sm" fw={600} mb="xs">
                                            Transparency Measures
                                        </Text>
                                        <List size="sm">
                                            {documentation.stakeholder_communication.transparency_measures.map(
                                                (measure, index) => (
                                                    <List.Item key={index}>{measure}</List.Item>
                                                )
                                            )}
                                        </List>
                                    </Paper>
                                </Grid.Col>
                            </Grid>
                        </Card>
                    </>
                )}
            </Stack>
        </Container>
    );
}
