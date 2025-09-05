'use client';

import {
  Modal,
  Stepper,
  Button,
  TextInput,
  Select,
  Textarea,
  Group,
  Text,
  Title,
  Stack,
  Card,
  Badge,
  ThemeIcon,
  Alert,
  Progress,
  Box,
  Divider,
  List,
  Checkbox,
  NumberInput,
  Switch,
  Tabs,
  ScrollArea,
} from '@mantine/core';
import {
  IconBrain,
  IconShield,
  IconTarget,
  IconChartBar,
  IconSettings,
  IconCheck,
  IconArrowRight,
  IconArrowLeft,
  IconRobot,
  IconDatabase,
  IconUsers,
  IconBuilding,
  IconRocket,
  IconSparkles,
  IconInfoCircle,
} from '@tabler/icons-react';
import { useState } from 'react';

interface OnboardingWizardProps {
  opened: boolean;
  onClose: () => void;
}

interface OnboardingData {
  organization: {
    name: string;
    size: string;
    industry: string;
    aiMaturity: string;
  };
  useCases: {
    biasDetection: boolean;
    securityTesting: boolean;
    compliance: boolean;
    monitoring: boolean;
    explainability: boolean;
    modelRegistry: boolean;
  };
  models: {
    count: number;
    types: string[];
    frameworks: string[];
  };
  preferences: {
    alertChannels: string[];
    reportingFrequency: string;
    dataRetention: string;
  };
}

