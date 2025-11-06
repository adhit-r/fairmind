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
  Select, 
  MultiSelect,
  Slider, 
  Switch,
  Badge,
  Progress,
  Tabs,
  Card,
  ActionIcon,
  Tooltip,
  Alert
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
  IconX
} from '@tabler/icons-react';
import ErrorBoundary from '../ErrorBoundary';

interface BiasDataPoint {
  x: number;
  y: number;
  z: number;
  bias_score: number;
  group: string;
  timestamp: string;
  confidence: number;
}

interface AdvancedBiasVisualizationProps {
  data?: BiasDataPoint[];
  analysisType?: 'causal' | 'counterfactual' | 'intersectional' | 'adversarial' | 'temporal' | 'contextual';
  onAnalysisComplete?: (results: any) => void;
}

const AdvancedBiasVisualization: React.FC<AdvancedBiasVisualizationProps> = ({
  data = [],
  analysisType: initialAnalysisType = 'causal',
  onAnalysisComplete
}) => {
  const [analysisType, setAnalysisType] = useState<'causal' | 'counterfactual' | 'intersectional' | 'adversarial' | 'temporal' | 'contextual'>(initialAnalysisType);
  const [selectedView, setSelectedView] = useState<'3d' | 'heatmap' | 'timeline' | 'network'>('3d');
  const [selectedGroups, setSelectedGroups] = useState<string[]>([]);
  const [timeRange, setTimeRange] = useState<[number, number]>([0, 100]);
  const [biasThreshold, setBiasThreshold] = useState(0.3);
  const [showConfidence, setShowConfidence] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState<any>(null);

  // Mock data for demonstration
  const mockData: BiasDataPoint[] = [
    { x: 0.2, y: 0.3, z: 0.1, bias_score: 0.15, group: 'gender', timestamp: '2024-01-01', confidence: 0.85 },
    { x: 0.4, y: 0.6, z: 0.2, bias_score: 0.35, group: 'race', timestamp: '2024-01-02', confidence: 0.92 },
    { x: 0.1, y: 0.8, z: 0.3, bias_score: 0.45, group: 'age', timestamp: '2024-01-03', confidence: 0.78 },
    { x: 0.7, y: 0.2, z: 0.4, bias_score: 0.25, group: 'education', timestamp: '2024-01-04', confidence: 0.88 },
    { x: 0.5, y: 0.5, z: 0.5, bias_score: 0.55, group: 'intersectional', timestamp: '2024-01-05', confidence: 0.95 },
  ];

  const displayData = data.length > 0 ? data : mockData;

  const availableGroups = Array.from(new Set(displayData.map(d => d.group)));

  useEffect(() => {
    if (selectedGroups.length === 0) {
      setSelectedGroups(availableGroups);
    }
  }, [availableGroups, selectedGroups.length]);

  const filteredData = displayData.filter(d => 
    selectedGroups.includes(d.group) &&
    d.bias_score >= biasThreshold
  );

  const handleRunAnalysis = async () => {
    setIsAnalyzing(true);
    
    // Simulate analysis
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    const results = {
      analysis_type: analysisType,
      overall_bias_score: Math.max(...filteredData.map(d => d.bias_score)),
      risk_level: Math.max(...filteredData.map(d => d.bias_score)) > 0.5 ? 'high' : 'medium',
      recommendations: [
        'Implement bias mitigation strategies',
        'Monitor intersectional groups',
        'Add fairness constraints to model training'
      ],
      detailed_results: filteredData
    };
    
    setAnalysisResults(results);
    setIsAnalyzing(false);
    
    if (onAnalysisComplete) {
      onAnalysisComplete(results);
    }
  };

  const render3DVisualization = () => (
    <Paper p="md" style={{ height: '400px', position: 'relative' }}>
      <Title order={4} mb="md">3D Bias Landscape</Title>
      <div style={{ 
        width: '100%', 
        height: '300px', 
        background: 'linear-gradient(45deg, #1a1a1a 0%, #2d2d2d 100%)',
        borderRadius: '8px',
        position: 'relative',
        overflow: 'hidden'
      }}>
        {filteredData.map((point, index) => (
          <div
            key={index}
            style={{
              position: 'absolute',
              left: `${point.x * 100}%`,
              top: `${point.y * 100}%`,
              width: '12px',
              height: '12px',
              borderRadius: '50%',
              background: `hsl(${point.bias_score * 120}, 70%, 50%)`,
              transform: `translateZ(${point.z * 20}px)`,
              boxShadow: `0 0 ${point.bias_score * 20}px hsl(${point.bias_score * 120}, 70%, 50%)`,
              cursor: 'pointer',
              transition: 'all 0.3s ease'
            }}
            title={`${point.group}: ${point.bias_score.toFixed(3)}`}
          />
        ))}
        
        {/* 3D Grid Lines */}
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} style={{
            position: 'absolute',
            left: `${i * 25}%`,
            top: 0,
            bottom: 0,
            width: '1px',
            background: 'rgba(255, 255, 255, 0.1)',
            transform: `rotateY(45deg)`
          }} />
        ))}
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} style={{
            position: 'absolute',
            top: `${i * 25}%`,
            left: 0,
            right: 0,
            height: '1px',
            background: 'rgba(255, 255, 255, 0.1)',
            transform: `rotateX(45deg)`
          }} />
        ))}
      </div>
      <Text size="sm" c="dimmed" mt="sm">
        Each point represents a bias measurement in 3D space. Color intensity indicates bias severity.
      </Text>
    </Paper>
  );

  const renderHeatmap = () => (
    <Paper p="md" style={{ height: '400px' }}>
      <Title order={4} mb="md">Bias Heatmap</Title>
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(10, 1fr)', 
        gap: '2px',
        height: '300px'
      }}>
        {Array.from({ length: 100 }).map((_, index) => {
          const x = index % 10;
          const y = Math.floor(index / 10);
          const biasValue = Math.random() * 0.8; // Mock data
          
          return (
            <div
              key={index}
              style={{
                background: `hsl(${biasValue * 120}, 70%, 50%)`,
                borderRadius: '2px',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
              title={`Position (${x}, ${y}): Bias ${biasValue.toFixed(3)}`}
            />
          );
        })}
      </div>
      <Group justify="space-between" mt="sm">
        <Text size="sm" c="dimmed">Low Bias</Text>
        <Text size="sm" c="dimmed">High Bias</Text>
      </Group>
    </Paper>
  );

  const renderTimeline = () => (
    <Paper p="md" style={{ height: '400px' }}>
      <Title order={4} mb="md">Temporal Bias Analysis</Title>
      <div style={{ height: '300px', position: 'relative' }}>
        {availableGroups.map((group, groupIndex) => {
          const groupData = filteredData.filter(d => d.group === group);
          return (
            <div key={group} style={{ marginBottom: '20px' }}>
              <Text size="sm" mb="xs">{group}</Text>
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '10px',
                height: '30px'
              }}>
                {Array.from({ length: 30 }).map((_, dayIndex) => {
                  const dayData = groupData.find(d => 
                    new Date(d.timestamp).getDate() === dayIndex + 1
                  );
                  const biasValue = dayData?.bias_score || Math.random() * 0.3;
                  
                  return (
                    <div
                      key={dayIndex}
                      style={{
                        width: '8px',
                        height: `${biasValue * 100}%`,
                        background: `hsl(${biasValue * 120}, 70%, 50%)`,
                        borderRadius: '1px',
                        cursor: 'pointer'
                      }}
                      title={`Day ${dayIndex + 1}: ${biasValue.toFixed(3)}`}
                    />
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </Paper>
  );

  const renderNetwork = () => (
    <Paper p="md" style={{ height: '400px' }}>
      <Title order={4} mb="md">Bias Network Analysis</Title>
      <div style={{ 
        height: '300px', 
        position: 'relative',
        background: 'linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%)',
        borderRadius: '8px',
        overflow: 'hidden'
      }}>
        {availableGroups.map((group, index) => {
          const angle = (index * 2 * Math.PI) / availableGroups.length;
          const radius = 100;
          const x = 150 + radius * Math.cos(angle);
          const y = 150 + radius * Math.sin(angle);
          
          return (
            <div key={group}>
              {/* Node */}
              <div
                style={{
                  position: 'absolute',
                  left: x - 15,
                  top: y - 15,
                  width: '30px',
                  height: '30px',
                  borderRadius: '50%',
                  background: `hsl(${index * 60}, 70%, 50%)`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  boxShadow: '0 0 20px rgba(255, 255, 255, 0.3)'
                }}
                title={group}
              >
                <Text size="xs" c="white" fw="bold">
                  {group.charAt(0).toUpperCase()}
                </Text>
              </div>
              
              {/* Connections */}
              {availableGroups.slice(index + 1).map((otherGroup, otherIndex) => {
                const otherAngle = ((index + otherIndex + 1) * 2 * Math.PI) / availableGroups.length;
                const otherX = 150 + radius * Math.cos(otherAngle);
                const otherY = 150 + radius * Math.sin(otherAngle);
                
                return (
                  <div
                    key={`${group}-${otherGroup}`}
                    style={{
                      position: 'absolute',
                      left: x,
                      top: y,
                      width: Math.sqrt((otherX - x) ** 2 + (otherY - y) ** 2),
                      height: '2px',
                      background: 'rgba(255, 255, 255, 0.3)',
                      transformOrigin: '0 0',
                      transform: `rotate(${Math.atan2(otherY - y, otherX - x)}rad)`
                    }}
                  />
                );
              })}
            </div>
          );
        })}
        
        {/* Center node */}
        <div
          style={{
            position: 'absolute',
            left: 135,
            top: 135,
            width: '30px',
            height: '30px',
            borderRadius: '50%',
            background: 'linear-gradient(45deg, #ffd700, #ffed4e)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 30px rgba(255, 215, 0, 0.5)'
          }}
        >
          <IconBrain size={16} color="black" />
        </div>
      </div>
    </Paper>
  );

  const renderAnalysisResults = () => {
    if (!analysisResults) return null;

    return (
      <Paper p="md" mt="md">
        <Title order={4} mb="md">Analysis Results</Title>
        <Grid>
          <Grid.Col span={6}>
            <Card>
              <Group justify="space-between" mb="sm">
                <Text fw="bold">Overall Bias Score</Text>
                <Badge 
                  color={analysisResults.risk_level === 'high' ? 'red' : 'yellow'}
                  variant="light"
                >
                  {analysisResults.risk_level}
                </Badge>
              </Group>
              <Progress 
                value={analysisResults.overall_bias_score * 100} 
                color={analysisResults.risk_level === 'high' ? 'red' : 'yellow'}
                size="lg"
              />
              <Text size="sm" c="dimmed" mt="xs">
                {analysisResults.overall_bias_score.toFixed(3)}
              </Text>
            </Card>
          </Grid.Col>
          <Grid.Col span={6}>
            <Card>
              <Text fw="bold" mb="sm">Recommendations</Text>
              <Stack gap="xs">
                {analysisResults.recommendations.map((rec: string, index: number) => (
                  <Group key={index} gap="xs">
                    <IconCheck size={16} color="green" />
                    <Text size="sm">{rec}</Text>
                  </Group>
                ))}
              </Stack>
            </Card>
          </Grid.Col>
        </Grid>
      </Paper>
    );
  };

  return (
    <ErrorBoundary context="AdvancedBiasVisualization">
      <Stack>
        <Paper p="md">
          <Group justify="space-between" mb="md">
            <Title order={3}>
              <Group gap="sm">
                <Icon3dCubeSphere size={24} />
                Advanced Bias Visualization
              </Group>
            </Title>
            <Group>
              <Button
                leftSection={<IconRefresh size={16} />}
                onClick={handleRunAnalysis}
                loading={isAnalyzing}
                variant="light"
              >
                Run Analysis
              </Button>
              <Button
                leftSection={<IconDownload size={16} />}
                variant="outline"
              >
                Export
              </Button>
            </Group>
          </Group>

        <Tabs value={selectedView} onChange={(value) => setSelectedView(value as any)}>
          <Tabs.List>
            <Tabs.Tab value="3d" leftSection={<Icon3dCubeSphere size={16} />}>
              3D Landscape
            </Tabs.Tab>
            <Tabs.Tab value="heatmap" leftSection={<IconChartBar size={16} />}>
              Heatmap
            </Tabs.Tab>
            <Tabs.Tab value="timeline" leftSection={<IconUsers size={16} />}>
              Timeline
            </Tabs.Tab>
            <Tabs.Tab value="network" leftSection={<IconBrain size={16} />}>
              Network
            </Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="3d" pt="md">
            {render3DVisualization()}
          </Tabs.Panel>

          <Tabs.Panel value="heatmap" pt="md">
            {renderHeatmap()}
          </Tabs.Panel>

          <Tabs.Panel value="timeline" pt="md">
            {renderTimeline()}
          </Tabs.Panel>

          <Tabs.Panel value="network" pt="md">
            {renderNetwork()}
          </Tabs.Panel>
        </Tabs>
      </Paper>

      <Paper p="md">
        <Title order={4} mb="md">Analysis Controls</Title>
        <Grid>
          <Grid.Col span={4}>
            <Stack>
              <Text fw="bold">Analysis Type</Text>
              <Select
                value={analysisType}
                onChange={(value) => value && setAnalysisType(value as any)}
                data={[
                  { value: 'causal', label: 'Causal Analysis' },
                  { value: 'counterfactual', label: 'Counterfactual' },
                  { value: 'intersectional', label: 'Intersectional' },
                  { value: 'adversarial', label: 'Adversarial' },
                  { value: 'temporal', label: 'Temporal' },
                  { value: 'contextual', label: 'Contextual' }
                ]}
              />
            </Stack>
          </Grid.Col>
          <Grid.Col span={4}>
            <Stack>
              <Text fw="bold">Groups to Analyze</Text>
              <MultiSelect
                value={selectedGroups}
                onChange={setSelectedGroups}
                data={availableGroups.map(group => ({ value: group, label: group }))}
                placeholder="Select groups"
              />
            </Stack>
          </Grid.Col>
          <Grid.Col span={4}>
            <Stack>
              <Text fw="bold">Bias Threshold</Text>
              <Slider
                value={biasThreshold}
                onChange={setBiasThreshold}
                min={0}
                max={1}
                step={0.01}
                marks={[
                  { value: 0, label: '0' },
                  { value: 0.5, label: '0.5' },
                  { value: 1, label: '1' }
                ]}
              />
              <Text size="sm" c="dimmed">
                Current: {biasThreshold.toFixed(2)}
              </Text>
            </Stack>
          </Grid.Col>
        </Grid>

        <Group mt="md">
          <Switch
            label="Show Confidence Intervals"
            checked={showConfidence}
            onChange={(event) => setShowConfidence(event.currentTarget.checked)}
          />
        </Group>
      </Paper>

        {analysisResults && renderAnalysisResults()}
      </Stack>
    </ErrorBoundary>
  );
};

export default AdvancedBiasVisualization;
