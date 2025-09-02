'use client';

import {
  Container,
  Title,
  Text,
  Stepper,
  Button,
  Group,
  Card,
  Stack,
  TextInput,
  Select,
  NumberInput,
  Textarea,
  Checkbox,
  FileInput,
  Progress,
  Alert,
  Badge,
  Divider,
  Box,
  Paper,
  RingProgress,
  Table,
  ActionIcon,
  Modal,
  ThemeIcon,
  SimpleGrid,
} from '@mantine/core';
import {
  IconUpload,
  IconScan,
  IconTarget,
  IconShield,
  IconChecklist,
  IconCheck,
  IconX,
  IconAlertTriangle,
  IconEye,
  IconDownload,
  IconBrain,
  IconFileText,
  IconShieldCheck,
  IconTargetOff,
  IconDatabase,
} from '@tabler/icons-react';
import { useState } from 'react';

interface ModelData {
  name: string;
  type: string;
  version: string;
  description: string;
  fairnessThreshold: number;
  complianceConfirmed: boolean;
}

interface AssessmentResult {
  step: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  score: number;
  details: string;
  recommendations: string[];
}

export default function ModelAssessmentPage() {
  const [active, setActive] = useState(0);
  const [modelData, setModelData] = useState<ModelData>({
    name: '',
    type: '',
    version: '',
    description: '',
    fairnessThreshold: 0.8,
    complianceConfirmed: false,
  });
  const [assessmentResults, setAssessmentResults] = useState<AssessmentResult[]>([
    { step: 'Basic Analysis', status: 'pending', score: 0, details: '', recommendations: [] },
    { step: 'Bias Detection', status: 'pending', score: 0, details: '', recommendations: [] },
    { step: 'Security Check', status: 'pending', score: 0, details: '', recommendations: [] },
    { step: 'Compliance Review', status: 'pending', score: 0, details: '', recommendations: [] },
  ]);
  const [showResultsModal, setShowResultsModal] = useState(false);

  const nextStep = () => setActive((current) => (current < 4 ? current + 1 : current));
  const prevStep = () => setActive((current) => (current > 0 ? current - 1 : current));

  const runAssessment = async (stepIndex: number) => {
    // Simulate assessment process
    setAssessmentResults(prev => 
      prev.map((result, index) => 
        index === stepIndex 
          ? { ...result, status: 'running' }
          : result
      )
    );

    // Simulate processing time
    setTimeout(() => {
      const mockScores = [85, 92, 78, 88];
      const mockDetails = [
        'Model architecture validated, performance metrics within acceptable range',
        'Bias analysis completed, protected attributes identified and tested',
        'Security vulnerabilities scanned, OWASP AI Top 10 compliance checked',
        'Regulatory framework mapping completed, compliance gaps identified'
      ];
      const mockRecommendations = [
        ['Consider model compression for deployment', 'Monitor performance drift'],
        ['Implement fairness constraints for age attribute', 'Add bias monitoring'],
        ['Update authentication mechanisms', 'Implement rate limiting'],
        ['Document EU AI Act compliance', 'Establish audit trail']
      ];

      setAssessmentResults(prev => 
        prev.map((result, index) => 
          index === stepIndex 
            ? { 
                ...result, 
                status: 'completed', 
                score: mockScores[index],
                details: mockDetails[index],
                recommendations: mockRecommendations[index]
              }
            : result
        )
      );
    }, 2000);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'green';
      case 'running': return 'blue';
      case 'failed': return 'red';
      default: return 'gray';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <IconCheck size={16} />;
      case 'running': return <IconScan size={16} />;
      case 'failed': return <IconX size={16} />;
      default: return <IconTarget size={16} />;
    }
  };

  const overallScore = assessmentResults.reduce((sum, result) => 
    result.status === 'completed' ? sum + result.score : sum, 0
  ) / assessmentResults.filter(r => r.status === 'completed').length || 0;

  return (
    <Container size="lg" py="xl">
      {/* Page Header */}
      <Paper bg="white" py="xl" mb="xl" withBorder>
        <Stack gap="xs">
          <Title order={1} size="2.5rem" fw={600} c="dark.8">
            Model Assessment
          </Title>
          <Text size="lg" c="dark.6">
            Complete end-to-end model evaluation workflow
          </Text>
        </Stack>
      </Paper>

      {/* Assessment Stepper */}
      <Card withBorder mb="xl">
        <Card.Section withBorder inheritPadding py="md">
          <Text fw={500} size="lg">Assessment Progress</Text>
        </Card.Section>
        
        <Box p="xl">
          <Stepper active={active} size="sm" mb="xl">
            <Stepper.Step label="Upload" icon={<IconUpload size={16} />}>
              <Stack gap="md" mt="md">
                <Text size="sm" c="dimmed">
                  Upload your model and provide basic information
                </Text>
                
                <TextInput
                  label="Model Name"
                  placeholder="Enter model name"
                  value={modelData.name}
                  onChange={(e) => setModelData({ ...modelData, name: e.target.value })}
                  withAsterisk
                />
                
                <Select
                  label="Model Type"
                  placeholder="Select model type"
                  data={['Classification', 'Regression', 'Anomaly Detection', 'Recommendation', 'Other']}
                  value={modelData.type}
                  onChange={(value) => setModelData({ ...modelData, type: value || '' })}
                  withAsterisk
                />
                
                <TextInput
                  label="Version"
                  placeholder="e.g., 1.0.0"
                  value={modelData.version}
                  onChange={(e) => setModelData({ ...modelData, version: e.target.value })}
                  withAsterisk
                />
                
                <Textarea
                  label="Description"
                  placeholder="Brief description of the model"
                  value={modelData.description}
                  onChange={(e) => setModelData({ ...modelData, description: e.target.value })}
                  rows={3}
                />
                
                <NumberInput
                  label="Fairness Threshold"
                  placeholder="0.8"
                  min={0}
                  max={1}
                  step={0.1}
                  value={modelData.fairnessThreshold}
                  onChange={(value) => setModelData({ ...modelData, fairnessThreshold: value || 0.8 })}
                  withAsterisk
                />
                
                <FileInput
                  label="Model File"
                  placeholder="Upload model file"
                  accept=".pkl,.joblib,.onnx,.pb,.h5,.pt,.pth"
                  withAsterisk
                />
                
                <Checkbox
                  label="I confirm this model complies with our ethical AI guidelines"
                  checked={modelData.complianceConfirmed}
                  onChange={(e) => setModelData({ ...modelData, complianceConfirmed: e.target.checked })}
                  withAsterisk
                />
              </Stack>
            </Stepper.Step>
            
            <Stepper.Step label="Basic Analysis" icon={<IconScan size={16} />}>
              <Stack gap="md" mt="md">
                <Text size="sm" c="dimmed">
                  Automated analysis of model architecture and performance
                </Text>
                
                <Card withBorder p="md">
                  <Group justify="space-between" mb="md">
                    <Text fw={500}>Analysis Status</Text>
                    <Badge color={getStatusColor(assessmentResults[0].status)} variant="light">
                      {assessmentResults[0].status}
                    </Badge>
                  </Group>
                  
                  {assessmentResults[0].status === 'pending' && (
                    <Button 
                      onClick={() => runAssessment(0)}
                      leftSection={<IconScan size={16} />}
                    >
                      Start Analysis
                    </Button>
                  )}
                  
                  {assessmentResults[0].status === 'running' && (
                    <Stack gap="md">
                      <Progress value={75} animated />
                      <Text size="sm" c="dimmed">Analyzing model architecture...</Text>
                    </Stack>
                  )}
                  
                  {assessmentResults[0].status === 'completed' && (
                    <Stack gap="md">
                      <Group>
                        <Text size="lg" fw={500}>Score: {assessmentResults[0].score}%</Text>
                        <RingProgress
                          size={60}
                          thickness={6}
                          sections={[{ value: assessmentResults[0].score, color: 'green' }]}
                        />
                      </Group>
                      <Text size="sm">{assessmentResults[0].details}</Text>
                      <Text size="sm" fw={500}>Recommendations:</Text>
                      <Stack gap="xs">
                        {assessmentResults[0].recommendations.map((rec, index) => (
                          <Text key={index} size="sm" c="dimmed">• {rec}</Text>
                        ))}
                      </Stack>
                    </Stack>
                  )}
                </Card>
              </Stack>
            </Stepper.Step>
            
            <Stepper.Step label="Bias Detection" icon={<IconTarget size={16} />}>
              <Stack gap="md" mt="md">
                <Text size="sm" c="dimmed">
                  Fairness assessment and bias detection analysis
                </Text>
                
                <Card withBorder p="md">
                  <Group justify="space-between" mb="md">
                    <Text fw={500}>Bias Analysis Status</Text>
                    <Badge color={getStatusColor(assessmentResults[1].status)} variant="light">
                      {assessmentResults[1].status}
                    </Badge>
                  </Group>
                  
                  {assessmentResults[1].status === 'pending' && (
                    <Button 
                      onClick={() => runAssessment(1)}
                      leftSection={<IconTarget size={16} />}
                      disabled={assessmentResults[0].status !== 'completed'}
                    >
                      Start Bias Analysis
                    </Button>
                  )}
                  
                  {assessmentResults[1].status === 'running' && (
                    <Stack gap="md">
                      <Progress value={60} animated />
                      <Text size="sm" c="dimmed">Testing protected attributes...</Text>
                    </Stack>
                  )}
                  
                  {assessmentResults[1].status === 'completed' && (
                    <Stack gap="md">
                      <Group>
                        <Text size="lg" fw={500}>Fairness Score: {assessmentResults[1].score}%</Text>
                        <RingProgress
                          size={60}
                          thickness={6}
                          sections={[{ value: assessmentResults[1].score, color: 'green' }]}
                        />
                      </Group>
                      <Text size="sm">{assessmentResults[1].details}</Text>
                      <Text size="sm" fw={500}>Recommendations:</Text>
                      <Stack gap="xs">
                        {assessmentResults[1].recommendations.map((rec, index) => (
                          <Text key={index} size="sm" c="dimmed">• {rec}</Text>
                        ))}
                      </Stack>
                    </Stack>
                  )}
                </Card>
              </Stack>
            </Stepper.Step>
            
            <Stepper.Step label="Security Check" icon={<IconShield size={16} />}>
              <Stack gap="md" mt="md">
                <Text size="sm" c="dimmed">
                  OWASP AI security validation and threat assessment
                </Text>
                
                <Card withBorder p="md">
                  <Group justify="space-between" mb="md">
                    <Text fw={500}>Security Assessment Status</Text>
                    <Badge color={getStatusColor(assessmentResults[2].status)} variant="light">
                      {assessmentResults[2].status}
                    </Badge>
                  </Group>
                  
                  {assessmentResults[2].status === 'pending' && (
                    <Button 
                      onClick={() => runAssessment(2)}
                      leftSection={<IconShield size={16} />}
                      disabled={assessmentResults[1].status !== 'completed'}
                    >
                      Start Security Check
                    </Button>
                  )}
                  
                  {assessmentResults[2].status === 'running' && (
                    <Stack gap="md">
                      <Progress value={45} animated />
                      <Text size="sm" c="dimmed">Scanning for vulnerabilities...</Text>
                    </Stack>
                  )}
                  
                  {assessmentResults[2].status === 'completed' && (
                    <Stack gap="md">
                      <Group>
                        <Text size="lg" fw={500}>Security Score: {assessmentResults[2].score}%</Text>
                        <RingProgress
                          size={60}
                          thickness={6}
                          sections={[{ value: assessmentResults[2].score, color: 'orange' }]}
                        />
                      </Group>
                      <Text size="sm">{assessmentResults[2].details}</Text>
                      <Text size="sm" fw={500}>Recommendations:</Text>
                      <Stack gap="xs">
                        {assessmentResults[2].recommendations.map((rec, index) => (
                          <Text key={index} size="sm" c="dimmed">• {rec}</Text>
                        ))}
                      </Stack>
                    </Stack>
                  )}
                </Card>
              </Stack>
            </Stepper.Step>
            
            <Stepper.Step label="Compliance Review" icon={<IconChecklist size={16} />}>
              <Stack gap="md" mt="md">
                <Text size="sm" c="dimmed">
                  Regulatory compliance validation and documentation
                </Text>
                
                <Card withBorder p="md">
                  <Group justify="space-between" mb="md">
                    <Text fw={500}>Compliance Review Status</Text>
                    <Badge color={getStatusColor(assessmentResults[3].status)} variant="light">
                      {assessmentResults[3].status}
                    </Badge>
                  </Group>
                  
                  {assessmentResults[3].status === 'pending' && (
                    <Button 
                      onClick={() => runAssessment(3)}
                      leftSection={<IconChecklist size={16} />}
                      disabled={assessmentResults[2].status !== 'completed'}
                    >
                      Start Compliance Review
                    </Button>
                  )}
                  
                  {assessmentResults[3].status === 'running' && (
                    <Stack gap="md">
                      <Progress value={30} animated />
                      <Text size="sm" c="dimmed">Checking regulatory frameworks...</Text>
                    </Stack>
                  )}
                  
                  {assessmentResults[3].status === 'completed' && (
                    <Stack gap="md">
                      <Group>
                        <Text size="lg" fw={500}>Compliance Score: {assessmentResults[3].score}%</Text>
                        <RingProgress
                          size={60}
                          thickness={6}
                          sections={[{ value: assessmentResults[3].score, color: 'green' }]}
                        />
                      </Group>
                      <Text size="sm">{assessmentResults[3].details}</Text>
                      <Text size="sm" fw={500}>Recommendations:</Text>
                      <Stack gap="xs">
                        {assessmentResults[3].recommendations.map((rec, index) => (
                          <Text key={index} size="sm" c="dimmed">• {rec}</Text>
                        ))}
                      </Stack>
                    </Stack>
                  )}
                </Card>
              </Stack>
            </Stepper.Step>
          </Stepper>
          
          <Group justify="space-between" mt="xl">
            <Button variant="default" onClick={prevStep} disabled={active === 0}>
              Back
            </Button>
            
            {active === 4 ? (
              <Button 
                color="green" 
                size="lg"
                onClick={() => setShowResultsModal(true)}
                leftSection={<IconCheck size={20} />}
              >
                View Final Results
              </Button>
            ) : (
              <Button 
                onClick={nextStep}
                disabled={
                  active === 0 && (!modelData.name || !modelData.type || !modelData.version || !modelData.complianceConfirmed) ||
                  active > 0 && assessmentResults[active - 1].status !== 'completed'
                }
              >
                {active === 3 ? 'Complete Assessment' : 'Next Step'}
              </Button>
            )}
          </Group>
        </Box>
      </Card>

      {/* Overall Assessment Summary */}
      {assessmentResults.some(r => r.status === 'completed') && (
        <Card withBorder>
          <Card.Section withBorder inheritPadding py="md">
            <Text fw={500} size="lg">Assessment Summary</Text>
          </Card.Section>
          
          <Box p="xl">
            <Stack gap="lg">
              <Group justify="space-between">
                <Text size="xl" fw={600}>Overall Score</Text>
                <Group>
                  <Text size="2xl" fw={700} c="blue.7">{Math.round(overallScore)}%</Text>
                  <RingProgress
                    size={80}
                    thickness={8}
                    sections={[{ value: overallScore, color: 'blue' }]}
                  />
                </Group>
              </Group>
              
              <Divider />
              
              <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }}>
                {assessmentResults.map((result, index) => (
                  <Paper key={index} p="md" withBorder>
                    <Stack gap="xs" align="center">
                      <ThemeIcon 
                        size="lg" 
                        radius="md" 
                        color={getStatusColor(result.status)}
                      >
                        {getStatusIcon(result.status)}
                      </ThemeIcon>
                      <Text size="sm" fw={500} ta="center">
                        {result.step}
                      </Text>
                      {result.status === 'completed' && (
                        <Text size="lg" fw={700} c="blue.7">
                          {result.score}%
                        </Text>
                      )}
                      <Badge color={getStatusColor(result.status)} variant="light">
                        {result.status}
                      </Badge>
                    </Stack>
                  </Paper>
                ))}
              </SimpleGrid>
            </Stack>
          </Box>
        </Card>
      )}

      {/* Results Modal */}
      <Modal 
        opened={showResultsModal} 
        onClose={() => setShowResultsModal(false)}
        title="Assessment Complete"
        size="lg"
      >
        <Stack gap="lg">
          <Alert color="green" icon={<IconCheck size={16} />}>
            <Text fw={500}>Model assessment completed successfully!</Text>
            <Text size="sm">Your model has been evaluated across all criteria.</Text>
          </Alert>
          
          <Group justify="space-between">
            <Text fw={500}>Final Assessment Score</Text>
            <Text size="xl" fw={700} c="blue.7">{Math.round(overallScore)}%</Text>
          </Group>
          
          <Divider />
          
          <Stack gap="md">
            <Text fw={500}>Next Steps:</Text>
            <Text size="sm">• Review detailed recommendations for each assessment area</Text>
            <Text size="sm">• Implement suggested improvements</Text>
            <Text size="sm">• Schedule follow-up assessment if needed</Text>
            <Text size="sm">• Generate compliance documentation</Text>
          </Stack>
          
          <Group justify="flex-end" mt="md">
            <Button variant="light" onClick={() => setShowResultsModal(false)}>
              Close
            </Button>
            <Button leftSection={<IconDownload size={16} />}>
              Download Report
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Container>
  );
}
