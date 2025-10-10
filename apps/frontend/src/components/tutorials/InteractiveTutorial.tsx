"use client";

import React, { useState, useEffect } from 'react';
import { 
  Paper, 
  Title, 
  Text, 
  Group, 
  Stack, 
  Grid, 
  Button, 
  Badge,
  Progress,
  Card,
  ActionIcon,
  Tooltip,
  Alert,
  Stepper,
  Modal,
  List,
  ThemeIcon,
  Code,
  Blockquote,
  Divider,
  Textarea,
  NumberInput,
  Select,
  Switch,
  Tabs,
  Accordion,
  Highlight,
  Mark
} from '@mantine/core';
import { 
  IconBrain, 
  IconShield, 
  IconUsers, 
  IconChartBar, 
  Icon3dCubeSphere,
  IconRefresh,
  IconDownload,
  IconSettings,
  IconAlertTriangle,
  IconCheck,
  IconX,
  IconBell,
  IconActivity,
  IconTrendingUp,
  IconTrendingDown,
  IconEye,
  IconCode,
  IconBook,
  IconVideo,
  IconPresentation,
  IconTarget,
  IconFlask,
  IconDatabase,
  IconApi,
  IconRocket,
  IconStar,
  IconAward,
  IconBulb,
  IconGavel,
  IconScale,
  IconMicroscope,
  IconChartLine,
  IconNetwork,
  IconClock,
  IconWorld,
  IconChevronRight,
  IconChevronLeft,
  IconHelp,
  IconInfoCircle,
  IconAlertCircle
} from '@tabler/icons-react';

interface TutorialStep {
  id: string;
  title: string;
  description: string;
  content: React.ReactNode;
  interactive?: boolean;
  codeExample?: string;
  expectedResult?: any;
  hints?: string[];
  difficulty: 'beginner' | 'intermediate' | 'advanced';
}

interface Tutorial {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  category: 'bias' | 'integration' | 'visualization' | 'monitoring';
  estimatedTime: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  steps: TutorialStep[];
  prerequisites: string[];
  learningObjectives: string[];
}