export default function OnboardingWizard({ opened, onClose }: OnboardingWizardProps) {
  const [active, setActive] = useState(0);
  const [data, setData] = useState<OnboardingData>({
    organization: {
      name: '',
      size: '',
      industry: '',
      aiMaturity: '',
    },
    useCases: {
      biasDetection: false,
      securityTesting: false,
      compliance: false,
      monitoring: false,
      explainability: false,
      modelRegistry: false,
    },
    models: {
      count: 0,
      types: [],
      frameworks: [],
    },
    preferences: {
      alertChannels: [],
      reportingFrequency: '',
      dataRetention: '',
    },
  });

  const [aiRecommendations, setAiRecommendations] = useState<any>(null);
  const [isGeneratingRecommendations, setIsGeneratingRecommendations] = useState(false);

  const nextStep = () => setActive((current) => (current < 4 ? current + 1 : current));
  const prevStep = () => setActive((current) => (current > 0 ? current - 1 : current));

  const generateAIRecommendations = async () => {
    setIsGeneratingRecommendations(true);
    
    // Enhanced AI-powered recommendations based on user input
    setTimeout(() => {
      const industry = data.organization.industry;
      const size = data.organization.size;
      const aiMaturity = data.organization.aiMaturity;
      const modelCount = data.models.count;
      const useCases = data.useCases;
      
      // AI logic for personalized recommendations
      let priorityFeatures = [];
      let suggestedWorkflow = [];
      let riskAssessment = { overallRisk: 'Low', keyRisks: [] };
      let nextSteps = [];
      
      // Industry-specific recommendations
      if (industry === 'finance') {
        priorityFeatures.push(
          { name: 'Real-time Bias Detection', priority: 'critical', reason: 'Financial services require strict fairness compliance' },
          { name: 'Regulatory Compliance (GDPR, CCPA)', priority: 'critical', reason: 'Essential for financial data protection' },
          { name: 'Model Explainability', priority: 'high', reason: 'Required for credit decisions and loan approvals' }
        );
        riskAssessment.keyRisks.push('Regulatory compliance violations', 'Bias in credit scoring models', 'Data privacy breaches');
      } else if (industry === 'healthcare') {
        priorityFeatures.push(
          { name: 'HIPAA Compliance Monitoring', priority: 'critical', reason: 'Essential for healthcare data protection' },
          { name: 'Clinical Bias Detection', priority: 'high', reason: 'Critical for patient safety and equity' },
          { name: 'Model Validation & Testing', priority: 'high', reason: 'Required for medical AI systems' }
        );
        riskAssessment.keyRisks.push('Patient safety risks', 'Healthcare bias', 'HIPAA compliance gaps');
      } else if (industry === 'technology') {
        priorityFeatures.push(
          { name: 'Algorithmic Transparency', priority: 'high', reason: 'Important for user trust and platform integrity' },
          { name: 'Performance Monitoring', priority: 'high', reason: 'Critical for scalable AI systems' },
          { name: 'Security Testing', priority: 'high', reason: 'Essential for protecting user data' }
        );
        riskAssessment.keyRisks.push('Algorithmic bias', 'Security vulnerabilities', 'Performance degradation');
      }
      
      // Size-based recommendations
      if (size === 'startup' || size === 'small') {
        priorityFeatures.push(
          { name: 'Automated Compliance Reporting', priority: 'medium', reason: 'Reduce manual overhead for small teams' },
          { name: 'Quick Setup Templates', priority: 'high', reason: 'Fast deployment for growing organizations' }
        );
        suggestedWorkflow = [
          'Start with basic bias detection for your first model',
          'Set up automated monitoring alerts',
          'Configure simple compliance templates',
          'Schedule monthly governance reviews'
        ];
      } else if (size === 'large') {
        priorityFeatures.push(
          { name: 'Enterprise SSO Integration', priority: 'high', reason: 'Essential for large organization security' },
          { name: 'Advanced Audit Trails', priority: 'high', reason: 'Required for enterprise compliance' },
          { name: 'Multi-tenant Architecture', priority: 'medium', reason: 'Support multiple teams and departments' }
        );
        suggestedWorkflow = [
          'Conduct comprehensive model inventory',
          'Set up department-specific governance policies',
          'Configure enterprise-grade security and monitoring',
          'Establish regular compliance review cycles',
          'Train teams on AI governance best practices'
        ];
      }
      
      // AI Maturity-based recommendations
      if (aiMaturity === 'beginner') {
        priorityFeatures.push(
          { name: 'AI Governance Education', priority: 'high', reason: 'Build foundational knowledge' },
          { name: 'Simple Monitoring Dashboard', priority: 'high', reason: 'Easy-to-understand metrics' }
        );
        nextSteps = [
          'Complete AI governance training modules',
          'Start with one model for hands-on learning',
          'Set up basic monitoring and alerts',
          'Join FairMind community for support'
        ];
      } else if (aiMaturity === 'expert') {
        priorityFeatures.push(
          { name: 'Advanced Analytics & Reporting', priority: 'high', reason: 'Leverage sophisticated analysis capabilities' },
          { name: 'Custom Compliance Frameworks', priority: 'medium', reason: 'Tailor to specific organizational needs' }
        );
        nextSteps = [
          'Import existing model inventory',
          'Configure advanced monitoring and alerting',
          'Set up custom compliance frameworks',
          'Integrate with existing ML pipelines'
        ];
      }
      
      // Model count-based recommendations
      if (modelCount > 10) {
        priorityFeatures.push(
          { name: 'Bulk Model Analysis', priority: 'high', reason: 'Efficient analysis for multiple models' },
          { name: 'Model Portfolio Management', priority: 'high', reason: 'Organize and track model lifecycle' }
        );
      }
      
      // Use case-based recommendations
      if (useCases.biasDetection) {
        suggestedWorkflow.unshift('Configure bias detection thresholds for your models');
      }
      if (useCases.securityTesting) {
        suggestedWorkflow.push('Set up automated security testing pipeline');
      }
      if (useCases.compliance) {
        suggestedWorkflow.push('Configure compliance reporting templates');
      }
      
      // Calculate overall risk
      let riskScore = 0;
      if (industry === 'finance' || industry === 'healthcare') riskScore += 2;
      if (size === 'large') riskScore += 1;
      if (modelCount > 5) riskScore += 1;
      if (aiMaturity === 'beginner') riskScore += 1;
      
      if (riskScore >= 4) riskAssessment.overallRisk = 'High';
      else if (riskScore >= 2) riskAssessment.overallRisk = 'Medium';
      else riskAssessment.overallRisk = 'Low';
      
      const recommendations = {
        priorityFeatures: priorityFeatures.slice(0, 5), // Top 5 features
        suggestedWorkflow,
        riskAssessment,
        nextSteps,
        personalizedInsights: [
          `Based on your ${industry} industry, we recommend focusing on ${industry === 'finance' ? 'regulatory compliance' : industry === 'healthcare' ? 'patient safety' : 'algorithmic transparency'}`,
          `With ${size} organization size, ${size === 'startup' ? 'start simple and scale' : size === 'large' ? 'implement enterprise-grade governance' : 'balance automation with oversight'}`,
          `Your ${aiMaturity} AI maturity level suggests ${aiMaturity === 'beginner' ? 'starting with education and simple tools' : aiMaturity === 'expert' ? 'leveraging advanced features' : 'gradual implementation'}`
        ]
      };
      
      setAiRecommendations(recommendations);
      setIsGeneratingRecommendations(false);
    }, 3000); // Longer delay to show AI processing
  };

  const steps = [
    {
      label: 'Organization',
      description: 'Tell us about your organization',
      icon: <IconBuilding size="1.2rem" />,
    },
    {
      label: 'Use Cases',
      description: 'Select your AI governance needs',
      icon: <IconTarget size="1.2rem" />,
    },
    {
      label: 'Models',
      description: 'Describe your AI models',
      icon: <IconBrain size="1.2rem" />,
    },
    {
      label: 'Preferences',
      description: 'Configure your preferences',
      icon: <IconSettings size="1.2rem" />,
    },
    {
      label: 'AI Recommendations',
      description: 'Get personalized recommendations',
      icon: <IconSparkles size="1.2rem" />,
    },
  ];

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title="Welcome to FairMind AI Governance"
      size="xl"
      centered
    >
      <Stepper active={active} onStepClick={setActive} breakpoint="sm">
        {/* Step 1: Organization */}
        <Stepper.Step label="Organization" description="Organization details" icon={<IconBuilding size="1.2rem" />}>
          <Stack gap="md" mt="md">
            <Title order={3}>Tell us about your organization</Title>
            <Text c="dimmed">This helps us customize your AI governance experience</Text>
            
            <TextInput
              label="Organization Name"
              placeholder="Enter your organization name"
              value={data.organization.name}
              onChange={(e) => setData({
                ...data,
                organization: { ...data.organization, name: e.target.value }
              })}
              required
            />
            
            <Select
              label="Organization Size"
              placeholder="Select organization size"
              data={[
                { value: 'startup', label: 'Startup (1-50 employees)' },
                { value: 'small', label: 'Small (51-200 employees)' },
                { value: 'medium', label: 'Medium (201-1000 employees)' },
                { value: 'large', label: 'Large (1000+ employees)' },
              ]}
              value={data.organization.size}
              onChange={(value) => setData({
                ...data,
                organization: { ...data.organization, size: value || '' }
              })}
              required
            />
            
            <Select
              label="Industry"
              placeholder="Select your industry"
              data={[
                { value: 'finance', label: 'Financial Services' },
                { value: 'healthcare', label: 'Healthcare' },
                { value: 'technology', label: 'Technology' },
                { value: 'retail', label: 'Retail & E-commerce' },
                { value: 'manufacturing', label: 'Manufacturing' },
                { value: 'government', label: 'Government' },
                { value: 'education', label: 'Education' },
                { value: 'other', label: 'Other' },
              ]}
              value={data.organization.industry}
              onChange={(value) => setData({
                ...data,
                organization: { ...data.organization, industry: value || '' }
              })}
              required
            />
            
            <Select
              label="AI Maturity Level"
              placeholder="How mature is your AI program?"
              data={[
                { value: 'beginner', label: 'Beginner - Just getting started with AI' },
                { value: 'developing', label: 'Developing - Some AI models in production' },
                { value: 'advanced', label: 'Advanced - Multiple AI systems deployed' },
                { value: 'expert', label: 'Expert - AI-first organization' },
              ]}
              value={data.organization.aiMaturity}
              onChange={(value) => setData({
                ...data,
                organization: { ...data.organization, aiMaturity: value || '' }
              })}
              required
            />
          </Stack>
        </Stepper.Step>

        {/* Step 2: Use Cases */}
        <Stepper.Step label="Use Cases" description="AI governance needs" icon={<IconTarget size="1.2rem" />}>
          <Stack gap="md" mt="md">
            <Title order={3}>What AI governance features do you need?</Title>
            <Text c="dimmed">Select all that apply to your organization</Text>
            
            <Stack gap="sm">
              <Card withBorder p="md">
                <Group justify="space-between">
                  <Group gap="md">
                    <ThemeIcon size="lg" color="red" variant="light">
                      <IconTarget size="1.2rem" />
                    </ThemeIcon>
                    <Box>
                      <Text fw={500}>Bias Detection & Fairness</Text>
                      <Text size="sm" c="dimmed">Detect and mitigate bias in AI models</Text>
                    </Box>
                  </Group>
                  <Checkbox
                    checked={data.useCases.biasDetection}
                    onChange={(e) => setData({
                      ...data,
                      useCases: { ...data.useCases, biasDetection: e.currentTarget.checked }
                    })}
                  />
                </Group>
              </Card>
              
              <Card withBorder p="md">
                <Group justify="space-between">
                  <Group gap="md">
                    <ThemeIcon size="lg" color="blue" variant="light">
                      <IconShield size="1.2rem" />
                    </ThemeIcon>
                    <Box>
                      <Text fw={500}>Security Testing</Text>
                      <Text size="sm" c="dimmed">Test AI models for security vulnerabilities</Text>
                    </Box>
                  </Group>
                  <Checkbox
                    checked={data.useCases.securityTesting}
                    onChange={(e) => setData({
                      ...data,
                      useCases: { ...data.useCases, securityTesting: e.currentTarget.checked }
                    })}
                  />
                </Group>
              </Card>
              
              <Card withBorder p="md">
                <Group justify="space-between">
                  <Group gap="md">
                    <ThemeIcon size="lg" color="green" variant="light">
                      <IconCheck size="1.2rem" />
                    </ThemeIcon>
                    <Box>
                      <Text fw={500}>Compliance & Auditing</Text>
                      <Text size="sm" c="dimmed">Ensure regulatory compliance and audit trails</Text>
                    </Box>
                  </Group>
                  <Checkbox
                    checked={data.useCases.compliance}
                    onChange={(e) => setData({
                      ...data,
                      useCases: { ...data.useCases, compliance: e.currentTarget.checked }
                    })}
                  />
                </Group>
              </Card>
              
              <Card withBorder p="md">
                <Group justify="space-between">
                  <Group gap="md">
                    <ThemeIcon size="lg" color="purple" variant="light">
                      <IconChartBar size="1.2rem" />
                    </ThemeIcon>
                    <Box>
                      <Text fw={500}>Model Monitoring</Text>
                      <Text size="sm" c="dimmed">Monitor model performance and drift</Text>
                    </Box>
                  </Group>
                  <Checkbox
                    checked={data.useCases.monitoring}
                    onChange={(e) => setData({
                      ...data,
                      useCases: { ...data.useCases, monitoring: e.currentTarget.checked }
                    })}
                  />
                </Group>
              </Card>
            </Stack>
          </Stack>
        </Stepper.Step>

        {/* Step 3: Models */}
        <Stepper.Step label="Models" description="AI model details" icon={<IconBrain size="1.2rem" />}>
          <Stack gap="md" mt="md">
            <Title order={3}>Tell us about your AI models</Title>
            <Text c="dimmed">Help us understand your current AI infrastructure</Text>
            
            <NumberInput
              label="Number of AI Models"
              placeholder="How many AI models do you have?"
              value={data.models.count}
              onChange={(value) => setData({
                ...data,
                models: { ...data.models, count: Number(value) || 0 }
              })}
              min={0}
              required
            />
            
            <Select
              label="Model Types"
              placeholder="Select model types you use"
              data={[
                { value: 'classification', label: 'Classification' },
                { value: 'regression', label: 'Regression' },
                { value: 'nlp', label: 'Natural Language Processing' },
                { value: 'computer_vision', label: 'Computer Vision' },
                { value: 'recommendation', label: 'Recommendation Systems' },
                { value: 'anomaly_detection', label: 'Anomaly Detection' },
                { value: 'llm', label: 'Large Language Models' },
              ]}
              value={data.models.types[0] || ''}
              onChange={(value) => setData({
                ...data,
                models: { ...data.models, types: value ? [value] : [] }
              })}
              required
            />
            
            <Select
              label="AI Frameworks"
              placeholder="Select frameworks you use"
              data={[
                { value: 'tensorflow', label: 'TensorFlow' },
                { value: 'pytorch', label: 'PyTorch' },
                { value: 'scikit-learn', label: 'Scikit-learn' },
                { value: 'huggingface', label: 'Hugging Face' },
                { value: 'openai', label: 'OpenAI' },
                { value: 'anthropic', label: 'Anthropic' },
                { value: 'other', label: 'Other' },
              ]}
              value={data.models.frameworks[0] || ''}
              onChange={(value) => setData({
                ...data,
                models: { ...data.models, frameworks: value ? [value] : [] }
              })}
              required
            />
          </Stack>
        </Stepper.Step>

        {/* Step 4: Preferences */}
        <Stepper.Step label="Preferences" description="Configure settings" icon={<IconSettings size="1.2rem" />}>
          <Stack gap="md" mt="md">
            <Title order={3}>Configure your preferences</Title>
            <Text c="dimmed">Set up how you want to receive alerts and reports</Text>
            
            <Select
              label="Alert Channels"
              placeholder="How do you want to receive alerts?"
              data={[
                { value: 'email', label: 'Email' },
                { value: 'slack', label: 'Slack' },
                { value: 'teams', label: 'Microsoft Teams' },
                { value: 'webhook', label: 'Webhook' },
                { value: 'dashboard', label: 'Dashboard Only' },
              ]}
              value={data.preferences.alertChannels[0] || ''}
              onChange={(value) => setData({
                ...data,
                preferences: { ...data.preferences, alertChannels: value ? [value] : [] }
              })}
              required
            />
            
            <Select
              label="Reporting Frequency"
              placeholder="How often do you want reports?"
              data={[
                { value: 'daily', label: 'Daily' },
                { value: 'weekly', label: 'Weekly' },
                { value: 'monthly', label: 'Monthly' },
                { value: 'quarterly', label: 'Quarterly' },
                { value: 'on-demand', label: 'On Demand Only' },
              ]}
              value={data.preferences.reportingFrequency}
              onChange={(value) => setData({
                ...data,
                preferences: { ...data.preferences, reportingFrequency: value || '' }
              })}
              required
            />
            
            <Select
              label="Data Retention"
              placeholder="How long should we keep your data?"
              data={[
                { value: '30-days', label: '30 Days' },
                { value: '90-days', label: '90 Days' },
                { value: '1-year', label: '1 Year' },
                { value: '2-years', label: '2 Years' },
                { value: 'indefinite', label: 'Indefinite' },
              ]}
              value={data.preferences.dataRetention}
              onChange={(value) => setData({
                ...data,
                preferences: { ...data.preferences, dataRetention: value || '' }
              })}
              required
            />
          </Stack>
        </Stepper.Step>

        {/* Step 5: AI Recommendations */}
        <Stepper.Step label="AI Recommendations" description="Get personalized setup" icon={<IconSparkles size="1.2rem" />}>
          <Stack gap="md" mt="md">
            <Title order={3}>AI-Powered Recommendations</Title>
            <Text c="dimmed">Based on your inputs, here are our AI recommendations</Text>
            
            {!aiRecommendations && !isGeneratingRecommendations && (
              <Box>
                <Alert icon={<IconInfoCircle size="1rem" />} title="Ready to generate recommendations" color="blue">
                  Click the button below to get personalized AI recommendations based on your organization profile.
                </Alert>
                <Button
                  fullWidth
                  size="lg"
                  leftSection={<IconSparkles size="1.2rem" />}
                  onClick={generateAIRecommendations}
                  mt="md"
                >
                  Generate AI Recommendations
                </Button>
              </Box>
            )}
            
            {isGeneratingRecommendations && (
              <Box>
                <Alert icon={<IconRobot size="1rem" />} title="AI is analyzing your profile..." color="blue">
                  Our AI is processing your information to provide personalized recommendations.
                </Alert>
                <Progress value={75} animated mt="md" />
              </Box>
            )}
            
            {aiRecommendations && (
              <Stack gap="md">
                {/* Personalized Insights */}
                <Card withBorder p="md" bg="blue.0">
                  <Title order={4} mb="md" c="blue.7">AI-Powered Insights</Title>
                  <Stack gap="sm">
                    {aiRecommendations.personalizedInsights.map((insight: string, index: number) => (
                      <Alert key={index} color="blue" variant="light" icon={<IconSparkles size="1rem" />}>
                        <Text size="sm">{insight}</Text>
                      </Alert>
                    ))}
                  </Stack>
                </Card>

                <Card withBorder p="md">
                  <Title order={4} mb="md">Priority Features</Title>
                  <Stack gap="sm">
                    {aiRecommendations.priorityFeatures.map((feature: any, index: number) => (
                      <Group key={index} justify="space-between">
                        <Box>
                          <Text fw={500}>{feature.name}</Text>
                          <Text size="sm" c="dimmed">{feature.reason}</Text>
                        </Box>
                        <Badge 
                          color={feature.priority === 'critical' ? 'red' : feature.priority === 'high' ? 'orange' : 'yellow'} 
                          variant="light"
                        >
                          {feature.priority}
                        </Badge>
                      </Group>
                    ))}
                  </Stack>
                </Card>
                
                <Card withBorder p="md">
                  <Title order={4} mb="md">Suggested Workflow</Title>
                  <List spacing="sm">
                    {aiRecommendations.suggestedWorkflow.map((step: string, index: number) => (
                      <List.Item key={index} icon={<IconCheck size="1rem" />}>
                        {step}
                      </List.Item>
                    ))}
                  </List>
                </Card>
                
                <Card withBorder p="md">
                  <Title order={4} mb="md">Risk Assessment</Title>
                  <Group justify="space-between" mb="md">
                    <Text>Overall Risk Level</Text>
                    <Badge color={aiRecommendations.riskAssessment.overallRisk === 'Low' ? 'green' : 'yellow'} variant="light">
                      {aiRecommendations.riskAssessment.overallRisk}
                    </Badge>
                  </Group>
                  <Text size="sm" c="dimmed" mb="sm">Key Risks Identified:</Text>
                  <List spacing="xs">
                    {aiRecommendations.riskAssessment.keyRisks.map((risk: string, index: number) => (
                      <List.Item key={index} icon={<IconAlertTriangle size="0.8rem" />}>
                        {risk}
                      </List.Item>
                    ))}
                  </List>
                </Card>
              </Stack>
            )}
          </Stack>
        </Stepper.Step>
      </Stepper>

      <Group justify="space-between" mt="xl">
        <Button variant="default" onClick={prevStep} disabled={active === 0}>
          <IconArrowLeft size="1rem" />
          Previous
        </Button>
        
        {active < 4 ? (
          <Button onClick={nextStep}>
            Next
            <IconArrowRight size="1rem" />
          </Button>
        ) : (
          <Button onClick={onClose} leftSection={<IconRocket size="1rem" />}>
            Complete Setup
          </Button>
        )}
      </Group>
    </Modal>
  );
}
