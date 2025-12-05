'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { apiClient } from '@/lib/api/api-client';
import { Loader2, Bot } from 'lucide-react';

export default function LLMJudgePage() {
    const [text, setText] = useState('');
    const [model, setModel] = useState('gpt-4');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<any>(null);

    const handleEvaluate = async () => {
        if (!text) return;
        setLoading(true);
        try {
            const response = await apiClient.post('/api/v1/bias/llm-judge/evaluate', {
                text,
                model,
                criteria: ['gender', 'race', 'age']
            });
            setResult(response);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-8 p-8">
            <div>
                <h1 className="text-4xl font-bold">LLM-as-a-Judge</h1>
                <p className="text-muted-foreground mt-2">
                    Use advanced LLMs to evaluate content for subtle bias and fairness issues.
                </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <Card className="p-6 border-2 border-black shadow-brutal">
                    <h3 className="text-lg font-bold mb-4">Input</h3>
                    <div className="space-y-4">
                        <Textarea
                            placeholder="Enter text to evaluate..."
                            className="h-[200px] border-2 border-black"
                            value={text}
                            onChange={(e) => setText(e.target.value)}
                        />
                        <div className="flex justify-between items-center">
                            <Select value={model} onValueChange={setModel}>
                                <SelectTrigger className="w-[180px] border-2 border-black">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="gpt-4">GPT-4 (OpenAI)</SelectItem>
                                    <SelectItem value="claude-3">Claude 3 (Anthropic)</SelectItem>
                                    <SelectItem value="gemini-pro">Gemini Pro (Google)</SelectItem>
                                </SelectContent>
                            </Select>
                            <Button onClick={handleEvaluate} disabled={loading || !text}>
                                {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Bot className="mr-2 h-4 w-4" />}
                                Evaluate
                            </Button>
                        </div>
                    </div>
                </Card>

                {result && (
                    <Card className="p-6 border-2 border-black shadow-brutal bg-gray-50">
                        <h3 className="text-lg font-bold mb-4">Verdict</h3>
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <span className="font-medium">Status:</span>
                                <span className={`px-2 py-1 rounded text-sm font-bold ${result.verdict === 'PASS' ? 'bg-green-200 text-green-800' : 'bg-red-200 text-red-800'}`}>
                                    {result.verdict}
                                </span>
                            </div>
                            <div className="flex items-center justify-between">
                                <span className="font-medium">Bias Score:</span>
                                <span className="font-mono">{result.bias_score}</span>
                            </div>
                            <div>
                                <span className="font-medium block mb-2">Reasoning:</span>
                                <p className="text-sm text-gray-700 bg-white p-3 border border-gray-200 rounded">
                                    {result.reasoning}
                                </p>
                            </div>
                        </div>
                    </Card>
                )}
            </div>
        </div>
    );
}