const InteractiveTutorial: React.FC<{ tutorialId?: string }> = ({ tutorialId }) => {
  const [currentTutorial, setCurrentTutorial] = useState<string>(tutorialId || 'causal-analysis');
  const [currentStep, setCurrentStep] = useState(0);
  const [userInput, setUserInput] = useState<any>({});
  const [showHints, setShowHints] = useState(false);
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());
  const [showResults, setShowResults] = useState(false);

  const tutorials: Tutorial[] = [
    {
      id: 'causal-analysis',
      title: 'Causal Bias Analysis',
      description: 'Learn to detect bias in treatment effects using causal inference',
      icon: <IconMicroscope size={24} />,
      category: 'bias',
      estimatedTime: '15 minutes',
      difficulty: 'advanced',
      prerequisites: ['Basic statistics', 'Understanding of bias', 'Causal inference concepts'],
      learningObjectives: [
        'Understand causal inference in bias detection',
        'Learn to identify confounding variables',
        'Interpret treatment effects and confidence intervals',
        'Apply robustness testing methods'
      ],
      steps: [
        {
          id: 'introduction',
          title: 'Introduction to Causal Bias Analysis',
          description: 'Understanding the fundamentals of causal inference in bias detection',
          difficulty: 'beginner',
          content: (
            <Stack>
              <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
                <Text fw="bold">What is Causal Bias Analysis?</Text>
                <Text size="sm">
                  Causal bias analysis uses causal inference methods to detect bias in treatment effects, 
                  controlling for confounding variables and providing statistical rigor.
                </Text>
              </Alert>
              
              <Text>
                In this tutorial, you'll learn how to:
              </Text>
              <List spacing="xs">
                <List.Item icon={<IconCheck size={14} color="green" />}>
                  Identify treatment and outcome variables
                </List.Item>
                <List.Item icon={<IconCheck size={14} color="green" />}>
                  Control for confounding factors
                </List.Item>
                <List.Item icon={<IconCheck size={14} color="green" />}>
                  Calculate treatment effects with confidence intervals
                </List.Item>
                <List.Item icon={<IconCheck size={14} color="green" />}>
                  Assess robustness and statistical significance
                </List.Item>
              </List>
              
              <Blockquote color="blue" icon={<IconBulb size={16} />}>
                <Text size="sm">
                  <strong>Key Concept:</strong> Causal bias analysis goes beyond correlation to establish 
                  causal relationships between treatments and outcomes, providing stronger evidence of bias.
                </Text>
              </Blockquote>
            </Stack>
          )
        },
        {
          id: 'data-setup',
          title: 'Setting Up Your Data',
          description: 'Prepare your dataset for causal analysis',
          difficulty: 'intermediate',
          interactive: true,
          content: (
            <Stack>
              <Text>
                Let's set up a sample dataset for causal bias analysis. We'll analyze whether a hiring 
                algorithm shows bias in treatment effects.
              </Text>
              
              <Grid>
                <Grid.Col span={6}>
                  <Stack>
                    <Text fw="bold">Treatment Variable</Text>
                    <Select
                      label="Select treatment variable"
                      placeholder="Choose treatment"
                      data={[
                        { value: 'interview_score', label: 'Interview Score' },
                        { value: 'resume_quality', label: 'Resume Quality' },
                        { value: 'education_level', label: 'Education Level' }
                      ]}
                      value={userInput.treatment || ''}
                      onChange={(value) => setUserInput({...userInput, treatment: value})}
                    />
                  </Stack>
                </Grid.Col>
                <Grid.Col span={6}>
                  <Stack>
                    <Text fw="bold">Outcome Variable</Text>
                    <Select
                      label="Select outcome variable"
                      placeholder="Choose outcome"
                      data={[
                        { value: 'hired', label: 'Hired (Binary)' },
                        { value: 'salary_offer', label: 'Salary Offer' },
                        { value: 'job_level', label: 'Job Level' }
                      ]}
                      value={userInput.outcome || ''}
                      onChange={(value) => setUserInput({...userInput, outcome: value})}
                    />
                  </Stack>
                </Grid.Col>
              </Grid>
              
              <Text fw="bold">Protected Attributes</Text>
              <Group>
                <Switch
                  label="Gender"
                  checked={userInput.protected_gender || false}
                  onChange={(event) => setUserInput({...userInput, protected_gender: event.currentTarget.checked})}
                />
                <Switch
                  label="Race"
                  checked={userInput.protected_race || false}
                  onChange={(event) => setUserInput({...userInput, protected_race: event.currentTarget.checked})}
                />
                <Switch
                  label="Age"
                  checked={userInput.protected_age || false}
                  onChange={(event) => setUserInput({...userInput, protected_age: event.currentTarget.checked})}
                />
              </Group>
              
              {showHints && (
                <Alert icon={<IconHelp size={16} />} color="yellow" variant="light">
                  <Text size="sm">
                    <strong>Hint:</strong> Choose variables that represent a clear treatment (intervention) 
                    and outcome (result). Protected attributes should be characteristics that shouldn't 
                    influence the outcome.
                  </Text>
                </Alert>
              )}
            </Stack>
          ),
          hints: [
            'Treatment variables should represent interventions or decisions',
            'Outcome variables should be the results you want to analyze',
            'Protected attributes are characteristics that shouldn\'t influence outcomes'
          ]
        },
        {
          id: 'confounding-control',
          title: 'Controlling for Confounding Variables',
          description: 'Identify and control for confounding factors',
          difficulty: 'advanced',
          interactive: true,
          content: (
            <Stack>
              <Text>
                Confounding variables can bias your causal analysis. Let's identify potential confounders 
                and control for them.
              </Text>
              
              <Text fw="bold">Potential Confounding Variables</Text>
              <Group>
                <Switch
                  label="Experience Level"
                  checked={userInput.confound_experience || false}
                  onChange={(event) => setUserInput({...userInput, confound_experience: event.currentTarget.checked})}
                />
                <Switch
                  label="Education Quality"
                  checked={userInput.confound_education || false}
                  onChange={(event) => setUserInput({...userInput, confound_education: event.currentTarget.checked})}
                />
                <Switch
                  label="Industry Background"
                  checked={userInput.confound_industry || false}
                  onChange={(event) => setUserInput({...userInput, confound_industry: event.currentTarget.checked})}
                />
                <Switch
                  label="Geographic Location"
                  checked={userInput.confound_location || false}
                  onChange={(event) => setUserInput({...userInput, confound_location: event.currentTarget.checked})}
                />
              </Group>
              
              <Alert icon={<IconAlertCircle size={16} />} color="orange" variant="light">
                <Text fw="bold">Confounding Check</Text>
                <Text size="sm">
                  A variable is a confounder if it:
                </Text>
                <List size="sm" spacing="xs">
                  <List.Item>• Is associated with the treatment</List.Item>
                  <List.Item>• Is associated with the outcome</List.Item>
                  <List.Item>• Is not on the causal pathway</List.Item>
                </List>
              </Alert>
              
              {showHints && (
                <Alert icon={<IconHelp size={16} />} color="yellow" variant="light">
                  <Text size="sm">
                    <strong>Hint:</strong> Look for variables that might influence both your treatment 
                    and outcome variables. These need to be controlled for to get unbiased estimates.
                  </Text>
                </Alert>
              )}
            </Stack>
          ),
          hints: [
            'Confounders affect both treatment and outcome',
            'Not controlling for confounders can lead to biased results',
            'Use domain knowledge to identify potential confounders'
          ]
        },
        {
          id: 'analysis-execution',
          title: 'Running the Causal Analysis',
          description: 'Execute the causal bias analysis and interpret results',
          difficulty: 'advanced',
          interactive: true,
          content: (
            <Stack>
              <Text>
                Now let's run the causal analysis with your selected variables and confounders.
              </Text>
              
              <Button
                onClick={() => setShowResults(true)}
                size="lg"
                fullWidth
              >
                Run Causal Analysis
              </Button>
              
              {showResults && (
                <Card p="md" style={{ background: 'rgba(0, 255, 0, 0.1)' }}>
                  <Title order={4} mb="md">Analysis Results</Title>
                  
                  <Grid>
                    <Grid.Col span={6}>
                      <Stack>
                        <Text fw="bold">Treatment Effect</Text>
                        <Text size="xl" c="blue">0.15</Text>
                        <Text size="sm" c="dimmed">(0.12, 0.18)</Text>
                      </Stack>
                    </Grid.Col>
                    <Grid.Col span={6}>
                      <Stack>
                        <Text fw="bold">P-value</Text>
                        <Text size="xl" c="green">0.003</Text>
                        <Text size="sm" c="dimmed">Statistically significant</Text>
                      </Stack>
                    </Grid.Col>
                  </Grid>
                  
                  <Divider my="md" />
                  
                  <Stack>
                    <Text fw="bold">Robustness Score</Text>
                    <Progress value={85} size="lg" color="green" />
                    <Text size="sm" c="dimmed">High robustness - results are reliable</Text>
                  </Stack>
                  
                  <Divider my="md" />
                  
                  <Stack>
                    <Text fw="bold">Confounding Factors Detected</Text>
                    <List size="sm">
                      <List.Item>• Experience Level (correlation: 0.45)</List.Item>
                      <List.Item>• Education Quality (correlation: 0.32)</List.Item>
                    </List>
                  </Stack>
                  
                  <Alert icon={<IconCheck size={16} />} color="green" variant="light" mt="md">
                    <Text fw="bold">Interpretation</Text>
                    <Text size="sm">
                      The treatment effect of 0.15 is statistically significant (p &lt; 0.01), 
                      indicating potential bias. The high robustness score suggests reliable results.
                    </Text>
                  </Alert>
                </Card>
              )}
              
              {showHints && (
                <Alert icon={<IconHelp size={16} />} color="yellow" variant="light">
                  <Text size="sm">
                    <strong>Hint:</strong> Look for statistically significant treatment effects (p &lt; 0.05) 
                    and high robustness scores (&gt; 0.7) for reliable results.
                  </Text>
                </Alert>
              )}
            </Stack>
          ),
          hints: [
            'Treatment effect shows the magnitude of bias',
            'P-value indicates statistical significance',
            'Robustness score shows result reliability'
          ]
        },
        {
          id: 'interpretation',
          title: 'Interpreting Results and Recommendations',
          description: 'Understand what the results mean and how to act on them',
          difficulty: 'intermediate',
          content: (
            <Stack>
              <Text>
                Let's interpret the causal analysis results and generate actionable recommendations.
              </Text>
              
              <Alert icon={<IconAlertTriangle size={16} />} color="red" variant="light">
                <Text fw="bold">Bias Detected</Text>
                <Text size="sm">
                  The analysis reveals a statistically significant treatment effect of 0.15, 
                  indicating potential bias in the hiring process.
                </Text>
              </Alert>
              
              <Text fw="bold">Key Findings:</Text>
              <List spacing="xs">
                <List.Item icon={<IconCheck size={14} color="red" />}>
                  Treatment effect: 0.15 (statistically significant)
                </List.Item>
                <List.Item icon={<IconCheck size={14} color="orange" />}>
                  Confounding factors: Experience and education
                </List.Item>
                <List.Item icon={<IconCheck size={14} color="green" />}>
                  Robustness score: 0.85 (high reliability)
                </List.Item>
              </List>
              
              <Text fw="bold">Recommendations:</Text>
              <List spacing="xs">
                <List.Item icon={<IconBulb size={14} color="blue" />}>
                  Investigate the hiring process for bias sources
                </List.Item>
                <List.Item icon={<IconBulb size={14} color="blue" />}>
                  Control for experience and education in future analyses
                </List.Item>
                <List.Item icon={<IconBulb size={14} color="blue" />}>
                  Implement bias mitigation strategies
                </List.Item>
                <List.Item icon={<IconBulb size={14} color="blue" />}>
                  Monitor treatment effects over time
                </List.Item>
              </List>
              
              <Blockquote color="green" icon={<IconBulb size={16} />}>
                <Text size="sm">
                  <strong>Next Steps:</strong> Use these results to inform policy changes, 
                  retrain models, or implement fairness constraints in your system.
                </Text>
              </Blockquote>
            </Stack>
          )
        }
      ]
    },
    {
      id: 'counterfactual-explanations',
      title: 'Counterfactual Explanations',
      description: 'Learn to generate "what-if" scenarios for bias understanding',
      icon: <IconBulb size={24} />,
      category: 'bias',
      estimatedTime: '12 minutes',
      difficulty: 'intermediate',
      prerequisites: ['Basic understanding of bias', 'Familiarity with model predictions'],
      learningObjectives: [
        'Understand counterfactual reasoning in bias detection',
        'Generate minimal interventions for bias mitigation',
        'Interpret feature importance in bias contexts',
        'Create actionable explanations for stakeholders'
      ],
      steps: [
        {
          id: 'introduction',
          title: 'Introduction to Counterfactual Explanations',
          description: 'Understanding how "what-if" scenarios help explain bias',
          difficulty: 'beginner',
          content: (
            <Stack>
              <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
                <Text fw="bold">What are Counterfactual Explanations?</Text>
                <Text size="sm">
                  Counterfactual explanations answer "what-if" questions by showing how changing 
                  certain features would affect model predictions, helping identify bias sources.
                </Text>
              </Alert>
              
              <Text>
                In this tutorial, you'll learn how to:
              </Text>
              <List spacing="xs">
                <List.Item icon={<IconCheck size={14} color="green" />}>
                  Generate counterfactual scenarios
                </List.Item>
                <List.Item icon={<IconCheck size={14} color="green" />}>
                  Identify minimal interventions
                </List.Item>
                <List.Item icon={<IconCheck size={14} color="green" />}>
                  Calculate bias magnitude
                </List.Item>
                <List.Item icon={<IconCheck size={14} color="green" />}>
                  Create actionable explanations
                </List.Item>
              </List>
              
              <Blockquote color="blue" icon={<IconBulb size={16} />}>
                <Text size="sm">
                  <strong>Key Concept:</strong> Counterfactual explanations help answer "What would happen 
                  if we changed this protected attribute?" providing clear, actionable insights.
                </Text>
              </Blockquote>
            </Stack>
          )
        },
        {
          id: 'scenario-setup',
          title: 'Setting Up Counterfactual Scenarios',
          description: 'Create scenarios to test bias in model predictions',
          difficulty: 'intermediate',
          interactive: true,
          content: (
            <Stack>
              <Text>
                Let's set up a scenario to test for gender bias in a loan approval model.
              </Text>
              
              <Grid>
                <Grid.Col span={6}>
                  <Stack>
                    <Text fw="bold">Original Scenario</Text>
                    <NumberInput
                      label="Income ($)"
                      value={userInput.income || 50000}
                      onChange={(value) => setUserInput({...userInput, income: value})}
                    />
                    <NumberInput
                      label="Credit Score"
                      value={userInput.credit_score || 650}
                      onChange={(value) => setUserInput({...userInput, credit_score: value})}
                    />
                    <Select
                      label="Gender"
                      value={userInput.gender || 'female'}
                      onChange={(value) => setUserInput({...userInput, gender: value})}
                      data={[
                        { value: 'female', label: 'Female' },
                        { value: 'male', label: 'Male' }
                      ]}
                    />
                  </Stack>
                </Grid.Col>
                <Grid.Col span={6}>
                  <Stack>
                    <Text fw="bold">Counterfactual Scenario</Text>
                    <NumberInput
                      label="Income ($)"
                      value={userInput.cf_income || 50000}
                      onChange={(value) => setUserInput({...userInput, cf_income: value})}
                    />
                    <NumberInput
                      label="Credit Score"
                      value={userInput.cf_credit_score || 650}
                      onChange={(value) => setUserInput({...userInput, cf_credit_score: value})}
                    />
                    <Select
                      label="Gender"
                      value={userInput.cf_gender || 'male'}
                      onChange={(value) => setUserInput({...userInput, cf_gender: value})}
                      data={[
                        { value: 'female', label: 'Female' },
                        { value: 'male', label: 'Male' }
                      ]}
                    />
                  </Stack>
                </Grid.Col>
              </Grid>
              
              <Alert icon={<IconBulb size={16} />} color="yellow" variant="light">
                <Text fw="bold">Scenario Design</Text>
                <Text size="sm">
                  Keep all features the same except for the protected attribute you want to test. 
                  This isolates the effect of that attribute on the prediction.
                </Text>
              </Alert>
            </Stack>
          )
        },
        {
          id: 'analysis-execution',
          title: 'Running Counterfactual Analysis',
          description: 'Execute the analysis and compare predictions',
          difficulty: 'intermediate',
          interactive: true,
          content: (
            <Stack>
              <Text>
                Now let's run the counterfactual analysis to see how changing gender affects the loan approval prediction.
              </Text>
              
              <Button
                onClick={() => setShowResults(true)}
                size="lg"
                fullWidth
              >
                Run Counterfactual Analysis
              </Button>
              
              {showResults && (
                <Card p="md" style={{ background: 'rgba(0, 255, 0, 0.1)' }}>
                  <Title order={4} mb="md">Counterfactual Analysis Results</Title>
                  
                  <Grid>
                    <Grid.Col span={6}>
                      <Stack>
                        <Text fw="bold">Original Prediction</Text>
                        <Text size="xl" c="blue">0.65</Text>
                        <Text size="sm" c="dimmed">Female applicant</Text>
                      </Stack>
                    </Grid.Col>
                    <Grid.Col span={6}>
                      <Stack>
                        <Text fw="bold">Counterfactual Prediction</Text>
                        <Text size="xl" c="red">0.78</Text>
                        <Text size="sm" c="dimmed">Male applicant</Text>
                      </Stack>
                    </Grid.Col>
                  </Grid>
                  
                  <Divider my="md" />
                  
                  <Stack>
                    <Text fw="bold">Bias Magnitude</Text>
                    <Text size="xl" c="orange">0.13</Text>
                    <Text size="sm" c="dimmed">13% difference in approval probability</Text>
                  </Stack>
                  
                  <Divider my="md" />
                  
                  <Stack>
                    <Text fw="bold">Feature Importance</Text>
                    <List size="sm">
                      <List.Item>• Gender: 0.13 (high impact)</List.Item>
                      <List.Item>• Income: 0.05 (moderate impact)</List.Item>
                      <List.Item>• Credit Score: 0.03 (low impact)</List.Item>
                    </List>
                  </Stack>
                  
                  <Alert icon={<IconAlertTriangle size={16} />} color="red" variant="light" mt="md">
                    <Text fw="bold">Bias Detected</Text>
                    <Text size="sm">
                      The model shows a 13% bias against female applicants, with gender being the 
                      most important factor in the prediction difference.
                    </Text>
                  </Alert>
                </Card>
              )}
            </Stack>
          )
        }
      ]
    }
  ];

  const currentTutorialData = tutorials.find(t => t.id === currentTutorial);
  const currentStepData = currentTutorialData?.steps[currentStep];

  const nextStep = () => {
    if (currentTutorialData && currentStep < currentTutorialData.steps.length - 1) {
      setCompletedSteps(prev => {
        const newSet = new Set(prev);
        newSet.add(currentStep);
        return newSet;
      });
      setCurrentStep(currentStep + 1);
      setShowResults(false);
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
      setShowResults(false);
    }
  };

  const toggleHints = () => {
    setShowHints(!showHints);
  };

  if (!currentTutorialData) {
    return (
      <Paper p="xl">
        <Title order={2} mb="md">Tutorial Not Found</Title>
        <Text>The requested tutorial could not be found.</Text>
      </Paper>
    );
  }

  return (
    <Stack>
      <Paper p="md">
        <Group justify="space-between" mb="md">
          <Group gap="sm">
            <ThemeIcon size="lg" variant="light" color="blue">
              {currentTutorialData.icon}
            </ThemeIcon>
            <div>
              <Title order={3}>{currentTutorialData.title}</Title>
              <Text c="dimmed">{currentTutorialData.description}</Text>
            </div>
          </Group>
          <Group>
            <Badge color="blue" variant="light">
              {currentTutorialData.estimatedTime}
            </Badge>
            <Badge 
              color={currentTutorialData.difficulty === 'beginner' ? 'green' : 
                     currentTutorialData.difficulty === 'intermediate' ? 'yellow' : 'red'}
              variant="light"
            >
              {currentTutorialData.difficulty}
            </Badge>
          </Group>
        </Group>

        <Progress 
          value={(currentStep / currentTutorialData.steps.length) * 100} 
          size="sm" 
          mb="md"
        />
        
        <Text size="sm" c="dimmed">
          Step {currentStep + 1} of {currentTutorialData.steps.length}
        </Text>
      </Paper>

      <Paper p="md">
        <Group justify="space-between" mb="md">
          <Title order={4}>{currentStepData?.title}</Title>
          <Group>
            <ActionIcon
              variant="light"
              color="yellow"
              onClick={toggleHints}
              title="Toggle Hints"
            >
              <IconHelp size={16} />
            </ActionIcon>
          </Group>
        </Group>
        
        <Text mb="md">{currentStepData?.description}</Text>
        
        {currentStepData?.content}
        
        {currentStepData?.hints && showHints && (
          <Alert icon={<IconHelp size={16} />} color="yellow" variant="light" mt="md">
            <Text fw="bold">Hints:</Text>
            <List size="sm" spacing="xs">
              {currentStepData.hints.map((hint, index) => (
                <List.Item key={index}>{hint}</List.Item>
              ))}
            </List>
          </Alert>
        )}
      </Paper>

      <Paper p="md">
        <Group justify="space-between">
          <Button
            leftSection={<IconChevronLeft size={16} />}
            onClick={prevStep}
            disabled={currentStep === 0}
            variant="outline"
          >
            Previous
          </Button>
          
          <Group>
            <Button
              rightSection={<IconChevronRight size={16} />}
              onClick={nextStep}
              disabled={currentStep === currentTutorialData.steps.length - 1}
            >
              Next
            </Button>
            
            {currentStep === currentTutorialData.steps.length - 1 && (
              <Button
                leftSection={<IconCheck size={16} />}
                color="green"
              >
                Complete Tutorial
              </Button>
            )}
          </Group>
        </Group>
      </Paper>
    </Stack>
  );
};

export default InteractiveTutorial;
