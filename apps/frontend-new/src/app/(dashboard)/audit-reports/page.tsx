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
    Timeline,
    Accordion,
    List,
    ThemeIcon,
    Alert,
    Loader,
} from '@mantine/core';
import {
    IconFileText,
    IconDownload,
    IconAlertCircle,
    IconCheck,
    IconClock,
    IconShieldCheck,
    IconScale,
    IconBook,
    IconFileAnalytics,
} from '@tabler/icons-react';

interface AuditReport {
    report_id: string;
    system_id: string;
    report_date: string;
    system_name: string;
    system_description: string;
    risk_level: string;
    overall_compliance_score: number;
    frameworks_assessed: string[];
    compliance_results: Array<{
        framework: string;
        compliance_score: number;
        overall_status: string;
        total_requirements: number;
        compliant_requirements: number;
    }>;
    executive_summary: string;
    recommendations: Array<{
        framework: string;
        recommendation: string;
        priority: string;
    }>;
    next_review_date: string;
}

export default function AuditReportsPage() {
    const [systemId, setSystemId] = useState('');
    const [systemName, setSystemName] = useState('');
    const [systemDescription, setSystemDescription] = useState('');
    const [riskLevel, setRiskLevel] = useState<string>('');
    const [selectedFrameworks, setSelectedFrameworks] = useState<string[]>([]);
    const [auditReport, setAuditReport] = useState<AuditReport | null>(null);
    const [loading, setLoading] = useState(false);

    const frameworks = [
        { value: 'EU AI Act', label: 'EU AI Act' },
        { value: 'GDPR', label: 'GDPR' },
        { value: 'ISO 42001', label: 'ISO 42001' },
        { value: 'NIST AI RMF', label: 'NIST AI RMF' },
        { value: 'IEEE 7000', label: 'IEEE 7000' },
        { value: 'DPDP Act', label: 'DPDP Act (India)' },
        { value: 'India AI', label: 'India AI' },
    ];

    const riskLevels = [
        { value: 'minimal', label: 'Minimal Risk' },
        { value: 'limited', label: 'Limited Risk' },
        { value: 'high', label: 'High Risk' },
        { value: 'unacceptable', label: 'Unacceptable Risk' },
    ];

    const generateAuditReport = async () => {
        if (!systemId || !systemName) {
            alert('Please fill in system ID and name');
            return;
        }

        setLoading(true);
        try {
            // Sample system data with evidence
            const systemData = {
                name: systemName,
                description: systemDescription,
                risk_level: riskLevel,
                evidence_EU_AI_1: [{ quality: 0.9, description: 'Risk classification completed' }],
                evidence_EU_AI_2: [{ quality: 0.85, description: 'Transparency measures implemented' }],
                evidence_EU_AI_3: [{ quality: 0.8, description: 'Human oversight in place' }],
                evidence_EU_AI_4: [{ quality: 0.9, description: 'Data governance established' }],
                evidence_EU_AI_5: [{ quality: 0.95, description: 'Technical documentation maintained' }],
                evidence_EU_AI_6: [{ quality: 0.88, description: 'Logging system active' }],
                evidence_EU_AI_7: [{ quality: 0.82, description: 'Accuracy monitoring in place' }],
                evidence_EU_AI_8: [{ quality: 0.78, description: 'Cybersecurity measures in place' }],
                evidence_GDPR_1: [{ quality: 0.9, description: 'Legal basis established' }],
                evidence_GDPR_2: [{ quality: 0.85, description: 'Data minimization applied' }],
                evidence_GDPR_3: [{ quality: 0.8, description: 'Automated decision safeguards' }],
                evidence_GDPR_4: [{ quality: 0.9, description: 'DPIA conducted' }],
                evidence_GDPR_5: [{ quality: 0.87, description: 'Explanation mechanisms in place' }],
                evidence_ISO_1: [{ quality: 0.85, description: 'AI management system established' }],
                evidence_ISO_2: [{ quality: 0.88, description: 'Risk management implemented' }],
                evidence_ISO_3: [{ quality: 0.83, description: 'Personnel competence ensured' }],
                evidence_NIST_1: [{ quality: 0.9, description: 'Governance structure in place' }],
                evidence_NIST_2: [{ quality: 0.85, description: 'Risk mapping completed' }],
                evidence_NIST_3: [{ quality: 0.87, description: 'Performance measurement active' }],
                evidence_NIST_4: [{ quality: 0.84, description: 'Risk management strategies implemented' }],
                evidence_IEEE_1: [{ quality: 0.83, description: 'Value-based design applied' }],
            };

            const response = await fetch('http://localhost:8000/api/v1/compliance/audit-report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    system_id: systemId,
                    system_data: systemData,
                    frameworks: selectedFrameworks.length > 0 ? selectedFrameworks : null,
                }),
            });

            const data = await response.json();
            setAuditReport(data);
        } catch (error) {
            console.error('Error generating audit report:', error);
            alert('Error generating audit report');
        } finally {
            setLoading(false);
        }
    };

    const downloadReport = () => {
        if (!auditReport) return;

        const reportText = `
AUDIT REPORT
============

Report ID: ${auditReport.report_id}
System: ${auditReport.system_name}
Date: ${new Date(auditReport.report_date).toLocaleDateString()}

EXECUTIVE SUMMARY
${auditReport.executive_summary}

COMPLIANCE RESULTS
Overall Score: ${auditReport.overall_compliance_score.toFixed(1)}%
Risk Level: ${auditReport.risk_level}

Frameworks Assessed:
${auditReport.frameworks_assessed.map((f) => `- ${f}`).join('\n')}

DETAILED RESULTS
${auditReport.compliance_results
                .map(
                    (r) => `
${r.framework}
Score: ${r.compliance_score.toFixed(1)}%
Status: ${r.overall_status}
Requirements Met: ${r.compliant_requirements}/${r.total_requirements}
`
                )
                .join('\n')}

RECOMMENDATIONS
${auditReport.recommendations
                .map((r) => `[${r.priority.toUpperCase()}] ${r.framework}: ${r.recommendation}`)
                .join('\n')}

Next Review Date: ${new Date(auditReport.next_review_date).toLocaleDateString()}
    `;

        const blob = new Blob([reportText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `audit-report-${auditReport.report_id}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
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
                    <Title order={1}>Audit Reports</Title>
                    <Text c="dimmed" size="sm">
                        Generate comprehensive compliance audit reports
                    </Text>
                </div>

                {/* Report Generation Form */}
                <Card shadow="sm" padding="lg" radius="md" withBorder>
                    <Stack gap="md">
                        <Text fw={600} size="lg">
                            Generate New Audit Report
                        </Text>

                        <Grid>
                            <Grid.Col span={{ base: 12, md: 6 }}>
                                <TextInput
                                    label="System ID"
                                    placeholder="e.g., SYS-001"
                                    value={systemId}
                                    onChange={(e) => setSystemId(e.currentTarget.value)}
                                    required
                                />
                            </Grid.Col>
                            <Grid.Col span={{ base: 12, md: 6 }}>
                                <TextInput
                                    label="System Name"
                                    placeholder="e.g., Recommendation Engine"
                                    value={systemName}
                                    onChange={(e) => setSystemName(e.currentTarget.value)}
                                    required
                                />
                            </Grid.Col>
                            <Grid.Col span={12}>
                                <Textarea
                                    label="System Description"
                                    placeholder="Describe the AI system..."
                                    value={systemDescription}
                                    onChange={(e) => setSystemDescription(e.currentTarget.value)}
                                    minRows={3}
                                />
                            </Grid.Col>
                            <Grid.Col span={{ base: 12, md: 6 }}>
                                <Select
                                    label="Risk Level"
                                    placeholder="Select risk level"
                                    value={riskLevel}
                                    onChange={(value) => setRiskLevel(value || '')}
                                    data={riskLevels}
                                />
                            </Grid.Col>
                            <Grid.Col span={{ base: 12, md: 6 }}>
                                <Select
                                    label="Frameworks to Assess"
                                    placeholder="Leave empty for all frameworks"
                                    value={selectedFrameworks[0] || null}
                                    onChange={(value) => setSelectedFrameworks(value ? [value] : [])}
                                    data={frameworks}
                                    clearable
                                />
                            </Grid.Col>
                        </Grid>

                        <Button
                            leftSection={<IconFileAnalytics size={16} />}
                            onClick={generateAuditReport}
                            loading={loading}
                            size="md"
                        >
                            Generate Audit Report
                        </Button>
                    </Stack>
                </Card>

                {/* Loading State */}
                {loading && (
                    <Card shadow="sm" padding="lg" radius="md" withBorder>
                        <Stack align="center" gap="md">
                            <Loader size="lg" />
                            <Text>Generating comprehensive audit report...</Text>
                        </Stack>
                    </Card>
                )}

                {/* Audit Report */}
                {auditReport && !loading && (
                    <>
                        {/* Report Header */}
                        <Card shadow="sm" padding="lg" radius="md" withBorder>
                            <Group justify="space-between" mb="md">
                                <div>
                                    <Text size="xs" c="dimmed">
                                        Report ID
                                    </Text>
                                    <Text fw={600}>{auditReport.report_id}</Text>
                                </div>
                                <Button
                                    leftSection={<IconDownload size={16} />}
                                    onClick={downloadReport}
                                    variant="light"
                                >
                                    Download Report
                                </Button>
                            </Group>

                            <Grid>
                                <Grid.Col span={{ base: 12, md: 3 }}>
                                    <Text size="xs" c="dimmed">
                                        System Name
                                    </Text>
                                    <Text fw={600}>{auditReport.system_name}</Text>
                                </Grid.Col>
                                <Grid.Col span={{ base: 12, md: 3 }}>
                                    <Text size="xs" c="dimmed">
                                        Report Date
                                    </Text>
                                    <Text fw={600}>
                                        {new Date(auditReport.report_date).toLocaleDateString()}
                                    </Text>
                                </Grid.Col>
                                <Grid.Col span={{ base: 12, md: 3 }}>
                                    <Text size="xs" c="dimmed">
                                        Risk Level
                                    </Text>
                                    <Badge color={auditReport.risk_level === 'high' ? 'red' : 'blue'}>
                                        {auditReport.risk_level}
                                    </Badge>
                                </Grid.Col>
                                <Grid.Col span={{ base: 12, md: 3 }}>
                                    <Text size="xs" c="dimmed">
                                        Overall Score
                                    </Text>
                                    <Text fw={700} size="xl" c="green">
                                        {auditReport.overall_compliance_score.toFixed(1)}%
                                    </Text>
                                </Grid.Col>
                            </Grid>
                        </Card>

                        {/* Executive Summary */}
                        <Card shadow="sm" padding="lg" radius="md" withBorder>
                            <Group mb="md">
                                <ThemeIcon variant="light" size="lg">
                                    <IconFileText size={20} />
                                </ThemeIcon>
                                <Text fw={600} size="lg">
                                    Executive Summary
                                </Text>
                            </Group>
                            <Text style={{ whiteSpace: 'pre-line' }}>{auditReport.executive_summary}</Text>
                        </Card>

                        {/* Compliance Results */}
                        <Card shadow="sm" padding="lg" radius="md" withBorder>
                            <Group mb="md">
                                <ThemeIcon variant="light" size="lg" color="blue">
                                    <IconScale size={20} />
                                </ThemeIcon>
                                <Text fw={600} size="lg">
                                    Compliance Results
                                </Text>
                            </Group>

                            <Grid>
                                {auditReport.compliance_results.map((result, index) => (
                                    <Grid.Col key={index} span={{ base: 12, md: 6 }}>
                                        <Paper p="md" withBorder>
                                            <Group justify="space-between" mb="xs">
                                                <Text fw={600}>{result.framework}</Text>
                                                <Badge color={getStatusColor(result.overall_status)}>
                                                    {result.overall_status.replace('_', ' ')}
                                                </Badge>
                                            </Group>
                                            <Text size="xl" fw={700} mb="xs">
                                                {result.compliance_score.toFixed(1)}%
                                            </Text>
                                            <Text size="sm" c="dimmed">
                                                {result.compliant_requirements} / {result.total_requirements}{' '}
                                                requirements met
                                            </Text>
                                        </Paper>
                                    </Grid.Col>
                                ))}
                            </Grid>
                        </Card>

                        {/* Recommendations */}
                        <Card shadow="sm" padding="lg" radius="md" withBorder>
                            <Group mb="md">
                                <ThemeIcon variant="light" size="lg" color="orange">
                                    <IconBook size={20} />
                                </ThemeIcon>
                                <Text fw={600} size="lg">
                                    Recommendations
                                </Text>
                            </Group>

                            {auditReport.recommendations.length > 0 ? (
                                <Accordion>
                                    {auditReport.recommendations.map((rec, index) => (
                                        <Accordion.Item key={index} value={`rec-${index}`}>
                                            <Accordion.Control>
                                                <Group>
                                                    <Badge color={getPriorityColor(rec.priority)} size="sm">
                                                        {rec.priority.toUpperCase()}
                                                    </Badge>
                                                    <Text size="sm">{rec.framework}</Text>
                                                </Group>
                                            </Accordion.Control>
                                            <Accordion.Panel>
                                                <Text size="sm">{rec.recommendation}</Text>
                                            </Accordion.Panel>
                                        </Accordion.Item>
                                    ))}
                                </Accordion>
                            ) : (
                                <Alert icon={<IconCheck size={16} />} color="green">
                                    No recommendations - all requirements are met!
                                </Alert>
                            )}
                        </Card>

                        {/* Next Review */}
                        <Card shadow="sm" padding="lg" radius="md" withBorder>
                            <Group>
                                <ThemeIcon variant="light" size="lg" color="violet">
                                    <IconClock size={20} />
                                </ThemeIcon>
                                <div>
                                    <Text size="sm" c="dimmed">
                                        Next Review Date
                                    </Text>
                                    <Text fw={600}>
                                        {new Date(auditReport.next_review_date).toLocaleDateString()}
                                    </Text>
                                </div>
                            </Group>
                        </Card>
                    </>
                )}
            </Stack>
        </Container>
    );
}
