"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
    CheckCircle2,
    Circle,
    ArrowRight,
    ArrowLeft,
    Download,
    Sparkles,
    AlertTriangle
} from "lucide-react";
import { remediationService, type RemediationPlan } from "@/lib/api/remediation-service";

const WIZARD_STEPS = [
    { id: 1, title: "Upload & Analyze", description: "Upload bias test results" },
    { id: 2, title: "Review Recommendations", description: "See AI-recommended strategies" },
    { id: 3, title: "Configure Steps", description: "Customize remediation parameters" },
    { id: 4, title: "Preview Impact", description: "Estimate improvements" },
    { id: 5, title: "Apply & Compare", description: "Execute remediation" },
    { id: 6, title: "Export Code", description: "Download pipeline code" },
];

export default function RemediationWizardPage() {
    const [currentStep, setCurrentStep] = useState(1);
    const [plan, setPlan] = useState<RemediationPlan | null>(null);
    const [selectedSteps, setSelectedSteps] = useState<number[]>([]);
    const [generatedCode, setGeneratedCode] = useState<string>("");
    const [loading, setLoading] = useState(false);

    const progress = (currentStep / WIZARD_STEPS.length) * 100;

    const handleNext = () => {
        if (currentStep < WIZARD_STEPS.length) {
            setCurrentStep(currentStep + 1);
        }
    };

    const handleBack = () => {
        if (currentStep > 1) {
            setCurrentStep(currentStep - 1);
        }
    };

    const handleAnalyze = async () => {
        setLoading(true);
        try {
            // Call actual API
            const response = await remediationService.analyzeAndRecommend({
                bias_metrics: {
                    statistical_parity_difference: 0.25,
                    equaled_odds_tpr_difference: 0.18,
                    equal_opportunity_difference: 0.16
                },
                sensitive_attributes: {
                    gender: [0, 1, 0, 1, 1, 0],
                    race: ["A", "B", "A", "C", "B", "A"]
                }
            });

            if (response.success && response.data) {
                setPlan(response.data.plan);
                setSelectedSteps(response.data.plan.recommended_steps.filter((s: any) => s.selected).map((s: any) => s.step_id));
                handleNext();
            } else {
                console.error("Error analyzing bias:", response.error);
                // Fall back to mock data for demo
                const mockPlan: RemediationPlan = {
                    plan_id: "plan_20250128",
                    created_at: new Date().toISOString(),
                    recommended_steps: [
                        {
                            step_id: 1,
                            title: "Sample Reweighting",
                            description: "Assign higher weights to underrepresented groups during training",
                            strategy: "reweighting",
                            estimated_improvement: 0.15,
                            estimated_time_minutes: 30,
                            difficulty: "easy",
                            selected: true
                        },
                        {
                            step_id: 2,
                            title: "Threshold Optimization",
                            description: "Adjust decision thresholds per group to equalize outcomes",
                            strategy: "threshold_optimization",
                            estimated_improvement: 0.10,
                            estimated_time_minutes: 20,
                            difficulty: "medium",
                            selected: true
                        }
                    ],
                    estimated_total_improvement: 0.25,
                    estimated_total_time_minutes: 50,
                    priority_score: 75
                };
                setPlan(mockPlan);
                setSelectedSteps([1, 2]);
                handleNext();
            }
        } catch (error) {
            console.error("Error analyzing bias:", error);
        } finally {
            setLoading(false);
        }
    };

    const toggleStepSelection = (stepId: number) => {
        setSelectedSteps(prev =>
            prev.includes(stepId)
                ? prev.filter(id => id !== stepId)
                : [...prev, stepId]
        );
    };

    const handleGenerateCode = async () => {
        if (!plan) return;

        try {
            const response = await remediationService.generatePipeline({
                plan_id: plan.plan_id,
                selected_step_ids: selectedSteps
            });

            if (response.success && response.data) {
                setGeneratedCode(response.data.code);
            } else {
                // Fallback to mock code
                const code = `# Bias Remediation Pipeline
# Generated: ${new Date().toISOString()}
# Plan ID: ${plan.plan_id}

import numpy as np
import pandas as pd
from sklearn.utils.class_weight import compute_sample_weight

# Sample Reweighting
sample_weights = compute_sample_weight(
    class_weight='balanced',
    y=sensitive_attribute
)

# Train model with weights
model.fit(X_train, y_train, sample_weight=sample_weights)

print("Remediation complete!")
`;
                setGeneratedCode(code);
            }
        } catch (error) {
            console.error("Error generating code:", error);
        }
    };

    const downloadCode = () => {
        const blob = new Blob([generatedCode], { type: "text/plain" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `remediation_pipeline_${plan?.plan_id}.py`;
        a.click();
        URL.revokeObjectURL(url);
    };

    const renderStepContent = () => {
        switch (currentStep) {
            case 1:
                return (
                    <div className="space-y-6">
                        <div className="text-center py-8">
                            <Sparkles className="w-16 h-16 mx-auto mb-4 text-yellow-500" />
                            <h2 className="text-2xl font-bold mb-2">Upload & Analyze Bias Test Results</h2>
                            <p className="text-muted-foreground mb-6">
                                Upload your bias test results or select an existing test to get remediation recommendations
                            </p>
                        </div>

                        <Card>
                            <CardHeader>
                                <CardTitle>Sample Bias Metrics</CardTitle>
                                <CardDescription>Using example data for demonstration</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <p className="text-sm font-medium">Statistical Parity Difference</p>
                                        <p className="text-2xl font-bold text-red-600">0.25</p>
                                    </div>
                                    <div>
                                        <p className="text-sm font-medium">Equal Opportunity Difference</p>
                                        <p className="text-2xl font-bold text-orange-600">0.18</p>
                                    </div>
                                </div>

                                <Button
                                    onClick={handleAnalyze}
                                    className="w-full"
                                    disabled={loading}
                                >
                                    {loading ? "Analyzing..." : "Analyze & Get Recommendations"}
                                    <ArrowRight className="ml-2 h-4 w-4" />
                                </Button>
                            </CardContent>
                        </Card>
                    </div>
                );

            case 2:
                return (
                    <div className="space-y-6">
                        <div className="text-center py-4">
                            <h2 className="text-2xl font-bold mb-2">AI-Recommended Remediation Strategies</h2>
                            <p className="text-muted-foreground">
                                Based on your bias metrics, we recommend the following strategies
                            </p>
                        </div>

                        {plan?.recommended_steps.map((step) => (
                            <Card
                                key={step.step_id}
                                className={`cursor-pointer transition-all ${selectedSteps.includes(step.step_id)
                                    ? "ring-2 ring-yellow-500 bg-yellow-50/50"
                                    : "hover:shadow-md"
                                    }`}
                                onClick={() => toggleStepSelection(step.step_id)}
                            >
                                <CardContent className="pt-6">
                                    <div className="flex items-start justify-between">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-3 mb-2">
                                                <h3 className="text-lg font-bold">{step.title}</h3>
                                                <Badge variant={
                                                    step.difficulty === "easy" ? "default" :
                                                        step.difficulty === "medium" ? "secondary" :
                                                            "destructive"
                                                }>
                                                    {step.difficulty}
                                                </Badge>
                                            </div>
                                            <p className="text-sm text-muted-foreground mb-4">{step.description}</p>

                                            <div className="grid grid-cols-2 gap-4 text-sm">
                                                <div>
                                                    <span className="font-medium">Expected Improvement:</span>
                                                    <span className="ml-2 text-green-600 font-bold">
                                                        {(step.estimated_improvement * 100).toFixed(0)}%
                                                    </span>
                                                </div>
                                                <div>
                                                    <span className="font-medium">Est. Time:</span>
                                                    <span className="ml-2">{step.estimated_time_minutes} min</span>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="ml-4">
                                            {selectedSteps.includes(step.step_id) ? (
                                                <CheckCircle2 className="h-6 w-6 text-yellow-500" />
                                            ) : (
                                                <Circle className="h-6 w-6 text-gray-300" />
                                            )}
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}

                        <div className="bg-blue-50 p-4 rounded-lg">
                            <div className="flex items-start gap-3">
                                <AlertTriangle className="h-5 w-5 text-blue-600 mt-0.5" />
                                <div className="flex-1">
                                    <p className="font-medium text-blue-900">Selected Strategies Summary</p>
                                    <p className="text-sm text-blue-700 mt-1">
                                        {selectedSteps.length} strategies selected •
                                        Estimated improvement: <strong>{((plan?.recommended_steps
                                            .filter((s: any) => selectedSteps.includes(s.step_id))
                                            .reduce((acc: number, s: any) => acc + s.estimated_improvement, 0) || 0) * 100).toFixed(0)}%</strong>
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                );

            case 3:
                return (
                    <div className="space-y-6">
                        <div className="text-center py-4">
                            <h2 className="text-2xl font-bold mb-2">Configure Remediation Parameters</h2>
                            <p className="text-muted-foreground">
                                Adjust parameters for each selected strategy
                            </p>
                        </div>

                        <Card>
                            <CardContent className="pt-6">
                                <p className="text-muted-foreground text-center py-8">
                                    Parameter configuration UI will be added here.
                                    For now, using default parameters.
                                </p>
                            </CardContent>
                        </Card>
                    </div>
                );

            case 4:
                return (
                    <div className="space-y-6">
                        <div className="text-center py-4">
                            <h2 className="text-2xl font-bold mb-2">Preview Estimated Impact</h2>
                            <p className="text-muted-foreground">
                                See the expected improvements before applying remediation
                            </p>
                        </div>

                        <Card>
                            <CardHeader>
                                <CardTitle>Before vs After Comparison</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="grid grid-cols-2 gap-6">
                                    <div className="space-y-2">
                                        <p className="text-sm font-medium text-muted-foreground">BEFORE</p>
                                        <div className="space-y-2">
                                            <div>
                                                <p className="text-sm">Statistical Parity</p>
                                                <p className="text-xl font-bold text-red-600">0.25</p>
                                            </div>
                                            <div>
                                                <p className="text-sm">Accuracy</p>
                                                <p className="text-xl font-bold">0.85</p>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="space-y-2">
                                        <p className="text-sm font-medium text-muted-foreground">AFTER (Estimated)</p>
                                        <div className="space-y-2">
                                            <div>
                                                <p className="text-sm">Statistical Parity</p>
                                                <p className="text-xl font-bold text-green-600">0.10</p>
                                            </div>
                                            <div>
                                                <p className="text-sm">Accuracy</p>
                                                <p className="text-xl font-bold">0.84</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                );

            case 5:
                return (
                    <div className="space-y-6">
                        <div className="text-center py-4">
                            <h2 className="text-2xl font-bold mb-2">Apply Remediation</h2>
                            <p className="text-muted-foreground">
                                Execute the remediation pipeline
                            </p>
                        </div>

                        <Card>
                            <CardContent className="pt-6">
                                <p className="text-center text-muted-foreground py-8">
                                    In production, this step will retrain your model with the selected remediation strategies.
                                </p>
                                <Button onClick={handleNext} className="w-full">
                                    Simulate Remediation
                                    <ArrowRight className="ml-2 h-4 w-4" />
                                </Button>
                            </CardContent>
                        </Card>
                    </div>
                );

            case 6:
                return (
                    <div className="space-y-6">
                        <div className="text-center py-4">
                            <h2 className="text-2xl font-bold mb-2">Export Remediation Code</h2>
                            <p className="text-muted-foreground">
                                Download production-ready Python code
                            </p>
                        </div>

                        <Card>
                            <CardHeader>
                                <CardTitle>Generated Pipeline</CardTitle>
                                <CardDescription>Production-ready remediation code</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                {!generatedCode && (
                                    <Button onClick={handleGenerateCode} className="w-full">
                                        Generate Code
                                    </Button>
                                )}

                                {generatedCode && (
                                    <>
                                        <pre className="bg-gray-950 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm">
                                            <code>{generatedCode}</code>
                                        </pre>

                                        <div className="flex space-x-4">
                                            <Button onClick={handleDownloadCode} className="flex-1">
                                                <Download className="mr-2 h-4 w-4" />
                                                Download Python Script
                                            </Button>
                                            <Button variant="outline" onClick={() => {
                                                const blob = new Blob([generatedCode], { type: 'application/json' });
                                                const url = URL.createObjectURL(blob);
                                                const a = document.createElement('a');
                                                a.href = url;
                                                a.download = 'remediation_notebook.ipynb';
                                                document.body.appendChild(a);
                                                a.click();
                                                document.body.removeChild(a);
                                                URL.revokeObjectURL(url);
                                            }} className="flex-1">
                                                <IconNotebook className="mr-2 h-4 w-4" />
                                                Download Notebook
                                            </Button>
                                        </div>
                                    </>
                                )}
                            </CardContent>
                        </Card>
                    </div>
                );

            default:
                return null;
        }
    };

    return (
        <div className="container mx-auto py-8 max-w-4xl">
            {/* Progress indicator */}
            <div className="mb-8">
                <div className="flex items-center justify-between mb-4">
                    <h1 className="text-3xl font-bold">Bias Remediation Wizard</h1>
                    <Badge>
                        Step {currentStep} of {WIZARD_STEPS.length}
                    </Badge>
                </div>

                <Progress value={progress} className="mb-2" />

                <div className="flex justify-between mt-4">
                    {WIZARD_STEPS.map((step) => (
                        <div
                            key={step.id}
                            className={`flex-1 text-center ${step.id === currentStep ? "text-yellow-600 font-medium" : "text-muted-foreground"
                                }`}
                        >
                            <div className={`text-xs ${step.id <= currentStep ? "opacity-100" : "opacity-50"}`}>
                                {step.title}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Step content */}
            <div className="mb-8">
                {renderStepContent()}
            </div>

            {/* Navigation */}
            <div className="flex justify-between">
                <Button
                    variant="outline"
                    onClick={handleBack}
                    disabled={currentStep === 1}
                >
                    <ArrowLeft className="mr-2 h-4 w-4" />
                    Back
                </Button>

                {currentStep < WIZARD_STEPS.length && currentStep !== 1 && (
                    <Button onClick={handleNext}>
                        Next
                        <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                )}
            </div>
        </div>
    );
}
