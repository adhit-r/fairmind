'use client';

import { useState } from 'react';
import {
  IconFileAnalytics,
  IconCertificate,
  IconId,
  IconDownload,
  IconLoader,
  IconCheck
} from '@tabler/icons-react';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { reportsService } from '@/services/reports-service';
import { toast } from 'sonner';
import { useModels } from '@/lib/api/hooks/useModels';
import { IconBrain } from '@tabler/icons-react';

export default function ReportsPage() {
  const [loading, setLoading] = useState(false);
  const [generatedFile, setGeneratedFile] = useState<string | null>(null);

  const { data: models, loading: modelsLoading } = useModels();

  // Form State
  const [reportType, setReportType] = useState<string>('bias_audit');
  const [selectedModelId, setSelectedModelId] = useState<string>('');
  const [author, setAuthor] = useState('FairMind User');

  const handleGenerate = async () => {
    try {
      setLoading(true);
      setGeneratedFile(null);

      if (!selectedModelId) {
        toast.error('Please select a model');
        setLoading(false);
        return;
      }

      const selectedModel = models.find(m => m.id === selectedModelId);
      if (!selectedModel) {
        toast.error('Selected model not found');
        setLoading(false);
        return;
      }

      const modelData = {
        name: selectedModel.name,
        version: selectedModel.version,
        model_type: selectedModel.type,
        author: author
      };

      let reportData = {};

      if (reportType === 'bias_audit') {
        reportData = {
          overall_score: 0.85,
          metrics: {
            statistical_parity: 0.05,
            equalized_odds: 0.08,
            disparate_impact: 0.92
          },
          recommendations: [
            "Monitor demographic parity weekly",
            "Retrain with balanced dataset if possible"
          ]
        };
      } else if (reportType === 'compliance_cert') {
        reportData = {
          framework: "EU AI Act",
          status: "Compliant",
          requirements: [
            { name: "Data Governance", status: "Met", evidence: true },
            { name: "Human Oversight", status: "Met", evidence: true },
            { name: "Transparency", status: "Met", evidence: true }
          ]
        };
      } else if (reportType === 'model_card') {
        reportData = {
          license: "Proprietary",
          intended_use: "Credit risk assessment for loan applications.",
          out_of_scope: "Employment screening, insurance pricing.",
          factors: "Demographic groups (race, gender), Income levels, Geographic location",
          metrics: {
            "Accuracy": 0.82,
            "F1 Score": 0.79,
            "False Positive Rate": 0.12
          },
          ethical_considerations: "The model may exhibit bias against certain demographic groups. Regular auditing is required."
        };
      }

      const response = await reportsService.generateReport({
        report_type: reportType as any,
        model_data: modelData,
        report_data: reportData
      });

      if (response.success) {
        setGeneratedFile(response.filename);
        toast.success('Report generated successfully!');
      }
    } catch (error) {
      console.error('Error generating report:', error);
      toast.error('Failed to generate report');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (generatedFile) {
      window.open(reportsService.getDownloadUrl(generatedFile), '_blank');
    }
  };

  return (
    <div className="space-y-6 p-6 max-w-5xl mx-auto">
      <div className="flex flex-col space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">Report Generator</h1>
        <p className="text-muted-foreground">
          Create professional, audit-ready PDF reports for your models.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Report Selection */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Report Configuration</CardTitle>
            <CardDescription>Select report type and customize details.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label>Report Type</Label>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div
                  className={`cursor-pointer border rounded-lg p-4 flex flex-col items-center space-y-2 hover:bg-accent ${reportType === 'bias_audit' ? 'border-primary bg-accent' : ''}`}
                  onClick={() => setReportType('bias_audit')}
                >
                  <IconFileAnalytics className="h-8 w-8 text-blue-500" />
                  <span className="font-medium">Bias Audit</span>
                </div>
                <div
                  className={`cursor-pointer border rounded-lg p-4 flex flex-col items-center space-y-2 hover:bg-accent ${reportType === 'compliance_cert' ? 'border-primary bg-accent' : ''}`}
                  onClick={() => setReportType('compliance_cert')}
                >
                  <IconCertificate className="h-8 w-8 text-green-500" />
                  <span className="font-medium">Compliance Cert</span>
                </div>
                <div
                  className={`cursor-pointer border rounded-lg p-4 flex flex-col items-center space-y-2 hover:bg-accent ${reportType === 'model_card' ? 'border-primary bg-accent' : ''}`}
                  onClick={() => setReportType('model_card')}
                >
                  <IconId className="h-8 w-8 text-purple-500" />
                  <span className="font-medium">Model Card</span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2 md:col-span-2">
                <Label>Select Model</Label>
                <Select
                  value={selectedModelId}
                  onValueChange={setSelectedModelId}
                  disabled={modelsLoading}
                >
                  <SelectTrigger>
                    <SelectValue placeholder={modelsLoading ? "Loading models..." : "Select a model"} />
                  </SelectTrigger>
                  <SelectContent>
                    {models.length === 0 ? (
                      <SelectItem value="none" disabled>No models available</SelectItem>
                    ) : (
                      models.map((model) => (
                        <SelectItem key={model.id} value={model.id}>
                          {model.name} ({model.version})
                        </SelectItem>
                      ))
                    )}
                  </SelectContent>
                </Select>
                {models.length === 0 && !modelsLoading && (
                  <p className="text-sm text-muted-foreground">
                    <IconBrain className="inline h-4 w-4 mr-1" />
                    No models found. <a href="/models" className="underline">Upload a model</a> first.
                  </p>
                )}
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label>Author / Organization</Label>
                <Input value={author} onChange={(e) => setAuthor(e.target.value)} />
              </div>
            </div>
          </CardContent>
          <CardFooter>
            <Button onClick={handleGenerate} disabled={loading} className="w-full md:w-auto">
              {loading ? (
                <>
                  <IconLoader className="mr-2 h-4 w-4 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <IconFileAnalytics className="mr-2 h-4 w-4" />
                  Generate Report
                </>
              )}
            </Button>
          </CardFooter>
        </Card>

        {/* Preview / Download */}
        <div className="space-y-6">
          <Card className="h-full flex flex-col">
            <CardHeader>
              <CardTitle>Download</CardTitle>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col items-center justify-center space-y-4 min-h-[200px]">
              {generatedFile ? (
                <div className="text-center space-y-4 animate-in fade-in zoom-in duration-300">
                  <div className="bg-green-100 dark:bg-green-900 p-4 rounded-full inline-block">
                    <IconCheck className="h-8 w-8 text-green-600 dark:text-green-400" />
                  </div>
                  <div>
                    <h3 className="font-medium text-lg">Report Ready!</h3>
                    <p className="text-sm text-muted-foreground">{generatedFile}</p>
                  </div>
                  <Button onClick={handleDownload} className="w-full" variant="neutral">
                    <IconDownload className="mr-2 h-4 w-4" />
                    Download PDF
                  </Button>
                </div>
              ) : (
                <div className="text-center text-muted-foreground">
                  <IconFileAnalytics className="h-12 w-12 mx-auto mb-2 opacity-20" />
                  <p>Configure and generate a report to download it.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
